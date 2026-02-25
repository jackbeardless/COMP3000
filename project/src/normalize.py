# src/normalize.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

SFURL_RE = re.compile(r"<SFURL>\s*(.*?)\s*</SFURL>", re.IGNORECASE | re.DOTALL)

# Path segment "handles" that are usually NOT the person's handle
JUNK_PATH_SEGMENTS = {
    "user",
    "users",
    "member",
    "members",
    "profile",
    "people",
    "invite",
    "search",
    "search.php",
    "api",
    "by",
    "u",
    "id",
    "t",
    "share",
    "web",
    "wayback",
    "artists",
    "accounts",
}

# Domain -> platform mapping (extend whenever you want)
DOMAIN_PLATFORM = {
    "github.com": "github",
    "www.github.com": "github",
    "instagram.com": "instagram",
    "www.instagram.com": "instagram",
    "patreon.com": "patreon",
    "www.patreon.com": "patreon",
    "reddit.com": "reddit",
    "www.reddit.com": "reddit",
    "twitch.tv": "twitch",
    "www.twitch.tv": "twitch",
    "steamcommunity.com": "steam",
    "www.steamcommunity.com": "steam",
    "vimeo.com": "vimeo",
    "www.vimeo.com": "vimeo",
    "pinterest.com": "pinterest",
    "www.pinterest.com": "pinterest",
    "pastebin.com": "pastebin",
    "www.pastebin.com": "pastebin",
    "picsart.com": "picsart",
    "www.picsart.com": "picsart",
    "imageshack.com": "imageshack",
    "www.imageshack.com": "imageshack",
    "last.fm": "lastfm",
    "www.last.fm": "lastfm",
    "mixcloud.com": "mixcloud",
    "www.mixcloud.com": "mixcloud",
    "myspace.com": "myspace",
    "www.myspace.com": "myspace",
    "chess.com": "chess",
    "www.chess.com": "chess",
    "kongregate.com": "kongregate",
    "www.kongregate.com": "kongregate",
    "gog.com": "gog",
    "www.gog.com": "gog",
    "stackoverflow.com": "stackoverflow",
    "www.stackoverflow.com": "stackoverflow",
    "archive.org": "archive",
    "web.archive.org": "archive",
    "meta.wikimedia.org": "wikimedia",
    "truckersmp.com": "truckersmp",
    "www.truckersmp.com": "truckersmp",
    "discord.com": "discord",
    "www.discord.com": "discord",
    "zepeto.me": "zepeto",
    "web.zepeto.me": "zepeto",
}




def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


def _extract_sfurls(text: str) -> List[str]:
    return [m.strip() for m in SFURL_RE.findall(text or "") if m.strip()]


def _clean_seg(s: str) -> str:
    return s.strip().strip("/")

def _platform_from_url(url: str) -> str:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return "unknown"
    host = host.split(":")[0]
    return DOMAIN_PLATFORM.get(host, "unknown")

def parse_platform_and_username(url: str) -> tuple[str | None, str | None]:
    try:
        p = urlparse(url)
    except Exception:
        return None, None

    host = (p.netloc or "").lower()
    host = host[4:] if host.startswith("www.") else host
    path = _clean_seg(p.path)
    segs = [s for s in path.split("/") if s]

    platform = DOMAIN_PLATFORM.get(host)

    # Username rules by platform/domain
    if host == "github.com" and len(segs) >= 1:
        return platform, segs[0]  # /<user> or /<user>/<repo>
    if host == "twitch.tv" and len(segs) >= 1:
        return platform, segs[0]
    if host == "instagram.com" and len(segs) >= 1:
        return platform, segs[0]
    if host == "patreon.com" and len(segs) >= 1:
        return platform, segs[0]
    if host == "reddit.com" and len(segs) >= 2 and segs[0] in ("user", "u"):
        return platform, segs[1]
    if host == "steamcommunity.com" and len(segs) >= 2 and segs[0] in ("id", "profiles"):
        return platform, segs[1]
    if host == "vimeo.com" and len(segs) >= 1:
        return platform, segs[0]
    if host == "pinterest.com" and len(segs) >= 1:
        return platform, segs[0]
    if host == "www.last.fm" and len(segs) >= 2 and segs[0] == "user":
        return platform, segs[1]
    if host == "mixcloud.com" and len(segs) >= 1:
        return platform, segs[0]
    if host == "pastebin.com" and len(segs) >= 2 and segs[0] == "u":
        return platform, segs[1]
    if host == "picsart.com" and len(segs) >= 2 and segs[0] == "u":
        return platform, segs[1]
    if host == "scratch.mit.edu" and len(segs) >= 2 and segs[0] == "users":
        return platform, segs[1]
    if host == "kongregate.com" and len(segs) >= 2 and segs[0] == "accounts":
        return platform, segs[1]
    if host == "kik.me" and len(segs) >= 1:
        return platform, segs[0]
    if host == "disqus.com" and len(segs) >= 2 and segs[0] == "by":
        return platform, segs[1]
    if host == "gog.com" and len(segs) >= 2 and segs[0] == "u":
        return platform, segs[1]
    if host == "imageshack.com" and len(segs) >= 2 and segs[0] == "user":
        return platform, segs[1]
    if host == "web.zepeto.me":
        # your example: /share/user/profile/<name>
        if len(segs) >= 4 and segs[0:3] == ["share", "user", "profile"]:
            return platform, segs[3]
        return platform, None

    # For archive/wayback links etc: platform known, but username usually not meaningful
    if platform == "archive":
        return platform, None

    # Fallback: platform if known, username unknown
    return platform, None


def _guess_handle_from_url(url: str, target: str) -> Optional[str]:
    """
    Try to guess a user handle from common URL patterns.
    If it looks like a directory (users/profile/etc) return None.
    If it contains @handle in path, return handle.
    If last segment equals target, return target.
    """
    try:
        p = urlparse(url)
        path = (p.path or "").strip("/")
    except Exception:
        return None

    if not path:
        return None

    # If url has "@name" in the first segment, treat that as handle
    segs = [s for s in path.split("/") if s]
    if not segs:
        return None

    # handle like /@Yogscast
    if segs[0].startswith("@") and len(segs[0]) > 1:
        return segs[0][1:]

    # some sites use /user/<handle> or /users/<handle> etc
    if len(segs) >= 2 and segs[0].lower() in JUNK_PATH_SEGMENTS:
        # second segment might be the handle
        candidate = segs[1]
        if candidate and candidate.lower() not in JUNK_PATH_SEGMENTS:
            # if it's literally the target, accept; otherwise return candidate anyway
            return candidate

    # otherwise use last segment if it doesn't look like a junk directory
    last = segs[-1]
    if last.lower() in JUNK_PATH_SEGMENTS:
        return None

    # if last segment equals target (case-insensitive), that’s a strong signal
    if target and last.lower() == target.lower():
        return target

    # don't “invent” handles from generic pages
    # allow otherwise, but only if it isn't obviously a file
    if "." in last and len(last.split(".")) > 1:
        return None

    return last


def normalize_events(events: List[Dict[str, Any]], target: str) -> Dict[str, Any]:
    evidence: List[Dict[str, Any]] = []
    usernames_set = set()
    urls_set = set()
    accounts: List[Dict[str, Any]] = []

    for ev in events:
        ev_type = _safe_str(ev.get("type"))
        data = _safe_str(ev.get("data"))
        module = _safe_str(ev.get("module"))
        source = _safe_str(ev.get("source"))
        ts = ev.get("generated") or ev.get("ts") or 0

        # evidence record
        evidence.append(
            {
                "type": ev_type,
                "value": data,
                "module": module,
                "source": source,
                "ts": ts,
            }
        )

        # usernames (only if event is "Username" OR looks like a username)
        if ev_type.lower() == "username":
            if data:
                usernames_set.add(data)

        # extract urls from SFURL markup
        urls = _extract_sfurls(data)
        for u in urls:
            urls_set.add(u)

            platform0 = _platform_from_url(u)          # returns "unknown" sometimes
            handle0 = _guess_handle_from_url(u, target)

            p2, u2 = parse_platform_and_username(u)

            # Prefer the rule-based parser when available
            platform = p2 or (None if platform0 == "unknown" else platform0)
            handle = u2 or handle0



            # Create an account record
            accounts.append(
                {
                    "platform": platform if platform != "unknown" else None,
                    "url": u,
                    "username": handle if handle and handle.lower() != target.lower() else (target if target else handle),
                    "kind": "url",
                    "signals": [
                        {
                            "from_event": ev_type,
                            "module": module,
                            "source": source,
                        }
                    ],
                }
            )

    usernames = sorted(usernames_set)
    urls = sorted(urls_set)

    out = {
        "target": target,
        "counts": {
            "raw_events": len(events),
            "evidence": len(evidence),
            "unique_usernames": len(usernames),
            "unique_urls": len(urls),
            "accounts": len(accounts),
        },
        "usernames": usernames,
        "urls": urls,
        "accounts": accounts,
        "evidence": evidence,
    }
    return out