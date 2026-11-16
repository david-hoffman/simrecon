"""PH118 fixed DIRECT-stage observer; do not import/execute before resource grant.

One fresh process, one public target call. No numerical child or disk array.
Scientific generators/protocol are frozen before candidate measurements.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import reconstruction_memory_benchmark as observer

CASE_IDS = (
    "acquisition-64",
    "acquisition-128",
    "acquisition-off",
    "acquisition-drift",
    "known-64",
    "known-128",
    "preparation-context-64",
)
OPTICS = {"wavelength_nm": 500, "numerical_aperture": 1.0, "immersion_index": 1.0}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(root: Path, *args: str) -> str:
    """Read identity/status only, never source, diff or history contents."""
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True, text=True
    ).stdout.rstrip("\n")


def _provenance(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.worktree).resolve()
    if Path.cwd().resolve() != root:
        raise ValueError("selected worktree must equal the process working directory")
    if Path(sys.executable).absolute() != Path(args.expected_python).absolute():
        raise ValueError("interpreter path differs from the frozen selected interpreter")
    if Path(sys.prefix).resolve() != (root / ".venv").resolve():
        raise ValueError("interpreter prefix is not the selected worktree .venv")
    if sys.version_info[:3] != (3, 13, 12):
        raise ValueError("the frozen Python3.13.12 profile is required")
    revision, tree = _git(root, "rev-parse", "HEAD"), _git(root, "rev-parse", "HEAD^{tree}")
    status = _git(root, "status", "--porcelain", "--untracked-files=no")
    if (revision, tree, bool(status)) != (args.revision, args.tree, args.dirty == "true"):
        raise ValueError("selected Git revision/tree/dirty identity does not match")
    allowed_dirty = {
        "tests/preparation_harmonic_memory_benchmark.py",
        "tests/test_preparation_harmonic_lifetimes.py",
        "docs/packets/issue-118-direct-resource-protocol.md",
    }
    for line in status.splitlines():
        path = line[3:]
        if path not in allowed_dirty and not path.startswith("docs/reports/issue-118/"):
            raise ValueError(
                "tracked scientific/tool/lock inputs must be committed before measurement"
            )
    adapter = Path(__file__).resolve()
    shared = Path(observer.__file__).resolve()
    if adapter.parent != root / "tests" or shared.parent != root / "tests":
        raise ValueError("observer modules must come from the selected worktree tests")
    hashes = {
        "adapter": _sha(adapter),
        "shared_observer": _sha(shared),
        "lock": _sha(root / "uv.lock"),
    }
    if tuple(hashes.values()) != (
        args.adapter_sha256,
        args.shared_observer_sha256,
        args.lock_sha256,
    ):
        raise ValueError("frozen adapter/shared observer/lock identities differ")
    module_root = Path(args.expected_module_root).resolve()
    if not module_root.is_relative_to(root):
        raise ValueError("expected public package root must be inside the selected worktree")
    specification = importlib.util.find_spec("simrecon")
    if (
        specification is None
        or specification.origin is None
        or not Path(specification.origin).resolve().is_relative_to(module_root)
    ):
        raise ValueError("public package resolution would import another worktree")
    package = importlib.import_module("simrecon")
    origin = getattr(package, "__file__", None)
    if not isinstance(origin, str) or not Path(origin).resolve().is_relative_to(module_root):
        raise ValueError("public package import is outside the selected module root")
    distribution = importlib.metadata.distribution("simrecon")
    direct = distribution.read_text("direct_url.json")
    direct_value = None if direct is None else json.loads(direct)
    if direct_value is not None:
        url = urlparse(direct_value["url"])
        if url.scheme != "file" or Path(unquote(url.path)).resolve() != root:
            raise ValueError("installed editable/distribution provenance selects another worktree")
    return dict(
        worktree=str(root),
        interpreter=sys.executable,
        prefix=sys.prefix,
        package_origin=str(Path(origin).resolve()),
        package_resolution_origin=specification.origin,
        import_search_path=tuple(sys.path),
        distribution_version=distribution.version,
        public_version=getattr(package, "__version__", None),
        direct_url=direct_value,
        revision=revision,
        tree=tree,
        dirty=bool(status),
        tracked_status=status,
        product_tracked_clean=True,
        hashes=hashes,
    )


def _multifrequency(shape: tuple[int, int, int, int, int]) -> Any:
    """Exactly the RM84 analytic detector formula, explicit final float32 cast."""
    import numpy as np

    nt, nd, nz, ny, nx = shape
    z, y, x = np.indices((nz, ny, nx), dtype=np.float64)
    obj = 30 + 3 * np.cos(2 * np.pi * (x / nx + y / ny))
    obj += 2 * np.sin(2 * np.pi * (2 * x / nx - y / ny))
    obj += np.cos(2 * np.pi * (z / nz + 3 * x / nx))
    obj += 0.75 * np.cos(2 * np.pi * (3 * y / ny + x / nx))
    raw = np.empty((nt, nd, 5, nz, ny, nx), dtype=np.float32)
    for t in range(nt):
        for d in range(nd):
            angle = d * np.pi / nd
            spatial = 2 * np.pi * (x * np.cos(angle) + y * np.sin(angle)) / 8
            for p in range(5):
                phase = 2 * np.pi * p / 5
                illumination = 1 + (0.31 + t / 64) * np.cos(spatial + phase)
                illumination += (0.13 + t / 128) * np.cos(2 * spatial + 2 * phase + 0.3)
                raw[t, d, p] = obj * illumination + d / 4 + t / 8
    return raw


def _pattern(nd: int, ny: int, nx: int) -> Any:
    """Generate the approved CE07 T2/P5/Z2 patterned_case observations."""
    import numpy as np

    t, d, p, z, y, x = np.indices((2, nd, 5, 2, ny, nx))
    return (
        80
        + 7 * t
        + 3 * d
        + 2 * p
        + z
        + ((x * x + 3 * y + p * x + 2 * d * y) % 17)
        + (x == (2 + p) % nx) * 9
        + (y == (3 + d) % ny) * 5
    ).astype(np.float64)


def _case(case_id: str, api: Any) -> tuple[str, tuple[Any, ...], dict[str, Any], dict[str, Any]]:
    """All callers returned here stay live through target and final observation."""
    import numpy as np

    settings: dict[str, Any] = dict(
        acquisition_mode="3d",
        dxy_um=1.0,
        dz_um=1.0,
        norders=3,
        background=0.0,
        lateral_zoom=2,
        axial_zoom=1,
        edge_pixels=0,
        equalize=False,
    )
    callers: dict[str, Any] = {}
    if case_id in ("acquisition-off", "acquisition-drift"):
        nd, ny, nx = (2, 10, 10) if case_id == "acquisition-off" else (3, 10, 12)
        raw = _pattern(nd, ny, nx)
        settings.update(background=3.0, lateral_zoom=1.0)
        if case_id == "acquisition-off":
            off = np.stack((raw / 2, raw / 4), axis=4)
            off[0, 0, 0, 0, 0, -1, -1] = -1
            settings.update(
                dxy_um=0.1,
                edge_pixels=-1,
                equalize=True,
                equalize_z=True,
                equalize_time=True,
                combine_off_orders=np.array([1, 1, 1], dtype=np.int32),
                off_exposures=off,
                exposure_background=np.arange(40).reshape(2, 2, 5, 2) / 8,
            )
        else:
            for t in range(2):
                for d in range(3):
                    raw[t, d] = np.roll(raw[t, 0], (d, -d), axis=(-2, -1))
            background = np.full((10, 12), 3.0)
            background[-1, -1], background[-1, -2] = 5.0, 3.5
            raw[0, 0, 0, 0, -1, -1] = -1
            off = np.stack(
                (
                    np.roll(raw / 4, (1, 2), axis=(-2, -1)),
                    np.roll(raw / 2, (-2, -1), axis=(-2, -1)),
                ),
                axis=4,
            )
            settings.update(
                background=background,
                flatfield_slope=np.full((10, 12), 0.75),
                off_exposures=off,
                drift_between=True,
                drift_filter_fraction=0.2,
            )
        settings.update(OPTICS)
    else:
        size = 128 if case_id.endswith("128") else 64
        raw = _multifrequency(
            (2, 2, 8, size, size) if case_id.startswith("known") else (1, 3, 8, size, size)
        )
    callers["raw"] = raw
    callers["preparation_settings"] = settings
    if case_id.startswith("known"):
        bands = api.prepare_acquisition_bands(raw, **settings)
        m, r, k = np.indices((3, 64, 16))
        samples = 1 + m / 16 + r / 128 + 1j * (m + r + k) / 256
        transfer = api.declare_otf(samples, layout="radial", dkr_cyc_um=0.125, dkz_cyc_um=0.125)
        carriers = np.array([[0.125, 0.03125], [-0.0625, 0.125]], dtype=np.float64)
        modulation = np.array(
            [[0.5 + 0.125j, -0.25 + 0.0625j], [0.375 - 0.125j, 0.25 + 0.1875j]],
            dtype=np.complex128,
        )
        known_settings = dict(
            **OPTICS,
            carriers_cyc_um=carriers,
            modulation=modulation,
            wiener=0.5,
            suppress_singularities=False,
            output_taper="none",
        )
        callers.update(
            bands=bands, transfer=transfer, declared_samples=samples, known_settings=known_settings
        )
        return "reconstruct_known", (bands, transfer), known_settings, callers
    if case_id == "preparation-context-64":
        del settings["acquisition_mode"]
        return "prepare_bands", (raw,), settings, callers
    return "prepare_acquisition_bands", (raw,), settings, callers


def _witness(case_id: str, entry: str, result: Any, callers: dict[str, Any]) -> dict[str, Any]:
    """Frozen public qualification predicates, never candidate-driven selection."""
    import numpy as np

    shape = callers["raw"].shape
    if entry == "reconstruct_known":
        assert result.image.shape == (2, 8, 2 * shape[-2], 2 * shape[-1])
        assert result.image.dtype == np.float64 and np.isfinite(result.image).all()
        assert result.filtered_quadratures.shape == callers["bands"].quadratures.shape
        assert np.any(abs(callers["bands"].quadratures[:, :, 1:3]) > 0)
        assert np.any(abs(callers["bands"].quadratures[:, :, 3:5]) > 0)
        assert (
            result.carriers_cyc_um.tobytes()
            == callers["known_settings"]["carriers_cyc_um"].tobytes()
        )
        assert result.modulation.tobytes() == callers["known_settings"]["modulation"].tobytes()
        assert np.array_equal(result.axial_cutoffs_bins, [3, 3, 3])
        return dict(
            record="KnownReconstruction",
            image_shape=result.image.shape,
            quadratures_shape=result.filtered_quadratures.shape,
            cutoffs=(3, 3, 3),
        )
    assert result.quadratures.shape == (*shape[:2], 5, *shape[3:5], shape[-1] // 2 + 1)
    assert result.quadratures.dtype == np.complex128 and np.isfinite(result.quadratures).all()
    assert np.all(result.noise_variance_factors == 1)
    witness: dict[str, Any] = dict(
        record=type(result).__name__, quadratures_shape=result.quadratures.shape
    )
    if entry == "prepare_acquisition_bands":
        kinds = [event.kind for event in result.trace]
        assert kinds.count("phase-design") == shape[0] * shape[1] * shape[3]
        witness["event_counts"] = {kind: kinds.count(kind) for kind in sorted(set(kinds))}
        if case_id == "acquisition-off":
            assert kinds.count("off-combination") == 24
            assert result.off_quadratures is not None
            assert len(result.sentinel_frames) == 1
        elif case_id == "acquisition-drift":
            assert kinds.count("between-build") == 2 and kinds.count("drift-correlation") == 4
            assert result.background_after[-1, -1] == 3.5 and result.slope_after[-1, -1] == 1
            assert len(result.sentinel_frames) == 1
    return witness


def execute(args: argparse.Namespace) -> dict[str, Any]:
    import os

    for key in observer.THREAD_CONTROLS:
        if os.environ.get(key) != "1":
            raise ValueError(f"{key}=1 is required before process startup")
    provenance = _provenance(args)
    import numpy as np
    import scipy
    import scipy.fft

    api = importlib.import_module("simrecon")
    context = observer.host_context()
    entry, positional, settings, callers = _case(args.case, api)
    input_fingerprint = observer.public_value_sha256(callers)
    caller_payload = observer.retained_payload(callers)
    baseline = resource.getrusage(resource.RUSAGE_SELF)
    started = time.monotonic()
    result = getattr(api, entry)(*positional, **settings)
    elapsed = time.monotonic() - started
    target_return = resource.getrusage(resource.RUSAGE_SELF)
    witness = _witness(args.case, entry, result, callers)
    output_fingerprint = observer.public_value_sha256(result)
    caller_after = observer.public_value_sha256(callers)
    if caller_after != input_fingerprint:
        raise ValueError("target changed retained public caller values")
    result_payload = observer.retained_payload(result)
    union_payload = observer.retained_payload({"callers": callers, "result": result})
    final = resource.getrusage(resource.RUSAGE_SELF)
    system = context["system"]
    return dict(
        protocol="PH118-direct-v1",
        role=args.role,
        case=args.case,
        entry=entry,
        repetition=args.repetition,
        provenance=provenance,
        context=context,
        witness=witness,
        versions=dict(numpy=np.__version__, scipy=scipy.__version__),
        backend=np.__config__.CONFIG,
        scipy_fft_default_workers=scipy.fft.get_workers(),
        public_fingerprints=dict(
            protocol="RM84-public-values-v1",
            inputs=input_fingerprint,
            inputs_after=caller_after,
            result=output_fingerprint,
        ),
        caller_payload=caller_payload,
        result_payload=result_payload,
        union_payload=union_payload,
        elapsed_target_seconds=elapsed,
        ru_maxrss_native=dict(
            pre_target=baseline.ru_maxrss,
            target_return=target_return.ru_maxrss,
            final_whole_process=final.ru_maxrss,
        ),
        ru_maxrss_native_units="KiB" if system == "Linux" else "bytes",
        high_water_bytes=dict(
            pre_target=observer.rss_bytes(baseline.ru_maxrss, system),
            target_return=observer.rss_bytes(target_return.ru_maxrss, system),
            final_whole_process=observer.rss_bytes(final.ru_maxrss, system),
        ),
        page_faults=dict(
            before_minor=baseline.ru_minflt,
            before_major=baseline.ru_majflt,
            after_minor=final.ru_minflt,
            after_major=final.ru_majflt,
        ),
        swaps_native=dict(before=baseline.ru_nswap, after=final.ru_nswap),
        block_io_native=dict(inblock=final.ru_inblock, outblock=final.ru_oublock),
        disk_array_bytes=0,
        limits=(
            "Whole-process peak includes imports, fixture/setup preparation, hashes and observers; "
            "no subtraction attributes a stage peak. Payload is not RSS. Backend workspace, "
            "allocator sharing, foreign backing and swap attribution remain limited/unknown; "
            "redirected log/artifact disk use is recorded externally."
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_IDS, required=True)
    parser.add_argument("--role", choices=("parent", "candidate"), required=True)
    parser.add_argument("--repetition", choices=(1, 2, 3), type=int, required=True)
    for name in (
        "worktree",
        "expected-python",
        "expected-module-root",
        "revision",
        "tree",
        "dirty",
        "adapter-sha256",
        "shared-observer-sha256",
        "lock-sha256",
    ):
        parser.add_argument(f"--{name}", required=True)
    args = parser.parse_args()
    if args.dirty not in ("true", "false"):
        parser.error("--dirty must be true or false")
    try:
        result = execute(args)
    except BaseException as error:
        print(
            json.dumps(
                dict(
                    status="failure",
                    case=args.case,
                    role=args.role,
                    repetition=args.repetition,
                    type=type(error).__name__,
                    message=str(error),
                )
            )
        )
        return 2
    print(json.dumps(dict(status="pass", **result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
