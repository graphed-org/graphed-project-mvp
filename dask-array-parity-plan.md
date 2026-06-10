# graphed-numpy ↔ dask.array user-facing parity — analysis + prioritized plan

*Analyzed 2026-06-10 against `dask/dask@main` (`dask/array/__init__.py` + `core.py`) and the
graphed-org MVP repos (`graphed`, `graphed-numpy`, `graphed-core`, `graphed-exec-local`).*

## Verdict

`graphed-numpy` today implements **8 canonical ops** (add/sub/mul/div, field, filter, sum, map)
over 1-D "bags" with **no shape model** (`NumpyForm` carries only a dtype). dask.array's
user-facing surface is roughly **250 exported functions plus ~60 `Array` methods/properties** over
a chunked N-D model. About 70% of that surface is reachable within our architecture by mechanical,
table-driven extension; the remaining ~30% (N-D chunking, rechunk, distributed linalg/FFT,
map_overlap, zarr/HDF5 storage) presupposes an execution geometry we deliberately do not have and
is **deferred to Phase 2** (see below).

Process constraint: the plan's M2 guardrail says graphed-numpy is a *trivial seam-prover only*, so
parity work is a sequence of **new post-MVP gated milestones (M11–M14)** — new frozen suites
(`tests/frozen/m11..m14/`), no edits to anything under `tests/frozen/**`, opt-in wherever a frozen
test pins a default (e.g. `describe()` keeps its `vector[<dtype>]` prefix for 1-D vectors).

## Where the gap is

**Internal gap first:** the frontend `Array` proxy already records ~25 canonical ops (full
arithmetic, comparisons, boolean ops, a dozen ufuncs via `__array_ufunc__`, field/getitem/filter/
map/reduce) — but `NumpyBackend` implements only 4 arithmetic ops plus field/filter/sum.
graphed-numpy does not even cover its own frontend.

**dask.array surface by category:**

| Category | dask surface | graphed-numpy status |
|---|---|---|
| Ufuncs/elementwise | ~95 (`exp`, `log`, `clip`, `isnan`, …) + `__array_ufunc__` | 4 implemented; ~25 recordable; protocol exists |
| Reductions | ~33, axis/keepdims-aware + nan-variants + generic `reduction()` | `sum`, whole-array only |
| Array properties | `shape/dtype/ndim/chunks/T/real/imag/blocks…` | none (no shape in form) |
| Creation | ~25 (`zeros`, `arange`, `from_array(chunks=)`, `random`, `from_zarr`…) | `from_array`, `from_record` |
| Manipulation/routines | ~75 (`concatenate`, `stack`, `where`, `unique`, `histogram`, `take`…) | none |
| Indexing | slices, fancy, boolean, `__setitem__`, `vindex`, `.blocks` | boolean `filter` + field only |
| Escape hatches | `map_blocks`, `blockwise`, `apply_gufunc`, `map_overlap` | `map` (single-input) |
| Linalg/FFT/ma/stats | `linalg`, `fft`, `ma`, `stats`, `einsum`, `matmul` | none |
| Chunk model | `chunks`, `rechunk`, `unify_chunks`, `compute_chunk_sizes` | axis-0 `Partition` only |
| Execution UX | `compute/persist/visualize/store/to_zarr/to_hdf5` | `materialize`, exec-local, `to_dot` |

**Structural insight:** dask's differentiator is the chunked N-D model, not the function count. Our
model — 1-D source partitions + fused stages — matches dask.dataframe's geometry more than
dask.array's. Almost everything above operates *within a partition* once recorded (elementwise,
per-row manipulation) or *across partitions via tree reduction* (reductions, histogram, unique),
both of which the graphed IR and executor already do. Only rechunk, cross-chunk reshape, scaled
matmul/tensordot/linalg/FFT, and map_overlap genuinely need N-D chunk geometry.

## Prioritized plan

### P0 → milestone M11 — shape-aware form + full elementwise tier

1. `NumpyForm` gains a real `(shape, dtype)` with `None` for the partitioned axis-0 length, inferred
   by evaluating ops on zero-length **meta arrays** so numpy's own promotion/broadcasting machinery
   does the type inference (mirrors dask's `_meta` and the project's §A.2 "reuse the host library's
   inference" rule). Frontend `Array` exposes `.shape/.dtype/.ndim`, delegated to the form (with
   fallback to field recording so backends whose forms lack them are unaffected).
2. `NumpyBackend` implements **every op the frontend already records** (~21 missing), then
   `_UFUNC_TO_OP` in `graphed/array.py` is extended to the full single-output ufunc list (~90
   names). Table-driven in both repos.
3. `__array_function__` on `Array` so `np.sum(a)`, `np.where(c, a, b)`, `np.concatenate([...])`
   record ops instead of erroring (dispatch by function `__name__`, keeping graphed numpy-free).
   Optimizer caveat: new ops default to non-symmetric; any op claimed symmetric must be added to
   graphed-core's shared `SYMMETRIC_OPS`/`IDENTITY_TOKENS` with witness tests (R2.2/R0.10).

### P1 → milestone M12 — axis-aware reductions + creation

4. `sum/prod/mean/std/var/min/max/any/all/argmin/argmax` with `axis=`/`keepdims=`, nan-variants,
   `cumsum/cumprod`, method forms on `Array`. Implemented **tree-reducible**: mean/std/var carried
   as (count, sum, sumsq) monoids that drop straight into the M7 process/combine/empty model; a
   generic `reduction(chunk, combine, aggregate)` exposed (dask's `da.reduction` ≡ our plan triple).
5. Creation: `zeros/ones/full/empty(+_like)`, `arange`, `linspace`, `from_array(..., chunks=n)`
   producing axis-0 partition metadata, and a `random` namespace seeded per-(source, partition) so
   the determinism gate stays green.

### P2 → milestone M13 — manipulation + indexing in the partitioned model

6. `__getitem__` parity along axis 0 (slices, integer arrays, boolean masks — boolean is the
   existing `filter`) plus in-partition N-D ops: `reshape` (non-axis-0), `transpose/T`, `swapaxes`,
   `squeeze`, `expand_dims`, `ravel`, `astype`, `clip`, `round`, `take`, `where`.
7. Cross-array combination: `concatenate/stack/hstack/vstack` (axis-0 concatenate = partition-list
   concatenation), `diff`, `isin`, `searchsorted`, and the tree-reducible analytics:
   `histogram/histogram2d/histogramdd` (fixed bins → counts array), `unique`, `bincount`.

### P3.8 → milestone M14 — escape hatches

8. Generalize `map` into a multi-input `blockwise`/`map_partitions` analogue, still recorded as an
   `External` with a `PayloadDescriptor` (preservation semantics hold), with gufunc-style signature
   for form inference (`apply_gufunc` analogue).

### Phase 2 — explicitly deferred (do NOT build now)

- **P3.9** — `store`/`to_zarr`/`from_zarr` and in-partition `matmul/dot/tensordot`. *(User decision
  2026-06-10: Phase 2.)*
- **P4** — N-D `chunks`/`rechunk`/`unify_chunks`, cross-chunk `reshape`, distributed `linalg`/`fft`,
  `map_overlap`/halo exchange, `__setitem__`, masked arrays, `persist` (needs a distributed memory
  tier — Phase 2 executors), CuPy-style backend dispatch. All presuppose N-D block geometry;
  adopting it would mean generalizing `Partition`, the stage planner, and tree reduction
  project-wide — a plan-level decision, not a backend feature.

## Process wrapper (binding for M11–M14)

One gated milestone per tier. For each: frozen suite authored first under `tests/frozen/m1X/`
(verified non-vacuous against the pre-milestone code), implementation second, gates (`ruff`,
`mypy --strict`, coverage ≥ 90% from the frozen suite, determinism) third; `.graphed/M1X/attempts.md`
+ `state.json` updated; one commit per repo per milestone. Changes land in `graphed` (frontend
tables, `__array_function__`, properties), `graphed-numpy` (backend, projection, helpers), and
minimally `graphed-core` (only if new symmetric/identity rewrite rules are claimed). The root
prompt is updated afterward to bind the new surface. Frozen m2/m5 pins respected throughout
(`describe()` prefix, default behaviors).
