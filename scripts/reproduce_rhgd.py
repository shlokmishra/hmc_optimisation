#!/usr/bin/env python3
"""Inspect the paper-panel plan or replay one explicitly selected panel."""

# ruff: noqa: E402
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rhgd_reproduction.replay import load_sources, run_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["plan", "run"])
    parser.add_argument("--case")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--smoke", action="store_true", help="12 iterations; not a paper result")
    args = parser.parse_args()
    manifest, _ = load_sources()
    if args.command == "plan":
        print(json.dumps(manifest, indent=2))
        return
    if args.case not in manifest["cases"] or args.output is None:
        parser.error("run requires --case from the plan and a new --output directory")
    result = run_case(args.case, args.output, smoke_iterations=12 if args.smoke else None)
    print(f"{result['status']}: {args.output} ({result['mode']})")


if __name__ == "__main__":
    main()
