# systematics-vary-plan — review round 8, TEST ARCHITECTURE lens

- **Plan revision reviewed:** r16 (`systematics-vary-plan.md`, 3516 lines, read in full: header, Part I,
  every PART II section §1–§12, §10 milestone anchors m48–m51, Anchors appendix, revision history r16/r15/r14).
- **Lens:** test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), no wall-clock or
  size thresholds in frozen tests (R0.10a), determinism-gate compatibility, freeze-order hazards,
  traceability (requirement ↔ anchor, both directions), and testability-as-stated (can the test-author
  actually build the fixture from what the plan gives).
- **Date:** 2026-07-30.
- **Verification roots used** (all code facts below were read or executed by me in this session, never
  taken from the plan's own citation):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, verified `git log -1` → `ff7c607a8ba637ebc1b5db37316adf6e10028dcc`), including its working `.venv` (used for a live reducer probe).
  - `/private/tmp/claude-501/graphed-histogram-latest`.
  - `/Users/lgray/vibe-coding/graphed-workdir/systematics-vary-plan.md` (the document under review).
- **Owner-locked decisions** (naming, functional surface, e-form encoding, event-context attachment,
  record-time expansion, m48–m51 scope incl. §6.4, the Phase-2 pull-in) were treated as fixed. No finding
  below asks for a different choice; each is about how a frozen anchor is *specified*.

---

## Summary

The suite skeleton is in good shape. Seven review rounds have removed the classic traps this lens hunts
for: the equal-counts tautology (§4.3), the self-derived delta (§5.2a), the dynamic-discovery-returns-empty
vacuity (§2.3a/c/d floors), positional `layout` mis-slicing (§6.1c), the `bh.loc`/`h.axes.name` oracles that
raise against a correct implementation (§6.2 i-bis), the committed-`.parquet` golden that R0.10a forbids
(§6.4g), and — new in r16 — two genuinely load-bearing repairs: **§4.3's withdrawn intersection predicate**
(I confirmed it is satisfied by construction: `Histogram.fill` builds `inputs = list(args)` then
`inputs.extend(weights)` and records ONE External node, `graphed-histogram src/graphed_histogram/boost.py:176-212`,
so `reachable(selection_mask) ⊆ reachable(fill[L])` always, and its replacement — `inputs[:n_axes]` identity
against nominal — *is* directly readable, since `n_axes` really is a recorded param, `boost.py:180-212`, and
the m29 frozen precedent already reads node dicts that way, `tests/frozen/m29/test_multi_weight_fills.py:84-86`);
and **§10/m49's JER-SF oracle** (I confirmed `Session.materialize(self, array)` takes no partition,
`python/graphed/session.py:291-301`, while `SequentialRunner.run` folds `sorted(plan.tasks, key=lambda t: t.key)`,
`python/graphed/core/execution.py:450-457`, and `aggregate_plan(*outputs, reduce=…, combine=…, empty=…)`
accepts a user reduce/combine, `python/graphed/aggregate.py:67-107` — so the bound plan-run oracle is buildable
and the partition-invariance witness can actually observe `steps_per_file`).

I also probe-verified that r16's new §8.2(i) topology extension is satisfiable: a node consumed by two
NON-nominal universes survives reduction as ONE reduced id rather than being duplicated into both universes'
stages (probe below). That anchor is sound.

Eight findings remain — **0 BLOCKER, 0 HIGH, 5 MID, 3 LOW**. Four are traceability gaps (a binding rule with
no anchor, or an anchor placed where it will `importorskip`-SKIP), one is a spec contradiction a test-author
must resolve before writing an m49 assertion, one is a freeze-order hazard, two are non-vacuity/wording.

---

## Findings

### MID-1 — §8.2(i)'s declared `variation_labels` type contradicts the key space (iii) and m49's anchor look it up by

**Section:** §8.2(i)/(iii); m49 anchor "§8.2(i) accessor + keying, in `graphed`".

**Detail.** §8.2(i) declares the transported field as
`variation_labels: tuple[tuple[int, tuple[str, ...]], ...]` (plan `:1874`) — an **int**-keyed association list.
Two paragraphs later the same section binds "The map keys on `(reduced_node_id, member_index)` accordingly"
(`:1919-1920`), and (iii) binds the hook to annotate a failure with `(reduced_node_id, member_index | None)`
and says "`_PartitionReduce` maps **that** through `variation_labels`" (`:1948-1949`). A pair cannot be looked
up in an int-keyed table. r16's own new anchor text reaches into this shape directly: "that node maps to ONE
reduced id **whose `variation_labels` entry** carries BOTH labels" (`:2624-2631`) — so the m49 test-author must
know whether an entry is keyed by `int` or by `(int, int | None)` in order to spell the assertion, and freezes
whichever they guess read-only.

The member half is not cosmetic. Measured (probe below), a universe's chain collapses into a `stage` node whose
members are evaluated inline, so most varied record nodes have no reduced id of their own — which is exactly
why §8.2(i) introduced `member_index` in the first place.

**Evidence (mine).** Plan `:1874`, `:1919-1920`, `:1948-1949`, `:2624-2631`. Reducer shape re-measured this
session in `/private/tmp/claude-501/graphed-latest` (`.venv`, `graphed.core.GraphStore`): a 3-universe topology
reduces to `source`, four `stage` nodes and three `reduction`s; each stage carries its chain as inline
`members` with `('member', i)` input tags.

**Suggested fix.** State one key space in both places — e.g.
`variation_labels: tuple[tuple[tuple[int, int | None], tuple[str, ...]], ...]` (pair key, sorted, still no
`set`/`frozenset` so §8.2(i)'s determinism argument is untouched) — and re-word the m49 bullet as "the map
entry keyed `(reduced_id, member_index)` carries BOTH labels".

---

### MID-2 — m50's plan-level `{output: [labels]}` anchor is placed in a repo that cannot host it without `importorskip`

**Section:** §9.1 (r16 addition); m50 anchor "**§9.1's plan-level `{output: [labels]}` listing, its OWN anchor**"
(`:2727-2732`), placed "in `graphed`'s `tests/frozen/preserve/m50`".

**Detail.** r16 correctly removed this from the `inspect()` test (`inspect(bundle: Bundle) -> str`, which I
verified at `python/graphed/preserve/bundle.py:268-288` — takes a bundle, returns a string). But the replacement
anchor is *fill-shaped*: the notion of a named **output** exists only in `graphed-histogram`'s group API —
`plan(histograms: Mapping[str, Histogram] | Sequence[Histogram])` builds
`items = [(str(k), v) …]` and `layout = tuple((label, len(h._fill_nodes), h._spec) for label, h in items)`
(`graphed-histogram src/graphed_histogram/boost.py:256-292`); `graphed`'s own `aggregate_plan(*outputs: Array, …)`
has no output names at all (`python/graphed/aggregate.py:67-107`). The anchor's own wording confirms the tie:
"the unvaried output maps to the empty/`["nominal"]` shape **§6.1a's bare-`hist` rule** implies".

Placed in `graphed`, the fixture needs `graphed_histogram`, which `graphed` declares in **no** extra — I read
`graphed pyproject.toml:29-48` (`dev` = pytest/mypy/ruff/numpy/awkward/pyarrow/**boost-histogram**/hist/…; the
only `graphed_histogram` string in that file is a mypy override at `:91`), while CI installs `.[dev]`
(`.github/workflows/ci.yml:34`), and the house pattern is `gh = pytest.importorskip("graphed_histogram")`
(`tests/frozen/preserve/m25/test_histogram_preservation.py:31`). So the anchor SKIPs in CI — the exact defect
class r16 fixed twice elsewhere (m48's §2.3d floor, m49's matrix).

**Suggested fix.** Either move this anchor to `graphed-histogram`'s flat `tests/frozen/m50` (m50 already lists
both repos), or bind the verb's operand so it is exercisable in `graphed` alone (e.g. it takes the frontend's
`(output, label) → node id` map keyed by names the caller supplies) and re-word the anchor without the
`§6.1a bare-hist` dependence.

---

### MID-3 — §2.3e(2)'s "frozen test owns the contexted operand" rule is unsatisfiable for the container-traversing class

**Section:** §2.3e(2) (r16); m48 anchor "§2.3e context-handle propagation is a SEPARATE, SCOPED gate".

**Detail.** r16 closed a real hole (an implementer-written `src` fixture supplying a context-free primary
operand degrades the assertion to `None == None`) by giving the frozen test ownership of the contexted operand:
"the frozen test constructs the context and substitutes its own contexted `Array` into the **primary operand
position**; `src` fixtures supply only the auxiliary/typed operands the measured surface needs (**`zip`'s
mapping**, `concatenate`'s second array, `unflatten`'s counts, `where`'s branches, `linear_fit`'s operands)"
(plan `:716-724`).

For the *container-traversing* class the two halves collide: `gak.zip`'s mapping **is** its primary (and only)
array-bearing operand, and the plan assigns it to the fixture. The frozen test then has no position to
substitute into, the contexted array can only arrive from implementer-editable `src`, and the `None == None`
degradation survives for precisely the class whose purpose is detecting containers. The same ambiguity applies
to `linear_fit`, whose "operands" are all fixture-supplied.

**Evidence (mine).** Plan `:710-724` and the m48 bullet `:2342-2352`. `gak.zip` is
`python/graphed/awkward/functions.py:118` (mapping-first), consistent with the plan's own classification.

**Suggested fix.** Bind the fixture as a **template with a named substitution slot** (a sentinel the frozen
test replaces, including *inside* a Mapping/Sequence argument), and add one assertion that the substitution
actually happened (e.g. the fixture declares its slot path and the gate asserts the produced call graph's
handle-bearing input is the test's own `Array`).

---

### MID-4 — two r15/r16 bindings about universe/nominal-derived contexts in the m51 sink have no anchor

**Section:** §9.1 (`graphed.selection` on a universe/nominal-derived context, r15, `:1992-1997`); §6.4a(2a)
("Links of the universe/nominal projection kind are NOT admitted", r15, `:1581-1585`); m51 anchor list
(`:2760-2794`).

**Detail.** Both rules are binding, both name their failure case explicitly, and neither is anchored:

1. §9.1 binds a **type-changing** answer: on a context produced by `graphed.universe`/`graphed.nominal`,
   `graphed.selection` returns "that label's member of the argument's own selection — an unvaried `Array`, not
   a `Varied`, living in the GRANDparent's row space". `graphed.selection` lands in m51 (`:806-807`, `:2112`).
2. §6.4a(2a) binds that `select=graphed.selection(graphed.nominal(ctx))` on a record read from `ctx` must be
   **refused** at record time, with the stated reason that a bare parent test would accept it.

I grepped every `graphed.selection` occurrence in the document (lines 434, 806, 1120, 1556, 1564, 1578, 1583,
1586-1589, 1623-1626, 1979, 1989-2001, 2112, 2760-2792, 3016, 3114). The m51 anchors cover exactly three cases:
the mask-derived bridge, the ROOT-context `None`, and (new in r16) the `vary`-derived case. The
universe/nominal case appears in neither the bridge anchor nor the entry-check anchor (whose "chained-context"
positive is `sel2 = sel[mask2]`, a *second mask* link, not a projection link).

Consequence: a refusal path plus a polymorphic return, both new m51 source, land with zero frozen-suite
coverage — which the DoD's ≥90 % diff-coverage-**from-the-frozen-suite** gate is supposed to catch and which
this plan has treated as a defect five times already (§5.3, §2.5, §3.4, §2.3b, §2.5 diagnostic).

**Suggested fix.** Add to m51's bridge anchor: `graphed.selection(graphed.nominal(sel))` returns an unvaried
`Array` in the grandparent row space; and to the entry-check anchor: passing that value as `select=` for a
record read from `sel` is refused by (2a), naming both contexts.

---

### MID-5 — m48 freezes `graphed.awkward.to_parquet` as the *accepting*-class representative, a classification that is false until m51

**Section:** §2.3d disposition class set (r16, `:585-589`); m48 anchor `:2269-2285`.

**Detail.** r16 enumerated the class set (refusing / expanding / broadcasting / eager-metadata / **accepting**)
and, to keep `graphed`'s table-driven test out of `importorskip` territory, made
`graphed.awkward.to_parquet` the *accepting* representative in `graphed`'s floor list — "the *accepting*
class's representative in `graphed`'s half is `graphed.awkward.to_parquet`" (`:2284-2285`), where *accepting*
means "the verb consumes a `Varied` operand and handles it internally" (`:588-589`), realised by
"`to_parquet` takes `select=` per §6.4a" (`:581-582`).

But `select=` and every varied-write semantic is **§6.4, an m51 target** (`:2743`). At m48 there is no varied
`to_parquet`; handing it a `Varied` falls through into the awkward writer. So m48's gate certifies a `src`
classification table asserting that a verb *accepts* containers when it does not — a green gate over a
confidently-wrong entry, the class §2.5 exists to delete, frozen read-only for three milestones.

**Suggested fix.** Classify `to_parquet` as *refusing* at m48 (a clear error naming m51/`select=`) and flip it
to *accepting* in m51 — or state explicitly in the m48 bullet that the *accepting* floor member is a
**metadata-only** entry at m48 whose behaviour is anchored in m51, and pick a floor representative whose m48
behaviour is real (`Histogram.fill`, already asserted in `graphed-histogram`'s half, is the natural one for that
repo's floor; `graphed`'s half then has no accepting member and the floor should say so).

---

### LOW-1 — §2.6a's new slice/int context-subscript refusal has no m48 anchor

**Section:** §2.6a (r16, `:798-803`); m48 anchor list.

**Detail.** r16 added a binding refusal: "**A `slice` or `int` subscript on a CONTEXT is REFUSED**, naming the
supported forms", justified by `Array.__getitem__` accepting both (`python/graphed/array.py:344-371`). I
grepped the whole document for `slice`: the only occurrences inside §10's anchor lists are none — every hit is
in PART II or the appendix (lines 511/517/798/800/803/881-882/1206-1210/1422-1459/2697-2702/2914/2957). m48's
context anchors cover mask-vs-string subscription and reserved names, not the slice/int branch. New source,
zero frozen coverage.

**Suggested fix.** One clause in m48's §2.6/§6.1d bullet: `sel = events[0:1000]` and `events[0]` each raise,
naming the supported subscript forms, with the existing mask/string positives as controls.

---

### LOW-2 — §6.3's params-key-absence half is under-determined (and vacuous) at m48

**Section:** §6.3 (`:1485-1500`); m48 anchor "§6.3 goldens (committed GIR blob + params-key absence)".

**Detail.** §6.3 spells the pattern as `assert "<new key>" not in node["params"]` — a placeholder. The cited
precedent works because M29 had a *known* new key: `assert "n_weights" not in node["params"]`
(`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:93-95`, read this session). m48 in sibling mode
adds **no** params key by design (§1.2 keeps labels out of params), so the test-author has no key name to
spell; any invented name makes the assertion pass tautologically regardless of implementation. (The committed
GIR golden in the same bullet does cover the property, so this is redundancy rather than a hole — but a frozen
tautology is still a frozen tautology, and the m50 declaration anchor already had to be repaired for the same
"never read the expected value back from the object under test" reason.)

**Suggested fix.** Word it as a **key-set equality against a literally spelled expected set**:
`set(node["params"]) == {"spec", "n_axes", "weighted", "sampled"}` for the unvaried single-weight fill (I
verified those are exactly the keys recorded, with `n_weights` added only when `len(weights) > 1`,
`graphed-histogram src/graphed_histogram/boost.py:180-212`).

---

### LOW-3 — §1.1's integer-magnitude rejection message is unanchored; m48 freezes only the generic length rejection

**Section:** §1.1 (r13 clause, `:262-267`); m48 grammar anchor (`:2478-2481`).

**Detail.** §1.1 binds **two distinct** rejections around the 32-character cap: a generic canonical-tag-length
rejection, and — for an integer-valued input whose plain-digit rendering exceeds the cap, e.g. `"1e40"` → 41
digits — a rejection "**at canonicalization with a message naming the magnitude**, not with a generic
tag-length error". The m48 anchor freezes only "a >32-character canonical tag rejected (§1.1 r10)". An
implementation emitting the generic message for both passes the anchor while violating the binding sentence —
the same shape r15 repaired for §6.1d's loose-value message.

**Suggested fix.** Add `"1e40"` (integer-valued, over-cap) to the m48 grammar anchor with the magnitude-naming
message assertion alongside the existing `"1e-8"` → `eps_1em8` positive.

---

## Clean under this lens (checked, no finding)

- **R0.10a.** Exactly one wall-clock gate is frozen — §3.3's `time(128)/time(16) < 24.0` — and it is named as a
  deliberate carve-out discharging the project plan's M4 mandate, with measured headroom (≈5.4×). Every other
  performance claim (§6.2 axis scaling, §6.4c compression, the m50 object-count half) is demoted to an R0.11
  implementer report. No size threshold appears in any frozen anchor; m51's compression anchors are structural
  (representation + manifest), not size-based.
- **Determinism-gate compatibility.** m48 (IR bytes, two fresh processes, differing `PYTHONHASHSEED`), m49
  (`DurablePlan.to_bytes()` + per-partition `task_id` with the §8.2(i) field present), m51 (manifest bytes)
  form a complete ladder; the sorted-tuple/sorted-manifest-key rules are each observable by exactly one of
  them. §5.5's byte-identity claim is correctly narrowed to partition-local smeared values and masks rather
  than a weighted float histogram.
- **§4.3.** The r16 replacement predicate is directly readable and discriminating: I confirmed
  `inputs = list(args); inputs.extend(weights); if sample is not None: inputs.append(sample)` and
  `params["n_axes"] = len(args)` (`graphed-histogram src/graphed_histogram/boost.py:176-212`), so
  `inputs[:n_axes]` is exactly the axis-arg prefix and a `mask_L = mask & g_L` implementation changes those ids.
  The withdrawal of the r12–r15 intersection form is correct (containment holds in any implementation that
  fills selected data, so the intersection is constant).
- **§5.2a/§5.2c oracles.** Both are now independent hand-built constructions in a separate `Session`, runnable
  at freeze time before any `vary` exists, with the post-freeze "re-measure through the frontend" escape
  deleted. `Session.node_count()` exists (`python/graphed/session.py:50-51`) and is the right span reader.
- **m49 §8.2(i)'s r16 topology extension is satisfiable.** I built the exact shape it asks for — a derived node
  consumed by two NON-nominal universes and not by nominal — in `/private/tmp/claude-501/graphed-latest`
  (`.venv`, `graphed.core.GraphStore`; nominal chain off the source, `shift` off the source feeding an `up`
  chain and a `down` chain, all three reductions marked as outputs). Result: 15 record nodes reduce to 8, the
  shared `shift` node becomes **its own stage** (`id 3`, one member) consumed by both universes' stages — it is
  **not** duplicated into both, so "maps to ONE reduced id" holds against this reducer. Incidentally this also
  reproduces the plan's `stages == N+1` / `reduced == 2N+2` shape at N=3 (4 stages, 8 nodes).
- **Fixture buildability spot-checks.** `aggregate_plan` accepts user `reduce`/`combine`/`empty`
  (`python/graphed/aggregate.py:67-107`) so §5.5's plan-run oracle and m49's concatenating witnesses are
  writable; `SequentialRunner` folds in sorted task order (`core/execution.py:450-457`) so the concatenation is
  deterministic; `graphed.apply` records a user callable as one External node
  (`python/graphed/array.py:397-410`) so the JER-SF content-seeded draw fixture has a recording route without a
  new gak verb; `store.nodes()` yields dicts whose `id` is the enumeration index (`src/lib.rs:274-281`) so the
  §4.3/§1.2 node-dict reads work, and cross-package `session._store` access is already frozen house practice
  (`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84`).
- **Freeze-order sweep.** No anchor still describes r8-era p-form canonicalization: m48's grammar anchor,
  §6.4b's on-disk example and m51's numeric-tag anchor all use the r9 e-form (`murf_5em1`), and m50's
  `graphed.variations` anchor correctly requires *both* parsers (e-form canonical + p-form legacy). r16's
  removal of the unconstructible `label == "nominal"` rejection is right and the m48 anchor now says so
  explicitly. Sibling-vs-axis scoping is consistently applied to every count-bearing anchor (§6.1a, §6.1b,
  §1.2, m50's slot count), so m50 lands no feature contradicting an m49-frozen count.
- **Traceability sweep (requirement → anchor).** Every binding PART II clause I enumerated maps to at least one
  m48–m51 anchor except the four named in MID-4, MID-2 and LOW-1/LOW-3. No orphan anchors: every m48–m51 bullet
  traces back to a §-numbered requirement.

---

## Verdict

**DIRTY — but narrowly.** No BLOCKER, no HIGH. The five MID findings are all specification-level and each has a
one-to-three-line fix: one key-space contradiction (MID-1), two anchor placements/scopes that would silently
SKIP or certify a false classification (MID-2, MID-5), one gate rule that does not cover its own hardest class
(MID-3), and one pair of unanchored bindings (MID-4). The three LOWs are wording. Nothing here requires
reversing an owner-locked decision, and nothing blocks the m48 test-author on the plan's headline anchors — the
grammar, matrix, label-out-of-identity, `.plan()` refusal, stacking, dispositions, context/fill, determinism
and golden anchors are all non-vacuous, mechanism-witnessing and buildable as written.
