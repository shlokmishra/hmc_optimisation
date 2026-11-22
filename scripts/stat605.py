#!/usr/bin/env python3
"""Run STAT 605 demonstrations and the matched spectral comparison."""

# ruff: noqa: E402
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    smoke_parser = commands.add_parser("smoke", help="Run the original onboarding example")
    smoke_parser.add_argument("--output", required=True, type=Path)
    configs = Path(__file__).resolve().parents[1] / "configs/stat605"
    for name, default, help_text in (
        ("spectral", "spectral_check.json", "Run the configured quadratic comparison"),
        ("spectral-design", "spectral_pilot.json", "Measure and plot the input geometry"),
    ):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--config", default=configs / default, type=Path)
        command.add_argument("--output", required=True, type=Path)
    report = commands.add_parser(
        "spectral-report", help="Regenerate figures and tables from traces"
    )
    report.add_argument("--run", required=True, type=Path)
    report.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "smoke":
        from stat605.smoke import smoke

        metadata = smoke(args.output)
        print(f"{metadata['status']}: {args.output} (software smoke only)")
    elif args.command == "spectral-report":
        from stat605.spectral_reporting import write_report

        write_report(args.run, args.output)
        print(f"Rebuilt figures and tables in {args.output}")
        return
    elif args.command == "spectral-design":
        from stat605.spectral_suite import spectral_design

        spectral_design(args.output, args.config)
        print(f"Measured initial modal energies in {args.output}")
        return
    else:
        from stat605.spectral_suite import spectral_suite

        metadata = spectral_suite(args.output, args.config)
        print(f"{metadata['status']}: {args.output} ({len(metadata['runs'])} paths)")
    if metadata["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
