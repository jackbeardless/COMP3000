import json
import subprocess
import time
from pathlib import Path

BASE_DIR = Path.home() / "osint-dissertation"
SPIDERFOOT_DIR = BASE_DIR / "spiderfoot"

PROJECT_DIR = BASE_DIR / "project"
RESULTS_DIR = PROJECT_DIR / "results"
LOGS_DIR = PROJECT_DIR / "logs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

EVENT_TYPES_USERNAME = "USERNAME,ACCOUNT_EXTERNAL,USERNAME_MEMBER,URL,HUMAN_NAME"

MAX_THREADS = 5  # lower = fewer "too many open files" issues on macOS


def _run_spiderfoot(target: str, event_types: str, output_format: str = "json") -> dict:
    """Core SpiderFoot runner — target type agnostic."""
    ts = int(time.time())
    safe_target = "".join(c for c in target if c.isalnum() or c in "._-@")[:60]

    out_json   = RESULTS_DIR / f"spiderfoot_{safe_target}_{ts}.{output_format}"
    out_stderr = LOGS_DIR    / f"spiderfoot_{safe_target}_{ts}.stderr.log"

    cmd = (
        'mkdir -p "$HOME/.spiderfoot/db" "$HOME/.spiderfoot/cache" && '
        'chmod -R u+rwX "$HOME/.spiderfoot" && '
        'ulimit -n 8192 && '
        f'cd "{SPIDERFOOT_DIR}" && '
        'source "venv/bin/activate" && '
        f'python sf.py -max-threads {MAX_THREADS} -s "{target}" -t "{event_types}" -o {output_format}'
    )

    print("Running (bash -lc):")
    print(cmd)
    print("-" * 60)

    res = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True)
    out_stderr.write_text(res.stderr or "", encoding="utf-8")

    if res.returncode != 0:
        raise RuntimeError(f"SpiderFoot failed (exit {res.returncode}). See log: {out_stderr}")

    out_json.write_text(res.stdout, encoding="utf-8")
    data = json.loads(res.stdout) if output_format == "json" else res.stdout

    return {
        "target":       target,
        "event_types":  event_types,
        "max_threads":  MAX_THREADS,
        "output_file":  str(out_json),
        "stderr_log":   str(out_stderr),
        "event_count":  len(data) if isinstance(data, list) else None,
        "events":       data,
    }


def run_spiderfoot_username_scan(target: str, output_format: str = "json") -> dict:
    return _run_spiderfoot(target, EVENT_TYPES_USERNAME, output_format)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run a SpiderFoot OSINT scan for a target username.")
    parser.add_argument("target", help="Username to scan (e.g. Yogscast)")
    args = parser.parse_args()

    result = run_spiderfoot_username_scan(args.target)

    print(f"\nSaved results to: {result['output_file']}")
    print(f"Saved stderr log to: {result['stderr_log']}")
    print(f"Events returned: {result['event_count']}")