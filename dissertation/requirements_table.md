# Requirements Table

## Functional Requirements

| ID | Requirement | Priority | Implemented |
|---|---|---|---|
| FR-01 | The system shall allow authenticated users to create named investigation cases with a target identifier | Must | ✅ |
| FR-02 | The system shall allow users to run an OSINT pipeline scan against a case target | Must | ✅ |
| FR-03 | The system shall ingest SpiderFoot JSON output and normalise events into structured records | Must | ✅ |
| FR-04 | The system shall cluster normalised OSINT findings by platform and handle | Must | ✅ |
| FR-05 | The system shall assign a heuristic confidence score to each cluster based on named evidence features | Must | ✅ |
| FR-06 | The system shall expose the per-feature score breakdown to the analyst | Must | ✅ |
| FR-07 | The system shall weight confidence scores by source reliability tier | Must | ✅ |
| FR-08 | The system shall detect and flag structural contradictions within and across clusters | Must | ✅ |
| FR-09 | The system shall optionally invoke an LLM to generate a plain-English rationale for each cluster | Should | ✅ |
| FR-10 | The system shall store all scores, features, flags, and rationale in a persistent database | Must | ✅ |
| FR-11 | The system shall allow analysts to annotate clusters with a verdict (confirmed / disputed / needs review) | Must | ✅ |
| FR-12 | The system shall allow analysts to add free-text notes to any cluster | Must | ✅ |
| FR-13 | The system shall display scan results as a filterable, sortable cluster list | Must | ✅ |
| FR-14 | The system shall display a graph view of entity relationships for a completed scan | Should | ✅ |
| FR-15 | The system shall display confidence distribution, verdict breakdown, and platform coverage charts | Should | ✅ |
| FR-16 | The system shall stream live pipeline progress to the analyst via WebSocket | Should | ✅ |
| FR-17 | The system shall allow export of scan results in JSON and CSV formats | Should | ✅ |
| FR-18 | The system shall maintain a scan history per case | Must | ✅ |
| FR-19 | The system shall support configurable pipeline parameters per scan (threshold, model, dry run, etc.) | Should | ✅ |
| FR-20 | The system shall display a disclaimer on all results stating scores do not equal certainty | Must | ✅ |

---

## Non-Functional Requirements

| ID | Requirement | Category | Implemented |
|---|---|---|---|
| NFR-01 | All scoring decisions must be traceable to named, described evidence features | Transparency | ✅ |
| NFR-02 | Every cluster annotation and LLM call must be stored with a timestamp and user ID | Auditability | ✅ |
| NFR-03 | The LLM must not make final scoring decisions; it is restricted to explanation generation | Trustworthiness | ✅ |
| NFR-04 | The system must support multi-user access with per-user data isolation | Security | ✅ |
| NFR-05 | Row-level security must prevent users accessing each other's cases, scans, and clusters | Security | ✅ |
| NFR-06 | The frontend must be usable without OSINT training — plain English labels throughout | Usability | ✅ |
| NFR-07 | The pipeline must be modular — each step independently testable and replaceable | Modularity | ✅ |
| NFR-08 | The test suite must achieve >90% coverage of core scoring and clustering logic | Reliability | ✅ (164 tests) |
| NFR-09 | The system must handle LLM rate limits gracefully with automatic retry and local fallback | Reliability | ✅ |
| NFR-10 | Confidence scores must be clamped to [0, 1] and verdicts must be deterministically derived from them | Correctness | ✅ |
| NFR-11 | The system must operate locally — no data sent to external services beyond Supabase and Gemini API | Privacy | ✅ |
| NFR-12 | All results must include a confidence disclaimer visible to the analyst | Ethics | ✅ |
| NFR-13 | The system architecture must be documented sufficiently for reproduction | Reproducibility | ✅ |

---

## Scoring Feature Engineering Table

| Feature | Description | Score Delta | Rationale |
|---|---|---|---|
| base_score | Starting prior before any evidence | +0.20 | Weak prior that any found account could be the target |
| module_corroboration | Number of independent SpiderFoot modules that found this cluster | +0.15 per module, max +0.45 | Multiple independent sources reduce false-positive probability |
| profile_url | URL matches the structure of a direct user profile page | +0.10 | Profile pages are more likely to be genuine identity evidence |
| non_profile_url | URL is a search result, tool page, redirect, or archive | −0.15 | Non-profile URLs are weaker identity evidence |
| exact_handle_match | Extracted handle exactly matches the target (case-insensitive) | +0.30 | Strong identity signal |
| high_signal_platform | Exact match on a high-signal platform (GitHub, Twitter, etc.) | +0.10 | These platforms require account creation and are widely used |
| low_signal_platform | Platform is low-signal (anonymous, niche, or defunct) | −0.10 | Weaker identity evidence regardless of handle match |
| target_in_url | Target identifier appears somewhere in the URL path | +0.05 | Weak corroborating signal |
| source_reliability (high) | Platform is high-trust (verified identity, established) | +0.06–+0.08 | Higher trust source = more reliable OSINT |
| source_reliability (medium) | Platform is medium-trust | +0.02–+0.03 | Moderate uplift |
| source_reliability (low) | Platform is low-trust (paste site, adult, anonymous) | −0.04–−0.08 | Penalise unreliable sources |

---

## Source Reliability Tier Definitions

| Tier | Platforms | Rationale |
|---|---|---|
| **High** | GitHub, LinkedIn, Twitter/X, Instagram, Reddit, Twitch, YouTube, Patreon | Established platforms with real-name or verified-identity norms; account creation is public record |
| **Medium** | Steam, Chess.com, Last.fm, DeviantArt, Stack Overflow, Wattpad, Mixcloud, Letterboxd | Legitimate platforms with lower authentication bar; useful corroborating sources |
| **Low** | Pastebin, Archive.org, Fansly, Tinder, BDSMLR, Periscope, Chatango, LiveJournal, Kik | Anonymous, unverified, adult-only, or defunct platforms; weak OSINT sources |
| **Unknown** | All other platforms | No reliability assessment available; treated as neutral |
