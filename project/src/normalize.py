import re
from typing import Optional, List, Dict
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
}

def _as_str(x) -> str:
    return "" if x is None else str(x)

def looks_like_urlish(s: str) -> bool:
    if not s or " " in s:
        return False
    return s.startswith(("http://", "https://", "www.")) or ("." in s and "/" in s)

def ensure_scheme(s: str) -> str:
    if s.startswith(("http://", "https://")):
        return s
    if s.startswith("www."):
        return "https://" + s
    return "https://" + s

def platform_from_url(url: str) -> Optional[str]:
    try:
        host = urlparse(url).netloc.lower().lstrip("www.")
    except Exception:
        return None
    for h, name in PLATFORM_HOST_HINTS.items():
        if host == h or host.endswith("." + h):
            return name
    return None

def guess_platform_from_text(text: str) -> Optional[str]:
    t = text.lower()
    for host, name in PLATFORM_HOST_HINTS.items():
        if host in t or name in t:
            return name
    return None

def normalize_events(target: str, events: List[Dict]) -> Dict:
    evidence = []
    usernames = set()
    urls = set()
    accounts = {}  # key=(platform_guess, value)

    for e in events:
        etype = _as_str(e.get("type")).strip()
        data_raw = _as_str(e.get("data")).strip()
        module = _as_str(e.get("module")).strip()
        source = _as_str(e.get("source")).strip()
        ts = e.get("generated")

        if not data_raw or not etype:
            continue

        evidence.append({
            "type": etype,
            "value": data_raw,
            "module": module,
            "source": source,
            "ts": ts
        })

        if etype.lower() == "username":
            usernames.add(data_raw)

        # URLs if present
        if looks_like_urlish(data_raw):
            url = ensure_scheme(data_raw)
            urls.add(url)
            plat = platform_from_url(url)
            if plat:
                key = (plat, url)
                accounts[key] = {
                    "platform": plat,
                    "value": url,
                    "kind": "url",
                    "signals": accounts.get(key, {}).get("signals", []) + [{
                        "from_event": etype, "module": module, "source": source
                    }]
                }
            continue

        # Non-URL account evidence
        # ACCOUNT_EXTERNAL often contains something like "site:username" or just a handle-like value
        if etype.upper() in {"ACCOUNT_EXTERNAL", "USERNAME_MEMBER"}:
            plat_guess = guess_platform_from_text(source) or guess_platform_from_text(module) or guess_platform_from_text(data_raw)
            val = data_raw
            key = (plat_guess or "unknown", val)
            accounts[key] = {
                "platform": plat_guess,
                "value": val,
                "kind": etype.lower(),
                "signals": accounts.get(key, {}).get("signals", []) + [{
                    "from_event": etype, "module": module, "source": source
                }]
            }

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
        "accounts": list(accounts.values()),
        "evidence": evidence,
    }
