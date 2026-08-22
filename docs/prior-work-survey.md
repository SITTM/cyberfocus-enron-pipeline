# Prior-Work Survey — Insider Language Index

**For:** project team and University of Lancashire partners
**Status:** Working document. Sections 1–4 and 6 complete; §5 partially complete (noted inline).
**Date:** 22 August 2026

**Evidence tags used throughout.** **[V]** = source actually retrieved and read. **[S]** = existence and
bibliographic detail confirmed from a search result or index record; content not read. **[U]** =
unverified — do not cite.

This document surveys what already exists, so that we do not reinvent it and so the contribution can be
positioned honestly. It is deliberately blunt about weak evidence, including evidence that weakens our
own premise.

---

## 0. Executive summary

Five findings drive everything below.

1. **The meta-analytic support for linguistic deception cues is much weaker than the applied literature
   implies.** Of the four canonical Pennebaker cues, one holds at *d* ≈ 0.24, one is contradicted, and
   two are marginal and outlier-dependent (§1.1). Expect a modest or null result and design for it.
2. **Deception cues do not transfer across domains.** In-domain 0.89 → cross-domain 0.36–0.52, i.e. at
   or below chance (§1.2).
3. **On Enron specifically, role and network structure beat language.** A network-only baseline reaches
   83.9% on hierarchy against a theoretical NLP ceiling of 59.6% (§2.3). Word use correlates *clearly*
   with company role, while criminality is only *"slightly distinctive"* (§2.2).
4. **The headline accuracies in this field are artefacts of evaluation error.** The best-documented
   case, reported by the author against his own interest, is 70.7% → 91% from relaxing corpus filters
   alone (§2.3).
5. **No published work predicts Enron fraud from language under a person-disjoint split with a reported
   AUROC and base rate.** That is the gap (§6).

The recommended framing is therefore a **methodological calibration study** rather than a detection
claim. See §6.

---

## 1. Statistical language analysis of deception and fraud

### 1.1 Do linguistic deception cues replicate?

Weakly, inconsistently, and not in the form the popular version of the model claims.

**DePaulo et al. (2003), "Cues to Deception," *Psychological Bulletin* 129(1), 74–118. [V]**
1,338 estimates of 158 cues across 120 independent samples. Verbatim: *"many behaviors showed no
discernible links, or only weak links, to deceit."*
*(The widely-quoted "14 of 50 cues significant, mean d ≈ 0.25" pair appeared in a search summary, not in
the extracted PDF text — treat those two numbers as [S].)*

**Hauch, Blandón-Gitlin, Masip & Sporer (2015), *Personality and Social Psychology Review* 19(4). [V]**
The meta-analysis that matters most here, because it covers computer-assisted **word-count** cues — our
Phase 1 method exactly. 1,093 effect sizes, 79 cues, 44 studies.

- Overall effects centre on **gu = −0.01 (SD 0.37), median 0.02**, range −1.95 to 1.43.
- Taking the **absolute** magnitude of every effect — i.e. generously assuming all ran in the predicted
  direction — **mean 0.26, median 0.19**, IQR 0.09–0.34.
- Authors' conclusion, verbatim: *"without a priori theoretical predictions, computer analyses of
  linguistic cues to deception are a futile exercise."*

The four canonical cues, cue by cue:

| Claim | Hauch et al. result | Verdict |
|---|---|---|
| Fewer **first-person pronouns** | Singular **n.s.**; plural **n.s.**; *total* first-person **gu = 0.14 [0.06, 0.22]**, and only after excluding an outlier study | **Barely survives**, not in the singular form usually cited |
| Fewer **exclusive words** | **gu = 0.24 [0.17, 0.31]** | **Best-supported of the four.** Still small |
| More **negative emotion** | Umbrella **gu = −0.07 [−0.15, 0.01], n.s.**; anger −0.27; **anxiety n.s.** | **Not supported as stated.** The claim that anxiety words outperform overall negative emotion was explicitly **not** supported |
| More **motion/action verbs** | **gu = −0.09 [−0.17, −0.01]**, significant **only** after removing an outlier | Technically supported, trivially small |

Also: word quantity **gu = 0.24 [0.19, 0.29]** (truth-tellers write more); quantifiers 0.14 (k=4);
sensory-perceptual detail 0.06.

**A *d* of 0.2–0.25 corresponds to an AUC of roughly 0.55–0.57. That is the ceiling the meta-analytic
evidence supports for any single cue.**

**Luke (2019), *Perspectives on Psychological Science* 14(4), 646–671. [V]**
Monte Carlo simulations showing reported deception-cue effect sizes are inflated by publication bias,
small *k*, and low power. Concludes *"the informational value of the present deception literature is
quite low."* The strongest citation for "even the estimates above are probably too high."
*(Incidental: Luke gave a Security Lancaster seminar on this — a natural local hook for the partnership.)*

**Newman, Pennebaker, Berry & Richards (2003), *PSPB* 29(5), 665–675. [S]**
Origin of the four-cue model. Reports **67% classification with topic held constant, 61% overall**. Even
the original paper claims 61–67%, not the 90%+ that later applied work implies.

### 1.2 Cross-domain generalisation — the second structural problem

**Panda & Levitan (2023), *ACM JDIQ*. [V]**
Five deception domains, logistic regression (word and POS features) and BERT. A model trained on
Deceptive Opinion Spam reaches **0.89 in-domain** and transfers at **0.360–0.515** — at or below chance.
With BERT layers frozen, *"cross-domain classification is close to random guess."*

**Gröndahl & Asokan (2019), *ACM Computing Surveys* 52(3), Art. 45. [V]**
Verbatim: *"while certain linguistic features have been indicative of deception in certain corpora, they
fail to generalize across divergent semantic domains. We suggest that deceptiveness as such leaves no
content-invariant stylistic trace."*

This is the most direct threat to the project's framing and must be engaged head-on. Their constructive
alternative — measuring **deviation from an author's own baseline** rather than absolute deception style
— is a viable reframing for an *index*, and is worth serious consideration.

**Velutharambath et al. (2025), arXiv:2505.13147. [V]** Existing findings are *"largely driven by
artifacts introduced during data collection and do not generalize."* On a new belief-based corpus,
commonly cited indicators showed *"negligible, statistically insignificant correlations"* and models
performed **at chance** despite scoring well on established benchmarks.

Corroborating: Velutharambath & Klinger (2023), UNIDECOR [V]; Tomas, Dodier & Demarchi (2022),
*Frontiers in Communication* 7:792378 [V] — stylometric deception tools *"cannot be applied to deception
detection problems on the field in their current state."*

### 1.3 Other feature families

**Readability/complexity.** Loughran & McDonald (2014), *Journal of Finance* 69(4) [S] — the Fog Index
is *"poorly specified"* in financial applications; raw file size outperforms it. Readability formulas are
calibrated on continuous prose, not terse business email. Report them; do not make them load-bearing.

**Function-word stylometry, n-grams, bag-of-words.** Well validated for **authorship**, poorly validated
for **deception**. The critical implication: these features are *so* good at identifying authors that any
non-person-disjoint evaluation will silently learn author identity and relabel it as the target
construct.

**Syntactic/POS features.** Panda & Levitan test POS-only models and find the same in-domain/cross-domain
collapse. Crabb (2014) [V] deliberately uses POS-only features precisely to avoid Enron topic
overfitting — a design worth copying.

### 1.4 The best methodological exemplars (non-Enron fraud)

**Larcker & Zakolyukina (2012), *JAR* 50(2), 495–540. [S]** CEO/CFO earnings-call narratives labelled by
subsequent restatement. Out-of-sample performance *"better than random by 6%–16%."* **This is the
realistic ceiling for language-only misconduct detection with high-quality labels and real high-stakes
speech.** Anchor expectations here. *(The 6–16% figure is from a snippet — verify.)*

**Purda & Skillicorn (2015), *Contemporary Accounting Research* 32(3), 1193–1223. [V]** 4,895 MD&A
sections, ~23% fraudulent (SEC AAER labels). Data-derived word list beats pre-set dictionaries.
**82.19–82.95% accuracy, AUC 0.89 — against a 77% majority baseline, so ~5 points of real lift — falling
to 71.04% out of sample.** The split is report-level, not firm-level, so some of that 82% is firm
identity: our author-disjoint problem in another guise, and an excellent precedent to cite.

**Bloomfield (2012), *JAR* 50(2), 541–552. [V for citation; content not retrieved]** The published
critique of Larcker & Zakolyukina. Worth pulling.

---

## 2. Published predictive ML on Enron and analogous corpora

### 2.1 The closest comparable — and it is weak

**Noever (2020), "The Enron Corpus: Where the Email Bodies are Buried?" arXiv:2001.10374. [V]**
arXiv preprint, no peer-reviewed venue found. POI prediction over 145 employees using compensation
variables, email-volume counts, and NRC-style emotion scores; 51 algorithms, Random Forest best.

- **95.28% POI accuracy on the over-sampled dataset; 72.2% under-sampled — same features.**
- Financial + email-sentiment RF: **AUROC 0.8625**.
- **Email/linguistic features alone: AUROC 0.76** ← the number our index should be benchmarked against.
- A single rule (*bonus > $1.17M*) reaches 87% using **no email features at all**.

**Assessment: the headline is inflated.** n=145 with ~18 positives. The 95.3 vs 72.2 gap on identical
features shows resampling doing the work, and the described workflow makes oversampling-before-splitting
the most plausible reading. Worse, the dominant predictors (exercised stock options, stock value) are
close to the *definition* of who got prosecuted — target leakage in the causal sense. The author concedes
email factors were of *"moderate to low predictive value."*

### 2.2 Enron deception work

**Keila & Skillicorn (2005), "Structure in the Enron email dataset," *Computational and Mathematical
Organization Theory* 11(3), 183–199. [V]**
SVD and semidiscrete decomposition over word-frequency profiles. Unsupervised; no classifier, no split.
Findings: messages cluster into short/rare-word vs long/common-word groups; **word use correlates clearly
with organisational function**; and, hedged, word use among those *"involved in alleged criminal activity
**may be slightly distinctive**."* Their conclusion states *"a clear effect of company role."*

**This is the foundational insider-language paper on Enron, it is 21 years old, it claims only a weak
hedged signal — and it documents that the role confound is strong.** That combination is the central fact
for our gap analysis.

> **⚠️ Citation warning.** DBLP [V] lists only two Keila publications: the CMOT paper above, and
> **"Detecting unusual email communication," CASCON 2005, pp. 117–125**. The title widely cited in the
> secondary literature — *"Detecting unusual and deceptive communication in email"* — **does not match
> the DBLP record**, and the CASCON paper itself was not retrieved. DBLP also misnames the journal as
> "Computers & Mathematics with Organization Theory". **Resolve both before citing.** Our methodology
> briefing currently carries the disputed title and must be corrected.

**Louwerse, Lin, Drescher & Semin (2010), *CogSci 2010*. [V]** Linguistic Category Model abstractness
over Enron, correlated against **16 time-based events**. n=16 units of analysis, no split, no
classification metric. The authors disclaim predictive validity verbatim: *"By no means are we arguing
that by using the LCM model we can predict whether an email consists of fraudulent information or not."*

**Crabb (2014), *JDFSL* 9(2). [V]** Sent-mail of one prosecuted executive; deliberately
content-independent POS/pronoun/lexical-diversity features; within-author outlier ranking. **Reports no
performance figure, and says why:** *"no definitive identification of deceptive emails is possible, as no
ground-truth is available."* The most methodologically self-aware paper in this space and the best
citation for justifying our labelling scheme.

**Zhou, Burgoon, Nunamaker & Twitchell (2004), *Group Decision and Negotiation* 13(1), 81–106. [V —
record only]** Source of the standard 27-cue linguistic feature set reused by nearly all email-deception
work. Lab-elicited, low-stakes, student subjects. **Do not assume cue validity established here transfers
to Enron.**

**Ludwig, van Laer, de Ruyter & Friedman (2016), *JMIS* 33(2), 511–541. [V — abstract]** Real archival
business email with real fraud labels. Introduces meta-level **"intertextual exchange cues"** — deception
as a *dyadic* property. Closest published analogue to our design outside Enron; worth chasing.

### 2.3 Role and hierarchy inference — the best methodology in the field

**Bramsen, Escobar-Molano, Patel & Alonso (2011), *ACL 2011*, 773–782. [V] ⭐ The design to imitate.**
Enron UpSpeak vs DownSpeak, SVM. Split, verbatim: *"we partitioned the **authors** of text from the
corpus into two sets… text authored by individuals in A as a training set and text authored by
individuals in B as a test set."* **A genuine author-disjoint split.**

| Features | 10-fold CV | Test (weighted) | Test (unweighted) |
|---|---|---|---|
| Word unigrams (3,899) | 55.4% | 62.1% | 78.9% |
| Unigrams + bigrams | 51.8% | 63.3% | 80.7% |
| **Binned n-grams (106→8 features)** | **83.0%** | **78.1%** | 77.2% |
| Binned + polite imperatives | **83.9%** | 77.1% | 78.9% |

**High-dimensional lexical features score 51–55% in CV while an aggressively generalised 8-feature model
reaches 83.9%.** A live demonstration that lexical features on Enron memorise authors and topics rather
than learn the construct.

**Gilbert (2012), "Phrases that signal workplace hierarchy," *CSCW 2012*, 1037–1046. [V]**
2,044 messages after strict filtering. Feature hygiene worth copying wholesale: quoted/forward text
stripped; phrases appearing in <10 messages dropped; two human raters independently removed all
Enron-business-specific phrases; **"we discard any phrase not written by at least three different
people."** The SVM was deliberately denied sender identity, because *"an SVM would project lots of
predictive information onto the identities."*

Result: **70.7% vs a 60.5% majority baseline.** Then the admission we should quote directly: *"when we
expand the dataset to go past May 2001 (yielding 11K messages total), the SVM's accuracy goes to 91%."*

**A 70.7 → 91 jump from relaxing filtering alone, reported by the author against his own interest.** The
best single piece of evidence for why the 90%+ figures elsewhere in this literature are artefacts.

**Agarwal, Omuya, Harnly & Rambow (2012), *ACL 2012 (Short)*, 161–165. [V] — the sharpest published
critique of prior Enron ML work.**
- Prior work relies on Shetty & Adibi's job-title list, which covers only "core" employees whose full
  inboxes survive — **a survivorship-biased population**, and still the population most Enron ML papers
  use.
- Verbatim: *"(Bramsen et al., 2011a) use 142 dominance pairs for training and testing."*
- Their gold standard: **13,724 dominance pairs** over ~1,500 employees.
- **A simple social-network baseline reaches 83.88%. The theoretical upper bound for any purely
  NLP-based system is 59.61%**, because NLP can only judge pairs who actually exchanged email (2,640 of
  13,724).

**Implication, and it is severe: on Enron, metadata and network baselines beat text. If we do not report
a metadata-only baseline, reviewers will assume our language model is riding on network structure.**

**Prabhakaran & Rambow (2014), *ACL 2014 (Short)*, 339–344. [V]** Dialog-structure features (dangling
requests, participant add/remove, overt displays of power) reach **73.0%, +6.9 over a 68.3% lexical-only
system**. Thread-level split, **not** person-disjoint, so 73% is optimistic. Key insight: **the winning
features are interactional, not lexical.**

Also: Prabhakaran, Neralwala, Rambow & Diab (2012), *LREC 2012* [V] — 122 annotated Enron threads, four
power types; a ready-made gold set. Rowe, Creamer, Hershkop & Stolfo (2007) [V] — metadata-only org-chart
reconstruction. McCallum, Wang & Corrada-Emmanuel (2007), *JAIR* 30, 249–272 [V] — Author-Recipient-Topic
model; the design insight is that email language is a property of the **dyad**, not the author.

### 2.4 Authorship attribution on Enron

**Iqbal, Binsalleeh, Fung & Debbabi (2010), *Digital Investigation* 7(1–2), 56–64. [V]** 200,399 Enron
emails; 3–10 authors × 10–100 emails each. F-measure **0.73–0.88** at 5 authors × 40 messages, **0.91** at
100 msgs/author. **Structural features (signatures, greetings, layout) were strongest; content-specific
weakest** — much of the "authorship signal" is formatting, not language.

**Apoorva & Sangeetha (2021), *SN Applied Sciences* 3:348. [V]** Stylometry + TF-IDF + DNN: 5 authors 94%,
25 authors 86–87%, **149 authors 75% (DNN) / 86% (clustering)**. No train/test protocol stated; TF-IDF
over Enron means topic and named entities do much of the work.

**Tyo, Dhingra & Lipton (2022), arXiv:2209.06869 (VALLA benchmark). [V]** Verbatim: *"inconsistent
dataset splits/filtering and mismatched evaluation methods make it difficult to assess the state of the
art."* Flags **topic leakage "present in many popular datasets"** and names the split taxonomy — i.i.d.,
cross-topic, cross-genre, and **unknown-author (×a)**. Two takeaways: the author-disjoint split is an
established, citable protocol; and **VALLA's 15 datasets do not include Enron.** Also reports n-gram
baselines (76.50%) *beating* BERT (66.71%) on most AA datasets.

**Wright (2014), PhD thesis, University of Leeds. [V]** Corpus-linguistic critique of the "idiolect"
assumption in computational authorship work on Enron. A useful UK forensic-linguistics counterweight.

### 2.5 Insider-threat detection — mostly CERT, mostly not language, mostly not credible

**Kundiya & Haribhakta (2025), *International Journal of Information Security* 24:227. [V]** PRISMA review
of 66 studies (2019–2024) over CERT and Enron. Reports the field's headline claims as **"accuracies up to
99.2% and F1 above 94%"** — then lists why they should not be believed: synthetic data, **class-imbalance
bias skewed toward benign cases**, explainability gaps, scarcity of real anonymised data. **The best
single citation for "the reported numbers in this field are not credible."**

**Glasser & Lindauer (2013), IEEE SPW, 98–104. [S]** Origin of the CERT datasets. **CERT is entirely
synthetic** — background and malicious behaviour both generated. Any "99% on CERT" is accuracy at
recovering a data generator's own rules. Enron, whatever its flaws, is real; that is our dataset's main
claim to legitimacy.

**Mladenović et al. (2024), *Scientific Reports* 14. [V]** CERT email content, sentiment+NLP → XGBoost.
Reports **~98% accuracy, ~97% F1. Do not take at face value.** Plain 70/30 random split, **email-level not
person-disjoint** — the same insiders' emails appear in train and test. Imbalance "handled" by
downsampling the majority to 1:10 **including the test set**, so F1=0.97 at 1:10 may be worthless at a
true base rate. Data synthetic. **This is the closest published thing to what we are proposing, and it is
exactly the failure mode to design against.**

**Le, Zincir-Heywood & Heywood (2020), *IEEE TNSM* 17(1), 30–44. [S]** Names the field's problems
(*"hugely unbalanced data, limited ground truth, behaviour drifts and shifts"*) and evaluates at **both
instance level and normal/malicious user level** — the best methodological citation for justifying
person-level evaluation.

**Brown, Watkins & Greitzer (2013), *HICSS-46*, 1849–1858 [V for citation; content snippet-only]** and
**Greitzer et al. (2013), AMCIS 2013 [S]** — the closest published attempts at a psycholinguistic
insider-risk *index*. **Our nearest prior art by name. Pull these before claiming novelty.**

Also noted without close reading: Tuor et al. (2017) arXiv:1710.00811 [S]; Legg et al. (2015) [V];
Al-Shehari & Alsowail (2021), *Entropy* 23(10):1258 [V] — **standing caution: SMOTE-before-split is one of
the most common leakage bugs in this literature and the abstract does not state the ordering**; Janjua et
al. (2020) [V], which uses **TWOS**, a real human-subject insider dataset and a useful alternative to
CERT; Soh et al. (2019), *ESWA* 135, 351–361 [S — paywalled, close to our construct, worth chasing].

### 2.6 The person-disjoint evidence, in one line

On the real-life-trial deception corpus, papers with **speaker-independent** evaluation report **AUC
0.741–0.755**; papers without report **90–97%**. **That ~0.75 vs ~0.92 gap is the single best empirical
illustration that person-disjoint splitting separates real signal from leakage.**

---

## 3. Code and datasets

*All metadata retrieved live via `gh api`, PyPI, CRAN, HuggingFace and Kaggle APIs on 2026-08-22. Dates
are **last-commit**, not `pushed_at`.*

### 3.1 🔴 The build decision: is there a usable Enron body/quote extractor?

**No single library can be trusted. Build a thin layer over `quotequail` plus vendored talon heuristics,
and budget for manual validation.**

| Library | ★ | Last commit | Licence | Maintained |
|---|---|---|---|---|
| `mailgun/talon` | 1,342 | **2022-02-07** | Apache-2.0 | **NO — dead 4 yrs, 71 open issues** |
| `closeio/quotequail` | 69 | **2026-08-12** | MIT | **YES** |
| `zapier/email-reply-parser` | 530 | 2020-10-07 | MIT | **NO — 6 yrs stale** |
| `github/email_reply_parser` (Ruby) | 709 | 2025-07-12 | MIT | Lightly; **Ruby only** |
| `SpamScope/mail-parser` | 455 | **2026-08-21**, 0 open issues | Apache-2.0 | **YES — healthiest here** |
| `mailgun/flanker` | 1,650 | 2026-04-08 | Apache-2.0 | Alive, but **does NOT do quote stripping** — the star count misleads |

**The talon–Enron trap.** talon's ML signature classifier was trained on Mailgun's internal email **and
the EDRM-cleansed Enron subset** — so the one library explicitly trained on our corpus is talon. But:

- Its README states only **~190 emails were annotated**, and gives **no accuracy figure for the ML path**.
- `setup.py` requires **`cchardet`**, which has no wheels and fails to build on **Python ≥ 3.11**. We are
  on **3.12**. Issue **#234 open since 2023-06-30**; #239 and #240 open since 2023-10-17.
- Modernisation PR **#247** (opened 2025-05-30) is **unmerged**; follow-up issue #249 was **closed
  2026-08-14 without the merge landing**. Maintainers have stopped responding.
- The `--no-ml` codepath is broken (it tries to remove the literal string `"scikit-learn==0.24.1"` from a
  list that pins `scikit-learn>=1.0.0`).
- All 100 newest forks enumerated: **22 pushed since 2024; the most-starred has 3 stars.** No fork has
  taken over. `tictail/claw` (17★, 2015), `trilogy-group/kayako-ktalon` (0★), PyPI `talon-v2` (2021),
  `claw` (2015), `ktalon` (2018) — all dead.

**The decisive Enron-specific evidence.** Enron is overwhelmingly **Outlook 2000**, whose quote marker is
`-----Original Message-----` plus `From:/Sent:/To:/Subject:` — *not* Gmail's `On <date>, X wrote:`.

- **`quotequail/_patterns.py`** (source read): explicit Outlook support — `^---+ ?Original [mM]essage
  ?---+$`, the Outlook `________` rule, Outlook HTML border detection, plus DE/FR/ES/RU/SV/PT patterns.
- **`zapier/email-reply-parser/__init__.py`** (source read): its entire quote vocabulary is
  `QUOTE_HDR_REGEX = re.compile('On.*wrote:$')` plus a `From|Sent|To|Subject` regex. **No
  `-----Original Message-----` pattern at all.** Its `SIG_REGEX` contains `-\w`, matching any line
  starting with hyphen+word — **it would eat legitimate bulleted content.**

**PyPI names that do NOT exist (HTTP 404, verified):** `talon-core`, `mailgun-talon`, `talon-ml`,
`reply-parser`, `emailreplyparser`, `mailparser`, `talon2`, `email-quotations`. If any of these are
recommended anywhere, they are hallucinations. (`eml-parser` exists but is a forensics/IOC tool.)

**Recommended stack:** stdlib `email`/`mailbox` for RFC-822 → **`quotequail`** (MIT, maintained, the only
Outlook-aware candidate) for quote/forward splitting → **vendor talon's `signature/bruteforce.py`
heuristics** (Apache-2.0, so legally clean; dodges the cchardet wall) → `SpamScope/mail-parser` only if
MIME edge cases bite.

**A methodological point that will come up in review:** hand-annotate **300–500 Enron bodies and report
extraction precision/recall**. Talon's own README admits ~190 annotated emails and no ML accuracy figure,
so **no published extraction accuracy number exists for us to cite.** An index computed on bodies
contaminated by quoted text measures the *quoted party's* style, not the author's — the single largest
validity threat in the build.

### 3.2 Corpus sources

| Source | Detail | Verdict |
|---|---|---|
| **CMU canonical** | v2015-05-07. No attachments; redactions applied at employee request; invalid addresses normalised. No formal licence, only a privacy request | **Ground truth. Cite the version explicitly** |
| **⚠️ CMU April 2026 disclosure** [V] | Researchers found a vulnerability in the original Enron messaging system that *"allowed users to impersonate others… without leaving a trace."* CMU notes it *probably* does not affect NLP uses | **Must appear in limitations.** Our index rests on authorship integrity |
| **EnronSent** (Styler 2011, CU Boulder) | 96,107 Sent-Mail messages, 13.8M words; headers, quotes, forwards, HTML, signatures already stripped. **Public domain** | **Strong validation comparator.** Sent-only is arguably *correct* for authorship. **Weakness: flat text — sender, date and thread structure are gone** |
| **Kaggle CSV** | 358 MB, 2016-06-16. `message` is the **raw RFC-822 blob** — zero body extraction | Convenient only; use CMU |
| **ISI/USC MySQL (Shetty & Adibi)** | 252,759 emails, 151 employees. **Original URL dead; circulating copies unversioned** | Cite historically; do not build on |
| **AESLC** (Yale-LILY) | Bodies cleaned and truncated for subject-line generation | **Rejects our use case** |
| Pile/HF variants | Low-download, undocumented reprocessings | **Do not depend on any** |

**Enron loader libraries: none worth adopting.** `ZhaiResearchGroup/enron-parser` 1★ dead;
`tdebatty/java-datasets` 5★, 2017, Java. **Build it** — ~60 lines of `Path.rglob` +
`email.parser.BytesParser`.

### 3.3 Lexicons, readability, NLP

| Tool | Version / ★ | Licence | Verdict |
|---|---|---|---|
| **LIWC-22** | Commercial; **Academic tier exists** (universities only) | Commercial | **We qualify. Prices unpublished — start procurement now** |
| `empath` | 348★, last commit **2017-04-22** | MIT repo / **PyPI says UNKNOWN** | **Cross-validation, not substitute.** ⚠️ `create_category()` may call a remote Stanford server [U] |
| `liwc-python` | 240★, 2020-07-11 | MIT | **Parser only — ships no lexicon** |
| **NRC EmoLex** | v0.92; 14,182 unigrams, 8 emotions | Free for research, **no redistribution** | **Take it.** Ship a download script, not the data |
| `NRCLex` | 78★, 2026-03-03 | MIT code | Maintained; TextBlob tokenisation is inconsistent with spaCy |
| **`textstat`** | 1,378★, 2026-02-18 | MIT | **Healthy, take it** |
| `syntok` | 212★, 2022-03-12 | MIT | Stale but stable; excellent at ragged email sentence splitting |
| **spaCy** | 33,838★, 2026-08-07 | MIT | **Default for POS/lemma/dep** |
| Stanza | 7,865★, 2026-07-15 | Apache-ish | Spot-check only; too slow for 500k |
| MRC Psycholinguistic DB | 150,837 words | Academic/free | ⚠️ Only ~4–9k words carry concreteness/imageability. **Consider Brysbaert et al. (2014) 40k norms instead** [U] |
| Receptiviti | Paid metered API | MIT client | Rules itself out on cost at 500k messages |

### 3.4 Stylometry

| Tool | ★ | Last commit | Licence | Verdict |
|---|---|---|---|---|
| **`stylo` (R)** | 224 | **2026-06-19** | GPL ≥3 | **Gold standard. Use as validation reference** |
| **`faststylometry`** | 53 | **2025-07-21** | **MIT** | **Best Python option for Burrows's Delta. Recommended** |
| JGAAP | 283 | 2026-03-18 | **No licence file** | **Cite; do not build on.** No legal right to derive |
| `SuperStyl` | 27 | 2026-03-04 | GPL-3.0 | Sleeper pick — *supervised* stylometry, closer to our task |
| `pystyl` | 65 | 2018-04-26 | NOASSERTION | **Reject** |
| `jpotts18/stylometry` | 148 | one release in 11 yrs | NOASSERTION | **Reject** — stars are legacy, not health |
| `PyGAAP` | 2 | 2024-08-20 | AGPL-3.0 | **Reject** |
| `shaoormunir/writeprints` | 9 | 2022-11-29 | MIT | Feature set is a published spec; vendoring is low-risk |

**No maintained canonical Writeprints implementation exists.** It is a *feature specification*, not a
library — reimplement from the paper using spaCy + scikit-learn.

### 3.5 Insider-threat implementations

`gh search repos` for "enron insider threat" / "enron deception" / "enron fraud nlp" returned
**essentially nothing** (one 0★ repo). **There is no established Enron insider-language baseline
implementation on GitHub** — a genuine gap and a contribution opportunity.

CERT-based repos exist (`Chaofan-Z/InsiderThreatDetection` 27★; `CyberNexusX/...UBA...` 26★ MIT;
`cgly/ITDBERT` 23★; `NKU-HLT/Fusion-Insider-threat-detection` 18★) but **all are behavioural/log-based,
not linguistic**, and **most have no licence file** — cite, don't reuse.

---

## 4. Labelled role, identity and POI data

### 4.1 Org chart and job titles — three tables, all retrieved

**(a) EnronData.org custodian list — 148 rows, CC-BY 3.0 US. [V]**
`github.com/enrondata/enrondata/blob/master/data/misc/edo_enron-custodians-data.html`
Fields: index, maildir folder (`allen-p`), full name, rank, title.
Rank distribution: **N/A 45, Employee 35, Vice President 19, Director 13, Trader 12, Manager 10, CEO 4,
President 4, In House Lawyer 3, Managing Director 3.** ~30% unlabelled.
**The origin of the CEO/VP/Trader/Manager/Employee schema, the only one with an explicit licence, and it
maps directly to maildir folder names. Adopt this.**

**(b) `enron-employees.txt` — 184 lines. [V]**
`infosys.tuwien.ac.at/staff/dschall/email/enron-employees.txt`
`alias⇥Name⇥Rank⇥Title`. 184 lines because multiple aliases map to one person (`j..kaminski`,
`j.kaminski`, `vince.kaminski` → Vince Kaminski). **Doubles as a small alias→person map — the one
immediately usable artefact for identity resolution.** No licence, no author statement; it is a re-host.

**(c) 156-employee attribute table. [V]**
`raw.githubusercontent.com/karlrohe/disim/master/data/enron/employees.txt`
156 rows × 7 fields: `id, Name, Department{Legal|Trading|Other}, BusinessUnit, Title, Gender,
Seniority{Senior|Junior}`.
> **⚠️ Provenance not closed.** Hardin & Sarkis's JSE documentation [V] describes a *different* 156×7
> table with columns *ID, Name, Email ID, folder name, Department, Job title* — no gender/seniority. A
> snippet ties the gender/seniority variant to Priebe et al. (2005) [S]. **At least two circulating
> "156-employee" tables differ in columns. Flag this rather than asserting a source.**

**Reliability verdict on all three:** they trace back through Shetty & Adibi to an Enron "ex-employee
status report" of unclear original custody; ~30% N/A; titles are point-in-time and Enron reorganised
constantly. **Usable as coarse seniority strata, not as a validated org chart.**

Additionally, **Agarwal et al. (2012)** published the **13,724-pair dominance gold standard** — the most
rigorous role-relation resource available.

### 4.2 Identity resolution

- **Fiore & Heer (Berkeley)**, `bailando.berkeley.edu/enron_email.html` [V] — `enron.sql.gz`, ~219 MB,
  with *"a substantial amount of processing… to remove duplicates, **normalize names**, and so on."*
  MySQL only. **No licence stated.** The closest thing to a published alias-normalisation artefact.
- **Shetty & Adibi (2004) ISI TR** — **all mirrors dead** (404/403). **Do not cite as retrieved.** Obtain
  via ILL.
- **Zhou, Goldberg, Magdon-Ismail & Wallace (2007), NAACSOS 07** [S] — the "six standard aliases used at
  Enron" rules. It is a conference abstract, not a dataset — reimplement.
- **McCallum/UMass: verified negative.** The JAIR 2007 role assignments are **not** distributed.
- **Klimt & Yang (2004), ECML, LNCS 3201:217–226** [S] — introduces the corpus; publishes **no** identity
  or role labels.

### 4.3 Persons of interest

**Udacity `ud120-projects` [V] — do not use as a primary label source.**
1,643★. **`GET /LICENSE` → 404; GitHub API reports `license: None`. All rights reserved by default.**
- `poi_names.txt`: 35 names, each `(y)`/`(n)`. **The y/n flag means "is this person's mailbox in the
  corpus", NOT guilt** — only 4 are `(y)`: Lay, Skilling, Forney, Delainey.
- `final_project_dataset.pkl`: **146 people, 18 flagged `poi=True`**, 21 features. **Email features are
  counts, not language.** Only 111/146 have an email address; only 86/146 have `to_messages`.
- **Provenance: an Associated Press wire story, 28 Dec 2005**, retrieved via Wayback. **AP copyright —
  "may not be published, broadcast, rewritten or redistributed."**
- It is a **Dec-2005 snapshot predating the Lay/Skilling verdicts**, and its categories are heterogeneous:
  it lumps together SEC-civil-settlement-only people who *"face no criminal charges"*, a **withdrawn**
  guilty plea (Duncan), an **overturned** conviction (Arthur Andersen), and non-Enron employees (NatWest
  bankers, Merrill executives, Lea Fastow who left in 1997).

**Better ground truth — SEC. [V]** `sec.gov/spotlight/enron.htm`. **~31 distinct named individuals**, each
with a citable Litigation Release number and date: Furst, Hirko, Rogers, Mintz, Pai, Duncan, Bauer,
Lowther, Odom, Castleman, Lynn, McMahon, Causey, Rasmussen, Leboe, DeSpain, Bowen, Hannon, Koenig, Rice,
Lay, Rieker, Skilling, Fastow, Glisan, Gordon, Kopper, Howard, Krautz, Shelby, Yeager. **Includes several
the Udacity list omits — Pai and McMahon in particular are heavy corpus correspondents.** US Government
work → **public domain**.

**DOJ counts conflict across DOJ's own documents. [V — both read.]**
- Aug 2005: *"charges against **33 Enron defendants, including 21 former Enron executives**… **convictions
  of 11**."*
- 2010 accomplishments PDF, two figures **in the same document**: *"**34 defendants, 26 of whom were
  former Enron executives**"* and *"**36 defendants, including 27 former Enron Corporation executives.
  Eighteen of those charged pleaded guilty or were found guilty.**"*

**There is no canonical DOJ name list.** Report as a range: **33–36 charged, ~18 convicted or pleaded**,
citing both conflicting documents. **Lay's convictions were vacated by abatement on his death** — a real
labelling problem.

**Label classes must be kept distinct:** charged ≠ pleaded ≠ convicted ≠ civil-settlement-only ≠
vacated-on-death. The AP list conflates all of these.

### 4.4 Whistleblowers — ⚠️ this changes our labelling scheme

- **Sherron Watkins is NOT a custodian. [V]** Verified absent from all three rosters; there is no
  `watkins-s` maildir. **Whether her August 2001 memo survives inside other people's mailboxes was not
  verified — this must be grepped before either claim is made.**
- **Vince Kaminski IS a major custodian [V]** — `kaminski-v`, "Manager / Risk Management Head", and the
  **largest mailbox in the corpus at 28,465 messages**. The standard second internal dissenter in the
  literature.
- Margaret Ceconi named as a third [S].
- **There is no published whistleblower label set.**

**The Whistleblower group will be n ≈ 1–2. It cannot support statistical comparison and should be treated
as a qualitative case study.**

---

## 5. Critiques and pitfalls — ⚠️ PARTIALLY COMPLETE

*The dedicated critique agent did not return. This section draws on direct retrievals plus material
surfaced incidentally. **Not covered:** published ethics/consent commentary on using the corpus, IRB
considerations, critical data-studies literature, and any systematic quantification of encoding/HTML/
system-mail artefacts. Treat as a starting point, not a finished review.*

**Corpus provenance.** FERC legal-discovery release, ~150 users skewed to senior management. **No
attachments. Redactions applied at affected employees' request** — the corpus has already been
non-randomly thinned, plausibly by exactly the people most motivated to remove incriminating material.
Only the 2015-05-07 version is distributed; earlier versions (2004, 2009, 2011) are superseded and gone,
so older papers are not exactly reproducible. [V]

**⚠️ April 2026 impersonation disclosure. [V]** A vulnerability in the original Enron messaging system
*"allowed users to impersonate others… without leaving a trace."* CMU notes this *probably* does not
affect NLP uses. **For a paper attributing language to named individuals, this is a first-order
limitation, not a footnote.**

**Duplication.** Approximately **half** the ~500k messages are duplicates [S — search summary, no primary
source traced]. One study reports 517,424 emails / 242,944 unique content SHA1s → **252,759 after dedup**
[S]. Folders like `all_documents` are **computer-generated**, not user-created [S]. **Measure this
ourselves — a dedup rate we computed is worth more than a cited one.**

**Survivorship and sampling bias. [V — Agarwal et al. 2012.]** The Shetty & Adibi job-title list, backbone
of most Enron ML work, covers only "core" employees **whose complete inboxes survived**. **Our Convicted
vs Employee comparison is confounded with seniority, department, mailbox-survival, and time period
simultaneously.**

**The role confound is documented, not speculative. [V — Keila & Skillicorn 2005.]** *"A clear effect of
company role"* on word-use similarity — a strong signal — while criminality was only *"slightly
distinctive."* **The larger effect in our data will be role, not fraud.**

**Base rate.** ~18 positives among ~150 people. Accuracy is meaningless at this ratio.

**No email-level ground truth. [V — Crabb 2014]:** *"no definitive identification of deceptive emails is
possible, as no ground-truth is available."* Our label is necessarily person-level, capping effective N at
~150.

**Quoted-text contamination.** Gilbert (2012) strips quoted/forward text as step one [V]; Crabb (2014)
strips all received and forwarded text [V]; Iqbal et al. (2010) find **structural/formatting features are
the strongest authorship signal** [V]. Unstripped quotes will inflate any stylometric signal by mixing in
the correspondent's language.

**Leakage, quantified on this exact corpus. [V — Gilbert 2012]:** relaxing corpus filters moved accuracy
from **70.7% to 91%**. The best-documented instance of Enron-specific over-claiming, from the author
himself.

**Network beats text. [V — Agarwal et al. 2012]:** SNA baseline 83.88% vs a **theoretical NLP ceiling of
59.61%**.

---

## 6. Gap analysis

**The space is busy but shallow, and the specific thing we propose has not been done properly. There is a
real gap. It is narrower than we might hope, and the honest version of the contribution is partly
negative.**

**Genuinely occupied:**
- Pennebaker-style deception cues on Enron: **done in 2005** (Keila & Skillicorn). Result hedged and weak.
- Linguistic abstractness vs Enron fraud events: **done in 2010** (Louwerse et al.), authors explicitly
  disclaiming prediction.
- Role/hierarchy inference from Enron language: **well worked** (Bramsen 2011, Gilbert 2012, Agarwal 2012,
  Prabhakaran & Rambow 2014) — and this literature has *better* methodology than the fraud literature.
- Enron authorship attribution: **mature**.
- Psycholinguistic insider-risk indices: **attempted** (Brown/Watkins/Greitzer 2013; Greitzer et al.
  2013). **Pull these before claiming novelty.**
- POI prediction on Enron: **one preprint** (Noever 2020), dominated by financial features.

**Genuinely open — four defensible claims:**

1. **No published Enron insider-language work uses a person-disjoint split for a fraud/POI target.**
   Bramsen (2011) does author-disjoint for the *power* task on 142 pairs; nobody does it for fraud.
   Noever's language-only AUROC 0.76 has no described protocol.
2. **Enron is absent from every standardised authorship benchmark** — VALLA's 15 datasets exclude it [V].
   There is no agreed split protocol for Enron, so proposing one is a contribution.
3. **Almost all insider-threat NLP is CERT, and CERT is synthetic.** Real-corpus work is rare enough to
   matter.
4. **Interactional/dyadic features consistently beat lexical ones** (Prabhakaran & Rambow's dangling
   requests; Ludwig et al.'s intertextual exchange cues; McCallum's ART) **and have never been combined
   with a deception-cue lexicon on Enron.**

### Recommended framing

Given Hauch (*d* ≈ 0.2), Larcker & Zakolyukina (+6–16 points), Purda & Skillicorn (+5 points, 82% → 71%
out of sample), Noever (AUROC 0.76, protocol undescribed), and Gröndahl & Asokan ("no content-invariant
stylistic trace"), **the expected honest result for a person-disjoint language-only index on ~18 positives
is modest and possibly null.**

The stronger paper is a **methodological calibration study**: build the index properly, evaluate
person-disjoint against a metadata-only baseline and a majority-class baseline, and **deliberately run the
Gilbert experiment** — report what the same model scores under email-level splitting, under balanced-test
resampling, and under loosened filtering.

**"This pipeline reports 0.95 the way the literature does it and 0.6 the way it should be done"** is a
more useful and more citable contribution than another 95% number, and it is squarely within reach of the
Phase 1 design already agreed. The Convicted/Employee/Whistleblower/Other structure also lets us do
something the literature mostly has not: **show how much of any apparent fraud signal is actually role.**

---

## 7. Concrete recommendations for the build

**Extraction pipeline**
1. **Do not `pip install talon`** — will not install on Python ≥3.11 (cchardet), dead since Feb 2022,
   modernisation PR ignored as recently as Aug 2026, no published ML accuracy figure. Every "maintained
   fork" is also dead.
2. **stdlib `email`/`mailbox` + `quotequail`** (MIT, 2026-08-12, the only candidate with first-class
   `-----Original Message-----` support — *the* Enron case). Add `SpamScope/mail-parser` only if MIME
   edge cases bite.
3. **Vendor talon's `signature/bruteforce.py` heuristics** (Apache-2.0, legally clean, cite Mailgun)
   rather than depending on the package.
4. **Write our own maildir loader** — ~60 lines; no viable library exists.
5. **Hand-annotate 300–500 message bodies and report extraction precision/recall.** No published number
   exists to cite, and quote contamination is the largest validity threat in the build.

**Data**
6. **Corpus:** CMU `enron_mail_20150507`, version cited explicitly. Consider **EnronSent** (public domain,
   pre-cleaned, sent-only) as a validation comparator, noting it discards sender/date/thread metadata.
7. **Role labels:** **EnronData.org 148-custodian list (CC-BY 3.0)** — the only cleanly-licensed option,
   keyed on maildir folder names. Accept ~30% N/A. Cross-check the disim 156-table but caveat provenance.
8. **Alias resolution:** `enron-employees.txt` for custodians; Fiore/Heer Berkeley MySQL or a
   reimplementation of the Zhou et al. six-alias rules for the wider population.
9. **POI ground truth: build our own from the SEC spotlight page** (public domain, ~31 named individuals,
   dated Litigation Releases). **Do not build on the Udacity pickle.** Report DOJ counts as a range
   (33–36 charged, ~18 convicted/pleaded), citing both conflicting DOJ documents.
10. **Keep label classes distinct:** charged ≠ pleaded ≠ convicted ≠ civil-settlement-only ≠
    vacated-on-death (Lay).

**Analysis libraries**
11. **spaCy** (POS/lemma/dep), **textstat** (readability, with the Loughran–McDonald caveat), **NRC
    EmoLex** (download script — redistribution prohibited), **LIWC-22 academic licence** (start
    procurement now; prices unpublished), **`empath`** as a cross-lexicon robustness check,
    **`faststylometry`** (MIT) for Burrows's Delta with **`stylo`** (R) as validation reference.
    Reimplement Writeprints features — no maintained implementation exists.

**Evaluation — the part that determines whether the paper survives review**
12. **Person-disjoint (author-disjoint) folds.** Cite Bramsen (2011) for the design and Tyo et al. (2022)
    for the ×a protocol name.
13. **Report the majority-class baseline next to every accuracy figure**, and a **metadata/network-only
    baseline** (per Agarwal et al. 2012: SNA 83.88% vs an NLP ceiling of 59.61%).
14. **Report PR-AUC at the true base rate**, not accuracy on a rebalanced test set.
15. **Any resampling strictly inside training folds, and say so.** Noever's 95.3 vs 72.2 on identical
    features is what happens otherwise.
16. **Control for role explicitly.** Keila & Skillicorn showed the role signal is strong and the
    criminality signal weak on this exact corpus.
17. **Run the Gilbert ablation deliberately** — report what the same model scores under email-level
    splitting, balanced test sets, and loosened filtering. His own 70.7 → 91 is the template.
18. **Add at least one interactional/dyadic feature family** (dangling requests, thread participant
    management, style matching). It beats lexical features in every honest study found, and combining it
    with deception cues on Enron has not been done.
19. **State N prominently: ~150 people, ~18 positives, Whistleblower n ≈ 1–2.**
20. **Limitations must include the CMU April 2026 impersonation disclosure**, corpus redaction at employee
    request, and survivorship bias in the custodian population.

---

## 8. Immediate actions arising

| # | Action | Why |
|---|---|---|
| 1 | **Grep the corpus for the Watkins memo** | Determines whether the Whistleblower class exists at all |
| 2 | **Resolve the Keila & Skillicorn CASCON title** | Our methodology briefing currently carries the disputed title |
| 3 | **Retrieve Brown/Watkins/Greitzer (2013) and Greitzer et al. (2013)** | Nearest prior art by name; novelty claim depends on them |
| 4 | **Retrieve the ProQuest fraud-language dissertation** | Likely the closest prior work; needs library access |
| 5 | **Start LIWC-22 academic licence procurement** | Prices unpublished; lead time unknown |
| 6 | **Measure our own duplication rate** | The "~50% duplicates" figure is untraced |
| 7 | **Verify Larcker & Zakolyukina's 6–16% figure directly** | Currently from a snippet; it anchors our expectations |

---

## 9. Citation status summary

**Verified — retrieved and read (49 sources).** Full list retained in the survey working notes; the
principal ones are cited inline above with **[V]**.

**Unverified — flag before citing.** Keila & Skillicorn CASCON 2005 (title disputed); Newman et al. 2003
(61/67% from snippets); Larcker & Zakolyukina 2012 (6–16% from snippet); Loughran & McDonald 2014 (Fog
critique from snippet); Shetty & Adibi 2004 (**all mirrors dead**); Klimt & Yang 2004; de Vel et al. 2001;
Zhou et al. 2007 six-alias rules; Glasser & Lindauer 2013; Tuor et al. 2017; Le et al. 2020; Soh et al.
2019; Greitzer et al. 2013; Priebe et al. 2005 (provenance of the gender/seniority table); Brysbaert et
al. 2014; the "~50% duplicates" claim; "LIWC features hurt cross-domain performance"; empath's
`create_category()` remote-server behaviour.

**Explicitly could not confirm.** Any paper predicting individual Enron fraud/POI status **from email
language alone under a person-disjoint evaluation with a reported AUROC and base rate.** Noever (2020) is
nearest and its protocol is not described. **If that holds under our own checking, it is our
contribution.**

---

*Working document. No analysis has been run. All processing is local; no data, statistics or model
artefacts leave the analysis machine.*
