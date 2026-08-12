# systematics-vary-plan review — round 14, lens: DESIGN SOUNDNESS

- **Plan revision reviewed:** r22 (`systematics-vary-plan.md`, 5356 lines, read in full: header, PART I,
  every PART II section §1–§12, §10 milestone anchor lists, Anchors appendix, revision history r22–r16).
- **Lens:** design soundness — is PART II a coherent, implementable specification? Contradictions between
  sections, unhandled interactions, under-specified Implementation Targets, package-boundary/factorization
  violations, milestone-boundary consistency. Depth priority as briefed: §2.6 functional context, §6.1d,
  §6.4/m51, §1.1 r9 e-canonicalization.
- **Date:** 2026-07-30.
- **Verification roots used:** `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, verified
  `git log -1` → `ff7c607a8ba637ebc1b5db37316adf6e10028dcc`) — used to re-measure `to_parquet`'s
  compile-at-the-call claim (`python/graphed/awkward/io.py:230-231`, read directly). Every other finding
  below is an *internal* consistency defect whose evidence is the plan text itself; those are cited by
  `systematics-vary-plan.md:<line>` and were read this session, not recalled. Roots
  `graphed-exec-check`, `graphed-histogram-latest`, `uproot5-graphed`, `graphed-corpus-latest`,
  `prior-art/*`, `coffea-workdir` were available but not needed for this lens' findings; I make no claim
  that rests on them.
- **Owner-locked decisions** (naming, functional surface, e-form canonical encoding, event-context
  attachment, record-time expansion, m48–m51 scope incl. §6.4, JER-SF non-monotonicity, the Phase-2
  pull-in) are **not** relitigated below. Where a finding touches one, it is about how the plan
  *specifies* it, never about the choice.

---

## Findings

### 1. HIGH — Context handle IDENTITY is never defined, while a hard error and a record-time write refusal both hinge on it

**Section:** §2.2 / §2.6b / §2.3e / §6.1d(A) / §6.4a(2a).

**Detail.** The whole §2.6 functional idiom is built on context objects related by *lineage links*, and
three binding rules compare handles:

- §2.3e (`systematics-vary-plan.md:941-943`): "inputs whose handles lie on ONE ancestry chain propagate
  the most-derived handle; handles on divergent branches are an **error** at that op naming both."
- §6.1d(A) (`:1770-1773`): `graphed.unify_contexts(*handles)` "returns the most-derived handle when the
  non-`None` arguments lie on ONE ancestry chain … and **raises** the §2.3e divergence error … otherwise."
- §6.4a(2a) (`:2178-2179`): "the supplied mask's own §2.3e context handle MUST EQUAL the record's context
  handle — **`graphed.context_of(select_mask) is graphed.context_of(record)`**" — an explicit `is`
  comparison.

Nothing in §2.2, §2.6b or §2.3e says whether two contexts produced by *equivalent* operations are the same
handle. `graphed.nominal(ctx)` and `graphed.universe(ctx, label)` are **pure projections** that §2.2
(`:565-571`) binds to "return a CONTEXT — a CHILD of the argument"; `ctx[mask]` (§2.6a `:1084`) is likewise
a pure derivation. The natural implementation returns a fresh object per call, and then two calls that a
physicist reads as naming *one* universe are two **siblings** — neither an ancestor of the other — so the
divergence rule fires on legal programs:

```python
sel = events[mask]
a = graphed.nominal(sel).MET.pt      # handle: child#1 of sel
b = graphed.nominal(sel).Jet.pt      # handle: child#2 of sel  -> divergent!
h.fill(a, b)                          # or  a + b  (raises at the OP, §2.3e)
```

and identically for `sel1 = events[mask]; sel2 = events[mask]`. This is a *false refusal* — the inverse of
the "confidently wrong" class §2.5 exists to delete, and equally damaging because the diagnostic
("divergent contexts") names a condition the user's program does not contain.

The `is`-predicate in §6.4a(2a) makes the gap sharper rather than incidental: the plan has already
committed to object identity in one place, and its own m51 re-recorded-mask control turns on the
*handle* being the same object while the mask expression is re-recorded (`:2196-2197`).

No m48 anchor closes it: the divergence anchor's positive control is "an ancestor-chain pair unifies
silently to the most-derived context" (`:3606-3607`), which is a different shape. An implementer must
guess, and both guesses are defensible — the exact freeze hazard the plan repairs elsewhere (§6.1a's
result shape, §2.5's diagnostic channel, §5.3's stats verb).

**Evidence.** `systematics-vary-plan.md:565-571` (universe/nominal return a CHILD), `:941-943` (divergence
at the op), `:1084` (mask subscript derives a context), `:1770-1773` (`unify_contexts` raises on divergent),
`:2178-2179` (`is` comparison), `:3606-3607` (m48's only divergence positive control). Grep over the whole
plan for `same object|object identity|memoi|canonical context` returns only `:195` (prose about r5's mutable
registry) and `:4838` (a *withdrawn* r17 rule about **mask** identity, superseded in r19) — there is no
context-identity rule anywhere.

**Suggested fix.** Bind context identity once, in §2.6b, next to "Each returned context links to its
parent". The lazy, sufficient rule: **pure derivations are canonical** — `graphed.nominal(c)`,
`graphed.universe(c, L)` and `c[mask]` for the *same* mask node id return the *same* context object
(memoised on the parent), so equivalent spellings are one handle; `graphed.vary` always returns a fresh
context (each call registers different content), which keeps §2.3e's divergence rule meaningful for the
case it was written for. Alternatively, define unification over *structural* lineage equality rather than
object identity — but then §6.4a(2a)'s `is` must be re-spelled in the same terms, and m51's re-recorded-mask
control re-verified against it. Either way, state which, and add an m48 assertion that two separate
`graphed.nominal(sel)` reads unify instead of raising.

---

### 2. MID — §6.4a(2a)'s r19 handle-equality predicate is strictly NARROWER than the r16 rule it claims to preserve; the "vary links become automatic" justification is false

**Section:** §6.4a(2a).

**Detail.** r16 admitted the mask being `graphed.selection(c)` for a context `c` reachable from the
record's context "by exactly one MASK DERIVATION plus **any number of `vary` links**"
(`:2155-2158`), with the explicit rationale that "`vary` links do not move the row space, §6.1d link kind
(2), so admitting them changes nothing the predicate is protecting" (`:2148-2149`). r19 replaced the
predicate with handle equality and asserts: "**The r16 admission of any number of `vary` IDENTITY links
becomes automatic — a `vary` link does not change which context a read was performed through**"
(`:2192-2193`).

That sentence is false under the plan's own §2.3e **ORIGINATION** rule (`:937-939`): "every `Array`/`Varied`
a context produces — its own root wrapper and every read performed through it — carries **THAT** context's
handle, overriding whatever the input merge would yield". A read through `E2 = graphed.vary(E1, …)` carries
`E2`, a read through `E1` carries `E1`; they are *different handles* in the *same* row space. So handle
equality refuses exactly the configuration r16 admitted:

```python
E1  = gnano.events(src)
E2  = graphed.vary(E1, "pu", pu_nom, is_weight=True, up=…, down=…)
mask = gak.num(E2.Jet) >= 4          # read through E2  -> handle E2
sel  = E2[mask]
graphed.awkward.to_parquet(E1.Jet, select=graphed.selection(sel))
#   record handle E1, mask handle E2  ->  REFUSED by (2a)
#   r16's rule: sel is reachable from E1 by one vary link + one mask derivation -> ACCEPTED
```

The row space of `E1.Jet` and of `mask` is identical (vary is §6.1d link kind (2), IDENTITY), so the refusal
protects nothing — it is the "hard-block a legal skim spelling read-only" defect r20 fixed for absent-operand
case (ii) (`:2211-2219`), re-introduced one clause up. None of the four (r19) or five (r20) verified m51
controls exercises it — m51's `vary`-derived-context anchor (`:4175-4181`) puts the `vary` link *below* the
mask derivation, where the mask still carries the record's handle — so it will not be caught at freeze
either. The same clause's closing sentence, "A record read from an ancestor or a sibling context is refused"
(`:2198`), is a second statement of the narrowed rule and inherits the problem.

**Evidence.** `systematics-vary-plan.md:2143-2158` (the r16 rule and its rationale), `:2178-2182` (r19's
replacement), `:2192-2193` (the false "becomes automatic" claim), `:2198`, `:937-939` (ORIGINATION),
`:1746-1747` (§6.1d link kind (2) = IDENTITY), `:4175-4181` (m51's `vary` anchor, which does not
discriminate).

**Suggested fix.** Restate (2a) as: `graphed.context_of(select_mask)` **is, or is reachable from,**
`graphed.context_of(record)` **across `vary` IDENTITY links only** — one upward walk over the lineage the
plan already retains, in either direction, refusing on any mask-derivation or universe/nominal link. Then
withdraw the "becomes automatic" sentence and re-verify the five controls (all five still decide the same
way). Add the discriminating program above as m51's sixth control, or state explicitly that the vary-link
admission is dropped and delete r16's rationale — but do not keep both.

---

### 3. MID — `unweighted=True`'s effect on the fill's LABEL SET is unbound; m48 freezes the resulting shape

**Section:** §6.1d.

**Detail.** §6.1d binds the fill's label set as "the §2.4 union of value-borne labels, **ambient-weight
labels**, and explicit `weight=[...]` factor labels" (`:1699-1701`). r19 then binds `unweighted=True` to
suppress "the AMBIENT weight **and** any explicit `weight=[…]`" (`:1729-1731`). What it does to the *label
set* is never stated. Two defensible readings:

- **(A)** the labels still enter the union — a contexted fill with `pu_up`/`pu_down` registered yields
  `{nominal, pu_up, pu_down}`, three histograms with **identical** contents (no weight is applied);
- **(B)** suppressed weights contribute no labels — the fill is unvaried and §6.1a's **bare `hist`** applies.

These are different frozen result shapes under §6.1a, and m48 freezes the anchor: "`unweighted=True` in
§6.1d's r19 bound form — it suppresses the AMBIENT weight AND any explicit `weight=[…]` (a contexted fill
with registrations yields **counts equal to an unweighted eager reference**)" (`:3683-3686`). That wording
is satisfied by both readings — under (A) every label's histogram equals the reference. So the anchor does
not settle it, and a test-author's pick is frozen read-only for three milestones.

This is precisely the ambiguity r21 closed one clause earlier for the projection link — §6.1d r21 ordered
label inference AFTER the lineage step so a kind-(3) value "contributes NO labels", and m48's
`graphed.nominal(sel)` fixture asserts a BARE `hist` explicitly because otherwise "the fixture has two
defensible result shapes (`{label: hist}` with per-universe-identical contents being the other) and the
test-author's pick is frozen read-only" (`:3677-3682`). The identical argument applies verbatim here, and
reading (A) is the "labels kept, contents identical" implementation r21 names as the thing to discriminate
against.

**Evidence.** `systematics-vary-plan.md:1699-1701`, `:1724-1733`, `:3683-3686`; the parallel repair at
`:1700-1710` and `:3677-3682`.

**Suggested fix.** One sentence in §6.1d beside the `unweighted=True` binding: a suppressed weight
contributes **no labels** — the label set is computed over the factors the fill actually applies — so a
contexted `unweighted=True` fill whose only variation source is the ambient registry is UNVARIED and
returns a bare `hist` (§6.1a). Word m48's anchor over that shape, which also makes it the discriminator
against reading (A).

---

### 4. MID — §6.4a's "one entry per level that varies" contradicts r22's own FIELD-SCOPED level-k keys

**Section:** §6.4a / §6.4d.

**Detail.** r22 made level-k ≥ 1 `select=` entries field-scoped (`{0: evt, ("Jet", 1): jet_mask}`) with the
stated motivation that a per-depth-only key "is not single-valued for … a record carrying **two jagged
collections (Jet + Muon**, a JES shift moving only Jet), which has two distinct depth-1 offset arrays"
(`:2085-2090`). But the sentence the change amends still reads: "it accepts either a single `Varied` row
mask, or an ordered **per-depth** mapping of `Varied` masks — `{0: event_mask, ("Jet", 1): jet_mask, …}` —
**one entry per level that varies**" (`:2078-2080`), and three lines later "it stores **one packed per-label
validity mask per supplied level**, level 0 included" (`:2097-2098`).

Under field scoping the invariant is one entry **per (field, level)**, and the Jet+Muon record the
rationale names *requires* two depth-1 entries. As written, an implementer building a validation from
`:2080` refuses the exact program r22 exists to enable, and a test-author reading `:2097` stores one mask
per depth instead of one per entry. §6.4d's r22 sentence is already written the right way ("a field
shallower than a supplied level, or at that depth under a different field path, is unaffected by it",
`:2374-2377`), so the two paragraphs now disagree.

**Evidence.** `systematics-vary-plan.md:2078-2080` (stale "one entry per level"), `:2085-2090` (the r22
rationale that requires two depth-1 entries), `:2097-2098` (stale "per supplied level" for the stored
masks), `:2374-2377` (§6.4d's correct field-scoped wording).

**Suggested fix.** Replace "one entry per level that varies" with "one entry per (field path, level) that
varies; level 0 is keyed by the bare depth `0`", drop "ordered per-depth", and change "one packed per-label
validity mask per supplied **level**" to "per supplied **entry**, stored against that entry's field
(level 0 against the row axis)". No anchor changes: m51's fixtures use a single depth-1 entry either way.

---

### 5. MID — §1.1's family-check example and m48's grammar anchor are spelled in a call shape §2.1 REJECTS

**Section:** §1.1 (family definition) / §2.1(c) / §10 m48 grammar anchor.

**Detail.** §1.1's r17 family rule illustrates the cross-notation hazard with
`vary(ctx, "murf", variations={"0.5": a})` followed by `vary(ctx, "murf", variations={"0p5": b})`
(`:336-338`), and m48's grammar anchor freezes exactly that pair as a rejection, repeating the same
spelling (`:3710-3711`). But §2.1 binds three overloads over the signature
`vary(target, name, /, nominal=None, *, is_weight=False, variations=None, collections=None, **tags)`, and
for an **event-context target with no `is_weight`** the call is overload (c), the shift form, in which
"**`variations=` is REJECTED … with an error naming `collections=`**" (`:405-406`). So the anchor's own
fixture, read literally (`ctx` = an event context, which is what the identifier says everywhere else in this
plan), is refused by a *different* rule before the family check can run — the frozen test would be asserting
the wrong rejection, or the test-author has to guess which of three repairs was meant (make the target a
loose `Varied` per overload (a); add `is_weight=True` plus a central factor per overload (b); or route the
tags through `collections=`).

A secondary under-specification rides along: §1.1 defines a family as "the set of tags carried by one `name`
on one **container**" (`:339-340`), and §2.2 binds the per-`name` retained tag map on **`Varied`**
(`:515-521`). For a context target the map lives on the ambient-weight `Varied` (overload (b)) or on the
replaced collections (overload (c)) — implementable, but never said, and the m48 anchor is the only place
the context case is exercised.

**Evidence.** `systematics-vary-plan.md:336-338`, `:3710-3711` (the fixture spelling), `:405-406` (§2.1(c)
refuses `variations=`), `:456-460` (overload (c) is "no `is_weight`"), `:339-343` (family = tags on one
container), `:515-521` (the retained map is bound on `Varied`).

**Suggested fix.** Spell the fixture in a legal overload in both places, e.g. overload (b):
`vary(ctx, "murf", w_nom, is_weight=True, variations={"0.5": a})` then
`vary(ctx, "murf", w_nom, is_weight=True, variations={"0p5": b})` — the weight form is the one the μR/μF
family actually uses. Add one clause to §1.1 or §2.2 stating where a context's per-`name` tag map lives
(the ambient registry for weight families, the replaced collections for shift families), so the family check
has a named operand for a context target at m48, one milestone before `graphed.variations(ctx)` exports it.

---

### 6. MID — r22's m48/m49 milestone correction for §8.2(i)'s closure field is incompletely propagated: it is on no target line, and m48's own §7.2 anchor still attributes the change to m49

**Section:** §7.2 / §8.2(i) / §7.3 / §10 m48 + m49 target lines.

**Detail.** r22 corrected the milestone: §7.2 binds "**The field therefore EXISTS from m48**" (`:2574`), and
§7.3 (`:2719-2732`) and m50's docs anchor (`:4127-4133`) were both re-scoped to m48. Two consumers of that
correction were not updated:

1. **No milestone target line names it.** m48's targets (`:3039-3069`) run §1, §2, §3.2, §4, §6.1, §6.3,
   §7.2, §9.1-partially — §8 appears nowhere. m49's target line takes "**§8**" wholesale (`:3752`). So a
   reviewer checking the DoD's "targets exactly as specified" reads the §8.2(i) field as m49 work, while
   §7.2 bindingly requires it at m48 and m48's own (α) anchor freezes a returned dummy `()` being readable
   off the shipped closure (`:3283-3287`) — which is unimplementable without the field. This is verbatim the
   defect class §10 repairs four times by annotation (r13 for m48's §9 verbs, r18 for m51's
   `graphed.selection`, r19 for §2.5's diagnostic, r20 for m49's stats verb and seam half (β)), each time
   with the same justification: "the DoD scopes an implementer off the target line".
2. **m48's §7.2 schema-absence anchor still says m49.** `:3466-3468`: "Worded over key sets, NOT over plan
   bytes or the `process` spec — **m49's** §8.2(i) closure field changes those by design (§7.2, §7.3)."
   After r22 the `process` spec changes at **m48** — that is the whole content of the churn correction and
   the measured basis for it (`:4485`, the `8d058bf867dc6bcd` vs `22a566276fd6077d` digest pair). The
   anchor's rationale now names the wrong milestone in the very milestone it is frozen in.

**Evidence.** `systematics-vary-plan.md:2565-2575` (field type + "EXISTS from m48"), `:3039-3069` (m48
targets, no §8), `:3752` (m49 targets, "§8"), `:3283-3287` (m48's (α) dummy assertion), `:3466-3468` (stale
m49 attribution), `:2719-2732` + `:4485` (the r22 churn correction and its measurement).

**Suggested fix.** Add to m48's target line: "**plus §8.2(i)'s `variation_labels` FIELD DECLARATION only**
(`tuple[…] | None = None`, unpopulated — it is §7.2's (β) return channel and m48's (α) anchor reads it;
§8.2(i)'s accessor, keying and population stay m49)", and annotate m49's "§8" as "**except the field
declaration, which lands at m48**". Re-word `:3467` to "the §8.2(i) closure field, added at m48 and
populated at m49, changes those by design".

---

### 7. LOW — §2.3d's one-line `reindex_to` label rule is order-insensitive; §6.1d(B) composes links in lineage ORDER

**Section:** §2.3d / §6.1d(B) / §6.1d link kinds.

**Detail.** r22 binds `graphed.reindex_to` as broadcasting with "the §2.4 UNION of the value's labels and
the intervening MASK-DERIVATION links' labels, **MINUS every label eliminated by a universe/nominal
PROJECTION link on the path**" (`:762-768`, restated `:1780-1786`). Stated as a set expression it is
order-insensitive, but the operation is not: §6.1d binds "Links compose in **lineage order**,
parent-to-child" (`:1750-1751`), and a projection link annihilates everything accumulated *above* it while
leaving mask-derivation links *below* it free to re-introduce labels. For the path
`events →(mask, Varied) sel →(nominal projection) nom →(mask2, Varied) sel3`, the sequential semantics give
`mask2`'s labels; the set expression gives `(mask ∪ mask2) − mask` = `mask2` here by coincidence, but for
`mask2` sharing a label name with `mask` the two differ, and for a projection link *below* the last mask the
subtraction over-fires. The composed path is expressible (§2.6a admits `[]`-with-mask on any context,
including a `graphed.nominal(...)` one), and m48's lineage-seam anchor is split **per single link kind**
(`:3302-3312`), so no anchor exercises composition and no frozen test would catch the divergence.

**Evidence.** `systematics-vary-plan.md:762-768`, `:1780-1786` (the set expression), `:1743-1751` (link
kinds and "compose in lineage order"), `:3302-3312` (per-kind anchors only), `:1084` (mask subscript is
available on any context).

**Suggested fix.** Replace the set expression in §2.3d and §6.1d(B) with the sequential statement it is a
lossy summary of: "labels are computed by composing the links in lineage order — a mask-derivation link
unions that mask's labels per §2.4, a `vary` link is the identity, and a universe/nominal projection link
**resets the label set to empty** — so a value reached across a projection link carries only labels
introduced by mask-derivation links *below* it."

---

### 8. LOW — m48's target-line justification "m48 has weight labels only, so `|S| = 0`" is false of m48's own anchor list

**Section:** §10 m48 targets / §6.1b.

**Detail.** r22 defers §6.1b's arity anchor to m49 on the ground that "**m48 has weight labels only, so
`|S| = 0`**" (`:3044`). §6.1b r19 defines `S` as "the labels that require their own SIBLING fill node —
those borne by any **AXIS value** or by a `Varied` `sample=`" (`:1580-1583`). m48's own frozen anchor list
contains at least three programs with a non-empty `S`:

- the four-way fold-order anchor: "a fill with **varied values in TWO axes** plus an ambient weight plus an
  explicit `weight=[…]` factor **plus a varied `sample=`**" (`:3537-3539`);
- §2.3b's entry-point anchor: `plain_array[varied_mask]` "returns a `Varied` carrying the mask's labels"
  (`:3445-3447`), filled downstream;
- §6.1d's link-kind-(1) anchor: `h.fill(events.MET.pt, sel.MET.pt)` with `sel = events[varied_mask]`
  (`:3618`).

The *placement* conclusion (arity anchor at m49) is defensible on its own merits — §6.1b's r20 clause
concedes the `S`/`W` split is unwitnessable before m50 — but the stated reason is measurably wrong, and §10
is "the acceptance skeleton the test-author starts from", so a test-author may conclude m48 carries no
shift-shaped/axis-borne labels at all when three of its anchors do.

**Evidence.** `systematics-vary-plan.md:3043-3049` (the target-line note), `:1577-1591` (§6.1b's `S`/`W`
definitions by lowering behaviour), `:3537-3539`, `:3445-3447`, `:3618` (m48 anchors with varied axis values
and a varied `sample=`).

**Suggested fix.** Re-word to the true reason: "§6.1b's arity anchor is m49's — m48's `W` is exercised by
the corpus weight matrix while a *counted* `1 + |S| + |W|` assertion needs the shift path (§5, m49); m48's
own varied-axis and varied-`sample=` programs are anchored for fold order and result shape, not for arity."

---

### 9. LOW — §2.2 defines the introspection verbs over two shapes; §6.1a/§6.2(i-bis) bindingly extend them to four

**Section:** §2.2 / §6.1a / §6.2(i-bis).

**Detail.** §2.2 binds `graphed.labels(x)` / `graphed.nominal(x)` / `graphed.universe(x, label)` as "each
accepting a `Varied` **OR** an event context (uniform introspection, §9.1)" (`:523-528`). Two later sections
extend them without amending that definition: §6.1a requires them to narrow the *result* shapes —
"`graphed.universe(result[name], label)` and `graphed.labels(result[name])` work uniformly on BOTH shapes
(§2.2), a bare `hist` reading as the single label `"nominal"`" (`:1574-1576`), i.e. over a `bh.Histogram`
and over a `{label: hist}` mapping — and §6.2(i-bis) adds the axis-mode histogram, with a *different* rule
for its labels and a duck-typed detection that must not import `boost_histogram` (`:1960-1975`,
`:1999-2008`). So the verbs have **four** input shapes with three different label rules, and the section
that defines them lists two.

This is a documentation-coherence defect rather than a functional one — every extension is bound and
anchored where it is introduced (m48's §6.1a anchor, m50's (i-bis) anchor) — but §2.2 is where an
implementer types the signature, and the §11/§9.1 surface list does not repair it either.

**Evidence.** `systematics-vary-plan.md:523-528` (two shapes), `:1569-1576` (dict + bare-hist narrowing),
`:1960-1975` (axis-mode histogram, different ordering rule), `:1999-2008` (duck-typed `.axes` detection, no
`boost_histogram` import in `graphed`).

**Suggested fix.** One added clause in §2.2: "`x` is a `Varied`, an event context, a **`{label: hist}`
mapping** or a **bare histogram-like object** (duck-typed on `.axes`, §6.2(i-bis)); the per-shape answers are
bound in §6.1a and §6.2(i-bis)" — with the cross-references, so the definition site enumerates the surface
its callers rely on.

---

## Areas probed and found CLEAN (no finding)

Recorded so the round's coverage is legible, and so a later reviewer does not re-derive them:

- **§1.1 e-canonicalization (r9/r18/r19/r20/r22).** The r22 split — rendered canonical length under both
  renderings, magnitude message only when the *integer* digit count alone exceeds the cap — is internally
  consistent and total. Walked by hand: `"1e40"` (41 digits, magnitude), `"1.5e31"` (32 digits, accept),
  `"1.5e32"` (33, magnitude), `"-1.5e31"` (32 digits legal / 33 rendered chars, length message),
  fractional `len(mantissa)+2+len(exponent)` matching `12345em4`=8 and `m15em1`=6, negative-zero → `0`,
  `"1e1000000000"` decidable without rendering (the exponent is an integer parse). Cross-notation:
  `{"5em1","0p5"}` both parse to 0.5 and are rejected; `"m2"` re-renders minimally; `"em1"` is not numeric
  and rides through as an identifier tag — no ambiguity found. §6.4b's `__vary_{label}__{field}` correctly
  disclaims the 32-char cap and carries a both-directions collision check.
- **§2.4 label-aligned union vs §2.6c lineage unification.** Composition checked on a derived context whose
  mask labels and ambient labels are disjoint: §2.6c's re-indexing produces the union registry, which is why
  §2.2's term (a) already carries the mask's labels in the mainline; the r21 scoping of terms (b)/(c) and
  the three m48 discriminating programs (`:3645-3661`) are mutually consistent and non-degenerate.
- **§6.2 axis mode vs §6.1c/§6.1a keying and shift-sibling scalar labels.** The `(output, None)` slot, the
  per-slot spec taken from any gathered fill node (r22), the per-fill variation payload entering
  `content_hash((spec, variation_payload))` (§6.2 r15), and §1.2's r22 widened carve-out covering *both*
  label channels now agree. `Histogram.fill`'s one-array-per-axis arity is not violated because the
  variation axis lives in the fill node's spec, not on `self.axes`.
- **§6.4d structure rule vs jagged object-level migration.** Stored buffers are pre-object-cut on the
  event-row superset, so per-label offsets match nominal for scale/smear shifts, and migration is carried by
  the level-≥1 packed masks; the multiplicity refusal is the correct residual. The natural user spelling of a
  per-jet mask (`jets.pt > 25` at root row space, as the corpus writes it) satisfies the level-≥1 structural
  check by construction.
- **§5.4 boundary refusal vs §6.4 write plans.** No interaction: the write path builds no Exchange/Join, and
  §6.4f's shared `compile_ir` does not introduce one.
- **§7.3 checkpoint invalidation vs m51 writes.** `write_plan` builds a plain-callable `Plan`, so m51 churns
  no shipped journal; the scoping sentence at `:4296-4300` is consistent with §7.3 (its milestone wording is
  covered by finding 6, not by a second finding here).
- **numpy backend exemptions.** Consistent across §6.1d (`broadcast_like` is a bound NO-OP, not an
  either/or), §6.4a/§6.4f (the numpy-idiom write refuses; no neutral dispatcher is introduced) and §6.4e
  (no numpy `read_varied`).
- **Package boundaries / factorization.** No binding requirement puts awkward into `graphed-core` or into
  `graphed` proper: the broadcast seam is neutral and backend-dispatched, both parquet entry points and
  `read_varied` are awkward-idiom, §6.2(i-bis) is duck-typed with no `boost_histogram` import, and §6.4e's
  r21 rule explicitly forbids importing `awkward._connect.*` (knowingly unanchored, with its reason stated).
- **§7.2's node-id→position derivation** over `plan()`'s own ordered `fill_nodes` list, and the m48 merge
  refusal that makes the two orders agree, compose correctly; the unvaried mis-slice remains pre-existing
  rather than a regression.
- **`to_parquet` compiles at the call** — verified directly, not taken from the plan:
  `/private/tmp/claude-501/graphed-latest/python/graphed/awkward/io.py:230-231`
  (`columns = _evaluation_columns(...)` then `compiled = compile_ir(session, array)`), so m51's new §6.4f
  write-path merge-refusal anchor is affordable as a record-time check exactly as r22 claims.

---

## Verdict

**DIRTY** — 1 HIGH, 5 MID, 3 LOW; **no BLOCKER**.

Nothing found makes a milestone unimplementable or freezes a provably wrong test today. The plan's core
architecture (record-time expansion + interning, sibling fills, ambient context, axis mode, skim
augmentation) is coherent, and the areas flagged for deepest attention — §1.1's e-form canonicalization,
§6.2's axis mode, §6.4d's structure rule, the package-boundary discipline — are sound and closed.

The HIGH is a genuine hole in the *newest* surface: the functional context idiom compares handles by object
identity in three binding rules and never says when two contexts are the same handle, so the most natural
implementation raises a divergence error on programs that name one universe twice. Findings 2–6 are all in
the same family the plan has been closing round after round — a rule re-expressed over a new operand that
silently narrows what the old rule admitted (2), a new keyword whose effect on a frozen result shape is
unstated (3), a stale sentence contradicting the r22 change that amended it (4), a fixture spelled in a call
shape another section refuses (5), and a milestone correction not propagated to the two places that scope
implementers (6). Each has a local fix; none requires reopening an owner-locked decision.
