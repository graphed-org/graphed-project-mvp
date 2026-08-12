# systematics-vary-plan review — round 8, FACTS / HALLUCINATION lens

- **Plan revision reviewed:** r16 (`systematics-vary-plan.md`, 3516 lines, read in full — Part I, all of PART II §§1–12, the milestone skeleton §10, the Anchors appendix, and the full revision history).
- **Lens:** facts / hallucination audit — every `file:line` anchor in the body AND the appendix opened at the cited lines; measured claims re-run where cheap and checked for internal consistency with the worklog where expensive; citations into `systematics-vary-codebase-analysis.md` (cba) and `systematics-vary-litsearch.md` (lit) read at the cited sections; prior-art claims checked against the prior-art clones; arithmetic and counts recomputed.
- **Date:** 2026-07-30.
- **Verification roots used** (fresh clones at the revisions the plan cites; the stale submodules under `/Users/lgray/vibe-coding/graphed-workdir` were NOT used for any code fact):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (+ its `.venv`: awkward 2.12.0)
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42`
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef`
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718, WRemnants, narf, mkShapesRDF, PocketCoffea, boostedhiggs, topeft}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf`
  - ephemeral probe envs via `uv run --no-project --with …` (boost_histogram 1.8.0, pyarrow 25.0.1, cloudpickle 3.1.2)

---

## Findings

### 1. HIGH — §7.3 / Anchors appendix: `_PartitionReduce` and `_WritePart` are NOT "the plan's opaque `process` spec"; the "ALL-programs" and "WRITE-plan journal" one-time-churn claims (and the r16 label-RENAME class built on them) are false as stated

**Section:** §7.3 (both churn paragraphs), §7.2's closing sentence, the Anchors row *"`_PartitionReduce` is the plan's opaque `process` spec; `task_id` folds `identity()` (the §7.3 one-time churn)"*, and the two frozen docs anchors that consume them (§10/m50 *"Docs: … all three invalidation classes, including the label-RENAME one"* and §10/m51 *"Docs: the §7.3 checkpoint paragraph gains m51's own one-time churn"*).

**Detail.** The plan asserts, as measured fact, that adding a field to `_PartitionReduce` (m49, §8.2(i)) and widening `_WritePart` (m51, §6.4f) each change "the plan's opaque `process` spec", and therefore invalidate "every existing checkpoint journal … including for *unvaried* programs" and "every existing WRITE-plan journal … unvaried writes included". This conflates two different objects that the shipped code does not connect:

- `_PartitionReduce` is the `process` of an **in-memory `graphed.core.execution.Plan`** — `process: Callable[[Partition, WorkerResources], R]`, a plain callable with no `identity()` and no `task_id` (`graphed-latest/python/graphed/core/execution.py:206-217`, verified). Same for `_WritePart`: `write_plan` returns `Plan(process=write_part, combine=_concat_paths, empty=_no_paths, tasks=tasks)` (`python/graphed/write.py:40`, verified) — a `Plan`, not a durable one.
- `task_id` exists **only** on `DurablePlan` (`core/plan.py:164-176`) and `DurablePlanV2` (`:286-301`), whose `process` is an `OpSpec` (`plan.py:61-90`). Feeding a callable into that requires `OpSpec.from_callable`.
- Measured, the **only** production `OpSpec.from_callable` call sites in the pinned roots are `python/graphed/shuffle.py:181,188,245,259` (the V2 shuffle/join stages: a user `reduce`, `_GatherReduce`, `partition_block`, `join_blocks`) — none of them `_PartitionReduce` or `_WritePart`. Every `DurablePlan(` construction in `graphed-latest` is in hand-written tests (`tests/frozen/checkpoint/m8/analyses.py:115,176`, `deployment.py:146`, `test_no_source.py:41`, `tests/frozen/core/m8/test_durable_plan.py:32,65,103`). `graphed-exec-check/src` contains **zero** `task_id` and zero `DurablePlan` references. There is no `Plan → DurablePlan` bridge anywhere (`grep -rn "from_plan\|to_durable\|def durable" python/graphed/` → 0 hits).
- The **documented** checkpoint idiom explicitly uses the *user's own* module-level functions, not `_PartitionReduce`: `docs/checkpoint/design.rst:58-65` — `DurablePlan(process=OpSpec.from_ref("myanalysis:hist_chunk"), combine=OpSpec.from_ref("myanalysis:hist_add"), …)`, and `:20` says the plan carries "its process/combine/empty operations as import-referenced ``OpSpec``\ s".

So on the shipped and documented path, widening `_PartitionReduce`/`_WritePart` invalidates **nothing**, and write plans have **no journal at all**. (I confirmed the sub-claim the plan does get right: `OpSpec.from_callable(_PartitionReduce(...))` → `kind == "opaque"`, so *if* a caller wraps it the churn would follow; but no caller does.) The first invalidation class in §7.3 — "adding/removing a variation changes the IR and therefore every `task_id`" — is unaffected and remains true, because the IR is folded directly (`plan.py:164-176`).

**Evidence:**
```
python/graphed/core/execution.py:206-217   class Plan: process: Callable[[Partition, WorkerResources], R]   # no OpSpec, no task_id
python/graphed/write.py:40                 return Plan(process=write_part, combine=_concat_paths, empty=_no_paths, tasks=tasks)
python/graphed/core/plan.py:164-176        DurablePlan.task_id(...)  -> folds self.process.identity()   # process is an OpSpec
grep -rn "OpSpec.from_callable" graphed-latest/python  -> shuffle.py:181,188,245,259 (+ the definition at plan.py:97)
grep -rn "DurablePlan(" graphed-latest/python          -> 0 hits (all constructions are in tests/)
grep -rn "task_id|DurablePlan" graphed-exec-check/src  -> 0 hits
docs/checkpoint/design.rst:58-65           process=OpSpec.from_ref("myanalysis:hist_chunk")
probe: OpSpec.from_callable(_PartitionReduce(...)).kind -> "opaque"   (true, but unreached)
```

**Suggested fix.** Either (a) name the missing bridge as an explicit m49 precondition ("an aggregate/write plan reaches the checkpoint runner only through a caller-built `DurablePlan(process=OpSpec.from_callable(plan.process), …)`; m49's interrupt/resume fixture constructs it that way, m8 pattern") and scope both churn sentences to *journals whose `process` `OpSpec` embeds `_PartitionReduce`/`_WritePart`*; or (b) delete "ALL-programs"/"including for unvaried programs" and the entire m51 WRITE-plan-journal paragraph, and restate §7.3's second and third invalidation classes as conditional on that construction. Either way the r16 label-RENAME class must carry the same scoping — under the documented `OpSpec.from_ref` idiom a rename changes neither the IR (§1.2, which holds) nor the user's process ref, so nothing is invalidated — and the m50/m51 **docs** anchors must not freeze the unconditional wording, or an implementer will freeze a false statement into user docs. Related: §7.3's m49 interrupt/resume anchor currently has no stated path from a varied `aggregate_plan` to a `DurablePlan`; naming it closes both gaps at once.

---

### 2. LOW — six stale/imprecise line spans (claims themselves are true; the cited ranges do not contain the quoted content)

**Section:** §4.3, §8.2(ii), §12.3(b) + header, Anchors appendix (parquet-metadata row, m8 resume row), §10/m48.

**Detail + evidence** (each measured with `grep -n` in the verification roots):

| Plan citation | Quoted/claimed content | Measured location |
|---|---|---|
| §4.3 and the m48 §4.3 anchor: `boost.py:176-178`, "`inputs = list(args)` then `inputs.extend(weights)`" | `inputs: list[Array] = list(args)` | `graphed-histogram/src/graphed_histogram/boost.py:175` (`:176` is `inputs.extend(weights)`, `:178` the sample append) |
| §4.3: "`tests/frozen/m29/test_multi_weight_fills.py:84-86` asserts `len(node["inputs"]) == 4`" | `assert len(node["inputs"]) == 4` | that file's `:87`; `:84-86` are the node lookup + the `n_weights`/`weighted` asserts |
| §8.2(ii): "`Session._provenance` … written at `:141-166`" | the provenance writes | `session.py:138` (`source`), `:166` (`record_op`), `:181`, `:202`, `:240` — the cited span reaches only one of five (the §2.3e "FIVE construction sites" row gets this right) |
| Anchors, parquet row: "the only `metadata` uses on the write/read path are `ParquetFile(path).metadata.num_rows` (`python/graphed/parquet.py:77,107,118`)" | a *use* | only `:77` is a use; `:107` and `:118` are docstring mentions. The load-bearing half re-verified TRUE: `grep -rn "key_value_metadata\|with_metadata" graphed-latest/python uproot5-graphed/src` → **0** |
| §12.3(b) and the header: root-prompt bullet at `graphed-root-prompt.md:1286` | "treating systematic variations as a graph axis" | the phrase begins at `:1285` and wraps onto `:1286` (`:1284` is the section header, cited correctly) |
| §5.5(a): "`graphed tests/frozen/checkpoint/m8/test_resume.py:51-58`" (partition-count-invariance precedent) | `test_result_is_invariant_to_partition_count` | `:54-58`; `:51` is the last assert of the preceding test |

**Suggested fix.** Mechanical: `:176-178`→`:175-178`; `:84-86`→`:84-87`; `:141-166`→`:138,166,181,202,240` (or reuse the appendix row's phrasing); re-word the parquet row as "the only `metadata` *use* is `parquet.py:77`; `:107,118` are docstring mentions — and no `key_value_metadata`/`with_metadata` exists anywhere in `graphed-latest/python` or `uproot5-graphed/src` (0 hits)"; `:1286`→`:1285-1286`; `:51-58`→`:54-58`.

---

### 3. NIT — Part I §2: "the in-IR `add_systematic` prototype stalled for ~4 years" vs the cited lit's "~3-year stall"

**Section:** Part I §2 (coffea paragraph), citing lit §coffea-sys.

**Detail.** `systematics-vary-litsearch.md:213` records the timeline as created 2021-05-13, docstrings 2022-03-07, then dormant, dask-mode merged 2025-07-12 — and calls it "a **~3-year stall** on the prototype". The plan says "~4 years". Both are defensible readings of the same recorded dates (creation→revival ≈ 4.2 y; last-activity→revival ≈ 3.3 y), but the two committed documents now state different numbers for the same fact.

**Evidence:** `systematics-vary-litsearch.md:213` ("created 2021-05-13 … dask-mode support only merged **2025-07-12** … a ~3-year stall on the prototype"); plan Part I §2 ("stalled for ~4 years").

**Suggested fix.** Pick one and say from what: "dormant for ~3 years after its last documentation activity (created 2021-05, docstrings 2022-03, dask mode 2025-07 — lit §coffea-sys §2)".

---

### 4. NIT — §1.1 / header note: the underscore label style is credited to RDataFrame, which uses a colon

**Section:** the header "Naming — owner-verified" block and §1.1.

**Detail.** The sentence reads: *"Variation labels are `f"{name}_{tag}"` underscore style (`jes_up`, `btag_down`); **`"nominal"` is reserved** … This matches RDataFrame's `Vary` precedent (lit §rdf-vary §6), graphed's lowercase-verb convention (`join`, `repartition`), and — verbatim — the 15 stored corpus reference names."* Measured, RDF's full variation key is `variationName + ":" + tag` (`pt:up`, `ptAndEta:down`) — lit §rdf-vary §1 and §6 both state it. What RDF actually supplies as precedent is the **verb** and the reserved `"nominal"` key; the underscore style comes from the corpus names only (verified: `graphed-corpus-latest/corpus/references/ttbar_4j1b_btag_up.json` and 14 siblings). Naming is owner-locked and untouched by this finding — the issue is only which precedent the sentence credits, and a reader could otherwise cite RDF for a style it does not use.

**Evidence:** `systematics-vary-litsearch.md` §rdf-vary §6 ("full key = `variationName + ":" + tag` (`"pt:down"`)"); `ls graphed-corpus-latest/corpus/references | grep -v adl_` → 15 files, all `f"{name}_{tag}"`.

**Suggested fix.** Split the attribution: "…matches RDataFrame's `Vary` **verb** and reserved `"nominal"` key (lit §rdf-vary §6; RDF's own label separator is `:`), graphed's lowercase-verb convention, and — verbatim — the 15 stored corpus reference names."

---

## What was checked and found clean (no finding raised)

Recorded for the review trail; every item below was opened/executed in this session.

**Code anchors, `graphed-latest@ff7c607`** — all confirmed at the cited lines: `array.py:127-128,137-143,156,245-275,332-335,344-371,374-391,397-410,54`; `session.py:30,39,50-51,113-125,133-140,142-168,170-183,185-204,206-242,245-252,255-286,291-301` and `:152,159`; `execute.py:36-45,54-58,70,85-91,96-126,104-105,109,110-117,116-124,126`; `aggregate.py:44-65,57-65,68,86,89-93,95-97,101`; `projection.py:109,147`; `shuffle.py:5-8,68,84,89,92-96,142,155,170,208,220,232,181/188/245/259`; `core/plan.py:72-76,72-90,164-176,286-301,97`; `core/execution.py:276-284,450-457`; `checkpoint/store.py:31-41,62-73`; `checkpoint/runner.py:100-109`; `debug/errors.py:29,75-78,80-81`; `debug/runner.py:6-7,37,57-69`; `provenance.py:26-33,66-79`; `preserve/bundle.py:103-123,206-210,268-288`; `awkward/io.py:111-127,121,157-185,206-216,239,260,274`; `awkward/functions.py:18,118,346,383,400,476,513,600,612-616,673,677-685,687,693,717,722,727,732,737`; `awkward/__init__.py:14,17-31,30`; `numpy/array.py:92-190,132-136`; `numpy/io.py:158-173,163-171`; `numpy/creation.py:27-28,31-75`; `numpy/__init__.py:8,578-598`; `__init__.py:8-25,9,12,44,46,27-58,50-57`; `write.py:32-43,77-79`; Rust `store.rs:73-88,147-156,152-153`, `node.rs:39-41,41-85` (variant heads 42/46/51/56/64/72/81 exactly as claimed), `:102-103`, `optimizer/engine.rs:7-13,54-56`, `optimizer/mod.rs:1-11,88-116`, `lib.rs` `#[pymethods]` blocks at exactly `:102`, `:159`(impl 160–416), `:470` with the 15 named `GraphStore` methods and no id mapping.

**Cross-repo anchors** — `graphed-histogram-latest@211cbbe`: `boost.py:39-47,60-71,88-98,100-117,120-122,127-130,146-150,153-163,160-161,166-174,180-212,205-212,215-216,218-219,226-253,245-255,282,283-286`; `_spec.py:31-37,70,74,81-84,115-122,129-135`; `pyproject.toml:21,25-39,50`; `ci.yml:44,67`; 0 `__init__.py`, 0 corpus hits, `tests/frozen/{m23,m29}` only. `graphed-exec-check@201ea42`: `submit/engine.py:381-396`; `pyproject.toml:20-35,54`; `ci.yml:13,15,17,38,65,94,136,44,67,101,153`; 15 milestone dirs, 0 `__init__.py`, no `graphed-histogram` anywhere. `uproot5-graphed@393ecef`: `_graphed_write.py:59-64` (0 `compile_ir`/`evaluate_ir` hits), `behaviors/RNTuple.py:1560-1562,1564-1569,562,567` (`to_akform` at `:505`), `behaviors/TBranch.py:2015-2017,2019-2024`, `writing/_cascadetree.py:1606`, 12 flat `test_graphed_*.py` + 2 helper modules, 0 `tests/frozen` references. `graphed-corpus-latest@49650e4`: `systematics.py:25-36,39-45,60-61,74-76,79,91-92,102,50`, `histograms.py:20`, `pyproject.toml:28-30`, 23 references (15 systematics). Frozen-test anchors: `corpus/m05/test_systematics.py:26-38`, `core/m4/test_benchmark.py:10,28-33,40-43,40-53`, `core/m4/test_systematics.py:28-53`, `core/m40/test_join_serialize.py:83-99`, `awkward/m24/test_interface_parity.py:39-79` (**39** names, counted) and `:74-76`, `m29/test_multi_weight_fills.py:75-79,84,93-99`, `m23/test_group_plan.py:60-66,68-77`, `preserve/m9/agc.py:56-62,94-118,106-107`, `preserve/m9/test_reproduce.py:19-23`, `preserve/m25/…:31`, `m27/…:185,207`, `m30/…:155`, `debug/m6/test_process_boundary.py:7,16`, `debug/m6/analyses.py:52-56`, `checkpoint/m8/analyses.py:29-30`, `graphed-executors m7/adl.py:124-158,156-158`, `m7/analyses.py:118-127`. Repo-layout facts: `graphed pyproject.toml:27,29-46,42-48,103-130,114-127`, `ci.yml:34,57,143`, `scripts/run-tests.sh:16-25,30`, 0 `__init__.py` under `tests/frozen`, `tests/_corpus` byte-identical to the corpus package.

**Re-run measurements** — all reproduced exactly as the plan states:
- §3.3/§5.2a topology (source → D=500 prefix → per universe {fork, K=50 chain, terminating reduction}, every reduction marked): N=16 → stages **17** / reduced **34**; N=128 → **129** / **258**; without the reduction → **18** / **130**; Δ(N=1→2) = **52** with, **51** without.
- §7.2 dedup: `compile_ir(s,b,c)` with `b`,`c` structurally identical → **1** value; `compile_ir(s,b,d)` → **2**. Interning: the same op recorded twice returns node id **1** both times.
- §2.3d discovery: the annotation-wide filter over `graphed.__all__` yields exactly `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']` (8) and misses `compile_ir` (`(session: 'Session', *outputs: 'Any', …)`). `graphed.awkward.functions` → **65** public functions (73 `def`s, `__all__` absent); the package `__all__` yields exactly the wrong six-name set `from_awkward/from_parquet/project/project_buffers/read_parquet_partition/to_parquet`; `graphed.awkward.num` → `AttributeError`. `[n for n in dir(Array) if not n.startswith("_")] == ['filter','map','node_id','reduce','repartition','session']`; `dir(NumpyArray)` → **32** public names adding `T`/`dtype`/`ndim`/`shape`.
- §6.1d/§6.4c: `float32 ^ float32` → `TypeError: ufunc 'bitwise_xor' not supported…` for **both** `np.ndarray` and `ak.Array`; `a.view(np.uint32) ^ b.view(np.uint32)` works; `ak.broadcast_arrays` over lengths 7 and 3 → `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`, jagged 3-row broadcasts fine.
- §6.2/§6.2(i-bis) on boost_histogram 1.8.0: `StrCategory(name=…)` → `TypeError`; `Traits(overflow=True, growth=False)`; under-declaration `sum 2.0` vs `flow 3.0`; over-declaration `3.0 == 3.0`; `h[{"variation": …}]` and `h[{"variation": bh.loc(…)}]` → `TypeError: list indices must be integers or slices, not str`; `h[{1: ax.index(…)}] == h[{1: bh.loc(…)}]`; `h.axes.name` → `AttributeError: object Regular has no attribute name`; per-axis `[None,'variation']`; cross-axis `+` → `ValueError: axes have different length`.
- §6.4e/§6.4g on awkward 2.12.0 / pyarrow **25.0.1**: `ak.to_parquet` vs `pq.write_table(ak.to_arrow_table(…))` differ in bytes for record/list-of-float/flat; the arrow path drops `awkward_array_metadata`; `ARROW:schema` always present, `ak:parameters` array-dependent; `"metadata" in signature(ak.to_parquet)` → `False`; `created_by == "parquet-cpp-arrow version 25.0.1"`; two writes of one array in one process are byte-identical; `ak.from_parquet(columns=["murf_0.5"])` → silently empty (0 rows, no fields).
- §8.2(i): cloudpickle 3.1.2, payload `(3, frozenset({...5 labels...}))`, `PYTHONHASHSEED` 1/7/12345 → sha256[:16] `b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831` — the plan's triple reproduces **exactly**.
- §2.6 sketch: `w[:, 1]` → `TypeError: unsupported index (slice(None, None, None), 1)`; `gak.firsts(w[gak.local_index(w) == 1])` over `[[1,2,3],[4,5,6]]` → `[2.0, 5.0]`.
- §4.3's spelling is implementable: `store.nodes()` is id-indexed (`index == n["id"]` for all nodes) and each dict carries `inputs`.
- `_array_cls` appears only in `session.py` (6 hits = 1 assignment + the 5 return sites).

**Research-doc citations** — cba §corpus §1/§3/§4/§5, §optimizer §2/§5 (3.1 ms @ N=16, 16.7 ms @ N=128, 12.9× nodes → 11.9× time, `2N+2`/`stages=N+1`, ratio ≈5.4 vs the 24.0 gate — arithmetic checked), §histogram §1/§2/§3, §ir-rust §1 all say what the plan says they say, including the plan's own honest correction of cba §histogram §1's module-scoped `full_like` grep. lit §rdf-vary §1–§6, §rdf-users §1–§5, §coffea-sys §1–§5 (incl. the word-level-UNVERIFIED caveat on Discussion #469, which is at `systematics-vary-litsearch.md:236` exactly), §pythonic-analyses conventions/failure modes, and §ewkcoffea-confirmed + addendum all check out. Worklog: the §6.4c compression probe (`raw=3.551MB / ratio=2.883 / xor=3.280`; masks `798KB → 169KB ≈ 4.7×`) is recorded with full methodology and matches every plan citation.

**Prior art** — independently re-verified: WRemnants and narf have **0** `Vary`/`VariationsFor` uses; `ewkcoffea@063e8d7 wwz4l.py:1204-1207` is the nominal-only exclusion rule verbatim and `:396-397` the "these weights can go outside the … sys loop" comment verbatim; the 0.7-era counts are exact (10 common + 2 R2 = **12** weight bases → **24** labels; 3 obj bases → **6** shift labels; `["nominal"] + 6` = **7**-pass loop); `coffea2023@63abb06` has `obj_correction_systs = []` (`:331`), the `masked_val_cache`/`masked_weights_cache` hand-CSE at `:808-865`, and `run_wwz4l.py:259-261` "# Does not work" over a commented `cloudpickle.dump`; `FNALLPC/wwz4l@cc71718` has **0** dask/`dataset_tools`/`hist.dask` hits, the byte-identical shift machinery at `:395-400`/`:711-718`, 14 categories, and lit's "27 = 1 + 20 + 6" label arithmetic is correct; coffea `CorrectedJetsFactory.py:36-47` seeds PCG64 from the input array's own bytes and `:64-95` takes one shared `jet_resolution_rand_gauss` with only `jersf` varying per label and a signed `deltaPtRel` (non-monotone by construction); coffea `Weights` stores `var/nominal` ratios (`analysis_tools.py:491,499`) and **does** auto-symmetrize a missing Down (`:570-571`, docstring `:308`).

**Counts and arithmetic** — 15 corpus systematics references (23 total − 8 ADL); m48's "9 of the 15" = 6 ttbar + 3 ttgamma, all nine files present; the §2.6 sketch carries exactly **104** ambient weight labels (pu 2 + pdf 102); the e-form renderings (`0.5→5em1`, `2.5→25em1`, `1.2345→12345em4`, `-1.5→m15em1`, `1e-8→1em8`, `50em2→5em1`, `20e-1→2`) and the cap illustrations (`1e40` → 41 digits, `1e-40` → the 5-char `1em40`) are all arithmetically correct; `1+|S|+|W|` vs axis-mode `1+|S|` and the 1-vs-`N+1` combine-slot count are internally consistent with §6.1c's key shape; `798/169 ≈ 4.7×`.

**Root prompt / catalog** — `graphed-root-prompt.md:25` (the "tens of thousands" sentence), `:1262` (R22.0's Phase-2 mention), `:1282` (R22.10's), `:1284` (the Out-of-scope header), and `ops_catalog.md:75` (verbatim "Systematics-as-a-graph-axis (named axes / template instantiation) — cf. RDataFrame `Vary`.") all confirmed; R0.4a/R0.5/R0.10/R0.10a/R0.11/R22.3 exist and say what the plan relies on.

---

## Verdict

**Dirty — but only just, and in one place.**

Of roughly 130 `file:line` anchors and 15 re-run measurements, exactly one substantive claim failed verification: §7.3's checkpoint/write-plan churn story (finding 1), which links `_PartitionReduce`/`_WritePart` to `task_id` through a `Plan → DurablePlan` bridge that does not exist in the pinned code and is contradicted by the repo's own documented checkpoint idiom. It is HIGH rather than MID only because two **frozen docs anchors** (m50, m51) would freeze the unconditional wording into user documentation. Everything else in the factual substrate — including every probe the plan claims to have measured, the `PYTHONHASHSEED` digest triple, the reduced-shape integers, the boost_histogram and pyarrow behaviours, the prior-art counts and quotes, and the r16 line-number corrections (`__init__.py:12,46`, `projection.py:147`) — reproduced exactly. The remaining three findings are one consolidated LOW on six drifted line spans and two NITs on attribution.

This is the cleanest facts round in the review series; r16 fixed the r15 defects it claims to have fixed, and the surviving line drifts are all one to three lines and none of them changes a meaning.
