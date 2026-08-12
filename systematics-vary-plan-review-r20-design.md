# systematics-vary-plan review — round 12, DESIGN SOUNDNESS lens

- **Plan revision reviewed:** r20 (`systematics-vary-plan.md`, 4841 lines, read in full: Part I,
  every PART II section, §10 milestones, §11, §12, Anchors appendix, revision history r20–r16).
- **Lens:** design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections; unhandled interactions; under-specified Implementation Targets; package-boundary
  / factorization violations; milestone-boundary consistency. Deepest attention to the surfaces the
  brief flags as least-reviewed: §2.6 functional context, §6.1d, §6.4/m51, §1.1 r9 e-canonicalization,
  and the r20-new §7.2 `aggregate_plan` seam / §6.1d lineage seams.
- **Date:** 2026-07-30.
- **Owner-locked decisions** (naming, functional surface, e-form encoding, event-context attachment,
  record-time expansion, m48–m51 scope incl. §6.4, JER-SF non-ordering, the Phase-2 pull-in) were
  taken as given; nothing below asks for a different choice. No `OPEN ITEMS (owner)` block is present
  in the header, so nothing was excluded on that ground.
- **Verification roots used** (all facts below were measured by me in this session, in these trees):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (its own `.venv`, awkward 2.12.0, no pyarrow)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`
  - `/private/tmp/claude-501/graphed-exec-check`, `graphed-corpus-latest`, `uproot5-graphed` (read-only checks)
  - probes written to `/tmp/probe_r20_seam*.py`

---

## Findings

### 1. HIGH — §7.2's `node id → position` derivation "from the compiled output list" is not computable; the seam's first named consumer is spurious

**Section:** §7.2 (plan `:2322-2350`), consumed by §6.1c (`:1545-1553`) and m48's §6.1a anchor
(`:3116-3140`).

**Detail.** §7.2 binds: *"The frontend owns `(output, label) → node id` … and derives `node id →
position` from the compiled output list"*, and r19/r20 then justify a NEW `aggregate_plan` seam
(an m48 Implementation Target with its own frozen anchor) on the ground that *"§6.1c's index-based
`layout` is 'derived frontend-side from the compiled output list' yet is a constructor argument of
`_GroupReduce`/`_GroupZero`, which are passed INTO `aggregate_plan`"*.

Both halves of that are wrong against the measured code:

1. **The compiled output list is in the REDUCED id space**, so it cannot be joined to the record node
   ids the frontend owns. Measured (probe `/tmp/probe_r20_seam4.py` vs `graphed-latest@ff7c607`):
   record ids `src=0, dead=1, b=2, e=3, c=2`; `compile_ir(s, b, e, c)` →
   `GraphStore.deserialize(ir).outputs() == [1, 2]` and `evaluate_ir` returns 2 values whose contents
   are b's and e's. The reduced ids `1,2` bear no relation to the record ids `2,3`. The plan itself
   establishes why (§8.2(i), `:2560-2563`: "record-time ids are wrong, because DCE compacts and
   remaps … the pipeline rebuilds into a fresh interned store") and states that the record→reduced
   map **does not exist** until m49's new core accessor. So at m48 there is no way to turn
   "the compiled output list" into `node id → position`.
2. **The same probe shows `s._store.outputs()` is `[]` after `compile_ir`** — `compile_ir` passes
   `outputs=ids` into `reduce()` (`python/graphed/execute.py:70-80`) and never calls
   `GraphStore.mark_output` on the record store. The plan's mechanism citation for the derivation
   (`mark_output` de-dups, `src/store.rs:152-153`) therefore describes a call the compile path does
   not make; the dedup that actually collapses positions happens when the *reduced* store is built.
3. Consequently the workable derivation needs **no seam at all**: positions are the index of first
   occurrence in the frontend's OWN dedup-ordered list of requested record ids — which `plan()`
   already holds as `fill_nodes` (`graphed-histogram src/graphed_histogram/boost.py:281-288`,
   `fill_nodes` built at `:281`, `layout` at `:282`, passed at `:286-290`). Measured: requested
   `[b(2), e(3), c(2)]` → 2 values in `b, e` order, i.e. exactly first-occurrence order of the
   distinct record ids. Under §7.2's own m48 guard (which refuses varied programs whose distinct
   compiled outputs fall short of distinct marked record ids) this derivation is exact for every
   program m48 admits.

Net effect: §6.1c's `layout` never needed the compiled artifact, so the "constructor argument"
problem the r20 seam was introduced to solve does not exist for that consumer; and an implementer
who follows §7.2 literally will try to key positions by compiled ids and find they do not match
anything he owns.

**Evidence.**
- `/private/tmp/claude-501/graphed-latest/python/graphed/aggregate.py:95-96,108` — `compiled =
  compile_ir(session, *outputs)` then `process = _PartitionReduce(…)`, then `return Plan(...)`.
- `/private/tmp/claude-501/graphed-latest/python/graphed/execute.py:70-80` — `ids = [arr.node_id …]`
  passed as `outputs=ids` to `reduce`/`serialize`; no `mark_output` call.
- `/private/tmp/claude-501/graphed-latest/src/optimizer/mod.rs:88-116,327-331` — DCE remaps, and the
  reduced `outputs` are `comp_to_reduced[comp_id[o]]` per requested output.
- Probe output (this session): `record ids: src 0 dead 1 b 2 e 3 c 2` / `record store outputs(): []`
  / `reduced outputs(): [1, 2]` / `n values: 2` with values `[0,2]` and `[0,3]`.

**Suggested fix.** Re-bind §7.2's derivation to the operand that exists: *the frontend derives
`node id → position` as the index of first occurrence in its OWN ordered list of marked record ids
(the list it passes to `compile_ir`), which is exactly the order `evaluate_ir` returns values in;
the COMPILED artifact is required only for §7.2's shortfall guard and for m49's §8.2(i) keying.*
Drop §6.1c's layout from the seam's list of consumers (and drop the "constructor argument of
`_GroupReduce`" rationale), and correct the `mark_output` mechanism citation to the reduced-store
dedup that `reduce(outputs=…)` performs.

---

### 2. HIGH — §7.2's seam half (β) cannot be satisfied as an input parameter: `variation_labels` is only computable from the artifact the same call produces

**Section:** §7.2 (`:2345-2371`), §8.2(i) (`:2532-2563`), m49 anchor (`:3583-3600`), m48 target line
(`:2792-2797`).

**Detail.** r20 binds ONE seam doing two things: *"(α) lets the caller see the COMPILED ARTIFACT …
before the worker closure is finalized, and (β) accepts per-plan variation metadata to be carried as
an additive field on the shipped closure (m49's `variation_labels`, §8.2(i))"*, and pins its shape as
*"a NEW optional keyword/hook — `on_compiled(compiled)`-shaped"*.

(β) is not satisfiable by a value supplied at call time:

- §8.2(i) binds `variation_labels` keyed on **POST-REDUCTION** ids, obtained through the m49 core
  accessor "for the reduction that produced a given compiled artifact" — i.e. it is a function of the
  `CompiledGraph` that `aggregate_plan` produces **internally** (measured: `compiled = compile_ir(...)`
  at `python/graphed/aggregate.py:95`, one line before `_PartitionReduce(...)` at `:96`).
- §7.2 explicitly forbids the only other route: *"`plan()` MUST NOT compile a second time"*.
- §8.2(i) declares the field as an **immutable sorted tuple**
  (`tuple[tuple[tuple[int, int | None], tuple[str, ...]], ...]`, `:2532-2541`) precisely for
  determinism, so it cannot be a mutable holder the (α) callback fills before `_PartitionReduce` is
  constructed.

So with (α) read as see-only (which is what "lets the caller SEE" and the literal
`on_compiled(compiled)` spelling say), there is no path from the callback's computation into the
shipped closure. The only compositions that work are (i) the hook RETURNS the metadata and
`aggregate_plan` attaches it, or (ii) the metadata parameter accepts a *callable* of the compiled
artifact. Neither is bound, and the m48 anchor freezes only *"the new hook fires EXACTLY ONCE and
receives the `CompiledGraph`"* (`:3002-3013`) — which is green against the see-only spelling.

This is the identical trap the same paragraph was written to close one axis over: §7.2 argues at
length that the artifact must be the `CompiledGraph` and not an id list, because *"an m48
implementer choosing the narrower spelling would ship a seam m49 cannot use, and m49 could then only
re-open an m48-frozen surface or compile twice, which the next sentence forbids."* The direction of
the metadata flow is left exactly as open, with the same consequence at exactly the same milestone
boundary (m48 freezes the spelling; m49 is the only consumer).

**Evidence.**
- `/private/tmp/claude-501/graphed-latest/python/graphed/aggregate.py:68-108` — signature takes
  `reduce`/`combine`/`empty` as pre-built callables; `compile_ir` at `:95`; `_PartitionReduce`
  constructed at `:96-104` from those parameters; `Plan` returned at `:108`.
- `/private/tmp/claude-501/graphed-histogram-latest/src/graphed_histogram/boost.py:100-118` —
  `@dataclass(frozen=True) class _GroupReduce` with `layout: tuple[...]` (frozen, immutable) —
  the same immutability that blocks post-hoc filling.
- Plan `:2350` "(β) accepts per-plan variation metadata"; `:2358-2360` "The seam is a NEW optional
  keyword/hook — `on_compiled(compiled)`-shaped"; `:2367-2369` "`plan()` MUST NOT compile a second
  time".

**Suggested fix.** Bind the direction: *the hook is called with the `CompiledGraph` before the worker
closure is constructed and its RETURN VALUE (a mapping/tuple, or `None`) is attached to the shipped
closure as the additive field*; state that (β) is that return channel, not a separate call-time
parameter. Add one sentence to m48's (α) anchor freezing that a returned value is carried onto the
closure (a trivially observable property at m48 with a dummy payload), so m49 cannot be blocked by an
m48-frozen see-only spelling.

---

### 3. MID — §6.1d does not order label-set inference against link-kind-(3) projection; m48's own anchor fixture has two defensible result shapes

**Section:** §6.1d (`:1596-1600` label-set rule; `:1631-1638` link kinds), §2.2 (`:530-536`), m48
anchor (`:3333-3341`).

**Detail.** §6.1d(d) binds *"the fill's label set is the §2.4 union of value-borne labels,
ambient-weight labels, and explicit `weight=[...]` factor labels"*. Several paragraphs later it binds
link kind **(3) universe/nominal projection — "PROJECT each ancestor `Varied` value to that label's
member …, yielding an unvaried value in the ancestor's row space"**. Nothing says whether the label
set is collected **before** or **after** that projection, and for link kind (3) the two give
different answers (for kinds (1) and (2) the order is immaterial, since both are label-preserving).

On m48's own anchored fixture `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` with
`sel = events[varied_mask]`:

- Unified context = `graphed.nominal(sel)` (most-derived). Its ambient weight is "that label's …
  ambient weight" (§2.2 `:530-536`), i.e. unvaried; its `graphed.selection` is an unvaried `Array`
  (§9.1 `:2666-2671`), contributing no labels (§2.2 r20, `:509-521`).
- The ONLY label source is the ancestor value `sel.MET.pt`. Collected **before** projection the fill
  carries the shift labels (every universe holding identical, nominal-projected content); collected
  **after**, the fill is wholly unvaried and, by §6.1a (`:1436-1439`), the output must be a **bare
  `hist`**, not `{"nominal": hist}`.

m48 freezes this fixture ("asserted over the resulting VALUE … compared elementwise against a
manually projected reference"), so the test-author must pick one, read-only, and the two picks are
mutually red. This is the same defect class the plan repaired for §6.1a-vs-§6.1c in r18.

**Evidence.** Plan `:1596-1600`, `:1631-1638`, `:3333-3341`; §2.2 `:530-536`; §6.1a `:1436-1439`.
No sentence in §6.1d, §2.2 or §10 sequences the two operations.

**Suggested fix.** State the order once in §6.1d: *the fill's label set is computed on the inputs
AFTER lineage re-indexing/projection, so a value reached across a universe/nominal projection link
contributes no labels*; and add to m48's anchor that this fixture's output is a **bare `hist`** (the
§6.1a unvaried shape), which is also the discriminator against a "labels kept, contents identical"
implementation.

---

### 4. MID — §2.3d's disposition for `graphed.reindex_to` ("same labels") contradicts §6.1d(B) and §2.4

**Section:** §2.3d (`:726-730`), §6.1d(B) (`:1662-1665`), §6.1d link kind (1) (`:1632-1634`), m48
anchors (`:3014-3023`, `:3291-3299`).

**Detail.** §2.3d r20 classifies the new seam: *"`graphed.reindex_to` … BROADCASTS — a `Varied` value
gives a `Varied` with the same labels, each member re-indexed by that label's own mask per §2.4"*.
But §6.1d(B) binds it as *"returns `value` re-expressed in `ctx`'s row space by composing link kinds
(1)-(3) …, **label-aligned per §2.4**"*, and link kind (1) is *"re-index the ancestor value by THAT
mask, label-aligned per §2.4 (each label's member by that label's mask, nominal's by nominal's)"*.

§2.4 is a **union** rule. On m48's own link-kind-(1) fixture the value is **unvaried**:
`h.fill(events.MET.pt, sel.MET.pt)` with `sel = events[varied_mask]` — `MET` is not a varied
collection, so `events.MET.pt` is a plain `Array`. Re-indexing it into `sel`'s row space **must**
produce a `Varied` carrying the MASK's labels (each label's rows), or its per-label lengths cannot
match `sel.MET.pt`'s — which is exactly what the anchor asserts ("compared ELEMENTWISE,
label-aligned, against a manually re-indexed reference (each label's ancestor value by that label's
mask, nominal's by nominal's)", `:3296-3298`).

So `reindex_to` demonstrably does **not** preserve the input's label set: it must ADD the mask's
labels, including turning a plain `Array` into a `Varied`. §2.3d's one-line description says the
opposite, and it is the line an implementer classifying the verb (and the m48 table gate) works from.
The precedent is already the other way — §2.3d's own `broadcast_like` entry (`:721-725`) says
"returns a `Varied` whose labels are the §2.4 **UNION**" — so the fix is a wording alignment, but as
written the narrow reading silently drops the mask's labels, i.e. the §2.5 confidently-wrong class.

**Evidence.** Plan `:726-730` vs `:1662-1665`, `:1632-1634`, `:3291-3299`; §2.3d `:721-725` for the
union-shaped precedent; §2.4 `:974-980` (union, not intersection/identity).

**Suggested fix.** Re-word §2.3d's `reindex_to` entry to match §6.1d(B): *"BROADCASTS — the result's
labels are the §2.4 union of the value's labels and the intervening masks' labels; an UNVARIED value
re-indexed across a `Varied` mask link becomes a `Varied` carrying that mask's labels."*

---

### 5. MID — §6.4e's "MUST reproduce awkward's own KV entries" names no route, and the only producer measured is an awkward PRIVATE module

**Section:** §6.4e (`:2246-2251`), m51 manifest anchor (`:3879-3887`).

**Detail.** §6.4e binds: a varied write *"takes the `ak.to_arrow_table` + `pq.write_table` path and
MUST reproduce awkward's own KV entries alongside the graphed manifest, with `ak.from_parquet`
round-tripping the augmented file as a frozen m51 anchor"* — because the arrow path measurably drops
`awkward_array_metadata`. It names no mechanism for reproducing that entry.

Measured in `graphed-latest`'s own environment (awkward 2.12.0): the ONLY definition of that key is
`awkward/_connect/pyarrow/table_conv.py:16` — `AWKWARD_INFO_KEY = b"awkward_array_metadata"` — inside
awkward's **private** `_connect` package; `ak.operations.ak_to_parquet` contains no occurrence of the
string at all (it reaches it via the imported private helper
`convert_awkward_arrow_table_to_native`). So the requirement as written is satisfiable only by
importing another distribution's private module — precisely the failure mode §2.3e and §6.1d(A)/(B)
were each opened to eliminate inside this project ("satisfiable only by reaching into `graphed`'s
private context object — the very thing `context_of` exists to prevent", `:1653-1657`), applied to a
third-party package where the project has no ability to add a seam.

A public composition does exist (write once with `ak.to_parquet`, re-read the table and re-write with
merged schema metadata; or `Table.replace_schema_metadata` over whatever `ak.to_arrow_table` yields
plus a copied entry), but it costs a second write and is not the path §6.4e bindingly names. Left as
is, m51's implementer either violates the package hygiene this plan enforces everywhere else, or
silently substitutes a different write path than the one §6.4e binds — while m51's byte-identity and
`ak.from_parquet` round-trip anchors are frozen over the outcome.

**Evidence.**
- `grep -rn "awkward_array_metadata" .venv/lib/python3.12/site-packages/awkward/` in
  `/private/tmp/claude-501/graphed-latest` → 3 hits, all in
  `awkward/_connect/pyarrow/table_conv.py:16,23,47` (a private module).
- `inspect.getsource(ak.operations.ak_to_parquet)` contains no `awkward_array_metadata`; its module
  namespace imports `convert_awkward_arrow_table_to_native` from that private module.
- `Table.replace_schema_metadata` is used inside `ak_to_parquet` for `attrs`, so a public merge point
  exists.
- (pyarrow is not installed in that venv, so I did not re-run the plan's byte/KV probes; the design
  point above depends only on where the KV key is produced, which I did measure.)

**Suggested fix.** Bind the ROUTE, not just the outcome: name the public composition m51 must use
(e.g. *"build the table awkward's own writer would — `ak.to_parquet` to a temporary/in-memory sink,
or `pq.read_table` of an `ak.to_parquet` write — then `replace_schema_metadata` to add the graphed
manifest and `pq.write_table`; graphed MUST NOT import `awkward._connect.*`"*), and add the
no-private-import rule to §6.4's factorization sentence.

---

### 6. LOW — §6.4a's entry checks constrain lineage and row COUNT but never the DEPTH of a level-0 `select=` mask; a jagged mask passes both and silently filters objects instead of rows

**Section:** §6.4a predicates (`:1988-2102`), §6.4d (`:2210-2227`).

**Detail.** §6.4a enumerates the entry checks as complete ("Each predicate has its own error message,
and the m51 anchors name which predicate decides which positive control"). For a level-0 mask the
gate is (2a) context-handle equality (record-time) and (2b) row-count equality (execution-time,
per partition). Neither constrains the mask's **depth**.

A per-object mask read through the record's own context — e.g. `select=(events.Jet.pt > 25)` instead
of an event-level mask — satisfies (2a) by construction (§2.3e ORIGINATION gives it the record's
handle, the same reason r20's new fifth positive control `select=(events.MET.pt > 50)` is accepted),
and satisfies (2b) because a jagged boolean over the record's own structure has the **same outer
length** as the record. The level-≥1 structural check does not apply, since the mask was supplied at
level 0. The writer then applies it as the level-0 OR: awkward's jagged-boolean indexing filters
INNER elements and keeps every row, so the file silently violates §6.4a's superset-row contract and
§6.4d's "inner cuts are never applied" rule — with no error anywhere.

This is small (a competent implementer may raise on the shape by accident) but it is exactly the
silent-corruption class the two predicates were introduced to close, and §6.4a claims the enumeration
is the gate.

**Evidence.** Plan `:2048-2052` (handle-equality predicate), `:2091-2094` ((2b) row-count only),
`:2095-2098` (structural check scoped to levels ≥ 1), `:2081-2089` (r20's accepted
`select=(events.MET.pt > 50)` case, which is per-EVENT and shares every property a per-OBJECT mask
has except depth). Awkward's jagged-boolean semantics (outer length preserved, inner filtered) are
standard and are what §6.4d relies on for its own inner masks.

**Suggested fix.** Add one clause to §6.4a: *a mask supplied at level 0 MUST be flat over the record's
row axis (depth 0); a jagged mask at level 0 is refused at the `to_parquet` call, naming the level and
the supported per-level channel* — and give it the m51 negative control alongside the four existing
(2a) controls.

---

### 7. LOW — §1.1's magnitude pre-check counts DIGITS while the cap bounds the canonical TAG's characters, so the sign decides the message class at the boundary m48 freezes

**Section:** §1.1 (`:257-281`), m48 grammar anchor (`:3373-3388`).

**Detail.** §1.1 binds two rejections around the same bound: (a) *"a canonical tag longer than 32
characters is REJECTED"* (generic tag-sanity), and (b) an integer-valued input *"whose plain-digit
rendering exceeds the cap is rejected at canonicalization with a message naming the magnitude"*,
where the magnitude test *"runs on the COMPUTED DIGIT COUNT BEFORE any rendering"*.

Negative values carry an `m` sign marker that is a character but not a digit, so the two bounds
disagree by one for them. `"-1.5e31"`: normalized digit count = 2 + 30 = **32** → passes the magnitude
test; canonical tag = `m` + 32 digits = **33 characters** → refused by the generic length rule with
the wrong message class. Its positive twin `"1.5e31"` (32 digits, 32 characters) is ACCEPTED and is
exactly the r20 boundary pair m48 freezes. So at the cap boundary the diagnostic depends on the sign,
which no clause states and no anchor covers — while r17 added the distinct-message requirement
precisely so "an implementation [cannot] emit the generic message for both and pass every anchor".

**Evidence.** Plan `:257-262` (cap), `:263-279` (magnitude rule + the `"1.5e31"`/`"1.5e32"` pair),
`:255-258` (`m` prefix is part of the canonical tag: `-1.5` → `m15em1`), m48 anchor `:3379-3385`.
Arithmetic checked by hand: 1.5e31 = 15 followed by 30 zeros (32 digits); the normalization
(mantissa digits after stripping the point/leading zeros, plus the exponent adjusted for where the
point sat) gives 2 + 30 = 32, matching.

**Suggested fix.** State that the magnitude pre-check compares the **rendered canonical LENGTH**
(digit count + 1 when the value is negative) against the cap, so a value and its negation get the
same treatment and the magnitude message covers both; or explicitly scope the 32-char cap to the
digit count. Either way, note the sign case in m48's boundary-pair anchor.

---

## Verdict

**DIRTY — two HIGH findings, three MID, two LOW.**

The plan remains internally coherent across the old surfaces: I probed the interactions the brief
named (§2.4 union vs §2.6c lineage unification; §2.1 stacking vs the shift form, including the
corpus b-tag-on-JES case and the r16 shift-after-weight ordering rule; §1.1 e-canonicalization across
exact-decimal, huge-exponent, integer-rendering and cross-notation cases; §6.2 axis mode vs
shift-sibling scalar labels and the per-fill carrier; §6.1c slot keying vs `_add_groups`/`_GroupZero`;
§6.4d structure rule vs object-level migration; §7.3 checkpoint scope vs m51 writes; §5.4 boundary
refusal vs the write path; the numpy exemptions) and found them sound and consistent. The package
boundaries hold: no requirement puts awkward or `boost_histogram` behind a neutral namespace, and the
r20 lineage seams (`unify_contexts`/`reindex_to`) correctly close the cross-distribution hole that
§6.1d's fill-side unification had. Milestone targets and section assignments line up (m48 §9.1 verbs,
m49's §3.4/§5.3/§2.5-diagnostic/seam-(β), m50's §6.1c axis slot, m51's `graphed.selection` and the
`to_parquet` table entry are each named on the target line that owns them).

The defects concentrate in exactly the newest surface. Both HIGH findings are about the r20
`aggregate_plan` seam — a new m48 Implementation Target with a frozen anchor whose stated first
consumer does not need it and whose only real consumer (m49's `variation_labels`) cannot be reached
through the bound shape. Finding 1 also invalidates a binding derivation sentence that §6.1c and
m48's §6.1a anchor rest on. Finding 3 leaves an m48-frozen fixture with two mutually-red readings.
None of these requires reversing an owner-locked decision, and all seven have local fixes.
