#!/usr/bin/env bash
# Create or update the isolated environment; safe to rerun from any directory.
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd -- "$project_root"
if [[ -d /sw/eb ]]; then
    source scripts/grace_modules.sh
    # Avoid accidentally choosing another project's active venv from PATH.
    python_bin="${EBROOTPYTHON:?The Python module must set EBROOTPYTHON}/bin/python"
else
    python_bin="$(command -v python3.13 || command -v python3)"
fi
"$python_bin" -c 'import sys; assert sys.version_info[:2] == (3, 13), sys.version'

if [[ -e .venv ]]; then
    if [[ ! -x .venv/bin/python ]]; then
        echo "Existing .venv is incomplete; inspect it before rebuilding." >&2
        exit 1
    fi
    expected_base="$("$python_bin" -c 'import sys; print(sys.base_prefix)')"
    actual_base="$(.venv/bin/python -c 'import sys; print(sys.base_prefix)')"
    if [[ "$actual_base" != "$expected_base" ]]; then
        echo "Existing .venv uses $actual_base; expected $expected_base. Inspect it first." >&2
        exit 1
    fi
else
    "$python_bin" -m venv --prompt hmc-opt .venv
fi

mkdir -p tmp/pip-cache logs
export PIP_CACHE_DIR="$project_root/tmp/pip-cache"
if [[ -f requirements.txt ]]; then
    .venv/bin/python -m pip install -r requirements.txt
else
    .venv/bin/python -m pip install -r requirements.in
    {
        printf '# Resolved on Grace with Python 3.13.5; direct dependencies: requirements.in\n'
        .venv/bin/python -m pip freeze
    } > requirements.txt
fi
.venv/bin/python -m pip check
source scripts/activate_env.sh
python scripts/check_env.py
printf '\nActivate in your shell with: source %s/scripts/activate_env.sh\n' "$project_root"
