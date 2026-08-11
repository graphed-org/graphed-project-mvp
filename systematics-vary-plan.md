# Systematic variations in graphed — `vary`, the variation frontend + IR treatment (execution plan)

Status: **draft for review (r12).** Anchoring doc for the work, structured like the root prompt:
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
coffea Discussion #469 *reports* ~2-3× (up to ~7-8× for many systematics) for vectorized
(extra-axis) systematics over re-run loops — read via summarizing fetch, word-level UNVERIFIED
(lit §coffea-sys, `systematics-vary-litsearch.md:236` carries the caveat).

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
   going N=1→2 variations grows the arena by precisely the varied suffix (Δ = K+2 = 52 nodes on
   the §3.3 builder, whose per-universe suffix is K=50 chain ops + 1 fork + 1 reduction — §3.3
   uses D for the *shared prefix*, so do not read the cba's letter here), reduction
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

**Why systematics attach to the event record (owner semantic correction, 2026-07-30).** The r0–r4
sketches threaded loose `Varied` weights into each fill by hand — re-creating the survey's
forgotten-weight/name-list failure mode and mismatching the physicist's model, on which all three
precedents agree: RDF's weight is a *column of the frame*, coffea's `Weights` belongs to the
*event batch*, boostedhiggs expresses shifts as *collection replacements on `events`*. Systematics
are ambient properties of the event record; the fill is where everything applicable applies
simultaneously (plotting Jet pT must also yield the pileup-reweighting universes). §2.6 binds the
event context (attach-once, ambient thereafter) and §6.1d the fill inference; the one genuine
tension — selection-dependent object SFs cannot be ambient on the root — is resolved by derived,
registry-inheriting contexts rather than the exemplars' per-channel `deepcopy`.

**Why the context surface is functional, and why write-out enters scope (collaborator feedback,
2026-07-30).** The r5 context reserved attribute names on the event record (`events.weights`,
`events.vary`) — but that namespace belongs to the *tree*: branch names are analysis-controlled
and open-ended, so ANY reserved name is a latent collision (a branch named `weights` is entirely
plausible), and the mutable registry left no object identity for provenance to hang on. r6 respins
the surface to one functional verb — `graphed.vary(...)` always returns a NEW context/container,
never mutates — which (a) frees the record namespace completely (§2.6a), (b) makes each variation
step an object with lineage, the provenance the collaborators asked for (§2.6b), and (c) turns
r5's "fill-time registry snapshot" rule into plain immutability (§2.6c). The same principle
resolved a latent r5 ambiguity: `Varied[label]` collided with awkward's string-getitem field
access; extraction moves to module functions too (§2.2). The same feedback round surfaced the
missing sink: skims. Two surveyed frameworks hit exactly this wall and bolted around it — RDF
Snapshot needed a per-event validity bitmask bolt-on, mkShapesRDF re-implemented `Vary` wholesale
for its Snapshot stage (suffixed columns + OR-of-cuts, Part I §2) — and graphed's write path is
measured greenfield: zero variation machinery, zero metadata use, one seam method per backend
(write-seam evidence rows, Anchors). §6.4 binds the native treatment: superset rows by
OR-of-selections, appended exact-by-construction reconstruction columns (measured: XOR bit-delta
exact by construction; the suggested "1+delta" float ratio NOT bit-exact — worklog probe,
2026-07-30), packed varied-cutflow masks, and a manifest in existing metadata channels.

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
- **Skim growth**: the §6.4 superset+augmentation write stores more rows (OR of selections) and
  more columns than a nominal-only skim. Mitigated by exact-by-construction deltas that are zero
  wherever a label agrees with nominal (maximally compressible) and packed masks (~4.7× measured,
  §6.4c); bounded by the m51 report measurement on real skims.

---

# PART II — REQUIREMENTS (binding; specific)

## §1 Vocabulary (owner-verified)

- **§1.1** Verb `graphed.vary`; container `graphed.Varied`; concept "variation" everywhere (docs,
  APIs, tests, R23). The reserved central label is the string `"nominal"`; user variation labels
  are `f"{name}_{tag}"` (e.g. `jes_up`). **Tag grammar (r6; float spellings r7; canonicalized
  r8; e-form canonical r9, owner-selected):** `up`/`down` are conventions, not specials —
  σ-families, PDF member
  indices, and stringified-float families (μR/μF scale factors, σ-scans; correctionlib category
  inputs are arbitrary strings — `preserve/m9/agc.py:56-62` — so a float-spelled key is
  expressible, §4.1) are all first-class. A `name` MUST be
  a valid Python identifier. A **tag** is a string matching `[A-Za-z0-9_]+` — every label is
  therefore itself a valid identifier, usable verbatim as a StrCategory bin (§6.2),
  result key, manifest key, and on-disk column/branch name (§6.4). It is NOT necessarily
  spellable as *literal* kwarg syntax: canonical numeric tags are digit-leading (`2=`, `102=`
  are SyntaxErrors), which is exactly what the `variations=` channel exists for (below).
  Floating-point tags use the
  **e-encoding** (owner-selected 2026-07-30, three-option encoding decision): the canonical
  numeric form is `m?\d+(em\d+)?` — integer values render as plain digits (`2`, `102`, `m2` for
  −2; PDF indices are untouched), fractional values as minimal-mantissa scientific notation
  with `em` for the negative exponent (`0.5`→`5em1`, `2.5`→`25em1`, `1.2345`→`12345em4`,
  `-1.5`→`m15em1`, `1e-8`→`1em8`; a fractional value's exponent is negative by construction, so
  bare `e` never appears in canonical form; **negative zero canonicalizes to `0`**, never `m0` —
  one value, one label; and a canonical tag longer than **32 characters is REJECTED** — a
  tag-sanity bound and nothing more: it covers every real σ-scan / μR-μF / PDF family, but it
  does NOT bound the label (`f"{name}_{tag}"`) or the on-disk name (`__vary_{label}__{field}`,
  §6.4b), both of which also carry the user's arbitrary `name` and field) — chosen for its
  uniformly parseable numeric
  structure over the WHOLE float range (parse = `m`→`-`, `em`→`e-`, then a standard float
  literal), at the cost of not reading as the decimal at sight (the datacard p-form `2p5` was
  the r8 canonical; p-encoded tags remain legal identifier tags, see below). `vary` ACCEPTS
  plain float spellings as input sugar: a tag matching `-?\d+(\.\d+)?([eE][+-]?\d+)?` (`"0.5"`,
  `"-2"`, `"2.0"`, `"1e-8"`; no leading `+`, no `inf`/`nan`, no `_` separators or whitespace)
  is **canonicalized at call time** by exact decimal-string arithmetic (never an IEEE
  round-trip — no float artifacts enter labels) to the form above, so `"2"`, `"2.0"`, `"2e0"`,
  and `"20e-1"` all yield the SAME tag `2`. **A tag that already matches the canonical numeric
  grammar is canonicalized too — re-rendered minimally** (`"50em2"` → `5em1`, `"05"` → `5`);
  without that rule a hand-typed non-minimal e-form is not matched by the input-sugar grammar
  above (it contains `m`) and would ride through as an ordinary identifier tag, giving two
  labels for one value — caught only when both spellings met in one family. **"Unify" means
  ACROSS calls**: two separate `vary` calls spelling `"0.5"` and `"5em1"` name the identical
  label `murf_5em1`; the same two spellings *within one call* are a duplicate-after-
  canonicalization rejection (below), the same shape as the cross-notation `{"0.5", "0p5"}`
  case. A dotted or signed spelling never reaches a label. The
  rationale for canonicalizing at all is measured, not taste (r7 probes, worklog 2026-07-30):
  dotted names store byte-exact but are unreadable-by-name (`ak.from_parquet(columns=
  ["murf_0.5"])` silently empty; a dotted uproot 5.7.5 RNTuple field is reachable via
  `__getitem__` — exact lookup runs first, `behaviors/RNTuple.py:1560-1562` — but
  `RField.array()` FAILS, because `to_akform` splits the field path on `.`
  (`behaviors/RNTuple.py:562,567` → `KeyInFileError: 'murf_0'`; re-measured this session,
  uproot 5.7.5 / awkward 2.12.0 / pyarrow 25.0.0 — `ntuple.arrays(["murf_0.5"])` still works,
  so the hazard is per-field access, not wholesale unreadability); the TTree writer
  uses `.` as its own nesting separator), while identifier-shaped names round-tripped
  byte-exact AND readable in every measured path. Normalization kills spelling multiplicity by
  construction; the one residual duplicate class is **cross-notation**: a p-encoded identifier
  tag (`"0p5"`) does not canonicalize but p-parses to the same value as `"0.5"`→`5em1`, so two
  tags in one family that both parse as numbers (under either notation) MUST NOT parse
  numerically equal (`{"0.5", "0p5"}` and `{"2", "2p0"}` are rejected — distinct labels for
  one value would silently create semantically duplicate universes, distinct StrCategory bins,
  and distinct content hashes).
  (Encoding decision trail, owner 2026-07-30: r8's canonical was the datacard p-form; the
  owner's scaled-integer proposal — carry the scale as an exponent suffix, `1.2345`→`12345e-4`
  — is self-describing and, in identifier-safe rendering, IS this e-form; selected over p for
  the uniform full-range grammar and native numeric structure. Trade-off recorded: hand-typed
  datacard tags (`0p5`) no longer unify with float spellings (`"0.5"`→`5em1`) — the
  cross-notation rejection catches in-family mixes; p-tags stay legal identifier tags.)
  Tags arrive as **kwarg names** (`up=…, sig2=…`) or via the `variations={tag: …}` mapping.
  Validation and canonicalization are **channel-independent**: literal kwarg syntax cannot spell
  dotted or digit-leading tags (`0p5=` is a SyntaxError), but CPython admits any string key
  through `**`-unpacking (measured, CPython 3.12.10), so both channels apply the same rules;
  `variations=` is simply the documented route for such tags. Arbitrary hashables are REJECTED
  (labels serialize into specs, files, and manifests; string-only — a float tag is passed as its
  string, never as a Python float, so the user owns the spelling). `vary` MUST reject, at call
  time: a label equal to `"nominal"`, duplicate labels after canonicalization (within the call,
  within the container, or colliding with inherited labels, §2.1), numeric-equal tag pairs
  within a family (above), a tag supplied both as kwarg and in `variations=`, malformed or
  non-string tags (including Python floats — pass the string), and empty tag sets.
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

- **§2.1 (API — ONE functional verb, three targets; always returns a NEW object.)**
  `graphed.vary(target, name, /, nominal=None, *, is_weight=False, variations=None,
  collections=None, **tags)` — a
  **neutral module verb** exported like `join`/`repartition` (`shuffle.py:92-96` precedent; per
  the factorization rule it is not an `Array` method, not gak, not numpy-idiom). It NEVER
  mutates: the result is a new object of the target's kind and the target remains valid,
  unchanged — provenance hangs on object lineage (§2.6b). Tag/member pairs come from `**tags`
  and/or `variations=` under the §1.1 grammar. **The signature's own keyword names shadow
  `**tags`**: `nominal`, `is_weight`, `variations` and `collections` are all legal §1.1 tags AND
  legal tree collection names, so a tag or collection so named MUST come through a mapping
  channel — `variations={tag: …}` for tags in overloads (a)/(b), a
  `collections={Name: {tag: record}}` mapping for collections in overload (c), which resolves
  its own name by self-reference (`collections={"collections": {...}}`). `variations=` is
  REJECTED in the shift form (c) with an error naming `collections=`. This is the §2.6a
  no-reserved-names hazard re-surfacing at the signature instead of on the record; the m48
  grammar anchor covers all FOUR shadowed names.
  Three binding overloads:
  (a) **Array | Varied target** (the loose primitive): members are Arrays;
  `graphed.vary(jets, "jes", up=j_up, down=j_dn) -> Varied` with the target as `"nominal"`.
  `is_weight=True` and `nominal=` are invalid here (a loose weight variation is just a `Varied`
  used in a `weight=[…]` factor list, §4.2).
  (b) **Event-context target, weight form** (`is_weight=True`): `nominal` (third positional) is
  the central per-event weight factor and every member is a per-event weight Array —
  `graphed.vary(events, "pu", pu_nom, is_weight=True, up=pu_up, down=pu_dn) -> new context` with
  the factor registered into the returned context's ambient weight (§2.6b).
  (c) **Event-context target, shift form** (no `is_weight`): each kwarg names a **collection**;
  each value maps tags to varied records — `graphed.vary(events, "jes", Jet={"up": j_up, "down":
  j_dn}, MET={…}) -> new context` with every named collection replaced by a `Varied` (all
  collections in one call MUST share one tag set — the lockstep Jet+MET form; §2.6a).
  **Stacking**: when the target (or a named collection on it) already carries variations, the
  result inherits those labels and adds the new labels; a new label's member is the provided
  value's central universe (`graphed.nominal(v)` if the provided value is itself `Varied`, else
  the Array as given). **What "inherits" means differs per overload, and the corpus turns on
  it**:
  in the loose/shift forms (a)/(c) inherited members pass through **unchanged**; in the **weight
  form (b)** the newly registered factor is combined into the ambient weight **label-aligned per
  §2.4**, so an inherited label L's ambient member becomes `old_ambient[L] × factor[L]` — the
  factor evaluated in *that label's own universe* (its central universe only when L is new to
  the factor). This is not a nicety: for `variation="jes_up"` the corpus computes the CENTRAL
  b-tag SF **on JES-shifted, JES-selected jets**
  (`graphed-corpus src/graphed_corpus/analyses/systematics.py:74-76` — `sel_jets = good[sel]`
  then `_btag_weight(sel_jets, variation=variation)`, which returns the central SF unless
  `variation` is `btag_up`/`btag_down`, `:25-36`), so the `ttbar_4j1b_jes_up` reference IS b-tag
  weighted; a naive "inherited labels keep the old ambient" reading omits the SF entirely and
  misses the reference. Each label still differs from
  `"nominal"` in exactly **one** knob — the one-at-a-time rule is structural, and a weight
  variation layered on a shift-propagated weight (the corpus b-tag-on-JES case,
  `systematics.py:74-76`) is expressible without cross products.
  All member Arrays MUST share one Session, have compatible forms (backend `op_form`-checked at
  construction), and root in the same partitioned-source set (checked at construction; the
  otherwise-deferred failure surface is `aggregate_plan`'s single-source check,
  `aggregate.py:89-93`). Lockstep multi-column variation within one collection (jet pt+mass
  shifted together) is expressed by varying a record Array — the corpus JES fixture already does
  this via `ak.with_field` (`systematics.py:39-45`); no second verb.
- **§2.2 (`Varied` is a mapping of universes; extraction is functional.)** `Varied` holds
  `{label: Array}` with `"nominal"` always present. Universe extraction and introspection are
  **module functions** (the r6 namespace-collision principle, §2.6a): `graphed.labels(x)`
  (ordered: nominal first, then insertion order; inherited labels before new ones under
  stacking), `graphed.nominal(x)`, and `graphed.universe(x, label)` (KeyError on an unknown
  label, listing the valid labels) — each accepting a `Varied` OR an event context (uniform
  introspection, §9.1). String subscription `v["pt"]` is **field access** (broadcast per §2.3a,
  Array-coherent), NEVER label lookup — r5's `[label]` indexing collided with awkward's
  string-getitem field access and is removed. `Varied.apply(fn)` remains a method — apply a
  record-time `Array -> Array` function per universe (attribute shadowing follows the awkward
  precedent: real methods win; a field named `apply` stays reachable via string getitem). (Named
  `apply`, NOT `map`: `Array.map` is an execution-time data callable, `array.py:377-379`; the two
  contracts must not share a name. **The stated criterion cuts against `apply` too, and the
  collision is accepted knowingly rather than by oversight** (r12): `graphed.apply` is already a
  public module verb with the same execution-time contract as `Array.map` and interns with it
  (`array.py:397-410`, "With one array this IS `Array.map` (interns with it)"; exported at
  `python/graphed/__init__.py:9` and in `__all__`). It is accepted because the two names live on
  different objects with no dispatch path between them — `Varied.apply` is a bound method on the
  container, `graphed.apply` a module function over `Array`s — whereas r1's rejected `Varied.map`
  would have shadowed `Array.map` on the very surface §2.3a mirrors. If the m48 test-author judges
  the collision confusing, the rename is `Varied.per_label`; the spelling is pinned at m48 freeze
  like every other new surface here.) `fn` MUST return an `Array`; if it returns a `Varied` (because
  it closed over another container), `.apply` raises with guidance to combine containers via
  ordinary ops instead. **`Varied` reserves the `Array` protocol attribute names**: `node_id` and
  `session` raise `AttributeError` on a `Varied` rather than resolving as field access. This is
  binding because `Array` exposes both as plain properties, not dunders (`array.py:137-143`), while
  `Array.__getattr__` guards only leading underscores (`array.py:332-335`) — so a `Varied` that
  implements field access by mapping over labels would answer `varied.node_id` with a recorded
  `field` op named `"node_id"`, and `compile_ir(session, varied)` (`execute.py:74`,
  `ids = [arr.node_id for arr in outputs]`) would silently compile that nonsense instead of
  raising, the §2.5 confidently-wrong class. `Varied` is a plain frontend object — no IR type, no
  new NodeKey (§3.1).
- **§2.3 (Broadcast propagation — five bound dispatch points.)**
  (a) **`Varied` implements the full `Array` PUBLIC surface — dunders AND methods** — by mapping
  over labels. Dunders: enumerated
  at implementation from `array.py` and including `__array_ufunc__` (`array.py:156`), the bitwise
  set (`__and__/__or__/__invert__`, `array.py:245-275`), `__getitem__`, field access, and all
  reflected variants. **Public methods are in scope too, and were unbound until r12**: `Array`
  carries four (`filter`, `map`, `reduce`, `repartition` — `array.py:374-391`) and the numpy idiom
  adds ~25 more on top of a tuple-accepting `__getitem__` override
  (`python/graphed/numpy/array.py:92-190`, `:132-136` — `sum`/`prod`/`mean`/`std`/`var`/`min`/
  `max`/`any`/`all`/`argmin`/`argmax`/`cumsum`/`cumprod`/`reshape`/`ravel`/`squeeze`/`transpose`/
  `swapaxes`/`astype`/`clip`/`round`/`take`…), none of which a dunder-only enumeration reaches —
  and an unimplemented one does not raise cleanly: `Varied`'s label-mapping field access turns
  `varied.filter` into a recorded `field` op (§2.2's reserved-name rule covers only the `Array`
  protocol properties). Each method carries the same per-class disposition as (c): *broadcast*
  for the elementwise/structural ones, *refusing* for `repartition` (§5.4).
  Parity is gated by a frozen test iterating the inventory
  **enumerated dynamically from `type(graphed.nominal(v))` at test time** (so idiom subclasses are
  covered), not from a literal list (same
  self-repairing rule, and the same **non-vacuity floor**, as (c) — which for this gate MUST name
  at least one METHOD alongside the named dunders).
  (b) **Plain-`Array` entry points learn `Varied`**: today `Array.__getitem__` accepts only an
  `Array` mask, a `str` field, a `list[str]` field subset, a `slice`, or an `int`, and raises
  `TypeError` on anything else (`array.py:344-371`) — including a `Varied`; `Array.filter` has NO
  runtime check at all (`array.py:374-375`), so a `Varied` falls through into `record_op` and
  surfaces as an `AttributeError` on `a.node_id` (`session.py:152,159`). There is no reflected
  protocol for subscription, so both gain an explicit `Varied`-mask branch delegating to the
  container (the corpus
  requires it: unvaried `photons`/`muons` sliced by a JES-varied selection, `systematics.py:91-92`).
  (c) **The gak layer gets one dispatch mechanism plus a bound per-function classification** —
  "one wrapper, zero per-function thought" is falsified by the measured surface (review r0), so the
  classification is explicit, lives in code, and is gated by a frozen exhaustiveness test that
  **enumerates gak's public surface DYNAMICALLY at test time** (not a
  hand-written literal name tuple — the `m24/test_interface_parity.py` anti-drift pin is a
  **39**-name literal (`:39-79`), which would let a future gak function go silently unclassified,
  exactly the failure this requirement names; a dynamic check is also self-repairing, since a new
  function is fixed in `src`, never by editing a frozen test).
  **The discovery rule is bound, because the obvious one does not exist**: `graphed.awkward.
  functions` defines **no `__all__`** (measured: `grep -c "__all__" python/graphed/awkward/
  functions.py` → 0), and the package `__all__` lists modules/classes, not gak's functions
  (`python/graphed/awkward/__init__.py:17-31`), so an `__all__`-driven test would discover
  nothing and assert nothing; a bare `dir()` over-fires on imported symbols and on the module's
  private helpers (`grep -c "^def " functions.py` → 73, including `_comb_params`, `_reduce`).
  Binding discovery: `inspect.getmembers(gak, inspect.isfunction)` filtered to
  `__module__ == gak.__name__` and no leading underscore. **Binding non-vacuity floor, asserted
  in the same frozen test** (a dynamic gate whose discovery returns an empty or wrong set passes
  tautologically): the discovered set is non-empty, is at least the freeze-time count, and
  contains at least one NAMED member of each classification class below. The classes:
  *broadcast* (elementwise/structural default),
  *container-traversing* (`gak.zip`/`concatenate`/… detect `Varied` **inside** their
  Mapping/Sequence arguments), *tuple-returning* (`gak.unzip`/`broadcast_arrays` return a tuple of
  `Varied`), *eager-metadata* (`fields`/`type_of`/… answer on the nominal member — sound because
  §2.1 requires form compatibility), and *refusing* (`gak.join` and boundary verbs, per §5.4).
  Signatures do not change (R17.0 anti-drift preserved).
  (d) **Module verbs and sinks — the enumeration is EXHAUSTIVE over `graphed`'s public
  Array-consuming surface** (r12; the r11 list named three and left the rest undisposed, which is
  not harmless: `Varied`'s field-access `getattr` (§2.2) turns an unhandled duck-typed read into a
  recorded op rather than an error, so an undisposed verb silently compiles nonsense). Measured
  surface (`python/graphed/__init__.py:8-25`, `__all__` `:27-58`): `graphed.join` and
  `graphed.repartition` **refuse** with the §5.4 error; `graphed.apply` and `graphed.read_columns`
  **expand into universes** (per-label results — `apply` returns a `Varied`, `read_columns` returns
  the union over all labels' members, §5.3); `graphed.compile_ir`, `graphed.evaluate_ir` and
  `graphed.aggregate_plan` **refuse** a `Varied` output with an error naming `graphed.universe` —
  they consume `arr.node_id`/`arr.session` directly (`execute.py:74`, `aggregate.py:66-72`) and
  §2.2's reserved-name rule makes the refusal a clean `AttributeError` seam rather than a compiled
  field op; the varied route to a plan is the §6.1c group API. `graphed.awkward.to_parquet` takes
  `select=` per §6.4a. `Histogram.fill` accepts `Varied` (§6).
  (e) **Context-tag propagation** (the §6.1d substrate; NEW in r10 — it was previously implied,
  and mis-named "provenance"). Every `Array`/`Varied` produced from a contexted input carries a
  **context handle: a Python attribute on the frontend wrapper object, explicitly NOT part of
  node identity** — it never reaches `NodeKey` params/tokens/hashes (§1.2 and interning stay
  intact). **This is an Implementation Target, not free**: `Array` is `__slots__`-ed with no
  `__dict__` (`python/graphed/array.py:127-128`, `__slots__ = ("_node_id", "_session")`) and
  `NumpyArray` keeps it closed (`python/graphed/numpy/array.py:71-74`, `__slots__ = ()`), so an
  ad-hoc attribute raises `AttributeError` today. Binding: **one added slot, underscore-prefixed**
  (e.g. `_context`), so `Array.__getattr__`'s `startswith("_")` guard keeps it out of field
  access (`array.py:332-335`). A wrapper attribute is the only sound carrier, measured: two sibling contexts derived
  from one root that differ only in registered weights expose collections whose reads record
  identical `NodeKey`s and therefore the SAME node id (interning, `src/store.rs:73-88`; re-measured
  this session — `src * 2.0` recorded twice returns node id 1 both times), so a node-id-keyed
  context map provably cannot distinguish them; and `Provenance` is a frozen
  `(filename, lineno, function, source)` dataclass with no lineage channel
  (`provenance.py:26-33,66-79`), so provenance cannot carry it either. **Propagation is a
  chokepoint, not per-function work**: every frontend `Array` is constructed in `Session` at
  **FIVE** sites, not the three the r11 prose named (r12 — omitting `source` drops the handle at
  every tree read, omitting `record_join` drops it across a join):
  `source` (def `:133`, return `:140`), `record_op` (`:142`→`:168`), `record_exchange`
  (`:170`→`:183`), `record_join` (`:185`→`:204`), `record_external` (`:206`→`:242`) — all five end
  `return self._array_cls(self, node_id)` (`python/graphed/session.py:140,168,183,204,242`) and
  they are the only `_array_cls` call sites in the repo (measured: no hit outside `session.py`).
  Those methods already receive
  the input `Array`s, so the merge rule is implemented ONCE there; gak functions and module verbs
  inherit it by construction, and the propagation gate below is the anti-drift gate
  over the ones that bypass `record_op` (e.g. tuple-returning wrappers that rebuild results).
  **Merge rule at the op, not at the fill**: inputs whose
  handles lie on ONE ancestry chain propagate the most-derived handle; handles on divergent
  branches are an error at that op naming both. **The op is not the only raiser** — every
  *combining point* runs the same unification, and the fill is one of them (§6.1d): a fill takes
  several independent inputs no op ever combined (`h.fill(a_from_ctx1, b_from_ctx2,
  weight=[w_from_ctx3])`), and `Histogram.fill` is the first place those handles meet — it
  collects args/weights/sample into ONE `inputs` list and records ONE External node
  (`graphed-histogram src/graphed_histogram/boost.py:154-212`). The op-level rule is *early*
  detection, not the sole raiser. **Drop rule**: an op that cannot propagate a handle (no contexted input) yields a
  context-free result, and a subsequent fill mixing context-free with contexted inputs adopts the
  unified context (§6.1d) — an op that silently *loses* a handle it had is the §2.5 failure mode
  and is a bug. **The propagation gate is a SEPARATE test from (c)'s classification gate, and it is
  scoped, because a behavioural gate over the whole surface is not buildable** (r12; the r11 "SAME
  frozen exhaustiveness test" wording was not implementable). (c)'s gate is *metadata-only* — it
  reads a classification off each discovered function and never calls it — so it runs over all
  **65** public gak functions (measured: 73 `def`s, 65 public, `python/graphed/awkward/
  functions.py`) for free. A propagation gate must CALL each function with a contexted `Array`, and
  the measured surface makes a blanket call impossible: `apply_correction` and `onnx_inference`
  take a payload + evaluator/runner first, not an `Array` (`functions.py:476,513`); `to_list`,
  `head` and `sample` are eager and return Python objects (`:693,732,737`); `fields`, `type_of`,
  `backend_of` return `list[str]`/`str` (`:717,722,727`), for which "preserves the handle" is
  undefined; `join` must refuse (`:18`); and `zip`/`concatenate`/`where`/`unflatten`/`linear_fit`
  need typed or extra operands (`:118,383,400,600,346`). The m24 precedent gate compares
  signatures and never calls (`tests/frozen/awkward/m24/test_interface_parity.py:39-79`). Binding:
  **(1)** the classification gate of (c) covers all 65, metadata only; **(2)** the propagation gate
  dynamically enumerates only the *broadcast*, *container-traversing* and *tuple-returning*
  classes, and derives its call arguments from **argument fixtures that live in `src` beside the
  classification** — so a newly added function arrives with its classification AND its fixture and
  the frozen test stays untouched (the self-repairing property is preserved); **(3)** the
  *eager-metadata* and *refusing* classes are EXEMPT by classification, not by omission, and the
  gate asserts the exemption set is exactly those two classes (so an exemption cannot be used to
  hide an unimplemented member); **(4)** the `Array` public surface of (a) is gated the same way,
  dynamically enumerated. Both gates carry (c)'s non-vacuity floor.
  Broadcast recording happens while the *user's* frame is on the stack, so `capture()` attributes
  each varied node to the user's own op line with no provenance copying (`provenance.py:66-79`
  skips graphed frames).
- **§2.4 (Combination rule — label-aligned union; one-at-a-time; no cross products.)** When an
  operation combines `Varied` inputs — including a `Varied` combined with one derived from it
  (`jets[jets.pt > 25]` is the canonical case) — the result's labels are the **union**, and for
  each label L every container contributes **its own member for L when present, else its
  `"nominal"` member**. **The union's ORDER is bound** (§3.2 determinism and the §6.1b/`_GroupReduce`
  positional layout both depend on it, `boost.py:102-117`): the first operand's order, then labels
  new to the second operand in its own order, `"nominal"` always first. Within a universe L, all
  uses of varied quantities are therefore coherent
  (RDF's whole-cone-substitution semantic). Because §2.1 makes each label belong to exactly one
  knob, cross products can never arise implicitly: at a fill combining shift-varied kinematics with
  a stacked weight `Varied`, shift labels fill with the central weight *as evaluated in that
  shift's universe* (label-aligned), and weight labels fill with nominal kinematics — exactly the
  corpus reference semantics (`systematics.py:74-76`) and the universal exclusion convention
  (lit §pythonic-analyses).
- **§2.5 (Validation over convention.)** Silent-drop failure modes from the survey become errors
  or diagnostics: unknown label on `graphed.universe(x, label)` → KeyError listing valid labels;
  form-incompatible or
  cross-Session/cross-source member → construction-time error naming the label; `vary()` registers
  each container with its Session (weak reference), and `compile_ir` diagnostics report any
  registered label that reaches no marked output (DCE already prunes the work; the diagnostic
  prevents the mkShapesRDF silent-cost case).
- **§2.6 (The event context — systematics attach to `events`, functionally; owner semantics
  2026-07-30, respun functional per collaborator feedback 2026-07-30.)** The primary user idiom
  is not loose `Varied` threading but an **event context**: a frontend wrapper over the root
  event record carrying (a) the collections and (b) an **ambient event-weight registry** (itself
  a `Varied` of accumulated M29 factors). Pure frontend sugar over §§2.1–2.5 — no IR change,
  §3.1 intact. Binding, in the r6 functional form:
  (a) **The context reserves NO NAMES.** Attribute access, and `[]` **with a string (or list of
  strings)**, resolve ONLY tree content (collections/branches); `[]` **with an `Array`/`Varied`
  mask derives a new context** (§2.6c — `sel = events[gak.num(jets) >= 4]`, the sketch's central
  idiom), mirroring `Array.__getitem__`'s own mask-vs-field split (`array.py:344-371`). Every
  graphed operation on a context is a module function
  (`graphed.vary`, `graphed.labels`, `graphed.universe`, `graphed.nominal`, `graphed.weight`,
  `graphed.selection`, and `graphed.variations` — §9.1; `graphed.variations` lands in m50,
  `graphed.selection` in m51, the rest in m48). This is
  load-bearing, not style: branch names are analysis-controlled and open-ended, so any reserved
  attribute (r5's `events.weights`, `events.vary`) is a latent collision with real tree content.
  (b) **Contexts are immutable; `graphed.vary` returns a NEW context** (§2.1 overloads b/c). The
  shift form replaces the named collections with `Varied` members (thereafter
  `events.<Collection>` is a `Varied` and §2.3 broadcast carries it; repeated calls stack,
  §2.1); the weight form registers the factor into the returned context's ambient weight (M29
  factor-list semantics; explicit tags in v1 — auto-symmetric derivation from a lone `up` is
  Phase 2, §11). Each returned context links to its parent: variation history is **object
  lineage** — the provenance handle the collaborators asked for; no hidden mutable registry.
  (c) **Scoping is lineage.** A fill sees exactly the registrations present on the context its
  inputs were read from (§6.1d) — r5's fill-time-snapshot rule re-bound as immutability: a fill
  from a pre-`vary` context is unaffected by later `vary` calls *by construction*. Derived
  contexts (`events[mask]`) **inherit the ambient registry with every member RE-INDEXED by the
  derivation mask, label-aligned per §2.4** — the parent's members carry the PARENT's row count, so
  an un-re-indexed inheritance makes every §6.1d ambient fill from a derived context
  length-mismatched, and §6.1d's "unify to the most-derived context" is ill-defined without it.
  Selection-scoped weights are `vary` on
  the derived context (`sel = graphed.vary(sel, "btag", …, is_weight=True, …)` — the replacement
  for the exemplars' per-channel `deepcopy(Weights)`); the parent is never touched. Inputs whose
  contexts lie on ONE ancestry chain unify to the most-derived one; contexts on divergent
  branches are the §6.1d hard error (raised at the op, §2.3e).
  **Varied contexts (per-label row sets) are first-class.** When the derivation mask is itself
  `Varied` — the central idiom of the sketch below, `sel = events[gak.num(jets) >= 4]` with a
  JES-varied `jets` — the derived context's ROW SET DIFFERS PER LABEL. Binding: its collections are
  `Varied` per §2.6b; `graphed.labels(ctx)` reports the mask's labels; re-indexing happens per label
  (each label's ambient member is re-indexed by THAT label's mask, nominal's by nominal's);
  `graphed.vary(ctx, …, is_weight=True)` on it stacks per §2.1 (a new weight label's member is the
  provided value's central universe, each inherited shift label keeps its own); fills from it are
  label-aligned per §2.4; and §6.4a's OR-of-selections is exactly the union of these per-label row
  sets.
  (d) **Data contexts refuse BOTH forms.** `is_weight=True` on a data context is a guard error, and
  a **shift-form `vary` on a data context is likewise refused**, with an error naming the variation:
  accepting it and discarding its labels at the fill would silently drop an explicit user
  registration — the §2.5 failure mode. "Data fills nominal-only" is therefore structural, not a
  convention. What makes a context a data context is an explicit constructor flag
  (`gnano.events(src, is_data=True)`-shaped; exact spelling pinned at m48 freeze) — the survey's
  universal data special-casing, made explicit.
  Sketch (binding shapes; helper-verb spellings pinned at m48 freeze):
  ```python
  events = gnano.events(src)                                  # MC event context (immutable)
  events = graphed.vary(events, "pu",                         # event-level weight
                        pu_sf(events.Pileup.nTrueInt), is_weight=True,
                        up=pu_sf(events.Pileup.nTrueInt, systematic="up"),
                        down=pu_sf(events.Pileup.nTrueInt, systematic="down"))
  member = lambda i: gak.firsts(lhe_w[gak.local_index(lhe_w) == i])   # inner index, see below
  events = graphed.vary(events, "pdf", member(0),             # tags beyond up/down (§1.1)
                        is_weight=True,
                        variations={f"{i}": member(i) for i in range(1, 103)})
  events = graphed.vary(events, "jes",                        # lockstep object shift
                        Jet={"up": j_up, "down": j_dn}, MET={"up": m_up, "down": m_dn})
  jets = events.Jet[events.Jet.pt > 25]                       # universes flow (§2.3)
  sel  = events[gak.num(jets) >= 4]                           # derived context
  sel  = graphed.vary(sel, "btag", btag_sf(sel.Jet),          # selection-scoped weight
                      is_weight=True,
                      up=btag_sf(sel.Jet, "up"), down=btag_sf(sel.Jet, "down"))
  h.fill(sel.Jet.pt)                                          # per-OBJECT fill: the value stays
                                                              # UNFLATTENED so the ambient event
                                                              # weight can broadcast against it
                                                              # (§6.1d); the evaluator flattens
                                                              # both (boost.py:39-47,60-71)
  ```
  **Two spellings in that sketch are measured, not assumed** (r11 — an earlier revision spelled
  both in a form that does not exist, exactly the mid-freeze discovery §4.1's `full_like` note
  exists to prevent):
  (i) **there is no tuple subscript on the awkward-idiom `Array`** — `Array.__getitem__` accepts
  an `Array` mask, `str`, `list[str]`, `slice` or `int` and raises `TypeError` otherwise
  (`array.py:344-371`; measured: `w[:, 1]` → `TypeError: unsupported index (slice(None, None,
  None), 1)`), tuple subscripts exist only on the numpy idiom (`numpy/array.py:132-136`), and no
  gak function takes an arbitrary inner index. The expressible form is the masked one above —
  measured this session against `graphed-latest`: `gak.firsts(w[gak.local_index(w) == 1])` over
  `[[1,2,3],[4,5,6]]` materializes `[2.0, 5.0]`. (A first-class inner-index verb would be a gak
  addition; it is NOT scoped in m48–m51.)
  (ii) **`Histogram.fill` is positional** — `fill(self, *args: Array, weight=…, sample=…,
  threads=…)` (`graphed-histogram src/graphed_histogram/boost.py:153-163`), so `h.fill(pt=…)` is
  an unexpected keyword. Named-axis kwarg fills exist only in the `hist.graphed` fork (cba
  §histogram §3), which is not in m48's repo scope.
  The neutral context *mechanism* (lineage, ambient weight, fill-inference seam) lives in
  `graphed` proper; the nanoevents-flavored constructor is awkward-idiom and lives in
  `graphed.awkward` (factorization rule preserved). The loose `graphed.vary` on Arrays (§2.1a)
  remains public — the context is built on it, not beside it.

## §3 IR and optimizer treatment

- **§3.1 (No new NodeKey.)** No Rust IR variant, no serialize tag, no optimizer change is added for
  variations. The varied universes are ordinary nodes; sharing is interning
  (`src/store.rs:73-88`); the m4 frozen scaling contract
  (`tests/frozen/core/m4/test_systematics.py`) continues to bind unchanged. Any future first-class
  node (introspection-driven) is Phase 2 and follows the full M40 checklist (cba §ir-rust §1).
- **§3.2 (Determinism.)** Expansion order is deterministic: labels in `graphed.labels` order,
  recording
  per §2.3. Two-run byte-identical compilation of a variation-expanded graph is a frozen m48
  anchor (§10) in the strong R22.3 form (fresh processes, differing `PYTHONHASHSEED`).
- **§3.3 (Anti-quadratic guard gains a variation topology — in a NEW frozen file.)** A new frozen
  benchmark (`tests/frozen/core/m49/…`, replicating the `test_benchmark.py:10,40-53` pattern;
  **the m4 files are untouched** — frozen tests are read-only, §B.6) pins the variation shape.
  **The builder is bound explicitly, because the pinned integers depend on it**: source → a shared
  prefix of D ops → per universe {one varied fork op, K chain ops, **exactly one terminating
  reduction node**}, every universe's reduction separately marked as an output, N counting nominal
  (the m4 `_systematics` builder funnels all variations into ONE output and would make the
  assertion vacuous, review r0). N ∈ {16, 32, 64, 128}. Under that topology the exact reduced shape
  is `stages == N + 1` and `reduced_nodes == 2N + 2` — re-measured this session against
  `graphed-latest` (D=500, K=50): N=16 → stages 17 / reduced 34; N=128 → stages 129 / reduced 258,
  matching cba §optimizer §2 exactly. **The terminating reduction is load-bearing**: the same
  builder WITHOUT it reports `reduced_nodes == N + 2` (N=16 → 18, N=128 → 130), so a suite that
  omits it freezes an assertion a correct reducer fails. A fill IS a reduction, so the
  with-reduction shape is also the realistic one.
  Plus a linear-growth bound (time(128)/time(16) < 24.0, the m4 threshold style), replicating the
  m4 noise floor (`base = max(times[SIZES[0]], 1e-4)`) and best-of-N timing
  (`test_benchmark.py:28-33,40-43`). **This is the ONE frozen wall-clock gate in m48–m51, and it is
  a deliberate, named carve-out to R0.10a**: the project plan's M4 mandates a CI benchmark that
  fails on super-linear reduction time, and `tests/frozen/core/m4/test_benchmark.py` is the frozen
  precedent that discharges it. Every other performance claim in this plan (§6.2 axis scaling,
  §6.4c compression) is demoted to an R0.11 implementer-report measurement precisely because it has
  no such mandate. Threshold headroom is measured, not assumed: cba §optimizer §2 records 3.1 ms at
  N=16 and 16.7 ms at N=128, a ratio of ≈5.4 against the 24.0 gate.
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
  (lit §ewkcoffea-confirmed). The binding v1 form is **`gak.full_like(<an existing per-event
  Array>, sf)`** — a real recorded graph op producing a constant-valued Array shaped like an
  existing one (`python/graphed/awkward/functions.py:612-616`; already parity-pinned by
  `tests/frozen/awkward/m24/test_interface_parity.py:74-76`) — or ordinary arithmetic on such an
  Array. What does NOT exist is a **partition-aligned** constant Array with no shape donor (r12 —
  the r11 sentence said "a constant Array from *nothing*", which is false as stated):
  `graphed.numpy` ships donor-free `full`/`ones`/`zeros`/`empty`/`arange`/`linspace`
  (`python/graphed/numpy/creation.py:31-75`, all in `__all__`,
  `python/graphed/numpy/__init__.py:578-598`), but each records an **eager fixed-shape in-memory
  Source** (`creation.py:27-28`, `session.source(name, form=…, data=arr)`), and a plan built
  through `aggregate_plan` binds exactly ONE source (`python/graphed/aggregate.py:96-101`,
  `{self.source_name: chunk}` at `:57-63`), so a second source makes `evaluate_ir` raise
  `"no data bound for source"` (`python/graphed/execute.py:104-105`). cba §histogram §1's
  "no constant-Array constructor" grep was scoped to the session/array modules and did not cover
  `graphed/awkward/functions.py` or `graphed/numpy/creation.py`. The gap — a constant/scalar
  broadcast helper needing no donor and no second source — is parked in §11.
- **§4.2** Fills accept a `Varied` entry in the M29 `weight=[...]` factor list (`boost.py:166-174`);
  lowering emits the nominal fill node + one sibling fill node per label under the §2.4 rule,
  differing only in the varied input ids — everything upstream interns. All siblings join the
  **same group plan**; the single-pass property is frozen-witnessed on the corpus run itself in
  m48 (§10), not only on a toy graph. With the §2.6 event context, weight variations typically
  reach fills **ambiently** (registered once via `graphed.vary(events, …, is_weight=True)`,
  applied per §6.1d); the explicit factor-list form remains the primitive underneath and stays
  public.
- **§4.3** Weight variations MUST NOT change selection. The frozen m48 anchor is **structural**,
  not only behavioral (equal counts is a tautology under §3's expansion — the selection nodes are
  the same interned ids by construction, an R0.10 trap flagged in review r0): **the selection
  cone's node ids MUST be identical across all weight labels.** (r9's alternative wording — "the
  §3.4 impact set contains no node outside the fill's weight-input cone" — is WITHDRAWN in r10: it
  is false for a correct implementation, because a label's output IS its sibling fill node, which
  by construction is not reachable from nominal's output and therefore always lands in the impact
  set while sitting *downstream* of, not inside, the weight-input cone. The two are not equivalent;
  the node-id form is binding, and the m48 anchor quotes it verbatim.) **The EXTRACTION mechanism
  is bound too** (r12 — two revisions were spent on the predicate and none on how to obtain its
  operands, which invites a third): in a weight-only program the selection is a plain unvaried
  `Array`, so "the selection cone" is singular and the assertion has content only in the per-label
  form — compute `reachable(fill_node[label])` per label via `session.walk`
  (`python/graphed/session.py:245-252`), take `reachable(selection_mask)` the same way, and assert
  that its intersection with each label's reachable set is IDENTICAL across labels (and equal to
  `reachable(selection_mask)` itself). `fill_node[label]` comes from the §6.1c per-slot output
  indices / §7.2 `(output, label) → node id` map, the only public per-label fill-node channel
  (`Histogram._fill_nodes` is private). The repaired impact-set form is an equivalent public
  cross-check and MAY ride along: `impact(L)` minus L's own output node is disjoint from
  `reachable(selection_mask)`. The m05
  equal-counts check rides along as a sanity assertion.

## §5 Shift-path lowering

- **§5.1** A shift variation is a `Varied` at a kinematic quantity (column or record), created
  **before selection** — the corpus applies JES at the jets record before the pt cut
  (`systematics.py:60-61`) and the m9 AGC fixture shifts `Jet.pt` before its jet mask
  (`agc.py:106-107`); broadcast (§2.3) re-records the selection/observable cone per label;
  interning shares everything else. The *defining* behavior is per-universe re-derivation of the
  selection (cutflow divergence). **The general shift contract asserts NO monotonicity or ordering
  across labels** (owner directive, 2026-07-30): the `jes_up > nominal > jes_down` ordering is a
  property of the corpus's monotone-scale JES *fixture* and MUST stay scoped to it — a JER-SF
  re-smearing shift migrates events in both directions (§5.5), and any suite or API language
  implying shifts order is a test-authoring error.
- **§5.2 (Witnesses that sharing engaged — R0.10.)** The m49 suite pins mechanism witnesses, not
  just results: (a) **arena-delta witness on the §3.3 topology with a literal expected integer**
  (the m4 style — on the §3.3 builder, one universe = {1 varied fork op, K=50 chain ops, 1
  terminating reduction}, so going N=1→2 adds exactly `K + 2 = 52` nodes; re-measured this session
  against `graphed-latest`. **The terminating reduction is load-bearing here too**: the same
  builder without it measures Δ = 51, so the literal must travel with the builder. A self-derived
  `delta == len(cone)` comparison is tautological, review r0). Labels structurally identical to a
  prior label dedup to Δ = 0 by §1.2 — that case is witnessed separately as the dedup feature, in
  the **m48 §1.2 label-out-of-identity anchor** (§10), not under this witness. (b) **single-read
  witness bound to the reference-matrix run itself**: the
  read-counting partitioned source (m23 pattern) asserts `part_reads == n_partitions` — not
  `n_partitions × n_labels` — on the SAME Session/plan that reproduces the corpus references
  (the m49 **frontend** half, §10, where the vendored references live), so a per-variation re-run
  loop cannot pass. (c) **reduced-stage shape** — the shared
  prefix appears in exactly one stage.
- **§5.3 (Projection.)** Column projection is the union over all requested outputs — correct today
  with zero changes (`read_columns` takes `Sequence[Array]`, `projection.py:109-147`); m49 pins a
  test where a shift needs an extra column (e.g. binned SF needing `Jet.eta`) and the union grows by
  exactly that field. Per-label projection stats are exposed via §3.4 so the read-width cost of a
  shift is visible — **and that exposure is anchored in the same m49 test** (r12; it was binding
  but unanchored, and §3.4's own anchor covers impact sets, not read widths, so it could have
  shipped unimplemented with every m49 anchor green): the same test asserts the stats report the
  shifted label's extra column. Per-variation partition-level projection splitting is Phase 2.
- **§5.4 (Boundary restriction, explicit.)** v1 REFUSES (clear `NotImplementedError` naming the
  label and the boundary) a variation whose cone crosses an `Exchange`/`Join` node — the m39/m40
  plan builders are single-boundary (`shuffle.py:170,232`) and silent miscompilation is worse than
  refusal. The refusal test carries a **positive control**: a variation entirely *downstream* of a
  Join/Exchange compiles and produces correct results (a blanket "Varied near Join raises" must
  fail the suite). Generalizing the builders is named Phase 2 (§11).
- **§5.5 (Stochastic shifts — JER-SF re-smearing is first-class; determinism still binds.)** A
  shift variation MAY be stochastic (MC jet re-smearing under a jet-energy-resolution scale
  factor). Two binding rules, both grounded in coffea's own implementation (local checkout @
  `f34b8bdf`, measured representative of upstream — lit §coffea-sys): (a) **randomness MUST be a
  deterministic pure function of event content** — the precedent seeds PCG64 from the input
  array's own bytes (`rand_gauss`, `coffea jetmet_tools/CorrectedJetsFactory.py:36-47`); global
  RNG state, wall-clock, or per-run seeds are forbidden — the R0.4/R12 determinism gate applies
  to varied graphs unchanged. (b) **One draw, all universes**: the random vector is drawn once
  and shared — coffea's `jer_smear` takes a single `jet_resolution_rand_gauss` while only the SF
  column varies per label (`:64-95`, hybrid `detSmear`/`stochSmear`, where `deltaPtRel` is signed
  and the stochastic branch scales a signed gaussian — hence non-monotone by construction) — so
  under `vary` the draw node lives in the shared prefix and interns once (§3). The m49 suite
  carries a JER-SF-style fixture (§10) whose witnesses assert bidirectional migration and
  run-to-run byte-identity, never ordering (§5.1).

## §6 Sinks: histogram fills (§6.1–§6.3) and variation-aware write-out (§6.4)

- **§6.1 (MVP shape: sibling fills, named results.)** `Histogram.fill` accepting `Varied` axis
  values and/or `Varied` weight factors lowers per §4.2/§5.1 under the §2.4 rule. Binding result
  and lowering shape:
  (a) **Per-output label sets** (this rule is **scoped to the DEFAULT sibling-fill lowering**;
  §6.2's opt-in axis mode has a third result shape, bound there). Each output's mapping carries exactly the union of labels reaching
  *that* output — `{output_name: {label: hist}}`, nominal always present; an output no variation
  reaches returns a bare `hist` (NOT `{"nominal": hist}`), so unvaried programs see today's shapes
  unchanged. Absent labels are absent, never silently duplicated from nominal. The declared result
  type is therefore the value-dependent union
  `dict[str, bh.Histogram | dict[str, bh.Histogram]]` — a real typing cost under the DoD's
  `mypy --strict` on src AND tests, accepted for the backward-compatibility win and paid for
  explicitly: the combine BRANCHES on the two shapes (today's `_add_groups` assumes a homogeneous
  mapping, `boost.py:120-122`), and a bound narrowing helper is provided so callers do not
  hand-roll `isinstance` — `graphed.universe(result[name], label)` and `graphed.labels(result[name])`
  work uniformly on BOTH shapes (§2.2), a bare `hist` reading as the single label `"nominal"`.
  (b) **Structural fill-node arity** (again **sibling-mode only**). A fill combining shift labels
  S and weight labels W records
  exactly `1 + |S| + |W|` fill nodes — never the product (frozen-counted via the staged-fill list,
  the §2.4 discriminator). Axis mode's arity is `1 + |S|` and is stated in §6.2, so m50 does not
  land a feature contradicting a count frozen in m49.
  (c) **The single-histogram `.plan()` path refuses varied fills**: `_SumFills` sums ALL staged
  fill nodes into one histogram (`boost.py:88-98`) and would silently merge universes; varied
  histograms route through the group-reduce path (`_GroupReduce` `{label: hist}` generalized to
  two-level keys, `boost.py:100-122`), and `.plan()` on a varied `Histogram` raises, pointing at
  the group API. **The reducer's LAYOUT changes shape, and that is binding, not an implementation
  detail** — "generalized to two-level keys" is satisfiable while shipping the §7.2 bug: today
  `layout` is `tuple[tuple[str, int, str], ...]` = `(label, n_fills, spec)` sliced
  **positionally** over the distinct-output list (`boost.py:100-117`, `for j in range(i, i + k)`,
  built from `len(h._fill_nodes)` at `:282`), so the moment two marked fills intern to one node —
  the case §1.2 mandates and m48 freezes — `sum(k)` exceeds `len(values)` and the reducer
  mis-slices or `IndexError`s (`aggregate.py:57-65` passes `evaluate_ir`'s values straight to
  `reduce`; `mark_output` de-dups, `src/store.rs:147-156`; `execute.py:126` returns one value per
  DISTINCT output). Binding: **`layout` carries per-slot output INDICES**, not counts —
  `tuple[tuple[str, tuple[int, ...], str], ...]` (or `{(output, label): [indices]}` for the
  two-level shape) — derived frontend-side from the compiled output list per §7.2, so a shared
  node id **replicates** into every slot that needs it instead of shifting positions. (Latent
  today for two unvaried histograms with identical fills; variations make it routine.) **The
  layout's third element — the per-slot spec — is the FILL node's spec, not the histogram
  object's** (r12): today every consumer takes it from the histogram (`boost.py:282`
  `layout = tuple((label, len(h._fill_nodes), h._spec) …)`; `_GroupZero` builds `zero_of(spec)`,
  `:100-130`; `Histogram.plan` passes `_SumFills(self._spec)`/`_ZeroHist(self._spec)`, `:245-255`),
  which is fixed in `__init__` (`self._spec = spec_of(self)`, `:146-150`) — so under §6.2's
  fill-time axis declaration the zero/identity histogram would lack the `"variation"` axis the
  evaluator's output carries, and `_add_groups`' `+` would fail or mis-combine. Binding: the slot
  spec is the spec baked into that fill node's params (`:180-212`).
  (d) **Ambient-weight application (the §2.6 completion of register-then-forget).** `fill` reads its
  input Arrays' **context handle** (§2.3e — a Python-object attribute on the frontend wrapper,
  outside node identity; NOT `Provenance`, which is source-location only,
  `provenance.py:26-33,66-79`, and NOT `Session._provenance`/`sourcemap()`) and **auto-applies that
  context's ambient weight** (§2.6c lineage rule — contexts are immutable, so *which context* fully
  determines *which registrations*): the fill's label set is the §2.4 union of value-borne labels,
  ambient-weight labels, and explicit `weight=[...]` factor labels — so a plain Jet-pT fill
  yields the jes/jer universes AND the pileup/PDF universes with zero per-fill bookkeeping (the
  owner's simultaneity requirement). **The union's ORDER is bound here too**, because §2.4 binds
  only a BINARY combination while this is three-way (and a fill may carry several varied axis
  values): the fill folds LEFT in a fixed operand order — **axis values in argument order, then
  the ambient weight, then explicit `weight=[...]` factors in list order** — each fold applying
  §2.4. Without it two conforming implementations produce different label orders for one program:
  a determinism-gate difference (§3.2) and a different `_GroupReduce` layout (§6.1c).
  `weight=[...]` *adds* factors; `unweighted=True` opts out
  (counts histograms); inputs whose contexts sit on one ancestry chain unify to the
  **most-derived** context, **and every ancestor-context VALUE is re-indexed to the unified
  context by the intervening derivation mask(s), label-aligned per §2.4** (r12): unification alone
  is not enough, because §2.6c re-indexes the ambient weight to the derived row count, so
  `h.fill(events.MET.pt, sel.Jet.pt)` would otherwise apply `sel`'s weight (row count = |sel|)
  against a value read at `events`' row count — a length mismatch whose only symptom is the
  execution-time refusal below, whose message is about the wrong thing. Re-indexing is the same
  operation §2.6c already binds for the ambient registry, applied to the values.
  Contexts on **divergent branches are a hard error** naming both. **The
  fill raises it itself**: §2.3e's op-level rule is early detection, but the fill is a combining
  point no op precedes — it is the first place independent axis/weight/sample handles meet
  (`boost.py:154-212` collects them into one `inputs` list and records one node) — so the fill
  runs the same most-derived unification and divergence check across all axis values, all explicit
  weight factors, and the winning context's ambient weight.
  Context-free (loose) inputs alongside contexted ones adopt the unified context; an all-loose
  fill is unweighted (the r4 primitive path, still supported). **Every weight factor the fill
  applies — the ambient one AND explicit `weight=[...]` factors — is broadcast to the fill's value
  structure**, not just the ambient one: the evaluator flattens each input independently and
  multiplies factors elementwise *after* flattening (`boost.py:60-71`, `weight = weight *
  _flat(rest.pop(0))`), so in a per-object fill an unbroadcast per-event explicit factor
  (`weight=[events.genWeight]`) flattens to `n_events` against `n_objects` — the mainline idiom of
  "ambient registrations plus one explicit factor" would length-mismatch.
  The mechanism is bound, because the r9 wording
  was unsatisfiable as written: **a per-object fill MUST pass its value UNFLATTENED**
  (`h.fill(sel.Jet.pt)`, the sketch — not `gak.flatten(...)`, which destroys the jagged
  structure there is nothing left to broadcast against), and the frontend then records a
  **broadcast-to-value-structure seam** (see below) relying on the evaluator's existing
  independent per-input flatten (`boost.py:39-47,60-71`).
  **The broadcast is a neutral, backend-dispatched seam, NOT a named gak call** (r11): the fill
  lives in `graphed-histogram`, whose runtime dependencies are `["graphed",
  "boost-histogram>=1.4", "numpy>=1.24"]` with awkward only in the dev extra
  (`graphed-histogram pyproject.toml:20-21,24-38`), and `gak.broadcast_arrays` records the
  awkward-namespaced op `"ak.broadcast_arrays"` (`python/graphed/awkward/functions.py:677-685`)
  with no numpy-idiom equivalent (`grep -rn broadcast python/graphed/numpy/*.py` → a docstring
  mention only). Naming it in a binding requirement would make the neutral seam awkward-only,
  the very factorization rule §2.1 invokes. Binding: the seam is **`graphed.broadcast_like(value,
  factor) -> Array`** (spelling pinned at m48 freeze) — a neutral entry point owned by `graphed`
  proper and dispatched to the backend idiom, taking an ARBITRARY factor, **not a context method
  that can only reach the ambient weight** (r12 — the r11 wording bound the requirement to "every
  weight factor" while binding a mechanism that only the context could drive, which cannot reach a
  user-owned `weight=[events.genWeight]` factor, cannot be spelled inside `graphed-histogram` as a
  gak call, and does not exist at all in an all-loose fill, which §6.1d still supports). The fill
  applies it to the ambient weight and to every explicit factor alike. The awkward implementation
  records `ak.broadcast_arrays`, the numpy idiom documents a
  no-op (rectilinear, already aligned) or a refusal. The seam is owned by `graphed` proper; the
  awkward implementation by `graphed.awkward`; `graphed-histogram` gains no awkward dependency.
  **The already-flattened-value case is an EXECUTION-time refusal, not a record-time one** (r11 —
  the r10 wording had no bound raiser and no static discriminator): a legitimately per-event value
  (`gak.firsts(...)`, `gak.num(...)`, `MET.pt`) and a flattened per-object value
  (`gak.flatten(sel.Jet.pt)`) have identical 1-D forms and differ only in runtime length, and the
  only record-time alternative is an unbounded cone-walk hunting a flatten node — which
  false-positives on `gak.flatten(x, axis=2)` (still jagged, still per-event). **The refusal is
  bound as a CONTRACT, not as a named class** (r12 — the r11 wording named `FillEvaluator` as the
  raiser, which the bound mechanism never reaches: the broadcast seam is a recorded graph node
  UPSTREAM of the fill, so it executes first and dies there. Measured, awkward 2.12.0:
  `ak.broadcast_arrays(ak.Array(np.arange(7.0)), ak.Array(np.arange(3.0)+1))` →
  `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`, while the same
  call against a legitimately jagged 3-row value succeeds. A `FillEvaluator` raise is what you get
  in a world with NO broadcast seam). Binding: **at execution, a varied fill whose weight input
  cannot be broadcast to the axis values' structure fails with a `graphed` error naming the
  OFFENDING FACTOR** — the ambient weight or the explicit `weight=[…]` entry by position — **and,
  when the offender is a per-event factor against a per-object value, pointing at "pass the value
  unflattened"**. The seam's awkward implementation wraps its evaluator so awkward's `ValueError`
  is translated into that message; nothing binds WHICH class raises.
  Frozen-witnessed against a manually broadcast reference.
  This reproduces the corpus reference layout (independent per-variation histograms — UHI, no
  invented formats).
- **§6.2 (Scaling shape: the variation axis, m50 — weight labels only.)** An opt-in fill mode
  (**opt-in spelling pinned at m50 freeze** — r12; every other new surface in this plan carries
  that clause and this one did not, leaving the m50 fixture unwritable) lands
  **weight-label** variations in ONE histogram with a **non-growth, pre-declared, sorted
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
  sibling-fill decomposition. **Axis-mode fill-node arity is therefore `1 + |S|`** (weight labels
  collapse into the evaluator-side loop), which is why §6.1b's `1 + |S| + |W|` is scoped to
  sibling mode.
  Non-growth is required: identical spec per partition keeps `+` combine safe and deterministic
  (PocketCoffea's deterministic pre-declared axis lesson; growth axes stay Phase 2 per the existing
  `_spec.py:70,74` refusal). **Who declares the bins is bound, because non-growth alone is a
  silent-drop hazard**: measured, boost_histogram 1.7.2, a non-growth `StrCategory` does NOT raise
  on an undeclared string — it has an overflow bin
  (`Traits(underflow=False, overflow=True, growth=False, …)`), so filling `['nominal','bogus',
  'jes_up']` into `StrCategory(['nominal','jes_up','jes_down'])` gives `h.sum() == 2.0` while
  `h.sum(flow=True) == 3.0`: the label just vanishes — exactly the "hand-maintained name lists where
  a typo silently drops a systematic" failure mode §2.5 exists to delete. Binding: (i) **the
  FRONTEND declares the axis, at FILL time** — the point the spec enters node identity — from the
  §6.1d inferred label set (which IS known at fill time), so the spec is
  identical per partition by construction and combine-safety follows. **"At plan time" is
  measurably unimplementable** (r11): a `Histogram`'s spec is fixed in `__init__`
  (`self._spec = spec_of(self)`, `graphed-histogram src/graphed_histogram/boost.py:146-150`) and
  is baked into node identity at `fill` (`chash = content_hash(self._spec)`, `params={"spec":
  self._spec, …}`, `self._evaluators[chash] = evaluator` — `:180-212`), so adding a `"variation"`
  axis after the fill nodes exist would leave nodes, evaluators, `_GroupReduce`'s per-slot spec
  and `_GroupZero` disagreeing, and repairing it needs either re-recording every fill at plan time
  (unbound, large) or mutating interned node params (forbidden, §3.1/§1.2). Fill-time declaration
  needs no such thing: each fill node's params/evaluator already carry THEIR OWN spec.
  **Cross-fill agreement rule**: a second fill into the same axis-mode histogram whose inferred
  label set differs from the first's is a hard error naming the mismatch (the alternative is two
  incompatible specs in one histogram, uncombinable at `_add_groups`).
  **(i-bis) Axis-mode RESULT SHAPE** — §6.1a binds only the sibling shapes, so this is stated
  here: an axis-mode varied output returns a **bare `bh.Histogram` carrying the `"variation"`
  axis**, which is *indistinguishable by type* from an unvaried output. `graphed.labels` and
  `graphed.universe` therefore recognise it explicitly: `graphed.labels(h)` = the variation
  axis's bin set (NOT `["nominal"]`), `graphed.universe(h, label)` = **that label's slice along
  the variation axis**. Without this the §6.1a narrowing helper answers `["nominal"]`
  for a histogram that does contain `jes_up` and `KeyError`s on extracting it — a confidently
  wrong bookkeeping answer, the exact failure class §2.5 exists to delete. The helper is uniform
  over all THREE shapes (bare-unvaried, `{label: hist}`, bare-axis-mode).
  **The SPELLING of that slice is bound, because the obvious one does not work** (r12 — the r11
  text bound `h[{"variation": label}]`, which raises): measured on boost_histogram **1.7.2 and
  1.8.0**, `bh.axis.StrCategory([...], name="variation")` is a `TypeError` (no `name=` kwarg) and
  a string-keyed dict index raises `TypeError: list indices must be integers or slices, not str`
  — with or without `bh.loc`, and regardless of the axis's metadata. Named-axis dict access is a
  `hist`-package feature, and `hist.graphed` is out of m48's repo scope (§2.6 note (ii)) and out of
  m50's. The only working form is positional: `h[{axis_index: bh.loc(label)}]` (measured). Binding:
  (1) the frontend **writes the axis name into `axis.__dict__["name"] = "variation"`** — the `hist`
  convention `graphed-histogram`'s spec codec already round-trips as axis metadata
  (`src/graphed_histogram/_spec.py:31-37` `_metadata_of` harvests `__dict__`, `:81-84`
  `_restore_metadata` writes it back), so the handle survives the spec/`zero_of` rebuild
  (measured: after setting it, `h.axes.name == ('variation',)`); (2) `graphed.labels`/
  `graphed.universe` resolve the axis POSITION from that name and slice by index. Nothing binds a
  literal subscript expression.
  (ii) **A user-declared `"variation"` axis is NOT supported in v1** (r12 — the r11 text hedged
  "if a user-declared axis is supported at all" while three m50 anchors froze behaviour that
  presupposes it; an implementer taking the hedge would conform and fail the frozen suite). The
  frontend declares it, always, from the inferred label set, so a label cannot be undeclared and
  the declared bin set IS the inferred set by construction. This is not merely a scoping
  preference: a user-declared axis is **unfillable today** — `Histogram.fill` requires one array
  per axis (`graphed-histogram src/graphed_histogram/boost.py:160-161`, `if len(args) !=
  len(self.axes): raise TypeError(...)`), so a histogram constructed with a variation
  `StrCategory` rejects the user's N-array fill outright, and supporting it needs an arity
  carve-out this plan does not scope. **The residual silent-drop hazard the measurement above
  names is still gated**, by the frontend-side invariant instead of a user-facing error: the
  declared bin set equals the inferred label set exactly, witnessed by `h.sum(flow=True) ==
  h.sum()` (a stale or partial declaration otherwise buries the difference in the overflow bin).
  User-declared axes are parked in §11. (iii) The frontend, not the user, imposes the sort, so
  "sorted" and "pre-declared" cannot conflict. M29's identity discipline binds: new
  params/spec content only when the feature is used. The sorted bin order is **lexicographic over
  label strings and MUST NOT be
  read numerically** (r7): determinism and combine-safety are unaffected by numeric-tag labels —
  sorting is a total order over arbitrary strings, every partition still declares an identical
  spec — but `murf_10` sorts before `murf_2`; positional/plot ordering for numeric families comes
  from §9.1's parsed-value introspection, never from bin index.
- **§6.3** Data / no-variation paths are unchanged, gated by both in-tree golden patterns (review
  r0): a **committed golden GIR blob** for an unvaried fill graph (the
  `core/m40/test_join_serialize.py:84-99` pattern) plus **params-key absence** (`assert
  "<new key>" not in node["params"]`, the `m29/test_multi_weight_fills.py:93-99` pattern).
- **§6.4 (Variation-aware write-out — skim augmentation; NEW scope, collaborator-directed
  2026-07-30.)** Writing varied data (`to_parquet`, the uproot fork's `graphed_write`) is a
  first-class sink, not a Phase-2 parking: the surveyed frameworks each hit this wall and bolted
  around it (RDF Snapshot's per-event validity bitmask; mkShapesRDF re-implementing `Vary` for
  its Snapshot stage as suffixed columns + OR-of-cuts — Part I §2), and graphed's write path is
  measured greenfield (zero variation machinery, zero metadata use, one seam method per backend —
  Anchors, write-seam rows). Binding:
  (a) **Row rule — OR of selections, with the selection supplied EXPLICITLY.** When the written rows
  pass through a varied selection, the writer materializes the **superset**: rows passing ANY
  universe's selection, nominal included. The OR is recorded as ordinary graph ops over the
  per-label masks (`getitem`/`gak.mask` — no mask algebra exists in the IR and none is added).
  **The varied write API takes the mask(s), it does not infer them**:
  `graphed.awkward.to_parquet(record, select=…)`-shaped (exact spelling at m51 freeze — and it is
  the **awkward-idiom** verb: `to_parquet` is exported only from `graphed.awkward`
  (`python/graphed/awkward/__init__.py:14,30`; `python/graphed/awkward/io.py:206-216`), the numpy
  idiom having its own 1-D-capped implementation, `python/graphed/numpy/io.py:158-173`; §6.4f's
  "numpy backend EXEMPT" therefore means *the numpy-idiom function refuses*, not that a new
  neutral dispatcher is introduced), where
  `record` is PRE-selection (see the entry check below) and `select=` carries the `Varied`
  mask(s). **`select=` is per SELECTION LEVEL, not one row mask** — this is what makes §6.4d's
  object-level cutflow implementable at all: it accepts either a single `Varied` row mask, or an
  ordered per-depth mapping `{0: event_mask, 1: jet_mask, …}` of `Varied` masks, one per level
  that varies. **What the writer does with them is exact** (r12 — the r11 "applies NONE of them"
  sentence read against this paragraph's own superset rule and §6.4b/§6.4d's "on the event-row
  superset", producing two defensible readings that yield different files): it applies the
  **level-0 OR** to the stored ROWS — that IS the superset — and applies **no other supplied mask**
  to the stored buffers (that is the point of §6.4d's widest-common-structure rule: inner cuts are
  never applied, or the deltas lose their common shape); and it stores **one packed per-label
  validity mask per supplied level, level 0 included**. Without a per-level channel
  §6.4d is unsatisfiable in both directions: passing the post-object-cut record
  (`jets[jets.pt > 25]` under a JES shift) trips §6.4d's offsets refusal — which IS the
  object-migration case m51 requires as a positive control — while passing the pre-object-cut
  record leaves the writer with no knowledge of the per-jet cut and so unable to store inner
  masks or satisfy §6.4c. This is binding
  because the implicit form is not implementable under §3.1: if the user writes
  `to_parquet(sel.Jet)` with `sel = events[nominal_mask]`, producing the same fields on superset
  rows would require substituting the OR mask INSIDE an already-interned, immutable expression —
  a node rewrite the IR forbids, needing a second record-time expansion pass plus an undecidable
  "which node in the cone is *the* selection" rule (several selections; selection not outermost).
  With `select=`, the writer owns the masks, builds both the OR and the per-label masks, and no
  retargeting is needed.
  **The "record is pre-selection" precondition is a DECIDABLE entry check, not "by construction"**
  (r11): the r10 refusal ("a record expression that already embeds a `Varied` selection") is not
  mechanically decidable — a record varied because its VALUES vary (the expected input, §6.4b) and
  one varied because a varied MASK was applied are both just `Varied` containers of Arrays, §1.2
  keeps labels out of the IR, and telling them apart needs the same undecidable cone rule this
  paragraph rejects three lines above; it also misses the case that actually corrupts data (a
  NON-varied embedded selection, `sel = events[nominal_mask]` then `select=varied_mask`, which
  applies the superset mask to already-selected rows, silently). Binding replacement: **TWO
  predicates, not one** (r12 — the r11 single offsets predicate provably cannot decide the
  embedded-selection case, which the m51 anchor names as its positive control: that predicate
  compares per-label members against nominal WITHIN the record, while the corruption is a
  record-vs-mask ROW-SPACE mismatch it never inspects. With `sel = events[nominal_mask]`, either
  `sel.Jet` is a plain `Array` and the predicate is vacuous, or every member was masked by the SAME
  non-varied mask and all offsets equal nominal's — it passes either way. The same hole swallows
  the chained-context case this section's own bridge creates, `graphed.selection(sel2)` for
  `sel2 = sel[mask2]`, which lives in `sel`'s row space while the canonical spelling writes
  `events.Jet` in root row space):
  **(1) MULTIPLICITY** — every per-label member's offsets equal nominal's at every level the
  writer will store (§6.4d's own rule, the multiplicity-changing refusal);
  **(2) ROW-SPACE AGREEMENT** — every supplied `select=` level must be a mask over the SAME row
  space as the record. Bound structurally via §2.6b lineage: each mask must be the selection
  deriving directly from the context the record was read from (`graphed.selection(ctx)` of the
  record's own context handle, §2.3e), which is decidable frontend-side because lineage is a Python
  object chain, plus a runtime row-count equality between the record and each level-0 mask. A
  record read from an ancestor or a sibling context is refused, naming both contexts.
  Each predicate has its own error message, and the m51 anchors name which predicate decides which
  positive control. Both are **execution-time**, per partition — see the raiser binding below.
  **Writing from a context (§2.6 idiom).** In the owner-locked context idiom the user holds a
  derived context (`sel = events[mask]`), not the mask, and contexts expose no mask accessor
  (§2.2/§9.1 list `labels`/`universe`/`nominal`/`weight`/`variations` only) — so without a bridge the m51
  sink would be reachable only from the loose §2.1a style, one milestone after §2.6 makes the
  context the primary idiom. Binding bridge: **`graphed.selection(ctx)`** returns the `Varied`
  mask that derived `ctx` from its parent (the §2.6b lineage already retains it; a root context
  returns `None`), so the skim spelling is
  `to_parquet(events.Jet, select=graphed.selection(sel))`. Frozen-anchored in m51.
  **Where the checks RUN (r12 — the r11 "at entry … run once up front" is not achievable for the
  offsets half).** Offsets are data. At the `to_parquet` call the frontend holds a recorded graph
  and typetracer forms, not per-label offsets, and the write is evaluated **per partition inside
  the worker**: `_WritePart.__call__` reads the partition, calls `evaluate_ir`, then writes one
  part (`python/graphed/awkward/io.py:111-127`; the per-partition task graph is built by
  `python/graphed/write.py:32-43`). Binding: predicate (2) (row-space/lineage) IS a record-time
  check and raises from the `to_parquet` call; predicate (1) (offsets) is an **execution-time,
  per-partition check raised by `_WritePart` BEFORE any buffer is stored**, surfacing through the
  executor's error path — the same treatment §6.1d already takes for its length check. m51's
  anchors are worded accordingly; do NOT freeze a record-time raise for the offsets predicate.
  (b) **Column rule — augmentation.** The written record carries the user's fields evaluated in
  the **nominal** universe (on superset rows), PLUS appended per-label reconstruction data: for
  every stored field whose value differs per label, a same-shaped delta column; and per-label
  selection masks (the varied cutflow) plus the nominal mask, so each universe's row set is
  recoverable. Weight-only labels contribute no kinematic deltas — their varied factors, when
  among the stored fields, augment like any other varied field (**reachable via
  `graphed.weight(ctx)`**, §9.1 — added in r12: under the owner-locked context idiom a factor
  handed to `graphed.vary(..., is_weight=True)` is otherwise absorbed into an immutable registry
  the user cannot name, so "when among the stored fields" was unsatisfiable). Appended names follow one bound
  convention (`__vary_{label}__{field}`-shaped; exact spelling pinned at m51 freeze). Labels are
  valid identifiers by construction (**§1.1 canonicalization, r9 e-form** — a dotted spelling never
  reaches a label), so labels appear in on-disk names VERBATIM: the canonical on-disk shape is
  `__vary_murf_5em1__Jet_pt`. The probe-measured hazards that forbade
  dotted names (`ak.from_parquet(columns=["murf_0.5"])` silently empty, pyarrow 25.0.0 /
  awkward 2.12.0; a dotted uproot 5.7.5 RNTuple field is reachable via `__getitem__`
  (`behaviors/RNTuple.py:1560-1562`, exact lookup first) but `RField.array()` fails because
  `to_akform` splits the path on `.` (`behaviors/RNTuple.py:562,567`);
  the TTree writer's own `.` nesting separator, `writing/_cascadetree.py:1606`; ROOT
  TTreeFormula `.`/`-` operator meaning) are foreclosed at the §1.1 gate. Carried-over probe
  evidence: the r8 p-form fixture `__vary_murf_0p5__Jet_pt` — identifier-shaped exactly like the
  r9 canonical form — round-tripped byte-exact and readable in every measured path.
  (c) **Bit-exact reconstruction is REQUIRED.** Reading the file back and applying the deltas
  MUST reproduce every universe's post-selection values and row set bit-for-bit vs the in-memory
  varied run. The default representation is therefore **exact by construction**: same-dtype XOR
  bit-delta vs nominal for value columns (zero wherever a label equals nominal — maximally
  compressible), `packbits` for masks stored as nominal + XOR-vs-nominal diffs. Measured basis
  (R0.11; worklog 2026-07-30, float32/1M-value/zlib-6 probe): the suggested "1+delta" float
  ratio compresses best (2.88 MB vs 3.55 raw) but is **NOT bit-exact** (measured false);
  subtraction delta is bit-exact only data-dependently; XOR is exact by construction (3.28 MB);
  XOR-diff+packbits masks are ~4.7× smaller than raw booleans (169 KB vs 798 KB, 5 labels).
  Lossy ratio storage is a Phase-2 opt-in (§11); the representation is recorded per column in
  the manifest; sizes are re-measured on real skims in the m51 implementer report.
  (d) **Structure rule, with an explicit refusal.** Deltas require same-shaped buffers: varied
  columns are stored at the
  widest common structure (pre-object-cut values on the event-row superset), with per-label
  validity masks at every selection level that varies — event-level AND object-level (a JES
  shift moves jets across a per-jet pt cut, so per-label *inner* masks are part of the cutflow
  data, not an edge case). **The object-level half is only expressible because §6.4a's `select=`
  is per LEVEL** — the writer stores one packed per-label mask for each level the user supplies
  (`{0: event_mask, 1: jet_mask}`) and never applies them to the stored buffers; nothing else in
  this plan gives the writer knowledge of an inner cut, and inferring it from the record
  expression is the undecidable rule §6.4a rejects. That holds for scale/smear shifts, which preserve multiplicity — but
  §2.1 does NOT guarantee it: §2.1's construction check is awkward form compatibility, a TYPE
  check (`var * float64` matches `var * float64` whatever the per-event counts), so a variation
  that legitimately changes multiplicity (shift-dependent cleaning, overlap removal, a matched
  collection) passes §2.1 and then has no representable XOR delta. **Binding refusal**: a stored
  varied field whose per-label offsets differ from nominal's is REFUSED with an error naming the
  label and the field. The supported v1 model is same-multiplicity variation plus per-label
  validity masks; multiplicity-changing stored variations are Phase 2 (§11). Frozen as an m51
  negative anchor.
  (e) **Manifest — invent no formats.** A manifest (labels → appended columns → representation)
  travels in existing metadata channels: parquet key-value file metadata (measured unused today —
  greenfield). **The writer swap is CONDITIONAL, not unconditional** — otherwise it contradicts
  §6.4g's byte-identity requirement: measured this session (awkward 2.12.0 / pyarrow 25.0.0),
  `ak.to_parquet(a, p)` and `pq.write_table(ak.to_arrow_table(a), p)` produce **different bytes**
  (sha256[:16] `ad1725aca34f2bbb` vs `43b093e8bc616bd7`) and different key-value metadata sets
  (`{awkward_array_metadata, ak:parameters}` vs `{ak:parameters}` — the plain arrow path LOSES
  awkward's own metadata, which would break `ak.from_parquet` round-tripping). `ak.to_parquet` has
  no metadata parameter (signature verified), so the swap genuinely is required for the manifest.
  Binding: an **unvaried write keeps `ak.to_parquet` untouched** (preserving the §6.4g golden); a
  **varied write** takes the `ak.to_arrow_table` + `pq.write_table` path and MUST reproduce
  awkward's own KV entries alongside the graphed manifest, with `ak.from_parquet` round-tripping
  the augmented file as a frozen m51 anchor. The
  ROOT-side equivalent pinned at m51 freeze. The manifest maps each label to its stored
  column/branch names and per-column representation; readers resolve labels **through the
  manifest**, never by parsing stored names (names embed labels for human inspection, not as
  the machine channel). A frontend reader (`graphed.read_varied(path)`-shaped; spelling at freeze)
  reconstructs `{label: array}` per universe from the manifest — the round-trip is the m51
  frozen anchor.
  (f) **Seam binding (write-seam evidence, verified).** Parquet: appended columns are extra
  marked outputs of the SAME `compile_ir` (variadic by design, `execute.py:54-70`), so the M4
  optimizer shares the pass with the primary expression — appended between the evaluate and
  write steps of `_WritePart.__call__` (`awkward/io.py:111-127`). **That call site unpacks a
  SINGLE output today** (`(out,) = evaluate_ir(...)`, `io.py:122`), so widening it to the
  augmented output list is part of this target, not incidental (r12); the read list widens at
  `_evaluation_columns` (`awkward/io.py:157-185`) or projection starves the task. ROOT:
  `graphed_write` today copies branches verbatim with NO IR evaluation
  (`_graphed_write.py:59-64`; zero `compile_ir`/`evaluate_ir` hits) — adding evaluation is the
  **larger half** of m51 and is scoped there explicitly. numpy backend: EXEMPT — it hard-caps
  output at one 1-D column (`numpy/io.py:163-171`); varied writes refuse with a clear error
  naming the awkward backend.
  (g) **Single pass; no cost when unused.** The augmented write stays one plan / one read pass
  (the §5.2b witness applies to the write run); an unvaried write is byte-identical to today's
  output, and carries no manifest. **The byte-identity is frozen as a SAME-PROCESS comparison,
  never as a committed `.parquet` fixture** (r11): §6.3's golden pattern works for GIR because
  that format is graphed's own and deterministic by construction
  (`core/m40/test_join_serialize.py:83-99` compares a literal `b"GIR1\x03…"`), but a parquet
  footer embeds its **writer version** — an `ak.to_parquet` file carries the ASCII string
  `parquet-cpp-arrow version <arrow version>`, readable as
  `ParquetFile(path).metadata.created_by` (re-measured r12: `parquet-cpp-arrow version 25.0.1`
  under awkward 2.12.0 / pyarrow 25.0.1; the r11 text quoted `24.0.0`, an artifact of a different
  environment than the pyarrow version it named) — so a committed parquet blob turns red on
  any pyarrow bump and can differ across §A.5 matrix legs while the behaviour is correct, which
  R0.10a forbids. The available invariant is an in-run one, and it is what m51 freezes: write the
  same array through the feature-present path and through `ak.to_parquet` directly in ONE process
  (measured byte-identical for repeat writes: `True`) and assert byte equality plus the absence of
  the manifest KV key. Params-absence (the §6.3 pattern) still applies to the graph side.

## §7 Execution, results, checkpoint

- **§7.1** One Session, one IR, one plan for nominal + all variations; executors are untouched
  (`R` opaque through `Plan`/tree-reduce/engines — cba §exec-checkpoint §1,§4). No per-variation
  execution loop may be introduced anywhere.
- **§7.2** The frontend owns `(output, label) → **node id**` — NOT `→ position` — and derives
  `node id → position` from the compiled output list, so **many labels MAY resolve to one position
  and the unpacker replicates that value**. This is forced by content dedup, measured:
  `GraphStore::mark_output` de-duplicates (`src/store.rs:152-153`) and `evaluate_ir` returns
  `[vals[o] for o in store.outputs()]` (`execute.py:126`), so compiling two structurally identical
  outputs returns ONE value — re-measured this session against `graphed-latest`: `compile_ir(s, b,
  c)` with `b`/`c` structurally identical returns 1 value, `compile_ir(s, b, d)` with distinct
  expressions returns 2. A positional `(output, label) → position` map would therefore walk off the
  end of `_GroupReduce`'s `fills` list or mis-assign labels (`boost.py:102-117`) on exactly the case
  §1.2 mandates and §5.2a/m51 put in scope (a label structurally equal to nominal). The frontend
  unpacks into the §6.1 named mapping. `ExecResult`/`Plan`/monitor **schemas** do not change in
  m48–m50 (per-variation monitor events: Phase 2, the defaulted-field trick documented —
  `store.py:31-41` precedent); the absence is a frozen m48 anchor (§10), worded over **schema KEY
  SETS**, not over plan bytes: §8.2(i)'s added `_PartitionReduce` field leaves the public schemas
  untouched but *does* change the shipped worker closure, which is embedded as an opaque
  cloudpickle `OpSpec` whose bytes feed `identity()` and therefore `task_id`
  (`python/graphed/core/plan.py:72-90,164-176`). See §7.3 for the churn that causes.
- **§7.3 (Checkpoint semantics, documented honestly and anchored.)** Within one plan, resume works
  per-partition exactly as today (the N-variation composite partial is the journal unit) — m49
  freezes an interrupt/resume test over a varied graph whose result is byte-identical to an
  uninterrupted run. Across plan revisions, adding/removing a variation changes the IR and
  therefore **every** `task_id` (`plan.py:164-176,286-301`) — no cross-revision reuse. This
  limitation MUST be documented in the user docs and design.rst — naming the canonical
  invalidating edit from the exemplar workflow: toggling the expensive shift class on or off
  between runs (the `skip_obj_systematics` pattern, lit §ewkcoffea-confirmed) rebuilds the IR and
  invalidates the whole cache. **One-time, ALL-programs churn on landing m49**: §8.2(i) adds a
  field to `_PartitionReduce`, the worker closure shipped as the plan's opaque `process` spec, and
  `task_id` folds `self.process.identity()` (`plan.py:72-90,164-176`), so every existing
  checkpoint journal is invalidated once — including for *unvaried* programs. Wider than the
  per-variation invalidation above; state it in the same doc paragraph. Stage-granular content
  addressing is the named Phase-2 fix (§11).
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
  (review r0). **r9's mechanism sentence is WITHDRAWN in r10: the channel it named does not exist.**
  Verified against `graphed-latest`: `_PartitionReduce.__call__` — the callable that actually runs
  on a worker for an `aggregate_plan` — reads the partition and calls `evaluate_ir` bare, with no
  provenance, no node map, no try/except and no `StageError` (`aggregate.py:44-65`); `grep
  "StageError("` over `python/graphed/` returns exactly two hits, the class itself
  (`debug/errors.py:29`) and the M6 debug runner (`debug/runner.py:37`), which is **driver-side** —
  it needs a live `Session` (`lower(session, array)`, `session.source_value(nid)`,
  `runner.py:57-69`) and its own docstring says "a *debug* runner, not the M7 executor"
  (`runner.py:6-7`). Per-node provenance is likewise driver-side only (`Session._provenance`,
  `session.py:30`, exposed via `sourcemap()`, `:113-125`). The executors never build one either —
  they translate worker death or re-raise an already-raised `StageError`
  (`submit/engine.py:381-396`). Every existing cross-process `StageError` with real provenance comes
  from a test closure that REBUILDS the graph in the worker (`tests/frozen/debug/m6/analyses.py:52-56`;
  `graphed-executors tests/frozen/m7/analyses.py:118-127`).
  **The r10 mechanism is therefore NEW work, in two parts, both m49 targets.**
  (i) *Transport*: a `variation_labels: tuple[tuple[int, frozenset[str]], ...]` field is ADDED to
  the worker process closure (`_PartitionReduce`, `aggregate.py:44-55`) — an additive dataclass
  field, so `Plan`/`ExecResult` schemas stay untouched (§7.2). It is keyed on **POST-REDUCTION node
  ids** taken from the same `compile_ir` call that produced the shipped `ir` (`aggregate.py:95-97`);
  record-time ids are wrong, because DCE compacts and remaps (`src/optimizer/mod.rs:88-116`, the
  `remap` vector) and the pipeline rebuilds into a fresh interned store (`mod.rs:1-11`).
  **THAT KEY SPACE REQUIRES A CORE ACCESSOR THAT DOES NOT EXIST, and building it is an explicit
  m49 Implementation Target** (r12 — r10 withdrew r9's transport sentence because "the channel it
  named does not exist"; r11's replacement re-introduced the same defect one layer down, keying on
  ids no channel produces). Measured: `CompiledGraph` carries `ir: bytes` and
  `source_names: tuple[str, ...]` and nothing else (`python/graphed/execute.py:36-45`, built at
  `:54-80`) — no remap, no id table; and the PyO3 surface exposes no mapping either (enumerated
  every `#[pymethods]` fn in `src/lib.rs:106-543`: `add_source`/`add_op`/`add_reduction`/
  `add_external`/`add_exchange`/`add_join`/`node_count`/`to_dot`/`serialize`/`deserialize`/
  `nodes`/`outputs`/`reduce`/`reduce_incremental`/`reduction_report`; the `remap` vector lives
  entirely inside `dead_code_elimination` and is never returned, `src/optimizer/mod.rs:88-116`).
  Fusion also means most varied nodes have **no** post-reduction node id of their own: a universe's
  chain collapses into ONE `Stage` whose members are evaluated inline (`execute.py:110-117`), which
  this plan's own §3.3 measurement shows (N=128 universes × 50 chain ops → 129 stages / 258 nodes).
  Binding: m49 adds a **read-only** `graphed-core` accessor returning, for the reduction that
  produced a given compiled artifact, `record_node_id -> (reduced_node_id, member_index | None)`.
  **§3.1 still holds**: it is a read-only accessor over data the reducer already computes — no new
  `NodeKey`, no serialize tag, no optimizer arm, no semantics. The map keys on
  `(reduced_node_id, member_index)` accordingly. If the accessor is descoped, the honest fallback
  is coarser and MUST be stated as such rather than silently assumed: key on **output position**
  (the frontend owns that id space already per §7.2 — dedup by record-time node id, matching
  `store.outputs()`' first-occurrence order) and attribute a failure to the label(s) of the
  raising output, losing per-node granularity.
  (ii) *Attributed worker-side errors*, which do not exist today: the `evaluate_ir` call site in
  `_PartitionReduce.__call__` is wrapped so a worker failure becomes a `StageError`, and the
  per-node provenance the map keys alongside is shipped in the same closure — **re-keyed through
  the same accessor**, since `Session._provenance` is keyed by RECORD-time ids (`session.py:30`,
  written at `:141-166`) and inherits the identical remap problem.
  **The map is set-valued, not a function** — §3.4 proves it in this document: "a node shared by
  `jes_up` and `jes_down` but not nominal appears in BOTH impact sets." Rendering is bound: a
  singleton renders as that label; a multi-label set renders as its labels sorted and joined by
  `,`; the empty set renders `""` (nominal/unvaried, §8.1).
  Frozen m49 anchors: a failure
  raised inside the `jes_up` universe on a worker across a process boundary re-raises driver-side
  carrying `variation == "jes_up"` AND the user's analysis line (M6 contract extended, not
  altered), and the dead-letter descriptor shows the label (§7.4); **plus a shared-node failure
  asserting the multi-label rendering** — without it the single-label anchor passes under a
  pick-one-arbitrarily implementation and the defect survives the freeze.
- **§8.3** Per-node provenance needs no new machinery (§2.3): varied nodes record at user op lines.
  `to_dot`/debug labels remain readable; the impact-set API (§3.4) is the "which nodes belong to
  which label" view.

## §9 Preservation and introspection

- **§9.1** `graphed.labels`/`graphed.universe`/`graphed.nominal` (§2.2),
  **`graphed.weight(ctx)`** (the context's ambient weight as a `Varied`, `None` when nothing is
  registered; m48 — added in r12 as the weight-side twin of `graphed.selection`: §2.6a reserves no
  attribute names and the r11 surface exposed no accessor at all, so a factor handed to
  `graphed.vary(..., is_weight=True)` was absorbed into an immutable registry the user could never
  read back. That is fine for the ambient-fill mainline but not for §6.4b, whose "their varied
  factors, when among the stored fields" presumes the user can name them, nor for anything wanting
  the event weight explicitly alongside `unweighted=True`. Read-only: it returns the registry's
  current `Varied`, it does not mutate),
  `graphed.variations(ctx)` (per-name listing of a context's registered variations, their tags
  and kinds — and, for numeric tags (canonical e-form `m?\d+(em\d+)?`, `5em1` → 0.5; plus the
  datacard p-form `m?\d+(p\d+)?`, `2p5` → 2.5), the parsed float value: the ordering handle for
  σ-scan/envelope plots, since §6.2's sorted axis is lexicographic), **`graphed.selection(ctx)`**
  (the `Varied` mask that derived a context from its parent, `None` for a root context — the
  §6.4a bridge that makes the m51 skim sink reachable from the §2.6 context idiom; m51),
  the §3.4 impact API, and a
  plan-level listing of `{output: [labels]}` constitute the introspection surface (RDF
  `GetVariations` analogue); the listing is frozen-anchored inside m50's `inspect()` test (§9.2).
- **§9.2** Preservation: a bundle built from a variation-expanded graph reproduces **all** labels
  from ONE bundle, in the m9 comparison form (per label,
  `np.array_equal(reproduce(bundle)[label], build_time[label])` — the genuinely bit-exact
  in-process form, `preserve/m9/test_reproduce.py:19-23`), and `inspect()` lists the labels without
  executing. **The API surface this presupposes does not exist today and is bound here**: today
  `build_bundle(root, *, session, value, weight=None, …, histogram=None, …)` is strictly SINGULAR
  (and raises unless `weight=` and `histogram=` are given together, `preserve/bundle.py:103-123`),
  and `reproduce(bundle)` returns a single array (`bundle.py:206-210`). m50 extends both: a varied
  bundle accepts a `Varied` `value=`/`weight=` (equivalently a per-label mapping) and `reproduce`
  returns `{label: array}`; **an unvaried bundle still takes bare Arrays and `reproduce` still
  returns a bare array** (backward compatible). Exact spellings pinned at m50 freeze. This replaces
  the m9 fixture's one-bundle-per-config pattern *additively*: existing m9 frozen tests are
  untouched.

## §10 Milestones (strictly ordered; m48 → m49 → m50 → m51)

Numbering: the executors repo froze m47 last. Frozen layouts by repo: consolidated `graphed` —
directories pinned now, because that repo's frozen tree is partitioned by package, pytest runs it
per subtree at per-milestone granularity, and duplicate basenames have bitten it before
(`pyproject.toml:103-130`): **`tests/frozen/frontend/m48`, `tests/frozen/frontend/m49`,
`tests/frozen/preserve/m50`, `tests/frozen/awkward/m51`**, plus the §3.3 benchmark in
`tests/frozen/core/m49`. Any helper imported ACROSS those directories must be added to
`pyproject.toml`'s `pythonpath` list (the corpus-reference anchors already have `tests/_corpus`
there); a shared `vary` fixture module is expected and must be listed.
`graphed-executors` = flat `tests/frozen/m49`;
**`graphed-histogram` = flat `tests/frozen/m48` and `tests/frozen/m50`** (its existing shape —
`m23/`, `m29/`; m50's primary target §6.2 lives there, so its directory is pinned too, while
m50's `graphed` half is `tests/frozen/preserve/m50`, which hosts m50's preservation, docs **and
frontend-introspection** anchors — the §9.1 `graphed.variations(ctx)` anchor and the §6.2(i-bis)
narrowing-helper behaviour of `graphed.labels`/`graphed.universe` over a histogram object both live
in `graphed`, so r11's "preservation/docs only" description contradicted m50's own anchor list
(r12; mechanically the directory is fine — `scripts/run-tests.sh:16-24,29` runs `preserve` per
package and frozen tests already import across package boundaries, e.g.
`tests/frozen/frontend/m40/test_noninner_null_key_option.py` importing `graphed.awkward`).
**`uproot5-graphed-mvp` has NO frozen tree today** — verified at `393ecef`: its graphed tests are
flat, ordinarily-named files directly under `tests/` (`test_graphed_write.py`,
`test_graphed_nanoaod.py`, … **12** files, plus the two shared helper modules
`graphed_uproot_analysis.py` / `graphed_uproot_report.py`, which are not `test_graphed_*.py`) and
the string `tests/frozen` appears nowhere in the repo.
m51 therefore **CREATES `tests/frozen/m51/` there**, and the integrity rules bind it from freeze;
the existing `tests/test_graphed_*.py` stay unfrozen.
Each milestone runs the full §12 process. Frozen anchors listed here are the acceptance skeleton
the test-author starts from; the frozen m05/m4/m9/m23/m29 artifacts are **binding and unchanged**.

- **m48 — `vary` frontend + weight path** (repos: `graphed` + `graphed-histogram`).
  Targets: §1, §2 (incl. the §2.6 event context), §3.2/§3.4 (API only), §4, §6.1 (incl. §6.1d
  ambient fills), **§7.2** (r12 — m48 freezes the §7.2 schema-absence anchor, and §6.1a/§6.1c
  cannot be implemented without §7.2's `(output, label) -> node id` map and the indices-based
  `_GroupReduce.layout` it feeds; §7.1/§7.3/§7.4 stay m49), §6.3.
  **The anchor list is PARTITIONED per repo, and the fill-dependent half needs a dependency edit**
  (r11 — the same analysis §10/m49(ii) already did for its half; leaving m48 a single flat list
  for two repos left "which anchor is frozen where" undecided while §10 pins directories):
  **`graphed`, `tests/frozen/frontend/m48`** takes the pure-frontend anchors (§1.1 grammar, §2.x
  semantics, §2.6 context lineage, §1.2 label-out-of-identity **except its dedup half**, §3.2
  determinism, §7.2 schema absence). **`graphed-histogram`, flat `tests/frozen/m48`** takes every
  anchor that needs a fill:
  the corpus weight matrix + its §5.2b read witness, §6.1a result shapes, §6.1c `.plan()` refusal,
  §6.1d ambient fills, §4.1 correctionlib, §6.3 goldens.
  **Three anchors straddle the split and are assigned explicitly** (r12 — r11 pinned the
  directories but left these three undivided, the very "which anchor is frozen where" gap it says
  it closed): **(1)** §1.2's *dedup* half asserts "both keys present in the result with ONE
  evaluated fill", and the per-label result mapping is `_GroupReduce`'s `{label: hist}`
  (`graphed-histogram src/graphed_histogram/boost.py:100-122`), which does not exist in `graphed`
  — its first half (arena Δ = 0, same node id, `compile_ir` returning one value) stays in `graphed`
  and the result-mapping half goes to `graphed-histogram`; **(2)** §2.1 stacking's
  `old_ambient[L] × factor[L]` assertion is observable only through a fill unless
  `graphed.weight(ctx)` (§9.1, m48) is used — with that accessor it is frontend-observable and
  stays in `graphed`, and the anchor MUST use it rather than a fill; **(3)** the §2.6/§6.1d
  mega-bullet below is SPLIT: its pure-frontend clauses (tag grammar, no-reserved-names, lockstep
  validation, data guard, lineage, re-indexing, `graphed.labels` on a Varied-derived context,
  op-level divergence) stay in `graphed`; its fill-shaped clauses (ambient fill on a per-object
  quantity, the manual-broadcast reference, the execution-time refusal, divergent-lineage AT THE
  FILL, `unweighted=True`) go to `graphed-histogram`'s flat `tests/frozen/m48`. **Neither repo can host the matrix as it
  stands**, measured: `graphed` vendors the 23 reference JSONs (`tests/_corpus/references`, on
  `pythonpath`) but lists **no** `graphed-histogram` in any extra (its `dev` extra carries
  `boost-histogram>=1.4`/`hist>=2.7` only) while CI installs `.[dev]`
  (`.github/workflows/ci.yml:34,57,143`), and the house pattern there is
  `pytest.importorskip("graphed_histogram")` (`tests/frozen/preserve/m25/…:31`, `m27/…:185,207`,
  `m30/…:155`) — an anchor written that way would **SKIP in CI**, silently discharging the
  milestone's headline gate and contributing no frozen-suite diff coverage (the DoD requires ≥90%
  diff coverage FROM the frozen suite). `graphed-histogram` has the fill sink but **no corpus
  dependency and no reference JSONs** (`grep -rn corpus tests/ .github/workflows/` → 0 hits; the
  corpus wheel packages only `src/graphed_corpus`, `graphed-corpus pyproject.toml:28-30`, while
  the 23 JSONs live in the repo dir `corpus/references/`). **Binding: m48 adds `graphed-corpus` to
  `graphed-histogram`'s `dev` extra AND vendors the 23 reference JSONs there the way `graphed`
  already does (`tests/_corpus/references` on `pythonpath`), and the matrix anchor MUST NOT be
  guarded by `importorskip`** — a skipped headline gate is a silently discharged milestone.
  Frozen anchors:
  - Corpus **weight**-variation references through the frontend — ttbar 4j1b/4j2b ×
    {nominal, btag_up, btag_down} (6) + ttgamma {nominal, pho_up, pho_down} (3) = **9 of the 15
    refs**, `fingerprint(h) == ref["fingerprint"]` and `bin_values(h) == ref["values"]` (the
    `m05/test_fixtures_reproduce.py` comparison form). Note: the ttgamma flat SF weight is a
    constant — spell it `gak.full_like(<a per-event Array>, sf)`
    (`python/graphed/awkward/functions.py:612-616`, parity-pinned at
    `tests/frozen/awkward/m24/test_interface_parity.py:74-76`) or as arithmetic on such an Array;
    what does not exist is a constant Array with no shape donor (§4.1, §11). The anchor says so to
    spare the test-author the mid-freeze discovery. **Same service for the corpus's `stable()`
    rounding, the detail that decides what is bit-comparable**: the references round the
    observable to 6 decimals BEFORE the fill and the view after
    (`tests/_corpus/graphed_corpus/analyses/systematics.py:79,102,50`;
    `histograms.py:20,34-37,39-42` — `bin_values`/`fingerprint` round again). So (a) the recorded
    program must re-express the pre-fill rounding if bin-edge decisions are to match the corpus's
    cross-platform-stability intent, and **gak has no `round(x, decimals)`** (`rint` exists only
    as a ufunc, `python/graphed/array.py:54`), so `rint(x * 1e6) / 1e6` is the expressible form;
    (b) conversely `bin_values`' driver-side rounding is what absorbs the float-summation-order
    differences a per-partition fill introduces, so the comparison rides
    `bin_values`/`fingerprint` — **raw-view bit-identity vs the references MUST NOT be asserted**.
  - §4.3 structural selection-invariance, in the r10 binding form: **the selection cone's node ids
    are identical across all weight labels** (NOT the withdrawn impact-set-subset wording, which is
    false for a correct implementation — §4.3); **with the extraction mechanism named** (§4.3 r12):
    per label, `reachable(fill_node[label])` via `session.walk`
    (`python/graphed/session.py:245-252`), `fill_node[label]` from the §7.2 map, asserting the
    intersection with `reachable(selection_mask)` is identical across labels and equal to
    `reachable(selection_mask)`. m05 equal-counts as sanity.
  - **§1.2 label-out-of-identity** (no anchor existed before r10, and it guards the whole interning
    story): for a varied program, NO node in the store carries any label string in its params or
    token, AND renaming every label leaves `compile_ir(...).ir` byte-identical. Plus the **dedup
    witness §5.2a defers to this bullet**: two labels whose members are structurally identical give
    arena Δ = 0, the same node id, and — per §7.2 — both keys present in the result with ONE
    evaluated fill (measured: `mark_output` de-dups, `src/store.rs:152-153`, so `compile_ir` over
    two identical outputs returns one value).
  - **§6.1c `.plan()` refusal** (no anchor existed before r10): `.plan()` on a `Histogram`
    carrying **more than one staged fill node with varied labels** (i.e. sibling mode)
    raises naming the group API — `_SumFills` sums ALL staged fills into one histogram
    (`boost.py:88-98`) and would otherwise silently merge universes into a plausible-looking,
    physically wrong result. Positive control: `.plan()` on an unvaried `Histogram` still works.
    **Worded over the fill-node count, not over "a varied Histogram"** (r12): m50's axis mode with
    weight labels only collapses to ONE fill node (§6.2, arity `1 + |S|`), where the merge hazard
    does not exist — a blanket refusal frozen at m48 would over-constrain m50.
  - **§2.1 stacking** (an r1 BLOCKER fix with no anchor until r10; m49's 15-reference matrix
    exercises it only implicitly, one milestone later): `vary` on a target that already carries
    variations inherits those labels, adds the new ones, label order = inherited-then-new,
    the new label's member is the provided value's central universe, and each label differs from
    nominal in exactly ONE knob (the corpus b-tag-on-JES case, `systematics.py:74-76`).
    **Extended in r11 to a WEIGHT `vary` on a context already carrying SHIFT labels** — the case
    the corpus matrix actually turns on and the case m48's weight-only matrix cannot reach (it has
    no shift labels, so a wrong reading survives m48 and only detonates against m49's 15-reference
    matrix, after m48 is frozen): assert the **inherited** shift label's ambient member is
    `old_ambient[L] × factor[L]` — the factor evaluated in THAT label's universe, per §2.1's
    per-overload stacking rule — not the old ambient unchanged. **Read through
    `graphed.weight(ctx)`** (§9.1, r12) so the assertion is frontend-observable and this anchor
    stays in `graphed`'s half of the m48 split.
  - **§2.2 `Varied.apply`**: per-universe application of an `Array -> Array` function, plus the
    error contract — `fn` returning a `Varied` raises with guidance to combine via ordinary ops.
  - **§6.1a result shapes** — **in SIBLING mode** (§6.2 axis mode is m50 and has its own shape,
    §6.2(i-bis); word the anchor so it does not freeze a general rule m50 must contradict) — on a
    MIXED varied/unvaried output set: a varied output is
    `{label: hist}`, an output no variation reaches is a BARE `hist` (not `{"nominal": hist}`),
    absent labels are absent (never duplicated from nominal), and `graphed.universe`/`graphed.labels`
    narrow both shapes uniformly.
  - **§2.3b plain-Array entry points learn `Varied`** (binding since r1, unanchored until r11; the
    m48 dunder-parity anchor is the MIRROR property and does not exercise it, and it otherwise
    reaches the suite only implicitly one milestone later inside m49's 15-reference matrix, where
    the corpus indexes unvaried photons by a JES-varied selection,
    `graphed-corpus src/graphed_corpus/analyses/systematics.py:91-92`): `plain_array[varied_mask]`
    and `plain_array.filter(varied_mask)` each return a `Varied` carrying the mask's labels
    (label-aligned per §2.4), with a negative control that neither raises the wrong-implementation
    shapes — `TypeError` from `__getitem__`'s final raise (`array.py:369-371`) or `AttributeError`
    on `.node_id` from `filter`'s unchecked `record_op` (`array.py:374-375`), both invisible to a
    histogram-value comparison — plus a still-`TypeError`s control for a genuinely unsupported
    index type, so the branch cannot be implemented as a blanket `except`.
  - **§2.5 unreached-label diagnostic** (binding, unanchored until r11; §2.5's raising cases are
    covered by "§2 validation errors" below but this one is a DIAGNOSTIC, not an error — the
    mkShapesRDF silent-cost guard): a registered label reaching no marked output is reported by
    `compile_ir` diagnostics; absent when every label reaches an output.
  - **§7.2 schema absence**: the `ExecResult`/`Plan`/monitor payload schema **KEY SETS** are
    identical for a varied and an unvaried program (the §6.3 params-key-absence pattern applied to
    the plan/result schemas). Worded over key sets, NOT over plan bytes or the `process` spec —
    m49's §8.2(i) closure field changes those by design (§7.2, §7.3).
  - Single-pass read witness **on the reference-matrix run** (§5.2b applied to the weight matrix).
  - §3.2 determinism: same varied program compiled in two fresh processes under differing
    `PYTHONHASHSEED` → byte-identical `compile_ir` output; `graphed.labels` order pinned
    (nominal-first + insertion order).
  - §6.3 goldens (committed GIR blob + params-key absence).
  - §2.3 **public-surface** parity (dunders AND methods, §2.3a r12 — enumerated dynamically from
    `type(graphed.nominal(v))` so the numpy idiom's ~25 methods and tuple `__getitem__` are
    covered, `python/graphed/numpy/array.py:92-190,132-136`; `Array`'s own `filter`/`map`/`reduce`/
    `repartition` at `array.py:374-391`) and gak-classification exhaustiveness, both **dynamically
    enumerated**
    (§2.3a/c) — the classification test freezes only that every DISCOVERED public gak function has a
    classification; the *behaviour* of the `refusing` class is an m49 anchor, since §5.4 (the refusal
    message and its positive control) is an m49 target. **§2.3e context-handle propagation is a
    SEPARATE, SCOPED gate** (r12 — a behavioural "every public gak function preserves the handle"
    gate is not buildable over the measured 65-function surface: `apply_correction`/
    `onnx_inference` take a payload first, `to_list`/`head`/`sample` are eager, `fields`/`type_of`/
    `backend_of` return non-Arrays, `zip`/`concatenate`/`where`/`unflatten`/`linear_fit` need typed
    operands — and a frozen test cannot grow arguments for a function added later): it enumerates
    only the *broadcast*, *container-traversing* and *tuple-returning* classes, takes its call
    arguments from fixtures living in `src` beside the classification, and asserts the exempt set
    is exactly {*eager-metadata*, *refusing*}.
    **Each of these three tests MUST carry §2.3c's non-vacuity floor in
    the same test** — a dynamic gate whose discovery step returns an empty or wrong set passes
    tautologically, and the obvious discovery mechanism does not exist here (gak has no `__all__`,
    §2.3c): the discovered set is non-empty, at least the freeze-time count, and names at least one
    member of each classification class; the parity gate additionally names `__array_ufunc__`,
    `__getitem__`, a bitwise dunder **and at least one public METHOD**.
  - **Per-class gak behaviour** (r12 — the exhaustiveness gate asserts a classification EXISTS, not
    that it is RIGHT, and three of §2.3c's five classes had no behavioural anchor anywhere in
    m48–m51; the corpus matrices cannot reach them, since the corpus fixture uses `ak.with_field`,
    `graphed-corpus src/graphed_corpus/analyses/systematics.py:39-45`, never `ak.zip`. A
    mis-classified `gak.zip` would hand the `Varied` straight into `record_op`): one named
    representative per unanchored class —
    `gak.zip({"pt": varied_pt, "eta": plain})` returns a `Varied` carrying the labels
    (*container-traversing*, `python/graphed/awkward/functions.py:118`);
    `gak.unzip(varied_record)` returns a TUPLE of `Varied` (*tuple-returning*, `:687`);
    `gak.fields(varied)` / `gak.type_of(varied)` answer on the nominal member (*eager-metadata*,
    `:717,722`). Plus §2 validation errors (§1.1,
    §2.5); §2.4 label-aligned combination on a Varied-meets-itself program, **including the bound
    union ORDER** (first operand's order, then labels new to the second in its own order, nominal
    first) **and §6.1d's three-way fill fold order** — a fill with varied values in TWO axes plus
    an ambient weight plus an explicit `weight=[…]` factor, asserting the bound operand order
    (axis values in argument order, then ambient, then explicit factors in list order).
  - §4.1 correctionlib single-payload multi-parameterization.
  - §2.6/§6.1d event-context anchors (r6 functional form): ambient fill on a per-object quantity —
    the value passed **UNFLATTENED** (§6.1d), Jet-pT fill yields value labels ∪ ambient labels,
    weight broadcast frozen against a manual-broadcast reference — **for the ambient weight AND an
    explicit `weight=[…]` per-event factor in the same per-object fill** (§6.1d: the evaluator
    multiplies factors after flattening each independently, `boost.py:60-71`, so an unbroadcast
    explicit factor length-mismatches on the mainline idiom) — plus the **execution-time** refusal
    when a per-object fill hands in an already-flattened value alongside a per-event ambient weight
    (§6.1d r12: an execution-time `graphed` error naming the OFFENDING FACTOR and pointing at
    "pass the value unflattened"; there is
    no record-time discriminator, so do NOT freeze a record-time raise — **and do NOT freeze
    `FillEvaluator` as the raiser**: under the bound broadcast seam the recorded broadcast node is
    upstream of the fill and fails first (measured, awkward 2.12.0: `ak.broadcast_arrays` over
    lengths 7 and 3 raises `ValueError: cannot broadcast RegularArray of size 3 with RegularArray
    of size 7`), so the anchor freezes the MESSAGE CONTRACT at execution time, not a class name;
    same anchor covers an offending EXPLICIT factor, whose message names that factor, not the
    ambient weight);
    **divergent-lineage detection AT THE FILL** (§2.3e/§6.1d: `h.fill(a_from_ctx1, b_from_ctx2)` —
    handles no op ever combined — is a hard error naming both contexts) **AND AT THE OP**
    (§2.3e r12 — the op-level rule is §2.3e's *early detection* half and had no anchor, so an
    implementation checking only at the fill satisfied every m48 anchor while pointing every
    diagnostic at the fill line instead of the line that mixed the contexts): a binary op over
    `Array`s from two divergent contexts raises AT THAT OP naming both, with a positive control
    that an ancestor-chain pair unifies silently to the most-derived context;
    lineage semantics (`graphed.vary` returns a NEW context and the
    input context is unchanged — a fill from the pre-vary context carries no new label, a fill
    from the returned context does; ancestor-chain inputs unify to the most-derived context);
    selection-scoped weight via `vary` on a derived context (parent unaffected) **and the derived
    context's ambient weight re-indexed to the derived row count** (§2.6c — **elementwise equality
    per label against a manually re-indexed reference, not length equality** (r12): length equality
    catches only the named failure of inheriting the parent's un-re-indexed members, while the
    adjacent and likelier bug — re-indexing every label's member by NOMINAL's mask, or by whichever
    label was iterated first — yields right-length, silently mis-weighted arrays whenever per-label
    counts coincide; the manually re-indexed reference is already in the test, so comparing values
    is free. The **varied-mask case (per-label row sets) is inside this anchor**, where a
    length-only check is weakest); `graphed.labels` on a context derived by a **Varied** mask
    (per-label row sets, §2.6c); `unweighted=True`; data-context guard for
    **both** forms (`is_weight=True` AND a shift-form `vary`, §2.6d);
    lockstep `graphed.vary(events, name, Jet=…, MET=…)` shared-tag-set validation; §1.1 tag
    grammar (kwarg tags + `variations=` numeric-tag escape + every listed rejection); no
    reserved names on the context (a tree branch named `weights` or `vary` stays reachable —
    the collision that motivated r6); §2.2 `graphed.universe`/`labels`/`nominal` on both
    `Varied` and contexts, string getitem = field access. The §1.1 grammar anchor MUST cover the
    r9 e-canonicalization semantics: float spellings accepted via `variations=` AND via
    `**`-unpacking (channel-independent) and normalized by exact decimal arithmetic
    (`"2"`/`"2.0"`/`"2e0"`/`"20e-1"` → the ONE label `murf_2`; `"1e-8"` → `eps_1em8`; integer PDF
    indices untouched), **non-minimal canonical-grammar tags re-rendered** (`"50em2"` → `5em1`,
    §1.1 r11), the two readings of "`"0.5"` and hand-typed `"5em1"` unify" **split explicitly**
    (§1.1 r11 — a single "they unify" bullet is freezable either way): across TWO `vary` calls the
    spellings name the identical label `murf_5em1`; within ONE call they are a
    duplicate-after-canonicalization REJECTION, like `{"0.5", "0p5"}`. Plus cross-notation
    numeric-equal
    pairs rejected (`{"0.5", "0p5"}`, `{"2", "2p0"}`), `inf`/`nan`/leading-`+`/underscore/
    whitespace spellings rejected, Python-float (non-string) tags rejected, negative zero
    canonicalizing to `0` (never `m0`) and a >32-character canonical tag rejected (§1.1 r10), the
    **FOUR signature-shadowed names** (`nominal`/`is_weight`/`variations`/`collections` reachable
    only through `variations=` / `collections=` — including `collections`' own self-reference,
    §2.1 r11 — and `variations=` refused in the shift form), and no
    label ever containing `.`/`-` — freezing an earlier revision's rejections would hard-block this
    grammar (review-sweep finding).
- **m49 — shift path + impact + executor end-to-end** (repos: `graphed` + `graphed-executors`).
  Targets: §3.3, §3.4 (frozen anchor), §5, §7, §8. Frozen anchors:
  - The **full 15-reference matrix**, split across two repos explicitly (r10 — the halves have
    different fixture problems and r9 named neither):
    (i) **`graphed-histogram`, flat `tests/frozen/m49`** — the matrix through the frontend,
    fingerprint-exact against the 15 stored references, plus a separate
    run-to-run `array_equal` determinism assertion (the m29 dual-assert precedent; "bit-for-bit"
    is claimed only run-to-run, not vs the rounded references — review r0). **The §5.2b read
    witness binds to THIS run**, and like m48's matrix this anchor **MUST NOT be guarded by
    `importorskip`**.
    **Moved out of `graphed` in r12 — the m48 fixture analysis (below) applies here verbatim and
    r11 left this half unamended**: `graphed` vendors the 15 references but lists no
    `graphed-histogram` in any extra (`pyproject.toml:41-48` — `dev` carries
    `boost-histogram>=1.4`/`hist>=2.7` only) while CI installs `.[dev]`
    (`.github/workflows/ci.yml:34,57,143`), and the house pattern there is
    `pytest.importorskip("graphed_histogram")` (`tests/frozen/preserve/m30/test_producer_cross_seam.py:155`),
    so a fill-based matrix in `graphed` would SKIP in CI — silently discharging m49's headline gate
    AND its single-read mechanism witness, with zero frozen-suite diff coverage. After m48,
    `graphed-histogram` already carries the corpus dep and the vendored references (m48's bound
    dependency edit), so it can host this half without a new fixture problem.
    `tests/frozen/frontend/m49` in `graphed` keeps m49's NON-fill anchors (§5.2a arena delta,
    §5.2c stage shape, §3.4 impact sets, §5.3 projection, §5.4 refusal, §3.3 benchmark).
    (ii) **`graphed-executors`, flat `tests/frozen/m49`** — the same matrix through a process-pool
    executor (the `graphed` repo ships no `Executor` implementation — the executors live in
    `graphed-executors`; `graphed`'s only cross-process frozen test is the M6 error-transport pool,
    `tests/frozen/debug/m6/test_process_boundary.py:16`). Two fixture facts bind the shape:
    the 15 stored references are NOT reachable from the `graphed-corpus` wheel (it packages only
    `src/graphed_corpus`, `pyproject.toml:28-30`, while the reference JSONs live in the repo
    directory `corpus/references/`), and `graphed-histogram` is **not** a dependency of
    `graphed-executors` (`pyproject.toml:20-35`; no `histogram` hit in its pyproject or workflows).
    Because this half must exercise §4.2/§6.1's varied-fill lowering — the whole point of a
    weight-variation matrix — **m49 adds `graphed-histogram` to `graphed-executors`' `dev` extra**
    and compares against corpus references recomputed in-process via `graphed_corpus` (the m7 house
    pattern, `tests/frozen/m7/adl.py:124-158`). The materialize-then-fill-eagerly alternative is
    explicitly NOT chosen: it reproduces the numbers while exercising none of §4.2/§6.1/§6.2.
    This is the executor-level systematics end-to-end no frozen test currently
    discharges (cba §corpus §4).
  - m05 ordering witness (`jes_up > nominal > jes_down`) through graphed — explicitly scoped to
    the monotone JES fixture (§5.1); the suite MUST NOT assert ordering for any other shift.
  - A **JER-SF-style stochastic shift fixture** (additive — corpus m05 tests/references
    untouched): content-seeded re-smearing per §5.5, one shared draw, SF-varied per label.
    Witnesses: run-to-run byte-identical results (content-seeded stochasticity survives the
    determinism gate); selected counts pairwise distinct across {nominal, jer_up, jer_down} with
    NO ordering asserted, plus **bidirectional migration** (no universe's selection mask is a
    subset of another's — the non-monotone discriminator); and the shared random-draw node
    interned ONCE across all universes (mechanism witness, §5.5b).
  - §5.2 witnesses (a: literal-integer arena delta; c: reduced-stage shape).
  - §3.4 impact-set anchor: three labels where two share a derived node — the shared node appears
    in both impact sets; result independent of expansion order.
  - §2.4/§6.1b structural no-cross-product count — **in SIBLING mode** — `1 + |S| + |W|` fill
    nodes (axis mode's `1 + |S|` is m50, §6.2; word the anchor so it does not freeze a general rule
    m50 must contradict — r12 applies to this line the scoping r11 gave the m48 §6.1a anchor and
    §6.1b's own prose).
  - §5.3 projection-union test — **including the per-label projection stats** reporting the shifted
    label's extra column (§5.3 r12; the union-growth assertion alone leaves the stats surface
    unanchored); §5.4 refusal + positive control.
  - §3.3 NEW frozen variation benchmark file (exact `stages == N+1`, `reduced == 2N+2`, linear
    bound).
  - §8.2 cross-process labeled StageError (incl. §7.4 dead-letter label); §7.3 interrupt/resume
    byte-identity. **Plus §8.1's `__hash__` participation explicitly** (r11): `__eq__` compares
    `self.__dict__` so a new field participates for free, but `__hash__` is a hand-written tuple
    that must be edited (`python/graphed/debug/errors.py:75-78` vs `:80-81`) — assert two
    `StageError`s differing ONLY in `variation` are unequal **AND hash differently**, or the
    omission is invisible to the cross-process label anchor.
- **m50 — scale + integration** (repos: `graphed-histogram` + `graphed` preserve/docs).
  Targets: §6.2, §9. Frozen anchors:
  - Variation-axis fill equals sibling-fill results bin-for-bin on the corpus **weight** labels,
    AND a mixed shift+weight program lands in ONE axis-mode histogram equal to its sibling-fill
    decomposition (§6.2, scalar-labeled shift siblings); combine-safety across partitions
    (identical spec, deterministic label order).
  - **§6.2 declaration contract** (r11 — the only behaviour §6.2 MEASURED to be silent had no
    anchor; **rescoped in r12 to the frontend-declared-only rule §6.2(ii) now binds**, because the
    r11 anchors froze user-declaration behaviour that §6.2 left optional AND that today's
    `Histogram.fill` cannot accept — it requires one array per axis,
    `graphed-histogram src/graphed_histogram/boost.py:160-161`): the declared bin set equals the
    §6.1d inferred label set EXACTLY, with the direct discriminator that
    `h.sum(flow=True) == h.sum()` (a stale or partial declaration otherwise buries the difference
    in a non-growth `StrCategory`'s overflow bin — measured, bh 1.7.2, `sum 2.0` vs
    `sum(flow=True) 3.0`); a second fill whose
    inferred label set differs from the first's is a hard error naming the mismatch (§6.2 i,
    cross-fill agreement); **and a user-constructed histogram that already carries a `"variation"`
    axis is refused with an error pointing at the opt-in mode** (user-declared axes are §11). The
    r11 "undeclared label at fill" and "unsorted user-supplied bin order" anchors are DELETED —
    under frontend declaration neither state is reachable.
  - **§6.2(i-bis) axis-mode result shape**: an axis-mode varied output is a BARE histogram
    carrying the variation axis (name in `axis.__dict__["name"]`, §6.2(i-bis)), and
    `graphed.labels(h)` returns the axis bin set (NOT
    `["nominal"]`) while `graphed.universe(h, label)` returns that label's slice along it
    — the narrowing helper uniform over all three shapes (§6.1a bare-unvaried, `{label: hist}`,
    bare-axis-mode). **Worded over SEMANTICS, not over a literal subscript expression** (r12): the
    oracle is equality against a manually sliced reference, because
    `h[{"variation": label}]` raises on a bare `bh.Histogram` — measured on boost_histogram 1.7.2
    AND 1.8.0, `TypeError: list indices must be integers or slices, not str` (and
    `StrCategory(..., name=...)` is itself a `TypeError`); only the positional
    `h[{axis_index: bh.loc(label)}]` works.
  - The §6.2 scaling claim frozen **structurally** (R0.10a: no wall-clock in frozen tests): per
    partition, axis mode allocates 1 histogram object and ships 1 combine payload entry vs `N+1`
    in sibling mode (countable at the `FillEvaluator`/`_GroupReduce` seam, `boost.py:100-117`),
    plus bin-for-bin equality. The N≈100 wall-clock sibling-vs-axis comparison is an
    **implementer-report measurement under R0.11** (methodology stated: what is warmed, timed,
    held constant) — NOT a frozen gate.
  - §9.2 one-bundle-N-labels preservation (m9 comparison form, on the r10-bound varied
    `build_bundle`/`reproduce` surface — with the backward-compat control that an unvaried bundle
    still returns a BARE array) + `inspect()` label listing (§9.1).
  - **§9.1 `graphed.variations(ctx)`** (no anchor before r10, and load-bearing because §6.2
    explicitly refuses to give numeric ordering from bin index): per-name tags and kinds, plus the
    parsed float value under **both** parsers — canonical e-form `m?\d+(em\d+)?` (`5em1` → 0.5,
    `m15em1` → −1.5) and datacard p-form `m?\d+(p\d+)?` (`2p5` → 2.5) — and a non-numeric tag
    (`up`) returning no value rather than raising.
  - Docs: a "How variations work" design.rst section with **executed** examples (the docs-sweep
    rule) covering §7.3's limitation explicitly.
- **m51 — variation-aware write-out (skim augmentation)** (repos: `graphed` +
  `uproot5-graphed-mvp`). Targets: §6.4. Frozen anchors:
  - Superset-row anchor, against an **INDEPENDENT** reference (r10 — the r9 wording compared the
    written rows against per-label row sets taken from the same varied graph, which under §6.4a's
    "the OR is recorded as ordinary graph ops over the per-label masks" degenerates to
    `OR(masks) == OR(masks)` for any wrong per-label mask — the self-derived trap §5.2a names): the
    per-label reference row sets are computed **eagerly with plain awkward, outside graphed**, from
    the same input events (the `m23/test_group_plan.py:60-66` and `m7/adl.py:156-158` house
    pattern); the written row set MUST equal their union, and each universe's reconstructed rows
    MUST equal that universe's eager row set.
  - Bit-exact round-trip: write an augmented skim → the §6.4e reader reconstructs every
    universe's post-selection values and row set bit-for-bit vs the in-memory varied run (the m9
    comparison form) — covering a shift with object-level migration (per-label inner masks,
    §6.4d, **written through the per-LEVEL `select={0: event_mask, 1: jet_mask}` channel** —
    §6.4a r11 is what makes this anchor satisfiable at all; a single row mask cannot express it),
    a weight-only label, a label structurally equal to nominal (all-zero delta), and an
    e-canonical numeric-tag label (`murf_5em1`): stored names embed the label verbatim and the
    reader returns the same label.
  - **`graphed.selection(ctx)` bridge** (§6.4a/§9.1, r11): a skim written from the §2.6 context
    idiom — `to_parquet(events.Jet, select=graphed.selection(sel))` where `sel = events[mask]` —
    round-trips identically to the same skim written with the mask passed by hand;
    `graphed.selection` on a ROOT context returns `None`. Without it the m51 sink is reachable
    only from the loose §2.1a style, one milestone after §2.6 makes the context the primary idiom.
  - **Entry checks (§6.4a, r12 — TWO predicates, each anchored with the positive control IT
    decides; the r11 single offsets predicate could not decide the case r11's own anchor named as
    its positive control)**: (1) **multiplicity** — a write whose per-label member offsets differ
    from nominal's at any stored level is refused, **per partition at execution time from
    `_WritePart` before any buffer is stored** (`python/graphed/awkward/io.py:111-127` evaluates
    inside the worker; do NOT freeze a record-time raise); (2) **row-space agreement** — a record
    whose context is not the one the supplied `select=` mask derives from is refused at the
    `to_parquet` call naming both contexts, with the *silent-corruption* case as its named
    positive: a record carrying a NON-varied embedded selection (`sel = events[nominal_mask]`,
    then `select=varied_mask`) is refused, not written on mismatched rows — and the chained-context
    case (`graphed.selection(sel2)` for `sel2 = sel[mask2]` against a root-row-space record)
    likewise.
  - Representation anchors, structural (R0.10a — no size thresholds in frozen tests): appended
    columns land in the bound exact representation (XOR-delta values, packed masks) with
    identifier-shaped stored names (labels verbatim, §6.4b) — verified by reading the raw file
    schema + manifest; the compression WIN is an R0.11 implementer-report measurement on a real
    skim (methodology stated), NOT a frozen gate.
  - Manifest: parquet KV metadata lists exactly the appended labels/columns/representations and
    reads back; the augmented file also round-trips through `ak.from_parquet` (the arrow-write path
    must reproduce awkward's own KV entries, §6.4e); an unvaried write keeps the `ak.to_parquet`
    path, carries NO manifest, and is byte-identical to today — **as a SAME-PROCESS comparison,
    never a committed `.parquet` fixture** (§6.4g: a parquet footer embeds its writer version —
    `parquet-cpp-arrow version <arrow version>`, re-measured r12 as `25.0.1` under pyarrow 25.0.1
    via `ParquetFile(path).metadata.created_by` — so a committed blob breaks on a pyarrow bump and
    across §A.5 matrix legs while the behaviour is correct — R0.10a). Committed byte oracles stay
    for GIR/IR goldens (§6.3).
  - **Structure refusal (negative anchor, §6.4d)**: a stored varied field whose per-label offsets
    differ from nominal's is refused with an error naming the label and the field — with a positive
    control that a same-multiplicity shift with object-level migration still writes and round-trips.
  - ROOT half: `graphed_write` gains IR evaluation (derived columns in ROOT skims — the §6.4f
    larger half) with the same round-trip anchor; numpy-backend refusal test (§6.4f).
  - Single-read witness on the augmented write run (§5.2b form).

Definition of Done per milestone = the standard checklist (root `CLAUDE.md` §E.0): targets exactly
as specified, frozen suite green and unmodified since freeze, ≥90% diff coverage from the frozen
suite, determinism gate, ruff/clippy/mypy-strict (src AND tests, R0.4a), Sphinx `-W`, full-matrix
CI green at the pinned revision (R0.5), attempts log + reviewer APPROVE recorded.

## §11 Out of scope (Phase 2 — named, not silently dropped)

Declarative nuisance registry / config layer (mkShapesRDF-style `{name, type, kind, samples}`);
correlation/decorrelation metadata, envelope/RMS/symmetrize post-aggregation ops; dataset-level
variation automation (separate-sample variations stay a partition-metadata pattern, documented);
lossy/ratio ("1+delta") storage for §6.4 reconstruction columns (measured NOT bit-exact — worklog
2026-07-30; any opt-in must leave §6.4c's exact default intact); per-variation file fan-out (one
file per universe — §6.4 appends columns instead; the `part_path` prefix/suffix seam exists,
`write.py:77-79`); auto-symmetric weight derivation from a lone `up` (§2.6b);
**user-declared `"variation"` axes** for §6.2 (the frontend declares them in v1; a user-constructed
variation axis is unfillable today — `Histogram.fill` requires one array per axis,
`graphed-histogram src/graphed_histogram/boost.py:160-161` — and supporting it needs a fill-arity
carve-out plus a declared-vs-inferred reconciliation rule, r12);
per-variation monitor/dashboard axis; stage-granular checkpoint task ids (the §7.3 fix);
variations crossing Exchange/Join boundaries (§5.4); implicit variation cross products; weight
clamping/validation hooks (narf `theory_weight_truncate` precedent); growth category axes;
**per-sample divergence of the variation-label set** (merging outputs across samples whose label
sets legitimately differ — the exemplar's suffix-blacklist pathology, lit §ewkcoffea-confirmed;
§6.1a governs one program's outputs, not cross-sample merging); a constant/scalar-Array broadcast
helper needing NO shape donor (§4.1's normalization gap — `gak.full_like` covers the donor case);
a **gak inner-index verb** (`arr[:, i]` on the awkward idiom — measured absent, §2.6 note (i); the
`gak.firsts(arr[gak.local_index(arr) == i])` spelling covers the PDF-member case today, so this is
ergonomics, NOT a blocker, and is deliberately NOT scoped into m48–m51);
**multiplicity-changing stored variations** for §6.4 (shift-dependent cleaning / overlap removal /
matched collections: no representable same-shape delta, refused in v1 per §6.4d); a first-class
Rust `Vary` NodeKey.

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
| Corpus stacked weight (central b-tag on shifted jets) | `systematics.py:74-76`; `_btag_weight` `:25-36` |
| JER-SF hybrid smear: content-seeded PCG64, one draw for all variations, signed/non-monotone | `coffea src/coffea/jetmet_tools/CorrectedJetsFactory.py:36-47,64-95` (local @ f34b8bdf) |
| correctionlib `systematic` category param in one payload | `tests/frozen/preserve/m9/agc.py:38-66` |
| M29 multi-weight fill + identity discipline | `graphed-histogram src/graphed_histogram/boost.py:166-174,205-206`; `tests/frozen/m29/test_multi_weight_fills.py:82-99` |
| Single-pass group plan witness | `graphed-histogram tests/frozen/m23/test_group_plan.py:68-77` |
| bh rejects 2-D weight; StrCategory probes | cba §histogram §2,§3 (runtime probes, bh 1.7.2) |
| `{label: hist}` group reduce; `_SumFills` merges all fills | `graphed-histogram src/graphed_histogram/boost.py:100-122,88-98` |
| Golden-bytes + param-absence frozen patterns | `tests/frozen/core/m40/test_join_serialize.py:84-99`; `m29/test_multi_weight_fills.py:93-99` |
| Array dunder surface incl. `__array_ufunc__`, bitwise; `__getitem__` accepts Array/str/list/slice/int and TypeErrors otherwise; `filter` has NO check (a Varied AttributeErrors inside `record_op`) | `python/graphed/array.py:156,245-275,344-371,374-375,377-379`; `python/graphed/session.py:152,159` |
| `Provenance` = (filename, lineno, function, source) only — no lineage channel (why §2.3e is an object attribute) | `python/graphed/provenance.py:26-33,66-79`; driver-side `Session._provenance`/`sourcemap()` `session.py:30,113-125` |
| Positional outputs; unknown-kind raise | `graphed python/graphed/execute.py:99-126` |
| Whole-IR task_id (no cross-revision reuse) | `python/graphed/core/plan.py:164-176,286-301` |
| First-boundary-only plan builders (§5.4) | `python/graphed/shuffle.py:170,232` |
| Single-partitioned-source check | `python/graphed/aggregate.py:89-93`; union projection `:101` |
| StageError is built ONLY driver-side today (M6 debug runner); the worker closure has no provenance/error wrapping — §8.2's transport is NEW work | `python/graphed/debug/runner.py:6-7,37,57-69`; `python/graphed/aggregate.py:44-65,95-97`; executors translate only: `graphed-executors src/graphed_executors/submit/engine.py:381-396` |
| DCE compacts + remaps node ids; pipeline rebuilds into a fresh interned store (why §8.2 keys post-reduction) | `src/optimizer/mod.rs:1-11,88-116` |
| `mark_output` de-duplicates; `evaluate_ir` returns one value per DISTINCT output (why §7.2 keys node ids, not positions) | `src/store.rs:152-153`; `python/graphed/execute.py:126` (re-measured 2026-07-30) |
| Non-growth `StrCategory` silently overflows an undeclared label (why §6.2 binds the declaration) | measured, boost_histogram 1.7.2 (2026-07-30): `sum 2.0` vs `sum(flow=True) 3.0`, `Traits(overflow=True, growth=False)` |
| `FillEvaluator` flattens each input INDEPENDENTLY (why §6.1d's per-object fill stays unflattened) | `graphed-histogram src/graphed_histogram/boost.py:39-47,60-71` |
| `ak.to_parquet` vs `pq.write_table` differ in bytes AND KV metadata; `ak.to_parquet` has no metadata param (why §6.4e branches) | measured, awkward 2.12.0 / pyarrow 25.0.0 (2026-07-30): sha256[:16] `ad1725aca34f2bbb` vs `43b093e8bc616bd7`; KV `{awkward_array_metadata, ak:parameters}` vs `{ak:parameters}` |
| §3.3/§5.2a reduced shape requires a per-universe terminating reduction | measured 2026-07-30 vs `graphed-latest`: with reduction N=16→(17, 34), N=128→(129, 258), Δ(N=1→2)=52; without, N=16→(17, 18), N=128→(129, 130), Δ=51 |
| `build_bundle`/`reproduce` are singular today (why §9.2 binds a varied surface) | `python/graphed/preserve/bundle.py:103-123,206-210` |
| `gak.full_like` records a real constant-valued op (the §4.1 flat-SF form) | `python/graphed/awkward/functions.py:612-616`; parity-pinned `tests/frozen/awkward/m24/test_interface_parity.py:74-76` |
| `graphed-executors` has no `graphed-histogram` dep; corpus wheel ships no reference JSONs (m49 fixture facts) | `graphed-executors pyproject.toml:20-35`; `graphed-corpus pyproject.toml:28-30` vs `corpus/references/`; vendored copy `graphed tests/_corpus/references` |
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
| Write path: `_WritePart.__call__` — single-output evaluate → record-vs-column → write, no metadata | `python/graphed/awkward/io.py:111-127` |
| `compile_ir` variadic outputs ("EXACTLY the requested outputs", M22) — the §6.4f sharing lever | `python/graphed/execute.py:54-70` |
| Write read-list (`_evaluation_columns`) — must widen for appended columns | `python/graphed/awkward/io.py:157-185,113` |
| No write/sink NodeKey — write is driver-side Python only | `src/node.rs:41-85` (the WHOLE enum — variant heads at `:42` Source, `:46` Op, `:51` Reduction, `:56` External, `:64` Stage, `:72` Exchange, `:81` Join; a completeness claim needs the full span), re-verified 2026-07-30 |
| Parquet KV metadata unused today (greenfield for the §6.4e manifest) | re-verified 2026-07-30: the only `metadata` uses on the write/read path are `ParquetFile(path).metadata.num_rows` (`python/graphed/parquet.py:77,107,118`); no `key_value_metadata` / `schema.with_metadata` anywhere in `graphed-latest/python` or `uproot5-graphed/src` |
| `graphed_write` copies branches verbatim — zero IR evaluation (§6.4f ROOT half) | `uproot5-graphed-mvp src/uproot/writing/_graphed_write.py:59-64` |
| numpy write hard-caps one 1-D column (§6.4f exemption) | `python/graphed/numpy/io.py:163-171` |
| `part_path` prefix/suffix seam (per-universe file fan-out parked, §11) | `python/graphed/write.py:77-79` |
| Compression probe: ratio NOT bit-exact; XOR exact by construction; packed XOR masks ~4.7× | worklog 2026-07-30 (R0.11, methodology stated) |
| Dotted/minus field names round-trip byte-exact in pyarrow storage; KV metadata round-trips | measured probe, pyarrow 25.0.0 (worklog 2026-07-30, r7) |
| `ak.from_parquet(columns=["a.b"])` silently EMPTY (splits on `.`; list-path form works) — why §1.1 canonicalizes | measured probe, awkward 2.12.0 (worklog 2026-07-30, r7) |
| uproot 5.7.5 RNTuple: `__getitem__` is exact-first (a dotted field IS reachable) but `RField.array()` fails — `to_akform` splits the path on `.`; `ntuple.arrays([name])` still works | `behaviors/RNTuple.py:1560-1562` (exact lookup), `:1564-1569` (dot-split fallback), `:562,567` (`to_akform` split → `KeyInFileError 'murf_0'`) — re-measured 2026-07-30 |
| TTree writer joins nested fields with `.`; TTree lookup is exact-first and splits only on `/`, never `.` | `writing/_cascadetree.py:1606`; `behaviors/TBranch.py:2015-2017` (exact-first), `:2019-2024` (`/`-split) |
| CPython `**`-unpacking admits non-identifier tag strings (validation must be channel-independent) | measured, CPython 3.12.10 (worklog 2026-07-30, r7) |
| `Array` is `__slots__`-ed — a context handle needs an ADDED slot (§2.3e) | `python/graphed/array.py:127-128` (`__slots__ = ("_node_id","_session")`); `python/graphed/numpy/array.py:71-74` (`__slots__ = ()`); `__getattr__` underscore guard `array.py:332-335` |
| Every frontend `Array` is built at ONE chokepoint — **FIVE** call sites, all of them (why §2.3e propagation is not per-function) | `python/graphed/session.py:140` (`source`, def `:133`), `:168` (`record_op` `:142`), `:183` (`record_exchange` `:170`), `:204` (`record_join` `:185`), `:242` (`record_external` `:206`); `_array_cls` assigned `:39`, no call site outside `session.py` (re-verified r12) |
| No tuple subscript on the awkward-idiom `Array`; the expressible inner index (§2.6 sketch) | measured 2026-07-30 vs `graphed-latest`: `w[:, 1]` → `TypeError: unsupported index (slice(None,None,None), 1)`; `gak.firsts(w[gak.local_index(w) == 1])` over `[[1,2,3],[4,5,6]]` materializes `[2.0, 5.0]`. Tuple form is numpy-idiom only: `python/graphed/numpy/array.py:132-136` |
| `Histogram.fill` is POSITIONAL (`h.fill(pt=…)` is not a thing outside `hist.graphed`) | `graphed-histogram src/graphed_histogram/boost.py:153-163` |
| Histogram spec is fixed at `__init__` and baked into node identity at `fill` (why §6.2 declares at FILL time) | `graphed-histogram src/graphed_histogram/boost.py:146-150` (`self._spec = spec_of(self)`), `:180-212` (`chash = content_hash(self._spec)`; `params={"spec": …}`; `self._evaluators[chash] = evaluator`); `_spec.py:115-122,129-135` |
| `_GroupReduce.layout` is COUNT-based positional slicing (why §6.1c re-binds it to indices) | `graphed-histogram src/graphed_histogram/boost.py:100-117` (`for j in range(i, i + k)`), built from `len(h._fill_nodes)` at `:282` (r12: `:198` is inside `record_external`); per-slot spec is `h._spec` `:282`, `_GroupZero` `:127-130`, `Histogram.plan` `:245-255`; `python/graphed/aggregate.py:57-65` |
| `gak` defines NO `__all__` (why §2.3c binds an explicit discovery rule + non-vacuity floor) | measured 2026-07-30: `grep -c "__all__" python/graphed/awkward/functions.py` → 0; `grep -c "^def " …` → 73 (incl. private helpers); package `__all__` at `python/graphed/awkward/__init__.py:17-31` lists modules/classes |
| m24 anti-drift pin is a **39**-name literal | `tests/frozen/awkward/m24/test_interface_parity.py:39-79` (counted 2026-07-30) |
| `graphed` has NO `graphed-histogram` dependency; the house pattern is `importorskip` (m48 fixture fact) | `graphed pyproject.toml` `dev` extra (boost-histogram/hist only); CI installs `.[dev]` `.github/workflows/ci.yml:34,57,143`; `tests/frozen/preserve/m25/test_histogram_preservation.py:31`, `m27/test_variadic_call_templates.py:185,207`, `m30/test_producer_cross_seam.py:155` |
| `graphed-histogram` has NO corpus dependency and no reference JSONs (m48 fixture fact) | measured 2026-07-30: `grep -rn "corpus" tests/ .github/workflows/` → 0 hits; runtime deps `pyproject.toml:20-21` |
| `graphed`'s only cross-process frozen test is the M6 error pool (it ships no `Executor`) | `tests/frozen/debug/m6/test_process_boundary.py:7,16` |
| `uproot5-graphed-mvp` has NO frozen tree (m51 creates one) | measured at `393ecef`: `find . -type d -name "*frozen*"` → empty; **12** flat `tests/test_graphed_*.py` (+2 shared helper modules `graphed_uproot_analysis.py`/`graphed_uproot_report.py`, re-counted r12); zero `tests/frozen` references repo-wide |
| Parquet footers embed the WRITER VERSION (why §6.4g's golden is same-process, not a committed blob) | re-measured r12 (awkward 2.12.0 / pyarrow 25.0.1): the footer string is `parquet-cpp-arrow version <arrow version>` = `25.0.1`, readable as `ParquetFile(path).metadata.created_by`; two writes of the same array in one process ARE byte-identical |
| Corpus rounds to 6 decimals PRE-fill and again in the comparison helpers (m48 matrix anchor) | `graphed tests/_corpus/graphed_corpus/analyses/systematics.py:79,102,50`; `histograms.py:20,34-37,39-42`; gak has no `round(decimals)` — `rint` is a ufunc only, `python/graphed/array.py:54` |
| Corpus b-tag SF is the CENTRAL SF on JES-shifted jets (why §2.1 stacking is label-aligned for weights) | `graphed-corpus src/graphed_corpus/analyses/systematics.py:74-76,25-36` (re-counted r12: `:73` is blank, `:75` is the `ht` sum) |
| `StageError.__hash__` is a hand-written tuple (`__eq__` is `__dict__`-based) — a new field does NOT ride free | `python/graphed/debug/errors.py:75-78` (`__eq__`, `:78` is the `__dict__` compare), `:80-81` (`__hash__`) — re-counted r12 |
| `_PartitionReduce` is the plan's opaque `process` spec; `task_id` folds `identity()` (the §7.3 one-time churn) | `python/graphed/aggregate.py:44-65`; `python/graphed/core/plan.py:72-90,164-176` |
| `to_parquet` is awkward-idiom only (numpy has its own 1-D-capped one) — §6.4a/f spelling | `python/graphed/awkward/__init__.py:14,30`; `python/graphed/awkward/io.py:206-216`; `python/graphed/numpy/io.py:158-173` |
| `gak.broadcast_arrays` records an awkward-namespaced op; `graphed-histogram` has no awkward runtime dep (why §6.1d's broadcast is a neutral seam) | `python/graphed/awkward/functions.py:677-685`; `graphed-histogram pyproject.toml:20-21` (runtime) vs `:24-38` (dev) |
| `bh.Histogram` has NO name-based axis lookup: `StrCategory(name=…)` and `h[{"variation": label}]` both raise (why §6.2(i-bis) slices by POSITION) | measured r12, boost_histogram **1.7.2 and 1.8.0**: `StrCategory(..., name="variation")` → `TypeError: unexpected keyword argument 'name'`; `h[{'variation': 'jes_up'}]` and `h[{'variation': bh.loc(...)}]` → `TypeError: list indices must be integers or slices, not str`; `h[{1: bh.loc('jes_up')}]` works. With `axis.__dict__["name"]="variation"` set, `h.axes.name == ('variation',)` |
| Axis "names" are spec METADATA in graphed-histogram, round-tripped from `axis.__dict__` (the §6.2(i-bis) name carrier) | `graphed-histogram src/graphed_histogram/_spec.py:31-37` (`_metadata_of`), `:81-84` (`_restore_metadata`), `:115-135` (`zero_of` rebuilds a plain `bh.Histogram`) |
| `Histogram.fill` requires ONE array per axis (why a user-declared variation axis is unfillable, §6.2(ii)/§11) | `graphed-histogram src/graphed_histogram/boost.py:160-161` |
| `CompiledGraph` carries only `ir` + `source_names`; the PyO3 surface exposes no record→reduced id map (why §8.2's transport needs a NEW read-only core accessor) | `python/graphed/execute.py:36-45,54-80`; every `#[pymethods]` fn enumerated in `src/lib.rs:106-543` (add_source/add_op/add_reduction/add_external/add_exchange/add_join/node_count/to_dot/serialize/deserialize/nodes/outputs/reduce/reduce_incremental/reduction_report); `remap` never returned, `src/optimizer/mod.rs:88-116`; stage members evaluated inline `execute.py:110-117` |
| `graphed.numpy` DOES ship donor-free constants — but as eager fixed-shape Sources a one-source plan cannot bind (the precise §4.1 gap) | `python/graphed/numpy/creation.py:27-28,31-75`; `__all__` `python/graphed/numpy/__init__.py:578-598`; single-source binding `python/graphed/aggregate.py:57-63,96-101`; `python/graphed/execute.py:104-105` |
| `ak.broadcast_arrays` raises on a length mismatch (why §6.1d's refusal is a message CONTRACT, not `FillEvaluator`) | measured r12, awkward 2.12.0: lengths 7 vs 3 → `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`; a jagged 3-row value broadcasts fine |
| gak public surface is **65** functions with heterogeneous first arguments (why §2.3e's propagation gate is scoped, not blanket) | measured r12: 73 `def`s / 65 public in `python/graphed/awkward/functions.py`; `apply_correction` `:476`, `onnx_inference` `:513` (payload first), `to_list` `:693`, `head` `:732`, `sample` `:737` (eager), `fields` `:717`, `type_of` `:722`, `backend_of` `:727` (non-Array returns), `zip` `:118`, `concatenate` `:383`, `where` `:400`, `unflatten` `:600`, `linear_fit` `:346` |
| `Array` public METHODS exist beyond the dunder surface (why §2.3a widens) | `python/graphed/array.py:374-391` (`filter`/`map`/`reduce`/`repartition`); numpy idiom `python/graphed/numpy/array.py:92-190`, tuple `__getitem__` `:132-136` |
| `graphed`'s Array-consuming module verbs (the §2.3d enumeration) read `node_id`/`session` directly | `python/graphed/__init__.py:8-25`, `__all__` `:27-58`; `python/graphed/execute.py:74`; `python/graphed/aggregate.py:66-72`; `Array.node_id`/`session` are PROPERTIES (`array.py:137-143`) and `__getattr__` guards only `_` (`:332-335`) |
| `graphed.apply` is a public module verb with `Array.map`'s execution-time contract (the §2.2 `Varied.apply` name collision, accepted knowingly) | `python/graphed/array.py:397-410`; exported `python/graphed/__init__.py:9` |
| `_WritePart` evaluates PER PARTITION in the worker and unpacks ONE output (why §6.4a's offsets check is execution-time and §6.4f must widen the unpack) | `python/graphed/awkward/io.py:111-127` (`(out,) = evaluate_ir(...)` `:122`), `:206-216`; per-partition task graph `python/graphed/write.py:32-43` |
| `graphed` cannot host a fill-based frozen matrix (m48 AND m49(i) fixture fact) | `graphed pyproject.toml:41-48` (`dev` = boost-histogram/hist, no `graphed-histogram`); CI `.[dev]` `.github/workflows/ci.yml:34,57,143`; house pattern `tests/frozen/preserve/m30/test_producer_cross_seam.py:155` |
| Phase-2 parking being un-parked | `graphed-root-prompt.md:1262,1282,1286`, `ops_catalog.md:75` |

## Revision history

- **r12 (2026-07-30)** — review round 3 (three independent r11 reviews: facts / design / tests,
  `systematics-vary-plan-review-r11-{facts,design,tests}.md`; 32 findings, 30 after cross-lens
  merge — 0 BLOCKER, 6 HIGH, 11 MID, 13 LOW; the §6.2 axis-slicing defect and the §6.2
  declaration-hedge defect were each raised by two lenses and are merged). Every finding
  re-verified in-session against the pinned verification roots before acting; audit trail in
  `systematics-vary-plan-revision-r12-notes.md`. **Nothing rejected, nothing deferred** — no
  finding's resolution required reversing an owner-locked decision.
  **HIGH** — **§8.2's transport re-grounded**: it keyed on post-reduction node ids no channel
  produces (measured: `CompiledGraph` = `ir` + `source_names` only; the whole PyO3 surface
  enumerated, no record→reduced map; the `remap` vector never leaves Rust; and fusion collapses a
  universe's chain into ONE `Stage`), so m49 now scopes an explicit **read-only core accessor**
  `record_id -> (reduced_id, member_index)` (§3.1 intact — no NodeKey, no optimizer arm) with the
  coarser output-position fallback stated honestly, and §8.2(ii)'s provenance re-keyed through it.
  **§6.4a's entry check split into TWO predicates** — the r11 offsets predicate provably cannot
  decide the embedded-selection case the m51 anchor names as its positive control (it is a
  within-record comparison; the corruption is a record-vs-mask ROW-SPACE mismatch), so row-space
  agreement is bound structurally via §2.6b lineage plus a runtime row-count check.
  **§6.2's user-declared axis hedge deleted** — three m50 anchors froze behaviour §6.2 left
  optional AND that `Histogram.fill` cannot accept (measured: one array per axis,
  `boost.py:160-161`); v1 is frontend-declared only, user-declared axes park in §11, and the
  silent-overflow discriminator survives as a declared-equals-inferred invariant.
  **§2.3d widened to the whole Array-consuming module surface** (`apply`/`compile_ir`/
  `aggregate_plan`/`read_columns`/`evaluate_ir`/`to_parquet` were unclassified) with §2.2 binding
  `Varied` to reserve `node_id`/`session` — otherwise field-access `getattr` turns a duck-typed
  read into a recorded `field` op and `compile_ir` silently compiles nonsense.
  **§6.1d's refusal re-bound to a message CONTRACT** — the named `FillEvaluator` raiser is
  unreachable under the bound broadcast seam (measured: `ak.broadcast_arrays` dies first on a
  length mismatch), so the m48 anchor freezes the execution-time message, not a class.
  **§2.3e's propagation gate scoped and split from §2.3c's** — a behavioural gate over the
  measured 65-function surface is not buildable (payload-first, eager, non-Array-returning and
  typed-operand members enumerated), and a frozen test cannot grow arguments for a later function.
  **m49(i) moved to `graphed-histogram`** — r11's own m48 fixture analysis applies verbatim and was
  left unapplied to m49's headline matrix, which would have `importorskip`-SKIPped in CI.
  **MID** — §6.1d's broadcast seam re-bound as `graphed.broadcast_like(value, factor)` over an
  ARBITRARY factor (the context could only supply the ambient one); §6.1c's per-slot spec bound to
  the FILL node's spec (`h._spec` lacks the axis-mode variation axis); §6.4a's "applies NONE of
  them" disambiguated (level-0 OR applies to rows; no other mask touches the buffers; every level
  is stored packed); §6.4a's offsets check named as an execution-time, per-partition `_WritePart`
  raise; §9.1 gains **`graphed.weight(ctx)`** (§6.4b presumed varied factors were nameable, and the
  §2.1 stacking anchor needed a fill without it); §6.2(i-bis) binds the axis-name carrier
  (`axis.__dict__["name"]`) and POSITION-based slicing; new m48 anchors for the three unanchored
  gak classification classes and for op-level divergence; §2.6c's re-indexing anchor strengthened
  from length equality to elementwise per-label equality; §4.3's extraction mechanism named
  (`session.walk` + the §7.2 map); m48's three straddling anchors assigned per repo.
  **LOW** — §4.1's "constant Array from nothing" corrected (`graphed.numpy` ships donor-free
  constants; the real bar is partition alignment under one-source binding); §2.3e's prose now names
  all FIVE `Session` construction sites, not three; §2.2 records the `Varied.apply` /
  `graphed.apply` collision knowingly; §2.3a widened to public METHODS (numpy idiom's ~25);
  m48 targets gain §7.2; m49's arity anchor scoped to sibling mode; §5.3's projection stats and
  §6.1c's `.plan()` refusal re-worded (the latter over fill-node count, so m50's axis mode is not
  over-frozen); m50's `graphed` directory no longer labelled "preservation/docs only";
  line-number corrections — `_GroupReduce.layout` `:198`→`:282`, `StageError` `:74-77`/`:79-81` →
  `:75-78`/`:80-81`, corpus stacking `:73-75`→`:74-76`, uproot flat tests 14→12, parquet writer
  version restated version-agnostically (`25.0.1` re-measured; `24.0.0` was a foreign environment).
  Anchors appendix +11 measured rows, 7 rewritten.
- **r11 (2026-07-30)** — review round 2 (three independent r10 reviews: facts / design / tests,
  `systematics-vary-plan-review-r10-{facts,design,tests}.md`; 40 findings, 39 after cross-lens
  merge — 1 BLOCKER, 7 HIGH, 15 MID, 16 LOW; the §6.1a-vs-axis-mode defect was raised by both the
  design and tests lenses and is merged). Every finding re-verified in-session against the pinned verification roots
  before acting; audit trail in `systematics-vary-plan-revision-r11-notes.md`. **Nothing rejected,
  nothing deferred** — no finding's resolution required reversing an owner-locked decision
  (naming, functional surface, e-form canonical, context attachment, record-time expansion +
  interning, m48–m51 scope incl. §6.4, JER-SF non-ordering, the Phase-2 pull-in).
  **BLOCKER (§6.4 object-level cutflow)** — §6.4d required per-label object-level validity masks
  that no bound API could supply: the only selection channel was §6.4a's single event-level row
  mask, so the post-object-cut record tripped §6.4d's own offsets refusal (which IS the migration
  case) while the pre-object-cut record left the writer blind to the inner cut, making m51's
  REQUIRED object-migration positive control unsatisfiable. **`select=` is now per LEVEL** (one
  row mask, or an ordered `{0: event_mask, 1: jet_mask}` mapping of `Varied` masks); the writer
  applies none of them to stored buffers and stores one packed per-label mask per supplied level.
  §6.4d and the m51 anchors updated to name the channel.
  **HIGH** — §6.2's axis declaration moved from plan time to **fill time** (measured: a
  `Histogram`'s spec is fixed in `__init__` and baked into node identity at `fill`, so a plan-time
  axis leaves nodes/evaluators/`_GroupReduce` disagreeing) plus a cross-fill agreement rule; §6.2
  gained the missing **axis-mode result shape** (bare hist + `graphed.labels`/`universe` reading
  the variation axis — otherwise the §6.1a narrowing helper answers `["nominal"]` for a histogram
  that contains `jes_up`), with §6.1a/§6.1b explicitly scoped to sibling mode; **the fill is a
  combining point** and raises the divergence error itself (§2.3e's op-level rule cannot see
  handles no op combined — `h.fill(a_from_ctx1, b_from_ctx2)`); §6.1d's already-flattened refusal
  re-bound to an **execution-time** length check (there is no static discriminator: a per-event
  value and a flattened per-object value have identical 1-D forms); §2.1 stacking **split per
  overload** — the weight form combines label-aligned per §2.4, so an inherited shift label's
  ambient becomes `old[L] × factor[L]` (the corpus computes the CENTRAL b-tag SF on JES-shifted
  jets, so the naive reading misses `ttbar_4j1b_jes_up` entirely), with the m48 stacking anchor
  extended to a weight-on-shift case; the §2.6 sketch's `lhe_w[:, i]` respelled (measured: no
  tuple subscript on the awkward idiom; `gak.firsts(w[gak.local_index(w) == i])` measured working)
  and `h.fill(pt=…)` made positional; **m48's anchors partitioned per repo** with the fixture
  facts bound (neither repo can host the corpus matrix as it stands — `graphed` has the references
  but no `graphed-histogram` and would `importorskip`-SKIP the headline gate in CI;
  `graphed-histogram` has the fill but no corpus).
  **MID** — §2.3e binds an ADDED `__slots__` slot and names `Session`'s five construction sites as
  the single propagation chokepoint (measured: `Array` is `__slots__`-ed, an ad-hoc attribute
  raises); §6.1c re-binds `_GroupReduce.layout` to per-slot output INDICES (the count-based
  positional layout mis-slices on the very dedup case §1.2 mandates); §2.1 signature gains
  `collections=` (it was mandated two sentences later but absent) → FOUR shadowed names; §6.1d
  binds the three-way fill fold ORDER and extends the broadcast to **every** weight factor
  (an unbroadcast explicit per-event factor length-mismatches in a per-object fill); §6.4a
  replaces "pre-selection by construction" with a decidable entry check (offsets equal nominal's
  at every stored level) and adds the **`graphed.selection(ctx)`** bridge so the m51 sink is
  reachable from the §2.6 context idiom; §6.1d's broadcast re-bound as a neutral backend-dispatched
  seam (`gak.broadcast_arrays` is awkward-namespaced and `graphed-histogram` has no awkward runtime
  dep); §2.6a re-worded so `events[mask]` is not contradicted by "`[]` resolves ONLY tree content";
  §2.3c binds the enumeration **discovery rule + non-vacuity floor** (gak has no `__all__`, so the
  stated mechanism discovers nothing and passes tautologically); §6.4g's unvaried-write golden
  re-based on a same-process comparison (a parquet footer embeds its writer version); new anchors
  for §2.3b, §2.5's diagnostic, and §6.2's declaration contract; m50's histogram-side frozen
  directory pinned.
  **LOW** — Part I §3's `Δ = D+2` → `K+2 = 52` (D means the shared prefix in §3.3); m24 literal is
  **39** names (`:39-79`), not 41; "the `graphed` repo contains no process pool" corrected (it
  ships no `Executor`; its M6 pool is real); `src/node.rs:41-70` → `:41-85` (a completeness claim
  needs the whole enum); the two "write-seam report §N" citations replaced with reproducible
  anchors (no such file exists); `uproot5-graphed-mvp` has NO frozen tree — m51 creates one;
  `to_parquet` named as awkward-idiom; §1.1's "usable verbatim as a kwarg name" scoped, the 32-char
  cap re-stated as a tag-sanity bound, non-minimal canonical tags now re-rendered (`50em2`→`5em1`),
  and "unify" split into across-calls vs within-one-call; `graphed.variations` marked m50 in §2.6a;
  m48's corpus anchor gained the `stable()` 6-decimal clause; m48's schema-absence anchor scoped to
  KEY SETS with §7.3 recording the one-time all-programs `task_id` churn; m49's §8.2 anchor gained
  `StageError.__hash__`. Anchors appendix +19 measured rows (2 rewritten); §11 parks the gak
  inner-index verb.
- **r10 (2026-07-30)** — review round 1 (three independent r9 reviews: facts / design / tests,
  `systematics-vary-plan-review-r9-{facts,design,tests}.md`; 1 BLOCKER, 7 HIGH, 13 MID, 11 LOW after
  cross-lens merge). Every finding re-verified in-session against the pinned verification roots
  before acting; audit trail in `systematics-vary-plan-revision-r10-notes.md`.
  **BLOCKER (context inference)** — §6.1d named `provenance` as the carrier of a fill's event
  context, which measurably cannot carry one (`Provenance` is a 4-field source-location dataclass;
  and interning gives sibling contexts the SAME node ids, so no node-id-keyed map can distinguish
  them). New **§2.3(e)**: context-tag propagation as a fifth bound dispatch point — a Python-object
  attribute on the frontend wrapper, explicitly outside node identity, with a merge rule at the op,
  a drop rule, and the same dynamic exhaustiveness gate as the gak classification.
  **HIGH** — §7.2 re-bound to `(output, label) → node id` (measured: `mark_output` de-dups, so a
  positional map breaks on the very dedup case §1.2 mandates); §8.2's transport mechanism withdrawn
  and rebuilt as NEW m49 work (the cited "already delivers" channel does not exist — no worker-side
  `StageError` construction anywhere in the production path) and the map made set-valued per §3.4;
  §6.2 gained a bound declaration contract (measured: non-growth `StrCategory` silently overflows an
  undeclared label); §6.1d's ambient broadcast made implementable (per-object fills pass UNFLATTENED;
  the sketch fixed to match); §6.4a re-bound to an explicit `select=` mask (the implicit form needed
  an expression-retargeting pass §3.1 forbids); §2.6c gained ambient re-indexing and a definition of
  varied (label-plural) contexts; §1.2/§6.1c and five other unanchored binding requirements gained
  m48 anchors.
  **MID** — §3.3/§5.2a spell the benchmark builder (the pinned `2N+2`/`Δ=52` need a per-universe
  terminating reduction; measured both ways) and name §3.3 as the deliberate M4 carve-out to R0.10a;
  §4.3's impact-set predicate withdrawn for the node-id form (the old one is false for a correct
  implementation); §2.4 union order bound; §2.1 signature-shadowed names (`nominal`/`is_weight`/
  `variations`) bound with mapping escapes; §2.6d now refuses shift forms on data contexts too;
  §6.4d gained a multiplicity refusal; §6.4e's writer swap made conditional (measured: the arrow path
  changes bytes and loses awkward's KV metadata); m49's reference matrix split across repos with its
  fixture facts; m51's superset anchor re-based on an eager, independent reference; §9.2 binds the
  varied `build_bundle`/`reproduce` surface; §10 pins the consolidated repo's frozen directories.
  **LOW** — dynamic (not literal-list) enumeration for the §2.3 parity/classification gates;
  §1.1 negative-zero and 32-char tag rules; §6.1a's union result type declared with a narrowing
  helper; §4.1 corrected (`gak.full_like` exists — the cba grep was module-scoped); the correctionlib
  float-key claim weakened to what `agc.py:56-62` supports; #469's "2-8×" carries its
  word-level-UNVERIFIED caveat; RNTuple hazard re-stated from measurement (exact-first getitem;
  `to_akform` is what splits) and its anchor re-pointed; `TBranch.py:2098` → `:2015-2017`;
  §2.3(b)'s description of today's `__getitem__`/`filter` corrected; §6.4b's stale "r8
  canonicalization" citation and p-form lead fixed. Anchors appendix +12 measured rows.
  **Nothing rejected, nothing deferred**: no finding's resolution required reversing an owner-locked
  decision (naming, functional surface, e-form canonical, context attachment, record-time
  expansion + interning, m48–m51 scope incl. §6.4, JER-SF non-ordering, the Phase-2 pull-in).
- **r9 (2026-07-30)** — encoding decision, owner-selected (three-option AskUserQuestion after a
  design exchange): **e-form canonical** for float-valued tags, superseding r8's p-form.
  Canonical numeric grammar `m?\d+(em\d+)?`: integers as plain digits (PDF indices untouched),
  fractional values as minimal-mantissa `em`-exponent scientific form (`"0.5"`→`5em1`,
  `"-1.5"`→`m15em1`, `"1e-8"`→`1em8`) — the identifier-safe rendering of the owner's
  scaled-integer-with-exponent-suffix proposal (`1.2345`→`12345e-4`), self-describing with a
  uniformly parseable numeric structure over the whole float range (deletes the r9-draft
  Phase-2 widening seam). Input grammar widens to full float literals incl. exponents;
  canonicalization by exact decimal-string arithmetic (no IEEE artifacts) kills all spelling
  multiplicity (`"2"`≡`"2.0"`≡`"2e0"`≡`"20e-1"`); cross-notation numeric-equality rejection
  covers legal datacard p-tags (`{"0.5", "0p5"}` rejected). Decision trail + trade-off recorded
  in §1.1; §6.4b/§9.1/m48/m51 updated.
- **r8 (2026-07-30)** — owner directive on the float-tag encoding: **canonicalize to the
  p-encoding at the source** instead of r7's dual representation. `vary` still accepts plain
  float spellings (`"2.5"`, `"-2"`) as input sugar but canonicalizes at call time (`.`→`p`,
  leading `-`→`m`); the p-form (`2p5`, `m2`) IS the tag everywhere — labels, bins, result keys,
  disk — restoring the r6 every-label-is-an-identifier invariant unconditionally and deleting
  the r7 name-safe dual machinery (its collision check collapses into ordinary duplicate
  detection: `{"0.5", "0p5"}` are now the same tag). Probe coverage carries over directly: the
  p-form name `__vary_murf_0p5__Jet_pt` was in both r7 probe fixtures and measured byte-exact +
  readable in every path. §6.4b/e simplified (labels verbatim in stored names; the manifest
  stays the machine channel); §9.1 parses the p-form; m48/m51 anchors updated. The owner's
  scaled-integer alternative (×10 until integral + a scale in metadata) is recorded in §1.1 and
  not chosen: it leaves the minus sign unhandled, is not self-describing (`murf_25` is
  ambiguous without the side table; the p-form carries its own inverse), and the scale varies
  per tag across one family; revisitable Phase 2.
- **r7 (2026-07-30)** — owner directive: tags must also admit **stringified floating-point
  values** (μR/μF `"0.5"`/`"2.0"`, σ-scans `"-2"`…`"2"`). §1.1 gains the two-form grammar:
  identifier tags (unchanged) + fixed-point numeric tags `-?\d+(\.\d+)?` (no exponent/`+`/
  `inf`/`nan`), with numeric-equality duplicate rejection (`{"2","2.0"}`), name-safe collision
  rejection, and channel-independent validation (CPython `**`-unpacking admits non-identifier
  keys — measured). The r6 "every label is an identifier" invariant is rescoped: it holds for
  identifier tags; numeric-tag labels reach disk through the §6.4b **name-safe form** (`.`→`p`,
  leading `-`→`m`, the datacard `0p5`/`m2` convention). Grounded in a 3-agent measured
  verification (2 probes + a full-plan dependency sweep): dotted names store byte-exact in both
  file backends but are unreadable-by-name (`ak.from_parquet(columns=)` silently empty; uproot
  RNTuple getitem splits on `.`; the TTree writer uses `.` itself as its nesting separator), so
  on-disk names stay identifier-shaped and the §6.4e manifest becomes the sole label resolver.
  §6.2 pins the sorted axis as lexicographic (determinism/combine-safety measured unaffected;
  numeric ordering comes from §9.1, which now reports parsed values for numeric tags). m48
  grammar anchor rewritten to the r7 rejections (the sweep's hard-block finding: the r6 wording
  would have frozen the old rejections into read-only tests); m51 round-trip gains the
  numeric-tag fixture. Anchors +4 measured rows.
- **r6 (2026-07-30)** — collaborator-feedback respin (owner-relayed, three points). (1)
  **Functional surface**: reserved context attributes (`events.weights`, `events.vary`) were
  latent collisions with real branch names — replaced by ONE module verb
  `graphed.vary(target, name, …)` with three overloads (§2.1: loose Array/Varied; context weight
  form `is_weight=True`; context shift form `Collection={tag: record}`), ALWAYS returning a new
  object; contexts reserve NO names (§2.6a); registry mutation → object lineage (§2.6b/c;
  fill-time snapshot re-bound as immutability; §6.1d most-derived-context rule); r5's
  `Varied[label]` (collided with string field access) → `graphed.universe`/`graphed.labels`/
  `graphed.nominal` module functions (§2.2, §9.1). (2) **Tag grammar beyond up/down** (§1.1):
  kwarg-name tags + `variations=` mapping escape for numeric families; label must be a valid
  identifier; arbitrary hashables rejected. (3) **NEW scope — §6.4 variation-aware write-out
  (skim augmentation) + milestone m51**: OR-of-selections superset rows; appended
  exact-by-construction reconstruction columns + packed varied-cutflow masks with bit-exact
  round-trip REQUIRED (the suggested "1+delta" ratio measured NOT bit-exact → Phase-2 opt-in,
  §11); object-level masks for jagged migration (§6.4d); parquet-KV manifest + reader (§6.4e);
  seams bound to the measured-greenfield write path (all verified: variadic `compile_ir`
  sharing, `_WritePart` append point, read-list widening, ROOT `graphed_write` needs IR
  evaluation — the larger half; numpy exempt). Part I §3 rationale paragraph + §4 skim-growth
  cost added; anchors appendix +9 rows.
- **r5 (2026-07-30)** — owner semantic correction + three owner-selected decisions (context
  methods / inferred ambient fills / progressive+scoped registration): systematics attach to the
  **event context**, not to per-fill threading. New §2.6 (events.vary collection replacement incl.
  lockstep Jet+MET, events.weights.add/add_multi, derived registry-inheriting contexts, data
  guard); §6.1d (fill infers the context and auto-applies the ambient weight; union with value
  and explicit-factor labels; broadcast to object structure; two-context error; unweighted
  opt-out); §4.2 cross-ref; Part I rationale paragraph; m48 targets + seven event-context
  anchors. Frontend-only — §3 backend and the `Varied` machinery unchanged.
- **r4 (2026-07-30)** — owner directive: do not engineer the shift contract to the monotone JES
  expectation. §5.1 rescopes the `jes_up > nominal > jes_down` witness to the JES fixture only
  (general contract asserts no ordering); new §5.5 makes stochastic JER-SF re-smearing first-class
  with two binding rules grounded in coffea's implementation (content-seeded PCG64 randomness —
  determinism gate unchanged; one shared draw across universes → interns in the shared prefix,
  non-monotone by construction); m49 gains the JER-SF fixture anchor (bidirectional-migration +
  byte-identity + shared-draw witnesses, no ordering); anchor row added.
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
