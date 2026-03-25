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
    "7cups.com": "7cups",
    "artbreeder.com": "artbreeder",
    "deviantart.com": "deviantart",
    "fansly.com": "fansly",
    "flipboard.com": "flipboard",
    "letterboxd.com": "letterboxd",
    "linktr.ee": "linktree",
    "periscope.tv": "periscope",
    "smule.com": "smule",
    "streamelements.com": "streamelements",
    "streamlabs.com": "streamlabs",
    "tinder.com": "tinder",
    "nightbot.tv": "nightbot",
    "blogspot.com": "blogspot",
    "bdsmlr.com": "bdsmlr",
    "chatango.com": "chatango",
    "livejournal.com": "livejournal",
    "insanejournal.com": "insanejournal",
    "duolingo.com": "duolingo",
    "genius.com": "genius",
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

LOW_SIGNAL_PLATFORMS = {
    "7cups", "artbreeder", "fansly", "tinder", "linktree", "smule", "periscope",
    "streamelements", "streamlabs", "blogspot", "bdsmlr", "chatango", "livejournal",
    "insanejournal"
}

# Source reliability tiers — how trustworthy a platform is as an OSINT source.
# Independent of HIGH/LOW_SIGNAL_PLATFORMS (which measure identity-match signal strength).
# tier: high = strong authentication / established identity verification
#        medium = legitimate platform, lower authentication bar
#        low = anonymous, unverified, or not identity-focused
SOURCE_RELIABILITY: Dict[str, Dict] = {
    # High-trust: strong authentication, real-identity platforms
    "github":        {"tier": "high",   "label": "Technical repository",    "delta":  0.08},
    "linkedin":      {"tier": "high",   "label": "Professional platform",   "delta":  0.08},
    "twitter":       {"tier": "high",   "label": "Mainstream social",       "delta":  0.06},
    "instagram":     {"tier": "high",   "label": "Mainstream social",       "delta":  0.06},
    "reddit":        {"tier": "high",   "label": "Mainstream social",       "delta":  0.06},
    "twitch":        {"tier": "high",   "label": "Live-streaming platform", "delta":  0.06},
    "youtube":       {"tier": "high",   "label": "Video platform",          "delta":  0.06},
    "patreon":       {"tier": "high",   "label": "Creator platform",        "delta":  0.05},
    # Medium-trust: legitimate, lower authentication bar
    "steam":         {"tier": "medium", "label": "Gaming platform",         "delta":  0.03},
    "chess":         {"tier": "medium", "label": "Chess platform",          "delta":  0.03},
    "lastfm":        {"tier": "medium", "label": "Music tracker",           "delta":  0.03},
    "deviantart":    {"tier": "medium", "label": "Creative platform",       "delta":  0.03},
    "stackoverflow": {"tier": "medium", "label": "Technical Q&A",           "delta":  0.03},
    "wattpad":       {"tier": "medium", "label": "Publishing platform",     "delta":  0.02},
    "mixcloud":      {"tier": "medium", "label": "Music platform",          "delta":  0.02},
    "letterboxd":    {"tier": "medium", "label": "Film review platform",    "delta":  0.02},
    "duolingo":      {"tier": "medium", "label": "Language platform",       "delta":  0.02},
    "genius":        {"tier": "medium", "label": "Lyrics platform",         "delta":  0.02},
    # Low-trust: anonymous, unverified, or not identity-focused
    "pastebin":      {"tier": "low",    "label": "Paste site",              "delta": -0.05},
    "archive":       {"tier": "low",    "label": "Web archive",             "delta": -0.05},
    "wikimedia":     {"tier": "low",    "label": "Wiki metadata",           "delta": -0.05},
    "fansly":        {"tier": "low",    "label": "Adult content platform",  "delta": -0.08},
    "tinder":        {"tier": "low",    "label": "Dating platform",         "delta": -0.08},
    "bdsmlr":        {"tier": "low",    "label": "Adult content platform",  "delta": -0.08},
    "periscope":     {"tier": "low",    "label": "Defunct live platform",   "delta": -0.06},
    "chatango":      {"tier": "low",    "label": "Anonymous chat",          "delta": -0.05},
    "livejournal":   {"tier": "low",    "label": "Legacy blog platform",    "delta": -0.04},
    "insanejournal": {"tier": "low",    "label": "Legacy blog platform",    "delta": -0.04},
    "blogspot":      {"tier": "low",    "label": "Generic blog host",       "delta": -0.04},
    "kik":           {"tier": "low",    "label": "Anonymous messaging",     "delta": -0.06},
    "imageshack":    {"tier": "low",    "label": "Image host",              "delta": -0.04},
    "chyoa":         {"tier": "low",    "label": "Adult fiction site",      "delta": -0.06},
}


def _host(url: str) -> str:
    h = urlparse(url).netloc.lower()
    if h.startswith("www."):
        h = h[4:]
    return h

def _path_parts(url: str) -> List[str]:
    return [p for p in urlparse(url).path.strip("/").split("/") if p]

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

    if platform == "duolingo":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "profile" else None

    if platform == "genius":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "artists" else None

    if platform == "nightbot":
        return parts[1] if len(parts) >= 2 and parts[0].lower() == "t" else None
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

    if platform == "zepeto":
        # example: /share/user/profile/<name>
        if len(parts) >= 4 and parts[0].lower() == "share" and parts[1].lower() == "user" and parts[2].lower() == "profile":
            return parts[3]
        return None

    return parts[0]

def is_profile_like(platform: str, url: str) -> bool:
    """
    Conservative 'does this URL look like an actual profile page?'
    We keep generic blockers, but add platform-specific allow rules.
    """
    if platform in NON_PROFILE_PLATFORMS:
        return False

    parts = _path_parts(url)
    if not parts:
        return False

    parts_l = [p.lower() for p in parts]

    # ---- Platform-specific ALLOW rules (override generic blockers) ----
    if platform == "zepeto":
        # /share/user/profile/<name>
        return len(parts_l) >= 4 and parts_l[0:3] == ["share", "user", "profile"]

    if platform == "duolingo":
        # /profile/<name>
        return len(parts_l) >= 2 and parts_l[0] == "profile"

    if platform == "genius":
        # /artists/<name>
        return len(parts_l) >= 2 and parts_l[0] == "artists"

    if platform == "nightbot":
        # /t/<channel>/commands (not a profile, more like a channel page)
        # We'll treat it as NOT profile-like to keep noise down.
        return False

    # ---- Platform-specific DENY rules ----
    if platform == "stackoverflow" and parts_l[:2] == ["users", "filter"]:
        return False

    if platform == "truckersmp" and parts_l[:2] == ["user", "search"]:
        return False

    if platform == "discord":
        # invite links are not user profiles
        return False

    # ---- Generic DENY rules ----
    bad_prefixes = {
        "search", "search.php", "wayback", "web", "api", "wiki",
        "commands", "filter", "invite"
    }
    if parts_l[0] in bad_prefixes:
        return False

    # If it passes all blockers, assume it's profile-like
    return True

def score_account(target: str, acc: Dict) -> Tuple[float, List[Dict]]:
    """
    Returns (score, features) where features is a list of structured scoring components.
    Each feature: {"feature": str, "delta": float, "label": str}

    This makes confidence scores fully auditable — every point contribution is traceable
    to a named, described feature. Supports the explainability requirement.
    """
    features: List[Dict] = []

    target_n = normalized_handle(target)
    plat = acc.get("platform") or "unknown"
    url = acc.get("url") or ""
    handle = acc.get("handle") or ""
    handle_n = normalized_handle(handle) if handle else ""

    signals = acc.get("signals") or []
    modules = {s.get("module") for s in signals if s.get("module")}
    module_count = len(modules)

    score = 0.20
    features.append({"feature": "base_score", "delta": 0.20, "label": "Base score"})

    mod_boost = round(min(0.15 * module_count, 0.45), 2)
    score += mod_boost
    n = module_count
    features.append({
        "feature": "module_corroboration",
        "delta": mod_boost,
        "label": f"Corroborated by {n} SpiderFoot module{'s' if n != 1 else ''}",
    })

    if is_profile_like(plat, url):
        score += 0.10
        features.append({"feature": "profile_url", "delta": 0.10, "label": "Profile-like URL structure"})
    else:
        score -= 0.15
        features.append({"feature": "non_profile_url", "delta": -0.15, "label": "Non-profile URL (search/redirect/archive)"})

    if handle_n and handle_n == target_n:
        score += 0.30
        features.append({"feature": "exact_handle_match", "delta": 0.30, "label": f"Exact handle match: '{handle}'"})
        if plat in HIGH_SIGNAL_PLATFORMS:
            score += 0.10
            features.append({"feature": "high_signal_platform", "delta": 0.10, "label": f"High-signal platform: {plat}"})

    if plat in LOW_SIGNAL_PLATFORMS:
        score -= 0.10
        features.append({"feature": "low_signal_platform", "delta": -0.10, "label": f"Low-signal platform: {plat}"})

    if target_n and target_n in normalized_handle(url):
        score += 0.05
        features.append({"feature": "target_in_url", "delta": 0.05, "label": "Target identifier present in URL"})

    # Source reliability weighting — independent axis from signal strength.
    # Measures how trustworthy the platform is as an OSINT source.
    rel = SOURCE_RELIABILITY.get(plat)
    if rel:
        delta = rel["delta"]
        score += delta
        tier_label = {"high": "High", "medium": "Medium", "low": "Low"}.get(rel["tier"], "Unknown")
        features.append({
            "feature": "source_reliability",
            "delta": round(delta, 2),
            "label": f"Source reliability: {rel['label']} ({tier_label} trust)",
        })

    score = max(0.0, min(1.0, score))
    return score, features

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

        # If we don't know the platform, DO NOT cluster by handle.
        # Otherwise lots of unrelated domains collapse into one cluster.
        if plat == "unknown":
            key = (plat, _host(url))
        else:
            key = (plat, normalized_handle(handle) if handle else _host(url))

        c = clusters.get(key)
        if not c:
            c = {"platform": plat, "handle": handle or None, "key": key[1], "accounts": []}

        c["accounts"].append(acc2)
        clusters[key] = c

    out: List[Dict] = []
    for c in clusters.values():
        plat = c["platform"]
        scored = [score_account(target, a) for a in c["accounts"]]
        best_score, best_features = max(scored, key=lambda t: t[0]) if scored else (0.0, [])
        c["confidence"] = best_score
        c["score_features"] = best_features
        c["source_reliability"] = SOURCE_RELIABILITY.get(plat, {}).get("tier", "unknown")

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
