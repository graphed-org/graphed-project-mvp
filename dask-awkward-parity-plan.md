# graphed-awkward ↔ dask-awkward user-facing parity — analysis + prioritized plan

*Analyzed 2026-06-10 against `dask-contrib/dask-awkward@main` and the graphed-org MVP repos.
Execution order below is the USER-DIRECTED order (parquet I/O first), not the analysis order.*

## Verdict

`graphed-awkward` implements ~25 elementwise ops + 6 reducers + 17 structure functions in `gak`;
dask-awkward's surface is 19 reducers + ~41 structure functions + full ufunc support + behaviors +
partitioned I/O + a collection class. The skeletons already align — both infer forms via awkward's
typetracer and both are functions-over-arrays (`dak.*` mirrors `ak.*` exactly as `gak.*` does,
validating the M11 factorization) — and graphed **leads** in two areas: buffer-granular projection
(`project_buffers` + R15.8 counter-branch reads vs. their report-only `report_necessary_buffers`)
and content-hashed external payloads (correctionlib/ONNX; dask-awkward has none). The gap is
mostly table-driven breadth plus two deep features: **behaviors** and **partitioned I/O**.

Known internal gaps: the M11 frontend records ~85 canonical ufunc ops but `AwkwardBackend`
implements only 8 unary + 17 binary; the name-based `_BOUNDARY` set misclassifies inner-axis
reductions (`gak.sum(a, axis=1)` is partition-local and should be fusible under the M12
structural rule).

## Execution plan (user-directed order)

### M15 — Partitioned parquet I/O (P3.7, FIRST; spans graphed + both backends)

- **M15.1 (Common base in `graphed`.)** A backend-agnostic `graphed.parquet` module: deterministic
  file discovery (file / directory / glob / explicit list, sorted), metadata-only row counts and
  schema access (pyarrow as an optional extra — graphed itself stays numpy/awkward-free),
  partition construction with `steps_per_file` and an `open_files=False` **blind** mode using the
  first-class blind `Partition` of R7.9 (no file is opened at partition time), blind resolution,
  a deferred-source recording helper (lazy whole-dataset loader for `materialize`), and a
  deferred **write-plan builder**: compute-disabled returns a task graph of write tasks (each
  writes one output part and returns its path), compute-enabled runs that same plan (sequential
  reference runner by default, any R7 executor pluggable) — the two modes MUST be consistent
  (R15.4 semantics).
- **M15.2 (graphed-awkward specialization.)** `from_parquet` grows multi-file + `steps_per_file`
  + blind partitioning; the form comes from the **arrow schema alone** (schema → awkward form →
  typetracer; no event data read at construction — witness-tested). `read_parquet_partition`
  resolves blind partitions and reads **only the projected columns**.
  `to_parquet(array, destination, ...)`: per-partition compiled-IR evaluation (R7.8 — no
  re-recording) of the array's graph, writing only the **projected** columns; multi-source arrays
  rejected loudly; compute-disabled/enabled consistency pinned bit-for-bit.
- **M15.3 (graphed-numpy specialization — RECTILINEAR ONLY.)** Same surface, restricted to
  rectilinear data: every parquet column must be a primitive (no list/struct columns — jagged
  data is graphed-awkward's job; the refusal is a clear record-time TypeError naming the column).
  `from_parquet` records a record source (columns → `NumpyForm` fields); `to_parquet` writes 1-D
  arrays (single column) or record outputs. The M5 field-touch projection wires the read list.
- *Note:* this **amends the R16.7 deferral** for graphed-numpy: the user pulled parquet I/O
  (alone) into the MVP on 2026-06-10; zarr/store and the rest of P3.9/P4 stay Phase 2.

### M16 — P0: close the internal gaps (foundation)

1. Complete `AwkwardBackend._UNARY/_BINARY` to the full M11 canonical ufunc set (~60 rows;
   awkward arrays take numpy ufuncs; typetracer infers forms).
2. Apply the M12 structural rule to awkward reducers: `gak` reducers record
   `reduction = axis in (None, 0)`; retire the name-based `_BOUNDARY` reducer list. Frozen
   witness: `gak.sum(a, axis=1)` records a fusible op, `gak.sum(a)` a boundary node.
3. Add the 13 missing reducers (`mean/std/var/min/max/prod/count_nonzero/ptp/moment/softmax/
   corr/covar/linear_fit`) through the shared `apply` dispatch.

### M17 — P1: structure-op parity

4. ~24 missing structure functions through the same dispatch: `sort`, `mask`, `pad_none`,
   `is_none`, `singletons`, `unflatten`, `broadcast_arrays`, `ravel`, `unzip` (per-field recorded
   ops), `full_like`, `nan_to_num`, `isclose`, `argcartesian`/`argcombinations`, `run_lengths`,
   `to_regular`/`from_regular`, `without_field`, `values_astype` wrapper, `to_list` (materialize
   sugar). Plus list-of-strings `__getitem__` on the base proxy (one recorded record-subset op).
5. Projection regression pins: structure-only touches (`pad_none`, `mask`) flow truthfully
   through `project`/`project_buffers`.

### M18 — P2: behaviors (the HEP feature)

6. `gak.with_name` + behavior registration on `AwkwardBackend(behavior=...)`: name+behavior
   carried through the typetracer in `op_form`; the `field` op's evaluation falls back from
   getitem to getattr so behavior properties (`muons.pt`, `.mass`) work lazily at record time and
   in evaluation — frozen-tested against `vector`'s `Momentum4D` (the coffea pattern).
   `attrs`/`with_parameter`/`without_parameters` ride along. Functions + plain attribute access
   only — no proxy changes.

### M19 — P3.8: conveniences (LAST)

7. `gak.fields/type_of/backend_of` (form introspection), `head(n)`/`sample` (slice + materialize
   partition 0).

## Phase 2 — explicitly deferred, MUST NOT be built in the MVP

- **`__awkward_function__` dispatch (`ak.sum(garr)` routing)** — *user decision 2026-06-10: this
  is an MVP and dispatch is largely syntactic sugar; users write `gak.*`.* Also keeps the
  factorization rule untouched (no hooks, no proxy for awkward).
- `repartition`/`divisions` (the plan already excludes adaptive reshaping), `persist`,
  `Scalar`/`Record` collection classes, `__setitem__`/`__delitem__` sugar (`with_field`/
  `without_field` cover it), `.str` accessor, `to_dataframe`/dask interop, tuple `__getitem__`,
  `enforce_type`/`to_packed`, text I/O, row-group-exact parquet range reads (MVP reads
  column-projected files and slices entry ranges).

## Already at or above parity (no work)

Column projection (`project` ↔ `report_necessary_columns`); buffer projection (`project_buffers`
↔ `report_necessary_buffers`, plus counter-branch read translation they lack); content-hashed
correctionlib/ONNX externals; typetracer form inference; compiled-IR execution; non-iterability.

## Process wrapper (binding for M15–M19)

Gated milestones in the order above; frozen suites authored FIRST and verified non-vacuous in
every touched repo (`graphed` for the common parquet base and the list-of-strings getitem;
`graphed-awkward`; `graphed-numpy` for its parquet specialization); the standard gates (ruff,
mypy --strict, ≥90% branch coverage from the frozen suites, determinism, sphinx -W);
`.graphed/M1x/` attempts + state bookkeeping; one commit per repo per milestone; downstream + fork
regression after each; root prompt extended (R17, including the Phase-2 deferrals and the R16.7
parquet amendment) at the end. pyarrow enters as an optional extra + dev dependency; frozen I/O
suites `importorskip` pyarrow so matrix cells without wheels stay green without weakening tests.
