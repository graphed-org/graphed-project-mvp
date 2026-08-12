# systematics-vary-plan review — round 15, lens: TEST ARCHITECTURE

- **Document reviewed:** `systematics-vary-plan.md` **r23** (5605 lines; read in full — Part I, §§1–12,
  §10 anchor lists, Anchors appendix, revision history r23/r22).
- **Lens:** test architecture — non-vacuity/discrimination of every §10 anchor and every
  "frozen-witnessed / frozen-anchored" claim in §§1–9; witness-of-mechanism (R0.10); R0.10a (no
  wall-clock / size thresholds in frozen tests); determinism-gate compatibility; freeze-order
  hazards; traceability (requirement ↔ anchor, both directions); testability of the fixtures as
  stated.
- **Date:** 2026-07-30 (review executed against the pinned roots).
- **Verification roots used (every code fact and probe below was read or executed by me in this
  session):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (probes in its `.venv`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (probes in its `.venv`,
    boost_histogram 1.8.0)
  - `/private/tmp/claude-501/graphed-exec-check` (graphed-executors @ `201ea42`)
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef` (branch `graphed-mvp`)
  - `graphed-root-prompt.md` (R0.4a read verbatim at `:147-153`)

## What I re-verified clean (recorded so round 16 need not redo it)

All measured this session:

- **r23's new §4.1 correctionlib digest reproduces exactly.** Executing
  `correctionlib_content_hash(agc.correctionlib_json())` (the fixture's default `scale=1.0`,
  `tests/frozen/preserve/m9/agc.py:38`; hash fn
  `python/graphed/preserve/externals/correctionlib_external.py:14-18`) gives
  `sha256:e72c0da3cb6614cfaf50cea8c93ab740e8229986024a8bad4361e9ae82f4b5cd` — the literal m48's
  anchor now carries. The r22 withdrawal was right and the replacement is re-runnable.
- **r23's new m50 fourth output is buildable.** `bh.Histogram(Regular(3,0,1), StrCategory(["nominal"]))`
  fills and sums correctly (1-bin, non-growth), and `graphed_histogram._spec.spec_of` → `zero_of`
  round-trips it with the name carrier intact:
  `[a.__dict__.get("name") for a in z.axes] == [None, "variation"]`, bins `['nominal']`. The
  `(output, None)`-keying witness costs exactly the one histogram r23 claims.
- **The `Mean`/`WeightedMean` storage pins (m48 four-way fold order, m50 sample-only label) create no
  second fixture problem**: a two-axis `Mean()` histogram accepts `weight=` and `sample=` together,
  `Mean()` + a `StrCategory` variation axis fills, round-trips through `spec_of`/`zero_of` (storage
  preserved) and **adds** (`(h+h).sum()` → `Mean(count=6, …)`), so §6.1c's key-wise `+` is safe on the
  axis-mode sample fixture.
- **r23's §10 `uproot5-graphed-mvp` gate analysis is correct at `393ecef`**: `pyproject.toml:136`
  `testpaths = ["tests"]` (so a new `tests/frozen/m51` IS collected); `.github/workflows/graphed.yml:55`
  runs `python -m pytest -vv tests -m "not xrootd"` with zero `--cov`; matrix is `ubuntu-latest` ×
  `["3.11","3.12"]` (`:32`); triggers are `push: [graphed-mvp]` + `workflow_dispatch` (`:7-10`), no
  `pull_request`; there is no `[tool.mypy]` section anywhere. The three binding m51 items (a)/(b)/(c)
  are the right shape.
- **r23's `graphed-executors` span correction holds**: `ci.yml:44` and `:67` run `pytest tests/frozen`
  whole-tree, `:101` runs `tests/frozen/m42 … m45` and `:153` runs `m46 m47` — per-milestone, as r23
  now says.
- **r23's re-citation of the type gate to R0.4a is right**: `graphed pyproject.toml:83` is
  `strict = true` and `:84` is `files = ["python"]` (src-only), while R0.4a
  (`graphed-root-prompt.md:147-153`) is what actually binds src+tests and names src-only repos as a
  pending cleanup. My r22 finding #2 is discharged.
- **m48's §6.1c layout re-keying breaks no frozen artifact**: no frozen test in `graphed-histogram`
  touches `_GroupReduce.layout` (`grep -rn "layout" tests/frozen` → only
  `m23/test_process_executor_witnesses.py:87,109`, which are `ak.Array.layout`, and
  `m23/test_deferred_histograms.py:67` `staged_fills()`), so §10's "m23 artifacts binding and
  unchanged" survives the index-based layout.
- **Private access from a frozen test is precedented**, so r23's (α) read-back route is not novel:
  `graphed tests/frozen/awkward/m28/test_preservable_externals.py:43` already does
  `s._store.nodes()`.
- **R0.10a sweep**: still exactly one wall-clock threshold in the whole anchor set (§3.3's
  `time(128)/time(16) < 16.0`, the named M4-mandated carve-out). Nothing r23 added carries a
  wall-clock or size threshold; m51's new CI coverage gate is a CI invocation, not a frozen test.
- **Freeze-order sweep over r23's additions**: the m48 `variation_labels == ()` read-back stays green
  at m49 (the m48 fixture supplies its own hook return); m48's §7.2 schema-key-set anchor is unaffected
  by the `_PartitionReduce` field (all three named schemas are separate dataclasses); the §2.3d
  per-class floors and gak/`Array` refusing floors remain containment + monotone counts; `unpack`'s
  declared union still covers the axis-mode bare histogram; §6.3's pre-m48 golden is untouched by the
  `unweighted=`/`_context`/layout/seam work. **No new instance of the r7 "grammar anchor freezes a
  superseded rejection" class, and no anchor left describing r8-era p-form canonical semantics.**
- **Self-derived-oracle sweep**: no new instance of the §4.3 equal-counts / §5.2a `delta == len(cone)`
  trap class. r23's new controls are all independently derived (m51's sixth control compares against
  "the same skim written from `E2`", m50's fourth output against a literal key form, m49's §3.4
  fixture against the watermark implementation's empty set).

## Findings

### 1. MID — §3.4's impact API is the one new public surface with no name, no argument shape, no return type and no "spelling pinned at freeze" clause, and m49 freezes an anchor written over it

**Section:** §3.4, §9.1 (its list entry), §10/m49's impact-set anchor, §4.3's optional cross-check.

**Detail.** Every other new read-only surface in this plan is pinned with a shape *and* a
freeze-pinning clause, each time after a review found it "unwritable as stated": §2.5's diagnostic
channel (r15), §5.3's projection-stats verb (r16: *"the stats had no name, no shape, no return type
and no 'spelling pinned at freeze' clause, unlike every other new surface here"*), §6.1a's
`unpack(value) -> dict[str, bh.Histogram | dict[str, bh.Histogram]]` (r18), §6.1d's
`unify_contexts`/`reindex_to` (r20), §9.1's `fill_nodes_by_label(h) -> dict[str, Array]` (r13),
`context_of`, `weight`, `selection`, `read_varied`, the plan-level `{output: [labels]}` listing.

§3.4 is the exception. Its whole surface statement is *"A read-only frontend helper reports, per
label, the reachability difference `reachable(label's outputs) − reachable(nominal outputs)` computed
via `session.walk`"* (§3.4, plan `:1297-1303`), and §9.1 lists it as the bare phrase **"the §3.4
impact API,"** (`:3039`) — no verb name, no operand (a `Varied`? a context? a sequence of outputs?),
no element type (node ids? `Array`s?), no container type, no freeze-pinning clause. The nearest thing
to a shape is §2.3d's r20 aside that it *"answer[s] PER LABEL over `Array` operands"* (`:889`) and
that *"m49's own anchors assert their per-verb shapes (§5.3's `{label: …}` mapping; §3.4's impact
sets)"* (`:894`) — but "impact sets" is not a shape.

m49 then freezes behaviour through it: *"§3.4 impact-set anchor: three labels where two share a
derived node — the shared node appears in both impact sets; result independent of expansion order"*
(`:4023-4034`), and §4.3 offers `impact(L)` as an optional m48 cross-check (`:1386`). A test-author
must therefore invent the call spelling **and** the element type and freeze the guess read-only —
the exact defect class this plan has repaired five times. The element type is not cosmetic: the
assertion "the shared node appears in both impact sets" is written one way for a set of ints and
another for a set of `Array`s, and `session.walk` itself hands the caller node ids only through
its own handlers (`python/graphed/session.py:245-290` — it takes `source`/`op`/`external` callables
and returns the root's value, so the impact helper's return shape is a free choice).

**Evidence.** Plan `:1297-1303` (§3.4), `:3039` (§9.1 entry), `:889,894` (§2.3d r20), `:4023-4034`
(m49 anchor), `:1386` (§4.3 cross-check); contrast §5.3's r16 repair at `:1479-1487` and §9.1's other
entries at `:2982-3053`. `python/graphed/session.py:245-290` read this session.

**Suggested fix.** Give §3.4 the §5.3 treatment in one clause: a read-only `graphed` module verb over
the same operands as `read_columns`/`graphed.labels`, returning `{label: tuple[int, ...]}` (sorted
record node ids, the house discipline `projection.py:147` already uses) — **spelling pinned at m49
freeze**, listed with a shape in §9.1 alongside the projection-stats verb. Say explicitly whether the
per-label value is node ids or `Array`s, since m49's anchor asserts membership in it.

### 2. MID — §2.6b's only worked program for the new context-identity rule is a mixed-granularity fill, the exact fixture shape §6.1d r19 twice removed as unexecutable

**Section:** §2.6b (r23), §6.1d's r19 same-granularity clause, §10/m48's op-level divergence anchor.

**Detail.** r23's HIGH fix binds "PURE DERIVATIONS ARE CANONICAL" and motivates it with:

> the divergence rule fires on legal programs (`h.fill(graphed.nominal(sel).MET.pt,
> graphed.nominal(sel).Jet.pt)`; `sel1 = events[mask]`, `sel2 = events[mask]`), a FALSE refusal …

The first program mixes a **per-event** axis value with a **per-object** one. §6.1d's own r19 clause
exists precisely to forbid that as a fixture — *"Both worked examples in this paragraph use
SAME-GRANULARITY axis values, and that is deliberate, r19 (r12–r18 wrote them as
`h.fill(events.MET.pt, sel.Jet.pt)` … which cannot execute for a reason unrelated to the mechanism
they illustrate — **and m48 froze both as fixtures**)"* — and it closes with *"mixed-granularity
multi-axis fills are NOT scoped in m48–m51"*, so the r23 sentence's "legal programs" is also
inaccurate about the second axis. Re-measured this session, boost_histogram 1.8.0:
`bh.Histogram(Regular(3,0,10), Regular(3,0,10)).fill(np.arange(3.0), np.arange(5.0))` →
`ValueError: spans must have compatible lengths`, and `graphed-histogram`'s evaluator flattens each
axis input independently (`src/graphed_histogram/boost.py:39-47,60-71`), so the program dies at
EVALUATION, after the freeze, against a correct implementation.

Mitigating: m48's anchor bullet attaches the new positive control to the **op-level** half
(*"a binary op over `Array`s from two divergent contexts raises AT THAT OP … AND a SECOND positive
control for §2.6b's r23 context-IDENTITY rule — two separate `graphed.nominal(sel)` reads … UNIFY
rather than raising"*, `:3744-3754`), which lives in `graphed`'s half and needs no fill. But the
anchor spells no program, so §2.6b's illustration is what a test-author transcribes — and this plan's
practice, everywhere else, is to make the illustration the buildable fixture (`gak.full_like`,
`stable()` rounding, `h.axes.name`, the pt-cut jets, the correctionlib spelling, the `Mean` storage).

**Evidence.** Plan `:1134-1140` (§2.6b r23), `:1845-1856` (§6.1d r19), `:3744-3754` (m48 anchor);
bh 1.8.0 probe above; `graphed-histogram src/graphed_histogram/boost.py:39-47,60-71` read this session.

**Suggested fix.** Change the illustration to same-granularity —
`h.fill(graphed.nominal(sel).MET.pt, graphed.nominal(sel).MET.pt)` — or, better, to the op-level shape
the anchor actually freezes (`graphed.nominal(sel).MET.pt + graphed.nominal(sel).MET.pt`), and drop
"legal programs" for "programs this plan scopes".

### 3. MID — §6.2's "an unvaried … fill hashes exactly as today" contradicts r23's own new m50 fourth-output anchor

**Section:** §6.2 (the per-fill variation-payload paragraph), §6.2(ii), §6.1a/§6.1c's r22 keying rule,
§10/m50's MIXED-MODE anchor (r23).

**Detail.** §6.2 closes its carrier binding with: *"M29's identity discipline is preserved: the extra
content exists only in axis mode, and **an unvaried or sibling-mode fill hashes exactly as today**"*
(`:1974-1977`). r23 then adds to m50's mixed-mode anchor *"a FOURTH output — axis-mode opt-in, NO
variations — asserting its slot key is `(output, None)` and that it unpacks to a bare histogram
**carrying a 1-bin variation axis**"* (`:4191-4200`).

That output's fill is *unvaried* and *axis-mode*. Under §6.2(ii) the frontend declares the variation
axis ALWAYS in axis mode, from the inferred label set (`{"nominal"}` there — §6.1a's r22 paragraph
says exactly this), so the fill node's spec necessarily differs from today's and, since the payload
hash is `content_hash((spec, variation_payload))` in axis mode, so does the content hash. The two
sentences cannot both hold: an implementer taking §6.2's clause literally ("unvaried ⇒ hashes as
today ⇒ no variation axis in this fill's spec") produces a bare histogram with **no** variation axis
and reds the new frozen m50 assertion. This is the same class §6.2 itself flags one paragraph earlier
("an implementer taking the optional reading conforms to §6.2 and fails the frozen m50 anchor").

**Evidence.** Plan `:1974-1977` (§6.2), `:1986-1997` (§6.2(i)/(ii) fill-time always-declare),
`:1567-1573` (§6.1a r22: an axis-mode output whose fills carry no variations, inferred set
`{"nominal"}`), `:4191-4200` (m50's r23 fourth output). Probe: a 1-bin `StrCategory` fills, sums and
round-trips through `spec_of`/`zero_of` (this session), so the anchor is buildable and it is the
§6.2 sentence that is wrong.

**Suggested fix.** One word: *"an unvaried **sibling-mode** fill hashes exactly as today"* — i.e.
scope the exemption to the MODE, exactly as §6.1a/§6.1c's r22 rule already scopes the slot keying
("the MODE, not the variation count, decides").

### 4. LOW — m48's (α) anchor names an operand the object does not have: `CompiledGraph` has no `outputs()`

**Section:** §10/m48's `§7.2's r19 aggregate_plan SEAM (α)` anchor; §7.2's r20 "`CompiledGraph`, not ids".

**Detail.** The anchor reads *"the new hook fires EXACTLY ONCE and receives the `CompiledGraph` (its
`outputs()` readable inside the hook)"* (`:3399-3401`), and §7.2's r20 rationale says the merge
refusal *"needs only the COUNT of distinct compiled outputs, which `outputs()` would give"*
(`:2663-2665`). Measured against `graphed-latest@ff7c607`: `CompiledGraph` is a frozen dataclass with
fields `ir: bytes`, `source_names: tuple[str, ...]` and one method `evaluate`
(`python/graphed/execute.py:36-52`); `hasattr(compiled, "outputs")` → **False**. The working spelling
is the one §7.2 uses in its own probe elsewhere: `GraphStore.deserialize(compiled.ir).outputs()` —
verified this session on a three-output program (`[1, 2]`, reproducing §7.2's r21 probe).

The cost here is small (the test-author hits an `AttributeError` while writing, not mid-freeze), but
this plan spares that discovery everywhere else, and the same phrase drives the m48 merge-guard
implementation.

**Evidence.** Plan `:3399-3401`, `:2663-2665`, `:2722-2724` (which does spell the deserialize form);
`python/graphed/execute.py:36-52` read and probed this session.

**Suggested fix.** Replace the parenthetical with *"(the compiled outputs readable inside the hook as
`graphed.core.GraphStore.deserialize(compiled.ir).outputs()` — `CompiledGraph` itself exposes only
`ir`/`source_names`, `python/graphed/execute.py:36-45`)"*, and adjust §7.2's r20 sentence in the same
way.

### 5. LOW — r23's sequential link-composition rule for `reindex_to` is witnessed by no anchor and is not marked knowingly-unanchored

**Section:** §2.3d (`reindex_to` disposition, r23), §6.1d(B) (r23), §10/m48's lineage-seam anchor (r22).

**Detail.** r23 replaced r22's order-insensitive label expression with a **sequential** rule: *"a
mask-derivation link UNIONS that mask's labels per §2.4, a `graphed.vary` link is the IDENTITY, and a
universe/nominal PROJECTION link RESETS the accumulated label set to empty"*, explicitly because the
set expression *"diverges once links COMPOSE"*. But m48's lineage-seam anchor is split **per single
kind** (r22): *"(1) a mask-derivation link returns a `Varied` … (2) a `graphed.vary` link is the
IDENTITY … (3) a universe/nominal projection link returns an UNVARIED `Array`"* (`:3434-3445`), and
no other anchored program crosses two links of *different* kinds — m48's fill fixtures
(`h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)`, `h.fill(events.MET.pt, sel.MET.pt)`) are each a
single link. The two readings agree on every one-link path and on the natural two-link path
(mask-then-projection: both give an empty label set); they diverge only where a mask link sits
*below* a projection link (e.g. a value at the root re-indexed to `graphed.nominal(sel)[mask2]`),
which no anchor and arguably no m48–m51-scoped program builds.

That is a legitimate outcome — this plan explicitly records such rules as *"knowingly left
UNANCHORED … on §1.1's `"1e1000000000"` precedent"* (§2.2's term-(c) `vary`-link half, §6.4e's
no-private-import rule, §7.2's "MUST NOT compile a second time"). This one carries no such marker, so
the next reviewer or the m48 test-author has to re-derive that it is unwitnessable.

**Evidence.** Plan `:775-794` (§2.3d r23), `:1829-1839` (§6.1d(B) r23), `:3434-3445` (m48 anchor,
per-kind), `:1746-1752` (§6.1d's kinds (1)/(2) label-preserving note).

**Suggested fix.** One sentence in §6.1d(B) or §2.3d: the ordering half is knowingly left UNANCHORED —
the divergence needs a mask link below a projection link, which no m48–m51 program builds — on the
`"1e1000000000"` precedent. (Alternatively, add the two-link value to m48's existing fixture:
`h.fill(events.MET.pt, graphed.nominal(sel).MET.pt)`, both per-event, which at least freezes the
compose-then-project outcome.)

### 6. LOW — §9.1's `graphed.variations(ctx)` freezes assertions over "kinds", a vocabulary the plan never defines, and over an unpinned return shape

**Section:** §9.1's `graphed.variations` entry, §2.2, §10/m50's `graphed.variations` anchor.

**Detail.** §9.1 describes it as *"per-name listing of a context's registered variations, their tags
and **kinds** — and, for numeric tags …, the parsed float value"* (`:3001-3004`), and m50 freezes
*"per-name tags and kinds, plus the parsed float value under both parsers … and a non-numeric tag
(`up`) returning no value rather than raising"* (`:4294-4298`). Measured over the plan text, the word
"kind" is used nowhere else for a variation (every other occurrence is "link kind" or "NodeKey"), so
the **kind vocabulary is undefined**: is it `"weight"`/`"shift"`? the overload letter? something
else? And unlike its §9.1 neighbours the entry carries neither a return type nor a "spelling pinned at
m50 freeze" clause (contrast the §5.3 verb two lines below: `{label: tuple[str, ...] | None}`,
"spelling pinned at m49 freeze").

Consequence for the lens: m50's test-author invents both the container shape and the kind strings and
freezes them read-only, with no clause licensing the invention. It is a smaller instance of finding 1
(the §5.3-r16 defect), on a surface §6.2 depends on for numeric ordering.

**Evidence.** Plan `:3001-3004`, `:4294-4298`; `grep -n "kinds"` over the plan → only these two sites
plus "link kinds".

**Suggested fix.** Name the two kinds (`"weight"` for overload (b), `"shift"` for overload (c)), give
the verb a return type (e.g. `{name: tuple[VariationInfo, ...]}` or a plain
`{name: {tag: (kind, value|None)}}`), and add the "spelling pinned at m50 freeze" clause the rest of
§9.1 carries.

### 7. LOW — m49's §8.2(i) accessor anchor is assigned a repo but no directory, while §10 pins a directory for every other m49 anchor

**Section:** §10/m49's per-repo partition paragraph and the `§8.2(i) accessor + keying` bullet.

**Detail.** §10 states *"The per-repo partition covers EVERY m49 anchor, not only (i) and (ii)"* and
then enumerates: `graphed tests/frozen/frontend/m49` = "§5.2a arena delta, §5.2c stage shape, §3.4
impact sets, §5.3 projection, §5.4 refusal"; `graphed tests/frozen/core/m49` = "the §3.3 benchmark"
(and §5.2c adds "keeps the raw-`GraphStore` scaling benchmark **only**"); `graphed
tests/frozen/checkpoint/m49` = "§7.3 interrupt/resume and §7.4 dead-letter";
`graphed-histogram tests/frozen/m49` and `graphed-executors tests/frozen/m49` as listed. The
`§8.2(i) accessor + keying` bullet is placed only *"in `graphed`"* (`:4056`), and it straddles the
enumerated homes: the accessor half is a frontend/core-shaped `compile_ir` program, while the same
bullet's plan-byte determinism half builds a `DurablePlan` from module-level fixtures — the natural
`checkpoint/m49` shape. §10 pins directories precisely because placement is mechanically
load-bearing: `frontend` runs one pytest process **per milestone subdir** while `core`, `checkpoint`
and `preserve` run one process per package (`scripts/run-tests.sh:16-25`, `SPLIT_PKGS="frontend numpy
awkward"` at `:30`, verified this session), and the unique-basename rule is keyed on that scope.

**Evidence.** Plan `:3936-3953` (the partition), `:4056-4126` (the bullet), `:3098-3104` (the
basename rule); `graphed scripts/run-tests.sh:15-30` read this session.

**Suggested fix.** Name the directory: put the accessor+keying half in `graphed`'s
`tests/frozen/frontend/m49` and the plan-byte determinism half in `tests/frozen/checkpoint/m49`
(alongside §7.3, whose `DurablePlan`-by-value construction it shares verbatim), each under the
unique-basename rule.

### 8. NIT — m48's target line cites an anchor with no fill as evidence that m48 carries a non-empty `S`

**Section:** §10/m48 target line (r23's withdrawal of the "`|S| = 0`" justification).

**Detail.** r23 correctly withdraws r22's false "m48 has weight labels only, so `|S| = 0`", listing
*"three m48 anchors [that] carry a non-empty `S` — the four-way fold-order anchor …, §2.3b's
`plain_array[varied_mask]` entry point, and §6.1d's link-kind-(1) fixture `h.fill(events.MET.pt,
sel.MET.pt)`"*. `S` and `W` are defined by §6.1b r19 over **a fill's** labels ("the labels that
require their own SIBLING fill node — those borne by any AXIS value or by a `Varied` `sample=`"), and
§2.3b's anchor asserts only that `plain_array[varied_mask]` / `.filter(varied_mask)` return a `Varied`
— it records no fill, so `S` is undefined for it. The other two citations are correct and carry the
claim on their own.

**Evidence.** Plan `:3158-3165` (target line), `:1619-1633` (§6.1b r19's `S`/`W` definitions),
`:3574-3584` (m48's §2.3b anchor).

**Suggested fix.** Drop the §2.3b citation, or replace it with m48's corpus weight matrix, whose fills
do carry axis-borne labels.

## Verdict

**Dirty, but shallow — nothing blocks starting m48's TEST_AUTHORING.**

No BLOCKER and no HIGH. I could not find an anchor that is vacuous as worded, that a plausible wrong
implementation passes, that violates R0.10a, that breaks the determinism gate, or that freezes a
semantic a later milestone must contradict — and all four r23 changes I could settle by measurement
(the correctionlib digest, the 1-bin variation axis, the `Mean`-storage fixtures, the uproot gate
analysis) are correct and buildable. My two r22 MID findings are discharged (m51's ROOT-half gates are
now bound in §10; the type-gate citation is re-based on R0.4a and the (α) read-back route is named).

The three MIDs are of one shape — a binding statement and an anchor that disagree, or a surface a
frozen test must consume that the plan never named. Finding 1 (§3.4) is the most consequential: it is
the last unpinned public surface in a plan that has pinned every other one after a review found it,
and m49 freezes an assertion through it. Findings 2 and 3 are one-line text repairs to statements that
would send a test-author or an m50 implementer into an avoidable red. The four LOW/NIT items are
one-sentence corrections.
