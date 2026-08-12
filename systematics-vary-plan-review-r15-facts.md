# systematics-vary-plan review — round 7, FACTS / HALLUCINATION lens

- **Plan revision reviewed:** r15 (`systematics-vary-plan.md`, 3171 lines)
- **Lens:** facts / hallucination audit — every `file:line` anchor in the body and the Anchors
  appendix, every "measured/verified/re-measured" claim, citations into the two research companions,
  prior-art claims, and arithmetic/counts.
- **Date:** 2026-07-30
- **Reviewer discipline:** R0.11 — nothing below is asserted that I did not open or run myself in
  this session. Anchors I verified and found correct are listed in the closing inventory so the
  record shows what was checked, not only what failed.

## Verification roots used (revisions confirmed by `git log -1` in-session)

| Root | Revision | Plan's cited revision | Match |
|---|---|---|---|
| `/private/tmp/claude-501/graphed-latest` | `ff7c607a8ba6…` | `ff7c607` | ✅ |
| `/private/tmp/claude-501/graphed-exec-check` (graphed-executors) | `201ea4231b8e…` | `201ea42` | ✅ |
| `/private/tmp/claude-501/graphed-histogram-latest` | `211cbbe22497…` | `211cbbe` | ✅ |
| `/private/tmp/claude-501/uproot5-graphed` | `393ecefee80a…` | `393ecef` | ✅ |
| `/private/tmp/claude-501/graphed-corpus-latest` | `49650e4a6282…` | `49650e4` | ✅ |
| `/private/tmp/claude-501/prior-art/ewkcoffea` | `063e8d7dab4b…` | `063e8d7` | ✅ |
| `/private/tmp/claude-501/prior-art/ewkcoffea-coffea2023` | `63abb064b01a…` | `63abb06` | ✅ |
| `/private/tmp/claude-501/prior-art/wwz4l` | `cc71718a1b9f…` | `cc71718` | ✅ |
| `/Users/lgray/vibe-coding/coffea-workdir` | `f34b8bdf2bdf…` | `f34b8bdf` | ✅ |

Probe environments: `graphed-latest/.venv` (awkward 2.12.0), `graphed-histogram-latest/.venv`
(boost_histogram 1.8.0), a clean `uv run --no-project --with "awkward>=2.12" --with pyarrow`
(resolved awkward 2.12.0 / pyarrow 25.0.1), `uv run --with cloudpickle==3.1.2`.

---

## Findings

Ordered by severity. **No BLOCKER, HIGH, or MID finding survived verification.** All four surviving
findings are LOW/NIT — stale or dangling pointers and two imprecise rationale sentences. None
changes a binding requirement.

### 1. LOW — `python/graphed/__init__.py:12,44` is stale for `compile_ir` (`:44` is `"apply"`)

**Section:** §2.3d (plan `:567`) and Anchors appendix row *"The ANNOTATION-WIDE filter still misses
`compile_ir` …"* (plan `:2705`).

**Detail.** Both places substantiate the r15 headline finding — that `compile_ir` IS in
`graphed.__all__` while the annotation-wide filter misses it — with `python/graphed/__init__.py:12,44`.
Line 12 is correct (`from .execute import CompiledGraph, compile_ir, evaluate_ir`). Line 44 is not:
it is the `"apply"` entry. `"compile_ir"` is at **`:46`**.

**Evidence (measured):**
```
$ grep -n '"compile_ir"\|"apply"\|"aggregate_plan"' python/graphed/__init__.py
43:    "aggregate_plan",
44:    "apply",
46:    "compile_ir",
```
The substantive claim behind the pointer is *true and independently reproduced*: re-running the r15
probe in `graphed-latest/.venv` gives exactly
`['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`
(8), with `compile_ir(session: 'Session', *outputs: 'Any', …)` absent and `inspect.isfunction`
True — an exact reproduction of the r15 row.

**Suggested fix.** Replace `python/graphed/__init__.py:12,44` with `:12,46` in both places.

---

### 2. LOW — the Anchors appendix still carries the `projection.py:109-121` pointer that r15's own revision history records as corrected

**Section:** Anchors appendix row *"A `frozenset` field in the worker closure makes the serialized
plan seed-dependent …"* (plan `:2694`).

**Detail.** r15's revision-history LOW block states: *"line-number corrections — …
`projection.py:109-121`→`:147`"*, and §8.2(i) in the body (plan `:1723`) carries the corrected form
("`return tuple(sorted(needed))`, `projection.py:147` (the whole function is `:109-147`; the r13/r14
`:109-121` pointer landed on the docstring, corrected r15)"). The appendix row was not updated: it
still reads *"the house discipline is `read_columns`' SORTED read set (`projection.py:109-121`)"*.
The document therefore disagrees with itself on a pointer it explicitly claims to have fixed.

**Evidence (measured, `graphed-latest`):** `read_columns` is defined at `projection.py:109`; lines
110–121 are its docstring; `return tuple(sorted(needed))` is at `:147` (function span `:109-147`).
Verified by reading `sed -n '105,150p' python/graphed/projection.py`.

**Suggested fix.** In the appendix row, change `projection.py:109-121` → `projection.py:147`.

---

### 3. LOW — dangling `(:590-592)` citation in §6.4a(2a); it resolves to nothing

**Section:** §6.4a, predicate (2a) absent-operand clause (plan `:1451`).

**Detail.** The r15 text reads: *"(2a) was stated purely in lineage terms while §2.3e's drop rule
yields context-free results (`:590-592`) …"*. The bare `:590-592` names no file, and by this
document's convention a bare line span continues the last-named file — but no file is named anywhere
in that clause or the surrounding sentences of §6.4a. Read as a plan-internal self-reference it is
also wrong: §2.3e's drop rule is at plan line **640** ("**Drop rule**: an op that cannot propagate a
handle (no contexted input) yields a context-free result…"), while plan lines 590–592 are §2.3e's
`__slots__` / `graphed.context_of` binding. No source file in the verification roots has a relevant
`:590-592` either (`array.py` is 412 lines; `session.py` ends well before; `boost.py:590` does not
exist).

**Evidence (measured):** `grep -n "Drop rule" systematics-vary-plan.md` → `640:`; `sed -n '588,594p'`
of the plan shows the `__slots__`/`context_of` text.

**Suggested fix.** Drop the parenthetical, or replace it with the section reference the rest of the
document uses (`§2.3e`, "Drop rule").

---

### 4. LOW — §2.3c's "an `__all__`-driven test would discover nothing" is measurably wrong; it would discover a WRONG set of six

**Section:** §2.3c, the discovery-rule rationale (plan `:494-500`).

**Detail.** The plan says: *"the package `__all__` lists modules/classes, not gak's functions
(`python/graphed/awkward/__init__.py:17-31`), so an `__all__`-driven test would discover nothing and
assert nothing."* Both halves are imprecise. `graphed.awkward.__all__` lists **six package-level
functions** alongside the modules/classes, so an `__all__`-driven gate discovers a *wrong* six-name
set rather than an empty one — which matters because the plan's own non-vacuity floor tests
"non-empty and ≥ the freeze-time count", a condition a wrong-but-non-empty set can satisfy.

**Evidence (measured, `graphed-latest/.venv`):**
```
>>> [n for n in graphed.awkward.__all__ if inspect.isfunction(getattr(graphed.awkward, n))]
['from_awkward', 'from_parquet', 'project', 'project_buffers', 'read_parquet_partition', 'to_parquet']
```
`__all__` is at `python/graphed/awkward/__init__.py:17-31` as cited ✅, and it contains
`AwkwardBackend`, `AwkwardForm`, `from_awkward`, `from_parquet`, `functions`, `gak`, `io`,
`payloads`, `project`, `project_buffers`, `read_parquet_partition`, `shuffle`, `to_parquet`.

The *binding* consequences are unaffected and in fact strengthened: the plan already binds the
discovery rule to `inspect.getmembers(graphed.awkward.functions, inspect.isfunction)` filtered on
`__module__` (r15's own correction, which I reproduced: the alias discovers **0**, the module
discovers **65** — both exact), and already requires a per-class membership floor.

**Suggested fix.** Rewrite as: *"the package `__all__` lists modules, classes and six package-level
functions — none of them gak's (`python/graphed/awkward/__init__.py:17-31`), so an `__all__`-driven
test over `graphed.awkward` discovers a wrong six-name set, which a bare non-emptiness floor would
not catch."*

---

### 5. NIT — §6.4a's `numpy/io.py:158-173` points at `_WritePart.__call__`, not at the numpy `to_parquet`

**Section:** §6.4a (plan `:1380`).

**Detail.** The sentence *"the numpy idiom having its own 1-D-capped implementation,
`python/graphed/numpy/io.py:158-173`"* cites a span inside `_WritePart.__call__`. The numpy-idiom
`to_parquet` function is defined at `numpy/io.py:182`. The cited span does contain the actual cap
(`if result.ndim != 1: raise TypeError(...)` at `:164-165`), so the claim is true; only the framing
("its own … implementation") points at the wrong construct. The Anchors appendix row for the same
fact (`numpy/io.py:163-171`) is precise.

**Evidence (measured):** `grep -n "^def \|^class " python/graphed/numpy/io.py` → `136:class
_WritePart:`, `175:def _memory_step`, `182:def to_parquet(`.

**Suggested fix.** Cite `python/graphed/numpy/io.py:182` (the function) together with `:163-171`
(the cap).

---

### 6. NIT — Part I §2's quoted exemplar comment is not verbatim

**Section:** Part I §2 (plan `:114-115`), Anchors row `ewkcoffea@063e8d7 … wwz4l.py:…396-397`.

**Detail.** The plan quotes *"these weights can go outside the sys loop since they do not depend on
pt of mu or jets"*. The source reads *"These weights can go outside of the **outside** sys loop
since they do not depend on pt of mu or jets"* (`ewkcoffea@063e8d7 analysis/wwz/wwz4l.py:396`). The
litsearch companion quotes it correctly; the plan's paraphrase sits inside quotation marks. Part I is
explicitly non-binding, and the meaning is preserved.

**Evidence (measured):** `sed -n '396,399p' analysis/wwz/wwz4l.py` in the `ewkcoffea` clone.

**Suggested fix.** Restore the verbatim wording or drop the quotation marks.

---

## What I verified and found CORRECT (inventory, so the record shows the coverage)

Everything below was opened at the cited lines or re-run as a probe. This is not a summary of the
plan's claims — it is a list of claims I personally confirmed.

**Frontend / `graphed` source anchors — all exact:**
`array.py` `:54` (`rint` ufunc-only), `:127-128` (`__slots__`), `:137-143` (`node_id`/`session` as
plain properties), `:156` (`__array_ufunc__`), `:245-275` (bitwise dunders), `:332-335`
(`__getattr__` underscore guard → recorded `field` op for ANY non-underscore name), `:344-371`
(`__getitem__` accepts Array/str/list/slice/int, TypeErrors otherwise, final raise at `:369-371`),
`:374-375` (`filter`, no runtime check), `:377-379` (`map`), `:374-391` (the four public methods),
`:397-410` (`graphed.apply`). `session.py` `:30` (`_provenance`), `:39` (`_array_cls`), `:50-51`
(`node_count`), `:113-125` (`sourcemap`), and **all five** `_array_cls` return sites `:140/:168/:183/
:204/:242` with **no call site outside `session.py`** (grep-verified); `:152,159` (the two
`a.node_id` reads a `Varied` would die on); `:245-252` (`walk` signature) and `root = array.node_id`
at **`:268`** (r15's correction from `:269` is right). `execute.py` `:36-45` (`CompiledGraph` carries
**only** `ir` + `source_names`), `:54-58`, `:70`, `:85-91` (`evaluate_ir` takes no `Array`),
`:99-126` (bare dispatch loop, **no** `try`/`except`, op dispatch `:109`, stage members `:110-115`,
external dispatch by `descriptor.content_hash` `:116-124`, `:126` returns one value per DISTINCT
output), `:104-105` ("no data bound for source"). `aggregate.py` `:44-55`, `:57-65`, `:68-77`, `:86`,
`:89-93`, `:95-97`, `:101`. `projection.py` `:109`, `:147`. `shuffle.py` `:5-8`, `:84`, `:89`,
`:92-96`, `:142`, `:155`, **`:170` (first exchange)**, `:208`, `:220`, **`:232` (first join)**.
`provenance.py` `:26-33`, `:66-79`. `debug/errors.py` `:29`, `:32-81`, `:75-78` (`__eq__` is
`__dict__`-based, `:78` the compare), `:80-81` (`__hash__` is a hand-written tuple — the new field
does NOT ride free). `errors.py` (`GraphedError(Exception)`, unrelated to `NotImplementedError`).
`debug/runner.py` `:6-7`, `:37`, `:57-69`. `core/plan.py` `:72-77`, `:164-176`, `:286-301`.
`checkpoint/runner.py` `:100-109`; `checkpoint/store.py` `:31-41`, `:62-73`. `awkward/io.py`
`:111-127` (with `(out,) = evaluate_ir(...)` at **`:121`** and `result = ak.Array(out)` at `:122`),
`:157-185`, `:206-216`, `:239`, `:260`, `:274`. `write.py` `:32-43`, `:77-79`. `numpy/array.py`
`:71-74`, `:132-136`, and **exactly 25** `def`s in `:92-190` (every method the plan names —
`sum prod mean std var min max any all argmin argmax cumsum cumprod reshape ravel squeeze transpose
swapaxes astype clip round take` — is present). `numpy/creation.py` `:27-28`, `:31-75`;
`numpy/__init__.py:578-598`. `parquet.py:77` + **zero** `key_value_metadata`/`with_metadata` hits
repo-wide.

**gak surface:** `functions.py` has **73** `def`s / **65** public and **no `__all__`** — all three
counts exact; every named function line verified: `join:18`, `zip:118`, `linear_fit:346`,
`concatenate:383`, `where:400`, `apply_correction:476`, `onnx_inference:513`, `unflatten:600`,
`full_like:612`, `values_astype:673`, `broadcast_arrays:677`, `unzip:687`, `to_list:693`,
`fields:717`, `type_of:722`, `backend_of:727`, `head:732`, `sample:737`. The r15 discovery claim
reproduced exactly: the **alias** `graphed.awkward` discovers **0**, the **module**
`graphed.awkward.functions` discovers **65**, `graphed.awkward.num` → `AttributeError`.

**Rust anchors:** `store.rs:73-88` (`intern`), `:147-156` / `:152-153` (`mark_output` de-dup);
`node.rs:39-41`, `:102-103` (`is_boundary = !Op`); `optimizer/engine.rs:7-13` (the O(N) extractor
note naming "the deep chains a systematics graph produces"), `:54-56`; `optimizer/mod.rs:1-11`,
`:88-116` (the `remap` vector, never returned). `src/lib.rs`: **exactly three** `#[pymethods]` blocks
at `:102`, `:159` (GraphStore, closing `:416`) and `:470`, and the GraphStore method list matches the
plan's enumeration **name for name** — no record→reduced id mapping is exposed.

**graphed-histogram anchors:** `boost.py` `:39-47` (`_flat`), `:60-71` (weight product after
independent flatten), `:88-98` (`_SumFills`), `:100-117` (`_GroupReduce`, `for j in range(i, i+k)`),
`:120-122` (`_add_groups` key-wise `+`), `:127-130` (`_GroupZero`), `:146-150` (`self._spec` fixed in
`__init__`), `:153-163` (positional `fill`), `:160-161` (one array per axis), `:160-178`
(**`sample` appended with NO isinstance check** — the r15 `sample=` finding is real), `:166-174`,
`:180-212` (`chash = content_hash(self._spec)`, `PayloadDescriptor`, `self._evaluators[chash]`),
`:215-216`/`:218-219` (`staged_fills`/unlabeled `fill_nodes`), `:245-255` (`Histogram.plan` passes
the `__init__`-time spec), `:255-292` (`layout` built at `:282` from `(output_name, Histogram)`
pairs — the key IS the output name today), `:283-286` (`evaluators.update`). `_spec.py` `:31-37`,
`:70`/`:74` (growth refusal), `:81-84`, `:115-122`, `:129-135`. `pyproject.toml` `:21` runtime /
`:25-39` dev (**r15's correction verified exactly**) / `:50` pythonpath; `ci.yml` `:13-17` (GRAPHED +
EXECLOCAL only), `:44`, `:67`; **0** `__init__.py` under `tests`; **0** corpus hits.

**graphed-executors:** `submit/engine.py:381-396` (translate-only); `pyproject.toml:20-35` (no
`graphed-histogram`); `pythonpath` `:54`; `ci.yml` env `:13,15,17` (GRAPHED + CORPUS only), installs
`:38,65,94,136`, frozen runs `:44,67,101,153`; **15** existing milestone directories; **0**
`__init__.py`. `tests/frozen/m7/analyses.py:118-127`, `m7/adl.py:124-158`.

**uproot fork @ 393ecef:** `behaviors/RNTuple.py:1560-1562` (exact-first lookup), `:1564-1569`
(dot-split fallback), `:562,567` (inside `to_akform`, def at `:505`); `writing/_cascadetree.py:1606`
(`field_name + "." + subfield_name`); `behaviors/TBranch.py:2015-2017` / `:2019-2024` (`/`-split,
never `.`); `writing/_graphed_write.py:59-64` with **zero** `compile_ir`/`evaluate_ir` hits;
**12** flat `tests/test_graphed_*.py` + the two helper modules; **no** frozen dir and **zero**
`tests/frozen` strings repo-wide.

**Corpus:** `systematics.py` (112 lines) `:25-36` (`_btag_weight`), `:39-45` (`ak.with_field` JES),
`:50` (`_round_hist`), `:60-61` (JES before the pt cut), `:74-76` (`sel_jets = good[sel]` then the
**central** b-tag SF), `:79` and `:102` (pre-fill `np.round(..., STABLE_DECIMALS)`), `:91-92`
(unvaried photons sliced by the JES-varied selection — exact); `histograms.py` `STABLE_DECIMALS=6`,
`bin_values`, `fingerprint`; `corpus/references/` = **23** JSONs of which **15** are systematics, and
the nine m48 files (`ttbar_4j{1,2}b_{nominal,btag_up,btag_down}`, `ttgamma_{nominal,pho_up,pho_down}`)
all exist — the "**9 of the 15 refs**" arithmetic is correct; `pyproject.toml:28-30` packages only
`src/graphed_corpus`; `docs/requirements/ops_catalog.md:75` is exactly the
"Systematics-as-a-graph-axis … cf. RDataFrame `Vary`" row; `tests/frozen/m05/test_catalog.py` is
**text-presence-only** (every assertion is an `in text` substring check plus
`len(all_fixtures()) == 23`), so §12.3(d)'s un-park claim holds.

**graphed frozen tree:** `core/m4/test_systematics.py:28-53` (the <1 s / 10⁴-node / variation-count-
independent contract), `core/m4/test_benchmark.py:10,28-33,40-53` (built with raw
`import graphed.core as gc` — the r15 §5.2c/§5.2a surface correction is grounded);
`corpus/m05/test_systematics.py:26-38` (`jes_up > nominal > jes_down`, `btag_up == nominal ==
btag_down`) and `m05/test_fixtures_reproduce.py:34-35` (the exact
`bin_values`/`fingerprint` comparison form); `preserve/m9/agc.py:38-66`, `:56-62`, `:94-118`,
`:106-107`; `preserve/m9/test_reproduce.py:19-23`; `checkpoint/m8/test_resume.py:51-58` +
`analyses.py:29-30` (**int64** counts — the r15 §5.5a argument is grounded);
`core/m40/test_join_serialize.py:84-99` (literal `b"GIR1\x03…"`);
`awkward/m24/test_interface_parity.py:39-79` — a **39**-name literal, counted exactly — and `:74-76`
(`full_like`); `debug/m6/test_process_boundary.py:7,16` and `m6/analyses.py:52-56`; the importorskip
house pattern at `m25:31`, `m27:185,207`, `m30:155`; `preserve/bundle.py:103-123`, `:206-210`;
`pyproject.toml:42-48` (dev, no `graphed-corpus`) and the pytest block `:103-130`; `run-tests.sh:16-25`
(SUITES) and `:30` (`SPLIT_PKGS="frontend numpy awkward"` — `core` and `preserve` really are one
process each); CI `.[dev]` at `:34,57,143`; **no `__init__.py` under `tests/frozen`** (the only two in
`tests/` are the vendored `tests/_corpus/graphed_corpus` packages); `tests/_corpus/references` = 23
JSONs; `tests/frozen/checkpoint` holds only `m8`/`m39`; the **only** cross-process frozen test is the
M6 pool; `graphed` ships `Executor` only as a Protocol.

**Re-run probes — every one reproduced the plan's stated result exactly:**
- Interning: recording `src * 2.0` twice returns node id **1** both times, `node_count()` stays **2**.
- Output dedup: `compile_ir` over two structurally identical outputs evaluates to **1** value; over
  two distinct outputs, **2**.
- §3.3/§5.2a shape (D=500, K=50): with the terminating reduction N=16 → **stages 17 / reduced 34**,
  N=128 → **129 / 258**, Δ(N=1→2) = **52**; without it, 17/18 and 129/130, Δ = **51**. All five
  literals exact.
- Anti-quadratic headroom: cba §optimizer §2's table is internally consistent (N=1 → 553 nodes /
  1.4 ms, N=128 → 7157 / 16.7 ms ⇒ 12.9× nodes, 11.9× time; 16.7/3.1 ≈ 5.4 against the 24.0 gate),
  and my own N=16 build reproduces the table's 1333-node row.
- `Array` tuple subscript: `w[:, 1]` → `TypeError: unsupported index (slice(None, None, None), 1); …`
  (verbatim); `gak.firsts(w[gak.local_index(w) == 1])` over `[[1,2,3],[4,5,6]]` materializes
  `[2.0, 5.0]`.
- boost_histogram **1.8.0**: `StrCategory(name=…)` → `TypeError`; `Traits(underflow=False,
  overflow=True, growth=False, …)`; under-declaration `sum 2.0` / `flow 3.0`; over-declaration
  `sum == flow == 3.0`; `h[{"variation": …}]` and `h[{"variation": bh.loc(…)}]` both →
  `TypeError: list indices must be integers or slices, not str`; positional index works;
  `h.axes.name` → `AttributeError: object Regular has no attribute name` on a two-axis histogram;
  `[a.__dict__.get("name") for a in h.axes] == [None, 'variation']` and it survives
  `spec_of` → `zero_of`; cross-axis addition → `ValueError: axes have different length`.
- awkward 2.12.0: `ak.broadcast_arrays` lengths 7 vs 3 → `ValueError: cannot broadcast RegularArray
  of size 3 with RegularArray of size 7` (verbatim), jagged case fine; `float32 ^ float32` →
  `TypeError: ufunc 'bitwise_xor' not supported …` for **both** `np.ndarray` and `ak.Array`;
  `a.view(np.uint32) ^ b.view(np.uint32)` works; `"metadata" in signature(ak.to_parquet)` → **False**.
- Clean resolve of `awkward>=2.12` + `pyarrow` gives **pyarrow 25.0.1** (r14's version correction is
  right); `created_by` = `parquet-cpp-arrow version 25.0.1`; two writes of one array in one process
  are byte-identical; `ak.from_parquet(columns=["murf_0.5"])` returns **0 rows / no fields** while the
  p-form name reads back fine; `ak.to_parquet` vs `pq.write_table` differ in bytes for **all three**
  probed arrays, and the file-level KV sets match the appendix **exactly**: record
  `{ARROW:schema, ak:parameters, awkward_array_metadata}` vs `{ARROW:schema, ak:parameters}`;
  list-of-float and flat numeric `{ARROW:schema, awkward_array_metadata}` vs `{ARROW:schema}`.
- cloudpickle **3.1.2**, payload `(3, frozenset({...}))` under `PYTHONHASHSEED` 1 / 7 / 12345 →
  sha256[:16] **`b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831`** — the r14 triple
  reproduced digit for digit.
- `graphed-histogram` on PyPI: name `graphed-histogram`, version **`0.0.1`**, and the repo's own
  `pyproject.toml` version is also `0.0.1` (m49(ii)'s git-URL argument stands).

**Companion-doc citations:** litsearch `:236` does carry the word-level UNVERIFIED caveat for coffea
Discussion #469's ~2-3× / ~7-8× figures, exactly as §Part I 2 says; lit §rdf-vary §5 does carry the
arXiv:2212.04889 "largest pain point" quote; lit §ewkcoffea-confirmed does say 12 bases → 24 labels,
6 object-shift labels, 7 shift passes, and the impact-partitioned Weights; cba §optimizer §2 does
record the measurements the plan cites (and the plan's own warning that the cba's letter `D` means
the chain length, not the prefix, is correct and necessary). Worklog `:181-187` records the
compression probe with methodology (float32, 1M elems, zlib-6, seed 42) and the numbers the plan
quotes (raw 3.551 MB / ratio 2.883 / delta 3.193 / XOR 3.280; masks 798 KB → 169 KB ≈ 4.7×) —
consistent, and the ×4.7 arithmetic checks.

**Prior art:** `ewkcoffea@063e8d7 wwz4l.py:1204-1207` is exactly the nominal-only exclusion rule;
`:396-397` is the impact-partitioning comment (see NIT 6 for the quote wording).
`ewkcoffea@63abb06 wwz4l.py:808-865` is the hand-written `masked_val_cache`/`masked_weights_cache`
CSE with `hout = {}` at `:807`; `run_wwz4l.py:259-261` is `# Does not work` above the commented
`cloudpickle.dump`; `:302-313` is the build-vs-compute timing block; and the dask-era
`obj_correction_systs = []` at `:331` confirms the "no dask-era object shift" finding.
`FNALLPC/wwz4l@cc71718 analysis_processor.py:395-400` and `:711-718` are as cited, its
`ApplyJetSystematics` is byte-identical to `ewkcoffea`'s (md5 match), and the repo has **zero**
dask/`dataset_tools`/`hist.dask` surface.
`coffea@f34b8bdf CorrectedJetsFactory.py:36-47` seeds `PCG64` from the input array's own bytes, and
`:64-95` takes ONE `jet_resolution_rand_gauss` while `jersf = …[:, variation]` varies per label, with
`deltaPtRel` signed and `stochSmear` scaling a signed gaussian — the non-monotonicity argument is
grounded in the code.

**Arithmetic and counts, all correct:** 9 of 15 refs; 23 total reference JSONs; 12 weight bases → 24
labels; 27 labels for `wwz4l` (1 + 20 + 6); 104 non-nominal ambient weight labels on the §2.6 sketch
(2 pu + 102 pdf); `1 + |S| + |W|` vs `1 + |S|` internally consistent between §6.1b and §6.2; 1 vs
`N+1` combine-payload entries consistent with §6.1c's key shape; the e-form renderings
(`0.5`→`5em1`, `2.5`→`25em1`, `1.2345`→`12345em4`, `-1.5`→`m15em1`, `1e-8`→`1em8`, `50em2`→`5em1`,
`05`→`5`) are all exact; `1e40` is 41 plain digits and `1em40` is 5 characters; `16.7/3.1 ≈ 5.4`;
`798/169 ≈ 4.7`; 39-name m24 literal; 65 public gak functions; 25 numpy-idiom methods; 5
`_array_cls` call sites; 3 `#[pymethods]` blocks; 15 executors milestone dirs; 12 uproot graphed
test files.

**Root prompt:** `:25` carries the "tens of thousands" sentence; `:1262` (R22.0) and `:1282` (R22.10)
both carry the inline "systematics-as-a-graph-axis stays Phase 2"; `:1284` is the Out-of-scope header
and `:1286` begins the "treating systematic variations as a graph axis" bullet — all four exact.
R0.4a `:147`, R0.5 `:175`, R0.10a `:203`, R0.11 `:216`, R17.0 `:842` all exist as cited.

---

## Verdict

**CLEAN for this lens.** Zero BLOCKER, zero HIGH, zero MID. Four LOW and two NIT findings, all of
them pointer hygiene or rationale phrasing; none touches a binding requirement, an anchor's meaning,
or a milestone's implementability.

This is the strongest factual substrate I have audited in this plan's review chain. Of roughly 120
distinct `file:line` anchors opened and ~20 probes re-run, every measured claim reproduced —
including the ones that are easiest to get wrong: the five `_array_cls` chokepoints, the exact
`stages == N+1` / `reduced == 2N+2` / `Δ = 52` integers under *both* topologies, the three
`PYTHONHASHSEED` cloudpickle digests reproduced digit for digit, the parquet KV sets per array kind,
the `h.axes.name` two-axis `AttributeError`, and the r15 headline measurement that the
annotation-wide `graphed.__all__` filter discovers exactly eight verbs and misses `compile_ir`.

The only systematic weakness worth naming for future rounds is pointer *maintenance*, not pointer
*accuracy*: finding 2 shows a correction landing in the body while the Anchors appendix keeps the old
value, and finding 3 shows a citation surviving a revision that moved what it pointed at. A mechanical
pass that resolves every `file:line` in the appendix against the pinned roots before each revision
ships would close that class entirely.
