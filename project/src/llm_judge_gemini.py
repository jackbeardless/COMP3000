import json
import os
import time
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from google import genai
from google.genai import errors as genai_errors

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"

HIGH_SIGNAL_PLATFORMS = {
    "github", "instagram", "twitch", "reddit", "twitter",
    "linkedin", "youtube", "patreon"
}
PLATFORM_TRUST = {
    "github": "high",
    "instagram": "high",
    "reddit": "high",
    "twitch": "high",
    "patreon": "high",
    "steam": "medium",
    "chess": "medium",
    "lastfm": "medium",
    "mixcloud": "medium",
    "wattpad": "medium",
    "deviantart": "medium",
    "disqus": "low",
    "fansly": "low",
    "tinder": "low",
    "archive": "low",
    "wikimedia": "low",
}
AUTO_LOW_STATUSES = {"search_or_tooling", "invite_or_redirect"}
AUTO_MAYBE_STATUSES = {"unknown_pattern"}


@dataclass
class JudgeConfig:
    threshold: float = 0.75
    include_low: bool = False
    dry_run: bool = False
    model: str = "gemini-2.5-flash"
    batch_size: int = 10
    skip_obvious_noise: bool = True
    retry_sleep_seconds: int = 20


def latest_llm_ready_json() -> Path:
    files = sorted(
        RESULTS_DIR.glob("llm_ready_clustered_normalized_spiderfoot_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not files:
        raise FileNotFoundError("No llm_ready_clustered_normalized_spiderfoot_*.json in results/")
    return files[0]


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def chunks(lst: List[Any], n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def build_batch_prompt(target: str, clusters: List[Dict[str, Any]]) -> str:
    return f"""
You are judging whether OSINT account clusters likely belong to the target identity.

Target: {target}

Clusters JSON array:
{json.dumps(clusters, ensure_ascii=False)}

Return STRICT JSON ONLY (no markdown) as an array with the SAME length and SAME order:
[
  {{
    "final_confidence": number between 0 and 1,
    "verdict": "likely" | "maybe" | "low",
    "rationale": "short explanation",
    "flags": []
  }}
]

Rules:
- Always include all four keys in every result, even if flags is an empty list.
- likely if final_confidence >= 0.75
- maybe if 0.55 <= final_confidence < 0.75
- low if final_confidence < 0.55

Scoring guidance:
- Treat heuristic_score as a baseline estimate.
- Only move substantially above or below heuristic_score when the structural evidence strongly justifies it.
- Exact handle match alone is NOT enough for "likely".
- "likely" should usually be reserved for strong platforms or especially convincing profile URLs.
- For weak/obscure/niche platforms, matching the same handle should often be "maybe", not "likely".
- Use platform_trust as a hint: high-trust platforms can support stronger confidence than low-trust platforms.
- Downrank invites, search/tooling pages, archives, redirects, API/search pages.
- Downrank adult-content or niche-site matches unless the evidence is structurally very strong.
- Uprank exact handle matches on high-signal platforms with profile-like URLs.
- Be conservative. If uncertain, lower the score.
- Do NOT infer anything about the person beyond linkage confidence.
""".strip()


def judge_cluster_dry(target: str, cluster: Dict[str, Any]) -> Dict[str, Any]:
    score = float(cluster.get("heuristic_score", 0.0))
    status = (cluster.get("status") or "").lower()
    plat = (cluster.get("platform") or "").lower()
    handle = (cluster.get("handle") or "") or ""
    target_l = (target or "").lower()

    if status in AUTO_LOW_STATUSES:
        score -= 0.25

    if status in AUTO_MAYBE_STATUSES:
        score -= 0.10

    if plat in HIGH_SIGNAL_PLATFORMS and target_l and handle.lower() == target_l:
        score += 0.05

    score = clamp01(score)

    if score >= 0.75:
        verdict = "likely"
    elif score >= 0.55:
        verdict = "maybe"
    else:
        verdict = "low"

    return {
        "final_confidence": score,
        "verdict": verdict,
        "rationale": f"dry_run: adjusted heuristic_score={cluster.get('heuristic_score')} status={status}",
        "flags": [f"status:{status}"] if status else [],
    }


def judge_cluster_local_noise(cluster: Dict[str, Any]) -> Dict[str, Any]:
    """
    Auto-handle obvious noise without spending LLM requests.
    """
    status = (cluster.get("status") or "").lower()
    plat = (cluster.get("platform") or "").lower()

    if status == "invite_or_redirect":
        return {
            "final_confidence": 0.20,
            "verdict": "low",
            "rationale": "Auto-low: invite/redirect style URL, not a direct profile.",
            "flags": [f"status:{status}"],
        }

    if status == "search_or_tooling":
        return {
            "final_confidence": 0.15,
            "verdict": "low",
            "rationale": "Auto-low: search/tooling/archive-style URL, not a direct profile.",
            "flags": [f"status:{status}"],
        }

    if status == "unknown_pattern":
        return {
            "final_confidence": 0.45,
            "verdict": "low",
            "rationale": "Auto-low: unknown pattern with weak structural evidence.",
            "flags": [f"status:{status}"],
        }

    return {
        "final_confidence": clamp01(float(cluster.get("heuristic_score", 0.0))),
        "verdict": "maybe",
        "rationale": "Fallback local classification.",
        "flags": [f"platform:{plat}"],
    }

def validate_batch_results(batch_results: List[Dict[str, Any]], expected_len: int) -> List[Dict[str, Any]]:
    if not isinstance(batch_results, list):
        raise ValueError("Gemini response was not a list.")

    if len(batch_results) != expected_len:
        raise ValueError(f"Gemini returned {len(batch_results)} results for batch size {expected_len}.")

    valid_verdicts = {"likely", "maybe", "low"}
    fixed_results: List[Dict[str, Any]] = []

    for i, item in enumerate(batch_results):
        if not isinstance(item, dict):
            raise ValueError(f"Batch result {i} is not an object.")

        # only require the core fields
        missing = {"final_confidence", "verdict", "rationale"} - set(item.keys())
        if missing:
            raise ValueError(f"Batch result {i} missing keys: {sorted(missing)}")

        fixed = dict(item)

        fixed["final_confidence"] = clamp01(fixed.get("final_confidence", 0.0))

        verdict = str(fixed.get("verdict", "low")).strip().lower()
        if verdict not in valid_verdicts:
            verdict = "low"
        fixed["verdict"] = verdict

        fixed["rationale"] = str(fixed.get("rationale", "")).strip()

        flags = fixed.get("flags", [])
        if not isinstance(flags, list):
            flags = [str(flags)]
        fixed["flags"] = [str(x) for x in flags]

        fixed_results.append(fixed)

    return fixed_results
    
def post_adjust_result(cluster: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Conservative final adjustment after LLM output.
    Prevents weak platforms / edge-case URLs from being over-promoted.
    """
    out = dict(result)

    plat = (cluster.get("platform") or "").lower()
    trust = (cluster.get("platform_trust") or "unknown").lower()
    status = (cluster.get("status") or "").lower()
    urls = cluster.get("urls") or []
    score = clamp01(out.get("final_confidence", 0.0))

    url_text = " ".join(urls).lower()

    # Never allow obvious non-profile patterns to be promoted
    if status in {"search_or_tooling", "invite_or_redirect"}:
        score = min(score, 0.20)

    # Weak/unknown platforms should rarely become "likely"
    if trust in {"unknown", "low"} and score > 0.74:
        score = 0.70

    if plat in {"7cups", "artbreeder", "duolingo", "flipboard", "genius", "imageshack", "kik", "letterboxd", "smule"}:
        score = min(score, 0.70)
    # Tip/donation pages are weaker than real profiles
    if "/tip" in url_text:
        score = min(score, 0.70)

    # Adult/dating platforms should not become likely from handle match alone
    if plat in {"fansly", "tinder", "bdsmlr"}:
        score = min(score, 0.40)

    # Defunct/legacy-ish platforms should be capped
    if plat in {"periscope"}:
        score = min(score, 0.50)

    # Recompute verdict from adjusted score
    if score >= 0.75:
        verdict = "likely"
    elif score >= 0.55:
        verdict = "maybe"
    else:
        verdict = "low"

    out["final_confidence"] = score
    out["verdict"] = verdict
    return out

def call_gemini_json_batch(
    client: genai.Client,
    prompt: str,
    model: str,
    retry_sleep_seconds: int,
) -> List[Dict[str, Any]]:
    while True:
        try:
            resp = client.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            )
            text = (resp.text or "").strip()
            data = json.loads(text)
            if not isinstance(data, list):
                raise ValueError("Gemini response was not a list.")
            return data

        except genai_errors.ClientError as e:
            if getattr(e, "status_code", None) == 429:
                print(f"Rate limited (429). Sleeping {retry_sleep_seconds}s and retrying...")
                time.sleep(retry_sleep_seconds)
                continue
            raise


def main() -> Path:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set. Export it as an environment variable.")

    try:
        threshold = float(os.getenv("OSINT_THRESHOLD", "0.75"))
        batch_size = int(os.getenv("OSINT_BATCH_SIZE", "20"))
        retry_sleep = int(os.getenv("OSINT_RETRY_SLEEP", "20"))
    except ValueError as e:
        raise RuntimeError(f"Invalid env var value: {e}") from e

    cfg = JudgeConfig(
        threshold=threshold,
        include_low=os.getenv("OSINT_INCLUDE_LOW", "0") == "1",
        dry_run=os.getenv("OSINT_DRY_RUN", "0") == "1",
        model=os.getenv("OSINT_MODEL", "gemini-2.5-flash"),
        batch_size=batch_size,
        skip_obvious_noise=os.getenv("OSINT_SKIP_NOISE", "1") == "1",
        retry_sleep_seconds=retry_sleep,
    )

    fp = latest_llm_ready_json()
    data = json.loads(fp.read_text(encoding="utf-8"))
    target = data.get("target") or ""
    clusters: List[Dict[str, Any]] = data.get("clusters") or []

    client = genai.Client(api_key=key)

    judged: List[Dict[str, Any]] = []
    llm_queue: List[Dict[str, Any]] = []

    # First pass: optionally auto-handle obvious noise locally
    for c in clusters:
        status = (c.get("status") or "").lower()

        c_for_judging = dict(c)
        c_for_judging["platform_trust"] = PLATFORM_TRUST.get((c.get("platform") or "").lower(), "unknown")

        if cfg.skip_obvious_noise and status in (AUTO_LOW_STATUSES | AUTO_MAYBE_STATUSES):
            j = judge_cluster_local_noise(c_for_judging)
            j = post_adjust_result(c_for_judging, j)
            out_c = dict(c_for_judging)
            out_c.update(j)
            judged.append(out_c)
        else:
            llm_queue.append(c_for_judging)

    print("Clusters total:", len(clusters))
    print("Queued for LLM:", len(llm_queue))
    print("Auto-classified:", len(judged))
    print("Batch size:", cfg.batch_size)
    print("Expected Gemini requests:", math.ceil(len(llm_queue) / cfg.batch_size) if llm_queue else 0)
    
    # Second pass: LLM-judge remaining clusters in batches
    if cfg.dry_run:
        for c in llm_queue:
            j = judge_cluster_dry(target, c)
            j = post_adjust_result(c, j)
            out_c = dict(c)
            out_c.update(j)
            judged.append(out_c)
    else:
        for batch in chunks(llm_queue, cfg.batch_size):
            prompt = build_batch_prompt(target, batch)

            try:
                batch_results = call_gemini_json_batch(
                    client=client,
                    prompt=prompt,
                    model=cfg.model,
                    retry_sleep_seconds=cfg.retry_sleep_seconds,
                )
                batch_results = validate_batch_results(batch_results, len(batch))

            except Exception as e:
                print(f"Batch failed, falling back locally: {e}")
                batch_results = [judge_cluster_dry(target, c) for c in batch]

            for c, j in zip(batch, batch_results):
                j = post_adjust_result(c, j)
                out_c = dict(c)
                out_c.update(j)
                judged.append(out_c)

    # Sort globally by final confidence
    judged = sorted(judged, key=lambda x: float(x.get("final_confidence", 0.0)), reverse=True)

    shown = [c for c in judged if float(c.get("final_confidence", 0.0)) >= cfg.threshold]
    hidden = [c for c in judged if float(c.get("final_confidence", 0.0)) < cfg.threshold]

    out = {
        "target": target,
        "input_file": fp.name,
        "config": {
            "threshold": cfg.threshold,
            "include_low": cfg.include_low,
            "dry_run": cfg.dry_run,
            "model": cfg.model,
            "batch_size": cfg.batch_size,
            "skip_obvious_noise": cfg.skip_obvious_noise,
            "retry_sleep_seconds": cfg.retry_sleep_seconds,
        },
        "counts": {
            "clusters": len(judged),
            "shown": len(judged) if cfg.include_low else len(shown),
            "hidden": 0 if cfg.include_low else len(hidden),
            "llm_judged": len(llm_queue),
            "auto_classified": len(judged) - len(llm_queue),
        },
        "shown": judged if cfg.include_low else shown,
        "hidden": [] if cfg.include_low else hidden,
    }

    out_path = RESULTS_DIR / f"final_{fp.stem}.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")

    print("Input:", fp.name)
    print("Output:", out_path.name)
    print("Counts:", out["counts"])
    print("Top 10 shown (platform, handle, final_confidence, verdict, status):")
    for c in out["shown"][:10]:
        print(
            "-",
            c.get("platform"),
            c.get("handle"),
            round(float(c.get("final_confidence", 0.0)), 3),
            c.get("verdict"),
            c.get("status"),
        )

    return out_path


if __name__ == "__main__":
    main()