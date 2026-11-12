"""Frozen input preparation and independent numerical fidelity gates."""

import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np

from .core import B_PATH, CONFIG, CONFIG_PATH, FROZEN_B, ROOT, run

BASE = ROOT / CONFIG["paths"]["results"]
DATA = BASE / "data"
DOCS = ROOT / CONFIG["paths"]["docs"]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, obj):
    path = Path(path)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def prior_paths():
    roots = [
        ROOT / "study/A",
        ROOT / "study/B",
        ROOT / "study/C",
        ROOT / "results/reproduction",
        ROOT / "results/studies/synthesis-20260923",
        ROOT / "docs/reproduction",
        ROOT / "docs/design",
        ROOT / "external/RHGD",
        ROOT / "src/rhgd_reproduction",
    ]
    paths = [ROOT / "docs/studies/SYNTHESIS.md", ROOT / "configs/reproduction/rhgd.json"]
    for base in roots:
        paths += [
            p
            for p in base.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and ".git" not in p.parts
        ]
    return sorted(set(paths))


def prepare():
    if (BASE / "freeze.json").exists():
        raise FileExistsError("Already frozen; do not overwrite inputs")
    DATA.mkdir(parents=True, exist_ok=False)
    start = perf_counter()
    protected = {str(p.relative_to(ROOT)): sha(p) for p in prior_paths()}
    write_json(BASE / "prior_artifacts.json", protected)
    with np.load(ROOT / CONFIG["paper_source"]) as z:
        A, x0 = z["A"], z["x0"]
    lam, Q = np.linalg.eigh((A + A.T) / 2)
    pivot = np.argmax(np.abs(Q), axis=0)
    Q *= np.where(Q[pivot, np.arange(len(lam))] < 0, -1.0, 1.0)
    intended = np.geomspace(CONFIG["alpha"], CONFIG["L"], CONFIG["dimension"])
    A_log = Q @ np.diag(intended) @ Q.T
    arrays = {"A_paper": A, "A_log": A_log, "x0": x0, "Q": Q, "lambdas_log_intended": intended}
    descriptions = {}
    for name, matrix in (("paper", A), ("log", A_log)):
        eigenvalues, U = np.linalg.eigh((matrix + matrix.T) / 2)
        pivot = np.argmax(np.abs(U), axis=0)
        U *= np.where(U[pivot, np.arange(len(eigenvalues))] < 0, -1.0, 1.0)
        slow = float(U[:, 0] @ x0)
        arrays.update(
            {
                f"spectrum_{name}": eigenvalues,
                f"basis_{name}": U,
                f"raw_eigenvalues_{name}": np.linalg.eigvals(matrix),
                f"slow_x0_{name}": slow * U[:, 0],
            }
        )
        descriptions[name] = {
            "alpha_computed": float(eigenvalues[0]),
            "L_computed": float(eigenvalues[-1]),
            "kappa_computed": float(eigenvalues[-1] / eigenvalues[0]),
            "slow_projection": slow,
            "initial_slow_loss": float(0.5 * eigenvalues[0] * slow**2),
            "symmetry_residual_max": float(np.max(np.abs(matrix - matrix.T))),
            "orthogonality_residual_max": float(np.max(np.abs(U.T @ U - np.eye(len(x0))))),
            "spectral_reconstruction_max": float(
                np.max(np.abs(U @ np.diag(eigenvalues) @ U.T - matrix))
            ),
        }
        assert np.isclose(eigenvalues[0], CONFIG["alpha"], rtol=1e-7, atol=1e-12)
        assert np.isclose(eigenvalues[-1], CONFIG["L"], rtol=1e-12, atol=1e-10)
    hashes = {}
    for name, a in arrays.items():
        path = DATA / f"{name}.npy"
        np.save(path, a)
        hashes[name] = {
            "path": str(path.relative_to(ROOT)),
            "file_sha256": sha(path),
            "raw_c_order_sha256": hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest(),
            "shape": list(a.shape),
            "dtype": str(a.dtype),
        }
    assert (
        abs(descriptions["paper"]["slow_projection"] - descriptions["log"]["slow_projection"])
        < 1e-6
    )
    freeze = {
        "protocol_sha256": sha(DOCS / "PROTOCOL.md"),
        "config_sha256": sha(CONFIG_PATH),
        "B_source_sha256": sha(B_PATH),
        "B_config_sha256": sha(ROOT / CONFIG["B_configuration"]),
        "paper_source_sha256": sha(ROOT / CONFIG["paper_source"]),
        "construction": "Exact float64 expression pinned in protocol/config, no optimizer executed",
        "arrays": hashes,
        "problems": descriptions,
        "preparation_seconds": perf_counter() - start,
        "protected_files": len(protected),
    }
    write_json(BASE / "freeze.json", freeze)
    return freeze


def check_freeze(check_prior=False):
    freeze = json.loads((BASE / "freeze.json").read_text())
    for key, path in (
        ("protocol_sha256", DOCS / "PROTOCOL.md"),
        ("config_sha256", CONFIG_PATH),
        ("B_source_sha256", B_PATH),
        ("B_config_sha256", ROOT / CONFIG["B_configuration"]),
        ("paper_source_sha256", ROOT / CONFIG["paper_source"]),
    ):
        assert sha(path) == freeze[key], str(path)
    for desc in freeze["arrays"].values():
        assert sha(ROOT / desc["path"]) == desc["file_sha256"]
    if check_prior:
        for name, value in json.loads((BASE / "prior_artifacts.json").read_text()).items():
            assert sha(ROOT / name) == value, name
    return freeze


def load_problem(spectrum, slow_only=False):
    return (
        np.load(DATA / f"A_{spectrum}.npy"),
        np.load(DATA / f"slow_x0_{spectrum}.npy" if slow_only else DATA / "x0.npy"),
        np.load(DATA / f"basis_{spectrum}.npy"),
        np.load(DATA / f"spectrum_{spectrum}.npy"),
    )


def validate():
    freeze = check_freeze()
    A = np.load(DATA / "A_paper.npy")
    Q = np.load(DATA / "Q.npy")
    with np.load(ROOT / CONFIG["paper_source"]) as z:
        np.testing.assert_array_equal(A, z["A"])
        np.testing.assert_array_equal(np.load(DATA / "x0.npy"), z["x0"])
    np.testing.assert_array_equal(
        np.load(DATA / "A_log.npy"),
        Q @ np.diag(np.geomspace(CONFIG["alpha"], CONFIG["L"], 100)) @ Q.T,
    )
    rows = []
    n = CONFIG["validation_prefix_updates"]
    for spectrum in CONFIG["spectra"]:
        A, x0, U, lam = load_problem(spectrum)
        for method, seeds in CONFIG["seeds"].items():
            for seed in seeds:
                outputs = []
                for cached in (False, True):
                    out, meta = run(
                        A,
                        x0,
                        method,
                        budget=2 * n,
                        seed=seed,
                        cached=cached,
                        detailed=True,
                        basis=U,
                        eigenvalues=lam,
                        keep_states=True,
                        max_updates=n,
                    )
                    outputs.append((out, meta))
                raw, cache = outputs[0][0], outputs[1][0]
                for key in ("f", "x", "aux_final", "x_final"):
                    np.testing.assert_array_equal(raw[key], cache[key])
                expected_primary = n * CONFIG["primary_gradients_per_update"][method]
                assert outputs[1][1]["numerical_gradients"] == expected_primary
                assert (
                    outputs[1][1]["literal_gradient_requests"]
                    == n * CONFIG["literal_gradients_per_update"][method]
                )
                repeat, _ = run(A, x0, method, 2 * n, seed=seed, max_updates=n)
                np.testing.assert_array_equal(cache["f"], repeat["f"])
                author = True
                p = FROZEN_B.Problem(A, x0)
                if method == "B":
                    direct, _ = FROZEN_B.run(p, "exact", "B", 2 * n, diagnostic=True, max_states=n)
                    np.testing.assert_array_equal(cache["f"], direct["f"])
                    np.testing.assert_array_equal(cache["x"][1:], direct["states"])
                    for key in ("power", "event", "cap", "age", "reset"):
                        np.testing.assert_array_equal(cache[key], direct[key])
                    if spectrum == "paper":
                        with np.load(ROOT / "study/B/results/main-19819175/exact-B-0.npz") as prior:
                            np.testing.assert_array_equal(cache["f"], prior["f"][: n + 1])
                            np.testing.assert_array_equal(cache["x"][1:], prior["states"][:n])
                elif method != "AR_AGD":
                    ns = FROZEN_B.original_functions("exact", p)
                    source_points = []

                    def observed_loss(x):
                        source_points.append(x.copy())
                        return 0.5 * x @ A @ x

                    ns["quad_loss"] = observed_loss
                    rng = np.random.default_rng(seed)
                    if method == "AGD":
                        end, loss = ns["run_nag"](x0, n, CONFIG["alpha"], CONFIG["eta"])
                    elif method == "CAGD":
                        end, loss = ns["stochastic_accelerated_descent"](
                            x0, CONFIG["eta"], CONFIG["alpha"], n, rng=rng
                        )
                    else:
                        end, loss = ns["run_rhgd"](
                            x0, n, np.sqrt(CONFIG["eta"]), CONFIG["alpha"], rng=rng
                        )
                    np.testing.assert_array_equal(cache["f"][:-1], loss)
                    np.testing.assert_array_equal(cache["x"][:-1], source_points)
                    np.testing.assert_array_equal(cache["x_final"], end)
                else:
                    author = None
                rows.append(
                    {
                        "spectrum": spectrum,
                        "method": method,
                        "seed": seed,
                        "updates": n,
                        "cached_uncached_exact": True,
                        "repeat_exact": True,
                        "source_or_prior_B_exact": author,
                        "primary_gradients": expected_primary,
                        "literal_calls": outputs[0][1]["literal_gradient_requests"],
                    }
                )
    result = {
        "passed": True,
        "rows": rows,
        "problem_validation": freeze["problems"],
        "B_source_sha256": freeze["B_source_sha256"],
        "notes": "AR analytic tests are recorded separately in pytest receipt.",
    }
    write_json(BASE / "validation.json", result)
    return result
