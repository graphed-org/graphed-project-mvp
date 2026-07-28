# systematics-vary-plan.md — pre-delivery hygiene review (r0, 2026-07-28)

Workflow wf_5f787a93-9a4: facts=sonnet-high, design=inherit-xhigh, tests=opus-high, process=sonnet-high.


---

# [facts lens]

# FACTS Lens — Anchor Verification: `systematics-vary-plan.md` (r0)

Every `file:line` anchor in the plan body and Anchors appendix was opened at the cited path/line in the ground-truth clones (`graphed-latest`, `graphed-exec-check`, `graphed-histogram-latest`, `graphed-corpus`) or in `graphed-root-prompt.md`. Six-plus claims attributed to cba/lit were checked word-for-word against those docs. Results below, most severe first.

---

**[HIGH]** §10 (m48 milestone target) — arithmetic error in the stated reference count: the milestone claims its weight-path target set is "= 10 of the 15 refs," but it is 9.
Evidence: the plan's own enumeration is "ttbar 4j1b/4j2b × {nominal, btag_up, btag_down} + ttgamma {nominal, pho_up, pho_down}" = (2 regions × 3) + 3 = **9**, not 10. Verified against the actual fixture set (`graphed-corpus/src/graphed_corpus/analyses/systematics.py:107-112`, `TTBAR_FIXTURES` = 2×5, `TTGAMMA_FIXTURES` = 5, 15 total, confirmed by `ls corpus/references/*.json` = 15 non-ADL files) and against the codebase-analysis doc's own count (cba §corpus §1: "`TTBAR_FIXTURES` = 2 regions × {nominal, jes_up, jes_down, btag_up, btag_down} = 10; `TTGAMMA_FIXTURES` = ... = 5"). This is a binding milestone acceptance-anchor count a test-author will use to build the frozen m48 suite; the miscount should be fixed to 9 (or the enumerated set corrected) before freeze.

**[MID]** Part I §4 and §5.4 — drifted line number: `shuffle.py:233` does not show the "first Join" logic the text cites it for; the actual evidence is one line above, at `shuffle.py:232`.
Evidence: opened `graphed-latest/python/graphed/shuffle.py:225-239` directly. Line 232 is `join_params = dict(next(n for n in store.nodes() if n["kind"] == "join")["params"])` — the `next(...)` call that silently picks only the first `Join` node (the fact actually being cited). Line 233 is `how = str(join_params.get("how", "inner"))`, unrelated to boundary selection. This drift is not local to the plan — it was inherited from `systematics-vary-codebase-analysis.md` §frontend-python §4 ("`join_plan` takes the **first** join node (`shuffle.py:233`)"), which has the same off-by-one. The companion citation `shuffle.py:170` (for `shuffle_plan`'s `exchanges[0]`) is correct as written.

**[LOW]** Scope-deviation section / §12.3(b) — `graphed-root-prompt.md:1284` is cited as showing the Out-of-scope block's "systematics-as-a-graph-axis" line, but line 1284 is only the block's section header; the actual bullet naming it is line 1286.
Evidence: `graphed-root-prompt.md:1284` = `"## Out of scope (later phases — MUST NOT be built initially)"`; the line reading `"treating systematic variations as a graph axis;"` is at line 1286. Lines 1262 and 1282 (the R22.0/R22.10 inline citations) are exact verbatim matches, so this is a minor, isolated imprecision — pointing at "the block" rather than the specific item.

**[LOW]** §5.1 — the factual claim "the corpus and AGC fixtures both apply JES at `Jet.pt` pre-cut" is asserted without an inline anchor at the point of use (PART II is meant to be self-anchored).
Evidence (the claim is true, just not cited in place): `graphed-corpus/src/graphed_corpus/analyses/systematics.py:60` (`jets = _apply_jes(...)` before the `pt>25` cut at :61) and `tests/frozen/preserve/m9/agc.py:106` (`spt = ev.Jet.pt * jes` before `jetmask = spt > 25.0` at :107). The supporting anchors exist elsewhere in the doc (Part I, Anchors appendix) but aren't repeated at this specific PART II assertion.

**[NIT]** Part I §1 — the quoted fragment from `graphed-root-prompt.md:25` ("On real analyses with many systematic variations the graph reaches tens of thousands") truncates the sentence without an ellipsis; the source continues "...to hundreds of thousands of nodes." Meaning is unchanged, purely a quoting-hygiene nit.

**[NIT]** Anchors appendix — `src/node.rs:39-41` (cited for "identical key ⇒ same NodeId") is an indirect anchor: those lines are the `NodeKey` enum's doc-comment + `#[derive(... Eq, Hash)]`, i.e. the *precondition* for interning, not the dedup lookup itself (which is correctly co-cited at `src/store.rs:73-88`, the actual `HashMap::get` short-circuit). Not wrong, just one step removed from the claim it anchors.

---

### What held up clean (no defects found)
Every other anchor checked — `src/node.rs:102-103`, `src/optimizer/engine.rs:7-13,54-56`, `src/store.rs:73-88`, `tests/frozen/core/m4/test_systematics.py` and `test_benchmark.py:10,40-53`, `tests/frozen/corpus/m05/test_systematics.py:26-38`, `tests/frozen/preserve/m9/agc.py:38-66,56-62,94-118`, `execution.py:276-284`, `shuffle.py:92-96,5-8,170`, `plan.py:164-176,286-301`, `aggregate.py:101`, `provenance.py:66-79`, `projection.py:109-147`, `debug/errors.py:29-81`, `execute.py:99-126`, `checkpoint/store.py:31-41,62-73`, `checkpoint/runner.py:100-109`, `graphed_histogram/boost.py:100-117,100-122,166-174,205-206`, `_spec.py:70,74`, `tests/frozen/m23/test_group_plan.py:68-77`, `tests/frozen/m29/test_multi_weight_fills.py:82-99`, `ops_catalog.md:75` (verbatim quote), `root-prompt.md:1262,1282` (verbatim), and `graphed-corpus/src/graphed_corpus/analyses/systematics.py:25-112` — all resolve to the exact content the plan attributes to them, at the exact lines cited. The 15-corpus-reference-JSON count, the R-rule references (R0.4/R0.4a/R0.5/R0.10/R0.10a/R0.11/R17.0), and root `CLAUDE.md`'s "Part F" label all check out against the live files. Six-plus cba/lit attributions spot-checked word-for-word (the "R is opaque end-to-end" quote, the "23 JSON files / 10 ttbar + 5 ttgamma" count, the "no IR construct expresses 'N variations of one graph'" near-verbatim lift, the N=1→2 delta=D+2 / 12.9×→11.9× scaling numbers, the whole-IR `task_id` fold, and the shift×weight no-cross-product convention against boostedhiggs) all matched their source docs exactly.

---

**Verdict:** No BLOCKER-level factual or anchor defects; one HIGH (a genuine 9-vs-10 count error in a binding milestone target) and one MID (an inherited off-by-one line citation used twice) should be fixed before freeze, plus three low-stakes precision nits — the plan's factual scaffolding is otherwise solid and its anchors overwhelmingly check out verbatim.

---

# [design lens]

# Design-lens review — systematics-vary-plan.md r0

## Findings (most severe first)

**[BLOCKER] §2.4 (+§6.1) — The combination rule is wrong/ambiguous for the dominant case: two `Varied` inputs sharing labels (including a `Varied` meeting itself), which is the first thing every shift analysis does.**
§2.4 binds: *"When an operation combines two `Varied` inputs, the result's labels are the union; for each label the other container contributes its `"nominal"` member."* Applied literally to the corpus fixture's first selection step — `good = jets[jets.pt > 25]` (`graphed-corpus/src/graphed_corpus/analyses/systematics.py:61`), where `jets` is the shift `Varied` and the mask is a `Varied` derived from it with identical labels — "the other container" is ill-defined (both carry `jes_up`), and the rule as written yields `jets[jes_up]` sliced by the *nominal* mask (or vice versa): wrong physics either way. The same defect recurs at the fill: the corpus `jes_up` reference weights with the central b-tag SF evaluated **on the shifted selected jets** (`weight = _btag_weight(sel_jets, variation="jes_up")` → central branch, `systematics.py:74-76,31-36`), while §2.4's own sentence *"shift labels fill with nominal weights"* prescribes the nominal-jet weight — so the m49 anchor "full 15-reference matrix bit-for-bit" is unreachable under the rule as written. It also contradicts the plan's cited precedent: the litsearch records RDF's universe model as whole-cone substitution — "for each variation, substitute the varied column node(s) and rebuild only the downstream cone" (lit §rdf-vary, lines 55-59, 89), i.e. all uses of a varied quantity are coherent within a universe. The plan must bind: labels present in both containers align member-to-member; only absent labels take the other side's nominal. Nothing in r0 says this.

**[BLOCKER] §2.1 + §2.4 + §4.1 — Stacked variations (a weight variation on top of a shift-propagated weight) are inexpressible, and both corpus analyses require them on one output.**
`vary(nominal: Array, variations: Mapping[str, Array], *, name)` (§2.1) accepts only plain Arrays. In the corpus, the b-tag weight is computed from the **jes-Varied** selected jets (`systematics.py:76`), so the central weight is itself a `Varied`; adding btag labels on top requires `vary()` on a `Varied` nominal — a type error under §2.1. The escape routes fail: (a) a separate `btag = vary(w.nominal, {...})` container combined at the fill gives `jes_up` the *nominal-length* btag factor while `ht[jes_up]` and `w[jes_up]` have the **shifted selection's length** (cutflow divergence is §5.1's own defining behavior) — a runtime length mismatch, not a fill; (b) a ratio-factor `Varied` in `weight=[...]` (§4.2) hits the identical per-label length mismatch. ttgamma has the same wall (`pho_up/down` weight built from a jes-Varied selection, `systematics.py:91-99`; TTGAMMA_FIXTURES spans jes and pho labels, `:112`). m49's flagship anchor needs jes⊗btag and jes⊗pho on single outputs; the plan provides no mechanism (vary-on-Varied, label-extension, or bound equivalent).

**[HIGH] §1.2 vs §6.2 — Direct internal contradiction on label identity.**
§1.2: a label *"MUST NOT enter NodeKey params, tokens, or content hashes."* §6.2: in variation-axis mode *"labels ride params"* — and External fill-node identity **is** descriptor+inputs+params (`graphed-histogram src/graphed_histogram/boost.py:196-211`; spec/`content_hash` at `:188-195`), and StrCategory bin labels necessarily enter the canonical spec hash. The plan's own evidence doc demands the opposite of §1.2 for this mode ("The variation labels must enter the content hash", cba §histogram, design implications). In axis mode renaming a systematic *genuinely* changes the output (bin labels), so §1.2's blanket ban is overbroad; it must be scoped to sibling-fill lowering, or §6.2 violates a MUST.

**[HIGH] §2.3(b) — "ONE uniform wrapper … applied mechanically to the module, no per-function code" is falsified by the measured gak surface.**
`python/graphed/awkward/functions.py` contains: `join` (:18 — must **refuse** per §5.4, not broadcast per-label, which would also multiply Join boundaries past the first-join-only builder, `shuffle.py:233`); `unzip`/`broadcast_arrays` (:687,:677 — return `tuple[Array, ...]`, so per-label mapping yields a Varied-of-tuples, violating §2.2's `{label: Array}`); eager/metadata functions `fields`/`type_of`/`backend_of`/`to_list`/`head`/`sample` (:717-737 — return `list[str]`/`str`/`object`); and `zip`/`concatenate` (:118,:383 — take a Mapping/Sequence, so a `Varied` *inside* the container is invisible to an "receives ≥1 Varied argument" check). A bound exclusion/containment/traversal spec (i.e. per-function classification) is required; the plan currently forbids exactly that. Relatedly, module verbs (`graphed.join`/`repartition`) are a needed fourth dispatch point for §5.4's "clear NotImplementedError," but §2.3 enumerates only three.

**[HIGH] §2.3(a) — plain-`Array[Varied]` indexing is uncovered and the corpus requires it.**
ttgamma slices **unvaried** collections with a jes-Varied mask: `photons[sel]`, `muons[sel]` pattern (`systematics.py:91-92` — `sel` depends on `_apply_jes` jets). §2.3(a) only makes `Varied` implement the dunders; `__getitem__` has no reflected protocol, and `Array.__getitem__` raises `TypeError("unsupported index …")` on a non-Array key (`graphed-latest python/graphed/array.py:344-372`); `Array.filter(mask)` likewise feeds a `Varied` straight into `record_op` (`array.py:374-375`). Either `Array.__getitem__`/`filter` learn `Varied` (inverting the stated dependency direction) or the plan must say how this corpus line runs.

**[HIGH] §8.2 vs §1.2 + §7.2 — the labeled StageError has no possible transport for the label under the plan's own constraints.**
`StageError` is built worker-side from `(op, frames, input_forms, partition, …)` with no node id (`python/graphed/debug/errors.py:33-49`; `_stage_error`, `debug/runner.py:34-45`; executor translation `graphed-exec-check src/graphed_executors/submit/engine.py:381-392`). Under §2.3 broadcast, all N per-label siblings record at the **same user line** (§8.3 confirms), so op+frames cannot disambiguate `jes_up` from `jes_down`. The node-id→label map is frontend-only state; §1.2 bans labels from IR/params and §7.2 freezes `ExecResult`/`Plan`/monitor schemas — closing every channel by which a worker (or the executor-side translator) could learn the label. §8.2's frozen cross-process test is unimplementable as constrained; the plan must name the mechanism (e.g. driver-side re-annotation keyed on a StageError-carried node id, which itself is a schema change).

**[MID] §2.2 — `Varied.map` collides with `Array.map` under an incompatible contract, and a `Varied` captured inside `.map` of another `Varied` is undefined.**
`Array.map(fn)` records an External whose `fn` is an **execution-time data→data** callable (`array.py:377-379`); §2.2's `Varied.map(fn)` applies a **record-time Array→Array** function per universe — same name, different `fn` type, silent misuse hazard. And if `fn` closes over a second `Varied`, broadcast fires inside `fn`, `fn` returns a `Varied`, and `.map` produces nested `Varied`s that §2.4's one-at-a-time rule never addresses.

**[MID] §3.4 — the impact-set mechanism ("Session id watermark before/after expansion") doesn't fit the plan's own expansion model.**
Under §2.3 there is no "expansion" window: per-label nodes accrue interleaved, one broadcast step at a time, across the whole user program (each dunder/gak call appends one node per label). A before/after watermark around `vary()` brackets nothing, and a node shared by `jes_up` and `jes_down` but not nominal (§1.2 dedup) is attributed only to whichever label recorded first. Per-broadcast per-label id tracking is the workable mechanism; §3.4 should bind that instead.

**[MID] §6.1 — the named-result shape is under-specified on three concrete paths.**
(a) One `Histogram` with multiple `.fill` calls carrying different label sets: what enters `jes_up` for a fill call with no jes labels (physically: its nominal) is nowhere stated, and `_GroupReduce.layout` counts fills per output positionally (`boost.py:100-117`). (b) The single-histogram `Histogram.plan()` path reduces via `_SumFills`, which sums **all** staged fill nodes into one histogram (`boost.py:88-98`) — a varied fill through an un-rewired `.plan()` silently sums nominal+up+down; the plan names only the `_GroupReduce` generalization. (c) Mixing varied and unvaried outputs in one `plan()`: `{output: hist}` vs `{output: {label: hist}}` value shapes (does unvaried become `{"nominal": hist}`?) is unbound; §6.3 pins node bytes, not result shape.

**[MID] §6.2 — the variation-axis evaluator shape covers weight labels but not the shift labels its own m50 anchor requires.**
The bound mechanism ("labels ride params", extend `FillEvaluator` with N weight inputs + a scalar-string loop) assumes shared axis columns; shift labels have **per-label axis columns of differing lengths** (§5.1 cutflow divergence), yet the m50 anchor demands "variation-axis fill equals sibling-fill results bin-for-bin on the corpus matrix," which includes jes labels. Per-label axis-input grouping in the evaluator/params layout needs binding or the anchor needs scoping to weight labels.

**[LOW] §2.5 — the "unreached non-nominal labels" diagnostic requires a frontend registry of live `Varied`s that no section creates (`compile_ir` sees only output Arrays, `python/graphed/execute.py:54-82`).**

**[LOW] §2.3(a) — the dunder inventory is illustrative where it must be exhaustive: `Array` also implements `__array_ufunc__` (`array.py:156`), bitwise `__and__/__or__/__invert__` (`:245-275`, corpus `sel = base & (...)`), and reflected dunders; `np.sqrt(varied)` et al. silently bypass a Varied lacking `__array_ufunc__`.**

**[LOW] §10 m48 — reference arithmetic: ttbar 4j1b/4j2b × {nominal, btag_up, btag_down} (6) + ttgamma × {nominal, pho_up, pho_down} (3) is 9 refs, not "10 of the 15".**

**[LOW] §2.1 — a `Varied` whose members root in a second partitioned source fails only much later at `aggregate_plan` ("exactly one partitioned source", `python/graphed/aggregate.py:91-93`); §2.1's construction-time checks (Session, form) should also pin the source constraint or name the deferred error surface (§11 parks the automation, not the diagnostics).**

**[NIT] §5.2(a) — the arena-delta witness ("grows by exactly the varied cone") is false for a label structurally identical to a prior label (Δ=0 by §1.2 dedup); the witness formulation must exclude or separately witness the dedup case.**

## Lens coverage

1. **Record-time expansion promises**: two BLOCKERs (same-label combination incl. Varied-meets-itself; stacking) + MID (.map capture). Reductions over `Varied` per se: nothing found (gak reducers broadcast cleanly; partition-axis reductions are per-label boundary nodes, unproblematic). Sources/partitions × labels: LOW only.
2. **§2.3 sufficiency for the corpus**: fails today on plain-`Array[Varied]` (HIGH), the uniform-wrapper fiction (HIGH), and the stacking BLOCKER; `with_field`/`prod`/`num`/`sum`/`firsts`/`drop_none`/comparisons/field-access are covered (all present in `functions.py`).
3. **§6.1 coherence**: BLOCKER-1 covers the axes+weights-both case; MIDs on result shape and the `_SumFills` path.
4. **Internal contradictions / R-rules**: §1.2 vs §6.2 (HIGH), §8.2 vs §1.2+§7.2 (HIGH); R17.0 claim itself holds (an inspect-transparent wrapper preserves the pinned defaults surface); no §A.4 boundary violation found (core untouched, dependency directions correct); milestone numbering m48–m50 verified collision-free (consolidated repo tops out at m41 per-pkg, executors at m47).
5. **Directive fidelity**: nothing silently dropped — the "systematics node of the IR" framing is openly resolved to no-new-NodeKey in Part I §3/§3.1 with evidence; the impact-analysis open question, joint-fill question, and process asks are all addressed; added scope (§6.2 axis mode, §9.2 preservation, §3.4 impact API) traces to directive sentences or flagged milestones. No finding above LOW.

## Verdict

**NOT CLEAN — r1 required: 2 BLOCKERs (combination-rule label alignment; variation stacking) make the m49 15-reference anchor unreachable as specified, plus 4 HIGH internal/completeness defects; the record-time-expansion core is sound but §2's semantics need one more design pass before test-authoring.**

---

# [tests lens]

# TESTS / acceptance-anchor review — `systematics-vary-plan.md` r0

Scope: §10's m48/m49/m50 frozen anchors, witness discipline (R0.10/R0.10a/R0.11), and whether the cited existing frozen artifacts are real and usable as claimed. I opened every artifact named below.

**Artifact-reality check (all four cited anchor sets are REAL and say what the plan says):**
- `graphed-latest/tests/frozen/corpus/m05/test_systematics.py:25-37` — `test_kinematic_variation_changes_selection` asserts `jes_up > nominal > jes_dn`; `test_weight_variation_preserves_selection` asserts `btag_up == nominal == btag_dn`. Confirmed.
- `graphed-latest/tests/frozen/core/m4/test_systematics.py:28-53` and `test_benchmark.py:10,36-53` — confirmed (`SIZES=[1000,2000,4000,8000]`, `growth < 24.0`).
- `graphed-histogram-latest/tests/frozen/m23/test_group_plan.py:68-77` — read-counting `ChunkedSource`, `assert len(src.part_reads) == 4`. Confirmed.
- `graphed-histogram-latest/tests/frozen/m29/test_multi_weight_fills.py:82-99` — confirmed, incl. the identity-discipline test at :93-99.
- `graphed-latest/tests/frozen/preserve/m9/test_reproduce.py:19-60` + `agc.py:38-66,94-118` — confirmed, incl. the correctionlib `systematic` category input and the per-bundle-config variation pattern.
- Corpus references: 23 files in `graphed-corpus/corpus/references/` (= `graphed-latest/tests/_corpus/references/`), 15 of them systematics. Confirmed.

---

## BLOCKER

**[BLOCKER] §10 (m50), §6.2 — the m50 scaling benchmark is listed as a *frozen anchor* but is a wall-clock A/B comparison, which R0.10a forbids in a frozen test.**
§10 m50 reads: "Frozen anchors: … N≈100 weight-variation scaling benchmark with **measured** methodology (R0.11 …) comparing sibling-fill vs axis mode". That is literally the `dt_with < dt_without` shape R0.10a bans: *"(a) **wall-clock comparisons** (`dt_with < dt_without`) — on a loaded runner real work is dwarfed by process-startup and transport noise"* and *"measurement of a perf claim is R0.11; a frozen **gate** must not depend on it"* (`graphed-root-prompt.md:203-215`). R0.11 governs the *report*; putting the comparison in `tests/frozen/**` makes it a gate.
*Minimal fix:* split it — the frozen anchor asserts the **structural** invariant §6.2 actually claims ("O(1) objects instead of O(N)"): per-partition histogram-object count and per-combine payload entry count are `1` in axis mode vs `N+1` in sibling mode (countable at the `FillEvaluator`/`_GroupReduce` seam, `boost.py:100-117`), plus bin-for-bin equality. The wall-clock N≈100 comparison moves to the m50 implementer/reviewer report under R0.11 methodology, out of the frozen suite.

**[BLOCKER] §1.2 vs §6.2 — the two binding clauses contradict each other, and a frozen §1.2 test would fail the §6.2 implementation by construction.**
§1.2: "a label MUST NOT enter `NodeKey` params, tokens, or content hashes." §6.2: the variation axis is a "pre-declared, sorted StrCategory `"variation"` axis … labels ride params". Measured: `Histogram.fill` passes `{"spec": self._spec, …}` as the External **params** and derives `content_hash = content_hash(self._spec)` for the `PayloadDescriptor` (`graphed-histogram-latest/src/graphed_histogram/boost.py:183-207`), and the spec is canonical JSON of axes+storage (`_spec.py:115-122`). Adding a StrCategory axis whose categories are the labels therefore puts the label strings into **both** params and the content hash. cba §histogram states the opposite of §1.2 outright: *"The variation labels must enter the content hash (via spec metadata or params)."* A test-author freezing §1.2 ("renaming a systematic must not recompute") and an implementer building §6.2 collide → guaranteed Test Dispute at m50.
*Minimal fix:* scope §1.2 to the sibling-fill/expansion path and add the carve-out explicitly: labels that become **output content** (bin identities on the variation axis) are content and DO fork identity; labels used only as frontend bookkeeping MUST NOT. Then §10 m48 must name the §1.2 anchor (see below) in its scoped form.

---

## HIGH

**[HIGH] §10 (m48/m49) — the corpus-reference matrix is by itself completely non-discriminating: today's per-variation re-run loop (`m05`) reproduces all 15 references perfectly.**
`tests/frozen/corpus/m05/test_fixtures_reproduce.py:29-35` already reproduces every one of the 15 refs by calling `ttbar_region(events, region=…, variation=…)` once per variation. An implementation of `vary` that is a `for label in labels: rerun(analysis)` loop passes the m48 *and* m49 headline anchors identically. The plan does name witnesses (single-pass read, dispatch count, §5.2 a/b/c) but lists them as **separate** anchors from the matrix, so a test-author can legitimately satisfy them on a toy graph while the reference matrix runs through a loop.
*Minimal fix:* bind them — require the read-count and dispatch-count witnesses to be asserted **on the same Session/plan run that produces the reference matrix** (one `graphed_histogram.plan({...})` over all 15 outputs; `len(src.part_reads) == n_partitions`, not `n_partitions × n_labels`), the m23 pattern applied to the real fixture rather than a toy.

**[HIGH] §4.3 / §10 (m48) — the "weight variation preserves selection" anchor is guaranteed true by the chosen architecture and therefore cannot fail: an R0.10 test-sanity failure.**
The m05 invariant asserts *equal selected counts* across weight labels (`test_systematics.py:33-37`). Under §3's record-time expansion + interning, a weight variation forks only the fill's weight input; the selection nodes are the *same interned NodeIds* by construction (`src/store.rs:73-88`). Equal counts is then a tautology — exactly the "input/output equivalence for a *how* requirement" R0.10 calls out (`graphed-root-prompt.md:196-202`).
*Minimal fix:* keep the count assertion as a sanity check, but make the **discriminating** anchor structural: assert the selection cone's NodeIds are byte-identical across all weight labels (equivalently, the §3.4 impact set for every weight label contains **no** node upstream of the fill's weight input). That fails a re-run/clone implementation and passes the real one.

**[HIGH] §3.4 / §5.3 / §10 — the impact-set API is defined by an id watermark, which computes the wrong set for every label after the first, and §10 names **no** anchor for it at all.**
§3.4: "the per-label set of node ids **not shared with nominal** (computable from the Session's id watermark before/after expansion)". Ids are monotone and `intern` returns existing ids (`src/store.rs:73-88`), so a watermark diff yields "nodes new since the previous label" = *not shared with nominal **or any earlier label***. Two labels that share a derived node (e.g. `jes_up` and `jes_down` both deriving `Jet.eta` bins) attribute it entirely to whichever expanded first — order-dependent and wrong. §5.3 then builds per-label projection stats on top of it. §10's m49 anchor list ("15-reference matrix; m05 ordering; §5.2 (a)(b)(c); §2.4; §5.3 projection-union; §3.3 benchmark; §8.2; §5.4 refusal") contains no §3.4 test, so nothing catches it.
*Minimal fix:* define the impact set as a set difference over reachable-node sets (`reachable(label) − reachable(nominal)`, `session.walk` already exists) rather than a watermark, and add an m49 anchor: three labels where label 2 and 3 share a derived node, asserting that node appears in **both** impact sets and that the result is independent of expansion order.

**[HIGH] §3.3 — "The M4 CI benchmark … **gains** a variation-shaped topology" reads as editing `tests/frozen/core/m4/test_benchmark.py`, which the integrity rules make non-negotiably read-only.**
§3.1 says the m4 frozen contract "continues to bind unchanged" and §10 says the layout is `tests/frozen/<pkg>/m48…`, so the intent is probably a new file — but §3.3's binding text says the m4 benchmark gains the topology, and it is listed under m49's anchors. Root `CLAUDE.md` §A.7/§B.6: never "edit, delete, `skip`, `xfail`, or weaken any test under `tests/frozen/**`".
*Minimal fix:* one word — "a **new** frozen benchmark file (`tests/frozen/core/m49/test_variation_benchmark.py`) replicating the `test_benchmark.py:10,36-43` pattern; m4's file is untouched."

---

## MID

**[MID] §3.3 / §10 (m49) — the benchmark topology as stated can be written in the m4 `_systematics` shape, in which the assertion is vacuous.**
`tests/frozen/core/m4/test_systematics.py:20-25` funnels **all** variations into a single output (`acc = add(acc, w)`), which is why `reduced.node_count() <= 8` at 3300 variations. The real `vary` topology has **one output per variation** (one fill per label), for which the measured reduced form is `2N+2` nodes / `N+1` stages (cba §optimizer §2). If the test-author copies the m4 builder, "reduced stage count = shared-prefix stages + O(1) per variation" degenerates to a constant and pins nothing about expansion.
*Minimal fix:* §3.3 must state that each variation is a **separately marked output**, and pin the exact expected value (`stages == N + 1`, `reduced_nodes == 2N + 2`) rather than an asymptotic phrase.

**[MID] §5.2(a) / §10 (m49) — the arena-delta witness is tautological unless the expected count is computed independently.**
"adding label k … grows the Session node count by exactly the varied cone" invites `assert delta == len(varied_cone)` where both sides come from the same expansion. The in-context probe got its discriminating power from a **hardcoded** expectation (`delta == D + 2 == 52` for a known 50-op chain).
*Minimal fix:* require a fixed-topology fixture with a literal integer expectation (`assert store.node_count() - before == 52`), the m4 style, not a self-derived one.

**[MID] §2.4 / §10 (m49) — a "behavioral test" of the no-cross-product rule is passed by an implementation that computes the cross product and discards it.**
The values-and-labels assertion is output equivalence for a *how* requirement (R0.10 again). The cheap discriminator is structural.
*Minimal fix:* add `len(fill_nodes) == 1 + |shift_labels| + |weight_labels|` (never the product) alongside the label-set/value assertions — countable via `Histogram.staged_fills()` / `_fill_nodes`.

**[MID] §6.3 / §10 (m48) — "records exactly the pre-m48 node bytes" is not writable as stated at freeze time, but two in-tree patterns make it writable.**
The test-author freezes before the implementation exists, so "pre-m48 bytes" has no in-test referent. Both precedents exist: a committed **golden byte literal** (`tests/frozen/core/m40/test_join_serialize.py:84-99`, "M8 golden: tags 0..2 + GIR1 magic must not move") and **param-absence** (`m29/test_multi_weight_fills.py:93-96`, `assert "n_weights" not in node["params"]`).
*Minimal fix:* name both patterns in §6.3 — a committed golden GIR blob for an unvaried fill graph, plus absence of every new params key.

**[MID] §10 (m49) — "the full 15-reference matrix bit-for-bit … through a process-pool executor" overstates what the existing precedent achieves.**
The corpus systematics fixtures use `Double` (weighted) storage; through a partitioned executor the per-partition partials reassociate. The nearest in-tree precedent deliberately does **not** claim bit equality on the plan path: `m29/test_multi_weight_fills.py:77-79` asserts `array_equal(result, again)` run-to-run but only `allclose(..., rtol=1e-12)` against the eager reference. The corpus comparison survives because `bin_values`/`fingerprint` round at `STABLE_DECIMALS = 6` (`graphed-corpus/src/graphed_corpus/histograms.py:20,35-43`) — i.e. it is rounding-mediated equality, not byte equality.
*Minimal fix:* state the comparison explicitly as `fingerprint(h) == ref["fingerprint"]` / `bin_values(h) == ref["values"]` (the `m05/test_fixtures_reproduce.py:33-35` form) and add the run-to-run `array_equal` determinism assertion separately. Drop the phrase "bit-for-bit" for the executor leg or qualify it.

**[MID] §3.2 / §10 — no anchor anywhere pins two-run byte-identical compilation of a variation-expanded graph, despite §2.2 making label order an insertion-order-dependent thing.**
§3.2 defers to the R0.4 mechanical gate, but §10 lists no determinism anchor for m48/m49, and the failure mode is specific: a `set`-backed label store or a dict-order regression silently reorders expansion and changes the GIR bytes. R22.3 already established the strong form of this test (cross-process, differing `PYTHONHASHSEED`).
*Minimal fix:* add to m48 anchors — same varied program compiled in two fresh processes under different `PYTHONHASHSEED` produces byte-identical `compile_ir` output, and `.labels` order is nominal-first + insertion order.

**[MID] §5.4 / §10 (m49) — the refusal anchor has no positive control, so a blanket "any `Varied` + any `Join` raises" passes it.**
*Minimal fix:* pair the refusal test with a variation whose cone is entirely **downstream** of the Join/Exchange and must still compile and produce correct results.

**[MID] §7.3, §7.4, §9.1 — three binding requirements with no §10 anchor.**
m49 targets "§7" but its anchor list contains no checkpoint/resume test; §7.3's "within one plan, resume works per-partition exactly as today" and §7.4's "the StageError names the guilty label" (distinct from §8.2's cross-process test) are unanchored, as is §9.1's introspection surface.
*Minimal fix:* add to m49 — a mid-plan interrupt/resume over a varied graph that is byte-identical to an uninterrupted run (existing checkpoint-resume pattern), and fold §7.4's label assertion into the §8.2 test; add §9.1's `{output: [labels]}` listing to m50's `inspect()` anchor, where it costs nothing.

**[MID] §9.2 / §10 (m50) — "reproduces the per-label reference histograms bit-for-bit" is ambiguous about which references.**
m9's bundle reference is an in-process `np.histogram` result (`preserve/m9/agc.py:120-128`, `test_reproduce.py:19-23` compares `reproduce(bundle)` to the build-time materialize), not the corpus `hist.Hist` references. The two are different objects with different comparison semantics.
*Minimal fix:* say which — recommend the m9 form (`np.array_equal(reproduce(bundle)[label], build_time[label])` per label), since it is the one that is genuinely bit-exact.

---

## LOW

**[LOW] §10 (m48) — the arithmetic is wrong: the weight-variation subset is 9 of the 15 references, not 10.**
`TTBAR_FIXTURES` = 2 regions × {nominal, jes_up, jes_down, btag_up, btag_down}; `TTGAMMA_FIXTURES` = {nominal, jes_up, jes_down, pho_up, pho_down} (`graphed-corpus/src/graphed_corpus/analyses/systematics.py:107-112`; 15 files confirmed in `corpus/references/`). ttbar 4j1b/4j2b × {nominal, btag_up, btag_down} = 6, plus ttgamma {nominal, pho_up, pho_down} = 3 → **9**. The remaining 6 are the JES (shift) refs deferred to m49.

**[LOW] §10 (m48) — the ttgamma weight references need a constant weight array, which the fill layer cannot accept directly.**
`ttgamma_region` builds `weight = np.full(n, sf)` (`systematics.py:94-99`). `Histogram.fill` rejects non-`Array` weights (`boost.py:173-174`) and there is no constant-Array constructor in the frontend (cba §histogram §1). Expressible as arithmetic on an existing array, but the anchor should say so rather than leave the test-author to discover it mid-freeze.

## NIT

**[NIT] §10 — the frozen-layout sentence omits `graphed-histogram`, which m50 primarily targets.** That repo's layout is flat (`tests/frozen/m23`, `tests/frozen/m29`), not `tests/frozen/<pkg>/mXX`; §10 covers only "consolidated repo" and "executors".

---

**Verdict: NOT CLEAN — 2 BLOCKERs (a wall-clock frozen gate that R0.10a forbids; a §1.2/§6.2 label-in-content-hash contradiction that guarantees a test dispute), 4 HIGHs, 9 MIDs; every cited existing frozen artifact is real and accurately described, but the §10 anchor set as written can be discharged by a per-variation re-run loop.**

---

# [process lens]

# Findings — PROCESS-FIT + STREAMLINING lens, `systematics-vary-plan.md` r0

**[HIGH] §10, m48 repo scope — `graphed-histogram` is silently absorbed into "`graphed` repo," contradicting the plan's own evidence and its sibling milestones.**
Line 339: `- **m48 — vary frontend + weight path** (\`graphed\` repo: frontend + histogram).` But m48's own Targets list includes §6.1/§6.3 (Histogram integration), and the plan's own Anchors appendix cites the implementing code as `graphed-histogram src/graphed_histogram/boost.py:166-174,205-206` and `graphed-histogram tests/frozen/m23/test_group_plan.py:68-77` — a **separate repo**, confirmed by memory `graphed-consolidation.md:35` ("**graphed-histogram** and **graphed-executors** (RENAMED 2026-07-18 …)" — i.e. histogram was *not* one of the 8 packages folded into the consolidated `graphed` repo) and by the task's own ground-truth paths (`/private/tmp/claude-501/graphed-latest` vs. the distinct `/private/tmp/claude-501/graphed-histogram-latest`). m49 and m50 both label multi-repo scope correctly (`` `graphed` + `graphed-executors` ``, `` `graphed-histogram` + `graphed` preserve/docs ``) — only m48 collapses it to one repo. Since the orchestrator dispatches per-repo submodule, this mislabel would misroute m48's setup/test-authoring scope.

**[MID] §10 numbering note omits `graphed-histogram`'s frozen-tree convention even though m48/m50 need it.**
Lines 334-335: `` per-repo frozen layout is `tests/frozen/<pkg>/m48…` (consolidated repo) / `tests/frozen/m48…` (executors, if touched). `` Only two conventions are named. Verified on the clones: `graphed-histogram-latest/tests/frozen/` contains `m23/`, `m29/` directly — the flat `tests/frozen/mXX/` shape (like executors), **not** the consolidated repo's `tests/frozen/<pkg>/mXX/` shape. Since m50 (and, per the HIGH finding above, actually m48 too) lands work in `graphed-histogram`, the note should say so explicitly; as written a test-author could default to the wrong nesting convention for that repo.

**[MID] §10, m48 reference-count is arithmetically wrong (off by one).**
Line 341-342: `ttbar 4j1b/4j2b × {nominal, btag_up, btag_down} + ttgamma {nominal, pho_up, pho_down} = 10 of the 15 refs`. Computed: 2 regions × 3 labels = 6 (ttbar) + 3 (ttgamma) = **9**, not 10. Verified against the actual 15 systematics reference files in `graphed-corpus/corpus/references/` (`ttbar_{4j1b,4j2b}_{nominal,btag_up,btag_down,jes_up,jes_down}.json` = 10, `ttgamma_{nominal,jes_up,jes_down,pho_up,pho_down}.json` = 5). This is a binding milestone-acceptance-anchor number a test-author would freeze the m48 suite against; it should read "9 of the 15 refs."

**[LOW/NIT] §3.3 duplicates a measured figure already stated in Part I, against the owner's streamlining instruction.**
Line 227-228 parenthetical `(Measured today: linear, 11.9× time for 12.9× nodes — the test pins it so it stays true.)` restates, verbatim in substance, Part I §3 bullet 3 (line 130): `128 variations × 50-op chains: 12.9× nodes → 11.9× time, 16.7 ms`. Given the doc's own framing ("rationale is context and binds nothing; PART II binds… separate rationale from requirements"), this is exactly the kind of restated evidence that belongs only in Part I / cba, with Part II cross-referencing it (`see §3 Part I`) rather than repeating the numbers. Not misleading, just redundant.

**Item 1 (rationale/requirements separation) — no stray binding "MUST" content found stranded in PART I.** Grepped `MUST|MUST NOT|REFUSES` over lines 1-164: zero hits. Part II's inline precedent-pointers (`RDF lesson`, `PocketCoffea's … lesson`, `mkShapesRDF silent-cost case`, etc.) are all one-clause parentheticals grounding a specific requirement, not prose blocks — this doc is materially more disciplined about the rationale/requirements split than the join-repartition plan precedent (which doesn't even cite R0.x). Only the §3.3 duplication above rises above noise level.

**Item 2 (§12 vs root prompt R0) — no missing or misstated R0 content found.** Checked §12.1 and §10's DoD line against R0.1–R0.11 (`graphed-root-prompt.md:124-223`) directly: R0.3 test-sanity wording matches almost verbatim; R0.4/"coverage from the frozen suite" is correctly captured in §10 ("≥90% diff coverage from the frozen suite," not just any coverage); R0.4a ("src AND tests") is explicitly cited in §10; R0.5's "confirmed at the pinned revision" language is correctly reflected; R0.7's dispute path (`.graphed/<mX>/disputes/`) is correctly cited; R0.9 (strict order) is enforced by the `m48 → m49 → m50` header itself; R0.10/R0.10a/R0.11 are explicitly invoked and §5.2's three witnesses are shaped exactly like R0.10's own examples (arena-delta counter, single-read counter, structural stage-count — no wall-clock/emergent-distribution witness anywhere, consistent with R0.10a). R0.4b/R0.4c (local-gate-matches-CI, platform-portability) are standing tooling rules that apply uniformly via existing infra and don't need per-plan restatement — their absence is not a defect.

**Item 3 (§12.3 bookkeeping amendment sites) — all four sites verified correct and complete; found nothing else parked on systematics that's missed.** (a) `r22-draft.md` precedent file exists at the cited path. (b) R22.0 is at `graphed-root-prompt.md:1262` and contains "systematics-as-a-graph-axis … stay Phase 2" verbatim; R22.10 at `:1282` contains the same phrase verbatim; the Out-of-scope block header is at `:1284`, and its systematics line is at `:1286` ("treating systematic variations as a graph axis") — the plan cites the block by its header line, which is an acceptable pointer to "the block" even though the phrase itself is two lines further down (minor imprecision, not worth a separate finding). (c) Root `CLAUDE.md` Part F header is at line 238 and its systematics mention at line 240 — matches. (d) `ops_catalog.md:75` is exactly the "Systematics-as-a-graph-axis…" row, quoted verbatim in the plan, and Section C ("Systematics, corrections, ML," line 43) exists as a real target section; `tests/frozen/m05/test_catalog.py` only does text-presence assertions (`test_every_fixture_family_is_catalogued`, `test_catalog_maps_ops_to_milestones`), so moving the row into Section C genuinely won't break lock-step, confirming the parenthetical claim. Grepping the full root prompt and CLAUDE.md for "systematic" turned up no other Phase-2-parking mention outside these four sites (the remaining hits — R4.2, R13.7, R18.4c, the M7/M9 corpus descriptions — are unrelated narrative/perf-test content, not parked scope).

**Item 4 (milestone numbering vs. actual frozen-tree layout) — covered above (the two findings); no further discrepancies found** beyond the m48 repo-mislabel and the missing graphed-histogram layout convention. "Executors repo froze m47 last" is confirmed (`graphed-exec-check/tests/frozen/` top entry is `m47`).

**Item 5 (readability/cross-references/jargon) — no broken §-cross-references found.** Every forward/backward `§N.M` reference in Part II (§3.4, §6.1/§6.2/§2.4 combination rule, §5.4, §7.3, §11, etc.) resolves to the section it claims to. No undefined jargon beyond terms already established as real codebase vocabulary (`op_form`, `AddressTable`, group-plan) that this project's own conventions treat as known to the intended (graphed-engineer) reader.

**Verdict:** Not clean — one HIGH (m48's repo scope is factually wrong and inconsistent with its own sibling milestones and anchors) plus two MID findings (an unaddressed frozen-layout convention for `graphed-histogram`, and an off-by-one in the m48 reference-count anchor) block a claim of "ready for round 1 sign-off"; fix those three plus the minor Part I/II duplication before the multi-lens review cycle starts.