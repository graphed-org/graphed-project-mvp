# systematics-vary plan — review round 11, DESIGN SOUNDNESS lens

- **Plan revision reviewed:** r19 (`systematics-vary-plan.md`, 4545 lines, read in full — Part I,
  every PART II section, §10 milestones, §11, §12, Anchors appendix, revision history r19/r18).
- **Lens:** design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections; unhandled interactions; under-specified Implementation Targets; package-boundary
  / factorization violations; milestone-boundary consistency. Facts and test-design lenses are run
  separately; I flag a fact only where it invalidates a design requirement.
- **Date:** 2026-07-30.
- **Verification roots used** (every code claim below was read or executed by me in this session):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (consolidated `graphed`; its `.venv` was
    used for the runtime probes)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42` (referenced, not needed for findings)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef` (referenced, not needed for findings)
- **Owner-locked decisions were treated as fixed.** No finding below asks for a different choice on
  naming, the functional surface, e-form canonicalization, event-context attachment, record-time
  expansion, m48–m51 scope, or the Phase-2 pull-in. Findings 4, 6, 7 concern *how* owner-locked
  decisions are specified, not *whether*.

Runtime probes I ran (reproduced here because several findings rest on them):

```
$ .venv/bin/python -c "... dataclasses.fields(Plan|ExecResult|TaskEvent) ..."
Plan       ['combine','empty','next_tasks','open_once','process','stop','tasks']
ExecResult ['n_combines','n_partitions','stopped','value']
TaskEvent  ['bytes_read','error','key','n_entries','partition','phase','t','worker']      # §7.2 anchor OK

$ .venv/bin/python -c "... annotation-wide filter over graphed.__all__ ..."
['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']
compile_ir in __all__: True                                                                # §2.3d r15 OK

$ .venv/bin/python   # NumpyArray property deltas, 1-D source
dtype delta 0 / ndim delta 0 / shape delta 0 / T delta 1                                   # §2.2 r19 OK
$ ... on a (4,3) source: b.T -> GraphedTypeError "transpose without axes ... displacing the
                              partitioned axis 0"                                          # see LOW-4
```

---

## HIGH-1 — §6.1d's fill-side lineage unification and ancestor re-indexing have **no public surface** at m48; `graphed.selection(ctx)` is m51 and no parent/ancestry accessor is bound at all

**Section:** §6.1d (+ §2.3e, §2.2, §9.1, §10/m48).

**Detail.** §6.1d binds `Histogram.fill` as a combining point that must, itself: (a) decide whether
several input handles "sit on one ancestry chain", (b) pick the **most-derived** one, (c) raise on
divergent branches, and (d) **re-index every ancestor-context VALUE to the unified context across
the intervening lineage links**, per the r15 link-kind table (plan `:1552-1569`):

> **(1) mask-derivation link** (`ctx[mask]`, §2.6c) — re-index the ancestor value by THAT mask,
> label-aligned per §2.4 … **(3) universe/nominal projection link** … Links compose in lineage
> order, parent-to-child

`Histogram.fill` lives in **`graphed-histogram`** — verified,
`graphed-histogram-latest/src/graphed_histogram/boost.py:152-212` — a different distribution from
`graphed`. §2.3e already recognised this class of problem and fixed it once for the handle itself
(plan `:791-798`): "the slot alone is not reachable across a package boundary: §6.1d requires
`Histogram.fill` to read its inputs' handle … so m48's fill-shaped anchors … were implementable only
by reaching into another package's private slot". The identical argument applies verbatim to the
**lineage relation and the intervening masks**, and there it is *not* fixed:

- §9.1's whole context surface is `labels` / `universe` / `nominal` / `context_of` / `weight` /
  `variations` (m50) / `selection` (**m51**). There is no `parent_of`, no ancestry predicate, no
  "re-index this value to that context" verb. I grepped the plan for
  `parent_of|ancestry chain|re-index` (30 hits) — every hit is a *requirement*, none is an
  *accessor*.
- `graphed.selection(ctx)` — the only bound way to obtain a derivation mask — is explicitly **m51**
  (plan `:2521-2523`, "the §6.4a bridge that makes the m51 skim sink reachable … m51"), and m48's
  §9.1 target line is closed with "only": "§9.1 partially — `graphed.labels`/`universe`/`nominal`/
  `weight`, `graphed.context_of` (r15), the per-label fill-node accessor, and
  `graphed_histogram.unpack` … **only**" (plan `:2655-2659`).
- Yet §10 assigns to `graphed-histogram`'s flat `tests/frozen/m48` (plan `:2707-2712`): "the
  fill-shaped clauses (… divergent-lineage AT THE FILL, **§6.1d's link-kind-(1) ancestor-VALUE
  re-indexing (r18)**, … and the projected-VALUE half of the universe/nominal clause)". Both
  re-indexing anchors are **m48**, both are asserted **over the VALUE** (elementwise against a
  manually re-indexed / projected reference, plan `:3085-3099` and `:3127-3136`), and both therefore
  require the fill to walk the lineage and obtain the masks at m48.

So an m48 implementer of `graphed-histogram` must either reach into `graphed`'s private context
object across a package boundary — the exact thing r15 bound `graphed.context_of` to prevent — or
the m48 anchors are unsatisfiable. It is not literally unimplementable (Python does not enforce the
boundary), which is why this is HIGH rather than BLOCKER; but the plan's own discipline ("every new
surface's spelling is pinned at freeze") has nothing to pin here, and a test-author freezing the
link-kind anchors at m48 freezes behaviour whose only bound implementation route violates the
factorization rule.

**Suggested fix.** Bind the missing seam(s) at m48 and add them to §9.1's m48 list. Cheapest shape,
consistent with what is already bound: (i) move **`graphed.selection(ctx)` to m48** (it already
answers per link kind, §9.1 r15/r16, and m51 only *uses* it), and (ii) bind one additional read-only
`graphed` verb the fill can drive the unification with — an ancestry/most-derived resolver over two
handles (e.g. `graphed.unify_contexts(*handles)`-shaped, spelling pinned at m48 freeze) — or,
alternatively, bind a single neutral seam `graphed.reindex_to(value, ctx)` that performs (1)/(2)/(3)
internally inside `graphed`, leaving `graphed-histogram` with `context_of` + that one call. Update
m48's §9.1 "only" list and §10's m48 target line accordingly.

---

## HIGH-2 — §6.4a's absent-operand case (ii), and m51's anchor for it, are stale against r19's handle-equality predicate: they freeze a REFUSAL for a program r19 ACCEPTS

**Section:** §6.4a(2a) (r19) vs §6.4a case (ii) and §10/m51's entry-check anchor.

**Detail.** r19 replaced the deciding rule with a single comparison (plan `:1939-1968`):

> **the supplied mask's own §2.3e context handle MUST EQUAL the record's context handle —
> `graphed.context_of(select_mask) is graphed.context_of(record)`**

and asserts the absent-operand cases survive: "a hand-built loose mask carries no handle (§2.3e Drop
rule) so it can never equal a contexted record's handle → (ii)'s refusal."

But case (ii) is written over a **different property** (plan `:1977-1980`):

> **(ii) the record has a handle but the supplied mask derived no context** — REFUSED at the
> `to_parquet` call, naming the record's context and stating that the mask has no lineage to check
> against

and m51's anchor repeats that wording verbatim (plan `:3598-3601`): "while a contexted record whose
supplied mask **derived no context** is refused naming the record's context".

"Carries no handle" and "derived no context" are not the same predicate. A mask recorded entirely
from reads **through the record's own context** — e.g. `select=(events.MET.pt > 50)` passed directly
instead of via `graphed.selection(sel)` — carries handle `events` (the §2.3e ORIGINATION rule, plan
`:820-831`) and has **derived no context**. Under r19's binding rule the handles are equal →
**ACCEPT** (and it is a legal, in-row-space mask). Under (ii)'s literal wording and m51's anchor →
**REFUSE**. A test-author who builds that fixture (it is at least as natural as a loose mask, and it
is the only fixture that distinguishes (ii) from (i)) freezes a refusal that hard-blocks a legal
skim spelling, read-only, for the life of the milestone — resolvable only by Test Dispute or an
integrity violation. This is the same defect class r19 itself repaired for §6.1a's slot keying and
r18 for `to_parquet`'s m48 disposition.

**Suggested fix.** Re-express (ii) over the operand r19's rule actually reads: "**(ii) the record has
a handle but the supplied mask carries NO context handle** (§2.3e Drop rule — a hand-built loose
mask) — REFUSED …". Re-word m51's anchor bullet identically, and state explicitly that a
contexted mask carrying the **record's own** handle is ACCEPTED whether or not any context was ever
derived from it (this is the r19 rule's stated intent, and it deserves its own positive control
alongside the four already listed, since it is the case that discriminates the two readings).

---

## HIGH-3 — §7.2's r19 `aggregate_plan` SEAM is an m48 `graphed` Implementation Target with **no m48 `graphed` frozen anchor**; every anchor that exercises it is fill-shaped and lives in `graphed-histogram`

**Section:** §7.2 (r19) + §10/m48 target line and anchor list.

**Detail.** r19 added a new m48 Implementation Target in `graphed` (plan `:2224-2245`):

> Binding: **`aggregate_plan` gains ONE pinned seam (exact spelling pinned at m48 freeze) that (α)
> lets the caller see the compiled output list before the worker closure is finalized … and (β)
> accepts per-plan variation metadata to be carried as an additive field on the shipped closure**

and m48's target line names it (plan `:2650-2655`). I verified the premise — `aggregate_plan`
compiles internally and builds `_PartitionReduce` from pre-built closures
(`graphed-latest/python/graphed/aggregate.py:68-108`, `compiled = compile_ir(session, *outputs)`
then `process = _PartitionReduce(...)`), and `graphed_histogram.plan()` builds `layout` at
`boost.py:282` before its `aggregate_plan` call at `:286` — so the seam is genuinely needed.

The problem is coverage. `grep -n "SEAM\|on_compiled\|factories over the compiled"` over the plan
returns exactly four hits: §7.2's binding, m48's target line, and the revision history. **No frozen
anchor mentions it**, and none of `graphed`'s m48 anchors can reach it incidentally:

- §7.2 schema absence (r19) is now pure dataclass introspection (`dataclasses.fields(Plan)` …) —
  builds no plan (plan `:2951-2963`);
- §3.2 determinism is `compile_ir` output bytes only;
- §1.2's `graphed`-half clauses are arena Δ / node id / `compile_ir` returning one value;
- §2.5's diagnostic is a `compile_ir` diagnostics channel;
- every anchor that *does* consume the seam — §6.1c's index-based `layout`, §7.2's own varied merge
  refusal — is fill-shaped and §10 places it in `graphed-histogram`'s flat `tests/frozen/m48`.

The DoD gate is per repo ("≥90% diff coverage **from the frozen suite**", plan `:3659-3662`), so
new `graphed/aggregate.py` lines covered only by another repo's suite fail it. This is precisely the
argument r14 used to move §3.4 out of m48 and r18 used to drop `to_parquet` from m48's table; the
same argument was not applied to r19's own new target. (A second, smaller instance of the same
shape: `graphed.broadcast_like`'s **awkward** implementation lives in `graphed/awkward/` while
m48's `graphed` half is pinned to `tests/frozen/frontend/m48` and every fill anchor exercising the
awkward branch is in `graphed-histogram`.)

**Suggested fix.** Add an explicit m48 anchor to `graphed`'s `tests/frozen/frontend/m48` over the
seam itself — an **unvaried** `aggregate_plan` call through the new (α) form asserting the caller
receives the compiled artifact and the resulting plan behaves identically to today's positional
form, plus (once §8.2(i) lands) an m49 anchor for (β). Add a sentence to m48's anchor list. While
there, state whether the `graphed`-side `broadcast_like` disposition anchor uses the awkward backend
(covering the recorded `ak.broadcast_arrays` branch) or the numpy no-op branch — or name both.

---

## MID-1 — `graphed.context_of` on a `Varied` is bound two different ways: "answering on the nominal member" (§2.3d/§2.3e) vs "the container carries the most-derived handle" (§2.1 r18) — and §6.4a(2a)'s r19 predicate is built on it

**Section:** §2.3e `:797-800` / §2.3d, vs §2.1 `:466-473`, consumed by §6.4a(2a) `:1948-1952`.

**Detail.** §2.3e binds the accessor's disposition:

> It carries a §2.3d disposition — *eager-metadata*, **answering on the nominal member for a
> `Varied`** (plan `:798-799`)

while §2.1 r18 binds the container's own handle:

> **all members' handles MUST lie on ONE ancestry chain, the container carries the most-derived
> one**, and divergent handles are a construction-time error (plan `:471-473`)

These disagree whenever the most-derived handle belongs to a **non-nominal** member — which §2.1
explicitly permits (only *divergent* handles are refused; an ancestor/descendant pair on one chain
is accepted, and §2.1's construction checks are form compatibility + session + source, not row
space). *Eager-metadata* answering on the nominal member is sound for `gak.fields`/`type_of`
(§2.1's form compatibility makes every member agree — the justification §2.3c actually gives); it is
**unsound for `context_of`**, because handles are the one per-member property the plan does not
require to agree.

This is not cosmetic: r19 re-expressed §6.4a's level-0 lineage predicate as
`graphed.context_of(select_mask) is graphed.context_of(record)` — and both operands are routinely
`Varied` (`events.Jet` under a JES shift; `graphed.selection(sel)` is bound to return a `Varied`
mask). If `context_of` answers on the nominal member while the container's bound handle is the
most-derived one, the r19 predicate compares something other than what §2.1 says the container
carries, and the four m51 controls are verified in the plan against the *container* reading.

**Suggested fix.** One clause in §2.3e: "`graphed.context_of` of a `Varied` returns **the
container's** handle (the most-derived member handle §2.1 binds), not the nominal member's; the
*eager-metadata* class label describes only that it is answered without recording." Add the
one-line discriminator to m48's §2.3d table anchor (a container built from an ancestor-handled
nominal member and a more-derived non-nominal member answers with the more-derived handle).

---

## MID-2 — §7.2's seam (α) is under-specified in a way that breaks m49: "compiled output ids" is not enough for `variation_labels`

**Section:** §7.2 (r19) vs §8.2(i).

**Detail.** (α) is offered as an either/or (plan `:2238-2241`): "e.g. `reduce`/`empty` supplied as
**factories over the compiled output ids**, or an `on_compiled`-shaped hook". Those two are
equivalent for §6.1c's `layout` (which needs only `node id → position`, derivable from
`outputs()`), and for §7.2's own merge refusal (distinct compiled outputs vs distinct marked ids).
They are **not** equivalent for §8.2(i), which the same paragraph names as the third consumer:
`variation_labels` is keyed on `(reduced_node_id, member_index)` obtained from the m49 core accessor
that answers "**for the reduction that produced a given compiled artifact**" (plan `:2444-2445`).
That accessor takes the compiled artifact; a list of output ids cannot produce it. An m48
implementer picking the factory spelling therefore ships a seam m49 cannot use, and m49 must either
re-open an m48-frozen surface or compile twice — which §7.2 explicitly forbids ("`plan()` MUST NOT
compile a second time … a frontend-side `compile_ir` before `aggregate_plan`'s own would double
it", plan `:2241-2243`).

**Suggested fix.** Bind (α) to expose the **compiled artifact** (the `CompiledGraph`), not merely
the output ids — e.g. "an `on_compiled(compiled)`-shaped hook, or `reduce`/`empty` supplied as
factories **taking the `CompiledGraph`**" — and say so with the m49 dependency named, exactly as the
paragraph already names §6.1c and §7.2 as consumers.

---

## MID-3 — §2.1(b)'s new row-space contract closes only the ANCESTOR direction; a factor read through a DESCENDANT context violates the stated MUST with no bound error and no anchor

**Section:** §2.1(b) (r19), plan `:404-420`.

**Detail.** r19 binds:

> the registered factor — and every member of a `Varied` factor — MUST live in the TARGET context's
> row space, i.e. be read through that context **or through an ancestor of it**. An
> ANCESTOR-handled factor is re-indexed … ; **a factor whose handle is on a divergent branch is the
> construction-time divergence error**

Three cases exist, two are bound: target-or-ancestor (accepted, re-indexed) and divergent (error).
The third — a factor handled by a **descendant** of the target — violates the MUST and is *not*
divergent (it lies on the same ancestry chain, so §2.1 r18's divergence check passes), and no
re-indexing exists for it (a mask has no inverse — the plan makes exactly this argument for §6.4b at
`:2039`). The natural spelling is a common user error and precisely the one the exemplars' per-channel
`deepcopy(Weights)` exists to avoid: `graphed.vary(events, "btag", btag_sf(sel.Jet), is_weight=True, …)`
— registering a selection-scoped SF onto the root context. I verified the failure mode r19 cites:
`Session.record_op` validates only the backend's `op_form` and never lengths or row spaces
(`graphed-latest/python/graphed/session.py:142-168`), so this records cleanly and dies at execution
with a message about nothing in particular — the same hole r19 opened §2.1(b) to close.

**Suggested fix.** Restate the violation half as total: "a factor whose handle is neither the target's
nor an **ancestor** of it — including a **descendant** — is a construction-time error naming both
contexts and the direction of the mismatch." Add a negative control to m48's §2.1 stacking anchor
alongside its r19 parent-factor positive control (both are frontend-observable, so both stay in
`graphed`'s half).

---

## MID-4 — §2.2's third union term for `graphed.labels(ctx)` has no answer for a `vary`-derived or universe/nominal-derived context, while §9.1 binds `graphed.selection` to walk `vary` links; the §2.6 sketch's mainline `sel` IS vary-derived

**Section:** §2.2 `:486-489` vs §9.1 `:2530-2539`, §6.1d link kinds `:1562-1568`.

**Detail.** §2.2 binds `graphed.labels(ctx)` as the union of "(a) the ambient weight registry's
labels, (b) the labels of any `Varied` collections on the context, and **(c) the labels of the mask
that derived it (`None` for a root context)**". Only two lineage link kinds are dispositioned there:
root and mask-derivation. §6.1d binds **three** kinds, and §9.1 r16 explicitly binds
`graphed.selection(ctx)` to "skip over any number of `vary` links and answer as of the first
non-identity link" and r15 binds its universe/nominal answer. §2.2(c) carries neither walk.

This is not hypothetical: the §2.6 sketch's own `sel` is rebound by a `vary` call
(`sel = graphed.vary(sel, "btag", …, is_weight=True, …)`, plan `:1042-1044`), so the object whose
labels a user or a test asks for is a **`vary`-derived** context, for which (c) as written has no
value. m48 freezes `graphed.labels(ctx)` semantics (plan `:3117-3127`) and §2.2 makes the answer a
binding SUPERSET invariant. In the common case (a) rescues the answer, because a factor registered
into a mask-derived context is itself `Varied` and re-carries the mask's labels — but that is an
accident of the mainline program, not a rule, and a "uniform introspection verb answering less than
the sink produces" is the §2.5 confidently-wrong class §2.2 was rewritten (r13) to close.

**Suggested fix.** One-word repair, using the verb the plan already binds: replace (c) with "**the
labels of `graphed.selection(ctx)`** (§9.1 — which walks `vary` identity links and is `None` for a
root context; for a universe/nominal-derived context its answer is that label's unvaried member, so
the term contributes no labels)". Add the vary-derived case to m48's `graphed.labels` anchor
alongside its two existing programs.

---

## MID-5 — §10's m48 repo split leaves §7.2's varied merge-refusal assertion in `graphed`, where §7.2 r18's own SITE binding makes it unbuildable without `importorskip`

**Section:** §10/m48 split `:2672-2676` vs the §1.2 anchor bullet `:2797-2807` and §7.2 r18
`:2264-2267`.

**Detail.** §7.2 r18 binds the optimizer-merge guard's site precisely:

> **on the VARIED UNPACK PATH — the owner of the `(output, label) → node id` map, i.e.
> `graphed-histogram`'s group-plan builder (`plan()`, `src/graphed_histogram/boost.py:254-292`), NOT
> `compile_ir` and NOT `aggregate_plan`**

I verified `plan()` at `graphed-histogram-latest/src/graphed_histogram/boost.py:256-292`: it is the
only place `(output_name, Histogram)` pairs exist, so triggering the guard requires
`Histogram.fill` + `gh.plan(...)`. But §10's m48 split assigns to `graphed`
"§1.2 label-out-of-identity **except the RESULT-MAPPING half of its dedup clause**" — and the
§7.2-guard clause ("Assert §7.2's m48 guard: the VARIED program is REFUSED with a message naming the
labels") sits inside that same §1.2 bullet and is *not* in the exception list. The bullet's own
parenthetical hints at the answer ("with the SCOPE positive control alongside it (r18), **in
`graphed`'s half since it needs no fill**"), which implies the varied half belongs elsewhere, but it
never says where — and §10's general rule ("any clause whose assertion requires a `Histogram.fill`
lives in `graphed-histogram`'s flat `tests/frozen/m48`") is stated inside straddling-anchor **(3)**,
scoped to the §2.6/§6.1d mega-bullet. Placed literally per the split sentence, the varied half needs
`pytest.importorskip("graphed_histogram")` in `graphed` → SKIP in CI (`graphed pyproject.toml:29-48`
declares no `graphed-histogram`; CI installs `.[dev]`) → the milestone's merge guard silently
discharged, the exact failure mode §10 fixes three other times.

**Suggested fix.** Promote §10's "requires a `Histogram.fill` ⇒ `graphed-histogram`" sentence out of
straddling-anchor (3) to a general splitting rule for the whole m48 list, and amend the split
sentence's exception to read "§1.2 label-out-of-identity **except the RESULT-MAPPING half of its
dedup clause and the VARIED half of its §7.2 merge-guard clause**", both of which go to
`graphed-histogram`'s flat `tests/frozen/m48`; the unvaried scope positive control stays in
`graphed`.

---

## LOW-1 — §1.1's "family" check needs a `name → tags` decomposition that §2.2's bound `Varied` representation does not carry

**Section:** §1.1 r17 `:310-322` vs §2.2 `:476-477`.

**Detail.** §1.1 defines a family as "the set of tags carried by one `name` on one container,
**INCLUDING labels inherited through §2.1 stacking**", and binds the numeric-equal check to run
against inherited labels of the same `name`. §2.2 binds `Varied` as holding `{label: Array}` and
nothing else; on a context the per-name structure exists (`graphed.variations(ctx)` is "a per-name
listing"), but on a **loose** `Varied` (§2.1a, which stays public) there is no bound name→tags map.
The only available decomposition is prefix-matching `f"{name}_"` on labels, which is ambiguous
whenever one name plus an underscore prefixes another (`vary(v,"jes",up_2=…)` and
`vary(v,"jes_up","2"=…)` both produce `jes_up_2`; the duplicate-LABEL rejection catches that
particular pair, but the attribution ambiguity is what the family check reads). m48 freezes the
two-call cross-notation rejection on the family rule.

**Suggested fix.** One clause in §2.2: "`Varied` additionally retains, per `name`, the tags
registered under it (the operand §1.1's family check and §9.1's `graphed.variations` read); the
label mapping is the public shape, the name→tags map is internal." Or state the prefix rule
explicitly as the decomposition and note that a label collision is already rejected.

---

## LOW-2 — m49's target line omits §9.1's §5.3 projection-stats verb

**Section:** §10/m49 `:3189-3191` vs §5.3 `:3314-3322` / §9.1 `:2557-2561`.

**Detail.** m49's targets are "§3.3, §3.4 (frozen anchor), §5, §7, §8, plus §2.5's shift-after-weight
diagnostic". §9.1 marks the per-label projection-stats verb "m49, spelling pinned at m49 freeze", and
m49's anchor bullet consumes it. This is the same defect class the plan repaired for m48 (r13:
"m48's target line named no §9 section … leaving `graphed.weight` an m50 target that an m48 frozen
anchor consumes") and for m51 (r18: "§9.1 marks `graphed.selection` m51 and m51's anchors freeze
both, while the target line named only §6.4; the DoD scopes an implementer off the target line").

**Suggested fix.** Append to m49's target line: "**plus §9.1's per-label projection-stats verb**
(§5.3, spelling pinned at m49 freeze)".

---

## LOW-3 — the m49-landing `graphed` module verbs (§3.4 impact API, §5.3 stats verb) will be *discovered* by m48's frozen §2.3d exhaustiveness gate, but §2.3d assigns them no disposition class

**Section:** §2.3d `:730-741` vs §3.4 / §5.3.

**Detail.** m48's gate enumerates `graphed.__all__` filtered to functions "any of whose parameter
annotations MENTIONS `Array`" and asserts every member carries a disposition. I ran that filter
against `graphed-latest` (8 verbs today). §3.4's impact helper and §5.3's stats verb both take
Array outputs and land at m49 in `graphed.__all__`, so the frozen m48 gate will demand a class for
each. The self-repairing design does cover this (a new function arrives with its classification in
`src`), and the per-class floors are containment, so nothing reds — but §2.3d calls its enumeration
"EXHAUSTIVE over `graphed`'s public Array-consuming surface" while knowingly adding two members one
milestone later without naming their class, leaving the m49 implementer to guess between *expanding*
and a new class.

**Suggested fix.** One sentence in §2.3d: "the m49 verbs §3.4 and §5.3 bind enter the table
*expanding* when they land; the m48 gate's self-repair rule (classification in `src`) is the
mechanism, and m49's own anchors assert their per-verb shapes."

---

## LOW-4 — `NumpyArray.T` raises on any ≥2-D partitioned form, so §2.2/§2.3a's measurement-based property classifier and m48's `varied.T` anchor are fixture-sensitive

**Section:** §2.2 r19 `:526-549`, §2.3a `:594-604`, m48 anchor `:2906-2917`.

**Detail.** r19's discriminator is "access the property on a plain nominal `Array` and read the
`Session.node_count()` delta". Measured against `graphed-latest@ff7c607`:

```
gnp.ones(s, (4,))   ->  dtype/ndim/shape delta 0 ;  T delta 1                      # as the plan states
gnp.ones(s, (4,3))  ->  b.T raises GraphedTypeError: ill-typed op 'transpose' …
                        "transpose without axes reverses them, displacing the partitioned axis 0"
                        (graphed/numpy/__init__.py:297,420 via numpy/array.py:157-161)
```

So on the natural multi-dimensional fixture for a `T` test, the *measurement step itself* raises and
the gate cannot classify the name at all. §2.2's parenthetical does pin the probe to "a 1-D
`NumpyForm` source", but m48's anchor bullet — which is what a test-author works from — names
`varied.T` without repeating it, and the plan elsewhere makes a point of repeating exactly such
mid-freeze-discovery notes (`gak.full_like`, `stable()` rounding, `h.axes.name`, the r19 pt-cut jets).

**Suggested fix.** Repeat the constraint in m48's anchor bullet: "the property-classification fixture
is a **1-D** partitioned source — `NumpyArray.T` on a ≥2-D partitioned form raises
`GraphedTypeError` (partitioned axis 0 displacement), so a 2-D fixture reds the measurement step
rather than the implementation."

---

## LOW-5 — m48's §6.1a positive control claims `plan()`'s declared return type is unchanged; §6.1a's own slot keying forces it to widen

**Section:** §10/m48 `:2929-2935` vs §6.1a `:1386-1401`.

**Detail.** The anchor says a wholly-unvaried group plan keeps bare keys "so
`run(gh.plan({...})).value["hi"]` still works and `plan()`'s declared `Plan[dict[str,
bh.Histogram]]` (`boost.py:262`) still types under `mypy --strict`". I verified the annotation is
literally at `graphed-histogram-latest/src/graphed_histogram/boost.py:262`
(`) -> Plan[dict[str, bh.Histogram]]:`). But §6.1a binds a **varied** plan's value to carry
`(output, label)` / `(output, None)` **tuple** keys — which that annotation forbids — so the
declaration must widen to a union key type. The m23 indexing (`out["hi"]`) does still type-check
under the widened union, which is the property the control actually protects; the sentence as
written asserts something stronger and false.

**Suggested fix.** Re-word: "…`run(gh.plan({...})).value["hi"]` still works and still type-checks
under `mypy --strict` once `plan()`'s return type widens to the union key form §6.1a binds
(`dict[str | tuple[str, str | None], bh.Histogram]`); the widening is part of m48's §6.1c target."

---

## Areas probed and found CLEAN (recorded so the next round need not re-run them)

- **§1.1 e-canonicalization edge cases.** I worked the r19 digit-count normalization by hand across
  `1.5e31` (mantissa "15" = 2, exponent adjusted 31−1 = 30, sum **32** = exactly the cap, LEGAL —
  matches the rendered `15` + 30 zeros), `1.5e32` (33 → reject), `0.15e33` (2 + 31 = 33 → reject,
  and the true value is 1.5e32 = 33 digits ✓), `150e-1` (3 + (−1) = 2 ✓), `1200e-2` (4 − 2 = 2 ✓),
  `0.0000000001e40` (1 + 30 = 31 ✓). The normalization is exactly right, including the trailing-zero
  and leading-zero cancellations, and the "before any rendering" ordering closes the `1e1000000000`
  hazard. Integer rendering, negative zero → `0`, the `em`-never-bare property (a fractional value's
  minimal exponent is negative by construction), the re-render-non-minimal rule, and the
  cross-notation e/p disjointness (`5em1` does not match `m?\d+(p\d+)?`; `2p5` does not match the
  e-grammar; `m2` matches both to the same value) are all internally consistent. The three tag
  channels and the four shadowed signature names are consistent with §2.1's overloads.
- **§2.4 label-aligned union vs §2.6c lineage unification.** Worked end-to-end on the §2.6 sketch:
  ambient labels {pu, pdf, btag} × collection labels {jes} at a fill from a varied-mask-derived
  context. Per-label row spaces agree (value and ambient weight are re-indexed by the *same* label's
  mask), the corpus stacking semantics (`old_ambient[jes_up] × central-btag-SF[jes_up]`) fall out,
  and no cross product is constructible. Consistent with `graphed-corpus
  src/graphed_corpus/analyses/systematics.py:60-76,25-36`, which I read.
- **§6.2 axis mode vs shift-sibling scalar labels.** The arity `1 + |S|`, the per-fill carrier
  entering `content_hash((spec, variation_payload))`, the one-slot `(output, None)` keying, the
  per-slot spec taken from the fill node, and `_GroupReduce`'s summation of disjoint category bins
  are mutually consistent, and `FillEvaluator._flat` does pass scalars through
  (`graphed-histogram boost.py:39-47`, "scalars pass through for boost broadcasting"). §6.1b/§6.2's
  r19 `S`/`W` split is total and disjoint, so both frozen arity formulas stay correct under a
  `Varied` `sample=`.
- **§6.1a/§6.1c/§9.1 unpack after r19.** The three slot key forms are disjoint per output, a varied
  sibling output always carries ≥2 labels, `_add_groups` is a key-wise `+`
  (`boost.py:120-122`, verified) so heterogeneous keys are safe, and the deleted per-output MODE
  field is genuinely unwitnessable. The r19 scoping does keep m23 green — I read
  `tests/frozen/m23/test_group_plan.py:60-105` and confirmed all three bare-name indexings.
- **§6.4 structure rule vs object-level migration.** Level-0 OR on rows, no inner mask applied to
  buffers, per-level packed masks, same-offsets refusal, and XOR-delta same-shape are consistent for
  scale/smear shifts; the multiplicity-changing case is explicitly refused and parked. §6.4f's
  node-id resolution is buildable at the driver: `to_parquet` calls `compile_ir` itself
  (`graphed-latest/python/graphed/awkward/io.py:229`) and `_WritePart` is a frozen dataclass shipped
  per partition (`:100-127`), so the table can be a field as bound.
- **§5.4 boundary refusal vs §6.4 write plans.** No conflict: the write path is
  `gw.write_plan(...)` → plain-callable `Plan` (`python/graphed/write.py:32-43`), no
  Exchange/Join involvement.
- **numpy backend exemptions.** §6.1d's numpy `broadcast_like` no-op and §6.4f's numpy-idiom write
  refusal are mutually consistent and both correctly scoped to the *idiom* function rather than a
  neutral dispatcher.
- **Package boundaries.** `graphed-core` gains only a read-only Rust accessor (no awkward);
  `graphed` proper gains no `boost_histogram`, no awkward, no pyarrow import (the duck-typed `.axes`
  detection and the awkward-idiom placement of `to_parquet`/`read_varied` hold); `vary` is a neutral
  module verb; the fill's unpacker is in `graphed-histogram`. The one boundary problem is HIGH-1.
- **Milestone boundaries.** m48/m49/m50/m51 target lines agree with their sections after r19's
  repairs, except LOW-2 (m49/§5.3 verb) and MID-5 (m48 anchor placement). §7.2 appearing in both
  m48's and m49's target lines is harmless overlap.
- **§7.2 schema-absence anchor (r19).** Field sets verified exactly as spelled (probe above).
- **§7.3 checkpoint invalidation vs m51 writes.** r17's scoping holds: `write_plan` builds a
  plain-callable `Plan`, which `run_resumable` cannot take, so no shipped journal churns.

---

## Verdict

**DIRTY.** Three HIGH findings and five MID findings, no BLOCKER.

The plan is internally coherent to an unusual degree and the r19 changes are, on my reading, all
improvements — the e-form digit-count normalization, the `S`/`W` lowering definitions, the deleted
MODE field, the §6.1a unvaried scoping and the §8.2(i) `2N+2` correction each hold up under
independent checking. The residue is concentrated exactly where the brief predicted: **the newest
surfaces**. r19 introduced two new bindings (§6.4a's handle-equality predicate, §7.2's
`aggregate_plan` seam) and left their neighbourhoods un-swept — the stale absent-operand case (ii)
and its m51 anchor (HIGH-2), and a new m48 target with no m48 anchor (HIGH-3). HIGH-1 is older and
larger: §6.1d has been accumulating fill-side lineage obligations since r12 (link kinds, most-derived
unification, ancestor re-indexing, divergence) while the public surface those obligations must be
implemented through was only ever extended once (`context_of`, r15) — the masks and the ancestry
relation are still private, one package away, with m48 anchors already written over them.

All eight findings have local fixes: one clause each for MID-1/3/4, one word for HIGH-2, one anchor
for HIGH-3, one sentence for MID-2/5, and for HIGH-1 either moving `graphed.selection` to m48 or
binding one neutral re-index seam. None requires reopening an owner-locked decision, and none
requires re-scoping a milestone.
