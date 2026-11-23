#!/usr/bin/env python3
"""Course entry point: software smoke demonstrations and restarted-AGD runs."""

# ruff: noqa: E402
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["smoke", "fixed-time-smoke", "agd"])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--config", type=Path, help="required for agd, e.g. configs/stat605/*.json")
    parser.add_argument(
        "--smoke", action="store_true", help="agd only: <=2000G total, dimension<=100"
    )
    args = parser.parse_args()
    if args.smoke and args.command != "agd":
        parser.error("--smoke is only used with agd; the other commands are already smoke checks")
    if args.command == "agd":
        if args.config is None:
            parser.error("agd requires --config")
        if not args.smoke and not os.environ.get("SLURM_JOB_ID"):
            parser.error("Configured AGD runs require Slurm; use --smoke with a small config")
        from stat605.agd_experiments import run_config

        metadata = run_config(args.config, args.output, smoke=args.smoke)
        note = metadata["execution"]
    else:
        from stat605.smoke import fixed_time_smoke, smoke

        command = smoke if args.command == "smoke" else fixed_time_smoke
        metadata = command(args.output)
        note = "software smoke only"
    print(f"{metadata['status']}: {args.output} ({note})")
    if metadata["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
