# Systematics-vary plan — review round 6, FACTS / HALLUCINATION lens

- **Plan revision reviewed:** r14 (`systematics-vary-plan.md`, 2837 lines, read in full — Part I, every PART II section, §10 milestones, §11, §12, the Anchors appendix, and the full revision history).
- **Lens:** facts / hallucination audit. Every `file:line` anchor in the body and the appendix opened at the cited lines; measured claims re-run where cheap and checked for internal consistency where not; citations into the two research docs read at the cited sections; prior-art claims checked against the prior-art clones; arithmetic and counts recomputed.
- **Date:** 2026-07-30.
- **Verification roots used (all at the pinned revisions):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (its committed `python/graphed/core/graphed_core.cpython-312-darwin.so` + `.venv` were used to re-run the graph probes)
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42`
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef` (branch `graphed-mvp`)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf`
  - `/Users/lgray/vibe-coding/graphed-workdir/{systematics-vary-codebase-analysis,systematics-vary-litsearch,systematics-vary-worklog,graphed-root-prompt}.md`
- **Owner-locked decisions were not relitigated.** Nothing below asks for a different choice; every finding is an internal-consistency or evidence defect.

---

## Findings

### 1. HIGH — §2.3d / m48 anchor: the bound discovery rule provably does **not** discover `compile_ir`, one of the two "compile/aggregate" verbs the same section bindingly disposes

**Section:** §2.3d (plan `:523-541`) and the m48 refusal-table anchor (`:1836-1856`).

**Detail.** r14 withdrew the r13 `Array`-FIRST-parameter filter because it "provably MISSES four of the verbs disposed above: `compile_ir(session: Session, *outputs: Any)`, `evaluate_ir(...)`, `read_columns(arrays: Sequence[Array], source_nid: int)` and `apply(fn: ..., *arrays: Array)` — i.e. exactly the safety-bearing dispositions", and replaced it with: enumerate `graphed.__all__`, keep "callables **any of whose parameter annotations MENTIONS `Array`**", **plus the named non-`graphed.__all__` members** (`graphed.awkward.to_parquet`, `graphed_histogram.Histogram.fill`), and assert every discovered verb carries a disposition.

Measured against `graphed-latest@ff7c607` (`inspect.signature` over `graphed.__all__`, run in the repo's own `.venv`):

```
ANNOTATION-WIDE: ['aggregate_plan', 'apply', 'join', 'join_plan', 'pack_key',
                  'read_columns', 'repartition', 'shuffle_plan']
FIRST-PARAM:     ['aggregate_plan', 'join', 'join_plan', 'pack_key',
                  'read_columns', 'repartition', 'shuffle_plan']
compile_ir (session: 'Session', *outputs: 'Any', optimize: 'bool' = True,
            maximal_fusion: 'bool' = False) -> 'CompiledGraph'
```

`compile_ir`'s outputs are annotated `Any`, not `Array` (`python/graphed/execute.py:54-58`), so **no parameter annotation mentions `Array`** and the annotation-wide filter misses it — the repair fixes `read_columns` and `apply` (both discovered) but not `compile_ir`. `compile_ir` is in `graphed.__all__` (`python/graphed/__init__.py:12,44`), so the "named non-`__all__` members" escape hatch does not reach it either; it falls through both channels. Yet §2.3d bindingly disposes it (**refuse** a `Varied` output with an error naming `graphed.universe`), and m48 freezes that contract explicitly ("The **compile/aggregate verbs** (`compile_ir`, `aggregate_plan`) raise a `graphed` error naming `graphed.universe`").

Consequence: the m48 gate as bound cannot assert a disposition for `compile_ir`, and its "at least the freeze-time count" non-vacuity floor bakes the absence in — the anti-drift property the rule exists for does not cover the verb whose undisposed failure mode §2.3d itself calls out (`Varied`'s field-access `getattr` turning a duck-typed read into a recorded `field` op). Nothing goes red; the gate is silently weaker than the prose claims.

Secondary, same paragraph: the parenthetical "`aggregate_plan(*outputs: Array)` … is var-positional and **ambiguous** under it [the first-parameter filter]" is implementation-dependent, not inherent — a plain `inspect.signature`-based first-parameter check **does** discover `aggregate_plan` (see FIRST-PARAM above). Not load-bearing, but stated as measured.

**Evidence.** Command run in-session: `.venv/bin/python` enumerating `graphed.__all__` with `inspect.signature`, output quoted above; `python/graphed/execute.py:54-58` (signature), `python/graphed/__init__.py:12` (import) and `:44` (`__all__` entry); §2.3d text at plan `:523-541`.

**Suggested fix.** Add `graphed.compile_ir` to the explicitly named members of the enumeration (the same channel `graphed.awkward.to_parquet` / `Histogram.fill` already use, with the named list no longer scoped to non-`__all__` members), or widen the filter to "any parameter annotation mentioning `Array`, **or** a var-positional parameter on a verb that reads `arr.node_id`". The first is one clause and matches the existing escape hatch. While editing, drop or soften the `aggregate_plan` "ambiguous" parenthetical.

---

### 2. LOW — stale line number: `session.walk`'s `root = array.node_id` is at `session.py:268`, not `:269` (cited twice)

**Section:** §4.3 (plan `:836-838`) and the Anchors appendix row for `Histogram.fill_nodes()` / `session.walk` (`:2418`).

**Detail.** Both places read "`session.walk` takes an `Array`, not a node id (`session.py:245-252`, `root = array.node_id` at `:269`)". Measured: `grep -n "root = array.node_id" python/graphed/session.py` → **`268`**; `:269` is `stack = [root]`. The `:245-252` half is exact (`def walk(` … `) -> object:`). Claim unaffected; only the pointer drifts.

**Suggested fix.** `:269` → `:268` in both places.

---

### 3. LOW — §6.1d carries the pre-r13 `graphed-histogram` dependency line numbers, contradicting the appendix row r13 corrected

**Section:** §6.1d (plan `:1039-1041`) vs the Anchors appendix row (`:2407`).

**Detail.** §6.1d cites "(`graphed-histogram pyproject.toml:20-21,24-38`)" for "runtime dependencies … with awkward only in the dev extra". The appendix row says "`graphed-histogram pyproject.toml:21` (runtime) vs `:25-39` (dev) — re-counted r13", and the r13 revision history records the correction "`graphed-histogram pyproject.toml:24-38`→`:25-39`". Measured: `dependencies = ["graphed", "boost-histogram>=1.4", "numpy>=1.24"]` is line **21** alone (`:19-20` are comments); the `dev` extra is `dev = [` at **25** through `]` at **39**. The r13 correction was applied to the appendix only; the body kept the old span.

**Suggested fix.** `:20-21,24-38` → `:21,25-39` in §6.1d.

---

### 4. LOW — §8.2(i)'s "`read_columns` returns its read set SORTED" points at the docstring, not the sort

**Section:** §8.2(i) (plan `:1520-1522`).

**Detail.** "the house discipline is already the opposite: `read_columns` returns its read set SORTED precisely so a set never reaches a plan, `projection.py:109-121`". Measured: `:109` is `def read_columns(arrays: Sequence[Array], source_nid: int)`, `:110-121` is its docstring; the sorted return is `return tuple(sorted(needed))` at **`:147`** (and the function runs `:109-147`, which §5.3 cites correctly). The claim is true; the cited span contains no sorting.

**Suggested fix.** `projection.py:109-121` → `projection.py:147` (or `:109-147`).

---

### 5. NIT — a cluster of ±1/±2 span drifts where the cited range brackets rather than contains the quoted content

**Sections / measured values (all claims true; only the spans are loose):**

- `python/graphed/numpy/__init__.py:578-598` cited in §4.1 for the donor-free constructors being "all in `__all__`" — the `__all__` block starts at `:578` but runs past `:598`: `zeros` is at `:599`, `zeros_like` at `:600`.
- `histograms.py:39-42` (m48 corpus-rounding anchor, plan `:1774`) for `fingerprint` — measured `def fingerprint` at `:40`, body `:42-43`; `:39` is blank and the hashing line `:43` is outside the span. (`bin_values` cited `:34-37` is likewise `def` at `:35`.)
- `tests/frozen/corpus/m05/test_systematics.py:26-38` (appendix, plan `:2338`) for the two behavioural invariants — measured `test_kinematic_variation_changes_selection` at `:25-30` and `test_weight_variation_preserves_selection` at `:33-37`.
- `execute.py:110-117` (§8.2(i), plan `:1543`) for "stage members are evaluated inline" — the stage branch is `:110-115`; `:116-117` is the `external` branch. The plan uses the correct `:110-115` in §8.2(iii) and in the appendix.
- `session.py:141-166` (§8.2(ii), plan `:1559`) for where `Session._provenance` is written — measured writes at `:138` (`source`), `:166`, `:181`, `:202`, `:240`; the span misses the `source` write, which is one of the five sites §2.3e itself enumerates.

**Suggested fix.** Mechanical span corrections; none changes a requirement.

---

### 6. NIT — Part I §2's "~4 years" for the coffea `add_systematic` stall matches neither number in the cited section

**Section:** Part I §2 (plan `:98`) citing lit §coffea-sys.

**Detail.** The plan says the in-IR prototype "stalled for ~4 years". `systematics-vary-litsearch.md:214` (§coffea-sys §2, Timeline) records "created 2021-05-13 … docstrings 2022-03-07, then dormant; dask-mode support only merged **2025-07-12** … a **~3-year stall**", while the same document's assessment (`:249`) says "coffea left `explodes_how` unimplemented for **5 years**". The plan's figure sits between the two and is defensible from the raw dates (2021-05 → 2025-07 ≈ 4.2 y), but it reproduces neither statement of the cited source. Part I binds nothing.

**Suggested fix.** Either cite the elapsed dates directly ("2021-05 → 2025-07") or use the source's own "~3-year stall".

---

### 7. NIT — the "522 identical processor lines" figure is method-dependent and the cited document carries two different values

**Section:** Part I §2 (plan `:127`) and the appendix teaching-strip row (`:2374`).

**Detail.** The plan states "522 identical processor lines" for `FNALLPC/wwz4l@cc71718` vs `ewkcoffea@main`. `systematics-vary-litsearch.md` gives **522** in its comparison table but **503** in the lead's independent re-verification note four lines earlier ("set-based line overlap 503 vs main / 308 vs coffea2023"). My own in-session count over the same two files (`difflib.SequenceMatcher` on rstripped lines, order-preserving matching blocks) gave **658**. All three are "identical lines" under different definitions; no counting method is stated anywhere. Everything else in that sentence reproduces exactly (see the clean list below).

**Suggested fix.** Name the method with the number ("522 identical lines by set intersection of stripped lines"), or drop the figure and keep the qualitative claim, which is independently verified.

---

## What I re-ran and reproduced (no findings — recorded so the verdict has weight)

Every item below was re-measured in this session and matched the plan **exactly** unless noted.

**Graph / IR probes (against `graphed-latest@ff7c607`, its built extension):**
- §3.3 / §5.2a topology: with a terminating reduction, N=16 → `stages 17 / reduced 34`, N=128 → `stages 129 / reduced 258`; **without** it, N=16 → 18, N=128 → 130; arena Δ(N=1→2) = **52** with the reduction, **51** without. All four numbers, including the "load-bearing terminating reduction" claim, reproduce exactly (D=500, K=50).
- Interning: `src * 2.0` recorded twice returns node id **1** both times (source id 0, `node_count` 2) — the §2.3e claim verbatim.
- §7.2 dedup: `compile_ir(s, b, c)` with structurally identical `b`/`c` → **1** value; `compile_ir(s, b, d)` → **2**.
- §2.6 note (i): `w[:, 1]` → `TypeError: unsupported index (slice(None, None, None), 1)`; `gak.firsts(w[gak.local_index(w) == 1])` over `[[1,2,3],[4,5,6]]` materializes the second element of each row.

**boost_histogram (1.8.0):** under-declared `StrCategory` → `sum 2.0` vs `sum(flow=True) 3.0` with `Traits(underflow=False, overflow=True, growth=False, …)`; over-declaration → `sum == sum(flow=True) == 3.0` (invisible to the flow check); `StrCategory(name=…)` → `TypeError`; `h[{"variation": label}]` → `TypeError: list indices must be integers or slices, not str` with and without `bh.loc`; `h[{1: ax.index('jes_up')}]` equals `h[{1: bh.loc('jes_up')}]`; per-axis `[a.__dict__.get("name") …]` → `[None, 'variation']` and `h.axes.name` → `AttributeError: object Regular has no attribute name`; cross-axis addition → `ValueError: axes have different length`. The `spec_of`→`zero_of` round-trip of the axis name (`graphed-histogram` `_spec.py`) also reproduces `[None, 'variation']`.

**awkward 2.12.0 / pyarrow:** `ak.broadcast_arrays` length 7 vs 3 → `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`, jagged 3-row value broadcasts fine; `float32 ^ float32` → `TypeError: ufunc 'bitwise_xor' not supported …` for **both** `np.ndarray` and `ak.Array`, while `a.view(np.uint32) ^ b.view(np.uint32)` works; `ak.from_parquet(columns=["murf_0.5"])` returns an EMPTY array (fields `[]`, len 0); `"metadata" in signature(ak.to_parquet)` → `False`; `ak.to_parquet` vs `pq.write_table(ak.to_arrow_table(...))` → different bytes for record / list-of-float / flat numeric, with file KV `{ARROW:schema, ak:parameters, awkward_array_metadata}` vs `{ARROW:schema, ak:parameters}` for a record and `{ARROW:schema, awkward_array_metadata}` vs `{ARROW:schema}` for the other two — i.e. `ARROW:schema` always present and `ak:parameters` array-dependent, exactly as §6.4e states; repeat writes in one process are byte-identical; the footer `created_by` is `parquet-cpp-arrow version <arrow version>`. A clean `uv` resolve of `awkward>=2.12` + `pyarrow` gives **25.0.1** (§6.4e's r14 correction confirmed; adding an explicit `numpy` pin drags it to 24.0.0, which is presumably where the r11/r13 attribution wobble came from — the KV/byte findings are identical either way).

**cloudpickle determinism (§8.2(i)):** cloudpickle **3.1.2**, payload `(3, frozenset({"btag_down","btag_up","jes_down","jes_up","nominal"}))`, `PYTHONHASHSEED` 1 / 7 / 12345 → sha256[:16] **`b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831`** — all three digests reproduce bit-for-bit. The r14 "payload + toolchain named so the probe is reproducible" repair works as advertised.

**Code anchors — spot-verified exact** (a non-exhaustive list of the load-bearing ones): `src/store.rs:73-88` (intern), `:147-156`/`:152-153` (`mark_output` dedup); `src/node.rs:39-41`, `:102-103`, and the whole enum `:41-85` with variant heads at 42/46/51/56/64/72/81 (the r11 completeness correction is right); `src/optimizer/engine.rs:7-13,54-56`; `src/optimizer/mod.rs:1-11,88-116` (`remap` computed at `:101`, never returned — the return is `(kept, out_idx)`); `src/lib.rs` has exactly **three** `#[pymethods]` blocks at `:102`, `:159`(–`:416`), `:470`, and the `GraphStore` block is exactly the 15 methods listed (+`new`) with no id mapping; `array.py:54,127-128,137-143,156,245-275,332-335,344-371,374-391,397-410`; `session.py:30,39,50-51,113-125,133-140,142-168,170-183,185-204,206-242,245-252`, and `_array_cls` has **no** call site outside `session.py`; `execute.py:36-45,54-55,70,85-91,99-126`; `aggregate.py:44-65,57-63,68,86,89-93,95-97,101`; `plan.py:72-77,164-176,286-301`; `shuffle.py:68,84,89,92-96,142,155,170,208,220,232`; `debug/errors.py:29,75-78,80-81` (the `__hash__` tuple genuinely excludes any new field); `debug/runner.py:6-7,37,57-69`; exactly **two** `StageError(` hits under `python/graphed/`; `provenance.py:26-33,66-79`; `projection.py:109-147`; `preserve/bundle.py:103-123,206-210`; `checkpoint/store.py:31-41,62-73`, `checkpoint/runner.py:100-109`; `write.py:32-43,77-79`; `awkward/io.py:111-127` (`(out,) = evaluate_ir` at `:121`), `:157-185`, `:206-216`, `:239,260,274`; `awkward/__init__.py:14,17-31`; `numpy/array.py:71-74` and exactly **25** methods in `:92-190`; `numpy/creation.py:27-28,31-75`; `numpy/io.py:163-171`; gak: **73** `def`s / **65** public / **zero** `__all__` / no `view`/`packbits`/`frombuffer`, and every cited function line (`join:18`, `zip:118`, `linear_fit:346`, `concatenate:383`, `where:400`, `apply_correction:476`, `onnx_inference:513`, `unflatten:600`, `full_like:612`, `values_astype:673`, `broadcast_arrays:677`, `unzip:687`, `to_list:693`, `fields:717`, `type_of:722`, `backend_of:727`, `head:732`, `sample:737`) is exact; the only `broadcast` string in `graphed/numpy/*.py` is the docstring at `__init__.py:8`.

**Fixture / CI facts:** `graphed` vendors `tests/_corpus/{graphed_corpus,references}` (**23** JSONs) on `pythonpath` `:114-127`, has **no** `graphed-corpus` in any extra, `dev` at `:42-48` carries `boost-histogram`/`hist` only, CI installs `.[dev]` at `:34,57,143`; `run-tests.sh` `SUITES` `:16-25`, `SPLIT_PKGS` `:30`; **zero** `__init__.py` under `tests/frozen`; `tests/frozen/checkpoint` holds only `m8`/`m39` with `m8/test_resume.py` present; `preserve/m9` holds both `test_reproduce.py` and `test_inspect.py`; the `importorskip` house pattern at `preserve/m25/…:31`, `m27/…:185,207`, `m30/…:155`; the only multiprocessing frozen test is `debug/m6/test_process_boundary.py:7,16`. `graphed-histogram`: runtime deps `:21`, `pythonpath` `:50`, `pytest tests/frozen` in ONE process at `ci.yml:44,67`, env carries `GRAPHED`+`EXECLOCAL` only (`:13-17`), zero `corpus` hits under `tests/` or the workflows, existing `tests/frozen/{m23,m29}`, version `0.0.1`, and **PyPI `graphed-histogram` resolves to `0.0.1`** with the graphed-org homepage (r14's git-URL argument holds). `graphed-executors`: no `histogram` hit anywhere, `pythonpath` `:54`, env `GRAPHED`+`CORPUS` at `ci.yml:13,15,17` installed at `:38,65,94,136`, frozen runs at `:44,67,101,153`, **15** milestone dirs, zero `__init__.py`. `uproot5-graphed@393ecef`: **no** frozen tree, **12** flat `tests/test_graphed_*.py` + 2 helper modules, zero `tests/frozen` references, and no `key_value_metadata`/`with_metadata` anywhere under `src/`. `graphed-corpus`: wheel packages only `src/graphed_corpus` (`:28-30`), **23** reference JSONs of which **15** are systematics (10 ttbar + 5 ttgamma — the "9 of the 15" split is arithmetically right), `ops_catalog.md:75` is verbatim the Phase-2 row the plan un-parks.

**Corpus / m4 / m9 anchors:** the vendored `tests/_corpus/graphed_corpus` is byte-identical to `graphed-corpus@49650e4`, so all shared line numbers carry: `systematics.py:25-36` (`_btag_weight`), `:39-45` (`ak.with_field` JES), `:60-61` (JES before the pt cut), `:74-76` (`sel_jets = good[sel]` → `ht` → central b-tag SF on shifted jets, with `:73` blank as r12 recorded), `:79`/`:102` (pre-fill 6-decimal rounding), `:91-92` (the `sel` built from JES-varied `good_jets`, then `photons[sel]` — the §2.3b "unvaried photons sliced by a varied selection" case, correctly anchored). `core/m4/test_systematics.py:28-53` and its single-output `_systematics` builder (the vacuity trap the plan flags) both check out; `core/m4/test_benchmark.py:10,28-33,40-53` matches, including `base = max(times[SIZES[0]], 1e-4)` and the `24.0` threshold. `preserve/m9/agc.py:38-66` (correctionlib set with a **string**-typed `systematic` category, `:56`/`:62`), `:94-118` (variation as build-time config), `:106-107` (shift before the mask); `test_reproduce.py:19-23`; `core/m40/test_join_serialize.py:83-99` (the literal `b"GIR1\x03…"` golden); `awkward/m24/test_interface_parity.py:39-79` is a literal tuple of exactly **39** names with `full_like` at `:75`.

**Histogram internals:** `boost.py:39-47` (`_flat`), `:60-71` (independent flatten + `weight = weight * _flat(rest.pop(0))`), `:88-98` (`_SumFills`), `:100-122` (`_GroupReduce` + `_add_groups`, count-based `for j in range(i, i + k)`), `:127-130` (`_GroupZero`), `:146-150` (`self._spec` fixed in `__init__`), `:153-163` (positional `fill`, one array per axis at `:160-161`), `:180-212` (spec into `chash`/params/evaluator), `:215-219` (`staged_fills`/`fill_nodes()` — public and **unlabeled**), `:245-255` (`plan` passing the `__init__`-time spec), `:282` (`layout` built from `len(h._fill_nodes)`, keyed on the OUTPUT name); `_spec.py:31-37,70,74,81-84,115-122,129-135`.

**Research-doc citations:** `cba §corpus §1,§3,§4,§5`, `§optimizer §2,§5`, `§histogram §1,§2,§3`, `§exec-checkpoint §1,§4`, `§ir-rust §1` all exist and say what the plan says they say — including cba §optimizer §2's table (N=1 → 553 arena nodes, N=16 → 3.1 ms / 34 reduced / 17 stages, N=128 → 16.7 ms / 258 / 129), which my independent re-measurement reproduces node-for-node, and whose "12.9× nodes → 11.9× time" and the plan's derived "≈5.4 against the 24.0 gate" both recompute correctly. cba §histogram §1's constant-Array grep really is scoped to the session/array modules, exactly as §4.1 says. `lit §rdf-vary §1-§6`, `§rdf-users §1-§5`, `§coffea-sys §1-§5`, `§pythonic-analyses`, `§ewkcoffea-confirmed` + addendum all support the Part I digest; the #469 caveat is verbatim at `systematics-vary-litsearch.md:236` as cited.

**Prior art:** `ewkcoffea@063e8d7 wwz4l.py:1204-1207` (nominal-only exclusion) and `:396-397` (impact-partitioned Weights comment) are exact; the weight list is **12** bases for R2 (10 common + 2 R2-only) → **24** labels and the object list **3** bases → **6** labels → a **7**-pass loop, all as claimed; `copy.deepcopy(weights_obj_base)` per shift confirmed; `sow_renorm*` present in **both** eras. `ewkcoffea@63abb06 wwz4l.py:808-865` (the hand-written `masked_val_cache`/`masked_weights_cache` CSE), `:342` (`copy.copy(...)  # TODO do we need copy here?`), `:331` (`obj_correction_systs = []` — empty), and `hout = {}` at `:807` genuinely sits **inside** the shift loop opened at `:339` with `return hout` at `:892`, so the latent last-shift-wins bug is real; `run_wwz4l.py:259-261` is the "# Does not work" cloudpickle block and `:302-313` the timing prints. `FNALLPC/wwz4l@cc71718`: zero dask/`dataset_tools`/`hist.dask` hits repo-wide, `ApplyJetSystematics` identical to `ewkcoffea@main`'s, `analysis_processor.py:395-400` (shift list) and `:711-718` (exclusion rule) exact, 764-line processor. coffea @ `f34b8bdf`: `CorrectedJetsFactory.py:36-47` (`rand_gauss` seeding PCG64 from the input array's own bytes) and `:64-95` (`jer_smear` taking ONE `jet_resolution_rand_gauss` while only `jersf = …[:, variation]` varies; signed `deltaPtRel`; hybrid `detSmear`/`stochSmear`) are exact — §5.5's two binding rules and the non-monotonicity argument are properly grounded.

**Root prompt:** `:25` is the "tens of thousands" sentence verbatim; R22.0 at `:1262` and R22.10 at `:1282` both carry the "systematics-as-a-graph-axis stays Phase 2" mention; the Out-of-scope header is at `:1284` and "treating systematic variations as a graph axis" begins at `:1286`; R0.4a/R0.5/R0.10/R0.10a/R0.11/R22.3 all exist, and R22.3 is indeed the cross-process differing-`PYTHONHASHSEED` form §3.2 invokes.

**Arithmetic / counts:** 9 of 15 refs (6+3); 15 systematics references (10 ttbar + 5 ttgamma out of 23); the §2.6 sketch really does register **104** non-nominal ambient weight labels before the derivation (2 pileup + 102 PDF members from `range(1, 103)`); `K + 2 = 52`; `stages == N+1`, `reduced == 2N+2`, and `N+2` without the reduction; the e-form renderings (`0.5`→`5em1`, `2.5`→`25em1`, `1.2345`→`12345em4`, `-1.5`→`m15em1`, `1e-8`→`1em8`, `"1e40"` → 41 plain digits, `"1e-40"` → the 5-character `1em40`) are all internally consistent with the stated grammar and the 32-character cap; the §6.4c compression figures (raw 3.551 MB, ratio 2.883, XOR 3.280; masks 798 KB → 169 KB ≈ 4.7×) match `systematics-vary-worklog.md:183-188` including the stated methodology (float32, 1M elements, zlib-6, seed 42, 5 masks flipping ~3%).

---

## Verdict

**Dirty, but only just — one HIGH and no BLOCKER.** This is the cleanest factual substrate I have audited on this plan: of roughly 200 distinct anchors and measured claims checked, every substantive one reproduced, several to the digit (the arena/stage/reduced integers, the three cloudpickle digests, the bh and awkward error strings, the ewkcoffea label counts). The single HIGH is a real defect in r14's own headline repair — the annotation-wide discovery rule still misses `compile_ir`, so the m48 exhaustiveness gate cannot cover one of the two verbs §2.3d bindingly disposes — and it is fixable with one clause (add `compile_ir` to the named-members list). The remaining findings are three cosmetic line-number defects and three notes on soft numbers inherited from the research docs. Nothing here requires reversing an owner-locked decision, and nothing blocks test authoring once finding 1 is closed.
