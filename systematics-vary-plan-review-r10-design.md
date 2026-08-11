# systematics-vary-plan r10 — review round 2, DESIGN SOUNDNESS lens

- **Lens**: design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections, unhandled interactions, under-specified Implementation Targets, package-boundary
  / factorization violations, milestone-boundary consistency. Depth-weighted to the newest surfaces
  (§2.6 functional context, §6.1d, §6.4/m51, §1.1 r9 e-canonicalization) per the review brief.
- **Plan revision reviewed**: r10 (`systematics-vary-plan.md`, read in full — Part I, PART II §§1–12,
  §10 milestones, Anchors appendix, revision history).
- **Date**: 2026-07-30.
- **Verification roots used** (fresh clones at the pinned revisions; the stale workdir submodules were
  NOT used):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607` — confirmed via
    `git log --oneline -1`)
  - `/private/tmp/claude-501/graphed-histogram-latest`
  - `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`)
  - `/private/tmp/claude-501/graphed-exec-check` (graphed-executors)
  - `/private/tmp/claude-501/uproot5-graphed`
- **Method**: every finding below is grounded in a file I read or a command I ran in this session.
  No Python environment with the built Rust extension was available in the roots
  (`import graphed` → `ModuleNotFoundError`), so runtime re-measurement was not attempted; where the
  plan's own probes are the basis (e.g. `compile_ir` dedup counts) I verified the *source-level*
  mechanism instead (`mark_output`'s `if !g.outputs.contains(&id)`, `execute.py:126`) and say so.
- **Owner-locked decisions were not relitigated.** Nothing below asks for a different naming, a
  different canonical float encoding, a different attachment point, a different architecture, or a
  different milestone scope. Every finding is about how the plan *specifies* those decisions.

---

## BLOCKER

### B1 — §6.4d requires object-level cutflow data that no bound API can supply; m51's required positive control is unsatisfiable as written

**Section**: §6.4a / §6.4d / m51 anchors.

**Detail.** §6.4d binds two things at once: (i) varied columns are stored "at the widest common
structure (**pre-object-cut values** on the event-row superset), with per-label validity masks at
every selection level that varies — event-level **AND object-level** (a JES shift moves jets across a
per-jet pt cut, so per-label *inner* masks are part of the cutflow data, not an edge case)"; and
(ii) a **refusal**: "a stored varied field whose per-label offsets differ from nominal's is REFUSED".

The only selection channel the plan binds is §6.4a's *event-level* one:
`graphed.to_parquet(record, select=varied_mask)`, where `select=` is a row mask and the writer
"builds both the OR and the per-label masks". There is no channel for a per-object (jagged) varied
mask, and §6.4a explicitly forecloses deriving one from the record expression — its own argument is
that substituting a mask "INSIDE an already-interned, immutable expression" is "a node rewrite the IR
forbids", plus an "undecidable 'which node in the cone is *the* selection' rule". That argument
applies verbatim, and with more force, to an *inner* cut buried inside `good = jets[jets.pt > 25]`.

So the two reachable user spellings both fail:
- user passes the **post-object-cut** record (`to_parquet(good_jets, select=evt_mask)`): under a JES
  shift the per-label offsets of `good_jets` differ from nominal's by construction — that IS object
  migration — so §6.4d's refusal fires;
- user passes the **pre-object-cut** record (`to_parquet(jets, select=evt_mask)`): offsets match, the
  write succeeds, but the writer never sees the per-jet cut and therefore cannot store the per-label
  inner masks §6.4d requires, and the round-trip cannot reconstruct any universe's *post-selection*
  object set — which §6.4c makes REQUIRED ("reproduce every universe's post-selection values and row
  set bit-for-bit").

m51 then freezes both sides of the hole as *passing* anchors: "Bit-exact round-trip … covering a
shift with **object-level migration** (per-label inner masks, §6.4d)" and, under the structure-refusal
anchor, "with a **positive control** that a same-multiplicity shift with object-level migration still
writes and round-trips". A test-author starting from these anchors must invent the missing API to
write the test at all (guessing semantics), or freeze something that does not exercise object-level
migration (vacuous). Either outcome is a bad freeze.

**Evidence.**
- Plan text: §6.4a (`systematics-vary-plan.md:737-751`), §6.4d (`:781-794`), §6.4c
  (`:770-780`), m51 anchors (`:1098-1103`, `:1113-1115`).
- The write path today evaluates exactly one compiled output and writes it verbatim — there is no
  second mask input and no per-level structure knowledge:
  `/private/tmp/claude-501/graphed-latest/python/graphed/awkward/io.py:111-127`
  (`(out,) = evaluate_ir(...)`; `payload = result if result.fields else ak.Array({self.column: result})`;
  `ak.to_parquet(payload, path)`).
- `to_parquet`'s current signature has no selection channel at all:
  `python/graphed/awkward/io.py:206-216`.

**Suggested fix.** Bind an explicit per-level selection channel alongside `select=` — e.g.
`select=` accepting either one row mask or an ordered per-depth mapping of `Varied` masks
(`{0: event_mask, 1: jet_mask}`), with the rule "the writer applies none of them to the stored
buffers; it stores the widest structure plus one packed per-label validity mask per supplied level".
Then m51's positive control has a spelling. If that is too much for v1, the alternative is equally
acceptable and much smaller: restrict §6.4d to **event-level** cutflow, move object-level validity
masks to §11 (Phase 2) with the rest of the multiplicity story, and delete the object-migration
clause from both m51 anchors.

---

## HIGH

### H1 — §6.2's "the FRONTEND declares the axis **at plan time**" collides with measured record-time spec identity

**Section**: §6.2 (m50).

**Detail.** §6.2 binds: "(i) **the FRONTEND declares the axis** at plan time from the §6.1d inferred
label set, so the spec is identical per partition by construction". But a `Histogram`'s spec is fixed
at construction and is baked into **node identity at `fill()` time**, one milestone earlier:

- `Histogram.__init__` → `self._spec = spec_of(self)`
  (`graphed-histogram-latest/src/graphed_histogram/boost.py:146-150`);
- `fill()` records the spec into the External node's **params** *and* its
  **PayloadDescriptor content hash**, and registers the evaluator under that hash:
  `chash = content_hash(self._spec)`; `params={"spec": self._spec, "n_axes": …}`;
  `self._evaluators[chash] = evaluator` (`boost.py:180-212`);
- `spec_of` is a pure function of the histogram's axes + storage (`_spec.py:115-122`), and
  `zero_of(spec)` rebuilds the empty histogram from it (`_spec.py:129-135`), so the *combine identity*
  and the *fill node identity* are the same string.

Adding a `variation` StrCategory axis at **plan time** therefore changes `spec_of` after the fill
nodes were already recorded with the old spec in their params and content hash: the recorded nodes,
their evaluators, `_GroupReduce`'s per-label `spec`, and `_GroupZero` would disagree. As written the
requirement is not implementable without either re-recording every fill at plan time (an unbound,
large change) or mutating interned node params (which §3.1/§1.2 forbid).

Note the label set is in fact known at **fill time** — the inputs' `Varied` labels are in hand when
`fill()` is called — so the natural binding is "declared at fill time from that fill's §6.1d inferred
label set", with the cross-fill consistency rule stated explicitly (several fills into one axis-mode
histogram must agree on the bin set, or the second fill is a hard error naming the mismatch). What is
missing is a decision, not a mechanism.

**Suggested fix.** Re-bind §6.2(i) to the point at which the spec enters node identity (fill time),
and add the cross-fill agreement rule. If plan-time declaration is genuinely wanted, say explicitly
that axis-mode fills are recorded lazily (staged, not recorded, until `plan()`), and carry that
through §6.1b/§7.2 — but that is a larger design and should be named as such.

### H2 — §6.1a's result-shape contract has no axis-mode case; the bound narrowing helper would silently report one label for an N-label histogram

**Section**: §6.1a vs §6.2 (m48 anchor vs m50 anchor).

**Detail.** §6.1a binds exactly two result shapes and a narrowing contract over them: a varied output
is `{label: hist}`; an unvaried output is a **bare** `hist`; and "`graphed.universe(result[name],
label)` and `graphed.labels(result[name])` work uniformly on BOTH shapes …, **a bare `hist` reading as
the single label `"nominal"`**". §6.2's axis mode produces a **third** shape: one bare histogram that
contains *all* labels along a `variation` axis. Under §6.1a's bound rule, `graphed.labels(h_axis)`
returns `["nominal"]` and `graphed.universe(h_axis, "jes_up")` raises KeyError — a confidently wrong
answer about a histogram that does contain `jes_up`. That is precisely the silent-bookkeeping failure
class §2.5 exists to delete.

m50's anchor ("Variation-axis fill equals sibling-fill results bin-for-bit") presupposes some
extraction operation on the axis-mode result; the plan never says what it is or what
`run(plan).value[name]` is in axis mode.

**Evidence.** Plan §6.1a (`:649-659`), §6.2 (`:692-704`), m50 anchors (`:1068-1077`). Today's
group-plan result is `{name: hist}` built by `_GroupReduce`
(`graphed-histogram-latest/src/graphed_histogram/boost.py:100-122`), so the mixed shape
`{name: hist | {label: hist}}` is real and the third shape has to be placed inside it.

**Suggested fix.** Add an explicit §6.2 clause: an axis-mode output returns a bare `hist` carrying the
`variation` axis, and `graphed.labels`/`graphed.universe` recognise it (labels = the axis' bin set;
`universe` = the `h[{"variation": label}]` slice), so the narrowing helper stays uniform across all
three shapes. Anchor it in m50 next to the equality anchor.

### H3 — §6.1d's "the fill only ever sees an already-unified handle" is false; the fill *is* a combining point, and the m48 divergence anchor has no bound raiser

**Section**: §6.1d / §2.3e (m48 anchor "divergent-lineage fill → hard error").

**Detail.** §2.3e puts the merge/divergence rule "at the op, not at the fill", and §6.1d repeats it:
"contexts on **divergent branches are a hard error** naming both (raised at the combining op per
§2.3e, so the fill only ever sees an already-unified handle)". The parenthetical does not hold. A fill
takes several *independent* inputs that no op ever combined:

```python
h.fill(pt=a_from_ctx1, eta=b_from_ctx2, weight=[w_from_ctx3])
```

`a`, `b` and `w` reach `Histogram.fill` without any op having taken two of them as inputs
(`boost.py:154-212`: `fill` collects `args`, `weights`, `sample` into `inputs` and records ONE
External node — that node is the first place the handles meet). So the fill must run its own
unification (most-derived along one chain) *and* its own divergence check, over: all axis values, all
explicit weight factors, and the ambient weight of whichever context wins. As written, §6.1d
delegates a check to a place that structurally cannot perform it, while m48 freezes the behaviour
("divergent-lineage fill → hard error", `:1007`).

**Suggested fix.** State plainly that the unification+divergence rule runs at **every** combining
point, of which the fill is one, and that §2.3e's op-level rule is an early-detection convenience,
not the only raiser. One sentence; the m48 anchor then has an owner.

### H4 — §6.1d's "already-flattened value" refusal has no bound mechanism and no static discriminator, yet m48 freezes it

**Section**: §6.1d (m48 anchor).

**Detail.** §6.1d bins two shapes: a per-object fill MUST pass its value UNFLATTENED (the frontend
records `gak.broadcast_arrays(ambient, value)` and lets the evaluator flatten each input
independently), and "A per-object fill whose value arrives **already flat** alongside a per-event
ambient weight is REFUSED with an error naming the flatten, not silently length-mismatched." m48
freezes that refusal (`:999-1000`).

There is no static discriminator between the two flat cases. A legitimately per-event value
(`gak.firsts(photons[sel].pt)`, `gak.num(jets)`, `MET.pt`) and a flattened per-object value
(`gak.flatten(sel.Jet.pt)`) have the **same** form — 1-D, no jagged dimension — and the same depth
relative to the ambient weight. They differ only in runtime length. The only implementations
consistent with "naming the flatten" are (a) a session walk of the value's cone looking for an
`ak.flatten` node — an unbounded heuristic with real false positives (`gak.flatten(x, axis=2)` yields
a still-jagged per-event array; a per-event quantity computed downstream of some flatten) — or (b) a
runtime length check inside the evaluator, which is an *execution-time* error, not a record-time
refusal.

The evaluator side is measured and supports the positive half of the rule: `FillEvaluator.__call__`
flattens each input independently via `_flat` (`ak.flatten(values, axis=None)`) —
`graphed-histogram-latest/src/graphed_histogram/boost.py:39-47,60-71` — so an unflattened value plus a
broadcast ambient weight do line up. It is only the *refusal* that is unbound.

**Suggested fix.** Bind where the refusal is raised and on what predicate. The cheap, sound version:
raise at **execution** in `FillEvaluator` when a weight input's flattened length differs from the axis
values' — with a message naming the ambient weight and pointing at "pass the value unflattened" —
and re-word the m48 anchor to that contract. If a record-time refusal is really wanted, bind the
cone-walk rule and its false-positive scope explicitly.

### H5 — §2.1's stacking wording ("members pass through unchanged") is wrong for the weight form, and the corpus b-tag-on-JES case turns on it

**Section**: §2.1 stacking vs §2.6b/c (m48 anchor; m49 reference matrix).

**Detail.** §2.1 binds stacking as: "the result inherits those labels (**members pass through
unchanged**) and adds the new labels; a new label's member is the provided value's central universe".
For the loose form (a) that is right. For the **weight form (b)** it is not: registering a new factor
must combine into the ambient weight *label-aligned*, so an inherited shift label's ambient member
becomes `old_ambient[L] × new_factor[L]` — the new factor evaluated **in that shift's universe**.

This is exactly the case the plan advertises as its headline stacking example, and the corpus fixture
is unambiguous about the required physics:

```python
# graphed-corpus-latest/src/graphed_corpus/analyses/systematics.py:73-75
sel_jets = good[sel]
ht = ak.sum(sel_jets.pt, axis=1)
weight = _btag_weight(sel_jets, variation=variation)
```

For `variation="jes_up"`, `_btag_weight` returns the **central** SF computed on JES-shifted jets — so
the `ttbar_4j1b_jes_up` reference histogram is weighted by a b-tag SF that the naive reading of
"members pass through unchanged" (inherited labels keep the OLD ambient, only new labels get the new
factor) would omit entirely. §2.6c's terser phrasing ("each inherited shift label keeps its own")
gestures at the right rule but never says *its own what*, and neither sentence names §2.4 as the
combining rule for the ambient.

The freeze risk is concrete: m48's weight-only reference matrix is `{nominal, btag_up, btag_down}` and
`{nominal, pho_up, pho_down}` — **no shift labels** — so a wrong reading survives m48's stacking anchor
and only detonates against m49's 15-reference matrix, one milestone later, after the m48 suite is
frozen around the wrong semantics.

**Suggested fix.** In §2.1, split the stacking rule per overload: for (a) members pass through; for
(b) the newly registered factor is combined into the ambient weight **label-aligned per §2.4**, so an
inherited label L takes the provided value's own universe L (its central universe only when L is new).
Then extend the m48 stacking anchor to cover a weight `vary` on a context that already carries shift
labels, asserting that the inherited label's ambient member is the factor's L-universe (a node-id or
manual-reference comparison — the corpus fixture is available in m48's repo).

---

## MID

### M1 — §2.3e's "plain Python attribute on the frontend wrapper" is impossible on today's `Array`: it is `__slots__`-ed

**Section**: §2.3e.

**Detail.** §2.3e binds the context handle as "a **plain Python attribute** on the frontend wrapper
object" and argues (correctly, and I verified both legs) that neither a node-id-keyed map nor
`Provenance` can carry it. But `Array` has no `__dict__`:

```
python/graphed/array.py:127-128
class Array:
    __slots__ = ("_node_id", "_session")
```

and the numpy-idiom subclass keeps it closed: `python/graphed/numpy/array.py:71-74`
(`class NumpyArray(Array): __slots__ = ()`). Setting an ad-hoc attribute raises `AttributeError`. The
fix is one slot, but it is a real, un-named Implementation Target on a class every op constructs.

Worth naming in the same breath: the propagation point is a **chokepoint**, not a per-function
obligation. Every frontend Array is constructed in exactly one module —
`python/graphed/session.py:140,168,183,204` all `return self._array_cls(self, node_id)` — and
`record_op(op, inputs, …)` already receives the input Arrays, so the merge rule can be implemented
once there and inherited by every gak function and module verb for free. §2.3e's phrasing ("every
frontend op, every gak function, and every module verb propagates the handle") reads as per-function
work across gak's whole surface and invites a much larger diff than the code requires.

**Suggested fix.** Bind the added slot (e.g. `_context`, underscore-prefixed so `Array.__getattr__`'s
`if name.startswith("_"): raise AttributeError` keeps it out of field-access,
`python/graphed/array.py:332-335`), and name `Session.record_op`/`record_external`/`record_exchange`
as the single propagation site. Keep the dynamic exhaustiveness test as the anti-drift gate.

### M2 — §7.2's node-id unpacking is not reachable through `_GroupReduce`'s count-based positional layout; m48's dedup anchor fails without a layout change nobody bound

**Section**: §7.2 / §6.1c (m48 anchor).

**Detail.** §7.2 correctly derives that `(output, label) → position` is unsound because `mark_output`
de-duplicates — verified at source: `src/store.rs:147-156` (`if !g.outputs.contains(&id) { … }`) and
`python/graphed/execute.py:126` (`return [vals[o] for o in store.outputs()]`). But the *unpacking* for
group plans does not happen in the frontend: it happens on the **worker**, in a reducer whose layout
is count-based and positional:

```
graphed-histogram-latest/src/graphed_histogram/boost.py:100-117
layout: tuple[tuple[str, int, str], ...]   # (label, n_fills, spec), in compiled-fill order
… for label, k, spec in self.layout:  for j in range(i, i+k): total += fills[j];  i += k
```

built from `layout = tuple((label, len(h._fill_nodes), h._spec) …)` (`boost.py:198`) and fed the
distinct-output list (`aggregate.py:57-65`: `values = evaluate_ir(...)`; `return self.reduce(values)`).
The moment two marked fills intern to one node — the exact case §1.2 mandates and m48 freezes ("two
labels whose members are structurally identical give arena Δ = 0, the same node id … both keys present
in the result with ONE evaluated fill", `:962-965`) — `sum(k)` exceeds `len(values)` and
`_GroupReduce` mis-slices or `IndexError`s. §6.1c's only mention of this reducer is "`_GroupReduce`
`{label: hist}` generalized to two-level keys", which an implementer can satisfy while keeping counts
and shipping the bug.

(This is a pre-existing latent defect — two unvaried histograms with structurally identical fills
already trip it — but variations make it a routine case and m48 freezes an assertion that depends on
it.)

**Suggested fix.** In §6.1c (or §7.2), bind the layout change: `_GroupReduce.layout` carries per-slot
**output indices** (`tuple[tuple[str, tuple[int, ...], str], ...]`, or `{(output,label): [indices]}`
for the two-level shape), derived frontend-side from the compiled output list per §7.2 — so shared
node ids replicate rather than shift positions.

### M3 — §2.1's bound signature omits `collections=`, which §2.1 itself requires

**Section**: §2.1.

**Detail.** §2.1 binds the signature literally:

```
graphed.vary(target, name, /, nominal=None, *, is_weight=False, variations=None, **tags)
```

and then, two sentences later, mandates "a `collections={Name: {tag: record}}` mapping for
collections in overload (c)" as the escape for a collection named `nominal`/`is_weight`/`variations`.
`collections=` is not in the signature. m48's grammar anchor freezes "the three **signature-shadowed
names** (`nominal`/`is_weight`/`variations` reachable only through `variations=` / `collections=`)"
(`:1021-1022`) — i.e. the anchor tests a parameter the bound signature does not have. Adding it also
creates a fourth shadowed name (a collection literally named `collections`), which the "three shadowed
names" phrasing then under-counts.

**Suggested fix.** Put `collections=None` in the signature and re-word the shadowing clause to
"the signature's own keyword names (`nominal`, `is_weight`, `variations`, `collections`)", with the
self-reference rule for `collections` stated (it is reachable through itself:
`collections={"collections": {...}}`).

### M4 — the fill's three-way label union has no bound ORDER, although §3.2 determinism and §6.1b/`_GroupReduce` depend on order

**Section**: §2.4 vs §6.1d.

**Detail.** §2.4 binds union order for a **binary** combination ("the first operand's order, then
labels new to the second operand in its own order, `"nominal"` always first") and says explicitly that
order is bound *because* §3.2 determinism and the `_GroupReduce` positional layout depend on it.
§6.1d then forms a **three-way** union — "value-borne labels, ambient-weight labels, and explicit
`weight=[...]` factor labels" — with no operand ordering, and a fill can carry several varied axis
values (`h.fill(pt=varied_A, eta=varied_B)`) with no stated order among them either. Two conforming
implementations can produce different label orders for the same program, which is a determinism gate
(§3.2) and a `_GroupReduce` layout difference.

**Suggested fix.** One sentence in §6.1d: the fill's union is folded left in a fixed order —
axis values in argument order, then the ambient weight, then explicit `weight=[...]` factors in list
order — each fold applying §2.4. Extend the m48 union-order anchor to a fill with varied values in two
axes plus an ambient and an explicit factor.

### M5 — §6.1d broadcasts only the *ambient* weight; an explicit per-event `weight=[...]` factor in a per-object fill hits the same length mismatch

**Section**: §6.1d / §4.2.

**Detail.** §6.1d binds the broadcast for the ambient weight only ("The per-event ambient weight is
**broadcast to the fill's object structure**"), while `weight=[...]` merely "*adds* factors". But the
evaluator flattens **every** input independently and multiplies the weight factors elementwise after
flattening:

```
graphed-histogram-latest/src/graphed_histogram/boost.py:60-71
axes = [_flat(v) for v in values[: self.n_axes]]
weight = _flat(rest.pop(0)); for _ in range(self.n_weights - 1): weight = weight * _flat(rest.pop(0))
```

So in a per-object fill, a per-event explicit factor (`weight=[events.genWeight]`) flattens to
n_events while the ambient flattens to n_objects — the product is a length mismatch, on the mainline
idiom of "ambient registrations plus one explicit factor". Either the frontend broadcasts explicit
factors the same way, or the plan must state that explicit factors are the user's responsibility to
shape and that mixing a per-event explicit factor into a per-object fill is refused (and how).

**Suggested fix.** Extend §6.1d's broadcast rule to "every weight factor the fill applies — ambient
and explicit — is broadcast to the fill's value structure", and add the mixed case to the m48
broadcast anchor.

### M6 — §6.4a's "record is PRE-selection by construction" is an unenforced assumption, and the refusal predicate it leans on is not mechanically defined

**Section**: §6.4a.

**Detail.** §6.4a asserts "`record` is PRE-selection **by construction**" and backs it with one
refusal: "A varied write whose record expression already embeds a `Varied` selection is REFUSED with
an error pointing at `select=`". Two gaps:

1. **Non-varied selections are not covered.** `sel = events[nominal_mask]` then
   `to_parquet(sel.Jet, select=varied_mask)` passes the refusal, and the writer then applies the
   superset mask to an already-selected record — wrong rows, silently, which is the outcome §6.4
   exists to prevent.
2. **The predicate is not decidable as stated.** "Embeds a `Varied` selection" cannot be read off the
   object: a record varied because its *values* vary (the supported, expected input per §6.4b) and a
   record varied because a *varied mask* was applied are both just `Varied` containers of Arrays. §1.2
   keeps labels out of the IR, so nothing in the graph marks a node as "the selection". Distinguishing
   them requires a per-label offsets comparison (which conflates with §6.4d's own refusal) or a cone
   walk with an undecidable "which getitem was the selection" rule — the very rule §6.4a rejects as
   undecidable three lines earlier.

**Suggested fix.** Replace "by construction" with a decidable check the writer can actually run — the
honest one is structural: **all per-label member offsets must equal nominal's at every stored level**
(§6.4d's rule, applied as the *entry* condition), which catches both a varied selection and a
multiplicity-changing variation with one predicate and one error. Then drop the separate "embeds a
Varied selection" refusal or re-word it as the message that predicate emits.

### M7 — §6.1b's `1 + |S| + |W|` fill-node arity is unconditional and axis mode contradicts it

**Section**: §6.1b (m49 anchor) vs §6.2 (m50).

**Detail.** §6.1b binds "A fill combining shift labels S and weight labels W records **exactly**
`1 + |S| + |W|` fill nodes", frozen-counted in m49. §6.2's opt-in axis mode collapses *weight* labels
into a single evaluator-side loop ("lands **weight-label** variations in ONE histogram … via an
evaluator-side loop"), so the arity in axis mode is `1 + |S|`. §6.1b carries no carve-out, and §6.2
never says the arity rule is scoped to sibling mode — so m50 lands a feature that violates binding
text frozen in m49.

**Suggested fix.** Scope §6.1b explicitly to the sibling lowering ("in the §6.1 sibling lowering …"),
and state the axis-mode arity in §6.2 alongside the m50 structural anchor (which already counts
histogram objects and combine payload entries, so it can count fill nodes too).

### M8 — §2.6a ("`[]` access resolves ONLY tree content") contradicts `events[mask]` deriving a context

**Section**: §2.6a vs §2.6c and the §2.6 sketch.

**Detail.** §2.6a binds: "**Attribute and `[]` access on a context resolve ONLY tree content
(collections/branches)**". §2.6c and the sketch both derive a context by exactly that syntax:
"Derived contexts (`events[mask]`) inherit the ambient registry …" and `sel = events[gak.num(jets) >=
4]`. As written the two are contradictory, and m48 freezes §2.6a's clause ("no reserved names on the
context — a tree branch named `weights` or `vary` stays reachable"). A test-author reading §2.6a
literally could freeze `events[mask] → TypeError`, hard-blocking the sketch's central idiom.

**Suggested fix.** Re-word §2.6a to "`[]` with a **string** (or list of strings) resolves ONLY tree
content; `[]` with an `Array`/`Varied` mask derives a new context (§2.6c). The context reserves no
*names*." One clause; the intent is obviously that, but the binding text says otherwise.

### M9 — §6.1d's bound broadcast mechanism is awkward-only, while the seam it lives on is declared neutral

**Section**: §6.1d vs §2.6 ("the neutral context *mechanism* … lives in `graphed` proper") and the
root `CLAUDE.md` §A.4 factorization rule.

**Detail.** §6.1d binds the mechanism by name: "the frontend then records
`gak.broadcast_arrays(ambient, value)`". That function is awkward-idiom and records an
awkward-namespaced op:

```
python/graphed/awkward/functions.py:677-685
session.record_op("ak.broadcast_arrays", list(arrays), {"index": i, **extra})
```

There is no numpy-idiom equivalent (`grep -rn broadcast python/graphed/numpy/*.py` → only a docstring
mention). Meanwhile the ambient-weight application sits on the *fill*, which lives in
`graphed-histogram` — whose runtime dependency list is `["graphed", "boost-histogram>=1.4",
"numpy>=1.24"]`, with awkward only in the `dev` extra
(`graphed-histogram-latest/pyproject.toml:20-21,24-38`). So the requirement as written asks either
`graphed` proper or `graphed-histogram` to reach into the awkward idiom, which is the boundary rule
§2.1 itself invokes to keep `vary` a neutral module verb.

**Suggested fix.** Bind the broadcast as a **seam**, not a call: the context supplies its ambient
weight already shaped to the fill's value structure via a backend-dispatched op (the neutral op-name
route the frontend already uses everywhere else), with the awkward implementation being
`ak.broadcast_arrays` and the numpy idiom a documented no-op/refusal (rectilinear values have no
per-object level). Say which package owns it.

### M10 — §6.4a's `select=` has no bound relationship to the §2.6 context idiom that m48 establishes

**Section**: §6.4a vs §2.6.

**Detail.** In the owner-locked context idiom the user holds `sel` (a derived context), not a mask —
`sel = events[gak.num(jets) >= 4]`. §6.4a's write API requires the *mask* and refuses the
post-selection record, so a user who followed the m48 idiom has no bound way to write a skim: contexts
expose no accessor for the mask that derived them (§2.2/§9.1 list `labels`/`universe`/`nominal`/
`variations` only), and there is no bound way to write "the collections of a context". m51 thus lands
a sink that only works for programs written in the loose (§2.1a) style, one milestone after the plan
makes the context the "primary user idiom" (§2.6).

**Suggested fix.** Either add a bound accessor for a derived context's own mask (`graphed.selection(ctx)`
returning the `Varied` mask, which §2.6b's lineage already retains), or bind a context-aware write
spelling (`graphed.to_parquet(ctx.Jet)` where the writer reads the context's lineage for the masks and
the pre-selection buffers) — the latter also does most of B1's work. Whichever is chosen, say it in
§6.4a and anchor it in m51.

---

## LOW

### L1 — `to_parquet` is `graphed.awkward.to_parquet`, not `graphed.to_parquet`

§6.4a and §6.4e spell the write verb `graphed.to_parquet(...)` / `graphed.read_varied(path)`.
Measured: `to_parquet` is exported only from the awkward idiom package
(`python/graphed/awkward/__init__.py:14,30`; defined at `python/graphed/awkward/io.py:206`), with a
separate 1-D-capped numpy implementation (`python/graphed/numpy/io.py:158-173`). The plan hedges
("exact spelling at m51 freeze"), but the `graphed.`-prefixed spelling reads as a neutral module verb
and interacts with M9/§6.4f's "numpy backend: EXEMPT … varied writes refuse with a clear error naming
the awkward backend" — a refusal that only makes sense if there *is* a neutral entry point.
**Fix**: say which package owns the varied write verb, and whether §6.4f's numpy refusal implies a
new neutral dispatcher or is just the numpy-idiom function refusing.

### L2 — `graphed.variations` is load-bearing in an m48 section but anchored only in m50

§2.6a lists `graphed.variations` among the module functions that make "the context reserves NO names"
work, and §2.6 is an m48 target; but the only anchor for it is m50's ("**§9.1
`graphed.variations(ctx)`** (no anchor before r10)"), and m48's introspection anchor names only
`graphed.universe`/`labels`/`nominal`. **Fix**: either move the surface's existence (not its numeric
parsing) into m48's §2.2 anchor, or drop it from §2.6a's list.

### L3 — §1.1's "every label is … usable verbatim as a kwarg name" is contradicted two paragraphs later

§1.1: "every label is therefore itself a valid identifier, **usable verbatim as a kwarg name**, …" —
but tags are what appear as kwarg names, and §1.1 itself then says "literal kwarg syntax cannot spell
dotted or digit-leading tags (`0p5=` is a SyntaxError)". Canonical numeric tags (`2`, `102`, `5em1`
for the first two) are digit-leading. The claim is true of *labels* as identifiers (because `name` is
an identifier) and false of tags as kwarg names. **Fix**: drop "usable verbatim as a kwarg name" from
the list, or scope it to non-digit-leading tags.

### L4 — the 32-character cap bounds the tag, not the things it is justified by

§1.1 caps the **canonical tag** at 32 characters and justifies it as bounding "the label that reaches
a StrCategory bin and an on-disk column name". The label is `f"{name}_{tag}"` and the on-disk name is
`__vary_{label}__{field}` (§6.4b), both unbounded (`name` and `field` are arbitrary identifiers). The
cap is a fine sanity rule, but the stated justification does not follow. **Fix**: either state the cap
as a tag-sanity bound with no downstream claim, or cap the label.

### L5 — non-minimal hand-typed e-forms are legal and un-canonicalized, so "one value, one label" holds only within a family

§1.1's input sugar grammar is `-?\d+(\.\d+)?([eE][+-]?\d+)?`, which does **not** match an e-form tag
(`50em2` contains `m`), so a hand-typed non-minimal e-form is treated as an ordinary identifier tag and
never canonicalized: `"0.5"` → `5em1` but `"50em2"` stays `50em2`, two labels for one value. The
cross-notation numeric-equality rule catches them only when both appear **in one family**. I checked
the rest of the e-form edge cases and found them sound: exact-decimal arithmetic makes
`"2"/"2.0"/"2e0"/"20e-1"` agree; negative zero → `0`; a fractional value's exponent is negative by
construction so bare `e` cannot appear; huge exponents are bounded by the 32-char cap (`1e30` → 31
digits, accepted; `1e40` → rejected); `".5"`, `+`, `inf`, `nan`, `_` are excluded by the input grammar;
and no string parses under both the e-parser and the p-parser with different values (`m2` = −2 under
both). **Fix (optional)**: either canonicalize a tag that matches the canonical numeric grammar
(cheap: re-render it minimally), or state that non-minimal e-forms are user-owned spellings.

---

## Verdict

**DIRTY** — 1 BLOCKER, 5 HIGH, 10 MID, 5 LOW.

The architecture holds up under this lens and I found nothing to relitigate: §3 (no new NodeKey,
interning-as-sharing, the reachability-difference impact set), §5 (shift lowering, the JER-SF
stochastic contract, the boundary refusal with its positive control), §7.3's honest checkpoint
limitation, and §8.2's r10-rebuilt transport are internally coherent and consistent with what I read
in the pinned roots. §1.1's e-canonicalization survived a deliberate edge-case sweep (L5 is the only
residue). The plan's r10 self-corrections are real corrections, not paper ones — §7.2's node-id rule
and §6.1d's unflattened broadcast are both right about the underlying mechanism.

What is not yet a specification is the **newest surface**, exactly where the brief predicted: the
write-out milestone (B1, M6, M10 — m51 as written cannot express the object-level cutflow its own
anchors require), the axis-mode milestone (H1, H2, M7 — the declaration point and the result shape are
both unbound), and the ambient-fill seam (H3, H4, M4, M5, M9 — the fill is a combining point the plan
does not treat as one, and the mechanism is bound to one backend idiom). H5 and M1/M2 are smaller but
sharp: each is a place where an implementer following the text literally ships something a later
milestone's anchor will reject.

None of the fixes requires reversing an owner-locked decision. B1 and H1 are the two that need a
design call rather than a wording change; the rest are one-to-three-sentence bindings.
