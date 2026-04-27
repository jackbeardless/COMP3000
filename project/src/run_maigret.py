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

    # -J simple: write ndjson report to folderoutput as report_{username}_simple.json
    cmd = (
        f'python3.11 -m maigret "{target}" '
        f'--folderoutput "{out_folder}" '
        f'-J simple '
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

    # Maigret writes report_{username}_simple.json (ndjson: one JSON object per line)
    # Each line: { "SiteName": { "url_user": "...", "status": { "status": "Claimed", "url": "..." } } }
    json_files = sorted(out_folder.glob("*_simple.json"))
    report = json_files[0] if json_files else None

    if report and report.exists():
        for line in report.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                for site_name, site_data in obj.items():
                    if not isinstance(site_data, dict):
                        continue
                    status = site_data.get("status") or {}
                    if isinstance(status, dict):
                        st = str(status.get("status", "")).lower()
                        url = status.get("url") or site_data.get("url_user") or ""
                    else:
                        st = str(status).lower()
                        url = site_data.get("url_user") or ""
                    if "claimed" not in st:
                        continue
                    if url.startswith("http"):
                        events.append({
                            "type": "URL",
                            "data": f"<SFURL>{url}</SFURL>",
                            "module": "maigret",
                            "source": f"maigret:{site_name}",
                            "generated": ts,
                        })
            except Exception:
                continue

    print(f"Maigret: {len(events)} accounts found for '{target}'")
    return events
