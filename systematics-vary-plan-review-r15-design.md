# `systematics-vary-plan.md` — review round 7, **DESIGN SOUNDNESS** lens

- **Plan revision reviewed:** r15 (`systematics-vary-plan.md`, 3171 lines, read in full: Part I,
  PART II §§1–12, Anchors appendix, revision history r0–r15).
- **Date:** 2026-07-30.
- **Lens:** design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections; unhandled interactions; under-specified Implementation Targets; package
  boundary / factorization violations; milestone-boundary consistency. NEW-SURFACE priority:
  §2.6, §6.1d, §6.4/m51, §1.1 r9 e-canonicalization.
- **Verification roots used (fresh clones at the pinned revisions; the stale submodules in
  `/Users/lgray/vibe-coding/graphed-workdir` were NOT used for code facts):**
  - `/private/tmp/claude-501/graphed-latest` (`ff7c607`, confirmed in-session via `git log`)
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`, confirmed in-session)
  - `/private/tmp/claude-501/graphed-exec-check`, `/private/tmp/claude-501/uproot5-graphed`,
    `/private/tmp/claude-501/graphed-corpus-latest` (available; not needed for the findings below)
- **Owner-locked decisions were not relitigated.** No finding below proposes a different naming,
  surface style, encoding, attachment point, architecture, or scope choice; every one is an
  internal-consistency or implementability defect in how a locked decision is *specified*.

---

## Findings (ordered by severity)

### HIGH-1 — §9.1 / §6.4a(2a): `graphed.selection` is undefined on a **`vary`-derived** context, and the m51 entry check then refuses the plan's own mainline idiom

**Section:** §9.1 (`:1815-1824`), §6.4a(2a) (`:1434-1449`), §6.1d link-kind table (`:1139-1146`),
§2.6 sketch (`:783-786`).

**Detail.** §6.1d (r15) enumerates **three** lineage link kinds: (1) mask-derivation, (2)
`graphed.vary` (identity), (3) universe/nominal projection. §9.1 defines `graphed.selection(ctx)` as
"the `Varied` mask that derived a context from its parent (`None` for a root context)" and then, in
r15, adds a second rule for the **universe/nominal** link — closing with "One rule, stated per
lineage link kind, matching §6.1d's r15 link-kind table". But the **`vary` link kind is never
stated**, and it is the link kind the plan's own mainline sketch produces:

```
sel  = events[gak.num(jets) >= 4]                       # mask link      (:783)
sel  = graphed.vary(sel, "btag", …, is_weight=True, …)  # vary link      (:784-786)
```

After the rebind, `sel` is a `vary`-child of a mask-child. Two readings are both available and they
disagree:

- *strict* — a `vary` link carries no mask, so `graphed.selection(sel) is None`, and the m51
  canonical skim spelling `to_parquet(events.Jet, select=graphed.selection(sel))` (§6.4a `:1479-1482`)
  silently passes `select=None` for the mainline program;
- *walk-up* — return the nearest ancestral mask-derivation's mask, in which case §6.4a(2a)'s
  predicate fails anyway: it requires the mask to be `graphed.selection(c)` for a context `c` whose
  **PARENT is the record's own context handle** *and* whose link to that parent is a **MASK
  DERIVATION**. Here `c = sel`'s parent is the pre-`vary` `sel`, not `events`, so a record read from
  `events` is REFUSED — i.e. the entry check rejects the exact program §2.6's sketch teaches.

This is load-bearing rather than cosmetic: §6.4b (`:1500-1504`) says stored varied weight factors are
reached "via `graphed.weight(ctx)`", so a skim that stores varied weights is written **from a
weight-`vary`-derived context by construction**. m51's own anchor (`:2479-2483`) dodges the problem
only because it writes `sel = events[mask]` with no subsequent weight `vary`.

**Evidence.** Plan `:1139-1146` (three link kinds), `:1815-1824` (`graphed.selection` stated for the
mask link and the universe/nominal link only), `:1434-1449` (parent + MASK-DERIVATION test),
`:783-786` (the sketch rebinds `sel` through a weight `vary`), `:1500-1504` (`graphed.weight`
presupposes the weight-vary context), `:2479-2483` (the m51 bridge anchor).

**Suggested fix.** State `graphed.selection` for the third link kind and make (2a) transitive over
identity links: (a) on a `vary`-derived context, `graphed.selection` returns the selection of the
nearest ancestor reached across `vary` (identity) links only — the row space is unchanged by such a
link, so this is well-defined; (b) restate (2a) as "the supplied mask is `graphed.selection(c)` for a
context `c` reachable from the record's own context handle by **exactly one mask-derivation link plus
any number of `vary` identity links**". Add an m51 assertion writing from a weight-`vary`-derived
context (i.e. the sketch's own `sel`), since that is the shape a real skim takes.

---

### HIGH-2 — §5.2c freezes a literal on a `vary`-built program with **no oracle**, retaining the exact "re-measure at implementation time" escape r15 removed from §5.2a

**Section:** §5.2c (`:979-990`), cf. §5.2a (`:957-971`), §12.1 (`:2578-2589`), §10/m49 (`:2346`).

**Detail.** r15 corrected §5.2a because "the integer is re-measured through the frontend at freeze" is
**unfollowable — under §12.1 the test-author freezes the suite before any `vary` implementation
exists** (`:962-964`), and replaced it with a bound SPAN plus an **independent oracle** (a second
universe hand-built without `vary` in a separate Session, `:964-971`). §5.2c received the same surface
correction in r15 (it moved off the raw-`GraphStore` §3.3 fixture onto a frontend `vary`-built program
in `tests/frozen/frontend/m49`) but **kept the defective clause**:

> "the total is `stages == N + 1` (§3.3's own re-measured shape: N=16 → 17, N=128 → 129,
> **re-measured through the frontend at implementation time if the frontend construction differs**)"

The measured `17`/`129` come from the **raw `graphed.core.GraphStore`** builder (plan's own statement
at `:983-986`; anchors row `:2635`), and the frontend construction *does* differ structurally — under
record-time expansion the nominal universe is the target itself and has no fork op, so the raw
builder's per-universe node inventory is not the frontend's. The test-author must therefore freeze a
literal they cannot compute, and the escape hatch instructs a *post-freeze* re-measurement, which
under §B.6 / §12.1 is either a Test Dispute or an integrity violation (frozen tests are read-only).

**Evidence.** Plan `:957-971` (the identical defect diagnosed and fixed for §5.2a in this very
revision), `:979-990` (§5.2c retaining it), `:983-986` + `:2635` (the literal's provenance is the raw
builder), `:2346` (the m49 skeleton lists "c: reduced-stage shape" with no oracle).

**Suggested fix.** Give §5.2c the same treatment §5.2a now has: bind an **oracle** — the same N-universe
topology hand-built **without** `vary` in a separate Session, reduced, and its stage count taken as the
expected integer — and assert the `vary`-built program's stage count equals it, plus the qualitative
half ("the shared prefix appears in exactly ONE stage"). Delete the "re-measured at implementation
time" clause; nothing post-freeze may adjust a frozen literal.

---

### MID-1 — §8.2's "output-position fallback" is unimplementable for the same reason (iii) exists

**Section:** §8.2(i) fallback (`:1754-1758`), §8.2(iii) (`:1764-1781`).

**Detail.** §8.2(iii) exists because "a wrapper AROUND the call cannot produce a node id, so it cannot
index the map (i) ships" (`:1765-1768`). The stated fallback if the core accessor is descoped is to
"key on **output position** … and attribute a failure to the label(s) of **the raising output**"
(`:1755-1758`), and §8.2 further says "If (iii) is descoped, the §8.2 output-position fallback below is
promoted to the primary binding" (`:1780-1781`). Measured, that fallback needs the same missing
information: `evaluate_ir` is one flat loop over `store.nodes()` that appends into `vals` and only at
the very end selects outputs (`return [vals[o] for o in store.outputs()]`) — a failure inside the loop
carries **no node id and no output identity**, and most nodes are not outputs at all. So a bare
`except` around `evaluate_ir` cannot name "the raising output" any more than it can name the raising
node.

**Evidence.** Measured in `/private/tmp/claude-501/graphed-latest`,
`python/graphed/execute.py:96-126`: `for nd in store.nodes(): … vals.append(...)`, no `try`/`except`,
no per-node annotation, `return [vals[o] for o in store.outputs()]` at `:126`. Plan `:1764-1781`.

**Suggested fix.** Either (a) make (iii) non-optional (it is the keying event for both (i) and the
fallback), or (b) restate the fallback honestly as *plan-level*: with no per-node attribution, a worker
failure is attributed to the **union of all labels registered on that plan** (still better than nothing,
and deterministic), and say so — do not describe it as "the label(s) of the raising output".

---

### MID-2 — §2.3d's disposition CLASS SET is never enumerated; two members of its own named floor list fit none of the three classes the gate's floor names

**Section:** §2.3d (`:516-581`), §2.3e (`:598-600`), m48 anchor (`:2046-2062`).

**Detail.** The m48 gate is table-driven and asserts "every member of that union carries a disposition"
plus a floor that "contains at least one member of each disposition class **(refusing / expanding /
broadcasting)**" (`:576-581`). But the dispositions §2.3d actually assigns span more than three
vocabularies, and two members of the **named floor list** fit none of the three:

- `graphed.awkward.to_parquet` — "takes `select=` per §6.4a" (`:545-546`) — not refusing, not
  expanding, not broadcasting;
- `graphed_histogram.Histogram.fill` — "accepts `Varied` (§6)" (`:546`) — likewise;
- `graphed.context_of` — classified ***eager-metadata*** (`:598-600`), a class introduced in §2.3c for
  **gak** functions and absent from §2.3d's floor enumeration.

A test-author freezing a table-driven gate must decide what strings are legal dispositions and what
"carries a disposition" means for the two verbs above; an implementer must invent a class name for
them. Both decisions are frozen at m48.

**Evidence.** Plan `:516-581` (the enumeration and floor), `:545-546` (`to_parquet` / `Histogram.fill`
dispositions), `:598-600` (`context_of` as *eager-metadata*), `:2046-2062` (the m48 table-driven anchor
inheriting the floor).

**Suggested fix.** Enumerate the §2.3d class set explicitly and exhaustively — e.g. `{refusing,
expanding, broadcasting, eager-metadata, accepting}` — assign `to_parquet` and `Histogram.fill` to
`accepting` (the verb takes a `Varied` and handles it in its own section), and restate the floor as
"contains at least one member of each class in that set".

---

### MID-3 — §1.1's "reject a label equal to `nominal`" is unreachable under the label grammar, while §2.1 explicitly makes `nominal` a legal **tag**

**Section:** §1.1 (`:239-249`, `:318-322`), §2.1 (`:342-350`), m48 grammar anchor (`:2226-2250`).

**Detail.** §1.1 binds `label = f"{name}_{tag}"` with `name` a valid Python identifier (non-empty) and
`tag` matching `[A-Za-z0-9_]+` (non-empty). Every label therefore contains at least one `_`; the string
`"nominal"` contains none — **no input can produce a label equal to `"nominal"`**, so the listed
rejection ("`vary` MUST reject, at call time: a label equal to `"nominal"`", `:318-320`) is vacuous.
Meanwhile §2.1 states that `nominal` "is a legal §1.1 tag" that "MUST come through a mapping channel"
(`:342-347`) — i.e. `variations={"nominal": arr}` is explicitly *supported* and yields the perfectly
legal label `pu_nominal`. The m48 anchor freezes "**every listed rejection**" (`:2227`, `:2243-2249`),
so the test-author must either write an unconstructible negative case or freeze a rejection §2.1
contradicts.

**Evidence.** Plan `:239-249` (label + tag grammar), `:318-322` (the rejection list), `:342-350`
(`nominal` as a legal tag reachable only through `variations=`), `:2226-2250` (the m48 anchor's "every
listed rejection").

**Suggested fix.** Replace the unreachable clause with the reachable invariant actually intended, and
reconcile it with §2.1: either (a) drop it and state "`"nominal"` is reserved as the central *label*;
it is unreachable as a user label by construction, so there is nothing to reject", or (b) bind the
rejection at the **tag** level (`tag == "nominal"` is refused) and delete `nominal` from §2.1's list of
shadowed names that must route through `variations=`. (a) is the smaller change and matches §2.1.

---

### MID-4 — shift-after-weight: an ambient weight registered **before** a shift is never re-derived in the shifted universes, and nothing states the ordering rule or diagnoses the violation

**Section:** §2.1 stacking (`:365-382`), §2.6b (`:727-732`), §2.4 (`:677-690`).

**Detail.** §2.1(b) carefully binds the *weight-on-shift* direction: registering a weight factor on a
context that already carries shift labels combines label-aligned, so an inherited shift label L gets
`old_ambient[L] × factor[L]` — "the factor evaluated in *that label's own universe*" (`:369-379`), which
is what makes the corpus `ttbar_4j1b_jes_up` reference reproducible. The **reverse order is
unaddressed**: §2.1(c)/§2.6b say the shift form replaces the named collections and that in forms (a)/(c)
"inherited members pass through **unchanged**" (`:368-369`), and nothing touches the ambient registry.
So if a user registers a jet-dependent weight and *then* applies a JES shift, every shift universe fills
with a weight computed on **pre-shift** jets — silently, with no error and no diagnostic. This is
structurally unfixable after the fact (the registry members are already-recorded expressions rooted at
the pre-shift collection nodes), which makes it an ordering *rule* the plan must state; Part I §2 itself
records that the exemplars handle exactly this by hand ("these weights can go outside the sys loop since
they do not depend on pt of mu or jets", `:114-116`) and calls it "a human-judgement impact analysis".
Leaving it unstated in the binding half is the §2.5 confidently-wrong class the plan exists to delete —
and it is detectable with machinery the plan already scopes (§3.4 reachability: a registered factor whose
cone reaches a subsequently varied collection).

**Evidence.** Plan `:365-382` (the weight-on-shift rule, bound), `:368-369` (shift form: inherited
members unchanged), `:727-732` (§2.6b: the shift form registers nothing on the weight side), `:114-116`
(the exemplar's hand-partitioned impact analysis), `:691-697` (§2.5's validation-over-convention rule).

**Suggested fix.** Add one binding sentence to §2.1(c)/§2.6b: "A shift `vary` does NOT re-derive the
ambient weight registry; factors registered before the shift keep their pre-shift members. A weight that
depends on a varied collection MUST be registered after that collection is varied." Plus a diagnostic in
the §2.5 family (reuse §3.4's reachability): warn when a registered factor's cone reaches a collection
that a later `vary` on the same lineage replaces. Anchor the diagnostic in m49 (where §3.4 lands).

---

### MID-5 — §7.3's invalidation list omits label **renaming**, which after m49 changes every `task_id` — directly against §1.2's stated rationale

**Section:** §7.3 (`:1662-1681`), §8.2(i) (`:1708-1728`), §1.2 (`:323-331`).

**Detail.** §1.2's rationale for keeping labels out of node identity is explicit: "dedup is correct:
**renaming a systematic must not recompute**" (`:325-326`). m49's §8.2(i) then adds
`variation_labels: tuple[tuple[int, tuple[str, ...]], ...]` — **label strings** — to `_PartitionReduce`,
the plan's opaque `process` spec (`:1725-1728`). Measured, `task_id` is
`sha256(_TASK_DOMAIN, self.ir, self.process.identity(), partition_bytes)` and `OpSpec.identity()` for an
opaque spec is the cloudpickle blob itself — so after m49 a **pure rename** (IR byte-identical, per
m48's own §1.2 anchor at `:2013-2014`) changes every `task_id` and invalidates every cached partition.
§7.3 documents two invalidation classes honestly (adding/removing a variation; the one-time all-programs
churn on landing m49/m51) and misses this third one, which is the one §1.2 promised would not happen.

**Evidence.** Measured in `graphed-latest`, `python/graphed/core/plan.py:164-176`
(`task_id` folds `self.process.identity()`) and `:72-76` (`identity()` returns the opaque blob bytes).
Plan `:325-326` (§1.2's rationale), `:1708-1728` (label strings in the closure), `:1662-1681` (§7.3's
list), `:2013-2014` (the m48 anchor that keeps renaming IR-neutral).

**Suggested fix.** Add one sentence to §7.3's documented-limitation paragraph (and to the m50 docs
anchor): "From m49, a label RENAME also changes the worker closure and therefore every `task_id`, even
though the IR is byte-identical — §1.2's no-recompute property holds at the IR/interning level, not at
checkpoint granularity." Consider noting that stage-granular content addressing (§11) removes this too.

---

### MID-6 — m48 targets "§6.1" wholesale, which drags §6.1c's **axis-mode** slot binding into a milestone whose frozen suite cannot exercise it

**Section:** §10/m48 targets (`:1907-1912`), §6.1c axis-mode slot (`:1089-1099`), §10/m50 targets
(`:2383-2385`), cf. the r14 precedent for §3.4 (`:1918-1922`).

**Detail.** §6.1c's r15 paragraph binds the axis-mode slot — "an axis-mode output contributes exactly
ONE slot, keyed `(output, None)` … the per-slot VALUE TYPE is recorded in the layout and the combine
branches on it" — and carries **no milestone scoping**, while m48's target line names "§6.1 (incl.
§6.1d ambient fills)" and m50's names only "§6.2, §9.1's `graphed.variations`, §9.2". Axis mode does not
exist until m50, so an implementer reading m48's target line lands the value-type branch and the
`(output, None)` slot in m48 with **zero m48 frozen coverage** — which fails the DoD's ≥90 % diff
coverage *from the frozen suite*, or is covered only by `tests/extra`, which that gate excludes. This is
verbatim the reasoning r14 used to move §3.4 out of m48's targets (`:1918-1922`); the same rule was not
applied here. Conversely, m50's anchors *do* depend on the axis-mode slot (the scaling anchor is worded
over it, `:2432-2444`) while m50's target line does not name §6.1c.

**Evidence.** Plan `:1089-1099` (unscoped axis-mode slot binding), `:1907-1912` (m48 targets),
`:2383-2385` (m50 targets), `:2432-2444` (m50's scaling anchor consuming §6.1c r15), `:1918-1922`
(the r14 precedent, same argument).

**Suggested fix.** Scope §6.1c's axis-mode paragraph "(m50, with §6.2)" and add §6.1c's axis-mode half to
m50's target line, exactly as §6.1a/§6.1b already carry sibling-mode scoping. m48 then implements only
the sibling `{(output, label): [indices]}` layout its anchors exercise.

---

### LOW-1 — §7.1's "No per-variation execution loop may be introduced **anywhere**" collides with §6.2's evaluator-side weight loop

**Section:** §7.1 (`:1642-1644`), §6.2 (`:1225-1231`).

**Detail.** §7.1 is absolute; §6.2 lands weight labels "in ONE histogram … via an **evaluator-side
loop** (extend/sibling `FillEvaluator`)". Read literally, m50's headline mechanism violates an m49
requirement. The intent is clearly "no re-execution of the graph/plan per variation", but the sentence
as written is the kind an integrity reviewer will cite.

**Suggested fix.** Scope it: "No per-variation re-execution of the graph or the plan may be introduced
anywhere; §6.2's evaluator-side loop *inside one fill node* is not such a loop."

---

### LOW-2 — §2.6a leaves context `[]` with a **slice or int** undefined, though it says it mirrors `Array.__getitem__`

**Section:** §2.6a (`:716-719`).

**Detail.** §2.6a binds `[]` with `str`/`list[str]` (tree content) and `[]` with an `Array`/`Varied`
mask (derived context), "mirroring `Array.__getitem__`'s own mask-vs-field split". Measured,
`Array.__getitem__` also accepts a `slice` (recording a boundary `slice` reduction) and an `int`
(`index`), and raises `TypeError` otherwise. `events[:1000]` on a context is therefore an expressible
thing to type with no bound answer, and m48 freezes context semantics.

**Evidence.** Measured, `graphed-latest` `python/graphed/array.py:344-371`: `Array`/`str`/`list[str]`/
`slice`/`int` branches, final `raise TypeError(f"unsupported index …")`.

**Suggested fix.** One clause in §2.6a: a slice or int subscript on a context is REFUSED with an error
naming the supported forms (row-slicing an event context has no defined effect on the ambient registry's
re-indexing rule), or is defined as a derivation link like a mask. Refusal is the smaller commitment.

---

### LOW-3 — §6.3(2)'s seam-scoping and §6.1d's "every weight factor is broadcast" leave the contexted-but-unvaried fill undecided

**Section:** §6.3 (`:1357-1364`), §6.1d (`:1166-1179`).

**Detail.** §6.1d binds "**Every** weight factor the fill applies — the ambient one AND explicit
`weight=[...]` factors — is broadcast to the fill's value structure", with the measured reason that an
unbroadcast per-event explicit factor length-mismatches in a per-object fill. §6.3(2) then scopes the
recorded seam: "a fill with NO context handle and NO `Varied` input records byte-identically to today,
i.e. the recorded `graphed.broadcast_like` node is inserted **only on the varied/ambient path**". The two
scopings are not the same: a fill that HAS a context handle but no ambient registrations and no `Varied`
input (a data context, or an MC context before any `vary`) with an explicit per-event factor against a
per-object value falls inside "no varied/ambient path" but outside "no handle and no `Varied` input" —
so whether it gets the seam, and therefore whether it runs at all, depends on which sentence the
implementer follows.

**Suggested fix.** State one trigger: "the seam is recorded for every factor of a fill that carries a
context handle **or** any `Varied` input; a fill with neither records byte-identically to today" — and
let §6.3's golden be exactly that latter case (which it already is).

---

### LOW-4 — §2.3e(3)'s membership floor cites a "§5.4 boundary set" that is never enumerated, and (4) inherits clauses that do not apply to the `Array` surface

**Section:** §2.3e(3)-(4) (`:663-673`), m48 anchor (`:2127-2130`), §2.3c (`:512-514`).

**Detail.** The r15 membership floor asserts "the *refusing* class is exactly the bound **§5.4 boundary
set**". §5.4 defines a *condition* (a variation cone crossing an `Exchange`/`Join`), not a set of
function names; §2.3c defines the gak refusing class as "`gak.join` and boundary verbs, per §5.4". A
frozen assertion needs the name set. Measured, gak's public surface (65 functions) contains exactly one
boundary verb, `join` — there is no `repartition`/`exchange`/`pack_key` in gak — so the intended operand
is `{gak.join}`, but the plan never says so. §2.3e(4) then says "the `Array` public surface of (a) is
gated the same way", inheriting a floor whose other clauses do not transfer: `Array`'s refusing member is
`repartition` (not a "§5.4 boundary set"), and "every *eager-metadata* member's return annotation is
non-`Array`" is false for `Array` methods generally.

**Evidence.** Measured in `graphed-latest`: `grep -n "^def " python/graphed/awkward/functions.py`
public names — the only boundary verb is `join` (`functions.py:18`); no `repartition`/`exchange`/
`pack_key` among them. Plan `:512-514`, `:663-673`, `:2127-2130`.

**Suggested fix.** Enumerate the operand where it is asserted: "the *refusing* class is exactly
`{gak.join}` at freeze time (grow only with a new gak boundary verb)", and give §2.3e(4) its own
one-line floor for the `Array` surface (`{repartition}` refusing; broadcast count ≥ freeze-time count)
rather than "gated the same way".

---

## Areas probed and found clean (for the record)

- **§1.1 e-canonicalization (r9).** Probed exact-decimal normalization (`"2"`/`"2.0"`/`"2e0"`/`"20e-1"`
  → `2`), minimal-mantissa rendering, integer vs fractional dispatch, negative zero, non-minimal
  canonical re-rendering (`"50em2"` → `5em1`, `"05"` → `5`), the 32-char cap and its explicit
  non-coverage of the label / on-disk name, the large-magnitude-integer refusal path, cross-notation
  numeric-equality rejection against the datacard p-form, and the three tag channels (kwargs,
  `variations=`, shift-form inner keys). The grammar is closed and self-consistent; identifier-safety
  of `f"{name}_{tag}"` holds for digit-leading tags because `name` leads. No design defect — the one
  issue I found in §1.1 is the unreachable `"nominal"`-label rejection (MID-3), which is a rejection-list
  defect, not an encoding defect.
- **§2.4 label-aligned union vs §2.6c lineage unification.** Checked the interaction at a fill: a
  derived context's collections are all `Varied` when the derivation mask is (`:746-752`), so mask labels
  reach the fill's label set through value-borne labels regardless of whether the union is computed
  before or after §6.1d's ancestor re-indexing. No ordering hole.
- **§2.1 stacking vs the context shift form.** The corpus b-tag-on-JES case, the "new label's member is
  the provided value's central universe" rule, and the one-at-a-time invariant compose correctly in both
  the weight and shift overloads. (The *unhandled* direction is MID-4.)
- **§6.4c/§6.4d structure + XOR-delta.** Widest-common-structure storage, per-level packed masks, the
  same-offsets refusal, and bit-exact reconstruction (`nominal ^ delta`, then the per-label level-1 and
  level-0 masks) are mutually consistent, and the level-per-`select=` channel is what makes the jagged
  object-migration case expressible. §6.4c's `_WritePart` encoding site is consistent with §6.4f's marked
  outputs being the per-label values/masks.
- **§5.4 boundary refusal vs §6.4 write plans.** No conflict: write plans are `write_plan`-built and the
  §5.4 refusal is a cone-crossing condition; the §2.3d refusal of `graphed.repartition(varied)` and
  §2.3a's *refusing* disposition for `Varied.repartition` agree.
- **Package boundaries / factorization.** `graphed.broadcast_like` neutral + backend-dispatched with a
  bound numpy no-op; §6.2(i-bis)'s duck-typed `.axes` detection and `axis.index(label)` keep
  `boost_histogram` out of `graphed`; `graphed.awkward.read_varied`/`to_parquet` stay awkward-idiom;
  `graphed-histogram` gains no awkward runtime dep; the only core change is a read-only accessor with
  §3.1 re-worded to "no optimizer SEMANTICS change". Clean — no boundary violation found.
- **Owner-locked decisions.** Nothing in PART II contradicts them; §2.2's `Varied.apply` method is not
  an introspection verb and does not breach the module-function rule.

---

## Verdict

**DIRTY.** Two HIGH findings — one that leaves the m51 write sink unreachable from the plan's own
mainline context idiom (HIGH-1), one that hands the m49 test-author a frozen literal they cannot compute
and an instruction to re-measure after freeze (HIGH-2) — plus six MID defects, of which MID-2, MID-3 and
MID-6 land directly in frozen m48 material and MID-4 is a physics-silent-wrong hazard on the new context
surface. None require reversing an owner-locked decision; all have local fixes. The new surfaces this
round was asked to probe hardest (§2.6, §6.1d, §6.4/m51, §1.1) are otherwise in better shape than the
finding count suggests: §1.1 and the §6.4 structure/reconstruction rules survived close reading intact,
and every remaining defect is a missing *statement*, not a broken design.
