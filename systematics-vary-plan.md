# Systematic variations in graphed — `vary`, the variation frontend + IR treatment (execution plan)

Status: **draft for review (r3).** Anchoring doc for the work, structured like the root prompt:
rationale is context and binds nothing; PART II binds. Committed in the meta repo
(`graphed-org/graphed-project-mvp`) as a durable reference, together with its cited research and
review companions (`systematics-vary-codebase-analysis.md`, `systematics-vary-litsearch.md`,
`systematics-vary-plan-review-r0.md`). Every design claim traces to a `file:line` (Anchors appendix), a cited
section of `systematics-vary-codebase-analysis.md` (cited *cba §agent*), of
`systematics-vary-litsearch.md` (cited *lit §agent*), or an explicit stated assumption. Source
directive: the owner's high-level doc (Google Doc `116lg4…`, mirrored at
`scratchpad/systematics-plan.txt`), revised here per the owner's instruction to separate rationale
from requirements and ground every open question in measured evidence. A pre-delivery hygiene
review (4 lenses, `systematics-vary-plan-review-r0.md`) is applied in this revision; the formal
§12.1 review cycle starts from here.

> **Naming — owner-verified 2026-07-28.** Verb **`vary`** (`graphed.vary`), concept noun
> **"variation"**, container **`Varied`**. Variation labels are `f"{name}_{tag}"` underscore style
> (`jes_up`, `btag_down`); **`"nominal"` is reserved** for the central value. This matches
> RDataFrame's `Vary` precedent (lit §rdf-vary §6), graphed's lowercase-verb convention
> (`join`, `repartition`), and — verbatim — the 15 stored corpus reference names (cba §corpus §1).

## Scope deviation (flagged, deliberate — the R22.0 pattern)

The project plan lists **systematics-as-a-graph-axis** as Phase 2 in four places: the root
`CLAUDE.md` Part F block, the root prompt Out-of-scope block (header
`graphed-root-prompt.md:1284`, the bullet "treating systematic variations as a graph axis" at
`:1286`), inline in R22.0 and R22.10 (`graphed-root-prompt.md:1262,1282`), and the corpus ops
catalog ("Systematics-as-a-graph-axis (named axes / template instantiation) — cf. RDataFrame
`Vary`", `ops_catalog.md:75`). **The project owner has decided to pull it into scope now** (this
doc's source directive). Consistent with "THE PROJECT PLAN ALWAYS WINS," the deviation is
deliberate and flagged, not silent: this doc records it; the root prompt gets an **R23** entry
binding it once landed (§12.3). The pull-in is *smaller* than R22's: no new execution substrate —
the work rides the existing IR/interning, group-plan, and executor machinery, which the evidence
shows were built expecting exactly this load (Part I §1).

---

# PART I — RATIONALE (context; non-binding)

## 1. Why now: the system was built for this and the anchor tests already exist

- Systematics bookkeeping is "the largest pain point in analysis software" in the field's own
  assessment (Second Analysis Ecosystem Workshop report, arXiv:2212.04889 — lit §rdf-vary §5).
- graphed's founding rationale names variation-multiplied graphs as *the* scaling driver: "On real
  analyses with many systematic variations the graph reaches tens of thousands […]"
  (`graphed-root-prompt.md:25`); the corpus `graph_bloat_note.md` quantifies it (full AGC weight +
  JES/JER + b-tag set ⇒ O(10⁴) nodes; dask-awkward's per-layer×partition model is what died there —
  cba §corpus §5). M4's optimizer was hardened for it in advance: the egg extractor was redesigned
  O(N) specifically because recursive extraction "blows up … on the deep chains a systematics graph
  produces" (`src/optimizer/engine.rs:7-13`), and frozen `tests/frozen/core/m4/test_systematics.py`
  already pins that a 3300-variation, ~10⁴-node graph reduces in < 1 s to a node count
  **independent of variation count** (cba §corpus §4).
- The acceptance anchors pre-exist: the corpus canonical systematics analysis (weight = b-tag SF ±,
  photon-ID SF ±; shift = JES ± applied *before* selection) ships 15 stored reference histograms
  with fingerprints and the behavioral frozen tests `test_weight_variation_preserves_selection` /
  `test_kinematic_variation_changes_selection` (strict `jes_up > nominal > jes_down` selected-count
  ordering) — `tests/frozen/corpus/m05/` in the consolidated repo (cba §corpus §1,§3).
- What exists today is caller-side replication only: m05 calls the analysis once per variation
  string; the m9 preservation fixture bakes the variation into per-bundle build config ("one graph
  per variation", `tests/frozen/preserve/m9/agc.py:94-118`); no frontend/IR construct expresses
  "N variations of one graph" (cba §corpus, "Assessment"). The ops catalog parked exactly this row
  as Phase 2; this plan un-parks it.

## 2. Prior art and its hard lessons (digest — full evidence in the two research docs)

**RDataFrame `Vary`** (lit §rdf-vary). The precedent this work takes its name and user model from.
Register-then-forget: `Vary(col, expr, tags, name)` attaches variations to a column; propagation
through downstream `Filter`/`Define`/actions is automatic; `VariationsFor(result)` yields a keyed
result map (`"nominal"` + `name:tag`); everything runs in **one event loop**, sharing I/O and all
computation not downstream of the varied column. Internally ROOT hand-implements the sharing:
copy-on-write column registers, per-variation cloned Defines/Filters that are **skipped when
unaffected** ("varied universes", `RDefine::MakeVariations`, `RFilter::GetVariedFilter`) — and
within a universe, *every* use of the varied column coheres (whole-cone substitution). Its weak
spots, learned the hard way: varied results lack first-class identity (file-write name collisions),
no varied `Report`/cutflow, Snapshot needed a bolt-on per-event validity bitmask because varied
selections diverge, and the extraction API sat in `Experimental` for 4+ years.

**WRemnants / narf** (lit §rdf-users §1-3). The precision-analysis end **refuses per-variation
control flow entirely**: zero uses of `Vary` (grep-verified). Weight systematics are per-event
Eigen **tensor** columns filled into extra histogram axes in one pass (one atomic shared histogram,
O(1) memory in thread count); even genuinely kinematic effects are beaten into weight vectors or
alternate-column fills; cut migration becomes histogram axes applied at fit-prep. Nuisance naming,
symmetrization, envelope collapse, decorrelation all happen **outside the loop** as histogram
transforms. Lesson: the labeled-axis fill is the proven scaling shape, and bookkeeping must not
live in the event loop.

**mkShapesRDF (Latinos)** (lit §rdf-users §4). The config-driven end: a declarative nuisance
registry (`{name, type ∈ lnN|shape, kind ∈ weight|suffix|envelope…, samples: {sample: exprs}}`)
compiled into `Vary` calls; weight nuisances native-`Vary` the weight column, kinematic ones come
from pre-produced friend trees. They had to **reimplement `Vary`** for the Snapshot stage
(suffixed-column defines + OR-of-cuts), prune variations whose base column no output uses, and
rename every extracted histogram to dodge ROOT name clashes.

**coffea** (lit §coffea-sys). Three disjoint mechanisms glued by string conventions: `Weights`
(weight-type only; stores variations as `var/nominal` ratios, auto-symmetric Down — the right
economics), the jetmet factories + shift loop (`shifts` list of collection-replacement dicts;
**the whole selection re-executes per shift**, nothing dedups), and dataset-level variation samples.
The in-IR `add_systematic` prototype stalled for ~4 years: it materialized variations as columns
(solving storage, not propagation), left selection propagation a documented TODO, and left the
combinatorics abstract method (`explodes_how`) an unimplemented joke. Lesson, verbatim from the
evidence: **variation forking is a graph-transformation problem, not a data-layout problem** — and
coffea Discussion #469 measured 2-8× wins for vectorized (extra-axis) systematics over re-run loops.

**Pythonic analyses** (lit §pythonic-analyses): nsmith-/boostedhiggs, PocketCoffea,
TopEFT/topeft + cmstas/ewkcoffea.
**Kelci's analysis — CONFIRMED (owner, 2026-07-30): `cmstas/ewkcoffea`**, promoted to the
canonical exemplar with a dedicated deep-dive over both its eras (lit §ewkcoffea-confirmed;
`main@063e8d7` = coffea-0.7-era, branch `coffea2023@63abb06` = dask-era port). The 0.7-era
treatment is the field's mature form: 12 weight bases → 24 labels under combine-datacard names
encoding correlation scope, 6 object-shift labels by column swap, a 7-pass outer shift loop
re-running selection + a BDT, the nominal-only exclusion rule explicit in code, and the Weights
registry **hand-partitioned by shift-impact** ("these weights can go outside the sys loop since
they do not depend on pt of mu or jets") — a human-judgement impact analysis. The **dask-era port
is the highest-value evidence in the survey**: migration changed *none* of the systematics
semantics but forced the analyst to hand-write CSE inside the physics processor
(`masked_val_cache`/`masked_weights_cache` — interning re-implemented in user code), degraded
`deepcopy` to `copy` + "TODO do we need copy here?", and abandoned persisting the built task graph
(`# Does not work` above a commented `cloudpickle.dump`) — the variation-expanded artifact could
not be saved, shipped, or inspected. No dask-era version of the analysis ever carried an object
shift (falsified as a migration casualty: the empty `obj_correction_systs` predates the branch),
and a latent `hout = {}`-inside-the-shift-loop bug would silently keep only the last shift the
moment one is added — the dask-era shift-loop cost is therefore UNVERIFIED there.
**`FNALLPC/wwz4l` — resolved (access granted 2026-07-30; lit §ewkcoffea-confirmed addendum):**
named as a modern-coffea version, it is **measured to be neither** — a coffea-0.7-era CMS-DAS
teaching derivative of `ewkcoffea@main` (`main@cc71718`; 522 identical processor lines;
byte-identical `ApplyJetSystematics`; zero dask/`dataset_tools`/`hist.dask` surface repo-wide,
independently re-verified). It carries the full weight+shift treatment (27 labels) and adds no
dask-era evidence, so `coffea2023@63abb06` remains the sole modern-coffea exemplar and the
no-dask-era-object-shift finding extends to it. Its distinct value: the teaching strip removed
every piece of *physics* (BDT, EFT, 54→14 categories) while the **variation scaffolding survived
completely intact** — the loops, deepcopies, exclusion rule, growth axes, and suffix generator are
irreducible accidental complexity by construction, which is precisely what `vary` deletes.
Universal conventions across all four surveyed: `"nominal"` reserved; `Up`/`Down`-suffixed labels;
**shift × weight cross products never produced** (under a kinematic shift, only the central weight
fills — evaluated on that shift's selection); one histogram with a `systematic` StrCategory axis;
data special-cased (no shifts, no variation axis). Universal failure modes: whole-chain
re-execution per shift; defensive `copy.deepcopy` of accumulate-by-mutation Weights;
hand-maintained name lists where a typo silently drops a systematic; per-variation cutflow
clobbering; skim-vs-shift interaction requiring an OR-of-selections mask.

## 3. Why this architecture: record-time expansion + interning, not a new node kind

Three candidate shapes were evaluated against the measured codebase (cba §ir-rust, §optimizer,
§frontend-python):

1. **A first-class boundary `Vary` NodeKey** (Exchange/Join sibling). Rejected for the core
   mechanism: every non-`Op` kind is automatically a stage boundary (`src/node.rs:102-103`) and
   boundaries **end stages** — a Vary node between a kinematic op and the cuts would forbid fusing
   the varied suffix, defeating M4. It would also carry the full M40 checklist (serialize tags,
   optimizer arms, both backends, `evaluate_ir`) *plus* semantics no existing node has (downstream
   multiplicity), a strictly larger blast radius than Exchange/Join (cba §optimizer, "Assessment").
2. **IR-level variation annotation + plan-time expansion** (RDF's internal model). Rejected:
   RColumnRegister/MakeVariations is ROOT *hand-implementing* the sharing that graphed's
   hash-consing provides structurally. Rebuilding it as IR metadata re-derives what interning gives
   for free and pushes variation-awareness into optimizer, projection replay, and executors.
3. **Record-time expansion + hash-consing** (chosen). The frontend re-records the downstream ops
   per variation; `GraphStore::intern` returns existing ids for every node not downstream of the
   varied input (`src/store.rs:73-88`), so the unvaried prefix is shared **exactly** — measured:
   going N=1→2 variations grows the arena by precisely the varied suffix (Δ = D+2 nodes), reduction
   stays linear (128 variations × 50-op chains: 12.9× nodes → 11.9× time, 16.7 ms), and the reduced
   form is one shared-prefix stage + one stage per variation (cba §optimizer §2,§5). DCE, fusion,
   projection, determinism, and every executor need **zero changes** for correctness — `R` is
   opaque end-to-end (cba §exec-checkpoint §4).

The source directive's open question — "is it useful to add optimization impact analysis to isolate
subgraphs a variation must re-run?" — **resolves to: it already exists structurally.** The impact
set of a shift IS the set of nodes reachable from a label's outputs but not from nominal's; RDF
computes the same thing by hand with dependency-tracked clone caches. We expose it as a trivial
read-only API (§3.4), and build no invalidation machinery (none exists and none is needed —
grep-verified, cba §optimizer §5).

Weight vs shift needs **no API distinction** (RDF lesson: the dependency structure discovers the
difference — a varied weight only reaches the fill; varied kinematics reach the cuts). It does need
**distinct lowering economics** at the sink, which §4/§5 bind separately.

## 4. Honest costs (the requirements in PART II that mitigate each)

- **Build-time cost**: expansion re-executes the user's downstream *recording* code per variation
  (Python-side). Mitigated by the incremental reducer (per-step cost ∝ delta) and bounded by a
  variation-shaped anti-quadratic benchmark (§3.3).
- **Partial size ×N**: every reduction-tree slot carries the N-variation composite. Mitigated by
  the variation-axis fill mode (§6.2, O(1) objects) and `pooled_combines`/peer reduction; gated by
  the milestone benchmarks (§10).
- **Checkpoint granularity**: `task_id` folds the **whole plan IR** (`plan.py:164-176,286-301`), so
  adding a variation later invalidates every cached task even though the graph shares nodes.
  Documented limitation (§7.3); stage-granular content addressing is named Phase-2 follow-up (§11).
- **Union projection**: a merged plan reads the union of nominal + shifted columns for all
  partitions (`aggregate.py:101`). Accepted for MVP; per-variation projection stats surface the
  cost (§5.3).
- **Boundary interaction**: the m39/m40 plan builders consume exactly one Exchange/first Join
  (`shuffle.py:170,232`); v1 therefore restricts variations from crossing shuffle boundaries
  (§5.4) rather than silently miscompiling.

---

# PART II — REQUIREMENTS (binding; specific)

## §1 Vocabulary (owner-verified)

- **§1.1** Verb `graphed.vary`; container `graphed.Varied`; concept "variation" everywhere (docs,
  APIs, tests, R23). The reserved central label is the string `"nominal"`; user variation labels
  are `f"{name}_{tag}"` (e.g. `jes_up`); `vary` MUST reject a user label equal to `"nominal"`,
  duplicate labels (within the container or colliding with inherited labels, §2.1), and empty tag
  sets, at call time.
- **§1.2** In the expansion/sibling-fill lowering (§4, §5, §6.1), variation labels are **frontend
  metadata, never structural identity**: a label MUST NOT enter `NodeKey` params, tokens, or
  content hashes. Two variations with structurally identical content intern to the same nodes
  (dedup is correct: renaming a systematic must not recompute — the AddressTable
  label-out-of-hash precedent, `execution.py:276-284`). Only real content differences (a different
  input id; a different correctionlib `systematic=` param) fork identity. **Carve-out (§6.2):** in
  variation-axis fill mode the labels become *output content* — StrCategory bin identities in the
  histogram spec — and there they DO enter the spec/params/content hash, by design; renaming a
  systematic in axis mode legitimately changes the output histogram.

## §2 Frontend semantics: `vary` and `Varied`

- **§2.1 (API.)** `graphed.vary(nominal: Array | Varied, variations: Mapping[str, Array | Varied],
  *, name: str) -> Varied` — a **neutral module verb** exported like `join`/`repartition`
  (`shuffle.py:92-96` precedent; per the factorization rule it is not an `Array` method, not gak,
  not numpy-idiom). Keys of `variations` are tags; the new labels are `name_tag`.
  **Stacking**: when `nominal` is itself a `Varied`, the result inherits its labels (members pass
  through unchanged) and adds the new labels; a new label's member is the provided value's central
  universe (`.nominal` if the provided value is itself `Varied`, else the Array as given). Each
  label therefore differs from `"nominal"` in exactly **one** knob — the one-at-a-time rule is
  structural, and a weight variation layered on a shift-propagated weight (the corpus b-tag-on-JES
  case, `systematics.py:74-76`) is expressible without cross products.
  All member Arrays MUST share one Session, have compatible forms (backend `op_form`-checked at
  construction), and root in the same partitioned-source set (checked at construction; the
  otherwise-deferred failure surface is `aggregate_plan`'s single-source check,
  `aggregate.py:89-93`). Lockstep multi-column variation (jet pt+mass shifted together) is
  expressed by varying a record Array — the corpus JES fixture already does this via
  `ak.with_field` (`systematics.py:39-45`); no second verb.
- **§2.2 (`Varied` is a mapping of universes.)** `Varied` holds `{label: Array}` with `"nominal"`
  always present; exposes `.labels` (ordered: nominal first, then insertion order; inherited labels
  before new ones under stacking), `.nominal`, `[label]` (KeyError on unknown label lists the valid
  labels), and `.apply(fn)` — apply a record-time `Array -> Array` function per universe. (Named
  `apply`, NOT `map`: `Array.map` is an execution-time data callable, `array.py:377-379`; the two
  contracts must not share a name.) `fn` MUST return an `Array`; if it returns a `Varied` (because
  it closed over another container), `.apply` raises with guidance to combine containers via
  ordinary ops instead. `Varied` is a plain frontend object — no IR type, no new NodeKey (§3.1).
- **§2.3 (Broadcast propagation — four bound dispatch points.)**
  (a) **`Varied` implements the full `Array` dunder surface** by mapping over labels — enumerated
  at implementation from `array.py` and including `__array_ufunc__` (`array.py:156`), the bitwise
  set (`__and__/__or__/__invert__`, `array.py:245-275`), `__getitem__`, field access, and all
  reflected variants; parity is gated by a frozen test iterating the dunder inventory.
  (b) **Plain-`Array` entry points learn `Varied`**: `Array.__getitem__` and `Array.filter`
  currently reject non-Array keys (`array.py:344-375`) and there is no reflected protocol for
  subscription — both gain an explicit `Varied`-mask branch delegating to the container (the corpus
  requires it: unvaried `photons`/`muons` sliced by a JES-varied selection, `systematics.py:91-92`).
  (c) **The gak layer gets one dispatch mechanism plus a bound per-function classification** —
  "one wrapper, zero per-function thought" is falsified by the measured surface (review r0), so the
  classification is explicit, lives in code, and is gated by a frozen exhaustiveness test (every
  public gak function classified; no silent default): *broadcast* (elementwise/structural default),
  *container-traversing* (`gak.zip`/`concatenate`/… detect `Varied` **inside** their
  Mapping/Sequence arguments), *tuple-returning* (`gak.unzip`/`broadcast_arrays` return a tuple of
  `Varied`), *eager-metadata* (`fields`/`type_of`/… answer on the nominal member — sound because
  §2.1 requires form compatibility), and *refusing* (`gak.join` and boundary verbs, per §5.4).
  Signatures do not change (R17.0 anti-drift preserved).
  (d) **Module verbs and sinks**: `graphed.join`/`repartition` refuse `Varied` inputs with the
  §5.4 error; `Histogram.fill` accepts `Varied` (§6).
  Broadcast recording happens while the *user's* frame is on the stack, so `capture()` attributes
  each varied node to the user's own op line with no provenance copying (`provenance.py:66-79`
  skips graphed frames).
- **§2.4 (Combination rule — label-aligned union; one-at-a-time; no cross products.)** When an
  operation combines `Varied` inputs — including a `Varied` combined with one derived from it
  (`jets[jets.pt > 25]` is the canonical case) — the result's labels are the **union**, and for
  each label L every container contributes **its own member for L when present, else its
  `"nominal"` member**. Within a universe L, all uses of varied quantities are therefore coherent
  (RDF's whole-cone-substitution semantic). Because §2.1 makes each label belong to exactly one
  knob, cross products can never arise implicitly: at a fill combining shift-varied kinematics with
  a stacked weight `Varied`, shift labels fill with the central weight *as evaluated in that
  shift's universe* (label-aligned), and weight labels fill with nominal kinematics — exactly the
  corpus reference semantics (`systematics.py:74-76`) and the universal exclusion convention
  (lit §pythonic-analyses).
- **§2.5 (Validation over convention.)** Silent-drop failure modes from the survey become errors
  or diagnostics: unknown label on `[label]` → KeyError listing valid labels; form-incompatible or
  cross-Session/cross-source member → construction-time error naming the label; `vary()` registers
  each container with its Session (weak reference), and `compile_ir` diagnostics report any
  registered label that reaches no marked output (DCE already prunes the work; the diagnostic
  prevents the mkShapesRDF silent-cost case).

## §3 IR and optimizer treatment

- **§3.1 (No new NodeKey.)** No Rust IR variant, no serialize tag, no optimizer change is added for
  variations. The varied universes are ordinary nodes; sharing is interning
  (`src/store.rs:73-88`); the m4 frozen scaling contract
  (`tests/frozen/core/m4/test_systematics.py`) continues to bind unchanged. Any future first-class
  node (introspection-driven) is Phase 2 and follows the full M40 checklist (cba §ir-rust §1).
- **§3.2 (Determinism.)** Expansion order is deterministic: labels in `.labels` order, recording
  per §2.3. Two-run byte-identical compilation of a variation-expanded graph is a frozen m48
  anchor (§10) in the strong R22.3 form (fresh processes, differing `PYTHONHASHSEED`).
- **§3.3 (Anti-quadratic guard gains a variation topology — in a NEW frozen file.)** A new frozen
  benchmark (`tests/frozen/core/m49/…`, replicating the `test_benchmark.py:10,40-53` pattern;
  **the m4 files are untouched** — frozen tests are read-only, §B.6) pins the variation shape:
  shared prefix + N varied suffixes where **each variation is a separately marked output** (the
  real `vary` topology — the m4 `_systematics` builder funnels all variations into one output and
  would make the assertion vacuous, review r0), N ∈ {16, 32, 64, 128}, asserting the exact reduced
  shape for the fixed topology (`stages == N + 1`, `reduced_nodes == 2N + 2`) and a linear-growth
  bound (time(128)/time(16) < 24.0, the m4 threshold style). The underlying measurement is in
  Part I §3; the frozen test pins it so it stays true.
- **§3.4 (Impact-set API.)** A read-only frontend helper reports, per label, the **reachability
  difference** `reachable(label's outputs) − reachable(nominal outputs)` computed via
  `session.walk` — NOT an id watermark (interleaved broadcast recording makes watermark
  bracketing order-dependent and wrong for labels sharing derived nodes, review r0). The result is
  independent of expansion order; a node shared by `jes_up` and `jes_down` but not nominal appears
  in **both** impact sets. This is the RDF `RVariationsDescription` analogue and the §5.3
  projection-stats input; it is frozen-anchored in m49 (§10).

## §4 Weight-path lowering

- **§4.1** A weight variation is a `Varied` whose members are per-event weight Arrays (any source:
  arbitrary expressions, or a correctionlib `External` evaluated per label). The **canonical
  correctionlib form varies the existing `systematic` category parameter** of ONE payload
  (`preserve/m9/agc.py:56-62` fixture precedent): same `content_hash`, N parameterizations — the
  payload is never duplicated (§A.3.1 reproducibility). Weight variations routinely require a
  **per-dataset scalar normalization** — the sum-of-weights rescaling (`sow/sow_renormUp`, with
  per-sample LHE-index branching) appears in both eras of the confirmed exemplar
  (lit §ewkcoffea-confirmed) — and the frontend has no constant-Array constructor: the binding v1
  form is arithmetic on an existing per-event Array (the m48 anchor names it); a constant/scalar
  broadcast helper is parked in §11.
- **§4.2** Fills accept a `Varied` entry in the M29 `weight=[...]` factor list (`boost.py:166-174`);
  lowering emits the nominal fill node + one sibling fill node per label under the §2.4 rule,
  differing only in the varied input ids — everything upstream interns. All siblings join the
  **same group plan**; the single-pass property is frozen-witnessed on the corpus run itself in
  m48 (§10), not only on a toy graph.
- **§4.3** Weight variations MUST NOT change selection. The frozen m48 anchor is **structural**,
  not only behavioral (equal counts is a tautology under §3's expansion — the selection nodes are
  the same interned ids by construction, an R0.10 trap flagged in review r0): the §3.4 impact set
  of every weight-only label MUST contain no node outside the fill's weight-input cone
  (equivalently: the selection cone's node ids are identical across weight labels). The m05
  equal-counts check rides along as a sanity assertion.

## §5 Shift-path lowering

- **§5.1** A shift variation is a `Varied` at a kinematic quantity (column or record), created
  **before selection** — the corpus applies JES at the jets record before the pt cut
  (`systematics.py:60-61`) and the m9 AGC fixture shifts `Jet.pt` before its jet mask
  (`agc.py:106-107`); broadcast (§2.3) re-records the selection/observable cone per label;
  interning shares everything else. Cutflow divergence is the *defining* behavior and is
  frozen-gated by the m05 ordering witness (`jes_up > nominal > jes_down` selected counts) through
  the frontend.
- **§5.2 (Witnesses that sharing engaged — R0.10.)** The m49 suite pins mechanism witnesses, not
  just results: (a) **arena-delta witness on a fixed topology with a literal expected integer**
  (the m4 style — e.g. a 50-op varied chain adds exactly 52 nodes; a self-derived
  `delta == len(cone)` comparison is tautological, review r0). Labels structurally identical to a
  prior label dedup to Δ = 0 by §1.2 — that case is witnessed separately as the dedup feature, not
  under this witness. (b) **single-read witness bound to the reference-matrix run itself**: the
  read-counting partitioned source (m23 pattern) asserts `part_reads == n_partitions` — not
  `n_partitions × n_labels` — on the SAME Session/plan that reproduces the corpus references
  (§10 m49), so a per-variation re-run loop cannot pass. (c) **reduced-stage shape** — the shared
  prefix appears in exactly one stage.
- **§5.3 (Projection.)** Column projection is the union over all requested outputs — correct today
  with zero changes (`read_columns` takes `Sequence[Array]`, `projection.py:109-147`); m49 pins a
  test where a shift needs an extra column (e.g. binned SF needing `Jet.eta`) and the union grows by
  exactly that field. Per-label projection stats are exposed via §3.4 so the read-width cost of a
  shift is visible. Per-variation partition-level projection splitting is Phase 2.
- **§5.4 (Boundary restriction, explicit.)** v1 REFUSES (clear `NotImplementedError` naming the
  label and the boundary) a variation whose cone crosses an `Exchange`/`Join` node — the m39/m40
  plan builders are single-boundary (`shuffle.py:170,232`) and silent miscompilation is worse than
  refusal. The refusal test carries a **positive control**: a variation entirely *downstream* of a
  Join/Exchange compiles and produces correct results (a blanket "Varied near Join raises" must
  fail the suite). Generalizing the builders is named Phase 2 (§11).

## §6 Histogram integration

- **§6.1 (MVP shape: sibling fills, named results.)** `Histogram.fill` accepting `Varied` axis
  values and/or `Varied` weight factors lowers per §4.2/§5.1 under the §2.4 rule. Binding result
  and lowering shape:
  (a) **Per-output label sets.** Each output's mapping carries exactly the union of labels reaching
  *that* output — `{output_name: {label: hist}}`, nominal always present; an output no variation
  reaches returns a bare `hist` (NOT `{"nominal": hist}`), so unvaried programs see today's shapes
  unchanged. Absent labels are absent, never silently duplicated from nominal.
  (b) **Structural fill-node arity.** A fill combining shift labels S and weight labels W records
  exactly `1 + |S| + |W|` fill nodes — never the product (frozen-counted via the staged-fill list,
  the §2.4 discriminator).
  (c) **The single-histogram `.plan()` path refuses varied fills**: `_SumFills` sums ALL staged
  fill nodes into one histogram (`boost.py:88-98`) and would silently merge universes; varied
  histograms route through the group-reduce path (`_GroupReduce` `{label: hist}` generalized to
  two-level keys, `boost.py:100-122`), and `.plan()` on a varied `Histogram` raises, pointing at
  the group API.
  This reproduces the corpus reference layout (independent per-variation histograms — UHI, no
  invented formats).
- **§6.2 (Scaling shape: the variation axis, m50 — weight labels only.)** An opt-in fill mode
  lands **weight-label** variations in ONE histogram with a **non-growth, pre-declared, sorted
  StrCategory `"variation"` axis** via an evaluator-side loop (extend/sibling `FillEvaluator`;
  labels ride the spec/params under the §1.2 carve-out; scalar-string broadcast and non-growth
  combine-safety are probe-verified — cba §histogram §3). **Shift labels always lower as sibling
  fill nodes** — their per-label axis columns have diverging lengths (§5.1 cutflow), which the
  single-weight-loop evaluator shape cannot carry — **but a shift sibling MAY target the same
  pre-declared variation axis**, writing its label as the scalar category value of its own fill:
  one histogram carrying both classes, filled from separate passes with a scalar label, is the
  field's actual layout in both eras of the confirmed exemplar (lit §ewkcoffea-confirmed), and
  scalar-string broadcast is probe-verified. The m50 equality anchor covers both the weight-label
  evaluator loop and a mixed shift+weight program landing in ONE axis-mode histogram equal to its
  sibling-fill decomposition.
  Non-growth is required: identical spec per partition keeps `+` combine safe and deterministic
  (PocketCoffea's deterministic pre-declared axis lesson; growth axes stay Phase 2 per the existing
  `_spec.py:70,74` refusal). M29's identity discipline binds: new params/spec content only when the
  feature is used.
- **§6.3** Data / no-variation paths are unchanged, gated by both in-tree golden patterns (review
  r0): a **committed golden GIR blob** for an unvaried fill graph (the
  `core/m40/test_join_serialize.py:84-99` pattern) plus **params-key absence** (`assert
  "<new key>" not in node["params"]`, the `m29/test_multi_weight_fills.py:93-99` pattern).

## §7 Execution, results, checkpoint

- **§7.1** One Session, one IR, one plan for nominal + all variations; executors are untouched
  (`R` opaque through `Plan`/tree-reduce/engines — cba §exec-checkpoint §1,§4). No per-variation
  execution loop may be introduced anywhere.
- **§7.2** The frontend owns `(output, label) → position` and unpacks results into the §6.1 named
  mapping. `ExecResult`/`Plan`/monitor schemas do not change in m48–m50 (per-variation monitor
  events: Phase 2, the defaulted-field trick documented — `store.py:31-41` precedent).
- **§7.3 (Checkpoint semantics, documented honestly and anchored.)** Within one plan, resume works
  per-partition exactly as today (the N-variation composite partial is the journal unit) — m49
  freezes an interrupt/resume test over a varied graph whose result is byte-identical to an
  uninterrupted run. Across plan revisions, adding/removing a variation changes the IR and
  therefore **every** `task_id` (`plan.py:164-176,286-301`) — no cross-revision reuse. This
  limitation MUST be documented in the user docs and design.rst — naming the canonical
  invalidating edit from the exemplar workflow: toggling the expensive shift class on or off
  between runs (the `skip_obj_systematics` pattern, lit §ewkcoffea-confirmed) rebuilds the IR and
  invalidates the whole cache. Stage-granular content addressing is the named Phase-2 fix (§11).
  Blob storage stays content-deduped (`store.py:62-73`).
- **§7.4** Retry/dead-letter stay partition-atomic; docs state that one poisoned variation
  dead-letters the partition's whole composite (`runner.py:100-109`); the dead-letter surface names
  the guilty label via the §8 StageError (asserted inside the §8.2 frozen test).

## §8 Debug, errors, provenance

- **§8.1** `StageError` gains `variation: str = ""` — constructor field, `summary()` line,
  `__eq__`/`__hash__` participation (`debug/errors.py:32-81`); pickling rides the existing
  `__dict__` `__reduce__` for free. Empty string = nominal/unvaried (backward compatible).
- **§8.2 (Label transport — mechanism bound.)** Under §1.2 the label is not in the IR and under
  §2.3 all sibling nodes share the user's source line, so op+frames cannot disambiguate labels
  (review r0). The bound mechanism: the frontend's **node-id → label map travels the same
  process-closure channel that already delivers per-node provenance to worker-side StageError
  construction** (`debug/runner.py:20-45`; closures ship via the plan's OpSpec payload,
  `aggregate.py:54,96-104`) — no `Plan`/`ExecResult` schema change; the worker sets
  `StageError.variation` from the failing node id at construction. Frozen m49 anchor: a failure
  raised inside the `jes_up` universe on a worker across a process boundary re-raises driver-side
  carrying `variation == "jes_up"` AND the user's analysis line (M6 contract extended, not
  altered), and the dead-letter descriptor shows the label (§7.4).
- **§8.3** Per-node provenance needs no new machinery (§2.3): varied nodes record at user op lines.
  `to_dot`/debug labels remain readable; the impact-set API (§3.4) is the "which nodes belong to
  which label" view.

## §9 Preservation and introspection

- **§9.1** `Varied.labels`, the §3.4 impact API, and a plan-level listing of
  `{output: [labels]}` constitute the introspection surface (RDF `GetVariations` analogue); the
  listing is frozen-anchored inside m50's `inspect()` test (§9.2).
- **§9.2** Preservation: a bundle built from a variation-expanded graph reproduces **all** labels
  from ONE bundle, in the m9 comparison form (per label,
  `np.array_equal(reproduce(bundle)[label], build_time[label])` — the genuinely bit-exact
  in-process form, `preserve/m9/test_reproduce.py:19-23`), and `inspect()` lists the labels without
  executing. This replaces the m9 fixture's one-bundle-per-config pattern *additively*: existing
  m9 frozen tests are untouched.

## §10 Milestones (strictly ordered; m48 → m49 → m50)

Numbering: the executors repo froze m47 last. Frozen layouts by repo: consolidated `graphed` =
`tests/frozen/<pkg>/m48…`; `graphed-executors` = flat `tests/frozen/m49…`;
**`graphed-histogram` = flat `tests/frozen/m48…`** (its existing shape — `m23/`, `m29/`).
Each milestone runs the full §12 process. Frozen anchors listed here are the acceptance skeleton
the test-author starts from; the frozen m05/m4/m9/m23/m29 artifacts are **binding and unchanged**.

- **m48 — `vary` frontend + weight path** (repos: `graphed` + `graphed-histogram`).
  Targets: §1, §2, §3.2/§3.4 (API only), §4, §6.1, §6.3. Frozen anchors:
  - Corpus **weight**-variation references through the frontend — ttbar 4j1b/4j2b ×
    {nominal, btag_up, btag_down} (6) + ttgamma {nominal, pho_up, pho_down} (3) = **9 of the 15
    refs**, `fingerprint(h) == ref["fingerprint"]` and `bin_values(h) == ref["values"]` (the
    `m05/test_fixtures_reproduce.py` comparison form). Note: the ttgamma flat SF weight is a
    constant — expressible only as arithmetic on an existing per-event Array (no constant-Array
    constructor exists, cba §histogram §1); the anchor says so to spare the test-author the
    mid-freeze discovery.
  - §4.3 structural selection-invariance (impact set of each weight label ⊆ weight-input cone;
    m05 equal-counts as sanity).
  - Single-pass read witness **on the reference-matrix run** (§5.2b applied to the weight matrix).
  - §3.2 determinism: same varied program compiled in two fresh processes under differing
    `PYTHONHASHSEED` → byte-identical `compile_ir` output; `.labels` order pinned
    (nominal-first + insertion order).
  - §6.3 goldens (committed GIR blob + params-key absence).
  - §2.3 dunder-parity and gak-classification exhaustiveness tests; §2 validation errors (§1.1,
    §2.5); §2.4 label-aligned combination on a Varied-meets-itself program.
  - §4.1 correctionlib single-payload multi-parameterization.
- **m49 — shift path + impact + executor end-to-end** (repos: `graphed` + `graphed-executors`).
  Targets: §3.3, §3.4 (frozen anchor), §5, §7, §8. Frozen anchors:
  - The **full 15-reference matrix** through the frontend (fingerprint-exact, as m48) AND through a
    process-pool executor — fingerprint-exact vs the references plus a separate run-to-run
    `array_equal` determinism assertion (the m29 dual-assert precedent; "bit-for-bit" is claimed
    only run-to-run, not vs the rounded references — review r0). The §5.2b read witness binds to
    this same run. This is the executor-level systematics end-to-end no frozen test currently
    discharges (cba §corpus §4).
  - m05 ordering witness (`jes_up > nominal > jes_down`) through graphed.
  - §5.2 witnesses (a: literal-integer arena delta; c: reduced-stage shape).
  - §3.4 impact-set anchor: three labels where two share a derived node — the shared node appears
    in both impact sets; result independent of expansion order.
  - §2.4/§6.1b structural no-cross-product count (`1 + |S| + |W|` fill nodes).
  - §5.3 projection-union test; §5.4 refusal + positive control.
  - §3.3 NEW frozen variation benchmark file (exact `stages == N+1`, `reduced == 2N+2`, linear
    bound).
  - §8.2 cross-process labeled StageError (incl. §7.4 dead-letter label); §7.3 interrupt/resume
    byte-identity.
- **m50 — scale + integration** (repos: `graphed-histogram` + `graphed` preserve/docs).
  Targets: §6.2, §9. Frozen anchors:
  - Variation-axis fill equals sibling-fill results bin-for-bin on the corpus **weight** labels,
    AND a mixed shift+weight program lands in ONE axis-mode histogram equal to its sibling-fill
    decomposition (§6.2, scalar-labeled shift siblings); combine-safety across partitions
    (identical spec, deterministic label order).
  - The §6.2 scaling claim frozen **structurally** (R0.10a: no wall-clock in frozen tests): per
    partition, axis mode allocates 1 histogram object and ships 1 combine payload entry vs `N+1`
    in sibling mode (countable at the `FillEvaluator`/`_GroupReduce` seam, `boost.py:100-117`),
    plus bin-for-bin equality. The N≈100 wall-clock sibling-vs-axis comparison is an
    **implementer-report measurement under R0.11** (methodology stated: what is warmed, timed,
    held constant) — NOT a frozen gate.
  - §9.2 one-bundle-N-labels preservation (m9 comparison form) + `inspect()` label listing (§9.1).
  - Docs: a "How variations work" design.rst section with **executed** examples (the docs-sweep
    rule) covering §7.3's limitation explicitly.

Definition of Done per milestone = the standard checklist (root `CLAUDE.md` §E.0): targets exactly
as specified, frozen suite green and unmodified since freeze, ≥90% diff coverage from the frozen
suite, determinism gate, ruff/clippy/mypy-strict (src AND tests, R0.4a), Sphinx `-W`, full-matrix
CI green at the pinned revision (R0.5), attempts log + reviewer APPROVE recorded.

## §11 Out of scope (Phase 2 — named, not silently dropped)

Declarative nuisance registry / config layer (mkShapesRDF-style `{name, type, kind, samples}`);
correlation/decorrelation metadata, envelope/RMS/symmetrize post-aggregation ops; dataset-level
variation automation (separate-sample variations stay a partition-metadata pattern, documented);
variation-aware materialize/write-out (OR-of-selections masks — RDF Snapshot's bitmask cautionary
tale); per-variation monitor/dashboard axis; stage-granular checkpoint task ids (the §7.3 fix);
variations crossing Exchange/Join boundaries (§5.4); implicit variation cross products; weight
clamping/validation hooks (narf `theory_weight_truncate` precedent); growth category axes;
**per-sample divergence of the variation-label set** (merging outputs across samples whose label
sets legitimately differ — the exemplar's suffix-blacklist pathology, lit §ewkcoffea-confirmed;
§6.1a governs one program's outputs, not cross-sample merging); a constant/scalar-Array broadcast
helper (§4.1's normalization gap); a first-class Rust `Vary` NodeKey.

## §12 Process and bookkeeping

- **§12.1 (Full stringency — the join-repartition standard, owner-confirmed.)** This plan enters
  multi-round, multi-lens review **until clean**: independent facts / design / tests lenses per
  round, findings ranked BLOCKER / HIGH / MID / LOW / NIT, recorded as
  `systematics-vary-plan-review-rN[-lens].md`; a clean round is required before any implementation.
  Each milestone then runs the gated three-role pipeline: test-author writes and freezes the
  acceptance suite (TEST_SANITY: collects, non-vacuous — fails the stub for the right reason —
  deterministic, coverage-wired), implementer iterates under the full R0.4 mechanical gates without
  ever touching `tests/frozen/**` (disputes via `.graphed/<mX>/disputes/`, the m39 precedent),
  reviewer judges intent/guardrails/technique and may REJECT; implementation review runs the
  design / integrity / mutation three-lens pattern (m46/m47 precedent) at the same severity terms,
  cycling until clean, empowered to send work back to planning. R0.5 pins DONE to full-matrix CI
  green. R0.10/R0.10a govern every witness; R0.11 governs every number in every report.
- **§12.2 (Worklogs.)** `systematics-vary-worklog.md` continues as the dual memory; per-milestone
  `.graphed/<mX>/attempts.md` as always.
- **§12.3 (Bookkeeping amendments, on landing.)** (a) Draft **R23** for the root prompt binding
  §§1–9 outcomes (r22-draft.md pattern: separate draft file, owner inserts); (b) amend the root
  prompt Out-of-scope bullet (`graphed-root-prompt.md:1286`) and the two inline R22.0/R22.10
  "systematics-as-a-graph-axis stays Phase 2" mentions (`:1262,:1282`) to point at R23; (c) edit
  root `CLAUDE.md` Part F likewise; (d) un-park `ops_catalog.md:75` into a milestone-tagged
  Section-C row (`test_catalog.py` lock-step preserved — verified text-presence-only, review r0);
  (e) memory-file update.

---

## Anchors appendix (key file:line evidence; full trails in the two research docs)

| Claim | Anchor |
|---|---|
| Interning = CSE; identical key ⇒ same NodeId | `graphed src/store.rs:73-88` (the lookup); identity fields `src/node.rs:39-41` |
| Non-Op ⇒ automatic stage boundary (why no Vary NodeKey) | `src/node.rs:102-103`, `src/optimizer/engine.rs:54-56` |
| O(N) extractor built for deep systematics chains | `src/optimizer/engine.rs:7-13` |
| Variation-count-independent reduction, < 1 s at 10⁴ nodes (frozen) | `tests/frozen/core/m4/test_systematics.py:28-53` |
| Anti-quadratic benchmark shape | `tests/frozen/core/m4/test_benchmark.py:10,40-53` |
| Measured expansion scaling (linear; Δ = varied suffix) | cba §optimizer §2,§5 (in-context probe) |
| Corpus systematics fixture + 15 refs + fingerprints | `graphed-corpus src/graphed_corpus/analyses/systematics.py:25-112`, `corpus/references/` |
| m05 behavioral invariants (weight preserves / shift orders selection) | `tests/frozen/corpus/m05/test_systematics.py:26-38` |
| Corpus JES-before-cut; AGC shift-before-mask | `systematics.py:60-61`; `tests/frozen/preserve/m9/agc.py:106-107` |
| Corpus stacked weight (central b-tag on shifted jets) | `systematics.py:74-76,31-36` |
| correctionlib `systematic` category param in one payload | `tests/frozen/preserve/m9/agc.py:38-66` |
| M29 multi-weight fill + identity discipline | `graphed-histogram src/graphed_histogram/boost.py:166-174,205-206`; `tests/frozen/m29/test_multi_weight_fills.py:82-99` |
| Single-pass group plan witness | `graphed-histogram tests/frozen/m23/test_group_plan.py:68-77` |
| bh rejects 2-D weight; StrCategory probes | cba §histogram §2,§3 (runtime probes, bh 1.7.2) |
| `{label: hist}` group reduce; `_SumFills` merges all fills | `graphed-histogram src/graphed_histogram/boost.py:100-122,88-98` |
| Golden-bytes + param-absence frozen patterns | `tests/frozen/core/m40/test_join_serialize.py:84-99`; `m29/test_multi_weight_fills.py:93-99` |
| Array dunder surface incl. `__array_ufunc__`, bitwise; `__getitem__`/`filter` reject non-Array | `python/graphed/array.py:156,245-275,344-375,377-379` |
| Positional outputs; unknown-kind raise | `graphed python/graphed/execute.py:99-126` |
| Whole-IR task_id (no cross-revision reuse) | `python/graphed/core/plan.py:164-176,286-301` |
| First-boundary-only plan builders (§5.4) | `python/graphed/shuffle.py:170,232` |
| Single-partitioned-source check | `python/graphed/aggregate.py:89-93`; union projection `:101` |
| Worker-side StageError construction channel (§8.2) | `python/graphed/debug/runner.py:20-45`; closure shipping `aggregate.py:54,96-104` |
| StageError field mechanics | `python/graphed/debug/errors.py:29-81` |
| Provenance skips graphed frames | `python/graphed/provenance.py:66-79` |
| Neutral-verb factorization precedent | `python/graphed/shuffle.py:92-96,5-8` |
| RDF Vary semantics/limitations/vocabulary | lit §rdf-vary §1-§6 |
| narf tensor-axis fills; WRemnants no-Vary | lit §rdf-users §1-§3 |
| coffea three mechanisms; prototype stall; #469 measurements | lit §coffea-sys §1-§5 |
| Cross-analysis conventions + failure modes | lit §pythonic-analyses |
| Exemplar 0.7-era: exclusion rule; impact-partitioned Weights | `ewkcoffea@063e8d7 analysis/wwz/wwz4l.py:1204-1207,396-397` (lit §ewkcoffea-confirmed) |
| Exemplar dask-era: hand-written CSE in the processor; build-vs-compute timing | `ewkcoffea@63abb06 analysis/wwz/wwz4l.py:808-865`; `run_wwz4l.py:302-313` |
| Exemplar dask-era: unserializable variation-expanded graph ("Does not work") | `ewkcoffea@63abb06 analysis/wwz/run_wwz4l.py:259-261` |
| Teaching strip removes physics, variation scaffolding survives intact | `FNALLPC/wwz4l@cc71718 analysis/analysis_processor.py:395-400,408-759,711-718` (private; lit §ewkcoffea-confirmed addendum) |
| Phase-2 parking being un-parked | `graphed-root-prompt.md:1262,1282,1286`, `ops_catalog.md:75` |

## Revision history

- **r3 (2026-07-30)** — the r2 OPEN item resolved with its conclusion inverted: access to
  `FNALLPC/wwz4l` granted; measured to be a coffea-0.7-era CMS-DAS teaching derivative of
  `ewkcoffea@main` (not modern coffea as framed) carrying the full weight+shift treatment; the
  no-dask-era-object-shift finding extends to it and `coffea2023` remains the sole modern-coffea
  exemplar. Addendum appended to lit §ewkcoffea-confirmed (era/lineage claims independently
  re-verified); teaching-strip anchor row added. **No requirement changes** — PART II unchanged.
- **r2 (2026-07-30)** — Kelci's analysis confirmed by the owner as `cmstas/ewkcoffea` and
  integrated as the canonical exemplar (deep-dive appended to the litsearch as
  §ewkcoffea-confirmed, both eras pinned: `main@063e8d7`, `coffea2023@63abb06`; headline claims
  spot-verified by the lead). Part I §2 stub replaced. Evidence-driven deltas applied: §4.1
  per-dataset scalar normalization named (+ §11 parks a scalar-broadcast helper); §6.2 permits
  scalar-labeled shift siblings on the shared variation axis (+ m50 mixed-program anchor); §7.3
  names the `skip_obj_systematics` re-run as the canonical cache-invalidating edit; §11 parks
  per-sample label-set divergence; 3 exemplar anchor rows added. OPEN item recorded: the
  owner-named `FNALLPC/wwz4l` is 404 to this account (likely private) — `coffea2023` stands in;
  needs access or a corrected URL.
- **r1 (2026-07-28)** — applied the 4-lens pre-delivery hygiene review
  (`systematics-vary-plan-review-r0.md`; facts/design/tests/process). Headline changes: §2.4
  rewritten to **label-aligned union** (fixes the Varied-meets-itself BLOCKER); §2.1 gains
  **stacking** (`vary` on a `Varied` nominal — fixes the corpus b-tag-on-JES BLOCKER); §1.2 scoped
  with the §6.2 axis-mode carve-out (fixes the label-identity contradiction); §2.3 rewritten to
  four dispatch points with a bound gak classification (drops the falsified "one uniform wrapper"
  claim) and `Array.__getitem__`/`filter` learning `Varied`; `Varied.map` renamed `.apply`;
  §3.3 moved to a NEW frozen file with per-variation outputs and exact pinned values; §3.4
  redefined as reachability difference (watermark was order-dependent); §4.3 made structural
  (equal-counts was tautological); m50 wall-clock comparison demoted from frozen gate to R0.11
  report measurement with a structural frozen invariant instead; §6.1 bound on per-output label
  sets, fill-node arity, and the `_SumFills` refusal; §6.2 scoped to weight labels; §8.2 label
  transport mechanism bound (process-closure channel); §7.3 resume and §9.1 introspection
  anchored; m48 repo scope corrected to `graphed` + `graphed-histogram`; 9-of-15 count fixed;
  `shuffle.py:233`→`:232` and root-prompt `:1284`→`:1286` anchor corrections; graphed-histogram's
  flat frozen layout named.
- **r0 (2026-07-28)** — initial draft from the owner's high-level doc + the 10-agent research
  fan-out (workflow `wf_e7666c8a-794`). Naming and label style owner-verified in-session. Kelci's
  analysis left as a stub per owner instruction (candidates recorded in Part I §2, unconfirmed).
