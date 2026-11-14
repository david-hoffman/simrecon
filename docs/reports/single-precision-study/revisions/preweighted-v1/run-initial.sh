#!/usr/bin/env bash
# Sequential fresh processes; coordinator must grant each requested phase.
set -eu
cd /workspace/work/issue-112
report=docs/reports/single-precision-study
phase=${1:?phase required}
run() {
  local case_name=$1 profile=$2 rep=$3
  local dest="$report/raw/${case_name}_${profile}_${rep}.json"
  local args=(timeout 30s docker exec --user 1000:1000 -w /workspace/work/issue-112 -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e VECLIB_MAXIMUM_THREADS=1 simrecon-campaign-ubuntu .venv/bin/python "$report/study.py" run --case "$case_name" --profile "$profile" --repeat "$rep")
  printf '%q ' "${args[@]}" >> "$report/raw/commands.log"
  printf '> %q\n' "$dest" >> "$report/raw/commands.log"
  set +e
  "${args[@]}" > "$dest" 2> "$dest.stderr"
  status=$?
  set -e
  printf '%s %s %s status=%s\n' "$case_name" "$profile" "$rep" "$status" >> "$report/raw/process-status.log"
  if [ "$status" -ne 0 ]; then return "$status"; fi
}
if [ "$phase" = first ]; then
  for rep in 1 2 3; do run M01 mixed "$rep"; done
  for case_name in M02-signed M03-zero-mod M03-carrier-positive M03-carrier-negative; do
    for profile in mixed prototype-double public-double; do
      for rep in 1 2 3; do run "$case_name" "$profile" "$rep"; done
    done
  done
elif [ "$phase" = small ]; then
  for case_name in M04-directions M05-power-100 M05-power0 M05-power100 M06-near-cancel M06-exact-cancel M16-times; do
    for profile in mixed prototype-double; do
      for rep in 1 2 3; do run "$case_name" "$profile" "$rep"; done
    done
  done
  for case_name in M06-near-cancel M06-exact-cancel; do
    for rep in 1 2 3; do run "$case_name" public-double "$rep"; done
  done
  for case_name in M07 M08-M09 M14-M18; do
    for rep in 1 2 3; do run "$case_name" mixed "$rep"; done
  done
elif [ "$phase" = resource ]; then
  for case_name in M19-spatial32 M19-spatial64 M20-direction1 M20-times2 M20-native2d; do
    for profile in mixed prototype-double; do
      for rep in 1 2 3; do run "$case_name" "$profile" "$rep"; done
    done
  done
else
  exit 2
fi
