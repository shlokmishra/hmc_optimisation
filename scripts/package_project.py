#!/usr/bin/env python3
"""Package only group-facing sources, independent of Git state and local raw data."""

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = (
    "README.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    ".gitignore",
    "pyproject.toml",
    "requirements.in",
    "requirements.txt",
    "Hamiltonian Descent Algorithms for Optimization.pdf",
    "docs",
    "configs",
    "src",
    "scripts",
    "tests",
    "study/B/src",
    "study/B/configs",
)


def package(output):
    output = Path(output).resolve()
    # Keep generated archives outside shared inputs, even on subsequent packages.
    for name in SHARED:
        source = ROOT / name
        if output == source or output.is_relative_to(source):
            raise ValueError("Write the bundle outside shared inputs, e.g. tmp/project.tar.gz")
    files = []
    for name in SHARED:
        source = ROOT / name
        candidates = [source] if source.is_file() else source.rglob("*")
        for path in candidates:
            if "__pycache__" in path.parts or path.suffix in (".pyc", ".pyo"):
                continue
            if path.is_symlink():
                raise ValueError(f"Refusing symlink in shared inputs: {path}")
            if path.is_file():
                files.append(path)
    manifest = []
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream, tarfile.open(fileobj=stream, mode="w:gz") as archive:
        for path in sorted(set(files)):
            data = path.read_bytes()
            name = str(path.relative_to(ROOT))
            manifest.append(
                {"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
            )
            archive.add(path, arcname=name, recursive=False)
        data = (json.dumps(manifest, indent=2) + "\n").encode()
        entry = tarfile.TarInfo("SHARE_MANIFEST.json")
        entry.size = len(data)
        archive.addfile(entry, io.BytesIO(data))
    # Verify that the delivered bytes, not just the original inputs, match.
    with tarfile.open(output) as archive:
        for item in manifest:
            data = archive.extractfile(item["path"]).read()
            if hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise RuntimeError(f"Bundle verification failed: {item['path']}")
    print(f"Verified {len(manifest)} files: {output} ({output.stat().st_size:,} bytes)")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    package(args.output)


if __name__ == "__main__":
    main()
