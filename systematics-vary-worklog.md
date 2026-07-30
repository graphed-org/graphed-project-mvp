# Systematics variation ("Vary") plan — worklog

Session: graphed-dev, 2026-07-28. Task: revise/improve/streamline the high-level systematics plan
(Google Doc 116lg4Lw5YcVsvHpdsptOYC-wcxdFXywh0YNAUV2NfeE) into a local plan document that separates
rationale from requirements and can drive the plan → plan-review → implement → impl-review cycle.

## Source doc digest (downloaded to scratchpad/systematics-plan.txt, 3374 bytes)

- Build the systematics IR node + a frontend that emits it. Concept = RDataFrame `Vary`; naming to
  be chosen deliberately and **verified with the user** before it is locked.
- Study: RDF Vary + WRemnants / narf / Latinos (RDF side); nsmith-/BoostedHiggs, PocketCoffea,
  Kelci's analysis (**STUB — user awaiting repo location from Kelci; do not fill without
  confirmation**), and the scikit-hep/coffea prototype systematics harness (python side).
- Taxonomy: **weight** systematics (vary per-event weight at fill; co-computed with central; could
  fill jointly if the histogram layer allows) vs **shift** systematics (alter kinematics → change
  cutflow → part of the analysis re-runs per variation).
- Open design question from the doc: extend optimizer "impact analysis" to isolate the subgraph a
  shift variation must re-run, vs machinery that re-drives the analysis on varied inputs.
- Process: plan → plan review → implement → impl review; BLOCKER/HIGH/MID/LOW/NIT; cycle until clean.

## Setup facts (verified locally)

- `graphed-root-prompt.md` already uses the exact idiom the user asked for: PART I — RATIONALE
  (non-binding, lines 17–123) vs PART II — REQUIREMENTS (binding, R0–R22, line 124+). New plan
  should follow it and will presumably bind as **R23**.
- "systematics-as-a-graph-axis" is currently **named Phase-2** in the root prompt Out-of-scope block
  (line ~1284) and inline in R22.0 + R22.10 → the plan needs the R22.0-style "owner-sanctioned
  pull-in, deliberate and flagged, not silent" language and must amend those three mentions.
- Workdir submodules are STALE (graphed @ fb48fcd, m39-era). Live repos (fresh clones):
  - /private/tmp/claude-501/graphed-latest — consolidated graphed @ ff7c607 (Rust core src/*.rs +
    src/optimizer/, python/graphed/{core,awkward,numpy,debug,checkpoint,preserve,...}, tests/frozen
    reorganized by package: {awkward,checkpoint,core,corpus,debug,frontend,numpy,preserve}).
  - /private/tmp/claude-501/graphed-exec-check — graphed-executors @ 201ea42 (PR #5 merged; frozen
    m7, m41–m47 ⇒ **next milestone number is m48**).
  - /private/tmp/claude-501/graphed-histogram-latest @ 211cbbe.
- Pre-existing acceptance anchor: standalone corpus has `graphed_corpus.analyses.systematics` +
  frozen `m05/test_systematics.py` + `docs/graph_bloat_note.md` (systematics-driven graph growth
  numbers); consolidated repo has tests/frozen/corpus. Root prompt already demands an AGC-ttbar-like
  slice with corrections + systematics (lines ~672–682) and cites "many systematic variations" as
  the graph-bloat driver (line 25) — strong rationale hooks.

## Research fan-out (Workflow wf_e7666c8a-794, 10 agents)

Repo context: ir-rust, frontend-python, histogram, optimizer, exec-checkpoint, corpus.
Prior art: rdf-vary, rdf-users (WRemnants/narf/mkShapesRDF), coffea-sys (Weights/prototype/jetmet/AGC),
pythonic-analyses (BoostedHiggs/PocketCoffea/kmohrman-candidates).
Key claims tasked for structural verification: (a) hash-consing gives shift-variation prefix sharing
for free; (b) checkpoint content-addressing dedupes identical unvaried stages across variations;
(c) whether histogram fills can carry multiple weights vs needing a variation axis; (d) RDF runs all
variations in ONE event loop via per-variation cloned actions — the "impact analysis" precedent.

## Research digest (fan-out complete: 10/10 agents, 0 errors, ~752k tokens)

Reports split into systematics-vary-codebase-analysis.md (6 repo readers) + systematics-vary-litsearch.md
(4 prior-art researchers). Headline conclusions (all evidence-cited in those files):

1. **No new Rust NodeKey needed.** Frontend expansion + hash-consing is the measured path: interning
   gives exact prefix sharing (probe: N=1→2 delta = varied suffix only), reduce stays linear (128
   variations → 16.7 ms), and frozen `core/m4/test_systematics.py` already pins reduced-size
   independence at 3300 variations. A boundary Vary node would FORBID fusing the varied suffix.
2. **"Impact analysis" question resolved**: RDF hand-builds dependency-tracked clones
   (RColumnRegister/MakeVariations) because ROOT lacks hash-consing; in graphed the impact set = new
   node ids past the interning watermark. Expose as trivial API, build nothing.
3. **Weight path nearly free**: correctionlib External already has a `systematic` category param
   (preserve/m9 agc.py); histogram M29 `weight=[...]` + single-pass group plan (frozen witness) do
   the rest. bh rejects 2-D weight (probed) → sibling fills MVP; StrCategory variation-axis fill via
   evaluator loop = the narf-proven scaling mode (non-growth axis verified combine-safe).
4. **Universal conventions** (RDF + coffea + 4 analyses): "nominal" reserved; up/down suffixed
   labels; shift×weight cross products excluded; StrCategory systematic axis; data special-cased.
   Corpus = ready acceptance anchor: 15 stored references, jes_up>nominal>jes_down ordering witness.
5. **Real gaps**: whole-IR task_id ⇒ adding a variation invalidates all cached checkpoint tasks
   (document; stage-granular hashing = follow-up); outputs positional ⇒ named-mapping wrapper needed;
   StageError needs a variation field; m39/40 plan builders are first-boundary-only ⇒ v1 restricts
   variations from crossing Exchange/Join.
6. **coffea prototype stall lesson**: variation forking is a graph-transformation problem, not a
   data-layout problem (`explodes_how` never implemented; selection propagation left TODO).

## Decisions (owner-verified 2026-07-28 via AskUserQuestion)

- Name: verb `vary`, concept "variation", container `Varied`. Labels `name_tag` underscore style
  (`jes_up`), `"nominal"` reserved — matches the 15 corpus reference names verbatim.
- Kelci's analysis: STUB in plan (kmohrman = #1 contributor to TopEFT/topeft + cmstas/ewkcoffea,
  API-verified, identity unconfirmed — candidates noted, not filled).
- Process: FULL join-repartition stringency (user correction): evidence-anchored plan → multi-lens
  review rounds until clean → three-role gated implementation under R0.4 gates → design/integrity/
  mutation impl reviews → R0.5 CI pinning.
- Subagent tuning (user): model AND effort sized per task; saved as memory subagent-model-effort-tuning.

## Plan drafted (r0) → hygiene review → r1 DELIVERED (2026-07-28)

- r0 drafted; 4-lens hygiene workflow wf_5f787a93-9a4 (facts=sonnet-high, design=inherit-xhigh,
  tests=opus-high, process=sonnet-high; ~531k tokens) → systematics-vary-plan-review-r0.md.
- Findings: 2 design BLOCKERs (§2.4 combination rule wrong for Varied-meets-itself — `jets[jets.pt
  > 25]`; stacked variations b-tag-on-JES inexpressible), 2 tests BLOCKERs (wall-clock frozen gate
  vs R0.10a; §1.2/§6.2 label-in-content-hash contradiction), 6 HIGHs (gak "one uniform wrapper"
  falsified; Array[Varied] uncovered; §8.2 label transport had no channel; impact-set watermark
  order-dependent; ref count 9 not 10; m48 repo scope missing graphed-histogram), plus MIDs/LOWs.
- r1 fixes all of it. Load-bearing semantics added in r1: **label-aligned union** (§2.4: for label
  L every container contributes its own L member else nominal — verified expressible against the
  corpus fixture end-to-end incl. jes⊗btag/jes⊗pho reference semantics) and **stacking** (§2.1:
  vary on a Varied nominal; new-label members taken at the provided value's central universe ⇒
  one-at-a-time structural). Also: §3.4 = reachability difference; §4.3 structural (equal-counts
  tautological); §3.3 NEW frozen file (never edit m4); m50 wall-clock → R0.11 report + structural
  frozen invariant; §6.1 per-output label sets + fill arity + _SumFills refusal; §8.2 label rides
  the provenance process-closure channel; shuffle.py:233→232 erratum (also noted in cba header).
- Deliverables: systematics-vary-plan.md (r1), -review-r0.md, -codebase-analysis.md, -litsearch.md,
  this worklog; memory systematics-vary-plan.md written.

## Committed + Kelci exemplar integrated (2026-07-28 → 2026-07-30)

- Plan + 3 evidence docs committed to graphed-org/graphed-project-mvp main @ 173a628 (durable
  link); readme-sync CI green (local gen_readme --check failure = stale-submodule artifact only;
  README/state.json byte-identical to HEAD).
- Kelci's analysis CONFIRMED by owner = cmstas/ewkcoffea; owner also named FNALLPC/wwz4l (modern
  coffea) → **404 to lgray's account** (absent from FNALLPC's 46 public repos; likely private —
  OPEN: needs access/corrected URL). Deep-dive (1 opus agent, ewkcoffea-reader; scope extended
  mid-flight; substitute = branch coffea2023@63abb06, same analysis dask-era port) appended to
  litsearch as §ewkcoffea-confirmed; lead spot-verified 7 headline claims against the clones
  (/private/tmp/claude-501/prior-art/ewkcoffea{,-coffea2023}).
- Headline evidence: dask-era port kept ALL systematics semantics but forced hand-written CSE in
  the processor (masked_val_cache), deepcopy→copy+TODO, and an unserializable task graph
  ("# Does not work" cloudpickle) — graphed's interning/IR-durability claims, recorded by the
  exemplar's own author. No dask-era version ever carried an object shift (empty
  obj_correction_systs predates the branch); hout={} scoping bug latent.
- Plan → **r2**: stub replaced; deltas applied (§4.1 sow normalization + §11 scalar helper parked;
  §6.2 scalar-labeled shift siblings on the shared axis + m50 mixed anchor; §7.3
  skip_obj_systematics as canonical invalidating edit; §11 per-sample label-set divergence;
  3 anchor rows). Reinforced-no-change: §1, §2.4, §3.1, §3.4, §4.3, §5.1, §6.1a, §6.3.

## FNALLPC/wwz4l resolved (2026-07-30, plan → r3)

- Access granted; ewkcoffea-reader resumed for the deferred re-check; lead independently
  re-verified era/lineage (0 dask hits repo-wide; dict_accumulator; Weights(len(events)); shifts
  :395-400; overlap 503 lines vs main / 308 vs coffea2023; sole branch main).
- **Conclusion inverted vs the user's framing**: wwz4l@cc71718 is a coffea-0.7-era CMS-DAS
  teaching derivative of ewkcoffea@main (NOT modern coffea), full weight+shift treatment
  (27 labels). C.4 extends: NO reachable dask-era version of this analysis has ever carried an
  object shift → dask-era shift-loop cost remains unverifiable from prior art. Distinct value:
  teaching strip removed all physics, variation scaffolding survived intact = irreducible
  accidental complexity, exactly what vary deletes. Zero requirement changes (PART II untouched).
- Litsearch addendum appended; plan r3 (Part I §2 resolution + anchor row + revision entry).

## JER-SF corner killed (2026-07-30, plan → r4)

- Owner: don't engineer the shift contract to jes_up>nominal>jes_down — JER-SF re-smearing is
  non-monotone. Verified in coffea's CorrectedJetsFactory.py: rand_gauss seeds PCG64 from the
  input array's own bytes (:37-40, content-seeded determinism); jer_smear draws ONCE and varies
  only the SF column per label (:64-95, hybrid detSmear/stochSmear, signed → bidirectional
  migration).
- r4: §5.1 rescopes ordering witness to the JES fixture; new §5.5 (stochastic shifts first-class:
  content-seeded randomness mandatory, one-draw-all-universes → draw interns in shared prefix);
  m49 gains a JER-SF fixture anchor (bidirectional-migration witness = no selection mask is a
  subset of another's; run-to-run byte-identity; shared-draw interned once). Anchor row added.

## Event-context semantics (2026-07-30, plan → r5)

- Owner semantic correction: systematics are ambient properties of the EVENT RECORD; per-fill
  Varied-weight threading (r0-r4 sketches) re-created the forgotten-weight failure mode. Precedents
  agree: RDF weight column / coffea Weights-on-batch / boostedhiggs shifts-as-collection-swap.
- Owner selected (AskUserQuestion, all recommendations): context methods
  (events.vary(name, Coll={tag: rec}, ...) lockstep + events.weights.add/add_multi); inferred
  auto-applied ambient weight at fill (weight= adds factors, unweighted=True, two-context = error);
  progressive + scoped registration (fill-time snapshot; derived contexts inherit + extend —
  replaces per-channel deepcopy).
- r5: new §2.6 (event context, frontend-only sugar over Varied — §3 backend untouched; mechanism
  neutral in graphed, nanoevents constructor in graphed.awkward), §6.1d (fill inference, label
  union = value ∪ ambient ∪ explicit, per-event→per-object weight broadcast witness, data guard),
  Part I rationale para, m48 +7 event-context anchors.

## Collaborator feedback round (2026-07-30, → r6 in progress)

Four points from collaborators via owner: (1) events.weights attribute collides with real tree
branches → functional graphed.vary(events, name, ...) returning NEW contexts (overturns r5's
method+mutation choices — easier provenance, no reserved attributes); (2) tags generalize beyond
up/down (1/2/3-sigma) → bind kwarg-parseable identifier-string tags (collaborator lean; arbitrary
hashables rejected); (3) NEW SCOPE: variation-aware WRITE-OUT (skim augmentation) — OR of varied
selections determines written events; varied columns + cutflow masks stored compression-
efficiently; appended to user-indicated columns (un-parks the §11 write-out item); (4) respin
requirements + example.

Compression probe (R0.11; float32, 1M elems, zlib-6, rng seed 42; synthetic jes-like pt ×1.03 w/
0.5% spread + near-1 weight ratio; 5 masks flipping ~3% vs nominal):
- values: raw=3.551MB ratio=2.883 delta=3.193 xor=3.280 (of 4.0MB) — ratio compresses best BUT
  reconstruction NOT bit-exact (measured False); XOR bit-exact by construction; subtract-delta
  bit-exact here but only data-dependently → bind bit-exact REQUIRED, exact-by-construction
  default (XOR-delta candidate), lossy ratio = Phase-2 opt-in; re-measure on real skims at m51.
- masks ×5: raw-bool 798KB / packbits 614KB / XOR-vs-nominal+packbits 169KB (~4.7×) → store
  nominal mask + per-variation packed XOR-diff masks.
write-seam-reader agent (opus) mapping write.py/parquet.py/uproot graphed_write seams.

## Pending (next session / owner call)

- [ ] Formal §12.1 review cycle r7…rN (multi-lens, BLOCKER..NIT, until clean) before test-authoring
      — §2.6 (functional respin), §6.1d, and NEW §6.4/m51 write-out all need the design lens
- [ ] On landing: R23 draft + un-park the Phase-2 mentions (§12.3)

## 2026-07-30 (cont.) — r6 respin EXECUTED (functional API + tag grammar + §6.4/m51 write-out)

write-seam-reader report recovered from agent transcript (idle-without-delivering again) and ALL 7
headline claims spot-verified against fresh clones: PartitionedSource write.py:83-97;
_WritePart.__call__ awkward/io.py:111-127 (single-output evaluate, no metadata); NodeKey has NO
write kind (node.rs:41-70); compile_ir variadic "EXACTLY the requested outputs" execute.py:54-70;
numpy 1-D single-column cap numpy/io.py:163-171; graphed_write zero compile_ir/evaluate_ir hits
(verbatim branch copy _graphed_write.py:59-64); KV metadata 0 hits repo-wide. Fork name verified:
graphed-org/uproot5-graphed-mvp.

Plan r5 → r6 (single edit pass): §1.1 tag grammar (kwarg tags; variations= escape for numeric
families; label = valid identifier; hashables rejected); §2.1 ONE functional verb, 3 overloads
(loose Array/Varied; context is_weight=True; context Collection={tag: record}), never mutates;
§2.2 graphed.universe/labels/nominal module functions — also fixes r5's latent Varied[label] vs
string-field-getitem collision; §2.6 rewritten functional (no reserved names on context; lineage
= provenance; snapshot rule → immutability); §6.1d most-derived-context rule; NEW §6.4 (a-g:
OR-superset rows, augmentation columns, bit-exact REQUIRED w/ measured XOR default + probe
numbers, structure rule w/ object-level masks, parquet-KV manifest + reader, verified seam
bindings, no-cost-when-unused); NEW m51 milestone (6 anchor groups; ROOT eval = larger half);
§11 un-parks write-out, parks lossy ratio + per-universe fan-out + auto-symmetric; Part I §3
rationale paragraph + §4 skim-growth cost; anchors +9 rows; revision history r6.

Also: killed 2 zombie CI watchers (173a628/a1aaefd gh-run polls, 2 days stale — merges long
settled; user flagged).
