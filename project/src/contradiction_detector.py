"""
contradiction_detector.py

Detects potential contradictions and inconsistencies within and across
OSINT clusters. Returns each cluster annotated with contradiction_flags.

These flags are evidence-backed signals that analysts should investigate
further — they do not invalidate findings but highlight areas of uncertainty.
This is a core component of the explainability and false-positive reduction
goals of the Vantage platform.

Rules
-----
1. source_trust_mismatch
   A high-trust platform returned a low-confidence verdict, suggesting the
   account may belong to a different person sharing the same identifier.

2. structural_inconsistency
   The handle matches the target exactly but the URL is not a direct profile
   page — may be a search result, API reference, or misdirected link.

3. handle_collision_risk
   The same handle appears on multiple platforms with significantly different
   confidence levels — a classic false-positive pattern where two distinct
   people share the same username.

4. signal_volume_mismatch
   Multiple intelligence modules corroborated this cluster yet the final
   confidence remains low — the signals may be indirect or the platform is
   unreliable despite high coverage.
"""
from typing import Any, Dict, List

# Import only the function we need to keep the dependency surface small
from cluster import normalized_handle


CONTRADICTION_DESCRIPTIONS: Dict[str, str] = {
    "source_trust_mismatch": (
        "High-trust platform, low-confidence verdict — this account may belong "
        "to a different person who shares the same identifier on this platform."
    ),
    "structural_inconsistency": (
        "Handle matches the target but the URL is not a direct profile — this "
        "result may be a search page, tool reference, or misdirected link rather "
        "than a genuine profile."
    ),
    "handle_collision_risk": (
        "The same handle appears on other platforms with significantly different "
        "confidence levels — a possible identity collision between two people "
        "using the same username."
    ),
    "signal_volume_mismatch": (
        "Multiple intelligence modules found this account but overall confidence "
        "remains low — investigate whether the signals are indirect or the "
        "platform is unreliable despite high coverage."
    ),
}


def _feature_names(cluster: Dict[str, Any]) -> set:
    return {f.get("feature") for f in (cluster.get("score_features") or [])}


def _module_delta(cluster: Dict[str, Any]) -> float:
    for f in (cluster.get("score_features") or []):
        if f.get("feature") == "module_corroboration":
            return float(f.get("delta", 0.0))
    return 0.0


def detect_contradictions(clusters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Annotate each cluster with contradiction_flags.

    Parameters
    ----------
    clusters : list of cluster dicts (post-LLM judging, with score_features,
               source_reliability, verdict, handle fields present)

    Returns
    -------
    Same list with contradiction_flags: List[str] added/extended on each cluster.
    """
    # Build cross-cluster index: normalised handle → set of verdicts seen
    handle_verdicts: Dict[str, List[str]] = {}
    for c in clusters:
        h = normalized_handle(c.get("handle") or "")
        if h:
            handle_verdicts.setdefault(h, []).append(c.get("verdict") or "low")

    result = []
    for c in clusters:
        flags: List[str] = []
        features = _feature_names(c)
        verdict = c.get("verdict") or "low"
        reliability = c.get("source_reliability") or "unknown"

        # Rule 1: high-trust source but low confidence — possible wrong person
        if reliability == "high" and verdict == "low":
            flags.append("source_trust_mismatch")

        # Rule 2: exact handle match + non-profile URL — structural contradiction
        if "exact_handle_match" in features and "non_profile_url" in features:
            flags.append("structural_inconsistency")

        # Rule 3: same handle appears across platforms with conflicting verdicts
        h = normalized_handle(c.get("handle") or "")
        if h:
            seen_verdicts = set(handle_verdicts.get(h, []))
            if "likely" in seen_verdicts and "low" in seen_verdicts:
                flags.append("handle_collision_risk")

        # Rule 4: many modules found it but confidence is still low
        if _module_delta(c) >= 0.30 and verdict == "low":
            flags.append("signal_volume_mismatch")

        c2 = dict(c)
        c2["contradiction_flags"] = flags
        result.append(c2)

    return result
