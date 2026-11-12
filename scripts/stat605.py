#!/usr/bin/env python3
"""Course entry point for a small self-contained software demonstration."""

# ruff: noqa: E402
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from stat605.smoke import smoke


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["smoke"])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    metadata = smoke(args.output)
    print(f"{metadata['status']}: {args.output} (software smoke only)")
    if metadata["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
