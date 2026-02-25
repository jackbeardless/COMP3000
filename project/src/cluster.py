import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

HIGH_SIGNAL_PLATFORMS = {
    "github", "instagram", "twitch", "reddit", "twitter", "linkedin", "youtube", "patreon"
}

HOST_PLATFORM_MAP = {
    "github.com": "github",
    "instagram.com": "instagram",
    "twitch.tv": "twitch",
    "reddit.com": "reddit",
    "patreon.com": "patreon",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "linkedin.com": "linkedin",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "vimeo.com": "vimeo",
    "pinterest.com": "pinterest",

    "last.fm": "lastfm",
    "wattpad.com": "wattpad",
    "scratch.mit.edu": "scratch",
    "steamcommunity.com": "steam",
    "chess.com": "chess",

    "disqus.com": "disqus",
    "discord.com": "discord",
    "kik.me": "kik",
    "mixcloud.com": "mixcloud",
    "myspace.com": "myspace",

    "pastebin.com": "pastebin",
    "picsart.com": "picsart",
    "gog.com": "gog",
    "imageshack.com": "imageshack",

    "chyoa.com": "chyoa",
    "kongregate.com": "kongregate",
    "etoro.com": "etoro",
    "truckersmp.com": "truckersmp",
    "zepeto.me": "zepeto",
    "web.zepeto.me": "zepeto",

    "stackoverflow.com": "stackoverflow",

    "archive.org": "archive",
    "web.archive.org": "archive",
    "meta.wikimedia.org": "wikimedia",
}

NON_PROFILE_PLATFORMS = {"archive", "wikimedia"}

def _host(url: str) -> str:
    return urlparse(url).netloc.lower().lstrip("www.")

def _host(url: str) -> str:
    h = urlparse(url).netloc.lower()
    if h.startswith("www."):
        h = h[4:]
    return h

def platform_guess(url: str, platform_field: Optional[str]) -> str:
    if platform_field:
        return platform_field
    h = _host(url)
    for suf, plat in HOST_PLATFORM_MAP.items():
        if h == suf or h.endswith("." + suf):
            return plat
    return "unknown"

def normalized_handle(s: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "", s.lower())

def extract_handle(platform: str, url: str) -> Optional[str]:
    parts = _path_parts(url)
    if not parts:
        return None

    # archive/wiki/etc are not accounts
    if platform in NON_PROFILE_PLATFORMS:
        return None

    # discord invites are codes, not user profiles
    if platform == "discord":
        return None

    # reddit: /user/<handle>
    if platform == "reddit":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "user" else None

    # chess.com: /member/<user>
    if platform == "chess":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "member" else None

    # last.fm: /user/<user>
    if platform == "lastfm":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "user" else None

    # wattpad: /user/<user>
    if platform == "wattpad":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "user" else None

    # scratch: /users/<user>
    if platform == "scratch":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "users" else None

    # steamcommunity: /id/<vanity> or /profiles/<numeric>
    if platform == "steam":
        return parts[1] if len(parts) >= 2 and parts[0].lower() in {"id", "profiles"} else None

    # disqus: /by/<user>
    if platform == "disqus":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "by" else None

    # imageshack: /user/<user>
    if platform == "imageshack":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "user" else None

    # chyoa: /user/<user>
    if platform == "chyoa":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "user" else None

    # gog/pastebin/picsart: /u/<user>
    if platform in {"gog", "pastebin", "picsart"}:
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "u" else None

    # kongregate: /accounts/<user>
    if platform == "kongregate":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "accounts" else None

    # etoro: /people/<user>
    if platform == "etoro":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "people" else None

    # stackoverflow: real profiles are /users/<id>/<name>
    # but /users/filter is search, not a profile.
    if platform == "stackoverflow":
        if len(parts) >= 2 and parts[0].lower() == "users" and parts[1].lower() != "filter":
            # second part is usually numeric id; third part is the display name slug
            return parts[2] if len(parts) >= 3 else parts[1]
        return None

    # truckersmp: /user/<id> might exist; /user/search is not profile
    if platform == "truckersmp":
        if len(parts) >= 2 and parts[0].lower() == "user" and parts[1].lower() != "search":
            return parts[1]
        return None

    # default patterns:
    if platform == "github":
        return parts[0]
    return parts[0]

def is_profile_like(platform: str, url: str) -> bool:
    if platform in NON_PROFILE_PLATFORMS:
        return False

    parts = _path_parts(url)
    if not parts:
        return False

    # common non-profile prefixes
    bad_prefixes = {
        "search", "search.php", "wayback", "web", "api", "share", "wiki", "commands", "filter"
    }
    if parts[0].lower() in bad_prefixes:
        return False

    # stackoverflow filter is not a profile
    if platform == "stackoverflow" and parts[:2] == ["users", "filter"]:
        return False

    # truckersmp search is not a profile
    if platform == "truckersmp" and parts[:2] == ["user", "search"]:
        return False

    return True

def score_account(target: str, acc: Dict) -> Tuple[float, List[str]]:
    """
    Returns (score, reasons[]) so you can explain the confidence.
    """
    reasons: List[str] = []

    target_n = normalized_handle(target)
    plat = acc.get("platform") or "unknown"
    url = acc.get("url") or ""
    handle = acc.get("handle") or ""
    handle_n = normalized_handle(handle) if handle else ""

    signals = acc.get("signals") or []
    modules = {s.get("module") for s in signals if s.get("module")}
    module_count = len(modules)

    score = 0.20
    reasons.append("base=0.20")

    mod_boost = min(0.15 * module_count, 0.45)
    score += mod_boost
    reasons.append(f"module_support(+{mod_boost:.2f}) modules={sorted(m for m in modules if m)}")

    if is_profile_like(plat, url):
        score += 0.10
        reasons.append("profile_like(+0.10)")
    else:
        score -= 0.15
        reasons.append("non_profile_like(-0.15)")

    if handle_n and handle_n == target_n:
        score += 0.30
        reasons.append("exact_handle_match(+0.30)")
        if plat in HIGH_SIGNAL_PLATFORMS:
            score += 0.10
            reasons.append("high_signal_platform(+0.10)")

    if target_n and target_n in normalized_handle(url):
        score += 0.05
        reasons.append("target_in_url(+0.05)")

    # clamp
    score = max(0.0, min(1.0, score))
    return score, reasons

def cluster_accounts(target: str, accounts: List[Dict]) -> List[Dict]:
    clusters: Dict[Tuple[str, str], Dict] = {}

    for acc in accounts:
        url = acc.get("url") or ""
        plat = platform_guess(url, acc.get("platform"))
        handle = extract_handle(plat, url) or ""

        if handle.startswith("@"):
            handle = handle[1:]

        acc2 = dict(acc)
        acc2["platform"] = plat
        acc2["handle"] = handle

        key = (plat, normalized_handle(handle) if handle else _host(url))
        c = clusters.get(key)
        if not c:
            c = {"platform": plat, "handle": handle or None, "key": key[1], "accounts": []}
        c["accounts"].append(acc2)
        clusters[key] = c

    out: List[Dict] = []
    for c in clusters.values():
        scored = [score_account(target, a) for a in c["accounts"]]
        best_score, best_reasons = max(scored, key=lambda t: t[0]) if scored else (0.0, [])
        c["confidence"] = best_score
        c["confidence_reasons"] = best_reasons

        c["signals"] = sorted({
            s.get("module")
            for a in c["accounts"]
            for s in (a.get("signals") or [])
            if s.get("module")
        })
        c["urls"] = sorted({a.get("url") for a in c["accounts"] if a.get("url")})
        out.append(c)

    out.sort(key=lambda x: x["confidence"], reverse=True)
    return out