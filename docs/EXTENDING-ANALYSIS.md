# Changing what the pipeline measures

Everything the pipeline currently computes is a **placeholder**. This document
explains what is a placeholder, why, and how to replace each part without
breaking the work already done.

Read `docs/methodology-briefing.md` first — it specifies what the analysis is
*supposed* to be. This document is only about how to get there in code.

---

## 1. What is currently a placeholder

There are two separate things, and they are at different stages.

### 1a. The feature set — a placeholder, and marked as one

`analyze.py` currently measures, per email:

- `word_count` — non-punctuation tokens
- `pos_ADJ`, `pos_NOUN`, `pos_VERB`, … — counts for each of the 17 Universal
  POS tags

That is a stand-in. It was chosen because it is cheap, deterministic and
exercises the whole pipeline end to end — **not** because it measures insider
language. The real ILI feature list is to be pre-specified separately
(methodology briefing §8, and §9 on pre-specification).

It is labelled in code: `FEATURE_VERSION = "v2-placeholder"` in
`src/enron_ili/analyze.py`.

### 1b. The statistics — not placeholders, absent

`aggregate.py` computes **descriptive statistics only**: the per-person mean of
each feature, grouped by role. There are no significance tests, no
cross-validation, no confidence intervals and no multiple-comparison
correction anywhere in the codebase.

This is deliberate and matches the stated scope — the briefing note says Phase 1
is "static, descriptive statistical analysis only". But it means that if someone
opens `person_stats.csv` and sees that one role has a higher mean adjective
count than another, **the pipeline has not told them whether that difference is
real.** Nothing in the current output supports an inferential claim.

The inferential design that has to be built is specified in the briefing note:
person-disjoint splitting (§5), repeated stratified group k-fold (§6),
label-permutation testing (§6), the metric set (§7), and Benjamini–Hochberg
correction over a pre-specified test list (§9).

---

## 2. The mechanism that makes changes safe

Two design decisions in the schema do the heavy lifting. Understanding them is
the whole job.

**Features are stored long, not wide.** The `feature` table holds one row per
`(email_id, feature_set_version, feature_name, value)`. A new feature is
therefore *new rows*, never a schema migration. You can add twenty features
without an `ALTER TABLE`.

**Stage completion is versioned.** `stage_status` is keyed on
`(email_id, stage, version)`. Each stage only processes emails that don't
already have a `done` row at the current version. So bumping the version of one
stage re-queues exactly that stage, and leaves the expensive upstream work —
parsing 500,000 files, extracting authored text — untouched.

Together these mean: **changing the feature set costs one re-run of `analyze.py`
and nothing else.** Old feature rows stay in the database under their old
version label, so you can compare old and new side by side, and roll back by
passing the old version string to `aggregate.py`.

---

## 3. How to add or change a feature

Three steps, in `src/enron_ili/analyze.py`.

**Step 1 — write the measurement.** Add it to `features_for_doc()`, which
receives one spaCy `Doc` (one email's authored text) and returns a dict of
`{feature_name: float}`. For example, a first-person pronoun rate:

```python
def features_for_doc(doc) -> dict[str, float]:
    ...
    # existing word_count and POS counts ...
    first_person = sum(
        1 for tok in doc
        if tok.pos_ == "PRON" and tok.lower_ in {"i", "me", "my", "mine", "myself"}
    )
    feats["first_person_rate"] = first_person / word_count if word_count else 0.0
    return feats
```

Keep every value a `float` — the `value` column is numeric, and downstream
aggregation takes means.

**Step 2 — bump the version.** In the same file:

```python
FEATURE_VERSION = "v3-ili-draft"    # was "v2-placeholder"
```

Use a name that says what the set *is*. This string ends up in the database and
is how anyone later works out which numbers came from which definition.

**Step 3 — re-run analysis and aggregation.**

```bash
python3 src/enron_ili/analyze.py --db db/enron.sqlite
python3 src/enron_ili/aggregate.py --db db/enron.sqlite \
    --out annotations/person_stats.csv --feature-set-version v3-ili-draft
```

`analyze.py` will report the number of emails it needs to process — it should be
all of them, since none have a `done` row at the new version.

> **Watch this:** `aggregate.py`'s `--feature-set-version` default is a literal
> string that must be kept in step with `analyze.FEATURE_VERSION`. A stale
> default there caused a real bug (`.wolf/buglog.json`, bug-003) where stage 5
> silently produced nothing. It now exits with an error and lists the versions
> actually present, rather than writing an empty file — but **update the default
> when you bump the version.**

**Step 4 — update the smoke test.** `tests/test_smoke.py` asserts an exact
feature row count (`367902` = 20,439 emails × 18 features). Changing the number
of features changes that number. Work out the new expected count, put it in, and
re-run — don't just delete the assertion. If the count is not what you predicted,
that is the test doing its job.

Some features need parts of the spaCy pipeline that are currently switched off
for speed:

```python
nlp = spacy.load("en_core_web_sm", exclude=["ner", "lemmatizer", "parser"])
```

Lemmas, dependency parses and named entities are all unavailable as written.
Remove the relevant name from `exclude` if you need one — expect analysis to get
several times slower, particularly with the parser.

---

## 4. How to add the inferential statistics

This is new work, not an edit. The recommended shape:

**Put it in a new module, not in `aggregate.py`.** `aggregate.py` produces the
person-level table — that is a clean input to statistics, and it should stay a
pure descriptive roll-up. A new `src/enron_ili/model.py` (or an analysis
notebook reading `person_stats.csv`) keeps the separation.

**The unit of analysis is the person, not the email** (briefing §4). The
person-level CSV is already the right grain. Any test that treats emails as
independent observations is wrong — one person writing 3,000 emails is one data
point, not 3,000.

**Splitting must be person-disjoint** (briefing §5). Never use a random split
over emails: the same individual would appear in both sides and the model would
learn their idiolect rather than anything generalisable. The briefing specifies
repeated stratified *group* k-fold, grouped on `person_id`.

**A label-permutation test is treated as essential, not optional** (briefing §6),
because the positive classes are small — permute person-level labels through the
complete pipeline, 10,000 times, and compare the observed statistic to that null
distribution.

**Correct for multiple comparisons** (briefing §9) using Benjamini–Hochberg over
a test list pre-specified *before* looking at the test set.

This will need `scipy` and probably `scikit-learn` and `pandas`, none of which
are currently dependencies. Add them to `requirements.txt` and re-run
`scripts/bootstrap.py` on every machine.

**Before writing any of this, resolve the open questions in briefing §12** —
particularly the annotation evidence standard and the seniority confound. Those
are methodology decisions with academic partners, not implementation details,
and building the statistics before they are settled will mean rebuilding them.

---

## 5. Checklist

Before treating any new numbers as results:

- [ ] `FEATURE_VERSION` bumped to a descriptive name
- [ ] `aggregate.py`'s `--feature-set-version` default updated to match
- [ ] Expected feature count in `tests/test_smoke.py` recalculated
- [ ] `python3 scripts/bootstrap.py` passes on a clean machine
- [ ] The feature list was pre-specified in writing *before* it was run against
      labelled data (briefing §9) — otherwise the multiple-comparison correction
      is not valid and the result is exploratory, not confirmatory
