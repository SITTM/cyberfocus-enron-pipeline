# Enron Pipeline — Getting Started

*For the three collaborators joining the Insider Language Index analysis.
No prior experience with this codebase assumed. Budget about an hour, most of
it waiting for a download.*

---

## What this project is

We are testing whether people who later turned out to be committing fraud
**wrote differently** from their colleagues — before anyone knew. The idea is
an "Insider Language Index": a measurable linguistic signature of insider
threat.

The Enron email corpus is the obvious place to try this. It is around half a
million real internal emails from 150 employees, released publicly by the US
Federal Energy Regulatory Commission during the investigation. Crucially, we
know what happened afterwards — who was indicted, who testified, who was
cleared. That gives us labels to test against, which almost no other email
dataset does.

This pipeline is the machinery that turns 500,000 raw email files into a table
of per-person linguistic measurements that we can run statistics on.

**Research partner:** University of Lancashire. The methodology is written up in
`docs/methodology-briefing.md` and has been circulated to academic partners for
comment.

---

## Where the code lives

https://github.com/SITTM/cyberfocus-enron-pipeline

**The repository is private.** Jez is sending you an invite — you'll need to
accept it before any link on this page will open, or before you can clone.

The two files worth reading directly:

- [scripts/bootstrap.ps1](https://github.com/SITTM/cyberfocus-enron-pipeline/blob/main/scripts/bootstrap.ps1) — the Windows setup script
- [scripts/bootstrap-v2.py](https://github.com/SITTM/cyberfocus-enron-pipeline/blob/main/scripts/bootstrap-v2.py) — the setup script it hands over to
  you run in step 2 below.
- [tests/test_smoke.py](https://github.com/SITTM/cyberfocus-enron-pipeline/blob/main/tests/test_smoke.py) — the check that your
  machine matches everyone else's.

These are linked rather than copied here on purpose: GitHub always shows the
current version, whereas a copy pasted into the page would silently go out of date.

## What we need from you

Get the pipeline running on your own machine and confirm it produces the same
numbers everyone else gets. That is genuinely the whole ask for today.

Why it matters that we all match: if your machine quietly produces different
results from mine, every comparison we make later is meaningless, and we
probably wouldn't notice for weeks. So the setup ends with an automatic check
against a known-good run.

**You do not need a powerful computer, and you do not need a graphics card.**
Any laptop from the last five years running Windows, macOS or Linux is fine.

---

## What the pipeline actually does

Five steps, run in order. Each one feeds the next.

**1. Ingest.** Reads the raw email files and pulls out the envelope information —
who sent it, who received it, when, what the subject was. Spots and discards
duplicate copies of the same message.

**2. Extract.** Separates what a person actually *wrote* from what they quoted,
forwarded, or attached as a signature. This matters enormously: if you don't
strip quoted text, you measure the writing style of whoever they replied to.

**3. Analyse.** Runs the authored text through a language model that counts words
and labels each word's grammatical role — noun, verb, adjective and so on. This
is the slow step, about three minutes for the test set.

**4. Annotate.** Produces a spreadsheet of the 500 most prolific senders, so a
human can review and correct who each person actually was. Automatic guesses
aren't good enough for the labels our conclusions depend on.

**5. Aggregate.** Rolls everything up to one row per person — their average word
count, average adjective use, and so on. This is the table the statistics will
eventually run on.

A deliberate design decision worth knowing: **the unit of analysis is the
person, not the email.** Someone who wrote 3,000 emails is one data point, not
3,000. Otherwise the loudest people in the company would dominate every result.

---

## Setting it up

### Before you start

- **On Windows: nothing. You do not need to install Python.** The setup script
  installs the exact Python this project needs, for this project only. It won't
  touch or conflict with any Python you already have.
- On Linux or macOS: any Python 3.12–3.14 to start the script off
  (`python3 --version`).
- **About 6 GB of free disk space.**
- A reasonable internet connection — there's roughly 700 MB to download.

### Step 1 — get the code

```
git clone <repo-url> cyberfocus-enron-pipeline
cd cyberfocus-enron-pipeline
```

### Step 2 — run one command

On Windows PowerShell:

```
powershell -ExecutionPolicy Bypass -File scripts\bootstrap.ps1
```

On Linux or macOS:

```
python3 scripts/bootstrap-v2.py
```

That is the entire setup. Go and do something else for an hour.

Behind the scenes it: reports what it finds on your machine, installs the right
Python if you haven't got one, builds an isolated
environment so this project's software can't interfere with anything else on
your machine, **looks for an Enron corpus you might already have and only
downloads the 423 MB archive if it can't find one**, unpacks it, checks all 150
employee mailboxes arrived intact, and then runs the full pipeline over four
mailboxes as a test.

**If it stops partway through, just run it again.** Every step it has already
completed is skipped, and a part-finished download picks up where it left off
rather than starting over. You cannot break anything by re-running it.

### Step 3 — confirm it worked

You're looking for this at the end:

```
====================================================================
Everything works. Your environment is verified against a known-good run.
====================================================================
```

If you see that, you're done. **If you don't see it, you are not set up** —
don't start any analysis. Send me whatever the terminal printed.

### Useful variations

| If... | Run |
|---|---|
| You already have the Enron corpus somewhere | add `--corpus /path/to/enron` — nothing gets downloaded |
| You want to see what it makes of your machine, changing nothing | add `--diagnose-only` — takes seconds, writes `bootstrap-report.json` |
| You have an NVIDIA graphics card | nothing to do — it is detected and used automatically. Optional; saves about two minutes |
| You want to re-check everything later | run the same command again — it skips to the verification |

(On Windows put these after `...\bootstrap.ps1`; on Linux/macOS after
`...\bootstrap-v2.py`.)

**Windows note:** let it use the default location, `C:\enron`. The email
archive has very deeply nested folders, and Windows has an old limit on how long
a file path can be. Unpacking it somewhere like your Documents folder can
silently lose files. The setup script checks for this and refuses to continue
rather than leaving you with a half-corpus.

---

## Running the pipeline yourself

The setup script proves the pipeline works, but throws its database away
afterwards. To keep one, activate the environment first — your prompt should
then show `(.venv)`:

```
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\Activate.ps1       # Windows
```

Tell it where the corpus is, and make the output folders:

```
export MAILDIR=~/data/enron/maildir      # Linux / macOS
$env:MAILDIR = "C:\enron\maildir"        # Windows
mkdir -p db annotations
```

Then run the five stages **in order** — each depends on the one before. All of
them are resumable, so re-running after a failure picks up where it stopped.

```
# 1. Ingest — headers into the database (~15 seconds)
python3 src/enron_ili/ingest.py \
    --db db/enron.sqlite --maildir "$MAILDIR" \
    --custodians skilling-j lay-k allen-p sanders-r

# 2. Extract — separate authored text from quoted/forwarded (~20 seconds)
python3 src/enron_ili/extract.py --db db/enron.sqlite --maildir "$MAILDIR"

# 3. Analyse — word and part-of-speech counts (~3 minutes)
python3 src/enron_ili/analyze.py --db db/enron.sqlite

# 4. Annotate — top-500 sender spreadsheet for manual review
python3 src/enron_ili/annotate.py \
    --db db/enron.sqlite --out annotations/top500.csv --top-n 500

# 5. Aggregate — per-person, per-role averages
python3 src/enron_ili/aggregate.py \
    --db db/enron.sqlite --out annotations/person_stats.csv
```

Add more names to the `--custodians` list in step 1 to widen the analysis —
there are 150 in the corpus. Stages 2–5 pick up the new emails automatically.

**Expected results on the four-custodian set** — if your numbers differ,
something is wrong, so please say so rather than pressing on:

- 20,439 emails
- 14,007 people
- 367,902 measurements
- `top500.csv` — 501 lines (a header plus 500 senders)
- `person_stats.csv` — 3,593 lines (a header plus 3,592 people)

## The most important thing on this page

**Everything the pipeline currently measures is a placeholder.**

Right now it counts words and parts of speech — how many nouns, how many verbs,
how many adjectives per email. That was chosen because it is fast, reliable and
proves the machinery works end to end. It was **not** chosen because it measures
insider threat, and there is no reason to think it does.

Equally: the output contains **no statistical tests at all**. It reports
averages. If you open the results and see that one group has a higher average
adjective count than another, the pipeline has told you nothing about whether
that difference is real, meaningful, or chance. Testing that is a later phase
with a specific design already written up — and it deliberately hasn't been
built yet, because the feature list has to be agreed and written down *before*
we test it, or the statistics don't hold up.

So: please don't read the current output as findings, and please don't share
screenshots of it as if it were. It's a working pipeline with dummy
measurements in it.

The technical detail on how to change what's measured is in
`docs/EXTENDING-ANALYSIS.md`. The short version is that the system was built so
that adding a new measurement costs one re-run of step 3 and nothing else — the
expensive work of reading and cleaning half a million emails is never repeated.

---

## Handling the data

This is real private correspondence from real people, most of whom did nothing
wrong and never consented to any of this.

**The code repository is public.** The data is not, and must never end up there.
Anything committed is visible to everyone instantly and permanently — deleting
it afterwards does not help, because forks and caches survive.

- **Keep the corpus and anything derived from it off shared drives, cloud sync
  folders and email.**
- **Never commit data to the repository.** It's configured to refuse.
  **Never use `git add -f`** — that flag overrides exactly the protection
  keeping personal data off a public page.
- Keep it on your machine, in the location the setup script chose.

---

## When something goes wrong

| What you see | What to do |
|---|---|
| `python3` or `py` "is not recognized" on Windows | Expected — you don't need either. Use the `bootstrap.ps1` command above |
| Windows says Python is installed, but nothing works | The `python.exe` on your PATH is probably the Microsoft Store placeholder, not Python. `bootstrap.ps1` ignores it and installs a real one |
| Someone tells you the pipeline needs Python 3.8 | It doesn't — that's the *spaCy* version, not a Python version. See `docs/python-version-requirements.md` |
| PowerShell says running scripts is disabled | The command above already includes `-ExecutionPolicy Bypass`, so use it exactly as written |
| The download stalls or fails | Run the command again — it resumes |
| "Extraction produced only N custodian directories" | The archive unpacked incompletely. On Windows this is the path-length problem — unpack to `C:\enron` |
| The smoke test fails on row counts | Something is genuinely different. Send me the output — **please don't edit the expected numbers to make it pass** |
| Anything else | Ask. Don't work around it quietly — a silent workaround on one machine is exactly the thing that makes our results incomparable |

---

## Reference

| Document | What's in it |
|---|---|
| `docs/SETUP.md` | The technical version of this page |
| `docs/EXTENDING-ANALYSIS.md` | How to change what the pipeline measures |
| `docs/methodology-briefing.md` | The research design — why the analysis is shaped the way it is |
| `docs/prior-work-survey.md` | What's already been published on this corpus |
| `.wolf/buglog.json` | Known problems and their fixes |

**Questions:** ask Jez.

---

*Published to ClickUp (NITRRO → Team Space → Team Docs) as "Enron Pipeline —
Getting Started":*
https://app.clickup.com/90122079853/v/dc/2kxv3kkd-92/2kxv3kkd-152

*Note: tables paste into ClickUp Docs with fixed narrow columns and become
unreadable for prose. The published version uses bold-led paragraphs and
bullets instead — keep it that way if you re-publish.*
