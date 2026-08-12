# `systematics-vary-plan.md` r24 — review round 16, DESIGN SOUNDNESS lens

- **Lens:** design soundness — is PART II a coherent, implementable specification? Internal
  contradictions, unhandled interactions, under-specified Implementation Targets, package-boundary
  violations, milestone-boundary consistency. Deepest attention (per the round brief) on the
  newest surfaces: §2.6 functional context, §6.1d, §6.4/m51, §1.1's r9 e-canonicalization.
- **Plan revision reviewed:** r24 (whole document read: PART I, every PART II section, §10–§12,
  the anchors appendix, and the r24/r23 revision-history entries).
- **Date:** 2026-07-30.
- **Verification roots used** (every code fact below was read or run by me in this session; nothing
  is taken from the plan's own citations):
  - `/private/tmp/claude-501/graphed-latest` — consolidated `graphed` @ `ff7c607`
  - `/private/tmp/claude-501/graphed-histogram-latest` — `graphed-histogram` @ `211cbbe`
  - (`graphed-exec-check`, `graphed-corpus-latest`, `uproot5-graphed`, `prior-art/*`,
    `coffea-workdir` were available; no finding below needed them)
- **Owner-locked decisions** were treated as fixed. Nothing below asks for a different choice on
  naming, the functional surface, e-form canonicalization, event-context attachment, record-time
  expansion, m48–m51 scope, or the Phase-2 pull-in; every finding is about how the plan *specifies*
  what it has already decided.

Seven findings: 2 HIGH, 3 MID, 2 LOW. No BLOCKER — nothing in m48–m51 is unimplementable or
self-contradictory in a way that cannot be repaired by a bounded edit, and no finding contradicts
an owner-locked decision.

---

## HIGH-1 — §8.2(i)'s record→reduced accessor has NO bound carrier to its only consumer, and m48 freezes the hook shape that would have carried it

**Section:** §7.2 (the `aggregate_plan` seam, halves (α)/(β)) × §8.2(i) (the m49 core accessor) ×
§10/m48's (α) anchor.

**Detail.** The r19–r24 chain is: m48 adds a hook on `aggregate_plan`; the hook is *called with the
`CompiledGraph`* and its **return value** becomes `_PartitionReduce.variation_labels` (§7.2, "the
hook is called with the `CompiledGraph` before the worker closure is constructed, and its RETURN
VALUE … is attached to the shipped closure"). m49 then populates that field, whose keys are
`(reduced_node_id, member_index)` "obtained from the m49 core accessor, which answers *for the
reduction that produced a given compiled artifact*" (§7.2's own justification for passing the whole
artifact rather than an id list; §8.2(i) binds the accessor).

Measured, the artifact cannot answer that question, and no other channel is bound:

- `CompiledGraph` is `ir: bytes` + `source_names: tuple[str, ...]`, one method `evaluate`
  (`graphed-latest python/graphed/execute.py:36-52`). The plan itself measured this twice; what it
  did not do is close the loop.
- The reduction runs **inside** `compile_ir` (`execute.py:70-80`: `session._store.reduce(...)[0]
  .serialize()` / `session._reducer.finalize(...)[0].serialize()`), and only the serialized bytes
  escape.
- The core reduce entry point returns `(PyGraphStore, HashMap<String, usize>)` — the reduced store
  plus a **count report**, no id table (`src/lib.rs:365-381`, `reduce_incremental` `:387-399`,
  `reduction_report` `:403-415`). The `remap` vector is local to
  `dead_code_elimination`; only the outputs' images escape (`src/optimizer/mod.rs:88-116`,
  `let out_idx = …; (kept, out_idx)` at `:114-115`).

So the m49 hook that must produce `variation_labels` has: the labels and record ids (from
`plan()`), and `compiled.ir`. It has no record→reduced map and no way to obtain one. The three
conceivable carriers are each either unbound or foreclosed by this plan:

1. **An additive `CompiledGraph` field** — permitted (§2.5 already uses exactly this shape for the
   unreached-label diagnostic, and notes m48's §7.2 schema anchor is worded over
   `ExecResult`/`Plan`/monitor, *not* `CompiledGraph`) — but **nowhere bound** for §8.2(i).
2. **A second reduction inside the hook** (`session._store.<accessor>(outputs=ids)`) — deterministic
   and therefore correct, but it is precisely the doubled reduction §7.2 forbids one paragraph later
   ("`plan()` MUST NOT compile a second time: the §3.3 anti-quadratic budget is written for ONE
   reduction of the variation-expanded graph").
3. **Serializing the map into the IR** so `GraphStore.deserialize(compiled.ir)` can answer — barred
   by §3.1 ("no serialize tag").

The freeze-order consequence is the trap §7.2 r20 closed on the *ids-vs-artifact* axis and left open
one level down: m48's frozen (α) anchor fixes the hook's operand list — "the new hook fires EXACTLY
ONCE and receives the `CompiledGraph`", and explicitly "the hook receives only the `CompiledGraph`
and has no handle on the closure" (§10/m48). A frozen test supplying `lambda compiled: ()` makes any
m49 attempt to call `hook(compiled, remap)` a `TypeError` against a read-only test — resolvable only
by Test Dispute. This is the third recurrence of the defect class the plan already repaired twice
("the channel it named does not exist" — r10's withdrawal of r9's transport sentence, r12's
withdrawal of r11's key space).

**Suggested fix.** Bind the carrier at **m48**, in §8.2(i) and in §7.2's (α)/(β) text, and word
m48's (α) anchor so the frozen hook signature admits it. The smallest choice consistent with this
plan's own precedent is an **additive `CompiledGraph` field** carrying the reduction's
`record_node_id -> (reduced_node_id, member_index | None)` map (populated at m49; `None`/absent at
m48), since §2.5 already establishes `CompiledGraph` as an additive channel outside m48's schema
anchor — and then §7.2's "the artifact, not an id list" rationale becomes true as stated. If a
second hook parameter is preferred instead, m48's anchor must freeze the two-parameter shape now.

---

## HIGH-2 — §6.1c's `.plan()` refusal states a false equivalence; the "equivalently" predicate excludes m48's own exercised arm

**Section:** §6.1c (`.plan()` refusal), r24 re-keying; §10/m48's `.plan()`-refusal anchor.

**Detail.** §6.1c binds: "**`.plan()` raises — pointing at the group API — on a `Histogram` that is
VARIED *or* in §6.2 AXIS MODE** (equivalently: whose staged fill nodes' spec differs from the
`__init__`-time `self._spec`)."

The parenthetical is not equivalent — it is false for every **varied sibling-mode** histogram, which
is exactly the arm m48 exercises. Measured at `graphed-histogram@211cbbe`:

- `Histogram.__init__` sets `self._spec = spec_of(self)` (`src/graphed_histogram/boost.py:148`).
- **Every** `fill` bakes that same object into the node: `chash = content_hash(self._spec)` and
  `params={"spec": self._spec, "n_axes": …, "weighted": …, "sampled": …}`
  (`boost.py:180-212`). Nothing per-fill enters the spec today.
- In sibling mode nothing may change that: §1.2 keeps labels out of params/hashes (its m48 anchor
  freezes it), and §6.3's frozen params key set is the literal
  `{"spec", "n_axes", "weighted", "sampled"}`.

So a varied sibling-mode histogram's staged fill nodes carry a spec **identical** to
`self._spec`, and the parenthetical predicate is `False` for it. The parenthetical is correct only
for axis mode, where §6.2(i) declares the variation axis at FILL time — which is precisely why r24
introduced it.

Consequence: m48's anchor tells the test-author to "word the anchor over the predicate, not over
'varied' alone", and §6.1c offers two mutually exclusive readings of "the predicate". An implementer
who implements the parenthetical (the operational one — it needs no varied-ness tracking on the
histogram) ships code that lets a varied sibling-mode `.plan()` through into `_SumFills`, which
silently merges universes — the exact hazard the refusal exists to prevent — and reds m48's frozen
anchor mid-milestone.

**Suggested fix.** Delete "equivalently" and state it as a disjunction with two distinct tests:
`.plan()` raises when the histogram carries any varied fill (frontend-tracked) **or** when any
staged fill node's spec differs from the `__init__`-time `self._spec` (the axis-mode arm). Keep
m48's varied-arm anchor and m50's axis-mode arm as they are — both are then covered by one
requirement whose two clauses are independent, not "equivalent".

---

## MID-1 — after r24's bare depth-`k` key, §6.4a's level-≥1 depth and structural predicates still have no operand for the plan's own canonical skim

**Section:** §6.4a — (2c) generalized depth check, and the "Levels ≥ 1 … STRUCTURAL" predicate;
interaction with §6.4a's r24 exception and §6.4d.

**Detail.** r24 admits a **bare depth-`k`** `select=` key "where the level-k structure is the
RECORD'S OWN", precisely so §6.4's canonical single-collection skim
(`to_parquet(events.Jet, select={0: event_mask, 1: jet_mask})`, form `var * {pt, eta}`) has a legal
object-level spelling. r24 swept the *storage* sentence ("stored against that entry's FIELD (against
the record's own axis at that depth for a bare depth-`k` entry, r24)") and §6.4d. It did **not**
sweep the two validating predicates, which still read:

- (2c), r22: "a mask supplied at level k MUST have depth k over the record's structure — **over the
  NAMED FIELD for a level-k ≥ 1 entry**";
- "Levels ≥ 1 — … the check is STRUCTURAL: each per-label member of the mask must carry **that NAMED
  FIELD's own offsets at that depth** … and the packed per-label mask is stored against that field."

For a bare depth-`k` entry there is no named field, so both binding predicates have no operand for
the very program r24 opened them to. §6.4d even records the symptom ("the single-collection skim
`to_parquet(events.Jet, …)`, where the field-scoped rule below has no operand") without repairing
§6.4a. m51's entry-check anchors are worded over §6.4a's predicates, and the canonical skim is m51's
positive control, so a test-author has to invent the missing operand and freeze the invention.

**Suggested fix.** One clause in each predicate: for a bare depth-`k` entry, both the depth check and
the per-label offsets check run **against the record's own structure/offsets at depth `k`**, which
r24's own legality condition ("the record is itself jagged at depth `k` — its own offsets, all
fields inside them") makes single-valued by construction; the packed mask is stored against that
axis. Nothing else moves.

---

## MID-2 — §2.3d's "EXHAUSTIVE" Array-consuming surface excludes `graphed.numpy`'s module verbs, while r24 makes the numpy idiom a first-class `Varied` carrier

**Section:** §2.3d (module-verb dispositions + the m48 exhaustiveness gate) × §2.2 r24 (per-idiom
`Varied`) × §6.1d (numpy no-op broadcast seam) × §10/m48 (numpy-idiom property fixture).

**Detail.** §2.3d calls its enumeration "EXHAUSTIVE over `graphed`'s public Array-consuming surface"
and binds a discovery rule over **`graphed.__all__`** (plus a named floor list). gak gets its own
dynamic gate over `graphed.awkward.functions` (§2.3c, 65 functions), and `graphed.awkward.to_parquet`
gets an explicit table entry at m51 — so idiom-package verbs *are* in scope for dispositions when the
plan notices them. `graphed.numpy`'s module surface is noticed nowhere.

Measured at `graphed-latest@ff7c607`, `graphed.numpy.__all__`
(`python/graphed/numpy/__init__.py:578-601`) contains at least six **Array-consuming** public verbs
with no disposition and no gate:

- `full_like(array, fill_value)`, `ones_like(array)`, `zeros_like(array)`, `empty_like(array)` —
  each `array.session.record_op(...)` (`python/graphed/numpy/creation.py:77-91`);
- `project(array, *, on_fail="raise")` (`python/graphed/numpy/projection.py:40`);
- `apply_gufunc(fn, signature, *arrays: NumpyArray, output_dtype, name=None)`
  (`python/graphed/numpy/gufunc.py:74-90`, `session = arrays[0].session`).

This is not an idle surface for this plan: r24 bindingly makes `graphed.numpy` supply the numpy-idiom
`Varied` subclass; §10 pins the property-classification fixture to a numpy 1-D partitioned source;
§6.1d binds the numpy `broadcast_like` as a NO-OP *"precisely so an all-numpy varied fill works"*;
and §6.4f disposes the numpy-idiom write function at m51. A numpy-idiom user therefore gets a
first-class `Varied` and then hands it to `gnp.full_like` — the numpy twin of the *binding* §4.1
constant-weight form `gak.full_like` — where behaviour is unbound. (The failure is at least loud
rather than silent, because §2.2's reserved-name rule makes `varied.session` raise
`AttributeError`; but that is an accident of the reserved-name rule, not a bound contract, and the
message points at the wrong thing.)

**Suggested fix.** Either (a) extend §2.3d with a one-line rule that `graphed.numpy`'s public
Array-consuming verbs carry the same disposition classes, discovered the same way over
`graphed.numpy.__all__`, with the m48 gate run per idiom package (`*_like`/`project`/`apply_gufunc`
→ *broadcast*/*expanding* as appropriate); or (b) state explicitly that the numpy idiom's **module**
verbs are out of v1 scope and that a `Varied` reaching them raises §2.2's `AttributeError` — and say
so where §4.1 names `gak.full_like`, since that is where a numpy user looks.

---

## MID-3 — §6.1d's binding fill-unification/divergence enumeration omits `sample=`, which the same section makes a first-class labelled input

**Section:** §6.1d (fill-time context unification / divergence / ancestor re-indexing) × §6.1b r19
(`S` includes sample-borne labels) × §6.1d r15 (sample folds last).

**Detail.** §6.1d's rationale names the right operand set — "it is the first place independent
axis/**weight**/**sample** handles meet (`boost.py:154-212` collects them into one `inputs` list…)" —
but the binding sentence that follows enumerates only three: "so the fill runs the same most-derived
unification and divergence check across **all axis values, all explicit weight factors, and the
winning context's ambient weight**." The ancestor-value re-indexing rule is written over "every
ancestor-context VALUE" with the same three worked operands.

`sample=` is elsewhere bindingly first-class: §6.1d r15 fixes it LAST in the fold order precisely
because §2.3d binds `Histogram.fill` to accept a `Varied`; §6.1b r19 puts a sample-borne label in
`S`; m48 freezes a four-way fold-order anchor *including* a varied `sample=`; m50's equality anchor
turns on a sample-only label. Measured, today's `fill` type-checks `args` and `weights` and appends
`sample` to the same `inputs` list with **no check at all**
(`graphed-histogram@211cbbe src/graphed_histogram/boost.py:160-178`) — i.e. the one input for which
nothing upstream would catch a divergent handle.

Consequence: a `sample=` read through a divergent context is not refused by any bound rule; it
either dies at execution with a length error whose message is about the wrong thing, or — when the
row counts coincide — silently samples the wrong universe's rows. That is the §2.5
confidently-wrong class the whole unification rule exists to delete.

**Suggested fix.** Add `sample=` to both enumerations: the fill unifies and divergence-checks across
*axis values, explicit weight factors, `sample=`, and the winning context's ambient weight*, and an
ancestor-context `sample=` is re-indexed like any other ancestor value. (The broadcast seam's
scoping to weight factors is deliberate and should stay as is.) m48's existing four-way fold anchor
can carry the divergence control at no extra fixture cost.

---

## LOW-1 — m49's target line takes `§7` wholesale while §7.2 is bound to m48

**Section:** §10/m49 target line vs §10/m48 target line.

**Detail.** m48's line bindingly targets "**§7.2** (… including §7.2's r19 `aggregate_plan` SEAM …)
— … §7.1/§7.3/§7.4 stay m49". m49's line reads "Targets: §3.3, §3.4 (frozen anchor), §5, **§7**, §8
— EXCEPT §8.2(i)'s … FIELD DECLARATION". Read literally, §7.2 is a target of both milestones. This
is the same defect class §10 annotates explicitly four other times (§3.4 → m49, §2.5's diagnostic →
m49, §6.1c's axis slot → m50, `to_parquet` → m51, and r23's `§8 — EXCEPT …`), and the DoD's "targets
exactly as specified" check is what it feeds.

**Suggested fix.** `§7 — EXCEPT §7.2, which lands at m48 (§10/m48)`, mirroring the `§8` treatment.

---

## LOW-2 — §3.4's r24 operand phrase names two incompatible operand shapes

**Section:** §3.4 (impact-set API, shaped in r24) and its §9.1 entry.

**Detail.** r24 binds the impact verb as "a **read-only `graphed` module verb over the same operands
as `read_columns`/`graphed.labels`**, returning `{label: tuple[int, ...]}`". Those two are not one
operand shape: measured, `read_columns(arrays: Sequence[Array], source_nid: int)` takes a *sequence
plus a required source id* (`graphed-latest python/graphed/projection.py:109`), while
`graphed.labels(x)` takes a single object (§2.2's four input shapes). An impact set needs no
`source_nid` (it is pure reachability), so the two references pull in opposite directions, and m49
freezes membership assertions read through this verb. §5.3's projection-stats verb does not have the
ambiguity — it *applies* `read_columns` per label, so `read_columns`' operands are the right ones
there; §3.4 inherited the phrase without that justification.

**Suggested fix.** Name one shape. The natural one is `graphed.labels`': a single `Varied`/context
(or a sequence of varied outputs) — no `source_nid` — with the spelling pinned at m49 freeze as
already stated.

---

## Verdict

**Dirty** — but narrowly, and none of it touches an owner-locked decision.

- **HIGH-1** is the one finding that would bite hard if it survives: m49's §8.2 transport chain has
  no operand at the site the plan bindingly assigns it, and m48's frozen hook shape is what
  forecloses the natural repair. It needs a sentence in §8.2(i)/§7.2 **and** a wording change in
  m48's (α) anchor, i.e. it must be fixed before m48 freezes, not before m49 starts.
- **HIGH-2** is a one-word repair ("equivalently" → a disjunction) but must land before m48's
  test-author writes the `.plan()`-refusal anchor.
- The three MIDs are bounded sweeps (one clause each in §6.4a; one rule or one exclusion for
  `graphed.numpy`; one operand added to §6.1d's enumeration).
- The two LOWs are annotation hygiene of the kind §10 already applies elsewhere.

Everything else I probed in the priority areas held up under adversarial reading, and is worth
recording as *clean* so a later round does not re-litigate it: §2.1's r24 two-level `factor[L]`
resolution is correct against the corpus semantics (b-tag central SF on JES-shifted, JES-selected
jets) and keeps the composed ambient flat; §2.6b's canonical-pure-derivation rule closes the
handle-identity hole without breaking §2.3e's divergence rule (`vary` stays fresh); §2.6c's per-label
row sets compose consistently with §2.1(b)'s row-space rule and §6.4b's storability precondition;
§6.1a/§6.1c's three slot key forms are disjoint and per output, so the unpacker is well-defined in a
mixed plan and the m23 frozen suite stays green; §6.1c's index-based `layout` is derivable exactly
where the plan says it is (`fill_nodes` built at `graphed-histogram boost.py:281`, one line before
`layout` at `:282`, five before `aggregate_plan` at `:286`, and `aggregate_plan(*fill_nodes)` is
called with that same ordered list); §6.2's axis mode is combine-safe under §6.1c's per-slot
fill-node spec and the cross-fill agreement rule; §1.1's e-canonicalization arithmetic checks out on
every boundary I recomputed (`"1.5e31"` → 32 digits, `"-1.5e31"` → 33 rendered characters and hence
the length message, `"0.5"` → `5em1` under both the normalized-count and rendered-length rules,
negative zero → `0`); and §6.4a's five/six entry-check controls all decide as the plan claims under
the r23 `vary`-identity-link admission. No package-boundary violation was found: `graphed` proper
imports no `boost_histogram` (§6.2(3) duck-typing) and no awkward (§6.1d's neutral
`broadcast_like`), `graphed-histogram` gains no awkward dependency, the r24 per-idiom `Varied`
mirrors the shipped `Session._array_cls` seam (`python/graphed/session.py:36-39`) and keeps
numpy-idiom names out of `graphed` proper, and no requirement puts a label into `NodeKey`
params/hashes outside §1.2's own §6.2 carve-out.
