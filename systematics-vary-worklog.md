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

## 2026-07-30 (cont.) — r7: stringified-float tags (owner directive)

Directive: tags must also allow stringified floats ("0.5", "-2", "2.0" — μR/μF scales, σ-scans).
Verification workflow (wf_c7b44dbe-0fb, 3 agents: parquet probe / uproot probe / full-plan
identifier-dependence sweep), all headline results:
- pyarrow 25.0.0: dotted/minus column+field names round-trip byte-exact; arrow schema stays FLAT;
  pq column selection by dotted name works; KV metadata round-trips.
- awkward 2.12.0 HAZARD: ak.from_parquet(columns=["murf_0.5"]) SILENTLY EMPTY (splits string
  specs on '.'); list-path columns=[["murf_0.5"]] works.
- uproot 5.7.5: accepts dotted/minus branch names silently (no validation anywhere in writer);
  byte-exact on disk (RNTuple + TTree). HAZARDS: RNTuple __getitem__ splits on '.'
  unconditionally (behaviors/RNTuple.py:1573-1576 → KeyInFileError 'murf_0'); TTree exact-lookup
  works (TBranch.py:2098); writer joins nested-record subfields with '.' (_cascadetree.py:1606).
- CPython 3.12.10: f(**{'0.5': 1}) ACCEPTED → tag validation must be channel-independent.
- Sweep (36 sites): 4 blast zones — §1.1 grammar root; §6.4b/f stored-name interpolation (the
  only place '.'/'-' meet systems that assign them meaning); §6.2 sorted axis (determinism/
  combine-safety FINE — lexicographic ≠ numeric order is UX only); m48 grammar anchor would have
  FROZEN the r6 rejections into read-only tests (hard block). New hazards the amendment itself
  introduces: spelling multiplicity ("2"/"2.0"/"+2"/"2e0") → narrow grammar + numeric-equality
  dup rejection; label→(name,tag) split on last '_' stays unambiguous.

r7 binding: two-form tag grammar (identifier | fixed-point float -?\d+(\.\d+)?); raw labels in
memory (bins/keys/manifest measured string-safe); NAME-SAFE form on disk only ('.'→'p',
leading '-'→'m', datacard 0p5/m2 convention; identifier labels are their own name-safe form);
manifest = sole label resolver; name-safe collision + numeric-equal dup rejected at vary time;
§9.1 variations() reports parsed floats (ordering handle; §6.2 sorted axis pinned lexicographic);
m48 anchor rewritten to r7 rejections; m51 adds numeric-tag round-trip fixture.

## 2026-07-30 (cont.) — r8: p-encoding canonicalized at the source (owner directive ×2)

Owner: solve the dot problem by translating decimals to 'p' (2.5 → 2p5, common practice); offered
scaled-integer alternative (×10 until integral + scale metadata). Bound: r7's dual representation
(raw label in memory / mangled on disk / manifest as translator) DELETED in favor of call-time
canonicalization — vary accepts "2.5"/"-2" spellings as sugar, canonicalizes '.'→'p', leading
'-'→'m'; the p-form IS the tag everywhere. Restores the r6 every-label-is-an-identifier invariant
unconditionally; r7 name-safe-collision check collapses into ordinary duplicate detection
({"0.5","0p5"} = same tag). No new probes needed: __vary_murf_0p5__Jet_pt was ALREADY in both r7
probe fixtures, byte-exact + readable everywhere. Scaled-int alternative recorded in §1.1, not
chosen (minus unhandled; not self-describing — murf_25 ambiguous without side table; scale varies
per tag within a family); revisitable Phase 2. §6.4b/e simplified; §9.1 parses m?\d+(p\d+)?;
m48 grammar anchor → canonicalization semantics; m51 fixture → murf_0p5 verbatim.

## 2026-07-30 (cont.) — r9: e-form canonical (owner-selected via 3-option decision)

Owner refined the scaled-int alternative to exponent-suffix form (1.2345 → 12345e-4 =
self-describing; my r8 side-table objection retracted) and argued its parseable numeric
structure; presented 3-option AskUserQuestion (p-canonical / e-canonical / hybrid) → owner
selected E-FORM CANONICAL. r9 binds: canonical numeric grammar m?\d+(em\d+)? — integers = plain
digits (PDF indices untouched: "102"→102, NOT mangled), fractional = minimal-mantissa em-form
("0.5"→5em1, "-1.5"→m15em1, "1e-8"→1em8; bare e never appears — fractional exponent negative by
construction). Input grammar widened to full float literals incl. exponents; canonicalization by
EXACT decimal-string arithmetic (no IEEE artifacts); normalization unifies all spellings
("2"≡"2.0"≡"2e0"≡"20e-1"); cross-notation numeric-equal rejection ({"0.5","0p5"}) since datacard
p-tags remain legal identifier tags. Probe coverage carries over (identifier-shaped names
measured safe; fixture __vary_murf_0p5__Jet_pt ≡ shape of canonical __vary_murf_5em1__Jet_pt).
Deletes the r9-draft Phase-2 e-widening seam (e IS canonical now). Decision trail in §1.1.

## 2026-07-30 (cont.) — §12.1 REVIEW CYCLE round 1 DONE (r9 → r10); PAUSED at round boundary

Owner launched the formal multi-lens cycle: per round 3 ISOLATED Opus-high reviewers
(facts/design/tests, fresh contexts) + 1 isolated Opus-high reviser; loop until zero
B/H/M/L. Workflow wf_c45b3140-382 (script persisted in session workflows dir).

Round 1 on r9: B=1 H=5+ M=8+ L=4+ across lenses (design DIRTY: 1/5/8/4). Reviser re-verified
all 32 findings (28 distinct), applied ALL, rejected 0, deferred 0 (nothing touched
owner-locked decisions). Headlines: BLOCKER — §6.1d context inference via "provenance" can't
work → NEW §2.3(e) context-tag propagation dispatch point; §8.2 StageError label transport
channel measured nonexistent → withdrawn + rebound as named m49 work (variation_labels on
_PartitionReduce, post-reduction ids); §7.2 positional unpacking breaks under interning dedup →
(output,label)→node-id map; §6.2 axis declaration contract (silent label swallowing fixed);
§6.1d broadcast contradiction → unflattened values + gak.broadcast_arrays; §6.4a implicit mask
undecidable → explicit to_parquet(record, select=varied_mask); §6.4d multiplicity-divergence
refusal; §3.3 pinned integers re-derived BOTH WAYS (with/without per-universe reduction:
2N+2/Δ52 vs N+2/Δ51); + 5 missing-anchor traceability fixes, 6 facts corrections (RNTuple
hazard re-measured: to_akform splits :562,567 not getitem; TBranch :2015-2017; ak
Discussion #469 restated as reported-not-measured). Plan now r10, 1388 lines. Reviews:
review-r9-{facts,design,tests}.md; audit: revision-r10-notes.md.

PAUSED (owner laptop shutdown) at the clean round boundary: workflow STOPPED after reviser
completion; round 1 (4 agents) fully journal-cached.

## RESUME INSTRUCTIONS (next session)

1. Relaunch: Workflow({scriptPath: "~/.claude/projects/-Users-lgray-vibe-coding-graphed-workdir/
   8f54f531-a6e8-4340-a81d-efa35f73b6f6/workflows/scripts/vary-plan-review-cycle-wf_c45b3140-382.js",
   resumeFromRunId: "wf_c45b3140-382"}) — round 1 replays from cache instantly; round 2 (fresh
   isolated reviews of r10) runs live; loop continues until clean (cap 6 rounds).
2. NOTE: the loop's `rev` starts at 9 in the script — resume replay reconstructs state through
   the cached round-1 results, so round 2 reviews r10 automatically.
3. On clean: commit final plan + all review/notes files, set status "review-clean", update
   memory, then proceed toward m48 test-authoring (gated pipeline).
4. Verify readme-sync CI green on the pause commit (docs-only; 9-for-9 green today).

## 2026-08-11 — RESUMED; review round 2 done (r10 → r11)

Resume after 12-day pause: readme-sync on b3518e6 verified green (--limit+headSha pattern).
/private/tmp wiped by reboot → ALL 14 verification roots re-cloned at exact pinned SHAs
(graphed ff7c607, executors 201ea42, histogram 211cbbe, uproot5 393ecef@graphed-mvp, corpus
49650e4; prior-art pins recovered from litsearch evidence tables: ewkcoffea 063e8d7,
coffea2023 63abb06, wwz4l cc71718 private, WRemnants c5be6c6, narf 7d73361, mkShapesRDF
b89a71f, PocketCoffea b29e33b, boostedhiggs a33dca8, topeft bbb23ca). Script untouched so
round-1 journal cache stayed valid; resume replayed round 1, round-2 reviewers restarted fresh.

Round 2 on r10: 1 BLOCKER / 7 HIGH / 16 MID / 16 LOW / 3 NIT (design 1B/5H/10M/5L, tests
1H/5M/5L/1N, facts 1H/1M/6L/2N). Character: ~60% second-order fallout from r10's own new
surface (BLOCKER = §6.4d demands cutflow data no bound API supplies; §6.2 plan-time axis
declaration vs record-time identity; §6.1d "already-unified handle" false at the fill; §2.3e
plain-attribute impossible on today's Array), ~40% deeper excavation of pre-r10 surface
(m48 headline anchor unbuildable; §2.1 stacking wrong for weight form; §2.6 sketch
lhe_w[:, i] measured TypeError). Zero re-raises of round-1 items.

Reviser → r11 (1803 lines, +415): 39 applied (40 merged to 39 on the §6.1a-axis-mode dup),
0 rejected, 0 deferred, no owner-locked reversals, no OPEN ITEMS. Reviser's own measurement:
working inner-index spelling gak.firsts(w[gak.local_index(w) == i]) replaces the broken
lhe_w[:, i] sketch line. Note: r11 history entry says 2026-07-30 (script's hard-coded date;
kept to preserve the round-1 cache — cosmetic only, real date 2026-08-11).

Round 3 (fresh isolated reviews of r11) launches automatically.

## 2026-08-11 — OWNER RULING (binds next plan-writing phase, NOT this review cycle)

Partition plan execution into commit-sized steps: each commit ≤1-2k LOC MAX (smaller fine) =
one bounded "thought"; use the partition to separate concerns so the whole stays well
factored. Applies from the m48+ decomposition/plan-writing phase after the current §12.1
review cycle reaches clean. Recorded in memory (commit-sized-thoughts.md). The plan doc is
NOT edited mid-cycle for this; fold it into the milestone decomposition structure when the
cycle closes (each milestone → named commit sequence with concern + rough size per commit).

## 2026-08-11 — review round 3 done (r11 → r12)

Round 3 on r11: 0 BLOCKER / 8 HIGH / 13 MID / 15 LOW / 3 NIT (tests 4H/5M/4L, design
4H/7M/4L, facts 1M/7L/3N). Blocker class gone; facts lens essentially clean (nearly every
anchor resolves exactly against the pinned roots) — HIGH mass concentrated in tests+design
stress of the r11 anchor/contract rework. Reviser → r12 (2204 lines, +505/-104): 30 applied
(32 raw, two cross-lens dup pairs merged: §6.2(i-bis) axis-slicing, §6.2 declaration hedge),
0 rejected, 0 deferred, no owner-locked tensions. Anchors appendix +11 measured rows, 7
rewritten. Round 4 (fresh isolated reviews of r12) launches automatically.

## 2026-08-11 — review round 4 done (r12 → r13); PAUSED (owner laptop close)

Round 4 on r12: 0 BLOCKER / 5 HIGH / 12 MID / 11 LOW / 4 NIT (design 3H/5M/4L/1N, tests
2H/4M/4L, facts 3M/3L/3N — facts lens: "strongest substrate in this review series", every
load-bearing measurement reproduced exactly). HIGH trend across rounds: 8 → 7 → 8 → 5.
Reviser → r13 (2511 lines, +307): 24 applied (28 raw, cross-lens merges: §2.3d
exhaustiveness, §10 m49 move, §4.3 fill-node channel + "_fill_nodes is private" fold-in),
0 rejected, 0 deferred, no owner-locked tensions. CI note: bb20579 readme-sync failed once
on a transient runner TLS error (submodule clone cert verification) — rerun green.

PAUSED at the round-4 boundary: workflow wb3qid1p1 STOPPED after the reviser; all 16 agent
results (rounds 1–4) journal-cached; round-boundary monitor stopped; no watchers left.

## RESUME INSTRUCTIONS (updated 2026-08-11)

1. DO NOT auto-resume: the owner will give an explicit go-ahead before round 5 starts.
2. On go-ahead: verify the 14 verification roots still exist at pinned SHAs (reboot wipes
   /private/tmp — re-clone recipe + pins in the 2026-08-11 RESUMED entry above), then
   Workflow({scriptPath: "~/.claude/projects/-Users-lgray-vibe-coding-graphed-workdir/
   8f54f531-a6e8-4340-a81d-efa35f73b6f6/workflows/scripts/vary-plan-review-cycle-wf_c45b3140-382.js",
   resumeFromRunId: "wf_c45b3140-382"}) — rounds 1–4 replay from cache; round 5 reviews r13
   live. Round 5 is the LAST before the cap (script cap = 6 rounds; round 6 reports
   max-rounds instead of revising).
3. Standing owner ruling for AFTER the cycle: commit-sized thoughts — plan steps as commits
   ≤1-2k LOC each (memory: commit-sized-thoughts.md); apply in the m48+ decomposition.
4. Per-round pattern: commit r-review files + revised plan + notes + worklog, push, bounded
   CI check (--limit+headSha, never --commit; rerun once on transient infra failures).

## 2026-08-11 — RESUMED on owner go-ahead; review round 5 done (r13 → r14)

Owner directives: continue plan/review until clean; do NOT proceed to implementation after.
All 14 verification roots survived intact (no re-clone needed). Rounds 1-4 replayed from
cache; round 5 fresh on r13.

Round 5 on r13: 0 BLOCKER / 10 HIGH / 12 MID / 11 LOW / 2 NIT (design 4H/7M/4L, tests
4H/5M/4L/1N, facts 2H/3L/1N). Raw HIGH count up vs round 4 (5H) BUT 5-6 of the 10 are ONE
defect through three lenses: the r13-added §2.3d discovery rule (graphed.__all__ filtered to
Array-annotated first param) misses 4/10 verbs, over-fires on broadcast_like, binds a dead
evaluate_ir refusal, and its m48 anchor freezes 1 error contract where the body binds 2.
Genuine vacuity catch: §5.2a arena-delta witness satisfiable without calling graphed.vary.
Character still fix-induced surface (r13 was +307 lines), not noise — substance converging
(no blockers since round 3, facts anchors near-perfect).

Reviser → r14 (2837 lines, +326): 29 applied (33 raw; discovery-rule cluster merged
facts+design+tests, refusal contract design+tests, §3.3 directory folded into m49
partition), 0 rejected, 0 deferred, no owner-locked tensions. Anchors +11 rows / 3
rewritten. Round 6 = CAP round: reviews r14, reports max-rounds if dirty (no revision).
Plan if dirty at cap: raise cap in script (loop control only — safe, prompts unchanged,
journal cache preserved) and resume; escalate to owner if rounds 7+ plateau ~30 findings.

## 2026-08-11 — review round 6 (cap round) done on r14; cap raised 6 → 12

Round 6 on r14: 0 BLOCKER / 9 HIGH / 10 MID / 10 LOW / 3 NIT (design 4H/3M/3L, tests
4H/7M/4L, facts 1H/3L/3N). Severe volume decaying slowly (33 → 29). Facts HIGH is a
precision catch: r14's REPLACEMENT §2.3d discovery rule (annotation mentions Array,
anywhere) still misses compile_ir — signature (session: Session, *outputs: Any) mentions
Array nowhere, and compile_ir IS in graphed.__all__ so the named-members escape hatch
(scoped to non-__all__ members) doesn't reach it; measured in-session against
graphed-latest with inspect.signature. Same design-lens cluster confirms + over-fire on
m48's own new exports. Workflow returned status=max-rounds (script cap). Per owner
directive (continue until clean), cap raised 6 → 12 in the script — LOOP CONTROL ONLY,
no agent prompt changed, all 22 cached results stay valid; resume runs the r14→r15
reviser live, then round 7. Round-6 artifacts = 3 review files only (no reviser at cap).

## 2026-08-11 — round-6 reviser done (r14 → r15)

Reviser → r15 (3171 lines, +334): 26 applied entries / 23 distinct after cross-lens merge
(compile_ir defect = ALL THREE lenses; §5.2c design+tests; §5.2a span+discriminator one
paragraph), 0 rejected, 0 deferred, no owner-locked tensions. Reviser re-measured the r14
annotation-wide rule: discovers exactly 8 verbs, NOT compile_ir — fix landed per the
triple-lens cluster. Round 7 (fresh isolated reviews of r15) launches automatically.

## 2026-08-11 — review round 7 done (r15 → r16); sharp convergence

Round 7 on r15: 0 BLOCKER / 4 HIGH / 13 MID / 12 LOW / 2 NIT (design 2H/6M/4L, tests
2H/7M/4L, facts 0H/0M/4L/2N — facts CLEAN above LOW for the first time, "all pointer
hygiene"). HIGH trend: 8/7/8/5/10/9/4 — the compile_ir/discovery cluster fix broke the
plateau. Reviser → r16 (3516 lines, +345): 29 applied, 0 rejected, 0 deferred, no
owner-locked tensions. Round 8 (fresh isolated reviews of r16) launches automatically.

## 2026-08-11 — review round 8 done (r16 → r17)

Round 8 on r16: 0 BLOCKER / 2 HIGH / 12 MID / 11 LOW (tests 0H/5M/3L — first HIGH-free
lens report of the series; design 1H/6M/7L; facts 1H/1L/2N, ~130 anchors verified, exactly
one substantive failure: §7.3). HIGH trend: ...10/9/4/2. Reviser → r17 (3857 lines, +341):
24 applied, 1 REJECTED (first rejection of the series — facts LOW claiming a stale
checkpoint test line span; reviser re-measured and refuted it), 0 deferred. Round 9
launches on r17.

## 2026-08-11 — review round 9 done (r17 → r18)

Round 9 on r17: 1 BLOCKER / 5 HIGH / 11 MID / 8 LOW (design 1B/2H/4M/3L, tests 3H/7M/3L,
facts 0H/0M/2L/1N — essentially clean two rounds running). BLOCKER = r17-introduced drift:
§6.1a bound a NESTED group-result dict ("combine BRANCHES") while r17's §6.1c bound a FLAT
slot-keyed mapping ("combine needs no branch") — same frozen object, mutually exclusive
shapes. Reviser → r18 (4209 lines, +352): 22 applied, 0 rejected, 0 deferred. Round 10
launches on r18.

## 2026-08-11 — review round 10 done (r18 → r19)

Round 10 on r18: 3 BLOCKER / 7 HIGH / 6 MID / 8 LOW raw = 2 distinct blockers, both
r18-introduced: (1) §2.2/§2.3a property rule freezes "every non-shape property answers
eagerly, node-delta 0" but NumpyArray.T is a RECORDING property (return self.transpose()
→ record_op) — tests+facts twin; (2) §6.1a flat slot-keyed mapping bound UNQUALIFIED,
re-keying unvaried programs and breaking frozen m23 — design. MID/LOW volume lowest of
series (6M/8L). Reviser → r19 (4545 lines, +336): 19 unique applied (22 post-NIT, 3
cross-lens dup pairs merged: T-property blocker, N+1 image, unpack/MODE), 0 rejected,
0 deferred. Round 11 launches on r19. Trend: revision-seam regressions now dominate;
work lists shrinking (39/33/29/24/22/19 applied per round).

## 2026-08-11 — review round 11 done (r19 → r20)

Round 11 on r19: 0 BLOCKER / 4 HIGH / 8 MID / 7 LOW (tests 1H/3M/2L, design 3H/5M/5L,
facts FULLY CLEAN — 2 NITs only, first zero-findings-above-NIT lens report of the series).
No new blockers: the r18 seam-regression cycle did not repeat. Reviser → r20 (4841 lines,
+296): 17 applied, 0 rejected, 0 deferred. Applied trend: 39/33/29/24/22/19/17. Round 12
= NEW CAP round: reviews r20, reports max-rounds if dirty (no revision) — if dirty, raise
cap again and resume (same loop-control-only edit).

## 2026-08-11 — review round 12 (cap round) done on r20; cap raised 12 → 18

Round 12 on r20: 0 BLOCKER / 2 HIGH / 7 MID / 5 LOW / 1 NIT (tests 0H/4M/1L — cleanest
tests report yet; design 2H/3M/2L; facts 2L/1N, clean 4th round running). CLEANEST ROUND
OF THE SERIES: 14 severe (trend 37/40/36/28/33/29/29/25/24/24/19/14). Both HIGHs = two
halves of ONE defect: the r19/r20 aggregate_plan seam — §7.2 binds "node id → position
from the compiled output list" which is measurably not computable frontend-side (compiled
list lives in REDUCED id space; record→reduced map doesn't exist until m49's accessor;
compile_ir never calls mark_output on the record store — probe evidence in the round-12
design review), and seam half (β) takes a parameter only computable from the artifact the
same call produces. Suggested fix already in the finding: derive positions from the
frontend's OWN dedup-ordered requested-id list (= evaluate_ir return order, measured).
Workflow returned max-rounds again; cap raised 12 → 18 (loop control only, cache intact);
resume runs reviser r20 → r21 live, then round 13.

## 2026-08-11 — round-12 reviser done (r20 → r21)

Reviser → r21 (5069 lines, +228 — smallest revision of the series): 13 applied (14 severe,
one cross-lens merge), 0 rejected, 0 deferred. The §7.2 seam derivation re-bound to the
frontend's own dedup-ordered requested-id list per the measured fix. Round 13 launches
on r21.

## 2026-08-12 — review round 13 done (r21 → r22); FIRST HIGH-FREE ROUND

Round 13 on r21: 0 BLOCKER / 0 HIGH / 9 MID / 10 LOW / 3 NIT (design 0H/4M/6L — first
HIGH-free design report; tests 0H/5M/2L; facts 2L/3N "all line-span precision"). First
round with nothing above MID. Reviser → r22 (5356 lines, +287): 17 applied, 1 REJECTED on
measured counter-evidence (tests LOW about a correctionlib systematic= param the m9
fixture does carry), 0 deferred. Round 14 launches on r22; remaining work is the MID/LOW
tail.

## 2026-08-12 — review round 14 done (r22 → r23)

Round 14 on r22: 0 BLOCKER / 1 HIGH / 8 MID / 12 LOW (design 1H/5M/3L, tests 0H/2M/4L/1N,
facts 0H/1M/5L/1N). Single HIGH across all lenses. Reviser → r23 (5605 lines, +249): 19
applied, 0 rejected, 0 deferred. Round 15 launches on r23.

## 2026-08-12 — review round 15 done (r23 → r24)

Round 15 on r23: 0 BLOCKER / 1 HIGH / 9 MID / 8 LOW (tests 0H/3M/4L, design 0H/5M/3L,
facts 1H/1M/1L — the HIGH: r23's "exactly one construction exists" claim for the two-label
shared-node fixture measured false). Reviser → r24 (5842 lines, +237): 16 applied, 0
rejected, 0 deferred. Round 16 launches on r24.

## 2026-08-12 — review round 16 done (r24 → r25)

Round 16 on r24: 0 BLOCKER / 2 HIGH / 8 MID / 8 LOW (tests 0H/4M/4L, design 2H/3M/2L,
facts 1M/2L/2N). Reviser → r25 (6036 lines, +194): 13 applied, 0 rejected, 0 deferred.
Series has settled into 0-2H oscillation with ~8M/8L tail for 4 rounds. Round 17 (last
revising round before cap-18 report) launches on r25.

## 2026-08-12 — review round 17 done (r25 → r26)

Round 17 on r25: 0 BLOCKER / 1 HIGH / 9 MID / 8 LOW (tests 1H/2M/6L, design 0H/7M/2L,
facts CLEAN — 3 NITs). Reviser → r26 (6250 lines, +214): 17 applied, 0 rejected, 0
deferred. Round 18 = cap round: reviews r26, reports. Structural assessment due at the
report.

## 2026-08-12 — review round 18 (cap round) done on r26; STRUCTURAL DECISION POINT

Round 18 on r26: 0 BLOCKER / 4 HIGH / 6 MID / 8 LOW / 1 NIT (design 1H/3M/6L, tests
3H/3M/1L, facts 1L/1N — facts clean 3 of last 4 rounds). Workflow returned max-rounds a
third time. Series data (severe B+H+M+L per round): 37/40/36/28/33/29/29/25/25/24/19/14/
19/21/18/18/18/18 — plateau ~18 since round 12. Plan grew 1388 → 6250 lines over the
cycle. Run totals: 71 agents, ~8.08M subagent tokens, 0 errors. Diagnosis: each revision
(+200-350 lines) mints findings on its own new text at roughly the rate old findings are
retired; zero-B/H/M/L is not reachable by iteration alone while the document grows.
Round-18 HIGHs are still genuine (e.g. r26's §8.2(i) producer clause cannot produce the
set-valued map §8.2 itself binds — the composition's image only contains marked fill
nodes, measured). Escalated to owner with three options (continue loop / adjudicated
closure / ledger-and-stop).

## 2026-08-12 — ADJUDICATED CLOSURE done (r26 → r27); §12.1 REVIEW CYCLE CLOSED

Owner selected adjudicated closure over continued looping (AskUserQuestion, after 18
rounds plateaued ~18 severe/round; H/M classification: ~60-65% code-facing structural,
~20% self-referential anchor bookkeeping, ~15% hybrid). Closure workflow
(wf_d1253631-f20, 4 agents, ~465k tokens, 26 min): closure reviser fixed all 18 round-18
findings under strict no-new-surface discipline (5 pure deletions/replacements; 2
suggested fixes DECLINED as too additive; 2 unnamed mirror sites swept) → verify pass 1:
17/18 (one LOW respell) → bounded repair → verify pass 2: 18/18 RESOLVED, every
measurement re-run independently. 3 items descoped to NEW §12.4 Closure ledger (operand
normalization pinning at m49 freeze; §6.4f error class/wording at m51 freeze; §8.2(i)
producer cost measurement under R0.11). §12.1a records the closure decision. Plan r27,
6444 lines, status "review-clean (r27, adjudicated closure)".

Key closure fixes: §8.2(i) producer respelled as per-label record-CONE walk (the
composition-over-roots defect measured at src/node.rs:100-104); m48 stacking anchor
respelled over .node_id equality (bool(a==b) unconditionally True — vacuity killed);
§5.3 union-growth fixture pinned FLAT (read_columns granularity measured);
Sequence[Varied] operand widened to include Mapping[str, Sequence[Array]].

NEXT (owner-gated): m48 decomposition via the gated pipeline, working from the §12.4
ledger, under the commit-sized-thoughts ruling (steps ≤1-2k LOC). Implementation
explicitly NOT started per owner directive.

## 2026-08-26 — r28: design extraction (r27 → r28) under the revised CLAUDE.md

Owner directive: the review cycle's apparatus had metastasized into the plan itself; extract
the design per the revised root CLAUDE.md ("a plan is a design, not a ledger"). r28 rewrites
systematics-vary-plan.md in place: 6444 → 4586 lines. Removed wholesale: the Anchors appendix
(file:line stamps; evidence lives in cba/lit companions) and the Revision history (git +
revision-r*-notes files hold it). Removed in-body: measurement transcripts/"(measured: …)"
parentheticals (load-bearing facts restated plainly, symbols instead of line coordinates),
all lowercase-rN round attributions, drift-log/re-pin prose, adjudication/disposition prose,
counts beside enumerated lists. §12.1+§12.1a folded into one forward-process statement
(cycle closed; gated pipeline per milestone). §12.4 ledger, §12.3 actions, all binding
rules/anchors/targets retained.

Method: 13 parallel section extractors under one editorial spec + one bounded loss-check pass
(no loop). Loss check: zero binding losses; subsection-marker sets differ only by §12.1a;
per-milestone anchor bullets and frozen-test directory sets identical. Two stale in-body
counts r27 carried ("two parts" vs its own three-item enumeration; "Two spellings" vs three)
were resolved by dropping the figures per the count rule.

NEXT unchanged: m48 decomposition from the §12.4 ledger, owner-gated.

## 2026-08-26 — r29: critical streamlining pass (r28 → r29)

Owner directive: one thorough critical pass for further streamlining beyond r28's mechanical
apparatus strip. Diagnosis (from a full read of §1-§2.3, §6.1, §10 samples): five residual bulk
classes — (B1) vacuity engineering (the plan pre-litigating how a frozen test could be
mis-written, doing TEST_SANITY's and the test-author's job), (B2) negative-space enumeration of
wrong implementations/filters, (B3) the same rule restated at every touching site, (B4)
justification walk-throughs and rhetoric ("§2.5 confidently-wrong class" ~15 sites), (B5)
milestone-assignment defenses in §10. Canonical homes fixed: x[L]/.node_id conventions → §2.2;
label-aligned union → §2.4; MODE-decides → §6.1c; basename/pythonpath/vendoring/importorskip →
§10 preamble; b-tag-on-JES walk-through → §2.1.

Method: 14 parallel section streamliners under one spec + one bounded loss-check pass (no loop).
Result: 4586 → 3231 lines (r27 was 6444; net −50%). Loss check: all 42 r28 Binding: clauses have
counterparts (several merged), all 7 UNANCHORED markers 1:1, every directory pin/threshold/
control/§12.4 item present; §-marker sets and section headers identical. Repairs applied from
the check: restored the §5.1 no-API-language-implying-shift-order clause and the m49 per-repo
freeze-tagging clause; de-conflated §6.4d's refusal fixture from m51's legal same-offsets
object-migration case; restored §6.4a(2a)'s direction sentence; resolved the PRE-EXISTING
§9.1-vs-§10/m50 contradiction on the plan-level listing anchor's home in favor of §10/m50
(graphed-histogram flat m50 — the argued, importorskip-consistent side); dropped a false (§2.2)
citation on the 1-D fixture pin. Accepted widening: the importorskip prohibition is now one
universal §10-preamble rule instead of three per-anchor restatements. Committed per revision:
r28 and r29 as two commits, per owner call.

## 2026-09-01 — EXECUTION START (m48 arc opens)

Owner un-gated implementation: execute the r29 plan (276644c) with per-section review →
(re-plan | fold-in) → decomposition → gated pipeline → PRs (open, never merge). Isolated
sub-agents for plan/review/implement/impl-review; ultracode workflows; reviews at
BLOCKER/HIGH/MED/LOW/NIT (re-plan iff ≥MED; LOW/NIT fold-in, no re-review; >2 consecutive
prose-only rounds + stable design ⇒ pass with prose fixup).

Setup (persistent this time, not /private/tmp):
- Consolidated graphed cloned to **/Users/lgray/vibe-coding/graphed** @ ff7c607 (origin/main).
  Workdir submodule `graphed` is the OLD graphed-mvp — do not implement there.
- graphed-histogram: workdir submodule fast-forwarded to origin/main @ 211cbbe.
- Env: /Users/lgray/vibe-coding/graphed/.venv (py3.13, uv). graphed -e .[dev] (maturin build ok),
  graphed-histogram -e --no-deps, + boost-histogram 1.8.0 / hist / graphed-executors. Import +
  core-ext probe green.
- m48 plan block = lines 2191–2704 of systematics-vary-plan.md (r29).

m48 section review launched: workflow wf_bce65da0-b25 — 5 probe-driven lenses (frontend-claims,
histogram-corpus-claims, design-coherence, process-ci, feasibility-sizing; opus xhigh) →
adjudicate → adversarial verify of BLOCKER/HIGH/MED.

## 2026-09-01 — vary-m48 section review (wf_bce65da0-b25) → re-plan r30 issued

5 lenses probed ~200 claims; substrate overwhelmingly measured-true (discovery sets, key sets,
bh 1.8.0 pins, PYTHONHASHSEED byte-identity, §4.1 observable, §7.2 merge hazard + control all
confirm). 18 adjudicated → skeptics: 2 REFUTED (F1 two-repo ordering — executed m41 precedent
covers it; F11 ledger-vs-freeze phase mismatch), 3 RESIZED to LOW (F4 rounding spelling, F5
mypy-files instrument, F7 stage-members route). Surviving: HIGH F2 (required awkward-free
freethreaded CI job collects tests/frozen/frontend whole → gak-importing m48 anchors red it;
three-way split w/ new tests/frozen/awkward/m48), MED F3 (node-id→position off-by-duplicates,
§7.2:1809 + §6.1c:1251 → deduped rank), F6 (§4.1 anchor is fill-free → graphed's half; agc.py
fixture unreachable in histogram repo), F8 (golden GIR embeds unpinned bh version via
PayloadDescriptor), F9 (stacking anchor RHS `old_ambient_jes_up` unspellable without a parent
ambient registration — skeptic also invalidated the adjudicator's repair), F10 (node_id-getitem
control vs 1-D-numpy property fixture need different array forms → two fixtures). 9 LOW/NIT
fold-ins. Full evidence: scratchpad/vary-m48-section-review-result.json (session scratchpad).
Isolated planner vary-m48-replan-r30 (opus xhigh) dispatched: repairs F2,F3,F6,F8,F9,F10 +
folds F4,F5,F7,F12–F18; F1/F11 untouched. Next: commit r30, delta review loop until no B/H/M.

## 2026-09-01 — r30 committed (b6d031e); delta review round 1 launched

Planner vary-m48-replan-r30 applied all repairs + fold-ins (+75 net lines, 172/97; consistency
greps all zero w/ live control; two adjudicated repair-texts rejected on measured grounds — F4
drop_none clause false, F9 label-set clause wrong — skeptic-corrected versions used). Notable
class repairs: F2 → whole §2.6 context family + §1.1/§2.1/§6.1d/gak/§4.1 anchors → NEW
tests/frozen/awkward/m48 (run-tests.sh globs it; freethreaded job never collects awkward tree);
F8 golden normalizes descriptor version (single occurrence in blob, removal deterministic,
axis-count still discriminates); multi-axis fixture granularity class closed 3/3.
Precommit gate on workdir: toml+integrity ok; pytest leg = 133 PRE-EXISTING submodule collection
errors (venv lacks old -mvp pkgs), unrelated to docs diff.
Delta review r1: wf_e14f2757-313 — lenses structural/semantic/regression (opus xhigh) →
adjudicator tags verify_route → routed skeptics (sonnet/high mechanical-recheck, opus/xhigh
semantic; owner-approved routing). Exit condition: zero B/H/M.

## 2026-09-01 — delta round 1 on r30 (wf_e14f2757-313): NOT clean → r31 dispatched

3 lenses (23/41/46 claims) → 9 adjudicated (2H/4M/3L) → routed skeptics (4 sonnet mechanical,
2 opus semantic): F1 HIGH CONFIRMED (§6.3 version-normalization content-derived from LIVE
bh.__version__ — never touches committed literal on a bump; probe p_ver.py shows fail + two
sound transforms), F2 HIGH→MED (awkward-free rule (2) scoped to m48 only; §5.3 gak anchor in
frontend/m49 reds the same required gate; one-clause respell suffices), F3 MED (dict.fromkeys
over unhashable Array — spell over node_ids; Array.__hash__=None by design), F4 MED (§2.1(b)
L-range excludes labels the call registers → headline weight matrix unbuildable as worded; range
= §2.4 union), F5 MED (§12.1 graphed gate swap silently drops integrity/toml/workflows legs),
F6 MED (basename enumeration wrong both directions after the same commit's tree move). LOWs:
F7 §8.2 mypy-scope member, F8 property-fixture operand-kind, F9 stale two-tree language.
Routing note: mechanical-recheck skeptics (sonnet/high) upheld cleanly incl. the F2 downgrade.
r31 dispatched to planner vary-m48-replan-r30 (F1–F6 + fold-ins F7–F9).

## 2026-09-01 — r31 committed (d090c52); delta round 2 launched

Planner applied d1-F1..F9 (+32 net; 92/60): F1 → committed-literal-pre-stripped + per-side live
strip (laziest sound reading, no T_EXTERNAL byte-walk); F2 → both halves (rule (2) repo-wide
m48–m51 + §5.3 respelled awkward-free at requirement AND m49-anchor sites, m5 inline-backend
precedent probed; §5.4 bound conditionally — awkward-free fixture keeps frontend/m49, gak.join
refusal takes awkward/m49); F3 → id-spellings both sites + 2 stragglers; F4 → L over §2.4 union
w/ new-label answer; F5 → precommit --fast (run_gate keeps toml/workflows/integrity/prek under
--fast, probed) + COV=1 run-tests.sh; F6 → rule + regenerating find, binding examples swapped;
F9 class scan found 9 sites (3 beyond the finding), repaired via one REPO-level lead-in + 6
rewordings. Greps: stale 0/new 1 with live controls. No new ≥MED.
Delta round 2: wf_cea280b4-7c4 — 2 lenses (repairs, regression; opus xhigh) → adjudicate →
routed verify. Exit: zero B/H/M.

## 2026-09-01 — delta round 2 on r31 (wf_cea280b4-7c4): 1 MED + 4 LOW + 2 NIT → r32 dispatched

All nine r31 repairs verified closed (65 claims across 2 lenses; golden-strip rule re-probed
across length-changing bh bumps incl. discrimination controls; dedup spellings run live; §5.3
awkward-free respell exact vs projection.py conservative branch; --fast probed as strict
superset of the uvx prek command it replaced). Sole MED (d2-F1, skeptic-confirmed): rule (2)'s
correct m48–m51 widening was not re-walked over m49's 12 anchor bullets — §2.5's
shift-after-weight diagnostic left unplaced, defaults into frontend/m49 which the required
awkward-free 3.14t gate collects whole (same class as d1-F2); "it alone takes awkward/m49" is a
falsified universal. LOWs are layout-list/trap-list/rule-ground bookkeeping of the same
generalization; NITs prose. r32 dispatched (F1 + fold-ins F2–F7 + full m49 re-walk). Loop
trajectory: 6→1 confirmed ≥MED per round, defect class narrowing to bookkeeping of the
review's own repairs.

## 2026-09-01 — round 3 on r32 (agent vary-m48-d3-review): 0 B/H/M → m48 PLAN LOOP CLOSED

Single-lens proportionate check + whole-artifact spot check (exit-round rule). d2-F1 repair
verified independently (13/13 m49 bullets homed; §2.5 placement FORCED by §2.1(b)+rule (2), not
chosen); all fold-in code-facts probed w/ live controls (find-command regenerates trap list,
control-without-exclusion shows exactly the m40 false positives; 9/9 referenced trees in §10
layout list; core's in-process sys.modules guard confirmed). Verdict: 0/0/0/1 LOW/2 NIT.
LOW = §5.4 witness citation points at backend-primitives file; true witness =
frontend/m40/shuffle_backends.py REAL_BACKENDS numpy case (design decision itself verified
sound). Final fold-in r33 dispatched (no re-review per process). Loop trajectory across rounds:
6 → 1 → 0 confirmed ≥MED. Next: commit r33, m48 DECOMPOSE.

## 2026-09-01 — r33 committed (ca475c4); m48 DECOMPOSE dispatched

r33 = exit-round fold-in (+7: §5.4 witness repointed case-scoped to REAL_BACKENDS numpy;
§7.4 mechanism→checkpoint/m49 vs label→§8.2 executors anchor; rule (2) trigger list exact).
Plan loop m48 CLOSED at r33. Memory updated (plan memory + index). Decomposer
vary-m48-decompose (opus xhigh, isolated) writing vary-m48-decomposition.md: anchor→tree→file
map w/ collision check, impl inventory (sizing-lens numbers adjusted for the r30–r33 tree
split), ≤1–2k-LOC commit partition, pipeline schedule (freeze order w/ m41 cross-repo
ImportError precedent, tags, .graphed/m48, TEST_SANITY expected failures, deferred-spelling
grep for the test-author), per-repo gates + CI additions, out-of-scope fence.

## 2026-09-01 — decomposition delivered; review launched (wf_297aba71-4b0)

vary-m48-decomposition.md (702 lines, 63 ids): 13 commits, graphed arc 3790 freeze
(frontend/m48 1070 + awkward/m48 2720) + 1805 impl; histogram arc 2040 freeze + 560 impl +
425-LOC vendored corpus. Decomposer's own decisions (measured bases): (a) STRICTLY SEQUENTIAL
arcs — histogram CI installs graphed@main in every job, so m41's expected-ImportError freeze
route would make all 12 histogram TEST_SANITY files vacuous (fail on missing frontend, never
on fill lowering); (b) §6.3 golden capture pinned to graphed@ff7c607/histogram@211cbbe (§0)
since the histogram arc now runs post-graphed-landing; (c) no shared cross-tree fixture module
(frontend tree must import under pytest+hypothesis+numpy only) — three same-dir helpers;
(d) tags m48-freeze (graphed) / freeze-m48 (histogram), per-repo precedent. Zero plan defects
found (agc.correctionlib_json + record_external re-probed live). Risks: R1 fill rewrite ~300
LOC into 357-LOC boost.py w/ 6 anchors on one method (H-T3 authored as one contract, H-I1
scoped to fill); R2 awkward-free frontend boundary = collection-time CI failure (numpy-idiom
fixtures via loose §2.1a vary); R3 two anchors green-on-HEAD (F3/H12) → TEST_SANITY rejection
criteria named in doc §4.3.
Decomp review: wf_297aba71-4b0, lenses fidelity/feasibility (opus xhigh) → adjudicate →
routed verify. Exit: 0 B/H/M.

## 2026-09-01 — decomp review (wf_297aba71-4b0): 1 BLOCKER + 2 MED → rev 2 dispatched

Lenses fidelity (48 claims) + feasibility (84 claims); 16 adjudicated; routed verify (F1 skeptic
died on StructuredOutput cap → re-run standalone, sonnet). CONFIRMED: F1 BLOCKER (A8(b) bundles
the fill-label-superset half plan 2314-2318 routes to graphed-histogram; grep superset = 1 doc
hit vs 13 plan hits live-control; only def fill( in either repo = boost.py:153), F2 MED (68→65:
plan's __module__ filter dropped, 3 re-exported descriptor helpers admitted), F5 MED (collapsed
AttributeError claim for six histogram anchors; real modes differ per anchor; Varied
determinately non-Array). RESIZED→LOW: F3 (registry row missing = impl-detail omission within
doc's stated scope), F4 (skeptic: "nothing graphed-side covers golden" measurably FALSE +
tests/extra remedy unbuildable → one-line sequencing note only), F6 (half refuted). Clean
otherwise: 20/20 anchors mapped, both self-made decisions upheld (sequential arcs; §0 golden
pin), basename clearance 32+3 names/0 collisions all scopes, all 10 LOC anchors recompute,
H-C0 vendoring verbatim vs preamble + ruff/integrity clean w/ fired controls.
Rev 2 dispatched to vary-m48-decompose (F1+F2+F5 + 13 fold-ins w/ verdict-corrected actions).

## 2026-09-01 — decomp rev 2 closure check (vary-m48-dc2-review): 0 B/H/M → ACCEPTED

16/16 rev-1 findings verified closed per verdict-corrected actions; every probe reproduced
(65-count via plan's __module__ filter; 5 fill failure modes driven live incl. DID-NOT-RAISE for
H7/H8 and AttributeError-for-none-of-six; all LOC rollups recompute to 8850; F13's
executors-unaffected grep 0 hits w/ histogram control 4). F1 class repair verified: fill-shaped
assertions now only in H rows (A-row scan clean); H6 carries the relocated superset + A7 halves.
5 adversarial plan spot-checks pass. Residual: 2 LOW (stale 1150 figure in §7 R1; cite 664→703)
+ 3 NIT (2 review-history prose sites, 1 dropped qualifier) → rev 3 fold-in dispatched, no
re-review. NEXT: TEST_AUTHORING, graphed arc (G-T1..G-T3, est 3790 LOC frozen).

## 2026-09-01 — decomposition FINAL (rev 3, 765 lines); TEST_AUTHORING opens (graphed arc)

Rev 3 fold-in applied (5 sites). vary-m48-decomposition.md = frozen DECOMPOSE artifact (stays
untracked per m41 precedent). Pipeline: graphed arc first (sequential; histogram TEST_AUTHORING
may start once graphed IMPLEMENTING closes, DONE needs main — doc §4.1). Test-author dispatched:
branch m48-vary off ff7c607, commits G-T1 (frontend/m48 F1–F8+fixtures, 1070) / G-T2
(awkward/m48 A1–A6+fixtures, 1500) / G-T3 (A7–A12 + preserve/m9 pythonpath, 1220); freeze tag
m48-freeze AFTER I verify TEST_SANITY (author does not tag/push).

## 2026-09-01 — graphed arc FROZEN (m48-freeze @ 37d86cf); IMPLEMENTING opens

Test-author delivered G-T1/T2/T3 (5860280/6f9ba35/37d86cf): 25 files, 2404 insertions, 112 test
fns (2265 py LOC — leaner than the 3790 est; ~20 LOC/fn vs m40's 37). TEST_SANITY verified
INDEPENDENTLY (scope diff clean; 110 red all named-absent-symbol at call time — attribute access
not from-import, so zero collection errors; 2 green both decomposition-named w/ criteria;
blocker probe frontend-clean + m3 control fires; spot-reads show witnesses/discriminators).
§4.4 spellings pinned incl. graphed.vary signature, gnano.events, on_compiled hook,
CompiledGraph.unreached_labels, 4 src classification tables (VERB/SURFACE/GAK_DISPOSITIONS,
GAK_ARG_FIXTURES). 5 recorded deviations: fixture dup forced by §1.4; union floor keys
(package,name) pairs; labels(root-ctx) UNSPECIFIED → implementer decides + records; non-constant
pu_weight (anti-coincidence); awkward/m16 5-red PRE-EXISTING env artifact (verified independent
of m48 via pythonpath rollback probe) — implementer must treat as known-env-red, not fix.
Coverage trap: run-tests.sh invokes bare python — venv must be on PATH or --cov dies.
Tagged m48-freeze (not pushed; push at PR). Implementer dispatched: G-I1..G-I4 on m48-vary.

## 2026-09-01 — graphed arc IMPLEMENTING complete w/ TEST_DISPUTE; adjudication dispatched

Implementer delivered G-I1..G-I4 (d376ce2/b8cfcb7/ab95261/fdbc2ae, 2128 insertions): 110/112
frozen green, whole-suite no regressions (7 red = 5 known-env m16 + 2 disputed), combined cov
93% (frozen-alone 92%; accessors.py 68% frozen-alone — the gap is histogram-side anchors; +2
tests/extra files lift to 99%), ruff+mypy-strict clean, determinism green. Root-ctx labels
decided ("nominal",). DISPUTE (proper stop, clean hands: diff m48-freeze..HEAD -- tests/frozen
= 0 lines): test_lineage_seams 2 tests demand plain-Array reads through shift-varied /
Varied-mask-derived contexts; plan §2.6b/§2.6c bind Varied (measured w/ Photon controls —
fixture shifts BOTH Jet+MET, leaving no unvaried branch; test-author fixture slip, intent
sound). Proposed corrections preserve anchor intent (Photon read; nominal-projected target or
`is`-identity). Adjudicator vary-m48-dispute-adjudicator dispatched (independent, opus).
If upheld → test-author corrects 2 tests → re-freeze m48-freeze2 → implementer re-verifies.

## 2026-09-01 — dispute ADJUDICATED: UPHELD; correction with test-author

Independent adjudicator re-measured (both Photon controls live), verified clean hands via blob
hashes (test_lineage_seams 14b0f91e at both m48-freeze and fdbc2ae; 0 frozen paths in 27
changed), closed 3 named escapes + 1 unclaimed (§2.6b named-collections incl. MET per the
lockstep fixture; link-kind-(1) obliges the FIXTURE to supply the unvaried operand; reindex_to
identity worded over HANDLES §6.1d(B)/1354-5; §2.6c "implicit property of the derivation").
Ruling: tests' anchors sound, operands mis-chosen. Correction: test 1 operand → shifted.Photon.pt
(5/5 assertions kept); test 2 → adjudicator's per-label node_id spelling (STRICTLY stronger;
dispute's own option B refuted — `is` returns False against conforming impl, over-binds object
identity vs plan's structural convention 513-517). Both green on fdbc2ae. Test-author applying
as re-freeze commit → I verify + tag m48-freeze2 → implementer re-verify → 3-lens impl review.

## 2026-09-01 — re-freeze m48-freeze2 (affd355); dispute closed; final gate pass running

Test-author applied corrections (affd355, 6+/3−, only the one frozen file; README correctly
untouched — no row references operands) + independently re-measured the dispute premises incl.
non-vacuity of the new per-label loop (3 labels; re-indexed member ids differ). My verify:
frozen diff scope = 1 file, both m48 trees 112/112 (exit 0). Tagged m48-freeze2. Resolution
appended to dispute file (86f7d91). Implementer running final full-gate pass on tip; 3-lens
impl review next. Probe trap recorded: bare imports of frozen fixtures need
PYTHONPATH=tests/_corpus:tests/frozen/awkward/m48 (pytest supplies via pyproject pythonpath).

## 2026-09-01 — graphed final gates GREEN (tip 79a61a7); impl review + histogram TEST_AUTHORING in parallel

Final gate pass: 112/112 frozen (0-line source delta vs m48-freeze2 — corrections satisfied by
existing impl), whole suite green modulo 5 known-env m16, combined cov 93 / frozen-alone 92
(accessors.py 68 frozen-alone = cross-repo gap, 99 w/ extras), ruff+format+mypy clean,
attempts.md 9 iterations (79a61a7). Untracked uv.lock noted (mine, from env setup — keep out
of PR). Dispatched in parallel per decomposition §4.1 weaker condition:
(1) impl review wf_29716736-1a5 — 3 lenses design/integrity/mutation (mutation = 10 required
targeted mutants M1–M10 + ~4 self-designed, worktree-isolated) → adjudicate → routed verify;
REJECT iff ≥MED confirmed.
(2) histogram test-author (vary-m48-test-author-histogram) — H-C0 vendor (git archive @ff7c607)
+ H-T1..T3 on graphed-histogram branch m48-vary; graphed-m48 present via editable venv so reds
are histogram-side per §4.3's corrected modes; golden captured at §0 pins PRE-m48 + stored
stripped.

## 2026-09-01 — histogram arc FROZEN (freeze-m48 @ 40f9b48); implementer dispatched

Suite: 4 commits (H-C0 a4be7aa vendor 30f/1491; H-T1 7876ccc; H-T2 b15e05a; H-T3 40f9b48) =
57 fns/66 items/1542 LOC (vs 2090 est). TEST_SANITY verified independently: 50 red ALL
histogram-side (28 weights-guard TypeError, 10 args-guard, 3 unweighted-kwarg, 3+1 missing
accessors, 2 spans-length = absent re-indexing, H7 trio), 16 green each named (7 goldens
sentinel, 6 H8 divergence sentinels — §4.3's DID-NOT-RAISE prediction MEASURED WRONG: the m48
frontend's unify_contexts in record_external already raises; kept as regression sentinels w/
rejection criteria vs H-I1), m23/m29 exit 0, scope clean. Golden committed PRE-STRIPPED
(pattern b'\x05\0\0\01.8.0': golden 0 hits / live 1 = control; strip(live)==golden; BONUS:
graphed m48 tip reproduces the same stripped blob = no-variation paths unchanged, §6.3's
sentinel already discharged once). Histogram-side spellings pinned (unpack, fill_nodes_by_label,
plan-value keys, unweighted=, GraphedError refusals, 3 distinguishable length messages).
Frontend observation (recorded): refused record_external leaves one orphan arena node (DCE'd,
harmless). Tagged freeze-m48. Implementer vary-m48-implementer-histogram dispatched (H-I1 fill
lowering, H-I2 group/plan surface). graphed impl review wf_29716736-1a5 still running.

## 2026-09-02 — second TEST_DISPUTE (histogram H9) → adjudication dispatched

Implementer filed mid-arc (continuing other 65 items; clean hands): H9's ancestor-re-indexing
fixture reads root.MET.pt which is CONTEXT-FREE (gnano.events leaves argument context-free);
plan §6.1d ~1385-90 binds loose values row-space-unadjusted, and H7 freezes the same shape as
the value[i] refusal — mutual exclusivity measured (reindex_to identity on loose; 400-vs-234
rows). Proposed: read through events (genuine ancestor ctx), assertions unchanged. Sent to
vary-m48-dispute-adjudicator w/ pointer: the plan's own H9 anchor bullet spells
h.fill(events.MET.pt, sel.MET.pt) — the plan's fixture spelling may settle it directly.

## 2026-09-02 — graphed impl review (wf_29716736-1a5): REJECT 1H/5M → fix cycle dispatched

3 lenses (25/34/27 claims): design REJECT, integrity APPROVE (frozen tree 256 blobs byte-equal
since m48-freeze2 w/ control; only config delta = the bound pythonpath line; 0 stubs/hardcodes
via AST string-literal sweep; suppressions all error-code-scoped), mutation REJECT (all 10
required mutants CAUGHT incl. label-leak/union-order/re-index-skip/two-level/determinism; the
escapes = its 4 MEDs). 13 adjudicated, 6 hot ALL CONFIRMED (sonnet mechanical-recheck skeptics
w/ fresh-worktree reproductions): F1 HIGH _vary_loose re-indexes only NEW members (mixed row
spaces 200v102, context_of claims derived); F2 _vary_weight lacks the sibling duplicate-label
guard; F3 _mask_key keys on nominal node_id alone (adversarial silent-corruption pair built);
F4 no-label scan blind downstream of containers (witness gap only); F5 labels lost across
EventContext._project → §2.5 diagnostic dead on context programs; F6 union_tags unwitnessed
through §2.4 ops (M11 escape). Also: §1.1 grammar drove 18 spellings incl 1e1000000000 in 9µs;
beyond-inventory changes both validated (unflatten = R17.0 parity; read_columns None-dominance
= real pre-existing bug w/ old-algorithm repro); root-ctx ('nominal',) decision upheld by
derivation. Fix cycle → implementer: F1,F2,F3,F5,F7,F10,F13 impl + extras; F8,F9,F11 records.
**vary-m49 freeze ledger (carried): ir-F3/F4/F5/F6 anchors + d2-era §5.4 conditional + F7's
follow-up if deferred.** F12 uv.lock removed (was mine). Decomposition conftest line corrected
(ir-F11 half). Histogram implementer + H9 adjudication still in flight.

## 2026-09-02 — H9 dispute ADJUDICATED: UPHELD; correction with histogram test-author

Decisive: plan's own H9 bullet (~2696-2702) spells h.fill(events.MET.pt, sel.MET.pt,
sample=events.<field>) — reads through the CONTEXT; author transcribed events→root (loose).
Rescue reading (gnano stamps root) closed 3 ways incl. graphed's own frozen anchor
context_of(root.MET.pt) is None — stamping would red one frozen suite to green another.
Narrow rescue (re-index axis but not factors) closed by §6.1d 1385's "inputs" wording + 1388
naming the shape as H7's refusal. Correction = implementer's verbatim (0 assertion delta; row
sets 234/243/224 measured both arms; WeightedMean pins untouched). Clean hands verified w/
live control (caveat honest: end-to-end green unverifiable pre-lowering; seam half proven).
Correction dispatched to test-author (path-scoped add — implementer working concurrently in
same tree on src/). Re-freeze tag freeze-m48-fixup after my verify.

## 2026-09-02 — H9 re-frozen (freeze-m48-fixup @ 90c5d6d); histogram implementer continuing

Correction applied verbatim (1 file, 3+/2−, path-scoped; src/.graphed untouched). Verified +
tagged. Bonus signal: corrected H9 already PASSES against the implementer's in-flight fill
lowering (fill_nodes_by_label present; unpack absent = H-I2 in flight). Implementer notified:
no lowering change needed, frozen tree now final, gates against tip incl 90c5d6d.
In flight: graphed fix cycle (ir-F1..); histogram H-I1/H-I2 completion.

## Histogram H-I complete — clean-hands verification (2026-09-01)
Implementer reports arc done at tip f546d44 (H-I1 8f8014a fill lowering, H-I2 f546d44 group/plan
surface); 2 attempts.md iterations. My independent checks (all from the histogram submodule, shared
graphed .venv):
- `git diff freeze-m48-fixup -- tests/frozen` EMPTY, control diff shows 581 insertions elsewhere.
- frozen+extra suite exit 0; collected counts 66 m48-frozen / 97 total (file-by-file sums match).
- sphinx -W: implementer's env lacked sphinx; I installed sphinx+furo into the venv and built —
  exit 0, "build succeeded". Gate table now fully green locally.
Implementer-flagged design call for review: `_WeightGuard` External recorded upstream of the
broadcast seam to carry record-time blame strings for §6.1d's three length messages (frontend seam
at 79a61a7 measured not translating awkward's ValueError). Next: three-lens impl review.

## vary-m49 freeze ledger additions (from histogram implementer observations, 2026-09-02)
- Plan-text reconciliation: §6.1d assigns the awkward ValueError translation to "the seam's
  awkward implementation" but at graphed@79a61a7 the seam (AwkwardBackend.broadcast_like /
  gak.broadcast_arrays) never translates, and blame (ambient vs weight[i] vs value[i]) is
  fill-local — the contract landed histogram-side as `_WeightGuard`. Amend the sentence at m49.
- graphed frontend wart: `Session._wrap` raises AFTER `record_external` adds a node, so a refused
  fill leaves a stray session node (histogram's own unification refuses before recording; the H8
  frozen anchor is scoped to histogram staging so it is green either way). m49 candidate fix.

## Both m48 reviews dispatched (2026-09-02)
- Graphed fix cycle 38eebf6 clean-hands verified: frozen untouched since m48-freeze2 (empty diff,
  363-insertion control), suite reproduces the 5-member m16 known-env red set exactly, nothing new.
  F8 settled without collapse: reviewer 90.24% = arc delta at 79a61a7 (801 lines/326 arcs),
  implementer 94.25% = at 38eebf6 (795 lines/1188 departing arcs) — different tip AND arc
  convention, both >90 gate; attempts.md dual record with commands kept. clippy = known
  toolchain-unresolvable env cell.
- Histogram impl review: wf_b72fb7b4-9da (design opus/xhigh incl. _WeightGuard call; integrity
  opus/high re-establishing all 10 gates; mutation opus/high with 9 required surfaces incl.
  refuse-before-record) → adjudicator → routed skeptics.
- Graphed delta re-review: wf_e291240f-c2e (fix-correctness opus/xhigh with F1 link-kind population
  walk + adversarial member hunt + blunt-form premise probe; integrity opus/high replaying all 6
  witness mutations + cross-repo histogram leg) → adjudicator → routed skeptics.
- After both: PRs opened, NOT merged (user instruction), then §12.3 bookkeeping.

## HAZARD: parallel mutate-and-restore in shared trees (2026-09-02)
The delta-rereview integrity lens measured a collision in /Users/lgray/vibe-coding/graphed: a
sibling's mutation landed mid-replay-loop and its `git checkout -- python` restores clobbered
in-flight state — mutation verdicts from that window unreliable BOTH directions. Root cause: my
workflow prompts allowed two graphed lenses + one histogram lens to mutate/read the same trees
in parallel instead of using per-agent isolated worktrees. Repair: integrity lens self-isolated
(detached worktree wt-integrity @ 38eebf6, .so copied, PYTHONPATH pinned, everything re-run);
I mandated the same protocol to the correctness + histogram-mutation lenses and tree-clean
bracketing to the read-only lenses; pre-hazard mutation-dependent results declared void and
re-run. Editable-install trap noted: PYTHONPATH prepend may lose to the editable finder —
verify import location with `print(module.__file__)` before trusting a worktree run.
RULE for future review workflows in this project: any lens that mutates source gets
`isolation: 'worktree'` (or an explicit detached worktree + import-location probe); suites that
import an editable sibling repo bracket runs with clean-tree checks on BOTH repos.

## Lens results landing (2026-09-02, pre-adjudication)
- HIST design lens (post-hazard, pristine git-archive exports, byte-identical probes at 79a61a7 AND
  38eebf6): REJECT pending 3 MED — hF1 `_blame` loose-branch fires on ANY loose axis arg (blame
  must follow inputs[0], the compared operand); hF2 §6.1d contract covers only outer-length faults
  (nested-broadcast failure surfaces RAW ValueError; frontend observation #1 hides a real gap
  HERE); hF3 blame PROSE inside content_hash → PayloadDescriptor → IR → a copy-edit invalidates
  every checkpoint of a varied analysis (repair: hash the blame coordinate, prose in evaluator
  field; secondary: version="" preservation hole). LOW: hF4 mixed-plan refusal names wrong output;
  hF5 _slots uses hist._spec not fill-node spec (m50 must change). §7.2 budget/dedup-rank/§1.2/
  §6.3/_WeightGuard-load-bearing all confirmed sound by probe.
- HIST mutation lens (journal; possibly pre-mandate window, isolated re-check pending): APPROVE +
  MUT-1 MED (deleting weight-factor re-index survives whole frozen+extra; code correct, suite gap
  — m49 freeze ledger) + MUT-2 MED (blame contract anchored only via session.materialize; plan-path
  blame mis-attribution survives with zero reds — collapsing per-message chash mis-blames on plan
  path).
- GRAPHED integrity+replay lens (isolated wt-integrity; first replay loop VOIDED per disclosure):
  REJECT — gF-A HIGH: F2 fix over-broad, refuses a weight correlated with the SAME nuisance as an
  existing shift (parent ACCEPTED, HEAD REFUSED, driven probe; §2.1 one-knob composition legal;
  plan r33 L466-470 subject matches; narrow registry-scoped form validated 112/112+21/21+ACCEPT).
  gF-B MED: attempts.md iter-10 scan figures stale (its own prose trips skip_or_xfail_added;
  counts off by one; planted control reproduces). All 6 witness replays + 3 positive controls
  reproduce; suites/lint/coverage/cross-repo(97/97 pinned import) green; pyproject delta
  comment-only. Pre-existing out-of-delta note: _vary_loose `if label in existing` same shape.
Plan: batch graphed fixes (gF-A + gF-B) after correctness lens lands; histogram fix cycle after
its adjudication (hF1-hF3 ~20 lines in _blame/_guard).

## HIST mutation lens isolated re-run (2026-09-02): APPROVE, 19 mutants 16/3
Shared-tree runs discarded; all verdicts from detached worktree (pytest pythonpath=["src"] beats
the editable finder — verified RESOLVED path). Survivors: F-MUT-1 MED (weight-factor re-index
unwitnessed — M19 survives whole suite; live control + non-equivalence probe), F-MUT-2 LOW-MED
(constant guard chash mis-blames by index on the PLAN path only; materialize path anchored),
F-MUT-3 LOW (compile budget not asserted in this repo; spy must target graphed.execute.compile_ir,
not aggregate — first attempt mis-read 1/1). Implementer's "H8 green either way" claim MEASURED
FALSE in the suite's favour: M14b (stage node + re-raise same error) reds exactly
test_no_fill_node_is_staged_by_the_refused_fill. Golden strip lives in the frozen test, out of
src-mutant reach; its instrument test forbids unstripped goldens. Cross-repo: all probes identical
at graphed 38eebf6. NOTE for adjudicator: F-MUT-2 + design hF3 converge — hash the blame
COORDINATE (per-blame distinct, copy-edit stable); satisfies both directions.

## GRAPHED correctness lens (isolated re-run, 2026-09-02): REJECT — C1/C2 MED, C3 LOW/MED
C1 == integrity gF-A (independent convergence, same registry-scoped old._tags repair, C1 adds
ORDER-DEPENDENCE: same program accepted/refused by registration order). C2: F7 fixed one of two
structural twins — awkward/io.py:153 _syntactic_fields still external=lambda:None; masked set
omits a column the External replays against (live 4-row table with narrowing controls); class
repair = share the lifted reads_source predicate. C3: post-F1 a Varied-mask vary hides jes_up
(surfaces on arithmetic; universe() loop dies) — nested shape pre-existing, hidden label new.
F1 depth: link population {mask,project,vary} instrument-derived; blunt-form premise CONFIRMED
twice; adversarial hunt found C3 as the refuting member. All 6 witness replays + reverse-direction
controls hold; F3/F5/F10/F13/F11 dispositions correct. m49 ledger adds: frozen m48 witnesses NONE
of F1 (drop _align → 112/112 green); loose-value row spaces deliberately mixed (§6.1d) — name it.
Next: await both workflow adjudications; then ONE batched graphed fix cycle (C1/gF-A, C2, gF-B,
C3 disposition) and the histogram fix cycle (hF1-hF3).

## HIST integrity lens (isolated re-run, 2026-09-02): PASS — 0 B/H/M, 4 LOW + 1 NIT
Retracted its own would-be BLOCKER (suite flakiness 2/5 red, coverage 82.71↔96.16 swing) after
tracing it to the sibling mutation lens editing the shared editable graphed install; 10/10 green
isolated. All 10 gates re-established live incl. cross-revision (79a61a7 vs 38eebf6: golden,
budget, determinism, 97/97 byte-identical). attempts.md three quantitative claims exact. LOWs:
sphinx claim (RESIZED by lead: TRUE when written — I installed sphinx AFTER the report; NIT at
most), state.json metrics_history missing red iter-0 row, prek ruff-resolution env failure,
tests-not-typechecked (pre-existing repo-wide follow-up). NIT: dispute .md landed one commit late
(mtime proves authoring order). _WeightGuard: no integrity objection (spec text hashed, not
fixture data; H6 corroborated by golden probe).
NEW FLEET HAZARDS (add to review-workflow rule): namespace probe files per lens (shared scratchpad
collisions observed); sibling `git worktree prune` deletes foreign worktrees + missing-PYTHONPATH
dir silently ignored → always assert module.__file__ provenance in probe scripts.

## GRAPHED delta re-review ADJUDICATED (wf_e291240f, 2026-09-02): REJECT — 3 MED CONFIRMED
A-1 (=FC-1/gF-A/INT-2 merged; adjudicator normalized HIGH→MED): F2 check keys on §2.4 union not
registration set; repair = old._tags-derived labels (both lenses validated). A-2 (NEW, found post
free-text): _align before dup-guard → None._links_below AttributeError escapes where 79a61a7
raised GraphedError; repair = guard first. A-3 (=gF-B): scan record non-reproducing (26/15 vs
25/14; both new hits self-referential prose). A-4 NIT docstring. DROPPED: FC-3 (plan §2.1
two-level rule blesses nested inherited labels — adjudicator re-measured resolution correct;
residue → A-1 witness obligation + m49 plan question: does §2.2 labels() flatten nested?);
FC-4 merged into A-1 as test obligation. C2 (io.py:153 twin) never entered structured output —
lead re-bought premise (grep: ONLY remaining external=lambda site) and issued as F7 class
completion with lens measurement attached. Fix cycle 2 dispatched to implementer-graphed
(A-1 a/b/c witnesses, A-2, A-3 record correction, C2, A-4). Adjudicator skipped re-verifying
6 replays + gates (both lenses agree; verification-of-verification declined — correct).

## HIST impl review ADJUDICATED (wf_b72fb7b4, 10 agents, 2026-09-02): REJECT — 5 MED post-skeptic
A1 preserve-plugin gap RESIZED HIGH→MED (m50 owns §9.2 varied preserve surface; m48 repair = make
plugin WRITABLE: coordinate in params + real version). A2/A4 = one class (blame naming untested
operands: loose-branch not keyed on inputs[0]; merge refusal blames varied output for unvaried
sibling's merge). A6 plan-path blame unanchored (materialize-only). A5 weight-factor re-index
unwitnessed. CLUSTER A1+A6+A7 = ONE edit at _guard (hash on blame coordinate, coordinate→params,
prose evaluator-side). A3 RESIZED MED→LOW w/ kill probe (nesting class died bare pre-m48 too;
never-decomposed seam binding, §2.1 bars awkward dep in histogram → m49 PLAN decision). A11
overruled by lead timing fact. A8 LOW but §6.1c-binding → fold-in (witness impossible until m50).
DROPPED INT-2..5 (collision misattribution/env/closed-in-review/self-refuting). _WeightGuard
adjudicated SOUND as mechanism (ordering graph-guaranteed by data dependence; M3/M4/M5/M15/M10
discriminate), defective in 3 details. Fix cycle dispatched to implementer-histogram.

## vary-m49/m50 ledger additions (from histogram adjudication)
- m49 PLAN decision: §6.1d ValueError-translation binding never decomposed on either side
  (vary-m48-I-bcast omits the wrapper); no local fix exists (histogram len()-only per §2.1;
  broadcast_like has no blame channel). Decide: m48-fixup vs m49 seam work.
- m49 test-authoring anchors: weight-factor re-index (A5 mutant), plan/executor-path blame (A6),
  compile-budget spy at graphed.execute.compile_ir (A9 + definition-site trap), golden per-side
  strip discriminator (A10), unvaried-only merged plan IndexError (pre-existing, measured at
  freeze-m48-fixup), varied-mask _align path (graphed side, FC-3 residue).
- m50: preserve plugin for histogram.weight_guard kind (payload now derivable post-fix);
  _slots fill-node-spec witness (§6.2 divergence enables it).

## Both fix cycles landed; both delta reviews running (2026-09-02)
- GRAPHED f7deb10 (fix cycle 2): clean-hands green (frozen untouched, suite = 5-member m16
  baseline exactly); delta-3 reviewer vary-m48-delta3-review (opus/high, isolated worktree,
  probe replay + 5-mutation table + same-family-twice adversarial admit check) running.
- HIST a474a93 (fix cycle 1): all 5 MED in one commit; A1/A6/A7 = coordinate-keyed identity +
  params blame + real version; A4 = per-output recompile ON REFUSAL PATH; A8 honest no-witness
  row (mutant survives, stated). Clean-hands green (frozen untouched, suite exit 0/0 FAILED).
  delta-2 reviewer vary-m48-hist-delta2-review (opus/high) running with adversarial focuses:
  success-path compile budget vs refusal-path recompiles; A6 parity index-1 leg (witness table
  only showed [0]); coordinate-collision identity check (two messages, one coordinate).
Next: on 0 B/H/M each → open PRs (graphed, histogram), do NOT merge; then §12.3 bookkeeping.

## GRAPHED delta-3 review (2026-09-02): REJECT — 1 MED (D3-1), all else verified closed
A-1/A-2/A-3/C2/A-4 all replay closed with parent controls (A-1 both orders + §2.4 fallback shape
{nominal 1.0, jes_up 1.1, pu_up 1.2, jes_down 1.0}; A-2 crash class complete incl. _vary_shift
sibling audit; C2 class complete — only other external=lambda is session.py:323 evaluator, not a
walk; A-3 fixed point w/ live control; 5-row mutation table replays; suites/gates green, m16
baseline byte-identical). D3-1 MED: re-keyed check discriminates by carrier KIND not family NAME —
admits cross-name collision (shift name=sf_up,tag=x vs weight name=sf,tag=up_x both spell
sf_up_x → one label on two independent knobs; parent refused). Round trajectory 6→3→1; repair
form pending reviewer tail (correct predicate = name-provenance: refuse existing label unless
produced by the SAME family name).

## Fix cycle 3 dispatched (2026-09-02): D3-1 family-name keying
D3-1 tail: one label two knobs measured (shift 1.05 + weight 3.0 on sf_up_x; compile_ir silent,
universe materializes). Reviewer-validated repair = family-name-keyed population over the three
_context_labels sources with n != name (correlated case admitted both orders 1.0/1.1/1.2; case B
+ cross-name control refused; gates green). Closing tests = shift-carrier + selection-carrier arms
on the population control (class = 3 carrier arms, existing control covers weight only).
Lead's same-family-twice adversarial construction REFUTED — check_family.inherited already
refuses; no redundant guard. D3-2 LOW = one attempts.md sentence. Round trajectory 6→3→1(+1 LOW).
Round 4 = same reviewer verifies the validated-form delta (exit-shaped).

## HIST delta-2 review (2026-09-02): APPROVE — arc review-complete at a474a93
All 5 MED close under probes: reword-stability True×3 with live coordinate-shift control;
coordinate-distinctness via independent field-collapse attribution (hash alone OR params alone
suffices — either-redundancy measured); plan/materialize parity byte-identical at BOTH indices
(reviewer ran the materialize leg the witness lacked); descriptor params blame + real version
0.0.1; A2 two-axis probe blames weight[0]; A4 mixed-plan names merging output only, cross-output
merge (neither-shrinks-alone) falls back to naming both w/ workaround since varied; §7.2 success
path exactly 1 compile (refusal path 3 — diagnostic-only); A9 spy patches 6 bindings incl.
boost's. 7-row mutation table replays (M7 honest-green A8 row). Adversarial identity: collision
WOULD be silent (evaluator not hashed; 4→3 intern with coordinate removed) but 448-pair exhaustive
_blame grid shows no coordinate carries two messages. 1 LOW + 2 observations pending tail.
PR ORDERING: histogram PR waits for graphed round-4 pass — histogram CI installs graphed@main
(git URL), so PRs open together, graphed first.

## HIST delta-2 tail + L1 fold-in dispatched (2026-09-02)
Identity-walk control live (injected n_factors-varying message detected on 4 coordinates).
L1 LOW: import-time version() lookup → unimportable without installed dist (src-only PYTHONPATH
exposure); fold-in = mirror graphed preserve/bundle.py:65-66 guarded pattern; dispatched, no
review per process. Obs1 coverage-arm note informational. Obs2 = pre-existing unvaried-merged
IndexError, re-measured at a474a93, already m49-ledgered. Histogram arc = APPROVE + fold-in
pending; PR gated on graphed round-4.

## HISTOGRAM ARC COMPLETE (2026-09-02): tip 3cef279
L1 fold-in landed (guarded version read, forced-raise probe: import survives, _VERSION="");
frozen byte-untouched since freeze-m48-fixup (verified), 93/93 frozen + 106/106 w/ extras,
gates clean. Arc: H-C0..H-T3 freeze → dispute #2 upheld/re-frozen → H-I1/H-I2 → 3-lens review
REJECT(5 MED) → fix a474a93 → delta-2 APPROVE → L1 fold-in 3cef279. Awaiting graphed round-4
to open both PRs (graphed first; do NOT merge).

## M48 ARC COMPLETE — PRs OPEN, NOT MERGED (2026-09-02)
Graphed round-4: APPROVE, zero findings (diff = validated form verbatim; six-arm probe matrix vs
reviewer's own round-3 measurements; opposite-direction mutations; four_jets dedup verified
neutral; fallback paths driven). PRs: graphed-org/graphed#3 (cd02a5e; branch m48-vary + tags
m48-freeze/m48-freeze2 pushed) and graphed-org/graphed-histogram#2 (3cef279; freeze-m48/
freeze-m48-fixup pushed; body marks dependency — m48 CI legs red until #3 merges).
§12.3 bookkeeping DEFERRED to landing: R23 binds §§1–9 outcomes (whole arc), edits a–d wait for
merge; memory (e) updated now. m49 blocked per root CLAUDE.md (next milestone needs DONE = merge
+ CI green). Final tallies — graphed: 112 frozen / 30 extra witnesses / 12 attempts iterations /
2 disputes upheld / review rounds 6→3→1→0 findings. histogram: 66+27 frozen / 13 extra / L1
fold-in / rounds 5→1LOW→0.

## CI diagnosis + fixes (2026-09-02): both PRs were red for two separate causes
1. GRAPHED (all 16 OS×py matrix jobs): exactly the five m16 std/var anchors — NOT env-local after
   all. Root cause: awkward 2.13.0 (2026-08-14, after main's last green CI; CI + local both
   resolve it) — ak_var._impl:303 indexes its mean scalar (xmean[(0,)*ndim]) → to_layout refuses
   the tracer's unknown scalar; mask_identity=False does NOT help (measured). Same upstream
   pattern _global_extremum already works around for ptp ("indexes its scalar result").
   FIX 0dd1590: _global_moment composes tracing-path axis=None std/var from mean/count kernels
   (dtype rules measured identical, f32→f64 both paths; ak.moment probed fine → class={std,var};
   weighted arm dropped — weight cannot change a scalar reduction's abstract form). Witnesses =
   the five frozen m16 anchors; whole suite now 0 FAILED across 52 subtrees (first fully-green
   run of the arc — the "known-env baseline" label had been masking a real regression).
2. HISTOGRAM (every leg): ImportError Varied from graphed@main at collection — the documented
   cross-repo dependency, package-wide because boost.py imports vary names at import time.
   FIX 1c592e8: ci.yml env.GRAPHED + docs/requirements.txt pinned to @m48-vary with explicit
   revert-to-@main markers for merge (no gate/threshold/matrix change).
PR #3 body updated (gh pr edit broken by Projects-classic GraphQL deprecation → REST PATCH).
Watcher bv3bivria on tips 0dd1590/1c592e8. LESSON recorded: a red set that reproduces on a fresh
env is not "known-env" — check the dependency release timeline before labeling.

## m48 DONE — both PRs MERGED (2026-09-02)
graphed#3 → main d7e579a (merge queue; ci+wheels green at 0dd1590 incl. the awkward-2.13.0
_global_moment fix). histogram#2 → main 45d567a (pin flipped back to @main at 58c0a5e, green
against merged main BEFORE enqueue — the revert-marker discipline held). Meta submodule pointer
committed (graphed-histogram only; other submodule drift pre-existing). Meta state.json tracks
only mvp M0-M9/ORCH — no edit. Clones: graphed on main d7e579a (vary/Varied import-verified);
histogram submodule on main 45d567a. §12.3 a-d still deferred to arc landing (R23 binds §§1-9).
NEXT: m49 section review (lenses incl. as-built-m48 reconciliation; ledger file
scratchpad/vary-m49-ledger.md) → re-plan loop → decompose → gated pipeline. Labels vary-m49-*.

## m49 section review round 1 (wf_2e1afa2a, 28 agents, 2026-09-02): REPLAN
Post-skeptic: 1 BLOCKER + 8 HIGH + 8 MED CONFIRMED; ADJ-10/21 REFUTED; ADJ-14/18/19 RESIZED LOW.
BLOCKER ADJ-1: §8.2(i) accessor scoped to DCE's remap but as-built reduce_with_mode re-indexes
4× (dce → engine.canonicalize → cse → stage_fusion) and the RewriteEngine seam returns no
correspondence (EggEngine discards canon/class_to_new) — record→reduced map needs a designed
channel through the trait ("no egg types leak" bears). HIGHs incl.: universe() KeyError on union
labels (§3.4/§5.3 name the strict accessor; member_of is the §2.4 one); §5.4 binds
NotImplementedError vs frozen GraphedError law; §5.4 fixture source unimportable awkward-free
(reds REQUIRED 3.14t gate); §7.2 unvaried-merge sentence false as-built (opaque IndexError, no
positive control exists); §8.1/8.2 anchors homed in executors repo; §2.5 shift-after-weight
channel inputs unreachable; ledger decision (1) still undecided; rand_gauss partition-seeded
counterexample. MEDs incl. ledger-anchor homes unassigned (8 owed), compile-budget spy site
intercepts nothing (import-time binding), ill-typed `ev + 1` spelling, JER-SF discriminating
construction missing. Full result: scratchpad/vary-m49-section-review-result.json.
→ re-plan r34 dispatched (opus/xhigh planner); loop until 0 B/H/M per owner process.

## r34 committed (8dcdd5c, plan-only, +313/-130); delta round 1 dispatched (2026-09-02)
All 17 CONFIRMED >=MED repaired per planner report (vary-m49-replan-r34-report.md). Key decisions:
ADJ-1 = RewriteEngine::canonicalize returns graph + total node_map Vec<usize>, four-pass remap
composition in reduce_with_mode (~200 LOC target; discriminating anchor: identity-token node on
a live path survives DCE, dies in canonicalize); ADJ-2 = member_of promoted to §9.1 surface;
ADJ-5 = merge-shortfall refusal DE-scoped from varied-only (unvaried merged plan gets GraphedError
instead of IndexError); ADJ-8 = record-time detection at the shift vary call + additive
CompiledGraph field; ADJ-9 = awkward broadcast-blame wrapper IS an m49 target w/ awkward/m49
anchor. Delta review wf_cd56b1a6 running: repair-correctness lens (opus/xhigh; mandatory: ADJ-1
seam vs as-built four passes; ADJ-5 vs FROZEN LAW incl. §6.3 sentence; ADJ-8 additivity vs
golden/determinism) + delta-consistency lens (opus/high; hunk-by-hunk discipline, REFUTED
untouched, ledger walk, sizing) → adjudicator → routed skeptics. Loop until 0 B/H/M.

## m49 delta round 1 (wf_cd56b1a6, 7 agents): REPLAN — 17→3 trajectory (2026-09-02)
DR1-01 HIGH CONFIRMED: ADJ-5 premise false over its class — Histogram.plan()/_SumFills path RUNS
and silently drops a merged fill (99.25 vs 198.51 measured; for-loop under-sums, no positional
index); reviewer also proved class-wide widening reds ZERO frozen tests (whole-tree simulation
w/ controls). DR1-02 HIGH CONFIRMED: r34's JER-SF mandates SF<1 which degenerates to factor≡1
under coffea's own formula (max(SF²−1,0)); fix = both SFs >1, distinct magnitudes (control
validated). DR1-03 MED CONFIRMED: one-field §8.2 collapse never decides the provenance producer
(graphed debug/m49 anchor would self-supply = vacuous; hook-less StageError w/ empty frames =
crash in error handling). DR1-04 RESIZED LOW (facts survive, sizing didn't). +6 LOW/2 NIT incl.
DR1-07 (delta edits at REFUTED ADJ-10's site while planner report claims otherwise). 2 dropped.
r35 dispatched to the same planner w/ per-repair constraints. Result JSON:
scratchpad/vary-m49-delta-r1-result.json.

## m49 delta round 2 (wf_e990a22b, 6 agents): REPLAN — 3 MED, all DR1-03 ripples (2026-09-02)
DR1-01/02/03 core repairs verified CLOSED (both-consumer widening simulated over whole frozen
tree: 1 sim-artifact red only; Histogram.plan-only sim clean w/ live controls; JER 1.2/1.05
re-probed all-six-False). New: DR2-02 MED producer-population not byte-neutral (CompiledGraph
BY VALUE in _WritePart; sha flip + control, +39% closure on 401-node chain; repair = gate on
registered variations); DR2-01 MED "hook-less" classifier falsified by own widening (shortfall
check needs artifact ⇒ every builder hook-ED; classify by field value + empty-union hook returns
None); DR2-03 MED artifact field = second cross-repo shared structure, unpinned home. LOWs:
sort key None-vs-int TypeError (planted trap confirmed), stale "to unvaried programs" scope
line, tie-break anchor homed cross-repo. Trajectory 17→3(2H)→3(M only) — severity ceiling
decaying. r36 dispatched (one coupled repair + 3 fold-ins).

## m49 r36 committed + delta round 3 launched (wf_3234f831, 2026-09-02)
r36 (cac5e6c, +60/-34, plan-file-only) closes DR2-01/02/03 as ONE coupled repair: artifact-field
population GATED on session-registered variations (unvaried closures byte-identical); wrap (ii)
classified by the failing key's ENTRY (hook returns None on no-correspondence; nominal-only key
keeps its entry w/ EMPTY label tuple + real frame, renders ""); artifact field shape/owner pinned
in §8.2(i) (map + per-key frames in closure key order, compile_ir owns + tie-breaks, hook reads).
Fold-ins: sort key spelled, §7 target rescoped, tie-break anchor → debug/m49. No new probes
(premises exhibited). Delta r3 launched: repair-correctness (opus/xhigh) carries the planted
class-boundary trap — the gate is SESSION-granular but the churn sentence quantifies over
PROGRAMS; boundary member = one session w/ a registration + an unrelated unvaried write (candidate
refinement: per-compile reachability per §3.4); also probes m51-clause subject (varied write at
m49: refused or silent?), EMPTY-tuple StageError rendering, DR1-01-composition. Delta-consistency
(opus/high) adds the closing-round sweep (round-artifact grep w/ control). Then adjudicate +
routed skeptics. On 0 B/H/M: whole-artifact pass → fold-in → DECOMPOSE. On ≥MED: r37.

## m49 delta round 3 (wf_3234f831, 6 agents): REPLAN — 1H/2M, all CONFIRMED (2026-09-02)
ADJ3-01 HIGH: DR2-02's gate is mechanically void — a defaulted frozen-dataclass field is in EVERY
pickle (measured on a real _WritePart closure: digest flips w/ field at DEFAULT; control clean),
so "additive CompiledGraph field" + "no field, no bytes" cannot both hold; every by-value write
journal churns once at m49 regardless. Fork left to planner: (a) document the m49 churn in §7.3
+ delete byte-identity claim, or (b) conditionally-set NON-field attribute (+ reword L2123).
ADJ3-02 MED: the planted session-vs-program trap CONFIRMED — unvaried program in a varied session
is inside the gate (session._varied session-scoped, execute.py:91; measured unreached_labels
('jes_down','jes_up') on the unvaried write, falsifying r36's own §2.5-precedent cite); fix
direction = per-COMPILE reachability gate (reached already computed, execute.py:88-90); closure
anchor must be the ADMITTED member, not the L3046 easy end. ADJ3-03 MED: third site of the
DR2-01 decision unrepaired — §8.2 rendering rule L2219-2221 still keys "" on "a key with no
entry" while the producer now emits EMPTY-tuple entries; both halves false under r36. Fold-ins:
ADJ3-04 LOW rationale-beside-decision prose; ADJ3-05 NIT header says r29. Trajectory
17→3(2H)→3(3M)→3(1H/2M): count flat at 3, but rounds keep finding real mechanism defects (the
HIGH invalidates a delta-new mechanism w/ a reproduced probe) — not prose-only, loop stays open.
r37 dispatched; dispatch file scratchpad/vary-m49-delta-r3-dispatch.md; result JSON
scratchpad/vary-m49-delta-r3-result.json.

## m49 r37 committed + delta round 4 launched (wf_c2290cf1, 2026-09-02)
r37 (4fd944b, +34/-34, plan-file-only, subtractive): ADJ3-01 via fork (a) PLUS gate deletion
(byte-identity claim gone; field UNCONDITIONAL; §7.3 states the second one-time m49 by-value
churn beside the m48 one + size growth); ADJ3-02 dissolved (only condition left = hook returns
None when no key carries a label — program-scoped by construction; UNATTRIBUTED arm respelled on
the admitted member); ADJ3-03 rendering rule enumerates singleton/multi-label/EMPTY tuple → ""
+ no-entry-renders-nothing clause. Fold-ins: rationale prose left w/ the gate; r29 markers
deleted. Delta r4 launched w/ the COMPOSITION TRAP as mandatory check: hook None for every
unvaried program × DR1-01 widened refusal reaching the artifact only through the hook × ledger's
owed UNVARIED-MERGED refusal anchors — if the None starves the shortfall check for unvaried
merged fills back to the m48 IndexError/under-sum, ADJ3-02's dissolution reopened DR1-01 (HIGH).
Also: churn statement truth over population, stale gate references after subtraction (grep w/
controls), respelled-arm satisfiability (reached vs unreached populations differ), four-state
rendering enumeration vs the two test-author anchors, deleted-hunk load-bearing text.

## m49 delta round 4 (wf_c2290cf1, 5 agents): REPLAN — 1H/1M + 3 LOW folds (2026-09-02)
COMPOSITION TRAP NOT REOPENED (mandatory check): the m49 target line binds the merged-fill
refusal on every builder and every program independent of the hook's return — DR1-01 stays
closed; the subtractive design held. ADJ4-01 HIGH CONFIRMED (semantic): the respelled
UNATTRIBUTED arm is red-or-inert — its appositive names the ordinary multi-output analysis,
which as-built is ONE compile (histogram plan() collects all fills; producer seeds
{"nominal": None} per output) so the failing key DOES get an entry; read as separate hook-less
compile it merely re-pins frozen m48 variation_labels-is-None and no session-scoped producer can
fail it (own-hook forbidden by L2178-2180). Fix: admitted-member anchor moves to histogram m49
where the producer runs; debug/m49 keeps the wrap-side re-raise. ADJ4-02 MED CONFIRMED
(mechanical): "Document BOTH churns; that is what m51's docs anchor says" is false (m51 bullet
= §6.4f mechanism); m50's "all three invalidation classes … m49 only populates it" now
under-counts. Fix at m50's enumeration + re-aim pointer. LOW folds: unqualified "(i) gives
every key it maps an entry" parenthetical; EMPTY-tuple render state asserted by no anchor;
residue prose ("rather than gated away", stale bolded WRITE-path lead). Adjudicator dropped one
false lens subclaim (m51 bullet exists). ≥MED trajectory 3→3→3→2, narrowing to anchor placement
+ doc routing. r38 dispatched; dispatch scratchpad/vary-m49-delta-r4-dispatch.md; JSON
vary-m49-delta-r4-result.json.

## m49 r38 committed + delta round 5 launched (wf_8d3d0c1d, 2026-09-02)
r38 (9bc80cf, +19/-16, plan-file-only): ADJ4-01 arm SPLIT by witnessing repo — debug/m49 keeps
wrap-side branch only (appositive deleted); admitted member → histogram m49 anchor (unvaried
builder call in varied session ships variation_labels is None; claimed to fail a session-scoped
producer, unmakeable in graphed since hook-less aggregate_plan returns None regardless).
ADJ4-02 fixed at anchor end: m50 keeps three classes, third = BY-VALUE JOURNAL class landing
twice (m48 _PartitionReduce + m49 CompiledGraph); §7.3 pointer re-aimed m51→m50. Folds:
parenthetical deleted; §8.2 anchor list + shared-prefix failure asserting variation == "" w/
user's line; both residues dropped. Delta r5 launched; decisive question = four-leg
DISCRIMINATION check on the relocated anchor: (a) satisfiable (payload None vs artifact
empty-tuple entries — anchor must assert the PAYLOAD), (b) discriminating (session-scoped
producer must FAIL it; session._varied non-empty for the member), (c) legal (no own-hook per
L2178-2180), (d) debug residual arm still witnessable + non-vacuous. Plus m50 enumeration truth,
duty carriage, fold coherence (EMPTY-TUPLE state not no-entry state), re-homing ripples, and
the whole-plan closing sweep. If 0 B/H/M → whole-artifact pass.

## m49 delta round 5 (wf_8d3d0c1d, 4 agents): REPLAN — single HIGH from a fold-in (2026-09-02)
Round-4 repairs ALL verified closed: relocated histogram-m49 anchor passed the four-leg
discrimination check w/ live probes (payload None as-built; session._varied=1 for the member w/
fresh-session control → session-scoped producer ships non-None and FAILS the anchor; hook
presence on unvaried programs independently pinned by the merge-refusal anchor, closing the
gated-hook escape; debug residual arm witnessable + non-vacuous). ADJ4-02 closed both ends
(m50 enumeration names both landings; §7.3 pointer lands on text carrying the duty; zero stale
m51-pointer hits). ADJ5-01 HIGH CONFIRMED: the ADJ4-04 LOW fold (applied w/o review by rule)
anchored EMPTY-tuple rendering on the SHARED PREFIX — but the producer rule gives the shared
prefix the NON-NOMINAL UNION (measured rc5_prefix_cone.py: prefix ids 2,3 in union;
nominal-exclusive [6,8,9] are the empty-tuple keys; controls live) → anchor red against a
correct build + collides w/ the multi-label sibling :2223. Root = pre-existing seed gloss :2158
conflating empty-tuple w/ shared prefix; repair = re-aim member to nominal-exclusive key
(constructible, prov at user's line) + sweep the seed. ADJ5-02 LOW: new anchor lacks §10
per-repo home. LESSON (loop mechanics): a LOW fold-in can mint a HIGH — the fold rule trades
review for speed and round 5's coherence check is what caught it; keep fold coherence checks in
every subsequent delta round. r39 dispatched; dispatch scratchpad/vary-m49-delta-r5-dispatch.md.

## m49 r39 committed + combined round 6 (delta-verify + WHOLE-ARTIFACT) launched (wf_b33c92b5, 2026-09-02)
r39 (0e20c37, +8/-5, 3 hunks) read directly against the dispatch: anchor member re-aimed to
NOMINAL-EXCLUSIVE node ("nominal sibling fill is one" — matches measured member id 9); seed gloss
corrected w/ the whole-cone reason; both rendering anchors homed on executors flat
tests/frozen/m49. Since the repair transcribes a measured instruction, round 6 COMBINES the
small-delta check (opus/high) with the whole-artifact pass (opus/xhigh) a clean delta would have
triggered: full m49 surface read cold — design coherence (four-pass remap × unconditional field ×
reachability producer × always-hook × entry wrap × four-state rendering × churn account),
completeness vs the carried freeze ledger (owed anchors incl. ir-F3..F6, compile-budget spy,
golden strip, varied-mask _align), buildability (partition sizing, anchor homes real + witnessing
repos right per the round-4 lesson), fresh-eyes hunt over §5/§7 pre-loop text. Rationale for
combining: artifact pass needed regardless if delta clean; only cost if delta bad = one early
lens. On 0 B/H/M → final LOW/NIT fold-in → m49 DECOMPOSE.

## m49 round 6 = delta-verify + WHOLE-ARTIFACT (wf_b33c92b5, 4 agents): 1 MED + 4 LOW (2026-09-02)
r39 delta CLEAN both legs (member class ≡ empty-tuple population both directions; seed gloss
correct; no surviving empty-tuple↔shared-prefix chain — whole-file walk w/ controls). ARTIFACT
PASS = closure evidence: design COMPOSES as-built (four optimizer passes match §8.2(i)
DCE/canon/CSE/fusion w/ local remaps already present in mod.rs/engine.rs → node_map derivable, no
new computation; record ids ARE arena ids; evaluate_ir has exactly the two dispatch points;
identity-token discriminator real; four rendering states have four anchors); LEDGER fully homed
(§6.1d wrapper DECIDED as m49 target in graphed.awkward w/ anchor; labels() two-level decided;
re-index/blame-parity/golden-strip/unvaried-merged/budget-spy all anchored). ADJ6-01 MED
CONFIRMED: hook-None gloss "predicate is the PAYLOAD's own emptiness" false vs producer recipe —
unvaried payload = NON-empty all-empty-tuple list (measured 5 entries; varied control separates);
implementer coding the gloss is RED vs frozen :3218 is-None anchor; cross-repair inconsistency
(ADJ3-02's gloss × ADJ3-03's entry rule, never cross-checked). LOW folds: §10 executors bullet
missing empty-tuple row; exemplar not injectable (builder External — swap to user-op member);
§5.2c vs cardinality-clause literals; CompiledGraph field needs §12.4 row. r40 dispatched as
CLOSING revision; then ONE focused verify on the r39→r40 diff (artifact pass stands); 0 ≥MED ⇒
loop CLOSED → m49 DECOMPOSE. Dispatch scratchpad/vary-m49-round6-dispatch.md.

## m49 PLAN LOOP CLOSED at r40 (wf_50a1dd47 closing verify: CLEAN, 0 findings) (2026-09-02)
Single xhigh lens, 4 driven probes, zero findings. ADJ6-02 artifact-as-oracle SURVIVED all three
vacuity attacks: (a) falsifiable — map read from accessor, id set from artifact IR; degenerate
constant map image {1 id} ≠ 10-id store set, DCE-remap-identity image (36 record ids) ≠ {0..9};
(b) set-equality vs independently-read store strictly STRONGER than the deleted 2N+2/N+1 literals
for every accessor error class; the one thing a literal alone carries (reduction-shape regression
moving both sides) is §3.3's frozen variation benchmark's job (:3151, core/m49); (c) §5.2c bar
not crossed (no literal asserted). ADJ6-01 gloss exact vs measurement (payload never empty:
cone-union == reachable record-id set on all three program shapes). ADJ6-04 exemplar buildable +
injectable END-TO-END (driven: SequentialRunner().run(gh.plan) raises worker-side broadcast
ValueError w/ user file in traceback; unpoisoned control green). Exit NITs N1-N4 (stale
co-references from r40's deletions + §12.4 row order) → fold-in r41 dispatched, NO review.
MEASURED DECOMPOSITION TRAP recorded in ledger: empty-tuple poison must be USER arithmetic op
(m6 numpy_mismatch idiom); .map idiom dies — gh.plan has no externals= seam (boost.py:452/528;
aggregate_plan externals=None). Rounds: 17→3→3→3→2→1→1→0 across r34..r40. Verify JSON:
scratchpad/vary-m49-r40-verify-result.json. NEXT: r41 NIT commit (verify plan-file-only, no
round) → m49 DECOMPOSE under the gated pipeline (vary-m49-* labels, isolation protocol baked in).

## r41 landed; m49 DECOMPOSE dispatched (2026-09-02)
r41 (f3b3a15, +10/-12, plan-file-only, net deletion, no design change) — N1-N4 folded exactly as
dispatched. Plan loop FINAL: r41 tip, design closed at r40. Decomposition dispatched to the loop
planner (deepest context): vary-m49-decomposition.md — frozen-tree layout per repo, per-tree
test-author briefs (anchor slices by plan-line citation, poison-idiom + witness-repo traps,
isolation protocol), commit-sized implementation partition (≤1-2k LOC, m48-history estimates,
dependency order), sequencing + gates + freeze-tag names. Underdeterminations go to an
"open items" section, not decided by the planner. On receipt: hallucination check, then
test-authoring launch.

## m49 decomposition delivered + fact-check launched (wf_18391e8e, 2026-09-02)
vary-m49-decomposition.md (~330 lines, uncommitted): 7 trees / 3 repos (graphed frontend|awkward|
core|debug|checkpoint m49; histogram flat m49; executors flat m49 — trees carry their WIDEST
collecting process; frontend+core = the awkward-free pair per the 3.14t job scope); commits
C0 (executors install pair, lands w/ test-authoring) + C1 core→C2 frontend→C3 error→C4 histogram
(all ≤500 LOC, m48-calibrated; C2 second is HARD: C1's frontend anchor needs §3.4's impact verb;
C3 before C4: UNATTRIBUTED arm = pre-C4 behaviour); §12.4(3) producer-cost duty discharged
(linear in N, 1.68×@16→2.64×@128 vs reduce, O(N·D) shared-prefix re-walk, outside §3.3 budget
which times GraphStore.reduce only; population = frontend path); freeze tags verified against
live conventions (graphed m49-freeze vs histogram/executors freeze-m49); executors coverage gate
note (no new source — coverage discharged in source repos). OPEN ITEM (sole genuine one):
labels() flatten on nested Varied — RULING: explicit m50 deferral (ground: plan blesses
two-level §2.1, freezes no m49 anchor either way, no m49 Implementation Target depends on it =
outside m49 frozen scope; separate complete thought on the labels() surface). Surface to owner at
next report for override. Fact-check workflow launched before test-authoring (mandatory plan
check): tree/CI-scope claims, C0 necessity, LOC actuals re-derivation, dependency readings,
§12.4(3) command+population, tag conventions, full ledger walk, brief traps.

## Decomposition fact-check (wf_18391e8e): 3 MED confirmed — incl. a false "open item" (2026-09-02)
DK-1 MED: labels()-nested is NOT open — plan §2.2 (r34, 8dcdd5c) binds strictly-two-level;
decomposer routed a closed decision to the owner. CORRECTION to the previous entry: my m50-
deferral ruling was premised on the decomposer's claim and is VOID — the plan decides it, no
owner call needed, ledger item 2 retires as closed-by-§2.2. DK-2 MED: "same-dir, no pythonpath"
falsified by reproduced probe — prepend import mode silently binds bare helper basenames across
sibling milestone dirs in one process (frontend 3.14t/debug/checkpoint scopes); fix = milestone-
namespaced helper basenames (live m10_toy.py convention) + non-test-.py duplicate check in
TEST_SANITY; §10 regen command is test_*-scoped, can't catch it. DK-3 MED: compile-budget R0.11
obligation missing from C4 brief; plan :1949-1958 binds IMPORT-SITE patching (aggregate + boost
from-import bindings) — definition-site spy measures nothing; LEDGER ITEM WAS WRONG (said
definition site) — plan wins. LOWs: histogram LOC churn-vs-insertions (+370/−63 actual);
four-vs-five witnesses; §12.4(3) missing regen command; checkpoint scope incl. tests/extra.
Everything else verified (tree scopes exact, 22 basenames collision-free live, checkpoint tree
plan-homed :2320/:3037, executors read via origin/main 201ea42 — no fresh clone, submodule stale
3e047dd). Fix dispatched to planner; verification by grep on receipt, no re-check round.

## Decomposition FIXED (7/7 grep-verified) + TEST_AUTHORING launched (wf_003303d7, 2026-09-02)
All 7 decomp fixes verified in place w/ live control: §5 leads "No design decision is open"
(labels() closed by §2.2, correctly attributed); helper-module uniqueness block + m49_ prefixes
bound in frontend/debug/checkpoint briefs + TEST_SANITY non-test-.py dup check (control:
shuffle_backends.py w/ m40 lifted); C4 R0.11 compile-budget paragraph w/ import-site bindings;
histogram LOC +370/−63; witness set named not counted; producer-cost probe installed durably at
vary-m49-producer-cost.py w/ command + re-run reproducing; checkpoint scope row = frozen+extra.
ENV PREP: executors submodule graphed-exec-local fetched+checked out origin/main 201ea42,
editable-installed into shared venv via uv (venv has no pip — uv pip --python). TEST-AUTHOR
FLEET launched: 7 authors (opus/high) — frontend/core/awkward/debug/checkpoint (graphed@d7e579a)
+ histogram(45d567a) + executors(201ea42, carries C0 install pair); each in own detached
worktree ta49-<key>, branch m49-tests-<key>, import-provenance assert, stub-failure signatures +
two-run determinism required, disputes recorded not routed around. Reports →
vary-m49-test-author-<key>-report.md. Next: collect branches → TEST_SANITY → freeze.

## TEST_AUTHORING complete (wf_003303d7, 7/7, 0 disputes) + TEST_SANITY launched (wf_19721497)
Seven trees authored in isolated worktrees, all branches committed: frontend 94620af (40 tests:
24 RED on stub at named missing surface — impact_by_label/read_columns_by_label/member_of/
CompiledGraph.correspondence/§5.4 label-listing message; 16 GREEN w/ per-test mutation witnesses,
4-run determinism, import-ceiling probe w/ control, whole-subtree unperturbed 24f/255p); core
ec2b367 (2-test §3.3 benchmark GUARD tree, green-by-design; author correctly re-scoped my brief
drift — accessor clauses live in frontend per plan §5.2c); awkward 0ec805d (10: 7 RED incl.
shift_after_weight + §6.1d blame; pins CompiledGraph.shift_after_weight spelling); debug d404cb0
(7: 6 RED; pins NO frames spelling — locates by LAYOUT, deliberate cross-tree coordination);
checkpoint bf906b7 (11 invariant tests green-by-construction — §7.3/7.4 freeze EXISTING behavior
against the m49 field); histogram ddcf48e (13 RED all m49-new; variation_labels read off
plan.process; payload asserted STRUCTURALLY); executors a00f6a1 (31: 8 RED at _crossing_failure
seam; poison = USER arithmetic op — ledger trap held; carries C0; corrected ledger corpus path →
tests/_corpus). MERGED per repo into sanity worktrees on branch m49-tests: graphed 2d038b9
(+2304/27f), histogram ddcf48e (+1264/11f), executors a00f6a1 (+442/−2/6f). TEST_SANITY launched:
3 independent verifiers (collect scopes, stub-set match + traceback spot-reads, mutation re-runs
for green-on-stub trees, 2× determinism, coverage wiring, integrity spot-read, helper dup check
w/ control, cross-tree correspondence reconciliation, C0 exact-diff check).

## TEST_SANITY PASS ×3 → m49 FROZEN (2026-09-02)
Sanity (wf_19721497): graphed PASS (all 5 criteria, 37 stub-failure surfaces verified, mutation
witnesses re-run for green trees incl. debug's TA49_MODE=correct whole-tree-satisfiable control;
cross-tree correspondence reconciliation MEASURED compatible — one plain dataclass
correspondence(node_map, frames) satisfies frontend's pin + debug's layout scan; import-ceiling
proxy clean); histogram PASS 0 findings (import provenance verified: worktree src via
pythonpath=["src"], graphed = stub clone; ci stays red until C1-C3 land = decomposition §4
ordering); executors PASS (8 REDs at one correct seam; 3 green-justifications re-verified w/
mutants killing exactly their targets; C0 bit-exact). NITs: slots-constraint → C1 implementer
(correspondence container needs __dict__ or tuple shape); inert type-ignores STRIPPED pre-freeze
(aba82c6; behavior-neutral verified — first recheck FAILED 2 via my own clobbered -o pythonpath
missing checkpoint/m8 entry, correct invocation 57/57 exit 0, failing run = live control);
report miscount ignored. FROZEN: graphed m49-freeze @ aba82c6, histogram freeze-m49 @ ddcf48e,
executors freeze-m49 @ a00f6a1. Impl branches m49-vary checked out in all three clones at the
frozen tips; .graphed/m49/attempts.md initialized. NEXT: IMPLEMENTING — C1 core correspondence
(Rust node_map + four-pass composition + CompiledGraph field; slots constraint; ~350-500 LOC).

## C1 LANDED (0304a1e) + C2 launched (wf_a9ee50be, 2026-09-02)
C1: +253/−47 8 files (206 source LOC, UNDER the 350-500 band — each pass already computed its
remap; only returns + one composition missing). All gates green w/ live controls: zero new
FAILED (comm w/ fixed-leg control), coverage 94% (diff 60/61 — sole gap = compile_ir
optimize=False identity line, unexercised by the whole suite), cargo test 30/30 (2 new incl.
four-pass composition test), clippy/fmt/mypy/ruff clean, §3.3 guard green, checkpoint 57/57,
precommit ok. Frozen UNMODIFIED (empty diff w/ control). Red 37→32 = exact expected subset;
5 targeted greens (4× record_correspondence + debug no-entry re-raise). DESIGN: canonicalize →
(EngineGraph, Vec<usize>) total map (representative = EARLIEST member, no egg type crosses
trait); node_map rides Reduced → from_reduced re-keys through re-interning → store Inner →
PyGraphStore.node_map() ([] for hand-built/deserialized stores) — kept every reduce* tuple arity
unchanged (frozen suite destructures (store, report)); compile_ir publishes unconditional
correspondence (plain frozen dataclass, NOT slots per sanity constraint) w/ node_map dict +
frames in key order, lowest-record-id tie-break. REVIEWER FLAG: the from_reduced re-keying
choice. ENV TRAPS measured: venv-no-pip maturin workaround (cargo build + cp dylib w/
dynamic_lookup link args), PYO3_PYTHON+DYLD_FALLBACK for cargo test, rustup component adds,
no-subtree-combining (test_deployment.py collision). C2 launched w/ C1 handoff (Correspondence/
Key/Frame reuse, field-after-correspondence default rule, red-anchor-reads-through-C2 note).

## C2 LANDED (8e562e7) + C3 launched (wf_aae5fe4c, 2026-09-02)
C2: +192/−1 6 files (162 source LOC; no Rust). Zero regressions (comm w/ 19-fixed control),
red 32→13 = exact C3 set; all 19 targeted green incl. C1's held-over collapse anchor (verb-not-
map diagnosis confirmed). Diff coverage: by_label.py 100%, others' misses all pre-existing;
covering hits from FROZEN suite. DESIGN: by_label.py = both verbs + _per_label (one §3.4 operand
contract) + cone(); operand alias spelled concretely (Any would evade the §2.3d verb-discovery
gate — measured); both verbs registered *expanding* per §2.3d m49 clause; §2.5 shift-after-weight
via Session._weight_factors filled in _vary_weight + cone-vs-collection pairing (disjoint-cone
premise MEASURED: Jet nid 1 vs MET nid 6), reported sorted in new CompiledGraph.shift_after_weight
(after correspondence, default). C3 HANDOFF (measured): §5.4 refusal = THREE spellings
(varied.py:298 method surface; varied.py:340 refuse_boundary → 5 shuffle.py callers;
awkward/functions.py:905 gak) — widen the CLASS; refuse_container = 4th site, DIFFERENT
m48-anchored contract, don't widen blind; Session._shift_after_weight is session-lifetime (not
per-compile) — single place to change later; C4 should import by_label.cone; precommit needs
PATH+RUSTUP_TOOLCHAIN both (each missing fakes a lint fail). C3 launched: StageError.variation +
wrap arms + widened messages; expect graphed suite FULLY green after (13→0), histogram C4 only.

## C3 LANDED (b412023) — graphed frozen suite FULLY GREEN; C4 launched (wf_df3810bd, 2026-09-02)
C3: +268/−25 (143 src — under band; three of four targets were message widenings). Full suite
rc=0, 0 FAILED across 55 processes, coverage 94%, zero regressions (comm w/ 13-fixed control).
All 13 targeted green: §5.4 labels-naming refusals (class widened via shared boundary_refusal in
varied.py, gak arm rerouted; refuse_container verified different contract via m48 anchor grep and
left alone), §6.1d broadcast blame (one site — both op_form and eval_stage bottom out in
_ops.apply, measured; record-time leg = GraphedTypeError), StageError.variation (hash/eq, ""
default, summary clause, spawn-witnessed picklability), wrap at BOTH evaluate_ir dispatch points
(frozen fixture lands at key (1,0) INSIDE a fused stage — top-level point witnessed by new
tests/extra test), lowest-record-id tie-break. Non-vacuity: 3 restored mutants each kill their
guards. REVIEWER NOTES: attributed StageError hardcodes opt_level=1 (aggregate_plan always
optimizes — revisit if a plan path ever compiles optimize=False); worker input_forms = runtime
type names. C4 launched (histogram producer + R0.11 import-site measurement + cross-repo
executors m49 confirmation — its 8 reds sit at the seam C3 wired).

## C4 LANDED (8443775) — ALL THREE REPOS GREEN; implementation phase COMPLETE (2026-09-02)
C4: histogram boost.py +88/−33. Frozen: histogram 154/154 (m23+m48 unperturbed via comm w/
planted-row control), graphed 0 failed, executors 31/31 — WITH revert-control (boost.py at
ddcf48e → exactly the 8 crossing reds return → restored) proving causation. Coverage 96%,
precommit FULL ok. R0.11: 1 compile per gh.plan (import-site spies 'aggregate'; DEFINITION-site
control spy 0 hits = vacuous exactly as plan §7.2 predicted); refusal path 2 compiles
['aggregate','boost'] (decomposition caveat). DESIGN: entries driven off correspondence.frames
(sortedness/uniqueness fall out of C1's artifact; NO sorted() over mixed keys — the §8.2(i)
TypeError trap); §2.4 fallback per_label.get(label, per_label["nominal"]) — plan-faithfulness
choice, NO frozen discriminator (stated openly); Histogram.plan() hook = refusal-only (payload
always None; m50 lift pre-wired). Commits: C1 0304a1e / C2 8e562e7 / C3 b412023 (graphed),
C4 8443775 (histogram), C0 in a00f6a1 (executors). LOC 206+162+143+88 src = 599 total, every
commit under band. NEXT: three-lens impl REVIEW (design/integrity/mutation) w/ MANDATORY
isolation protocol; accumulated reviewer flags: from_reduced re-keying, opt_level=1 hardcode,
session-lifetime _shift_after_weight, frames-driven entries, §2.4-fallback no-discriminator.

## Impl review (wf_fa3d406b): FIX_CYCLE — A-1 HIGH + 4 MED; fix cycle 1 launched (wf_abc97633)
Design REJECT (1H/2M/1L/2N) + Mutation REJECT (1H/2M/2L/2N) + Integrity APPROVE (1L/2N);
adjudicated 14 findings, 0 dropped, every spot-check reproduced. A-1 HIGH: evaluate_ir external
arm outside _dispatch — External failures unattributed despite carrying entries (probe: image+
frame keys include (2,None), hook saw []; fused-stage control live); the canonical §4.1 weight
node class; frozen suites structurally blind (executors poison docstring says why). A-2 MED
(downgraded from H: pre-existing + outside §7.2 literal wording): two fills interning to ONE
record node → marked==outputs==1, no refusal, silent 0.5 under-sum on UNMUTATED tree. A-3 MED:
shift_after_weight session-scoped (cross-lineage false positive measured; repair premise
ctx._weight._tags live at call site; sole frozen consumer same-lineage → filter keeps it green).
A-4 MED: both verbs evade §2.3d discovery (future-annotations stringification; alias hides the
Array mention; comment asserts the opposite) — closing witness ALREADY FROZEN once annotations
inline. A-5 MED: frozen incremental anchor can't fail in its named direction (map=identity on
fixture; only Rust unit test kills) — NOT closable in cycle (frozen read-only) → m50 LEDGER.
LOW/NIT: A-6/A-7/A-8 suite gaps (ledger + extras), A-9 dead guard, A-10 unexported cone import,
A-11 nominal double-walk, A-12 CompiledGraph unhashable, A-13 unwitnessed re-key leg, A-14
workflows-valid skip (ROOT-CAUSED: pyyaml absent — installed, leg now live). Ledger updated
(5 m50 anchor items). Fix cycle 1 launched: A-1/2/3/4 + A-8..A-13, one commit per repo, extras
as witnesses, full gates + cross-repo check.

## Fix cycle 1 (wf_abc97633): A-2/3/4 + LOWs CLOSED; A-1 → TEST DISPUTE → ADJUDICATED (2026-09-02)
Commits: graphed 6554122, histogram 2053709. A-2: plan_ passes _SumFills per-staged-fill OUTPUT
INDICES (sums by index → interned fills replicate; optimizer-merge refusal unchanged); witness
red-before ([0,4,12,8,17.6] vs 2×) green-after. A-3: repair at the SHIPPING site (adjudicator's
correction) — _shift_after_weight now maps (family,collection)→offending member node ids;
compile_ir ships a pair only when ids intersect THIS artifact's node_map; cross-lineage + same-
session witnesses red→green, frozen violating anchor green. A-4: annotations inlined AT the
parameters; before/after discovery measured (False,False→True,True w/ read_columns control +
cone negative control); false comment replaced. A-8 opt_level=0 identity witness; A-9 dead guard
deleted; A-10 cone import INLINED via session.walk (choice: no new cross-repo surface); A-11
nominal reuses central; A-12 __hash__ = None explicit; A-13 re-key leg = same map all rides,
comment corrected; A-14 workflows-valid LIVE both repos. A-1 NOT SHIPPED per §A.7: the repair
reds FOUR frozen blame-parity anchors (weight_guard GraphedError must survive plan path VERBATIM
inside pytest.raises(GraphedError); StageError is a bare Exception) — dispute filed w/
measurement, arm reverted, witness quoted in dispute file. ADJUDICATION (mine, measured):
_attribute wraps every exception type; NO frozen anchor requires wrapping a GraphedError; the
class rule satisfying both plan clauses = GraphedError passes verbatim on EVERY arm (already-
attributed), wrap attributes RAW failures. Plan r42 (df68e3e) records the §8.2(ii) carve-out.
Fix cycle 1b launched (wf_c31f5913): carve-out guard + external arm dispatched + witnesses
(raw-with-entry → StageError; no-entry → untouched; GraphedError-with-entry → verbatim).

## Fix cycle 1b LANDED (4364beb + docs 17ea684); delta re-review launched (wf_4b6c292d)
1b: carve-out guard AT THE HOOK (contract intact — other on_failure suppliers decide for
themselves; that independence is what makes witness (d) discriminate guard from arm); external
arm through reshaped _dispatch (run-thunk + functools.partial — B023 avoidance); blame-parity
5/5 green WITH the arm dispatched (adjudication confirmed by measurement); 4-test witness file,
3 of 4 run red against two different partial states; all gates green incl. workflows-valid LIVE;
frozen untouched both repos w/ live controls. Dispute CLOSED in file w/ resolution. Source arm
deliberately NOT dispatched (only failure class = GraphedError → no-op under carve-out) —
accepted. Delta re-review launched (opus/xhigh + skeptics-on-≥MED): per-class closure incl.
adversarial member hunts (user-op GraphedError at entried key; three-fill interned+distinct;
merged-beside-interned; two-artifact one-session; same-family-two-collections), _dispatch
signature fresh-eyes, gates spot-re-run. APPROVE ⇒ DONE checklist → PRs.

## Re-review APPROVE → m49 DONE-pending-CI; PRs OPEN (2026-09-02)
Re-review (wf_4b6c292d): APPROVE, 1 LOW + 2 NIT. All four A-classes closed against hunted
members (user-op GraphedError verbatim w/ raw control; 4 interned-fill members exact; two-
artifact-one-session + two-collections-one-family; discovery instrument w/ negative control);
_dispatch fresh-eyes clean (eager binding verified both ends of the member loop; 110ns/dispatch);
OnFailure contract intact (custom hook still sees GraphedError — carve-out is aggregate's
choice). RR-1 attempts corrections committed (graphed abe7778 incl. RR-3 source-arm ruling as an
execute.py comment; histogram c243c1f); RR-2 inseparability bound + RR-3 ruling → ledger.
PUSHED: graphed m49-vary+m49-freeze, histogram m49-vary+freeze-m49, executors m49-vary+freeze-m49.
TEMP CI PINS (revert-before-merge markers): histogram GRAPHED@m49-vary (d615c94); executors
GRAPHED+HISTOGRAM@m49-vary (c5a3e43). PRs OPEN (not merging without owner call, per arc
instruction): graphed#4, graphed-histogram#3, graphed-executors#6. CI watcher brdttli15 polling
by headSha (self-expiring 2h). Remaining before DONE tick: CI green on the A.5 matrix + wheels
(rides the PRs); §12.3 bookkeeping stays deferred to ARC landing (R23 binds §§1-9). OPEN for
owner: labels()-flatten needs NO call (closed by §2.2); merge call on the three PRs.

## m49 CI GREEN ×3 — milestone complete pending owner merge call (2026-09-02)
Watcher b9h4xjt2l (rewritten after tick-1 false-positive: the first watcher's assoc-array
declare failed silently and its done-check was absence-shaped with no live control — my own
null-result rule, violated then honored; v2 verified the instrument inline pre-launch): 40 ticks,
ALL COMPLETE — graphed ci+wheels success (abe7778), histogram ci+wheels success (d615c94),
executors ci+wheels success (c5a3e43). §E.0 status: frozen suites green + unmodified since
freeze tags; coverage ≥90 frozen-sourced; determinism + §3.3 benchmark green; ruff/clippy/mypy
clean; CI green + wheels built; attempts.md current; reviewer APPROVE recorded. Sphinx -W rides
each repo's ci workflow (green). AWAITING OWNER: merge call on graphed#4 → histogram#3 →
executors#6 (in that order; revert temp pins in the latter two pre-merge). Memory updated.

## m49 MERGING — graphed#4 + histogram#3 merged; executors#6 queued (2026-09-02)
Owner gave merge call. Pin-safe order: graphed#4 → main 01d908b (merge queue, GraphQL enqueue).
Reverted histogram GRAPHED pin → @main (8797365), histogram#3 → main 4d166d2 (transient
"workflow scope" enqueue refusal on the first try — the just-pushed commit hadn't propagated;
succeeded ~10s later; token has repo scope, not the issue). Reverted executors both pins → @main
(a925853), executors#6 enqueued (watcher br7l7837d). After #6 merges: meta submodule pointers +
clone syncs to merged main, then m50 kickoff (StrCategory variation-axis fills + preservation;
m50 ledger carries the 5 m49-review frozen-suite gaps + weight_guard preserve plugin + _slots).

## m49 MERGED ×3 → DONE; m50 kickoff (2026-09-02)
executors#6 → main 7ee4dac. All three merged: graphed 01d908b, histogram 4d166d2, executors
7ee4dac. Clones synced to merged main (main reset to origin/main; m49-vary branches retained);
editable venv now resolves merged m49 code. Pin reverts verified on merged main (0 m49-vary
residue, @main controls present). META SUBMODULE POINTERS: graphed-histogram + graphed-exec-local
show '+' (ahead of recorded pins) — DEFERRED to arc landing w/ §12.3, NOT bumped now. Ground:
partial bump is incoherent (meta 'graphed' submodule still points at pre-consolidation
graphed-mvp; readme-sync CI regenerates README from state.json+all pins via bookkeep.py, and
state.json tracks only mvp M0-M9), and full meta reconciliation is a separate complete thought
due at landing. m49 is the middle milestone; §12.3/R23/root-prompt all bind §§1-9 (whole arc) =
after m51. NEXT: m50 = StrCategory variation-axis fill weight-labels-only + preservation
(weight_guard preserve plugin; _slots fill-node-spec witness; the 5 m49-review frozen-suite
gaps). Same loop shape as m49: dedicated m50 SECTION REVIEW → re-plan until 0 B/H/M → decompose
→ gated pipeline.

## m50 SECTION REVIEW launched (wf_b4fed5c1, 2026-09-02)
m50 = StrCategory variation-AXIS fill (§6.2, weight-labels-only) + preservation bundle/one-bundle-
N-labels (§9.2) + plan-level {output:[labels]} inspect() listing + graphed.variations(ctx) (§9.1)
+ docs. Plan spans: §6.2 ~1490+ / axis-mode slot 1303-1339,1490-1570; §9.1/9.2 2239-2315; §10/m50
3246-3359. 5 probe lenses (axis xhigh, preserve xhigh, introspect high, asbuilt xhigh, coherence
high) → adjudicate → routed skeptics. KEY NEW ANGLE vs m49 section review: m48+m49 now MERGED, so
every m50 anchor leaning on graphed.labels/variations/correspondence/variation_labels/_slots/
weight_guard/sibling-fill lowering is probed against REAL merged code (01d908b/4d166d2/7ee4dac) —
a plan anchor naming a non-existent surface = BLOCKER. AS-BUILT lens also walks the carried m50
ledger (8 items: 5 frozen-suite gaps + RR-2 + weight_guard preserve plugin + _slots witness) for
homes in the m50 section. Loop until 0 B/H/M → decompose → gated pipeline.

## m50 SECTION REVIEW (wf_b4fed5c1, 11 agents): REPLAN — 4 MED confirmed (2026-09-02)
5 lenses over the m50 surface vs merged m48+m49. Adjudicated 5 ≥MED, then skeptics REFUTED PR-1
→ LOW. Net 4 MED to repair (r43 dispatched to vary-m49-replan-r34):
AX-1 CONFIRMED: §6.2 axis-mode loop node doesn't bind the §6.1d weight-guard/broadcast seam per
weight column — as-built FillEvaluator (boost.py:76-87) flattens value+weight independently →
per-object value × per-event weight length-mismatches at h.fill; per-event fixture passes while
per-object (the ewkcoffea oracle IS jagged) breaks. Repair: bind the seam per column + jagged
anchor fixture.
CO-1 CONFIRMED (mechanical): §6.1c "today" layout baseline (~1313) + scaling parenthetical
(~3324) are STALE — two-level SlotKey + indexed Layout SHIPPED at m48 (boost.py:33/231/456 on
4d166d2); false as-built claim keeps loop open.
IN-1 CONFIRMED: plan-level {output:[labels]} listing silent on axis-mode outputs (one (output,None)
slot, no label on the key — labels on the slot's variation axis); anchor exercises only sibling.
AB-2 CONFIRMED: 4 m49-review carryovers UNHOMED in m50 §10 (A-1 ext-attr, A-5 incremental
discriminator, A-7 unflatten-hint, A-8 opt_level=0, +RR-2); only A-6 render-sorted homed. Home
or defer each.
PR-1 REFUTED→LOW: §9.2 bundle IS pinned (TRIPLE value/weight/spec form, zero Externals, np.array
compare, cites m9 test_reproduce) — the ledger's weight_guard-plugin m50 item is MOOT (assumed
the fill-graph form the plan doesn't use). LEDGER CORRECTED. Folds: AX-2 header reword, CO-2
opt-in surface. Loop until 0 B/H/M → m50 decompose.

## m50 r43 committed (50f454e) + delta review launched (wf_8ea825f7, 2026-09-02)
r43 +96/-27 plan-file-only. AX-1: §6.2 per-column seam clause ("axis mode of same rule") + m50
equality anchor now jagged value + per-event factor. CO-1: DELETED both stale loci, §6.1c
regenerated from merged boost.py (two-level SlotKey/indexed Layout/dedup rank SHIPPED at m48) +
caught §6.1c per-slot-spec pending-work implication. IN-1: {output:[labels]} uniform over both
modes, axis labels from the fill's declared variation SET not the spec string, 3-output anchor.
AB-2: 4 homed in NEW frozen trees (debug/m50 ext-attr, frontend/m50 incremental+opt_level=0
AWKWARD-FREE, awkward/m50 unflatten); §10 preamble updated; RR-2 = §2.5 note. TWO m49-SCOPE
edits flagged: §6.1c per-slot-spec removed; §8.2(iii) "two dispatch points"→THREE (op/inline/
external) + source arm — claimed stale bc evaluate_ir has 3 _dispatch at 01d908b. Folds: header
reword, opt-in per-fill, §9.2 triple explicit. §11: histogram-terminal bundle Phase-2 +
weight_guard condition. Delta review launched (repair-correctness xhigh + delta-consistency high
→ adjudicate → skeptics): highest-risk probes = AX-1 seam LAYER (upstream-per-column vs
in-loop-node) + §8.2(iii) 3-dispatch as-built truth + frontend/m50 awkward-free. Loop to 0 B/H/M.

## m50 delta review (wf_8ea825f7): CLEAN — plan loop CLOSED at r43 (2026-09-02)
Repair-correctness lens 0 findings; all 4 MEDs closed against merged code. AX-1 seam bound at the
RIGHT layer (upstream per column, boost.py:370-374 record _guard+broadcast_like BEFORE
FillEvaluator's independent flatten — sibling mechanism scaled to |W| cols, NOT inside the loop
node = the section-review failure hypothesis, refuted). §8.2(iii) m49-scope correction VERIFIED
TRUE: evaluate_ir@01d908b has exactly 3 _dispatch (op :226, inline :232, external :244) + source
arm :214 excluded w/ matching RR-3 comment. CO-1 regenerated §6.1c all as-built-true (SlotKey :33,
Layout :231, dedup rank :456/532, _slots reads _fill_specs[0] :489). IN-1 uniform listing sourced
from builder's declared label set (non-vacuous 3-output anchor: key-reading impl answers [None]).
AB-2 4 homed; frontend/m50 genuinely awkward-free (A-5/A-8 import only core/numpy/ListBackend; the
3.14t job ignores ONLY m40); §11 weight_guard Phase-2 condition true as-built. 2 NITs: DC-1
DROPPED (intro next-step hunk substantively correct), DC-2 KEPT (new m50 trees omit the
basename-uniqueness reminder — pure prose, global preamble governs; CARRIED INTO DECOMPOSITION
briefs per the m49 DK-2 helper-collision lesson, not folded as plan prose). NO whole-artifact
round: the section review WAS that pass (5 lenses, whole m50 surface, as-built-probed); a re-run
catches nothing nameable = verification-of-verification. m50 plan loop CLOSED at r43 (50f454e).
NEXT: m50 DECOMPOSE → gated pipeline.

## m50 r44 (plan fix) + decomposition written + fact-check launched (wf_c3123565, 2026-09-02)
r44 (37abec1, +5/-3): planner caught its OWN r43 defect while decomposing — r43's AB-2 parenthetical
"no graphed source outside preserve/docs" is FALSE (contradicted §9.1 graphed.variations target 2
lines below; §6.2 i-bis needs accessors.py edit — VERIFIED: accessors.py:47-48 hasattr(x,'axes')→
('nominal',) hard-codes histograms unvaried). r44 names 3 graphed source targets (preserve/,
graphed.variations, accessors.py axis-mode arm), keeps carryover trees test-only. The delta review
missed it because AB-2 lens verified carryover-trees-test-only (true) not the over-broad
parenthetical — decomposition scoping is a real verification surface, planner honestly flagged its
own defect. vary-m50-decomposition.md (~250 lines): 5 trees (histogram m50 source+tests, graphed
preserve/m50 source+tests, debug/frontend/awkward m50 test-only carryovers); commits H1 axis-mode
lowering→H2 axis slot+listing→G1 graphed introspection+preservation→D1 docs; planner CORRECTED my
"+88" to squash 114/37. Fact-check launched (asbuilt xhigh + mechanics high → adjudicate →
skeptics): mandatory = r44 source-target COMPLETENESS (a 4th omitted target?), carryover trees
truly test-only over 01d908b, awkward-free frontend/m50, basename/sizing re-derivation, §9.2
manifest-bump check. On ≥MED → fix; else test-authoring.

## m50 decomposition fact-check (wf_c3123565): FIX — MC-1 HIGH inversion; fix dispatched (2026-09-02)
Verdict FIX. After skeptics: MC-1 HIGH (CONFIRMED), MC-3 RESIZED to LOW, AB-1/MC-2 LOW. r44's 3
graphed source-targets verified CORRECT+COMPLETE (no omitted 4th); graphed.variations absent; all
4 carryover trees test-only over 01d908b source; §9.2 manifest bump scoped in G1; freeze-tag
convention matches. **MC-1 (load-bearing):** decomposition §3/§4/§5.3 INVERT G1's cross-repo dep —
claim G1's accessors §6.2(i-bis) anchor needs "a real axis-mode histogram only H1+H2 can produce"
via cross-package import. FALSE and would ship a SKIPPED zero-coverage anchor. Verified live:
graphed deps boost-histogram>=1.4 directly (pyproject:46); graphed CI does NOT install
graphed_histogram (only mypy override :91); EVERY existing cross-package preserve import is
pytest.importorskip("graphed_histogram") (m25:31/m27:185,207/m30:155 → skip under graphed CI, cover
nothing) → contradicts §4:267 "coverage from graphed's own frozen suite" + ≥90% diff gate; axis-mode
hist hand-constructable from bh alone (StrCategory(name=)=TypeError, h.axes[1].__dict__['name']=
'variation' write OK) — exactly Brief A's own idiom (115-118). Real coupling runs REVERSE:
graphed-histogram Brief A calls graphed.labels over axis-mode → needs G1 → histogram pins
graphed@G1-branch (§4:273 already right; cause was backwards). G1 independent, lands first. LOWs:
MC-3 (graphed-histogram flat tree carries unprefixed behavior_toy.py/vary_hist_fixtures.py in one
--cov process → add to m50_ prefix + TEST_SANITY), AB-1 (§1:42 "Four/one" → "Five/two source"),
MC-2 (§1:50 frontend 51→43 minus-m40). RR-2: NO m50 action — homed at m49 (plan line 856 + §10
anchors 3020/3056/3139); decomp correctly omits it. Dispatch (vary-m50-decomp-fix-dispatch.md) sent
to planner vary-m49-replan-r34; fix in place, grep-verify, no re-review round. NEXT: verify fix →
TEST_AUTHORING.

## m50 decomposition FIXED (grep-verified) + TEST_AUTHORING launched (wf_2879ea3d, 2026-09-02)
Planner landed all 4 edits in vary-m50-decomposition.md (uncommitted). Grep-verified: 4 inverted-claim
patterns return EMPTY (control 'variation'=31 → grep live); positive presence confirmed — §3:235
"G1 INDEPENDENT may land first" + :242 hand-construct + :244 __dict__ idiom; §4:278 "graphed-histogram
→ graphed one direction" + :285 "pins nothing back"; §5:305 "scheduling call, not a dependency"; §1:42
"Five trees/two source"; :51 "43 (51 minus m40)"; :54 "EVERY tree here, graphed-histogram's". Planner
self-flagged MC-1 as its own defect (reasoned from repo names vs the fixture Brief A already specified)
— good-faith. Decomposition frozen-ready. TEST_AUTHORING wf launched: 5 parallel authors (A histogram
m50 xhigh = milestone centre / 6 discriminating anchors; B preserve, C debug, D frontend-awkward-free,
E awkward = high). Env measured: shared venv .venv (py3.13, editable graphed+graphed_histogram, bh1.8.0
ak2.13.0 np2.5.2); graphed trees run from repo root (pythonpath auto), histogram from its own root
(flat one-process CI → m50_ prefix load-bearing). Non-vacuity: A/B fail-absent-feature (G1/H1/H2
unbuilt), C/D/E kill-mutant over shipped 01d908b (f.bak-backed disjoint-file edits, no git stash).
Authors pick+report freeze spellings (axis-mode opt-in, {output:[labels]} name, variations module home,
§9.2 manifest key). NEXT: collect reports → TEST_SANITY ×N → freeze tags (freeze-m50 / m50-freeze).

## m50 TEST_AUTHORING done (5/5, 0 disputes) → TEST_SANITY PASS → FROZEN (2026-09-02)
wf_2879ea3d: 5 authors, 0 errors, 0 disputes. Trees: histogram m50 (7 files/24 anchors, A),
preserve/m50 (2/8, B), debug/m50 (1/2, C), frontend/m50 (2/4, D), awkward/m50 (1/2, E). Non-vacuity
per author: A 23 fail-absent (right reasons: TypeError variation_axis / AttributeError variations|
label_listing / AssertionError labels==nominal) + 1 kills-mutant; B 7 fail-absent + 1 backward-compat
control; C/D/E carryover green-today + kills-mutant. Freeze spellings picked+coherent: axis-mode opt-in
Histogram.fill(...,variation_axis=False) remembered per-hist; graphed_histogram.label_listing verb;
graphed.variations exported from accessors.py; manifest['analysis']['variations']; format_version 2
varied/1 unvaried; recognition axis.__dict__.get('name')=='variation' (A & B independently agree).
TEST_SANITY (inline, mechanical): all trees collect clean in their FULL collecting process (histogram
flat 178-test exit 0; graphed preserve/debug whole-subtree exit 0; frontend-ft all-minus-m40 exit 0
WITH and WITHOUT m50 → no collision; earlier exit=4 was a transient fluke, non-reproducing). Determinism
×2 identical failsets (hist 23/23, preserve 7/7, debug/frontend/awkward 0/0 green). Basenames: no dup
tests anywhere; only dup-helper conftest.py in preserve (pytest-native per-dir, pre-existing, benign);
m50_axis_fixtures.py unique+prefixed. awkward-free frontend/m50 confirmed (no awkward/pyarrow/hist/
pandas in sys.modules). DEEP spot-check (frozen carryover discrimination vs REAL source, not monkeypatch):
applied hint-drop mutant to _ops.py::_broadcast_blame → E test RED (exactly the hint-half test; the
conditionality-guard stays green), restored clean, post-restore green. FROZEN: graphed-histogram 950aa04
tag freeze-m50 br m50-vary (631 LOC); graphed ee354b0 tag m50-freeze br m50-vary (481 LOC). NEXT:
IMPLEMENTING G1(graphed, independent, first)→H1+H2(histogram, narrowing anchors need G1 via shared
editable venv)→D1(docs). Sequential — implementers share the editable-graphed venv (mid-edit race risk).

## m50 IMPLEMENTING: G1 + H1 + H2 landed & verified (2026-09-02)
Sequential (shared editable venv). G1 (graphed 8c62dbe, +97/-15 src: accessors axis-mode arm +
graphed.variations + varied preserve): frozen preserve/m50 8/8, carryovers 9/9, combined COV 94%
(accessors 97% / bundle 96%), ruff+mypy-strict+precommit clean, determinism byte-identical,
format_version 2 varied/1 unvaried. G1 judgment call flagged for review: removed a dead
tests/extra/preserve/m50 witness (run-tests.sh preserve suite is frozen-only → never collected),
leaving 2 defensive-guard lines (variations non-context guard + ambient-None) uncovered — diff cov
still >90% (2 of ~97 new lines). Then H1 (graphed-histogram b6516d4, variation-axis fill lowering)
+ H2 (2fa36c3, axis slot + label_listing): +344/-19 boost.py+__init__. m50 frozen suite ALL 24 green
(incl. the 4 G1-dependent narrowing anchors → G1 live in shared venv confirmed); whole flat
tests/frozen green (real CI gate). Both repos: tests/frozen UNMODIFIED since freeze; no spurious
files; not pushed. STALL LESSON: G1 backgrounded its combined-gate + idled without a live monitor
(caught by the user); fixed by re-dispatching "run gates in FOREGROUND". H monitor's process-based
stall heuristic false-positived during H's read/implement phase (no pytest process ≠ stall) —
ListAgents running/idle is the reliable signal; switched to commit-driven monitors + ListAgents
liveness check. NEXT: D1 docs (both repos, executed examples, Sphinx -W) → three-lens impl review.

## m50 H-report: REVIEW-CRITICAL deviation flagged (sibling hashing changed) (2026-09-02)
H final: H1 b6516d4 (+227/-16 boost.py), H2 2fa36c3 (+57/-9). tests/frozen/m50 24/24; whole flat
178/178; boost.py 97% cov; ruff/mypy/precommit(incl sphinx -W) clean; determinism byte-identical
(slot keys, axis bytes, label_listing, 5 mixed chashes). CI PIN for PR: graphed-histogram pins
graphed@m50-vary (4 narrowing anchors need G1). **DEVIATION for REVIEW (design+integrity+mutation
lenses MUST probe):** H2 brief said "sibling-mode hashing UNCHANGED"; H changed it. Cause: evaluate_ir
resolves External evaluators by content_hash ALONE (execute.py:244); content_hash(spec) is identical
for a weighted output (sib, Jet.pt, Regular(20,0,200)+Weight) and an unweighted output (plain, MET.pt,
same spec) → merged registry resolves BOTH distinct nodes to the last-registered evaluator → sib
nominal silently evaluates UNWEIGHTED (232.16→1037.0). test_mixed_mode_plan (four-output: weighted +
unweighted same-spec) is the first program to combine them. H claims PRE-EXISTING latent m48/m49
(reproduced sibling-only, zero axis code) and UNAVOIDABLE with content_hash(spec) alone. Fix: _fill_chash
folds only WITHIN-spec-differing fields (unweighted flag, weight-factor count, §6.2 variation);
CANONICAL single-weight fill still == content_hash(spec) verbatim → m48 golden (test_variation_goldens)
byte-stable (CONFIRMED: flat 178/178 green). has_sample/n_axes excluded (spec-borne). First attempt
folding everything broke the golden; baseline-delta restores it. Review must verify: (a) the collision
is genuinely pre-existing/constructible on m48/m49 WITHOUT m50 (H's load-bearing justification for a
brief deviation), (b) _fill_chash is sound+complete (no NEW collision, deterministic, the within-spec
field set is exhaustive), (c) legitimacy (implements correct behavior, does not weaken any frozen test).
Also carry G1's flag: removed dead tests/extra/preserve/m50 → 2 defensive-guard lines uncovered
(diff cov still >90%). NEXT: D1 docs landing → three-lens review with these two flags as focus items.

## m50 D1 done → implementation COMPLETE → three-lens review launched (wf_163e6aac, 2026-09-02)
D1: graphed 5165f25 (docs/frontend/design.rst +126) + histogram 00952a6 (docs/design.rst +100);
frozen untouched both repos; no spurious files. Full m50 series: graphed [G1 8c62dbe, D1 5165f25];
histogram [H1 b6516d4, H2 2fa36c3, D1 00952a6]. Review wf: design+integrity read-only PARALLEL
(barrier) then mutation lens on MAIN trees (shared editable venv → mutation must own main; cp .mutbak
bracket + import-provenance assert + git-diff-quiet restore check, one repo/file at a time, foreground
gates). Primary probes: F1 (H's _fill_chash sibling-hashing deviation — design soundness, integrity
legitimacy, mutation verifies pre-existing/unavoidable claim ADVERSARIALLY + within-spec field set
exhaustive) and F2 (G1 dead-tests/extra → 2 uncovered defensive guards). All lenses opus xhigh,
structured findings (symbol-anchored, measured evidence, no file:line pins). NEXT: collect findings →
adjudicate (dedup/severity/verify_route) → route skeptics on verify_route-tagged → fix cycles → delta
re-review → PRs (histogram pins graphed@m50-vary; both merge-queue via GraphQL enqueue).

## m50 three-lens review (wf_f60fa97f): FIX_CYCLE — 1 BLOCKER + 2 MED (2026-09-02)
Design FIX_CYCLE (2 MED), Integrity FIX_CYCLE (1 BLOCKER), Mutation APPROVE (1 NIT). Adjudicated:
- INT-1 (BLOCKER, integrity — design+mutation MISSED it, no preserve seam in their probes): H's _fill_chash
  broke the cross-repo preserve↔histogram content_hash contract. histogram_external.py plugin re-derives
  the node hash as SHA-256(spec) ("IDENTICAL to the fill node's descriptor hash by construction"), but
  _fill_chash now records SHA-256(spec+disc) for unweighted/n_weights>1/axis-mode fills → build_bundle's
  "mismatched/poisoned" guard fires. INDEPENDENTLY REPRODUCED: preserve/m25 test_histogram_terminal,
  m27 test_histogram_multi_axis_fill, m30 test_gh_multi_weight_fill all RED w/ PreserveError, all import
  graphed_histogram (the seam), COV run-tests EXIT=1. Fix = OPTION (b), graphed-only: histogram_external
  folds the SAME disc from params (params confirmed to carry weighted/n_axes/sampled/n_weights>1 line
  461-468, variation for axis line 640) matching _fill_chash format (spec + "\x00" + "\x00".join([
  "unweighted" if not weighted, "n_weights=N" if !=1, "variation=<json>" if present])); canonical
  single-weight stays content_hash(spec) verbatim. Close class vs ALL 3 members (unweighted, multi-weight,
  axis-mode). No core/execute.py change (option a rejected: leaves content_hash(spec) an incomplete
  content-address + needs core edit), no histogram change, no frozen mod.
- G1-boost-import (MED, design): graphed.universe axis-arm imports boost_histogram (violates §A.4
  backend-agnostic + §6.2(3) no-boost-in-graphed + silenced PLC0415 w/ noqa). Fix: import-free
  x.axes[index].index(label) integer form (design measured KeyError-on-unknown identical to bh.loc).
- D1-rename-overclaim (MED, design): docs "honest limits" claims axis-mode rename is by-value-only /
  from_ref immune — FALSE per §1.2 carve-out (axis-mode labels ride StrCategory bins + variation payload
  → IR → task_id folds ir → rename invalidates unconditionally incl from_ref). Fix: scope rename+field-
  churn to sibling mode, add axis-mode carve-out.
- F2/MUT-F2 (LOW/NIT): ACCEPT as-is (disclosed, >90% diff cov, 2 defensive lines; frozen anchor needs
  re-freeze, not worth it). F1 VINDICATED (design+mutation adversarially confirmed _fill_chash correct:
  collision pre-existing/sibling-only, field set exhaustive — only has_sample/n_axes unfolded & both
  spec-borne, m48 golden byte-stable). NEXT: graphed-only fix agent (INT-1 + 2 MED) → re-verify 3 preserve
  tests green + full graphed suite + histogram 178/178 unaffected → delta re-review → PRs.

## m50 fix cycle 1 DONE (all 3 findings) + 2 conditions adjudicated (2026-09-02)
fix1: 30117b4 (INT-1 preserve plugin) + 0f8866e (G1 boost-import) + ff9c329 (D1 docs rename), +283/-39
7 files. VERIFIED: frozen untouched; 3 preserve tests green (m25/m27/m30: 20 passed/6 skipped/0 failed);
boost import+bh.loc+PLC0415 gone from accessors; histogram 178/178 unaffected; axis-mode class-closure
witness (tests/extra/preserve/m50/test_axis_mode_preservation.py) passes. INT-1 fix SCRUTINIZED sound:
synthesize gains recorded_hash arg (SynthesizePayload sig change, only histogram plugin uses it — no other
synthesize fn exists); _canonical_payload rebuilds _fill_chash's disc byte-for-byte; tries discriminated
then bare form, emits whichever hashes to ch (reconciles the TWO record paths agent found: Histogram.fill
discriminated vs legacy record_external bare, frozen m27); falls back to canonical to SURFACE genuine
mismatch → poison-detection PRESERVED (only emits params-derived bytes). eval_histogram delegates
multi-weight to FillEvaluator (m27/m30 green confirm equivalence). Agent's adversarial same-spec hunt:
could NOT construct a still-mis-hashing pair (discriminated-vs-bare is the only case). D1 probe: axis
rename → IR changed (1856≠1880), sibling rename → IR byte-identical (2405=2405).
TWO PRE-EXISTING CONDITIONS (both OUT of m50 scope):
1. Full precommit's naive whole-repo `pytest -q` leg collect-fails (basename collisions) — PRE-EXISTING
   repo-wide (naive collect broken at HEAD regardless of m50; that's why run-tests.sh splits per-subtree).
   graphed CI uses ./scripts/run-tests.sh (ci.yml:41/60), NOT naive pytest → NOT a CI blocker. Authoritative
   gate green. Precommit --fast + run-tests.sh cover the real gates.
2. Seam-active variation_axis=True fill records histogram.weight_guard externals (no preserve plugin) →
   whole-GRAPH reproduce blocked. Orthogonal to INT-1 (content_hash contract fully closed). m50 preserves
   the §9.2 TRIPLE form (zero Externals); fill-graph bundle w/ weight_guard = Phase-2 §11. → PHASE-2
   FOLLOW-UP (weight_guard preserve plugin, payload derivable), not m50. NEXT: full run-tests.sh confirm
   (bibw9p15f running) → focused delta re-review (INT-1 poison-probe + mutation on new plugin code + 2 MED
   closure) → PRs (histogram pins graphed@m50-vary).

## m50 delta re-review (vary-m50-delta-review): APPROVE — review loop CLOSED (2026-09-02)
Fix-cycle-1 delta (5165f25..HEAD) closes all 3 findings, no new defect, new code non-vacuously tested.
INT-1: (a) POISON DETECTION intact — driven build_bundle w/ tampered id-vs-params: byte-flip /
disc-mismatch(id=discriminated-unweighted,params=weighted-single) / wrong-variation ALL → PreserveError;
legit discriminated-unweighted control builds cleanly (probe discriminates, not always-raising). try-both
returns a candidate ONLY when it hashes to recorded id, else falls to canonical → bundle.py integrity
rejects. (b) disc byte-exact vs _fill_chash over all 7 {unweighted/single/multi}×{sibling/axis} combos
incl. 2-member n_weights+variation ordering — ALL MATCH. (c) MUTATION MATRIX 8 mutants ALL KILLED, no
survivor (M1 drop-unweighted→m25/m27; M3 corrupt-n_weights→m30/m50pair; M6 corrupt-\x00→5 tests;
M7 drop-variation→m50axis; M4 return-bare-uncond→every discriminated case; M5 emit-canonical-uncond→m27
bare-leg; M8 eval-force-nweights=1→m27/m30) — try-both required BOTH directions. G1: no boost import in
python/graphed (only §A.4 comment + framework metadata string); axes[index].index KeyError identical to
bh.loc; frozen green. D1: rename claim matches §1.2 (sibling by-value only, axis unconditional incl
from_ref), probe-confirmed, sphinx -W 0 warnings. New-defect: SynthesizePayload sig change contained
(AST-walked 9 externals, histogram only one w/ synthesize; sole call site bundle.py:171). INFORMATIONAL
(non-gating, accepted like F2): pure ORDER-SWAP of the 2 independent disc members survives mutation (no
test records a 2-member discriminated fill via first candidate) but order correctness PROVEN by (b) byte-
exact probe → test-discrimination gap on correct code, not a defect (closing needs re-freeze; not worth).
m50 REVIEW CLOSED. Full graphed suite RC=0/94%, histogram 178/178, frozen untouched. NEXT: PRs — push
both m50-vary branches, open graphed PR + graphed-histogram PR (pin graphed@m50-vary), verify CI, await
merge authority. Meta submodule bumps deferred to arc landing (post-m51). Phase-2 follow-up: weight_guard
preserve plugin (condition 2).

## m50 PRs OPENED — awaiting CI + merge authority (2026-09-02)
Both branches pushed, PRs open:
- graphed#5 https://github.com/graphed-org/graphed/pull/5 — carries G1 (8c62dbe) + D1 (5165f25) + fix1
  (30117b4/0f8866e/ff9c329) on base ee354b0. Full suite RC=0/94%, frozen untouched. CI skips m25/m27/m30
  via importorskip → coverage stays >=90 w/ ~4% headroom.
- graphed-histogram#4 https://github.com/graphed-org/graphed-histogram/pull/4 — H1 (b6516d4) + H2 (2fa36c3)
  + D1 (00952a6) + ci pin a71d8c2. ci.yml:17 GRAPHED pinned @m50-vary (revert->@main after graphed#5 merges,
  before merging this PR — comment ci.yml:15-16). Histogram PR CI validates G1<->histogram integration
  against graphed@m50-vary. 178/178 local.
MERGE ORDER (needs explicit user authority — irreversible, m49 precedent): (1) merge graphed#5 -> graphed
main; (2) commit ci.yml revert @m50-vary->@main on histogram m50-vary, re-run CI; (3) merge histogram#4.
Both via GraphQL enqueuePullRequest if `gh pr merge` fails (merge-queue repos). CI monitor bglyzglyc armed.

## m50 FULLY LANDED — both PRs merged (2026-09-02)
graphed#5 MERGED -> main cea7985 "m50: variation introspection + varied preservation (vary arc) (#5)"
(G1+D1+fix1). histogram#4 MERGED -> main 32bd44b "m50: variation-axis fill lowering (vary arc) (#4)"
(H1+H2+D1). Both repos use MERGE QUEUES: `gh pr merge --squash` fails ("merge strategy set by the merge
queue / Auto merge not allowed"); GraphQL `enqueuePullRequest(input:{pullRequestId}){mergeQueueEntry{...}}`
works (payload has NO `pullRequest` field — mergeQueueEntry only). Reshuffle: merged graphed#5 first, then
committed histogram ci.yml pin revert @m50-vary->@main (430b724), re-ran histogram CI green vs graphed@main,
enqueued histogram#4. m50 review loop was already CLOSED (delta APPROVE). Frozen untouched both repos.
meta submodule bumps + §12.3 DEFERRED to arc landing (post-m51). Phase-2 follow-up: weight_guard preserve
plugin. NEXT: m51 §6.4 section review.

## side task: issue #2 (EL8/glibc 2.28) — opus subagent issue2-el8-glibc, PR#6 open (2026-09-02)
User-requested during m50 landing. Root cause (measured): graphed Linux wheels tagged manylinux_2_34
(glibc 2.34); objdump -T shows gettid@GLIBC_2.30 (reporter's exact error) + fstat64@2.33 + pthread_*@2.34;
positive control GLIBC_2.2.5 present. Cause: wheels.yml/release.yml run bare `maturin build --release` on
Ubuntu 24.04 (glibc 2.39), no manylinux container. Fix (PR graphed#6, branch fix/el8-glibc228): add
`maturin build --release --zig --compatibility manylinux_2_28` on Linux jobs (--zig retargets the actual
glibc floor, not just the tag; pure-Rust crate = low zig risk; keeps 3.14t + macOS/Windows untouched).
x86_64 incl 3.14t built GREEN on 2_28; arm64 verification pending. PR left UNMERGED for user.

## m51 §6.4 SECTION REVIEW — dispatched (2026-09-02)
§6.4 (variation-aware write-out) = plan lines 1616-1904, sub-rules (a)-(g): (a) OR-of-selections superset
+ explicit select= mask(s), per-(field,level) keying, decidable entry check [2 predicates: multiplicity +
row-space; 2a lineage record-time / 2b row-count exec-time / 2c depth]; (b) column augmentation
__vary_{label}__{field} + collision refusal; (c) bit-exact XOR delta + packbits masks (computed in
_WritePart, in-graph bit-view not expressible); (d) same-multiplicity refusal (offsets differ -> REFUSE);
(e) parquet-KV manifest via PUBLIC recompose (no awkward._connect import), sorted keys, read_varied reader;
(f) seam: parquet = extra marked outputs of compile_ir (node-id resolve not positional); ROOT graphed_write
gains IR eval = the LARGER half; numpy EXEMPT (refuses Varied first-positional). Review = multi-lens
ultracode workflow (code fact-check graphed + uproot fork, measured-claim re-probe, design consistency,
scope/sizing) + adversarial verify of B/H findings. Two repos: ~/vibe-coding/graphed + uproot5-graphed-mvp.

## m51 §6.4 SECTION REVIEW round 1 — 0 B/H survive, 6 MED + folds (2026-09-02)
Workflow wf_1c585b5c-ce0 (10 agents, ~1.03M tok): 5 lenses (fact-graphed, fact-root, probe-measured,
design-consistency, scope-sizing) + adversarial verify of the 5 BLOCKER/HIGH. Verify RESULT: 2 refuted,
3 downgraded to MED → ZERO surviving B/H. Output: tasks/wific067v.output; journal in the wf transcript dir.
REFUTED (verified false): (R1) design BLOCKER "vary bridge anchor self-contradictory" — fabricated the
premise context_of(record)=C; actual anchor reads events.Jet (handle=root events), so (2a) accepts by BARE
equality; §10:3467-3474 already supplies the real discriminator E2=vary(E1). (R2) scope HIGH "ROOT larger
half undesigned" — elided §10:3581's parenthetical "(derived columns in ROOT skims)"; ROOT half is
derived-col eval, needs no varied manifest.
CONFIRMED-as-MED (change what gets built → re-plan r45): M1 §6.4a cites _form_meta for depth but AwkwardForm
has no depth/ndim → _form_meta('depth') CRASHES; correct = session.form(array).tt.ndim (probe-verified).
M2 §6.4e promises a VARIED ROOT read_varied but §10 (authoritative freeze list) scopes ROOT to
derived-columns-only → align §6.4e to §10, varied ROOT write-out = Phase-2 (no ROOT manifest/delta designed
& none needed for derived cols). M3 §6.4e:1822 "dropping awkward_array_metadata would break ak.from_parquet
round-tripping" is DIRECTIONALLY FALSE (reconstruction rides ak:parameters; 16 forms + surgical strip) →
delete clause (swap necessity carried by no-metadata-param + byte-golden). M4 §6.4a graphed.selection must
implement §9.1 full 3-case (case-2 non-None on universe/nominal) not a thin _selection() wrapper (returns
None on project links) else universe/nominal REFUSE control can't fire. M5 "fifth positive control" names
TWO fixtures (re-recorded-interning @1675 vs MET.pt-origination @1689) → disambiguate, align §6.4a↔§10.
M6 §10 fork-gates omit the cross-repo pin (fork installs graphed@main but needs new graphed.selection) →
add two-PR pin/reshuffle note. FOLDS (exit-round): M7 drop "larger half" label (1881/2426/3582); L1 add
level-≥1 depth to the checks-run record-time set (1728-1734); NIT §6.4a:1664 "requires the admission"
wording; version stamps LEFT (facts hold on 2.13.0, non-actionable).
Adjudication: MED changes-build → re-plan; folds applied same pass. Dispatched vary-m51-replan-r45 (opus
xhigh) to apply class repairs + commit r45; NEXT = adversarial delta re-review of the diff → if 0 B/H/M,
decompose. LOOP-EXIT rule applied: magnitude labels + summary omissions + wording = exit-round folds, not
loop-openers.

## m51 §6.4 SECTION REVIEW — CLOSED at r46 (2026-09-03)
r45 (f4b550e) applied the 6 MED class repairs + 3 folds; INDEPENDENT delta re-review (vary-m51-delta-review,
opus xhigh) verdict CLEAN — 0 B/H/M, every closure backed by re-grep/live-probe/quote, whole-§6.4 coherence
pass clean, could NOT construct a failure for any fix. Sole sub-threshold NIT (exit-round): (2c) depth
citation offered `.tt.layout.minmax_depth` "equivalently" to `.tt.ndim` (tuple vs int trap) → folded in r46
(402ec46), aside dropped, `.tt.ndim` kept. Class greps post-r46: "larger half" 0, "fifth positive control"
0, "minmax_depth" 0. Key design outcomes locked for m51: ROOT half = DERIVED-COLUMN IR evaluation only in v1
(variation-aware ROOT write-out+reader = Phase-2 §11; no ROOT manifest/delta designed/needed); depth check =
typetracer form .tt.ndim (AwkwardForm has no depth accessor); graphed.selection = §9.1 full 3-case (case-2
non-None on universe/nominal, NOT a _selection() wrapper); manifest = parquet-KV via PUBLIC recompose
(Table.replace_schema_metadata, no awkward._connect import); cross-repo two-PR pin (fork graphed.yml GRAPHED
@main→m51-branch→@main). NEXT: m51 DECOMPOSE → fact-check → freeze → gated pipeline (test-authors → impl →
three-lens review → PRs). Scope-sizing reviewer's proposed graphed partition (starting point): C1
graphed.selection+§2.3d+numpy-refusal; C2 entry-check predicates+select= plumbing; C3 augmentation+XOR/
packbits+naming/collision; C4 manifest+read_varied+§7.2 reuse; + ROOT derived-column-eval half. Est ~4-6k
LOC across graphed + fork, fits one PR/repo, each commit ≤1-2k. m51 touches graphed + uproot5-graphed-mvp fork.

## m51 DECOMPOSE artifact + pin correction r47 (2026-09-03)
vary-m51-decompose produced vary-m51-decomposition.md (NOT committed — fact-check pending). Partition
(probed vs real LOC, all << 1-2k band): C1 graphed.selection (§9.1 full 3-case; case-2 NEW) + numpy refusal
~70-140; C2 select= API + record-time entry checks (2a lineage/vary-admission, 2c depth .tt.ndim, bare-key)
+ level-0 OR superset ~220-360; C3 augmentation + XOR/packbits in _WritePart + §7.2 node-id unpack + naming/
collision + row-space refusal + merge refusal + exec-time predicates ~320-500 (band-risk flagged, C3a/C3b
split available); C4 parquet-KV manifest (sorted keys + levels (depth,field) order) + writer swap (public
replace_schema_metadata) + read_varied ~240-400; D1 docs ~60-150; R1 (fork) ROOT derived-column IR eval only
~50-120. Trees: graphed tests/frozen/awkward/m51 (A-N) + tests/frozen/numpy/m51 (refusal L, globally unique)
+ fork tests/frozen/m51 (K). Order C1->C2->C3->C4; R1 independent.
FACT-CHECK FLAG (confirmed + fixed r47): decompose flagged §10(d)'s cross-repo PIN as vestigial. M6 pin note
(r45) premised on fork needing graphed.selection — but that was PRE-M2 varied-ROOT. FINAL scope: ROOT half =
derived-col eval only; fork imports ONLY shipped graphed API (Array/Session/compile_ir/evaluate_ir/core.*/
awkward.*, >=m10). PROBE: fork src/ grep graphed.selection|select=|read_varied = EMPTY (evaluate_ir positive
control live at _graphed.py:358/372/382). So NO cross-repo pin needed; fork TEST_SANITY collects vs
graphed@main. r47 (8cdf7d4) rewrote §10(d): two INDEPENDENT PRs, graphed-first for tidiness, pin retained
only as documented fallback if varied-ROOT returns (§11). This is a decomposition-fact-check catch (m50 MC-1
shape), NOT a design re-open (ROOT scope unchanged). NEXT: independent dc fact-check (vary-m51-dc-factcheck,
opus xhigh) — anchor-map completeness (every §10/m51 anchor -> tree/file/commit), file/LOC grounding, tree
basename-uniqueness (3.14t-collects-whole), dependency ordering, Phase-2 boundary, trap ledger. Clean ->
freeze decomposition -> gated pipeline.

## m51 DECOMPOSE fact-check CLEAN → frozen (acfe34e) → TEST_AUTHORING dispatched (2026-09-03)
vary-m51-dc-factcheck verdict CLEAN (0 B/H/M): 14 §10/m51 anchors <-> 14 tree letters 1:1; pin removal
re-confirmed; symbols grounded; LOC in band; C1->C2->C3->C4 order clean (no MC-1); Phase-2 boundary intact;
trap ledger accurate. 2 LOW folded (basename check --ignore=m40; header r46->r47; §5 flag marked resolved).
Decomposition COMMITTED acfe34e (graphed-workdir). Clones: graphed on m50-vary, origin/main 54325a4 (m50 +
wheels PR#6); fork on graphed-mvp, origin d500682 (fork's FIRST frozen tree). TEST_AUTHORING: two ISOLATED
authors dispatched — vary-m51-ta-graphed (opus xhigh, branch m51-vary off origin/main): awkward/m51 A-N (11
files) + numpy/m51 L (awkward-free refusal); owns freeze spellings (select= keys, __vary_{label}__{field},
manifest keys+levels order, read_varied/graphed.selection names, numpy refusal msg); 3 load-bearing
discriminators (B all-zero-delta node-id-vs-positional divergence, E Jet.pt-vs-flat-Jet_pt collision, D/2c
jagged-level-0 passing 2a+2b). vary-m51-ta-fork (opus high, branch m51-vary off graphed-mvp): fork
tests/frozen/m51 K (ROOT derived-column round-trip; fails vs today's verbatim-copy graphed_write). NEXT:
authors report -> TEST_SANITY (collect + non-vacuous + basename check) -> freeze tags (graphed m51-freeze,
fork freeze-m51) -> implementers (graphed C1-C4+D1 in order; fork R1) -> three-lens review -> two independent
PRs (graphed-first, NO pin). NOTE: m51 landing = 2 PRs but NO cross-repo pin (r47).

## m51 fork: TEST_SANITY clean → freeze-m51 → R1 implementer (2026-09-03)
Fork test-author DONE: branch m51-vary off graphed-mvp (base verified: graphed integration lands on
graphed-mvp not main), commit f9e6333, tests/frozen/m51 (4 tests: 3 derived-column + 1 positive control) +
README + scaffolding. Independent TEST_SANITY (graphed .venv, --noconftest): collects, 3 FAILED (real
AssertionError "derived column dropped", feature absent) + 1 PASSED (positive control), DETERMINISTIC 2x.
Froze: tag freeze-m51 @ f9e6333. Dispatched vary-m51-impl-fork (opus high): R1 = _write_partition evaluates
the graphed graph per partition (mirror _graphed.py graphed_head compile_ir+evaluate_ir @~382) writing the
EVALUATED record's derived fields; derived-columns-only (NOT varied). Also wires fork frozen-tree CI (root
conftest imports RangeHTTPServer — must not break frozen collection) + pyproject/mypy per §10 fork-gates.
Gates FOREGROUND (G1 stall lesson). Parallel with graphed test-author. NOTE: fork side runs INDEPENDENTLY
(no cross-repo pin); its PR can open any time. graphed side (vary-m51-ta-graphed, 11 files) still authoring.

## m51 fork R1 — implementer crashed transiently, work sound + recovered (2026-09-03)
vary-m51-impl-fork died on "Connection lost mid-response" (transient API error, NOT task failure) after
applying a SOUND change but before gates/attempts.md/commit. Inspected: working tree had uncommitted
_graphed_write.py (+36/-12) + graphed.yml (+9); frozen suite PASSES 4/4; frozen tests UNMODIFIED since
freeze-m51. Diff reviewed sound: _write_partition evaluates compiled graph per partition
((evaluated,)=evaluate_ir(compiled,backend,{source_name:chunk})) not verbatim copy — mirrors graphed_head;
read list = SYNTACTIC _evaluation_columns not necessary_columns buffer-projection (evaluation replays field
reads output buffers don't touch → projection starves, §6.4f); shipped API only, derived-cols only. graphed.yml
adds isolated `pytest tests/frozen --noconftest` step (sidesteps unrelated RangeHTTPServer root conftest) +
m51-vary push branch. Re-dispatched vary-m51-impl-fork-2 (opus high) to VERIFY + full gate battery (coverage
≥90% diff, lint, mypy, determinism) FOREGROUND + attempts.md + commit. Lesson: a transient API crash mid-impl
leaves recoverable working-tree state — inspect + re-dispatch a finishing agent, don't gamble on resuming a
connection-lost context.

## m51 fork R1 committed (4c706ba) + fork-gates follow-up (2026-09-03)
vary-m51-impl-fork-2 finished R1: verified prior work, FOUND+FIXED a regression (bare non-record expr
g.x+g.y -> fieldless array -> TypeError; fix `out_rec = evaluated if evaluated.fields else chunk`, strict
superset, 24/24 non-frozen green), gates: frozen 4/4 green+deterministic+UNMODIFIED, 100% diff coverage
(8/8 added lines; bare-expr fallback branch covered by non-frozen m10 test — flagged honestly), ruff clean;
black N/A (baseline fails black, not in CI); mypy N/A (no [tool.mypy], untyped fork). Committed 4c706ba
(src + graphed.yml frozen-step + attempts.md). Independent verify: frozen+m10 regression = 5 passed, frozen
diff empty. GAP: §10 fork-gates (a) coverage-gate-in-CI, (b) [tool.mypy] config, (c) DoD matrix/trigger are
UNMET (graphed.yml has no lint/mypy/cov step; pyproject has ruff not mypy). These ride the m51 fork PR (fork's
first gated milestone) = R1 scope. Sent follow-up to vary-m51-impl-fork-2: wire cov gate, add proportionate
[tool.mypy] scoped to new graphed-integration source (untyped-upstream reality — don't rabbit-hole; document
reduced scope if genuinely blocked), DoD matrix+trigger. Separate commit on m51-vary. graphed side still
authoring (vary-m51-ta-graphed, 11 files).

## m51 graphed: TEST_SANITY clean → m51-freeze → implementer dispatched (2026-09-03)
graphed test-author DONE: branch m51-vary @ ab5c71e (origin/main 54325a4), tests/frozen/awkward/m51 (11 files
A-J,N + helper + README) + tests/frozen/numpy/m51 (L, awkward-free + README). No TEST_DISPUTE. Independent
TEST_SANITY: 40 collect / 0 collection errors; 36 RED feature-absent (14x "no attribute 'selection'", 55x
"unexpected keyword argument 'select'"; NO NameError/fixture/import surprises) + 4 GREEN positive controls;
DETERMINISTIC (run1==run2); numpy/m51 awkward-free (grep clean); basename instrument LIVE (no-prune control
surfaces m5<->m40 test_projection.py; m40-pruned empty = m51 no new collision). Froze: tag m51-freeze @
ab5c71e (13 files). FREEZE SPELLINGS (LAW, in awkward/m51 README): graphed.selection; read_varied;
select= single-mask/{int|(field,depth)} dict; __vary_{label}__{field_flat} value + __vary_{label}__mask__{entry};
KV b"graphed.variations"; manifest json {labels+levels}, levels ordered (depth,flat or ""), json.dumps
sort_keys; numpy refusal GraphedError names awkward on Varied first-positional (no select=). TWO CROSS-FROZEN
GOTCHAS: (1) to_parquet accepting = BEHAVIORAL, keep array:Any + NOT in VERB_DISPOSITIONS (else frozen m48
test_to_parquet_carries_no_disposition_until_m51 breaks); (2) §7.2 opt-merge msg matches r"merge|optimiz".
Anchor B node-id trap: murf_1 shares nominal node 13 (collapse EARLY not last) -> positional unpack
misassigns -> impl MUST resolve by node id. Dispatched vary-m51-impl-graphed (opus high): C1 graphed.selection
+ numpy refusal -> C2 select= + record-time entry checks + superset -> C3 augmentation + XOR/packbits +
node-id unpack + collision + exec-time checks -> C4 manifest + writer-swap (public recompose, no
awkward._connect) + read_varied -> D1 docs. Commit each partition (crash-durable). Gates FOREGROUND.

## m51 fork three-lens review: REJECT (1 MED) → fix dispatched (2026-09-03)
vary-m51-review-fork (opus xhigh, design+integrity+mutation) on delta freeze-m51..8f65049. Design correct
(R1 mirrors graphed_head; _evaluation_columns-over-necessary_columns proven load-bearing via
gak.zip({a:x,b:y})[[a]] starve; fallback correct for per-event cases; no varied creep; §5 no-pin CONFIRMED
— only shipped API). Integrity clean (frozen unmodified+non-vacuous reproduced; diff-cov gate legit 9/9=100%
proven live at 55.6% frozen-only; mypy meaningful, evaluated:Any legit boundary; reduced CI scope per §10(c)).
Gates all re-run green. MUTATION kill-matrix: (1) revert eval→verbatim KILLED by frozen; (2) break fallback
NOT caught by frozen but caught by non-frozen m10+extra+cov-gate (informational); (3) corrupt read
list→necessary_columns caught by NOTHING. THE MED: the syntactic-_evaluation_columns starve-avoidance
(§6.4f) is load-bearing but has ZERO witness (mutation 3) — norm "tests witness the mechanism engaged" →
MED. Fix (tests/extra only, frozen untouched, ~10 lines, reviewer-designed+pre-verified non-vacuous): add
starve-witness gak.zip({a:x,b:y})[[a]] → assert output fields==['a'] (starves KeyError under
necessary_columns). Reviewer pre-committed "add witness → APPROVE." LOW (optional): opaque bare-expr fallback
message for out-of-scope scalar/zip({}). Sent fix to vary-m51-impl-fork-2. graphed impl still running.

## m51 fork: review CLOSED (APPROVE) → PR #1 opened → CI validating (2026-09-03)
Fork fix 2e37b7b (test-only): starve-witness test_syntactic_read_list_witness_no_starve added; non-vacuity
MEASURED (repoint read list->necessary_columns => AttributeError "no field named 'y'" starve, revert=>pass;
source back at committed). Verified: frozen untouched (empty diff vs freeze-m51), frozen(4)+extra(3)=7 pass.
Fork three-lens review CLOSED = APPROVE (R1 4c706ba + gates 8f65049 + witness 2e37b7b). Pushed m51-vary
(fork's FIRST PR — prior graphed work went direct to graphed-mvp; gh pr list empty). Opened FORK PR #1
https://github.com/graphed-org/uproot5-graphed-mvp/pull/1 base=graphed-mvp. graphed.yml CI triggers on the
m51-vary PUSH (not pull_request — deliberately, to avoid colliding w/ uproot's matrix), so PR shows the head
commit's push-CI checks. Monitor bn0kunatv validates the NEVER-remotely-run gate wiring (diff_coverage_gate.py
diffs vs origin/graphed-mvp needs fetch-depth:0; scoped mypy; --noconftest frozen step) on 3.11/3.12. Fork
side fully DONE pending CI + user merge auth (targets graphed-mvp). graphed side still IMPLEMENTING (long pole).

## m51 fork: CI GREEN → PR #1 ready (awaiting merge auth) + frozen-test dispute UPHELD (2026-09-03)
Fork CI on push 5b012ba is GREEN (run 33727260427): all gates pass (frozen-acceptance --noconftest,
scoped mypy, diff-coverage, full uproot suite). Two pre-existing infra reds diagnosed + fixed, NEITHER a
graphed regression: (1) 1f9db92 — diff-coverage gate step ran `python -m coverage` without installing it
(mypy step installs mypy inline the same way); "No module named coverage" on 3.11/3.12, passed locally only
because dev venv had it. (2) 5b012ba — full-suite step hard-failed on test_*_s3 (4 tests, all
@pytest.mark.network) with FileNotFoundError on public pivarski-princeton/…picoDst.root (external S3 data
rot); 995 uproot tests passed, 0 graphed/m51 fails. Deselected via `-k "not xrootd and not s3"` on the same
basis as xrootd (external infra this lightweight job doesn't provision); local-http tests keep running w/
existing rerun-on-transient. Verified all 4 s3-named tests are network-marked (no non-network coverage lost).
Fork PR #1 (base graphed-mvp) fully DONE pending USER merge auth.

FROZEN-TEST DISPUTE (graphed side, adjudicated UPHELD): vary-m51-impl-graphed filed a dispute on
tests/frozen/awkward/m51/test_selection_bridge.py::
test_selection_on_a_universe_nominal_context_is_a_grandparent_array_and_refuses_downstream line 128:
`assert as_list(projected) == as_list(mask)` compares TWO deferred graphed arrays; as_list=ak.to_list can't
list a deferred graphed.Array (getattr fabricates a non-callable `tolist` Array → TypeError('Array' object
is not callable)) — assertion never reaches value-compare, never fails for its guarded reason. Independently
reproduced w/ live positive control: as_list(session.materialize(mask)) lists 60 vals; as_list(mask) raises.
It is the SOLE as_list-on-deferred call in the entire m48-m51 frozen suite missing the session.materialize
wrapper (m48:93-94,118-119; m49:56 all wrap). Adjudication: UPHELD; remedy = one-line m51-freeze-fixup
(rename already-bound _session->session, wrap both operands) — REPAIRS the value-eq check to do what its
comment says, does NOT weaken. Freeze-fixup precedent: m40-freeze3/4/5, m48-freeze2; decomp §4 anticipates
m51-freeze-fixup. BLOCKED: editing tests/frozen/** gated by auto-mode permission classifier; surfaced to
user for authorization (won't route around w/ sed/python). Implementer told: continue C2-C4+D1, report that
test red-pending-fixup, don't touch tests/frozen.

## m51 graphed impl COMPLETE (C1-C4+D1) + dispute #2 adjudicated UPHELD (2026-09-03)
vary-m51-impl-graphed done on branch m51-vary (freeze ab5c71e), NOT pushed. Commits: 06141f0 C1
(selection bridge + numpy varied-write refusal), 578bdbb C2+C3 merged (write path: record-time entry
checks + superset + column augmentation + §7.2 node-id unpack + exec-time predicates; C2/C3 can't split —
integrity forbids a stub between commits; well under band), 4665b15 C4 (parquet-KV manifest + read_varied),
aa43e93 D1 (docs, executed example), 9aca321 style. Gates @ tip: 38/40 frozen green (2 reds = the 2
disputes), git diff m51-freeze -- tests/frozen EMPTY, diff-cov 97.4 line/92.3 branch, ruff+ruff-fmt clean,
mypy --strict Success(77), sphinx -W, determinism F green, integrity clean (0 NotImpl/0 bare-except/16
messaged raises). NODE-ID TRAP resolved: rank={nid:i for i,nid in enumerate(dict.fromkeys(out.node_id))};
murf_1 shares nominal's id, evaluate_ir returns 1 val/distinct id, resolved(nid) replicates to every label —
anchor B bit-exact (murf_1.w==nominal.w, murf_5em1.w!=nominal.w). Worklog:
/Users/lgray/vibe-coding/graphed-workdir/m51-graphed-impl-worklog.md; attempts: graphed/.graphed/m51/attempts.md.

DISPUTE #2 (test_superset_rows.py:56) adjudicated UPHELD (independently reproduced w/ live positive control):
evt-mask sizes nominal=43/jes_up=44/jes_down=41; masks strictly nested (jes_down⊆nominal⊆jes_up because
ak.any(pt*c>30) is monotone in c, 1.05>1.0>0.95), so level-0 OR EQUALS jes_up (superset==jes_up True); line
56 `superset_size(44) > max_uni(44)` = False, unsatisfiable for any correct impl. It's a FIXTURE
self-consistency assertion (after 47/51/55 pass it reduces to eager-superset>max-eager-universe). Lines
47/51/55 (per-universe==eager, union==eager superset, sizes equal) all PASS; feature correct. FIX (minimal,
non-weakening): line 56 max->min (44>41=True, witnesses universes differ = migration property) + docstring
"STRICTLY larger than any single universe"->"strictly larger than the smallest universe". Rejected
gold-plating (non-monotone fixture redesign): 47/51/55 already pin superset to the INDEPENDENT eager OR, and
jes_down reading 41 of the 44 stored rows already exercises §6.4a superset-write-then-mask.

BOTH disputes -> ONE m51-freeze-fixup (decomp §4 anticipates it): (1) selection_bridge:128 materialize wrap;
(2) superset_rows:56 max->min + docstring. BLOCKED on user authorization for tests/frozen edit (permission
classifier). Impl told: work ACCEPTED, don't touch frozen, push m51-vary for graphed-CI validation of
non-frozen+gates while auth pending.

## m51-freeze-fixup LANDED (40/40 green) → three-lens impl review launched (2026-09-03)
User authorized the tests/frozen edit. Applied both adjudicated fixes on graphed branch m51-vary:
- test_selection_bridge.py:128 — _session->session, wrap both operands in session.materialize (m48/m49 idiom).
- test_superset_rows.py:56 — max->min + docstring "any single universe"->"the smallest universe".
Commit 64f606d, tagged m51-freeze-fixup. `git diff m51-freeze -- tests/frozen` = EXACTLY those 2 files,
exactly the intended changes (no drift; uv.lock untracked, excluded). Re-ran: awkward m51 = 37 passed,
numpy m51 = 3 passed => 40/40 m51 frozen GREEN; both formerly-red tests PASSED explicitly (red->green
transition witnesses non-vacuity). graphed CI is pull_request-triggered (not branch-push), so CI runs at
PR time; sequence = review -> fix -> push+PR.

THREE-LENS IMPL REVIEW launched as workflow wnkoetmpz (opus xhigh lenses): design + integrity PARALLEL
(read-only wrt source), then mutation EXCLUSIVE (edit->test->revert on the editable-install source, can't
overlap), then adversarial verify of every finding. Surface = source diff 06141f0..9aca321 (~742 LOC,
python/graphed/awkward/io.py +697 + context/accessors/numpy/__init__). Mechanisms mapped to io.py fns:
_VariedWritePart.resolved (§7.2 node-id), _write_varied/_evaluation_columns_union (superset OR),
_encode_delta/_apply_xor/_decode_* (XOR/packbits), _check_collision/_check_bare_key (augmentation),
_lineage_refusal/_check_depth(.tt.ndim) (record-time checks), _write_augmented/_build_manifest (public
KV route, no awkward._connect), read_varied/_reconstruct_universe. Awaiting workflow result -> fix cycles
-> push m51-vary -> open graphed PR (awaits user merge auth, like fork PR #1).

## m51 graphed three-lens review ROUND 1 (wnkoetmpz): integrity clean + 1 MED; design/mutation redo (2026-09-03)
Workflow wnkoetmpz (design+integrity parallel -> mutation exclusive -> verify). Outcomes:
- INTEGRITY: LEGITIMATELY green (independently reproduced). frozen untouched-except-fixup (git diff
  m51-freeze..9aca321 -- tests/frozen EMPTY); fixup 64f606d = exactly the 2 adjudicated changes; non-vacuous
  (both fixup tests red-before/green-after + mutation-kill RED). Gates: mypy strict Success(77), ruff+format
  clean, awkward m51 37 / numpy m51 3 passed, determinism anchor 2 passed (has positive control vs null
  manifest), sphinx -W zero warnings. Diff-cov re-derived FROZEN-only = 379/389=97.4% line, 144/156=92.3%
  branch (matches reported). Integrity scan clean (0 stub/bare-except/blanket-ignore; 2 justified noqa PLC0415).
  No awkward._connect import (ast walk; the 1 textual hit is a docstring). numpy added lines import no awkward.
- CONFIRMED MED (verifier reproduced): io.py:~550 level>=1 STRUCTURAL-mask refusal (raises GraphedError when
  a level-k>=1 mask's offsets don't match the field it filters) is load-bearing silent-corruption guard but
  has NO frozen/extra test witness. Repro: {Jet,MET} record, select={0:evt_mask,("Jet",1):muon_mask} with
  muon_mask=Muon.pt>0 (passes record-time depth, carries Muon offsets) -> GraphedError at :550. FIX (pending):
  add witness test to tests/extra/awkward/m51 (frozen untouchable). Sibling row-count raise at :543 likely
  unreachable via context-constrained API (record-time fires first) — re-run mutation lens to confirm.
- DESIGN lens MISFIRED: returned placeholder {"summary":"test","findings":[]} (one-off, not schema — integrity
  used same schema fully). MUST redo.
- MUTATION lens CRASHED (transient "response stopped arriving") mid M5-struct mutation; LEFT DIRTY SOURCE:
  io.py:547 `if False and mask_spec.depth>=1 ... # MUT M5-struct: disabled` (guard disabled). REVERTED via
  git checkout; confirmed clean (positive control: GraphedError count 15). Lesson: a mutation-lens crash can
  leave the editable-install source dirty — ALWAYS git status + checkout after a mutation workflow.

RE-RUN launched wo1u0hg0y: design(full, read-only) -> mutation(complete uncovered mechanisms M4/M5a-e/M6/M7/M8,
crash-hardened one-mutation-at-a-time + end clean check) -> verify. Then batch fix cycle (MED witness test +
any new confirmed) -> delta re-review if needed -> push m51-vary -> open graphed PR.

## m51 graphed review CLOSED (design+integrity+mutation clean) -> PR #7 opened (2026-09-03)
Re-run wo1u0hg0y: DESIGN cleared all 9 aspects with live probes (node-id resolution by dict.fromkeys,
superset OR 44==44, XOR true inverse, augmentation+collision, no awkward._connect, numpy exempt, §9.1
three-case, record/exec placement + .tt.ndim not _form_meta, no varied creep) — no BLOCKER/HIGH. MUTATION
kill-matrix complete: M4 collision/bare-key/naming, M5a lineage/M5b depth/M5c multiplicity, M6 numpy, M7
manifest, M8a/b/c selection ALL GUARDED (mutate->guarding test RED; baseline pos-control green before+after
reverts, tree clean). 4 raw findings, 1 refuted, 3 confirmed = 2 real gaps (2 lenses both flagged the same
structural-refusal mechanism):
- MED MUT-M5e: level>=1 STRUCTURAL mask-offsets refusal (io.py:547-553) reachable+load-bearing, NO witness.
- LOW: malformed select-key guard (_normalize_select io.py:281) no witness.
- REFUTED/LOW MUT-M5d: row-count refusal (io.py:542) — unreachable (base+masks sliced by same superset off
  same chunk => len always equal), defensive, not load-bearing. No action.
FIX (271743f, tests/extra only — frozen untouchable): test_structural_and_key_guards.py, 3 witnesses. BOTH
proven NON-VACUOUS by guard-disable mutation: structural witness -> RED "DID NOT RAISE" when :547 disabled;
malformed-key witness initially VACUOUS (downstream lineage check also raises GraphedError) -> fixed to
assert the _normalize_select-specific "bare depth" message -> RED when :281 disabled (downstream msg differs).
Each carries a positive control. All reverted, 0 leftovers. ruff check+format clean; mypy files=["python"]
so tests not type-checked (frozen fixtures same); awkward m51 frozen 37 + extra 3 + numpy m51 3 green.

CRASH RECOVERY (round 1 wnkoetmpz): mutation lens crashed leaving io.py:547 `if False and ... # MUT M5-struct`
(guard disabled) uncommitted -> reverted via git checkout, confirmed clean. Lesson: always git status+checkout
after a mutation workflow (editable-install source).

Pushed m51-vary (base main, 8 commits freeze..271743f). graphed PR #7 opened
https://github.com/graphed-org/graphed/pull/7. graphed CI = pull_request-triggered (matrix test 4os×4py +
prek ruff/format/mypy + run-tests.sh full + combined cov>=90% + rust unaffected + 3.14t). Monitor bo2f4bnu2.
BOTH PRs (fork #1 base graphed-mvp CI-green; graphed #7) await USER MERGE AUTH. No cross-repo pin (§10d:
two independent PRs, no graphed.yml repoint, no m51-new graphed symbol in the fork).

## m51 BOTH PRs CI-GREEN — at merge gate (2026-09-03)
graphed PR #7 CI: 45/45 checks SUCCESS, 0 failures (full matrix test 4os×4py + combined cov>=90% + rust +
rust-cov + 3.14t + prek ruff/format/mypy). Fork PR #1 CI green (run 33727260427). m51 COMPLETE + VALIDATED:
impl C1-C4+D1 (graphed) + R1 (fork), freeze-fixup (2 adjudicated defects, 40/40 frozen), three-lens review
closed clean, 2 witness gaps closed non-vacuously. BOTH PRs await USER MERGE AUTH (no cross-repo pin, land
graphed first per §10d for tidiness). On merge: update durable memory systematics-vary-plan.md; §12.3
bookkeeping; the arc's write-out milestone m51 is the last of m48-m51.

## fork PR #1 CI-red -> rebased fork onto latest upstream uproot + merged graphed #7 (2026-09-03)
User: "PR #1 CI-red. Fix" + "Rebase graphed-mvp on latest upstream uproot" + "rebase the PR on refreshed
graphed-mvp" + "merge graphed #7, then update fork #1 if needed".

DIAGNOSIS: fork PR #1 red was NOT m51 — it's the fork's FIRST-EVER PR, so uproot's own pull_request CI
(build-test.yml "Test build" + semantic-pr-title.yml "Lint PR") ran for the first time against a STALE fork.
graphed-mvp forked at d500682 (also the fork's main tip); upstream/main was 53 commits ahead. graphed.yml
(my integration workflow, push-triggered) was green; only the upstream pull_request matrix was red.

REBASE (backup tags backup/graphed-mvp-pre-rebase=393ecef, backup/m51-vary-pre-rebase=5b012ba):
- Added upstream remote scikit-hep/uproot5, fetched (tip 4a41da3).
- graphed-mvp = 21 linear addition commits (no merges) on d500682. Conflict surface: additions modify only
  src/uproot/{__init__,writing/__init__}.py, neither touched by upstream's 53 commits -> `git rebase --onto
  upstream/main d500682` = 21/21 CLEAN. Net additions IDENTICAL pre/post (24 files, 2360 insertions); hooks
  byte-identical; _graphed_write.py present. New graphed-mvp tip bab0388.
- m51-vary = 6 commits (f9e6333..5b012ba) on old graphed-mvp -> `git rebase --onto rebase-tmp 393ecef`; ONE
  conflict: pyproject.toml (upstream added [tool.uv], m51 8f65049 added [tool.mypy]) -> resolved KEEP BOTH,
  TOML validated. New m51-vary tip 31dfdb9. Force-pushed BOTH (--force-with-lease).
- PR #1 title fixed via REST API (gh pr edit hit Projects-classic GraphQL deprecation): "feat(m51): ROOT
  derived-column IR evaluation in graphed_write (variation-aware write-out)" (was "m51: ..." -> semantic-PR reject).
- build-test SAFETY verified: runs `pytest tests` w/o graphed; ALL collected graphed test_*.py importorskip
  BEFORE the graphed import (guard@N < import@M for all 14) -> skip cleanly, no collection error. gpu-build
  NOT in the `pass` aggregator's needs [build,vanilla-build,numpy1-build,pyodide-build] -> its perpetual
  pending (no fork GPU runners) doesn't block. Monitor ba6187av7 (excludes gpu from pending gate).

MERGE: graphed #7 (45/45 green, MERGEABLE/CLEAN) ENQUEUED to merge queue (enqueuePullRequest ->
MQE_...czgK6kV8, QUEUED position 1, enqueuer lgray). Monitor bw9ghr5mu. Once #7 lands in graphed main, fork
graphed.yml @main pulls m51 graphed; then check if fork #1 needs changes (§10d: no m51-new graphed symbol
reaches the fork, so likely none). Fork #1 still awaits its own merge auth AFTER CI green.

## PAUSE (laptop close) — RESUME STATE 2026-09-03
Server-side ops continue regardless of laptop (only local monitors die on sleep):
- graphed #7: ENQUEUED in merge queue (position 1). On resume: `gh pr view 7 --repo graphed-org/graphed
  --json state,mergeCommit` -> expect MERGED. If still QUEUED, wait; if dequeued/failed, re-check its queue CI.
- fork PR #1: CI running on rebased m51-vary (31dfdb9). On resume: `gh pr checks 1 --repo
  graphed-org/uproot5-graphed-mvp` -> expect required checks (build/vanilla/numpy1/pyodide/pass + Lint PR +
  graphed) GREEN; gpu-build stays pending (no fork GPU runners, NOT required — ignore).
LOCAL STATE (clean, pushed): graphed on m51-vary=271743f (PR #7); fork on m51-vary=31dfdb9 + graphed-mvp=bab0388
(both rebased onto upstream 4a41da3, force-pushed). Backups: backup/graphed-mvp-pre-rebase=393ecef,
backup/m51-vary-pre-rebase=5b012ba (fork repo). Temp branches rebase-tmp/m51-rebase-tmp exist (harmless).
Dead monitors to re-launch if needed: ba6187av7 (fork CI), bw9ghr5mu (#7 merge).
NEXT ON RESUME: (1) confirm #7 MERGED; (2) once merged, fork graphed.yml @main pulls m51 graphed — re-check
fork #1 CI; (3) if fork #1 needs changes (per user), make them; (4) fork #1 awaits its own merge auth after
green; (5) on full arc landing: durable memory systematics-vary-plan.md update + §12.3 bookkeeping.

## UPDATE (during pause-prep): graphed #7 MERGED
graphed PR #7 MERGED to main via merge queue, merge commit e48b70a (2026-09-03). m51 graphed work is IN main.
Remaining on resume: fork PR #1 CI result (monitor ba6187av7, still running server-side) on rebased 31dfdb9.
Fork graphed.yml @main now resolves to m51 graphed; §10d says fork needs NO m51-new graphed symbol, so fork #1
likely needs NO changes — CONFIRM by reading fork #1 CI on resume; if red for a graphed@main reason, re-run.
Fork #1 then awaits its own merge auth. NEXT: durable memory update + §12.3 bookkeeping at arc landing.

## RESOLVED before pause: fork PR #1 CI GREEN, needs NO changes
Fork PR #1 (rebased 31dfdb9): ALL required checks SUCCESS — full Test-build matrix (build/vanilla/numpy1/
pyodide across 3os×py3.10-3.14), "Check required tests" pass, "Validate PR title" pass (title fixed),
graphed workflow 3.11+3.12 pass. mergeable=MERGEABLE (status UNSTABLE only because non-required gpu-build is
QUEUED — no fork GPU runners). FAILURES: NONE. The rebase-onto-upstream + title fix FULLY fixed the red.
Fork #1 needs NO code changes (§10d: no m51-new graphed symbol reaches the fork) — confirmed empirically.
BOTH sides done: graphed #7 MERGED (e48b70a); fork #1 GREEN + MERGEABLE, awaits USER merge auth (not given
for #1 yet — only #7 was authorized). On resume: offer fork #1 merge; then arc landing (durable memory +
§12.3 bookkeeping). Nothing pending locally; safe to close.

## ARC LANDED + MERGED; §12.3 bookkeeping (2026-09-03)
User authorized merge of fork PR #1 → MERGED to graphed-mvp via --rebase (3f0b0bf ≡ 31dfdb9,
content-identical; range-diff `=`). Both PRs now landed: graphed #7 (e48b70a), fork #1 (graphed-mvp).
POST-MERGE CI TRAP: the fork `graphed` workflow (push on graphed-mvp) went RED at the diff-coverage gate
on 3f0b0bf — NOT a regression: `0/0 changed lines ... FAIL: no changed executable lines found — gate ran
against an empty diff`. Cause: once m51-vary merged, the m51 lines in _graphed_write.py ARE the
graphed-mvp baseline, so diffing the source vs origin/graphed-mvp yields an empty diff and the gate's own
empty-diff guard false-fails EVERY future push to the integration branch (7 tests still PASS). FIX
(12442fe): `if: github.ref_name != 'graphed-mvp'` on the gate step — it is a feature-branch concept;
frozen suite + mypy + full suite still guard graphed-mvp. Re-run on 12442fe: GREEN (3.11+3.12 success).
§12.3 items: (d) ops_catalog.md un-park DONE+PUSHED (corpus 9ea9f90): systematics-as-graph-axis Phase-2
row → milestone-tagged Section-C `vary`/`Varied` row (m48-m51); residue (Rust Vary NodeKey + user-declared
axes) stays flagged Phase-2; m05 test_catalog.py lock-step green 6/6. (e) durable memory updated (prev turn).
(a) R23 draft IN PROGRESS via fact-checked workflow wf8kza6zi (5 extract → 1 draft → 4 factcheck, grounded
in landed m48-m51 code, mirrors r22-draft precedent). (b)/(c) [repoint "systematics-as-a-graph-axis stays
Phase 2" mentions in graphed-root-prompt.md R22.0/R22.10 + Out-of-scope, and root CLAUDE.md Part F, at R23]
go in the R23 draft's INSERTION PLAN for the owner (R23 not yet inserted; R22 precedent = owner inserts).
DEFERRED (not user-requested): meta superproject submodule pointer bumps — superproject/consolidated-repo
relationship is non-trivial; confirm with owner before broad pointer surgery.

## §12.3 (a) R23 DRAFT DONE (2026-09-03)
r23-draft.md written (77 lines, R23.0-R23.10 + glossary + factcheck-notes), mirrors r22-draft precedent.
Produced by fact-checked workflow wf8kza6zi (10 agents, 0 err, ~1.02M tok): 5 section-readers extracted
binding outcomes w/ code anchors from landed+merged m48-m51 → 1 xhigh drafter → 4 adversarial factcheckers.
2 findings (0B/0Maj/1MINOR/1NIT), both lead-verified vs code + applied: (R23.1) tag canonicalization is
INTEGER (sign,digits,exp10) triples not Fraction (Fraction only in _tags.numeric_value / graphed.variations);
(R23.5) refuse_boundary defined in graphed/varied.py:347, called in shuffle.py. Insertion-plan anchors
verified live (R22 ends <L1284, Out-of-scope L1284, PART III GLOSSARY L1301, R22.0 L1262, R22.10 L1282,
systematics Out-of-scope bullet L1286). (b)/(c) = REPOINT the 3 "systematics-as-a-graph-axis stays Phase 2"
mentions at R23, keeping §11 residue Phase-2 (sink axis IS MVP) — left in the draft's INSERTION PLAN for the
owner (R23 not inserted; owner-inserts precedent). §12.3 COMPLETE (a done/draft, b/c owner-side, d+e done).

## SUPERPROJECT RECONCILIATION (2026-09-03, owner-authorized "full consolidation reconciliation")
The meta repo (graphed-org/graphed-project-mvp) still carried the PRE-consolidation 10-repo layout:
`graphed` submodule → dead graphed-mvp; 6 package repos (core/awkward/numpy/debug/checkpoint/preserve)
consolidated into graphed-org/graphed on 2026-07-17 were still separate submodules; state.json frozen
at the June MVP-complete state (milestones only to M38). Owner chose full reconciliation over a minimal
3-pin bump (via AskUserQuestion). Done in commit 5074106 (superproject main), PUSHED:
- Repoint `graphed` submodule graphed-mvp → graphed-org/graphed @ e48b70a (m51 #7).
- Drop the 6 consolidated -mvp package submodules (code now in `graphed`; old repos still exist → historical links valid).
- Bump live pins: graphed-histogram 32bd44b (m50 #4; working tree was pre-squash branch 430b724 → checked out squash-merged main), graphed-exec-local/graphed-executors 7ee4dac (m49 #6), graphed-corpus 9ea9f90.
- state.json: repos→5 live submodules; +milestones M39-M51 (joins/repartition/cluster R22, dask+parsl backends M42-47, systematics-vary R23); refreshed note/current_milestone=m51.
- gen_readme.py `_gh`: graphed/graphed-histogram → suffixless; graphed-exec-local→graphed-executors; historical -mvp names keep own repos.
- test_workflows.py: REPOS→5 live; Rust wheels/coverage gates retargeted graphed-core→graphed; no-publish test corrected to enforce the invariant (no PR/branch-push publish) since consolidated repos publish on version-TAG push not a `release:` event. test_all_repos.py REPOS→5.
- Regenerated README; readme-sync tests + gen_readme --check GREEN locally (19 passed).
Push also published 20 unpushed local plan commits (r28→r47 + m51 DECOMPOSE freeze; origin was stuck at r27 f85528e) — owner-authorized. Superproject CI (readme-sync) monitored on 5074106 (mon b3tvgz45t).

## Notebook systematics example + preservation.py drift fix (2026-09-03)
- Task: rerun coffea-benchmarks-graphed-mvp/graphed-adl-benchmarks.ipynb, confirm no perf regression, add a systematics example.
- PERF: no regression, faster than baseline. seq 400k 0.70s / 1.6M 2.79s (was 0.78/3.11); pools ~4.6-5.0x (hub 0.142/0.595, peer 0.153/0.592, pinned 0.151/0.594). Env: /Users/lgray/vibe-coding/graphed/.venv (editable graphed+forks); needed `uv pip install mplhep` (was missing → hist.plot1d ModuleNotFoundError).
- Example added (cells 31 md + 32 code, after Q8): JES ±5% on jet pt via `graphed.vary(g.Jet_pt,"jes",up=..,down=..)` threaded through Q4's ">=2 jets>40" SELECTION → visible band (nominal 5708 / jes_up 6198 / jes_down 5169 pass). Fill `hist.graphed` accepts the Varied mask; aggregate `EXECUTOR.run(gh.plan({...},backend="adl_graphed:make_backend")).value` → `gh.unpack(value)["q4_jes"]` = {label: bh.Histogram}; wrap hist.Hist for plot1d + ratio panel. `graphed.labels()` reports the triple on the varied ARRAY, only ('nominal',) on the staged histogram — surface it on the array.
- BUG found + fixed (pre-existing demo drift, NOT graphed core): notebook's hand-rolled preservation.py read the preserved External payload as the bare spec. Payload format is now DISCRIMINATED: `spec_json + "\x00" + "\x00".join(disc)` where disc∈{unweighted, n_weights=N, variation=<json>} (graphed/python/graphed/preserve/externals/histogram_external.py:_canonical_payload; m48-m51/M29). q5 fill is unweighted → payload = `spec\x00unweighted`. `reproduce()` (graphed's own, rebuilds FillEvaluator from node PARAMS via eval_histogram, never decodes payload) worked; the hand-rolled peer re-target `json.loads`ed the whole payload → JSONDecodeError "Extra data char 143". Fix in preservation.py: bare spec = `payload.split("\x00",1)[0]` for zero_of/FillEvaluator; externals KEY = node identity = `entry["content_hash"]` (hash of FULL payload), threaded as `_RetargetFill.chash` (was recomputed from spec → wrong key after split). Verified peer rerun==reproduce bit-for-bit on 4-worker ProcessPool (probe4). Canonical replay never decodes payload (params-based) — demo hand-roll is the only decoder, so it must split the discriminator itself.

## Systematics fanout PERFORMANCE investigation (2026-09-06; PR graphed#16 perf/systematics-fanout)
Construction (frontend) — 3 pathologies FIXED + CI guard (tests/extra/frontend/test_fanout_perf.py):
- provenance.capture() used inspect.stack() (FrameInfo+stat per frame per op) = 80-90% of fanout build → f_back walk (7159109): G=64 9.4x, G=512 4.8x.
- vary._check_unique O(registry²) → Session._points_by_point reverse index (aed961c; 6cc7802 error-parity fix, 0/1482 divergences).
- vary._source_ids re-walked the shared prefix per member → per-node memo Session._source_ids_cache (6cc7802).
- NOT changed: Varied._member_for O(G²) fallback (behind max_universes=64 guard, never engaged).
Execution (50k skim, E2E workflow, G=15→255): one pass over data (reads==partitions), reductions==3G exactly, plan nodes sub-linear, driver/worker RSS exp 0.24/0.17, unpack 0.12ms@G255. Remaining ~G^1.35 = weight-family product chain in context.py vary_context (ambient[L]=_two_level(old,L)*applied for every union label): distinct multiply ops 30/94/318/1150/4350 for N=4..64 families. O(N) prefix×suffix design exists but is NOT bit-identical (≤few ulp) AND frozen awkward/m48/test_vary_stacking.py pins the chain STRUCTURALLY (composed.node_id == (old*universe(central,L)).node_id) → §2.4 owner decision, not a same-PR fix. Bounded: quadratic in INDEPENDENT FAMILY count (100 PDF replicas as one family = O(100)); +30% at N=24, +44% at N=56.
Large scale (~/coffea-dev/coffea/Run2012B_SingleMu.root, 53.4M ev, 86 branches, 1142 baskets): explicit `Partition(uri,"Events",start,stop)` via gh.plan(partitions=...). Column projection VERIFIED: one task reads exactly the 5 Jet_* branches it touches, exact entry range, 9.1 MB/100k events. Per-partition memory (100k ev, fresh seq process): eager awkward 435MB (4.2KB/ev) / graphed nominal 414MB / jes(3 kin universes) 892MB (2.15x) / full G=15 965MB (9.6KB/ev) — no memory pathology; combinatorics dominate. TRAP: 250k chunks × 8 workers = 2.6GB each → 10GB swap, workers at 50% CPU (owner calibration: file sizes into ~500 chunks nominal ≈107k ev). At 100k chunks: G=15 0.30-0.33 Mev/s saturated (8 workers); 4M ev universe axis G=15/31/63 = 13.3/15.6/21 s (+48 universes ≈ +60%, ~40ns/ev/universe); FULL FILE G=15 = 204s/215s (535 tasks), identical results across reps, driver 151MB flat. OPEN: worker peak RSS plateaus ~2.75-3.1GB at EVERY G and partition count (vs 965MB single-partition fresh process) → profiling (graphed's own M37 StackSampler via a file Monitor + psutil RSS timeline; scratchpad/profile_run.py) in progress.
Side finding (graphed-histogram, NOT changed): plain-Array weight + ragged/option sample dies in boost ("spans must have compatible lengths") while the identical fill with a Varied weight works — the plain path records no broadcast seam, pinned by frozen m48 test_ambient_object_fills.py:145 (`plain_delta == 1`). Owner decision; a one-line fix (always broadcast) passed everything else. mypy error at boost.py:322 (Histogram Any base) is pre-existing in this venv.
Harness/tooling traps: `graphed.vary` attr shadows the submodule (use sys.modules['graphed.vary']); zsh `--include=*.py` globs fail → find|xargs (dead-instrument zeros); `gh pr edit` hits GraphQL projectCards deprecation → `gh api -X PATCH repos/.../pulls/N -F body=@file`; zsh `set -- $var` does not word-split; unvaried fills unpack to a BARE hist (no label dict).
Round-2/3 follow-through (2026-09-07): vector verifier notes closed in 24e6f08 (stale operand records dropped at the next wrap via a `wrapped` flag; `_project_one_carry` trims the shared index to `layout.length`; both mutants fail their tests; 942 passed). Upstream PRs opened: correctionlib#357, vector#741. Exec-local deadlock fix round-2 re-review REJECTED on 3 blockers (persistent-pool stale 'node'/'done' after a failed run → next run wedges, reproduced 45 s; HttpTransport.close() drops queued release POSTs 1/2 vs control 2/2; test_outbox_send_failure passes on main). Round-3 fixup (discard persistent peer state after a failed run; bounded drain in HttpTransport.close; recv-count witness) dispatched as workflow w4ro295jo. Harness made durable at graphed-workdir/perf-harness/.
Round 3 (2026-09-07): implementer closed B1 (discard persistent peer state after a failed run), B2 (bounded HttpTransport.close drain; inline HTTP release), B3 (recv-count witness); verifier REJECTED on one new blocker — `_close_peer` unbounded on KeyboardInterrupt (driver leaves `_collect_peer` without releasing; 90 s watchdog). Fixed directly: `_collect_peer` releases on every exit (try/except BaseException), test_interrupt_releases_workers (persistent × non-persistent; mutant wedges 40 s both legs, fixed 7 s). Gates green (m41 12 passed; frozen 385 passed/72 skipped minus the known m49 skew test; mypy --strict; sphinx -W). Committed c2377e8, pushed, PR graphed-executors#9 open. PR #16 body links it.
Kernel-vs-everything breakdown (2026-09-07, workflow w2eumriki, 6 agents/2 rounds): Instrument A (exact perf_counter brackets at each Python→C boundary, exclusive accounting) verified by positive controls + 2-worker reproduction. G=15/100k task, contention-free: awkward C++ kernels 36.2 %, numpy-via-awkward 19.7 %, correctionlib C++ 12.0 %, numpy-via-vector 7.7 %, uproot/boost/small 6.9 % → ≥79 % compiled; 17 % unwrapped Python frames (awkward's Python layer ~8.5 pp, numpy direct ~4.7, graphed ~1.6) — bytecode-vs-numpy inside it UNRESOLVED (both extreme claims refuted). 1.27 s/100k in-process, 2.82 s at 8 workers (2.18× inflation; kernels 26.6 % there). 79 % of kernel time = option-type bookkeeping (IndexedArray numnull/flatten_nextcarry/overlay_mask/getitem_nextcarry). vector fork −5 % task / −11.7 % kernels; correctionlib fork never entered in graphed. M37 sampler biased toward C frames at ~300 µs call durations. Harness perf-harness/kernel_breakdown.py; results in perf-harness/breakdown/results.md; memory kernel-time-breakdown.md.
CI fixes queued by user: executors#9 macOS/Windows http teardown wedge = single HTTP sender starved the live worker's `done` behind a mid-shutdown peer → per-destination lanes (07c3aa9, local starvation test discriminates; WEDGED failures now carry the child's faulthandler dump); correctionlib#357 3.14t `--iterations` failures = fixture left `_shared_structure` patched across iterations → per-call MonkeyPatch.context (606dfc8; reproduced locally with pytest-run-parallel, PYTHONPATH=src needed — the .venv-correctionlib site-packages highlevel is the stock wheel). CI watcher b7g3zlevz.
CI round 2 (2026-09-07): correctionlib#357 all 19 checks green at 606dfc8. executors#9 07c3aa9: Windows green (lane fix real); macOS still WEDGED — the new child thread dump showed the driver AND every worker parked 35 s in `socket.getfqdn('127.0.0.1')` inside `HTTPServer.server_bind` (macOS runner resolver has no answer for loopback) → `_InboxServer.server_bind` now binds via `TCPServer.server_bind` without the lookup (53ad833; witness test fails pre-fix on `getfqdn called while binding`). Lesson: the macOS frozen suite's 3× slowness on CI is likely the same stall per HttpTransport. vector#741: maintainer (henryiii) pushed 7a40b06 replacing the mechanism (index-identity grouping inside awkward_transform; stateless, −205 lines) — cold bench: indexed rows identical to mine, flat rows back to main (0.66→1.0 ms v+v); local branch fast-forwarded; no comment posted (user's call).
2026-09-07 10:07: executors#9 @ 53ad833 CI 24/24 green (macOS 9.5 min, was 15.5 — the getfqdn stall also inflated the frozen suite). All PRs green; merges await user.
PAUSE 2026-09-07 ~10:35 (laptop close): merges done (graphed#16 → ab3c640, executors#9 → 639a357 via merge queues); executors#10 (m49 re-freeze + pin) open, CI queued; two implementation lanes (histogram plain-fill seam, graphed in-process correctionlib routing) and the §2.4 plan chain in flight with no results yet — see SESSION-RESUME-STATE.md "PAUSE 2026-09-07" for resume steps and the uncommitted working trees.
RESUME 2026-09-07 (after laptop sleep): both workflows had died on stall retries (all 0-tool attempts during sleep). Histogram implementer result was cached (DEFECT CONFIRMED, FIXED; tree dirty); graphed implementer was interrupted mid-final-probes with its change complete in the tree; planner interrupted after probes (p1_count/p1c_eagerfloor/p1d_structures/proto_reassoc in scratch; proto_all==base_all byte-identical incl. m48 pin passing → prototype never engaged, VOID). Relaunched both via resumeFromRunId with RESUME NOTE addenda (graphed lane = finisher over the tree; planner = reuse probes, re-run prototype with the m48 pin as positive control). executors#10 24/24 green → enqueued (queue position 1). OWNER AUTHORIZED (2026-09-07) the m28 re-freeze of test_preservable_externals::test_apply_correction_with_a_template_records_path_free_and_obeys_it (stub evaluator no longer called on the template path) — apply after the graphed lane's review, before the PR.
FOLLOW-UP (owner, 2026-09-07): when correctionlib releases with #357 (`_shared_structure` in highlevel.py; admits ListOffset/Regular/IndexedOption — a superset of graphed's guard), delete graphed's `_flat_buffer_fast_path` + `_peel_layout/_same_layers/_rebuild` in preserve/externals/correctionlib_external.py and the `fast = ...` branch in eval_correctionlib, bump the `correctionlib>=2.6` floor (pyproject.toml, 3 places) to that release, and retarget the tests spying on `_flat_buffer_fast_path` (tests/extra/awkward/m52/test_correctionlib_layout_fast_path.py + the in-process routing witness) to `ak.transform` call count == 0. Blocked on: #357 merge (0 reviews as of today) + release > 2.9.0.
2026-09-07 CI gating: graphed#17 / executors#11 / histogram#9 add `merge_group:` + a `ci required` aggregate job; rulesets have merge_queue but NO required_status_checks (executors#10 merged 27 s after enqueue with no queue CI) — owner authorized adding required_status_checks=["ci required"] (integration 15368) after the PRs land (watcher bl2ph1omk enqueues graphed/executors when green). histogram#9 red = pre-existing m53 skew: histogram CI installs graphed@main UNPINNED; 19 frozen failures locally == CI. Owner authorized the re-freeze + pinning GRAPHED to ab3c640. CORRECTION to what I told the owner: the m52 fixture is not a keyword rename — m52's named points (third tag 'jesup_hf_up' + points={label: coords}) were REPLACED by m53's auto joint grid + placement selection (label btag_hf_up__jes_up), so the four m52 anchor files are re-authored semantically (workflow wz3jy6ggn / wf_9cb734a8-7e5 in scratch worktree wt-hist-refreeze, branch fix/m53-refreeze-points-and-joint-labels). m48/m49/m50 edits already applied by the lead in that worktree.
Follow-ups wf_95452379-9b0 finished 2 rounds each: BOTH lanes REJECT. Histogram: the form-depth rule misfires both ways (already-flat per-object weight -> hard GraphedError; numpy 2-D/1-D fill breaks; deeper-than-value factor moves the graph). Graphed: compound corrections (cset.compound) crash with raw IndexError under plugin routing; m28 re-freeze coupled the frozen test to the private _flat_buffer_fast_path spy. Lead adjudication dispatched as round 3 (wf_8dd352ba-9a1 / task wmck72q54; a mis-argued launch wf_858c82ce-df4 was stopped before any edit): histogram = fire only for 0<depth(factor)<depth(value) AND backend supplies broadcast_like; exec-time seam accepts leaf-row-space (pass-through) and outer-row-space (broadcast) factors; graphed = compound resolution + branded errors, m28 shrunk to the spy-free assertion set, spy stays in tests/extra.
Histogram m53 re-freeze APPROVED (round 2; 7 reviewer mutants of the C5 rule, admitted-member hunt empty) → committed 8e2163e on fix/m53-refreeze-points-and-joint-labels, graphed pinned at 6cc2bbe in ci.yml + docs/requirements.txt, PR graphed-histogram#10 open; watcher bcb7f8aa3 enqueues when green then rebases #9 (merge_group trigger) onto the new main. After #9 merges: add required_status_checks=["ci required"] to the histogram ruleset (owner-authorized).
histogram#10 (m53 re-freeze) merged by the owner directly (dcf7747); #9 (merge_group + 'ci required') rebased, green, enqueued, merged; histogram ruleset now carries required_status_checks=["ci required"]. ALL THREE repos gated. Live test of the queue actually building (a merge_group run) still pending — the next enqueue anywhere shows it.
SESSION SHUTDOWN 2026-09-07 evening after a major API outage killed review:graphed-r3 (twice), review:histogram-r4 and review:plan-r4. Graphed tree restored from the killed reviewer's r3rev/*.post.py backups (7 files, 227/49). Handoff written: SESSION-RESUME-STATE.md "RESUME 2026-09-07 evening" + graphed-workdir/session-12dd48ff-handoff/ (reports, scripts, probes). Numeric points= answer measured (strings only; canonical e-form).
RESUMED (new session, 2026-09-07 evening) from SESSION-RESUME-STATE.md "RESUME 2026-09-07 evening". Trees verified (graphed 7 files 227/49; histogram 3 files, boost 09a4b4d9). Relaunched the three outage-killed reviews from the handoff scripts (SCRATCH repointed to session-12dd48ff-handoff/scratch): graphed review r3 = wf_62952db4-844 (task w63eedbze), histogram review r4 = wf_0cd22e26-5bc (wje4amlbv), plan delta r4 = wf_5e41167c-86d (w5lk6fk5w). Session attribution now also requires Co-Authored-By + Claude-Session trailers on commits and the "Generated with Claude Code" footer on PRs.

### 2026-09-07 late — three verdicts, two PRs enqueued, numeric tag keys
- graphed routing lane review r3 = APPROVE (0 blocking; non-blocking: m28 now needs correctionlib at run time — CI-safe, every awkward job installs .[dev]; `_resolve` lets a plain name shadow a same-named compound). Committed 03db0bb on perf/inprocess-correctionlib-routing → PR graphed#18.
- histogram seam lane review r4 = APPROVE (0 blocking; carried: frozen coverage of `_renest` leaf branch is zero, needs a further re-freeze → next freeze). Rebased onto 9cea3e5 clean, gates green (214 passed, sphinx -W), commit 33f7e63 → PR histogram#11.
- Merge-queue lesson: `enqueuePullRequest` refuses until the PR-level `ci required` check has reported ("Required status check 'ci required' is expected") and until mergeability is computed. Watcher `scratchpad/enqueue_watch.sh` polls both PRs and enqueues on SUCCESS (self-expiring, 45 min).
- Owner asked for int/float `points=`/`collections=` keys (σ-valued variations). Measured: f-strings already worked; only `canonical_tag`'s type gate refused numbers; no frozen test pins the refusal. Change: `_tags.canonical_tag` admits `numbers.Integral` (exact) and non-Rational `numbers.Real` (shortest round-trip repr), refuses bool/Fraction/complex/non-finite; declares and coordinates share one rule. Branch feat/numeric-tag-keys (worktree scratchpad/graphed-numkeys, .so copied from m52 tree; Rust delta ab3c640..main empty). 19 extra tests; split frontend suites green.
- Found while executing that page: docs/frontend/design.rst carried 4 pre-#15 `variations=` examples that raise on the tree (sphinx never executes blocks). Rewritten to the unified grammar + fanout/placement prose; runner `scratchpad/run_rst_blocks.py` = 12/12 pass. Second commit on the same branch.
- Plan §2.4 delta review r4: 3 design findings (per-label form clash admitted by nominal-only check, rev4/r4d; running-form state unset at 4 sites, r4b; check position vs `_weight_factors.append`, r4_wf_residue). Lead decisions folded into plan §5 (per-label running form map, memoised op_form on distinct pairs, check BEFORE append = residue behaviour change stated, state follows the factor list at all 4 sites) and §9 (regenerator rev4/r4a_both_programs.py). No further planner rounds; next = C1/C2 implementation workflow on branch perf/lazy-weight-composition.
- MERGED via merge queue (first live merge_group runs, gating confirmed): graphed#18 → 4cf74ad (routing), histogram#11 → 49d8358 (seam). Histogram clone synced to main; graphed clone stays on perf/lazy-weight-composition (lane C implementer live in it).
- graphed#19 (numeric keys) CI RED: frozen `tests/frozen/awkward/m48/test_tag_grammar.py::test_malformed_and_non_string_tags_are_rejected` pins `points={0.5: ...}` raises. My local instrument walked only tests/frozen/frontend (+extra) — the tag-grammar frozen tests live under awkward/m48 (the awkward-free 3.14t split). Lesson: run the FULL scripts/run-tests.sh before any push. Owner asked for the one-leg re-freeze (float → bool as the non-tag member).
- Owner affirmed the m48 tag-grammar re-freeze (AskUserQuestion): `points={0.5: ...}` leg → `points={True: ...}`. Evidence: POST m48 awkward subtree 84 passed; mutation (bool guard removed from canonical_tag) → the leg goes red (1 failed); PRE (origin/main `_tags.py` swapped in — the first stash-based control was VOID, `_tags.py` was already committed) → leg green, numeric extra tests 12 failed / 7 refusal guards passed. Commit 0bd70fb pushed; watcher enqueue_one.sh on #19. Note: `ruff format --check` in the scratchpad worktree wants to reflow untouched lines of that frozen file at a longer line length — config resolution differs from the m52 tree; CI does not run ruff format.
- OWNER RULE (2026-09-07): commits carry ONLY `Assisted-by: ClaudeCode:<model>` — no Co-Authored-By / Claude-Session lines (GitHub renders Co-Authored-By as a second author in the commit list; that was the objection). Memory commit-attribution-trailer.md. PR #19's three commits rewritten (38f0d05, e08b1a3, 4f083bf) via `git rebase origin/main --exec strip_trailers.sh`; force-push needed a GraphQL dequeuePullRequest first (push to a queued branch is refused). Merged commits on main from earlier today keep the trailer (protected history).
- graphed#19 MERGED e80ee1a (rewritten commits, Assisted-by only). Superproject: bookkeep.py now takes `--trailer` (hard-coded Co-Authored-By removed, e356c96); pointers bumped graphed e80ee1a / histogram 49d8358 / executors b6da60d + state note m52/m53 + current m53 (91ff663); readme-sync went RED because scripts/test_workflows.py pinned graphed's pre-#8 wheels matrix (macos-latest, universal2, "3.14t" runner label) — measured: cibuildwheel builds per-arch macos-14/macos-15-intel and declares cp314t-* in [tool.cibuildwheel] build; test re-aimed at that (e6269fe + import repair cdaa185) → readme-sync GREEN. coffea-benchmarks fork: apply_correction comment updated to the plugin-owned contract (b93be8a on graphed-mvp). Open: §2.4 lane C (wf_753c85cc-207 running); correctionlib fast-path removal blocked on a release > 2.9.0 (#357 still open); vector#741 open (comment posted); histogram `_renest` frozen-coverage gap → next histogram freeze; basket-aligned partitioning Phase 2 by owner.
- Owner authorized the `_renest` re-freeze: six seam witnesses moved verbatim tests/extra/m48/test_review_witnesses.py → tests/frozen/m48/test_broadcast_seam_row_spaces.py (+6 H6 §6.3(2) README rows). Path counts over tests/frozen with r4_trace.py: renest 0→2, guard_leaf 0→2, drops_true 1→5, mixed_true 1→6; suites 214 passed unchanged. Commit c5294fc → histogram PR #12, watcher enqueues on green.

## 2026-09-08 — §2.4 lazy weight composition landed as graphed PR #20 (round 7 APPROVE)
Owner course-corrected round 6 to an epoch-stamped memo with a read-time resolution contract (plan §3/§5/§7 rewritten); round 7 closed the leak (label-path memo) and the late-clash test. Details: weight-composition-worklog.md (rounds 6–7). Numeric-key PR #19 and correctionlib #357 (now item 1 only; item 2 → scikit-hep/awkward#4326 draft) are in the same session.

## 2026-09-08 — tour capstone: JEC → JES/JER → Type-1 MET → b-tag (Level 19) + graphed#21
Physics fixes first: Level 5 now scales jet pt+mass by one JES factor (eta untouched); the Levels 15/17/18 second carrier moved from `jer`-on-`eta` to a muon scale `mus` on a new `mu_pt` collection (tour commit 33ccc20). Capstone (12 cells inserted before the closing table; closing row + map pointer added) mocks the CMS stack with correctionlib formula/category payloads: JEC one factor on pt+mass, hybrid JER (gen-match within 3σ else stored N(0,1) draw, 10 MeV floor), JES δ at the smeared pt, Type-1 MET from RAW MET over jets with nominal pt>15 & emf<0.9 (selection frozen at nominal), unclustered ±(dx,dy) on nominal-jet MET, b-tag shape SF product with `up_jes` REPLACING central inside the jes universe (BTV JSON: "not additional nuisance parameters!"), hf/lf/cferr1 one-at-a-time on nominal jets. Prescription research: scratchpad/metresearch/prescription.md (coffea master + PR#1631 (open), PocketCoffea, BTV JSON via topcoffea mirrors, columnflow, nanoAOD-tools). Mechanism map: lockstep Jet+MET `collections=`; unclustered off `graphed.nominal`; central SF over Varied jets (propagation); `up_jes` via name identity on `jes` (kind 'both'; members read at `member_of(jet, "jes_up")` so no jer joints); method sources as ratio factors on a unit nominal (ambient = PRODUCT of factors); hf over Varied jets mints hf×jer joints only (jes is a stacked weight → resolved label-aligned, not fanned); `composes_as_union=True` → 9; prune placement → 2 joints. Seven read-back checks incl. a negative control (all OK). Findings: (1) graphed bug — `graphed.weight(graphed.universe(ctx, L))` flipped from the member Array to `Varied('nominal',)` after any later mint (epoch remake wrapped the adopted bare factor); fixed by returning the sole non-Varied factor; test red on main → PR graphed#21 (918d8b6), prek ruff/mypy pass (cargo hooks: no rustup default in shell, no Rust touched), run-tests.sh 63 sections exit 0. (2) Tour Levels 6 and 17 pass the AMBIENT as a new family's nominal (`vary(btag, "mu", ambient, ...)`): measured nominal 0.25 = w² (product semantics), only labels are printed so invisible — owner decision pending (fix the idiom with a unit nominal, or make the weight form dedupe an already-registered factor). (3) The combined `pytest tests/frozen tests/extra` cannot collect (duplicate basenames) — use scripts/run-tests.sh. Notebook re-executed on the fixed tree: pre-existing cells byte-identical modulo timings; capstone outputs recorded. LANDED: graphed#21 merged 07d5172; superproject pin 4c62793 (bookkeep, pushed); tour capstone commit 109b608 pushed to graphed-mvp.

## 2026-09-08 — m54 behavior METHODS with arguments (in flight; branch m52/graphed m54/behavior-methods)
Owner's Phase-2 item (root prompt R19.1): behavior methods could not take args (`a.deltaR(b)` → 'Array' object is not callable; measured scratchpad/behmeth/probe_now.py on main 07d5172). Plan graphed-workdir/behavior-methods-plan.md (design: two optional awkward-only backend hooks `attribute_kind`/`method_outputs`; `graphed.BoundMethod` returned by `Array.__getattr__` for callable class attributes; one `method` op with JSON `args`/`kwargs` params, Array args as `{"$": i}` inputs (kwargs joined in sorted-key order), constants JSON-only, refusals before any node; tuple results one node per `index`; Varied via expand/expand_tuple; `apply` re-wraps every operand with the backend behavior — this also fixes the pre-existing M18 gap that backend-only behavior dicts resolved nothing, vector worked only via global ak.behavior). Plan review (Opus, 16 probes, review/plan-review.md): 2 BLOCKING (behavior not reaching operands → top-of-apply wrap; kwargs order changed node ids → sorted encoding) + MED (source-record methods read WHOLE source: `_evaluation_columns` short-circuits before refinement — documented, over-read only; partition-axis-consuming method bodies undetectable — stated limitation like map_partitions; callable predicate incl. partialmethod; NaN/inf refused; 0-d arrays coerced; `item`→`index`). Measured on the impl: 23/23 contract probes OK (probe_contract.py); skim: read_columns identical to the explicit-formula baseline, buffer-level need = pt/eta/phi DATA + offsets, two builds compile to equal stages, ProcessPool histogram == eager awkward+vector (24339 entries, probe_skim3.py); scripts/run-tests.sh 63 sections exit 0 with the operand wrap; sphinx -W clean (docs/awkward/{index,design}.rst updated with an executed example). Test-author (Opus, isolated worktree scratchpad/ta54-graphed from main, branch m54-tests) writing tests/frozen/awkward/m54 — pending. Next: merge tests, run, commit, ultracode review workflow (reviewers Opus xhigh, verifiers Opus high), PR, pin, R19.1 edit.
- Progress: frozen suite a3460942 (36 tests; sanity on main 34 red for the right reasons) cherry-picked onto the branch → 36/36 pass on the impl; commits bb90bfc feat / 96f5e60 docs / 611ff33 tests / 1aa052b dead re-raise dropped. Mutation probe in the author's worktree: disabling the top-of-`apply` operand wrap fails the first m54 test ('no field named scaled') → the wrap is pinned. Diff coverage of the added lines from the WHOLE frozen suite (awkward+frontend+numpy subtrees, scratchpad/behmeth/diffcov.py): 98.1 % lines / 97.8 % branches; only the `method_outputs`-missing guard is unhit. run-tests.sh exit 0 (all sections dots), prek ruff/format/mypy pass (cargo hooks = no rustup default). Review workflow wf_0f421006-483 launched (3 lenses Opus xhigh → 2 refuters Opus high each). Test author still running a second pass (uncommitted: staticmethod/cached_property classification, two-array keyword ORDER test, `index` pin dropped, vector ufuncs re-keyed onto Jet) — will re-run when it commits.

## 2026-09-08 — m55 lockstep by propagation (owner request; plan graphed-workdir/lockstep-varied-plan.md)
Owner asked whether the capstone's lockstep could use `composes_as_union` instead: no — lockstep is `collections=` (one label moving several collections, §2.6a `_check_lockstep`), union governs composition ACROSS families; two families + union would move Jet and MET in separate universes (wrong for Type-1 MET). `points=` is refused in the shift form. What shrinks the setup: the shift form accepting a `Varied` member so MET follows by propagation. Measured (scratchpad/lockstep/probe1.py over capstone/final.py with the notebook's imports as init_globals): loose `vary(jet,"jes",up=,down=)` carries tags {'jes': (up,down)}; `type1_met(raw_met, raw, v, in_type1)` propagates the same labels and its nominal interns to the context's MET node (79) for jes AND jer; hand-unpacking the containers into {tag: record} mints the same jes_up MET node (104) as the notebook's `lockstep()` → the feature is unpack + validation (one family = name, no joints, nominal node == context's). Plan review loop wf_e9a312ca-caf (reviewer Opus xhigh → fold Opus high → delta rounds until clean → whole pass). m54 still in flight: delta plan round (behmeth-plan-reviewer) + impl review wf_0f421006-483; m55 work goes in its own worktree from main (m52/graphed HEAD must stay on m54/behavior-methods while its review runs).
- Delta rounds (behmeth-plan-reviewer): r1 D1 (partialmethod/singledispatchmethod → property; fold: CLOSED property side = data descriptor or cached_property, everything else callable-or-`__get__` is a method), D2 (dict constants walked in insertion order → sorted at every level), D3 (over-read clause had no gate); r2 E1 (class constant records a field whose form holds the constant — no record-time failure; plan corrected), E2 (`read_columns` answers top-level fields → prefix containment + `columns_for` equality for the field-rooted shape); r3 ZERO → whole pass (behmeth-whole-pass, fresh Opus) running. Impl review wf_0f421006-483 (27 agents, 6 confirmed / 6 refuted): 3 classes — stale docs at 3 sites; `{"$": i}` marker forgeable by a dict constant; foreign-Session Array spliced by node id (pre-existing, binary ops too) → fixed at `Session.record_op`. All fixes in scratch worktree scratchpad/m54-fix (detached from the branch tip): a6e48ce D1/D2, 9660038 marker+session guard+docs; runner exit 0, m54 suite 43/43 (test author 0b23863), sphinx -W clean. Test author now pinning the two refusals (F1/F2) + README reason fix. Branch rebuild (feat, docs, fixes, tests, refactor) after the whole pass returns.
- Whole pass (behmeth-whole-pass): 1 design finding — `ak.Array(x.layout, behavior=...)` drops `attrs`, so a behavior member reading `self.attrs.get("calib", 1.0)` silently answered its default under a backend behavior dict (probe review/whole/w6_attrs_clean.py: 70.96 vs eager 141.91); class = 3 constructions (typetracer wrap, apply re-wrap, pre-existing with_name) → all pass `attrs=x.attrs` (11f19fc in scratchpad/m54-fix; probe now equal, 50/50 frozen). Plan §3 folded; delta round dispatched; test author pinning attrs in both shapes (F3). Frozen suite now a4be33a (50 tests; F1 marker refusal rows, F2 cross-Session method+binary legs, item-3 int/float pin, README reason dropped). Diff coverage from m54 alone 97.2 %/94.0 %.
- m54 LANDED AS PR graphed#22 (branch m54/behavior-methods 7031ba2: feat bb90bfc, docs 96f5e60, refactor d64b9f8, fixes 9716fec/cbb4593/ac7d1f4, tests 7031ba2 = test-author 047e794, 51 tests; tag freeze-m54). Whole-pass delta round ZERO. Gates on the branch: m54 51/51, run-tests.sh exit 0 (all sections dots), prek ruff/format/mypy pass, sphinx -W clean, diff coverage 97.2 %/96.0 % from the m54 suite alone. Watcher enqueue_one.sh graphed-org/graphed 22 running (log scratchpad/behmeth/enqueue22.log). After merge: superproject pin (bookkeep), root prompt R19.1 sentence retired + R23 rule, memory note, graphed-exec-local extra pool witness, remove worktrees ta54-graphed + m54-fix. Lesson recorded: worktree `git checkout <sha> -- tests/...` stages files, so later `commit -q -m` swept them into fix commits — rebuild resolved by `git rm -r` on the DU paths.
- m54 MERGED: graphed#22 → main 1598395 (13:21). Superproject 5cade03 pushed (graphed pin, current=m54, root prompt: R19.1 parenthetical retired, new §R23/R23.1). Memory behavior-methods-m54.md. Worktrees ta54-graphed + m54-fix removed, branch m54-tests deleted. Remaining m54 follow-up: graphed-exec-local tests/extra pool witness (backend-only behavior method through ProcessPoolExecutor with backend="module:factory"), based on review-impl/integrity/{behmod.py,p10_pool_witness2.py}.
- Superproject 5cade03 readme-sync green. graphed-exec-local: branch m54/pool-witness c4b7a30(amended) — tests/extra/m54 pool witness (backend-only JetArray, import-ref backend, pool == sequential == in-process exactly; default backend raises) + ci.yml GRAPHED pin ab3c640 → 1598395 (6 commits: #17-#22). Trap: a global `ak.sum` reference differs from the plan's per-partition sums in the last bit → integer-valued fixture. PR graphed-executors#12 (repo graphed-org/graphed-executors; watcher enqueue-exec12.log + CI monitor).
- m55 plan loop wf_e9a312ca-caf (11 agents, 76 min) ended NOT clean after 5 rounds: the "no silent drop" rule for containers carrying extra labels grew every round (families → labels → context-wide labels → tag subtraction → node-keyed subtraction) — apparatus. CUT: plan rewritten to the NARROW contract (r5 version kept at scratchpad/lockstep/plan-r5-final.md): a Varied member carries EXACTLY family `name` (tags == {name}, labels == nominal + name_tag), reindexed nominal == context's central node, `points=` placements refused beside a Varied member; everything else refused loudly naming `graphed.nominal(ctx["Jet"])` + the hand form. Kept from the rounds: reindex before comparing (R1-1), placement channel awareness (R1-4), `member_of(v,"nominal")` not `.nominal` (R2-3), `_check_lockstep` message widening. Next: one fresh whole-artifact review of the narrow plan (cap 2 delta rounds), then test author + impl in worktrees ta55-graphed / m55-impl.
- graphed-executors#12: rerun of the macOS py3.13 job GREEN (flake confirmed: 5/5 local, delta-free core, main green); PR CLEAN → enqueued 13:50 (MQE …LGGeY); flake note commented on the PR. Merge monitor bpest607a armed; after merge: superproject pin bump for graphed-exec-local (bookkeep --touch --commit --push).
- m54 ARC CLOSED (2026-09-08 ~14:00): graphed#22 → 1598395; graphed-executors#12 → bb5aa51 (pool witness + CI pin at 1598395); superproject 5cade03 (graphed pin, R19.1 retired, R23.1) and c620d0a (exec-local pin), readme-sync watcher on c620d0a running (readme-sync-c620d0a.log). Open from the arc: none blocking; noted for exec-local: the m37 exact-count emit test on a best-effort transport (PR #12 comment).
- m55 narrow-plan loop wf_e83ede53-b07 (7 agents, 42 min): whole pass 2 (N1-1 item 3 over-claimed "as the hand form does" at projected/record-read descendants → predicate stated, refusals delegated to §4 legs; N1-2 W5 re-aimed at systematics plan §2 overload (c)'s "each value maps tags to varied records"), delta 1 (N2-1 lineage: vary-link descendants admitted; location enumeration deleted), delta 0, whole W3-1 (stacking refusal = `check_family` "variation tag 'up' is already registered under 'jes'", not item 2 → covers-list and §4 leg re-aimed). Cap hit before a confirming round; wording folds applied by me (declaring channel incl. 2-tuples + message widening; reindex_to's own errors; snippet param `points`; determinism gate = two programs in two Sessions; wraps). Final delta round → agent m55-plan-delta (snapshot plan-n3.md).
- m55 plan CLEAN: final delta (m55-plan-delta) ZERO DESIGN FINDINGS (probe final-delta/p_stack.py: item 2 admits the stacking container; refusal is check_family's message verbatim, before any mint; reindex_to's own errors at accessors.py:220-230; _parse_points channels; snippet param). The W3 whole pass one round earlier covered the whole artifact; no further whole pass (only its fold + wording changed, both confirmed). Dispatching test author (ta55-graphed) + implementing in m55-impl.
- m55 W1+W2 DONE in m55-impl (a0f6a70): `_unpack_varied` in context.py (placement refusal → exact-family/labels refusal → reindexed-nominal node check → `{tag: member_of(v, f"{name}_{tag}")}`), normalisation loop before `_check_lockstep`, both messages widened, `collections:` annotations admit `Varied` (mapping local typed `dict[str, Any]` for mypy). Probe scratchpad/lockstep/p55.py on the capstone: container == hand nodes per label (jes, mixed, jer-on-nominal, stack `flat`), refusals for placement / declare / two-family / jer-after-jes / foreign nominal / other family / re-offered tag (`check_family` message), registry unchanged after each, masked child accepted, projected child refused by the node message. Full runner green in the worktree; ruff/mypy/sphinx -W clean. Docs example trap: the propagated MET must be computed from the RAW MET and the context's MET must be the Type-1 MET of its central jets (`EventContext(s, ev, collections=...)`), else the container's nominal is a fresh node and item 3 refuses — the example says so. W5 applied to systematics-vary-plan.md §2 (c). Awaiting m55-test-author.
- m55 frozen suite landed: test author commit 6cab5f5 (19 tests, 6 files + fixtures + README; sanity 17 fail on pre-m55 with the lockstep message, 2 declared controls pass) cherry-picked as b6d49d4 on m55/lockstep-varied, tag freeze-m55. Gates: frozen 19/19 first run; diff coverage from the frozen suite alone 19/19 lines + 10/10 branches (generic script scratchpad/lockstep/diffcov.py — the m54 diffcov.py hardcoded its file list); ruff/format clean on tests; mypy on tests reports `Session(AwkwardBackend())` arg-type — same error ×5 in frozen m54 under the same invocation, pre-existing tests-not-typechecked debt, not m55's. Impl review wf_ab7b1e07-439 launched (4 lenses Opus xhigh + 2 refuters/finding Opus high; mutation lens works on a copy under scratchpad/lockstep/review-mutation).
- m55 impl review wf_ab7b1e07-439 (18 agents, 17 min): standing MUT-1 (`**tags` spelling unguarded), MUT-2 (later-collection refusal leaks `_shift_after_weight`; the frozen `refused()` sees only the point registry, which vary's rollback restores) — measured PRE-EXISTING on the hand form (scratchpad/lockstep/leak.py: form-mismatch and non-array members leak `('sf','Jet')`); RULES-1 (root prompt: three unqualified "systematics-as-a-graph-axis stays Phase 2" statements vs R23.2, and no rule section for the m48–m53 arc at all — the systematics plan §"Scope deviation" promised an R23 entry that m54 took). Refuted: INT-1, MUT-3, RULES-2 (wording folded), RULES-3 (folded by the R24 move). Fold commit on m55/lockstep-varied: rollback snapshots/restores `_shift_after_weight` + `_weight_factors`; tests/extra/awkward/m55/test_review_folds.py (5 tests; the rollback witness fails pre-fix, passes post-fix); pyproject pythonpath += tests/frozen/awkward/m55; orphan tests/extra/m53 (not in SUITES, never ran) → tests/extra/frontend/m53; .graphed/m55 + retro m54 attempts.md (INT-2 class). mypy on tests: only the pre-existing `Session(AwkwardBackend())` arg-type in the fixtures.
- m55 PR graphed#23 opened (branch m55/lockstep-varied: a0f6a70 impl+docs, b6d49d4 frozen, 34c7610 fold; full runner exit 0 on the fold). Root prompt: R23.2 draft lifted into a new "## R24 — Systematic variations as a graph axis (m48–m55)" (R24.1 binding pointer to systematics-vary-plan.md — the arc had NO rule section; R24.2 = m55 with the RULES-2 wording fix); the three "systematics-as-a-graph-axis stays Phase 2" statements (R22.0, R22.10, Out-of-scope) qualified "since pulled into the MVP — R24". Enqueue watcher + merge poll launched; after merge: bookkeep --set-current m55, pull m52/graphed, tour notebook W4 (final55.py → final.py, assemble, execute, push graphed-mvp), memory, worktree cleanup.
- m55 LANDED 2026-09-08: graphed#23 merged bfbb9a9 (enqueue watcher → merge queue; CI green); m52/graphed main fast-forwarded; superproject ca66da4 (bookkeep --set-current m55; graphed pin bfbb9a9; root prompt R24 + Phase-2 qualifiers; plan + journal + systematics plan §2(c)) pushed, readme-sync watched; tour capstone rewritten (update55.py replaced md cell 45 + code cell 46; run_nb2.py EXECUTED_OK; cmp_outputs: 0/26 code cells differ) → graphed-mvp 84781f7 pushed over SSH; worktrees ta55-graphed/m55-impl + branches m55-tests/m55/lockstep-varied removed (remote branch left, as m54's was); memory lockstep-varied-m55.md. Open owner items unchanged: tour Levels 6/17 ambient-as-nominal idiom; `_points.coordinate()` numpy scalars; exec-local m37 exact-count emit test; tests not type-checked in CI (`Session(AwkwardBackend())` arg-type).
- m56 (owner: "Fix it" — hf×jes joints missing when jes is both shift and weight): gap measured (capstone order 4 joints vs reversed 8; scratchpad/m56/cases.py A–F). Prototype in scratchpad/m56-impl (diff m56/prototype.diff): AmbientCarrier.members (per-label factor member nodes) + `_reads_ambient` cone test replaces the kind-based `nuisances & composed`; cases: B fans out, C/D/E/F unchanged; capstone 8 joints in both orders, joint weight = SF(up_jes)×ratio(up_hf) on jes_up jets by value. Full runner on the prototype: ONE frozen failure, m48 test_vary_stacking::test_a_factor_read_at_the_parent_… — measured a pre-existing lineage inconsistency (parent mints sf×jes joints, masked child does not because the adopted composed container's `_tags` carries the leaked shift); prototype child joint has 23 rows == mask rows at jes_up (correct row space); the test maps joint labels to nominal rows. DISPUTE filed (.graphed/m56/disputes/, awaiting owner affirmation). Plan both-kind-fanout-plan.md written; worktrees ta56-graphed (m56-tests) + m56-impl (m56/both-kind-fanout) from bfbb9a9. Next: plan review workflow → test author → implement → gates → impl review → PR (held on the dispute).
- m56: OWNER AUTHORIZED the m48 re-freeze (test_vary_stacking::test_a_factor_read_at_the_parent_…: joint labels resolve their row space through the registered point). Applied + committed on m56/both-kind-fanout (frozen m48 green on the prototype); dispute file carries the resolution. Plan review wf_34eefe68-f89 running.
- m56 plan review r1 wf_34eefe68-f89 (45 agents, 40 min): BLOCKERS RS2 (targets keyed by literal member keys — joint labels had no targets → ambient-derived members leaked joints; measured p7/p8) and CC1+RS3 (mask-derived context adopts ONE composed factor → a member computed from the parent's ambient fanned out); LOW CC6 (determinism leg unfalsifiable). Refuted: RS1/RS4/RS5/RS6, CC2/CC3/CC4/CC5/CC7, FS1–FS8. Prototype v2: AmbientCarrier.resolve(label) = two-level point-restricted read of every LINEAGE factor (`_lineage_factors`); `_member_nodes` shared from vary.py. v2 closes p7 (no joints), p8 (jer joints only), derived_ambient/derived_ratio/leaked_shift (as main); B + capstone still 8 joints both orders. Plan r1 folds items 1/4, §3, §4 legs (joint-label + mask-derived legs; determinism leg dropped). Delta review wf_e94b139b-f7b launched.

## 2026-09-08 — kinds: `graphed.Kind` flag replaces the "weight"/"shift"/"both" strings (owner request, no workflow; branch m52 scratchpad/kinds-impl kinds/enum)
Owner: "make it based on unions … enums or classes rather than strings"; assessment delivered, then "Go ahead … it doesn't need a workflow since it's just a substitution. Re-freeze tests as needed and submit the PR." Measured before cutting: the kind string was derived-only (no consumer in graphed, executors, histogram, or the tour beyond prints), and the derivation had two defects at a masked child because it read the ambient container's `_tags`, which `_adopt_ambient` widens with the mask's shift families (scratchpad/m56/kinds_probe.py: parent jes=shift, child jes=both; scratchpad/m56/nameid_child.py: name identity on jes ACCEPTED at the parent, REFUSED at the child with "tag 'up' is already registered under 'jes'").
- Design: `python/graphed/_kinds.py` `Kind(enum.Flag)` {WEIGHT, SHIFT}, repr `Kind.WEIGHT|SHIFT`; `EventContext._weight_tags: dict[name, tags]` = the lineage's registration record (copied parent→child in `__init__`, written by `_vary_weight`, `inherited` reads it, DROPPED in `_project` since §2.2 projection drops the registry — caught by extra test `test_variations_answers_an_empty_registry_on_a_projected_context`); `variations()` = record (WEIGHT) ∪ collections' `_tags` (SHIFT). Both child defects close as a consequence (probes on the kinds tree: child == parent; name identity accepted at the child).
- Re-frozen (owner-affirmed "as needed"): frozen frontend/m52 test_variations_kind.py, preserve/m50 test_context_variations.py; extra test_weight_composition.py, m48/test_numeric_tag_keys.py — pure `"x"` → `Kind.X` substitution (script; 4 files). New tests/extra/frontend/kinds/test_kind_record.py (union semantics; masked child reports the parent's kinds; name identity accepted at parent AND child) — ImportError on main (no `Kind`), and the two behavioural legs are the measured main defects above. Docs: design.rst prints re-executed (scratchpad/kinds/design-ex.py extracts the block verbatim), kind paragraph rewritten around `Kind` + the record; api.rst prose; Sphinx -W exit 0. Plan §9.1 test sentence + root prompt R24.3 written.
- kinds: PR graphed#24 ENQUEUED 17:41 (MQE …LGGeY-class id in scratchpad/kinds/enqueue-24.log); monitor armed. Tour e466b4a committed locally (8/26 code cells differ only by the kind repr), push after merge.
- m56 delta review r2 wf_e94b139b-f7b (10 agents, 26 min): STANDING rs-r2-1 BLOCKER (1 refuter for, 1 against) + CD1 MED (both refuters against): the r1 target set was EVERY lineage factor's member at L, so a factor label-invariant at L — the bare seed weight `EventContext(weight=genWeight)`, an unrelated pu family's central — put its node in the member's cone and the both-kind joints vanished (q2 hfB, contract-r2/g_unrelated_factor hf_pu, refuter's seed cut `ctx[genWeight>0]`); rs-r2-2 (item-4 parenthesis self-contradictory) REFUTED (single program satisfies both clauses; deciding variable = the factor's input cone, not family kinds); nits CD3 (guard bounds, does not count) + CD4 (cone per member NODE). FOLD → prototype v3 (resolve = per factor, nodes at L MINUS nodes at nominal; measured scratchpad/m56/v3-battery.log: q2/g_unrelated/seedcut/r1_gwcut now mint the 4 joints, cases A–F, p7/p8, derived_*, leaked_shift, m48probe, capstone 8 joints unchanged from v2; `weight(ctx)>0` mask stays conservative = decided scope sentence) + plan r2 (§2 item 1 "varied member at L", boolean-read scope; item 4 inclusion class; §3 resolve; §4 three inclusion legs + guard sentence + cost per node). Full runner on v3 exit 0 (65 sections). Round 3 delta review (r1→r2) launching.
- kinds LANDED 2026-09-08 18:05: graphed#24 merged cccff9b (merge queue); m52/graphed main fast-forwarded; tour e466b4a pushed; worktree kinds-impl + branch removed; superproject pin bump below. m56 round-3 review wf_f9fe71a5-cf4 survived the laptop pause (11 agents started, none finished at 19:27).
- m56 delta review r3 (r1→r2) wf_f9fe71a5-cf4 (12 agents, 125 min incl. the laptop pause): ZERO standing design findings. Refuted: rs-r3-1 MED (node identity narrowing lets an identity leg `up=central` fan an ambient-derived member out — conceded no-op class, no admitted identity leg in tests/docs/tour, key-based alternative mis-decides the m56 class), rs-r3-2 LOW + cc-r3-1 MED (item 1's "(nothing registered, or only shift coordinates on L)" parenthetical inaccurate — prose), cc-r3-2 MED (second inclusion leg's spelling), cc-r3-3 LOW (seed-weight leg is the squaring idiom — labels only). Nits folded into plan r3: parenthetical deleted; case C qualified "where the member at the label is not its nominal node" + identity-leg concession; item 5 guard "bound accounts for"; inclusion legs assert LABELS, central member "computed from the unshifted objects"; prototype resolve field comment. Boolean-read scope sentence verified by the reviewer's live scan (corpus 28 / tests 395 / docs 100 / benchmarks 48 files, positive control fires). WHOLE-ARTIFACT PASS launched wf_3852cdfb-cee (composition / frozen / code lenses + refuters).
- m56 WHOLE-ARTIFACT PASS wf_3852cdfb-cee (27 agents, 34 min): ONE standing MED (split vote) M56-ONEATATIME-SPELLING — §4's "X_u weight is the name-identity factor" holds only for a unit-central second family (m53's fixture idiom has `central = pt*1.0`) → restated to the item-3 property (the two-level product at the point, unchanged from pre-m56). Refuted (with wording residues folded): CW1 (gloss vs central-on-varied-objects factor — that factor HAS a coordinate under the rule), CW2/FS-1 (order independence exact only for a two-factor ambient — item 2 now says so; the leg uses two factors), CW3/DEAD-GUARD (`ambient is None` unreachable → parameter non-optional), FS-2 (item-4 parenthesis names its fixture: second family shift AND weight), FS-3 (oracle = factors in registration order), FS-4 (mask leg builds the member at the parent), FS-5 (union leg beside the unflagged registration), FS-6 (shift-only family on the nominal jets), W5-TARGETS (R24.4; the m53 "GENUINELY CONSUMES" clause), DOCS-JOINT-COUNT (decided: docs example = one both-kind nuisance, four joints). Nits CW4/CW5/CW6/FS-7/COMPOSED-SOURCE folded (item 1 says `composed` stays the ambient tag map, NOT `_weight_tags`). Plan r4 = exit. Test author dispatched (Agent m56-test-author, Opus high, ta56-graphed on cccff9b). m56-impl rebased onto cccff9b clean (re-freeze now 452a24a); W1 finishing.
- m56 W1+W2 COMMITTED d9d256b on m56/both-kind-fanout (rebased: cccff9b → 452a24a re-freeze → d9d256b): v3 rule + ambient non-optional at the composed call site (assert narrowing, no dead branch) + docs example (4 joints; prints Kind.WEIGHT|SHIFT) + dispute file. Full runner exit 0 (65 sections, scratchpad/m56/runtests-v3r.log); Sphinx -W exit 0; battery identical to v3 modulo kind repr (v3r-battery.log). Awaiting the test author.
- m56 W5 WRITTEN (uncommitted in graphed-workdir): systematics plan m53 "GENUINELY CONSUMES" clause gains the node test + composition exclusion; root prompt R24.4 (node rule, `composed` stays the ambient tag map, decided scopes, m48 re-freeze). W4 in progress: tour md cell 49 rewritten (union of hf×jes and hf×jer, dataflow decides), cell 50 gains the jes-joint two-level weight + MET checks, cell 52's placement keeps a cross-kind joint; re-executing against m56-impl d9d256b (baseline scratchpad/m56/tour-baseline.ipynb).
- m56 FROZEN: test author (Agent m56-test-author, Opus high) committed 50050b7 on m56-tests — 14 tests / 6 files + m56_fanout_fixtures.py + README; pre-m56 sanity 13 FAIL for the right reasons (missing joints / label sets / oracle / PointError / guard DID NOT RAISE) + 1 declared control PASS; determinism byte-identical; ruff clean (frozen/** excluded from the formatter → checked on a copy). Author decisions: mixed-member leg under two both-kind families asserts empty (no non-composed family) with the bare sibling live; pure-weight leg's pu members independent of the shift. Cherry-picked as 9961f24 on m56/both-kind-fanout, tag freeze-m56; on the implementation 14/14 PASS first run; frozen-suite diff coverage vs cccff9b 33/33 lines, 14/14 branches. W4 tour committed locally 3917bd4 (17 universes, 8 joints, checks all OK, only the grid/placement cells' outputs differ). Impl review launching.
- m56 IMPL REVIEW wf_53f49564-e83 (17 agents, 32 min): design REJECT / integrity APPROVE / mutation APPROVE. STANDING: F1 MED (split vote) + m56-MUT-7 MED (2/2 stand) — same class: two precision mutations survive every frozen suite (401 tests): site A `member._members[label]` → `member` (judge every universe, not the one at L) and site B `_two_level` → `member_of` in resolve (one-level read); non-equivalent on exotic programs (a member whose nominal universe reads the factor's varied member; a member reading a factor's member from another universe); the branch's answers are the plan's. → test author asked for an additive fixup (two frozen legs; precedent freeze-m47-fixup). Refuted: F2 (eager `_lineage_factors` walk cost — number did not reproduce), F3/M56-INT-1 (attempts.md untracked — committed anyway), M56-TST-2 (central-product leg passes under the r1 rule — seed/cut legs kill it), MUT-9 (nested `_member_nodes` recursion unexercised — pre-existing helper). Nits folded: the comment above `composed = frozenset(ambient_tags)` now states the candidate-set + node-test rule (F4/NIT-1); §3 sentence aligned with the Optional+assert (DES-3); attempts.md section count (DOC-4). Gates re-measured by the reviewers: diff coverage 33/33 + 14/14, ruff/mypy clean, determinism, Sphinx, item 2 six orders identical labels / 1 ulp, eight pre-m56 programs byte-identical main vs branch.
- m56 fixup 1 (test author ac91f6d → cherry-picked 28e8461): 3 precision legs, 17 tests. Mutation re-check (scratchpad/m56/mutcheck.sh, detached worktree, applied-check via git diff --stat): site A (judge every universe) now KILLED by test_label_precision::…other_universe…; site B label-side (`_two_level(factor, label)` → `member_of`) still SURVIVES 17/17 — first harness run was a DEAD instrument (ruff had reflowed the line, replace matched nothing; fixed with an assert on the count and a diff-stat print); the both-sides variant IS killed by the new two-level leg. Measured why (scratchpad/m56/siteB_probe.py): a weight member computed over the jes-varied jets is itself a container, `member_of(factor, "jes_up")` yields all its universes (33,34,35) where `_two_level` yields (34,), so the label-side mutant composes a probe that reads the up member's jes_DOWN universe node (reviewer's p8: 4 → 2 joints). The fixup's cross-universe leg read the other TAG's member (never a target) → asked the test author for fixup 2: the probe reads `member_of(up_member, "jes_down")`.
- m56 fixup 2 (test author 3848d37 → 55de38b): nested-projection leg; 18 tests, 18/18 on the implementation; mutation re-check: site A KILLED (test_label_precision::…other_universe…), site B KILLED (test_nested_projection::…), control killed → F1 + MUT-7 CLOSED IN CODE. Tags freeze-m56 (9961f24) + freeze-m56-fixup (55de38b) pushed with the branch. Full runner on 55de38b launched; PR next.
- m56 PR graphed#25 OPENED (branch tip 55de38b; final runner exit 0, 66 sections, scratchpad/m56/runtests-final.log). Enqueue watcher scratchpad/m56/enqueue-25.log; monitor armed.
- m56 LANDED 2026-09-09 04:51: graphed#25 merged 3b00157 (merge queue, CI green); m52/graphed main fast-forwarded; tour 3917bd4 pushed (fork graphed-mvp); worktrees m56-impl + ta56-graphed and branches removed (remote branch + tags left in place). Superproject pin bump (--set-current m56) below.
