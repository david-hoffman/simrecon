"""Resource-observer checks and safe baseline workload qualification for RM84."""

from __future__ import annotations

import dataclasses
import hashlib
from typing import Any

import numpy as np
import pytest

import simrecon
from reconstruction_memory_benchmark import (
    host_context,
    public_value_sha256,
    retained_payload,
    rss_bytes,
)
from reconstruction_summary_fixture import SCENARIOS, identity, scenario, workload


@pytest.mark.parametrize("system,native,expected", [("Linux", 123, 125952), ("Darwin", 123, 123)])
def test_native_rss_conversion(system: str, native: int, expected: int) -> None:
    assert rss_bytes(native, system) == expected


def test_unknown_rss_units_are_not_guessed() -> None:
    with pytest.raises(ValueError, match="unsupported"):
        rss_bytes(123, "unqualified")


def test_retained_payload_counts_shared_backing_once_not_visible_view_bytes() -> None:
    @dataclasses.dataclass(frozen=True)
    class Record:
        left: Any
        right: Any
        nested: Any

    owner = np.arange(100, dtype=np.float64)
    independent = owner[:10].copy()
    record = Record(owner[:10], owner[50:60], (independent, independent, owner[:0]))
    observed = retained_payload(record)
    assert observed["array_payload_bytes"] == 880
    assert observed["unique_backings"] == 2
    assert len(observed["arrays"]) == 4
    assert observed["python_metadata_estimate_bytes"] > 0


def test_retained_observer_handles_cycles_and_zero_payload() -> None:
    value: list[Any] = [np.empty((0, 3), dtype=np.complex128)]
    value.append(value)
    observed = retained_payload(value)
    assert observed["array_payload_bytes"] == 0
    assert observed["unique_backings"] == 1


def test_foreign_backing_is_reported_as_unmeasured() -> None:
    with pytest.raises(ValueError, match="external array backing"):
        retained_payload(np.frombuffer(bytearray(80), dtype=np.float64))


def test_identity_preserves_endian_signed_zero_and_preconversion_bits() -> None:
    data = np.array([0.0, -0.0, 1 + 2**-40], dtype="<f8")
    big = data.astype(">f8")
    assert identity(data, "raw") == identity(big, "raw")
    assert identity(data, "raw")[3] != identity(data.astype("f4"), "raw")[3]
    flipped = data.copy()
    flipped[1] = 0.0
    assert identity(data, "raw")[3] != identity(flipped, "raw")[3]


def test_resource_context_exposes_limits_and_unknown_attribution() -> None:
    context = host_context()
    assert context["pointer_bits"] == 64
    assert context["backend_workspace_bytes"] == "unknown"
    assert context["swap_attribution"] == "unknown"
    assert "cgroup_memory_max" in context


@pytest.mark.parametrize("name", SCENARIOS)
def test_baseline_public_workloads_are_valid_and_reach_named_branches(name: str) -> None:
    case = scenario(name)
    result = simrecon.reconstruct_workflow(**case)
    assert np.isfinite(result.image).all()
    branches = result.parameters.branches
    if name.startswith("searched"):
        assert branches[0] == ("searched",) * 3
        assert branches[1] == (
            ("time0-reused",) * 3 if name.endswith("reuse") else ("searched",) * 3
        )
        assert {"coarse", "bracket", "parabola"} <= {e.kind for e in result.parameters.trace}
    elif name == "2d-search":
        assert branches[0] == ("searched",) * 2
        assert "cumulative-product" in {e.kind for e in result.parameters.trace}
    else:
        assert all(branch == "known" for row in branches for branch in row)
    kinds = {e.kind for e in result.bands.trace}
    if name in {"off1", "off2"}:
        assert "off-combination" in kinds
        affected = [dict(e.details) for e in result.bands.trace if e.kind == "off-combination"]
        assert {item["call_z"] for item in affected} == {0, 1, 2, 3}
        assert all(item["affected_z"] == 0 for item in affected)
    if name == "within":
        assert {"cubic-fit", "exposure-correction", "drift-correlation"} <= kinds
    if name == "between":
        assert {"between-build", "between-correction", "drift-correlation"} <= kinds
    if name == "fast":
        assert "between-build" not in kinds
        assert not np.any(result.bands.between_displacements_pixels)


def test_generator_is_deterministic_and_time_modulation_is_distinct() -> None:
    left = workload((2, 1, 2, 12, 16))
    right = workload((2, 1, 2, 12, 16))
    assert identity(left["specimen"], "specimen") == identity(right["specimen"], "specimen")
    assert not np.array_equal(left["specimen"][0], left["specimen"][1])


def test_retained_payload_includes_hidden_instance_cache() -> None:
    @dataclasses.dataclass(frozen=True)
    class Record:
        name: str

    result = Record("small metadata")
    object.__setattr__(result, "private_cache", np.zeros(123, dtype=np.complex128))
    assert retained_payload(result)["array_payload_bytes"] == 1968


def test_retained_payload_rejects_unmeasured_closure() -> None:
    captured = np.ones(8)
    with pytest.raises(ValueError, match="unsupported retained value"):
        retained_payload(lambda: captured)


def test_public_fingerprint_has_independent_typed_scalar_encoding() -> None:
    # Fixed byte witness: signed-zero components must survive scalar encoding.
    value = (False, -0.0, complex(1.0, -0.0), None, "é", b"")
    encoded = (
        b"protocol:21:RM84-public-values-v1tuple:1:6bool:1:0float64:8:"
        + bytes.fromhex("0000000000000080")
        + b"complex128:16:"
        + bytes.fromhex("000000000000f03f0000000000000080")
        + b"none:0:str:2:\xc3\xa9bytes:0:"
    )
    assert public_value_sha256(value) == hashlib.sha256(encoded).hexdigest()


@pytest.mark.parametrize(
    "left,right",
    [
        (False, 0),
        (0, 0.0),
        (0.0, -0.0),
        (complex(1, 0.0), complex(1, -0.0)),
        ((1, 2), [1, 2]),
        (("a", "bc"), ("ab", "c")),
        ((1, 2), (2, 1)),
        ((("x", 1), ("y", 2)), (("y", 2), ("x", 1))),
    ],
)
def test_public_fingerprint_distinguishes_exact_scalar_and_sequence_values(
    left: Any, right: Any
) -> None:
    assert public_value_sha256(left) != public_value_sha256(right)


def test_public_fingerprint_array_bits_shape_dtype_and_storage_alternatives() -> None:
    array = np.array([[0.0, -0.0], [1.0, 1.0 + 2**-40]], dtype="<f8")
    expected = public_value_sha256(array)
    for equivalent in (
        array.copy(order="F"),
        array.astype(">f8"),
        np.repeat(array, 2, axis=1)[:, ::2],
    ):
        equivalent.flags.writeable = False
        assert public_value_sha256(equivalent) == expected
    changed = array.copy()
    changed[0, 1] = 0.0
    for different in (changed, array.reshape(4), array.astype("f4"), array.T):
        assert public_value_sha256(different) != expected
    complex_array = np.array([complex(1, -0.0)], dtype=np.complex128)
    assert public_value_sha256(complex_array) != public_value_sha256(
        np.array([complex(1, 0.0)], dtype=np.complex128)
    )
    large = np.arange(131073, dtype=np.float64).reshape(3, 43691)
    assert public_value_sha256(large) == public_value_sha256(large.copy(order="F"))
    assert public_value_sha256(large) == public_value_sha256(large.astype(">f8"))
    assert public_value_sha256(np.empty((0, 3))) != public_value_sha256(np.empty((3, 0)))


def test_public_fingerprint_keeps_every_declared_record_value_and_repeated_occurrence() -> None:
    @dataclasses.dataclass(frozen=True)
    class Record:
        image: Any
        details: Any

    @dataclasses.dataclass(frozen=True)
    class OtherClass:
        image: Any
        details: Any

    image = np.arange(12, dtype=np.float64).reshape(3, 4)
    record = Record(image, (("overlap_index", 0), ("objective", 1.0)))
    expected = public_value_sha256(record)
    assert public_value_sha256(OtherClass(image.copy(), record.details)) == expected
    assert public_value_sha256((record, record)) == public_value_sha256(
        (record, OtherClass(image.copy(), record.details))
    )
    changed = image.copy()
    changed[1, 2] += 2**-40
    assert public_value_sha256(Record(changed, record.details)) != expected
    assert public_value_sha256(Record(image, record.details[::-1])) != expected
    assert (
        public_value_sha256(Record(image, (("overlap_index", 1), ("objective", 1.0)))) != expected
    )
    assert public_value_sha256((record,)) != public_value_sha256((record, record))


def test_public_fingerprint_rejects_unmeasured_objects_and_cycles() -> None:
    with pytest.raises(ValueError, match="unsupported public value"):
        public_value_sha256(object())
    cycle: list[Any] = []
    cycle.append(cycle)
    with pytest.raises(ValueError, match="cyclic public value"):
        public_value_sha256(cycle)
