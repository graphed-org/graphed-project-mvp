# Systematics-`vary` plan — review round 9, FACTS / HALLUCINATION lens

- **Plan revision reviewed**: r17 (`systematics-vary-plan.md`, 3857 lines, read in full including Part I,
  every PART II section, §10 milestones, the Anchors appendix and the revision history).
- **Date**: 2026-07-30.
- **Lens**: factual substrate only — (a) every `file:line` anchor in the body and the appendix,
  (b) measured/"re-measured this session" claims, (c) citations into `systematics-vary-codebase-analysis.md`
  (cba) and `systematics-vary-litsearch.md` (lit), (d) prior-art claims against the clones,
  (e) arithmetic and counts. Design/test-authoring concerns are out of scope except where a stated fact
  is false or unverifiable as written.
- **Verification roots used** (all reads and probes were done against these, never the workdir submodules):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (its own `.venv`: awkward 2.12.0, cloudpickle 3.1.2)
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42`
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (its own `.venv`: boost_histogram 1.8.0)
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef` (branch `graphed-mvp`)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718,
    WRemnants, narf, mkShapesRDF, PocketCoffea, boostedhiggs, topeft}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf`
  - clean resolve for the parquet probes: `uv run --no-project --with "awkward>=2.12" --with pyarrow`
    → awkward 2.12.0 / pyarrow 25.0.1

**Verdict up front: this lens is essentially CLEAN.** Three findings, all LOW/NIT, none touching a binding
requirement's truth. Everything r17 added or changed as a *measured* claim reproduced exactly in-session
(details in the "verified clean" register at the end), including the two HIGH-severity r17 repairs
(the optimizer-merged-outputs probe and the checkpoint-churn scoping).

---

## Findings

### 1. LOW — the root-prompt Out-of-scope anchor `:1285-1286` is wrong; r17 replaced a correct pointer with an incorrect one

**Section**: Scope-deviation block (plan `:24-29`), §12.3(b), Anchors appendix row "Phase-2 parking being
un-parked", and the r17 revision-history LOW entry ("line-number corrections — … root prompt
`:1286`→`:1285-1286` (body, §12.3(b) and appendix)").

**Detail**: The plan states the Out-of-scope bullet "treating systematic variations as a graph axis" wraps
`graphed-root-prompt.md:1285-1286`. Measured, `:1285` is a **blank line** and the sentence wraps
**`:1286-1287`**. r17's own revision history records this as a *correction* of the previously-correct
`:1286`, so the edit moved the anchor off-target rather than onto it. The header anchor `:1284` and the
inline R22.0/R22.10 anchors `:1262,:1282` are correct.

**Evidence** (`awk 'NR>=1284 && NR<=1288' graphed-root-prompt.md`):

```
1284: ## Out of scope (later phases — MUST NOT be built initially)
1285:
1286: Distributed-scheduler executors for specific batch systems; treating systematic variations as a graph
1287: axis; advanced adaptive reshaping; predicate pushdown; interactive debugging or time-travel; export to
1288: external analysis-preservation portals; swapping the optimizer engine for a more capable one behind the
```

**Why it matters (bounded)**: §12.3(b) is an executable bookkeeping instruction ("amend the root prompt
Out-of-scope bullet (`graphed-root-prompt.md:1285-1286`)"). An agent following it literally edits a blank
line plus half the sentence and leaves the word "axis;" behind on `:1287`. No requirement changes meaning.

**Suggested fix**: replace `:1285-1286` with `:1286-1287` in all three places (body scope-deviation block,
§12.3(b), Anchors appendix), and correct the r17 revision-history line to record `:1286` → `:1286-1287`.

---

### 2. LOW — m49's §8.2(i) plan-byte determinism anchor presumes a `DurablePlan` that a varied program does not produce; r17 bound the construction path for the sibling anchor only

**Section**: §10 / m49, bullet "**§8.2(i) accessor + keying, in `graphed`**" — "Plus **plan-byte determinism
with the §8.2(i) field present**: the same varied program built in two fresh processes under differing
`PYTHONHASHSEED` yields byte-identical `DurablePlan.to_bytes()` and identical per-partition `task_id`".

**Detail**: r17's own HIGH repair established — and I re-verified — that `aggregate_plan` returns a plain
`graphed.core.execution.Plan` whose `process` is a bare callable with no `identity()`/`task_id`, that
`task_id`/`to_bytes` live only on `DurablePlan`, and that **no `Plan → DurablePlan` bridge ships**. r17 drew
the correct consequence for §7.3's interrupt/resume anchor ("the m49 fixture builds the `DurablePlan`
explicitly, either in the m8 pattern … or as `DurablePlan(ir=…, process=OpSpec.from_callable(plan.process),
…)`; the anchor states which") but did not carry it to this anchor, which asserts `DurablePlan.to_bytes()`
over "the same varied program". As worded the fixture has no stated route from a varied program to a
`DurablePlan`, and the anchor is the *only* place the §8.2(i) sorted-tuple-vs-`frozenset` determinism
requirement becomes observable.

**Evidence** (all re-measured in `graphed-latest@ff7c607`):
- `aggregate.py:95-108` → `return Plan(process=process, combine=combine, empty=empty, tasks=tasks)`;
  `Plan.process: Callable[[Partition, WorkerResources], R]`, `core/execution.py:206-217` (no `identity()`,
  no `task_id`).
- `task_id`/`to_bytes` on `DurablePlan`: `core/plan.py:126,164-176`.
- `grep -rn "DurablePlan(" python/` → **0 hits**; `OpSpec.from_callable` only at
  `shuffle.py:181,188,245,259` (V2 shuffle/join stages, which §5.4 forbids a variation cone from crossing).
- `OpSpec.from_callable(_PartitionReduce(...)).kind` → `"opaque"` (so the wrap is possible — it is just
  never performed by shipped code).

**Suggested fix**: add the same one clause r17 gave §7.3 — e.g. "…built as
`DurablePlan(ir=compiled.ir, process=OpSpec.from_callable(plan.process), …)` from the varied
`aggregate_plan`, since `aggregate_plan` returns a plain `Plan` (§7.2)" — to the m49 §8.2(i) plan-byte
bullet.

---

### 3. NIT — two small citation-span slips

**(a) `python/graphed/numpy/__init__.py:578-598`** (§4.1 and the appendix row "`graphed.numpy` DOES ship
donor-free constants"): cited as the `__all__` block containing `full`/`ones`/`zeros`/`empty`/`arange`/
`linspace`. Measured, `__all__` runs `:578-601` and `"zeros"` is at **`:599`** — outside the cited span, i.e.
one of the six named functions is not inside the evidence pointer. (`creation.py:31-75` and `:27-28` are
exact: `zeros` `:31`, `ones` `:36`, `full` `:41`, `empty` `:48`, `arange` `:57`, `linspace` `:70`.)
Fix: `:578-601`.

**(b) The `w` vs `w * 1.0` fill-node id literals** (§7.2, the appendix optimizer-merge row, and m48's §1.2
dedup anchor bullet): "two `Histogram.fill`s … record fill nodes `2` and `4` and compile to
`outputs() == [2]`". The *binding* half reproduces exactly — I built two fills differing only in
`weight=[w]` vs `weight=[w*1.0]` (numpy idiom, `from_record`) and got **distinct** fill node ids collapsing
to **one** compiled output — but the specific integers depend on an unstated source construction: mine were
`3` and `5` → `outputs() == [3]`. Under this plan's own reproducibility discipline (r13 withdrew the §6.4e
sha256 digests and r14 re-measured the §8.2(i) digest triple precisely because the payload was unnamed), the
literals should either name their program or be dropped in favour of the shape assertion the anchor actually
needs ("distinct record ids, one compiled output"). No requirement is affected; the four-array probe
(`nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5` → record ids `0,1,2,3`, `outputs() == [0,1,2]`,
`evaluate_ir` → 3 values) reproduced **verbatim**, ids included, because that one names its program.

---

## Verified-clean register (what this lens checked and found true)

Recorded for the review trail; each item was opened at the cited lines in the verification roots or
re-run as a probe in-session.

**r17's own new/changed measured claims — all reproduce exactly**

| Claim | Result |
|---|---|
| Optimizer merges DISTINCT record ids: `nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5` → ids `0,1,2,3`, `compile_ir` → `outputs() == [0,1,2]`, `evaluate_ir` → 3 values | reproduced verbatim |
| Same collapse on the FILL path (two fills, `weight=[w]` vs `weight=[w*1.0]`) → distinct fill nodes, ONE compiled output | reproduced (ids differ, see NIT 3b) |
| `EggEngine` sound rule set = commutativity over `SYMMETRIC_OPS` + `x+0.0`/`x*1.0` identity tokens, `engine.rs:22-31,67-80`; saturate+quotient `:89-110` | exact |
| `aggregate_plan` → plain `Plan`; `Plan.process` a bare callable (`core/execution.py:206-217`); `task_id`/`OpSpec` only on `DurablePlan` (`core/plan.py:54,126,164-176`); `run_resumable` needs a `DurablePlan` (`checkpoint/runner.py:77-91`) | exact |
| `grep -rn "DurablePlan(" python/` → 0; `OpSpec.from_callable` only `shuffle.py:181,188,245,259`; `graphed-executors/src` → 0 `task_id`/`DurablePlan`; documented idiom `OpSpec.from_ref("myanalysis:hist_chunk")` `docs/checkpoint/design.rst:20,58-65`; m8 fixture `analyses.py:114-123`; `OpSpec.from_callable(_PartitionReduce(...)).kind == "opaque"` | exact |
| Write plans carry no journal: `write.py:32-43` `Plan(process=write_part, …)`; `_WritePart` at `awkward/io.py:111-127`, `(out,) = evaluate_ir` `:121`, constructed `:239,260`, `gw.write_plan` `:274` | exact |
| `read_columns(arrays, source_nid) -> tuple[str,...] | None`, `None` = "read every column" on whole-record consumption / bare source read (`projection.py:109-115,146-147`), sorted return `:147` | exact |
| `_add_groups` is `{label: a[label] + b[label] for label in a}` (`boost.py:120-122`); `_GroupZero` per-slot `zero_of(spec)` `:127-130`; count-based `layout` `:100-117` built at `:282`; group `plan(...)` `:256-292` with `items = [(str(k), v) …]`; `aggregate_plan(*outputs: Array)` carries no output names (`aggregate.py:68-107`) | exact |
| §6.3 params KEY SET of an unvaried single-weight fill = `{"spec","n_axes","weighted","sampled"}` (recorded a fill and read `node["params"]`); `n_weights` added only when `len(weights) > 1` (`boost.py:198-212`); m29's `assert "n_weights" not in node["params"]` at `:96` | exact |
| `Session._provenance` setdefault sites `:138,166,181,202,240` (r17 correction); five `_array_cls` sites `:140,168,183,204,242`, none outside `session.py` | exact |
| `gak.zip(fields: Mapping[str, Array] | Sequence[Array], …)` at `functions.py:118-119` (the container-traversing template argument) | exact |
| `m29/test_multi_weight_fills.py:84-87` (`len(node["inputs"]) == 4`), `:75-79` (`array_equal` at fixed partitioning + `allclose(rtol=1e-12)`) | exact |
| Parquet KV metadata unused: only `.metadata` USE is `parquet.py:77`; `:107,118` are docstring mentions; zero `key_value_metadata`/`schema.with_metadata` in `graphed-latest/python` or `uproot5-graphed/src` | exact |
| `graphed.__all__` annotation-wide filter discovers exactly `aggregate_plan, apply, join, join_plan, pack_key, read_columns, repartition, shuffle_plan` (8), all refusing/expanding; `compile_ir` IS in `__all__` (`__init__.py:12,46`; `:44` = `"apply"`) and is NOT discovered (`compile_ir(session: Session, *outputs: Any, …)`) | exact |

**Earlier-revision claims re-verified (spot checks across the whole plan)**

- IR/optimizer: `store.rs:73-88` intern; `node.rs:39-41` identity, `:41-85` the whole enum with variant heads
  at `:42/46/51/56/64/72/81`, `:102-103` `is_boundary`; `mark_output` de-dup `store.rs:147-156` (`:152-153`);
  DCE remap `optimizer/mod.rs:88-116` (the `remap` vector is discarded, only `out_idx` returned);
  pipeline docstring `mod.rs:1-11`; `engine.rs:7-13` O(N) extractor note, `:54-56` boundary_from_token.
- PyO3 surface: exactly three `#[pymethods]` blocks at `lib.rs:102/159(-416)/470`; the `GraphStore` block is
  precisely the 15 methods the plan lists; no id mapping anywhere.
- §3.3 / §5.2a integers, re-measured on `graphed-latest` with D=500, K=50:
  **N=16 → stages 17 / reduced 34; N=128 → stages 129 / reduced 258; without the terminating reduction
  18 / 130; Δ(N=1→2) = 52 with, 51 without.** Matches cba §optimizer §2 (3.1 ms @ N=16, 16.7 ms @ N=128,
  ratio ≈5.4 vs the 24.0 gate; 12.9× nodes → 11.9× time) and the m4 gate style
  (`test_benchmark.py:10`, noise floor `:40`, `assert growth < 24.0` `:43`, best-of-N `:28-33`;
  built with raw `graphed.core.GraphStore` — the §5.2a/§5.2c surface correction is well-founded).
- Interning/dedup: recording one op twice → same node id, `node_count()` unchanged; `compile_ir` over two
  structurally identical outputs → ONE value, over distinct ones → two.
- Frontend: `array.py` `__slots__ :127-128`, properties `:137-143`, `__array_ufunc__ :156`,
  `__getattr__ :332-335`, `__getitem__ :344-371` (final raise `:369-371`, slice/int branches present),
  `filter` unchecked `:374-375`, `map :377-379`, `apply :397`; `dir(Array)` public =
  `['filter','map','node_id','reduce','repartition','session']`; `NumpyArray` = 32 public names adding
  `T/dtype/ndim/shape` + 22 methods, tuple `__getitem__ numpy/array.py:132-136`.
- gak: 73 `def`s / **65** public, no `__all__`; package `__all__` `awkward/__init__.py:17-31` yields the
  WRONG six-name set (`from_awkward/from_parquet/project/project_buffers/read_parquet_partition/to_parquet`);
  the alias under the bound discovery rule (`__module__ == "graphed.awkward.functions"`) discovers **0**,
  the module **65**; `graphed.awkward.num` → `AttributeError`; `gak is functions`; `join :18`,
  `full_like :612-616`, `broadcast_arrays :677-685`, and every other cited offset exact.
- Histogram package: `fill :153`, arity check `:160-161`, `inputs = list(args) :175` + `extend :176`,
  `chash = content_hash(self._spec) :187`, `record_external :196-210`, `_evaluators[chash] :212`,
  `staged_fills :215`, `fill_nodes :218-219` (public, unlabeled), `plan :226/245-255`,
  `self._spec = spec_of(self) :148`; `_spec.py` `_metadata_of :31-37`, `_restore_metadata :81-84`,
  growth refusal `:70,74`, `spec_of/zero_of :115-135`; two-axis name round-trip `spec_of→zero_of` →
  `[None, 'variation']`.
- boost_histogram 1.8.0 probes, all reproduced: under-declaration `sum 2.0` vs `sum(flow=True) 3.0` with
  `Traits(overflow=True, growth=False)`; over-declaration invisible (`3.0 == 3.0`);
  `StrCategory(..., name=...)` → `TypeError`; `h[{"variation": …}]` and the `bh.loc` form → `TypeError:
  list indices must be integers or slices, not str`; `h.axes.name` → `AttributeError: object Regular has no
  attribute name` on a two-axis histogram; `h[{1: ax.index(l)}] == h[{1: bh.loc(l)}]`; cross-axis addition →
  `ValueError: axes have different length`.
- awkward 2.12.0 probes: `float32 ^ float32` → `TypeError` for both `np.ndarray` and `ak.Array`,
  `view(uint32) ^ view(uint32)` works; `ak.broadcast_arrays` lengths 7 vs 3 → `ValueError: cannot broadcast
  RegularArray of size 3 with RegularArray of size 7`, jagged 3-row broadcasts fine;
  `"metadata" in signature(ak.to_parquet)` → `False`; no tuple subscript on the awkward idiom
  (`w[:, 1]` → `TypeError: unsupported index (slice(None, None, None), 1)`), while
  `gak.firsts(w[gak.local_index(w) == 1])` materializes the inner index.
- Parquet (clean resolve, awkward 2.12.0 / **pyarrow 25.0.1**): `ak.to_parquet` vs
  `pq.write_table(ak.to_arrow_table(...))` differ in bytes; file-KV sets exactly as the appendix row states
  (record `{ARROW:schema, ak:parameters, awkward_array_metadata}` vs `{ARROW:schema, ak:parameters}`;
  list-of-float and flat `{ARROW:schema, awkward_array_metadata}` vs `{ARROW:schema}` — so `ARROW:schema`
  always present, `ak:parameters` array-dependent); `created_by == "parquet-cpp-arrow version 25.0.1"`;
  repeat writes byte-identical; `ak.from_parquet(columns=["murf_0.5"])` returns a fields-less array.
- Determinism probe: cloudpickle 3.1.2, payload `(3, frozenset({...5 labels...}))` under `PYTHONHASHSEED`
  1 / 7 / 12345 → `b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831` — **the three digests
  reproduce exactly**.
- uproot fork @ `393ecef`: RNTuple `__getitem__` exact-first `:1560-1562`, dot-split fallback `:1564-1569`,
  `to_akform` path split `:562,567`; `_cascadetree.py:1606` `.`-nesting; `TBranch.py:2015-2017` exact-first,
  `:2019-2024` `/`-split; `_graphed_write.py:59-64` verbatim branch copy with **0** `compile_ir`/
  `evaluate_ir`; **12** flat `tests/test_graphed_*.py` + 2 helper modules; no frozen tree, zero
  `tests/frozen` references.
- Corpus: 23 reference JSONs (8 ADL + **15** systematics); the m48 anchor's **9 of 15** weight refs all
  exist; `systematics.py` `_btag_weight :25-36`, `_apply_jes/with_field :39-45`, JES-before-cut `:60-61`,
  `sel_jets/_btag_weight :74-76`, pre-fill rounding `:79` and `:102`, `_round_hist :50`,
  photons/muons sliced by the varied selection `:91-92`; vendored copy in `graphed` byte-identical;
  `histograms.py:20` `STABLE_DECIMALS = 6`, `bin_values :35-37`, `fingerprint :40-43`;
  m05 comparison form is exactly `bin_values(h) == ref["values"]` / `fingerprint(h) == ref["fingerprint"]`;
  m05 ordering/invariance tests as quoted; `ops_catalog.md:75` verbatim; `test_catalog.py` is
  text-presence-only (so §12.3(d)'s "lock-step preserved" holds).
- Fixture/CI facts: `graphed` deps `:27`, extras `:29-46` (dev `:42-48`, no `graphed-histogram`, no
  `graphed-corpus`), pytest config `:103-130` with `pythonpath :114-127` incl. `tests/_corpus`,
  CI `.[dev]` at `:34,57,143`; `run-tests.sh` `SUITES :16-25`, `SPLIT_PKGS :30`; zero `__init__.py` under
  `tests/frozen`; `graphed`'s only cross-process frozen test is `debug/m6/test_process_boundary.py`;
  `graphed-histogram` runtime deps `:21`, dev `:25-39`, `pythonpath :50`, `pytest tests/frozen` at
  `ci.yml:44,67`, env `GRAPHED`+`EXECLOCAL` only, **0** corpus hits, version `0.0.1`;
  `graphed-executors` deps `:20-35` (no histogram), env `ci.yml:13,15,17`, installs `:38,65,94,136`,
  frozen runs `:44,67`, `pythonpath :54`, 15 milestone dirs, 0 `__init__.py`;
  `graphed-corpus pyproject.toml:28-30` packages only `src/graphed_corpus`.
- Errors/provenance/preserve: `StageError` class `errors.py:29`, `__eq__ :75-78`, `__hash__ :80-81`;
  `grep "StageError("` → exactly two hits (`errors.py:29`, `debug/runner.py:37`);
  `runner.py:6-7` "a *debug* runner, not the M7 executor"; `provenance.py:26-33` dataclass,
  `capture() :66-79` skipping graphed frames; `build_bundle` singular + paired-arg raise `:101-123`,
  `reproduce :205-210`, `inspect(bundle) -> str :267-288`; m9 `agc.py` correctionlib `systematic` category
  `:38-66`, shift-before-mask `:106-107`, `record :93-118`; `test_reproduce.py:19-23`.
- Executors: `submit/engine.py:381-396` translate-only; `m7/analyses.py:118-127` rebuilds in the worker;
  `m7/adl.py:124,156-158` in-process corpus references; `m23/test_group_plan.py:60-66` eager oracle,
  `:68-77` `part_reads == 4`.
- Research-doc citations: lit §rdf-vary §5 (arXiv:2212.04889 "largest pain point"), §6 (naming vocabulary,
  `"nominal"` reserved); lit §coffea-sys §5 with the #469 caveat at **`systematics-vary-litsearch.md:236`**
  verbatim; lit §ewkcoffea-confirmed (12 bases → 24 labels, 6 shift labels, 7 shift passes, 27 labels for
  the teaching fork); cba §histogram §1's constant-Array grep scope is exactly as §4.1 characterises it;
  cba §optimizer §2/§5 and §exec-checkpoint §1 as cited; worklog compression numbers (raw 3.551 MB /
  ratio 2.883 / XOR 3.280; masks 798 KB → 169 KB ≈4.7×) with the stated methodology.
- Prior art: `ewkcoffea@063e8d7 wwz4l.py:396-397` ("These weights can go outside of the outside sys loop…")
  and `:1204-1207` (exclusion rule) verbatim; `ewkcoffea@63abb06 wwz4l.py:807-809` (`hout = {}` inside the
  shift loop + `masked_val_cache`/`masked_weights_cache`), `run_wwz4l.py:259-261` ("# Does not work" over a
  commented `cloudpickle.dump`), `:302-313` timing block, `:331` empty `obj_correction_systs`;
  `wwz4l@cc71718 analysis_processor.py:395-400,408,711-718` and `ApplyJetSystematics` **byte-identical**
  to `ewkcoffea`'s (same sha256 over both function bodies); **522 identical processor lines reproduced
  exactly** (multiset intersection of non-blank raw lines — the lit doc's number is recoverable);
  `WRemnants`+`narf` → **0** hits for `.Vary(`/`VariationsFor`; `mkShapesRDF` reimplements `Vary`
  (`mRDF.py:177,214-215,273,292`); coffea @ `f34b8bdf` `CorrectedJetsFactory.py:36-47` (PCG64 seeded from
  the array's own bytes) and `:64-95` (one shared `jet_resolution_rand_gauss`, `jersf[:, variation]`,
  signed `deltaPtRel`, hybrid det/stoch smear).
- Arithmetic: 9 = 6 + 3 of 15 refs ✓; the sketch's ambient label count 104 = 2 (pu) + 102 (pdf) ✓;
  `1e40` → 41 plain digits vs `1em40` → 5 chars ✓; e-form renderings (`0.5→5em1`, `2.5→25em1`,
  `1.2345→12345em4`, `-1.5→m15em1`) ✓; lexicographic ordering example
  `btag_down < btag_up < jes_down < nominal < pu_up` ✓; `stages == N+1` / `reduced == 2N+2` / `Δ = K+2 = 52`
  ✓; 65/73 gak, 39-name m24 pin, 32 NumpyArray names, 23 JSONs, 12 uproot test files ✓.

**Not verifiable from here (stated, not a defect)**: the PyPI lookup behind the m49(ii) claim that
`graphed-histogram` resolves to a stale `0.0.1` (no network used in this review); the local half — the
repo's own `pyproject.toml` version is `0.0.1` — checks out. The boost_histogram **1.7.2** legs of the
probes that also cite **1.8.0** were re-run on 1.8.0 only; every 1.8.0 result matched, and no 1.7.2-only
claim is load-bearing on its own.

---

## Verdict

**CLEAN for this lens** (with three LOW/NIT corrections). r17's factual substrate is the strongest of the
review chain so far: every one of its new measured claims — including the two that drove HIGH-severity
edits (optimizer-merged distinct record ids collapsing to one compiled output, and the
`Plan`-vs-`DurablePlan` checkpoint-churn scoping) — reproduced in-session against the pinned roots, and the
one claim r17 explicitly **rejected** with counter-evidence (`checkpoint/m8/test_resume.py:51-58` is not
stale) is confirmed correct: `def test_result_is_invariant_to_partition_count` is at `:51` and its last
assert at `:57`. No BLOCKER, HIGH or MID factual defect was found.
