#!/usr/bin/env bash
# Shared module choices for setup, interactive use, and future Slurm jobs.
# Python/3.13.5 requires GCCcore/14.3.0 (verified 2026-09-09).
if ! command -v module >/dev/null 2>&1; then
    for hmc_module_init in /etc/profile.d/modules.sh /usr/share/Modules/init/bash; do
        if [[ -r "$hmc_module_init" ]]; then
            source "$hmc_module_init"
            break
        fi
    done
    unset hmc_module_init
fi

if ! command -v module >/dev/null 2>&1; then
    echo "Grace's module command is unavailable; initialize the cluster shell first." >&2
    return 1
fi

# Keep other compatible modules loaded, including tools used by the caller.
module load GCCcore/14.3.0 Python/3.13.5
