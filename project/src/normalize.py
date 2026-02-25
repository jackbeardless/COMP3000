import re
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse

PLATFORM_HOST_HINTS = {
    "github.com": "github",
    "instagram.com": "instagram",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "tiktok.com": "tiktok",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "twitch.tv": "twitch",
    "reddit.com": "reddit",
    "facebook.com": "facebook",
    "linkedin.com": "linkedin",
    "patreon.com": "patreon",
    "steamcommunity.com": "steam",
    "pinterest.com": "pinterest",
    "vimeo.com": "vimeo",
}

SFURL_RE = re.compile(r"<SFURL>\s*(https?://[^<\s]+)\s*</SFURL>", re.IGNORECASE)

def _as_str(x) -> str:
    return "" if x is None else str(x)

def platform_from_url(url: str) -> Optional[str]:
    try:
        host = urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return None
    for h, name in PLATFORM_HOST_HINTS.items():
        if host == h or host.endswith("." + h):
            return name
    return None

def username_from_url(url: str) -> Optional[str]:
    try:
        path = urlparse(url).path.strip("/")
    except Exception:
        return None
    if not path:
        return None
    first = path.split("/")[0]
    if first.lower() in {"watch", "channel", "c", "user", "status", "hashtag", "search"}:
        return None
    if re.fullmatch(r"[A-Za-z0-9._-]{2,64}", first):
        return first
    return None

def extract_urls(value: str) -> List[str]:
    """Extract URLs from raw SpiderFoot strings (supports <SFURL> tags and plain URLs)."""
    urls = []

    # <SFURL>...</SFURL>
    for m in SFURL_RE.finditer(value):
        urls.append(m.group(1))

    # plain http(s) URLs anywhere in the string
    for m in re.finditer(r"(https?://[^\s<]+)", value):
        u = m.group(1).rstrip(").,]")
        urls.append(u)

    # de-dup while preserving order
    seen = set()
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def normalize_events(target: str, events: List[Dict]) -> Dict:
    evidence: List[Dict] = []
    usernames = set()
    urls = set()

    # accounts keyed by URL (best) or by (platform,value)
    accounts_by_url: Dict[str, Dict] = {}
    accounts_other: Dict[Tuple[str, str], Dict] = {}

    for e in events:
        etype = _as_str(e.get("type")).strip()
        value = _as_str(e.get("data")).strip()
        module = _as_str(e.get("module")).strip()
        source = _as_str(e.get("source")).strip()
        ts = e.get("generated")

        if not etype or not value:
            continue

        evidence.append({
            "type": etype,
            "value": value,
            "module": module,
            "source": source,
            "ts": ts
        })

        if etype.lower() == "username":
            usernames.add(value)

        found_urls = extract_urls(value)
        for u in found_urls:
            urls.add(u)
            plat = platform_from_url(u)
            uname = username_from_url(u)

            acc = accounts_by_url.get(u)
            if not acc:
                acc = {
                    "platform": plat,
                    "url": u,
                    "username": uname,
                    "kind": "url",
                    "signals": []
                }
            acc["signals"].append({"from_event": etype, "module": module, "source": source})
            accounts_by_url[u] = acc

        # Also capture non-URL “account” evidence as fallback
        if etype.lower() in {"account on external site", "account_external", "username_member"} and not found_urls:
            key = (platform_from_url(value) or "unknown", value)
            acc2 = accounts_other.get(key)
            if not acc2:
                acc2 = {"platform": key[0], "value": value, "kind": etype.lower(), "signals": []}
            acc2["signals"].append({"from_event": etype, "module": module, "source": source})
            accounts_other[key] = acc2

    accounts = list(accounts_by_url.values()) + list(accounts_other.values())

    return {
        "target": target,
        "counts": {
            "raw_events": len(events),
            "evidence": len(evidence),
            "unique_usernames": len(usernames),
            "unique_urls": len(urls),
            "accounts": len(accounts),
        },
        "usernames": sorted(usernames),
        "urls": sorted(urls),
        "accounts": accounts,
        "evidence": evidence,
    }