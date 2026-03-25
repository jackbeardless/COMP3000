# Dissertation Chapter Structure

**Title:** Vantage: An Explainable OSINT Entity Disambiguation and Triage Platform for Reducing False Positives in Multi-Source Identity Investigations

---

## Chapter 1 — Introduction

1.1 Motivation and Context
1.2 Problem Statement
1.3 Project Aims and Objectives
1.4 Main Research Question and Sub-Questions
1.5 Project Scope and Boundaries
1.6 Key Contributions
1.7 Dissertation Structure

**Key content:** Establish the OSINT false-positive problem; frame the project academically; state the research questions; overview the solution; list contributions clearly.

---

## Chapter 2 — Background and Literature Review

2.1 Open-Source Intelligence: Challenges and Tools
2.2 Entity Resolution and Record Linkage
2.3 Confidence Scoring in Uncertain Environments
2.4 Explainable AI (XAI) and Analyst Trust
2.5 Graph-Based Analysis in OSINT and Intelligence
2.6 Large Language Models in Investigative Contexts: Opportunities and Risks
2.7 Human-in-the-Loop Intelligence Systems
2.8 Summary and Gaps in the Literature

**Key content:** Review entity resolution literature (Fellegi-Sunter, Ditto); explainability literature (LIME, SHAP concepts applied to scoring); intelligence analysis bias (Heuer); LLM hallucination risks in factual tasks; graph analytics for OSINT.

---

## Chapter 3 — Requirements and System Design

3.1 Requirements Elicitation
3.2 Functional Requirements
3.3 Non-Functional Requirements
3.4 High-Level System Architecture
3.5 Pipeline Module Design
3.6 Evidence Schema Design
3.7 Database Design and Entity-Relationship Model
3.8 Scoring Engine Design
3.9 Contradiction Detection Design
3.10 LLM Integration Architecture
3.11 Design Decisions and Trade-offs

**Key content:** Requirements table; architecture diagram; data flow diagram; justification for algorithm-first, LLM-explanation design.

---

## Chapter 4 — Implementation

4.1 Technology Stack and Justification
4.2 SpiderFoot Integration and Event Normalisation
4.3 Clustering Algorithm
4.4 Feature-Based Scoring Engine
4.5 Source Reliability Weighting
4.6 Contradiction Detection Engine
4.7 LLM Judge (Gemini) — Scope-Restricted Integration
4.8 FastAPI Backend and Supabase Integration
4.9 React Frontend — Case Management, Scan Results, Graph View
4.10 Testing Strategy and Results

**Key content:** Code walkthrough of key modules; test coverage summary (164 tests); discussion of Python 3.9 compatibility decisions; rate-limit handling; WebSocket progress streaming.

---

## Chapter 5 — Evaluation

5.1 Evaluation Methodology
5.2 Ground Truth Dataset Construction
5.3 Evaluation Metrics
5.4 Baseline Comparisons (Ablation Study)
5.5 False Positive Analysis
5.6 Contradiction Detection Effectiveness
5.7 LLM Evaluation: Consistency, Alignment, Hallucination Risk
5.8 Usability Observations
5.9 Summary of Results

**Key content:** Precision/recall/F1 tables; false positive rate before and after; ablation table; LLM consistency results; case study walkthroughs.

---

## Chapter 6 — Discussion

6.1 Interpretation of Results
6.2 Does Clustering Reduce Analyst Effort?
6.3 Is Explainability Achievable Without Sacrificing Accuracy?
6.4 The Appropriate Role of LLMs in OSINT Pipelines
6.5 Comparison with Related Work
6.6 Unexpected Findings

---

## Chapter 7 — Limitations and Ethical Considerations

7.1 Technical Limitations
7.2 Data Quality and Source Coverage Gaps
7.3 Risk of Misidentification and Harms
7.4 Privacy and Proportionality
7.5 Legal and Regulatory Considerations (GDPR, UK DPA 2018)
7.6 Responsible Use and Deployment Constraints
7.7 Bias in Public Data Sources

---

## Chapter 8 — Conclusion and Future Work

8.1 Summary of Contributions
8.2 Research Questions Revisited
8.3 Future Work
  - Real-time monitoring and alerting
  - Cross-case entity linking at scale
  - Image similarity and profile photo hashing
  - Federated multi-analyst deployment
  - Fine-tuned domain-specific LLM judge
8.4 Closing Remarks

---

## Appendices

A. Full Requirements Table
B. Database Schema (ERD)
C. Scoring Feature Engineering Table
D. Source Reliability Tier Definitions
E. Contradiction Detection Rules
F. Ground Truth Dataset Description
G. Test Suite Summary
H. LLM Prompt Templates
