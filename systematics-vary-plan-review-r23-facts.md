# systematics-vary-plan review — round 15, revision r23 — FACTS / HALLUCINATION lens

- **Lens:** facts / hallucination audit — every `file:line` anchor (body + Anchors appendix), every
  measured/"verified" claim, every citation into the two research docs, prior-art claims, and all
  arithmetic/counts.
- **Plan revision reviewed:** r23 (`systematics-vary-plan.md`, 5605 lines).
- **Date:** 2026-07-30.
- **Isolation:** fresh context; every claim below rests on a file I opened or a command I ran in
  this session. Nothing is carried over from earlier review rounds.

## Verification roots used

| Root | Revision (re-confirmed in session) |
|---|---|
| `/private/tmp/claude-501/graphed-latest` | `ff7c607a8ba637ebc1b5db37316adf6e10028dcc` |
| `/private/tmp/claude-501/graphed-exec-check` | `201ea4231b8e2329dbee366ef1064db00888e5f6` |
| `/private/tmp/claude-501/graphed-histogram-latest` | `211cbbe22497b64ce624d4880005af7faddf74f7` |
| `/private/tmp/claude-501/uproot5-graphed` (branch `graphed-mvp`) | `393ecefee80aa4fdf563d938e4ff906f329126d8` |
| `/private/tmp/claude-501/graphed-corpus-latest` | `49650e4a628201cfac569b1829aaa6c32655ec92` |
| `/private/tmp/claude-501/prior-art/{ewkcoffea, ewkcoffea-coffea2023, wwz4l, …}` | `063e8d7` / `63abb06` / `cc71718` |
| `/Users/lgray/vibe-coding/coffea-workdir` | `f34b8bdf` |
| Interpreters used | `graphed-latest/.venv` (CPython 3.12.10, awkward 2.12.0, cloudpickle 3.1.2); `graphed-histogram-latest/.venv` (boost_histogram 1.8.0) |

---

## Findings

### 1. HIGH — §3.4 / m49 impact-set anchor: "exactly one construction exists" is measurably false; the pinned fixture is the degenerate one

**Where.** §10, m49 anchor list, the r23-added clause:

> **The FIXTURE is stated, because exactly one construction exists, r23** … under hash-consing two
> labels share a node iff that node's input ids agree, which transitively requires their `vary`
> members to be structurally IDENTICAL (`src/store.rs:73-88`; measured, `a = src * 2.0; b = src *
> 2.0` → `a.node_id == b.node_id == 1`, `session.node_count() == 2`), so the shared node comes from
> giving two labels the SAME member expression — §1.2's dedup case, `vary(x, "jes", up=e, down=e)` —
> and the naive fixture (two labels with DIFFERENT members plus a "shared" downstream op) does not
> exist at all. The two impact sets are then identical rather than merely overlapping …

**Detail.** The interning half is right and I reproduced it (`a.node_id == b.node_id == 1`,
`node_count() == 2`). The *inference* is not: a node reachable from `jes_up`'s and `jes_down`'s
outputs but not from nominal's does **not** require identical members. It only requires a shared
**upstream sub-expression of the two members** that nominal's member does not use. §3.4 defines the
impact set as `reachable(label's outputs) − reachable(nominal outputs)`, and a common
sub-expression of the two varied members sits squarely inside that difference for both labels while
the members themselves stay distinct. Only the *downstream* variant of the fixture (distinct
members, a "shared" op below the fork) is genuinely impossible — that narrower statement is true,
but it is not what the clause binds.

**Evidence (measured this session, `graphed-latest@ff7c607`, `.venv`).** Simulated per-label
expansion in one `Session` (no `vary` implementation needed), nominal member independent of the
shared node:

```
nom  = src2 * 1.0        # nominal member
u    = src2 * 7.0        # shared sub-expression, NOT used by nominal
up   = u + 1.0
dn   = u + 2.0
```
```
cones:  {'nominal': {0, 1}, 'up': {0, 2, 3}, 'down': {0, 2, 4}}
impact up:   [2, 3]      impact down: [2, 4]
shared-in-both (not nominal): [2]      u.node_id = 2
members identical?  False
```

i.e. node `2` is in **both** impact sets and in neither nominal cone, with `up.node_id !=
dn.node_id`. This is exactly §3.4's own worded case ("a node shared by `jes_up` and `jes_down` but
not nominal appears in **both** impact sets"), and it is a natural physics spelling — a `pu`/`btag`
SF whose `up`/`down` members share a base expression the central member does not
(`vary(events, "pu", w_nom, is_weight=True, up=u*1.1, down=u*0.9)`).

**Why it matters.** The clause is the stated reason for pinning a frozen m49 fixture. Under the
pinned `vary(x, "jes", up=e, down=e)` fixture the two impact sets are *identical*, so the anchor's
headline property degenerates to "the same set twice" — the plan concedes this and rescues
non-vacuity only against the id-watermark implementation. The shared-upstream fixture is strictly
stronger (sets overlap but differ, so an implementation that returns one label's set for both, or
that unions the two, fails) and it is what §3.4's prose actually describes. The pinned fixture is
not *wrong*, so this is not a BLOCKER; but a test-author is being told a better construction "does
not exist at all", which is false.

**Suggested fix.** Replace the "exactly one construction exists" claim with the true, narrower one
("no node *downstream* of the fork can be shared by two labels with distinct members — interning
keys on input ids"), and state the fixture as the shared-**upstream** form: nominal member
independent; `up`/`down` members both derived from one shared node `u`. Assert `u ∈ impact(up) ∩
impact(down)`, `u ∉ reachable(nominal)`, **and `impact(up) != impact(down)`** — the last conjunct is
what the degenerate fixture cannot carry. Keep §1.2's identical-member dedup case where it already
lives (m48's §1.2 anchor).

---

### 2. MID — §2.6b's r23 illustration uses a mixed-granularity multi-axis fill, which the plan itself establishes cannot execute

**Where.** §2.6b, the r23 CONTEXT HANDLE IDENTITY paragraph (and verbatim again in the r23 entry of
the revision history):

> … so the divergence rule fires on legal programs (`h.fill(graphed.nominal(sel).MET.pt,
> graphed.nominal(sel).Jet.pt)`; `sel1 = events[mask]`, `sel2 = events[mask]`), a FALSE refusal …

**Detail.** `MET.pt` is per-event and `Jet.pt` is per-object. §6.1d's r19 clause binds the opposite
and gives the measured reason: the evaluator flattens each AXIS input independently
(`graphed-histogram src/graphed_histogram/boost.py:39-47,60-71`) and `boost_histogram` requires
equal lengths across axes, so such a fill dies at evaluation for a reason unrelated to the
mechanism being illustrated — and §6.1d/§10 explicitly repaired two *earlier* fixtures
(`h.fill(events.MET.pt, sel.Jet.pt)`, `h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)`) for exactly
this, with "**both axis values are PER-EVENT, and the fixture MUST NOT be 'improved' to a per-object
second axis, r19**". r23 re-introduces the same shape in a new illustration and calls the program
"legal".

**Evidence (measured, boost_histogram 1.8.0, `graphed-histogram-latest/.venv`):**

```
bh.Histogram(Regular(3,0,10), Regular(3,0,10)).fill(np.arange(3.0), np.arange(5.0))
→ ValueError: spans must have compatible lengths
```
and the independent-flatten site is verified at `src/graphed_histogram/boost.py:60-71`
(`axes = [_flat(v) for v in values[: self.n_axes]]`, then `h.fill(*axes, …)`).

**Why it matters.** §2.6b is a binding section, and the r23 m48 anchor it adds ("two separate
`graphed.nominal(sel)` reads … UNIFY rather than raising") does not spell its own program. A
test-author reaching back to §2.6b for the fixture transcribes a fill that reds at evaluation,
post-freeze, against a correct implementation — the precise mid-freeze-discovery class this plan
repairs four other times (`gak.full_like`, `stable()` rounding, `h.axes.name`, the pt-cut jets).
The risk is partly mitigated because the anchor is attached to the *op-level* divergence bullet
(observable with a binary op, no fill), but the illustration is what the reader sees first.

**Suggested fix.** Respell the illustration with same-granularity axes — e.g.
`h.fill(graphed.nominal(sel).MET.pt, graphed.nominal(sel).MET.phi)` — or drop the fill and use the
op-level form the anchor actually needs (`graphed.nominal(sel).MET.pt + graphed.nominal(sel).MET.phi`).
The second illustration (`sel1 = events[mask]; sel2 = events[mask]`) already carries the argument
and needs no change.

---

### 3. LOW — m48 target line (r23): "three m48 anchors carry a non-empty `S`" over-counts by one

**Where.** §10, m48 target line:

> **The r22 justification "m48 has weight labels only, so `|S| = 0`" is WITHDRAWN as measurably
> false of m48's own anchor list, r23**: §6.1b r19 defines `S` as the labels borne by any AXIS value
> or by a `Varied` `sample=`, and three m48 anchors carry a non-empty `S` — the four-way fold-order
> anchor …, §2.3b's `plain_array[varied_mask]` entry point, and §6.1d's link-kind-(1) fixture …

**Detail.** `S` is defined in §6.1b as a property of a **fill** ("the labels that require their own
SIBLING fill node"). m48's §2.3b anchor performs no fill: it asserts that
`plain_array[varied_mask]` / `plain_array.filter(varied_mask)` return a `Varied` carrying the
mask's labels, with negative controls whose stated discriminator is that the wrong-implementation
failures are "*both invisible to a histogram-value comparison*" — i.e. the anchor is deliberately
fill-free (§10, m48 §2.3b bullet). `S` is undefined for it.

The substantive point (r22's `|S| = 0` justification is false) stands on the other two anchors,
both of which I checked: the four-way fold-order anchor has varied values in TWO axes plus a varied
`sample=`, and §6.1d's link-kind-(1) fixture is `h.fill(events.MET.pt, sel.MET.pt)` with
`sel = events[varied_mask]`, whose axis value is `Varied` after re-indexing.

**Suggested fix.** Change "three m48 anchors" to "two m48 anchors" and drop the §2.3b item, or
re-word it as "and §2.3b's `plain_array[varied_mask]` anchor produces axis-borne labels, though it
does not fill".

---

### 4. NIT — grammatical/typo and span-width nits

- §6.4a: "or an **mapping** of `Varied` masks — `{0: event_mask, ("Jet", 1): jet_mask, …}`" — "an" →
  "a".
- `python/graphed/execute.py:110-117` is cited twice (§8.2(i) body and the appendix `CompiledGraph`
  row) for "stage members evaluated inline". Measured, the `kind == "stage"` branch is `:110-115`;
  `:116` starts the `external` branch. The plan itself uses the correct `:110-115` elsewhere
  (§8.2(iii)). Content is inside the cited span, so nothing is stale — just two lines wide.
- §10's quote of the uproot workflow test step, "`python -m pytest -vv tests -m "not xrootd"` at
  `:55`", truncates the real line, which continues `-k "not xrootd" \` plus `--reruns 10
  --reruns-delay 30 --only-rerun …` on `:56-57`. The claim it supports (no `--cov`) is correct.

---

## What I verified clean (no finding)

Everything below was re-derived in-session; each matched the plan exactly unless noted.

**Anchors appendix + body `file:line` (sampled ≈120 cites, all repos).**
`src/store.rs:73-88` (intern), `:147-156` / `:152-153` (mark_output dedup), `:185-200` incl.
`mark_output(map[o])` at `:197`; `src/node.rs:39-41`, `:41-85` with variant heads at
42/46/51/56/64/72/81, `:102-103` (`is_boundary` = `!Op`); `src/optimizer/mod.rs:88-116` (`remap` at
`:101`, never returned); `src/optimizer/engine.rs:7-13` (the verbatim "blows up … on the deep chains
a systematics graph produces"), `:22-31` (`SYMMETRIC_OPS`, the four `IDENTITY_TOKENS`), `:54-56`;
`src/lib.rs` `#[pymethods]` blocks at `:102`/`:159`/`:470`, GraphStore impl closing `:416`, and the
15-method enumeration is complete (plus `new`) with no id-mapping accessor.
`python/graphed/array.py:54,127-128,137-143,283-290,332-335,344-371,374-391,397-410`;
`session.py:29-32,50-51,113-125,133-140,142-168,170-204,206-242,245-252,268,291-301` — the five
`_array_cls` sites (140/168/183/204/242) and five `_provenance.setdefault` sites
(138/166/181/202/240) are exactly as claimed, and `source()` takes no context;
`execute.py:36-45,54-58,68-80,85-91,99-126` (incl. `:104-105` "no data bound", `:116-124` external
dispatch by `content_hash`, `:126` `[vals[o] for o in store.outputs()]`);
`aggregate.py:44-55,57-65,68,86,89-93,95,96-104,101`; `projection.py:109-147` with `conservative =
False` at `:123`, `nonlocal` at `:130`, `= True` at `:140`, the loop at `:143-144`, and
`if conservative or not needed: return None` at `:145-146` (r23's correction is right);
`core/plan.py:72-76,164-176`; `core/execution.py:206-217` (`Plan.process` annotated
`Callable[[Partition, WorkerResources], R]` at `:210`), `:219-224`, `:335-351` (`TaskEvent` fields
exactly `{phase,key,worker,t,partition,n_entries,bytes_read,error}`), `:378-384`, `:448-458`
(sorted-key fold); `debug/errors.py:75-78,80-81`; `debug/runner.py:6-7`; `checkpoint/runner.py:77-91,
100-109`; `checkpoint/store.py:31-41,62-73`; `preserve/bundle.py:103-123,206-210,268-288`;
`preserve/externals/_base.py:215-…`; `preserve/externals/correctionlib_external.py:14-18`;
`awkward/io.py:111-127` (`(out,) = evaluate_ir` at `:121`), `:157-185`, `:206-216` (no `select=`),
`:230-231` (compiles at the call); `numpy/io.py:163-171,182-191`; `numpy/creation.py:27-28,31-75`;
`numpy/__init__.py:578`; `awkward/functions.py:18,118-119,505-509,612-616,677-685`;
`shuffle.py:84,89,92-96,170,181,188,245,259`; `write.py:32-43,77-79`; `parquet.py:77`;
`errors.py` (`GraphedError(Exception)`, unrelated to `NotImplementedError`).
graphed-histogram: `boost.py:39-47,58-72,86-98,100-122,127-130,144-150,152-182,196-219,244-253,
256-295` — `fill_nodes` at `:281`, `layout` at `:282`, `aggregate_plan` at `:286`, `plan()` return
type `Plan[dict[str, bh.Histogram]]` at `:262`, `_GroupReduce.__call__ -> dict[str, bh.Histogram]`
at `:108`, params dict `{spec, n_axes, weighted, sampled}` with `n_weights` only when `> 1`, and
`sample` appended with no type check. Frozen tests: `m29:75-79,82-99`, `m23:60-66,68-77,74-75,86,89,99`.
uproot fork: `RNTuple.py:1560-1562` (exact-first), `:1564-1569`, `:562,567` (both inside `to_akform`,
which starts `:505`), `_cascadetree.py:1606`, `TBranch.py:2015-2017,2019-2024`,
`_graphed_write.py:59-64` (zero `compile_ir`/`evaluate_ir` in the file).
Root prompt: R0.4a at `:147-153` (says exactly what §7.2 r23 re-cites it for, including the
src-only-repos cleanup note), `:25`, `:1262`, `:1282`, `:1284` header / `:1285` blank /
`:1286-1287` bullet. Corpus: `ops_catalog.md:75` verbatim; `graph_bloat_note` O(10⁴).

**Measured claims re-run.**
- §3.3/§5.2a/§8.2(i) topology, rebuilt from scratch (D=500, K=50): N=16 → `stages 17 / reduced 34 /
  1333 reachable / 3.70 ms`; N=128 → `129 / 258 / 7157 / 21.52 ms`; without the terminating
  reduction, `reduced = N + 2` (18 / 130); `Δ(N=1→2) = 52` with, `51` without. Kinds
  `{source:1, stage:N+1, reduction:N}`. r19's `N=3 → 4/8/{1,4,3}` and r20's shared-node extension
  (`2N+3` / `N+2`: N=3 → 9/{1,5,3}, N=16 → 35/{1,18,16}) and the DCE'd dead branch all reproduce
  exactly. Node ratio 5.37× ✓; the cba's "12.9× nodes → 11.9× time" is over N=1→128 (7157/553,
  16.7/1.4) and is internally consistent with its own table.
- §7.2 probes: record ids `src 0, dead 1, b 2, e 3, c 2`; `compile_ir(s, b, e, c)` →
  `outputs() == [1, 2]`; `evaluate_ir` → 2 values; `s._store.outputs() == []`. Optimizer merge:
  `w, w*1.0, w*2.0, w*0.5` (ids 0/1/2/3) → `outputs() == [0, 1, 2]`, 3 values. Fill path
  (numpy idiom): two fills weighted `w` vs `w*1.0` → fill node ids **2** and **4** →
  `outputs() == [2]`.
- §2.2/§2.3a property dispositions: on a 1-D partitioned source, `dtype`/`ndim`/`shape` →
  `node_count()` delta **0**; `T` → delta **1**; `gnp.ones(s, (4, 3)).T` → `GraphedTypeError: …
  transpose without axes reverses them, displacing the partitioned axis 0`.
- §2.3c/§2.3d surface counts: gak public = **65** (73 `def`s); `graphed.awkward` under the bound
  discovery rule (module filter) = **0**, and the unfiltered alias yields exactly the wrong six
  (`from_awkward`/`from_parquet`/`project`/`project_buffers`/`read_parquet_partition`/`to_parquet`);
  the annotation-wide filter over `graphed.__all__` = exactly
  `{aggregate_plan, apply, join, join_plan, pack_key, read_columns, repartition, shuffle_plan}` (6
  refusing + 2 expanding), with `compile_ir(session: Session, *outputs: Any, …)` absent from it and
  present in `__all__` (`:46`; `:44` is `"apply"`); `dir(Array)` public =
  `['filter','map','node_id','reduce','repartition','session']`; `dir(NumpyArray)` = 32 public,
  adding `T`/`dtype`/`ndim`/`shape`; discovered `NumpyArray` properties =
  `['T','dtype','ndim','node_id','session','shape']`. All five §2.3e operand kinds cover every
  primary among the 65 (checked by enumeration).
- boost_histogram 1.8.0: `sample=` rejected on `Double()` **and** `Weight()`
  (`TypeError: Keyword(s) sample not expected`), accepted on `Mean()`/`WeightedMean()`;
  `StrCategory(..., name=…)` → `TypeError`; `h[{"variation": …}]` → `TypeError: list indices must be
  integers or slices, not str`; `h[{1: ax.index(l)}]` equals `h[{1: bh.loc(l)}]`; `h.axes.name` →
  `AttributeError: object Regular has no attribute name` on a 2-axis histogram while
  `[a.__dict__.get("name") for a in z.axes] == [None, 'variation']` survives `spec_of`→`zero_of`;
  under-declaration `sum 2.0` vs `sum(flow=True) 3.0`, over-declaration `3.0 == 3.0`; cross-axis add
  → `ValueError: axes have different length`; `_STORAGES` carries `Mean`/`WeightedMean`.
- awkward 2.12.0: `ak.broadcast_arrays` over lengths 7 and 3 → `ValueError: cannot broadcast
  RegularArray of size 3 with RegularArray of size 7`; `float32 ^ float32` → `TypeError`;
  `"metadata" in signature(ak.to_parquet)` → `False`; `AWKWARD_INFO_KEY` defined ONCE at
  `_connect/pyarrow/table_conv.py:16` and written only inside that module
  (`convert_awkward_arrow_table_to_native`, `:19-40`), imported by `ak_to_parquet.py:14` and called
  at `:417`, with the public `replace_schema_metadata` merge point at `:424-431`.
  Frontend: `w[:, 1]` → `TypeError: unsupported index …`; `gak.firsts(w[gak.local_index(w) == 1])`
  over `[[1,2,3],[4,5,6]]` → `[2, 5]`; `gak.with_field(a, gak.num(a), "x")` → `GraphedTypeError`
  while `num`/`unzip`/`drop_none`/`singletons`/`firsts` record cleanly.
- **§4.1 correctionlib digest (r23's headline re-measurement): reproduces exactly.** Over
  `agc.correctionlib_json()` at its default `scale=1.0` (`tests/frozen/preserve/m9/agc.py:38`),
  `correctionlib_content_hash` →
  `sha256:e72c0da3cb6614cfaf50cea8c93ab740e8229986024a8bad4361e9ae82f4b5cd`. r23's withdrawal of the
  unnamed-payload `sha256:cae4dd4b…` is justified.
- **§8.2(i) digest triple: reproduces exactly.** cloudpickle 3.1.2 / CPython 3.12.10, payload
  `(3, frozenset({...}))`, `PYTHONHASHSEED` 1/7/12345 → `b7984b3caadf74f7` / `2778da7a97834ac5` /
  `97429e5989f2a831`.
- **§7.3 cloudpickle qualitative claims: reproduce.** Importable module-level frozen dataclass with
  vs without one defaulted `variation_labels` field → different digests; importable + sorted tuple
  → ONE digest across three seeds; + `frozenset` → three distinct; `__main__`-defined → three
  distinct. My same-shaped probe gives a *different* literal pair than r22's, which is precisely
  r23's stated reason for withdrawing `8d058bf867dc6bcd` / `22a566276fd6077d` — the withdrawal is
  correct and self-consistent.
- **§10's r23 uproot-gate analysis: fully confirmed at `393ecef`.** `pyproject.toml:136`
  `testpaths = ["tests"]`; `graphed.yml:7-10` `push: branches: [graphed-mvp]` + `workflow_dispatch`,
  no `pull_request`; `:26-32` ubuntu-latest, CPython 3.11/3.12 only; `:55` the pytest step;
  `grep -c cov graphed.yml` → **0**; **no** `[tool.mypy]` section and **no** `[tool.coverage]`
  anywhere; `graphed.yml` is the only workflow referencing graphed; 12 flat `tests/test_graphed_*.py`
  + the 2 helper modules; zero `tests/frozen` references repo-wide.
- Fixture/CI facts: `graphed` dev extra carries boost-histogram/hist and **no** `graphed-histogram`
  (`pyproject.toml:42-48`) while CI installs `.[dev]` at `:34,57,143`; the `importorskip` house
  pattern at `m25:31`, `m27:185,207`, `m30:155`; vendored `tests/_corpus/references` = **23** JSONs;
  `pythonpath` at `:115-127`; `scripts/run-tests.sh:16-25` + `SPLIT_PKGS` at `:30`.
  `graphed-histogram`: zero corpus hits, `ci.yml:44` = `pytest tests/frozen --cov=graphed_histogram
  --cov-branch …`, `:67` = bare `pytest tests/frozen`, `pythonpath` at `:50`, `[tool.mypy]
  files = ["src"]` at `:70-73`, runtime deps `:21` vs dev `:25-39` (awkward dev-only), version
  `0.0.1` — and PyPI `graphed-histogram` resolves to `0.0.1` (fetched in session).
  `graphed-executors`: `ci.yml:44,67` whole-tree runs, `:101`/`:153` per-milestone runs (r23's span
  correction is right), env `GRAPHED`/`CORPUS` at `:15,17` with no histogram anywhere, `pythonpath`
  at `:54`, 15 milestone dirs, zero `__init__.py`, zero `task_id`/`DurablePlan` in `src/`.
  `grep "StageError("` over `python/graphed/` → exactly 2 hits; `DurablePlan(` in `python/` → 0;
  `OpSpec.from_callable` only at `shuffle.py:181,188,245,259`.
- Corpus + arithmetic: `systematics.py:25-36` (`ak.prod` per-jet SF over `axis=1`), `:39-45`
  (`ak.with_field` JES), `:60-61`, `:74-76` (`sel_jets = good[sel]` → `_btag_weight(sel_jets)` —
  the r19 pt-cut-jets note is correct), `:91-92`, `:79,102,50` (pre-fill rounding + the view
  rounding in `_round_hist`); `histograms.py:20,35-37,40-43` with `fingerprint`'s return at `:43`
  (r22's span correction is right). Fixture catalog: ttbar 2 regions × 5 variations + ttgamma 5 =
  **15** systematics references (23 JSONs total with the 8 ADL) — so m48's "**9 of the 15**"
  (6 ttbar btag + 3 ttgamma pho) is exact. m05 invariants at `:25`/`:33` in consolidated `graphed`
  and `:26`/`:34` in `graphed-corpus` — matching r22's re-measurement. m24 parity pin is a **39**-name
  literal at `:39-79` with `full_like` at `:75`.
- Prior art: coffea `f34b8bdf` `CorrectedJetsFactory.py:36-47` (PCG64 seeded from the array's own
  bytes) and `:64-95` (one shared `jet_resolution_rand_gauss`, per-label `jersf = …[:, variation]`,
  signed `deltaPtRel`, hybrid `detSmear`/`stochSmear` — non-monotone by construction);
  `ewkcoffea@063e8d7 wwz4l.py:396-397` (the "these weights can go outside the sys loop" comment) and
  `:1204-1207` (the nominal-only exclusion rule); `ewkcoffea@63abb06 wwz4l.py:807-809,858-865`
  (`hout = {}` inside the shift loop; `masked_val_cache`/`masked_weights_cache`) and
  `run_wwz4l.py:259-261` ("# Does not work" over the commented `cloudpickle.dump`), `:302-313`
  (timing); `FNALLPC/wwz4l@cc71718 analysis_processor.py:395-400,711-718`, zero dask/`dataset_tools`
  surface repo-wide, and `ApplyJetSystematics` **byte-identical** to `ewkcoffea@main`'s (14 lines,
  equal). The 27-label count (1 + 20 + 6) and the 12-bases→24-labels count are recorded in
  lit §ewkcoffea-confirmed as cited. (The "522 identical processor lines" figure lives in the lit
  doc's own table; my independent SequenceMatcher count over the same two files gives 639 — a
  different metric, same order of magnitude, and the plan cites the doc faithfully, so no finding.)
- Research-doc citations spot-checked: lit `:67` (arXiv:2212.04889 quote), `:236` (coffea #469
  ~2-3× / up to ~7-8×, carrying the word-level-UNVERIFIED caveat the plan reproduces), `:411`,
  `:443`, `:456`, `:464`, `:481`, `:545`, `:553`; cba §optimizer §2 (the 5-row table and the
  `2N+2` / `stages = N+1` statement), §optimizer §3 (projection), §optimizer §4. Worklog `:183,187`
  carries the compression probe: raw 3.551 MB / ratio 2.883 / xor 3.280, masks 798 KB → 169 KB
  (~4.7×) — the plan's §6.4c/§11 numbers match, and 798/169 = 4.72.
- §1.1 encoding arithmetic: `0.5→5em1`, `2.5→25em1`, `1.2345→12345em4`, `-1.5→m15em1`, `1e-8→1em8`,
  `50em2→5em1` all check; `"1.5e31"` renders 32 plain digits (`15` + 30 zeros) and `"1.5e32"` 33,
  `"1e40"` 41, `"-1.5e31"` 33 rendered characters, `"1e-40"` → the 5-character `1em40`; the r22
  fractional worked example (31-digit mantissa → normalized count −4, rendered length 35 =
  31 + 2 + 2) is self-consistent. §9.1's `5em1 → 0.5`, `m15em1 → −1.5`, `2p5 → 2.5` all check.
- Internal-consistency spot checks that came out clean: the five m51 `select=` controls all decide
  identically under r23's `vary`-link admission (each refusal is separated by a mask-derivation or
  projection link, never by `vary` alone) and the new sixth control is the only one that
  discriminates it; §9.1's universe/nominal `graphed.selection` answer (`handle = events` for
  `graphed.selection(graphed.nominal(sel))`) is consistent with §2.3e's ORIGINATION rule; §2.2's
  `jes` + `up_2` vs `jes_up` + `2` prefix-collision example both yield `jes_up_2`; m50's r23 fourth
  output (axis-mode, unvaried, 1-bin variation axis) is consistent with §6.2(ii) and §6.1c's r22
  MODE-decides-the-key rule; §2.3d's 6-refusing/2-expanding split matches the measured 8.

---

## Verdict

**Dirty — but only just.** One HIGH, one MID, one LOW, one NIT bundle; **no BLOCKER**.

r23's own new measurements are the strongest part of the revision: the correctionlib payload digest,
the §8.2(i) seed triple, the §7.3 cloudpickle shape, the uproot-fork gate analysis and every stale
span it corrected all reproduce exactly against the pinned roots, and its two withdrawals
(`8d058bf8…`/`22a56627…`, `sha256:cae4dd4b…`) are correctly reasoned. Of roughly 120 anchors and 40
measured claims I re-derived, exactly one is factually false — the r23 §3.4 fixture rationale
(finding 1) — and it is a false *negative existence* claim that pins a weaker-than-necessary frozen
fixture rather than a wrong one. Findings 2 and 3 are r23-introduced regressions of hygiene rules
the plan already established for itself elsewhere (§6.1d r19's same-granularity rule; §6.1b's
definition of `S`). All three have one-sentence fixes and none requires reversing an owner-locked
decision.
