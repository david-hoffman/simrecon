#!/usr/bin/env bash
# No authority to start: coordinator must explicitly return numerical window.
set -eu
cd /workspace/work/issue-112
report=docs/reports/single-precision-study
for case_name in workflow-full workflow-summary; do
  for rep in 1 2 3; do
    dest="$report/raw/corrections-v3_${case_name}_${rep}.json"
    args=(timeout 30s docker exec --user 1000:1000 -w /workspace/work/issue-112 -e PATH=/workspace/.simrecon-tools/uv-env/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin -e OMP_NUM_THREADS=1 -e OPENBLAS_NUM_THREADS=1 -e MKL_NUM_THREADS=1 -e NUMEXPR_NUM_THREADS=1 -e VECLIB_MAXIMUM_THREADS=1 simrecon-campaign-ubuntu .venv/bin/python "$report/corrections_v3.py" run --case "$case_name" --repeat "$rep")
    printf '%q ' "${args[@]}" >> "$report/raw/commands.log"
    printf '> %q\n' "$dest" >> "$report/raw/commands.log"
    set +e
    "${args[@]}" > "$dest" 2> "$dest.stderr"
    status=$?
    set -e
    printf 'corrections %s %s status=%s\n' "$case_name" "$rep" "$status" >> "$report/raw/process-status.log"
    if [ "$status" -ne 0 ]; then exit "$status"; fi
    if ! jq -e '.status == "completed"' "$dest" >/dev/null; then exit 3; fi
  done
done
