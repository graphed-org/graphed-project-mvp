# systematics-vary-plan — review r26, DESIGN SOUNDNESS lens

- **Lens:** design soundness (PART II as a coherent, implementable specification: contradictions
  between sections, unhandled interactions, under-specified Implementation Targets, package-boundary
  violations, milestone-boundary consistency).
- **Plan revision reviewed:** r26 (`systematics-vary-plan.md`, 6250 lines, read in full — Part I
  rationale, every PART II section, §10 milestones, §11, §12, the Anchors appendix and the revision
  history).
- **Date:** 2026-07-30.
- **Reviewer context:** isolated agent, fresh context. Every claim below rests on a file I read or a
  command I ran in this session.
- **Verification roots used:**
  - `/private/tmp/claude-501/graphed-latest` (`ff7c607`) — including its own `.venv` for runtime probes
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`)
  - `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`)
  - companion docs on disk (`systematics-vary-codebase-analysis.md`, `-litsearch.md`, `-worklog.md`)
- **Owner-locked decisions** (naming, functional surface, e-form canonical encoding, event-context
  attachment, record-time expansion, m48–m51 scope incl. §6.4, JER-SF non-monotone contract, the
  Phase-2 pull-in) were treated as fixed. No finding below asks for a different choice; each is an
  internal inconsistency, gap, or stale rationale in how a locked decision is **specified**.

Depth was weighted per the review brief toward the newest surfaces — §2.6, §6.1d, §6.4/m51, §1.1's
r9 e-canonicalization, and the r26 deltas (§8.2(i)'s producer, §3.4/§5.3's operand change, §2.1's
row-space generalization, the idiom-package gate, §9.2's manifest channel).

---

## Findings

### 1. HIGH — §8.2(i)'s r26 PRODUCER cannot produce the content §8.2 binds; m49's population anchor is unsatisfiable as written

**Section:** §8.2(i) (r26 producer clause) × §8.2(iii) × §10/m49's new `graphed-histogram` bullet.

**Detail.** r26 closed a real gap (the field had no owner) by naming one:

> "the association list is computed by the HOOK SUPPLIER — `graphed-histogram`'s group-plan builder
> (`plan()`, `src/graphed_histogram/boost.py:256-295`), the sole owner of the `(output, label) →
> record node id` map (§7.2 r18) — **by composing that map with the m49 core accessor**" (plan
> §8.2(i)).

That composition is `(output, label) → record_id` ∘ `record_id → (reduced_id, member_index)`. Its
image contains **only the marked fill nodes**. Three binding requirements in the same section need
strictly more:

1. §8.2(i) declares the transport as "a sorted association list from the PAIR key
   `(reduced_node_id, member_index)` to **that node's** labels" — every node, not every output.
2. §8.2 argues the map **must be set-valued** and cites §3.4 for the proof: "*a node shared by
   `jes_up` and `jes_down` but not nominal appears in BOTH impact sets*". A node shared by two
   labels but not nominal is by construction an **intermediate** node — two distinct labels' fill
   nodes are distinct marked outputs, so the composition's image can never witness that case.
3. §8.2(iii) binds the attribution hook to annotate a failure with `(reduced_node_id,
   member_index | None)` **at the op-dispatch and stage-member dispatch points**. Measured,
   `evaluate_ir` is a flat `for nd in store.nodes():` loop with op dispatch and an inner stage-member
   loop (`/private/tmp/claude-501/graphed-latest/python/graphed/execute.py:99-126`) — so the key
   handed to `variation_labels` is routinely an ordinary op inside a fused universe chain, not a
   fill node. Under the r26 producer that lookup misses and the m49 anchor "a failure raised inside
   the `jes_up` universe … re-raises carrying `variation == 'jes_up'`" only passes if the fixture
   happens to fail *at the fill node itself*.

§10/m49's new bullet makes the contradiction explicit and freezes it:

> "for a `(reduced_node_id, member_index)` key **two labels' cones both reach**, carries BOTH labels
> — the set-valued half the `graphed` accessor anchor can only witness as a key collapse."

A "key two labels' cones both reach" is not in the composition's image. A test-author who freezes
that assertion reds an implementation that follows §8.2(i)'s producer sentence literally, and an
implementer who follows the anchor is doing work the producer sentence does not authorise.

**Evidence.** Plan §8.2(i) (r26 producer clause), §8.2's set-valuedness paragraph, §8.2(iii),
§10/m49's `variation_labels` POPULATION bullet. Measured: `plan()` at
`graphed-histogram-latest/src/graphed_histogram/boost.py:256-295` (read this session — `fill_nodes`
at `:281`, `layout` at `:282`, `aggregate_plan` at `:286`); `evaluate_ir`'s per-node dispatch loop at
`graphed-latest/python/graphed/execute.py:99-126`.

**Suggested fix.** Bind the producer's computation, not just its owner: the group-plan builder walks
the **per-label record cone** of each `(output, label)` entry (`session.walk` from that label's fill
node — the same reachability §3.4 already binds, available to `plan()` because every fill node is an
`Array` carrying its `Session`), maps each reached record id through the m49 accessor, and unions
labels per `(reduced_id, member_index)` key. One sentence, e.g.: *"…by walking each `(output, label)`
entry's record cone, mapping every reached record id through the m49 accessor, and unioning the
labels per resulting key — which is what makes the map SET-VALUED; composing the output map alone
would key only the fill nodes and could never carry the shared-node case §3.4 proves."*

---

### 2. MID — §3.4/§5.3's r26 operand (`Sequence[Varied]`) cannot be formed for the plan's primary sink

**Section:** §3.4 × §5.3 × §9.1 × §4.3's optional cross-check.

**Detail.** r26 narrowed both introspection verbs from `Sequence[Array]` to `Sequence[Varied]` on a
correct premise ("`Array` is `__slots__ = ('_node_id','_session')` … carries NO label attribution" —
verified, `graphed-latest/python/graphed/array.py:127-128`). But the labelled outputs of the plan's
**primary sink** are not a `Varied`: §9.1 binds them as
`graphed_histogram.fill_nodes_by_label(h) -> dict[str, Array]`, and today's public accessor returns a
bare `list[Array]` (`graphed-histogram-latest/src/graphed_histogram/boost.py:218-219`). To call
either verb on a real varied histogram program the caller must **re-assemble a `Varied` out of that
mapping**, and the only public constructor is `graphed.vary(target, name, /, …, **tags)`, which
derives labels as `f"{name}_{tag}"`. That reconstruction:

- requires reverse-engineering `name`/`tag` from each label, which the plan itself says is not
  reliable — §2.2 r20: "prefix-matching `f'{name}_'` … mis-attributes whenever one name plus an
  underscore prefixes another — `vary(v, 'jes', up_2=…)` and `vary(v, 'jes_up', …)` both yield
  `jes_up_2`";
- needs one `vary` call per `name` (jes, btag, pu, pdf …) purely to rebuild a map the accessor
  already returns.

Two consequences inside m48–m51:

- **§5.3's own motivating example is not computable from observable containers.** §5.3 names "a
  shift needs an extra column (e.g. binned SF needing `Jet.eta`)". A scale factor is a **weight**;
  its columns are read through the weight factor, which reaches the **fill node**, not the axis
  observable. Measured, `read_columns(arrays: Sequence[Array], source_nid: int)` walks each array's
  cone and walks *through* External nodes to their inputs
  (`graphed-latest/python/graphed/projection.py:109-147`) — so the per-label read set that matches
  the plan's actual projection is the one taken at the per-label **fill** node.
- **§4.3's optional impact cross-check has no operand.** §4.3 offers "`impact(L)` minus L's own
  output node is disjoint from `reachable(selection_mask)`", whose operands are explicitly the
  per-label fill nodes obtained from §9.1's accessor — a `dict[str, Array]`, not a `Sequence[Varied]`.

**Evidence.** Plan §3.4 (r26 operand clause), §5.3 (r26 operand clause), §9.1's two entries and its
fill-node accessor entry, §4.3's cross-check, §2.2 r20's prefix-matching argument. Measured:
`Array.__slots__` at `graphed-latest/python/graphed/array.py:127-128`; `read_columns` signature and
External walk-through at `graphed-latest/python/graphed/projection.py:109-147`;
`Histogram.fill_nodes()` at `graphed-histogram-latest/src/graphed_histogram/boost.py:218-219`.

**Suggested fix.** Keep r26's label-attribution requirement but bind the operand as **the labelled
mapping the plan already produces**: `Mapping[str, Sequence[Array]]` (or `Sequence[Varied] |
Mapping[str, Sequence[Array]]`), i.e. exactly the shape `fill_nodes_by_label` returns, so the fill
sink and the loose-expression case are both reachable. m49's own anchors are unaffected (their
fixtures build loose containers), so this costs no frozen-suite change; add one sentence to §3.4 and
§5.3 and mirror it in §9.1.

---

### 3. MID — §2.1's r26 row-space rule is single-valued; §2.6c makes a `Varied`-mask-derived context's row space PER LABEL, and the (a)/(c) reduce-to-central rule then re-opens the hole the rule was written to close

**Section:** §2.1 (r26 generalization) × §2.1 r18 member rule × §2.6c.

**Detail.** r26 binds: "*every member MUST live in ONE row space — the TARGET context's in overloads
(b)/(c), the container's most-derived handle's in overload (a) — an ANCESTOR-handled member being
re-indexed across the intervening links per §6.1d kinds (1)-(3)*", with the parenthetical "(a
`Varied` produced by that re-index is then reduced to its central universe by this section's member
rule for (a)/(c))".

§2.6c bindingly denies that a context has *one* row space: "**Varied contexts (per-label row sets)
are first-class.** … the derived context's ROW SET DIFFERS PER LABEL". So for the case the whole
§2.6 idiom is built around — `sel = events[gak.num(jets) >= 4]` with a JES-varied `jets`, the
sketch's own central idiom — "the container's most-derived handle's row space" names a per-label
family, not a row space.

Follow the parenthetical through on that handle. `graphed.vary(events.Jet, "jes", up=X, down=Y)` with
members read through such a `sel`:

1. Container's most-derived handle = `sel` (per §2.3e r20).
2. The `"nominal"` member `events.Jet` is ancestor-handled → re-indexed across a kind-(1) link →
   per §2.3d's `reindex_to` rule it **becomes a `Varied`** carrying the mask's labels.
3. The (a)/(c) member rule then **reduces it to its central universe** → it lands at
   **nominal's** row count.
4. Every member reached through `sel` is likewise `Varied` (§2.6c) and likewise reduced → also
   nominal's rows.

So the container's members sit uniformly at *nominal's* rows while `graphed.context_of(container)`
answers `sel`, whose reads are per-label. At a downstream fill, §6.1d unifies to `sel`, and
`graphed.reindex_to` is bindingly the **identity** when "value already carries `ctx`'s handle" — so
nothing repairs the mismatch, and it "records CLEANLY … dying at execution", verbatim the failure
mode §2.1(b) r20 and §2.1 r26 exist to prevent (measured basis the plan itself cites and I
re-verified: `Session.record_op` validates only the backend's `op_form`,
`graphed-latest/python/graphed/session.py:142-168`).

By contrast §2.1(b) gets this right for weight factors, because §2.6c re-indexes the ambient
registry **label-aligned per §2.4** rather than projecting to nominal.

**Evidence.** Plan §2.1 (r26 clause and its parenthetical), §2.1 r18 member rule, §2.3d's
`reindex_to` disposition (r23), §2.3e r20, §2.6c's "Varied contexts (per-label row sets) are
first-class" and its label-aligned re-index rule, §6.1d(B)'s identity clause. Measured:
`Session.record_op` performs no length/row-space validation,
`graphed-latest/python/graphed/session.py:142-168`.

**Suggested fix.** State the row-space requirement **per label** wherever the governing handle is
`Varied`-mask-derived, and order the two rules explicitly: (i) a `Varied` supplied as a member of
overload (a)/(c) is reduced to its central universe **as supplied**, *before* any re-indexing; (ii)
the resulting member is then re-indexed to the target handle **label-aligned per §2.4** (each label's
member by that label's mask, nominal's by nominal's) — the identical operation §2.6c already binds
for the ambient registry. That makes the invariant "every member answers in the container handle's
per-label row spaces", which is what §6.1d's identity clause assumes.

---

### 4. MID — §6.4f's numpy-idiom write refusal has no bound trigger, no spelling, and no reachable entry point

**Section:** §6.4f × §6.4a's parenthetical × §10/m51's new `tests/frozen/numpy/m51` bullet.

**Detail.** §6.4f binds: "*the numpy-idiom write function refuses a varied write with a clear error
naming the awkward backend*", and §6.4a adds "*§6.4f's 'numpy backend EXEMPT' therefore means the
numpy-idiom function refuses*". r26 then pins an m51 frozen anchor for it in a newly created
directory (`graphed tests/frozen/numpy/m51`). Three things a test-author must guess, all of which
produce different frozen tests:

1. **What triggers the refusal.** Measured, `graphed.numpy.io.to_parquet(array: Any, destination, *,
   steps_per_file, compute, executor, prefix, column)` has **no `select=` parameter**
   (`graphed-latest/python/graphed/numpy/io.py:182-191`). So "a varied write" is either (a) a
   `Varied` first positional, or (b) a `select=` keyword the implementer must *add in order to
   refuse it*. Under (a) with no explicit guard the program dies as §2.2's reserved-name
   `AttributeError` on `.session`; under (b) with no added parameter it dies as `TypeError:
   unexpected keyword argument`. Neither is "a clear error naming the awkward backend".
2. **Which entry point.** Measured against `graphed-latest`'s own venv:
   `hasattr(graphed.numpy, "to_parquet")` is **False** — the function is only reachable as
   `graphed.numpy.io.to_parquet`. The plan notes it is absent from `graphed.numpy.__all__` (§2.3d
   r26, correct) but never says the anchor must import the submodule.
3. **The spelling.** Every other new m51 surface in this plan carries an explicit "exact spelling
   pinned at m51 freeze" clause (`select=`, `read_varied`, the manifest keys, `graphed.selection`);
   this one carries none.

**Evidence.** Plan §6.4f's numpy sentence, §6.4a's parenthetical, §10/m51's r26 numpy bullet, §2.3d
r26's `graphed.numpy.to_parquet` note. Measured this session in `graphed-latest`'s `.venv`:
`hasattr(graphed.numpy, 'to_parquet')` → `False`; `graphed.numpy.io.to_parquet` exists with
`array: Any` and no `select` parameter (`python/graphed/numpy/io.py:182-191`); the 1-D cap is inside
`_WritePart.__call__` at `:163-165`.

**Suggested fix.** One sentence in §6.4f: *"the numpy-idiom `to_parquet` (reachable as
`graphed.numpy.io.to_parquet`; not a package attribute — measured) gains the same `select=` keyword
and refuses BOTH a `Varied` record and a non-`None` `select=` with a `graphed` error naming the
awkward backend; exact spelling pinned at m51 freeze."* Mirror the trigger pair in §10/m51's numpy
bullet so the anchor freezes both arms.

---

### 5. LOW — `graphed.awkward.project_buffers` is classified as returning `{label: Projection}`; it returns `BufferProjection`

**Section:** §2.3d (r26 awkward-idiom clause) × §10/m48's idiom-enumeration bullet.

**Detail.** §2.3d r26: "*Binding: both **expand**, per-label results, exactly as their numpy twin
above*" (the numpy twin being `{label: Projection}`), and §10/m48 spells it out:
"`project`/`project_buffers` **expand**, returning `{label: Projection}`". Measured,
`project_buffers(array, *, on_fail="raise") -> BufferProjection`
(`graphed-latest/python/graphed/awkward/projection.py:119`), and `BufferProjection` is a distinct
frozen dataclass whose field is `read_buffers: Mapping[str, Mapping[str, BufferNeed]]`
(`graphed-latest/python/graphed/projection.py:60-72`), not `Projection`'s
`read_columns: Mapping[str, frozenset[str]]` (`:34-44`). A test-author freezing the m48 bullet's
literal value type reds a correct implementation.

**Suggested fix.** "…`project` expands to `{label: Projection}` and `project_buffers` to
`{label: BufferProjection}` — each verb's own return type, per label."

---

### 6. LOW — §2.3d r20's stated ground for classifying the m49 verbs is falsified by r26's operand change

**Section:** §2.3d (r20 clause) × §3.4/§5.3 (r26).

**Detail.** §2.3d r20: "*The m49 verbs this plan itself adds enter the table *expanding* when they
land … so any annotation mentioning `Array` makes the m48 frozen gate discover them one milestone
after the freeze.*" After r26 both verbs take `Sequence[Varied]` (and §3.4 explicitly drops
`source_nid`), so neither annotation mentions `Array` and the m48 discovery filter never reaches
them. Nothing reds — the floor is a containment floor — but the clause's justification is now false,
and a reviewer checking §2.3d's exhaustiveness claim against the m49 surface gets a wrong prediction.

**Evidence.** Plan §2.3d r20 clause; §3.4/§5.3 r26 operand clauses; measured, the annotation-wide
filter over `graphed.__all__` in `graphed-latest`'s venv yields exactly
`['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`
— it keys on the literal string `Array` in a parameter annotation.

**Suggested fix.** Reword to: *"…their operands are labelled containers, so the annotation-wide
filter does NOT discover them; they are classified here for the table's completeness, and the m48
gate's containment floor is unaffected."* (If the operand becomes the labelled mapping per finding 2,
say so there instead.)

---

### 7. LOW — §6.4 never binds the row length at which the stored per-label masks live, nor whether the level-≥1 structural check runs before or after the level-0 OR

**Section:** §6.4a × §6.4b × §6.4c × §6.4d.

**Detail.** §6.4a binds that the writer "*applies the **level-0 OR** to the stored ROWS — that IS the
superset — and applies **no other supplied mask** to the stored buffers … and it stores **one packed
per-label validity mask per supplied ENTRY***". Two operands are left undefined:

1. The per-label masks were recorded over the **full** (pre-superset) row space, while the stored
   buffers live on the **superset** rows. §6.4c requires the reader to reproduce each universe's row
   set bit-for-bit by applying those masks to the stored data — which is only well-typed if the
   stored masks were themselves restricted to the superset rows. Nothing says so.
2. §6.4a's level-≥1 structural predicate is "*each per-label member of the mask must carry that NAMED
   FIELD's own offsets at that depth*", raised per partition from `_WritePart` "**BEFORE any buffer
   is stored**" — i.e. presumably against the *pre-OR* record — while the mask that is eventually
   *stored* must align with the *post-OR* buffers. The two operands differ and the section uses one
   phrase for both.

This is self-consistent for any single implementation (m51's round-trip anchor pairs the writer with
its own reader, so it cannot discriminate), which is precisely why the choice should be written down
rather than discovered: it is the on-disk contract §6.4e's manifest describes to third-party readers.

**Evidence.** Plan §6.4a (storage sentence, levels-≥1 predicate, "Where the checks RUN"), §6.4b's
"on superset rows", §6.4c's reconstruction contract, §6.4e's "readers resolve labels through the
manifest". Measured site: `_WritePart.__call__` evaluates and writes per partition,
`graphed-latest/python/graphed/awkward/io.py:111-127`.

**Suggested fix.** One clause in §6.4a: *"every stored per-label mask — level 0 and every level
k ≥ 1 — is stored on the SUPERSET rows (level-0-OR-restricted), so a reader applies it directly to
the stored buffers; the level-≥1 structural predicate runs against the record's offsets as evaluated,
before the OR restriction, and the restriction is applied to mask and buffers alike."*

---

### 8. LOW — the m48 `context_of` fixture note's stated ground is stale under §2.1's r26 rule

**Section:** §10/m48's §2.3d-table bullet (r21 fixture pin) × §2.1 (r26).

**Detail.** The m48 bullet pins the `context_of`-on-a-`Varied` discriminator to a `vary` IDENTITY
link and justifies it: "*the mask-derived spelling builds a container whose members sit in DIFFERENT
row spaces, and freezing it read-only would pin such a container as CONSTRUCTIBLE for three
milestones — foreclosing any §2.1 construction check*". §2.1's r26 clause has since **decided** that
case: an ancestor-handled member is *re-indexed*, not refused, so the program is legal and its
members do **not** sit in different row spaces. The fixture pin is still the right choice (it keeps
the row space fixed and is closer to what §6.4a(2a) consumes), but the rationale now argues from a
premise the plan itself has reversed, and a reviewer checking "targets exactly as specified" gets two
readings of whether `graphed.vary(events.Jet, "jes", up=sel.Jet, …)` is constructible.

**Evidence.** Plan §10/m48's r21 fixture-pin paragraph; §2.1's r26 clause, whose own worked example
is that exact program.

**Suggested fix.** Replace the stale half with: *"§2.1 r26 now makes the mask-derived spelling legal
(the ancestor member is re-indexed), so it discriminates nothing extra; the identity link is chosen
because it keeps the row space fixed and matches what §6.4a(2a)'s predicate consumes."*

---

### 9. LOW — §2.3d's *accepting* disposition for `to_parquet` covers `select=` only, while the canonical m51 program passes a `Varied` as the RECORD

**Section:** §2.3d (m51 table entry) × §6.4b × §10/m51's table-entry anchor.

**Detail.** §2.3d: "*`to_parquet` takes `select=` per §6.4a*", and m51's anchor freezes "*a `Varied`
`select=` is consumed internally and no per-label result is returned to the caller*". But §6.4b is
written over a record whose **fields are `Varied` structurally at record time**, and §6.4's own
canonical skim is `to_parquet(events.Jet, select=…)` where `events.Jet` is a `Varied` after a
shift-form `vary` (§2.6b). So the first positional is a `Varied` in the headline program, and the
*accepting* disposition — the thing m51 freezes — names only the keyword.

**Evidence.** Plan §2.3d's `to_parquet` clauses, §6.4b's "for every stored field that IS `Varied` —
structurally, at record time", §6.4's canonical `to_parquet(events.Jet, select=…)` spelling, §2.6b's
"thereafter `events.<Collection>` is a `Varied`", §10/m51's `§2.3d table entry` bullet. Measured:
today's signature is `to_parquet(array: Any, destination, *, steps_per_file, compute, executor,
prefix, column, behavior)` (`graphed-latest/python/graphed/awkward/io.py:206-216`) — it reads the
array's `Session`, so an unhandled `Varied` first positional hits §2.2's reserved-name
`AttributeError`.

**Suggested fix.** Extend both the §2.3d sentence and the m51 anchor to "*a `Varied` RECORD and/or a
`Varied` `select=` are consumed internally; no per-label result is returned*".

---

### 10. LOW — §2.6c's "its collections are `Varied` per §2.6b" reads against §2.2 term (b)'s explicit exclusion at the definition site

**Section:** §2.6c × §2.2 (`graphed.labels(ctx)` term (b), r21 scoping).

**Detail.** §2.2 scopes term (b) to "*the labels of any `Varied` collections the context CARRIES — the
collections a shift-form `vary` replaced, inherited ones included, **NOT** the implicitly-varied reads
§2.6c produces through a `Varied`-mask-derived context*". §2.6c, describing exactly such a context,
says "*Binding: its collections are `Varied` **per §2.6b***" — and §2.6b is the shift-form
registration clause, i.e. the sentence that defines what "carries" means. Read at its own site,
§2.6c makes those collections carried, which §2.2 denies. The tension is resolved only inside §2.2's
r21 parenthetical, three sections away, and the r21 argument ("(b) would subsume (c) everywhere and
(c) would be dead text") depends on the reader finding it.

**Evidence.** Plan §2.6c's "Varied contexts" paragraph; §2.2's term-(b) clause and its r21 scoping
parenthetical.

**Suggested fix.** One cross-reference at §2.6c: *"its collections read as `Varied` (§2.4-aligned per
label) — an implicit property of the derivation, NOT a shift-form registration, so §2.2's
`graphed.labels` term (b) does not count them; the mask's own labels enter through term (c)."*

---

## Areas probed and found CLEAN

Recorded so a later round does not re-spend the effort:

- **§2.4 label-aligned union × §2.6c per-label re-indexing.** Worked through the mixed case (a value
  read through a `Varied`-mask-derived `sel` filled against an ambient weight carrying *both* the
  mask's shift labels and unrelated weight labels): for a weight-only label `L`, §2.4's fallback
  gives the mask its nominal member, so the ambient member for `L` is re-indexed by *nominal's* mask
  and matches the value's nominal member row-for-row. Coherent; no length hazard.
- **§2.1's two-level `factor[L]` rule (r24) against the corpus.** Re-measured at
  `graphed-corpus-latest@49650e4`: `jets = _apply_jes(events.Jet, variation)`,
  `good = jets[jets.pt > 25]`, `sel_jets = good[sel]`, `weight = _btag_weight(sel_jets, variation)`,
  with `_btag_weight` returning the CENTRAL per-jet SF product over `axis=1` unless the variation is
  `btag_up`/`btag_down` (`src/graphed_corpus/analyses/systematics.py:25-36,60-79`). The two-level
  resolution and m48's r25/r26 stacking-anchor assertion match the fixture exactly.
- **§6.2 axis mode × §6.1b/§6.1c arithmetic.** `1 + |S|` fill nodes gathering into ONE `(output,
  None)` slot is consistent with `_GroupReduce`'s per-slot sum and `_add_groups`' key-wise `+`
  (`graphed-histogram-latest/src/graphed_histogram/boost.py:100-122`, read this session): all
  gathered nodes share one spec (forced by §6.2(i)'s cross-fill agreement), so the sum is well-typed,
  and the per-fill variation payload entering `content_hash((spec, variation_payload))` is what keeps
  the evaluators distinct. §1.2's r22 two-channel carve-out now covers both label channels.
- **§1.1 e-canonicalization edge cases.** Exercised the rendered-length arithmetic by hand: `"0.5"` →
  `5em1` (4 chars = `len(mantissa)+2+len(exponent)`), `"1.2345"` → `12345em4` (8), the r19
  normalization boundary pair (`"1.5e31"` → 32 digits ACCEPTED / `"1.5e32"` → 33 REJECTED), r22's
  cause-split (`"-1.5e31"`: legal magnitude, 33 rendered chars → length message), negative zero → `0`.
  Also checked the *negative*-exponent analogue of the `"1e1000000000"` hazard: `"1e-1000000000"`
  renders as the 13-character `1em1000000000`, so the huge-string hazard is genuinely one-sided, as
  §1.1 assumes. Cross-notation: `"m2"`/`"2p0"`/`"05"`/`"em1"` all resolve consistently under the
  stated grammars.
- **§9.2's r26 manifest label channel.** Verified the measured basis (`analysis.outputs` is the
  singular `{"value": id, "weight": id|None}` record at
  `graphed-latest/python/graphed/preserve/bundle.py:184-193`) and that the additive, label-sorted
  extension plus a version bump is safe: `canonical_bytes` is `json.dumps(..., sort_keys=True)`
  (`preserve/manifest.py:20-22`), there is no reader-side `FORMAT_VERSION` equality check anywhere in
  `python/graphed/preserve/`, and no frozen m9/m25 test pins a literal fingerprint or version — all
  are relative comparisons (`tests/frozen/preserve/m9/test_fingerprint.py`, `m25/…:81`). Keeping the
  unvaried shape at version 1 preserves them.
- **§2.2's r24 per-idiom `Varied`.** Re-measured against `graphed-latest@ff7c607`: `dir(Array)` public
  = `['filter','map','node_id','reduce','repartition','session']` (6), `dir(NumpyArray)` = 32, the 26
  extras exactly as the plan lists, and the properties on `NumpyArray` are
  `['T','dtype','ndim','node_id','session','shape']`. Also confirmed the seam the design mirrors is
  real and numpy-only: `array_type` appears solely on `NumpyBackend`
  (`python/graphed/numpy/__init__.py:345`), consumed at `session.py:36-39`, so the awkward idiom
  inherits the neutral base and the design needs no third container.
- **§2.3d's discovery counts.** Ran the annotation-wide filter in `graphed-latest`'s venv: `graphed`
  → 8 verbs (`aggregate_plan, apply, join, join_plan, pack_key, read_columns, repartition,
  shuffle_plan`), `graphed.numpy.__all__` (22 names) → exactly the 6 named, `graphed.awkward.__all__`
  (13 names) → exactly `project`/`project_buffers`. The r26 "floor over the UNION, never per
  enumeration" scoping is therefore necessary and correct.
- **§5.4 boundary refusal × §6.4 write plans.** No conflict: a variation cone crossing an
  Exchange/Join is caught by §2.3d's operand refusals on `join`/`repartition`/`pack_key`/
  `shuffle_plan`/`join_plan`, and the write path builds a plain `Plan` via `write_plan`, which has no
  boundary builder to miscompile.
- **§7.3 checkpoint invalidation × m51 writes.** Consistent: the write closure is the `process` of a
  plain-callable `Plan` (`python/graphed/write.py:32-43`) while `run_resumable` requires a
  `DurablePlan` (`python/graphed/checkpoint/runner.py:77-91`), so §6.4f's widened unpack churns no
  shipped journal, exactly as §7.3 r17 and m51's docs anchor say.
- **§6.4a(2a) handle-equality against all six m51 controls**, including r23's `vary`-link admission
  and r20's fifth positive control — each decides as the plan states under §2.3e's ORIGINATION rule
  and §2.6b's r23 canonicalization.
- **Package boundaries.** No binding requirement here violates §A.4: the neutral `broadcast_like` /
  `unify_contexts` / `reindex_to` / `context_of` seams live in `graphed` proper with idiom
  dispatch; §6.4's reader/writer are awkward-idiom; §6.2(3) forbids `boost_histogram` inside
  `graphed` (and marks the rule knowingly unanchored); §6.4e forbids importing `awkward._connect`;
  the IR/core gains only a read-only accessor (§3.1 as re-worded in r13). Nothing pushes awkward or
  boost-histogram behind a neutral namespace.
- **Milestone-boundary consistency.** Cross-checked every "except …" annotation on the m48/m49/m50/m51
  target lines against the sections they cite (§2.5's diagnostic → m49; §3.4 → m49; §6.1b's arity →
  m49; §6.1c's axis slot → m50; §7.2 → m48 with §7.1/§7.3/§7.4 at m49; §8.2(i)'s field declaration →
  m48, accessor/keying/population → m49; §9.1's per-verb milestones; `to_parquet`'s table entry →
  m51). They agree in both directions after r23–r26's sweeps; I found no residual two-answer case
  beyond finding 8's stale rationale.

---

## Verdict

**DIRTY** — 1 HIGH, 3 MID, 6 LOW; no BLOCKER.

The specification is in far better shape than its size suggests: the hard cross-section interactions
this lens is meant to break (label-aligned union vs per-label row sets, ambient-weight re-indexing,
axis-mode slot arithmetic, the write-path predicate lattice, the e-form cap arithmetic) all hold up
under adversarial reading, and the milestone boundaries are internally consistent. The defects are
concentrated exactly where the brief predicted — in the r26 deltas, which have had no review round
yet. Finding 1 is the one that would actually derail m49: as written, the newly named producer cannot
produce the content the same section binds, and the new m49 anchor freezes the half it cannot reach.
Findings 2–4 are single-sentence repairs that each close a "the implementer must guess the semantics"
gap on a surface a frozen anchor already depends on. None of the ten touches an owner-locked
decision; all are repairable inside the existing structure without moving a milestone.
