# Systematic variations in graphed — `vary`, the variation frontend + IR treatment (execution plan)

Status: **draft for review (r24).** Anchoring doc for the work, structured like the root prompt:
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
`graphed-root-prompt.md:1284`, the bullet "treating systematic variations as a graph axis" wrapping
`:1286-1287` — re-measured r18: `:1285` is BLANK, the sentence runs `:1286-1287`), inline in R22.0 and R22.10 (`graphed-root-prompt.md:1262,1282`), and the corpus ops
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
  §6.4b), both of which also carry the user's arbitrary `name` and field; **the input grammar
  below states no magnitude bound, so a large-magnitude INTEGER-valued input is the one spelling
  the grammar admits and the cap then refuses** — `"1e40"` renders as 41 plain digits while
  `"1e-40"` renders as the 5-character `1em40`, so an integer-valued input whose plain-digit
  rendering exceeds the cap is rejected **at canonicalization with a message naming the
  magnitude**, not with a generic tag-length error, r13; **the magnitude test runs on the COMPUTED
  DIGIT COUNT BEFORE any rendering, and the canonical string is
  produced only once that count is within the cap**, r18 — **with the NORMALIZATION stated, r19**:
  the count is (the input's mantissa digits after removing the decimal point and stripping leading
  zeros) + (the exponent adjusted for where that decimal point sat), NOT a naive "mantissa digits +
  exponent", which is off by one at the boundary for a dotted mantissa (`"1.5e31"` renders as `15`
  followed by 30 zeros = 32 plain digits, exactly at the cap and LEGAL, while the naive sum gives
  2 + 31 = 33 and rejects it — **and m48's grammar anchor carries that BOUNDARY PAIR, r20**:
  `"1.5e31"` ACCEPTED with the 32-digit canonical tag and a 33-digit neighbour (`"1.5e32"`)
  rejected with the magnitude message. The accepted half is the discriminating one — the naive sum
  rejects it — and r19's own claim that "the cap boundary is precisely where m48 freezes the
  magnitude message" was false of m48's anchor list, which named only `"1e40"`, a value the naive
  computation also rejects); **and the quantity compared against the cap is the RENDERED CANONICAL
  LENGTH under BOTH renderings, r22** (r21 bound it as "that digit count PLUS 1 when the value is
  NEGATIVE", which is the rendered length only for an INTEGER-valued input): for an integer-valued
  input it is the normalized digit count, plus 1 when negative — the `m` sign marker is a character
  of the canonical tag but not a digit; for a FRACTIONAL input the normalized count is not the
  rendered length at all, since the adjusted exponent is negative by construction (a
  31-digit-mantissa fractional value has a normalized count of 31 − 35 = −4 while rendering as 35
  characters), so the compared quantity there is `len(mantissa) + 2 + len(exponent)`, again plus 1
  when negative. **The two refusals are split by CAUSE, r22**: an input whose INTEGER digit count
  alone exceeds the cap is rejected with the MAGNITUDE message (`"1e40"`, `"1.5e32"`); every other
  over-cap case is rejected with a canonical-tag-LENGTH message naming the rendered length — the
  sign marker pushing an otherwise legal magnitude to 33 characters (`"-1.5e31"`: 32 digits, legal
  magnitude, 33 rendered characters) and the long-mantissa fractional case alike. r21 gave
  `"-1.5e31"` the MAGNITUDE message, which blames a magnitude the adjacent m48 anchor certifies as
  LEGAL — `"1.5e31"` is ACCEPTED with the same magnitude — and the plan's own standard elsewhere
  (§6.1d's loose-value message split, §6.4b's row-space-not-offsets message) is that a diagnostic
  must not blame the wrong property; the m48 verdicts are unchanged and only the negative twin's
  message CLASS moves; r18: the input grammar states no magnitude
  bound, so `"1e1000000000"` is legal input and a render-then-measure implementation must
  materialize a one-billion-digit string before the cap can refuse it) — chosen for its
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
  and distinct content hashes). **"FAMILY" is defined here, once, and the check spans calls**
  (r17 — the word appeared six times in this section and was never defined, while every other
  rejection is scoped explicitly ("within the call, within the container, or colliding with
  inherited labels") and this section goes out of its way to bind that canonical spellings unify
  ACROSS calls; under the natural per-call reading
  `vary(ctx, "murf", w_nom, is_weight=True, variations={"0.5": a})` followed by the same call with
  `variations={"0p5": b}` is ACCEPTED — two labels, two universes, two StrCategory bins and two
  content hashes for ONE value, verbatim the hazard this rule exists to prevent and uncatchable
  later, since the p-form deliberately does not canonicalize. **The illustration is spelled in the
  WEIGHT form (b), r23**: an event-context target with NO `is_weight` is overload (c), the shift
  form, in which `variations=` is REJECTED with an error naming `collections=` (§2.1), so the
  r17–r22 spelling `vary(ctx, "murf", variations={"0.5": a})` is refused by a DIFFERENT rule before
  the family check can run — and m48's grammar anchor repeated that spelling, i.e. would have frozen
  the wrong rejection): **a family is the set of tags carried
  by one `name` on one container, INCLUDING labels inherited through §2.1 stacking.**
  **For a CONTEXT target the per-`name` tag map §2.2 retains lives on the container the call
  registers into — the ambient-weight `Varied` in the weight form (b), the replaced collections in
  the shift form (c) — so the family check has a named operand from m48, one milestone before
  `graphed.variations(ctx)` (§9.1, m50) exports it (r23).** The
  numeric-equal check therefore runs against inherited labels of the same `name` too — it is the
  same parse the check already performs — and the m48 grammar anchor carries the two-call
  cross-notation case.
  (Encoding decision trail, owner 2026-07-30: r8's canonical was the datacard p-form; the
  owner's scaled-integer proposal — carry the scale as an exponent suffix, `1.2345`→`12345e-4`
  — is self-describing and, in identifier-safe rendering, IS this e-form; selected over p for
  the uniform full-range grammar and native numeric structure. Trade-off recorded: hand-typed
  datacard tags (`0p5`) no longer unify with float spellings (`"0.5"`→`5em1`) — the
  cross-notation rejection catches in-family mixes; p-tags stay legal identifier tags.)
  Tags arrive through **THREE channels**: **kwarg names** (`up=…, sig2=…`), the
  `variations={tag: …}` mapping, and — in the shift form (c), where `variations=` is REJECTED — the
  **INNER keys of the collection mappings** (`Jet={"up": …}`, `collections={Name: {tag: …}}`; added
  r15: the two-channel enumeration covered neither channel that the entire shift form uses, so a
  canonicalization or rejection bug confined to it would survive the m48 grammar anchor, which is
  written over the enumerated channels).
  Validation and canonicalization are **channel-independent** across all three: literal kwarg syntax cannot spell
  dotted or digit-leading tags (`0p5=` is a SyntaxError), but CPython admits any string key
  through `**`-unpacking (measured, CPython 3.12.10), so both channels apply the same rules;
  `variations=` is simply the documented route for such tags. Arbitrary hashables are REJECTED
  (labels serialize into specs, files, and manifests; string-only — a float tag is passed as its
  string, never as a Python float, so the user owns the spelling). `vary` MUST reject, at call
  time: duplicate labels after canonicalization (within the call,
  within the container, or colliding with inherited labels, §2.1), numeric-equal tag pairs
  within a family (above), a tag supplied both as kwarg and in `variations=`, malformed or
  non-string tags (including Python floats — pass the string), and empty tag sets.
  **`"nominal"` is reserved as the central LABEL and is unreachable as a user label BY
  CONSTRUCTION, not by a rejection** (r16 — r6–r15 listed "a label equal to `"nominal"`" among the
  rejections, which is unconstructible under this section's own grammar: `label = f"{name}_{tag}"`
  with a non-empty identifier `name` and a non-empty `tag`, so every user label contains at least
  one `_` while `"nominal"` contains none; a test-author freezing "every listed rejection" would
  have to write an unconstructible negative case). The TAG `nominal` stays legal — §2.1 says so
  explicitly and routes it through `variations=` because it shadows a signature keyword — and it
  yields the ordinary label `pu_nominal`, distinct from the reserved central label.
- **§1.2** In the expansion/sibling-fill lowering (§4, §5, §6.1), variation labels are **frontend
  metadata, never structural identity**: a label MUST NOT enter `NodeKey` params, tokens, or
  content hashes. Two variations with structurally identical content intern to the same nodes
  (dedup is correct: renaming a systematic must not recompute — the AddressTable
  label-out-of-hash precedent, `execution.py:276-284`). Only real content differences (a different
  input id; a different correctionlib `systematic=` param) fork identity. **Carve-out (§6.2),
  covering BOTH of axis mode's label channels (r22):** in variation-axis fill mode the labels become
  *output content* — (1) StrCategory bin identities in the histogram spec, and (2) §6.2's r15
  **per-fill variation payload**, a field of the fill's `FillEvaluator` that enters the External
  payload's content hash as `content_hash((spec, variation_payload))` — and in both they DO enter
  the spec/params/content hash, by design; renaming a systematic in axis mode legitimately changes
  the output histogram. (r6–r21 named only (1), while §6.2 says in terms that its carrier is NOT the
  spec — "§1.2's §6.2 carve-out does not close it — it puts the BIN IDENTITIES in the spec, which is
  exactly the part identical across siblings" — so this section read literally forbade the mechanism
  §6.2 binds, and an m50 integrity reviewer working from §1.2 had a defensible objection. Nothing
  inside m48–m51 reds either way: m48's §1.2 anchor is sibling-mode-scoped by r13.)

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
  **What a MEMBER may be is stated once here, r18, and it is not "an `Array`"** (the r6–r17 per-overload
  type declarations — "members are Arrays" in (a), "every member is a per-event weight Array" in (b) —
  contradict this section's own stacking rule three paragraphs below, which is written for and
  REQUIRES `Varied` members ("`graphed.nominal(v)` if the provided value is itself `Varied`";
  "`old_ambient[L] × factor[L]` — the factor evaluated in that label's own universe", which exists
  only if the registered factor IS a `Varied`), and contradict this section's own mainline sketch,
  which passes `btag_sf(sel.Jet)` — a `Varied`, since `sel.Jet` is one — as `nominal=`/`up=`/`down=`
  (§2.6 sketch). §2.5 binds construction-time member validation and m48 freezes "§2 validation
  errors", so an implementer coding the literal type would add an `isinstance(m, Array)` guard that
  raises on this plan's own mainline program): **a member may be an `Array` OR a `Varied`.** In
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
  **The factor's ROW SPACE is bound here, r19, because nothing else binds it and the stacking rule
  below multiplies against it**: the registered factor — and every member of a `Varied` factor —
  MUST live in the TARGET context's row space, i.e. be read through that context or through an
  ancestor of it. An ANCESTOR-handled factor is re-indexed to the target across the intervening
  lineage links per §6.1d link kinds (1)-(3), exactly as §6.1d re-indexes an ancestor VALUE at a
  fill; **the violation half is TOTAL, r20** (r19 named only the divergent branch, leaving the third
  case — a factor handled by a DESCENDANT of the target, the natural mis-spelling
  `graphed.vary(events, "btag", btag_sf(sel.Jet), is_weight=True, …)` that registers a
  selection-scoped SF onto the ROOT context — silently unbound: it is not divergent, so §2.1's
  end-of-section divergence check passes, and no re-indexing exists in that direction, a mask having
  no inverse (§6.4b makes the same argument); it then records cleanly and dies at execution, the very
  hole this paragraph was opened to close): **a factor whose handle is neither the target's own nor
  an ANCESTOR of it — a DESCENDANT handle as much as a divergent one — is a construction-time error
  naming both contexts and the DIRECTION of the mismatch.** m48's stacking anchor carries the
  descendant case as a negative control alongside its parent-factor positive one. Left unbound, a factor computed from a value read at the PARENT
  (the natural spelling for a jet-derived SF reusing a pre-selection collection) sits at the
  parent's row count while §2.6c re-indexes the derived context's inherited members to `|sel_L|`
  rows, and the stacking product `old_ambient[L] × factor[L]` records CLEANLY — measured,
  `Session.record_op` validates only the backend's `op_form`, never lengths or row spaces
  (`python/graphed/session.py:142-168`) — dying at execution with a message §6.1d's refusal contract
  does not cover (that contract is scoped to a fill's weight factors, and §6.1d's link-kind
  re-indexing runs at the FILL, too late: the mismatch is already interned). The resulting invariant
  is the one §6.4b's r18 precondition already assumes: **`graphed.weight(ctx)` always answers in
  `ctx`'s own row space.** m48's stacking anchor carries a positive control registering a factor
  computed at the PARENT context.
  (c) **Event-context target, shift form** (no `is_weight`): each kwarg names a **collection**;
  each value maps tags to varied records — `graphed.vary(events, "jes", Jet={"up": j_up, "down":
  j_dn}, MET={…}) -> new context` with every named collection replaced by a `Varied` (all
  collections in one call MUST share one tag set — the lockstep Jet+MET form; §2.6a).
  **`nominal=` is REJECTED in the shift form**, with an error naming `collections=`, mirroring the
  `variations=`-in-(c) refusal (r17 — overload (a) declares it invalid and (b) gives it a meaning,
  while (c) left it undefined: in the shift form the collections' central members come from the
  target context, so `nominal=` has nothing to mean, and it is one of the four shadowed names so it
  cannot be read as a tag either; m48's grammar anchor covers the four shadowed names but not this
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
  the factor). **`factor[L]` means §2.4 applied TWICE when the factor NESTS, r24**: a registered
  factor may itself be a `Varied` whose members are `Varied` (§2.1's r18 member rule plus this
  plan's own mainline — `graphed.vary(sel, "btag", btag_sf(sjets), is_weight=True, up=…, down=…)`
  registers a container labelled `{nominal, btag_up, btag_down}` whose members are each `Varied`
  over the INHERITED jes labels, because `sjets` is `Varied`), and the one-level reading is
  silently wrong exactly where the corpus is: for `L = jes_up`, L is new to the *container*, so
  "its central universe" would give the b-tag SF on NOMINAL jets — the omission the paragraph above
  says misses the `ttbar_4j1b_jes_up` reference. Binding: take the container's member for L (its
  `"nominal"` member when L is new to the container), then, if THAT member is itself `Varied`, take
  its own L (its `"nominal"` when L is new to the member). The composed ambient weight is therefore
  always FLAT — `{label: Array}` — which is what `graphed.weight(ctx)` (§9.1) returns. This is not a nicety: for `variation="jes_up"` the corpus computes the CENTRAL
  b-tag SF **on JES-shifted, JES-selected jets**
  (`graphed-corpus src/graphed_corpus/analyses/systematics.py:74-76` — `sel_jets = good[sel]`
  then `_btag_weight(sel_jets, variation=variation)`, which returns the central SF unless
  `variation` is `btag_up`/`btag_down`, `:25-36`), so the `ttbar_4j1b_jes_up` reference IS b-tag
  weighted; a naive "inherited labels keep the old ambient" reading omits the SF entirely and
  misses the reference. Each label still differs from
  `"nominal"` in exactly **one** knob — the one-at-a-time rule is structural, and a weight
  variation layered on a shift-propagated weight (the corpus b-tag-on-JES case,
  `systematics.py:74-76`) is expressible without cross products.
  **The REVERSE order is bound too, as an ordering rule, r16** (the weight-on-shift direction above
  was bound carefully while shift-after-weight was unaddressed, and it is silently wrong: the shift
  form replaces collections and leaves the ambient registry untouched — this section's own
  "inherited members pass through unchanged" for overloads (a)/(c), and §2.6b's shift-form
  description, which registers nothing on the weight side — so a jet-dependent weight registered
  BEFORE a JES `vary` fills every
  shift universe with its PRE-shift value. It is structurally unfixable after the fact, since the
  registry's members are already-recorded expressions rooted at pre-shift nodes, which is why the
  exemplars handle it as a hand-partitioned "these weights can go outside the sys loop" judgement,
  Part I §2): **a shift `vary` does NOT re-derive the ambient weight registry; a weight factor that
  depends on a collection MUST be registered AFTER that collection is varied.** The rule is backed
  by a §2.5 diagnostic rather than left to convention (below), using machinery §3.4 already scopes.
  All members MUST share one Session, have compatible forms (backend `op_form`-checked at
  construction), and root in the same partitioned-source set (checked at construction; the
  otherwise-deferred failure surface is `aggregate_plan`'s single-source check,
  `aggregate.py:89-93`). **Their CONTEXT HANDLES are unified here too, r18** — `vary` is a combining
  point in §2.3e's sense and it is not an op, so the `record_op` merge chokepoint never sees it
  (the five `_array_cls` sites are `source`/`record_op`/`record_exchange`/`record_join`/
  `record_external`, `session.py:140,168,183,204,242`, and a container construction reaches none of
  them), while `graphed.context_of` answers with ONE handle (r15-r19 said "the nominal member's";
  **r20 binds it to the CONTAINER's most-derived handle, §2.3e** — either way a single answer), so a
  divergently-handled member would be silently dropped from introspection and surface
  only at the fill's unification: **all members' handles MUST lie on ONE ancestry chain, the
  container carries the most-derived one, and divergent handles are a construction-time error naming
  both contexts** — the same rule §2.3e binds at every other combining point. Lockstep multi-column variation within one collection (jet pt+mass
  shifted together) is expressed by varying a record Array — the corpus JES fixture already does
  this via `ak.with_field` (`systematics.py:39-45`); no second verb.
- **§2.2 (`Varied` is a mapping of universes; extraction is functional.)** `Varied` holds
  `{label: Array}` with `"nominal"` always present — **a member may itself be a `Varied`** when the
  container is a registered weight factor (§2.1 r18, resolved two-level in r24), while the AMBIENT
  weight `graphed.weight(ctx)` returns is always flat. **The container is PER IDIOM, and that is bound
  here, r24** (r1–r23 bound the container's SURFACE — §2.3a's parity gate resolves every public name
  of `type(graphed.nominal(v))` ON THE CLASS — while never saying what class `graphed.vary` returns,
  and §2.2/§10 pin the property fixture to the NUMPY idiom, so a single neutral `graphed.Varied`
  would have to define the 26 numpy-only public names `NumpyArray` adds — measured against
  `graphed-latest@ff7c607`: `dir(Array)` public = `['filter','map','node_id','reduce',
  'repartition','session']` (6), `dir(NumpyArray)` = 32, the extra 26 being
  `T/all/any/argmax/argmin/astype/clip/cumprod/cumsum/dtype/max/mean/min/ndim/prod/ravel/reshape/
  round/shape/squeeze/std/sum/swapaxes/take/transpose/var` — which is numpy-idiom leakage into
  `graphed` proper (§2.1's factorization sentence, root `CLAUDE.md` §A.4) AND silently shadows
  field access for those 26 names on an awkward-idiom container, re-creating the §2.6a
  namespace-collision hazard the r6 functional respin exists to delete; while a neutral container
  carrying only `Array`'s six names is RED against §2.3a's own gate on the mandated fixture):
  **`Varied` mirrors the existing `Session._array_cls` backend seam** — a neutral `graphed.Varied`
  base carrying `Array`'s surface, with `graphed.numpy` supplying the numpy-idiom subclass mirroring
  `NumpyArray` — and `graphed.vary(x, …)` returns the container class PAIRED WITH `type(x)`, exactly
  as the session pairs its proxy class with the backend (`factory = getattr(backend, "array_type",
  None)`; `self._array_cls: type[Array] = factory() if callable(factory) else Array`,
  `python/graphed/session.py:36-39`, used at `:140,168,183,204,242`). §2.3a's dynamic enumeration is
  then self-consistent: inventory and resolving class come from ONE idiom. **It additionally retains, PER `name`, the tags
  registered under that name, r20** — internal state, not a second public shape: §1.1's family check
  is defined over "the set of tags carried by one `name` on one container, INCLUDING labels inherited
  through §2.1 stacking", and the label mapping alone cannot answer it (the only decomposition
  available from `{label: Array}` is prefix-matching `f"{name}_"`, which mis-attributes whenever one
  name plus an underscore prefixes another — `vary(v, "jes", up_2=…)` and `vary(v, "jes_up", …)`
  both yield `jes_up_2`; the duplicate-LABEL rejection catches that particular pair, but attribution
  is what the family check reads). `graphed.variations(ctx)` (§9.1, m50) is the per-name listing on a
  CONTEXT; on a loose `Varied` (§2.1a, which stays public) this retained map is the operand and stays
  internal. Universe extraction and introspection are
  **module functions** (the r6 namespace-collision principle, §2.6a): `graphed.labels(x)`
  (ordered: nominal first, then insertion order; inherited labels before new ones under
  stacking), `graphed.nominal(x)`, and `graphed.universe(x, label)` (KeyError on an unknown
  label, listing the valid labels) — each accepting **FOUR input shapes, enumerated here because
  this is the definition site and two later sections extend it (r23): a `Varied`, an event context
  (uniform introspection, §9.1), a `{label: hist}` RESULT MAPPING and a bare histogram-like object
  (duck-typed on `.axes`, never importing `boost_histogram` into `graphed`)** — the per-shape
  answers for the two result shapes being bound in §6.1a (a bare `hist` reads as the single label
  `"nominal"`) and §6.2(i-bis) (an axis-mode histogram reads its variation axis's bin set, re-ordered
  to this section's rule). **`graphed.nominal` on those two shapes is bound here, r24** (§6.1a and
  §6.2(i-bis) name only `graphed.labels`/`graphed.universe`, and m50's (i-bis) anchor asserts only
  those two, so the third verb was claimed here and defined nowhere — and the natural fallback,
  return the argument unchanged, is CORRECT for a bare unvaried histogram and confidently WRONG for
  an axis-mode one, handing back a histogram whose variation bins sum into the view the caller reads
  as the central value, the §2.5 class §6.2(i-bis) opens by naming): **`graphed.nominal(x)` ≡
  `graphed.universe(x, "nominal")`** on both result shapes — identity for a bare unvaried histogram
  (which reads as the single label `"nominal"`), `x["nominal"]` for a `{label: hist}` mapping, and
  the nominal SLICE along the variation axis for an axis-mode histogram. **On a CONTEXT the answer is bound here, once** (r13 — §2.6c bound only
  "the mask's labels", which is a strict SUBSET of what a fill from that context produces, and
  said nothing at all about a root context carrying only weight registrations; a "uniform"
  introspection verb answering less than the sink produces is the §2.5 confidently-wrong class):
  `graphed.labels(ctx)` is the **§2.4-ordered union** of (a) the ambient weight registry's
  labels, (b) the labels of any `Varied` collections the context CARRIES — the collections a
  shift-form `vary` replaced, inherited ones included, **NOT the implicitly-varied reads §2.6c
  produces through a `Varied`-mask-derived context (scoped, r21**: under the wide reading every read
  through such a context is `Varied`, so (b) would subsume (c) everywhere and (c) would be dead
  text — the term-(c) discrimination m48 anchors depends on this scoping) — and (c) the labels of
  **`graphed.selection(ctx)` in §9.1's sense — the selection reached by skipping over any number of
  `vary` IDENTITY links and answering as of the first non-identity link, `None` for a root context;
  on a universe/nominal-derived context that answer is a single label's unvaried member and
  contributes NO labels** (r20 — r13-r19 said "the mask that derived it", which has no value at all
  for the two lineage link kinds that carry no mask: §6.1d binds THREE kinds and §2.6's own sketch
  rebinds `sel` by a `vary` call, so the object whose labels a user or an m48 anchor asks for is
  routinely `vary`-derived. In the mainline term (a) happens to rescue the answer — a factor
  registered into a mask-derived context is itself `Varied` and re-carries the mask's labels — but
  that is a property of the program, not a rule, and a uniform introspection verb answering less
  than the sink produces is the §2.5 confidently-wrong class this clause was written to close. The
  definitional reference does not move `graphed.selection`'s own milestone: §9.1 keeps it at m51,
  and its per-link-kind ANSWER is bound there independently of when the verb is exported. **Term (c)
  itself gains an m48 program that isolates it, r21** — a context derived by a LOOSE-`vary`-varied
  mask, where (a) and (b) are both empty — **while the r20 `vary`-link-walking HALF is knowingly left
  UNANCHORED**: on a `Varied`-mask-derived context every read through the context is `Varied`
  (§2.6c), so a weight registered onto a `vary`-derived child lands the mask's labels in term (a) and
  a shift-form `vary` stacks them into term (b), leaving no m48–m51-scoped program in which the two
  readings differ. It stays binding for the verb's correctness, on §1.1's `"1e1000000000"`
  precedent) — by
  construction the SUPERSET of the
  CONTEXT-BORNE half of any §6.1d fill's label set from that context, `"nominal"` first. **The
  superset property is scoped to context-borne sources, and that scoping is binding** (r14 — stated
  unscoped it is a false invariant a test-author could freeze: §6.1d's fill label set also unions
  labels carried by *loose* values and by explicit `weight=[…]` factors, and the loose
  `graphed.vary` on `Array`s stays public (§2.1a, §2.6 close), so both
  `h.fill(sel.Jet.pt, weight=[loose_varied])` and `h.fill(graphed.vary(sel.Jet, "jer", …).pt)` are
  expressible programs whose fill label set exceeds `graphed.labels(ctx)`).
  `graphed.universe(ctx, label)` and `graphed.nominal(ctx)` return **a CONTEXT** — a CHILD of the
  argument in the §2.6b lineage chain (bound here, r14, because §6.1d's unification is defined over
  lineage and would otherwise have no way to relate the result to its argument: `h.fill(
  graphed.nominal(sel).MET.pt, sel.MET.pt)` would either unify by an unstated rule or raise the
  divergence error on a legitimate program) — carrying that label's collections and ambient weight
  (falling back to each container's `"nominal"` member per §2.4), with `graphed.selection(...)`
  equal to the argument's selection at that label. The m48 anchor asserts the ancestry relation. String subscription `v["pt"]` is **field access** (broadcast per §2.3a,
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
  ordinary ops instead. **`Varied` gives EVERY public PROPERTY of the nominal member's class a disposition** — the rule is a
  discovery rule over properties, not a two-name list (r18; r6–r17 closed the hazard for `node_id`
  and `session` only, while §2.3a deliberately EXCLUDES properties from its parity gate, so the
  numpy idiom's `shape`/`dtype`/`ndim`/`T` (`python/graphed/numpy/array.py:78,82,86,160`, all plain
  properties invisible to `inspect.isfunction`) had neither a reserved-name rule nor a gate entry and
  would resolve through the label-mapping field access, recording a graph node named `"dtype"`. It is
  a live path: §6.1d binds the numpy `broadcast_like` seam as a NO-OP precisely so an all-numpy
  varied fill works). **The disposition splits by MECHANISM, not by `isinstance(m, property)`, r19**
  (r18 read "every other property is answered EAGERLY … on a plain `NumpyArray` these are already
  answered from the form and never recorded", which is false of `T`: measured against
  `graphed-latest@ff7c607`, `NumpyArray.T` is `@property def T: return self.transpose()`
  (`python/graphed/numpy/array.py:159-161`) and `transpose` is
  `self._session.record_op("transpose", [self], params)` (`:156-157`), so accessing `T` RECORDS —
  probe on a 1-D `NumpyForm` source: `dtype`/`ndim`/`shape` → `Session.node_count()` delta 0,
  `T` → delta 1. `Array._form_meta` is not its path at all, and `_form_meta` itself falls back to
  recording a `field` op when the form lacks the name, `python/graphed/array.py:283-290`. Under the
  r18 reading `varied.T` would answer on the nominal member alone, silently dropping every other
  universe — verbatim the §2.5 confidently-wrong class the rule exists to close — while §2.3a
  classifies the `transpose` METHOD *broadcast*): for every non-underscore property on
  `type(graphed.nominal(v))`, exactly one of three classes applies —
  **(1) `node_id` and `session` raise `AttributeError`** rather than resolving as field access;
  **(2) a FORM-ANSWERED property — one whose access on a plain nominal `Array` records NO node
  (measured today: `shape`/`dtype`/`ndim`, all `_form_meta`-backed,
  `python/graphed/numpy/array.py:76-86`) — is answered EAGERLY on the nominal member** (sound by
  §2.1's form compatibility, the same argument §2.3c uses for `gak.fields`/`type_of`);
  **(3) a RECORDING property — one whose access on a plain nominal `Array` records a node (`T`
  today) — takes its underlying METHOD's §2.3a disposition** (`T` → *broadcast*: it returns a
  `Varied` whose `graphed.labels` match the input's). The discriminator between (2) and (3) is
  behavioural and measurable pre-implementation — access the property on a plain nominal `Array`
  and read the `Session.node_count()` delta — so the gate below classifies each discovered name by
  measurement rather than by a literal list. The `node_id`/`session` half
  is binding because `Array` exposes both as plain properties, not dunders (`array.py:137-143`), while
  `Array.__getattr__` guards only leading underscores (`array.py:332-335`) — so a `Varied` that
  implements field access by mapping over labels would answer `varied.node_id` with a recorded
  `field` op named `"node_id"`, and `compile_ir(session, varied)` (`execute.py:70`,
  `ids = [arr.node_id for arr in outputs]`) would silently compile that nonsense instead of
  raising, the §2.5 confidently-wrong class. **Both this rule and §2.3d's dispositions are
  frozen-anchored in m48** (r13 — they were binding and unanchored, the same gap r12 closed for
  §5.3; the §2.3a parity gate cannot reach them, since `node_id`/`session` are plain properties
  that `inspect.isfunction` does not enumerate, `array.py:137-143`). `Varied` is a plain frontend object — no IR type, no
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
  covered), not from a literal list. **The enumeration FILTER is stated here, r16**, because the
  reserved-name reasoning below presupposes it twice ("the §2.3a parity gate cannot reach
  `node_id`/`session`, since they are plain properties that `inspect.isfunction` does not
  enumerate") while no clause ever bound it — and r15's per-name rule ("resolved ON THE CLASS … and
  MUST be a real attribute") applied to an UNFILTERED enumeration would demand `Varied.node_id`/
  `.session` exist, which §2.2's reserved-name anchor in the same milestone demands raise
  `AttributeError`, and would demand dispositions for numpy-idiom properties §2.3a never assigns
  (measured: `[n for n in dir(Array) if not n.startswith("_")]` is
  `['filter','map','node_id','reduce','repartition','session']`, of which `node_id`/`session` are
  properties, `python/graphed/array.py:137-143`; `dir(NumpyArray)` adds `T`/`dtype`/`ndim`/`shape`,
  32 public names): the method half is
  `inspect.getmembers(type(graphed.nominal(v)), inspect.isfunction)` with no leading underscore,
  plus the dunder set — the same spelling §2.3c and §2.3d already bind (same
  self-repairing rule, and the same **non-vacuity floor**, as (c) — which for this gate MUST name
  at least one METHOD alongside the named dunders).
  **The PROPERTY half is enumerated too, under §2.2's r18 disposition rule** (r18 — excluding
  properties outright is what left `shape`/`dtype`/`ndim`/`T` with no disposition anywhere): a
  third enumeration over `inspect.getmembers(type(graphed.nominal(v)),
  lambda m: isinstance(m, property))` with no leading underscore, asserting each discovered name
  resolves per §2.2's THREE-class rule (r19; the r18 blanket "records NO node" is red against a
  correct implementation for `T`, which is a plain alias for the recorded `transpose` op —
  measured, `python/graphed/numpy/array.py:156-161`, discovered set on `NumpyArray` =
  `['T','dtype','ndim','node_id','session','shape']`): `node_id`/`session` raise `AttributeError`;
  a property the same test measures to record NO node on the plain nominal `Array` must answer
  eagerly on the nominal member with a `Session.node_count()` delta of 0 across the `Varied`
  access; a property that DOES record on the plain nominal `Array` must broadcast — returning a
  `Varied` whose `graphed.labels` match the input's. The gate's floor names **both** representatives
  measured today: `varied.dtype` (eager, delta 0) and `varied.T` (broadcast, returns a `Varied`).
  **What the gate ASSERTS per name is bound too, because a presence check is vacuous here** (r15 —
  r12–r14 bound only the ENUMERATION and the floor, and a `hasattr`/`getattr`-on-the-instance
  iteration is green against exactly the failure this paragraph names: `Varied` implements field
  access by mapping over labels, mirroring `Array.__getattr__`, which returns a recorded `field` op
  for ANY non-underscore name — `python/graphed/array.py:332-335` — so `hasattr(varied, "filter")`
  is True on a `Varied` that broadcasts ZERO methods, and for the refusing disposition
  `varied.repartition` resolves to a container and calling it raises `TypeError: not callable`,
  which a loose `pytest.raises` refusal check accepts). Binding: **(1)** each discovered name is
  resolved ON THE CLASS — `getattr(type(varied), name, None)`, which the instance `__getattr__`
  never intercepts — and MUST be a real attribute; **(2)** the same test carries at least one
  BEHAVIOURAL probe per disposition class: a broadcast method returns a `Varied` whose
  `graphed.labels` match the input's, and `repartition` raises the §5.4 refusal, not
  `TypeError: not callable`. §2.3e's `Array`-surface propagation gate ((e)(4)) inherits the identical
  class-lookup rule.
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
  functions.py` → 0), and the package `__all__` lists modules, classes and **six package-level
  functions — none of them gak's** (`python/graphed/awkward/__init__.py:17-31`; measured r16, the
  functions among them are `from_awkward`/`from_parquet`/`project`/`project_buffers`/
  `read_parquet_partition`/`to_parquet`), so an `__all__`-driven test over `graphed.awkward`
  discovers a **WRONG six-name set** — non-empty, so a bare non-emptiness floor would not catch it;
  a bare `dir()` over-fires on imported symbols and on the module's
  private helpers (`grep -c "^def " functions.py` → 73, including `_comb_params`, `_reduce`).
  Binding discovery: `inspect.getmembers(graphed.awkward.functions, inspect.isfunction)` filtered
  to `__module__ == "graphed.awkward.functions"` and no leading underscore. **The MODULE is named,
  not the `gak` alias** (r15 — measured: the alias `graphed.awkward` used as the target discovers
  **0** functions, because the package re-exports modules/classes only and gak's functions are not
  package-level attributes (`graphed.awkward.num` → `AttributeError`), while
  `graphed.awkward.functions` discovers **65**; the non-vacuity floor below would catch the empty
  reading at freeze, but naming the module spares the discovery). **Binding non-vacuity floor, asserted
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
  `graphed.repartition` **refuse** with the §5.4 error; **`graphed.pack_key`, `graphed.shuffle_plan`
  and `graphed.join_plan` refuse likewise** (r13 — the r12 list called itself EXHAUSTIVE and left
  these three undisposed; measured, all three are exported in `__all__` and take an `Array` first:
  `pack_key(array, *, on)` reading `array.session` at `shuffle.py:84,89`, `shuffle_plan(output, …)`
  at `:142,155`, `join_plan(output, …)` at `:208,220`. `pack_key` is a fusible `Op` rather than a
  boundary, but it exists to pre-key a source for a shuffle/join, and both plan builders ARE the
  §5.4 boundary path, so one refusal message covers all three); `graphed.apply` and
  `graphed.read_columns`
  **expand into universes** (per-label results — `apply` returns a `Varied`, `read_columns` returns
  the union over all labels' members, §5.3; **the union is `None` — "read every column" — if ANY
  member's read set is `None`, else the sorted set union**, r17: `read_columns` returns
  `tuple[str, ...] | None` and `None` is the conservative answer, `projection.py:109-115,145-146`,
  so a plain set union would silently NARROW a conservative label's read list and starve its task); `graphed.compile_ir` and
  `graphed.aggregate_plan` **refuse** a `Varied` output with an error naming `graphed.universe` —
  they consume `arr.node_id`/`arr.session` directly (`execute.py:70`, `aggregate.py:86`) and
  §2.2's reserved-name rule makes the refusal a clean `AttributeError` seam rather than a compiled
  field op; the varied route to a plan is the §6.1c group API. **`graphed.evaluate_ir` is OUTSIDE
  the `Array`-consuming surface entirely and carries NO `Varied` disposition** (r14 — r12/r13 put it
  in the refusing set, which is unimplementable: measured, its signature is
  `evaluate_ir(compiled: CompiledGraph | bytes, backend, sources, *, externals=None)`
  (`python/graphed/execute.py:85-91`) — it never receives an `Array`, never reads
  `arr.node_id`/`arr.session`, and a "plain `Array` still works" positive control is false for it in
  the other direction too, since a plain `Array` is not a `CompiledGraph`). `graphed.broadcast_like`
  (the §6.1d seam, NEW in m48) **broadcasts**: with a `Varied` value and/or factor it returns a
  `Varied` whose labels are the §2.4 union, per label broadcasting that label's members (r14 — it is
  discoverable by any `Array`-annotation rule and was undisposed, so the exhaustiveness gate below
  would have gone red against a correct m48 implementation).
  **`graphed.reindex_to` (the §6.1d lineage seam, NEW in m48, r20) BROADCASTS** — the result's
  labels are computed by **COMPOSING THE LINKS IN LINEAGE ORDER, parent-to-child (r23, replacing
  r22's order-insensitive set expression "the §2.4 union … MINUS every label a projection link
  eliminates", which §6.1d's own "links compose in lineage order" contradicts whenever a
  mask-derivation link sits BELOW a projection link or two masks share a label name): a
  mask-derivation link UNIONS that mask's labels per §2.4, a `graphed.vary` link is the IDENTITY,
  and a universe/nominal PROJECTION link RESETS the accumulated label set to empty** —
  each member re-indexed by that label's own mask, so an UNVARIED value re-indexed across a
  `Varied`-mask link BECOMES a `Varied` carrying that mask's labels **while a value reached across a
  link kind (3) is that label's unvaried member and carries NO labels** — r21's unqualified "the
  §2.4 union" is false across a projection link, which §6.1d(B) admits by definition ("composing
  link kinds (1)-(3)") and whose own clause yields "an unvaried value in the ancestor's row space";
  it is also what §6.1d's r21 ordering rule and m48's `h.fill(graphed.nominal(sel).MET.pt,
  sel.MET.pt)` BARE-`hist` anchor depend on, and m48's lineage-seam anchor is split PER LINK KIND so
  the two readings cannot both be frozen (**r21 — the r20 "a `Varied` with the SAME labels"
  contradicted §6.1d(B)'s "label-aligned per §2.4" and is false of m48's own link-kind-(1) anchor,
  whose value `events.MET.pt` is a plain `Array` re-indexed into `sel`'s per-label row spaces; the
  narrow reading silently drops the mask's labels, the §2.5 confidently-wrong class, and the plan's
  own precedent is the other way — `broadcast_like` is classified *broadcasting* with §2.4-UNION
  labels**) —
  and **`graphed.unify_contexts` carries NO disposition**, taking context handles rather than
  `Array`s (the `evaluate_ir` treatment, r14); both are disposed here so the m48 gate does not
  discover `reindex_to` unclassified.
  `graphed.awkward.to_parquet` and `graphed_histogram.Histogram.fill` **accept** — a fifth
  disposition class, bound below: `to_parquet` takes `select=` per §6.4a, `fill` takes `Varied`
  values/weights/`sample` per §6. **`to_parquet` carries NO disposition until m51 and is NOT in
  m48's table at all** (r18 — r17 classified it *refusing* at m48 and *accepting* at m51 while
  naming it in m48's floor list and justifying the classification on the grounds that "the gate
  certifies a table entry": a test-author freezing that entry's VALUE — the most plausible reading —
  freezes it read-only for three milestones, and m51's bindingly required re-classification then
  reds it, leaving only a Test Dispute or an integrity violation. r17's m48 *refusal behaviour* also
  had no m48 anchor asserting it — new m48 source with zero frozen-suite diff coverage, the DoD
  argument r14/r16/r17 used elsewhere. Measured, there is nothing to refuse at m48:
  `to_parquet(array, destination, *, steps_per_file, compute, executor, prefix, column, behavior)`
  has NO `select=` parameter today (`python/graphed/awkward/io.py:206-216`), so a varied `select=`
  is an unexpected keyword until §6.4 lands; and `to_parquet` is not discovered dynamically — it is
  outside `graphed.__all__` entirely (appendix) — so dropping it from the m48 floor list removes it
  from m48's union at no cost in class coverage: measured, the annotation-wide filter yields
  `aggregate_plan`/`apply`/`join`/`join_plan`/`pack_key`/`read_columns`/`repartition`/`shuffle_plan`,
  six *refusing* and two *expanding*, while *broadcasting* and *eager-metadata* are supplied by the
  named `graphed.broadcast_like`/`graphed.context_of`): at **m51** it enters the table *accepting*,
  and m51's anchors assert the accepting behaviour. `Histogram.fill` is *accepting* from m48 and is
  the class's behaviourally real representative.
  **The disposition CLASS SET is enumerated exhaustively here, r16** (the m48 gate is table-driven
  and its floor requires "one member of each class", which is unwritable without the vocabulary —
  and two members of §2.3d's own named floor list, `to_parquet` and `Histogram.fill`, fit none of
  the three classes r15's floor named, while `graphed.context_of` is classified *eager-metadata*, a
  fourth borrowed from §2.3c): the legal §2.3d dispositions are **refusing / expanding /
  broadcasting / eager-metadata / accepting**, where *accepting* means the verb consumes a `Varied`
  operand and handles it internally without returning per-label results to the caller.
  **Exhaustiveness is kept by a DISCOVERY RULE, not by this literal list** (the self-repairing rule
  §2.3a/c already adopt), **and the rule is bound over the MEASURED signature surface, not over
  first parameters** (r14 — the r13 filter "callables whose FIRST positional parameter is annotated
  `Array`" discovers only `repartition`/`pack_key`/`join`/`shuffle_plan`/`join_plan` and provably
  MISSES four of the verbs disposed above: `compile_ir(session: Session, *outputs: Any)`
  (`execute.py:54-58`), `evaluate_ir(compiled: CompiledGraph | bytes, …)` (`:85-86`),
  `read_columns(arrays: Sequence[Array], source_nid: int)` (`projection.py:109`) and
  `apply(fn: Callable[..., object], *arrays: Array)` (`array.py:397`) — i.e. exactly the safety-
  bearing dispositions; `aggregate_plan(*outputs: Array)` (`aggregate.py:68`) is var-positional, so
  whether a first-parameter filter reaches it depends on how that filter treats `*args`. "The table
  cannot silently miss a verb" is therefore NOT achievable by any first-parameter filter over this
  surface and that phrasing is withdrawn): the m48 anchor
  enumerates `graphed.__all__` dynamically, filtered to `inspect.isfunction` members **any of whose
  parameter annotations MENTIONS `Array`** (including `Sequence[Array]`, unions and `*args: Array`),
  **UNION an explicitly NAMED freeze-time floor list**, and asserts every member of that union
  carries a disposition. **The named list is not restricted to non-`graphed.__all__` members** (r15
  — the r14 wording scoped it that way and therefore reached neither channel for `compile_ir`:
  measured against `graphed-latest`, the annotation-wide filter over `graphed.__all__` discovers
  exactly `aggregate_plan`, `apply`, `join`, `join_plan`, `pack_key`, `read_columns`, `repartition`,
  `shuffle_plan` — `compile_ir` is absent, because its parameters are annotated `Session` and `Any`
  (`execute.py:54-58`), while it IS in `graphed.__all__` (`python/graphed/__init__.py:12,46`; `:44`
  is `"apply"`, corrected r16), so it
  fell through BOTH channels while §2.3d bindingly disposes it and m48 freezes that disposition).
  The named list is: **`graphed.compile_ir`**, **`graphed.context_of`**, **`graphed.broadcast_like`**
  (both added r17), `graphed_histogram.Histogram.fill`, and — **from m51 only** (r18) —
  `graphed.awkward.to_parquet`. **`context_of` and `broadcast_like` are named because they are
  the SOLE representatives of two classes** (r17 — measured, the annotation-wide filter over
  `graphed.__all__` discovers exactly `aggregate_plan`/`apply`/`join`/`join_plan`/`pack_key`/
  `read_columns`/`repartition`/`shuffle_plan`, every one of which §2.3d classifies *refusing* or
  *expanding*; *broadcasting* is supplied only by `graphed.broadcast_like` and *eager-metadata* only
  by `graphed.context_of`, both NEW in m48 — so whether the frozen per-class floor can find them
  would otherwise depend entirely on the implementer's post-freeze parameter annotations, and
  `broadcast_like` is described as a NEUTRAL seam taking an arbitrary factor, for which `value: Any`
  is a plausible annotation. Naming them costs nothing and is the shape r14 used for
  `broadcast_like` and r15 for `compile_ir`). **The floor is asserted PER REPO, r16**: `graphed`'s
  m48 gate takes `{graphed.compile_ir, graphed.context_of, graphed.broadcast_like}` (`to_parquet`
  joins it at m51, r18) — `graphed-histogram` is in no extra at all (`graphed pyproject.toml:29-48`; CI installs
  `.[dev]`, `.github/workflows/ci.yml:34`) and the house pattern for reaching it is a module-level
  `pytest.importorskip` (`tests/frozen/preserve/m25/test_histogram_preservation.py:31`,
  `m27/…:185,207`, `m30/…:155`), which would SKIP the whole test and silently discharge both this
  gate and §2.2's reserved-name anchor with zero frozen-suite diff coverage — while
  `graphed_histogram.Histogram.fill`'s disposition is asserted in `graphed-histogram`'s flat
  `tests/frozen/m48`, which depends on `graphed` and already hosts every other fill-shaped m48
  anchor (§10).
  **Two exclusions are bound too** (r15): `inspect.isfunction` keeps classes such as `graphed.Varied`
  out of the enumeration, and **`graphed.vary` itself is excluded BY NAME** — it is the verb that
  PRODUCES containers, not one that consumes them, and its own annotations mention `Array`, so once
  m48 lands it would otherwise be discovered with no disposition class to carry (the same red-against-
  a-correct-implementation shape r14 fixed for `broadcast_like`). It
  carries §2.3a/c's **non-vacuity floor in the same test**: the discovered set is non-empty, is at
  least the freeze-time count, contains every member of the named floor list, and contains at least
  one member of **each class in the bound class set above that the repo's own table can host**
  (refusing / expanding / broadcasting / eager-metadata / accepting — r16; **the per-class floor is
  scoped to the hostable classes, r17**: at m48 `graphed`'s table has no *accepting* member, since
  `to_parquet` is out of the table until m51 (r18) and `Histogram.fill` lives in the other repo, so
  `graphed`'s m48 floor requires **at least one** member of each of {refusing, expanding,
  broadcasting, eager-metadata} — a containment floor, never an exact set, so m51's added
  *accepting* member cannot red it (r18);
  the *accepting* class's m48 representative is `Histogram.fill` in `graphed-histogram`'s flat
  `tests/frozen/m48`, and m51 adds the *accepting* assertion for `to_parquet`). This list is the
  freeze-time floor, not the definition; a
  verb whose signature mentions no `Array` and which is not named above (`evaluate_ir`) is out of
  scope by construction.
  **The m49 verbs this plan itself adds enter the table *expanding* when they land, r20** — §3.4's
  impact helper and §5.3's per-label projection-stats verb (§9.1) both answer PER LABEL over `Array`
  operands, so any annotation mentioning `Array` makes the m48 frozen gate discover them one
  milestone after the freeze. Nothing reds: the gate's self-repair rule puts each new function's
  classification in `src` (never in a frozen test) and every floor is a containment floor, so the
  only thing at stake is which class the m49 implementer picks — and this sentence picks it. m49's
  own anchors assert their per-verb shapes (§5.3's `{label: …}` mapping; §3.4's impact sets).
  (e) **Context-tag propagation** (the §6.1d substrate; NEW in r10 — it was previously implied,
  and mis-named "provenance"). Every `Array`/`Varied` produced from a contexted input carries a
  **context handle: a Python attribute on the frontend wrapper object, explicitly NOT part of
  node identity** — it never reaches `NodeKey` params/tokens/hashes (§1.2 and interning stay
  intact). **This is an Implementation Target, not free**: `Array` is `__slots__`-ed with no
  `__dict__` (`python/graphed/array.py:127-128`, `__slots__ = ("_node_id", "_session")`) and
  `NumpyArray` keeps it closed (`python/graphed/numpy/array.py:71-74`, `__slots__ = ()`), so an
  ad-hoc attribute raises `AttributeError` today. Binding: **one added slot, underscore-prefixed**
  (e.g. `_context`), so `Array.__getattr__`'s `startswith("_")` guard keeps it out of field
  access (`array.py:332-335`), **plus a read-only PUBLIC seam exposing it —
  `graphed.context_of(array)`-shaped, spelling pinned at m48 freeze, returning the handle or
  `None`** (r15 — the slot alone is not reachable across a package boundary: §6.1d requires
  `Histogram.fill` to read its inputs' handle, `fill` lives in `graphed-histogram`, and §9.1's
  surface is entirely context-TAKING (`labels`/`universe`/`nominal`/`weight`/`variations`/
  `selection`) with no `Array` → context read — so m48's fill-shaped anchors, all assigned to
  `graphed-histogram` (§10), were implementable only by reaching into another package's private
  slot, and the "spelling pinned at freeze" discipline had nothing to pin). It carries a §2.3d
  disposition — *eager-metadata* — so the m48
  exhaustiveness gate discovers it, the intended anti-drift property; listed in §9.1.
  **On a `Varied` it answers with the CONTAINER's handle — the most-derived member handle §2.1 binds
  — NOT with the nominal member's, r20** (r15-r19 wrote "answering on the nominal member for a
  `Varied`", which is the class LABEL's usual shape but is unsound for this one property: the
  eager-metadata argument works for `gak.fields`/`type_of` because §2.1's form compatibility makes
  every member agree, while §2.1's construction checks are form compatibility + Session + source and
  never row space, so `context_of` is the one per-member property the plan does NOT require to
  agree — §2.1 explicitly ACCEPTS members whose handles differ along one ancestry chain and refuses
  only divergent ones, so the most-derived handle may well belong to a non-nominal member. It is
  load-bearing: §6.4a(2a)'s r19 predicate is `graphed.context_of(select_mask) is
  graphed.context_of(record)` and both operands are routinely `Varied`, and its four m51 controls
  are verified against the CONTAINER reading). *Eager-metadata* here means only that the answer is
  produced without recording. m48's §2.3d table anchor carries the discriminator: a container built
  from an ancestor-handled nominal member and a more-derived non-nominal member answers with the
  MORE-DERIVED handle.
  A wrapper attribute is the only sound carrier, measured: two sibling contexts derived
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
  **ORIGINATION rule — a context STAMPS its own handle, overriding the merge result** (r14; it was
  unbound, and the merge rule alone gets the mainline sketch wrong): `Session.source` takes no
  `Array` and no context (`python/graphed/session.py:133-140`,
  `source(self, name, *, form, data, **params)`) and `record_op` merges only from its `inputs`
  (`:142-168`, a fresh wrapper per call), so nothing in the merge rule can give a *derived* context's
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
  classes, and derives its **AUXILIARY** call arguments from **argument fixtures that live in `src`
  beside the classification** — so a newly added function arrives with its classification AND its
  fixture and the frozen test stays untouched (the self-repairing property is preserved).
  **The CONTEXTED operand is owned by the FROZEN TEST, not by the fixture, and the assertion is
  positive** (r16 — the other half of the implementer-editable-`src` hole r15 closed for the exempt
  set: if a fixture supplies a context-free primary `Array`, both the input and the output handle
  are `None` and "the handle is preserved" degrades to `None == None`, passing while witnessing
  nothing, for every function whose fixture the implementer wrote): the frozen test constructs the
  context and substitutes its own contexted `Array` into the primary operand position; `src`
  fixtures supply only the auxiliary/typed operands the measured surface needs
  (`concatenate`'s second array, `unflatten`'s counts, `where`'s branches, `linear_fit`'s operands),
  and the gate asserts the result's handle is **NOT `None` AND IS the input's handle**.
  **For the CONTAINER-TRAVERSING class the two halves collide, and the fixture is bound as a
  TEMPLATE, r17**: `gak.zip`'s mapping IS its primary and only array-bearing operand
  (`zip(fields: Mapping[str, Array] | Sequence[Array], …)`,
  `python/graphed/awkward/functions.py:118-119`), so if that operand is fixture-supplied the frozen
  test has no position to substitute into and "the handle is preserved" degrades to `None == None`
  for exactly the class whose purpose is detecting `Varied`/handles INSIDE containers (the same
  applies to `linear_fit`, whose operands are all fixture-supplied). Binding: each `src` fixture
  declares a named **substitution SLOT** — a sentinel the frozen test replaces with its own
  contexted `Array`, *including inside a Mapping/Sequence argument* — and the gate asserts the
  substitution actually happened: the handle-bearing input of the produced call IS the test's own
  contexted `Array`, and only then that the result's handle is not `None` and equals it.
  **Each slot DECLARES the operand KIND it needs, and the frozen test owns one contexted `Array` of
  each kind, r22**: the enumerated classes span functions whose primary operands are incompatible
  and graphed type-checks the primary at RECORD time through the backend's `op_form`, so ONE
  test-owned array cannot serve them all — measured against `graphed-latest@ff7c607` with a
  contexted jagged-numeric `Array` (`from_awkward(s, "events", ak.Array([[1.0, 2.0], [3.0]]))`),
  `gak.num`/`unzip`/`drop_none`/`singletons`/`firsts`/`where`/`unflatten(a, num(a))` all record
  cleanly while `gak.with_field(a, gak.num(a), "x")` raises
  `GraphedTypeError: ill-typed op 'ak.with_field' … no tuples or records in array`, and r16 bars the
  fixture from supplying the primary. Binding: each `src` fixture's substitution slot names its
  operand KIND (flat numeric / jagged numeric / record / boolean mask / option type); the frozen
  test owns one contexted `Array` per kind, ALL read through the SAME context, and substitutes the
  kind the slot names. The context stays test-owned (r16's property intact) while the type
  requirement — a property of the function — stays beside its classification in `src` (the
  self-repairing rule). **The KIND VOCABULARY is frozen at m48, and that trap is recorded rather
  than ignored, r23** (the shape r18 used for `refusing == {gak.join}`): a gak function added later
  whose primary operand falls outside these five kinds arrives with its classification and fixture
  in `src` as designed, but the frozen test owns no operand of its kind — exercising it would
  require EDITING a frozen test, i.e. a Test Dispute. Nothing in m48–m51 trips it: measured over the
  65 public gak functions (`python/graphed/awkward/functions.py`), every primary among the
  *broadcast* / *container-traversing* / *tuple-returning* classes falls inside the five kinds;
  **(3)** the
  *eager-metadata* and *refusing* classes are EXEMPT by classification, not by omission, and the
  gate asserts the exemption set is exactly those two classes (so an exemption cannot be used to
  hide an unimplemented member) **plus a MEMBERSHIP floor on those two classes** (r15 — asserting
  the exempt CLASS NAMES constrains nothing about who is in them: classification and its fixtures
  are implementer-editable `src`, so an implementer unable to make `gak.where`/`concatenate`/
  `unflatten` propagate the handle could re-classify it as *eager-metadata*, keep the exempt set
  exactly those two names and stay green; only the four representatives m48 pins by name
  (`zip`/`unzip`/`fields`/`type_of`) are otherwise protected, out of a measured **65** public
  functions): **`gak.join` IS IN the *refusing* class and the refusing COUNT is ≥ the freeze-time
  count** — containment plus a monotone count, never an exact set (r18 — r16 wrote "exactly
  `{gak.join}` at freeze time" while the same sentence provided for a future gak boundary verb
  arriving with its classification in `src`; both cannot hold, since a frozen `refusing ==
  {gak.join}` equality reds the moment such a verb is classified. Nothing inside m48–m51 trips it,
  so this is a maintenance trap rather than a milestone blocker, and containment is the shape this
  clause already uses for the broadcast class) (r16 — "the bound §5.4
  boundary set" names a CONDITION, a variation cone crossing an Exchange/Join, not a name set, and a
  frozen assertion needs the operand; measured over `python/graphed/awkward/functions.py`, the only
  boundary verb among gak's 65 public functions is `join` at `:18` — there is no gak
  repartition/exchange/pack_key — so the freeze-time operand is `{gak.join}`, and a future gak
  boundary verb arrives with its classification in `src`, which is where the self-repairing rule
  wants it);
  every *eager-metadata*
  member's return annotation is non-`Array`; and the count of *broadcast*-classified functions is at
  least the freeze-time count; **(4)** the `Array` public surface of (a) is gated the same way,
  dynamically enumerated **and resolved on the CLASS per (a)'s r15 rule**, **but with its OWN
  one-line floor rather than (3)'s** (r16 — (3)'s clauses do not transfer: the `Array` surface's
  refusing member is `repartition`, not `gak.join`, and "every eager-metadata member's return
  annotation is non-`Array`" is false of `Array` methods generally): on the `Array` surface the
  refusing class is `{repartition}` and the broadcast count is ≥ the freeze-time count. Both gates
  carry (c)'s non-vacuity floor.
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
  **The CHANNEL is named, and its spelling is pinned at m48 freeze like every other new surface
  here** (r15 — the requirement was unwritable as stated: measured, `compile_ir` returns a frozen
  `CompiledGraph` carrying ONLY `ir: bytes` and `source_names: tuple[str, ...]`
  (`python/graphed/execute.py:36-45`), so there is no diagnostics channel, and a test-author had to
  invent both it and its shape — a returned field? `warnings.warn`? a separate accessor? — with a
  wrong guess frozen read-only): the report is an **additive `CompiledGraph` field** (a sorted tuple
  of unreached labels, empty when every registered label reaches an output) **or an equivalent
  read-only accessor over the same compile**; exact spelling pinned at m48 freeze. If it lands on
  `CompiledGraph`, note the interaction with m48's §7.2 schema-absence anchor, which is worded over
  the `ExecResult`/`Plan`/monitor schemas and not over `CompiledGraph`. The registration mechanism
  ("each container registered with its Session, weak reference") is likewise an m48 Implementation
  Target whose spelling is pinned at freeze — nothing in the anchors depends on it directly.
  **The §2.1 shift-after-weight ordering rule gets a diagnostic on the same channel (r16), and it is
  an m49 target** — a registered ambient weight factor whose reachability cone (§3.4, which lands in
  m49) contains a node a LATER shift `vary` replaces is reported, naming the factor and the varied
  collection, so the "pre-shift weight in every shift universe" case is not silent. Diagnostic, not
  an error: a weight that legitimately does not track the shift is a valid program.
- **§2.6 (The event context — systematics attach to `events`, functionally; owner semantics
  2026-07-30, respun functional per collaborator feedback 2026-07-30.)** The primary user idiom
  is not loose `Varied` threading but an **event context**: a frontend wrapper over the root
  event record carrying (a) the collections and (b) an **ambient event-weight registry** (itself
  a `Varied` of accumulated M29 factors). Pure frontend sugar over §§2.1–2.5 — no IR change,
  §3.1 intact. Binding, in the r6 functional form:
  (a) **The context reserves NO NAMES.** Attribute access, and `[]` **with a string (or list of
  strings)**, resolve ONLY tree content (collections/branches); `[]` **with an `Array`/`Varied`
  mask derives a new context** (§2.6c — `sel = events[gak.num(jets) >= 4]`, the sketch's central
  idiom), mirroring `Array.__getitem__`'s own mask-vs-field split (`array.py:344-371`).
  **A `slice` or `int` subscript on a CONTEXT is REFUSED**, naming the supported forms (r16 — the
  mirror is partial and m48 freezes context semantics: measured, `Array.__getitem__` also accepts a
  `slice`, recording a boundary `slice` reduction, and an `int`, recording `index`
  (`python/graphed/array.py:344-371`), so `events[:1000]` is expressible with no bound answer;
  row-slicing has no defined effect on §2.6c's per-label re-indexing rule, and refusal is the
  smaller commitment — a slice-derived context is not scoped in m48–m51). Every
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
  **CONTEXT HANDLE IDENTITY is bound here, once, r23** — three binding rules compare handles
  (§2.3e raises a divergence error when input handles are not on ONE ancestry chain, §6.1d(A)'s
  `graphed.unify_contexts` raises the same error, and §6.4a(2a) is a literal object-identity
  comparison, `graphed.context_of(select_mask) is graphed.context_of(record)`) while nothing said
  whether two contexts produced by EQUIVALENT pure operations are the same handle. The natural
  fresh-object-per-call implementation makes two reads of one universe SIBLINGS — neither an
  ancestor of the other — so the divergence rule fires on programs this plan scopes
  (`graphed.nominal(sel).MET.pt + graphed.nominal(sel).MET.phi` — the OP-level form m48's anchor
  actually freezes; `sel1 = events[mask]`, `sel2 = events[mask]`), a FALSE refusal whose diagnostic names a condition the program does not
  contain — the §2.5 confidently-wrong class, and an implementer's coin-flip frozen read-only for
  three milestones: **PURE DERIVATIONS ARE CANONICAL.** `graphed.nominal(c)`,
  `graphed.universe(c, L)` and `c[mask]` for the same mask (identical per-label node ids) return the
  **SAME context object**, memoised on the parent — while `graphed.vary` ALWAYS returns a fresh one
  (each call registers different content, so §2.3e's divergence rule keeps its meaning for the case
  it was written for, and §2.1's "always returns a NEW object" is untouched). m48's op-level
  divergence anchor gains the positive control that two separate `graphed.nominal(sel)` reads
  UNIFY instead of raising.
  (c) **Scoping is lineage.** A fill sees exactly the registrations present on the context its
  inputs were read from (§6.1d) — r5's fill-time-snapshot rule re-bound as immutability: a fill
  from a pre-`vary` context is unaffected by later `vary` calls *by construction*.
  **A read performed THROUGH a derived context yields THAT context's row space** (bound here, r17 —
  the central rule of the whole idiom, previously only asserted in passing inside §6.1d's rationale
  for value re-indexing ("`h.fill(events.MET.pt, sel.MET.pt)` would otherwise apply `sel`'s weight
  … against a value read at `events`' row count") and implied by the §2.6 sketch, while §6.1d's link
  kind (1), §6.4a's row-space predicates and m48's TWO re-indexing anchors — the §2.6c ambient-registry
  one and, r18, the §6.1d fill-time ancestor-VALUE one — are all defined against it):
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
  JES-varied `jets` — the derived context's ROW SET DIFFERS PER LABEL. Binding: its collections are
  `Varied` per §2.6b; `graphed.labels(ctx)` **INCLUDES** the mask's labels (the full answer is
  §2.2's union — ambient-weight labels ∪ varied-collection labels ∪ the derivation mask's labels;
  r13: "reports the mask's labels" was a strict subset of what a §6.1d fill from that context
  produces — on this section's own sketch, `sel` carries 104 ambient weight labels the mask does
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
  context-borne registration**, not a convention — **scoped, r14**: the loose primitive stays public,
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
  (iii) **the b-tag SF's ARGUMENT is the pt-CUT jets, not `sel.Jet`** (r19 — r6–r18 wrote
  `btag_sf(sel.Jet)`, which §2.6c binds to `events.Jet` re-indexed by `sel`'s mask, i.e. the UNCUT
  collection restricted to selected events, while the corpus reference computes the SF on the
  pt-cut jets and `_btag_weight` products a per-jet SF over `axis=1` — so sub-25 GeV jets change
  the weight and a test-author transcribing the sketch into m48/m49's reference matrix misses the
  15 stored references. Measured, `graphed-corpus src/graphed_corpus/analyses/systematics.py:60-76`:
  `jets = _apply_jes(events.Jet, …)`, `good = jets[jets.pt > 25]`, `sel_jets = good[sel]`,
  `weight = _btag_weight(sel_jets, …)`, with `_btag_weight` = `ak.prod(per-jet SF, axis=1)` at
  `:25-36`). `sel.Jet[sel.Jet.pt > 25]` is the corpus-faithful spelling — the object cut and the
  event re-index commute — and it is read THROUGH `sel`, so it also satisfies §2.1(b)'s row-space
  requirement by construction. m48's matrix anchor repeats the note alongside the existing
  `gak.full_like` / `stable()`-rounding mid-freeze-discovery notes.
  The neutral context *mechanism* (lineage, ambient weight, fill-inference seam) lives in
  `graphed` proper; the nanoevents-flavored constructor is awkward-idiom and lives in
  `graphed.awkward` (factorization rule preserved). The loose `graphed.vary` on Arrays (§2.1a)
  remains public — the context is built on it, not beside it.

## §3 IR and optimizer treatment

- **§3.1 (No new NodeKey.)** No Rust IR variant, no serialize tag, and **no optimizer SEMANTICS
  change** is added for variations. (r13 — "no optimizer change" read absolutely contradicts
  §8.2(i)'s m49 read-only remap accessor, which necessarily retains and returns data
  `dead_code_elimination` today discards, `src/optimizer/mod.rs:88-116`. The accessor is the ONE
  optimizer-adjacent addition in m48–m51: read-only, no new `NodeKey`, no serialize tag, no rewrite
  arm, no change to what the reducer produces. Cross-referenced from §8.2.) The varied universes are ordinary nodes; sharing is interning
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
  Plus a linear-growth bound (**time(128)/time(16) < 16.0**, the m4 threshold STYLE at m4's
  headroom RATIO rather than at m4's literal — r18): m4 spans 8× NODES and gates at 24.0, i.e. 3×
  headroom over linear, failing exponents ≥ ln24/ln8 = 1.53. This topology's node count grows only
  **5.37×** from N=16 to N=128 while N grows 8× (re-measured this session vs `graphed-latest@ff7c607`
  on this exact builder: N=16 → 1333 reachable nodes / 3.77 ms, N=128 → 7157 / 21.28 ms; time ratio
  5.64, node ratio 5.37), so the copied 24.0 would fail only exponents ≥ ln24/ln5.37 = 1.89 — a
  node-QUADRATIC reducer measures 5.37² ≈ 28.8× asymptotically, only 1.2× above the gate, and any
  non-negligible linear term pulls it under. 16.0 keeps ≈2.8× headroom over the measured 5.64 and
  still fails a node-quadratic reducer by ≈1.8×. (The self-scaling form
  `time(128)/time(16) < 3 × nodes(128)/nodes(16)` is equivalent and buildable — `reachable_nodes` is
  in `reduce()`'s returned report — if a future revision prefers it to a literal.) Replicating the
  m4 noise floor (`base = max(times[SIZES[0]], 1e-4)`) and best-of-N timing
  (`test_benchmark.py:28-33,40-43`). **This is the ONE frozen wall-clock gate in m48–m51, and it is
  a deliberate, named carve-out to R0.10a**: the project plan's M4 mandates a CI benchmark that
  fails on super-linear reduction time, and `tests/frozen/core/m4/test_benchmark.py` is the frozen
  precedent that discharges it. Every other performance claim in this plan (§6.2 axis scaling,
  §6.4c compression) is demoted to an R0.11 implementer-report measurement precisely because it has
  no such mandate. Threshold headroom is measured, not assumed: cba §optimizer §2 records 3.1 ms at
  N=16 and 16.7 ms at N=128 (ratio ≈5.4); re-measured r18, 3.77 ms → 21.28 ms (ratio 5.64) — both
  against the 16.0 gate bound above.
- **§3.4 (Impact-set API.)** A read-only frontend helper reports, per label, the **reachability
  difference** `reachable(label's outputs) − reachable(nominal outputs)` computed via
  `session.walk`. **The SURFACE is named, shaped and pinned, r24** — r0–r23 gave it no verb name, no
  operand and no return type, unlike every other new surface here, while m49 freezes behaviour
  through it and §4.3 offers it as an optional m48 cross-check (the same unwritable-as-stated defect
  r15 fixed for §2.5's diagnostic channel and r16 for §5.3's projection-stats verb): it is a
  **read-only `graphed` module verb over the same operands as `read_columns`/`graphed.labels`,
  returning `{label: tuple[int, ...]}`** — per label, that label's SORTED RECORD-time node ids
  (`tuple(sorted(...))` is the house shape, `python/graphed/projection.py:147`) — **listed
  in §9.1, exact spelling pinned at m49 freeze**. The element type is load-bearing, not defensive
  typing: `session.walk` exposes ids only through caller-supplied handlers and returns the root's
  value (`python/graphed/session.py:245-255`), so the return shape is otherwise a free
  implementation choice, and m49's anchor asserts MEMBERSHIP in the per-label value — an assertion
  written one way for node ids and another for `Array`s. It is **NOT an id watermark** (interleaved broadcast recording makes watermark
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
  form. **The r12–r15 predicate — "the intersection of `reachable(selection_mask)` with each label's
  `reachable(fill_node[label])` is identical across labels and equal to `reachable(selection_mask)`"
  — is WITHDRAWN in r16: it is satisfied BY CONSTRUCTION and cannot fail.** Measured: in any
  weight-variation program the filled value is post-selection (`obs = x[mask]`) and `Histogram.fill`
  records ONE External node whose `inputs` are the axis args followed by the weights
  (`graphed-histogram src/graphed_histogram/boost.py:175-178`, `inputs = list(args)` at `:175` then
  `inputs.extend(weights)`; one `record_external` over that list, `:196-210`), while `session.walk`'s
  post-order over `inputs_of` makes a node's cone the transitive closure of its inputs
  (`python/graphed/session.py:255-286`) — so `reachable(selection_mask) ⊆ reachable(fill_node[L])`
  for EVERY label in every implementation that fills selected data, the intersection is the constant
  `reachable(selection_mask)`, and both halves hold. It is a containment test, blind to the failure
  §4.3's binding sentence names: a label whose selection cone is a strict SUPERSET of nominal's
  (`mask_L = mask & g_L`) passes it. **Binding replacement — the converse, which is literally the
  binding sentence and directly readable**: per label, take the fill node's recorded `inputs` from
  the store and assert the **NON-WEIGHT prefix** (`store.nodes()[fill_id]["inputs"][:n_axes]`) is
  IDENTICAL to nominal's for every label — identical node ids ⇒ identical cones by interning
  (`src/store.rs:73-88`), and the `n_axes` split is exactly the recorded `params["n_axes"]`
  (`boost.py:180-212`; the frozen precedent counts that layout already —
  `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84-87` asserts
  `len(node["inputs"]) == 4` for one axis + three weights). A reachability cross-check MAY ride
  along, in the discriminating shape only:
  `reachable(fill[L]) − reachable(weight_input[L]) − {fill[L]}` identical across labels. Either form
  fails a `mask_L = mask & g_L` implementation; the withdrawn one passes it.
  **`session.walk` takes an `Array`, not a node id**
  (`session.py:245-252`, `root = array.node_id` at `:268`), so the test wraps each id as
  `Array(session, nid)` (`array.py:133-135`; `Array` is exported, `__init__.py:9`) — stated here to
  spare the mid-freeze discovery, the same service §4.1's `full_like` note provides.
  `fill_node[label]` needs a **public per-label channel that must be BUILT, and is bound in §9.1**
  (r13): today `Histogram.fill_nodes()` IS public (`graphed-histogram
  src/graphed_histogram/boost.py:218-219`, used by `tests/frozen/m29/test_multi_weight_fills.py:84`)
  but returns a bare `list[Array]` in staged-fill order with **no label attribution**, and §7.2 says
  only that the frontend *owns* the `(output, label) → node id` map — ownership is not an importable
  surface, and a frozen test cannot import an internal. So the r12 parenthetical
  ("`Histogram._fill_nodes` is private") named the wrong obstacle: the obstacle is the missing LABEL
  correspondence, and §9.1 pins the accessor's spelling at m48 freeze. Because the operands come
  from a fill, **this anchor sits in `graphed-histogram`'s half of the m48 split** (§10). The repaired impact-set form is an equivalent public
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
  `delta == len(cone)` comparison is tautological, review r0).
  **The witness MUST be built through the public `graphed.vary` surface** (r14): §3.3 tells the
  author to replicate `tests/frozen/core/m4/test_benchmark.py`, which builds with the raw
  `graphed.core.GraphStore` API (`import graphed.core as gc`; `add_source`/`add_op` — measured, and
  `tests/frozen/core/m4/test_systematics.py` likewise), so an author following §3.3 can hit every
  pinned integer while witnessing only `GraphStore::intern` — already frozen at m1/m4.
  **What the delta DOES and does NOT discriminate is restated in r15**, because r14's rationale was
  measurably wrong: re-recording the shared prefix through the SAME Session interns to the same ids
  and adds ZERO nodes (measured this session against `graphed-latest`: recording one op twice returns
  node id 1 both times and leaves `node_count()` at 2), so no arena-delta form can catch a
  prefix-re-recording implementation. The delta discriminates that **no per-universe COPY enters the
  arena** — i.e. labels are out of node identity (§1.2) and interning is engaged through the public
  `vary` path, which a per-universe store or a label leaking into `NodeKey` params would blow up.
  The re-recording concern is caught by §5.2b's single-read `part_reads == n_partitions`, which a
  per-variation re-run loop cannot pass; that is where it is anchored.
  **The measurement SPAN and the ORACLE are bound, and both are obtainable pre-implementation**
  (r15 — r14 bound the span as `node_count()` "before/after adding the SECOND label through
  `graphed.vary`", which cannot observe `K + 2`: under record-time expansion (Part I §3) the `vary`
  call introduces only the fork member, and the K chain ops and the terminating reduction are
  recorded AFTERWARDS, when the user applies the chain to the returned `Varied` — so bracketing the
  call measures Δ ∈ {0, 1}. r14 also said the integer is "re-measured through the frontend at
  freeze", which is unfollowable: under §12.1 the test-author freezes the suite before any `vary`
  implementation exists): **(1) SPAN** — `Session.node_count()`
  (`python/graphed/session.py:50-51`) after building the COMPLETE N=1 program versus after building
  the COMPLETE N=2 program in the SAME `Session` (the nominal re-record is free by interning), so
  the delta is exactly the second universe's suffix; **(2) ORACLE** — the same second universe
  hand-built WITHOUT `vary` in a separate `Session`, whose own node-count delta supplies the expected
  integer. That is an INDEPENDENT construction the author can run at freeze time, not a self-derived
  `delta == len(cone)` comparison (the tautology review r0 named), and it needs no
  frontend `vary`. `K + 2 = 52` is the raw-builder number and MUST NOT be assumed to carry over
  unchecked. Labels structurally identical to a
  prior label dedup to Δ = 0 by §1.2 — that case is witnessed separately as the dedup feature, in
  the **m48 §1.2 label-out-of-identity anchor** (§10), not under this witness. (b) **single-read
  witness bound to the reference-matrix run itself**: the
  read-counting partitioned source (m23 pattern) asserts `part_reads == n_partitions` — not
  `n_partitions × n_labels` — on the SAME Session/plan that reproduces the corpus references
  (**the m49 `graphed-histogram` half, §10/m49(i), where m48's vendored references live** — r16;
  r14/r15 said "the m49 frontend half", which contradicts §10: r12 moved m49's reference matrix out
  of `graphed` into `graphed-histogram`'s flat `tests/frozen/m49` and §10/m49(i) says explicitly
  "The §5.2b read witness binds to THIS run", while `graphed`'s `tests/frozen/frontend/m49` holds
  the NON-fill anchors and measurably cannot host a fill-based matrix without `importorskip`-SKIPping
  it — `graphed pyproject.toml:29-48` vs `.github/workflows/ci.yml:34`. The same reading applies to
  m48's matrix, which §10/m48 already places in `graphed-histogram`), so a per-variation re-run
  loop cannot pass. (c) **reduced-stage shape — on the §3.3 SHAPE but built through `graphed.vary`** (r14 gave it a
  program and a literal; r15 gives it the same surface correction §5.2a already carries): the shared
  prefix appears in exactly ONE stage, and the total stage count equals an **ORACLE**, not a literal.
  **The oracle is bound for the same reason §5.2a's is** (r16 — r15 corrected §5.2a's surface but
  left §5.2c's defective clause in place: the `stages == N + 1` / `reduced == 2N + 2` literals come
  from the raw `graphed.core.GraphStore` builder, as §3.3 and this paragraph both say, and "re-measured
  through the frontend at implementation time if the frontend construction differs" instructs a
  POST-FREEZE re-measurement of a frozen literal — a Test Dispute or an integrity violation under
  §12.1, since the author freezes before any `vary` implementation exists): the expected integer is
  taken from the **same N-universe topology hand-built WITHOUT `vary` in a separate `Session`**,
  reduced, its stage count read off — the independent construction §5.2a already binds for the arena
  delta — and the `vary`-built program MUST equal it. §3.3's raw-builder shape (N=16 → 17 stages,
  N=128 → 129) is the expectation for the oracle itself and MUST NOT be asserted directly of the
  `vary`-built program. **It does NOT ride the §3.3 benchmark fixture** — that fixture is
  a raw `graphed.core.GraphStore` construction (measured: `tests/frozen/core/m4/test_benchmark.py`
  builds with `import graphed.core as gc` / `add_source` / `add_op`, and §3.3 tells the author to
  replicate it), so asserting the stage shape there would re-assert the M4 frozen reducer contract
  and witness nothing about `vary`, under a section headed "witnesses that sharing engaged". It is a
  frontend, `vary`-built program in `graphed`'s `tests/frozen/frontend/m49` — the same fixture
  §5.2a needs and the placement §10/m49 already assigns it; `tests/frozen/core/m49` keeps the raw-
  `GraphStore` scaling benchmark only.
- **§5.3 (Projection.)** Column projection is the union over all requested outputs — correct today
  with zero changes (`read_columns` takes `Sequence[Array]`, `projection.py:109-147`); m49 pins a
  test where a shift needs an extra column (e.g. binned SF needing `Jet.eta`) and the union grows by
  exactly that field. Per-label projection stats make the read-width cost of a
  shift visible — **and that exposure is anchored in the same m49 test** (r12; it was binding
  but unanchored, and §3.4's own anchor covers impact sets, not read widths, so it could have
  shipped unimplemented with every m49 anchor green): the same test asserts the stats report the
  shifted label's extra column. **The SURFACE is named and pinned, r16** — r12–r15 said only
  "exposed via §3.4", but §3.4's API is a reachability difference over node SETS, not a read width,
  so the stats had no name, no shape, no return type and no "spelling pinned at freeze" clause,
  unlike every other new surface here (`graphed.context_of`, `graphed.weight`, `graphed.selection`,
  the per-label fill-node accessor, `graphed.broadcast_like`, `read_varied`, §2.5's diagnostic
  channel): it is a **read-only `graphed` module verb over the same operands as `read_columns`,
  returning `{label: tuple[str, ...] | None}`** — per label, that label's SORTED read set, computed
  by applying `read_columns` (`projection.py:109-147`) to each label's outputs — **listed in §9.1,
  exact spelling pinned at m49 freeze**. **The `| None` is load-bearing, not defensive typing**
  (r17): measured, `read_columns(arrays, source_nid) -> tuple[str, ...] | None` and `None` is a
  live, semantically INVERTED answer — "read every column", returned on whole-record consumption or
  a bare source read (`projection.py:109-115,145-146`, `if conservative or not needed: return None`).
  Under a bare `tuple[str, ...]` an implementer must render that as `()`, which reads as "reads
  nothing" — the exact opposite — or violate a frozen type. The m49 anchor carries a conservative
  label (one gak op applied directly to the source) asserting the `None`.
  **That conservative label rides a SEPARATE program (or a separate output set) from the
  union-growth assertion, and the scoping is binding, r22**: measured, `read_columns` carries ONE
  `conservative` flag across ALL the arrays passed and returns `None` if any one of them consumes
  the whole source record (`python/graphed/projection.py:130-146`, `conservative = True` at `:140`,
  `if conservative or not needed: return None` at `:145`), and §2.3d states the same for the varied
  union ("`None` if ANY member's read set is `None`"). With the conservative label inside the SAME
  varied program the union collapses to `None` and the "union grows by exactly that field" half is
  either vacuous (`None == None`) or red against a correct implementation. Equivalently, half (i)
  MAY be restated per label through the stats verb (`stats[jes_up] == stats[nominal] +
  ("Jet.eta",)`), which is immune to the interaction.
  Per-variation partition-level projection splitting is Phase 2.
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
  to varied graphs unchanged. **The observable consequence is PARTITION INVARIANCE, and that is
  what the m49 witness asserts** (r13): a per-partition constant seed
  (`np.random.default_rng(0)`) is reproducible, migrates events both ways, and still interns as one
  draw node — so it passes every other listed witness while giving the same event a different smear
  under a different partitioning. Content-seeded randomness makes the same event set at two
  different `steps_per_file` values produce byte-identical per-label results; a seeded-per-partition
  implementation does not.
  **The COMPARED QUANTITY is bound, because "byte-identical" is not a safe invariant for an
  aggregated float result** (r15): `steps_per_file` is a plan parameter, so changing it changes the
  grouping of float additions in the combine tree, and a CORRECT implementation can then differ in
  the last ulp — this plan concedes the effect in m48's own matrix bullet ("`bin_values`' driver-side
  rounding is what absorbs the float-summation-order differences a per-partition fill introduces"),
  and the existing partition-count-invariance precedent works only because its result is an int64
  histogram (`graphed tests/frozen/checkpoint/m8/test_resume.py:51-58` with
  `analyses.py:29-30` returning `np.int64` counts; contrast
  `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:75-79`, which asserts
  `array_equal` run-to-run at FIXED partitioning and only `allclose(rtol=1e-12)` against the eager
  fill). The invariance witness therefore compares **partition-local objects that concatenate
  deterministically** — the per-event/per-object SMEARED VALUES and the per-label selection MASKS —
  or an unweighted integer-storage count histogram; never a weighted float histogram. (b) **One draw, all universes**: the random vector is drawn once
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
  unchanged. Absent labels are absent, never silently duplicated from nominal.
  **This is the shape of the UNPACKED user-facing result, NOT of the plan's combined value, and the
  two are settled here in §6.1c's favour (r18)**: r6–r17 said "the combine BRANCHES on the two
  shapes", which is mutually exclusive with §6.1c's r17 sentence "The COMBINE needs no branch …
  under it every slot's value is a plain `bh.Histogram` … a key-wise `+`". m48 freezes BOTH ends
  (this section's result shape and §6.1c's indices layout), so the contradiction is a mid-milestone
  Test Dispute waiting to happen. Binding: **the plan's combined value is the FLAT slot-keyed
  mapping §6.1c binds — `{(output, label) → bh.Histogram}` for a VARIED output in sibling mode,
  `{(output, None) → bh.Histogram}` for an axis-mode output — and `_add_groups` stays a homogeneous
  key-wise `+`** (measured,
  `graphed-histogram src/graphed_histogram/boost.py:120-122`: `{label: a[label] + b[label] for label
  in a}`). **The slot keying is SCOPED to outputs a variation reaches, and that scoping is binding
  (r19)**: an output NO variation reaches keeps today's BARE `output_name` key — **and that rule is
  itself scoped to SIBLING-mode outputs, r22**: the MODE, not the variation count, decides an
  axis-mode output's key, so an axis-mode output whose fills carry no variations is still keyed
  `(output, None)` per §6.1c. That program is expressible — §6.2's opt-in is per-histogram and
  §6.2(ii) makes the frontend declare the axis ALWAYS, from an inferred label set that is
  `{"nominal"}` there — and m48/m50 freeze the plan value's slot-keyed shape directly, so without
  the scoping the test-author's pick between two defensible key forms is frozen read-only for the
  wrong reason (the user-facing result is identical either way: a bare histogram, which
  `graphed.labels` duck-types on `.axes`). r18's unqualified
  wording re-keyed a wholly UNVARIED group plan's value from `{output_name: hist}` to
  `{(output_name, "nominal"): hist}` — and sibling mode is the default for every program, so it
  broke the already-frozen m23 suite, which indexes `SequentialRunner().run(gh.plan({…})).value` by
  bare output name (`graphed-histogram tests/frozen/m23/test_group_plan.py:74-75` `out["hi"]`/
  `out["lo"]`, `:86,:89` `grouped["0"]`/`grouped["1"]`, `:99` `zero["hi"]`; the reducer's key IS the
  output name today, `boost.py:108-117` fed by `layout` built over `(output_name, Histogram)` pairs
  at `:282`) — while §10 binds the frozen m23 artifacts "binding and unchanged" and `plan()`'s
  declared return type is `Plan[dict[str, bh.Histogram]]` (`:262`) under the DoD's `mypy --strict`.
  All three key forms carry a plain `bh.Histogram` value, so `_add_groups`' key-wise `+` stays
  homogeneous whatever the key. m48's §6.1a anchor carries a wholly-unvaried positive control.
  The `{output_name: hist | {label: hist}}` shape above is what a bound **FRONTEND UNPACKER**
  produces from that value. **That unpacker is a NAMED read-only surface, not an
  unstated step** (r18 — three places assumed it ("the information the FRONTEND UNPACKER needs";
  "The frontend unpacks into the §6.1 named mapping"; this section's narrowing helper applied to
  `result[name]`) while nothing bound where it lives or what it is called, and measured there is no
  seam to hang it on: `Plan` is `(process, combine, empty, tasks, next_tasks, stop, open_once)` with
  NO finalize hook and `ExecResult.value` is exactly the combine output
  (`python/graphed/core/execution.py:206-224`), while `graphed_histogram.plan()` returns that `Plan`
  and nothing else (`src/graphed_histogram/boost.py:256-295`) — and adding a `Plan` field is
  foreclosed by §7.2's m48 schema-KEY-SET anchor, so a test-author would have had to invent the
  surface AND its spelling and freeze the guess read-only, the defect class already repaired for
  §2.5's diagnostic channel and §5.3's stats verb): a read-only **`graphed_histogram` module verb
  over the executed plan value ALONE — `graphed_histogram.unpack(value)`-shaped, exact spelling
  pinned at m48 freeze** — returning `dict[str, bh.Histogram | dict[str, bh.Histogram]]`.
  **It takes ONE argument, and the per-output shape is decided by the SLOT KEY FORM, not by a
  recorded MODE (r19)**: r18 declared a one-argument verb in §9.1 while describing it here as
  operating over the value PLUS the layout, which is unreachable from the value — measured, `Plan`
  has no layout accessor and `ExecResult` carries only `value`/`n_partitions`/`n_combines`/`stopped`
  (`python/graphed/core/execution.py:206-224`), the layout living inside `_GroupReduce`, the plan's
  `process` (`graphed-histogram src/graphed_histogram/boost.py:106-117,288`). The key form is
  total and per output: a BARE `output_name` key → that output's bare `bh.Histogram`; a
  `(output, None)` key → the axis-mode output's bare variation-axis histogram (§6.2 i-bis); the
  `(output, label)` keys of one output → `{label: hist}`. A varied sibling output always carries
  ≥ 2 labels (§1.1 makes labels non-empty and `"nominal"` is always present), so no output's shape
  is ambiguous, and this holds in a MIXED plan exactly as in a single-mode one. Listed in §9.1
  with the other m48 accessors; m48's §6.1a anchor is worded over it.
  The declared result
  type is therefore the value-dependent union
  `dict[str, bh.Histogram | dict[str, bh.Histogram]]` **at the unpack surface** — a real typing cost
  under the DoD's
  `mypy --strict` on src AND tests, accepted for the backward-compatibility win and paid for
  explicitly by a bound narrowing helper so callers do not
  hand-roll `isinstance` — `graphed.universe(result[name], label)` and `graphed.labels(result[name])`
  work uniformly on BOTH shapes (§2.2), a bare `hist` reading as the single label `"nominal"`.
  (b) **Structural fill-node arity** (again **sibling-mode only**). A fill combining shift labels
  S and weight labels W records
  exactly `1 + |S| + |W|` fill nodes — never the product (frozen-counted via the staged-fill list,
  the §2.4 discriminator). **S and W are defined by LOWERING BEHAVIOUR, not by the "shift"/"weight"
  vocabulary, r19**: `S` = the labels that require their own SIBLING fill node — those borne by any
  AXIS value **or by a `Varied` `sample=`** — and `W` = the labels borne ONLY by weight factors
  (ambient or explicit), which are the ones §6.2's axis mode can collapse into an evaluator-side
  loop. r15/r16 made `sample=` a first-class fourth label source that m48 freezes as
  ACCEPTED/expanded (`sample` is appended to the same `inputs` list with no type check today,
  `graphed-histogram src/graphed_histogram/boost.py:175-178`), while the taxonomy had only two
  classes: a label borne solely by `sample=` cannot ride the weight loop, which re-fills with
  different weights against a FIXED sample column, so it must lower as a sibling — and under the
  narrower reading both frozen arity formulas were wrong for such a program. Axis mode's arity is
  `1 + |S|` under the same definitions and is stated in §6.2, so m50 does not
  land a feature contradicting a count frozen in m49.
  **WHERE the `S`/`W` split is witnessable is bound too, r20, because the sibling formula cannot see
  it**: `1 + |S| + |W|` counts every label exactly once whatever its class, so m49's arity anchor is
  green under EITHER classification of a `sample=`-borne label and adding such a label to that
  fixture buys nothing discriminating. The split is observable only in AXIS mode, whose arity
  `1 + |S|` counts `S` and collapses `W`: **m50's equality anchor carries a label borne ONLY by a
  `Varied` `sample=`, asserting it lowers as a SIBLING (it counts in `S`) and that the axis-mode
  result still equals its sibling-fill decomposition.** **That fixture MUST use a `Mean` or
  `WeightedMean` STORAGE and per-label sample values that DIFFER, r21**: measured, boost_histogram
  1.8.0 rejects `sample=` on the default `Double()` storage AND on `Weight()`
  (`TypeError: Keyword(s) sample not expected`) and accepts it on `Mean()`/`WeightedMean()`, while
  `graphed-histogram`'s evaluator passes `sample` straight through to `h.fill`
  (`src/graphed_histogram/boost.py:60-71`) — so on the default storage the anchor dies at EVALUATION,
  after the freeze, against a correct implementation; and with a storage that discards the sample the
  two classifications are indistinguishable, i.e. the anchor is vacuous. (`_spec.py:19-27`'s
  `_STORAGES` carries both mean storages, and the variation-axis spec round-trips and adds on them —
  verified this session.) Without it an implementation classing a
  sample-only label into `W` passes every m48-m49 anchor and, at m50, folds it into the evaluator's
  weight loop — which re-fills with different weights against a FIXED sample column, i.e. a silently
  WRONG histogram no frozen test would see.
  (c) **The single-histogram `.plan()` path refuses varied fills**: `_SumFills` sums ALL staged
  fill nodes into one histogram (`boost.py:88-98`) and would silently merge universes; varied
  histograms route through the group-reduce path (`_GroupReduce` `{label: hist}` generalized to
  two-level keys, `boost.py:100-122`), and **`.plan()` raises — pointing at the group API — on a
  `Histogram` that is VARIED *or* in §6.2 AXIS MODE** (equivalently: whose staged fill nodes' spec
  differs from the `__init__`-time `self._spec`). **The trigger is re-keyed on the MODE in r24**,
  matching §6.1a/§6.1c's own r22 rule that "the MODE, not the variation count, decides": r14's
  "varied" wording leaves the axis-mode-with-NO-variations program — legal, and the fourth output
  m50's r23 anchor adds — falling THROUGH the refusal into the same hazard, since §6.2(ii) declares
  the variation axis ALWAYS in axis mode (a 1-bin `{"nominal"}` axis there), so its fills' spec
  still differs from `self._spec` and `.plan()` dies with an opaque `boost_histogram` error instead
  of the bound refusal — measured, bh 1.8.0: `bh.Histogram(Regular(3,0,1)) +
  bh.Histogram(Regular(3,0,1), StrCategory(['nominal']))` → `ValueError: axes have different
  length`. **The refusal is GENERAL — sibling mode AND §6.2's axis mode** (r14; r13 rescoped
  it to sibling mode on the grounds that `_SumFills`' plain addition over disjoint variation-axis
  bins merges nothing, which is true of the ADDITION but not of the SPEC it starts from: measured,
  `Histogram.plan` passes `_SumFills(self._spec)`/`_ZeroHist(self._spec)`
  (`graphed-histogram src/graphed_histogram/boost.py:244-253`) and `self._spec` is fixed in
  `__init__` (`:146-150`) — the very fact §6.2(i) uses to prove a plan-time variation axis
  unimplementable — so under §6.2's FILL-time declaration the reducer starts from
  `zero_of(spec-without-variation-axis)` and adds fill results that carry it; measured on
  boost_histogram 1.8.0, `bh.Histogram(Regular(3,0,1)) + bh.Histogram(Regular(3,0,1),
  StrCategory(['nominal','jes_up']))` → `ValueError: axes have different length`. §6.1c's per-slot
  spec repair is scoped to `_GroupReduce`'s layout and does not reach `_SumFills`/`_ZeroHist`, which
  take a single spec and have no slot). Axis-mode programs therefore also route through the group
  API; no m50 anchor needs `Histogram.plan` to SUCCEED on an axis-mode histogram (r24: m50's
  fourth output asserts it RAISES this refusal, which is the axis-mode arm's only coverage). **The reducer's LAYOUT changes shape, and that is binding, not an implementation
  detail** — "generalized to two-level keys" is satisfiable while shipping the §7.2 bug: today
  `layout` is `tuple[tuple[str, int, str], ...]` = `(label, n_fills, spec)` sliced
  **positionally** over the distinct-output list (`boost.py:100-117`, `for j in range(i, i + k)`,
  built from `len(h._fill_nodes)` at `:282`), so the moment two marked fills intern to one node —
  the case §1.2 mandates and m48 freezes — `sum(k)` exceeds `len(values)` and the reducer
  mis-slices or `IndexError`s (`aggregate.py:57-65` passes `evaluate_ir`'s values straight to
  `reduce`; `mark_output` de-dups, `src/store.rs:147-156`; `execute.py:126` returns one value per
  DISTINCT output). Binding: **`layout` carries per-slot output INDICES**, not counts —
  `tuple[tuple[str, tuple[int, ...], str], ...]` (or `{(output, label): [indices]}` for the
  two-level shape) — derived frontend-side per §7.2 as **the index of each marked record id's FIRST
  OCCURRENCE in `plan()`'s OWN ordered `fill_nodes` list**, so a shared node id **replicates** into
  every slot that needs it instead of shifting positions. **The operand is that list, NOT the
  compiled output list, and NOT §7.2's `aggregate_plan` seam (r21, correcting r18/r19)**: measured,
  the compiled artifact's `outputs()` are POST-REDUCTION ids that cannot be joined to the record ids
  `plan()` owns (§7.2 r21 probe), while `fill_nodes` is built at
  `graphed-histogram src/graphed_histogram/boost.py:281` — one line BEFORE `layout` at `:282` and
  five before the `aggregate_plan` call at `:286` — and `evaluate_ir` returns one value per distinct
  requested id in exactly that first-occurrence order. The seam stays an m48 target for §7.2's merge
  refusal and m49's `variation_labels`; this layout needs nothing from it.
  **The AXIS-MODE slot is bound here too — and it is scoped to m50, with §6.2** (r15; scoping added
  r16, mirroring §6.1a/§6.1b's sibling-mode scoping: axis mode does not exist until m50, so leaving
  this source in m48's "§6.1" target lands it with zero m48 frozen coverage — the DoD's ≥90%
  diff-coverage-FROM-THE-FROZEN-SUITE gate, exactly the argument r14 used to move §3.4 out of m48;
  m50's scaling anchor is already worded over this paragraph — §6.1c bound only the sibling `{(output, label)}`
  shape while axis mode needs the opposite: its `1 + |S|` fill nodes collapse into ONE slot per
  output whose value is a BARE histogram carrying the variation axis, §6.2(i-bis), not a
  `{label: hist}` mapping; nothing said how such a slot is keyed, and m50's scaling anchor counts
  exactly these slots): an axis-mode output contributes **exactly ONE slot, keyed `(output, None)`**,
  gathering ALL that output's fill-node indices, and its per-slot value is the bare histogram.
  **That keying holds WHATEVER the output's label count — the MODE decides, not the variation count,
  r22** (§6.1a's bare-`output_name` rule is scoped to SIBLING-mode outputs; an axis-mode output no
  variation reaches is still `(output, None)`). A
  plan MAY therefore carry sibling-mode and axis-mode outputs together. **The layout records NO
  per-output MODE (r18's field is DELETED, r19)**: the three key forms §6.1a binds — bare
  `output_name`, `(output, label)`, `(output, None)` — are disjoint and per OUTPUT, so the unpacker
  reads the shape off the keys in a MIXED plan exactly as in a single-mode one, which makes the MODE
  field unwitnessable: an implementation that never records it passes every m48–m51 anchor,
  including m50's mixed-mode one, so it could not carry a discriminating frozen test. It is also
  what forced §9.1's `unpack(value)` to contradict §6.1a's "value plus the layout" — measured, the
  layout is not reachable from the executed value (`python/graphed/core/execution.py:206-224`).
  A mixed-mode plan stays m50's anchored case for the UNPACKING and per-slot-spec behaviour it is
  the only program to exercise (§10/m50). **The COMBINE needs no branch**
  (r17 — r15's "the per-slot VALUE TYPE is recorded in the layout and the combine branches on it"
  asks for something the bound keying makes unnecessary: under it every slot's value is a plain
  `bh.Histogram` — a sibling slot `(output, label)` holds one, an axis-mode slot `(output, None)`
  holds one carrying the variation axis — what actually varies per slot is the SPEC, which this
  paragraph binds separately as the fill node's spec and which `_GroupZero` already consumes per
  slot, `graphed-histogram src/graphed_histogram/boost.py:127-130`) — measured, `_add_groups` is
  `{label: a[label] + b[label] for label in a}` (`graphed-histogram
  src/graphed_histogram/boost.py:120-122`), a key-wise `+` that requires the value type be uniform
  PER KEY, which the `(output, None)` keying gives by construction. (Latent
  today for two unvaried histograms with identical fills; variations make it routine.) **The
  layout's third element — the per-slot spec — is the FILL node's spec, not the histogram
  object's** (r12): today every consumer takes it from the histogram (`boost.py:282`
  `layout = tuple((label, len(h._fill_nodes), h._spec) …)`; `_GroupZero` builds `zero_of(spec)`,
  `:100-130`; `Histogram.plan` passes `_SumFills(self._spec)`/`_ZeroHist(self._spec)`, `:244-253`),
  which is fixed in `__init__` (`self._spec = spec_of(self)`, `:146-150`) — so under §6.2's
  fill-time axis declaration the zero/identity histogram would lack the `"variation"` axis the
  evaluator's output carries, and `_add_groups`' `+` would fail or mis-combine. Binding: the slot
  spec is the spec baked into that fill node's params (`:180-212`). **A sibling slot maps to ONE
  fill node, so "that fill node" is unambiguous there; for an AXIS-MODE slot, which gathers `1 + |S|`
  fill nodes, the slot spec is that of ANY of the gathered nodes and an implementation MAY assert
  they agree, r22** — §6.2(i)'s cross-fill agreement rule forces one inferred label set per
  axis-mode histogram, hence one variation axis, hence one spec; stating it spares the reader the
  derivation, since `_GroupZero` consumes the spec per slot
  (`graphed-histogram src/graphed_histogram/boost.py:127-130`).
  (d) **Ambient-weight application (the §2.6 completion of register-then-forget).** `fill` reads its
  input Arrays' **context handle** (§2.3e — a Python-object attribute on the frontend wrapper,
  outside node identity; NOT `Provenance`, which is source-location only,
  `provenance.py:26-33,66-79`, and NOT `Session._provenance`/`sourcemap()`) and **auto-applies that
  context's ambient weight** (§2.6c lineage rule — contexts are immutable, so *which context* fully
  determines *which registrations*): the fill's label set is the §2.4 union of value-borne labels,
  ambient-weight labels, and explicit `weight=[...]` factor labels — **computed on the inputs AFTER
  the lineage step below (unification + re-indexing/projection), not before it, r21**, so a value
  reached across a universe/nominal PROJECTION link (kind (3)) contributes NO labels, having been
  projected to one label's unvaried member. Nothing sequenced the two before, and for kind (3) the
  order changes the answer (kinds (1) and (2) are label-preserving, so it is immaterial there): on
  m48's own anchored fixture `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` the unified context is
  `graphed.nominal(sel)` — whose ambient weight is that label's member and whose `graphed.selection`
  is an unvaried `Array` (§2.2) — so the ancestor value is the ONLY label source, and the two orders
  give a labelled result with per-universe-identical content versus a wholly unvaried one. Under
  this rule that fill is UNVARIED and §6.1a's bare-`hist` shape applies; m48's anchor says so, which
  is also its discriminator against a "labels kept, contents identical" implementation. So a plain Jet-pT fill
  yields the jes/jer universes AND the pileup/PDF universes with zero per-fill bookkeeping (the
  owner's simultaneity requirement). **The union's ORDER is bound here too**, because §2.4 binds
  only a BINARY combination while this is three-way (and a fill may carry several varied axis
  values): the fill folds LEFT in a fixed operand order — **axis values in argument order, then
  the ambient weight, then explicit `weight=[...]` factors in list order** — each fold applying
  §2.4. **`sample=` folds LAST, after the explicit factors** (r15 — §2.3d binds "`Histogram.fill`
  accepts `Varied`" while this enumeration named only axis values, the ambient weight and explicit
  factors; measured, today's `fill` type-checks `args` and `weights` but appends `sample` to the same
  `inputs` list with NO check — `graphed-histogram src/graphed_histogram/boost.py:160-178` — so an
  undisposed `Varied` sample falls through into `record_external` and dies on `.node_id`, the §2.3b
  unchecked-fall-through shape). Without it two conforming implementations produce different label
  orders for one program:
  a determinism-gate difference (§3.2) and a different `_GroupReduce` layout (§6.1c).
  `weight=[...]` *adds* factors; `unweighted=True` opts out
  (counts histograms). **What `unweighted=True` suppresses, and its interaction with an explicit
  `weight=[…]`, is bound here, r19** (it was introduced in one clause and m48's anchor names it
  bare, so a test-author would freeze a guess about NEW source — measured, today's signature is
  `fill(self, *args, weight=None, sample=None, threads=None)`,
  `graphed-histogram src/graphed_histogram/boost.py:152-158`, with no such parameter): it suppresses
  the AMBIENT weight **and** any explicit `weight=[…]` — a counts histogram carries no weight at all
  — and supplying both `unweighted=True` and a non-`None` `weight=` in ONE call is a **record-time
  error naming both**, the §2.5 validation-over-convention shape (silently letting one win is the
  confidently-wrong class). **The consequence is stated, not hidden, r24**: "suppress the AMBIENT
  weight but apply my own factor" is therefore NOT expressible from a contexted program in v1 —
  every fill from a contexted value applies that context's ambient weight (this section), reading
  through `graphed.nominal`/`graphed.universe` still yields a context carrying it (§2.2), and the
  only opt-out also kills the explicit factor; only an all-loose fill escapes. Parked in §11 (the
  v2 answer is a context-level detach or a narrower `unweighted=` that suppresses the AMBIENT
  factor only); §9.1's `graphed.weight(ctx)` rationale is corrected in r24 to stop naming it. **Its effect on the fill's LABEL SET is bound here too, r23**: a
  SUPPRESSED weight contributes NO labels — the label set above is computed over the factors the
  fill ACTUALLY APPLIES — so a contexted `unweighted=True` fill whose only variation source is the
  ambient registry is UNVARIED and returns a BARE `hist` (§6.1a), not a `{label: hist}` mapping of
  per-universe-identical counts. Without it the clause had two defensible frozen result shapes,
  exactly the ambiguity r21 closed one clause earlier for the projection link, and m48's anchor
  ("counts equal to an unweighted eager reference") is satisfied by BOTH. m48's anchor is worded
  over the bare-`hist` shape, which is also its discriminator against the labels-kept reading.
  Inputs whose contexts sit on one ancestry chain unify to the
  **most-derived** context, **and every ancestor-context VALUE is re-indexed to the unified
  context across the intervening lineage links, label-aligned per §2.4** (r12; **stated PER LINK
  KIND in r15**, because the r12/r14 wording — "by the intervening derivation mask(s)" — is total
  only if every link is a mask derivation, which r14 made false in two places: §2.2 binds
  `graphed.universe`/`graphed.nominal` to return a CHILD context, and §2.6b binds `graphed.vary` to
  return one, and neither link carries a mask. On this section's own cited example
  `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` the unified context is the child, the ancestor
  value carries per-label row sets (§2.6c), and no mask relates them — so the rule as written had no
  operand while m48 freezes the outcome). The three link kinds:
  **(1) mask-derivation link** (`ctx[mask]`, §2.6c) — re-index the ancestor value by THAT mask,
  label-aligned per §2.4 (each label's member by that label's mask, nominal's by nominal's);
  **(2) `graphed.vary` link** (§2.6b) — IDENTITY: the row space is unchanged, only registrations
  differ;
  **(3) universe/nominal projection link** (§2.2) — PROJECT each ancestor `Varied` value to that
  label's member (falling back to its `"nominal"` member per §2.4), yielding an unvaried value in
  the ancestor's row space, then continue with the links below it. Links compose in lineage order,
  parent-to-child): unification alone
  is not enough, because §2.6c re-indexes the ambient weight to the derived row count, so
  `h.fill(events.MET.pt, sel.MET.pt)` would otherwise apply `sel`'s weight (row count = |sel|)
  against a value read at `events`' row count — a length mismatch whose only symptom is the
  execution-time refusal below, whose message is about the wrong thing. Re-indexing is the same
  operation §2.6c already binds for the ambient registry, applied to the values.
  **THE SURFACE THAT MAKES THIS IMPLEMENTABLE ACROSS THE PACKAGE BOUNDARY IS BOUND HERE, AND IT IS
  AN m48 IMPLEMENTATION TARGET IN `graphed`, r20.** `Histogram.fill` lives in `graphed-histogram`, a
  DIFFERENT distribution (`src/graphed_histogram/boost.py:153-212`, verified at `211cbbe`), and
  §2.3e already fixed exactly this class once for the handle itself ("the slot alone is not reachable
  across a package boundary" — hence `graphed.context_of`). The LINEAGE RELATION between two handles
  and the intervening masks are NOT fixed by that: §9.1's m48 surface is
  `labels`/`universe`/`nominal`/`weight`/`context_of`/the per-label fill-node accessor/`unpack`, none
  of which relates two handles or yields a derivation mask, and `graphed.selection(ctx)` — the only
  bound route to one — is m51. As written, m48's own `graphed-histogram` anchors (§6.1d's
  link-kind-(1) ancestor-VALUE re-indexing and the projected-VALUE half of the universe/nominal
  clause, §10) were satisfiable only by reaching into `graphed`'s private context object — the very
  thing `context_of` exists to prevent. Binding, both READ-ONLY, exact spellings pinned at m48
  freeze, listed in §9.1:
  **(A) `graphed.unify_contexts(*handles)`-shaped** — returns the most-derived handle when the
  non-`None` arguments lie on ONE ancestry chain (`None` when all are context-free; context-free
  arguments are ignored, the adopt rule below), and raises the §2.3e divergence error naming both
  contexts otherwise;
  **(B) `graphed.reindex_to(value, ctx)`-shaped** — returns `value` re-expressed in `ctx`'s row
  space by composing link kinds (1)-(3) in lineage order, label-aligned per §2.4; identity when
  `value` already carries `ctx`'s handle or carries none; raising when `value`'s handle is neither
  `ctx`'s nor an ancestor of it (the §2.1(b) direction rule, r20).
  With those two, the fill's entire lineage step is `unify_contexts` over its inputs' `context_of`s
  followed by `reindex_to` per input, and `graphed-histogram` imports nothing private. §2.3d
  dispositions: `reindex_to` **broadcasts** — the result's labels are obtained by composing the
  links in LINEAGE ORDER (a mask-derivation link unions that mask's labels per §2.4, a `vary` link
  is the identity, a universe/nominal projection link RESETS the label set to empty), **r23**
  (r22's order-insensitive "the §2.4 union … MINUS every label a projection link eliminates" reads
  the same for a single link but diverges once links COMPOSE, which this very paragraph orders;
  correcting in turn r21's unqualified "the §2.4
  union of the value's and the intervening masks'": across a path containing a kind-(3) link the
  result is that label's unvaried member and carries NO labels, per kind (3)'s own clause above and
  this section's r21 ordering rule, on which m48's BARE-`hist`
  `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` anchor depends; m48's lineage-seam anchor is
  split per link kind so the two readings cannot both be frozen — §2.3d). **The ORDERING half is
  knowingly left UNANCHORED, r24** (the plan's convention for such rules — §2.2's term-(c) vary-link
  half, §6.4e's no-private-import rule, §7.2's "MUST NOT compile a second time" — marked so a
  reviewer does not read it as a coverage gap): r23's sequential rule and r22's order-insensitive set
  expression agree on every ONE-link path and on the natural two-link path (mask-then-projection:
  both empty), and diverge only where a MASK link sits BELOW a PROJECTION link (a root value
  re-indexed to `graphed.nominal(sel)[mask2]`), which no m48–m51 anchor builds — m48's lineage-seam
  anchor is split per SINGLE kind and its fill fixtures cross one link each. A test-author who wants
  it anchored can add the two-link, both-per-event value
  `h.fill(events.MET.pt, graphed.nominal(sel)[mask2].MET.pt)` to an existing m48 fixture.
  `unify_contexts` takes context handles rather than
  `Array`s, so — like `evaluate_ir` (§2.3d r14) — it is outside the `Array`-consuming surface and
  carries NO disposition. m48 anchors them where each is observable: `graphed`'s half asserts (A)'s
  most-derived answer plus its divergence refusal and (B)'s identity and wrong-direction refusals,
  while the VALUE-level re-indexing stays in the fill-shaped `graphed-histogram` anchors that
  consume it.
  **Both worked examples in this paragraph use SAME-GRANULARITY axis values, and that is
  deliberate, r19** (r12–r18 wrote them as `h.fill(events.MET.pt, sel.Jet.pt)` and
  `h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)`, which cannot execute for a reason unrelated to
  the mechanism they illustrate — and m48 froze both as fixtures): the evaluator flattens each AXIS
  input INDEPENDENTLY and hands them to `boost_histogram`
  (`graphed-histogram src/graphed_histogram/boost.py:39-47,60-71`), which requires equal lengths
  across axes — measured, bh 1.8.0: `bh.Histogram(Regular(3,0,10), Regular(3,0,10)).fill(
  np.arange(3.0), np.arange(5.0))` → `ValueError: spans must have compatible lengths`. Re-indexing
  fixes an ancestor value's row COUNT, not its per-object STRUCTURE, and the broadcast seam bound
  below is scoped to WEIGHT factors — nothing broadcasts one axis value against another, and
  mixed-granularity multi-axis fills are NOT scoped in m48–m51. A per-event and a per-object value
  therefore never share one fill's axis list; the link-kind mechanisms need no such program.
  Contexts on **divergent branches are a hard error** naming both. **The
  fill raises it itself**: §2.3e's op-level rule is early detection, but the fill is a combining
  point no op precedes — it is the first place independent axis/weight/sample handles meet
  (`boost.py:154-212` collects them into one `inputs` list and records one node) — so the fill
  runs the same most-derived unification and divergence check across all axis values, all explicit
  weight factors, and the winning context's ambient weight.
  Context-free (loose) inputs alongside contexted ones adopt the unified context **for LABEL
  ALIGNMENT only; their row space is NOT adjusted** (r14 — the re-indexing bound above applies to
  ancestor-CONTEXT values, using the intervening derivation masks; a loose value carries no handle,
  so no intervening mask is known and no re-indexing is possible, yet it may sit in the root row
  space while the unified context's ambient weight is at `|sel|` rows). When the execution-time
  length refusal below is traceable to a loose VALUE rather than a weight factor, its message names
  that value — not "the offending factor" and not "pass the value unflattened", both of which are
  the wrong diagnosis there. An all-loose
  fill is unweighted (the r4 primitive path, still supported). **Every weight factor the fill
  applies — the ambient one AND explicit `weight=[...]` factors — is broadcast to the fill's value
  structure**, not just the ambient one (the recording TRIGGER is the one §6.3(2) states: a fill
  carrying a context handle OR any `Varied` input; a fill with neither records as today — r16): the evaluator flattens each input independently and
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
  (`graphed-histogram pyproject.toml:21` runtime vs `:25-39` dev — re-counted r13, corrected here
  r15), and `gak.broadcast_arrays` records the
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
  records `ak.broadcast_arrays`; **the numpy idiom is a NO-OP — bound, not an either/or** (r13; the
  r12 wording left "a no-op … or a refusal" to the implementer, and the two are not
  interchangeable: one makes an all-numpy varied fill work, the other makes it fail). `graphed.numpy`
  is rectilinear and its shapes are numpy's own (`python/graphed/numpy/__init__.py:8`; measured: no
  broadcast op exists there to inherit), so the seam returns the factor unchanged and a genuine
  shape mismatch surfaces as numpy's own error at execution — the same execution-time refusal shape
  bound below. The seam is owned by `graphed` proper; the
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
  single-weight-loop evaluator shape cannot carry — **and in axis mode a shift sibling TARGETS the
  same pre-declared variation axis** (binding, r17: the r6–r16 "MAY" read as an either/or while the
  next sentence asserts the arity `1 + |S|` unconditionally, §6.1c binds the axis-mode output to ONE
  slot gathering ALL its fill-node indices with a BARE histogram value, and m50 freezes "a mixed
  shift+weight program lands in ONE axis-mode histogram equal to its sibling-fill decomposition" —
  so an implementer taking the optional reading and lowering shift labels as ordinary sibling slots
  conforms to §6.2 and fails the frozen m50 anchor, the class r13 closed for the numpy broadcast
  seam), writing its label as the scalar category value of its own fill and contributing **no**
  per-label sibling slot:
  one histogram carrying both classes, filled from separate passes with a scalar label, is the
  field's actual layout in both eras of the confirmed exemplar (lit §ewkcoffea-confirmed), and
  scalar-string broadcast is probe-verified. The m50 equality anchor covers both the weight-label
  evaluator loop and a mixed shift+weight program landing in ONE axis-mode histogram equal to its
  sibling-fill decomposition. **Axis-mode fill-node arity is therefore `1 + |S|`** (only `W` — the
  labels borne ONLY by weight factors — collapses into the evaluator-side loop), which is why
  §6.1b's `1 + |S| + |W|` is scoped to sibling mode. **`S` and `W` carry §6.1b's r19 lowering
  definitions here too**: a label borne by a `Varied` `sample=` is in `S` and lowers as a sibling
  writing its own scalar category value, since the evaluator's weight loop re-fills against a fixed
  sample column and cannot carry it.
  **The per-fill variation payload needs its own CARRIER, and it is bound here, because the obvious
  channel does not exist** (r15): both halves above are per-FILL information — a shift sibling
  writes ITS label as the scalar category value of its own fill, and the weight loop needs ITS
  ordered weight-label subset — but measured, an External evaluator is resolved solely by the
  payload's content hash, which today is `content_hash(self._spec)`
  (`graphed-histogram src/graphed_histogram/boost.py:180-212`: `chash = content_hash(self._spec)`,
  `PayloadDescriptor(content_hash=chash, …)`, `self._evaluators[chash] = evaluator`), the plan-time
  registry merges every histogram's evaluators into ONE dict keyed the same way (`:283-286`,
  `evaluators.update(h._evaluators)`), and `evaluate_ir` dispatches an external node by
  `nd["descriptor"]["content_hash"]` (`graphed python/graphed/execute.py:116-124`). §6.2(i)'s
  cross-fill agreement rule forces one inferred label set — hence ONE spec, hence ONE chash — per
  axis-mode histogram, so the `1 + |S|` fill nodes would all resolve to a single evaluator:
  last registration wins and every shift sibling writes the same category value. §1.2's §6.2
  carve-out does not close it — it puts the BIN IDENTITIES in the spec, which is exactly the part
  identical across siblings. Binding: the per-fill variation payload (the scalar label for a shift
  sibling; the ordered weight-label tuple for the loop) is a **field of the fill's `FillEvaluator`
  AND enters the External payload's content hash** — `content_hash((spec, variation_payload))` in
  axis mode — so each axis-mode fill node resolves to its own evaluator. M29's identity discipline
  is preserved: the extra content exists only in axis mode, and a **SIBLING-mode fill — varied or
  not — hashes exactly as today (r24: the MODE decides, §6.1a/§6.1c r22; r15–r23's "an unvaried or
  sibling-mode fill" was false of an unvaried AXIS-MODE fill, which under (ii) still declares the
  1-bin `{"nominal"}` variation axis, so its spec and its `content_hash((spec, variation_payload))`
  both differ from today's — an implementer taking the old clause literally ships no variation axis
  there and reds m50's r23 fourth-output anchor)**. Cross-referenced from §6.1c, whose per-slot spec is the fill node's, not
  the histogram object's, for the same class of reason.
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
  **The MODE is a property of the HISTOGRAM, not of a single `fill()` call** (r17 — the opt-in
  spelling is pinned at m50 freeze and is plausibly a per-`fill` argument, and the only bound
  cross-fill rule concerned LABEL SETS, so a histogram whose first fill opts in and whose second
  does not was undecided; it is not benign: §6.1c keys an axis-mode output `(output, None)` and a
  sibling-mode output `(output, label)`, so a mixed histogram produces both key forms for ONE output
  and §6.1a/§6.2(i-bis) then give it two contradictory result shapes, while `_GroupZero` builds one
  `zero_of(spec)` per slot and `_add_groups` is a key-wise `+`
  (`graphed-histogram src/graphed_histogram/boost.py:120-122,127-130`) over specs that differ by the
  variation axis — cross-axis addition raises, §6.1c): **the first fill fixes the mode and a later
  fill into the same histogram in the OTHER mode is a hard error naming both**, the same shape as
  the label-set mismatch above. Frozen alongside the m50 declaration anchor.
  **(i-bis) Axis-mode RESULT SHAPE** — §6.1a binds only the sibling shapes, so this is stated
  here: an axis-mode varied output returns a **bare `bh.Histogram` carrying the `"variation"`
  axis**, which is *indistinguishable by type* from an unvaried output. `graphed.labels` and
  `graphed.universe` therefore recognise it explicitly: `graphed.labels(h)` = the variation
  axis's bin set (NOT `["nominal"]`), `graphed.universe(h, label)` = **that label's slice along
  the variation axis**. **The ORDER `graphed.labels(h)` returns is §2.2's, not the axis's** (r17 —
  §2.2 binds the verb to "nominal first, then insertion order" while §6.2(iii) binds the stored bin
  order LEXICOGRAPHIC, in which `"nominal"` is not first for any realistic family
  (`btag_down < btag_up < jes_down < nominal < pu_up`), so the two rules collided on this shape and
  §6.2's declaration anchor deliberately forbids using `graphed.labels(h)` as its oracle):
  `graphed.labels(h)` returns the axis's bin set RE-ORDERED to §2.2's rule — `"nominal"` first, then
  the remaining bins in axis (lexicographic) order — while the STORED bin order stays lexicographic
  and unchanged. The m50 (i-bis) anchor asserts that ordering. Without this the §6.1a narrowing helper answers `["nominal"]`
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
  `_restore_metadata` writes it back), so the handle survives the spec/`zero_of` rebuild —
  **measured on a TWO-axis histogram** (r13; the r12 evidence `h.axes.name == ('variation',)` holds
  only for a ONE-axis histogram, a configuration axis mode never produces, because the variation
  axis is added alongside the user's ≥1 value axes): `bh.Histogram(Regular(3,0,1), StrCategory([…]))`
  with the name set on axis 1 round-trips `spec_of` → `zero_of` as
  `[a.__dict__.get("name") for a in z.axes] == [None, "variation"]` (boost_histogram 1.8.0).
  **`h.axes.name` raises `AttributeError` unless EVERY axis carries a name** — `bh`'s
  `axes.__getattr__` maps the attribute over all axes (`boost_histogram/axis/__init__.py:925`;
  measured: `AttributeError: object Regular has no attribute name`) — so the position lookup MUST
  read `axis.__dict__`, never `h.axes.name`, and an m50 test-author must not write `h.axes.name` as
  the oracle; (2) `graphed.labels`/
  `graphed.universe` resolve the axis POSITION from that name and slice by index. Nothing binds a
  literal subscript expression.
  **(3) No `boost_histogram` import in `graphed` proper** (r14 — `graphed.labels`/`graphed.universe`
  are `graphed` module functions and must be uniform over the bare-histogram shape, but `graphed`'s
  runtime dependencies are `["executing>=2.0", "cloudpickle"]` (`pyproject.toml:27`) with
  boost-histogram only in the `dev` extra — the same dependency fact this plan uses twice for its
  m48/m49 fixture analysis, so binding the `bh.loc` spelling inside `graphed` would import a package
  it does not depend on): detection is **duck-typed** (an object exposing `.axes`) and the slice
  uses a plain INTEGER bin index obtained from the axis itself — `axis.__dict__["name"]` to find the
  position, then `axis.index(label)`. Measured equivalent to the `bh.loc` form (boost_histogram
  1.8.0: `h[{1: ax.index("jes_up")}]` and `h[{1: bh.loc("jes_up")}]` give equal `values()`), and the
  m50 anchor's oracle is a manually sliced reference, so nothing downstream depends on `bh.loc`.
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
  declared bin set equals the inferred label set exactly. `h.sum(flow=True) == h.sum()` witnesses
  only the UNDER-declaration half (a label with no bin lands in the overflow) — **an
  OVER-declaration is invisible to it** (measured, boost_histogram 1.8.0, r13: declaring
  `['nominal','jes_up','jes_down','stale']` and filling the three real labels gives
  `sum == sum(flow=True) == 3.0`), so the closing half is an equality against a literally spelled
  expected label list, never one read back from the histogram.
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
  `core/m40/test_join_serialize.py:84-99` pattern) plus a **params KEY-SET equality**, not a
  key-absence placeholder (r17 — the r0–r16 spelling `assert "<new key>" not in node["params"]` is
  literally a placeholder: the M29 precedent it cites works because M29 had a KNOWN new key
  (`assert "n_weights" not in node["params"]`,
  `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:96`), while m48 in sibling mode
  adds NO params key by design — §1.2 keeps labels out of params — so the test-author has no key to
  spell and any invented name passes tautologically): the unvaried single-weight fill node's
  `set(node["params"])` equals a LITERALLY spelled expected set, measured today as
  `{"spec", "n_axes", "weighted", "sampled"}` (`graphed-histogram
  src/graphed_histogram/boost.py:198-212`; `n_weights` is added only when `len(weights) > 1`).
  **Two halves are bound, r15, or the gate is under-determined**: **(1)** the golden blob is
  captured from the **PRE-m48 revision** of that fill graph (captured after implementation it is a
  no-op tautology); **(2)** §6.1d's broadcast seam is **SCOPED, and the trigger is stated ONCE, r16** (r15 stated it
  here as "only on the varied/ambient path" while §6.1d binds it for EVERY weight factor a fill
  applies, leaving the contexted-but-unvaried fill — a handle, no ambient registrations, no `Varied`
  input, an explicit per-event factor against a per-object value — inside one scoping and outside
  the other): **the seam is recorded for every weight factor of a fill that carries a context handle
  OR any `Varied` input; a fill with NEITHER records byte-identically to today** — which is exactly
  this section's golden case. Read unscoped, §6.1d's
  "EVERY weight factor the fill applies … is broadcast" adds a node to an ordinary
  `h.fill(x, weight=[w])`, which makes this committed golden either red against a correct
  implementation (frozen ⇒ Test Dispute) or a tautology.
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
  idiom having its own 1-D-capped implementation, `python/graphed/numpy/io.py:182-191` (signature; its 1-D cap is inside `_WritePart.__call__`, `:164-165`); §6.4f's
  "numpy backend EXEMPT" therefore means *the numpy-idiom function refuses*, not that a new
  neutral dispatcher is introduced), where
  `record` is PRE-selection (see the entry check below) and `select=` carries the `Varied`
  mask(s). **`select=` is per SELECTION LEVEL, not one row mask** — this is what makes §6.4d's
  object-level cutflow implementable at all: it accepts either a single `Varied` row mask, or an
  mapping of `Varied` masks — `{0: event_mask, ("Jet", 1): jet_mask, …}` — **one
  entry per (FIELD PATH, LEVEL) that varies, level 0 being keyed by the bare depth `0` (r23,
  correcting r21's "an ordered per-depth mapping … one entry per level that varies", which the r22
  field-scoping below makes false: the Jet+Muon record that r22's own rationale names REQUIRES TWO
  depth-1 entries, so validation built from the stale sentence refuses the program r22 exists to
  enable)**. **A level-0 entry is keyed by the bare depth `0` and applies to the
  record's ROW axis; every level-k ≥ 1 entry is FIELD-SCOPED and names the field path it applies
  to, r22 — EXCEPT where the level-k structure is the RECORD'S OWN, which takes the bare depth `k`,
  r24.** The exception is not an ergonomic nicety: §6.4's own canonical skim writes the varying
  COLLECTION itself (`to_parquet(events.Jet, select=…)`, `to_parquet(E1.Jet, …)`, and the
  silent-corruption control `to_parquet(sel.Jet)`), for which `"Jet"` is not a field of the written
  record — it IS the record — so under r22's unqualified field scoping the object-level mask of the
  plan's own headline program has NO legal spelling, and a test-author building m51's positive
  control must guess between a self-referencing `("Jet", 1)`, a missing-field refusal, and a third
  form, then freeze the guess read-only. **The discriminator is a record-time FORM property, so the
  grammar is decidable**: measured (awkward 2.x, `graphed-latest@ff7c607` venv) the single-collection
  record's form is `var * {pt: float64, eta: float64}` — one level-1 structure, the record's own,
  shared by every field, exactly r22's single-valuedness condition — while the multi-collection
  record's is `{Jet: var * {…}, Muon: var * {…}}`, whose two level-1 structures are distinguishable
  only by field path. Binding: the bare depth `k ≥ 1` key is legal iff the record is itself jagged
  at depth `k` (its own offsets, all fields inside them); a record carrying two or more
  independently jagged fields at that depth REFUSES the bare key at the `to_parquet` call, naming
  the ambiguity and the field paths — the r22 hazard, now diagnosed rather than mis-validated. Levels ≥ 1 were bound per-depth alone through r21, which is single-valued only for a
  record whose fields are all jagged with the SAME offsets (e.g. `events.Jet`) and is not
  single-valued for either shape this section puts in scope: a record mixing depths (§6.4b makes
  `graphed.weight(ctx)` a storable depth-0 field alongside a depth-1 collection, and m51's
  round-trip anchor lists both) or a record carrying two jagged collections (Jet + Muon, a JES shift
  moving only Jet), which has two distinct depth-1 offset arrays while a bare `{0: evt, 1: jet_mask}`
  is well-formed under the r21 grammar — so the writer would validate a jet mask against muon
  offsets or die with an offsets message about the wrong field, the diagnosis-quality failure
  §6.4b's own r18 clause exists to avoid. §6.4d's "widest common structure" governs where varied
  columns are STORED, not which field a level-k mask is validated and stored against, and does not
  close this. **What the writer does with them is exact** (r12 — the r11 "applies NONE of them"
  sentence read against this paragraph's own superset rule and §6.4b/§6.4d's "on the event-row
  superset", producing two defensible readings that yield different files): it applies the
  **level-0 OR** to the stored ROWS — that IS the superset — and applies **no other supplied mask**
  to the stored buffers (that is the point of §6.4d's widest-common-structure rule: inner cuts are
  never applied, or the deltas lose their common shape); and it stores **one packed per-label
  validity mask per supplied ENTRY — stored against that entry's FIELD (against the record's own
  axis at that depth for a bare depth-`k` entry, r24), level 0 against the row
  axis (r23, for the same reason: a per-LEVEL count is not single-valued once level-k ≥ 1 entries
  are field-scoped)**. Without a per-level channel
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
  **(2) ROW-SPACE AGREEMENT, SCOPED PER LEVEL** (r13 — the r12 wording applied one lineage test to
  "every supplied `select=` level", which no legal level ≥ 1 argument can satisfy: a level-1 mask is
  per-OBJECT, jagged over the record's INNER dimension, not a mask over the record's row space, and
  it is not `graphed.selection(...)` of anything, because §9.1 defines that verb as the mask that
  derived a CONTEXT and contexts are event-level, §2.6c `events[mask]`. Read literally it refused
  every `select={0: …, 1: …}` call — i.e. exactly the m51 object-migration anchor r11 exists to make
  satisfiable; the r12 runtime clause already narrowed itself to "each level-0 mask", so the
  sentence also disagreed with itself):
  **level 0, split in two halves with different sites** (r14).
  **(2a) LINEAGE, record-time** — the supplied mask must live in the record's own row space, which
  in r19's binding form is decided by **CONTEXT-HANDLE EQUALITY** (the operative rule; see "HOW IT
  IS DECIDED" below, which is what an implementer and a test-author work from). Its r16–r18
  formulation — the mask is the selection that derived some context from the context the record was
  read from, **across exactly ONE mask-derivation link and any number of `graphed.vary` IDENTITY
  links** — is retained here only for its rationale (r16 — the r15 wording required the mask's context `c` to
  have the record's own handle as its immediate PARENT across a mask-derivation link, which refuses
  this plan's own mainline skim shape: §2.6's sketch rebinds `sel = graphed.vary(sel, "btag", …,
  is_weight=True, …)` after `sel = events[mask]`, so a skim written after ANY weight `vary` is
  written from a `vary`-derived context; `vary` links do not move the row space, §6.1d link kind
  (2), so admitting them changes nothing the predicate is protecting, and m51's own bridge anchor
  (`select=graphed.selection(sel2)` for `sel2 = graphed.vary(sel, …)`) requires it. **r16's
  additional justification — "§6.4b's stored varied weight factors are reached via
  `graphed.weight(ctx)`, so a skim storing varied weights is written from a weight-`vary`-derived
  context BY CONSTRUCTION" — is SOFTENED in r18**: a SELECTION-scoped weight is not storable at all
  (§6.4b's r18 row-space precondition), so that particular ground does not carry; admitting `vary`
  links is still right, on the bridge-anchor ground above): `graphed.selection(c)`
  — which under §9.1 r16 already walks `vary` identity links — for a context `c` reachable from the
  record's own context handle (§2.3e) by exactly one MASK DERIVATION plus any number of `vary`
  links. Links of the universe/nominal projection kind are NOT admitted (r15 — the parent relation
  alone is not enough now that §2.2's universe/nominal children exist:
  `select=graphed.selection(graphed.nominal(ctx))` on a record read from `ctx` satisfies a bare
  parent test while the returned mask lives in the GRANDparent's row space, §9.1 r15; predicate (2b)
  catches it at execution, but the record-time check should decide it). (The r13 parenthetical said
  "`graphed.selection(ctx)` of the record's own context handle", which inverts the direction and
  refuses the canonical skim spelling bound 15 lines below: in
  `to_parquet(events.Jet, select=graphed.selection(sel))` with `sel = events[mask]`, the record's
  own context is the ROOT `events`, and §9.1 defines `graphed.selection` of a root context as
  `None`. The m51 anchor's wording — "a record whose context is not the one the supplied `select=`
  mask DERIVES FROM is refused" — was already the correct direction and is normative.)
  **HOW IT IS DECIDED is RE-EXPRESSED over the operand that exists, r19 — `graphed.context_of` of
  the supplied mask, not a search over the record's context's descendants.** The r16–r18 statement
  ("a context `c` reachable FROM the record's own context handle by exactly one MASK DERIVATION plus
  any number of `vary` links, whose `graphed.selection(c)` is the supplied mask") is a DOWNWARD,
  parent→children search, and no bound surface supports one: §2.6b binds lineage as "Each returned
  context links to its parent" — an upward chain only — §9.1's `graphed.selection` runs
  context→mask, and §2.5's weak-reference registration is scoped to `Varied` containers, not
  contexts. Nothing maps a mask back to the context it derived, so neither (2a) nor absent-operand
  case (ii) was decidable, while m51 freezes four controls on the predicate. Binding replacement:
  **the supplied mask's own §2.3e context handle MUST BE the record's context handle, OR be
  reachable from it across `graphed.vary` IDENTITY LINKS ONLY, in either direction —
  `graphed.context_of(select_mask) is graphed.context_of(record)`, else one upward walk over the
  lineage §2.6b already retains that crosses `vary` links and NOTHING else (r23; r19–r22 bound bare
  handle equality and claimed "the r16 admission of any number of `vary` IDENTITY links becomes
  AUTOMATIC", which is FALSE under §2.3e's own ORIGINATION rule — a read through
  `E2 = graphed.vary(E1, …)` carries `E2` while a read through `E1` carries `E1`, different handles
  and identical row spaces — so bare equality REFUSED exactly the configuration r16 admitted:
  `E2 = graphed.vary(E1, "pu", …, is_weight=True)`, `mask = gak.num(E2.Jet) >= 4`,
  `sel = E2[mask]`, `to_parquet(E1.Jet, select=graphed.selection(sel))`. That refusal protects
  nothing — a `vary` link does not move the row space, §6.1d link kind (2) — and is the
  hard-block-a-legal-skim-spelling defect r20 fixed for absent-operand case (ii), one clause up.
  The "becomes automatic" sentence is WITHDRAWN)** — a comparison of two
  values both operands already carry, plus at most a walk over identity links. It is the same property (2a) was
  reaching for: a mask whose reads were performed through the record's context lives in the
  record's row space by §2.6c, which is exactly what the level-0 OR requires. Verified against the
  m51 controls: canonical skim `to_parquet(events.Jet, select=graphed.selection(sel))` with
  `sel = events[mask]` — the mask is recorded from reads through `events`, so both handles are
  `events` → ACCEPT; silent-corruption case (`sel = events[nominal_mask]`, record `sel.Jet` handle
  `sel`, `select=varied_mask` handle `events`) → REFUSE; chained-context case
  (`graphed.selection(sel2)` for `sel2 = sel[mask2]` has handle `sel`, against a root-row-space
  record) → REFUSE; universe/nominal case (`graphed.selection(graphed.nominal(sel))` has handle
  `events`, record read from `sel`) → REFUSE. Both ABSENT-operand cases below are preserved
  unchanged by it: a record with no handle short-circuits to (i), and a hand-built loose mask
  carries no handle (§2.3e Drop rule) so it can neither equal a contexted record's handle nor be
  reached from it across `vary` links → (ii)'s
  refusal. All five m51 controls decide identically under the r23 `vary`-link admission (each
  refused pair is separated by a MASK-DERIVATION or PROJECTION link, never by `vary` alone), and
  the r17 per-label
  **node-id-equality** rule for "the supplied mask IS `graphed.selection(c)`" is WITHDRAWN with the
  search it served; m51's re-recorded-equal-expression positive control survives and is
  strengthened, since a re-recorded mask carries the same handle by construction (measured:
  `a = src * 2.0; b = src * 2.0` → `a.node_id == b.node_id == 1`, `a is b` False). A record read
  across a MASK-DERIVATION or PROJECTION link from the mask's context — an ancestor or a sibling in
  that sense — is refused at the `to_parquet` call, naming both contexts.
  **Both operands can be ABSENT, and each case is bound** (r15 — (2a) was stated purely in lineage
  terms while §2.3e's Drop rule yields context-free results and a hand-built `Varied`
  mask need never have derived a context, so the predicate had nothing to compare and no contexts to
  name for exactly the loose §2.1a write style this section calls supported — a test-author freezing
  the refusing reading would hard-block that sink permanently):
  **(i) the RECORD carries no context handle** — (2a) is SKIPPED, and predicate (2b)'s per-partition
  row-count equality alone decides (it is the half that catches the corrupting case, and the loose
  style must stay reachable);
  **(ii) the record has a handle but the supplied mask carries NO context handle** (a hand-built
  loose mask, §2.3e's Drop rule) — REFUSED at the
  `to_parquet` call, naming the record's context and stating that the mask has no lineage to check
  against (mixing a contexted record with an unrelated loose mask is the ambiguous case, not a
  supported style). **Re-expressed over the operand r19's rule actually reads, r20** (r15-r19 wrote
  "the supplied mask DERIVED NO CONTEXT", which is a different property from "carries no handle" and
  makes (ii) refuse a program r19's binding predicate ACCEPTS: a mask recorded entirely from reads
  performed THROUGH the record's own context — `select=(events.MET.pt > 50)` passed directly instead
  of via `graphed.selection(sel)` — carries handle `events` by §2.3e's ORIGINATION rule and derived
  no context, so handle equality holds and it is a legal in-row-space level-0 mask, while (ii) as
  written refused it and m51's anchor froze that refusal read-only): **a contexted mask carrying the
  RECORD'S OWN handle is ACCEPTED whether or not any context was ever derived from it.** That case
  is m51's fifth positive control — it is the only fixture that distinguishes the two readings.
  m51's entry-check anchor carries a loose-style write as an explicit POSITIVE control for (i).
  **(2b) ROW-COUNT EQUALITY between the record and that mask — EXECUTION-time, per partition**,
  raised by `_WritePart` before any buffer is stored, exactly like predicate (1) (r14 — r13 bound it
  inside the record-time clause, contradicting this section's own "offsets are data" argument three
  paragraphs below, and left it with no raiser and no site).
  **(2c) LEVEL-0 DEPTH, record-time, r21** — a mask supplied at level 0 MUST be FLAT over the
  record's row axis (depth 0); a JAGGED level-0 mask is refused at the `to_parquet` call, naming the
  level and the per-level channel. Neither (2a) nor (2b) constrains depth, and a per-OBJECT mask read
  through the record's own context (`select=(events.Jet.pt > 25)` instead of an event-level mask)
  passes BOTH: (2a) by §2.3e ORIGINATION — the same property that makes r20's fifth positive control
  `select=(events.MET.pt > 50)` legal — and (2b) because a jagged boolean over the record's own
  structure has the record's OUTER length. The writer would then apply it as the level-0 OR, and
  jagged-boolean indexing filters INNER elements while keeping every row, silently violating this
  section's superset-row contract and §6.4d's "inner cuts are never applied" rule with no error
  anywhere. m51 carries it as a negative control alongside (2a)'s.
  **(2c) GENERALIZES TO EVERY SUPPLIED LEVEL, r22**: a mask supplied at level k MUST have depth k
  over the record's structure — over the NAMED FIELD for a level-k ≥ 1 entry — and a depth mismatch
  at ANY supplied level is refused at the `to_parquet` call, naming the level. r21 closed the
  level-0 half on the argument that depth is a FORM property known at record time (measured,
  `python/graphed/array.py:283-290`, `_form_meta` reads `self._session.form(self)`, so depth is
  decidable at the call); the mirror case is identical — a FLAT mask supplied at level 1
  (`select={0: evt, ("Jet", 1): evt}`, an easy mis-spelling) has no depth-1 offsets, so the
  structural check below has no operand and the likely implementation dies inside `_WritePart` per
  partition with an `AttributeError`/`IndexError` rather than a graphed error naming the level, at
  execution, on a record-time form property. m51's (2c) negative control carries the too-shallow
  level-1 mask alongside the jagged level-0 one.
  **Levels ≥ 1** — lineage is not the available handle, so the check is STRUCTURAL:
  each per-label member of the mask must carry **that NAMED FIELD's own offsets at that depth
  (r22** — "the record's own offsets at that depth" is not single-valued for a
  mixed-depth or multi-collection record; the entry names the field precisely so this check and the
  packed per-label mask both have one operand**)**, and the packed per-label mask is stored against
  that field. That is
  predicate (1)'s comparison at the same level, so it costs nothing extra, runs per partition, and
  shares (1)'s raiser and error shape.
  Each predicate has its own error message, and the m51 anchors name which predicate decides which
  positive control. **Where each runs is bound below** (predicate (2)'s level-0 LINEAGE half (2a)
  **and its level-0 DEPTH half (2c), r21,** are
  record-time; predicate (1), predicate (2a)'s row-count twin (2b) and predicate (2)'s level-≥1
  structural half are execution-time, per partition).
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
  `python/graphed/write.py:32-43`). Binding: predicate (2a)'s **level-0 lineage** half **and (2c)'s
  level-0 DEPTH half (r21 — depth is a FORM property, known at record time)** ARE
  record-time checks raised from the `to_parquet` call; predicate (1) (offsets), **predicate
  (2b)'s level-0 row-count equality** **and predicate
  (2)'s level-≥1 structural half** are **execution-time, per-partition checks raised by `_WritePart`
  BEFORE any buffer is stored**, surfacing through the
  executor's error path — the same treatment §6.1d already takes for its length check. m51's
  anchors are worded accordingly; do NOT freeze a record-time raise for any offsets- or
  row-count-shaped predicate (r14: that now includes (2b)).
  (b) **Column rule — augmentation.** The written record carries the user's fields evaluated in
  the **nominal** universe (on superset rows), PLUS appended per-label reconstruction data: for
  every stored field that **IS `Varied` — structurally, at record time** (r17 — "whose VALUE differs
  per label" reads data-dependently, and §6.4c computes the deltas inside `_WritePart` on the
  evaluated buffers, i.e. PER PARTITION (`python/graphed/awkward/io.py:111-127`), so the literal
  reading makes the augmented column set data-dependent: a partition where a label happens to agree
  with nominal everywhere would write fewer columns than its neighbour, giving parts with different
  schemas and different manifests inside ONE dataset, and m51 freezes the file layout. m51's own
  round-trip anchor settles the intent the other way — "a label structurally equal to nominal
  (all-zero delta)" IS written), a same-shaped delta column — **so the augmented column set is
  identical across partitions by construction**; and per-label
  selection masks (the varied cutflow) plus the nominal mask, so each universe's row set is
  recoverable. Weight-only labels contribute no kinematic deltas — their varied factors, when
  among the stored fields, augment like any other varied field (**reachable via
  `graphed.weight(ctx)`**, §9.1 — added in r12: under the owner-locked context idiom a factor
  handed to `graphed.vary(..., is_weight=True)` is otherwise absorbed into an immutable registry
  the user cannot name, so "when among the stored fields" was unsatisfiable).
  **The ROW-SPACE precondition on that is bound here, r18, because "when among the stored fields" is
  not free**: the written record is PRE-selection and its buffers are stored on the event-row
  SUPERSET (this section and §6.4a), while §2.6c gives a SELECTION-derived context per-label row sets
  and re-indexes its ambient registry by each label's own mask — so `graphed.weight(sel)` for
  `sel = events[mask]` has a nominal length of |sel_nominal| and per-label lengths that differ, and
  storing it would trip predicate (1) / §6.4d ("a stored varied field whose per-label offsets differ
  from nominal's is REFUSED") BY CONSTRUCTION, with a message about offsets rather than about the
  real fault. No re-indexing rule back onto the superset is bound, and none is expressible — a mask
  has no inverse. Binding: **a stored varied field MUST live in the record's own row space;
  `graphed.weight(ctx)` is storable exactly when `ctx` is reached from the record's context across
  `vary` IDENTITY links only (§6.1d link kind (2)) — no mask-derivation link — and a
  SELECTION-scoped weight is NOT storable in v1, refused at m51's entry check with a message naming
  the row-space mismatch, not an offsets mismatch.** (The selection-scoped weight remains fully
  supported for FILLS, §2.6c; only the skim sink refuses it.) m51's entry-check anchor carries the
  refusal and its round-trip anchor names the storable spelling. Appended names follow one bound
  convention (`__vary_{label}__{field}`-shaped; exact spelling pinned at m51 freeze). Labels are
  valid identifiers by construction (**§1.1 canonicalization, r9 e-form** — a dotted spelling never
  reaches a label), so labels appear in on-disk names VERBATIM: the canonical on-disk shape is
  `__vary_murf_5em1__Jet_pt`. **The `{field}` half of that name is bound separately, because §1.1's
  discipline covers only the LABEL half** (r15 — the example silently assumes a `.`→`_` transform of
  the field path that nothing bound, while the measured hazards below are properties of the WHOLE
  column name and a nested path (`Jet.pt`, `FatJet.subjet.pt`) puts a `.` straight back into it;
  §1.1 is explicit that its 32-character cap does not bound `__vary_{label}__{field}`): the field
  path is flattened with `_` per level, **and the resulting on-disk names are checked for COLLISION
  in BOTH directions — derived-vs-derived and derived-vs-stored: the derived names of all augmented
  columns MUST be pairwise distinct AND MUST NOT equal any stored field name; a collision is REFUSED
  at m51's entry check, naming both source fields** (r16 — r15's wording checked only
  derived-vs-stored and illustrated it with a case that is NOT a collision: under the bound
  `__vary_{label}__` prefix the derived name for `Jet.pt` is `__vary_L__Jet_pt`, which cannot equal a
  stored user field `Jet_pt`, so the check as stated was nearly a no-op while the REAL collision
  class — both `Jet.pt` and a flat `Jet_pt` varying, each deriving to `__vary_L__Jet_pt` — went
  unstated; a test-author freezing r15's sentence would most plausibly build the fixture from its
  example and freeze a refusal for a program that is LEGAL under this convention, hard-blocking a
  legitimate nested-field skim in read-only tests). §6.4e's manifest
  remains the sole machine resolver either way: readers resolve labels and columns THROUGH it, never
  by parsing stored names, so the flattening is for human inspection and the collision refusal
  exists so the two never disagree. m51 freezes a nested-field skim round-trip and the collision
  refusal. The probe-measured hazards that forbade
  dotted names (`ak.from_parquet(columns=["murf_0.5"])` silently empty, pyarrow 25.0.0 /
  awkward 2.12.0; a dotted uproot 5.7.5 RNTuple field is reachable via `__getitem__`
  (`behaviors/RNTuple.py:1560-1562`, exact lookup first) but `RField.array()` fails because
  `to_akform` splits the path on `.` (`behaviors/RNTuple.py:562,567`);
  the TTree writer's own `.` nesting separator, `writing/_cascadetree.py:1606`; ROOT
  TTreeFormula `.`/`-` operator meaning) are foreclosed at the §1.1 gate. Carried-over probe
  evidence: the r8 p-form fixture `__vary_murf_0p5__Jet_pt` — identifier-shaped exactly like the
  r9 canonical form — round-tripped byte-exact and readable in every measured path.
  (c) **Bit-exact reconstruction is REQUIRED — at every selection level SUPPLIED through `select=`
  (r24).** Reading the file back and applying the deltas MUST reproduce every universe's
  post-selection values and row set bit-for-bit vs the in-memory varied run, at those levels. **The
  scoping is not a weakening, it is what the writer can promise**: §6.4a is explicit that the API
  takes the masks and does not infer them, storing one packed per-label validity mask per SUPPLIED
  entry, so a user who applies an object-level cut in memory but supplies only `{0: event_mask}`
  produces a file no reader can reconstruct at level 1 — through no fault of the implementation.
  Unqualified, the sink's headline contract was unsatisfiable for a legal program while correct code
  met its intent. User-visible consequence: **a level not supplied is not recoverable, and §6.4e's
  manifest records which levels are stored** (m51's round-trip anchor supplies both levels, so
  nothing in the frozen suite changes). The default representation is therefore **exact by construction**: same-dtype XOR
  bit-delta vs nominal for value columns (zero wherever a label equals nominal — maximally
  compressible), `packbits` for masks stored as nominal + XOR-vs-nominal diffs.
  **The COMPUTATION SITE is bound, because the in-graph reading is measurably not expressible**
  (r14): the extra marked outputs of §6.4f's shared `compile_ir` are the **per-label VALUES and
  per-label masks**, and the XOR bit-delta and `packbits` are computed inside
  `_WritePart.__call__` on the EVALUATED buffers (`ndarray.view(uintN)`), after `evaluate_ir` and
  before the write. A recorded XOR over the float columns that matter does not exist: measured
  (awkward 2.12.0 / numpy), `float32 ^ float32` raises `TypeError: ufunc 'bitwise_xor' not supported
  for the input types` for both `np.ndarray` and `ak.Array`, gak has no bit-view verb
  (`grep -c "^def " python/graphed/awkward/functions.py` → 73, with no `view`/`packbits`/
  `frombuffer`; `values_astype` is a VALUE cast), while `a.view(np.uint32) ^ b.view(np.uint32)`
  works on evaluated buffers. §6.4f's "appended columns are extra marked outputs" therefore refers to
  the per-label values/masks, and its read-list widening must cover them. An in-IR bit-view verb is
  NOT scoped (§11). Measured basis
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
  (`{0: event_mask, ("Jet", 1): jet_mask}`) and never applies them to the stored buffers; **a
  level-k ≥ 1 entry is FIELD-SCOPED (§6.4a r22) unless the level-k structure is the record's own,
  which takes the bare depth `k` (§6.4a r24 — the single-collection skim `to_parquet(events.Jet,
  …)`, where the field-scoped rule below has no operand), so a field shallower than a supplied
  level, or at that depth under a different field path, is unaffected by it — a depth-0 stored factor
  (`graphed.weight(c)`, §6.4b) coexists in one record with a depth-1 `("Jet", 1)` entry, r22**;
  nothing else in
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
  (e) **Manifest — invent no formats.** A manifest (labels → appended columns → representation,
  **plus the selection LEVELS whose per-label masks are stored, r24** — §6.4c scopes bit-exact
  reconstruction to the levels the user supplied through `select=`, so a reader must be able to tell
  which those were rather than discovering the gap as wrong physics)
  travels in existing metadata channels: parquet key-value file metadata (measured unused today —
  greenfield). **The writer swap is CONDITIONAL, not unconditional** — otherwise it contradicts
  §6.4g's byte-identity requirement: re-measured (awkward 2.12.0 / **pyarrow 25.0.1**, version
  corrected r14 — a clean resolve of `awkward>=2.12` + `pyarrow` gives 25.0.1, which is also what
  §6.4g's `created_by` row records, and the r13 attribution of these same-revision probes to two
  different pyarrow versions was a reproducibility snag; re-verified r14 in that clean environment
  for the list-of-float case: different bytes, `{ARROW:schema, awkward_array_metadata}` vs
  `{ARROW:schema}`, no `metadata` parameter. The r7-era dotted-name probes at §1.1/§6.4b were taken
  under pyarrow 25.0.0 and are left attributed as measured — the r12
  row recorded two sha256 digests without naming the array written, so they are not reproducible,
  and recorded KV SETS that are incomplete and array-dependent),
  `ak.to_parquet(a, p)` and `pq.write_table(ak.to_arrow_table(a), p)` produce **different bytes**
  for every array probed, and the arrow path **drops awkward's own `awkward_array_metadata` KV
  entry** — which would break `ak.from_parquet` round-tripping. Both paths always keep
  `ARROW:schema`; `ak:parameters` appears only when the array carries awkward parameters (present
  for a record array, absent for a plain list-of-float or flat numeric array), so it is a property
  of the DATA, not of the writer, and a test freezing a literal KV set would be red for the wrong
  reason. `ak.to_parquet` has
  no metadata parameter (signature verified), so the swap genuinely is required for the manifest.
  Binding: an **unvaried write keeps `ak.to_parquet` untouched** (preserving the §6.4g golden); a
  **varied write** MUST reproduce
  awkward's own KV entries alongside the graphed manifest, with `ak.from_parquet` round-tripping
  the augmented file as a frozen m51 anchor.
  **The ROUTE is bound too, r21, because the outcome is otherwise reachable only through another
  distribution's PRIVATE module**: measured in `graphed-latest`'s own environment (awkward 2.12.0),
  the dropped key is defined ONCE, as
  `AWKWARD_INFO_KEY = b"awkward_array_metadata"` in `awkward/_connect/pyarrow/table_conv.py:16`, and
  written only by `convert_awkward_arrow_table_to_native` there (`:19-40`); `ak.to_parquet` reaches
  it solely by importing that private helper
  (`awkward/operations/ak_to_parquet.py:14`, called at `:417`), while `ak.to_arrow_table` never adds
  it. Binding: **the varied write MUST NOT import `awkward._connect.*`** (the §2.3e/§6.1d
  package-boundary rule, here against a package where `graphed` cannot add a seam), and its route is
  the PUBLIC composition — build the file awkward's own writer would (`ak.to_parquet` to the part
  path or an in-memory sink), then re-read the table and re-write it with the graphed manifest merged
  into the schema metadata (`Table.replace_schema_metadata` + `pq.write_table`), which is the same
  merge point `ak.to_parquet` itself uses for `attrs` (`ak_to_parquet.py:424-431`). The second write
  is the accepted cost of the varied path; the unvaried path is untouched (§6.4g). A future revision
  MAY bind a cheaper route, but never one that imports awkward's private package. **The
  no-private-import half is knowingly left UNANCHORED, r22, and rides code review plus the repo's
  integrity scan**: m51's manifest anchor asserts only the OUTCOME — that the augmented file
  round-trips through `ak.from_parquet`, i.e. that `awkward_array_metadata` survives — which an
  implementer who simply imports the private helper also satisfies, so no frozen test discriminates
  the rule. It stays binding for the package-boundary reason above, on the same footing as §7.2's
  "MUST NOT compile a second time" and §1.1's `"1e1000000000"`; an m51 implementation MAY discharge
  it with a one-line static assertion (the varied-write module's source contains no
  `awkward._connect` import) in `tests/extra`. The
  ROOT-side equivalent pinned at m51 freeze. The manifest maps each label to its stored
  column/branch names and per-column representation, **serialized with SORTED keys** (r13 — a
  manifest serialized in set/dict-iteration order would make the written bytes depend on
  `PYTHONHASHSEED`, the same hazard §8.2(i) names for the plan closure); readers resolve labels
  **through the manifest**, never by parsing stored names (names embed labels for human inspection, not as
  the machine channel). A frontend reader (**`graphed.awkward.read_varied(path)`-shaped**; spelling
  at freeze) reconstructs `{label: array}` per universe from the manifest — the round-trip is the m51
  frozen anchor. **The reader is awkward-idiom, symmetric with the writer** (r14 — r13 spelled it in
  the NEUTRAL namespace while §6.4a binds the writer awkward-idiom on the factorization rule;
  measured, `graphed`'s runtime dependencies are `["executing>=2.0", "cloudpickle"]`
  (`pyproject.toml:27`) with awkward and pyarrow only in extras (`:29-46`), and both parquet entry
  points already live in `graphed.awkward` (`python/graphed/awkward/__init__.py:14,30`), so a
  neutral `graphed.read_varied` returning awkward arrays would put pyarrow + awkward behind the
  neutral namespace). The ROOT-side equivalent lives in the uproot fork.
  (f) **Seam binding (write-seam evidence, verified).** Parquet: appended columns are extra
  marked outputs of the SAME `compile_ir` (variadic by design, `execute.py:54-70`), so the M4
  optimizer shares the pass with the primary expression — appended between the evaluate and
  write steps of `_WritePart.__call__` (`awkward/io.py:111-127`). **The marked outputs are the
  per-label VALUES and masks, not the encoded deltas** (§6.4c r14 — the XOR/`packbits` encoding is
  not expressible as a recorded op and runs in `_WritePart` on the evaluated buffers), and the
  read-list widening below must cover them. **That call site unpacks a
  SINGLE output today** (`(out,) = evaluate_ir(...)`, `io.py:121`), so widening it to the
  augmented output list is part of this target, not incidental (r12).
  **The widened unpack resolves each augmented output BY NODE ID per §7.2, never positionally**
  (r18 — §7.2 states the general rule and even names m51, but this paragraph is what an m51
  implementer works from and never referenced it): `mark_output` de-dups (`src/store.rs:147-156`) and
  `evaluate_ir` returns one value per DISTINCT output (`execute.py:126`), so on m51's own anchored
  case — "a label structurally equal to nominal (all-zero delta)" — a positional unpack silently
  misassigns every label after the collapsed one, and an all-zero delta is exactly the content one
  expects there. A shared value is REPLICATED into every label that maps to it, and the
  **`record node id → output position` table is a FIELD of `_WritePart`** — driver-derived and
  shipped in the closure, since `_WritePart` is a frozen dataclass evaluated per partition in the
  worker (`python/graphed/awkward/io.py:100-127`) and cannot recompute it there. Whether §7.2's
  optimizer-merge REFUSAL also guards the write path is settled here: **it does** — the varied
  write is a varied unpack path in §7.2's sense and a μR/μF label spelled `w * 1.0` is §1.1-legal,
  so at m51 the same distinct-outputs-vs-distinct-marked-ids shortfall check runs in the varied
  `to_parquet` path (record-time, at the call) with §7.2's message and workaround; the read list widens at
  `_evaluation_columns` (`awkward/io.py:157-185`) or projection starves the task. ROOT:
  `graphed_write` today copies branches verbatim with NO IR evaluation
  (`_graphed_write.py:59-64`; zero `compile_ir`/`evaluate_ir` hits) — adding evaluation is the
  **larger half** of m51 and is scoped there explicitly. numpy backend: EXEMPT — it hard-caps
  output at one 1-D column (`numpy/io.py:163-171`); the numpy-idiom write function refuses a varied
  write with a clear error naming the awkward backend, **and the numpy idiom exposes no
  `read_varied` counterpart** (r14, symmetry with §6.4e's awkward-idiom reader).
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
  (`R` opaque through `Plan`/tree-reduce/engines — cba §exec-checkpoint §1,§4). **No per-variation
  RE-EXECUTION of the graph or the plan may be introduced anywhere** (r16 — the r0–r15 wording "no
  per-variation execution loop may be introduced anywhere" is absolute and collides with §6.2's own
  m50 mechanism, an evaluator-side weight loop inside ONE fill node; §6.2's loop is not a
  re-execution and is explicitly not such a loop). §5.2b's single-read witness is the mechanism
  witness for this requirement.
- **§7.2** The frontend owns `(output, label) → **node id**` — NOT `→ position` — and derives
  `node id → position` as **the index of that record id's FIRST OCCURRENCE in the frontend's OWN
  ordered list of marked record ids** (the list it passes to `compile_ir`), so **many labels MAY
  resolve to one position and the unpacker replicates that value**.
  **The operand is bound to that list, r21, because "derived from the compiled output list"
  (r18–r20) names one that cannot be joined to it**: measured against `graphed-latest@ff7c607`, the
  compiled artifact's `outputs()` are POST-REDUCTION ids, and the record→reduced map does not exist
  until m49's §8.2(i) accessor. Probe: record ids `src 0, dead 1, b 2, e 3, c 2` (`c` interning with
  `b`) → `compile_ir(s, b, e, c)` gives `GraphStore.deserialize(ir).outputs() == [1, 2]` — neither
  value a record id — while `evaluate_ir` returns TWO values, `b`'s then `e`'s, i.e. exactly
  first-occurrence order over the DISTINCT record ids. The frontend's own ordered list is therefore
  the exact operand for every program m48 admits: the two orders can only disagree when the
  OPTIMIZER merges distinct record ids, which is precisely what the m48 shortfall guard below
  refuses. This is forced by content dedup, measured:
  `GraphStore::mark_output` de-duplicates (`src/store.rs:147-156`) — **on the REDUCED store, which
  `from_reduced` marks (`src/store.rs:185-200`, the `mark_output(map[o])` at `:197`); `compile_ir` never marks the RECORD store at all
  (measured: `s._store.outputs() == []` after the probe above — it passes the ids as
  `reduce(outputs=ids)`/`serialize(outputs=ids)`, `python/graphed/execute.py:70-80`), r21** — and `evaluate_ir` returns
  `[vals[o] for o in store.outputs()]` (`execute.py:126`), so compiling two structurally identical
  outputs returns ONE value — re-measured this session against `graphed-latest`: `compile_ir(s, b,
  c)` with `b`/`c` structurally identical returns 1 value, `compile_ir(s, b, d)` with distinct
  expressions returns 2. A positional `(output, label) → position` map would therefore walk off the
  end of `_GroupReduce`'s `fills` list or mis-assign labels (`boost.py:102-117`) on exactly the case
  §1.2 mandates and §5.2a/m51 put in scope (a label structurally equal to nominal). The frontend
  unpacks into the §6.1 named mapping through §6.1a's bound unpack verb (r18).
  **THE SEAM THAT MAKES THE COMPILED ARTIFACT REACHABLE IS BOUND HERE, AND IT IS AN m48
  IMPLEMENTATION TARGET (r19)**, because TWO binding requirements need that artifact at a site that
  does not have it — **r21 removes the third**: §6.1c's index-based `layout` needs only the
  frontend's OWN ordered marked-id list above, which `plan()` already holds as `fill_nodes`
  (`graphed-histogram src/graphed_histogram/boost.py:281`, one line before it builds `layout` at
  `:282`), so it never needed the compiled artifact and its "derived from the compiled output list"
  rationale is withdrawn. The two that remain: this section's own m48 optimizer-merge refusal must
  compare the number of DISTINCT compiled outputs against the number of distinct marked record ids
  inside the group-plan builder; and m49's §8.2(i)
  `variation_labels` is a FIELD of `_PartitionReduce` keyed on POST-REDUCTION ids from the same
  compile. Measured against `graphed-latest@ff7c607`: `aggregate_plan(*outputs, reduce, combine,
  empty, externals, backend, steps_per_file, partitions)` compiles internally
  (`compiled = compile_ir(session, *outputs)`, `python/graphed/aggregate.py:95`) and immediately
  constructs the frozen dataclass `_PartitionReduce(ir=…, …, reduce=reduce)` (`:44-55,96-104`) from
  pre-built closures, and `graphed_histogram.plan()` builds `layout` at
  `src/graphed_histogram/boost.py:282` — BEFORE its `aggregate_plan` call at `:286`. Binding:
  **`aggregate_plan` gains ONE pinned seam (exact spelling pinned at m48 freeze) that (α) lets the
  caller see the COMPILED ARTIFACT — the `CompiledGraph` itself, not merely a list of output ids —
  before the worker closure is CONSTRUCTED, and (β)
  carries per-plan variation metadata onto that closure as an additive field
  (m49's `variation_labels`, §8.2(i)).**
  **(β) IS THE HOOK'S RETURN CHANNEL, NOT A CALL-TIME PARAMETER, r21**, and the direction is binding
  because as an input parameter (β) is unsatisfiable: §8.2(i) keys `variation_labels` on
  POST-REDUCTION ids obtained through the m49 accessor "for the reduction that produced a given
  compiled artifact", and that artifact is produced INSIDE the call — measured,
  `compiled = compile_ir(session, *outputs)` at `python/graphed/aggregate.py:95`, one line before
  `_PartitionReduce` is constructed from the parameters at `:96-104` — while this section forbids
  compiling twice (below) and §8.2(i) declares the field an IMMUTABLE sorted tuple, so no caller-side
  value and no mutable holder filled by a see-only callback can carry it. Binding: **the hook is
  called with the `CompiledGraph` before the worker closure is constructed, and its RETURN VALUE (the
  per-plan variation metadata, or `None`) is attached to the shipped closure as the additive §8.2(i)
  field.** m48's (α) anchor asserts that a returned payload reaches the closure (with a dummy value),
  so an m48 implementer cannot freeze a see-only spelling m49 is then blocked by — the same trap this
  paragraph closes on the artifact axis.
  **The field's TYPE is bound ONCE, in §8.2(i), as `tuple[…, …] | None` defaulting to `None`, and
  the m48 dummy is a well-typed NON-DEFAULT value of it — the empty tuple `()` (r22).** r21 left the
  hook's return declared "the per-plan variation metadata, or `None`" against a §8.2(i) field
  declared NON-optional, while m48 freezes a "dummy" read-back whose value must type-check against
  the field's DECLARED type — src, and checked today — under R0.4a's `mypy --strict` over src AND
  tests (`graphed-root-prompt.md:147-153`; **the r22 parenthetical cited `graphed
  pyproject.toml:83` → `strict = true` for the "AND tests" half, which that file's very next line
  contradicts — `files = ["python"]` at `:84`, and `graphed-histogram pyproject.toml:70-73` is
  `files = ["src"]` — so the binding source is R0.4a, which names src-only repos as a pending
  cross-cutting cleanup, not the measured config, r23**) — so the m48 test-author
  supplying the hook had to invent both the type and a value of it: a str/sentinel dummy is a type
  error at the hook's return and `None` is a type error against the non-optional declaration, and
  m49's bindingly declared type would then red the frozen test. `()` is the smallest well-typed
  value, is distinguishable from the `None` default, and keeps the (α) anchor discriminating without
  inventing a type. **The field therefore EXISTS from m48**, which is where its one-time journal
  churn lands — see §7.3.
  **The seam is ADDITIVE and the artifact is the `CompiledGraph`, both bound in r20.**
  *Additive*: the contracts of the existing `reduce`/`combine`/`empty` parameters are UNCHANGED —
  they are plain callables and frozen m5 passes them that way
  (`tests/frozen/frontend/m5/test_aggregate_plan.py:77,88,102`, e.g.
  `aggregate_plan(out1, out2, reduce=_sum_each, combine=_add_pairs, empty=lambda: [0, 0],
  steps_per_file=4)`), and a "factory over the compiled output ids" cannot be duck-typed apart from
  a plain reducer (`_sum_each` also takes one positional argument), so r19's factory illustration was
  implementable only by breaking a frozen test (§B.6) or filing a Test Dispute. The seam is a NEW
  optional keyword/hook — `on_compiled(compiled)`-shaped — beside the existing parameters, the same
  additivity discipline §8.1, §8.2(i) and §9.2 already take on shipped surfaces.
  *`CompiledGraph`, not ids*: this section's own merge refusal needs only the COUNT of distinct
  compiled outputs, which `GraphStore.deserialize(compiled.ir).outputs()` gives (r24 — the r20
  phrasing "which `outputs()` would give" reads as a `CompiledGraph` method and there is none:
  measured, its fields are `ir`/`source_names` and its only method is `evaluate`,
  `python/graphed/execute.py:36-52`), but the seam's OTHER named consumer does not
  — m49's `variation_labels` keys on `(reduced_node_id, member_index)` obtained from the m49 core
  accessor, which answers "for the reduction that produced a given compiled artifact" (§8.2(i)), and
  a bare id list cannot produce that. An m48 implementer choosing the narrower spelling would ship a
  seam m49 cannot use, and m49 could then only re-open an m48-frozen surface or compile twice, which
  the next sentence forbids. `plan()` MUST NOT compile a second time: the §3.3
  anti-quadratic budget is written for ONE reduction of the variation-expanded graph, and a
  frontend-side `compile_ir` before `aggregate_plan`'s own would double it. **That rule is knowingly
  left UNANCHORED and rides an R0.11 implementer-report measurement instead (the measured compile
  count for one `gh.plan({…})` call), r21** — its violation is silent (correct results, doubled
  reduction cost), m48's (α) anchor observes only the hook's own firing INSIDE `aggregate_plan` and
  says nothing about a compile that preceded it, and §3.3's frozen budget is a gate on a different
  fixture; the same treatment §1.1 gives its `"1e1000000000"` rule. The seam is a function
  signature, not a schema, so m48's §7.2 schema-absence anchor (worded over `ExecResult`/`Plan`/
  monitor) is untouched by it.
  **Each half is anchored in the repo whose source it is, r20** (the seam is new source in
  `graphed`'s `python/graphed/aggregate.py` while every requirement consuming it is fill-shaped and
  §10 places those anchors in `graphed-histogram` — whose frozen suite does not count toward
  `graphed`'s ≥90% diff-coverage-from-the-frozen-suite gate, the DoD argument r14 used to move §3.4
  out of m48 and r18 to drop `to_parquet` from m48's table; measured, no m48 anchor in `graphed`'s
  half calls `aggregate_plan` at all, and r19's own re-wording of the §7.2 schema anchor to
  `dataclasses.fields(...)` removed the last plan-shaped one): **(α) carries a `graphed`-side m48
  anchor over an UNVARIED `aggregate_plan` build** (§10/m48), and **(β)'s return CHANNEL is anchored
  at m48 WITH (α) — m48's (α) anchor freezes that a returned value reaches the shipped closure —
  while (β)'s per-plan PAYLOAD is anchored at m49 alongside §8.2(i)** (r23; the r20 "(β) carries its
  anchor at m49" predates r21's return-channel binding and r22's milestone correction), whose
  `variation_labels` is its only consumer — until m49 the field is a
  pass-through with a default, not unreachable source. **The §8.2(i) FIELD DECLARATION is therefore
  an m48 target and m49's `§8` target line excepts it, r23** — both target lines say so (§10). **The same node-id
  rule governs §6.4f's widened write-path unpack** — it is stated there too, r18, because that is
  the paragraph an m51 implementer works from.
  **A SECOND collapse mechanism exists that record-time identity CANNOT see, and m48 refuses rather
  than mis-slices (r17)**: the derivation above is sound only for collapses the frontend can
  observe — two labels whose members intern to ONE record node id. Measured against
  `graphed-latest@ff7c607`, the M4 reducer also merges **distinct** record ids: `EggEngine`'s sound
  rule set is commutativity over `SYMMETRIC_OPS` plus the identity tokens `x + 0.0` / `x * 1.0`
  (`src/optimizer/engine.rs:22-31,67-80`), extracted by quotienting the IR by the e-graph
  (`:89-110`). Two probes, this session: (1) with `nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5`
  (record ids 0/1/2/3), `compile_ir(s, nom, m1, m2, mh)` gives
  `GraphStore.deserialize(ir).outputs() == [0, 1, 2]` and `evaluate_ir` returns THREE values;
  (2) on the FILL path directly, two `Histogram.fill`s differing only in `weight=[w]` versus
  `weight=[w * 1.0]` record fill nodes `2` and `4` and compile to `outputs() == [2]` — one value for
  two fill nodes, exactly the `_GroupReduce` mis-slice §6.1c's index-based layout exists to prevent,
  arriving from a source no record-id key can distinguish. It is not a contrived case: §1.1 makes
  stringified-float families first class and names μR/μF factors, and the obvious spelling
  `variations={s: w * float(s)}` contains a literal `w * 1.0` member. The sound key is the
  record→reduced map §8.2(i) establishes does **not** exist (an m49 Implementation Target), so
  **binding for m48**: **on the VARIED UNPACK PATH — the owner of the `(output, label) → node id`
  map, i.e. `graphed-histogram`'s group-plan builder (`plan()`,
  `src/graphed_histogram/boost.py:256-295`), NOT `compile_ir` and NOT `aggregate_plan` — and over a
  VARIED program only** (SITE and SCOPE bound in r18: r17 said "after `compile_ir` the frontend",
  which reads most naturally as `compile_ir` itself — that is where marking happens — while the
  error must name LABELS, which exist only in the group-plan builder; and the predicate carried no
  varied-program qualifier, so an UNVARIED two-histogram program whose fills the M4 identity rules
  merge (`w` vs `w * 1.0` — this section's own measured case) would start raising where it
  previously ran, against §6.3's binding "Data / no-variation paths are unchanged" and §6.1c's own
  note that the mis-slice is "Latent today for two unvaried histograms with identical fills". An
  unvaried program's compile path is untouched; m48 carries a positive control for it, §10):
  the builder compares the number of DISTINCT compiled
  outputs (`GraphStore.deserialize(ir).outputs()`) against the number of distinct record node ids it
  marked and, on a shortfall, raises a `graphed` error naming the outputs and labels involved plus
  the workaround — spell a label whose value equals another's with the SAME expression
  (`variations={"1": w}`, not `w * 1.0`), which routes it through §1.2's record-time dedup path and
  is supported. It MUST NOT slice on a shortfall: the mis-slice surfaces as an opaque worker-side
  `IndexError`. Lifting the refusal into full support (replicating through §8.2(i)'s map once it
  exists) is NOT scoped in m48–m51 and is parked in §11. `ExecResult`/`Plan`/monitor **schemas** do not change in
  m48–m50 (per-variation monitor events: Phase 2, the defaulted-field trick documented —
  `store.py:31-41` precedent); the absence is a frozen m48 anchor (§10), worded over **schema KEY
  SETS asserted against LITERALLY SPELLED expected sets, never against a sibling unvaried run**
  (r19 — all three are dataclasses whose field names are class-level constants
  (`python/graphed/core/execution.py:206-217` `Plan`, `:219-224` `ExecResult`, `:335-351`
  `TaskEvent`, the monitor payload, passed through by instance at `:378-384`), so a
  varied-vs-unvaried key-set comparison is equal BY CONSTRUCTION — including after an implementer
  adds a field, which is the only thing the anchor exists to detect; this is the §6.3 repair r17
  made for the params key set, applied here), not over plan bytes: §8.2(i)'s added
  `_PartitionReduce` field leaves the public schemas
  untouched but *does* change the shipped worker closure — and **wherever that closure is wrapped
  for checkpointing** it is embedded as an opaque cloudpickle `OpSpec` whose bytes feed
  `identity()` and therefore `task_id` (`python/graphed/core/plan.py:72-90,164-176`). **That wrap
  is a CALLER step, not something `aggregate_plan` performs** (r17 — measured: `aggregate_plan`
  returns a `graphed.core.execution.Plan`, whose `process` is a plain
  `Callable[[Partition, WorkerResources], R]` with no `identity()` and no `task_id`
  (`python/graphed/core/execution.py:206-217`; the construction at `aggregate.py:95-108`), while
  `task_id` lives on `DurablePlan`/`DurablePlanV2`, whose `process` is an `OpSpec`
  (`core/plan.py:54,126,164-176`), and **no `Plan → DurablePlan` bridge ships**:
  `grep -rn "DurablePlan(" python/` → 0 hits (every construction is in hand-written tests) and the
  only production `OpSpec.from_callable` call sites are the four V2 shuffle/join stages
  (`shuffle.py:181,188,245,259`)). See §7.3 for the churn that causes and for its exact scope.
- **§7.3 (Checkpoint semantics, documented honestly and anchored.)** Within one plan, resume works
  per-partition exactly as today (the N-variation composite partial is the journal unit) — m49
  freezes an interrupt/resume test over a varied graph whose result is byte-identical to an
  uninterrupted run. **The fixture's plan construction is bound, because a varied AGGREGATE graph
  does not reach the checkpoint runner on its own** (r17): `run_resumable` takes a `DurablePlan` —
  it calls `plan.process.resolve()` and `plan.task_id(part)`
  (`python/graphed/checkpoint/runner.py:77-91`) — while `aggregate_plan` returns a plain
  `Plan` (§7.2), so the m49 fixture builds the `DurablePlan` explicitly — **BY VALUE:
  `DurablePlan(ir=compiled.ir, process=OpSpec.from_callable(plan.process), …)` over the plan
  `aggregate_plan` actually returned** (bound in r18; the m8 `OpSpec.from_ref` pattern —
  `tests/frozen/checkpoint/m8/analyses.py:114-123` — stays the documented USER idiom but is NOT the
  fixture construction, and the r17 "either/or, the anchor states which" is withdrawn). The reason
  is measured: `OpSpec.identity()` for `kind="ref"` is `b"ref\0" + ref`
  (`python/graphed/core/plan.py:72-76`), so the closure's FIELDS are not in the plan bytes at all —
  under `from_ref` the §8.2(i) determinism anchor freezes GREEN against a `frozenset`
  `variation_labels`, the exact defect it exists to catch — and a `from_ref` fixture's `process` is a
  hand-written module-level callable over a hand-built IR, exercising no varied lowering. **The
  fixture's closure operands (the `PartitionedSource`, the reduce/combine/empty callables) MUST be
  module-level definitions in an importable module**, for the converse reason: re-measured r21
  (cloudpickle 3.1.2, CPython 3.12.10, `PYTHONHASHSEED` ∈ {1, 7, 12345}) an importable frozen
  dataclass carrying a
  SORTED TUPLE of labels digests identically across all three seeds while the
  same dataclass carrying a `frozenset` gives three distinct digests — but the SAME dataclass defined
  in `__main__` (pickled by value) gives three distinct digests for BOTH forms, i.e. the anchor would
  be red against a correct implementation. **The r18–r20 literal `80e8024dc8f3b77d` is WITHDRAWN,
  r21**: cloudpickle bytes for an importable class embed its module, qualname and field names, none
  of which that row named, so the digest is not re-runnable and fails this document's own r14
  reproducibility standard — the standard that withdrew the r12 §6.4e digest pair. The QUALITATIVE
  shape above is what reproduces (a module-level dataclass of one's own gives one digest ×3 for the
  sorted tuple and three distinct for each of the other two cases); §8.2(i)'s digest triple, which
  DOES name its payload, was re-run in r21 and reproduces exactly. The same clause governs the §8.2(i) plan-byte determinism
  anchor (§10/m49). Across plan revisions, adding/removing a variation changes the IR and
  therefore **every** `task_id` (`plan.py:164-176,286-301`) — no cross-revision reuse. This
  limitation MUST be documented in the user docs and design.rst — naming the canonical
  invalidating edit from the exemplar workflow: toggling the expensive shift class on or off
  between runs (the `skip_obj_systematics` pattern, lit §ewkcoffea-confirmed) rebuilds the IR and
  invalidates the whole cache. **A third invalidation class is a label RENAME, and it must be
  documented alongside the other two** (r16 — §1.2's stated rationale for keeping labels out of node
  identity is "renaming a systematic must not recompute", and that property holds at the IR/interning
  level exactly as §1.2's own m48 anchor freezes it, but NOT at checkpoint granularity from m49
  onwards **for a journal whose `process` spec embeds the worker closure BY VALUE** (scope added
  r17): §8.2(i) puts label STRINGS into `_PartitionReduce`, and
  measured, `task_id = sha256(_TASK_DOMAIN, ir, process.identity(), partition_bytes)` while
  `OpSpec.identity()` for an opaque spec returns the cloudpickle blob itself
  (`python/graphed/core/plan.py:72-76,164-176`) — so a pure rename leaves the IR byte-identical and
  still changes those `task_id`s. Under the documented `OpSpec.from_ref` idiom (below) a rename
  changes neither the IR nor the referenced process and invalidates nothing. State the scope
  explicitly in the same doc paragraph: §1.2's
  no-recompute property is about the graph, not about the checkpoint cache. **One-time churn on
  landing m48, SCOPED (r17; the MILESTONE corrected from m49 in r22)**: §7.2's seam half (β) is the
  hook's return channel and m48's (α) anchor freezes that a returned value is carried onto the
  SHIPPED closure and readable there (`plan.process`), which forces the additive §8.2(i) field onto
  `_PartitionReduce` at **m48**; adding it changes the pickled instance state, and the chain this
  section already cites (an opaque `OpSpec.identity()` IS the cloudpickle blob →
  `task_id`, `python/graphed/core/plan.py:72-76,164-176`) makes that a `task_id` churn. Measured
  r22 and re-measured r23 (cloudpickle 3.1.2, CPython 3.12.10): the SAME module-level frozen
  dataclass, with and without one defaulted `variation_labels` field, digests DIFFERENTLY — the
  state dict gains the key whatever its value. **The r22 literal pair `8d058bf867dc6bcd` /
  `22a566276fd6077d` is WITHDRAWN, r23** — it named the toolchain but not the module name, class
  name, field list or instance values, all of which enter cloudpickle's bytes for an importable
  class, so it is not re-runnable (a same-shaped r23 probe gives a different pair) and fails this
  document's own r14 reproducibility standard — the standard §7.3 used to withdraw
  `80e8024dc8f3b77d` and r13 to withdraw the §6.4e pair. The QUALITATIVE shape is what binds and is
  what reproduces; §8.2(i)'s digest triple, which DOES name its payload, is the counter-example
  done right. **m49 only POPULATES the field**, which churns
  nothing further for unvaried programs (their value stays the `None` default) — so every journal
  whose `DurablePlan.process` `OpSpec` embeds
  `_PartitionReduce` by value is invalidated once, at m48, *unvaried* programs included (the field is
  unconditional). r17–r21 attributed this to m49 and m50's FROZEN docs anchor repeated it; both are
  corrected. **It is NOT "every existing journal"**, and the r13–r16 wording that said so is
  withdrawn: measured, `_PartitionReduce` is the `process` of the in-memory
  `graphed.core.execution.Plan` (a plain callable — no `identity()`, no `task_id`,
  `core/execution.py:206-217`), not of a `DurablePlan`, and the documented checkpoint idiom embeds
  the USER's module-level functions BY REFERENCE
  (`process=OpSpec.from_ref("myanalysis:hist_chunk")`, `docs/checkpoint/design.rst:20,58-65`; the
  frozen m8 fixtures do the same, `tests/frozen/checkpoint/m8/analyses.py:114-123`), for which the
  added field changes nothing. Journals of the by-value kind exist only where a caller built the
  `DurablePlan` itself through `OpSpec.from_callable(plan.process)` — measured `kind == "opaque"`
  for a `_PartitionReduce` instance, which carries no `__qualname__` — and `graphed-executors/src`
  has zero `task_id`/`DurablePlan` references at all. Document the churn WITH that scope.
  **The WRITE path has NO journal to churn** (r17 — r13's "the identical one-time churn hits WRITE
  plans when m51 lands" is withdrawn): §6.4f widens `_WritePart.__call__`'s single-output
  unpack, but measured, `graphed.write.write_plan` builds `Plan(process=write_part, …)`
  (`write.py:32-43`) — the same plain-callable `Plan` — while `run_resumable` takes a `DurablePlan`
  (`checkpoint/runner.py:77-91`), so nothing that ships today is invalidated. Where a caller wraps a
  write closure by hand (`OpSpec.from_callable(write_part)`), the m48 churn scope above applies
  verbatim (milestone corrected r22 with the churn itself);
  that is what m51's docs anchor says. Stage-granular content
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
  (i) *Transport*: a `variation_labels: tuple[tuple[tuple[int, int | None], tuple[str, ...]], ...]
  | None = None` field (**the `| None` and the default bound in r22**, because §7.2's (β) makes this
  the hook's return channel — "the per-plan variation metadata, or `None`" — and the field is
  ADDED at m48 as a defaulted pass-through, one milestone before m49 populates it, all under the
  DoD's `mypy --strict` on src AND tests; a non-optional declaration made m48's dummy read-back
  unwritable and would have red m48's frozen (α) anchor at m49)
  — a sorted association list from the **PAIR key** `(reduced_node_id, member_index)` to that
  node's labels (**pair key, r17**: the r11–r16 declaration was int-keyed while this same section
  binds "the map keys on `(reduced_node_id, member_index)` accordingly" and (iii) binds the
  attribution hook to annotate a failure with `(reduced_node_id, member_index | None)` and hand THAT
  to the map — a pair cannot be looked up in an int-keyed table, and r16's m49 anchor reaches into
  this shape directly, so the test-author would have had to guess the key space and freeze the
  guess read-only. The member half is not cosmetic: measured, a universe's chain collapses into a
  Stage whose members are evaluated inline, `execute.py:110-117`, which is why `member_index`
  exists. It is still a sorted tuple, so §8.2(i)'s determinism argument is untouched) — **an
  ORDERED, SORTED label tuple per key, never a `set`/`frozenset`** (r13; the r11/r12 `frozenset[str]` is a
  determinism BUG, not a style preference: a frozenset pickles in hash order, so the closure's
  cloudpickle bytes differ across processes with differing `PYTHONHASHSEED`, and those bytes feed
  `OpSpec.identity()` → `DurablePlan.task_id()`/`to_bytes()`/`fingerprint()`
  (`core/plan.py:72-77,164-176`). Measured, **with the payload and toolchain named so the probe is
  reproducible** (r14 — r13's digest triple named neither the labels nor the cloudpickle version, so
  it could not be re-run, the same defect r13 itself cited when withdrawing the §6.4e digests):
  cloudpickle 3.1.2, payload
  `(3, frozenset({"btag_down", "btag_up", "jes_down", "jes_up", "nominal"}))`, under
  `PYTHONHASHSEED` 1 / 7 / 12345 → sha256[:16] `b7984b3caadf74f7` / `2778da7a97834ac5` /
  `97429e5989f2a831` — three distinct plans for
  one program, violating §3.2 in its R22.3 form, failing the DoD determinism gate, and killing
  cross-run checkpoint reuse outright. The house discipline is already the opposite: `read_columns`
  returns its read set SORTED precisely so a set never reaches a plan — `return tuple(sorted(needed))`,
`projection.py:147` (the whole function is `:109-147`; the r13/r14 `:109-121` pointer landed on the
docstring, corrected r15). The
  §8.2 multi-label rendering already sorts, so nothing downstream changes) — is ADDED to
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
  every `#[pymethods]` fn on `GraphStore`, `src/lib.rs:159-416` — plus the `PayloadDescriptor` and
  `IncrementalReducer` blocks at `:102` and `:470`, neither of which returns an id mapping either;
  r14, the r12/r13 wording cited one span as if it held one block, and a completeness claim needs the
  whole surface: `add_source`/`add_op`/`add_reduction`/
  `add_external`/`add_exchange`/`add_join`/`node_count`/`to_dot`/`serialize`/`deserialize`/
  `nodes`/`outputs`/`reduce`/`reduce_incremental`/`reduction_report`; the `remap` vector lives
  entirely inside `dead_code_elimination` and is never returned, `src/optimizer/mod.rs:88-116`).
  Fusion also means most varied nodes have **no** post-reduction node id of their own: a universe's
  chain collapses into ONE `Stage` whose members are evaluated inline (`execute.py:110-117`), which
  this plan's own §3.3 measurement shows (N=128 universes × 50 chain ops → 129 stages / 258 nodes).
  Binding: m49 adds a **read-only** `graphed-core` accessor returning, for the reduction that
  produced a given compiled artifact, `record_node_id -> (reduced_node_id, member_index | None)`.
  **§3.1 still holds as re-worded in r13** ("no optimizer SEMANTICS change"): it is a read-only
  accessor over data the reducer already computes — no new
  `NodeKey`, no serialize tag, no optimizer arm, no semantics — but it does mean retaining and
  returning the `remap` vector `dead_code_elimination` discards today, which §3.1 now names
  explicitly so an integrity reviewer does not read the m49 work as violating it. The map keys on
  `(reduced_node_id, member_index)` accordingly. If the accessor is descoped, the honest fallback
  is much coarser than r13–r15 stated, and is restated here (r16) rather than silently assumed:
  **an "output-position" fallback is NOT implementable either**, for the same reason part (iii)
  exists — measured, `evaluate_ir` is one flat loop over `store.nodes()` appending into `vals`
  with no `try`/`except` and no per-node annotation, and outputs are selected only at the end
  (`return [vals[o] for o in store.outputs()]`, `python/graphed/execute.py:96-126`), so a failure
  inside the loop carries neither a node id NOR an output identity, and most nodes are not outputs
  at all. Without (iii) the only truthful attribution is **plan-wide**: the raised `StageError`
  carries the sorted UNION of all labels registered on that plan (rendered per the multi-label rule
  below), and the docs say so. That is why (iii) is the keying event for both (i) and any fallback:
  descoping it does not buy a coarser key space, it removes per-label attribution entirely.
  (ii) *Attributed worker-side errors*, which do not exist today: the `evaluate_ir` call site in
  `_PartitionReduce.__call__` is wrapped so a worker failure becomes a `StageError`, and the
  per-node provenance the map keys alongside is shipped in the same closure — **re-keyed through
  the same accessor**, since `Session._provenance` is keyed by RECORD-time ids (`session.py:30`,
  written at `:138,166,181,202,240` — the five `self._provenance.setdefault(...)` sites, one per
  `_array_cls` chokepoint, r17) and inherits the identical remap problem.
  (iii) *Per-node failure attribution inside `evaluate_ir`* — **the keying EVENT, and it is a third
  m49 target** (r13; without it (i) and (ii) do not compose: a wrapper AROUND the call cannot
  produce a node id, so it cannot index the map (i) ships. This is the same "the channel does not
  exist" defect r10 and r11 each fixed one layer up — r10 withdrew r9's transport sentence, r12
  withdrew r11's key space — with the raising-node identity still missing). Measured against
  `graphed-latest@ff7c607`: `_PartitionReduce.__call__` is `read_partition` → `evaluate_ir` →
  `self.reduce(values)`, one call with no per-node context (`aggregate.py:57-65`); `evaluate_ir` is
  a bare `for nd in store.nodes():` dispatch loop with **no `try`/`except` and no node-id
  annotation anywhere**, whose `kind == "stage"` branch evaluates members in an inner loop that
  annotates nothing (`execute.py:99-126`, op dispatch `:109`, stage members `:110-115`). So
  `except Exception` at the call site yields an exception carrying no node id — no map key, no
  label. Binding: `evaluate_ir` gains an **optional attribution hook** (or an equivalent
  exception wrapper) that annotates a failure with `(reduced_node_id, member_index | None)` at
  those two dispatch points, and `_PartitionReduce` maps that through `variation_labels`. This is a
  change to `graphed`'s **evaluation path** — not to core, not to the IR, not to any schema — and
  it lands in `graphed`, so the m49 anchors are worded over the RESULTING `StageError`, never over
  the wrap site. **If (iii) is descoped, the plan-wide fallback above is what remains** (r16 — r13's
  "the output-position fallback is promoted to the primary binding" presumed a fallback that is not
  implementable: it needs the same missing raising-node identity), because the accessor alone then
  buys nothing.
  **The map is set-valued, not a function** — §3.4 proves it in this document: "a node shared by
  `jes_up` and `jes_down` but not nominal appears in BOTH impact sets" — **carried as (i)'s sorted
  tuple**, which is the same content in a deterministic wire shape. Rendering is bound: a
  singleton renders as that label; a multi-label value renders as its labels sorted and joined by
  `,`; the empty value renders `""` (nominal/unvaried, §8.1).
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
  **`graphed.context_of(array)`** (the §2.3e context handle carried by an `Array`/`Varied`, `None`
  when context-free; read-only; m48, spelling pinned at m48 freeze — added r15 because
  `Histogram.fill` lives in `graphed-histogram` and §6.1d requires it to read that handle, while
  every other §9.1 verb TAKES a context and none returns one from a value),
  **`graphed.unify_contexts(*handles)`** and **`graphed.reindex_to(value, ctx)`** (the §6.1d
  lineage seams — most-derived-or-divergence-error over context handles, and an ancestor value
  re-expressed in a context's row space across §6.1d's link kinds; read-only; both m48, spellings
  pinned at m48 freeze — added r20 because `context_of` exposes the HANDLE but nothing exposes the
  RELATION between two handles or the intervening masks, while §6.1d's unification and re-indexing
  are executed by `Histogram.fill` in the other distribution and `graphed.selection` is m51),
  **`graphed.weight(ctx)`** (the context's ambient weight as a `Varied`, `None` when nothing is
  registered; m48 — added in r12 as the weight-side twin of `graphed.selection`: §2.6a reserves no
  attribute names and the r11 surface exposed no accessor at all, so a factor handed to
  `graphed.vary(..., is_weight=True)` was absorbed into an immutable registry the user could never
  read back. That is fine for the ambient-fill mainline but not for §6.4b, whose "their varied
  factors, when among the stored fields" presumes the user can name them, nor for a program that
  needs to READ the ambient weight — to store it, to compare it, or to fold it into a value
  explicitly. **The r12–r23 second ground, "for anything wanting the event weight explicitly
  alongside `unweighted=True`", is WITHDRAWN in r24**: §6.1d's later r19 clause makes that exact
  combination a record-time error, so the rationale named a refused program (§6.1d r24 parks the
  underlying gap in §11). Read-only: it returns the registry's
  current `Varied`, it does not mutate),
  `graphed.variations(ctx)` (per-name listing of a context's registered variations, their tags
  and kinds — **the KIND vocabulary is exactly two words and is fixed here, r24: `"weight"` for a
  §2.1 overload-(b) registration and `"shift"` for an overload-(c) one (overload (a) is loose and
  reaches no context), and the return type is `{name: {tag: (kind, value | None)}}`, spelling
  pinned at m50 freeze** — r10–r23 used "kinds" nowhere else in this plan for a variation (every
  other occurrence is a §6.1d LINK kind or a `NodeKey` kind) and gave this entry neither a type nor
  a pinning clause, unlike its neighbours, so m50's test-author would have invented both the
  container shape and the kind strings and frozen them read-only — and, for numeric tags (canonical e-form `m?\d+(em\d+)?`, `5em1` → 0.5; plus the
  datacard p-form `m?\d+(p\d+)?`, `2p5` → 2.5), the parsed float value: the ordering handle for
  σ-scan/envelope plots, since §6.2's sorted axis is lexicographic), **`graphed.selection(ctx)`**
  (the `Varied` mask that derived a context from its parent, `None` for a root context — the
  §6.4a bridge that makes the m51 skim sink reachable from the §2.6 context idiom; m51.
  **Its answer on a universe/nominal-derived context is stated here, r15**, because §2.2 gave a
  second, differently-typed definition for that case — "equal to the argument's selection at that
  label", which is the mask that derived the ARGUMENT from ITS parent, restricted to one label: on a
  context produced by `graphed.universe`/`graphed.nominal` the verb returns **that label's member of
  the argument's own selection — an unvaried `Array`, not a `Varied`, living in the GRANDparent's
  row space** (`None` when the argument is a root context).
  **Its answer on a `graphed.vary`-derived context is stated here too, r16**, because that is the
  third §6.1d link kind and it is the one the §2.6 sketch's own skim path produces
  (`sel = events[mask]` then `sel = graphed.vary(sel, "btag", …, is_weight=True, …)` rebinds `sel`,
  §2.6 sketch, so `graphed.selection(sel)` on the rebound name would otherwise be undefined and the
  canonical §6.4a spelling would silently pass `None`): a `vary` link is an IDENTITY link (§6.1d
  link kind (2) — the row space is unchanged, only registrations differ), so the verb returns the
  selection of the **nearest ancestor reached across `vary` identity links only** — i.e. it skips
  over any number of `vary` links and answers as of the first non-identity link, `None` when that
  walk reaches a root context. One rule, stated per lineage link kind,
  matching §6.1d's r15 link-kind table),
  **the §6.1a RESULT UNPACKER** (`graphed_histogram.unpack(value) -> dict[str, bh.Histogram |
  dict[str, bh.Histogram]]`-shaped, over the executed plan's flat slot-keyed value ALONE, choosing
  per output from the SLOT KEY FORM (r19 — the r18 "plus the plan's layout … the layout's MODE" is
  unreachable from a one-argument verb and unnecessary: the three key forms are disjoint and per
  output, §6.1a/§6.1c); read-only; **m48, spelling pinned at m48
  freeze** — added r18 because §6.1a's result shape is produced by no bound surface today: `Plan` has
  no finalize hook and `ExecResult.value` is exactly the combine output,
  `python/graphed/core/execution.py:206-224`, while `plan()` returns that `Plan` and nothing else,
  `graphed-histogram src/graphed_histogram/boost.py:256-295`),
  **a per-label FILL-NODE accessor** (`graphed_histogram.fill_nodes_by_label(h) -> dict[str, Array]`
  -shaped, or an equivalent labelled return from the §6.1c group API; **exact spelling pinned at
  m48 freeze**, m48 — added in r13 because §4.3's bound extraction mechanism reaches for the §7.2
  `(output, label) → node id` map, which §7.2 only says the frontend *owns*: ownership is not an
  importable surface, and today's public `Histogram.fill_nodes()` is UNLABELED
  (`graphed-histogram src/graphed_histogram/boost.py:218-219` — staged-fill order, no label
  attribution, and nothing in this plan pairs that order with `graphed.labels` order). Read-only),
  **the §3.4 impact API** (`{label: tuple[int, ...]}` of that label's sorted record node ids, over
  `read_columns`' operands; read-only; m49, spelling pinned at m49 freeze — shaped in r24 for the
  reason r16 shaped the projection-stats verb below),
  **the §5.3 per-label projection-stats verb** (`{label: tuple[str, ...] | None}` of that label's
  sorted read set — `None` meaning "read every column", `read_columns`' own conservative answer,
  §5.3 r17 — over `read_columns`' operands; read-only; m49, spelling pinned at m49 freeze — added
  r16, because §5.3 bound the exposure and anchored it while naming no surface, the same
  unwritable-as-stated defect r15 fixed for §2.5's diagnostic channel), and a
  plan-level listing of `{output: [labels]}` **(m50; spelling pinned at m50 freeze; its own frozen
  anchor in `graphed`'s `tests/frozen/preserve/m50` — r16: r10–r15 anchored it "inside m50's
  `inspect()` test", which cannot exercise it, since measured `inspect(bundle: Bundle) -> str`
  renders a preservation BUNDLE as human-readable text, `python/graphed/preserve/bundle.py:268-288`
  — it takes a bundle, not a plan, and returns a string, not a mapping, so a string-containment
  assertion over a bundle rendering leaves the mapping API uncovered under the DoD's ≥90%
  diff-coverage-from-the-frozen-suite gate)** constitute the introspection surface (RDF
  `GetVariations` analogue); `inspect()`'s own label listing stays anchored in m50's `inspect()`
  test (§9.2).
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
**Pinning the directory does not close the per-FILE hazard for the two new NON-split directories**
(r13): `scripts/run-tests.sh:16-25` runs `core` and `preserve` as ONE pytest process each —
`SPLIT_PKGS` is `"frontend numpy awkward"` only (`:30`) — there is no `__init__.py` anywhere under
`tests/frozen` (measured), and prepend import mode turns a duplicate top-level basename into a
collection ERROR. The colliding names are the natural ones: `tests/frozen/core/m4/test_benchmark.py`
already exists while §3.3 tells the author to replicate it, and `tests/frozen/preserve/m9/` already
holds `test_reproduce.py` AND `test_inspect.py` — precisely m50's §9.2 anchors. Binding: files under
`tests/frozen/core/m49` and `tests/frozen/preserve/m50` MUST use basenames unique across their whole
package subtree (e.g. `test_variation_benchmark.py`, `test_varied_bundle_reproduce.py`,
`test_varied_inspect.py`).
**The rule GENERALIZES to every new frozen directory this plan creates, in every repo** (r14 — r13
scoped it to the two `graphed` non-split subtrees, but the hazard is identical wherever one pytest
process collects a flat tree with no `__init__.py`): measured, `graphed-histogram` runs
`pytest tests/frozen` in ONE process (`.github/workflows/ci.yml:44`) with zero `__init__.py` under
`tests` and gains THREE flat directories (`m48`/`m49`/`m50`) whose natural file names collide with
each other and with the existing `m23`/`m29` files; `graphed-executors` likewise runs
`pytest tests/frozen` in one process (`.github/workflows/ci.yml:44,67`; `:101` and `:153` run only
`tests/frozen/m42 … m45` and `m46`/`m47` — span corrected r23) with zero `__init__.py`
and 15 existing milestone directories; and `graphed`'s `checkpoint` subtree — where §7.3/§7.4 belong
— is NOT a `SPLIT_PKG` and already holds `tests/frozen/checkpoint/m8/test_resume.py`, the most
natural name for an m49 resume anchor. Binding: **every file added under
`graphed-histogram tests/frozen/m48|m49|m50`, `graphed-executors tests/frozen/m49`,
`graphed tests/frozen/{core/m49,preserve/m50,checkpoint/m49}` and `uproot5-graphed-mvp
tests/frozen/m51` carries a basename unique across its whole pytest-process scope**, and a helper
imported across directories is added to that repo's `pythonpath` (the same clause `graphed` already
carries; `graphed-histogram` uses the convention at `pyproject.toml` `pythonpath = ["src",
"tests/frozen/m23"]`, `graphed-executors` at `pythonpath = ["src", "tests/frozen/m7", …]`).
`graphed-executors` = flat `tests/frozen/m49`;
**`graphed-histogram` = flat `tests/frozen/m48`, `tests/frozen/m49` and `tests/frozen/m50`**
(r13 — `tests/frozen/m49` was missing here while m49 anchor (i) bindingly requires it, the very
"which anchor is frozen where" gap this paragraph exists to close; its existing shape —
`m23/`, `m29/`; m50's primary target §6.2 lives there, so its directory is pinned too, while
m50's `graphed` half is `tests/frozen/preserve/m50`, which hosts m50's preservation, docs **and
frontend-introspection** anchors — the §9.1 `graphed.variations(ctx)` anchor and the §6.2(i-bis)
narrowing-helper behaviour of `graphed.labels`/`graphed.universe` over a histogram object both live
in `graphed`, so r11's "preservation/docs only" description contradicted m50's own anchor list
(r12; mechanically the directory is fine — `scripts/run-tests.sh:16-25,30` runs `preserve` per
package and frozen tests already import across package boundaries, e.g.
`tests/frozen/frontend/m40/test_noninner_null_key_option.py` importing `graphed.awkward`).
**`uproot5-graphed-mvp` has NO frozen tree today** — verified at `393ecef`: its graphed tests are
flat, ordinarily-named files directly under `tests/` (`test_graphed_write.py`,
`test_graphed_nanoaod.py`, … **12** files, plus the two shared helper modules
`graphed_uproot_analysis.py` / `graphed_uproot_report.py`, which are not `test_graphed_*.py`) and
the string `tests/frozen` appears nowhere in the repo.
m51 therefore **CREATES `tests/frozen/m51/` there**, and the integrity rules bind it from freeze;
the existing `tests/test_graphed_*.py` stay unfrozen.
**That repo's GATES are analysed here too, r23, because §10 does it for the other three and m51's
ROOT half is "the larger half of m51" (§6.4f)** — measured at `393ecef`: the new tree IS collected
(`pyproject.toml:136`, `testpaths = ["tests"]`), but the only workflow that installs `graphed` and
runs the graphed tests is `.github/workflows/graphed.yml`, whose test step is
`python -m pytest -vv tests -m "not xrootd"` at `:55` with **zero `--cov`** (`grep -c cov
graphed.yml` → 0), on **ubuntu-latest only**, CPython **3.11/3.12 only** (`:26-32`), triggered
`on: push: branches: [graphed-mvp]` + `workflow_dispatch` (`:7-10`, **not** on `pull_request`); the
repo has **no `[tool.mypy]` section at all** and no coverage config. As configured, the DoD's ≥90%
diff coverage FROM THE FROZEN SUITE, `mypy --strict`, and full-§A.5-matrix CI green (R0.5) cannot
be discharged for that half — the silently-discharged-gate class §10 repairs three times for the
other repos. **Binding, as part of m51:** (a) a `--cov` invocation over m51's new ROOT-side source
with the ≥90% diff-coverage gate, added to `graphed.yml` (the `graphed-histogram
.github/workflows/ci.yml:44` shape, `pytest tests/frozen --cov=… --cov-branch`); (b) a
`[tool.mypy]` config covering that new source AND `tests/frozen/m51` (R0.4a); (c) an explicit
statement, in m51's DoD record, of the CI matrix its DONE is keyed on for this repo — either widen
`graphed.yml` toward §A.5 or record the reduced matrix (ubuntu / 3.11-3.12) as the accepted scope —
and either add `pull_request` to the trigger or state that DONE is keyed on a branch push.
Each milestone runs the full §12 process. Frozen anchors listed here are the acceptance skeleton
the test-author starts from; the frozen m05/m4/m9/m23/m29 artifacts are **binding and unchanged**.

- **m48 — `vary` frontend + weight path** (repos: `graphed` + `graphed-histogram`).
  Targets: §1, §2 (incl. the §2.6 event context) **except §2.5's shift-after-weight ordering
  diagnostic, which is m49's — it needs §3.4's reachability cone, which r14 moved to m49** (r19 —
  §2.5 itself says "it is an m49 target" and r18 added it to m49's target line, while this line's
  bare "§2" left a reviewer checking "targets exactly as specified" with two answers), §3.2, §4,
  §6.1 (incl. §6.1d
  ambient fills; **§6.1b's arity anchor is m49's — m48's `W` is exercised by the corpus weight
  matrix, while a COUNTED `1 + |S| + |W|` assertion needs the shift path (§5, m49); m48's own
  varied-AXIS and varied-`sample=` programs are anchored for fold order and result shape, not for
  arity, r23**:
  every other cross-milestone split on this line is annotated explicitly (§3.4 → m49, §2.5's
  diagnostic → m49, §6.1c's axis slot → m50, `to_parquet` → m51) and this one was not, while §10 is
  "the acceptance skeleton the test-author starts from"; no coverage gap results, since §6.1b
  describes a property of the sibling lowering that m48's matrix and §6.1a anchors exercise and
  §6.1b's own r20 clause concedes the `S`/`W` split is unwitnessable before m50. **The r22
  justification "m48 has weight labels only, so `|S| = 0`" is WITHDRAWN as measurably false of
  m48's own anchor list, r23**: §6.1b r19 defines `S` as the labels borne by any AXIS value or by a
  `Varied` `sample=`, and **two** m48 anchors carry a non-empty `S` — the four-way fold-order anchor
  (varied values in TWO axes plus a varied `sample=`) and §6.1d's link-kind-(1) fixture
  `h.fill(events.MET.pt, sel.MET.pt)` with `sel = events[varied_mask]` (**r24 drops r23's third
  item: §2.3b's `plain_array[varied_mask]` anchor performs NO fill — its stated negative controls
  are `TypeError`/`AttributeError` shapes "invisible to a histogram-value comparison" — and `S` is
  a property of a FILL, so it is undefined there; the two above carry the point**) — so a test-author could otherwise read m48 as carrying no axis-borne
  labels at all. The placement is unchanged)
  **except §6.1c's AXIS-MODE slot, which is m50's with §6.2** (r16 — m48 implements
  only the sibling `{(output, label): [indices]}` layout its anchors exercise), **§7.2** (r12 — m48 freezes the §7.2 schema-absence anchor, and §6.1a/§6.1c
  cannot be implemented without §7.2's `(output, label) -> node id` map and the indices-based
  `_GroupReduce.layout` it feeds; **including §7.2's r19 `aggregate_plan` SEAM**, without which the
  COMPILED ARTIFACT is not available where §7.2's own merge refusal needs it (**r21 — §6.1c's layout
  is NO LONGER a consumer: it is derived from `plan()`'s own ordered `fill_nodes` list,
  `graphed-histogram src/graphed_histogram/boost.py:281`**) —
  measured, `aggregate_plan` compiles internally at `python/graphed/aggregate.py:95` and takes
  pre-built closures; §7.1/§7.3/§7.4 stay m49), **plus §8.2(i)'s `variation_labels` FIELD
  DECLARATION ONLY — `tuple[…, …] | None = None` on `_PartitionReduce`
  (`python/graphed/aggregate.py:44-55`), unpopulated: it is §7.2's (β) return channel and m48's (α)
  anchor reads a returned dummy off the SHIPPED closure, which is unimplementable without the
  field; §8.2(i)'s accessor, keying and population stay m49 (r23 — r22 bindingly moved the field to
  m48 in §7.2/§7.3 and m50's docs anchor, but it landed on NO milestone target line while m49's
  target line still takes `§8` wholesale, so a reviewer checking the DoD's "targets exactly as
  specified" got two answers — the defect class §10 repairs by annotation four times already)**,
  §6.3, **§9.1 partially —
  `graphed.labels`/`universe`/`nominal`/`weight`, `graphed.context_of` (r15),
  **`graphed.unify_contexts` + `graphed.reindex_to`** (r20 — §6.1d's lineage seams, without which
  m48's fill-shaped re-indexing anchors are implementable only by reaching into `graphed`'s private
  context object from `graphed-histogram`), the per-label
  fill-node accessor, and `graphed_histogram.unpack` (r19 — §9.1 marks the r18 unpack verb m48 with
  its spelling pinned at m48 freeze and m48's §6.1a anchor is bindingly worded over it, while the
  r18 target line's "only" excluded it) only** (r13;
  §9.1 marks all four m48 and §2.6a agrees, but m48's target line named no §9 section while m50's
  said "§6.2, §9", leaving `graphed.weight` an m50 target that an m48 frozen anchor consumes — the
  §2.1 stacking anchor MUST use it, and §6.4b is stated to be unsatisfiable without it. m50's §9
  target narrows to `graphed.variations` + §9.2 correspondingly; m51's carries `graphed.selection`).
  **§3.4 is an m49 target, NOT m48** (r14 — m48 listed it "(API only)" while §3.4 itself and m49's
  target line both place its frozen anchor in m49, and no m48 anchor exercises it: §4.3's impact-set
  cross-check is explicitly optional ("MAY ride along"). New m48 source with zero m48 frozen coverage
  either fails the DoD's ≥90 % diff-coverage-from-the-frozen-suite gate or is covered only by
  `tests/extra`, which that gate excludes. The API lands with its anchor in m49.)
  **The anchor list is PARTITIONED per repo, and the fill-dependent half needs a dependency edit**
  (r11 — the same analysis §10/m49(ii) already did for its half; leaving m48 a single flat list
  for two repos left "which anchor is frozen where" undecided while §10 pins directories):
  **`graphed`, `tests/frozen/frontend/m48`** takes the pure-frontend anchors (§1.1 grammar, §2.x
  semantics, §2.6 context lineage, §1.2 label-out-of-identity **except the RESULT-MAPPING half of
  its dedup clause** (r14 — "except its dedup half" contradicted the straddling-anchor assignment
  four lines below, which keeps the dedup clause's arena-Δ/node-id/one-value half in `graphed`)
  **AND except the VARIED half of its §7.2 merge-guard clause, r20** (§7.2 r18 binds that guard's
  SITE to `graphed-histogram`'s group-plan builder — `plan()`,
  `src/graphed_histogram/boost.py:256-295`, verified the sole owner of `(output_name, Histogram)`
  pairs — so triggering it needs `Histogram.fill` + `gh.plan(...)`; left in `graphed` it needs
  `pytest.importorskip("graphed_histogram")`, i.e. a SKIP in CI silently discharging the milestone's
  merge guard, the failure mode §10 fixes three other times. The UNVARIED scope positive control
  (`compile_ir(s, b, b * 1.0)`) needs no fill and stays in `graphed`), §3.2
  determinism, §7.2 schema absence, **§7.2's r19 `aggregate_plan` seam (α), r20**).
  **The "needs a fill ⇒ `graphed-histogram`" rule is GENERAL over m48's whole anchor list, r20** —
  it is stated below inside straddling-anchor (3), scoped there to the §2.6/§6.1d mega-bullet, while
  it is exactly the rule that decides every other split in this milestone; it is promoted here.
  **`graphed-histogram`, flat `tests/frozen/m48`** takes every
  anchor that needs a fill:
  the corpus weight matrix + its §5.2b read witness, §6.1a result shapes, §6.1c `.plan()` refusal,
  §6.1d ambient fills, §4.1 correctionlib, §6.3 goldens, **and §4.3's selection-invariance anchor**
  (r13 — its operands are per-label fill nodes read through §9.1's accessor, so it is fill-shaped;
  r12 named the anchor's mechanism but assigned it to neither repo).
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
  mega-bullet below is SPLIT **by a RULE, not by a frozen enumeration** (r16 — the enumeration was
  written in r12 and two clauses added since are fill-dependent while sitting on the `graphed` side:
  r14's discriminating second `graphed.labels` program ends "…remains a superset of the
  context-borne half of a FILL's label set", and r15 strengthened the
  `graphed.universe`/`graphed.nominal`-return-a-CHILD clause to be asserted over the resulting VALUE
  of `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)`; both then need `graphed_histogram` inside
  `graphed`, i.e. `importorskip`, i.e. a SKIP in CI — `graphed pyproject.toml:29-48` vs
  `.github/workflows/ci.yml:34`, house pattern
  `tests/frozen/preserve/m25/test_histogram_preservation.py:31`). **The rule: any clause whose
  assertion requires a `Histogram.fill` lives in `graphed-histogram`'s flat `tests/frozen/m48`;
  everything frontend-observable stays in `graphed`.** Applied to the enumeration: the pure-frontend
  clauses (tag grammar, no-reserved-names, lockstep
  validation, data guard, lineage, the §2.6c ambient-registry re-indexing,
  op-level divergence **and `vary`-construction divergence**, r18) stay in `graphed`, as do the frontend-observable HALVES of the two split
  clauses (`graphed.labels(ctx)` reports the shift labels; `graphed.universe`/`nominal` return a
  context that is a CHILD of the argument); the fill-shaped clauses (ambient fill on a per-object
  quantity, the manual-broadcast reference (all THREE of its assertions, incl. r18's
  contexted-but-unvaried one), the execution-time refusal, divergent-lineage AT THE
  FILL, **§6.1d's link-kind-(1) ancestor-VALUE re-indexing (r18)**,
  `unweighted=True`, §6.1d's four-way fold order, the fill-label-superset half of the
  `graphed.labels` clause and the projected-VALUE half of the universe/nominal clause) go to
  `graphed-histogram`'s flat `tests/frozen/m48`. **Neither repo can host the matrix as it
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
  the 23 JSONs live in the repo dir `corpus/references/`). **Binding: m48 VENDORS the corpus into
  `graphed-histogram` exactly the way `graphed` already does** — copy `graphed_corpus` + the 23
  reference JSONs to `tests/_corpus/` and put that directory on the repo's `pythonpath` — **and the
  matrix anchor MUST NOT be guarded by `importorskip`** (a skipped headline gate is a silently
  discharged milestone). **Vendoring, NOT a new dependency** (r13; r12 bound "dev extra AND vendor",
  which mixes two mechanisms and mis-describes the cited precedent: measured, `graphed` has no
  `graphed-corpus` in ANY extra — `pyproject.toml:42-48` — and vendors
  `tests/_corpus/{graphed_corpus,references}` with `tests/_corpus` on `pythonpath` `:115-127`. A
  dependency edit alone also would not install: `graphed-corpus` is not resolvable by name in this
  org's CI — the working precedent pre-installs it from a git URL via a workflow env var BEFORE
  `pip install -e .[dev]` (`graphed-executors .github/workflows/ci.yml:17` `CORPUS: "graphed-corpus
  @ git+…"`, installed at `:38`), and `graphed-histogram`'s workflow has neither
  (`.github/workflows/ci.yml:13-17` carries `GRAPHED` + `EXECLOCAL` only). If a future revision
  prefers the dependency route instead, it MUST bind the pair — dev-extra name PLUS the env var and
  its `pip install` line in every job that runs the frozen suite.)
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
    `histograms.py:20,35-37,40-43` — `bin_values`/`fingerprint` round again; the r6–r21 span
    `:39-42` opened on a blank line and stopped one short of `fingerprint`'s
    `return hashlib.sha256(payload).hexdigest()[:16]`, the line that establishes the claim —
    re-measured r22). So (a) the recorded
    program must re-express the pre-fill rounding if bin-edge decisions are to match the corpus's
    cross-platform-stability intent, and **gak has no `round(x, decimals)`** (`rint` exists only
    as a ufunc, `python/graphed/array.py:54`), so `rint(x * 1e6) / 1e6` is the expressible form;
    (b) conversely `bin_values`' driver-side rounding is what absorbs the float-summation-order
    differences a per-partition fill introduces, so the comparison rides
    `bin_values`/`fingerprint` — **raw-view bit-identity vs the references MUST NOT be asserted**.
    **Third mid-freeze discovery spared, r19**: the b-tag SF's operand is the **pt-CUT** jets
    (`sel.Jet[sel.Jet.pt > 25]`, §2.6 sketch note (iii)), not `sel.Jet` — the corpus computes
    `sel_jets = good[sel]` off `good = jets[jets.pt > 25]` and products the per-jet SF over `axis=1`
    (`graphed-corpus src/graphed_corpus/analyses/systematics.py:60-76,25-36`), so including sub-25
    GeV jets changes the weight and misses the references.
  - §4.3 structural selection-invariance, in the r10 binding form: **the selection cone's node ids
    are identical across all weight labels** (NOT the withdrawn impact-set-subset wording, which is
    false for a correct implementation — §4.3); **with the extraction mechanism named** (§4.3 r12):
    per label, `reachable(fill_node[label])` via `session.walk`
    (`python/graphed/session.py:245-252`), `fill_node[label]` from **§9.1's per-label fill-node
    accessor** (`graphed_histogram.fill_nodes_by_label(h)`-shaped, spelling pinned at m48 freeze —
    r14; this bullet still said "the §7.2 map", which r13 established is not an importable surface:
    §7.2 binds only *ownership*, and a frozen test cannot import an internal), asserting **that the
    per-label fill nodes' NON-WEIGHT input ids agree with nominal's** — `store.nodes()[fill_id]
    ["inputs"][:n_axes]`, identical ids ⇒ identical cones by interning (§4.3 r16). **The r12–r15
    intersection wording is NOT frozen** — it is satisfied by construction (the axis args' cone
    contains the selection mask's in every implementation that fills selected data, so the
    intersection is a constant) and passes a `mask_L = mask & g_L` implementation; the optional
    reachability cross-check is frozen only in §4.3's discriminating shape.
    m05 equal-counts as sanity.
  - **§1.2 label-out-of-identity** (no anchor existed before r10, and it guards the whole interning
    story) — **for a varied program in the DEFAULT SIBLING lowering** (r13; §1.2's own §6.2
    carve-out makes both clauses false by design in m50's axis mode, where labels ARE StrCategory
    bin identities inside the content-hashed spec, `graphed-histogram
    src/graphed_histogram/boost.py:180-212`; every sibling-exposed anchor elsewhere carries this
    scoping and this one was left general): no node's `name` or `params` — **including, for a
    reduced `stage` node, its `members`' own names and params** — contains any label string,
    AND renaming every label leaves `compile_ir(...).ir` byte-identical. **"or token" is DROPPED,
    r19**: measured, `GraphStore.nodes()` yields `{id, output, inputs, kind, name, params}` (a
    stage adding `n_members`/`members`, each member carrying its own `kind`/`name`/`params`) and no
    `#[pymethods]` member returns a token, so the r10–r18 wording asserted over a quantity no public
    surface exposes; the token is derived from kind+name+params, and the byte-identity clause
    strictly subsumes it either way. The house pattern for reaching the store from a frozen test is
    `s._store.nodes()` (`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84,95`).
    Plus the **dedup
    witness §5.2a defers to this bullet**: two labels whose members are structurally identical give
    arena Δ = 0, the same node id, and — per §7.2 — both keys present in the result with ONE
    evaluated fill (measured: `mark_output` de-dups, `src/store.rs:152-153`, so `compile_ir` over
    two identical outputs returns one value). **Plus the NON-record-time collapse case (§7.2 r17)**:
    a label whose member is `nominal * 1.0` (or a sibling's `x + y` against `y + x`) has a DISTINCT
    record node id and is merged by the OPTIMIZER, which the Δ = 0 / same-node-id / one-value
    clauses above provably cannot reach — measured, two fills weighted `w` and `w * 1.0` record
    fill nodes `2` and `4` and compile to ONE output. Assert §7.2's m48 guard: the VARIED program is
    REFUSED with a message naming the labels, not silently mis-sliced — **with the SCOPE positive
    control alongside it (r18), in `graphed`'s half since it needs no fill**: an UNVARIED
    multi-output program whose outputs the optimizer merges — `compile_ir(s, b, b * 1.0)`, measured
    to return ONE value — still compiles and runs exactly as today, so the guard cannot be
    implemented unconditionally in `compile_ir`/`aggregate_plan` (§7.2 r18 SITE+SCOPE; §6.3's
    "no-variation paths are unchanged").
  - **§6.1c `.plan()` refusal** (no anchor existed before r10): `.plan()` on a `Histogram` that is
    VARIED **or in axis mode** (§6.1c's r24 predicate; m48 exercises the varied arm — axis mode
    lands at m50, which extends this to its unvaried axis-mode fourth output — so word the anchor
    over the predicate, not over "varied" alone) raises naming the group API —
    `_SumFills` sums ALL staged fills into one histogram
    (`boost.py:88-98`) and would otherwise silently merge universes into a plausible-looking,
    physically wrong result. Positive control: `.plan()` on an unvaried **sibling-mode**
    `Histogram` still works (r24 — an unvaried AXIS-MODE one is REFUSED, §6.1c).
    **Worded over ANY varied `Histogram` — and, r24, over any AXIS-MODE one — not over the
    fill-node count and not scoped to sibling
    mode** (r14 — r12's count wording over-froze m50's mixed program, and r13's sibling-mode
    rescoping opened a hole: an axis-mode `.plan()` measurably dies inside the reducer, because
    `Histogram.plan` passes the `__init__`-time `self._spec` to `_SumFills`/`_ZeroHist`
    (`boost.py:244-253,146-150`) while §6.2 declares the variation axis at FILL time, and
    cross-axis histogram addition raises — measured, bh 1.8.0: `ValueError: axes have different
    length`; §6.1c). The refusal covers both merge hazards; the group API is the varied route in
    both modes.
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
    stays in `graphed`'s half of the m48 split. **Plus §2.1(b)'s r19 ROW-SPACE positive control**:
    registering, on a DERIVED context, a factor computed from a value read at the PARENT is accepted
    and re-indexed to the derived row space per §6.1d's link kinds, so `graphed.weight(sel)` answers
    at `sel`'s per-label row counts — the invariant §6.4b's row-space precondition assumes;
    `Session.record_op` performs no length check (`python/graphed/session.py:142-168`), so without
    this the mismatch survives recording and dies at execution.
    **Plus §2.1(b)'s r20 DESCENDANT negative control**: registering, on the ROOT context, a factor
    computed from a value read through a DERIVED one (`graphed.vary(events, "btag",
    btag_sf(sel.Jet), is_weight=True, …)`) is a CONSTRUCTION-time error naming both contexts and the
    DIRECTION — it is not divergent, so §2.1's divergence check alone lets it through, and no
    re-indexing exists in that direction (a mask has no inverse, §6.4b), leaving it to record
    cleanly and die at execution outside §6.1d's refusal contract. Both controls are
    frontend-observable through `graphed.weight(ctx)` and stay in `graphed`'s half.
  - **§7.2's r19 `aggregate_plan` SEAM (α), in `graphed`'s `tests/frozen/frontend/m48`** (r20 — the
    seam is an m48 Implementation Target in `graphed`'s `python/graphed/aggregate.py` and every
    requirement consuming it is fill-shaped and lives in `graphed-histogram`, whose frozen suite
    does not count toward `graphed`'s ≥90% diff-coverage-from-the-frozen-suite gate; measured, no
    other `graphed` m48 anchor calls `aggregate_plan`, and `graphed`'s existing frozen coverage of it
    is m5's positive path plus m39's two-source-rejection control
    (`tests/frozen/frontend/m39/test_shuffle_plan_builder.py:58-64` — r21 corrects r20's "only m5's";
    neither exercises a seam that does not yet exist): over an UNVARIED multi-output program in the
    m5 call shape
    (`tests/frozen/frontend/m5/test_aggregate_plan.py:77`), the new hook fires EXACTLY ONCE and
    receives the `CompiledGraph` (the compiled outputs readable inside the hook as
    `graphed.core.GraphStore.deserialize(compiled.ir).outputs()` — **`CompiledGraph` itself exposes
    only `ir`/`source_names` plus `evaluate`, `python/graphed/execute.py:36-52`; measured r24,
    `hasattr(compile_ir(...), "outputs")` is False**) and
    the resulting `Plan` runs to the same value as the same program built WITHOUT the hook (m5's own
    assertion as the positive control), with the existing `reduce`/`combine`/`empty` parameters
    passed as the plain callables m5 freezes (§7.2 r20: the seam is ADDITIVE — those contracts are
    unchanged). **Plus the RETURN-CHANNEL assertion, r21** (§7.2's (β) is the hook's return value):
    a value returned from the hook — a dummy at m48 — is carried onto the SHIPPED closure and is
    readable there (`plan.process`), so a see-only spelling cannot be frozen here and block m49's
    `variation_labels`. **The dummy is a well-typed NON-DEFAULT value of §8.2(i)'s declared field
    type — the empty tuple `()`, r22** (§7.2/§8.2(i): the field is
    `tuple[…] | None = None` from m48, so `()` is well-typed against the field's DECLARED type,
    is distinguishable from the default, and needs no invented type; a str/sentinel dummy is a type
    error at the hook's return and `None` is indistinguishable from the default).
    **The READ-BACK ROUTE is named, r23**: `Plan.process` is declared
    `Callable[[Partition, WorkerResources], R]` (`python/graphed/core/execution.py:210`), so
    `plan.process.variation_labels` is an `attr-defined` error under `mypy --strict` wherever the
    test tree is type-checked (R0.4a; `graphed` is configured `files = ["python"]` today,
    `pyproject.toml:84`, one of the src-only repos R0.4a names as a pending cleanup) — the anchor
    reads the field off the CONCRETE closure type, `graphed.aggregate._PartitionReduce`
    (`python/graphed/aggregate.py:44-55`), via a narrowing `isinstance`/cast, so the route is pinned
    rather than guessed, the discipline §9.1 applies to every other new read surface.
    **"before the worker closure exists" is NOT asserted** — the hook receives
    only the `CompiledGraph` and has no handle on the closure, so a test has no operand for that
    ordering; the return-channel assertion is what makes the ordering observable at all. Seam half
    (β)'s own per-plan metadata is anchored at m49 with §8.2(i).
  - **§6.1d's r20 LINEAGE SEAMS, in `graphed`'s `tests/frozen/frontend/m48`** (new `graphed` source
    whose only consumers are fill-shaped and live in `graphed-histogram`, the same per-repo coverage
    argument as the seam above): `graphed.unify_contexts`-shaped answers the MOST-DERIVED handle for
    handles on one ancestry chain, `None` when every argument is context-free, ignores context-free
    arguments alongside contexted ones (the §6.1d adopt rule), and raises the §2.3e divergence error
    naming BOTH contexts on divergent handles; `graphed.reindex_to`-shaped is the IDENTITY when the
    value already carries the target's handle or carries none, re-indexes an ancestor value
    label-aligned per §2.4 across link kinds (1)-(3) — compared elementwise against a manually
    re-indexed reference, the discriminator §10 already applies to the fill-side twin — and RAISES
    when the value's handle is a DESCENDANT of the target or divergent (§2.1(b) r20).
    **The link-kind half is asserted PER KIND, and each kind's RESULT LABELS are part of the
    assertion, r22** (r20/r21 wrote one undivided "across link kinds (1)-(3)" clause while §2.3d
    stated the disposition unconditionally as "the §2.4 union", which is false across a kind-(3)
    link — §6.1d's own kind (3) yields "an unvaried value in the ancestor's row space" — so a
    test-author working from §2.3d freezes "a `Varied` with the union labels" and one working from
    §6.1d(3) freezes "an unvaried `Array`", mutually exclusive and both read-only, a mid-m48 Test
    Dispute): **(1)** a mask-derivation link returns a `Varied` carrying the intervening mask's
    labels (an UNVARIED value BECOMES `Varied`), each member re-indexed by that label's own mask;
    **(2)** a `graphed.vary` link is the IDENTITY, labels unchanged; **(3)** a universe/nominal
    projection link returns an UNVARIED `Array` equal to a manually projected reference, carrying NO
    labels — the same rule §6.1d r21 uses to make `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)`
    a BARE `hist`.
  - **§2.2 `Varied.apply`**: per-universe application of an `Array -> Array` function, plus the
    error contract — `fn` returning a `Varied` raises with guidance to combine via ordinary ops.
  - **§2.3d module-verb dispositions + §2.2's reserved `Array`-protocol names** (r13 — both were
    introduced as guards against the named confidently-wrong class and neither had an anchor; the
    §2.3a parity gate cannot reach the reserved names, because `node_id`/`session` are plain
    properties, `array.py:137-143`, which `inspect.isfunction` does not enumerate, and m49's §5.4
    anchor is the boundary-crossing refusal, not `graphed.join(varied)`). One table-driven test in
    `graphed`'s `tests/frozen/frontend/m48`, driven by the §2.3d **discovery rule** (dynamic over
    `graphed.__all__`, filtered to `inspect.isfunction` members ANY of whose parameter annotations
    mentions `Array`, **UNION the named floor list — in `graphed`'s test
    `{graphed.compile_ir, graphed.context_of, graphed.broadcast_like}` (**`to_parquet` REMOVED from
    the m48 list, r18** — it carries no disposition until m51, §2.3d r18: it is outside
    `graphed.__all__` so the dynamic half never reaches it, it has no `select=` parameter to refuse
    today (`python/graphed/awkward/io.py:206-216`), and freezing an m48 entry whose VALUE m51 is
    bindingly required to change is a freeze-order trap resolvable only by Test Dispute or integrity
    violation; dropping it costs no class coverage, since the eight dynamically discovered verbs
    already supply *refusing* and *expanding* and the named `broadcast_like`/`context_of` supply the
    other two)
    (`context_of`/`broadcast_like` added r17: measured, the annotation-wide filter discovers 8 verbs
    that are ALL refusing/expanding, so these two are the only representatives of *eager-metadata*
    and *broadcasting* and the per-class floor would otherwise hinge on post-freeze annotation
    style; r16: `graphed` declares no
    `graphed-histogram` in any extra, `pyproject.toml:29-48` vs CI's `.[dev]`,
    `.github/workflows/ci.yml:34`, so naming `Histogram.fill` here forces the house
    `importorskip` and SKIPS the whole table-driven test — discharging §2.3d's dispositions AND
    §2.2's reserved-name anchor with zero frozen-suite diff coverage; `awkward`+`pyarrow` ARE in the
    dev extra, which is why `to_parquet` is reachable at m51 when it joins the list) with
    `graphed_histogram.Histogram.fill`'s disposition
    asserted in `graphed-histogram`'s flat `tests/frozen/m48` — and MINUS `graphed.vary`** — r15;
    measured, the r14 annotation-wide filter discovers 8 verbs and still misses `compile_ir`
    (annotations `Session`/`Any`, `execute.py:54-58`), which is in `graphed.__all__` and so was
    reached by neither channel, dropping frozen coverage of one of the two compile/aggregate
    dispositions; and it would discover m48's own `graphed.vary`, for which no disposition class
    exists. r14 fixed the r13 `Array`-FIRST filter's other three misses
    (`read_columns`/`apply`, plus `graphed.broadcast_like`, which r13 left undisposed). The gate
    carries §2.3c's non-vacuity floor: non-empty, ≥ the freeze-time count, containing every member of
    that repo's floor list, ≥ one member of each class in §2.3d's bound class set **that the repo's
    table can host at THIS milestone** (refusing / expanding / broadcasting / eager-metadata /
    accepting — r16; **at m48 `graphed`'s half hosts AT LEAST {refusing, expanding, broadcasting,
    eager-metadata} — a containment floor, never an exact set, so m51's added *accepting* member
    cannot red it (r18, correcting r17's "the first four ONLY")** — `to_parquet` is out of the m48
    table entirely (§2.3d r18) and the *accepting* representative at m48 is
    `graphed_histogram.Histogram.fill` in `graphed-histogram`'s flat `tests/frozen/m48`, and
    `broadcasting`/`eager-metadata` are supplied by the newly named `graphed.broadcast_like` /
    `graphed.context_of`).
    **The refusal table is SPLIT BY CONTRACT, because §2.3d binds two** (r14 — r13 froze one
    contract for all of them; measured, `GraphedError` subclasses `Exception` with no relation to
    `NotImplementedError` (`python/graphed/errors.py`), so an implementer following §2.3d would fail
    a test freezing the other shape, and frozen tests are read-only):
    the **boundary/plan verbs** (`join`, `repartition`, `pack_key`, `shuffle_plan`, `join_plan`)
    refuse with a refusal that NAMES THE OFFENDING CONTAINER — m48 asserts only that they raise and
    do not silently compile; the exact §5.4 message shape (a `NotImplementedError` naming the label
    and the boundary) is frozen in **m49**, since §5.4 is an m49 target and this bullet's own gak
    clause already defers refusing-class behaviour there. The **compile/aggregate verbs**
    (`compile_ir`, `aggregate_plan`) raise a `graphed` error naming `graphed.universe`, with the
    positive control that the same verb on a plain `Array` still works. **`evaluate_ir` is NOT in
    the table** (r14 — it takes no `Array`: `evaluate_ir(compiled: CompiledGraph | bytes, …)`,
    `execute.py:85-91`, so there is no `Varied` to refuse and the plain-`Array` positive control is
    false for it too — a plain `Array` is not a `CompiledGraph`).
    The expanding verbs are asserted **per verb, r17** (the r12–r16 wording "every expanding verb
    returns the bound per-label shape" is false for `read_columns` and would freeze §5.3's m49 verb
    one milestone early, read-only): `apply` returns a `Varied`; `read_columns` returns the SINGLE
    union read set over all labels' members — `None` if any member's is `None` — NOT a per-label
    mapping (§2.3d). `graphed.broadcast_like` broadcasts (§2.3d, §6.1d); and
    `varied.node_id` / `varied.session` raise `AttributeError` rather than recording a `field` op,
    with a negative control that `varied["node_id"]` (STRING getitem) still resolves as field
    access — so the rule cannot be implemented as a blanket `__getattr__` refusal; **plus the
    PROPERTY half of §2.2's disposition rule, classified BY MEASUREMENT, r19** — the numpy idiom's
    `shape`/`dtype`/`ndim`/`T` are plain properties `inspect.isfunction` never enumerates
    (`python/graphed/numpy/array.py:76-86,159-161`) and so cannot fall through into a recorded
    `field` op, but they are NOT one class: measured against `graphed-latest@ff7c607`,
    `dtype`/`ndim`/`shape` are `_form_meta`-backed and record nothing (`Session.node_count()`
    delta 0) while `T` is `return self.transpose()` over `record_op("transpose", …)` and records
    (delta 1). So the anchor asserts per discovered name against the delta measured on the PLAIN
    nominal `Array`: `varied.dtype` (the eager representative) answers eagerly on the nominal member
    with delta 0, `varied.T` (the recording representative) returns a `Varied` whose
    `graphed.labels` match the input's — the §2.3a *broadcast* disposition its own `transpose`
    method carries — and `varied.node_id`/`.session` raise. Freezing a blanket "delta 0 for every
    property" reds a correct implementation on `T`.
    **The property-classification fixture MUST be a 1-D partitioned source, r20** (§2.2 pins the
    probe to a 1-D `NumpyForm` source; this bullet — what a test-author works from — named
    `varied.T` without repeating it, the same mid-freeze discovery this milestone spares elsewhere
    for `gak.full_like`, `stable()` rounding, `h.axes.name` and the pt-cut jets): measured against
    `graphed-latest@ff7c607`, `NumpyArray.T` on a ≥2-D partitioned form RAISES —
    `gnp.ones(s, (4, 3)).T` → `GraphedTypeError: ill-typed op 'transpose' … transpose without axes
    reverses them, displacing the partitioned axis 0` — so on a 2-D fixture the MEASUREMENT STEP
    itself raises and the gate cannot classify the name at all.
    **Plus the r20 `graphed.context_of`-on-a-`Varied` discriminator**: a container built from an
    ancestor-handled nominal member and a MORE-DERIVED non-nominal member answers with the
    more-derived handle (§2.3e r20 — the container's, not the nominal member's; §2.1 accepts exactly
    such a container and only DIVERGENT handles are refused, and §6.4a(2a)'s handle-equality
    predicate reads this answer). **The FIXTURE is pinned to a `graphed.vary` IDENTITY link, r21** —
    `events2 = graphed.vary(events, "pu", …, is_weight=True)` then
    `v = graphed.vary(events.Jet, "jes", up=events2.Jet)`, asserting `graphed.context_of(v) is
    events2` — **not to a MASK-derivation link** (`up=sel.Jet`): both discriminate identically
    against the nominal-member reading, which answers `events`, but the mask-derived spelling builds
    a container whose members sit in DIFFERENT row spaces, and freezing it read-only would pin such a
    container as CONSTRUCTIBLE for three milestones — foreclosing any §2.1 construction check of the
    kind §2.1(b) r20 just added for the analogous weight-factor mis-spelling (measured, `record_op`
    validates only the backend's `op_form`, never lengths or row spaces,
    `python/graphed/session.py:142-168`, which is why such programs record cleanly and die at
    execution). The identity link keeps the row space fixed and is also closer to what §6.4a(2a)'s
    predicate consumes.
  - **§6.1a result shapes** — **in SIBLING mode** (§6.2 axis mode is m50 and has its own shape,
    §6.2(i-bis); word the anchor so it does not freeze a general rule m50 must contradict), **worded
    over §6.1a's bound UNPACK verb (`graphed_histogram.unpack`-shaped, spelling pinned at freeze) and
    freezing the plan value's slot-keyed shape in the SAME anchor, r18** (the two halves must be
    frozen together or a test-author freezing the nested result shape goes red against an
    implementation conforming to §6.1c's flat keying): the executed plan's value is the flat
    `{(output, label) → bh.Histogram}` mapping (`_add_groups` stays a homogeneous key-wise `+`,
    `graphed-histogram src/graphed_histogram/boost.py:120-122`), and unpacking it on a
    MIXED varied/unvaried output set gives: a varied output is
    `{label: hist}`, an output no variation reaches is a BARE `hist` (not `{"nominal": hist}`),
    absent labels are absent (never duplicated from nominal), and `graphed.universe`/`graphed.labels`
    narrow both shapes uniformly. **Plus a WHOLLY-UNVARIED positive control (r19)**: a group plan
    with no variation anywhere keeps today's value verbatim — every key a BARE output name, so
    `run(gh.plan({"hi": h1, "lo": h2})).value["hi"]` still works **and still type-checks under
    `mypy --strict` once `plan()`'s declared return type WIDENS to the union-key form §6.1a binds
    (`Plan[dict[str | tuple[str, str | None], bh.Histogram]]`), which is part of m48's §6.1c target,
    r20** (the r19 wording claimed the declared `Plan[dict[str, bh.Histogram]]` — verified literally
    at `graphed-histogram src/graphed_histogram/boost.py:262`, with `_GroupReduce.__call__`'s own
    `-> dict[str, bh.Histogram]` at `:108` — is UNCHANGED, which §6.1a's own varied slot keying
    makes false and which reads to an implementer as an instruction not to touch the annotation; the
    RUNTIME half — bare keys, m23 indexing unchanged — is what this control protects and is
    unchanged). §6.1a's
    slot keying is scoped to outputs a variation reaches precisely so the already-frozen m23 suite
    stays green (`graphed-histogram tests/frozen/m23/test_group_plan.py:74-75,86,89,99` all index
    the value by bare output name), and §10 binds those artifacts unchanged.
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
  - **§7.2 schema absence**: the `ExecResult`/`Plan`/monitor payload schema **KEY SETS** on a varied
    program equal **LITERALLY SPELLED expected sets** — `{f.name for f in dataclasses.fields(Plan)}
    == {"process","combine","empty","tasks","next_tasks","stop","open_once"}` and likewise
    `ExecResult` → `{"value","n_partitions","n_combines","stopped"}` and the monitor payload
    `TaskEvent` → `{"phase","key","worker","t","partition","n_entries","bytes_read","error"}`
    (measured, `python/graphed/core/execution.py:206-217,219-224,335-351`; `emit_task` passes the
    `TaskEvent` INSTANCE, `:378-384`, so the payload is that dataclass, not a dict). **A
    varied-vs-unvaried COMPARISON is vacuous and MUST NOT be the assertion** (r19): all three are
    dataclasses with class-level field lists, so both programs yield instances of the SAME classes
    and the key sets are equal by construction — including after a field is added, the only thing
    this anchor exists to detect. The comparison may ride along as a sanity assertion. Worded over
    key sets, NOT over plan bytes or the `process` spec — the §8.2(i) closure field, ADDED at m48
    (§7.2's (β) return channel) and POPULATED at m49, changes those by design (**r23 — the r19–r22
    wording said "m49's §8.2(i) closure field", the milestone r22 corrected everywhere else; the
    `process` spec changes at m48, inside the very milestone this anchor is frozen in**; §7.2, §7.3).
  - Single-pass read witness **on the reference-matrix run** (§5.2b applied to the weight matrix).
  - §3.2 determinism: same varied program compiled in two fresh processes under differing
    `PYTHONHASHSEED` → byte-identical `compile_ir` output; `graphed.labels` order pinned
    (nominal-first + insertion order).
  - §6.3 goldens (committed GIR blob, captured PRE-m48 + the params KEY-SET equality against a
    literally spelled set — `{"spec", "n_axes", "weighted", "sampled"}` for the unvaried
    single-weight fill, §6.3 r17; a `"<new key>" not in params` assertion is vacuous here because
    m48's sibling mode adds no params key at all).
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
    only the *broadcast*, *container-traversing* and *tuple-returning* classes, takes its
    AUXILIARY call arguments from fixtures living in `src` beside the classification **while the
    frozen test itself owns the CONTEXTED primary operand and asserts the returned handle is not
    `None` and IS the input's** (§2.3e(2) r16 — a context-free fixture operand makes the assertion
    `None == None`) — **each fixture being a TEMPLATE with a named substitution SLOT the test fills,
    including inside a Mapping/Sequence argument, plus an assertion that the substitution happened**
    (§2.3e(2) r17: `gak.zip`'s mapping is its ONLY array-bearing operand, `functions.py:118-119`, so
    without a slot the container-traversing class has no test-owned position at all), and asserts the exempt set
    is exactly {*eager-metadata*, *refusing*} **plus §2.3e(3)'s MEMBERSHIP floor** (r19 — the r16
    wording "the refusing class is exactly `{gak.join}` at freeze time" is STALE: §2.3e(3) was
    rebound in r18 to containment plus a monotone count precisely because a frozen equality reds the
    moment a future gak boundary verb arrives with its classification in `src`, which is where the
    self-repairing rule wants it, and §10 is "the acceptance skeleton the test-author starts from",
    so the stale spelling re-installs the trap: **`gak.join` IS IN the refusing class and
    `len(refusing) >= ` the freeze-time count** — measured, the only boundary verb among gak's 65
    public functions, `python/graphed/awkward/functions.py:18`; every eager-metadata member's
    return annotation is non-`Array`; the broadcast count is ≥ the freeze-time count — otherwise a
    re-classification hides an unimplemented member while the exempt CLASS NAMES stay exactly those
    two), **and the `Array`-surface gate carries its own floor** (refusing = `{repartition}`,
    broadcast count ≥ freeze-time, §2.3e(4) r16).
    **Each of these three tests MUST carry §2.3c's non-vacuity floor in
    the same test** — a dynamic gate whose discovery step returns an empty or wrong set passes
    tautologically, and the obvious discovery mechanism does not exist here (gak has no `__all__`,
    §2.3c): the discovered set is non-empty, at least the freeze-time count, and names at least one
    member of each classification class; the parity gate additionally names `__array_ufunc__`,
    `__getitem__`, a bitwise dunder **and at least one public METHOD**.
    **The parity gate's per-name ASSERTION is bound, not just its enumeration** (§2.3a r15): each
    discovered name is resolved on the CLASS (`getattr(type(varied), name, None)`) — an
    instance-level `hasattr` is answered by `Varied`'s label-mapping field access for EVERY name
    (`Array.__getattr__` records a `field` op for any non-underscore name, `array.py:332-335`), so a
    presence-based iteration is green against a `Varied` that broadcasts zero methods — plus one
    behavioural probe per disposition class in the same test (a broadcast method returns a `Varied`
    with matching `graphed.labels`; `varied.repartition` raises the §5.4 refusal rather than
    `TypeError: not callable`).
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
    first) **and §6.1d's FOUR-way fill fold order** — a fill with varied values in TWO axes plus
    an ambient weight plus an explicit `weight=[…]` factor **plus a varied `sample=`** (r16 — r15
    bound `sample=` to fold LAST and no anchor mentioned it; measured, today's `fill` type-checks
    `args` and `weights` but appends `sample` unchecked, `graphed-histogram
    src/graphed_histogram/boost.py:160-178`, so a `Varied` sample falls into `record_external` and
    dies on `.node_id`), asserting the bound operand order
    (axis values in argument order, then ambient, then explicit factors in list order, then
    `sample=`) and that the varied `sample=` is ACCEPTED/expanded rather than raising
    `AttributeError`. **The fixture's histogram MUST use a `Mean`/`WeightedMean` STORAGE, r22** —
    the same pin r21 gave m50's `sample=`-only-label anchor, one milestone earlier and for the same
    measured reason: bh 1.8.0 rejects `sample=` on the default `Double()` AND on `Weight()`
    (re-measured r22 in `graphed-histogram-latest`'s venv: `TypeError: Keyword(s) sample not
    expected`; `Mean()`/`WeightedMean()` accept it) while `graphed-histogram`'s evaluator passes
    `sample` straight to `h.fill` (`src/graphed_histogram/boost.py:60-71`) and `Histogram.fill`
    type-checks nothing about the sample at record time (`:152-178`), so a default-storage fixture
    RECORDS cleanly and dies at EVALUATION, after the freeze, against a correct implementation. If
    the anchor is instead written as a RECORD-TIME assertion — the fold order read off the recorded
    fill node's `inputs` / the per-label fill-node accessor, with the plan never run — the test
    MUST say so explicitly, so the test-author does not build a plan run around it.
  - §4.1 correctionlib single-payload multi-parameterization — **with its observable stated**
    (r15; every neighbouring anchor states one and this was a bare title): all labels' `External`
    nodes share ONE `PayloadDescriptor.content_hash` and differ only in the `systematic=` param, so
    the payload is never duplicated (fixture precedent `tests/frozen/preserve/m9/agc.py:56-62`).
    **The RECORDING SPELLING is named, r22, because only one of the two correctionlib paths yields
    that observable** — the fixture's own
    `graphed.preserve.record_external(s, CORRECTIONLIB_PLUGIN, corr_bytes, [njet],
    params={"name": "event_sf", "systematic": syst})` (`tests/frozen/preserve/m9/agc.py:113-115`),
    re-measured r23 against `graphed-latest@ff7c607` **with the PAYLOAD named, since the hash is a
    pure function of it** (`correctionlib_content_hash` = sha256 over `b"correctionlib-contents-v1"`
    + canonical JSON, `python/graphed/preserve/externals/correctionlib_external.py:14-18`): over
    `agc.correctionlib_json()` at its default `scale=1.0` (`agc.py:38`), three labels give three
    External nodes sharing `descriptor.content_hash =
    sha256:e72c0da3cb6614cfaf50cea8c93ab740e8229986024a8bad4361e9ae82f4b5cd` and differing ONLY in
    `params["systematic"]`. **The r22 literal `sha256:cae4dd4b…` is WITHDRAWN, r23** — it named no
    payload (the deficiency this plan twice used to withdraw other digests) and does not reproduce
    against the fixture it cites at the pinned revision; the substantive half — ONE shared payload
    hash, `systematic` the only differing param — is unchanged and is what the anchor asserts.
    `gak.apply_correction` is NOT that path — measured, it records
    `params={"name": …, "args": json.dumps(args)}` (`python/graphed/awkward/functions.py:505-509`),
    so the systematic value rides INSIDE the `args` JSON string and there is no `systematic` key; a
    test-author reaching for it would find this anchor's observable unsatisfiable. Same
    mid-freeze-discovery service as the `gak.full_like`, `stable()`-rounding and pt-cut-jets notes.
  - §2.6/§6.1d event-context anchors (r6 functional form): ambient fill on a per-object quantity —
    the value passed **UNFLATTENED** (§6.1d), Jet-pT fill yields value labels ∪ ambient labels,
    weight broadcast frozen against a manual-broadcast reference — **for the ambient weight AND an
    explicit `weight=[…]` per-event factor in the same per-object fill** (§6.1d: the evaluator
    multiplies factors after flattening each independently, `boost.py:60-71`, so an unbroadcast
    explicit factor length-mismatches on the mainline idiom) **AND, as a third assertion, for the
    CONTEXTED-BUT-UNVARIED fill — a context with NO registrations, no `Varied` input, a per-object
    value plus an explicit per-event factor** (r18 — §6.3(2)'s r16 trigger is a DISJUNCTION, "a
    context handle OR any `Varied` input", and it was written precisely to cover this case, yet only
    the two ends were anchored: the "neither" end by §6.3's golden GIR blob + params key-set equality
    and the "`Varied` input" end by the manual-broadcast reference above, so an implementer reading
    the trigger as "any `Varied` input" passes both and length-mismatches at execution on a legal
    contexted program): equality against the manually broadcast reference, **plus a witness that the
    seam node was actually recorded** — the fill node's input cone, or a `Session.node_count()` delta
    against the identical fill built with no context handle — plus the **execution-time** refusal
    when a per-object fill hands in an already-flattened value alongside a per-event ambient weight
    (§6.1d r12: an execution-time `graphed` error naming the OFFENDING FACTOR and pointing at
    "pass the value unflattened"; there is
    no record-time discriminator, so do NOT freeze a record-time raise — **and do NOT freeze
    `FillEvaluator` as the raiser**: under the bound broadcast seam the recorded broadcast node is
    upstream of the fill and fails first (measured, awkward 2.12.0: `ak.broadcast_arrays` over
    lengths 7 and 3 raises `ValueError: cannot broadcast RegularArray of size 3 with RegularArray
    of size 7`), so the anchor freezes the MESSAGE CONTRACT at execution time, not a class name;
    same anchor covers an offending EXPLICIT factor, whose message names that factor, not the
    ambient weight; **and the LOOSE-VALUE case as a third assertion** — r15: §6.1d binds a DISTINCT
    message there (it names the offending VALUE, not "the offending factor" and not "pass the value
    unflattened", both of which are the wrong diagnosis for a loose value in the root row space),
    and without this assertion an implementation emitting the anchored factor message for it passes
    every anchor while violating the binding sentence);
    **divergent-lineage detection AT THE FILL** (§2.3e/§6.1d: `h.fill(a_from_ctx1, b_from_ctx2)` —
    handles no op ever combined — is a hard error naming both contexts) **AND AT THE OP**
    (§2.3e r12 — the op-level rule is §2.3e's *early detection* half and had no anchor, so an
    implementation checking only at the fill satisfied every m48 anchor while pointing every
    diagnostic at the fill line instead of the line that mixed the contexts): a binary op over
    `Array`s from two divergent contexts raises AT THAT OP naming both, with a positive control
    that an ancestor-chain pair unifies silently to the most-derived context **AND a SECOND positive
    control for §2.6b's r23 context-IDENTITY rule — two separate `graphed.nominal(sel)` reads (and
    two separate `events[mask]` derivations from one mask) UNIFY rather than raising, since pure
    derivations are canonical; without it the fresh-object-per-call implementation makes them
    SIBLINGS and the divergence error fires on a legal program, and the ancestor-chain control above
    is a different shape that cannot catch it** **AND AT `vary`'s OWN
    CONSTRUCTION** (§2.1 r18 — `vary` is a combining point that no `_array_cls` chokepoint sees, so
    members carrying divergent handles would otherwise be accepted and the loser silently dropped,
    `graphed.context_of` answering with ONE handle — the container's most-derived one, §2.3e r20):
    building a container from members read
    through two divergent contexts is a construction-time error naming both;
    **§6.1d link-kind (1) ancestor-VALUE re-indexing, asserted over the VALUE** (r18 — link kind (3)
    got exactly this strengthening in r15 "so a guess that unifies but silently mis-weights cannot
    pass", link kind (2) is identity, and link kind (1) — §6.1d's own worked example and §2.6c's
    central rule — was covered only by the ABSENCE of an error at the op, the shape r15 rejected for
    its sibling; the §2.6c anchor below is the ambient-REGISTRY re-index, a different operation):
    `h.fill(events.MET.pt, sel.MET.pt)` with `sel = events[varied_mask]` compared ELEMENTWISE,
    label-aligned, against a manually re-indexed reference (each label's ancestor value by that
    label's mask, nominal's by nominal's) — an implementation that unifies the handles but never
    re-indexes the ancestor value must fail it, on the row COUNT alone. **Both axis values are
    PER-EVENT, and the fixture MUST NOT be "improved" to a per-object second axis, r19** (the r18
    spelling `h.fill(events.MET.pt, sel.Jet.pt)` cannot execute at all: the evaluator flattens each
    axis independently, `graphed-histogram src/graphed_histogram/boost.py:39-47,60-71`, and bh
    requires equal lengths across axes — measured, bh 1.8.0, `ValueError: spans must have
    compatible lengths` — so it would red for a reason unrelated to what the anchor asserts, and
    §6.1d's broadcast seam is scoped to weight factors, never axis-vs-axis);
    lineage semantics (`graphed.vary` returns a NEW context and the
    input context is unchanged — a fill from the pre-vary context carries no new label, a fill
    from the returned context does; ancestor-chain inputs unify to the most-derived context);
    **context-handle ORIGINATION** (§2.3e r14 — the merge-from-inputs rule alone gets this wrong,
    since `Session.source` receives no context and `record_op` merges only from `inputs`,
    `session.py:133-140,142-168`): the same read performed through a `vary`-derived context and
    through its PARENT yields the SAME node id (interning) but DIFFERENT handles, and fills from
    each yield different label sets — the discriminator against an implementation that hands
    `events2.Jet` its parent's handle and silently drops the newly registered universes;
    selection-scoped weight via `vary` on a derived context (parent unaffected) **and the derived
    context's ambient weight re-indexed to the derived row count** (§2.6c — **elementwise equality
    per label against a manually re-indexed reference, not length equality** (r12): length equality
    catches only the named failure of inheriting the parent's un-re-indexed members, while the
    adjacent and likelier bug — re-indexing every label's member by NOMINAL's mask, or by whichever
    label was iterated first — yields right-length, silently mis-weighted arrays whenever per-label
    counts coincide; the manually re-indexed reference is already in the test, so comparing values
    is free. The **varied-mask case (per-label row sets) is inside this anchor**, where a
    length-only check is weakest); `graphed.labels` on a context derived by a **Varied** mask
    (per-label row sets, §2.6c) — **asserted as §2.2's UNION on a program that registers a weight
    BEFORE the derivation** (r13), so the answer is ambient-weight labels ∪ the mask's labels in
    §2.4 order with `"nominal"` first, not the mask's labels alone — **plus a SECOND program that
    discriminates the third union term** (r14: in the weight-before-derivation program the varied
    collections' labels are a SUBSET of the mask's labels, since the mask is varied *because* the
    collection is, so an implementation computing ambient ∪ mask and dropping the collection term
    passes; the discriminating case is a shift-varied collection with an UNVARIED derivation mask,
    where the collection is the only source of the shift labels — assert `graphed.labels(ctx)` still
    reports them, and that it remains a superset of the context-borne half of a fill's label set,
    §2.2) — **plus a THIRD program that discriminates the union's THIRD TERM ITSELF, r21** (neither
    program above can: in the first the mask's labels are covered by term (a), in the second by term
    (b), so an implementation computing only (a) ∪ (b) passes both while term (c) is the one §2.2
    rebound in r20): a context derived by a mask varied through the LOOSE §2.1a primitive —
    `mask = gak.num(graphed.vary(events.Jet, "jes", up=j_up, down=j_dn)) >= 4`, `sel = events[mask]`,
    with NO weight registered and NO shift-form `vary` on the context — for which terms (a) and (b)
    are both EMPTY and `graphed.labels(sel)` MUST still report the JES labels.
    **§2.2's r20 half — that term (c) SKIPS OVER `vary` identity links — is knowingly left
    UNANCHORED, r21**, because no m48–m51-scoped program isolates it: on a `Varied`-mask-derived
    context every read through the context is `Varied` (§2.6c), so a weight registered onto it lands
    in term (a) carrying the mask's labels, and a shift-form `vary` on it stacks onto an
    already-`Varied` collection (§2.1) and lands them in term (b) — either way the answer is right
    under both readings. The clause stays binding for correctness of the verb, on §1.1's
    `"1e1000000000"` precedent; `graphed.universe(ctx, label)`/`graphed.nominal(ctx)` return a context that is a CHILD of
    the argument in the lineage chain (§2.2 r14), so a fill mixing it with a read from the argument
    unifies instead of diverging — **asserted over the resulting VALUE, not merely over the absence
    of the divergence error** (r15): the ancestor-context value is PROJECTED to that label per
    §6.1d's link-kind (3) and compared elementwise against a manually projected reference, so a
    guess that unifies but silently mis-weights cannot pass — the fixture is
    `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)`, **both axis values PER-EVENT for the reason
    §6.1d states, r19** (the r15–r18 `graphed.nominal(sel).Jet.pt` mixes a per-object with a
    per-event axis and cannot execute: bh requires equal flattened lengths across axes, measured
    `ValueError: spans must have compatible lengths`) — **and the RESULT SHAPE is asserted too, r21:
    that fill's output is a BARE `hist`** (§6.1a's unvaried shape), because §6.1d r21 computes the
    label set AFTER projection and the projected value carries none, while the unified context
    `graphed.nominal(sel)` contributes none either; without this the fixture has two defensible
    result shapes (`{label: hist}` with per-universe-identical contents being the other) and the
    test-author's pick is frozen read-only. It is also the discriminator against an implementation
    that keeps the labels and projects only the contents; **`unweighted=True` in §6.1d's r19
    bound form** — it suppresses the AMBIENT weight AND any explicit `weight=[…]` (a contexted fill
    with registrations yields counts equal to an unweighted eager reference) **AND, r23, the
    suppressed weight contributes NO LABELS: such a fill, whose only variation source is the ambient
    registry, returns a BARE `hist` (§6.1a), not a `{label: hist}` of per-universe-identical counts
    — the r19–r22 wording is satisfied by BOTH readings, so the result shape was a test-author's
    coin-flip frozen read-only, the same ambiguity r21 closed for the projection link one clause
    above; the bare shape is the discriminator against the labels-kept implementation**, and
    `fill(x, weight=[w], unweighted=True)` is a RECORD-TIME error naming both; data-context guard for
    **both** forms (`is_weight=True` AND a shift-form `vary`, §2.6d);
    lockstep `graphed.vary(events, name, Jet=…, MET=…)` shared-tag-set validation; §1.1 tag
    grammar (kwarg tags + `variations=` numeric-tag escape + every listed rejection); no
    reserved names on the context (a tree branch named `weights` or `vary` stays reachable —
    the collision that motivated r6); **the SLICE/INT context-subscript refusal** (§2.6a r16, given
    an anchor r17 — the refusal was binding, justified by `Array.__getitem__` accepting both
    (`python/graphed/array.py:344-371`), and unanchored: `events[0:1000]` and `events[0]` each raise
    naming the supported subscript forms, with the mask and string subscripts as positive controls); §2.2 `graphed.universe`/`labels`/`nominal` on both
    `Varied` and contexts, string getitem = field access. The §1.1 grammar anchor MUST cover the
    r9 e-canonicalization semantics **across all THREE tag channels** (§1.1 r15 — including the
    shift form's inner mapping keys, e.g. `Jet={"0.5": …}` → `murf_5em1`, plus a
    duplicate-after-canonicalization rejection INSIDE one collection mapping): float spellings
    accepted via `variations=`, via
    `**`-unpacking and via a collection mapping (channel-independent) and normalized by exact decimal arithmetic
    (`"2"`/`"2.0"`/`"2e0"`/`"20e-1"` → the ONE label `murf_2`; `"1e-8"` → `eps_1em8`; integer PDF
    indices untouched), **non-minimal canonical-grammar tags re-rendered** (`"50em2"` → `5em1`,
    §1.1 r11), the two readings of "`"0.5"` and hand-typed `"5em1"` unify" **split explicitly**
    (§1.1 r11 — a single "they unify" bullet is freezable either way): across TWO `vary` calls the
    spellings name the identical label `murf_5em1`; within ONE call they are a
    duplicate-after-canonicalization REJECTION, like `{"0.5", "0p5"}`. Plus cross-notation
    numeric-equal
    pairs rejected (`{"0.5", "0p5"}`, `{"2", "2p0"}`) **within one call AND across two stacking
    calls on the same `name`** (§1.1 r17's family definition: a family is one `name`'s tags on one
    container INCLUDING inherited labels, so `vary(ctx,"murf",w_nom,is_weight=True,
    variations={"0.5": a})` then the same call with `variations={"0p5": b}` is rejected — **the pair
    is spelled in the WEIGHT form (b), r23**: an event-context target with no `is_weight` is
    overload (c), in which `variations=` is REJECTED outright (§2.1), so the r17–r22 spelling
    `vary(ctx,"murf",variations={…})` would have frozen the WRONG rejection here — freezing only the
    within-one-call pairs
    pins the weaker reading), `inf`/`nan`/leading-`+`/underscore/
    whitespace spellings rejected, Python-float (non-string) tags rejected, negative zero
    canonicalizing to `0` (never `m0`) and a >32-character canonical tag rejected (§1.1 r10)
    **alongside the INTEGER-MAGNITUDE rejection as a distinct case** (r17 — §1.1 binds two
    rejections around the cap and freezing only the generic one lets an implementation emit the
    generic message for both and pass every anchor while violating the binding sentence, the shape
    r15 repaired for §6.1d's loose-value message): `"1e40"` (integer-valued, 41 plain digits) is
    rejected **at canonicalization with a message NAMING THE MAGNITUDE**, not with a generic
    tag-length error, alongside the existing `"1e-8"` → `eps_1em8` positive; **plus the CAP-BOUNDARY
    PAIR that pins r19's digit-count NORMALIZATION, r20** — `"1.5e31"` is ACCEPTED and yields the
    canonical 32-digit tag (`15` followed by 30 zeros, exactly at the cap) while `"1.5e32"`
    (33 plain digits) is REJECTED with the magnitude message **and its NEGATIVE twin `"-1.5e31"` is
    REJECTED with the canonical-tag-LENGTH message, r22** (r21 froze the SAME magnitude message
    here; §1.1's r22 split refuses by CAUSE — the magnitude message only when the INTEGER digit
    count alone exceeds the cap, and `"-1.5e31"`'s magnitude is the one the adjacent half of this
    very anchor certifies as LEGAL, so blaming it names the wrong property; the real cause is the
    `m` sign marker taking the rendered tag to 33 characters. Both VERDICTS are unchanged — the
    negative twin is still REJECTED and `"1.5e31"` still ACCEPTED — only the message class moves,
    and the two rejections stay distinguishable, which is what the anchor exists to freeze). The ACCEPTED half is the discriminating
    one: the naive "mantissa digits + exponent" the normalization exists to replace computes
    2 + 31 = 33 and rejects a legal tag, and `"1e40"` alone cannot catch that (the naive sum rejects
    it too, 1 + 40 = 41), so freezing only `"1e40"` leaves §1.1's normalization unwitnessed. (The
    r18/r19 "count BEFORE any rendering" rule is knowingly left UNANCHORED — its witness would be
    `"1e1000000000"`, whose failure mode under a render-then-measure implementation is a hang/OOM,
    not a clean red.) The
    **FOUR signature-shadowed names** (`nominal`/`is_weight`/`variations`/`collections` reachable
    only through `variations=` / `collections=` — including `collections`' own self-reference,
    §2.1 r11 — and `variations=` refused in the shift form, **plus `nominal=` refused in the shift
    form with an error naming `collections=`**, §2.1 r17; **the tag `nominal` is LEGAL and yields
    the ordinary label `pu_nominal`, and there is NO "label equals `nominal`" rejection to freeze**,
    §1.1 r16: every label contains a `_` by construction, so that rejection was unconstructible),
    and no
    label ever containing `.`/`-` — freezing an earlier revision's rejections would hard-block this
    grammar (review-sweep finding).
- **m49 — shift path + impact + executor end-to-end** (repos: `graphed` + **`graphed-histogram`** +
  `graphed-executors`; r13 — r12 moved m49's headline matrix into `graphed-histogram`, anchor (i)
  below, but left the repo list and §10's directory pins behind. The list is what the DoD's
  full-matrix-CI-green-at-the-pinned-revision (R0.5) and per-repo freeze tagging key on, so a
  milestone whose headline gate lives in an unlisted repo could be declared DONE with that repo's CI
  unexamined).
  Targets: §3.3, §3.4 (frozen anchor), §5, §7, **§8 — EXCEPT §8.2(i)'s `variation_labels` FIELD
  DECLARATION, which lands at m48 with §7.2's (β) return channel; m49 adds the core accessor, the
  keying and the POPULATION (r23)**, **plus §2.5's shift-after-weight diagnostic**
  (r18 — §2.5 itself calls it an m49 target and m49's anchor list freezes it, while it appeared in no
  milestone's target line; the DoD scopes an implementer off the target line), **plus §9.1's
  per-label projection-stats verb (§5.3; spelling pinned at m49 freeze) and §7.2's `aggregate_plan`
  seam half (β)** (r20 — §9.1 marks the stats verb m49 and m49's §5.3 anchor reads through it, while
  it appeared on no target line: the same defect r13 fixed for m48's §9 verbs and r18 for m51's;
  (β) is the per-plan variation-metadata half of the m48 seam, whose only consumer is §8.2(i)'s
  `variation_labels`, anchored below). Frozen anchors:
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
    `graphed-histogram` in any extra (`pyproject.toml:42-48` — `dev` carries
    `boost-histogram>=1.4`/`hist>=2.7` only) while CI installs `.[dev]`
    (`.github/workflows/ci.yml:34,57,143`), and the house pattern there is
    `pytest.importorskip("graphed_histogram")` (`tests/frozen/preserve/m30/test_producer_cross_seam.py:155`),
    so a fill-based matrix in `graphed` would SKIP in CI — silently discharging m49's headline gate
    AND its single-read mechanism witness, with zero frozen-suite diff coverage. After m48,
    `graphed-histogram` already carries the corpus dep and the vendored references (m48's bound
    dependency edit), so it can host this half without a new fixture problem.
    **The per-repo partition covers EVERY m49 anchor, not only (i) and (ii)** (r14 — r13 assigned
    two and left the rest to default, which lands fill-shaped anchors in a repo measured unable to
    host them and checkpoint anchors in a directory §10 never pinned): `tests/frozen/frontend/m49` in
    `graphed` keeps m49's NON-fill frontend anchors (§5.2a arena delta,
    §5.2c stage shape, §3.4 impact sets, §5.3 projection, §5.4 refusal) and `graphed`'s
    `tests/frozen/core/m49` keeps the §3.3 benchmark (**not** `frontend/m49` — r14; §10's header pins
    it to `core/m49` and §3.3 says the same, and the unique-basename rule is written for that
    one-process subtree). `graphed-histogram`'s flat `tests/frozen/m49` additionally keeps the
    §2.4/§6.1b structural arity anchor (its operands are `Histogram.staged_fills`/`fill_nodes`,
    `graphed-histogram src/graphed_histogram/boost.py:215-219`, and `graphed` lists no
    `graphed-histogram` in any extra, so placed there it would `importorskip`-SKIP). `graphed` gains
    **`tests/frozen/checkpoint/m49`** for §7.3 interrupt/resume and §7.4 dead-letter (the machinery is
    `graphed`'s checkpoint package; `tests/frozen/checkpoint` today holds only `m8`/`m39`, so the
    directory is new and falls under the unique-basename rule — `m8/test_resume.py` already exists).
    §8.1's `__hash__` anchor and §8.2's cross-process/multi-label anchors live in
    `graphed-executors`' flat `tests/frozen/m49` except the §8.2(i) accessor anchor, which is
    explicitly `graphed`'s (below); `graphed` CAN host a spawn-based cross-process test if the
    test-author prefers (`tests/frozen/debug/m6/test_process_boundary.py:16`).
    **The two remaining m49 anchors are assigned explicitly** (r15 — r14 said the partition covers
    EVERY anchor while the m05 ordering witness and the JER-SF stochastic fixture appeared in none of
    the lists, and placement is load-bearing here for the same measured reason as the matrix: a
    fill-based anchor placed in `graphed` `importorskip`-SKIPs in CI): the **m05 ordering witness**
    is histogram-observable and goes to `graphed-histogram`'s flat `tests/frozen/m49` alongside the
    matrix it scopes; the **JER-SF stochastic fixture** goes there too, since its partition-
    invariance witness needs a plan run at two `steps_per_file` values. **The comparison quantities
    (§5.5a r15) are produced by a PLAN RUN — per-partition values concatenated in task order — and
    `Session.materialize` MUST NOT be the oracle** (r16 — r15's "materialized through the same
    Session" is a partition-BLIND API: measured, `materialize(self, array)` evaluates the whole graph
    in one shot and takes no partition and no `steps_per_file`,
    `python/graphed/session.py:291-301`, so quantities obtained that way are byte-identical across
    any partitioning BY CONSTRUCTION and the witness cannot observe `steps_per_file` at all — the
    per-partition `np.random.default_rng(0)` failure r13 added this witness to catch survives it
    together with the other four witnesses r13 already showed cannot discriminate it. The
    deterministic route exists: `SequentialRunner` folds tasks in SORTED key order
    (`python/graphed/core/execution.py:450-457`), so an `aggregate_plan` whose reduce returns
    partition-local arrays and whose combine concatenates is order-deterministic).
    (ii) **`graphed-executors`, flat `tests/frozen/m49`** — the same matrix through a process-pool
    executor (the `graphed` repo ships no `Executor` implementation — the executors live in
    `graphed-executors`; `graphed`'s only cross-process frozen test is the M6 error-transport pool,
    `tests/frozen/debug/m6/test_process_boundary.py:16`). Two fixture facts bind the shape:
    the 15 stored references are NOT reachable from the `graphed-corpus` wheel (it packages only
    `src/graphed_corpus`, `pyproject.toml:28-30`, while the reference JSONs live in the repo
    directory `corpus/references/`), and `graphed-histogram` is **not** a dependency of
    `graphed-executors` (`pyproject.toml:20-35`; no `histogram` hit in its pyproject or workflows).
    Because this half must exercise §4.2/§6.1's varied-fill lowering — the whole point of a
    weight-variation matrix — **m49 adds `graphed-histogram` to `graphed-executors`' `dev` extra
    AND binds the install pair, exactly as m48 does for the corpus** (r14 — a name-only dev-extra
    entry is the mechanism r13 measured to be insufficient in this org: `graphed-histogram` IS on
    PyPI (verified in-session: `pypi.org/pypi/graphed-histogram/json` → name `graphed-histogram`,
    version `0.0.1`, homepage `github.com/graphed-org/graphed-histogram`), and the repo's own version
    is also `0.0.1`, so the name resolves to a release that predates m48's varied-fill work and is
    not even distinguishable by version. `graphed-executors`' workflow pre-installs only `GRAPHED`
    and `CORPUS` from git URLs — `.github/workflows/ci.yml:13,15,17`, installed at `:38`, `:65`, `:94`,
    `:136` — and nothing pulls `graphed-histogram` from HEAD): m49 adds a **`HISTOGRAM` git-URL
    workflow env var plus its `pip install` line in every job that runs `tests/frozen`**
    (`ci.yml:38,65,94,136`) alongside the dev-extra name. **This anchor MUST NOT be guarded by
    `importorskip`** either (r14 — anchor (i) and m48's matrix carry that clause and (ii) did not,
    leaving the headline executor-level systematics gate silently skippable).
    It compares against corpus references recomputed in-process via `graphed_corpus` (the m7 house
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
    subset of another's — the non-monotone discriminator); the shared random-draw node
    interned ONCE across all universes (mechanism witness, §5.5b); **and PARTITION INVARIANCE — the
    identical event set run at two different `steps_per_file` values yields byte-identical per-label
    SMEARED VALUES and selection MASKS** (r13; the compared quantity narrowed in r15 — a weighted
    float histogram is NOT byte-invariant under a re-partitioning even for a correct implementation,
    since the combine tree regroups the float additions, §5.5a; the other four witnesses cannot discriminate the failure §5.5(a) actually
    forbids: a constant-seeded `np.random.default_rng(0)` per partition is reproducible, migrates
    both ways and still interns as one draw node, so it passes all four while giving the same event
    a different smear under a different partitioning — a data-dependent nondeterminism the
    determinism gate, which holds partitioning fixed, never sees. Deterministic invariant, R0.10a-safe).
  - §5.2 witnesses (a: arena delta vs an independently hand-built oracle; c: reduced-stage shape
    vs the same-topology no-`vary` ORACLE, r16 — not a frozen literal and with NO post-freeze
    re-measurement clause, §5.2c).
  - **§2.5 shift-after-weight diagnostic** (§2.1/§2.5 r16, using §3.4 which lands here): a weight
    factor registered BEFORE the `vary` that replaces a collection its cone reaches is reported,
    naming both; the positive control is the correct order (weight registered after the shift),
    which reports nothing.
  - §3.4 impact-set anchor: three labels where two share a derived node — the shared node appears
    in both impact sets; result independent of expansion order. **The FIXTURE is stated, r23,
    corrected r24** (the same mid-freeze-discovery service m48 gives `gak.full_like`, `stable()`
    rounding, `h.axes.name` and the pt-cut jets): the sharing must be UPSTREAM of the fork — the two
    varied members have DIFFERENT expressions that both consume ONE derived node the nominal member
    does not use. **A node DOWNSTREAM of the fork can never be shared by two labels with distinct
    members**, since interning keys on input ids (`src/store.rs:73-88`; measured, `a = src * 2.0;
    b = src * 2.0` → `a.node_id == b.node_id == 1`, `session.node_count() == 2`) — that is the true,
    narrower statement; **r23's "exactly one construction exists … the naive fixture does not exist
    at all" is WITHDRAWN as measurably false** (measured r24 against `graphed-latest@ff7c607` on a
    raw `GraphStore`: `src`; `k = add_op("scale",[src])`; `nom = add_op("sel",[src])`;
    `up = add_op("shift",[src,k],{"d":"up"})`; `dn = add_op("shift",[src,k],{"d":"dn"})` →
    `impact(up) = [1,3]`, `impact(dn) = [1,4]`, shared-non-nominal `= [1] = k`, with members `3 ≠ 4`
    structurally different). Assert all three: `u ∈ impact(up) ∩ impact(down)`,
    `u ∉ reachable(nominal)`, **and `impact(up) ≠ impact(down)`** — the last conjunct is what r23's
    identical-member form (`vary(x, "jes", up=e, down=e)`, which belongs in m48's §1.2 dedup anchor
    where it already lives) cannot carry, since there the two impact sets coincide and "appears in
    BOTH" is satisfied by returning one set twice or by unioning. The id-WATERMARK implementation
    §3.4 rejects is still red on this fixture (it hands the second label an impact set missing `u`).
    **This is the same construction §8.2(i)'s m49 anchor already builds** ("one derived node
    consumed by TWO NON-nominal universes"), so the two anchors MAY share one fixture.
  - §2.4/§6.1b structural no-cross-product count — **in SIBLING mode** — `1 + |S| + |W|` fill
    nodes (axis mode's `1 + |S|` is m50, §6.2; word the anchor so it does not freeze a general rule
    m50 must contradict — r12 applies to this line the scoping r11 gave the m48 §6.1a anchor and
    §6.1b's own prose).
  - §5.3 projection-union test — **including the per-label projection stats** reporting the shifted
    label's extra column (§5.3 r12; the union-growth assertion alone leaves the stats surface
    unanchored), **read through the §9.1 verb whose shape §5.3 r16 pins**
    (`{label: tuple[str, ...] | None}`, sorted per label; spelling pinned at m49 freeze) — **with a
    CONSERVATIVE label in the same fixture** (r17: one gak op applied directly to the source, for
    which `read_columns` returns `None` = "read every column", `projection.py:145-146`), asserting
    that label maps to `None` and not to `()` — **the conservative label riding a SEPARATE program
    (or a separate output set) in the same test module, r22**: measured,
    `read_columns` carries ONE `conservative` flag across all the arrays passed and returns `None`
    if any one of them consumes the whole record (`python/graphed/projection.py:130-146`), so a
    conservative label inside the SAME varied program collapses the union to `None` and the
    union-growth half degenerates to `None == None` (vacuous) or goes red against a correct
    implementation. Equivalently, state the growth half per label through the stats verb
    (`stats[jes_up] == stats[nominal] + ("Jet.eta",)`), which is immune to the interaction;
    §5.4 refusal + positive control.
  - §3.3 NEW frozen variation benchmark file (exact `stages == N+1`, `reduced == 2N+2`, linear
    bound).
  - **§8.2(i) accessor + keying, in `graphed`** — **directories named in r24, since §10 pins one for
    every other m49 anchor and this bullet straddles two homes: the accessor half in
    `tests/frozen/frontend/m49` (a `compile_ir`-shaped program) and the plan-byte determinism half
    in `tests/frozen/checkpoint/m49` beside §7.3, whose module-level-`DurablePlan`-by-value
    construction it shares verbatim; both under the unique-basename rule. Placement is mechanically
    load-bearing: `frontend` runs one pytest process per milestone subdir while `core`/`checkpoint`
    run one per package (`graphed scripts/run-tests.sh:16` `SUITES`, `:30` `SPLIT_PKGS="frontend
    numpy awkward"`), and that scope is what the basename rule is keyed on** (r13 — the new read-only core accessor is an m49
    Implementation Target in `graphed`, yet every anchor exercising it sat in `graphed-executors`,
    so it risked landing uncovered in the repo it lives in while the DoD requires ≥90% diff coverage
    from THAT repo's frozen suite; its own correctness is also never asserted directly): over the
    §3.3 builder topology — **built through the frontend `compile_ir` path, since that is the key
    space the accessor answers in, and EXTENDED with one deliberately unmarked branch** (r15: §3.3's
    builder marks every universe's terminating reduction as an output, so nothing in that topology is
    dead and the DCE clause below has no operand) — every surviving record id maps to a
    `(reduced_id, member_index)` whose
    reduced id **is a node id of the compiled reduced store** (r19 — "in the compiled output/stage
    set" is false for the SOURCE record, whose reduced node is measured to be neither an output nor
    a stage: reduced kinds on this topology are `{source: 1, stage: N+1, reduction: N}`), the
    unmarked branch's record id maps to `None`, and
    — **on a topology EXTENDED a second way, r16: one derived node consumed by TWO NON-nominal
    universes** — that node maps to ONE `(reduced_id, member_index)` key **whose `variation_labels`
    entry carries BOTH labels** (the PAIR key space §8.2(i) declares, r17). That extension is what makes the clause non-vacuous: §3.3's builder gives each universe
    its own fork + K chain ops + terminating reduction off a shared prefix, so no node is shared by
    two labels in §3.4's sense ("shared by `jes_up` and `jes_down` but not nominal") — prefix nodes
    are shared by ALL labels including nominal — and "two labels' shared node maps to ONE reduced id"
    degenerates to "the map is a function", which it is by type. The extended form is the actual
    non-vacuity witness for §8.2's SET-VALUED keying claim (the same repair r15 gave the DCE clause).
    **Plus a PARTITIONING clause the §3.3 topology makes exact, r18** (without it every clause above
    is satisfied by a degenerate constant map `record_id -> (one_stage_id, 0)`: (1) "maps into the
    output/stage set" holds trivially, (2) the `None` for the unmarked branch is DCE reachability the
    implementation computes anyway, and (3) "one key carrying BOTH labels" holds *a fortiori*, since
    one key then collects every label — while the real discriminator, the executors' single-label
    `variation == "jes_up"` anchor, lives in another repo, which is the per-repo-coverage argument
    that motivated adding this anchor at all): the shared-prefix record ids all map to ONE reduced
    id, each universe's chain maps to a reduced id DISTINCT from every other universe's, and the
    map's image over the WHOLE topology has exactly **2N + 2** distinct reduced ids, of which
    exactly **N + 1** are of kind `stage` — matching the `reduced_nodes == 2N + 2` / `stages ==
    N + 1` shape §3.3 already pins. **The r18 "exactly N + 1 distinct reduced ids" is CORRECTED
    here, r19**: the accessor is bound over EVERY surviving record id, which on this topology
    includes the source and each universe's terminating reduction — neither of which is a stage —
    so a frozen `len({rid for rid, _ in m.values()}) == N + 1` reds a correct accessor by ~2×.
    Re-measured r19 against `graphed-latest@ff7c607` on the §3.3 builder: N=3 → stages 4 /
    reduced_nodes 8 / kinds `{source: 1, stage: 4, reduction: 3}`; N=16 → 17 / 34 /
    `{source: 1, stage: 17, reduction: 16}`; N=128 → 129 / 258 /
    `{source: 1, stage: 129, reduction: 128}`. Both halves stay non-degenerate against the constant
    map the clause exists to catch, since it fails the per-universe-distinctness half.
    **The cardinality clause is asserted on the BASE fixture (± the unmarked dead branch) ONLY, and
    NOT on the shared-node extension, r20** (the anchor names two extensions of one topology and
    "the map's image over the WHOLE topology" reads as "all record ids"; a test-author who
    economically builds ONE fixture carrying both extensions freezes a literal a CORRECT accessor
    fails): measured this session against `graphed-latest@ff7c607` on this builder (D=20, K=5, every
    universe's reduction marked), the dead branch changes nothing — DCE removes it — N=3 → reduced 8
    / `{source: 1, stage: 4, reduction: 3}`, N=16 → 34 / `{1, 17, 16}`, i.e. `2N + 2` / `N + 1`
    stages either way, while adding one derived node consumed by TWO non-nominal universes gives
    N=3 → 9 / `{source: 1, stage: 5, reduction: 3}` and N=16 → 35 / `{1, 18, 16}`, i.e. `2N + 3` /
    `N + 2`. The shared-node fixture carries the BOTH-labels clause; the cardinality literals stay
    with the base one.
    Plus **plan-byte determinism with the §8.2(i) field present** — the field reaches the shipped
    closure through §7.2's seam half (β), so this anchor is also (β)'s frozen coverage (r20): the same
    varied program built in two fresh processes under differing `PYTHONHASHSEED` yields
    byte-identical `DurablePlan.to_bytes()` and identical per-partition `task_id` (the plan-level
    twin of §3.2's IR-level m48 anchor; measured basis for why it is needed: a `frozenset` field
    pickles in hash order — three distinct digests across three seeds, §8.2(i)).
    **The fixture's plan construction is part of the anchor, r18, because both halves are
    load-bearing** (§7.3): the `DurablePlan` is built BY VALUE over the plan `aggregate_plan`
    returned — `DurablePlan(ir=…, process=OpSpec.from_callable(plan.process), …)`, never
    `OpSpec.from_ref`, since `identity()` for `kind="ref"` is `b"ref\0" + ref`
    (`python/graphed/core/plan.py:72-76`) and would keep the closure's fields out of the plan bytes
    entirely, freezing this anchor GREEN against the very `frozenset` §8.2(i) bans — **and every
    closure operand (the `PartitionedSource`, reduce/combine/empty) is a MODULE-LEVEL definition in
    an importable module**, since a by-value-pickled `__main__` class makes the plan bytes
    seed-dependent regardless of `variation_labels` and would make the anchor red against a correct
    implementation (re-measured r21, cloudpickle 3.1.2 / CPython 3.12.10, `PYTHONHASHSEED` ∈
    {1, 7, 12345}: importable dataclass + sorted tuple → ONE digest ×3; + `frozenset` → 3 distinct;
    `__main__`-defined dataclass + sorted tuple → 3 distinct. The r18–r20 literal
    `80e8024dc8f3b77d` is withdrawn — it named no module/class/field names and so is not
    re-runnable, §7.3 r21; the qualitative shape is what binds here).
  - §8.2 cross-process labeled StageError (incl. §7.4 dead-letter label) **plus the shared-node
    multi-label RENDERING half** (r14 — §8.2 states it inline as a required m49 anchor and this
    skeleton list dropped it; without it the single-label anchor passes under a
    pick-one-arbitrarily implementation and the defect survives the freeze); §7.3 interrupt/resume
    byte-identity **over a `DurablePlan` built by value exactly as the §8.2(i) anchor above builds
    it** (r18 — §7.3 previously delegated the choice to "the anchor states which" and this bullet
    stated nothing; under `OpSpec.from_ref` the `process` would be a hand-written module-level
    callable over a hand-built IR, exercising no varied lowering at all). **Plus §8.1's `__hash__` participation explicitly** (r11): `__eq__` compares
    `self.__dict__` so a new field participates for free, but `__hash__` is a hand-written tuple
    that must be edited (`python/graphed/debug/errors.py:75-78` vs `:80-81`) — assert two
    `StageError`s differing ONLY in `variation` are unequal **AND hash differently**, or the
    omission is invisible to the cross-process label anchor.
- **m50 — scale + integration** (repos: `graphed-histogram` + `graphed` preserve/docs).
  Targets: §6.2, **§6.1c's AXIS-MODE slot** (r16 — the `(output, None)` keying and the per-slot
  spec taken from the fill node; **r19: "the per-OUTPUT MODE recorded in the layout" is DELETED
  here**, §6.1c having dropped the field — the three slot key forms are disjoint and per output, so
  the unpacker reads the shape off the keys and no anchor in m48–m51 could witness a MODE field;
  m50's scaling anchor
  consumes exactly this and m50's target line did not name it. **r18: "the per-slot value type in
  the layout and the combine's branch on it" is DELETED here** — r17 withdrew that design in §6.1c
  ("The COMBINE needs no branch"; `_add_groups` is a key-wise `+`, `graphed-histogram
  src/graphed_histogram/boost.py:120-122`) while this target line still directed the test-author and
  implementer to build and freeze around it), **§9.1's `graphed.variations`** (the rest of §9.1 is an m48
  target, r13) **plus §9.1's plan-level `{output: [labels]}` listing** (r16, own anchor below) +
  §9.2. Frozen anchors:
  - Variation-axis fill equals sibling-fill results bin-for-bin on the corpus **weight** labels,
    AND a mixed shift+weight program lands in ONE axis-mode histogram equal to its sibling-fill
    decomposition (§6.2, scalar-labeled shift siblings); combine-safety across partitions
    (identical spec, deterministic label order). **The mixed program carries a label borne ONLY by a
    `Varied` `sample=`, r20** (§6.1b's `S`/`W`-by-lowering definitions are binding and this is the
    only place they are witnessable: sibling arity `1 + |S| + |W|` counts every label once whatever
    its class, so m49's arity anchor is green under either reading, while axis mode's `1 + |S|`
    counts `S` and collapses `W`): that label must lower as a SIBLING — it counts in `S`, since the
    evaluator's weight loop re-fills with different weights against a FIXED sample column — and the
    axis-mode result still equals its sibling-fill decomposition. Without it an implementation
    classing a sample-only label into `W` passes every m48–m49 anchor and silently produces one
    sample column reused across universes. **The fixture MUST use a `Mean`/`WeightedMean` storage
    and per-label sample values that DIFFER (§6.1b r21)** — measured, bh 1.8.0 raises
    `TypeError: Keyword(s) sample not expected` for `sample=` on `Double()` and `Weight()`, and the
    evaluator passes `sample` straight to `h.fill`
    (`graphed-histogram src/graphed_histogram/boost.py:60-71`), so a default-storage fixture dies at
    evaluation against a correct implementation and a sample-discarding storage makes the equality
    vacuous. **Plus the per-fill CARRIER witness** (§6.2 r15):
    in the mixed program the `1 + |S|` axis-mode fill nodes carry **distinct External
    `content_hash`es and resolve to distinct evaluators** — without it every sibling resolves to the
    one evaluator registered last (measured: the registry is keyed on `content_hash(self._spec)`
    alone and merged across histograms, `graphed-histogram src/graphed_histogram/boost.py:180-212,
    283-286`; `evaluate_ir` dispatches by `nd["descriptor"]["content_hash"]`,
    `graphed python/graphed/execute.py:116-124`), which the bin-for-bin equality can mask whenever
    two siblings happen to agree.
  - **MIXED-MODE PLAN — mixed-mode UNPACKING and the per-slot SPEC (r18; re-headlined r19)**: one
    `plan(...)` call carrying an axis-mode output AND a sibling-mode varied output together, plus a
    third output no variation reaches. **What it witnesses is the unpacking and the per-slot spec,
    NOT a per-output MODE field** (r19 — r18 headlined it "the per-OUTPUT MODE's only reason to
    exist", which it measurably is not: §6.1a/§6.1c make the three slot key forms disjoint and per
    OUTPUT, so an implementation that never records a MODE passes every assertion here exactly as it
    passes the single-mode ones; §6.1c has accordingly dropped the field, and §9.1's one-argument
    `unpack(value)` is consistent again). Every other m50 anchor is single-mode (the equality anchor
    compares two separate programs, the scaling anchor pins the fixture's output count at 1, (i-bis)
    is one axis-mode histogram, the declaration/mode-mismatch anchors concern one histogram), so
    this is the only program that reaches the mixed unpack at all. Assert:
    the axis-mode output unpacks to a BARE variation-axis histogram, the sibling-mode output to
    `{label: hist}`, the unvaried output to a BARE `hist` under its bare key (§6.1a), all narrow
    through `graphed.labels`/`graphed.universe`, and all are
    bin-for-bin correct. **Plus a FOURTH output — axis-mode opt-in, NO variations — asserting its
    slot key is `(output, None)` and that it unpacks to a bare histogram carrying a 1-bin variation
    axis (r23)**: §6.1a/§6.1c's r22 rule that the MODE, not the variation count, decides an
    axis-mode key is directly witnessable (these anchors assert the plan value's KEY SET) but was
    covered by no program — the three outputs above give the unvaried one a BARE key, i.e.
    sibling-mode, so an implementation keying an unvaried axis-mode output bare passed every
    m48–m51 anchor while contradicting the rule. Cost: one histogram in an existing fixture.
    **That same histogram carries §6.1c's r24 axis-mode arm, one line: `.plan()` on it RAISES the
    §6.1c refusal naming the group API** — it is unvaried, so m48's varied-only trigger would let
    it through into an opaque `ValueError: axes have different length` from `_SumFills`'
    `__init__`-time spec (measured, bh 1.8.0; `boost.py:244-253,146-150` — `_SumFills(self._spec)`
    at `:246`, `self._spec = spec_of(self)` at `:148`).
    (It also exercises `_GroupZero`'s per-slot spec across two DIFFERENT specs —
    `graphed-histogram src/graphed_histogram/boost.py:127-130` — which nothing else in m48–m51
    reaches.)
  - **§6.2 declaration contract** (r11 — the only behaviour §6.2 MEASURED to be silent had no
    anchor; **rescoped in r12 to the frontend-declared-only rule §6.2(ii) now binds**, because the
    r11 anchors froze user-declaration behaviour that §6.2 left optional AND that today's
    `Histogram.fill` cannot accept — it requires one array per axis,
    `graphed-histogram src/graphed_histogram/boost.py:160-161`): the declared bin set equals the
    §6.1d inferred label set EXACTLY — **two assertions, because one direction is invisible to the
    flow check** (r13): `h.sum(flow=True) == h.sum()` catches an UNDER-declaration (measured, bh
    1.7.2 and 1.8.0: filling three labels into a two-bin declaration gives `sum 2.0` vs
    `sum(flow=True) 3.0`), while an OVER-declaration — a declared bin no fill reaches — passes it
    unchanged (measured, bh 1.8.0: four declared bins, three labels filled, `sum ==
    sum(flow=True) == 3.0`), so the closing half asserts the axis's bin tuple against a LITERALLY
    spelled expected label list, never one read back from the histogram or from
    `graphed.labels(h)` (which §6.2(i-bis) DERIVES FROM the axis bin set — so the comparison is
    circular on CONTENT regardless of order; r18 corrects the r11–r17 parenthetical "defines AS the
    axis bin set", stale since r17 re-ordered `graphed.labels(h)` to §2.2's rule, which a
    test-author could read as making the comparison non-circular); a second fill whose
    inferred label set differs from the first's is a hard error naming the mismatch (§6.2 i,
    cross-fill agreement); **plus the MODE-mismatch error** (§6.2(i) r17: a second fill into the
    same histogram in the OTHER mode — first fill axis-mode, second sibling-mode — is a hard error
    naming both, since a mixed histogram yields both §6.1c key forms for one output and two
    contradictory result shapes); **and a user-constructed histogram that already carries a `"variation"`
    axis is refused with an error pointing at the opt-in mode** (user-declared axes are §11) —
    **with the RECOGNITION RULE and the fixture spelling bound, r16**: recognition is
    `axis.__dict__.get("name") == "variation"` (the §6.2(i-bis) name carrier;
    `graphed-histogram src/graphed_histogram/_spec.py:31-37,81-84` round-trips it), the fixture sets
    the name that way because `bh.axis.StrCategory(..., name="variation")` is itself a `TypeError`
    (measured, boost_histogram 1.7.2 and 1.8.0, §6.2 i-bis), and a user `StrCategory` under ANY
    OTHER name is untouched — the frontend still appends its own variation axis. Without the rule
    the plausible alternative ("any `StrCategory` axis") would refuse a legitimate user category
    axis (a region axis) and freeze that refusal read-only. The
    r11 "undeclared label at fill" and "unsorted user-supplied bin order" anchors are DELETED —
    under frontend declaration neither state is reachable.
  - **§6.2(i-bis) axis-mode result shape**: an axis-mode varied output is a BARE histogram
    carrying the variation axis (name in `axis.__dict__["name"]`, §6.2(i-bis) — **the name is read
    per axis, and `h.axes.name` MUST NOT be the oracle**: `bh` maps that attribute over EVERY axis
    and raises when one lacks it, so on any real axis-mode histogram, which has ≥1 value axis
    alongside the variation axis, it is an `AttributeError` against a CORRECT implementation
    (measured, bh 1.8.0, r13; the surviving invariant is that the name round-trips
    `spec_of`→`zero_of`, `[a.__dict__.get("name") for a in z.axes] == [None, "variation"]`)), and
    `graphed.labels(h)` (**and `graphed.nominal(h)`, r24 — §2.2 binds it to
    `graphed.universe(h, "nominal")` on this shape, i.e. the nominal SLICE, not the whole histogram;
    same manually-sliced oracle, one extra assertion**) returns the axis bin set
    **re-ordered to §2.2's rule — `"nominal"` first,
    then the remaining bins in axis order — while the stored bin order stays lexicographic**
    (§6.2(i-bis) r17; assert both, since a family whose lexicographic first bin is not `"nominal"`
    is the discriminating case) and NOT
    `["nominal"]`, while `graphed.universe(h, label)` returns that label's slice along it
    — the narrowing helper uniform over all three shapes (§6.1a bare-unvaried, `{label: hist}`,
    bare-axis-mode). **Worded over SEMANTICS, not over a literal subscript expression** (r12): the
    oracle is equality against a manually sliced reference, because
    `h[{"variation": label}]` raises on a bare `bh.Histogram` — measured on boost_histogram 1.7.2
    AND 1.8.0, `TypeError: list indices must be integers or slices, not str` (and
    `StrCategory(..., name=...)` is itself a `TypeError`); only the positional
    `h[{axis_index: bh.loc(label)}]` works.
  - The §6.2 scaling claim frozen **structurally** (R0.10a: no wall-clock in frozen tests): per
    partition, axis mode ships **1 combine payload entry** vs `N+1` in sibling mode — the length of
    the per-partition combine payload under §6.1c's key shape: one entry per `(output, label)` in
    sibling mode, ONE entry `(output, None)` in axis mode (§6.1c r15), with the fixture's output
    count pinned at 1 **and the fixture scoped to WEIGHT labels only** (r15 — under a mixed
    shift+weight program the axis-mode side still records `1 + |S|` fill nodes, and the 1-vs-`N+1`
    count is only unambiguous when every label collapses into the evaluator loop; the mixed program
    is frozen by the adjacent equality anchor, which does not count slots) (r14 — the r13 wording pointed at
    `_GroupReduce.__call__`'s returned `{label: histogram}` mapping, whose key TODAY is the OUTPUT
    name, not a variation label: measured, `layout = tuple((label, len(h._fill_nodes), h._spec) for
    label, h in items)` over `(output_name, Histogram)` pairs,
    `graphed-histogram src/graphed_histogram/boost.py:256-295,100-117`; the 1-vs-`N+1` count only
    holds once §6.1c's two-level `{(output, label): hist}` shape exists) — plus
    bin-for-bin equality. **The r12 "allocates 1 histogram object" half is DROPPED from the frozen
    anchor** (r13): counting allocations needs monkeypatched production code or a `gc`/`tracemalloc`
    heuristic, neither bound anywhere here and both fragile across the §A.5 matrix; the object-count
    claim goes to the R0.11 implementer report alongside the wall-clock half. The N≈100 wall-clock sibling-vs-axis comparison is an
    **implementer-report measurement under R0.11** (methodology stated: what is warmed, timed,
    held constant) — NOT a frozen gate.
  - §9.2 one-bundle-N-labels preservation (m9 comparison form, on the r10-bound varied
    `build_bundle`/`reproduce` surface — with the backward-compat control that an unvaried bundle
    still returns a BARE array) + `inspect()` label listing (§9.1).
  - **§9.1's plan-level `{output: [labels]}` listing, its OWN anchor** (r16 — it was anchored
    "inside m50's `inspect()` test", which takes a `Bundle` and returns a `str`,
    `python/graphed/preserve/bundle.py:268-288`, and cannot exercise a plan-level mapping): **in
    `graphed-histogram`'s flat `tests/frozen/m50`, NOT in `graphed`** (r17 — the anchor is
    fill-shaped: a named OUTPUT exists only in `graphed-histogram`'s group API
    (`plan(histograms: Mapping[str, Histogram] | Sequence[Histogram])`, `items = [(str(k), v) …]`,
    `graphed-histogram src/graphed_histogram/boost.py:256-295`), while `graphed`'s own
    `aggregate_plan(*outputs: Array, …)` carries no output names at all
    (`python/graphed/aggregate.py:68-107`), and the anchor's own wording leans on §6.1a's bare-`hist`
    rule; placed in `graphed`'s `tests/frozen/preserve/m50` its fixture needs `graphed_histogram`,
    which `graphed` declares in no extra (`pyproject.toml:29-48` vs CI's `.[dev]`,
    `.github/workflows/ci.yml:34`), so the house `pytest.importorskip` pattern
    (`tests/frozen/preserve/m25/test_histogram_preservation.py:31`) would SKIP it in CI — the
    silently-discharged-target shape r16 fixed twice elsewhere), over a TWO-output varied program — one output reached
    by variations, one not — the listing maps each output to its labels in §2.4 order, and the
    unvaried output maps to **`["nominal"]`** (r17 — r16 left "the empty/`["nominal"]` shape" as an
    either/or, and `[]` and `["nominal"]` are different frozen assertions that §6.1a does not settle,
    since it fixes the HISTOGRAM shape, not the listing's; `["nominal"]` is the consistent choice
    because §6.1a already binds a bare `hist` to READ as the single label `"nominal"` through the
    narrowing helper).
  - **§9.1 `graphed.variations(ctx)`** (no anchor before r10, and load-bearing because §6.2
    explicitly refuses to give numeric ordering from bin index): per-name tags and kinds — **over
    §9.1's r24 shape `{name: {tag: (kind, value | None)}}` with the two-word kind vocabulary
    `"weight"`/`"shift"`, so the fixture registers ONE of each and asserts both strings** — plus the
    parsed float value under **both** parsers — canonical e-form `m?\d+(em\d+)?` (`5em1` → 0.5,
    `m15em1` → −1.5) and datacard p-form `m?\d+(p\d+)?` (`2p5` → 2.5) — and a non-numeric tag
    (`up`) returning no value rather than raising.
  - Docs: a "How variations work" design.rst section with **executed** examples (the docs-sweep
    rule) covering §7.3's limitations explicitly — **all three invalidation classes, each with the
    scope §7.3 binds** (r17): the IR-level one (adding/removing a variation) is unconditional, while
    the label-RENAME class and **m48's** one-time closure churn (**milestone corrected in r22**:
    §7.2's (β) return channel puts §8.2(i)'s field on `_PartitionReduce` at m48 and adding it is
    what changes the pickled state — measured, one defaulted field flips the cloudpickle digest,
    §7.3 r22 — while m49 only POPULATES it; freezing "m49's one-time closure churn" into design.rst
    would put a false milestone attribution in the user docs, the same defect class r17 fixed when
    it scoped the unscoped churn sentence) apply only to journals whose
    `DurablePlan.process` `OpSpec` embeds the worker closure BY VALUE — the documented
    `OpSpec.from_ref` idiom (`docs/checkpoint/design.rst:20,58-65`) is unaffected. Freezing the
    unscoped r16 sentence would put a false claim in the user docs (§1.2/§7.3).
- **m51 — variation-aware write-out (skim augmentation)** (repos: `graphed` +
  `uproot5-graphed-mvp`). Targets: §6.4, **plus §9.1's `graphed.selection` and §2.3d's `to_parquet`
  table entry** (r18 — §9.1 marks `graphed.selection` m51 and m51's anchors freeze both, while the
  target line named only §6.4; the DoD scopes an implementer off the target line). Frozen anchors:
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
    comparison form). **Its coverage items MAY be SEPARATE fixtures, r22** — they exercise
    different record shapes (a depth-1 collection for the object-migration case, a depth-0 stored
    factor for the weight-only one), and §6.4a's r22 field-scoped level channel makes one mixed
    record legal but not required — covering a shift with object-level migration (per-label inner masks,
    §6.4d, **written through the per-LEVEL, FIELD-SCOPED
    `select={0: event_mask, ("Jet", 1): jet_mask}` channel** (r22 — the level-≥1 entry names its
    field; §6.4a) — **so this fixture's written record is the MULTI-FIELD one (`{Jet: var * {…}, …}`,
    where a field path is what disambiguates depth 1), while §6.4's canonical single-collection skim
    (`to_parquet(events.Jet, …)`, form `var * {…}`) uses §6.4a's r24 BARE depth-`k` key; state which
    shape each coverage item writes, since the two key forms are not interchangeable** —
    §6.4a r11 is what makes this anchor satisfiable at all; a single row mask cannot express it),
    a weight-only label **whose stored factor is in the RECORD's own row space — `graphed.weight(c)`
    for a `c` reached from the record's context across `vary` IDENTITY links only** (r18, §6.4b's
    row-space precondition: a selection-scoped `graphed.weight(sel)` is NOT storable and is refused
    at the entry check, so naming the storable spelling here keeps the anchor buildable), a label
    structurally equal to nominal (all-zero delta) — **which is also the OUTPUT-COLLAPSE case, and
    the anchor witnesses the REPLICATION, not only the all-zero content** (r18: `mark_output`
    de-dups, `src/store.rs:147-156`, so `evaluate_ir` returns FEWER values than marked outputs and a
    positional unpack in `_WritePart` misassigns every label after the collapsed one — silently,
    since an all-zero delta is exactly what one expects there; §6.4f binds resolution BY NODE ID) —
    and an
    e-canonical numeric-tag label (`murf_5em1`): stored names embed the label verbatim and the
    reader returns the same label.
  - **`graphed.selection(ctx)` bridge** (§6.4a/§9.1, r11): a skim written from the §2.6 context
    idiom — `to_parquet(events.Jet, select=graphed.selection(sel))` where `sel = events[mask]` —
    round-trips identically to the same skim written with the mask passed by hand;
    `graphed.selection` on a ROOT context returns `None`. Without it the m51 sink is reachable
    only from the loose §2.1a style, one milestone after §2.6 makes the context the primary idiom.
    **Plus the `vary`-derived-context case explicitly** (r16 — §6.4b's stored varied weight factors
    are reached through `graphed.weight(ctx)`, so the weight-storing skim is written from a
    weight-`vary`-derived context by construction, and the r15 predicate refused it): with
    `sel2 = graphed.vary(sel, "btag", …, is_weight=True, …)`,
    `to_parquet(events.Jet, select=graphed.selection(sel2))` is ACCEPTED by (2a) and round-trips
    identically to the pre-`vary` spelling (§9.1 r16: `graphed.selection` walks `vary` identity
    links; §6.4a(2a) r16 admits them). **Plus the SIXTH control, r23, which is the one that
    discriminates §6.4a(2a)'s r23 `vary`-link admission from bare handle equality** (in the bullet
    above the `vary` link sits BELOW the mask derivation, so the mask still carries the record's own
    handle and both readings ACCEPT): with `E2 = graphed.vary(E1, "pu", …, is_weight=True)`,
    `mask = gak.num(E2.Jet) >= 4`, `sel = E2[mask]`, the write
    `to_parquet(E1.Jet, select=graphed.selection(sel))` — record handle `E1`, mask handle `E2`,
    identical row spaces (a `vary` link is §6.1d kind (2), IDENTITY) — is ACCEPTED and round-trips
    identically to the same skim written from `E2`. Bare handle equality REFUSES it, which is the
    hard-block-a-legal-spelling defect r20 fixed one clause up for absent-operand case (ii).
    **Plus the RE-RECORDED-MASK positive control (r18; re-worded r19 for §6.4a(2a)'s handle-equality
    predicate, which withdrew the per-label node-id rule along with the descendant search it served —
    the control's PURPOSE is unchanged: an implementer shipping `mask is ctx._selection` would pass
    every other m51 anchor and refuse a legal program forever)**: a `select=` value that is a
    RE-RECORDED equal expression — a distinct Python object carrying the record's context handle and
    the same per-label node ids — is ACCEPTED and round-trips identically (measured r18 vs
    `graphed-latest@ff7c607`: `a = src * 2.0; b = src * 2.0` → `a.node_id == b.node_id == 1`,
    `a is b` False, `session.node_count() == 2`).
    **Plus the UNIVERSE/NOMINAL-derived case, both halves (r17 — two binding rules in this sink had
    no anchor at all, so a polymorphic return and a refusal path would land as new m51 source with
    zero frozen-suite coverage under the DoD's ≥90 % diff-coverage-from-the-frozen-suite gate)**:
    (a) `graphed.selection(graphed.nominal(sel))` returns **that label's member of the argument's own
    selection — an unvaried `Array`, not a `Varied`, in the GRANDparent's row space** (§9.1 r15),
    asserted against a manually projected reference, and `None` when the argument is a root context;
    (b) passing that value as `select=` for a record read from `sel` is **REFUSED at record time by
    predicate (2a)**, naming both contexts (§6.4a(2a) r15: universe/nominal projection links are not
    admitted — a bare parent test accepts it while the mask lives one row space up).
  - **Entry checks (§6.4a, r12 — TWO predicates, each anchored with the positive control IT
    decides; the r11 single offsets predicate could not decide the case r11's own anchor named as
    its positive control)**: (1) **multiplicity** — a write whose per-label member offsets differ
    from nominal's at any stored level is refused, **per partition at execution time from
    `_WritePart` before any buffer is stored** (`python/graphed/awkward/io.py:111-127` evaluates
    inside the worker; do NOT freeze a record-time raise); (2) **row-space agreement, SCOPED PER
    LEVEL** (§6.4a r13) — at **level 0** the check has two halves with two sites (§6.4a r14):
    **(2a) lineage, record-time** — a record whose context is not the one the supplied
    `select=` mask derives from is refused at the
    `to_parquet` call naming both contexts, with the *silent-corruption* case as its named
    positive: a record carrying a NON-varied embedded selection (`sel = events[nominal_mask]`,
    then `select=varied_mask`) is refused, not written on mismatched rows — and the chained-context
    case (`graphed.selection(sel2)` for `sel2 = sel[mask2]` against a root-row-space record)
    likewise; **plus the two ABSENT-OPERAND cases** (§6.4a r15) — a CONTEXT-FREE record (the loose
    §2.1a write style) SKIPS (2a) and IS written, the positive control that keeps the loose sink
    reachable, while a contexted record whose supplied mask **carries NO context handle** (a
    hand-built loose mask, §2.3e's Drop rule) is refused naming the
    record's context — **worded over the handle, NOT over "derived no context", r20, plus the FIFTH
    positive control that discriminates the two readings**: a mask recorded entirely from reads
    performed THROUGH the record's own context (`select=(events.MET.pt > 50)` rather than
    `graphed.selection(sel)`) carries the record's handle by §2.3e's ORIGINATION rule and derived no
    context, so r19's binding handle-equality predicate ACCEPTS it and it round-trips; the r15–r19
    wording froze a REFUSAL for it, hard-blocking a legal skim spelling read-only (§6.4a(2a) r20);
    **(2c) DEPTH at every supplied level, record-time (r21; generalized r22)** — a JAGGED level-0
    mask read through the record's own
    context (`select=(events.Jet.pt > 25)`) is REFUSED at the `to_parquet` call naming the level and
    the per-level channel, with the flat event-level mask over the same context as the positive
    control: it passes (2a) by ORIGINATION and (2b) by outer length, so without (2c) the writer
    applies it as the level-0 OR and silently filters OBJECTS instead of rows — **plus the mirror
    case at level ≥ 1, r22**: a FLAT mask supplied at level 1
    (`select={0: evt, ("Jet", 1): evt}`) is refused at the call naming the level, since it has no
    depth-1 offsets and the level-≥1 structural check below would otherwise have no operand and die
    per partition inside `_WritePart` with an `AttributeError`/`IndexError` — at execution, on a
    record-time form property (§6.4a r22, the argument r21 used at level 0); **(2b) row-count equality between the record and that mask — EXECUTION-time, per
    partition from `_WritePart`** like (1), NOT a record-time raise (r14: row counts are data);
    at **levels ≥ 1** the check is structural (the mask's per-label offsets equal the
    record's at that depth) and raises per partition from `_WritePart` like (1) — a lineage test is
    unsatisfiable there, since an inner mask is per-OBJECT and is not `graphed.selection` of any
    context. Positive control for the level-≥1 half: the `select={0: event_mask, ("Jet", 1): jet_mask}`
    object-migration write below still passes both predicates.
    **Plus §6.4b's r18 ROW-SPACE refusal for a stored varied field**: a write whose stored fields
    include `graphed.weight(sel)` for a SELECTION-derived `sel` is refused at the entry check with a
    message naming the ROW-SPACE mismatch (the record is pre-selection on the superset rows while
    §2.6c gives `sel`'s registry per-label row sets re-indexed by each label's mask, and no inverse
    exists) — explicitly NOT the offsets message predicate (1) would otherwise emit; the positive
    control is the storable spelling, `graphed.weight(c)` for a `c` reached across `vary` identity
    links only.
  - Representation anchors, structural (R0.10a — no size thresholds in frozen tests): appended
    columns land in the bound exact representation (XOR-delta values, packed masks) with
    identifier-shaped stored names (labels verbatim, §6.4b) — verified by reading the raw file
    schema + manifest — **plus the FIELD half of the name convention** (§6.4b r15): a NESTED field
    path (`Jet.pt`) is flattened per level and the skim still reads back through the manifest, and a
    name COLLISION is refused naming BOTH SOURCE FIELDS — **the fixture varies BOTH `Jet.pt` AND a
    flat field named `Jet_pt`**, which is the derived-vs-derived class (both derive to
    `__vary_L__Jet_pt`); r16: a varying `Jet.pt` alongside a NON-varying `Jet_pt` is NOT a collision
    under the bound `__vary_{label}__` prefix and MUST NOT be frozen as a refusal (it is a legal
    nested-field skim); the compression WIN is an R0.11 implementer-report measurement on a real
    skim (methodology stated), NOT a frozen gate.
  - **Manifest DETERMINISM** (r14 — §6.4e binds sorted manifest keys precisely because
    set/dict-iteration order would make the written bytes `PYTHONHASHSEED`-dependent, yet every m51
    manifest anchor is content-only, which an unsorted serialization satisfies, and m51's one
    byte-identity anchor is on the manifest-FREE unvaried path and can never observe it — the same
    invisible-violation shape r13 caught for §8.2(i) and closed with an m49 plan-byte anchor): the
    same varied write performed in two fresh processes under differing `PYTHONHASHSEED` yields
    byte-identical manifest bytes; minimally, the serialized key order is asserted sorted.
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
  - **§6.4f WRITE-PATH optimizer-merge refusal (r22 — §6.4f settles that §7.2's refusal "does"
    guard the write path, binding new m51 source that had NO anchor in this list; new source with
    zero frozen-suite diff coverage either fails the DoD's ≥90% diff-coverage-FROM-THE-FROZEN-SUITE
    gate or is covered only by `tests/extra/**`, which that gate excludes — the coverage class this
    plan repairs elsewhere, r14/r16/r17/r18)**: a varied `to_parquet` whose per-label expressions
    include an optimizer-mergeable spelling — a label whose value is `w * 1.0`, which §1.1 makes
    first-class via `variations={s: w * float(s)}` and the M4 identity tokens merge
    (`src/optimizer/engine.rs:22-31`; measured, two fills weighted `w` vs `w * 1.0` record fill
    nodes `2`/`4` and compile to `outputs() == [2]`) — is REFUSED at the `to_parquet` call with
    §7.2's message and workaround, with an UNVARIED positive control that today's write path is
    unchanged (§6.3). The check is affordable there: `to_parquet` already compiles at the call
    (measured r22 vs `graphed-latest@ff7c607`, `python/graphed/awkward/io.py:231` —
    `compiled = compile_ir(session, array)`, one line after `_evaluation_columns` at `:230`).
  - **§2.3d table entry for `to_parquet`** (r17; re-worded r18 — it carries NO m48 disposition and is
    absent from m48's table and floor list, so nothing frozen has to change here): with §6.4's
    `select=` landed, `graphed.awkward.to_parquet` ENTERS the table as *accepting* and joins the
    named floor list — the m51 entry asserts the accepting behaviour, i.e. a `Varied` `select=` is
    consumed internally and no per-label result is returned to the caller.
  - ROOT half: `graphed_write` gains IR evaluation (derived columns in ROOT skims — the §6.4f
    larger half) with the same round-trip anchor; numpy-backend refusal test (§6.4f).
  - Docs: the §7.3 checkpoint paragraph gains m51's write-path scope (r17, correcting r13): widening
    `_WritePart` (§6.4f) churns **no shipped journal** — `write_plan` builds a plain-callable
    `Plan` (`write.py:32-43`) and the checkpoint runner takes a `DurablePlan`
    (`checkpoint/runner.py:77-91`) — so the churn sentence is scoped to a journal a caller built by
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
**full support for labels the OPTIMIZER merges** (§7.2 r17: distinct record ids that the M4 identity
/commutativity rules collapse into one compiled output — m48 REFUSES them with a named workaround;
replicating such a value across its labels needs §8.2(i)'s record→reduced map on the frontend unpack
path and is not scoped in m48–m51);
an **in-IR bit-view / `packbits` verb** (r14: §6.4c's XOR deltas are computed in `_WritePart` on
evaluated buffers precisely because no recorded form exists — measured, `float32 ^ float32` is a
`TypeError` in both numpy and awkward and gak ships no `view`/`packbits`/`frombuffer`);
**multiplicity-changing stored variations** for §6.4 (shift-dependent cleaning / overlap removal /
matched collections: no representable same-shape delta, refused in v1 per §6.4d);
**a contexted fill that suppresses the AMBIENT weight while applying its own explicit factor**
(r24, §6.1d: `unweighted=True` suppresses both, by design, and nothing detaches a context's
registry — the v2 answers are a context-level detach verb or a narrower `unweighted=` scoped to the
ambient factor alone); a first-class Rust `Vary` NodeKey.

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
  prompt Out-of-scope bullet (`graphed-root-prompt.md:1286-1287`) and the two inline R22.0/R22.10
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
| m05 behavioral invariants (weight preserves / shift orders selection) | consolidated: `graphed tests/frozen/corpus/m05/test_systematics.py:25-37`; `graphed-corpus tests/frozen/m05/test_systematics.py:26-38` — the two copies differ by one blank line (cba §corpus §3), and r6–r21 carried the corpus-repo numbers on the consolidated path; re-measured r22: `test_kinematic_variation_changes_selection` at `:25` / `:26`, `test_weight_variation_preserves_selection` at `:33` / `:34`, bodies `assert jes_up > nominal > jes_dn` and `assert btag_up == nominal == btag_dn` |
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
| The dedup runs on the REDUCED store; `compile_ir` never marks the RECORD store, and compiled `outputs()` are POST-REDUCTION ids (why §7.2's r21 derivation uses the frontend's OWN marked-id list) | `src/store.rs:185-200` (`from_reduced`; `mark_output(map[o])` at `:197`), `python/graphed/execute.py:70-80` (ids passed as `reduce(outputs=ids)`/`serialize(outputs=ids)`); measured r21 vs `graphed-latest@ff7c607`: record ids `src 0, dead 1, b 2, e 3, c 2` → `GraphStore.deserialize(ir).outputs() == [1, 2]`, `evaluate_ir` returns 2 values (b's then e's, first-occurrence order over distinct record ids), `s._store.outputs() == []` |
| `awkward_array_metadata` is written ONLY by awkward's PRIVATE `_connect` helper (why §6.4e binds a public route + a no-private-import rule, r21) | `awkward/_connect/pyarrow/table_conv.py:16` (`AWKWARD_INFO_KEY`), `:19-40` (`convert_awkward_arrow_table_to_native`); `ak.to_parquet` imports it at `awkward/operations/ak_to_parquet.py:14` and calls it at `:417`; the same file's public merge point for `attrs` is `table.replace_schema_metadata(merged_metadata)` `:424-431`; `ak.to_arrow_table` never adds the key (measured, awkward 2.12.0 in `graphed-latest`'s venv) |
| `boost_histogram` REJECTS `sample=` on `Double()`/`Weight()` and accepts it on `Mean()`/`WeightedMean()` (why m50's `sample=`-only-label fixture pins its storage, r21) | measured r21, bh 1.8.0 in `graphed-histogram-latest`'s venv: `Double`/`Weight` → `TypeError: Keyword(s) sample not expected`; `Mean().fill(x, sample=…)` and `WeightedMean().fill(x, weight=…, sample=…)` succeed; the evaluator passes `sample` straight through, `graphed-histogram src/graphed_histogram/boost.py:60-71`; `_spec.py:19-27` carries both mean storages |
| The OPTIMIZER also merges DISTINCT record ids — record-time identity cannot see it (why §7.2 binds an m48 refusal, r17) | rule set `src/optimizer/engine.rs:22-31` (`SYMMETRIC_OPS`, `IDENTITY_TOKENS` `x+0.0`/`x*1.0`), `:67-80` (rule construction), `:89-110` (saturate + quotient). Measured r17 vs `graphed-latest@ff7c607`: `nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5` → record ids `0,1,2,3`, `compile_ir(s, nom, m1, m2, mh)` → `outputs() == [0,1,2]`, `evaluate_ir` returns 3 values; on the fill path (graphed-histogram@211cbbe) two `Histogram.fill`s with `weight=[w]` vs `weight=[w*1.0]` → fill node ids `2`,`4` → `outputs() == [2]` |
| Non-growth `StrCategory` silently overflows an undeclared label (why §6.2 binds the declaration) | measured, boost_histogram 1.7.2 (2026-07-30): `sum 2.0` vs `sum(flow=True) 3.0`, `Traits(overflow=True, growth=False)` |
| `FillEvaluator` flattens each input INDEPENDENTLY (why §6.1d's per-object fill stays unflattened) | `graphed-histogram src/graphed_histogram/boost.py:39-47,60-71` |
| `ak.to_parquet` vs `pq.write_table` differ in bytes AND KV metadata; `ak.to_parquet` has no metadata param (why §6.4e branches) | re-measured r13, awkward 2.12.0 / pyarrow **25.0.1** (version corrected r14; a clean resolve gives 25.0.1, matching the `created_by` row, and the list-of-float half was re-verified there in r14): different bytes for every array probed (record, list-of-float, flat numeric); the arrow path DROPS `awkward_array_metadata` (record: file-KV `{ARROW:schema, ak:parameters, awkward_array_metadata}` vs `{ARROW:schema, ak:parameters}`; list-of-float: `{ARROW:schema, awkward_array_metadata}` vs `{ARROW:schema}` — so `ARROW:schema` is always present and `ak:parameters` is ARRAY-dependent, not writer-dependent); `"metadata" in signature(ak.to_parquet)` → `False`. The r12 row's two sha256 digests are withdrawn — they named no array and are not reproducible |
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
| Parquet KV metadata unused today (greenfield for the §6.4e manifest) | re-verified r17: the only `metadata` USE on the write/read path is `ParquetFile(path).metadata.num_rows` (`python/graphed/parquet.py:77`; `:107,118` are docstring mentions of the same); no `key_value_metadata` / `schema.with_metadata` anywhere in `graphed-latest/python` or `uproot5-graphed/src` (0 hits) |
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
| `_GroupReduce.layout` is COUNT-based positional slicing (why §6.1c re-binds it to indices) | `graphed-histogram src/graphed_histogram/boost.py:100-117` (`for j in range(i, i + k)`), built from `len(h._fill_nodes)` at `:282` (r12: `:198` is inside `record_external`); per-slot spec is `h._spec` `:282`, `_GroupZero` `:127-130`, `Histogram.plan` `:244-253`; `python/graphed/aggregate.py:57-65` |
| `gak` defines NO `__all__` (why §2.3c binds an explicit discovery rule + non-vacuity floor) | measured 2026-07-30: `grep -c "__all__" python/graphed/awkward/functions.py` → 0; `grep -c "^def " …` → 73 (incl. private helpers); package `__all__` at `python/graphed/awkward/__init__.py:17-31` lists modules/classes |
| m24 anti-drift pin is a **39**-name literal | `tests/frozen/awkward/m24/test_interface_parity.py:39-79` (counted 2026-07-30) |
| `graphed` has NO `graphed-histogram` dependency; the house pattern is `importorskip` (m48 fixture fact) | `graphed pyproject.toml` `dev` extra (boost-histogram/hist only); CI installs `.[dev]` `.github/workflows/ci.yml:34,57,143`; `tests/frozen/preserve/m25/test_histogram_preservation.py:31`, `m27/test_variadic_call_templates.py:185,207`, `m30/test_producer_cross_seam.py:155` |
| `graphed-histogram` has NO corpus dependency and no reference JSONs (m48 fixture fact) | measured 2026-07-30: `grep -rn "corpus" tests/ .github/workflows/` → 0 hits; runtime deps `pyproject.toml:20-21` |
| `graphed`'s only cross-process frozen test is the M6 error pool (it ships no `Executor`) | `tests/frozen/debug/m6/test_process_boundary.py:7,16` |
| `uproot5-graphed-mvp` has NO frozen tree (m51 creates one) | measured at `393ecef`: `find . -type d -name "*frozen*"` → empty; **12** flat `tests/test_graphed_*.py` (+2 shared helper modules `graphed_uproot_analysis.py`/`graphed_uproot_report.py`, re-counted r12); zero `tests/frozen` references repo-wide |
| `uproot5-graphed-mvp` COLLECTS a new frozen tree but GATES nothing (why §10 binds m51's cov/type/matrix edits, r23) | measured at `393ecef`: `pyproject.toml:136` `testpaths = ["tests"]` (so `tests/frozen/m51` is collected); `.github/workflows/graphed.yml:55` runs `python -m pytest -vv tests -m "not xrootd"` with **no `--cov`** (`grep -c cov graphed.yml` → 0), `:26-32` ubuntu-latest + CPython 3.11/3.12 only, `:7-10` triggers on `push` to `graphed-mvp` + `workflow_dispatch` (no `pull_request`); NO `[tool.mypy]` section anywhere in `pyproject.toml` and no coverage config. Contrast `graphed-histogram .github/workflows/ci.yml:44`, `pytest tests/frozen --cov=graphed_histogram --cov-branch` |
| Parquet footers embed the WRITER VERSION (why §6.4g's golden is same-process, not a committed blob) | re-measured r12 (awkward 2.12.0 / pyarrow 25.0.1): the footer string is `parquet-cpp-arrow version <arrow version>` = `25.0.1`, readable as `ParquetFile(path).metadata.created_by`; two writes of the same array in one process ARE byte-identical |
| Corpus rounds to 6 decimals PRE-fill and again in the comparison helpers (m48 matrix anchor) | `graphed tests/_corpus/graphed_corpus/analyses/systematics.py:79,102,50`; `histograms.py:20` (`STABLE_DECIMALS = 6`), `:35-37` (`bin_values`), `:40-43` (`fingerprint`, whose `return hashlib.sha256(payload).hexdigest()[:16]` at `:43` is the line that establishes the claim) — re-measured r22, correcting the r6–r21 `:34-37,39-42`, which opened on blank lines and truncated `fingerprint`'s return; gak has no `round(decimals)` — `rint` is a ufunc only, `python/graphed/array.py:54` |
| Corpus b-tag SF is the CENTRAL SF on JES-shifted jets (why §2.1 stacking is label-aligned for weights) | `graphed-corpus src/graphed_corpus/analyses/systematics.py:74-76,25-36` (re-counted r12: `:73` is blank, `:75` is the `ht` sum) |
| `StageError.__hash__` is a hand-written tuple (`__eq__` is `__dict__`-based) — a new field does NOT ride free | `python/graphed/debug/errors.py:75-78` (`__eq__`, `:78` is the `__dict__` compare), `:80-81` (`__hash__`) — re-counted r12 |
| `_PartitionReduce` is the `process` of the in-memory `Plan`, NOT a `DurablePlan` `OpSpec` — and no `Plan → DurablePlan` bridge ships (why §7.3's **m48** churn is SCOPED — r17; the MILESTONE corrected in r22 and swept into this row in r23) | `python/graphed/aggregate.py:44-65,95-108`; `Plan.process` is a plain `Callable[[Partition, WorkerResources], R]` `python/graphed/core/execution.py:206-217`; `task_id`/`OpSpec` live on `DurablePlan` `python/graphed/core/plan.py:54,126,164-176`; `run_resumable` requires a `DurablePlan` `python/graphed/checkpoint/runner.py:77-91`. Measured r17: `grep -rn "DurablePlan(" python/` → 0 (all constructions are in hand-written tests); `OpSpec.from_callable` only at `shuffle.py:181,188,245,259`; `graphed-exec-check/src` → 0 `task_id`/`DurablePlan`; documented idiom `process=OpSpec.from_ref("myanalysis:hist_chunk")` `docs/checkpoint/design.rst:20,58-65`, mirrored in `tests/frozen/checkpoint/m8/analyses.py:114-123`; `OpSpec.from_callable(_PartitionReduce(...)).kind` → `"opaque"` (true, but unreached by any shipped caller) |
| `to_parquet` is awkward-idiom only (numpy has its own 1-D-capped one) — §6.4a/f spelling | `python/graphed/awkward/__init__.py:14,30`; `python/graphed/awkward/io.py:206-216`; `python/graphed/numpy/io.py:182-191` (signature; its 1-D cap is inside `_WritePart.__call__`, `:164-165`) |
| `gak.broadcast_arrays` records an awkward-namespaced op; `graphed-histogram` has no awkward runtime dep (why §6.1d's broadcast is a neutral seam) | `python/graphed/awkward/functions.py:677-685`; `graphed-histogram pyproject.toml:21` (runtime) vs `:25-39` (dev) — re-counted r13 |
| `bh.Histogram` has NO name-based axis lookup: `StrCategory(name=…)` and `h[{"variation": label}]` both raise (why §6.2(i-bis) slices by POSITION) | measured r12, boost_histogram **1.7.2 and 1.8.0**: `StrCategory(..., name="variation")` → `TypeError: unexpected keyword argument 'name'`; `h[{'variation': 'jes_up'}]` and `h[{'variation': bh.loc(...)}]` → `TypeError: list indices must be integers or slices, not str`; `h[{1: bh.loc('jes_up')}]` works. **The name carrier is per-axis `__dict__`, and `h.axes.name` is NOT a usable oracle** (re-measured r13, bh 1.8.0): it maps the attribute over every axis and raises `AttributeError: object Regular has no attribute name` on a two-axis histogram (the only shape axis mode produces); `[a.__dict__.get("name") for a in h2.axes]` → `[None, 'variation']`, preserved across `spec_of`→`zero_of`. The r12 row's `h.axes.name == ('variation',)` holds only for a ONE-axis histogram |
| Axis "names" are spec METADATA in graphed-histogram, round-tripped from `axis.__dict__` (the §6.2(i-bis) name carrier) | `graphed-histogram src/graphed_histogram/_spec.py:31-37` (`_metadata_of`), `:81-84` (`_restore_metadata`), `:115-135` (`zero_of` rebuilds a plain `bh.Histogram`) |
| `Histogram.fill` requires ONE array per axis (why a user-declared variation axis is unfillable, §6.2(ii)/§11) | `graphed-histogram src/graphed_histogram/boost.py:160-161` |
| `CompiledGraph` carries only `ir` + `source_names`; the PyO3 surface exposes no record→reduced id map (why §8.2's transport needs a NEW read-only core accessor) | `python/graphed/execute.py:36-45,54-80`; the THREE `#[pymethods]` blocks in `src/lib.rs` are at `:102` (`PayloadDescriptor`), `:159` (`GraphStore`, impl closing at `:416`) and `:470` (`IncrementalReducer`) — re-counted r14; the GraphStore block is add_source/add_op/add_reduction/add_external/add_exchange/add_join/node_count/to_dot/serialize/deserialize/nodes/outputs/reduce/reduce_incremental/reduction_report, and neither of the other two returns an id mapping; `remap` never returned, `src/optimizer/mod.rs:88-116`; stage members evaluated inline `execute.py:110-117` |
| `graphed.numpy` DOES ship donor-free constants — but as eager fixed-shape Sources a one-source plan cannot bind (the precise §4.1 gap) | `python/graphed/numpy/creation.py:27-28,31-75`; `__all__` `python/graphed/numpy/__init__.py:578-598`; single-source binding `python/graphed/aggregate.py:57-63,96-101`; `python/graphed/execute.py:104-105` |
| `ak.broadcast_arrays` raises on a length mismatch (why §6.1d's refusal is a message CONTRACT, not `FillEvaluator`) | measured r12, awkward 2.12.0: lengths 7 vs 3 → `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`; a jagged 3-row value broadcasts fine |
| gak public surface is **65** functions with heterogeneous first arguments (why §2.3e's propagation gate is scoped, not blanket) | measured r12: 73 `def`s / 65 public in `python/graphed/awkward/functions.py`; `apply_correction` `:476`, `onnx_inference` `:513` (payload first), `to_list` `:693`, `head` `:732`, `sample` `:737` (eager), `fields` `:717`, `type_of` `:722`, `backend_of` `:727` (non-Array returns), `zip` `:118`, `concatenate` `:383`, `where` `:400`, `unflatten` `:600`, `linear_fit` `:346` |
| `Array` public METHODS exist beyond the dunder surface (why §2.3a widens) | `python/graphed/array.py:374-391` (`filter`/`map`/`reduce`/`repartition`); numpy idiom `python/graphed/numpy/array.py:92-190`, tuple `__getitem__` `:132-136` |
| `graphed`'s Array-consuming module verbs (the §2.3d enumeration) read `node_id`/`session` directly | `python/graphed/__init__.py:8-25`, `__all__` `:27-58`; `python/graphed/execute.py:70` (`ids = [arr.node_id …]`; r13 — `:74` is `blob = bytes(`); `python/graphed/aggregate.py:86` (`session = outputs[0].session`; r13 — `:66-72` is the blank line + signature head, the def runs `:68-77`); `Array.node_id`/`session` are PROPERTIES (`array.py:137-143`) and `__getattr__` guards only `_` (`:332-335`) |
| Three further public `Array`-first verbs the r12 §2.3d list left undisposed (why r13 adds them + a discovery rule) | `python/graphed/shuffle.py:84,89` (`pack_key(array, *, on)` → `array.session.record_op`), `:142,155` (`shuffle_plan(output, …)` → `output.session`), `:208,220` (`join_plan(output, …)` → `output.session`); all three in `__all__` `python/graphed/__init__.py:50-57` |
| `Histogram.fill_nodes()` is PUBLIC but UNLABELED (why §4.3/§9.1 need a per-label accessor, not "the private list") | `graphed-histogram src/graphed_histogram/boost.py:215-216` (`staged_fills`), `:218-219` (`fill_nodes() -> list[Array]`); already used by frozen tests `tests/frozen/m29/test_multi_weight_fills.py:84,95`; `session.walk` takes an `Array`, not an id — `python/graphed/session.py:245-252`, `root = array.node_id` `:268` (re-counted r15) |
| A `frozenset` field in the worker closure makes the serialized plan seed-dependent (why §8.2(i) binds a sorted tuple) | re-measured r14 with the payload + toolchain NAMED so it reproduces (the r13 row named neither): cloudpickle 3.1.2, payload `(3, frozenset({"btag_down","btag_up","jes_down","jes_up","nominal"}))` under `PYTHONHASHSEED` 1 / 7 / 12345 → sha256[:16] `b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831` (three distinct digests; the r13 triple was measured on an unnamed payload and is withdrawn); those bytes feed `OpSpec.identity()` (`core/plan.py:72-77`) → `task_id`/`to_bytes` (`:164-176`); the house discipline is `read_columns`' SORTED read set (`return tuple(sorted(needed))`, `projection.py:147`; function span `:109-147` — corrected r16 to match §8.2(i), where the `:109-121` pointer landed on the docstring) |
| `evaluate_ir` has NO per-node error attribution (why §8.2 needs part (iii)) | `python/graphed/execute.py:99-126` — a bare `for nd in store.nodes():` dispatch loop, no `try`/`except`, op dispatch `:109`, stage members evaluated inline `:110-115`; `_PartitionReduce.__call__` is read → `evaluate_ir` → `reduce`, one call, no node context (`python/graphed/aggregate.py:57-65`) |
| `_WritePart` is the `process` of a plain-callable write `Plan` — write plans carry NO journal (why m51's churn sentence is scoped, r17) | `python/graphed/awkward/io.py:239,260` construct it, `:274` `gw.write_plan(partitions, writer)`; `python/graphed/write.py:32-43` `Plan(process=write_part, …)` — a `graphed.core.execution.Plan` (`core/execution.py:206-217`), which `run_resumable` cannot take (`checkpoint/runner.py:77-91` needs `process.resolve()` + `task_id`); `task_id` folds `process.identity()` only on a `DurablePlan` `python/graphed/core/plan.py:164-176` |
| `core` and `preserve` are ONE pytest process each — duplicate basenames collide (why §10 pins unique file names for `core/m49`, `preserve/m50`) | `scripts/run-tests.sh:16-25` (`SUITES`), `:30` (`SPLIT_PKGS="frontend numpy awkward"`); no `__init__.py` under `tests/frozen` (measured); existing `tests/frozen/core/m4/test_benchmark.py`, `tests/frozen/preserve/m9/test_reproduce.py`, `tests/frozen/preserve/m9/test_inspect.py` |
| `graphed` VENDORS the corpus (no dependency); a name-only dep does not install in this org's CI (the m48/m49 fixture edit) | `graphed pyproject.toml:42-48` (`dev`, no `graphed-corpus`), `tests/_corpus/{graphed_corpus,references}` (23 JSONs) on `pythonpath` `:115-127`; the dependency route needs a git-URL env + install line — `graphed-executors .github/workflows/ci.yml:17,38` (`CORPUS`), absent from `graphed-histogram .github/workflows/ci.yml:13-17` |
| A non-growth `StrCategory` OVER-declaration is invisible to the flow check (why the m50 declaration anchor needs a literal expected list) | measured r13, bh 1.8.0: 4 declared bins, 3 labels filled → `sum == sum(flow=True) == 3.0`; under-declaration (2 bins, 3 labels) → `sum 2.0` vs `sum(flow=True) 3.0` |
| `graphed.apply` is a public module verb with `Array.map`'s execution-time contract (the §2.2 `Varied.apply` name collision, accepted knowingly) | `python/graphed/array.py:397-410`; exported `python/graphed/__init__.py:9` |
| `_WritePart` evaluates PER PARTITION in the worker and unpacks ONE output (why §6.4a's offsets check is execution-time and §6.4f must widen the unpack) | `python/graphed/awkward/io.py:111-127` (`(out,) = evaluate_ir(...)` `:121`; r13 — `:122` is `result = ak.Array(out)`), `:206-216`; per-partition task graph `python/graphed/write.py:32-43` |
| `graphed` cannot host a fill-based frozen matrix (m48 AND m49(i) fixture fact) | `graphed pyproject.toml:42-48` (`dev` = boost-histogram/hist, no `graphed-histogram`); CI `.[dev]` `.github/workflows/ci.yml:34,57,143`; house pattern `tests/frozen/preserve/m30/test_producer_cross_seam.py:155` |
| `graphed.evaluate_ir` takes NO `Array` (why r14 removes it from §2.3d's refusing set) | `python/graphed/execute.py:85-91` — `evaluate_ir(compiled: CompiledGraph \| bytes, backend: Backend, sources: Mapping[str, object], *, externals=None)`; contrast `compile_ir(session: Session, *outputs: Any)` `:54-55` which DOES read `arr.node_id` `:70` |
| An `Array`-FIRST-parameter filter misses four disposed verbs (why §2.3d's discovery rule is annotation-wide, r14) | measured signatures in `graphed-latest`: `compile_ir(session: Session, …)` `execute.py:54`, `evaluate_ir(compiled: CompiledGraph \| bytes, …)` `:85`, `read_columns(arrays: Sequence[Array], source_nid: int)` `projection.py:109`, `apply(fn: Callable[..., object], *arrays: Array)` `array.py:397`, `aggregate_plan(*outputs: Array)` `aggregate.py:68` (var-positional, so first-parameter reachability depends on the filter's `*args` handling); DISCOVERED by it: `repartition` `shuffle.py:68`, `pack_key` `:84`, `join` `:92`, `shuffle_plan` `:142`, `join_plan` `:208`; `graphed.awkward.to_parquet(array: Any, …)` `awkward/io.py:206` is outside `graphed.__all__` entirely |
| The ANNOTATION-WIDE filter still misses `compile_ir` (why §2.3d's rule unions a NAMED floor list, r15) | measured r15 in `graphed-latest` (its own `.venv`), enumerating `graphed.__all__` via `inspect.signature` and keeping callables any of whose parameter annotations mentions `Array` → `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']` (8); `compile_ir(session: 'Session', *outputs: 'Any', optimize: 'bool' = True, maximal_fusion: 'bool' = False)` is NOT among them, and IS exported (`python/graphed/__init__.py:12,46` — re-counted r16: `:44` is `"apply"`, `:46` is `"compile_ir"`), so r14's "named non-`__all__` members" escape hatch did not reach it either |
| `GraphedError` is unrelated to `NotImplementedError` (why m48's refusal table splits by contract) | `python/graphed/errors.py` — `class GraphedError(Exception)`, `class GraphedTypeError(GraphedError)`; §5.4 binds a `NotImplementedError` |
| `Session.source` receives no context and `record_op` merges only from `inputs` (why §2.3e needs an ORIGINATION rule) | `python/graphed/session.py:133-140` (`source(self, name, *, form, data, **params)`), `:142-168` (fresh wrapper per call); `Session.node_count()` `:50-51` (the frontend-side arena-delta read §5.2a binds) |
| `Histogram.plan` passes the `__init__`-time spec, and cross-axis histogram addition raises (why §6.1c's `.plan()` refusal is GENERAL) | `graphed-histogram src/graphed_histogram/boost.py:244-253` (`_SumFills(self._spec)`/`_ZeroHist(self._spec)`), `:146-150` (`self._spec = spec_of(self)` in `__init__`); measured r14, boost_histogram 1.8.0: `bh.Histogram(Regular(3,0,1)) + bh.Histogram(Regular(3,0,1), StrCategory(['nominal','jes_up']))` → `ValueError: axes have different length` |
| `_GroupReduce.layout`'s first element is the OUTPUT name today, not a label (why m50's scaling anchor is worded over the two-level key shape) | `graphed-histogram src/graphed_histogram/boost.py:256-295` (`layout = tuple((label, len(h._fill_nodes), h._spec) for label, h in items)`, `items` = `(output_name, Histogram)`), consumed `:100-117` |
| Float XOR is not expressible in the IR; the buffer-side view is (why §6.4c binds `_WritePart` as the encoding site) | measured r14, awkward 2.12.0 / numpy: `float32 ^ float32` → `TypeError: ufunc 'bitwise_xor' not supported for the input types` for BOTH `np.ndarray` and `ak.Array`; `a.view(np.uint32) ^ b.view(np.uint32)` works; `grep -c "^def " python/graphed/awkward/functions.py` → 73 with no `view`/`packbits`/`frombuffer` (`values_astype` `:673` is a value cast) |
| `graphed` proper depends only on `executing` + `cloudpickle` (why §6.4e's reader is awkward-idiom and §6.2(i-bis) imports no `boost_histogram`) | `graphed pyproject.toml:27` (`dependencies = ["executing>=2.0", "cloudpickle"]`), extras `:29-46`; parquet entry points live in `graphed.awkward` (`python/graphed/awkward/__init__.py:14,30`) |
| A positional integer bin index equals the `bh.loc` slice (why §6.2(i-bis) needs no `bh.loc` inside `graphed`) | measured r14, boost_histogram 1.8.0: `h[{1: ax.index('jes_up')}].values()` equals `h[{1: bh.loc('jes_up')}].values()`; detection is duck-typed on `.axes` |
| `graphed-histogram` resolves on PyPI to a stale `0.0.1` (why m49(ii) needs a git-URL install pair, not a dev-extra name) | verified r14: `pypi.org/pypi/graphed-histogram/json` → name `graphed-histogram`, version `0.0.1`; the repo's own `pyproject.toml` version is also `0.0.1`; `graphed-executors .github/workflows/ci.yml:13,15,17` carries `GRAPHED`+`CORPUS` only, installed `:38,65,94,136`; frozen suite runs `:44,67,101,153` |
| `graphed-histogram` and `graphed-executors` each run `tests/frozen` as ONE process with no `__init__.py` (why r14 generalizes the unique-basename rule) | measured r14: `graphed-histogram .github/workflows/ci.yml:44,67`, `pyproject.toml:50` (`pythonpath = ["src","tests/frozen/m23"]`), `find tests -name __init__.py` → 0, existing `tests/frozen/{m23,m29}`; `graphed-executors ci.yml:44,67`, `pyproject.toml:54`, 0 `__init__.py`, 15 existing milestone dirs; `graphed tests/frozen/checkpoint/{m8,m39}` with `m8/test_resume.py` present |
| Adding ONE defaulted field to the worker closure dataclass changes its cloudpickle bytes (why §7.3's one-time churn lands at m48, where §7.2's (β) puts §8.2(i)'s field, not at m49, which only populates it) | measured r22, re-measured r23 (cloudpickle 3.1.2 / CPython 3.12.10): the SAME module name, class name and field names, with vs without one `variation_labels: tuple \| None = None` field, digest DIFFERENTLY (the instance state dict gains the key whatever its value). **The r22 literal pair `8d058bf867dc6bcd` / `22a566276fd6077d` is WITHDRAWN, r23** — it named the toolchain but not the module name, class name, field list or instance values, all of which enter cloudpickle's bytes for an importable class, so it is not re-runnable (an r23 probe of the same SHAPE gives a different pair); the qualitative statement is what binds, the shape §7.3 itself adopted when it withdrew `80e8024dc8f3b77d`; the chain is `OpSpec.identity()` = the cloudpickle blob → `task_id`, `python/graphed/core/plan.py:72-76,164-176`; `_PartitionReduce`'s fields today are ir/source_name/backend_factory/reader/columns/externals/reduce, `python/graphed/aggregate.py:44-55`, built at `:96-104` one line after `compile_ir` at `:95` |
| The m9 correctionlib recording path DOES put `systematic` in params (why m48's §4.1 anchor names the spelling, r22) | measured r22 vs `graphed-latest@ff7c607`: `graphed.preserve.record_external(s, CORRECTIONLIB_PLUGIN, corr, [njet], params={"name": "event_sf", "systematic": syst})` (`preserve/externals/_base.py:215-248`, the fixture spelling at `tests/frozen/preserve/m9/agc.py:113-115`) records three External nodes sharing ONE `descriptor.content_hash` and differing only in `params["systematic"]` — re-measured r23 **with the payload NAMED** (`agc.correctionlib_json()` at its default `scale=1.0`, `agc.py:38`), giving `sha256:e72c0da3cb6614cfaf50cea8c93ab740e8229986024a8bad4361e9ae82f4b5cd`; the hash is a pure function of the payload (`correctionlib_content_hash` = sha256 over `b"correctionlib-contents-v1"` + canonical JSON, `python/graphed/preserve/externals/correctionlib_external.py:14-18`), so the r22 literal `sha256:cae4dd4b…`, which named no payload, is WITHDRAWN as non-reproducing at the pinned revision. The gak verb is NOT that path: `gak.apply_correction` records `params={"name": …, "args": json.dumps(args)}` (`python/graphed/awkward/functions.py:505-509`), the systematic riding inside the args JSON |
| `read_columns` carries ONE conservative flag across ALL arrays passed (why m49's §5.3 conservative label rides a separate program, r22) | `python/graphed/projection.py:109-147` — `conservative = False` `:123` (`:130` is `nonlocal conservative` inside `on_op` — corrected r23), `conservative = True` on a non-field op applied to the source `:140`, `for array in arrays:` `:143` with `array.session.walk(...)` `:144` (corrected r23), `if conservative or not needed:` `:145` / `return None` `:146` |
| gak's *broadcast* class spans incompatible PRIMARY operand kinds, type-checked at record time (why §2.3e's propagation slots declare a kind, r22) | measured r22 vs `graphed-latest@ff7c607` with a contexted jagged-numeric `Array` (`from_awkward(s,"events",ak.Array([[1.0,2.0],[3.0]]))`): `num`/`unzip`/`drop_none`/`singletons`/`firsts`/`where`/`unflatten(a, num(a))` → OK; `with_field(a, num(a), "x")` → `GraphedTypeError: ill-typed op 'ak.with_field' … no tuples or records in array` |
| `to_parquet` compiles AT THE CALL (why m51's §6.4f write-path merge refusal is a record-time check) | `python/graphed/awkward/io.py:230-231` — `columns = _evaluation_columns(...)` then `compiled = compile_ir(session, array)`, both inside `to_parquet` (`:206-216`), measured r22 vs `graphed-latest@ff7c607` |
| Phase-2 parking being un-parked | `graphed-root-prompt.md:1262,1282,1286-1287` (the Out-of-scope bullet wraps two lines; `:1284` is the header, `:1285` blank — re-measured r18), `ops_catalog.md:75` |

## Revision history

- **r24 (2026-07-30)** — review round 15 (three independent r23 reviews: facts / design / tests,
  `systematics-vary-plan-review-r23-{facts,design,tests}.md`; 18 findings after NIT exclusion, 16
  unique after merging two cross-lens duplicate pairs — the §3.4 impact-set fixture (facts+design)
  and §2.6b's mixed-granularity illustration (facts+tests)). **All 16 confirmed against the pinned
  roots and applied; nothing rejected, nothing deferred to the owner** (no finding touched an
  owner-locked decision). Audit trail:
  `systematics-vary-plan-revision-r24-notes.md`.
  **HIGH** — **§10/m49's §3.4 impact-set fixture is re-pinned to the SHARED-UPSTREAM form**: r23's
  "exactly one construction exists … the naive fixture does not exist at all" is withdrawn as
  measurably false (measured r24 on a raw `GraphStore`: nominal `sel(src)`, `up = shift(src, k)`,
  `dn = shift(src, k)` with `k = scale(src)` → `impact(up) = [1,3]`, `impact(dn) = [1,4]`, shared
  `= [1] = k`, members structurally different). Only the DOWNSTREAM variant is impossible, since
  interning keys on input ids; the anchor now asserts `u ∈ impact(up) ∩ impact(down)`,
  `u ∉ reachable(nominal)` AND `impact(up) ≠ impact(down)` — the discriminating conjunct r23's
  identical-member fixture cannot carry — and notes it is the same construction §8.2(i)'s m49
  anchor builds, so the two may share a fixture.
  **MID** — **§3.4's impact API is NAMED, SHAPED and PINNED** (read-only `graphed` module verb over
  `read_columns`' operands, `{label: tuple[int, ...]}` of sorted record node ids, spelling pinned at
  m49 freeze, listed with that shape in §9.1) — the §5.3 r16 treatment, applied to the one new
  surface that still lacked it while m49 freezes assertions through it (`session.walk` returns the
  root's value and exposes ids only through handlers, `python/graphed/session.py:245-255`).
  **MID** — **§6.1c's `.plan()` refusal is re-keyed on the MODE**: it raises on a `Histogram` that is
  VARIED *or* in axis mode (equivalently, whose staged fills' spec differs from the `__init__`-time
  `self._spec`), since r23's own new m50 fourth output — axis mode, no variations — fell through the
  "varied" trigger into the opaque `ValueError: axes have different length` the refusal exists to
  replace (measured, bh 1.8.0); m48's anchor and its positive control are re-worded, and m50's
  fourth output carries the axis-mode arm in one line.
  **MID** — **`Varied` is bound PER IDIOM**, mirroring the shipped `Session._array_cls` seam
  (`python/graphed/session.py:36-39`): a neutral base carrying `Array`'s surface plus a
  `graphed.numpy` subclass mirroring `NumpyArray`, `graphed.vary` returning the class paired with
  `type(x)`. Without it §2.3a's class-resolution gate on §10's mandated numpy-idiom fixture forces
  the 26 numpy-only public names onto a container §2.1 says must stay idiom-neutral (measured:
  `dir(Array)` public = 6, `dir(NumpyArray)` = 32).
  **MID** — **§6.2's hashing exemption is scoped to the MODE**: a SIBLING-mode fill, varied or not,
  hashes as today; an unvaried AXIS-mode fill does not (it declares the 1-bin `{"nominal"}` axis),
  which the r15–r23 wording denied while m50's r23 anchor asserts it.
  **MID** — **§9.1's `graphed.weight(ctx)` rationale stops naming a refused program** (`unweighted=
  True` alongside an explicit weight is a record-time error, §6.1d r19); §6.1d states the
  consequence — "ambient suppressed, my own factor applied" is not expressible from a contexted
  program in v1 — and §11 parks it.
  **MID** — **§6.4a admits the BARE depth-`k` key where the level-k structure is the RECORD'S OWN**,
  so §6.4's canonical single-collection skim (`to_parquet(events.Jet, …)`) has a legal object-level
  spelling at all; the discriminator is a record-time form property (measured: `var * {pt, eta}`
  versus `{Jet: var * {…}, Muon: var * {…}}`), a record with two independently jagged fields at that
  depth refuses the bare key naming the ambiguity, and m51's object-migration anchor states that it
  writes the MULTI-FIELD record. §6.4d and the anchors appendix follow.
  **MID** — **§2.6b's context-identity illustration is respelled** to the op-level
  `graphed.nominal(sel).MET.pt + graphed.nominal(sel).MET.phi` (the form m48's anchor freezes);
  r23's `h.fill(…MET.pt, …Jet.pt)` was the mixed-granularity fill §6.1d r19 twice removed as
  unexecutable (measured, bh 1.8.0: `ValueError: spans must have compatible lengths`).
  **LOW** — §2.2 binds `graphed.nominal` on the two RESULT shapes (≡ `graphed.universe(x,
  "nominal")`; identity for a bare unvaried hist, `x["nominal"]` for a mapping, the nominal SLICE
  for an axis-mode hist) and m50's (i-bis) anchor asserts it. §2.1's stacking rule states the
  TWO-LEVEL §2.4 resolution a nested `Varied` weight factor needs (container's member for L, then
  that member's own L), with §2.2 noting the composed ambient stays flat. §6.4c's bit-exact
  reconstruction is scoped to the levels SUPPLIED through `select=`, with §6.4e's manifest recording
  which those are. §6.1d(B) marks the reindex_to ORDERING half knowingly UNANCHORED and names the
  two-link value that would anchor it. §9.1 fixes `graphed.variations`' kind vocabulary
  (`"weight"`/`"shift"`), return type and freeze pinning; m50's anchor asserts both strings. m48's
  §7.2 (α) anchor and §7.2's r20 sentence stop naming a `CompiledGraph.outputs()` that does not
  exist (measured: fields `ir`/`source_names`, only method `evaluate`,
  `python/graphed/execute.py:36-52`) — the working spelling is
  `GraphStore.deserialize(compiled.ir).outputs()`. m49's §8.2(i) bullet names its two directories
  (`frontend/m49` accessor half, `checkpoint/m49` plan-byte half). §10's "three m48 anchors carry a
  non-empty `S`" is corrected to TWO (§2.3b's anchor performs no fill, and `S` is a property of a
  fill).
- **r23 (2026-07-30)** — review round 14 (three independent r22 reviews: facts / design / tests,
  `systematics-vary-plan-review-r22-{facts,design,tests}.md`; 21 findings after NIT exclusion, 19
  unique after merging two cross-lens duplicate pairs (the `mypy --strict on src AND tests`
  mis-citation, facts+tests; the §8.2(i) closure-field milestone propagation, design+tests) —
  0 BLOCKER, 1 HIGH, 8 MID, 10 LOW). Every
  finding re-verified in-session against the pinned verification roots before acting; audit trail in
  `systematics-vary-plan-revision-r23-notes.md`. **Nothing rejected, nothing deferred** — no
  finding's resolution required reversing an owner-locked decision.
  **HIGH** — **§2.6b binds CONTEXT HANDLE IDENTITY, which nothing defined while three rules compare
  handles** (§2.3e's op-level divergence error, §6.1d(A)'s `unify_contexts`, and §6.4a(2a)'s literal
  `graphed.context_of(select_mask) is graphed.context_of(record)`): PURE DERIVATIONS ARE CANONICAL —
  `graphed.nominal(c)`, `graphed.universe(c, L)` and `c[mask]` for the same mask return the SAME
  context object, memoised on the parent, while `graphed.vary` always returns a fresh one. Without
  it the natural fresh-object-per-call implementation makes two reads of one universe SIBLINGS and
  the divergence error fires on programs this plan scopes (r24 respells r23's illustration, which
  was a mixed-granularity fill §6.1d r19 forbids: `graphed.nominal(sel).MET.pt +
  graphed.nominal(sel).MET.phi`; `sel1 = events[mask]; sel2 = events[mask]`) — a FALSE refusal, the
  §2.5 confidently-wrong class, with the implementer's coin-flip frozen read-only; m48's op-level
  divergence anchor gains the two-`graphed.nominal(sel)`-reads positive control.
  **MID** — **§6.4a(2a)'s predicate admits `vary` IDENTITY links explicitly**: r19–r22's bare handle
  equality is strictly NARROWER than the r16 rule it claimed to subsume, because §2.3e's ORIGINATION
  rule gives a read through `E2 = graphed.vary(E1, …)` the handle `E2` while a read through `E1`
  carries `E1` — identical row spaces, different handles — so `to_parquet(E1.Jet,
  select=graphed.selection(E2[mask]))` was refused; the "becomes automatic" sentence is withdrawn
  and m51 gains a sixth control (the five existing ones decide identically). **§6.1d binds what
  `unweighted=True` does to the LABEL SET** — a suppressed weight contributes NO labels, so such a
  fill is UNVARIED and returns a bare `hist`; m48's anchor ("counts equal to an unweighted eager
  reference") was satisfied by both readings. **§6.4a's row-rule sentences are swept to r22's
  FIELD-SCOPED level keys** — "one entry per level that varies" / "one packed mask per supplied
  LEVEL" contradicted the Jet+Muon record r22's own rationale requires TWO depth-1 entries for.
  **§1.1's family example and m48's grammar anchor are re-spelled in a LEGAL overload** (the weight
  form): with an event-context target and no `is_weight` the call is overload (c), in which
  `variations=` is REJECTED, so the frozen anchor would have asserted the wrong rejection; §1.1 also
  states where a context's per-`name` tag map lives. **r22's m48/m49 milestone correction for
  §8.2(i)'s closure field is propagated to the places r22 missed**: m48's target line gains the FIELD
  DECLARATION (m49's `§8` excepts it), m48's §7.2 schema-absence anchor stops attributing the change
  to m49, and §7.2's "(β) carries its anchor at m49" becomes channel-at-m48 / payload-at-m49.
  **§10 analyses `uproot5-graphed-mvp`'s GATES for m51's ROOT half** — measured at `393ecef`, the new
  frozen tree is collected (`pyproject.toml:136`) but the only workflow running it has no `--cov`
  (`graphed.yml:55`), no `[tool.mypy]` anywhere, ubuntu + 3.11/3.12 only and no `pull_request`
  trigger, so the DoD's coverage / type / R0.5 matrix gates cannot be discharged for "the larger half
  of m51"; m51 now binds the cov invocation, the mypy config and an explicit matrix statement.
  **m48's §4.1 correctionlib digest is re-measured with its payload NAMED** — `sha256:e72c0da3…` over
  `agc.correctionlib_json()` at `scale=1.0`; the r22 literal `sha256:cae4dd4b…` named no payload and
  does not reproduce at the pinned revision, so it is withdrawn (the substantive observable — one
  shared payload hash, `systematic` the only differing param — is unchanged and re-verified).
  **LOW** — §7.3's and the appendix's cloudpickle digest pair `8d058bf867dc6bcd` /
  `22a566276fd6077d` is WITHDRAWN for the same non-reproducibility reason §7.3 used against
  `80e8024dc8f3b77d` (an r23 probe of the same shape gives a different pair); the qualitative shape
  binds. §7.2's "measured, `graphed pyproject.toml:83` → `strict = true`" is re-cited to R0.4a
  (`graphed-root-prompt.md:147-153`), the actually-binding source, with the measured src-only state
  recorded (`files = ["python"]`, `:84`), and m48's (α) anchor names its READ-BACK ROUTE (`Plan.process`
  is declared `Callable[…]`, `core/execution.py:210`, so the field is read off the concrete
  `_PartitionReduce`). §2.3d/§6.1d's `reindex_to` label rule is restated as SEQUENTIAL link
  composition (r22's set expression is order-insensitive while §6.1d composes in lineage order).
  m48's target line drops the false "m48 has weight labels only, so `|S| = 0`" (three m48 anchors
  carry a non-empty `S` — **corrected to TWO in r24**, §2.3b's anchor performs no fill) for the
  true reason. §2.2 enumerates all FOUR input shapes its verbs carry.
  §2.3e records that the slot-KIND vocabulary is frozen at m48 (a sixth kind needs a Test Dispute),
  the shape r18 used for `refusing == {gak.join}`. m50's mixed-mode anchor gains a fourth output
  (axis-mode, unvaried) so r22's `(output, None)` rule is witnessed. m49's §3.4 impact-set anchor
  states its fixture, since interning admits exactly one construction (`vary(x, "jes", up=e,
  down=e)`) — **WITHDRAWN in r24 as measurably false: the shared-UPSTREAM construction exists and
  is the discriminating one**. Stale spans corrected: `boost.py` `plan` `:256-295` and `Histogram.plan` `:244-253`,
  `_GroupReduce.__call__`'s annotation `:108`, `graphed.numpy`'s `to_parquet` `:182-191`, `graphed
  pyproject.toml`'s `pythonpath` `:115-127`, `graphed-executors ci.yml:101/:153` as per-milestone
  (not whole-tree) runs, the `read_columns` appendix row's `:123`/`:143-144`, and the appendix row
  still attributing §7.3's churn to m49.
- **r22 (2026-07-30)** — review round 13 (three independent r21 reviews: facts / design / tests,
  `systematics-vary-plan-review-r21-{facts,design,tests}.md`; 19 findings after NIT exclusion, 18
  unique after merging one cross-lens duplicate pair — 0 BLOCKER, 0 HIGH, 8 MID, 10 LOW). Every
  finding re-verified in-session against the pinned verification roots before acting; audit trail in
  `systematics-vary-plan-revision-r22-notes.md`. **One finding REJECTED on measured counter-evidence;
  nothing deferred** — no finding's resolution required reversing an owner-locked decision.
  **MID** — **The §8.2(i) closure field's MILESTONE and TYPE are both corrected.** r21's (β)
  return-channel binding puts the field on `_PartitionReduce` at **m48** (m48's (α) anchor freezes a
  returned dummy being readable off `plan.process`), so §7.3's "one-time churn on landing m49" and
  m50's FROZEN docs anchor named the wrong milestone — measured r22 (cloudpickle 3.1.2), the same
  module-level dataclass with vs without one defaulted field digests `8d058bf867dc6bcd` vs
  `22a566276fd6077d`, i.e. the churn lands when the field is ADDED; m49 only populates it. The field
  is declared `… | None = None` and m48's dummy is bound to the empty tuple `()`, so the anchor
  type-checks under the DoD's `mypy --strict` on tests (`graphed pyproject.toml:83`) and m49's
  declared type cannot red a frozen m48 test. **§2.3d/§6.1d's `graphed.reindex_to` label rule is
  scoped per LINK KIND** — the §2.4 union with the intervening MASK-derivation links' labels, minus
  every label a universe/nominal PROJECTION link eliminates — r21's unconditional "union" is false
  across a kind-(3) link, whose own clause yields an unvaried value and on which m48's BARE-`hist`
  `graphed.nominal(sel)` anchor depends; m48's lineage-seam anchor is split per kind so the two
  readings cannot both be frozen. **§6.4a's level-≥1 `select=` channel is FIELD-SCOPED** — **except
  where the level-k structure is the RECORD'S OWN, which takes the bare depth `k`, r24: measured,
  the single-collection skim's form is `var * {pt: float64, eta: float64}` (one level-1 structure,
  no field path to name) versus `{Jet: var * {…}, Muon: var * {…}}` for the multi-collection record**
  (`{0: evt, ("Jet", 1): jet_mask}`): "the record's own offsets at that depth" is not single-valued
  for the mixed-depth record §6.4b/m51 put in scope (a depth-0 `graphed.weight(c)` beside a depth-1
  collection) nor for a two-collection record, so the writer would validate a jet mask against muon
  offsets; §6.4d gains the shallower-fields sentence and m51's round-trip anchor states its coverage
  items may be separate fixtures. **m48's four-way fold-order anchor gains m50's `sample=` storage
  pin** (re-measured r22, bh 1.8.0: `TypeError: Keyword(s) sample not expected` on `Double()` AND
  `Weight()`; `Mean`/`WeightedMean` accept) or must say it is record-time only — otherwise it dies at
  EVALUATION post-freeze. **m49's §5.3 conservative label rides a SEPARATE program**: measured,
  `read_columns` carries ONE conservative flag across all arrays passed and returns `None` if any
  consumes the whole record (`projection.py:130-146`), so a conservative label in the same program
  collapses the union and makes the growth half vacuous or red. **§2.3e's propagation slots declare
  their operand KIND** and the frozen test owns one contexted `Array` per kind — measured, one
  jagged-numeric primary serves `num`/`unzip`/`drop_none`/`singletons`/`unflatten`/`where` but
  `gak.with_field` raises `GraphedTypeError`. **m51 gains the §6.4f write-path merge-refusal
  anchor**, binding source §6.4f settles and no anchor covered (`to_parquet` compiles at the call,
  `awkward/io.py:230-231`).
  **LOW** — §1.1's compared quantity is defined under BOTH renderings (r21's digit-count-plus-sign
  form is the rendered length only for INTEGER-valued inputs; a long-mantissa fractional value has a
  smaller normalized count than its rendering) and the two refusals split by CAUSE, so `"-1.5e31"`
  gets the canonical-tag-LENGTH message rather than a magnitude message blaming a magnitude the
  adjacent m48 anchor certifies as legal — verdicts unchanged, message class only. §6.4a's (2c)
  depth check generalizes to every supplied level (a too-shallow level-1 mask leaves the structural
  check with no operand). §1.2's §6.2 carve-out widens to name §6.2's r15 per-fill variation payload,
  the second channel putting a label into a content hash. §6.1a's bare-key rule is scoped to
  SIBLING-mode outputs (the MODE decides an axis-mode key, not the variation count). §6.1c states
  that an axis-mode slot's spec is that of any gathered fill node (§6.2(i) forces them equal).
  m48's target line annotates that §6.1b's arity anchor is m49's. §6.4e's no-`awkward._connect`-import
  rule is marked knowingly UNANCHORED with its reason, the shape §7.2 already uses. Two stale anchor
  spans corrected: the m05 row carried the corpus-repo line numbers on the consolidated path
  (`:25-37` there, `:26-38` in `graphed-corpus`), and `histograms.py:39-42` opened on a blank line and
  truncated `fingerprint`'s return (`:35-37,40-43`).
  **REJECTED** — m48's §4.1 anchor "differ only in the `systematic=` param" is TRUE on the path its
  own cited fixture uses: measured r22, `graphed.preserve.record_external(…, params={"name":
  "event_sf", "systematic": syst})` (`tests/frozen/preserve/m9/agc.py:113-115`) gives three External
  nodes sharing ONE `descriptor.content_hash` and differing only in `params["systematic"]`. The
  review checked `gak.apply_correction`, which is a DIFFERENT path (`functions.py:505-509`, the
  systematic riding inside the `args` JSON); the anchor keeps its wording and gains a note naming the
  recording spelling, since a test-author reaching for the gak verb would find it unsatisfiable.
- **r21 (2026-07-30)** — review round 12 (three independent r20 reviews: facts / design / tests,
  `systematics-vary-plan-review-r20-{facts,design,tests}.md`; 13 findings after NIT exclusion, no
  cross-lens duplicates — 2 HIGH, 6 MID, 5 LOW). Every finding re-verified in-session against the
  pinned verification roots before acting; audit trail in
  `systematics-vary-plan-revision-r21-notes.md`. **Nothing rejected, nothing deferred** — no
  finding's resolution required reversing an owner-locked decision.
  **HIGH** — **§7.2's `node id → position` derivation is re-bound to the operand that exists**: the
  frontend derives it as the index of each marked record id's FIRST OCCURRENCE in its OWN ordered
  marked-id list, not "from the compiled output list" — measured probe vs `graphed-latest@ff7c607`
  (record ids `0/1/2/3/2`, `compile_ir(s, b, e, c)` → `outputs() == [1, 2]`, two values in
  first-occurrence order of the DISTINCT record ids, `s._store.outputs() == []`): the compiled
  outputs are POST-REDUCTION ids that cannot be joined to record ids until m49's §8.2(i) accessor,
  and `compile_ir` never marks the record store (the `mark_output` dedup runs when `from_reduced`
  builds the reduced store, `src/store.rs:185-200`). Consequently **§6.1c's layout is REMOVED from
  the seam's consumer list** — `plan()` already holds the list as `fill_nodes`
  (`graphed-histogram src/graphed_histogram/boost.py:281`, one line before `layout` at `:282`) — and
  m48's target line follows; the seam remains an m48 target for §7.2's merge refusal and m49's
  `variation_labels`. **§7.2's seam half (β) is bound as the hook's RETURN CHANNEL**, not a call-time
  parameter: `variation_labels` keys on post-reduction ids from the artifact the call itself produces
  (`compile_ir` at `python/graphed/aggregate.py:95`, `_PartitionReduce` built at `:96-104`), the plan
  forbids compiling twice, and §8.2(i) declares the field an immutable sorted tuple — so a see-only
  hook has no path into the shipped closure; m48's (α) anchor gains a return-payload assertion.
  **MID** — §6.1d ORDERS label-set inference AFTER the lineage step, so a value reached across a
  universe/nominal PROJECTION link contributes no labels; m48's `graphed.nominal(sel)` fixture
  accordingly asserts a BARE `hist` (two defensible shapes before, both frozen read-only). §2.3d's
  `graphed.reindex_to` labels corrected from "the SAME labels" to the §2.4 UNION with the intervening
  masks' — an unvaried value re-indexed across a `Varied` mask BECOMES `Varied`, which is exactly
  m48's own link-kind-(1) anchor (`h.fill(events.MET.pt, sel.MET.pt)`). §6.4e binds the ROUTE, not
  only the outcome: measured, `awkward_array_metadata` is produced ONLY by
  `awkward/_connect/pyarrow/table_conv.py:16,19-40` via a PRIVATE helper `ak.to_parquet` imports
  (`ak_to_parquet.py:14,417`), so the varied write MUST NOT import `awkward._connect.*` and takes the
  public write-then-re-write-with-`replace_schema_metadata` composition. m50's `sample=`-only-label
  anchor MUST use a `Mean`/`WeightedMean` storage with differing per-label samples (measured, bh
  1.8.0: `TypeError: Keyword(s) sample not expected` on `Double()` AND `Weight()`; the evaluator
  passes `sample` through at `boost.py:60-71`) — otherwise it dies at evaluation post-freeze, or is
  vacuous. m48's `context_of`-on-a-`Varied` fixture is pinned to a `vary` IDENTITY link (not a
  mask-derivation one), so it does not freeze a row-space-mismatched container as constructible.
  §2.2 SCOPES union term (b) to vary-REPLACED collections and gains an m48 program isolating term (c)
  (a loose-`vary`-varied mask, (a) and (b) empty), while r20's `vary`-link-walking half is marked
  knowingly unanchored with its measured reason.
  **LOW** — §1.1's magnitude pre-check compares the rendered canonical LENGTH (digits + 1 when
  negative), so `"-1.5e31"` gets the magnitude message rather than the generic cap error, with the
  case added to m48's boundary pair. The unreproducible `80e8024dc8f3b77d` digest is WITHDRAWN from
  §7.3 and m49's anchor (it named no module/class/field names; re-measured r21, the qualitative shape
  reproduces and §8.2(i)'s named triple reproduces exactly). §6.4a gains predicate **(2c)**: a
  level-0 `select=` mask must be FLAT (a jagged one passes (2a) by ORIGINATION and (2b) by outer
  length, then filters objects instead of rows), with an m51 negative control. §7.2's "MUST NOT
  compile a second time" is marked knowingly unanchored against an R0.11 compile-count measurement,
  and m48's (α) anchor drops the unassertable "before the worker closure exists". §10/m48's
  `aggregate_plan`-coverage claim corrected: `graphed`'s existing frozen coverage is m5's plus m39's
  (`tests/frozen/frontend/m39/test_shuffle_plan_builder.py:58-64`).
- **r20 (2026-07-30)** — review round 11 (three independent r19 reviews: facts / design / tests,
  `systematics-vary-plan-review-r19-{facts,design,tests}.md`; 19 findings after NIT exclusion, 17
  unique after merging two cross-lens duplicate pairs — 3 HIGH, 8 MID, 6 LOW). Every finding
  re-verified in-session against the pinned verification roots before acting; audit trail in
  `systematics-vary-plan-revision-r20-notes.md`. **Nothing rejected, nothing deferred** — no
  finding's resolution required reversing an owner-locked decision.
  **HIGH** — **§6.1d gains the two LINEAGE SEAMS its fill-side unification needs across the package
  boundary**, `graphed.unify_contexts(*handles)` and `graphed.reindex_to(value, ctx)` (read-only,
  m48, listed in §9.1 and on m48's target line, anchored in `graphed`'s half): §2.3e fixed this
  class once for the HANDLE (`context_of`) but nothing exposed the RELATION between two handles or
  the intervening masks, `graphed.selection` is m51, and m48's re-indexing/projection anchors are
  assigned to `graphed-histogram` — where `Histogram.fill` lives
  (`src/graphed_histogram/boost.py:153-212`, a different distribution) — so they were satisfiable
  only by reaching into `graphed`'s private context object.
  **§6.4a's absent-operand case (ii) re-expressed over the operand r19's predicate reads** — "the
  mask carries NO context handle", not "derived no context": a mask recorded from reads THROUGH the
  record's own context carries that handle (§2.3e ORIGINATION) and derived no context, so handle
  equality ACCEPTS it while (ii) and m51's anchor refused it, freezing a hard block on a legal skim
  spelling; the accepting case is m51's new fifth positive control.
  **§7.2's r19 `aggregate_plan` seam is bound ADDITIVE, over the `CompiledGraph`, and anchored per
  repo**: the "factories over the compiled output ids" illustration would have changed the meaning
  of `reduce`/`empty`, which frozen m5 passes as plain callables
  (`tests/frozen/frontend/m5/test_aggregate_plan.py:77,88,102`) — an integrity violation or a Test
  Dispute — and an id list cannot serve m49's `variation_labels`, which keys off the compiled
  artifact; (α) now carries a `graphed`-side m48 anchor (no other `graphed` m48 anchor calls
  `aggregate_plan`, and r19's `dataclasses.fields` re-wording removed the last plan-shaped one) and
  (β) is anchored at m49 with §8.2(i).
  **MID** — `graphed.context_of` of a `Varied` answers the CONTAINER's (most-derived) handle, not
  the nominal member's: §2.1 accepts members whose handles differ along one ancestry chain and
  checks form/Session/source but never row space, so this is the one per-member property the plan
  does not require to agree, and §6.4a(2a)'s predicate reads it. §2.1(b)'s row-space violation half
  is made TOTAL — a DESCENDANT-handled factor is a construction-time error naming the direction (it
  is not divergent, so nothing caught it; `record_op` validates only `op_form`,
  `python/graphed/session.py:142-168`) — with an m48 negative control. §2.2's third
  `graphed.labels(ctx)` union term becomes `graphed.selection(ctx)` in §9.1's sense, which walks
  `vary` identity links (the §2.6 sketch's own `sel` is `vary`-derived, for which "the mask that
  derived it" had no value). §10's "needs a fill ⇒ `graphed-histogram`" rule is promoted to a
  general m48 splitting rule and the §7.2 merge-guard's VARIED half is moved there explicitly (its
  SITE is `plan()`, `boost.py:256-292`). §6.1b states WHERE the `S`/`W` split is witnessable —
  sibling arity is class-blind, so m50's equality anchor gains a `sample=`-only label. §1.1's
  digit-count normalization gains its cap-BOUNDARY pair in m48's grammar anchor (`"1.5e31"` accepted
  at 32 plain digits, `"1.5e32"` rejected; `"1e40"` alone is passed by the naive off-by-one).
  **LOW** — §2.2 records that `Varied` retains a per-`name` tag map (§1.1's family check has no
  other operand); m49's target line gains §9.1's projection-stats verb and seam (β); §2.3d states
  that the m49 verbs enter the table *expanding*; m48's property-classification fixture is pinned
  1-D (measured: `gnp.ones(s, (4, 3)).T` raises `GraphedTypeError`, partitioned-axis displacement);
  m48's §6.1a positive control is re-worded — `plan()`'s declared return type WIDENS to the
  union-key form (`boost.py:262`), only the runtime bare keys are unchanged; m49's §8.2(i)
  cardinality clause is scoped to the base fixture (re-measured: base `2N + 2` / `N + 1` stages,
  unchanged by the dead branch, but `2N + 3` / `N + 2` with the shared-node extension).
- **r19 (2026-07-30)** — review round 10 (three independent r18 reviews: facts / design / tests,
  `systematics-vary-plan-review-r18-{facts,design,tests}.md`; 22 findings after NIT exclusion, 19
  unique after merging three cross-lens duplicate pairs — 2 BLOCKER, 6 HIGH, 3 MID, 8 LOW). Every finding
  re-verified in-session against the pinned verification roots before acting; audit trail in
  `systematics-vary-plan-revision-r19-notes.md`. **Nothing rejected, nothing deferred** — no
  finding's resolution required reversing an owner-locked decision.
  **BLOCKER** — **§2.2's property rule splits by MECHANISM, not by `isinstance(m, property)`**: r18's
  premise ("every other property is answered EAGERLY … already answered from the form and never
  recorded") is false for `T`, which is `@property def T: return self.transpose()` over
  `record_op("transpose", …)` (`python/graphed/numpy/array.py:156-161`) — measured on
  `graphed-latest@ff7c607`, discovered properties `['T','dtype','ndim','node_id','session','shape']`
  with `dtype`/`ndim`/`shape` at `node_count()` delta 0 and `T` at delta 1 — so the r18 m48 gate
  froze an assertion a correct `Varied` must fail, and read literally the rule made `varied.T` drop
  every non-nominal universe. Three classes now: `node_id`/`session` raise; a form-answered property
  is eager; a RECORDING property takes its method's §2.3a disposition (`T` → broadcast). The m48
  anchor names `varied.dtype` AND `varied.T` and classifies by measured delta.
  **§6.1a's flat slot keying is SCOPED to outputs a variation reaches**: r18's unqualified binding
  re-keyed a wholly UNVARIED group plan's value to `{(output, "nominal"): hist}` — sibling mode is
  every program's default — which breaks the already-frozen m23 suite (`graphed-histogram
  tests/frozen/m23/test_group_plan.py:74-75,86,89,99` all index by bare output name) that §10 binds
  unchanged, and changes `plan()`'s declared `Plan[dict[str, bh.Histogram]]` under `mypy --strict`.
  An unvaried output keeps its bare key; m48's §6.1a anchor gains a wholly-unvaried positive control.
  **HIGH** — **m49's §8.2(i) image-cardinality clause corrected N+1 → 2N+2** (of which N+1 are of
  kind `stage`): the accessor is bound over EVERY surviving record id, and re-measured r19 the §3.3
  topology reduces to `{source: 1, stage: N+1, reduction: N}` — N=16 → 17 stages / 34 reduced,
  N=128 → 129 / 258, exactly the `reduced_nodes == 2N + 2` §3.3 itself pins; the companion clause
  widens to "a node id of the compiled reduced store", since the source is neither output nor stage.
  **§6.4a(2a) re-expressed over the operand that exists** — `graphed.context_of(select_mask) is
  graphed.context_of(record)`: r16–r18 required a DOWNWARD search over the record context's
  descendants, while §2.6b binds lineage parent-ward only and nothing maps a mask back to a context,
  so neither (2a) nor absent-operand case (ii) was decidable; handle equality decides all four m51
  controls identically, preserves both absent-operand cases, and makes the `vary`-identity-link
  admission automatic (r17's per-label node-id rule is withdrawn with the search it served).
  **§2.1(b) gains a ROW-SPACE contract on a registered weight factor** — it must live in the target
  context's row space, an ancestor-handled factor is re-indexed per §6.1d's link kinds — because
  `record_op` validates only `op_form`, never lengths (`python/graphed/session.py:142-168`), so a
  parent-computed factor stacked into a derived context's registry records cleanly and dies at
  execution outside §6.1d's refusal contract; the invariant `graphed.weight(ctx)` answers in `ctx`'s
  row space is what §6.4b's r18 precondition already assumed. **§7.2 binds the `aggregate_plan`
  SEAM** three requirements need — §6.1c's index layout, §7.2's own merge refusal and m49's
  `variation_labels` all want the compiled artifact at a site that lacks it (measured:
  `aggregate_plan` compiles internally at `aggregate.py:95` and takes pre-built closures; `plan()`
  builds `layout` at `boost.py:282` BEFORE calling it) — with an explicit "MUST NOT compile twice".
  **m48's §7.2 schema-absence anchor re-worded to LITERAL expected key sets**: all three schemas are
  dataclasses with class-level field lists (`core/execution.py:206-217,219-224,335-351`; `emit_task`
  passes the `TaskEvent` instance, `:378-384`), so the varied-vs-unvaried comparison is equal by
  construction — including after a field is added — the §6.3 repair r17 made for params, applied here.
  **MID** — §6.1b/§6.2 define `S`/`W` by LOWERING behaviour, so a label borne only by a `Varied`
  `sample=` (first-class since r15, frozen ACCEPTED in m48) has a class: it needs a sibling fill node,
  keeping both frozen arity formulas correct. §6.1c's per-output MODE field is DELETED and §9.1's
  `unpack(value)` stays one-argument: the three slot key forms are disjoint and per output, so the
  shape is read off the keys even in a mixed plan — the field was unwitnessable and forced §9.1 to
  contradict §6.1a's "value plus the layout" (measured, the layout is unreachable from the executed
  value); m50's mixed-mode anchor is re-headlined as the unpacking/per-slot-spec anchor it is.
  m48's two mixed-granularity fill fixtures are restated at SAME granularity (`sel.Jet.pt` →
  `sel.MET.pt`, `graphed.nominal(sel).Jet.pt` → `.MET.pt`): the evaluator flattens each axis
  independently (`boost.py:39-47,60-71`) and bh requires equal lengths across axes — measured, bh
  1.8.0, `ValueError: spans must have compatible lengths` — so both anchors named programs that
  cannot execute, for a reason unrelated to what they assert. m48's gak floor drops r16's stale
  "the refusing class is exactly `{gak.join}`" for §2.3e(3)'s r18 containment + monotone count.
  **LOW** — m48's target line excepts §2.5's shift-after-weight diagnostic (m49) and adds
  `graphed_histogram.unpack` to its §9.1 list; §6.1d binds `unweighted=True` (suppresses ambient AND
  explicit factors; both in one call is a record-time error) with the answer named in m48's anchor;
  the §2.6 sketch's b-tag SF takes the pt-CUT jets (`sel.Jet[sel.Jet.pt > 25]`), matching
  `graphed-corpus …/systematics.py:60-76,25-36`, with the note repeated in m48's matrix anchor;
  §1.1's integer-magnitude digit count states its normalization (naive "mantissa digits + exponent"
  is off by one at the cap for a dotted mantissa); m48's §1.2 anchor drops "or token" (measured:
  `GraphStore.nodes()` exposes no token) and recurses into a stage's `members`; citations corrected
  `projection.py:146-147` → `:145-146` and `boost.py:205-212` → `:196-210`.
- **r18 (2026-07-30)** — review round 9 (three independent r17 reviews: facts / design / tests,
  `systematics-vary-plan-review-r17-{facts,design,tests}.md`; 24 findings after NIT exclusion —
  1 BLOCKER, 5 HIGH, 11 MID, 7 LOW; three cross-lens duplicate pairs merged). Every finding
  re-verified in-session against the pinned verification roots before acting; audit trail in
  `systematics-vary-plan-revision-r18-notes.md`. **Nothing rejected, nothing deferred** — no
  finding's resolution required reversing an owner-locked decision.
  **BLOCKER** — **§6.1a vs §6.1c settled in §6.1c's favour**: r17 bound two incompatible shapes for
  the same m48-frozen object ("the combine BRANCHES on the two shapes" vs "The COMBINE needs no
  branch"), and m48 freezes both ends. Binding now: the plan's COMBINED value is the flat
  slot-keyed `{(output, label|None) → bh.Histogram}` mapping with `_add_groups` staying a
  homogeneous key-wise `+` (measured, `graphed-histogram src/graphed_histogram/boost.py:120-122`),
  and §6.1a's `{output: hist | {label: hist}}` is the shape of a NAMED unpack surface.
  **HIGH** — **that unpacker is bound** (`graphed_histogram.unpack(value)`-shaped, spelling pinned
  at m48 freeze, listed in §9.1, and m48's §6.1a anchor is worded over it and freezes the plan
  value's slot shape in the same anchor): measured, there is no seam to hang it on — `Plan` has no
  finalize hook and `ExecResult.value` IS the combine output
  (`python/graphed/core/execution.py:206-224`), `plan()` returns that `Plan`
  (`boost.py:254-292`), and adding a `Plan` field is foreclosed by §7.2's own m48 schema-KEY-SET
  anchor. **§6.4b gains a ROW-SPACE precondition** — a stored varied field must live in the record's
  own row space, so `graphed.weight(ctx)` is storable only across `vary` IDENTITY links and a
  SELECTION-scoped weight is refused (§2.6c gives it per-label row sets while the record is
  pre-selection on superset rows and a mask has no inverse); §6.4a(2a)'s r16 justification is
  softened accordingly (admitting `vary` links stands on m51's bridge anchor instead).
  **m48 no longer freezes `to_parquet`'s §2.3d disposition** — it carries none until m51 (measured:
  no `select=` parameter today, `python/graphed/awkward/io.py:206-216`; outside `graphed.__all__`,
  so the dynamic half never reaches it), removing a frozen entry m51 is bindingly required to change
  and an m48 refusal behaviour no m48 anchor asserted; the per-class floors are re-worded as
  CONTAINMENT, never exact sets. **m49's two `DurablePlan` anchors are bound to the BY-VALUE
  construction** with module-level closure operands: measured r18 (cloudpickle 3.1.2, seeds
  {1,7,12345}) `OpSpec.identity()` for `kind="ref"` is `b"ref\0"+ref`, so a `from_ref` fixture
  freezes the determinism anchor green against the very `frozenset` §8.2(i) bans, while a
  `__main__`-defined (by-value) operand makes the bytes seed-dependent for BOTH forms — red against
  a correct implementation. **§6.1d link kind (1) gets a VALUE-asserting m48 anchor**
  (`h.fill(events.MET.pt, sel.MET.pt)` elementwise against a manually re-indexed reference), the
  treatment r15 gave link kind (3).
  **MID** — §2.1 states the member-type rule once (a member may be an `Array` OR a `Varied`;
  (a)/(c) reduce to the central universe, (b) keeps it label-aligned), since "members are Arrays"
  contradicted this section's own stacking rule and its own sketch; §2.2 widens the reserved-name
  rule to a PROPERTY discovery rule (`shape`/`dtype`/`ndim`/`T` are plain properties
  `inspect.isfunction` never enumerates, `python/graphed/numpy/array.py:78,82,86,160`) with the
  property half added to the §2.3a gate and `varied.dtype` named in m48's parity anchor; §7.2's m48
  optimizer-merge refusal gains a SITE (the `(output, label)` map's owner — the group-plan builder)
  and a SCOPE (varied programs only) plus an m48 positive control for the unvaried merged case;
  §6.4f binds the widened `_WritePart` unpack to §7.2's node-id resolution with the id→position
  table as a `_WritePart` field, and m51's round-trip anchor witnesses the replication; §3.3's
  frozen wall-clock bound moves 24.0 → **16.0** (re-measured r18: the topology's nodes grow 5.37×
  and time 5.64× from N=16 to N=128, so m4's literal — sized for an 8× span — left only 1.2×
  against a node-quadratic reducer); m49's §8.2(i) accessor anchor gains an image-cardinality
  clause (exactly N+1 distinct reduced ids) that a degenerate constant map fails; m51's bridge
  anchor gains the re-recorded-equal-expression positive control for §6.4a(2a)'s node-id rule; m50
  gains a MIXED-MODE plan anchor (the per-output MODE's only reason to exist) and its target line
  drops the design r17 withdrew; m48's broadcast anchor gains the contexted-but-unvaried third
  assertion §6.3(2)'s disjunction exists for.
  **LOW** — root-prompt Out-of-scope anchor corrected `:1285-1286` → `:1286-1287` (`:1285` is blank;
  body, §12.3(b), appendix, and the r17 history line); §1.1's integer-magnitude check runs on the
  computed DIGIT COUNT before rendering; §2.1's construction checks add context-handle unification
  (with an m48 anchor clause) since `vary` is a combining point no `_array_cls` chokepoint sees;
  m49/m51 target lines gain the sections their anchors freeze; §2.3e(3)'s refusing class becomes
  containment + a monotone count instead of `== {gak.join}`; m50's declaration-anchor circularity
  parenthetical re-worded ("DERIVES FROM", stale since r17 re-ordered `graphed.labels(h)`).
- **r17 (2026-07-30)** — review round 8 (three independent r16 reviews: facts / design / tests,
  `systematics-vary-plan-review-r16-{facts,design,tests}.md`; 24 findings after NIT exclusion —
  0 BLOCKER, 2 HIGH, 11 MID, 11 LOW). Every finding re-verified in-session against the pinned
  verification roots before acting; audit trail in `systematics-vary-plan-revision-r17-notes.md`.
  **One sub-item rejected with counter-evidence, nothing deferred** — no finding's resolution
  required reversing an owner-locked decision.
  **HIGH** — **the checkpoint-churn claims are SCOPED**: `_PartitionReduce`/`_WritePart` are the
  `process` of the in-memory `graphed.core.execution.Plan` — a plain
  `Callable[[Partition, WorkerResources], R]` with no `identity()`/`task_id`
  (`core/execution.py:206-217`) — NOT a `DurablePlan` `OpSpec`, and no `Plan → DurablePlan` bridge
  ships (`grep -rn "DurablePlan(" python/` → 0; `OpSpec.from_callable` only at
  `shuffle.py:181,188,245,259`; `graphed-executors/src` → 0 `task_id`/`DurablePlan`), while the
  documented idiom embeds the USER's functions by reference
  (`OpSpec.from_ref("myanalysis:hist_chunk")`, `docs/checkpoint/design.rst:20,58-65`), so r13–r16's
  "every existing checkpoint journal … including for *unvaried* programs" and the m51
  "every existing WRITE-plan journal" are withdrawn: m49's churn is scoped to journals whose
  `process` spec embeds the closure BY VALUE, write plans have no journal at all, the label-RENAME
  class inherits the same scope, and §7.3's m49 interrupt/resume anchor now names its `DurablePlan`
  construction path (`run_resumable` needs one, `checkpoint/runner.py:77-91`); the m50/m51 DOCS
  anchors and two appendix rows are re-worded so the unconditional claim is not frozen into user
  docs. **§7.2's `node id → position` derivation gets an m48 REFUSAL for optimizer-merged outputs**
  — measured, the M4 reducer merges DISTINCT record ids (`engine.rs:22-31,67-110`): `w` vs `w*1.0`
  compile to one output (4 record ids → 3 values), and on the fill path two `Histogram.fill`s
  differing only in `weight=[w]` vs `weight=[w*1.0]` give fill nodes 2 and 4 → `outputs() == [2]`,
  the exact `_GroupReduce` mis-slice §6.1c exists to prevent, from a source record-time interning
  cannot see (and §1.1 makes `w * 1.0` a natural μR/μF member). m48 compares distinct compiled
  outputs against distinct marked record ids and raises with a named workaround; the m48 §1.2 dedup
  anchor gains that case; full support is parked in §11 (it needs §8.2(i)'s m49 map).
  **MID** — §6.2(i-bis) binds `graphed.labels(h)` to §2.2's order (nominal first) over a
  lexicographically stored axis; §5.3/§9.1/§2.3d bind `tuple[str, ...] | None` (measured:
  `read_columns` returns `None` = "read every column", `projection.py:145-146`) and the `Varied`
  union is `None` if any member's is; §6.2(i) makes the fill MODE a property of the histogram (first
  fill fixes it, the other mode is a hard error); §6.2's "a shift sibling MAY target the same axis"
  becomes binding (the MAY contradicted its own `1 + |S|` arity, §6.1c's one-slot rule and m50's
  frozen equality anchor); §1.1 DEFINES "family" (one `name`'s tags on one container including
  inherited labels) so the cross-notation numeric-equal check spans stacking calls; §2.3d's named
  floor list gains `graphed.context_of` + `graphed.broadcast_like` (measured: the annotation-wide
  discovery yields 8 verbs, all refusing/expanding, so these two are the sole representatives of
  *eager-metadata* and *broadcasting*) and `to_parquet` is classified *refusing* at m48 —
  `select=` is §6.4, an m51 target — with the per-class floor scoped to the classes a repo's table
  can host at that milestone and the m48 *accepting* representative being `Histogram.fill`;
  §8.2(i)'s `variation_labels` re-declared over the PAIR key `(reduced_node_id, member_index)` it is
  bindingly looked up by; m50's plan-level `{output: [labels]}` anchor moved to `graphed-histogram`
  (named outputs exist only in its group API, `boost.py:256-292`, and `graphed` would
  `importorskip`-SKIP it); §2.3e(2)'s propagation fixtures re-bound as TEMPLATES with a substitution
  SLOT (`gak.zip`'s mapping is its only array-bearing operand, `functions.py:118-119`, so the
  container-traversing class otherwise degrades to `None == None`); m51 gains anchors for
  `graphed.selection` on a universe/nominal-derived context and for (2a)'s refusal of it as
  `select=`.
  **LOW** — §2.6c states the central idiom rule (a read through a derived context is the parent's
  value re-indexed by the derivation mask, label-aligned); m48's expanding-verb anchor worded per
  verb (`read_columns` returns the UNION, not a per-label mapping); m50's listing anchor picks
  `["nominal"]` over the r16 either/or; §6.4b says "every stored field that IS `Varied`
  (structurally, at record time)" so the augmented column set cannot become per-partition;
  §6.1c records the per-OUTPUT MODE instead of a per-slot value type (the combine needs no branch —
  `_add_groups` is a key-wise `+`); §6.4a(2a) decides mask identity by per-label NODE-ID equality
  with object identity as a fast path; §2.1 REJECTS `nominal=` in the shift form; m48 anchors added
  for §2.6a's slice/int refusal and §1.1's integer-magnitude message; §6.3's params gate re-bound as
  a KEY-SET equality (`{"spec","n_axes","weighted","sampled"}`) because m48 adds no params key;
  line-number corrections — `boost.py:176-178`→`:175-178`, `m29/test_multi_weight_fills.py:84-86`
  →`:84-87`, `Session._provenance` "written at `:141-166`"→`:138,166,181,202,240`, the appendix
  parquet-metadata row (only `parquet.py:77` is a USE), root prompt `:1286`→`:1285-1286` (off by
  one — the sentence runs `:1286-1287`; corrected in r18) (body,
  §12.3(b) and appendix). **REJECTED**: the claim that
  `checkpoint/m8/test_resume.py:51-58` is stale — measured, `def
  test_result_is_invariant_to_partition_count` IS at `:51` and its last assert at `:57`, so the
  cited span is correct (the reviewer's proposed `:54-58` would point at the loop body).
  Anchors appendix +1 measured row (optimizer-merged distinct record ids), 2 rewritten.
- **r16 (2026-07-30)** — review round 7 (three independent r15 reviews: facts / design / tests,
  `systematics-vary-plan-review-r15-{facts,design,tests}.md`; 29 findings after NIT exclusion —
  0 BLOCKER, 4 HIGH, 13 MID, 12 LOW). Every finding re-verified in-session against the pinned
  verification roots before acting; audit trail in `systematics-vary-plan-revision-r16-notes.md`.
  **Nothing rejected, nothing deferred** — no finding's resolution required reversing an
  owner-locked decision.
  **HIGH** — **`graphed.selection` is now defined over the `graphed.vary` (identity) link** and
  §6.4a(2a) is TRANSITIVE over such links: the r15 predicate ("parent + MASK-DERIVATION link")
  refused this plan's own mainline skim shape, since §2.6's sketch rebinds `sel` through a weight
  `vary` and §6.4b's stored varied factors are reached via `graphed.weight(ctx)`, so a
  weight-storing skim is written from a `vary`-derived context by construction; m51's bridge anchor
  gains that case. **§5.2c gets §5.2a's treatment** — an independently hand-built no-`vary` ORACLE
  instead of a raw-`GraphStore` literal, and the "re-measured through the frontend at implementation
  time" escape (a post-freeze re-measurement of a read-only literal) is deleted. **§4.3's bound
  predicate is WITHDRAWN as satisfied by construction** — `reachable(selection_mask)` is contained in
  every label's fill cone in any implementation that fills selected data (`boost.py:176-178,205-212`;
  `session.py:255-286`), so the intersection is constant and a `mask_L = mask & g_L` implementation
  passes; the binding form is now the converse, the per-label fill nodes' NON-WEIGHT input ids
  agreeing with nominal's. **m48's §2.3d floor is split per repo** — `graphed` declares no
  `graphed-histogram` (`pyproject.toml:29-48` vs CI's `.[dev]`), so naming `Histogram.fill` in
  `graphed`'s table-driven test forces the house `importorskip` and SKIPs §2.3d's dispositions AND
  §2.2's reserved-name anchor; that member moves to `graphed-histogram`'s flat `tests/frozen/m48`.
  **MID** — §8.2's output-position fallback restated honestly (it needs the same missing raising-node
  identity part (iii) exists to supply; without (iii) attribution is plan-wide); §2.3d's disposition
  CLASS SET enumerated (refusing / expanding / broadcasting / eager-metadata / accepting, with
  `to_parquet`/`Histogram.fill` as *accepting*); §1.1's unconstructible "label equal to `nominal`"
  rejection replaced by a reserved-by-construction statement that agrees with §2.1's legal `nominal`
  TAG; §2.1/§2.5 bind the **shift-after-weight ordering rule** plus an m49 diagnostic (a shift `vary`
  does not re-derive the ambient registry); §7.3 documents the third invalidation class, a label
  RENAME (from m49 it changes the worker closure and every `task_id`, `plan.py:72-76,164-176`, though
  the IR is byte-identical); §6.1c's axis-mode slot scoped to m50 and added to m50's target line;
  m48's §2.6/§6.1d split restated as a RULE (any clause needing a fill lives in `graphed-histogram`)
  with the two fill-dependent halves moved; m48's fold-order anchor extended with a varied `sample=`;
  m49's §8.2(i) anchor topology extended with a node consumed by two NON-nominal universes (the
  actual set-valued-keying witness); §5.3's per-label projection-stats surface named, shaped
  (`{label: tuple[str, ...]}`) and pinned at m49 freeze, listed in §9.1; §6.4b's collision check
  re-worded derived-vs-derived AND derived-vs-stored, with the m51 fixture varying BOTH `Jet.pt` and
  `Jet_pt` (r15's example was not a collision); §2.3e(2) gives the FROZEN TEST ownership of the
  contexted primary operand (a context-free `src` fixture degrades the assertion to `None == None`);
  §10/m49's JER-SF oracle re-bound to a PLAN RUN — `Session.materialize` is partition-blind
  (`session.py:291-301`) and cannot observe `steps_per_file`.
  **LOW** — §7.1 scoped to per-variation RE-EXECUTION (§6.2's evaluator-side loop is not one);
  §2.6a REFUSES a `slice`/`int` context subscript (`Array.__getitem__` accepts both,
  `array.py:344-371`); §6.3(2)/§6.1d state ONE broadcast-seam trigger (a handle OR any `Varied`
  input); §2.3e(3)'s refusing class enumerated as `{gak.join}` (measured: gak's only boundary verb,
  `functions.py:18`) and §2.3e(4) given its own `Array`-surface floor (`{repartition}`); §9.1's
  plan-level `{output: [labels]}` listing given m50, a pinned spelling and its own anchor
  (`inspect(bundle) -> str` cannot exercise it, `preserve/bundle.py:268-288`); §5.2b's placement
  pointer corrected to the m49 `graphed-histogram` half; §2.3a states its `inspect.isfunction`
  enumeration filter; m50's user-declared-axis refusal binds the recognition rule
  (`axis.__dict__.get("name") == "variation"`); §2.3c's `__all__` claim corrected (the package
  `__all__` yields a WRONG six-name set, not an empty one); line-number corrections —
  `__init__.py:12,44`→`:12,46` (body + appendix), appendix `projection.py:109-121`→`:147`, and the
  dangling `(:590-592)` citation in §6.4a replaced by a section reference.
- **r15 (2026-07-30)** — review round 6 (three independent r14 reviews: facts / design / tests,
  `systematics-vary-plan-review-r14-{facts,design,tests}.md`; 26 findings, 23 after cross-lens merge
  — 0 BLOCKER, 6 HIGH, 8 MID, 9 LOW; two defects were raised by all/most lenses and are merged:
  §2.3d's discovery rule still missing `compile_ir` (facts+design+tests) and §5.2c's raw-`GraphStore`
  binding (design+tests)). Every finding re-verified in-session against the pinned verification roots
  before acting; audit trail in `systematics-vary-plan-revision-r15-notes.md`. **Nothing rejected,
  nothing deferred** — no finding's resolution required reversing an owner-locked decision.
  **HIGH** — **§2.3d's discovery rule unions an explicitly NAMED floor list containing
  `graphed.compile_ir`** (measured: the r14 annotation-wide filter over `graphed.__all__` discovers
  8 verbs and still misses `compile_ir`, whose parameters are annotated `Session`/`Any`,
  `execute.py:54-58`, while it IS in `__all__` — so r14's "named non-`__all__` members" hatch reached
  it through neither channel and the m48 gate could assert no disposition for one of the two
  safety-bearing compile/aggregate verbs); the filter is restricted to `inspect.isfunction` and
  excludes `graphed.vary` (m48's own export, otherwise discovered with no disposition class);
  `aggregate_plan`'s "ambiguous" parenthetical softened. **§6.1d's ancestor re-indexing restated PER
  LINK KIND** (mask → re-index; `vary` → identity; universe/nominal → project to that label) — r14's
  mask-only rule had no operand for the non-mask links r14 itself introduced, on this plan's own
  example. **§6.2 binds a per-fill variation CARRIER** — measured, an External evaluator resolves by
  `content_hash(spec)` alone (`boost.py:180-212,283-286`; `execute.py:116-124`) and §6.2's cross-fill
  rule forces one spec per axis-mode histogram, so all `1 + |S|` fill nodes would resolve to one
  evaluator (last registration wins); the payload now enters the `FillEvaluator` AND the content
  hash, with an m50 witness. **§6.4a(2a) bound for both ABSENT-operand cases** (context-free record →
  skipped, keeping the loose §2.1a sink reachable; contexted record + context-free mask → refused),
  with the loose write as an m51 positive control. **§5.2a's arena-delta SPAN and ORACLE re-bound**:
  bracketing the `vary` call cannot observe `K+2` under record-time expansion, and "re-measure at
  freeze through the frontend" is unfollowable before an implementation exists — the span is now
  complete-N=1 vs complete-N=2 in one Session and the oracle an independently hand-built second
  universe. **§2.3a's parity gate binds the per-name ASSERTION** (class lookup + one behavioural
  probe per disposition class) — an instance `hasattr` is answered for every name by `Varied`'s
  label-mapping field access (`array.py:332-335`), so the r12–r14 enumeration-only gate was vacuous
  exactly where §2.3a says it matters. **§5.2c moved off the raw-`GraphStore` §3.3 fixture** to the
  frontend `vary`-built program in `tests/frozen/frontend/m49` (measured: `m4/test_benchmark.py`
  builds with `import graphed.core as gc`), resolving its double placement too.
  **MID** — §6.1c binds the AXIS-MODE slot (`(output, None)`, one per output, value type in the
  layout) and m50's scaling anchor is scoped to weight labels; §6.4b binds the FIELD half of
  `__vary_{label}__{field}` (per-level flattening + collision refusal + manifest as sole resolver),
  with an m51 nested-field anchor; §5.5(a)'s partition-invariance witness compares smeared VALUES and
  selection MASKS, never a weighted float histogram (a re-partitioning regroups float additions —
  the m8 precedent is int64, `checkpoint/m8/test_resume.py:51-58`); §2.5's unreached-label
  DIAGNOSTIC gains a named channel (additive `CompiledGraph` field or read-only accessor, spelling
  pinned at m48 freeze — measured, `CompiledGraph` carries `ir` + `source_names` only); §6.3's golden
  bound to a PRE-m48 capture and §6.1d's broadcast seam scoped to the varied/ambient path; §2.3e
  gains a public `graphed.context_of(array)` seam (the fill lives in another package and §9.1 had no
  `Array` → context read); §2.3e's propagation-gate exemption gains a MEMBERSHIP floor (asserting
  class NAMES let a re-classification hide an unimplemented member); §10/m49 assigns the two
  unassigned anchors (m05 ordering witness, JER-SF fixture → `graphed-histogram`'s `tests/frozen/m49`);
  §5.2a's discriminator restated (measured: re-recording through one Session adds ZERO nodes, so no
  arena delta catches prefix re-recording — §5.2b's single-read witness does).
  **LOW** — §1.1 names the THIRD tag channel (the shift form's collection-mapping inner keys) and
  the m48 grammar anchor gains a shift-form case; §6.1d binds `sample=` (folds last — measured, `fill`
  leaves it unchecked, `boost.py:160-178`); §9.1 states what `graphed.selection` returns on a
  universe/nominal-derived context and §6.4a(2a) tests the link KIND; m48's execution-time refusal
  anchor gains the loose-VALUE message; m48's §4.1 anchor gains its observable; m49's §8.2(i)
  accessor anchor gains an unmarked branch for its DCE clause and names its construction; §2.3c's
  discovery target named as `graphed.awkward.functions` (measured: the package alias discovers 0, the
  module 65); line-number corrections — `session.py:269`→`:268` (twice), `graphed-histogram
  pyproject.toml:20-21,24-38`→`:21`/`:25-39`, `projection.py:109-121`→`:147`. Anchors appendix +1
  measured row, 2 rewritten.
- **r14 (2026-07-30)** — review round 5 (three independent r13 reviews: facts / design / tests,
  `systematics-vary-plan-review-r13-{facts,design,tests}.md`; 33 findings, 29 after cross-lens merge
  — 0 BLOCKER, 7 HIGH, 12 MID, 10 LOW; three defects were raised by more than one lens and are
  merged: §2.3d's discovery rule (facts+design+tests), m48's single refusal contract for two bound
  contracts (design+tests), and §10/m49's `§3.3`-benchmark directory contradiction (design+tests)).
  Every finding re-verified in-session against the pinned verification roots before acting; audit
  trail in `systematics-vary-plan-revision-r14-notes.md`. **Nothing rejected, nothing deferred** —
  no finding's resolution required reversing an owner-locked decision.
  **HIGH** — **`graphed.evaluate_ir` removed from §2.3d's refusing set and from the m48 anchor**: it
  takes no `Array` at all (`evaluate_ir(compiled: CompiledGraph | bytes, …)`, `execute.py:85-91`), so
  the bound refusal had no varied input to refuse and the frozen "plain `Array` still works"
  positive control was false in the other direction too. **§2.3d's discovery rule re-bound over the
  measured signature surface** — the r13 `Array`-FIRST filter discovers 5 verbs and misses
  `compile_ir`/`evaluate_ir`/`read_columns`/`apply` (the safety-bearing dispositions) while
  discovering the undisposed `graphed.broadcast_like`, so the "cannot silently miss a verb" claim is
  withdrawn, the filter now matches ANY parameter annotation mentioning `Array` plus the named
  non-`__all__` members, `broadcast_like` gains a disposition, and the gate carries §2.3c's
  non-vacuity floor. **m48's refusal anchor SPLIT BY CONTRACT** — §2.3d binds the boundary/plan verbs
  to §5.4's `NotImplementedError` and the compile/aggregate verbs to a `graphed.universe` error, and
  `GraphedError` is unrelated to `NotImplementedError`, so one frozen contract for both was a
  guaranteed Test Dispute; the §5.4 message shape moves to m49, where §5.4 is a target.
  **§2.3e gains an ORIGINATION rule** — a context STAMPS its handle on everything it hands out,
  overriding the input merge: `Session.source` takes no context and `record_op` merges only from
  `inputs` (`session.py:133-140,142-168`), so on the plan's own sketch `events2.Jet` would carry the
  PARENT's handle and §6.1d would apply the pre-`vary` ambient registry. **§6.1c's `.plan()` refusal
  restored to GENERAL** — r13's sibling-mode rescoping permitted an axis-mode `.plan()` that
  measurably dies in the reducer (`_SumFills`/`_ZeroHist` take the `__init__`-time spec, which under
  §6.2 lacks the fill-time variation axis; cross-axis addition → `ValueError: axes have different
  length`, bh 1.8.0). **§5.2a's arena-delta witness bound to the public `graphed.vary` surface**
  (`Session.node_count()`), because §3.3's builder is raw `GraphStore` and the witness was
  satisfiable without ever calling `vary`. **m49(ii) binds the `HISTOGRAM` git-URL env var + install
  lines and a no-`importorskip` clause** — `graphed-histogram` resolves on PyPI to a stale `0.0.1`,
  so the dev-extra name alone installs the wrong package.
  **MID** — §6.4a's level-0 lineage parenthetical INVERTED (it demanded `select=None` for the
  canonical skim spelling) and split into (2a) record-time lineage + (2b) execution-time row-count,
  which had no raiser or site; §6.4c binds the XOR/`packbits` COMPUTATION SITE (`_WritePart`, on
  evaluated buffers — float XOR is a `TypeError` in numpy and awkward and gak has no bit-view verb),
  with §6.4f corrected and §11 parking an in-IR bit-view verb; §6.4e's reader respelled
  `graphed.awkward.read_varied` (neutral namespace would put pyarrow+awkward behind `graphed`, whose
  runtime deps are `executing`+`cloudpickle`) with the numpy-idiom read exemption made symmetric;
  §6.2(i-bis) binds duck-typed detection + `axis.index(label)` instead of `bh.loc`, so `graphed`
  imports no `boost_histogram`; §2.2's "superset of any fill's label set" scoped to CONTEXT-BORNE
  sources (loose `Varied` values and explicit `weight=[…]` factors are expressible and are not in the
  union) and `graphed.universe`/`nominal` ON A CONTEXT bound to return a CHILD context so §6.1d's
  ancestry unification can classify it; §10/m49's per-repo partition extended to EVERY anchor (arity
  → `graphed-histogram`, §7.3/§7.4 → a new `tests/frozen/checkpoint/m49`, §8.x named) with §3.3's
  benchmark pinned to `core/m49` in both places; the unique-basename rule generalized to
  `graphed-histogram`, `graphed-executors`, `graphed`'s checkpoint subtree and the new uproot frozen
  tree; §3.4 moved out of m48's targets (its anchor is m49's and no m48 anchor exercised it);
  m48's `graphed.labels(ctx)` anchor gains the discriminating second program (shift-varied collection
  + unvaried mask); m51 gains a manifest-determinism anchor (the sorted-key rule was otherwise
  unobservable).
  **LOW** — §2.6d's "structural, not a convention" scoped to context-borne registrations; §6.1d's
  loose-input adoption bound to label alignment only, with the refusal message naming the VALUE;
  §5.2c bound to the §3.3 topology with its `stages == N+1` literal; m48's §4.3 bullet re-pointed at
  §9.1's per-label fill-node accessor instead of "the §7.2 map"; m48's split re-worded ("except the
  RESULT-MAPPING half of its dedup clause"); m50's scaling anchor re-worded over §6.1c's two-level
  key shape (`_GroupReduce`'s key is the OUTPUT name today); §10/m49 gains §8.2's multi-label
  rendering half; §8.2(i)'s digest triple re-measured with payload + cloudpickle version named
  (r13's was unreproducible); the `#[pymethods]` enumeration corrected to the three blocks in
  `src/lib.rs` (`:102`/`:159`-`:416`/`:470`); pyarrow version pinned to 25.0.1 across the r13-dated
  probes. Anchors appendix +11 measured rows, 3 rewritten.
- **r13 (2026-07-30)** — review round 4 (three independent r12 reviews: facts / design / tests,
  `systematics-vary-plan-review-r12-{facts,design,tests}.md`; 28 findings, 24 after cross-lens merge
  — 0 BLOCKER, 5 HIGH, 9 MID, 10 LOW; three defects were raised by two lenses each and are merged:
  §2.3d's exhaustiveness claim (facts+design), §10's un-followed m49 repo move (facts+design), and
  §4.3's missing per-label fill-node channel (design+tests, with the facts lens's
  "`_fill_nodes` is private" correction folded in)). Every finding re-verified in-session against
  the pinned verification roots before acting; audit trail in
  `systematics-vary-plan-revision-r13-notes.md`. **Nothing rejected, nothing deferred** — no
  finding's resolution required reversing an owner-locked decision.
  **HIGH** — **§8.2 gains part (iii), per-node failure attribution inside `evaluate_ir`**: (i)'s
  label map and (ii)'s call-site wrap did not compose, because a wrapper AROUND `evaluate_ir` cannot
  produce a node id and therefore cannot index the map it is given (measured: `evaluate_ir` is a bare
  dispatch loop with no `try`/`except` and no node annotation, `execute.py:99-126`; the stage branch
  `:110-115` annotates nothing) — the same "the channel does not exist" defect r10 and r11 each fixed
  one layer up, with the keying EVENT still missing; the output-position fallback is promoted if (iii)
  is descoped. **§8.2(i)'s `frozenset[str]` transport field re-bound as a SORTED TUPLE** — a frozenset
  pickles in hash order, so the worker closure's bytes (hence `OpSpec.identity()` → `task_id`/
  `to_bytes`/`fingerprint`) differ across `PYTHONHASHSEED` (measured: three distinct digests), which
  breaks §3.2 in its R22.3 form and kills cross-run checkpoint reuse; a plan-byte determinism anchor
  is added to m49 and the §6.4e manifest is bound to sorted keys for the same reason.
  **§6.4a predicate (2) scoped PER LEVEL** — the r12 lineage test is unsatisfiable for level ≥ 1
  (an inner mask is per-OBJECT and is not `graphed.selection` of any context), so it refused every
  `select={0:…,1:…}` call, i.e. exactly the m51 object-migration anchor r11 exists to enable; levels
  ≥ 1 now use predicate (1)'s structural offsets comparison. **§2.2 binds a context's label set
  once** — §2.6c's "the mask's labels" is a strict subset of what a §6.1d fill produces (104 ambient
  weight labels on the plan's own sketch) and said nothing about a root context, so `graphed.labels`
  on a context is now the §2.4-ordered union of ambient-weight, varied-collection and mask labels.
  **§2.3d's dispositions and §2.2's reserved `node_id`/`session` gain an m48 anchor** — both were
  binding and unanchored, and the parity gate cannot reach plain properties.
  **MID** — §2.3d's "EXHAUSTIVE" list completed (`pack_key`/`shuffle_plan`/`join_plan` were
  undisposed; measured `Array`-first exports) and backed by a dynamic discovery rule; §4.3's
  extraction channel bound as a real §9.1 accessor with its spelling pinned at m48 freeze (§7.2
  binds only *ownership*, and `Histogram.fill_nodes()` is public but UNLABELED — the r12 "private"
  parenthetical named the wrong obstacle), plus the `Array(session, nid)` note for `session.walk`;
  m48's `.plan()` refusal re-worded over SIBLING MODE (the r12 fill-node-count wording over-froze
  m50's mixed axis-mode program, where `_SumFills`' plain addition over disjoint variation bins is
  correct); §10 pins `graphed-histogram`'s `tests/frozen/m49` and m49's repo list gains that repo
  (r12 moved the headline matrix there and left both behind); m48 gains §9.1's m48 half as an
  explicit target (m50's §9 target narrows accordingly); §10 binds unique basenames for
  `tests/frozen/core/m49` and `tests/frozen/preserve/m50` (both suites run as ONE pytest process,
  `run-tests.sh:16-25,30`, and the natural names collide with `m4/test_benchmark.py`,
  `m9/test_reproduce.py`, `m9/test_inspect.py`); the m48/m49 corpus fixture edit re-bound as
  VENDORING only (measured: `graphed` takes no corpus dependency, and a name-only dep does not
  install — the working precedent pre-installs a git URL via a workflow env var
  `graphed-executors ci.yml:17,38` that `graphed-histogram`'s workflow lacks); m49's JER-SF anchor
  gains a PARTITION-INVARIANCE witness (the four r12 witnesses all pass under a constant per-partition
  seed, which §5.5(a) forbids); §6.2(i-bis)'s `h.axes.name` evidence restated (it holds only for a
  one-axis histogram; on any axis-mode histogram it raises `AttributeError`, so the position lookup
  reads `axis.__dict__`).
  **LOW** — §3.1 re-worded to "no optimizer SEMANTICS change" (the m49 remap accessor is the one
  optimizer-adjacent addition, cross-referenced from §8.2); §6.1d's numpy `broadcast_like` bound as
  a NO-OP rather than "a no-op or a refusal"; §1.1 rejects an over-cap INTEGER magnitude at
  canonicalization with a magnitude message; §7.3 + an m51 docs anchor record the same one-time
  journal churn for WRITE plans when `_WritePart` widens; m50's declaration anchor gains the
  literal-expected-list half (an OVER-declaration passes the flow check — measured) and its scaling
  anchor drops the unobservable allocation-count half; m48's §1.2 anchor scoped to sibling mode
  (§1.2's own §6.2 carve-out contradicts it in axis mode); m49 gains an accessor anchor in the repo
  that owns the accessor; §6.4e's two sha256 digests withdrawn as unreproducible and its KV sets
  restated (`ARROW:schema` always present, `ak:parameters` array-dependent); line-number corrections
  — `execute.py:74`→`:70`, `aggregate.py:66-72`→`:86`, `io.py:122`→`:121`,
  `graphed pyproject.toml:41-48`→`:42-48`, `graphed-histogram pyproject.toml:24-38`→`:25-39`,
  `run-tests.sh:16-24,29`→`:16-25,30`. Anchors appendix +8 measured rows, 5 rewritten.
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
