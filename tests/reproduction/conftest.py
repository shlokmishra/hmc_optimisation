"""Keep source-only checkouts usable without downloading upstream during tests."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def require_pinned_reproduction_inputs():
    if not (ROOT / "external/RHGD/code_of_experiments.ipynb").is_file():
        pytest.skip("Pinned RHGD checkout absent; follow docs/REPRODUCTION.md")
