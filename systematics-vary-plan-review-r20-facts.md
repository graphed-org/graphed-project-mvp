# systematics-vary-plan review — round 12, FACTS / HALLUCINATION lens

- **Lens:** facts / hallucination audit (file:line anchors, measured claims, research-doc citations,
  prior-art claims, arithmetic and counts). Design and test-authoring concerns are out of scope here.
- **Plan revision reviewed:** r20 (`systematics-vary-plan.md`, 4841 lines, read in full including
  Part I, every PART II section, §10 milestones, §11, §12, the Anchors appendix and the revision
  history).
- **Date:** 2026-07-30.
- **Verification roots used (every code fact below was re-read/re-run in these, never in the stale
  workdir submodules):**
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607`) + its `.venv`
    (CPython 3.12.10, awkward 2.12.0, numpy 2.5.2, cloudpickle 3.1.2)
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`) + its `.venv` (boost_histogram 1.8.0)
  - `/private/tmp/claude-501/graphed-exec-check` (`graphed-executors`, `201ea42`)
  - `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`)
  - `/private/tmp/claude-501/uproot5-graphed` (uproot fork, `393ecef`)
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06,
    wwz4l@cc71718, WRemnants, narf, mkShapesRDF}`
  - `/Users/lgray/vibe-coding/coffea-workdir` (`f34b8bdf`)
  - ephemeral `uv run --no-project --with awkward --with pyarrow` env (pyarrow 25.0.1) for the
    parquet probes
  - the companion docs (`…-codebase-analysis.md`, `…-litsearch.md`, `…-worklog.md`) and
    `graphed-root-prompt.md`

**Bottom line: this lens is essentially clean.** Three findings, all LOW/NIT, none touching a
requirement. Everything load-bearing that I could test reproduced — including every r20-new measured
claim.

---

## Findings

### 1. LOW — §10/m48, the r20 `aggregate_plan`-seam anchor: "graphed's only existing coverage of it is m5's" is false as measured

**Section:** §10, m48 frozen anchors, bullet "**§7.2's r19 `aggregate_plan` SEAM (α), in `graphed`'s
`tests/frozen/frontend/m48`** (r20 …)" (plan lines ~3002-3013).

**Detail.** The bullet's placement rationale asserts, as a measured fact, "measured, no other
`graphed` m48 anchor calls `aggregate_plan`, and `graphed`'s only existing coverage of it is m5's."
The first half is true by inspection of m48's own anchor list. The second half is not: the frozen
m39 suite also calls `aggregate_plan` (as the two-source-rejection control).

**Evidence (measured this session, `graphed-latest@ff7c607`):**

```
$ grep -rln "aggregate_plan" tests/frozen
tests/frozen/frontend/m39/README.md
tests/frozen/frontend/m39/test_shuffle_plan_builder.py
tests/frozen/frontend/m40/test_join_plan_builder.py
tests/frozen/frontend/m5/test_aggregate_plan.py
```

`tests/frozen/frontend/m39/test_shuffle_plan_builder.py:18` imports it and `:58-64` calls it:

```
58: def test_single_source_aggregate_plan_is_unchanged() -> None:
64:         aggregate_plan(a, b, reduce=lambda vs: vs, combine=lambda x, y: x, empty=lambda: None)
```

(`m40/test_join_plan_builder.py:3` is only a docstring mention, so m39 is the one real second
caller.)

**Impact:** none on the requirement — the seam is NEW `graphed` source in
`python/graphed/aggregate.py` and still needs an m48 frozen anchor for the DoD's
≥90 % diff-coverage-from-the-frozen-suite gate, whatever pre-existing coverage `aggregate_plan` has.
Only the supporting sentence is wrong.

**Suggested fix:** replace "and `graphed`'s only existing coverage of it is m5's" with "and
`graphed`'s existing frozen coverage of it is m5's positive path plus m39's two-source-rejection
control (`tests/frozen/frontend/m39/test_shuffle_plan_builder.py:58-64`) — neither exercises a
seam that does not yet exist."

---

### 2. LOW — §7.3 / §10-m49: the `80e8024dc8f3b77d` digest is not reproducible as recorded (the plan's own r14 standard), while the §8.2(i) triple is

**Sections:** §7.3 ("measured this session … an importable frozen dataclass carrying a SORTED TUPLE
of labels digests identically across all three seeds (`80e8024dc8f3b77d` ×3) …", plan lines
~2458-2465) and the same digest repeated in §10/m49's §8.2(i) anchor (~3598-3600).

**Detail.** r13→r14 set an explicit in-document standard: a digest is only admissible if the payload
and toolchain are named "so the probe is reproducible" (that is why the r12 §6.4e sha256 pair was
withdrawn, appendix row "…the r12 row's two sha256 digests are withdrawn — they named no array").
The `80e8024dc8f3b77d` literal names cloudpickle 3.1.2 and the seeds but not the module, class name,
or field names of the "importable frozen dataclass", and cloudpickle bytes depend on all three, so it
cannot be re-run. The QUALITATIVE claim it supports does reproduce, and so does the §8.2(i) triple —
which is the one that actually binds an anchor.

**Evidence (measured this session, cloudpickle 3.1.2, CPython 3.12.10):**

- §8.2(i)'s named payload reproduces **exactly**:
  `sha256(cloudpickle.dumps((3, frozenset({"btag_down","btag_up","jes_down","jes_up","nominal"}))))[:16]`
  → seed 1 `b7984b3caadf74f7`, seed 7 `2778da7a97834ac5`, seed 12345 `97429e5989f2a831` —
  identical to the plan.
- §7.3's qualitative claim reproduces with my own module-level dataclass
  (`/private/tmp/claude-501/rev12mod/vmod.py`): importable + sorted tuple → one digest ×3
  (`7c822d415da97a9c`, not `80e8024dc8f3b77d`); importable + `frozenset` → 3 distinct
  (`1bfd03e223e59c18` / `d23abc88b6776a1b` / `79820cdadc935059`); `__main__`-defined + sorted tuple
  → 3 distinct (`e7829dc850eedf13` / `054274c5a1dc835f` / `a7afaa3565b76b31`). The differing literal
  is purely an artifact of the unnamed class.
- Bonus fact that *strengthens* §8.2(i) and is worth recording: the pickle bytes of a `frozenset`
  depend on its **construction order**, not only its content. At a fixed `PYTHONHASHSEED=1`,
  `frozenset(("btag_down","btag_up","jes_down","jes_up","nominal"))` → `dcbaefaddebcaf1b` while the
  equal `frozenset({...})` set-literal → `b7984b3caadf74f7` (`a == b` is True). So a `frozenset`
  field is nondeterministic even at a *fixed* seed if two code paths build it differently.

**Suggested fix:** either name the fixture module/class/fields alongside the digest, or drop the
literal and keep the reproducible qualitative form ("one digest across all three seeds vs three
distinct"). Optionally add the construction-order measurement above to §8.2(i)'s rationale — it
closes a residual "but we always build it the same way" objection.

---

### 3. NIT — a handful of one-to-three-line citation-range drifts (content correct in every case)

**Sections:** scattered. Each cited range still *contains* the quoted content, so no meaning changes;
listed only for the record.

| Plan citation | Measured |
|---|---|
| `graphed-root-prompt.md:25` (the "On real analyses with many systematic variations…" quote, Part I §1) | the sentence begins at `:24` and runs `:24-26` |
| `graphed-histogram …/boost.py:152-158` (fill signature, §6.1d r19) | signature is `:153-159`; `:152` is a section comment |
| `…/boost.py:254-292` / `:256-292` (`plan()`, several sites incl. §7.2 r18, §6.1a) | `def plan` is `:256`, the function ends at `:295` (its `aggregate_plan` call is `:286-295`) |
| `…/boost.py:245-255` (`Histogram.plan` passing `_SumFills`/`_ZeroHist`, §6.1c) | the `aggregate_plan` call is `:244-253` |
| `python/graphed/aggregate.py:68-107` (§9.1, m50 anchor) | `aggregate_plan` is `:68-108` |
| `graphed pyproject.toml:114-127` (`pythonpath`) | the list is `:115-127`; `:114` is a comment |
| `python/graphed/numpy/__init__.py:578-598` (`__all__`) | `__all__` is `:578-601` |
| `tests/frozen/preserve/m9/agc.py:94-118` (`record()`) | `def record` is `:93` |

**Suggested fix:** correct on the next revision pass, or leave — none is load-bearing.

---

## Verified clean (what I checked and found accurate)

Recorded so a later round does not re-litigate ground already measured.

**Anchors appendix — spot-checked ~60 of the rows against the pinned roots; every one held**, including
the two rows that make explicit completeness claims:

- `src/node.rs:41-85` "the WHOLE enum" with variant heads at `:42` Source, `:46` Op, `:51` Reduction,
  `:56` External, `:64` Stage, `:72` Exchange, `:81` Join — **all seven exact**, enum closes at `:85`.
- `src/lib.rs` three `#[pymethods]` blocks at `:102`, `:159` (GraphStore, closing `:416`), `:470`;
  the GraphStore surface is exactly
  `add_source/add_op/add_reduction/add_external/add_exchange/add_join/node_count/to_dot/serialize/
  deserialize/nodes/outputs/reduce/reduce_incremental/reduction_report` — matches the plan's
  enumeration verbatim, and no member returns an id map.

Other verified anchors (non-exhaustive): `src/store.rs:73-88` (intern) and `:147-156`/`:152-153`
(`mark_output` de-dup); `src/node.rs:39-41`, `:102-103`; `src/optimizer/engine.rs:7-13` (extraction
note), `:22-31` (`SYMMETRIC_OPS`/`IDENTITY_TOKENS` exactly), `:54-56`, `:67-80`, `:89-110`;
`src/optimizer/mod.rs:1-11`, `:88-116` (`remap` built and never returned);
`session.py:30,39,50-51,113-125,133-140,142-168,170-183,185-204,206-242,245-252,255-288,291-301`
(including: the five `_array_cls` return sites `140/168/183/204/242`, the five
`_provenance.setdefault` sites `138/166/181/202/240`, `record_op` validating only the backend's
`op_form` and never lengths, and **zero** `_array_cls` hits outside `session.py`);
`array.py:54,127-128,137-143,156,245-275,283-290,332-335,344-371,374-391,397-410`;
`numpy/array.py:71-74,76-86,92-190,132-136,154-161`; `numpy/creation.py:27-28,31-75`;
`projection.py:109,145-146,147`; `execute.py:36-45,54-70,85-91,96-126,104-105,109,110-115,116-124,126`;
`aggregate.py:44-55,57-65,68-108,86,89-93,95,96-104,101`;
`core/execution.py:206-217,219-224,335-351,378-384,450-457` (all three schema key sets match the
literals m48 freezes); `core/plan.py:53-54,72-76,125-126,164-176,286-301`;
`checkpoint/runner.py:77-91,100-109`; `debug/errors.py:29,75-78,80-81`; `debug/runner.py:6-7,37,57-69`;
`provenance.py` (frozen 4-field dataclass); `awkward/io.py:98-127,121,157-185,206-216,239,260,274`
(`to_parquet` has **no** `select=` today); `awkward/functions.py:18,118-119,346,383,400,476,513,600,
612-616,673,677,687,693,717,722,727,732,737`; `awkward/__init__.py:14,17-31,30`; `write.py:32-43,77-79`;
`preserve/bundle.py:103-123,206-210,268-288`; `shuffle.py:84,89,92-96,142,155,170,181,188,208,220,232,
245,259`; `parquet.py:77` + **0** hits for `key_value_metadata`/`with_metadata` in both `graphed` and
the uproot fork; `graphed-histogram boost.py:39-47,60-71,87-98,101-117,120-122,125-130,144-150,153-212,
215-219,226-253,256-295,262,282,285-286` and `_spec.py:31-37,70,74,81-84,115-135`;
`uproot5-graphed behaviors/RNTuple.py:562,567` (inside `to_akform`, which starts `:505`) and
`:1560-1562,1564-1569` (inside `__getitem__`, `:1541`), `behaviors/TBranch.py:2015-2017,2019-2024`,
`writing/_cascadetree.py:1606`, `writing/_graphed_write.py:59-64` (zero `compile_ir`/`evaluate_ir`);
`coffea …/CorrectedJetsFactory.py:36-47` (PCG64 seeded from the array's own bytes) and `:65-97`
(one `jet_resolution_rand_gauss`, `jersf = …[:, variation]`, signed `deltaPtRel`, hybrid
det/stochSmear).

**Fixture/CI facts:** `graphed pyproject.toml:29-48` has no `graphed-histogram` in any extra and CI
installs `.[dev]` at `ci.yml:34,57,143`; `tests/_corpus/{graphed_corpus,references}` with **23** JSONs
on `pythonpath`; `scripts/run-tests.sh:16-25,30` (`SPLIT_PKGS="frontend numpy awkward"`); **zero**
`__init__.py` under `tests/frozen`; `tests/frozen/checkpoint` = `m8`,`m39`; `core/m4/test_benchmark.py`
and `preserve/m9/{test_reproduce,test_inspect}.py` exist (the basename-collision hazard is real);
`graphed`'s only cross-process frozen test is `debug/m6/test_process_boundary.py` (grep for
multiprocessing/spawn over `tests/frozen` returns only m6 + an m41 README);
`graphed-histogram`: runtime deps `["graphed","boost-histogram>=1.4","numpy>=1.24"]` (`:21`), awkward
dev-only (`:25-39`), `pythonpath = ["src","tests/frozen/m23"]` (`:50`), **0** corpus hits in
`tests/`+workflows, **0** `__init__.py`, `tests/frozen` = `m23`,`m29`, one-process
`pytest tests/frozen` at `ci.yml:44,67`, env carries `GRAPHED`+`EXECLOCAL` only, version `0.0.1`;
`graphed-executors`: deps `["graphed"]`, dev extra `:24-35` with `graphed-corpus` and **no**
`graphed-histogram` (0 grep hits repo-wide), env `GRAPHED`+`CORPUS` at `ci.yml:13-17` installed at
`:38,65,94,136`, frozen suite at `:44,67,101,153`, **15** existing milestone dirs, **0**
`task_id`/`DurablePlan` in `src/`; `graphed-corpus` wheel packages only `src/graphed_corpus`
(`:28-29`) while the 15+8 references live in `corpus/references/`; uproot fork has **no** frozen tree,
**12** flat `test_graphed_*.py` + 2 helper modules, **0** `tests/frozen` references.

**Re-run measurements (all reproduced):**

- §3.3/§5.2a topology (D=500, K=50): N=16 → 1333 nodes / reduced 34 / 17 stages; N=128 → 7157 /
  258 / 129; best-of-5 3.6 ms → 21.2 ms. Δ(N=1→2) = **52** with the terminating reduction, **51**
  without. Node ratio 5.37; the m4-style arithmetic (ln24/ln8 = 1.53, ln24/ln5.37 = 1.89,
  5.37² ≈ 28.8, 28.8/24 = 1.2, 16/5.64 = 2.84, 28.8/16 = 1.8) is correct throughout.
- §8.2(i) r20 cardinality: base fixture N=3 → reduced 8 / `{source:1, stage:4, reduction:3}`,
  N=16 → 34 / `{1,17,16}` (= `2N+2` / `N+1` stages), unchanged by a dead branch; shared-node
  extension N=3 → 9 / `{1,5,3}`, N=16 → 35 / `{1,18,16}` (= `2N+3` / `N+2`). Exactly as r20 states —
  the scoping of the cardinality literals to the base fixture is measurably necessary.
- §7.2 merge probes: fresh session `w, w*1.0, w*2.0, w*0.5` → record ids `0,1,2,3`,
  `compile_ir(...).outputs() == [0,1,2]`, `evaluate_ir` returns 3 values; on the fill path, two fills
  weighted `w` vs `w*1.0` → fill nodes `2`,`4` → `outputs() == [2]`. Structurally identical outputs
  compile to 1 value, distinct ones to 2. `a = src*2.0; b = src*2.0` → both node id 1, `a is b` False,
  `node_count() == 2`.
- §2.2/§2.3a property surface: `dir(Array)` public = `['filter','map','node_id','reduce',
  'repartition','session']`; `NumpyArray` adds `T/dtype/ndim/shape` for **32** public names (26
  methods + 6 properties); discovered properties `['T','dtype','ndim','node_id','session','shape']`;
  `node_count()` delta on a 1-D source: `dtype`/`ndim`/`shape` → 0, `T` → 1; on a 2-D partitioned form
  `gnp.ones(s,(4,3)).T` raises `GraphedTypeError: ill-typed op 'transpose' … displacing the
  partitioned axis 0` (so r20's 1-D fixture pin is necessary).
- §2.3c/d discovery: annotation-wide filter over `graphed.__all__` yields exactly
  `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition',
  'shuffle_plan']` (8) and misses `compile_ir` (annotations `Session`/`Any`), which IS in `__all__`
  (`__init__.py:12,46`; `:44` = `"apply"`); gak has **no** `__all__` (grep 0), **73** `def`s / **65**
  public functions in `graphed.awkward.functions`, and the package alias discovers **0**
  (`graphed.awkward.num` → AttributeError); the package `__all__` (`:17-31`) lists exactly the six
  package-level functions the plan names.
- boost_histogram 1.8.0: `StrCategory(name=…)` → TypeError; `h[{"variation": …}]` → `TypeError: list
  indices must be integers or slices, not str`; `h[{1: ax.index(l)}]` == `h[{1: bh.loc(l)}]`;
  `h.axes.name` → `AttributeError: object Regular has no attribute name` on a two-axis histogram
  while `[a.__dict__.get("name") for a in h.axes] == [None,'variation']` and survives
  `spec_of`→`zero_of`; non-growth `StrCategory` traits `overflow=True, growth=False`, under-declaration
  `sum 2.0` vs `sum(flow=True) 3.0`, over-declaration `3.0 == 3.0` (invisible); cross-axis addition
  → `ValueError: axes have different length`; two Regular axes filled with lengths 3 and 5 →
  `ValueError: spans must have compatible lengths` (so r19's same-granularity fixture restatement is
  necessary).
- awkward 2.12.0 / numpy 2.5.2: `ak.broadcast_arrays` over lengths 7 and 3 → `ValueError: cannot
  broadcast RegularArray of size 3 with RegularArray of size 7`, jagged 3-row broadcast fine;
  `float32 ^ float32` → `TypeError` for both `np.ndarray` and `ak.Array`, `a.view(np.uint32) ^ …`
  works.
- pyarrow 25.0.1: `ak.from_parquet(columns=["murf_0.5"])` → `fields []`, length 0 (silently empty)
  while `["murf_1"]` reads; `"metadata" in signature(ak.to_parquet)` → False; `ak.to_parquet` repeat
  writes byte-identical; `ak.to_parquet` vs `pq.write_table(ak.to_arrow_table(...))` differ in bytes
  and the arrow path drops `awkward_array_metadata` (`ARROW:schema` always present; `ak:parameters`
  present for a record array, absent for a list-of-float — i.e. array-dependent, as the plan says);
  `ParquetFile(...).metadata.created_by == "parquet-cpp-arrow version 25.0.1"`.
- Frontend sketch spellings: `w[:, 1]` → `TypeError: unsupported index (slice(None,None,None), 1)`;
  `gak.firsts(w[gak.local_index(w) == 1])` over `[[1,2,3],[4,5,6]]` materializes `[2.0, 5.0]`.
- §6.3 params key set on a real unvaried single-weight fill: `['n_axes','sampled','spec','weighted']`
  — exactly the literal m48 freezes.
- CPython 3.12.10 admits non-identifier keys through `**`-unpacking (`f(**{'0p5':1,'2':2})`).
- `OpSpec.from_callable(_PartitionReduce(...)).kind == "opaque"`, `_PartitionReduce` has no
  `__qualname__`; `grep -rn "DurablePlan(" python/` → 0; `OpSpec.from_callable` only at
  `shuffle.py:181,188,245,259`.

**Counts and arithmetic:** 15 systematics references (10 ttbar + 5 ttgamma) of 23 total JSONs, and
m48's subset "ttbar 4j1b/4j2b × {nominal, btag_up, btag_down} (6) + ttgamma {nominal, pho_up,
pho_down} (3) = **9 of the 15**" checks out; m24's anti-drift pin is a **39**-name literal at
`:39-79` (counted); `1 + |S| + |W|` vs `1 + |S|` are internally consistent with §2.4; §1.1's cap
arithmetic is right (`1.5e31` → `15` + 30 zeros = **32** digits, legal; `1.5e32` → 33, rejected;
`1e40` → 41; `1e-40` → the 5-char `1em40`; the naive "mantissa digits + exponent" gives 33 for
`1.5e31`, so the accepted half of the boundary pair is genuinely the discriminating one); the
e-form renderings (`0.5`→`5em1`, `2.5`→`25em1`, `1.2345`→`12345em4`, `-1.5`→`m15em1`,
`"50em2"`→`5em1`) are all correct; §6.4c's compression figures (raw 3.551 MB / ratio 2.883 /
XOR 3.280; masks 798 KB → 169 KB ≈ 4.7×) match the worklog entry, which states its methodology
(float32, 1M elems, zlib-6, seed 42, 5 masks flipping ~3%).

**Research-doc citations:** `systematics-vary-litsearch.md:236` does carry the word-level UNVERIFIED
caveat on coffea Discussion #469 (~2-3×, up to ~7-8×), exactly as §Part I §2 represents it;
cba §optimizer §2's table (N=1 → 553/1.4 ms … N=128 → 7157/16.7 ms) supports both the "12.9× nodes
→ 11.9× time" figure (the N=1→128 span) and the "5.37×/5.64×" figure (the N=16→128 span) without
contradiction, and the plan explicitly flags the D/K notation clash with the cba; cba §histogram §3
does record the scalar-string-broadcast and non-growth combine-safety probes §6.2 cites; cba §corpus
§1/§3/§4/§5 support the Part I §1 claims (15 references, m05 behavioral invariants at
`test_systematics.py:26-38`, m9's one-graph-per-variation config, the graph-bloat O(10⁴) figure).

**Prior art (checked against the clones):** `ewkcoffea@063e8d7` — 10 common + 2 R2-only weight bases
= **12 → 24 labels** (`wwz4l.py:439-449`), 3 shift bases → **6 labels** (`:454-459`), the
impact-partitioning comment verbatim at `:396` ("These weights can go outside of the outside sys
loop since they do not depend on pt of mu or jets"), `copy.deepcopy(weights_obj_base)` at `:470`, the
nominal-only exclusion at `:1204-1207`; totals 1+24+6 = 31 (R2) / 1+20+6 = 27 (R3).
`ewkcoffea-coffea2023@63abb06` — `masked_val_cache`/`masked_weights_cache` at `:808-809` (**0**
occurrences on `main`), `copy.copy(weights_obj_base) # TODO do we need copy here?` at `:342`,
`obj_correction_systs = [] # Will have e.g. jes etc` at `:331`, `hout = {}` at `:807` inside the shift
loop with `return hout` at `:892`, and `# Does not work` above the commented `cloudpickle.dump` at
`run_wwz4l.py:259-261`. `wwz4l@cc71718` — `ApplyJetSystematics` is **byte-identical** to ewkcoffea's
(`modules/corrections.py:581-594` vs `:579-592`, verified by extraction + string compare), the same
12/10-base weight lists, and **zero** dask surface in `analysis/*.py`; my own line-similarity measure
gives 509 matching non-blank lines / 512 shared distinct stripped lines against the plan's "522
identical processor lines" — corroborating, the small delta being a methodology difference.
WRemnants and narf: **0** `Vary` uses (grep). mkShapesRDF: 25 `Vary` uses plus its own
`mRDF.Vary` at `processor/framework/mRDF.py:185` under a class docstring that says it exists to
"use Vary together with Snapshot" — exactly the reimplementation the plan cites.

**Root prompt / catalog:** `graphed-root-prompt.md:1284` is the Out-of-scope header, `:1285` is blank,
the "treating systematic variations as a graph axis" sentence wraps `:1286-1287`, and R22.0/R22.10
carry the inline Phase-2 mentions at `:1262`/`:1282` — all as the plan (and §12.3(b)) states.

---

## Verdict

**CLEAN for this lens** (3 findings: 0 BLOCKER, 0 HIGH, 0 MID, 2 LOW, 1 NIT). No anchor I opened
pointed at absent or contradicting content; no measured claim I re-ran failed to reproduce; the
arithmetic, counts and prior-art claims check out. The two LOW findings are a wrong supporting
sentence about pre-existing `aggregate_plan` coverage and one non-reproducible digest literal;
neither changes a requirement, an anchor's content, or a milestone's scope. This lens does not block
r21.
