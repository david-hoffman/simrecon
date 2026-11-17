# SP113 — selected standalone-sine source-path clarification

This supplements point-libm-method.md without changing its frozen bytes or
extending its finite point domain. This whole file is an approved public input;
its references are provenance, not permission to read source or follow links.
No numerical observation, acceptance, new tolerance or execution grant follows.

For glibc2.39 at x=+/-P/2, distinguish the source sequences:

- Standalone cosine and combined sincos form y=hp0-abs(x), a=y+hp1,
  da=(y-a)+hp1. At the selected point y=0,a=hp1,da=0. Cosine evaluates
  do_sin(hp1,0); combined sine evaluates sign(x)*do_cos(hp1,0).
- Standalone sine instead forms t=hp0-abs(x) and evaluates
  copysign(do_cos(t,hp1),x). At the selected point t=0, so its call is
  do_cos(0,hp1), not the preceding a/da statement sequence.

In do_cos, the source forms u=big+abs(z), then
r=abs(z)-(u-big)+dz. Here big=0x1.8p45 and hp1=0x1.1a62633145c07p-54.
Since hp1 is positive and smaller than the half-spacing 2^-8 at big,
both (z,dz)=(0,hp1) and (hp1,0) select knot zero and give r=hp1 exactly
under the stated RNE assumptions. Knot zero has (sn,ssn,cs,ccs)=(0,0,1,0).
The subsequent source cosine polynomial expression is therefore the same for
these two selected calls. Keep the original tiny-correction/range/rounding-cell
proof; do not generalize this selected-point equality to other arguments or
claim identical source arithmetic for the different entry points.

The actual primitive/binary/source correspondence, arithmetic conditions and
each fixture's complete propagation remain necessary. This clarification alone
establishes no actual dispatch, runtime accuracy, signed-zero result, product
acceptance or closure of unsupported FFT/libm witnesses. A/B independently
derive any used bound and actual branch/bin margins. Do not change a tolerance
from observed results, omit required positive cases or introduce a general
oracle framework to implement this clarification.

Primary facts independently opened at tag glibc-2.39 in bminor/glibc:

- sysdeps/ieee754/dbl-64/s_sin.c, Git blob
  ad3175001fad5e1376ff9fc0442b43853b6d6bbe: do_cos, standalone sine's moderate
  branch and standalone cosine's moderate branch.
- sysdeps/ieee754/dbl-64/s_sincos.c, Git blob
  adbc57af2827bb801c3497d6716c41109cb1eafa: combined moderate reduction.
- sysdeps/ieee754/dbl-64/sincostab.c, Git blob
  1459368bc73dcd2bd5cbb53500a992a101076b9d: knot-zero exact bit values.

Same A1 may read only this additional whole file and update its existing
eight-file/report scope if its explanation depends on the compressed wording.
Preserve existing work/attempts. Return revised input/code/method hashes and
explicit applicability gaps. All existing static-only, source-free transport,
wide-test safety, fresh-B and installed/build holds remain.
