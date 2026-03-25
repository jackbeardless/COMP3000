# Problem Statement

## Full Paragraph (Dissertation Introduction)

Existing OSINT collection tools can gather large volumes of information about people — aliases, usernames, domains, email addresses, and related infrastructure — but they routinely produce noisy, ambiguous, and weakly connected results. Analysts must manually decide which records likely belong to the same real-world entity and which are irrelevant or misleading, a process that is time-consuming, inconsistent, and prone to false positives, particularly when targets share common usernames or operate across many platforms. This project addresses that burden by building **Vantage**, an explainable entity disambiguation and triage platform that ingests raw OSINT collection output, normalises and clusters related findings into candidate identity groups, assigns transparent confidence scores grounded in named, weighted evidence features, detects structural contradictions that indicate false-positive risk, and provides an interactive analyst review interface — reducing the cognitive load on analysts while preserving human oversight and accountability.

---

## Short Version (Abstract)

OSINT investigations produce large, noisy datasets that analysts must manually triage for identity linkage. Vantage addresses this by applying structured clustering, feature-based confidence scoring, and contradiction detection to raw OSINT output, producing explainable, analyst-reviewable results rather than opaque ranked lists. A controlled LLM layer adds plain-English evidence summaries without replacing deterministic scoring logic.

---

## One-Sentence Version (Presentation / Demo)

Vantage reduces false positives in OSINT identity investigations by clustering multi-source findings, scoring them with explainable evidence features, and flagging structural contradictions — all reviewable by a human analyst.

---

## The Problem in Numbers

- A typical SpiderFoot scan against a common username returns **50–200+ raw events**
- Without clustering, analysts must manually evaluate every result independently
- Username collisions (multiple people sharing the same handle) are extremely common — especially on older or niche platforms
- No standard tool exposes *why* a result was ranked the way it was — scores are opaque
- LLM-only approaches introduce hallucination risk and are not auditable

---

## What Vantage Fixes

| Problem | Vantage Solution |
|---|---|
| Raw OSINT is noisy | Clustering groups related findings by platform + handle |
| Scores are opaque | Feature breakdown shows every +/- contribution |
| False positives are high | Contradiction detection flags identity collisions and structural inconsistencies |
| LLMs make unjustified decisions | LLM is restricted to explanation generation only; scoring is deterministic |
| No audit trail | Every score, flag, and annotation is stored and queryable |
| Results are a flat list | Graph view shows entity relationships visually |
