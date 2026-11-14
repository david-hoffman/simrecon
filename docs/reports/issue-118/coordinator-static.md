# Issue 118 coordinator static observations

Nonblind coordination evidence; excluded from A/B inputs. This is not an
implementation, test checkpoint, measured result or acceptance verdict.

Public baseline examined: 64a752b4642709c539df2079cc3c906acf4cc7b8,
tree 9cafd665c6a2542a54e502c39ffa6bdc2cecad32. Source inspected statically
under the execution hold; no Python, probe, check or measurement was run.

At this provisional baseline, acquisition preparation owns `on` and optional
`off` phase arrays in the z loop. Both feed their lateral transforms; subsequent
drift/phase separation uses transform arrays rather than the phase arrays.
Transform arrays feed separation and copied x-Nyquist cells; optional off-order
combination then consumes the copied quadratures. Their local bindings otherwise
survive across the next z allocation and, on the last z, the full-Z transform.
Any future release needs independent C/D last-read/alias justification on the
actual parent, preserving camera/equalization/drift/finite-check/event order.

Native harmonic filtering allocates `plus` for each positive order and consumes
it when recombining reflected partners into the destination. Its local binding
otherwise survives until the next order assignment. Releasing after the complete
recombination would avoid that binding during the next allocation. Reuse would
add reset/zero/sign/untouched-cell reasoning; no reuse design is selected here.
Odd-Y omissions, Y=1, support-excluded cells and all-axis reflection require
independent contract tests; freeing a local must not free any published record.

These are theoretical lifetime overlaps only. No lower resident high-water,
payload reduction, churn reduction, speedup or 16GiB feasibility is established.
Matched fresh-process measurements, including repeated timing and retained
payload, remain required under the root's exclusive measurement scheduling.

Root reported the pinned Ubuntu preflight passed on its first attempt at
`/workspace/work/campaign/preflight-118-attempt1.log`; the environment is ready,
but all execution remains held for the priority #112 full gate. This report
does not reinterpret preflight as product verification.

Before C, root must freeze accepted parent117, and the coordinator must assess
all actual inherited changes (including profile113/shared helpers), rebind
packets/checkpoint and renew affected evidence. The public-main observations
here supply no automatic qualification of later branches.
