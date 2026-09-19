# m60 — library-integration seams (decomposition)

Authority: `coffea-fastjet-conda-plan.md` §3 row m60; root prompt R25.3. Gaps measured in
`coffea-fastjet-conda-findings/` (`nano-behaviors:G1`, `graphed-seams:G2/G4/G5`, `fastjet-dask:G5`) and by
the lead's probes `<scratchpad>/m60/probe_m60.py`, `probe_x.py`, `probe_pq2.py` (re-run them for the figures).
Repo: `graphed-org/graphed`, branch `m60-integration-seams` stacked on `m59-awkward-idiom-parity`. Python only.
Frozen suite: `tests/frozen/frontend/m60/` for the backend-neutral items, `tests/frozen/awkward/m60/` for the
awkward-backed ones; helper prefix `m60_`; traceability `README.md`. Work-item prefix `integ-m60-`.

## Shape (where the decisions live today)

`graphed/session.py::Session` owns one `GraphStore` and the side tables keyed by that store's node ids; every
method that takes an `Array` reads `array.node_id` against ITS OWN tables. `record_op` alone checks that an
input belongs to the session. `graphed/provenance.py::capture` owns "which frame is the user's": the first
frame whose module name does not start with `graphed`. `graphed/array.py::Array.map`/`apply` and
`graphed/numpy/gufunc.py::apply_gufunc` own an opaque callable's identity: the `fn` param, `name or
fn.__name__`; each backend's `external_payload` derives the descriptor's content hash from that param (the
frozen toy backends do too, so identity travels in the PARAM). `graphed/awkward/io.py::_schema_form` owns a
parquet source's form (`ak.from_arrow_schema` of the first file's arrow schema); partitions are read with
`ak.from_parquet`. Stated in: the module docstrings of `session.py`, `provenance.py`, `awkward/io.py`.
Regenerate the sites: `grep -n "    def record_\|    def materialize\|    def form\|    def walk\|    def
provenance" python/graphed/session.py; grep -rn '"fn"' python/graphed; grep -n "_schema_form" -r python/graphed`.

## integ-m60-X — a Session refuses an Array it did not record

- X1. Every `Session` method that takes an `Array` refuses one recorded in another Session, recording nothing:
  the `record_*` family with `GraphedTypeError` (the message `record_op` gives today), the reading entries
  (`form`, `materialize`, `provenance`, `walk`) with `TypeError`. The method set comes from an instrument, not
  a list: the suite walks `inspect.getmembers(Session)` for public methods with an `Array`-typed parameter and
  fails on one it has no leg for.
- X2. Module-level verbs that take a session beside arrays (`compile_ir(session, *arrays)` and whatever the
  same walk of `graphed.__all__` finds) refuse the same way.
- X3. Controls: own-session calls record/read exactly as today (same nodes, same IR bytes); `record_op`'s
  existing refusal is unchanged.
- One guard on `Session`, called from every member — not a check per method.

## integ-m60-O — two callables never share a node by accident

- O1. Two DISTINCT callable objects recorded without `name=` over the same inputs are two nodes and evaluate
  to their own results — two lambdas, two closures of one factory, two same-named functions of different
  modules; through `Array.map`, `graphed.apply` and `graphed.numpy.apply_gufunc`; on the materialize path AND
  the durable path (`compile_ir` → pickle → `evaluate_ir`).
- O2. The SAME callable object recorded twice over the same inputs is one node; `apply(f, x)` still interns
  with `x.map(f)`.
- O3. A program whose un-named callables have pairwise-distinct `__name__`s records byte-identical IR to
  today; two builds of any program give byte-identical IR.
- O4. `name=` stays the caller's identity declaration: equal names intern, and its docstring says the name
  must encode everything that changes the callable's behaviour.
- Decision: identity is a per-Session first-seen ordinal on the derived name, carried in the `fn` param (the
  first object named `q` records `q`, the next distinct one `q#1`). No cloudpickle on the record path, no
  hashing of code objects (closures of one factory share code). Ceiling: under a concurrent build the
  assignment of ordinals to colliding callables follows thread interleaving.

## integ-m60-V — a wrapping library's frames are not the user's line

- V1. `graphed.provenance.register_internal(prefix)`: after it, `capture()` skips frames of module `prefix`
  and its submodules, so an op recorded inside a registered library points at the user's line that called
  the library. `prefix` matches whole dotted components (`"lib"` covers `lib` and `lib.sub`, not `libx`).
- V2. Idempotent, thread-safe, process-global; an unregistered helper module still gets its own line
  (the control), and the built-in `graphed*` rule is unchanged.
- V3. The `StageError` a registered library's op raises at run time points at the same user line (M6 path).

## integ-m60-P — a parquet source keeps awkward's record parameters

- P1. `from_parquet`'s recorded form equals the form eager `ak.from_parquet` gives the same file, for a file
  written by awkward (or by graphed's own `to_parquet`): named records, parameters on nested nodes, option
  and regular types; a behavior keyed on the record name resolves on the deferred array, and execution
  equals eager.
- P2. `columns=` still selects; a file written without awkward's metadata gets the form it gets today.
- P3. No event data is read at record time (row-group read counter or an unreadable-data witness), and
  `open_files=False` still opens no file beyond the first one's schema.
- Decision: the form is what awkward's OWN reader gives a zero-row parquet file of the dataset's arrow schema
  (`schema.empty_table()` written through pyarrow, read back with `ak.from_parquet`) — public routes only;
  `awkward._connect` stays unused, as `_write_augmented` already requires.

## integ-m60-E — `expand` is public

- E1. `graphed.expand` is `graphed.systematics.varied.expand`, in `__all__`; a third-party verb built on
  `record_external` and wrapped with it returns a `Varied` over a `Varied` operand and passes an unvaried
  call straight through (one node, same IR bytes as the bare call).

## integ-m60-D — docs

- `docs/architecture.rst`: "serialized by value" is true of the durable plan only; on a process-pool runner
  an External's callable must be importable (module-level). State that contract where the claim sits; the
  frontend design page documents `register_internal`, `expand`, O4's `name=` rule and X1.

## Non-goals

No per-partition scratch for External evaluators (`graphed-seams:G3`), no cloudpickle on the runner path, no
content hashing of opaque callables (M9 owns real hashing), no Rust change, no change to any frozen suite.

## Follow-through in the forks (after m60 is on the dev envs' pin)

fastjet `graphed-arm`: the cross-session refusal test, `register_internal("fastjet")`, `graphed.expand` by its
public name. uproot `graphed-form-mapping`: `register_internal("uproot")`. coffea A1 registers `"coffea"`.

## Size and commits

~150 src + ~350 test. Frozen suite: one commit. Implementation: two commits — X + O (session identity), then
V + P + E + D — each with its extra tests and docs.

## Gates

As m58 (`m58-decomposition.md` §Gates), freeze tag `freeze-m60`; TEST_SANITY runs every assertion behind a
test's first failing one by simulation.
