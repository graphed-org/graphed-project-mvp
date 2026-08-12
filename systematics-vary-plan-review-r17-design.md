# systematics-vary plan — review round 9, DESIGN SOUNDNESS lens

- **Lens**: design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections; unhandled interactions; under-specified Implementation Targets; package-boundary
  / factorization violations; milestone-boundary consistency.
- **Plan revision reviewed**: `systematics-vary-plan.md` **r17** (3857 lines, read in full: header,
  Part I, every PART II section, §10 milestones, §11, §12, Anchors appendix, revision history).
- **Date**: 2026-07-30.
- **Verification roots used** (every code fact below was read or executed by me in this session; no
  claim is carried over from the plan's own citations without checking it):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607` — confirmed by
    `git log --oneline -1`)
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe` — confirmed)
  - `/private/tmp/claude-501/graphed-exec-check`, `/private/tmp/claude-501/uproot5-graphed`,
    `/private/tmp/claude-501/graphed-corpus-latest` (consulted, no finding depends on them)
- **Owner-locked decisions** (naming, functional surface, e-form encoding, event-context attachment,
  record-time expansion, m48–m51 scope incl. §6.4, JER-SF non-monotonicity, the Phase-2 pull-in) are
  taken as given. No finding below asks for a different choice; every one is about internal
  consistency or completeness of how a locked choice is *specified*.

Findings are ordered by severity. Counts: **1 BLOCKER, 2 HIGH, 4 MID, 3 LOW, 0 NIT.**

---

## BLOCKER-1 — §6.1a and §6.1c(r17) bind two incompatible shapes for the same m48-frozen object; "the combine BRANCHES" vs "The COMBINE needs no branch"

**Section**: §6.1a / §6.1c (both m48 targets; both carry m48 frozen anchors).

**Detail.** §6.1a binds the group result to a value-dependent nesting and binds the *combine* to
branch over it:

> `:1247-1251` — "The declared result type is therefore the value-dependent union
> `dict[str, bh.Histogram | dict[str, bh.Histogram]]` … paid for explicitly: **the combine BRANCHES
> on the two shapes** (today's `_add_groups` assumes a homogeneous mapping, `boost.py:120-122`), and
> a bound narrowing helper is provided … `graphed.universe(result[name], label)` and
> `graphed.labels(result[name])` work uniformly on BOTH shapes."

§6.1c(r17) binds the reducer's slot keying and then states the opposite about the same combine:

> `:1295-1308` — "an axis-mode output contributes **exactly ONE slot, keyed `(output, None)`** …
> **The COMBINE needs no branch** (r17 — r15's 'the per-slot VALUE TYPE is recorded in the layout and
> the combine branches on it' asks for something the bound keying makes unnecessary: under it every
> slot's value is a plain `bh.Histogram` — a sibling slot `(output, label)` holds one, an axis-mode
> slot `(output, None)` holds one carrying the variation axis) — measured, `_add_groups` is
> `{label: a[label] + b[label] for label in a}` …, a key-wise `+` **that requires the value type be
> uniform PER KEY**, which the `(output, None)` keying gives by construction."

These cannot both hold. Under §6.1c the plan's combined value is a **flat, slot-keyed**
`{(output, label|None): bh.Histogram}` whose values are uniformly plain histograms — that is exactly
why no branch is needed. Under §6.1a the plan's value is **nested**, `{output: hist | {label: hist}}`,
and the combine must branch because `a[key] + b[key]` is `dict + dict` for a varied output.

I verified the mechanical half rather than trusting the citation:
`graphed-histogram-latest src/graphed_histogram/boost.py:120-122` is
`return {label: a[label] + b[label] for label in a}`, and `plan()` at `:254-292` returns
`Plan[dict[str, bh.Histogram]]` whose `reduce=_GroupReduce(layout)`, `combine=_add_groups`,
`empty=_GroupZero(layout)` are the *only* value-shaping steps. So whatever shape those three agree on
IS the user-visible value; there is no second place for the other shape to appear.

r17 introduced this: r15's withdrawn sentence was about the *axis-vs-sibling per-slot value type*, a
narrower question than §6.1a's *varied-vs-unvaried output* branch, and r17 answered it with an
absolute sentence that reaches §6.1a.

**Why BLOCKER.** m48 freezes both ends. `:2514-2519` freezes §6.1a's result shape ("on a MIXED
varied/unvaried output set: a varied output is `{label: hist}`, an output no variation reaches is a
BARE hist (not `{"nominal": hist}`) … and `graphed.universe`/`graphed.labels` narrow both shapes
uniformly"), while §6.1c's indices-based, slot-keyed layout is an m48 target that §7.2/§6.1a
themselves declare load-bearing (`:2295-2297` "§6.1a/§6.1c cannot be implemented without §7.2's
`(output, label) -> node id` map and the indices-based `_GroupReduce.layout` it feeds"). A
test-author freezes §6.1a's shape; a §6.1c-conforming implementer returns slot keys; the frozen suite
goes red against a correct implementation ⇒ Test Dispute mid-milestone. That is the
"self-contradictory / freezes wrong tests" definition.

**Suggested fix.** Settle it in §6.1c's favour and repair §6.1a:
1. Withdraw §6.1a's "the combine BRANCHES on the two shapes" clause. Bind explicitly: *the plan's
   combined value is the flat slot-keyed mapping `{(output, label) -> bh.Histogram}` /
   `{(output, None) -> bh.Histogram}`; `_add_groups` stays a homogeneous key-wise `+` with no branch.*
2. Re-word §6.1a's `dict[str, bh.Histogram | dict[str, bh.Histogram]]` as the return type of the
   **unpack surface** (BLOCKER-1's sibling finding, HIGH-1), not of the combine — the `mypy --strict`
   cost paragraph then attaches to the unpacker.
3. Re-word m48's §6.1a anchor (`:2514-2519`) over the unpacker's output, and add one clause pinning
   the *plan value's* slot-keyed shape so both halves are frozen and cannot drift apart again.

---

## HIGH-1 — §6.1a's result shape has no bound producer: the "FRONTEND UNPACKER" is named three times and never given a surface, and `Plan` has no post-combine seam

**Section**: §6.1a / §6.1c / §7.2 (m48).

**Detail.** Three places assume an unpacking step between the executed plan's value and the
user-visible result:

- `:1298-1299` — "the layout records the **per-OUTPUT MODE** (sibling / axis) — the information the
  **FRONTEND UNPACKER** needs to choose between `{label: hist}` and a bare histogram per
  §6.1a/§6.2(i-bis)";
- `:1936-1937` — "**The frontend unpacks into the §6.1 named mapping**";
- §6.1a's narrowing helper is applied to `result[name]`, i.e. to the unpacked shape.

Nothing binds where that unpacker lives or what it is called. Measured, there is no seam for it:

- `graphed-latest python/graphed/core/execution.py:206-217` — `Plan` is
  `(process, combine, empty, tasks, next_tasks, stop, open_once)`. There is **no finalize /
  post-combine hook**; `ExecResult` at `:218-224` is `(value, n_partitions, n_combines, stopped)` and
  `value` is exactly the combine's output.
- `graphed-histogram-latest src/graphed_histogram/boost.py:254-292` — the group `plan()` builds and
  returns that `Plan` and nothing else; the user's next call is an executor's `run(plan)`.
- Adding a `Plan` field is foreclosed by this plan's own §7.2 (`:1961-1964`): "`ExecResult`/`Plan`/
  monitor **schemas** do not change in m48–m50 … the absence is a frozen m48 anchor … worded over
  **schema KEY SETS**". A new `Plan` field changes that key set and would turn m48's own anchor red.

So the m48 §6.1a anchor is **unwritable as stated**: the test-author must invent both the surface and
its spelling (a `graphed_histogram` module verb over the executed value? a wrapper `run`? a
classmethod?) and freeze the guess read-only. This is verbatim the defect class the plan has already
repaired twice — for §2.5's diagnostic channel (`:827-838`, "the requirement was unwritable as
stated … a test-author had to invent both it and its shape … with a wrong guess frozen read-only")
and for §5.3's projection-stats verb (`:1181-1189`) — and every other new surface in this plan
carries a "spelling pinned at m48 freeze" clause. This one does not.

**Suggested fix.** Bind it the same way the plan bound `graphed.context_of`, `graphed.weight`,
`graphed.broadcast_like` and the per-label fill-node accessor: a **read-only `graphed_histogram`
module verb over the executed plan value plus the plan's layout** —
`graphed_histogram.unpack(value)`-shaped, returning
`dict[str, bh.Histogram | dict[str, bh.Histogram]]` per §6.1a and choosing per output from the
layout's recorded MODE; **exact spelling pinned at m48 freeze**; listed in §9.1 alongside the other
m48 accessors; and named in m48's anchor list as the operand of the §6.1a result-shape anchor. (If
the owner prefers the value itself to be user-facing, the alternative is to withdraw §6.1a's nested
shape and re-base §6.1a/§9.1's narrowing helpers on slot keys — but then §6.1a's
backward-compatibility argument, "unvaried programs see today's shapes unchanged", is false and must
also be withdrawn, because today's shape is `{output_name: hist}`.)

---

## HIGH-2 — §6.4b's stored varied weight factors are unstorable exactly where §6.4a(2a) says they come from: `graphed.weight(ctx)` on a selection-derived context is refused by predicate (1)/§6.4d, and m51's "weight-only label" anchor does not say which spelling it means

**Section**: §6.4b / §6.4a(2a) / §6.4d / m51 anchors.

**Detail.** §6.4b (`:1770-1774`) binds:

> "Weight-only labels contribute no kinematic deltas — their varied factors, **when among the stored
> fields**, augment like any other varied field (**reachable via `graphed.weight(ctx)`**, §9.1 —
> added in r12: under the owner-locked context idiom a factor handed to
> `graphed.vary(..., is_weight=True)` is otherwise absorbed into an immutable registry the user
> cannot name, so 'when among the stored fields' was unsatisfiable)."

and §6.4a(2a) r16 (`:1683-1689`) justifies admitting `vary` links with:

> "§6.4b's stored varied weight factors are reached via `graphed.weight(ctx)`, so **a skim storing
> varied weights is written from a weight-`vary`-derived context BY CONSTRUCTION**".

Now take the plan's own mainline idiom (§2.6 sketch `:930-934`): `sel = events[gak.num(jets) >= 4]`
with a JES-varied `jets`, then `sel = graphed.vary(sel, "btag", btag_sf(sel.Jet), is_weight=True, …)`.
By §2.6c (`:883-905`) that context's **row set differs per label**, and its ambient registry is
inherited "with every member RE-INDEXED by the derivation mask, label-aligned per §2.4 … each label's
ambient member is re-indexed by THAT label's mask". So `graphed.weight(sel)` is a `Varied` whose
members have **different lengths per label** and whose nominal length is `|sel_nominal|`.

The record being written is, by §6.4a's own binding, **pre-selection** and is stored on the
**superset** rows (`:1619-1621`, `:1758-1759`). Therefore, if such a factor is placed among the
stored fields:

- **§6.4a/§6.4d predicate (1)** (`:1670-1671`, `:1842-1844`: "every per-label member's offsets equal
  nominal's at every level the writer will store" / "a stored varied field whose per-label offsets
  differ from nominal's is REFUSED") fires — the per-label lengths differ *by construction* under
  §2.6c's varied-mask rule; and
- even for an unvaried mask, nominal's length is `|sel|`, not the superset row count, so the field
  cannot be stored on the written rows at all.

There is no bound re-indexing rule from a derived context's row space back onto the superset (and
none is expressible: a mask has no inverse). So §6.4b's clause is satisfiable **only** when the
weight's context shares the record's row space — i.e. a weight registered on a *root-derived*
context, `graphed.weight(events2)` — which is precisely *not* the selection-scoped weight that
§9.1/§6.4b introduce `graphed.weight` for, and not the case §6.4a(2a) r16 describes.

**Why HIGH.** m51's round-trip anchor (`:3006-3013`) lists "a weight-only label" as one of four
covered cases with no spelling. A test-author taking the plan's own idiom (`graphed.weight(sel)`)
freezes a program that a correct implementation must refuse; one taking the root-registered spelling
freezes something else. Either way the milestone's headline round-trip anchor is under-determined,
and the failure surfaces as an offsets error from `_WritePart` per partition whose message is about
the wrong thing.

**Suggested fix.** In §6.4b, bind the row-space precondition explicitly: *a stored varied field MUST
live in the record's own row space; `graphed.weight(ctx)` is storable only when `ctx` is reached from
the record's context across `vary` identity links only (no mask-derivation link) — a
selection-scoped weight is NOT storable in v1, and the refusal names it as such rather than as an
offsets mismatch.* Add that refusal to m51's entry-check anchor list, and re-word m51's round-trip
"weight-only label" bullet to name the storable spelling
(`graphed.weight(<root-derived vary context>)`). Correspondingly soften §6.4a(2a) r16's
justification: `vary` links must still be admitted (the `select=graphed.selection(sel2)` case at
`:3019-3025` is real and independent), but not on the grounds that varied weights are stored from a
selection-derived context.

---

## MID-1 — §2.1(a)/(b) declare member values to be `Array`s, contradicting §2.1's own stacking rule, the §2.6 sketch, and the corpus case m48 freezes

**Section**: §2.1 (m48; frozen by m48's "§2.1 stacking" anchor).

**Detail.** §2.1 overload (a) (`:372-373`): "**Array | Varied target** (the loose primitive):
**members are Arrays**". Overload (b) (`:376-378`): "`nominal` (third positional) is the central
per-event weight factor and **every member is a per-event weight Array**".

Both are contradicted three lines later by the stacking rule (`:390-405`), which is written for
`Varied` members and *requires* them:

- "a new label's member is the provided value's central universe (**`graphed.nominal(v)` if the
  provided value is itself `Varied`**, else the Array as given)";
- "in the **weight form (b)** … an inherited label L's ambient member becomes
  `old_ambient[L] × factor[L]` — **the factor evaluated in that label's own universe** (its central
  universe only when L is new to the factor)".

`factor[L]` for `L = jes_up` only exists if the registered factor is a `Varied` carrying `jes_up`.
And the plan's own sketch produces exactly that: `:932-934` registers
`graphed.vary(sel, "btag", btag_sf(sel.Jet), is_weight=True, up=btag_sf(sel.Jet, "up"), …)` where
`sel.Jet` is a `Varied` (§2.6b/§2.6c), so `btag_sf(sel.Jet)` broadcasts to a `Varied` by §2.3a — the
`nominal=` argument and both tags are `Varied`, not `Array`. This is the corpus b-tag-on-JES case the
plan calls load-bearing (`:397-405`, `graphed-corpus systematics.py:74-76`) and that m48's stacking
anchor freezes (`:2442-2454`).

The contradiction is not cosmetic because §2.5 (`:822-823`) binds *construction-time* member
validation ("form-incompatible or cross-Session/cross-source member → construction-time error naming
the label"), and m48 freezes "§2 validation errors" (`:2599`). An implementer reading (b) literally
adds an `isinstance(m, Array)` guard and the plan's own mainline program raises.

**Suggested fix.** Replace both type declarations with one rule stated once: *a member may be an
`Array` or a `Varied`. In overloads (a)/(c) a `Varied` member is reduced to its central universe
(`graphed.nominal(v)`). In overload (b) a `Varied` member is kept and consumed label-aligned per
§2.4 — `factor[L]`, falling back to its central universe when L is new to the factor.* Then §2.1's
construction checks (Session / form / partitioned-source) are stated as applying per member of the
flattened container.

---

## MID-2 — the numpy-idiom `Array` **properties** (`shape`/`dtype`/`ndim`/`T`) get no `Varied` disposition and are deliberately filtered out of the §2.3a gate, so `varied.dtype` records a `field` op — the exact confidently-wrong class §2.2 exists to close

**Section**: §2.2 reserved names / §2.3a parity gate (m48).

**Detail.** §2.2 (`:470-480`) closes this hazard for exactly two names:

> "**`Varied` reserves the `Array` protocol attribute names**: `node_id` and `session` raise
> `AttributeError` … so a `Varied` that implements field access by mapping over labels would answer
> `varied.node_id` with a recorded `field` op named `"node_id"` … and `compile_ir` would silently
> compile that nonsense instead of raising, the §2.5 confidently-wrong class."

§2.3a r16 (`:502-513`) then *excludes properties from the gate on purpose*, citing "would demand
dispositions for numpy-idiom properties §2.3a never assigns (measured … `dir(NumpyArray)` adds
`T`/`dtype`/`ndim`/`shape`)", and binds the enumeration to
`inspect.getmembers(type(graphed.nominal(v)), inspect.isfunction)`. Net effect: those four names get
**neither** a reserved-name rule **nor** a gate entry.

Measured in `graphed-latest`:

- `python/graphed/numpy/array.py:71` `class NumpyArray(Array)`, with `shape` `:78`, `dtype` `:82`,
  `ndim` `:86`, `T` `:160` — all `@property`, so `inspect.isfunction` does not see them.
- `python/graphed/array.py:332-335` — `Array.__getattr__` returns
  `self._session.record_op("field", [self], {"field": name})` for **any** non-underscore name; the
  plan itself relies on this fact twice (`:494`, `:517-520`).
- `python/graphed/array.py:283-290` — `_form_meta` answers these eagerly from the form when the
  backend models it (never recorded), so on a plain `NumpyArray` `x.dtype` is a dtype, while on a
  `Varied` of `NumpyArray`s `v.dtype` would be a recorded graph node named `"dtype"`.

So on the numpy idiom — which this plan keeps a first-class varied path (§6.1d binds the numpy
`broadcast_like` seam as a NO-OP precisely so "an all-numpy varied fill works", `:1406-1411`) —
`varied.shape` / `varied.dtype` silently compile nonsense, and no m48 anchor can see it.

**Suggested fix.** Widen §2.2's rule from "the two `Array` protocol properties" to a discovery rule
over properties, mirroring what §2.3a/c already do for methods: *every non-underscore **property** on
`type(graphed.nominal(v))` carries a disposition — `node_id`/`session` raise `AttributeError`; all
others are **eager-metadata**, answered on the nominal member (sound by §2.1's form compatibility,
the same argument §2.3c uses for `gak.fields`/`type_of`).* Add the property half to the §2.3a gate's
enumeration (`inspect.getmembers(type(...), lambda o: isinstance(o, property))`) with the same
non-vacuity floor, and add one named representative (`varied.dtype`) to m48's parity anchor.

---

## MID-3 — §7.2's m48 optimizer-merge refusal has no bound SITE and no scope, so as written it also fires on unvaried programs, against §6.3's "no-variation paths are unchanged"

**Section**: §7.2 (m48).

**Detail.** `:1953-1960`:

> "**binding for m48**: after `compile_ir` **the frontend** compares the number of DISTINCT compiled
> outputs (`GraphStore.deserialize(ir).outputs()`) against the number of distinct record node ids it
> marked and, on a shortfall, raises a `graphed` error naming the outputs and labels involved plus
> the workaround …"

Two things are unbound and they pull in opposite directions:

1. **The site.** "after `compile_ir` the frontend" reads most naturally as `compile_ir` itself
   (measured, that is where marking happens: `python/graphed/execute.py:54-80`, `ids = [arr.node_id
   for arr in outputs]` at `:70`; and `evaluate_ir` returns `[vals[o] for o in store.outputs()]`,
   `:126` — I re-read both). But the error must "name … the **labels** involved", and labels exist
   only where the `(output, label)` map lives, i.e. `graphed-histogram`'s group-plan builder. The two
   candidate sites give different behaviour and only one of them can host the message the anchor
   freezes (`:2427-2428`, "the program is REFUSED with a message naming the labels").
2. **The scope.** The predicate is stated over *any* compile, with no "varied program" qualifier. An
   unvaried two-histogram program whose fills the M4 identity rules merge (`w` vs `w * 1.0` — the
   plan's own measured case, appendix `:3196`) then starts raising where it previously ran. §6.3
   (`:1588`) binds "Data / no-variation paths are unchanged", and §6.1c itself notes the mis-slice is
   "(Latent today for two unvaried histograms with identical fills)" (`:1308-1309`) — i.e. the
   unvaried case is in the same blast radius.

**Suggested fix.** Bind both in one sentence: *the check runs in the group-plan builder that owns the
`(output, label) → node id` map (`graphed-histogram`'s `plan()`), over the outputs of a **varied**
program only; an unvaried program's compile path is untouched (§6.3).* If the owner prefers the check
to be universal, say so explicitly and add the consequence to §6.3 plus an m48 anchor for the
unvaried-merge refusal — but do not leave it inferable from the site.

---

## MID-4 — §6.4f binds `_WritePart`'s widened output unpack without binding it to §7.2's node-id keying, while m51's round-trip anchor puts the dedup case in scope

**Section**: §6.4f / §6.4c / m51 anchors.

**Detail.** §6.4f (`:1891-1894`): "That call site unpacks a SINGLE output today
(`(out,) = evaluate_ir(...)`, `io.py:121`), so **widening it to the augmented output list** is part
of this target, not incidental". §6.4c (`:1811-1815`) makes the extra marked outputs the **per-label
values and per-label masks**.

m51's round-trip anchor (`:3006-3013`) explicitly includes "**a label structurally equal to nominal
(all-zero delta)**". Measured, that is exactly the case a positional unpack gets wrong:

- `graphed-latest src/store.rs:147-156` — `mark_output` pushes only `if !g.outputs.contains(&id)`,
  i.e. it de-duplicates;
- `graphed-latest python/graphed/execute.py:126` — `return [vals[o] for o in store.outputs()]`, one
  value per **distinct** output.

So a label whose value (and mask) intern to nominal's node id yields *fewer* returned values than
marked outputs, and a positional `nominal, *per_label = evaluate_ir(...)` in `_WritePart` misassigns
every label after the collapsed one — silently, since an all-zero delta is the expected content there.

§7.2 does state the general rule and even names m51 (`:1934-1937`: "many labels MAY resolve to one
position and the unpacker replicates that value … §5.2a/m51 put in scope (a label structurally equal
to nominal)"), but §6.4f — the paragraph an m51 implementer works from — never references it, and the
node-id → position table has to be *shipped into the worker closure* (`_WritePart` is a frozen
dataclass evaluated per partition, `python/graphed/awkward/io.py:111-127`), which is a concrete design
obligation nothing states.

**Suggested fix.** In §6.4f, add: *the widened unpack resolves each augmented output **by node id**
per §7.2, replicating a shared value into every label that maps to it; the `record node id → output
position` table is a field of `_WritePart` (it is driver-derived, not recomputable in the worker).*
Add the collapse case to m51's entry/round-trip anchor wording so the freeze witnesses the
replication rather than only the all-zero delta. While there, state whether §7.2's m48 refusal for
**optimizer-merged** outputs also guards the write path (it is reachable there too — a μR/μF label
spelled `w * 1.0` is §1.1-legal), which is the same decision MID-3 asks to bind.

---

## LOW-1 — milestone target lines under-list sections whose anchors that milestone freezes

**Section**: §10 (m49, m51).

**Detail.** The DoD is "targets exactly as specified" (`:3101-3104`), so the target line is what an
implementer scopes from.

- **m49** targets are "§3.3, §3.4 (frozen anchor), §5, §7, §8" (`:2724`), but m49's anchor list
  contains "**§2.5 shift-after-weight diagnostic** (§2.1/§2.5 r16, using §3.4 which lands here)"
  (`:2826-2829`), and §2.5 itself says the diagnostic "is an m49 target" (`:2839-2843`). §2 is an m48
  target line; §2.5's m49 carve-out appears in neither milestone's target list.
- **m51** targets are "§6.4" only (`:2997`), but m51's anchors freeze §9.1's `graphed.selection`
  (`:3014-3018`; §9.1 marks it m51 at `:2179-2181`, and m48's line says "m51's carries
  `graphed.selection`", `:2303`) and §2.3d's re-classification of `to_parquet` (`:3088-3091`).

**Suggested fix.** Append the carve-outs to the two target lines: m49 "+ §2.5's shift-after-weight
diagnostic"; m51 "+ §9.1's `graphed.selection` + §2.3d's `to_parquet` re-classification".

---

## LOW-2 — §1.1's integer-magnitude rejection is specified over the *rendered* digit string while the input grammar states no magnitude bound

**Section**: §1.1 (m48; frozen by the m48 grammar anchor).

**Detail.** `:262-267`: "**the input grammar below states no magnitude bound, so a large-magnitude
INTEGER-valued input is the one spelling the grammar admits and the cap then refuses** — `"1e40"`
renders as 41 plain digits while `"1e-40"` renders as the 5-character `1em40`, so an integer-valued
input whose **plain-digit rendering** exceeds the cap is rejected at canonicalization with a message
naming the magnitude". The canonical grammar has no positive-exponent form by construction
(`:257-258`), so integers *must* render as plain digits.

Read literally, `"1e1000000000"` — legal under the stated input grammar
`-?\d+(\.\d+)?([eE][+-]?\d+)?`, with no magnitude bound — requires materialising a one-billion-digit
string before the 32-character cap can refuse it. The e-form's own structure (mantissa + exponent)
makes this avoidable: the digit count is `len(mantissa_digits) + exponent`, computable without
rendering.

**Suggested fix.** One clause: *the magnitude check is performed on the computed digit COUNT
(mantissa digits + exponent), before rendering; the canonical string is only produced once the count
is within the cap.* Optionally have the m48 grammar anchor's integer-magnitude case use a large
exponent rather than `"1e40"`, so the freeze witnesses the count-based check.

---

## LOW-3 — `graphed.vary` is a combining point but §2.1's construction checks omit context-handle divergence, and `graphed.context_of`'s eager-metadata rule then hides the mismatch

**Section**: §2.1 / §2.3e (m48).

**Detail.** §2.3e (`:731-739`) binds "every *combining point* runs the same unification, and the fill
is one of them … handles on divergent branches are an error at that op naming both", but §2.1's
enumerated construction checks are only "one Session … compatible forms (backend `op_form`-checked)
… root in the same partitioned-source set" (`:421-424`) — context handles are not among them, and
`vary` is not an op, so the `record_op` merge chokepoint (`session.py:142-168`, re-verified: five
`_array_cls` sites, all in `session.py`) never sees it. A user-supplied member computed through a
different context (`graphed.vary(events.Jet, "jes", up=<read through sel>)`) therefore yields a
`Varied` whose members carry divergent handles, and §2.3d classifies `graphed.context_of` as
*eager-metadata* "answering on the nominal member for a `Varied`" (`:697-699`) — so the introspection
verb reports one handle and the other is silently dropped at the fill's unification.

This is narrow (it needs a deliberately mixed construction) and the plan's "every combining point"
sentence arguably already covers it, but the enumerated check list is what an implementer will code
from, and m48 freezes "§2 validation errors".

**Suggested fix.** Add context-handle unification to §2.1's construction-check enumeration: *all
members' context handles MUST lie on one ancestry chain; the container carries the most-derived one;
divergent handles are a construction-time error naming both contexts* — and add it as a clause to
m48's existing divergent-lineage anchor (`:2635-2641`), which today covers only the op and the fill.

---

## Verdict: **DIRTY**

One BLOCKER and two HIGH findings. The BLOCKER (§6.1a vs §6.1c(r17)) is an r17 regression: a
narrowly-correct repair to §6.1c's per-slot value-type question was stated absolutely and now
contradicts §6.1a's combine clause, leaving m48 with two incompatible frozen result shapes. HIGH-1 is
its sibling — the shape §6.1a describes has no producer and no named surface, and `Plan` (measured)
has no seam for one while §7.2's own m48 anchor forbids adding one. Both must be settled together and
the settlement re-worded into m48's anchor list. HIGH-2 is a §6.4/m51 gap: the varied-weight-storage
clause is unsatisfiable in exactly the context lineage §6.4a(2a) says produces it, and m51's headline
round-trip anchor names that case without a spelling.

The rest of PART II held up well under this lens. In particular I probed and found **clean**: §2.4's
label-aligned union against §2.6c's lineage/re-indexing rules (including the varied-mask per-label
row-set case and §2.2's three-term `graphed.labels(ctx)` union — term (b) covers the mask labels for
every derived context by §2.6c's "its collections are `Varied`" clause, so the superset invariant
survives `vary` and universe/nominal links); §1.1's e-canonicalization edge cases (exact-decimal
unification, non-minimal re-rendering, negative zero, cross-notation p/e rejection, the family
definition spanning stacking calls — the two grammars are disjoint except on integers, where they
agree, so no ambiguous parse exists); §6.2's axis mode against §6.1c's slot keying, the per-fill
carrier and the fill-time declaration argument; §6.4a's per-level `select=` against §6.4d's
structure rule and the object-migration reconstruction path; §5.4's boundary refusal against the
write path (write plans do not build shuffle/join boundaries); §7.3's r17 checkpoint-churn scoping
(re-verified: `write_plan` builds a plain-callable `Plan`, `write.py:32-43`, and `run_resumable`
requires a `DurablePlan`); and the package-boundary rules — no binding requirement puts `awkward`,
`pyarrow` or `boost_histogram` behind a neutral namespace, and the one optimizer-adjacent addition
(§8.2(i)) is read-only and awkward-free.
