# Which Python does this pipeline actually need?

**Short answer: Python 3.12, 3.13 or 3.14. Not 3.8. Nothing here needs 3.8.**

If you have been told the pipeline needs "Python 3.8.3", that is a
misunderstanding — and following it would break things, not fix them. This page
explains where the number came from and what the real constraints are.

---

## Where "3.8" came from

`requirements.txt` contains these two lines:

```
en_core_web_sm @ .../en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
spacy==3.8.16
```

and `en_core_web_sm`'s own README says:

| | |
|---|---|
| **Version** | `3.8.0` |
| **spaCy** | `>=3.8.0,<3.9.0` |

Every `3.8` on this page so far is a **spaCy version**. spaCy 3.8 is the current
release series of the NLP library. It has nothing to do with CPython 3.8, which
is a language release from 2019 that reached end of life in October 2024.

That last table row — `spaCy >=3.8.0,<3.9.0` — is the line most often misread as
a Python requirement. It is the model saying which *spaCy* it was trained
against.

## The real constraints

Taken from the packages' own metadata:

| Package | `Requires-Python` | Sets |
|---|---|---|
| `spacy 3.8.16` | `>=3.9,<3.15` | the **upper** bound: 3.14 is the newest allowed |
| `numpy 2.5.3` | `>=3.12` | the **lower** bound: 3.12 is the oldest allowed |
| `blis`, `cymem`, `preshed`, `murmurhash` | `<3.15` | agree with spaCy |
| `cupy-cuda12x 14.2.0` (optional GPU) | `>=3.10` | not binding |

Intersecting those gives the supported window:

> **Python 3.12 – 3.14.** `pyproject.toml` declares exactly this:
> `requires-python = ">=3.12,<3.15"`.

Python 3.14 — the version several of us already run — is fully supported. There
is no reason to downgrade, and downgrading to 3.8 is impossible anyway: `numpy`
would refuse to install.

## "But I got a compiler error / a wheel error"

That is a real problem, but it is not a Python-version problem. Every compiled
dependency in this pipeline publishes a ready-built **Windows wheel for Python
3.14** (`cp314-cp314-win_amd64`) — verified for `spacy`, `thinc`, `blis`,
`murmurhash`, `cymem`, `preshed`, `srsly`, `numpy`, `pydantic-core` and
`cupy-cuda12x`. Nothing needs to be compiled on your machine, and no Visual C++
build tools are required.

The only dependency without a wheel is `quotequail`, which is pure Python (no C
code at all), so it installs without a compiler too.

If pip tried to *compile* something, it means it could not find a matching
wheel — usually because it was run against an unsupported or 32-bit interpreter.
The fix is to use the right interpreter, not an older one.

## What actually goes wrong, and the fix

The real causes we have seen are:

- several Pythons installed, and the wrong one being picked up off `PATH`
- `pip` installing into a different interpreter than the one running the code
- a 32-bit Python
- transitive dependencies drifting between machines, because `requirements.txt`
  pinned only 5 direct packages while the full chain is 50
- on Windows, the 260-character path limit silently truncating the corpus

**`scripts/bootstrap-v2.py` removes all five.** It installs
[uv](https://docs.astral.sh/uv/), has uv download the exact CPython 3.14 this
project wants — so whatever Python is already on your machine stops mattering
entirely — and installs the fully pinned set from `uv.lock`, all 50 packages
with hashes. It then runs the real pipeline end to end and checks the output
against known-good numbers.

```bash
py scripts\bootstrap-v2.py          # Windows
python3 scripts/bootstrap-v2.py     # Linux / macOS
```

To see what it thinks of your machine without changing anything:

```bash
py scripts\bootstrap-v2.py --diagnose-only
```

That writes `bootstrap-report.json`, listing every interpreter it can find, your
GPU, disk, network reachability and (on Windows) whether long paths are enabled.
Send that file if you get stuck — it is designed to be the only thing you need
to send.
