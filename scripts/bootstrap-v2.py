"""One-shot setup for the Enron ILI pipeline, using uv and a locked dependency set.

    Windows:  py scripts\\bootstrap-v2.py
    Linux/mac: python3 scripts/bootstrap-v2.py

What it does, in order. Every phase is skipped if already done, so re-running
is safe and cheap:

    1. diagnose this machine (OS, interpreters, GPU, disk, network)
    2. install uv if absent, and let uv fetch the exact Python this needs
    3. uv sync --locked  -- installs the EXACT versions in uv.lock
    4. find the Enron corpus, or download and extract it
    5. pipeclean run: the end-to-end smoke test (~4 min)
    6. write bootstrap-report.json with everything above

If anything fails, the report is still written, failures are classified
against known causes with a remedy for each, and the collaborator is told to
send that one file. Nothing else needs to be screenshotted or copied.

WHY uv AND NOT venv+pip (see also docs/SETUP.md):
  * uv.lock pins all 50 packages in the chain, not just the 5 direct ones
    requirements.txt names. Two machines get byte-identical environments.
  * uv installs the required Python itself, so the machine's own Python
    version stops mattering. This is the actual fix for most of the
    "dependency issues" collaborators have been hitting.

ON THE "PYTHON 3.8.3" REPORT: there is no such requirement. `spacy==3.8.16`
and `en_core_web_sm-3.8.0` are *spaCy* versions. spaCy 3.8 declares
Requires-Python >=3.9,<3.15, and numpy 2.5 needs >=3.12, so the real window
is 3.12-3.14. Every compiled dependency ships a cp314 win_amd64 wheel --
nothing in this pipeline needs to be compiled, and nothing needs Python 3.8.

Stdlib only, and deliberately written in Python 3.8-compatible syntax, so
that a collaborator running an old interpreter still gets a readable
diagnosis instead of a SyntaxError.
"""
from __future__ import annotations

import argparse
import functools
import json
import os
import platform
import re
import shutil
import socket
import ssl
import subprocess
import sys
import tarfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

print = functools.partial(print, flush=True)

ROOT = Path(__file__).resolve().parent.parent
MIN_PY = (3, 12)   # numpy 2.5.x floor
MAX_PY = (3, 14)   # spacy 3.8.x ceiling is <3.15
TARGET_PY = "3.14"

CORPUS_URL = "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz"
TARBALL = "enron_mail_20150507.tar.gz"
EXPECTED_CUSTODIANS = 150
PROGRESS_EVERY = 60  # seconds between extraction progress lines
DOWNLOAD_ATTEMPTS = 4

UV_INSTALL_SH = "https://astral.sh/uv/install.sh"
UV_INSTALL_PS1 = "https://astral.sh/uv/install.ps1"

IS_WINDOWS = sys.platform == "win32"


# ==========================================================================
# pure logic (unit-tested in tests/test_bootstrap_v2.py)
# ==========================================================================

def classify_python(version):
    # type: (Tuple[int, int]) -> str
    """'ok', 'too-old' or 'too-new' against the real supported window."""
    if version < MIN_PY:
        return "too-old"
    if version > MAX_PY:
        return "too-new"
    return "ok"


def parse_cuda_version(text):
    # type: (str) -> Optional[str]
    """Pull the CUDA version out of the nvidia-smi banner.

    Older drivers print 'CUDA Version: 12.8'; drivers from the 6xx series print
    'CUDA UMD Version: 13.3'. Both forms must parse.
    """
    m = re.search(r"CUDA (?:UMD )?Version:\s*([\d.]+)", text)
    return m.group(1) if m else None


def parse_nvidia_smi(stdout, cuda):
    # type: (str, Optional[str]) -> Optional[Dict[str, Any]]
    """Parse `nvidia-smi --query-gpu=name,driver_version,memory.total` CSV.

    Returns None when there is no usable GPU line, including when nvidia-smi
    is missing and the shell has echoed something like 'command not found'.
    """
    line = stdout.strip().splitlines()[0].strip() if stdout.strip() else ""
    if not line:
        return None
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2 or not re.match(r"^[\d.]+$", parts[1]):
        return None
    memory = None
    if len(parts) > 2:
        m = re.match(r"^(\d+)", parts[2])
        if m:
            memory = int(m.group(1))
    return {"name": parts[0], "driver": parts[1], "memory_mib": memory, "cuda": cuda}


def gpu_verdict(gpu, plat):
    # type: (Optional[Dict[str, Any]], str) -> Tuple[bool, str]
    """Can this machine use the optional cupy-cuda12x GPU extra?

    The GPU is never required -- analyze.py defaults to --device cpu -- so
    every 'no' here is a note, not an error.
    """
    if plat == "darwin":
        return False, "macOS has no CUDA support; cupy-cuda12x ships no macOS wheels. CPU only."
    if not gpu:
        return False, "no NVIDIA GPU detected (nvidia-smi absent or returned nothing). CPU only."
    cuda = gpu.get("cuda")
    if not cuda:
        return False, "NVIDIA GPU found but the CUDA driver version could not be read. CPU only."
    # nvidia-smi reports the NEWEST CUDA runtime the driver supports, and NVIDIA
    # drivers are backward compatible, so a CUDA 13.x driver still runs the
    # CUDA 12 binaries in cupy-cuda12x. The test is >= 12, not == 12.
    try:
        major = int(cuda.split(".")[0])
    except ValueError:
        return False, "could not read the CUDA version from the driver. CPU only."
    if major < 12:
        return False, (
            "driver supports only CUDA %s; cupy-cuda12x needs a driver supporting "
            "CUDA 12.x or newer. CPU only." % cuda
        )
    return True, ("NVIDIA GPU, driver supports CUDA %s (>=12, so the CUDA 12 "
                  "binaries in cupy-cuda12x will run); the gpu extra can be "
                  "installed." % cuda)


# Ordered: the first match is the headline cause, so put the specific ones first.
FAILURE_SIGNATURES = [
    {
        "id": "corpus-incomplete",
        "pattern": r"custodian directories, expected|differs from the known-good run",
        "remedy": (
            "The corpus did not extract completely. On Windows this is almost "
            "always the 260-character path limit: the maildir tree is very deep. "
            "Delete the partial tree and re-extract to a SHORT path such as "
            "C:\\enron, and enable long paths (see the report's "
            "windows_long_paths field)."
        ),
    },
    {
        "id": "needs-compiler",
        "pattern": (r"Microsoft Visual C\+\+ 14\.0|vcvarsall|Building wheel for .* failed"
                    r"|error: command '.*(gcc|cc|cl)\.exe?' failed"),
        "remedy": (
            "pip tried to COMPILE a dependency, which means it could not find a "
            "matching wheel. Every compiled dependency in uv.lock has a cp314 "
            "win_amd64 wheel, so this should not happen on the uv path -- it is "
            "a sign the old requirements.txt/pip path was used, or an unsupported "
            "Python version. Re-run this script rather than pip."
        ),
    },
    {
        "id": "no-matching-wheel",
        "pattern": r"No matching distribution found|Could not find a version that satisfies",
        "remedy": (
            "No wheel matched this interpreter/platform. Usually an unsupported "
            "Python version (the window is 3.12-3.14) or a 32-bit Python. uv "
            "installs its own Python 3.14, so re-running this script normally "
            "fixes it."
        ),
    },
    {
        "id": "tls-intercepted",
        "pattern": r"CERTIFICATE_VERIFY_FAILED|SSLCertVerificationError|SSLError|certificate verify failed",
        "remedy": (
            "Certificate verification failed. Two causes are common: (a) uv's "
            "managed CPython ships no CA bundle on Windows -- this script now "
            "works around that by using certifi from the venv, so if you see "
            "this at the corpus step, re-run and it should pass; or (b) a "
            "corporate proxy or AV doing TLS inspection, in which case ask IT "
            "for the proxy root CA and set SSL_CERT_FILE, and set "
            "UV_SYSTEM_CERTS=1 (UV_NATIVE_TLS=1 on uv older than 0.9) so uv "
            "uses the OS certificate store."
        ),
    },
    {
        "id": "network-unreachable",
        "pattern": r"Temporary failure in name resolution|Failed to establish a new connection"
                   r"|getaddrinfo failed|Network is unreachable|Connection refused",
        "remedy": (
            "No route to the package index or the corpus host. Check the network "
            "and any HTTP_PROXY/HTTPS_PROXY settings the machine needs."
        ),
    },
    {
        "id": "disk-full",
        "pattern": r"Errno 28|No space left on device|not enough space",
        "remedy": (
            "Out of disk. The corpus needs about 6GB (423MB tarball + ~2.6GB "
            "extracted), plus ~1GB for the environment. Free space or pass "
            "--corpus pointing at a roomier drive."
        ),
    },
    {
        "id": "out-of-memory",
        "pattern": r"\bMemoryError\b|Cannot allocate memory|out of memory",
        "remedy": (
            "Ran out of RAM. The smoke test needs roughly 2GB free. Close other "
            "applications and re-run."
        ),
    },
    {
        "id": "gpu-driver",
        "pattern": r"CUDADriverError|CUDA_ERROR_SYSTEM_DRIVER_MISMATCH"
                   r"|CUDA driver version is insufficient|cudaErrorInsufficientDriver",
        "remedy": (
            "The NVIDIA driver is too old for cupy-cuda12x. The GPU is optional: "
            "re-run with --no-gpu and the pipeline will use the CPU, which is the "
            "default for analyze.py anyway."
        ),
    },
]


def classify_failure(text):
    # type: (str) -> List[Dict[str, str]]
    """Map raw failure output to known causes. Empty list means 'novel'."""
    out = []
    for sig in FAILURE_SIGNATURES:
        if re.search(sig["pattern"], text, re.IGNORECASE):
            out.append({"id": sig["id"], "remedy": sig["remedy"]})
    return out


# ==========================================================================
# phase 1: diagnose
# ==========================================================================

def run_streaming(cmd, heartbeat=None, **kw):
    # type: (Any, Optional[str], Any) -> subprocess.CompletedProcess
    """Run a command, showing its output live AND keeping a copy.

    The long phases (installing ~250MB of wheels, the pipeclean run) can take
    tens of minutes. Capturing their output silences them completely, which
    looks identical to a hang -- so tee it instead.

    Some phases are worse than quiet: a single pipeline stage (spaCy analysis)
    can run for minutes printing nothing at all. Pass `heartbeat` with a label
    and a line is printed every PROGRESS_EVERY seconds of silence, so the user
    can tell the difference between "working" and "wedged".
    """
    lines = []
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                bufsize=1, **kw)
    except (OSError, subprocess.SubprocessError) as exc:
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))

    started = time.time()
    last = [started]
    stop = threading.Event()

    def beat():
        # Poll rather than sleep(PROGRESS_EVERY) so the thread exits promptly
        # when the process does, instead of outliving it and printing over
        # whatever comes next.
        while not stop.wait(0.1):
            quiet = time.time() - last[0]
            if quiet >= PROGRESS_EVERY:
                mins = (time.time() - started) // 60
                print("     ... %s still running, %d min elapsed" % (heartbeat, mins))
                last[0] = time.time()

    thread = None
    if heartbeat:
        thread = threading.Thread(target=beat)
        thread.daemon = True
        thread.start()
    try:
        # `with` so the pipe is closed even if the loop raises; leaving it open
        # leaks a file descriptor per call and emits a ResourceWarning into the
        # middle of the pipeclean output.
        with proc.stdout:
            for line in proc.stdout:
                last[0] = time.time()
                sys.stdout.write("     | " + line)
                sys.stdout.flush()
                lines.append(line)
    finally:
        stop.set()
        if thread is not None:
            thread.join(timeout=2)
        if proc.poll() is None:
            # Only reached if we bailed out early (Ctrl+C); do not leave the
            # child running detached.
            proc.kill()
        proc.wait()
    return subprocess.CompletedProcess(cmd, proc.returncode, "".join(lines), "")


def run(cmd, timeout=120, **kw):
    # type: (Any, int, Any) -> subprocess.CompletedProcess
    """subprocess.run that never raises, on a missing binary or a timeout.

    Callers override `timeout` for the slow phases (installs, downloads), so it
    must be a real parameter and not baked into the call below.
    """
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, **kw)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            cmd, 124, "", "timed out after %ss: %s" % (timeout, cmd))
    except (OSError, subprocess.SubprocessError) as exc:
        return subprocess.CompletedProcess(cmd, 127, "", str(exc))


def find_interpreters():
    # type: () -> List[Dict[str, str]]
    """Every Python this machine can see. The usual cause of 'it works on mine'."""
    found = []
    seen = set()

    def add(path, source):
        if not path or path in seen:
            return
        seen.add(path)
        # %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe is the Microsoft Store
        # "App Execution Alias" -- a stub that opens the Store rather than running
        # Python. It is on PATH by default on a fresh Windows install, so it is a
        # very common cause of "python is installed but nothing works". Never
        # execute it; just record that it is there.
        if "windowsapps" in path.replace("/", "\\").lower():
            found.append({"path": path, "version": None, "arch": None,
                          "source": source, "store_alias": True})
            return
        r = run([path, "-c", "import sys,platform;"
                            "print(sys.version.split()[0], platform.architecture()[0])"])
        if r.returncode == 0 and r.stdout.strip():
            ver, arch = (r.stdout.split() + ["?"])[:2]
            found.append({"path": path, "version": ver, "arch": arch,
                          "source": source, "store_alias": False})

    add(sys.executable, "running this script")
    if IS_WINDOWS:
        # The py launcher is the reliable way to enumerate on Windows.
        r = run(["py", "-0p"])
        for line in r.stdout.splitlines():
            m = re.search(r"(\w:\\[^\s].*?python\.exe)", line, re.IGNORECASE)
            if m:
                add(m.group(1), "py launcher")
    for name in ("python3", "python", "python3.14", "python3.13", "python3.12"):
        add(shutil.which(name), "PATH")
    return found


def probe_gpu():
    # type: () -> Optional[Dict[str, Any]]
    banner = run(["nvidia-smi"])
    cuda = parse_cuda_version(banner.stdout) if banner.returncode == 0 else None
    q = run(["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
             "--format=csv,noheader,nounits"])
    if q.returncode != 0:
        return None
    return parse_nvidia_smi(q.stdout, cuda)


def windows_long_paths_enabled():
    # type: () -> Optional[bool]
    """Read LongPathsEnabled, the registry flag behind most Windows corpus failures."""
    if not IS_WINDOWS:
        return None
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SYSTEM\CurrentControlSet\Control\FileSystem")
        value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
        return bool(value)
    except Exception:
        return False


def reachable(host, port=443, timeout=6):
    # type: (str, int, int) -> bool
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except OSError:
        return False


def diagnose(corpus_dir):
    # type: (Path) -> Dict[str, Any]
    print("[..] diagnosing this machine")
    gpu = probe_gpu()
    gpu_ok, gpu_reason = gpu_verdict(gpu, sys.platform)
    try:
        usage = shutil.disk_usage(str(corpus_dir if corpus_dir.exists() else ROOT))
        free_gb = round(usage.free / 1e9, 1)
    except OSError:
        free_gb = None

    report = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "sys_platform": sys.platform,
        },
        "running_python": {
            "executable": sys.executable,
            "version": platform.python_version(),
            "status": classify_python(sys.version_info[:2]),
            "supported_window": "%d.%d - %d.%d" % (MIN_PY + MAX_PY),
        },
        "interpreters_found": find_interpreters(),
        "gpu": gpu,
        "gpu_usable": gpu_ok,
        "gpu_note": gpu_reason,
        "free_disk_gb": free_gb,
        "windows_long_paths": windows_long_paths_enabled(),
        "network": {
            "pypi.org": reachable("pypi.org"),
            "astral.sh": reachable("astral.sh"),
            "www.cs.cmu.edu": reachable("www.cs.cmu.edu"),
        },
        "proxy_env": {k: v for k, v in os.environ.items()
                      if k.lower() in ("http_proxy", "https_proxy", "no_proxy",
                                       "ssl_cert_file", "requests_ca_bundle")},
        "phases": {},
        "failures": [],
    }

    print("     %s %s (%s), Python %s [%s]" % (
        report["platform"]["system"], report["platform"]["release"],
        report["platform"]["machine"], report["running_python"]["version"],
        report["running_python"]["status"]))
    real = [i for i in report["interpreters_found"] if not i.get("store_alias")]
    stubs = [i for i in report["interpreters_found"] if i.get("store_alias")]
    print("     %d real interpreter(s) visible%s" % (
        len(real), (", plus %d Microsoft Store stub(s)" % len(stubs)) if stubs else ""))
    for i in real:
        print("       %s  %s" % (i["version"], i["path"]))
    if stubs and not real:
        print("[warn] the only 'python' on PATH is the Microsoft Store alias stub, "
              "which is not a Python. Use scripts\\bootstrap.ps1, which installs a "
              "real one via uv.")
    print("     GPU: %s" % gpu_reason)
    if free_gb is not None:
        print("     free disk: %sGB" % free_gb)
    unreachable = [h for h, ok in report["network"].items() if not ok]
    if unreachable:
        print("[warn] cannot reach: %s -- installs or the corpus download may fail"
              % ", ".join(unreachable))
    if IS_WINDOWS and not report["windows_long_paths"]:
        print("[warn] Windows long paths are DISABLED. The corpus tree is deep enough "
              "to hit the 260-character limit; extract to a short path (C:\\enron).")
    return report


# ==========================================================================
# phase 2: uv
# ==========================================================================

def uv_candidates():
    # type: () -> List[str]
    home = Path.home()
    paths = [shutil.which("uv")]
    if IS_WINDOWS:
        paths += [str(home / ".local" / "bin" / "uv.exe"),
                  str(home / ".cargo" / "bin" / "uv.exe")]
    else:
        paths += [str(home / ".local" / "bin" / "uv"),
                  str(home / ".cargo" / "bin" / "uv")]
    return [p for p in paths if p]


def find_uv():
    # type: () -> Optional[str]
    for path in uv_candidates():
        if run([path, "--version"]).returncode == 0:
            return path
    return None


def ensure_uv(report):
    # type: (Dict[str, Any]) -> str
    uv = find_uv()
    if uv:
        version = run([uv, "--version"]).stdout.strip()
        print("[skip] uv already installed: %s (%s)" % (version, uv))
        report["phases"]["uv"] = {"status": "present", "path": uv, "version": version}
        return uv

    print("[..] installing uv (a single ~30MB binary, user-local, no admin needed)")
    if IS_WINDOWS:
        cmd = ["powershell", "-ExecutionPolicy", "ByPass", "-NoProfile", "-Command",
               "irm %s | iex" % UV_INSTALL_PS1]
    else:
        cmd = ["sh", "-c", "curl -LsSf %s | sh" % UV_INSTALL_SH]
    r = run(cmd, timeout=600)
    uv = find_uv()

    if not uv:
        # Locked-down machine: no network to astral.sh, or no PowerShell policy.
        print("[warn] the official installer did not work; falling back to pip")
        fb = run([sys.executable, "-m", "pip", "install", "--user", "--upgrade", "uv"],
                 timeout=600)
        uv = find_uv()
        if not uv:
            fail(report, "uv", (r.stdout + r.stderr + fb.stdout + fb.stderr),
                 "Could not install uv by either method.")
    version = run([uv, "--version"]).stdout.strip()
    print("[ok] uv installed: %s (%s)" % (version, uv))
    report["phases"]["uv"] = {"status": "installed", "path": uv, "version": version}
    return uv


# ==========================================================================
# phase 3: locked install
# ==========================================================================

def sync(uv, report, venv, want_gpu):
    # type: (str, Dict[str, Any], Path, bool) -> Path
    env = dict(os.environ)
    env["UV_PROJECT_ENVIRONMENT"] = str(venv)
    # Use the OS certificate store, so uv keeps working behind a corporate
    # proxy doing TLS inspection. Older uv spells this UV_NATIVE_TLS.
    env.setdefault("UV_SYSTEM_CERTS", "1")

    print("[..] fetching CPython %s via uv (so this machine's own Python "
          "version stops mattering)" % TARGET_PY)
    r = run_streaming([uv, "python", "install", TARGET_PY], cwd=str(ROOT), env=env)
    if r.returncode != 0:
        # Not fatal on its own: a suitable Python may already be present.
        print("[warn] `uv python install` failed; will try an interpreter already here")

    cmd = [uv, "sync", "--locked", "--python", TARGET_PY]
    if want_gpu:
        cmd += ["--extra", "gpu"]
    print("[..] installing the locked dependency set%s (~250MB of wheels)"
          % (" incl. GPU extra" if want_gpu else ""))
    r = run_streaming(cmd, cwd=str(ROOT), env=env)
    if r.returncode != 0:
        fail(report, "sync", r.stdout + r.stderr,
             "Dependency installation failed. Nothing was half-installed -- uv "
             "syncs atomically, so re-running after the remedy below is safe.")

    py = venv / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")
    check = ("import quotequail, spacy; "
             "spacy.load('en_core_web_sm', exclude=['ner','lemmatizer','parser']); "
             "import sys; print(sys.version.split()[0])")
    v = run([str(py), "-c", check])
    if v.returncode != 0:
        fail(report, "sync", v.stdout + v.stderr,
             "Dependencies installed but spaCy or quotequail will not load.")

    installed = run([uv, "pip", "list", "--format=json"], cwd=str(ROOT), env=env)
    try:
        packages = json.loads(installed.stdout)
    except ValueError:
        packages = []
    print("[ok] %d packages installed and verified, on Python %s"
          % (len(packages), v.stdout.strip()))
    report["phases"]["sync"] = {
        "status": "ok",
        "venv": str(venv),
        "python": v.stdout.strip(),
        "package_count": len(packages),
        "gpu_extra": want_gpu,
        "packages": packages,
    }
    return py


# ==========================================================================
# phase 4: corpus  (same discovery rules as scripts/bootstrap.py)
# ==========================================================================

def custodian_count(maildir):
    # type: (Path) -> int
    if not maildir.is_dir():
        return 0
    return sum(1 for p in maildir.iterdir() if p.is_dir())


def default_corpus_dir():
    # type: () -> Path
    if IS_WINDOWS:
        # Short on purpose: the maildir tree is deep enough to hit the 260-char limit.
        return Path("C:/enron")
    return Path.home() / "data" / "enron"


def candidate_maildirs(explicit):
    # type: (Optional[Path]) -> List[Path]
    raw = [
        explicit,
        Path(os.environ["ENRON_MAILDIR"]) if os.environ.get("ENRON_MAILDIR") else None,
        default_corpus_dir() / "maildir",
        Path.home() / "data" / "enron" / "maildir",
        Path("C:/enron/maildir") if IS_WINDOWS else None,
        ROOT / "maildir",
    ]
    seen, out = set(), []
    for p in raw:
        if p is None:
            continue
        p = p.expanduser()
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def find_corpus(explicit):
    # type: (Optional[Path]) -> Optional[Path]
    partial = []
    for path in candidate_maildirs(explicit):
        n = custodian_count(path)
        if n == 0:
            continue
        if n >= EXPECTED_CUSTODIANS:
            print("[skip] found existing corpus at %s (%d custodians)" % (path, n))
            return path
        partial.append((path, n))
    for path, n in partial:
        print("[warn] %s is incomplete: %d custodian directories, expected %d. "
              "Not using it as-is; extraction will resume into it and finish it "
              "off." % (path, n, EXPECTED_CUSTODIANS))
    return None


def corpus_ssl_context(venv_python):
    # type: (Optional[Path]) -> Any
    """An SSL context that can actually verify certificates.

    uv's managed CPython (python-build-standalone) ships no CA bundle on
    Windows, so urllib cannot verify ANY https certificate and every download
    dies with CERTIFICATE_VERIFY_FAILED. On Linux the same build happens to
    find the system store at /etc/ssl/certs, which is why this only bites
    Windows. The locked dependency set includes certifi, so borrow its bundle
    from the venv we have just created. (buglog bug-006)
    """
    ctx = ssl.create_default_context()
    if venv_python is None:
        return ctx
    r = run([str(venv_python), "-c", "import certifi; print(certifi.where())"])
    cafile = r.stdout.strip()
    if r.returncode == 0 and cafile and Path(cafile).is_file():
        try:
            ctx.load_verify_locations(cafile)
            print("     using the certifi CA bundle from the venv")
        except (OSError, ssl.SSLError):
            pass
    return ctx


def download(url, dest, context=None):
    # type: (str, Path, Any) -> None
    """Download with resume, so an interrupted 423MB fetch is not restarted."""
    part = dest.with_suffix(dest.suffix + ".part")
    have = part.stat().st_size if part.exists() else 0
    req = urllib.request.Request(url)
    if have:
        print("[..] resuming download at %dMB" % (have / 1e6))
        req.add_header("Range", "bytes=%d-" % have)
    with urllib.request.urlopen(req, context=context) as resp:
        resuming = resp.status == 206
        if have and not resuming:
            print("[warn] server ignored resume request; starting over")
            have = 0
        total = int(resp.headers.get("Content-Length", 0)) + (have if resuming else 0)
        mode = "ab" if (have and resuming) else "wb"
        done = have if resuming else 0
        with part.open(mode) as f:
            while True:
                chunk = resp.read(1 << 20)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if total:
                    print("\r    %6.0f / %.0f MB (%d%%)"
                          % (done / 1e6, total / 1e6, done * 100 // total), end="")
        print()
    part.rename(dest)


class ExtractResult(object):
    """What one extraction pass did. `extracted + skipped` is everything seen."""

    def __init__(self, extracted, skipped, custodians):
        # type: (int, int, int) -> None
        self.extracted = extracted
        self.skipped = skipped
        self.custodians = custodians

    @property
    def total(self):
        # type: () -> int
        return self.extracted + self.skipped


def _resume_target(corpus_dir, name):
    # type: (Path, str) -> Optional[Path]
    """Where a member should already be, or None if the name is not safe.

    Only used to decide whether to SKIP a member. Extraction itself is still
    guarded by filter='data'; this refuses to stat anything outside the
    destination so a hostile archive cannot probe the filesystem.
    """
    clean = name.replace("\\", "/").strip("/")
    if not clean or ".." in clean.split("/"):
        return None
    target = corpus_dir / clean
    try:
        target.relative_to(corpus_dir)
    except ValueError:
        return None
    return target


def extract_corpus(tarball, corpus_dir, resume=True):
    # type: (Path, Path, bool) -> ExtractResult
    """Extract the corpus, resumably, printing progress every PROGRESS_EVERY s.

    Two problems with tarfile.extractall(). It is a single silent blocking call,
    and on Windows the corpus's ~500k small files take 1-3 hours, during which
    the script is indistinguishable from a hang. And if it is interrupted --
    Ctrl+C, a reboot, a full disk -- everything done so far is thrown away and
    the next run starts from nothing.

    So walk the members instead: report progress as we go, and skip any file
    already on disk at its full size. A file that was half-written when the
    interrupt landed has the wrong size, so it is re-extracted rather than
    silently kept. Progress is counted in custodian directories, because that
    is the number the success check uses (EXPECTED_CUSTODIANS).
    """
    started = last = time.time()
    extracted = skipped = 0
    custodians = set()
    with tarfile.open(str(tarball)) as tf:
        for member in tf:
            target = _resume_target(corpus_dir, member.name) if resume else None
            if target is not None and member.isfile():
                try:
                    if target.stat().st_size == member.size:
                        skipped += 1
                        target = None   # nothing to do
                    else:
                        target = False  # exists but wrong size: redo it
                except OSError:
                    target = False      # not there: extract it
            else:
                target = False

            if target is False:
                # filter='data' refuses absolute paths and traversal outside
                # the destination. Default from 3.14; explicit so 3.12-3.14
                # behave identically.
                tf.extract(member, str(corpus_dir), filter="data")
                extracted += 1

            parts = member.name.replace("\\", "/").split("/")
            if len(parts) >= 2 and parts[0] == "maildir" and parts[1]:
                custodians.add(parts[1])

            now = time.time()
            if now - last >= PROGRESS_EVERY:
                elapsed = now - started
                n = len(custodians)
                done = extracted + skipped
                msg = ("     %d/%d custodians, %s files, %.0f/sec, %d min elapsed"
                       % (n, EXPECTED_CUSTODIANS, "{:,}".format(done),
                          done / elapsed if elapsed else 0, elapsed // 60))
                if skipped:
                    msg += " (%s already there)" % "{:,}".format(skipped)
                if 0 < n < EXPECTED_CUSTODIANS and elapsed > 30:
                    remaining = elapsed / n * (EXPECTED_CUSTODIANS - n)
                    msg += " -- about %d min left" % max(1, remaining // 60)
                print(msg)
                last = now
    return ExtractResult(extracted, skipped, len(custodians))


def download_with_retries(url, dest, context=None, attempts=None):
    # type: (str, Path, Any, Optional[int]) -> None
    """Download, retrying on failure, so an unattended run survives a blip.

    This matters because the script is meant to be started and left alone: a
    single dropped connection 300MB into a 423MB download would otherwise abort
    the whole setup. download() resumes from the .part file, so each retry costs
    only the bytes still missing.
    """
    attempts = attempts or DOWNLOAD_ATTEMPTS
    for attempt in range(1, attempts + 1):
        try:
            download(url, dest, context)
            return
        except Exception as exc:
            if attempt >= attempts:
                raise
            wait = min(30, 5 * attempt)
            print("[warn] download attempt %d of %d failed (%s: %s). "
                  "Retrying in %ds; it resumes where it stopped."
                  % (attempt, attempts, type(exc).__name__, exc, wait))
            time.sleep(wait)


def ensure_corpus(explicit, corpus_dir, report, venv_python=None):
    # type: (Optional[Path], Path, Dict[str, Any], Optional[Path]) -> Path
    found = find_corpus(explicit)
    if found:
        report["phases"]["corpus"] = {"status": "present", "path": str(found),
                                      "custodians": custodian_count(found)}
        return found

    maildir = corpus_dir / "maildir"
    try:
        corpus_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        fail(report, "corpus", str(exc), "Could not create %s." % corpus_dir)
    tarball = corpus_dir / TARBALL

    if tarball.exists():
        print("[skip] tarball already downloaded: %s (%dMB)"
              % (tarball, tarball.stat().st_size / 1e6))
    else:
        free = shutil.disk_usage(str(corpus_dir)).free
        if free < 6e9:
            fail(report, "corpus", "Errno 28: only %.1fGB free at %s" % (free / 1e9, corpus_dir),
                 "The corpus needs about 6GB.")
        print("[..] downloading the corpus (~423MB) from %s" % CORPUS_URL)
        try:
            download_with_retries(CORPUS_URL, tarball,
                                  corpus_ssl_context(venv_python))
        except Exception as exc:
            fail(report, "corpus", "%s: %s" % (type(exc).__name__, exc),
                 "Corpus download failed.")
        print("[ok] downloaded")

    print("[..] extracting to %s (bloody ages.. ~2.6GB of ~500k tiny files; "
          "minutes on Linux, 1-3 HOURS on Windows -- progress every %ds so you "
          "can see it is not stuck)" % (maildir, PROGRESS_EVERY))
    if IS_WINDOWS:
        # ~1-3 hours measured on a Windows 11 VM whose Defender was DISABLED, so
        # the cost there was the ~500k small-file creates themselves, not AV.
        # On a normal machine real-time scanning is on and adds to that, hence
        # the tip -- but we do not claim it is the whole story, and we never
        # change anyone's AV settings automatically.
        print("     Tip: if your antivirus does real-time scanning (most do), it")
        print("     scans each of the ~500k small files as they land. Excluding")
        print("     the corpus folder first, in an admin PowerShell, can help:")
        print("       Add-MpPreference -ExclusionPath '%s'" % corpus_dir)
        print("     It only holds public research data. Skip this if your")
        print("     organisation's policy says not to.")
    try:
        result = extract_corpus(tarball, corpus_dir)
        if result.skipped:
            print("[ok] %s files extracted, %s already present (resumed)"
                  % ("{:,}".format(result.extracted), "{:,}".format(result.skipped)))
        else:
            print("[ok] extracted %s files" % "{:,}".format(result.extracted))
    except Exception as exc:
        fail(report, "corpus", "%s: %s" % (type(exc).__name__, exc),
             "Corpus extraction failed.")

    n = custodian_count(maildir)
    if n < EXPECTED_CUSTODIANS:
        fail(report, "corpus",
             "Extraction produced only %d custodian directories, expected %d."
             % (n, EXPECTED_CUSTODIANS),
             "The corpus is incomplete; the pipeline would produce wrong counts.")
    print("[ok] corpus ready at %s (%d custodians)" % (maildir, n))
    print("     you can delete %s to reclaim ~423MB" % tarball)
    report["phases"]["corpus"] = {"status": "downloaded", "path": str(maildir),
                                  "custodians": n}
    return maildir


# ==========================================================================
# phase 5: pipeclean
# ==========================================================================

def pipeclean(py, maildir, report):
    # type: (Path, Path, Dict[str, Any]) -> None
    """Run the real pipeline end to end and check it against known-good counts."""
    print("[..] pipeclean run: the whole pipeline over four custodians, for real.")
    print("     ~4 minutes on Linux, longer on Windows. Five stages: ingest,")
    print("     extract, analyze (the slow one -- spaCy), annotate, aggregate.")
    env = dict(os.environ)
    env["ENRON_MAILDIR"] = str(maildir)
    # Without this the child block-buffers stdout into the pipe and the stage
    # names only appear at the very end, defeating the point.
    env["PYTHONUNBUFFERED"] = "1"
    started = time.time()
    r = run_streaming(
        [str(py), "-m", "unittest", "discover", "-s", "tests", "-v"],
        heartbeat="pipeclean", cwd=str(ROOT), env=env,
    )
    elapsed = round(time.time() - started, 1)
    output = r.stdout

    report["phases"]["pipeclean"] = {
        "status": "ok" if r.returncode == 0 else "failed",
        "exit_code": r.returncode,
        "seconds": elapsed,
        # The full output is kept in the report so nothing has to be re-run to
        # diagnose it. This is the "log errors for further analysis" bit.
        "output": output,
    }
    if r.returncode != 0:
        fail(report, "pipeclean", output,
             "The pipeline ran but did not produce the known-good results. "
             "Do NOT start analysis on this machine.", exit_now=False)
    else:
        print("[ok] pipeclean passed in %ss" % elapsed)


# ==========================================================================
# reporting
# ==========================================================================

REPORT_PATH = ROOT / "bootstrap-report.json"


def fail(report, phase, output, summary, exit_now=True):
    # type: (Dict[str, Any], str, str, str, bool) -> None
    causes = classify_failure(output)
    report["failures"].append({
        "phase": phase, "summary": summary,
        "likely_causes": causes,
        "output": output[-20000:],
    })
    report["phases"].setdefault(phase, {})["status"] = "failed"
    print("\n[FAIL] %s: %s" % (phase, summary))
    if causes:
        for c in causes:
            print("\n  likely cause: %s\n  what to do:   %s" % (c["id"], c["remedy"]))
    else:
        print("\n  This failure does not match any known cause. The full output is "
              "in the report.")
    if exit_now:
        finish(report, ok=False)


def finish(report, ok):
    # type: (Dict[str, Any], bool) -> None
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    bar = "=" * 70
    if ok:
        venv = report["phases"].get("sync", {}).get("venv", ".venv")
        activate = (venv + r"\Scripts\Activate.ps1" if IS_WINDOWS
                    else "source %s/bin/activate" % venv)
        print("\n%s\nEverything works. This environment matches uv.lock exactly and\n"
              "reproduced the known-good pipeline results.\n\n"
              "  corpus:   %s\n  activate: %s\n  report:   %s\n\n"
              "Next: docs/SETUP.md section 4.\n%s\n"
              % (bar, report["phases"].get("corpus", {}).get("path", "?"),
                 activate, REPORT_PATH, bar))
    else:
        print("\n%s\nSETUP DID NOT COMPLETE. Do not start analysis on this machine.\n\n"
              "Send this one file to Jez -- it has the full diagnosis, so nothing\n"
              "needs to be re-run or screenshotted:\n\n  %s\n%s\n"
              % (bar, REPORT_PATH, bar))
    sys.exit(0 if ok else 1)


# ==========================================================================

def main():
    # type: () -> None
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", type=Path, default=None, metavar="DIR",
                    help="where the corpus lives or should go (default: %s)"
                         % default_corpus_dir())
    ap.add_argument("--venv", type=Path, default=ROOT / ".venv", metavar="DIR",
                    help="environment directory (default: .venv)")
    ap.add_argument("--gpu", dest="gpu", action="store_const", const=True, default=None,
                    help="force-install the GPU extra")
    ap.add_argument("--no-gpu", dest="gpu", action="store_const", const=False,
                    help="never install the GPU extra")
    ap.add_argument("--skip-pipeclean", action="store_true",
                    help="set up only, do not verify (not recommended)")
    ap.add_argument("--diagnose-only", action="store_true",
                    help="write the environment report and stop; changes nothing")
    args = ap.parse_args()

    corpus_dir = (args.corpus or default_corpus_dir()).expanduser()
    explicit = args.corpus.expanduser() if args.corpus else None
    if explicit and explicit.name != "maildir":
        explicit = explicit / "maildir"
    if corpus_dir.name == "maildir":
        corpus_dir = corpus_dir.parent

    report = diagnose(corpus_dir)
    if args.diagnose_only:
        REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print("\n[ok] diagnosis written to %s (nothing was changed)" % REPORT_PATH)
        return

    want_gpu = report["gpu_usable"] if args.gpu is None else args.gpu
    if args.gpu and not report["gpu_usable"]:
        print("[warn] --gpu was forced but this machine looks unsuitable: %s"
              % report["gpu_note"])

    try:
        uv = ensure_uv(report)
        py = sync(uv, report, args.venv.expanduser().resolve(), want_gpu)
        maildir = ensure_corpus(explicit, corpus_dir, report, py)
    except SystemExit:
        raise  # fail() already wrote the report
    except BaseException:
        import traceback
        fail(report, "unexpected", traceback.format_exc(),
             "The setup script itself crashed. This is a bug in "
             "bootstrap-v2.py, not a problem with your machine.")

    if args.skip_pipeclean:
        print("[skip] pipeclean (--skip-pipeclean); the environment is NOT verified")
        report["phases"]["pipeclean"] = {"status": "skipped"}
    else:
        pipeclean(py, maildir, report)

    finish(report, ok=not report["failures"])


if __name__ == "__main__":
    main()
