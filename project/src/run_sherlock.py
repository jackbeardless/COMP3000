import json
import re
import subprocess
import time
from pathlib import Path

BASE_DIR = Path.home() / "osint-dissertation"
PROJECT_DIR = BASE_DIR / "project"
LOGS_DIR = PROJECT_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def run_sherlock_scan(target: str) -> list:
    """Run Sherlock and return events in SpiderFoot-compatible format."""
    ts = int(time.time())
    safe = "".join(c for c in target if c.isalnum() or c in "._-")[:50]
    stderr_log = LOGS_DIR / f"sherlock_{safe}_{ts}.stderr.log"

    # --print-found: only output claimed accounts
    # --no-txt:      don't create a .txt file in cwd
    # --no-color:    clean text output
    cmd = f'python3.11 -m sherlock_project "{target}" --print-found --no-color --no-txt'
    try:
        res = subprocess.run(
            ["bash", "-lc", cmd], capture_output=True, text=True, timeout=120
        )
        stderr_log.write_text(res.stderr or "", encoding="utf-8")
    except Exception as e:
        stderr_log.write_text(str(e), encoding="utf-8")
        return []

    events = []
    for line in (res.stdout or "").splitlines():
        line = _ANSI.sub("", line).strip()
        # Sherlock found-account lines: "[+] SiteName: https://..."
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
