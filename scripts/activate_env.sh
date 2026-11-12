#!/usr/bin/env bash
# Source this file: it must change the caller's shell.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "Use: source ${BASH_SOURCE[0]}" >&2
    exit 1
fi

_hmc_opt_activate() {
    local project_root
    project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)" || return 1
    if [[ ! -f "$project_root/.venv/bin/activate" ]]; then
        echo "Environment missing. Run: bash $project_root/scripts/setup_env.sh" >&2
        return 1
    fi

    if [[ -d /sw/eb ]]; then
        source "$project_root/scripts/grace_modules.sh" || return 1
    fi
    # venv's activation script also deactivates a previously active venv.
    source "$project_root/.venv/bin/activate" || return 1

    # Set before importing numerical libraries, as required by the pilot runbook.
    export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
    export BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1
    export MPLBACKEND=Agg
    export MPLCONFIGDIR="$project_root/tmp/matplotlib"
    export PIP_CACHE_DIR="$project_root/tmp/pip-cache"
    mkdir -p "$MPLCONFIGDIR" "$PIP_CACHE_DIR" || return 1
    cd -- "$project_root" || return 1

    printf 'Environment ready:\n  Project: %s\n  Python:  %s\n' \
        "$project_root" "$(command -v python)"
}

if _hmc_opt_activate; then
    unset -f _hmc_opt_activate
else
    unset -f _hmc_opt_activate
    return 1
fi
