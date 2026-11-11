# Source edge bounds depend on the actual caller and allocation

**Version 1.0**

- ID: 20261104T045108Z-ce06-coordinator-source-padding
- Date: 2026-11-04T04:51:08.665983+00:00
- Task: [CE06 acquisition modes](../tasks/c-equivalence-acquisition-modes.md)
- Role: coordinator
- Topic: static source-domain analysis
- Status: confirmed for the pinned source mathematics; executable behavior unqualified
- Observation: The bead helper's fixed10 horizontal subtraction uses Y-1-k in a zero-initialized row of X+2 floats. Its tight edge-address envelope is even X>=8, Y>=10, Y<=X+2. The specimen helper uses X-1-k and still needs X>=10. Transferring the specimen bound incorrectly excluded the defined bead X8/Y10 family. Edge safety alone does not waive centering, diagnostic, repair, normalization or downstream stencil conditions.
- Evidence: [Accepted contract section8](../contracts/c-equivalence-acquisition-modes-v1.md#8-safe-rectangular-and-z1-empirical-radialft-preparation), hash 57305b967a33a9a2177b145df3f964289e24424e9b5a730fb51bc91e8660f162; pinned mainfile.c b923813e221127e01eb602f163dd816e0404fef351b46c8f68006f507e0309a8, sirecon.c 3f15d3dfddf4db21c8f166de63820870c9775e22a954b6df1ba8be625622c567. CE06 source-review-4 report SHA256 00dd1fb9c73dcb4b19f9a192ceb92be7745ddf6ac335a0a73f32119f045e7ef7: independent complete-caller/address/control derivation, including 880 geometry checks; no retained C execution.
- Suggested action: Derive bounds from each executed flat address and initialized allocation before transferring a similarly named helper's restriction. Check the complete caller and a permitted boundary control.
