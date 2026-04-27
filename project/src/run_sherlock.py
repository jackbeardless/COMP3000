import json
import re
import subprocess
import time
from pathlib import Path

BASE_DIR = Path.home() / "osint-dissertation"
PROJECT_DIR = BASE_DIR / "project"
RESULTS_DIR = PROJECT_DIR / "results"
LOGS_DIR = PROJECT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_sherlock_scan(target: str) -> list:
    """Run Sherlock and return events in SpiderFoot-compatible format."""
    ts = int(time.time())
    safe = "".join(c for c in target if c.isalnum() or c in "._-")[:50]
    out_json = RESULTS_DIR / f"sherlock_{safe}_{ts}.json"
    stderr_log = LOGS_DIR / f"sherlock_{safe}_{ts}.stderr.log"

    cmd = f'python3.11 -m sherlock_project "{target}" --json "{out_json}" --no-color'
    try:
        res = subprocess.run(
            ["bash", "-lc", cmd], capture_output=True, text=True, timeout=120
        )
        stderr_log.write_text(res.stderr or "", encoding="utf-8")
    except Exception as e:
        stderr_log.write_text(str(e), encoding="utf-8")
        return []

    # Parse JSON output file
    events = []
    if out_json.exists():
        try:
            data = json.loads(out_json.read_text(encoding="utf-8"))
            # Sherlock JSON: flat dict of {SiteName: {url: ..., status: ...}}
            # (username key may also be present)
            for site, info in data.items():
                if site == "username" or not isinstance(info, dict):
                    continue
                if str(info.get("status", "")).lower() != "claimed":
                    continue
                url = info.get("url") or info.get("url_user") or ""
                if url.startswith("http"):
                    events.append({
                        "type": "URL",
                        "data": f"<SFURL>{url}</SFURL>",
                        "module": "sherlock",
                        "source": f"sherlock:{site}",
                        "generated": ts,
                    })
        except Exception:
            # Fallback: parse stdout [+] lines
            for line in (res.stdout or "").splitlines():
                line = _ANSI.sub("", line).strip()
                if not line.startswith("[+]") or ": http" not in line:
                    continue
                site, _, url = line[3:].strip().partition(": ")
                url = url.strip()
                if url.startswith("http"):
                    events.append({
                        "type": "URL",
                        "data": f"<SFURL>{url}</SFURL>",
                        "module": "sherlock",
                        "source": f"sherlock:{site.strip()}",
                        "generated": ts,
                    })

    print(f"Sherlock: {len(events)} accounts found for '{target}'")
    return events
