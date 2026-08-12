# Review r19 — FACTS / HALLUCINATION AUDIT

- **Lens:** facts / hallucination audit (anchors, measured claims, research-doc citations, prior art, arithmetic).
- **Document reviewed:** `systematics-vary-plan.md` **r19** (4545 lines), read in full — header, Part I, all of PART II (§1–§12), the milestone anchor lists, the Anchors appendix, and the revision history.
- **Date:** 2026-07-30. Review round 11.
- **Reviewer context:** isolated agent, fresh context. Every claim below rests on a file I opened or a command I ran in this session.

## Verification roots used

| Root | Revision | Used for |
|---|---|---|
| `/private/tmp/claude-501/graphed-latest` | `ff7c607` | frontend/core/Rust anchors, live probes (its `.venv`) |
| `/private/tmp/claude-501/graphed-histogram-latest` | `211cbbe` | `boost.py`/`_spec.py` anchors, m23/m29 frozen tests, bh probes (its `.venv`, bh 1.8.0) |
| `/private/tmp/claude-501/graphed-exec-check` | `201ea42` | executors fixture facts, `submit/engine.py` |
| `/private/tmp/claude-501/graphed-corpus-latest` | `49650e4` | corpus analysis, references, ops catalog, catalog test |
| `/private/tmp/claude-501/uproot5-graphed` | `393ecef` (`graphed-mvp`) | RNTuple/TTree name hazards, `_graphed_write.py`, test-tree shape |
| `/private/tmp/claude-501/prior-art/{ewkcoffea,ewkcoffea-coffea2023,wwz4l}` | `063e8d7` / `63abb06` / `cc71718` | exemplar systematics claims |
| `/Users/lgray/vibe-coding/coffea-workdir` | `f34b8bdf` | JER-SF smear contract (§5.5) |
| clean env via `uv run --no-project --with awkward==2.12.0 --with pyarrow==25.0.1` | — | parquet writer/KV/dotted-name probes |

## Findings

### NIT-1 — three cited spans are off by one or two lines at an edge (meaning unchanged)

- **Section:** §6.1d (r19 `unweighted=` paragraph), §4.1, §6.1a/§9.1.
- **Detail:** Each claim is true; only the cited span edge is imprecise, and in two cases the plan itself cites the correct span elsewhere.
  1. §6.1d r19: “today's signature is `fill(self, *args, weight=None, sample=None, threads=None)`, `graphed-histogram src/graphed_histogram/boost.py:152-158`”. Measured @`211cbbe`: `:152` is the section comment `# ---- recording ----`; the signature runs `:153-159` (`def fill` at 153, `) -> Histogram:` at 159). §2.6 note (ii) cites the same signature correctly as `:153-163`.
  2. §4.1: “`graphed.numpy` ships donor-free `full`/`ones`/`zeros`/`empty`/`arange`/`linspace` … all in `__all__`, `python/graphed/numpy/__init__.py:578-598`”. Measured: `__all__` starts at `:578` but `"zeros"` is at `:599` and `"zeros_like"` at `:600`, i.e. the cited span excludes one of the six names it asserts. The claim itself is true (all six are exported).
  3. §6.1a / §9.1 / §7.3: `graphed_histogram.plan()` cited as `boost.py:254-292`. Measured: `def plan` at `:256`, the `aggregate_plan(...)` return runs `:286-295`. (§10/m50 cites `:256-292` for the same function — also two lines short at the tail.) Minor over/under-span; `:282` (layout) and `:286` (the `aggregate_plan` call) — the two lines r19's §7.2 seam argument actually turns on — are both exact.
- **Evidence:** `grep -n "" src/graphed_histogram/boost.py | sed -n '145,230p'` → `153: def fill(`, `159: ) -> Histogram:`, `256: def plan(`, `282: layout = tuple(...)`, `286: return aggregate_plan(`, `295: )`; `grep -n "" python/graphed/numpy/__init__.py | sed -n '576,600p'` → `578: __all__ = [` … `599: "zeros",`, `600: "zeros_like",`.
- **Suggested fix:** `:152-158` → `:153-159`; `:578-598` → `:578-601`; `:254-292` / `:256-292` → `:256-295`.

### NIT-2 — `ops_catalog.md:75` is cited without its repo-relative path

- **Section:** Scope-deviation block, Part I §1, §12.3(d).
- **Detail:** The row exists exactly as quoted, but the file lives at `graphed-corpus/docs/requirements/ops_catalog.md`, not at a repo root; §12.3(d) is an edit instruction, so the path matters to whoever executes it.
- **Evidence:** `grep -rn "Systematics-as-a-graph-axis" /private/tmp/claude-501/graphed-corpus-latest` → `docs/requirements/ops_catalog.md:75:- Systematics-as-a-graph-axis (named axes / template instantiation) — cf. RDataFrame \`Vary\`.` (verbatim match with the plan's quotation). The lock-step guard is likewise real and text-presence-only: `graphed-corpus tests/frozen/m05/test_catalog.py:13` points `CATALOG` at `docs/requirements/ops_catalog.md` and asserts substrings (`"ttbar_" in text`, `"M3"/"M4"/"M7"/"M9" in text`), so §12.3(d)'s "lock-step preserved" is accurate.
- **Suggested fix:** spell it `graphed-corpus docs/requirements/ops_catalog.md:75` at the three citation sites.

**No BLOCKER, HIGH, MID or LOW finding.** Everything else this lens checked was verified true, at the cited line, with the cited value.

## What was verified (the positive record)

### (a) r19's own changes — all re-measured, all correct

| r19 claim | Independent measurement |
|---|---|
| §2.2/§2.3a property rule splits by mechanism; `T` RECORDS | `NumpyArray.T` = `@property def T: return self.transpose()` (`python/graphed/numpy/array.py:159-161`); `transpose` → `record_op("transpose", …)` (`:154-157`). Probe on a 1-D numpy source: `dtype`/`ndim`/`shape` → `Session.node_count()` delta **0**; `T` → delta **1**. Discovered properties on `NumpyArray` = `['T','dtype','ndim','node_id','session','shape']`; `dir(Array)` public = `['filter','map','node_id','reduce','repartition','session']`; `dir(NumpyArray)` = **32** public names. All exactly as written. |
| §6.1a slot keying scoped to varied outputs; unvaried m23 must stay green | `graphed-histogram tests/frozen/m23/test_group_plan.py:74-75` (`out["hi"]`/`out["lo"]`), `:86` (`grouped["0"]`), `:89` (`grouped["1"]`), `:99` (`zero["hi"]`) — all four index the plan value by BARE output name; `plan()` declares `Plan[dict[str, bh.Histogram]]` at `boost.py:262`; `layout` is built over `(output_name, Histogram)` pairs at `:282` and consumed positionally at `:108-117`; `_add_groups` is `{label: a[label] + b[label] for label in a}` at `:120-122`. The r19 scoping is required exactly as argued. |
| m49 §8.2(i) image cardinality **2N+2**, of which **N+1** are `stage` | Re-ran the §3.3 builder (D=500, K=50) against `graphed-latest@ff7c607`: N=3 → reduced 8, kinds `{source:1, stage:4, reduction:3}`; N=16 → 34, `{1,17,16}`; N=128 → 258, `{1,129,128}`. Both halves of the r19 correction hold; the r18 "N+1 distinct reduced ids" would indeed have red-ed a correct accessor by ≈2×. |
| §2.1(b) row-space contract: `record_op` validates only `op_form` | `python/graphed/session.py:142-168` — `op_form` call at `:154` inside try/except, then `add_op`/`add_reduction`; no length or row-space check anywhere. Correct. |
| §7.2 `aggregate_plan` seam is needed | `aggregate_plan` compiles internally at `python/graphed/aggregate.py:95` and constructs the frozen `_PartitionReduce` at `:96-104` from pre-built closures (`:44-55`); `graphed_histogram.plan()` builds `layout` at `boost.py:282` BEFORE its `aggregate_plan` call at `:286`. The compiled output list is genuinely unreachable at both sites. |
| §7.2 schema key sets are literal, not comparative | `Plan` fields `{process,combine,empty,tasks,next_tasks,stop,open_once}` (`python/graphed/core/execution.py:206-217`); `ExecResult` `{value,n_partitions,n_combines,stopped}` (`:219-224`); `TaskEvent` `{phase,key,worker,t,partition,n_entries,bytes_read,error}` (`:335-351`); `emit_task(monitor, event)` passes the instance (`:378-384`). All three are dataclasses with class-level fields ⇒ a varied-vs-unvaried comparison is equal by construction, as r19 says. |
| §6.1b/§6.2 `sample=` is unchecked today | `boost.py:160-163` checks `args`, `:173-174` checks `weights`, `:177-178` appends `sample` with **no** type check. Correct. |
| mixed-granularity fixtures cannot execute (r19 restatement to per-event axes) | bh 1.8.0: `bh.Histogram(Regular(3,0,10),Regular(3,0,10)).fill(np.arange(3.),np.arange(5.))` → `ValueError: spans must have compatible lengths`. Evaluator flattens each axis independently at `boost.py:39-47,60-71`. Correct. |
| §2.6 sketch note (iii): the b-tag SF's operand is the **pt-cut** jets | `graphed-corpus src/graphed_corpus/analyses/systematics.py:60` `jets = _apply_jes(events.Jet, …)`, `:61` `good = jets[jets.pt > 25]`, `:74` `sel_jets = good[sel]`, `:76` `weight = _btag_weight(sel_jets, …)`, with `_btag_weight` = `ak.prod(per-jet SF, axis=1)` at `:25-36`. Exactly as claimed; the r19 correction is real and load-bearing. |
| §1.2 anchor drops "or token" | `GraphStore.nodes()` yields `{id, output, inputs, kind, name, params}`; a `stage` adds `n_members`/`members`, each member carrying `kind`/`name`/`params` (+`inputs`). No `#[pymethods]` member returns a token (`src/lib.rs`: `add_source/add_op/add_reduction/add_external/add_exchange/add_join/node_count/to_dot/serialize/deserialize/nodes/outputs/reduce/reduce_incremental/reduction_report`). Correct. |
| citation corrections `projection.py:145-146`, `boost.py:196-210` | `projection.py:145 if conservative or not needed:` / `:146 return None` / `:147 return tuple(sorted(needed))`; `boost.py:196 session.record_external(` … `:210 )`. Both exact. |
| §1.1 magnitude-count normalization | Arithmetic checks out: `"1.5e31"` → mantissa digits after dot-removal = 2, exponent adjusted for the decimal position = 30 ⇒ 32 plain digits (at the cap, legal); the naive `2 + 31 = 33` rejects it. `"1e40"` → 1 + 40 = 41 digits. `"1e-40"` → `1em40`, 5 chars. |

### (b) Measured/probe claims re-run in-session

- **§3.3 / §5.2a topology numbers.** N=16 → 1333 reachable / 34 reduced / 17 stages / 3.78 ms; N=128 → 7157 / 258 / 129 / 21.7 ms (plan: 3.77 / 21.28 — timing noise only). Node ratio 5.37, time ratio ≈5.6 ✓. Without the terminating reduction: reduced = N+2 (18 / 130) ✓. Arena Δ(N=1→2) = **52** with the reduction, **51** without ✓. Threshold arithmetic: `ln24/ln8 = 1.53`, `ln24/ln5.37 = 1.89`, `5.37² = 28.8`, `16.0/5.64 ≈ 2.8` — all as stated.
- **§7.2 optimizer-merge probes.** `nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5` → record ids `0,1,2,3`; `compile_ir(s, nom,m1,m2,mh)` → `outputs() == [0,1,2]`. Two structurally identical outputs → **one** compiled output; two distinct → two. Re-recording `src*2.0` twice → same node id, `a is b` False, `node_count()` unchanged. All as claimed.
- **§8.2(i)/§7.3 pickle determinism.** cloudpickle 3.1.2, `PYTHONHASHSEED ∈ {1,7,12345}`, payload `(3, frozenset({...5 labels...}))` → `b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831` — **byte-for-byte the plan's triple**. Importable frozen dataclass + sorted tuple → `80e8024dc8f3b77d` ×3; + `frozenset` → 3 distinct; `__main__`-defined + tuple → 3 distinct. Exactly the r18/r19 claims.
- **boost_histogram probes (1.8.0).** `StrCategory(..., name=...)` → `TypeError`; `h[{"variation": label}]` → `TypeError: list indices must be integers or slices, not str`; `h[{1: ax.index(l)}]` equals `h[{1: bh.loc(l)}]`; `h.axes.name` → `AttributeError: object Regular has no attribute name` on a two-axis histogram; cross-axis `+` → `ValueError: axes have different length`; under-declaration `sum 2.0` vs `sum(flow=True) 3.0` with `Traits(overflow=True, growth=False)`; over-declaration `3.0 == 3.0` (invisible). Axis name round-trips `spec_of`→`zero_of` as `[None, 'variation']`.
- **awkward/gak probes (ak 2.12.0).** `w[:, 1]` → `TypeError: unsupported index (slice(None,None,None), 1)`; `gak.firsts(w[gak.local_index(w)==1])` over `[[1,2,3],[4,5,6]]` → `[2.0, 5.0]`; `ak.broadcast_arrays` 7 vs 3 → `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7` (jagged case fine); `float32 ^ float32` → `TypeError`, `a.view(np.uint32) ^ b.view(np.uint32)` fine.
- **parquet probes (ak 2.12.0 / pyarrow 25.0.1, clean resolve).** `"metadata" in signature(ak.to_parquet)` → **False**; `ak.to_parquet` vs `pq.write_table(ak.to_arrow_table(...))` → different bytes; KV list-of-float `{ARROW:schema, awkward_array_metadata}` vs `{ARROW:schema}`; record adds `ak:parameters` (data-dependent, as the plan says); `created_by = "parquet-cpp-arrow version 25.0.1"`; repeat writes byte-identical; `ak.from_parquet(p, columns=["murf_0.5"])` → **empty** (fields `[]`, len 0). Every §6.4e/§6.4g claim reproduces.
- **Discovery-rule measurements.** Annotation-wide filter over `graphed.__all__` → exactly `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']` (8; six *refusing* + two *expanding*, as §2.3d's arithmetic says); `compile_ir(session: 'Session', *outputs: 'Any', …)` is absent from it and present in `__all__` (`__init__.py:12,46`; `:44` is `"apply"`). `graphed.awkward.functions`: **73** `def`s, **65** public, **0** `__all__`; the package `__all__` (`:17-31`) exposes exactly six package-level functions, none of them gak's; the `graphed.awkward` alias discovers **0** gak functions and `graphed.awkward.num` raises `AttributeError`. `tests/frozen/awkward/m24/test_interface_parity.py:39-79` is a **39**-name literal.
- **Compression numbers (§6.4c).** Match the worklog verbatim (`raw=3.551MB ratio=2.883 delta=3.193 xor=3.280`; masks `798KB` → `169KB`, 798/169 = 4.7×), and the worklog states its methodology (float32, 1M elems, zlib-6, seed 42, synthetic JES-like) — R0.11-conformant.

### (c) Anchor spot-checks (line-exact unless noted)

Rust: `store.rs:73-88` (intern), `:147-156` + `:152-153` (`mark_output` dedup), `node.rs:39-41`, `:102-103` (`is_boundary`), the whole `NodeKey` enum with variant heads at **`:42,46,51,56,64,72,81`** (all seven exact), `engine.rs:7-13,22-31,54-56,67-80,89-110`, `optimizer/mod.rs:1-11,88-116` (`remap` local, never returned), `lib.rs:102,159,470` (three `#[pymethods]` blocks; the `GraphStore` method list matches verbatim).

Python frontend: `session.py:30,39,50,113,133/140,142/168,170/183,185/204,206/242,245-252,268,291-301` and the five `_provenance.setdefault` sites `:138,166,181,202,240` (all exact; `_array_cls` appears only in `session.py`); `array.py:128,137-143,332-335,344-371,374-391,397-410,283-290`; `numpy/array.py:74,78,82,86,132-136,154-161`; `execute.py:36-45,54-58,70,85-91,96-126,104-105,109,110-115,116-124,126`; `aggregate.py:44-55,57-65,68,86,89-93,95,96-104,101`; `projection.py:109,145-146,147`; `shuffle.py:84,89,92,142,155,170 (exchanges[0]),181,188,208,220,232 (first join via next()),245,259`; `write.py:32-43,77-79`; `awkward/io.py:111-127,121,157,206-216`; `numpy/io.py:163-171`; `numpy/creation.py:27-28,31-75`; `core/plan.py:54,72-76,126,164-176,286-301`; `checkpoint/runner.py:77-91,100-109`; `checkpoint/store.py:31-41,62-73`; `debug/errors.py:29,75-78,80-81`; `debug/runner.py:6-7,37,57-69`; `preserve/bundle.py:103-123` (incl. the `weight=`/`histogram=` together guard), `:206-210`, `:268`; `parquet.py:77` is indeed the only metadata USE; exactly two `StageError(` hits in `python/graphed/`; zero `DurablePlan(` in `python/`.

graphed-histogram: `boost.py:39-47,60-71,88-98,100-117,120-122,127-130,146-150,153-163,160-161,175-178,180-212,196-210,215-219,245-255,262,282,283-286`; `_spec.py:31-37,70,74,81-84,115,129`; frozen `m23:60-66,68-77,74-75,86,89,99`; `m29:75-79,84-87,96`.

Fixture facts: `graphed` vendors **23** reference JSONs (15 systematics + 8 ADL) with `tests/_corpus` on `pythonpath` (`pyproject.toml:115-127`), declares no `graphed-histogram` in any extra (`:42-48`) while CI installs `.[dev]` (`ci.yml:34,57,143`), and the `importorskip` house pattern exists at `preserve/m25:31`, `m27:185,207`, `m30:155`. `run-tests.sh:16-25` + `:30` (`SPLIT_PKGS="frontend numpy awkward"`); **0** `__init__.py` under `tests/frozen`; `tests/frozen/checkpoint` holds only `m8`/`m39`; `debug/m6/test_process_boundary.py:7,16` is the only cross-process frozen test. `graphed-histogram`: runtime deps `pyproject.toml:21`, dev `:25-39`, `pythonpath` `:50`, `ci.yml:44,67` one-process `pytest tests/frozen`, **0** corpus hits, **0** `__init__.py`, existing `m23`/`m29`. `graphed-executors`: **15** milestone dirs, **0** `graphed-histogram` references, env `ci.yml:13-17` = `GRAPHED`+`CORPUS` only, frozen runs at `:44,67,101,153`, **0** `task_id`/`DurablePlan` in `src`, `submit/engine.py:381-396` translate-only. `graphed-corpus pyproject.toml:28-30` packages only `src/graphed_corpus`. PyPI `graphed-histogram` → single release `0.0.1`. `uproot5-graphed@393ecef`: **12** flat `tests/test_graphed_*.py` + 2 helpers, no frozen tree, zero `tests/frozen` references, `_graphed_write.py:59-64` verbatim branch copy with zero `compile_ir`/`evaluate_ir`.

uproot name hazards: `behaviors/RNTuple.py:1560-1562` exact-first lookup, `:1564-1569` dot-split fallback, `:562,567` `to_akform` path split on `.`; `writing/_cascadetree.py:1606` joins nested fields with `.`; `behaviors/TBranch.py:2015-2017` exact-first, `:2019-2024` `/`-split. All exact.

Root prompt / catalog: `graphed-root-prompt.md:25` (the "tens of thousands" founding sentence), `:1262` (R22.0) and `:1282` (R22.10) both carrying "systematics-as-a-graph-axis … stay Phase 2", `:1284` header, `:1285` blank, `:1286-1287` the Out-of-scope sentence — the r18 correction is right.

### (d) Research-doc citations

- `cba §optimizer §2` carries the exact table the plan quotes (N=16 → 1333 nodes / 3.1 ms / 34 / 17; N=128 → 7157 / 16.7 ms / 258 / 129) and the "12.9× nodes → 11.9× time" line; the plan's explicit warning that the cba uses **D** for the per-universe chain while §3.3 uses **D** for the shared prefix and **K** for the chain is accurate and prevents a real misreading.
- `cba §optimizer §5` states prefix-sharing TRUE and the grep-verified absence of any dirty/invalidation machinery — as the plan says.
- `cba §histogram §1` does scope its "no constant-Array constructor" grep to the session/array modules (§4.1's correction is a fair reading); `§3` carries the StrCategory/growth probes.
- `lit §rdf-vary §5` carries the arXiv:2212.04889 "largest pain point in analysis software" quote; `§6` the naming vocabulary; the assessment carries "Experimental namespace for 4+ years".
- `lit §coffea-sys §5` line **236** carries the #469 "~2-3× … up to ~7-8×" figure **with** the "summarizing fetch / word-level UNVERIFIED" caveat the plan reproduces.
- `lit §ewkcoffea-confirmed` line 411 gives "12 bases → 24 labels (Run 2); 10 → 20 (Run 3)" and line 415 "31 (R2) / 27 (R3) = 1 + 24|20 + 6" — the plan's "24 labels / 6 object-shift labels / 7-pass loop" (0.7-era) and "27 labels" (wwz4l, Run-3-only) both follow. Line 545 records the **522** identical-line measurement.

### (e) Prior art, checked against the clones

- `ewkcoffea@063e8d7`: 10 common weight bases + 2 R2-only = **12** → 24 up/down labels; `obj_correction_systs` = 3 → 6 labels; `obj_corr_syst_var_list = ["nominal"] + 6` ⇒ the **7-pass** outer loop (`wwz4l.py:454-467`); the impact-partition comment "These weights can go outside of the outside sys loop since they do not depend on pt of mu or jets" at `:396`; the nominal-only exclusion rule at `:1204-1207`.
- `ewkcoffea@coffea2023@63abb06`: `masked_val_cache`/`masked_weights_cache` hand-written CSE at `:808-809,851-865`; `copy.copy(weights_obj_base) # TODO do we need copy here?` at `:342`; empty `obj_correction_systs` at `:331`; `hout = {}` at `:807` **inside** the shift loop opened at `:339`; `run_wwz4l.py:259-261` `# Does not work` above the commented `cloudpickle.dump`; timing block at `:302-313`.
- `FNALLPC/wwz4l@cc71718`: **zero** `dask`/`dataset_tools`/`hist.dask` hits repo-wide; `ApplyJetSystematics` byte-identical to `ewkcoffea@main`'s (14 lines, exact equality); processor line overlap independently measured at 509 (non-blank matched) / 524 (membership) / 658 (all matched blocks) — brackets the lit doc's 522 under its own method.
- coffea `@f34b8bdf`: `rand_gauss` seeds `PCG64` from the input array's own bytes (`CorrectedJetsFactory.py:36-47`); `jer_smear(:65-95)` takes ONE `jet_resolution_rand_gauss` while only `jersf = ...[:, variation]` varies (`:84`); signed `deltaPtRel` (`:85`) with hybrid `detSmear`/`stochSmear` (`:88-89`) ⇒ non-monotone by construction. Every §5.5 clause is grounded.

### (f) Arithmetic and counts

- 15 stored systematics references confirmed by name (`ttbar_4j1b|4j2b × {nominal,jes_up,jes_down,btag_up,btag_down}` + `ttgamma × {nominal,jes_up,jes_down,pho_up,pho_down}`); m48's weight matrix "6 + 3 = **9 of the 15**" is exact; the vendored copy holds 23 JSONs (15 + 8 ADL) as claimed.
- `1 + |S| + |W|` (sibling) vs `1 + |S|` (axis) are mutually consistent under r19's lowering-behaviour definitions of `S`/`W`.
- §3.3 threshold arithmetic (5.37× nodes, 5.64× time, gate 16.0, ln-exponents 1.53 / 1.89, quadratic 28.8) — all reproduce.
- §8.2(i) image cardinality 2N+2 = 1 source + 1 prefix stage + N universe stages + N reductions, matching `stages == N+1` — internally consistent and measured.
- §2.3d "six refusing and two expanding" over the 8 discovered verbs — consistent with the dispositions §2.3d assigns.
- §6.4c "~4.7×" = 798 KB / 169 KB ✓.

## Verdict

**CLEAN for this lens.** Round 11 found **no BLOCKER / HIGH / MID / LOW** factual defect. Every `file:line` anchor I opened in the pinned verification roots contained the claimed content (including the ones r19 newly introduced or corrected), every cheap measured claim I re-ran reproduced — several of them digit-for-digit, including the cloudpickle seed triple and the reduced-graph kind counts — every citation into `systematics-vary-codebase-analysis.md` / `systematics-vary-litsearch.md` said what the plan says it says, every prior-art claim held against the clones, and the arithmetic (label counts, "9 of 15", fill arity, compression ratio, benchmark exponents) is sound. The two NITs are line-span/pathing polish that change no meaning.

Two notes for the record, not findings: (1) r19's honest reconciliation of the cba's `D` (per-universe chain) vs the plan's `K` is exactly the kind of collision that would otherwise have produced a wrong frozen literal — it is correct as written; (2) the plan's practice of carrying the *withdrawal* of superseded measurements (the r12 parquet digests, the r13 unnamed-payload digests, the r17 `h.axes.name` row) is what made this audit fast and is worth preserving in future revisions.
