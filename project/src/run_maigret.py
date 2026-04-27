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


def run_maigret_scan(target: str) -> list:
    """Run Maigret and return events in SpiderFoot-compatible format."""
    ts = int(time.time())
    safe = "".join(c for c in target if c.isalnum() or c in "._-")[:50]
    out_folder = RESULTS_DIR / f"maigret_{safe}_{ts}"
    out_folder.mkdir(parents=True, exist_ok=True)
    stderr_log = LOGS_DIR / f"maigret_{safe}_{ts}.stderr.log"

    # -J writes a JSON report to the folder; --timeout limits per-site wait
    cmd = (
        f'python3.11 -m maigret "{target}" '
        f'--folderoutput "{out_folder}" '
        f'--json "{out_folder}/report.json" '
        f'--no-color --timeout 15'
    )
    try:
        res = subprocess.run(
            ["bash", "-lc", cmd], capture_output=True, text=True, timeout=300
        )
        stderr_log.write_text(res.stderr or "", encoding="utf-8")
    except Exception as e:
        stderr_log.write_text(str(e), encoding="utf-8")
        return []

    events = []
    report = out_folder / "report.json"

    # Try JSON report first
    if report.exists():
        try:
            data = json.loads(report.read_text(encoding="utf-8"))
            # Maigret JSON: { "username": { "sites": { "SiteName": { "status": ..., "url": ... } } } }
            # OR flat: { "sites": { ... } }
            sites = {}
            if "sites" in data:
                sites = data["sites"]
            elif isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, dict) and "sites" in v:
                        sites = v["sites"]
                        break
            for site_name, info in sites.items():
                if not isinstance(info, dict):
                    continue
                status = info.get("status") or {}
                if isinstance(status, dict):
                    st = str(status.get("status", "")).lower()
                else:
                    st = str(status).lower()
                if "claimed" not in st and "found" not in st:
                    continue
                url = info.get("url") or ""
                if url.startswith("http"):
                    events.append({
                        "type": "URL",
                        "data": f"<SFURL>{url}</SFURL>",
                        "module": "maigret",
                        "source": f"maigret:{site_name}",
                        "generated": ts,
                    })
        except Exception:
            pass

    # Fallback: parse stdout [+] lines
    if not events:
        for line in (res.stdout or "").splitlines():
            line = _ANSI.sub("", line).strip()
            # Strip progress-bar artifacts (carriage returns, box chars)
            line = re.sub(r"[\r\x00-\x1f\u2500-\u259f]", "", line).strip()
            if not line.startswith("[+]") or ": http" not in line:
                continue
            site, _, url = line[3:].strip().partition(": ")
            url = url.strip()
            if url.startswith("http"):
                events.append({
                    "type": "URL",
                    "data": f"<SFURL>{url}</SFURL>",
                    "module": "maigret",
                    "source": f"maigret:{site.strip()}",
                    "generated": ts,
                })

    print(f"Maigret: {len(events)} accounts found for '{target}'")
    return events
