"""
metadata_extractor.py

Fetches structured profile metadata from public platform APIs for each cluster.
Uses only unauthenticated public endpoints — no scraping, no credentials required.

Supported platforms: GitHub (REST API), Reddit (JSON API)
"""
import time
import requests

HEADERS = {"User-Agent": "Vantage-OSINT-Research/1.0 (Academic dissertation, non-commercial)"}
TIMEOUT = 8


def _fetch_github(handle: str) -> dict:
    try:
        r = requests.get(
            f"https://api.github.com/users/{handle}",
            headers=HEADERS, timeout=TIMEOUT
        )
        if r.status_code != 200:
            return {}
        d = r.json()
        return {
            "display_name": d.get("name"),
            "bio": d.get("bio"),
            "location": d.get("location"),
            "company": d.get("company"),
            "external_links": [d["blog"]] if d.get("blog") else [],
            "followers": d.get("followers"),
        }
    except Exception:
        return {}


def _fetch_reddit(handle: str) -> dict:
    try:
        r = requests.get(
            f"https://www.reddit.com/user/{handle}/about.json",
            headers=HEADERS, timeout=TIMEOUT
        )
        if r.status_code != 200:
            return {}
        d = r.json().get("data", {})
        sub = d.get("subreddit") or {}
        return {
            "display_name": sub.get("title") or d.get("name"),
            "bio": sub.get("public_description"),
            "location": None,
            "external_links": [],
        }
    except Exception:
        return {}


_FETCHERS = {
    "github": _fetch_github,
    "reddit": _fetch_reddit,
}


def enrich_clusters(clusters: list, delay: float = 0.4) -> list:
    """
    Add a 'metadata' dict to each cluster where a public API is available.
    Only non-null fields are included. Clusters with no supported platform
    get an empty metadata dict.
    """
    for c in clusters:
        plat = (c.get("platform") or "").lower()
        handle = c.get("handle") or ""
        fetcher = _FETCHERS.get(plat)
        if fetcher and handle:
            raw = fetcher(handle)
            # Strip null values to keep the output clean
            c["metadata"] = {k: v for k, v in raw.items() if v is not None}
            time.sleep(delay)
        else:
            c["metadata"] = {}
    return clusters
