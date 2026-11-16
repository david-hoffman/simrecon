# chore(memory): Design releasable prepared-band storage

https://github.com/david-hoffman/simrecon/issues/119

Follow-up to #84 and merged #108. This is a separate backlog task for its own intake; filing it does not activate a new runtime or scientific contract. Preserve the completed summary/full-debug compatibility work. No fixed process-memory ceiling, latency ratio or numerical tolerance has been selected. A 16 GiB workstation remains a feasibility objective, with caller/OS headroom to be measured.

The compact workflow still owns a complete monolithic prepared-band allocation through later reconstruction. Views of a completed time/direction block cannot release that allocation's backing storage. A design is needed before changing the private representation.

**One-task outcome:** one concrete prepared-band storage/ownership design and a bounded implementation handoff, or a documented equivalence blocker. This issue does not implement a disk API or redesign Fourier assembly.

**Prerequisite:** #116 supplies the measured peak and relevant workload. Reuse #112 if precision findings are available.

**Scope**
- Compare independently owned time blocks and direction blocks against the measured live set. Explicitly distinguish benefits for T>1 from the motivating T=1/multiple-direction case; time-only fragmentation cannot solve the latter's essential working set.
- Preserve preparation-before-estimation-before-reconstruction ordering, time-zero carrier reuse/fresh modulation, camera/anchor/drift state and all current finite/failure priorities.
- Specify logical shape/aggregate extent validation, ownership, adapters and the existing C-order little-endian byte identity without concatenating a second full band array.
- Define which blocks can die after their actual last consumer and what storage remains mandatory. Filter denominators can depend on all directions' parameters even when image-coefficient reads are local.
- If in-memory fragmentation cannot address the target peak, state the exact need for external storage and hand off one separately bounded disk-storage contract; do not silently introduce memmap or scratch ownership.

**Done when**
- [ ] A stage/block lifetime and dependency map justifies the proposed release points and accounts for all retained references.
- [ ] Same-input/output/identity and failure-order obligations are explicit, including off exposure and noncontiguous representations.
- [ ] A measured or analytically bounded opportunity is distinguished from unproved RSS savings; one-time and multi-time implications are reported separately.
- [ ] Independent scientific review accepts a concrete implementation slice with named representation boundaries and validation plan, or records the specific blocker.
- [ ] Any necessary disk-backed follow-up defines the missing ownership/cleanup/I/O/failure questions rather than claiming memory mapping alone solves FFT residency.

**Dependencies / exclusions:** after the working-set report; no preparation/estimation interleaving, filter/assembly fusion, raw replay, precision activation, domain expansion, output writer or general backend migration.

Sources: [compact bands](https://github.com/david-hoffman/simrecon/blob/836ec790aac55fb7fcdff8d51da1547091952b6e/src/simrecon/acquisition/modes.py#L98-L116), [workflow lifetime](https://github.com/david-hoffman/simrecon/blob/836ec790aac55fb7fcdff8d51da1547091952b6e/src/simrecon/workflow/reconstruct.py#L375-L431).

