# Plan review — `systematics-vary-plan.md` r9 — DESIGN SOUNDNESS lens (round 1)

- **Lens:** design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections; unhandled interactions; under-specified Implementation Targets; package-boundary
  / factorization violations; milestone-boundary consistency.
- **Plan revision reviewed:** r9 (2026-07-30), full document (Part I, PART II §§1–12, Anchors
  appendix, revision history).
- **Date:** 2026-07-30.
- **Verification roots used** (all code facts come from these, never the workdir submodules):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607`)
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`)
  - runtime probes in a scratch venv (`python 3.12.10`, `graphed 0.0.1` from the root above,
    `boost_histogram 1.7.2`, `awkward 2.12.0`, `pyarrow 25.0.0`)
  - `/Users/lgray/vibe-coding/graphed-workdir/systematics-vary-codebase-analysis.md` (for the
    provenance of the §3.3 pinned integers)
- **Owner-locked decisions** (naming, functional surface, e-form canonical, event-context
  attachment, record-time expansion, m48–m51 scope incl. §6.4, JER-SF non-monotone contract, the
  Phase-2 pull-in) are taken as given. Nothing below argues for a different choice; every finding
  is about how the plan *specifies* a locked choice.

---

## BLOCKER

### B1. §6.1d names a context-inference mechanism (`provenance`) that measurably cannot carry a context, and the propagation surface it actually needs is unbound

**Section:** §6.1d (plan lines 565–571), with §2.6b/c (lines 403–413) and the m48 anchors
(lines 754–759).

**Detail.** §6.1d binds: "`fill` walks its input Arrays' **provenance** to their event context and
auto-applies that context's ambient weight", and "inputs whose contexts sit on one ancestry chain
unify to the most-derived context; contexts on **divergent branches are a hard error** naming both".
Both halves are unimplementable as specified:

1. **`provenance` is source-location only.** `Provenance` is a frozen dataclass of
   `(filename, lineno, function, source)`; `capture()` returns the first non-`graphed` stack frame
   (`/private/tmp/claude-501/graphed-latest/python/graphed/provenance.py:26-33, 66-79`). There is no
   object-lineage channel from an `Array` to anything — `array.py:1-7`: "An `Array` is a typed handle
   to one interned node … holds no backend data — only a session + node id."

2. **Interning erases the distinction the divergence rule depends on.** Two contexts derived from
   the same root that differ only in *registered weights* (e.g. `c1 = vary(events,"pu",…)`,
   `c2 = vary(events,"pdf",…)`) expose collections whose reads record identical `NodeKey`s and
   therefore the **same node id**. Measured:

   ```
   $ pv/bin/python -c "... p1 = a + 0.0; p2 = a + 0.0 ..."
   sibling-context reads share a node id: True   distinct py objects: True
   ```

   So a node-id-keyed context map cannot distinguish `c1` from `c2`, and the "divergent branches →
   hard error naming both" anchor (m48, line 760) cannot fire.

3. **What is actually required is unbound.** The only viable channel is a *Python-object-level* tag
   on the returned `Array` wrapper (node ids are shared, Python objects are not — the probe shows
   `p1 is not p2`). But the plan's own binding sketch fills from
   `gak.flatten(sel.Jet.pt)` (line 434) — several ops downstream of the context. So **every**
   frontend op (`Array.__getitem__`, every dunder, `record_op`) **and every gak function** would have
   to propagate the context tag. §2.3's four bound dispatch points cover `Varied` propagation only
   (lines 341–369); context propagation is named nowhere in PART II, has no exhaustiveness gate,
   and is not in any milestone's targets. m48 freezes five anchors on the resulting behavior
   (lines 754–760) — a test-author would freeze tests against a mechanism that does not exist.

**Evidence.** `provenance.py:26-33,66-79`; `array.py:1-7`; interning probe above; plan lines
565–571, 434, 754–760.

**Suggested fix.** Replace "walks its input Arrays' provenance" with the real mechanism and bind its
surface: (a) state that the context handle is a **Python-object attribute on the `Array`/`Varied`
wrapper, explicitly NOT part of node identity** (so §1.2 stays intact and interning is unaffected);
(b) add a fifth §2.3 dispatch point — "context-tag propagation" — with the same
frozen exhaustiveness gate as the gak classification, defining the merge rule for multi-input ops
(most-derived on one chain, error on divergence) *at the op*, not at the fill; (c) state what
happens when a tagged Array is passed through an op that drops the tag (refuse, or fall back to
unweighted with a diagnostic — silence is the §2.5 failure mode).

---

## HIGH

### H2. §1.2's content dedup breaks §7.2's positional `(output, label) → position` mapping — measured

**Section:** §1.2 (lines 288–296), §7.2 (lines 673–675), §6.1a/§6.1c (lines 549–560), §5.2a
(lines 509–513), m51 anchor (lines 821–824).

**Detail.** §1.2 *mandates* that structurally identical variations intern to the same nodes, and
§5.2a explicitly puts the case in scope ("Labels structurally identical to a prior label dedup to
Δ = 0 by §1.2 — that case is witnessed separately as the dedup feature"); m51 freezes "a label
structurally equal to nominal (all-zero delta)" (line 822). §7.2 then binds "The frontend owns
`(output, label) → position`", and §6.1c routes varied histograms through `_GroupReduce`, which
consumes the evaluated output list **positionally**
(`graphed-histogram/src/graphed_histogram/boost.py:102-117`: `for label, k, spec in self.layout:
… for j in range(i, i+k): total = total + fills[j]`).

The positional contract does not survive dedup. `GraphStore::mark_output` de-duplicates
(`graphed-latest/src/store.rs:152-153`: `if !g.outputs.contains(&id) { g.outputs.push(id) }`), so a
compile whose output list contains the same node twice returns **one** value, not two. Measured:

```
interned same id: 1 1 True
reduced outputs: [1]
n outputs returned: 1
```

(`compile_ir(s, b, c)` with `b`/`c` structurally identical → `evaluate_ir` returns a 1-element
list.) With a `_GroupReduce`-style layout expecting `1 + |S| + |W|` entries, the reduce walks off
the end of `fills` — an `IndexError` at worst, a mis-sliced label→histogram assignment at best.

**Evidence.** `store.rs:152-153`; `boost.py:102-117`; `python/graphed/execute.py` `evaluate_ir`
(`return [vals[o] for o in store.outputs()]`); probe output above.

**Suggested fix.** Re-bind §7.2 as `(output, label) → node id`, with the frontend holding a
**many-labels-to-one-position** map built after compile (`node_id → position` from the compiled
output list, then `label → node_id`). Say explicitly that several labels may resolve to one
position and the unpacker replicates the value. Add the dedup case to a frozen anchor in m48/m49
(two labels whose members are the same expression → both keys present, one evaluated fill).

### H3. §6.2's "non-growth, pre-declared" variation axis silently swallows undeclared labels; the plan never binds who declares the bins or what happens on mismatch

**Section:** §6.2 (lines 577–597), against §2.5 (lines 381–387) and §6.1d (lines 565–571).

**Detail.** §6.2 requires a "non-growth, pre-declared, sorted StrCategory `"variation"` axis" and
justifies non-growth by combine-safety. But the fill's label set is *inferred* at fill time —
§6.1d makes it the union of value-borne, ambient-weight and explicit-factor labels, which the user
never enumerates. The plan does not say who declares the bins (user at `Histogram(...)`
construction? the frontend from the inferred set?), nor what happens when the inferred set and the
declared set differ. That matters because boost-histogram's non-growth `StrCategory` **does not
raise** on an undeclared string — it has an overflow bin. Measured (bh 1.7.2):

```
h = bh.Histogram(bh.axis.StrCategory(['nominal','jes_up','jes_down']), bh.axis.Regular(4,0,4))
h.fill(['nominal','bogus','jes_up'], [1.0,1.0,2.0])
sum 2.0   sum flow 3.0
axis traits Traits(underflow=False, overflow=True, …, growth=False, …)
```

An undeclared label lands in flow and vanishes from `h.sum()` / `h.values()` — precisely the
"hand-maintained name lists where a typo silently drops a systematic" failure mode Part I §2 cites
and §2.5 promises to convert into an error. Also unaddressed: §6.2 says the axis is "sorted"
*and* "pre-declared" — if the user declares an unsorted bin order, which wins?

**Evidence.** bh 1.7.2 probe above; plan lines 578–581, 590–597; §2.5 lines 381–387.

**Suggested fix.** Bind (a) the declaration source — recommend the frontend building the
`StrCategory` from the inferred label set at plan time (identical per partition ⇒ combine-safe,
deterministic under the §2.4 order fix in M12); (b) if a user-declared axis is supported, an
**exact-set** check at fill: any label not in the declared bins is a hard error naming it, and any
declared bin no label reaches is a diagnostic (the §2.5 mkShapesRDF case); (c) state that the
frontend sorts and that a user-supplied order is normalized (or refused).

### H4. §6.1d's "ambient weight broadcast to the fill's object structure" is contradicted by the plan's own fill sketch

**Section:** §6.1d (lines 572–574) and the §2.6 sketch (line 434); m48 anchor (lines 754–756).

**Detail.** §6.1d binds: "The per-event ambient weight is **broadcast to the fill's object
structure** (a per-jet fill gets the event weight replicated across each event's jets before the
existing jagged flatten)". The sketch's fill is `h.fill(pt=gak.flatten(sel.Jet.pt))` — i.e. the
value reaching `fill` is **already flat**. The recorded graph node handed to `Histogram.fill` is a
flat array; nothing in the fill's inputs carries the jagged structure to broadcast against. The
evaluator flattens each value *independently*
(`graphed-histogram/src/graphed_histogram/boost.py:39-47` `_flat` → `ak.flatten(values, axis=None)`;
`:60-71` applies `_flat` to axes and to the weight separately), so a per-event weight paired with a
per-jet axis simply yields mismatched lengths at fill time.

So the requirement is satisfiable only if per-object fills are passed **unflattened**, or if the
frontend walks the fill input's graph back to the flatten node and re-records the broadcast against
its input — an unbound and fragile transformation the plan does not mention. As written the m48
anchor ("ambient fill on a per-object quantity … weight broadcast frozen against a manual-broadcast
reference") is authored against a contradiction.

**Evidence.** `boost.py:39-47, 60-71`; plan lines 434, 572–574, 754–756.

**Suggested fix.** Bind one of: (a) per-object ambient fills take the **unflattened** Array
(`h.fill(pt=sel.Jet.pt)`), the frontend records `broadcast_arrays(ambient, value)` and relies on the
evaluator's existing `_flat`; fix the sketch at line 434 accordingly; or (b) explicitly bind the
graph-walk (find the outermost flatten on each value input, broadcast against its argument) and
bind what happens when no such node exists (refuse, naming the fill). Either way the sketch and the
requirement must agree, because the sketch is declared "binding shapes".

### H5. §6.4b requires stored fields "evaluated in the nominal universe on superset rows", but no mechanism exists to re-target an already-recorded expression at the OR mask

**Section:** §6.4a (lines 609–613), §6.4b (lines 614–628), against §3.1 (lines 443–447).

**Detail.** §6.4a says the OR of per-label selections "is recorded as ordinary graph ops over the
per-label masks (`getitem`/`gak.mask` — no mask algebra exists in the IR and none is added)" and
"stored columns are evaluated on the **superset** rows". §6.4b then says the written record carries
"the user's fields evaluated in the **nominal** universe (on superset rows)".

The user's write target is an expression that *already embeds a selection* — e.g.
`to_parquet(sel.Jet)` where `sel = events[nominal_mask]`. Producing "the same fields on superset
rows" requires substituting the OR mask for the selection node **inside** an already-interned,
immutable expression. Recording the OR mask (§6.4a) is the easy half and is bound; the substitution
is the hard half and is bound nowhere. It cannot be a node rewrite (§3.1 forbids new IR machinery
and nodes are immutable/interned); it would have to be a second record-time expansion pass over the
user's write expression, with a rule for *which* node in the cone is "the selection".

Consequence: an implementer must invent the decomposition semantics, and m51's headline anchors
(superset-row anchor, bit-exact round-trip, lines 817–824) sit directly on top of it.

**Evidence.** Plan lines 609–613, 617–619, 443–447; `python/graphed/awkward/io.py:111-127`
(`_WritePart.__call__` evaluates one compiled output and writes it — no selection introspection).

**Suggested fix.** Bind the user-facing shape instead of the rewrite: require the varied write to be
expressed as `graphed.to_parquet(record, select=varied_mask)` (or equivalent) so the writer owns
the mask and can build both the OR and the per-label masks itself, with the record expression
recorded **pre-selection** by construction. If the implicit form is kept, bind the decomposition
rule explicitly (which node is the selection, what happens when the cone contains several, what
happens when the varied selection is not the outermost op) and add a refusal for the cases the rule
cannot decide.

### H6. §2.6c leaves derived contexts under-specified in the two ways the sketch actually exercises: ambient-weight re-indexing, and a context derived by a `Varied` mask

**Section:** §2.6c (lines 406–413), §6.1d (lines 570–571), the sketch (lines 429–434).

**Detail.** §2.6c says only "Derived contexts (`events[mask]`) inherit the ambient registry". Two
load-bearing consequences are unstated:

1. **Re-indexing.** The ambient weight registered on `events` is a per-event Array of the *parent's*
   row count. After `sel = events[gak.num(jets) >= 4]`, a fill from `sel` (sketch line 434) needs a
   weight of the *derived* row count. So "inherit" must mean "inherit, each member re-indexed by the
   derivation mask" — a real requirement with a real cost, never stated. Without it every §6.1d
   ambient fill from a derived context is length-mismatched. The same gap makes §6.1d's
   "inputs on one ancestry chain unify to the **most-derived** context" ill-defined when an input was
   read from an *ancestor* (its rows are the ancestor's).

2. **`Varied`-mask derivation.** In the sketch, `jets` is JES-varied, so `gak.num(jets) >= 4` is a
   `Varied` mask and `sel = events[that]` is a context whose **row set differs per label**. §2.6b
   only describes contexts whose *collections* are `Varied`; nothing in §2.6 defines a context that
   is itself label-plural, yet it is the central idiom of the binding sketch and the substrate for
   the very next line (`graphed.vary(sel, "btag", …, is_weight=True, …)`). Everything downstream —
   ambient-weight members per label, §2.4 alignment at the fill, §6.4a's OR-of-selections — depends
   on semantics the plan never writes down.

**Evidence.** Plan lines 406–413, 429–434, 570–571.

**Suggested fix.** Add to §2.6c: (a) "a derived context re-indexes every ambient-weight member by the
derivation mask, label-aligned per §2.4"; (b) an explicit paragraph defining a **varied context**
(per-label row sets), stating that `graphed.labels(ctx)` reports them, that `vary(...,
is_weight=True)` on it stacks per §2.1 (new-label members take the provided value's central
universe), and that fills from it are label-aligned per §2.4. Add an m48 anchor for the derived-
context weight length and for `graphed.labels(sel)` on a `Varied`-mask-derived context.

---

## MID

### M7. §6.4d's structure rule assumes variations preserve multiplicity; §2.1's form check does not, and §6.4c's XOR delta needs identical buffer lengths

**Section:** §6.4c (lines 629–639), §6.4d (lines 640–644), §2.1 (lines 328–331).

**Detail.** §6.4c mandates bit-exact reconstruction via "same-dtype XOR bit-delta vs nominal", which
requires per-label buffers of **identical length**. §6.4d justifies that by storing values "at the
widest common structure (pre-object-cut values on the event-row superset)". That holds for scale and
smear shifts (the corpus `ak.with_field` fixture), but §2.1 permits varying an arbitrary record
Array and only checks that members "have compatible forms (backend `op_form`-checked)". Awkward form
compatibility is a *type* check: `var * float64` matches `var * float64` regardless of per-event
multiplicity. A variation that legitimately changes multiplicity (a shift-dependent cleaning /
overlap-removal / matched collection) therefore passes §2.1 and then has no representable delta, and
§6.4 specifies no refusal.

**Evidence.** Plan lines 328–331, 631–632, 640–644.

**Suggested fix.** Add to §6.4d a bound refusal: "a stored varied field whose per-label offsets
differ from nominal's is refused with a clear error naming the label and the field; the supported
model is same-multiplicity variation plus per-label validity masks." Add it as an m51 frozen anchor
(negative test) so the boundary is pinned rather than discovered.

### M8. §6.4e's writer swap contradicts §6.4g's byte-identity requirement — measured

**Section:** §6.4e (lines 645–653), §6.4g (lines 664–666).

**Detail.** §6.4e: "the `ak.to_parquet` call is swapped for a metadata-capable arrow write".
§6.4g: "an unvaried write is **byte-identical** to today's output … and carries no manifest". These
conflict if the swap is unconditional. Measured (awkward 2.12.0 / pyarrow 25.0.0):

```
ak.to_parquet  e0706c0ddb1f0dc6
pq.write_table d24f3bc55fbe46bd
kv(ak.to_parquet): {awkward_array_metadata, ARROW:schema, ak:parameters}
kv(pq.write_table): [ARROW:schema, ak:parameters]     # awkward_array_metadata absent
```

and `ak.to_parquet` (2.12.0) has no key-value-metadata parameter — its signature is
`(array, destination, list_to32, …, parquet_extra_options, storage_options)` — so the swap really is
needed to carry a manifest.

**Evidence.** Probe above; plan lines 646–648, 665–666;
`python/graphed/awkward/io.py:111-127` (`ak.to_parquet(payload, path)`).

**Suggested fix.** Bind the branch explicitly: unvaried writes keep `ak.to_parquet` untouched
(preserving §6.4g's golden); varied writes take the `ak.to_arrow_table` + `pq.write_table` path and
must reproduce awkward's own KV entries (`awkward_array_metadata`, `ak:parameters`) alongside the
graphed manifest, so the file stays `ak.from_parquet`-readable. Add a frozen m51 anchor for
`ak.from_parquet` round-tripping the augmented file.

### M9. §3.3's pinned integers are not derivable from the topology §3.3 describes

**Section:** §3.3 (lines 452–460).

**Detail.** §3.3 asks the test-author to freeze "the exact reduced shape for the fixed topology
(`stages == N + 1`, `reduced_nodes == 2N + 2`)" for "shared prefix + N varied suffixes where each
variation is a separately marked output". From that description the reduced shape is
`1 source + 1 prefix stage + N variation stages = N + 2` nodes, not `2N + 2` — each suffix is a
single-use chain and fuses into one stage. The measured basis says why: `cba §optimizer §5`
(`systematics-vary-codebase-analysis.md:283`) — "Reduced form is `2N+2` nodes (`stages = N+1`): one
shared-prefix stage computed once + **per-variation {chain-stage, reduction}**". The second node per
variation is a *reduction* terminating each suffix, and §3.3 never says the suffixes end in a
reduction. A test-author replicating §3.3 literally would build an `N + 2` graph and freeze a
failing assertion.

**Evidence.** Plan lines 452–460; `systematics-vary-codebase-analysis.md:283`;
`graphed-latest/tests/frozen/core/m4/test_systematics.py:11-26` (the pattern being replicated).

**Suggested fix.** Spell the topology in §3.3: "shared prefix of D ops; per variation, a varied
input feeding a D-op chain **terminated by a reduction**, each reduction separately marked" — then
`stages == N + 1`, `reduced_nodes == 2N + 2` follows and is reproducible.

### M10. §4.3's structural predicate is false as literally written

**Section:** §4.3 (lines 489–494), §3.4 (lines 462–467).

**Detail.** §4.3: "the §3.4 impact set of every weight-only label MUST contain no node outside the
fill's weight-input cone". The §3.4 impact set is `reachable(label's outputs) − reachable(nominal
outputs)`; the label's output **is** the sibling fill node, which is not reachable from nominal's
output and is not in the weight-*input* cone (it is downstream of it). So the assertion as written
fails for a correct implementation. The parenthetical alternative — "equivalently: the selection
cone's node ids are identical across weight labels" — is the sound formulation, and the two are not
in fact equivalent.

**Evidence.** Plan lines 462–467, 490–494.

**Suggested fix.** Make the parenthetical the binding form ("the selection cone's node ids are
identical across weight labels"), or restate §4.3 as "impact set ⊆ (weight-input cone ∪ {the
label's own fill node})". Whichever is chosen must be the one the m48 anchor (line 744) quotes.

### M11. §8.2's `node id → label` map is not a function; §3.4 proves it

**Section:** §8.2 (lines 695–704), §3.4 (lines 464–467), §7.4 (lines 686–688).

**Detail.** §8.2 binds "the frontend's **node-id → label map** … the worker sets
`StageError.variation` from the failing node id at construction". §3.4 states the opposite property
in the same document: "a node shared by `jes_up` and `jes_down` but not nominal appears in **both**
impact sets". A node can therefore belong to several labels, and §8.2 gives no rule for that case —
the worker would attribute a failure to one arbitrary label, silently mislabelling the other. The
m49 anchor (line 802) uses a single-label failure and would pass regardless, so the defect would
survive the freeze.

**Evidence.** Plan lines 464–467, 697–701; `python/graphed/debug/errors.py:29-81` (`variation`
would ride `__dict__` and `__eq__`, but `__hash__` is an explicit tuple that must be extended).

**Suggested fix.** Bind the map as `node id → frozenset[label]` and define the rendering: a single
label → that label; several → a deterministic sorted join (or `""` plus the set on a new
`variations` field). Extend the m49 anchor with a shared-node failure asserting the multi-label
rendering.

### M12. §2.4 does not define the label ORDER of the union, which §3.2, §6.1b and the group layout all depend on

**Section:** §2.4 (lines 370–380), §2.2 (lines 332–334), §3.2 (lines 448–451).

**Detail.** §2.2 defines ordering only *within* a container ("nominal first, then insertion order;
inherited labels before new ones under stacking"). §2.4 defines the union's *membership* but not its
*order*. §3.2 then requires "labels in `graphed.labels` order" for deterministic expansion, and
§6.1b counts fill nodes whose compile order fixes the `_GroupReduce` layout
(`boost.py:102-117`). Two containers with disjoint or differently ordered label sets have no defined
merge order, so the byte-identical-compilation anchor (m48, lines 747–749) rests on an unstated rule.

**Evidence.** Plan lines 332–334, 370–380, 448–451; `boost.py:102-117`.

**Suggested fix.** Add one sentence to §2.4: "the union's order is the first operand's order,
followed by labels new to the second operand in its own order (nominal always first)" — and pin it
in the m48 determinism anchor.

### M13. `**tags` collides with `vary`'s own parameter names — the exact hazard class §2.6a declares load-bearing

**Section:** §2.1 signature (line 301), §1.1 tag grammar (lines 251–253), §2.6a (lines 393–398).

**Detail.** The signature is
`graphed.vary(target, name, /, nominal=None, *, is_weight=False, variations=None, **tags)`. In
overload (b) `**tags` holds **tag names**; in overload (c) it holds **tree collection names**. Either
way the names `nominal`, `is_weight` and `variations` are silently consumed by the signature: a tag
`variations` binds to the mapping parameter (likely a confusing type error), and a *collection*
named `is_weight` or `variations` is unreachable via the shift form. §1.1's grammar `[A-Za-z0-9_]+`
admits all three, and §2.6a declares reserving names in an analysis-controlled namespace to be
"load-bearing, not style" — collection names come from the tree, so the shift form re-introduces
exactly that hazard. §1.1 names `variations=` as "the documented route for such tags" but does not
say it is also the escape for tags colliding with the signature; overload (c) never says whether
`variations=` applies at all.

**Evidence.** Plan lines 301, 251–253, 393–398.

**Suggested fix.** State in §2.1 that `nominal`/`is_weight`/`variations` are shadowed by the
signature and MUST be supplied through `variations=` (tags) or a `collections={...}` mapping (shift
form), and bind `variations=`'s meaning in overload (c) (or refuse it there). Add the three shadowed
names to the m48 §1.1 grammar anchor.

### M14. §2.6d's data-context rule silently drops shift variations

**Section:** §2.6d (lines 414–416), against §2.5 (lines 381–387).

**Detail.** §2.6d guards only the weight form ("`is_weight=True` on a data context is a guard
error") and then says data contexts "fill nominal-only". A shift-form `vary` on a data context is
therefore *accepted* and its labels *silently discarded at the fill* — a silent drop of an explicit
user registration, which §2.5 exists to eliminate. (The survey convention the clause cites is "data:
no shifts, no variation axis" — i.e. shifts should be refused, not swallowed.) Separately, what
makes a context a "data context" is never defined (no constructor flag is bound anywhere).

**Evidence.** Plan lines 414–416, 381–387; Part I §2 lines 137–139.

**Suggested fix.** Make §2.6d refuse **both** forms on a data context (guard error naming the
variation), so "fill nominal-only" is a structural consequence rather than a silent drop; and pin
the data flag ("`gnano.events(src, is_data=True)`-shaped; spelling at m48 freeze"). Update the m48
anchor at line 761 to cover the shift-form refusal too.

---

## LOW

### L15. §6.4b's canonicalization citation and probe evidence are stale after r9

**Section:** §6.4b (lines 621–628).

**Detail.** §6.4b still reads "Labels are valid identifiers by construction (**§1.1 r8**
canonicalization — a dotted spelling never reaches a label)" and leads with the p-form probe
fixture `__vary_murf_0p5__Jet_pt` as its evidence, mentioning the r9 canonical
`__vary_murf_5em1__Jet_pt` only as a comparison. r9 made the e-form canonical (lines 244–252,
940–951); the p-form is now a merely-legal identifier tag. The text is not wrong, but a
test-author reading §6.4b first would take `0p5` as the canonical on-disk shape.

**Suggested fix.** Reverse the emphasis: cite "§1.1 (r9) canonicalization", lead with
`__vary_murf_5em1__Jet_pt`, and keep the p-form fixture as the carried-over probe evidence.

### L16. §1.1 leaves negative zero and exponent magnitude unspecified

**Section:** §1.1 (lines 244–260).

**Detail.** The input grammar `-?\d+(\.\d+)?([eE][+-]?\d+)?` accepts `"-0"`, `"-0.0"` and
`"-0e5"`, but the canonical rendering rule ("integer values render as plain digits … `m2` for −2")
does not say whether −0 renders as `0` or `m0` — two different labels, two different StrCategory
bins and column names, from one value. It also places no bound on the exponent: `"1e400"`
canonicalizes under exact decimal arithmetic to a 401-digit tag, hence a 401-character label
embedded in a parquet column name (§6.4b).

**Suggested fix.** One clause: "negative zero canonicalizes to `0`; a canonical tag longer than N
characters is refused" (pick N at freeze — 32 is generous for every real σ-scan / μR-μF family).

### L17. §6.1a's heterogeneous result type is not typeable under the `mypy --strict` gate as stated

**Section:** §6.1a (lines 549–552), §7.2 (lines 673–675), DoD (lines 837–840).

**Detail.** §6.1a binds `{output_name: {label: hist}}` for varied outputs but "a bare `hist` (NOT
`{"nominal": hist}`)" for unvaried ones — a value-dependent union return type
(`dict[str, bh.Histogram | dict[str, bh.Histogram]]`) that every caller must `isinstance`-narrow,
and which `_add_groups`
(`boost.py:120-122`: `{label: a[label] + b[label]}`) must also branch on. The DoD requires
`mypy --strict` on src *and* tests. The backward-compatibility motive is sound; the typing cost is
unacknowledged.

**Suggested fix.** State the declared result type in §6.1a/§7.2 and bind the combine's branch, or
keep the union but add a bound narrowing helper (`graphed.universe(result[name], label)` already
works on both shapes per §2.2 — say so explicitly).

### L18. m48 freezes the gak classification including the "refusing" class, whose behaviour (§5.4) is an m49 target

**Section:** §2.3c (lines 358–364), §10 m48 (line 751) vs §10 m49 (line 795).

**Detail.** §2.3c's classification includes "*refusing* (`gak.join` and boundary verbs, per §5.4)",
and the m48 anchor list freezes "§2.3 … gak-classification exhaustiveness tests". §5.4 (the refusal
semantics, its message, and its positive control) is an m49 target. The m48 test-author must
therefore freeze the existence of a refusal whose contract is specified for the next milestone.

**Suggested fix.** Either move the "refusing" class's behavioural assertion to m49 and have m48
freeze only the *classification table's* exhaustiveness, or move §5.4's refusal (not the plan-builder
positive control) into m48's targets. Say which in §10.

---

## Verdict

**DIRTY.** One BLOCKER, five HIGH, eight MID, four LOW.

The architecture (record-time expansion + interning, no new NodeKey) is sound and well-evidenced,
and the older sections (§1.2/§2.4 stacking + label-aligned union, §3, §4, §5) hold up under this
lens — I found nothing structurally wrong there beyond M9/M10's precision defects. The problems are
concentrated exactly where the review brief predicted: the **new surface**. §6.1d's ambient-fill
inference is specified against a mechanism (`provenance`) that measurably cannot carry a context and
against a fill shape (pre-flattened values) that measurably cannot carry the broadcast; §2.6c does
not define the derived/varied contexts its own binding sketch uses; §6.2's axis mode has an unbound
declaration contract over a container that silently swallows unknown labels; and §6.4/m51's
superset-row rule needs an expression-retargeting mechanism nobody has specified. §1.1's r9 e-form
is in good shape — only negative zero and exponent bounds are open.

The BLOCKER and H4/H6 must be resolved before m48 enters TEST_AUTHORING: as written, five of the
m48 event-context anchors would be frozen against mechanisms that do not exist. H2 must be resolved
before any milestone freezes a multi-label result assertion. H3/H5/M7/M8 gate m50 and m51
respectively and can be fixed in a later revision without blocking m48.
