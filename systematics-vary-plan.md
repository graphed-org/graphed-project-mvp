# Systematic variations in graphed — `vary`, the variation frontend + IR treatment (execution plan)

Status: **streamlined design.** Revision identity lives in git, not here. Rationale
(PART I) is context and binds nothing; PART II binds. Committed in the meta repo
(`graphed-org/graphed-project-mvp`) together with its research companions. Measurements and
evidence trails live in the files the plan cites — `systematics-vary-codebase-analysis.md`
(cited *cba §agent*) and `systematics-vary-litsearch.md` (cited *lit §agent*) — or are explicit
stated assumptions. Source directive: the owner's high-level doc (Google Doc `116lg4…`, mirrored
at `scratchpad/systematics-plan.txt`). The plan-review cycle is closed (§12.1); review history
lives in git and the `systematics-vary-plan-review-r*` / `systematics-vary-plan-revision-r*-notes`
files. m48 and m49 are DONE and merged; next step is the m50 decomposition.

> **Naming — owner decision.** Verb **`vary`** (`graphed.vary`), concept noun **"variation"**,
> container **`Varied`**. Variation labels are `f"{name}_{tag}"` underscore style (`jes_up`,
> `btag_down`); **`"nominal"` is reserved** for the central value. This matches RDataFrame's
> `Vary` precedent (lit §rdf-vary §6), graphed's lowercase-verb convention (`join`,
> `repartition`), and — verbatim — the stored corpus reference names (cba §corpus §1).

## Scope deviation (flagged, deliberate — the R22.0 pattern)

The project plan lists **systematics-as-a-graph-axis** as Phase 2 everywhere the Phase-2 listing
appears (root `CLAUDE.md` Part F, the root prompt Out-of-scope block, inline in R22.0 and R22.10,
and the corpus `ops_catalog.md`). **The project owner has decided to pull it into scope now**
(this doc's source directive). Consistent with "THE PROJECT PLAN ALWAYS WINS," the deviation is
deliberate and flagged, not silent: this doc records it; the root prompt gets an **R23** entry
binding it once landed (§12.3). The pull-in is *smaller* than R22's: no new execution substrate —
the work rides the existing IR/interning, group-plan, and executor machinery, which were built
expecting exactly this load (Part I §1).

---

# PART I — RATIONALE (context; non-binding)

## 1. Why now: the system was built for this and the anchor tests already exist

- Systematics bookkeeping is "the largest pain point in analysis software" in the field's own
  assessment (Second Analysis Ecosystem Workshop report, arXiv:2212.04889 — lit §rdf-vary §5).
- graphed's founding rationale names variation-multiplied graphs as *the* scaling driver: "On real
  analyses with many systematic variations the graph reaches tens of thousands […]"
  (`graphed-root-prompt.md`); the corpus `graph_bloat_note.md` quantifies it (full AGC weight +
  JES/JER + b-tag set ⇒ O(10⁴) nodes — cba §corpus §5). M4's optimizer was hardened for it in
  advance: the egg extractor was redesigned O(N) specifically for "the deep chains a systematics
  graph produces" (`src/optimizer/engine.rs`), and frozen `tests/frozen/core/m4/test_systematics.py`
  already pins that a 3300-variation, ~10⁴-node graph reduces in < 1 s to a node count
  **independent of variation count** (cba §corpus §4).
- The acceptance anchors pre-exist: the corpus canonical systematics analysis (weight = b-tag SF ±,
  photon-ID SF ±; shift = JES ± applied *before* selection) ships stored reference histograms
  with fingerprints and the behavioral frozen tests `test_weight_variation_preserves_selection` /
  `test_kinematic_variation_changes_selection` (strict `jes_up > nominal > jes_down` selected-count
  ordering) — `tests/frozen/corpus/m05/` in the consolidated repo (cba §corpus §1,§3).
- What exists today is caller-side replication only: m05 calls the analysis once per variation
  string; the m9 preservation fixture bakes the variation into per-bundle build config
  (`tests/frozen/preserve/m9/agc.py`); no frontend/IR construct expresses "N variations of one
  graph" (cba §corpus, "Assessment"). The ops catalog parked exactly this row as Phase 2; this
  plan un-parks it.

## 2. Prior art and its hard lessons (digest — full evidence in the two research docs)

**RDataFrame `Vary`** (lit §rdf-vary). The precedent this work takes its name and user model from.
Register-then-forget: `Vary(col, expr, tags, name)` attaches variations to a column; propagation
through downstream `Filter`/`Define`/actions is automatic; `VariationsFor(result)` yields a keyed
result map (`"nominal"` + `name:tag`); everything runs in one event loop, sharing I/O and all
computation not downstream of the varied column. ROOT hand-implements the sharing (copy-on-write
column registers; per-variation cloned Defines/Filters skipped when unaffected), and within a
universe *every* use of the varied column coheres — whole-cone substitution. Hard lessons: varied
results lack first-class identity (file-write name collisions); no varied `Report`/cutflow;
Snapshot needed a bolt-on per-event validity bitmask because varied selections diverge; the
extraction API sat in `Experimental` for 4+ years.

**WRemnants / narf** (lit §rdf-users §1-3). The precision-analysis end refuses per-variation
control flow entirely: zero uses of `Vary`. Weight systematics are per-event Eigen tensor columns
filled into extra histogram axes in one pass (one atomic shared histogram, O(1) memory in thread
count); even kinematic effects are beaten into weight vectors or alternate-column fills; cut
migration becomes histogram axes applied at fit-prep; nuisance naming, symmetrization, envelope
collapse, and decorrelation happen outside the loop as histogram transforms. Lesson: the
labeled-axis fill is the proven scaling shape, and bookkeeping must not live in the event loop.

**mkShapesRDF (Latinos)** (lit §rdf-users §4). The config-driven end: a declarative nuisance
registry compiled into `Vary` calls (weight nuisances native-`Vary` the weight column; kinematic
ones come from pre-produced friend trees). Hard lessons: they reimplemented `Vary` wholesale for
the Snapshot stage (suffixed-column defines + OR-of-cuts), prune variations whose base column no
output uses, and rename every extracted histogram to dodge ROOT name clashes.

**coffea** (lit §coffea-sys). Three disjoint mechanisms glued by string conventions: `Weights`
(weight-type only; stores variations as `var/nominal` ratios, auto-symmetric Down — the right
economics), the jetmet factories + shift loop (the whole selection re-executes per shift, nothing
dedups), and dataset-level variation samples. The in-IR `add_systematic` prototype stalled for
~4 years: it materialized variations as columns (solving storage, not propagation), left selection
propagation a documented TODO, and left the combinatorics method (`explodes_how`) unimplemented.
Lesson, verbatim from the evidence: **variation forking is a graph-transformation problem, not a
data-layout problem.** coffea Discussion #469 reports ~2-3× (up to ~7-8× for many systematics)
for extra-axis systematics over re-run loops — UNVERIFIED (lit §coffea-sys carries the caveat).

**Pythonic analyses** (lit §pythonic-analyses): nsmith-/boostedhiggs, PocketCoffea,
TopEFT/topeft + cmstas/ewkcoffea.
**Kelci's analysis — owner-confirmed: `cmstas/ewkcoffea`**, the canonical exemplar
(lit §ewkcoffea-confirmed; `main@063e8d7` = coffea-0.7-era, branch `coffea2023@63abb06` =
dask-era port). The 0.7-era treatment is the field's mature form: 12 weight bases → 24 labels
under combine-datacard names encoding correlation scope, 6 object-shift labels by column swap, a
7-pass outer shift loop re-running selection + a BDT, the nominal-only exclusion rule explicit in
code, and the Weights registry hand-partitioned by shift-impact ("these weights can go outside
the sys loop since they do not depend on pt of mu or jets") — a human-judgement impact analysis.
The dask-era port is the highest-value evidence in the survey: migration changed *none* of the
systematics semantics but forced hand-written CSE inside the physics processor
(`masked_val_cache`/`masked_weights_cache`), degraded `deepcopy` to `copy` + "TODO do we need
copy here?", and abandoned persisting the built task graph (`# Does not work` above a commented
`cloudpickle.dump`). No dask-era version of the analysis ever carried an object shift (the empty
`obj_correction_systs` predates the branch), and a latent `hout = {}`-inside-the-shift-loop bug
would silently keep only the last shift the moment one is added — the dask-era shift-loop cost is
therefore UNVERIFIED there.
**`FNALLPC/wwz4l`** (lit §ewkcoffea-confirmed addendum): named as a modern-coffea version, it is
neither — a coffea-0.7-era CMS-DAS teaching derivative of `ewkcoffea@main` (`main@cc71718`; a
near-verbatim processor copy with byte-identical `ApplyJetSystematics`; zero
dask/`dataset_tools`/`hist.dask` surface). It carries the full weight+shift treatment (27 labels)
and adds no dask-era evidence, so `coffea2023@63abb06` remains the sole modern-coffea exemplar
and the no-dask-era-object-shift finding extends to it. Its distinct value: the teaching strip
removed every piece of *physics* (BDT, EFT, 54→14 categories) while the variation scaffolding —
loops, deepcopies, exclusion rule, growth axes, suffix generator — survived completely intact:
irreducible accidental complexity by construction, precisely what `vary` deletes.

Universal conventions across the surveyed analyses: `"nominal"` reserved; `Up`/`Down`-suffixed
labels; none of the surveyed analyses produced shift × weight cross products (under a kinematic
shift, only the central weight fills — evaluated on that shift's selection); one histogram with a `systematic` StrCategory
axis; data special-cased (no shifts, no variation axis). Universal failure modes: whole-chain
re-execution per shift; defensive `copy.deepcopy` of accumulate-by-mutation Weights;
hand-maintained name lists where a typo silently drops a systematic; per-variation cutflow
clobbering; skim-vs-shift interaction requiring an OR-of-selections mask.

## 3. Why this architecture: record-time expansion + interning, not a new node kind

Three candidate shapes were evaluated against the codebase (cba §ir-rust, §optimizer,
§frontend-python):

1. **A first-class boundary `Vary` NodeKey** (Exchange/Join sibling). Rejected: every non-`Op`
   kind is a stage boundary (`src/node.rs`) and boundaries end stages — a Vary node between a
   kinematic op and the cuts would forbid fusing the varied suffix, defeating M4. It would also
   carry the full M40 checklist (serialize tags, optimizer arms, both backends, `evaluate_ir`)
   *plus* downstream-multiplicity semantics no existing node has (cba §optimizer, "Assessment").
2. **IR-level variation annotation + plan-time expansion** (RDF's internal model). Rejected:
   RColumnRegister/MakeVariations is ROOT hand-implementing the sharing that graphed's
   hash-consing provides structurally; rebuilding it as IR metadata pushes variation-awareness
   into optimizer, projection replay, and executors.
3. **Record-time expansion + hash-consing** (chosen). The frontend re-records the downstream ops
   per variation; `GraphStore::intern` returns existing ids for every node not downstream of the
   varied input, so the unvaried prefix is shared exactly — going N=1→2 variations grows the
   arena by precisely the varied suffix, reduction stays linear in variation count, and the
   reduced form is one shared-prefix stage + one stage per variation (cba §optimizer §2,§5). DCE,
   fusion, projection, determinism, and every executor need zero changes for correctness — `R`
   is opaque end-to-end (cba §exec-checkpoint §4).

The source directive's open question — "is it useful to add optimization impact analysis to
isolate subgraphs a variation must re-run?" — resolves to: it already exists structurally. The
impact set of a shift IS the set of nodes reachable from a label's outputs but not from nominal's.
We expose it as a trivial read-only API (§3.4) and build no invalidation machinery
(cba §optimizer §5).

Weight vs shift needs **no API distinction** (RDF lesson: the dependency structure discovers the
difference — a varied weight only reaches the fill; varied kinematics reach the cuts). It does
need **distinct lowering economics** at the sink, which §4/§5 bind separately.

**Why systematics attach to the event record (owner semantic correction).** Earlier sketches
threaded loose `Varied` weights into each fill by hand — re-creating the survey's
forgotten-weight/name-list failure mode. All three precedents treat systematics as ambient
properties of the event record (RDF's weight is a column of the frame; coffea's `Weights` belongs
to the event batch; boostedhiggs shifts are collection replacements on `events`); the fill is
where everything applicable applies simultaneously (plotting Jet pT must also yield the
pileup-reweighting universes). §2.6 binds the event context (attach-once, ambient thereafter) and
§6.1d the fill inference; the one genuine tension — selection-dependent object SFs cannot be
ambient on the root — is resolved by derived, registry-inheriting contexts rather than the
exemplars' per-channel `deepcopy`.

**Why the context surface is functional, and why write-out enters scope (collaborator feedback).**
A context that reserves attribute names on the event record (`events.weights`, `events.vary`) was
rejected — that namespace belongs to the *tree*: branch names are analysis-controlled and
open-ended, so any reserved name is a latent collision, and a mutable registry leaves no object
identity for provenance to hang on. The surface is one functional verb — `graphed.vary(...)`
always returns a NEW context/container, never mutates — which (a) frees the record namespace
(§2.6a), (b) makes each variation step an object with lineage (§2.6b), and (c) makes the
fill-time registry snapshot rule plain immutability (§2.6c). The same principle resolves
`Varied[label]` colliding with awkward's string-getitem field access: extraction moves to module
functions too (§2.2). The same feedback surfaced the missing sink: skims. Two surveyed frameworks
hit exactly this wall (RDF Snapshot's validity-bitmask bolt-on, mkShapesRDF's `Vary`
reimplementation — Part I §2), and graphed's write path is greenfield: zero variation machinery,
one seam method per backend. §6.4 binds the native treatment: superset rows by OR-of-selections,
appended exact-by-construction reconstruction columns (XOR bit-deltas are exact by construction;
a "1+delta" float ratio is not bit-exact), packed varied-cutflow masks, and a manifest in
existing metadata channels.

## 4. Honest costs (the requirements in PART II that mitigate each)

- **Build-time cost**: expansion re-executes the user's downstream *recording* code per variation
  (Python-side). Mitigated by the incremental reducer (per-step cost ∝ delta) and bounded by a
  variation-shaped anti-quadratic benchmark (§3.3).
- **Partial size ×N**: every reduction-tree slot carries the N-variation composite. Mitigated by
  the variation-axis fill mode (§6.2, O(1) objects) and `pooled_combines`/peer reduction; gated by
  the milestone benchmarks (§10).
- **Checkpoint granularity**: `task_id` folds the **whole plan IR** (`plan.py`), so adding a
  variation later invalidates every cached task even though the graph shares nodes. Documented
  limitation (§7.3); stage-granular content addressing is named Phase-2 follow-up (§11).
- **Union projection**: a merged plan reads the union of nominal + shifted columns for all
  partitions (`aggregate.py`). Accepted for MVP; per-variation projection stats surface the
  cost (§5.3).
- **Boundary interaction**: the m39/m40 plan builders consume exactly one Exchange/first Join
  (`shuffle.py`); v1 therefore restricts variations from crossing shuffle boundaries (§5.4)
  rather than silently miscompiling.
- **Skim growth**: the §6.4 superset+augmentation write stores more rows (OR of selections) and
  more columns than a nominal-only skim. Mitigated by exact-by-construction deltas that are zero
  wherever a label agrees with nominal (maximally compressible) and packed masks (§6.4c); bounded
  by the m51 report measurement on real skims.

---

# PART II — REQUIREMENTS (binding; specific)

## §1 Vocabulary (owner decision)

- **§1.1** Verb `graphed.vary`; container `graphed.Varied`; concept "variation" everywhere (docs,
  APIs, tests, R23). The reserved central label is the string `"nominal"`; user variation labels
  are `f"{name}_{tag}"` (e.g. `jes_up`).
  - **Grammar.** `up`/`down` are conventions, not specials — σ-families, PDF member indices, and
    stringified-float families (μR/μF scale factors, σ-scans; correctionlib category inputs are
    arbitrary strings — `preserve/m9/agc.py` — so a float-spelled key is expressible, §4.1) are
    all first-class. A `name` MUST be a valid Python identifier. A **tag** is a string matching
    `[A-Za-z0-9_]+` — every label is therefore itself a valid identifier, usable verbatim as a
    StrCategory bin (§6.2), result key, manifest key, and on-disk column/branch name (§6.4). A
    tag is not necessarily spellable as literal kwarg syntax (canonical numeric tags are
    digit-leading; `2=` is a SyntaxError) — the `variations=` channel exists for exactly those.
  - **Canonical numeric form (e-encoding; owner decision).** `m?\d+(em\d+)?`: integer values
    render as plain digits (`2`, `102`, `m2` for −2; PDF indices are untouched), fractional
    values as minimal-mantissa scientific notation with `em` for the negative exponent
    (`0.5`→`5em1`, `2.5`→`25em1`, `1.2345`→`12345em4`, `-1.5`→`m15em1`, `1e-8`→`1em8`). A
    fractional value's exponent is negative by construction, so bare `e` never appears in
    canonical form. Negative zero canonicalizes to `0`, never `m0` — one value, one label.
    Parse = `m`→`-`, `em`→`e-`, then a standard float literal: uniformly parseable over the
    whole float range, at the cost of not reading as the decimal at sight (the datacard p-form
    `2p5` does; p-encoded tags remain legal identifier tags, below).
  - **Input sugar and call-time canonicalization.** `vary` ACCEPTS plain float spellings as
    input: a tag matching `-?\d+(\.\d+)?([eE][+-]?\d+)?` (`"0.5"`, `"-2"`, `"2.0"`, `"1e-8"`;
    no leading `+`, no `inf`/`nan`, no `_` separators or whitespace) is canonicalized at call
    time by exact decimal-string arithmetic (never an IEEE round-trip — no float artifacts
    enter labels), so `"2"`, `"2.0"`, `"2e0"`, and `"20e-1"` all yield the SAME tag `2`. A tag
    that already matches the canonical numeric grammar is canonicalized too — re-rendered
    minimally (`"50em2"` → `5em1`, `"05"` → `5`) — otherwise a hand-typed non-minimal e-form
    would ride through as an ordinary identifier tag, two labels for one value. **"Unify" means
    ACROSS calls**: two separate `vary` calls spelling `"0.5"` and `"5em1"` name the identical
    label `murf_5em1`; the same two spellings within one call are a
    duplicate-after-canonicalization rejection (below). A dotted or signed spelling never
    reaches a label. The measured ground for canonicalizing: dotted names break per-field
    access — `ak.from_parquet(columns=["murf_0.5"])` is silently empty, an RNTuple
    `RField.array()` fails because `to_akform` (`behaviors/RNTuple.py`) splits the field path
    on `.`, and the TTree writer uses `.` as its own nesting separator — while
    identifier-shaped names round-trip byte-exact and readable in every measured path.
  - **The 32-character cap.** A canonical tag longer than **32 characters is REJECTED** — a
    tag-sanity bound covering every real σ-scan / μR-μF / PDF family; it does NOT bound the
    label (`f"{name}_{tag}"`) or the on-disk name (`__vary_{label}__{field}`, §6.4b). The input
    grammar states no magnitude bound, so measurement runs BEFORE rendering
    (render-then-measure would materialize e.g. a billion-digit string for `"1e1000000000"`):
    the magnitude test runs on the COMPUTED DIGIT COUNT, and the canonical string is produced
    only once that count is within the cap. The count is (the input's mantissa digits after
    removing the decimal point and stripping leading zeros) + (the exponent adjusted for where
    that decimal point sat). **m48's grammar anchor carries the boundary pair**: `"1.5e31"`
    ACCEPTED with its 32-digit canonical tag, `"1.5e32"` rejected with the magnitude message (a
    naive mantissa-digits + exponent sum is off by one for a dotted mantissa and wrongly
    rejects the accepted half — the discriminating one). The quantity compared against the cap
    is the RENDERED CANONICAL LENGTH under both renderings: for an integer-valued input, the
    normalized digit count, plus 1 when negative (the `m` marker is a character of the tag but
    not a digit); for a fractional input, `len(mantissa) + 2 + len(exponent)`, again plus 1
    when negative.
  - **Two refusals, split by CAUSE.** An input whose INTEGER digit count alone exceeds the cap
    is rejected with the MAGNITUDE message naming the magnitude (`"1e40"`, `"1.5e32"`); every
    other over-cap case takes a canonical-tag-LENGTH message naming the rendered length — the
    sign marker pushing a legal magnitude to 33 characters (`"-1.5e31"`) and the long-mantissa
    fractional case alike. A diagnostic must not blame the wrong property (the same standard as
    §6.1d's loose-value message split and §6.4b's row-space-not-offsets message).
  - **Family and the cross-notation rejection.** Normalization kills spelling multiplicity by
    construction; the one residual duplicate class is **cross-notation**: a p-encoded
    identifier tag (`"0p5"`) does not canonicalize but p-parses to the same value as
    `"0.5"`→`5em1`. Two tags in one family that both parse as numbers (under either notation)
    MUST NOT parse numerically equal (`{"0.5", "0p5"}` and `{"2", "2p0"}` are rejected —
    distinct labels for one value would silently create semantically duplicate universes,
    distinct StrCategory bins, and distinct content hashes). **A family is the set of tags
    carried by one `name` on one container, INCLUDING labels inherited through §2.1 stacking —
    defined here, once, and the check spans calls** (a per-call check would accept the same
    value spelled `"0.5"` in one call and `"0p5"` in the next, uncatchable later since the
    p-form deliberately does not canonicalize). For a CONTEXT target the per-`name` tag map
    §2.2 retains lives on the container the call registers into — the ambient-weight `Varied`
    in the weight form (b), the replaced collections in the shift form (c) — so the family
    check has a named operand from m48, one milestone before `graphed.variations(ctx)` (§9.1,
    m50) exports it. The numeric-equal check runs against inherited labels of the same `name`
    too, and the m48 grammar anchor carries the two-call cross-notation case. (Encoding
    decision, owner: the scaled-integer proposal — scale carried as an exponent suffix —
    rendered identifier-safe IS this e-form; selected over the datacard p-form for the uniform
    full-range grammar. p-tags stay legal identifier tags; they do not unify with float
    spellings, and the cross-notation rejection catches in-family mixes.)
  - **Three channels.** Tags arrive through **kwarg names** (`up=…, sig2=…`), the
    `variations={tag: …}` mapping, and — in the shift form (c), where `variations=` is REJECTED
    with an error naming `collections=` (§2.1) — the **INNER keys of the collection mappings**
    (`Jet={"up": …}`, `collections={Name: {tag: …}}`). Validation and canonicalization are
    **channel-independent** across all three: literal kwarg syntax cannot spell dotted or
    digit-leading tags, but CPython admits any string key through `**`-unpacking, so every
    channel applies the same rules; `variations=` is simply the documented route for such tags.
    Arbitrary hashables are REJECTED (labels serialize into specs, files, and manifests;
    string-only — a float tag is passed as its string, never as a Python float, so the user
    owns the spelling).
  - **Call-time rejections.** `vary` MUST reject, at call time: duplicate labels after
    canonicalization (within the call, within the container, or colliding with inherited
    labels, §2.1); numeric-equal tag pairs within a family (above); a tag supplied both as
    kwarg and in `variations=`; malformed or non-string tags (including Python floats — pass
    the string); and empty tag sets.
  - **`"nominal"` is unreachable as a user label BY CONSTRUCTION, not by a rejection**:
    `label = f"{name}_{tag}"` with a non-empty identifier `name` and a non-empty `tag` means
    every user label contains at least one `_`, while `"nominal"` contains none. The TAG
    `nominal` stays legal — §2.1 routes it through `variations=` because it shadows a signature
    keyword — and yields the ordinary label `pu_nominal`, distinct from the reserved central
    label.
- **§1.2** In the expansion/sibling-fill lowering (§4, §5, §6.1), variation labels are **frontend
  metadata, never structural identity**: a label MUST NOT enter `NodeKey` params, tokens, or
  content hashes. Two variations with structurally identical content intern to the same nodes
  (dedup is correct: renaming a systematic must not recompute — the AddressTable
  label-out-of-hash precedent, `execution.py`). Only real content differences (a different
  input id; a different correctionlib `systematic=` param) fork identity. **Carve-out (§6.2),
  covering BOTH of axis mode's label channels:** in variation-axis fill mode the labels become
  *output content* — (1) StrCategory bin identities in the histogram spec, and (2) §6.2's
  **per-fill variation payload**, a field of the fill's `FillEvaluator` that enters the External
  payload's content hash as `content_hash((spec, variation_payload))` — and in both they DO
  enter the spec/params/content hash, by design; renaming a systematic in axis mode legitimately
  changes the output histogram. m48's §1.2 anchor is sibling-mode-scoped.

## §2 Frontend semantics: `vary` and `Varied`

- **§2.1 (API — ONE functional verb, three targets; always returns a NEW object.)**
  `graphed.vary(target, name, /, nominal=None, *, is_weight=False, variations=None,
  collections=None, **tags)` — a
  **neutral module verb** exported like `join`/`repartition` (the `shuffle.py` precedent; per
  the factorization rule it is not an `Array` method, not gak, not numpy-idiom). It NEVER
  mutates: the result is a new object of the target's kind and the target remains valid,
  unchanged — provenance hangs on object lineage (§2.6b). Tag/member pairs come from `**tags`
  and/or `variations=` under the §1.1 grammar. **The signature's own keyword names shadow
  `**tags`**: `nominal`, `is_weight`, `variations` and `collections` are all legal §1.1 tags AND
  legal tree collection names, so a tag or collection so named MUST come through a mapping
  channel — `variations={tag: …}` for tags in overloads (a)/(b), a
  `collections={Name: {tag: record}}` mapping for collections in overload (c), which resolves
  its own name by self-reference (`collections={"collections": {...}}`). `variations=` is
  REJECTED in the shift form (c) with an error naming `collections=` (the §2.6a
  no-reserved-names hazard at the signature); the m48 grammar anchor covers all of the shadowed
  names.
  **Member rule**: a member may be an `Array` OR a `Varied`. In overloads (a)/(c) a `Varied`
  member is reduced to its central universe (`graphed.nominal(v)`); in overload (b) a `Varied`
  factor is KEPT and consumed label-aligned per §2.4 (`factor[L]`, falling back to its central
  universe when L is new to the factor). The construction checks below apply per member of the
  flattened container.
  Three binding overloads:
  (a) **Array | Varied target** (the loose primitive):
  `graphed.vary(jets, "jes", up=j_up, down=j_dn) -> Varied` with the target as `"nominal"`.
  `is_weight=True` and `nominal=` are invalid here (a loose weight variation is just a `Varied`
  used in a `weight=[…]` factor list, §4.2).
  (b) **Event-context target, weight form** (`is_weight=True`): `nominal` (third positional) is
  the central per-event weight factor and every member is a per-event weight factor —
  `graphed.vary(events, "pu", pu_nom, is_weight=True, up=pu_up, down=pu_dn) -> new context` with
  the factor registered into the returned context's ambient weight (§2.6b).
  **The factor's ROW SPACE is bound here**: the registered factor — and every member of a
  `Varied` factor — MUST live in the TARGET context's row space, i.e. be read through that
  context or through an ancestor of it. An ANCESTOR-handled factor is re-indexed to the target
  across the intervening lineage links per §6.1d link kinds (1)-(3). **The violation half is
  TOTAL**: a factor whose handle is neither the target's own nor an ANCESTOR of it — a
  DESCENDANT handle as much as a divergent one — is a construction-time error naming both
  contexts and the DIRECTION of the mismatch (the descendant case is the natural mis-spelling
  `graphed.vary(events, "btag", btag_sf(sel.Jet), is_weight=True, …)`; no re-indexing exists in
  that direction, a mask having no inverse, §6.4b). The resulting invariant is the one §6.4b's
  precondition assumes: **`graphed.weight(ctx)` always answers in `ctx`'s own row space.** m48's
  stacking anchor carries a positive control registering a factor computed at the PARENT
  context, and the descendant case as a negative control.
  (c) **Event-context target, shift form** (no `is_weight`): each kwarg names a **collection**;
  each value maps tags to varied records — `graphed.vary(events, "jes", Jet={"up": j_up, "down":
  j_dn}, MET={…}) -> new context` — or is a `Varied` carrying exactly the family being
  registered on the context's central collection (m55, `lockstep-varied-plan.md`: MET propagated
  from loose-form jets, unpacked to the map form before anything else runs), with every named
  collection replaced by a `Varied` (all collections in one call MUST share one tag set — the
  lockstep Jet+MET form; §2.6a).
  **`nominal=` is REJECTED in the shift form**, with an error naming `collections=`: the
  collections' central members come from the target context, so `nominal=` has nothing to mean,
  and as a shadowed name it cannot be read as a tag (the m48 grammar anchor covers the shadowed
  names but not this call shape).
  **Stacking**: when the target (or a named collection on it) already carries variations, the
  result inherits those labels and adds the new labels; a new label's member is the provided
  value's central universe (`graphed.nominal(v)` if the provided value is itself `Varied`, else
  the Array as given). In the loose/shift forms (a)/(c) inherited members pass through
  **unchanged**; in the **weight form (b)** the newly registered factor is combined into the
  ambient weight **label-aligned per §2.4**, so an inherited label L's ambient member becomes
  `old_ambient[L] × factor[L]` — the factor evaluated in *that label's own universe* (its
  central universe only when L is new to the factor). **L ranges over the §2.4 union — the
  labels the target already carries (§2.2) TOGETHER WITH the labels this call registers** — not
  over the ambient registry's own labels: `old_ambient[L]` is that registry's member for L, its
  `"nominal"` member when L is new to the registry, `factor[L]` is the container's `"nominal"`
  member when L is new to the container, and the product degenerates to `factor[L]` alone when
  nothing is registered yet. So a NEWLY registered label's ambient member is `old_ambient
  ["nominal"] × factor[L]`, which is what puts `btag_up` into `graphed.weight(sel2)` on an
  otherwise unlabelled target — the m48 weight matrix's own case. **`factor[L]` means §2.4
  applied TWICE when the factor NESTS**: a registered factor may itself be a `Varied` whose
  members are `Varied` (the member rule above; the mainline
  `graphed.vary(sel, "btag", btag_sf(sjets), is_weight=True, up=…, down=…)` registers a
  container labelled `{nominal, btag_up, btag_down}` whose members are each `Varied` over the
  inherited jes labels, `sjets` being `Varied`). Binding: take the container's member for L (its
  `"nominal"` member when L is new to the container), then, if THAT member is itself `Varied`,
  take its own L (its `"nominal"` when L is new to the member). The composed ambient weight is
  therefore always FLAT — `{label: Array}` — which is what `graphed.weight(ctx)` (§9.1)
  returns. The corpus turns on the two-level rule: for `variation="jes_up"` the corpus computes
  the CENTRAL b-tag SF **on JES-shifted, JES-selected jets**
  (`graphed-corpus src/graphed_corpus/analyses/systematics.py` — `sel_jets = good[sel]`
  then `_btag_weight(sel_jets, variation=variation)`, which returns the central SF unless
  `variation` is `btag_up`/`btag_down`), so the `ttbar_4j1b_jes_up` reference IS b-tag
  weighted; a one-level reading would take the b-tag SF on NOMINAL jets and miss the reference.
  Each label NAMES A POINT in nuisance space. A label registered without `points=` carries the
  default point `{name: tag}` and so differs from `"nominal"` on exactly one axis — **unless its
  member depends on another registered nuisance's varied nodes, in which case the joint point is
  minted automatically** (m53, `systematics-design/dependency-fanout-design.md`, superseding the
  "≥2 axes only via explicit `points=`" rule for that case). That axis-aligned set is the default for
  INDEPENDENT members. A universe the graph cannot infer as dependent is displaced on ≥2 axes only via
  explicit `points=`, which m53 inverts to PRUNE the automatic fanout rather than add to it.
  **Ordering rule**: a shift `vary` replaces collections and leaves the ambient registry
  untouched (§2.6b), so a jet-dependent weight registered BEFORE a JES `vary` fills every shift
  universe with its PRE-shift value — structurally unfixable after the fact, since the
  registry's members are already-recorded expressions rooted at pre-shift nodes (the exemplars
  hand-partition this as "these weights can go outside the sys loop", Part I §2). Binding: **a
  shift `vary` does NOT re-derive the ambient weight registry; a weight factor that depends on a
  collection MUST be registered AFTER that collection is varied.** The rule is backed by a §2.5
  diagnostic using machinery §3.4 already scopes.
  All members MUST share one Session, have compatible forms (backend `op_form`-checked at
  construction), and root in the same partitioned-source set (checked at construction; the
  otherwise-deferred failure surface is `aggregate_plan`'s single-source check,
  `aggregate.py`). **Their CONTEXT HANDLES are unified here too** — `vary` is a combining point
  in §2.3e's sense but not an op, so the `record_op` merge chokepoint never sees it: **all
  members' handles MUST lie on ONE ancestry chain, the container carries the most-derived one
  (which is what `graphed.context_of` answers, §2.3e), and divergent handles are a
  construction-time error naming both contexts** — the same rule §2.3e binds at every other
  combining point.
  **The §2.1(b) ROW-SPACE rule generalizes to EVERY overload.** One ancestry chain does NOT
  imply one row space (a §6.1d link kind (1) moves it, and §2.6c puts a read through a derived
  context at that context's per-label row counts). Binding: **every member MUST live in ONE row
  space — the TARGET context's in overloads (b)/(c), the container's most-derived handle's in
  overload (a) — an ANCESTOR-handled member being re-indexed across the intervening links per
  §6.1d kinds (1)-(3) exactly as a §2.1(b) factor is.** **The two rules are ORDERED**: a
  `Varied` SUPPLIED as a member of (a)/(c) is reduced to its central universe AS SUPPLIED, and
  the resulting member is then re-indexed to the target handle **label-aligned per §2.4** — each
  label's member by that label's mask, nominal's by nominal's — the identical operation §2.6c
  already binds for the ambient registry. Read the row-space invariant per label accordingly:
  every member answers in the container handle's PER-LABEL row spaces (§2.6c: a
  `Varied`-mask-derived context's row set differs per label). **A member reached across a link
  no re-indexing can invert — a DESCENDANT handle, e.g. a selection-scoped record assigned to a
  collection on the ROOT context in overload (c) — is a construction-time error naming both
  contexts and the DIRECTION**, the §2.1(b) shape; m48's `vary`-construction divergence anchor
  carries the descendant case as one extra negative control. (m48's `context_of` fixture pins
  the `vary`-IDENTITY-link spelling for row-space stability and §6.4a(2a) proximity; this clause
  decides the mask-derived case by re-indexing.) Lockstep multi-column variation within one
  collection (jet pt+mass shifted together) is expressed by varying a record Array — the corpus
  JES fixture already does this via `ak.with_field` (`systematics.py`); no second verb.
- **§2.2 (`Varied` is a mapping of universes; extraction is functional.)** `Varied` holds
  `{label: Array}` with `"nominal"` always present — **a member may itself be a `Varied`** when
  the container is a registered weight factor (§2.1, resolved two-level), while the AMBIENT
  weight `graphed.weight(ctx)` returns is always flat. **`graphed.labels` stays strictly
  two-level** — the labels of the container it is asked about, never a flattened view over nested
  members; the two-level resolution rule is what reads through nesting, and a flattened listing
  would erase which knob a label belongs to. Verbs that cannot resolve two-level say so: §3.4/§5.3
  refuse a nested member rather than reaching past it. **The container is PER IDIOM**: `Varied`
  mirrors the existing `Session._array_cls` backend seam — a neutral `graphed.Varied` base
  carrying `Array`'s surface, with `graphed.numpy` supplying the numpy-idiom subclass mirroring
  `NumpyArray` (a single neutral container would either leak numpy-idiom names into `graphed`
  proper — §2.1's factorization sentence, root `CLAUDE.md` §A.4 — or fail §2.3a's parity gate on
  the mandated numpy fixture). `graphed.vary(x, …)` returns the container class PAIRED WITH
  `type(x)` when `x` is an `Array`, and with `type(graphed.nominal(x))` when `x` is ALREADY a
  `Varied` (the idiom comes from the members, never from the container), exactly as the session
  pairs its proxy class with the backend (`Session._array_cls` comes from the backend's
  `array_type` factory, falling back to `Array`). §2.3a's dynamic enumeration is then
  self-consistent: inventory and resolving class come from ONE idiom.
  **It additionally retains, PER `name`, the tags registered under that name** — internal state,
  not a second public shape: §1.1's family check is defined over "the set of tags carried by one
  `name` on one container, INCLUDING labels inherited through §2.1 stacking", and the label
  mapping alone cannot answer it (prefix-matching `f"{name}_"` mis-attributes whenever one name
  plus an underscore prefixes another — `vary(v, "jes", up_2=…)` vs `vary(v, "jes_up", …)`).
  `graphed.variations(ctx)` (§9.1, m50) is the per-name listing on a CONTEXT; on a loose
  `Varied` (§2.1a, which stays public) this retained map is the operand and stays internal.
  Universe extraction and introspection are **module functions** (the namespace-collision
  principle, §2.6a): `graphed.labels(x)` (ordered: nominal first, then insertion order;
  inherited labels before new ones under stacking), `graphed.nominal(x)`, and
  `graphed.universe(x, label)` (KeyError on an unknown label, listing the valid labels) — each
  accepting **the same input shapes: a `Varied`, an event context (uniform introspection,
  §9.1), a `{label: hist}` RESULT MAPPING, and a bare histogram-like object (duck-typed on
  `.axes`, never importing `boost_histogram` into `graphed`)** — the per-shape answers for the
  two result shapes being bound in §6.1a (a bare `hist` reads as the single label `"nominal"`)
  and §6.2(i-bis) (an axis-mode histogram reads its variation axis's bin set, re-ordered to this
  section's rule). **`graphed.nominal` on those two shapes is bound here**: **`graphed.nominal(x)`
  ≡ `graphed.universe(x, "nominal")`** — identity for a bare unvaried histogram, `x["nominal"]`
  for a `{label: hist}` mapping, and the nominal SLICE along the variation axis for an axis-mode
  histogram (the natural return-the-argument-unchanged fallback would hand an axis-mode caller a
  histogram whose variation bins sum into the view read as central).
  **On a CONTEXT the answer is bound here, once**: `graphed.labels(ctx)` is the **§2.4-ordered
  union** of (a) the ambient weight registry's labels, (b) the labels of any `Varied`
  collections the context CARRIES — the collections a shift-form `vary` replaced, inherited ones
  included, NOT the implicitly-varied reads §2.6c produces through a `Varied`-mask-derived
  context — and (c) the labels of **`graphed.selection(ctx)` in §9.1's sense — the selection
  reached by skipping over any number of `vary` IDENTITY links and answering as of the first
  non-identity link, `None` for a root context; on a universe/nominal-derived context that
  answer is a single label's unvaried member and contributes NO labels**. The definitional
  reference does not move `graphed.selection`'s own milestone: §9.1 keeps it at m51, and its
  per-link-kind ANSWER is bound there independently of when the verb is exported. Term (c) gains
  an m48 program that isolates it — a context derived by a LOOSE-`vary`-varied mask, where (a)
  and (b) are both empty — while the `vary`-link-walking HALF is knowingly left UNANCHORED (no
  m48–m51-scoped program distinguishes the readings); it stays binding for the verb's
  correctness, on §1.1's `"1e1000000000"` precedent. The union is by construction the SUPERSET
  of the CONTEXT-BORNE half of any §6.1d fill's label set from that context, `"nominal"` first —
  **scoped to context-borne sources, and the scoping is binding**: §6.1d's fill label set also
  unions labels carried by loose values and by explicit `weight=[…]` factors (§2.1a's loose
  `vary` stays public), so a fill's label set can exceed `graphed.labels(ctx)`.
  `graphed.universe(ctx, label)` and `graphed.nominal(ctx)` return **a CONTEXT** — a CHILD of
  the argument in the §2.6b lineage chain (so §6.1d's lineage-based unification can relate the
  result to its argument) — carrying that label's collections and ambient weight (falling back
  to each container's `"nominal"` member per §2.4), with `graphed.selection(...)` equal to the
  argument's selection at that label. The m48 anchor asserts the ancestry relation.
  String subscription `v["pt"]` is **field access** (broadcast per §2.3a, Array-coherent), NEVER
  label lookup — `[label]` indexing is removed: it collided with awkward's string-getitem field
  access. **`x[L]` in this document's PROSE — §2.1's `old_ambient[L] × factor[L]`, §2.4's fold
  notation, m48's stacking anchor — denotes `graphed.universe(x, L)` and is NEVER a literal
  subscript** (transcribed literally it records a `field` op named `"jes_up"`, the hazard the
  removal closes). **Its sibling rule: `==` between two RECORDED expressions in this document's
  prose denotes STRUCTURAL IDENTITY (`.node_id` equality, sound by interning), never a Python
  `assert` on the recorded comparison** — `Array.__eq__` returns an `Array` and `Array` defines
  no `__bool__`, so `bool(a == b)` is unconditionally `True`. A frozen test transcribes it as
  `.node_id` equality or materializes both sides and compares elementwise.
  `Varied.apply(fn)` remains a method — apply a record-time `Array -> Array` function per
  universe (attribute shadowing follows the awkward precedent: real methods win; a field named
  `apply` stays reachable via string getitem). Named `apply`, NOT `map`: `Array.map` is an
  execution-time data callable and the two contracts must not share a name. The collision with
  the public module verb `graphed.apply` is accepted knowingly — the two live on different
  objects with no dispatch path between them; if the m48 test-author judges it confusing, the
  rename is `Varied.per_label`, pinned at m48 freeze like every other new surface here. `fn`
  MUST return an `Array`; if it returns a `Varied` (because it closed over another container),
  `.apply` raises with guidance to combine containers via ordinary ops instead.
  **`Varied` gives EVERY public PROPERTY of the nominal member's class a disposition** — a
  discovery rule over properties, not a two-name list (§2.3a deliberately EXCLUDES properties
  from its parity gate). **The disposition splits by MECHANISM, not by
  `isinstance(m, property)`**: `NumpyArray.T` is a property alias for the recorded `transpose`
  op, while `dtype`/`ndim`/`shape` are `_form_meta`-backed and record nothing (`Array._form_meta`
  itself falls back to recording a `field` op when the form lacks the name). Binding: for every
  non-underscore property on `type(graphed.nominal(v))`, exactly one of three classes applies —
  **(1) `node_id` and `session` raise `AttributeError`** rather than resolving as field access
  (label-mapping field access would answer `varied.node_id` with a recorded `field` op named
  `"node_id"`, which `compile_ir(session, varied)` — reading `arr.node_id` per output — would
  silently compile); **(2) a FORM-ANSWERED property — one whose access on a plain nominal
  `Array` records NO node (today: `shape`/`dtype`/`ndim`) — is answered EAGERLY on the nominal
  member** (sound by §2.1's form compatibility, the same argument §2.3c uses for
  `gak.fields`/`type_of`); **(3) a RECORDING property — one whose access on a plain nominal
  `Array` records a node (`T` today) — takes its underlying METHOD's §2.3a disposition** (`T` →
  *broadcast*: it returns a `Varied` whose `graphed.labels` match the input's). The
  discriminator between (2) and (3) is behavioural and measurable pre-implementation — access
  the property on a plain nominal `Array` and read the `Session.node_count()` delta — so the
  gate classifies each discovered name by measurement rather than by a literal list. **Both this
  rule and §2.3d's dispositions are frozen-anchored in m48** (the §2.3a parity gate cannot reach
  them: `node_id`/`session` are plain properties `inspect.isfunction` does not enumerate).
  `Varied` is a plain frontend object — no IR type, no new NodeKey (§3.1).

- **§2.3 (Broadcast propagation — five bound dispatch points.)**
  (a) **`Varied` implements the full `Array` PUBLIC surface — dunders AND methods** — by mapping
  over labels. Dunders: enumerated at implementation from `array.py`, including `__array_ufunc__`,
  the bitwise set (`__and__`/`__or__`/`__invert__`), `__getitem__`, field access, and all
  reflected variants. Public methods are in scope too: `Array` carries `filter`, `map`, `reduce`,
  `repartition`, and the numpy idiom adds its method set on top of a tuple-accepting
  `__getitem__` override (`sum`/`prod`/`mean`/`std`/`var`/`min`/`max`/`any`/`all`/`argmin`/
  `argmax`/`cumsum`/`cumprod`/`reshape`/`ravel`/`squeeze`/`transpose`/`swapaxes`/`astype`/`clip`/
  `round`/`take`…). An unimplemented method does not raise cleanly — `Varied`'s label-mapping
  field access turns `varied.filter` into a recorded `field` op — so each method carries the same
  per-class disposition as (c): *broadcast* for the elementwise/structural ones, *refusing* for
  `repartition` (§5.4).
  Parity is gated by a frozen test whose inventory is **enumerated dynamically from
  `type(graphed.nominal(v))` at test time** (so idiom subclasses are covered), not from a literal
  list. The method half is `inspect.getmembers(type(graphed.nominal(v)), inspect.isfunction)`
  with no leading underscore, plus the dunder set — the same spelling §2.3c/§2.3d bind, with the
  same self-repairing rule and non-vacuity floor as (c), whose floor for this gate MUST name at
  least one METHOD alongside the named dunders. The PROPERTY half is enumerated too, under §2.2's
  disposition rule: `inspect.getmembers(type(graphed.nominal(v)), lambda m: isinstance(m,
  property))` with no leading underscore, asserting each discovered name resolves per §2.2's
  three-class rule — `node_id`/`session` raise `AttributeError`; a property that records NO node
  on the plain nominal `Array` answers eagerly on the nominal member with a
  `Session.node_count()` delta of 0 across the `Varied` access; a property that DOES record
  broadcasts, returning a `Varied` whose `graphed.labels` match the input's (`T` is a plain alias
  for the recorded `transpose` op, so it broadcasts). The floor names both representatives:
  `varied.dtype` (eager, delta 0) and `varied.T` (broadcast, returns a `Varied`).
  What the gate asserts per name is bound: **(1)** each discovered name is resolved ON THE CLASS
  — `getattr(type(varied), name, None)`, which the instance `__getattr__` never intercepts — and
  MUST be a real attribute (instance-level `hasattr`/`getattr` is unconditionally satisfied by
  the field-access fallback); **(2)** the same test carries at least one BEHAVIOURAL probe per
  disposition class: a broadcast method returns a `Varied` whose `graphed.labels` match the
  input's, and `repartition` raises the §5.4 refusal, not `TypeError: not callable`. §2.3e's
  `Array`-surface propagation gate ((e)(4)) inherits the identical class-lookup rule.
  (b) **Plain-`Array` entry points learn `Varied`**: today `Array.__getitem__` raises `TypeError`
  on a `Varied` mask, and `Array.filter` has no runtime check at all (a `Varied` falls through
  into `record_op`). Both gain an explicit `Varied`-mask branch delegating to the container (the
  corpus requires it: unvaried `photons`/`muons` sliced by a JES-varied selection,
  `systematics.py`).
  (c) **The gak layer gets one dispatch mechanism plus a bound per-function classification** —
  the classification is explicit, lives in code, and is gated by a frozen exhaustiveness test
  that **enumerates gak's public surface DYNAMICALLY at test time** (not a literal name tuple,
  which would let a future gak function go silently unclassified; a dynamic check is also
  self-repairing — a new function is fixed in `src`, never by editing a frozen test).
  Binding discovery: `inspect.getmembers(graphed.awkward.functions, inspect.isfunction)` filtered
  to `__module__ == "graphed.awkward.functions"` and no leading underscore. The MODULE is named,
  not the PACKAGE `graphed.awkward` — the package re-exports modules/classes only and discovers
  NO functions (`graphed.awkward.num` → `AttributeError`), while `gak` IS that same module
  object (`from . import functions as gak`), which defines no `__all__`. Non-vacuity floor,
  asserted in the same frozen test: the discovered set is non-empty, is at least the freeze-time
  count, and contains at least one NAMED member of each
  classification class. The classes: *broadcast* (elementwise/structural default),
  *container-traversing* (`gak.zip`/`concatenate`/… detect `Varied` **inside** their
  Mapping/Sequence arguments), *tuple-returning* (`gak.unzip`/`broadcast_arrays` return a tuple
  of `Varied`), *eager-metadata* (`fields`/`type_of`/… answer on the nominal member — sound
  because §2.1 requires form compatibility), and *refusing* (`gak.join` and boundary verbs, per
  §5.4). Signatures do not change (R17.0 anti-drift preserved).
  (d) **Module verbs and sinks — the enumeration is EXHAUSTIVE over `graphed`'s public
  Array-consuming surface** (an undisposed verb does not fail loudly: §2.2's field-access
  `getattr` turns an unhandled duck-typed read into a recorded op, silently compiling nonsense).
  Dispositions: `graphed.join` and `graphed.repartition` **refuse** with the §5.4 error;
  `graphed.pack_key`, `graphed.shuffle_plan` and `graphed.join_plan` **refuse likewise** — all
  three take an `Array` first and read `array.session` (`shuffle.py`); `pack_key` exists to
  pre-key a source for a shuffle/join and both plan builders ARE the §5.4 boundary path, so one
  refusal message covers all three. `graphed.apply` and `graphed.read_columns` **expand into
  universes** (per-label results — `apply` returns a `Varied`; `read_columns` returns the union
  over all labels' members, §5.3: **`None` — "read every column" — if ANY member's read set is
  `None`, else the sorted set union** — a plain set union would silently narrow a conservative
  label's read list). `graphed.compile_ir` and `graphed.aggregate_plan` **refuse** a `Varied`
  output with an error naming `graphed.universe` — they consume `arr.node_id`/`arr.session`
  directly, and §2.2's reserved-name rule makes the refusal a clean `AttributeError` seam; the
  varied route to a plan is the §6.1c group API. **`graphed.evaluate_ir` is OUTSIDE the
  `Array`-consuming surface and carries NO `Varied` disposition** — its signature is
  `evaluate_ir(compiled: CompiledGraph | bytes, backend, sources, *, externals=None)`; it never
  receives an `Array`. `graphed.broadcast_like` (the §6.1d seam, NEW in m48) **broadcasts**: with
  a `Varied` value and/or factor it returns a `Varied` whose labels are the §2.4 union, per label
  broadcasting that label's members. **`graphed.reindex_to` (the §6.1d lineage seam, NEW in m48)
  BROADCASTS** — the result's labels are computed by **COMPOSING THE LINKS IN LINEAGE ORDER,
  parent-to-child**: a mask-derivation link UNIONS that mask's labels per §2.4, a `graphed.vary`
  link is the IDENTITY, and a universe/nominal PROJECTION link RESETS the accumulated label set
  to empty — each member re-indexed by that label's own mask, so an UNVARIED value re-indexed
  across a `Varied`-mask link BECOMES a `Varied` carrying that mask's labels, while a value
  reached across a link kind (3) is that label's unvaried member and carries NO labels (m48's
  lineage-seam anchor is split PER LINK KIND). **`graphed.unify_contexts` carries NO
  disposition**, taking context handles rather than `Array`s; both m48 verbs are disposed here so
  the m48 gate does not discover `reindex_to` unclassified.
  `graphed.awkward.to_parquet` and `graphed_histogram.Histogram.fill` **accept** — a fifth
  disposition class: `to_parquet` takes a `Varied` RECORD and/or a `Varied` `select=` per §6.4a
  (§6.4's canonical skim is `to_parquet(events.Jet, select=…)` where `events.Jet` is itself a
  `Varied` after a shift-form `vary`, §2.6b — the record arm is the headline case); `fill` takes
  `Varied` values/weights/`sample` per §6. **`to_parquet` carries NO disposition until m51 and is
  NOT in m48's table**: today's signature has no `select=` parameter, and `to_parquet` is outside
  `graphed.__all__` so it is not discovered dynamically; at m51 it enters the table *accepting*
  and m51's anchors assert the accepting behaviour. `Histogram.fill` is *accepting* from m48 and
  is the class's behaviourally real representative.
  **The disposition CLASS SET**: the legal §2.3d dispositions are **refusing / expanding /
  broadcasting / eager-metadata / accepting**, where *accepting* means the verb consumes a
  `Varied` operand and handles it internally without returning per-label results to the caller.
  Exhaustiveness is kept by a DISCOVERY RULE, not by this literal list (the self-repairing rule
  §2.3a/c already adopt), bound over the MEASURED signature surface, not over first parameters (a
  first-positional-`Array` filter misses `compile_ir` and `apply`, whose `Array` operand is not
  first, and `read_columns`, whose first operand is `Sequence[Array]` rather than `Array`).
  Binding: the m48 anchor enumerates `graphed.__all__` dynamically, filtered to
  `inspect.isfunction` members **any of whose parameter annotations MENTIONS
  `Array`** (including `Sequence[Array]`, unions and `*args: Array`), **UNION an explicitly NAMED
  freeze-time floor list**, and asserts every member of that union carries a disposition. The
  named list is: **`graphed.compile_ir`**, **`graphed.context_of`**, **`graphed.broadcast_like`**,
  `graphed_histogram.Histogram.fill`, and — **from m51 only** — `graphed.awkward.to_parquet`.
  `compile_ir` is named because its parameters are annotated `Session` and `Any`, so the
  annotation filter never discovers it; `context_of` and `broadcast_like` are named because they
  are the SOLE representatives of *eager-metadata* and *broadcasting*, both NEW in m48 (and
  `value: Any` is a plausible annotation for `broadcast_like`'s neutral factor). **The floor is
  asserted PER REPO**: `graphed`'s m48 gate takes `{graphed.compile_ir, graphed.context_of,
  graphed.broadcast_like}` (`to_parquet` joins it at m51), while
  `graphed_histogram.Histogram.fill`'s disposition is asserted in `graphed-histogram`'s flat
  `tests/frozen/m48`, which depends on `graphed` and hosts every other fill-shaped m48 anchor
  (§10 preamble's cross-repo import rules apply).
  **`graphed.numpy`'s public module verbs are in scope too, and the gate runs PER IDIOM
  PACKAGE.** The same annotation-wide filter over `graphed.numpy.__all__` discovers exactly six
  functions — `apply_gufunc`, `empty_like`, `full_like`, `ones_like`, `project`, `zeros_like` —
  each reaching `array.session`/`arrays[0].session`. Binding: the four `*_like` creation verbs
  and `apply_gufunc` **broadcast** (per-label recording, §2.3c's elementwise rule;
  `gnp.full_like` is the numpy twin of §4.1's `gak.full_like`), and `project` **expands —
  per-label results, `{label: Projection}`, NOT `read_columns`' union treatment**: `Projection`
  is a frozen dataclass whose one field is `read_columns: Mapping[str, frozenset[str]]` with no
  conservative `None` sentinel — conservative projection is expressed as the FULL column set — so
  §5.3's `None`-dominant union rule has no operand here.
  **The AWKWARD idiom package is in scope on the identical footing** (§2.3c's gate is scoped to
  the MODULE `graphed.awkward.functions` and reaches no package-level verb): the same
  annotation-wide filter over `graphed.awkward.__all__` discovers exactly **`project`** and
  **`project_buffers`** (`project(array: Array, *, on_fail="raise") -> Projection` /
  `project_buffers(...) -> BufferProjection`, both routing through `_replay`, whose first
  statement reads `array.session`); the other package functions take a `Session`/`Partition`
  rather than an `Array` (`from_awkward`/`from_parquet`/`read_parquet_partition`) or are disposed
  at m51 (`to_parquet`). Binding: both **expand**, per-label results, **each returning its OWN
  return type per label: `project` to `{label: Projection}` and `project_buffers` to
  `{label: BufferProjection}`** (`BufferProjection` is a distinct frozen dataclass whose field is
  `read_buffers`, not `Projection`'s `read_columns`; the numpy twin above is `project` only).
  m48's gate runs the identical dynamic enumeration over `graphed.numpy.__all__` AND
  `graphed.awkward.__all__`, in the same repo and the same anchor. **The FLOOR is asserted over
  the UNION of the enumerations, never per enumeration** (neither idiom package hosts any member
  of the named floor list, so a per-enumeration floor is unsatisfiable against a correct
  implementation), and it stays a containment floor, never an exact set.
  **Two exclusions are bound**: `inspect.isfunction` keeps classes such as `graphed.Varied` out
  of the enumeration, and **`graphed.vary` itself is excluded BY NAME** — it PRODUCES containers
  rather than consuming them, and its annotations mention `Array`, so it would otherwise be
  discovered with no disposition class to carry. The gate carries §2.3a/c's **non-vacuity floor
  in the same test**: the discovered set is non-empty, is at least the freeze-time count,
  contains every member of the named floor list, and contains at least one member of **each
  class in the bound class set that the repo's own table can host** — at m48 `graphed`'s table
  has no *accepting* member (`to_parquet` is out until m51; `Histogram.fill` lives in the other
  repo), so `graphed`'s m48 floor requires at least one member of each of {refusing, expanding,
  broadcasting, eager-metadata}; a containment floor, so m51's added *accepting* member cannot
  red it. This list is the freeze-time floor, not the definition; a verb whose signature mentions
  no `Array` and which is not named above (`evaluate_ir`) is out of scope by construction.
  **The m49 verbs this plan itself adds enter the table *expanding* when they land** — §3.4's
  impact helper and §5.3's per-label projection-stats verb (§9.1) both answer PER LABEL; their
  operand annotations mention `Array`, so the annotation-wide filter discovers them one milestone
  after the m48 freeze. Nothing reds: the self-repair rule puts each new function's
  classification in `src` and every floor is a containment floor. m49's own anchors assert their
  per-verb shapes (§5.3's `{label: …}` mapping; §3.4's impact sets).
  (e) **Context-tag propagation** (the §6.1d substrate). Every `Array`/`Varied` produced from a
  contexted input carries a **context handle: a Python attribute on the frontend wrapper object,
  explicitly NOT part of node identity** — it never reaches `NodeKey` params/tokens/hashes (§1.2
  and interning stay intact). **This is an Implementation Target, not free**: `Array` is
  `__slots__`-ed with no `__dict__` (`__slots__ = ("_node_id", "_session")`) and `NumpyArray`
  keeps it closed (`__slots__ = ()`). Binding: **one added slot, underscore-prefixed** (e.g.
  `_context`), so `Array.__getattr__`'s `startswith("_")` guard keeps it out of field access,
  **plus a read-only PUBLIC seam exposing it — `graphed.context_of(array)`-shaped, spelling
  pinned at m48 freeze, returning the handle or `None`** — the slot alone is not reachable
  across a package boundary, and §6.1d requires `Histogram.fill` (in `graphed-histogram`) to
  read its inputs' handles. It carries a §2.3d disposition — *eager-metadata* — so the m48
  exhaustiveness gate discovers it; listed in §9.1. **On a `Varied` it answers with the
  CONTAINER's handle — the most-derived member handle §2.1 binds — NOT with the nominal
  member's**: §2.1 accepts members whose handles differ along one ancestry chain, so the
  most-derived handle may belong to a non-nominal member, and §6.4a(2a)'s predicate
  `graphed.context_of(select_mask) is graphed.context_of(record)` routinely takes `Varied`
  operands on both sides. *Eager-metadata* here means only that the answer is produced without
  recording. m48's §2.3d table anchor carries the discriminator: a container built from an
  ancestor-handled nominal member and a more-derived non-nominal member answers with the
  MORE-DERIVED handle.
  A wrapper attribute is the only sound carrier: two sibling contexts differing only in
  registered weights expose collections whose reads intern to the SAME node id, so a
  node-id-keyed context map cannot distinguish them, and `Provenance` is a frozen `(filename,
  lineno, function, source)` dataclass with no lineage channel. **Propagation is a chokepoint,
  not per-function work**: every frontend `Array` is constructed in `Session` at the
  `_array_cls` sites — `source`, `record_op`, `record_exchange`, `record_join`,
  `record_external` — the only `_array_cls` call sites in the repo. Those methods already
  receive the input `Array`s, so the merge rule is implemented ONCE there; gak functions and
  module verbs inherit it by construction, and the propagation gate below is the anti-drift gate
  over the ones that bypass `record_op` (e.g. tuple-returning wrappers that rebuild results).
  **ORIGINATION rule — a context STAMPS its own handle, overriding the merge result** (the merge
  rule alone cannot supply a derived context's handle: `Session.source` takes no `Array`, and a
  derived context's reads go through the same root wrapper carrying the parent's handle).
  Binding: **every `Array`/`Varied` a context produces — its own root wrapper and every read
  performed through it — carries THAT context's handle**, overriding whatever the input merge
  would yield; the merge rule below governs only ops whose inputs already carry handles.
  Frozen-anchored in m48.
  **Merge rule at the op, not at the fill**: inputs whose handles lie on ONE ancestry chain
  propagate the most-derived handle; handles on divergent branches are an error at that op
  naming both. Every *combining point* runs the same unification, and the fill is one of them
  (§6.1d): `Histogram.fill` is the first place independently derived handles meet — it collects
  args/weights/sample into ONE `inputs` list and records ONE External node (`graphed-histogram
  src/graphed_histogram/boost.py`). The op-level rule is *early* detection, not the sole raiser.
  **Drop rule**: an op with no contexted input yields a context-free result, and a subsequent
  fill mixing context-free with contexted inputs adopts the unified context (§6.1d); an op that
  silently *loses* a handle it had is a bug.
  **The propagation gate is a SEPARATE test from (c)'s classification gate, and it is scoped**:
  (c)'s gate is *metadata-only* — it reads a classification off each discovered function and
  never calls it — so it runs over the full public gak surface for free, while a propagation
  gate must CALL each function with a contexted `Array`, and a blanket call is impossible over
  the measured surface (payload-first verbs like `apply_correction`/`onnx_inference`, eager
  verbs returning Python objects, non-`Array` metadata returns, the refusing `join`, and verbs
  needing typed extra operands). Binding: **(1)** the classification gate of (c) covers the full
  public gak surface, metadata only; **(2)** the propagation gate dynamically enumerates only
  the *broadcast*, *container-traversing* and *tuple-returning* classes, and derives its
  **AUXILIARY** call arguments from **argument fixtures that live in `src` beside the
  classification** — a newly added function arrives with its classification AND its fixture and
  the frozen test stays untouched. **The CONTEXTED operand is owned by the FROZEN TEST, not by
  the fixture**: the frozen test constructs the context and substitutes its own contexted
  `Array` into the primary operand position (a fixture-supplied context-free primary would
  degrade the check to `None == None`); `src` fixtures supply only the auxiliary/typed operands
  the measured surface needs (`concatenate`'s second array, `unflatten`'s counts, `where`'s
  branches, `linear_fit`'s operands), and the gate asserts the result's handle is **NOT `None`
  AND IS the input's handle**. **For the CONTAINER-TRAVERSING class the fixture is bound as a
  TEMPLATE** (`gak.zip`'s mapping is its only array-bearing operand, so there is otherwise no
  position to substitute into): each `src` fixture declares a named
  **substitution SLOT** — a sentinel the frozen test replaces with its own contexted `Array`,
  *including inside a Mapping/Sequence argument* — and the gate asserts the substitution
  actually happened (the handle-bearing input of the produced call IS the test's own contexted
  `Array`) before asserting the result's handle is not `None` and equals it. **Each slot
  DECLARES the operand KIND it needs, and the frozen test owns one contexted `Array` of each
  kind**: graphed type-checks the primary at RECORD time through the backend's `op_form`, so one
  test-owned array cannot serve every function. Each `src` fixture's slot names its operand KIND
  (flat numeric / jagged numeric / record / boolean mask / option type); the frozen test owns
  one contexted `Array` per kind, ALL read through the SAME context, and substitutes the kind
  the slot names. The type requirement — a property of the function — stays beside its
  classification in `src` (the self-repairing rule). **The KIND VOCABULARY is frozen at m48, and
  the trap is recorded**: a later gak function whose primary operand falls outside these kinds
  arrives with classification and fixture in `src` as designed, but exercising it would require
  editing the frozen test — a Test Dispute. Nothing in m48–m51 trips it. **(3)** the
  *eager-metadata* and *refusing* classes are EXEMPT by classification, not by omission, and the
  gate asserts the exemption set is exactly those two classes, **plus a MEMBERSHIP floor on
  those two classes** (classification is implementer-editable `src`, so without a membership
  floor a hard-to-implement member could be re-classified into an exempt class and stay green).
  Binding floor: **`gak.join` IS IN the *refusing* class and the refusing COUNT is ≥ the
  freeze-time count** — containment plus a monotone count, never an exact set; `join` is the
  only boundary verb among gak's public functions, so the freeze-time operand is `{gak.join}`.
  Every *eager-metadata* member's return annotation is non-`Array`, and the count of
  *broadcast*-classified functions is at least the freeze-time count. **(4)** the `Array` public
  surface of (a) is gated the same way, dynamically enumerated **and resolved on the CLASS per
  (a)'s rule**, with its OWN one-line floor: on the `Array` surface the refusing class is
  `{repartition}` and the broadcast count is ≥ the freeze-time count. Both gates carry (c)'s
  non-vacuity floor.
  Broadcast recording happens while the *user's* frame is on the stack, so `capture()`
  attributes each varied node to the user's own op line with no provenance copying
  (`provenance.py` skips graphed frames).

- **§2.4 (Combination rule — label-aligned union by point projection; implicit cross products ONLY where the graph carries the dependency.)** When an
  operation combines `Varied` inputs — including a `Varied` combined with one derived from it
  (`jets[jets.pt > 25]` is the canonical case) — the result's labels are the **union**, and for
  each label L every container contributes **its own member for L when present, else its
  `"nominal"` member**. **The union's ORDER is bound** (§3.2 determinism and the §6.1b/`_GroupReduce`
  positional layout in `boost.py` both depend on it): the first operand's order, then labels
  new to the second operand in its own order, `"nominal"` always first. Within a universe L, all
  uses of varied quantities are therefore coherent (RDF's whole-cone-substitution semantic).
  Because a label's point is fixed at registration and resolution only PROJECTS it, cross products
  never arise implicitly — **except where a member's graph GENUINELY CONSUMES another nuisance's
  varied nodes: such a dependent joint universe is minted AUTOMATICALLY (m53,
  `systematics-design/dependency-fanout-design.md`), because the physics cross-term already exists in
  the graph and dropping it would be silent.** Consumption is decided on nodes, not on the
  nuisance's kind (m56, `both-kind-fanout-plan.md`): a foreign coordinate on a member is
  *composition* — excluded from the fan-out — only when its nuisance is a family in the ambient
  tag map AND the member's node at that label reads a lineage factor's varied member there (the
  factor's two-level member at the label where it differs from the factor's nominal); every other
  foreign coordinate, including one reached through objects shifted by a nuisance that is ALSO a
  weight (the b-tag SF's jes-correlated table by name identity over jes-shifted jets), is a
  dependency and mints its joints, whichever registration comes first. At a fill combining shift-varied kinematics with a
  stacked weight `Varied`, a label whose point names no weight axis fills with the central weight *as
  evaluated in that universe*, and one whose point names no shift axis fills with nominal kinematics —
  the corpus reference semantics (`systematics.py`). **Independent members (no such consumption) stay
  union.** A label whose point names both is one the graph minted as a dependent joint or the analyst
  named with `points=` (m53 inverts `points=` to PRUNE the automatic fanout; the one-at-a-time
  exclusion convention that lit §pythonic-analyses documents is reached with `composes_as_union=True`,
  and is no longer the default).
- **§2.5 (Validation over convention.)** Silent-drop failure modes from the survey become errors
  or diagnostics: unknown label on `graphed.universe(x, label)` → KeyError listing valid labels;
  form-incompatible or cross-Session/cross-source member → construction-time error naming the
  label; `vary()` registers each container with its Session (weak reference), and `compile_ir`
  diagnostics report any registered label that reaches no marked output (DCE already prunes the
  work; the diagnostic prevents the mkShapesRDF silent-cost case).
  **The channel is named, and its spelling is pinned at m48 freeze.** Binding: the report is an
  **additive `CompiledGraph` field** (a sorted tuple of unreached labels, empty when every
  registered label reaches an output) **or an equivalent read-only accessor over the same
  compile**; if it lands on `CompiledGraph`, note that m48's §7.2 schema-absence anchor is worded
  over the `ExecResult`/`Plan`/monitor schemas, not over `CompiledGraph`. The registration
  mechanism ("each container registered with its Session, weak reference") is likewise an m48
  Implementation Target whose spelling is pinned at freeze; nothing in the anchors depends on it
  directly.
  **The §2.1 shift-after-weight ordering rule gets a diagnostic on the same CHANNEL but is
  DETECTED AT RECORD TIME, and it is an m49 target.** Detection cannot ride the compile-time walk
  the unreached-label diagnostic uses: for a context-borne registration — the only kind carrying an
  ambient weight — `_stamp` rebuilds the container after `register`, so the registry's weak
  reference is dead before compile, and no Session-retained object ever carries a COLLECTION name.
  Both operands are live at exactly one place, the shift `vary` call itself (`_vary_shift`,
  `context.py`): the ambient weight `ctx._weight` and the collection about to be replaced, read off
  the target context. Binding: **the weight form records `(factor family name, that factor's own
  member node ids)` on the Session BY VALUE** — the shape `register` already uses, and for the same
  reason — **and the shift form reports the families whose cone (§3.4's walk) reaches the replaced
  collection's node, paired with that collection's name.** The report is a SECOND additive
  `CompiledGraph` field, a sorted tuple of `(factor family, collection)` pairs, empty when the order
  is sound; the m48 scoping note above (the schema-absence anchor is worded over
  `ExecResult`/`Plan`/monitor, not `CompiledGraph`) governs it unchanged. Diagnostic, not an error:
  a weight that legitimately does not track the shift is a valid program.
  **It is session-HISTORY-scoped by construction, and that is settled**: a sound program and a
  violating one can compile to byte-identical artifacts (same IR, same correspondence map), so no
  filter at a shipping site can separate them — the report is the only channel that carries the
  ordering, and it names the pair. Nothing downstream may be asked to re-derive it.
- **§2.6 (The event context — systematics attach to `events`, functionally; owner semantics,
  respun functional per collaborator feedback.)** The primary user idiom
  is not loose `Varied` threading but an **event context**: a frontend wrapper over the root
  event record carrying (a) the collections and (b) an **ambient event-weight registry** (itself
  a `Varied` of accumulated M29 factors). Pure frontend sugar over §§2.1–2.5 — no IR change,
  §3.1 intact. Binding, in the functional form:
  (a) **The context reserves NO NAMES.** Attribute access, and `[]` **with a string (or list of
  strings)**, resolve ONLY tree content (collections/branches); `[]` **with an `Array`/`Varied`
  mask derives a new context** (§2.6c — `sel = events[gak.num(jets) >= 4]`, the sketch's central
  idiom), mirroring `Array.__getitem__`'s own mask-vs-field split.
  **A `slice` or `int` subscript on a CONTEXT is REFUSED**, naming the supported forms (a
  slice-derived context is not scoped in m48–m51). Every graphed operation on a context is a
  module function
  (`graphed.vary`, `graphed.labels`, `graphed.universe`, `graphed.nominal`, `graphed.weight`,
  `graphed.selection`, and `graphed.variations` — §9.1; `graphed.variations` lands in m50,
  `graphed.selection` in m51, the rest in m48): branch names are analysis-controlled and
  open-ended, so any reserved attribute (`events.weights`, `events.vary`) is a latent collision
  with real tree content.
  (b) **Contexts are immutable; `graphed.vary` returns a NEW context** (§2.1 overloads b/c). The
  shift form replaces the named collections with `Varied` members (thereafter
  `events.<Collection>` is a `Varied` and §2.3 broadcast carries it; repeated calls stack,
  §2.1); the weight form registers the factor into the returned context's ambient weight (M29
  factor-list semantics; explicit tags in v1 — auto-symmetric derivation from a lone `up` is
  Phase 2, §11). Each returned context links to its parent: variation history is **object
  lineage** — the provenance handle the collaborators asked for; no hidden mutable registry.
  **CONTEXT HANDLE IDENTITY is bound here, once** — three binding rules compare handles
  (§2.3e's divergence error when input handles are not on ONE ancestry chain, §6.1d(A)'s
  `graphed.unify_contexts` raising the same error, and §6.4a(2a)'s literal object-identity
  comparison `graphed.context_of(select_mask) is graphed.context_of(record)`):
  **PURE DERIVATIONS ARE CANONICAL.** `graphed.nominal(c)`,
  `graphed.universe(c, L)` and `c[mask]` for the same mask (identical per-label node ids) return
  the **SAME context object**, memoised on the parent (fresh-object-per-call would make two reads
  of one universe siblings and falsely trip §2.3e's divergence rule) — while `graphed.vary`
  ALWAYS returns a fresh one (each call registers different content; §2.1's "always returns a NEW
  object" is untouched). m48's op-level divergence anchor gains the positive control that two
  separate `graphed.nominal(sel)` reads UNIFY instead of raising.
  (c) **Scoping is lineage.** A fill sees exactly the registrations present on the context its
  inputs were read from (§6.1d) — the fill-time-snapshot rule re-bound as immutability: a fill
  from a pre-`vary` context is unaffected by later `vary` calls *by construction*.
  **A read performed THROUGH a derived context yields THAT context's row space** — the central
  rule of the whole idiom, against which §6.1d's link kind (1), §6.4a's row-space predicates and
  m48's TWO re-indexing anchors (the §2.6c ambient-registry one and the §6.1d fill-time
  ancestor-VALUE one) are defined:
  `sel.Jet` IS `events.Jet` re-indexed by `sel`'s derivation mask, label-aligned per §2.4 when
  that mask is `Varied` — the same operation the ambient rule below performs, applied to values.
  Derived contexts (`events[mask]`) **inherit the ambient registry with every member RE-INDEXED
  by the derivation mask, label-aligned per §2.4**. Selection-scoped weights are `vary` on
  the derived context (`sel = graphed.vary(sel, "btag", …, is_weight=True, …)` — the replacement
  for the exemplars' per-channel `deepcopy(Weights)`); the parent is never touched. Inputs whose
  contexts lie on ONE ancestry chain unify to the most-derived one; contexts on divergent
  branches are the §6.1d hard error (raised at the op, §2.3e).
  **Varied contexts (per-label row sets) are first-class.** When the derivation mask is itself
  `Varied` — the central idiom of the sketch below, `sel = events[gak.num(jets) >= 4]` with a
  JES-varied `jets` — the derived context's ROW SET DIFFERS PER LABEL. Binding: its collections
  READ as `Varied` (§2.4-aligned per label) — **an implicit property of the derivation, NOT a
  shift-form registration, so §2.2's `graphed.labels` term (b) does not count them (term (b)'s
  own exclusion at its definition site); the mask's own labels enter through term (c)**;
  `graphed.labels(ctx)` **INCLUDES** the mask's labels — the full answer is §2.2's union
  (ambient-weight labels ∪ varied-collection labels ∪ the derivation mask's labels);
  re-indexing happens per label
  (each label's ambient member is re-indexed by THAT label's mask, nominal's by nominal's);
  `graphed.vary(ctx, …, is_weight=True)` on it stacks per §2.1 (a new weight label's member is
  the provided value's central universe, each inherited shift label keeps its own); fills from it
  are label-aligned per §2.4; and §6.4a's OR-of-selections is exactly the union of these
  per-label row sets.
  (d) **Data contexts refuse BOTH forms.** `is_weight=True` on a data context is a guard error,
  and a **shift-form `vary` on a data context is likewise refused**, with an error naming the
  variation (accepting it and dropping its labels at the fill would be the §2.5 silent-drop).
  "Data fills nominal-only" is therefore structural **for every context-borne registration** —
  **scoped**: the loose primitive (§2.1a) stays public, so
  `graphed.vary(data_events.Jet, "jes", up=…, down=…)` is still expressible, its result indexes
  plain `Array`s per §2.3b, and §6.1d's union carries its labels into the fill; v1 does not bind
  that case. What makes a context a data context is an explicit constructor flag
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
  sjets = sel.Jet[sel.Jet.pt > 25]                            # the corpus SF is on the pt-CUT jets
  sel  = graphed.vary(sel, "btag", btag_sf(sjets),            # selection-scoped weight
                      is_weight=True,
                      up=btag_sf(sjets, "up"), down=btag_sf(sjets, "down"))
  h.fill(sel.Jet.pt)                                          # per-OBJECT fill: the value stays
                                                              # UNFLATTENED so the ambient event
                                                              # weight can broadcast against it
                                                              # (§6.1d); the evaluator flattens
                                                              # both (boost.py)
  ```
  **The following spellings in that sketch are measured, not assumed:**
  (i) **there is no tuple subscript on the awkward-idiom `Array`** — `Array.__getitem__` accepts
  an `Array` mask, `str`, `list[str]`, `slice` or `int` and raises `TypeError` otherwise; tuple
  subscripts exist only on the numpy idiom, and no gak function takes an arbitrary inner index.
  The expressible form is the masked one above — `gak.firsts(w[gak.local_index(w) == 1])`. (A
  first-class inner-index verb would be a gak addition; it is NOT scoped in m48–m51.)
  (ii) **`Histogram.fill` is positional** — `fill(self, *args: Array, weight=…, sample=…,
  threads=…)` (`graphed-histogram src/graphed_histogram/boost.py`), so `h.fill(pt=…)` is
  an unexpected keyword; named-axis kwarg fills exist only in the `hist.graphed` fork (cba
  §histogram §3), which is not in m48's repo scope.
  (iii) **the b-tag SF's ARGUMENT is the pt-CUT jets, not `sel.Jet`** — the corpus reference
  computes the SF on the pt-cut jets and `_btag_weight` products a per-jet SF over `axis=1`
  (`graphed-corpus src/graphed_corpus/analyses/systematics.py`), so sub-25 GeV jets change the
  weight and `btag_sf(sel.Jet)` misses the stored references. `sel.Jet[sel.Jet.pt > 25]` is the
  corpus-faithful spelling (the object cut and the event re-index commute), and it is read
  THROUGH `sel`, so it satisfies §2.1(b)'s row-space requirement by construction. m48's matrix
  anchor repeats the note alongside the existing `gak.full_like` / pre-fill-rounding notes.
  The neutral context *mechanism* (lineage, ambient weight, fill-inference seam) lives in
  `graphed` proper; the nanoevents-flavored constructor is awkward-idiom and lives in
  `graphed.awkward` (factorization rule preserved). The loose `graphed.vary` on Arrays (§2.1a)
  remains public — the context is built on it, not beside it.

## §3 IR and optimizer treatment

- **§3.1 (No new NodeKey.)** No Rust IR variant, no serialize tag, and **no optimizer SEMANTICS
  change** is added for variations. The ONE optimizer-adjacent addition in m48–m51 is §8.2(i)'s
  m49 record→reduced correspondence, which retains and composes the re-indexings each reduction
  pass already computes and then throws away: read-only, no new `NodeKey`, no serialize tag, no
  rewrite arm, no change to what the reducer produces, and DCE/CSE stay outside the engine
  (cross-referenced from §8.2, which binds the `RewriteEngine` signature that change requires).
  The varied universes are ordinary nodes; sharing
  is interning (`src/store.rs`); the m4 frozen scaling contract
  (`tests/frozen/core/m4/test_systematics.py`) continues to bind unchanged. Any future
  first-class node (introspection-driven) is Phase 2 and follows the full M40 checklist
  (cba §ir-rust §1).
- **§3.2 (Determinism.)** Expansion order is deterministic: labels in `graphed.labels` order,
  recording per §2.3. Two-run byte-identical compilation of a variation-expanded graph is a frozen
  m48 anchor (§10) in the strong R22.3 form (fresh processes, differing `PYTHONHASHSEED`).
- **§3.3 (Anti-quadratic guard gains a variation topology — in a NEW frozen file.)** A new frozen
  benchmark (`tests/frozen/core/m49/…`, replicating the `test_benchmark.py` pattern; **the m4
  files are untouched** — frozen tests are read-only, §B.6) pins the variation shape. **The
  builder is bound explicitly, because the pinned integers depend on it**: source → a shared
  prefix of D ops → per universe {one varied fork op, K chain ops, **exactly one terminating
  reduction node**}, every universe's reduction separately marked as an output, N counting nominal
  (the m4 `_systematics` builder funnels all variations into ONE output and would make the
  assertion vacuous; omitting the terminating reduction changes the correct answer to
  `reduced_nodes == N + 2` — and a fill IS a reduction, so the with-reduction shape is the
  realistic one). N ∈ {16, 32, 64, 128}. Under that topology (D=500, K=50) the exact reduced
  shape is `stages == N + 1` and `reduced_nodes == 2N + 2` (cba §optimizer §2).
  Linear-growth bound: **time(128)/time(16) < 16.0** — m4's threshold STYLE at m4's headroom
  RATIO rather than its literal 24.0: this topology's node count grows only 5.37× while N grows
  8× (measured time ratio 5.64, cba §optimizer §2), so 16.0 keeps ≈2.8× headroom over the
  measurement and still fails a node-quadratic reducer, where the copied 24.0 barely would.
  (The equivalent self-scaling form `time(128)/time(16) < 3 × nodes(128)/nodes(16)` is
  buildable — `reachable_nodes` is in `reduce()`'s returned report — if a future revision prefers
  it to a literal.) Replicate the m4 noise floor (`base = max(times[SIZES[0]], 1e-4)`) and
  best-of-N timing (`test_benchmark.py`). **This is the ONE frozen wall-clock gate in m48–m51**,
  a deliberate, named carve-out to R0.10a discharged by the project plan's M4 benchmark mandate
  and its frozen precedent `tests/frozen/core/m4/test_benchmark.py`; every other performance
  claim in this plan (§6.2 axis scaling, §6.4c compression) is an R0.11 implementer-report
  measurement.
- **§3.4 (Impact-set API.)** A read-only frontend helper reports, per label, the **reachability
  difference** `reachable(label's outputs) − reachable(nominal outputs)` computed via
  `session.walk`. It is a **read-only `graphed` module verb over the per-label output CONTAINERS —
  `Sequence[Varied] | Mapping[str, Sequence[Array]]`** (the labelled analogue of `read_columns`'
  first operand), the mapping being what §9.1's `fill_nodes_by_label(h) -> dict[str, Array]`
  returns on a real varied histogram program and what §4.3's optional cross-check names as its
  operand. **The two forms do not mix, and the rejection is bound for BOTH m49 verbs** (§5.3 takes
  the same operand): a sequence must be all `Varied`, a mapping must map a label to a sequence of
  `Array`, and a `Varied` member must not itself be a `Varied` (§2.2 admits nested members but the
  per-label walk cannot resolve past one level). Anything else raises a `GraphedError` naming the
  offending element, rather than the `AttributeError` an unchecked operand produces today by
  reaching for `.session` on whatever it was handed. No `source_nid` parameter: the reachability
  difference over `session.walk` is
  source-agnostic, and a bare `Sequence[Array]` carries no label attribution. **The key set is the
  §2.4 UNION over the operand's containers, in §2.4's bound union order** (a mapping operand's own
  keys, in its order), and resolution is §2.4's rule, NOT the strict `graphed.universe`: a
  heterogeneous operand — a jes-varied kinematic beside a btag-varied weight, the corpus mainline —
  has containers that carry no member for a union label, and `universe` raises `KeyError` on
  exactly that case. The verb resolves each label's outputs by **`graphed.member_of(v, L)`** (the
  container's own member for L, else its `"nominal"` one) and walks from there — returning
  `{label: tuple[int, ...]}`: per label, that label's SORTED RECORD-time node ids
  (`tuple(sorted(...))` is the house shape, `python/graphed/projection.py`) — **listed in §9.1,
  exact spelling pinned at m49 freeze**. It is **NOT an id watermark** (interleaved broadcast
  recording makes watermark bracketing order-dependent and wrong for labels sharing derived
  nodes). The result is independent of expansion order; a node shared by `jes_up` and `jes_down`
  but not nominal appears in **both** impact sets. This is the RDF `RVariationsDescription`
  analogue and the §5.3 projection-stats input; it is frozen-anchored in m49 (§10).

## §4 Weight-path lowering

- **§4.1** A weight variation is a `Varied` whose members are per-event weight Arrays (any source:
  arbitrary expressions, or a correctionlib `External` evaluated per label). The **canonical
  correctionlib form varies the existing `systematic` category parameter** of ONE payload
  (`preserve/m9/agc.py` fixture precedent): same `content_hash`, N parameterizations — the
  payload is never duplicated (§A.3.1 reproducibility). Weight variations routinely require a
  **per-dataset scalar normalization** — the sum-of-weights rescaling (`sow/sow_renormUp`, with
  per-sample LHE-index branching) appears in both eras of the confirmed exemplar
  (lit §ewkcoffea-confirmed). The binding v1 form is **`gak.full_like(<an existing per-event
  Array>, sf)`** — a real recorded graph op producing a constant-valued Array shaped like an
  existing one (`python/graphed/awkward/functions.py`; parity-pinned by
  `tests/frozen/awkward/m24/test_interface_parity.py`) — or ordinary arithmetic on such an Array.
  The donor-free `graphed.numpy` creation ops (`full`/`ones`/`zeros`/`empty`/`arange`/`linspace`,
  `python/graphed/numpy/creation.py`) cannot serve: each records an eager fixed-shape in-memory
  Source, and a plan built through `aggregate_plan` binds exactly ONE source
  (`python/graphed/aggregate.py`), so a second source makes `evaluate_ir` raise
  `"no data bound for source"` (`python/graphed/execute.py`). The gap — a constant/scalar
  broadcast helper needing no donor and no second source — is parked in §11.
- **§4.2** Fills accept a `Varied` entry in the M29 `weight=[...]` factor list (`boost.py`);
  lowering emits the nominal fill node + one sibling fill node per label under the §2.4 rule,
  differing only in the varied input ids — everything upstream interns. All siblings join the
  **same group plan**; the single-pass property is frozen-witnessed on the corpus run itself in
  m48 (§10), not only on a toy graph. With the §2.6 event context, weight variations typically
  reach fills **ambiently** (registered once via `graphed.vary(events, …, is_weight=True)`,
  applied per §6.1d); the explicit factor-list form remains the primitive underneath and stays
  public.
- **§4.3** Weight variations MUST NOT change selection. The frozen m48 anchor is **structural**,
  not only behavioral (equal counts is a tautology under §3's expansion — the selection nodes are
  the same interned ids by construction, an R0.10 trap): **the selection cone's node ids MUST be
  identical across all weight labels**, and the m48 anchor quotes that sentence verbatim. Two
  superficially plausible predicates are rejected: "the §3.4 impact set contains no node outside
  the fill's weight-input cone" (false for a correct implementation — a label's sibling fill node
  always lands in the impact set, downstream of that cone), and the containment form
  "`reachable(selection_mask)` ⊆ each label's `reachable(fill_node[label])`, intersection
  constant across labels" (holds by construction in any program that fills selected data, and
  passes a `mask_L = mask & g_L` implementation). In a weight-only program the selection is a
  plain unvaried `Array`, so the assertion has content only in the per-label form; **the
  EXTRACTION mechanism is bound too**: per label, take the fill node's recorded `inputs` from the
  store and assert the **NON-WEIGHT prefix** (`store.nodes()[fill_id]["inputs"][:n_axes]`) is
  IDENTICAL to nominal's for every label — identical node ids ⇒ identical cones by interning
  (`src/store.rs`) — where the `n_axes` split is the recorded `params["n_axes"]` (`boost.py`; the
  m29 frozen precedent `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py` already
  counts that layout). A reachability cross-check MAY ride along, in the discriminating shape
  only: `reachable(fill[L]) − reachable(weight_input[L]) − {fill[L]}` identical across labels;
  either form fails a `mask_L = mask & g_L` implementation. **`session.walk` takes an `Array`,
  not a node id** (`root = array.node_id` in `python/graphed/session.py`), so the test wraps each
  id as `Array(session, nid)` (`Array` is exported from `graphed`). `fill_node[label]` needs a
  **public per-label channel that must be BUILT, and is bound in §9.1**: today
  `Histogram.fill_nodes()` (`graphed-histogram src/graphed_histogram/boost.py`) returns a bare
  `list[Array]` in staged-fill order with no label attribution, and no private route reaches a
  label correspondence that exists nowhere; §9.1 pins the accessor's spelling at m48 freeze.
  Because the operands come from a fill, **this anchor sits in `graphed-histogram`'s half of the
  m48 split** (§10). An equivalent public impact-set cross-check MAY ride along: `impact(L)`
  minus L's own output node is disjoint from `reachable(selection_mask)`. The m05 equal-counts
  check rides along as a sanity assertion.

## §5 Shift-path lowering

- **§5.1** A shift variation is a `Varied` at a kinematic quantity (column or record), created
  **before selection** — the corpus applies JES at the jets record before the pt cut
  (`systematics.py`) and the m9 AGC fixture shifts `Jet.pt` before its jet mask (`agc.py`);
  broadcast (§2.3) re-records the selection/observable cone per label; interning shares everything
  else. The *defining* behavior is per-universe re-derivation of the selection (cutflow
  divergence). **The general shift contract asserts NO monotonicity or ordering across labels**
  (owner decision): the `jes_up > nominal > jes_down` ordering is a property of the corpus's
  monotone-scale JES *fixture* and MUST stay scoped to it — a JER-SF re-smearing shift migrates
  events in both directions (§5.5), and any suite or API language implying shifts order is a
  test-authoring error.
- **§5.2 (Witnesses that sharing engaged — R0.10.)** Mechanism witnesses, not just results;
  (a) and (c) are m49's, (b) is applied at m48, m49 and m51:
  (a) **Arena-delta witness with a literal expected integer**, built through the public
  `graphed.vary` surface on the §3.3 topology (the raw-`GraphStore` replication §3.3 describes
  witnesses only `GraphStore::intern`, already frozen at m1/m4). One universe = {1 varied fork op,
  K=50 chain ops, 1 terminating reduction}, so N=1→2 adds exactly `K + 2 = 52` nodes; the
  terminating reduction is load-bearing (without it the delta is `K + 1`), so the literal travels
  with the builder, and a self-derived `delta == len(cone)` comparison is tautological. The delta
  discriminates that no per-universe COPY enters the arena — labels are out of node identity
  (§1.2) and interning is engaged through the public `vary` path; prefix re-recording interns to
  the same ids (Δ = 0) and is caught by §5.2b, not here. **SPAN and ORACLE:** (1) SPAN —
  `Session.node_count()` after building the COMPLETE N=1 program versus after the COMPLETE N=2
  program in the SAME `Session` (bracketing the `vary` call alone measures only the fork member
  under record-time expansion, Part I §3); (2) ORACLE — the same second universe hand-built
  WITHOUT `vary` in a separate `Session`, whose own node-count delta supplies the expected
  integer; this independent construction is runnable at freeze time and needs no frontend `vary`.
  `K + 2 = 52` is the raw-builder number and MUST NOT be assumed to carry over unchecked. Labels
  structurally identical to a prior label dedup to Δ = 0 by §1.2 — witnessed in the m48 §1.2
  label-out-of-identity anchor (§10), not here.
  (b) **Single-read witness bound to the reference-matrix run itself**: a read-counting
  partitioned source (m23 pattern) asserts `part_reads == n_partitions` — not
  `n_partitions × n_labels` — on the SAME Session/plan that reproduces the corpus references, so
  a per-variation re-run loop cannot pass. **The shape is applied to every anchored reference or
  write run**: m48's weight-only matrix and m49's full 15-reference matrix, both in
  `graphed-histogram` where m48's vendored references live (§10/m48, §10/m49(i)), and m51's
  augmented write run (§6.4).
  (c) **Reduced-stage shape — the §3.3 SHAPE, built through `graphed.vary`**: the shared prefix
  appears in exactly ONE stage, and the total stage count equals an **ORACLE**, not a literal —
  the same N-universe topology hand-built WITHOUT `vary` in a separate `Session`, reduced, its
  stage count read off (the independent construction §5.2a binds; §3.3's raw-builder literals,
  e.g. N=16 → 17 stages, are the expectation for the oracle itself and MUST NOT be asserted
  directly of the `vary`-built program). It does NOT ride the §3.3 benchmark fixture (a raw
  `graphed.core.GraphStore` construction); it is a frontend, `vary`-built program in `graphed`'s
  `tests/frozen/frontend/m49` per §10/m49 — the same fixture §5.2a needs — and
  `tests/frozen/core/m49` keeps the raw-`GraphStore` scaling benchmark only.
- **§5.3 (Projection.)** Column projection is the union over all requested outputs — correct today
  with zero changes (`read_columns` takes `Sequence[Array]`, `projection.py`); m49 pins a test
  where a shift needs an extra column and the union grows by exactly that field. **The fixture is
  FLAT** (branch-per-column, `Jet_pt`/`Jet_eta`/`Muon_pt`) and the shift's extra column is a
  distinct TOP-LEVEL field, `Jet_eta` (on that shape: `('Jet_pt',)` → `('Jet_eta','Jet_pt')`):
  `read_columns` reports only fields read directly off the source node (the `reads_source` check
  in `python/graphed/projection.py`), so a nested-record fixture cannot discriminate the union
  growth. Buffer-level projection is not what §5.3 binds.
  Per-label projection stats make the read-width cost of a shift visible, anchored in the same
  m49 test (§3.4's anchor covers impact sets, not read widths): the test asserts the stats report
  the shifted label's extra column. **The surface**: a read-only `graphed` module verb over the
  per-label output CONTAINERS — `Sequence[Varied] | Mapping[str, Sequence[Array]]` (§3.4; the
  labelled mapping is what §9.1's fill-node accessor returns, and a weight-borne shift column is
  read at the per-label FILL node) — plus `read_columns`' own `source_nid`, returning
  `{label: tuple[str, ...] | None}`: per label, that label's SORTED read set, computed by applying
  `read_columns` to each label's members — **`graphed.member_of(v, L)` for a `Varied` operand**
  (§3.4's key set and §2.4 resolution rule, verbatim), the mapping's own entry for a labelled
  mapping. Listed in §9.1,
  exact spelling pinned at m49 freeze. The `| None` is live semantics, not defensive typing:
  `read_columns` returns `None` to mean "read every column" (whole-record consumption or a bare
  source read), the inverse of what `()` would say. The m49 anchor carries a conservative label —
  **a whole-record consumer applied directly to the source, spelled `ev.map(f)`**; the plain
  elementwise spelling is ill-typed against both shipping backends on the flat record fixture this
  clause mandates, which reject a record operand rather than recording a conservative read.
  **The conservative label lives in the SAME varied program as the growth labels**, because the
  two halves read differently: `read_columns`' union over the container collapses to `None` once
  any member is conservative, while the stats verb answers PER LABEL and does not collapse. So the
  stats assertions (growth on the shifted label, `None` on the conservative one) and the collapse
  of the plain union all ride one fixture, and only the plain `read_columns` union-GROWTH
  assertion — the one the collapse would make vacuous — needs its own program or output set.
  The union-growth half MAY be restated per label through the stats verb, order-insensitively:
  `set(stats["jes_up"]) - set(stats["nominal"]) == {"Jet_eta"}` AND
  `set(stats["nominal"]) - set(stats["jes_up"]) == set()` (the second conjunct keeps it from
  degenerating to containment). Plain concatenation — `stats["nominal"] + ("Jet_eta",)` — is RED,
  because both returns are SORTED and `Jet_eta` sorts first;
  `stats["jes_up"] == tuple(sorted(stats["nominal"] + ("Jet_eta",)))` is the acceptable
  concatenation form.
  Per-variation partition-level projection splitting is Phase 2.
- **§5.4 (Boundary restriction, explicit.)** v1 REFUSES a `Varied` OPERAND to a boundary or plan
  verb — the disposition table's `join`/`repartition`/`pack_key`/`shuffle_plan`/`join_plan`
  (§2.3d) — because the m39/m40 plan builders are single-boundary (`shuffle.py`): they take one
  output and pick one join/exchange node out of the store, so a cone-crossing variation compiles
  to a silent miscompilation, which is worse than refusal. **The refusal class is `GraphedError`**,
  the class m48's frozen disposition anchors already assert (§2.3d splits the table by contract for
  exactly this reason; `GraphedError` is unrelated to `NotImplementedError`). What m49 freezes is
  the MESSAGE shape, and it is worded over what the site actually knows: **the refusing VERB and
  the offending container's labels** — there is no boundary NODE at an operand check, and the
  container carries N labels, not one. The refusal test carries a **positive control**: a variation
  entirely *downstream* of a Join/Exchange compiles and produces correct results per universe (a
  blanket "Varied near Join raises" must fail the suite); its route is `Session.materialize` per
  universe, the house route of the m40 join fixtures, not a plan builder. Generalizing the builders
  is named Phase 2 (§11).
- **§5.5 (Stochastic shifts — JER-SF re-smearing is first-class; determinism still binds.)** A
  shift variation MAY be stochastic (MC jet re-smearing under a jet-energy-resolution scale
  factor). Two binding rules, both grounded in coffea's implementation (lit §coffea-sys):
  (a) **Randomness MUST be a deterministic pure function of PER-ROW event content, and the seeding
  rule is bound: the draw for a row is a pure function of THAT ROW's own content**, so the same row
  draws the same value in every partitioning. Global RNG state, wall-clock, per-run and
  **per-partition** seeds are all forbidden — the R0.4/R12 determinism gate applies to varied
  graphs unchanged. The coffea precedent (`rand_gauss`, `jetmet_tools/CorrectedJetsFactory.py`) is
  cited for the SHAPE of the computation (§5.5b's one shared draw, SF-varied per label) and is a
  **counterexample on the seeding rule, not a model for it**: it seeds PCG64 from the first and
  last elements of the array SLICE it is handed and then draws positionally from that stream, which
  is a per-partition seed and measurably fails the partition-invariance witness below. No graphed
  primitive draws per-row content-seeded values (`graphed.numpy.random` seeds from
  `(seed, draw-counter)`), so the draw is an opaque `apply`/`External` (§5.5b's shared node). The
  observable consequence is **PARTITION INVARIANCE**, and that is what the m49 witness
  asserts: the same
  event set at two different `steps_per_file` values yields byte-identical per-label results (a
  per-partition constant seed passes every other listed witness yet fails this one). The COMPARED
  QUANTITY is bound: changing `steps_per_file` regroups float additions in the combine tree, so a
  correct implementation can differ in the last ulp of an aggregated float — the witness compares
  **partition-local objects that concatenate deterministically** — the per-event/per-object
  SMEARED VALUES and the per-label selection MASKS — or an unweighted integer-storage count
  histogram; never a weighted float histogram.
  (b) **One draw, all universes**: the random vector is drawn once and shared — coffea's
  `jer_smear` takes a single `jet_resolution_rand_gauss` while only the SF column varies per label
  — so under `vary` the draw node lives in the shared prefix and interns once (§3).
  **The fixture's construction is bound too, because bidirectional migration does not fall out of
  "use the JER formula"**: the smear takes coffea's stochastic shape
  `1 + sqrt(max(SF² − 1, 0)) · g` with `g` the per-row content-seeded standard normal of (a), each
  varied label carries **SF ABOVE 1, at DIFFERENT magnitudes** — the `max(…, 0)` floor makes the
  factor exactly 1 for every row at any SF ≤ 1, so such a label equals nominal, its
  partition-invariance leg passes vacuously and it reds the bidirectional-migration witness by
  being a mutual subset of nominal; above 1 is also the physical range of a JER scale factor.
  The selection threshold sits inside the smeared
  distribution's bulk so a signed per-row `g` moves events across it in both directions. Nominal is
  unsmeared, so every varied mask differs from it both ways by construction. The m49 suite carries
  the fixture (§10); its witnesses assert bidirectional migration and run-to-run byte-identity,
  never ordering (§5.1).

## §6 Sinks: histogram fills (§6.1–§6.3) and variation-aware write-out (§6.4)

- **§6.1 (MVP shape: sibling fills, named results.)** `Histogram.fill` accepting `Varied` axis
  values and/or `Varied` weight factors lowers per §4.2/§5.1 under the §2.4 rule. Binding result
  and lowering shape:
  (a) **Per-output label sets** (scoped to the DEFAULT sibling-fill lowering; §6.2's opt-in axis
  mode has a third result shape, bound there). Each output's mapping carries exactly the union of
  labels reaching *that* output — `{output_name: {label: hist}}`, nominal always present; an
  output no variation reaches returns a bare `hist` (NOT `{"nominal": hist}`), so unvaried
  programs see today's shapes unchanged. Absent labels are absent, never silently duplicated from
  nominal.
  This is the shape of the UNPACKED user-facing result, not of the plan's combined value. Binding:
  **the plan's combined value is the FLAT slot-keyed mapping §6.1c binds —
  `{(output, label) → bh.Histogram}` for a VARIED output in sibling mode,
  `{(output, None) → bh.Histogram}` for an axis-mode output — and `_add_groups` stays a
  homogeneous key-wise `+`** (`graphed-histogram src/graphed_histogram/boost.py`); all three key
  forms carry a plain `bh.Histogram` value. An output NO variation reaches keeps today's BARE
  `output_name` key — a rule scoped to SIBLING-mode outputs: an axis-mode output's key is decided
  by the MODE, not the variation count (§6.1c), so an axis-mode output whose fills carry no
  variations is still keyed `(output, None)`. The bare-key rule preserves the already-frozen m23
  suite, which indexes `SequentialRunner().run(gh.plan({…})).value` by bare output name
  (`graphed-histogram tests/frozen/m23/test_group_plan.py`), with §10 binding the frozen m23
  artifacts unchanged. m48's §6.1a anchor carries a wholly-unvaried positive control.
  The `{output_name: hist | {label: hist}}` shape is produced by a bound **FRONTEND UNPACKER** —
  a named read-only `graphed_histogram` module verb over the executed plan value ALONE,
  **`graphed_histogram.unpack(value)`-shaped, exact spelling pinned at m48 freeze**, returning
  `dict[str, bh.Histogram | dict[str, bh.Histogram]]`. **It takes ONE argument, and the
  per-output shape is decided by the SLOT KEY FORM, not by a recorded MODE** (the layout is not
  reachable from the executed value). The key form is total and per output: a BARE `output_name`
  key → that output's bare `bh.Histogram`; a `(output, None)` key → the axis-mode output's bare
  variation-axis histogram (§6.2 i-bis); the `(output, label)` keys of one output →
  `{label: hist}`. A varied sibling output always carries ≥ 2 labels (§1.1; `"nominal"` is always
  present), so no output's shape is ambiguous, in a MIXED plan exactly as in a single-mode one.
  Listed in §9.1 with the other m48 accessors; m48's §6.1a anchor is worded over it.
  The declared result type at the unpack surface is the union
  `dict[str, bh.Histogram | dict[str, bh.Histogram]]`, paid for by bound narrowing helpers so
  callers do not hand-roll `isinstance`: `graphed.universe(result[name], label)` and
  `graphed.labels(result[name])` work uniformly on BOTH shapes (§2.2), a bare `hist` reading as
  the single label `"nominal"`.
  (b) **Structural fill-node arity** (sibling-mode only). A fill combining shift labels S and
  weight labels W records exactly `1 + |S| + |W|` fill nodes — never the product (frozen-counted
  via the staged-fill list, the §2.4 discriminator). **S and W are defined by LOWERING BEHAVIOUR,
  not by the "shift"/"weight" vocabulary**: `S` = the labels that require their own SIBLING fill
  node — those borne by any AXIS value **or by a `Varied` `sample=`** — and `W` = the labels
  borne only by weight factors (ambient or explicit), the ones §6.2's axis mode can collapse into
  an evaluator-side loop. `sample=` is a first-class fourth label source that m48 freezes as
  ACCEPTED/expanded; a label borne solely by `sample=` cannot ride the weight loop — the loop
  re-fills with different weights against a FIXED sample column — so it lowers as a sibling. Axis
  mode's arity is `1 + |S|` under the same definitions, stated in §6.2.
  The S/W split is observable only in AXIS mode (the sibling formula counts every label once
  whatever its class): **m50's equality anchor carries a label borne ONLY by a `Varied`
  `sample=`, asserting it lowers as a SIBLING (it counts in `S`) and that the axis-mode result
  still equals its sibling-fill decomposition. That fixture MUST use a `Mean` or `WeightedMean`
  STORAGE and per-label sample values that DIFFER** — boost_histogram 1.8.0 rejects `sample=` off
  those storages (`TypeError: Keyword(s) sample not expected`), and a storage that discards the
  sample makes the two classifications indistinguishable.
  (c) **The single-histogram `.plan()` path refuses varied fills**: `_SumFills` sums ALL staged
  fill nodes into one histogram and would silently merge universes; varied histograms route
  through the group-reduce path (`_GroupReduce` `{label: hist}` generalized to two-level keys),
  and **`.plan()` raises — pointing at the group API — on a `Histogram` that is VARIED *or* in
  §6.2 AXIS MODE**. **The two arms are INDEPENDENT tests**: the VARIED arm is decided
  frontend-side on whether the histogram carries any varied fill (m48) — it is not spec-visible,
  since a sibling-mode fill, varied or not, records `self._spec` verbatim (§1.2 keeps labels out
  of params/hashes; §6.3 pins the params key set) — and the AXIS-MODE arm by the spec comparison,
  a staged fill node whose spec differs from the `__init__`-time `self._spec` (m50). **The
  trigger is keyed on the MODE: the MODE, not the variation count, decides** (the rule §6.1a and
  §6.2 cite) — the axis-mode-with-NO-variations program is legal (the fourth output m50's anchor
  adds) and must not fall THROUGH the refusal, since §6.2(ii) declares the variation axis ALWAYS
  in axis mode (a 1-bin `{"nominal"}` axis there). **The refusal is GENERAL — sibling mode AND
  §6.2's axis mode**: `Histogram.plan` starts from `self._spec`
  (`_SumFills(self._spec)`/`_ZeroHist(self._spec)`), fixed in `__init__`, which under §6.2's
  fill-time declaration lacks the variation axis the fill results carry; §6.1c's per-slot spec —
  the fill node's, shipped at m48 — lives on `_GroupReduce`'s layout and does not reach
  `_SumFills`/`_ZeroHist`.
  Axis-mode programs therefore also route through the group API; no m50 anchor needs
  `Histogram.plan` to SUCCEED on an axis-mode histogram (m50's fourth output asserts it RAISES
  this refusal — the axis-mode arm's only coverage).
  **The reducer's LAYOUT shape SHIPPED at m48–m49 and is binding unchanged**: the two-level
  `SlotKey`, the per-slot output INDEX tuples, and the dedup rank that derives them are live code
  (`src/graphed_histogram/boost.py`), so nothing here is migration work and m50 must not be read as
  re-deriving it. Indices, not counts, because two marked fills intern to one node the moment §1.2's
  identical-label case arises (`mark_output` de-dups in `src/store.rs`; `evaluate_ir` returns one
  value per DISTINCT output), and the indices are
  **the rank of each marked record id in the DEDUPLICATED list of `fill_nodes` NODE IDS**
  (`list(dict.fromkeys(n.node_id for n in fill_nodes))` — `fill_nodes` is `list[Array]` and
  `Array` is unhashable, so the dedup runs over ids, never the Arrays), which matches
  `evaluate_ir`'s one-value-per-distinct-output list element for element; a raw index into the
  undeduplicated list overruns it. A shared node id therefore **replicates** into every slot that
  needs it. The operand is that
  list, NOT the compiled output list (post-reduction ids cannot be joined to the record ids
  `plan()` owns, §7.2) and NOT §7.2's `aggregate_plan` seam — that seam is m48's, for §7.2's merge
  refusal and m49's `variation_labels`; this layout needs nothing from it.
  **m50's ONLY delta to the layout is the axis-mode slot below**, plus §9.1's listing and
  §6.2(i-bis)'s recognition of the shape it produces.
  **The AXIS-MODE slot is bound here too — scoped to m50, with §6.2**: an axis-mode output
  contributes **exactly ONE slot, keyed `(output, None)`**, gathering ALL that output's fill-node
  indices; its per-slot value is the bare histogram carrying the variation axis (§6.2 i-bis), not
  a `{label: hist}` mapping, and m50's scaling anchor counts exactly these slots. That keying
  holds WHATEVER the output's label count — the MODE decides (§6.1a's bare-`output_name` rule is
  scoped to SIBLING-mode outputs). A plan MAY therefore carry sibling-mode and axis-mode outputs
  together. **The layout records NO per-output MODE**: the three key forms §6.1a binds — bare
  `output_name`, `(output, label)`, `(output, None)` — are disjoint and per OUTPUT, so the
  unpacker reads the shape off the keys in a MIXED plan exactly as in a single-mode one. A
  mixed-mode plan stays m50's anchored case for the unpacking and per-slot-spec behaviour it is
  the only program to exercise (§10/m50).
  **The COMBINE needs no branch**: under the bound keying every slot's value is a plain
  `bh.Histogram`, so `_add_groups`' key-wise `+` stays uniform per key; what varies per slot is
  the SPEC. **The layout's third element — the per-slot spec — is the FILL node's spec, not the
  histogram object's** (which is fixed in `__init__` and under §6.2's fill-time axis declaration
  would lack the `"variation"` axis, breaking `_GroupZero`'s `zero_of(spec)` and `_add_groups`'
  `+`). A sibling slot maps to ONE fill node, so "that fill node" is unambiguous there; for an
  AXIS-MODE slot, which gathers `1 + |S|` fill nodes, the slot spec is that of ANY of the
  gathered nodes and an implementation MAY assert they agree (§6.2(i)'s cross-fill agreement rule
  forces one spec per axis-mode histogram).
  (d) **Ambient-weight application (the §2.6 completion of register-then-forget).** `fill` reads
  its input Arrays' **context handle** (§2.3e — outside node identity; NOT `Provenance`, NOT
  `Session._provenance`/`sourcemap()`) and **auto-applies that context's ambient weight** (§2.6c
  — contexts are immutable, so *which context* fully determines *which registrations*). The
  fill's label set is the §2.4 union of value-borne labels, ambient-weight labels, explicit
  `weight=[...]` factor labels **and `sample=`-borne labels** — **computed on the inputs AFTER
  the lineage step below (unification + re-indexing/projection), not before it**, so a value
  reached across a universe/nominal PROJECTION link (kind (3)) contributes NO labels, having been
  projected to one label's unvaried member. Kinds (1) and (2) are label-preserving, so the order
  matters only for kind (3): on m48's anchored fixture
  `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` the unified context is `graphed.nominal(sel)`
  and the fill is UNVARIED — §6.1a's bare-`hist` shape, which m48's anchor asserts (its
  discriminator against a "labels kept, contents identical" implementation). A plain Jet-pT fill
  thus yields the jes/jer universes AND the pileup/PDF universes with zero per-fill bookkeeping
  (the owner's simultaneity requirement).
  **The union's ORDER is bound here too** (§2.4 binds only a binary combination; a fill is
  multi-way): the fill folds LEFT in a fixed operand order — **axis values in argument order,
  then the ambient weight, then explicit `weight=[...]` factors in list order, then `sample=`
  LAST** (§2.3d binds "`Histogram.fill` accepts `Varied`"; today's `fill` appends `sample` to the
  `inputs` list with no type check — the §2.3b unchecked-fall-through shape). An unbound order
  would let two conforming implementations produce different label orders for one program — a
  determinism-gate difference (§3.2) and a different `_GroupReduce` layout (§6.1c).
  `weight=[...]` *adds* factors; `unweighted=True` opts out (counts histograms). **Binding
  `unweighted=` semantics** (today's signature has no such parameter): it suppresses the AMBIENT
  weight **and** any explicit `weight=[…]` — a counts histogram carries no weight at all — and
  supplying both `unweighted=True` and a non-`None` `weight=` in ONE call is a **record-time
  error naming both** (§2.5). Consequence, stated: "suppress the AMBIENT weight but apply my own
  factor" is NOT expressible from a contexted program in v1 — every fill from a contexted value
  applies that context's ambient weight, and the only opt-out also kills the explicit factor;
  only an all-loose fill escapes. Parked in §11 (v2: a context-level detach or a narrower
  `unweighted=` that suppresses the AMBIENT factor only). A SUPPRESSED weight contributes NO
  labels — the label set is computed over the factors the fill ACTUALLY APPLIES — so a contexted
  `unweighted=True` fill whose only variation source is the ambient registry is UNVARIED and
  returns a BARE `hist` (§6.1a); m48's anchor ("counts equal to an unweighted eager reference")
  is worded over that shape.
  Inputs whose contexts sit on one ancestry chain unify to the **most-derived** context, **and
  every ancestor-context VALUE is re-indexed to the unified context across the intervening
  lineage links, label-aligned per §2.4**, stated PER LINK KIND. The three link kinds:
  **(1) mask-derivation link** (`ctx[mask]`, §2.6c) — re-index the ancestor value by THAT mask,
  label-aligned per §2.4 (each label's member by that label's mask, nominal's by nominal's);
  **(2) `graphed.vary` link** (§2.6b) — IDENTITY: the row space is unchanged, only registrations
  differ;
  **(3) universe/nominal projection link** (§2.2) — PROJECT each ancestor `Varied` value to that
  label's member (falling back to its `"nominal"` member per §2.4), yielding an unvaried value in
  the ancestor's row space, then continue with the links below it.
  Links compose in lineage order, parent-to-child. Unification alone is not enough: §2.6c
  re-indexes the ambient weight to the derived row count, so an un-re-indexed ancestor value
  (`h.fill(events.MET.pt, sel.MET.pt)`) would length-mismatch at execution with a message about
  the wrong thing. Re-indexing is the same operation §2.6c already binds for the ambient
  registry, applied to the values.
  **The cross-package surface is bound here, and it is an m48 IMPLEMENTATION TARGET in
  `graphed`** — `Histogram.fill` lives in `graphed-histogram`, a DIFFERENT distribution, and the
  lineage relation between two handles is not reachable through §9.1's other m48 accessors, so
  without it the fill could only reach `graphed`'s private context object — the very thing
  `context_of` (§2.3e) exists to prevent. Binding, both READ-ONLY, exact spellings pinned at m48
  freeze, listed in §9.1:
  **(A) `graphed.unify_contexts(*handles)`-shaped** — returns the most-derived handle when the
  non-`None` arguments lie on ONE ancestry chain (`None` when all are context-free; context-free
  arguments are ignored, the adopt rule below), and raises the §2.3e divergence error naming both
  contexts otherwise;
  **(B) `graphed.reindex_to(value, ctx)`-shaped** — returns `value` re-expressed in `ctx`'s row
  space by composing link kinds (1)-(3) in lineage order, label-aligned per §2.4; identity when
  `value` already carries `ctx`'s handle or carries none; raising when `value`'s handle is
  neither `ctx`'s nor an ancestor of it (the §2.1(b) direction rule).
  With those two, the fill's entire lineage step is `unify_contexts` over its inputs'
  `context_of`s followed by `reindex_to` per input, and `graphed-histogram` imports nothing
  private. §2.3d dispositions: `reindex_to` **broadcasts** — the result's labels are obtained by
  composing the links in LINEAGE ORDER (a mask-derivation link unions that mask's labels per
  §2.4, a `vary` link is the identity, a universe/nominal projection link RESETS the label set to
  empty), so across a path containing a kind-(3) link the result carries NO labels — the rule
  m48's bare-`hist` anchor above depends on; m48's lineage-seam anchor is split per link kind
  (§2.3d). **The ORDERING half is knowingly left UNANCHORED** (it diverges from an
  order-insensitive set expression only where a MASK link sits BELOW a PROJECTION link, which no
  m48–m51 anchor builds; m48's lineage-seam anchor is split per SINGLE kind and its fill fixtures
  cross one link each). `unify_contexts` takes context handles rather than `Array`s, so — like
  `evaluate_ir` (§2.3d) — it is outside the `Array`-consuming surface and carries NO disposition.
  m48 anchors them where each is observable: the `graphed` side asserts (A)'s most-derived answer
  plus its divergence refusal and (B)'s identity and wrong-direction refusals; the VALUE-level
  re-indexing stays in the fill-shaped `graphed-histogram` anchors that consume it.
  Both worked examples in this paragraph use SAME-GRANULARITY axis values, deliberately:
  re-indexing fixes an ancestor value's row COUNT, not its per-object STRUCTURE, the broadcast
  seam bound below is scoped to WEIGHT factors — nothing broadcasts one axis value against
  another — and mixed-granularity multi-axis fills are NOT scoped in m48–m51 (bh 1.8.0 requires
  equal lengths across axes).
  Contexts on **divergent branches are a hard error** naming both. **The fill raises it itself**:
  §2.3e's op-level rule is early detection, but the fill is a combining point no op precedes —
  the first place independent axis/weight/sample handles meet — so the fill runs the same
  most-derived unification and divergence check across all axis values, all explicit weight
  factors, **`sample=`**, and the winning context's ambient weight. `sample=` is included
  explicitly because nothing upstream checks it (appended to `inputs` unchecked today); an
  ancestor-context `sample=` is re-indexed like any other ancestor VALUE, and the broadcast seam
  stays scoped to weight factors, deliberately.
  Context-free (loose) inputs alongside contexted ones adopt the unified context **for LABEL
  ALIGNMENT only; their row space is NOT adjusted** (a loose value carries no handle, so no
  intervening mask is known and no re-indexing is possible). When the execution-time length
  refusal below is traceable to a loose VALUE rather than a weight factor, its message names that
  value — not "the offending factor" and not "pass the value unflattened". An all-loose fill is
  unweighted (the primitive path, still supported).
  **Every weight factor the fill applies — the ambient one AND explicit `weight=[...]` factors —
  is broadcast to the fill's value structure** (the recording TRIGGER is the one §6.3(2) states:
  a fill carrying a context handle OR any `Varied` input; a fill with neither records as today).
  The evaluator flattens each input independently and multiplies factors elementwise *after*
  flattening, so in a per-object fill an unbroadcast per-event factor
  (`weight=[events.genWeight]`) would length-mismatch. The mechanism is bound: **a per-object
  fill MUST pass its value UNFLATTENED** (`h.fill(sel.Jet.pt)` — not `gak.flatten(...)`, which
  destroys the jagged structure there is nothing left to broadcast against), and the frontend
  then records a **broadcast-to-value-structure seam** relying on the evaluator's existing
  independent per-input flatten.
  **The broadcast is a neutral, backend-dispatched seam, NOT a named gak call**
  (`graphed-histogram` has no awkward runtime dependency, and naming `gak.broadcast_arrays` would
  make the neutral seam awkward-only — the factorization rule §2.1 invokes). Binding: the seam is
  **`graphed.broadcast_like(value, factor) -> Array`** (spelling pinned at m48 freeze) — a
  neutral entry point owned by `graphed` proper, dispatched to the backend idiom, taking an
  ARBITRARY factor, **not a context method** (which could not reach a user-owned
  `weight=[events.genWeight]` factor or an all-loose fill). The fill applies it to the ambient
  weight and to every explicit factor alike. The awkward implementation records
  `ak.broadcast_arrays`; **the numpy idiom is a NO-OP — bound, not an either/or** (a no-op makes
  an all-numpy varied fill work; `graphed.numpy` is rectilinear, so a genuine shape mismatch
  surfaces as numpy's own error at execution — the same execution-time refusal shape bound
  below). The seam is owned by `graphed` proper; the awkward implementation by `graphed.awkward`;
  `graphed-histogram` gains no awkward dependency.
  **The already-flattened-value case is an EXECUTION-time refusal, not a record-time one**: a
  legitimately per-event value (`gak.firsts(...)`, `gak.num(...)`, `MET.pt`) and a flattened
  per-object value have identical 1-D forms and differ only in runtime length (the record-time
  alternative — a flatten-hunting cone walk — false-positives on `gak.flatten(x, axis=2)`).
  **The refusal is bound as a CONTRACT, not as a named class**: the broadcast seam is a recorded
  graph node UPSTREAM of the fill, so it executes first and dies there. Binding: **at execution,
  a varied fill whose weight input cannot be broadcast to the axis values' structure fails with a
  `graphed` error naming the OFFENDING FACTOR** — the ambient weight or the explicit `weight=[…]`
  entry by position — **and, when the offender is a per-event factor against a per-object value,
  pointing at "pass the value unflattened"**. **The translating wrapper is an m49 target in
  `graphed.awkward`, and it is what makes that contract true**: as built, `broadcast_like` is a
  bare `broadcast_arrays` with no blame channel, and the histogram-side guard compares row COUNTS
  only, so a structure mismatch that agrees on outer length reaches the user as a raw awkward
  `ValueError` naming two `RegularArray`s. m49 wraps the awkward seam's evaluator so that
  `ValueError` is re-raised as the `graphed` error above; nothing binds WHICH class raises, only
  that it is a `graphed` one naming the offending factor. Frozen-witnessed in `awkward/m49` against
  a manually broadcast reference, with the compatible-factor positive control in the same test.
  This reproduces the corpus reference layout (independent per-variation histograms — UHI, no
  invented formats).

- **§6.2 (Scaling shape: the variation axis, m50 — weight labels collapse into the loop.)** An
  opt-in fill mode — **expressed PER `fill()` call and remembered by the histogram**, which is what
  makes §6.2(i)'s "later fill in the OTHER mode" reachable and its mode-mismatch error buildable;
  exact spelling pinned at m50 freeze — lands **weight-label** variations in ONE histogram with a
  **non-growth, pre-declared, sorted StrCategory `"variation"` axis** via an evaluator-side loop
  (extend/sibling `FillEvaluator`; labels ride the spec/params under the §1.2 carve-out;
  scalar-string broadcast and non-growth combine-safety are probe-verified — cba §histogram §3).
  **Shift labels always lower as sibling fill nodes** — their per-label axis columns have
  diverging lengths (§5.1 cutflow), which the single-weight-loop evaluator shape cannot carry —
  **and in axis mode a shift sibling TARGETS the same pre-declared variation axis**, writing its
  label as the scalar category value of its own fill and contributing **no** per-label sibling
  slot: one histogram carrying both classes, filled from separate passes with a scalar label, is
  the confirmed exemplar's actual layout in both eras (lit §ewkcoffea-confirmed). The m50 equality
  anchor covers both the weight-label evaluator loop and a mixed shift+weight program landing in
  ONE axis-mode histogram equal to its sibling-fill decomposition. **Axis-mode fill-node arity is
  therefore `1 + |S|`** (only `W` — the labels borne ONLY by weight factors — collapses into the
  evaluator-side loop), which is why §6.1b's `1 + |S| + |W|` is scoped to sibling mode. **`S` and
  `W` carry §6.1b's lowering definitions here too**: a label borne by a `Varied` `sample=` is in
  `S` and lowers as a sibling writing its own scalar category value, since the evaluator's weight
  loop re-fills against a fixed sample column and cannot carry it.
  **§6.1d's broadcast seam ranges over the loop node's weight COLUMNS, one per label — the axis
  mode of the same rule, not a new one.** §6.1d binds every weight factor a fill applies to be
  broadcast to that fill's value structure; axis mode hands the loop node `|W|` columns instead of
  one, so the seam is recorded upstream of the loop node PER COLUMN. The loop evaluator inherits
  the sibling evaluator's independent per-input flatten, so an unbroadcast per-event column
  length-mismatches against a per-object value exactly as a sibling fill's would — and the corpus
  this mode exists to serve is per-object (lit §ewkcoffea-confirmed), so m50's equality anchor
  carries a per-object value (§10/m50) rather than leaving that granularity to the test-author.
  **The per-fill variation payload has a bound CARRIER**: an External evaluator is resolved solely
  by the payload's content hash (today `content_hash(self._spec)`), the plan-time registry merges
  every histogram's evaluators into ONE dict keyed the same way, and §6.2(i)'s cross-fill
  agreement rule forces one spec — hence one chash — per axis-mode histogram, so the `1 + |S|`
  fill nodes would all resolve to a single evaluator. Binding: the per-fill variation payload (the
  scalar label for a shift sibling; the ordered weight-label tuple for the loop) is a **field of
  the fill's `FillEvaluator` AND enters the External payload's content hash** —
  `content_hash((spec, variation_payload))` in axis mode — so each axis-mode fill node resolves to
  its own evaluator. M29's identity discipline is preserved: the extra content exists only in axis
  mode, and a **SIBLING-mode fill — varied or not — hashes exactly as today (the MODE decides,
  §6.1c: an unvaried AXIS-MODE fill under (ii) still declares the 1-bin `{"nominal"}` variation
  axis, so its spec and its `content_hash((spec, variation_payload))` both differ from today's)**.
  Cross-referenced from §6.1c, whose per-slot spec is the fill node's, not the histogram
  object's.
  Non-growth is required: identical spec per partition keeps `+` combine safe and deterministic
  (growth axes stay Phase 2 per the existing `_spec.py` refusal). **Who declares the bins**:
  (i) **the FRONTEND declares the axis, at FILL time** — the point the spec enters node identity —
  from the §6.1d inferred label set (known at fill time), so the spec is identical per partition
  by construction and combine-safety follows (plan-time declaration would require re-recording
  every fill or mutating interned node params, forbidden §3.1/§1.2). Exact declaration is a
  silent-drop gate: a non-growth `StrCategory` does NOT raise on an undeclared string — it lands
  in the overflow bin and the label silently vanishes.
  **Cross-fill agreement rule**: a second fill into the same axis-mode histogram whose inferred
  label set differs from the first's is a hard error naming the mismatch.
  **The MODE is a property of the HISTOGRAM, not of a single `fill()` call**: the first fill fixes
  the mode and a later fill into the same histogram in the OTHER mode is a hard error naming both
  (a mixed histogram would give one output both §6.1c key forms and uncombinable per-slot specs).
  Frozen alongside the m50 declaration anchor.
  **(i-bis) Axis-mode RESULT SHAPE** — §6.1a binds only the sibling shapes, so this is stated
  here: an axis-mode varied output returns a **bare `bh.Histogram` carrying the `"variation"`
  axis**, indistinguishable by type from an unvaried output, so `graphed.labels` and
  `graphed.universe` recognise it explicitly. `graphed.labels(h)` = the variation axis's bin set
  RE-ORDERED to §2.2's rule — `"nominal"` first, then the remaining bins in axis (lexicographic)
  order — while the STORED bin order stays lexicographic and unchanged; `graphed.universe(h,
  label)` = that label's slice along the variation axis. The m50 (i-bis) anchor asserts that
  ordering, and the m50 declaration anchor must not use `graphed.labels(h)` as its oracle. **The
  two MODES do NOT agree on label ORDER for one program**: sibling mode reports §6.1d's fold
  order, axis mode nominal-first-then-lexicographic — so m50's axis-vs-sibling equality anchor
  compares PER LABEL and MUST NOT use `graphed.labels` equality across the two modes as its
  oracle. The §6.1a narrowing helper is uniform over all THREE shapes (bare-unvaried,
  `{label: hist}`, bare-axis-mode).
  **The SPELLING of that slice is bound**: on boost_histogram 1.7.2 and 1.8.0,
  `bh.axis.StrCategory([...], name="variation")` is a `TypeError` (no `name=` kwarg) and a
  string-keyed dict index raises regardless of axis metadata — named-axis dict access is a
  `hist`-package feature, out of m50's scope. Binding: (1) the frontend **writes the axis name
  into `axis.__dict__["name"] = "variation"`** — the `hist` convention `graphed-histogram`'s spec
  codec already round-trips as axis metadata, probe-verified to survive `spec_of` → `zero_of` on a
  two-axis histogram. **`h.axes.name` raises `AttributeError` unless EVERY axis carries a name**,
  so the position lookup MUST read `axis.__dict__`, never `h.axes.name`, and an m50 test-author
  must not write `h.axes.name` as the oracle; (2) `graphed.labels`/`graphed.universe` resolve the
  axis POSITION from that name and slice by index. Nothing binds a literal subscript expression.
  **(3) No `boost_histogram` import in `graphed` proper** (`graphed`'s runtime dependencies are
  `["executing>=2.0", "cloudpickle"]`; boost-histogram is only a `dev` extra): detection is
  **duck-typed** (an object exposing `.axes`) and the slice uses a plain INTEGER bin index
  obtained from the axis itself — `axis.__dict__["name"]` to find the position, then
  `axis.index(label)`, measured equivalent to the `bh.loc` form. **The no-import rule is knowingly
  left UNANCHORED**; an m50 implementation MAY discharge it with a one-line static assertion (the
  module's source contains no `boost_histogram` import) in `tests/extra`.
  (ii) **A user-declared `"variation"` axis is NOT supported in v1** (unfillable today:
  `Histogram.fill` requires one array per axis, so a histogram constructed with a variation
  `StrCategory` rejects the user's N-array fill, and the arity carve-out is unscoped). The
  frontend declares it, always, from the inferred label set, so the declared bin set IS the
  inferred set by construction; the frozen witness is an equality against a literally spelled
  expected label list, never one read back from the histogram (`h.sum(flow=True) == h.sum()`
  misses over-declaration). User-declared axes are parked in §11. (iii) The frontend, not the
  user, imposes the sort, so "sorted" and "pre-declared" cannot conflict. M29's identity
  discipline binds: new params/spec content only when the feature is used. The sorted bin order is
  **lexicographic over label strings and MUST NOT be read numerically** (`murf_10` sorts before
  `murf_2`); positional/plot ordering for numeric families comes from §9.1's parsed-value
  introspection, never from bin index.
- **§6.3** Data / no-variation paths are unchanged, gated by both in-tree golden patterns: a
  **committed golden GIR blob** for an unvaried fill graph (the `core/m40/test_join_serialize.py`
  pattern) plus a **params KEY-SET equality** — the unvaried single-weight fill node's
  `set(node["params"])` equals a LITERALLY spelled expected set, today
  `{"spec", "n_axes", "weighted", "sampled"}` (`n_weights` is added only when
  `len(weights) > 1`). A key-absence placeholder is unusable here: m48 in sibling mode adds NO
  params key by design (§1.2), so there is no key to spell. **Two halves are bound**: **(1)** the
  golden blob is captured from the **PRE-m48 revision** of that fill graph (captured after
  implementation it is a no-op tautology) **and COMMITTED ALREADY STRIPPED of the fill node's
  `PayloadDescriptor.version`**, the live blob being stripped at assert time of the version IT
  carries — `blob.replace(len(v).to_bytes(4, "little") + v.encode(), b"")` for that side's own
  `v = bh.__version__`. **The pattern is per-side, never one pattern applied to both**: it is
  content-derived, so a single live-derived pattern misses the literal's capture-time version
  entirely and the comparison reds on the first bump — silently, since both sides agree at
  capture. `Histogram.fill` hard-codes `version=bh.__version__` into the serialized descriptor
  with no author-facing knob and `boost-histogram>=1.4` is unpinned, so an unstripped literal
  reds on the next release, in a frozen file that cannot be repaired in place. The closing test
  monkeypatches `bh.__version__` to a different string, re-derives the live blob, and asserts
  equality after stripping; **(2)** §6.1d's broadcast seam is **SCOPED, and the
  trigger is stated ONCE: the seam is recorded for every weight factor of a fill that carries a
  context handle OR any `Varied` input; a fill with NEITHER records byte-identically to today** —
  exactly this section's golden case.
- **§6.4 (Variation-aware write-out — skim augmentation; collaborator-directed scope.)** Writing
  varied data (`to_parquet`, the uproot fork's `graphed_write`) is a first-class sink, not a
  Phase-2 parking: the surveyed frameworks each hit this wall and bolted around it (Part I §2),
  and graphed's write path is measured greenfield (zero variation machinery, zero metadata use,
  one seam method per backend). Binding:
  (a) **Row rule — OR of selections, with the selection supplied EXPLICITLY.** When the written
  rows pass through a varied selection, the writer materializes the **superset**: rows passing ANY
  universe's selection, nominal included. The OR is recorded as ordinary graph ops over the
  per-label masks (`getitem`/`gak.mask` — no mask algebra exists in the IR and none is added).
  **The varied write API takes the mask(s), it does not infer them** (inferring the selection
  inside an already-interned record expression would require a node rewrite the IR forbids, §3.1,
  plus an undecidable "which node is *the* selection" rule):
  `graphed.awkward.to_parquet(record, select=…)`-shaped (exact spelling at m51 freeze), the
  **awkward-idiom** verb — `to_parquet` is exported only from `graphed.awkward`
  (`python/graphed/awkward/io.py`), the numpy idiom having its own 1-D-capped implementation
  (`python/graphed/numpy/io.py`), so §6.4f's "numpy backend EXEMPT" means *the numpy-idiom
  function refuses*, not that a neutral dispatcher is introduced. `record` is PRE-selection (see
  the entry check below); `select=` carries the `Varied` mask(s). **`select=` is per SELECTION
  LEVEL, not one row mask**: it accepts either a single `Varied` row mask, or a mapping of
  `Varied` masks — `{0: event_mask, ("Jet", 1): jet_mask, …}` — **one entry per (FIELD PATH,
  LEVEL) that varies. A level-0 entry is keyed by the bare depth `0` and applies to the record's
  ROW axis; every level-k ≥ 1 entry is FIELD-SCOPED and names the field path it applies to —
  EXCEPT where the level-k structure is the RECORD'S OWN, which takes the bare depth `k`** (the
  canonical skim writes the varying collection itself, `to_parquet(events.Jet, select=…)`, where
  `"Jet"` is not a field of the written record — it IS the record). Binding: the bare depth
  `k ≥ 1` key is legal iff the record is itself jagged at depth `k` (its own offsets, all fields
  inside them); a record carrying two or more independently jagged fields at that depth REFUSES
  the bare key at the `to_parquet` call, naming the ambiguity and the field paths. **What the
  writer does with them is exact**: it applies the **level-0 OR** to the stored ROWS — that IS the
  superset — and applies **no other supplied mask** to the stored buffers (§6.4d: inner cuts are
  never applied, or the deltas lose their common shape); and it stores **one packed per-label
  validity mask per supplied ENTRY — stored against that entry's FIELD (against the record's own
  axis at that depth for a bare depth-`k` entry), level 0 against the row axis**.
  **The "record is pre-selection" precondition is a DECIDABLE entry check** — **TWO predicates**:
  **(1) MULTIPLICITY** — every per-label member's offsets equal nominal's at every level the
  writer will store (§6.4d's multiplicity-changing refusal);
  **(2) ROW-SPACE AGREEMENT, SCOPED PER LEVEL** (a level-1 mask is per-OBJECT, jagged over the
  record's INNER dimension, so one lineage test cannot apply to every supplied level): **level 0,
  split in two halves with different sites**.
  **(2a) LINEAGE, record-time** — decided by **CONTEXT-HANDLE EQUALITY** over the operand that
  exists: **the supplied mask's own §2.3e context handle MUST BE the record's context handle, OR
  be reachable from it across `graphed.vary` IDENTITY LINKS ONLY, in either direction —
  `graphed.context_of(select_mask) is graphed.context_of(record)`, else one upward walk over the
  lineage §2.6b already retains that crosses `vary` links and NOTHING else.** `vary` links must be
  admitted: a skim written after ANY weight `vary` is written from a `vary`-derived context, and
  `vary` links do not move the row space (§6.1d link kind (2)) — bare handle equality alone would
  refuse a legal configuration, since a read through `E2 = graphed.vary(E1, …)` carries `E2` while
  a read through `E1` carries `E1`, different handles and identical row spaces. The admission is
  WITNESSED by §10's discriminating control — `E2 = graphed.vary(E1, …)`, `sel = E2[mask]`,
  `to_parquet(E1.Jet, select=graphed.selection(sel))` (record handle `E1`, mask handle `E2`,
  accepted across the `vary` link) — NOT by the `sel2 = graphed.vary(sel, …)` bridge anchor, whose
  mask already carries the record's root handle and so accepts by bare handle equality. Links of
  the universe/nominal projection kind are NOT admitted. The direction
  matters: in the canonical `to_parquet(events.Jet, select=graphed.selection(sel))` with
  `sel = events[mask]`, the record's own context is the ROOT `events`, whose `graphed.selection`
  is `None` (§9.1) — the m51 anchor's wording, "a record whose context is not the one the
  supplied `select=` mask DERIVES FROM is refused", is normative. The
  m51 controls: canonical skim `to_parquet(events.Jet, select=graphed.selection(sel))` with
  `sel = events[mask]` → ACCEPT; silent-corruption case (`sel = events[nominal_mask]`, record
  `sel.Jet`, `select=varied_mask`) → REFUSE; chained-context case (`graphed.selection(sel2)` for
  `sel2 = sel[mask2]` against a root-row-space record) → REFUSE; universe/nominal case
  (`graphed.selection(graphed.nominal(sel))` against a record read from `sel`) → REFUSE;
  re-recorded-equal-expression positive control (two recordings of one expression intern to one
  node and carry the same handle by construction). A record read across a MASK-DERIVATION or
  PROJECTION link from the mask's context is refused at the `to_parquet` call, naming both
  contexts.
  **Both operands can be ABSENT, and each case is bound**:
  **(i) the RECORD carries no context handle** — (2a) is SKIPPED, and predicate (2b)'s
  per-partition row-count equality alone decides (the loose §2.1a style stays reachable); m51's
  entry-check anchor carries a loose-style write as an explicit POSITIVE control for (i).
  **(ii) the record has a handle but the supplied mask carries NO context handle** (a hand-built
  loose mask, §2.3e's Drop rule) — REFUSED at the `to_parquet` call, naming the record's context
  and stating that the mask has no lineage to check against. The trigger is "carries no handle",
  NOT "derived no context": a mask recorded entirely from reads through the record's own context
  (`select=(events.MET.pt > 50)` passed directly) carries handle `events` by §2.3e's ORIGINATION
  rule, so **a contexted mask carrying the RECORD'S OWN handle is ACCEPTED whether or not any
  context was ever derived from it** — the case-(ii) origination control, the only fixture that
  distinguishes the two readings (distinct from the enumerated fifth control, the
  re-recorded-equal-expression positive control above).
  **(2b) ROW-COUNT EQUALITY between the record and that mask — EXECUTION-time, per partition**,
  raised by `_WritePart` before any buffer is stored, exactly like predicate (1).
  **(2c) LEVEL-0 DEPTH, record-time** — a mask supplied at level 0 MUST be FLAT over the record's
  row axis (depth 0); a JAGGED level-0 mask is refused at the `to_parquet` call, naming the level
  and the per-level channel. Neither (2a) nor (2b) constrains depth — a per-OBJECT mask read
  through the record's own context (`select=(events.Jet.pt > 25)`) passes both, and
  jagged-boolean indexing would then filter INNER elements while keeping every row, silently
  violating the superset-row contract and §6.4d's "inner cuts are never applied" rule. m51
  carries it as a negative control alongside (2a)'s.
  **(2c) GENERALIZES TO EVERY SUPPLIED LEVEL**: a mask supplied at level k MUST have depth k over
  the record's structure — over the NAMED FIELD for a field-scoped level-k ≥ 1 entry, and over
  the RECORD'S OWN structure at depth k for a BARE depth-`k` entry (single-valued by the bare-key
  legality condition) — and a depth mismatch at ANY supplied level is refused at the `to_parquet`
  call, naming the level. Depth is a FORM property known at record time — read from the
  typetracer form (`session.form(array).tt.ndim`), since the awkward-idiom `AwkwardForm` exposes no
  depth accessor of its own. m51's (2c) negative control carries the too-shallow level-1 mask
  alongside the jagged level-0 one.
  **Levels ≥ 1** — lineage is not the available handle, so the check is STRUCTURAL: each
  per-label member of the mask must carry **that NAMED FIELD's own offsets at that depth — or,
  for a BARE depth-`k` entry, the RECORD'S OWN offsets at that depth** — and the packed per-label
  mask is stored against that field. **The stored mask's ROW SPACE is bound here too** (§6.4c
  requires a reader to reproduce each universe's row set from the stored data alone): every
  stored per-label mask — level 0 and every level k ≥ 1 — is stored on the **SUPERSET rows**
  (level-0-OR-restricted), so a reader applies it directly to the stored buffers; the level-≥1
  structural predicate runs against the record's offsets AS EVALUATED (pre-restriction, the
  operand `_WritePart` holds when it raises), and the restriction is then applied to mask and
  buffers alike. It shares predicate (1)'s raiser and error shape, per partition.
  Each predicate has its own error message, and the m51 anchors name which predicate decides
  which positive control.
  **Writing from a context (§2.6 idiom).** Contexts expose no mask accessor
  (§2.2/§9.1 list `labels`/`universe`/`nominal`/`weight`/`variations` only), so a binding bridge:
  **`graphed.selection(ctx)`** implements §9.1's FULL three-case contract — including CASE-2,
  which returns a NON-`None` handle-carrying mask on a universe/nominal-derived context (that
  label's member of the argument's own selection, an unvaried `Array` in the GRANDparent's row
  space), the case §6.4a's universe/nominal REFUSE control relies on to fire for the specified
  row-space/context reason. It is therefore NOT a thin wrapper over the current private
  `EventContext._selection()` walk, which returns `None` on any project/universe/nominal link. A
  root context returns `None`; the skim spelling is
  `to_parquet(events.Jet, select=graphed.selection(sel))`. Frozen-anchored in m51.
  **Where the checks RUN.** Offsets are data: at the `to_parquet` call the frontend holds a
  recorded graph and typetracer forms, and the write is evaluated **per partition inside the
  worker** (`_WritePart.__call__` reads the partition, calls `evaluate_ir`, then writes one
  part — `python/graphed/awkward/io.py`; the per-partition task graph is built by
  `python/graphed/write.py`). Binding: predicate (2a)'s **level-0 lineage** half **and (2c)'s
  DEPTH half at EVERY supplied level** ARE record-time checks raised from the `to_parquet` call
  (depth is a form property at every level, §6.4a); predicate (1)
  (offsets), **predicate (2b)'s level-0 row-count equality** **and predicate (2)'s level-≥1
  STRUCTURAL (offsets) half** are **execution-time, per-partition checks raised by `_WritePart` BEFORE any
  buffer is stored**, surfacing through the executor's error path — the same treatment §6.1d
  already takes for its length check. m51's anchors are worded accordingly; do NOT freeze a
  record-time raise for any offsets- or row-count-shaped predicate, (2b) included.
  (b) **Column rule — augmentation.** The written record carries the user's fields evaluated in
  the **nominal** universe (on superset rows), PLUS appended per-label reconstruction data: for
  every stored field that **IS `Varied` — structurally, at record time** (a value-based "differs
  per label" reading would make the augmented column set data-dependent per partition; m51's
  round-trip anchor settles the intent — "a label structurally equal to nominal (all-zero
  delta)" IS written), a same-shaped delta column — **so the augmented column set is identical
  across partitions by construction**; and per-label selection masks (the varied cutflow) plus
  the nominal mask, so each universe's row set is recoverable. Weight-only labels contribute no
  kinematic deltas — their varied factors, when among the stored fields, augment like any other
  varied field (**reachable via `graphed.weight(ctx)`**, §9.1). **The ROW-SPACE precondition on
  that is bound here**: §2.6c re-indexes a SELECTION-derived context's ambient registry by each
  label's own mask, so `graphed.weight(sel)` for `sel = events[mask]` has per-label lengths that
  differ from the superset, and no re-indexing back onto the superset is expressible (a mask has
  no inverse). Binding: **a stored varied field MUST live in the record's own row space;
  `graphed.weight(ctx)` is storable exactly when `ctx` is reached from the record's context
  across `vary` IDENTITY links only (§6.1d link kind (2)) — no mask-derivation link — and a
  SELECTION-scoped weight is NOT storable in v1, refused at m51's entry check with a message
  naming the row-space mismatch, not an offsets mismatch.** (It remains fully supported for
  FILLS, §2.6c; only the skim sink refuses it.) m51's entry-check anchor carries the refusal and
  its round-trip anchor names the storable spelling. Appended names follow one bound convention
  (`__vary_{label}__{field}`-shaped; exact spelling pinned at m51 freeze). Labels are valid
  identifiers by construction (**§1.1 canonicalization, e-form** — a dotted spelling never
  reaches a label), so labels appear in on-disk names VERBATIM: the canonical on-disk shape is
  `__vary_murf_5em1__Jet_pt`. **The `{field}` half is bound separately** (§1.1's discipline
  covers only the LABEL half, and a nested path — `Jet.pt`, `FatJet.subjet.pt` — puts a `.`
  straight back into the name): the field path is flattened with `_` per level, **and the
  resulting on-disk names are checked for COLLISION in BOTH directions — derived-vs-derived and
  derived-vs-stored — a collision REFUSED at m51's entry check, naming both source fields** (the
  real collision class is both `Jet.pt` and a flat `Jet_pt` varying, each deriving to
  `__vary_L__Jet_pt`; a nested-field skim is LEGAL under this convention, not a refusal case).
  §6.4e's manifest remains the sole machine resolver: readers resolve labels and columns THROUGH
  it, never by parsing stored names — the flattening is for human inspection, and the collision
  refusal exists so the two never disagree. m51 freezes a nested-field skim round-trip and the
  collision refusal. The probe-measured dotted-name hazards
  (`ak.from_parquet(columns=["murf_0.5"])` silently empty, pyarrow 25.0.0 / awkward 2.12.0;
  uproot 5.7.5 RNTuple `RField.array()` fails because `to_akform` splits the path on `.`; the
  TTree writer's own `.` nesting separator; ROOT TTreeFormula `.`/`-` operator meaning) are
  foreclosed at the §1.1 gate; identifier-shaped names of this convention's form round-trip
  byte-exact and readable in every measured path.
  (c) **Bit-exact reconstruction is REQUIRED — at every selection level SUPPLIED through
  `select=`.** Reading the file back and applying the deltas MUST reproduce every universe's
  post-selection values and row set bit-for-bit vs the in-memory varied run, at those levels.
  The scoping is what the writer can promise — §6.4a stores one packed per-label mask per
  SUPPLIED entry — so **a level not supplied is not recoverable, and §6.4e's manifest records
  which levels are stored** (m51's round-trip anchor supplies both levels). The default
  representation is **exact by construction**: same-dtype XOR bit-delta vs nominal for value
  columns (zero wherever a label equals nominal — maximally compressible), `packbits` for masks
  stored as nominal + XOR-vs-nominal diffs. **The COMPUTATION SITE is bound, because the
  in-graph reading is measurably not expressible**: `float32 ^ float32` raises `TypeError` for
  both `np.ndarray` and `ak.Array`, and gak has no bit-view verb — so the XOR bit-delta and
  `packbits` are computed inside `_WritePart.__call__` on the EVALUATED buffers
  (`ndarray.view(uintN)`), after `evaluate_ir` and before the write. The extra marked outputs of
  §6.4f's shared `compile_ir` are the **per-label VALUES and per-label masks**, and its
  read-list widening must cover them. An in-IR bit-view verb is NOT scoped (§11). Measured basis
  (R0.11; float32/1M-value/zlib-6 probe): the suggested "1+delta" float ratio compresses best
  (2.88 MB vs 3.55 raw) but is **NOT bit-exact**; subtraction delta is bit-exact only
  data-dependently; XOR is exact by construction (3.28 MB); XOR-diff+packbits masks are ~4.7×
  smaller than raw booleans (169 KB vs 798 KB, 5 labels). Lossy ratio storage is a Phase-2
  opt-in (§11); the representation is recorded per column in the manifest; sizes are measured on
  real skims in the m51 implementer report.
  (d) **Structure rule, with an explicit refusal.** Deltas require same-shaped buffers: varied
  columns are stored at the widest common structure (pre-object-cut values on the event-row
  superset), with per-label validity masks at every selection level that varies — event-level
  AND object-level (a JES shift moves jets across a per-jet pt cut, so per-label *inner* masks
  are part of the cutflow data, not an edge case). The writer stores one packed per-label mask
  for each level the user supplies (`{0: event_mask, ("Jet", 1): jet_mask}`) and never applies
  them to the stored buffers; a level-k ≥ 1 entry is FIELD-SCOPED unless the level-k structure
  is the record's own, which takes the bare depth `k` (§6.4a), so a field shallower than a
  supplied level, or at that depth under a different field path, is unaffected by it — a depth-0
  stored factor (`graphed.weight(c)`, §6.4b) coexists in one record with a depth-1 `("Jet", 1)`
  entry. §2.1's construction check is a TYPE check (`var * float64` matches `var * float64`
  whatever the per-event counts), so a variation that legitimately changes multiplicity
  (shift-dependent cleaning, overlap removal, a matched collection) passes §2.1 and then has no
  representable XOR delta. **Binding refusal**: a stored varied field whose per-label offsets
  differ from nominal's is REFUSED with an error naming the label and the field (m51's refusal
  fixture: a post-object-cut record, `jets[jets.pt > 25]` under a JES shift, whose per-label
  offsets differ — distinct from m51's LEGAL same-offsets object-migration case, which is
  expressed as per-label inner masks). The supported v1 model is same-multiplicity variation plus
  per-label validity masks; multiplicity-changing stored variations are Phase 2 (§11). Frozen as
  an m51 negative anchor.
  (e) **Manifest — invent no formats.** A manifest (labels → appended columns → representation,
  **plus the selection LEVELS whose per-label masks are stored** — §6.4c scopes reconstruction
  to the supplied levels, so a reader must be able to tell which those were) travels in existing
  metadata channels: parquet key-value file metadata (unused by graphed today — greenfield).
  **The writer swap is CONDITIONAL, not unconditional**: measured (awkward 2.12.0 / pyarrow
  25.0.1), `ak.to_parquet(a, p)` and `pq.write_table(ak.to_arrow_table(a), p)` produce
  **different bytes** for every array probed (so a naive arrow write breaks the §6.4g unvaried
  byte-golden), and the arrow path **drops awkward's own `awkward_array_metadata` KV entry**;
  `ak.to_parquet` has no metadata parameter (signature verified), so the swap genuinely is
  required for the manifest. (`ak:parameters` appears only when the array carries awkward
  parameters — a property of the DATA, not of the writer — so no test may freeze a literal KV
  set.) Binding: an **unvaried write keeps `ak.to_parquet` untouched** (preserving the §6.4g
  golden); a **varied write** MUST reproduce awkward's own KV entries alongside the graphed
  manifest, with `ak.from_parquet` round-tripping the augmented file as a frozen m51 anchor.
  **The ROUTE is bound too**: the dropped key is written only by a PRIVATE awkward helper
  (`AWKWARD_INFO_KEY` in `awkward/_connect/pyarrow/table_conv.py`). Binding: **the varied write
  MUST NOT import `awkward._connect.*`** (the §2.3e/§6.1d package-boundary rule, here against a
  package where `graphed` cannot add a seam), and its route is the PUBLIC composition — build
  the file awkward's own writer would (`ak.to_parquet` to the part path or an in-memory sink),
  then re-read the table and re-write it with the graphed manifest merged into the schema
  metadata (`Table.replace_schema_metadata` + `pq.write_table`), the same merge point
  `ak.to_parquet` itself uses for `attrs`. The second write is the accepted cost of the varied
  path; the unvaried path is untouched (§6.4g). A future revision MAY bind a cheaper route, but
  never one that imports awkward's private package. **The no-private-import half is knowingly
  left UNANCHORED, and rides code review plus the repo's integrity scan**; an m51 implementation
  MAY discharge it with a one-line static assertion (the varied-write module's source contains
  no `awkward._connect` import) in `tests/extra`.
  The manifest maps each label to its stored column/branch names and per-column representation,
  **serialized with SORTED keys** (set/dict-iteration order would make the written bytes depend
  on `PYTHONHASHSEED`, the hazard §8.2(i) names for the plan closure). **The selection-LEVELS
  entry's serialized SHAPE is bound here too** (§6.4a's key space is heterogeneous, with no
  JSON-native rendering): the entry is a **list whose elements are either an integer depth or a
  two-element `[field_path, depth]` array**, `field_path` spelled as the `_`-flattened path
  §6.4b binds for stored names. **The TOTAL ORDER is bound with it**: order by the key
  `(depth, field_path or "")` — bare-depth entries before field-scoped entries of the same
  depth, field-scoped entries by flattened field path — so the list is a pure function of the
  supplied `select=` keys and the manifest bytes stay `PYTHONHASHSEED`-independent (`sorted()`
  over the raw mixed elements is a `TypeError`, and `json.dumps(…, sort_keys=True)` never orders
  a list's elements, so neither the house serializer nor a bare `sorted()` supplies this order).
  Exact key spelling pinned at m51 freeze. Readers resolve labels **through the manifest**,
  never by parsing stored names (names embed labels for human inspection, not as the machine
  channel). A frontend reader (**`graphed.awkward.read_varied(path)`-shaped**; spelling at
  freeze) reconstructs `{label: array}` per universe from the manifest — the round-trip is the
  m51 frozen anchor. **The reader is awkward-idiom, symmetric with the writer** (awkward and
  pyarrow live only in `graphed`'s extras, so a neutral `graphed.read_varied` returning awkward
  arrays would put both behind the neutral namespace). A variation-aware ROOT write-out and reader
  (its own manifest channel + delta storage) is Phase-2 (§11); m51's ROOT half is derived-column
  IR evaluation only (§6.4f, §10).
  (f) **Seam binding (write-seam evidence).** Parquet: appended columns are extra marked outputs
  of the SAME `compile_ir` (variadic by design), so the M4 optimizer shares the pass with the
  primary expression — appended between the evaluate and write steps of `_WritePart.__call__`.
  **The marked outputs are the per-label VALUES and masks, not the encoded deltas** (§6.4c), and
  the read-list widening below must cover them. **That call site unpacks a SINGLE output today**
  (`(out,) = evaluate_ir(...)`), so widening it to the augmented output list is part of this
  target, not incidental. **The widened unpack resolves each augmented output BY NODE ID per
  §7.2, never positionally**: `mark_output` de-dups and `evaluate_ir` returns one value per
  DISTINCT output, so on m51's anchored all-zero-delta case a positional unpack silently
  misassigns every label after the collapsed one. A shared value is REPLICATED into every label
  that maps to it, and the **`record node id → output position` table is a FIELD of
  `_WritePart`** — driver-derived and shipped in the closure, since `_WritePart` is a frozen
  dataclass evaluated per partition in the worker and cannot recompute it there. §7.2's
  optimizer-merge REFUSAL also guards the write path: **it does** — the varied write is a varied
  unpack path in §7.2's sense and a μR/μF label spelled `w * 1.0` is §1.1-legal, so at m51 the
  same distinct-outputs-vs-distinct-marked-ids shortfall check runs in the varied `to_parquet`
  path (record-time, at the call) with §7.2's message and workaround; the read list widens at
  `_evaluation_columns` (`awkward/io.py`) or projection starves the task. ROOT: `graphed_write`
  today copies branches verbatim with NO IR evaluation (`_graphed_write.py`; zero
  `compile_ir`/`evaluate_ir` use) — adding evaluation (derived columns) is the ROOT half of m51 and is
  scoped there explicitly. numpy backend: EXEMPT — it hard-caps output at one 1-D column; the
  numpy-idiom write function refuses a varied write with a clear error naming the awkward
  backend. **The TRIGGER and the ENTRY POINT are pinned**: the function is
  `graphed.numpy.io.to_parquet` (reachable only through the module — absent from the
  `graphed.numpy` namespace and `__all__`), and the refusal triggers on a **`Varied` first
  positional**, raised as a graphed error naming the awkward backend instead of §2.2's
  reserved-name `AttributeError`. It gains **NO `select=` keyword** (the signature stays
  `to_parquet(array, destination, *, steps_per_file, compute, executor, prefix, column)`), so a
  `select=` call stays an ordinary `TypeError` and no m51 anchor may freeze a graphed error for
  it; exact message spelling pinned at m51 freeze. **And the numpy idiom exposes no
  `read_varied` counterpart** (symmetry with §6.4e's awkward-idiom reader).
  (g) **Single pass; no cost when unused.** The augmented write stays one plan / one read pass
  (the §5.2b witness applies to the write run); an unvaried write is byte-identical to today's
  output, and carries no manifest. **The byte-identity is frozen as a SAME-PROCESS comparison,
  never as a committed `.parquet` fixture**: a parquet footer embeds its writer version (an
  `ak.to_parquet` file carries `parquet-cpp-arrow version <arrow version>`, readable as
  `ParquetFile(path).metadata.created_by`), so a committed blob turns red on any pyarrow bump
  and can differ across §A.5 matrix legs while the behaviour is correct, which R0.10a forbids.
  What m51 freezes: write the same array through the feature-present path and through
  `ak.to_parquet` directly in ONE process (byte-identical for repeat writes) and assert byte
  equality plus the absence of the manifest KV key. Params-absence (the §6.3 pattern) still
  applies to the graph side.

## §7 Execution, results, checkpoint

- **§7.1** One Session, one IR, one plan for nominal + all variations; executors are untouched
  (`R` opaque through `Plan`/tree-reduce/engines — cba §exec-checkpoint §1,§4). **No per-variation
  RE-EXECUTION of the graph or the plan may be introduced anywhere.** §6.2's m50 evaluator-side
  weight loop inside ONE fill node is not such a re-execution. §5.2b's single-read witness is the
  mechanism witness for this requirement.
- **§7.2** The frontend owns `(output, label) → **node id**` — NOT `→ position` — and derives
  `node id → position` as **the rank of that record id in the DEDUPLICATED list of marked record
  IDS** (`list(dict.fromkeys(a.node_id for a in outputs))` over the outputs it passes to
  `compile_ir` — the dedup is over ids, since `Array` is unhashable), so **many labels MAY
  resolve to one position and the unpacker replicates that value**. The operand is
  bound to that list, not to the compiled output list: `GraphStore::mark_output` de-duplicates on
  the REDUCED store and `evaluate_ir` returns one value per reduced output, in first-occurrence
  order over the DISTINCT record ids — compiling two structurally identical outputs returns ONE
  value, so a RAW index into the marked list overruns the value list whenever a duplicate id
  precedes a later one. The deduplicated frontend list matches the value list element for element
  on every program m48 admits: the two disagree only when the OPTIMIZER merges distinct record
  ids, which the shortfall guard below refuses. (A
  positional `(output, label) → position` map would mis-assign labels on exactly the case §1.2
  mandates: a label structurally equal to nominal.) The frontend unpacks into the §6.1 named
  mapping through §6.1a's bound unpack verb.
  **THE SEAM THAT MAKES THE COMPILED ARTIFACT REACHABLE IS BOUND HERE, AND IT IS AN m48
  IMPLEMENTATION TARGET.** Two binding requirements need that artifact at a site that does not
  have it: this section's optimizer-merge refusal (below), which compares distinct compiled
  outputs against distinct marked record ids inside the group-plan builder; and m49's §8.2(i)
  `variation_labels`, a `_PartitionReduce` field keyed on POST-REDUCTION ids from the same
  compile. (§6.1c's index-based `layout` is not one of them: `plan()` already holds the marked
  Arrays as `fill_nodes`, and their ids, before it builds `layout`.)
  `aggregate_plan(*outputs, reduce, combine, empty, externals, backend, steps_per_file,
  partitions)` compiles internally
  (`compiled = compile_ir(session, *outputs)`) and immediately constructs the frozen dataclass
  `_PartitionReduce`. Binding: **`aggregate_plan` gains ONE pinned seam (exact spelling pinned at
  m48 freeze) that (α) lets the caller see the COMPILED ARTIFACT — the `CompiledGraph` itself,
  not merely a list of output ids — before the worker closure is CONSTRUCTED, and (β) carries
  per-plan variation metadata onto that closure as an additive field (m49's `variation_labels`,
  §8.2(i)).**
  **(β) IS THE HOOK'S RETURN CHANNEL, NOT A CALL-TIME PARAMETER** — the artifact (β)'s payload
  keys on is produced INSIDE the call, so no caller-side input can carry it. Binding: **the hook
  is called with the `CompiledGraph` before the worker closure is constructed, and its RETURN
  VALUE (the per-plan variation metadata, or `None`) is attached to the shipped closure as the
  additive §8.2(i) field.** m48's (α) anchor asserts that a returned payload reaches the closure
  (with a dummy value).
  **The field's TYPE is bound ONCE, in §8.2(i), as `tuple[…, …] | None` defaulting to `None`, and
  the m48 dummy is the empty tuple `()`** — a well-typed NON-DEFAULT value against §8.2(i)'s
  declared type (`graphed`'s mypy scope is `files = ["python"]`, so no gate checks it, R0.4a).
  **The field therefore EXISTS from m48**, which is where its one-time journal churn lands —
  see §7.3.
  **The seam is ADDITIVE and the artifact is the `CompiledGraph`.**
  *Additive*: the contracts of the existing `reduce`/`combine`/`empty` parameters are UNCHANGED —
  frozen m5 passes them as plain callables
  (`tests/frozen/frontend/m5/test_aggregate_plan.py`). The seam is a NEW optional keyword/hook —
  `on_compiled(compiled)`-shaped — beside the existing parameters, the same additivity discipline
  §8.1, §8.2(i) and §9.2 take on shipped surfaces.
  *`CompiledGraph`, not ids*: the merge refusal needs only the COUNT of distinct compiled outputs
  (`GraphStore.deserialize(compiled.ir).outputs()`), but m49's `variation_labels` keys on
  `(reduced_node_id, member_index)` via the m49 accessor answering "for the reduction that
  produced a given compiled artifact" (§8.2(i)) — a bare id list cannot produce that, and §8.2(i)
  binds the map as an additive `CompiledGraph` field populated at m49, so the ONE-argument hook
  shape m48 freezes needs no widening at m49.
  `plan()` MUST NOT compile a second time: the §3.3 anti-quadratic budget is written for ONE
  reduction of the variation-expanded graph. **That rule is knowingly left UNANCHORED and rides an
  R0.11 implementer-report measurement instead (the measured compile count for one `gh.plan({…})`
  call)** — the same treatment §1.1 gives its `"1e1000000000"` rule. **The instrument is bound,
  because the obvious one measures nothing**: both real call sites bind `compile_ir` into their own
  module namespace with a `from`-import, so a spy installed at the DEFINITION site
  (`graphed.execute`) intercepts neither and any "at most one call" assertion written against it
  passes vacuously. The measurement patches the two IMPORT-SITE bindings —
  `graphed.aggregate.compile_ir` and `graphed_histogram.boost.compile_ir` — and reports the count
  for one `gh.plan({…})` on a varied program that does NOT trip the merge refusal below; the
  builder's per-output re-compiles are on the refusal path, which is about to raise.
  The seam is a function
  signature, not a schema, so m48's §7.2 schema-absence anchor (below) is untouched by it.
  **Each half is anchored in the repo whose source it is** (the seam is new `graphed` source in
  `python/graphed/aggregate.py`, while the fill-shaped consumers' anchors live in
  `graphed-histogram`, whose frozen suite does not count toward `graphed`'s
  diff-coverage-from-the-frozen-suite gate): **(α) carries a `graphed`-side m48 anchor over an
  UNVARIED `aggregate_plan` build** (§10/m48), and **(β)'s return CHANNEL is anchored at m48 WITH
  (α), while (β)'s per-plan PAYLOAD is anchored at m49 alongside §8.2(i)** — until m49 the field
  is a pass-through with a default, not unreachable source. **The §8.2(i) FIELD DECLARATION is
  therefore an m48 target and m49's `§8` target line excepts it** — both target lines say so
  (§10). The same node-id rule governs §6.4f's widened write-path unpack (§6.4f).
  **A SECOND collapse mechanism exists that record-time identity cannot see, and m48 REFUSES
  rather than mis-slices.** The M4 reducer also merges **distinct** record ids (commutativity over
  `SYMMETRIC_OPS` plus the identity tokens `x + 0.0` / `x * 1.0`): two `Histogram.fill`s
  differing only in `weight=[w]` versus `weight=[w * 1.0]` record distinct fill nodes yet compile
  to ONE output — and §1.1's stringified-float families make `variations={s: w * float(s)}`,
  which contains a literal `w * 1.0` member, a natural spelling. The sound key is the
  record→reduced map, which does not exist until m49 (§8.2(i)). Binding for m48: **on the VARIED
  UNPACK PATH — the group-plan builder (`plan()`), NOT `compile_ir` and NOT `aggregate_plan` —
  and over a VARIED program only**, the builder compares the number of DISTINCT compiled outputs
  (`GraphStore.deserialize(ir).outputs()`) against the number of distinct record node ids it
  marked and, on a shortfall, raises a `graphed` error naming the outputs and labels involved
  plus the workaround — spell a label whose value equals another's with the SAME expression
  (`variations={"1": w}`, not `w * 1.0`), which routes it through §1.2's record-time dedup path
  and is supported. It MUST NOT slice on a shortfall (the mis-slice surfaces as an opaque
  worker-side `IndexError`). **m48's scoping — one consumer, varied programs only — is a stopgap,
  and m49 widens the refusal to its CLASS: every consumer that unpacks compiled outputs against
  marked fill nodes, on every program.** The premise the stopgap rests on ("unvaried programs are
  unaffected") is false on both members, and they fail differently, which is why the class and not
  one member is what gets fixed. On the GROUP-plan builder a merged unvaried program mis-slices and
  dies in the worker with exactly that `IndexError`. On `Histogram.plan()` — one histogram whose own
  staged fills merge, reduced by `_SumFills`, which iterates its fills rather than indexing them —
  nothing raises at all: the shortfall silently UNDER-SUMS, dropping a whole fill and returning a
  plausible, physically wrong histogram. That is the silent miscompilation §5.4 itself calls worse
  than refusal, and it is reachable from public API. Neither is covered by a frozen test (m48's
  positive control drives `compile_ir`/`evaluate_ir` directly, with no fill and no plan, so it
  reaches neither unpack). m49 therefore installs the same shortfall check on both consumers, with
  the message's label list dropped where there are no labels to name. A merge-FREE program of either
  shape is untouched — the m49 anchors carry that as their positive control — and the refusal stays
  BUILDER-side, never in `compile_ir` or `aggregate_plan`. Lifting the refusal
  into full support (replicating through §8.2(i)'s map once it exists) is NOT scoped in m48–m51
  and is parked in §11.
  `ExecResult`/`Plan`/monitor **schemas** do not change in m48–m50 (per-variation monitor events:
  Phase 2, the defaulted-field trick documented — the `store.py` precedent); the absence is a
  frozen m48 anchor (§10), worded over the schema KEY SETS of `Plan`, `ExecResult`, and
  `TaskEvent` (the monitor payload) asserted against LITERALLY SPELLED expected sets, never
  against a sibling unvaried run (a varied-vs-unvaried comparison is equal by construction, even
  after an implementer adds a field — the same wording discipline as §6.3's params key set), and
  not over plan bytes. §8.2(i)'s added `_PartitionReduce` field leaves the public schemas
  untouched but *does* change the shipped worker closure — and wherever that closure is wrapped
  for checkpointing it is embedded as an opaque cloudpickle `OpSpec` whose bytes feed
  `identity()` and therefore `task_id` (`python/graphed/core/plan.py`). **That wrap is a CALLER
  step, not something `aggregate_plan` performs**: `aggregate_plan` returns a
  `graphed.core.execution.Plan` whose `process` is a plain callable with no `identity()` and no
  `task_id`; `task_id` lives on `DurablePlan`/`DurablePlanV2`, and no `Plan → DurablePlan` bridge
  ships. See §7.3 for the churn that causes and for its exact scope.
- **§7.3 (Checkpoint semantics, documented honestly and anchored.)** Within one plan, resume works
  per-partition exactly as today (the N-variation composite partial is the journal unit) — m49
  freezes an interrupt/resume test over a varied graph whose result is byte-identical to an
  uninterrupted run. **The fixture's plan construction is bound**, because a varied aggregate
  graph does not reach the checkpoint runner on its own: `run_resumable` takes a `DurablePlan`
  (it calls `plan.process.resolve()` and `plan.task_id(part)`,
  `python/graphed/checkpoint/runner.py`) while `aggregate_plan` returns a plain `Plan` (§7.2), so
  the m49 fixture builds the `DurablePlan` explicitly — **BY VALUE:
  `DurablePlan(ir=compiled.ir, process=OpSpec.from_callable(plan.process), …)` over the plan
  `aggregate_plan` actually returned**. The m8 `OpSpec.from_ref` pattern
  (`tests/frozen/checkpoint/m8/analyses.py`) stays the documented USER idiom but is NOT the
  fixture construction: under `from_ref` (`identity()` = `b"ref\0" + ref`) the closure's fields
  are not in the plan bytes at all, so the §8.2(i) determinism anchor could not see them.
  **The fixture's closure operands (the `PartitionedSource`, the reduce/combine/empty callables)
  MUST be module-level definitions in an importable module**: a `__main__`-defined dataclass is
  pickled by value and cloudpickle-digests differently across `PYTHONHASHSEED` values, so the
  anchor would be red against a correct implementation. The same clause governs the §8.2(i)
  plan-byte determinism anchor (§10/m49). Across plan revisions, adding/removing a variation
  changes the IR and therefore **every** `task_id` — no cross-revision reuse. This limitation
  MUST be documented in the user docs and design.rst — naming the canonical invalidating edit
  from the exemplar workflow: toggling the expensive shift class on or off between runs (the
  `skip_obj_systematics` pattern, lit §ewkcoffea-confirmed) rebuilds the IR and invalidates the
  whole cache. **A third invalidation class is a label RENAME, documented alongside the other
  two**: §1.2's no-recompute property holds at the IR/interning level (its own m48 anchor freezes
  it) but NOT at checkpoint granularity from m49 onwards for a journal whose `process` spec
  embeds the worker closure BY VALUE — §8.2(i) puts label STRINGS into `_PartitionReduce`, and
  `task_id = sha256(_TASK_DOMAIN, ir, process.identity(), partition_bytes)` with an opaque
  `OpSpec.identity()` returning the cloudpickle blob itself, so a pure rename leaves the IR
  byte-identical and still changes those `task_id`s. Under the documented `OpSpec.from_ref` idiom
  a rename invalidates nothing. State the scope explicitly in the same doc paragraph: §1.2's
  no-recompute property is about the graph, not the checkpoint cache.
  **One-time churn on landing m48, SCOPED**: §7.2's (β) return channel forces the additive
  §8.2(i) field onto `_PartitionReduce` at **m48**; adding the field changes the pickled instance
  state and therefore, through the opaque-`OpSpec` chain above, every by-value `task_id` — once,
  at m48, *unvaried* programs included (the field is unconditional). **m49 only POPULATES the
  `_PartitionReduce` field**, which churns nothing further for unvaried programs (their value stays
  the `None` default). The m49 artifact field is a separate, second churn, on the write path —
  below. **It is NOT "every existing journal"**: the documented checkpoint idiom embeds the
  user's module-level functions BY REFERENCE (`process=OpSpec.from_ref("myanalysis:hist_chunk")`,
  `docs/checkpoint/design.rst`; the frozen m8 fixtures do the same), for which the added field
  changes nothing; by-value journals exist only where a caller built the `DurablePlan` itself
  through `OpSpec.from_callable(plan.process)`, and `graphed-executors/src` has no
  `task_id`/`DurablePlan` references at all. Document the churn WITH that scope.
  **The WRITE path churns no SHIPPED journal**: §6.4f widens `_WritePart.__call__`'s single-output
  unpack, but `graphed.write.write_plan` builds `Plan(process=write_part, …)` — the same
  plain-callable `Plan` — so nothing that ships today is invalidated. Where a caller wraps a
  write closure by hand (`OpSpec.from_callable(write_part)`), the m48 churn scope above applies —
  **and so does a SECOND one-time churn at m49**, because `_WritePart` embeds the whole
  `CompiledGraph` by value and §8.2(i) adds a field to it. Same shape as m48's, same scope, same
  documentation duty, and unconditional: a dataclass field is in every instance's pickled state
  whatever its value, so no unvaried program escapes it and the m49 artifact also grows by roughly
  an entry per record node. Both churns are documented together, in m50's docs anchor.
  Stage-granular content addressing is the named
  Phase-2 fix (§11). Blob storage stays content-deduped (`store.py`).
- **§7.4** Retry/dead-letter stay partition-atomic; docs state that one poisoned variation
  dead-letters the partition's whole composite (`runner.py`); the dead-letter surface names the
  guilty label via the §8 StageError (asserted inside the §8.2 frozen test). **No dead-letter edit
  is an m49 target**: the descriptor's `error_message` is `str(exc)`, which `StageError.__init__`
  makes `summary()`, so §8.1's added variation line reaches that surface with no further code. The
  descriptor's STRUCTURED half keeps its fixed key list and gains no variation key.

## §8 Debug, errors, provenance

- **§8.1** `StageError` gains `variation: str = ""` — constructor field, `summary()` line,
  `__eq__`/`__hash__` participation (`debug/errors.py`); pickling rides the existing `__dict__`
  `__reduce__` for free. Empty string = nominal/unvaried (backward compatible).
- **§8.2 (Label transport — mechanism bound.)** Under §1.2 the label is not in the IR and under
  §2.3 all sibling nodes share the user's source line, so op+frames cannot disambiguate labels.
  No existing channel carries a label to a worker-side error: `_PartitionReduce.__call__`
  (`aggregate.py`) calls `evaluate_ir` bare — no provenance, no node map, no `StageError`. **The
  mechanism is NEW work, in the parts below, all m49 targets** — `evaluate_ir` has no lowering to
  attribute against. The nearest prior art is `graphed.debug.runner`, whose `_stage_error` builds
  the same object per node from a `LoweredGraph` and already runs inside a worker process in the
  frozen m7 executors suite; (iii) models its attribution on that, over the reduced ids instead.
  (i) *Transport*: the `variation_labels` field on the worker closure (`_PartitionReduce`,
  `aggregate.py`) — added at m48 as a defaulted pass-through (it is §7.2's (β) return channel),
  populated at m49 — a sorted association list whose **ENTRY LAYOUT is bound**, because a producer
  in one repo and a consumer in another share it:
  `((reduced_node_id, member_index | None), (labels, frame))`, one entry per key the map covers,
  `labels` a sorted tuple of strings — **possibly EMPTY, which is how a key no non-nominal label
  reaches is carried** — and `frame` the user source location as plain string/int data. Entries sort
  on `(reduced_node_id, -1 if member_index is None else member_index)`; a bare `sorted()` over the
  keys is a `TypeError` the moment one reduced id carries both an indexed and a `None` entry.
  `member_index`
  exists because a universe's chain collapses into a Stage whose members are evaluated inline
  (`execute.py`). **ONE field carries both payloads** — the labels of (i) and the provenance of
  (ii) — so §7.3's churn scope (one field, once, at m48) stands; nothing else on the closure may
  grow. Every value in
  it is **ORDERED and SORTED, never a `set`/`frozenset`**: a frozenset pickles in hash order, so the
  closure's cloudpickle bytes would vary with `PYTHONHASHSEED` and feed `OpSpec.identity()` →
  `DurablePlan` fingerprints (`core/plan.py`), violating §3.2 and killing cross-run checkpoint
  reuse. It is an additive dataclass field, so `Plan`/`ExecResult` schemas stay untouched (§7.2).
  **The shipped ANNOTATION is m48's `tuple[Any, ...] | None`, and m49 does not narrow it** — the
  structure above is the binding, and the sorted-tuple rule is anchored by test (the producer anchor
  and the plan-byte determinism anchor, §10/m49), not by `mypy --strict`, which cannot see through
  `Any`. It is keyed on **POST-REDUCTION node ids** from the same `compile_ir` call that produced
  the shipped `ir`; record-time ids are wrong because the reduction re-indexes.
  That key space requires a **record→reduced correspondence that no reduction pass survives today,
  and building it is an explicit m49 Implementation Target in `graphed-core`.** The naive reading —
  "return the `remap` vector `dead_code_elimination` discards" — is wrong: DCE is only the FIRST of
  four re-indexings (`reduce_with_mode`, `src/optimizer/mod.rs`), and the `member_index` half is
  created by the LAST one, stage fusion. Binding, and this is the design decision the accessor
  turns on:
  **each pass returns the correspondence it already computes internally, and `reduce_with_mode`
  composes the four into one record-keyed map.** DCE and CSE each already build a local `remap`
  vector; stage fusion already knows each node's component and its position within the component's
  sorted member list. The one pass that emits nothing is `canonicalize`, which sits behind the
  swappable engine boundary and whose answer is not derivable from outside — equality saturation
  decides which node represents its class. **`RewriteEngine::canonicalize` therefore returns the
  canonicalized graph PLUS a total `node_map` from input node index to the index of its
  representative in that graph.** The map is a plain index vector, so the boundary stays egg-free
  and Phase-2-swappable; DCE and CSE stay outside the engine; the engine's semantics and outputs are
  unchanged, so §3.3's benchmark and §3.2's determinism gate see the same reduced graph they see
  today. It rides on the artifact as an **additive `CompiledGraph` field**, absent at m48, populated
  by `compile_ir` at m49 — the same additive-field shape §2.5 takes for its diagnostics channels,
  with the same scoping note (m48's §7.2 schema-absence anchor is worded over
  `ExecResult`/`Plan`/monitor, not `CompiledGraph`).
  **This field is the SECOND structure two repos share, so its shape and its owner are bound here,
  beside the closure's.** It carries two halves: the composed map
  `record_node_id -> (reduced_node_id, member_index | None)`, absent for a record id DCE dropped;
  and a per-KEY frame association list in (i)'s key order, `((reduced_node_id, member_index | None),
  frame)`. **`compile_ir` owns both and applies (ii)'s tie-break as it builds the second** — it is
  the one place holding the map and `Session._provenance` together, and that dict is `graphed`-
  private, so the tie-break never runs across a repo boundary. The `graphed-histogram` hook READS
  the map (to fold its cone walk onto keys) and COPIES the frames; it computes neither.
  **The field is unconditional; its one-time cost is §7.3's.** Consequence: **m48's (α)
  hook signature — ONE argument, the `CompiledGraph` — stays sufficient at m49 and MUST NOT be
  widened**; the hook reads both halves off the artifact it already receives.
  **BOTH reduction paths carry it.** `compile_ir` reduces through `GraphStore.reduce_with_outputs`
  or, for the public `Session(incremental=True)` configuration, through
  `IncrementalReducer::finalize`, which first translates original-arena ids through its own
  canonical map and only then runs the four passes. The incremental path composes that map in front
  of the four, so the accessor answers in RECORD ids on both; an accessor built on the one-shot path
  alone silently mis-keys every incremental program.
  **The PRODUCER of `variation_labels` is bound**: the hook supplier —
  `graphed-histogram`'s group-plan builder (`plan()`, `src/graphed_histogram/boost.py`), sole
  owner of the `(output, label) → record node id` map (§7.2) — computes it as: per label, walk that
  entry's record CONE (`session.walk` from that label's marked output — the whole cone, NOT §3.4's
  reachability difference, because the shared prefix is exactly where a fused failure raises), map
  every reached id through the accessor, and UNION the labels per resulting key — which is what
  makes the map set-valued. **`"nominal"` is EXCLUDED from that union, and a key no non-nominal
  label reaches keeps its entry with an EMPTY label tuple** — the NOMINAL-EXCLUSIVE region, since the
  whole-cone walk puts the shared prefix in every label's cone. It still has a frame, so a failure
  there is still attributed to the user's line, and it renders `""` per the rule below,
  which stays the single encoding of nominal/unvaried (§8.1); no key ever renders the literal string
  `nominal`. The producer pairs each key with the frame the artifact carries and returns the whole
  association list through §7.2's (β) channel.
  `graphed` itself never produces the CLOSURE field: §2.3d makes `compile_ir`/`aggregate_plan`
  refuse a `Varied` output. **The hook returns `None` when no key carries a label** — not when the
  payload is empty, which it never is (every key the map covers gets an entry, so an unvaried
  program's payload is a full list of all-empty-tuple entries). The predicate reads the LABELS, so it
  quantifies over the compiled program and not over the
  session, and an unvaried chain compiled beside a varied one in one session answers `None` like any
  other unvaried program. Hook PRESENCE classifies nothing at m49: §7.2's refusal reaches the
  artifact only through the (α) hook, so both builders supply one on every program.
  **What classifies is the ENTRY**: (ii) attributes a failure when the field carries an entry for
  the failing key, and re-raises the original exception untouched otherwise — today's behaviour, and
  what every unvaried program gets. So §7.3's closure-field scope holds verbatim (unvaried
  programs keep the `None` default), the M6 contract is extended where
  attribution exists rather than narrowed anywhere, and constructing a `StageError`
  with no frames is not a case the design admits. Consequence for §10: `graphed`'s m49 anchor
  witnesses the ACCESSOR (and the
  set-valuedness its key space must support); the LABEL association is witnessed in
  `graphed-histogram`'s m49 through the bound owner, never by a test that supplies its own hook
  and then asserts what it just computed (§5.2a).
  **§3.1 still holds** ("no optimizer SEMANTICS change"): read-only data the reducer already
  computes, composed and returned rather than dropped — no new `NodeKey`, no serialize tag, no
  rewrite arm. What widens is return types along the reduction call chain the target line names
  (the four passes, the engine trait, `finalize`, and `GraphStore`'s `reduce*` family, whose
  `Reduced`/report results the composed map travels in), not the IR and not what the reducer does.
  If the accessor is descoped the honest fallback is coarse, and is stated here rather than
  silently assumed: an "output-position" fallback is not implementable either (`evaluate_ir` is
  one flat loop with no per-node annotation, and outputs are selected only at the end), so
  without (iii) the only truthful attribution is **plan-wide** — the raised `StageError` carries
  the sorted UNION of all labels registered on that plan (rendered per the multi-label rule
  below), and the docs say so. (iii) is the keying event for both (i) and any fallback:
  descoping it removes per-label attribution entirely.
  (ii) *Attributed worker-side errors*, which do not exist today: the `evaluate_ir` call site in
  `_PartitionReduce.__call__` is wrapped so that a worker failure becomes a `StageError` **when the
  field carries an entry for the failing key, and re-raises untouched when it does not** (i); a
  `GraphedError` re-raises untouched on EVERY arm regardless of entry — it is already an attributed
  error, and §6.1d's blame parity (the plan path re-raises the guard's message verbatim) binds it —
  `StageError` needs the user's frames at construction, so with no entry there is nothing to build
  one from and today's behaviour is the correct behaviour. The frames ride the SAME field as (i),
  one entry per key, **re-keyed through the same accessor** by `compile_ir` (i), since
  `Session._provenance` is keyed by
  record-time ids and inherits the identical re-indexing problem. That re-keying is many-to-one —
  the reducer merges distinct record ids recorded at DIFFERENT user lines onto one key, including
  intra-stage, where `member_index` cannot separate them — so **the tie-break is bound: the LOWEST
  record id mapping to a key wins**, matching the driver-side house rule
  (`Session._provenance.setdefault`) and making the shipped frame a deterministic function of the
  graph rather than of dict order. It ships by value as plain string/int data, per (i)'s ordering
  rule.
  (iii) *Per-node failure attribution inside `evaluate_ir`* — **the keying EVENT, and a third
  m49 target**; without it (i) and (ii) do not compose: a wrapper around the call yields an
  exception carrying no node id, so it cannot index the map (i) ships. Binding: `evaluate_ir`
  gains an **optional attribution hook** (or an equivalent exception wrapper) annotating a
  failure with `(reduced_node_id, member_index | None)` at each evaluating dispatch point — the
  top-level node loop, the inline stage-member loop, and the External payload's evaluator; the
  SOURCE arm is deliberately excluded, since every label's cone reaches a source and attributing a
  load failure would render the union of every label — and `_PartitionReduce` maps that
  through `variation_labels`. This is a change to `graphed`'s **evaluation path** — not core,
  not the IR, not any schema — and it lands in `graphed`, so the m49 anchors are worded over the
  RESULTING `StageError`, never the wrap site. If (iii) is descoped, the plan-wide fallback
  above is what remains.
  **The map is set-valued, not a function** (§3.4: a node shared by `jes_up` and `jes_down` but
  not nominal appears in both impact sets), carried as (i)'s sorted tuple. Rendering is bound: a
  singleton renders as that label; a multi-label value renders as its labels sorted and joined
  by `,`; **an EMPTY label tuple — the only nominal encoding, since (i) excludes `"nominal"` from
  the union — renders `""` (nominal/unvaried, §8.1)**. A key
  with NO entry renders nothing: (ii) never builds a `StageError` for one.
  Frozen m49 anchors: a failure raised inside the `jes_up` universe on a worker across a process
  boundary re-raises driver-side carrying `variation == "jes_up"` AND the user's analysis line
  (M6 contract extended, not altered), and the dead-letter descriptor shows the label (§7.4);
  **plus a shared-node failure asserting the multi-label rendering** (a pick-one-arbitrarily
  implementation passes the single-label anchor alone) **and a NOMINAL-EXCLUSIVE-node failure in the
  same varied program asserting the empty-tuple rendering** — a key reached only from the nominal
  cone — a nominal-branch-exclusive USER op, which the m6 house pattern can poison; the
  builder-emitted nominal sibling fill cannot be — `variation == ""` WITH the user's line, so an
  implementation that renders it `"nominal"` or skips the wrap for it is red. Both ride the
  cross-process bullet's home, `graphed-executors`' flat `tests/frozen/m49` (§10/m49).
- **§8.3** Per-node provenance needs no new machinery (§2.3): varied nodes record at user op
  lines. `to_dot`/debug labels remain readable; the impact-set API (§3.4) is the "which nodes
  belong to which label" view.

## §9 Preservation and introspection

- **§9.1** `graphed.labels`/`graphed.universe`/`graphed.nominal` (§2.2),
  **`graphed.context_of(array)`** (the §2.3e context handle carried by an `Array`/`Varied`, `None`
  when context-free; read-only; m48, spelling pinned at m48 freeze),
  **`graphed.unify_contexts(*handles)`** and **`graphed.reindex_to(value, ctx)`** (the §6.1d
  lineage seams — most-derived-or-divergence-error over context handles, and an ancestor value
  re-expressed in a context's row space across §6.1d's link kinds; read-only; both m48, spellings
  pinned at m48 freeze),
  **`graphed.weight(ctx)`** (the context's ambient weight as a `Varied`, `None` when nothing is
  registered; read-only — it returns the registry's current `Varied`, it does not mutate; m48;
  the readable surface §6.4b's stored varied factors presuppose),
  `graphed.variations(ctx)` (per-name listing of a context's registered variations, their tags
  and kinds — **the KIND vocabulary is exactly two words: `"weight"` for a §2.1 overload-(b)
  registration and `"shift"` for an overload-(c) one (overload (a) is loose and reaches no
  context), and the return type is `{name: {tag: (kind, value | None)}}`, spelling pinned at m50
  freeze** — and, for numeric tags (canonical e-form `m?\d+(em\d+)?`, `5em1` → 0.5; plus the
  datacard p-form `m?\d+(p\d+)?`, `2p5` → 2.5), the parsed float value: the ordering handle for
  σ-scan/envelope plots, since §6.2's sorted axis is lexicographic),
  **`graphed.selection(ctx)`** (the `Varied` mask that derived a context from its parent, `None`
  for a root context — the §6.4a bridge that makes the m51 skim sink reachable from the §2.6
  context idiom; m51.
  **On a universe/nominal-derived context**, per §2.2 the verb returns that label's member of the
  argument's own selection — an unvaried `Array`, not a `Varied`, living in the GRANDparent's row
  space (`None` when the argument is a root context).
  **On a `graphed.vary`-derived context**: a `vary` link is an IDENTITY link (§6.1d link kind (2)
  — the row space is unchanged, only registrations differ), so the verb returns the selection of
  the nearest ancestor reached across `vary` identity links only — it skips any number of `vary`
  links and answers as of the first non-identity link, `None` when that walk reaches a root
  context),
  **the §6.1a RESULT UNPACKER** (`graphed_histogram.unpack(value) -> dict[str, bh.Histogram |
  dict[str, bh.Histogram]]`-shaped, over the executed plan's flat slot-keyed value ALONE, choosing
  per output from the SLOT KEY FORM — the three key forms are disjoint and per output,
  §6.1a/§6.1c; read-only; m48, spelling pinned at m48 freeze),
  **a per-label FILL-NODE accessor** (`graphed_histogram.fill_nodes_by_label(h) -> dict[str, Array]`
  -shaped, or an equivalent labelled return from the §6.1c group API; the importable surface
  behind §4.3's bound extraction — §7.2's `(output, label) → node id` map is owned, not exported,
  and today's public `Histogram.fill_nodes()` is unlabeled; read-only; m48, exact spelling pinned
  at m48 freeze),
  **`graphed.member_of(value, label)`** (§2.4's resolution rule — the container's own member for
  the label, else its `"nominal"` one, and the value itself when it is not a `Varied`; the two m49
  verbs below both range over the §2.4 label UNION, which §3.4 explains `graphed.universe` cannot
  serve. It is defined in `varied.py` today and re-exported into `accessors.py`, but not out of the
  package, so m49 exports it; read-only; m49, spelling pinned at m49 freeze),
  **the §3.4 impact API** (`{label: tuple[int, ...]}` of that label's sorted record node ids, over
  the per-label output CONTAINERS — `Sequence[Varied] | Mapping[str, Sequence[Array]]` (the
  labelled mapping is what the fill-node accessor above returns), WITHOUT `source_nid`, §3.4;
  read-only; m49, spelling pinned at m49 freeze),
  **the §5.3 per-label projection-stats verb** (`{label: tuple[str, ...] | None}` of that label's
  sorted read set — `None` meaning "read every column", `read_columns`' own conservative answer,
  §5.3 — over `Sequence[Varied] | Mapping[str, Sequence[Array]]` plus `read_columns`'
  `source_nid`; read-only; m49, spelling pinned at m49 freeze), and a
  plan-level listing of `{output: [labels]}` **(m50; spelling pinned at m50 freeze; its own frozen
  anchor in `graphed-histogram`'s flat `tests/frozen/m50` (§10/m50), separate from m50's
  `inspect()` test — that test covers a bundle's text rendering, not this mapping)** — **and it
  answers UNIFORMLY over both modes, which is bound because the slot key alone cannot serve it**:
  an axis-mode output contributes one `(output, None)` slot whose key carries no label (§6.1c), so
  the listing reads that output's labels from the fill's declared variation label set, which the
  builder holds while it builds the layout, and never by decoding the per-slot spec string. The
  caller does not have to know the mode; every varied output — sibling or axis — maps to its labels
  in §2.4 order, and §6.2(i-bis)'s nominal-first-then-lexicographic rule governs
  `graphed.labels(h)` on a RESULT histogram, a different surface that does not reach here — constitute the introspection surface
  (RDF `GetVariations` analogue); `inspect()`'s own label listing stays anchored in m50's
  `inspect()` test (§9.2).
- **§9.2** Preservation: a bundle built from a variation-expanded graph reproduces **all** labels
  from ONE bundle, in the m9 comparison form (per label,
  `np.array_equal(reproduce(bundle)[label], build_time[label])`,
  `preserve/m9/test_reproduce.py`), and `inspect()` lists the labels without executing. Today
  `build_bundle(root, *, session, value, weight=None, …, histogram=None, …)` is strictly SINGULAR
  (and raises unless `weight=` and `histogram=` are given together) and `reproduce(bundle)`
  returns a single array; m50 extends both: a varied bundle accepts a `Varied`
  `value=`/`weight=` (equivalently a per-label mapping) and `reproduce` returns
  `{label: array}`; **an unvaried bundle still takes bare Arrays and `reproduce` still returns a
  bare array** (backward compatible). **The bundled graph is the value/weight/`{name,bins,lo,hi}`
  TRIPLE the signature above already takes, NOT a histogram-terminal fill graph** — which is why
  `reproduce` yields a per-label count ARRAY and the m9 `np.array_equal` comparison applies
  unchanged. The triple carries no `External`, so no new preserve plugin is in m50's scope; the
  corollary is that the §6.2 axis-mode `Histogram` itself — its variation axis and storage — is not
  what a bundle round-trips, and widening the bundle to the fill graph is Phase 2 (§11). The
  MANIFEST gains a label channel, bound here — §1.2 keeps
  labels OUT of the IR, and today's `analysis.outputs` is the singular two-key record
  `{"value": int(value.node_id), "weight": None if weight is None else int(weight.node_id)}`, so
  nothing durable carries labels. Additive the way §8.2(i)'s field is: a VARIED bundle's manifest
  carries a per-label output map — `analysis.outputs` extended to
  `{label: {"value": id, "weight": id | None}}`, or an additive sibling key — **SORTED by label**
  so `canonical_bytes`' sorted-key serialization stays deterministic and the fingerprint stays
  stable; `FORMAT_VERSION` (today `1`) bumps with it, and an UNVARIED bundle keeps today's
  singular shape and version. Exact spellings pinned at m50 freeze. This replaces the m9 fixture's
  one-bundle-per-config pattern *additively*: existing m9 frozen tests are untouched.

## §10 Milestones (strictly ordered; m48 → m49 → m50 → m51 → m52 → m53)

Numbering: the executors repo froze m47 last. Frozen layouts by repo:

- **`graphed`** (frozen tree partitioned by package; `scripts/run-tests.sh` runs `frontend`,
  `numpy` and `awkward` one process PER MILESTONE dir): **`tests/frozen/frontend/m48`,
  `tests/frozen/awkward/m48`, `tests/frozen/frontend/m49`, `tests/frozen/awkward/m49`,
  `tests/frozen/checkpoint/m49` (new), **`tests/frozen/debug/m49` (new)**,
  `tests/frozen/preserve/m50`, **`tests/frozen/frontend/m50`, `tests/frozen/awkward/m50` and
  `tests/frozen/debug/m50` (new, for the m49 carryover anchors §10/m50 homes)**,
  `tests/frozen/awkward/m51`**, plus the §3.3 benchmark in `tests/frozen/core/m49` and
  **`tests/frozen/numpy/m51` for m51's numpy-backend refusal anchor** (§6.4f's numpy half is
  `graphed`-side source in `python/graphed/numpy/io.py`, and `numpy` is a `SPLIT_PKG`).
  **m48 gets a SECOND `graphed` tree because `ci.yml`'s REQUIRED `test-freethreaded` job collects
  `tests/frozen/frontend` WHOLE on 3.14t with only `pytest hypothesis numpy` installed** — it
  `--ignore`s `frontend/m40` for exactly this reason — so a `frontend/m48` anchor importing
  `graphed.awkward` reds that gate at COLLECTION. No required awkward-free job collects
  `tests/frozen/awkward`, `run-tests.sh` auto-globs its milestone dirs, and both `graphed` trees
  feed the same `--cov=graphed` gate, so the split costs no diff coverage.
  `tests/frozen/preserve/m50` hosts m50's preservation, docs **and frontend-introspection**
  anchors — the §9.1 `graphed.variations(ctx)` anchor and the §6.2(i-bis) narrowing-helper
  behaviour of `graphed.labels`/`graphed.universe` over a histogram object (frozen tests
  already import across package boundaries there).
- **`graphed-executors`** = flat `tests/frozen/m49`.
- **`graphed-histogram`** = flat `tests/frozen/m48`, `tests/frozen/m49` and `tests/frozen/m50`
  (m49 anchor (i) bindingly requires `tests/frozen/m49` here; m50's primary target §6.2 lives
  in this repo).
- **`uproot5-graphed-mvp` has NO frozen tree today** — its graphed tests are flat,
  ordinarily-named files directly under `tests/`. m51 **CREATES `tests/frozen/m51/`** there and
  the integrity rules bind it from freeze; the existing `tests/test_graphed_*.py` stay unfrozen.

**Basename uniqueness (binding, every repo)**: a duplicate top-level test basename is a pytest
collection ERROR wherever one process collects a flat tree with no `__init__.py` under prepend
import mode, and **the binding scope is the WIDEST pytest process any workflow runs, not the
narrowest**. `run-tests.sh` splits `graphed`'s `frontend`/`numpy`/`awkward` per milestone dir,
but the required free-threaded job collects **all of `tests/frozen/frontend` minus `m40`** and
**all of `tests/frozen/numpy` minus `m40`** in one process each: a `frontend/m48` basename must
be unique against every other frontend milestone but m40, and a `numpy/m51` basename against
every numpy milestone but m40. `tests/frozen/awkward` has no whole-subtree job, so any
`awkward/<mXX>` dir needs uniqueness only inside itself. Everywhere else the scope is the whole
tree: `graphed`'s `core`, `debug`, `preserve` and `checkpoint` subtrees, `graphed-histogram` and
`graphed-executors` (each runs `pytest tests/frozen` in ONE process), and `uproot5-graphed-mvp`.
The natural name for an anchor is routinely the colliding one, so the test-author walks the
scope before naming a file — regenerate it with
`find tests/frozen/<scope> -name 'test_*.py' -not -path '*/m40/*' -exec basename {} \; | sort`
(the m40 exclusion applies to the frontend and numpy scopes, which the gate `--ignore`s). Live
traps for anchors this plan places: `frontend/m5/test_aggregate_plan.py` against §7.2's seam (α)
anchor, `frontend/m5/test_read_columns_projection.py` against §5.3's m49 projection anchor,
`frontend/m3/test_array_surface.py` against §2.3a's parity gate, `frontend/m14/test_apply.py`
against §2.2 `Varied.apply`, `core/m4/test_benchmark.py`, `preserve/m9/test_reproduce.py` +
`test_inspect.py`, `checkpoint/m8/test_resume.py` — so use e.g. `test_varied_aggregate_plan.py`,
`test_varied_read_columns_projection.py`, `test_varied_array_surface.py`, `test_varied_apply.py`,
`test_variation_benchmark.py`, `test_varied_bundle_reproduce.py`, `test_varied_inspect.py`.

**Pythonpath**: any helper imported ACROSS frozen directories is added to that repo's
`pyproject.toml` `pythonpath` list (`graphed` already lists `tests/_corpus`;
`graphed-histogram` uses `pythonpath = ["src", "tests/frozen/m23"]`, `graphed-executors`
`["src", "tests/frozen/m7", …]`). A shared `vary` fixture module is expected and must be listed.
m48's §4.1 anchor reads `agc.correctionlib_json()` out of `graphed`'s frozen
`tests/frozen/preserve/m9`, so that directory joins `graphed`'s list.

**Vendoring, not `importorskip`**: `graphed` lists no `graphed-histogram` in any extra while CI
installs `.[dev]`, so the house pattern `pytest.importorskip("graphed_histogram")`
(`tests/frozen/preserve/m25/test_histogram_preservation.py`) would **SKIP in CI** — a skipped
headline gate is a silently discharged milestone contributing no frozen-suite diff coverage.
Binding: no frozen anchor in this plan is `importorskip`-guarded; an anchor needing both
packages is assigned to the repo that has them (the per-milestone splits below).
`graphed-histogram` has the fill sink but no corpus dependency and no reference JSONs (the
corpus wheel packages only `src/graphed_corpus`), so **m48 VENDORS the corpus into
`graphed-histogram` exactly the way `graphed` already does** — copy `graphed_corpus` + the
reference JSONs to `tests/_corpus/` and put that directory on `pythonpath`. Vendoring, NOT a
new dependency: `graphed-corpus` is not resolvable by name in this org's CI — the working
precedent pre-installs it from a git URL via a workflow env var before `pip install -e .[dev]`
(`graphed-executors .github/workflows/ci.yml`'s `CORPUS`); `graphed-histogram`'s workflow already
runs that preinstall shape for `graphed`/`graphed-executors` but carries no `CORPUS` entry.
Vendoring follows `graphed`'s own precedent and adds no cross-repo resolution surface. If
a future revision prefers the dependency route, it MUST bind the pair — dev-extra name PLUS the
env var and its `pip install` line in every job that runs the frozen suite.

**`uproot5-graphed-mvp` gates** (m51's ROOT half, §6.4f): the new
tree IS collected (`testpaths = ["tests"]`), but the only workflow that installs `graphed` and
runs the graphed tests is `.github/workflows/graphed.yml`, whose test step is
`python -m pytest -vv tests -m "not xrootd"` with **zero `--cov`**, on **ubuntu-latest only**,
CPython **3.11/3.12 only**, triggered `on: push: branches: [graphed-mvp]` + `workflow_dispatch`
(**not** `pull_request`); the repo has **no `[tool.mypy]` section** and no coverage config. As
configured, the DoD's ≥90% diff coverage from the frozen suite, `mypy --strict`, and
full-§A.5-matrix CI green (R0.5) cannot be discharged for that half. **Binding, as part of
m51:** (a) a `--cov` invocation over m51's new ROOT-side source with the ≥90% diff-coverage
gate, added to `graphed.yml` (the `graphed-histogram` `.github/workflows/ci.yml` shape);
(b) a `[tool.mypy]` config covering that new source AND `tests/frozen/m51` (R0.4a); (c) an
explicit statement, in m51's DoD record, of the CI matrix its DONE is keyed on for this repo —
either widen `graphed.yml` toward §A.5 or record the reduced matrix (ubuntu / 3.11–3.12) as the
accepted scope — and either add `pull_request` to the trigger or state that DONE is keyed on a
branch push. **(d) Cross-repo landing.** m51 lands as TWO INDEPENDENT PRs (graphed + fork). The fork's m51
scope is derived-column IR evaluation ONLY, using graphed's already-shipped IR API
(`compile_ir`/`evaluate_ir`/`Array`/`Session`, ≥m10) — NO m51-new graphed symbol
(`graphed.selection`/`select=`/`read_varied`, all awkward-side) reaches the fork — so the fork's
TEST_SANITY is collectible against `graphed@main` with NO `graphed.yml` repoint. Land graphed
first for tidiness. (A temporary `GRAPHED`-env pin — the m49/m50 precedent — is the fallback ONLY
if a future revision restores a variation-aware ROOT reading, §11.)

Each milestone runs the full §12 process. Frozen anchors listed here are the acceptance
skeleton the test-author starts from; the frozen m05/m4/m9/m23/m29 artifacts are **binding and
unchanged**.

- **m48 — `vary` frontend + weight path** (repos: `graphed` + `graphed-histogram`).
  Targets: §1; §2 incl. the §2.6 event context (**except §2.5's shift-after-weight ordering
  diagnostic — m49's, it needs §3.4's reachability cone, an m49 target**); §3.2; §4; §6.1 incl.
  §6.1d ambient fills (**§6.1b's arity anchor is m49's** — a COUNTED `1 + |S| + |W|` assertion
  needs the shift path (§5, m49); m48's varied-AXIS and varied-`sample=` programs are anchored
  for fold order and result shape, not arity) **except §6.1c's AXIS-MODE slot, which is m50's
  with §6.2** (m48 implements only the sibling `{(output, label): [indices]}` layout its
  anchors exercise); **§7.2, including its `aggregate_plan` SEAM** (`aggregate_plan` compiles
  internally in `python/graphed/aggregate.py` and takes pre-built closures; §6.1c's layout is
  derived from the DEDUPLICATED node ids of `plan()`'s own ordered `fill_nodes` list in
  `graphed-histogram src/graphed_histogram/boost.py` (§6.1c), not from the seam;
  §7.1/§7.3/§7.4 stay m49); **plus §8.2(i)'s `variation_labels` FIELD DECLARATION ONLY** —
  `tuple[…, …] | None = None` on `_PartitionReduce` (`python/graphed/aggregate.py`),
  unpopulated (it is §7.2's (β) return channel; the accessor, keying and population stay m49);
  §6.3; **§9.1 partially** — `graphed.labels`/`universe`/`nominal`/`weight`,
  `graphed.context_of`, `graphed.unify_contexts` + `graphed.reindex_to` (§6.1d's lineage
  seams), the per-label fill-node accessor, and `graphed_histogram.unpack` (spelling pinned at
  m48 freeze; m48's §6.1a anchor is worded over it). `graphed.weight` is m48's because the
  §2.1 stacking anchor and §6.4b consume it; m50's §9 target narrows to `graphed.variations` +
  §9.2; m51's carries `graphed.selection`. **§3.4 is an m49 target, NOT m48** (its frozen
  anchor lives in m49 and no m48 anchor exercises it — §4.3's impact-set cross-check is
  optional).
  **The anchor list is PARTITIONED into THREE trees by two rules applied in order: (1) any clause
  whose assertion requires a `Histogram.fill` lives in `graphed-histogram`'s flat
  `tests/frozen/m48`; (2) of the rest, any anchor that imports `graphed.awkward` — the gak
  enumerations and representatives, and any program built on an awkward-idiom fixture or backend —
  lives in `graphed`'s `tests/frozen/awkward/m48`; everything else in `graphed`'s
  `tests/frozen/frontend/m48`.** Rule (2) is the required awkward-free free-threaded gate (§10
  preamble), which on every push to `main`, every pull request and every `workflow_dispatch`
  collects `tests/frozen/core`, `tests/frozen/frontend` (minus m40) and `tests/frozen/numpy`
  (minus m40) WHOLE, one process each, and `tests/frozen/numpy/m40` in a fourth process (so
  numpy/m40 is INSIDE the gate, just separately collected), so **it binds every
  `graphed`-side frozen assignment in m48–m51, not m48's alone**: any later milestone's anchor
  in those three trees either stays awkward-free or gets its own `tests/frozen/awkward/<mXX>`.
  `core` is stricter than collection — a frozen m1 test asserts `"awkward" not in sys.modules`,
  so one awkward import anywhere in that invocation reds it. The
  corpus matrix anchors run against the corpus vendored into `graphed-histogram` (§10 preamble)
  and are not `importorskip`-guarded.
  Applied: **rule (2) takes the whole §2.6 event-context family** — its constructor
  (`gnano.events`-shaped) is awkward-idiom (§2.6), so every context-bound clause lands in
  `graphed`'s `awkward/m48`, §1.1's grammar and lockstep anchors and the §2.1 stacking anchor
  (base case and weight-form extension, with both §2.1(b) controls) among them — **together
  with** the §2.3d module-verb
  table (its idiom-package enumerations reach `graphed.awkward.__all__` and its floor is asserted
  over the UNION, so the table cannot be split), the gak-classification exhaustiveness gate,
  §2.3e's context-handle gate, the per-class gak representatives, §6.1d's lineage seams (they
  take context handles) and §4.1 correctionlib (fill-free, but `record_external` yields a payload
  descriptor only under `AwkwardBackend`). `graphed`'s `frontend/m48` keeps what needs neither
  `graphed.awkward` nor an event context, on numpy-idiom fixtures over the loose §2.1a `vary`:
  §1.2 label-out-of-identity, §3.2 determinism, §7.2 schema absence, §7.2's `aggregate_plan`
  seam (α) (the m5 call shape it extends is awkward-free), §2.2 `Varied.apply`, §2.3a's
  `Array`-surface parity gate, §2.3b's plain-Array entry points and §2.5's unreached-label
  diagnostic. `graphed-histogram` takes every anchor that needs a fill — the corpus weight matrix
  + its §5.2b read witness, §6.1a result shapes, §6.1c `.plan()` refusal, §6.1d ambient fills,
  §6.3 goldens, and §4.3's selection-invariance anchor (its operands are per-label fill nodes
  read through §9.1's accessor).
  **Straddling anchors are assigned explicitly — REPO-level; rule (2) then picks the `graphed`
  tree**: **(1)** §1.2's dedup clause — the arena-Δ /
  node-id / one-`compile_ir`-value half stays in `graphed`; the result-mapping half ("both keys
  present with ONE evaluated fill", read off `_GroupReduce`'s `{label: hist}`) goes to
  `graphed-histogram`; **(2)** §2.1 stacking reads through `graphed.weight(ctx)` (§9.1), which
  makes it frontend-observable — it stays in `graphed` and MUST use that accessor rather than a
  fill; **(3)** §1.2's §7.2 merge-guard clause: the VARIED-program refusal is fill-shaped
  (§7.2 binds the guard's SITE to `plan()` in `graphed-histogram src/graphed_histogram/boost.py`)
  and goes to `graphed-histogram`; its UNVARIED scope positive control
  (`compile_ir(s, b, b * 1.0)`) needs no fill and stays in `graphed`; **(4)** in the §2.6/§6.1d
  mega-bullet, the pure-frontend clauses (tag grammar, no-reserved-names, lockstep validation,
  data guard, lineage, the §2.6c ambient-registry re-indexing, op-level divergence and
  `vary`-construction divergence) stay in `graphed`, as do the frontend-observable HALVES of
  the two split clauses (`graphed.labels(ctx)` reports the shift labels;
  `graphed.universe`/`nominal` return a context that is a CHILD of the argument); the
  fill-shaped clauses (ambient fill on a per-object quantity, the manual-broadcast reference —
  all three of its assertions, incl. the contexted-but-unvaried one — the execution-time
  refusal, divergent-lineage AT THE FILL, §6.1d's link-kind-(1) ancestor-VALUE re-indexing,
  `unweighted=True`, the four-way fold order, the fill-label-superset half of the
  `graphed.labels` clause and the projected-VALUE half of the universe/nominal clause) go to
  `graphed-histogram`.
  Frozen anchors:
  - Corpus **weight**-variation references through the frontend — ttbar 4j1b/4j2b ×
    {nominal, btag_up, btag_down} + ttgamma {nominal, pho_up, pho_down}, the weight-variation
    subset of the 15-reference matrix — `fingerprint(h) == ref["fingerprint"]` and
    `bin_values(h) == ref["values"]` (the `m05/test_fixtures_reproduce.py` comparison form).
    Traps: the ttgamma flat SF is a constant — spell it
    `gak.full_like(<a per-event Array>, sf)` or as arithmetic on such an Array; no constant
    Array without a shape donor exists (§4.1, §11). The corpus rounds the observable to 6
    decimals BEFORE the fill — inline `np.round(ak.to_numpy(<observable>), STABLE_DECIMALS)` in
    `tests/_corpus/graphed_corpus/analyses/systematics.py` — and the view after (`_round_hist`
    there; `histograms.py`'s `bin_values`/`fingerprint` round again): the recorded program
    re-expresses the pre-fill rounding as **`np.rint(x * 1e6) / 1e6`, a numpy ufunc dispatched
    through `Array.__array_ufunc__`** — neither `gak` nor `graphed` exposes `rint` or
    `round(x, decimals)`, and `np.round(x, 6)` records a `field` access and raises — and the
    comparison rides `bin_values`/`fingerprint` — **raw-view bit-identity vs the references MUST
    NOT be asserted** (driver-side rounding absorbs per-partition summation-order differences). The
    b-tag SF's operand is the **pt-CUT** jets (`sel.Jet[sel.Jet.pt > 25]`, §2.6 sketch note
    (iii)), not `sel.Jet`.
  - §4.3 structural selection-invariance, in the binding form: **the selection cone's node ids
    are identical across all weight labels** — per label, `reachable(fill_node[label])` via
    `session.walk` (`python/graphed/session.py`), `fill_node[label]` from §9.1's per-label
    fill-node accessor (`graphed_histogram.fill_nodes_by_label(h)`-shaped, spelling pinned at
    m48 freeze), asserting **that the per-label fill nodes' NON-WEIGHT input ids agree with
    nominal's** — `store.nodes()[fill_id]["inputs"][:n_axes]`, identical ids ⇒ identical cones
    by interning (§4.3). Not the impact-set-subset or intersection wordings (§4.3); the
    optional reachability cross-check is frozen only in §4.3's discriminating shape. m05
    equal-counts as sanity.
  - **§1.2 label-out-of-identity** — **for a varied program in the DEFAULT SIBLING lowering**
    (§1.2's §6.2 carve-out makes both clauses false by design in m50's axis mode; every
    sibling-exposed anchor elsewhere carries this scoping): no node's `name` or `params`
    contains any label string, AND renaming every label leaves `compile_ir(...).ir`
    byte-identical — which subsumes any token clause and reaches the fused `stage` nodes'
    members, which the record-time store never carries. House pattern for reaching that store
    from a frozen test: `s._store.nodes()`
    (`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py`).
    Plus the **dedup witness §5.2a defers to this bullet**: two labels whose members are
    structurally identical give arena Δ = 0, the same node id, and — per §7.2 — both keys
    present in the result with ONE evaluated fill. Plus the **NON-record-time collapse case
    (§7.2)**, which the Δ = 0 / same-node-id clauses cannot reach: a label whose member is
    `nominal * 1.0` records a DISTINCT node id and is merged by the OPTIMIZER — assert §7.2's
    m48 guard: the VARIED program is REFUSED with a message naming the labels, not silently
    mis-sliced — with the SCOPE positive control alongside it, in `graphed` (needs no
    fill): an UNVARIED multi-output program whose outputs the optimizer merges
    (`compile_ir(s, b, b * 1.0)`, which returns ONE value) still compiles and runs exactly as
    today — the refusal is BUILDER-side, so this control stays true at m49 too, where §7.2 widens
    the refusal to every builder and every program.
  - **§6.1c `.plan()` refusal**: `.plan()` on a `Histogram` that is VARIED **or in axis mode**
    raises naming the group API (`_SumFills` would otherwise silently merge universes into a
    plausible-looking, physically wrong result). m48 exercises the varied arm; word the anchor
    over §6.1c's DISJUNCTION — not over "varied" alone, not over the fill-node count, not over
    the spec comparison (which decides only the axis-mode arm and has no m48-constructible
    fixture), and not scoped to sibling mode (§6.1c: the refusal covers both merge hazards).
    Positive control: `.plan()` on an unvaried **sibling-mode** `Histogram` still works (an
    unvaried AXIS-MODE one is REFUSED, §6.1c).
  - **§2.1 stacking**: `vary` on a target that already carries variations inherits those
    labels, adds the new ones, label order = inherited-then-new, the new label's member is the
    provided value's central universe, and each label differs from nominal in exactly ONE knob
    (the corpus b-tag-on-JES case, §2.1).
    **The base case's target is a LOOSE `Varied` (§2.1a)** — every other m48 `vary` anchor
    targets an `Array` or a context, so §2.2's pairing branch and §2.1(a)'s pass-through would
    otherwise ship unwitnessed: assert `type()` of the result carries the nominal member's
    idiom, and that the inherited members are unchanged.
    **Extended to a WEIGHT `vary` on a context already carrying SHIFT labels** — the case the
    corpus matrix turns on and m48's weight-only matrix cannot reach: assert the **inherited**
    shift label's ambient member is `old_ambient[L] × factor[L]` — the factor evaluated in
    THAT label's universe, per §2.1's per-overload stacking rule. **The registered factor MUST
    be NESTED** — a `Varied` whose members are themselves `Varied` over the inherited shift
    labels, the corpus spelling `graphed.vary(sel, "btag", btag_sf(sel.Jet[sel.Jet.pt > 25]),
    is_weight=True, …)` on a `Varied`-mask-derived `sel` (§2.1; a FLAT factor makes the one-
    and two-level readings agree and leaves §2.1's two-level rule unwitnessed). **The program
    MUST register an ambient weight on the PARENT context before that derivation** (the §2.6
    sketch's `pu`): §2.6c's re-indexing is what gives the ambient its own `jes_up` member, so
    without it `graphed.weight(sel)` is `None` (§9.1), the RHS's `old_ambient_jes_up` does not
    exist, and §2.1(b)'s composition is unwitnessed. The assertion is
    `graphed.universe(graphed.weight(sel2), "jes_up").node_id == (old_ambient_jes_up *
    graphed.universe(graphed.nominal(factor), "jes_up")).node_id`
    — **`.node_id` equality, NEVER a bare `assert` on the recorded comparison**:
    `Array.__eq__` RECORDS an elementwise op and `Array` defines no `__bool__`/`__len__`, so
    `bool(a == b)` is `True` for every operand pair. Node-id equality is sound by interning
    and frontend-observable; materializing both through `Session.materialize`
    (`python/graphed/session.py`) and comparing elementwise is the equally acceptable form —
    naming the ONE-LEVEL answer (the factor's own `"nominal"` member: the b-tag SF on
    unshifted jets) as the wrong result it discriminates against. Read through
    `graphed.weight(ctx)` (§9.1); needs no fill, so it stays in `graphed` — `awkward/m48` per
    rule (2), its fixture being context-borne.
    **Plus §2.1(b)'s ROW-SPACE positive control**: registering, on a DERIVED context, a factor
    computed from a value read at the PARENT is accepted and re-indexed to the derived row
    space per §6.1d's link kinds, so `graphed.weight(sel)` answers at `sel`'s per-label row
    counts (`Session.record_op` performs no length check, so without this the mismatch dies
    only at execution).
    **Plus §2.1(b)'s DESCENDANT negative control**: registering, on the ROOT context, a factor
    computed through a DERIVED context (`graphed.vary(events, "btag", btag_sf(sel.Jet),
    is_weight=True, …)`) is a CONSTRUCTION-time error naming both contexts and the DIRECTION
    (it is not divergent, and no re-indexing exists in that direction — a mask has no inverse,
    §6.4b). Both controls read through `graphed.weight(ctx)` and stay in that same tree.
  - **§7.2's `aggregate_plan` SEAM (α), in `graphed`'s `tests/frozen/frontend/m48`** (every
    requirement consuming the seam is fill-shaped and lives in `graphed-histogram`, whose
    frozen suite does not count toward `graphed`'s frozen-suite diff-coverage gate, so the
    seam needs a `graphed`-side anchor): over an UNVARIED multi-output program in the m5 call
    shape (`tests/frozen/frontend/m5/test_aggregate_plan.py`), the new hook fires EXACTLY ONCE
    and receives the `CompiledGraph` — the compiled outputs readable inside the hook as
    `graphed.core.GraphStore.deserialize(compiled.ir).outputs()`; `CompiledGraph` itself
    exposes only `ir`/`source_names`/`evaluate` (`python/graphed/execute.py`) and has no
    `outputs` attribute — and the resulting `Plan` runs to the same value as the same program
    built WITHOUT the hook (m5's own assertion as the positive control), with the existing
    `reduce`/`combine`/`empty` parameters passed as the plain callables m5 freezes (§7.2: the
    seam is ADDITIVE). **Plus the RETURN-CHANNEL assertion** (§7.2's (β)): a value returned
    from the hook — at m48 a dummy, **the empty tuple `()`**, a well-typed NON-DEFAULT value
    of §8.2(i)'s declared field type (`None` is indistinguishable from the default) — is
    carried onto the SHIPPED closure and is readable there (`plan.process`). **The READ-BACK
    ROUTE is named**: `Plan.process` is declared `Callable[[Partition, WorkerResources], R]`
    (`python/graphed/core/execution.py`), so the anchor reads the field off the CONCRETE
    closure type `graphed.aggregate._PartitionReduce` via a narrowing `isinstance`/cast (the
    declared type has no `variation_labels`, and the `isinstance` is also the runtime
    discriminator of the concrete closure). "Before the worker closure exists" is NOT asserted
    — the hook has no handle on the closure; the return channel is what makes the ordering
    observable. Seam half (β)'s own per-plan metadata is anchored at m49 with §8.2(i).
  - **§6.1d's LINEAGE SEAMS, in `graphed`'s `tests/frozen/awkward/m48`** (new `graphed`
    source whose only consumers are fill-shaped — the same per-repo coverage argument as the
    seam above): `graphed.unify_contexts`-shaped answers the MOST-DERIVED handle for handles
    on one ancestry chain, `None` when every argument is context-free, ignores context-free
    arguments alongside contexted ones (the §6.1d adopt rule), and raises the §2.3e divergence
    error naming BOTH contexts on divergent handles; `graphed.reindex_to`-shaped is the
    IDENTITY when the value already carries the target's handle or carries none, re-indexes an
    ancestor value label-aligned per §2.4 across link kinds (1)-(3) — compared elementwise
    against a manually re-indexed reference — and RAISES when the value's handle is a
    DESCENDANT of the target or divergent (§2.1(b)). **The link-kind half is asserted PER
    KIND, and each kind's RESULT LABELS are part of the assertion**: **(1)** a mask-derivation
    link returns a `Varied` carrying the intervening mask's labels (an UNVARIED value BECOMES
    `Varied`), each member re-indexed by that label's own mask; **(2)** a `graphed.vary` link
    is the IDENTITY, labels unchanged; **(3)** a universe/nominal projection link returns an
    UNVARIED `Array` equal to a manually projected reference, carrying NO labels (§6.1d).
  - **§2.2 `Varied.apply`**: per-universe application of an `Array -> Array` function, plus
    the error contract — `fn` returning a `Varied` raises with guidance to combine via
    ordinary ops.
  - **§2.3d module-verb dispositions + §2.2's reserved `Array`-protocol names**. One
    table-driven test in `graphed`'s `tests/frozen/awkward/m48`, driven by the §2.3d
    **discovery rule**: dynamic over `graphed.__all__`, filtered to `inspect.isfunction`
    members any of whose parameter annotations mentions `Array`, **UNION the named floor
    list `{graphed.compile_ir, graphed.context_of, graphed.broadcast_like}`** (`compile_ir`'s
    annotations are `Session`/`Any`, so the dynamic half never reaches it;
    `context_of`/`broadcast_like` are the only representatives of *eager-metadata* and
    *broadcasting*), **MINUS `graphed.vary`** (no disposition class exists for it).
    `to_parquet` is NOT in the m48 list — it carries no disposition until m51 (§2.3d): it is
    outside `graphed.__all__`, and freezing an m48 entry whose VALUE m51 must change is a
    freeze-order trap.
    `graphed_histogram.Histogram.fill`'s disposition is asserted in `graphed-histogram`'s flat
    `tests/frozen/m48` (the *accepting* representative; the importorskip rule, §10 preamble).
    The gate carries §2.3c's non-vacuity floor: non-empty, ≥ the freeze-time count, containing
    every member of that repo's floor list, ≥ one member of each class in §2.3d's bound class
    set **that the repo's table can host at THIS milestone** — at m48 `graphed`'s table hosts
    at least {refusing, expanding, broadcasting, eager-metadata}, **a containment floor, never
    an exact set** (so m51's added *accepting* member cannot red it).
    **Plus the IDIOM-PACKAGE enumerations, in the same test**: the identical dynamic filter
    over `graphed.numpy.__all__` and over `graphed.awkward.__all__` — the numpy verbs
    (`apply_gufunc`, `empty_like`, `full_like`, `ones_like`, `project`, `zeros_like`) and the
    awkward ones (`project`, `project_buffers`) — each asserted to carry its §2.3d
    classification (the `*_like` verbs and `apply_gufunc` **broadcast**;
    `project`/`project_buffers` **expand**, returning `{label: Projection}` and
    `{label: BufferProjection}` respectively — each verb's own return type, NOT
    `read_columns`' union, §2.3d). **The floor is asserted over the UNION of the three
    enumerations, never per enumeration** (neither idiom package hosts a floor-list member,
    and the discovered idiom verbs are only *broadcast*/*expanding*), and stays a containment
    floor. Freeze-order is clean for `to_parquet`: `graphed.numpy.to_parquet` is not in
    `graphed.numpy.__all__` and `graphed.awkward.to_parquet` annotates its first parameter
    `Any`, so neither enumeration discovers it at m48.
    **The refusal table is SPLIT BY CONTRACT, because §2.3d binds two** (`GraphedError` is
    unrelated to `NotImplementedError`, so one frozen contract for all would red a conforming
    implementation): the **boundary/plan verbs** (`join`, `repartition`, `pack_key`,
    `shuffle_plan`, `join_plan`) refuse naming the offending container — m48 asserts only that
    they raise and do not silently compile; the exact §5.4 message shape is frozen in **m49**.
    The **compile/aggregate verbs** (`compile_ir`, `aggregate_plan`) raise a `graphed` error
    naming `graphed.universe`, with the positive control that the same verb on a plain `Array`
    still works. **`evaluate_ir` is NOT in the table** (it takes no `Array`, so there is no
    `Varied` to refuse and the positive control is false for it).
    The expanding verbs are asserted **per verb** (a blanket per-label-shape wording is false
    for `read_columns`): `apply` returns a `Varied`; `read_columns` returns the SINGLE union
    read set over all labels' members — `None` if any member's is `None` — NOT a per-label
    mapping (§2.3d). `graphed.broadcast_like` broadcasts (§2.3d, §6.1d).
    `varied.node_id` / `varied.session` raise `AttributeError` rather than recording a `field`
    op, with a negative control that `varied["node_id"]` (STRING getitem) still resolves as
    field access — so the rule cannot be a blanket `__getattr__` refusal. **That control needs
    its OWN fixture: a RECORD-typed operand carrying a literal `node_id` field**
    (`graphed.numpy.from_record(s, "r", node_id=…, pt=…)`, or an awkward record). String getitem
    records a `field` op, which refuses on any vector form and on a record lacking the field, so
    on the 1-D fixture the property clause pins below it reds a correct implementation.
    **Plus the PROPERTY
    half of §2.2's disposition rule, classified BY MEASUREMENT**: the numpy idiom's
    `shape`/`dtype`/`ndim`/`T` are plain properties `inspect.isfunction` never enumerates
    (`python/graphed/numpy/array.py`), and they are NOT one class — `dtype`/`ndim`/`shape`
    record nothing (`Session.node_count()` delta 0) while `T` routes through
    `record_op("transpose", …)` (delta 1). The anchor asserts per discovered name against the
    delta measured on the PLAIN nominal `Array`: `varied.dtype` (the eager representative)
    answers eagerly on the nominal member with delta 0, `varied.T` (the recording
    representative) returns a `Varied` whose `graphed.labels` match the input's, and
    `varied.node_id`/`.session` raise. A blanket "delta 0 for every property" reds a correct
    implementation on `T`. **The property-classification fixture MUST be a 1-D VECTOR partitioned
    source** — rank AND kind, so the record fixture the getitem control needs cannot be reused
    here: `NumpyArray.T` RAISES on a ≥2-D partitioned form and on any record form
    (`elementwise ops need array operands, got record[…]`), so the measurement step itself
    raises.
    **Plus the `graphed.context_of`-on-a-`Varied` discriminator**: a container built from an
    ancestor-handled nominal member and a MORE-DERIVED non-nominal member answers with the
    more-derived handle (§2.3e — the container's, not the nominal member's; §6.4a(2a)'s
    handle-equality predicate reads this answer). **The FIXTURE is pinned to a `graphed.vary`
    IDENTITY link** — `events2 = graphed.vary(events, "pu", …, is_weight=True)` then
    `v = graphed.vary(events.Jet, "jes", up=events2.Jet)`, asserting
    `graphed.context_of(v) is events2` — not to a mask-derivation link (the identity link
    keeps the row space fixed and matches what §6.4a(2a)'s predicate consumes).
  - **§6.1a result shapes** — **in SIBLING mode** (§6.2 axis mode is m50 and has its own
    shape, §6.2(i-bis); word the anchor so it does not freeze a general rule m50 must
    contradict), **worded over §6.1a's bound UNPACK verb (`graphed_histogram.unpack`-shaped,
    spelling pinned at freeze) and freezing the plan value's slot-keyed shape in the SAME
    anchor** (freezing a nested result shape alone would red an implementation conforming to
    §6.1c's flat keying): the executed plan's value is the flat
    `{(output, label) → bh.Histogram}` mapping (`_add_groups` stays a homogeneous key-wise
    `+`, `graphed-histogram src/graphed_histogram/boost.py`), and unpacking it on a MIXED
    varied/unvaried output set gives: a varied output is `{label: hist}`, an output no
    variation reaches is a BARE `hist` (not `{"nominal": hist}`), absent labels are absent
    (never duplicated from nominal), and `graphed.universe`/`graphed.nominal`/`graphed.labels`
    narrow both shapes uniformly — **`graphed.nominal` included** (§2.2 binds it on both
    result shapes; the axis-mode answer is anchored at m50 (i-bis), and the assertion is what
    rules out "return the argument unchanged for every histogram"). **Plus a WHOLLY-UNVARIED
    positive control**: a group plan with no variation anywhere keeps today's value verbatim —
    every key a BARE output name, so `run(gh.plan({"hi": h1, "lo": h2})).value["hi"]` still
    works once **`plan()`'s declared return type WIDENS to
    `Plan[dict[str | tuple[str, str | None], bh.Histogram]]`, part of m48's §6.1c target** — a
    widening the repos' existing src-only `mypy --strict` already gates end to end, since
    `aggregate_plan` infers `Plan[V]` from `_GroupReduce.__call__`, `_add_groups` and
    `_GroupZero.__call__`, so a half-done widening is an `arg-type` error on `combine`/`empty`.
    §6.1a's slot keying is scoped to outputs a variation reaches precisely so the
    already-frozen m23 suite stays green (`tests/frozen/m23/test_group_plan.py` indexes the
    value by bare output name), and §10 binds those artifacts unchanged.
  - **§2.3b plain-Array entry points learn `Varied`**: `plain_array[varied_mask]` and
    `plain_array.filter(varied_mask)` each return a `Varied` carrying the mask's labels
    (label-aligned per §2.4), with a negative control that neither raises the
    wrong-implementation shapes — `TypeError` from `__getitem__`'s final raise or
    `AttributeError` on `.node_id` from `filter`'s unchecked `record_op` — plus a
    still-`TypeError`s control for a genuinely unsupported index type, so the branch cannot be
    a blanket `except`.
  - **§2.5 unreached-label diagnostic** (a DIAGNOSTIC, not an error — the mkShapesRDF
    silent-cost guard; §2.5's raising cases are covered by "§2 validation errors" below): a
    registered label reaching no marked output is reported by `compile_ir` diagnostics; absent
    when every label reaches an output.
  - **§7.2 schema absence**: the `ExecResult`/`Plan`/monitor payload schema **KEY SETS** on a
    varied program equal **LITERALLY SPELLED expected sets** —
    `{f.name for f in dataclasses.fields(Plan)} ==
    {"process","combine","empty","tasks","next_tasks","stop","open_once"}` and likewise
    `ExecResult` → `{"value","n_partitions","n_combines","stopped"}` and the monitor payload
    `TaskEvent` → `{"phase","key","worker","t","partition","n_entries","bytes_read","error"}`
    (`python/graphed/core/execution.py`; `emit_task` passes the `TaskEvent` INSTANCE, so the
    payload is that dataclass, not a dict). A varied-vs-unvaried comparison is equal by
    construction — even after a field is added — and may ride along only as sanity, never as
    the assertion. Worded over key sets, NOT over plan bytes or the `process` spec — the
    §8.2(i) closure field, ADDED at m48 and POPULATED at m49, changes those by design (§7.2,
    §7.3).
  - Single-pass read witness **on the reference-matrix run** (§5.2b applied to the weight
    matrix).
  - §3.2 determinism: same varied program compiled in two fresh processes under differing
    `PYTHONHASHSEED` → byte-identical `compile_ir` output; `graphed.labels` order pinned
    (nominal-first + insertion order).
  - §6.3 goldens: committed GIR blob, captured PRE-m48 and committed already stripped of the
    descriptor `version` field, the live side stripped per-side (§6.3), + the params KEY-SET
    equality against a literally
    spelled set — `{"spec", "n_axes", "weighted", "sampled"}` for the unvaried single-weight
    fill (§6.3).
  - §2.3 **public-surface** parity (dunders AND methods, §2.3a — enumerated dynamically from
    `type(graphed.nominal(v))` so the numpy idiom's methods and tuple `__getitem__` are
    covered; `Array`'s own `filter`/`map`/`reduce`/`repartition`) and gak-classification
    exhaustiveness, both **dynamically enumerated** (§2.3a/c) — the parity gate is
    `frontend/m48`'s, the two gak gates `awkward/m48`'s — the classification test
    freezes only that every DISCOVERED public gak function has a classification; the
    *behaviour* of the `refusing` class is an m49 anchor (§5.4 is an m49 target).
    **§2.3e context-handle propagation is a SEPARATE, SCOPED gate** (a behavioural gate over
    the full gak surface is not buildable — §2.3e): it enumerates only the *broadcast*,
    *container-traversing* and *tuple-returning* classes, takes its AUXILIARY call arguments
    from fixtures living in `src` beside the classification **while the frozen test itself
    owns the CONTEXTED primary operand and asserts the returned handle is not `None` and IS
    the input's** (§2.3e(2) — a context-free fixture operand makes the assertion
    `None == None`) — **each fixture being a TEMPLATE with a named substitution SLOT the test
    fills, including inside a Mapping/Sequence argument, plus an assertion that the
    substitution happened** (`gak.zip`'s mapping is its only array-bearing operand) — and
    asserts the exempt set is exactly {*eager-metadata*, *refusing*} **plus §2.3e(3)'s
    MEMBERSHIP floor** — containment plus a monotone count, because a frozen equality reds
    the moment a future gak boundary verb arrives with its classification in `src`, which is
    where the self-repairing rule wants it: **`gak.join` IS IN the refusing class and
    `len(refusing) >=` the freeze-time count**, the broadcast count ≥ the freeze-time count —
    otherwise a re-classification hides an unimplemented member while the exempt CLASS NAMES
    stay exactly those two — **and the `Array`-surface gate carries its own floor** (refusing
    = `{repartition}`, broadcast count ≥ freeze-time, §2.3e(4)).
    **Each of these three tests carries §2.3c's non-vacuity floor in the same test** (a
    dynamic gate whose discovery step returns an empty or wrong set passes tautologically;
    gak has no `__all__`, §2.3c): the discovered set is non-empty, at least the freeze-time
    count, and names at least one member of each classification class; the parity gate
    additionally names `__array_ufunc__`, `__getitem__`, a bitwise dunder **and at least one
    public METHOD**.
    **The parity gate's per-name ASSERTION is bound, not just its enumeration** (§2.3a): each
    discovered name is resolved on the CLASS (`getattr(type(varied), name, None)`) — an
    instance-level `hasattr` is answered by `Varied`'s label-mapping field access for EVERY
    name, since `Array.__getattr__` records a `field` op for any non-underscore name — plus
    one behavioural probe per disposition class in the same test (a broadcast method returns a
    `Varied` with matching `graphed.labels`; `varied.repartition` raises the §5.4 refusal
    rather than `TypeError: not callable`).
  - **Per-class gak behaviour** (the exhaustiveness gate asserts a classification EXISTS, not
    that it is RIGHT, and the corpus matrices cannot reach these classes — the corpus fixture
    uses `ak.with_field`, never `ak.zip`): one named representative per otherwise-unanchored
    class — `gak.zip({"pt": varied_pt, "eta": plain})` returns a `Varied` carrying the labels
    (*container-traversing*); `gak.unzip(varied_record)` returns a TUPLE of `Varied`
    (*tuple-returning*); `gak.fields(varied)` / `gak.type_of(varied)` answer on the nominal
    member (*eager-metadata*). Plus §2 validation errors (§1.1, §2.5); §2.4 label-aligned
    combination on a Varied-meets-itself program, including the bound union order (§2.4);
    **and §6.1d's FOUR-way fill fold order** — a fill with varied values in TWO axes plus an
    ambient weight plus an explicit `weight=[…]` factor **plus a varied `sample=`** (today's
    `fill` appends `sample` unchecked, so a `Varied` sample falls into `record_external` and
    dies on `.node_id`), asserting the bound operand order (axis values in argument order,
    then ambient, then explicit factors in list order, then `sample=`) and that the varied
    `sample=` is ACCEPTED/expanded rather than raising `AttributeError`. **Both varied axis
    values are PER-EVENT** — the same equal-lengths pin the link-kind-(1) fixture carries below.
    **The fixture's histogram MUST use a `Mean`/`WeightedMean` STORAGE** — bh 1.8.0 rejects
    `sample=` on the default `Double()` AND on `Weight()`
    (`TypeError: Keyword(s) sample not expected`) while the evaluator passes `sample` straight to
    `h.fill`, so a default-storage fixture records
    cleanly and dies at EVALUATION. If the anchor is instead written as a RECORD-TIME
    assertion — the fold order read off the recorded fill node's `inputs` / the per-label
    fill-node accessor, plan never run — the test MUST say so explicitly.
  - §4.1 correctionlib single-payload multi-parameterization — **with its observable stated**:
    all labels' `External` nodes share ONE `PayloadDescriptor.content_hash` and differ only in
    the `systematic=` param, so the payload is never duplicated (fixture precedent
    `tests/frozen/preserve/m9/agc.py`). **The RECORDING SPELLING is named**: the fixture's own
    `graphed.preserve.record_external(s, CORRECTIONLIB_PLUGIN, corr_bytes, [njet],
    params={"name": "event_sf", "systematic": syst})` over `agc.correctionlib_json()` at its
    default `scale=1.0` — three labels give three External nodes sharing one
    `descriptor.content_hash` and differing ONLY in `params["systematic"]`. **The Session takes
    `AwkwardBackend`**: under `NumpyBackend` the same call raises
    `backend returned no payload descriptor for external op`, which is why this fill-free anchor
    lands in `awkward/m48`. `correctionlib` itself is never imported (the plugin loads lazily).
    `gak.apply_correction` is NOT that path: it records
    `params={"name": …, "args": json.dumps(args)}` (`python/graphed/awkward/functions.py`), so
    the systematic value rides inside the `args` JSON string and this anchor's observable is
    unsatisfiable through it.
  - §2.6/§6.1d event-context anchors: ambient fill on a per-object quantity — the value passed
    **UNFLATTENED** (§6.1d), Jet-pT fill yields value labels ∪ ambient labels, weight
    broadcast frozen against a manual-broadcast reference — **for the ambient weight AND an
    explicit `weight=[…]` per-event factor in the same per-object fill** (§6.1d: the evaluator
    multiplies factors after flattening each independently) **AND, as a third assertion, for
    the CONTEXTED-BUT-UNVARIED fill** — a context with NO registrations, no `Varied` input, a
    per-object value plus an explicit per-event factor (§6.3(2)'s trigger is a DISJUNCTION,
    "a context handle OR any `Varied` input"; this is the context-handle-only case): equality
    against the manually broadcast reference, **plus a witness that the seam node was actually
    recorded** — the fill node's input cone, or a `Session.node_count()` delta against the
    identical fill built with no context handle;
    plus the **execution-time** refusal when a per-object fill hands in an already-flattened
    value alongside a per-event ambient weight (§6.1d: an execution-time `graphed` error
    naming the OFFENDING FACTOR and pointing at "pass the value unflattened"; there is no
    record-time discriminator, so do NOT freeze a record-time raise, and do NOT freeze
    `FillEvaluator` as the raiser — under the bound broadcast seam the recorded broadcast node
    fails first, so the anchor freezes the MESSAGE CONTRACT at execution time, not a class
    name); same anchor covers an offending EXPLICIT factor, whose message names that factor;
    **and the LOOSE-VALUE case as a third assertion** — §6.1d binds a DISTINCT message there,
    naming the offending VALUE (not "the offending factor", not "pass the value unflattened");
    **divergent-lineage detection AT THE FILL** (§2.3e/§6.1d: `h.fill(a_from_ctx1,
    b_from_ctx2)` is a hard error naming both contexts) **plus a `sample=` assertion**:
    `h.fill(a_from_ctx, weight=[w_from_ctx], sample=s_from_divergent_ctx)` raises the same
    divergence error naming both contexts (§6.1d makes `sample=` a first-class operand of the
    fill's unification/divergence check — today's `fill` type-checks `args`/`weights` and
    appends `sample` unchecked). The raise
    is record-time, so this assertion carries no storage constraint. **AND AT THE OP**
    (§2.3e's *early detection* half): a binary op over `Array`s from two divergent contexts
    raises AT THAT OP naming both, with a positive control that an ancestor-chain pair unifies
    silently to the most-derived context **AND a SECOND positive control for §2.6b's
    context-IDENTITY rule** — two separate `graphed.nominal(sel)` reads (and two separate
    `events[mask]` derivations from one mask) UNIFY rather than raising, since pure
    derivations are canonical (a fresh-object-per-call implementation makes them siblings and
    fires the divergence error on a legal program). **AND AT `vary`'s OWN CONSTRUCTION**
    (§2.1 — `vary` is a combining point no `_array_cls` chokepoint sees): building a container
    from members read through two divergent contexts is a construction-time error naming both;
    **§6.1d link-kind (1) ancestor-VALUE re-indexing, asserted over the VALUE**:
    `h.fill(events.MET.pt, sel.MET.pt)` with `sel = events[varied_mask]` compared ELEMENTWISE,
    label-aligned, against a manually re-indexed reference (each label's ancestor value by
    that label's own mask, nominal's by nominal's) — an implementation that unifies the
    handles but never re-indexes must fail it on the row COUNT alone. **Extended with an
    ancestor-context `sample=`** (§6.1d: an ancestor-context `sample=` is re-indexed like any
    other ancestor VALUE): `sample=events.<field>` alongside the same axis values, its
    per-label re-indexed values compared against the same manual reference — which pins this
    fixture's histogram to a `Mean`/`WeightedMean` STORAGE (the same bh 1.8.0 `sample=` pin as
    the fold-order fixture), or the `sample=` half rides the fold-order fixture instead.
    **Both axis values are PER-EVENT, and the fixture MUST NOT be "improved" to a per-object
    second axis**: the evaluator flattens each axis independently and bh requires equal
    lengths across axes (bh 1.8.0, `ValueError: spans must have compatible lengths`), so it
    would red for a reason unrelated to what the anchor asserts (§6.1d's broadcast seam is
    scoped to weight factors, never axis-vs-axis);
    lineage semantics (`graphed.vary` returns a NEW context and the input context is
    unchanged — a fill from the pre-vary context carries no new label, a fill from the
    returned context does; ancestor-chain inputs unify to the most-derived context);
    **context-handle ORIGINATION** (§2.3e — the merge-from-inputs rule alone gets this wrong,
    since `Session.source` receives no context and `record_op` merges only from `inputs`): the
    same read performed through a `vary`-derived context and through its PARENT yields the
    SAME node id (interning) but DIFFERENT handles, and fills from each yield different label
    sets;
    selection-scoped weight via `vary` on a derived context (parent unaffected) **and the
    derived context's ambient weight re-indexed to the derived row count** (§2.6c) —
    **elementwise equality per label against a manually re-indexed reference, not length
    equality** (a length-only check passes right-length, silently mis-weighted arrays whenever
    per-label counts coincide, e.g. every label re-indexed by nominal's mask); the varied-mask
    case (per-label row sets) is inside this anchor;
    `graphed.labels` on a context derived by a **Varied** mask (per-label row sets, §2.6c) —
    **asserted as §2.2's UNION on a program that registers a weight BEFORE the derivation**,
    so the answer is ambient-weight labels ∪ the mask's labels in §2.4 order with `"nominal"`
    first, not the mask's labels alone — **plus a SECOND program** discriminating the
    varied-collections term: a shift-varied collection with an UNVARIED derivation mask, where
    the collection is the only source of the shift labels — assert `graphed.labels(ctx)` still
    reports them, and that it remains a superset of the context-borne half of a fill's label
    set (§2.2) — **plus a THIRD program that discriminates the union's THIRD TERM ITSELF**
    (in the first program the mask's labels are covered by term (a), in the second by term
    (b)): a context derived by a mask varied through the LOOSE §2.1a primitive —
    `mask = gak.num(graphed.vary(events.Jet, "jes", up=j_up, down=j_dn)) >= 4`,
    `sel = events[mask]`, with NO weight registered and NO shift-form `vary` on the context —
    for which terms (a) and (b) are both EMPTY and `graphed.labels(sel)` MUST still report the
    JES labels.
    **§2.2's clause that term (c) SKIPS OVER `vary` identity links is knowingly left
    UNANCHORED** — no m48–m51-scoped program isolates it; it stays binding for correctness of
    the verb, on §1.1's `"1e1000000000"` precedent.
    `graphed.universe(ctx, label)`/`graphed.nominal(ctx)` return a context that is a CHILD of
    the argument in the lineage chain (§2.2), so a fill mixing it with a read from the
    argument unifies instead of diverging — **asserted over the resulting VALUE, not merely
    over the absence of the divergence error**: the ancestor-context value is PROJECTED to
    that label per §6.1d's link-kind (3) and compared elementwise against a manually projected
    reference — the fixture is `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)`, both axis
    values PER-EVENT (the bh equal-lengths constraint above) — **and the RESULT SHAPE is
    asserted too: that fill's output is a BARE `hist`** (§6.1a's unvaried shape; §6.1d
    computes the label set AFTER projection, and this is the discriminator against an
    implementation that keeps the labels and projects only the contents);
    **`unweighted=True` in §6.1d's bound form** — it suppresses the AMBIENT weight AND any
    explicit `weight=[…]` (a contexted fill with registrations yields counts equal to an
    unweighted eager reference) **AND the suppressed weight contributes NO LABELS: such a
    fill, whose only variation source is the ambient registry, returns a BARE `hist` (§6.1a),
    not a `{label: hist}` of per-universe-identical counts**, and
    `fill(x, weight=[w], unweighted=True)` is a RECORD-TIME error naming both;
    data-context guard for **both** forms (`is_weight=True` AND a shift-form `vary`, §2.6d);
    lockstep `graphed.vary(events, name, Jet=…, MET=…)` shared-tag-set validation; §1.1 tag
    grammar (kwarg tags + `variations=` numeric-tag escape + every listed rejection); no
    reserved names on the context (a tree branch named `weights` or `vary` stays reachable);
    **the SLICE/INT context-subscript refusal** (§2.6a; `Array.__getitem__` accepts both
    subscript kinds, so the refusal needs its own anchor): `events[0:1000]` and `events[0]`
    each raise naming the supported subscript forms, with the mask and string subscripts as
    positive controls; §2.2 `graphed.universe`/`labels`/`nominal` on both `Varied` and
    contexts, string getitem = field access.
    The §1.1 grammar anchor MUST cover the e-canonicalization semantics **across all THREE tag
    channels** (§1.1 — including the shift form's inner mapping keys, e.g. `Jet={"0.5": …}` →
    `murf_5em1`, plus a duplicate-after-canonicalization rejection INSIDE one collection
    mapping): float spellings accepted via `variations=`, via `**`-unpacking and via a
    collection mapping (channel-independent) and normalized by exact decimal arithmetic
    (`"2"`/`"2.0"`/`"2e0"`/`"20e-1"` → the ONE label `murf_2`; `"1e-8"` → `eps_1em8`; integer
    PDF indices untouched), **non-minimal canonical-grammar tags re-rendered** (`"50em2"` →
    `5em1`, §1.1), the two readings of "`"0.5"` and hand-typed `"5em1"` unify" **split
    explicitly**: across TWO `vary` calls the spellings name the identical label `murf_5em1`;
    within ONE call they are a duplicate-after-canonicalization REJECTION, like
    `{"0.5", "0p5"}`. Plus cross-notation numeric-equal pairs rejected (`{"0.5", "0p5"}`,
    `{"2", "2p0"}`) **within one call AND across two stacking calls on the same `name`**
    (§1.1's family definition includes inherited labels) — **the cross-call pair is spelled in
    the WEIGHT form (b)**: an event-context target with no `is_weight` is overload (c), in
    which `variations=` is REJECTED outright (§2.1), so a `vary(ctx,"murf",variations={…})`
    spelling would freeze the WRONG rejection here. `inf`/`nan`/leading-`+`/underscore/
    whitespace spellings rejected, Python-float (non-string) tags rejected, negative zero
    canonicalizing to `0` (never `m0`) and a >32-character canonical tag rejected (§1.1)
    **alongside the INTEGER-MAGNITUDE rejection as a distinct case** (§1.1 binds two
    rejections around the cap, and they must stay distinguishable): `"1e40"` (integer-valued,
    41 plain digits) is rejected **at canonicalization with a message NAMING THE MAGNITUDE**,
    not with a generic tag-length error, alongside the existing `"1e-8"` → `eps_1em8`
    positive; **plus the CAP-BOUNDARY PAIR that pins the digit-count NORMALIZATION** —
    `"1.5e31"` is ACCEPTED and yields the canonical 32-digit tag (`15` followed by 30 zeros,
    exactly at the cap; the naive "mantissa digits + exponent" sum computes 33 and rejects
    this legal tag, which `"1e40"` alone cannot catch) while `"1.5e32"` (33 plain digits) is
    REJECTED with the magnitude message **and its NEGATIVE twin `"-1.5e31"` is REJECTED with
    the canonical-tag-LENGTH message** (§1.1 refuses by CAUSE: the real cause is the `m` sign
    marker taking the rendered tag to 33 characters, not the magnitude the adjacent half of
    this anchor certifies as legal). The "count BEFORE any rendering" rule is knowingly left
    UNANCHORED — its witness would be `"1e1000000000"`, whose failure mode under a
    render-then-measure implementation is a hang/OOM, not a clean red. The
    **signature-shadowed names** (`nominal`/`is_weight`/`variations`/`collections` reachable
    only through `variations=` / `collections=` — including `collections`' own
    self-reference, §2.1 — and `variations=` refused in the shift form, **plus `nominal=`
    refused in the shift form with an error naming `collections=`**, §2.1; **the tag `nominal`
    is LEGAL and yields the ordinary label `pu_nominal`, and there is NO "label equals
    `nominal`" rejection to freeze** — every label contains a `_` by construction), and no
    label ever containing `.`/`-`.

- **m49 — shift path + impact + executor end-to-end** (repos: `graphed` + **`graphed-histogram`** +
  `graphed-executors` — the repo list is what R0.5's full-matrix-CI-green check and per-repo
  freeze tagging key on).
  Targets: §3.3, §3.4 (frozen anchor), §5 **including §6.1d's awkward broadcast-blame wrapper**,
  **§7 — EXCEPT §7.2's SEAM, which lands at m48 (§10/m48); m49 owns §7.2's merge-shortfall refusal
  on every builder and every program, which on `Histogram.plan()` is new work, not a widening**,
  **§8 — EXCEPT §8.2(i)'s `variation_labels` FIELD DECLARATION, which lands at m48 with §7.2's (β)
  return channel (its `tuple[Any, ...] | None` annotation is the shipped one and m49 does not
  narrow it); m49 adds the record→reduced correspondence through all four reduction passes and both
  reduction paths, the `RewriteEngine` return widening it needs, the keying, and the POPULATION of
  `variation_labels` (§7.2's seam-half-(β) payload)**, **plus §2.5's shift-after-weight
  diagnostic**, **plus §9.1's `graphed.member_of` export and per-label projection-stats verb (§5.3;
  spellings pinned at m49 freeze)**.
  **Implementation-target partition (one reasoning partition per commit)**: (1) the `graphed-core`
  correspondence — the four pass returns, the engine-trait widening, the incremental composition,
  and the PyO3 accessor, inside `src/optimizer` + `src/store.rs` + `src/lib.rs`, **plus its Python
  half: `compile_ir`'s additive `CompiledGraph` field and the per-key frame it puts there
  (`python/graphed/execute.py`)**; (2) the
  `graphed` frontend verbs — §3.4, §5.3's stats verb, `member_of`, §2.5's record-time diagnostic;
  (3) the `graphed` error path — §8.1's field, §8.2(ii)'s wrap and (iii)'s attribution hook,
  §6.1d's awkward wrapper, **and §5.4's message shape, which as built names the verb alone**;
  (4) the `graphed-histogram` producer — the `variation_labels` payload
  and §7.2's refusal on both merged-fill consumers. Each is a single compartmentalized concern
  inside one repo.
  Frozen anchors:
  - The **full 15-reference matrix**, split across two repos:
    (i) **`graphed-histogram`, flat `tests/frozen/m49`** — the matrix through the frontend,
    fingerprint-exact against the 15 stored references, plus a separate run-to-run `array_equal`
    determinism assertion (the m29 dual-assert precedent; "bit-for-bit" is claimed only run-to-run,
    not vs the rounded references). The §5.2b read witness binds to THIS run; no `importorskip`
    (§10 preamble). This half lives in `graphed-histogram`, not `graphed` — a fill-based matrix in
    `graphed` would `importorskip`-SKIP in CI (§10 preamble), while after m48 `graphed-histogram`
    carries the corpus dep and the vendored references.
    Per-repo partition of the remaining m49 anchors, **rule (2) (§10/m48) applying here too**:
    `graphed` `tests/frozen/frontend/m49` — the non-fill frontend anchors (§5.2a arena delta,
    §5.2c stage shape, §3.4 impact sets — including the two-form operand rejection both m49 verbs
    share (§3.4) — §5.3 projection with its awkward-free conservative spelling, §5.4's refusal and
    its positive control, the varied-mask `_align` path (`vary.py`), the no-label scan downstream
    of a container, and family TAGS surviving a §2.4 combining op — the M11 escape class, which
    the m48 tree witnesses only at construction).
    **§5.4's fixture is SELF-CONTAINED and awkward-free**: two flat
    `from_record` tables joined through `graphed.join` on a `NumpyBackend`, materialized per
    universe. It does NOT import `tests/frozen/frontend/m40/shuffle_backends.py` — that module
    imports awkward, pandas and `graphed_corpus` at module scope, so it cannot be imported at all
    on the required free-threaded gate, its directory is not on `pythonpath`, and putting it there
    would expose a top-level `shuffle_backends` that `frontend/m39` also ships.
    `graphed` `tests/frozen/awkward/m49` — **§2.5's shift-after-weight diagnostic**, whose fixture
    registers an ambient weight and so is an event-context program (§2.1(b)); §5.4's
    refusal if instead spelled through `gak.join`, the bound representative; §6.1d's broadcast-blame
    wrapper with its compatible-factor control; and the two context-program label regressions —
    `_mask_key` keyed on more than the nominal node id, and labels surviving
    `EventContext._project` (whose absence leaves the frozen loose-`vary` law green while the
    context path answers wrongly, which is why the §2.5 diagnostic fixture is where it belongs).
    `graphed` `tests/frozen/core/m49` — the §3.3 benchmark (§10's header and §3.3 pin it to
    `core/m49`). `graphed-histogram` flat `tests/frozen/m49` —
    additionally the §2.4/§6.1b structural arity anchor (fill-shaped; in `graphed` it would
    `importorskip`-SKIP), the m05 ordering witness, the JER-SF stochastic fixture (its
    partition-invariance witness needs a plan run at two `steps_per_file` values), the weight-factor
    re-index through `graphed.reindex_to` on the fill path, blame parity between the plan/executor
    path and `materialize` (§6.1d's contract holds on both), a per-side-strip discriminator for the
    §6.3 goldens (one pattern applied to both sides leaves them byte-identical and witnesses
    nothing), and **§7.2's merge-shortfall refusal on BOTH consumers** — two UNVARIED fills the M4
    identity rules merge raise the clear refusal on the group builder, where they die in the worker
    with an `IndexError` today, AND on `Histogram.plan()`, where today they RUN and silently
    under-sum (the anchor names the observed wrong answer's shape, not an exception, as what the
    refusal replaces); a merge-free pair of each shape is the positive control. `graphed` gains
    **`tests/frozen/checkpoint/m49`** for §7.3 interrupt/resume and §7.4's dead-letter
    MECHANISM — partition-atomic retry, one poisoned variation dead-lettering the whole composite
    — while the LABEL the dead-letter surface names rides the §8.2 StageError anchor in
    `graphed-executors` (§7.4, §8.2). A new directory; unique-basename rule —
    `m8/test_resume.py` exists. **`graphed` gains `tests/frozen/debug/m49`** for §8.1's `__hash__`
    anchor and §8.2(ii)/(iii)'s wrap-and-attribution anchors: that source is `graphed`'s, so under
    the rule that each half is anchored in the repo whose source it is (§7.2), its §B.3 diff
    coverage must come from `graphed`'s own frozen suite, which no `graphed-executors` test can
    supply. It carries the in-process failure through `_PartitionReduce` and a spawn-based
    cross-process test (`tests/frozen/debug/m6/test_process_boundary.py` precedent), **plus the
    UNATTRIBUTED arm**, which is wrap-side and nothing else: with no entry for the failing key a
    worker failure re-raises the ORIGINAL exception unchanged, not a `StageError` and not the
    `IndexError` an unconditional wrap would produce from empty frames — **and the
    tie-break**, whose source is `compile_ir`'s: two record ids recorded at DIFFERENT user lines
    that the reducer merges onto one key, asserting the frame of the LOWEST (a last-writer-wins
    implementation reports the other line and is red). Its attributed arm supplies
    a (β) hook, which is legal because §5.2a's self-derivation ban is worded over the LABEL
    association, not over the mechanism this anchor witnesses. The `debug`
    subtree runs whole, so basenames are unique against every debug milestone.
    `graphed-executors`' flat `tests/frozen/m49` keeps the CROSS-REPO half — the labelled
    `StageError` surviving a real process-pool boundary, including the dead-letter label, and both
    §8.2 rendering members (multi-label and empty-tuple) — which only that repo can exercise.
    The §5.5a comparison quantities are produced by a PLAN RUN — per-partition values concatenated
    in task order — and `Session.materialize` MUST NOT be the oracle: `materialize` is
    partition-blind, so the witness cannot observe `steps_per_file` through it. The deterministic
    route: `SequentialRunner` folds tasks in sorted key order, so an `aggregate_plan` whose reduce
    returns partition-local arrays and whose combine concatenates is order-deterministic.
    (ii) **`graphed-executors`, flat `tests/frozen/m49`** — the same matrix through a process-pool
    executor (the executors live in `graphed-executors`). Because this half must exercise
    §4.2/§6.1's varied-fill lowering, **m49 adds `graphed-histogram` to `graphed-executors`' `dev`
    extra AND binds the install pair, in the shape that repo's own `ci.yml` already uses for
    `CORPUS`** (a name-only dev-extra entry resolves to the stale PyPI `0.0.1` release): a
    **`HISTOGRAM` git-URL workflow env var plus its `pip install` line in every job that COLLECTS
    `tests/frozen/m49`** (`ci.yml`; the two milestone-scoped jobs collect other trees and need
    nothing). **The omission fails silently here, unlike its `CORPUS` model**: `graphed-corpus` is
    not on PyPI so a missing line errors at install, while `graphed-histogram` IS, so a missing line
    quietly installs the stale wheel and the job tests the wrong package. No
    `importorskip` (§10 preamble). It compares against corpus references recomputed in-process via
    `graphed_corpus` (the m7 house pattern, `tests/frozen/m7/adl.py`; not
    materialize-then-fill-eagerly, which exercises none of §4.2/§6.1/§6.2). This is the
    executor-level systematics end-to-end no frozen test currently discharges (cba §corpus §4).
  - m05 ordering witness (`jes_up > nominal > jes_down`) through graphed — explicitly scoped to
    the monotone JES fixture (§5.1); the suite MUST NOT assert ordering for any other shift.
  - A **JER-SF-style stochastic shift fixture** (additive — corpus m05 tests/references
    untouched): per-row content-seeded re-smearing per §5.5a, one shared draw, SF-varied per label.
    **The FIXTURE is stated** (§5.5b): the stochastic form `1 + sqrt(max(SF² − 1, 0)) · g` over the
    shared per-row standard normal, **both varied labels above 1 at different magnitudes** — any
    `SF ≤ 1` hits the formula's `max(…, 0)` floor, smears by exactly 1, and both passes that label's
    partition-invariance leg without testing anything and reds the migration witness below by
    equalling nominal — and the selection threshold inside the smeared bulk, which is what makes the
    migration two-way rather than nested.
    Witnesses: run-to-run byte-identical results; selected counts pairwise distinct across
    {nominal, jer_up, jer_down} with NO ordering asserted, plus **bidirectional migration** (no
    universe's selection mask is a subset of another's — the non-monotone discriminator); the
    shared random-draw node interned ONCE across all universes (mechanism witness, §5.5b); **and
    PARTITION INVARIANCE — the identical event set run at two different `steps_per_file` values
    yields byte-identical per-label SMEARED VALUES and selection MASKS** (a weighted float
    histogram is NOT byte-invariant under re-partitioning, §5.5a; a constant-seeded per-partition
    RNG passes the other four witnesses — the failure this witness exists to catch). Deterministic
    invariant, R0.10a-safe.
  - §5.2 witnesses (a: arena delta vs an independently hand-built oracle; c: reduced-stage shape
    vs the same-topology no-`vary` ORACLE — not a frozen literal and with NO post-freeze
    re-measurement clause, §5.2c).
  - **§2.5 shift-after-weight diagnostic** (§2.1/§2.5, using §3.4 which lands here): a weight
    factor registered BEFORE the `vary` that replaces a collection its cone reaches is reported,
    naming both. TWO positive controls, since the two ways of reporting nothing fail differently:
    the correct ORDER (the shift precedes the weight, so there is no ambient weight to test) and a
    weight of the correct order's shape that legitimately does not read the shifted collection (an
    ambient weight exists and the walk answers no). The fixture is a context program, so it doubles
    as the `EventContext._project` label regression's home.
  - §3.4 impact-set anchor: three labels where two share a derived node — the shared node appears
    in both impact sets; result independent of expansion order. **The FIXTURE is stated**: the
    sharing must be UPSTREAM of the fork — the two varied members have DIFFERENT expressions that
    both consume ONE derived node the nominal member does not use (interning keys on input ids,
    `src/store.rs`, so no node downstream of the fork can be shared by two labels with distinct
    members). Assert all three: `u ∈ impact(up) ∩ impact(down)`, `u ∉ reachable(nominal)`, **and
    `impact(up) ≠ impact(down)`** (the identical-member form belongs in m48's §1.2 dedup anchor).
    The id-watermark implementation §3.4 rejects is red on this fixture. The fixture is built
    through the public `graphed.vary` surface (§3.4's verb takes labelled containers a raw
    `GraphStore` cannot supply); the frontend spelling is cheap: `k = src * 2.0`, two different
    expressions over `(src, k)` as the two varied members, the unvaried target as `"nominal"`.
    This is the same construction §8.2(i)'s m49 anchor builds, so the two anchors MAY share one
    fixture.
  - §2.4/§6.1b structural no-cross-product count — **in SIBLING mode** — `1 + |S| + |W|` fill
    nodes (axis mode's `1 + |S|` is m50, §6.2; word the anchor so it does not freeze a general
    rule m50 must contradict).
  - §5.3 projection-union test — **over a FLAT source** (branch-per-column
    `Jet_pt`/`Jet_eta`/`Muon_pt`, the shift's extra column being the top-level `Jet_eta`;
    `read_columns` reports only top-level fields, so a nested `Jet.eta` example is unsatisfiable
    against a correct implementation) — **including the per-label projection stats** reporting the
    shifted label's extra column, read through the §9.1 verb whose shape §5.3 pins
    (`{label: tuple[str, ...] | None}`, sorted per label; spelling pinned at m49 freeze) — **with
    a CONSERVATIVE label in the same fixture**, spelled `ev.map(f)` (a whole-record consumer;
    awkward-free, so the anchor keeps its `frontend/m49` home — rule (2), §10, and unlike an
    elementwise op on the record, which both shipping backends reject as ill-typed on this flat
    source), asserting that label maps to `None` and not to `()`. The conservative label stays in
    the SAME program as the growth labels — the stats verb answers per label and does not collapse —
    and the plain `read_columns` UNION-growth assertion rides a separate program or output set,
    because there the conservative member collapses the union to `None` (§2.3d) and the growth half
    goes vacuous. State the growth half per label through the
    stats verb **order-insensitively**:
    `set(stats["jes_up"]) - set(stats["nominal"]) == {"Jet_eta"}` AND
    `set(stats["nominal"]) - set(stats["jes_up"]) == set()` (a plain concatenation is red — both
    returns are sorted and `Jet_eta` sorts first).
  - §5.4 refusal + positive control (a downstream variation still compiles and produces correct
    results per universe, against an independently computed relational reference) — its tree
    follows its refusing fixture per the partition above. The refusal asserts the bound
    `GraphedError` and that the message names the refusing verb and the container's labels; a
    `NotImplementedError` expectation would contradict m48's frozen disposition anchors.
  - §3.3 NEW frozen variation benchmark file (exact `stages == N+1`, `reduced == 2N+2`, linear
    bound).
  - **§8.2(i) correspondence + keying, in `graphed`** — the bullet straddles two homes: the accessor
    half in `tests/frozen/frontend/m49` (a `compile_ir`-shaped program) and the plan-byte
    determinism half in `tests/frozen/checkpoint/m49` beside §7.3, whose
    module-level-`DurablePlan`-by-value construction it shares verbatim; both under the
    unique-basename rule (§10 preamble). The accessor is an m49 Implementation Target in
    `graphed`, so its diff coverage must come from that repo's own frozen suite. Over the §3.3
    builder topology — **built through the frontend `compile_ir` path and EXTENDED with one
    deliberately unmarked branch** (§3.3's builder marks every universe's terminating reduction as
    an output, so the bare topology gives the DCE clause no operand) — assert: every surviving
    record id maps to a `(reduced_id, member_index)` whose reduced id **is a node id of the
    compiled reduced store** (not "in the output/stage set" — the SOURCE record's reduced node is
    neither); the unmarked branch's record id maps to `None`; and — **on a topology EXTENDED a
    second way: one derived node consumed by TWO NON-nominal universes** — that node maps to ONE
    `(reduced_id, member_index)` key reached from BOTH labels' record cones, i.e. the accessor's
    image collapses two labels onto one key (the SET-VALUED pair key space §8.2(i) declares; the
    bare §3.3 topology shares nodes only across ALL labels including nominal, so the clause needs
    this extension). **The clause is worded over the ACCESSOR here, not over `variation_labels`**
    — that field's only bound producer is `graphed-histogram`'s group-plan builder (§8.2(i),
    §7.2), and no bound producer exists in a `compile_ir` program. The two labels' shared record
    ids are recovered from §3.4's impact verb (§9.1); the LABEL association itself is anchored in
    `graphed-histogram`'s flat `tests/frozen/m49` (below).
    **Plus a PARTITIONING clause the §3.3 topology makes exact** (without it a degenerate constant
    map `record_id -> (one_stage_id, 0)` satisfies every clause above): the shared-prefix record
    ids all map to ONE reduced id, each universe's chain maps to a reduced id DISTINCT from every
    other universe's, and the map's image over the WHOLE topology is exactly the set of the
    compiled reduced store's node ids, its `stage`-kind subset exactly that store's stages. **Read
    off THAT artifact, never asserted as §3.3's raw-builder literals** — §5.2c bars those of a
    `vary`-built program, and the same reduction produced both sides here, so the artifact is the
    oracle and no literal is frozen.
    **The cardinality clause is asserted on the BASE fixture (± the unmarked dead branch) ONLY,
    NOT on the shared-node extension**, which carries the BOTH-labels clause instead.
    **Plus the clause that discriminates the composition from the DCE-only reading**: a THIRD
    extension carries a node the reduction removes AFTER dead-code elimination — an identity-token
    op (`x * 1.0`) on a live path, which is reachable from an output and so survives DCE, and is
    then folded away by the engine's identity rule. Its record id must map to the reduced node its
    input landed in, which only a map composed through canonicalization, CSE and stage fusion can
    answer. It is the NARROW discriminator: the base clauses above already red a DCE-`remap`-only
    accessor (where every universe's reduction is marked, DCE drops nothing, so its remap is the
    identity and its image is not the reduced store's node ids), while this
    one isolates the post-DCE passes from the composition as a whole.
    **Plus BOTH reduction paths**: the same fixture compiled on a
    `Session(incremental=True)` — public M10 surface, which reduces through a canonical arena of
    its own before the four passes — answers with the same RECORD-keyed map.
    Plus **plan-byte determinism with the §8.2(i) field POPULATED** — the field reaches the shipped
    closure through §7.2's seam half (β), so this anchor is also (β)'s frozen coverage, and **the
    fixture supplies the (β) hook returning a populated sorted payload**: the m48 default is `None`,
    which pickles seed-independently and would freeze this anchor green against the very `frozenset`
    it exists to ban. (Supplying the hook is legal here because §8.2(i)'s self-supplied-hook ban is
    worded over the LABEL ASSOCIATION, which this anchor does not assert.) The same
    varied program built in two fresh processes under differing `PYTHONHASHSEED` yields
    byte-identical `DurablePlan.to_bytes()` and identical per-partition `task_id` (the plan-level
    twin of §3.2's IR-level m48 anchor; a `frozenset` field pickles in hash order, §8.2(i)).
    **The fixture's plan construction is part of the anchor** (§7.3): the `DurablePlan` is built
    BY VALUE over the plan `aggregate_plan` returned — `OpSpec.from_callable`, never
    `OpSpec.from_ref`, which would keep the closure's fields out of the plan bytes and freeze the
    anchor GREEN against the very `frozenset` §8.2(i) bans — **and every closure operand (the
    `PartitionedSource`, reduce/combine/empty) is a MODULE-LEVEL definition in an importable
    module**, since a by-value-pickled `__main__` class makes the plan bytes seed-dependent and
    the anchor red against a correct implementation.
  - **`variation_labels` POPULATION, in `graphed-histogram`'s flat `tests/frozen/m49`** (the
    field's only bound producer is that repo's group-plan builder, §8.2(i)): over a varied
    program, `gh.plan({…})`'s shipped closure carries a `variation_labels` entry in §8.2(i)'s bound
    layout whose label tuple
    is SORTED and, for a `(reduced_node_id, member_index)` key two labels' cones both reach,
    carries BOTH labels — the set-valued half the `graphed` accessor anchor can only witness as a
    key collapse. The fixture's shared node is UPSTREAM of the label fork (the §3.4 shape):
    distinct labels have distinct FILL nodes by §6.1b's count, so no fill-node key is ever reached
    by two labels. **Plus the ADMITTED member of the hook's None rule** (§8.2(i)), which only this
    repo can witness because only here does the producer run: an UNVARIED builder call made in a
    session that registered a variation on ANOTHER chain ships `variation_labels is None`. A
    session-scoped producer fails it; the `graphed` trees cannot, since a hook-less
    `aggregate_plan` returns `None` whatever the producer does.
    **Plus the nominal-exclusion clause** (§8.2(i)): the shared prefix, which every
    label's cone reaches, carries the non-nominal labels and NOT the string `nominal`, and a key
    reached only from the nominal cone carries an EMPTY label tuple beside a real frame — so it
    renders `""` and still points at the user's line, the one encoding §8.1's empty-string contract
    admits.
  - §8.2 cross-process labeled StageError (incl. §7.4 dead-letter label) **plus both §8.2 rendering
    members — the shared-node MULTI-LABEL half and the nominal-exclusive EMPTY-TUPLE half**
    (without the first, the single-label anchor passes under a pick-one-arbitrarily
    implementation) — the tie-break behind it is `graphed` source and is
    anchored in `debug/m49` above, so what this bullet adds is that a shared node's attribution
    SURVIVES the process crossing. §7.3 interrupt/resume byte-identity **over a
    `DurablePlan` built by value exactly as the §8.2(i) anchor above builds it** (under
    `OpSpec.from_ref` the fixture would exercise no varied lowering at all). **Plus §8.1's
    `__hash__` participation explicitly**: `__eq__` compares `self.__dict__` so a new field
    participates for free, but `__hash__` is a hand-written tuple that must be edited
    (`python/graphed/debug/errors.py`) — assert two `StageError`s differing ONLY in `variation`
    are unequal **AND hash differently**. The `__hash__` and wrap/attribution halves are `graphed`
    source, so they are anchored in `graphed`'s `tests/frozen/debug/m49`; what stays in
    `graphed-executors` is the real process-pool crossing.
- **m50 — scale + integration** (repos: `graphed-histogram` + `graphed`. The `graphed` source
  targets are `preserve/` for §9.2, the §9.1 `graphed.variations` verb, and §6.2(i-bis)'s
  axis-mode arm of the narrowing helpers — `accessors.py` already dispatches a duck-typed
  histogram but reads every one as unvaried, so recognising a variation axis is an edit to that
  arm. **The m49 carryover trees below add `graphed` frozen tests only, no source.**)
  Targets: §6.2, **§6.1c's AXIS-MODE slot** (the `(output, None)` keying and the per-slot spec
  taken from the fill node; §6.1c defines no per-output MODE field — the three slot key forms are
  disjoint and per output, and the combine stays a key-wise `+`), **§9.1's `graphed.variations`**
  (the rest of §9.1 is an m48 target) **plus §9.1's plan-level `{output: [labels]}` listing** (own
  anchor below) + §9.2. Frozen anchors:
  - Variation-axis fill equals sibling-fill results bin-for-bin on the corpus **weight** labels,
    AND a mixed shift+weight program lands in ONE axis-mode histogram equal to its sibling-fill
    decomposition (§6.2, scalar-labeled shift siblings); combine-safety across partitions
    (identical spec, deterministic label order). **The mixed program carries a label borne ONLY by
    a `Varied` `sample=`** — the one place §6.1b's `S`/`W`-by-lowering definitions are
    witnessable: that label must lower as a SIBLING (it counts in `S`), and the axis-mode result
    still equals its sibling-fill decomposition (an implementation classing a sample-only label
    into `W` would silently reuse one sample column across universes). **The fixture MUST use a
    `Mean`/`WeightedMean` storage and per-label sample values that DIFFER (§6.1b)** — bh rejects
    `sample=` on `Double()`/`Weight()` storages with a `TypeError`, so a default-storage fixture
    dies at evaluation and a sample-discarding storage makes the equality vacuous.
    **Its VALUE is PER-OBJECT (jagged) and at least one weight factor is per-EVENT, so §6.1d's
    broadcast seam is engaged on the loop node's columns** (§6.2): every pinned quantity above is
    satisfiable on flat per-event data, on which the broadcast is a no-op, so a per-event fixture
    admits an implementation that hands the loop node raw columns — which then length-mismatches
    at `h.fill` on the per-object analyses this mode exists for. The sibling analogue is already
    discriminating this way (`tests/frozen/m48/test_ambient_object_fills.py`); axis mode gets the
    same treatment rather than a weaker one. **Plus the
    per-fill CARRIER witness** (§6.2): in the mixed program the `1 + |S|` axis-mode fill nodes
    carry distinct External `content_hash`es and resolve to distinct evaluators (the registry is
    keyed on `content_hash(self._spec)` alone, so otherwise every sibling resolves to the
    evaluator registered last — which bin-for-bin equality can mask when two siblings agree).
  - **MIXED-MODE PLAN — mixed-mode UNPACKING and the per-slot SPEC**: one `plan(...)` call
    carrying an axis-mode output AND a sibling-mode varied output together, plus a third output no
    variation reaches — the only program that reaches the mixed unpack. It witnesses the unpacking
    and the per-slot spec, NOT a per-output MODE field (§6.1c defines none). Assert: the axis-mode
    output unpacks to a BARE variation-axis histogram, the sibling-mode output to `{label: hist}`,
    the unvaried output to a BARE `hist` under its bare key (§6.1a), all narrow through
    `graphed.labels`/`graphed.universe`, and all are bin-for-bin correct. **Plus a FOURTH output —
    axis-mode opt-in, NO variations — asserting its slot key is `(output, None)` and that it
    unpacks to a bare histogram carrying a 1-bin variation axis** (the MODE, not the variation
    count, decides — §6.1c). **That same histogram carries §6.1c's axis-mode arm, one line:
    `.plan()` on it RAISES the §6.1c refusal naming the group API** — it is unvaried, so m48's
    varied-only trigger would let it through into an opaque bh `ValueError`. (It also exercises
    `_GroupZero`'s per-slot spec across two DIFFERENT specs, which nothing else in m48–m51
    reaches.)
  - **§6.2 declaration contract** (scoped to the frontend-declared-only rule §6.2(ii) binds): the
    declared bin set equals the §6.1d inferred label set EXACTLY — **two assertions, because one
    direction is invisible to the flow check**: `h.sum(flow=True) == h.sum()` catches an
    UNDER-declaration, while an OVER-declaration passes it unchanged (measured on bh
    1.7.2/1.8.0), so the closing half asserts the axis's bin tuple against a LITERALLY spelled
    expected label list, never one read back from the histogram or from `graphed.labels(h)`
    (circular on content per §6.2(i-bis)); a second fill whose inferred label set differs from
    the first's is a hard error naming the mismatch (§6.2 i, cross-fill agreement); **plus the
    MODE-mismatch error** (§6.2(i)): a second fill into the same histogram in the OTHER mode —
    first fill axis-mode, second sibling-mode — is a hard error naming both; **and a
    user-constructed histogram that already carries a `"variation"` axis is refused with an error
    pointing at the opt-in mode** (user-declared axes are §11) — **with the RECOGNITION RULE and
    the fixture spelling bound**: recognition is `axis.__dict__.get("name") == "variation"` (the
    §6.2(i-bis) name carrier; the fixture sets the name that way because
    `bh.axis.StrCategory(..., name="variation")` is itself a `TypeError`, §6.2 i-bis), and a user
    `StrCategory` under ANY OTHER name is untouched — the frontend still appends its own
    variation axis (the "any `StrCategory`" alternative would refuse a legitimate user category
    axis). There is no "undeclared label at fill" or "unsorted user-supplied bin order" anchor —
    under frontend declaration neither state is reachable.
  - **§6.2(i-bis) axis-mode result shape**: an axis-mode varied output is a BARE histogram
    carrying the variation axis. The name is read per axis and **`h.axes.name` MUST NOT be the
    oracle** (bh maps that attribute over every axis and raises when one lacks it — an
    `AttributeError` against a CORRECT implementation); the surviving invariant is that the name
    round-trips `spec_of`→`zero_of`:
    `[a.__dict__.get("name") for a in z.axes] == [None, "variation"]`. `graphed.labels(h)` (**and
    `graphed.nominal(h)` — §2.2 binds it to the nominal SLICE, not the whole histogram; same
    manually-sliced oracle, one extra assertion**) returns the axis bin set **re-ordered to
    §2.2's rule — `"nominal"` first, then the remaining bins in axis order — while the stored bin
    order stays lexicographic** (assert both; the discriminating case is a family whose
    lexicographic first bin is not `"nominal"`) and NOT `["nominal"]`, while
    `graphed.universe(h, label)` returns that label's slice along it — the narrowing helper
    uniform over all three shapes (§6.1a bare-unvaried, `{label: hist}`, bare-axis-mode).
    **Worded over SEMANTICS, not a literal subscript expression**: the oracle is equality against
    a manually sliced reference, because `h[{"variation": label}]` raises `TypeError` on a bare
    `bh.Histogram` (measured on 1.7.2 and 1.8.0); only the positional
    `h[{axis_index: bh.loc(label)}]` works.
  - The §6.2 scaling claim frozen **structurally** (R0.10a: no wall-clock in frozen tests): per
    partition, axis mode ships **1 combine payload entry** vs `N+1` in sibling mode — the length
    of the per-partition combine payload under §6.1c's key shape: one entry per `(output, label)`
    in sibling mode, ONE entry `(output, None)` in axis mode — with the fixture's output count
    pinned at 1 **and the fixture scoped to WEIGHT labels only** (under a mixed program the
    axis-mode side still records `1 + |S|` fill nodes and the 1-vs-`N+1` count is ambiguous; the
    mixed program is frozen by the adjacent equality anchor, which does not count slots). Plus
    bin-for-bin equality. The "allocates 1
    histogram object" half and the N≈100 wall-clock sibling-vs-axis comparison are
    **implementer-report measurements under R0.11** (methodology stated) — NOT frozen gates.
  - §9.2 one-bundle-N-labels preservation (m9 comparison form, on the bound varied
    `build_bundle`/`reproduce` surface — with the backward-compat control that an unvaried bundle
    still returns a BARE array) + `inspect()` label listing (§9.1) — **plus the `FORMAT_VERSION`
    bump**: the varied bundle's manifest carries `format_version == <the bumped value>` and the
    unvaried control still carries `1` (`python/graphed/preserve/manifest.py`; without these the
    bound bump is invisible to every anchor here).
  - **§9.1's plan-level `{output: [labels]}` listing, its OWN anchor** (m50's `inspect()` test
    takes a `Bundle` and cannot exercise a plan-level mapping): **in `graphed-histogram`'s flat
    `tests/frozen/m50`, NOT in `graphed`** — the anchor is fill-shaped (a named OUTPUT exists
    only in `graphed-histogram`'s group API, while `graphed`'s `aggregate_plan` carries no output
    names; in `graphed` it would `importorskip`-SKIP, §10 preamble). Over a THREE-output program —
    a sibling-mode varied output, an **AXIS-MODE** varied output, and one no variation reaches —
    the listing maps each output to its
    labels in §2.4 order, and the unvaried output maps to **`["nominal"]`** (`[]` and
    `["nominal"]` are different frozen assertions §6.1a does not settle; `["nominal"]` is the
    consistent choice because §6.1a binds a bare `hist` to read as the single label `"nominal"`
    through the narrowing helper). **The axis-mode arm is what makes the anchor discriminating**
    (§9.1): that output's slot key is `(output, None)` and carries no label, so an implementation
    reading labels off the KEY answers `[None]` or `[]` for it and is red, while a sibling-only
    program admits that implementation. Assert its entry equals the sibling output's label list —
    the two outputs carry the same variations, so the listing must not vary with the MODE.
  - **§9.1 `graphed.variations(ctx)`** (load-bearing because §6.2 explicitly refuses to give
    numeric ordering from bin index): per-name tags and kinds — **over §9.1's shape
    `{name: {tag: (kind, value | None)}}` where the kind is the `graphed.Kind` flag (`Kind.WEIGHT`,
    `Kind.SHIFT`, their union for a tag registered both ways — a `Kind` since the kinds change,
    graphed#24, which replaced the `"weight"`/`"shift"`/`"both"` strings), so the fixture registers
    ONE of each and asserts both members** — plus the parsed float value
    under **both** parsers — canonical e-form `m?\d+(em\d+)?` (`5em1` → 0.5, `m15em1` → −1.5) and
    datacard p-form `m?\d+(p\d+)?` (`2p5` → 2.5) — and a non-numeric tag (`up`) returning no
    value rather than raising.
  - **The m49 frozen-suite carryovers, homed here rather than deferred** — each is one file over
    ALREADY-SHIPPED m49 source, so m50 adds `graphed` frozen trees but no `graphed` source target
    (§10 preamble). They are frozen now because m50 is the last milestone before the write-out one,
    and each currently rides a `tests/extra` witness, which no gate protects:
    **`tests/frozen/debug/m50`** — the External ARM of §8.2(ii)'s attribution: a failure raised
    inside an External evaluator with an entry for its key becomes a labelled `StageError`, with the
    no-entry control beside it. `evaluate_ir` dispatches attribution at THREE sites — the op loop,
    the inline stage-member loop, and the External payload's evaluator — and no frozen anchor
    reaches the third.
    **`tests/frozen/frontend/m50`** (awkward-free — the required 3.14t job collects this subtree
    whole) — two arms of §8.2(i)'s correspondence. (a) The INCREMENTAL discriminator: a fixture
    whose record arena makes `IncrementalReducer`'s own original→canonical map NON-identity, so an
    accessor that skips composing it in front of the four passes is red. m49's incremental arm is
    present but vacuous in exactly that direction — it passes under the deletion it exists to catch.
    (b) The `opt_level=0` arm: the same program compiled unoptimized answers in RECORD ids too
    (§8.2(i) binds both reduction paths; a 1:1 lowering is the case where a composed map and an
    identity map are hardest to tell apart, which is why it needs its own assertion).
    **`tests/frozen/awkward/m50`** — §6.1d's UNFLATTEN HINT: the per-event-factor-against-per-object-
    value refusal names the offending factor AND points at "pass the value unflattened". m49's frozen
    blame anchor asserts the factor half only, so an implementation that drops the hint ships green.
  - Docs: a "How variations work" design.rst section with **executed** examples (the docs-sweep
    rule) covering §7.3's limitations — **all three invalidation classes, each with the scope §7.3
    binds**: the IR-level one (adding/removing a variation) is unconditional, while the
    label-RENAME class and the **by-value journal** class — which lands TWICE, once at m48
    (§7.2's (β) puts §8.2(i)'s field on `_PartitionReduce`) and once at m49 (§8.2(i) adds a field
    to `CompiledGraph`, which the write closures embed by value, §7.3) — apply only to journals
    whose `DurablePlan.process` `OpSpec` embeds the worker closure BY VALUE — the documented
    `OpSpec.from_ref` idiom (`docs/checkpoint/design.rst`) is unaffected.

- **m51 — variation-aware write-out (skim augmentation)** (repos: `graphed` +
  `uproot5-graphed-mvp`). Targets: §6.4, **plus §9.1's `graphed.selection` and §2.3d's
  `to_parquet` table entry**. Frozen anchors:
  - Superset-row anchor, against an **INDEPENDENT** reference (a reference taken from the same
    varied graph is the self-derived trap §5.2a names): the per-label reference row sets are
    computed eagerly with plain awkward, outside graphed, from the same input events (the
    `m23/test_group_plan.py` and `m7/adl.py` house pattern); the written row set MUST equal their
    union, and each universe's reconstructed rows MUST equal that universe's eager row set.
  - Bit-exact round-trip: write an augmented skim → the §6.4e reader reconstructs every
    universe's post-selection values and row set bit-for-bit vs the in-memory varied run (the m9
    comparison form). Its coverage items MAY be SEPARATE fixtures (they exercise different record
    shapes, and §6.4a's field-scoped level channel makes one mixed record legal but not
    required): a shift with object-level migration (per-label inner masks, §6.4d), **written
    through the per-LEVEL, FIELD-SCOPED `select={0: event_mask, ("Jet", 1): jet_mask}` channel**
    (§6.4a) — this fixture's written record is the MULTI-FIELD one (`{Jet: var * {…}, …}`), while
    §6.4's canonical single-collection skim (`to_parquet(events.Jet, …)`, form `var * {…}`) uses
    §6.4a's BARE depth-`k` key; state which shape each coverage item writes, since the two key
    forms are not interchangeable — **and AT LEAST ONE round-trip coverage item MUST be that
    bare-key skim, written as `to_parquet(events.Jet, select={0: event_mask, 1: jet_mask})`**
    (otherwise §6.4a's bare-key branch — new m51 source — could carry zero frozen-suite diff
    coverage under the DoD's ≥90% gate); §6.4a's per-level channel is what makes this anchor
    satisfiable at all — a single row mask cannot express it. Plus a weight-only label **whose
    stored factor is in the RECORD's own row space — `graphed.weight(c)` for a `c` reached from
    the record's context across `vary` IDENTITY links only** (§6.4b's row-space precondition; a
    selection-scoped `graphed.weight(sel)` is not storable and is refused at the entry check, so
    naming the storable spelling keeps the anchor buildable). Plus a label structurally equal to
    nominal (all-zero delta) — **which is also the OUTPUT-COLLAPSE case, and the anchor witnesses
    the REPLICATION, not only the all-zero content** (`mark_output` de-dups in `src/store.rs`, so
    `evaluate_ir` returns FEWER values than marked outputs and a positional unpack in
    `_WritePart` silently misassigns every label after the collapsed one; §6.4f binds resolution
    BY NODE ID). Plus an e-canonical numeric-tag label (`murf_5em1`): stored names embed the
    label verbatim and the reader returns the same label.
  - **`graphed.selection(ctx)` bridge** (§6.4a/§9.1): a skim written from the §2.6 context
    idiom — `to_parquet(events.Jet, select=graphed.selection(sel))` where `sel = events[mask]` —
    round-trips identically to the same skim written with the mask passed by hand;
    `graphed.selection` on a ROOT context returns `None`. (Without it the m51 sink is reachable
    only from the loose §2.1a style.) **Plus the `vary`-derived-context case explicitly**: with
    `sel2 = graphed.vary(sel, "btag", …, is_weight=True, …)`,
    `to_parquet(events.Jet, select=graphed.selection(sel2))` is ACCEPTED by (2a) and round-trips
    identically to the pre-`vary` spelling (§9.1: `graphed.selection` walks `vary` identity
    links; §6.4a(2a) admits them). **Plus the control that discriminates §6.4a(2a)'s `vary`-link
    admission from bare handle equality** (in the bullet above the `vary` link sits BELOW the
    mask derivation, so both readings accept): with
    `E2 = graphed.vary(E1, "pu", …, is_weight=True)`, `mask = gak.num(E2.Jet) >= 4`,
    `sel = E2[mask]`, the write `to_parquet(E1.Jet, select=graphed.selection(sel))` — record
    handle `E1`, mask handle `E2`, identical row spaces (a `vary` link is §6.1d kind (2),
    IDENTITY) — is ACCEPTED and round-trips identically to the same skim written from `E2` (bare
    handle equality refuses it). **Plus the RE-RECORDED-MASK positive control for §6.4a(2a)'s
    handle-equality predicate**: a `select=` value that is a RE-RECORDED equal expression — a
    distinct Python object carrying the record's context handle and the same per-label node
    ids — is ACCEPTED and round-trips identically (hash-consing gives it the same node id;
    guards against an `is`-identity implementation). **Plus the UNIVERSE/NOMINAL-derived case,
    both halves**: (a) `graphed.selection(graphed.nominal(sel))` returns **that label's member of
    the argument's own selection — an unvaried `Array`, not a `Varied`, in the GRANDparent's row
    space** (§9.1), asserted against a manually projected reference, and `None` when the argument
    is a root context; (b) passing that value as `select=` for a record read from `sel` is
    **REFUSED at record time by predicate (2a)**, naming both contexts (§6.4a(2a):
    universe/nominal projection links are not admitted — the mask lives one row space up).
  - **Entry checks (§6.4a) — each predicate anchored with the positive control IT decides**:
    (1) **multiplicity** — a write whose per-label member offsets differ from nominal's at any
    stored level is refused, **per partition at execution time from `_WritePart` before any
    buffer is stored** (`python/graphed/awkward/io.py` evaluates inside the worker; do NOT freeze
    a record-time raise); (2) **row-space agreement, SCOPED PER LEVEL** (§6.4a) — at **level 0**
    the check has two halves with two sites: **(2a) lineage, record-time** — a record whose
    context is not the one the supplied `select=` mask derives from is refused at the
    `to_parquet` call naming both contexts, with the silent-corruption case as its named
    positive: a record carrying a NON-varied embedded selection (`sel = events[nominal_mask]`,
    then `select=varied_mask`) is refused, not written on mismatched rows — and the
    chained-context case (`graphed.selection(sel2)` for `sel2 = sel[mask2]` against a
    root-row-space record) likewise; **plus the two ABSENT-OPERAND cases** (§6.4a) — a
    CONTEXT-FREE record (the loose §2.1a write style) SKIPS (2a) and IS written (the positive
    control that keeps the loose sink reachable), while a contexted record whose supplied mask
    **carries NO context handle** (a hand-built loose mask, §2.3e's Drop rule) is refused naming
    the record's context — **worded over the handle, NOT over "derived no context", plus the
    positive control that discriminates the two readings**: a mask recorded entirely from reads
    performed THROUGH the record's own context (`select=(events.MET.pt > 50)`) carries the
    record's handle by §2.3e's ORIGINATION rule while deriving no context, so the binding
    handle-equality predicate ACCEPTS it and it round-trips; **(2c) DEPTH at every supplied
    level, record-time** — a JAGGED level-0 mask read through the record's own context
    (`select=(events.Jet.pt > 25)`) is REFUSED at the `to_parquet` call naming the level and the
    per-level channel, with the flat event-level mask over the same context as the positive
    control (it passes (2a) and (2b), so without (2c) the writer silently filters OBJECTS instead
    of rows) — **plus the mirror case at level ≥ 1**: a FLAT mask supplied at level 1
    (`select={0: evt, ("Jet", 1): evt}`) is refused at the call naming the level — a record-time
    form property (otherwise the level-≥1 structural check has no operand and dies per partition
    with an `AttributeError`/`IndexError`); **(2b) row-count equality between the record and
    that mask — EXECUTION-time, per partition from `_WritePart`** like (1), NOT a record-time
    raise (row counts are data); at **levels ≥ 1** the check is structural (the mask's per-label
    offsets equal the record's at that depth) and raises per partition from `_WritePart` like (1)
    (a lineage test is unsatisfiable there — an inner mask is per-OBJECT and is not
    `graphed.selection` of any context). Positive control for the level-≥1 half: the
    `select={0: event_mask, ("Jet", 1): jet_mask}` object-migration write above still passes both
    predicates.
    **Plus §6.4a's BARE-KEY AMBIGUITY refusal**: a record with two independently jagged depth-1
    fields (`{Jet: var * {…}, Muon: var * {…}}`) supplied a BARE `1` key is refused at the
    `to_parquet` call naming the ambiguity and the field paths, with the field-scoped
    `("Jet", 1)` spelling on the SAME record as its positive control (a record-time FORM
    property, §6.4a).
    **Plus §6.4b's ROW-SPACE refusal for a stored varied field**: a write whose stored fields
    include `graphed.weight(sel)` for a SELECTION-derived `sel` is refused at the entry check
    with a message naming the ROW-SPACE mismatch (the record is pre-selection on the superset
    rows while §2.6c gives `sel`'s registry per-label row sets re-indexed by each label's mask,
    and no inverse exists) — explicitly NOT the offsets message predicate (1) would otherwise
    emit; the positive control is the storable spelling, `graphed.weight(c)` for a `c` reached
    across `vary` identity links only.
  - Representation anchors, structural (R0.10a — no size thresholds in frozen tests): appended
    columns land in the bound exact representation (XOR-delta values, packed masks) with
    identifier-shaped stored names (labels verbatim, §6.4b) — verified by reading the raw file
    schema + manifest — **plus the FIELD half of the name convention** (§6.4b): a NESTED field
    path (`Jet.pt`) is flattened per level and the skim still reads back through the manifest,
    and a name COLLISION is refused naming BOTH SOURCE FIELDS — **the fixture varies BOTH
    `Jet.pt` AND a flat field named `Jet_pt`** (the derived-vs-derived class: both derive to
    `__vary_L__Jet_pt`); a varying `Jet.pt` alongside a NON-varying `Jet_pt` is NOT a collision
    under the bound `__vary_{label}__` prefix and MUST NOT be frozen as a refusal (it is a legal
    nested-field skim); the compression WIN is an R0.11 implementer-report measurement on a real
    skim (methodology stated), NOT a frozen gate.
  - **Manifest DETERMINISM** (§6.4e binds sorted manifest keys; a content-only manifest anchor is
    satisfied by an unsorted, `PYTHONHASHSEED`-dependent serialization): the same varied write
    performed in two fresh processes under differing `PYTHONHASHSEED` yields byte-identical
    manifest bytes; minimally, the serialized MAPPING-key order is asserted sorted and the levels
    LIST is asserted in §6.4e's `(depth, field_path or "")` order ("sorted" is not a computable
    predicate over that list's heterogeneous elements, and `sort_keys=True` never reorders list
    elements).
  - Manifest: parquet KV metadata reads back and matches a **literally spelled expected KEY SET —
    which INCLUDES §6.4e's selection-LEVELS entry — with one assertion that the levels entry's
    value equals the literally spelled expected LIST, in §6.4e's bound order** (`[0, ["Jet", 1]]`
    for the object-migration item, `[0]` for the weight-only one — §6.4e binds a JSON list, so
    the expected value is spelled as a list, never a Python set; the levels entry needs its own
    assertion because the round-trip anchor supplies both levels itself and cannot discriminate a
    reader that never consults it); the augmented file also round-trips through `ak.from_parquet`
    (the arrow-write path must reproduce awkward's own KV entries, §6.4e); an unvaried write
    keeps the `ak.to_parquet` path, carries NO manifest, and is byte-identical to today — **as a
    SAME-PROCESS comparison, never a committed `.parquet` fixture** (§6.4g: a parquet footer
    embeds its writer version, so a committed blob breaks on a pyarrow bump and across §A.5
    matrix legs while the behaviour is correct — R0.10a). Committed byte oracles stay for GIR/IR
    goldens (§6.3), whose only framework-version bytes are the `External` payload descriptor's,
    which §6.3 strips per side — the committed literal at capture, the live blob at assert time.
  - **Structure refusal (negative anchor, §6.4d)**: a stored varied field whose per-label offsets
    differ from nominal's is refused with an error naming the label and the field — with a
    positive control that a same-multiplicity shift with object-level migration still writes and
    round-trips.
  - **§6.4f WRITE-PATH optimizer-merge refusal** (§6.4f settles that §7.2's refusal guards the
    write path, binding new m51 source): a varied `to_parquet` whose per-label expressions
    include an optimizer-mergeable spelling — a label whose value is `w * 1.0`, which §1.1 makes
    first-class via `variations={s: w * float(s)}` and the M4 identity tokens merge — is REFUSED
    at the `to_parquet` call with §7.2's message and workaround, with an UNVARIED positive
    control that today's write path is unchanged (§6.3). The check is affordable there:
    `to_parquet` already compiles at the call (`compile_ir` runs in
    `python/graphed/awkward/io.py`).
  - **§2.3d table entry for `to_parquet`** (absent from m48's table and floor list, so nothing
    frozen has to change here): with §6.4's `select=` landed, `graphed.awkward.to_parquet` ENTERS
    the table as *accepting* and joins the named floor list — the m51 entry asserts the accepting
    behaviour, i.e. a `Varied` RECORD and/or a `Varied` `select=` (both arms) is consumed
    internally and no per-label result is returned to the caller.
  - ROOT half: `graphed_write` gains IR evaluation (derived columns in ROOT skims — the §6.4f
    ROOT half) with a DERIVED-COLUMN round-trip anchor. A variation-aware ROOT write-out is
    Phase-2 (§11), so no varied ROOT reader/manifest is frozen at m51.
  - **numpy-backend refusal (§6.4f), in `graphed`'s `tests/frozen/numpy/m51`** (it is
    `graphed`-side source, `python/graphed/numpy/io.py`; unique basename per §10's rule). **The
    anchor is worded over §6.4f's trigger**: `graphed.numpy.io.to_parquet(<a Varied>, …)` raises
    a graphed error naming the awkward backend (`graphed.numpy.to_parquet` is not a package
    attribute, so the module path is the entry point). Do NOT freeze a `select=` arm — that
    keyword is bindingly not added to the numpy idiom and stays a plain `TypeError`.
  - Docs: the §7.3 checkpoint paragraph gains m51's write-path scope: widening `_WritePart`
    (§6.4f) churns **no shipped journal** — `write_plan` builds a plain-callable `Plan`
    (`write.py`) and the checkpoint runner takes a `DurablePlan` (`checkpoint/runner.py`) — so
    the churn sentence is scoped to a journal a caller built by wrapping the write closure via
    `OpSpec.from_callable`.
  - Single-read witness on the augmented write run (§5.2b form).

Definition of Done per milestone = the standard checklist (root `CLAUDE.md` §E.0): targets exactly
as specified, frozen suite green and unmodified since freeze, ≥90% diff coverage from the frozen
suite, determinism gate, ruff/clippy/mypy-strict over each repo's configured scope (R0.4a; the
src-only configs are that rule's own cross-cutting cleanup, not an m48–m51 target), Sphinx `-W`,
full-matrix CI green at the pinned revision (R0.5), attempts log + reviewer APPROVE recorded.

## §11 Out of scope (Phase 2 — named, not silently dropped)

Declarative nuisance registry / config layer (mkShapesRDF-style `{name, type, kind, samples}`);
correlation/decorrelation **export** metadata (datacard/HS3 serialization of a point, the `up ≡ +1σ`
convention) — correlation-by-name and the Session point registry ship in m52; envelope/RMS/symmetrize post-aggregation ops; dataset-level
variation automation (separate-sample variations stay a partition-metadata pattern, documented);
lossy/ratio ("1+delta") storage for §6.4 reconstruction columns (it is NOT bit-exact; any opt-in
must leave §6.4c's exact default intact); per-variation file fan-out (one file per universe — §6.4
appends columns instead; the `part_path` prefix/suffix seam exists in `write.py`);
a **variation-aware ROOT write-out and reader** (its own manifest channel + delta/packbits storage;
m51's ROOT half is derived-column IR evaluation only, §6.4e/§6.4f);
auto-symmetric weight derivation from a lone `up` (§2.6b);
**user-declared `"variation"` axes** for §6.2 (the frontend declares them in v1; a user-constructed
variation axis is unfillable today — `Histogram.fill` requires one array per axis
(`graphed-histogram src/graphed_histogram/boost.py`) — and supporting it needs a fill-arity
carve-out plus a declared-vs-inferred reconciliation rule);
**a HISTOGRAM-TERMINAL preservation bundle** (§9.2 bundles the value/weight/spec triple, so
`reproduce` returns count arrays; serializing the fill graph instead would round-trip the §6.2
variation axis and its storage, but it carries the `histogram.weight_guard` `External`, for which
no preserve plugin is registered — the plugin becomes a target only if that widening is adopted);
per-variation monitor/dashboard axis; stage-granular checkpoint task ids (the §7.3 fix);
variations crossing Exchange/Join boundaries (§5.4); the *undirected* full grid across INDEPENDENT nuisances (a joint universe the graph cannot infer as dependent — m53 pulls in dependency-driven cross products, minting the joint AUTOMATICALLY when a member consumes another nuisance's varied nodes, while independent families stay union; `systematics-design/dependency-fanout-design.md`); weight
clamping/validation hooks (narf `theory_weight_truncate` precedent); growth category axes;
**per-sample divergence of the variation-label set** (merging outputs across samples whose label
sets legitimately differ — the exemplar's suffix-blacklist pathology, lit §ewkcoffea-confirmed;
§6.1a governs one program's outputs, not cross-sample merging); a constant/scalar-Array broadcast
helper needing NO shape donor (§4.1's normalization gap — `gak.full_like` covers the donor case);
a **gak inner-index verb** (`arr[:, i]` on the awkward idiom — absent from gak, §2.6 note (i); the
`gak.firsts(arr[gak.local_index(arr) == i])` spelling covers the PDF-member case today —
ergonomics, not a blocker; not scoped into m48–m51);
**full support for labels the OPTIMIZER merges** (§7.2: distinct record ids that the M4 identity
/commutativity rules collapse into one compiled output — m48 REFUSES them with a named workaround;
replicating such a value across its labels needs §8.2(i)'s record→reduced map on the frontend unpack
path and is not scoped in m48–m51);
an **in-IR bit-view / `packbits` verb** (§6.4c's XOR deltas are computed in `_WritePart` on
evaluated buffers because no recorded form exists — `float32 ^ float32` is a `TypeError` in both
numpy and awkward, and gak ships no `view`/`packbits`/`frombuffer`);
**multiplicity-changing stored variations** for §6.4 (shift-dependent cleaning / overlap removal /
matched collections: no representable same-shape delta, refused in v1 per §6.4d);
**a contexted fill that suppresses the AMBIENT weight while applying its own explicit factor**
(§6.1d: `unweighted=True` suppresses both, by design — the v2 answers are a context-level detach
verb or a narrower `unweighted=` scoped to the ambient factor alone); a first-class Rust `Vary`
NodeKey.

## §12 Process and bookkeeping

- **§12.1 (Forward process, owner decision.)** The plan-review cycle is CLOSED; no further plan
  rounds run. Residual sharpening happens in m48 decomposition against the §12.4 ledger, not in
  plan rounds. Each milestone m48–m51 runs the gated three-role pipeline: test-author writes and
  freezes the acceptance suite (TEST_SANITY: collects, non-vacuous — fails the stub for the right
  reason — deterministic, coverage-wired), implementer iterates under the full R0.4 mechanical
  gates without ever touching `tests/frozen/**` (disputes via `.graphed/<mX>/disputes/`, the m39
  precedent). **The gate command is PER REPO**: `graphed` runs
  `python -m graphed_orchestrator.precommit . --fast` (which keeps the toml, workflow, INTEGRITY
  and prek checks and drops only the suite/docs legs) PLUS `COV=1 ./scripts/run-tests.sh` for the
  suite and the combined ≥90% gate, because the unqualified command cannot derive that repo's
  coverage command (no single `pytest --cov` CI line) and falls back to a repo-root `pytest` that
  cannot collect the split tree; Sphinx `-W` rides `graphed`'s own `docs` CI job. Every other
  repo runs `python -m graphed_orchestrator.precommit .`. **The integrity scan is never the leg
  that gets dropped** (root `CLAUDE.md` §A.7/§B.6). Reviewer judges intent/guardrails/technique
  and may REJECT; implementation review runs the design / integrity / mutation three-lens pattern
  (m46/m47 precedent) at the BLOCKER / HIGH / MID / LOW / NIT severity terms, cycling until
  clean, empowered to send work back to planning. R0.5 pins DONE to full-matrix CI green.
  R0.10/R0.10a govern every witness; R0.11 governs every number in every report.
- **§12.2 (Worklogs.)** `systematics-vary-worklog.md` continues as the dual memory; per-milestone
  `.graphed/<mX>/attempts.md` as always.
- **§12.3 (Bookkeeping amendments, on landing.)** (a) Draft **R23** for the root prompt binding
  §§1–9 outcomes (the R22 precedent: separate draft file, owner inserts); (b) amend the root
  prompt Out-of-scope bullet in `graphed-root-prompt.md` and the two inline R22.0/R22.10
  "systematics-as-a-graph-axis stays Phase 2" mentions to point at R23; (c) edit root `CLAUDE.md`
  Part F likewise; (d) un-park the `ops_catalog.md` row into a milestone-tagged Section-C row
  (the `test_catalog.py` lock-step is text-presence-only and is preserved); (e) memory-file update.
- **§12.4 Closure ledger (deferred to m48 decomposition).** Items the closure deliberately did
  NOT specify further; the decomposition pins each one before the milestone that consumes it.
  Nothing here is a new requirement — each is a naming/normalization choice inside an
  already-bound rule.
  - (1) **§3.4/§5.3 two-form operand.** Both verbs take
    `Sequence[Varied] | Mapping[str, Sequence[Array]]` so the primary sink (§9.1's
    `fill_nodes_by_label`) is reachable; §3.4 binds the rejection of a mixed, ill-formed or nested
    operand and §9.1 the annotation. Only the exact SPELLING is pinned at m49 freeze.
  - (2) **§6.4f numpy refusal.** The trigger (a `Varied` first positional) and entry point
    (`graphed.numpy.io.to_parquet`) are bound; the error CLASS and message wording are pinned at m51
    freeze. The numpy idiom bindingly gains no `select=` keyword, so no m51 anchor freezes that arm.
  - (3) **§8.2(i) producer cost.** The bound recipe walks one record CONE per label inside
    `plan()`. Its cost is bounded by the per-label cone size (the same traversal §3.4's verb
    performs) and is a driver-side, once-per-plan walk; m49 decomposition confirms it against §3.3's
    budget and states the measurement (R0.11) rather than assuming it here.
  - (4) **§8.2(i)'s `CompiledGraph` correspondence field.** Its shape and owner are bound in
    §8.2(i); the field NAME and the accessor's exported spelling are pinned at m49 freeze, like the
    verbs in §9.1.

---

Revision history lives in git and the `systematics-vary-plan-revision-r*-notes.md` files;
evidence trails live in the two research companions.

