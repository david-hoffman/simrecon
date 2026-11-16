"""Fixed stdlib file-only manuscript assembly, gated by CLOSED78 collation.
No scientific function, benchmark, installed package, subprocess or new observation.
"""
import collections
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
ANALYSIS = EVIDENCE / "resource-analysis-closed78-1"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name):
    return json.loads((ANALYSIS / name).read_text())

def table(headers, rows):
    return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] +
                     ["| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |" for row in rows])

def triple(group):
    return " / ".join(str(group[key]) for key in ("min", "median", "max"))

metadata = load("run-metadata.json")
if metadata["record_count"] != 78 or metadata["complete_condition_mode_profile_role_groups"] != 26:
    raise ValueError("not complete CLOSED78/26 scalar corpus")
records = load("per-process.json")["records"]
if [row["ordinal"] for row in records] != list(range(1, 79)) or any(row["terminal"]["returncode"] != 0 for row in records):
    raise ValueError("failed/missing/unordered member; no manuscript assembly")
summary = load("three-repeat-summary.json")["groups"]
profiles = load("profile-control-references.json")["references"]
common_modes = load("shared-mode-common-correspondence.json")["references"]
checks = load("fingerprint-correspondence.json")["checks"]
stages = load("stage-events.json")["events"]
if len(profiles) != 12 or not all(row["same_role_mode_condition_repetition"] for row in profiles):
    raise ValueError("missing exact fresh profile references")
input_names = ("run-metadata.json", "per-process.json", "per-process.csv", "three-repeat-summary.json", "three-repeat-summary.csv",
               "profile-control-references.json", "shared-mode-common-correspondence.json", "fingerprint-correspondence.json", "stage-events.json", "closed78-inputs.sha256", "closed78-roster.tsv", "collate_closed78.py")
input_hashes = {str(ANALYSIS / name): sha(ANALYSIS / name) for name in input_names}
primary_sources = (
    Path("/workspace/work/issue-118/src/simrecon/acquisition/modes.py"),
    Path("/workspace/work/issue-118/src/simrecon/reconstruction/known_parameters.py"),
    Path("/workspace/work/issue-118/src/simrecon/workflow/reconstruct.py"),
    Path("/workspace/work/issue-118/src/simrecon/workflow/summary.py"),
    Path("/workspace/work/issue-118/docs/contracts/preparation-harmonic-lifetimes-v1.md"),
    Path("/workspace/work/issue-119/docs/contracts/prepared-band-storage-design-v1.md"),
    Path("/workspace/work/campaign/issue-119.md"), Path("/workspace/work/campaign/issue-120.md"),
    EVIDENCE / "ROOT-global78-schedule-before-observation-1.json",
    EVIDENCE / "resource-method-final-source-preparation/PROTOCOL-SOURCE2.md",
)
input_hashes.update({str(path): sha(path) for path in primary_sources})
lookup = {(row["route"], row["condition"], row["mode"], row["profile"], row["role"], row["metric"]): row for row in summary}
family_keys = sorted({(row["route"], row["condition"], row["mode"], row["profile"]) for row in records})
result_rows = []
payload_rows = []
range_rows = []
for family in family_keys:
    for role in ("parent", "candidate"):
        values = [lookup[family + (role, metric)] for metric in ("terminal_native_KiB", "target_or_workflow_call_seconds", "sampled_valid_RSS_max_bytes")]
        result_rows.append(list(family) + [role] + [triple(row) for row in values])
        payload_values = [lookup[family + (role, metric)] for metric in ("caller_array_payload_bytes", "result_array_payload_bytes", "union_array_payload_bytes")]
        payload_rows.append(list(family) + [role] + [triple(row) if row["summary_status"] == "complete_three_numeric" else "NOT_EMITTED" for row in payload_values])
    observation = []
    for metric in ("terminal_native_KiB", "target_or_workflow_call_seconds"):
        parent, candidate = (lookup[family + (role, metric)] for role in ("parent", "candidate"))
        if candidate["max"] < parent["min"]:
            meaning = "all three candidate values below all three parent values"
        elif candidate["min"] > parent["max"]:
            meaning = "all three candidate values above all three parent values"
        else:
            meaning = "observed ranges overlap or touch"
        observation.append(meaning)
    range_rows.append(list(family) + observation)

all_fp = all(row["all_six_scientific_fingerprint_projections_equal"] for row in checks)
all_direct_callers_unchanged = all(row["direct_caller_inputs_unchanged"] for row in checks if row["route"] == "direct")
all_profile_fp = all(row["input_common_public_branches_fingerprints_equal"] for row in profiles)
all_common_modes = all(row["common_hash_equal"] and row["input_hash_equal"] and row["branches_equal"] for row in common_modes)
gap_rows = [[row["ordinal"], row["attempt_id"], row["samples"]["line_count"], row["samples"]["valid_rss_count"],
             row["samples"]["missing_or_invalid_rss_count"], row["samples"]["malformed_json_count"],
             (row["receipt_rss_terminal_confirmation"] or {}).get("outcome")]
            for row in records if row["samples"]["missing_or_invalid_rss_count"] or row["samples"]["malformed_json_count"]]
profile_stage_rows = []
for row in records:
    if row["route"] == "workflow" and row["profile"]:
        exits = [f"{event['stage']}({event.get('time_index')}):{event['ru_maxrss_native_KiB']}" for event in row["stages"] if event["edge"] == "exit"]
        profile_stage_rows.append([row["attempt_id"], row["role"], row["mode"], row["repetition"], "; ".join(exits)])

# These are this author's primary-source/data dispositions, not copied SCI verdicts.
# All claims await the independent whole review; currentlarge/downstream premises remain held.
disposition_rows = [
    ["EA central searched full/summary tables", "SUPERSEDE only observed current g1/g2 rows", "Current 75fc/2cb raw-three results below; original EA values retain EA identity, no causal pooling."],
    ["EA central stage association", "REFRESH observed g5/g6 associations only", "stage-events.json and exact fresh same-role/repetition controls; cumulative endpoints and profile perturbation, not stage allocations."],
    ["EA largest256 profiles/tables/ranking", "HOLD current extrapolation; RETAIN EA historical-only", "No current256 row; NOT_ADMITTED/UNMEASURED. No current margin/scaling/ranking follows."],
    ["Native harmonic scratch opportunity", "SOURCE liveness shortened; empirical scope direct-known/whole workflow only", "Complete filtered/debug owners retained; known process peak includes earlier acquisition setup, not filtering-only attribution."],
    ["CE06 per-z liveness", "SUPERSEDE affected local-owner lifetime wording", "on/off and consumed spectra explicitly end after copied values; direct64/128/off/drift observations, CE02 separate context."],
    ["Compact estimator overlap handoff", "RETAIN inherited117 scope, not an118 effect", "Accepted117 code already in both roles; code difference is only six118 insertions, with no isolated causal effect proved by matching context."],
    ["Full diagnostic ownership", "RETAIN complete independent public records", "Source owners/keeper semantics plus matching-mode fingerprints; no removal/payload reduction is implemented."],
    ["All-T q/time aggregation", "RETAIN source premise; HOLD T-growth benefit", "Current monolithic q backing persists across time views. Tiny T2 compatibility and central T1D3 cannot demonstrate T-growth release."],
    ["Phase/padded/inverse expression lifetime", "RETAIN unresolved named opportunity", "118 changes native plus, not phase assembly. Direct-known/profile associations do not locate native workspace or isolate expression savings."],
    ["Payload/native metric statements", "REFRESH emitted per-row quantities and units", "Caller/result/backing union only where emitted; RSS/wait4/self peaks distinct, no physical-reclaim/source-size equivalence."],
    ["Original huge target /115 wide", "HOLD unmeasured and allocation-unadmitted", "Byte-only cap superseded; signed/native/stencil constraints remain, no16GiB guarantee or full-volume trial."],
    ["119 prepared-band feasibility", "SOURCE-only relevance retained; no design acceptance", "All-T ownership and T1D3/all-directions parameter/consumer/failure constraints remain; time-only fragmentation is not established as a T1 solution."],
    ["119 block/file-backed benefit/identity", "HOLD implementation and necessary currentlarge premises", "No block prototype, streaming identity/partial-release proof, currentlarge ranking or measured T-growth advantage in this series."],
    ["120 destructive assembly/backend equivalence", "HOLD prototype/backend/negative-control proof", "Overwrite hint is not in-place/no-workspace proof; signed grid/Nyquist/norm/true2D/finite/failure compatibility still needs the study's own controls."],
    ["120 relevant current peak/fit/benefit", "HOLD required attribution/ranking premises", "Observed direct-known/setup and cumulative shared stages are finite associations; necessary currentlarge measurements require separate admission before reliance."],
    ["113 single precision", "ABSENT / no qualification transferred", "Current float64/complex128 scientific mapping unchanged; no single-precision result or benefit."],
]

report = f'''# Preparation and harmonic scratch lifetimes: finite matched observations

AUTHOR MANUSCRIPT — CLOSED78 descriptive evidence; independent WHOLE post118 SCI is
PENDING. This document is the coordinator's source/data-based assessment, not a copied
peer verdict, numerical release or final-gate/D/publication acceptance.

## Scientific subject and local-owner change

Measured candidate75fce7e1ea424127f1b875aaa395d8b3ea29ecaa/tree275e0d94ff94dc1283f5da80815d6bb383c68c86
over parent1172cb73d7a8352d88a16477e5e802852b4948c62cd/treead275aa5bbfb2e0b69db81e8803764ddf4b00fbc.
Six source insertions implement four completed-private-local deletions and two comments.
Per-z on expires after rfft2 before off transform; off expires after its optional
transform; on_fft/off_fft expire after q/off_q separation, stored Nyquist and selected
off combination; plus expires after reflected partner/recombination reads copy into
filtered. Caller/camera state, q/off_q, independently copied debug occurrences and
published filtered/image/parameter owners remain live. No buffer reuse or arithmetic,
stage/check/failure order, signed-zero/reflection/oddY/Y1 change is introduced. The
local lifetime argument does not reduce allocation counts, public payload, or prove
physical reclamation/churn/peak benefit. Monolithic all-T prepared backing remains.

Actual-parent B4static checkpoint2043/ed43 and1872 C ordinary passes are separately
labelled preservation evidence, not new memory trials or exact final verification.
Source38-perrole/protocol/directece8/workflowchild5249/value9291/fixture2713 pins bind
the scientific subjects. Later documentation commits must preserve these identities.

## Complete finite corpus and comparison meaning

78 original scheduled observations closed:42 DIRECT plus36 WORKFLOW, each of13 exact
route/condition/mode/profile families has3 per role (26 groups). Actual frozen order:
g3tiny2Dsummary6,g4tiny2Dfull6,seven directcases6each,g1central64summary6,g2full6,
g5profilesummary6,g6profilefull6. Every case/group r1P/C,r2C/P,r3P/C. This is partial
counterbalancing, not randomized balance/drift correction/population uncertainty.
Old18 original117candidate rows precede this series and are CONTEXT ONLY, never fresh
controls, relabelled2cb observations or substitute slots. Profile references are the
same actual role/mode/condition/repetition unprofiled members;12 references add0runs.
No256/newscale/Cartesian expansion/retry/favorable-case selection was added.

All78 receipts are complete/terminal0 and bound material identities match. Every
refused/failed/partial/diagnostic history remains separately preserved, not erased by
these successful members. Direct input-after/result cohort fingerprint equality:
{all_fp}. Direct before/after caller-input fingerprint equality: {all_direct_callers_unchanged}.
Profile vs own fresh unprofiled fingerprint projection equality: {all_profile_fp}.
These are HASH/PROJECTION correspondence, NOT literal full-array byte comparison or
an independent physical-accuracy oracle. Scientific helper finite sums/RC1 conditional
primitive/FFT-enclosure assumptions remain distinct preservation evidence. No new
tolerance or result-derived expectation was selected. Existing18 full-summary same-role/
case/profile/repetition reference pairs compare common values/branches only; all such
hash/branch projections equal: {all_common_modes}. Whole public graphs compare within
matching mode/schema, not across full and summary.

## Literal per-role three-repeat observations

Cells are minimum / stdlib median / maximum of the actual3 values; rawr1/r2/r3 and
sourcepath/hash remain in canonical scalar files. Memory native LinuxKiB, call seconds,
sampled validRSS bytes. Workflow union is NOT_EMITTED, never fabricated from separate
caller/result traversals. Direct caller/result/union are actual emitted supported
backing traversals. The complete payload/self/terminal/ownership/context metrics and
all nativevalues remain in per-process.json/CSV and three-repeat-summary.json/CSV.

{table(["Route","Condition","Mode","Profile","Role","Terminal native KiB min/med/max","Call seconds min/med/max","Sampled validRSS bytes min/med/max"], result_rows)}

## Retained backing payload and profile endpoints

Payload cells are actual emitted supported-array backing bytes min/median/max,
not process memory or native workspace. Workflow union is explicitly NOT_EMITTED.
The unchanged scientific/public storage contract can leave all payload values the
same even when a private local lifetime differs.

{table(["Route","Condition","Mode","Profile","Role","Caller backing bytes","Result backing bytes","Emitted union bytes"], payload_rows)}

Each following endpoint sequence is literal native LinuxKiB, in emitted stage order,
for one profiled process. Parenthetical time indices distinguish reconstruction time.
These cumulative associations are paired with the exact same-role unprofiled control
in profile-control-references.json. Do not subtract adjacent endpoints or treat them
as isolated stage/workspace allocations, a measured contributor ranking, or current256.

{table(["Attempt","Role","Mode","Repetition","Stage-exit(time): cumulative native KiB"], profile_stage_rows)}

## Bounded observed range relations

The following is only literal ordering of these finite range endpoints. It makes no
causal, population, capacity, isolated-native/FFT or general performance claim. Even
separated triples may reflect physical/cache/native/allocator/context variability.
Known peak includes preparation/setup while its target timer excludes that work.

{table(["Route","Condition","Mode","Profile","Terminal native range relation","Call-time range relation"], range_rows)}

## Sampling gaps and metric boundaries

{table(["Ordinal","Attempt","Sample lines","ValidRSS","Missing/invalidRSS","MalformedJSON","Receipt confirmation outcome"], gap_rows)}

Null/missing/invalidRSS are retained with exactline/keypresence/error/receipt gap basis,
not zero or proof of exit. MaxvalidRSS is discrete and maymiss instantaneous peaks.
Target selfpre/call-end/post highwater is cumulative, before JSON/teardown. Terminal
exactPID wait4 is directchild usage through finalexit, nativeLinuxKiB×1024; preexec/
inherited highwater retention unresolved, no tree/observer sum or baseline subtraction.
Directtarget timing is onepubliccall; known raw/settings/setupbands/transfers/parameters/
result stay retained, and earliergeneration/preparation can dominate wholeprocesspeak.
Payload roots/metadata/nativeworkspace/RSS remain different scopes. Profile stages
are cumulative associations and perturb the context, not isolated allocation/FFT
attribution or unperturbed stage timing. Stage events exported: {len(stages)}, with
rawtimestamps/nativeKiB/explicitbytes and exact same-role unprofiled references.

Spawn-to-terminal_collection uses actual reaped_monotonic_ns. Separately the recorded
finished_monotonic_ns interval ends at observer finalization BEFORE final candidate/
material hashing/postflight/receipt serialization. Actual receipt-serialization
completion is UNMEASURED. Neither is target-call time. The earlier README description
was corrected with originalbytes retained; numeric54 data/source were not rerun.

## Provenance, activation and qualification

Role-specific source/Git/package/publicversion/origin/editable/interpreter/lock/backend/
thread/allocator/host/cgroup/currentlimits/ownership/proofs remain per actualrecord.
No physical-state equivalence or effective native-worker count beyond observed context
is fabricated. ROOT preserves P3's14 EXPECTED normal/help/abort/provenance outcomes,
zero publicscientificcalls/workloadspawns, not14 failed trials. P2 retains exact named
function/input/environment qualification only; old caps do not transfer authority.
Initial tiny actual members supplied limitedP4 exec/PID/map/schema/backend correspondence
in their original slots. Direct expectedprovenance/environment was frozen BEFOREdirect
from actual own-role WF context+P3 helper. First real adapterparentcase qualification
preceded dependentcandidate releases; no duplicate workflow/Q0/control matrix needed.

Historical review-time13pins were PREACTIVATION. ROOT changed only3operationalflags
in each of2manifests (6field transitions): approved/numerical_release false→true and
execution_status→released_exact_case. Beforemanifest copies and currentactive hashes/
activationreceipts are separate, no code/predicate/scientificinput change. Parent is
TRACKEDclean but FULL exactly2declareduntrackedmethodcopies (17150B ece8 adapter,
12755B2ce88 protocol); dirtyfalse is tracked-only, never FULLclean. ROOTowns exactcopy
cleanup after ownership/resourcewindow closure and archival. Candidate subjectclean
status and later documentation identity remain separately recorded.

ROOT supplied actual per-member representation/stencil/namespace/everyvisibleancestor/
host/rlimit/swap/disk/parser/observer headroom/proof contents/exclusive grants. Proof
hashes are identity, not semantic safety. Hidden ancestors/actors and unsupported
abruptspawn/Git/outerloss remain conditionalunknown. Inner exactPID solewait4 cleanup,
outerPopen+communicate expiry UNKNOWN/HOLD/no-nextcase disposition, no genericreaper/
automaticretry/universaldeath recovery claim. Direct1200/1320andWF240/300 operating
bounds are not performance/capacity guarantees or humanselected budget.

## Affected116 and downstream conclusions proposed for independent SCI

{table(["Statement/premise","Author disposition","Source/data basis and retained limit"], disposition_rows)}

Current256 remains NOT_ADMITTED/UNMEASURED; largest/d1/36/19gap holds persist. Old116EA
is historicalEA, not current117118 profile/rank/margin/scaling truth. Necessary current
large attribution/ranking measurements stay separately held BEFORE any119/120 premise
that depends on them. This finite report does not commission that matrix or119/120
implementation, streaming identity, backend/prototype or storage behavior. Unrelated
119opticalgeneration contract is inapplicable. Correct prepared-band-storage-design-v1
contract80afb7a7 supplies design-only R1–R9 and actual118 reviewed-refresh prerequisites,
alongside the authoritative issue body; no stronger119 design/API acceptance follows.
113single is absent;115byte-only removal leaves signed/native/stencil
constraints intact. No default16GiB fit, physicalaccuracy/Cbinaryequivalence or universal
improvement is established.

## Analysis history, portability and remaining gates

Collation/assembly are file-only stdlib scalar work, no product/numpy/scipy/pytest/bench
imports or scientificcalls/workloadspawns. -I-S-B applies only to this analysisprocess,
NOT numericaltarget startup qualification/argv. Frozen partial54 source/outputs and
schema/terminalcollection/READMEdescription corrections remain preserved, no science
retry. Final78 source/commands/status/inputclosure/outputhashes separately pinned.
Raw JSON/sample/binary/receipt paths and identities must survive portableintegration;
compressed transport never substitutes its hash for restored originals. ROOT owns
exact archival location/restoration and final portablemap checks.

All A/B/STOP/C/SRC/method/preSCI/scalar/correction charges/history remain; actualserving/
meters/tokens/cache/money/unrecordedelapsed unknown. WHOLEpost118SCI must independently
judge these actual data, claims, source/science/ownership/metrics/variation/failures and
explicit affected116/downstream dispositions. Full exact Ubuntuverify/freshD/publication
remain separate pending gates. No partial or sourceacceptance is finalwholeacceptance.
'''
(HERE / "manuscript.md").write_text(report)
(HERE / "dispositions.md").write_text("# Author post118 dispositions — pending independent WHOLE SCI\n\n" +
    table(["Statement/premise", "Author disposition", "Source/data basis and retained limit"], disposition_rows) + "\n")
(HERE / "assembly-inputs.sha256").write_text("".join(f"{value}  {path}\n" for path, value in input_hashes.items()))
(HERE / "assembly-metadata.json").write_text(json.dumps({"scope": "CLOSED78_AUTHOR_MANUSCRIPT_PENDING_INDEPENDENT_WHOLE_SCI",
    "script_sha256": sha(Path(__file__)), "python": sys.version, "executable": sys.executable,
    "no_site": sys.flags.no_site, "isolated": sys.flags.isolated,
    "input_identity": input_hashes, "scientific_calls": 0, "numerical_workload_spawns": 0,
    "source_oracle_changes": False, "opinion_bodies_copied": False,
    "all_fingerprint_projections_equal": all_fp, "all_direct_caller_inputs_unchanged": all_direct_callers_unchanged,
    "profile_reference_fingerprints_equal": all_profile_fp,
    "full_summary_common_projections_equal": all_common_modes}, indent=2) + "\n")
print(json.dumps({"status": "author_manuscript_assembled_pending_WHOLE_SCI", "records": len(records), "groups": 26}))
