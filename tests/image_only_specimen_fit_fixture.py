"""Blind A1 mathematical controls and obligation ledger, contract v1.

Authority: public-bundle/public/docs/contracts/image-only-specimen-fit-v1.md,
SHA256 5523bbe67838c42a23b365f2da9bae0932d011c16fa7b0196b8209a48cdc7c32.
The following map precedes test design. IDs name distinct obligations; parameter
rows within an ID are examples unless they select a different decision. No old
test/helper, implementation, coverage report or runtime numerical answer is an
expectation source. All calls use the actual public fit boundary.

SF01 boundary: binding tests reject omitted/extra/positional-only misuse and
truth/cache/pilot/callback inputs. Fixed-model/geometry result metadata protects
the declared conditional model. Origin-label invariance
protects once-only driver transfer; unequal beams, nonzero signed carriers and
unwrapped phases protect the passed gauge. Provenance labels are preserved, not
authenticated. No test proves arrays came from images or that a driver transferred
phases once. Purity/import exclusion and no hidden calibration need D inspection.

SF02 representation: raw rejection/positive-layout and metadata rejection/layout
tests cover exact plain/native float64, dimensions, finite values, independent
owned writable C snapshots, untouched caller storage/flags. Camera subclass is
legal, unconsumed fields deliberately meaningless. Metadata mutation after return
and two independent returns protect ownership. Raw borrowing, absence of an
unconditional payload copy and concurrent mutation are not inferred from equality.

SF03 validation: every group has invalid controls with d<=0; pairwise precedence
uses one invalid representative per group. Within-array representation/shape/value
precedence has no separately selected diagnostic order. Missing/wrong camera is
invalid. Nonpositive d retains metadata without deriving half-spacing or doing
work. Positive d with gain=None must fit; means need not agree with supplied d.

SF04 units/loss: exact-integer doubled source geometry, half-spacing and fixed
constants; zero-candidate signed loss uses independent Decimal arithmetic on all
15*Z*Y*X raw samples, including an isolated last pixel. Blank is means[1], never
dark or gain. Initial score/gradient and nonzero controls protect normalization by
M/N and no intercept/volume factor on the selected one-pixel control. Its physical
Q1 reference includes separate builder/application allowances. General nonzero
cache-defined loss and supplied-phase accuracy remain unproved; origin invariance
alone cannot prove phase accuracy. No continuum-resolution claim.

SF05 arithmetic: Decimal exact represented-value references for signed subtraction,
mean, RMS and normalized squared loss. Examples cover C-b overflow with finite Y,
raw residual-square/signed-sum overflow with finite final targets, finite underflow,
unrepresentable observation and normalized data objective. Failures must follow
penalty, then per-orientation observation/forward/residual/mean/RMS, then data/total.
The returned best penalty is checked independently against its represented source.
Remaining adversarial reachability gaps:
penalty/total/residual/mean/RMS final-range failures and large exact indexing limits.

SF06 gradient: initial trace/order plus physical first-step bounds protect a small
composition. Tiny residual32 underflow has a zero-gradient control. Float64
residual beyond float32 range retains full initial score and no partial gradient.
Exact real public residual arguments, general assembled gradient and recomputation
need a transparent public-dependency observer; its import path is missing from the
allowed contract. No observer is claimed here. Gradient accumulation
overflow/underflow at a later candidate remains a risk for B/D.

SF07 initial: zero candidate, score immediately best, separate gradient. All-zero
and negative observations under a positive one-pixel kernel exercise no direction;
tiny residual32 underflow gives zero approximate gradient without a convergence
claim. Complete initial call order and exact counts are independently prescribed.

SF08 seed: independent physical first-step intervals bound the seed using
v=RN32(max(0,-g)/max(max(0,-g))); counts require three additional forwards,
candidate identity 0 and seed completion. Tiny dyadic regularization is legal.
Actual direction arguments, nonuniform seed ratios, unsafe-but-representable raw
ratios and genuine seed failure need further public controls. No arbitrary seed
cap, injected inverse return or convergence claim is adopted.

SF09 projection: the first physical-step interval and a tiny-step stagnation
control cover finite projection/rounding and nonzero PG with exact-zero trial.
General PG accuracy, legal nonzero subnormal projection, negative overflow
projection, positive overflow/unscored trial and values just above float32 max
rounding back to finite max lack qualified witnesses. These are B omissions.

SF10 selection: trace relations check strict reported-total comparison, first
acceptance, no rejected gradient, nonincreasing carried steps, halving, bounds and
final unused gradient whenever reached. This alone does not independently prove
score numerical accuracy. First-iteration acceptance and exact float32 stagnation
have physical witnesses. Ties, rejected trials, carried steps and backtracking
exhaustion lack demonstrated witnesses; no outcome-deciding mock is substituted.

SF11 halving: relational trace verifies every entered retry uses prior step/2;
no unused halving/zero step is demanded after trial bound. Required-step underflow
and distinction from zero-step stagnation lack a reachable qualified witness.

SF12 retention: independently select strictly improving complete observed scores;
best/initial/last-gradient identities and gradient_state cannot be relabeled.
Initial residual32 failure proves score-first retention. Later gradient failure,
late trial-score failure and retained rejected score need reachable witnesses.

SF13 grammar: all six public record types, required fields, native Python scalar/tuple
grammar, frozen bindings, scalar finiteness and exact status/stage/code/component
for reached outcomes. Every returned trace entry has one finalized candidate;
no incomplete score/gradient. Exact absence of extra fields/volume archives is
not proved by required-attribute checks. Real allocation failures,
interruptions, unrelated dependency errors/warnings and recognized inverse range
need qualified real-boundary witnesses or independent D review; no injected
outcome supplies optimizer correctness. Numerical messages need nonblank stage
information, without an exact-prose oracle. Invalid/binding exceptions preserve
callers and policies. Record constructors are not authenticity certificates.

SF14 calls/storage: trace order/purpose/identity and complete/partial counters are
checked against independently prescribed small-case counts and trace relations.
The unavailable public import path blocks the independent entered-call observer;
honest traces themselves are not independent actual-entry proof. No large-memory
bound is claimed. Owned C float32 best and independent outputs protect
public storage. One orientation at a time, no hidden prediction/residual archive,
two-source lifetime/reuse and absence of gratuitous copies require D inspection
and coordinator resource studies. No full-size workload is authorized here.

Delivery: behavior coverage with independent risk review; no percentage selected.
Fresh B reviews every helper/tolerance/use and the omissions. Narrow checks only, unavailable
operation is not red. Full-local/platform/report/resource gates belong to root.

For each keeper the four authoring answers are: (1) obligation above; (2) named
credible wrong result above; (3) accepted camera/inverse boundary proof does not
exercise this new composition; (4) actual fit plus public dependencies, no extra
production export/seam. Decimal references use exact float input values and 1600
digits, enough for products spanning binary64's exponent range. Reduction checks
allow ordinary binary64 roundoff, not inverse error. Physical first-step intervals
use 2e-4+1e-8 from the separate inverse component bounds, plus explicit reference
uncertainty and RN32 error. No general optimizer allowance follows.
This ledger is an omission disclosure, not an A completeness certification.

Keeper index (test_ prefix omitted; assert_protocol is shared by every returned
control, assert_initial_score by every complete initial numerical control):
SF01: missing_required_argument_is_python_binding_error,
extra_truth_or_configuration_channel_is_binding_error, settings_are_keyword_only,
full_signed_tail_loss_and_fixed_geometry,
origin_is_only_a_label_and_supplied_phases_are_not_transferred.
SF02: invalid_group_even_with_unavailable_normalization,
camera_consumed_field_grammar, valid_raw_and_metadata_layouts_are_preserved,
metadata_snapshot_and_cross_call_independence.
SF03: validation_group_order, nonpositive_contrast_is_metadata_only,
camera_subclass_and_unconsumed_fields_are_legal.
SF04: full_signed_tail_loss_and_fixed_geometry,
independent_one_pixel_first_step_units_and_seed, assert_protocol penalty relation.
SF05: subtraction_overflow_with_finite_normalized_observation,
raw_square_overflow_still_has_complete_score,
required_data_objective_range_after_safe_means_and_rms,
unrepresentable_observation_fails_before_its_forward.
SF06/SF12: residual32_failure_retains_complete_initial_score,
raw_square_overflow_still_has_complete_score, assert_protocol identities.
SF07: initial_zero_and_no_approximate_projected_direction.
SF08/SF10: independent_one_pixel_first_step_units_and_seed, assert_protocol.
SF09: large_regularization_can_round_trial_to_zero_without_convergence_claim.
SF11: assert_protocol only; required-underflow witness absent.
SF13: derived_half_spacing_underflow_is_geometry_failure,
reached_record_bindings_are_frozen, assert_protocol,
caller_arrays_and_global_policies_survive_success_or_invalid_input.
SF14: initial_zero_and_no_approximate_projected_direction plus exact partial-count
assertions in residual32/observation/data-range controls; observer gap above.
Positive boundary examples: legal_beam_scales_and_repeated_signed_carriers.
Unsupported memmap positives/negative type, exact field absence, exception/warning
propagation, source/prediction lifetimes and the stated nonzero failure/protocol
gaps remain explicit for fresh B. This is a partial proposed checkpoint, not ready
for C; no omissions are silently delegated to a percentage metric.
"""

from __future__ import annotations

import importlib
import math
import warnings
import weakref
from collections.abc import Iterator
from contextlib import contextmanager
from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Any

import numpy as np

# A2 extension ledger. This supersedes the A1 missing-import/observer and partial
# checkpoint statements above; the A1 keepers and charges are retained.
#
# Prior partial checkpoint: f56a60b954380e8edb195d82b1ad211e3402100d72ce117c3aa53b769849b939.
# No B acceptance exists. Every new control exercises fit_specimen, with public
# inverse operations wrapped at their documented import boundary. Reloading the
# fit after installing wrappers binds either ordinary import spelling; there is
# no inspection/patching of fit internals. Successful calls always execute the
# original inverse and return its actual output unchanged. Exception/warning
# sentinels test propagation only; they never supply a successful numeric result
# or choose a step, score, gradient, trial, or optimizer outcome.
#
# SF01/SF04: observed_public_composition_and_rounded_protocol checks every cache
# and orientation argument, no added origin/phase transfer, fixed synthetic
# model, native residual32 and source32. Independent finite represented-cache
# matrices check its nonuniform signed-carrier/unequal-beam public calls. All
# required lags are used; no builder coefficients/free padding are prescribed.
# The zero-padding choice in the old fixture is not used. Exact cache inversion
# is qualified only for transform periods 4/8. New shape (1,4,4), Q=1 and moderate
# phases are inside that domain. Matrix arithmetic uncertainty is conservatively
# 256*eps64 of the relevant norm scale, separate from application allowance 1e-4.
# Existing accepted inverse boundary proves dependencies, not fit argument flow.
#
# SF05/SF06/SF08/SF09/SF10: the same observer independently reduces the REAL
# returned score forwards/gradient adjoints/seed forwards with Decimal. This
# proves the specified arithmetic composition, not those calls' own accuracy;
# separate cache-matrix inequalities supply the latter for this tiny example.
# Residual32 is exact RN32 of the gradient pass's own float64 prediction minus
# signed observation. Gradient = summed real adjoint outputs/M + lambda*x/N;
# seed = norm(v)^2/(sum(real seed outputs^2)/M+lambda*norm(v)^2/N).
# Source32 projection uses ordinary RN64 multiply/subtract then RN32, never an
# inverse allowance. PG uses exact-real component formula, finite-reduction
# allowance 256*eps64. Candidate buffer snapshots here are TEST observations,
# not permitted production archives. Trace order is compared with actual entries.
# Plausible wrong outcomes: combined score/gradient pass, old residual reused,
# float64 residual silently sent to adjoint, no seed forwards, wrong orientation,
# hidden scale, clipping, premature float32 gradient, increasing carried step,
# gradient allocated for rejected/final candidates, fabricated entered-call trace.
#
# SF09/SF10/SF12: qualified_large_signal_retention uses m=3*2**126, one -m
# and fourteen +m, Q1 central-only. Independently evaluated physical coefficient
# a=0.12790161839307201 (the existing Decimal/Bessel reference). Put
# eta=2e-4+1e-8+1e-13 and e=2**-23,
# vmin=(13/15-eta)/(13/15+eta)*(1-e).
# Each initial gradient magnitude/m lies in a*(13/15 +/- eta). The physical
# seed bounds in first_step_bounds include both inverse budgets, direction RN32,
# ordinary reduction uncertainty and small reference uncertainty. Conservative
# rounded intervals (checked by test_reference_large_signal_margins) are:
# first x/f32max in (1.26,1.28), half-step x/f32max in (.63,.64),
# half-step prediction/m in (.43,.44), negative-observation residual/f32max>1.07,
# Jhalf/m^2<.23 versus Jzero/m^2=.5. Bounds remain well clear of all decisions.
# Trial1 is unscored unrepresentable; trial2 is first accepted. With one trial
# the procedure ends backtracking_limit, with two trials/one iteration it ends
# iteration_limit without unused gradient, with two iterations it preserves
# candidate2 after trial-gradient residual32 failure. No mocked math supplies
# these outcomes. rounded_subnormal_trial additionally exercises nonzero finite
# float32 underflow (not rounded all-zero stagnation).
#
# SF13/SF14: dependency_range_partial_trace exercises every surrounding call
# stage with one public-boundary range exception. All earlier successful math is
# real. It proves exact partial call counts, stage, original code, complete-score
# retention and old gradient identity; it does not prove natural inverse range
# reachability. unrelated_dependency_failures_preserve_identity and
# backend_warning_policy_is_preserved cover unrelated public errors, MemoryError,
# interruption and warnings, including caller state/policy on propagation.
# Observer source/output weak references check release on return and bounded
# observed live payloads; lifetime assertion permits the previous assignment's
# output until replacement, with at most two orientation payloads. It cannot see
# unseen copies, raw snapshots or temporary backend allocations. Those exact
# storage/copy obligations and import/I/O/purity exclusions remain D inspection
# plus coordinator resource evidence; no portable peak-memory claim follows.
# Memmap subclass rejection/plain-view acceptance use the same actual buffer and
# preserve caller state; the file is under pytest's owned tmp_path, not runtime I/O.
#
# Explicit risk dispositions (not silently covered or declared impossible):
# R1 SF05: if finite r exists, mean and RMS are <=max(abs(r)); hence a final
# mean/RMS overflow cannot be reached from finite r. A failure of either on finite
# r is a product defect, not a legitimate numerical status. Initial penalty=0.
# At initial zero, residual=-finite observation, penalty=0, and a finite data
# objective plus zero cannot fail at total. Once the initial gradient completes,
# every normalized observation has a finite RN32 conversion. Its magnitude is
# then below 2**129, whereas DBL_MAX's overflow-midpoint gap is 2**970. Adding
# such an observation to any finite prediction cannot overflow the RN64 residual.
# The unchanged normalization cannot newly fail later without external mutation
# (outside the promise). These are conditional protocol invariants, not injected
# failure obligations. Late penalty/total/data-objective/gradient range remains
# for D numerical review; no robust natural witness is supplied for those labels.
# Safe huge initial means/RMS/data and late residual32 are concrete keepers.
# R2 SF08: exact seed denominator >=lambda*||v||^2/N and >0, so 0<t<=N/lambda.
# RN32 v has an exact 1. Any zero/nonfinite ratio needs genuine represented-range
# obstruction, not a direction norm overflow or step cap. Tiny geometry may
# underflow represented optical curvature; a universal seed-success claim is
# NOT made. tiny_curvature_seed_range_and_finite_ratio supplies a natural
# seed-range witness: lateral spacing 2**-521 gives coefficient ~1.896e-312,
# nonzero initial gradient and optical curvature O(1e-623). With lambda=2**-1000
# the ratio is finite near 2**1002; with lambda=2**-1074 it exceeds DBL_MAX.
# The Q1 near-axis Bessel series differs from its peak by <1e-300 relatively;
# inherited inverse bounds do not change either decision. Real public inverse
# calls at this geometry were qualified successfully. No step cap is permitted.
# D reviews other extreme ratios; observer checks actual ratio when reached.
# R3 SF09: x>=0 and g>=0 implies max(0,x-t*g) is zero when the negative product
# overflows; PG=min(g,x/t) is bounded. Conversely g<0 can overflow positively and
# cannot be clipped. Natural positive float32 overflow is covered above. Negative
# float64 overflow, just-above-f32max rounding back to max and extreme PG division
# have no robust qualified public witness here; D reviews those arithmetic rules.
# R4 SF10: exact quadratic curvature seed at x0 has descent along its own exact
# gradient, but residual32/operator error and later carried iterations remove a
# universal exact-descent theorem. Ties/rejection are therefore NOT impossible.
# Observed protocol tests verify strict comparison, first acceptance, rejected
# gradient omission, carrying and halving whenever these occur. The mixed signed
# cancellation example is permitted to take any contract-compliant rounded path;
# it is no promised tie/rejection witness. A platform-specific exact tie oracle
# would overconstrain permitted float64 reduction trees. The A2 continuation below
# CLOSES the robust scored-rejection/carried-step/projection gap with an independent
# physical enclosure. Exact computed ties and rejected-then-accepted scored paths
# remain relational checks plus D policy inspection; neither is called impossible.
# R5 SF11: RN64(t/2)=0 for positive finite t only when t=2**-1074. If the complete
# gradient has infinity norm <=2**923, its displacement then is <=2**-151, one
# quarter of the minimum float32 quantum. RN64 multiply/subtract then RN32
# cannot change a float32 x, including at zero, so stagnation precedes halving.
# A strict half-quantum shortcut is not used: intermediate RN64 can land on a
# midpoint. This sufficient bound covers our controls; it is not a universal
# theorem. Public adjoint OUTPUT is float64, not float32, so finite score and
# float32 residual input alone give no such universal data-gradient bound.
# No robust required-next-halving-underflow witness is supplied. D inspects
# the conditional arithmetic/guard, including halving only when
# another trial remains and propagation as backtracking_step, not zero-step trial.
# The real one-trial unrepresentable control covers exhaustion without any retry.
# R6 SF13: reached record scalar/types/frozen fields and absence of arrays in all
# documented trace fields are checked. Python's unbounded attribute space makes
# absence of every hidden/private archive unprovable through known public fields.
# Exact six-record declared fields/absence of extra state needs D inspection.
# Source-free exception behavior is tested, but external OS kill/timeouts have
# no promised result and are not simulated as success. Validation/geometry range
# tests do not prove address-space behavior on all machines.
# R7 SF01/SF14: provenance authenticity, driver once-only transfer, no calibration
# or truth channel internally, allocation strategy, no raw full-copy and full-size
# science/resource feasibility require coordinator/D work. No such proof or
# acceptance is claimed by this A checkpoint. Binding rejects public extra inputs.
#
# A2 keeper delta (all original keepers above remain):
# SF01/04/06/08/09/10/14 -> observed_public_composition_and_rounded_protocol;
# SF02 -> mapped_subclass_rejected_but_plain_view_valid, observer weakref checks;
# SF08 -> tiny_curvature_seed_range_and_finite_ratio;
# SF05/06/09/10/11/12 -> qualified_large_signal_retention,
# reference_large_signal_margins, rounded_subnormal_trial;
# SF10 -> rounded_cancellation_path_obeys_measured_selection (relational only);
# SF12/13/14 -> dependency_range_partial_trace;
# SF02/13 -> unrelated_dependency_failures_preserve_identity,
# backend_warning_policy_is_preserved.
#
# A2 continuation from checkpoint
# 057c51f5c4e92d3a7ecfe9be0e3a44754923621746eb420aca614243655bf17a:
# New approved expectation-source PROPOSAL PUBLIC-MATH-REFERENCE.md SHA256
# 008b622f4e70172f46775b3773b9b667f35ae9fb946c93545be3f5c9fa662ec4;
# pure-math script 97b9a6dd5d488521a932e2339eddbe6d4985389e9890e351ca9f57fd4de91d73;
# results e891324eec61ce15901e9baf06146fe355d991f7f2958806a41f5338e756ea53.
# All bindings verified; script/results were read, not executed or imported.
# No test depends on artifacts. Existing large-signal keepers remain stronger
# than adding a duplicate of control 1: they already prove all three outcomes
# with wide independently computed bounds and exact counts.
#
# SF04/06/08/09/10/12/14 distinct gap/keeper:
# nonuniform_projection_and_scored_backtracking with its two-iteration companion,
# qualified by reference_nonuniform_decision_margins and nonuniform_enclosure.
# Q1 detector spacing (0.125,1.0,0.08) um, q=(1,0), beams=(1,1,0), phases
# +/-RN64(pi/2), observations (1, fourteen RN64(1/140)), lambda=RN64(1e-6).
# Fine y sites are .25/.75 um. Physical rows are [2a,2a,0,0] and
# [0,0,2a,2a] within <1e-29 illumination error, not exact dark zeros;
# a=0.8610245072417031 from the finite Q1 pupil/pixel equation. No padding or
# coefficientwise builder condition is imposed. L=2, C_r(B_Q)=4a,C_c(B_Q)=a.
# Thus successful physical forward errors <=eta*8a*max(abs(x)); adjoint errors
# per orientation <=eta*10a*max(abs(r32)), eta=2e-4+1e-8. Calls/orientations
# may differ independently. Residuals/normalized direction/projections explicitly
# enclose RN64 then RN32. Decimal interval operations round outward at 110 digits.
# Additional 1e-12 observer padding encloses physical-reference/phase uncertainty
# and short ordinary reduction roundoff; it is NOT extra inverse tolerance.
# Real-call arithmetic still uses the existing independent 256*eps64 checks and
# cache application uses its unchanged 1e-4 allowance plus reference uncertainty.
#
# Two accepted first trials are followed by three strictly higher complete scores.
# Candidate2 has exactly zero second-y group; PG in iteration2 is <.015 while
# the gradient infinity norm is >.12. Rejected candidates 3/4/5 retain scores,
# never gradients, cannot replace incumbent2, and use t0,t0/2,t0/4. The two-
# iteration companion omits candidate2's unused gradient. Counts and actual
# entries are independent of the reported counters. Expected decision gaps are
# checked from independently recalculated intervals, not copied JSON endpoints.
# Test-side interval propagation is a fixed six-candidate witness calculation,
# not a general optimizer/recovery oracle. It never reads fit/dependency outputs.
# A fourth retry is not qualified. No new recovery/convergence target follows.
#
# Four authoring answers: approved projection/strict-selection/carry/retention
# obligations; plausible wrong raw-gradient PG, increasing step, accepting a
# worse score or replacing best by last rejection; existing composition tests
# had only conditional rejection checks; real fit plus transparent public calls,
# no production seam. Shared changes to the physical-weight helper extend B's
# review to all its existing dependents; independent no-argument coefficient is
# retained, and no A/B acceptance or historical accounting is reset.
# Every row uses a real caller boundary, has no new production seam, distinguishes
# the named credible failure, and fills a composition/propagation gap not proved
# by the existing inverse/camera contract keepers. B decides risk adequacy.


# A2 correction1 (post-C; supplemental additions retain that label): prior B1
# checkpoint 59b3fa8f6784999910dc673ec18e77c3ce172a9228dc665616890c9ded3cfb78.
# Diagnosed TEST DEFECT: the -1000 seed control asserted full completion merely
# from a finite seed. It did not qualify the first trial's public forward output.
# tiny_cache_exact_reference below instead derives the exact represented-payload
# target and unchanged 1e-4 application allowance with rational arithmetic. Shape
# (1,2,2) has lateral periods 4: cosine roots are exactly 0,+1,-1, so the inverse
# DFT and pixel coefficient are rational. Free padding is interpreted, never
# prescribed. Absolute kernel values precede pixel summation for G_C. The public
# caller's represented source/residual is the operand; no successful output is
# used as numerical truth. Nearest-binary64 distance proves a concrete output
# precision obstruction when it exceeds the allowance.
#
# REVISED keeper tiny_curvature_seed_range_and_finite_ratio[-1000] still requires
# a complete finite seed near 2**1002. It observes the actual trial-score entry,
# verifies its RN32 source from the real initial adjoint outputs and prescribed
# seed relation, and requires any recognized public range to retain the exact
# stage, code, partial trace/counts and initial best. On the qualified bound
# payload, nearest-output error exceeds the unchanged inverse tolerance, so
# numerical_incomplete/trial_score/dependency is the legitimate reached result.
# NEW SUPPLEMENTAL [-1010] separately exercises seed near 2**1012 and trial
# forward precision with a larger subnormal target. Nearest-output rounding then
# fits the allowance. This permits successful forwards; it is not a theorem
# that all inverse internal arithmetic or all later calls must complete. Both
# finite controls allow only a recognized range from an actually observed public
# trial-score forward, with no own range/earlier failure substituted. Successful
# calls must meet exact rational target inequalities. Complete scored decisions
# obey strict measured selection; no exact tie or rounded search path is forced.
# The smallest-positive lambda curvature_seed/seed_step proof is RETAINED.
#
# Affected obligations: SF05/SF08 (range-safe seed vs later representability),
# SF10/SF12 (score-incomplete trial cannot replace initial best), SF13/SF14
# (actual recognized dependency range and exact partial ledger). Observer code,
# shared decimal_score/decimal_seed, existing physical controls and all other
# keepers remain unchanged. New exact helper and the three parameter examples
# need fresh B2 review; broader retained applicability is B2's decision. Prior
# unavailable pre-C evidence is retained, never replaced by post-C product-red.


def camera(*, blank: float = 0.0, contrast: float = 1.0) -> Any:
    """Construct a public record with deliberately unused unavailable gain."""
    from simrecon import ScalarCameraEstimate

    return ScalarCameraEstimate(
        means_counts=np.array([blank - 2.0, blank, blank + 7.0]),
        variances_counts2=np.full(3, np.nan),
        frame_means_counts=(np.full(2, np.nan), np.full(2, np.nan), np.full(2, np.nan)),
        frame_variances_counts2=(np.full(2, np.nan), np.full(2, np.nan), np.full(2, np.nan)),
        empirical_mean_se_counts=np.full(3, np.nan),
        contrast_counts=contrast,
        gain_counts_per_e=None,
        information_codes=("nonpositive_variance_contrast",),
        source="  estimated camera; opaque  ",
    )


def inputs(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "raw_counts": np.zeros((3, 5, 1, 1, 1), dtype=np.float64),
        "camera_estimate": camera(),
        "carriers_yx_per_um": np.zeros((3, 2), dtype=np.float64),
        "phases_at_specimen_origin_rad": np.zeros((3, 5), dtype=np.float64),
        "beam_amplitudes": np.array([1.0, 0.0, 0.0]),
        "illumination_source": "  independent estimated arrays  ",
        "detector_spacing_um_zyx": (0.125, 0.08, 0.08),
        "specimen_origin_um_zyx": (0, -1, 2),
        "pupil_order": 1,
        "regularization": 0.25,
        "max_iterations": 2,
        "max_backtracking_trials": 4,
    }
    values.update(overrides)
    return values


def replace_camera(original: Any, **overrides: Any) -> Any:
    fields = {
        name: getattr(original, name)
        for name in (
            "means_counts",
            "variances_counts2",
            "frame_means_counts",
            "frame_variances_counts2",
            "empirical_mean_se_counts",
            "contrast_counts",
            "gain_counts_per_e",
            "information_codes",
            "source",
        )
    }
    fields.update(overrides)
    return type(original)(**fields)


def one_pixel_physical_weight(
    detector_spacing_yx_um: tuple[float, float] = (0.08, 0.08),
) -> float:
    """Q=1, dz irrelevant: pixel-integrated weight per source in (1,2,2).

    Independent Bessel power series, Decimal pi with >90 correct digits, 160
    decimal digits, 120 terms. Arguments are <6: the alternating tail is bounded
    by 9**120/(120!)**2 <1e-270. Float conversion dominates (<1e-14 relative).
    This physical target has no coefficientwise zero-padding assumption.
    """
    with localcontext() as ctx:
        ctx.prec = 160
        pi = Decimal(
            "3.1415926535897932384626433832795028841971693993751058209749445923078164062862089986280348253421170679"
        )
        radius = Decimal(1.4) / Decimal(0.525)
        dy, dx = (Decimal(s) / 2 for s in detector_spacing_yx_um)

        def h(radius_squared: Decimal) -> Decimal:
            argument_squared = 2 * pi * pi * radius * radius * radius_squared
            assert argument_squared < 36
            term = Decimal(1)
            terms = [term]
            for k in range(1, 120):
                term *= -argument_squared / (4 * k * k)
                terms.append(term)
            return pi * radius * radius * sum(terms) ** 2

        return float(dy * dx * (h(Decimal(0)) + h(dy * dy) + h(dx * dx) + h(dy * dy + dx * dx)))


def invoke(module: Any, values: dict[str, Any]) -> Any:
    kwargs = dict(values)
    raw = kwargs.pop("raw_counts")
    return module.fit_specimen(raw, **kwargs)


def decimal_score(
    source: np.ndarray,
    predictions: list[np.ndarray],
    values: dict[str, Any],
) -> tuple[float, float, float, tuple[tuple[float, ...], ...], tuple[tuple[float, ...], ...]]:
    """Exact represented-input loss target; no unstable raw float64 products."""
    with localcontext() as ctx:
        ctx.prec = 1600
        blank = Decimal(float(values["camera_estimate"].means_counts[1]))
        contrast = Decimal(float(values["camera_estimate"].contrast_counts))
        means, rmss = [], []
        squares = Decimal(0)
        for o, prediction in enumerate(predictions):
            row_means, row_rmss = [], []
            for p in range(5):
                # Contract: normalized observation and pointwise residual are RN64.
                residuals = [
                    Decimal(float(float(y) - float((Decimal(float(c)) - blank) / contrast)))
                    for y, c in zip(
                        prediction[p].flat, values["raw_counts"][o, p].flat, strict=True
                    )
                ]
                square = sum((r * r for r in residuals), Decimal(0))
                squares += square
                row_means.append(float(sum(residuals, Decimal(0)) / len(residuals)))
                row_rmss.append(float((square / len(residuals)).sqrt()))
            means.append(tuple(row_means))
            rmss.append(tuple(row_rmss))
        penalty = (
            Decimal(float(values["regularization"]))
            * sum((Decimal(float(x)) ** 2 for x in source.flat), Decimal(0))
            / (2 * source.size)
        )
        data = squares / (2 * values["raw_counts"].size)
        # Final sum is explicitly of the two returned binary64 components.
        return float(data), float(penalty), float(data) + float(penalty), tuple(means), tuple(rmss)


def first_step_bounds(regularization: float, *, mean_fraction: float = 1.0) -> tuple[float, float]:
    """Physical Q1 bounds, separately budgeting inverse, RN32 and reference error."""
    eta = 2e-4 + 1e-8 + 1e-13
    a = one_pixel_physical_weight()
    vmin = (mean_fraction - eta) / (mean_fraction + eta) * (1 - 2.0**-23)
    return (
        1 / (4 * a**2 * (1 + eta) ** 2 / vmin**2 + regularization / 4),
        1 / (4 * a**2 * (vmin - eta) ** 2 + regularization / 4),
    )


def large_signal_inputs(**overrides: Any) -> dict[str, Any]:
    raw = np.full((3, 5, 1, 1, 1), 3 * 2.0**126)
    raw[0, 0] *= -1
    return inputs(raw_counts=raw, regularization=0.001, **overrides)


class PublicObserver:
    """Transparent real public-entry observer; snapshots are tiny test-side data."""

    def __init__(
        self,
        *,
        fault: tuple[str, int, BaseException] | None = None,
        warning_at: tuple[str, int] | None = None,
    ) -> None:
        self.events: list[dict[str, Any]] = []
        self.fault = fault
        self.warning_at = warning_at
        self.cache: Any = None
        self.sources: dict[int, Any] = {}
        self.predictions: list[Any] = []
        self.adjoints: list[Any] = []
        self.max_live_sources = 0
        self.max_live_predictions = 0
        self.max_live_adjoints = 0

    def wrapper(self, operation: str, original: Any) -> Any:
        def entered(*args: Any, **kwargs: Any) -> Any:
            array = None
            if operation != "build_kernel_cache":
                key = "source_e" if operation == "forward" else "detector_values"
                array = args[0] if args else kwargs[key]
            event: dict[str, Any] = {
                "operation": operation,
                "settings": {
                    k: v.copy() if isinstance(v, np.ndarray) else v
                    for k, v in kwargs.items()
                    if k not in ("source_e", "detector_values")
                },
                "array": None if array is None else array.copy(),
                "outcome": "entered",
                "failure_code": None,
            }
            if array is not None:
                assert type(array) is np.ndarray and array.dtype == np.dtype("=f4")
                assert np.isfinite(array).all()
                if operation == "forward":
                    self.sources[id(array)] = weakref.ref(array)
            self.max_live_sources = max(
                self.max_live_sources, sum(ref() is not None for ref in self.sources.values())
            )
            self.max_live_predictions = max(
                self.max_live_predictions, sum(ref() is not None for ref in self.predictions)
            )
            self.max_live_adjoints = max(
                self.max_live_adjoints, sum(ref() is not None for ref in self.adjoints)
            )
            self.events.append(event)
            ordinal = sum(e["operation"] == operation for e in self.events)
            try:
                if self.warning_at == (operation, ordinal):
                    warnings.warn("public inverse warning sentinel", UserWarning, stacklevel=2)
                if self.fault is not None and self.fault[:2] == (operation, ordinal):
                    raise self.fault[2]
                returned = original(*args, **kwargs)
            except BaseException as error:
                event["outcome"] = "raised"
                event["failure_code"] = getattr(error, "code", None)
                raise
            event["outcome"] = "completed"
            if operation == "build_kernel_cache":
                self.cache = returned
            else:
                event["returned"] = returned.copy()
                references = self.predictions if operation == "forward" else self.adjoints
                references.append(weakref.ref(returned))
            return returned

        return entered


@contextmanager
def observe_public(
    module: Any,
    monkeypatch: Any,
    *,
    fault: tuple[str, int, BaseException] | None = None,
    warning_at: tuple[str, int] | None = None,
) -> Iterator[PublicObserver]:
    """Patch documented inverse entry points, reload importer, restore on all exits."""
    from scripts import simulation_inverse_operator as inverse

    observer = PublicObserver(fault=fault, warning_at=warning_at)
    try:
        with monkeypatch.context() as patch:
            for name in ("build_kernel_cache", "forward", "adjoint"):
                patch.setattr(inverse, name, observer.wrapper(name, getattr(inverse, name)))
            importlib.reload(module)
            yield observer
    finally:
        importlib.reload(module)


def decimal_gradient(
    source: np.ndarray, adjoints: list[np.ndarray], values: dict[str, Any]
) -> tuple[np.ndarray, np.ndarray]:
    """Independent complete expression and a conservative binary64 roundoff scale."""
    with localcontext() as context:
        context.prec = 1600
        answer, uncertainty = [], []
        for j, x in enumerate(source.flat):
            terms = [Decimal(float(a.flat[j])) / values["raw_counts"].size for a in adjoints]
            terms.append(Decimal(float(values["regularization"])) * Decimal(float(x)) / source.size)
            answer.append(float(sum(terms, Decimal(0))))
            uncertainty.append(float(sum(map(abs, terms), Decimal(0))) * 256 * 2.0**-52)
        return np.array(answer).reshape(source.shape), np.array(uncertainty).reshape(source.shape)


def decimal_seed(
    direction: np.ndarray, predictions: list[np.ndarray], regularization: float
) -> float:
    with localcontext() as context:
        context.prec = 1600
        numerator = sum((Decimal(float(v)) ** 2 for v in direction.flat), Decimal(0))
        image_square = sum(
            (Decimal(float(v)) ** 2 for p in predictions for v in p.flat), Decimal(0)
        )
        count = sum(p.size for p in predictions)
        return float(
            numerator
            / (image_square / count + Decimal(regularization) * numerator / direction.size)
        )


def projected_gradient(source: np.ndarray, gradient: np.ndarray, step: float) -> float:
    with localcontext() as context:
        context.prec = 1600
        components = [
            abs(Decimal(float(g)))
            if g < 0
            else min(Decimal(float(g)), Decimal(float(x)) / Decimal(step))
            for x, g in zip(source.flat, gradient.flat, strict=True)
        ]
        return float(max(components))


def cache_application_reference(
    cache: Any, values: dict[str, Any], orientation: int
) -> tuple[Any, float, float]:
    """Qualified tiny represented-payload target; no physical-padding expectation."""
    from simulation_inverse_operator_fixture import (
        kernel_from_spectra,
        light_bound,
        operator_matrix,
        pixel_matrix,
        row_column_norms,
    )

    shape, spacing = cache.source_shape_zyx, cache.source_spacing_um_zyx
    assert shape[1] in (2, 4) and shape[2] in (2, 4)
    kernel = kernel_from_spectra(cache.lateral_spectra, shape)
    amplitudes = (
        float(values["beam_amplitudes"][0]),
        float(values["beam_amplitudes"][1]),
        float(values["beam_amplitudes"][2]),
    )
    matrix = operator_matrix(
        kernel,
        shape,
        spacing,
        values["carriers_yx_per_um"][orientation],
        values["phases_at_specimen_origin_rad"][orientation],
        amplitudes,
        0.488,
        1.515,
    )
    rows, columns = row_column_norms(pixel_matrix(kernel, shape, spacing, absolute=True))
    light = light_bound(amplitudes)
    return matrix, light * rows, 5 * light * columns


def tiny_cache_exact_reference(
    cache: Any, operand: np.ndarray, *, transpose: bool = False
) -> tuple[list[Fraction], Fraction]:
    """Exact period-four, central-only zero-carrier application and error scale.

    The public cache's finite float32 payload, float64 spacing and float32
    operand are interpreted as exact rationals. This helper supplies no physical
    builder-coefficient expectation and never calls/reads product implementation.
    """
    assert cache.source_shape_zyx == (1, 2, 2)
    spectrum = cache.lateral_spectra
    assert spectrum.shape == (1, 4, 3)
    cosine = (1, 0, -1, 0)
    kernel = []
    for y in range(2):
        for x in range(2):
            value = (
                sum(
                    (
                        Fraction(float(spectrum[0, frequency_y, k]))
                        * (2 if k == 1 else 1)
                        * cosine[frequency_y * y % 4]
                        * cosine[k * x % 4]
                        for frequency_y in range(4)
                        for k in range(3)
                    ),
                    Fraction(),
                )
                / 16
            )
            kernel.append(value)
    area = Fraction(cache.source_spacing_um_zyx[1]) * Fraction(cache.source_spacing_um_zyx[2])
    coefficient = area * sum(kernel, Fraction())
    absolute_coefficient = area * sum(map(abs, kernel), Fraction())
    values = [Fraction(float(x)) for x in operand.flat]
    target = coefficient * sum(values, Fraction())
    scale = absolute_coefficient * max(map(abs, values)) * (5 if transpose else 4)
    return [target] * (4 if transpose else 5), scale / 10000


class MathInterval:
    """Outward Decimal arithmetic for one fixed, small physical witness only."""

    def __init__(self, low: Any, high: Any = None) -> None:
        self.low = Decimal(low)
        self.high = Decimal(low if high is None else high)
        assert self.low <= self.high

    @staticmethod
    def scalar(value: Any) -> MathInterval:
        return value if isinstance(value, MathInterval) else MathInterval(value)

    def __add__(self, other: Any) -> MathInterval:
        """Enclose every pairwise sum with outward decimal rounding."""
        other = self.scalar(other)
        with localcontext() as context:
            context.prec = 110
            return MathInterval(
                (self.low + other.low).next_minus(), (self.high + other.high).next_plus()
            )

    __radd__ = __add__

    def __neg__(self) -> MathInterval:
        """Reverse endpoints and negate exactly without context rounding."""
        return MathInterval(self.high.copy_negate(), self.low.copy_negate())

    def __sub__(self, other: Any) -> MathInterval:
        """Enclose subtraction through exact negation and outward addition."""
        return self + -self.scalar(other)

    def __mul__(self, other: Any) -> MathInterval:
        """Enclose all four endpoint products, including mixed signs."""
        other = self.scalar(other)
        with localcontext() as context:
            context.prec = 110
            products = [a * b for a in (self.low, self.high) for b in (other.low, other.high)]
            return MathInterval(min(products).next_minus(), max(products).next_plus())

    __rmul__ = __mul__

    def __truediv__(self, other: Any) -> MathInterval:
        """Enclose division by an interval known to be strictly positive."""
        other = self.scalar(other)
        assert other.low > 0
        with localcontext() as context:
            context.prec = 110
            reciprocal = MathInterval((1 / other.high).next_minus(), (1 / other.low).next_plus())
        return self * reciprocal

    def positive(self) -> MathInterval:
        return MathInterval(max(Decimal(0), self.low), max(Decimal(0), self.high))

    def square(self) -> MathInterval:
        with localcontext() as context:
            context.prec = 110
            endpoints = [self.low * self.low, self.high * self.high]
            lower = Decimal(0) if self.low <= 0 <= self.high else min(endpoints).next_minus()
            return MathInterval(lower, max(endpoints).next_plus())

    def padded(self, error: Any = Decimal("1e-12")) -> MathInterval:
        return self + MathInterval(Decimal(error).copy_negate(), Decimal(error))

    def rn64(self) -> MathInterval:
        return MathInterval(float(self.low), float(self.high))

    def rn32(self) -> MathInterval:
        # Float64 endpoints bracket the Decimal endpoints before RN32. This
        # handles possible endpoint double-rounding without assuming it away.
        low = math.nextafter(float(self.low), -math.inf)
        high = math.nextafter(float(self.high), math.inf)
        return MathInterval(float(np.float32(low)), float(np.float32(high)))

    def max_abs(self) -> Decimal:
        return max(self.low.copy_abs(), self.high.copy_abs())

    def contains(self, value: float) -> bool:
        return self.low <= Decimal(value) <= self.high

    def bounds(self) -> tuple[float, float]:
        return float(self.low), float(self.high)


def nonuniform_inputs(*, max_iterations: int) -> dict[str, Any]:
    raw = np.full((3, 5, 1, 1, 1), 1 / 140, dtype=np.float64)
    raw[0, 0] = 1
    phases = np.full((3, 5), math.pi / 2, dtype=np.float64)
    phases[0, 0] *= -1
    return inputs(
        raw_counts=raw,
        detector_spacing_um_zyx=(0.125, 1.0, 0.08),
        carriers_yx_per_um=np.array([[1.0, 0.0]] * 3),
        phases_at_specimen_origin_rad=phases,
        beam_amplitudes=np.array([1.0, 1.0, 0.0]),
        regularization=1e-6,
        max_iterations=max_iterations,
        max_backtracking_trials=3,
    )


def nonuniform_enclosure() -> dict[str, Any]:
    """Recalculate fixed candidate bounds from physical equations, never fit outputs.

    Four independent source-component intervals preserve nonuniform application
    error; no equality of columns/phases/orientations/calls is assumed. The tiny
    ideal dark-row correction and <1e-14 coefficient uncertainty are included in
    the separate 1e-12 observer enclosure. This is not a general numerical solver.
    """
    a = Decimal(one_pixel_physical_weight((1.0, 0.08)))
    eta = Decimal("0.00020001") + Decimal("1e-12")
    regularization = Decimal(1e-6)
    rows = [[2 * a, 2 * a, Decimal(0), Decimal(0)]]
    rows += [[Decimal(0), Decimal(0), 2 * a, 2 * a] for _ in range(14)]
    observations = [Decimal(1)] + [Decimal(1 / 140)] * 14

    def predictions(source: list[MathInterval]) -> list[MathInterval]:
        with localcontext() as context:
            context.prec = 110
            error = eta * 8 * a * max(x.max_abs() for x in source)
        return [
            sum((x * b for x, b in zip(source, row, strict=True)), MathInterval(0))
            .padded(error)
            .padded()
            for row in rows
        ]

    def residuals(source: list[MathInterval]) -> list[MathInterval]:
        return [(p - y).rn64() for p, y in zip(predictions(source), observations, strict=True)]

    def gradient(source: list[MathInterval]) -> list[MathInterval]:
        residual32 = [r.rn32() for r in residuals(source)]
        with localcontext() as context:
            context.prec = 110
            error = (
                eta
                * 10
                * a
                * sum(max(r.max_abs() for r in residual32[o * 5 : o * 5 + 5]) for o in range(3))
                / 15
            )
        return [
            (
                sum((r * row[j] for r, row in zip(residual32, rows, strict=True)), MathInterval(0))
                / 15
                + source[j] * regularization / 4
            )
            .padded(error)
            .padded()
            for j in range(4)
        ]

    def score(source: list[MathInterval]) -> MathInterval:
        data = sum((r.square() for r in residuals(source)), MathInterval(0)) / 30
        penalty = sum((x.square() for x in source), MathInterval(0)) * regularization / 8
        return (data + penalty).padded()

    def project(
        source: list[MathInterval], g: list[MathInterval], step: MathInterval
    ) -> list[MathInterval]:
        return [
            (x - (step * v).rn64()).rn64().positive().rn32() for x, v in zip(source, g, strict=True)
        ]

    def diagnostic(
        source: list[MathInterval], g: list[MathInterval], step: MathInterval
    ) -> MathInterval:
        components = []
        for x, v in zip(source, g, strict=True):
            ratio = x / step
            if v.high <= 0:
                components.append(-v)
            elif v.low >= 0:
                components.append(MathInterval(min(v.low, ratio.low), min(v.high, ratio.high)))
            else:
                components.append(MathInterval(0, max(-v.low, min(v.high, ratio.high))))
        return MathInterval(
            max(v.low for v in components), max(v.high for v in components)
        ).padded()

    x0 = [MathInterval(0) for _ in range(4)]
    g0 = gradient(x0)
    direction = [(-v).positive() for v in g0]
    maximum = MathInterval(max(v.low for v in direction), max(v.high for v in direction))
    direction = [(v / maximum).rn64().rn32() for v in direction]
    norm = sum((v.square() for v in direction), MathInterval(0))
    image_square = sum((v.square() for v in predictions(direction)), MathInterval(0))
    seed = (norm / (image_square / 15 + norm * regularization / 4)).padded()
    x1 = project(x0, g0, seed)
    g1 = gradient(x1)
    x2 = project(x1, g1, seed)
    g2 = gradient(x2)
    retries = [seed, (seed / 2).rn64(), (seed / 4).rn64()]
    rejected_sources = [project(x2, g2, step) for step in retries]
    sources = [x0, x1, x2, *rejected_sources]
    return {
        "coefficient": float(a),
        "seed": seed,
        "direction": direction,
        "sources": sources,
        "scores": [score(x) for x in sources],
        "gradients": [g0, g1, g2],
        "projected_gradient": [
            diagnostic(x0, g0, seed),
            diagnostic(x1, g1, seed),
            *(diagnostic(x2, g2, t) for t in retries),
        ],
    }
