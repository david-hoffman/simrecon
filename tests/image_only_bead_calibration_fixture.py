"""Public-contract observers for finite bead calibration; never call its internals.

Pre-authorship obligation inventory (contract sections, then keeper families):

BC01/02: fixed clear-pupil model, image/truth boundary, unchanged PilotCandidate,
required argument binding, five frozen records, excluded optimizer/solver/transfer
and CLI scope -> binding, records, finite_equation. Prior prerequisite acceptance
proves underlying operations, not this new composition. Old-operation preservation
and absence of unrelated runtime dependencies remain coordinator/D obligations.

BC03: each raw array's plain type, i/u/f kinds, original/normalized finiteness,
rank/shape/nonempty/exact side length; signed/rounded/underflow/layout/endian/
readonly positives; snapshot all inputs; camera instance/subclass, means native
f64 (3,), finite plain contrast, opaque nonblank source, ignored gain/other fields;
origin tuple/subclass, plain finite members; scales built-in nonempty tuple,
plain finite positive members, repeated/increasing/decreasing/huge/subnormal;
all validation before unavailable, ordinary binding -> invalid_*, positive_*,
unavailable, ownership. Wider-original conversion overflow is platform-qualified,
not silently skipped. Concurrent mutation has no atomic-snapshot promise.

BC04: D/radius/refinement/wavelength/index/pupil/pixels, exact containment/tangency/
nonoverlap, closed membership, rounded unit electron weights/mass, relative B,
full signed 28-image squared loss /2M, continuous signed q and axial kappa,
amplitude S normalization, local origin/gauge alternatives -> initialization,
finite_equation, schedule, origin_and_heldout. No recovery/continuum threshold.

BC05: signed finite Gaussian radius4 sigma1 constant0 f64, actual SciPy version,
three positive lexicographic peaks, <=0.5 um suppression without local-max test,
clipped unsmoothed +/-2,3,3 windows, max(Y,0) centroid, inward-only clamp,
clipped/overlap/clamp notes, no overlap repair, positive window/complete-response
max ratio, fixed B_start, finite information vs numerical failure ->
initialization, information_failure, initial_range, finite_equation. Signed and
weighted-centroid fixtures have independently derived impulse/weight geometry;
the Gaussian-tail fixture reaches zero centroid weight. Notes prose has no
parseable schema: accounting values need manual public-result review, not a
fabricated token format. A separate exact-suppression-boundary fixture also
requires a non-local-maximum peak and overlapping centroid windows. Overlapping
initialized centers and finite unusable response/brightness remain fixture gaps.

BC06: all 47 coordinate indices/storage/units, base steps/bounds, fixed start,
brightness scale retention, angle/polar/phase decoding, exact beam endpoints,
positive brightness underflow, nonfinite decoder, exact represented q domain,
no bin rounding, rerasterized centers -> initialization, schedule, endpoints,
finite_equation. Array/field relations do not prove the optical equation.

BC07: scale order, negative/positive order from same incumbent, rounded step/
addition, bounds->geometry->carrier ordering, infeasible no score, unchanged
feasible scores, strict improvement/negative tie, no early stop or retry,
chronological best vs completed-pair incumbent -> schedule, ledger. Natural
poll_range covers immediate stop with no successful poll; improving_pair adds
best/incumbent divergence after an improving score in an unresolved first pair.
No backend call count or hidden-layout demand.

BC08: freeze after all pairs, exact frozen Q256 then Q512, no reselection, first
five Q512 predictions, heldout correction only afterwards, independent training,
paired summaries, late retention -> finite_equation, origin_and_heldout,
late_range. Dependency-specific late prediction/refinement faults need a natural
public reproducer; no patch requiring a particular backend call is introduced.

BC09: all documented fields/types/shapes/frozen bindings, native writable plain
C arrays, no aliases within/across records/calls/callers, chronology, Python
indices/counts, exact derived counters, zero/partial records -> records, ledger,
ownership. The observers use documented attributes, never source introspection.

BC10: all eight exact ordered information conditions, occupied SET rather than
count, coordinate vs parameter, per-coordinate ordered union, unprobed iff zero
distinct-parameter scores, no identifiability claim -> ledger, subnormal,
endpoints. The zero-brightness fixture independently forces zero-brightness and
zero-total codes, including exact zero images. The endpoint fixtures require
targeted exact-zero beams/carriers. zero_carrier_angle and single_beam_illumination
are audited if reached; their occurrence in a later poll is not forced here.

BC11: four statuses, nine stages, invalid vs infeasible vs own/dependency range,
immediate stop, every partial availability rule, None vs empty vs zero, unchanged
caller arrays/random/error/warning policy -> unavailable, information_failure,
initial_range, poll_range, improving_pair, late_range, ledger, preservation.
Unrelated exceptions/warnings,
MemoryError and known dependency-code propagation have no controlled real public
stimulus here: explicitly unproved, never fabricated by a decision mock.

BC12: independent finite-equation 1e-5*T using TOTAL unilluminated peak, separate
node/weight/Bessel/phase/reduction/reference-T uncertainty, exact zero at T=0,
f64 reductions, strict computed decisions, fixed-version determinism, distinct
scientific uncertainties -> finite_equation, deterministic, ledger. Immutable
optical observer domain is enforced; OracleInconclusive blocks proof.

BC13: public completion inventory/compatibility and actual image-derived output
boundary -> all keeper families. Full local/platform/resource/report gates,
unchanged old suite, downstream solver/origin transfer/truth evaluation remain
coordinator-owned and are not claimed by these tests. No source inspection,
test-only production seam, supplied-truth fit or new rejection gate is used.

Every keeper uses fit_bead_calibration, a real caller boundary. New composition
is the distinct gap beyond the sanitized prerequisite completion summary.
Numerical relations audited from returned fields prove those relations only.
Independent finite-equation checks below use immutable public mathematics,
bound by coordinator-public-clarification1.json (SHA256
2aa7f2531f7898b44f437810cdee4fadb2ee5af4b1808d07811f2049b2fcd01a).
All three deployed hashes were independently verified against that clarification
and its immutable public copies. Public script records use their scripts-module
imports. This metadata clarification changes no scientific requirement or oracle.

Exact keeper index (test declarations live in the companion test module):

* BC01/02 binding/scope -> test_binding_all_arguments_required,
  test_binding_no_truth_optimizer_or_extra_inputs,
  test_binding_only_central_may_be_positional; record reuse -> assert_candidate
  via test_records_frozen_public_types_and_independent_writable_snapshots.
* BC03 array domain -> test_invalid_raw_arrays_before_unavailable (three arrays
  x all named invalid forms), test_invalid_physical_box_even_before_normalization,
  test_invalid_orientation_command_dimensions,
  test_finite_original_values_follow_platform_conversion_range. With no wider
  original format the alternate branch exercises a maximum-finite positive
  public input; it supplies no original-finite/normalized-overflow rejection proof.
  Permitted alternatives -> test_positive_raw_representations,
  test_positive_layouts_normalize_to_same_actual_observations. None of these
  treats signed data, readonly storage or conversion rounding as a rejection.
* BC03 scalar/container/camera domain -> test_invalid_contrast_scalar,
  test_invalid_origin_member, test_invalid_scale_member_before_unavailable,
  test_invalid_scales_container, test_invalid_origin_container,
  test_invalid_consumed_camera_fields, test_invalid_camera_type.
  Positive counterparts -> test_positive_minimum_box_and_extreme_normalized_metadata,
  test_relative_count_gauge_and_unconsumed_camera_fields,
  test_real_image_derived_camera_record_composes_without_physical_gain.
* BC03/11 d<=0 and validation ordering ->
  test_unavailable_has_exact_absence_and_zero_ledgers plus every invalid_* test.
* BC04 geometry/membership/unit mass -> assert_candidate's Fraction predicates
  in every ledger audit; all-tail signed loss ->
  test_finite_equation_initializer_brightness_and_initial_complete_signed_loss,
  test_finite_equation_changed_profiles_illumination_and_full_training_loss.
  Separate gamma/eta and radial/angular samples distinguish unequal sides and
  carrier-dependent axial frequency. The adapted incumbent is checked too.
  Relative gauge -> test_relative_count_gauge_and_unconsumed_camera_fields.
  Origin-only metadata -> test_origin_and_heldout_only_change_allowed_metadata_summaries.
* BC05/06 exact initial state/units ->
  test_initialization_full_47_state_units_and_fixed_nominal_settings,
  test_initialization_tie_lexicographic_edges_and_inward_clamp,
  test_initialization_smooths_signed_data_and_uses_unsmoothed_positive_centroid,
  test_initialization_weighted_physical_centroid_without_pixel_round_trip,
  test_initialization_exact_suppression_boundary_and_nonlocal_peak_window.
  Brightness ratio independent optical uncertainty -> assert_initial_brightness.
  Missing positive data/peaks/zero centroid weight ->
  test_information_failure_is_not_range_or_fabricated_candidate.
* BC06/07 decoder/order/scale/steps/domain/strict pairing ->
  test_schedule_all_coordinates_strict_pair_decisions_and_fixed_scales,
  test_schedule_order_repeats_huge_legal_scale_no_clamp_or_early_stop,
  test_endpoints_exact_beam_zeros_and_coordinate_parameter_distinction and
  assert_ledger/assert_decoded. A feasible score must satisfy coordinate bounds,
  exact geometry and exact represented carrier norm. At rho=1, angle=0,
  q=(0,RN64(1.515/0.488)) is strictly legal by Fraction comparison and MUST score.
  The old rho-near-one heuristic is removed. A nonzero-angle unscored attempt
  has no returned q snapshot. Taylor/ordinary-decoder enclosures exclude proved
  legal refusals; straddling leaves an observer gap, not a relaxed domain limit.
* BC07/10 unchanged finite arithmetic/ties/unprobed ->
  test_subnormal_scale_scores_unchanged_trials_and_reports_unprobed. Unchanged
  coordinates/parameters do not imply equal computed losses or nonselection.
  Selection/equality codes follow reported scores via assert_ledger; numerical
  truth is checked separately on initial and unchanged poll scores. Equal
  strictly improving +/- ties are conditional, not forced by a fixture.
* BC08 fixed rescores/first-five prediction ->
  test_finite_equation_exact_frozen_rescores_and_first_five_prediction;
  this checks the adapted moving candidate, not only unchanged initialization;
  summary sign/divisors ->
  test_residuals_signed_mean_and_rms_from_complete_frozen_prediction;
  heldout independence ->
  test_origin_and_heldout_only_change_allowed_metadata_summaries, on subnormal
  and moving schedules without a predetermined fitted trajectory, and
  test_late_range_retains_complete_prediction_both_summaries_absent.
* BC09 every documented field/type/array shape, successful chronology,
  derived counts, ordering, strict best, completed-pair incumbent, frozen state,
  and conditional partial-state relations -> assert_ledger. No representation
  introspection is used to enumerate undocumented/default fields. Freezing and
  aliases -> test_records_frozen_public_types_and_independent_writable_snapshots,
  test_deterministic_repeated_fixed_dependency_execution and preservation test.
* BC10 each code/union/distinct count/unprobed definition -> information and
  assert_ledger. All-zero brightness is forced by
  test_zero_brightness_is_a_legal_fit_and_information_codes_stay_literal;
  signed zeros compare numerically, with no extra tolerance or identifiability
  inference. Equal occupied count never supplies set-equivalence evidence.
* BC11 own unavoidable correction/initial-square/late-correction ranges ->
  test_normalization_range_before_candidate_formation,
  test_initial_range_keeps_constructed_candidate_but_no_success_or_polls,
  test_poll_range_stops_immediately_and_retains_unresolved_partial_pair,
  test_improving_poll_is_best_but_not_incumbent_when_positive_trial_fails,
  test_late_range_retains_complete_prediction_both_summaries_absent.
  Known dependency codes, actual MemoryError, unrelated warnings/exceptions,
  and late refinement/prediction faults lack independent natural stimuli.
  Improving incomplete-pair best/incumbent divergence now has a dedicated keeper.
  Conditional ledger
  assertions do not substitute for those missing exercised outcomes.
* BC11 caller state -> test_preservation_inputs_random_numpy_and_warning_policy
  on success/invalid/unavailable/initial-range/poll-range; caller error=raise and
  warning=error, random states, array values/layout/write flags and no aliases.
* BC12 fixed-version exact repetition ->
  test_deterministic_repeated_fixed_dependency_execution. Ordinary decoder
  roundoff comparisons are explicitly separate from certified optical bounds.
  T=0 exactness -> zero-brightness fixture. T>0 total-peak/reference uncertainty
  -> finite_predictions and all test_finite_equation_* declarations.
* BC13 preserved old API/suite, no specimen coupling, downstream truth separation,
  platform/resource/full-report gates and actual full-noisy completion remain
  excluded from A proof and owned by coordinator/D. This is a proposed blind
  test checkpoint, not completeness, recovery or platform acceptance.

Scoped B1 correction / B2 dependency map (prior proposed checkpoint
ad37933efd39b747f7e8540b16e7f17e6fe5763a998e40c00abc297066b04885;
no accepted checkpoint exists). Findings SHA256
1dbc6832e6b4f78558daf2fa3d4ca6e196c15d37fcceeb8db6e81be094817567.

F1 -> BC07 pairing/best, BC10 equality/union, BC12 ordinary reductions: remove
fixed equality/nonselection/best-index demands from subnormal keeper; retain
unchanged-coordinate/unprobed proof. Mixed schedule checks unchanged COORDINATES,
not bitwise equal candidate records. Zero-brightness no longer implies equal
computed objectives. information/assert_ledger retain exact reported-float
selection and equality rules. Initial + unchanged-poll finite-equation checks
remain independent numerical oracles, not a comparison between those scores.

F2 -> BC06 carrier representation and BC07 feasibility order: endpoint keeper
requires rho_one to score with exact (0,k0_float); carrier_refusal_possible
replaces the generic rho tolerance in assert_ledger. Exact-zero/axis cases use
no norm tolerance. Non-axis enclosures reuse trig_enclosures/interval_product
and the existing decoder envelope; returned scored carriers always undergo an
EXACT norm comparison. All assert_ledger keepers above are affected dependents.
Section6 specifies ordinary float64 trigonometry without selecting a correctly
rounded transcendental backend; section9 omits q for infeasible polls. Some
non-axis boundary refusals therefore cannot be fully certified from the exposed
record. This is an explicit observer limit, never proof of an illegal carrier.

F3 -> BC04 direct squares; BC05 finite initialization; BC07 immediate stop;
BC09/11 partial grammar/counters: poll_range_arguments feeds qualification and
the new poll-range keeper (also caller preservation). Qualification dependencies:
exact exp Taylor/dyadic Gaussian intervals -> peak ordering; gamma64 centroid
box -> exact stable midpoint sets; frozen unit_sites/optical_enclosure ->
B_start intervals and component errors; analytic illumination Lipschitz bound
-> decoder alternatives; TOTAL peak/exact rational residual bounds -> finite
initial sum and impossible positive-trial direct square. Huge brightness is
handled in rational L=2e151 units, never as electron input to the optical helper;
every reused helper call retains its original finite domain. The keeper checks
initial coordinates and B/center enclosures, all20 attempts, 19 infeasible polls,
two trace entries, nine completed pairs, unresolved coordinate9 signs, no later
stages and unchanged caller state on this new failure path.

Heldout follow-up -> BC08/12: compare each actual baseline training record to
changed heldout/origin records, for both schedules. No predetermined selected
trial or recovery expectation is supplied. The mean-shift allowance propagates
BOTH returned-prediction-relative reductions rather than a guessed fixed error.
Shared ledger/carrier/qualification changes expand fresh B2 review to this
entire two-file checkpoint and all keepers; B2 determines retained evidence
applicability. B1 is a nonacceptance, not a verdict to resume. All prior charges,
including initial false oracle assumptions, remain retained.

Scoped B2-F1 correction / fresh B3 dependency map (prior proposed checkpoint
c2ed5626e317f74b2c031c8be9d68697b99ad6f78411bae11e83794737cc71f8).
B2 requalified the earlier three corrections, combined-image T and heldout
invariance; its sole nonacceptance was the missing improving-incomplete pair.
The pure public-equation proposal (SHA256
4c26c201493d632c4a9fd319e639153907ad6ac25cc4bc9700b9785928571a66)
was read and independently adapted, never executed at its B2/artifact paths.
Published keepers depend only on these owned helpers and deployed frozen math.

BC07 section7 -> chronological best updates after the first negative score,
without committing a paired decision. BC09 section9 -> three chronological
score records, two coordinate0 attempts, independent initial/best/trace arrays,
best index1 versus incumbent index0, and unresolved selected=None on BOTH signs.
BC11 section11 -> positive numerical failure stops the first pair immediately;
retain the improving negative candidate/Q128 score, no frozen/refined/heldout
outputs. BC13 section13 -> this previously missing partial-state boundary now
has its own real-entry keeper. The old20-poll/no-successful-poll keeper stays.

improving_pair_arguments -> fixed L=1e146 central observations, zero training
except the supplied exact hex pixel, zero heldout, blank0/contrast1/scale0.5.
improving_pair_qualification -> unchanged _qualify_scaled_peaks for initialization;
unchanged _qualify_profile_stability for initial and both trial center boxes;
frozen unit_sites/optical_enclosure for all three prescribed finite targets;
fresh initial-only brightness intervals held fixed for both trials; independent
field/S Lipschitz accounting; outward 2^-80 interval arithmetic; each state's
TOTAL unilluminated peak; exact signed residual/direct-square bounds including
ordinary reduction alternatives. Its disjoint intervals prove initial finite,
negative finite/strictly improving, positive required square unrepresentable.
No search/decision/output mock, implicit truth input or special product seam.

The new keeper binds observed initial centers, brightness and coordinates to
the independently qualified domain, then checks each actual reported score
against its own numerical interval. Strict best/incumbent assertions use those
reported scores. It also checks caller arrays/random/warning/NumPy policies
under error=raise, all partial counters, and actual mutation of an independent
best-coordinate snapshot. assert_ledger/assert_independent/assert_same and all
pre-existing oracle, fixture and keeper bodies remain unchanged. Their reuse
by this new case is the affected dependency edge; the risk-specific qualifier
is dedicated rather than a change to earlier expectation sources. B3 decides
retained-proof applicability and review scope; B2 is closed, not acceptance.
Non-axis refused-carrier observability, dependency/unrelated failure propagation,
and later refinement/prediction failure stimuli remain disclosed limitations.
"""

from __future__ import annotations

import itertools
import math
from fractions import Fraction
from functools import lru_cache
from typing import Any

import numpy as np
from numpy.typing import NDArray

from simrecon import ScalarCameraEstimate

F64 = NDArray[np.float64]
D = (0.125, 0.080, 0.080)
RADIUS = 0.050
SHAPE = (1, 2, 15)
RANGE_SHAPE = (2, 2, 16)
AXIAL_SHAPE = (2, 2, 15)
EPS = np.finfo(np.float64).eps
SMALLEST = float(np.nextafter(0.0, 1.0))
BASE_STEPS = np.array(
    [*(d / 8 for _ in range(3) for d in D), *([0.1] * 3), 0.05, 0.05, *([0.01] * 6), *([0.05] * 27)]
)
CODE_ORDER = (
    "unchanged_coordinate",
    "unchanged_parameter",
    "occupancy_equivalent_center",
    "zero_brightness_center",
    "zero_carrier_angle",
    "single_beam_illumination",
    "zero_total_brightness",
    "equal_computed_objective",
)
FIELDS = {
    "PilotCandidate": (
        "centers_um_zyx",
        "brightness_relative",
        "carriers_yx_per_um",
        "phases_rad",
        "beam_amplitudes",
        "occupied_counts",
        "stored_unit_masses_e",
    ),
    "BeadCalibrationScore": (
        "stage",
        "pupil_order",
        "coordinates",
        "candidate",
        "objective",
        "outcome",
        "failure_code",
    ),
    "BeadCalibrationAttempt": (
        "sweep_index",
        "coordinate_index",
        "sign",
        "base_score_index",
        "trial_coordinates",
        "coordinate_changed",
        "parameter_changed",
        "outcome",
        "infeasibility_reason",
        "score_index",
        "selected",
        "information_codes",
        "failure_code",
    ),
    "BeadCoordinateEvidence": (
        "coordinate_index",
        "attempt_count",
        "scored_count",
        "distinct_coordinate_scored_count",
        "distinct_parameter_scored_count",
        "selected_count",
        "information_codes",
    ),
    "BeadCalibrationCounts": (
        "planned_poll_attempts",
        "attempted_polls",
        "scored_polls",
        "infeasible_polls",
        "numerical_incomplete_polls",
        "completed_pairs",
        "completed_sweeps",
        "score_attempts",
        "successful_scores",
    ),
    "BeadCalibrationResult": (
        "status",
        "stage",
        "message",
        "failure_code",
        "detector_shape_zyx",
        "origin_um_zyx",
        "scipy_version",
        "camera_source",
        "blank_counts",
        "contrast_counts",
        "sweep_scales",
        "initialization_notes",
        "initial_candidate",
        "initial_coordinates",
        "best_candidate",
        "best_coordinates",
        "best_score_index",
        "incumbent_score_index",
        "frozen_candidate",
        "frozen_coordinates",
        "objective_trace",
        "poll_attempts",
        "coordinate_evidence",
        "unprobed_coordinates",
        "counts",
        "training_objectives_q128_q256_q512",
        "heldout_prediction",
        "heldout_residual_mean",
        "heldout_residual_rms",
    ),
}


def camera(**changes: Any) -> ScalarCameraEstimate:
    """Construct consumed public fields; deliberately no physical gain gate."""
    fields: dict[str, Any] = {
        "means_counts": np.array([-7.0, 5.0, 7.0]),
        "variances_counts2": None,
        "frame_means_counts": None,
        "frame_variances_counts2": None,
        "empirical_mean_se_counts": None,
        "contrast_counts": 2.0,
        "gain_counts_per_e": None,
        "information_codes": ("nonpositive_variance_contrast",),
        "source": "opaque estimated camera",
    }
    fields.update(changes)
    return ScalarCameraEstimate(**fields)


def observations(
    *, edge: bool = False, tie: bool = False, shape: tuple[int, int, int] = SHAPE
) -> tuple[F64, F64, F64]:
    """Dyadic signed observations; these are data, not a claimed recovered truth."""
    y = np.full(shape, 0.0 if tie else -0.03125)
    peaks = ((0, 7, 15) if edge else (1, 8, 15)) if shape == RANGE_SHAPE else (0, 7, 14)
    for x, height in zip(peaks, (8.0, 8.0, 8.0) if tie else (8.0, 6.0, 4.0), strict=True):
        y[0, 0, x] = height
    structured = np.empty((3, 9, *shape))
    for o, p in itertools.product(range(3), range(9)):
        structured[o, p] = (o + 1) / 8 + (p - 4) / 16 + y / 2 ** (o + 2)
    heldout = (np.arange(15 * math.prod(shape)).reshape(3, 5, *shape) % 17 - 8) / 16
    return 5 + 2 * y, 5 + 2 * structured, 5 + 2 * heldout


def arguments(*, shape: tuple[int, int, int] = SHAPE, **changes: Any) -> dict[str, Any]:
    central, structured, heldout = observations(shape=shape)
    values = dict(
        central_counts=central,
        structured_counts=structured,
        heldout_counts=heldout,
        camera_estimate=camera(),
        origin_um_zyx=(0.0, -0.125, 1.25),
        sweep_scales=(SMALLEST,),
    )
    values.update(changes)
    return values


def poll_range_arguments() -> dict[str, Any]:
    """Build the natural direct-square poll failure using observations only."""
    central, structured, _ = observations(shape=RANGE_SHAPE)
    return arguments(
        central_counts=2e151 * ((central - 5) / 2),
        structured_counts=2e151 * ((structured - 5) / 2),
        heldout_counts=np.zeros((3, 5, *RANGE_SHAPE)),
        camera_estimate=camera(means_counts=np.zeros(3), contrast_counts=1),
        sweep_scales=(900.0,),
    )


def _gaussian_weight_intervals() -> list[tuple[Fraction, Fraction]]:
    # Enclose exp(-j^2/2) by the reciprocal of the positive exp Taylor sum.
    # For x<=8, after term 120 the remaining positive terms have ratio
    # <=8/122. Round the resulting normalized bounds outward to dyadics;
    # later convolutions then use exact, modest-size rational arithmetic.
    exps = []
    for j in range(-4, 5):
        x = Fraction(j * j, 2)
        term = total = Fraction(1)
        for k in range(1, 121):
            term *= x / k
            total += term
        tail = term * x / 121 / (1 - x / 122)
        exps.append((1 / (total + tail), 1 / total))
    denominator_lo, denominator_hi = (sum(v[i] for v in exps) for i in (0, 1))
    dyadic = 2**60
    return [
        (
            Fraction(math.floor(lo / denominator_hi * dyadic), dyadic),
            Fraction(math.ceil(hi / denominator_lo * dyadic), dyadic),
        )
        for lo, hi in exps
    ]


def _qualify_scaled_peaks(y: F64, peaks: tuple[tuple[int, int, int], ...]) -> None:
    from simulation_optics_fixture import OracleInconclusive

    weights = _gaussian_weight_intervals()
    magnitude = max(abs(Fraction(float(v))) for v in y.flat)
    values = {i: (Fraction(float(y[i])), Fraction(float(y[i]))) for i in np.ndindex(y.shape)}
    for axis in range(3):
        old, values = values, {}
        for i in np.ndindex(y.shape):
            lo = hi = Fraction(0)
            for shift, weight in zip(range(-4, 5), weights, strict=True):
                other = list(i)
                other[axis] += shift
                if 0 <= other[axis] < y.shape[axis]:
                    a, b = interval_product(old[tuple(other)], weight)
                    lo += a
                    hi += b
            values[i] = lo, hi
    # The three nine-tap reductions/finite kernel normalization take fewer
    # than 256 ordinary operations along an entry's separable path. Inflate
    # further by 16; this is product roundoff, separate from exact reference
    # kernel intervals. No special-function reference margin is guessed.
    e = Fraction(float(EPS))
    arithmetic = 16 * (256 * e / (1 - 256 * e)) * magnitude
    available = set(np.ndindex(y.shape))
    for peak in peaks:
        if values[peak][0] <= arithmetic or any(
            values[peak][0] - arithmetic <= values[i][1] + arithmetic
            for i in available
            if i != peak
        ):
            raise OracleInconclusive("scaled initializer peak order is not independently separated")
        available = {
            i
            for i in available
            if sum(((i[a] - peak[a]) * Fraction(D[a])) ** 2 for a in range(3)) > Fraction(1, 4)
        }


def _qualify_profile_stability(center: F64, delta: Fraction, shape: tuple[int, int, int]) -> None:
    from simulation_optics_fixture import OracleInconclusive

    c = tuple(Fraction(float(v)) for v in center)
    a = Fraction(RADIUS)
    steps = tuple(Fraction(d) / 8 for d in D)
    ranges = [
        range(
            max(0, math.floor((v - a - delta) / s) - 1),
            min(n * 8, math.ceil((v + a + delta) / s) + 1),
        )
        for v, s, n in zip(c, steps, shape, strict=True)
    ]
    for index in itertools.product(*ranges):
        distances = [
            abs((Fraction(j) + Fraction(1, 2)) * s - v)
            for j, s, v in zip(index, steps, c, strict=True)
        ]
        lo = sum(max(Fraction(0), d - delta) ** 2 for d in distances)
        hi = sum((d + delta) ** 2 for d in distances)
        if lo <= a**2 < hi:
            raise OracleInconclusive("centroid roundoff enclosure straddles a source membership")


@lru_cache(maxsize=1)
def poll_range_qualification() -> dict[str, Any]:
    """Bound the fixed large-count fixture without any product-produced truth.

    Work in units of L=the represented float 2e151, so no observer square
    overflows. Exact rational Gaussian intervals prove peaks (0,0,1),
    (0,0,8),(0,0,15). Each centroid window has one positive sample: fewer
    than 64 ordinary operations give gamma64*max(box length) center error.
    Exact midpoint tests prove the entire enclosed center box has the same
    occupied set. Thus the immutable optical observer applies to every such
    represented initial center, not just one chosen reduction order.

    Enclose B_start/L using the positive unit peak, its certified reference
    error, the unit-response 1e-5 peak allowance, and division roundoff.
    Bound initial decoder variation by the same conservative ordinary-f64
    envelope used in assert_decoded. For |q|<2.5, k0>3, sqrt(k0^2-|q|^2)>1,
    kappa is 3-Lipschitz. With pi<4, |d|<=1/4 and y+x<2, the bounds below
    propagate carrier/phase/amplitude errors through the squared field and
    S normalization (S>=1/2). No special-function uncertainty is inferred
    from product output; optical node/Bessel/phase uncertainties stay intact.

    Use the TOTAL unilluminated peak upper bound once for each composed
    image's arithmetic allowance. Exact rational residual squares plus a
    gamma_(8M+64) reduction bound prove the initial direct sum is finite.
    At coordinate 9, positive sign, the brightness coordinate is 91. Even
    ignoring both other positive beads, one central residual square has a
    strict lower bound above maxfloat. Direct squares are mandated by section
    4, so a safe-final-ratio rearrangement cannot evade this required failure.
    """
    import image_only_calibration_pilot_fixture as reference
    from simulation_optics_fixture import OracleInconclusive

    values = poll_range_arguments()
    y, t = values["central_counts"], values["structured_counts"]
    scale = Fraction(2e151)
    peaks = ((0, 0, 1), (0, 0, 8), (0, 0, 15))
    _qualify_scaled_peaks(y, peaks)
    centers = np.array(
        [[0.0625, 0.05, 0.12], [0.0625, 0.05, 0.68], [0.0625, 0.05, inward_upper(16, D[2])]]
    )
    center_error = reference.gamma(64) * max(
        n * Fraction(d) for n, d in zip(RANGE_SHAPE, D, strict=True)
    )
    for center in centers:
        _qualify_profile_stability(center, center_error, RANGE_SHAPE)
    pi = math.pi
    gamma_coord = math.acos(1 / math.sqrt(3)) / (pi / 2)
    g, e = gamma_coord * (pi / 2), 0.5 * (pi / 2)
    amplitudes = np.array([math.cos(g), math.sin(g) * math.cos(e), math.sin(g) * math.sin(e)])
    angles = np.array([0, 1 / 3, 2 / 3]) * pi
    rho = (1.2 / 1.515) * (1.515 / 0.488)
    carriers = rho * np.stack([np.sin(angles), np.cos(angles)], axis=-1)
    phases = np.tile(np.array([0, 0.2, 0.4, 0.6, 0.8, 0.1, 0.3, 0.7, 0.9]) * (2 * pi), (3, 1))
    eps = Fraction(float(EPS))
    # Amplitudes include both the gamma initializer's admitted ordinary
    # roundoff and the separate decoder envelope. q/phases have fixed exact
    # initial normalized coordinates; their component bounds cover decoding.
    da, dq, dp = 256 * eps, 512 * eps, 1024 * eps
    k0 = Fraction(1.515) / Fraction(0.488)
    assert k0 > 3 and (Fraction(5, 2)) ** 2 < k0**2 - 1
    assert all(
        sum(Fraction(float(v)) ** 2 for v in q) < (Fraction(5, 2) - 2 * dq) ** 2 for q in carriers
    )
    norm = sum(Fraction(float(v)) ** 2 for v in amplitudes)
    dk = 3 * 2 * dq
    dalpha, dtheta = 2 * dk, 16 * dq + dp
    dfield, ds = 3 * da + 2 * dalpha + 4 * dtheta, 3 * (4 * da + da**2)
    assert norm - ds > Fraction(1, 2) and all(0 <= a < 2 for a in amplitudes)
    di = 24 * dfield + 144 * ds

    def outward(lo: Fraction, hi: Fraction) -> tuple[Fraction, Fraction]:
        grid = 2**80
        return Fraction(math.floor(lo * grid), grid), Fraction(math.ceil(hi * grid), grid)

    units, modulated, brightness = [], [], []
    for center, peak in zip(centers, peaks, strict=True):
        sites, count, _ = reference.unit_sites(tuple(float(v) for v in center), RANGE_SHAPE)
        weight = float(Fraction(1, count))
        unit = reference.optical_enclosure(
            sites,
            weight,
            RANGE_SHAPE,
            np.zeros((1, 2)),
            np.zeros((1, 1)),
            np.array([1.0, 0.0, 0.0]),
            128,
        )
        mod = reference.optical_enclosure(
            sites, weight, RANGE_SHAPE, carriers, phases, amplitudes, 128
        )
        maximum = Fraction(float(np.max(unit.values)))
        lo = (maximum - unit.radius) * Fraction(99999, 100000)
        hi = (maximum + unit.radius) * Fraction(100001, 100000)
        height = Fraction(float(y[peak])) / scale
        if lo <= 0:
            raise OracleInconclusive("positive initial unit peak is not separated")
        brightness.append(
            outward(height / hi * (1 - reference.gamma(8)), height / lo * (1 + reference.gamma(8)))
        )
        units.append(unit)
        modulated.append((mod, mod.radius + di * (maximum + unit.radius)))

    def prediction_interval(
        index: tuple[int, ...], structured: bool, multiplier: int = 1
    ) -> tuple[Fraction, Fraction]:
        lo = hi = Fraction(0)
        for b in range(3):
            ref, radius = modulated[b] if structured else (units[b], units[b].radius)
            value = Fraction(float(ref.values[index if structured else (0, 0, *index)]))
            mult_lo = mult_hi = Fraction(multiplier if b == 0 else 1)
            if b == 0 and multiplier != 1:
                mult_lo *= 1 - reference.gamma(2)
                mult_hi *= 1 + reference.gamma(2)
            lower, upper = outward(max(Fraction(0), value - radius), value + radius)
            lo += brightness[b][0] * mult_lo * lower
            hi += brightness[b][1] * mult_hi * upper
        return outward(lo, hi)

    total_peak_hi = max(prediction_interval(i, False)[1] for i in np.ndindex(RANGE_SHAPE))
    prediction_error = total_peak_hi / 100000
    squares = lower_squares = Fraction(0)
    for array, structured in ((y, False), (t, True)):
        for i in np.ndindex(array.shape):
            lo, hi = prediction_interval(i, structured)
            observation = Fraction(float(array[i])) / scale
            residual = max(
                abs(observation - lo + prediction_error), abs(observation - hi - prediction_error)
            )
            squares = outward(Fraction(0), squares + residual**2)[1]
            left, right = observation - hi - prediction_error, observation - lo + prediction_error
            if not left <= 0 <= right:
                lower_squares = outward(
                    lower_squares + min(abs(left), abs(right)) ** 2, Fraction(0)
                )[0]
    maxfloat = Fraction(float(np.finfo(np.float64).max))
    reduction = reference.gamma(8 * 28 * y.size + 64)
    initial_upper_ratio = squares * scale**2 * (1 + reduction) / maxfloat
    peak_index = tuple(
        int(v) for v in np.unravel_index(np.argmax(units[0].values[0, 0]), RANGE_SHAPE)
    )
    response_lo = Fraction(float(units[0].values[(0, 0, *peak_index)])) - units[0].radius
    trial_peak_hi = max(prediction_interval(i, False, 91)[1] for i in np.ndindex(RANGE_SHAPE))
    residual_lo = (
        91 * brightness[0][0] * (1 - reference.gamma(2)) * response_lo
        - trial_peak_hi / 100000
        - Fraction(float(y[peak_index])) / scale
    )
    square_lower_ratio = (residual_lo * scale) ** 2 * (1 - reference.gamma(8)) / maxfloat
    if not initial_upper_ratio < 1 or residual_lo <= 0 or not square_lower_ratio > 1:
        raise OracleInconclusive("poll direct-square range witness is not separated")
    return dict(
        initial_upper_ratio=initial_upper_ratio,
        square_lower_ratio=square_lower_ratio,
        centers=centers,
        center_error=center_error,
        brightness_intervals=tuple(brightness),
        initial_objective_scaled_interval=(
            lower_squares * (1 - reduction) / (2 * 28 * y.size),
            squares * (1 + reduction) / (2 * 28 * y.size),
        ),
        illumination_error=di,
        peak_index=peak_index,
    )


def improving_pair_arguments() -> dict[str, Any]:
    """Build the fixed image-only improving/incomplete-pair control."""
    central, _, _ = observations(shape=RANGE_SHAPE)
    structured = np.zeros((3, 9, *RANGE_SHAPE))
    structured[0, 7, 1, 0, 1] = float.fromhex("-0x1.fffffc0bfd3e0p+511")
    return arguments(
        central_counts=1e146 * ((central - 5) / 2),
        structured_counts=structured,
        heldout_counts=np.zeros((3, 5, *RANGE_SHAPE)),
        camera_estimate=camera(means_counts=np.zeros(3), contrast_counts=1),
        origin_um_zyx=(0, 0, 0),
        sweep_scales=(0.5,),
    )


@lru_cache(maxsize=1)
def improving_pair_qualification() -> dict[str, Any]:
    """Qualify the improving negative center trial before the positive failure.

    The fixed public B2 proposal is an input, not a certified expected result.
    Its literal negative observation is treated as an exact normalized float;
    no pixel selection, root approximation or observation retuning occurs here.
    This independent composition imports only the deployed frozen math helpers.

    Exact Gaussian intervals prove the central-data peak order. Each centroid
    window has one positive weight, so gamma64*max(box length) encloses its
    ordinary centroid error. Trial boxes add gamma4 for coordinate formation.
    Exact midpoint predicates prove stable source profiles for all three states.
    B_start/L intervals come ONLY from initial profiles and are fixed thereafter.

    The nominal decoder and a conservative analytic illumination perturbation
    enclose ordinary floating alternatives: |q|<2.5, k0>3, axial gap>1 makes
    kappa 3-Lipschitz; pi<4, |d|<=1/4, lateral-coordinate sum<2, beams<2 and
    S>=1/2 give the explicit field/S bounds below. Immutable node/weight,
    Bessel, phase and summation errors remain in each optical enclosure.

    Every intermediate reference interval is rounded OUTWARD to a 2^-80 grid.
    This caps rational denominators; it introduces no product tolerance. The
    exact rational sum of weighted intervals includes all component/assembly
    reference error. Each state's TOTAL unilluminated peak bounds its one
    1e-5*T product allowance. Final signed residual/squared-sum bounds include
    gamma_(8M+64), covering subtraction, direct squares, positive reductions
    and objective division with no prescribed reduction order. Assertions use
    disjoint intervals, never last-bit equality or a product-generated image.

    initial_upper<maxfloat proves initial direct arithmetic is representable;
    negative_upper<initial_lower proves an improving successful first poll;
    a positive single-square lower>maxfloat proves own range failure in the
    next score before paired selection. All three candidates are geometrically
    legal. OracleInconclusive blocks qualification if any proof fails.
    """
    import image_only_calibration_pilot_fixture as reference
    from simulation_optics_fixture import OracleInconclusive

    values = improving_pair_arguments()
    central, structured = values["central_counts"], values["structured_counts"]
    scale = Fraction(1e146)
    peaks = ((0, 0, 1), (0, 0, 8), (0, 0, 15))
    _qualify_scaled_peaks(central, peaks)
    centers = np.array(
        [[0.0625, 0.05, 0.12], [0.0625, 0.05, 0.68], [0.0625, 0.05, inward_upper(16, D[2])]]
    )
    lengths = tuple(n * Fraction(d) for n, d in zip(RANGE_SHAPE, D, strict=True))
    center_error = reference.gamma(64) * max(lengths)
    trial_error = center_error + reference.gamma(4) * max(lengths)
    command = [0, 0.2, 0.4, 0.6, 0.8, 0.1, 0.3, 0.7, 0.9]
    rho_coord = 1.2 / 1.515
    gamma_coord = math.acos(1 / math.sqrt(3)) / (math.pi / 2)
    tail = np.array(
        [
            1,
            1,
            1,
            gamma_coord,
            0.5,
            rho_coord,
            0,
            rho_coord,
            1 / 3,
            rho_coord,
            2 / 3,
            *np.tile(command, 3),
        ]
    )
    g, e = gamma_coord * (math.pi / 2), 0.5 * (math.pi / 2)
    amplitudes = np.array([math.cos(g), math.sin(g) * math.cos(e), math.sin(g) * math.sin(e)])
    angles = np.array([0, 1 / 3, 2 / 3]) * math.pi
    rho = rho_coord * (1.515 / 0.488)
    carriers = rho * np.stack([np.sin(angles), np.cos(angles)], axis=-1)
    phases = np.tile(np.array(command) * (2 * math.pi), (3, 1))
    eps = Fraction(float(EPS))
    da, dq, dp = 256 * eps, 512 * eps, 1024 * eps
    k0 = Fraction(1.515) / Fraction(0.488)
    assert k0 > 3 and Fraction(5, 2) ** 2 < k0**2 - 1
    assert all(
        sum(Fraction(float(v)) ** 2 for v in q) < (Fraction(5, 2) - 2 * dq) ** 2 for q in carriers
    )
    ds = 3 * (4 * da + da**2)
    assert sum(Fraction(float(v)) ** 2 for v in amplitudes) - ds > Fraction(1, 2)
    assert all(0 <= a < 2 for a in amplitudes)
    dfield = 3 * da + 2 * (12 * dq) + 4 * (16 * dq + dp)
    illumination_error = 24 * dfield + 144 * ds

    def outward(lo: Fraction, hi: Fraction) -> tuple[Fraction, Fraction]:
        grid = 2**80
        return Fraction(math.floor(lo * grid), grid), Fraction(math.ceil(hi * grid), grid)

    brightness = []
    for center, index in zip(centers, peaks, strict=True):
        _qualify_profile_stability(center, center_error, RANGE_SHAPE)
        sites, count, _ = reference.unit_sites(tuple(float(v) for v in center), RANGE_SHAPE)
        unit = reference.optical_enclosure(
            sites,
            float(Fraction(1, count)),
            RANGE_SHAPE,
            np.zeros((1, 2)),
            np.zeros((1, 1)),
            np.array([1.0, 0.0, 0.0]),
            128,
        )
        peak = Fraction(float(np.max(unit.values)))
        lower = (peak - unit.radius) * Fraction(99999, 100000)
        upper = (peak + unit.radius) * Fraction(100001, 100000)
        height = Fraction(float(central[index])) / scale
        if lower <= 0:
            raise OracleInconclusive("improving-pair initial unit peak is unresolved")
        brightness.append(
            outward(
                height / upper * (1 - reference.gamma(64)),
                height / lower * (1 + reference.gamma(64)),
            )
        )

    def image_intervals(c: F64) -> tuple[dict[Any, Any], dict[Any, Any], Fraction]:
        if not geometry_valid(c, RANGE_SHAPE):
            raise OracleInconclusive("improving-pair proposed center geometry is illegal")
        units, modulated = [], []
        for center in c:
            _qualify_profile_stability(center, trial_error, RANGE_SHAPE)
            sites, count, _ = reference.unit_sites(tuple(float(v) for v in center), RANGE_SHAPE)
            unit = reference.optical_enclosure(
                sites,
                float(Fraction(1, count)),
                RANGE_SHAPE,
                np.zeros((1, 2)),
                np.zeros((1, 1)),
                np.array([1.0, 0.0, 0.0]),
                128,
            )
            mod = reference.optical_enclosure(
                sites,
                float(Fraction(1, count)),
                RANGE_SHAPE,
                carriers,
                phases,
                amplitudes,
                128,
            )
            units.append((unit, unit.radius))
            peak_hi = Fraction(float(np.max(unit.values))) + unit.radius
            modulated.append((mod, mod.radius + illumination_error * peak_hi))
        images = []
        for refs, shape in ((units, RANGE_SHAPE), (modulated, (3, 9, *RANGE_SHAPE))):
            image = {}
            for i in np.ndindex(shape):
                lo = hi = Fraction(0)
                for (blo, bhi), (ref, error) in zip(brightness, refs, strict=True):
                    v = Fraction(
                        float(ref.values[(0, 0, *i)] if len(shape) == 3 else ref.values[i])
                    )
                    lower, upper = outward(max(Fraction(0), v - error), v + error)
                    lo += blo * lower
                    hi += bhi * upper
                image[i] = outward(lo, hi)
            images.append(image)
        total_peak = max(hi for _, hi in images[0].values())
        product_error = total_peak / 100000
        # Leave negative lower endpoints after the arithmetic allowance:
        # this conservative enclosure also admits tiny signed mean errors.
        for image in images:
            for i, (lo, hi) in image.items():
                image[i] = lo - product_error, hi + product_error
        return images[0], images[1], total_peak

    step = float((D[0] / 8) * 0.5)
    states, state_centers = [], []
    for sign in (0, -1, 1):
        c = centers.copy()
        c[0, 0] += sign * step
        state_centers.append(c)
        states.append(image_intervals(c))
    maxfloat = Fraction(float(np.finfo(np.float64).max))
    arithmetic = reference.gamma(8 * 28 * central.size + 64)

    def squared_sum_interval(state: Any) -> tuple[Fraction, Fraction]:
        lo_sum = hi_sum = Fraction(0)
        for array, refs in ((central, state[0]), (structured, state[1])):
            for i in np.ndindex(array.shape):
                lo, hi = refs[i]
                observation = Fraction(float(array[i]))
                left, right = observation - scale * hi, observation - scale * lo
                hi_sum += max(abs(left), abs(right)) ** 2
                if not left <= 0 <= right:
                    lo_sum += min(abs(left), abs(right)) ** 2
        return lo_sum * (1 - arithmetic) / maxfloat, hi_sum * (1 + arithmetic) / maxfloat

    initial = squared_sum_interval(states[0])
    negative = squared_sum_interval(states[1])
    index = (0, 7, 1, 0, 1)
    positive_prediction_lo = states[2][1][index][0]
    residual_lo = scale * positive_prediction_lo - Fraction(float(structured[index]))
    positive_square_lo = residual_lo**2 * (1 - reference.gamma(8)) / maxfloat
    if not (0 < negative[0] <= negative[1] < initial[0] <= initial[1] < 1):
        raise OracleInconclusive("improving-pair finite scores are not strictly separated")
    if residual_lo <= 0 or positive_square_lo <= 1:
        raise OracleInconclusive("improving-pair positive direct square is not unrepresentable")
    return dict(
        initial_sumsq_ratio=initial,
        negative_sumsq_ratio=negative,
        positive_square_lower_ratio=positive_square_lo,
        centers=tuple(state_centers),
        center_error=center_error,
        trial_center_error=trial_error,
        brightness_intervals=tuple(brightness),
        initial_tail=tail,
        pixel=index,
        prediction_scaled_intervals=tuple(state[1][index] for state in states),
        illumination_error=illumination_error,
        reference_grid=Fraction(1, 2**80),
    )


def inward_upper(n: int, spacing: float) -> float:
    exact = n * Fraction(spacing) - Fraction(RADIUS)
    represented = float(exact)
    return (
        float(np.nextafter(represented, -np.inf)) if Fraction(represented) > exact else represented
    )


def geometry_valid(centers: F64, shape: tuple[int, int, int]) -> bool:
    c = [[Fraction(float(v)) for v in row] for row in centers]
    radius = Fraction(RADIUS)
    if any(
        not radius <= c[b][a] <= shape[a] * Fraction(D[a]) - radius
        for b, a in itertools.product(range(3), range(3))
    ):
        return False
    return all(
        sum((c[b][a] - c[e][a]) ** 2 for a in range(3)) >= (2 * radius) ** 2
        for b, e in itertools.combinations(range(3), 2)
    )


def coordinate_bounds_valid(z: F64) -> bool:
    return (
        all(0 <= z[i] <= (100 if i < 12 else 1) for i in range(9, 15))
        and all((-1 if i % 2 else 0) <= z[i] <= 1 for i in range(15, 20))
        and all(-1 <= z[i] <= 1 for i in range(20, 47))
    )


@lru_cache(maxsize=512)
def occupied(center: tuple[float, ...], shape: tuple[int, int, int]) -> frozenset[tuple[int, ...]]:
    """Exact rational occupied INDEX set, including closed boundary ties."""
    c = tuple(Fraction(v) for v in center)
    steps = tuple(Fraction(d) / 8 for d in D)
    ranges = [
        range(
            max(0, math.floor((v - Fraction(RADIUS)) / s - Fraction(1, 2)) - 1),
            min(n * 8, math.ceil((v + Fraction(RADIUS)) / s) + 1),
        )
        for v, s, n in zip(c, steps, shape, strict=True)
    ]
    return frozenset(
        j
        for j in itertools.product(*ranges)
        if sum(
            ((Fraction(i) + Fraction(1, 2)) * s - v) ** 2
            for i, s, v in zip(j, steps, c, strict=True)
        )
        <= Fraction(RADIUS) ** 2
    )


def assert_array(value: Any, shape: tuple[int, ...]) -> None:
    assert type(value) is np.ndarray and value.shape == shape
    assert value.dtype == np.dtype(np.float64) and value.dtype.isnative
    assert value.flags.c_contiguous and value.flags.writeable
    assert np.isfinite(value).all()


def assert_same(left: Any, right: Any) -> None:
    """Equality of documented values only; no implementation introspection."""
    if isinstance(left, np.ndarray):
        np.testing.assert_array_equal(left, right)
    elif type(left) is tuple:
        assert type(right) is tuple and len(left) == len(right)
        for a, b in zip(left, right, strict=True):
            assert_same(a, b)
    elif type(left).__name__ in FIELDS:
        assert type(left) is type(right)
        for name in FIELDS[type(left).__name__]:
            assert_same(getattr(left, name), getattr(right, name))
    else:
        assert type(left) is type(right) and left == right


def output_arrays(value: Any) -> list[F64]:
    if isinstance(value, np.ndarray):
        return [value]
    if type(value) is tuple:
        return [a for item in value for a in output_arrays(item)]
    if type(value).__name__ in FIELDS:
        return [
            a for name in FIELDS[type(value).__name__] for a in output_arrays(getattr(value, name))
        ]
    return []


def assert_independent(*values: Any) -> None:
    arrays = [a for value in values for a in output_arrays(value)]
    for i, array in enumerate(arrays):
        assert all(not np.shares_memory(array, other) for other in arrays[i + 1 :])


def assert_candidate(candidate: Any, shape: tuple[int, int, int], pilot_type: type) -> None:
    assert type(candidate) is pilot_type
    for name, dims in (
        ("centers_um_zyx", (3, 3)),
        ("brightness_relative", (3,)),
        ("carriers_yx_per_um", (3, 2)),
        ("phases_rad", (3, 9)),
        ("beam_amplitudes", (3,)),
        ("stored_unit_masses_e", (3,)),
    ):
        assert_array(getattr(candidate, name), dims)
    assert geometry_valid(candidate.centers_um_zyx, shape)
    assert np.all(candidate.brightness_relative >= 0) and np.all(candidate.beam_amplitudes >= 0)
    assert np.count_nonzero(candidate.beam_amplitudes) >= 1
    assert type(candidate.occupied_counts) is tuple and len(candidate.occupied_counts) == 3
    for b, center in enumerate(candidate.centers_um_zyx):
        count = len(occupied(tuple(float(v) for v in center), shape))
        assert (
            type(candidate.occupied_counts[b]) is int and candidate.occupied_counts[b] == count > 0
        )
        # A correctly rounded one-electron cell weight, then exact stored mass rounded to f64.
        mass = float(count * Fraction(float(Fraction(1, count))))
        assert abs(candidate.stored_unit_masses_e[b] - mass) <= (count + 8) * EPS * mass
    k0 = Fraction(1.515) / Fraction(0.488)
    assert all(
        sum(Fraction(float(v)) ** 2 for v in row) <= k0**2 for row in candidate.carriers_yx_per_um
    )


@lru_cache(maxsize=4096)
def trig_enclosures(angle: float) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
    """Enclose sine/cosine independently for the decoder's |angle|<=pi<4.

    Sum rational Taylor terms through degrees 81/80. Lagrange's remainder is
    at most 4**82/82! for both series (the sine bound is smaller). All series
    arithmetic is exact. This is reference uncertainty, not a libm guess.
    """
    x = Fraction(angle)
    assert abs(x) < 4
    square, sine_term, cosine_term = x * x, x, Fraction(1)
    sine, cosine = sine_term, cosine_term
    for k in range(1, 41):
        sine_term *= -square / ((2 * k) * (2 * k + 1))
        cosine_term *= -square / ((2 * k - 1) * (2 * k))
        sine += sine_term
        cosine += cosine_term
    radius = Fraction(4**82, math.factorial(82))
    return (sine - radius, sine + radius), (cosine - radius, cosine + radius)


def interval_product(
    left: tuple[Fraction, Fraction], right: tuple[Fraction, Fraction]
) -> tuple[Fraction, Fraction]:
    products = [a * b for a in left for b in right]
    return min(products), max(products)


def assert_decoder_interval(
    value: float, interval: tuple[Fraction, Fraction], scale: float
) -> None:
    # 128 eps conservatively admits ordinary rounding at each of the few
    # prescribed decoder operations. The independently bounded reference
    # interval is separate. This is never an optical-image allowance.
    ordinary = Fraction(float(128 * EPS * scale))
    assert interval[0] - ordinary <= Fraction(float(value)) <= interval[1] + ordinary


def carrier_refusal_possible(z: F64, before: F64, index: int) -> bool:
    """Reject provably legal carrier refusals without a norm tolerance.

    Unchanged carriers use the actual legal pre-coordinate representation.
    Zero radius/angle gives an exactly known represented vector, including
    the rho=1, angle=0 legal positive. For nonzero angles the failed-attempt
    grammar exposes no q snapshot. A Taylor/ordinary-decoder enclosure can
    disprove an interior refusal, but straddling the exact norm boundary is
    only an observer limit, not proof that the refusal was justified. This
    residual non-axis boundary gap is disclosed for independent B/D review.
    """
    if not 14 <= index < 20 or z[index] == before[index]:
        return False
    o = (index - 14) // 2
    rho = float(z[14 + 2 * o] * (1.515 / 0.488))
    angle = float(z[15 + 2 * o] * math.pi)
    k0 = Fraction(1.515) / Fraction(0.488)
    if rho == 0 or angle == 0:
        return Fraction(rho) ** 2 > k0**2
    radius = 128 * Fraction(float(EPS)) * max(Fraction(1), abs(Fraction(rho)))
    upper_norm2 = Fraction(0)
    for interval in trig_enclosures(angle):
        lo, hi = interval_product((Fraction(rho), Fraction(rho)), interval)
        upper_norm2 += max(abs(lo - radius), abs(hi + radius)) ** 2
    return upper_norm2 > k0**2


def assert_decoded(z: F64, candidate: Any, brightness_start: F64) -> None:
    """Check decoder relations with independent trigonometric enclosures.

    Rational Taylor enclosures supply reference uncertainty. Comparisons
    separately allow 128 eps ordinary decoder roundoff. Exact endpoint zeros
    and multiplication/phase storage are asserted separately. Optical
    assertions use their own enclosures below.
    """
    assert coordinate_bounds_valid(z)
    np.testing.assert_array_equal(candidate.centers_um_zyx, z[:9].reshape(3, 3))
    np.testing.assert_array_equal(candidate.brightness_relative, z[9:12] * brightness_start)
    gamma, eta = z[12:14] * (math.pi / 2)
    sg, cg = trig_enclosures(float(gamma))
    se, ce = trig_enclosures(float(eta))
    beams = [cg, interval_product(sg, ce), interval_product(sg, se)]
    if z[12] == 0:
        beams[1:] = [(Fraction(0), Fraction(0))] * 2
    if z[12] == 1:
        beams[0] = (Fraction(0), Fraction(0))
    if z[13] == 0:
        beams[2] = (Fraction(0), Fraction(0))
    if z[13] == 1:
        beams[1] = (Fraction(0), Fraction(0))
    for index, interval in enumerate(beams):
        assert_decoder_interval(candidate.beam_amplitudes[index], interval, 1.0)
        if interval == (0, 0):
            assert candidate.beam_amplitudes[index] == 0
    for o in range(3):
        rho = z[14 + 2 * o] * (1.515 / 0.488)
        angle = z[15 + 2 * o] * math.pi
        for axis, interval in enumerate(trig_enclosures(float(angle))):
            q = interval_product((Fraction(float(rho)), Fraction(float(rho))), interval)
            assert_decoder_interval(candidate.carriers_yx_per_um[o, axis], q, max(1.0, abs(rho)))
    np.testing.assert_array_equal(candidate.phases_rad, z[20:].reshape(3, 9) * (2 * math.pi))


def parameter(candidate: Any, index: int) -> F64:
    if index < 9:
        return candidate.centers_um_zyx.reshape(-1)[index : index + 1]
    if index < 12:
        return candidate.brightness_relative[index - 9 : index - 8]
    if index < 14:
        return candidate.beam_amplitudes
    if index < 20:
        return candidate.carriers_yx_per_um[(index - 14) // 2]
    return candidate.phases_rad.reshape(-1)[index - 20 : index - 19]


def information(
    attempt: Any, base: Any, score: Any, shape: tuple[int, int, int]
) -> tuple[str, ...]:
    i, before, after = attempt.coordinate_index, base.candidate, score.candidate
    flags = [
        not attempt.coordinate_changed,
        not attempt.parameter_changed,
        False,
        False,
        False,
        False,
        False,
        score.objective == base.objective,
    ]
    if i < 9:
        b = i // 3
        flags[2] = occupied(tuple(float(v) for v in before.centers_um_zyx[b]), shape) == occupied(
            tuple(float(v) for v in after.centers_um_zyx[b]), shape
        )
        flags[3] = before.brightness_relative[b] == after.brightness_relative[b] == 0
    if i in (15, 17, 19):
        flags[4] = not np.any(before.carriers_yx_per_um[(i - 14) // 2]) and not np.any(
            after.carriers_yx_per_um[(i - 14) // 2]
        )
    if i >= 14:
        flags[5] = np.count_nonzero(before.beam_amplitudes) == 1
    if i < 9 or i >= 12:
        flags[6] = not np.any(before.brightness_relative) and not np.any(after.brightness_relative)
    return tuple(code for code, present in zip(CODE_ORDER, flags, strict=True) if present)


def assert_ledger(result: Any, module: Any, pilot_type: type) -> None:
    """Audit prescribed relations without pretending scores are numerical truth."""
    import scipy

    shape = result.detector_shape_zyx
    assert type(result) is module.BeadCalibrationResult
    assert type(shape) is tuple and len(shape) == 3 and all(type(n) is int for n in shape)
    assert type(result.origin_um_zyx) is tuple and all(
        type(v) is float for v in result.origin_um_zyx
    )
    assert type(result.scipy_version) is str and result.scipy_version == scipy.__version__
    assert type(result.camera_source) is str and result.camera_source.strip()
    assert type(result.blank_counts) is float and type(result.contrast_counts) is float
    assert type(result.sweep_scales) is tuple and all(
        type(s) is float and s > 0 for s in result.sweep_scales
    )
    assert type(result.message) is str and result.message.strip()
    assert result.status in (
        "completed_finite_fit",
        "normalization_unavailable",
        "initialization_failed",
        "numerical_incomplete",
    )
    assert result.stage in (
        "normalization",
        "initialization",
        "initial",
        "poll",
        "refinement_q256",
        "refinement_q512",
        "heldout_prediction",
        "heldout_residual",
        "complete",
    )
    assert result.failure_code in (
        None,
        "image_only_bead_calibration_range",
        "simulation_source_range",
        "simulation_optics_range",
        "image_only_calibration_pilot_range",
    )
    assert (result.failure_code is not None) == (result.status == "numerical_incomplete")
    assert type(result.objective_trace) is tuple and type(result.poll_attempts) is tuple
    assert type(result.coordinate_evidence) is tuple and len(result.coordinate_evidence) == 47
    assert type(result.unprobed_coordinates) is tuple
    if result.objective_trace:
        first = result.objective_trace[0]
        assert first.stage == "initial" and first.pupil_order == 128
        if result.initial_coordinates is not None:
            assert_same(first.coordinates, result.initial_coordinates)
        if first.outcome == "scored":
            assert_same(first.candidate, result.initial_candidate)
    for prefix in ("initial", "best", "frozen"):
        candidate, coords = (
            getattr(result, prefix + "_candidate"),
            getattr(result, prefix + "_coordinates"),
        )
        assert (candidate is None) == (coords is None)
        if candidate is not None:
            assert_candidate(candidate, shape, pilot_type)
            assert_array(coords, (47,))
            assert_decoded(coords, candidate, result.initial_candidate.brightness_relative)
    for name in ("best_score_index", "incumbent_score_index"):
        value = getattr(result, name)
        assert value is None or type(value) is int
    for score in result.objective_trace:
        assert type(score) is module.BeadCalibrationScore
        assert score.stage in ("initial", "poll", "refinement")
        assert type(score.pupil_order) is int and score.pupil_order in (128, 256, 512)
        assert score.outcome in ("scored", "numerical_incomplete")
        if score.coordinates is not None:
            assert_array(score.coordinates, (47,))
        if score.outcome == "scored":
            assert (
                type(score.objective) is float
                and math.isfinite(score.objective)
                and score.objective >= 0
            )
            assert score.failure_code is None and score.coordinates is not None
            assert_candidate(score.candidate, shape, pilot_type)
            assert_decoded(
                score.coordinates, score.candidate, result.initial_candidate.brightness_relative
            )
        else:
            assert score.candidate is None and score.objective is None
            assert score.failure_code == result.failure_code
    successful = [
        (i, s)
        for i, s in enumerate(result.objective_trace)
        if s.outcome == "scored" and s.pupil_order == 128
    ]
    if successful:
        best_index, best = min(successful, key=lambda entry: entry[1].objective)
        assert result.best_score_index == best_index
        assert_same(result.best_candidate, best.candidate)
        assert_same(result.best_coordinates, best.coordinates)
    else:
        assert result.best_score_index is result.best_candidate is result.best_coordinates is None
        assert result.incumbent_score_index is None
    incumbent = 0 if successful else None
    next_score = 1
    completed_pairs = 0
    for pair_start in range(0, len(result.poll_attempts), 2):
        pair = result.poll_attempts[pair_start : pair_start + 2]
        pair_complete = len(pair) == 2 and all(a.selected is not None for a in pair)
        for offset, attempt in enumerate(pair):
            ordinal = pair_start + offset
            assert type(attempt) is module.BeadCalibrationAttempt
            expected_sweep, remainder = divmod(ordinal, 94)
            expected_coordinate, expected_sign = remainder // 2, (-1, 1)[remainder % 2]
            for name, value in (
                ("sweep_index", expected_sweep),
                ("coordinate_index", expected_coordinate),
                ("sign", expected_sign),
                ("base_score_index", incumbent),
            ):
                assert type(getattr(attempt, name)) is int and getattr(attempt, name) == value
            base = result.objective_trace[attempt.base_score_index]
            assert base.outcome == "scored" and base.pupil_order == 128
            if attempt.trial_coordinates is not None:
                assert_array(attempt.trial_coordinates, (47,))
                expected = base.coordinates.copy()
                expected[expected_coordinate] += expected_sign * float(
                    BASE_STEPS[expected_coordinate] * result.sweep_scales[expected_sweep]
                )
                np.testing.assert_array_equal(attempt.trial_coordinates, expected)
                assert type(attempt.coordinate_changed) is bool
                assert attempt.coordinate_changed == bool(
                    expected[expected_coordinate] != base.coordinates[expected_coordinate]
                )
            else:
                assert attempt.coordinate_changed is None
                assert attempt.outcome == "numerical_incomplete" and attempt.score_index is None
            assert attempt.outcome in ("scored", "infeasible", "numerical_incomplete")
            assert type(attempt.information_codes) is tuple
            assert attempt.selected is None or type(attempt.selected) is bool
            if attempt.outcome == "infeasible":
                assert attempt.trial_coordinates is not None
                z = attempt.trial_coordinates
                if not coordinate_bounds_valid(z):
                    assert attempt.infeasibility_reason == "coordinate_bounds"
                elif not geometry_valid(z[:9].reshape(3, 3), shape):
                    assert attempt.infeasibility_reason == "center_geometry"
                else:
                    assert attempt.infeasibility_reason == "carrier_domain"
                    assert carrier_refusal_possible(z, base.coordinates, expected_coordinate)
                assert (
                    attempt.score_index is attempt.parameter_changed is attempt.failure_code is None
                )
                assert attempt.information_codes == ()
            else:
                assert attempt.infeasibility_reason is None
                if attempt.score_index is not None:
                    assert type(attempt.score_index) is int and attempt.score_index == next_score
                    score = result.objective_trace[next_score]
                    next_score += 1
                    assert score.stage == "poll" and score.pupil_order == 128
                    assert score.outcome == attempt.outcome
                    assert_same(score.coordinates, attempt.trial_coordinates)
                if attempt.outcome == "scored":
                    assert type(attempt.score_index) is int
                    score = result.objective_trace[attempt.score_index]
                    assert attempt.failure_code is None and type(attempt.parameter_changed) is bool
                    assert attempt.parameter_changed == bool(
                        not np.array_equal(
                            parameter(base.candidate, expected_coordinate),
                            parameter(score.candidate, expected_coordinate),
                        )
                    )
                    assert attempt.information_codes == information(attempt, base, score, shape)
                else:
                    assert ordinal == len(result.poll_attempts) - 1
                    assert attempt.parameter_changed is None and attempt.information_codes == ()
                    assert attempt.failure_code == result.failure_code and result.stage == "poll"
        if pair_complete:
            assert incumbent is not None
            completed_pairs += 1
            improving = [
                a
                for a in pair
                if a.outcome == "scored"
                and result.objective_trace[a.score_index].objective
                < result.objective_trace[incumbent].objective
            ]
            selected = (
                min(improving, key=lambda a: result.objective_trace[a.score_index].objective)
                if improving
                else None
            )
            for attempt in pair:
                assert attempt.selected is (attempt is selected)
            if selected is not None:
                incumbent = selected.score_index
        else:
            assert pair_start + len(pair) == len(result.poll_attempts)
            assert all(a.selected is None for a in pair)
    assert result.incumbent_score_index == incumbent
    # Every score after initialization belongs to its actual poll attempt or
    # one of the two ordered rescores. No orphan/retried score is fabricated.
    if result.objective_trace:
        assert all(s.stage == "refinement" for s in result.objective_trace[next_score:])
    else:
        assert result.poll_attempts == ()
    failed_scores = [s for s in result.objective_trace if s.outcome == "numerical_incomplete"]
    assert len(failed_scores) <= 1
    if failed_scores:
        failed = failed_scores[0]
        assert failed is result.objective_trace[-1]
        expected_stage = (
            "refinement_q" + str(failed.pupil_order)
            if failed.stage == "refinement"
            else failed.stage
        )
        assert result.status == "numerical_incomplete" and result.stage == expected_stage
    unprobed = []
    for i, evidence in enumerate(result.coordinate_evidence):
        assert type(evidence) is module.BeadCoordinateEvidence
        attempts = [a for a in result.poll_attempts if a.coordinate_index == i]
        scored = [a for a in attempts if a.outcome == "scored"]
        expected_counts = (
            i,
            len(attempts),
            len(scored),
            sum(a.coordinate_changed for a in scored),
            sum(a.parameter_changed for a in scored),
            sum(a.selected is True for a in attempts),
        )
        for name, value in zip(FIELDS["BeadCoordinateEvidence"][:-1], expected_counts, strict=True):
            assert type(getattr(evidence, name)) is int and getattr(evidence, name) == value
        assert evidence.information_codes == tuple(
            c for c in CODE_ORDER if any(c in a.information_codes for a in scored)
        )
        if not expected_counts[4]:
            unprobed.append(i)
    assert result.unprobed_coordinates == tuple(unprobed)
    counts = (
        94 * len(result.sweep_scales),
        len(result.poll_attempts),
        sum(a.outcome == "scored" for a in result.poll_attempts),
        sum(a.outcome == "infeasible" for a in result.poll_attempts),
        sum(a.outcome == "numerical_incomplete" for a in result.poll_attempts),
        completed_pairs,
        completed_pairs // 47,
        len(result.objective_trace),
        sum(s.outcome == "scored" for s in result.objective_trace),
    )
    assert type(result.counts) is module.BeadCalibrationCounts
    for name, expected_count in zip(FIELDS["BeadCalibrationCounts"], counts, strict=True):
        assert (
            type(getattr(result.counts, name)) is int
            and getattr(result.counts, name) == expected_count
        )
    objectives = result.training_objectives_q128_q256_q512
    assert type(objectives) is tuple and len(objectives) == 3
    for value in objectives:
        assert value is None or (type(value) is float and math.isfinite(value) and value >= 0)
    assert objectives[0] == (min(s.objective for _, s in successful) if successful else None)
    refinements = [s for s in result.objective_trace if s.stage == "refinement"]
    if refinements:
        assert result.frozen_candidate is not None
        assert completed_pairs == 47 * len(result.sweep_scales)
    assert [s.pupil_order for s in refinements] == [256, 512][: len(refinements)]
    if refinements:
        assert all(s.stage == "refinement" for s in result.objective_trace[-len(refinements) :])
    for j, score in enumerate(refinements, 1):
        assert_same(score.coordinates, result.frozen_coordinates)
        assert objectives[j] == score.objective
        if score.outcome == "scored":
            assert_same(score.candidate, result.frozen_candidate)
    for j in range(len(refinements) + 1, 3):
        assert objectives[j] is None
    if result.frozen_candidate is not None:
        assert incumbent is not None
        assert completed_pairs == 47 * len(result.sweep_scales)
        assert_same(result.frozen_candidate, result.objective_trace[incumbent].candidate)
        assert_same(result.frozen_coordinates, result.objective_trace[incumbent].coordinates)
    if result.heldout_prediction is not None:
        assert_array(result.heldout_prediction, (3, 5, *shape))
        assert np.all(result.heldout_prediction >= 0)
    assert (result.heldout_residual_mean is None) == (result.heldout_residual_rms is None)
    if result.heldout_residual_mean is not None:
        assert_array(result.heldout_residual_mean, (3, 5))
        assert_array(result.heldout_residual_rms, (3, 5))
        assert np.all(result.heldout_residual_rms >= 0)
    if result.status == "completed_finite_fit":
        assert result.stage == "complete" and result.frozen_candidate is not None
        assert result.heldout_prediction is not None and result.heldout_residual_mean is not None
        assert len(result.poll_attempts) == 94 * len(result.sweep_scales)
        assert len(result.objective_trace) == result.counts.scored_polls + 3
        assert [s.stage for s in result.objective_trace] == ["initial"] + [
            "poll"
        ] * result.counts.scored_polls + ["refinement"] * 2
    elif result.stage in ("normalization", "initialization"):
        assert result.initial_candidate is result.best_candidate is result.frozen_candidate is None
        assert (
            result.initial_coordinates
            is result.best_coordinates
            is result.frozen_coordinates
            is None
        )
        assert result.objective_trace == result.poll_attempts == ()
    elif result.stage in ("initial", "poll"):
        assert result.frozen_candidate is None and result.frozen_coordinates is None
    if result.stage not in ("complete", "heldout_residual"):
        assert result.heldout_prediction is None
    if result.status != "completed_finite_fit":
        assert result.heldout_residual_mean is result.heldout_residual_rms is None


def finite_predictions(
    candidate: Any, shape: tuple[int, int, int], order: int
) -> tuple[F64, F64, Any]:
    """Compose TOTAL-image peak and component/assembly uncertainty.

    Use only the three immutable, matching, coordinator-bound math helpers.
    No old allowance (sum of object peaks) or old search observer is reused.
    The helper itself rejects sites>1024, shape>(9,5,16), |phase|>8, unsupported
    Q, illegal exact carriers, norm outside [1/4,32], J0 arguments>24 or cis
    arguments>128. OracleInconclusive propagates and blocks evidence.
    """
    import image_only_calibration_pilot_fixture as reference

    central = np.zeros(shape)
    structured = np.zeros((3, 9, *shape))
    ru = rs = magnitude_u = magnitude_s = Fraction(0)
    for center, brightness in zip(
        candidate.centers_um_zyx, candidate.brightness_relative, strict=True
    ):
        b = Fraction(float(brightness))
        if not b:
            continue
        sites, count, _ = reference.unit_sites(tuple(float(v) for v in center), shape)
        weight = float(Fraction(1, count))
        unit = reference.optical_enclosure(
            sites,
            weight,
            shape,
            np.zeros((1, 2)),
            np.zeros((1, 1)),
            np.array([1.0, 0.0, 0.0]),
            order,
        )
        modulated = reference.optical_enclosure(
            sites,
            weight,
            shape,
            candidate.carriers_yx_per_um,
            candidate.phases_rad,
            candidate.beam_amplitudes,
            order,
        )
        central += float(b) * unit.values[0, 0]
        structured += float(b) * modulated.values
        ru += b * unit.radius
        rs += b * modulated.radius
        magnitude_u += b * max(abs(Fraction(float(v))) for v in unit.values.flat)
        magnitude_s += b * max(abs(Fraction(float(v))) for v in modulated.values.flat)
    # Three products and sums plus observer composition: gamma8 bounds all,
    # with additive underflow errors. Include both central and modulated sums.
    ru += reference.gamma(8) * magnitude_u + (32 * reference.TINY if magnitude_u else 0)
    rs += reference.gamma(8) * magnitude_s + (32 * reference.TINY if magnitude_s else 0)
    peak = Fraction(float(np.max(central)))
    bound = reference.PredictionAllowance(
        max(Fraction(0), peak - ru) / 100000, (peak + ru) / 100000, max(ru, rs)
    )
    return central, structured, bound


def assert_finite_score(score: Any, inputs: dict[str, Any]) -> tuple[F64, F64, Any]:
    """Check full loss and return its independent reference for local reuse."""
    import image_only_calibration_pilot_fixture as reference

    central, structured, bound = finite_predictions(
        score.candidate, inputs["central_counts"].shape, score.pupil_order
    )
    b, d = inputs["camera_estimate"].means_counts[1], inputs["camera_estimate"].contrast_counts
    y = (inputs["central_counts"] - b) / d
    training = (inputs["structured_counts"] - b) / d
    expected = reference.objective(y, training, central, structured)
    allowance = reference.loss_allowance(y, training, central, structured, bound)
    reference.assert_scalar_close(score.objective, expected, allowance)
    return central, structured, bound


def assert_initial_brightness(candidate: Any, maxima: F64, shape: tuple[int, int, int]) -> None:
    import image_only_calibration_pilot_fixture as reference

    for center, height, brightness in zip(
        candidate.centers_um_zyx, maxima, candidate.brightness_relative, strict=True
    ):
        sites, count, _ = reference.unit_sites(tuple(float(v) for v in center), shape)
        response = reference.optical_enclosure(
            sites,
            float(Fraction(1, count)),
            shape,
            np.zeros((1, 2)),
            np.zeros((1, 1)),
            np.array([1.0, 0.0, 0.0]),
            128,
        )
        peak = Fraction(float(np.max(response.values)))
        lo = (peak - response.radius) * Fraction(99999, 100000)
        hi = (peak + response.radius) * Fraction(100001, 100000)
        assert lo > 0
        rounding = reference.gamma(8)
        assert Fraction(float(height)) / hi * (1 - rounding) <= Fraction(float(brightness))
        assert Fraction(float(brightness)) <= Fraction(float(height)) / lo * (1 + rounding)
