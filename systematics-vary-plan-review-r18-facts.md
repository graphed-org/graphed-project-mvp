# systematics-vary-plan review — round 10, lens: FACTS / HALLUCINATION AUDIT

- **Plan revision reviewed:** r18 (`systematics-vary-plan.md`, 4209 lines, read in full: Part I,
  every PART II section §1–§12, §10 milestones, the Anchors appendix, and the revision history).
- **Date:** 2026-07-30
- **Lens:** verify the factual substrate — every `file:line` anchor in the body and the appendix,
  every "measured/re-measured/verified" claim, every citation into `systematics-vary-codebase-analysis.md`
  (*cba*) and `systematics-vary-litsearch.md` (*lit*), every prior-art claim, and all arithmetic/counts.
- **Verification roots used (all revisions confirmed with `git rev-parse`):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607`
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42`
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef`
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf`
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md`
- **Method:** anchors opened at the cited lines in the roots above; cheap probes re-run in the roots'
  own venvs (`graphed-latest/.venv`, `graphed-histogram-latest/.venv`) or via
  `uv run --no-project --with …`; expensive/environment-bound claims cross-checked against
  `systematics-vary-worklog.md`'s recorded methodology. Nothing below is asserted from the plan's own
  text alone.

---

## Findings

### 1. BLOCKER — §2.2/§2.3a's r18 PROPERTY rule is factually false for `T`, and its m48 anchor would freeze a wrong assertion

**Section:** §2.2 (r18 property disposition rule), §2.3a (r18 third enumeration), §10/m48
(`§2.3d module-verb dispositions + §2.2's reserved Array-protocol names` bullet, "PROPERTY half").

**Detail.** r18 widens the reserved-name rule from a two-name list to a *discovery rule over
properties*, and states as its factual premise:

> "for every non-underscore property on `type(graphed.nominal(v))`, **`node_id` and `session` raise
> `AttributeError`** … and **every other property is answered EAGERLY on the nominal member** (sound
> by §2.1's form compatibility …; on a plain `NumpyArray` these are already answered from the form
> and never recorded, `python/graphed/array.py:283-290`)" — §2.2, naming
> `shape`/`dtype`/`ndim`/`T` (`python/graphed/numpy/array.py:78,82,86,160`).

§2.3a then binds the gate and §10/m48 freezes it:

> "a third enumeration over `inspect.getmembers(type(graphed.nominal(v)), lambda m: isinstance(m,
> property))` with no leading underscore, asserting each discovered name resolves per §2.2 —
> `node_id`/`session` raise `AttributeError`, every other property answers eagerly on the nominal
> member and **records NO node** (witnessed by a `Session.node_count()` delta of 0 across the access)."

**Measured — the premise is false for `T`, one of the four names §2.2 itself lists.**
`shape`/`dtype`/`ndim` go through `Array._form_meta` (`python/graphed/array.py:283-290`) and are
answered from the form. `T` does not: it is a plain alias for the `transpose` **op**.

```
$ sed -n '158,162p' python/graphed/numpy/array.py
    @property
    def T(self) -> Array:  # numpy parity name
        return self.transpose()
```
`transpose` is `self._session.record_op("transpose", [self], params)`
(`python/graphed/numpy/array.py:157`). Measured in `graphed-latest/.venv` against `ff7c607`:

```
discovered properties: ['T', 'dtype', 'ndim', 'node_id', 'session', 'shape']
  dtype: node_count delta=0     shape: node_count delta=0     ndim: node_count delta=0
  T    : node_count delta=1                     # 1-D source; on a 2-D form it raises GraphedTypeError
```

(The enumeration used is *literally* the one §2.3a binds,
`inspect.getmembers(NumpyArray, lambda m: isinstance(m, property))` with the underscore filter, so
`T` is unavoidably in the frozen gate's discovered set.)

**Why this is a BLOCKER, not a nit.** Two independent failures, both inside m48:

1. **The frozen gate reds against a correct implementation.** §2.3a classifies the numpy idiom's
   `transpose` **method** as *broadcast* ("*broadcast* for the elementwise/structural ones"), so a
   correct `Varied` returns a `Varied` from `varied.transpose()` and records one node per label. The
   property `T` is the same operation under a different spelling; the m48 property-half anchor
   asserts it "records NO node … delta of 0", which a correct broadcast implementation cannot satisfy.
   Frozen ⇒ Test Dispute or an integrity violation.
2. **Followed literally, the rule ships the §2.5 confidently-wrong failure it exists to delete.**
   "Answered EAGERLY on the nominal member" applied to `T` means `varied.T` returns the *nominal*
   universe's transpose and silently drops every other universe — exactly the silent-drop class the
   whole section is written against. §6.1d explicitly keeps the all-numpy varied path live ("the
   numpy `broadcast_like` seam is a NO-OP precisely so an all-numpy varied fill works"), so this is a
   reachable program, not a corner.

The plan is also **self-contradictory** here: `transpose` (method) = *broadcast*, `T` (property alias
for the identical recorded op) = *eager on nominal*.

**Suggested fix.** Split the property set by mechanism, not by "is a property":
- bind the rule over properties **that `Array._form_meta` answers from the form** (measured today:
  `shape`, `dtype`, `ndim`) → eager on the nominal member, node_count delta 0;
- `node_id`/`session` → `AttributeError` (unchanged);
- **any remaining property that records an op — `T` today — takes its METHOD's disposition** (`T` →
  *broadcast*, returning a `Varied` whose `graphed.labels` match the input's);
- state the discriminator so the m48 test-author can build it without guessing: a property is
  *eager* iff accessing it on a plain nominal `Array` leaves `Session.node_count()` unchanged, and the
  gate asserts each discovered property against **that measured classification** rather than against a
  blanket "delta 0". Keep `varied.dtype` as the eager representative and add `varied.T` as the
  recording representative.
- Drop the sentence "on a plain `NumpyArray` these are already answered from the form and never
  recorded" or scope it to `shape`/`dtype`/`ndim`.

---

### 2. HIGH — m49's r18 image-cardinality clause asserts **N + 1** distinct reduced ids; the measured value on the §3.3 topology is **2N + 2**

**Section:** §10/m49, `§8.2(i) accessor + keying, in graphed` bullet, "**Plus a PARTITIONING clause
the §3.3 topology makes exact, r18**".

**Detail.** The clause binds a frozen assertion:

> "the shared-prefix record ids all map to ONE reduced id, each universe's chain maps to a reduced id
> DISTINCT from every other universe's, and **the map's image over the topology has exactly N + 1
> distinct reduced ids** — matching the `stages == N + 1` shape §3.3 already pins (re-measured r18:
> N=16 → 17 stages, N=128 → 129)."

The accessor being anchored is `record_node_id -> (reduced_node_id, member_index | None)` (§8.2(i)),
i.e. it is defined over **every surviving record id** — which on the §3.3 builder includes the
source and each universe's terminating reduction, neither of which is a stage.

**Measured** (`graphed-latest/.venv` @ `ff7c607`, §3.3 builder shape, N=3, D=4, K=3 for legibility;
the shape is scale-invariant and I confirmed the counts at N=16/128 as well):

```
report {'stages': 4, 'reduced_nodes': 8, 'reachable_nodes': 20, ...}
0 source events   inputs []
1 stage           inputs [0]  (shared prefix)
2 stage inputs[1] / 3 reduction inputs[2]
4 stage inputs[1] / 5 reduction inputs[4]
6 stage inputs[1] / 7 reduction inputs[6]
outputs [3, 5, 7]
```

The reduced graph is `1 source + 1 prefix stage + N universe stages + N reductions = 2N + 2`
(= `reduced_nodes`, which §3.3 itself pins as `2N + 2`). Every one of those ids is in the image of
the record→reduced map. The image is therefore **2N + 2**, not N + 1. `N + 1` is the count of
**STAGE-kind** reduced nodes only (`stages` in the report — 17 at N=16, 129 at N=128, both re-measured
and correct).

A test-author freezing the clause as written (`len({rid for rid, _ in m.values()}) == N + 1`) freezes
an assertion a correct accessor fails by construction — the exact defect class this plan repairs
elsewhere (cf. §4.3's withdrawn predicate, §5.2c's withdrawn literal). It is HIGH rather than BLOCKER
only because the trailing clause "matching the `stages == N + 1` shape" gives an alert author the
correct restriction; the sentence itself does not.

**Suggested fix.** Re-word to the measured quantity, keeping both halves (both are non-degenerate
against the constant-map failure the clause exists to catch):

> "…and the map's image over the topology has exactly **`2N + 2` distinct reduced ids**, of which
> exactly **`N + 1` are of kind `stage`** — matching the `reduced_nodes == 2N + 2` / `stages == N + 1`
> shape §3.3 already pins (re-measured r18: N=16 → 17 stages / 34 reduced, N=128 → 129 / 258)."

While editing, tighten the sibling clause "every surviving record id maps to a `(reduced_id,
member_index)` whose reduced id is **in the compiled output/stage set**" — measured, the source
node's reduced id (0 above) is neither an output nor a stage, so that clause is also short by one
kind. "…is a node id of the compiled reduced store" is the true statement.

---

### 3. LOW — `projection.py:146-147` is cited for a snippet that lives at `:145-146`

**Section:** §2.3d (r17 `read_columns` union), §5.3 (`| None` is load-bearing), §10/m49 §5.3 anchor.

**Detail.** The plan writes, three times, `(projection.py:109-115,146-147, "if conservative or not
needed: return None")` and `projection.py:146-147`. Measured:

```
145|    if conservative or not needed:  # whole-record consumption or a bare source read -> read all
146|        return None
147|    return tuple(sorted(needed))
```

So the quoted two-line snippet is `:145-146`; `:147` is a *different* return (the sorted tuple). The
substantive claims are all true — `read_columns(arrays, source_nid) -> tuple[str, ...] | None`
(`:109`, verified by `inspect.signature`), the function spans `:109-147`, and the appendix's
`return tuple(sorted(needed))`, `projection.py:147` is **exact**. Only the quoted-snippet span drifts.

**Suggested fix.** `146-147` → `145-146` in §2.3d, §5.3 and the m49 anchor bullet.

---

### 4. LOW — §4.3 cites `boost.py:205-212` for the `record_external` call; the call is `:196-210`

**Section:** §4.3 (r16 withdrawal rationale).

**Detail.**

> "`Histogram.fill` records ONE External node whose `inputs` are the axis args followed by the
> weights (`…boost.py:175-178`, `inputs = list(args)` at `:175` then `inputs.extend(weights)`; one
> `record_external` over that list, **`:205-212`**)"

Measured in `graphed-histogram-latest@211cbbe`: `inputs: list[Array] = list(args)` at `:175` and
`inputs.extend(weights)` at `:176` — **exact**. But `node = session.record_external(` opens at
`:196` and closes at `:210`; `:205-206` is the `n_weights` conditional inside the params dict and
`:211-212` are `self._fill_nodes.append(node)` / `self._evaluators[chash] = evaluator`. The plan's own
cited source agrees with me: cba §histogram §1 records the call as `boost.py:196-210`.

An implementer opening `:205-212` to see "the `record_external` over that list" lands on the params
tail and the post-call bookkeeping, not the call. (The neighbouring `:198-212` used by §6.3 for the
params key set *is* fine — the dict is `:200-207` — and the appendix's `:166-174,205-206` for the M29
identity discipline is **exact**.)

**Suggested fix.** `:205-212` → `:196-210` in §4.3.

---

### 5. NIT — a cluster of one-line span drifts (claims all true; spans truncate or overshoot)

Each verified individually in the roots; none changes a meaning, but this file is a durable reference
and several of these are the exact lines an implementer will open.

| Plan citation | Measured | Where |
|---|---|---|
| `graphed_histogram.plan()` at `boost.py:254-292` (also spelled `:255-292`, `:256-292`) | `def plan(` is `:256`, the call closes at `:295` | §6.1a, §7.2 r18 SITE, §10/m50, appendix |
| `python/graphed/numpy/__init__.py:578-598` "all in `__all__`" | `__all__ = [` is `:578`; `"zeros"` is at `:599`, outside the span | §4.1, appendix |
| `histograms.py:34-37,39-42` ("`bin_values`/`fingerprint` round again") | `bin_values` is `:35-37`; `fingerprint` is `:40-43` (its `return` falls outside `:39-42`) | §10/m48 matrix bullet, appendix |
| `preserve/bundle.py:103-123` (`build_bundle` signature) | `def build_bundle(` is `:101`; the paired-args raise is `:119-122` | §9.2 |
| `preserve/m9/agc.py:38-66` (correctionlib payload) | `def correctionlib_json(` is `:37`; the `systematic` **input declaration** is `:55`, just outside the `:56-62` span §1.1 cites for "category inputs are arbitrary strings" (the category *block* at `:57-60` is inside) | §4.1, §1.1, appendix |
| appendix: "`:107,118` are docstring mentions of the same" (`parquet.py`) | true, but `:11`, `:24`, `:55` are also non-USE mentions; the load-bearing half ("the only USE is `ParquetFile(path).metadata.num_rows`, `:77`") is **exact**, and `key_value_metadata`/`with_metadata` are 0 hits in both `graphed-latest/python` and `uproot5-graphed/src` | appendix |
| Part I §2 quote "these weights can go outside the sys loop since they do not depend on pt of mu or jets" | verbatim source is "These weights can go outside of **the outside** sys loop since …" (`ewkcoffea@063e8d7 analysis/wwz/wwz4l.py:396`) — a paraphrase presented inside quotation marks | Part I §2 |
| §2.6 note (i): "`gak.firsts(w[gak.local_index(w) == 1])` over `[[1,2,3],[4,5,6]]` materializes `[2.0, 5.0]`" | re-measured against `graphed-latest`: the stated **integer** input materializes `[2, 5]` (int64). The claim's point (the masked inner index is expressible) is confirmed; only the dtype in the quoted result is off | §2.6 note (i), appendix |

**Suggested fix.** Correct the spans in one editorial pass; drop the quotation marks around the
ewkcoffea comment or quote it verbatim; make the `firsts` example's input floats (`[[1.,2.,3.],…]`)
so the recorded result matches.

---

## Everything else in this lens verified clean

Recorded for the audit trail — each item below was opened at the cited lines or re-run as a probe,
and matches the plan.

**Root prompt / catalog (the r18 LOW fix).** `graphed-root-prompt.md:1284` is the Out-of-scope
header, `:1285` is **blank**, and "treating systematic variations as a graph axis" wraps `:1286-1287`
— the r18 correction is right and the r17 `:1285-1286` was indeed off by one. `:1262` (R22.0) and
`:1282` (R22.10) both carry "systematics-as-a-graph-axis … stay Phase 2". `:25` carries the
tens-of-thousands sentence. `ops_catalog.md:75` is verbatim.

**Rust core.** `store.rs:73-88` (`intern`), `:147-156` (`mark_output`, dedup at `:152-153`);
`node.rs:39-41`, `:102-103` (`is_boundary`), and the **whole** `NodeKey` enum `:41-85` with variant
heads at exactly `42/46/51/56/64/72/81` (the appendix's completeness claim is exact);
`optimizer/mod.rs:1-11` (pipeline, "rebuild … into a fresh interned GraphStore"), `:88-116`
(`dead_code_elimination`, `remap` built and never returned); `optimizer/engine.rs:7-13` (the O(N)
extractor note, verbatim "blows up to O(N²) on the deep chains a systematics graph produces"),
`:22-31` (`SYMMETRIC_OPS` + `IDENTITY_TOKENS` incl. `x*1.0`), `:54-56`, `:67-80`, `:89-110`;
`lib.rs` `#[pymethods]` at exactly `:102`, `:159`, `:470`.

**Frontend.** `session.py` — the **five** `_array_cls` sites at `:140,168,183,204,242` and the five
`_provenance.setdefault` sites at `:138,166,181,202,240` (both exact, no other `_array_cls` call site
in the repo); `:50-51` `node_count`, `:133-140` `source`, `:142-168` `record_op` (with `:152`/`:159`
being the two `a.node_id` reads a `Varied` would `AttributeError` on), `:245-252`/`:268` `walk`,
`:255-286` post-order over `inputs_of`, `:291-301` partition-blind `materialize`, `:113-125`
`sourcemap`. `array.py:54` (`rint` ufunc only), `:127-128` `__slots__`, `:133-135`, `:137-143`
(`node_id`/`session` are plain properties), `:156`, `:245-275`, `:283-290` (`_form_meta`),
`:332-335` (underscore-only guard), `:344-371`/`:369-371`, `:374-391`, `:397-410`.
`numpy/array.py:71-74`, `:78,82,86,160` (all four property line numbers exact), `:92-190`,
`:132-136`. `execute.py:36-45`, `:54-58`, `:70`, `:85-91`, `:96-126`, `:104-105`, `:109`, `:110-115`,
`:116-124`, `:126`. `aggregate.py:44-55`, `:57-65`, `:68`, `:86`, `:89-93`, `:95-97`, `:101`.
`shuffle.py:5-8`, `:68`, `:84,89`, `:92-96`, `:142,155`, `:170`, `:208,220`, `:232`, and exactly four
`OpSpec.from_callable` sites at `:181,188,245,259`. `provenance.py:26-33`, `:66-79`.
`debug/errors.py:29`, `:75-78` (`__eq__` on `__dict__`), `:80-81` (hand-written `__hash__` tuple,
no `variation`); `debug/runner.py:6-7,37,57-69`; `grep "StageError("` over `python/graphed/` → exactly
2 hits. `core/plan.py:54,72-76` (`identity()` for `kind="ref"` is literally `b"ref\0" + self.ref.encode()`),
`:126`, `:164-176`, `:286-301`; `core/execution.py:206-217` (`Plan` = the seven listed fields, plain
callable `process`, no `identity()`), `:219-224` (`ExecResult.value`), `:450-457`
(`sorted(plan.tasks, key=…)`). `checkpoint/runner.py:77-91`, `:100-109`. `write.py:32-43`, `:77-79`.
`awkward/io.py:100-127` (`(out,) = evaluate_ir` at `:121`, `result = ak.Array(out)` at `:122` —
exact), `:157-185`, `:206-216` (**no `select=` parameter today**, the r18 premise for dropping
`to_parquet` from m48's table). `numpy/io.py:163-171`. `parquet.py:77`.

**Surface counts (all exact).** `dir(Array)` public =
`['filter','map','node_id','reduce','repartition','session']`; `dir(NumpyArray)` adds
`T`/`dtype`/`ndim`/`shape` for **32** public names; `graphed.awkward.functions` has **73** `def`s /
**65** public and **no `__all__`**; the package `__all__` (`awkward/__init__.py:17-31`) lists the
**six** package-level functions the plan names, and `graphed.awkward.num` raises `AttributeError`;
the m24 anti-drift pin is a **39**-name literal at `:39-79`; `graphed/__init__.py:8-25`, `__all__`
`:27-58`, `:9`, `:12`, `:44`("apply"), `:46`("compile_ir"), `:50-57`. Every gak line anchor is exact:
`join:18`, `zip:118`, `linear_fit:346`, `concatenate:383`, `where:400`, `apply_correction:476`,
`onnx_inference:513`, `unflatten:600`, `full_like:612`, `values_astype:673`, `broadcast_arrays:677`,
`unzip:687`, `to_list:693`, `fields:717`, `type_of:722`, `backend_of:727`, `head:732`, `sample:737`.
The annotation-wide discovery over `graphed.__all__` yields **exactly**
`['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`
(8), with `compile_ir(session: Session, *outputs: Any, …)` absent — the r15/r17/r18 argument for the
named floor list is confirmed, and the r18 "six refusing / two expanding" split is arithmetically right.

**graphed-histogram.** `boost.py:39-47`, `:60-71`, `:88-98`, `:100-117` (`for j in range(i, i+k)` at
`:113`, count-based `layout` at `:106`), `:120-122` (`_add_groups` is a key-wise `+`, the r18 BLOCKER
fix's premise), `:127-130`, `:146-150`, `:153-163` (positional `fill`; the arity check is `:160-161`),
`:160-178` (`sample` appended **unchecked** — exact), `:166-174`, `:175-176`, `:180-212`, `:198-212`
(params keys measured today `{"spec","n_axes","weighted","sampled"}`, `n_weights` only when
`len(weights) > 1` — §6.3 r17's literal set is correct), `:215-219`, `:245-255`, `:282`, `:283-286`.
`_spec.py:31-37`, `:68-76` (growth refusal at `:70`/`:74`), `:81-84`, `:115-122`, `:129-135`.
`tests/frozen/m29/test_multi_weight_fills.py:75-79,84-87,93-99,96`;
`tests/frozen/m23/test_group_plan.py:60-66,68-77`. `pyproject.toml:21` runtime deps, `:25-39` dev,
`:50` pythonpath; `ci.yml:44,67` run `tests/frozen` in one process; 0 `__init__.py` under `tests`;
existing `m23`/`m29`; `grep -rn corpus tests/ .github/workflows/` → **0**; repo version `0.0.1`.

**Probes re-run in-session (all reproduce the plan's numbers).**
- §3.3 / §5.2a topology, `graphed-latest@ff7c607`: N=16 → 1333 arena / 17 stages / 34 reduced;
  N=128 → 7157 / 129 / 258; **without** the terminating reduction → 18 / 130 and Δ(N=1→2) = **51**;
  **with** it Δ = **52** (= K+2). Node ratio 7157/1333 = **5.369**. Timing 3.95 ms → 23.77 ms this
  run (plan records 3.77 → 21.28); the ratio 6.02 vs the plan's 5.64 is ordinary timer noise and the
  16.0 gate still keeps ≈2.7× headroom. All the §3.3 arithmetic checks: ln24/ln8 = 1.528 ("1.53"),
  ln24/ln5.37 = 1.890 ("1.89"), 5.37² = 28.8, 28.8/24 = 1.2, 16/5.64 = 2.84, 28.8/16 = 1.8, and m4's
  `_build` really does span 8.00× nodes (1749 → 13999) against its 24.0 gate
  (`tests/frozen/core/m4/test_benchmark.py:10,28-33,40-43`). `reachable_nodes` is in `reduce()`'s
  report, so the self-scaling alternative form is buildable as claimed.
- §7.2 / m48 optimizer-merge: `nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5` → record ids `0,1,2,3`,
  `compile_ir(s, nom, m1, m2, mh)` → `outputs() == [0,1,2]`, `evaluate_ir` returns **3** values; on
  the fill path, two `Histogram.fill`s differing only in `weight=[w]` vs `weight=[w*1.0]` → fill node
  ids **2** and **4** → `outputs() == [2]`. The r18 unvaried positive control `compile_ir(s, b, b*1.0)`
  → **one** output. `compile_ir(s,b,c)` (structurally identical) → 1 value; `compile_ir(s,b,d)` → 2.
- §2.3e / m51: `a = src * 2.0; b = src * 2.0` → `a.node_id == b.node_id == 1`, `a is b` **False**,
  `node_count() == 2`.
- §7.3 / m49 cloudpickle (cloudpickle **3.1.2**, `PYTHONHASHSEED` ∈ {1,7,12345}): importable frozen
  dataclass + sorted tuple → `80e8024dc8f3b77d` ×3; + `frozenset` → 3 distinct; `__main__`-defined +
  sorted tuple → 3 distinct. §8.2(i)'s r14 triple for `(3, frozenset({…}))` reproduces **exactly**:
  `b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831`.
- boost_histogram **1.8.0**: `Traits(underflow=False, overflow=True, growth=False)`; under-declaration
  `sum 2.0` vs `sum(flow=True) 3.0`; over-declaration `3.0 == 3.0` (invisible);
  `StrCategory(name=…)` → `TypeError`; `h[{"variation": …}]` → `TypeError: list indices must be
  integers or slices, not str`; `h.axes.name` → `AttributeError: object Regular has no attribute name`
  on a two-axis histogram; per-axis `[None,'variation']` survives `spec_of`→`zero_of`;
  `h[{1: ax.index(l)}]` equals `h[{1: bh.loc(l)}]`; cross-axis `+` → `ValueError: axes have different
  length`.
- awkward **2.12.0**: `ak.broadcast_arrays` over lengths 7 and 3 → `ValueError: cannot broadcast
  RegularArray of size 3 with RegularArray of size 7` (verbatim), while a jagged 3-row value
  broadcasts; `float32 ^ float32` → `TypeError: ufunc 'bitwise_xor' not supported…` for **both**
  `np.ndarray` and `ak.Array`, while `.view(np.uint32) ^` works; `"metadata" in
  signature(ak.to_parquet)` → **False**.
- parquet (clean resolve of `awkward==2.12.0` + `pyarrow` → **25.0.1**, confirming the r14 version
  correction): `ak.to_parquet` vs `pq.write_table(ak.to_arrow_table(…))` → different bytes for
  record, list-of-float and flat numeric; KV sets exactly as the appendix row states
  (record `{ARROW:schema, ak:parameters, awkward_array_metadata}` vs `{ARROW:schema, ak:parameters}`;
  list-of-float `{…, awkward_array_metadata}` vs `{ARROW:schema}`), so `ak:parameters` is
  data-dependent and `awkward_array_metadata` is dropped by the arrow path;
  `created_by == "parquet-cpp-arrow version 25.0.1"`; two writes of one array in one process are
  byte-identical; `ak.from_parquet(path, columns=["murf_0.5"])` returns **fields `[]`, len 0** —
  silently empty.
- frontend idiom: `w[:, 1]` → `TypeError: unsupported index (slice(None, None, None), 1)` (verbatim);
  CPython **3.12.10** `**`-unpacking admits `{'0p5':…, 'murf_0.5':…, '2':…}`.
- `§1.1` e-form arithmetic all correct: `0.5`→`5em1`, `2.5`→`25em1`, `1.2345`→`12345em4`,
  `-1.5`→`m15em1`, `1e-8`→`1em8`, `"50em2"`→`5em1`, `"05"`→`5`; `"1e40"` really is 41 plain digits
  while `"1e-40"` is the 5-character `1em40`.

**Corpus & repo-layout facts.** `graphed-corpus@49650e4`: `TTBAR_FIXTURES` = 2 regions × 5 vars,
`TTGAMMA_FIXTURES` = 5 → **15** systematics references, and `corpus/references/` holds **23** JSONs
(8 ADL + 15) — so m48's "**9 of the 15**" (6 ttbar + 3 ttgamma) is right. `systematics.py:25-36`
(`_btag_weight`), `:39-45` (`ak.with_field` lockstep JES), `:60-61` (JES before the pt cut),
`:74-76` (`sel_jets = good[sel]` → central b-tag SF on JES-shifted jets — the stacking case, with
`:73` blank and `:75` the `ht` sum exactly as the appendix says), `:79,102,50` (pre-fill rounding
twice + the view round), `:91-92` (unvaried photons/muons sliced by the varied selection). The
vendored `graphed tests/_corpus/graphed_corpus/analyses/systematics.py` is **byte-identical** to the
corpus repo's, so the vendored line numbers hold. `corpus/m05/test_systematics.py` carries both
behavioural invariants including `jes_up > nominal > jes_dn`. `graphed-corpus pyproject.toml:28-30`
packages only `src/graphed_corpus`. `graphed pyproject.toml:27` (`["executing>=2.0","cloudpickle"]`),
`:29-48` extras with **no** `graphed-histogram`, `:103-130`/`pythonpath` incl. `tests/_corpus`;
`.github/workflows/ci.yml:34,57,143` install `.[dev]`; `scripts/run-tests.sh:16-25` SUITES and `:30`
`SPLIT_PKGS="frontend numpy awkward"`; `tests/frozen/checkpoint` holds only `m8`/`m39` with
`m8/test_resume.py` present; the four `importorskip` anchors (`preserve/m25:31` module-level,
`m27:185,207`, `m30:155`) and `debug/m6/test_process_boundary.py:7,16` are exact;
`frontend/m40/test_noninner_null_key_option.py:30` really does `from graphed.awkward import …`.
`graphed-executors@201ea42`: `submit/engine.py:381-396`, `pyproject.toml:20-35` (no histogram dep),
`pythonpath` `:54`, env `ci.yml:13,15,17` (GRAPHED + CORPUS only), installs at `:38,65,94,136`,
frozen runs at `:44,67,101,153`, 0 `__init__.py`, **15** milestone dirs. `uproot5-graphed@393ecef`:
**12** flat `test_graphed_*.py` + the 2 helper modules, **zero** `tests/frozen` references repo-wide,
`_graphed_write.py:59-64` copies branches with **zero** `compile_ir`/`evaluate_ir` hits;
`behaviors/RNTuple.py:1560-1562` (exact-first lookup), `:1564-1569` (dot-split), `:562,567`
(`to_akform` splits on `.`); `writing/_cascadetree.py:1606` (`.` nesting join);
`behaviors/TBranch.py:2015-2017,2019-2024` (exact-first, `/`-split only).

**Prior art.** `ewkcoffea@063e8d7 analysis/wwz/wwz4l.py:396-397` (the impact-partitioned Weights
comment) and `:1204-1207` (the nominal-only exclusion rule) are both at the cited lines.
`ewkcoffea@63abb06`: `hout = {}` at `:807` **inside** the shift loop with `return hout` at `:892`
**outside** it, `masked_val_cache`/`masked_weights_cache` at `:808-809`,
`obj_correction_systs = []  # Will have e.g. jes etc` at `:331`, and `run_wwz4l.py:259-261` is
literally `# Does not work` above a commented `cloudpickle.dump`; `run_wwz4l.py:302-313` is the timing
block. `FNALLPC/wwz4l@cc71718`: `:395-400` is the populated `obj_correction_systs`, the processor is
**764** lines, and `grep dataset_tools|hist.dask|import dask` over `analysis/` → **0**. coffea
@`f34b8bdf`: `jetmet_tools/CorrectedJetsFactory.py:36-47` seeds PCG64 from the input array's own
bytes; `:64-95` takes ONE `jet_resolution_rand_gauss` while `jersf = …[:, variation]` varies per
label, with a signed `deltaPtRel` and a signed-gaussian stochastic branch (non-monotone by
construction).

**Research-doc citations.** Every cited section exists and says what the plan says: lit §rdf-vary
§1-§6 (§6 is "Naming vocabulary (exact)"), §rdf-users §1-§5, §coffea-sys §1-§5,
§pythonic-analyses, §ewkcoffea-confirmed (incl. the wwz4l addendum); cba §ir-rust §1, §frontend-python,
§histogram §1-§3, §optimizer §1-§5, §exec-checkpoint, §corpus §1-§5. Spot-checked in detail:
- lit `:236` really does carry the "read via summarizing fetch … UNVERIFIED at word level" caveat on
  the coffea #469 "~2-3× … up to ~7-8×" numbers — the plan's caveated citation is honest.
- "12 bases → 24 labels" (lit `:411`), "6 object-shift labels" (`:413`), the 7-pass loop (`:421`),
  "**522** identical processor lines" (`:545`), "byte-identical `ApplyJetSystematics`" (`:549`),
  "54→14 categories" (`:549,564`), and wwz4l's "**27** labels = 1 + 20 + 6" (`:555`) are all present
  and arithmetically consistent.
- cba §optimizer §2's table (N=16 → 1333 / 3.1 ms / 34 / 17; N=128 → 7157 / 16.7 ms / 258 / 129) and
  its Δ = 52 line match my re-measurement. The plan's Part I §3 "12.9× nodes → 11.9× time" is the
  cba's **N=1→128** span (arena at N=1 is 553; 7157/553 = 12.94), not §3.3's N=16→128 span — worth a
  parenthetical in a future revision, but not an error.
- cba §histogram §1 does scope its "no constant-Array constructor" grep to the session/array modules,
  exactly as §4.1 r12 says when correcting it; §4.1's replacement facts
  (`numpy/creation.py:27-28,31-75`, one-source binding at `aggregate.py:57-63,96-101`, the
  `"no data bound for source"` raise at `execute.py:104-105`) are all verified.
- worklog `:181-187` records the §6.4c compression probe with its methodology (float32, 1M elements,
  zlib-6, seed 42) and the exact numbers the plan quotes: raw 3.551 MB, ratio 2.883 (not bit-exact),
  XOR 3.280, masks 798 KB → 169 KB (**4.7×**).

---

## Verdict

**DIRTY** — 1 BLOCKER, 1 HIGH, 2 LOW, 1 NIT-bundle.

The factual substrate of r18 is, with two exceptions, in unusually good shape: I opened every anchor
in the Anchors appendix and the overwhelming majority of the in-body `file:line` citations, re-ran
every cheap probe the plan claims, and re-verified the prior-art and research-doc citations. The
Rust-side anchors, the five-chokepoint claim, the surface counts (65 gak functions, the 8-verb
annotation-wide discovery, the 39-name m24 pin, `dir(Array)`/`dir(NumpyArray)`), the topology
integers (`stages == N+1`, `reduced == 2N+2`, Δ = 52/51), the cloudpickle seed digests, the parquet
KV/`created_by` measurements, and every §3.3 arithmetic step reproduce **exactly**. The r18
line-number correction to the root prompt (`:1286-1287`) is right, and the r18 claim that
`to_parquet` has no `select=` parameter today is right.

The two real defects are both **new in r18** and both sit on frozen anchors:

1. the property-discovery rule (§2.2/§2.3a/m48) generalises a true statement about
   `shape`/`dtype`/`ndim` to `T`, which is a recorded `transpose` op — making the binding rule
   self-contradictory with §2.3a's own *broadcast* disposition for `transpose` and making the m48
   property-half anchor red against a correct implementation (BLOCKER);
2. m49's image-cardinality clause asserts N+1 where the measured image is 2N+2 (HIGH).

Both are one-sentence repairs with the corrected quantity supplied above. The remaining items are
citation hygiene only.
