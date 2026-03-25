# Evaluation Framework

## Overview

The evaluation answers the core research question by measuring whether Vantage's clustering, scoring, and contradiction detection meaningfully improve entity disambiguation accuracy and reduce false positives compared to baselines.

---

## Evaluation Metrics

| Metric | Definition | Why It Matters |
|---|---|---|
| **Precision** | TP / (TP + FP) — of all clusters marked "likely", how many actually belong to the target | Measures false positive rate directly |
| **Recall** | TP / (TP + FN) — of all true target accounts, how many did the system surface as "likely" | Measures coverage / missed findings |
| **F1 Score** | Harmonic mean of precision and recall | Balanced measure for disambiguation quality |
| **False Positive Rate** | FP / (FP + TN) — how often non-target accounts are incorrectly attributed | Primary failure mode for OSINT; most important metric |
| **False Negative Rate** | FN / (FN + TP) — how often target accounts are missed | Secondary concern; missed leads are also harmful |
| **Cluster Purity** | For each cluster, proportion of accounts that are correctly attributed | Measures within-cluster quality |
| **Contradiction Detection Rate** | Proportion of known false-positive cases that generated at least one contradiction flag | Validates the contradiction detection rules |
| **LLM Alignment Rate** | Proportion of LLM verdicts that agree with heuristic verdict (within one tier) | Measures LLM consistency with the deterministic layer |

---

## Ground Truth Dataset

### Construction Methodology

Ground truth cases use **public figures with clearly attributable, publicly documented OSINT traces** — not private individuals.

Each case is manually annotated with:
- `true_match: true/false` per platform found
- `ground_truth_verdict: likely/maybe/low` (expected output)
- `notes`: explanation of why each decision was made

### Case Categories

**Category A — Clear Match (high confidence expected)**
Targets with strong, consistent multi-platform presence under the same handle.
Expected: High precision, most found clusters correctly attributed.

| Case | Target | Platforms Expected | Notes |
|---|---|---|---|
| A1 | jacksepticeye | YouTube, Twitter, Instagram, Twitch, Reddit | Well-known creator, consistent handle across all platforms |
| A2 | Yogscast | YouTube, Twitter, Reddit, Twitch | Gaming collective, consistent brand handle |

**Category B — Ambiguous (mixed confidence expected)**
Targets where username collisions are likely — same handle used by multiple people.

| Case | Target | Challenge | Notes |
|---|---|---|---|
| B1 | john_smith | Very common name, many collisions | Should produce many "low" verdicts and contradiction flags |
| B2 | alex | Single short name, extreme collision risk | Tests whether system correctly downgrades ambiguous matches |

**Category C — False-Positive Heavy (contradiction detection test)**
Targets where the system should produce many contradiction flags and low confidence.

| Case | Target | Challenge | Notes |
|---|---|---|---|
| C1 | admin | Generic username used across thousands of unrelated sites | Tests noise filtering and source reliability downranking |
| C2 | user123 | Generic handle pattern | Tests that low-signal matches are correctly scored low |

### Labelling Process

1. Run SpiderFoot scan for each target
2. Manually review every cluster in the raw output
3. Assign ground truth label (`true_match: true/false`) based on:
   - Public documentation confirming the target uses that platform
   - Corroborating cross-platform signals (bio text, link sharing, etc.)
4. Record expected verdict tier

---

## Baseline Comparisons (Ablation Study)

| Baseline | Description | What It Isolates |
|---|---|---|
| **B0: Raw SpiderFoot** | Count all SpiderFoot events as "found" with equal confidence | Measures the starting noise level before any processing |
| **B1: No clustering** | Score each account individually, no grouping | Isolates the value of clustering |
| **B2: Clustering, no source weighting** | Cluster but use flat scoring without reliability tiers | Isolates the value of source reliability weighting |
| **B3: Clustering + source weighting, no contradiction detection** | Full heuristic scoring but no contradiction flags | Isolates the value of contradiction detection |
| **B4: Heuristic only (no LLM)** | Full pipeline but skip Gemini — use dry-run scores | Isolates the marginal value of the LLM judge |
| **B5: Full Vantage** | Complete pipeline including LLM and contradiction detection | Final system |

### Expected Results Hypothesis

- B0 → B1: Large precision improvement (clustering removes duplicates and merges corroborating signals)
- B1 → B2: Moderate precision improvement on low-trust platform matches
- B2 → B3: Measurable reduction in false positive rate (source weighting catches untrustworthy sources)
- B3 → B4: Small but consistent improvement from contradiction flags (catches identity collision cases)
- B4 → B5: LLM improves rationale quality but minimal score change (by design)

---

## False Positive Case Studies

### Case Study 1 — Username Collision
**Target:** common username used by multiple people on GitHub
**Expected contradiction flags:** `handle_collision_risk`
**Expected outcome:** High-confidence accounts on high-trust platforms (the actual target) vs. low-confidence accounts on low-trust platforms (other people)

### Case Study 2 — Search/Tool Page Misattribution
**Target:** any target with SpiderFoot returning search result pages
**Expected contradiction flags:** `structural_inconsistency`
**Expected outcome:** Clusters with exact handle match but non-profile URLs correctly scored low

### Case Study 3 — Defunct Platform Noise
**Target:** older username on platforms like Periscope or LiveJournal
**Expected:** Source reliability weighting downgrades these correctly; contradiction flags if confidence is still elevated

---

## LLM Evaluation Protocol

### Consistency Test
Run the LLM judge on the same 20-cluster batch three times. Measure:
- Proportion of verdicts that are identical across all three runs
- Mean absolute deviation in `final_confidence` scores
- Threshold: >85% verdict consistency, <0.05 mean absolute deviation

### Alignment Test
Compare LLM verdict to heuristic verdict for each cluster. Measure:
- Proportion agreeing exactly (same tier)
- Proportion agreeing within one tier
- Cases where LLM moved a score by more than 0.20 from heuristic baseline

### Hallucination Check
For 10 clusters, manually verify that the LLM rationale references only information present in the input prompt (platform, handle, URL, modules). Flag any rationale containing invented biographical claims.

---

## Headline Claims to Defend

1. **"Vantage reduces false-positive exposure by surfacing contradiction evidence that raw OSINT tools do not generate."**
   - Evidence: Contradiction detection rate on Category C cases; false positive rate comparison B3 → B4

2. **"Explainable feature-based scoring improves analyst trust over opaque confidence values."**
   - Evidence: Score breakdown panel; every verdict traceable to named features; qualitative usability observations

3. **"Entity clustering makes OSINT triage more efficient than reviewing flat source listings."**
   - Evidence: Cluster count vs. raw event count; how many events collapse into a single high-confidence cluster; ablation B0 → B1

---

## Evaluation Plan — Execution Order

- [ ] Run Category A cases through full pipeline; record precision/recall
- [ ] Run Category B cases; measure false positive rate
- [ ] Run Category C cases; validate contradiction detection rate
- [ ] Run ablation study (B0–B5) on a single Category A case
- [ ] Run LLM consistency test (3 identical batches)
- [ ] Run LLM alignment test (compare to heuristic)
- [ ] Run LLM hallucination spot-check (10 clusters)
- [ ] Write up results tables for Chapter 5
