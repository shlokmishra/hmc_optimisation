"""Check the BLAS runtime used by the single-threaded course entry points."""

import ctypes
import platform

import numpy as np
import scipy
from threadpoolctl import threadpool_info


def single_thread_pools():
    """Return verified runtimes for the calling thread after project activation."""
    pools = threadpool_info()
    if platform.system() == "Darwin" and any(
        package.__config__.CONFIG["Build Dependencies"]["blas"]["name"].lower() == "accelerate"
        for package in (np, scipy)
    ):
        # threadpoolctl does not enumerate Accelerate. On macOS 15+ the
        # system BLAS exposes a per-calling-thread set/get pair instead.
        blas = ctypes.CDLL("/System/Library/Frameworks/Accelerate.framework/Accelerate")
        if not hasattr(blas, "BLASSetThreading"):
            raise RuntimeError("Verifying Accelerate threading requires macOS 15 or newer.")
        blas.BLASSetThreading.argtypes = [ctypes.c_uint]
        blas.BLASGetThreading.restype = ctypes.c_uint
        if blas.BLASSetThreading(1) != 0 or blas.BLASGetThreading() != 1:
            raise RuntimeError("Accelerate did not enter single-threaded BLAS mode.")
        pools.append({"internal_api": "accelerate", "num_threads": 1})
    if not pools or any(pool["num_threads"] != 1 for pool in pools):
        raise RuntimeError(f"Expected one thread per numerical runtime: {pools}")
    return pools
