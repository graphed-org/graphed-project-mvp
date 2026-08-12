# systematics-vary plan — review round 6, DESIGN SOUNDNESS lens

- **Lens:** design soundness (is PART II a coherent, implementable specification? contradictions,
  unhandled interactions, under-specified Implementation Targets, package-boundary/factorization
  violations, milestone-boundary consistency).
- **Plan revision reviewed:** r14 (`systematics-vary-plan.md`, 2837 lines, read in full including
  Part I, every PART II section, §10 milestones, the Anchors appendix and the revision history).
- **Date:** 2026-07-30.
- **Verification roots used** (all code facts below were measured in-session against these, never
  against the stale submodules in `/Users/lgray/vibe-coding/graphed-workdir`):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607a8ba637ebc1b5db37316adf6e10028dcc`
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe22497b64ce624d4880005af7faddf74f7`
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4a628201cfac569b1829aaa6c32655ec92`
- **Owner-locked decisions were not relitigated.** Nothing below asks for a different naming,
  surface, encoding, attachment point, architecture, scope or ordering choice; every finding is an
  internal inconsistency or an unbound semantic inside a decision the owner already made.

Emphasis followed the brief: deepest attention to §2.6 (functional context), §6.1d, §6.4/m51 and
§1.1's r9 e-canonicalization. §1.1's canonicalization was probed hard (exact-decimal unification,
non-minimal re-rendering, negative zero, the 32-char cap and its integer-magnitude carve-out,
cross-notation p/e rejection, canonical-grammar-vs-input-sugar overlap) and I found **no** internal
contradiction there beyond LOW-1 below; the grammar is closed.

---

## Findings

### HIGH-1 — §2.3d's r14 discovery rule provably misses `compile_ir`, and over-fires on m48's own new exports

**Section:** §2.3d (`:492-541`), m48 anchor bullet (`:1831-1861`).

**Detail.** r14 withdrew the r13 "first positional parameter annotated `Array`" filter precisely
because it "provably MISSES four of the verbs disposed above: `compile_ir(session: Session,
*outputs: Any)` …" (`:526-531`) and replaced it with "callables **any of whose parameter annotations
MENTIONS `Array`**" (`:534-536`). Measured, the replacement misses `compile_ir` for exactly the same
reason the plan quotes two paragraphs earlier: its annotations are `Session` and `Any` — the string
`Array` appears nowhere in its signature.

I ran the r14 rule over today's `graphed.__all__` by AST (annotations of every exported callable):

```
discovered: aggregate_plan, apply, join, join_plan, pack_key, read_columns, repartition, shuffle_plan
NOT discovered: compile_ir, evaluate_ir, resolve_backend, capture, handle_opaque, is_enabled, set_enabled
```

`compile_ir` at `python/graphed/execute.py:54-59` is verbatim
`def compile_ir(session: Session, *outputs: Any, optimize: bool = True, maximal_fusion: bool = False) -> CompiledGraph:`.
So the m48 gate — "asserts every discovered verb carries a disposition" — never reaches `compile_ir`,
which is one of the two verbs §2.3d singles out as safety-bearing (it "consume[s]
`arr.node_id`/`arr.session` directly (`execute.py:70` …) and §2.2's reserved-name rule makes the
refusal a clean `AttributeError` seam", `:507-510`) and whose refusal m48's split refusal table
freezes (`:1851-1853`). The closing sentence "a verb whose signature mentions no `Array` at all
(`evaluate_ir`) is out of scope by construction" (`:540-541`) reads as if `compile_ir` were in scope;
it is not.

The same rule over-fires in the other direction once m48 lands. `callable(Varied)` is true and
`inspect.signature(Varied)` exposes `__init__`'s annotations; §2.2 defines `Varied` as holding
`{label: Array}`, and §2.1 types `graphed.vary(target, …)` over `Array | Varied | context`. Both
will therefore be *discovered* by an annotation-mention filter over `graphed.__all__`, and §2.3d
defines no disposition class for them — the gate's own non-vacuity floor enumerates only
"refusing / expanding / broadcasting" (`:538-540`). This is precisely the failure r14 diagnosed for
`broadcast_like` ("the exhaustiveness gate below would have gone red against a correct m48
implementation", `:519-520`), reintroduced by the new filter. (Measured for today's surface: no
currently exported class mentions `Array` in its constructor annotations — `Array.__init__(self,
session: Session, node_id: int)`, `Session.__init__(self, backend: Backend, *, incremental: bool)`,
`GraphedTypeError.__init__(self, op: str, provenance: Provenance, detail: str)`, and the exported
dataclasses' fields — so the over-fire arrives with m48's own additions, not before.)

**Suggested fix.** Bind the discovery set as *annotation-mention OR explicitly named*, with
`compile_ir` moved into the named list beside `graphed.awkward.to_parquet` and
`graphed_histogram.Histogram.fill` (its `*outputs: Any` is not going to be re-annotated by this
work), and exclude non-function members explicitly (`inspect.isfunction`, so classes such as
`Varied` and protocol/dataclass exports are out) or give `vary`/`Varied` an explicit
"is the variation surface" disposition class. Drop the "`evaluate_ir` is out of scope by
construction" sentence's implication that everything else is in scope by construction.

---

### HIGH-2 — §6.1d's ancestor re-indexing is defined only over derivation MASKS, but r14 put non-mask links in the lineage chain — including in the plan's own example program

**Section:** §2.2 (`:404-410`), §6.1d (`:1003-1010`), §2.6b/c (`:657-673`), m48 anchor (`:1981-1983`).

**Detail.** §6.1d binds: "inputs whose contexts sit on one ancestry chain unify to the
**most-derived** context, **and every ancestor-context VALUE is re-indexed to the unified context by
the intervening derivation mask(s), label-aligned per §2.4**". That rule is total only if every
lineage link is a mask derivation. It is not, in two ways:

1. **r14's own addition.** §2.2 now binds `graphed.universe(ctx, label)` and `graphed.nominal(ctx)`
   to return "a CHILD of the argument in the §2.6b lineage chain", justified by the program
   `h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)` — which "would either unify by an unstated rule
   or raise the divergence error on a legitimate program" (`:404-408`). The link
   `sel → graphed.nominal(sel)` has **no derivation mask**. The unified context is the child; the
   ancestor value `sel.MET.pt` is a `Varied` whose per-label members live in *per-label* row sets
   (§2.6c "its ROW SET DIFFERS PER LABEL"), while the child carries only nominal's row set. The
   operation actually needed is a *universe projection* (take each container's `"nominal"` member),
   not a mask re-index — and nothing in §6.1d or §2.2 says so. m48 nonetheless freezes the outcome:
   "so a fill mixing it with a read from the argument unifies instead of diverging" (`:1981-1983`).
   An implementer is left to guess what that fill computes, and the frozen anchor will accept a
   guess that silently mis-weights (the §2.5 confidently-wrong class the plan exists to delete).
2. **§2.6b `vary` links.** `sel2 = graphed.vary(sel, "btag", …, is_weight=True)` also produces a
   child with no derivation mask (row spaces are equal, so re-indexing is the identity) — benign,
   but the rule as written has no case for it either, so "the intervening derivation mask(s)" is
   undefined on the mainline sketch's own last step (`:713-715`).

**Suggested fix.** State the re-indexing rule per link KIND: a mask link re-indexes by that mask
(label-aligned per §2.4); a `vary` link is the identity; a **universe/nominal link projects each
ancestor `Varied` to that label's member (falling back to `"nominal"` per §2.4) and then re-indexes
by the mask(s) below the link**. Say explicitly what `h.fill(graphed.nominal(sel).Jet.pt,
sel.MET.pt)` computes, and word the m48 anchor over that value, not merely over "unifies instead of
diverging".

---

### HIGH-3 — §6.2's per-fill variation label has no carrier: `graphed-histogram` keys its evaluator registry (and the External payload) on `content_hash(spec)` alone, and §6.2's cross-fill rule forces one spec per axis-mode histogram

**Section:** §6.2 (`:1082-1098`), §1.2 carve-out (`:322-326`), §6.1c (`:967-987`).

**Detail.** §6.2 lowers weight labels through "an evaluator-side loop (extend/sibling
`FillEvaluator`; **labels ride the spec/params** under the §1.2 carve-out)" and permits a shift
sibling to "target the same pre-declared variation axis, **writing its label as the scalar category
value of its own fill**". Both require per-fill information the evaluator resolution channel cannot
carry. Measured in `graphed-histogram src/graphed_histogram/boost.py:180-212`:

```python
chash = content_hash(self._spec)
descriptor = PayloadDescriptor(kind="histogram", content_hash=chash, ...)
node = session.record_external("histogram.fill", evaluator, inputs, {"spec": self._spec, ...},
                               descriptor=descriptor, form=HistogramForm(chash))
self._fill_nodes.append(node)
self._evaluators[chash] = evaluator
```

and `graphed python/graphed/execute.py:116-124`:

```python
elif kind == "external":
    chash = nd["descriptor"]["content_hash"]
    ...
    vals.append(externals[chash](*ins))
```

The evaluator is resolved **by the spec's content hash and nothing else**, and `plan()` merges every
histogram's registry into one dict (`boost.py:284-286`, `evaluators.update(h._evaluators)`).
§6.2(i)'s cross-fill agreement rule makes every axis-mode fill in one histogram share one inferred
label set, hence one spec, hence one `chash`. So the `1 + |S|` axis-mode fill nodes of a mixed
shift+weight program (§6.2's own arity) are distinct *nodes* (their inputs differ) that all resolve
to a **single evaluator** — the last one registered wins, and every shift sibling writes the same
scalar category value. §1.2's carve-out does not close this: it says the *bin identities* enter the
spec/params/content hash, which is exactly the part that is identical across siblings.

The same gap hits the weight-label loop: in a mixed program the axis bin set contains shift labels
too, so the evaluator cannot recover "which subset of bins is mine, in what order" from the spec.

This is the shape r10 and r12 each treated as HIGH ("the channel it named does not exist"), applied
to m50's headline mechanism.

**Suggested fix.** Bind the carrier: the per-fill variation payload (a scalar label for a shift
sibling, the ordered weight-label tuple for the loop) is a field of the `FillEvaluator` **and enters
the `PayloadDescriptor.content_hash`** (i.e. `content_hash((spec, variation_payload))`), so each
axis-mode fill node resolves to its own evaluator. Note the M29 identity discipline is preserved —
the extra content appears only when axis mode is used — and cross-reference §6.1c, whose per-slot
spec binding is unaffected.

---

### HIGH-4 — §6.4a predicate (2a) is undefined for a context-free record or a mask that derived no context, i.e. for the loose `§2.1a` write style the same section says is supported

**Section:** §6.4a (`:1261-1292`), m51 anchors (`:2210-2234`).

**Detail.** Predicate (2a) is stated purely in lineage terms: "the supplied mask must be the
selection that derived some context DIRECTLY FROM the context the record was read from:
`graphed.selection(c)` for a context `c` whose PARENT is the record's own context handle (§2.3e) …
a record read from an ancestor or a sibling context is refused at the `to_parquet` call, **naming
both contexts**". Two of its operands can be absent:

- the record may carry **no context handle** — §2.3e's drop rule explicitly produces context-free
  results, and §6.4a itself says the bridge exists because "without a bridge the m51 sink would be
  reachable only from the loose §2.1a style" (`:1287-1288`), i.e. the loose style is treated as a
  supported route; §2.6's close repeats "The loose `graphed.vary` on Arrays (§2.1a) remains public"
  (`:739-740`);
- the mask may be a hand-built `Varied` that derived **no** context at all (nothing in §2.1a
  requires a mask to be used in `events[mask]`).

With either absent, (2a) has nothing to compare and no contexts to name, and the plan does not say
whether the call is refused or passes. Both readings are live and both are costly: refusing makes
the loose sink unreachable one section after the plan asserts it is reachable; passing leaves the
guard silent for context-free records (predicate (2b)'s execution-time row-count equality still
catches the corrupting case, so passing is defensible — but it is *unbound*). A test-author who
freezes the refusal reading hard-blocks the loose sink permanently, which is the exact hazard the r7
sweep recorded for §1.1's grammar ("freezing an earlier revision's rejections would hard-block this
grammar", `:2005-2006`).

**Suggested fix.** State (2a)'s behaviour for the two absent-operand cases explicitly — the natural
binding is: *if the record carries no context handle, (2a) is skipped and (2b) alone decides
(row-count equality per partition); if the record carries a handle and the mask derived no context,
the call is refused naming the record's context* — and add the chosen reading to m51's entry-check
anchor with the loose-style write as an explicit positive control.

---

### MID-1 — §5.2c is pinned to §3.3's raw-`GraphStore` fixture (the `vary`-blind witness r14 just rejected for §5.2a), and §10/m49 places it in a different directory than §5.2c does

**Section:** §5.2c (`:889-893`), §5.2a (`:872-882`), §10/m49 (`:2032-2039`), §3.3 (`:757-779`).

**Detail.** r14 bound §5.2a's arena delta to the public surface because "§3.3 tells the author to
replicate `tests/frozen/core/m4/test_benchmark.py`, which builds with the raw
`graphed.core.GraphStore` API … so an author following §3.3 can hit every pinned integer while
witnessing only `GraphStore::intern` … and a `vary` implementation that re-recorded the shared prefix
per universe would still pass (the R0.10 semantic-stub shape)". Measured, that premise is right:
`graphed-latest tests/frozen/core/m4/test_benchmark.py:1-25` builds with `import graphed.core as gc;
s = gc.GraphStore(); s.add_source(...); s.add_op(...)` — no frontend, no `vary`.

§5.2c was left behind: "reduced-stage shape — **on the §3.3 topology, with its literal** … **It rides
the §3.3 fixture**, so it is one assertion in that file rather than a separate program." Riding the
raw-`GraphStore` benchmark file makes §5.2c a witness of the *reducer*, not of `vary` — the same
semantic-stub exposure, under a section whose heading is "Witnesses that sharing engaged — R0.10".

It is also placed twice, differently: §5.2c puts the assertion "in that file" (§3.3's benchmark,
which §10 pins to `graphed tests/frozen/core/m49`, `:2036-2038`), while §10/m49's per-repo partition
lists "§5.2c stage shape" among the anchors kept in `tests/frozen/frontend/m49` (`:2034-2036`).

**Suggested fix.** Give §5.2c the same r14 treatment as §5.2a: build the topology **through
`graphed.vary`** in `tests/frozen/frontend/m49` (re-measuring `stages == N+1` through the frontend at
freeze, exactly as §5.2a now re-measures its Δ), and delete "It rides the §3.3 fixture, so it is one
assertion in that file"; leave `core/m49` as the raw-`GraphStore` scaling benchmark only.

---

### MID-2 — §6.1c binds only the sibling-mode `{(output, label)}` slot shape; axis mode's slot keying and per-output value shape are unbound, while m50's headline scaling anchor counts exactly those slots

**Section:** §6.1c (`:967-987`), §6.1a (`:934-945`), §6.2(i-bis) (`:1122-1130`), m50 anchor
(`:2167-2181`).

**Detail.** Measured, today's reducer is one slot per OUTPUT with a homogeneous value type
(`graphed-histogram src/graphed_histogram/boost.py:100-130`):

```python
layout: tuple[tuple[str, int, str], ...]   # (output_name, n_fills, spec)
for label, k, spec in self.layout:
    total = zero_of(spec)
    for j in range(i, i + k): total = total + fills[j]
    out[label] = total
def _add_groups(a, b): return {label: a[label] + b[label] for label in a}
```

§6.1c re-binds this to per-slot output INDICES "(or `{(output, label): [indices]}` for the two-level
shape)". That shape is right for sibling mode. Axis mode needs the opposite: its `1 + |S|` fill nodes
must collapse into ONE slot per output (§6.2 "one histogram carrying both classes, filled from
separate passes with a scalar label") and its result must be a **bare** histogram (§6.2(i-bis)), not
`{label: hist}`. Nothing binds (a) how an axis-mode slot is keyed under the two-level shape, (b) that
a single plan may carry sibling-mode and axis-mode outputs whose reducer value types differ — which
§6.1a's declared union result type `dict[str, bh.Histogram | dict[str, bh.Histogram]]` implies and
`_add_groups`' key-wise `+` requires be uniform *per key*.

m50's scaling anchor then counts those slots: "axis mode ships **1 combine payload entry** vs `N+1`
in sibling mode — the length of the per-partition combine payload under §6.1c's two-level key shape,
**one entry per (output, label)**, with the fixture's output count pinned at 1". Under a literal
per-`(output, label)` keying, a mixed shift+weight axis-mode program — the *other* m50 anchor,
`:2128-2131` — ships `1 + |S|` entries, not 1, so the two m50 anchors are only reconcilable if the
scaling anchor's fixture is weight-labels-only, which it does not say.

**Suggested fix.** In §6.1c, bind the axis-mode slot explicitly: one slot per output, keyed
`(output, None)` (or the one-level shape retained for axis-mode outputs), gathering all that output's
fill-node indices, with the reducer's per-slot value type recorded in the layout so a mixed plan is
well-typed. In m50's scaling anchor, scope the fixture to **weight labels only** (`N` weight labels,
no shift siblings) so the 1-vs-`N+1` count is unambiguous.

---

### MID-3 — §6.4b applies §1.1's dot-free discipline to the LABEL half of the stored name only; the `{field}` half re-opens the measured dotted-name hazards

**Section:** §6.4b (`:1306-1326`), §1.1 (`:284-300`), §11 anchor rows (`:2385-2387`).

**Detail.** §6.4b binds the appended-column convention as `__vary_{label}__{field}` and argues at
length that labels are safe: "Labels are valid identifiers by construction (**§1.1 canonicalization,
r9 e-form** — a dotted spelling never reaches a label), so labels appear in on-disk names VERBATIM:
the canonical on-disk shape is `__vary_murf_5em1__Jet_pt`." The measured hazards it cites — 
`ak.from_parquet(columns=["a.b"])` silently empty; uproot 5.7.5 `RField.array()` failing because
`to_akform` splits on `.`; the TTree writer's own `.` nesting separator — are properties of the whole
column name, not of its label half. The `{field}` half carries the user's field path, which is dotted
whenever the written record is nested (`Jet.pt`, `FatJet.subjet.pt`). The plan's own example silently
renders `Jet.pt` as `Jet_pt`, i.e. it assumes a `.`→`_` transform that is never bound, and does not
address the aliasing that transform creates (a real field `Jet_pt` and the derived name for `Jet.pt`
collide). §1.1 is explicitly aware that the field enters the name — "it does NOT bound the label …
or the on-disk name (`__vary_{label}__{field}`, §6.4b), both of which also carry the user's arbitrary
`name` and field" (`:260-263`) — it just never states the constraint.

**Suggested fix.** Bind the field half of the convention at m51 freeze alongside the label half:
either flatten the field path with a separator that cannot appear in a field name and state the
collision rule (refuse when the flattened name collides with an existing stored field), or keep the
path as-is and require §6.4e's manifest to be the *only* resolver with a frozen negative anchor that
a nested-field skim still reads back. Either way, say it, because the plan's stated hazard model
otherwise leaves the exact measured failure reachable.

---

### LOW-1 — §1.1 enumerates two tag channels; overload (c) supplies tags through a third

**Section:** §1.1 (`:307-317`), §2.1(c) (`:355-358`).

**Detail.** §1.1: "Tags arrive as **kwarg names** (`up=…, sig2=…`) or via the `variations={tag: …}`
mapping. Validation and canonicalization are **channel-independent**…". In the shift form (c) tags
arrive as the **inner** keys of the collection mappings (`Jet={"up": j_up, "down": j_dn}` or
`collections={Name: {tag: record}}`), and `variations=` is REJECTED there (`:344`) — so for the
entire shift form neither enumerated channel applies. The rule intended ("channel-independent") plainly
covers it, but the m48 grammar anchor is written over the two named channels only ("float spellings
accepted via `variations=` AND via `**`-unpacking (channel-independent)", `:1990-1991`), so a
canonicalization/rejection bug confined to the shift form survives the freeze.

**Suggested fix.** Add the inner mapping keys of overload (c) as the third named channel in §1.1 and
extend the m48 grammar anchor with one shift-form case (e.g. `Jet={"0.5": …}` canonicalizing to
`5em1`, and a duplicate-after-canonicalization rejection inside one collection mapping).

---

### LOW-2 — `sample=` is undisposed at the fill

**Section:** §6.1d (`:1011-1016`), §2.3d (`:521-522`).

**Detail.** §2.3d binds "`Histogram.fill` accepts `Varied` (§6)" and §6.1d enumerates the fill's
unification and fold order over "all axis values, all explicit weight factors, and the winning
context's ambient weight" — `sample=` appears in neither. Measured, `Histogram.fill` type-checks
`args` and `weights` but **not** `sample`, and appends it to the same `inputs` list
(`graphed-histogram src/graphed_histogram/boost.py:160-178`), so a `Varied` `sample=` falls into
`record_external` and dies on `.node_id` — the same unchecked-fall-through §2.3b documents for
`Array.filter`. Low severity because `sample=` is rare and the failure is loud rather than silent.

**Suggested fix.** One clause in §6.1d: `sample=` participates in the label union and the fold (after
the explicit weight factors), or is explicitly refused when `Varied` with a message naming
`graphed.universe`; mention it in the m48 fill anchor either way.

---

### LOW-3 — `graphed.selection` has two different definitions once §2.2's r14 child contexts exist

**Section:** §2.2 (`:404-410`), §9.1 (`:1608-1610`), §6.4a(2a) (`:1262-1272`).

**Detail.** §9.1 defines `graphed.selection(ctx)` as "the `Varied` mask that derived a context from
its parent". §2.2 defines it for a universe child as "`graphed.selection(...)` equal to **the
argument's** selection at that label" — which is the mask that derived the *parent* from the
*grandparent*, restricted to one label, and is an unvaried `Array` rather than a `Varied`. The two
definitions disagree in both provenance and type. The consequence lands in §6.4a predicate (2a),
whose test is purely "the mask is `graphed.selection(c)` for a `c` whose PARENT is the record's
handle": a record read from `ctx` with `select=graphed.selection(graphed.nominal(ctx))` satisfies
that test while the mask lives in the *grandparent's* row space. (Predicate (2b)'s execution-time
row-count equality would catch it, so this is a specification inconsistency rather than a data-loss
path.)

**Suggested fix.** Say in §9.1 that `graphed.selection` on a universe/nominal-derived context returns
the argument's selection projected to that label (naming the type it returns), and add "…and its
lineage link is not a mask derivation" to §6.4a(2a) so the predicate tests the link KIND, not only the
parent relation.

---

## Clean/dirty verdict

**Dirty** — 4 HIGH, 3 MID, 3 LOW; **0 BLOCKER**. No milestone is unimplementable as written and no
finding requires reversing an owner-locked decision.

The four HIGHs cluster exactly where the brief predicted the least prior review: the §2.3d discovery
rule (re-bound only in r14, and still not matching the measured signature surface it was re-bound
over), the r14 child-context addition to §2.2 meeting §6.1d's mask-only re-indexing rule, §6.2's
per-fill evaluator identity, and §6.4a's entry checks meeting the loose write style. All four are
local: each is a paragraph-sized binding, not a design change.

Areas probed and found **clean** under this lens, stated so the record is not read as silence:
§1.1's e-form canonicalization (exact-decimal unification, non-minimal re-rendering, negative zero,
the 32-char cap and its integer-magnitude carve-out, cross-notation p/e rejection, identifier
closure of every label); §2.1's four shadowed signature names and the per-overload stacking rule
(re-verified against `graphed-corpus src/graphed_corpus/analyses/systematics.py:39-45,60-76,25-36` —
the central b-tag SF is computed on JES-shifted, JES-selected jets, so the label-aligned weight
stacking rule is required and correctly stated); §2.4's union order and the §6.1d three-way fold
order; §5.4's boundary refusal, which is fully discharged by §2.3d's refusing dispositions with no
reachable gap (a variation can only cross a boundary through one of the refusing verbs, and a
variation created downstream of an existing Exchange/Join is correctly permitted); the
package-boundary/factorization rules (§6.2(i-bis)'s duck-typed detection keeps `boost_histogram` out
of `graphed`, §6.1d's `broadcast_like` keeps awkward out of `graphed-histogram`, §6.4e's
awkward-idiom reader keeps pyarrow out of the neutral namespace, and no binding requirement makes
`graphed-core` import awkward); §7.2/§7.3's dedup and churn reasoning; and the milestone/target
mapping in §10, which after r14's corrections is consistent section-by-section (§3.4→m49,
§9.1 split m48/m50/m51, §7.2→m48, §6.2→m50, §6.4→m51) apart from MID-1's §5.2c placement.
