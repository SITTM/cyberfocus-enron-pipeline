# Insider Language Index — Methodology Briefing Note

**For:** academic partners, University of Lancashire
**From:** CyberFocus / SITTM
**Status:** Draft for comment — Phase 1 (descriptive statistics) design
**Date:** 22 August 2026

---

## 1. Purpose of this note

This note sets out the proposed experimental design for the **Insider Language Index (ILI)**, a method
to identify organisational insiders — specifically individuals who committed fraud — from their
language use in corporate email. It is circulated for methodological comment **before** any analysis
is run, so that the design can be criticised while it is still cheap to change.

It covers the corpus, the unit of analysis, the evaluation design, the statistical controls, and the
known threats to validity. It deliberately does **not** propose specific linguistic features; the
feature list is to be pre-specified separately (see §8).

A note on scope: Phase 1 is **static, descriptive statistical analysis only**. No predictive model is
trained in Phase 1. Predictive modelling is a Phase 2 item, and several design choices below are made
now specifically so that Phase 2 remains methodologically available later.

---

## 2. Corpus and provenance

We use the CMU CALO release of the Enron email corpus, `enron_mail_20150507`, obtained directly from
`https://www.cs.cmu.edu/~enron/`.

| Property | Value |
|---|---|
| SHA-256 (tarball) | `b3da1b3fe0369ec3140bb4fbce94702c33b7da810ec15d718b3fadf5cd748ca7` |
| Tarball size | 443,254,787 bytes |
| Extracted size | ~1.42 GB apparent |
| Message files | 517,401 |
| Custodian mailboxes | 150 |
| Retrieved | 2026-08-22 |

A machine-readable provenance record is stored alongside the corpus and will be published with the
paper so the exact corpus state is reproducible.

**Two corpus facts that bear on the design:**

**Date range.** A full scan of all 517,401 `Date:` headers parsed successfully. The effective range is
**1999–2002** (2001: 273,032; 2000: 196,101; 2002: 35,905; 1999: 11,144 — 99.9% of the corpus). A small
tail of outliers (1979, 1986, 1997, 2004, and single-digit counts as late as 2044) are client clock-skew
artefacts from misconfigured mail software, not data corruption. All time-based analysis will filter to
the effective range and report the exclusion.

**File count is not message count.** The 517,401 figure counts *files*. A message sent to five custodians
appears five times, and messages are further triplicated within a single mailbox across `sent`,
`sent_items` and `_sent_mail`. We deduplicate on `Message-ID` and retain a copy-count. This matters
directly for the statistics: without deduplication, individuals who happened to correspond with many
custodians are silently over-weighted in every per-person measure.

---

## 3. Labelling scheme

Each *person* is assigned one of four roles:

| Role | Assignment |
|---|---|
| **Convicted** | Manual, against public record (DOJ / SEC / court records) |
| **Whistleblower** | Manual, against public record |
| **Employee** | Default for `@enron.com` domain addresses not otherwise labelled |
| **Other** | Default for external-domain addresses not otherwise labelled |
| *(unassigned)* | Retained as distinct from `Other`, to allow reporting of annotation coverage |

The top 500 senders by volume are additionally hand-reviewed. Each annotation carries an evidence
tier (`court_record` / `regulatory` / `major_press` / `corpus_internal` / `none`), a source URL where
one genuinely exists, and a confidence rating.

**The Whistleblower class has been measured and is not viable as a statistical group.** A full scan of
the corpus finds that **Sherron Watkins is not a custodian** — there is no `watkins-s` mailbox — and that
she authored exactly **7 unique messages** across the entire corpus. She is *referenced* in 139 files
spanning 33 custodian mailboxes, but as a correspondent and a subject of discussion, not as an author.
Seven authored messages cannot support any per-person linguistic measure. Vince Kaminski, the second
internal dissenter usually named in the literature, *is* a custodian — and is in fact the largest mailbox
in the corpus at 28,465 messages, which raises the opposite problem of role confounding (he was Head of
Risk Management). The Whistleblower group is therefore treated as a **qualitative case study**, not a
comparison group. See §6.

**We wish to flag a limitation honestly rather than obscure it.** Authoritative external evidence
exists for perhaps 30–60 individuals — the indicted, the executives, those who testified. The
remaining several hundred are mid-level traders, schedulers and analysts with no public record
whatsoever. For those, role assignment rests either on the email-domain rule or on evidence internal
to the corpus (signature blocks, distribution lists, internal org references). The `evidence_tier`
field makes this visible rather than hidden, and annotation coverage will be reported as a result in
its own right. We would welcome partner guidance on whether this is sufficient for the standard
expected, or whether the analysis should be restricted to the fully-evidenced subset.

---

## 4. Unit of analysis — persons, not emails

**The sample size for this study is approximately 150 custodians, not ~500,000 emails.** This is the
single most important framing point in this note, and we ask partners to hold us to it.

Emails are the unit of *measurement*; persons are the unit of *analysis* and of *inference*. Linguistic
features are computed per email and then aggregated to the person. Aggregation uses per-email means
rather than raw counts, so that an executive with 8,000 messages and a trader with 40 are placed on a
comparable footing. Where the modelling supports it, a mixed-effects specification with a person-level
random intercept is preferable to simple averaging.

Stating the sample size as "n ≈ 500,000" would invite readers to assume large-sample properties that
this design does not possess. The effective positive class — convicted individuals — is on the order of
**10–20 people**, and the whistleblower class on the order of **1–3**.

Only text **authored** by the person is counted: messages where they appear in `From`, with quoted and
forwarded material stripped. Quoted text is retained separately in the database rather than discarded,
for two reasons: it supports a planned Phase 2 analysis of copy-paste behaviour, and it allows the
quote-stripper's own decisions to be audited.

---

## 5. Splitting — person-disjoint, not email-random

**All partitioning is at the level of the person. Every message attributed to an individual falls in
exactly one fold. No individual appears in both training and test data.**

The rationale is a leakage argument. If partitioning is random over ~300,000 deduplicated emails, then
for each convicted individual roughly two-thirds of their messages fall in training and one-third in
test. What a model then learns is *that person's idiolect*. At test time it returns "Convicted" because
it recognises the writing of a specific known individual — which is closed-set authorship attribution,
a task at which the Enron corpus is notoriously tractable (Iqbal et al., 2010, report 80–90% accuracy
on ten authors from ten emails each). The reported performance would measure how identifiable a dozen
people's prose is, and would say nothing about whether an *unseen* insider can be flagged.

This is the record-wise versus subject-wise distinction formalised in the clinical machine-learning
literature by **Saeb et al. (2017)** and debated in the accompanying commentary by **Little et al.
(2017)**: record-wise splitting permits records from a training subject to enter the holdout, so the
model performs subject identification instead of the intended classification and the holdout ceases to
represent unseen data. Their empirical finding — record-wise cross-validation substantially
underestimating true error — transfers directly.

Supporting precedent from within the field: the PAN shared tasks on authorship verification moved
deliberately to **open-set, author-disjoint** evaluation, on the stated grounds that closed-set systems
overfit to properties that distinguish specific known authors from their peers rather than to general
stylistic signal.

**Residual leakage channels that person-disjoint splitting does not by itself close**, and which we
control separately:

- **Quotation leakage.** Enron messages quote each other extensively; person A's tokens appear inside
  person B's message. Addressed by quote and signature stripping before feature extraction.
- **Near-duplicate leakage.** `Message-ID` deduplication removes exact duplicates but not Bcc variants,
  list mail, or auto-replies.
- **Topic leakage.** Convicted individuals worked in identifiable business units on identifiable deals.
  A nominally "linguistic" feature set will partly index topic and job role rather than deception. This
  is a genuine threat that we do not claim to have eliminated.

---

## 6. Evaluation design

A single 67/33 holdout was considered and **rejected**. The reasoning is arithmetic. With ~15 convicted
individuals, a 33% test set contains ~5. Every metric computed on it is a fraction with denominator 5:
recall can take only the values 0, 0.2, 0.4, 0.6, 0.8, 1.0, and an exact 95% interval around 4/5 spans
roughly 0.28–0.99. That resolution cannot distinguish a strong method from a weak one, and the result
depends heavily on which five individuals the random seed selected. With 1–3 whistleblowers, a random
split can place zero of them in the test set, rendering the class unevaluable.

**Proposed design:** repeated stratified group *k*-fold cross-validation — *k* = 5, grouped by person,
stratified on person-level class, 50 repetitions with different seeds. Any feature selection or
hyper-parameter tuning occurs in an **inner** 5-fold loop on the training partition only (nested
cross-validation; **Varma & Simon, 2006**). Performance is reported as a **distribution across
repetitions**, never as a point estimate.

Supporting evidence for rejecting simpler schemes at this sample size:

- **Varoquaux (2018)** — cross-validation error bars are large and routinely *underestimated* at small
  *n*; single-split accuracy at these sizes is not a reliable basis for conclusions.
- **Vabalas et al. (2019)** — *k*-fold produces strongly biased estimates at small sample sizes, and in
  the published literature smaller samples correlate with *higher* reported accuracy, which is the
  signature of precisely this bias.
- **Geroldinger et al. (2023)** — relevant because it rules out the obvious alternative: plain
  leave-one-out cross-validation biases the c-statistic toward zero, worse for rare events. Where a
  leave-one-out flavour is wanted for a discrimination measure, **leave-pair-out** (one convicted, one
  control per iteration) is preferred.

**A label-permutation test is treated as essential rather than optional.** With 10–20 positives, a
pipeline with any flexibility can reach impressive-looking scores on noise. Person-level labels are
shuffled and the *entire* pipeline — including feature selection — is rerun, with the empirical
*p*-value of the observed score reported.

**On the Whistleblower class.** At *n* = 1–3, no partitioning scheme supports treating this as a
classification target. We propose to report it **descriptively** — where does each whistleblower fall
on the index? — or to collapse the problem to binary Convicted vs. Not-Convicted with the other roles
as stratifying covariates. Presenting per-class metrics for an *n* = 2 class would not withstand review.

**On model complexity (Phase 2).** Conventional events-per-variable guidance implies that ~15 positives
supports only 1–2 free parameters. This is a strong argument for constructing the ILI as a
**pre-specified, fixed-weight composite**, or a single regularised score with the penalty selected in
the inner loop, rather than a learned high-dimensional classifier.

**Framing.** At ~15 positives this study is closer in character to a **case-control design** than to a
machine-learning generalisation study. We intend to say so explicitly.

---

## 7. Metrics

| Metric | Rationale |
|---|---|
| **Average precision (PR-AUC)**, with prevalence baseline stated | Appropriate under severe imbalance |
| **Matthews correlation coefficient** | High only when all four confusion-matrix cells are good |
| **Per-class recall with Clopper–Pearson 95% intervals** | Intervals shown, not suppressed |
| **Precision@k** | Mirrors real investigative triage |
| **Full confusion matrix, raw counts** | At this *n*, more informative than any summary statistic |

Accuracy and ROC-AUC are reported only as secondary descriptors.

**Why those two mislead here.** Accuracy is uninformative: predicting "not convicted" for everyone
yields ~90% at person level. ROC-AUC misleads under severe imbalance because the false-positive rate
has a very large denominator — moving from 10 to 1,000 false positives barely shifts it, so a model
with unusable precision can still present a flattering ROC curve (**Saito & Rehmsmeier, 2015**).
**Chicco & Jurman (2020)** give the corresponding argument for MCC over F1 and accuracy.

The precision@k framing deserves emphasis: the index produces a ranking of ~150 people, and the
operationally meaningful question is how many of the ~15 convicted appear in the top 10, 20, or 50.
There is direct precedent in the accounting-fraud literature — **Bao et al. (2020)** argue explicitly
that standard classification metrics are inappropriate for rare-event fraud prediction and introduce a
ranking metric on the grounds that regulators can investigate only a limited number of top-ranked cases.

**Class imbalance handling.** Class weighting, not synthetic oversampling. SMOTE interpolates between
neighbours; with ~15 real positives the synthetic points are dense fabrications in a space we have not
characterised. Where any resampling is used it is applied strictly **inside** training folds — resampling
before splitting is a well-documented leakage error.

---

## 8. Temporal controls

**The primary analysis is restricted to messages sent before 1 October 2001.**

The motivation is a confounding hazard rather than a framing preference. Following the
October–December 2001 collapse, the email of implicated executives is saturated with subpoenas, Arthur
Andersen, document retention, counsel, resignation and bankruptcy language. A model trained across the
full period will detect this and perform impressively — while measuring nothing beyond "was this person
central to the scandal in Q4 2001," which is the label itself. Any reviewer familiar with the corpus
will raise this.

Restricting the **feature window** costs essentially nothing at person level: the same ~150 people
remain, only their post-collapse messages are dropped. The full-period result will be reported as a
secondary comparison, and the difference between the two is itself an informative finding.

A **temporal train/test split** (train on 1999–2000, test on 2001) is a different proposition and is
*not* a substitute for person-disjoint splitting — the same convicted individuals appear in both
windows, reintroducing the identity leakage of §5. Its legitimate role is as a secondary
temporal-generalisation check, ideally person-disjoint *and* time-forward simultaneously.

Precedent for time-forward evaluation in the closest analogous literature: **Larcker & Zakolyukina
(2012)** estimate on one period and report out-of-sample performance on later data; **Purda &
Skillicorn (2015)** likewise; **Bao et al. (2020)** use a strict time-forward design with a gap period
to avoid look-ahead bias.

**An open question for partners.** Some convicted individuals' conduct spans 1999–2001 and others' does
not. Aligning each person's feature window to their own offence period, using dates from the
indictments, is more defensible than a single calendar cut — but it introduces a researcher degree of
freedom that would need pre-specification. We would value a view on whether this is worth the added
complexity.

---

## 9. Multiple comparisons and pre-specification

With ~15 positives and a growing feature list, uncorrected feature-by-feature comparison will generate
significant results by chance.

- The **feature list is pre-specified** in a time-stamped protocol before any group differences are
  examined. The paper separates a **confirmatory** section (pre-registered, corrected) from an
  **exploratory** section (labelled hypothesis-generating, not claimed).
- **Benjamini–Hochberg FDR at q = 0.05** across the feature family. BH tolerates the positive dependence
  that POS and length features exhibit; Bonferroni over-corrects severely on correlated features.
  Bonferroni is reserved for the small confirmatory core on which the index itself is built.
- **Effect sizes with confidence intervals are reported for every feature**, corrected or not. At ~15
  versus thousands, *p*-values are dominated by the large group's precision and are near-uninformative;
  Cliff's delta or Hedges' *g* with an interval communicates far more.
- **The correlation structure of the feature set is reported**, so readers can judge the effective
  number of tests.
- **Multiplicity accounting covers the whole search** — aggregation schemes, time windows, and model
  choices included.
- **Feature selection never touches the full data before evaluation** (Varma & Simon, 2006).

---

## 10. Known threats to validity

We record these now so they are in the methods section rather than the reviews.

1. **Deception cues may not generalise across domains.** **Gröndahl & Asokan (2019)**, a systematic
   review, concludes that deception-indicative linguistic features fail to generalise across semantic
   domains. This is the most likely basis of reviewer scepticism and is pre-empted rather than omitted.
2. **The corpus is a legal-discovery subset**, not a random sample of Enron communication, and has been
   redacted over successive releases.
3. **Topic and role confounding** — see §5.
4. **Seniority confounding.** Convicted individuals are disproportionately senior. Any measure
   separating them may be measuring executive register rather than deception. This requires an explicit
   control, and we would welcome partner input on the right one.
5. **Automated senders.** Newsletters, announcement addresses and market-data feeds generate large
   volumes of boilerplate. These are flagged and excluded.
6. **Low-volume individuals** produce unstable ratio features. A minimum-volume threshold will be set
   from the observed distribution rather than chosen a priori, and reported.
7. **Prior work on this corpus overwhelmingly uses email-level random splits** and, so far as our
   survey has found, does not address person-level leakage. We read this as positioning person-disjoint
   evaluation as a contribution — but partners may judge that it instead makes our results
   non-comparable to the existing literature, and that tension should be resolved deliberately.

---

## 11. Draft methods-section text

> All splitting was performed at the level of the person, not the email: every message attributed to a
> given individual was assigned to exactly one fold, so that no individual appeared in both training
> and test data. Because the convicted class contains only ~N individuals, a single held-out split was
> rejected as providing insufficient resolution. Instead we used repeated stratified group k-fold
> cross-validation (k = 5, stratified on person-level class, grouped by person, 50 repetitions), with
> feature selection and hyper-parameter tuning performed in an inner 5-fold loop on the training
> partition only. Class imbalance was handled by class weighting rather than synthetic oversampling.
> Generalisation performance is reported as a distribution across repetitions and accompanied by a
> label-permutation test (10,000 permutations of person-level labels through the complete pipeline).
> Primary metrics are average precision, Matthews correlation coefficient, per-class recall with
> Clopper–Pearson intervals, and precision@k. The primary analysis uses only messages sent before
> 1 October 2001, with a secondary chronological analysis reported separately. The feature list was
> pre-specified before any test-set evaluation; group comparisons are corrected using
> Benjamini–Hochberg FDR at q = 0.05, with effect sizes and confidence intervals reported for every
> feature regardless of significance.

---

## 12. Questions for partners

1. Is the annotation evidence standard in §3 acceptable, or should analysis be restricted to the
   fully-evidenced subset?
2. Is per-person offence-period alignment (§8) worth the added researcher degree of freedom?
3. What is the appropriate control for the seniority confound (§10.4)?
4. Should the study pre-register formally (OSF / AsPredicted), or is a dated, version-controlled
   feature specification sufficient?
5. Does the Whistleblower class warrant descriptive treatment (§6), or should it be dropped from the
   headline analysis entirely?

---

## 13. Sources

### Retrieved and verified

1. Bao, Y., Ke, B., Li, B., Yu, Y. J., & Zhang, J. (2020). Detecting accounting fraud in publicly traded
   U.S. firms using a machine learning approach. *Journal of Accounting Research*, 58(1), 199–235.
2. Chicco, D., & Jurman, G. (2020). The advantages of the Matthews correlation coefficient (MCC) over F1
   score and accuracy in binary classification evaluation. *BMC Genomics*, 21, 6.
3. Geroldinger, A., Lusa, L., Nold, M., & Heinze, G. (2023). Leave-one-out cross-validation,
   penalization, and differential bias of some prediction model performance measures — a simulation
   study. *Diagnostic and Prognostic Research*, 7, 9.
4. Gröndahl, T., & Asokan, N. (2019). Text analysis in adversarial settings: does deception leave a
   stylistic trace? *ACM Computing Surveys*, 52(3). arXiv:1902.08939.
5. Iqbal, F., Binsalleeh, H., Fung, B. C. M., & Debbabi, M. (2010). Mining writeprints from anonymous
   e-mails for forensic investigation. *Digital Investigation*, 7(1–2), 56–64.
6. Keila, P. S., & Skillicorn, D. B. (2005). Structure in the Enron email dataset. *Computational and
   Mathematical Organization Theory*, 11(3), 183–199.
   *(Note: the frequently-cited companion title "Detecting unusual and deceptive communication in email"
   does not match the DBLP record, which lists "Detecting unusual email communication", CASCON 2005,
   117–125. Resolve before citing the CASCON paper.)*
7. Larcker, D. F., & Zakolyukina, A. A. (2012). Detecting deceptive discussions in conference calls.
   *Journal of Accounting Research*, 50(2), 495–540.
8. Little, M. A., Varoquaux, G., Saeb, S., Lonini, L., Jayaraman, A., Mohr, D. C., & Kording, K. P.
   (2017). Using and understanding cross-validation strategies: perspectives on Saeb et al.
   *GigaScience*, 6(5), gix020.
9. Noever, D. (2020). The Enron corpus: where the email bodies are buried? arXiv:2001.10374.
10. Priebe, C. E., Conroy, J. M., Marchette, D. J., & Park, Y. (2005). Scan statistics on Enron graphs.
    *Computational and Mathematical Organization Theory*, 11(3), 229–247.
11. Purda, L., & Skillicorn, D. (2015). Accounting variables, deception, and a bag of words: assessing
    the tools of fraud detection. *Contemporary Accounting Research*, 32(3), 1193–1223.
12. Saeb, S., Lonini, L., Jayaraman, A., Mohr, D. C., & Kording, K. P. (2017). The need to approximate
    the use-case in clinical machine learning. *GigaScience*, 6(5), gix019.
13. Saito, T., & Rehmsmeier, M. (2015). The precision-recall plot is more informative than the ROC plot
    when evaluating binary classifiers on imbalanced datasets. *PLOS ONE*, 10(3), e0118432.
14. Vabalas, A., Gowen, E., Poliakoff, E., & Casson, A. J. (2019). Machine learning algorithm validation
    with a limited sample size. *PLOS ONE*, 14(11), e0224365.
15. Varma, S., & Simon, R. (2006). Bias in error estimation when using cross-validation for model
    selection. *BMC Bioinformatics*, 7, 91.
16. Varoquaux, G. (2018). Cross-validation failure: small sample sizes lead to large error bars.
    *NeuroImage*, 180, 68–77.
17. Ruder, S., Ghaffari, P., & Breslin, J. G. (2016). Character-level and multi-channel convolutional
    neural networks for large-scale authorship attribution. arXiv:1609.06686.

### Standard references identified via search but not fetched directly

18. Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate. *Journal of the Royal
    Statistical Society, Series B*, 57(1), 289–300.
19. Bevendorff, J., et al. Overview of the (Cross-Domain) Authorship Verification Task at PAN 2020/2021.
    *CLEF Working Notes*, CEUR-WS Vol. 2936. *(Verify author list and volume for the specific year cited.)*

### ⚠ Not retrieved — must be verified before citing

These are cited in this note's reasoning but were **not** obtained in full. They should not enter a
bibliography until checked.

- **Ojala & Garriga (2010)**, *JMLR*, permutation tests for classifier performance — the standard
  reference for permutation-based significance testing, cited from memory, **not retrieved**.
- **Peduzzi et al. (1996)**, *J Clin Epidemiol*, events-per-variable — same status, **not retrieved**.
- **"The Manifestation of Fraud in Language: An Enron eMail Corpus Case Study on Fraudulent Language
  Markers"** — a ProQuest-indexed doctoral dissertation. The record exists but author and year could
  not be obtained (paywalled). **This is likely the closest prior work to the present project and
  should be retrieved through the university library and engaged with directly.**
- **"Uncovering Wrongdoing in the Enron Email Corpus" (2023)** — ResearchGate-hosted, peer-reviewed
  venue unconfirmed. Treat as grey literature.
- **Chronological-split claims in recent Enron insider-threat preprints** — split descriptions came from
  search snippets, not full texts. Do not cite for that detail without reading.
- **Reported per-author email counts and 8:2 splits across Enron deep-learning attribution papers** —
  synthesised from search snippets. Verify any figure before tabulating.

### Reasoning not drawn from a cited source

The quantitative arguments in §6 concerning interval widths, quantised recall, and events-per-variable
are our own arithmetic on the stated class sizes. The quotation, near-duplicate and topic-leakage
channels in §5, and the seniority confound in §10, are reasoned from the structure of the Enron corpus
rather than from published work documenting them for this dataset. We found no published work
specifically addressing person-level leakage on Enron.

---

*Prepared as a pre-analysis design document. No analysis has been run. All data processing is local;
no data, statistics or model artefacts leave the analysis machine.*
