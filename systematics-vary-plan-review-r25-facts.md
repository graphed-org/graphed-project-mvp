# systematics-vary plan — review r25, lens: FACTS / HALLUCINATION AUDIT

- **Plan reviewed:** `systematics-vary-plan.md` revision **r25** (6036 lines), review round **17**.
- **Lens:** facts / hallucination audit — file:line anchors (body + Anchors appendix), measured claims,
  citations into the two research docs, prior-art claims, arithmetic and counts.
- **Date:** 2026-07-30.
- **Verification roots used** (all confirmed at the cited revisions in-session via `git log --oneline -1`):
  - `/private/tmp/claude-501/graphed-latest` — **ff7c607** (+ its `.venv`: awkward 2.12.0, numpy 2.5.2,
    cloudpickle 3.1.2, CPython 3.12.10)
  - `/private/tmp/claude-501/graphed-histogram-latest` — **211cbbe** (+ its `.venv`: boost_histogram 1.8.0)
  - `/private/tmp/claude-501/graphed-exec-check` (graphed-executors) — **201ea42**
  - `/private/tmp/claude-501/uproot5-graphed` (branch `graphed-mvp`) — **393ecef**
  - `/private/tmp/claude-501/graphed-corpus-latest` — **49650e4**
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718}`
  - `/Users/lgray/vibe-coding/coffea-workdir` — **f34b8bdf**
  - `graphed-root-prompt.md`, `systematics-vary-{codebase-analysis,litsearch,worklog}.md` in the workdir.
- **Method:** every claim below was checked by opening the cited file at the cited lines in the
  verification roots (never the stale workdir submodules) or by re-running the probe in the pinned
  environment. No claim was accepted on the plan's own authority.

---

## Verdict

**CLEAN for this lens.** Three NIT-level imprecisions, no LOW or above.

Across ~90 distinct anchors and ~25 re-run probes I found **no false anchor, no unreproducible
measurement, no mis-cited research-doc section, no prior-art misstatement, and no arithmetic error.**
Every r25-new factual claim reproduces exactly, including the three that carry literal numbers
(the `graphed.numpy.__all__` discovery set, the `CompiledGraph`/core-reduce carrier analysis, and the
corpus nesting basis). The withdrawn-digest discipline (r21/r23 withdrawing `80e8024dc8f3b77d`,
`8d058bf867dc6bcd`/`22a566276fd6077d`, `sha256:cae4dd4b…`) is vindicated by the counter-example the
plan kept: §8.2(i)'s payload-named digest triple reproduces **bit-for-bit** in this session.

---

## Findings

### NIT-1 — §4.1's `graphed.numpy.__all__` span truncates before `zeros`

**Section:** §4.1 (and the appendix row "`graphed.numpy` DOES ship donor-free constants").

**Detail.** §4.1 writes: "`graphed.numpy` ships donor-free `full`/`ones`/`zeros`/`empty`/`arange`/
`linspace` (`python/graphed/numpy/creation.py:31-75`, all in `__all__`,
`python/graphed/numpy/__init__.py:578-598`)". Measured at `graphed-latest@ff7c607`, the `__all__`
block runs **`:578-601`**; `"zeros"` sits at **`:599`** and `"zeros_like"` at `:600`, i.e. one of the
six names the sentence enumerates falls outside the cited span. The substantive claim ("all in
`__all__`") is TRUE — I verified all six are exported — and the `creation.py:31-75` half is right
(`zeros` `:31`, `ones` `:36`, `full` `:41`, `empty` `:48`, `arange` `:57`, `linspace` `:70`).

**Evidence.**
```
$ python3 -c "lines=open('python/graphed/numpy/__init__.py').read().split('\n'); ..."
596     "ones_like",
597     "project",
598     "shuffle",
599     "zeros",
600     "zeros_like",
601 ]
```
Also measured: `graphed.numpy.__all__` has 22 entries (matching §2.3d r25).

**Suggested fix.** Cite `python/graphed/numpy/__init__.py:578-601`.

---

### NIT-2 — Part I §2's "27 labels" for `wwz4l` is one of two era-specific counts, unqualified

**Section:** Part I §2 (`FNALLPC/wwz4l` addendum).

**Detail.** The plan says wwz4l "carries the full weight+shift treatment (**27 labels**)". The
source (lit §ewkcoffea-confirmed, `systematics-vary-litsearch.md:415`) states: "Total
`systematic`-axis labels per MC sample: **31 (R2) / 27 (R3)** = `1 + 24|20 + 6`". 27 is the **R3**
number; R2 is 31. Verified in the clone: `wwz4l/analysis/analysis_processor.py:378-386` carries 10
common weight bases plus 2 more only when `not (is2022 or is2023)` (→ 24 or 20 labels after
`append_up_down_to_sys_base`), and `:395-400` carries 3 object bases → 6 shift labels; `+1` nominal
gives 31/27. The claim is therefore true-but-era-specific, and Part I is non-binding rationale, so
nothing downstream turns on it.

**Suggested fix.** "(27 labels in R3, 31 in R2)" — or "(up to 31 labels)".

---

### NIT-3 — §10's quotation of the uproot fork's test step is truncated

**Section:** §10 (m51 gate analysis, r23).

**Detail.** §10 says the only workflow running the graphed tests has a test step
"`python -m pytest -vv tests -m "not xrootd"` at `:55`". Measured at `393ecef`, line 55 is
`python -m pytest -vv tests -m "not xrootd" -k "not xrootd" \` and the command continues onto
following lines. Every *load-bearing* half of the surrounding claim is exactly right and I
re-verified each: `pyproject.toml:136` `testpaths = ["tests"]`; `grep -c cov graphed.yml` → **0**;
`:26-32` ubuntu-latest + CPython 3.11/3.12 only; `:7-10` `push: branches: [graphed-mvp]` +
`workflow_dispatch`, no `pull_request`; **no `[tool.mypy]` section anywhere** in that pyproject.

**Suggested fix.** Quote the line with an ellipsis (`… -m "not xrootd" -k "not xrootd" …`) or drop
the literal and keep the measured properties.

---

## Verification inventory (what was actually checked, for the record)

### A. Re-run probes — all reproduce exactly

| Probe (plan §) | Plan's number | Re-measured this session |
|---|---|---|
| §3.3 topology, D=500/K=50 | N=16 → stages 17 / reduced 34; N=128 → 129 / 258 | identical; kinds `{source:1, stage:N+1, reduction:N}` |
| §3.3 reachable nodes | 1333 → 7157 (ratio 5.37) | 1333 → 7157 |
| §3.3 / §5.2a no-reduction variant | N=16 → 18, N=128 → 130 | identical |
| §5.2a arena delta N=1→2 | 52 (51 without the reduction) | 52 / 51 |
| §7.2 r21 first-occurrence probe | record ids `0,1,2,3,2`; `outputs()==[1,2]`; 2 values; `s._store.outputs()==[]` | identical |
| §7.2 r17 identity-token merge | `w,w*1.0,w*2.0,w*0.5` → `outputs()==[0,1,2]`, 3 values | identical |
| §7.2 r17 fill-path merge | fill nodes `2`/`4` → `outputs()==[2]` | identical (bh 1.8.0, gh@211cbbe) |
| §1.2 / §5.2a re-record interning | `a=src*2.0; b=src*2.0` → id 1/1, `a is b` False, `node_count()==2` | identical |
| §8.2(i) frozenset seed-dependence | `b7984b3caadf74f7 / 2778da7a97834ac5 / 97429e5989f2a831` | **exact match** (cloudpickle 3.1.2, CPython 3.12.10, seeds 1/7/12345) |
| §8.2(i) m49 cardinality (D=20,K=5) | N=3 → 8 / `{1,4,3}`; N=16 → 34 / `{1,17,16}`; +dead branch unchanged; +shared node → 9 / `{1,5,3}` and 35 / `{1,18,16}` | identical on all six |
| §3.4 r24 impact fixture | `impact(up)=[1,3]`, `impact(dn)=[1,4]`, shared `[1]`, members distinct | identical |
| §2.2 r24 container surface | `dir(Array)` public = 6; `dir(NumpyArray)` = 32; the 26 extra names | identical, name-for-name |
| §2.2/§2.3a r19 property classes | `dtype/ndim/shape` → node delta 0; `T` → delta 1; 2-D `T` raises `GraphedTypeError` | identical; discovered property set `['T','dtype','ndim','node_id','session','shape']` |
| §2.3d r25 numpy verbs | annotation filter over `graphed.numpy.__all__` (22) → `apply_gufunc, empty_like, full_like, ones_like, project, zeros_like` | identical (6/6) |
| §2.3d r15 graphed verbs | 8 discovered: `aggregate_plan, apply, join, join_plan, pack_key, read_columns, repartition, shuffle_plan`; `compile_ir` absent | identical |
| §2.3c gak surface | 65 public / 73 `def`s / 0 `__all__`; alias discovers 0 | identical |
| §2.3e(2) r22 operand kinds | `num/unzip/drop_none/singletons/firsts/where/unflatten` OK; `with_field` → `GraphedTypeError … no tuples or records in array` | identical |
| §2.6 note (i) | `w[:,1]` → `TypeError: unsupported index …`; `gak.firsts(w[gak.local_index(w)==1])` → `[2.0, 5.0]` | identical |
| §6.1b r21 / §6.2 | `sample=` rejected on `Double()` and `Weight()`, accepted on `Mean()`/`WeightedMean()` | identical (bh 1.8.0) |
| §6.1c / §6.2(i) | cross-axis add → `ValueError: axes have different length` | identical |
| §6.2(i-bis) | `StrCategory(name=…)` → `TypeError`; `h[{"variation": …}]` → `TypeError: list indices…`; `h.axes.name` → `AttributeError` on a 2-axis hist; `axis.__dict__["name"]` round-trips `spec_of`→`zero_of` as `[None,'variation']`; positional index == `bh.loc` | identical on all five |
| §6.2(ii) declaration | under-declaration `sum 2.0` vs `flow 3.0`; over-declaration `3.0 == 3.0`; `Traits(overflow=True, growth=False)` | identical |
| §6.1d r19 | 2-axis unequal-length fill → `ValueError: spans must have compatible lengths` | identical |
| §6.1d r12 | `ak.broadcast_arrays` 7 vs 3 → `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`; jagged case OK | identical |
| §6.4c r14 | `float32 ^ float32` → `TypeError`, `.view(np.uint32) ^` works | identical (numpy + awkward) |
| §6.4a r24 form discriminator | `var * {pt, eta}` vs `{Jet: var * {…}, Muon: var * {…}}` | identical |
| §6.3 params key set | `{"spec","n_axes","weighted","sampled"}` | identical |
| §7.3 / §7.2 | `OpSpec.from_callable(_PartitionReduce(...)).kind == "opaque"`; `grep "DurablePlan(" python/` → 0; `OpSpec.from_callable` only at `shuffle.py:181,188,245,259` | identical |
| §10/m49(ii) | `graphed-histogram` on PyPI = `0.0.1`; repo version `0.0.1` | identical (re-fetched) |
| §6.4c worklog numbers | raw 3.55 MB / ratio 2.88 / XOR 3.28; masks 798 KB → 169 KB (~4.7×) | matches `systematics-vary-worklog.md:183,187` |

### B. Anchors opened and confirmed (selection)

- **Rust core:** `store.rs:73-88` (intern), `:147-156` (`mark_output` dedup, `:152-153`),
  `:185-200` (`from_reduced`, `mark_output(map[o])` at `:197`); `node.rs:39-41`, `:41-85` with variant
  heads at `:42/:46/:51/:56/:64/:72/:81`, `:102-103` (`!Op`), `:130-138`;
  `optimizer/mod.rs:88-116` (remap never returned); `optimizer/engine.rs:7-13` (O(N) extractor note,
  verbatim), `:22-31` (`SYMMETRIC_OPS`/`IDENTITY_TOKENS`), `:54-56`, `:67-80`, `:89-110`;
  `lib.rs` `#[pymethods]` blocks at `:102/:159/:470`, GraphStore impl closing `:416`, method list
  exactly as enumerated, `reduce`/`reduce_incremental`/`reduction_report` at `:365-415` returning
  `(store, report)` with no id table.
- **graphed frontend:** `execute.py:36-52` (`CompiledGraph` = `ir`/`source_names` + `evaluate`; no
  `outputs`), `:54-80`, `:70`, `:85-91`, `:99-126` (`:104-105`, `:109`, `:110-115`, `:116-124`, `:126`);
  `aggregate.py:44-55` (fields exactly as the appendix lists), `:57-65`, `:68-77`, `:86`, `:89-93`,
  `:95`, `:96-104`, `:101`; `projection.py:109-147` (`:123`, `:130`, `:140`, `:143-146`, `:147`);
  `session.py:36-39`, `:50-51`, `:113-125`, `:133-140`, `:142-168`, `:245-255`, `:268`, `:291-301`,
  and the five `_provenance.setdefault` / `_array_cls` sites at `138/166/181/202/240` and
  `140/168/183/204/242`; `array.py:54`, `:127-128`, `:133-135`, `:137-143`, `:156`, `:245-275`,
  `:283-290`, `:332-335`, `:344-371`, `:374-391`, `:397-410`; `numpy/array.py:71-74`, `:76-86`,
  `:132-136`, `:154-161`; `numpy/creation.py:27-28`, `:31-74`, `:77-91`; `numpy/gufunc.py:74-90`;
  `numpy/projection.py:40`; `numpy/io.py:163-171`, `:182-191`; `awkward/io.py:111-127` (`:121`),
  `:157-185`, `:206-216`, `:230-231`, `:239/:260/:274`; `awkward/functions.py:18/118-119/346/383/400/
  476/505-509/513/600/612-616/673/677-685/687/693/717/722/727/732/737`;
  `awkward/__init__.py:14,17-31,30`; `shuffle.py:68/84/89/92-96/142/155/170/181/188/208/220/232/245/259`;
  `core/execution.py:206-217`, `:219-224`, `:335-351`, `:378-384`, `:450-457`;
  `core/plan.py:54/72-76/126/164-176`; `debug/errors.py:29/75-78/80-81`; `debug/runner.py:6-7/37/57-69`;
  `provenance.py:26-33/66-79`; `preserve/bundle.py:103-123/206-210/268-288`;
  `checkpoint/runner.py:77-91/100-109`; `checkpoint/store.py:31-41/62-73`; `write.py:32-43/77-79`;
  `parquet.py:77` (and 0 hits for `key_value_metadata`/`with_metadata` across `graphed-latest/python`
  and `uproot5-graphed/src`); `errors.py` (`GraphedError(Exception)`, unrelated to `NotImplementedError`);
  `__init__.py:8-25`, `__all__ :27-58` (`:44` `"apply"`, `:46` `"compile_ir"`, `:50-57`).
- **graphed-histogram:** `boost.py:39-47/60-71/88-98/100-122/106-117/108/120-122/127-130/146-150/148/
  152-158/160-161/160-178/175-178/180-212/198-212/215-219/244-253/256-295/262/281/282/283-286`;
  `_spec.py:20-28 (_STORAGES incl. Mean/WeightedMean)/31-37/70/74/81-84/115-122/129-135`;
  frozen `m29/test_multi_weight_fills.py:75-79/84-87/96` and `m23/test_group_plan.py:60-66/68-77/74-75/
  86/89/99`; `pyproject.toml:21/25-39/50/70-73`; `ci.yml:13-17/44/67`; 0 `__init__.py` under `tests`;
  0 corpus hits.
- **graphed / frozen fixtures:** `core/m4/test_benchmark.py:10/28-33/40-53` (threshold 24.0, 8× sizes),
  `core/m4/test_systematics.py:28-53`, `core/m40/test_join_serialize.py:83-99` (literal `b"GIR1\x03…"`),
  `frontend/m5/test_aggregate_plan.py:77/88/102` (call shape verbatim),
  `frontend/m39/test_shuffle_plan_builder.py:58-64`, `debug/m6/test_process_boundary.py:7/16`,
  `checkpoint/m8/test_resume.py:51-58` + `analyses.py:29-30/114-123`,
  `awkward/m24/test_interface_parity.py:39-79` (**39** names, counted) and `:74-76`,
  `preserve/m9/agc.py:38-66/56-62/94-118/106-107/113-115`, `preserve/m9/test_reproduce.py:19-23`,
  `preserve/m25/…:31`, `m27/…:185,207`, `m30/…:155` (`importorskip` house pattern),
  `corpus/m05/test_systematics.py:25/33`; `pyproject.toml:27/29-48/42-48/83/84/103-127`;
  `scripts/run-tests.sh:16-25/30`; `docs/checkpoint/design.rst:20/58-65`; 0 `__init__.py` under
  `tests/frozen`; 23 vendored reference JSONs.
- **graphed-executors:** `submit/engine.py:381-396`; `tests/frozen/m7/analyses.py:118-127`,
  `m7/adl.py:124-158/156-158`; `pyproject.toml:20-35/54`; `ci.yml:13/15/17/38/44/65/67/94/101/136/153`
  (env carries `GRAPHED`+`CORPUS` only); 15 milestone dirs; 0 `__init__.py`; 0 `task_id`/`DurablePlan`
  in `src`.
- **uproot fork @393ecef:** 12 flat `tests/test_graphed_*.py` + 2 helper modules; no frozen tree; 0
  `tests/frozen` references; `writing/_graphed_write.py:59-64` (0 `compile_ir`/`evaluate_ir` hits);
  `writing/_cascadetree.py:1606`; `behaviors/RNTuple.py:562/567/1560-1562/1564-1569`;
  `behaviors/TBranch.py:2015-2017/2019-2024`; `pyproject.toml:136`; `graphed.yml:7-10/26-32/55`.
- **graphed-corpus @49650e4:** `analyses/systematics.py:25-36/39-45/50/60-61/74-76/79/91-92/102`,
  `histograms.py:20/35-37/40-43`; `pyproject.toml:28-29`; 23 references of which **15** are the
  systematics set (10 ttbar + 5 ttgamma) — the "9 of the 15" split (6 ttbar × {nominal,btag±} +
  3 ttgamma) is exactly right; frozen `m05/test_systematics.py:26/34` with the quoted assertion bodies.
- **coffea @f34b8bdf:** `jetmet_tools/CorrectedJetsFactory.py:36-47` (PCG64 seeded from the input
  array's own bytes) and `:64-95` (one `jet_resolution_rand_gauss`, `jersf = …[:, variation]`, signed
  `deltaPtRel`, hybrid `detSmear`/`stochSmear`) — the §5.5(a)/(b) claims hold verbatim.
- **Prior art:** `ewkcoffea@063e8d7 wwz4l.py:1204-1207` (exclusion rule) and `:396-397` (the
  "these weights can go outside of the outside sys loop" comment, quoted verbatim in Part I §2);
  weight bases 10+2 → **24** labels, obj bases 3 → **6** labels, **7**-pass loop, `skip_obj_systematics`
  present; `coffea2023@63abb06 wwz4l.py:807-809/863-865` (`hout={}` inside the loop; hand-written
  `masked_val_cache`/`masked_weights_cache`), `:331` empty `obj_correction_systs`,
  `run_wwz4l.py:259-261` ("# Does not work" over the commented `cloudpickle.dump`), `:302-313`
  (build-vs-compute timing); `wwz4l@cc71718`: **0** dask/`dataset_tools`/`hist.dask` hits,
  `ApplyJetSystematics` **byte-identical** to ewkcoffea's, and the **522** identical processor lines
  reproduce exactly as the non-blank-line multiset intersection (`Counter(a) & Counter(b)` → 522).
- **Root prompt / catalog:** `graphed-root-prompt.md:25` (the quoted founding-rationale sentence),
  `:147-153` (R0.4a, incl. the "repos still configured `src`-only are a known cross-cutting cleanup"
  half the r23 correction leans on), `:1262`, `:1282`, `:1284` header, `:1285` blank, `:1286-1287`
  bullet; `ops_catalog.md:75` verbatim.
- **Research-doc citations:** cba §optimizer §2 (the N-table: 1333/3.1 ms → 7157/16.7 ms, 12.9× nodes
  → 11.9× time, `2N+2`/`N+1`, Δ=52 — and the plan's r-note disambiguating the cba's letter `D` from
  §3.3's is correct), cba §optimizer §3 (projection), cba §corpus §5 (`graph_bloat_note` O(10⁴));
  lit §rdf-vary §5 (arXiv:2212.04889 quote; the file-name-collision and Snapshot-bitmask pain points)
  and §6 (naming vocabulary); lit §coffea-sys §5 — the plan's "#469 … word-level UNVERIFIED
  (`systematics-vary-litsearch.md:236` carries the caveat)" is exact: line **236** is that bullet and
  it carries the caveat verbatim.

### C. Arithmetic and counts checked

`9 = 6 + 3` of 15 refs ✓ · `Δ = K + 2 = 52` ✓ · `stages == N+1`, `reduced == 2N+2` ✓ ·
`ln24/ln8 = 1.53`, `ln24/ln5.37 = 1.89`, `5.37² ≈ 28.8`, `28.8/24 ≈ 1.2`, `16.0/5.64 ≈ 2.8`,
`28.8/16 ≈ 1.8` ✓ · e-form cap arithmetic: `"1.5e31"` → `15`+30 zeros = 32 digits (at the cap, legal;
naive `2+31=33` rejects — the accepted half really is the discriminating one), `"1.5e32"` → 33,
`"-1.5e31"` → 33 rendered characters, `"1e40"` → 41 digits, `"1e-40"` → `1em40` (5 chars), and the
fractional length identity `len(mantissa)+2+len(exponent)` = 31+2+2 = 35 against a normalized count of
31−35 = −4 ✓ · 12 bases → 24 labels, 3 → 6, 7 passes ✓ · 522 identical lines ✓ · 4.7× mask packing ✓ ·
39-name m24 pin ✓ · 65/73 gak ✓ · 26 numpy-only names, 32 vs 6 `dir` counts ✓ · 22 `graphed.numpy.__all__`
entries ✓ · 23 reference JSONs ✓ · 12 uproot test files + 2 helpers ✓ · 15 executor milestone dirs ✓ ·
5 `_array_cls` chokepoints ✓.

---

## Notes for the record (not findings)

1. **Version drift is nil where it matters.** The plan's boost_histogram probes are attributed to
   1.7.2 and/or 1.8.0; every one of them reproduces on the 1.8.0 in `graphed-histogram-latest`'s venv,
   so the dual attribution is not load-bearing anywhere.
2. **`pyarrow` is absent from `graphed-latest`'s venv**, so the §6.4e/§6.4g parquet probes
   (`ak.to_parquet` vs `pq.write_table` bytes/KV sets, `created_by = parquet-cpp-arrow version 25.0.1`)
   could not be re-run here. They are internally consistent with the worklog and with the plan's own
   r13/r14 corrections (the withdrawn unnamed-array digests), and the r14 environment note
   ("a clean resolve of `awkward>=2.12` + `pyarrow` gives 25.0.1") is a falsifiable, stated
   methodology — I flag the non-re-run only for completeness, not as a defect.
3. **The plan's self-corrections check out where I could test them.** `histograms.py:40-43` (r22's
   correction of `:39-42`) lands on `fingerprint` including its `return … [:16]` at `:43`;
   `projection.py:109-147` (r15/r16's correction of `:109-121`) is the whole function;
   `graphed/__init__.py:44 == "apply"`, `:46 == "compile_ir"` (r16's correction) is exact;
   `src/store.rs:185-200` with `mark_output(map[o])` at `:197` (r21) is exact.
