#!/usr/bin/env python3
"""
pipeline.py — single entry point for the full OSINT analysis pipeline.

Usage:
    # Full run including SpiderFoot scan:
    python pipeline.py --target Yogscast

    # Skip SpiderFoot (use existing results file):
    python pipeline.py --no-spiderfoot

    # Skip the Gemini LLM step:
    python pipeline.py --target Yogscast --skip-llm

    # Use heuristics instead of Gemini (no API key needed):
    python pipeline.py --target Yogscast --dry-run

Steps:
    0. run_spiderfoot   — collect raw OSINT events (skipped with --no-spiderfoot)
    1. normalize_run    — parse events into structured accounts
    2. cluster_run      — group accounts by platform/handle and score them
    3. reduce_for_llm   — produce compact LLM-ready cluster summaries
    4. llm_judge_gemini — send to Gemini for final verdict (requires GEMINI_API_KEY)

Environment variables (all optional):
    GEMINI_API_KEY      Required for the LLM step (unless --dry-run or --skip-llm)
    OSINT_THRESHOLD     Confidence threshold for shown results (default 0.75)
    OSINT_MODEL         Gemini model to use (default gemini-2.5-flash)
    OSINT_BATCH_SIZE    Clusters per Gemini request (default 20)
    OSINT_DRY_RUN       Set to 1 to skip real API calls
    OSINT_INCLUDE_LOW   Set to 1 to include low-confidence results in output
    OSINT_SKIP_NOISE    Set to 0 to send all clusters to LLM (default 1)
    OSINT_RETRY_SLEEP   Seconds to wait on rate-limit (default 20)
"""
import argparse
import os
import sys
import time
from pathlib import Path

# Ensure src/ is importable
SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))


def _step(name: str):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")


def run_spiderfoot(target: str):
    import run_spiderfoot as sf
    result = sf.run_spiderfoot_username_scan(target)
    print(f"\nEvents collected: {result['event_count']}")
    print(f"Output: {result['output_file']}")


def run_normalize():
    import normalize_run
    normalize_run.main()


def run_cluster():
    import cluster_run
    return cluster_run.main()


def run_reduce():
    import reduce_for_llm
    reduce_for_llm.main()


def run_llm(dry_run: bool):
    if dry_run:
        os.environ["OSINT_DRY_RUN"] = "1"
    import llm_judge_gemini
    return llm_judge_gemini.main()


def main():
    parser = argparse.ArgumentParser(
        description="Run the full OSINT analysis pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "target",
        nargs="?",
        help="Target username to scan (required unless --no-spiderfoot).",
    )
    parser.add_argument(
        "--no-spiderfoot",
        action="store_true",
        help="Skip SpiderFoot scan and use the most recent existing results file.",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Stop after the reduce step (no Gemini API call).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the LLM step using heuristics only (no API key needed).",
    )
    args = parser.parse_args()

    if not args.no_spiderfoot and not args.target:
        parser.error("target is required unless --no-spiderfoot is set.")

    start = time.time()
    total_steps = 3 if args.skip_llm else 4
    step_offset = 0 if args.no_spiderfoot else 1

    if not args.no_spiderfoot:
        _step(f"Step 1 / {total_steps + 1} — SpiderFoot scan")
        run_spiderfoot(args.target)

    _step(f"Step {1 + step_offset} / {total_steps + step_offset} — Normalise")
    run_normalize()

    _step(f"Step {2 + step_offset} / {total_steps + step_offset} — Cluster")
    run_cluster()

    _step(f"Step {3 + step_offset} / {total_steps + step_offset} — Reduce for LLM")
    run_reduce()

    if args.skip_llm:
        print("\n[--skip-llm] Stopping before LLM step.")
    else:
        _step(f"Step {4 + step_offset} / {total_steps + step_offset} — LLM judgement (Gemini)")
        if not args.dry_run and not os.getenv("GEMINI_API_KEY"):
            print("\nERROR: GEMINI_API_KEY is not set.")
            print("       Export it, or re-run with --dry-run to use heuristics only.")
            sys.exit(1)
        run_llm(dry_run=args.dry_run)

    elapsed = time.time() - start
    print(f"\nPipeline complete in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
