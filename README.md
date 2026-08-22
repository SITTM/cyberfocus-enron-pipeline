# CyberFocus / Insider Language Index — Enron pipeline

Pipeline analysing the Enron email corpus for the Insider Language Index (ILI)
research project with the University of Lancashire. See `docs/` for the
methodology briefing and prior-work survey circulated to academic partners.

**No data ships with this repo.** The corpus lives outside the working tree
at `/home/jez/data/enron/` and is never committed (`.gitignore`).

## Pipeline stages

Run in order; each is idempotent and resumable via `stage_status`.

```
1. ingest.py     maildir -> email/person/recipient rows, dedup on Message-ID
2. extract.py    split authored text from quoted/forwarded text
3. analyze.py    spaCy -> word count + POS counts (placeholder feature set)
4. annotate.py   generate top-N sender CSV for manual role review
5. aggregate.py  roll features up to per-person, per-role means
```

## Usage

```
source .venv/bin/activate

python3 src/enron_ili/ingest.py \
    --db db/enron.sqlite --maildir /home/jez/data/enron/maildir \
    --custodians skilling-j lay-k allen-p sanders-r   # or all 150

python3 src/enron_ili/extract.py \
    --db db/enron.sqlite --maildir /home/jez/data/enron/maildir

python3 src/enron_ili/analyze.py --db db/enron.sqlite --n-process 28

python3 src/enron_ili/annotate.py \
    --db db/enron.sqlite --out annotations/top500.csv --top-n 500

python3 src/enron_ili/aggregate.py \
    --db db/enron.sqlite --out annotations/person_stats.csv
```

## Design notes

- `feature` is long-format (`email_id, feature_set_version, feature_name, value`).
  A new feature is a new row, not a schema migration.
- `stage_status` is keyed on `(stage, version)`. Bumping the analysis feature
  set version re-queues analysis without touching parsing or extraction.
- No `split` column on `person`: evaluation uses repeated stratified group
  k-fold generated at analysis time from role labels (see docs/methodology-briefing.md §6).
- Role default: `enron.com` domain -> Employee, external -> Other. Named
  figures and the top-500 senders are manually reviewed (see `annotate.py`).

## Known limitations (see docs/prior-work-survey.md and troubleshooting.log)

- Body extraction (quotequail + a supplementary Lotus Notes regex) is a
  heuristic, not a validated parser. Precision/recall against a hand-annotated
  sample has not yet been measured.
- The Whistleblower role is not a viable statistical group: Sherron Watkins
  is not a custodian and authored only 7 messages in the whole corpus.
