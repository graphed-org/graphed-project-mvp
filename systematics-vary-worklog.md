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

## Pending (next session / owner call)

- [ ] Formal §12.1 review cycle r4…rN (multi-lens, BLOCKER..NIT, until clean) before test-authoring
- [ ] On landing: R23 draft + un-park the 4 Phase-2 mentions (§12.3)
