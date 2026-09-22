# Setup — running the Enron ILI pipeline on your machine

**One command does all of it.** This page exists for when that command needs
explaining, or when it fails.

Target: a verified environment on Linux, macOS or Windows. **A GPU is not
required.** Allow 45–60 minutes, nearly all of it downloading the corpus.

---

## 0. What you need

| | Requirement |
|---|---|
| OS | Linux, macOS, or Windows 10/11 |
| Python | 3.11, 3.12, 3.13 or 3.14 — check with `python3 --version` (Windows: `py -3 --version`) |
| Disk | **~6 GB free**: 0.5 GB tarball + 2.6 GB corpus + 0.2 GB venv + ~0.1 GB working database |
| RAM | 8 GB comfortable; 4 GB works |
| Network | ~700 MB of downloads |
| GPU | **Not needed.** Only relevant if you have an NVIDIA card — see the end. |

No Python? Install it from [python.org/downloads](https://www.python.org/downloads/).
On Windows, tick **"Add python.exe to PATH"** in the installer.

---

## 1. Get the code

```bash
git clone <repo-url> cyberfocus-enron-pipeline
cd cyberfocus-enron-pipeline
```

Everything below runs from this directory.

---

## 2. Run the bootstrap

```powershell
# Windows (PowerShell) -- works even if you have no Python at all
powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
```

```bash
# Linux / macOS
python3 scripts/bootstrap-v2.py
```

That is the whole setup.

> **Windows: use `bootstrap.ps1`, not `py`.** Two things routinely go wrong on a
> fresh Windows machine, and we reproduced both on a clean Windows 11 VM:
>
> * **`py` often doesn't exist.** The `py` launcher ships only with the
>   python.org installers, not the Microsoft Store package.
> * **`python.exe` on your PATH is probably not Python.** Windows ships an "App
>   Execution Alias" stub at
>   `%LOCALAPPDATA%\Microsoft\WindowsApps\python.exe`. Running it opens the
>   Microsoft Store. It looks like Python is installed when nothing is.
>
> `bootstrap.ps1` sidesteps both. `uv` is a single native binary that needs no
> Python, so it is installed first and then installs a real CPython 3.14 for
> you. **You do not need to install Python yourself.**

> **Hitting dependency errors?** Use `bootstrap-v2.py` above, not the older
> `bootstrap.py`. v2 installs [uv](https://docs.astral.sh/uv/), has uv download
> the exact CPython 3.14 this project needs — so whichever Python you already
> have stops mattering — and installs all 50 packages pinned in `uv.lock`
> rather than the 5 that `requirements.txt` pins. That combination is what
> fixes "works on your machine but not mine".
>
> **You do not need Python 3.8.** If someone has told you that, see
> [docs/python-version-requirements.md](python-version-requirements.md): `3.8`
> in `requirements.txt` is the *spaCy* version. The real window is Python
> 3.12–3.14, and 3.14 is fine.

`bootstrap-v2.py`:

1. **diagnoses your machine** — every Python it can find, your GPU, free disk,
   network reachability, proxy settings, and (Windows) whether long paths are
   enabled
2. installs `uv` if you don't have it — one user-local binary, no admin rights
3. installs CPython 3.14 and the locked dependency set (~250 MB)
4. **looks for an Enron corpus you already have** — and only downloads the
   423 MB archive if it can't find a complete one
5. extracts it and confirms all 150 custodian directories are present
6. runs the **pipeclean run**: the full five-stage pipeline over four
   custodians, ~20,000 emails, about 4 minutes on CPU
7. writes `bootstrap-report.json` and tells you whether it worked

**If anything fails, it does not just dump a traceback.** It matches the failure
against known causes — missing wheels, TLS interception by a corporate proxy,
the Windows path limit, out of disk, out of memory, an old GPU driver — prints
the specific remedy, and writes everything to `bootstrap-report.json`. Send that
one file; nothing else needs screenshotting.

Want to know what it thinks of your machine without changing anything?

```powershell
powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1 --diagnose-only
```

### The older bootstrap.py

`scripts/bootstrap.py` is the original venv + pip path. It still works and is
kept as a fallback for a machine that cannot install uv at all. It:

1. checks your Python version
2. creates `.venv` and installs the dependencies (~250 MB of packages)
3. **looks for an Enron corpus you already have** — and only downloads the
   423 MB archive if it can't find a complete one
4. extracts it and confirms all 150 custodian directories are present
5. runs the end-to-end smoke test — the full five-stage pipeline over four
   custodians, ~20,000 emails, about 4 minutes on CPU
6. tells you it worked

**It is safe to re-run.** Every step is skipped if already done, so if it dies
partway through — a dropped connection during the download, say — just run it
again. A part-finished download resumes rather than starting over.

It finishes with `Everything works. Your environment is verified against a
known-good run.` **If you don't see that line, you are not set up.** Don't start
analysis; see [Troubleshooting](#troubleshooting).

### Useful flags

These work on `bootstrap-v2.py`:

| Flag | Use |
|---|---|
| `--corpus DIR` | Corpus lives somewhere else, or you want it downloaded somewhere specific. Defaults to `~/data/enron` (`C:\enron` on Windows). |
| `--diagnose-only` | Report on your machine and stop. Changes nothing. |
| `--gpu` / `--no-gpu` | Force the GPU extra on or off. Default: install it only if a suitable NVIDIA GPU is detected. The GPU is never required. |
| `--venv DIR` | Put the environment somewhere other than `.venv`. |
| `--skip-pipeclean` | Set up without verifying. Not recommended. |

`bootstrap.py` takes `--corpus`, `--gpu` and `--skip-smoke-test`.

> **Already have the corpus?** Point at it and nothing is downloaded:
> `python3 scripts/bootstrap-v2.py --corpus /path/to/enron`
> The bootstrap also checks `$ENRON_MAILDIR`, `~/data/enron/maildir`,
> `C:\enron\maildir` and `./maildir` automatically.

> **Windows PowerShell refuses to run scripts?** Run once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

> **Windows: extraction is slow — expect 1–3 hours.** The corpus is ~500,000
> very small files, and creating that many is simply slow on Windows. Progress
> is printed every 60 seconds so you can see it is not stuck. (Measured in a
> Windows 11 VM with Defender switched off, so this is the floor, not an
> antivirus problem; a physical machine with an SSD should do better.)
>
> If your antivirus does real-time scanning — most do — it will add to that.
> Excluding the corpus folder first, in an admin PowerShell, can help:
> `Add-MpPreference -ExclusionPath 'C:\enron'`. The corpus is public research
> data, but skip this if your organisation's policy says not to. If that command
> returns error `0x800106ba`, Defender is not running on your machine and there
> is nothing to exclude.

> **Windows: keep the corpus path short**, e.g. `C:\enron`. The maildir tree is
> deeply nested, and extracting under a long path (like your Documents folder)
> can breach the 260-character path limit and silently lose files. The bootstrap
> checks for this and refuses to continue rather than leaving you with a partial
> corpus.

---

## 3. Running the pipeline yourself

The bootstrap proves the pipeline works, but throws its database away. To keep
one, activate the environment first:

```bash
source .venv/bin/activate          # Linux / macOS
.venv\Scripts\Activate.ps1         # Windows
```

Your prompt should now show `(.venv)`. Set the corpus location and create the
output directories:

```bash
export MAILDIR=~/data/enron/maildir        # Linux / macOS
$env:MAILDIR = "C:\enron\maildir"          # Windows
mkdir -p db annotations
```

Then run the five stages **in order** — each depends on the one before. All are
idempotent and resumable, so re-running after a failure picks up where it
stopped.

```bash
# 1. Ingest — headers into SQLite (~15 s)
python3 src/enron_ili/ingest.py \
    --db db/enron.sqlite --maildir "$MAILDIR" \
    --custodians skilling-j lay-k allen-p sanders-r

# 2. Extract — separate authored text from quoted/forwarded (~20 s)
python3 src/enron_ili/extract.py --db db/enron.sqlite --maildir "$MAILDIR"

# 3. Analyze — spaCy word counts and POS counts (~3 min on CPU)
python3 src/enron_ili/analyze.py --db db/enron.sqlite

# 4. Annotate — top-500 sender CSV for manual role review (seconds)
python3 src/enron_ili/annotate.py \
    --db db/enron.sqlite --out annotations/top500.csv --top-n 500

# 5. Aggregate — per-person, per-role means (seconds)
python3 src/enron_ili/aggregate.py \
    --db db/enron.sqlite --out annotations/person_stats.csv
```

Add more custodians to stage 1 to widen the analysis — there are 150 in total.
Stages 2–5 then pick up the new emails automatically on the next run.

`--device cpu` is the default for stage 3, so that command is correct whether or
not you have a GPU.

### Expected output on the four-custodian set

| | |
|---|---|
| emails | 20,439 |
| people | 14,007 |
| features | 367,902 |
| `top500.csv` | 501 lines (header + 500) |
| `person_stats.csv` | 3,593 lines (header + 3,592 people) |

---

## 4. Re-verifying later

After changing anything, or if results look odd:

```bash
python3 scripts/bootstrap.py
```

It skips straight to the smoke test if everything else is in place. You can also
run the test directly:

```bash
ENRON_MAILDIR=~/data/enron/maildir python3 -m unittest discover -s tests -v
```

---

## Optional: GPU acceleration

Only for **NVIDIA** GPUs with a CUDA 12.x driver. Apple Silicon, AMD and Intel
GPUs are not supported — use CPU.

```bash
python3 scripts/bootstrap.py --gpu
python3 src/enron_ili/analyze.py --db db/enron.sqlite --device gpu
```

This speeds up stage 3 only, and on the smoke test the saving is a couple of
minutes. **Not worth troubleshooting a CUDA install for.** If `--device gpu`
errors, drop the flag.

---

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `python3: command not found` (Windows) | Use `py -3` or `python`. |
| `running scripts is disabled on this system` | PowerShell execution policy — see section 2. |
| *"Python 3.x is not supported"* | Install Python 3.11–3.14 and re-run with that interpreter. |
| Download stalls or fails | Just re-run the bootstrap; it resumes from where it stopped. |
| *"Extraction produced only N custodian directories"* | Incomplete extraction — on Windows, almost always the path-length limit. Re-extract to `C:\enron`. |
| `ModuleNotFoundError: No module named 'spacy'` | The venv isn't active. Re-run the activate command; your prompt should show `(.venv)`. |
| `no such table: email` | Stage 1 was skipped, or `--db` points at a different file than the earlier stage used. |
| `Analysing 0 email(s)` | Stage 2 hasn't run successfully against this database. |
| `aggregate.py: no features found for version ...` | Stage 3 hasn't run, or the feature-set version doesn't match. The error lists the versions actually present. |
| `cupy` / CUDA errors | Drop `--device gpu`. CPU is the supported default. |
| Smoke test fails on row counts | Corpus is incomplete, or the pipeline's behaviour has genuinely changed. Send the output to Jez — don't edit the expected numbers. |
| Anything else | Check `troubleshooting.log` and `.wolf/buglog.json`, then ask. Don't work around it silently. |

---

## Handling note

**This repository is public.** Anything committed here is visible to the entire
internet, immediately and permanently — a later deletion does not undo it,
because forks, clones and caches survive.

The corpus is real personal correspondence from real people, most of whom did
nothing wrong. Keep it, and any `.sqlite` or `.csv` derived from it, **out of
the repo and off shared drives**. `.gitignore` already excludes `db/`,
`annotations/*.csv` and `maildir/`.

**Never use `git add -f` in this repository.** That flag exists to override
exactly the protection that is keeping personal data off a public page. If you
think you need it, you don't — ask first.

---

## Where to go next

- `docs/EXTENDING-ANALYSIS.md` — how to change what the pipeline measures.
  **Everything it currently measures is a placeholder**; read this before
  interpreting any output as a finding.
- `docs/methodology-briefing.md` — the research design these numbers are meant
  to serve.
