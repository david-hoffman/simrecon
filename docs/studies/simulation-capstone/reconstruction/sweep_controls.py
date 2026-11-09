"""Small analytical controls for the portable sweep witness."""

import json
import math
from copy import deepcopy
from functools import partial
from itertools import pairwise

import numpy as np
import sweep_response as response
import sweep_scoring as scoring
import sweep_witness as witness


def _reject(call, message):
    try:
        call()
    except ValueError as error:
        if message not in str(error):
            raise
    else:
        raise AssertionError(f"expected rejection: {message}")


def grid_controls():
    """Check exact API values, logarithmic steps and the separate filename labels."""
    exact = (0.002, 0.006324555320336759, 0.02, 0.0632455532033676, 0.2)
    assert exact == response.WIENERS
    labels = ("w-0.002.npz", "w-0.006325.npz", "w-0.020.npz", "w-0.063246.npz", "w-0.200.npz")
    assert tuple(response.WIENER_FILES.values()) == labels
    assert tuple(json.loads(json.dumps(response.WIENERS, allow_nan=False))) == exact
    ulps = 4 * math.ulp(1.0)
    for left, right in pairwise(response.WIENERS):
        assert math.isclose(math.log10(right) - math.log10(left), 0.5, abs_tol=ulps, rel_tol=0)
        assert math.isclose(right**2 / left**2, 10.0, abs_tol=0, rel_tol=ulps)
    assert not {0.006, 0.060}.intersection(response.WIENERS)


def scalar_controls():
    """Exercise exact scalar gates using settings and arrays, with no product records."""
    rows = [
        {"case": case, "wiener": np.float64(w)} for case in witness.PINS for w in response.WIENERS
    ]
    witness.require_complete(rows)
    for index in (1, 3):
        exact = response.WIENERS[index]
        known = {"wiener": np.float64(exact), "effective_wiener": (exact,), "wiener_increment": 0.0}
        assert witness._registered_wiener(np.float64(exact)).hex() == exact.hex()
        assert witness._check_known_wiener(known, exact, "known").hex() == exact.hex()
        for bad, reason in (
            (np.float32(exact), "binary64 scalar"),
            (np.nextafter(exact, math.inf), "unregistered"),
        ):
            _reject(partial(witness._registered_wiener, bad), reason)
            wrong_rows = rows.copy()
            wrong_rows[index] = rows[index] | {"wiener": bad}
            _reject(partial(witness.require_complete, wrong_rows), reason)
            for field, value in (("wiener", bad), ("effective_wiener", (bad,))):
                wrong = known | {field: value}
                _reject(
                    partial(witness._check_known_wiener, wrong, exact, "known"),
                    f"known {field}",
                )
    for bad in ("0.02", True, 0, np.array(0.02)):
        _reject(partial(witness._registered_wiener, bad), "binary64 scalar")

    base = witness.BASE_WIENER
    filtering = {"wiener": np.float64(base), "wiener_increment": np.float64(0.0)}
    sequence = np.array([base], dtype=np.float64)
    witness._check_workflow_wiener(filtering, sequence)
    known = filtering | {"effective_wiener": (np.float64(base),)}
    pairs = tuple(known.items())
    python_known = {"wiener": base, "wiener_increment": 0.0, "effective_wiener": (base,)}
    witness._check_replay_settings(pairs, tuple(python_known.items()))
    prior = {"wiener": base, "effective_wiener": np.float64(base)}
    assert witness._check_reuse_wieners(np.float64(base), prior) == (base, base)
    for bad, dtype, reason in (
        (np.float32(base), np.float32, "binary64 scalar"),
        (np.nextafter(base, math.inf), np.float64, "unregistered"),
    ):
        _reject(
            partial(witness._check_workflow_wiener, filtering | {"wiener": bad}, sequence),
            "workflow filtering wiener",
        )
        wrong_sequence = np.array([bad], dtype=dtype)
        _reject(
            partial(witness._check_workflow_wiener, filtering, wrong_sequence),
            "workflow effective_wiener",
        )
        _reject(partial(witness._check_reuse_wieners, bad, prior), reason)
        for field, value in (("wiener", bad), ("effective_wiener", (bad,))):
            wrong_pairs = tuple((known | {field: value}).items())
            _reject(
                partial(witness._check_replay_settings, wrong_pairs, pairs),
                f"default workflow primary {field}",
            )
            _reject(
                partial(witness._check_replay_settings, pairs, wrong_pairs),
                f"default staged replay {field}",
            )
            _reject(
                partial(witness._check_reuse_wieners, base, prior | {field: bad}),
                f"prior row {field}",
            )
    wrong_increment = {"wiener_increment": np.float32(0.0)}
    _reject(
        lambda: witness._check_workflow_wiener(filtering | wrong_increment, sequence),
        "workflow filtering wiener_increment",
    )
    _reject(
        lambda: witness._check_known_wiener(known | wrong_increment, base, "known"),
        "known wiener_increment",
    )


def response_controls():
    """Check independent count scaling, complex signs and distinguishable parameters."""
    z, y, x = 8, 8, 8
    points = ((3, 2), (9, 12))
    bins = (0, 1, 2)
    carriers = np.array([[0.31, -0.21], [0.10, 0.20], [0.23, 0.14]])
    modulation = np.zeros((3, 2), complex)
    variance = np.ones((3, 3))
    radial_step = 0.10
    table = np.ones((3, 60, z), complex)
    w = np.asarray(response.WIENERS)
    raw = np.full((3, 5, z, y, x), 120_512, dtype=np.float64)
    signatures = response.predicted(
        raw, table, radial_step, carriers, modulation, variance, points, bins
    )
    # Analytic uniform slab: zero-side data and transfer power 3; SU = 3/(3+w²).
    expected = np.zeros_like(signatures)
    expected[:, 0, :] = (3 / (3 + w * w))[:, None]
    np.testing.assert_allclose(signatures, expected, rtol=0, atol=4e-15)
    assert response.prediction_margin(signatures) > 1
    for i, row in enumerate(signatures):
        response.check_projection(row, expected[i])
        wrong_w = expected[(i + 1) % len(expected)]
        _reject(lambda row=row, wrong_w=wrong_w: response.check_projection(row, wrong_w), "differs")
    for i, rounded in ((1, 0.006), (3, 0.060)):
        rounded_slab = expected[i].copy()
        rounded_slab[0] = 3 / (3 + rounded**2)
        _reject(
            lambda i=i, rounded_slab=rounded_slab: response.check_projection(
                rounded_slab, signatures[i]
            ),
            "differs",
        )
        # This smaller rounding error fits the scientific tolerance. The scalar gate is separate.
        narrowed_slab = expected[i].copy()
        narrowed_slab[0] = 3 / (3 + float(np.float32(w[i])) ** 2)
        response.check_projection(narrowed_slab, signatures[i])
    _reject(
        lambda: response.prediction_margin(np.repeat(expected[2:3], 5, axis=0)),
        "does not distinguish",
    )
    for scale in (-1, 1 / 5, 5 / 3, 1 / (z * y * x * 4)):
        _reject(
            lambda scale=scale: response.check_projection(expected[2] * scale, expected[2]),
            "differs",
        )
    wrong_square = 3 / (3 + w[2])
    _reject(
        lambda: response.check_projection(
            expected[2] * wrong_square / expected[2, 0, 0], expected[2]
        ),
        "differs",
    )

    # One positive-order input mode, a noninteger carrier, and a complex transfer/gain.
    amplitude = 9000 - 2500j
    modulation[0, 0] = 0.7 + 0.3j
    transfer = 0.4 - 0.2j
    table.fill(0)
    table[1, :, 1] = transfer
    table[1, :, -1] = transfer.conjugate()
    raw.fill(512)
    axial = 2 * np.pi * np.arange(z) / z
    phases = 2 * np.pi * np.arange(5) / 5
    raw[0] += (2 * np.real(amplitude * np.exp(1j * (axial - phases[:, None]))))[:, :, None, None]
    signatures = response.predicted(
        raw, table, radial_step, carriers, modulation, variance, points, bins
    )
    coords = (np.asarray(points)[:, ::-1] - [x, y]) * 0.04
    ramp = np.exp(2j * np.pi * (coords @ carriers[0]))
    gain = transfer * modulation[0, 0]
    # At its object frequency only the two signed copies of this order carry power.
    projected_count = (
        5 / 12 * amplitude * gain.conjugate() / (2 * abs(gain) ** 2 + w[:, None] ** 2) * ramp
    )
    expected.fill(0)
    expected[:, 1, :] = projected_count * 2e-5
    np.testing.assert_allclose(signatures, expected, rtol=0, atol=4e-15)
    volume = np.zeros((z, 2 * y, 2 * x))
    for j, (iy, ix) in enumerate(points):
        volume[:, iy, ix] = 2 * np.real(projected_count[2, j] * np.exp(1j * axial))
    actual = response.observed(volume, points, bins)
    response.check_projection(actual, expected[2])
    for wrong in (-volume, volume[::-1], np.roll(volume, 1, axis=0)):
        _reject(
            lambda wrong=wrong: response.check_projection(
                response.observed(wrong, points, bins), expected[2]
            ),
            "differs",
        )


def score_controls():
    """Check false splits, unresolved pairs, half width and signed contrast/error."""
    t = scoring.LATERAL_T
    pair = np.maximum(1 - abs(abs(t) - 0.225) / 0.14, 0)
    resolved = scoring.pair_rule(t, pair, 0.45)
    assert resolved["status"] == "resolved"
    np.testing.assert_allclose(resolved["separation_um"], 0.45, rtol=0, atol=1e-14)
    shallow = scoring.pair_rule(t, 0.90 + pair * 0.1, 0.45)
    assert shallow["status"] == "unresolved" and shallow["separation_um"] is None
    assert "valley" in shallow["reason"]
    # Both maxima pass height, separation and dip, but the right one misses its truth window.
    misplaced = np.maximum(1 - np.minimum(abs(t + 0.225), abs(t - 0.085)) / 0.07, 0)
    outcome = scoring.pair_rule(t, misplaced, 0.45)
    assert outcome["status"] == "unresolved" and outcome["separation_um"] is None
    assert outcome["reason"] == "peaks miss ordered truth neighborhoods"
    split = np.maximum(1 - abs(abs(t) - 0.075) / 0.07, 0)
    assert scoring.pair_rule(t, split, 0)["status"] == "false-split"
    isolated = np.maximum(1 - abs(t) / 0.20, 0)
    ring = -0.13 * np.maximum(1 - abs(abs(t) - 0.34) / 0.045, 0)
    signed, widths = scoring.shape_profile(t, isolated + ring + 0.37, 0.16, 0.575, 0.70, 0.25, 0.55)
    assert scoring.pair_rule(t, signed, 0)["status"] == "unresolved"
    np.testing.assert_allclose(
        [widths["fwhm_um"], widths["sidelobe_min_su"]], [0.20, -0.13], rtol=0, atol=1e-14
    )
    assert scoring.crossings(t, 1 - t * t, len(t) // 2) is None

    # The compact broadcast field has a known signed y-gradient at every landmark.
    shape = scoring.OUTPUT_SHAPE
    truth = np.broadcast_to(-2 * scoring.GXY[None, :, None], shape)
    image = np.broadcast_to(-2 * scoring.GXY[None, :, None] + 0.25, shape)
    values, contrasts = scoring.landmark_scores(image, truth)
    assert len(values["nuclear-rim"]["profile_su"]) == 32
    assert len(values["branch_down"]["profile_su"]) == 12
    np.testing.assert_allclose(
        [contrasts["northeast"], contrasts["southwest"]], [0.44, -0.44], rtol=0, atol=1e-14
    )
    for landmark in values.values():
        np.testing.assert_allclose(
            [landmark["signed_bias_su"], landmark["rms_su"]], [0.25, 0.25], rtol=0, atol=1e-14
        )
    truth_wave = np.array([1, 0, -1, 0], float)
    mask = np.array([0, 1, 0, 1], bool)
    metrics = scoring.band_scores(-truth_wave + 0.25, truth_wave, mask)
    np.testing.assert_allclose(
        [
            metrics["relative_error"],
            metrics["coherent_response"],
            metrics["absolute_rms_error_su"],
            metrics["signed_mean_error_su"],
        ],
        [2, -1, np.sqrt(2), 0.25],
        rtol=0,
        atol=1e-14,
    )
    assert scoring.band_scores(truth_wave + 0.25, truth_wave, mask)["relative_error"] == 0
    field = scoring.field_summary(np.array([-2.0, 1.0]), np.array([1.0, 0.0]))
    assert field["signed_mean_error_su"] == -1 and field["residual_range_su"] == [-3, 1]
    assert field["negatives"] == 1


def prior_receipt_controls():
    """Exercise the exact receipt comparisons with no manufactured workflow records."""
    fixed = {
        "output_axes": witness._output_axes(),
        "fixed_metadata": {
            "array_identities": {
                "modulation": witness._array_identity(np.array([[0.5 - 0.25j]], dtype="<c16"))
            }
        },
    }
    prior = json.loads(json.dumps(fixed))
    witness._check_prior_fields(prior, fixed, "case")
    wrong_axis = deepcopy(prior)
    wrong_axis["output_axes"]["origin_um"][0] *= -1
    _reject(lambda: witness._check_prior_fields(wrong_axis, fixed, "case"), "output_axes differs")
    wrong_factor = deepcopy(prior)
    wrong_factor["fixed_metadata"]["array_identities"]["modulation"] = witness._array_identity(
        np.array([[0.5 + 0.25j]], dtype="<c16")
    )
    _reject(
        lambda: witness._check_prior_fields(wrong_factor, fixed, "case"), "fixed_metadata differs"
    )
    identity = {
        "case": "beads",
        "wiener": 0.002,
        "effective_wiener": 0.002,
        "signed_image_counts_identity": witness._array_identity(np.array([-0.5, 0.75])),
    }
    prior = json.loads(json.dumps(identity))
    witness._check_prior_fields(prior, identity, "row identity")
    for field, wrong in (
        ("case", "cell"),
        ("wiener", 0.020),
        ("effective_wiener", 0.020),
        ("signed_image_counts_identity", witness._array_identity(np.array([0.5, 0.75]))),
    ):
        bad = prior | {field: wrong}
        _reject(
            lambda bad=bad: witness._check_prior_fields(bad, identity, "row identity"),
            f"{field} differs",
        )


def main():
    """Exercise the independent oracle without importing or calling the product."""
    grid_controls()
    scalar_controls()
    response_controls()
    score_controls()
    prior_receipt_controls()
    rows = [{"case": case, "wiener": w} for case in witness.PINS for w in response.WIENERS]
    witness.require_complete(rows)
    _reject(lambda: witness.require_complete(rows[:-1]), "missing")
    _reject(lambda: witness.require_complete([*rows[:-1], rows[0]]), "duplicate")
    wrong = rows.copy()
    wrong[rows.index({"case": "beads", "wiener": response.WIENERS[1]})] = {
        "case": "beads",
        "wiener": 0.006,
    }
    _reject(lambda: witness.require_complete(wrong), "unregistered")
    print("PASS: exact grid and scalar gates, signed response, scores, prior receipts, completion")


if __name__ == "__main__":
    main()
