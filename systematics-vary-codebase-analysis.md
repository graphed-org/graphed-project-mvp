# Systematics-vary codebase analysis (agent fan-out, 2026-07-28)

Source: workflow wf_e7666c8a-794, 6 repo readers over fresh clones (graphed-latest @ ff7c607, graphed-exec-check @ 201ea42, graphed-histogram-latest @ 211cbbe).
Every claim carries file:line evidence per agent instructions; UNVERIFIED items are labeled.

ERRATUM (review r0, facts lens): §frontend-python §4 cites "`join_plan` takes the first join node
(`shuffle.py:233`)" — the first-join `next(...)` call is actually at `shuffle.py:232` (line 233 is
the unrelated `how=` read). The fact itself is correct; the line number is off by one. Reports below
are otherwise verbatim agent output.



---

# [ir-rust]

# Recipe: adding a new IR node kind to graphed (Exchange/Join as template)

All paths relative to `/private/tmp/claude-501/graphed-latest`. Template commits: M39 Exchange `530992f` ("Exchange IR variant + T_EXCHANGE codec"), M40 Join `4bc452e` ("Join IR + JoinBackend"), follow-up `1f45527` ("add missing NodeKey::Join arm to the optimizer test interpreter (E0004)") — all from `git log --oneline`.

## VERIFIED FACTS

### 1. Node-kind representation + full registration checklist

`NodeKey` is a plain Rust enum whose derived `Eq + Hash` **is** the interning identity: "The structural identity of a node. Equality/Hash here define interning." (`src/node.rs:39-41`, `#[derive(Clone, Debug, PartialEq, Eq, Hash)]` at :40). Current variants (`src/node.rs:41-84`): `Source{name,params}`, `Op{name,params,inputs}`, `Reduction{name,params,inputs}`, `External{descriptor,params,inputs}`, `Stage{inputs,members}`, `Exchange{scheme,inputs}` (:71-74), `Join{scheme,inputs}` (:80-84). Exchange/Join carry **no name** — their `scheme: ParamMap` + ordered inputs are the whole identity (doc comments `src/node.rs:66-70, 75-79`).

The M40 diff (`git show 4bc452e -- src/*.rs`) is the exact checklist. A new kind must touch:

| Where | What | HEAD file:line |
|---|---|---|
| `src/node.rs` enum | add variant | :41-84 |
| `node.rs::inputs()` | add to the or-pattern | :88-97 (Join at :96) |
| `node.rs::is_boundary()` | usually **nothing** — `!matches!(self, NodeKey::Op{..})`, every non-Op is a boundary automatically | :102-103 |
| `node.rs::token()` | add arm; prefix decides boundary-ness in the engine | :109-140 (Join `"join"` at :138) |
| `node.rs::with_inputs()` | add arm (rebuild with fresh inputs, preserves input order) | :144-179 (Join :175-178) |
| `node.rs::label()` | add display arm (to_dot/debug) | :183-215 (Join :212) |
| `node.rs` unit tests | boundary/label/display coverage | :293-360 |
| `src/store.rs` | `add_<kind>()` → `self.intern(NodeKey::…)`; interning itself is generic | `add_join` :143-146; `intern` :73-88 |
| `src/serialize.rs` | new `T_<KIND>` const **appended** + serialize arm + deserialize arm | `T_JOIN: u8 = 6` :30; serialize arm :180-184; deserialize arm :354-358 |
| `src/lib.rs` (PyO3) | `add_<kind>` method + a `nodes()` dict arm (`kind` string) | `add_join` :222-229; `nodes()` arm :311-315 |
| `src/param.rs` | usually **nothing** — `ParamValue` is a closed set `Int/Float/Bool/Str` (:13-18) and `ParamMap` is a sorted `Vec<(String, ParamValue)>` (:127-135); a new param *type* would be a codec change, a new node kind is not |
| `python/graphed/core/graphed_core.pyi` | stub for the new method | `add_join` :53 |
| `src/optimizer/` | **nothing in the engine** (generic over token/boundary, see §3) — but non-exhaustive `match NodeKey` in *tests* breaks (E0004): the optimizer test interpreter needed a `Join` arm (`src/optimizer/mod.rs:396-397`, commit `1f45527`) |
| Python frontend | `Session.record_<kind>()`: backend `op_form(...)` for the output Form, provenance `capture()`, `self._ops` entry, `self._step_reducer()` (incremental reduction) | `record_join` `python/graphed/session.py:185-204`; module verb `python/graphed/shuffle.py:92`; backend arms `python/graphed/awkward/backend.py:54-56` |
| Execution path | either an `evaluate_ir` branch **or** a plan builder (see §6) | `python/graphed/execute.py:85-126`; `python/graphed/shuffle.py:142-263` |

### 2. Structural hashing + determinism requirements

- Interning: `GraphStore` = `Mutex<Inner{nodes: Vec<NodeKey>, intern: HashMap<NodeKey, NodeId>}>` (`src/store.rs:38-46`); `intern()` validates input ids then dedups via the map (`src/store.rs:73-88`). CSE is literally this map — a new kind gets CSE for free iff its `Eq/Hash` fields are exactly its semantic identity.
- Determinism is structural, not hash-ordered: serialization walks `nodes` **in id order** (`src/serialize.rs:113-127`), params are key-sorted (`ParamMap::new` sorts, `src/param.rs:131-135`), floats hash/serialize by canonical IEEE bits with NaN collapsed (`src/param.rs:30-37,103-110`), so "identical graphs serialize to byte-identical output (the M8 determinism gate)" (`src/serialize.rs:5-7`). Round-trip is asserted byte-identical (`src/serialize.rs:287,448`).
- A new node must therefore: (a) put its entire identity into hashable, canonically-ordered fields (ParamMap, ordered `Vec<NodeId>`); (b) never embed run-varying data (pointers, `hash()`, dict order) — M40's `pack_key` is explicit bit-ops "never hash()" for this reason (commit message `4bc452e`); (c) keep its `token()` a pure function of those fields.

### 3. Boundary classification + how fusion consumes it

- `is_boundary()` = everything except `Op` (`src/node.rs:102-103`). Encoded a second time, string-wise, in the engine: `boundary_from_token(token) = !token.starts_with("op|")` (`src/optimizer/engine.rs:54-56`). So the **token prefix is load-bearing**: Exchange/Join deliberately chose non-`op|` prefixes (`"exch"`, `"join"`) with in-code comments saying so (`src/node.rs:132-138`).
- Fusion pipeline (`src/optimizer/mod.rs`): `reduce_with_mode` (:56) builds a token→NodeKey template map (:65-68) for reconstructing boundary nodes after canonicalization — hence "the scheme is in the token so distinct schemes are distinct templates" (`src/node.rs:133,136-137`); `to_engine_graph` copies `boundary: k.is_boundary()` per node (:118-131); CSE is a plain `(token, inputs)` hash-cons pass outside the engine (:133-157); `stage_fusion` (:191) never fuses across a boundary — a lone boundary node "reduced as itself" (:271-285); e-graph rewrites (commutativity etc.) only touch `op|` tokens (`src/optimizer/engine.rs:27-30,73-74`).
- Consequence: a new **non-Op** kind is automatically a stage terminator, survives reduction verbatim, and needs zero optimizer code. A new kind that must **fuse** has to be an `Op` (name+params), not a new variant.

### 4. GIR serialization + version-bump mechanics

- Format: `MAGIC = b"GIR1"` — "Bumping the trailing byte is the versioning hook" (`src/serialize.rs:15-17`); per-node u8 tags `T_SOURCE=0 … T_STAGE=4` (:20-24), then **appended** `T_EXCHANGE=5` (M39, :25-27) and `T_JOIN=6` (M40, :28-30). Both comments state the mechanics: tags appended so all prior tags "encode byte-identically and the M8 determinism gate is untouched; an old reader meeting T_JOIN fails loudly" (:25-30) via `DecodeError` (:42-55). Magic was **not** bumped for either addition — additive tags don't change old bytes.
- Plan level (M39): rather than mutating `DurablePlan` (V1, `format_version: int`, `python/graphed/core/plan.py:126-143`), a **separate additive class** `DurablePlanV2` with a distinct *string* `format_version = "graphed-plan/2"` "so a V1 blob and a V2 blob can never collide and each reader rejects the other's bytes loudly. V1 is untouched." (`plan.py:39,267-277,313-317`).

### 5. External nodes + PayloadDescriptor

- `PayloadDescriptor{kind, content_hash, framework, version, io_schema, preprocessing_ref}` (`src/node.rs:14-21`); it sits inside `NodeKey::External` (:57), participates in derived Hash, and all six fields are flattened into the `ext|…` token (`src/node.rs:117-130`) and serialized field-by-field (`src/serialize.rs:158-171`).
- Construction: `python/graphed/awkward/payloads.py` — `correctionlib_descriptor` (sha256 of the JSON file, `kind="correctionlib"`, :28-45), `onnx_descriptor` (:47-65), `opaque_callable_descriptor` flags unhashable cloudpickle payloads (:85-90). Recording: `Session.record_external` (`python/graphed/session.py:206-243`) — backend supplies descriptor+form by default; an External *family* (M23 histogram fills) passes both explicitly so backends stay domain-free (§A.4, docstring :216-219).
- Binding at execution: `evaluate_ir` dispatches Externals by `descriptor["content_hash"]` → user-supplied evaluator callable (`python/graphed/execute.py:117-124`). So a correctionlib weight lookup is *already* representable: content-addressed External node + evaluator keyed by hash.

### 6. Physical Plan shape (what executors consume)

- V1 `DurablePlan`: `ir: bytes` (canonical GIR blob — "IR canonical, not cloudpickle"), `map_op/reduce_op: OpSpec`, `partitions`, content-addressed `task_id(partition)` (`plan.py:126-177`). `OpSpec` prefers importable refs; cloudpickle only for genuinely opaque callables, flagged `opaque` (`plan.py:54-99`).
- V2 `DurablePlanV2`: `ir: bytes` + `stages: tuple[StageSpec, ...]` (`plan.py:277-279`). `StageSpec{kind, inputs (indices of stages it reads), process: OpSpec, routing: Mapping, tasks: tuple[Task,...]}` (`plan.py:229-244`); `task_id` folds stage index, kind, process identity, routing (incl. `backend_id`), partition (`plan.py:286-302`).
- Crucially: `evaluate_ir` has **no** `"exchange"`/`"join"` branch (`execute.py:102-126` handles only source/op/reduction/stage/external, else raises). Boundary kinds get their execution semantics from **plan builders** that scan `store.nodes()` for their kind string and emit stages: `shuffle_plan` → `map_write`+`gather` (`shuffle.py:142-193`, exchange scan :158), `join_plan` → two `map_write` + one `gather_join` (`shuffle.py:208-263`, join scan :223-234). A new node kind must choose its execution path: in-line `evaluate_ir` branch vs. plan-builder stages.

### UNVERIFIED / out of scope
- Executor-side consumption of `StageSpec` (local/dask/parsl live in the separate `graphed-executors` repo, not this checkout) — the plan shape above is what they receive, per `plan.py` docstrings; not traced into executor code here.
- The claim that column projection needs no per-kind change (no exchange/join hits in `python/graphed/projection.py`; M40 did touch `python/graphed/numpy/projection.py` per the `4bc452e` stat — per-field source provenance through the join). Projection interplay for a new kind should be checked against that file.

## ASSESSMENT / LESSONS (from the M39/M40 arc)

- The recipe is genuinely small in Rust (~25 lines node.rs, ~6 store.rs, ~13 serialize.rs, ~13 lib.rs per the `4bc452e` diffstat); the real work is Python-side: form inference (`op_form`), backend kernels, plan builder, protocol.
- Two identity systems must agree: enum `Eq/Hash` (interning) and `token()` string (engine + templates + CSE pass). Any field left out of the token silently merges distinct nodes during reduction.
- Non-exhaustive matches bite in *tests and helper interpreters*, not the core (commit `1f45527`); grep every `match` on `NodeKey` after adding a variant.
- Versioning discipline: append tags, never renumber; new plan semantics = new additive class with a disjoint `format_version` type/value; old readers must fail loudly, old bytes must not change.
- M39's dispute mechanism was used, not bypassed (frozen test contradiction documented in `.graphed/M39/disputes/`, commit message `530992f`) — precedent for how a Vary milestone should handle frozen-suite friction.

## Design implications for a graphed Vary-style node

- **Weight systematics need no new IR kind.** A correctionlib variation is already an `External` node (content-hashed descriptor, `payloads.py:28-45`) producing extra weight columns; hash-consing (`store.rs:73-88`) co-computes them with the central value in the same fused stage, and histogram fills are already an External family (M23). Frontend sugar only.
- **Shift systematics as graph-multiplication is the path of least resistance**: record the varied suffix N times from the frontend; the intern map automatically shares the unvaried prefix (CSE is the HashMap, `store.rs:40`), DCE/fusion need zero changes, and each variation's suffix fuses into its own stages. Cost is O(variations × varied-suffix) nodes, which is exactly the true work.
- If a dedicated `Vary` variant is added, it is structurally an **Exchange/Join sibling**: `Vary{scheme: ParamMap, inputs}` with variation set encoded in `scheme` (e.g. `sys=jes;dirs=up,down`), non-`op|` token → automatic boundary — but note a boundary **ends stages** (`node.rs:102-103`, `mod.rs:214-246`), so putting Vary between kinematic op and cuts would forbid fusing the varied suffix. That makes a boundary Vary suitable only as a *fan-out/materialization point*, not as an inline tag.
- A **metadata-carrying Vary as an `Op`** (name `"vary"`, params = variation tag) would fuse (token starts `op|`) but an Op yields one value per node — N variations still means N recorded nodes. That is the graph-multiplying option with provenance labels, and it composes with the existing `op_form` seam (`session.py:142`).
- The e-graph only rewrites `op|` tokens (`engine.rs:27-30`); a boundary Vary is invisible to equality saturation — safe, but also means no engine-level dedup of per-variation subgraphs beyond hash-consing.
- Whatever the shape, its **entire identity** (systematic name, direction, payload hash) must live in ParamMap/descriptor fields so token+Hash+serialization agree; variation payloads (correctionlib JSON) ride the existing `PayloadDescriptor.content_hash`, never inlined (§A.3.1).
- Codec: `T_VARY = 7` appended, magic untouched, old readers fail loudly — copy the `T_JOIN` comment pattern (`serialize.rs:28-30`).
- Execution: decide up front whether Vary is evaluated inline (`evaluate_ir` branch, `execute.py:102-126`) or plan-expanded (a `vary_plan` builder emitting per-variation stages into `DurablePlanV2`, mirroring `join_plan` at `shuffle.py:208-263`). Per-variation stages give executors natural scheduling units for shift systematics.
- Plan-level grouping of variations (so a checkpoint Store resumes per-variation) falls out of `StageSpec.routing` + `task_id` folding (`plan.py:286-302`) — put the variation tag in `routing`, get distinct content-addressed task ids for free.
- Frontend: follow `record_exchange/record_join` exactly (`session.py:170-204`) — backend `op_form("vary", …)` for the output Form (identity form for weight-style, input form for shift-style), provenance capture, `_step_reducer()` so incremental reduction sees it.

---

# [frontend-python]

# Systematics-Vary Node Research: graphed emission path, factorization, provenance, execution

Repo roots: `GL` = `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`), `GH` = `/private/tmp/claude-501/graphed-histogram-latest`. All paths repo-relative below. Nothing was modified.

**No prior art in-tree**: no `vary`/`variation` implementation exists anywhere in `GL/python/graphed` (grep hits are only a comment `session.py:264` "selection/systematics chain", and correctionlib's per-node `systematic` string param, `preserve/externals/correctionlib_external.py:37` — a record-time choice, not a graph axis). Systematics-as-a-graph-axis is explicitly Phase-2 out-of-scope in the root CLAUDE.md ("Out of scope — Phase 2 (Part F)").

## VERIFIED FACTS

### 1. Emission path: user verb → builder → Rust IR (M39/M40 template)

Freshest template commits: `2af76f9` (m39 repartition verb + shuffle_plan), `4bc452e` (m40 Join IR + JoinBackend), `1f45527` (optimizer NodeKey::Join arm) — `git log -- python/graphed/shuffle.py`.

Layering, using `graphed.join` as the exemplar:
- **User verb** = module function `join(left, right, *, on, how)` at `python/graphed/shuffle.py:92-111`. It composes existing recorders: `pack_key` (a plain fusible op, `shuffle.py:84-89`, via `session.record_op`) → hash `Exchange` per side (`session.record_exchange`, `shuffle.py:105-106`) → two-input `Join` boundary (`session.record_join`, `shuffle.py:111`).
- **Session recorders** (`python/graphed/session.py`) are the only layer that talks to the Rust store: `record_op` → `self._store.add_op/add_reduction` (`session.py:161-163`), `record_exchange` → `add_exchange` (`session.py:178`), `record_join` → `add_join` (`session.py:199`), `record_external` → `add_external` (`session.py:237`). Each recorder: (a) `capture()` provenance, (b) asks the backend for the output form via `op_form` (`session.py:154`, `177`, `193`), (c) interns the node, (d) fills Python-side tables `_forms/_ops/_provenance` with `setdefault` (interning may return an existing id → CSE, `session.py:164-166`), (e) steps the incremental reducer (`session.py:41-43`).
- **Rust extension** (`graphed.core` → compiled `graphed_core`, re-exported at `python/graphed/core/__init__.py:33`): `NodeKey::Exchange`/`NodeKey::Join` enum variants (`src/node.rs:95-96` inputs, `:134-138` labels), interning constructors `src/store.rs:138,144`, serialization arms `src/serialize.rs:174-179` and `:352-357`, Python `nodes()` kind dicts `src/lib.rs:306-315`, optimizer interpreter arm (commit `1f45527`). Typed stub: `core/graphed_core.pyi:51,53`.
- **Params are scalars only**: field lists are comma-joined strings (`shuffle.py:108-111` "IR params carry only scalars").
- **Plan builders**: `shuffle_plan` (`shuffle.py:142-193`) and `join_plan` (`shuffle.py:208-263`) compile via `compile_ir`, deserialize, scan `store.nodes()` for the boundary kind, and emit multi-stage `DurablePlanV2` (`StageSpec(kind="map_write"/"gather"/"gather_join", inputs=(...))` barrier edges).

### 2. Array factorization rule in practice

- `graphed.Array` (`python/graphed/array.py:127`) is idiom-neutral: dunders, `filter/map/reduce` and `repartition` — the latter kept as a method only because count/size rebalancing "MOVES rows without reinterpreting them — a physical, backend-neutral operation (no array idiom)" (`array.py:384-391`, delegating to `shuffle.repartition`).
- **Neutral module verbs**: keyed repartition and join are "neither an awkward nor a numpy idiom, so per the factorization rule it is a module function, not an `Array` method" (`shuffle.py:5-8`, `:93-96`). Exported at `python/graphed/__init__.py:25`.
- **gak location**: `python/graphed/awkward/functions.py` (75 defs), exported as `from . import functions as gak` at `python/graphed/awkward/__init__.py:12`, in `__all__` at `:23`. Awkward-only semantics live there — e.g. `gak.join(grouped=True)` adds the awkward-only grouped variant, and `grouped=False` is "a thin alias to the neutral `graphed.join`" (`awkward/functions.py:18-39`).
- **numpy idiom** rides a backend-supplied Array subclass: `Session.__init__` uses `backend.array_type()` if present (`session.py:38-39`); `NumpyArray(Array)` at `python/graphed/numpy/array.py:71`, `array_type` at `numpy/__init__.py:345`.
- Per this rule: a `vary` verb (backend-agnostic, semantic not idiomatic) belongs as a **`graphed` module function** like `join`/`repartition`; a varied-results container is frontend-side plain Python (see §4's `{label: hist}` precedent), not an IR object.

### 3. Provenance and StageError

- `capture()` (`python/graphed/provenance.py:66-79`) walks the stack to the first frame whose module doesn't start with `"graphed"`, recording filename/lineno/function + sub-expression text via `executing` (`provenance.py:51-63`). Toggleable (`:40-48`); thread-safe/stateless.
- Provenance lives in a **Python-side dict keyed by node id** (`session.py:30`, `_provenance`), NOT in the Rust IR; exported as `sourcemap()` (`session.py:113-125`).
- `StageError` (`python/graphed/debug/errors.py:29-81`) carries op, `frames` (user source-frame chain), input forms, partition, cause, opt_level — all plain data; custom `__reduce__`/`__setstate__` pickle the whole `__dict__` (`errors.py:67-73`), so **any new attribute rides pickling for free**. Equality/hash enumerate fields (`errors.py:75-81`) — a variation label must be added there and to `summary()` (`errors.py:57-62`).
- Frame chain built by `_chain` in `debug/runner.py:20-31`: failing op's provenance, then back along **primary (first) input** to a source. `_stage_error` at `runner.py:34-45`. Lowering keeps per-op provenance at every opt level via `session.walk` + `session.provenance` (`debug/lowering.py:11-12,82-104`).
- Consequence: if a Vary expansion records cloned nodes from inside graphed library code, `capture()` skips the library frames and attributes every clone to the user's `vary(...)` call line — the original per-op lines are lost unless the expansion copies the source nodes' `Provenance` entries explicitly (they are per-node dict entries, so copying is possible at the Session layer).

### 4. execute()/aggregate(): how results return; one-result-per-output assumptions

- `compile_ir(session, *outputs)` marks output ids, reduces, serializes (`python/graphed/execute.py:54-82`). `evaluate_ir` returns `[vals[o] for o in store.outputs()]` — **a list in mark order** (`execute.py:126`); it already supports N outputs. Output *naming* does not exist in the IR; labels are caller-side.
- `evaluate_ir` dispatches on node kind `source/op/reduction/stage/external` and **raises `GraphedError("unknown node kind")` on `exchange`/`join`** (`execute.py:99-125`) — boundary kinds are executable only via the multi-stage plan builders. A new Vary node kind that must run single-machine needs an arm here.
- `aggregate_plan` (`python/graphed/aggregate.py:68-108`): one IR over all outputs, exactly **one partitioned source** (`aggregate.py:90-93`), one `reduce(list_of_output_values) -> V` per partition + `combine/empty` monoid. `V` is caller-shaped — N named variations fit as `V = dict[label, ...]` with **existing precedent**: graphed-histogram's `_GroupReduce` produces `{label: histogram}` by slicing the flat evaluated-fills list with a positional `layout` (`GH src/graphed_histogram/boost.py:100-117`), combined key-wise by `_add_groups` (`boost.py:119-122`).
- Positional coupling to watch: `_GroupReduce.layout` assumes compiled-fill order matches recorded order (`boost.py:106-116`); N variations per fill multiply entries but the mechanism generalizes.
- Single-boundary assumptions that N shift variations WOULD break: `shuffle_plan` reads `exchanges[0]` only (`shuffle.py:170`); `join_plan` takes the **first** join node (`shuffle.py:233`) and requires exactly two partitioned sources (`shuffle.py:227-231`).

### 5. Session/backend surface a new node kind must extend (measured checklist from M39/M40)

1. Rust: `NodeKey` variant + label + inputs accessor (`src/node.rs`), `GraphStore.add_*` (`src/store.rs`), both serialize arms (`src/serialize.rs`), `nodes()` dict arm (`src/lib.rs`), optimizer arm (commit `1f45527` shows E0004 forces exhaustiveness).
2. Stub `core/graphed_core.pyi` + `Session.record_*` following the `record_exchange`/`record_join` pattern (`session.py:170-204`): capture provenance, backend `op_form`, intern, side tables.
3. `Backend` protocol (`python/graphed/backend.py:30-49`) has NO per-kind methods — new kinds reuse `op_form(op, inputs, params)`/`eval_stage` by op name; both backends special-case the name: awkward `op_form("exchange")=identity`, `op_form("join")=join_form` (`awkward/backend.py:54-58`), `eval_stage("join")` (`:67-68`); numpy mirrors at `numpy/__init__.py:351,363,459,463`. Boundary-ness for fusion is `boundary_ops()` (`awkward/backend.py:36-38,84-85`).
4. `evaluate_ir` kind dispatch (`execute.py:99-125`) and/or a plan builder if it is an execution barrier.
5. Projection: `read_columns` walks graphs syntactically and **walks through External nodes** (`python/graphed/projection.py:109-115`) — a Vary node must be transparent to column collection or projection under-reads.

### 6. graphed-histogram ↔ frontend coupling

- Plain imports, no entry points: `GH src/graphed_histogram/boost.py:22-24` imports `graphed.Array`, `graphed.aggregate_plan`, `graphed.core.PayloadDescriptor/Partition/Plan`.
- `Histogram.fill(*args, weight=..., sample=...)` (`boost.py:153-214`) records ONE External node per fill via `session.record_external("histogram.fill", evaluator, inputs, params, descriptor=..., form=HistogramForm)` (`boost.py:196-211`) — the M23 "package records its OWN External family" path where the backend is not consulted (`session.py:216-219`). **`weight=` already accepts a sequence of multiplicative weight Arrays** (`boost.py:166-172`, M29), each a real graph input.
- Multi-histogram single-pass: module-level `plan()` (`boost.py:256-300`) → `aggregate_plan` with `_GroupReduce` → `{label: hist}`; shared sub-graphs intern to one node so shared work runs once (`aggregate.py:1-11`).

## ASSESSMENT / LESSONS

- **Hash-consing already gives "co-compute the central value" for free.** Recording a varied chain re-uses every unvaried node (interning returns existing ids, `session.py:164`; "CSE falls out of M1 hash-consing", root CLAUDE.md §A.2). So the cheapest correct Vary implementation is *record-time expansion*: re-record the downstream sub-graph with substituted inputs; the shared prefix dedups automatically and one `aggregate_plan` over all variation outputs evaluates it in one pass. That matches how weight-vs-shift differs naturally: weight variations only fork at the fill's weight input; shift variations fork at the kinematic op and interning keeps everything upstream shared.
- The alternative — a first-class Rust `Vary` node kind — costs the full 5-point checklist in §5 including an optimizer arm and executor semantics, and `evaluate_ir`/plan builders currently hard-fail on unknown kinds. Nothing measured requires it for correctness; it would buy IR-level introspection ("this plan contains variations nominal/up/down") and per-variation DCE, which record-time expansion also gets implicitly (each variation output is just an output; DCE is reachability).
- UNVERIFIED: runtime cost of N-variation expanded graphs on optimizer/e-graph time (no benchmark run in this research); M4's super-linear-reduction CI guard (root CLAUDE.md) is the existing tripwire.
- The `{label: result}` container question is already answered in-tree twice: `_GroupReduce` dict results and `evaluate_ir`'s ordered list + caller-side labels. A `Varied` frontend container = a thin mapping `{variation_name: Array}` supporting broadcast of further ops across variations (RDataFrame's `VariationsFor` analogue), living in `graphed` proper (neutral) — not gak, not NumpyArray.

## Design implications for a graphed Vary-style node

- Put `vary(...)` as a **neutral module verb** in `graphed` (like `join`/`repartition`, `shuffle.py:92`); the varied-results container is a plain frontend mapping, no IR type.
- Prefer **record-time expansion + interning** over a new Rust NodeKey: re-record varied sub-graphs; hash-consing (`session.py:164`) dedups shared work; defer a first-class node until introspection demands it.
- Weight systematics = extra entries in the histogram `weight=` sequence (`GH boost.py:166-172`) producing one External fill node per variation; results come back named via the existing `_GroupReduce` dict pattern (`GH boost.py:100-117`).
- Shift systematics = substitute the varied kinematic Array at the fork point and replay downstream recording; everything above the fork stays one node — no re-run of the unvaried prefix.
- If a real node kind is ever added, budget the full M40 checklist: NodeKey + both serialize arms + `nodes()` arm + optimizer arm (E0004 enforces it) + `.pyi` + `Session.record_*` + `op_form`/`eval_stage` in BOTH backends + `evaluate_ir` arm + projection transparency (`projection.py:109-115`).
- Thread the variation label into `StageError` as a new constructor field + `summary()` + `__eq__`/`__hash__` (`debug/errors.py:32-81`); pickling is free via the `__dict__`-copying `__reduce__`.
- Preserve provenance under expansion: copy the original nodes' `Provenance` entries when cloning (`session.py:30` per-node dict), else every varied node points at the user's `vary()` line.
- Keep variation identity out of structural params unless it must change node identity — a differing param (e.g. correctionlib `systematic="up"`, `preserve/externals/correctionlib_external.py:37`) already forks the node hash; identical params must stay identical to keep CSE.
- Drive N-variation evaluation through the existing multi-output engines: `compile_ir(*outputs)` + `aggregate_plan` one-pass (`aggregate.py:68`); don't add a per-variation execution loop.
- Shift variations that cross an `Exchange`/`Join` boundary hit the first-boundary-only plan builders (`shuffle.py:170,233`) — generalize those before allowing varied shuffles, or restrict v1 to variations downstream of boundaries.

---

# [histogram]

All evidence gathered. Here is the report.

# Weight-systematic filling: what the histogram layer provides & needs

Repos examined: `/private/tmp/claude-501/graphed-histogram-latest` (graphed-histogram), `/private/tmp/claude-501/hist-graphed` (hist fork, branch `graphed-mvp`), `/private/tmp/claude-501/coffea-bench` (coffea-benchmarks fork, branch `graphed-mvp`, `git@github.com:graphed-org/coffea-benchmarks-graphed-mvp.git`), graphed frontend + exec-local at `/Users/lgray/vibe-coding/graphed-workdir/`. Runtime probes ran in a scratch venv with **boost-histogram 1.7.2, hist 2.10.1, dask-histogram 2026.2.0** (satisfying the repo pins `boost-histogram>=1.4`, `hist>=2.7` — `graphed-histogram-latest/pyproject.toml:22,37`).

## VERIFIED FACTS

### 1. The fill path
- `Histogram.fill(*args, weight=, sample=)` records ONE External node per call via `session.record_external("histogram.fill", evaluator, inputs, params, descriptor=, form=)` — `src/graphed_histogram/boost.py:196-210`. It never computes; it returns `self` and appends the node to `self._fill_nodes` (boost.py:211-213).
- All positional axis args MUST be graphed `Array`s (boost.py:162-163 raises otherwise). There is no way today to pass a constant/scalar category value into a fill — no constant-Array constructor exists in the frontend (`graphed/src/graphed/` has only `from_awkward`/sources; grep for `def constant|def full|def literal` in session/array modules: no hits).
- Payload: `PayloadDescriptor(kind="histogram", content_hash=sha256(spec), framework="boost_histogram", io_schema="uhi")` (boost.py:188-195); the spec is canonical sorted-key JSON of axes+storage (`_spec.py:115-122`), and `zero_of(spec)` rebuilds the empty histogram on any worker (`_spec.py:129-135`).
- Node identity = descriptor + input node ids + params (`graphed/src/graphed/session.py:216`, `self._store.add_external(descriptor, ids, params_d)`); identical fills intern (hash-consing store), stated at boost.py:4-5.
- The evaluator is a picklable frozen dataclass `FillEvaluator(spec, n_axes, has_weight, has_sample, n_weights)` that fills ONE chunk into a fresh `zero_of(spec)` (boost.py:50-71).

### 2. Weights today: N multiplicative FACTORS of one weight, not N variations
- M29: `weight=` accepts a **sequence of Arrays**; each factor is a real graph input; `FillEvaluator` multiplies them elementwise into a single 1-D weight (boost.py:166-174 recording; boost.py:64-68 evaluation; params carry `n_weights` only when >1, boost.py:205-206, keeping pre-M29 node identity — frozen test `tests/frozen/m29/test_multi_weight_fills.py:93-99`).
- Frozen m29 tests pin: 3 weights ⇒ 4 graph inputs (`test_multi_weight_fills.py:82-87`), plan-path determinism + equality to eager (lines 58-79), jagged flatten consistency (lines 102-121).
- Everything (values and weight) is flattened to 1-D by `_flat` before `bh.fill` (boost.py:39-47, 62-69). A 2-D weight cannot survive this path.
- boost-histogram itself rejects a 2-D weight against 1-D values: probe `h.fill(x_1d, weight=ones((2,3)))` → `ValueError: spans must have compatible lengths` (bh 1.7.2, scratch venv). **So one fill = one weight column; N variations cannot ride a single fill as a weight matrix.** N fills or an extra axis are the only shapes bh supports.
- dask-histogram's batching (site-packages `dask_histogram/boost.py:203-232`, `core.py:409-434, 978-1005`): N staged fills become ONE task per partition (`_blocked_multi`) that **loops the N fills into a single cloned histogram**, then tree-reduces with `split_every` default 8 (`boost.py:219-221`). I.e. multi-fill batching = a per-partition loop over `thehist.fill(...)`, never a multi-weight fill.

### 3. StrCategory "variation" axis support
- Non-growth `StrCategory`/`IntCategory` are fully supported in the canonical spec (`_spec.py:72-75, 68-71`); **growth axes raise `TypeError("growth axes are not supported (Phase 2)")`** (`_spec.py:70,74`; design.rst:118-120 lists growth axes as deliberate Phase 2 — cross-partition category-union merge is the stated reason).
- Probes (bh 1.7.2): scalar string broadcasts across a fill (`h.fill(x, 'up')` works); per-entry label arrays work (concatenated variation fill sums correctly per category); growth-axis histograms DO merge category-aware under `+` (`{'A':1,'B':3,'C':1}` from mismatched axes), but **non-growth mismatched axes fail `ValueError: axes not mergable`** — so a fixed-category variation axis is combine-safe by construction (identical spec on every partition).
- hist named-axis fills route kwargs→positional and hit the same path: `basehist.py:298` `fill(...)` → `basehist.py:338` `return super().fill(*args, *data, weight=weight, sample=sample, threads=threads)`. So `fill(..., variation="jesUp")` as a *named-axis kwarg* would still need the value to be a graphed Array under today's boost.py:162 check.

### 4. The ADL benchmark pattern (user code today)
- `hist.graphed` is a thin MRO sandwich: `class Hist(HistInMemory[S], ghb.Histogram, ...)` — `hist-graphed/src/hist/graphed/hist.py:15-20`; QuickConstruct + named-axis fills record deferred; executor results wrap back via `hist.Hist(value)`.
- User code (`coffea-bench/adl_graphed.py`): every query is one chained line, e.g. `hg.Hist.new.Reg(100, 0, 200, name="met", label=...).Double().fill(met=...)` (adl_graphed.py:74, 89); ALL of a query's histograms go into ONE group plan: `plan_group(staged, steps_per_file=..., backend="adl_graphed:make_backend")` then `runner.run(plan).value` → `{name: hist.Hist}` (adl_graphed.py:199-210). Currently **all unweighted Double storage**; no ADL query fills with `weight=` (grep: no `weight=` in adl_graphed.py fills).
- Group plan single-pass is a frozen witness: 4 partitions read ONCE each, not once per histogram (`tests/frozen/m23/test_group_plan.py:68-77`, read-counting PartitionedSource at lines 31-44).

### 5. Aggregation across partitions
- `Histogram.plan()` → `aggregate_plan(*fill_nodes, reduce=_SumFills(spec), combine=add_histograms, empty=_ZeroHist(spec), externals=...)` (boost.py:244-253); multi-histogram `plan()` uses `_GroupReduce(layout)` / `_add_groups` / `_GroupZero` over `{label: hist}` dicts (boost.py:281-295).
- `aggregate_plan` compiles ALL outputs to ONE IR, one task per partition, column projection over the union (`graphed/src/graphed/aggregate.py:67-107`, `columns=read_columns(list(outputs), nid)` at :100); returns `Plan(process, combine, empty, tasks)` (`graphed-core/python/graphed_core/execution.py:175`).
- Per partition: every fill node is evaluated (one filled histogram each), then `_SumFills`/`_GroupReduce` sums them **within the partition** (boost.py:88-98, 101-117) — so what crosses the wire per partition is one histogram (or one `{label: hist}` dict), not one-per-fill.
- Cross-partition combine is a fixed binary tree, deterministic and straggler-tolerant (`graphed-exec-local/src/graphed_executors/local/_reduce.py:1-11, 25-45`); combine is native `+` (boost.py:82-84), Int64 exact, floats deterministic per fixed tree (boost.py:10-11).
- **What N variations multiply**: (a) per-partition transient histogram allocations (one per fill node evaluated), (b) the size of the per-partition reduced value shipped up the tree (N+1 dict entries or an (N+1)-wide axis), (c) additions per combine node. The event-data read and the shared kinematics sub-graph do NOT multiply — one IR, one pass (test_group_plan.py:68-77).

## ASSESSMENT / LESSONS

Three candidate shapes for "central + N weight variations co-filled":

1. **Multi-weight single fill (2-D weight)** — dead on arrival: bh rejects 2-D weight (probe, §2) and `_flat` 1-D-ifies everything (boost.py:39-47). Would require an evaluator loop anyway, at which point it's option 3.
2. **N+1 sibling fills, grouped in one plan** — works TODAY with zero histogram-layer changes: N+1 `Histogram` objects sharing axes-Arrays (interned once by hash-consing), each `fill(x, weight=[w_central_factors..., w_var])`, all passed to `graphed_histogram.plan({...})`. Single pass over data is already guaranteed and frozen-tested. Cost: N+1 fill-node evaluations + N+1 transient hists per partition; combine ships an (N+1)-entry dict. This is exactly dask-histogram's shape (its `_blocked_multi` loop), so it is the proven-correct baseline.
3. **Fixed StrCategory variation axis** — one histogram of size nbins×(N+1); ONE object per partition and per combine (vectorized `+`). But today it is *inexpressible at fill time*: the category value can't be a constant (boost.py:162 requires Arrays; no constant-Array exists), and per-entry label arrays would tile the axis values N+1 times through the graph (wasteful). The cheap unlock is an **evaluator-side loop**: extend `FillEvaluator` (or add a sibling `VariedFillEvaluator`) to take N+1 weight inputs plus a params-carried category list, and do `h.fill(*axes, label_i, weight=w_i)` per variation into ONE spec'd histogram — scalar-string broadcast is verified working, non-growth category axes are combine-safe, and the spec/`zero_of` machinery already round-trips StrCategory. This mirrors dask-histogram's per-partition multifill loop but lands the variations in one storage.

Option 3 is the cheapest at scale (memory and combine traffic O(1) objects instead of O(N)); option 2 is the cheapest *to ship* (zero code). SHIFT systematics need neither: shifted kinematics are different input Arrays ⇒ different fill nodes whose common prefix dedups via hash-consing, and the group plan still evaluates everything in one pass — they are just more siblings in the same `plan({...})`.

UNVERIFIED: exact Rust-side interning behavior of `add_external` (claimed by docstrings boost.py:4-5, session.py contract; not traced into graphed-core Rust). The category-aware growth-axis merge probe used bh 1.7.2 only.

## Design implications for a graphed Vary-style node

- **bh cannot take a weight matrix** — a Vary node must lower to either N+1 fill nodes or one looping evaluator; never plan on a single multi-weight `bh.fill`.
- **Co-filling with central is already free**: any set of fill nodes passed to `graphed_histogram.plan()` shares one IR, one read, one kinematics evaluation per partition (frozen witness). A Vary frontend only needs to *stage siblings into the same plan*.
- Weight variations should lower by **swapping one factor in the M29 `weight=[...]` list** — everything upstream interns; the varied node differs only in that one input id.
- The cheapest scalable target is **one histogram with a fixed (non-growth) StrCategory "variation" axis filled by an evaluator-side loop** (params carry the labels; scalar-string broadcast verified) — O(1) objects per partition/combine vs O(N) for sibling fills.
- Keep the variation axis **non-growth**: fixed categories make partial histograms identical-spec and `+`-safe; growth axes are explicitly Phase 2 and non-growth mismatches refuse to merge.
- The variation labels must enter the **content hash** (via spec metadata or params) so two Vary fills with different variation sets are distinct nodes and replay-safe through the Store.
- Preserve M29's identity discipline: emit new params (e.g. `variations=[...]`) only when present, so unvaried fills keep pre-existing node identities byte-for-byte (the m29 precedent, frozen).
- Shift systematics need no histogram-layer work: shifted kinematics = different axis Arrays = sibling fill nodes; hash-consing dedups the unshifted prefix; the re-run-per-variation cost is confined to the divergent sub-graph.
- If a constant-category frontend sugar is wanted (`fill(..., variation="jesUp")`), route it through **params, not a fake Array** — boost.py:162's Arrays-only check is a deliberate seam; a params-carried label reaches the evaluator without touching the IR's input list.
- Follow dask-histogram's proven per-partition shape (loop fills into one clone, then tree-reduce) — graphed already has the superior fixed-tree deterministic combine; do not add a separate variation-reduction stage.

---

# [optimizer]

# Systematics variations vs. the graphed optimizer — research report

Target: `/private/tmp/claude-501/graphed-latest` (read-only). All runtime numbers measured in-context on this checkout (Rust ext built via `uv run`, 2026-07-28).

## VERIFIED FACTS

### 1. Where DCE / CSE / stage fusion live

- **Pipeline order** — `reduce(graph) = DCE → engine.canonicalize (egg) → CSE → stage_fusion → rebuild into a fresh interned store`: `src/optimizer/mod.rs:1-11` (doc), `mod.rs:56-84` (`reduce_with_mode`).
- **DCE** = plain reachability from marked outputs, iterative stack, compacts preserving topo order: `src/optimizer/mod.rs:88-116` (`dead_code_elimination`). "Never drops a node on a path to an output" (`mod.rs:86-87`).
- **CSE** = hash-consing `(token, inputs)` as a plain pass *outside* the engine: `src/optimizer/mod.rs:133-153` (`cse`). Construction-time CSE additionally falls out of M1 interning (below).
- **Construction-time interning** — `GraphStore::intern` looks up the structural `NodeKey` in a `HashMap<NodeKey, NodeId>` under one mutex; identical key ⇒ same `NodeId` returned, no new node: `src/store.rs:73-88`. `NodeKey` equality/hash *is* the interning identity: `src/node.rs:39-41`.
- **Stage fusion boundary rule** — fusion never crosses a boundary; `is_boundary()` is `!matches!(self, NodeKey::Op{..})` — i.e. Source/Reduction/External/Stage/Exchange/Join are all boundaries: `src/node.rs:100-104`. Two modes, `SingleUse` (default, pinned by frozen M4 suite) and `Maximal` (diamond-in-one-stage): `src/optimizer/mod.rs:23-33`, mechanics at `mod.rs:187-345`. A fan-out op under `SingleUse` heads its own stage (diamond apex test: `mod.rs:543-565`).
- **Engine** — egg over `SymbolLang`, sound rules only (commutativity of `SYMMETRIC_OPS`, identity tokens), deterministic iter budget 12, node limit `4·N + 1024`: `src/optimizer/engine.rs:22-31, 59-106`. O(N) extraction (earliest node per e-class) chosen explicitly because egg's recursive extractor is O(depth×nodes) and "blows up … on the deep chains a systematics graph produces": `engine.rs:7-13, 107-135`. Boundary detection inside the engine is token-prefix-based: `boundary_from_token = !token.starts_with("op|")`: `engine.rs:54-56`.

### 2. Incremental reducer + anti-quadratic guard

- **`IncrementalReducer`** (`src/optimizer/incremental.rs:30-131`): consumes the arena delta-by-delta; per-step cost ∝ delta, never history (`incremental.rs:63-76`); constructor-local canonicalization (identity elimination, symmetric-op dedup, hash-consing) uses the *same* `SYMMETRIC_OPS`/`IDENTITY_TOKENS` constants as the engine (`incremental.rs:78-109`, `engine.rs:22-31`); `total_work` is the incrementality witness (`incremental.rs:38-41,54-56`). `finalize` runs the standard pipeline over the canonical arena, O(canonical size) (`incremental.rs:110-130`). Session wires it in: every record calls `_step_reducer()` (`python/graphed/session.py:31-42`, and call sites at 139, 167, 182, 203, 241).
- **The guard** — frozen test `tests/frozen/core/m4/test_benchmark.py`: sizes `[1000, 2000, 4000, 8000]` (line 10); fails if `time(8k)/time(1k) >= 24.0` (linear ⇒ ~8×, quadratic ⇒ ~64×; lines 40-43); plus per-size absolute budget `< 1.0 s` and `reduced_nodes < 10` for its topology (lines 46-53).
- **Measured: what N shift variations cost today** (shared prefix P=500 ops, per-variation `shift` + 50-op downstream chain + 1 reduction; script run in-context):
  - Interning dedupe: re-adding an identical op returns the same id (`True`).
  - N=1→2 grows the arena by exactly the varied suffix (delta = 52 = D+2 nodes); the 501-node prefix is shared.
  - | N | nodes | reduce (best of 3) | reduced_nodes | stages |
    |---|---|---|---|---|
    | 1 | 553 | 1.4 ms | 3 | 1 |
    | 4 | 709 | 1.7 ms | 10 | 5 |
    | 16 | 1333 | 3.1 ms | 34 | 17 |
    | 64 | 3829 | 9.4 ms | 130 | 65 |
    | 128 | 7157 | 16.7 ms | 258 | 129 |
  - Scaling: 12.9× nodes → 11.9× time — **linear**, comfortably inside the guard. Reduced form is `2N+2` nodes (`stages = N+1`): one shared-prefix stage computed once + per-variation {chain-stage, reduction}. Un-reduced arena grows as `shared + N·(D+2)`; the reducer never sees duplicated prefix work because interning already deduped it.

### 3. Column projection (M5/M10)

- **Frontend seam** (`python/graphed/projection.py`): `Projection` (source → column set, lines 34-44), `BufferProjection` (M10, per-column `DATA` vs `OFFSETS`, lines 47-86), opaque-op policy `pass|warn|raise` (lines 24-27, 93-106). `read_columns` (lines 109-147) is the backend-agnostic *syntactic* read set: walks the graph via `session.walk`, collects `field`/`fields` params applied to the source; any non-field op consuming the whole source record ⇒ conservative `None` = read everything (lines 139-141, 145-146). Walks *through* External nodes (lines 116-118).
- **Backend refinement** — graphed-awkward replays the recorded graph on a reporting typetracer and collects touched buffer form-keys; opaque ops `_touch_data(recursive=True)` on their inputs; the materialized output's leaves are touched too: `python/graphed/awkward/projection.py:1-9, 65-103` (`_replay`), `project` (105+), `project_buffers` (119+).
- **Effect of a varied column**: projection is a pure function of the recorded ops. A shifted `Jet.pt` expressed as ordinary ops (`field(pt)` then `mul`/`add`) adds **no** new source columns — the same `field` params appear (union of per-variation walks = the central set). New reads appear only if a variation touches columns the nominal path did not (e.g. JES needs `Jet.eta` for a binned SF) — then the union grows by exactly those fields. Nothing in `projection.py` is variation-aware; there is no per-output projection split (one `read_columns` per source across *all* `arrays` passed in, lines 143-146).

### 4. The M39/M40 Exchange/Join integration template ("blast radius" of a new boundary node)

A boundary-ish node had to touch, verbatim:
1. **IR variant** with `scheme: ParamMap` as its structural identity: `src/node.rs:68-84` (Exchange, Join) + arms in `inputs()` (88-98), `with_inputs` (171-178), `label()` (205-218).
2. **Boundary semantics for free** — because `is_boundary` is `!Op` (`node.rs:102-104`) and the token uses a non-`op|` prefix so the engine's `boundary_from_token` agrees (`node.rs:132-138`, `engine.rs:54-56`). Scheme params go **in the token** so distinct schemes are distinct reconstruction templates (`node.rs:133-138`; template table in `mod.rs:65-69, 283`).
3. **Store constructor**: `add_exchange`/`add_join` (`src/store.rs:135-145`) — interns like every node ⇒ CSE for free.
4. **Serialization**: a new tag **appended** so old blobs stay byte-identical (`src/serialize.rs:25-28, 174-180, 352-358`).
5. **Frontend recording** with backend type-check via `op_form("exchange"/"join", …)` and registration in `session._ops` so `walk`/projection/materialize traverse it: `python/graphed/session.py:170-201`.
6. **Frozen contract**: interns/CSEs like any node, scheme participates in identity, *ends a stage and survives reduce*, byte-deterministic reduction, serialization round-trip + legacy stability: `tests/frozen/core/m39/test_exchange_ir.py:35-79`, `m39/test_exchange_serialize.py:31-63`, `m40/test_join_serialize.py:35-62`, plus plan-level task-id determinism (`m39/test_durable_plan_v2.py:105-122`).

### 5. Key claim — prefix sharing via interning: **TRUE**; extra diff machinery: **NONE**

- **True, structurally**: `GraphStore::intern` (`src/store.rs:73-88`) returns the existing `NodeId` for an identical `NodeKey`; a `NodeKey`'s identity is `(kind, name, params, input ids)` (`src/node.rs:40-85`). Re-emitting a varied subgraph with one input changed: every ancestor *not* downstream of the change has an identical key ⇒ identical id (shared, zero new nodes — measured above: N=1→2 delta exactly D+2). Every node downstream of the change has a different input id ⇒ different key ⇒ new node, cascading to the output. So CSE gives exact prefix sharing; the duplicated region is exactly the true impact set. DCE keeps all marked outputs (`mod.rs:88-99`); fusion keeps the shared prefix as one stage (fan-out node heads its own stage, `mod.rs:209-233`; measured `stages = N+1`).
- **No dirty-set / graph-diff / invalidation machinery exists**: `grep -rni "dirty|invalidat|graph_diff|impact"` over `src/` + `python/` (excluding tests) returns nothing. The `IncrementalReducer` watermark (`incremental.rs:37, 49-51`) is append-only consumption, not invalidation.
- **Execution-level reuse gap**: checkpoint memoization is content-addressed, but `task_id` folds **`self.ir` — the whole plan's IR** (`python/graphed/core/plan.py:164-176` V1; `plan.py:286-300` V2 also folds whole `self.ir` + stage index). Adding one variation changes the plan IR ⇒ *every* task id changes ⇒ zero cross-run cache reuse for unchanged stages, even though the store itself is idempotent by blob hash (`python/graphed/checkpoint/store.py:1-8, 63-70`). Graph-level sharing does **not** currently translate into checkpoint-level sharing across plan revisions.

## ASSESSMENT / LESSONS

**"Re-emit + intern" vs "first-class Vary node", under the anti-quadratic guard:**

- **Re-emit (measured)**: cost is `O(N·D)` arena nodes and linear reduce time (16.7 ms for 128 variations × 50-op chains — negligible vs. any real analysis). The guard is safe: the reducer is linear in *total* nodes and variations add nodes linearly. Weight systematics are even cheaper: N extra weight-multiply ops fuse into the existing fill stage (or one stage per fill), sharing everything upstream. Impact analysis is *implicit and exact*: the duplicated nodes ARE the impact set; no machinery needed. Weaknesses: (a) the frontend must re-execute user Python per variation to re-record (interpreter cost at build time, mitigated by `IncrementalReducer` keeping compile incremental — `session.py:31-34`); (b) N is burned into the graph — no "list variations" introspection without convention; (c) the reduced plan has O(N) stages, so plan bytes and scheduling metadata grow linearly (fine at N≈100s, per M4's linearity).
- **First-class Vary node kept through the optimizer**: everything in §4's template must be re-specified (variant, token/params-in-identity, boundary decision, serialize tag, frontend recording, frozen determinism suite) *plus* new semantics no existing node has: a Vary node changes the *multiplicity* of downstream values, so fusion, projection replay (`awkward/projection.py:_replay` evaluates one tracer per node), `walk`, and every executor would need variation-awareness — a much larger blast radius than Exchange/Join, which slotted into the existing "boundary that interns" mold. If instead the optimizer *expands* Vary early (macro-expansion into re-emitted subgraphs before reduction), you keep the measured linear behavior and the executor/projection stay unchanged — the Vary node is then frontend sugar + provenance, not an optimizer concern.
- **Lesson from the codebase**: egg extraction was already redesigned specifically because "deep chains a systematics graph produces" broke O(N) (`engine.rs:7-13`) — the system was built expecting variation-multiplied graphs and handles them linearly today.

## Design implications for a graphed Vary-style node

- **SHIFT systematics need no new optimizer machinery**: re-emit downstream ops per variation; interning gives exact prefix sharing (measured: delta = varied suffix only), fusion gives one shared prefix stage + one stage per variation, DCE/determinism hold. Make `Vary` a *frontend/IR-metadata* construct that expands before or at recording time, not a node the egg engine must understand.
- **WEIGHT systematics**: emit N weight ops feeding the fill; they co-fuse with the central fill stage under existing rules — verify with a frozen test asserting stage count stays O(1), not O(N), for weight-only variations.
- If a first-class `Vary` IR node is kept at all (for introspection/preservation), copy the Exchange template exactly (`node.rs:68-84` + §4 checklist): scheme-in-token, non-`op|` prefix, appended serialize tag, frozen intern/CSE/stage/determinism suite — and have `reduce` expand it before the engine sees it.
- **Anti-quadratic guard**: add variation-shaped sizes to the M4 benchmark topology (N variations × fixed chain) — current guard already passes this shape linearly (measured 11.9× time for 12.9× nodes) but nothing pins it.
- **Projection**: per-variation column needs are the union of per-output walks — `read_columns` already takes `Sequence[Array]` (`projection.py:109`); pass all variation outputs and it's correct today. A *per-variation* split (read shifted inputs only for shifted partitions) would be new work.
- **The real gap is checkpoint reuse, not graph reuse**: `task_id` hashes the whole plan IR (`plan.py:164-176, 286-300`), so adding one variation invalidates every cached task. For cheap "add a systematic, re-run only its cone", key tasks on a *per-stage subgraph* fingerprint (the stage's own reduced IR cone + partition), not the whole plan.
- **Impact analysis = node-identity diff**: the impact set of a shift is precisely "nodes whose `NodeKey` changed", available by construction (new ids past the interning watermark). Expose it as a trivial API over the existing arena rather than building invalidation machinery.
- Frontend ergonomics constraint: re-emission means user code between the varied quantity and the fill must be replayable N times — a `vary(...)`-scoped context or a callable-based API (RDataFrame `Vary` takes an expression) fits the existing `session.record_*` model (`session.py:170-241`).
- Provenance: per-variation nodes should carry the variation name in `params` (it lands in the token ⇒ distinct identity, deterministic reduction, and readable `to_dot` labels — `node.rs:109-140`).
- Plan-size ceiling: reduced graph grows ~2 nodes/variation (measured `2N+2`); at N≈1000 shifts this is still thousands of stages — acceptable, but partial re-fusion of per-variation stages that share a schedule (same partition set) is the Phase-2 lever if scheduling overhead ever shows up.

---

# [exec-checkpoint]

# Systematics-variation research: planning, scheduling, memoization, delivery in graphed

Paths: `EX` = `/private/tmp/claude-501/graphed-exec-check/src/graphed_executors`, `GR` = `/private/tmp/claude-501/graphed-latest/python/graphed`.

## VERIFIED FACTS

### 1. Plan structure the executors consume

- The runtime `Plan` is a **single monoid reduction**: `process(partition, resources) -> R`, associative `combine(R,R)`, `empty()`, a fixed `tasks: Sequence[Task]` or an adaptive `next_tasks` hook (`GR/core/execution.py:206-216`). A `Task` is `(key:int, partition)`; the int key fixes the reduction-tree shape (`GR/core/execution.py:152-158`). Every executor returns `ExecResult(value=<one R>, n_partitions, n_combines, stopped)` (`GR/core/execution.py:219-224`).
- Compilation: `compile_ir(session, *outputs)` marks outputs, reduces (DCE+CSE+eq-sat fusion), serializes to one IR blob (`GR/execute.py:54-82`). `evaluate_ir` walks the reduced nodes — kinds `source|op|reduction|stage|external` — and returns **outputs positionally, in mark order** (`GR/execute.py:96-126`). Fused-stage members evaluate inline in one dispatch loop (`GR/execute.py:110-115`).
- **Multi-output is already a solved shape**: `aggregate_plan(*outputs, reduce, combine, empty, ...)` compiles all outputs into ONE IR so shared sub-expressions intern to a single node ("evaluate the shared sub-graph ONCE, not once per output", `GR/aggregate.py:1-11`), reads each partition once projected to the **union** of the outputs' columns (`GR/aggregate.py:101`), evaluates once, then the caller's `reduce(values:list)->V` folds the per-partition output values into one composite partial (`GR/aggregate.py:44-65`). The partial `V` is opaque to executors — histograms/dicts/tuples all work; per-output identity is positional inside `V`.
- Durable form: `DurablePlan` = IR bytes + `process/combine/empty` OpSpecs + partitions + metadata, canonical sorted-key JSON, byte-deterministic (`GR/core/plan.py:126-209`). `with_partitions` = "compile once, run on N datasets" — same IR, new partition set (`GR/core/plan.py:179-192`). Multi-stage `DurablePlanV2` exists only for shuffles (map_write→gather stages with `inputs` edges, `GR/core/plan.py:228-323`).
- Executor task keys are **per-run nonced**: `_key(plan_fp, run_nonce, kind, idx)` with the nonce explicitly so a second `run()` re-executes instead of hitting a cached dask future (`EX/submit/engine.py:196-201, 243`). No cross-run memoization exists at executor level.

### 2. Content-addressed memoization: does an identical unvaried stage dedup across variations?

**Refuted at Store level; confirmed only inside one compiled plan.**

- Task identity: `DurablePlan.task_id(partition) = SHA256(domain, self.ir, process.identity(), partition_bytes)` — it folds the **entire plan IR** (`GR/core/plan.py:164-176`). V2 likewise folds the whole `self.ir` plus stage index/kind/process/routing/partition/key (`GR/core/plan.py:286-301`). There is **no per-stage subgraph hash**: a stage's id is not content-addressed on its own subgraph.
- Consequence: two variation plans whose IRs differ **anywhere** (e.g. one shifted-JES branch) produce different `task_id`s for **every** partition, including partitions of a byte-identical unvaried prefix stage → the Store recomputes everything. Dedup granularity is (whole-IR × process × partition), nothing finer.
- The resumable runner skips a partition iff its `task_id` is journaled with a present blob (`GR/checkpoint/runner.py:90-98`; journal replay `GR/checkpoint/store.py:101-118`). So dedup across variations happens **only** if two variations serialize to byte-identical plans (then task_ids collide by construction — e.g. a duplicated "nominal") — both within one run (`completed` consulted before each task, `runner.py:90-93`) and on resume.
- Output blobs DO dedup by content: `Store.put` names blobs by SHA-256 of the bytes, idempotent (`GR/checkpoint/store.py:62-73`) — identical partials share disk, but compute is not skipped and journal entries stay per-task_id.
- **Within one compiled plan**, sharing is free and total: the Rust `GraphStore` is a "Thread-safe interned graph store. Structurally identical nodes share one NodeId" (`GR/core/graphed_core.pyi:38`); reduction applies DCE+CSE+fusion (`GR/session.py:63-64`). So a shared unvaried subgraph feeding N variation outputs is ONE node chain evaluated once per partition pass.
- Executors never touch the checkpoint Store: no import/use of `graphed.checkpoint` anywhere in `EX` (grep over `EX/**/*.py`; the "Store" hits are the unrelated shuffle-block node stores, `EX/local/shuffle.py:165ff`). `run_resumable` is a **sequential single-machine for-loop** (`GR/checkpoint/runner.py:90-131`); the parallel executors (thread/process/dask/parsl) have no checkpoint/skip path.

### 3. External node execution (correctionlib/ONNX) — the weight-systematic compute site

- External nodes are **not embedded in the IR**; `evaluate_ir` resolves them via an `externals: {content_hash: callable}` mapping and fails loudly when missing (`GR/execute.py:16-18, 116-123`).
- The lookup runs **inside the per-partition worker process**: `_PartitionReduce.__call__` reads the chunk, then `evaluate_ir(..., externals=dict(self.externals))` (`GR/aggregate.py:57-65`). The evaluator callables ship to workers pickled inside `plan.process` (`GR/aggregate.py:54, 96-104`).
- Descriptors: `correctionlib_descriptor`/`onnx_descriptor` hash the payload file → `content_hash` (`GR/awkward/payloads.py:28-64`); domain-separated contents hashes at `payloads.py:100-151`. So a scale-factor lookup is a per-partition, per-worker call at a reduced-graph node — external is a stage boundary (glossary: boundary op = source|reduction|repartition|materialize|external, root CLAUDE.md), so it evaluates as its own node, not fused inside a stage (`GR/execute.py:116` — `kind == "external"` is a distinct branch from `"stage"`).

### 4. Tree reduction / aggregation with N variation outputs per partition

- Fixed path: `plan_tree(n)` builds a deterministic binary combine tree; `tree_reduce` fires each combine as soon as both inputs exist — straggler-tolerant, no barrier (`EX/local/_reduce.py:1-92`). `LazyReducer` keeps only the live frontier — measured `max_frontier`, O(log N) for in-order completion (`EX/local/_reduce.py:95-164`). Adaptive path: `running_fold` chain (`EX/local/_reduce.py:182-197`).
- The distributed engine mirrors it: leaves = `process` submits, combines = `plan_tree`-shaped future dependencies, driver waits on the **single root future** (`EX/submit/engine.py:283-302`).
- Each tree node holds a full partial `V`. With variations folded into `V` (dict of N×H histograms), every frontier slot and every in-flight combine operand is N× larger; the combine itself is N independent adds. Nothing in `_reduce.py` inspects `V` — it is type-generic (`R = TypeVar("R")`, `_reduce.py:18`), so correctness is unaffected; only memory/serialization per node scales ×N.
- `pooled_combines=True` runs combines on the worker pool to avoid a serial driver bottleneck (`EX/local/executors.py:399-403`); peer reduction (`comms="ipc"/"http"`) relocates combines onto workers over `WorkerTransport` (`EX/local/executors.py:427-429, 524-556`; seam `GR/core/execution.py:240-269`).

### 5. Single-logical-output-stream assumptions a variation axis stresses

- `Plan`/`ExecResult`/`Executor.run` are single-valued (`GR/core/execution.py:206-233`) — a variation axis must live **inside** `R`, or as N separate runs; there is no multi-plan or multi-root submission API.
- M37 monitor seam: `TaskEvent` carries `phase,key:int,worker,t,partition,...` — no output/variation dimension (`GR/core/execution.py:335-351`); `Monitor.on_combine(leaves_done:int)` counts one reduction stream (`GR/core/execution.py:366-375`). N-variations-in-one-`V` renders as one stream (fine); N separate per-variation runs would produce N unrelated monitor streams with clashing `key` spaces (keys are per-plan indices, `GR/aggregate.py:107`).
- `ExecContext`/`StopCondition` count one stream: `events_done`, `errors`, `elapsed_s` (`GR/core/execution.py:177-203`) — a target-events stop over N sequential variation runs would trigger per-run, not globally.
- Journal/dead-letter partition tag is `uri@start:stop` only (`GR/checkpoint/runner.py:161-162`); with N per-variation plans the `task_id` disambiguates but the human-audit tag does not.
- `aggregate_plan` requires **exactly one partitioned source** per session (`GR/aggregate.py:89-93`) and column projection is the union over outputs (`GR/aggregate.py:101`) — shift variations that touch extra branches widen every partition read for all variations in the merged-plan approach.

### 6. Straggler / retry / dead-letter per variation subgraph

- Retry policies operate on `(partition, process)` and are variation-blind: `RetryN`, `RetryElsewhere`, `RetrySmallerChunk` re-run the **whole** `process` (all N variations) on the failed partition/sub-ranges (`GR/checkpoint/retry.py:56-148`). A failure in one variation's branch dead-letters the whole partition's N-variation partial (`GR/checkpoint/runner.py:100-109`), with an `error_budget` stop (`runner.py:107-109`).
- Dead-letter descriptor captures task_id, partition, and StageError provenance (user file/line/op) (`GR/checkpoint/errors.py:16-41`) — provenance would identify *which variation's op* failed only if the varied node carries distinct provenance.
- Distributed retries: the engine passes `retries=3` per submit (`EX/submit/engine.py:229, 288, 299`); dask honors per-task retries, parsl/HTEX cannot (`per_task_retries=True` at `EX/dask_backend/backend.py:36` vs `False` at `EX/parsl_backend/backend.py:37`) — so per-variation-granular retry policy cannot rely on backend capabilities.
- Straggler tolerance is per-leaf, inherited by anything inside `V` (`EX/local/_reduce.py:6-10`): a slow partition delays all N of its variations equally; it cannot delay one variation independently because the partition is the scheduling atom.

## ASSESSMENT / LESSONS

- **"N almost-identical plans deduped by the Store" does NOT hold today.** Keying is whole-IR-granular (`plan.py:171-176`): any varied node changes every task_id, so the unvaried 90% recomputes N times, and the only executor consulting the Store at all is the sequential `run_resumable`. Refuted by construction, not by accident — fixing it needs per-stage subgraph content hashes in the task-id domain (an IR/plan change), or a different decomposition.
- **The winning decomposition for WEIGHT systematics already exists**: compile nominal + all weight variations as extra outputs of ONE `aggregate_plan`. Interning/CSE collapses the shared event selection to single nodes computed once per partition (`GR/aggregate.py:1-11`, `graphed_core.pyi:38`); the SF `External` evaluates once per partition on the worker; `reduce` emits a dict of N weighted histograms as `V`. Zero executor changes; cost ≈ nominal + N extra fill ops.
- **SHIFT systematics fit the same mold** if expressed as N output branches of one IR: the varied kinematics fork at the shift node; everything upstream (I/O, decompression, unvaried objects) shares via interning; everything downstream duplicates as real nodes. That is compute-optimal per partition (dask-awkward could never do this cheaply; graphed's incremental reduction can). The cost is graph width (~N× the post-shift subgraph — acceptable, it is the actual work) and the union column read.
- **Per-variation separate plans** are only attractive for resume/checkpoint granularity and match RDataFrame `Vary`'s independent-loop fallback — but with current keying they buy no sharing and lose the single-pass I/O. UNVERIFIED: no benchmark of merged vs per-variation plan cost was run here.
- **Executor-level awareness is NOT needed for correctness** — `R` is opaque end-to-end (`_reduce.py:18`, `engine.py:301`). It IS needed for: variation-labeled monitoring (M37 `TaskEvent` has no axis), per-variation memory accounting in fan-in (frontier × N), variation-granular retry/dead-letter (today the partition is the failure atom), and result delivery keyed by name rather than output position (`GR/execute.py:126`).

## Design implications for a graphed Vary-style node

- Make `vary` a **frontend graph transform, not an executor feature**: expand N named variations into N output subgraphs in ONE session/IR before `compile_ir`; interning + DCE/CSE give cross-variation sharing for free (`graphed_core.pyi:38`, `GR/aggregate.py:1-11`).
- Weight systematics = extra weight-array outputs feeding extra fills in the same partition pass; the correctionlib `External` runs once per partition per varied argument set (`GR/aggregate.py:57-65`) — co-computation with nominal is automatic.
- Shift systematics = fork at the shift node; the re-run region is exactly the varied node's downstream cone, discovered by the optimizer, not by the scheduler. Do NOT build N plans.
- Deliver results as a **named mapping**: today outputs are positional (`GR/execute.py:126`); the Vary frontend must own `(output, variation) -> position` and unpack `ExecResult.value` — plan a `{name: {variation: hist}}` result wrapper at the `aggregate_plan`-specialization layer.
- Partial size scales ×N through every combine and frontier slot (`_reduce.py:120-154`); for large N prefer `pooled_combines`/peer reduction (`EX/local/executors.py:399-429`) and consider chunked wire encoding of `V`.
- If Store-level cross-variation reuse is wanted (resume one variation, add a new one later), introduce **stage-granular task_ids hashed on the stage's own subgraph + its input hashes** — the current whole-IR fold (`plan.py:171-176`) makes variation-added-later invalidate everything. V2's journal `deps` field (`store.py:31-41`) is the right journal shape already.
- Keep variation names OUT of content addressing (hash the varied params, not the label), so renaming a systematic doesn't recompute; keep addresses/labels out per the AddressTable precedent (`GR/core/execution.py:276-284`).
- Add an optional `variation: str` field to `TaskEvent`/monitor events (default `""` preserves M37 pins, same trick as JournalEntry's defaulted `stage`, `store.py:31-41`) if per-variation dashboards are wanted.
- Retry/dead-letter stay partition-atomic; document that one poisoned variation dead-letters the partition's whole N-variation partial (`GR/checkpoint/runner.py:100-109`) — acceptable, since the partition read dominates.
- Column projection must union nominal + shifted branches per merged plan (`GR/aggregate.py:101`); expose per-variation projection stats so users see the read-width cost of a shift systematic.

---

# [corpus]

# Systematics requirements inventory — graphed's own pre-existing acceptance anchors

Paths: `CORPUS` = `/Users/lgray/vibe-coding/graphed-workdir/graphed-corpus`; `LATEST` = `/private/tmp/claude-501/graphed-latest` (consolidated repo); `EXEC` = `/private/tmp/claude-501/graphed-exec-check` (executors repo checkout).

## VERIFIED FACTS

### 1. Canonical systematics analysis fixture (`CORPUS/src/graphed_corpus/analyses/systematics.py`)

- Module docstring defines the two kinds exactly as this milestone frames them (`systematics.py:3-10`): **weight systematics** = per-event reweight, selection identical across variations; **kinematic systematics** = shift object kinematics, "*changes the selection itself* and the observables".
- **Weight systematics implemented:**
  - `_btag_weight` (`systematics.py:25-36`): per-jet SF `0.95 + 0.10*jets.btag`, `btag_up` = ×1.03, `btag_down` = ×0.97, reduced to per-event via `ak.prod(axis=1)`. Docstring: "Stands in for a real correctionlib JSON evaluation; M3/M9 replace this with an External node whose PayloadDescriptor content-hashes the correction set" (`:28-29`).
  - Photon-ID SF in `ttgamma_region` (`systematics.py:94-99`): flat SF 0.98 nominal, `pho_up`=1.01, `pho_down`=0.95.
- **Shift (kinematic) systematics implemented:** `_apply_jes` (`systematics.py:39-45`): `jes_up` scales `jets.pt` ×1.05, `jes_down` ×0.95, via `ak.with_field` — applied **before** selection.
- **Analyses:**
  - `ttbar_region` (`systematics.py:54-80`): AGC-style — ≥4 jets pt>25; regions `4j1b` (==1 b-tag>0.7) / `4j2b` (≥2); observable HT = `ak.sum(sel_jets.pt, axis=1)`; `Hist.new.Reg(40, 0, 800, name="ht").Double()`; fill weighted by `_btag_weight`. JES applied at `:60` before the pt cut, so it flows through selection.
  - `ttgamma_region` (`systematics.py:83-103`): ≥1 photon pt>20, ≥1 muon pt>30, ≥2 jets pt>25; observable lead-photon pt, `Hist.new.Reg(30, 0, 300, name="photon_pt")`.
- **Fixture matrix** (`systematics.py:107-112`): `TTBAR_FIXTURES` = 2 regions × {nominal, jes_up, jes_down, btag_up, btag_down} = 10; `TTGAMMA_FIXTURES` = {nominal, jes_up, jes_down, pho_up, pho_down} = 5.
- **Reference values:** 23 JSON files at `CORPUS/corpus/references/` (8 ADL + 10 ttbar + 5 ttgamma; listed by `ls`) — e.g. `ttbar_4j1b_nominal.json` holds `{"fingerprint": "095c6378aed020d7", "values": [...40 rounded bin contents...]}`. Fingerprint = first 16 hex of sha256 of the JSON-encoded rounded bins (`histograms.py:40-44`); rounding `STABLE_DECIMALS = 6` (`histograms.py:20`).
- **Input data:** deterministic synthetic NanoAOD-like events (`dataset.py:34-66`): `Muon/Electron/Jet/Photon/MET` collections, `Jet.btag` uniform [0,1] (`dataset.py:51`); determinism itself is frozen-tested (`tests/frozen/m05/test_determinism.py:11-27`).

### 2. Ops catalog requirements (`CORPUS/docs/requirements/ops_catalog.md`)

- Section C "Systematics, corrections, ML" (`ops_catalog.md:43-52`):
  - **weight systematic** — "reweight without changing selection (b-tag/photon SF up/down)", exercised by `ttbar_*_btag_*`, `ttgamma_pho_*` → milestone **M7** (`:47`).
  - **kinematic systematic** — "JES/JER shift that **re-runs selection** + observables", `ttbar_*_jes_*`, `ttgamma_jes_*` → **M7** (`:48`).
  - **process × variation axis** — "the AGC histogram layout" → **M7** (`:49`).
  - **correctionlib scale factor** — "SF from a content-hashed JSON (here: a stand-in fn)" → M3 (External node), M9 (payload) (`:50`).
- `ak.with_field`/`ak.zip` row is tagged "(flavor, JES)" and exercised by `systematics` (`:27`); ufuncs row also tags `systematics` (`:30`).
- Canonical-analyses section names the AGC ttbar slice as "Drives M7/M9" (`:66-67`).
- **Phase-2 list explicitly pre-registers this milestone** (`:75`): "Systematics-as-a-graph-axis (named axes / template instantiation) — cf. RDataFrame `Vary`." Same line in the consolidated copy `LATEST/docs/corpus/requirements/ops_catalog.md:75`.

### 3. Frozen `m05/test_systematics.py` (`CORPUS/tests/frozen/m05/test_systematics.py`)

- Docstring: "The two systematic kinds behave distinctly (the property M7/M9 depend on)" (`:1-4`).
- `test_kinematic_variation_changes_selection` (`:26-31`): unweighted selected-event count under `jes_up` ≠ nominal ≠ `jes_down`, with strict ordering `jes_up > nominal > jes_down`.
- `test_weight_variation_preserves_selection` (`:34-38`): `btag_up == nominal == btag_down` selected counts — **the invariant defining a weight systematic**.
- `test_variations_produce_distinct_histograms` (`:41-46`): all 5 ttbar-4j1b variation fingerprints pairwise distinct; `test_ttgamma_variations_distinct` (`:49-54`) same for 4 ttgamma variations.
- Companion frozen tests: `test_fixtures_reproduce.py:20-36` pins fixture count to exactly 23 and asserts every fixture reproduces its stored reference bin-for-bin + fingerprint; `test_catalog.py` keeps catalog↔fixtures in lock-step (`ops_catalog.md:6-7`).
- **Consolidated-repo relation:** tests moved to `LATEST/tests/frozen/corpus/m05/`, package to `LATEST/tests/_corpus/graphed_corpus/` (byte-identical: `diff -r` → "PKG-IDENTICAL"), references to `LATEST/tests/_corpus/references/`. Test diffs are only path constants + import order: `conftest.py:20` `REF_DIR ... / "_corpus" / "references"` (vs `"corpus"`), `test_catalog.py:12` `parents[4] / "docs" / "corpus"` (vs `parents[3] / "docs"`). `test_systematics.py` differs by one blank line. **Same tests, same names, relocated.**

### 4. AGC-ttbar fixtures elsewhere

- **`LATEST/tests/frozen/preserve/m9/agc.py`** — the only AGC slice recorded **through the graphed frontend** with real payloads. Docstring (`agc.py:1-8`): "reduced AGC ttbar slice ... an **ONNX model**, **correctionlib scale factors**, and **systematics** (JES kinematic + correctionlib weight up/down)". Mechanics:
  - Real correctionlib v2 JSON with a `systematic` **category axis** {nominal, up, down} binned in njet (`agc.py:38-66`); real ONNX Gemm+Sigmoid model (`agc.py:69-90`).
  - `record()` (`agc.py:94-118`): **variation is a build-time config**, not a graph axis — `config={"systematic", "jes_factor", "min_btag"}`; JES = `ev.Jet.pt * jes` before selection (`:106`); weight = correctionlib SF × ONNX score via `record_external` (`:113-117`). One graph per variation.
  - `LATEST/tests/frozen/preserve/m9/test_reproduce.py:49-60` `test_systematic_variations_change_the_result`: builds 3 separate bundles (nominal / correctionlib `up` / `jes_factor=1.05`) and asserts `reproduce()` outputs differ — weight variation moves the weighted histogram, JES moves selection/observable.
- **`LATEST/tests/frozen/core/m4/test_systematics.py`** — the graph-scaling anchor. `_systematics()` (`:11-25`) builds shared selection chain + N per-variation observable→weight tails combined by adds — "the structure the AGC systematics graph has". Frozen asserts: reduced node count **equal** for 50 vs 500 variations and ≤ 5 (`:28-36`); ~10,000-node graph (3300 variations × depth-100 selection) reduces in **< 1 s** to ≤ 8 nodes with a >1000× node reduction (`:39-53`).
- **`LATEST/tests/frozen/awkward/m3/analyses.py:116`** — "AGC ttbar object-selection slice: >=4 jets pt>25, exactly 1 b-tag (4j1b region) -> HT" — nominal only, no variations.
- **Executors repo has NO systematics fixture.** `grep -rln -i "ttbar|systemat|variation"` over `EXEC/tests/frozen/` (m7…m47) returns nothing; frozen m7 end-to-end is a MET histogram (`EXEC/tests/frozen/m7/test_hep_endtoend.py:14-25`, `analyses.py:76-107`) plus ADL integration. The "AGC ttbar slice end-to-end" bit-for-bit requirement is discharged at the corpus-reference level (m05) and bundle level (m9), **never through an executor with variations**.
- **coffea-benchmarks fork** (`/Users/lgray/vibe-coding/coffea-benchmarks-graphed-mvp/`): ADL q1–q8 ports + benchmarks only; `grep -il "systemat|variation|jes|btag_up"` over its `.py`/`.md` → no hits. Not a systematics source (ADL benchmarks have no systematics).

### 5. `graph_bloat_note.md` (`CORPUS/docs/graph_bloat_note.md`; identical topic copy at `LATEST/docs/corpus/graph_bloat_note.md`)

- Mechanism (`:9-22`): dask-awkward = one layer per awkward call, one task per (layer × partition); two multipliers: ~20–60 ops per ADL query / several hundred per AGC region, and **"each kinematic variation re-runs the whole selection+observable subgraph"** → `O(base_ops × R × S)`; full AGC weight+JES/JER+b-tag set reaches **O(10⁴) nodes** (`:16-17`); dask blockwise fusion effectively O(N²) in layers (`:19-20`).
- Numbers table (`:30-34`): ADL q5 ~25 ops; AGC ttbar nominal ~120 ops × 2 regions ≈ 240; full systematics ×5 (fixture) ≈ 1.2k, ×50+ (real) = **O(10⁴)**.
- Binding M4 gates it set (`:41-46`): 10,000-node systematics graph reduces < 1 s to O(stage); AGC stage-graph node count **independent of variation count**; CI fails on super-linear reduction across {1k,2k,4k,8k}. (First two are the frozen `core/m4/test_systematics.py` asserts above; UNVERIFIED here whether the {1k,2k,4k,8k} benchmark is a separate frozen file — not searched.)

## ASSESSMENT / LESSONS

- The project already **defines** the weight-vs-shift dichotomy precisely and tests its behavioral signature (selection invariant vs selection-changing) — the Vary node must preserve exactly these two frozen invariants (m05 `test_systematics.py:26-38`).
- Everything existing treats variation as **caller-side replication**: m05 calls `ttbar_region` once per variation string; m9 builds one Session/bundle per config. No IR construct, frontend API, or executor path expresses "N variations of one graph". The catalog explicitly parked that as Phase-2 "cf. RDataFrame `Vary`" (`ops_catalog.md:75`) — the new milestone is un-parking exactly that row.
- The correctionlib fixture already models **weight variations as a category axis inside one payload** (`agc.py:56-62`: `systematic` string input) — a natural Vary hook: same External node, varied parameter.
- The m4 frozen test is the scaling contract a Vary node must not regress: reduced graph size independent of variation count, <1 s at 10⁴ nodes. A naive Vary implementation that clones the selection subgraph per shift variation re-creates the bloat the note quantifies — but hash-consing/CSE should make clones collapse; the m4 fixture proves shared substructure fuses.

### Must satisfy (existing frozen artifacts, unchanged)
- `tests/frozen/{m05|corpus/m05}/test_systematics.py` — 4 tests; the 23 stored references (`corpus/references/*.json` fingerprints incl. `ttbar_4j1b_nominal = 095c6378aed020d7`).
- `LATEST/tests/frozen/core/m4/test_systematics.py` — size-independence + <1 s reduction.
- `LATEST/tests/frozen/preserve/m9/test_reproduce.py:49-60` — variations change reproduced results.

### Must extend (gaps a Vary milestone fills)
- No frozen test runs the ttbar process×variation matrix **through graphed** (m05 is plain awkward/hist reference code); the Vary milestone's natural acceptance = reproduce the 15 stored ttbar+ttgamma variation references bit-for-bit via the frontend.
- No executor-level systematics end-to-end exists (verified absent in `EXEC/tests/frozen/`).
- "process × variation axis" catalog row (`ops_catalog.md:49`) has no graphed-side realization; m9's per-variation-rebuild pattern is the anti-pattern to replace.

## Design implications for a graphed Vary-style node

- **Two semantics, one API:** weight variations (co-computed, selection-invariant — enforceable by m05's `test_weight_variation_preserves_selection` pattern) vs shift variations (fork the graph at the varied kinematic, re-run selection downstream — m05's ordering assert `jes_up > nominal > jes_down` is the witness).
- **Vary must inject before selection for shifts:** the fixtures apply JES at `ev.Jet.pt` before any cut (`systematics.py:60`, `agc.py:106`) — the node's variation point is a column, and everything downstream of it re-derives.
- **Weight variations should ride the correctionlib category axis** (`agc.py:56-62`): vary an External node's `params={"systematic": ...}` rather than duplicating the payload — content hash stays one payload, N parameterizations.
- **Scaling contract is already frozen:** reduced stage-graph size must be independent of variation count (`core/m4/test_systematics.py:28-36`); Vary expansion must rely on hash-consing/CSE so shared pre-variation substructure appears once.
- **Acceptance anchor is ready-made:** the 15 ttbar/ttgamma variation reference JSONs + `fingerprint` (sha256 of 6-decimal-rounded bins) give bit-for-bit targets without writing new physics.
- **Histogram output layout is fixed:** process × variation set of independent 1-D `Hist`s (`systematics.py:106-112`, `ops_catalog.md:49`) — the frontend should yield a named mapping {variation → hist}, not a new histogram axis format (UHI rule: invent no formats).
- **Preservation must carry the variation set:** m9 currently bakes variation into per-bundle `config` (`agc.py:27`); a Vary node makes the variation set part of the durable IR — one bundle, N reproducible variations.
- **Naming convention exists:** `{analysis}_{region}_{variation}` with `nominal/jes_up/jes_down/btag_up/btag_down/pho_up/pho_down` — reuse it for Vary tags.
- **Executor milestone should add the missing end-to-end:** ttbar 2-region × 5-variation matrix through an executor, bit-for-bit vs the m05 references — the one AGC requirement no frozen test currently discharges.
- **Catalog bookkeeping:** move `ops_catalog.md:75` ("Systematics-as-a-graph-axis … cf. RDataFrame Vary") from Phase-2 into a milestone-tagged Section-C row, keeping `test_catalog.py` lock-step.