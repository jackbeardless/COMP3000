
PROJECT NAME: Vantage
# Project aim you should build around

My project should be framed as something like:

**“An explainable OSINT entity disambiguation and triage platform for reducing false positives in multi-source identity investigations.”**

That framing is strong because it says:

- you’re solving a clear problem
    
- you’re not just “doing OSINT”
    
- you care about explainability
    
- you care about analyst trust
    
- you care about false positives, which is a very real issue
    

---

# MASTER TO-DO LIST

# Phase 1 — Lock the problem definition

## 1. Write a one-paragraph problem statement

You need to define exactly what the system is fixing. (Create markdown file)

Write something close to:

> Existing OSINT collection tools can gather large amounts of information about people, aliases, usernames, domains, emails, and related infrastructure, but they often produce noisy, ambiguous, and weakly connected results. Analysts must manually decide which records likely belong to the same entity and which are irrelevant or misleading. This project aims to reduce that burden by building an explainable entity disambiguation system that clusters related findings, assigns confidence scores, and provides evidence-backed reasoning for analyst review.

### Output

- 1 polished paragraph for dissertation intro
    
- 1 shorter version for abstract
    
- 1 sentence version for presentation/demo
    

---

## 2. Define the core research question (add into the markdown file)

Pick one main question and 3–4 subquestions. 

### Good main question

**How can explainable scoring and clustering improve entity disambiguation accuracy in OSINT investigations?**

### Good subquestions

- Which features are most useful for linking OSINT findings to the same real-world entity?
    
- How can confidence scoring be made transparent and auditable?
    
- Does graph-based clustering reduce analyst effort compared with raw scan output?
    
- What role, if any, should an LLM play in refinement or explanation?
    

### Output

- final research question set
    

---


# Phase 2 — Redesign the system so it is stronger than “SpiderFoot + LLM”

Right now the pipeline is useful, but it needs stronger architecture.

## 4. Redefine the pipeline into modules

Your architecture should become:

1. **Case creation**
    
2. **Input normalization**
    
3. **OSINT collection**
    
4. **Evidence extraction**
    
5. **Feature engineering**
    
6. **Confidence scoring**
    
7. **Entity clustering**
    
8. **Explainability generation**
    
9. **Analyst review**
    
10. **Report export**
    

### Output

- system architecture diagram
    
- 1 paragraph per module 
    

---

## 5. Add input normalization (I know we already do this but ensure its to a high standard assume the standard is like first class dissertation project or military grade)

Before scanning, standardize inputs.

You should normalize:

- names
    
- usernames
    
- email addresses
    
- domains
    
- phone numbers
    
- timestamps
    
- URLs
    
- location strings
    

### Why this matters

Messy inputs cause duplicate or missed matches. This is a real OSINT problem.

### To-do

- lowercase where appropriate
    
- strip spaces/symbol noise
    
- canonicalize URLs/domains
    
- standardize phone formats
    
- tokenize names and aliases
    
- detect obvious variants
    

### Output

- normalization rules table
    
- preprocessing module
    

---

## 6. Build a structured evidence schema

Do not keep raw SpiderFoot results as your main working format.

Create a common evidence record structure like:

- case_id
    
- source_tool
    
- source_name
    
- source_url
    
- source_type
    
- identifier_found
    
- identifier_type
    
- matched_entity_candidate
    
- timestamp_found
    
- raw_text
    
- extracted_features
    
- source_reliability_score
    
- recency_score
    
- algorithm_score
    
- final_score
    
- explanation
    
- review_status
    

### Why this matters

This makes the system auditable and much more dissertation-grade.

### Output

- evidence schema
    
- database design / ERD
    

---

# Phase 3 — Build the actual intelligence value

## 7. Replace “one confidence score” with feature-based scoring

This is one of the most important upgrades.

Instead of saying:

> this result scored 0.82

Say:

> this result scored 0.82 because of weighted evidence features

### Features to include

- exact username match
    
- partial username match
    
- exact email match
    
- domain overlap
    
- alias similarity
    
- name similarity
    
- shared profile image hash if available
    
- shared bio keywords
    
- shared infrastructure
    
- temporal consistency
    
- geographic consistency
    
- co-occurrence with known identifiers
    
- source credibility
    
- recency
    

### To-do

- define every feature
    
- define how it is measured
    
- define its score range
    
- define its weight
    

### Output

- feature engineering table
    
- scoring formula section
    

---

## 8. Implement source reliability weighting

This solves a real OSINT problem: not all sources are equally trustworthy.

### Create source categories

For example:

- official/public authority
    
- established company platform
    
- professional platform
    
- mainstream media
    
- technical repositories
    
- user-generated forum
    
- paste site
    
- unverified aggregator
    

### Then score reliability

Could be something like:

- high reliability
    
- medium reliability
    
- low reliability
    
- unknown
    

### Output

- source trust model
    
- rationale for weighting
    

---

## 9. Add recency weighting

An old result can still matter, but often current relevance matters.

### To-do

- compute age of finding
    
- create decay logic or recency boost
    
- make recency visible to the analyst
    

### Output

- recency model
    
- visual indicator in UI
    

---

## 10. Build entity clustering (ensure what we have is high standard)

This is probably your highest-value feature.

Instead of treating results independently, group them into likely distinct real-world identities.

### Example

Input: “John Smith”  
System returns:

- Cluster A: likely UK software engineer
    
- Cluster B: likely US academic
    
- Cluster C: uncertain/noisy results
    

### Methods you could use

- threshold-based grouping
    
- graph connected components
    
- similarity graph clustering
    
- hierarchical clustering
    
- density-based grouping
    

### What to show

- cluster confidence
    
- cluster summary
    
- top evidence supporting the cluster
    

### Output

- clustering module
    
- cluster visualization
    
- dissertation section on why clustering is better than flat lists
    

---

## 11. Add contradiction detection

A genuinely useful feature.

Your system should spot when evidence strongly conflicts.

### Examples

- one result says London, another says Sydney
    
- age mismatch
    
- different unrelated employers
    
- same username but incompatible timelines
    
- inconsistent domain ownership periods
    

### UI output

Show:

- “Potential contradiction detected”
    
- “Evidence may refer to multiple individuals”
    

### Why this matters

This is exactly how you reduce false positives.

### Output

- contradiction rules engine
    

---

## 12. Add explainability as a first-class feature

This is non-negotiable if you want serious credibility.

Every score and cluster should answer:

- why this score?
    
- what evidence contributed most?
    
- what evidence reduced confidence?
    
- what is uncertain?
    

### Good explanation format

**Confidence: 0.78**  
Contributing factors:

- exact email match: +0.35
    
- similar username across 3 sources: +0.20
    
- shared domain registration evidence: +0.14
    
- source reliability medium: +0.05
    
- contradictory location evidence: -0.08
    

### Output

- explanation panel in UI
    
- explanation generation logic
    

---

# Phase 4 — Use the LLM correctly

## 13. Restrict the LLM’s role

This is really important.

Do **not** let the LLM be the hidden brain deciding everything.  
That weakens your project academically and professionally.

### Better LLM roles

Use the LLM for:

- summarizing evidence
    
- generating plain-English explanations
    
- producing analyst-friendly cluster summaries
    
- flagging ambiguous cases for review
    
- converting structured evidence into reports
    

Avoid using it for:

- inventing new links
    
- silently overwriting algorithmic scores
    
- making unsupported identity judgments
    

### Better design

- scoring engine = deterministic / transparent
    
- LLM = explanation and interface layer
    

### Output

- revised LLM role in architecture
    
- justification in methodology section
    

---

## 14. Log every LLM action

If the LLM changes wording, interpretation, priority, or summary, log it.

### Log fields

- prompt input
    
- structured evidence passed in
    
- response
    
- timestamp
    
- affected case ID
    
- user who triggered it
    

### Why this matters

This makes the system auditable and avoids “black box” criticism.

### Output

- LLM audit log design
    

---

# Phase 5 — Build features analysts would actually want

## 15. Add case management properly

Not just “make a case.”

Each case should have:

- case title
    
- description
    
- target identifiers
    
- analyst notes
    
- case status
    
- timestamps
    
- linked evidence
    
- linked clusters
    
- exportable summary
    

### Output

- case dashboard
    
- case metadata model
    

---

## 16. Add cross-case linking

Huge feature.

If an identifier appears in multiple cases, show it.

### Example

“This email address appears in 3 previous cases.”  
“This domain overlaps with Case 12 and Case 18.”

### Why this matters

This is operationally valuable and makes the system feel much more serious.

### Output

- case overlap detector
    
- reuse graph or reuse alert
    

---

## 17. Add analyst feedback controls

A strong project allows human correction.

Analyst should be able to mark:

- correct match
    
- incorrect match
    
- uncertain
    
- merge clusters
    
- split clusters
    
- ignore evidence
    
- pin key evidence
    

### Why this matters

Shows human-in-the-loop design, which is very strong academically and professionally.

### Output

- feedback UI
    
- feedback stored in database
    

---

## 18. Add watchlist / priority flags

Let analysts mark:

- high priority entities
    
- high-risk identifiers
    
- infrastructure of interest
    
- persistent aliases
    

### Output

- tagging system
    
- alert logic
    

---

## 19. Add report generation

A military or intelligence-style prototype should generate structured outputs.

### Reports should include

- case summary
    
- investigated identifiers
    
- top findings
    
- entity clusters
    
- supporting evidence
    
- contradictions
    
- confidence explanation
    
- analyst notes
    
- recommendations for further review
    

### Export formats

- PDF
    
- JSON
    
- CSV for evidence table
    

### Output

- report templates
    
- export button
    

---

## 20. Add graph view

This is one of the biggest usability/value upgrades.

### Graph nodes

- person/entity cluster
    
- email
    
- username
    
- domain
    
- phone
    
- profile
    
- company
    
- location
    

### Graph edges

- belongs to
    
- associated with
    
- observed in
    
- registered to
    
- linked by
    
- appears with
    

### Why this matters

OSINT people think in relationships, not just tables.

### Output

- graph visualization
    
- graph schema
    

---

# Phase 6 — Make it look academically serious

## 21. Build a literature review to support your design

You need to cover:

- OSINT challenges
    
- entity resolution / record linkage
    
- explainable AI
    
- analyst trust in intelligence systems
    
- graph-based analysis
    
- confidence scoring in uncertain environments
    
- risks of LLM hallucination in investigative settings
    

### To-do

- find papers on entity resolution
    
- find papers on record linkage
    
- find papers on explainability
    
- find papers on graph analytics
    
- find papers on intelligence analysis bias/noise
    

### Output

- literature matrix
    
- 20–40 sources depending on course level
    

---

## 22. Define your novelty

You need a clear statement of contribution.

Possible contribution:

- combining OSINT collection with explainable clustering
    
- confidence scoring model designed for analyst auditability
    
- structured contradiction detection
    
- controlled use of LLMs for evidence explanation rather than opaque decision-making
    

### Output

- explicit “project contribution” section
    

---

## 23. Create a threats / limitations section

Markers love this if it is honest.

Include:

- incomplete OSINT coverage
    
- bias in public data
    
- risk of false positives
    
- source quality variation
    
- LLM output uncertainty
    
- legal/ethical constraints
    
- inability to confirm ground truth in all cases
    

### Output

- limitations chapter section
    

---

# Phase 7 — Evaluation, which will make or break the dissertation

## 24. Build a ground truth dataset

You need test cases with known outcomes.

### You can create:

- synthetic personas with seeded identifiers
    
- public figures with clearly attributable OSINT traces
    
- controlled sample identities across platforms
    
- deliberately ambiguous cases
    

### Include

- true matches
    
- false matches
    
- near-matches
    
- conflicting cases
    

### Output

- evaluation dataset
    
- label file
    

---

## 25. Define evaluation metrics

At minimum include:

- precision
    
- recall
    
- F1 score
    
- false positive rate
    
- false negative rate
    
- cluster purity or cluster quality
    
- analyst time reduction if you can measure it
    

### Output

- metrics section
    
- evaluation plan
    

---

## 26. Compare against baselines

You need comparison, not just “my system works.”

### Baselines

- raw SpiderFoot results only
    
- simple exact-match rules only
    
- score without clustering
    
- score without explainability
    
- score with vs without source weighting
    
- score with vs without contradiction detection
    

### Output

- ablation study
    
- comparison tables
    

---

## 27. Run false-positive-focused testing

This is especially important for your use case.

### Test:

- common names
    
- reused usernames
    
- old stale identifiers
    
- name collisions
    
- shared company domains
    
- burner emails
    
- generic bios
    

### Output

- false-positive case study section
    

---

## 28. Evaluate the LLM separately

Do not just say “the LLM improved it.”

Measure:

- explanation usefulness
    
- hallucination rate
    
- consistency
    
- whether users trust the output more
    
- whether explanations align with algorithm scores
    

### Output

- LLM evaluation subsection
    

---

## 29. Run a small usability study if possible

Even 3–8 users can help if done properly.

### Ask participants to assess:

- clarity of confidence score
    
- usefulness of cluster view
    
- trust in explanations
    
- ability to find relevant evidence quickly
    
- whether graph view helped
    

### Output

- usability findings
    
- participant feedback table
    

---

# Phase 8 — Security, ethics, realism

## 30. Add role-based access idea, even if basic

Even in a prototype, show:

- analyst role
    
- admin role
    
- reviewer role
    

### Why this matters

It makes the system feel deployable rather than just academic.

### Output

- simple access-control model
    

---

## 31. Add audit logging everywhere

Log:

- scans run
    
- evidence added
    
- score changes
    
- analyst overrides
    
- report generation
    
- LLM summaries
    

### Output

- audit trail feature
    
- event log schema
    

---

## 32. Include ethics and legal compliance discussion

You should explicitly discuss:

- public-source boundaries
    
- privacy concerns
    
- misidentification harms
    
- proportionality
    
- responsible use
    
- data retention
    
- human review requirements
    

### Output

- ethics section
    
- safe-use statement
    

---

## 33. Add confidence disclaimers in the UI

Every result should make clear:

- score does not equal certainty
    
- findings require analyst review
    
- contradictory evidence may exist
    

### Output

- responsible UI language
    

---

# Phase 9 — Front-end and UX improvements

## 34. Improve the case dashboard

Dashboard should show:

- case summary
    
- scan status
    
- number of evidence items
    
- number of clusters
    
- highest-confidence findings
    
- contradictions
    
- flagged items
    
- recent analyst actions
    

### Output

- polished dashboard
    

---

## 35. Add filtered evidence table

Allow filtering by:

- source
    
- source reliability
    
- identifier type
    
- score range
    
- cluster
    
- contradiction flag
    
- recency
    
- analyst-reviewed status
    

### Output

- searchable evidence table
    

---

## 36. Add a cluster page

Each cluster should show:

- cluster summary
    
- associated identifiers
    
- related profiles
    
- strongest supporting evidence
    
- contradictions
    
- confidence explanation
    
- analyst notes
    
- merge/split controls
    

### Output

- cluster detail page
    

---

## 37. Add analyst note-taking

Very useful and easy to justify.

### Output

- note system attached to evidence, cluster, and case
    

---

## 38. Add review queues

Example queues:

- high-confidence unreviewed
    
- contradictory findings
    
- low-confidence but cross-case linked
    
- recent findings only
    

### Output

- triage workflow
    

---

# Phase 10 — Dissertation writing tasks

## 39. Write the abstract early, then rewrite it later

Draft one now, finalise after evaluation.

### Output

- early abstract
    
- final abstract
    

---

## 40. Draft the chapter structure now (in markdown file)

Recommended structure:

1. Introduction
    
2. Background and literature review
    
3. Problem definition and requirements
    
4. System design
    
5. Implementation
    
6. Evaluation
    
7. Discussion
    
8. Limitations and ethical considerations
    
9. Conclusion and future work
    

### Output

- dissertation outline
    

---

## 41. Write a requirements table (in markdown file)

Split requirements into:

- functional
    
- non-functional
    

### Functional examples

- create case
    
- ingest identifiers
    
- run scan
    
- score evidence
    
- cluster results
    
- generate explanation
    
- export report
    

### Non-functional examples

- transparency
    
- auditability
    
- usability
    
- modularity
    
- reproducibility
    

### Output

- requirements table
    

---

## 42. Create architecture and data flow diagrams

You should produce:

- high-level system architecture
    
- data flow diagram
    
- database schema
    
- scoring flow
    
- clustering flow
    
- analyst review flow
    

### Output

- final diagrams for dissertation
    

---

# Phase 11 — Presentation/demo readiness

## 44. Prepare 3 demo cases

You need:

- one easy clear match
    
- one ambiguous identity case
    
- one contradictory / false-positive-heavy case
    

### Output

- reliable demo dataset
    

---

## 45. Create a before vs after demo narrative

Show:

- raw OSINT collection is noisy
    
- your system structures it
    
- your system clusters it
    
- your system explains it
    
- analyst can review faster and more safely
    

### Output

- demo script
    

---

## 46. Prepare 3 headline claims you can defend (in markdown file)

For example:

- “The system reduces false-positive exposure by surfacing contradictory evidence.”
    
- “Explainable scoring improves analyst trust over opaque ranking.”
    
- “Entity clustering makes OSINT triage more usable than flat-source listings.”
    

### Output

- viva/demo talking points
    


---

# Minimum viable “excellent” version

If you want the smallest version that still feels strong, aim for this:

- case creation
    
- SpiderFoot ingestion
    
- structured evidence schema
    
- feature-based score engine
    
- source reliability weighting
    
- entity clustering
    
- contradiction detection
    
- explainability panel
    
- graph view
    
- analyst review controls
    
- report export
    
- evaluation against baselines
    

That is enough to look serious.

---

# The single most important design decision

The strongest version of your project is:

**algorithm decides score, graph groups entities, human reviews, LLM explains**

Not:

**LLM decides everything**

That one choice will massively improve:

- dissertation quality
    
- trustworthiness
    
- real-world usefulness
    
- credibility with technical assessors
    

# Final checklist 

## Core research

-  write problem statement
    
-  write main research question
    
-  write subquestions
    
-  define project scope
    
-  define project contribution
    

## System design

-  design architecture
    
-  design evidence schema
    
-  design database
    
-  design scoring features
    
-  design source reliability model
    
-  design recency model
    
-  design clustering model
    
-  design contradiction rules
    
-  design explanation format
    

## Implementation

-  build case creation
    
-  build input normalization
    
-  integrate SpiderFoot ingestion
    
-  structure evidence storage
    
-  implement scoring engine
    
-  implement reliability weighting
    
-  implement recency weighting
    
-  implement clustering
    
-  implement contradiction detection
    
-  implement explanation engine
    
-  implement graph view
    
-  implement case dashboard
    
-  implement evidence filters
    
-  implement cluster page
    
-  implement analyst notes
    
-  implement review controls
    
-  implement cross-case linking
    
-  implement export/reporting
    
-  implement audit logs
    

## LLM

-  restrict LLM role
    
-  use LLM for summary/explanation only
    
-  log LLM inputs/outputs
    
-  test hallucination risk
    

## Evaluation

-  build ground truth dataset
    
-  define metrics
    
-  choose baselines
    
-  test raw SpiderFoot baseline
    
-  test scoring without clustering
    
-  test scoring with clustering
    
-  test contradiction detection value
    
-  measure false positives
    
-  evaluate explanation usefulness
    
-  run usability study if possible
    




