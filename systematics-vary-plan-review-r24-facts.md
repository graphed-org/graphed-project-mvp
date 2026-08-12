# systematics-vary-plan review — round 16, FACTS / HALLUCINATION lens

- **Plan revision reviewed:** r24 (`systematics-vary-plan.md`, 5842 lines, status line "draft for review (r24)")
- **Lens:** facts / hallucination audit — every `file:line` anchor (body + Anchors appendix), every
  measured/probe claim, every citation into the two research docs, prior-art claims, arithmetic and counts.
- **Date:** 2026-07-30
- **Reviewer:** isolated agent, fresh context. Every statement below rests on a file I opened or a
  command I ran in this session; nothing is carried over from earlier rounds.

**Verification roots used** (all confirmed at the pinned revisions with `git log -1`):

| Root | Revision |
|---|---|
| `/private/tmp/claude-501/graphed-latest` | `ff7c607a8ba637ebc1b5db37316adf6e10028dcc` |
| `/private/tmp/claude-501/graphed-exec-check` | `201ea4231b8e2329dbee366ef1064db00888e5f6` |
| `/private/tmp/claude-501/graphed-histogram-latest` | `211cbbe22497b64ce624d4880005af7faddf74f7` |
| `/private/tmp/claude-501/uproot5-graphed` | `393ecefee80aa4fdf563d938e4ff906f329126d8` |
| `/private/tmp/claude-501/graphed-corpus-latest` | `49650e4a628201cfac569b1829aaa6c32655ec92` |
| `/private/tmp/claude-501/prior-art/{ewkcoffea 063e8d7, ewkcoffea-coffea2023 63abb06, wwz4l cc71718, WRemnants c5be6c60, narf 7d73361, mkShapesRDF b89a71f}` | as cited |
| `/Users/lgray/vibe-coding/coffea-workdir` | `f34b8bdf2bdf05754920b49d6b8d6de078b3884f` |

Environments: `graphed-latest/.venv` (CPython 3.12.10, awkward 2.12.0),
`graphed-histogram-latest/.venv` (boost_histogram 1.8.0), plus `uv run --no-project` throwaways for
`awkward==2.12.0` + `pyarrow` (25.0.1) and `cloudpickle==3.1.2`.

---

## Findings

### 1. MID — §6.1c: the "equivalently: …spec differs from `self._spec`" parenthetical is a FALSE equivalence, and it is false exactly on m48's own arm

**Section:** §6.1c (plan `:1703-1708`), echoed in m48's anchor (`:3478-3485`) and in the r24 revision
notes (finding #4) and revision-history entry.

**What the plan says.** "`.plan()` raises — pointing at the group API — on a `Histogram` that is
VARIED *or* in §6.2 AXIS MODE **(equivalently: whose staged fill nodes' spec differs from the
`__init__`-time `self._spec`)**."

**Why it is false.** The parenthetical predicate is satisfied only by the AXIS-MODE arm. In sibling
mode — the default, and the arm m48 exercises — every staged fill node carries `self._spec`
verbatim:

- `Histogram.fill` records `params={"spec": self._spec, …}` and `chash = content_hash(self._spec)`
  (`graphed-histogram@211cbbe src/graphed_histogram/boost.py:187`, `:200-207`), with
  `self._spec = spec_of(self)` fixed in `__init__` at `:148`. A varied sibling lowering records N
  fill nodes on the SAME `Histogram`, so all N specs are that one string.
- Measured this session (graphed-histogram venv, two staged fills on one `Histogram`):
  `all(spec == h._spec for spec in staged_specs)` → `True`, `len(set(specs))` → `1`.
- The plan says so itself, twice: §1.2 keeps labels out of `params`/content hashes in sibling mode,
  and §6.2's own r24 sentence (`:2051-2056`) states "a **SIBLING-mode fill — varied or not —
  hashes exactly as today**" — i.e. the same spec. So §6.1c's parenthetical contradicts §6.2 r24
  and §1.2 in the same revision that introduced both.

**Failure scenario.** The parenthetical is the *implementable* form of the two (a spec comparison is
local to the histogram; "is this histogram VARIED?" needs label knowledge the `Histogram` object does
not obviously carry), and m48's anchor instructs the test-author to "word the anchor over the
predicate, not over 'varied' alone" (`:3479-3481`). An implementer who codes the parenthetical ships
a `.plan()` that does **not** refuse a varied SIBLING-mode histogram — precisely the merge hazard
§6.1c exists to prevent (`_SumFills` sums ALL staged fills into one histogram,
`boost.py:88-98`, silently merging universes). The frozen m48 anchor is worded over the disjunction,
so this surfaces as a mid-milestone red plus a defensible implementer objection ("the plan says the
two are equivalent"), not as a frozen-wrong test — hence MID, not HIGH.

**Suggested fix.** Scope the parenthetical to the axis-mode arm, e.g.: "…VARIED *or* in §6.2 AXIS
MODE (the AXIS-MODE arm equivalently: whose staged fill nodes' spec differs from the `__init__`-time
`self._spec`; the VARIED arm is **not** spec-visible — a sibling-mode fill records `self._spec`
whether varied or not, §6.2 r24, §1.2)." The m48 anchor's wording already names both arms and needs
no change beyond dropping any "the predicate" shorthand that could be read as the parenthetical.

---

### 2. LOW — §10/m48: "**two** m48 anchors carry a non-empty `S`" undercounts its own anchor list

**Section:** §10, m48 target line (`:3282-3290`).

**What the plan says.** "…**two** m48 anchors carry a non-empty `S` — the four-way fold-order anchor
(varied values in TWO axes plus a varied `sample=`) and §6.1d's link-kind-(1) fixture
`h.fill(events.MET.pt, sel.MET.pt)` with `sel = events[varied_mask]` (r24 drops r23's third item…)".

**Why it is inaccurate.** `S` is defined (§6.1b r19, `:1672-1676`) as the labels borne by any AXIS
value or by a `Varied` `sample=`. m48's own §2.6/§6.1d anchor bullet (`:3847-3851`) reads: "ambient
fill on a per-object quantity — the value passed **UNFLATTENED** (§6.1d), **Jet-pT fill yields value
labels ∪ ambient labels**, weight broadcast frozen against a manual-broadcast reference". The "value
labels" term is non-empty by construction there (otherwise the union assertion is not
discriminating), so that axis value bears labels and `S ≠ ∅` for a **third** m48 anchor. m48
carries varied values by design — the same bullet freezes `graphed.labels` on a `Varied`-mask-derived
context and a loose-`vary`-varied mask program (`:3925-3941`).

**Impact.** The sentence's purpose (refuting r22's "m48 has weight labels only, so `|S| = 0`") is
unharmed; the risk is a test-author reading the enumeration as exhaustive and treating the
ambient-fill fixture's value as unvaried.

**Suggested fix.** "…**at least two** m48 anchors carry a non-empty `S` — …" or add the ambient-fill
bullet as the third item.

---

### 3. LOW — §3.4/§9.1: the impact API is shaped "over `read_columns`' operands", which names a measured signature that cannot serve it

**Section:** §3.4 (`:1336-1348`, r24-new) and its §9.1 entry (`:3161-3163`, r24-new).

**What the plan says.** §3.4: "it is a **read-only `graphed` module verb over the same operands as
`read_columns`/`graphed.labels`, returning `{label: tuple[int, ...]}`**"; §9.1: "the §3.4 impact API
(`{label: tuple[int, ...]}` of that label's sorted record node ids, **over `read_columns`' operands**)".

**Why it is a problem.** The two named verbs have incompatible measured operand shapes:

- `read_columns(arrays: Sequence[Array], source_nid: int) -> tuple[str, ...] | None`
  (`graphed-latest python/graphed/projection.py:109`), and
- `graphed.labels(x)` takes a single `Varied` / context / result mapping / histogram (§2.2).

So "the same operands as `read_columns`/`graphed.labels`" resolves to two different signatures, and
the `source_nid` half of `read_columns`' pair has no role at all in a reachability-difference verb
(§3.4's computation is `reachable(label's outputs) − reachable(nominal outputs)` via `session.walk`,
which is source-agnostic — `session.walk(array, *, source, op, external)`,
`python/graphed/session.py:245-252`). §5.3's projection-stats verb legitimately borrows
`read_columns`' operands because it *calls* `read_columns` per label; §3.4 does not.

**Suggested fix.** State §3.4's operands directly: "a read-only `graphed` module verb over the
per-label output `Array`s (the `Sequence[Array]` half of `read_columns`' operands — no `source_nid`),
returning `{label: tuple[int, ...]}`", and mirror that in §9.1.

---

### 4. NIT — §2.2's "`dir(NumpyArray)` = 32" drops the word that makes it true

**Section:** §2.2 (`:540-543`, r24-new).

Measured against `graphed-latest@ff7c607`: `len(dir(NumpyArray))` is **101**;
`len([n for n in dir(NumpyArray) if not n.startswith("_")])` is **32**. The 26-name extra set the
plan lists is exactly right (`T/all/any/argmax/argmin/astype/clip/cumprod/cumsum/dtype/max/mean/min/
ndim/prod/ravel/reshape/round/shape/squeeze/std/sum/swapaxes/take/transpose/var`), and §2.3a's
parallel sentence (`:706-709`) says "32 **public** names". Only §2.2's copy drops "public".

**Fix.** "`dir(NumpyArray)` public = 32".

---

### 5. NIT — §10's quotation of the uproot fork's test step is truncated

**Section:** §10 (`:3251-3253`).

The plan writes: "whose test step is `python -m pytest -vv tests -m "not xrootd"` at `:55` with
**zero `--cov`**". Measured at `393ecef`, `.github/workflows/graphed.yml:55-57` is
`python -m pytest -vv tests -m "not xrootd" -k "not xrootd" \ --reruns 10 --reruns-delay 30 \
--only-rerun "(?i)http|ssl|timeout|expired|connection|socket"`. The load-bearing half — no `--cov`
anywhere in the workflow (`grep -c cov graphed.yml` → 0) — is exact; the quoted command is a prefix.

**Fix.** Add "…(plus `-k`/rerun flags)" or quote the full step.

---

## Verification ledger (what I checked and found CORRECT)

Everything below was opened at the cited lines or re-run in this session and matches the plan.

**Rust IR / optimizer.** `src/store.rs:73-88` intern (lookup at `:81-83`); `:147-156` `mark_output`
de-dup (`:152-153`); `:185-200` `from_reduced` with `mark_output(map[o])` at `:197`.
`src/node.rs:39-41` identity comment, variant heads `:42/46/51/56/64/72/81` with the enum closing at
`:85`, `is_boundary` at `:102-103`. `src/optimizer/engine.rs:7-13` (O(N) extractor note), `:22-31`
(`SYMMETRIC_OPS` + the four `IDENTITY_TOKENS`), `:54-56` (`boundary_from_token`), `:67-80` (rule
construction).

**Frontend.** `array.py:127-128` `__slots__`, `:137-143` `node_id`/`session` properties,
`:332-335` `__getattr__` underscore guard, `:344-371` `__getitem__` (Array/str/list/slice/int, final
`TypeError` `:369-371`), `:374-391` public methods, `:397-410` `graphed.apply` incl. "With one array
this IS `Array.map` (interns with it)", `:54` `rint`. `session.py:39` `_array_cls` (backend
`array_type` seam, `numpy/__init__.py:345`), used at `:140,168,183,204,242` (the five, and only,
call sites), `:50-51` `node_count`, `:133-140` `source`, `:245-252` `walk`, `:291-301` `materialize`
(partition-blind). `execute.py:36-52` `CompiledGraph` (fields `ir`/`source_names`, only method
`evaluate`; `hasattr(CompiledGraph, "outputs")` → **False**, r24's correction is right),
`:54-70` `compile_ir` (`ids = [arr.node_id …]` at `:70`), `:70-80` ids passed as
`serialize/reduce(outputs=ids)`, `:85-91` `evaluate_ir`, `:99-126` bare dispatch loop with
`:104-105` "no data bound for source". `aggregate.py:44-55` `_PartitionReduce` (fields exactly as the
appendix row lists), `:57-65` `__call__`, `:68` signature, `:86`, `:89-93` single-source check, `:95`
internal `compile_ir`, `:96-104` construction, `:101` union projection.
`projection.py:109-147` (`conservative=False` `:123`, `nonlocal` `:130`, `conservative=True` `:140`,
`if conservative or not needed: return None` `:145-146`, `return tuple(sorted(needed))` `:147`).
`__init__.py:9,12`, `__all__` `:27-58` (`:44` `"apply"`, `:46` `"compile_ir"`, `:50-57` the shuffle
verbs). `shuffle.py:5-8,84,89,92-96,142,155,170,181,188,208,220,232,245,259`.
`core/execution.py:206-217` `Plan` + `:210` `process` annotation, `:219-224` `ExecResult`,
`:335-351` `TaskEvent`, `:378-384` `emit_task` (instance passed), `:451` sorted-key fold.
`core/plan.py:72-76` `OpSpec.identity` (`b"ref\0"+ref`), `:125-126` `DurablePlan`, `:164-176` /
`:286-301` `task_id`. `debug/errors.py:75-78` `__eq__` (`__dict__`), `:80-81` hand-written
`__hash__`. `checkpoint/runner.py:77-91`. `preserve/bundle.py:103`, `:206-210`, `:268-288`.
`numpy/creation.py:27-28,31-33`, `numpy/__init__.py:585-599` donor-free constants,
`numpy/io.py:164-165` 1-D cap and `:182-191` signature. `awkward/io.py:111-127` (`(out,) =
evaluate_ir` at `:121`), `:157` `_evaluation_columns`, `:206-216` `to_parquet` (no `select=`),
`:230-231` compile-at-the-call. `write.py:32-43`, `:77-79`. `parquet.py:77` (the only metadata use;
zero `key_value_metadata`/`replace_schema_metadata` hits in `graphed` and in the uproot fork).

**graphed-histogram.** `boost.py:39-47` `_flat`, `:60-71` `FillEvaluator.__call__` (independent
flatten; `weight * _flat(...)` at `:68`; `sample` straight to `h.fill`), `:88-98` `_SumFills`,
`:100-117` count-based positional `layout`, `:120-122` `_add_groups`, `:127-130` `_GroupZero`,
`:146-150` `self._spec`, `:152-178` `fill` (arity check `:160-161`, `inputs` assembly `:175-178`,
sample unchecked), `:180-212` payload/params (`{"spec","n_axes","weighted","sampled"}` + conditional
`n_weights`), `:215-219` `staged_fills`/`fill_nodes`, `:244-253` `Histogram.plan`, `:256-295`
`plan()` (`fill_nodes` `:281`, `layout` `:282`, `aggregate_plan` `:286`, declared return
`Plan[dict[str, bh.Histogram]]` `:262`). `_spec.py:19-27` (`Mean`/`WeightedMean` present), `:31-37`,
`:81-84`, `:70,74` growth refusals, `:115`/`:129`. Frozen `m29/test_multi_weight_fills.py:75-79,
84-87,95-96`; `m23/test_group_plan.py:60-66,68-77,74-75,86,89,99`.

**Re-run measurements (all reproduce).**
- §3.3 topology (D=500, K=50): N=16 → 1333 arena / reduced 34 / stages 17; N=128 → 7157 / 258 / 129;
  timings 3.44 ms → 18.44 ms (ratio 5.36 on this machine vs the plan's 5.64 — same conclusion
  against the 16.0 gate). Arithmetic all correct: 7157/1333 = 5.37; ln24/ln8 = 1.53; ln24/ln5.37 =
  1.89; 5.37² = 28.8 ≈ 1.2× the 24.0 gate; 16/5.64 = 2.8; 28.8/16 = 1.8.
- §5.2a arena delta: N=1→2 Δ = **52** with a terminating reduction, **51** without; without the
  reduction the reduced form is N+2 (18 / 130), with it 2N+2 (34 / 258).
- §7.2 probes: record ids `src 0, dead 1, b 2, e 3, c 2` → `deserialize(ir).outputs() == [1, 2]`,
  `evaluate_ir` → 2 values, `s._store.outputs() == []`; `w, w*1.0, w*2.0, w*0.5` (ids 0/1/2/3) →
  `outputs() == [0, 1, 2]`, 3 values; on the FILL path, `weight=[w]` vs `weight=[w*1.0]` → fill node
  ids **2** and **4** → `outputs() == [2]`.
- §3.4 / m49 impact fixture (r24-new): `k=scale(src)`, `nom=sel(src)`, `up=shift(src,k)`,
  `dn=shift(src,k)` → `impact(up) = [1,3]`, `impact(dn) = [1,4]`, shared non-nominal `= [1] = k`,
  `impact(up) != impact(dn)` → True. r23's withdrawn "exactly one construction exists" is indeed
  false.
- m49 §8.2(i) cardinality literals (D=20, K=5): base and base+dead-branch → N=3: 8 /
  `{source:1, stage:4, reduction:3}`, N=16: 34 / `{1,17,16}`; with the shared-node extension → N=3:
  9 / `{1,5,3}`, N=16: 35 / `{1,18,16}` (`2N+3` / `N+2`). Exactly as r20 records.
- §2.2/§2.3a surface: `dir(Array)` public = `['filter','map','node_id','reduce','repartition',
  'session']` (6); `NumpyArray` public = 32; the 26-name delta is exactly the plan's list.
- §2.2 r19 property classes: `dtype`/`ndim`/`shape` → `Session.node_count()` delta **0**; `T` → delta
  **1** (`numpy/array.py:154-157` `transpose`, `:159-161` `T`); `gnp.ones(s,(4,3)).T` →
  `GraphedTypeError: … transpose without axes reverses them, displacing the partitioned axis 0`.
- §2.3d discovery: the annotation-wide filter over `graphed.__all__` yields exactly
  `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition',
  'shuffle_plan']` (8) and misses `compile_ir(session: Session, *outputs: Any, …)`; gak public
  surface = **65** (73 `def`s, no `__all__`); gak line anchors `18/118/346/383/400/476/513/600/612/
  673/677/687/693/717/722/727/732/737` all exact.
- §2.3e r22 operand kinds: `num/unzip/drop_none/singletons/firsts/where/unflatten` record cleanly on
  a jagged-numeric contexted array; `with_field(a, num(a), "x")` → `GraphedTypeError: ill-typed op
  'ak.with_field' … no tuples or records in array`.
- boost_histogram 1.8.0: `Regular + (Regular, StrCategory)` → `ValueError: axes have different
  length` (1-bin and 2-bin alike); two-axis fill of unequal lengths → `ValueError: spans must have
  compatible lengths`; `sample=` rejected on `Double()`/`Weight()`, accepted on `Mean()`/
  `WeightedMean()`; non-growth `StrCategory` traits `(underflow=False, overflow=True, growth=False)`;
  under-declaration `sum 2.0` vs `flow 3.0`; over-declaration `3.0 == 3.0`; `StrCategory(name=…)` →
  `TypeError`; `h[{"variation": …}]` → `TypeError: list indices must be integers…`;
  `h[{1: ax.index(l)}] == h[{1: bh.loc(l)}]`; the axis name round-trips `spec_of`→`zero_of` as
  `[None, 'variation']`; `h.axes.name` → `AttributeError: object Regular has no attribute name`.
- awkward/pyarrow (2.12.0 / 25.0.1): `ak.from_parquet(columns=["murf_0.5"])` → fields `[]`, len 0;
  `"metadata" in signature(ak.to_parquet)` → False; file-KV via `ak.to_parquet` vs
  `pq.write_table(ak.to_arrow_table(...))` — record: `{ARROW:schema, ak:parameters,
  awkward_array_metadata}` vs `{ARROW:schema, ak:parameters}`; list-of-float and flat:
  `{ARROW:schema, awkward_array_metadata}` vs `{ARROW:schema}`; bytes differ in every case;
  `created_by = parquet-cpp-arrow version 25.0.1`. `AWKWARD_INFO_KEY` at
  `awkward/_connect/pyarrow/table_conv.py:16`, writer `:19-40`, imported at
  `awkward/operations/ak_to_parquet.py:14`, called `:417`, `replace_schema_metadata` `:431`.
  `float32 ^ float32` → `TypeError` for both numpy and awkward; the `view(uint32)` XOR works;
  `ak.broadcast_arrays` 7-vs-3 → `ValueError: cannot broadcast RegularArray of size 3 with
  RegularArray of size 7`. `w[:, 1]` → the quoted `TypeError`;
  `gak.firsts(w[gak.local_index(w) == 1])` materializes `[2.0, 5.0]`.
- cloudpickle 3.1.2 under `PYTHONHASHSEED` ∈ {1,7,12345}: the §8.2(i) triple reproduces **exactly** —
  `b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831`. The §7.3 qualitative shapes
  reproduce too: importable module-level frozen dataclass + sorted tuple → ONE digest ×3; +
  `frozenset` → three distinct; `__main__`-defined → three distinct; adding one defaulted field
  changes the digest. (The withdrawn literals `80e8024dc8f3b77d` / `8d058bf867dc6bcd` /
  `22a566276fd6077d` are correctly withdrawn — they are payload-underspecified.)
- §4.1 correctionlib: over `agc.correctionlib_json()` at its default `scale=1.0` (`agc.py:38`),
  `correctionlib_content_hash` (`preserve/externals/correctionlib_external.py:14-18`) gives
  `sha256:e72c0da3cb6614cfaf50cea8c93ab740e8229986024a8bad4361e9ae82f4b5cd` — the r23 literal, exact.

**Corpus / counts.** 15 systematics references (5 ttbar_4j1b + 5 ttbar_4j2b + 5 ttgamma) out of 23
JSONs total; the m48 subset "ttbar 4j1b/4j2b × {nominal, btag_up, btag_down} (6) + ttgamma
{nominal, pho_up, pho_down} (3) = **9 of the 15**" is arithmetically and factually right (the other
6 are the jes pair on each of the three fixtures). `systematics.py:25-36` `_btag_weight`
(`ak.prod(axis=1)` at `:36`), `:39-45` `_apply_jes` via `ak.with_field`, `:60-61` JES-before-cut,
`:74-76` `sel_jets = good[sel]` → `_btag_weight(sel_jets, …)` (`:75` is the `ht` sum, as the appendix
says), `:91-92` unvaried photons indexed by a JES-varied selection, `:94-99` flat ttgamma SF
(`np.full`), `:107-112` fixture matrices. Rounding: `histograms.py:20` `STABLE_DECIMALS = 6`,
`:35-37` `bin_values`, `:40-43` `fingerprint` (return at `:43`); analysis-side rounding at
`systematics.py:50,79,102`. m05: consolidated `:25`/`:33` vs corpus-repo `:26`/`:34` with the quoted
bodies — the r22 re-measurement is exact. `ops_catalog.md:75` verbatim. `agc.py:38-66,94-118,
106-107,113-115`.

**Packaging / CI / layout.** `graphed pyproject.toml:27` runtime deps, `:29-48` extras (dev =
boost-histogram/hist, no `graphed-histogram`, no `graphed-corpus`), `:80-84` mypy (`strict = true`
`:83`, `files = ["python"]` `:84` — the r23 correction of the r22 mis-citation is right),
`:103-127` pytest ini with `tests/_corpus` on `pythonpath`; CI `.[dev]` at `:34,57,143`.
`graphed-histogram pyproject.toml:21,25-39,50,70-73`; CI `:44` (`pytest tests/frozen --cov=
graphed_histogram --cov-branch`), `:67`, env `:13-17` = `GRAPHED` + `EXECLOCAL` only; zero `corpus`
hits under `tests/` and the workflows. `graphed-executors pyproject.toml:20-35` (no histogram dep
anywhere), `:54` pythonpath; CI env `:13,15,17` = `GRAPHED` + `CORPUS`, installs `:38,65,94,136`,
frozen runs `:44,67,101,153` (with `:101` = m42–m45 and `:153` = m46/m47). `scripts/run-tests.sh:16`
`SUITES` / `:30` `SPLIT_PKGS="frontend numpy awkward"`. Zero `__init__.py` under the frozen trees of
all three repos; `graphed tests/frozen/checkpoint` = `{m8, m39}`; `graphed-histogram tests/frozen` =
`{m23, m29}`; `graphed-executors tests/frozen` = 15 milestone dirs. uproot fork at `393ecef`: no
frozen tree, 12 flat `tests/test_graphed_*.py`, `pyproject.toml:136` `testpaths = ["tests"]`, no
`[tool.mypy]`, `graphed.yml:7-10` push-to-`graphed-mvp` + `workflow_dispatch` (no `pull_request`),
`:26-32` ubuntu-latest × 3.11/3.12, zero `cov` hits; `_graphed_write.py:59-64` copies branches with
zero `compile_ir`/`evaluate_ir` hits. `graphed`'s only frozen `aggregate_plan` callers are
`frontend/m5/test_aggregate_plan.py:77,88,102` and `frontend/m39/test_shuffle_plan_builder.py:58-64`
(m40's is a docstring mention only) — the r21 correction is exact.

**Prior art.** coffea @ `f34b8bdf`: `CorrectedJetsFactory.py:36-47` content-seeded PCG64,
`:64-95` `jer_smear` with ONE `jet_resolution_rand_gauss`, per-label `jersf = …[:, variation]`
(`:84`), signed `deltaPtRel` (`:85`) and the hybrid det/stoch branches (`:88-89,94`) — the
non-monotonicity claim holds. `ewkcoffea@063e8d7 wwz4l.py:1204-1207` (the nominal-only exclusion
rule) and `:396-397` (the verbatim "These weights can go outside of the outside sys loop since they
do not depend on pt of mu or jets"); 12 weight bases (`:439-447`) → 24 labels, 3 shift bases
(`:454-459`) → 6 labels, 7-pass loop. `ewkcoffea-coffea2023@63abb06`: `obj_correction_systs = []` at
`:331` (the "no dask-era object shift" finding is right), `masked_val_cache`/`masked_weights_cache`
and `hout = {}` inside the loop around `:808-865`, `run_wwz4l.py:259-261` "# Does not work" over the
commented `cloudpickle.dump`, `:302-313` the timing block. `FNALLPC/wwz4l@cc71718`: zero
dask/`dataset_tools`/`hist.dask` hits repo-wide; `analysis_processor.py:395-400,408` the intact
shift scaffolding; `ApplyJetSystematics` byte-identical to `ewkcoffea`'s; its 27-label count is the
Run-3 figure the litsearch records (`litsearch.md:415`, "31 (R2) / 27 (R3)"), and the artifact ships
Run-3 skims only (`litsearch.md:549`), so the plan's unqualified "27 labels" is correct for it.
WRemnants and narf: zero `.Vary(` hits (grep-verified); mkShapesRDF: 23.

**Research-doc citations.** cba §optimizer §2 (`codebase-analysis.md:273-283`) records exactly the
table the plan quotes (N=16 → 3.1 ms / 34 / 17; N=128 → 16.7 ms / 258 / 129; "12.9× nodes → 11.9×
time"; Δ = 52), and the plan correctly flags the letter clash (cba's "D" = the per-universe chain,
the plan's "D" = the shared prefix). cba §optimizer §5 (`:301-305`), §corpus §1–§5 (`:416-465`),
§projection (`:285-289`) all say what the plan says they say. lit §rdf-vary §5 carries the
arXiv:2212.04889 "largest pain point" quote (`litsearch.md:67`); lit §coffea-sys §5
(`litsearch.md:236`) carries the coffea Discussion #469 "~2-3×, up to ~7-8×" figures **with** the
word-level UNVERIFIED caveat the plan reproduces. Worklog `:181-188` records the §6.4c compression
probe with its methodology (float32, 1M elems, zlib-6, seed 42, 5 masks flipping ~3%) and exactly the
numbers the plan quotes (raw 3.551 MB, ratio 2.883 — not bit-exact, XOR 3.280; masks 798 KB → 169 KB,
≈4.7×).

**§1.1 e-form arithmetic.** `1.5e31` → `15` + 30 zeros = 32 digits (at the cap, LEGAL); `1.5e32` → 33
digits (rejected); `-1.5e31` → 32 digits + the `m` marker = 33 rendered characters; `1e40` → 41
digits; `1e-40` → `1em40` = 5 characters; the fractional worked example (31-digit mantissa,
normalized count 31 − 35 = −4, rendered `len(mantissa) + 2 + len(exponent)` = 35). All internally
consistent and correct.

---

## Verdict

**Dirty — but only just, and nothing near a BLOCKER.** One MID (§6.1c's false "equivalently"
parenthetical, which is false precisely on the arm m48 exercises and contradicts §6.2 r24 and §1.2
in the same revision), two LOWs (an undercounted anchor enumeration in §10/m48; §3.4's impact API
shaped over an operand pair that cannot serve it), and two NITs.

Everything else this lens is responsible for checks out. I re-opened every anchor class in the body
and the Anchors appendix — Rust IR, frontend, histogram, executors, uproot, corpus, packaging/CI —
and re-ran every cheap probe plus the expensive ones that name their payload; the r24-new material
(the per-idiom `Varied` seam, the `.plan()` re-keying measurement, the `CompiledGraph.outputs()`
correction, the §6.4a record-form discriminator, the §3.4 impact fixture, the §8.2(i) directory
citations) reproduces exactly as written, and the two literal digests the document still asserts
(the `frozenset` triple and the correctionlib payload hash) reproduce byte-for-byte. The document's
discipline of withdrawing payload-underspecified digests is holding: I could not reproduce any
withdrawn literal, and I could reproduce every retained one.
