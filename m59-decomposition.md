# m59 — awkward-idiom parity: multi-axis keys, numpy-scalar dtypes, nested method outputs (decomposition)

Authority: `coffea-fastjet-conda-plan.md` §3 row m59 (review-clean r4); root prompt R25.2. Gaps measured in
`coffea-fastjet-conda-findings/` (`nano-behaviors:G2/G3`, `nano-factory-seam:G5`, `coffea-dask-surface:G1`).
Repo: `graphed-org/graphed`, branch `m59-awkward-idiom-parity` stacked on `m58-projection-declarations`.
Python only — `ParamValue` stays `int | float | bool | str` (the Rust store enforces that set).
Frozen suite: `tests/frozen/awkward/m59/` (numpy-backend legs, if the subtree split requires it, under
`tests/frozen/numpy/m59/`), helper prefix `m59_`, traceability `README.md`. Work-item prefix `integ-m59-`.

## Shape (where the three decisions live today)

`graphed/array.py::Array` is the idiom-neutral frontend: it turns Python syntax into `Session.record_op`
calls whose params are `ParamValue`s, and never imports numpy or awkward. `Array.__getitem__` owns which keys
are accepted and whether the op is a partition-axis BOUNDARY (`slice`/`index` record `reduction=True` because
they consume or restructure axis 0). `array.py::_as_param` owns how a scalar operand becomes a param — today
`float(value)` for anything that is not `bool | int | str`. Each backend owns evaluation and form inference
(`graphed/awkward/_ops.py::apply` + `_scalar_operands`, `AwkwardBackend.op_form`; the numpy backend's
equivalents). `AwkwardBackend.method_outputs` owns what a behavior method may return, and
`array.py::_record_method` records one `method` node per output with an `index` param.
Regenerate the sites: `grep -n "_as_param\|def __getitem__\|def _record_method" python/graphed/array.py;
grep -n "def method_outputs\|def _scalar_operands" -r python/graphed`.

## integ-m59-I — multi-axis keys

- I1. `array[key]` accepts a tuple key whose members are `slice`s with int fields, `int`s, `None` (newaxis) and
  at most one `Ellipsis`, PROVIDED the partitioned axis is left whole (the first member is `slice(None)` or a
  leading `Ellipsis`). The recorded form is the form eager awkward gives the same key, and execution equals
  eager bit-for-bit — `a[:, :2]`, `a[:, 0]`, `a[:, -1]`, `a[:, ::2]`, `a[:, :, None]`, `a[:, None, :]`,
  `a[..., 0]`, on jagged arrays and on records of jagged fields.
- I2. Such an op is NOT a boundary: it fuses like any per-row op, and a partitioned run (≥ 2 partitions) equals
  the unpartitioned one bit-for-bit.
- I3. A tuple key that would consume or restructure the partitioned axis (first member an `int`, a non-full
  `slice`, or `None`) is refused at record time with a `TypeError` naming the chained spelling
  (`a[1:3][:, 0]`); `bool` members, non-int slice fields, `Array` members and a second `Ellipsis` are refused.
- I4. Interning: equal keys give the same node, different keys different nodes; two builds give byte-identical IR.
- I5. A runtime index error (`a[:, 0]` over an empty row) surfaces as the executor's `StageError` pointing at
  the user's line, not at record time.
- I6. The numpy backend evaluates the same keys with numpy semantics (the key kinds are common to both idioms).
- Controls: every key `Array.__getitem__` accepts today records the same op, params and boundary flag.

## integ-m59-S — a numpy scalar operand keeps its dtype

- S1. For binary arithmetic, comparison and bitwise operators and ufuncs with a scalar operand on either side,
  the recorded form's dtype and the executed result equal eager awkward's, over {bool, int64, float64} arrays ×
  {`np.uint64`, `np.int32`, `np.float32`, `np.bool_`} scalars (the expression `PackedSelection` packs bits
  with is `mask * np.uint64(1 << bit)`).
- S2. Values round-trip exactly: `np.uint64(2**63)`, `np.uint64(2**64 - 1)`, `np.float32(0.1)`.
- S3. Python `bool`/`int`/`float` operands record exactly as today (same params, same IR bytes).
- S4. Interning: `np.uint64(1)`, `np.int32(1)` and `1` are three nodes; equal dtype + value is one node.
- S5. The frontend still imports neither numpy nor awkward (the dtype travels as a `str` param).

## integ-m59-M — nested method outputs

- M1. A behavior method whose eager result is a NESTED tuple of arrays records, and returns the same nesting of
  `graphed.Array`s; every leaf has the eager leaf's form and executes to it bit-for-bit
  (`metric_table(other, return_combinations=True)` is the motivating shape: `(metric, (a, b))`).
- M2. Single-array and flat-tuple returns record exactly as today (same nodes, same IR bytes).
- M3. A non-array leaf anywhere in the nest is refused with the existing refusal's message shape.
- M4. Interning: the same call twice gives the same leaf nodes; distinct leaves are distinct nodes.

## Non-goals

No `Array` members inside a tuple key, no boundary tuple keys, no new `ParamValue` kinds, no Rust change, no
change to any existing frozen suite.

## Size and commits

~250 src + ~300 test. Frozen suite: one commit (test-author). Implementation: two commits — I (keys) and
S + M (scalar dtype, nested outputs) — each with its extra tests and docs (the frontend/awkward design pages'
indexing and operator sections).

## Gates

As m58 (`m58-decomposition.md` §Gates), freeze tag `freeze-m59`. TEST_SANITY additionally runs, by simulation on
the unimplemented tree, every assertion that sits behind a test's first failing one.
