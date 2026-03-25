# Research Questions

## Main Research Question

**How can explainable confidence scoring and evidence-based clustering improve entity disambiguation accuracy and reduce false positives in open-source intelligence investigations?**

---

## Sub-Questions

### SQ1 — Feature Engineering
**Which evidence features are most useful for linking OSINT findings to the same real-world entity?**

Motivation: Not all signals are equally informative. An exact username match on GitHub is stronger evidence than the same match on a defunct platform. Identifying and weighting the right features is the core engineering challenge.

Investigated through: The feature-based scoring engine in `cluster.py` — exact handle match (+0.30), high-signal platform (+0.10), source reliability weighting (+0.08 to −0.08), module corroboration (+0.15 per module), profile URL structure (+0.10).

---

### SQ2 — Explainability
**How can confidence scoring be made transparent and auditable enough to support analyst trust without adding cognitive overhead?**

Motivation: If analysts cannot understand why a result was scored the way it was, they cannot correct errors or calibrate their trust. Black-box scoring undermines the human-in-the-loop requirement.

Investigated through: The `score_features` breakdown (stored per cluster in the database and displayed in the UI), the contradiction flag system, and LLM-generated rationale text.

---

### SQ3 — False Positive Reduction
**Does evidence-based clustering combined with contradiction detection meaningfully reduce false positive exposure compared to raw OSINT collection output?**

Motivation: False positives are the dominant failure mode in identity disambiguation — particularly with common usernames or platform username collisions.

Investigated through: Baseline comparison (raw SpiderFoot output vs. Vantage-processed output) on ground truth cases, measuring precision and false positive rate before and after clustering and contradiction detection.

---

### SQ4 — LLM Role
**What is the appropriate role for a large language model in an OSINT triage pipeline, and what are the risks of over-relying on it for scoring decisions?**

Motivation: LLMs can produce plausible-sounding but hallucinated justifications. Using them to make scoring decisions rather than explain pre-computed scores introduces unauditable risk.

Investigated through: Architecture decision to restrict Gemini to the explanation/rationale layer only; ablation comparing LLM-adjusted vs. heuristic-only confidence scores; consistency testing of LLM outputs across repeated calls.

---

## Scope

**In scope:**
- Username-based OSINT via SpiderFoot
- Social media and public platform profile linkage
- Heuristic + LLM hybrid confidence scoring
- Analyst review and annotation workflow
- False positive detection via contradiction rules

**Out of scope:**
- Real-time monitoring or alerting
- Facial recognition or image similarity
- Dark web / Tor hidden service scanning
- Proprietary or subscription-based OSINT tools
- Legal interception or non-public data sources
