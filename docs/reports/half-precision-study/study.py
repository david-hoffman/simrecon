#!/usr/bin/env python3
"""HP114 finite scientific harness, outside product and test discovery.

SOURCE PREPARATION ONLY: no execution, including syntax/import checks, until the
coordinator grants the numerical window. See manifest.md for frozen formulas,
commands, branch qualification, lifecycle accounting and interpretation limits.
Each invocation executes exactly one row/strategy/repetition in a fresh process.
There is deliberately no subprocess runner, growth search or environment repair.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import os
import platform
import resource
import sys
import time
import traceback
import warnings
from fractions import Fraction
from pathlib import Path

BASE = "b344e41a8b52de76d7cbbf8450319893904c3b8f"
ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = Path("/workspace/work/campaign/evidence/114/study")
EXPECTED = {
    "src/simrecon/acquisition/preparation.py": (
        "2c5bb8eb536f8b1edd0c4d155da603bb66c838ce2298a899cdd6f23a3eedd0da"
    ),
    "src/simrecon/acquisition/modes.py": (
        "4958415d1864b2e1a25fef4601ff8f9f911e242ff19549d49c838a050f5e2db1"
    ),
    "src/simrecon/reconstruction/parameter_estimation.py": (
        "f9a924d277518cdb0717c7fe82961f3d36a480109bcbef9f8d19b42fdae7d7e8"
    ),
    "src/simrecon/reconstruction/known_parameters.py": (
        "34fbc93aa5ac9a1f4eb24b1f39ce576a1bb7770238c62cab72412de120722295"
    ),
    "src/simrecon/workflow/reconstruct.py": (
        "50a4ce199f0cceca6ba9147a1ee218441b1b5588c03beabecef95828802e28fa"
    ),
    "src/simrecon/workflow/summary.py": (
        "f0ccb2f0c566ba255eb02b0047c7000c3fe6530a0a7c797224e185d3f31ebb2e"
    ),
    "uv.lock": ("222666a37b442986ea7652b657ece340f2f0b4ba8ed90a939763c2e86b97d93b"),
    "docs/contracts/half-precision-feasibility-v1.md": (
        "bb5963ce268e81dabf8773f8bce5f1b37e8153e2d18886ddef1e5766bd384284"
    ),
    "docs/packets/half-precision-study/investigator.md": (
        "712f72dec72690ed87a2a8228884e8fcecbf4185665676a93e62ee66528d1afd"
    ),
}
SHAPES = {
    "W01": (1, 1, 3, 1, 16, 16),
    "W02": (1, 3, 5, 4, 16, 16),
    "W03": (1, 3, 5, 4, 16, 16),
    "W04": (2, 3, 5, 4, 16, 16),
    "W05": (1, 3, 5, 4, 32, 32),
    "W06": (1, 3, 5, 4, 16, 16),
}
STRATEGIES = (
    "QUALIFY",
    "WIDER",
    "H1",
    "H1_PROMOTED",
    "H2_CORRECTED",
    "H2_PREPARED",
    "H2_FILTERED",
    "H2_EMBEDDED",
    "KERNEL",
    "CPU",
)
THREAD_KEYS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
OPTICS = dict(wavelength_nm=520, numerical_aperture=1.2, immersion_index=1.33)
KEEP = []  # Explicit conservative caller/conversion/result retention for RSS.
ARRAYS = {}
TIMINGS = []
np = scipy = sim = None  # Numerical imports occur only after explicit authorization.


def digest(path):
    """Hash one file without loading its entire contents."""
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def text_file(path):
    """Read an optional operating-system text record."""
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def authorize(args):
    """Check the root receipt; provide audit evidence, not technical isolation."""
    receipt = json.loads(Path(args.grant).read_text())
    if receipt.get("authorization") != "HP114_NUMERICAL_WINDOW":
        raise RuntimeError("missing explicit root numerical-window authorization")
    if receipt.get("baseline") != BASE:
        raise RuntimeError("grant does not identify the approved public baseline")
    for key, path in (
        ("harness_sha256", __file__),
        ("manifest_sha256", Path(__file__).with_name("manifest.md")),
    ):
        if receipt.get(key) != digest(path):
            raise RuntimeError(f"grant {key} differs from frozen artifact")
    if receipt.get("environment") != "simrecon-campaign-ubuntu":
        raise RuntimeError("grant is not for pinned Ubuntu environment")
    if (args.row, args.strategy, args.repetition) not in [tuple(x) for x in receipt["runs"]]:
        raise RuntimeError("this exact finite run is not in the root grant")
    for name, expected in EXPECTED.items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f"material source identity changed: {name}")
    osrelease = text_file("/etc/os-release") or ""
    if "ID=ubuntu" not in osrelease and 'ID="ubuntu"' not in osrelease:
        raise RuntimeError("host is not Ubuntu; host Debian cannot qualify")
    if "24.04" not in osrelease:
        raise RuntimeError("wrong Ubuntu series; record exact point release separately")
    if Path(sys.prefix).resolve() != (ROOT / ".venv").resolve():
        raise RuntimeError("interpreter is not the root-provisioned per-worktree .venv")
    for key in THREAD_KEYS:
        if os.environ.get(key) != "1":
            raise RuntimeError(f"set {key}=1 before launching the fresh interpreter")
    if os.environ.get("SCIPY_ARRAY_API") not in (None, "0"):
        raise RuntimeError("unqualified SciPy array-API backend selection")
    if args.row in SHAPES:
        if args.strategy in ("KERNEL", "CPU"):
            raise RuntimeError("kernel strategy cannot select a workflow row")
        if args.strategy != "QUALIFY":
            qualified = json.loads(Path(args.qualification).read_text())
            if (
                qualified.get("row") != args.row
                or qualified.get("status") != "branch-qualified-oracle-review-required"
                or qualified["identities"]["harness"] != digest(__file__)
                or qualified["identities"]["manifest"]
                != digest(Path(__file__).with_name("manifest.md"))
            ):
                raise RuntimeError("missing applicable wider branch-qualification record")
            if receipt.get("qualification_sha256", {}).get(args.row) != digest(args.qualification):
                raise RuntimeError(
                    "root grant did not accept this qualification record for comparison"
                )
    elif args.strategy not in ("KERNEL", "CPU"):
        raise RuntimeError("K rows require KERNEL; CPU bounded transforms use K01 only")
    if args.strategy == "CPU" and args.row != "K01":
        raise RuntimeError("CPU feasibility is bounded to K01")
    return receipt


def timed(label, operation):
    """Record elapsed monotonic seconds even for a failed call."""
    start = time.monotonic_ns()
    try:
        return operation()
    finally:
        TIMINGS.append(dict(operation=label, seconds=(time.monotonic_ns() - start) / 1e9))


def remember(name, value):
    """Retain caller/conversion storage and name an exported array."""
    KEEP.append(value)
    ARRAYS[name] = value
    return value


def encode(value, path="record"):
    """Lossless numeric arrays are separate NPY files; no enormous JSON lists."""
    if isinstance(value, np.ndarray):
        key = f"{len(ARRAYS):05d}-{path.replace('/', '_')}"
        ARRAYS[key] = value
        return {"array": key, "shape": value.shape, "dtype": value.dtype.str}
    if dataclasses.is_dataclass(value):
        return {
            field.name: encode(getattr(value, field.name), path + "." + field.name)
            for field in dataclasses.fields(value)
        }
    if isinstance(value, dict):
        return {str(k): encode(v, path + "." + str(k)) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v, path + f".{i}") for i, v in enumerate(value)]
    if isinstance(value, np.generic):
        return encode(value.item(), path)
    if isinstance(value, complex):
        return {"real": encode(value.real), "imag": encode(value.imag)}
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    if isinstance(value, Path):
        return str(value)
    return value


def array_hash(a):
    """Hash contiguous logical sample bytes outside call-only timing."""
    # Hashing conversion is explicit and outside call-only time; contiguous copy
    # can coexist with the caller. NPY artifact SHA also includes shape/dtype.
    contiguous = np.ascontiguousarray(a)
    return hashlib.sha256(memoryview(contiguous).cast("B")).hexdigest()


def scalar_stats(a):
    """Observe signed real components and binary16 range boundaries."""
    a = np.asarray(a)
    finite = np.isfinite(a)
    selected = a[finite]
    return dict(
        dtype=a.dtype.str,
        shape=a.shape,
        strides=a.strides,
        aligned=bool(a.flags.aligned),
        own=bool(a.flags.owndata),
        writeable=bool(a.flags.writeable),
        payload_bytes=a.nbytes,
        sha256=array_hash(a),
        nonfinite=int((~finite).sum()),
        minimum=float(selected.min()) if selected.size else None,
        maximum=float(selected.max()) if selected.size else None,
        negative=int((a < 0).sum()),
        zeros=int((a == 0).sum()),
        negative_zeros=int(((a == 0) & np.signbit(a)).sum()),
        positive_zeros=int(((a == 0) & ~np.signbit(a)).sum()),
        binary16_subnormal_range=int(((np.abs(a) > 0) & (np.abs(a) < 2**-14)).sum()),
    )


def stats(a):
    """Observe real and imaginary component ranges separately."""
    return (
        {"real": scalar_stats(a.real), "imag": scalar_stats(a.imag)}
        if np.iscomplexobj(a)
        else scalar_stats(a)
    )


def error_metrics(reference, candidate):
    """Compare finite arrays with explicit zero-reference and sign rules."""
    a, b = np.asarray(reference), np.asarray(candidate)
    if a.shape != b.shape:
        return {"status": "shape-change", "reference": a.shape, "candidate": b.shape}
    finite = np.isfinite(a) & np.isfinite(b)
    if not finite.all():
        return {
            "status": "nonfinite",
            "finite_pairs": int(finite.sum()),
            "reference": stats(a),
            "candidate": stats(b),
        }
    delta = b - a
    energy = float(np.vdot(a.ravel(), a.ravel()).real)
    squared = float(np.vdot(delta.ravel(), delta.ravel()).real)
    result = dict(
        status="finite",
        max_absolute=float(np.max(np.abs(delta), initial=0)),
        rms=math.sqrt(squared / a.size) if a.size else 0.0,
        relative_l2=math.sqrt(squared / energy) if energy else (0.0 if squared == 0 else None),
        zero_reference_rule="0 for both zero; undefined otherwise",
        reference_l2=math.sqrt(energy),
        candidate=stats(b),
    )
    for component, x, y in (("real", a.real, b.real), ("imag", a.imag, b.imag)):
        result[component] = dict(
            nonzero_to_zero=int(((x != 0) & (y == 0)).sum()),
            sign_changes_nonzero=int(
                ((x != 0) & (y != 0) & (np.signbit(x) != np.signbit(y))).sum()
            ),
            reference=scalar_stats(x),
            candidate=scalar_stats(y),
        )
    return result


def pack(a, label):
    """Explicit little-endian IEEE half encoding; original/packed/promoted live."""
    a = np.asarray(a)
    if np.iscomplexobj(a):
        packed = np.empty((*a.shape, 2), dtype="<f2")
        packed[..., 0] = a.real
        packed[..., 1] = a.imag
        remember(label + ".packed", packed)
        promoted = np.empty(a.shape, np.complex128)
        promoted.real = packed[..., 0]
        promoted.imag = packed[..., 1]
    else:
        packed = remember(label + ".packed", a.astype("<f2"))
        promoted = packed.astype(np.float64)
    remember(label + ".promoted", promoted)
    return packed, promoted


def phases_for(row):
    """Return the frozen uniform or perturbed phase declaration."""
    p = SHAPES[row][2]
    base = 2 * np.pi * np.arange(p) / p
    if row == "W06":
        base = base + np.array([0.0, 1 / 32, -1 / 64, 1 / 128, -1 / 32])
    return np.tile(base, (SHAPES[row][1], 1))


def generator(row):
    """Independent finite multifrequency signed specimen, no stochastic seed."""
    tcount, directions, phases, nz, ny, nx = SHAPES[row]
    z, y, x = np.indices((nz, ny, nx), dtype=np.float64)
    specimen = np.full((nz, ny, nx), 3.0)
    # The finite coefficients, angles and amplitude schedule are frozen in manifest.
    for kz in range(0, min(nz, 2)):
        for ky in range(-3, 4):
            for kx in range(0, 4):
                if (kz, ky, kx) == (0, 0, 0):
                    continue
                amplitude = 32 / (1 + kx * kx + ky * ky + kz * kz)
                offset = (kx + 2 * ky + 3 * kz) * np.pi / 7
                angle = 2 * np.pi * (kx * x / nx + ky * y / ny + kz * z / nz) + offset
                specimen += amplitude * np.cos(angle)
    if row == "W06":
        angle = 2 * np.pi * (x / nx + y / ny)
        specimen = (
            8 * np.cos(angle)
            + (-8 + 2**-9) * np.cos(angle + 2**-10)
            + 2 * np.cos(2 * np.pi * y / ny)
            + np.sin(2 * np.pi * x / nx)
            + 0.25 * np.cos(2 * np.pi * z / max(nz, 1))
        )
    background = 128.0 if row == "W06" else 256.0
    angles = np.arange(directions) * np.pi / directions
    magnitude = 1.25
    carriers = magnitude * np.column_stack((np.cos(angles), np.sin(angles)))
    phi = phases_for(row)
    analytic = np.empty(SHAPES[row], np.float64)
    for t in range(tcount):
        first = 0.55 if t == 0 else 0.37
        second = 0.23 if t == 0 else 0.16
        shift = 0.0 if t == 0 else 0.41
        for d in range(directions):
            carrier_angle = 2 * np.pi * (carriers[d, 0] * x * 0.1 + carriers[d, 1] * y * 0.1)
            for p in range(phases):
                theta = carrier_angle + phi[d, p]
                illumination = 1 + first * np.cos(theta + shift)
                if phases == 5:
                    illumination = illumination + second * np.cos(2 * theta + 0.3 + 2 * shift)
                analytic[t, d, p] = background + specimen * illumination
    raw = analytic.astype(np.float32)  # Public raw boundary requires exact float32.
    remember("generator.analytic64", analytic)
    remember("generator.raw32", raw)
    remember("generator.specimen", specimen)
    return raw, analytic, carriers, background


def settings(row, background):
    """Declare every scientifically selected workflow setting."""
    orders = 2 if row == "W01" else 3
    acquisition = dict(
        acquisition_mode="2d" if row == "W01" else "3d",
        dxy_um=0.1,
        dz_um=0.0 if row == "W01" else 0.2,
        norders=orders,
        background=background,
        lateral_zoom=2.0,
        axial_zoom=1,
        phase_policy="supplied" if row == "W06" else "uniform",
        edge_pixels=0,
        equalize=False,
        equalize_z=False,
        equalize_time=False,
    )
    if row == "W06":
        acquisition["phases_rad"] = phases_for(row)
    carrier = dict(
        linespacing_um=0.8 if row == "W01" else 0.4,
        phase_start_angle_rad=0.0,
        search_carriers=row in ("W03", "W04"),
        use_time0_carriers=True,
        fit_all_phases=row != "W03",
        amplitude_floors=np.array([0.75, 0.5]) if row == "W03" else None,
    )
    filtering = dict(
        wiener=0.125,
        wiener_increment=0.0,
        suppress_singularities=False,
        output_taper="none",
        omit_kz0=False,
        filter_overlaps=True,
    )
    return acquisition, carrier, filtering


def make_transfer(orders):
    """Declare the complete constant complex analytic transfer."""
    # Constant but genuinely complex, complete radial table; complex64 exact.
    samples = np.empty((orders, 64, 64), np.complex64)
    for m in range(orders):
        samples[m] = complex(1 - m / 8, m / 32)
    remember("transfer.caller", samples)
    return sim.declare_otf(samples, layout="radial", dkr_cyc_um=0.25, dkz_cyc_um=0.25)


def workflow(raw, acquisition, carrier, filtering, transfer, label):
    """Call only the root-facade full workflow entry."""
    return timed(
        label,
        lambda: sim.reconstruct_workflow(
            raw,
            acquisition=acquisition,
            optics=OPTICS,
            carrier=carrier,
            filtering=filtering,
            specimen_identity={"id": "HP114-analytic-v1", "intensity_unit": "detector-counts"},
            transfer=transfer,
            transfer_identity={
                "id": "HP114-constant-complex-v1",
                "intensity_unit": "dimensionless-transfer",
                "optics": OPTICS,
            },
        ),
    )


def one_time(bands, t):
    """Construct a public one-time band record with rebased diagnostics."""
    # Public record construction, no imports/calls to private product helpers.
    names = (
        "quadratures",
        "noise_variance_factors",
        "separation_matrices",
        "phase_angles_rad",
        "frame_sums",
        "equalization_gains",
        "off_frame_sums",
        "off_equalization_gains",
        "off_quadratures",
        "between_displacements_pixels",
        "exposure_displacements_pixels",
    )
    values = {
        name: None if getattr(bands, name) is None else getattr(bands, name)[t : t + 1]
        for name in names
    }
    return dataclasses.replace(
        bands,
        **values,
        input_shape=(1, *bands.input_shape[1:]),
        phase_policies=bands.phase_policies[t : t + 1],
        header_timestamps_after=None,
        sentinel_frames=tuple((0, *s[1:]) for s in bands.sentinel_frames if s[0] == t),
        trace=tuple(dataclasses.replace(e, time_index=0) for e in bands.trace if e.time_index == t),
    )


def compose(bands, transfer, baseline, carrier, filtering, label):
    """Compose public estimation and time-specific known reconstruction."""
    parameters = timed(
        label + ".estimate",
        lambda: sim.estimate_parameters(
            bands,
            transfer,
            initial_carriers_cyc_um=baseline.initial_carriers_cyc_um,
            **OPTICS,
            search_carriers=carrier["search_carriers"],
            use_time0_carriers=carrier["use_time0_carriers"],
            amplitude_floors=carrier["amplitude_floors"],
            fit_all_phases=carrier["fit_all_phases"],
            omit_kz0=False,
        ),
    )
    reconstructions = []
    for t in range(bands.input_shape[0]):
        single = one_time(bands, t)
        result = timed(
            label + f".known.{t}",
            lambda single=single, t=t: sim.reconstruct_known(
                single,
                transfer,
                carriers_cyc_um=parameters.carriers_cyc_um[t],
                modulation=parameters.modulation[t],
                **OPTICS,
                **filtering,
            ),
        )
        reconstructions.append(result)
    image = np.concatenate([r.image for r in reconstructions], axis=0)
    return dict(image=image, bands=bands, parameters=parameters, reconstructions=reconstructions)


def corrected_replay(raw, bands, background, quantize=False):
    """Replay the frozen camera/separation formulas without interception."""
    corrected = remember(
        "corrected.source", bands.input_scale * (raw.astype(np.float64) - background)
    )
    used = (
        timed("H2_CORRECTED.pack-unpack", lambda: pack(corrected, "corrected"))[1]
        if quantize
        else corrected
    )
    lateral = np.fft.rfft2(used, axes=(-2, -1))
    q = np.empty_like(bands.quadratures)
    for t in range(q.shape[0]):
        for d in range(q.shape[1]):
            for z in range(q.shape[3]):
                matrix = bands.separation_matrices[t, d, z]
                q[t, d, :, z, :, :-1] = np.einsum(
                    "qp,pyx->qyx", matrix, lateral[t, d, :, z, :, :-1]
                )
                q[t, d, :, z, :, -1] = lateral[t, d, : q.shape[2], z, :, -1]
            if q.shape[3] > 1:
                q[t, d] = np.fft.fft(q[t, d], axis=1)
    remember("corrected.replay.quadratures", q)
    return dataclasses.replace(
        bands, quadratures=q, frame_sums=used.sum(axis=(-2, -1), dtype=np.float64)
    )


def index_frequency(i, n):
    """Keep the positive native Nyquist endpoint."""
    return i if i <= n // 2 else i - n


def assemble_replay(filtered, raw_shape, carriers, x_um, y_um, quantize_embedding=False):
    """Source-identified assembly replay, independently checked by finite sums.

    Isolated filtered/embedded storage experiment, never a public half mode.
    """
    tcount, directions, slots, nz, ny, _ = filtered.shape
    nx = raw_shape[-1]
    output_shape = (nz, 2 * ny, 2 * nx)
    image = np.zeros((tcount, *output_shape), np.float64)
    witness = []
    for t in range(tcount):
        for d in range(directions):
            for m in range((slots + 1) // 2):
                padded = np.zeros(output_shape, np.complex128)
                for iz in range(nz):
                    kz = index_frequency(iz, nz)
                    for iy in range(ny):
                        ky = index_frequency(iy, ny)
                        for ix in range(nx):
                            kx = index_frequency(ix, nx)
                            src = (iz, iy, kx) if kx >= 0 else ((-kz) % nz, (-ky) % ny, -kx)
                            even = filtered[t, d, 0 if m == 0 else 2 * m - 1][src]
                            odd = 0j if m == 0 else filtered[t, d, 2 * m][src]
                            if kx < 0:
                                even, odd = even.conjugate(), complex(odd).conjugate()
                            padded[
                                kz % output_shape[0], ky % output_shape[1], kx % output_shape[2]
                            ] = even + 1j * odd
                label = f"embedding.{t}.{d}.{m}"
                remember(label + ".source", padded)
                if quantize_embedding:
                    used = timed(
                        label + ".pack-unpack",
                        lambda padded=padded, label=label: pack(padded, label),
                    )[1]
                else:
                    used = padded
                spatial = (
                    np.fft.ifft2(used[0], norm="forward")[None]
                    if nz == 1
                    else np.fft.ifftn(used, norm="forward")
                )
                # u(0)=sum F(k), independent of any FFT. Also one nonzero coordinate.
                for point in ((0, 0, 0), (0, 1, 2)):
                    real_terms, imag_terms = [], []
                    for index in np.ndindex(used.shape):
                        angle = (
                            2
                            * math.pi
                            * sum(index[j] * point[j] / output_shape[j] for j in range(3))
                        )
                        value = complex(used[index]) * complex(math.cos(angle), math.sin(angle))
                        real_terms.append(value.real)
                        imag_terms.append(value.imag)
                    finite = complex(math.fsum(real_terms), math.fsum(imag_terms))
                    witness.append(
                        dict(
                            site=label,
                            point=point,
                            finite_sum=finite,
                            transform=complex(spatial[point]),
                            sum_absolute_terms=math.fsum(
                                math.hypot(a, b)
                                for a, b in zip(real_terms, imag_terms, strict=True)
                            ),
                        )
                    )
                if m == 0:
                    image[t] += spatial.real
                else:
                    phase = (
                        2
                        * np.pi
                        * m
                        * (carriers[d, 0] * x_um[None, :] + carriers[d, 1] * y_um[:, None])
                    )
                    image[t] += 2 * (spatial * np.exp(1j * phase)).real
    return image, witness


def exact_inverse(matrix):
    """Exact rational Gauss-Jordan inverse of declared binary64 matrix values."""
    n = len(matrix)
    a = [
        [Fraction.from_float(float(v)) for v in row] + [Fraction(int(i == j)) for j in range(n)]
        for i, row in enumerate(matrix)
    ]
    for column in range(n):
        pivot = next(i for i in range(column, n) if a[i][column])
        a[column], a[pivot] = a[pivot], a[column]
        factor = a[column][column]
        a[column] = [v / factor for v in a[column]]
        for i in range(n):
            if i != column:
                factor = a[i][column]
                a[i] = [v - factor * w for v, w in zip(a[i], a[column], strict=True)]
    return np.array([[float(v) for v in row[n:]] for row in a], np.float64)


def oracle_checks(raw, analytic, baseline, row, background):
    """Observe independent finite sums and exact finite-matrix inverses."""
    bands = baseline.bands
    replay = corrected_replay(raw, bands, background)
    phase_checks = []
    p, slots = raw.shape[2], bands.quadratures.shape[2]
    for d in range(raw.shape[1]):
        angles = phases_for(row)[d]
        design = np.array(
            [
                [1 / p]
                + [
                    v
                    for m in range(1, (slots + 1) // 2)
                    for v in (2 * math.cos(m * a) / p, 2 * math.sin(m * a) / p)
                ]
                for a in angles
            ]
        )
        left = bands.separation_matrices[0, d, 0]
        # Both routes resolve I against this scaled forward design.
        target = np.eye(slots)
        residual = (
            np.array(
                [
                    [
                        math.fsum(float(left[i, k]) * float(design[k, j]) for k in range(p))
                        for j in range(slots)
                    ]
                    for i in range(slots)
                ]
            )
            - target
        )
        exact = exact_inverse(design)
        phase_checks.append(
            dict(
                direction=d,
                condition=float(np.linalg.cond(design)),
                finite_sum_left_residual=residual,
                exact_rational_inverse=exact,
                source_left_vs_exact=error_metrics(exact, left),
            )
        )
    # Direct compensated phase/spatial sums, selected signed Fourier coordinates.
    corrected = bands.input_scale * (raw.astype(np.float64) - background)
    fourier_checks = []
    nz, ny, nx = raw.shape[-3:]
    for d in range(raw.shape[1]):
        for slot in (0, 1, 2):
            for kz, ky, kx in ((0, 0, 0), (0, 1, 1), (nz - 1, ny - 1, nx // 2)):
                terms = []
                for iz, iy, ix in np.ndindex((nz, ny, nx)):
                    if kx == nx // 2:
                        value = float(corrected[0, d, slot, iz, iy, ix])
                    else:
                        value = math.fsum(
                            float(bands.separation_matrices[0, d, iz, slot, p0])
                            * float(corrected[0, d, p0, iz, iy, ix])
                            for p0 in range(p)
                        )
                    angle = -2 * math.pi * (kz * iz / nz + ky * iy / ny + kx * ix / nx)
                    terms.append(value * complex(math.cos(angle), math.sin(angle)))
                expected = complex(
                    math.fsum(v.real for v in terms), math.fsum(v.imag for v in terms)
                )
                fourier_checks.append(
                    dict(
                        direction=d,
                        slot=slot,
                        index=(kz, ky, kx),
                        finite_sum=expected,
                        prepared=complex(bands.quadratures[0, d, slot, kz, ky, kx]),
                        sum_absolute_terms=math.fsum(abs(v) for v in terms),
                    )
                )
    assembly_checks = []
    for t, known in enumerate(baseline.reconstructions):
        replay_image, witnesses = assemble_replay(
            known.filtered_quadratures,
            (1, *raw.shape[1:]),
            baseline.parameters.carriers_cyc_um[t],
            known.x_um,
            known.y_um,
        )
        assembly_checks.append(
            dict(
                time=t,
                formula_replay_vs_public=error_metrics(known.image, replay_image),
                finite_inverse_sums=witnesses,
            )
        )
    return dict(
        generator_float32_cast_error=error_metrics(analytic, raw),
        phase=phase_checks,
        preparation_replay_error=error_metrics(bands.quadratures, replay.quadratures),
        finite_forward_sums=fourier_checks,
        assembly=assembly_checks,
        scope=(
            "finite sums validate mapping sign/scale, not physical recovery; "
            "residuals require review"
        ),
    )


def decision_projection(parameters):
    """Keep ordered discrete outcomes separate from continuous fit values."""
    names = (
        "stage",
        "orders",
        "integer_peak_xy",
        "x_offset_status",
        "y_offset_status",
        "alias_decisions",
        "branch",
        "strict_improvement",
        "status",
        "order",
        "floor_applied",
        "phase_replaced",
        "source_time",
        "remake_overlaps",
    )
    return dict(
        branches=parameters.branches,
        ordered_events=[
            dict(
                kind=e.kind,
                time=e.time_index,
                direction=e.direction_index,
                details={k: v for k, v in e.details if k in names},
            )
            for e in parameters.trace
        ],
    )


def parameter_comparison(a, b, shape):
    """Report carrier, modulation and exact decision changes."""
    ca, cb = a.carriers_cyc_um, b.carriers_cyc_um
    ma, mb = a.modulation, b.modulation
    valid = (np.abs(ma) != 0) & (np.abs(mb) != 0)
    wrapped = np.full(ma.shape, np.nan)
    wrapped[valid] = np.angle(mb[valid] * np.conjugate(ma[valid]))
    return dict(
        carrier_cyc_um=error_metrics(ca, cb),
        carrier_bin_components=(cb - ca) * np.array([shape[-1] * 0.1, shape[-2] * 0.1]),
        modulation=error_metrics(ma, mb),
        raw_modulation=error_metrics(a.raw_modulation, b.raw_modulation),
        amplitude_error=np.abs(mb) - np.abs(ma),
        wrapped_phase_error_rad=wrapped,
        phase_defined=valid,
        decisions_reference=decision_projection(a),
        decisions_candidate=decision_projection(b),
        decisions_equal=encode(decision_projection(a)) == encode(decision_projection(b)),
    )


def expected_branches(row):
    """Name the intended wider known/search/reuse routes before observation."""
    t, d = SHAPES[row][:2]
    return tuple(
        tuple(
            "searched"
            if row in ("W03", "W04") and i == 0
            else "time0-reused"
            if row == "W04"
            else "known"
            for _ in range(d)
        )
        for i in range(t)
    )


def public_boundaries(raw, acquisition, carrier, filtering, transfer, background, row):
    """Check selected same-value ownership and invalid public-input boundaries."""
    result = {}
    if row != "W01":
        return result
    # Both examples preserve values, source ownership and exact float32 representation.
    wide = np.zeros((*raw.shape[:-1], raw.shape[-1] * 2), np.float32)
    wide[..., ::2] = raw
    strided = remember("boundary.strided", wide[..., ::2])
    strided.flags.writeable = False
    contiguous = remember("boundary.readonly", raw.copy())
    contiguous.flags.writeable = False
    for name, value in (("strided-readonly", strided), ("contiguous-readonly", contiguous)):
        result[name] = workflow(
            value, acquisition, carrier, filtering, transfer, "boundary." + name
        ).image
    half = remember("boundary.half", raw.astype(np.float16))
    result["half_workflow"] = workflow(
        half, acquisition, carrier, filtering, transfer, "boundary.half.workflow"
    ).image
    prep_options = {k: v for k, v in acquisition.items() if k != "phase_policy"}
    result["half_acquisition_dtype"] = sim.prepare_acquisition_bands(
        half, **prep_options
    ).quadratures.dtype.str
    # prepare_bands is intrinsically 3D; use W02 for its chosen accepted half path later.
    bad = raw.copy()
    bad.flat[0] = np.nan
    for name, value in (("nonfinite", bad), ("unsupported-shape", raw[..., 0])):
        try:
            workflow(value, acquisition, carrier, filtering, transfer, "boundary." + name)
        except Exception as error:
            result[name] = failure(error, "expected-public-boundary")
        else:
            result[name] = {"unexpected_success": True}
    return result


def run_workflow(args):
    """Execute one finite diagnostic comparison, retaining its wider reference."""
    raw, analytic, nominal_carriers, background = generator(args.row)
    acquisition, carrier, filtering = settings(args.row, background)
    transfer = make_transfer(acquisition["norders"])
    KEEP.append(transfer)
    baseline_start = time.monotonic_ns()
    baseline = workflow(raw, acquisition, carrier, filtering, transfer, "wider.workflow")
    baseline_inclusive = (time.monotonic_ns() - baseline_start) / 1e9
    KEEP.append(baseline)
    if baseline.parameters.branches != expected_branches(args.row):
        raise RuntimeError("study-fixture: wider intended branches not reached")
    if not np.isfinite(baseline.image).all() or not (baseline.image < 0).any():
        raise RuntimeError("study-fixture: wider image did not demonstrate finite signed negatives")
    base = dict(
        image=baseline.image,
        bands=baseline.bands,
        parameters=baseline.parameters,
        reconstructions=baseline.reconstructions,
    )
    if args.strategy == "QUALIFY":
        qualification = dict(
            status="branch-qualified-oracle-review-required",
            wider=baseline,
            nominal_generator_carriers_cyc_um=nominal_carriers,
            independent_oracles=oracle_checks(raw, analytic, baseline, args.row, background),
            public_boundaries=public_boundaries(
                raw, acquisition, carrier, filtering, transfer, background, args.row
            ),
        )
        if args.row == "W02":
            half = remember("prepare_bands.half", raw.astype(np.float16))
            options = {
                k: v
                for k, v in acquisition.items()
                if k not in ("phase_policy", "acquisition_mode")
            }
            qualification["half_prepare_bands"] = sim.prepare_bands(half, **options)
        summary = timed(
            "wider.summary",
            lambda: sim.reconstruct_summary(
                raw,
                acquisition=acquisition,
                optics=OPTICS,
                carrier=carrier,
                filtering=filtering,
                specimen_identity={"id": "HP114-analytic-v1", "intensity_unit": "detector-counts"},
                transfer=transfer,
                transfer_identity={
                    "id": "HP114-constant-complex-v1",
                    "intensity_unit": "dimensionless-transfer",
                    "optics": OPTICS,
                },
            ),
        )
        KEEP.append(summary)
        qualification["summary"] = summary
        qualification["summary_compatibility"] = dict(
            image=error_metrics(baseline.image, summary.image),
            carrier=error_metrics(baseline.parameters.carriers_cyc_um, summary.carriers_cyc_um),
            modulation=error_metrics(baseline.parameters.modulation, summary.modulation),
            branches_equal=baseline.parameters.branches == summary.branches,
        )
        return qualification
    begin = time.monotonic_ns()
    if args.strategy in ("H1", "H1_PROMOTED"):
        half, promoted = timed("H1.pack-unpack", lambda: pack(raw, "H1.raw"))
        candidate_result = workflow(
            half if args.strategy == "H1" else promoted,
            acquisition,
            carrier,
            filtering,
            transfer,
            "candidate.workflow",
        )
        KEEP.append(candidate_result)
        candidate = dict(
            image=candidate_result.image,
            bands=candidate_result.bands,
            parameters=candidate_result.parameters,
            reconstructions=candidate_result.reconstructions,
        )
        scope = "public full workflow; H1 caller half storage with wider computation"
    elif args.strategy in ("H2_CORRECTED", "H2_PREPARED"):
        if args.strategy == "H2_CORRECTED":
            bands = timed(
                "corrected.formula-replay",
                lambda: corrected_replay(raw, baseline.bands, background, True),
            )
        else:
            _, q = timed(
                "prepared.pack-unpack", lambda: pack(baseline.bands.quadratures, "prepared")
            )
            bands = dataclasses.replace(baseline.bands, quadratures=q)
        KEEP.append(bands)
        candidate = compose(bands, transfer, baseline, carrier, filtering, "candidate")
        scope = (
            "camera/separation wider-compute formula replay + public downstream stages"
            if args.strategy == "H2_CORRECTED"
            else "public band-record pack/unpack + public downstream stages"
        )
    elif args.strategy in ("H2_FILTERED", "H2_EMBEDDED"):
        images, witnesses = [], []
        for t, known in enumerate(baseline.reconstructions):
            filtered = known.filtered_quadratures
            if args.strategy == "H2_FILTERED":
                _, filtered = timed(
                    f"filtered.{t}.pack-unpack",
                    lambda filtered=filtered, t=t: pack(filtered, f"filtered.{t}"),
                )
            image, witness = timed(
                f"assembly-replay.{t}",
                lambda filtered=filtered, t=t, known=known: assemble_replay(
                    filtered,
                    (1, *raw.shape[1:]),
                    baseline.parameters.carriers_cyc_um[t],
                    known.x_um,
                    known.y_um,
                    args.strategy == "H2_EMBEDDED",
                ),
            )
            images.append(image)
            witnesses.extend(witness)
        candidate = dict(
            image=np.concatenate(images),
            bands=baseline.bands,
            parameters=baseline.parameters,
            reconstructions=baseline.reconstructions,
            isolated_inverse_witnesses=witnesses,
        )
        scope = (
            "isolated assembly formula replay; parameters/filtering fixed wider, "
            "no public half workflow"
        )
    else:
        candidate = base
        scope = "existing wider full workflow baseline"
    inclusive = (
        baseline_inclusive if args.strategy == "WIDER" else (time.monotonic_ns() - begin) / 1e9
    )
    KEEP.append(candidate)
    return dict(
        status="completed",
        scope=scope,
        baseline=base,
        candidate=candidate,
        conversion_and_candidate_seconds=inclusive,
        image_error_count_units=error_metrics(baseline.image, candidate["image"]),
        prepared_error=error_metrics(baseline.bands.quadratures, candidate["bands"].quadratures),
        noise_error=error_metrics(
            baseline.bands.noise_variance_factors, candidate["bands"].noise_variance_factors
        ),
        frame_sum_error=error_metrics(baseline.bands.frame_sums, candidate["bands"].frame_sums),
        gain_error=error_metrics(
            baseline.bands.equalization_gains, candidate["bands"].equalization_gains
        ),
        phase_matrix_error=error_metrics(
            baseline.bands.separation_matrices, candidate["bands"].separation_matrices
        ),
        parameters=parameter_comparison(baseline.parameters, candidate["parameters"], raw.shape),
    )


def failure(error, classification):
    """Preserve exception category, operation context and cause chain."""
    return dict(
        classification=classification,
        exception=type(error).__name__,
        message=str(error),
        code=getattr(error, "code", None),
        stage=getattr(error, "stage", None),
        time_index=getattr(error, "time_index", None),
        direction_index=getattr(error, "direction_index", None),
        cause=None if error.__cause__ is None else failure(error.__cause__, classification),
    )


def fit_equal_power(values):
    """Evaluate the frozen equally spaced three-power formula witness."""
    minus, center, plus = map(float, values)
    slope = (plus - minus) / 2
    curvature = plus + minus - 2 * center
    if curvature == 0:
        return 0.0, "zero-curvature"
    result = -slope / curvature
    return (0.0, "outside-range") if abs(result) > 1.5 else (result, "fitted")


def fit_general(points):
    """Evaluate the frozen general three-point parabola witness."""
    (x1, y1), (x2, y2), (x3, y3) = points
    if len({x1, x2, x3}) != 3:
        return 0.0, "duplicate-coordinate"
    s1, s2 = (y2 - y1) / (x2 - x1), (y3 - y2) / (x3 - x2)
    b1, b2 = (x1 + x2) / 2, (x2 + x3) / 2
    curvature = (s2 - s1) / (b2 - b1)
    return (0.0, "zero-curvature") if curvature == 0 else (b2 - s2 / curvature, "fitted")


def run_kernel(row):
    """Execute exactly one declared K row without a growth search."""
    if row == "K01":
        values = np.array(
            [
                0.0,
                -0.0,
                2**-25,
                -(2**-25),
                2**-24,
                -(2**-24),
                2**-14,
                -(2**-14),
                1.0,
                -1.0,
                65504.0,
                -65504.0,
                65520.0,
                -65520.0,
                70000.0,
                -70000.0,
            ]
        )
        complex_values = values + 1j * values[::-1]
        _, real = pack(values, "K01.real")
        _, paired = pack(complex_values, "K01.complex")
        return dict(
            values=values,
            complex_values=complex_values,
            real_error=error_metrics(values, real),
            paired_error=error_metrics(complex_values, paired),
            half_limits=dict(
                maximum=float(np.finfo(np.float16).max),
                smallest_normal=float(np.finfo(np.float16).tiny),
                smallest_subnormal=float(np.nextafter(np.float16(0), np.float16(1))),
                epsilon=float(np.finfo(np.float16).eps),
            ),
            classification="intentional nonfinite conversions retained; no pipeline continuation",
        )
    if row == "K02":
        result = []
        for label, d, z, y, x, lateral, a in (
            ("W02", 3, 4, 16, 16, 2, 1),
            ("W05", 3, 4, 32, 32, 2, 1),
            ("metadata-only", 3, 32, 512, 512, 2, 1),
        ):
            alpha = 1 / (x * y * z * lateral * lateral * a * d)
            values = alpha * np.array([0.0, -0.0, -128.0, -1.0, -(2**-12), 2**-12, 1.0, 128.0])
            _, promoted = pack(values, "K02." + label)
            result.append(
                dict(label=label, alpha=alpha, values=values, error=error_metrics(values, promoted))
            )
        return result
    if row == "K03":
        result = []
        for n in (16, 4096):
            for magnitude in (2**-12, 1.0, 256.0, 1024.0):
                for pattern in ("constant", "alternating"):
                    signs = (
                        np.ones(n)
                        if pattern == "constant"
                        else np.where(np.arange(n) % 2, -1.0, 1.0)
                    )
                    lower = np.full(n, complex(magnitude, magnitude / 8), np.complex128)
                    higher = signs * complex(magnitude * 3 / 4, -magnitude / 16)
                    label = f"K03.{n}.{magnitude}.{pattern}"
                    packed_l, wide_l = pack(lower, label + ".lower")
                    packed_h, wide_h = pack(higher, label + ".higher")
                    wide_sx = float(np.vdot(wide_l, wide_l).real)
                    wide_cross = np.vdot(wide_l, wide_h)
                    exact_sx = n * (
                        Fraction.from_float(magnitude) ** 2
                        + Fraction.from_float(magnitude / 8) ** 2
                    )
                    exact_cross = (
                        (n if pattern == "constant" else 0)
                        * complex(magnitude, -magnitude / 8)
                        * complex(magnitude * 3 / 4, -magnitude / 16)
                    )
                    # Explicit component half ufuncs, product rounding and half reduction.
                    real_product = np.add(
                        np.multiply(packed_l[..., 0], packed_h[..., 0], dtype=np.float16),
                        np.multiply(packed_l[..., 1], packed_h[..., 1], dtype=np.float16),
                        dtype=np.float16,
                    )
                    half_sx = np.sum(
                        np.add(
                            np.multiply(packed_l[..., 0], packed_l[..., 0], dtype=np.float16),
                            np.multiply(packed_l[..., 1], packed_l[..., 1], dtype=np.float16),
                            dtype=np.float16,
                        ),
                        dtype=np.float16,
                    )
                    result.append(
                        dict(
                            n=n,
                            magnitude=magnitude,
                            pattern=pattern,
                            exact_sx=float(exact_sx),
                            exact_cross=exact_cross,
                            original_sx=float(np.vdot(lower, lower).real),
                            original_cross=np.vdot(lower, higher),
                            quantized_operands_wide_sx=wide_sx,
                            quantized_operands_wide_cross=wide_cross,
                            explicit_half_energy=half_sx,
                            explicit_half_real_cross=np.sum(real_product, dtype=np.float16),
                            explicit_half_real_product_stats=stats(real_product),
                        )
                    )
        return result
    # K04 is formula witnesses, not private helper calls or public branch coverage.
    result = {}
    spectrum = np.array([complex(1024.0, -256.0)] * 16)
    _, quantized = pack(spectrum, "K04.spectrum")
    inverse = np.fft.ifft(quantized, norm="forward")
    result["inverse_growth"] = dict(
        spectrum=spectrum, inverse=inverse, exact_origin=complex(16384.0, -4096.0)
    )
    result["equal_power_fits"] = []
    for label, values in (
        ("fitted", [1.0, 4.0, 3.0]),
        ("zero-curvature", [1.0, 2.0, 3.0]),
        ("outside-range", [1.0, 2.0, 3.0 + 2**-12]),
        ("near-tie", [1.0, 1.0 + 2**-12, 1.0]),
    ):
        _, quantized = pack(np.array(values), "K04.fit." + label)
        result["equal_power_fits"].append(
            dict(
                label=label,
                values=values,
                wider=fit_equal_power(values),
                quantized_wider=fit_equal_power(quantized),
            )
        )
    result["general_fits"] = []
    for label, points in (
        ("fitted", [(0.0, 1.0), (1.0, 4.0), (2.0, 3.0)]),
        ("duplicate-coordinate", [(0.0, 1.0), (0.0, 4.0), (2.0, 3.0)]),
        ("zero-curvature", [(0.0, 1.0), (1.0, 2.0), (2.0, 3.0)]),
    ):
        result["general_fits"].append(dict(label=label, points=points, result=fit_general(points)))
    objectives = np.array([1.0, 1.0 + 2**-12, 1.0])
    _, quantized = pack(objectives, "K04.objectives")
    result["ordered_objectives"] = dict(
        wider=objectives,
        quantized=quantized,
        wider_first_max=int(np.argmax(objectives)),
        quantized_first_max=int(np.argmax(quantized)),
        wider_strict=bool(objectives[1] > objectives[0]),
        quantized_strict=bool(quantized[1] > quantized[0]),
    )
    result["regression_pairs"] = []
    for label, gain in (("equal-energy-singular", 1.0), ("unequal-energy", 1.0 + 2**-12)):
        lower = np.array([1.0, -1.0, 1.0, -1.0], np.complex128)
        higher = lower * gain
        _, wide = pack(higher, "K04.regression." + label)
        result["regression_pairs"].append(
            dict(
                label=label,
                wider_sx=float(np.vdot(lower, lower).real),
                wider_sy=float(np.vdot(higher, higher).real),
                quantized_sy=float(np.vdot(wide, wide).real),
                wider_equal=bool(np.vdot(lower, lower) == np.vdot(higher, higher)),
                quantized_equal=bool(np.vdot(lower, lower) == np.vdot(wide, wide)),
            )
        )
    result["phase_designs"] = []
    for label, angles in (
        ("uniform", [0.0, 2 * math.pi / 3, 4 * math.pi / 3]),
        ("singular", [0.0, 0.0, 0.0]),
        ("near-conditioned", [0.0, 2**-8, 2**-7]),
    ):
        design = np.array([[1 / 3, 2 * math.cos(a) / 3, 2 * math.sin(a) / 3] for a in angles])
        _, wide = pack(design, "K04.design." + label)
        entries = dict(
            label=label, design=design, condition=float(np.linalg.cond(design)), quantized=wide
        )
        for name, value in (("wider", design), ("quantized", wide)):
            try:
                inverse = exact_inverse(value)
                entries[name] = dict(inverse=inverse, residual=inverse @ value - np.eye(3))
            except (StopIteration, ZeroDivisionError) as error:
                entries[name] = failure(error, "intentional-singular-formula-witness")
        result["phase_designs"].append(entries)
    return result


def cpu_feasibility():
    """Observe bounded CPU dtype routes without inferring half arithmetic."""
    values = np.arange(16, dtype=np.float16) - np.float16(7)
    result = {
        "scope": (
            "bounded transform-only; arithmetic/workspace internals not inferred from output dtype"
        )
    }
    try:
        result["complex32_dtype"] = str(np.dtype("complex32"))
    except TypeError as error:
        result["complex32_dtype"] = failure(error, "unsupported-dtype")
    for backend in (np.fft, scipy.fft):
        label = backend.__name__
        transformed = backend.rfft(values)
        inverse = backend.irfft(transformed, n=values.size)
        result[label] = dict(
            input=stats(values),
            forward=stats(transformed),
            inverse=stats(inverse),
            reconstruction=error_metrics(values, inverse),
        )
        try:
            backend.rfft(values, norm="HP114-unsupported")
        except ValueError as error:
            result[label]["unsupported_norm"] = failure(error, "expected-backend-boundary")
    return result


def memory_state():
    """Record live physical and cgroup headroom before fixture allocation."""
    mem = {}
    for line in (text_file("/proc/meminfo") or "").splitlines():
        name, value = line.split(":", 1)
        if name in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            mem[name + "_bytes"] = int(value.split()[0]) * 1024
    cgroup = {}
    for name in (
        "memory.max",
        "memory.current",
        "memory.swap.max",
        "memory.swap.current",
        "memory.events",
    ):
        cgroup[name] = text_file(Path("/sys/fs/cgroup") / name)
    return dict(
        physical=mem,
        cgroup=cgroup,
        pressure=text_file("/proc/pressure/memory"),
        self_cgroup=text_file("/proc/self/cgroup"),
    )


def resource_plan(row):
    """Enumerate conservative simultaneous array payload for one small row."""
    if row not in SHAPES:
        # K03 stores 16 small vector variants including conversion operands.
        return {"finite_kernel_arrays": 16 * 4096 * (16 * 4 + 4 * 2 + 2 * 3)}
    t, d, p, z, y, x = SHAPES[row]
    n = t * d * p * z * y * x
    v = z * y * x
    q = t * d * p * z * y * (x // 2 + 1)
    output = t * z * (2 * y) * (2 * x)
    builds = t * d * (p // 2 + 1)
    # Payload inventory includes baseline+candidate+summary qualification, retained
    # source/replay embeddings and hash/stat conversion buffers. Metadata and
    # backend workspace remain unknown, never silently treated as zero.
    return dict(
        generator_and_caller_and_hash=n * (8 + 4 + 2 + 8 + 8),
        camera_and_lateral_work=n * (8 * 3 + 16 * 2),
        bands_and_filtered=q * 16 * 12,
        diagnostic_overlap_snapshots=builds * 66 * v * 3,
        live_overlap_work=2 * 2 * 16 * v * 3,
        retained_embedding_source_and_packed_and_promoted=t
        * d
        * ((p + 1) // 2)
        * (4 * v)
        * (16 + 4 + 16),
        inverse_and_phase_and_signed_results=output * (16 * 3 + 8 * 8),
        transfer_callers_and_promoted=((p + 1) // 2) * 64 * 64 * (8 + 16),
        finite_sum_observer_and_statistics_buffers=output * (16 * 2 + 8 * 6),
    )


def guard_resource(row):
    """Stop if modeled payload already exhausts known current headroom."""
    state = memory_state()
    ledger = resource_plan(row)
    payload = sum(ledger.values())
    bounds = []
    available = state["physical"].get("MemAvailable_bytes")
    if available is not None:
        bounds.append(available)
    maximum, current = state["cgroup"].get("memory.max"), state["cgroup"].get("memory.current")
    if maximum and maximum != "max" and current:
        bounds.append(max(0, int(maximum) - int(current)))
    if not bounds or payload >= min(bounds):
        raise RuntimeError(
            "resource-skip: modeled simultaneous payload does not fit known current headroom"
        )
    return dict(
        state=state,
        payload_ledger_bytes=ledger,
        modeled_payload_bytes=payload,
        minimum_observed_headroom_bytes=min(bounds),
        unmodeled_bytes=None,
        qualification=(
            "small finite row only; unknown native workspace, metadata "
            "and background reserves; no 16 GiB claim"
        ),
    )


def retained_payload():
    """Count reachable ndarray backing storage once and disclose unknown extent."""
    seen_objects = set()
    backing = {}

    def visit(value):
        if id(value) in seen_objects:
            return
        seen_objects.add(id(value))
        if isinstance(value, np.ndarray):
            root = value
            while isinstance(root.base, np.ndarray):
                root = root.base
            # Non-ndarray backing allocation extent is not always discoverable.
            backing[id(root)] = dict(nbytes=root.nbytes, external_base=root.base is not None)
        elif dataclasses.is_dataclass(value):
            for f in dataclasses.fields(value):
                visit(getattr(value, f.name))
        elif isinstance(value, dict):
            for v in value.values():
                visit(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                visit(v)

    visit(KEEP)
    visit(ARRAYS)
    return dict(
        unique_array_backings=len(backing),
        reachable_array_payload_bytes=sum(v["nbytes"] for v in backing.values()),
        undiscovered_external_backing_extent=any(v["external_base"] for v in backing.values()),
        python_metadata_and_allocator_overhead_bytes=None,
    )


def environment():
    """Record the provisioned numerical route and material process settings."""
    return dict(
        python=sys.version,
        executable=sys.executable,
        prefix=sys.prefix,
        platform=platform.platform(),
        os_release=text_file("/etc/os-release"),
        numpy=np.__version__,
        scipy=scipy.__version__,
        numpy_file=np.__file__,
        scipy_file=scipy.__file__,
        scipy_fft_workers=scipy.fft.get_workers(),
        threads={k: os.environ.get(k) for k in THREAD_KEYS},
        material_env={
            k: os.environ.get(k)
            for k in ("SCIPY_ARRAY_API", "PYTHONPATH", "MALLOC_ARENA_MAX", "LD_PRELOAD")
        },
        cpuinfo=text_file("/proc/cpuinfo"),
        affinity=sorted(os.sched_getaffinity(0)),
        transform_source={
            str(path.relative_to(ROOT)): digest(path)
            for path in (
                ROOT / ".venv/lib/python3.13/site-packages/numpy/fft/_pocketfft.py",
                ROOT / ".venv/lib/python3.13/site-packages/scipy/fft/_basic_backend.py",
                ROOT / ".venv/lib/python3.13/site-packages/scipy/fft/_duccfft/helper.py",
            )
        },
    )


def main():
    """Authorize, execute and retain one future finite numerical attempt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grant", required=True)
    parser.add_argument("--row", choices=(*SHAPES, "K01", "K02", "K03", "K04"), required=True)
    parser.add_argument("--strategy", choices=STRATEGIES, required=True)
    parser.add_argument("--repetition", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--qualification", default="")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    grant = authorize(args)
    if not args.run_id.replace("-", "").replace("_", "").isalnum():
        raise RuntimeError("run id must contain only letters, numbers, hyphens, underscores")
    if not EVIDENCE.is_dir():
        raise RuntimeError("root has not prepared the external raw evidence destination")
    target = EVIDENCE / args.run_id
    target.mkdir(exist_ok=False)  # Every attempt is retained; no overwrite/retry hiding.
    record = dict(
        schema="HP114-study-v1",
        row=args.row,
        strategy=args.strategy,
        repetition=args.repetition,
        run_id=args.run_id,
        grant=grant,
        grant_sha256=digest(args.grant),
        status="started",
        identities={
            "baseline": BASE,
            "harness": digest(__file__),
            "manifest": digest(Path(__file__).with_name("manifest.md")),
            "sources": EXPECTED,
            "task_at_run": digest(ROOT / "docs/tasks/half-precision-study.md"),
        },
    )
    start = time.monotonic_ns()
    global np, scipy, sim
    caught = []
    try:
        import numpy as numpy_module
        import scipy as scipy_module
        import scipy.fft

        import simrecon as simrecon_module

        np, scipy, sim = numpy_module, scipy_module, simrecon_module
        if (np.__version__, scipy.__version__) != ("2.5.3", "1.18.1"):
            raise RuntimeError("pinned numerical dependency versions differ")
        if Path(sim.__file__).resolve() != ROOT / "src/simrecon/__init__.py":
            raise RuntimeError("imported product does not belong to this source checkout")
        record["environment"] = environment()
        record["resource_preallocation"] = guard_resource(args.row)
        record["pre_call_high_water_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        with warnings.catch_warnings(record=True) as caught, scipy.fft.set_workers(1):
            warnings.simplefilter("always")
            record["result"] = (
                run_workflow(args)
                if args.row in SHAPES
                else cpu_feasibility()
                if args.strategy == "CPU"
                else run_kernel(args.row)
            )
            record["warnings"] = [
                dict(
                    category=w.category.__name__,
                    message=str(w.message),
                    filename=w.filename,
                    lineno=w.lineno,
                )
                for w in caught
            ]
        record["status"] = (
            record["result"].get("status", "completed")
            if isinstance(record["result"], dict)
            else "completed"
        )
    except Exception as error:
        record["status"] = "failed-retained"
        record["failure"] = failure(error, "diagnosis-required")
        record["traceback"] = traceback.format_exc()
    finally:
        record["warnings"] = [
            dict(
                category=w.category.__name__,
                message=str(w.message),
                filename=w.filename,
                lineno=w.lineno,
            )
            for w in caught
        ]
        record["whole_run_before_export_seconds"] = (time.monotonic_ns() - start) / 1e9
        record["timings"] = TIMINGS
        record["native_peak_rss_kib_before_export"] = resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
        record["native_peak_rss_bytes_before_export"] = (
            record["native_peak_rss_kib_before_export"] * 1024
        )
        record["rss_interpretation"] = (
            "diagnostic comparison-harness whole-process Linux KiB; "
            "baseline retained before candidate; unmatched between modes; "
            "actual whole-pipeline storage/speed benefit UNMEASURED"
        )
        if np is not None:
            encoded = encode(record)
            encoded["retained_payload"] = retained_payload()
            directory = target / "arrays"
            directory.mkdir()
            index = {}
            for i, (key, value) in enumerate(ARRAYS.items()):
                path = directory / f"{i:05d}.npy"
                np.save(path, value, allow_pickle=False)
                index[key] = dict(
                    path=str(path.relative_to(target)),
                    sha256=digest(path),
                    nbytes=path.stat().st_size,
                )
            encoded["array_index"] = index
        else:
            encoded = record
        encoded["native_peak_rss_kib_after_export"] = resource.getrusage(
            resource.RUSAGE_SELF
        ).ru_maxrss
        encoded["native_peak_rss_bytes_after_export"] = (
            encoded["native_peak_rss_kib_after_export"] * 1024
        )
        encoded["including_export_seconds"] = (time.monotonic_ns() - start) / 1e9
        (target / "run.json").write_text(json.dumps(encoded, indent=2, allow_nan=False) + "\n")
        print(
            json.dumps(
                {
                    "run": str(target / "run.json"),
                    "sha256": digest(target / "run.json"),
                    "status": record["status"],
                }
            )
        )
    return 2 if record["status"] == "failed-retained" else 0


if __name__ == "__main__":
    raise SystemExit(main())
