# systematics-vary-plan r13 — review round 5, FACTS / HALLUCINATION lens

- **Lens:** facts / hallucination audit — every `file:line` anchor (body + Anchors appendix), every
  measured/probe claim, every citation into the two research docs, every prior-art claim, every
  count/arithmetic statement.
- **Plan revision reviewed:** r13 (`systematics-vary-plan.md`, 2512 lines, read in full).
- **Date:** 2026-07-30.
- **Verification roots used** (nothing was read from the stale submodules in the workdir):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (consolidated `graphed`; its built
    extension + `.venv` were used to re-run the in-graph probes)
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42` (`graphed-executors`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef` (branch `graphed-mvp`)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06,
    wwz4l@cc71718, WRemnants@c5be6c60, narf@7d73361, mkShapesRDF@b89a71f}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf`
  - probe environments: `uv run --no-project` with boost_histogram **1.8.0**, awkward **2.12.0**,
    pyarrow **25.0.1**, cloudpickle, CPython **3.12.10**
- **Coverage:** 250 distinct `file:line` citations appear in the document; every high-frequency
  target was opened at the cited lines (`array.py`, `session.py`, `execute.py`, `aggregate.py`,
  `boost.py`, `_spec.py`, `shuffle.py`, `projection.py`, `provenance.py`, `write.py`,
  `awkward/io.py`, `awkward/functions.py`, `numpy/{array,io,creation,__init__}.py`,
  `core/plan.py`, `checkpoint/{store,runner}.py`, `debug/{errors,runner}.py`,
  `preserve/bundle.py`, `src/{store,node,lib}.rs`, `src/optimizer/{mod,engine}.rs`, the frozen
  m4/m05/m6/m9/m23/m24/m29/m40 tests, all four repos' `pyproject.toml`/`ci.yml`,
  `scripts/run-tests.sh`, uproot `RNTuple.py`/`TBranch.py`/`_cascadetree.py`/`_graphed_write.py`,
  `ops_catalog.md`, `graphed-root-prompt.md`). Nine measured probes were re-run from scratch.

**Result: two HIGH findings, both in §2.3d's module-verb disposition and its m48 anchor; the rest
is LOW/NIT. Every other measured number, anchor, citation and prior-art claim I checked
reproduced — including the ones the plan itself flags as delicate.**

---

## Findings

### 1. HIGH — §2.3d / m48 anchor: `graphed.evaluate_ir` can never receive a `Varied`, so its bound refusal and its named positive control are both unimplementable

**Section:** §2.3(d); m48 frozen anchor "§2.3d module-verb dispositions + §2.2's reserved
`Array`-protocol names".

**Claim as written (§2.3d):** "`graphed.compile_ir`, `graphed.evaluate_ir` and
`graphed.aggregate_plan` **refuse** a `Varied` output with an error naming `graphed.universe` —
they consume `arr.node_id`/`arr.session` directly (`execute.py:70`, `aggregate.py:86`)". The m48
anchor then freezes: "every refusing verb (`join`, `repartition`, `pack_key`, `shuffle_plan`,
`join_plan`, `compile_ir`, `evaluate_ir`, `aggregate_plan`) raises a `graphed` error naming
`graphed.universe`, **with the positive control that the same verb on a plain `Array` still
works**".

**Measured** (`/private/tmp/claude-501/graphed-latest`):

```
python/graphed/execute.py:85-91
def evaluate_ir(
    compiled: CompiledGraph | bytes,
    backend: Backend,
    sources: Mapping[str, object],
    *,
    externals: Mapping[str, Callable[..., object]] | None = None,
) -> list[object]:
```

`evaluate_ir` takes **no `Array` parameter at all** — it consumes a compiled artifact, a backend
and a source binding. It never reads `arr.node_id` or `arr.session`; the two evidence anchors the
sentence supplies cover only the other two verbs (`execute.py:70` is `ids = [arr.node_id for arr
in outputs]` inside `compile_ir`; `aggregate.py:86` is `session = outputs[0].session` inside
`aggregate_plan` — both re-read and confirmed). There is therefore no "varied output" for
`evaluate_ir` to refuse, and the frozen positive control is false in the other direction too:
`evaluate_ir(plain_array, …)` does not work either, because a plain `Array` is not a
`CompiledGraph`.

**Why it matters:** the m48 anchor is table-driven and each row is supposed to carry the
refusal + a passing positive control. The `evaluate_ir` row cannot be written truthfully; a
test-author will either invent a fake positive control (freezing nonsense) or file a dispute
mid-freeze — the exact mid-freeze discovery §4.1's `full_like` note and §2.6's `fill`-is-positional
note exist to prevent.

**Suggested fix:** drop `evaluate_ir` from the refusing set in §2.3d and from the m48 anchor list;
the honest statement is that `evaluate_ir` is *out of the Array-consuming surface entirely* (a
one-line note next to the compile/aggregate refusals, with `execute.py:85-91` as the anchor). If
some guard is still wanted for `evaluate_ir(varied_as_compiled, …)`, bind it separately and
without a plain-`Array` positive control.

---

### 2. HIGH — §2.3d's exhaustiveness discovery rule provably misses 4 of the 10 verbs §2.3d itself disposes; "the table cannot silently miss a verb" is false as bound

**Section:** §2.3(d) ("Exhaustiveness is kept by a DISCOVERY RULE, not by this literal list … the
m48 anchor enumerates `graphed.__all__` dynamically, filtered to callables whose FIRST positional
parameter is annotated `Array`, and asserts every discovered verb carries a disposition — so a
verb added later cannot arrive undisposed"); repeated in the m48 anchor ("driven by the §2.3d
**discovery rule** (dynamic over `graphed.__all__`, filtered to `Array`-first callables — so the
table cannot silently miss a verb)").

**Measured** — first-parameter annotations of every callable in `graphed.__all__`
(`python/graphed/__init__.py:27-58`), extracted with `ast` from the pinned root:

| verb | first parameter | annotation | discovered by the bound filter? |
|---|---|---|---|
| `repartition` | `array` | `Array` | yes |
| `pack_key` | `array` | `Array` | yes |
| `join` | `left` | `Array` | yes |
| `shuffle_plan` | `output` | `Array` | yes |
| `join_plan` | `output` | `Array` | yes |
| `aggregate_plan` | `*outputs` (VAR_POSITIONAL) | `Array` | ambiguous |
| **`compile_ir`** | `session` | **`Session`** | **no** |
| **`evaluate_ir`** | `compiled` | **`CompiledGraph \| bytes`** | **no** |
| **`read_columns`** | `arrays` | **`Sequence[Array]`** | **no** |
| **`apply`** | `fn` | **`Callable[..., object]`** | **no** |

(`python/graphed/shuffle.py:68,84,92,142,208`; `python/graphed/execute.py:54,85`;
`python/graphed/projection.py:109`; `python/graphed/array.py:397`; `python/graphed/aggregate.py:68`.)

So the rule discovers 5 (or 6) of the 10 verbs the section disposes, and silently misses
`compile_ir`, `aggregate_plan`'s sibling `read_columns`, `apply`, and `evaluate_ir` — including
**both** of the refusals §2.3d says protect against `Varied`'s field-access `getattr` "silently
compiling nonsense", and **both** expanding verbs. A frozen gate built literally on this rule
passes while the most consequential dispositions are unasserted, and a future `Array`-consuming
verb added with a `Sequence[Array]` or non-`Array`-first signature (the house has two such
already) still arrives undisposed. `aggregate_plan` is additionally ambiguous: its first parameter
is a `*args`, which "first positional parameter" does not obviously cover — an implementer choice
the plan does not bind.

**Suggested fix:** re-bind the discovery predicate to what actually matches the measured surface —
e.g. "any callable in `graphed.__all__` whose signature mentions `Array` in **any** parameter
annotation (including `Sequence[Array]`, `*args: Array`) **or** that appears in the plan's
freeze-time disposition list" — and state the freeze-time discovered set as a literal floor
(count + names) so the gate is non-vacuous, exactly as §2.3c does for gak. Drop or re-word
"cannot silently miss a verb", which is not true of any purely annotation-based filter over this
surface.

---

### 3. LOW — §8.2(i)'s three sha256 digests are not reproducible as stated (the payload is unnamed) — the same defect r13 withdrew one row earlier for §6.4e

**Section:** §8.2(i) and its Anchors row ("measured r13: one identical `(3, frozenset({5
labels}))` payload cloudpickled under `PYTHONHASHSEED` 1 / 7 / 12345 → sha256[:16]
`b33099e93b65735c` / `97af80b50319fead` / `d0001d6ad5eb8f3b`").

**Measured:** the substantive claim is TRUE and reproduces qualitatively — cloudpickling one
identical `(3, frozenset({...5 label strings...}))` payload under `PYTHONHASHSEED` 1 / 7 / 12345
gives three distinct digests (`b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831` for my
label set). But the *specific* triple in the plan cannot be reproduced by anyone, because neither
the five label strings nor the cloudpickle version are recorded. R13 withdrew the §6.4e sha256 row
for precisely this reason ("they named no array and are not reproducible") and then reintroduced
the pattern in §8.2(i) in the same revision.

Note the downstream chain is verified independently: `OpSpec.identity()` returns
`b"opaque\0" + base64.b64decode(self.blob_b64)` (`python/graphed/core/plan.py:72-77`) and
`DurablePlan.task_id` folds it (`plan.py:164-176`) — both re-read.

**Suggested fix:** either name the five labels + the cloudpickle version in the anchor row, or
replace the digest triple with the reproducible statement ("three distinct digests across three
seeds; the payload is any `frozenset` of ≥2 strings") plus the recipe.

---

### 4. LOW — §8.2's "enumerated every `#[pymethods]` fn in `src/lib.rs:106-543`" is an incomplete enumeration (the conclusion it supports is nevertheless true)

**Section:** §8.2(i) and the corresponding Anchors row.

**Measured** (`/private/tmp/claude-501/graphed-latest/src/lib.rs`, 554 lines): the cited span
`:106-543` contains three `#[pymethods]` blocks, not one. The listed 15 names are exactly the
`PyGraphStore` block; the span also holds `PayloadDescriptor`'s accessors (`new` `:106`, `kind`
`:127`, `content_hash` `:131`, `framework` `:135`, `version` `:139`, `io_schema` `:143`,
`preprocessing_ref` `:147`) and `PyIncrementalReducer`'s (`new` `:473`, `step` `:481`,
`watermark` `:488`, `total_work` `:496`, `canonical_count` `:504`, `finalize` `:515`) — none of
them listed.

The **conclusion holds**: none of the omitted methods exposes a record→reduced id map either.
`reduce`/`reduce_incremental`/`reduction_report` return `(store, HashMap<String, usize>)` and the
map is built by `report_to_map` from six counters (`src/lib.rs:365-415,445-457`); the `remap`
vector is local to `dead_code_elimination` and only `out_idx` escapes
(`src/optimizer/mod.rs:88-116`, re-read). So the m49 "new read-only accessor" target is correctly
motivated — only the completeness phrasing overstates what was enumerated. (r11 made the mirror
correction for `src/node.rs:41-70 → :41-85`; the same standard applies here.)

**Suggested fix:** say "every `#[pymethods]` fn on `GraphStore` (`src/lib.rs:159-416`), plus the
`PayloadDescriptor` and `IncrementalReducer` blocks, none of which returns an id mapping".

---

### 5. LOW — pyarrow version is stated inconsistently across two same-revision anchor rows

**Section:** Anchors appendix — the §6.4e row says "re-measured r13, awkward 2.12.0 / **pyarrow
25.0.0**"; the §6.4g footer row says "re-measured r12 (awkward 2.12.0 / **pyarrow 25.0.1**) …
`parquet-cpp-arrow version 25.0.1`"; §1.1 and §6.4b also cite "pyarrow 25.0.0".

**Measured:** a clean `uv run --no-project --with "awkward>=2.12" --with pyarrow` environment
resolves **awkward 2.12.0 / pyarrow 25.0.1**, and every claim in both rows reproduces there:
`ak.to_parquet` vs `pq.write_table(ak.to_arrow_table(a))` differ in bytes for a record array, a
list-of-float array and a flat numeric array; the arrow path drops `awkward_array_metadata` in all
three; `ak:parameters` appears only for the record array (array-dependent, as the row says);
`ARROW:schema` always present; `"metadata" in signature(ak.to_parquet)` → `False`; repeat writes
of one array in one process are byte-identical; `ParquetFile(p).metadata.created_by ==
"parquet-cpp-arrow version 25.0.1"`.

Given that r12 already corrected one version-attribution artifact ("`24.0.0` was a foreign
environment"), leaving two different pyarrow versions attached to r13-dated probes of the same
subsystem is a live R0.11 reproducibility snag — a reader cannot tell which environment the KV
claim was made in.

**Suggested fix:** pin one version string across §1.1/§6.4b/§6.4e/§6.4g and the two anchor rows
(25.0.1 is what a clean resolve gives today), or state the range over which both were checked.

---

### 6. NIT — four cited ranges are one to a few lines short of the content they support (all content-true)

Each verified by opening the file at the cited lines:

- `histograms.py:39-42` for "fingerprint rounds again" — `fingerprint` is at `:40-43`; the
  `hexdigest()[:16]` line is `:43`, just outside the range
  (`/private/tmp/claude-501/graphed-corpus-latest/src/graphed_corpus/histograms.py`, identical in
  the vendored `graphed tests/_corpus/…`).
- `python/graphed/numpy/__init__.py:578-598` for "all in `__all__`" (§4.1 / Anchors) — the list
  runs `:578-601`; `zeros` is at `:599` and `zeros_like` at `:600`, i.e. the cited range excludes
  one of the six donor-free constructors it is cited for.
- `python/graphed/numpy/io.py:158-173` cited as "the numpy idiom having its own 1-D-capped
  implementation" (§6.4a) — that span is `_WritePart.__call__`'s tail (which does carry the cap at
  `:164-165`); the `to_parquet` function itself is at `:182`. The separate `:163-171` anchor row
  for the cap is exact.
- `projection.py:109-121` cited for "`read_columns` returns its read set SORTED" (§8.2(i)) — the
  `return tuple(sorted(needed))` is at `:147`; the cited range is the def + docstring (which does
  say "sorted" at `:111`).

**Suggested fix:** widen/repoint these four; none changes a requirement.

---

## Verified clean (checked and confirmed — recorded so a later round need not re-do it)

**Rust / core.** `src/store.rs:73-88` (`intern`, lookup-then-push), `:147-156` + `:152-153`
(`mark_output` de-dup); `src/node.rs:39-41` (NodeKey identity), `:102-103` (`is_boundary =
!matches!(Op)`), `:41-85` (the whole enum — variant heads measured at 42/46/51/56/64/72/81, exactly
as the row claims); `src/optimizer/engine.rs:7-13` (the O(N)-extractor note, quote verbatim at
`:9-11`), `:54-56` (`boundary_from_token`); `src/optimizer/mod.rs:1-11` (pipeline docstring),
`:88-116` (DCE + the never-returned `remap`).

**Frontend.** `array.py:127-128` (`__slots__`), `:137-143` (`node_id`/`session` are plain
properties), `:156` (`__array_ufunc__`), `:245-275` (bitwise set), `:332-335` (underscore-only
`__getattr__` guard), `:344-371` (`__getitem__` accepts Array/str/list/slice/int, `TypeError`
otherwise at `:369-371`), `:374-375` (`filter` has NO check), `:377-379` (`map`), `:374-391` (four
public methods), `:397-410` (`graphed.apply`, incl. the verbatim "With one array this IS
`Array.map` (interns with it)" at `:403`), `:54` (`rint` is a ufunc entry only);
`session.py:30,113-125,133/140,142/168,170/183,185/204,206/242,245-252,269` — including the
**FIVE** `_array_cls` construction sites and the measured fact that there is no `_array_cls` call
site outside `session.py`; `provenance.py:26-33,66-79`; `projection.py:109-147`;
`shuffle.py:5-8,84,89,92-96,142,155,170,208,220,232` (first-Exchange / first-Join);
`execute.py:36-45,54-70,85-126` (bare dispatch loop, no `try`/`except`, `:109` op dispatch,
`:110-115` stage members, `:126` `[vals[o] for o in store.outputs()]`);
`aggregate.py:44-65,86,89-93,95-97,101`; `core/plan.py:72-90,164-176,286-301`;
`checkpoint/store.py:31-41,62-73`; `checkpoint/runner.py:100-109`;
`debug/errors.py:29,32-81,75-78,80-81`; `debug/runner.py:6-7,37,57-69`;
`preserve/bundle.py:103-123,206-210`; `write.py:32-43,77-79`; `parquet.py:77,107,118`;
`awkward/io.py:111-127` (incl. `(out,) = evaluate_ir(...)` at `:121`), `:157-185,206-216,239,260,274`;
`awkward/__init__.py:14,17-31,30`; `numpy/array.py:71-74,92-190,132-136` (26 public names measured);
`numpy/io.py:163-171`; `numpy/creation.py:27-28,31-75`.

`grep "StageError("` over `python/graphed/` returns **exactly two** hits (`debug/errors.py:29`,
`debug/runner.py:37`) — the §8.2 "NEW work" premise is exact. `graphed` ships no `Executor`
implementation (only Protocols at `core/execution.py:228,316`) and its only cross-process frozen
test is `tests/frozen/debug/m6/test_process_boundary.py` — both claims measured true.
`execution.py:276-284` (AddressTable ephemeral-out-of-hash precedent) is real and on point.

**gak surface.** 73 top-level `def`s / **65** public; `grep -c "__all__" functions.py` → **0**;
`_comb_params`/`_reduce` exist; and every cited line number is exact:
`join:18`, `zip:118`, `linear_fit:346`, `concatenate:383`, `where:400`, `apply_correction:476`,
`onnx_inference:513`, `unflatten:600`, `full_like:612`, `broadcast_arrays:677`, `unzip:687`,
`to_list:693`, `fields:717`, `type_of:722`, `backend_of:727`, `head:732`, `sample:737`.
`broadcast_arrays` records `"ak.broadcast_arrays"`; `grep -rn broadcast python/graphed/numpy/*.py`
→ one docstring mention only.

**Histogram.** `boost.py:39-47,60-71` (independent per-input flatten; `weight = weight *
_flat(rest.pop(0))` at `:68`), `:88-98` (`_SumFills` = plain `+` over all fills), `:100-117`
(`layout = (label, n_fills, spec)` sliced by `range(i, i+k)`), `:120-122`, `:127-130`,
`:146-150`, `:153-163`, `:160-161` (one array per axis), `:166-174`, `:180-212`, `:205-206`,
`:215-216`, `:218-219` (`fill_nodes()` public, unlabeled), `:245-255`, `:282` (layout built from
`len(h._fill_nodes)` and `h._spec`); `_spec.py:31-37,70,74,81-84,115-122,129-135`. Runtime deps
are `["graphed","boost-histogram>=1.4","numpy>=1.24"]` at `pyproject.toml:21` with awkward only in
the dev extra `:25-39`.

**Frozen artifacts + fixtures.** `core/m4/test_systematics.py:28-53` and
`core/m4/test_benchmark.py:10,28-33,40-43,46-53`; `core/m40/test_join_serialize.py:83-99` (the
literal `b"GIR1\x03…"`); `awkward/m24/test_interface_parity.py:39-79` — the literal is **39**
names, counted; `full_like` is inside it at `:75`; `m29/test_multi_weight_fills.py:82-99` (with
`fill_nodes()` used at `:84,95`); `m23/test_group_plan.py:60-66,68-77`;
`preserve/m9/{agc.py:38-66,56-62,94-118,106-107, test_reproduce.py:19-23}` and the existence of
both `test_reproduce.py` and `test_inspect.py` (the m50 basename hazard is real);
`corpus/m05/test_systematics.py:26-38`, `test_fixtures_reproduce.py` (`bin_values ==
ref["values"]`, `fingerprint == ref["fingerprint"]` — exactly the form the m48 anchor names);
`debug/m6/analyses.py:52-56`; `graphed-executors m7/analyses.py:118-127`, `m7/adl.py:124-158`.

**Corpus.** `systematics.py:25-36,39-45,60-61,74-76,79,91-92,102,107-112` all exact (`:74` is
`sel_jets = good[sel]`, `:76` is `_btag_weight(sel_jets, …)` — the stacking case is real);
`histograms.py:20,35-37`; **23** reference JSONs = 8 ADL + 10 ttbar + 5 ttgamma, so "15 stored
references" and "**9 of the 15**" (2 regions × {nominal,btag_up,btag_down} = 6, plus ttgamma
{nominal,pho_up,pho_down} = 3) are both arithmetically right; the ttgamma SF weight really is a
flat constant (`np.full(..., sf)` at `:99`). `graphed-corpus pyproject.toml:28-30` packages only
`src/graphed_corpus`; `ops_catalog.md:75` is the Phase-2 row, verbatim.

**Fixture / CI facts (the m48/m49 hosting argument).** `graphed` has **no** `graphed-corpus` and
**no** `graphed-histogram` in any extra (grep over the whole `pyproject.toml`), vendors
`tests/_corpus/{graphed_corpus,references}` with `tests/_corpus` on `pythonpath` (`:115-127`), and
installs `.[dev]` in CI at `:34,57,143`; the `importorskip` house pattern is at
`preserve/m25/…:31`, `m27/…:185,207`, `m30/…:155`. `graphed-histogram` has zero `corpus` hits in
`tests/` or `.github/workflows/`, and its `ci.yml:13-17` carries `GRAPHED` + `EXECLOCAL` only,
while `graphed-executors ci.yml:17,38` does pre-install `CORPUS` from a git URL — the whole
"vendoring, not a dependency" argument checks out. `graphed-executors pyproject.toml:20-35` has no
histogram dependency. `scripts/run-tests.sh:16-25,30` runs `core` and `preserve` as one process
each (`SPLIT_PKGS="frontend numpy awkward"`), and there is no `__init__.py` anywhere under
`tests/frozen` — the m49/m50 basename hazard is real. `graphed-histogram` has a
`pythonpath` list (`pyproject.toml:50`), so the vendoring instruction is mechanically possible.
Frozen-milestone inventory confirms executors froze **m47** last and no repo holds m48+.

**uproot.** `RNTuple.py:1560-1562` (exact-first `_lookup`), `:1564-1569` (dot-split fallback),
`:562,567` (the `.`-split inside `to_akform`, def at `:535`); `TBranch.py:2015-2017` (exact-first)
and `:2019-2024` (`/`-split only); `_cascadetree.py:1606` (`.` as the nesting separator);
`_graphed_write.py:59-64` copies branches verbatim with **zero** `compile_ir`/`evaluate_ir` hits;
no frozen tree, **12** flat `tests/test_graphed_*.py` + the two shared helper modules, zero
`tests/frozen` references repo-wide.

**Root prompt / bookkeeping.** `graphed-root-prompt.md:25` (the "tens of thousands" quote),
`:1262` (R22.0), `:1282` (R22.10), `:1284` (the Out-of-scope header), `:1286` ("treating systematic
variations as a graph axis") — all four exact.

**Re-run probes (9).** (a) boost_histogram 1.8.0: `StrCategory(name=…)` → `TypeError`;
`Traits(underflow=False, overflow=True, growth=False)`; `h[{'variation': …}]` → `TypeError: list
indices must be integers or slices, not str`; `h[{1: bh.loc(...)}]` works; two-axis
`[a.__dict__.get("name") for a in h.axes] == [None,'variation']`; `h.axes.name` → `AttributeError:
object Regular has no attribute name`. (b) under-declaration `sum 2.0` vs `flow 3.0`;
over-declaration `sum == flow == 3.0` — both exactly as §6.2/m50 state. (c) `spec_of → zero_of`
round-trips the per-axis name on a **two-axis** histogram (`[None,'variation']`), the r13 claim.
(d) awkward 2.12.0 `ak.broadcast_arrays` over lengths 7 and 3 → `ValueError: cannot broadcast
RegularArray of size 3 with RegularArray of size 7`; the jagged 3-row case broadcasts fine.
(e) parquet writer/KV probe — see finding 5; all content reproduced. (f) `ak.from_parquet(p,
columns=["murf_0.5"])` returns an empty array with no fields while a plain name works — the
load-bearing justification for §1.1 canonicalization, re-measured. (g) CPython 3.12.10 `**`-unpacks
`{'0p5':…,'-2':…,'2.5':…}` without complaint. (h) against `graphed-latest`: `src * 2.0` recorded
twice returns node id **1** both times; `compile_ir` over two structurally identical outputs
evaluates to **1** value, over two distinct outputs to **2**. (i) the §3.3 builder rebuilt from the
plan's own description (source → D=500 prefix → per universe {fork, K=50 chain, 1 reduction}, each
reduction a marked output): N=16 → **stages 17 / reduced 34**, N=128 → **stages 129 / reduced
258**; without the terminating reduction, **18** and **130**; Δ(N=1→2) = **52** with, **51**
without; time ratio 128/16 = **5.9** against the 24.0 gate. Every pinned integer in §3.3/§5.2a is
exact.

**Arithmetic / counts.** 9-of-15 refs ✓; 23 vendored JSONs ✓; 39-name m24 literal ✓; 65 public gak
functions ✓; five `Session` construction sites ✓; the §2.6 sketch's "104 ambient weight labels"
(2 pileup + 102 PDF members) ✓; e-form renderings (`0.5→5em1`, `2.5→25em1`, `1.2345→12345em4`,
`-1.5→m15em1`, `1e-8→1em8`, `50em2→5em1`, `05→5`, `2/2.0/2e0/20e-1→2`) ✓; `1e40` = 41 plain
digits vs `1e-40` = the 5-character `1em40` ✓; `murf_10` sorts before `murf_2` ✓; compression
numbers (3.551 raw / 2.883 ratio / 3.280 xor MB; 798 KB → 169 KB masks ≈ 4.7×) match the worklog's
recorded probe (float32, 1M elems, zlib-6, seed 42) exactly ✓.

**Research-doc citations.** cba §optimizer §2 carries the measured table the plan quotes (N=16 →
3.1 ms / 34 nodes / 17 stages; N=128 → 16.7 ms / 258 / 129; "12.9× nodes → 11.9× time"; Δ = 52) and
§5 carries the grep-verified "no invalidation machinery"; the plan's warning that cba's `D` means
the per-universe chain while §3.3's `D` means the shared prefix is correct and necessary. cba
§histogram §1's "no constant-Array constructor" grep really was scoped to the session/array modules
(the §4.1 correction is right); §2 (bh rejects a 2-D weight) and §3 (scalar-string broadcast,
non-growth combine-safety, growth refusal at `_spec.py:70,74`) say what the plan says. cba §corpus
§1/§3/§4/§5 support the fixture, the m05 invariants, "no executor-level systematics fixture", and
the O(10⁴) graph-bloat figure. lit §rdf-vary §5-§6 carry the arXiv:2212.04889 "largest pain point"
quote, the name-collision/Snapshot-bitmask lessons and the exact vocabulary; lit §rdf-users §4
carries all three mkShapesRDF claims; lit §coffea-sys carries the #469 numbers **with** the
word-level-UNVERIFIED caveat at `systematics-vary-litsearch.md:236`, exactly as the plan cites it.

**Prior art (re-verified in the clones, not just via the litsearch).** `ewkcoffea@063e8d7`
`wwz4l.py:1204-1207` is the nominal-only exclusion rule and `:396-397` is the impact-partitioned
Weights comment, near-verbatim; the measured lists give **12** weight bases → 24 labels, **3** shift
bases → 6 labels, and a **7**-pass outer loop, and `_skip_obj_systematics` is real.
`ewkcoffea@63abb06` has `masked_val_cache`/`masked_weights_cache` at `:808-809`, `copy.copy(...) #
TODO do we need copy here?` at `:342`, `obj_correction_systs = []` at `:331`, `hout = {}` inside the
shift loop at `:807`, and `run_wwz4l.py:259-261` is verbatim "# Does not work" over a commented
`cloudpickle.dump`. `FNALLPC/wwz4l@cc71718`: `ApplyJetSystematics` is byte-identical to main's
(function bodies compared programmatically), zero dask/`dataset_tools` hits across its `.py` files,
anchors `:395-400` and `:711-718` exact — and the "**522** identical processor lines" figure
reproduces precisely under the natural metric (non-blank identical lines with multiplicity: 522;
`27` labels = 1 + 20 + 6 under the R3 configuration, matching litsearch:415). WRemnants + narf:
`grep -rn "\.Vary("` → **0** hits. mkShapesRDF `mRDF.py:6-7,220,249-251` and `runner.py:479-484`
verified in the clone. coffea@`f34b8bdf`: `rand_gauss` seeds PCG64 from the input array's own bytes
(`CorrectedJetsFactory.py:36-40`), `jer_smear` takes ONE `jet_resolution_rand_gauss` while
`jersf = …[:, variation]` varies per label, and `deltaPtRel`/`stochSmear` are signed
(`:64-95`) — the whole §5.5 basis holds; `Weights` stores `var/nominal` ratios
(`analysis_tools.py:512,520-522`) with the documented `1/weightUp` auto-symmetric Down; and
`explodes_how` really is an `@abstractmethod` with a `pass` body and the comment "your opinions
about systematics go here. :D" (`nanoevents/methods/base.py:131-139`).

---

## Verdict

**DIRTY — two HIGH findings, no BLOCKER.** Both HIGHs sit in one place (§2.3d's module-verb
disposition and the m48 anchor it drives) and are cheap to fix: remove `evaluate_ir` from the
refusing set, and re-bind the discovery predicate so it actually covers the ten verbs the section
enumerates. Findings 3-6 are hygiene: one unreproducible digest triple, one overstated
enumeration, one version inconsistency, four short ranges.

Otherwise the factual substrate is in unusually good shape for a document this size. Every
"measured this session" number I re-ran came back exact — the §3.3/§5.2a integers
(17/34, 129/258, 18/130, Δ=52/51), the interning and `compile_ir` dedup probes, the bh 1.8.0 axis
and declaration probes, the two-axis `spec_of`→`zero_of` round trip, the parquet writer/KV probe,
the dotted-column emptiness, the `**`-unpacking behaviour and the broadcast `ValueError` — as did
the compression figures against the worklog's stated methodology, the prior-art anchors against
the pinned clones (including the 522-line derivative metric), and the research-doc citations
against the sections they name. No claim I checked was fabricated.
