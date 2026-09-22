"""One-command setup for the Enron ILI pipeline.

Stdlib only, so it runs on a clean machine before anything is installed.
Works on Linux, macOS and Windows, with or without a GPU.

    python3 scripts/bootstrap.py              # Windows: py -3 scripts\\bootstrap.py

It does four things, in order, and each one is skipped if already done:

    1. create .venv and install dependencies
    2. find the Enron corpus, or download and extract it
    3. run the end-to-end smoke test (~4 min)
    4. print what to do next

Re-running it is safe and cheap. It never re-downloads a corpus it can
already find, and never re-extracts a complete one.
"""
import argparse
import functools
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

print = functools.partial(print, flush=True)  # keep output ordered against pip's

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
MIN_PY = (3, 11)
MAX_PY = (3, 13)  # inclusive

CORPUS_URL = "https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz"
TARBALL = "enron_mail_20150507.tar.gz"
EXPECTED_CUSTODIANS = 150


# --------------------------------------------------------------------------
# environment
# --------------------------------------------------------------------------

def venv_python() -> Path:
    if sys.platform == "win32":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def check_python() -> None:
    v = sys.version_info[:2]
    if not (MIN_PY <= v <= MAX_PY):
        sys.exit(
            f"Python {v[0]}.{v[1]} is not supported. Install Python "
            f"{MIN_PY[0]}.{MIN_PY[1]}-{MAX_PY[0]}.{MAX_PY[1]} and re-run with "
            f"that interpreter."
        )
    print(f"[ok] Python {v[0]}.{v[1]}")


def make_venv() -> None:
    if venv_python().exists():
        print(f"[skip] venv already exists at {VENV}")
        return
    print(f"[..] creating venv at {VENV}")
    subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    print("[ok] venv created")


def deps_already_installed() -> bool:
    probe = "import quotequail, spacy; spacy.load('en_core_web_sm')"
    return subprocess.run(
        [str(venv_python()), "-c", probe],
        capture_output=True,
    ).returncode == 0


def install(gpu: bool) -> None:
    if not gpu and deps_already_installed():
        print("[skip] dependencies already installed")
        return
    req = ROOT / ("requirements-gpu.txt" if gpu else "requirements.txt")
    py = str(venv_python())
    subprocess.run([py, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    print(f"[..] installing from {req.name} (~250MB of wheels, a few minutes)")
    subprocess.run([py, "-m", "pip", "install", "-r", str(req)], check=True)
    check = (
        "import quotequail, spacy; "
        "spacy.load('en_core_web_sm', exclude=['ner','lemmatizer','parser'])"
    )
    subprocess.run([py, "-c", check], check=True)
    print("[ok] dependencies installed and verified")


# --------------------------------------------------------------------------
# corpus
# --------------------------------------------------------------------------

def custodian_count(maildir: Path) -> int:
    if not maildir.is_dir():
        return 0
    return sum(1 for p in maildir.iterdir() if p.is_dir())


def is_complete(maildir: Path) -> bool:
    return custodian_count(maildir) >= EXPECTED_CUSTODIANS


def default_corpus_dir() -> Path:
    if sys.platform == "win32":
        # Short path on purpose: the maildir tree is deep enough to hit the
        # 260-character path limit under a long parent like Documents.
        return Path("C:/enron")
    return Path.home() / "data" / "enron"


def candidate_maildirs(explicit: Path | None) -> list[Path]:
    """Places to look for an already-downloaded corpus, best guess first."""
    seen, out = set(), []
    raw = [
        explicit,
        Path(os.environ["ENRON_MAILDIR"]) if os.environ.get("ENRON_MAILDIR") else None,
        default_corpus_dir() / "maildir",
        Path.home() / "data" / "enron" / "maildir",
        Path("C:/enron/maildir") if sys.platform == "win32" else None,
        ROOT / "maildir",
    ]
    for p in raw:
        if p is None:
            continue
        p = p.expanduser()
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def find_corpus(explicit: Path | None) -> Path | None:
    """Return an existing, complete maildir, or None. Never downloads."""
    partial = []
    for path in candidate_maildirs(explicit):
        n = custodian_count(path)
        if n == 0:
            continue
        if n >= EXPECTED_CUSTODIANS:
            print(f"[skip] found existing corpus at {path} ({n} custodians)")
            return path
        partial.append((path, n))

    for path, n in partial:
        print(
            f"[warn] {path} looks incomplete: {n} custodian directories, "
            f"expected {EXPECTED_CUSTODIANS}. Ignoring it."
        )
        if sys.platform == "win32":
            print("[warn]   On Windows this is usually the 260-char path limit. "
                  "Re-extract to a short path such as C:\\enron.")
    return None


def download(url: str, dest: Path) -> None:
    """Download with resume, so an interrupted 423MB fetch is not restarted."""
    part = dest.with_suffix(dest.suffix + ".part")
    have = part.stat().st_size if part.exists() else 0

    req = urllib.request.Request(url)
    if have:
        print(f"[..] resuming download at {have / 1e6:.0f}MB")
        req.add_header("Range", f"bytes={have}-")

    with urllib.request.urlopen(req) as resp:
        resuming = resp.status == 206
        if have and not resuming:
            print("[warn] server ignored resume request; starting over")
            have = 0
        total = int(resp.headers.get("Content-Length", 0)) + (have if resuming else 0)
        mode = "ab" if (have and resuming) else "wb"
        done = have if resuming else 0
        with part.open(mode) as f:
            while chunk := resp.read(1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total:
                    print(f"\r    {done / 1e6:>6.0f} / {total / 1e6:.0f} MB "
                          f"({done * 100 // total}%)", end="")
        print()
    part.rename(dest)


def ensure_corpus(explicit: Path | None, corpus_dir: Path) -> Path:
    found = find_corpus(explicit)
    if found:
        return found

    maildir = corpus_dir / "maildir"
    corpus_dir.mkdir(parents=True, exist_ok=True)
    tarball = corpus_dir / TARBALL

    if tarball.exists():
        print(f"[skip] tarball already downloaded: {tarball} "
              f"({tarball.stat().st_size / 1e6:.0f}MB)")
    else:
        free = shutil.disk_usage(corpus_dir).free
        if free < 6e9:
            sys.exit(
                f"Only {free / 1e9:.1f}GB free at {corpus_dir}; the corpus needs "
                f"about 6GB (tarball + extracted tree). Free some space or pass "
                f"--corpus with a roomier location."
            )
        print(f"[..] downloading the corpus (~423MB) to {tarball}")
        print(f"     source: {CORPUS_URL}")
        download(CORPUS_URL, tarball)
        print("[ok] downloaded")

    print(f"[..] extracting to {maildir} (a few minutes, ~2.6GB)")
    with tarfile.open(tarball) as tf:
        # filter="data" refuses absolute paths and traversal outside the
        # destination. It is the default from 3.14; set it for 3.11-3.13.
        tf.extractall(corpus_dir, filter="data")

    n = custodian_count(maildir)
    if n < EXPECTED_CUSTODIANS:
        sys.exit(
            f"Extraction produced only {n} custodian directories, expected "
            f"{EXPECTED_CUSTODIANS}. The corpus is incomplete -- see the "
            f"path-length note in docs/SETUP.md. Not continuing."
        )
    print(f"[ok] corpus ready at {maildir} ({n} custodians)")
    print(f"     you can delete {tarball} to reclaim ~423MB")
    return maildir


# --------------------------------------------------------------------------
# verification
# --------------------------------------------------------------------------

def run_smoke_test(maildir: Path) -> None:
    print("[..] running the end-to-end smoke test (~4 minutes, be patient)")
    env = {**os.environ, "ENRON_MAILDIR": str(maildir)}
    r = subprocess.run(
        [str(venv_python()), "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=ROOT, env=env,
    )
    if r.returncode != 0:
        sys.exit(
            "\nThe smoke test FAILED. The environment is not ready -- do not "
            "start analysis.\nSend the output above to Jez; see the "
            "troubleshooting table in docs/SETUP.md first."
        )
    print("[ok] smoke test passed")


def next_steps(maildir: Path, verified: bool) -> None:
    activate = (r".venv\Scripts\Activate.ps1" if sys.platform == "win32"
                else "source .venv/bin/activate")
    headline = (
        "Everything works. Your environment is verified against a known-good run."
        if verified else
        "Setup complete, but NOT verified -- you skipped the smoke test.\n"
        "Run it before trusting any results: python3 scripts/bootstrap.py"
    )
    print(
        f"\n{'=' * 68}\n"
        f"{headline}\n\n"
        f"  corpus:   {maildir}\n"
        f"  activate: {activate}\n\n"
        f"Read docs/SETUP.md section 4 to run the pipeline on your own data,\n"
        f"and docs/EXTENDING-ANALYSIS.md to change what is measured.\n"
        f"{'=' * 68}\n"
    )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--corpus", type=Path, default=None, metavar="DIR",
        help="where the corpus lives, or should be downloaded to "
             f"(default: {default_corpus_dir()})",
    )
    ap.add_argument(
        "--gpu", action="store_true",
        help="also install cupy-cuda12x (NVIDIA + CUDA 12.x only; not required)",
    )
    ap.add_argument(
        "--skip-smoke-test", action="store_true",
        help="set up only, don't verify (not recommended)",
    )
    args = ap.parse_args()

    corpus_dir = (args.corpus or default_corpus_dir()).expanduser()
    # --corpus may name either the parent directory or the maildir itself.
    explicit = args.corpus.expanduser() if args.corpus else None
    if explicit and explicit.name != "maildir":
        explicit = explicit / "maildir"
    if corpus_dir.name == "maildir":
        corpus_dir = corpus_dir.parent

    check_python()
    make_venv()
    install(args.gpu)
    maildir = ensure_corpus(explicit, corpus_dir)
    if args.skip_smoke_test:
        print("[skip] smoke test (--skip-smoke-test)")
    else:
        run_smoke_test(maildir)
    next_steps(maildir, verified=not args.skip_smoke_test)


if __name__ == "__main__":
    main()
