# Systematic variations in graphed — `vary`, the variation frontend + IR treatment (execution plan)

Status: **r28 — design extraction of the review-clean r27.** Rationale (PART I) is context and
binds nothing; PART II binds. Committed in the meta repo (`graphed-org/graphed-project-mvp`)
together with its research companions. Measurements and evidence trails live in the files the
plan cites — `systematics-vary-codebase-analysis.md` (cited *cba §agent*) and
`systematics-vary-litsearch.md` (cited *lit §agent*) — or are explicit stated assumptions.
Source directive: the owner's high-level doc (Google Doc `116lg4…`, mirrored at
`scratchpad/systematics-plan.txt`). The plan-review cycle is closed (§12.1); review history
lives in git and the `systematics-vary-plan-review-r*` / `systematics-vary-plan-revision-r*-notes`
files. Next step: the m48 decomposition against the §12.4 ledger.

> **Naming — owner decision.** Verb **`vary`** (`graphed.vary`), concept noun **"variation"**,
> container **`Varied`**. Variation labels are `f"{name}_{tag}"` underscore style (`jes_up`,
> `btag_down`); **`"nominal"` is reserved** for the central value. This matches RDataFrame's
> `Vary` precedent (lit §rdf-vary §6), graphed's lowercase-verb convention (`join`,
> `repartition`), and — verbatim — the stored corpus reference names (cba §corpus §1).

## Scope deviation (flagged, deliberate — the R22.0 pattern)

The project plan lists **systematics-as-a-graph-axis** as Phase 2 wherever the Phase-2 listing
appears: the root `CLAUDE.md` Part F block, the root prompt Out-of-scope block ("treating
systematic variations as a graph axis"), inline in R22.0 and R22.10, and the corpus ops catalog
("Systematics-as-a-graph-axis (named axes / template instantiation) — cf. RDataFrame `Vary`",
`ops_catalog.md`). **The project owner has decided to pull it into scope now** (this doc's source
directive). Consistent with "THE PROJECT PLAN ALWAYS WINS," the deviation is deliberate and
flagged, not silent: this doc records it; the root prompt gets an **R23** entry binding it once
landed (§12.3). The pull-in is *smaller* than R22's: no new execution substrate — the work rides
the existing IR/interning, group-plan, and executor machinery, which the evidence shows were built
expecting exactly this load (Part I §1).

---

# PART I — RATIONALE (context; non-binding)

## 1. Why now: the system was built for this and the anchor tests already exist

- Systematics bookkeeping is "the largest pain point in analysis software" in the field's own
  assessment (Second Analysis Ecosystem Workshop report, arXiv:2212.04889 — lit §rdf-vary §5).
- graphed's founding rationale names variation-multiplied graphs as *the* scaling driver: "On real
  analyses with many systematic variations the graph reaches tens of thousands […]"
  (`graphed-root-prompt.md`); the corpus `graph_bloat_note.md` quantifies it (full AGC weight +
  JES/JER + b-tag set ⇒ O(10⁴) nodes; dask-awkward's per-layer×partition model is what died there —
  cba §corpus §5). M4's optimizer was hardened for it in advance: the egg extractor was redesigned
  O(N) specifically because recursive extraction "blows up … on the deep chains a systematics graph
  produces" (`src/optimizer/engine.rs`), and frozen `tests/frozen/core/m4/test_systematics.py`
  already pins that a 3300-variation, ~10⁴-node graph reduces in < 1 s to a node count
  **independent of variation count** (cba §corpus §4).
- The acceptance anchors pre-exist: the corpus canonical systematics analysis (weight = b-tag SF ±,
  photon-ID SF ±; shift = JES ± applied *before* selection) ships stored reference histograms
  with fingerprints and the behavioral frozen tests `test_weight_variation_preserves_selection` /
  `test_kinematic_variation_changes_selection` (strict `jes_up > nominal > jes_down` selected-count
  ordering) — `tests/frozen/corpus/m05/` in the consolidated repo (cba §corpus §1,§3).
- What exists today is caller-side replication only: m05 calls the analysis once per variation
  string; the m9 preservation fixture bakes the variation into per-bundle build config ("one graph
  per variation", `tests/frozen/preserve/m9/agc.py`); no frontend/IR construct expresses
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
control flow entirely**: zero uses of `Vary`. Weight systematics are per-event
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
coffea Discussion #469 reports ~2-3× (up to ~7-8× for many systematics) for vectorized
(extra-axis) systematics over re-run loops — word-level UNVERIFIED (lit §coffea-sys carries the
caveat).

**Pythonic analyses** (lit §pythonic-analyses): nsmith-/boostedhiggs, PocketCoffea,
TopEFT/topeft + cmstas/ewkcoffea.
**Kelci's analysis — owner-confirmed: `cmstas/ewkcoffea`**, promoted to the
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
**`FNALLPC/wwz4l`** (lit §ewkcoffea-confirmed addendum):
named as a modern-coffea version, it is **neither** — a coffea-0.7-era CMS-DAS
teaching derivative of `ewkcoffea@main` (`main@cc71718`; a near-verbatim processor copy with
byte-identical `ApplyJetSystematics`; zero dask/`dataset_tools`/`hist.dask` surface).
It carries the full weight+shift treatment (27 labels) and adds no
dask-era evidence, so `coffea2023@63abb06` remains the sole modern-coffea exemplar and the
no-dask-era-object-shift finding extends to it. Its distinct value: the teaching strip removed
every piece of *physics* (BDT, EFT, 54→14 categories) while the **variation scaffolding survived
completely intact** — the loops, deepcopies, exclusion rule, growth axes, and suffix generator are
irreducible accidental complexity by construction, which is precisely what `vary` deletes.
Universal conventions across the surveyed analyses: `"nominal"` reserved; `Up`/`Down`-suffixed
labels; **shift × weight cross products never produced** (under a kinematic shift, only the central
weight fills — evaluated on that shift's selection); one histogram with a `systematic` StrCategory
axis; data special-cased (no shifts, no variation axis). Universal failure modes: whole-chain
re-execution per shift; defensive `copy.deepcopy` of accumulate-by-mutation Weights;
hand-maintained name lists where a typo silently drops a systematic; per-variation cutflow
clobbering; skim-vs-shift interaction requiring an OR-of-selections mask.

## 3. Why this architecture: record-time expansion + interning, not a new node kind

Three candidate shapes were evaluated against the codebase (cba §ir-rust, §optimizer,
§frontend-python):

1. **A first-class boundary `Vary` NodeKey** (Exchange/Join sibling). Rejected for the core
   mechanism: every non-`Op` kind is automatically a stage boundary (`src/node.rs`) and
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
   varied input, so the unvaried prefix is shared **exactly** — going N=1→2 variations grows the
   arena by precisely the varied suffix, reduction stays linear in variation count, and the
   reduced form is one shared-prefix stage + one stage per variation (cba §optimizer §2,§5). DCE,
   fusion, projection, determinism, and every executor need **zero changes** for correctness —
   `R` is opaque end-to-end (cba §exec-checkpoint §4).

The source directive's open question — "is it useful to add optimization impact analysis to isolate
subgraphs a variation must re-run?" — **resolves to: it already exists structurally.** The impact
set of a shift IS the set of nodes reachable from a label's outputs but not from nominal's; RDF
computes the same thing by hand with dependency-tracked clone caches. We expose it as a trivial
read-only API (§3.4), and build no invalidation machinery (none exists and none is needed —
cba §optimizer §5).

Weight vs shift needs **no API distinction** (RDF lesson: the dependency structure discovers the
difference — a varied weight only reaches the fill; varied kinematics reach the cuts). It does need
**distinct lowering economics** at the sink, which §4/§5 bind separately.

**Why systematics attach to the event record (owner semantic correction).** Earlier
sketches threaded loose `Varied` weights into each fill by hand — re-creating the survey's
forgotten-weight/name-list failure mode and mismatching the physicist's model, on which all three
precedents agree: RDF's weight is a *column of the frame*, coffea's `Weights` belongs to the
*event batch*, boostedhiggs expresses shifts as *collection replacements on `events`*. Systematics
are ambient properties of the event record; the fill is where everything applicable applies
simultaneously (plotting Jet pT must also yield the pileup-reweighting universes). §2.6 binds the
event context (attach-once, ambient thereafter) and §6.1d the fill inference; the one genuine
tension — selection-dependent object SFs cannot be ambient on the root — is resolved by derived,
registry-inheriting contexts rather than the exemplars' per-channel `deepcopy`.

**Why the context surface is functional, and why write-out enters scope (collaborator feedback).**
A context that reserves attribute names on the event record (`events.weights`,
`events.vary`) was rejected — that namespace belongs to the *tree*: branch names are
analysis-controlled and open-ended, so ANY reserved name is a latent collision (a branch named
`weights` is entirely plausible), and a mutable registry leaves no object identity for provenance
to hang on. The surface is one functional verb — `graphed.vary(...)` always returns a NEW
context/container, never mutates — which (a) frees the record namespace completely (§2.6a),
(b) makes each variation step an object with lineage, the provenance the collaborators asked for
(§2.6b), and (c) makes the fill-time registry snapshot rule plain immutability (§2.6c). The same
principle resolves a related ambiguity: `Varied[label]` collides with awkward's string-getitem
field access; extraction moves to module functions too (§2.2). The same feedback surfaced the
missing sink: skims. Two surveyed frameworks hit exactly this wall and bolted around it — RDF
Snapshot needed a per-event validity bitmask bolt-on, mkShapesRDF re-implemented `Vary` wholesale
for its Snapshot stage (suffixed columns + OR-of-cuts, Part I §2) — and graphed's write path is
greenfield: zero variation machinery, zero metadata use, one seam method per backend.
§6.4 binds the native treatment: superset rows by
OR-of-selections, appended exact-by-construction reconstruction columns (XOR bit-deltas are exact
by construction; a "1+delta" float ratio is not bit-exact), packed varied-cutflow masks, and a
manifest in existing metadata channels.

## 4. Honest costs (the requirements in PART II that mitigate each)

- **Build-time cost**: expansion re-executes the user's downstream *recording* code per variation
  (Python-side). Mitigated by the incremental reducer (per-step cost ∝ delta) and bounded by a
  variation-shaped anti-quadratic benchmark (§3.3).
- **Partial size ×N**: every reduction-tree slot carries the N-variation composite. Mitigated by
  the variation-axis fill mode (§6.2, O(1) objects) and `pooled_combines`/peer reduction; gated by
  the milestone benchmarks (§10).
- **Checkpoint granularity**: `task_id` folds the **whole plan IR** (`plan.py`), so
  adding a variation later invalidates every cached task even though the graph shares nodes.
  Documented limitation (§7.3); stage-granular content addressing is named Phase-2 follow-up (§11).
- **Union projection**: a merged plan reads the union of nominal + shifted columns for all
  partitions (`aggregate.py`). Accepted for MVP; per-variation projection stats surface the
  cost (§5.3).
- **Boundary interaction**: the m39/m40 plan builders consume exactly one Exchange/first Join
  (`shuffle.py`); v1 therefore restricts variations from crossing shuffle boundaries
  (§5.4) rather than silently miscompiling.
- **Skim growth**: the §6.4 superset+augmentation write stores more rows (OR of selections) and
  more columns than a nominal-only skim. Mitigated by exact-by-construction deltas that are zero
  wherever a label agrees with nominal (maximally compressible) and packed masks (§6.4c); bounded
  by the m51 report measurement on real skims.

---

# PART II — REQUIREMENTS (binding; specific)

## §1 Vocabulary (owner decision)

- **§1.1** Verb `graphed.vary`; container `graphed.Varied`; concept "variation" everywhere (docs,
  APIs, tests, R23). The reserved central label is the string `"nominal"`; user variation labels
  are `f"{name}_{tag}"` (e.g. `jes_up`). **Tag grammar (e-form canonical; owner decision):**
  `up`/`down` are conventions, not specials — σ-families, PDF member indices, and
  stringified-float families (μR/μF scale factors, σ-scans; correctionlib category inputs are
  arbitrary strings — `preserve/m9/agc.py` — so a float-spelled key is expressible, §4.1) are all
  first-class. A `name` MUST be a valid Python identifier. A **tag** is a string matching
  `[A-Za-z0-9_]+` — every label is therefore itself a valid identifier, usable verbatim as a
  StrCategory bin (§6.2), result key, manifest key, and on-disk column/branch name (§6.4). It is
  NOT necessarily spellable as *literal* kwarg syntax: canonical numeric tags are digit-leading
  (`2=`, `102=` are SyntaxErrors), which is exactly what the `variations=` channel exists for
  (below). Floating-point tags use the **e-encoding** (owner-selected): the canonical numeric
  form is `m?\d+(em\d+)?` — integer values render as plain digits (`2`, `102`, `m2` for −2; PDF
  indices are untouched), fractional values as minimal-mantissa scientific notation with `em`
  for the negative exponent (`0.5`→`5em1`, `2.5`→`25em1`, `1.2345`→`12345em4`, `-1.5`→`m15em1`,
  `1e-8`→`1em8`; a fractional value's exponent is negative by construction, so bare `e` never
  appears in canonical form; **negative zero canonicalizes to `0`**, never `m0` — one value, one
  label; and a canonical tag longer than **32 characters is REJECTED** — a tag-sanity bound and
  nothing more: it covers every real σ-scan / μR-μF / PDF family, but it does NOT bound the
  label (`f"{name}_{tag}"`) or the on-disk name (`__vary_{label}__{field}`, §6.4b), both of
  which also carry the user's arbitrary `name` and field; **the input grammar below states no
  magnitude bound, so a large-magnitude INTEGER-valued input is the one spelling the grammar
  admits and the cap then refuses** — `"1e40"` renders as 41 plain digits while `"1e-40"`
  renders as the 5-character `1em40`, so an integer-valued input whose plain-digit rendering
  exceeds the cap is rejected **at canonicalization with a message naming the magnitude**, not
  with a generic tag-length error; **the magnitude test runs on the COMPUTED DIGIT COUNT BEFORE
  any rendering, and the canonical string is produced only once that count is within the cap**,
  with the normalization: the count is (the input's mantissa digits after removing the decimal
  point and stripping leading zeros) + (the exponent adjusted for where that decimal point sat),
  NOT a naive "mantissa digits + exponent", which is off by one at the boundary for a dotted
  mantissa (`"1.5e31"` renders as `15` followed by 30 zeros = 32 plain digits, exactly at the
  cap and LEGAL, while the naive sum gives 2 + 31 = 33 and rejects it); **m48's grammar anchor
  carries that BOUNDARY PAIR**: `"1.5e31"` ACCEPTED with the 32-digit canonical tag and the
  33-digit neighbour `"1.5e32"` rejected with the magnitude message — the accepted half is the
  discriminating one, since the naive sum rejects it; **the quantity compared against the cap is
  the RENDERED CANONICAL LENGTH under BOTH renderings**: for an integer-valued input it is the
  normalized digit count, plus 1 when negative — the `m` sign marker is a character of the
  canonical tag but not a digit; for a FRACTIONAL input the normalized count is not the rendered
  length at all, since the adjusted exponent is negative by construction (a 31-digit-mantissa
  fractional value has a normalized count of 31 − 35 = −4 while rendering as 35 characters), so
  the compared quantity there is `len(mantissa) + 2 + len(exponent)`, again plus 1 when
  negative. **The two refusals are split by CAUSE**: an input whose INTEGER digit count alone
  exceeds the cap is rejected with the MAGNITUDE message (`"1e40"`, `"1.5e32"`); every other
  over-cap case is rejected with a canonical-tag-LENGTH message naming the rendered length — the
  sign marker pushing an otherwise legal magnitude to 33 characters (`"-1.5e31"`: 32 digits,
  legal magnitude, 33 rendered characters) and the long-mantissa fractional case alike.
  `"-1.5e31"` carries a legal magnitude — `"1.5e31"` is ACCEPTED with the same magnitude — so it
  takes the length message, since a diagnostic must not blame the wrong property (the same
  standard as §6.1d's loose-value message split and §6.4b's row-space-not-offsets message). The
  input grammar states no magnitude bound, so `"1e1000000000"` is legal input and a
  render-then-measure implementation would materialize a one-billion-digit string before the cap
  could refuse it) — chosen for its uniformly parseable numeric structure over the WHOLE float
  range (parse = `m`→`-`, `em`→`e-`, then a standard float literal), at the cost of not reading
  as the decimal at sight (the datacard p-form `2p5` does; p-encoded tags remain legal
  identifier tags, see below). `vary` ACCEPTS plain float spellings as input sugar: a tag
  matching `-?\d+(\.\d+)?([eE][+-]?\d+)?` (`"0.5"`, `"-2"`, `"2.0"`, `"1e-8"`; no leading `+`,
  no `inf`/`nan`, no `_` separators or whitespace) is **canonicalized at call time** by exact
  decimal-string arithmetic (never an IEEE round-trip — no float artifacts enter labels) to the
  form above, so `"2"`, `"2.0"`, `"2e0"`, and `"20e-1"` all yield the SAME tag `2`. **A tag that
  already matches the canonical numeric grammar is canonicalized too — re-rendered minimally**
  (`"50em2"` → `5em1`, `"05"` → `5`); without that rule a hand-typed non-minimal e-form is not
  matched by the input-sugar grammar above (it contains `m`) and would ride through as an
  ordinary identifier tag, giving two labels for one value — caught only when both spellings met
  in one family. **"Unify" means ACROSS calls**: two separate `vary` calls spelling `"0.5"` and
  `"5em1"` name the identical label `murf_5em1`; the same two spellings *within one call* are a
  duplicate-after-canonicalization rejection (below), the same shape as the cross-notation
  `{"0.5", "0p5"}` case. A dotted or signed spelling never reaches a label. The rationale for
  canonicalizing at all is measured, not taste: dotted names store byte-exact but are
  unreadable-by-name (`ak.from_parquet(columns=["murf_0.5"])` is silently empty; a dotted uproot
  RNTuple field is reachable via `__getitem__` — exact lookup runs first — but `RField.array()`
  FAILS, because `to_akform` (`behaviors/RNTuple.py`) splits the field path on `.`
  (`KeyInFileError: 'murf_0'`), while `ntuple.arrays(["murf_0.5"])` works — the hazard is
  per-field access, not wholesale unreadability; the TTree writer uses `.` as its own nesting
  separator), while identifier-shaped names round-trip byte-exact AND readable in every measured
  path. Normalization kills spelling multiplicity by construction; the one residual duplicate
  class is **cross-notation**: a p-encoded identifier tag (`"0p5"`) does not canonicalize but
  p-parses to the same value as `"0.5"`→`5em1`, so two tags in one family that both parse as
  numbers (under either notation) MUST NOT parse numerically equal (`{"0.5", "0p5"}` and
  `{"2", "2p0"}` are rejected — distinct labels for one value would silently create semantically
  duplicate universes, distinct StrCategory bins, and distinct content hashes). **"FAMILY" is
  defined here, once, and the check spans calls**: under a per-call reading,
  `vary(ctx, "murf", w_nom, is_weight=True, variations={"0.5": a})` followed by the same call
  with `variations={"0p5": b}` would be ACCEPTED — two labels, two universes, two StrCategory
  bins and two content hashes for ONE value, exactly the hazard this rule exists to prevent and
  uncatchable later, since the p-form deliberately does not canonicalize. (The illustration is
  spelled in the WEIGHT form (b): an event-context target with NO `is_weight` is overload (c),
  the shift form, in which `variations=` is REJECTED with an error naming `collections=` (§2.1),
  before the family check can run.) **A family is the set of tags carried by one `name` on one
  container, INCLUDING labels inherited through §2.1 stacking.** **For a CONTEXT target the
  per-`name` tag map §2.2 retains lives on the container the call registers into — the
  ambient-weight `Varied` in the weight form (b), the replaced collections in the shift form (c)
  — so the family check has a named operand from m48, one milestone before
  `graphed.variations(ctx)` (§9.1, m50) exports it.** The numeric-equal check therefore runs
  against inherited labels of the same `name` too — it is the same parse the check already
  performs — and the m48 grammar anchor carries the two-call cross-notation case. (Encoding
  decision, owner: the owner's scaled-integer proposal — carry the scale as an exponent suffix,
  `1.2345`→`12345e-4` — is self-describing and, in identifier-safe rendering, IS this e-form;
  selected over the datacard p-form for the uniform full-range grammar and native numeric
  structure. Trade-off: hand-typed datacard tags (`0p5`) do not unify with float spellings
  (`"0.5"`→`5em1`) — the cross-notation rejection catches in-family mixes; p-tags stay legal
  identifier tags.) Tags arrive through **THREE channels**: **kwarg names** (`up=…, sig2=…`),
  the `variations={tag: …}` mapping, and — in the shift form (c), where `variations=` is
  REJECTED — the **INNER keys of the collection mappings** (`Jet={"up": …}`,
  `collections={Name: {tag: …}}`). Validation and canonicalization are **channel-independent**
  across all three: literal kwarg syntax cannot spell dotted or digit-leading tags (`0p5=` is a
  SyntaxError), but CPython admits any string key through `**`-unpacking, so every channel
  applies the same rules; `variations=` is simply the documented route for such tags. Arbitrary
  hashables are REJECTED (labels serialize into specs, files, and manifests; string-only — a
  float tag is passed as its string, never as a Python float, so the user owns the spelling).
  `vary` MUST reject, at call time: duplicate labels after canonicalization (within the call,
  within the container, or colliding with inherited labels, §2.1), numeric-equal tag pairs
  within a family (above), a tag supplied both as kwarg and in `variations=`, malformed or
  non-string tags (including Python floats — pass the string), and empty tag sets.
  **`"nominal"` is reserved as the central LABEL and is unreachable as a user label BY
  CONSTRUCTION, not by a rejection**: `label = f"{name}_{tag}"` with a non-empty identifier
  `name` and a non-empty `tag` means every user label contains at least one `_`, while
  `"nominal"` contains none. The TAG `nominal` stays legal — §2.1 says so explicitly and routes
  it through `variations=` because it shadows a signature keyword — and it yields the ordinary
  label `pu_nominal`, distinct from the reserved central label.
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
  REJECTED in the shift form (c) with an error naming `collections=`. This is the §2.6a
  no-reserved-names hazard re-surfacing at the signature instead of on the record; the m48
  grammar anchor covers all of the shadowed names.
  **What a MEMBER may be is stated once here, and it is not "an `Array`"** — the stacking rule
  below is written for and requires `Varied` members, and this section's own mainline sketch
  passes a `Varied` (`btag_sf(sjets)`, `sjets` being `Varied`) as `nominal=`/`up=`/`down=`
  (§2.6 sketch): **a member may be an `Array` OR a `Varied`.** In
  overloads (a)/(c) a `Varied` member is reduced to its central universe (`graphed.nominal(v)`); in
  overload (b) a `Varied` factor is KEPT and consumed label-aligned per §2.4 (`factor[L]`, falling
  back to its central universe when L is new to the factor). The construction checks below apply per
  member of the flattened container.
  Three binding overloads:
  (a) **Array | Varied target** (the loose primitive):
  `graphed.vary(jets, "jes", up=j_up, down=j_dn) -> Varied` with the target as `"nominal"`.
  `is_weight=True` and `nominal=` are invalid here (a loose weight variation is just a `Varied`
  used in a `weight=[…]` factor list, §4.2).
  (b) **Event-context target, weight form** (`is_weight=True`): `nominal` (third positional) is
  the central per-event weight factor and every member is a per-event weight factor —
  `graphed.vary(events, "pu", pu_nom, is_weight=True, up=pu_up, down=pu_dn) -> new context` with
  the factor registered into the returned context's ambient weight (§2.6b).
  **The factor's ROW SPACE is bound here, because nothing else binds it and the stacking rule
  below multiplies against it**: the registered factor — and every member of a `Varied` factor —
  MUST live in the TARGET context's row space, i.e. be read through that context or through an
  ancestor of it. An ANCESTOR-handled factor is re-indexed to the target across the intervening
  lineage links per §6.1d link kinds (1)-(3), exactly as §6.1d re-indexes an ancestor VALUE at a
  fill; **the violation half is TOTAL**: **a factor whose handle is neither the target's own nor
  an ANCESTOR of it — a DESCENDANT handle as much as a divergent one — is a construction-time error
  naming both contexts and the DIRECTION of the mismatch.** The descendant case is the natural
  mis-spelling `graphed.vary(events, "btag", btag_sf(sel.Jet), is_weight=True, …)` that registers a
  selection-scoped SF onto the ROOT context: it is not divergent, so a divergence check alone passes
  it, and no re-indexing exists in that direction, a mask having no inverse (§6.4b makes the same
  argument) — left unbound it records cleanly and dies at execution. A factor computed from a value
  read at the PARENT (the natural spelling for a jet-derived SF reusing a pre-selection collection)
  sits at the parent's row count while §2.6c re-indexes the derived context's inherited members to
  `|sel_L|` rows, and the stacking product `old_ambient[L] × factor[L]` records cleanly —
  `Session.record_op` validates only the backend's `op_form`, never lengths or row spaces —
  dying at execution with a message §6.1d's refusal contract does not cover (that contract is scoped
  to a fill's weight factors, and §6.1d's link-kind re-indexing runs at the FILL, too late: the
  mismatch is already interned). The resulting invariant is the one §6.4b's precondition assumes:
  **`graphed.weight(ctx)` always answers in `ctx`'s own row space.** m48's stacking anchor carries a
  positive control registering a factor computed at the PARENT context, and the descendant case as a
  negative control.
  (c) **Event-context target, shift form** (no `is_weight`): each kwarg names a **collection**;
  each value maps tags to varied records — `graphed.vary(events, "jes", Jet={"up": j_up, "down":
  j_dn}, MET={…}) -> new context` with every named collection replaced by a `Varied` (all
  collections in one call MUST share one tag set — the lockstep Jet+MET form; §2.6a).
  **`nominal=` is REJECTED in the shift form**, with an error naming `collections=`, mirroring the
  `variations=`-in-(c) refusal: in the shift form the collections' central members come from the
  target context, so `nominal=` has nothing to mean, and it is one of the shadowed names so it
  cannot be read as a tag either (the m48 grammar anchor covers the shadowed names but not this
  call shape).
  **Stacking**: when the target (or a named collection on it) already carries variations, the
  result inherits those labels and adds the new labels; a new label's member is the provided
  value's central universe (`graphed.nominal(v)` if the provided value is itself `Varied`, else
  the Array as given). **What "inherits" means differs per overload, and the corpus turns on
  it**:
  in the loose/shift forms (a)/(c) inherited members pass through **unchanged**; in the **weight
  form (b)** the newly registered factor is combined into the ambient weight **label-aligned per
  §2.4**, so an inherited label L's ambient member becomes `old_ambient[L] × factor[L]` — the
  factor evaluated in *that label's own universe* (its central universe only when L is new to
  the factor). **`factor[L]` means §2.4 applied TWICE when the factor NESTS**: a registered
  factor may itself be a `Varied` whose members are `Varied` (§2.1's member rule plus this
  plan's own mainline — `graphed.vary(sel, "btag", btag_sf(sjets), is_weight=True, up=…, down=…)`
  registers a container labelled `{nominal, btag_up, btag_down}` whose members are each `Varied`
  over the INHERITED jes labels, because `sjets` is `Varied`), and the one-level reading is
  silently wrong exactly where the corpus is: for `L = jes_up`, L is new to the *container*, so
  "its central universe" would give the b-tag SF on NOMINAL jets — omitting the SF from the
  `ttbar_4j1b_jes_up` reference. Binding: take the container's member for L (its
  `"nominal"` member when L is new to the container), then, if THAT member is itself `Varied`, take
  its own L (its `"nominal"` when L is new to the member). The composed ambient weight is therefore
  always FLAT — `{label: Array}` — which is what `graphed.weight(ctx)` (§9.1) returns. This is not a
  nicety: for `variation="jes_up"` the corpus computes the CENTRAL b-tag SF **on JES-shifted,
  JES-selected jets**
  (`graphed-corpus src/graphed_corpus/analyses/systematics.py` — `sel_jets = good[sel]`
  then `_btag_weight(sel_jets, variation=variation)`, which returns the central SF unless
  `variation` is `btag_up`/`btag_down`), so the `ttbar_4j1b_jes_up` reference IS b-tag
  weighted; a naive "inherited labels keep the old ambient" reading omits the SF entirely and
  misses the reference. Each label still differs from
  `"nominal"` in exactly **one** knob — the one-at-a-time rule is structural, and a weight
  variation layered on a shift-propagated weight (the corpus b-tag-on-JES case,
  `systematics.py`) is expressible without cross products.
  **The REVERSE order is bound too, as an ordering rule.** The shift
  form replaces collections and leaves the ambient registry untouched — this section's own
  "inherited members pass through unchanged" for overloads (a)/(c), and §2.6b's shift-form
  description, which registers nothing on the weight side — so a jet-dependent weight registered
  BEFORE a JES `vary` fills every
  shift universe with its PRE-shift value. It is structurally unfixable after the fact, since the
  registry's members are already-recorded expressions rooted at pre-shift nodes, which is why the
  exemplars handle it as a hand-partitioned "these weights can go outside the sys loop" judgement
  (Part I §2). Binding: **a shift `vary` does NOT re-derive the ambient weight registry; a weight
  factor that depends on a collection MUST be registered AFTER that collection is varied.** The rule
  is backed by a §2.5 diagnostic rather than left to convention (below), using machinery §3.4
  already scopes.
  All members MUST share one Session, have compatible forms (backend `op_form`-checked at
  construction), and root in the same partitioned-source set (checked at construction; the
  otherwise-deferred failure surface is `aggregate_plan`'s single-source check,
  `aggregate.py`). **Their CONTEXT HANDLES are unified here too** — `vary` is a combining
  point in §2.3e's sense and it is not an op, so the `record_op` merge chokepoint never sees it
  (the `_array_cls` sites are `source`/`record_op`/`record_exchange`/`record_join`/
  `record_external` in `Session`, and a container construction reaches none of them), while
  `graphed.context_of` answers with ONE handle — the CONTAINER's most-derived handle (§2.3e) — so a
  divergently-handled member would be silently dropped from introspection and surface
  only at the fill's unification: **all members' handles MUST lie on ONE ancestry chain, the
  container carries the most-derived one, and divergent handles are a construction-time error naming
  both contexts** — the same rule §2.3e binds at every other combining point.
  **The ROW-SPACE rule §2.1(b) binds for weight factors generalizes to EVERY overload.**
  One ancestry chain does NOT imply one row space — a §6.1d link kind (1) moves it and §2.6c puts a
  read through a derived context at that context's per-label row counts — so
  `graphed.vary(events.Jet, "jes", up=sel.Jet, down=sel.Jet_dn)` with `sel = events[mask]` passes
  every check above with its `"nominal"` member at root rows and its varied members at `|sel|` rows;
  `graphed.context_of` then answers with the CONTAINER's handle (`sel`, §2.3e), so
  `graphed.reindex_to` sees a value already carrying the target handle and re-indexes nothing, and
  the mismatch survives recording — `Session.record_op` validates only the backend's
  `op_form`, never lengths or row spaces. m48's `context_of` fixture pins the
  `vary`-IDENTITY-link spelling instead —
  for row-space stability and §6.4a(2a) proximity, NOT to keep a construction check open,
  since this clause decides the mask-derived case by RE-INDEXING it. Binding: **every member MUST
  live in ONE row space — the
  TARGET context's in overloads (b)/(c), the container's most-derived handle's in overload (a) — an
  ANCESTOR-handled member being re-indexed across the intervening links per §6.1d kinds (1)-(3)
  exactly as a §2.1(b) factor is** (**the two rules are ORDERED**: a `Varied` SUPPLIED as a
  member of (a)/(c) is reduced to its central universe AS SUPPLIED, and the resulting member is then
  re-indexed to the target handle **LABEL-ALIGNED per §2.4** — each label's member by that label's
  mask, nominal's by nominal's — the identical operation §2.6c already binds for the ambient
  registry. Reducing AFTER the re-index would land every member at nominal's row count while
  `graphed.context_of` answers a handle whose reads are per-label (§2.6c: a `Varied`-mask-derived
  context's ROW SET DIFFERS PER LABEL), and §6.1d(B)'s identity clause would then repair nothing.
  Read this section's row-space invariant per label accordingly: every member answers in the
  container handle's PER-LABEL row spaces), **and a member reached across a link
  no re-indexing can invert — a DESCENDANT handle, e.g. a selection-scoped record assigned to a
  collection on the ROOT context in overload (c) — is a construction-time error naming both contexts
  and the DIRECTION**, the §2.1(b) shape. m48's `vary`-construction divergence anchor carries the
  descendant case as one extra negative control. Lockstep multi-column variation within one
  collection (jet pt+mass
  shifted together) is expressed by varying a record Array — the corpus JES fixture already does
  this via `ak.with_field` (`systematics.py`); no second verb.
- **§2.2 (`Varied` is a mapping of universes; extraction is functional.)** `Varied` holds
  `{label: Array}` with `"nominal"` always present — **a member may itself be a `Varied`** when the
  container is a registered weight factor (§2.1, resolved two-level), while the AMBIENT
  weight `graphed.weight(ctx)` returns is always flat. **The container is PER IDIOM.**
  §2.3a's parity gate resolves every public name of `type(graphed.nominal(v))` ON THE CLASS, and
  §2.2/§10 pin the property fixture to the NUMPY idiom, so a single neutral `graphed.Varied`
  would have to define the numpy-only public names `NumpyArray` adds
  (`T`/`dtype`/`ndim`/`shape` and the method set) —
  which is numpy-idiom leakage into
  `graphed` proper (§2.1's factorization sentence, root `CLAUDE.md` §A.4) AND silently shadows
  field access for those names on an awkward-idiom container, re-creating the §2.6a
  namespace-collision hazard the functional respin exists to delete — while a neutral container
  carrying only `Array`'s names is RED against §2.3a's own gate on the mandated fixture. Binding:
  **`Varied` mirrors the existing `Session._array_cls` backend seam** — a neutral `graphed.Varied`
  base carrying `Array`'s surface, with `graphed.numpy` supplying the numpy-idiom subclass mirroring
  `NumpyArray` — and `graphed.vary(x, …)` returns the container class PAIRED WITH `type(x)` when `x`
  is an `Array`, and with `type(graphed.nominal(x))` when `x` is ALREADY a `Varied` (§2.1(a)'s
  target is `Array | Varied` and stacking on a loose container is public, for which `type(x)` IS the
  container class; the idiom comes from the members, never from the container), exactly
  as the session pairs its proxy class with the backend (`Session._array_cls` comes from the
  backend's `array_type` factory, falling back to `Array`). §2.3a's dynamic enumeration is
  then self-consistent: inventory and resolving class come from ONE idiom. **It additionally
  retains, PER `name`, the tags
  registered under that name** — internal state, not a second public shape: §1.1's family check
  is defined over "the set of tags carried by one `name` on one container, INCLUDING labels inherited
  through §2.1 stacking", and the label mapping alone cannot answer it (the only decomposition
  available from `{label: Array}` is prefix-matching `f"{name}_"`, which mis-attributes whenever one
  name plus an underscore prefixes another — `vary(v, "jes", up_2=…)` and `vary(v, "jes_up", …)`
  both yield `jes_up_2`; the duplicate-LABEL rejection catches that particular pair, but attribution
  is what the family check reads). `graphed.variations(ctx)` (§9.1, m50) is the per-name listing on a
  CONTEXT; on a loose `Varied` (§2.1a, which stays public) this retained map is the operand and stays
  internal. Universe extraction and introspection are
  **module functions** (the namespace-collision principle, §2.6a): `graphed.labels(x)`
  (ordered: nominal first, then insertion order; inherited labels before new ones under
  stacking), `graphed.nominal(x)`, and `graphed.universe(x, label)` (KeyError on an unknown
  label, listing the valid labels) — each accepting **the same input shapes, enumerated here because
  this is the definition site and two later sections extend it: a `Varied`, an event context
  (uniform introspection, §9.1), a `{label: hist}` RESULT MAPPING and a bare histogram-like object
  (duck-typed on `.axes`, never importing `boost_histogram` into `graphed`)** — the per-shape
  answers for the two result shapes being bound in §6.1a (a bare `hist` reads as the single label
  `"nominal"`) and §6.2(i-bis) (an axis-mode histogram reads its variation axis's bin set, re-ordered
  to this section's rule). **`graphed.nominal` on those two shapes is bound here** — the natural
  fallback, return the argument unchanged, is CORRECT for a bare unvaried histogram and confidently
  WRONG for an axis-mode one, handing back a histogram whose variation bins sum into the view the
  caller reads as the central value, the §2.5 class §6.2(i-bis) opens by naming: **`graphed.nominal(x)`
  ≡ `graphed.universe(x, "nominal")`** on both result shapes — identity for a bare unvaried histogram
  (which reads as the single label `"nominal"`), `x["nominal"]` for a `{label: hist}` mapping, and
  the nominal SLICE along the variation axis for an axis-mode histogram. **On a CONTEXT the answer is
  bound here, once**:
  `graphed.labels(ctx)` is the **§2.4-ordered union** of (a) the ambient weight registry's
  labels, (b) the labels of any `Varied` collections the context CARRIES — the collections a
  shift-form `vary` replaced, inherited ones included, **NOT the implicitly-varied reads §2.6c
  produces through a `Varied`-mask-derived context** (scoped: under the wide reading every read
  through such a context is `Varied`, so (b) would subsume (c) everywhere and (c) would be dead
  text — the term-(c) discrimination m48 anchors depends on this scoping) — and (c) the labels of
  **`graphed.selection(ctx)` in §9.1's sense — the selection reached by skipping over any number of
  `vary` IDENTITY links and answering as of the first non-identity link, `None` for a root context;
  on a universe/nominal-derived context that answer is a single label's unvaried member and
  contributes NO labels**. "The mask that derived it" would have no value at all
  for the two lineage link kinds that carry no mask: §6.1d binds THREE kinds and §2.6's own sketch
  rebinds `sel` by a `vary` call, so the object whose labels a user or an m48 anchor asks for is
  routinely `vary`-derived. In the mainline, term (a) happens to rescue the answer — a factor
  registered into a mask-derived context is itself `Varied` and re-carries the mask's labels — but
  that is a property of the program, not a rule, and a uniform introspection verb answering less
  than the sink produces is the §2.5 confidently-wrong class. The
  definitional reference does not move `graphed.selection`'s own milestone: §9.1 keeps it at m51,
  and its per-link-kind ANSWER is bound there independently of when the verb is exported. **Term (c)
  itself gains an m48 program that isolates it** — a context derived by a LOOSE-`vary`-varied
  mask, where (a) and (b) are both empty — **while the `vary`-link-walking HALF is knowingly left
  UNANCHORED**: on a `Varied`-mask-derived context every read through the context is `Varied`
  (§2.6c), so a weight registered onto a `vary`-derived child lands the mask's labels in term (a) and
  a shift-form `vary` stacks them into term (b), leaving no m48–m51-scoped program in which the two
  readings differ. It stays binding for the verb's correctness, on §1.1's `"1e1000000000"`
  precedent. The union is by
  construction the SUPERSET of the
  CONTEXT-BORNE half of any §6.1d fill's label set from that context, `"nominal"` first. **The
  superset property is scoped to context-borne sources, and that scoping is binding** — stated
  unscoped it is a false invariant a test-author could freeze: §6.1d's fill label set also unions
  labels carried by *loose* values and by explicit `weight=[…]` factors, and the loose
  `graphed.vary` on `Array`s stays public (§2.1a, §2.6 close), so both
  `h.fill(sel.Jet.pt, weight=[loose_varied])` and `h.fill(graphed.vary(sel.Jet, "jer", …).pt)` are
  expressible programs whose fill label set exceeds `graphed.labels(ctx)`.
  `graphed.universe(ctx, label)` and `graphed.nominal(ctx)` return **a CONTEXT** — a CHILD of the
  argument in the §2.6b lineage chain (bound because §6.1d's unification is defined over
  lineage and would otherwise have no way to relate the result to its argument: `h.fill(
  graphed.nominal(sel).MET.pt, sel.MET.pt)` would either unify by an unstated rule or raise the
  divergence error on a legitimate program) — carrying that label's collections and ambient weight
  (falling back to each container's `"nominal"` member per §2.4), with `graphed.selection(...)`
  equal to the argument's selection at that label. The m48 anchor asserts the ancestry relation.
  String subscription `v["pt"]` is **field access** (broadcast per §2.3a,
  Array-coherent), NEVER label lookup — `[label]` indexing is removed: it collided with awkward's
  string-getitem field access. **`x[L]` in this document's PROSE — §2.1's
  `old_ambient[L] × factor[L]`, §2.4's fold notation, m48's stacking anchor — denotes
  `graphed.universe(x, L)` and is NEVER a literal subscript**: transcribed literally into a
  frozen test it records a `field` op named `"jes_up"`, the very hazard the removal above closes.
  **Its sibling rule: `==` between two RECORDED expressions in this document's prose denotes
  STRUCTURAL IDENTITY (`.node_id` equality, sound by interning), never a Python `assert` on the
  recorded comparison** — `Array.__eq__` returns an `Array` and `Array`
  defines no `__bool__`, so `bool(a == b)` is unconditionally `True` and such an assertion is vacuous
  for every operand pair. A frozen test transcribes it as `.node_id` equality or materializes both
  sides and compares elementwise. `Varied.apply(fn)` remains a method — apply a
  record-time `Array -> Array` function per universe (attribute shadowing follows the awkward
  precedent: real methods win; a field named `apply` stays reachable via string getitem). (Named
  `apply`, NOT `map`: `Array.map` is an execution-time data callable; the two
  contracts must not share a name. **The stated criterion cuts against `apply` too, and the
  collision is accepted knowingly rather than by oversight**: `graphed.apply` is already a
  public module verb with the same execution-time contract as `Array.map` and interns with it,
  exported in `graphed.__all__`. It is accepted because the two names live on
  different objects with no dispatch path between them — `Varied.apply` is a bound method on the
  container, `graphed.apply` a module function over `Array`s — whereas the rejected `Varied.map`
  would have shadowed `Array.map` on the very surface §2.3a mirrors. If the m48 test-author judges
  the collision confusing, the rename is `Varied.per_label`; the spelling is pinned at m48 freeze
  like every other new surface here.) `fn` MUST return an `Array`; if it returns a `Varied` (because
  it closed over another container), `.apply` raises with guidance to combine containers via
  ordinary ops instead. **`Varied` gives EVERY public PROPERTY of the nominal member's class a
  disposition** — the rule is a
  discovery rule over properties, not a two-name list: §2.3a deliberately EXCLUDES properties from
  its parity gate, so the numpy idiom's `shape`/`dtype`/`ndim`/`T` (all plain
  properties invisible to `inspect.isfunction`) would otherwise have neither a reserved-name rule
  nor a gate entry and
  would resolve through the label-mapping field access, recording a graph node named `"dtype"`. It is
  a live path: §6.1d binds the numpy `broadcast_like` seam as a NO-OP precisely so an all-numpy
  varied fill works. **The disposition splits by MECHANISM, not by `isinstance(m, property)`** —
  `NumpyArray.T` is a property alias for the recorded `transpose` op
  (`@property def T: return self.transpose()`, and `transpose` records via `Session.record_op`),
  so accessing `T` RECORDS, while `dtype`/`ndim`/`shape` are `_form_meta`-backed and record nothing
  (`Array._form_meta` itself falls back to
  recording a `field` op when the form lacks the name). A rule answering every property
  eagerly on the nominal member would silently drop every other
  universe of `varied.T` — verbatim the §2.5 confidently-wrong class — while §2.3a
  classifies the `transpose` METHOD *broadcast*. Binding: for every non-underscore property on
  `type(graphed.nominal(v))`, exactly one of three classes applies —
  **(1) `node_id` and `session` raise `AttributeError`** rather than resolving as field access;
  **(2) a FORM-ANSWERED property — one whose access on a plain nominal `Array` records NO node
  (today: `shape`/`dtype`/`ndim`, all `_form_meta`-backed) — is answered EAGERLY on the nominal
  member** (sound by
  §2.1's form compatibility, the same argument §2.3c uses for `gak.fields`/`type_of`);
  **(3) a RECORDING property — one whose access on a plain nominal `Array` records a node (`T`
  today) — takes its underlying METHOD's §2.3a disposition** (`T` → *broadcast*: it returns a
  `Varied` whose `graphed.labels` match the input's). The discriminator between (2) and (3) is
  behavioural and measurable pre-implementation — access the property on a plain nominal `Array`
  and read the `Session.node_count()` delta — so the gate below classifies each discovered name by
  measurement rather than by a literal list. The `node_id`/`session` half
  is binding because `Array` exposes both as plain properties, not dunders, while
  `Array.__getattr__` guards only leading underscores — so a `Varied` that
  implements field access by mapping over labels would answer `varied.node_id` with a recorded
  `field` op named `"node_id"`, and `compile_ir(session, varied)` (which reads
  `arr.node_id` per output) would silently compile that nonsense instead of
  raising, the §2.5 confidently-wrong class. **Both this rule and §2.3d's dispositions are
  frozen-anchored in m48** — the §2.3a parity gate cannot reach them, since `node_id`/`session` are
  plain properties that `inspect.isfunction` does not enumerate. `Varied` is a plain frontend
  object — no IR type, no new NodeKey (§3.1).
- **§2.3 (Broadcast propagation — five bound dispatch points.)**
  (a) **`Varied` implements the full `Array` PUBLIC surface — dunders AND methods** — by mapping
  over labels. Dunders: enumerated
  at implementation from `array.py` and including `__array_ufunc__`, the bitwise
  set (`__and__`/`__or__`/`__invert__`), `__getitem__`, field access, and all
  reflected variants. **Public methods are in scope too**: `Array`
  carries `filter`, `map`, `reduce`, `repartition`, and the numpy idiom
  adds its method set on top of a tuple-accepting `__getitem__` override
  (`sum`/`prod`/`mean`/`std`/`var`/`min`/
  `max`/`any`/`all`/`argmin`/`argmax`/`cumsum`/`cumprod`/`reshape`/`ravel`/`squeeze`/`transpose`/
  `swapaxes`/`astype`/`clip`/`round`/`take`…), none of which a dunder-only enumeration reaches —
  and an unimplemented one does not raise cleanly: `Varied`'s label-mapping field access turns
  `varied.filter` into a recorded `field` op (§2.2's reserved-name rule covers only the `Array`
  protocol properties). Each method carries the same per-class disposition as (c): *broadcast*
  for the elementwise/structural ones, *refusing* for `repartition` (§5.4).
  Parity is gated by a frozen test iterating the inventory
  **enumerated dynamically from `type(graphed.nominal(v))` at test time** (so idiom subclasses are
  covered), not from a literal list. **The enumeration FILTER is stated here**, because the
  reserved-name reasoning presupposes it ("the §2.3a parity gate cannot reach
  `node_id`/`session`, since they are plain properties that `inspect.isfunction` does not
  enumerate") — an UNFILTERED enumeration under the per-name rule below would demand
  `Varied.node_id`/`.session` exist, which §2.2's reserved-name anchor in the same milestone demands
  raise `AttributeError`, and would demand dispositions for numpy-idiom properties §2.3a never
  assigns: the method half is
  `inspect.getmembers(type(graphed.nominal(v)), inspect.isfunction)` with no leading underscore,
  plus the dunder set — the same spelling §2.3c and §2.3d already bind (same
  self-repairing rule, and the same **non-vacuity floor**, as (c) — which for this gate MUST name
  at least one METHOD alongside the named dunders).
  **The PROPERTY half is enumerated too, under §2.2's disposition rule** (excluding
  properties outright is what would leave `shape`/`dtype`/`ndim`/`T` with no disposition anywhere): a
  third enumeration over `inspect.getmembers(type(graphed.nominal(v)),
  lambda m: isinstance(m, property))` with no leading underscore, asserting each discovered name
  resolves per §2.2's THREE-class rule (a blanket "records NO node" is red against a
  correct implementation for `T`, which is a plain alias for the recorded `transpose` op;
  the discovered property set on `NumpyArray` is
  `['T','dtype','ndim','node_id','session','shape']`): `node_id`/`session` raise `AttributeError`;
  a property the same test measures to record NO node on the plain nominal `Array` must answer
  eagerly on the nominal member with a `Session.node_count()` delta of 0 across the `Varied`
  access; a property that DOES record on the plain nominal `Array` must broadcast — returning a
  `Varied` whose `graphed.labels` match the input's. The gate's floor names **both** representatives:
  `varied.dtype` (eager, delta 0) and `varied.T` (broadcast, returns a `Varied`).
  **What the gate ASSERTS per name is bound too, because a presence check is vacuous here**: a
  `hasattr`/`getattr`-on-the-instance
  iteration is green against exactly the failure this paragraph names — `Varied` implements field
  access by mapping over labels, mirroring `Array.__getattr__`, which returns a recorded `field` op
  for ANY non-underscore name — so `hasattr(varied, "filter")`
  is True on a `Varied` that broadcasts ZERO methods, and for the refusing disposition
  `varied.repartition` resolves to a container and calling it raises `TypeError: not callable`,
  which a loose `pytest.raises` refusal check accepts. Binding: **(1)** each discovered name is
  resolved ON THE CLASS — `getattr(type(varied), name, None)`, which the instance `__getattr__`
  never intercepts — and MUST be a real attribute; **(2)** the same test carries at least one
  BEHAVIOURAL probe per disposition class: a broadcast method returns a `Varied` whose
  `graphed.labels` match the input's, and `repartition` raises the §5.4 refusal, not
  `TypeError: not callable`. §2.3e's `Array`-surface propagation gate ((e)(4)) inherits the identical
  class-lookup rule.
  (b) **Plain-`Array` entry points learn `Varied`**: today `Array.__getitem__` accepts only an
  `Array` mask, a `str` field, a `list[str]` field subset, a `slice`, or an `int`, and raises
  `TypeError` on anything else — including a `Varied`; `Array.filter` has NO
  runtime check at all, so a `Varied` falls through into `record_op` and
  surfaces as an `AttributeError` on `a.node_id`. There is no reflected
  protocol for subscription, so both gain an explicit `Varied`-mask branch delegating to the
  container (the corpus
  requires it: unvaried `photons`/`muons` sliced by a JES-varied selection, `systematics.py`).
  (c) **The gak layer gets one dispatch mechanism plus a bound per-function classification** —
  "one wrapper, zero per-function thought" is falsified by the measured surface, so the
  classification is explicit, lives in code, and is gated by a frozen exhaustiveness test that
  **enumerates gak's public surface DYNAMICALLY at test time** (not a
  hand-written literal name tuple — the `m24/test_interface_parity.py` anti-drift pin is a
  literal name tuple, which would let a future gak function go silently unclassified,
  exactly the failure this requirement names; a dynamic check is also self-repairing, since a new
  function is fixed in `src`, never by editing a frozen test).
  **The discovery rule is bound, because the obvious one does not exist**: `graphed.awkward.
  functions` defines **no `__all__`**, and the package `__all__` lists modules, classes and
  package-level
  functions — none of them gak's (the functions among them are
  `from_awkward`/`from_parquet`/`project`/`project_buffers`/
  `read_parquet_partition`/`to_parquet`) — so an `__all__`-driven test over `graphed.awkward`
  discovers a **WRONG set** — non-empty, so a bare non-emptiness floor would not catch it;
  a bare `dir()` over-fires on imported symbols and on the module's
  private helpers (`_comb_params`, `_reduce`).
  Binding discovery: `inspect.getmembers(graphed.awkward.functions, inspect.isfunction)` filtered
  to `__module__ == "graphed.awkward.functions"` and no leading underscore. **The MODULE is named,
  not the `gak` alias** — the alias `graphed.awkward` used as the target discovers
  NO functions, because the package re-exports modules/classes only and gak's functions are not
  package-level attributes (`graphed.awkward.num` → `AttributeError`), while
  `graphed.awkward.functions` discovers the full set; the non-vacuity floor below would catch the
  empty
  reading at freeze, but naming the module spares the discovery. **Binding non-vacuity floor,
  asserted
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
  Array-consuming surface.** A partial list is not harmless: `Varied`'s field-access `getattr`
  (§2.2) turns an unhandled duck-typed read into a
  recorded op rather than an error, so an undisposed verb silently compiles nonsense. Dispositions:
  `graphed.join` and
  `graphed.repartition` **refuse** with the §5.4 error; **`graphed.pack_key`, `graphed.shuffle_plan`
  and `graphed.join_plan` refuse likewise** — all three are exported in `__all__` and take an
  `Array` first, each reading `array.session` (`shuffle.py`). `pack_key` is a fusible `Op` rather
  than a
  boundary, but it exists to pre-key a source for a shuffle/join, and both plan builders ARE the
  §5.4 boundary path, so one refusal message covers all three. `graphed.apply` and
  `graphed.read_columns`
  **expand into universes** (per-label results — `apply` returns a `Varied`, `read_columns` returns
  the union over all labels' members, §5.3; **the union is `None` — "read every column" — if ANY
  member's read set is `None`, else the sorted set union**: `read_columns`
  returns
  `tuple[str, ...] | None` and `None` is the conservative answer,
  so a plain set union would silently NARROW a conservative label's read list and starve its task);
  `graphed.compile_ir` and
  `graphed.aggregate_plan` **refuse** a `Varied` output with an error naming `graphed.universe` —
  they consume `arr.node_id`/`arr.session` directly, and
  §2.2's reserved-name rule makes the refusal a clean `AttributeError` seam rather than a compiled
  field op; the varied route to a plan is the §6.1c group API. **`graphed.evaluate_ir` is OUTSIDE
  the `Array`-consuming surface entirely and carries NO `Varied` disposition** — its signature is
  `evaluate_ir(compiled: CompiledGraph | bytes, backend, sources, *, externals=None)`:
  it never receives an `Array`, never reads
  `arr.node_id`/`arr.session`, and a "plain `Array` still works" positive control is false for it in
  the other direction too, since a plain `Array` is not a `CompiledGraph`. `graphed.broadcast_like`
  (the §6.1d seam, NEW in m48) **broadcasts**: with a `Varied` value and/or factor it returns a
  `Varied` whose labels are the §2.4 union, per label broadcasting that label's members.
  **`graphed.reindex_to` (the §6.1d lineage seam, NEW in m48) BROADCASTS** — the result's
  labels are computed by **COMPOSING THE LINKS IN LINEAGE ORDER, parent-to-child** (an
  order-insensitive set expression contradicts §6.1d's own "links compose in lineage order" whenever
  a
  mask-derivation link sits BELOW a projection link or two masks share a label name): **a
  mask-derivation link UNIONS that mask's labels per §2.4, a `graphed.vary` link is the IDENTITY,
  and a universe/nominal PROJECTION link RESETS the accumulated label set to empty** —
  each member re-indexed by that label's own mask, so an UNVARIED value re-indexed across a
  `Varied`-mask link BECOMES a `Varied` carrying that mask's labels **while a value reached across a
  link kind (3) is that label's unvaried member and carries NO labels** — an unqualified "the
  §2.4 union" is false across a projection link, which §6.1d(B) admits by definition ("composing
  link kinds (1)-(3)") and whose own clause yields "an unvaried value in the ancestor's row space";
  it is also what §6.1d's ordering rule and m48's `h.fill(graphed.nominal(sel).MET.pt,
  sel.MET.pt)` BARE-`hist` anchor depend on, and m48's lineage-seam anchor is split PER LINK KIND so
  a narrower reading cannot be frozen alongside it (a "SAME labels" reading
  contradicts §6.1d(B)'s "label-aligned per §2.4" and is false of m48's own link-kind-(1) anchor,
  whose value `events.MET.pt` is a plain `Array` re-indexed into `sel`'s per-label row spaces; the
  narrow reading silently drops the mask's labels, the §2.5 confidently-wrong class, and the plan's
  own precedent is the other way — `broadcast_like` is classified *broadcasting* with §2.4-UNION
  labels) —
  and **`graphed.unify_contexts` carries NO disposition**, taking context handles rather than
  `Array`s (the `evaluate_ir` treatment); both are disposed here so the m48 gate does not
  discover `reindex_to` unclassified.
  `graphed.awkward.to_parquet` and `graphed_histogram.Histogram.fill` **accept** — a fifth
  disposition class, bound below: `to_parquet` takes a `Varied` RECORD and/or a `Varied` `select=`
  per §6.4a (§6.4's canonical skim is `to_parquet(events.Jet, select=…)` where `events.Jet` is
  itself a `Varied` after a shift-form `vary`, §2.6b, so the record arm is the headline case and the
  keyword arm alone under-covers it), `fill` takes `Varied`
  values/weights/`sample` per §6. **`to_parquet` carries NO disposition until m51 and is NOT in
  m48's table at all**: there is nothing to refuse at m48 —
  today's `to_parquet(array, destination, *, steps_per_file, compute, executor, prefix, column,
  behavior)`
  has NO `select=` parameter, so a varied `select=`
  is an unexpected keyword until §6.4 lands; and `to_parquet` is not discovered dynamically — it is
  outside `graphed.__all__` entirely — so dropping it from the m48 floor list removes it
  from m48's union at no cost in class coverage (*broadcasting* and *eager-metadata* are supplied by
  the
  named `graphed.broadcast_like`/`graphed.context_of`): at **m51** it enters the table *accepting*,
  and m51's anchors assert the accepting behaviour. `Histogram.fill` is *accepting* from m48 and is
  the class's behaviourally real representative.
  **The disposition CLASS SET is enumerated exhaustively here** (the m48 gate is table-driven
  and its floor requires "one member of each class", which is unwritable without the vocabulary):
  the legal §2.3d dispositions are **refusing / expanding /
  broadcasting / eager-metadata / accepting**, where *accepting* means the verb consumes a `Varied`
  operand and handles it internally without returning per-label results to the caller.
  **Exhaustiveness is kept by a DISCOVERY RULE, not by this literal list** (the self-repairing rule
  §2.3a/c already adopt), **and the rule is bound over the MEASURED signature surface, not over
  first parameters** — a "first positional parameter annotated `Array`" filter
  discovers only `repartition`/`pack_key`/`join`/`shuffle_plan`/`join_plan` and provably
  MISSES the verbs disposed above whose `Array` operand is not first: `compile_ir(session: Session,
  *outputs: Any)`,
  `evaluate_ir(compiled: CompiledGraph | bytes, …)`,
  `read_columns(arrays: Sequence[Array], source_nid: int)` and
  `apply(fn: Callable[..., object], *arrays: Array)` — i.e. exactly the safety-
  bearing dispositions; `aggregate_plan(*outputs: Array)` is var-positional, so
  whether a first-parameter filter reaches it depends on how that filter treats `*args`. "The table
  cannot silently miss a verb" is therefore NOT achievable by any first-parameter filter over this
  surface. Binding: the m48 anchor
  enumerates `graphed.__all__` dynamically, filtered to `inspect.isfunction` members **any of whose
  parameter annotations MENTIONS `Array`** (including `Sequence[Array]`, unions and `*args: Array`),
  **UNION an explicitly NAMED freeze-time floor list**, and asserts every member of that union
  carries a disposition. **The named list is not restricted to non-`graphed.__all__` members** —
  restricted that way it reaches neither channel for `compile_ir`:
  the annotation-wide filter over `graphed.__all__` discovers
  exactly `aggregate_plan`, `apply`, `join`, `join_plan`, `pack_key`, `read_columns`, `repartition`,
  `shuffle_plan` — `compile_ir` is absent, because its parameters are annotated `Session` and `Any`,
  while it IS in `graphed.__all__` — so it would
  fall through BOTH channels while §2.3d bindingly disposes it and m48 freezes that disposition.
  The named list is: **`graphed.compile_ir`**, **`graphed.context_of`**, **`graphed.broadcast_like`**,
  `graphed_histogram.Histogram.fill`, and — **from m51 only** —
  `graphed.awkward.to_parquet`. **`context_of` and `broadcast_like` are named because they are
  the SOLE representatives of two classes** — every verb the annotation-wide filter discovers is
  classified *refusing* or *expanding*;
  *broadcasting* is supplied only by `graphed.broadcast_like` and *eager-metadata* only
  by `graphed.context_of`, both NEW in m48 — so whether the frozen per-class floor can find them
  would otherwise depend entirely on the implementer's post-freeze parameter annotations, and
  `broadcast_like` is described as a NEUTRAL seam taking an arbitrary factor, for which `value: Any`
  is a plausible annotation. Naming them costs nothing. **The floor is asserted PER REPO**:
  `graphed`'s
  m48 gate takes `{graphed.compile_ir, graphed.context_of, graphed.broadcast_like}` (`to_parquet`
  joins it at m51) — `graphed-histogram` is in no extra of `graphed` at all (CI installs
  `.[dev]`) and the house pattern for reaching it is a module-level
  `pytest.importorskip` (`tests/frozen/preserve/m25/test_histogram_preservation.py` and siblings),
  which would SKIP the whole test and silently discharge both this
  gate and §2.2's reserved-name anchor with zero frozen-suite diff coverage — while
  `graphed_histogram.Histogram.fill`'s disposition is asserted in `graphed-histogram`'s flat
  `tests/frozen/m48`, which depends on `graphed` and already hosts every other fill-shaped m48
  anchor (§10).
  **`graphed.numpy`'s public module verbs are in scope too, and the gate runs PER IDIOM PACKAGE.**
  The numpy idiom is a first-class `Varied` carrier (§2.2's per-idiom container),
  §10 pins the property-classification fixture to a numpy source, §6.1d binds the numpy
  `broadcast_like` NO-OP "precisely so an all-numpy varied fill works", and §6.4f disposes the numpy
  write function at m51 — a discovery scoped to `graphed.__all__` alone would leave a numpy-idiom
  user handing a `Varied` to the twin of
  §4.1's BINDING `gak.full_like` constant-weight form with NO bound behaviour (loud only by
  accident, through §2.2's reserved-name `AttributeError` on `varied.session`, whose message points
  at the wrong thing). The same annotation-wide filter over
  `graphed.numpy.__all__` discovers exactly six functions —
  `apply_gufunc`, `empty_like`, `full_like`, `ones_like`, `project`, `zeros_like` — each reaching
  `array.session`/`arrays[0].session`. Binding: they carry dispositions by the same rules as their
  idiom twins — the four `*_like` creation verbs and `apply_gufunc` **broadcast** (per-label
  recording, §2.3c's elementwise rule; `gnp.full_like` is the numpy twin of §4.1's `gak.full_like`)
  and `project` **expands — per-label results, `{label: Projection}`, and NOT `read_columns`' union
  treatment**: `Projection` is a frozen dataclass whose one field is
  `read_columns: Mapping[str, frozenset[str]]` with no
  conservative `None` sentinel anywhere — conservative projection is expressed as the FULL column
  set — so §5.3's
  `None`-dominant union rule has no operand here.
  **The AWKWARD idiom package is in scope on the identical footing** — the same rationale (an
  idiom-package verb handed a `Varied` reaches NO bound behaviour, loud only by accident through
  §2.2's reserved-name `AttributeError`) holds verbatim for the default idiom of every fill anchor
  here, while §2.3c's gate is scoped to the MODULE `graphed.awkward.functions` and reaches no
  package-level verb: the same annotation-wide filter over
  `graphed.awkward.__all__` discovers exactly **`project`** and **`project_buffers`**
  (`project(array: Array, *, on_fail="raise") -> Projection` /
  `project_buffers(...) -> BufferProjection`, both
  routing through `_replay`, whose first statement reads `array.session`), the
  other package functions taking a `Session`/`Partition` rather than an `Array`
  (`from_awkward`/`from_parquet`/`read_parquet_partition`) or being disposed at m51 (`to_parquet`).
  Binding: both **expand**, per-label results — **each returning its OWN return type per label:
  `project` to `{label: Projection}` and `project_buffers` to `{label: BufferProjection}`**
  (`BufferProjection`
  is a distinct frozen dataclass whose field is `read_buffers`, not `Projection`'s
  `read_columns`; the numpy twin above is `project` only).
  m48's gate runs the identical dynamic enumeration over `graphed.numpy.__all__` AND
  `graphed.awkward.__all__`, in the same repo and the same anchor. **The FLOOR is asserted over the
  UNION of the enumerations, never per enumeration** (neither idiom package hosts any
  member of the named floor list — `graphed.compile_ir`/`context_of`/`broadcast_like` are all
  `graphed`-level — and the numpy verbs are only *broadcast* and *expanding*, so a per-enumeration
  floor is unsatisfiable against a correct implementation on both of its clauses), and it stays a
  containment floor, never an exact set.
  **Two exclusions are bound too**: `inspect.isfunction` keeps classes such as `graphed.Varied`
  out of the enumeration, and **`graphed.vary` itself is excluded BY NAME** — it is the verb that
  PRODUCES containers, not one that consumes them, and its own annotations mention `Array`, so once
  m48 lands it would otherwise be discovered with no disposition class to carry. It
  carries §2.3a/c's **non-vacuity floor in the same test**: the discovered set is non-empty, is at
  least the freeze-time count, contains every member of the named floor list, and contains at least
  one member of **each class in the bound class set above that the repo's own table can host**
  (refusing / expanding / broadcasting / eager-metadata / accepting; **the per-class floor is
  scoped to the hostable classes**: at m48 `graphed`'s table has no *accepting* member, since
  `to_parquet` is out of the table until m51 and `Histogram.fill` lives in the other repo, so
  `graphed`'s m48 floor requires **at least one** member of each of {refusing, expanding,
  broadcasting, eager-metadata} — a containment floor, never an exact set, so m51's added
  *accepting* member cannot red it;
  the *accepting* class's m48 representative is `Histogram.fill` in `graphed-histogram`'s flat
  `tests/frozen/m48`, and m51 adds the *accepting* assertion for `to_parquet`). This list is the
  freeze-time floor, not the definition; a
  verb whose signature mentions no `Array` and which is not named above (`evaluate_ir`) is out of
  scope by construction.
  **The m49 verbs this plan itself adds enter the table *expanding* when they land** — §3.4's
  impact helper and §5.3's per-label projection-stats verb (§9.1) both answer PER LABEL. Their
  operand `Sequence[Varied] | Mapping[str, Sequence[Array]]` MENTIONS `Array`, so the
  annotation-wide filter DOES discover them one milestone after the m48 freeze, under the §2.3d
  filter's own "unions" clause above. Nothing reds either way,
  since the gate's self-repair rule puts each new function's
  classification in `src` (never in a frozen test) and every floor is a containment floor. m49's
  own anchors assert their per-verb shapes (§5.3's `{label: …}` mapping; §3.4's impact sets).
  (e) **Context-tag propagation** (the §6.1d substrate). Every `Array`/`Varied` produced from a
  contexted input carries a
  **context handle: a Python attribute on the frontend wrapper object, explicitly NOT part of
  node identity** — it never reaches `NodeKey` params/tokens/hashes (§1.2 and interning stay
  intact). **This is an Implementation Target, not free**: `Array` is `__slots__`-ed with no
  `__dict__` (`__slots__ = ("_node_id", "_session")`) and
  `NumpyArray` keeps it closed (`__slots__ = ()`), so an
  ad-hoc attribute raises `AttributeError` today. Binding: **one added slot, underscore-prefixed**
  (e.g. `_context`), so `Array.__getattr__`'s `startswith("_")` guard keeps it out of field
  access, **plus a read-only PUBLIC seam exposing it —
  `graphed.context_of(array)`-shaped, spelling pinned at m48 freeze, returning the handle or
  `None`** — the slot alone is not reachable across a package boundary: §6.1d requires
  `Histogram.fill` to read its inputs' handle, `fill` lives in `graphed-histogram`, and §9.1's
  surface is entirely context-TAKING (`labels`/`universe`/`nominal`/`weight`/`variations`/
  `selection`) with no `Array` → context read — so m48's fill-shaped anchors, all assigned to
  `graphed-histogram` (§10), would otherwise be implementable only by reaching into another
  package's private
  slot, and the "spelling pinned at freeze" discipline would have nothing to pin. It carries a §2.3d
  disposition — *eager-metadata* — so the m48
  exhaustiveness gate discovers it, the intended anti-drift property; listed in §9.1.
  **On a `Varied` it answers with the CONTAINER's handle — the most-derived member handle §2.1 binds
  — NOT with the nominal member's.** "Answering on the nominal member" is the class LABEL's usual
  shape but is unsound for this one property: the
  eager-metadata argument works for `gak.fields`/`type_of` because §2.1's form compatibility makes
  every member agree, while §2.1's construction checks are form compatibility + Session + source and
  never row space, so `context_of` is the one per-member property the plan does NOT require to
  agree — §2.1 explicitly ACCEPTS members whose handles differ along one ancestry chain and refuses
  only divergent ones, so the most-derived handle may well belong to a non-nominal member. It is
  load-bearing: §6.4a(2a)'s predicate is `graphed.context_of(select_mask) is
  graphed.context_of(record)` and both operands are routinely `Varied`, and its m51 controls
  are verified against the CONTAINER reading. *Eager-metadata* here means only that the answer is
  produced without recording. m48's §2.3d table anchor carries the discriminator: a container built
  from an ancestor-handled nominal member and a more-derived non-nominal member answers with the
  MORE-DERIVED handle.
  A wrapper attribute is the only sound carrier:
  two sibling contexts derived
  from one root that differ only in registered weights expose collections whose reads record
  identical `NodeKey`s and therefore the SAME node id (interning), so a node-id-keyed
  context map provably cannot distinguish them; and `Provenance` is a frozen
  `(filename, lineno, function, source)` dataclass with no lineage channel,
  so provenance cannot carry it either. **Propagation is a
  chokepoint, not per-function work**: every frontend `Array` is constructed in `Session` at
  the `_array_cls` sites —
  `source`, `record_op`, `record_exchange`,
  `record_join`, `record_external` — all of which end
  `return self._array_cls(self, node_id)` and
  are the only `_array_cls` call sites in the repo (omitting `source` drops the handle at
  every tree read, omitting `record_join` drops it across a join).
  Those methods already receive
  the input `Array`s, so the merge rule is implemented ONCE there; gak functions and module verbs
  inherit it by construction, and the propagation gate below is the anti-drift gate
  over the ones that bypass `record_op` (e.g. tuple-returning wrappers that rebuild results).
  **ORIGINATION rule — a context STAMPS its own handle, overriding the merge result** (the merge
  rule alone gets the mainline sketch wrong): `Session.source` takes no
  `Array` and no context
  (`source(self, name, *, form, data, **params)`) and `record_op` merges only from its `inputs`
  (a fresh wrapper per call), so nothing in the merge rule can give a *derived* context's
  reads that context's handle: on this section's own sketch (`events2 = graphed.vary(events, "pu",
  …, is_weight=True)`), `events2.Jet` is a `field` op whose input is the SAME root record `Array`
  carrying `events`' handle, so a pure input-merge hands the read `events` — and §6.1d then
  auto-applies the PRE-`vary` ambient registry, silently dropping the pileup universes (the §2.5
  confidently-wrong class). Binding: **every `Array`/`Varied` a context produces — its own root
  wrapper and every read performed through it — carries THAT context's handle**, overriding whatever
  the input merge would yield; the merge rule below governs only ops whose inputs already carry
  handles. Frozen-anchored in m48.
  **Merge rule at the op, not at the fill**: inputs whose
  handles lie on ONE ancestry chain propagate the most-derived handle; handles on divergent
  branches are an error at that op naming both. **The op is not the only raiser** — every
  *combining point* runs the same unification, and the fill is one of them (§6.1d): a fill takes
  several independent inputs no op ever combined (`h.fill(a_from_ctx1, b_from_ctx2,
  weight=[w_from_ctx3])`), and `Histogram.fill` is the first place those handles meet — it
  collects args/weights/sample into ONE `inputs` list and records ONE External node
  (`graphed-histogram src/graphed_histogram/boost.py`). The op-level rule is *early*
  detection, not the sole raiser. **Drop rule**: an op that cannot propagate a handle (no contexted
  input) yields a
  context-free result, and a subsequent fill mixing context-free with contexted inputs adopts the
  unified context (§6.1d) — an op that silently *loses* a handle it had is the §2.5 failure mode
  and is a bug. **The propagation gate is a SEPARATE test from (c)'s classification gate, and it is
  scoped, because a behavioural gate over the whole surface is not buildable.** (c)'s gate is
  *metadata-only* — it
  reads a classification off each discovered function and never calls it — so it runs over the full
  public gak surface for free. A propagation gate must CALL each function with a contexted
  `Array`, and
  the measured surface makes a blanket call impossible: `apply_correction` and `onnx_inference`
  take a payload + evaluator/runner first, not an `Array`; `to_list`,
  `head` and `sample` are eager and return Python objects; `fields`, `type_of`,
  `backend_of` return `list[str]`/`str`, for which "preserves the handle" is
  undefined; `join` must refuse; and `zip`/`concatenate`/`where`/`unflatten`/`linear_fit`
  need typed or extra operands. The m24 precedent gate compares
  signatures and never calls (`tests/frozen/awkward/m24/test_interface_parity.py`). Binding:
  **(1)** the classification gate of (c) covers the full public gak surface, metadata only; **(2)**
  the propagation gate
  dynamically enumerates only the *broadcast*, *container-traversing* and *tuple-returning*
  classes, and derives its **AUXILIARY** call arguments from **argument fixtures that live in `src`
  beside the classification** — so a newly added function arrives with its classification AND its
  fixture and the frozen test stays untouched (the self-repairing property is preserved).
  **The CONTEXTED operand is owned by the FROZEN TEST, not by the fixture, and the assertion is
  positive**: if a fixture supplies a context-free primary `Array`, both the input and the output
  handle
  are `None` and "the handle is preserved" degrades to `None == None`, passing while witnessing
  nothing, for every function whose fixture the implementer wrote. Binding: the frozen test
  constructs the
  context and substitutes its own contexted `Array` into the primary operand position; `src`
  fixtures supply only the auxiliary/typed operands the measured surface needs
  (`concatenate`'s second array, `unflatten`'s counts, `where`'s branches, `linear_fit`'s operands),
  and the gate asserts the result's handle is **NOT `None` AND IS the input's handle**.
  **For the CONTAINER-TRAVERSING class the two halves collide, and the fixture is bound as a
  TEMPLATE**: `gak.zip`'s mapping IS its primary and only array-bearing operand
  (`zip(fields: Mapping[str, Array] | Sequence[Array], …)`),
  so if that operand is fixture-supplied the frozen
  test has no position to substitute into and "the handle is preserved" degrades to `None == None`
  for exactly the class whose purpose is detecting `Varied`/handles INSIDE containers (the same
  applies to `linear_fit`, whose operands are all fixture-supplied). Binding: each `src` fixture
  declares a named **substitution SLOT** — a sentinel the frozen test replaces with its own
  contexted `Array`, *including inside a Mapping/Sequence argument* — and the gate asserts the
  substitution actually happened: the handle-bearing input of the produced call IS the test's own
  contexted `Array`, and only then that the result's handle is not `None` and equals it.
  **Each slot DECLARES the operand KIND it needs, and the frozen test owns one contexted `Array` of
  each kind**: the enumerated classes span functions whose primary operands are incompatible
  and graphed type-checks the primary at RECORD time through the backend's `op_form`, so ONE
  test-owned array cannot serve them all — with a
  contexted jagged-numeric `Array`,
  `gak.num`/`unzip`/`drop_none`/`singletons`/`firsts`/`where`/`unflatten(a, num(a))` all record
  cleanly while `gak.with_field(a, gak.num(a), "x")` raises
  `GraphedTypeError: ill-typed op 'ak.with_field' … no tuples or records in array`, and the
  fixture is barred from supplying the primary. Binding: each `src` fixture's substitution slot
  names its
  operand KIND (flat numeric / jagged numeric / record / boolean mask / option type); the frozen
  test owns one contexted `Array` per kind, ALL read through the SAME context, and substitutes the
  kind the slot names. The context stays test-owned while the type
  requirement — a property of the function — stays beside its classification in `src` (the
  self-repairing rule). **The KIND VOCABULARY is frozen at m48, and that trap is recorded rather
  than ignored**: a gak function added later
  whose primary operand falls outside these kinds arrives with its classification and fixture
  in `src` as designed, but the frozen test owns no operand of its kind — exercising it would
  require EDITING a frozen test, i.e. a Test Dispute. Nothing in m48–m51 trips it: over the
  public gak functions, every primary among the
  *broadcast* / *container-traversing* / *tuple-returning* classes falls inside the five kinds;
  **(3)** the
  *eager-metadata* and *refusing* classes are EXEMPT by classification, not by omission, and the
  gate asserts the exemption set is exactly those two classes (so an exemption cannot be used to
  hide an unimplemented member) **plus a MEMBERSHIP floor on those two classes** — asserting
  the exempt CLASS NAMES constrains nothing about who is in them: classification and its fixtures
  are implementer-editable `src`, so an implementer unable to make `gak.where`/`concatenate`/
  `unflatten` propagate the handle could re-classify it as *eager-metadata*, keep the exempt set
  exactly those two names and stay green; only the representatives m48 pins by name
  (`zip`/`unzip`/`fields`/`type_of`) are otherwise protected. Binding floor:
  **`gak.join` IS IN the *refusing* class and the refusing COUNT is ≥ the freeze-time
  count** — containment plus a monotone count, never an exact set (a frozen `refusing ==
  {gak.join}` equality reds the moment a future gak boundary verb arrives with its classification
  in `src`, which is where the self-repairing rule wants it; nothing inside m48–m51 trips it, so
  this is a maintenance trap rather than a milestone blocker, and containment is the shape this
  clause already uses for the broadcast class). "The bound §5.4
  boundary set" names a CONDITION — a variation cone crossing an Exchange/Join — not a name set,
  and a
  frozen assertion needs the operand; the only
  boundary verb among gak's public functions is `join` — there is no gak
  repartition/exchange/pack_key — so the freeze-time operand is `{gak.join}`.
  Every *eager-metadata*
  member's return annotation is non-`Array`; and the count of *broadcast*-classified functions is at
  least the freeze-time count; **(4)** the `Array` public surface of (a) is gated the same way,
  dynamically enumerated **and resolved on the CLASS per (a)'s rule**, **but with its OWN
  one-line floor rather than (3)'s** ((3)'s clauses do not transfer: the `Array` surface's
  refusing member is `repartition`, not `gak.join`, and "every eager-metadata member's return
  annotation is non-`Array`" is false of `Array` methods generally): on the `Array` surface the
  refusing class is `{repartition}` and the broadcast count is ≥ the freeze-time count. Both gates
  carry (c)'s non-vacuity floor.
  Broadcast recording happens while the *user's* frame is on the stack, so `capture()` attributes
  each varied node to the user's own op line with no provenance copying (`provenance.py`
  skips graphed frames).
- **§2.4 (Combination rule — label-aligned union; one-at-a-time; no cross products.)** When an
  operation combines `Varied` inputs — including a `Varied` combined with one derived from it
  (`jets[jets.pt > 25]` is the canonical case) — the result's labels are the **union**, and for
  each label L every container contributes **its own member for L when present, else its
  `"nominal"` member**. **The union's ORDER is bound** (§3.2 determinism and the §6.1b/`_GroupReduce`
  positional layout in `boost.py` both depend on it): the first operand's order, then labels
  new to the second operand in its own order, `"nominal"` always first. Within a universe L, all
  uses of varied quantities are therefore coherent
  (RDF's whole-cone-substitution semantic). Because §2.1 makes each label belong to exactly one
  knob, cross products can never arise implicitly: at a fill combining shift-varied kinematics with
  a stacked weight `Varied`, shift labels fill with the central weight *as evaluated in that
  shift's universe* (label-aligned), and weight labels fill with nominal kinematics — exactly the
  corpus reference semantics (`systematics.py`) and the universal exclusion convention
  (lit §pythonic-analyses).
- **§2.5 (Validation over convention.)** Silent-drop failure modes from the survey become errors
  or diagnostics: unknown label on `graphed.universe(x, label)` → KeyError listing valid labels;
  form-incompatible or
  cross-Session/cross-source member → construction-time error naming the label; `vary()` registers
  each container with its Session (weak reference), and `compile_ir` diagnostics report any
  registered label that reaches no marked output (DCE already prunes the work; the diagnostic
  prevents the mkShapesRDF silent-cost case).
  **The CHANNEL is named, and its spelling is pinned at m48 freeze like every other new surface
  here.** `compile_ir` returns a frozen
  `CompiledGraph` carrying ONLY `ir: bytes` and `source_names: tuple[str, ...]`,
  so no diagnostics channel exists today and an unnamed one would leave a test-author to
  invent both it and its shape, with a wrong guess frozen read-only. Binding: the report is an
  **additive `CompiledGraph` field** (a sorted tuple
  of unreached labels, empty when every registered label reaches an output) **or an equivalent
  read-only accessor over the same compile**; exact spelling pinned at m48 freeze. If it lands on
  `CompiledGraph`, note the interaction with m48's §7.2 schema-absence anchor, which is worded over
  the `ExecResult`/`Plan`/monitor schemas and not over `CompiledGraph`. The registration mechanism
  ("each container registered with its Session, weak reference") is likewise an m48 Implementation
  Target whose spelling is pinned at freeze — nothing in the anchors depends on it directly.
  **The §2.1 shift-after-weight ordering rule gets a diagnostic on the same channel, and it is
  an m49 target** — a registered ambient weight factor whose reachability cone (§3.4, which lands in
  m49) contains a node a LATER shift `vary` replaces is reported, naming the factor and the varied
  collection, so the "pre-shift weight in every shift universe" case is not silent. Diagnostic, not
  an error: a weight that legitimately does not track the shift is a valid program.
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
  **A `slice` or `int` subscript on a CONTEXT is REFUSED**, naming the supported forms — the
  mirror is partial and m48 freezes context semantics: `Array.__getitem__` also accepts a
  `slice`, recording a boundary `slice` reduction, and an `int`, recording `index`,
  so `events[:1000]` would otherwise be expressible with no bound answer;
  row-slicing has no defined effect on §2.6c's per-label re-indexing rule, and refusal is the
  smaller commitment — a slice-derived context is not scoped in m48–m51. Every
  graphed operation on a context is a module function
  (`graphed.vary`, `graphed.labels`, `graphed.universe`, `graphed.nominal`, `graphed.weight`,
  `graphed.selection`, and `graphed.variations` — §9.1; `graphed.variations` lands in m50,
  `graphed.selection` in m51, the rest in m48). This is
  load-bearing, not style: branch names are analysis-controlled and open-ended, so any reserved
  attribute (`events.weights`, `events.vary`) is a latent collision with real tree content.
  (b) **Contexts are immutable; `graphed.vary` returns a NEW context** (§2.1 overloads b/c). The
  shift form replaces the named collections with `Varied` members (thereafter
  `events.<Collection>` is a `Varied` and §2.3 broadcast carries it; repeated calls stack,
  §2.1); the weight form registers the factor into the returned context's ambient weight (M29
  factor-list semantics; explicit tags in v1 — auto-symmetric derivation from a lone `up` is
  Phase 2, §11). Each returned context links to its parent: variation history is **object
  lineage** — the provenance handle the collaborators asked for; no hidden mutable registry.
  **CONTEXT HANDLE IDENTITY is bound here, once** — three binding rules compare handles
  (§2.3e raises a divergence error when input handles are not on ONE ancestry chain, §6.1d(A)'s
  `graphed.unify_contexts` raises the same error, and §6.4a(2a) is a literal object-identity
  comparison, `graphed.context_of(select_mask) is graphed.context_of(record)`), so it must be
  said whether two contexts produced by EQUIVALENT pure operations are the same handle. The natural
  fresh-object-per-call implementation makes two reads of one universe SIBLINGS — neither an
  ancestor of the other — so the divergence rule fires on programs this plan scopes
  (`graphed.nominal(sel).MET.pt + graphed.nominal(sel).MET.phi` — the OP-level form m48's anchor
  actually freezes; `sel1 = events[mask]`, `sel2 = events[mask]`), a FALSE refusal whose diagnostic
  names a condition the program does not
  contain — the §2.5 confidently-wrong class: **PURE DERIVATIONS ARE CANONICAL.**
  `graphed.nominal(c)`,
  `graphed.universe(c, L)` and `c[mask]` for the same mask (identical per-label node ids) return the
  **SAME context object**, memoised on the parent — while `graphed.vary` ALWAYS returns a fresh one
  (each call registers different content, so §2.3e's divergence rule keeps its meaning for the case
  it was written for, and §2.1's "always returns a NEW object" is untouched). m48's op-level
  divergence anchor gains the positive control that two separate `graphed.nominal(sel)` reads
  UNIFY instead of raising.
  (c) **Scoping is lineage.** A fill sees exactly the registrations present on the context its
  inputs were read from (§6.1d) — the fill-time-snapshot rule re-bound as immutability: a fill
  from a pre-`vary` context is unaffected by later `vary` calls *by construction*.
  **A read performed THROUGH a derived context yields THAT context's row space** — the central rule
  of the whole idiom, against which §6.1d's link
  kind (1), §6.4a's row-space predicates and m48's TWO re-indexing anchors — the §2.6c
  ambient-registry
  one and the §6.1d fill-time ancestor-VALUE one — are all defined:
  `sel.Jet` IS `events.Jet` re-indexed by `sel`'s derivation mask, label-aligned per §2.4 when that
  mask is `Varied` (each label's member by that label's mask, nominal's by nominal's) — the same
  operation the ambient rule below performs, applied to values. Derived
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
  JES-varied `jets` — the derived context's ROW SET DIFFERS PER LABEL. Binding: its collections
  READ as `Varied` (§2.4-aligned per label) — **an implicit property of the derivation, NOT a
  shift-form registration, so §2.2's `graphed.labels` term (b) does not count them (term (b)'s own
  exclusion at its definition site); the mask's own labels enter
  through term (c)**; `graphed.labels(ctx)` **INCLUDES** the mask's labels (the full answer is
  §2.2's union — ambient-weight labels ∪ varied-collection labels ∪ the derivation mask's labels;
  "reports the mask's labels" alone would be a strict subset of what a §6.1d fill from that context
  produces — on this section's own sketch, `sel` carries ambient weight labels the mask does
  not); re-indexing happens per label
  (each label's ambient member is re-indexed by THAT label's mask, nominal's by nominal's);
  `graphed.vary(ctx, …, is_weight=True)` on it stacks per §2.1 (a new weight label's member is the
  provided value's central universe, each inherited shift label keeps its own); fills from it are
  label-aligned per §2.4; and §6.4a's OR-of-selections is exactly the union of these per-label row
  sets.
  (d) **Data contexts refuse BOTH forms.** `is_weight=True` on a data context is a guard error, and
  a **shift-form `vary` on a data context is likewise refused**, with an error naming the variation:
  accepting it and discarding its labels at the fill would silently drop an explicit user
  registration — the §2.5 failure mode. "Data fills nominal-only" is therefore structural **for every
  context-borne registration**, not a convention — **scoped**: the loose primitive stays public,
  so `graphed.vary(data_events.Jet, "jes", up=…, down=…)` is still expressible, its result indexes
  plain `Array`s per §2.3b, and §6.1d's union carries its labels into the fill; making that
  structural too would mean refusing, at the fill, any `Varied` whose members carry a data context's
  handle, which v1 does not bind. What makes a context a data context is an explicit constructor flag
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
  **The following spellings in that sketch are measured, not assumed** (the mid-freeze discovery §4.1's
  `full_like` note
  exists to prevent):
  (i) **there is no tuple subscript on the awkward-idiom `Array`** — `Array.__getitem__` accepts
  an `Array` mask, `str`, `list[str]`, `slice` or `int` and raises `TypeError` otherwise,
  tuple subscripts exist only on the numpy idiom, and no
  gak function takes an arbitrary inner index. The expressible form is the masked one above —
  `gak.firsts(w[gak.local_index(w) == 1])`. (A first-class inner-index verb would be a gak
  addition; it is NOT scoped in m48–m51.)
  (ii) **`Histogram.fill` is positional** — `fill(self, *args: Array, weight=…, sample=…,
  threads=…)` (`graphed-histogram src/graphed_histogram/boost.py`), so `h.fill(pt=…)` is
  an unexpected keyword. Named-axis kwarg fills exist only in the `hist.graphed` fork (cba
  §histogram §3), which is not in m48's repo scope.
  (iii) **the b-tag SF's ARGUMENT is the pt-CUT jets, not `sel.Jet`** — `btag_sf(sel.Jet)`
  is what §2.6c binds to `events.Jet` re-indexed by `sel`'s mask, i.e. the UNCUT
  collection restricted to selected events, while the corpus reference computes the SF on the
  pt-cut jets and `_btag_weight` products a per-jet SF over `axis=1` — so sub-25 GeV jets change
  the weight and a test-author transcribing the `sel.Jet` spelling into m48/m49's reference matrix
  misses the stored references
  (`graphed-corpus src/graphed_corpus/analyses/systematics.py`:
  `jets = _apply_jes(events.Jet, …)`, `good = jets[jets.pt > 25]`, `sel_jets = good[sel]`,
  `weight = _btag_weight(sel_jets, …)`, with `_btag_weight` = `ak.prod(per-jet SF, axis=1)`).
  `sel.Jet[sel.Jet.pt > 25]` is the corpus-faithful spelling — the object cut and the
  event re-index commute — and it is read THROUGH `sel`, so it also satisfies §2.1(b)'s row-space
  requirement by construction. m48's matrix anchor repeats the note alongside the existing
  `gak.full_like` / `stable()`-rounding mid-freeze-discovery notes.
  The neutral context *mechanism* (lineage, ambient weight, fill-inference seam) lives in
  `graphed` proper; the nanoevents-flavored constructor is awkward-idiom and lives in
  `graphed.awkward` (factorization rule preserved). The loose `graphed.vary` on Arrays (§2.1a)
  remains public — the context is built on it, not beside it.

## §3 IR and optimizer treatment

- **§3.1 (No new NodeKey.)** No Rust IR variant, no serialize tag, and **no optimizer SEMANTICS
  change** is added for variations. The ONE optimizer-adjacent addition in m48–m51 is §8.2(i)'s
  m49 read-only remap accessor, which necessarily retains and returns data
  `dead_code_elimination` today discards: read-only, no new `NodeKey`, no serialize tag, no
  rewrite arm, no change to what the reducer produces (cross-referenced from §8.2). The varied
  universes are ordinary nodes; sharing is interning (`src/store.rs`); the m4 frozen scaling
  contract (`tests/frozen/core/m4/test_systematics.py`) continues to bind unchanged. Any future
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
  assertion vacuous). N ∈ {16, 32, 64, 128}. Under that topology (D=500, K=50) the exact reduced
  shape is `stages == N + 1` and `reduced_nodes == 2N + 2` (cba §optimizer §2). **The terminating
  reduction is load-bearing**: the same builder WITHOUT it reports `reduced_nodes == N + 2`
  (N=16 → 18, N=128 → 130), so a suite that omits it freezes an assertion a correct reducer fails.
  A fill IS a reduction, so the with-reduction shape is also the realistic one.
  Plus a linear-growth bound (**time(128)/time(16) < 16.0**, the m4 threshold STYLE at m4's
  headroom RATIO rather than at m4's literal): m4 spans 8× NODES and gates at 24.0, i.e. 3×
  headroom over linear, failing exponents ≥ ln24/ln8 = 1.53. This topology's node count grows only
  **5.37×** from N=16 to N=128 while N grows 8×, with a measured time ratio of 5.64
  (cba §optimizer §2), so the copied 24.0 would fail only exponents ≥ ln24/ln5.37 = 1.89 — a
  node-QUADRATIC reducer measures 5.37² ≈ 28.8× asymptotically, only 1.2× above the gate, and any
  non-negligible linear term pulls it under. 16.0 keeps ≈2.8× headroom over the measured 5.64 and
  still fails a node-quadratic reducer by ≈1.8×. (The self-scaling form
  `time(128)/time(16) < 3 × nodes(128)/nodes(16)` is equivalent and buildable — `reachable_nodes`
  is in `reduce()`'s returned report — if a future revision prefers it to a literal.) Replicate
  the m4 noise floor (`base = max(times[SIZES[0]], 1e-4)`) and best-of-N timing
  (`test_benchmark.py`). **This is the ONE frozen wall-clock gate in m48–m51, and it is a
  deliberate, named carve-out to R0.10a**: the project plan's M4 mandates a CI benchmark that
  fails on super-linear reduction time, and `tests/frozen/core/m4/test_benchmark.py` is the frozen
  precedent that discharges it. Every other performance claim in this plan (§6.2 axis scaling,
  §6.4c compression) is demoted to an R0.11 implementer-report measurement precisely because it
  has no such mandate.
- **§3.4 (Impact-set API.)** A read-only frontend helper reports, per label, the **reachability
  difference** `reachable(label's outputs) − reachable(nominal outputs)` computed via
  `session.walk`. It is a **read-only `graphed` module verb over the per-label output CONTAINERS —
  `Sequence[Varied] | Mapping[str, Sequence[Array]]`**, the labelled mapping being what this
  plan's primary sink already returns: §9.1's per-label fill-node accessor is
  `fill_nodes_by_label(h) -> dict[str, Array]`, so on a real varied histogram program the caller
  holds a mapping, and re-assembling a `Varied` from it would need the name/tag decomposition §2.2
  measures as unreliable; §4.3's optional cross-check names that same mapping as its operand. This
  is the LABELLED analogue of `read_columns`' first operand, and NOT its `source_nid`:
  `read_columns(arrays: Sequence[Array], source_nid: int)` (`python/graphed/projection.py`) and
  `Array` is `__slots__ = ("_node_id", "_session")` (`python/graphed/array.py`), so a
  `Sequence[Array]` carries NO label attribution and a verb over it can neither compute "that
  label's outputs" nor key its return by label — while a reachability DIFFERENCE over
  `session.walk` is source-agnostic, which is why `source_nid` stays out. The verb resolves each
  label's outputs by `graphed.universe(v, L)` per member and walks from there — returning
  `{label: tuple[int, ...]}`: per label, that label's SORTED RECORD-time node ids
  (`tuple(sorted(...))` is the house shape, `python/graphed/projection.py`) — **listed in §9.1,
  exact spelling pinned at m49 freeze**. The element type is load-bearing, not defensive typing:
  `session.walk` exposes ids only through caller-supplied handlers and returns the root's value
  (`python/graphed/session.py`), so the return shape is otherwise a free implementation choice,
  and m49's anchor asserts MEMBERSHIP in the per-label value — an assertion written one way for
  node ids and another for `Array`s. It is **NOT an id watermark** (interleaved broadcast
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
  existing one (`python/graphed/awkward/functions.py`; already parity-pinned by
  `tests/frozen/awkward/m24/test_interface_parity.py`) — or ordinary arithmetic on such an Array.
  What does NOT exist is a **partition-aligned** constant Array with no shape donor:
  `graphed.numpy` ships donor-free `full`/`ones`/`zeros`/`empty`/`arange`/`linspace`
  (`python/graphed/numpy/creation.py`, all in `__all__`), but each records an **eager fixed-shape
  in-memory Source** (`session.source(name, form=…, data=arr)`), and a plan built through
  `aggregate_plan` binds exactly ONE source (`python/graphed/aggregate.py`,
  `{self.source_name: chunk}`), so a second source makes `evaluate_ir` raise
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
  superficially plausible predicates are NOT equivalent to it and are rejected. The wording "the
  §3.4 impact set contains no node outside the fill's weight-input cone" is false for a correct
  implementation: a label's output IS its sibling fill node, which by construction is not
  reachable from nominal's output and therefore always lands in the impact set while sitting
  *downstream* of, not inside, the weight-input cone. The predicate "the intersection of
  `reachable(selection_mask)` with each label's `reachable(fill_node[label])` is identical across
  labels and equal to `reachable(selection_mask)`" is satisfied BY CONSTRUCTION and cannot fail:
  in any weight-variation program the filled value is post-selection (`obs = x[mask]`) and
  `Histogram.fill` records ONE External node whose `inputs` are the axis args followed by the
  weights (`graphed-histogram src/graphed_histogram/boost.py`), while `session.walk`'s post-order
  over `inputs_of` makes a node's cone the transitive closure of its inputs
  (`python/graphed/session.py`) — so `reachable(selection_mask) ⊆ reachable(fill_node[L])` for
  EVERY label in every implementation that fills selected data, the intersection is the constant
  `reachable(selection_mask)`, and both halves hold. It is a containment test, blind to the
  failure the binding sentence names: a label whose selection cone is a strict SUPERSET of
  nominal's (`mask_L = mask & g_L`) passes it. **The EXTRACTION mechanism is bound too**: in a
  weight-only program the selection is a plain unvaried `Array`, so "the selection cone" is
  singular and the assertion has content only in the per-label form. **The binding form is the
  converse, which is literally the binding sentence and directly readable**: per label, take the
  fill node's recorded `inputs` from the store and assert the **NON-WEIGHT prefix**
  (`store.nodes()[fill_id]["inputs"][:n_axes]`) is IDENTICAL to nominal's for every label —
  identical node ids ⇒ identical cones by interning (`src/store.rs`), and the `n_axes` split is
  exactly the recorded `params["n_axes"]` (`boost.py`; the frozen precedent counts that layout
  already — `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py` asserts
  `len(node["inputs"]) == 4` for one axis + three weights). A reachability cross-check MAY ride
  along, in the discriminating shape only:
  `reachable(fill[L]) − reachable(weight_input[L]) − {fill[L]}` identical across labels. Either
  form fails a `mask_L = mask & g_L` implementation; the rejected containment form passes it.
  **`session.walk` takes an `Array`, not a node id** (`root = array.node_id` in
  `python/graphed/session.py`), so the test wraps each id as `Array(session, nid)` (`Array` is
  exported from `graphed`). `fill_node[label]` needs a **public per-label channel that must be
  BUILT, and is bound in §9.1**: today `Histogram.fill_nodes()` IS public
  (`graphed-histogram src/graphed_histogram/boost.py`) but returns a bare `list[Array]` in
  staged-fill order with **no label attribution**, and §7.2 says only that the frontend *owns* the
  `(output, label) → node id` map — ownership is not an importable surface, and this assertion
  needs a PUBLIC one. Private access is tolerated where an anchor PINS the route (the m48 (α)
  anchor bindingly reads a field off `graphed.aggregate._PartitionReduce`; the m29 precedent reads
  `s._store.nodes()`), but no private route reaches a label correspondence that exists nowhere;
  §9.1 pins the accessor's spelling at m48 freeze. Because the operands come from a fill, **this
  anchor sits in `graphed-histogram`'s half of the m48 split** (§10). An equivalent public
  impact-set cross-check MAY ride along: `impact(L)` minus L's own output node is disjoint from
  `reachable(selection_mask)`. The m05 equal-counts check rides along as a sanity assertion.

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
- **§5.2 (Witnesses that sharing engaged — R0.10.)** The m49 suite pins mechanism witnesses, not
  just results: (a) **arena-delta witness on the §3.3 topology with a literal expected integer**
  (the m4 style — on the §3.3 builder, one universe = {1 varied fork op, K=50 chain ops, 1
  terminating reduction}, so going N=1→2 adds exactly `K + 2 = 52` nodes. **The terminating
  reduction is load-bearing here too**: the same builder without it measures Δ = 51, so the
  literal must travel with the builder. A self-derived `delta == len(cone)` comparison is
  tautological).
  **The witness MUST be built through the public `graphed.vary` surface**: §3.3 tells the author to
  replicate `tests/frozen/core/m4/test_benchmark.py`, which builds with the raw
  `graphed.core.GraphStore` API (`import graphed.core as gc`; `add_source`/`add_op`, as does
  `tests/frozen/core/m4/test_systematics.py`), so an author following §3.3 can hit every pinned
  integer while witnessing only `GraphStore::intern` — already frozen at m1/m4.
  **What the delta DOES and does NOT discriminate**: re-recording the shared prefix through the
  SAME Session interns to the same ids and adds ZERO nodes, so no arena-delta form can catch a
  prefix-re-recording implementation. The delta discriminates that **no per-universe COPY enters
  the arena** — i.e. labels are out of node identity (§1.2) and interning is engaged through the
  public `vary` path, which a per-universe store or a label leaking into `NodeKey` params would
  blow up. The re-recording concern is caught by §5.2b's single-read
  `part_reads == n_partitions`, which a per-variation re-run loop cannot pass; that is where it is
  anchored.
  **The measurement SPAN and the ORACLE are bound, and both are obtainable pre-implementation.**
  Bracketing the `vary` call itself cannot observe `K + 2`: under record-time expansion (Part I §3)
  the `vary` call introduces only the fork member, and the K chain ops and the terminating
  reduction are recorded AFTERWARDS, when the user applies the chain to the returned `Varied` — so
  bracketing the call measures Δ ∈ {0, 1}. And under §12.1 the test-author freezes the suite
  before any `vary` implementation exists, so no expected integer may require the frontend to
  obtain. **(1) SPAN** — `Session.node_count()` after building the COMPLETE N=1 program versus
  after building the COMPLETE N=2 program in the SAME `Session` (the nominal re-record is free by
  interning), so the delta is exactly the second universe's suffix; **(2) ORACLE** — the same
  second universe hand-built WITHOUT `vary` in a separate `Session`, whose own node-count delta
  supplies the expected integer. That is an INDEPENDENT construction the author can run at freeze
  time, not a self-derived `delta == len(cone)` comparison, and it needs no frontend `vary`.
  `K + 2 = 52` is the raw-builder number and MUST NOT be assumed to carry over unchecked. Labels
  structurally identical to a prior label dedup to Δ = 0 by §1.2 — that case is witnessed
  separately as the dedup feature, in the **m48 §1.2 label-out-of-identity anchor** (§10), not
  under this witness. (b) **single-read witness bound to the reference-matrix run itself**: the
  read-counting partitioned source (m23 pattern) asserts `part_reads == n_partitions` — not
  `n_partitions × n_labels` — on the SAME Session/plan that reproduces the corpus references
  (**the m49 `graphed-histogram` half, §10/m49(i), where m48's vendored references live** — §10
  places m49's reference matrix in `graphed-histogram`'s flat `tests/frozen/m49` and §10/m49(i)
  binds the §5.2b read witness to that run; `graphed`'s `tests/frozen/frontend/m49` holds the
  NON-fill anchors and cannot host a fill-based matrix without `importorskip`-SKIPping it, since
  `graphed`'s dependencies and CI do not install `graphed-histogram`. The same reading applies to
  m48's matrix, which §10/m48 already places in `graphed-histogram`), so a per-variation re-run
  loop cannot pass. (c) **reduced-stage shape — on the §3.3 SHAPE but built through
  `graphed.vary`**: the shared prefix appears in exactly ONE stage, and the total stage count
  equals an **ORACLE**, not a literal. **The oracle is bound for the same reason §5.2a's is**: the
  `stages == N + 1` / `reduced == 2N + 2` literals come from the raw `graphed.core.GraphStore`
  builder, as §3.3 and this paragraph both say, and re-measuring a frozen literal through the
  frontend post-freeze is a Test Dispute or an integrity violation under §12.1, since the author
  freezes before any `vary` implementation exists. The expected integer is taken from the **same
  N-universe topology hand-built WITHOUT `vary` in a separate `Session`**, reduced, its stage
  count read off — the independent construction §5.2a already binds for the arena delta — and the
  `vary`-built program MUST equal it. §3.3's raw-builder shape (N=16 → 17 stages, N=128 → 129) is
  the expectation for the oracle itself and MUST NOT be asserted directly of the `vary`-built
  program. **It does NOT ride the §3.3 benchmark fixture** — that fixture is a raw
  `graphed.core.GraphStore` construction (`tests/frozen/core/m4/test_benchmark.py` builds with
  `import graphed.core as gc` / `add_source` / `add_op`, and §3.3 tells the author to replicate
  it), so asserting the stage shape there would re-assert the M4 frozen reducer contract and
  witness nothing about `vary`, under a section headed "witnesses that sharing engaged". It is a
  frontend, `vary`-built program in `graphed`'s `tests/frozen/frontend/m49` — the same fixture
  §5.2a needs and the placement §10/m49 already assigns it; `tests/frozen/core/m49` keeps the raw-
  `GraphStore` scaling benchmark only.
- **§5.3 (Projection.)** Column projection is the union over all requested outputs — correct today
  with zero changes (`read_columns` takes `Sequence[Array]`, `projection.py`); m49 pins a test
  where a shift needs an extra column and the union grows by exactly that field.
  **The FIXTURE SHAPE is pinned here, because the granularity makes the obvious spelling
  unsatisfiable**: `read_columns` counts a `field`/`fields` op only when its input IS the source
  node (the `reads_source` check in `python/graphed/projection.py`), so it reports only fields
  read DIRECTLY off the source record — on a nested record `read_columns([events.Jet.pt], src)`
  and `read_columns([events.Jet.pt, events.Jet.eta], src)` are BOTH `('Jet',)`. The m49 fixture's
  source is therefore **FLAT** (branch-per-column, `Jet_pt`/`Jet_eta`/`Muon_pt`) and the shift's
  extra column is a distinct TOP-LEVEL field, `Jet_eta` (on that shape: `('Jet_pt',)` →
  `('Jet_eta','Jet_pt')`). Buffer-level projection is not what §5.3 binds. Per-label projection
  stats make the read-width cost of a shift visible — **and that exposure is anchored in the same
  m49 test** (§3.4's own anchor covers impact sets, not read widths): the same test asserts the
  stats report the shifted label's extra column. **The SURFACE is named and pinned** — §3.4's API
  is a reachability difference over node SETS, not a read width, so the stats carry their own
  name, shape, return type and "spelling pinned at freeze" clause, like every other new surface
  here (`graphed.context_of`, `graphed.weight`, `graphed.selection`, the per-label fill-node
  accessor, `graphed.broadcast_like`, `read_varied`, §2.5's diagnostic channel): it is a
  **read-only `graphed` module verb over the per-label output CONTAINERS —
  `Sequence[Varied] | Mapping[str, Sequence[Array]]` (§3.4 — the labelled mapping is what §9.1's
  fill-node accessor returns, and a weight-borne shift column is read at the per-label FILL node,
  which that accessor is what hands out) plus `read_columns`' own `source_nid`** (the verb does
  not take `read_columns`' own operands: that first operand is `Sequence[Array]`, and `Array`
  carries only a node id and a session — no label attribution to key a `{label: …}` return on;
  `source_nid` stays, because this verb CALLS `read_columns` per label) — **returning
  `{label: tuple[str, ...] | None}`** — per label, that label's SORTED read set, computed by
  applying `read_columns` to each label's members (`graphed.universe(v, L)` for a `Varied`
  operand, the mapping's own entry for a labelled mapping) — **listed in §9.1, exact spelling
  pinned at m49 freeze**. **The `| None` is load-bearing, not defensive typing**:
  `read_columns(arrays, source_nid) -> tuple[str, ...] | None` and `None` is a live, semantically
  INVERTED answer — "read every column", returned on whole-record consumption or a bare source
  read (`if conservative or not needed: return None`). Under a bare `tuple[str, ...]` an
  implementer must render that as `()`, which reads as "reads nothing" — the exact opposite — or
  violate a frozen type. The m49 anchor carries a conservative label (one gak op applied directly
  to the source) asserting the `None`.
  **That conservative label rides a SEPARATE program (or a separate output set) from the
  union-growth assertion, and the scoping is binding**: `read_columns` carries ONE `conservative`
  flag across ALL the arrays passed and returns `None` if any one of them consumes the whole
  source record, and §2.3d states the same for the varied union ("`None` if ANY member's read set
  is `None`"). With the conservative label inside the SAME varied program the union collapses to
  `None` and the "union grows by exactly that field" half is either vacuous (`None == None`) or
  red against a correct implementation. Equivalently, half (i) MAY be restated per label through
  the stats verb, **order-insensitively**:
  `set(stats["jes_up"]) - set(stats["nominal"]) == {"Jet_eta"}` AND
  `set(stats["nominal"]) - set(stats["jes_up"]) == set()` (the second conjunct keeps it from
  degenerating to a containment test). **Plain CONCATENATION — `stats["nominal"] + ("Jet_eta",)` —
  is RED**, because both returns are SORTED (`return tuple(sorted(needed))`) and on the flat
  fixture the extra column sorts FIRST (`('Jet_eta','Jet_pt')`);
  `stats["jes_up"] == tuple(sorted(stats["nominal"] + ("Jet_eta",)))` is the acceptable
  concatenation form.
  Per-variation partition-level projection splitting is Phase 2.
- **§5.4 (Boundary restriction, explicit.)** v1 REFUSES (clear `NotImplementedError` naming the
  label and the boundary) a variation whose cone crosses an `Exchange`/`Join` node — the m39/m40
  plan builders are single-boundary (`shuffle.py`) and silent miscompilation is worse than
  refusal. The refusal test carries a **positive control**: a variation entirely *downstream* of a
  Join/Exchange compiles and produces correct results (a blanket "Varied near Join raises" must
  fail the suite). Generalizing the builders is named Phase 2 (§11).
- **§5.5 (Stochastic shifts — JER-SF re-smearing is first-class; determinism still binds.)** A
  shift variation MAY be stochastic (MC jet re-smearing under a jet-energy-resolution scale
  factor). Two binding rules, both grounded in coffea's own implementation (lit §coffea-sys):
  (a) **randomness MUST be a deterministic pure function of event content** — the precedent seeds
  PCG64 from the input array's own bytes (`rand_gauss`, coffea
  `jetmet_tools/CorrectedJetsFactory.py`); global RNG state, wall-clock, or per-run seeds are
  forbidden — the R0.4/R12 determinism gate applies to varied graphs unchanged. **The observable
  consequence is PARTITION INVARIANCE, and that is what the m49 witness asserts**: a per-partition
  constant seed (`np.random.default_rng(0)`) is reproducible, migrates events both ways, and still
  interns as one draw node — so it passes every other listed witness while giving the same event a
  different smear under a different partitioning. Content-seeded randomness makes the same event
  set at two different `steps_per_file` values produce byte-identical per-label results; a
  seeded-per-partition implementation does not.
  **The COMPARED QUANTITY is bound, because "byte-identical" is not a safe invariant for an
  aggregated float result**: `steps_per_file` is a plan parameter, so changing it changes the
  grouping of float additions in the combine tree, and a CORRECT implementation can then differ in
  the last ulp — this plan concedes the effect in m48's own matrix bullet ("`bin_values`'
  driver-side rounding is what absorbs the float-summation-order differences a per-partition fill
  introduces"), and the existing partition-count-invariance precedent works only because its
  result is an int64 histogram (`graphed tests/frozen/checkpoint/m8/test_resume.py` with
  `analyses.py` returning `np.int64` counts; contrast
  `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py`, which asserts `array_equal`
  run-to-run at FIXED partitioning and only `allclose(rtol=1e-12)` against the eager fill). The
  invariance witness therefore compares **partition-local objects that concatenate
  deterministically** — the per-event/per-object SMEARED VALUES and the per-label selection
  MASKS — or an unweighted integer-storage count histogram; never a weighted float histogram.
  (b) **One draw, all universes**: the random vector is drawn once and shared — coffea's
  `jer_smear` takes a single `jet_resolution_rand_gauss` while only the SF column varies per label
  (the hybrid `detSmear`/`stochSmear`, where `deltaPtRel` is signed and the stochastic branch
  scales a signed gaussian — hence non-monotone by construction) — so under `vary` the draw node
  lives in the shared prefix and interns once (§3). The m49 suite carries a JER-SF-style fixture
  (§10) whose witnesses assert bidirectional migration and run-to-run byte-identity, never
  ordering (§5.1).

## §6 Sinks: histogram fills (§6.1–§6.3) and variation-aware write-out (§6.4)

- **§6.1 (MVP shape: sibling fills, named results.)** `Histogram.fill` accepting `Varied` axis
  values and/or `Varied` weight factors lowers per §4.2/§5.1 under the §2.4 rule. Binding result
  and lowering shape:
  (a) **Per-output label sets** (this rule is **scoped to the DEFAULT sibling-fill lowering**;
  §6.2's opt-in axis mode has a third result shape, bound there). Each output's mapping carries
  exactly the union of labels reaching *that* output — `{output_name: {label: hist}}`, nominal
  always present; an output no variation reaches returns a bare `hist` (NOT `{"nominal": hist}`),
  so unvaried programs see today's shapes unchanged. Absent labels are absent, never silently
  duplicated from nominal.
  **This is the shape of the UNPACKED user-facing result, NOT of the plan's combined value.**
  Binding: **the plan's combined value is the FLAT slot-keyed mapping §6.1c binds —
  `{(output, label) → bh.Histogram}` for a VARIED output in sibling mode,
  `{(output, None) → bh.Histogram}` for an axis-mode output — and `_add_groups` stays a homogeneous
  key-wise `+`** (`{label: a[label] + b[label] for label in a}`,
  `graphed-histogram src/graphed_histogram/boost.py`). **The slot keying is SCOPED to outputs a
  variation reaches, and that scoping is binding**: an output NO variation reaches keeps today's
  BARE `output_name` key — **and that rule is itself scoped to SIBLING-mode outputs**: the MODE,
  not the variation count, decides an axis-mode output's key, so an axis-mode output whose fills
  carry no variations is still keyed `(output, None)` per §6.1c. That program is expressible —
  §6.2's opt-in is per-histogram and §6.2(ii) makes the frontend declare the axis ALWAYS, from an
  inferred label set that is `{"nominal"}` there (the user-facing result is identical either way: a
  bare histogram, which `graphed.labels` duck-types on `.axes`). The bare-key rule for wholly
  unvaried sibling-mode outputs preserves the already-frozen m23 suite, which indexes
  `SequentialRunner().run(gh.plan({…})).value` by bare output name
  (`graphed-histogram tests/frozen/m23/test_group_plan.py` — the reducer's key IS the output name
  today, fed by a `layout` built over `(output_name, Histogram)` pairs), while §10 binds the frozen
  m23 artifacts "binding and unchanged" and `plan()`'s declared return type is
  `Plan[dict[str, bh.Histogram]]` under the DoD's `mypy --strict`. All three key forms carry a
  plain `bh.Histogram` value, so `_add_groups`' key-wise `+` stays homogeneous whatever the key.
  m48's §6.1a anchor carries a wholly-unvaried positive control.
  The `{output_name: hist | {label: hist}}` shape above is what a bound **FRONTEND UNPACKER**
  produces from that value. **That unpacker is a NAMED read-only surface, not an unstated step**
  — there is no seam to hang it on otherwise: `Plan` is
  `(process, combine, empty, tasks, next_tasks, stop, open_once)` with NO finalize hook,
  `ExecResult.value` is exactly the combine output (`python/graphed/core/execution.py`),
  `graphed_histogram.plan()` returns that `Plan` and nothing else, and adding a `Plan` field is
  foreclosed by §7.2's m48 schema-KEY-SET anchor: a read-only **`graphed_histogram` module verb
  over the executed plan value ALONE — `graphed_histogram.unpack(value)`-shaped, exact spelling
  pinned at m48 freeze** — returning `dict[str, bh.Histogram | dict[str, bh.Histogram]]`.
  **It takes ONE argument, and the per-output shape is decided by the SLOT KEY FORM, not by a
  recorded MODE**: the layout is not reachable from the executed value — `Plan` has no layout
  accessor and `ExecResult` carries only `value`/`n_partitions`/`n_combines`/`stopped`, the layout
  living inside `_GroupReduce`, the plan's `process`. The key form is total and per output: a BARE
  `output_name` key → that output's bare `bh.Histogram`; a `(output, None)` key → the axis-mode
  output's bare variation-axis histogram (§6.2 i-bis); the `(output, label)` keys of one output →
  `{label: hist}`. A varied sibling output always carries ≥ 2 labels (§1.1 makes labels non-empty
  and `"nominal"` is always present), so no output's shape is ambiguous, and this holds in a MIXED
  plan exactly as in a single-mode one. Listed in §9.1 with the other m48 accessors; m48's §6.1a
  anchor is worded over it.
  The declared result type is therefore the value-dependent union
  `dict[str, bh.Histogram | dict[str, bh.Histogram]]` **at the unpack surface** — a real typing
  cost under the DoD's `mypy --strict` on src AND tests, accepted for the backward-compatibility
  win and paid for explicitly by a bound narrowing helper so callers do not hand-roll
  `isinstance` — `graphed.universe(result[name], label)` and `graphed.labels(result[name])` work
  uniformly on BOTH shapes (§2.2), a bare `hist` reading as the single label `"nominal"`.
  (b) **Structural fill-node arity** (again **sibling-mode only**). A fill combining shift labels
  S and weight labels W records exactly `1 + |S| + |W|` fill nodes — never the product
  (frozen-counted via the staged-fill list, the §2.4 discriminator). **S and W are defined by
  LOWERING BEHAVIOUR, not by the "shift"/"weight" vocabulary**: `S` = the labels that require their
  own SIBLING fill node — those borne by any AXIS value **or by a `Varied` `sample=`** — and `W` =
  the labels borne ONLY by weight factors (ambient or explicit), which are the ones §6.2's axis
  mode can collapse into an evaluator-side loop. `sample=` is a first-class fourth label source
  that m48 freezes as ACCEPTED/expanded (`sample` is appended to the same `inputs` list with no
  type check today, `graphed-histogram src/graphed_histogram/boost.py`); a label borne solely by
  `sample=` cannot ride the weight loop, which re-fills with different weights against a FIXED
  sample column, so it must lower as a sibling. Axis mode's arity is `1 + |S|` under the same
  definitions and is stated in §6.2, so m50 does not land a feature contradicting a count frozen
  in m49.
  **WHERE the `S`/`W` split is witnessable is bound too, because the sibling formula cannot see
  it**: `1 + |S| + |W|` counts every label exactly once whatever its class, so m49's arity anchor
  is green under EITHER classification of a `sample=`-borne label and adding such a label to that
  fixture buys nothing discriminating. The split is observable only in AXIS mode, whose arity
  `1 + |S|` counts `S` and collapses `W`: **m50's equality anchor carries a label borne ONLY by a
  `Varied` `sample=`, asserting it lowers as a SIBLING (it counts in `S`) and that the axis-mode
  result still equals its sibling-fill decomposition.** **That fixture MUST use a `Mean` or
  `WeightedMean` STORAGE and per-label sample values that DIFFER**: boost_histogram 1.8.0 rejects
  `sample=` on the default `Double()` storage AND on `Weight()`
  (`TypeError: Keyword(s) sample not expected`) and accepts it on `Mean()`/`WeightedMean()`, while
  `graphed-histogram`'s evaluator passes `sample` straight through to `h.fill` — so on the default
  storage the anchor dies at EVALUATION, after the freeze, against a correct implementation; and
  with a storage that discards the sample the two classifications are indistinguishable, i.e. the
  anchor is vacuous. (`_spec.py`'s `_STORAGES` carries both mean storages, and the variation-axis
  spec round-trips and adds on them.) Without it an implementation classing a sample-only label
  into `W` passes every m48-m49 anchor and, at m50, folds it into the evaluator's weight loop —
  which re-fills with different weights against a FIXED sample column, i.e. a silently WRONG
  histogram no frozen test would see.
  (c) **The single-histogram `.plan()` path refuses varied fills**: `_SumFills` sums ALL staged
  fill nodes into one histogram and would silently merge universes; varied histograms route
  through the group-reduce path (`_GroupReduce` `{label: hist}` generalized to two-level keys),
  and **`.plan()` raises — pointing at the group API — on a `Histogram` that is VARIED *or* in
  §6.2 AXIS MODE**. **The two arms are INDEPENDENT tests, not equivalents**: the AXIS-MODE arm is
  equivalently "a staged fill node whose spec differs from the `__init__`-time `self._spec`", but
  the VARIED arm is NOT spec-visible — `__init__` fixes `self._spec = spec_of(self)` and EVERY
  `fill` bakes that same attribute into the node (`params={"spec": self._spec, …}`,
  `chash = content_hash(self._spec)`), while §1.2 keeps labels out of params/hashes and §6.3 pins
  the params key set, so a SIBLING-mode fill — varied or not — records `self._spec` verbatim (§6.2
  says the same); a spec-comparison-only `.plan()` would NOT refuse a varied sibling-mode
  histogram — the merge hazard this clause exists to prevent. Binding: the VARIED arm is decided
  frontend-side on whether the histogram carries any varied fill (m48); the AXIS-MODE arm by the
  spec comparison (m50). **The trigger is keyed on the MODE**, matching §6.1a/§6.1c's rule that
  "the MODE, not the variation count, decides": the axis-mode-with-NO-variations program — legal,
  and the fourth output m50's anchor adds — must not fall THROUGH the refusal into the same
  hazard, since §6.2(ii) declares the variation axis ALWAYS in axis mode (a 1-bin `{"nominal"}`
  axis there), so its fills' spec still differs from `self._spec` and `.plan()` would otherwise
  die with an opaque `boost_histogram` error instead of the bound refusal (bh 1.8.0: adding
  histograms whose axis lists differ raises `ValueError: axes have different length`). **The
  refusal is GENERAL — sibling mode AND §6.2's axis mode**: `_SumFills`' plain addition over
  disjoint variation-axis bins merges nothing, but the SPEC it starts from is the hazard —
  `Histogram.plan` passes `_SumFills(self._spec)`/`_ZeroHist(self._spec)` and `self._spec` is
  fixed in `__init__` (the very fact §6.2(i) uses to prove a plan-time variation axis
  unimplementable), so under §6.2's FILL-time declaration the reducer starts from
  `zero_of(spec-without-variation-axis)` and adds fill results that carry it — the same
  `ValueError` (boost_histogram 1.8.0). §6.1c's per-slot spec repair is scoped to `_GroupReduce`'s
  layout and does not reach `_SumFills`/`_ZeroHist`, which take a single spec and have no slot.
  Axis-mode programs therefore also route through the group API; no m50 anchor needs
  `Histogram.plan` to SUCCEED on an axis-mode histogram (m50's fourth output asserts it RAISES
  this refusal, which is the axis-mode arm's only coverage).
  **The reducer's LAYOUT changes shape, and that is binding, not an implementation detail** —
  "generalized to two-level keys" is satisfiable while shipping the §7.2 bug: today `layout` is
  `tuple[tuple[str, int, str], ...]` = `(label, n_fills, spec)` sliced **positionally** over the
  distinct-output list, so the moment two marked fills intern to one node — the case §1.2 mandates
  and m48 freezes — `sum(k)` exceeds `len(values)` and the reducer mis-slices or `IndexError`s
  (`mark_output` de-dups in `src/store.rs`; `evaluate_ir` returns one value per DISTINCT output).
  Binding: **`layout` carries per-slot output INDICES**, not counts —
  `tuple[tuple[str, tuple[int, ...], str], ...]` (or `{(output, label): [indices]}` for the
  two-level shape) — derived frontend-side per §7.2 as **the index of each marked record id's
  FIRST OCCURRENCE in `plan()`'s OWN ordered `fill_nodes` list**, so a shared node id
  **replicates** into every slot that needs it instead of shifting positions. **The operand is
  that list, NOT the compiled output list, and NOT §7.2's `aggregate_plan` seam**: the compiled
  artifact's `outputs()` are POST-REDUCTION ids that cannot be joined to the record ids `plan()`
  owns (§7.2), while `fill_nodes` is built in `plan()` immediately before `layout` and before the
  `aggregate_plan` call, and `evaluate_ir` returns one value per distinct requested id in exactly
  that first-occurrence order. The seam stays an m48 target for §7.2's merge refusal and m49's
  `variation_labels`; this layout needs nothing from it.
  **The AXIS-MODE slot is bound here too — and it is scoped to m50, with §6.2** (mirroring
  §6.1a/§6.1b's sibling-mode scoping: axis mode does not exist until m50, so leaving this source
  in m48's "§6.1" target lands it with zero m48 frozen coverage — the DoD's ≥90%
  diff-coverage-FROM-THE-FROZEN-SUITE gate; m50's scaling anchor is worded over this paragraph —
  §6.1c binds only the sibling `{(output, label)}` shape while axis mode needs the opposite: its
  `1 + |S|` fill nodes collapse into ONE slot per output whose value is a BARE histogram carrying
  the variation axis, §6.2(i-bis), not a `{label: hist}` mapping, and m50's scaling anchor counts
  exactly these slots): an axis-mode output contributes **exactly ONE slot, keyed
  `(output, None)`**, gathering ALL that output's fill-node indices, and its per-slot value is the
  bare histogram. **That keying holds WHATEVER the output's label count — the MODE decides, not
  the variation count** (§6.1a's bare-`output_name` rule is scoped to SIBLING-mode outputs; an
  axis-mode output no variation reaches is still `(output, None)`). A plan MAY therefore carry
  sibling-mode and axis-mode outputs together. **The layout records NO per-output MODE**: the
  three key forms §6.1a binds — bare `output_name`, `(output, label)`, `(output, None)` — are
  disjoint and per OUTPUT, so the unpacker reads the shape off the keys in a MIXED plan exactly as
  in a single-mode one, which makes a MODE field unwitnessable: an implementation that never
  records it passes every m48–m51 anchor, including m50's mixed-mode one, so it could not carry a
  discriminating frozen test. The layout is also not reachable from the executed value, which is
  why §9.1's `unpack(value)` takes the value alone. A mixed-mode plan stays m50's anchored case
  for the UNPACKING and per-slot-spec behaviour it is the only program to exercise (§10/m50).
  **The COMBINE needs no branch**: under the bound keying every slot's value is a plain
  `bh.Histogram` — a sibling slot `(output, label)` holds one, an axis-mode slot `(output, None)`
  holds one carrying the variation axis — what actually varies per slot is the SPEC, which this
  paragraph binds separately as the fill node's spec and which `_GroupZero` already consumes per
  slot. `_add_groups` is a key-wise `+` that requires the value type be uniform PER KEY, which the
  `(output, None)` keying gives by construction. (Latent today for two unvaried histograms with
  identical fills; variations make it routine.) **The layout's third element — the per-slot spec —
  is the FILL node's spec, not the histogram object's**: today every consumer takes it from the
  histogram (`layout` built from `h._spec`; `_GroupZero` builds `zero_of(spec)`; `Histogram.plan`
  passes `_SumFills(self._spec)`/`_ZeroHist(self._spec)`), which is fixed in `__init__` — so under
  §6.2's fill-time axis declaration the zero/identity histogram would lack the `"variation"` axis
  the evaluator's output carries, and `_add_groups`' `+` would fail or mis-combine. Binding: the
  slot spec is the spec baked into that fill node's params. **A sibling slot maps to ONE fill
  node, so "that fill node" is unambiguous there; for an AXIS-MODE slot, which gathers `1 + |S|`
  fill nodes, the slot spec is that of ANY of the gathered nodes and an implementation MAY assert
  they agree** — §6.2(i)'s cross-fill agreement rule forces one inferred label set per axis-mode
  histogram, hence one variation axis, hence one spec; stating it spares the reader the
  derivation, since `_GroupZero` consumes the spec per slot.
  (d) **Ambient-weight application (the §2.6 completion of register-then-forget).** `fill` reads
  its input Arrays' **context handle** (§2.3e — a Python-object attribute on the frontend wrapper,
  outside node identity; NOT `Provenance`, which is source-location only, and NOT
  `Session._provenance`/`sourcemap()`) and **auto-applies that context's ambient weight** (§2.6c
  lineage rule — contexts are immutable, so *which context* fully determines *which
  registrations*): the fill's label set is the §2.4 union of value-borne labels, ambient-weight
  labels, explicit `weight=[...]` factor labels **and `sample=`-borne labels** (this section's own
  fold order folds `sample=` LAST and §6.1b's `S` counts it as a SIBLING-forcing source; a fill
  whose only variation is a `Varied` `sample=` is therefore varied and lowers a sibling, which is
  what m50's sample-only-label anchor freezes) — **computed on the inputs AFTER the lineage step
  below (unification + re-indexing/projection), not before it**, so a value reached across a
  universe/nominal PROJECTION link (kind (3)) contributes NO labels, having been projected to one
  label's unvaried member. Kinds (1) and (2) are label-preserving, so the order is immaterial
  there; for kind (3) the order changes the answer: on m48's own anchored fixture
  `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` the unified context is `graphed.nominal(sel)`
  — whose ambient weight is that label's member and whose `graphed.selection` is an unvaried
  `Array` (§2.2) — so the ancestor value is the ONLY label source, and the two orders give a
  labelled result with per-universe-identical content versus a wholly unvaried one. Under this
  rule that fill is UNVARIED and §6.1a's bare-`hist` shape applies; m48's anchor says so, which is
  also its discriminator against a "labels kept, contents identical" implementation. So a plain
  Jet-pT fill yields the jes/jer universes AND the pileup/PDF universes with zero per-fill
  bookkeeping (the owner's simultaneity requirement). **The union's ORDER is bound here too**,
  because §2.4 binds only a BINARY combination while this is three-way (and a fill may carry
  several varied axis values): the fill folds LEFT in a fixed operand order — **axis values in
  argument order, then the ambient weight, then explicit `weight=[...]` factors in list order** —
  each fold applying §2.4. **`sample=` folds LAST, after the explicit factors** (§2.3d binds
  "`Histogram.fill` accepts `Varied`"; today's `fill` type-checks `args` and `weights` but appends
  `sample` to the same `inputs` list with NO check, so an undisposed `Varied` sample falls through
  into `record_external` and dies on `.node_id`, the §2.3b unchecked-fall-through shape). Without
  a bound order two conforming implementations produce different label orders for one program: a
  determinism-gate difference (§3.2) and a different `_GroupReduce` layout (§6.1c).
  `weight=[...]` *adds* factors; `unweighted=True` opts out (counts histograms). **What
  `unweighted=True` suppresses, and its interaction with an explicit `weight=[…]`, is bound here**
  (today's signature is `fill(self, *args, weight=None, sample=None, threads=None)`, with no such
  parameter): it suppresses the AMBIENT weight **and** any explicit `weight=[…]` — a counts
  histogram carries no weight at all — and supplying both `unweighted=True` and a non-`None`
  `weight=` in ONE call is a **record-time error naming both**, the §2.5 validation-over-convention
  shape (silently letting one win is the confidently-wrong class). **The consequence is stated,
  not hidden**: "suppress the AMBIENT weight but apply my own factor" is therefore NOT expressible
  from a contexted program in v1 — every fill from a contexted value applies that context's
  ambient weight (this section), reading through `graphed.nominal`/`graphed.universe` still yields
  a context carrying it (§2.2), and the only opt-out also kills the explicit factor; only an
  all-loose fill escapes. Parked in §11 (the v2 answer is a context-level detach or a narrower
  `unweighted=` that suppresses the AMBIENT factor only). **Its effect on the fill's LABEL SET is
  bound here too**: a SUPPRESSED weight contributes NO labels — the label set above is computed
  over the factors the fill ACTUALLY APPLIES — so a contexted `unweighted=True` fill whose only
  variation source is the ambient registry is UNVARIED and returns a BARE `hist` (§6.1a), not a
  `{label: hist}` mapping of per-universe-identical counts. m48's anchor ("counts equal to an
  unweighted eager reference") is worded over the bare-`hist` shape, which is also its
  discriminator against the labels-kept reading.
  Inputs whose contexts sit on one ancestry chain unify to the **most-derived** context, **and
  every ancestor-context VALUE is re-indexed to the unified context across the intervening lineage
  links, label-aligned per §2.4**, stated PER LINK KIND (not every link carries a mask: §2.2 binds
  `graphed.universe`/`graphed.nominal` to return a CHILD context, and §2.6b binds `graphed.vary`
  to return one, and neither link carries a mask — on the cited example
  `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` the unified context is the child, the ancestor
  value carries per-label row sets (§2.6c), and no mask relates them). The three link kinds:
  **(1) mask-derivation link** (`ctx[mask]`, §2.6c) — re-index the ancestor value by THAT mask,
  label-aligned per §2.4 (each label's member by that label's mask, nominal's by nominal's);
  **(2) `graphed.vary` link** (§2.6b) — IDENTITY: the row space is unchanged, only registrations
  differ;
  **(3) universe/nominal projection link** (§2.2) — PROJECT each ancestor `Varied` value to that
  label's member (falling back to its `"nominal"` member per §2.4), yielding an unvaried value in
  the ancestor's row space, then continue with the links below it. Links compose in lineage order,
  parent-to-child. Unification alone is not enough, because §2.6c re-indexes the ambient weight to
  the derived row count, so `h.fill(events.MET.pt, sel.MET.pt)` would otherwise apply `sel`'s
  weight (row count = |sel|) against a value read at `events`' row count — a length mismatch whose
  only symptom is the execution-time refusal below, whose message is about the wrong thing.
  Re-indexing is the same operation §2.6c already binds for the ambient registry, applied to the
  values.
  **THE SURFACE THAT MAKES THIS IMPLEMENTABLE ACROSS THE PACKAGE BOUNDARY IS BOUND HERE, AND IT IS
  AN m48 IMPLEMENTATION TARGET IN `graphed`.** `Histogram.fill` lives in `graphed-histogram`, a
  DIFFERENT distribution, and §2.3e already fixed exactly this class once for the handle itself
  ("the slot alone is not reachable across a package boundary" — hence `graphed.context_of`). The
  LINEAGE RELATION between two handles and the intervening masks are NOT fixed by that: §9.1's m48
  surface is `labels`/`universe`/`nominal`/`weight`/`context_of`/the per-label fill-node
  accessor/`unpack`, none of which relates two handles or yields a derivation mask, and
  `graphed.selection(ctx)` — the only bound route to one — is m51. Without a bound surface, m48's
  own `graphed-histogram` anchors (§6.1d's link-kind-(1) ancestor-VALUE re-indexing and the
  projected-VALUE half of the universe/nominal clause, §10) would be satisfiable only by reaching
  into `graphed`'s private context object — the very thing `context_of` exists to prevent.
  Binding, both READ-ONLY, exact spellings pinned at m48 freeze, listed in §9.1:
  **(A) `graphed.unify_contexts(*handles)`-shaped** — returns the most-derived handle when the
  non-`None` arguments lie on ONE ancestry chain (`None` when all are context-free; context-free
  arguments are ignored, the adopt rule below), and raises the §2.3e divergence error naming both
  contexts otherwise;
  **(B) `graphed.reindex_to(value, ctx)`-shaped** — returns `value` re-expressed in `ctx`'s row
  space by composing link kinds (1)-(3) in lineage order, label-aligned per §2.4; identity when
  `value` already carries `ctx`'s handle or carries none; raising when `value`'s handle is neither
  `ctx`'s nor an ancestor of it (the §2.1(b) direction rule).
  With those two, the fill's entire lineage step is `unify_contexts` over its inputs'
  `context_of`s followed by `reindex_to` per input, and `graphed-histogram` imports nothing
  private. §2.3d dispositions: `reindex_to` **broadcasts** — the result's labels are obtained by
  composing the links in LINEAGE ORDER (a mask-derivation link unions that mask's labels per §2.4,
  a `vary` link is the identity, a universe/nominal projection link RESETS the label set to
  empty): across a path containing a kind-(3) link the result is that label's unvaried member and
  carries NO labels, per kind (3)'s own clause above and this section's ordering rule, on which
  m48's BARE-`hist` `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` anchor depends; m48's
  lineage-seam anchor is split per link kind (§2.3d). **The ORDERING half is knowingly left
  UNANCHORED** (the plan's convention for such rules — §2.2's term-(c) vary-link half, §6.4e's
  no-private-import rule, §7.2's "MUST NOT compile a second time" — marked so a reviewer does not
  read it as a coverage gap): the sequential rule and an order-insensitive set expression agree on
  every ONE-link path and on the natural two-link path (mask-then-projection: both empty), and
  diverge only where a MASK link sits BELOW a PROJECTION link (a root value re-indexed to
  `graphed.nominal(sel)[mask2]`), which no m48–m51 anchor builds — m48's lineage-seam anchor is
  split per SINGLE kind and its fill fixtures cross one link each. A test-author who wants it
  anchored can add the two-link, both-per-event value
  `h.fill(events.MET.pt, graphed.nominal(sel)[mask2].MET.pt)` to an existing m48 fixture.
  `unify_contexts` takes context handles rather than `Array`s, so — like `evaluate_ir` (§2.3d) —
  it is outside the `Array`-consuming surface and carries NO disposition. m48 anchors them where
  each is observable: `graphed`'s half asserts (A)'s most-derived answer plus its divergence
  refusal and (B)'s identity and wrong-direction refusals, while the VALUE-level re-indexing stays
  in the fill-shaped `graphed-histogram` anchors that consume it.
  **Both worked examples in this paragraph use SAME-GRANULARITY axis values, and that is
  deliberate**: the evaluator flattens each AXIS input INDEPENDENTLY and hands them to
  `boost_histogram`, which requires equal lengths across axes (bh 1.8.0 raises
  `ValueError: spans must have compatible lengths`). Re-indexing fixes an ancestor value's row
  COUNT, not its per-object STRUCTURE, and the broadcast seam bound below is scoped to WEIGHT
  factors — nothing broadcasts one axis value against another, and mixed-granularity multi-axis
  fills are NOT scoped in m48–m51. A per-event and a per-object value therefore never share one
  fill's axis list; the link-kind mechanisms need no such program.
  Contexts on **divergent branches are a hard error** naming both. **The fill raises it itself**:
  §2.3e's op-level rule is early detection, but the fill is a combining point no op precedes — it
  is the first place independent axis/weight/sample handles meet (they are collected into one
  `inputs` list recording one node) — so the fill runs the same most-derived unification and
  divergence check across all axis values, all explicit weight factors, **`sample=`** and the
  winning context's ambient weight (this section makes `sample=` a first-class labelled input,
  folded LAST and counted in `S` (§6.1b), and m48 freezes a four-way fold anchor including a
  varied `sample=`; `fill` type-checks `args` and `weights` and appends `sample` to the same
  `inputs` list with no check at all, so a `sample=` read through a divergent context is the one
  input nothing upstream catches — it dies at execution with a length message about the wrong
  thing, or silently samples the wrong universe's rows when the counts coincide, the §2.5
  confidently-wrong class. An ancestor-context `sample=` is re-indexed like any other ancestor
  VALUE; the broadcast seam stays scoped to weight factors, deliberately).
  Context-free (loose) inputs alongside contexted ones adopt the unified context **for LABEL
  ALIGNMENT only; their row space is NOT adjusted** (the re-indexing bound above applies to
  ancestor-CONTEXT values, using the intervening derivation masks; a loose value carries no
  handle, so no intervening mask is known and no re-indexing is possible, yet it may sit in the
  root row space while the unified context's ambient weight is at `|sel|` rows). When the
  execution-time length refusal below is traceable to a loose VALUE rather than a weight factor,
  its message names that value — not "the offending factor" and not "pass the value unflattened",
  both of which are the wrong diagnosis there. An all-loose fill is unweighted (the primitive
  path, still supported).
  **Every weight factor the fill applies — the ambient one AND explicit `weight=[...]` factors —
  is broadcast to the fill's value structure**, not just the ambient one (the recording TRIGGER is
  the one §6.3(2) states: a fill carrying a context handle OR any `Varied` input; a fill with
  neither records as today): the evaluator flattens each input independently and multiplies
  factors elementwise *after* flattening, so in a per-object fill an unbroadcast per-event
  explicit factor (`weight=[events.genWeight]`) flattens to `n_events` against `n_objects` — the
  mainline idiom of "ambient registrations plus one explicit factor" would length-mismatch.
  The mechanism is bound: **a per-object fill MUST pass its value UNFLATTENED**
  (`h.fill(sel.Jet.pt)`, the sketch — not `gak.flatten(...)`, which destroys the jagged structure
  there is nothing left to broadcast against), and the frontend then records a
  **broadcast-to-value-structure seam** (see below) relying on the evaluator's existing
  independent per-input flatten.
  **The broadcast is a neutral, backend-dispatched seam, NOT a named gak call**: the fill lives in
  `graphed-histogram`, whose runtime dependencies are `["graphed", "boost-histogram>=1.4",
  "numpy>=1.24"]` with awkward only in the dev extra, and `gak.broadcast_arrays` records the
  awkward-namespaced op `"ak.broadcast_arrays"` with no numpy-idiom equivalent. Naming it in a
  binding requirement would make the neutral seam awkward-only, the very factorization rule §2.1
  invokes. Binding: the seam is **`graphed.broadcast_like(value, factor) -> Array`** (spelling
  pinned at m48 freeze) — a neutral entry point owned by `graphed` proper and dispatched to the
  backend idiom, taking an ARBITRARY factor, **not a context method that can only reach the
  ambient weight** (a context-driven mechanism cannot reach a user-owned
  `weight=[events.genWeight]` factor, cannot be spelled inside `graphed-histogram` as a gak call,
  and does not exist at all in an all-loose fill, which §6.1d still supports). The fill applies it
  to the ambient weight and to every explicit factor alike. The awkward implementation records
  `ak.broadcast_arrays`; **the numpy idiom is a NO-OP — bound, not an either/or** (a no-op and a
  refusal are not interchangeable: one makes an all-numpy varied fill work, the other makes it
  fail). `graphed.numpy` is rectilinear and its shapes are numpy's own (no broadcast op exists
  there to inherit), so the seam returns the factor unchanged and a genuine shape mismatch
  surfaces as numpy's own error at execution — the same execution-time refusal shape bound below.
  The seam is owned by `graphed` proper; the awkward implementation by `graphed.awkward`;
  `graphed-histogram` gains no awkward dependency.
  **The already-flattened-value case is an EXECUTION-time refusal, not a record-time one**: a
  legitimately per-event value (`gak.firsts(...)`, `gak.num(...)`, `MET.pt`) and a flattened
  per-object value (`gak.flatten(sel.Jet.pt)`) have identical 1-D forms and differ only in runtime
  length, and the only record-time alternative is an unbounded cone-walk hunting a flatten node —
  which false-positives on `gak.flatten(x, axis=2)` (still jagged, still per-event). **The refusal
  is bound as a CONTRACT, not as a named class**: the broadcast seam is a recorded graph node
  UPSTREAM of the fill, so it executes first and dies there (awkward 2.12.0:
  `ak.broadcast_arrays` on two mismatched flat lengths raises `ValueError: cannot broadcast
  RegularArray of size 3 with RegularArray of size 7`, while the same call against a legitimately
  jagged value succeeds; a `FillEvaluator` raise is what you get in a world with NO broadcast
  seam). Binding: **at execution, a varied fill whose weight input cannot be broadcast to the axis
  values' structure fails with a `graphed` error naming the OFFENDING FACTOR** — the ambient
  weight or the explicit `weight=[…]` entry by position — **and, when the offender is a per-event
  factor against a per-object value, pointing at "pass the value unflattened"**. The seam's
  awkward implementation wraps its evaluator so awkward's `ValueError` is translated into that
  message; nothing binds WHICH class raises. Frozen-witnessed against a manually broadcast
  reference.
  This reproduces the corpus reference layout (independent per-variation histograms — UHI, no
  invented formats).
- **§6.2 (Scaling shape: the variation axis, m50 — weight labels only.)** An opt-in fill mode
  (**opt-in spelling pinned at m50 freeze** — every other new surface in this plan carries that
  clause) lands **weight-label** variations in ONE histogram with a **non-growth, pre-declared,
  sorted StrCategory `"variation"` axis** via an evaluator-side loop (extend/sibling
  `FillEvaluator`; labels ride the spec/params under the §1.2 carve-out; scalar-string broadcast
  and non-growth combine-safety are probe-verified — cba §histogram §3). **Shift labels always
  lower as sibling fill nodes** — their per-label axis columns have diverging lengths (§5.1
  cutflow), which the single-weight-loop evaluator shape cannot carry — **and in axis mode a shift
  sibling TARGETS the same pre-declared variation axis** (binding, not optional: §6.1c binds the
  axis-mode output to ONE slot gathering ALL its fill-node indices with a BARE histogram value,
  and m50 freezes "a mixed shift+weight program lands in ONE axis-mode histogram equal to its
  sibling-fill decomposition" — an implementer lowering shift labels as ordinary sibling slots
  would conform to a permissive reading and fail that frozen anchor), writing its label as the
  scalar category value of its own fill and contributing **no** per-label sibling slot: one
  histogram carrying both classes, filled from separate passes with a scalar label, is the field's
  actual layout in both eras of the confirmed exemplar (lit §ewkcoffea-confirmed), and
  scalar-string broadcast is probe-verified. The m50 equality anchor covers both the weight-label
  evaluator loop and a mixed shift+weight program landing in ONE axis-mode histogram equal to its
  sibling-fill decomposition. **Axis-mode fill-node arity is therefore `1 + |S|`** (only `W` — the
  labels borne ONLY by weight factors — collapses into the evaluator-side loop), which is why
  §6.1b's `1 + |S| + |W|` is scoped to sibling mode. **`S` and `W` carry §6.1b's lowering
  definitions here too**: a label borne by a `Varied` `sample=` is in `S` and lowers as a sibling
  writing its own scalar category value, since the evaluator's weight loop re-fills against a
  fixed sample column and cannot carry it.
  **The per-fill variation payload needs its own CARRIER, and it is bound here, because the
  obvious channel does not exist**: both halves above are per-FILL information — a shift sibling
  writes ITS label as the scalar category value of its own fill, and the weight loop needs ITS
  ordered weight-label subset — but an External evaluator is resolved solely by the payload's
  content hash, which today is `content_hash(self._spec)`; the plan-time registry merges every
  histogram's evaluators into ONE dict keyed the same way (`evaluators.update(h._evaluators)`),
  and `evaluate_ir` dispatches an external node by its descriptor's `content_hash`. §6.2(i)'s
  cross-fill agreement rule forces one inferred label set — hence ONE spec, hence ONE chash — per
  axis-mode histogram, so the `1 + |S|` fill nodes would all resolve to a single evaluator: last
  registration wins and every shift sibling writes the same category value. §1.2's §6.2 carve-out
  does not close it — it puts the BIN IDENTITIES in the spec, which is exactly the part identical
  across siblings. Binding: the per-fill variation payload (the scalar label for a shift sibling;
  the ordered weight-label tuple for the loop) is a **field of the fill's `FillEvaluator` AND
  enters the External payload's content hash** — `content_hash((spec, variation_payload))` in axis
  mode — so each axis-mode fill node resolves to its own evaluator. M29's identity discipline is
  preserved: the extra content exists only in axis mode, and a **SIBLING-mode fill — varied or not
  — hashes exactly as today (the MODE decides, §6.1a/§6.1c: an unvaried AXIS-MODE fill under (ii)
  still declares the 1-bin `{"nominal"}` variation axis, so its spec and its
  `content_hash((spec, variation_payload))` both differ from today's)**. Cross-referenced from
  §6.1c, whose per-slot spec is the fill node's, not the histogram object's, for the same class of
  reason.
  Non-growth is required: identical spec per partition keeps `+` combine safe and deterministic
  (PocketCoffea's deterministic pre-declared axis lesson; growth axes stay Phase 2 per the
  existing `_spec.py` refusal). **Who declares the bins is bound, because non-growth alone is a
  silent-drop hazard**: a non-growth `StrCategory` does NOT raise on an undeclared string — it has
  an overflow bin (`Traits(underflow=False, overflow=True, growth=False, …)`), so filling
  `['nominal','bogus','jes_up']` into `StrCategory(['nominal','jes_up','jes_down'])` gives
  `h.sum() == 2.0` while `h.sum(flow=True) == 3.0`: the label just vanishes — exactly the
  "hand-maintained name lists where a typo silently drops a systematic" failure mode §2.5 exists
  to delete. Binding: (i) **the FRONTEND declares the axis, at FILL time** — the point the spec
  enters node identity — from the §6.1d inferred label set (which IS known at fill time), so the
  spec is identical per partition by construction and combine-safety follows. **"At plan time" is
  unimplementable**: a `Histogram`'s spec is fixed in `__init__` (`self._spec = spec_of(self)`)
  and is baked into node identity at `fill` (`chash = content_hash(self._spec)`,
  `params={"spec": self._spec, …}`, evaluator registration), so adding a `"variation"` axis after
  the fill nodes exist would leave nodes, evaluators, `_GroupReduce`'s per-slot spec and
  `_GroupZero` disagreeing, and repairing it needs either re-recording every fill at plan time
  (unbound, large) or mutating interned node params (forbidden, §3.1/§1.2). Fill-time declaration
  needs no such thing: each fill node's params/evaluator already carry THEIR OWN spec.
  **Cross-fill agreement rule**: a second fill into the same axis-mode histogram whose inferred
  label set differs from the first's is a hard error naming the mismatch (the alternative is two
  incompatible specs in one histogram, uncombinable at `_add_groups`).
  **The MODE is a property of the HISTOGRAM, not of a single `fill()` call** (the opt-in spelling
  is plausibly a per-`fill` argument, and a mixed histogram is not benign: §6.1c keys an axis-mode
  output `(output, None)` and a sibling-mode output `(output, label)`, so a mixed histogram
  produces both key forms for ONE output and §6.1a/§6.2(i-bis) then give it two contradictory
  result shapes, while `_GroupZero` builds one `zero_of(spec)` per slot and `_add_groups` is a
  key-wise `+` over specs that differ by the variation axis — cross-axis addition raises, §6.1c):
  **the first fill fixes the mode and a later fill into the same histogram in the OTHER mode is a
  hard error naming both**, the same shape as the label-set mismatch above. Frozen alongside the
  m50 declaration anchor.
  **(i-bis) Axis-mode RESULT SHAPE** — §6.1a binds only the sibling shapes, so this is stated
  here: an axis-mode varied output returns a **bare `bh.Histogram` carrying the `"variation"`
  axis**, which is *indistinguishable by type* from an unvaried output. `graphed.labels` and
  `graphed.universe` therefore recognise it explicitly: `graphed.labels(h)` = the variation axis's
  bin set (NOT `["nominal"]`), `graphed.universe(h, label)` = **that label's slice along the
  variation axis**. **The ORDER `graphed.labels(h)` returns is §2.2's, not the axis's** (§2.2
  binds the verb to "nominal first, then insertion order" while §6.2(iii) binds the stored bin
  order LEXICOGRAPHIC, in which `"nominal"` is not first for any realistic family
  (`btag_down < btag_up < jes_down < nominal < pu_up`); §6.2's declaration anchor deliberately
  forbids using `graphed.labels(h)` as its oracle): `graphed.labels(h)` returns the axis's bin set
  RE-ORDERED to §2.2's rule — `"nominal"` first, then the remaining bins in axis (lexicographic)
  order — while the STORED bin order stays lexicographic and unchanged. The m50 (i-bis) anchor
  asserts that ordering. **The two MODES therefore do NOT agree on label ORDER for one program,
  and that is bound rather than left to be discovered**: sibling mode reports §6.1d's fold order
  (axis values in argument order, then ambient, then explicit factors, then `sample=`), axis mode
  reports nominal-first-then-lexicographic, and for any realistic family they differ — so m50's
  axis-vs-sibling equality anchor compares PER LABEL and MUST NOT use `graphed.labels` equality
  across the two modes as its oracle. Without this the §6.1a narrowing helper answers
  `["nominal"]` for a histogram that does contain `jes_up` and `KeyError`s on extracting it — a
  confidently wrong bookkeeping answer, the exact failure class §2.5 exists to delete. The helper
  is uniform over all THREE shapes (bare-unvaried, `{label: hist}`, bare-axis-mode).
  **The SPELLING of that slice is bound, because the obvious one does not work**: on
  boost_histogram **1.7.2 and 1.8.0**, `bh.axis.StrCategory([...], name="variation")` is a
  `TypeError` (no `name=` kwarg) and a string-keyed dict index raises `TypeError: list indices
  must be integers or slices, not str` — with or without `bh.loc`, and regardless of the axis's
  metadata. Named-axis dict access is a `hist`-package feature, and `hist.graphed` is out of m48's
  repo scope (§2.6 note (ii)) and out of m50's. The only working form is positional:
  `h[{axis_index: bh.loc(label)}]`. Binding: (1) the frontend **writes the axis name into
  `axis.__dict__["name"] = "variation"`** — the `hist` convention `graphed-histogram`'s spec codec
  already round-trips as axis metadata (`_spec.py`'s `_metadata_of` harvests `__dict__`,
  `_restore_metadata` writes it back), so the handle survives the spec/`zero_of` rebuild —
  verified on a TWO-axis histogram, the configuration axis mode actually produces (the variation
  axis is added alongside the user's ≥1 value axes): the name set on axis 1 round-trips
  `spec_of` → `zero_of` as `[a.__dict__.get("name") for a in z.axes] == [None, "variation"]`.
  **`h.axes.name` raises `AttributeError` unless EVERY axis carries a name** — `bh`'s
  `axes.__getattr__` maps the attribute over all axes — so the position lookup MUST read
  `axis.__dict__`, never `h.axes.name`, and an m50 test-author must not write `h.axes.name` as the
  oracle; (2) `graphed.labels`/`graphed.universe` resolve the axis POSITION from that name and
  slice by index. Nothing binds a literal subscript expression.
  **(3) No `boost_histogram` import in `graphed` proper** (`graphed.labels`/`graphed.universe` are
  `graphed` module functions and must be uniform over the bare-histogram shape, but `graphed`'s
  runtime dependencies are `["executing>=2.0", "cloudpickle"]` with boost-histogram only in the
  `dev` extra, so binding the `bh.loc` spelling inside `graphed` would import a package it does
  not depend on): detection is **duck-typed** (an object exposing `.axes`) and the slice uses a
  plain INTEGER bin index obtained from the axis itself — `axis.__dict__["name"]` to find the
  position, then `axis.index(label)`. Measured equivalent to the `bh.loc` form
  (`h[{1: ax.index("jes_up")}]` and `h[{1: bh.loc("jes_up")}]` give equal `values()`), and the m50
  anchor's oracle is a manually sliced reference, so nothing downstream depends on `bh.loc`.
  **The no-import rule itself is knowingly left UNANCHORED** (the plan's convention for a binding
  rule no frozen test discriminates — §6.1d's reindex ORDERING half, §6.4e's no-private-import
  rule, §7.2's "MUST NOT compile a second time", §1.1's `"1e1000000000"` — marked so a reviewer
  does not read it as a coverage gap): boost-histogram is in `graphed`'s `dev` extra, so an
  implementation importing it inside `graphed.labels` stays green on every behavioural gate. An
  m50 implementation MAY discharge it with the same one-line static assertion §6.4e offers — the
  module's source contains no `boost_histogram` import — in `tests/extra`.
  (ii) **A user-declared `"variation"` axis is NOT supported in v1.** The frontend declares it,
  always, from the inferred label set, so a label cannot be undeclared and the declared bin set IS
  the inferred set by construction. This is not merely a scoping preference: a user-declared axis
  is **unfillable today** — `Histogram.fill` requires one array per axis
  (`if len(args) != len(self.axes): raise TypeError(...)`), so a histogram constructed with a
  variation `StrCategory` rejects the user's N-array fill outright, and supporting it needs an
  arity carve-out this plan does not scope. **The residual silent-drop hazard the measurement
  above names is still gated**, by the frontend-side invariant instead of a user-facing error: the
  declared bin set equals the inferred label set exactly. `h.sum(flow=True) == h.sum()` witnesses
  only the UNDER-declaration half (a label with no bin lands in the overflow) — **an
  OVER-declaration is invisible to it** (declaring `['nominal','jes_up','jes_down','stale']` and
  filling the three real labels gives `sum == sum(flow=True) == 3.0`), so the closing half is an
  equality against a literally spelled expected label list, never one read back from the
  histogram. User-declared axes are parked in §11. (iii) The frontend, not the user, imposes the
  sort, so "sorted" and "pre-declared" cannot conflict. M29's identity discipline binds: new
  params/spec content only when the feature is used. The sorted bin order is **lexicographic over
  label strings and MUST NOT be read numerically**: determinism and combine-safety are unaffected
  by numeric-tag labels — sorting is a total order over arbitrary strings, every partition still
  declares an identical spec — but `murf_10` sorts before `murf_2`; positional/plot ordering for
  numeric families comes from §9.1's parsed-value introspection, never from bin index.
- **§6.3** Data / no-variation paths are unchanged, gated by both in-tree golden patterns: a
  **committed golden GIR blob** for an unvaried fill graph (the `core/m40/test_join_serialize.py`
  pattern) plus a **params KEY-SET equality**, not a key-absence placeholder (m48 in sibling mode
  adds NO params key by design — §1.2 keeps labels out of params — so a key-absence assertion has
  no key to spell and any invented name passes tautologically; the M29 precedent
  `assert "n_weights" not in node["params"]`
  (`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py`) works only because M29 had a
  KNOWN new key): the unvaried single-weight fill node's `set(node["params"])` equals a LITERALLY
  spelled expected set, today `{"spec", "n_axes", "weighted", "sampled"}` (`n_weights` is added
  only when `len(weights) > 1`). **Two halves are bound, or the gate is under-determined**:
  **(1)** the golden blob is captured from the **PRE-m48 revision** of that fill graph (captured
  after implementation it is a no-op tautology); **(2)** §6.1d's broadcast seam is **SCOPED, and
  the trigger is stated ONCE**: **the seam is recorded for every weight factor of a fill that
  carries a context handle OR any `Varied` input; a fill with NEITHER records byte-identically to
  today** — which is exactly this section's golden case. Read unscoped, §6.1d's "EVERY weight
  factor the fill applies … is broadcast" adds a node to an ordinary `h.fill(x, weight=[w])`,
  which makes this committed golden either red against a correct implementation (frozen ⇒ Test
  Dispute) or a tautology.
- **§6.4 (Variation-aware write-out — skim augmentation; collaborator-directed scope.)** Writing
  varied data (`to_parquet`, the uproot fork's `graphed_write`) is a first-class sink, not a
  Phase-2 parking: the surveyed frameworks each hit this wall and bolted around it (RDF Snapshot's
  per-event validity bitmask; mkShapesRDF re-implementing `Vary` for its Snapshot stage as
  suffixed columns + OR-of-cuts — Part I §2), and graphed's write path is measured greenfield
  (zero variation machinery, zero metadata use, one seam method per backend). Binding:
  (a) **Row rule — OR of selections, with the selection supplied EXPLICITLY.** When the written
  rows pass through a varied selection, the writer materializes the **superset**: rows passing ANY
  universe's selection, nominal included. The OR is recorded as ordinary graph ops over the
  per-label masks (`getitem`/`gak.mask` — no mask algebra exists in the IR and none is added).
  **The varied write API takes the mask(s), it does not infer them**:
  `graphed.awkward.to_parquet(record, select=…)`-shaped (exact spelling at m51 freeze — and it is
  the **awkward-idiom** verb: `to_parquet` is exported only from `graphed.awkward`
  (`python/graphed/awkward/io.py`), the numpy idiom having its own 1-D-capped implementation
  (`python/graphed/numpy/io.py`; the cap is inside `_WritePart.__call__`); §6.4f's "numpy backend
  EXEMPT" therefore means *the numpy-idiom function refuses*, not that a new neutral dispatcher is
  introduced), where `record` is PRE-selection (see the entry check below) and `select=` carries
  the `Varied` mask(s). **`select=` is per SELECTION LEVEL, not one row mask** — this is what
  makes §6.4d's object-level cutflow implementable at all: it accepts either a single `Varied` row
  mask, or a mapping of `Varied` masks — `{0: event_mask, ("Jet", 1): jet_mask, …}` — **one entry
  per (FIELD PATH, LEVEL) that varies**. **A level-0 entry is keyed by the bare depth `0` and
  applies to the record's ROW axis; every level-k ≥ 1 entry is FIELD-SCOPED and names the field
  path it applies to — EXCEPT where the level-k structure is the RECORD'S OWN, which takes the
  bare depth `k`.** The exception is not an ergonomic nicety: §6.4's own canonical skim writes the
  varying COLLECTION itself (`to_parquet(events.Jet, select=…)`, `to_parquet(E1.Jet, …)`, and the
  silent-corruption control `to_parquet(sel.Jet)`), for which `"Jet"` is not a field of the
  written record — it IS the record — so under unqualified field scoping the object-level mask of
  the plan's own headline program has NO legal spelling. **The discriminator is a record-time FORM
  property, so the grammar is decidable**: the single-collection record's form is
  `var * {pt: float64, eta: float64}` — one level-1 structure, the record's own, shared by every
  field — while the multi-collection record's is `{Jet: var * {…}, Muon: var * {…}}`, whose two
  level-1 structures are distinguishable only by field path. Binding: the bare depth `k ≥ 1` key
  is legal iff the record is itself jagged at depth `k` (its own offsets, all fields inside them);
  a record carrying two or more independently jagged fields at that depth REFUSES the bare key at
  the `to_parquet` call, naming the ambiguity and the field paths. A purely per-depth grammar is
  single-valued only for a record whose fields are all jagged with the SAME offsets (e.g.
  `events.Jet`) and is not single-valued for either shape this section puts in scope: a record
  mixing depths (§6.4b makes `graphed.weight(ctx)` a storable depth-0 field alongside a depth-1
  collection, and m51's round-trip anchor lists both) or a record carrying two jagged collections
  (Jet + Muon, a JES shift moving only Jet), which has two distinct depth-1 offset arrays — the
  writer would validate a jet mask against muon offsets or die with an offsets message about the
  wrong field. §6.4d's "widest common structure" governs where varied columns are STORED, not
  which field a level-k mask is validated and stored against, and does not close this. **What the
  writer does with them is exact**: it applies the **level-0 OR** to the stored ROWS — that IS the
  superset — and applies **no other supplied mask** to the stored buffers (that is the point of
  §6.4d's widest-common-structure rule: inner cuts are never applied, or the deltas lose their
  common shape); and it stores **one packed per-label validity mask per supplied ENTRY — stored
  against that entry's FIELD (against the record's own axis at that depth for a bare depth-`k`
  entry), level 0 against the row axis** (a per-LEVEL count is not single-valued once level-k ≥ 1
  entries are field-scoped). Without a per-level channel §6.4d is unsatisfiable in both
  directions: passing the post-object-cut record (`jets[jets.pt > 25]` under a JES shift) trips
  §6.4d's offsets refusal — which IS the object-migration case m51 requires as a positive control
  — while passing the pre-object-cut record leaves the writer with no knowledge of the per-jet cut
  and so unable to store inner masks or satisfy §6.4c. This is binding because the implicit form
  is not implementable under §3.1: if the user writes `to_parquet(sel.Jet)` with
  `sel = events[nominal_mask]`, producing the same fields on superset rows would require
  substituting the OR mask INSIDE an already-interned, immutable expression — a node rewrite the
  IR forbids, needing a second record-time expansion pass plus an undecidable "which node in the
  cone is *the* selection" rule (several selections; selection not outermost). With `select=`, the
  writer owns the masks, builds both the OR and the per-label masks, and no retargeting is needed.
  **The "record is pre-selection" precondition is a DECIDABLE entry check, not "by construction"**:
  a refusal worded over "a record expression that already embeds a `Varied` selection" is not
  mechanically decidable — a record varied because its VALUES vary (the expected input, §6.4b) and
  one varied because a varied MASK was applied are both just `Varied` containers of Arrays, §1.2
  keeps labels out of the IR, and telling them apart needs the same undecidable cone rule this
  paragraph rejects above; it also misses the case that actually corrupts data (a NON-varied
  embedded selection, `sel = events[nominal_mask]` then `select=varied_mask`, which applies the
  superset mask to already-selected rows, silently). Binding: **TWO predicates, not one** (a
  single offsets predicate cannot decide the embedded-selection case, which the m51 anchor names
  as its positive control: that predicate compares per-label members against nominal WITHIN the
  record, while the corruption is a record-vs-mask ROW-SPACE mismatch it never inspects. With
  `sel = events[nominal_mask]`, either `sel.Jet` is a plain `Array` and the predicate is vacuous,
  or every member was masked by the SAME non-varied mask and all offsets equal nominal's — it
  passes either way. The same hole swallows the chained-context case this section's own bridge
  creates, `graphed.selection(sel2)` for `sel2 = sel[mask2]`, which lives in `sel`'s row space
  while the canonical spelling writes `events.Jet` in root row space):
  **(1) MULTIPLICITY** — every per-label member's offsets equal nominal's at every level the
  writer will store (§6.4d's own rule, the multiplicity-changing refusal);
  **(2) ROW-SPACE AGREEMENT, SCOPED PER LEVEL** (a level-1 mask is per-OBJECT, jagged over the
  record's INNER dimension, not a mask over the record's row space, and it is not
  `graphed.selection(...)` of anything, because §9.1 defines that verb as the mask that derived a
  CONTEXT and contexts are event-level, §2.6c `events[mask]` — so one lineage test cannot apply to
  every supplied level): **level 0, split in two halves with different sites**.
  **(2a) LINEAGE, record-time** — the supplied mask must live in the record's own row space,
  decided by **CONTEXT-HANDLE EQUALITY** (the operative rule; see "HOW IT IS DECIDED" below, which
  is what an implementer and a test-author work from). The rationale form: the mask is the
  selection that derived some context from the context the record was read from, across exactly
  ONE mask-derivation link and any number of `graphed.vary` IDENTITY links. `vary` links must be
  admitted: §2.6's sketch rebinds `sel = graphed.vary(sel, "btag", …, is_weight=True, …)` after
  `sel = events[mask]`, so a skim written after ANY weight `vary` is written from a `vary`-derived
  context; `vary` links do not move the row space (§6.1d link kind (2)), so admitting them changes
  nothing the predicate is protecting, and m51's own bridge anchor
  (`select=graphed.selection(sel2)` for `sel2 = graphed.vary(sel, …)`) requires it. (A
  SELECTION-scoped weight is not storable at all — §6.4b's row-space precondition.) Links of the
  universe/nominal projection kind are NOT admitted:
  `select=graphed.selection(graphed.nominal(ctx))` on a record read from `ctx` satisfies a bare
  parent test while the returned mask lives in the GRANDparent's row space (§9.1); predicate (2b)
  catches it at execution, but the record-time check should decide it. The direction matters: in
  `to_parquet(events.Jet, select=graphed.selection(sel))` with `sel = events[mask]`, the record's
  own context is the ROOT `events`, and §9.1 defines `graphed.selection` of a root context as
  `None` — the m51 anchor's wording, "a record whose context is not the one the supplied `select=`
  mask DERIVES FROM is refused", is normative.
  **HOW IT IS DECIDED is expressed over the operand that exists — `graphed.context_of` of the
  supplied mask, not a search over the record's context's descendants.** A downward,
  parent→children search has no bound surface: §2.6b binds lineage as "Each returned context links
  to its parent" — an upward chain only — §9.1's `graphed.selection` runs context→mask, and §2.5's
  weak-reference registration is scoped to `Varied` containers, not contexts; nothing maps a mask
  back to the context it derived. Binding: **the supplied mask's own §2.3e context handle MUST BE
  the record's context handle, OR be reachable from it across `graphed.vary` IDENTITY LINKS ONLY,
  in either direction — `graphed.context_of(select_mask) is graphed.context_of(record)`, else one
  upward walk over the lineage §2.6b already retains that crosses `vary` links and NOTHING else**
  — a comparison of two values both operands already carry, plus at most a walk over identity
  links. Bare handle equality alone is not enough under §2.3e's own ORIGINATION rule — a read
  through `E2 = graphed.vary(E1, …)` carries `E2` while a read through `E1` carries `E1`,
  different handles and identical row spaces — so equality alone would refuse a legal
  configuration: `E2 = graphed.vary(E1, "pu", …, is_weight=True)`,
  `mask = gak.num(E2.Jet) >= 4`, `sel = E2[mask]`,
  `to_parquet(E1.Jet, select=graphed.selection(sel))`; that refusal protects nothing — a `vary`
  link does not move the row space (§6.1d link kind (2)). It is the same property (2a) is reaching
  for: a mask whose reads were performed through the record's context lives in the record's row
  space by §2.6c, which is exactly what the level-0 OR requires. The m51 controls: canonical skim
  `to_parquet(events.Jet, select=graphed.selection(sel))` with `sel = events[mask]` — the mask is
  recorded from reads through `events`, so both handles are `events` → ACCEPT; silent-corruption
  case (`sel = events[nominal_mask]`, record `sel.Jet` handle `sel`, `select=varied_mask` handle
  `events`) → REFUSE; chained-context case (`graphed.selection(sel2)` for `sel2 = sel[mask2]` has
  handle `sel`, against a root-row-space record) → REFUSE; universe/nominal case
  (`graphed.selection(graphed.nominal(sel))` has handle `events`, record read from `sel`) →
  REFUSE. Both ABSENT-operand cases below are preserved unchanged by it: a record with no handle
  short-circuits to (i), and a hand-built loose mask carries no handle (§2.3e Drop rule) so it can
  neither equal a contexted record's handle nor be reached from it across `vary` links → (ii)'s
  refusal. All five m51 controls decide identically under the `vary`-link admission (each refused
  pair is separated by a MASK-DERIVATION or PROJECTION link, never by `vary` alone). m51's
  re-recorded-equal-expression positive control holds, since a re-recorded mask carries the same
  handle by construction (two recordings of one expression intern to one node: `a = src * 2.0;
  b = src * 2.0` → `a.node_id == b.node_id`, `a is b` False). A record read across a
  MASK-DERIVATION or PROJECTION link from the mask's context — an ancestor or a sibling in that
  sense — is refused at the `to_parquet` call, naming both contexts.
  **Both operands can be ABSENT, and each case is bound** (§2.3e's Drop rule yields context-free
  results and a hand-built `Varied` mask need never have derived a context, so a purely
  lineage-stated predicate would have nothing to compare and no contexts to name for exactly the
  loose §2.1a write style this section calls supported):
  **(i) the RECORD carries no context handle** — (2a) is SKIPPED, and predicate (2b)'s
  per-partition row-count equality alone decides (it is the half that catches the corrupting case,
  and the loose style must stay reachable);
  **(ii) the record has a handle but the supplied mask carries NO context handle** (a hand-built
  loose mask, §2.3e's Drop rule) — REFUSED at the `to_parquet` call, naming the record's context
  and stating that the mask has no lineage to check against (mixing a contexted record with an
  unrelated loose mask is the ambiguous case, not a supported style). The trigger is "carries no
  handle", NOT "derived no context" — the two are different properties: a mask recorded entirely
  from reads performed THROUGH the record's own context (`select=(events.MET.pt > 50)` passed
  directly instead of via `graphed.selection(sel)`) carries handle `events` by §2.3e's ORIGINATION
  rule and derived no context, so handle equality holds and it is a legal in-row-space level-0
  mask: **a contexted mask carrying the RECORD'S OWN handle is ACCEPTED whether or not any context
  was ever derived from it.** That case is m51's fifth positive control — it is the only fixture
  that distinguishes the two readings. m51's entry-check anchor carries a loose-style write as an
  explicit POSITIVE control for (i).
  **(2b) ROW-COUNT EQUALITY between the record and that mask — EXECUTION-time, per partition**,
  raised by `_WritePart` before any buffer is stored, exactly like predicate (1).
  **(2c) LEVEL-0 DEPTH, record-time** — a mask supplied at level 0 MUST be FLAT over the record's
  row axis (depth 0); a JAGGED level-0 mask is refused at the `to_parquet` call, naming the level
  and the per-level channel. Neither (2a) nor (2b) constrains depth, and a per-OBJECT mask read
  through the record's own context (`select=(events.Jet.pt > 25)` instead of an event-level mask)
  passes BOTH: (2a) by §2.3e ORIGINATION — the same property that makes the fifth positive control
  `select=(events.MET.pt > 50)` legal — and (2b) because a jagged boolean over the record's own
  structure has the record's OUTER length. The writer would then apply it as the level-0 OR, and
  jagged-boolean indexing filters INNER elements while keeping every row, silently violating this
  section's superset-row contract and §6.4d's "inner cuts are never applied" rule with no error
  anywhere. m51 carries it as a negative control alongside (2a)'s.
  **(2c) GENERALIZES TO EVERY SUPPLIED LEVEL**: a mask supplied at level k MUST have depth k over
  the record's structure — over the NAMED FIELD for a field-scoped level-k ≥ 1 entry, and over the
  RECORD'S OWN structure at depth k for a BARE depth-`k` entry (the record's own depth-k structure
  is single-valued by the bare-key legality condition, so the check is well-defined) — and a depth
  mismatch at ANY supplied level is refused at the `to_parquet` call, naming the level. Depth is a
  FORM property known at record time (`_form_meta` in `python/graphed/array.py` reads
  `self._session.form(self)`, so depth is decidable at the call); the mirror case is identical — a
  FLAT mask supplied at level 1 (`select={0: evt, ("Jet", 1): evt}`, an easy mis-spelling) has no
  depth-1 offsets, so the structural check below has no operand and the likely implementation dies
  inside `_WritePart` per partition with an `AttributeError`/`IndexError` rather than a graphed
  error naming the level, at execution, on a record-time form property. m51's (2c) negative
  control carries the too-shallow level-1 mask alongside the jagged level-0 one.
  **Levels ≥ 1** — lineage is not the available handle, so the check is STRUCTURAL: each per-label
  member of the mask must carry **that NAMED FIELD's own offsets at that depth — or, for a BARE
  depth-`k` entry, the RECORD'S OWN offsets at that depth, the mask then being stored against that
  axis** ("the record's own offsets at that depth" is not single-valued for a mixed-depth or
  multi-collection record; the entry names the field precisely so this check and the packed
  per-label mask both have one operand), and the packed per-label mask is stored against that
  field. **The stored mask's ROW SPACE is bound here too, since §6.4c requires a reader to
  reproduce each universe's row set from the stored data alone**: every stored per-label mask —
  level 0 and every level k ≥ 1 — is stored on the **SUPERSET rows** (level-0-OR-restricted), so a
  reader applies it directly to the stored buffers; the level-≥1 structural predicate above runs
  against the record's offsets AS EVALUATED (pre-restriction, which is the operand `_WritePart`
  holds when it raises), and the restriction is then applied to mask and buffers alike. That is
  predicate (1)'s comparison at the same level, so it costs nothing extra, runs per partition, and
  shares (1)'s raiser and error shape.
  Each predicate has its own error message, and the m51 anchors name which predicate decides which
  positive control. **Where each runs is bound below** (predicate (2)'s level-0 LINEAGE half (2a)
  **and its level-0 DEPTH half (2c)** are record-time; predicate (1), predicate (2a)'s row-count
  twin (2b) and predicate (2)'s level-≥1 structural half are execution-time, per partition).
  **Writing from a context (§2.6 idiom).** In the owner-locked context idiom the user holds a
  derived context (`sel = events[mask]`), not the mask, and contexts expose no mask accessor
  (§2.2/§9.1 list `labels`/`universe`/`nominal`/`weight`/`variations` only) — so without a bridge
  the m51 sink would be reachable only from the loose §2.1a style, one milestone after §2.6 makes
  the context the primary idiom. Binding bridge: **`graphed.selection(ctx)`** returns the `Varied`
  mask that derived `ctx` from its parent (the §2.6b lineage already retains it; a root context
  returns `None`), so the skim spelling is
  `to_parquet(events.Jet, select=graphed.selection(sel))`. Frozen-anchored in m51.
  **Where the checks RUN.** Offsets are data. At the `to_parquet` call the frontend holds a
  recorded graph and typetracer forms, not per-label offsets, and the write is evaluated **per
  partition inside the worker**: `_WritePart.__call__` reads the partition, calls `evaluate_ir`,
  then writes one part (`python/graphed/awkward/io.py`; the per-partition task graph is built by
  `python/graphed/write.py`). Binding: predicate (2a)'s **level-0 lineage** half **and (2c)'s
  level-0 DEPTH half** (depth is a FORM property, known at record time) ARE record-time checks
  raised from the `to_parquet` call; predicate (1) (offsets), **predicate (2b)'s level-0 row-count
  equality** **and predicate (2)'s level-≥1 structural half** are **execution-time, per-partition
  checks raised by `_WritePart` BEFORE any buffer is stored**, surfacing through the executor's
  error path — the same treatment §6.1d already takes for its length check. m51's anchors are
  worded accordingly; do NOT freeze a record-time raise for any offsets- or row-count-shaped
  predicate, (2b) included.
  (b) **Column rule — augmentation.** The written record carries the user's fields evaluated in
  the **nominal** universe (on superset rows), PLUS appended per-label reconstruction data: for
  every stored field that **IS `Varied` — structurally, at record time** ("whose VALUE differs per
  label" reads data-dependently, and §6.4c computes the deltas inside `_WritePart` on the
  evaluated buffers, i.e. PER PARTITION, so the literal reading makes the augmented column set
  data-dependent: a partition where a label happens to agree with nominal everywhere would write
  fewer columns than its neighbour, giving parts with different schemas and different manifests
  inside ONE dataset, while m51 freezes the file layout; m51's own round-trip anchor settles the
  intent the other way — "a label structurally equal to nominal (all-zero delta)" IS written), a
  same-shaped delta column — **so the augmented column set is identical across partitions by
  construction**; and per-label selection masks (the varied cutflow) plus the nominal mask, so
  each universe's row set is recoverable. Weight-only labels contribute no kinematic deltas —
  their varied factors, when among the stored fields, augment like any other varied field
  (**reachable via `graphed.weight(ctx)`**, §9.1: under the owner-locked context idiom a factor
  handed to `graphed.vary(..., is_weight=True)` is otherwise absorbed into an immutable registry
  the user cannot name, so "when among the stored fields" would be unsatisfiable).
  **The ROW-SPACE precondition on that is bound here, because "when among the stored fields" is
  not free**: the written record is PRE-selection and its buffers are stored on the event-row
  SUPERSET (this section and §6.4a), while §2.6c gives a SELECTION-derived context per-label row
  sets and re-indexes its ambient registry by each label's own mask — so `graphed.weight(sel)` for
  `sel = events[mask]` has a nominal length of |sel_nominal| and per-label lengths that differ,
  and storing it would trip predicate (1) / §6.4d ("a stored varied field whose per-label offsets
  differ from nominal's is REFUSED") BY CONSTRUCTION, with a message about offsets rather than
  about the real fault. No re-indexing rule back onto the superset is bound, and none is
  expressible — a mask has no inverse. Binding: **a stored varied field MUST live in the record's
  own row space; `graphed.weight(ctx)` is storable exactly when `ctx` is reached from the record's
  context across `vary` IDENTITY links only (§6.1d link kind (2)) — no mask-derivation link — and
  a SELECTION-scoped weight is NOT storable in v1, refused at m51's entry check with a message
  naming the row-space mismatch, not an offsets mismatch.** (The selection-scoped weight remains
  fully supported for FILLS, §2.6c; only the skim sink refuses it.) m51's entry-check anchor
  carries the refusal and its round-trip anchor names the storable spelling. Appended names follow
  one bound convention (`__vary_{label}__{field}`-shaped; exact spelling pinned at m51 freeze).
  Labels are valid identifiers by construction (**§1.1 canonicalization, e-form** — a dotted
  spelling never reaches a label), so labels appear in on-disk names VERBATIM: the canonical
  on-disk shape is `__vary_murf_5em1__Jet_pt`. **The `{field}` half of that name is bound
  separately, because §1.1's discipline covers only the LABEL half** (the measured hazards below
  are properties of the WHOLE column name and a nested path (`Jet.pt`, `FatJet.subjet.pt`) puts a
  `.` straight back into it; §1.1 is explicit that its 32-character cap does not bound
  `__vary_{label}__{field}`): the field path is flattened with `_` per level, **and the resulting
  on-disk names are checked for COLLISION in BOTH directions — derived-vs-derived and
  derived-vs-stored: the derived names of all augmented columns MUST be pairwise distinct AND MUST
  NOT equal any stored field name; a collision is REFUSED at m51's entry check, naming both source
  fields** (under the bound `__vary_{label}__` prefix the derived name for `Jet.pt` is
  `__vary_L__Jet_pt`, which cannot equal a stored user field `Jet_pt` — the REAL collision class
  is both `Jet.pt` and a flat `Jet_pt` varying, each deriving to `__vary_L__Jet_pt`; a
  nested-field skim is LEGAL under this convention, not a refusal case). §6.4e's manifest remains
  the sole machine resolver either way: readers resolve labels and columns THROUGH it, never by
  parsing stored names, so the flattening is for human inspection and the collision refusal exists
  so the two never disagree. m51 freezes a nested-field skim round-trip and the collision refusal.
  The probe-measured hazards that forbade dotted names (`ak.from_parquet(columns=["murf_0.5"])`
  silently empty, pyarrow 25.0.0 / awkward 2.12.0; a dotted uproot 5.7.5 RNTuple field is
  reachable via `__getitem__` (exact lookup first) but `RField.array()` fails because `to_akform`
  splits the path on `.`; the TTree writer's own `.` nesting separator; ROOT TTreeFormula `.`/`-`
  operator meaning) are foreclosed at the §1.1 gate. Identifier-shaped names of this convention's
  form (e.g. `__vary_murf_0p5__Jet_pt`) round-trip byte-exact and readable in every measured path.
  (c) **Bit-exact reconstruction is REQUIRED — at every selection level SUPPLIED through
  `select=`.** Reading the file back and applying the deltas MUST reproduce every universe's
  post-selection values and row set bit-for-bit vs the in-memory varied run, at those levels.
  **The scoping is not a weakening, it is what the writer can promise**: §6.4a is explicit that
  the API takes the masks and does not infer them, storing one packed per-label validity mask per
  SUPPLIED entry, so a user who applies an object-level cut in memory but supplies only
  `{0: event_mask}` produces a file no reader can reconstruct at level 1 — through no fault of the
  implementation. Unqualified, the sink's headline contract would be unsatisfiable for a legal
  program while correct code met its intent. User-visible consequence: **a level not supplied is
  not recoverable, and §6.4e's manifest records which levels are stored** (m51's round-trip anchor
  supplies both levels). The default representation is therefore **exact by construction**:
  same-dtype XOR bit-delta vs nominal for value columns (zero wherever a label equals nominal —
  maximally compressible), `packbits` for masks stored as nominal + XOR-vs-nominal diffs.
  **The COMPUTATION SITE is bound, because the in-graph reading is measurably not expressible**:
  the extra marked outputs of §6.4f's shared `compile_ir` are the **per-label VALUES and per-label
  masks**, and the XOR bit-delta and `packbits` are computed inside `_WritePart.__call__` on the
  EVALUATED buffers (`ndarray.view(uintN)`), after `evaluate_ir` and before the write. A recorded
  XOR over the float columns that matter does not exist: `float32 ^ float32` raises
  `TypeError: ufunc 'bitwise_xor' not supported for the input types` for both `np.ndarray` and
  `ak.Array`, gak has no bit-view verb (no `view`/`packbits`/`frombuffer`; `values_astype` is a
  VALUE cast), while `a.view(np.uint32) ^ b.view(np.uint32)` works on evaluated buffers. §6.4f's
  "appended columns are extra marked outputs" therefore refers to the per-label values/masks, and
  its read-list widening must cover them. An in-IR bit-view verb is NOT scoped (§11). Measured
  basis (R0.11; float32/1M-value/zlib-6 probe): the suggested "1+delta" float ratio compresses
  best (2.88 MB vs 3.55 raw) but is **NOT bit-exact**; subtraction delta is bit-exact only
  data-dependently; XOR is exact by construction (3.28 MB); XOR-diff+packbits masks are ~4.7×
  smaller than raw booleans (169 KB vs 798 KB, 5 labels). Lossy ratio storage is a Phase-2 opt-in
  (§11); the representation is recorded per column in the manifest; sizes are measured on real
  skims in the m51 implementer report.
  (d) **Structure rule, with an explicit refusal.** Deltas require same-shaped buffers: varied
  columns are stored at the widest common structure (pre-object-cut values on the event-row
  superset), with per-label validity masks at every selection level that varies — event-level AND
  object-level (a JES shift moves jets across a per-jet pt cut, so per-label *inner* masks are
  part of the cutflow data, not an edge case). **The object-level half is only expressible because
  §6.4a's `select=` is per LEVEL** — the writer stores one packed per-label mask for each level
  the user supplies (`{0: event_mask, ("Jet", 1): jet_mask}`) and never applies them to the stored
  buffers; **a level-k ≥ 1 entry is FIELD-SCOPED (§6.4a) unless the level-k structure is the
  record's own, which takes the bare depth `k` (§6.4a — the single-collection skim
  `to_parquet(events.Jet, …)`, where the field-scoped rule has no operand), so a field shallower
  than a supplied level, or at that depth under a different field path, is unaffected by it — a
  depth-0 stored factor (`graphed.weight(c)`, §6.4b) coexists in one record with a depth-1
  `("Jet", 1)` entry**; nothing else in this plan gives the writer knowledge of an inner cut, and
  inferring it from the record expression is the undecidable rule §6.4a rejects. That holds for
  scale/smear shifts, which preserve multiplicity — but §2.1 does NOT guarantee it: §2.1's
  construction check is awkward form compatibility, a TYPE check (`var * float64` matches
  `var * float64` whatever the per-event counts), so a variation that legitimately changes
  multiplicity (shift-dependent cleaning, overlap removal, a matched collection) passes §2.1 and
  then has no representable XOR delta. **Binding refusal**: a stored varied field whose per-label
  offsets differ from nominal's is REFUSED with an error naming the label and the field. The
  supported v1 model is same-multiplicity variation plus per-label validity masks;
  multiplicity-changing stored variations are Phase 2 (§11). Frozen as an m51 negative anchor.
  (e) **Manifest — invent no formats.** A manifest (labels → appended columns → representation,
  **plus the selection LEVELS whose per-label masks are stored** — §6.4c scopes bit-exact
  reconstruction to the levels the user supplied through `select=`, so a reader must be able to
  tell which those were rather than discovering the gap as wrong physics) travels in existing
  metadata channels: parquet key-value file metadata (unused by graphed today — greenfield). **The
  writer swap is CONDITIONAL, not unconditional** — otherwise it contradicts §6.4g's byte-identity
  requirement: measured (awkward 2.12.0 / pyarrow 25.0.1), `ak.to_parquet(a, p)` and
  `pq.write_table(ak.to_arrow_table(a), p)` produce **different bytes** for every array probed,
  and the arrow path **drops awkward's own `awkward_array_metadata` KV entry** — which would break
  `ak.from_parquet` round-tripping. Both paths always keep `ARROW:schema`; `ak:parameters` appears
  only when the array carries awkward parameters (present for a record array, absent for a plain
  list-of-float or flat numeric array), so it is a property of the DATA, not of the writer, and a
  test freezing a literal KV set would be red for the wrong reason. `ak.to_parquet` has no
  metadata parameter (signature verified), so the swap genuinely is required for the manifest.
  Binding: an **unvaried write keeps `ak.to_parquet` untouched** (preserving the §6.4g golden); a
  **varied write** MUST reproduce awkward's own KV entries alongside the graphed manifest, with
  `ak.from_parquet` round-tripping the augmented file as a frozen m51 anchor.
  **The ROUTE is bound too, because the outcome is otherwise reachable only through another
  distribution's PRIVATE module**: the dropped key is defined ONCE, as
  `AWKWARD_INFO_KEY = b"awkward_array_metadata"` in `awkward/_connect/pyarrow/table_conv.py`, and
  written only by `convert_awkward_arrow_table_to_native` there; `ak.to_parquet` reaches it solely
  by importing that private helper, while `ak.to_arrow_table` never adds it. Binding: **the varied
  write MUST NOT import `awkward._connect.*`** (the §2.3e/§6.1d package-boundary rule, here
  against a package where `graphed` cannot add a seam), and its route is the PUBLIC composition —
  build the file awkward's own writer would (`ak.to_parquet` to the part path or an in-memory
  sink), then re-read the table and re-write it with the graphed manifest merged into the schema
  metadata (`Table.replace_schema_metadata` + `pq.write_table`), which is the same merge point
  `ak.to_parquet` itself uses for `attrs`. The second write is the accepted cost of the varied
  path; the unvaried path is untouched (§6.4g). A future revision MAY bind a cheaper route, but
  never one that imports awkward's private package. **The no-private-import half is knowingly left
  UNANCHORED, and rides code review plus the repo's integrity scan**: m51's manifest anchor
  asserts only the OUTCOME — that the augmented file round-trips through `ak.from_parquet`, i.e.
  that `awkward_array_metadata` survives — which an implementer who simply imports the private
  helper also satisfies, so no frozen test discriminates the rule. It stays binding for the
  package-boundary reason above, on the same footing as §7.2's "MUST NOT compile a second time"
  and §1.1's `"1e1000000000"`; an m51 implementation MAY discharge it with a one-line static
  assertion (the varied-write module's source contains no `awkward._connect` import) in
  `tests/extra`. The ROOT-side equivalent pinned at m51 freeze. The manifest maps each label to
  its stored column/branch names and per-column representation, **serialized with SORTED keys** (a
  manifest serialized in set/dict-iteration order would make the written bytes depend on
  `PYTHONHASHSEED`, the same hazard §8.2(i) names for the plan closure). **The selection-LEVELS
  entry's serialized SHAPE is bound here too, because §6.4a's key space is heterogeneous and has
  no JSON-native rendering** (a level-0 or record's-own entry is a bare depth `k`, a field-scoped
  entry is a `(field path, depth)` PAIR — §6.4a — and m51's manifest anchor asserts the entry's
  value against the levels the fixture supplied): the entry is a **list whose elements are either
  an integer depth or a two-element `[field_path, depth]` array**, `field_path` spelled as the
  `_`-flattened path §6.4b already binds for stored names. **The TOTAL ORDER is bound with it,
  because "sorted" names no computable predicate over a heterogeneous element space**: order by
  the key `(depth, field_path or "")` — bare-depth entries before field-scoped entries of the same
  depth, field-scoped entries by flattened field path — so the list is a pure function of the
  supplied `select=` keys and the manifest bytes stay `PYTHONHASHSEED`-independent. `sorted()`
  over the raw mixed elements is a `TypeError` (`sorted([0, ["Jet", 1]])`), and
  `json.dumps(…, sort_keys=True)` sorts mapping keys only, never a list's element order — so
  neither the house serializer (`python/graphed/preserve/manifest.py`) nor a bare `sorted()`
  supplies this order. Exact key spelling pinned at m51 freeze. Readers resolve labels **through
  the manifest**, never by parsing stored names (names embed labels for human inspection, not as
  the machine channel). A frontend reader (**`graphed.awkward.read_varied(path)`-shaped**;
  spelling at freeze) reconstructs `{label: array}` per universe from the manifest — the
  round-trip is the m51 frozen anchor. **The reader is awkward-idiom, symmetric with the writer**
  (§6.4a binds the writer awkward-idiom on the factorization rule; `graphed`'s runtime
  dependencies are `["executing>=2.0", "cloudpickle"]` with awkward and pyarrow only in extras,
  and both parquet entry points already live in `graphed.awkward`, so a neutral
  `graphed.read_varied` returning awkward arrays would put pyarrow + awkward behind the neutral
  namespace). The ROOT-side equivalent lives in the uproot fork.
  (f) **Seam binding (write-seam evidence).** Parquet: appended columns are extra marked outputs
  of the SAME `compile_ir` (variadic by design), so the M4 optimizer shares the pass with the
  primary expression — appended between the evaluate and write steps of `_WritePart.__call__`.
  **The marked outputs are the per-label VALUES and masks, not the encoded deltas** (§6.4c — the
  XOR/`packbits` encoding is not expressible as a recorded op and runs in `_WritePart` on the
  evaluated buffers), and the read-list widening below must cover them. **That call site unpacks a
  SINGLE output today** (`(out,) = evaluate_ir(...)`), so widening it to the augmented output list
  is part of this target, not incidental.
  **The widened unpack resolves each augmented output BY NODE ID per §7.2, never positionally**
  (§7.2 states the general rule; this paragraph is what an m51 implementer works from):
  `mark_output` de-dups and `evaluate_ir` returns one value per DISTINCT output, so on m51's own
  anchored case — "a label structurally equal to nominal (all-zero delta)" — a positional unpack
  silently misassigns every label after the collapsed one, and an all-zero delta is exactly the
  content one expects there. A shared value is REPLICATED into every label that maps to it, and
  the **`record node id → output position` table is a FIELD of `_WritePart`** — driver-derived and
  shipped in the closure, since `_WritePart` is a frozen dataclass evaluated per partition in the
  worker and cannot recompute it there. Whether §7.2's optimizer-merge REFUSAL also guards the
  write path is settled here: **it does** — the varied write is a varied unpack path in §7.2's
  sense and a μR/μF label spelled `w * 1.0` is §1.1-legal, so at m51 the same
  distinct-outputs-vs-distinct-marked-ids shortfall check runs in the varied `to_parquet` path
  (record-time, at the call) with §7.2's message and workaround; the read list widens at
  `_evaluation_columns` (`awkward/io.py`) or projection starves the task. ROOT: `graphed_write`
  today copies branches verbatim with NO IR evaluation (`_graphed_write.py`; zero
  `compile_ir`/`evaluate_ir` use) — adding evaluation is the **larger half** of m51 and is scoped
  there explicitly. numpy backend: EXEMPT — it hard-caps output at one 1-D column; the numpy-idiom
  write function refuses a varied write with a clear error naming the awkward backend. **The
  TRIGGER and the ENTRY POINT are pinned, because neither is decidable from that sentence alone**:
  the function is `graphed.numpy.io.to_parquet` (reachable only through the module —
  `hasattr(graphed.numpy, "to_parquet")` is `False` and it is absent from
  `graphed.numpy.__all__`), and the refusal triggers on a **`Varied` first positional**, raised as
  a graphed error naming the awkward backend instead of §2.2's reserved-name `AttributeError`. It
  gains **NO `select=` keyword** (the signature is `to_parquet(array, destination, *,
  steps_per_file, compute, executor, prefix, column)`), so a `select=` call stays an ordinary
  `TypeError` and no m51 anchor may freeze a graphed error for it; exact message spelling pinned
  at m51 freeze. **And the numpy idiom exposes no `read_varied` counterpart** (symmetry with
  §6.4e's awkward-idiom reader).
  (g) **Single pass; no cost when unused.** The augmented write stays one plan / one read pass
  (the §5.2b witness applies to the write run); an unvaried write is byte-identical to today's
  output, and carries no manifest. **The byte-identity is frozen as a SAME-PROCESS comparison,
  never as a committed `.parquet` fixture**: §6.3's golden pattern works for GIR because that
  format is graphed's own and deterministic by construction (`core/m40/test_join_serialize.py`
  compares a literal `b"GIR1\x03…"`), but a parquet footer embeds its **writer version** — an
  `ak.to_parquet` file carries the ASCII string `parquet-cpp-arrow version <arrow version>`,
  readable as `ParquetFile(path).metadata.created_by` — so a committed parquet blob turns red on
  any pyarrow bump and can differ across §A.5 matrix legs while the behaviour is correct, which
  R0.10a forbids. The available invariant is an in-run one, and it is what m51 freezes: write the
  same array through the feature-present path and through `ak.to_parquet` directly in ONE process
  (byte-identical for repeat writes) and assert byte equality plus the absence of the
  manifest KV key. Params-absence (the §6.3 pattern) still applies to the graph side.

## §7 Execution, results, checkpoint

- **§7.1** One Session, one IR, one plan for nominal + all variations; executors are untouched
  (`R` opaque through `Plan`/tree-reduce/engines — cba §exec-checkpoint §1,§4). **No per-variation
  RE-EXECUTION of the graph or the plan may be introduced anywhere.** §6.2's m50 mechanism — an
  evaluator-side weight loop inside ONE fill node — is not a re-execution and is not such a loop.
  §5.2b's single-read witness is the mechanism witness for this requirement.
- **§7.2** The frontend owns `(output, label) → **node id**` — NOT `→ position` — and derives
  `node id → position` as **the index of that record id's FIRST OCCURRENCE in the frontend's OWN
  ordered list of marked record ids** (the list it passes to `compile_ir`), so **many labels MAY
  resolve to one position and the unpacker replicates that value**.
  **The operand is bound to that list** — not to the compiled output list, which cannot be joined
  to it: the compiled artifact's `outputs()` are POST-REDUCTION ids, and the record→reduced map
  does not exist until m49's §8.2(i) accessor. `compile_ir` never marks the RECORD store — it
  passes the ids as `reduce(outputs=ids)`/`serialize(outputs=ids)` — and `GraphStore::mark_output`
  de-duplicates on the REDUCED store, which `from_reduced` marks; `evaluate_ir` returns one value
  per reduced output, in first-occurrence order over the DISTINCT record ids. Compiling two
  structurally identical outputs therefore returns ONE value. The frontend's own ordered list is
  the exact operand for every program m48 admits: the two orders can only disagree when the
  OPTIMIZER merges distinct record ids, which is precisely what the m48 shortfall guard below
  refuses. A positional `(output, label) → position` map would walk off the end of
  `_GroupReduce`'s `fills` list or mis-assign labels on exactly the case §1.2 mandates and
  §5.2a/m51 put in scope (a label structurally equal to nominal). The frontend unpacks into the
  §6.1 named mapping through §6.1a's bound unpack verb.
  **THE SEAM THAT MAKES THE COMPILED ARTIFACT REACHABLE IS BOUND HERE, AND IT IS AN m48
  IMPLEMENTATION TARGET**, because TWO binding requirements need that artifact at a site that
  does not have it. (§6.1c's index-based `layout` is not one of them: it needs only the frontend's
  OWN ordered marked-id list above, which `plan()` already holds as `fill_nodes` immediately
  before it builds `layout`, so it never needs the compiled artifact.) The two: this section's own
  m48 optimizer-merge refusal must compare the number of DISTINCT compiled outputs against the
  number of distinct marked record ids inside the group-plan builder; and m49's §8.2(i)
  `variation_labels` is a FIELD of `_PartitionReduce` keyed on POST-REDUCTION ids from the same
  compile. `aggregate_plan(*outputs, reduce, combine, empty, externals, backend, steps_per_file,
  partitions)` compiles internally (`compiled = compile_ir(session, *outputs)`) and immediately
  constructs the frozen dataclass `_PartitionReduce` from pre-built closures, and
  `graphed_histogram.plan()` builds `layout` BEFORE its `aggregate_plan` call. Binding:
  **`aggregate_plan` gains ONE pinned seam (exact spelling pinned at m48 freeze) that (α) lets the
  caller see the COMPILED ARTIFACT — the `CompiledGraph` itself, not merely a list of output ids —
  before the worker closure is CONSTRUCTED, and (β) carries per-plan variation metadata onto that
  closure as an additive field (m49's `variation_labels`, §8.2(i)).**
  **(β) IS THE HOOK'S RETURN CHANNEL, NOT A CALL-TIME PARAMETER**, and the direction is binding
  because as an input parameter (β) is unsatisfiable: §8.2(i) keys `variation_labels` on
  POST-REDUCTION ids obtained through the m49 accessor "for the reduction that produced a given
  compiled artifact", and that artifact is produced INSIDE the call —
  `compiled = compile_ir(session, *outputs)` immediately precedes the `_PartitionReduce`
  construction — while this section forbids compiling twice (below) and §8.2(i) declares the field
  an IMMUTABLE sorted tuple, so no caller-side value and no mutable holder filled by a see-only
  callback can carry it. Binding: **the hook is called with the `CompiledGraph` before the worker
  closure is constructed, and its RETURN VALUE (the per-plan variation metadata, or `None`) is
  attached to the shipped closure as the additive §8.2(i) field.** m48's (α) anchor asserts that a
  returned payload reaches the closure (with a dummy value), so an m48 implementer cannot freeze a
  see-only spelling m49 is then blocked by — the same trap this paragraph closes on the artifact
  axis.
  **The field's TYPE is bound ONCE, in §8.2(i), as `tuple[…, …] | None` defaulting to `None`, and
  the m48 dummy is a well-typed NON-DEFAULT value of it — the empty tuple `()`.** The dummy must
  type-check against the field's DECLARED type under R0.4a's `mypy --strict` (R0.4a names src-only
  mypy configs as a pending cross-cutting cleanup): a str/sentinel dummy is a type error at the
  hook's return, and m49's bindingly declared type must not red the frozen test. `()` is the
  smallest well-typed value, is distinguishable from the `None` default, and keeps the (α) anchor
  discriminating without inventing a type. **The field therefore EXISTS from m48**, which is where
  its one-time journal churn lands — see §7.3.
  **The seam is ADDITIVE and the artifact is the `CompiledGraph`.**
  *Additive*: the contracts of the existing `reduce`/`combine`/`empty` parameters are UNCHANGED —
  they are plain callables and frozen m5 passes them that way
  (`tests/frozen/frontend/m5/test_aggregate_plan.py`), and a factory over the compiled output ids
  cannot be duck-typed apart from a plain reducer, so any non-additive spelling is implementable
  only by breaking a frozen test (§B.6) or filing a Test Dispute. The seam is a NEW
  optional keyword/hook — `on_compiled(compiled)`-shaped — beside the existing parameters, the
  same additivity discipline §8.1, §8.2(i) and §9.2 already take on shipped surfaces.
  *`CompiledGraph`, not ids*: this section's own merge refusal needs only the COUNT of distinct
  compiled outputs, which `GraphStore.deserialize(compiled.ir).outputs()` gives (`CompiledGraph`'s
  fields are `ir`/`source_names` and its only method is `evaluate`), but the seam's OTHER named
  consumer does not — m49's `variation_labels` keys on `(reduced_node_id, member_index)` obtained
  from the m49 core accessor, which answers "for the reduction that produced a given compiled
  artifact" (§8.2(i)), and a bare id list cannot produce that. **The artifact is what CARRIES that
  answer** — §8.2(i) binds the map as an additive `CompiledGraph` field populated at m49 — which
  is what makes this paragraph's "the artifact, not an id list" rationale true rather than merely
  preferable, and is why the ONE-argument hook shape m48 freezes needs no widening at m49. An m48
  implementer choosing the narrower spelling would ship a seam m49 cannot use, and m49 could then
  only re-open an m48-frozen surface or compile twice, which the next sentence forbids. `plan()`
  MUST NOT compile a second time: the §3.3 anti-quadratic budget is written for ONE reduction of
  the variation-expanded graph, and a frontend-side `compile_ir` before `aggregate_plan`'s own
  would double it. **That rule is knowingly left UNANCHORED and rides an R0.11 implementer-report
  measurement instead (the measured compile count for one `gh.plan({…})` call)** — its violation
  is silent (correct results, doubled reduction cost), m48's (α) anchor observes only the hook's
  own firing INSIDE `aggregate_plan` and says nothing about a compile that preceded it, and §3.3's
  frozen budget is a gate on a different fixture; the same treatment §1.1 gives its
  `"1e1000000000"` rule. The seam is a function signature, not a schema, so m48's §7.2
  schema-absence anchor (worded over `ExecResult`/`Plan`/monitor) is untouched by it.
  **Each half is anchored in the repo whose source it is** (the seam is new source in `graphed`'s
  `python/graphed/aggregate.py` while every requirement consuming it is fill-shaped and §10 places
  those anchors in `graphed-histogram` — whose frozen suite does not count toward `graphed`'s
  ≥90% diff-coverage-from-the-frozen-suite gate): **(α) carries a `graphed`-side m48 anchor over
  an UNVARIED `aggregate_plan` build** (§10/m48), and **(β)'s return CHANNEL is anchored at m48
  WITH (α) — m48's (α) anchor freezes that a returned value reaches the shipped closure — while
  (β)'s per-plan PAYLOAD is anchored at m49 alongside §8.2(i)**, whose `variation_labels` is its
  only consumer — until m49 the field is a pass-through with a default, not unreachable source.
  **The §8.2(i) FIELD DECLARATION is therefore an m48 target and m49's `§8` target line excepts
  it** — both target lines say so (§10). **The same node-id rule governs §6.4f's widened
  write-path unpack** — it is stated there too, because that is the paragraph an m51 implementer
  works from.
  **A SECOND collapse mechanism exists that record-time identity CANNOT see, and m48 refuses
  rather than mis-slices**: the derivation above is sound only for collapses the frontend can
  observe — two labels whose members intern to ONE record node id. The M4 reducer also merges
  **distinct** record ids: `EggEngine`'s sound rule set is commutativity over `SYMMETRIC_OPS` plus
  the identity tokens `x + 0.0` / `x * 1.0`, extracted by quotienting the IR by the e-graph. Two
  `Histogram.fill`s differing only in `weight=[w]` versus `weight=[w * 1.0]` record distinct fill
  nodes yet compile to ONE output — one value for two fill nodes, exactly the `_GroupReduce`
  mis-slice §6.1c's index-based layout exists to prevent, arriving from a source no record-id key
  can distinguish. It is not a contrived case: §1.1 makes stringified-float families first class
  and names μR/μF factors, and the obvious spelling `variations={s: w * float(s)}` contains a
  literal `w * 1.0` member. The sound key is the record→reduced map §8.2(i) establishes does
  **not** exist (an m49 Implementation Target), so **binding for m48**: **on the VARIED UNPACK
  PATH — the owner of the `(output, label) → node id` map, i.e. `graphed-histogram`'s group-plan
  builder (`plan()`), NOT `compile_ir` and NOT `aggregate_plan` — and over a VARIED program only**
  (the error must name LABELS, which exist only in the group-plan builder; and an UNVARIED
  two-histogram program whose fills the M4 identity rules merge (`w` vs `w * 1.0` — this section's
  own case) must not start raising where it previously ran, per §6.3's binding "Data /
  no-variation paths are unchanged" and §6.1c's own note that the mis-slice is "Latent today for
  two unvaried histograms with identical fills". An unvaried program's compile path is untouched;
  m48 carries a positive control for it, §10): the builder compares the number of DISTINCT
  compiled outputs (`GraphStore.deserialize(ir).outputs()`) against the number of distinct record
  node ids it marked and, on a shortfall, raises a `graphed` error naming the outputs and labels
  involved plus the workaround — spell a label whose value equals another's with the SAME
  expression (`variations={"1": w}`, not `w * 1.0`), which routes it through §1.2's record-time
  dedup path and is supported. It MUST NOT slice on a shortfall: the mis-slice surfaces as an
  opaque worker-side `IndexError`. Lifting the refusal into full support (replicating through
  §8.2(i)'s map once it exists) is NOT scoped in m48–m51 and is parked in §11.
  `ExecResult`/`Plan`/monitor **schemas** do not change in m48–m50 (per-variation monitor events:
  Phase 2, the defaulted-field trick documented — the `store.py` precedent); the absence is a
  frozen m48 anchor (§10), worded over **schema KEY SETS asserted against LITERALLY SPELLED
  expected sets, never against a sibling unvaried run** (all three are dataclasses whose field
  names are class-level constants — `Plan`, `ExecResult`, and `TaskEvent`, the monitor payload,
  passed through by instance — so a varied-vs-unvaried key-set comparison is equal BY
  CONSTRUCTION, including after an implementer adds a field, which is the only thing the anchor
  exists to detect; the same wording discipline as §6.3's params key set), not over plan bytes:
  §8.2(i)'s added `_PartitionReduce` field leaves the public schemas untouched but *does* change
  the shipped worker closure — and **wherever that closure is wrapped for checkpointing** it is
  embedded as an opaque cloudpickle `OpSpec` whose bytes feed `identity()` and therefore
  `task_id` (`python/graphed/core/plan.py`). **That wrap is a CALLER step, not something
  `aggregate_plan` performs**: `aggregate_plan` returns a `graphed.core.execution.Plan`, whose
  `process` is a plain `Callable[[Partition, WorkerResources], R]` with no `identity()` and no
  `task_id`, while `task_id` lives on `DurablePlan`/`DurablePlanV2`, whose `process` is an
  `OpSpec`, and **no `Plan → DurablePlan` bridge ships**: every `DurablePlan` construction is in
  hand-written tests, and the only production `OpSpec.from_callable` call sites are the V2
  shuffle/join stages (`shuffle.py`). See §7.3 for the churn that causes and for its exact scope.
- **§7.3 (Checkpoint semantics, documented honestly and anchored.)** Within one plan, resume works
  per-partition exactly as today (the N-variation composite partial is the journal unit) — m49
  freezes an interrupt/resume test over a varied graph whose result is byte-identical to an
  uninterrupted run. **The fixture's plan construction is bound, because a varied AGGREGATE graph
  does not reach the checkpoint runner on its own**: `run_resumable` takes a `DurablePlan` — it
  calls `plan.process.resolve()` and `plan.task_id(part)`
  (`python/graphed/checkpoint/runner.py`) — while `aggregate_plan` returns a plain `Plan` (§7.2),
  so the m49 fixture builds the `DurablePlan` explicitly — **BY VALUE:
  `DurablePlan(ir=compiled.ir, process=OpSpec.from_callable(plan.process), …)` over the plan
  `aggregate_plan` actually returned**; the m8 `OpSpec.from_ref` pattern
  (`tests/frozen/checkpoint/m8/analyses.py`) stays the documented USER idiom but is NOT the
  fixture construction. The reason: `OpSpec.identity()` for `kind="ref"` is `b"ref\0" + ref`, so
  the closure's FIELDS are not in the plan bytes at all — under `from_ref` the §8.2(i) determinism
  anchor would freeze GREEN against a `frozenset` `variation_labels`, the exact defect it exists
  to catch — and a `from_ref` fixture's `process` is a hand-written module-level callable over a
  hand-built IR, exercising no varied lowering. **The fixture's closure operands (the
  `PartitionedSource`, the reduce/combine/empty callables) MUST be module-level definitions in an
  importable module**, for the converse reason: an importable frozen dataclass carrying a SORTED
  TUPLE of labels cloudpickle-digests identically across `PYTHONHASHSEED` values, while the same
  dataclass carrying a `frozenset` does not — and the SAME dataclass defined in `__main__`
  (pickled by value) digests differently across seeds for BOTH forms, i.e. the anchor would be red
  against a correct implementation. The same clause governs the §8.2(i) plan-byte determinism
  anchor (§10/m49). Across plan revisions, adding/removing a variation changes the IR and
  therefore **every** `task_id` — no cross-revision reuse. This limitation MUST be documented in
  the user docs and design.rst — naming the canonical invalidating edit from the exemplar
  workflow: toggling the expensive shift class on or off between runs (the
  `skip_obj_systematics` pattern, lit §ewkcoffea-confirmed) rebuilds the IR and invalidates the
  whole cache. **A third invalidation class is a label RENAME, and it must be documented alongside
  the other two**: §1.2's stated rationale for keeping labels out of node identity is "renaming a
  systematic must not recompute", and that property holds at the IR/interning level exactly as
  §1.2's own m48 anchor freezes it, but NOT at checkpoint granularity from m49 onwards **for a
  journal whose `process` spec embeds the worker closure BY VALUE**: §8.2(i) puts label STRINGS
  into `_PartitionReduce`, and `task_id = sha256(_TASK_DOMAIN, ir, process.identity(),
  partition_bytes)` while `OpSpec.identity()` for an opaque spec returns the cloudpickle blob
  itself — so a pure rename leaves the IR byte-identical and still changes those `task_id`s.
  Under the documented `OpSpec.from_ref` idiom (below) a rename changes neither the IR nor the
  referenced process and invalidates nothing. State the scope explicitly in the same doc
  paragraph: §1.2's no-recompute property is about the graph, not about the checkpoint cache.
  **One-time churn on landing m48, SCOPED**: §7.2's seam half (β) is the hook's return channel and
  m48's (α) anchor freezes that a returned value is carried onto the SHIPPED closure and readable
  there (`plan.process`), which forces the additive §8.2(i) field onto `_PartitionReduce` at
  **m48**; adding it changes the pickled instance state, and the chain this section already cites
  (an opaque `OpSpec.identity()` IS the cloudpickle blob → `task_id`) makes that a `task_id`
  churn — the same module-level frozen dataclass, with and without one defaulted
  `variation_labels` field, digests differently: the state dict gains the key whatever its value.
  **m49 only POPULATES the field**, which churns nothing further for unvaried programs (their
  value stays the `None` default) — so every journal whose `DurablePlan.process` `OpSpec` embeds
  `_PartitionReduce` by value is invalidated once, at m48, *unvaried* programs included (the field
  is unconditional). **It is NOT "every existing journal"**: `_PartitionReduce` is the `process`
  of the in-memory `graphed.core.execution.Plan` (a plain callable — no `identity()`, no
  `task_id`), not of a `DurablePlan`, and the documented checkpoint idiom embeds the USER's
  module-level functions BY REFERENCE (`process=OpSpec.from_ref("myanalysis:hist_chunk")`,
  `docs/checkpoint/design.rst`; the frozen m8 fixtures do the same,
  `tests/frozen/checkpoint/m8/analyses.py`), for which the added field changes nothing. Journals
  of the by-value kind exist only where a caller built the `DurablePlan` itself through
  `OpSpec.from_callable(plan.process)` — `kind == "opaque"` for a `_PartitionReduce` instance,
  which carries no `__qualname__` — and `graphed-executors/src` has no `task_id`/`DurablePlan`
  references at all. Document the churn WITH that scope.
  **The WRITE path has NO journal to churn**: §6.4f widens `_WritePart.__call__`'s single-output
  unpack, but `graphed.write.write_plan` builds `Plan(process=write_part, …)` — the same
  plain-callable `Plan` — while `run_resumable` takes a `DurablePlan`, so nothing that ships today
  is invalidated. Where a caller wraps a write closure by hand
  (`OpSpec.from_callable(write_part)`), the m48 churn scope above applies verbatim; that is what
  m51's docs anchor says. Stage-granular content addressing is the named Phase-2 fix (§11).
  Blob storage stays content-deduped (`store.py`).
- **§7.4** Retry/dead-letter stay partition-atomic; docs state that one poisoned variation
  dead-letters the partition's whole composite (`runner.py`); the dead-letter surface names the
  guilty label via the §8 StageError (asserted inside the §8.2 frozen test).

## §8 Debug, errors, provenance

- **§8.1** `StageError` gains `variation: str = ""` — constructor field, `summary()` line,
  `__eq__`/`__hash__` participation (`debug/errors.py`); pickling rides the existing `__dict__`
  `__reduce__` for free. Empty string = nominal/unvaried (backward compatible).
- **§8.2 (Label transport — mechanism bound.)** Under §1.2 the label is not in the IR and under
  §2.3 all sibling nodes share the user's source line, so op+frames cannot disambiguate labels.
  No existing channel carries a label to a worker-side error: `_PartitionReduce.__call__` — the
  callable that actually runs on a worker for an `aggregate_plan` — reads the partition and calls
  `evaluate_ir` bare, with no provenance, no node map, no try/except and no `StageError`
  (`aggregate.py`); the only code that constructs a `StageError` is the class itself
  (`debug/errors.py`) and the M6 debug runner (`debug/runner.py`), which is **driver-side** — it
  needs a live `Session` (`lower(session, array)`, `session.source_value(nid)`) and is a debug
  runner, not the M7 executor. Per-node provenance is likewise driver-side only
  (`Session._provenance`, exposed via `sourcemap()`). The executors never build one either — they
  translate worker death or re-raise an already-raised `StageError` (`submit/engine.py`). Every
  existing cross-process `StageError` with real provenance comes from a test closure that REBUILDS
  the graph in the worker (`tests/frozen/debug/m6/analyses.py`; `graphed-executors`
  `tests/frozen/m7/analyses.py`).
  **The mechanism is therefore NEW work, in the parts enumerated below, all m49 targets.**
  (i) *Transport*: a `variation_labels: tuple[tuple[tuple[int, int | None], tuple[str, ...]], ...]
  | None = None` field (the `| None` and the default are bound: §7.2's (β) makes this the hook's
  return channel — "the per-plan variation metadata, or `None`" — and the field is ADDED at m48 as
  a defaulted pass-through, one milestone before m49 populates it, all under the DoD's
  `mypy --strict` on src AND tests; a non-optional declaration would make m48's dummy read-back
  unwritable and red m48's frozen (α) anchor at m49) — a sorted association list from the **PAIR
  key** `(reduced_node_id, member_index)` to that node's labels. The member half is not cosmetic:
  a universe's chain collapses into a Stage whose members are evaluated inline (`execute.py`),
  which is why `member_index` exists; the value is still a sorted tuple, so the determinism
  argument below is untouched. The value is **an ORDERED, SORTED label tuple per key, never a
  `set`/`frozenset`** — a `frozenset[str]` is a determinism BUG, not a style preference: a
  frozenset pickles in hash order, so the closure's cloudpickle bytes differ across processes with
  differing `PYTHONHASHSEED`, and those bytes feed `OpSpec.identity()` →
  `DurablePlan.task_id()`/`to_bytes()`/`fingerprint()` (`core/plan.py`); the same label set
  pickled under differing `PYTHONHASHSEED` values yields distinct plan fingerprints for one
  program — violating §3.2 in its R22.3 form, failing the DoD determinism gate, and killing
  cross-run checkpoint reuse outright. The house discipline is already the opposite:
  `read_columns` returns its read set SORTED precisely so a set never reaches a plan
  (`return tuple(sorted(needed))`, `projection.py`). The §8.2 multi-label rendering below already
  sorts, so nothing downstream changes. The field is ADDED to the worker process closure
  (`_PartitionReduce`, `aggregate.py`) — an additive dataclass field, so `Plan`/`ExecResult`
  schemas stay untouched (§7.2). It is keyed on **POST-REDUCTION node ids** taken from the same
  `compile_ir` call that produced the shipped `ir`; record-time ids are wrong, because DCE
  compacts and remaps (the `remap` vector in `dead_code_elimination`, `src/optimizer/mod.rs`) and
  the pipeline rebuilds into a fresh interned store.
  **THAT KEY SPACE REQUIRES A CORE ACCESSOR THAT DOES NOT EXIST, and building it is an explicit
  m49 Implementation Target.** `CompiledGraph` carries `ir: bytes` and
  `source_names: tuple[str, ...]` and nothing else (`python/graphed/execute.py`) — no remap, no id
  table; the PyO3 surface exposes no mapping either — no `#[pymethods]` fn on `GraphStore` (nor in
  the `PayloadDescriptor` or `IncrementalReducer` blocks) returns an id mapping, and the `remap`
  vector lives entirely inside `dead_code_elimination` and is never returned. Fusion also means
  most varied nodes have **no** post-reduction node id of their own: a universe's chain collapses
  into ONE `Stage` whose members are evaluated inline (`execute.py`), as §3.3's measurement shows
  (N=128 universes × 50 chain ops → 129 stages / 258 nodes).
  Binding: m49 adds a **read-only** `graphed-core` accessor returning, for the reduction that
  produced a given compiled artifact, `record_node_id -> (reduced_node_id, member_index | None)`.
  **The CARRIER to the consumer is bound too, because none exists today and the m48 hook shape is
  frozen before m49 needs it**: `CompiledGraph` carries `ir`/`source_names` and one method
  `evaluate`; `compile_ir` reduces INSIDE itself and lets only the serialized bytes escape; the
  core reduce entry points return `(store, report)` with no id table; and the DCE `remap` never
  leaves the optimizer — so "an accessor over a given compiled artifact" has no operand as stated,
  while the three conceivable carriers are each foreclosed (a second reduction inside the hook is
  the doubled reduction §7.2 forbids; serializing the map into the IR is barred by §3.1's "no
  serialize tag"; a second hook PARAMETER would contradict m48's frozen one-argument (α) anchor).
  Binding: the map rides on the artifact as an **additive `CompiledGraph` field** — absent/`None`
  at m48, populated by `compile_ir` from the core accessor at m49 — the same additive-field shape
  §2.5 already takes for its unreached-label diagnostics channel, and the same scoping note
  applies (m48's §7.2 schema-absence anchor is worded over `ExecResult`/`Plan`/monitor, not over
  `CompiledGraph`). Consequence, and it is the point: **m48's (α) hook signature — ONE argument,
  the `CompiledGraph` — stays sufficient at m49 and MUST NOT be widened**, since the hook reads
  the map off the artifact it already receives.
  **The PRODUCER of `variation_labels` is bound**: the association list is computed by the HOOK
  SUPPLIER — `graphed-histogram`'s group-plan builder (`plan()`,
  `src/graphed_histogram/boost.py`), the sole owner of the `(output, label) → record node id` map
  (§7.2) — and the COMPUTATION is bound with it, because composition over that map ALONE cannot
  produce the content this section binds: per label, take that entry's record CONE (the record ids
  reachable from that label's marked output via `session.walk` — the same computation §3.4's
  impact verb performs; the `(output, label)` map supplies the cone ROOTS, and `plan()` holds
  those fill nodes hence a `Session`), map every reached id through the m49 core accessor, and
  UNION the labels per resulting `(reduced_node_id, member_index)` key — which is what makes the
  map SET-VALUED. Composition over the roots alone is single-valued by construction (distinct
  labels have distinct fill nodes, §6.1b's `1 + |S| + |W|`) and carries no entry for the node a
  failure actually raises at: an `External` fill is a stage BOUNDARY (`is_boundary` is
  `!matches!(self, NodeKey::Op { .. })`, `src/node.rs`), so a universe's compute chain fuses into
  a different stage whose key is never a fill-node key, and (iii)'s op-dispatch lookups would all
  miss. The map is returned through §7.2's (β) channel. `graphed` itself never produces it: §2.3d
  bindingly makes `compile_ir`/`aggregate_plan` REFUSE a `Varied` output, so no `graphed`-side
  program has labels to associate. Consequence for §10: `graphed`'s m49 anchor witnesses the
  ACCESSOR (and the set-valuedness its key space must support); the LABEL association is witnessed
  in `graphed-histogram`'s m49, through the bound owner, never by a test that supplies its own
  hook and then asserts what it just computed (the self-derived trap §5.2a names).
  **§3.1 still holds** ("no optimizer SEMANTICS change"): it is a read-only accessor over data the
  reducer already computes — no new `NodeKey`, no serialize tag, no optimizer arm, no semantics —
  but it does mean retaining and returning the `remap` vector `dead_code_elimination` discards
  today, which §3.1 names explicitly so an integrity reviewer does not read the m49 work as
  violating it. The map keys on `(reduced_node_id, member_index)` accordingly. If the accessor is
  descoped, the honest fallback is coarse, and is stated here rather than silently assumed: **an
  "output-position" fallback is NOT implementable either**, for the same reason part (iii)
  exists — `evaluate_ir` is one flat loop over `store.nodes()` appending into `vals` with no
  `try`/`except` and no per-node annotation, and outputs are selected only at the end
  (`return [vals[o] for o in store.outputs()]`, `python/graphed/execute.py`), so a failure inside
  the loop carries neither a node id NOR an output identity, and most nodes are not outputs at
  all. Without (iii) the only truthful attribution is **plan-wide**: the raised `StageError`
  carries the sorted UNION of all labels registered on that plan (rendered per the multi-label
  rule below), and the docs say so. That is why (iii) is the keying event for both (i) and any
  fallback: descoping it does not buy a coarser key space, it removes per-label attribution
  entirely.
  (ii) *Attributed worker-side errors*, which do not exist today: the `evaluate_ir` call site in
  `_PartitionReduce.__call__` is wrapped so a worker failure becomes a `StageError`, and the
  per-node provenance the map keys alongside is shipped in the same closure — **re-keyed through
  the same accessor**, since `Session._provenance` is keyed by RECORD-time ids (written at the
  `self._provenance.setdefault(...)` sites, one per `_array_cls` chokepoint) and inherits the
  identical remap problem.
  (iii) *Per-node failure attribution inside `evaluate_ir`* — **the keying EVENT, and a third m49
  target**; without it (i) and (ii) do not compose: a wrapper AROUND the call cannot produce a
  node id, so it cannot index the map (i) ships. `_PartitionReduce.__call__` is `read_partition` →
  `evaluate_ir` → `self.reduce(values)`, one call with no per-node context (`aggregate.py`);
  `evaluate_ir` is a bare `for nd in store.nodes():` dispatch loop with **no `try`/`except` and no
  node-id annotation anywhere**, whose `kind == "stage"` branch evaluates members in an inner loop
  that annotates nothing (`execute.py`). So `except Exception` at the call site yields an
  exception carrying no node id — no map key, no label. Binding: `evaluate_ir` gains an **optional
  attribution hook** (or an equivalent exception wrapper) that annotates a failure with
  `(reduced_node_id, member_index | None)` at those two dispatch points, and `_PartitionReduce`
  maps that through `variation_labels`. This is a change to `graphed`'s **evaluation path** — not
  to core, not to the IR, not to any schema — and it lands in `graphed`, so the m49 anchors are
  worded over the RESULTING `StageError`, never over the wrap site. **If (iii) is descoped, the
  plan-wide fallback above is what remains**, because the accessor alone then buys nothing.
  **The map is set-valued, not a function** — §3.4 proves it in this document: "a node shared by
  `jes_up` and `jes_down` but not nominal appears in BOTH impact sets" — **carried as (i)'s sorted
  tuple**, which is the same content in a deterministic wire shape. Rendering is bound: a
  singleton renders as that label; a multi-label value renders as its labels sorted and joined by
  `,`; the empty value renders `""` (nominal/unvaried, §8.1).
  Frozen m49 anchors: a failure raised inside the `jes_up` universe on a worker across a process
  boundary re-raises driver-side carrying `variation == "jes_up"` AND the user's analysis line (M6
  contract extended, not altered), and the dead-letter descriptor shows the label (§7.4); **plus a
  shared-node failure asserting the multi-label rendering** — without it the single-label anchor
  passes under a pick-one-arbitrarily implementation and the defect survives the freeze.
- **§8.3** Per-node provenance needs no new machinery (§2.3): varied nodes record at user op lines.
  `to_dot`/debug labels remain readable; the impact-set API (§3.4) is the "which nodes belong to
  which label" view.

## §9 Preservation and introspection

- **§9.1** `graphed.labels`/`graphed.universe`/`graphed.nominal` (§2.2),
  **`graphed.context_of(array)`** (the §2.3e context handle carried by an `Array`/`Varied`, `None`
  when context-free; read-only; m48, spelling pinned at m48 freeze — `Histogram.fill` lives in
  `graphed-histogram` and §6.1d requires it to read that handle, while every other §9.1 verb TAKES
  a context and none returns one from a value),
  **`graphed.unify_contexts(*handles)`** and **`graphed.reindex_to(value, ctx)`** (the §6.1d
  lineage seams — most-derived-or-divergence-error over context handles, and an ancestor value
  re-expressed in a context's row space across §6.1d's link kinds; read-only; both m48, spellings
  pinned at m48 freeze — `context_of` exposes the HANDLE but nothing else exposes the RELATION
  between two handles or the intervening masks, while §6.1d's unification and re-indexing are
  executed by `Histogram.fill` in the other distribution and `graphed.selection` is m51),
  **`graphed.weight(ctx)`** (the context's ambient weight as a `Varied`, `None` when nothing is
  registered; m48 — the weight-side twin of `graphed.selection`: §2.6a reserves no attribute
  names, so a factor handed to `graphed.vary(..., is_weight=True)` is absorbed into an immutable
  registry the user could not otherwise read back. That is fine for the ambient-fill mainline but
  not for §6.4b, whose "their varied factors, when among the stored fields" presumes the user can
  name them, nor for a program that needs to READ the ambient weight — to store it, to compare it,
  or to fold it into a value explicitly. Read-only: it returns the registry's current `Varied`, it
  does not mutate),
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
  **On a universe/nominal-derived context**, §2.2 defines this case as "equal to the argument's
  selection at that label" — the mask that derived the ARGUMENT from ITS parent, restricted to one
  label: on a context produced by `graphed.universe`/`graphed.nominal` the verb returns **that
  label's member of the argument's own selection — an unvaried `Array`, not a `Varied`, living in
  the GRANDparent's row space** (`None` when the argument is a root context).
  **On a `graphed.vary`-derived context** — the third §6.1d link kind, and the one the §2.6
  sketch's own skim path produces (`sel = events[mask]` then
  `sel = graphed.vary(sel, "btag", …, is_weight=True, …)` rebinds `sel`, so
  `graphed.selection(sel)` on the rebound name would otherwise be undefined and the canonical
  §6.4a spelling would silently pass `None`): a `vary` link is an IDENTITY link (§6.1d link kind
  (2) — the row space is unchanged, only registrations differ), so the verb returns the selection
  of the **nearest ancestor reached across `vary` identity links only** — i.e. it skips over any
  number of `vary` links and answers as of the first non-identity link, `None` when that walk
  reaches a root context. One rule, stated per lineage link kind, matching §6.1d's link-kind
  table),
  **the §6.1a RESULT UNPACKER** (`graphed_histogram.unpack(value) -> dict[str, bh.Histogram |
  dict[str, bh.Histogram]]`-shaped, over the executed plan's flat slot-keyed value ALONE, choosing
  per output from the SLOT KEY FORM — the three key forms are disjoint and per output,
  §6.1a/§6.1c; read-only; **m48, spelling pinned at m48 freeze** — §6.1a's result shape is
  produced by no bound surface today: `Plan` has no finalize hook, `ExecResult.value` is exactly
  the combine output, and `plan()` returns that `Plan` and nothing else),
  **a per-label FILL-NODE accessor** (`graphed_histogram.fill_nodes_by_label(h) -> dict[str, Array]`
  -shaped, or an equivalent labelled return from the §6.1c group API; **exact spelling pinned at
  m48 freeze**, m48 — §4.3's bound extraction mechanism reaches for the §7.2
  `(output, label) → node id` map, which §7.2 only says the frontend *owns*: ownership is not an
  importable surface, and today's public `Histogram.fill_nodes()` is UNLABELED (staged-fill order,
  no label attribution, and nothing in this plan pairs that order with `graphed.labels` order).
  Read-only),
  **the §3.4 impact API** (`{label: tuple[int, ...]}` of that label's sorted record node ids, over
  the per-label output CONTAINERS — `Sequence[Varied] | Mapping[str, Sequence[Array]]` (the
  labelled mapping is what the fill-node accessor above returns), WITHOUT `source_nid`, §3.4;
  read-only; m49, spelling pinned at m49 freeze),
  **the §5.3 per-label projection-stats verb** (`{label: tuple[str, ...] | None}` of that label's
  sorted read set — `None` meaning "read every column", `read_columns`' own conservative answer,
  §5.3 — over `Sequence[Varied] | Mapping[str, Sequence[Array]]` plus `read_columns`'
  `source_nid`; read-only; m49, spelling pinned at m49 freeze), and a
  plan-level listing of `{output: [labels]}` **(m50; spelling pinned at m50 freeze; its own frozen
  anchor in `graphed`'s `tests/frozen/preserve/m50` — it cannot be anchored inside m50's
  `inspect()` test, since `inspect(bundle: Bundle) -> str` renders a preservation BUNDLE as
  human-readable text: it takes a bundle, not a plan, and returns a string, not a mapping, so a
  string-containment assertion over a bundle rendering would leave the mapping API uncovered under
  the DoD's ≥90% diff-coverage-from-the-frozen-suite gate)** constitute the introspection surface
  (RDF `GetVariations` analogue); `inspect()`'s own label listing stays anchored in m50's
  `inspect()` test (§9.2).
- **§9.2** Preservation: a bundle built from a variation-expanded graph reproduces **all** labels
  from ONE bundle, in the m9 comparison form (per label,
  `np.array_equal(reproduce(bundle)[label], build_time[label])` — the genuinely bit-exact
  in-process form, `preserve/m9/test_reproduce.py`), and `inspect()` lists the labels without
  executing. **The API surface this presupposes does not exist today and is bound here**: today
  `build_bundle(root, *, session, value, weight=None, …, histogram=None, …)` is strictly SINGULAR
  (and raises unless `weight=` and `histogram=` are given together), and `reproduce(bundle)`
  returns a single array. m50 extends both: a varied bundle accepts a `Varied` `value=`/`weight=`
  (equivalently a per-label mapping) and `reproduce` returns `{label: array}`; **an unvaried
  bundle still takes bare Arrays and `reproduce` still returns a bare array** (backward
  compatible). **The MANIFEST needs a label channel and it is bound here, because the durable one
  does not exist**: the manifest's `analysis.outputs` is the two-key record
  `{"value": int(value.node_id), "weight": None if weight is None else int(weight.node_id)}`,
  `reproduce` ends `return values[out["value"]]`, and `inspect()` renders solely from
  `m['environment']`/`m['config']`/`m['analysis']['histogram']`, the deserialized IR nodes and the
  stored sourcemap — while §1.2 keeps labels OUT of the IR, so the nodes cannot supply them
  either; both bound behaviours above therefore need a new manifest field. Binding, and ADDITIVE
  the way §8.2(i)'s field is: a VARIED bundle's manifest carries a per-label output map —
  `analysis.outputs` extended to `{label: {"value": id, "weight": id | None}}`, or an additive
  sibling key — **SORTED by label** so `canonical_bytes`' sorted-key serialization stays
  deterministic and the fingerprint stays stable; `FORMAT_VERSION` (today `1`) bumps with it, and
  an UNVARIED bundle keeps today's singular shape and version. Exact spellings pinned at m50
  freeze. This replaces the m9 fixture's one-bundle-per-config pattern *additively*: existing m9
  frozen tests are untouched.

## §10 Milestones (strictly ordered; m48 → m49 → m50 → m51)

Numbering: the executors repo froze m47 last. Frozen layouts by repo: consolidated `graphed` —
directories pinned now, because that repo's frozen tree is partitioned by package, pytest runs it
per subtree at per-milestone granularity, and duplicate basenames have bitten it before:
**`tests/frozen/frontend/m48`, `tests/frozen/frontend/m49`, `tests/frozen/preserve/m50`,
`tests/frozen/awkward/m51`**, plus the §3.3 benchmark in `tests/frozen/core/m49` **and
`tests/frozen/numpy/m51` for m51's numpy-backend refusal anchor** — §6.4f's numpy half is
`graphed`-side source (`python/graphed/numpy/io.py`), and `numpy` is a `SPLIT_PKG` in
`scripts/run-tests.sh`, so placing that anchor in `tests/frozen/awkward/m51` would cross the
package partition these pins exist to respect and leave it outside the basename rule. Any helper
imported ACROSS those directories must be added to `pyproject.toml`'s `pythonpath` list (the
corpus-reference anchors already have `tests/_corpus` there); a shared `vary` fixture module is
expected and must be listed.
**Pinning the directory does not close the per-FILE hazard for the two new NON-split directories**:
`scripts/run-tests.sh` runs `core` and `preserve` as ONE pytest process each — `SPLIT_PKGS` is
`"frontend numpy awkward"` only — there is no `__init__.py` anywhere under `tests/frozen`, and
prepend import mode turns a duplicate top-level basename into a collection ERROR. The colliding
names are the natural ones: `tests/frozen/core/m4/test_benchmark.py` already exists while §3.3
tells the author to replicate it, and `tests/frozen/preserve/m9/` already holds
`test_reproduce.py` AND `test_inspect.py` — precisely m50's §9.2 anchors. Binding: files under
`tests/frozen/core/m49` and `tests/frozen/preserve/m50` MUST use basenames unique across their
whole package subtree (e.g. `test_variation_benchmark.py`, `test_varied_bundle_reproduce.py`,
`test_varied_inspect.py`).
**The rule GENERALIZES to every new frozen directory this plan creates, in every repo** — the
hazard is identical wherever one pytest process collects a flat tree with no `__init__.py`:
`graphed-histogram` runs `pytest tests/frozen` in ONE process (`.github/workflows/ci.yml`) with
zero `__init__.py` under `tests` and gains three flat directories (`m48`/`m49`/`m50`) whose
natural file names collide with each other and with the existing `m23`/`m29` files;
`graphed-executors` likewise runs `pytest tests/frozen` in one process with zero `__init__.py`
and its existing milestone directories; and `graphed`'s `checkpoint` subtree — where §7.3/§7.4
belong — is NOT a `SPLIT_PKG` and already holds `tests/frozen/checkpoint/m8/test_resume.py`, the
most natural name for an m49 resume anchor. Binding: **every file added under
`graphed-histogram tests/frozen/m48|m49|m50`, `graphed-executors tests/frozen/m49`,
`graphed tests/frozen/{core/m49,preserve/m50,checkpoint/m49}` and `uproot5-graphed-mvp
tests/frozen/m51` carries a basename unique across its whole pytest-process scope**, and a helper
imported across directories is added to that repo's `pythonpath` (the same clause `graphed`
already carries; `graphed-histogram` uses the convention `pythonpath = ["src",
"tests/frozen/m23"]`, `graphed-executors` `pythonpath = ["src", "tests/frozen/m7", …]`).
`graphed-executors` = flat `tests/frozen/m49`;
**`graphed-histogram` = flat `tests/frozen/m48`, `tests/frozen/m49` and `tests/frozen/m50`**
(m49 anchor (i) bindingly requires `tests/frozen/m49` here; m50's primary target §6.2 lives in
this repo, so its directory is pinned too, while m50's `graphed` half is
`tests/frozen/preserve/m50`, which hosts m50's preservation, docs **and frontend-introspection**
anchors — the §9.1 `graphed.variations(ctx)` anchor and the §6.2(i-bis) narrowing-helper
behaviour of `graphed.labels`/`graphed.universe` over a histogram object both live in `graphed`;
mechanically the directory is fine — `scripts/run-tests.sh` runs `preserve` per package and
frozen tests already import across package boundaries, e.g.
`tests/frozen/frontend/m40/test_noninner_null_key_option.py` importing `graphed.awkward`).
**`uproot5-graphed-mvp` has NO frozen tree today** — its graphed tests are flat, ordinarily-named
files directly under `tests/` (`test_graphed_write.py`, `test_graphed_nanoaod.py`, …, plus the
two shared helper modules `graphed_uproot_analysis.py` / `graphed_uproot_report.py`, which are
not `test_graphed_*.py`) and the string `tests/frozen` appears nowhere in the repo. m51 therefore
**CREATES `tests/frozen/m51/` there**, and the integrity rules bind it from freeze; the existing
`tests/test_graphed_*.py` stay unfrozen.
**That repo's GATES are analysed here too, because §10 does it for the other three and m51's ROOT
half is "the larger half of m51" (§6.4f)**: the new tree IS collected (`pyproject.toml`,
`testpaths = ["tests"]`), but the only workflow that installs `graphed` and runs the graphed
tests is `.github/workflows/graphed.yml`, whose test step is
`python -m pytest -vv tests -m "not xrootd"` with **zero `--cov`**, on **ubuntu-latest only**,
CPython **3.11/3.12 only**, triggered `on: push: branches: [graphed-mvp]` + `workflow_dispatch`
(**not** on `pull_request`); the repo has **no `[tool.mypy]` section at all** and no coverage
config. As configured, the DoD's ≥90% diff coverage FROM THE FROZEN SUITE, `mypy --strict`, and
full-§A.5-matrix CI green (R0.5) cannot be discharged for that half — the
silently-discharged-gate class §10 repairs for the other repos. **Binding, as part of m51:**
(a) a `--cov` invocation over m51's new ROOT-side source with the ≥90% diff-coverage gate, added
to `graphed.yml` (the `graphed-histogram` `.github/workflows/ci.yml` shape,
`pytest tests/frozen --cov=… --cov-branch`); (b) a `[tool.mypy]` config covering that new source
AND `tests/frozen/m51` (R0.4a); (c) an explicit statement, in m51's DoD record, of the CI matrix
its DONE is keyed on for this repo — either widen `graphed.yml` toward §A.5 or record the reduced
matrix (ubuntu / 3.11-3.12) as the accepted scope — and either add `pull_request` to the trigger
or state that DONE is keyed on a branch push.
Each milestone runs the full §12 process. Frozen anchors listed here are the acceptance skeleton
the test-author starts from; the frozen m05/m4/m9/m23/m29 artifacts are **binding and unchanged**.

- **m48 — `vary` frontend + weight path** (repos: `graphed` + `graphed-histogram`).
  Targets: §1, §2 (incl. the §2.6 event context) **except §2.5's shift-after-weight ordering
  diagnostic, which is m49's — it needs §3.4's reachability cone, an m49 target**, §3.2, §4,
  §6.1 (incl. §6.1d ambient fills; **§6.1b's arity anchor is m49's — m48's `W` is exercised by
  the corpus weight matrix, while a COUNTED `1 + |S| + |W|` assertion needs the shift path
  (§5, m49); m48's own varied-AXIS and varied-`sample=` programs are anchored for fold order and
  result shape, not for arity** — no coverage gap results, since §6.1b describes a property of
  the sibling lowering that m48's matrix and §6.1a anchors exercise, and §6.1b's `S`/`W` split is
  unwitnessable before m50)
  **except §6.1c's AXIS-MODE slot, which is m50's with §6.2** (m48 implements only the sibling
  `{(output, label): [indices]}` layout its anchors exercise), **§7.2** (m48 freezes the §7.2
  schema-absence anchor, and §6.1a/§6.1c cannot be implemented without §7.2's
  `(output, label) -> node id` map and the indices-based `_GroupReduce.layout` it feeds;
  **including §7.2's `aggregate_plan` SEAM**, without which the COMPILED ARTIFACT is not
  available where §7.2's own merge refusal needs it (§6.1c's layout is not a consumer: it is
  derived from `plan()`'s own ordered `fill_nodes` list in
  `graphed-histogram src/graphed_histogram/boost.py`) — `aggregate_plan` compiles internally in
  `python/graphed/aggregate.py` and takes pre-built closures; §7.1/§7.3/§7.4 stay m49),
  **plus §8.2(i)'s `variation_labels` FIELD DECLARATION ONLY — `tuple[…, …] | None = None` on
  `_PartitionReduce` (`python/graphed/aggregate.py`), unpopulated: it is §7.2's (β) return
  channel and m48's (α) anchor reads a returned dummy off the SHIPPED closure, which is
  unimplementable without the field; §8.2(i)'s accessor, keying and population stay m49**,
  §6.3, **§9.1 partially — `graphed.labels`/`universe`/`nominal`/`weight`, `graphed.context_of`,
  **`graphed.unify_contexts` + `graphed.reindex_to`** (§6.1d's lineage seams, without which
  m48's fill-shaped re-indexing anchors are implementable only by reaching into `graphed`'s
  private context object from `graphed-histogram`), the per-label fill-node accessor, and
  `graphed_histogram.unpack` (§9.1 marks the unpack verb m48 with its spelling pinned at m48
  freeze, and m48's §6.1a anchor is bindingly worded over it) only** (`graphed.weight` is m48's
  because an m48 frozen anchor consumes it — the §2.1 stacking anchor MUST use it, and §6.4b is
  unsatisfiable without it; m50's §9 target narrows to `graphed.variations` + §9.2
  correspondingly; m51's carries `graphed.selection`).
  **§3.4 is an m49 target, NOT m48** (§3.4 itself and m49's target line both place its frozen
  anchor in m49, and no m48 anchor exercises it: §4.3's impact-set cross-check is explicitly
  optional ("MAY ride along"). New m48 source with zero m48 frozen coverage either fails the
  DoD's ≥90 % diff-coverage-from-the-frozen-suite gate or is covered only by `tests/extra`,
  which that gate excludes. The API lands with its anchor in m49.)
  **The anchor list is PARTITIONED per repo, and the fill-dependent half needs a corpus edit**
  (the same analysis §10/m49(ii) does for its half):
  **`graphed`, `tests/frozen/frontend/m48`** takes the pure-frontend anchors (§1.1 grammar, §2.x
  semantics, §2.6 context lineage, §1.2 label-out-of-identity **except the RESULT-MAPPING half of
  its dedup clause** (the straddling-anchor assignment below keeps the dedup clause's
  arena-Δ/node-id/one-value half in `graphed`) **AND except the VARIED half of its §7.2
  merge-guard clause** (§7.2 binds that guard's SITE to `graphed-histogram`'s group-plan builder —
  `plan()` in `src/graphed_histogram/boost.py`, the sole owner of `(output_name, Histogram)`
  pairs — so triggering it needs `Histogram.fill` + `gh.plan(...)`; left in `graphed` it needs
  `pytest.importorskip("graphed_histogram")`, i.e. a SKIP in CI silently discharging the
  milestone's merge guard. The UNVARIED scope positive control (`compile_ir(s, b, b * 1.0)`)
  needs no fill and stays in `graphed`), §3.2 determinism, §7.2 schema absence, **§7.2's
  `aggregate_plan` seam (α)**).
  **The "needs a fill ⇒ `graphed-histogram`" rule is GENERAL over m48's whole anchor list** — it
  is stated below inside straddling-anchor (3) for the §2.6/§6.1d mega-bullet, and it is exactly
  the rule that decides every other split in this milestone.
  **`graphed-histogram`, flat `tests/frozen/m48`** takes every anchor that needs a fill:
  the corpus weight matrix + its §5.2b read witness, §6.1a result shapes, §6.1c `.plan()`
  refusal, §6.1d ambient fills, §4.1 correctionlib, §6.3 goldens, **and §4.3's
  selection-invariance anchor** (its operands are per-label fill nodes read through §9.1's
  accessor, so it is fill-shaped).
  **Anchors that straddle the split are assigned explicitly**: **(1)** §1.2's *dedup* half
  asserts "both keys present in the result with ONE evaluated fill", and the per-label result
  mapping is `_GroupReduce`'s `{label: hist}` (`graphed-histogram src/graphed_histogram/boost.py`),
  which does not exist in `graphed` — its first half (arena Δ = 0, same node id, `compile_ir`
  returning one value) stays in `graphed` and the result-mapping half goes to
  `graphed-histogram`; **(2)** §2.1 stacking's `old_ambient[L] × factor[L]` assertion is
  observable only through a fill unless `graphed.weight(ctx)` (§9.1, m48) is used — with that
  accessor it is frontend-observable and stays in `graphed`, and the anchor MUST use it rather
  than a fill; **(3)** the §2.6/§6.1d mega-bullet below is SPLIT **by a RULE, not by a frozen
  enumeration**. **The rule: any clause whose assertion requires a `Histogram.fill` lives in
  `graphed-histogram`'s flat `tests/frozen/m48`; everything frontend-observable stays in
  `graphed`.** Applied to the enumeration: the pure-frontend clauses (tag grammar,
  no-reserved-names, lockstep validation, data guard, lineage, the §2.6c ambient-registry
  re-indexing, op-level divergence **and `vary`-construction divergence**) stay in `graphed`, as
  do the frontend-observable HALVES of the two split clauses (`graphed.labels(ctx)` reports the
  shift labels; `graphed.universe`/`nominal` return a context that is a CHILD of the argument);
  the fill-shaped clauses (ambient fill on a per-object quantity, the manual-broadcast reference
  (all THREE of its assertions, incl. the contexted-but-unvaried one), the execution-time
  refusal, divergent-lineage AT THE FILL, **§6.1d's link-kind-(1) ancestor-VALUE re-indexing**,
  `unweighted=True`, §6.1d's four-way fold order, the fill-label-superset half of the
  `graphed.labels` clause and the projected-VALUE half of the universe/nominal clause) go to
  `graphed-histogram`'s flat `tests/frozen/m48`. **Neither repo can host the matrix as it
  stands**: `graphed` vendors the corpus reference JSONs (`tests/_corpus/references`, on
  `pythonpath`) but lists **no** `graphed-histogram` in any extra (its `dev` extra carries
  `boost-histogram>=1.4`/`hist>=2.7` only) while CI installs `.[dev]`, and the house pattern
  there is `pytest.importorskip("graphed_histogram")`
  (`tests/frozen/preserve/m25/test_histogram_preservation.py`) — an anchor written that way would
  **SKIP in CI**, silently discharging the milestone's headline gate and contributing no
  frozen-suite diff coverage (the DoD requires ≥90% diff coverage FROM the frozen suite).
  `graphed-histogram` has the fill sink but **no corpus dependency and no reference JSONs** (the
  corpus wheel packages only `src/graphed_corpus`, while the reference JSONs live in the repo dir
  `corpus/references/`). **Binding: m48 VENDORS the corpus into `graphed-histogram` exactly the
  way `graphed` already does** — copy `graphed_corpus` + the reference JSONs to `tests/_corpus/`
  and put that directory on the repo's `pythonpath` — **and the matrix anchor MUST NOT be guarded
  by `importorskip`** (a skipped headline gate is a silently discharged milestone). **Vendoring,
  NOT a new dependency** (`graphed` has no `graphed-corpus` in ANY extra and vendors
  `tests/_corpus/{graphed_corpus,references}` with `tests/_corpus` on `pythonpath`. A dependency
  edit alone also would not install: `graphed-corpus` is not resolvable by name in this org's
  CI — the working precedent pre-installs it from a git URL via a workflow env var BEFORE
  `pip install -e .[dev]` (`graphed-executors .github/workflows/ci.yml`,
  `CORPUS: "graphed-corpus @ git+…"`), and `graphed-histogram`'s workflow has neither — it
  carries `GRAPHED` + `EXECLOCAL` only. If a future revision prefers the dependency route
  instead, it MUST bind the pair — dev-extra name PLUS the env var and its `pip install` line in
  every job that runs the frozen suite.)
  Frozen anchors:
  - Corpus **weight**-variation references through the frontend — ttbar 4j1b/4j2b ×
    {nominal, btag_up, btag_down} + ttgamma {nominal, pho_up, pho_down}, the weight-variation
    subset of the 15-reference matrix — `fingerprint(h) == ref["fingerprint"]` and
    `bin_values(h) == ref["values"]` (the `m05/test_fixtures_reproduce.py` comparison form).
    Note: the ttgamma flat SF weight is a constant — spell it
    `gak.full_like(<a per-event Array>, sf)` (`gak.full_like` in
    `python/graphed/awkward/functions.py`, parity-pinned in
    `tests/frozen/awkward/m24/test_interface_parity.py`) or as arithmetic on such an Array; what
    does not exist is a constant Array with no shape donor (§4.1, §11). The anchor says so to
    spare the test-author the mid-freeze discovery. **Same service for the corpus's `stable()`
    rounding, the detail that decides what is bit-comparable**: the references round the
    observable to 6 decimals BEFORE the fill and the view after
    (`tests/_corpus/graphed_corpus/analyses/systematics.py`; `histograms.py`'s
    `bin_values`/`fingerprint` round again). So (a) the recorded program must re-express the
    pre-fill rounding if bin-edge decisions are to match the corpus's cross-platform-stability
    intent, and **gak has no `round(x, decimals)`** (`rint` exists only as a ufunc), so
    `rint(x * 1e6) / 1e6` is the expressible form; (b) conversely `bin_values`' driver-side
    rounding is what absorbs the float-summation-order differences a per-partition fill
    introduces, so the comparison rides `bin_values`/`fingerprint` — **raw-view bit-identity vs
    the references MUST NOT be asserted**. **Third mid-freeze discovery spared**: the b-tag SF's
    operand is the **pt-CUT** jets (`sel.Jet[sel.Jet.pt > 25]`, §2.6 sketch note (iii)), not
    `sel.Jet` — the corpus computes `sel_jets = good[sel]` off `good = jets[jets.pt > 25]` and
    products the per-jet SF over `axis=1`
    (`graphed-corpus src/graphed_corpus/analyses/systematics.py`), so including sub-25 GeV jets
    changes the weight and misses the references.
  - §4.3 structural selection-invariance, in the binding form: **the selection cone's node ids
    are identical across all weight labels** (NOT an impact-set-subset wording, which is false
    for a correct implementation — §4.3); **with the extraction mechanism named**
    (§4.3): per label, `reachable(fill_node[label])` via `session.walk`
    (`python/graphed/session.py`), `fill_node[label]` from **§9.1's per-label fill-node
    accessor** (`graphed_histogram.fill_nodes_by_label(h)`-shaped, spelling pinned at m48
    freeze — §7.2 binds only *ownership*, and a frozen test cannot import an internal),
    asserting **that the per-label fill nodes' NON-WEIGHT input ids agree with nominal's** —
    `store.nodes()[fill_id]["inputs"][:n_axes]`, identical ids ⇒ identical cones by interning
    (§4.3). **The intersection wording is NOT frozen** — it is satisfied by construction (the
    axis args' cone contains the selection mask's in every implementation that fills selected
    data, so the intersection is a constant) and passes a `mask_L = mask & g_L` implementation;
    the optional reachability cross-check is frozen only in §4.3's discriminating shape.
    m05 equal-counts as sanity.
  - **§1.2 label-out-of-identity** (guards the whole interning story) — **for a varied program in
    the DEFAULT SIBLING lowering** (§1.2's own §6.2 carve-out makes both clauses false by design
    in m50's axis mode, where labels ARE StrCategory bin identities inside the content-hashed
    spec; every sibling-exposed anchor elsewhere carries this scoping): no node's `name` or
    `params` — **including, for a reduced `stage` node, its `members`' own names and params** —
    contains any label string, AND renaming every label leaves `compile_ir(...).ir`
    byte-identical. **"or token" is NOT part of the clause**: `GraphStore.nodes()` yields
    `{id, output, inputs, kind, name, params}` (a stage adding `n_members`/`members`, each member
    carrying its own `kind`/`name`/`params`) and no `#[pymethods]` member returns a token, so a
    token clause would assert over a quantity no public surface exposes; the token is derived
    from kind+name+params, and the byte-identity clause strictly subsumes it either way. The
    house pattern for reaching the store from a frozen test is `s._store.nodes()`
    (`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py`). Plus the **dedup witness
    §5.2a defers to this bullet**: two labels whose members are structurally identical give
    arena Δ = 0, the same node id, and — per §7.2 — both keys present in the result with ONE
    evaluated fill (`mark_output` de-dups in `src/store.rs`, so `compile_ir` over two identical
    outputs returns one value). **Plus the NON-record-time collapse case (§7.2)**: a label whose
    member is `nominal * 1.0` (or a sibling's `x + y` against `y + x`) has a DISTINCT record
    node id and is merged by the OPTIMIZER, which the Δ = 0 / same-node-id / one-value clauses
    above provably cannot reach — two fills weighted `w` and `w * 1.0` record distinct fill
    nodes and compile to ONE output. Assert §7.2's m48 guard: the VARIED program is REFUSED with
    a message naming the labels, not silently mis-sliced — **with the SCOPE positive control
    alongside it, in `graphed`'s half since it needs no fill**: an UNVARIED multi-output program
    whose outputs the optimizer merges — `compile_ir(s, b, b * 1.0)`, which returns ONE value —
    still compiles and runs exactly as today, so the guard cannot be implemented unconditionally
    in `compile_ir`/`aggregate_plan` (§7.2 SITE+SCOPE; §6.3's "no-variation paths are
    unchanged").
  - **§6.1c `.plan()` refusal**: `.plan()` on a `Histogram` that is VARIED **or in axis mode**
    (§6.1c's predicate; m48 exercises the varied arm — axis mode lands at m50, which extends
    this to its unvaried axis-mode fourth output — so word the anchor over the DISJUNCTION, not
    over "varied" alone, and **NOT over the spec comparison alone**: §6.1c's two arms are
    independent tests, the spec comparison decides only the axis-mode arm, and at m48 nothing
    makes a fill's spec differ from `self._spec`, so a spec-only wording has no
    m48-constructible fixture) raises naming the group API — `_SumFills` sums ALL staged fills
    into one histogram and would otherwise silently merge universes into a plausible-looking,
    physically wrong result. Positive control: `.plan()` on an unvaried **sibling-mode**
    `Histogram` still works (an unvaried AXIS-MODE one is REFUSED, §6.1c).
    **Worded over ANY varied `Histogram` — and over any AXIS-MODE one — not over the fill-node
    count and not scoped to sibling mode** (a count wording over-freezes m50's mixed program,
    and a sibling-mode rescoping opens a hole: an axis-mode `.plan()` dies inside the reducer,
    because `Histogram.plan` passes the `__init__`-time `self._spec` to `_SumFills`/`_ZeroHist`
    while §6.2 declares the variation axis at FILL time, and cross-axis histogram addition
    raises — bh 1.8.0: `ValueError: axes have different length`; §6.1c). The refusal covers both
    merge hazards; the group API is the varied route in both modes.
  - **§2.1 stacking** (m49's 15-reference matrix exercises it only implicitly, one milestone
    later): `vary` on a target that already carries variations inherits those labels, adds the
    new ones, label order = inherited-then-new, the new label's member is the provided value's
    central universe, and each label differs from nominal in exactly ONE knob (the corpus
    b-tag-on-JES case, `systematics.py`).
    **The base case's target is a LOOSE `Varied` (§2.1a)** — every other `vary` call in m48's
    anchor list targets an `Array` or a context, so §2.2's pairing branch (`graphed.vary(x, …)`
    returns the container class paired with `type(graphed.nominal(x))` when `x` is ALREADY a
    `Varied`) and §2.1(a)'s "inherited members pass through unchanged" for the loose form would
    otherwise ship unwitnessed: assert `type()` of the result carries the nominal member's
    idiom, and that the inherited members are unchanged. The extension below targets a CONTEXT.
    **Extended to a WEIGHT `vary` on a context already carrying SHIFT labels** — the case the
    corpus matrix actually turns on and the case m48's weight-only matrix cannot reach (it has
    no shift labels, so a wrong reading survives m48 and only detonates against m49's
    15-reference matrix, after m48 is frozen): assert the **inherited** shift label's ambient
    member is `old_ambient[L] × factor[L]` — the factor evaluated in THAT label's universe, per
    §2.1's per-overload stacking rule — not the old ambient unchanged.
    **The registered factor MUST be NESTED** — a `Varied` whose members are themselves `Varied`
    over the inherited shift labels, i.e. the corpus spelling `graphed.vary(sel, "btag",
    btag_sf(sel.Jet[sel.Jet.pt > 25]), is_weight=True, …)` on a `Varied`-mask-derived `sel` —
    and the assertion reads, in the bound surface (`x[L]` is this document's PROSE for
    `graphed.universe(x, L)`, §2.2; transcribed literally it records a `field` op named
    `"jes_up"`, and the inner operand is TWO-level per §2.1 since `jes_up` is new to the factor
    container),
    `graphed.universe(graphed.weight(sel2), "jes_up").node_id == (old_ambient_jes_up *
    graphed.universe(graphed.nominal(factor), "jes_up")).node_id`
    — **`.node_id` equality, NEVER a bare `assert` on the recorded comparison**: `Array.__eq__`
    RECORDS an elementwise op and `Array` defines no `__bool__`/`__len__`
    (`__slots__ = ("_node_id","_session")`), so `bool(a == b)` is `True` for every operand
    pair — the one-level wrong answer included — and the assertion additionally records a stray
    node. Node-id equality is sound by interning (two independently recorded `a * 2.0`
    expressions share one node id while being distinct objects) and frontend-observable, which
    is why this anchor stays in `graphed`'s half; materializing both through
    `Session.materialize` (`python/graphed/session.py`) and comparing elementwise is the equally
    acceptable form — naming the ONE-LEVEL answer (the factor's own `"nominal"` member: the
    b-tag SF on unshifted jets) as the wrong result it discriminates against. Without the
    nesting the anchor is satisfiable by a FLAT factor (e.g. a factor built from
    `events2.MET.pt`, a plain `Array` when only `Jet` was replaced), for which the one-level and
    two-level readings AGREE — so §2.1's two-level rule would ship unwitnessed and detonate
    against m49's 15-reference matrix after the freeze, the same exposure the extension of this
    anchor exists to close one layer up. Corpus basis
    (`src/graphed_corpus/analyses/systematics.py`): `sel_jets = good[sel]` then
    `_btag_weight(sel_jets, variation=…)`, which returns the CENTRAL SF unless the variation is
    `btag_up`/`btag_down` — i.e. the factor is computed on JES-shifted, JES-selected jets. The
    fixture needs no fill, so the anchor stays in `graphed`'s half. **Read through
    `graphed.weight(ctx)`** (§9.1) so the assertion is frontend-observable and this anchor stays
    in `graphed`'s half of the m48 split. **Plus §2.1(b)'s ROW-SPACE positive control**:
    registering, on a DERIVED context, a factor computed from a value read at the PARENT is
    accepted and re-indexed to the derived row space per §6.1d's link kinds, so
    `graphed.weight(sel)` answers at `sel`'s per-label row counts — the invariant §6.4b's
    row-space precondition assumes; `Session.record_op` performs no length check, so without
    this the mismatch survives recording and dies at execution.
    **Plus §2.1(b)'s DESCENDANT negative control**: registering, on the ROOT context, a factor
    computed from a value read through a DERIVED one (`graphed.vary(events, "btag",
    btag_sf(sel.Jet), is_weight=True, …)`) is a CONSTRUCTION-time error naming both contexts and
    the DIRECTION — it is not divergent, so §2.1's divergence check alone lets it through, and
    no re-indexing exists in that direction (a mask has no inverse, §6.4b), leaving it to record
    cleanly and die at execution outside §6.1d's refusal contract. Both controls are
    frontend-observable through `graphed.weight(ctx)` and stay in `graphed`'s half.
  - **§7.2's `aggregate_plan` SEAM (α), in `graphed`'s `tests/frozen/frontend/m48`** (the seam
    is an m48 Implementation Target in `graphed`'s `python/graphed/aggregate.py` and every
    requirement consuming it is fill-shaped and lives in `graphed-histogram`, whose frozen suite
    does not count toward `graphed`'s ≥90% diff-coverage-from-the-frozen-suite gate; no other
    `graphed` m48 anchor calls `aggregate_plan`, and `graphed`'s existing frozen coverage of it
    is m5's positive path plus m39's two-source-rejection control
    (`tests/frozen/frontend/m39/test_shuffle_plan_builder.py`) — neither exercises a seam that
    does not yet exist): over an UNVARIED multi-output program in the m5 call shape
    (`tests/frozen/frontend/m5/test_aggregate_plan.py`), the new hook fires EXACTLY ONCE and
    receives the `CompiledGraph` (the compiled outputs readable inside the hook as
    `graphed.core.GraphStore.deserialize(compiled.ir).outputs()` — **`CompiledGraph` itself
    exposes only `ir`/`source_names` plus `evaluate` (`python/graphed/execute.py`) and has no
    `outputs` attribute**) and the resulting `Plan` runs to the same value as the same program
    built WITHOUT the hook (m5's own assertion as the positive control), with the existing
    `reduce`/`combine`/`empty` parameters passed as the plain callables m5 freezes (§7.2: the
    seam is ADDITIVE — those contracts are unchanged). **Plus the RETURN-CHANNEL assertion**
    (§7.2's (β) is the hook's return value): a value returned from the hook — a dummy at m48 —
    is carried onto the SHIPPED closure and is readable there (`plan.process`), so a see-only
    spelling cannot be frozen here and block m49's `variation_labels`. **The dummy is a
    well-typed NON-DEFAULT value of §8.2(i)'s declared field type — the empty tuple `()`**
    (§7.2/§8.2(i): the field is `tuple[…] | None = None` from m48, so `()` is well-typed against
    the field's DECLARED type, is distinguishable from the default, and needs no invented type;
    a str/sentinel dummy is a type error at the hook's return and `None` is indistinguishable
    from the default).
    **The READ-BACK ROUTE is named**: `Plan.process` is declared
    `Callable[[Partition, WorkerResources], R]` (`python/graphed/core/execution.py`), so
    `plan.process.variation_labels` is an `attr-defined` error under `mypy --strict` wherever
    the test tree is type-checked (R0.4a; `graphed` is configured `files = ["python"]` today,
    one of the src-only repos R0.4a names as a pending cleanup) — the anchor reads the field off
    the CONCRETE closure type, `graphed.aggregate._PartitionReduce`
    (`python/graphed/aggregate.py`), via a narrowing `isinstance`/cast, so the route is pinned
    rather than guessed, the discipline §9.1 applies to every other new read surface.
    **"before the worker closure exists" is NOT asserted** — the hook receives only the
    `CompiledGraph` and has no handle on the closure, so a test has no operand for that
    ordering; the return-channel assertion is what makes the ordering observable at all. Seam
    half (β)'s own per-plan metadata is anchored at m49 with §8.2(i).
  - **§6.1d's LINEAGE SEAMS, in `graphed`'s `tests/frozen/frontend/m48`** (new `graphed` source
    whose only consumers are fill-shaped and live in `graphed-histogram`, the same per-repo
    coverage argument as the seam above): `graphed.unify_contexts`-shaped answers the
    MOST-DERIVED handle for handles on one ancestry chain, `None` when every argument is
    context-free, ignores context-free arguments alongside contexted ones (the §6.1d adopt
    rule), and raises the §2.3e divergence error naming BOTH contexts on divergent handles;
    `graphed.reindex_to`-shaped is the IDENTITY when the value already carries the target's
    handle or carries none, re-indexes an ancestor value label-aligned per §2.4 across link
    kinds (1)-(3) — compared elementwise against a manually re-indexed reference, the
    discriminator §10 already applies to the fill-side twin — and RAISES when the value's
    handle is a DESCENDANT of the target or divergent (§2.1(b)).
    **The link-kind half is asserted PER KIND, and each kind's RESULT LABELS are part of the
    assertion**: **(1)** a mask-derivation link returns a `Varied` carrying the intervening
    mask's labels (an UNVARIED value BECOMES `Varied`), each member re-indexed by that label's
    own mask; **(2)** a `graphed.vary` link is the IDENTITY, labels unchanged; **(3)** a
    universe/nominal projection link returns an UNVARIED `Array` equal to a manually projected
    reference, carrying NO labels — the same rule §6.1d uses to make
    `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` a BARE `hist`.
  - **§2.2 `Varied.apply`**: per-universe application of an `Array -> Array` function, plus the
    error contract — `fn` returning a `Varied` raises with guidance to combine via ordinary ops.
  - **§2.3d module-verb dispositions + §2.2's reserved `Array`-protocol names** (both guard
    against the named confidently-wrong class; the §2.3a parity gate cannot reach the reserved
    names, because `node_id`/`session` are plain properties, which `inspect.isfunction` does not
    enumerate, and m49's §5.4 anchor is the boundary-crossing refusal, not
    `graphed.join(varied)`). One table-driven test in `graphed`'s `tests/frozen/frontend/m48`,
    driven by the §2.3d **discovery rule** (dynamic over `graphed.__all__`, filtered to
    `inspect.isfunction` members ANY of whose parameter annotations mentions `Array`, **UNION
    the named floor list — in `graphed`'s test
    `{graphed.compile_ir, graphed.context_of, graphed.broadcast_like}`** (`to_parquet` is NOT in
    the m48 list — it carries no disposition until m51, §2.3d: it is outside `graphed.__all__`
    so the dynamic half never reaches it, it has no `select=` parameter to refuse today
    (`python/graphed/awkward/io.py`), and freezing an m48 entry whose VALUE m51 is bindingly
    required to change is a freeze-order trap resolvable only by Test Dispute or integrity
    violation; dropping it costs no class coverage, since the dynamically discovered verbs
    already supply *refusing* and *expanding* and the named `broadcast_like`/`context_of` supply
    the other two)
    (`context_of`/`broadcast_like` are in the floor because the annotation-wide filter discovers
    verbs that are ALL refusing/expanding, so these two are the only representatives of
    *eager-metadata* and *broadcasting* and the per-class floor would otherwise hinge on
    post-freeze annotation style; `graphed` declares no `graphed-histogram` in any extra while
    CI installs `.[dev]`, so naming `Histogram.fill` here would force the house `importorskip`
    and SKIP the whole table-driven test — discharging §2.3d's dispositions AND §2.2's
    reserved-name anchor with zero frozen-suite diff coverage; `awkward`+`pyarrow` ARE in the
    dev extra, which is why `to_parquet` is reachable at m51 when it joins the list) with
    `graphed_histogram.Histogram.fill`'s disposition asserted in `graphed-histogram`'s flat
    `tests/frozen/m48` — and MINUS `graphed.vary`** (the filter would discover m48's own
    `graphed.vary`, for which no disposition class exists; `compile_ir` is in the named floor
    because its annotations are `Session`/`Any`, so the dynamic half never reaches it despite
    its membership in `graphed.__all__`). The gate carries §2.3c's non-vacuity floor: non-empty,
    ≥ the freeze-time count, containing every member of that repo's floor list, ≥ one member of
    each class in §2.3d's bound class set **that the repo's table can host at THIS milestone**
    (refusing / expanding / broadcasting / eager-metadata / accepting; **at m48 `graphed`'s half
    hosts AT LEAST {refusing, expanding, broadcasting, eager-metadata} — a containment floor,
    never an exact set, so m51's added *accepting* member cannot red it** — `to_parquet` is out
    of the m48 table entirely (§2.3d) and the *accepting* representative at m48 is
    `graphed_histogram.Histogram.fill` in `graphed-histogram`'s flat `tests/frozen/m48`, and
    `broadcasting`/`eager-metadata` are supplied by the named `graphed.broadcast_like` /
    `graphed.context_of`).
    **Plus the IDIOM-PACKAGE enumerations, in the same test** (§2.3d puts `graphed.numpy` and
    `graphed.awkward` in scope and §10 is "the acceptance skeleton the test-author starts from",
    so a suite written without them would leave those dispositions as m48 source with zero
    frozen-suite diff coverage): the identical dynamic filter over `graphed.numpy.__all__` and
    over `graphed.awkward.__all__` — the numpy verbs (`apply_gufunc`, `empty_like`, `full_like`,
    `ones_like`, `project`, `zeros_like`) and the awkward ones (`project`, `project_buffers`) —
    each asserted to carry its §2.3d classification (the `*_like` verbs and `apply_gufunc`
    **broadcast**; `project`/`project_buffers` **expand**, returning `{label: Projection}` and
    `{label: BufferProjection}` RESPECTIVELY — each verb's own return type — and NOT
    `read_columns`' union, §2.3d). **The floor is asserted over the UNION of the three
    enumerations, never per enumeration** (neither idiom package hosts a member of the named
    floor list, and the discovered idiom verbs are only *broadcast*/*expanding*, so a
    per-enumeration floor is red against a correct implementation), and stays a containment
    floor. Freeze-order is clean for the verb whose disposition m51 is bindingly required to
    CHANGE (§2.3d): `graphed.numpy.to_parquet` is not in `graphed.numpy.__all__` at all and
    `graphed.awkward.to_parquet` — which IS in `graphed.awkward.__all__` — annotates its first
    parameter `Any` (`python/graphed/awkward/io.py`, `python/graphed/numpy/io.py`), so neither
    idiom enumeration discovers it at m48.
    **The refusal table is SPLIT BY CONTRACT, because §2.3d binds two** (`GraphedError`
    subclasses `Exception` with no relation to `NotImplementedError`
    (`python/graphed/errors.py`), so one frozen contract for all of them would red a conforming
    implementation, and frozen tests are read-only):
    the **boundary/plan verbs** (`join`, `repartition`, `pack_key`, `shuffle_plan`, `join_plan`)
    refuse with a refusal that NAMES THE OFFENDING CONTAINER — m48 asserts only that they raise
    and do not silently compile; the exact §5.4 message shape (a `NotImplementedError` naming
    the label and the boundary) is frozen in **m49**, since §5.4 is an m49 target and this
    bullet's own gak clause already defers refusing-class behaviour there. The
    **compile/aggregate verbs** (`compile_ir`, `aggregate_plan`) raise a `graphed` error naming
    `graphed.universe`, with the positive control that the same verb on a plain `Array` still
    works. **`evaluate_ir` is NOT in the table** (it takes no `Array`:
    `evaluate_ir(compiled: CompiledGraph | bytes, …)`, so there is no `Varied` to refuse and the
    plain-`Array` positive control is false for it too — a plain `Array` is not a
    `CompiledGraph`).
    The expanding verbs are asserted **per verb** (a blanket "every expanding verb returns the
    bound per-label shape" is false for `read_columns` and would freeze §5.3's m49 verb one
    milestone early, read-only): `apply` returns a `Varied`; `read_columns` returns the SINGLE
    union read set over all labels' members — `None` if any member's is `None` — NOT a
    per-label mapping (§2.3d). `graphed.broadcast_like` broadcasts (§2.3d, §6.1d); and
    `varied.node_id` / `varied.session` raise `AttributeError` rather than recording a `field`
    op, with a negative control that `varied["node_id"]` (STRING getitem) still resolves as
    field access — so the rule cannot be implemented as a blanket `__getattr__` refusal; **plus
    the PROPERTY half of §2.2's disposition rule, classified BY MEASUREMENT** — the numpy
    idiom's `shape`/`dtype`/`ndim`/`T` are plain properties `inspect.isfunction` never
    enumerates (`python/graphed/numpy/array.py`) and so cannot fall through into a recorded
    `field` op, but they are NOT one class: `dtype`/`ndim`/`shape` are `_form_meta`-backed and
    record nothing (`Session.node_count()` delta 0) while `T` is `return self.transpose()` over
    `record_op("transpose", …)` and records (delta 1). So the anchor asserts per discovered
    name against the delta measured on the PLAIN nominal `Array`: `varied.dtype` (the eager
    representative) answers eagerly on the nominal member with delta 0, `varied.T` (the
    recording representative) returns a `Varied` whose `graphed.labels` match the input's — the
    §2.3a *broadcast* disposition its own `transpose` method carries — and
    `varied.node_id`/`.session` raise. Freezing a blanket "delta 0 for every property" reds a
    correct implementation on `T`.
    **The property-classification fixture MUST be a 1-D partitioned source** (§2.2 pins the
    probe to a 1-D `NumpyForm` source; this bullet — what a test-author works from — names
    `varied.T`, the same mid-freeze discovery this milestone spares elsewhere for
    `gak.full_like`, `stable()` rounding, `h.axes.name` and the pt-cut jets): `NumpyArray.T` on
    a ≥2-D partitioned form RAISES — `gnp.ones(s, (4, 3)).T` → `GraphedTypeError: ill-typed op
    'transpose' … transpose without axes reverses them, displacing the partitioned axis 0` — so
    on a 2-D fixture the MEASUREMENT STEP itself raises and the gate cannot classify the name
    at all.
    **Plus the `graphed.context_of`-on-a-`Varied` discriminator**: a container built from an
    ancestor-handled nominal member and a MORE-DERIVED non-nominal member answers with the
    more-derived handle (§2.3e — the container's, not the nominal member's; §2.1 accepts
    exactly such a container and only DIVERGENT handles are refused, and §6.4a(2a)'s
    handle-equality predicate reads this answer). **The FIXTURE is pinned to a `graphed.vary`
    IDENTITY link** — `events2 = graphed.vary(events, "pu", …, is_weight=True)` then
    `v = graphed.vary(events.Jet, "jes", up=events2.Jet)`, asserting
    `graphed.context_of(v) is events2` — **not to a MASK-derivation link** (`up=sel.Jet`): both
    discriminate identically against the nominal-member reading, which answers `events`; the
    identity link is chosen because it keeps the row space fixed and matches what §6.4a(2a)'s
    predicate consumes.
  - **§6.1a result shapes** — **in SIBLING mode** (§6.2 axis mode is m50 and has its own shape,
    §6.2(i-bis); word the anchor so it does not freeze a general rule m50 must contradict),
    **worded over §6.1a's bound UNPACK verb (`graphed_histogram.unpack`-shaped, spelling pinned
    at freeze) and freezing the plan value's slot-keyed shape in the SAME anchor** (the two
    halves must be frozen together or a test-author freezing the nested result shape goes red
    against an implementation conforming to §6.1c's flat keying): the executed plan's value is
    the flat `{(output, label) → bh.Histogram}` mapping (`_add_groups` stays a homogeneous
    key-wise `+`, `graphed-histogram src/graphed_histogram/boost.py`), and unpacking it on a
    MIXED varied/unvaried output set gives: a varied output is `{label: hist}`, an output no
    variation reaches is a BARE `hist` (not `{"nominal": hist}`), absent labels are absent
    (never duplicated from nominal), and `graphed.universe`/`graphed.nominal`/`graphed.labels`
    narrow both shapes uniformly (**`graphed.nominal` included** — §2.2 binds it on BOTH result
    shapes while the axis-mode answer is anchored at m50 (i-bis); its m48 halves are trivial but
    are m48 source under the diff-coverage gate, and the confidently-wrong implementation §2.2
    names — "return the argument unchanged for every histogram" — is green without this
    assertion). **Plus a WHOLLY-UNVARIED positive control**: a group plan with no variation
    anywhere keeps today's value verbatim — every key a BARE output name, so
    `run(gh.plan({"hi": h1, "lo": h2})).value["hi"]` still works **and still type-checks under
    `mypy --strict` once `plan()`'s declared return type WIDENS to the union-key form §6.1a
    binds (`Plan[dict[str | tuple[str, str | None], bh.Histogram]]`), which is part of m48's
    §6.1c target** (the RUNTIME half — bare keys, m23 indexing unchanged — is what this control
    protects). §6.1a's slot keying is scoped to outputs a variation reaches precisely so the
    already-frozen m23 suite stays green (`graphed-histogram tests/frozen/m23/test_group_plan.py`
    indexes the value by bare output name), and §10 binds those artifacts unchanged.
  - **§2.3b plain-Array entry points learn `Varied`** (the m48 dunder-parity anchor is the
    MIRROR property and does not exercise it, and it otherwise reaches the suite only implicitly
    one milestone later inside m49's 15-reference matrix, where the corpus indexes unvaried
    photons by a JES-varied selection,
    `graphed-corpus src/graphed_corpus/analyses/systematics.py`): `plain_array[varied_mask]`
    and `plain_array.filter(varied_mask)` each return a `Varied` carrying the mask's labels
    (label-aligned per §2.4), with a negative control that neither raises the
    wrong-implementation shapes — `TypeError` from `__getitem__`'s final raise or
    `AttributeError` on `.node_id` from `filter`'s unchecked `record_op`, both invisible to a
    histogram-value comparison — plus a still-`TypeError`s control for a genuinely unsupported
    index type, so the branch cannot be implemented as a blanket `except`.
  - **§2.5 unreached-label diagnostic** (§2.5's raising cases are covered by "§2 validation
    errors" below but this one is a DIAGNOSTIC, not an error — the mkShapesRDF silent-cost
    guard): a registered label reaching no marked output is reported by `compile_ir`
    diagnostics; absent when every label reaches an output.
  - **§7.2 schema absence**: the `ExecResult`/`Plan`/monitor payload schema **KEY SETS** on a
    varied program equal **LITERALLY SPELLED expected sets** —
    `{f.name for f in dataclasses.fields(Plan)} ==
    {"process","combine","empty","tasks","next_tasks","stop","open_once"}` and likewise
    `ExecResult` → `{"value","n_partitions","n_combines","stopped"}` and the monitor payload
    `TaskEvent` → `{"phase","key","worker","t","partition","n_entries","bytes_read","error"}`
    (`python/graphed/core/execution.py`; `emit_task` passes the `TaskEvent` INSTANCE, so the
    payload is that dataclass, not a dict). **A varied-vs-unvaried COMPARISON is vacuous and
    MUST NOT be the assertion**: all three are dataclasses with class-level field lists, so both
    programs yield instances of the SAME classes and the key sets are equal by construction —
    including after a field is added, the only thing this anchor exists to detect. The
    comparison may ride along as a sanity assertion. Worded over key sets, NOT over plan bytes
    or the `process` spec — the §8.2(i) closure field, ADDED at m48 (§7.2's (β) return channel)
    and POPULATED at m49, changes those by design (§7.2, §7.3).
  - Single-pass read witness **on the reference-matrix run** (§5.2b applied to the weight
    matrix).
  - §3.2 determinism: same varied program compiled in two fresh processes under differing
    `PYTHONHASHSEED` → byte-identical `compile_ir` output; `graphed.labels` order pinned
    (nominal-first + insertion order).
  - §6.3 goldens (committed GIR blob, captured PRE-m48 + the params KEY-SET equality against a
    literally spelled set — `{"spec", "n_axes", "weighted", "sampled"}` for the unvaried
    single-weight fill, §6.3; a `"<new key>" not in params` assertion is vacuous here because
    m48's sibling mode adds no params key at all).
  - §2.3 **public-surface** parity (dunders AND methods, §2.3a — enumerated dynamically from
    `type(graphed.nominal(v))` so the numpy idiom's methods and tuple `__getitem__` are covered
    (`python/graphed/numpy/array.py`); `Array`'s own `filter`/`map`/`reduce`/`repartition`) and
    gak-classification exhaustiveness, both **dynamically enumerated** (§2.3a/c) — the
    classification test freezes only that every DISCOVERED public gak function has a
    classification; the *behaviour* of the `refusing` class is an m49 anchor, since §5.4 (the
    refusal message and its positive control) is an m49 target. **§2.3e context-handle
    propagation is a SEPARATE, SCOPED gate** (a behavioural "every public gak function preserves
    the handle" gate is not buildable over the full gak surface:
    `apply_correction`/`onnx_inference` take a payload first, `to_list`/`head`/`sample` are
    eager, `fields`/`type_of`/`backend_of` return non-Arrays,
    `zip`/`concatenate`/`where`/`unflatten`/`linear_fit` need typed operands — and a frozen
    test cannot grow arguments for a function added later): it enumerates only the *broadcast*,
    *container-traversing* and *tuple-returning* classes, takes its AUXILIARY call arguments
    from fixtures living in `src` beside the classification **while the frozen test itself owns
    the CONTEXTED primary operand and asserts the returned handle is not `None` and IS the
    input's** (§2.3e(2) — a context-free fixture operand makes the assertion `None == None`) —
    **each fixture being a TEMPLATE with a named substitution SLOT the test fills, including
    inside a Mapping/Sequence argument, plus an assertion that the substitution happened**
    (§2.3e(2): `gak.zip`'s mapping is its ONLY array-bearing operand, so without a slot the
    container-traversing class has no test-owned position at all), and asserts the exempt set
    is exactly {*eager-metadata*, *refusing*} **plus §2.3e(3)'s MEMBERSHIP floor** — §2.3e(3)
    is containment plus a monotone count precisely because a frozen equality reds the moment a
    future gak boundary verb arrives with its classification in `src`, which is where the
    self-repairing rule wants it: **`gak.join` IS IN the refusing class and
    `len(refusing) >= ` the freeze-time count** — `gak.join` is the only boundary verb among
    gak's public functions (`python/graphed/awkward/functions.py`); every eager-metadata
    member's return annotation is non-`Array`; the broadcast count is ≥ the freeze-time count —
    otherwise a re-classification hides an unimplemented member while the exempt CLASS NAMES
    stay exactly those two — **and the `Array`-surface gate carries its own floor** (refusing =
    `{repartition}`, broadcast count ≥ freeze-time, §2.3e(4)).
    **Each of these three tests MUST carry §2.3c's non-vacuity floor in the same test** — a
    dynamic gate whose discovery step returns an empty or wrong set passes tautologically, and
    the obvious discovery mechanism does not exist here (gak has no `__all__`, §2.3c): the
    discovered set is non-empty, at least the freeze-time count, and names at least one member
    of each classification class; the parity gate additionally names `__array_ufunc__`,
    `__getitem__`, a bitwise dunder **and at least one public METHOD**.
    **The parity gate's per-name ASSERTION is bound, not just its enumeration** (§2.3a): each
    discovered name is resolved on the CLASS (`getattr(type(varied), name, None)`) — an
    instance-level `hasattr` is answered by `Varied`'s label-mapping field access for EVERY name
    (`Array.__getattr__` records a `field` op for any non-underscore name), so a presence-based
    iteration is green against a `Varied` that broadcasts zero methods — plus one behavioural
    probe per disposition class in the same test (a broadcast method returns a `Varied` with
    matching `graphed.labels`; `varied.repartition` raises the §5.4 refusal rather than
    `TypeError: not callable`).
  - **Per-class gak behaviour** (the exhaustiveness gate asserts a classification EXISTS, not
    that it is RIGHT, and three of §2.3c's classes have no behavioural anchor anywhere else in
    m48–m51; the corpus matrices cannot reach them, since the corpus fixture uses
    `ak.with_field` (`graphed-corpus src/graphed_corpus/analyses/systematics.py`), never
    `ak.zip`. A mis-classified `gak.zip` would hand the `Varied` straight into `record_op`): one
    named representative per otherwise-unanchored class —
    `gak.zip({"pt": varied_pt, "eta": plain})` returns a `Varied` carrying the labels
    (*container-traversing*, `python/graphed/awkward/functions.py`);
    `gak.unzip(varied_record)` returns a TUPLE of `Varied` (*tuple-returning*);
    `gak.fields(varied)` / `gak.type_of(varied)` answer on the nominal member
    (*eager-metadata*). Plus §2 validation errors (§1.1, §2.5); §2.4 label-aligned combination
    on a Varied-meets-itself program, **including the bound union ORDER** (first operand's
    order, then labels new to the second in its own order, nominal first) **and §6.1d's
    FOUR-way fill fold order** — a fill with varied values in TWO axes plus an ambient weight
    plus an explicit `weight=[…]` factor **plus a varied `sample=`** (today's `fill`
    type-checks `args` and `weights` but appends `sample` unchecked
    (`graphed-histogram src/graphed_histogram/boost.py`), so a `Varied` sample falls into
    `record_external` and dies on `.node_id`), asserting the bound operand order (axis values
    in argument order, then ambient, then explicit factors in list order, then `sample=`) and
    that the varied `sample=` is ACCEPTED/expanded rather than raising `AttributeError`. **The
    fixture's histogram MUST use a `Mean`/`WeightedMean` STORAGE** — the same pin m50's
    `sample=`-only-label anchor carries, one milestone later and for the same reason: bh 1.8.0
    rejects `sample=` on the default `Double()` AND on `Weight()`
    (`TypeError: Keyword(s) sample not expected`; `Mean()`/`WeightedMean()` accept it) while
    `graphed-histogram`'s evaluator passes `sample` straight to `h.fill` and `Histogram.fill`
    type-checks nothing about the sample at record time, so a default-storage fixture RECORDS
    cleanly and dies at EVALUATION, after the freeze, against a correct implementation. If the
    anchor is instead written as a RECORD-TIME assertion — the fold order read off the recorded
    fill node's `inputs` / the per-label fill-node accessor, with the plan never run — the test
    MUST say so explicitly, so the test-author does not build a plan run around it.
  - §4.1 correctionlib single-payload multi-parameterization — **with its observable stated**:
    all labels' `External` nodes share ONE `PayloadDescriptor.content_hash` and differ only in
    the `systematic=` param, so the payload is never duplicated (fixture precedent
    `tests/frozen/preserve/m9/agc.py`).
    **The RECORDING SPELLING is named, because only one of the two correctionlib paths yields
    that observable** — the fixture's own
    `graphed.preserve.record_external(s, CORRECTIONLIB_PLUGIN, corr_bytes, [njet],
    params={"name": "event_sf", "systematic": syst})` (`tests/frozen/preserve/m9/agc.py`)
    **with the PAYLOAD named, since the hash is a pure function of it**
    (`correctionlib_content_hash` = sha256 over `b"correctionlib-contents-v1"` + canonical
    JSON, `python/graphed/preserve/externals/correctionlib_external.py`): over
    `agc.correctionlib_json()` at its default `scale=1.0`, three labels give three External
    nodes sharing one `descriptor.content_hash` and differing ONLY in `params["systematic"]`.
    `gak.apply_correction` is NOT that path — it records
    `params={"name": …, "args": json.dumps(args)}` (`python/graphed/awkward/functions.py`), so
    the systematic value rides INSIDE the `args` JSON string and there is no `systematic` key;
    a test-author reaching for it would find this anchor's observable unsatisfiable. Same
    mid-freeze-discovery service as the `gak.full_like`, `stable()`-rounding and pt-cut-jets
    notes.
  - §2.6/§6.1d event-context anchors: ambient fill on a per-object quantity — the value passed
    **UNFLATTENED** (§6.1d), Jet-pT fill yields value labels ∪ ambient labels, weight broadcast
    frozen against a manual-broadcast reference — **for the ambient weight AND an explicit
    `weight=[…]` per-event factor in the same per-object fill** (§6.1d: the evaluator
    multiplies factors after flattening each independently, so an unbroadcast explicit factor
    length-mismatches on the mainline idiom) **AND, as a third assertion, for the
    CONTEXTED-BUT-UNVARIED fill — a context with NO registrations, no `Varied` input, a
    per-object value plus an explicit per-event factor** (§6.3(2)'s trigger is a DISJUNCTION,
    "a context handle OR any `Varied` input", and it was written precisely to cover this case;
    the "neither" end is anchored by §6.3's golden GIR blob + params key-set equality and the
    "`Varied` input" end by the manual-broadcast reference above, so an implementer reading the
    trigger as "any `Varied` input" would pass both and length-mismatch at execution on a legal
    contexted program): equality against the manually broadcast reference, **plus a witness
    that the seam node was actually recorded** — the fill node's input cone, or a
    `Session.node_count()` delta against the identical fill built with no context handle — plus
    the **execution-time** refusal when a per-object fill hands in an already-flattened value
    alongside a per-event ambient weight (§6.1d: an execution-time `graphed` error naming the
    OFFENDING FACTOR and pointing at "pass the value unflattened"; there is no record-time
    discriminator, so do NOT freeze a record-time raise — **and do NOT freeze `FillEvaluator`
    as the raiser**: under the bound broadcast seam the recorded broadcast node is upstream of
    the fill and fails first (awkward 2.12.0: `ak.broadcast_arrays` over mismatched lengths
    raises e.g. `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size
    7`), so the anchor freezes the MESSAGE CONTRACT at execution time, not a class name; same
    anchor covers an offending EXPLICIT factor, whose message names that factor, not the
    ambient weight; **and the LOOSE-VALUE case as a third assertion** — §6.1d binds a DISTINCT
    message there (it names the offending VALUE, not "the offending factor" and not "pass the
    value unflattened", both of which are the wrong diagnosis for a loose value in the root row
    space), and without this assertion an implementation emitting the anchored factor message
    for it passes every anchor while violating the binding sentence);
    **divergent-lineage detection AT THE FILL** (§2.3e/§6.1d: `h.fill(a_from_ctx1, b_from_ctx2)`
    — handles no op ever combined — is a hard error naming both contexts) **— plus a `sample=`
    assertion**: `h.fill(a_from_ctx, weight=[w_from_ctx], sample=s_from_divergent_ctx)` raises
    the same divergence error naming both contexts (§6.1d makes `sample=` a first-class operand
    of the fill's unification/divergence check; an implementation unifying over `args`+`weights`
    only — the shape today's code invites, since `fill` type-checks `args`/`weights` and
    appends `sample` unchecked — passes every other m48–m51 anchor and fails silently, sampling
    the wrong universe's rows whenever the counts coincide). The raise is record-time, so this
    assertion carries no storage constraint. **AND AT THE OP** (§2.3e's *early detection* half —
    an implementation checking only at the fill would point every diagnostic at the fill line
    instead of the line that mixed the contexts): a binary op over `Array`s from two divergent
    contexts raises AT THAT OP naming both, with a positive control that an ancestor-chain pair
    unifies silently to the most-derived context **AND a SECOND positive control for §2.6b's
    context-IDENTITY rule — two separate `graphed.nominal(sel)` reads (and two separate
    `events[mask]` derivations from one mask) UNIFY rather than raising, since pure derivations
    are canonical; without it the fresh-object-per-call implementation makes them SIBLINGS and
    the divergence error fires on a legal program, and the ancestor-chain control above is a
    different shape that cannot catch it** **AND AT `vary`'s OWN CONSTRUCTION** (§2.1 — `vary`
    is a combining point that no `_array_cls` chokepoint sees, so members carrying divergent
    handles would otherwise be accepted and the loser silently dropped, `graphed.context_of`
    answering with ONE handle — the container's most-derived one, §2.3e): building a container
    from members read through two divergent contexts is a construction-time error naming both;
    **§6.1d link-kind (1) ancestor-VALUE re-indexing, asserted over the VALUE** (link kind (3)
    carries exactly this strengthening "so a guess that unifies but silently mis-weights cannot
    pass", link kind (2) is identity; the §2.6c anchor below is the ambient-REGISTRY re-index,
    a different operation): `h.fill(events.MET.pt, sel.MET.pt)` with `sel = events[varied_mask]`
    compared ELEMENTWISE, label-aligned, against a manually re-indexed reference (each label's
    ancestor value by that label's mask, nominal's by nominal's) — an implementation that
    unifies the handles but never re-indexes the ancestor value must fail it, on the row COUNT
    alone. **Extended with an ancestor-context `sample=`** (§6.1d binds "an ancestor-context
    `sample=` is re-indexed like any other ancestor VALUE"): `sample=events.<field>` alongside
    the same axis values, its per-label re-indexed values compared against the same manual
    reference — **which pins this fixture's histogram to a `Mean`/`WeightedMean` STORAGE**, the
    pin the fold-order anchor already carries and for the identical reason (bh 1.8.0 rejects
    `sample=` on `Double()` and `Weight()`), or the `sample=` half rides the fold-order fixture
    instead. **Both axis values are PER-EVENT, and the fixture MUST NOT be "improved" to a
    per-object second axis** (the spelling `h.fill(events.MET.pt, sel.Jet.pt)` cannot execute
    at all: the evaluator flattens each axis independently
    (`graphed-histogram src/graphed_histogram/boost.py`), and bh requires equal lengths across
    axes — bh 1.8.0, `ValueError: spans must have compatible lengths` — so it would red for a
    reason unrelated to what the anchor asserts, and §6.1d's broadcast seam is scoped to weight
    factors, never axis-vs-axis);
    lineage semantics (`graphed.vary` returns a NEW context and the input context is
    unchanged — a fill from the pre-vary context carries no new label, a fill from the returned
    context does; ancestor-chain inputs unify to the most-derived context);
    **context-handle ORIGINATION** (§2.3e — the merge-from-inputs rule alone gets this wrong,
    since `Session.source` receives no context and `record_op` merges only from `inputs`,
    `python/graphed/session.py`): the same read performed through a `vary`-derived context and
    through its PARENT yields the SAME node id (interning) but DIFFERENT handles, and fills
    from each yield different label sets — the discriminator against an implementation that
    hands `events2.Jet` its parent's handle and silently drops the newly registered universes;
    selection-scoped weight via `vary` on a derived context (parent unaffected) **and the
    derived context's ambient weight re-indexed to the derived row count** (§2.6c —
    **elementwise equality per label against a manually re-indexed reference, not length
    equality**: length equality catches only the named failure of inheriting the parent's
    un-re-indexed members, while the adjacent and likelier bug — re-indexing every label's
    member by NOMINAL's mask, or by whichever label was iterated first — yields right-length,
    silently mis-weighted arrays whenever per-label counts coincide; the manually re-indexed
    reference is already in the test, so comparing values is free. The **varied-mask case
    (per-label row sets) is inside this anchor**, where a length-only check is weakest);
    `graphed.labels` on a context derived by a **Varied** mask (per-label row sets, §2.6c) —
    **asserted as §2.2's UNION on a program that registers a weight BEFORE the derivation**, so
    the answer is ambient-weight labels ∪ the mask's labels in §2.4 order with `"nominal"`
    first, not the mask's labels alone — **plus a SECOND program that discriminates the third
    union term** (in the weight-before-derivation program the varied collections' labels are a
    SUBSET of the mask's labels, since the mask is varied *because* the collection is, so an
    implementation computing ambient ∪ mask and dropping the collection term passes; the
    discriminating case is a shift-varied collection with an UNVARIED derivation mask, where
    the collection is the only source of the shift labels — assert `graphed.labels(ctx)` still
    reports them, and that it remains a superset of the context-borne half of a fill's label
    set, §2.2) — **plus a THIRD program that discriminates the union's THIRD TERM ITSELF**
    (neither program above can: in the first the mask's labels are covered by term (a), in the
    second by term (b), so an implementation computing only (a) ∪ (b) passes both): a context
    derived by a mask varied through the LOOSE §2.1a primitive —
    `mask = gak.num(graphed.vary(events.Jet, "jes", up=j_up, down=j_dn)) >= 4`,
    `sel = events[mask]`, with NO weight registered and NO shift-form `vary` on the context —
    for which terms (a) and (b) are both EMPTY and `graphed.labels(sel)` MUST still report the
    JES labels.
    **§2.2's clause that term (c) SKIPS OVER `vary` identity links is knowingly left
    UNANCHORED**, because no m48–m51-scoped program isolates it: on a `Varied`-mask-derived
    context every read through the context is `Varied` (§2.6c), so a weight registered onto it
    lands in term (a) carrying the mask's labels, and a shift-form `vary` on it stacks onto an
    already-`Varied` collection (§2.1) and lands them in term (b) — either way the answer is
    right under both readings. The clause stays binding for correctness of the verb, on §1.1's
    `"1e1000000000"` precedent; `graphed.universe(ctx, label)`/`graphed.nominal(ctx)` return a
    context that is a CHILD of the argument in the lineage chain (§2.2), so a fill mixing it
    with a read from the argument unifies instead of diverging — **asserted over the resulting
    VALUE, not merely over the absence of the divergence error**: the ancestor-context value is
    PROJECTED to that label per §6.1d's link-kind (3) and compared elementwise against a
    manually projected reference, so a guess that unifies but silently mis-weights cannot
    pass — the fixture is `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)`, **both axis values
    PER-EVENT for the reason §6.1d states** (a spelling like `graphed.nominal(sel).Jet.pt`
    mixes a per-object with a per-event axis and cannot execute: bh requires equal flattened
    lengths across axes — `ValueError: spans must have compatible lengths`) — **and the RESULT
    SHAPE is asserted too: that fill's output is a BARE `hist`** (§6.1a's unvaried shape),
    because §6.1d computes the label set AFTER projection and the projected value carries none,
    while the unified context `graphed.nominal(sel)` contributes none either; without this the
    fixture has two defensible result shapes (`{label: hist}` with per-universe-identical
    contents being the other) and the test-author's pick is frozen read-only. It is also the
    discriminator against an implementation that keeps the labels and projects only the
    contents; **`unweighted=True` in §6.1d's bound form** — it suppresses the AMBIENT weight
    AND any explicit `weight=[…]` (a contexted fill with registrations yields counts equal to
    an unweighted eager reference) **AND the suppressed weight contributes NO LABELS: such a
    fill, whose only variation source is the ambient registry, returns a BARE `hist` (§6.1a),
    not a `{label: hist}` of per-universe-identical counts — the bare shape is the
    discriminator against the labels-kept implementation**, and
    `fill(x, weight=[w], unweighted=True)` is a RECORD-TIME error naming both; data-context
    guard for **both** forms (`is_weight=True` AND a shift-form `vary`, §2.6d);
    lockstep `graphed.vary(events, name, Jet=…, MET=…)` shared-tag-set validation; §1.1 tag
    grammar (kwarg tags + `variations=` numeric-tag escape + every listed rejection); no
    reserved names on the context (a tree branch named `weights` or `vary` stays reachable);
    **the SLICE/INT context-subscript refusal** (§2.6a; `Array.__getitem__` accepts both
    subscript kinds, so the refusal needs its own anchor: `events[0:1000]` and `events[0]` each
    raise naming the supported subscript forms, with the mask and string subscripts as positive
    controls); §2.2 `graphed.universe`/`labels`/`nominal` on both `Varied` and contexts, string
    getitem = field access. The §1.1 grammar anchor MUST cover the e-canonicalization semantics
    **across all THREE tag channels** (§1.1 — including the shift form's inner mapping keys,
    e.g. `Jet={"0.5": …}` → `murf_5em1`, plus a duplicate-after-canonicalization rejection
    INSIDE one collection mapping): float spellings accepted via `variations=`, via
    `**`-unpacking and via a collection mapping (channel-independent) and normalized by exact
    decimal arithmetic (`"2"`/`"2.0"`/`"2e0"`/`"20e-1"` → the ONE label `murf_2`; `"1e-8"` →
    `eps_1em8`; integer PDF indices untouched), **non-minimal canonical-grammar tags
    re-rendered** (`"50em2"` → `5em1`, §1.1), the two readings of "`"0.5"` and hand-typed
    `"5em1"` unify" **split explicitly** (§1.1 — a single "they unify" bullet is freezable
    either way): across TWO `vary` calls the spellings name the identical label `murf_5em1`;
    within ONE call they are a duplicate-after-canonicalization REJECTION, like
    `{"0.5", "0p5"}`. Plus cross-notation numeric-equal pairs rejected (`{"0.5", "0p5"}`,
    `{"2", "2p0"}`) **within one call AND across two stacking calls on the same `name`**
    (§1.1's family definition: a family is one `name`'s tags on one container INCLUDING
    inherited labels, so `vary(ctx,"murf",w_nom,is_weight=True, variations={"0.5": a})` then
    the same call with `variations={"0p5": b}` is rejected — **the pair is spelled in the
    WEIGHT form (b)**: an event-context target with no `is_weight` is overload (c), in which
    `variations=` is REJECTED outright (§2.1), so a `vary(ctx,"murf",variations={…})` spelling
    would freeze the WRONG rejection here — freezing only the within-one-call pairs pins the
    weaker reading), `inf`/`nan`/leading-`+`/underscore/whitespace spellings rejected,
    Python-float (non-string) tags rejected, negative zero canonicalizing to `0` (never `m0`)
    and a >32-character canonical tag rejected (§1.1) **alongside the INTEGER-MAGNITUDE
    rejection as a distinct case** (§1.1 binds two rejections around the cap and freezing only
    the generic one lets an implementation emit the generic message for both and pass every
    anchor while violating the binding sentence, the same shape as §6.1d's loose-value
    message): `"1e40"` (integer-valued, 41 plain digits) is rejected **at canonicalization
    with a message NAMING THE MAGNITUDE**, not with a generic tag-length error, alongside the
    existing `"1e-8"` → `eps_1em8` positive; **plus the CAP-BOUNDARY PAIR that pins the
    digit-count NORMALIZATION** — `"1.5e31"` is ACCEPTED and yields the canonical 32-digit tag
    (`15` followed by 30 zeros, exactly at the cap) while `"1.5e32"` (33 plain digits) is
    REJECTED with the magnitude message **and its NEGATIVE twin `"-1.5e31"` is REJECTED with
    the canonical-tag-LENGTH message** (§1.1 refuses by CAUSE — the magnitude message only when
    the INTEGER digit count alone exceeds the cap, and `"-1.5e31"`'s magnitude is the one the
    adjacent half of this very anchor certifies as LEGAL, so blaming it names the wrong
    property; the real cause is the `m` sign marker taking the rendered tag to 33 characters.
    The two rejections stay distinguishable, which is what the anchor exists to freeze). The
    ACCEPTED half is the discriminating one: the naive "mantissa digits + exponent" the
    normalization exists to replace computes 2 + 31 = 33 and rejects a legal tag, and `"1e40"`
    alone cannot catch that (the naive sum rejects it too, 1 + 40 = 41), so freezing only
    `"1e40"` leaves §1.1's normalization unwitnessed. (The "count BEFORE any rendering" rule is
    knowingly left UNANCHORED — its witness would be `"1e1000000000"`, whose failure mode under
    a render-then-measure implementation is a hang/OOM, not a clean red.) The
    **signature-shadowed names** (`nominal`/`is_weight`/`variations`/`collections` reachable
    only through `variations=` / `collections=` — including `collections`' own self-reference,
    §2.1 — and `variations=` refused in the shift form, **plus `nominal=` refused in the shift
    form with an error naming `collections=`**, §2.1; **the tag `nominal` is LEGAL and yields
    the ordinary label `pu_nominal`, and there is NO "label equals `nominal`" rejection to
    freeze**, §1.1: every label contains a `_` by construction, so that rejection is
    unconstructible), and no label ever containing `.`/`-` — freezing an earlier revision's
    rejections would hard-block this grammar.

- **m49 — shift path + impact + executor end-to-end** (repos: `graphed` + **`graphed-histogram`** +
  `graphed-executors` — the repo list is what the DoD's full-matrix-CI-green-at-the-pinned-revision
  check (R0.5) and per-repo freeze tagging key on).
  Targets: §3.3, §3.4 (frozen anchor), §5, **§7 — EXCEPT §7.2, which lands at m48 (§10/m48)**,
  **§8 — EXCEPT §8.2(i)'s `variation_labels` FIELD DECLARATION, which lands at m48 with §7.2's (β)
  return channel; m49 adds the core accessor, the keying and the POPULATION**, **plus §2.5's
  shift-after-weight diagnostic**, **plus §9.1's per-label projection-stats verb (§5.3; spelling
  pinned at m49 freeze) and the POPULATION of §7.2's seam-half-(β) payload** ((β)'s return CHANNEL
  and §8.2(i)'s FIELD DECLARATION both land at m48 (§7.2 and m48's own target line), so m49's
  residue here is populating `variation_labels` — which the `§8` clause above already carries).
  Frozen anchors:
  - The **full 15-reference matrix**, split across two repos explicitly (the halves have different
    fixture problems):
    (i) **`graphed-histogram`, flat `tests/frozen/m49`** — the matrix through the frontend,
    fingerprint-exact against the 15 stored references, plus a separate run-to-run `array_equal`
    determinism assertion (the m29 dual-assert precedent; "bit-for-bit" is claimed only run-to-run,
    not vs the rounded references). **The §5.2b read witness binds to THIS run**, and like m48's
    matrix this anchor **MUST NOT be guarded by `importorskip`**.
    **This half lives in `graphed-histogram`, not `graphed`**: `graphed` vendors the 15 references
    but lists no `graphed-histogram` in any extra (`pyproject.toml` — `dev` carries
    `boost-histogram>=1.4`/`hist>=2.7` only) while CI installs `.[dev]`
    (`.github/workflows/ci.yml`), and the house pattern there is
    `pytest.importorskip("graphed_histogram")`
    (`tests/frozen/preserve/m30/test_producer_cross_seam.py`), so a fill-based matrix in `graphed`
    would SKIP in CI — silently discharging m49's headline gate AND its single-read mechanism
    witness, with zero frozen-suite diff coverage. After m48, `graphed-histogram` carries the
    corpus dep and the vendored references (m48's bound dependency edit), so it hosts this half
    without a new fixture problem.
    **The per-repo partition covers EVERY m49 anchor, not only (i) and (ii)**:
    `tests/frozen/frontend/m49` in `graphed` keeps m49's NON-fill frontend anchors (§5.2a arena
    delta, §5.2c stage shape, §3.4 impact sets, §5.3 projection, §5.4 refusal) and `graphed`'s
    `tests/frozen/core/m49` keeps the §3.3 benchmark (**not** `frontend/m49` — §10's header pins it
    to `core/m49` and §3.3 says the same, and the unique-basename rule is written for that
    one-process subtree). `graphed-histogram`'s flat `tests/frozen/m49` additionally keeps the
    §2.4/§6.1b structural arity anchor (its operands are `Histogram.staged_fills`/`fill_nodes`,
    `graphed-histogram src/graphed_histogram/boost.py`, and `graphed` lists no `graphed-histogram`
    in any extra, so placed there it would `importorskip`-SKIP). `graphed` gains
    **`tests/frozen/checkpoint/m49`** for §7.3 interrupt/resume and §7.4 dead-letter (the machinery
    is `graphed`'s checkpoint package; `tests/frozen/checkpoint` today holds only `m8`/`m39`, so
    the directory is new and falls under the unique-basename rule — `m8/test_resume.py` already
    exists). §8.1's `__hash__` anchor and §8.2's cross-process/multi-label anchors live in
    `graphed-executors`' flat `tests/frozen/m49` except the §8.2(i) accessor anchor, which is
    explicitly `graphed`'s (below); `graphed` CAN host a spawn-based cross-process test if the
    test-author prefers (`tests/frozen/debug/m6/test_process_boundary.py`).
    **The two remaining m49 anchors are assigned explicitly** (placement is load-bearing for the
    same reason as the matrix: a fill-based anchor placed in `graphed` `importorskip`-SKIPs in CI):
    the **m05 ordering witness** is histogram-observable and goes to `graphed-histogram`'s flat
    `tests/frozen/m49` alongside the matrix it scopes; the **JER-SF stochastic fixture** goes there
    too, since its partition-invariance witness needs a plan run at two `steps_per_file` values.
    **The comparison quantities (§5.5a) are produced by a PLAN RUN — per-partition values
    concatenated in task order — and `Session.materialize` MUST NOT be the oracle**: `materialize`
    is a partition-BLIND API — `materialize(self, array)` evaluates the whole graph in one shot and
    takes no partition and no `steps_per_file` (`python/graphed/session.py`), so quantities
    obtained that way are byte-identical across any partitioning BY CONSTRUCTION and the witness
    cannot observe `steps_per_file` at all — the per-partition `np.random.default_rng(0)` failure
    this witness exists to catch survives it, together with the other four witnesses, which cannot
    discriminate it. The deterministic route exists: `SequentialRunner` folds tasks in SORTED key
    order (`python/graphed/core/execution.py`), so an `aggregate_plan` whose reduce returns
    partition-local arrays and whose combine concatenates is order-deterministic.
    (ii) **`graphed-executors`, flat `tests/frozen/m49`** — the same matrix through a process-pool
    executor (the `graphed` repo ships no `Executor` implementation — the executors live in
    `graphed-executors`; `graphed`'s only cross-process frozen test is the M6 error-transport pool,
    `tests/frozen/debug/m6/test_process_boundary.py`). Two fixture facts bind the shape: the 15
    stored references are NOT reachable from the `graphed-corpus` wheel (it packages only
    `src/graphed_corpus`, `pyproject.toml`, while the reference JSONs live in the repo directory
    `corpus/references/`), and `graphed-histogram` is **not** a dependency of `graphed-executors`
    (`pyproject.toml`). Because this half must exercise §4.2/§6.1's varied-fill lowering — the
    whole point of a weight-variation matrix — **m49 adds `graphed-histogram` to
    `graphed-executors`' `dev` extra AND binds the install pair, exactly as m48 does for the
    corpus** (a name-only dev-extra entry is insufficient in this org: `graphed-histogram` IS on
    PyPI at version `0.0.1`, the same as the repo's own version, so the name resolves to a release
    that predates m48's varied-fill work and is not even distinguishable by version;
    `graphed-executors`' workflow pre-installs only `GRAPHED` and `CORPUS` from git URLs
    (`.github/workflows/ci.yml`) and nothing pulls `graphed-histogram` from HEAD): m49 adds a
    **`HISTOGRAM` git-URL workflow env var plus its `pip install` line in every job that runs
    `tests/frozen`** (`ci.yml`) alongside the dev-extra name. **This anchor MUST NOT be guarded by
    `importorskip`** either.
    It compares against corpus references recomputed in-process via `graphed_corpus` (the m7 house
    pattern, `tests/frozen/m7/adl.py`). The materialize-then-fill-eagerly alternative is explicitly
    NOT chosen: it reproduces the numbers while exercising none of §4.2/§6.1/§6.2.
    This is the executor-level systematics end-to-end no frozen test currently discharges
    (cba §corpus §4).
  - m05 ordering witness (`jes_up > nominal > jes_down`) through graphed — explicitly scoped to
    the monotone JES fixture (§5.1); the suite MUST NOT assert ordering for any other shift.
  - A **JER-SF-style stochastic shift fixture** (additive — corpus m05 tests/references
    untouched): content-seeded re-smearing per §5.5, one shared draw, SF-varied per label.
    Witnesses: run-to-run byte-identical results (content-seeded stochasticity survives the
    determinism gate); selected counts pairwise distinct across {nominal, jer_up, jer_down} with
    NO ordering asserted, plus **bidirectional migration** (no universe's selection mask is a
    subset of another's — the non-monotone discriminator); the shared random-draw node
    interned ONCE across all universes (mechanism witness, §5.5b); **and PARTITION INVARIANCE — the
    identical event set run at two different `steps_per_file` values yields byte-identical
    per-label SMEARED VALUES and selection MASKS** (a weighted float histogram is NOT byte-invariant
    under a re-partitioning even for a correct implementation, since the combine tree regroups the
    float additions, §5.5a; the other four witnesses cannot discriminate the failure §5.5(a)
    actually forbids: a constant-seeded `np.random.default_rng(0)` per partition is reproducible,
    migrates both ways and still interns as one draw node, so it passes all four while giving the
    same event a different smear under a different partitioning — a data-dependent nondeterminism
    the determinism gate, which holds partitioning fixed, never sees. Deterministic invariant,
    R0.10a-safe).
  - §5.2 witnesses (a: arena delta vs an independently hand-built oracle; c: reduced-stage shape
    vs the same-topology no-`vary` ORACLE — not a frozen literal and with NO post-freeze
    re-measurement clause, §5.2c).
  - **§2.5 shift-after-weight diagnostic** (§2.1/§2.5, using §3.4 which lands here): a weight
    factor registered BEFORE the `vary` that replaces a collection its cone reaches is reported,
    naming both; the positive control is the correct order (weight registered after the shift),
    which reports nothing.
  - §3.4 impact-set anchor: three labels where two share a derived node — the shared node appears
    in both impact sets; result independent of expansion order. **The FIXTURE is stated** (the same
    mid-freeze-discovery service m48 gives `gak.full_like`, `stable()` rounding, `h.axes.name` and
    the pt-cut jets): the sharing must be UPSTREAM of the fork — the two varied members have
    DIFFERENT expressions that both consume ONE derived node the nominal member does not use. **A
    node DOWNSTREAM of the fork can never be shared by two labels with distinct members**, since
    interning keys on input ids (`src/store.rs`: two syntactically identical expressions over the
    same inputs intern to one node). Assert all three: `u ∈ impact(up) ∩ impact(down)`,
    `u ∉ reachable(nominal)`, **and `impact(up) ≠ impact(down)`** — the last conjunct is what the
    identical-member form (`vary(x, "jes", up=e, down=e)`, which belongs in m48's §1.2 dedup anchor
    where it already lives) cannot carry, since there the two impact sets coincide and "appears in
    BOTH" is satisfied by returning one set twice or by unioning. The id-WATERMARK implementation
    §3.4 rejects is still red on this fixture (it hands the second label an impact set missing
    `u`).
    **The FIXTURE is built through the public `graphed.vary` surface** — a raw-`GraphStore`
    construction cannot be the fixture: §3.4's verb takes labelled containers
    (`Sequence[Varied] | Mapping[str, Sequence[Array]]`), which a raw `GraphStore` cannot supply at
    all — no Session, no `Array`s, no labels. The frontend spelling is cheap: `k = src * 2.0`, two
    different expressions over `(src, k)` as the two varied members, the unvaried target as
    `"nominal"`.
    **This is the same construction §8.2(i)'s m49 anchor already builds** ("one derived node
    consumed by TWO NON-nominal universes"), so the two anchors MAY share one fixture.
  - §2.4/§6.1b structural no-cross-product count — **in SIBLING mode** — `1 + |S| + |W|` fill
    nodes (axis mode's `1 + |S|` is m50, §6.2; word the anchor so it does not freeze a general rule
    m50 must contradict — the same scoping the m48 §6.1a anchor and §6.1b's own prose carry).
  - §5.3 projection-union test — **over a FLAT source** (branch-per-column
    `Jet_pt`/`Jet_eta`/`Muon_pt`, the shift's extra column being the top-level `Jet_eta`):
    `read_columns` counts a `field` op only when its input IS the source node (`projection.py`), so
    on a NESTED record both `[events.Jet.pt]` and `[events.Jet.pt, events.Jet.eta]` report
    `('Jet',)` and a nested `Jet.eta` example is unsatisfiable against a correct implementation —
    **including the per-label projection stats** reporting the shifted label's extra column (§5.3;
    the union-growth assertion alone leaves the stats surface unanchored), **read through the §9.1
    verb whose shape §5.3 pins** (`{label: tuple[str, ...] | None}`, sorted per label; spelling
    pinned at m49 freeze) — **with a CONSERVATIVE label in the same fixture** (one gak op applied
    directly to the source, for which `read_columns` returns `None` = "read every column",
    `projection.py`), asserting that label maps to `None` and not to `()` — **the conservative
    label riding a SEPARATE program (or a separate output set) in the same test module**:
    `read_columns` carries ONE `conservative` flag across all the arrays passed and returns `None`
    if any one of them consumes the whole record (`python/graphed/projection.py`), so a
    conservative label inside the SAME varied program collapses the union to `None` and the
    union-growth half degenerates to `None == None` (vacuous) or goes red against a correct
    implementation. Equivalently, state the growth half per label through the stats verb
    **order-insensitively**: `set(stats["jes_up"]) - set(stats["nominal"]) == {"Jet_eta"}` AND
    `set(stats["nominal"]) - set(stats["jes_up"]) == set()` — NOT a plain concatenation, which is
    red because both returns are sorted (`projection.py`) and on this fixture `Jet_eta` sorts
    FIRST;
    §5.4 refusal + positive control.
  - §3.3 NEW frozen variation benchmark file (exact `stages == N+1`, `reduced == 2N+2`, linear
    bound).
  - **§8.2(i) accessor + keying, in `graphed`** — the bullet straddles two homes: the accessor
    half in `tests/frozen/frontend/m49` (a `compile_ir`-shaped program) and the plan-byte
    determinism half in `tests/frozen/checkpoint/m49` beside §7.3, whose
    module-level-`DurablePlan`-by-value construction it shares verbatim; both under the
    unique-basename rule. Placement is mechanically load-bearing: `frontend` runs one pytest
    process per milestone subdir while `core`/`checkpoint` run one per package
    (`graphed scripts/run-tests.sh`, `SUITES` and `SPLIT_PKGS="frontend numpy awkward"`), and that
    scope is what the basename rule is keyed on. The accessor is an m49 Implementation Target in
    `graphed`, and the DoD requires ≥90% diff coverage from that repo's own frozen suite, so its
    coverage cannot live only in `graphed-executors`: over the §3.3 builder topology — **built
    through the frontend `compile_ir` path, since that is the key space the accessor answers in,
    and EXTENDED with one deliberately unmarked branch** (§3.3's builder marks every universe's
    terminating reduction as an output, so nothing in that topology is dead and the DCE clause
    below has no operand) — every surviving record id maps to a `(reduced_id, member_index)` whose
    reduced id **is a node id of the compiled reduced store** ("in the compiled output/stage set"
    is false for the SOURCE record, whose reduced node is neither an output nor a stage: reduced
    kinds on this topology are `{source: 1, stage: N+1, reduction: N}`), the unmarked branch's
    record id maps to `None`, and — **on a topology EXTENDED a second way: one derived node
    consumed by TWO NON-nominal universes** — that node maps to ONE `(reduced_id, member_index)`
    key **reached from BOTH labels' record cones, i.e. the accessor's image collapses two labels
    onto one key, which is what any label map over that key space must be SET-VALUED to represent**
    (the PAIR key space §8.2(i) declares). **The clause is worded over the ACCESSOR here, not over
    `variation_labels`** — that field's only bound PRODUCER is `graphed-histogram`'s group-plan
    builder (§8.2(i), §7.2), and this anchor is a `compile_ir`-shaped program in `graphed`, where
    no `aggregate_plan` call, no hook and no `_PartitionReduce` exist and §2.3d bindingly REFUSES a
    `Varied` output, so the three ways to write the clause over `variation_labels` here are all
    defective: the test supplying its own hook (the self-derived trap §5.2a names), an
    `importorskip` on `graphed_histogram` (a CI SKIP silently discharging the gate) or reading the
    accessor's own map, which carries no labels at all. Two labels' shared record ids are recovered
    from §3.4's impact verb (an m49 surface, §9.1), which IS the `graphed`-side label→record-id
    channel; the LABEL association itself is anchored in `graphed-histogram`'s flat
    `tests/frozen/m49` (below).
    That extension is what makes the clause non-vacuous: §3.3's builder gives each universe its own
    fork + K chain ops + terminating reduction off a shared prefix, so no node is shared by two
    labels in §3.4's sense ("shared by `jes_up` and `jes_down` but not nominal") — prefix nodes are
    shared by ALL labels including nominal — and "two labels' shared node maps to ONE reduced id"
    degenerates to "the map is a function", which it is by type. The extended form is the actual
    non-vacuity witness for §8.2's SET-VALUED keying claim (the same repair the DCE clause
    carries).
    **Plus a PARTITIONING clause the §3.3 topology makes exact** (without it every clause above is
    satisfied by a degenerate constant map `record_id -> (one_stage_id, 0)`: (1) "maps into the
    output/stage set" holds trivially, (2) the `None` for the unmarked branch is DCE reachability
    the implementation computes anyway, and (3) "one key reached from both labels" holds *a
    fortiori*, since one key then collects every label — while the real discriminator, the
    executors' single-label `variation == "jes_up"` anchor, lives in another repo): the
    shared-prefix record ids all map to ONE reduced id, each universe's chain maps to a reduced id
    DISTINCT from every other universe's, and the map's image over the WHOLE topology has exactly
    **2N + 2** distinct reduced ids, of which exactly **N + 1** are of kind `stage` — matching the
    `reduced_nodes == 2N + 2` / `stages == N + 1` shape §3.3 already pins. The accessor is bound
    over EVERY surviving record id, which on this topology includes the source and each universe's
    terminating reduction — neither of which is a stage — so a frozen
    `len({rid for rid, _ in m.values()}) == N + 1` reds a correct accessor by ~2×. Both halves stay
    non-degenerate against the constant map the clause exists to catch, since it fails the
    per-universe-distinctness half.
    **The cardinality clause is asserted on the BASE fixture (± the unmarked dead branch) ONLY, and
    NOT on the shared-node extension** (the anchor names two extensions of one topology; a
    test-author who economically builds ONE fixture carrying both extensions freezes a literal a
    CORRECT accessor fails): the dead branch changes nothing — DCE removes it — so the base fixture
    gives `2N + 2` reduced ids / `N + 1` stages either way, while adding one derived node consumed
    by TWO non-nominal universes gives `2N + 3` / `N + 2`. The shared-node fixture carries the
    BOTH-labels clause; the cardinality literals stay with the base one.
    Plus **plan-byte determinism with the §8.2(i) field present** — the field reaches the shipped
    closure through §7.2's seam half (β), so this anchor is also (β)'s frozen coverage: the same
    varied program built in two fresh processes under differing `PYTHONHASHSEED` yields
    byte-identical `DurablePlan.to_bytes()` and identical per-partition `task_id` (the plan-level
    twin of §3.2's IR-level m48 anchor; needed because a `frozenset` field pickles in hash order,
    §8.2(i)).
    **The fixture's plan construction is part of the anchor, because both halves are load-bearing**
    (§7.3): the `DurablePlan` is built BY VALUE over the plan `aggregate_plan` returned —
    `DurablePlan(ir=…, process=OpSpec.from_callable(plan.process), …)`, never `OpSpec.from_ref`,
    since `identity()` for `kind="ref"` is `b"ref\0" + ref` (`python/graphed/core/plan.py`) and
    would keep the closure's fields out of the plan bytes entirely, freezing this anchor GREEN
    against the very `frozenset` §8.2(i) bans — **and every closure operand (the
    `PartitionedSource`, reduce/combine/empty) is a MODULE-LEVEL definition in an importable
    module**, since a by-value-pickled `__main__` class makes the plan bytes seed-dependent
    regardless of `variation_labels` and would make the anchor red against a correct
    implementation.
  - **`variation_labels` POPULATION, in `graphed-histogram`'s flat `tests/frozen/m49`** (the label
    half of the anchor above: the field's only bound producer is that repo's group-plan builder
    (§8.2(i)), so this is where it can be witnessed without a self-supplied hook or an
    `importorskip`): over a varied program, `gh.plan({…})`'s shipped closure carries a
    `variation_labels` entry whose label tuple is SORTED and, for a `(reduced_node_id,
    member_index)` key two labels' cones both reach, carries BOTH labels — the set-valued half the
    `graphed` accessor anchor can only witness as a key collapse. **The fixture's shared node is
    UPSTREAM of the label fork (the §3.4 shape)**: distinct labels have distinct FILL nodes by
    §6.1b's `1 + |S| + |W|` count, so no fill-node key is ever reached by two labels and the
    witness exists only under §8.2(i)'s bound cone-walk producer.
  - §8.2 cross-process labeled StageError (incl. §7.4 dead-letter label) **plus the shared-node
    multi-label RENDERING half** (without it the single-label anchor passes under a
    pick-one-arbitrarily implementation); §7.3 interrupt/resume byte-identity **over a
    `DurablePlan` built by value exactly as the §8.2(i) anchor above builds it** (under
    `OpSpec.from_ref` the `process` would be a hand-written module-level callable over a hand-built
    IR, exercising no varied lowering at all). **Plus §8.1's `__hash__` participation explicitly**:
    `__eq__` compares `self.__dict__` so a new field participates for free, but `__hash__` is a
    hand-written tuple that must be edited (`python/graphed/debug/errors.py`) — assert two
    `StageError`s differing ONLY in `variation` are unequal **AND hash differently**, or the
    omission is invisible to the cross-process label anchor.
- **m50 — scale + integration** (repos: `graphed-histogram` + `graphed` preserve/docs).
  Targets: §6.2, **§6.1c's AXIS-MODE slot** (the `(output, None)` keying and the per-slot spec
  taken from the fill node; §6.1c defines no per-output MODE field — the three slot key forms are
  disjoint and per output, so the unpacker reads the shape off the keys — and the COMBINE needs no
  branch on a per-slot value type: `_add_groups` is a key-wise `+`, `graphed-histogram
  src/graphed_histogram/boost.py`; m50's scaling anchor consumes exactly this), **§9.1's
  `graphed.variations`** (the rest of §9.1 is an m48 target) **plus §9.1's plan-level
  `{output: [labels]}` listing** (own anchor below) + §9.2. Frozen anchors:
  - Variation-axis fill equals sibling-fill results bin-for-bin on the corpus **weight** labels,
    AND a mixed shift+weight program lands in ONE axis-mode histogram equal to its sibling-fill
    decomposition (§6.2, scalar-labeled shift siblings); combine-safety across partitions
    (identical spec, deterministic label order). **The mixed program carries a label borne ONLY by
    a `Varied` `sample=`** (§6.1b's `S`/`W`-by-lowering definitions are binding and this is the
    only place they are witnessable: sibling arity `1 + |S| + |W|` counts every label once whatever
    its class, so m49's arity anchor is green under either reading, while axis mode's `1 + |S|`
    counts `S` and collapses `W`): that label must lower as a SIBLING — it counts in `S`, since the
    evaluator's weight loop re-fills with different weights against a FIXED sample column — and the
    axis-mode result still equals its sibling-fill decomposition. Without it an implementation
    classing a sample-only label into `W` passes every m48–m49 anchor and silently produces one
    sample column reused across universes. **The fixture MUST use a `Mean`/`WeightedMean` storage
    and per-label sample values that DIFFER (§6.1b)** — bh 1.8.0 raises `TypeError: Keyword(s)
    sample not expected` for `sample=` on `Double()` and `Weight()`, and the evaluator passes
    `sample` straight to `h.fill` (`graphed-histogram src/graphed_histogram/boost.py`), so a
    default-storage fixture dies at evaluation against a correct implementation and a
    sample-discarding storage makes the equality vacuous. **Plus the per-fill CARRIER witness**
    (§6.2): in the mixed program the `1 + |S|` axis-mode fill nodes carry **distinct External
    `content_hash`es and resolve to distinct evaluators** — without it every sibling resolves to
    the one evaluator registered last (the registry is keyed on `content_hash(self._spec)` alone
    and merged across histograms, `graphed-histogram src/graphed_histogram/boost.py`;
    `evaluate_ir` dispatches by `nd["descriptor"]["content_hash"]`,
    `graphed python/graphed/execute.py`), which the bin-for-bin equality can mask whenever two
    siblings happen to agree.
  - **MIXED-MODE PLAN — mixed-mode UNPACKING and the per-slot SPEC**: one `plan(...)` call
    carrying an axis-mode output AND a sibling-mode varied output together, plus a third output no
    variation reaches. **What it witnesses is the unpacking and the per-slot spec, NOT a per-output
    MODE field** — §6.1a/§6.1c make the three slot key forms disjoint and per OUTPUT, so an
    implementation that never records a MODE passes every assertion here exactly as it passes the
    single-mode ones; §6.1c accordingly defines no such field, and §9.1's one-argument
    `unpack(value)` is consistent with that. Every other m50 anchor is single-mode (the equality
    anchor compares two separate programs, the scaling anchor pins the fixture's output count at 1,
    (i-bis) is one axis-mode histogram, the declaration/mode-mismatch anchors concern one
    histogram), so this is the only program that reaches the mixed unpack at all. Assert:
    the axis-mode output unpacks to a BARE variation-axis histogram, the sibling-mode output to
    `{label: hist}`, the unvaried output to a BARE `hist` under its bare key (§6.1a), all narrow
    through `graphed.labels`/`graphed.universe`, and all are bin-for-bin correct. **Plus a FOURTH
    output — axis-mode opt-in, NO variations — asserting its slot key is `(output, None)` and that
    it unpacks to a bare histogram carrying a 1-bin variation axis**: §6.1a/§6.1c's rule that the
    MODE, not the variation count, decides an axis-mode key is directly witnessable here (these
    anchors assert the plan value's KEY SET), and the three outputs above give the unvaried one a
    BARE key, i.e. sibling-mode, so an implementation keying an unvaried axis-mode output bare
    would pass every m48–m51 anchor while contradicting the rule. Cost: one histogram in an
    existing fixture. **That same histogram carries §6.1c's axis-mode arm, one line: `.plan()` on
    it RAISES the §6.1c refusal naming the group API** — it is unvaried, so m48's varied-only
    trigger would let it through into an opaque `ValueError: axes have different length` from
    `_SumFills`' `__init__`-time spec (bh 1.8.0; `_SumFills(self._spec)` over
    `self._spec = spec_of(self)`, `graphed-histogram src/graphed_histogram/boost.py`).
    (It also exercises `_GroupZero`'s per-slot spec across two DIFFERENT specs —
    `graphed-histogram src/graphed_histogram/boost.py` — which nothing else in m48–m51 reaches.)
  - **§6.2 declaration contract** (scoped to the frontend-declared-only rule §6.2(ii) binds;
    user-declaration behaviour is behaviour today's `Histogram.fill` cannot accept — it requires
    one array per axis, `graphed-histogram src/graphed_histogram/boost.py`): the declared bin set
    equals the §6.1d inferred label set EXACTLY — **two assertions, because one direction is
    invisible to the flow check**: `h.sum(flow=True) == h.sum()` catches an UNDER-declaration (bh
    1.7.2 and 1.8.0: filling three labels into a two-bin declaration gives `sum 2.0` vs
    `sum(flow=True) 3.0`), while an OVER-declaration — a declared bin no fill reaches — passes it
    unchanged (bh 1.8.0: four declared bins, three labels filled,
    `sum == sum(flow=True) == 3.0`), so the closing half asserts the axis's bin tuple against a
    LITERALLY spelled expected label list, never one read back from the histogram or from
    `graphed.labels(h)` (which §6.2(i-bis) DERIVES FROM the axis bin set — so the comparison is
    circular on CONTENT regardless of order); a second fill whose inferred label set differs from
    the first's is a hard error naming the mismatch (§6.2 i, cross-fill agreement); **plus the
    MODE-mismatch error** (§6.2(i): a second fill into the same histogram in the OTHER mode —
    first fill axis-mode, second sibling-mode — is a hard error naming both, since a mixed
    histogram yields both §6.1c key forms for one output and two contradictory result shapes);
    **and a user-constructed histogram that already carries a `"variation"` axis is refused with an
    error pointing at the opt-in mode** (user-declared axes are §11) — **with the RECOGNITION RULE
    and the fixture spelling bound**: recognition is `axis.__dict__.get("name") == "variation"`
    (the §6.2(i-bis) name carrier; `graphed-histogram src/graphed_histogram/_spec.py` round-trips
    it), the fixture sets the name that way because `bh.axis.StrCategory(..., name="variation")` is
    itself a `TypeError` (boost_histogram 1.7.2 and 1.8.0, §6.2 i-bis), and a user `StrCategory`
    under ANY OTHER name is untouched — the frontend still appends its own variation axis. Without
    the rule the plausible alternative ("any `StrCategory` axis") would refuse a legitimate user
    category axis (a region axis) and freeze that refusal read-only. There is no "undeclared label
    at fill" or "unsorted user-supplied bin order" anchor — under frontend declaration neither
    state is reachable.
  - **§6.2(i-bis) axis-mode result shape**: an axis-mode varied output is a BARE histogram
    carrying the variation axis (name in `axis.__dict__["name"]`, §6.2(i-bis) — **the name is read
    per axis, and `h.axes.name` MUST NOT be the oracle**: `bh` maps that attribute over EVERY axis
    and raises when one lacks it, so on any real axis-mode histogram, which has ≥1 value axis
    alongside the variation axis, it is an `AttributeError` against a CORRECT implementation (bh
    1.8.0); the surviving invariant is that the name round-trips `spec_of`→`zero_of`,
    `[a.__dict__.get("name") for a in z.axes] == [None, "variation"]`), and `graphed.labels(h)`
    (**and `graphed.nominal(h)` — §2.2 binds it to `graphed.universe(h, "nominal")` on this shape,
    i.e. the nominal SLICE, not the whole histogram; same manually-sliced oracle, one extra
    assertion**) returns the axis bin set **re-ordered to §2.2's rule — `"nominal"` first, then the
    remaining bins in axis order — while the stored bin order stays lexicographic** (§6.2(i-bis);
    assert both, since a family whose lexicographic first bin is not `"nominal"` is the
    discriminating case) and NOT `["nominal"]`, while `graphed.universe(h, label)` returns that
    label's slice along it — the narrowing helper uniform over all three shapes (§6.1a
    bare-unvaried, `{label: hist}`, bare-axis-mode). **Worded over SEMANTICS, not over a literal
    subscript expression**: the oracle is equality against a manually sliced reference, because
    `h[{"variation": label}]` raises on a bare `bh.Histogram` — on boost_histogram 1.7.2 AND 1.8.0,
    `TypeError: list indices must be integers or slices, not str` (and `StrCategory(..., name=...)`
    is itself a `TypeError`); only the positional `h[{axis_index: bh.loc(label)}]` works.
  - The §6.2 scaling claim frozen **structurally** (R0.10a: no wall-clock in frozen tests): per
    partition, axis mode ships **1 combine payload entry** vs `N+1` in sibling mode — the length of
    the per-partition combine payload under §6.1c's key shape: one entry per `(output, label)` in
    sibling mode, ONE entry `(output, None)` in axis mode (§6.1c), with the fixture's output count
    pinned at 1 **and the fixture scoped to WEIGHT labels only** (under a mixed shift+weight
    program the axis-mode side still records `1 + |S|` fill nodes, and the 1-vs-`N+1` count is only
    unambiguous when every label collapses into the evaluator loop; the mixed program is frozen by
    the adjacent equality anchor, which does not count slots). Today `_GroupReduce.__call__`
    returns a mapping whose key is the OUTPUT name, not a variation label (`graphed-histogram
    src/graphed_histogram/boost.py`); the 1-vs-`N+1` count only holds once §6.1c's two-level
    `{(output, label): hist}` shape exists. Plus bin-for-bin equality. The "allocates 1 histogram
    object" half is NOT part of the frozen anchor: counting allocations needs monkeypatched
    production code or a `gc`/`tracemalloc` heuristic, neither bound anywhere here and both fragile
    across the §A.5 matrix; the object-count claim goes to the R0.11 implementer report alongside
    the wall-clock half. The N≈100 wall-clock sibling-vs-axis comparison is an
    **implementer-report measurement under R0.11** (methodology stated: what is warmed, timed, held
    constant) — NOT a frozen gate.
  - §9.2 one-bundle-N-labels preservation (m9 comparison form, on the bound varied
    `build_bundle`/`reproduce` surface — with the backward-compat control that an unvaried bundle
    still returns a BARE array) + `inspect()` label listing (§9.1) — **plus the `FORMAT_VERSION`
    bump** (two cheap assertions on fixtures this anchor already builds: the varied bundle's
    manifest carries `format_version == <the bumped value>` and the unvaried control still carries
    `1`, `python/graphed/preserve/manifest.py`). Without it §9.2's bound bump is invisible to every
    anchor here — the label map is exercised behaviourally whether or not the version moves —
    while the bundle fingerprint is the SHA-256 of the canonical manifest (`manifest.py`), so an
    unbumped varied bundle is indistinguishable by version from a v1 bundle a v1 reader mis-parses.
  - **§9.1's plan-level `{output: [labels]}` listing, its OWN anchor** (m50's `inspect()` test
    takes a `Bundle` and returns a `str`, `python/graphed/preserve/bundle.py`, and cannot exercise
    a plan-level mapping): **in `graphed-histogram`'s flat `tests/frozen/m50`, NOT in `graphed`**
    (the anchor is fill-shaped: a named OUTPUT exists only in `graphed-histogram`'s group API
    (`plan(histograms: Mapping[str, Histogram] | Sequence[Histogram])`, `items = [(str(k), v) …]`,
    `graphed-histogram src/graphed_histogram/boost.py`), while `graphed`'s own
    `aggregate_plan(*outputs: Array, …)` carries no output names at all
    (`python/graphed/aggregate.py`), and the anchor's own wording leans on §6.1a's bare-`hist`
    rule; placed in `graphed`'s `tests/frozen/preserve/m50` its fixture needs `graphed_histogram`,
    which `graphed` declares in no extra (`pyproject.toml` vs CI's `.[dev]`,
    `.github/workflows/ci.yml`), so the house `pytest.importorskip` pattern
    (`tests/frozen/preserve/m25/test_histogram_preservation.py`) would SKIP it in CI), over a
    TWO-output varied program — one output reached by variations, one not — the listing maps each
    output to its labels in §2.4 order, and the unvaried output maps to **`["nominal"]`** (`[]` and
    `["nominal"]` are different frozen assertions that §6.1a does not settle, since it fixes the
    HISTOGRAM shape, not the listing's; `["nominal"]` is the consistent choice because §6.1a
    already binds a bare `hist` to READ as the single label `"nominal"` through the narrowing
    helper).
  - **§9.1 `graphed.variations(ctx)`** (load-bearing because §6.2 explicitly refuses to give
    numeric ordering from bin index): per-name tags and kinds — **over §9.1's shape
    `{name: {tag: (kind, value | None)}}` with the two-word kind vocabulary `"weight"`/`"shift"`,
    so the fixture registers ONE of each and asserts both strings** — plus the parsed float value
    under **both** parsers — canonical e-form `m?\d+(em\d+)?` (`5em1` → 0.5, `m15em1` → −1.5) and
    datacard p-form `m?\d+(p\d+)?` (`2p5` → 2.5) — and a non-numeric tag (`up`) returning no value
    rather than raising.
  - Docs: a "How variations work" design.rst section with **executed** examples (the docs-sweep
    rule) covering §7.3's limitations explicitly — **all three invalidation classes, each with the
    scope §7.3 binds**: the IR-level one (adding/removing a variation) is unconditional, while the
    label-RENAME class and **m48's** one-time closure churn (§7.2's (β) return channel puts
    §8.2(i)'s field on `_PartitionReduce` at m48, and adding it is what changes the pickled state —
    one defaulted field flips the cloudpickle digest, §7.3 — while m49 only POPULATES it, so
    attributing the churn to m49 would put a false milestone attribution in the user docs) apply
    only to journals whose `DurablePlan.process` `OpSpec` embeds the worker closure BY VALUE — the
    documented `OpSpec.from_ref` idiom (`docs/checkpoint/design.rst`) is unaffected. An unscoped
    churn sentence would put a false claim in the user docs (§1.2/§7.3).

- **m51 — variation-aware write-out (skim augmentation)** (repos: `graphed` +
  `uproot5-graphed-mvp`). Targets: §6.4, **plus §9.1's `graphed.selection` and §2.3d's `to_parquet`
  table entry**. Frozen anchors:
  - Superset-row anchor, against an **INDEPENDENT** reference (under §6.4a's "the OR is recorded
    as ordinary graph ops over the per-label masks", a reference taken from the same varied graph
    degenerates to `OR(masks) == OR(masks)` for any wrong per-label mask — the self-derived trap
    §5.2a names): the per-label reference row sets are computed **eagerly with plain awkward,
    outside graphed**, from the same input events (the `m23/test_group_plan.py` and `m7/adl.py`
    house pattern); the written row set MUST equal their union, and each universe's reconstructed
    rows MUST equal that universe's eager row set.
  - Bit-exact round-trip: write an augmented skim → the §6.4e reader reconstructs every
    universe's post-selection values and row set bit-for-bit vs the in-memory varied run (the m9
    comparison form). **Its coverage items MAY be SEPARATE fixtures** — they exercise
    different record shapes (a depth-1 collection for the object-migration case, a depth-0 stored
    factor for the weight-only one), and §6.4a's field-scoped level channel makes one mixed
    record legal but not required — covering a shift with object-level migration (per-label inner masks,
    §6.4d, **written through the per-LEVEL, FIELD-SCOPED
    `select={0: event_mask, ("Jet", 1): jet_mask}` channel** (the level-≥1 entry names its
    field; §6.4a) — **so this fixture's written record is the MULTI-FIELD one (`{Jet: var * {…}, …}`,
    where a field path is what disambiguates depth 1), while §6.4's canonical single-collection skim
    (`to_parquet(events.Jet, …)`, form `var * {…}`) uses §6.4a's BARE depth-`k` key; state which
    shape each coverage item writes, since the two key forms are not interchangeable** —
    **and AT LEAST ONE round-trip coverage item MUST be that bare-key skim, written as
    `to_parquet(events.Jet, select={0: event_mask, 1: jet_mask})`** (with the coverage items
    separable, a conforming suite could otherwise write every level-≥1 item field-scoped and leave
    §6.4a's bare-key branch — new m51 source — with zero frozen-suite diff coverage under the DoD's
    ≥90% gate, which excludes `tests/extra/**`) —
    §6.4a's per-level channel is what makes this anchor satisfiable at all; a single row mask
    cannot express it),
    a weight-only label **whose stored factor is in the RECORD's own row space — `graphed.weight(c)`
    for a `c` reached from the record's context across `vary` IDENTITY links only** (§6.4b's
    row-space precondition: a selection-scoped `graphed.weight(sel)` is NOT storable and is refused
    at the entry check, so naming the storable spelling here keeps the anchor buildable), a label
    structurally equal to nominal (all-zero delta) — **which is also the OUTPUT-COLLAPSE case, and
    the anchor witnesses the REPLICATION, not only the all-zero content** (`mark_output` de-dups in
    `src/store.rs`, so `evaluate_ir` returns FEWER values than marked outputs and a positional
    unpack in `_WritePart` misassigns every label after the collapsed one — silently, since an
    all-zero delta is exactly what one expects there; §6.4f binds resolution BY NODE ID) — and an
    e-canonical numeric-tag label (`murf_5em1`): stored names embed the label verbatim and the
    reader returns the same label.
  - **`graphed.selection(ctx)` bridge** (§6.4a/§9.1): a skim written from the §2.6 context
    idiom — `to_parquet(events.Jet, select=graphed.selection(sel))` where `sel = events[mask]` —
    round-trips identically to the same skim written with the mask passed by hand;
    `graphed.selection` on a ROOT context returns `None`. Without it the m51 sink is reachable
    only from the loose §2.1a style, one milestone after §2.6 makes the context the primary idiom.
    **Plus the `vary`-derived-context case explicitly** (§6.4b's stored varied weight factors
    are reached through `graphed.weight(ctx)`, so the weight-storing skim is written from a
    weight-`vary`-derived context by construction): with
    `sel2 = graphed.vary(sel, "btag", …, is_weight=True, …)`,
    `to_parquet(events.Jet, select=graphed.selection(sel2))` is ACCEPTED by (2a) and round-trips
    identically to the pre-`vary` spelling (§9.1: `graphed.selection` walks `vary` identity
    links; §6.4a(2a) admits them). **Plus the control that discriminates §6.4a(2a)'s
    `vary`-link admission from bare handle equality** (in the bullet
    above the `vary` link sits BELOW the mask derivation, so the mask still carries the record's own
    handle and both readings ACCEPT): with `E2 = graphed.vary(E1, "pu", …, is_weight=True)`,
    `mask = gak.num(E2.Jet) >= 4`, `sel = E2[mask]`, the write
    `to_parquet(E1.Jet, select=graphed.selection(sel))` — record handle `E1`, mask handle `E2`,
    identical row spaces (a `vary` link is §6.1d kind (2), IDENTITY) — is ACCEPTED and round-trips
    identically to the same skim written from `E2`. Bare handle equality REFUSES it — the same
    hard-block-a-legal-spelling defect class the absent-operand case (ii) wording guards against.
    **Plus the RE-RECORDED-MASK positive control for §6.4a(2a)'s handle-equality predicate
    (an implementer shipping `mask is ctx._selection` would pass
    every other m51 anchor and refuse a legal program forever)**: a `select=` value that is a
    RE-RECORDED equal expression — a distinct Python object carrying the record's context handle and
    the same per-label node ids — is ACCEPTED and round-trips identically (hash-consing gives a
    re-recorded equal expression the same node id on a distinct Python object).
    **Plus the UNIVERSE/NOMINAL-derived case, both halves**:
    (a) `graphed.selection(graphed.nominal(sel))` returns **that label's member of the argument's own
    selection — an unvaried `Array`, not a `Varied`, in the GRANDparent's row space** (§9.1),
    asserted against a manually projected reference, and `None` when the argument is a root context;
    (b) passing that value as `select=` for a record read from `sel` is **REFUSED at record time by
    predicate (2a)**, naming both contexts (§6.4a(2a): universe/nominal projection links are not
    admitted — a bare parent test accepts it while the mask lives one row space up).
  - **Entry checks (§6.4a) — each predicate anchored with the positive control IT
    decides**: (1) **multiplicity** — a write whose per-label member offsets differ
    from nominal's at any stored level is refused, **per partition at execution time from
    `_WritePart` before any buffer is stored** (`python/graphed/awkward/io.py` evaluates
    inside the worker; do NOT freeze a record-time raise); (2) **row-space agreement, SCOPED PER
    LEVEL** (§6.4a) — at **level 0** the check has two halves with two sites (§6.4a):
    **(2a) lineage, record-time** — a record whose context is not the one the supplied
    `select=` mask derives from is refused at the
    `to_parquet` call naming both contexts, with the *silent-corruption* case as its named
    positive: a record carrying a NON-varied embedded selection (`sel = events[nominal_mask]`,
    then `select=varied_mask`) is refused, not written on mismatched rows — and the chained-context
    case (`graphed.selection(sel2)` for `sel2 = sel[mask2]` against a root-row-space record)
    likewise; **plus the two ABSENT-OPERAND cases** (§6.4a) — a CONTEXT-FREE record (the loose
    §2.1a write style) SKIPS (2a) and IS written, the positive control that keeps the loose sink
    reachable, while a contexted record whose supplied mask **carries NO context handle** (a
    hand-built loose mask, §2.3e's Drop rule) is refused naming the
    record's context — **worded over the handle, NOT over "derived no context", plus the
    positive control that discriminates the two readings**: a mask recorded entirely from reads
    performed THROUGH the record's own context (`select=(events.MET.pt > 50)` rather than
    `graphed.selection(sel)`) carries the record's handle by §2.3e's ORIGINATION rule and derived no
    context, so the binding handle-equality predicate ACCEPTS it and it round-trips;
    **(2c) DEPTH at every supplied level, record-time** — a JAGGED level-0
    mask read through the record's own
    context (`select=(events.Jet.pt > 25)`) is REFUSED at the `to_parquet` call naming the level and
    the per-level channel, with the flat event-level mask over the same context as the positive
    control: it passes (2a) by ORIGINATION and (2b) by outer length, so without (2c) the writer
    applies it as the level-0 OR and silently filters OBJECTS instead of rows — **plus the mirror
    case at level ≥ 1**: a FLAT mask supplied at level 1
    (`select={0: evt, ("Jet", 1): evt}`) is refused at the call naming the level, since it has no
    depth-1 offsets and the level-≥1 structural check below would otherwise have no operand and die
    per partition inside `_WritePart` with an `AttributeError`/`IndexError` — at execution, on a
    record-time form property (§6.4a, the same argument as at level 0); **(2b) row-count equality
    between the record and that mask — EXECUTION-time, per
    partition from `_WritePart`** like (1), NOT a record-time raise (row counts are data);
    at **levels ≥ 1** the check is structural (the mask's per-label offsets equal the
    record's at that depth) and raises per partition from `_WritePart` like (1) — a lineage test is
    unsatisfiable there, since an inner mask is per-OBJECT and is not `graphed.selection` of any
    context. Positive control for the level-≥1 half: the `select={0: event_mask, ("Jet", 1): jet_mask}`
    object-migration write below still passes both predicates.
    **Plus §6.4a's BARE-KEY AMBIGUITY refusal**: a record with two independently
    jagged depth-1 fields (`{Jet: var * {…}, Muon: var * {…}}`) supplied a BARE `1` key is refused at
    the `to_parquet` call naming the ambiguity and the field paths, with the field-scoped
    `("Jet", 1)` spelling on the SAME record as its positive control (the discriminator is a
    record-time FORM property, §6.4a, so both are cheap to build at the call).
    **Plus §6.4b's ROW-SPACE refusal for a stored varied field**: a write whose stored fields
    include `graphed.weight(sel)` for a SELECTION-derived `sel` is refused at the entry check with a
    message naming the ROW-SPACE mismatch (the record is pre-selection on the superset rows while
    §2.6c gives `sel`'s registry per-label row sets re-indexed by each label's mask, and no inverse
    exists) — explicitly NOT the offsets message predicate (1) would otherwise emit; the positive
    control is the storable spelling, `graphed.weight(c)` for a `c` reached across `vary` identity
    links only.
  - Representation anchors, structural (R0.10a — no size thresholds in frozen tests): appended
    columns land in the bound exact representation (XOR-delta values, packed masks) with
    identifier-shaped stored names (labels verbatim, §6.4b) — verified by reading the raw file
    schema + manifest — **plus the FIELD half of the name convention** (§6.4b): a NESTED field
    path (`Jet.pt`) is flattened per level and the skim still reads back through the manifest, and a
    name COLLISION is refused naming BOTH SOURCE FIELDS — **the fixture varies BOTH `Jet.pt` AND a
    flat field named `Jet_pt`**, which is the derived-vs-derived class (both derive to
    `__vary_L__Jet_pt`); a varying `Jet.pt` alongside a NON-varying `Jet_pt` is NOT a collision
    under the bound `__vary_{label}__` prefix and MUST NOT be frozen as a refusal (it is a legal
    nested-field skim); the compression WIN is an R0.11 implementer-report measurement on a real
    skim (methodology stated), NOT a frozen gate.
  - **Manifest DETERMINISM** (§6.4e binds sorted manifest keys precisely because
    set/dict-iteration order would make the written bytes `PYTHONHASHSEED`-dependent; a content-only
    manifest anchor is satisfied by an unsorted serialization, and the manifest-FREE unvaried
    byte-identity anchor can never observe it): the
    same varied write performed in two fresh processes under differing `PYTHONHASHSEED` yields
    byte-identical manifest bytes; minimally, the serialized MAPPING-key order is asserted sorted and
    the levels LIST is asserted in §6.4e's `(depth, field_path or "")` order ("sorted" is
    not a computable predicate over that list's heterogeneous elements, and `sort_keys=True` never
    reorders list elements).
  - Manifest: parquet KV metadata reads back and matches a **literally spelled expected KEY SET —
    which INCLUDES §6.4e's selection-LEVELS entry — with one assertion that the levels entry's
    value equals the literally spelled expected LIST, in §6.4e's bound order** (`[0, ["Jet", 1]]`
    for the object-migration item, `[0]` for the weight-only one — §6.4e binds a JSON list of ints
    and two-element arrays, so the expected value is spelled as a list, never a Python set; the
    levels entry needs its own assertion because the round-trip anchor supplies both levels itself
    and cannot discriminate a reader that never consults it); the augmented file also round-trips
    through `ak.from_parquet` (the arrow-write path
    must reproduce awkward's own KV entries, §6.4e); an unvaried write keeps the `ak.to_parquet`
    path, carries NO manifest, and is byte-identical to today — **as a SAME-PROCESS comparison,
    never a committed `.parquet` fixture** (§6.4g: a parquet footer embeds its writer version —
    `parquet-cpp-arrow version <arrow version>`, readable via `ParquetFile(path).metadata.created_by`
    — so a committed blob breaks on a pyarrow bump and
    across §A.5 matrix legs while the behaviour is correct — R0.10a). Committed byte oracles stay
    for GIR/IR goldens (§6.3).
  - **Structure refusal (negative anchor, §6.4d)**: a stored varied field whose per-label offsets
    differ from nominal's is refused with an error naming the label and the field — with a positive
    control that a same-multiplicity shift with object-level migration still writes and round-trips.
  - **§6.4f WRITE-PATH optimizer-merge refusal** (§6.4f settles that §7.2's refusal guards the
    write path, binding new m51 source): a varied `to_parquet` whose per-label expressions
    include an optimizer-mergeable spelling — a label whose value is `w * 1.0`, which §1.1 makes
    first-class via `variations={s: w * float(s)}` and the M4 identity tokens merge
    (`src/optimizer/engine.rs`; two fills weighted `w` vs `w * 1.0` compile to a single output) —
    is REFUSED at the `to_parquet` call with
    §7.2's message and workaround, with an UNVARIED positive control that today's write path is
    unchanged (§6.3). The check is affordable there: `to_parquet` already compiles at the call
    (`compile_ir` runs in `python/graphed/awkward/io.py` beside `_evaluation_columns`).
  - **§2.3d table entry for `to_parquet`** (it carries NO m48 disposition and is
    absent from m48's table and floor list, so nothing frozen has to change here): with §6.4's
    `select=` landed, `graphed.awkward.to_parquet` ENTERS the table as *accepting* and joins the
    named floor list — the m51 entry asserts the accepting behaviour, i.e. a `Varied` RECORD and/or a
    `Varied` `select=` (both arms) is consumed internally and no per-label result is returned to
    the caller.
  - ROOT half: `graphed_write` gains IR evaluation (derived columns in ROOT skims — the §6.4f
    larger half) with the same round-trip anchor.
  - **numpy-backend refusal (§6.4f), in `graphed`'s `tests/frozen/numpy/m51`** (it is
    `graphed`-side source (`python/graphed/numpy/io.py`), not ROOT-side; unique basename per §10's
    rule). **The anchor is worded over §6.4f's trigger**: `graphed.numpy.io.to_parquet(<a Varied>,
    …)` raises a graphed error naming
    the awkward backend (`graphed.numpy.to_parquet` is not a package attribute, so the
    module path is the entry point). Do NOT freeze a `select=` arm — that keyword is bindingly not
    added to the numpy idiom and stays a plain `TypeError`.
  - Docs: the §7.3 checkpoint paragraph gains m51's write-path scope: widening
    `_WritePart` (§6.4f) churns **no shipped journal** — `write_plan` builds a plain-callable
    `Plan` (`write.py`) and the checkpoint runner takes a `DurablePlan`
    (`checkpoint/runner.py`) — so the churn sentence is scoped to a journal a caller built by
    wrapping the write closure via `OpSpec.from_callable`.
  - Single-read witness on the augmented write run (§5.2b form).

Definition of Done per milestone = the standard checklist (root `CLAUDE.md` §E.0): targets exactly
as specified, frozen suite green and unmodified since freeze, ≥90% diff coverage from the frozen
suite, determinism gate, ruff/clippy/mypy-strict (src AND tests, R0.4a), Sphinx `-W`, full-matrix
CI green at the pinned revision (R0.5), attempts log + reviewer APPROVE recorded.

## §11 Out of scope (Phase 2 — named, not silently dropped)

Declarative nuisance registry / config layer (mkShapesRDF-style `{name, type, kind, samples}`);
correlation/decorrelation metadata, envelope/RMS/symmetrize post-aggregation ops; dataset-level
variation automation (separate-sample variations stay a partition-metadata pattern, documented);
lossy/ratio ("1+delta") storage for §6.4 reconstruction columns (it is NOT bit-exact; any opt-in
must leave §6.4c's exact default intact); per-variation file fan-out (one file per universe — §6.4
appends columns instead; the `part_path` prefix/suffix seam exists in `write.py`);
auto-symmetric weight derivation from a lone `up` (§2.6b);
**user-declared `"variation"` axes** for §6.2 (the frontend declares them in v1; a user-constructed
variation axis is unfillable today — `Histogram.fill` requires one array per axis
(`graphed-histogram src/graphed_histogram/boost.py`) — and supporting it needs a fill-arity
carve-out plus a declared-vs-inferred reconciliation rule);
per-variation monitor/dashboard axis; stage-granular checkpoint task ids (the §7.3 fix);
variations crossing Exchange/Join boundaries (§5.4); implicit variation cross products; weight
clamping/validation hooks (narf `theory_weight_truncate` precedent); growth category axes;
**per-sample divergence of the variation-label set** (merging outputs across samples whose label
sets legitimately differ — the exemplar's suffix-blacklist pathology, lit §ewkcoffea-confirmed;
§6.1a governs one program's outputs, not cross-sample merging); a constant/scalar-Array broadcast
helper needing NO shape donor (§4.1's normalization gap — `gak.full_like` covers the donor case);
a **gak inner-index verb** (`arr[:, i]` on the awkward idiom — absent from gak, §2.6 note (i); the
`gak.firsts(arr[gak.local_index(arr) == i])` spelling covers the PDF-member case today, so this is
ergonomics, NOT a blocker, and is deliberately NOT scoped into m48–m51);
**full support for labels the OPTIMIZER merges** (§7.2: distinct record ids that the M4 identity
/commutativity rules collapse into one compiled output — m48 REFUSES them with a named workaround;
replicating such a value across its labels needs §8.2(i)'s record→reduced map on the frontend unpack
path and is not scoped in m48–m51);
an **in-IR bit-view / `packbits` verb** (§6.4c's XOR deltas are computed in `_WritePart` on
evaluated buffers precisely because no recorded form exists — `float32 ^ float32` is a
`TypeError` in both numpy and awkward, and gak ships no `view`/`packbits`/`frombuffer`);
**multiplicity-changing stored variations** for §6.4 (shift-dependent cleaning / overlap removal /
matched collections: no representable same-shape delta, refused in v1 per §6.4d);
**a contexted fill that suppresses the AMBIENT weight while applying its own explicit factor**
(§6.1d: `unweighted=True` suppresses both, by design, and nothing detaches a context's
registry — the v2 answers are a context-level detach verb or a narrower `unweighted=` scoped to the
ambient factor alone); a first-class Rust `Vary` NodeKey.

## §12 Process and bookkeeping

- **§12.1 (Forward process, owner decision.)** The plan-review cycle is CLOSED; no further plan
  rounds run. Residual sharpening happens in m48 decomposition against the §12.4 ledger, not in
  plan rounds. Each milestone m48–m51 runs the gated three-role pipeline: test-author writes and
  freezes the acceptance suite (TEST_SANITY: collects, non-vacuous — fails the stub for the right
  reason — deterministic, coverage-wired), implementer iterates under the full R0.4 mechanical
  gates without ever touching `tests/frozen/**` (disputes via `.graphed/<mX>/disputes/`, the m39
  precedent), reviewer judges intent/guardrails/technique and may REJECT; implementation review
  runs the design / integrity / mutation three-lens pattern (m46/m47 precedent) at the
  BLOCKER / HIGH / MID / LOW / NIT severity terms, cycling until clean, empowered to send work back
  to planning. R0.5 pins DONE to full-matrix CI green. R0.10/R0.10a govern every witness; R0.11
  governs every number in every report.
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
    `fill_nodes_by_label`) is reachable. The exact annotation, and how a mixed/ill-formed operand is
    rejected, are pinned at m49 freeze with the rest of each verb's spelling.
  - (2) **§6.4f numpy refusal.** The trigger (a `Varied` first positional) and entry point
    (`graphed.numpy.io.to_parquet`) are bound; the error CLASS and message wording are pinned at m51
    freeze. The numpy idiom bindingly gains no `select=` keyword, so no m51 anchor freezes that arm.
  - (3) **§8.2(i) producer cost.** The bound recipe walks one record CONE per label inside
    `plan()`. Its cost is bounded by the per-label cone size (the same traversal §3.4's verb
    performs) and is a driver-side, once-per-plan walk; m49 decomposition confirms it against §3.3's
    budget and states the measurement (R0.11) rather than assuming it here.

---

---

r28 is a design extraction of r27 (git `f85528e`): review/verification apparatus removed, binding
content unchanged. Earlier revision history lives in git and the
`systematics-vary-plan-revision-r*-notes.md` files; evidence trails live in the two research
companions.

