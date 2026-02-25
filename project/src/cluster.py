import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

# Treat these as "stronger" signals if username matches exactly
HIGH_SIGNAL_PLATFORMS = {
    "github", "instagram", "twitch", "reddit", "twitter", "linkedin", "youtube", "patreon"
}

# Paths that mean "the username is NOT the first segment"
# (so we should extract differently)
SPECIAL_PATH_PREFIXES = {
    "instagram": [""],  # /<user>/
    "twitch": [""],     # /<user>/
    "reddit": ["user"],
    "github": [""],     # /<user> or /<user>/<repo>
}

def _host(url: str) -> str:
    return urlparse(url).netloc.lower().lstrip("www.")

def _path_parts(url: str) -> List[str]:
    return [p for p in urlparse(url).path.strip("/").split("/") if p]

def platform_guess(url: str, platform_field: Optional[str]) -> str:
    if platform_field:
        return platform_field
    h = _host(url)
    if h.endswith("github.com"):
        return "github"
    if h.endswith("instagram.com"):
        return "instagram"
    if h.endswith("twitch.tv"):
        return "twitch"
    if h.endswith("reddit.com"):
        return "reddit"
    if h.endswith("patreon.com"):
        return "patreon"
    if h.endswith("twitter.com") or h.endswith("x.com"):
        return "twitter"
    if h.endswith("linkedin.com"):
        return "linkedin"
    if h.endswith("youtube.com") or h.endswith("youtu.be"):
        return "youtube"
    return "unknown"

def extract_handle(platform: str, url: str) -> Optional[str]:
    parts = _path_parts(url)
    if not parts:
        return None

    # Reddit: /user/<handle>
    if platform == "reddit":
        if len(parts) >= 2 and parts[0].lower() == "user":
            return parts[1]
        return None

    # GitHub: /<user> or /<user>/<repo>
    if platform == "github":
        # if it's clearly a repo URL, handle is still parts[0]
        return parts[0]

    # Patreon: /<handle>
    if platform == "patreon":
        return parts[0]

    # Twitch/Instagram/Vimeo/etc: often /<handle>
    return parts[0]

def normalized_handle(s: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "", s.lower())

def score_account(target: str, acc: Dict) -> float:
    """
    Confidence score that the account belongs to the target entity.
    This is heuristic + explainable (good for dissertation).
    """
    target_n = normalized_handle(target)

    plat = acc.get("platform") or "unknown"
    url = acc.get("url") or ""
    handle = acc.get("handle") or ""
    handle_n = normalized_handle(handle) if handle else ""

    # Evidence strength: distinct modules supporting the same URL
    signals = acc.get("signals") or []
    modules = {s.get("module") for s in signals if s.get("module")}
    module_count = len(modules)

    # Base score from module support
    score = 0.25 + min(0.15 * module_count, 0.45)  # 0.25..0.70

    # Direct handle match boosts a lot
    if handle_n and handle_n == target_n:
        score += 0.25

        # popular platforms boost a bit more (less likely to be random)
        if plat in HIGH_SIGNAL_PLATFORMS:
            score += 0.10

    # If URL contains the target token anywhere (weaker than handle match)
    if target_n and target_n in normalized_handle(url):
        score += 0.05

    # Clamp
    if score > 1.0:
        score = 1.0
    if score < 0.0:
        score = 0.0
    return score

def cluster_accounts(target: str, accounts: List[Dict]) -> List[Dict]:
    """
    Clusters by (platform, extracted handle). Accounts where handle can't be
    extracted fall back to domain-only buckets.
    """
    clusters: Dict[Tuple[str, str], Dict] = {}

    for acc in accounts:
        url = acc.get("url") or ""
        plat = platform_guess(url, acc.get("platform"))
        handle = extract_handle(plat, url) or ""

        # store extracted handle for downstream use
        acc2 = dict(acc)
        acc2["platform"] = plat
        acc2["handle"] = handle

        key = (plat, normalized_handle(handle) if handle else _host(url))

        c = clusters.get(key)
        if not c:
            c = {
                "platform": plat,
                "handle": handle or None,
                "key": key[1],
                "accounts": [],
            }
        c["accounts"].append(acc2)
        clusters[key] = c

    # compute cluster confidence as max of member scores
    out = []
    for c in clusters.values():
        member_scores = [score_account(target, a) for a in c["accounts"]]
        c["confidence"] = max(member_scores) if member_scores else 0.0

        # helpful explanation fields for dissertation write-up
        c["signals"] = sorted({s.get("module") for a in c["accounts"] for s in (a.get("signals") or []) if s.get("module")})
        c["urls"] = sorted({a.get("url") for a in c["accounts"] if a.get("url")})
        out.append(c)

    # sort highest confidence first
    out.sort(key=lambda x: x["confidence"], reverse=True)
    return out