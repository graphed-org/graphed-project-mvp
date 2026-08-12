# systematics-vary-plan r24 — revision notes (review round 15, from the r23 reviews)

Reviser: isolated agent, fresh context. Inputs: `systematics-vary-plan-review-r23-{facts,design,tests}.md`
findings (18 after NIT exclusion; 16 unique after merging two cross-lens duplicate pairs).
Verification roots used: `/private/tmp/claude-501/graphed-latest@ff7c607` (own `.venv`, CPython
3.12.10), `/private/tmp/claude-501/graphed-histogram-latest@211cbbe` (own `.venv`, boost_histogram
1.8.0). Every verdict below rests on a command I ran or a file I read in this session.

**Summary: 16/16 CONFIRMED and APPLIED. Nothing rejected. Nothing deferred — no finding required
reversing an owner-locked decision, so no "OPEN ITEMS (owner)" block was added.**

---

## 1. HIGH / facts §10-m49 §3.4 fixture + 5. MID / design §3.4 (MERGED — same text, same fix)

"exactly one construction exists" for a two-label shared node is false.

**Verdict: APPLIED.** Verified myself against `graphed-latest@ff7c607`:

```python
from graphed.core import GraphStore
s = GraphStore(); src = s.add_source("events", {})
k  = s.add_op("scale", [src], {"c": "3.0"})      # shared upstream node, nominal never uses it
nom= s.add_op("sel",   [src], {})
up = s.add_op("shift", [src, k], {"d": "up"}); dn = s.add_op("shift", [src, k], {"d": "dn"})
# reachability from s.nodes()[i]["inputs"]:
# impact up [1, 3]  impact down [1, 4]  shared non-nominal [1] (= k)
# members differ: True   impact sets differ: True
```

The interning half of r23's clause does hold (`src/store.rs:73-88`, read: `if let Some(&id) =
g.intern.get(&key) { return Ok(id); }`), but it only forbids the DOWNSTREAM variant. The
shared-upstream construction exists and is strictly more discriminating.

**Edit** (§10, m49 §3.4 anchor bullet): withdrew the "exactly one construction exists / does not
exist at all" sentences; re-pinned the fixture to the shared-upstream form; kept the true narrower
statement ("no node DOWNSTREAM of the fork can be shared by two labels with distinct members");
added the three-conjunct assertion incl. `impact(up) != impact(down)`; kept the id-watermark
rejection note; noted §8.2(i)'s m49 anchor already builds the same construction so the two may
share a fixture. The r23 revision-history line is marked WITHDRAWN in place.

## 2. MID / facts §2.6b + 12. MID / tests §2.6b (MERGED)

r23's context-identity illustration is a mixed-granularity multi-axis fill.

**Verdict: APPLIED.** Verified: `bh.Histogram(Regular(3,0,10), Regular(3,0,10)).fill(np.arange(3.0),
np.arange(5.0))` → `ValueError: spans must have compatible lengths` (bh 1.8.0, graphed-histogram
venv), and §6.1d r19 (plan :1845-1860) explicitly removed two fixtures of this shape and closes
"mixed-granularity multi-axis fills are NOT scoped in m48–m51".

**Edit**: §2.6b illustration → `graphed.nominal(sel).MET.pt + graphed.nominal(sel).MET.phi` (the
op-level form m48's anchor actually freezes) and "legal programs" → "programs this plan scopes";
the identical sentence in the r23 revision-history entry respelled the same way with an r24 note.

## 3. LOW / facts §10 m48 target line — "three m48 anchors carry a non-empty S"

**Verdict: APPLIED.** Read m48's §2.3b anchor (plan :3574-3585): it contains no `Histogram.fill`;
its negative controls are `TypeError` (`array.py:369-371`) / `AttributeError` on `.node_id`
(`array.py:374-375`), explicitly "invisible to a histogram-value comparison". §6.1b defines `S` as
a property of a FILL, so it is undefined there.

**Edit**: "three" → "two", §2.3b item dropped with the reason stated inline; the r23
revision-history line annotated "corrected to TWO in r24".

## 4. MID / design §6.1c — `.plan()` refusal keyed on "varied" while the hazard is keyed on MODE

**Verdict: APPLIED.** Verified in graphed-histogram@211cbbe: `Histogram.plan` passes
`_SumFills(self._spec)` (`boost.py:246`, within the plan's cited `:244-253`) and `self._spec =
spec_of(self)` at `:148`; measured `bh.Histogram(Regular(3,0,1)) + bh.Histogram(Regular(3,0,1),
StrCategory(['nominal']))` → `ValueError: axes have different length`. m50's r23 fourth output is
axis-mode with NO variations, so the "varied" trigger does not fire on it.

**Edit**: §6.1c re-keyed on "VARIED *or* in §6.2 AXIS MODE (equivalently: staged fills' spec differs
from the `__init__`-time `self._spec`)" with the measurement; m48's anchor re-worded to the same
predicate with the axis-mode arm assigned to m50; m48's positive control narrowed to "unvaried
SIBLING-mode"; m50's fourth output gained a one-line `.plan()`-raises assertion.

## 6. MID / design §2.2/§2.3a — `Varied`'s per-idiom surface unbound

**Verdict: APPLIED.** Verified: `dir(Array)` public = `['filter','map','node_id','reduce',
'repartition','session']` (6); `dir(NumpyArray)` = 32, the extra 26 numpy-only names as listed;
`issubclass(NumpyArray, Array)` True. The backend proxy seam exists and is the house pattern:
`factory = getattr(backend, "array_type", None)` / `self._array_cls: type[Array] = factory() if
callable(factory) else Array` (`python/graphed/session.py:36-39`, used at `:140,168,183,204,242`).
§10 pins the property fixture to the numpy idiom (plan :3657, "MUST be a 1-D partitioned source").

**Edit**: one bound clause in §2.2 — `Varied` is per-idiom, mirroring `_array_cls`: neutral base
carrying `Array`'s surface, `graphed.numpy` subclass mirroring `NumpyArray`, `graphed.vary`
returning the class paired with `type(x)`.

## 7. MID / design §9.1 vs §6.1d r19 — `graphed.weight(ctx)` justified on a refused program

**Verdict: APPLIED (option (a) — keep r19, fix the rationale, park the gap).** Verified the three
plan sites (§9.1 :2999 pre-edit, §6.1d :1771-1775, m48 anchor :3838) and that `unweighted=` is new
source (today's signature `fill(self, *args, weight=None, sample=None, threads=None)`,
`graphed-histogram src/graphed_histogram/boost.py:152-158`). Chose (a) because m48's anchor already
freezes r19's reading and (b) would re-open a frozen-anchor semantic for no measured need.

**Edit**: §9.1's second ground withdrawn and replaced with the read-back grounds that survive;
§6.1d gained an r24 sentence stating the consequence ("ambient suppressed + own factor" is not
expressible from a contexted program in v1) and pointing at §11; §11 gained the parked item.

## 8. MID / design §6.4a — field-scoped level-≥1 key has no spelling for the canonical skim

**Verdict: APPLIED.** Verified the plan's two spellings collide (`("Jet", 1)` at :2196 etc. vs
`to_parquet(events.Jet, …)` / `to_parquet(E1.Jet, …)` / `to_parquet(sel.Jet)` as the written record),
and measured the discriminator is a record-time FORM property (graphed-latest venv, awkward):
single-collection `jets.layout.form.type` → `var * {pt: float64, eta: float64}`; multi-collection →
`{Jet: var * {pt: float64, eta: float64}, Muon: var * {pt: float64}}`.

**Edit**: §6.4a admits the BARE depth-`k` key where the level-k structure is the record's own, with
the form-based decidability argument and a refusal (naming the ambiguity and field paths) for a
record with two or more independently jagged fields at that depth; the storage sentence and §6.4d
follow; m51's object-migration anchor now states it writes the MULTI-FIELD record while §6.4's
canonical skim uses the bare key; the anchors-appendix row updated with the measured forms.

## 9. LOW / design §2.2 — `graphed.nominal` unbound on the two result shapes

**Verdict: APPLIED.** Verified §6.1a (:1617-1618) names only `universe`/`labels`, §6.2(i-bis)
(:2014-2016) likewise, and m50's (i-bis) anchor asserts only those two.

**Edit**: §2.2 binds `graphed.nominal(x) ≡ graphed.universe(x, "nominal")` on both result shapes
(identity for a bare unvaried hist, `x["nominal"]` for a mapping, the nominal SLICE for axis mode);
m50's (i-bis) anchor asserts it against the same manually-sliced oracle.

## 10. LOW / design §2.1 — nested `Varied` weight factor needs two-level §2.4 resolution

**Verdict: APPLIED.** Verified §2.1's r18 member rule (:426-431), the stacking rule (:481-491) and
§2.6's mainline sketch passing `btag_sf(sjets)` — a `Varied` — as `nominal=`/`up=`/`down=`, plus
§2.2's `{label: Array}` shape statement, which a nested container does not satisfy.

**Edit**: §2.1's stacking paragraph states the two-level resolution (container's member for L, then
that member's own L, each with its own `"nominal"` fallback) and that the composed ambient is always
flat; §2.2's opening sentence notes a member may itself be `Varied` for a registered weight factor
while `graphed.weight(ctx)` stays flat.

## 11. LOW / design §6.4c — unconditional bit-exactness vs supplied-levels-only storage

**Verdict: APPLIED.** Verified §6.4c (:2416-2418) against §6.4a's "the varied write API takes the
mask(s), it does not infer them" and "one packed per-label validity mask per supplied ENTRY".

**Edit**: §6.4c scoped to "at every selection level SUPPLIED through `select=`", with the
consequence stated (an unsupplied level is not recoverable) and §6.4e's manifest extended by one
clause to record which levels are stored — the manifest previously listed only labels → columns →
representation, so the claim needed that clause to be true rather than asserted.

## 13. MID / tests §6.2 — "an unvaried … fill hashes exactly as today" contradicts m50's r23 anchor

**Verdict: APPLIED.** Verified §6.2's sentence, §6.2(ii)'s always-declare rule, §6.1a's r22
`{"nominal"}` inference, and m50's r23 fourth output; the axis-mode payload hash is
`content_hash((spec, variation_payload))` by §6.2's own binding, and the 1-bin axis changes `spec`.

**Edit**: one-word-class fix — "a SIBLING-mode fill, varied or not, hashes exactly as today", with
the reason and the m50 anchor named.

## 14. MID / tests §3.4 — impact API has no name, shape or freeze pinning

**Verdict: APPLIED.** Verified §3.4 (:1297-1303 pre-edit) carried no surface statement; §9.1 listed
it as the bare phrase "the §3.4 impact API"; contrast §5.3's r16 shaped+pinned entry. Read
`python/graphed/session.py:245-255`: `walk(...) -> object` returns the root's value and exposes ids
only through caller-supplied handlers, so the return shape is otherwise unconstrained. House shape
for sorted id/column tuples: `return tuple(sorted(needed))`, `python/graphed/projection.py:147`.

**Edit**: §3.4 gains the §5.3 treatment — read-only `graphed` module verb over `read_columns`'
operands, `{label: tuple[int, ...]}` of sorted record node ids, spelling pinned at m49 freeze — and
§9.1's entry carries the same shape.

## 15. LOW / tests m48 (α) anchor — `CompiledGraph.outputs()` does not exist

**Verdict: APPLIED.** Measured: `dataclasses.fields(CompiledGraph)` → `['ir','source_names']`;
`hasattr(CompiledGraph, "outputs")` → False; definition at `python/graphed/execute.py:36-52` (only
method `evaluate`). The working spelling is `GraphStore.deserialize(compiled.ir).outputs()`, which
§7.2 itself uses at :2722-2724.

**Edit**: m48's (α) anchor parenthetical and §7.2's r20 sentence both respelled, with the measured
field list cited.

## 16. LOW / tests §2.3d/§6.1d(B) — sequential link-composition rule unanchored, unmarked

**Verdict: APPLIED.** Verified m48's lineage-seam anchor is split per SINGLE kind (:3434-3445) and
that the two readings diverge only where a mask link sits below a projection link, which no m48–m51
program builds; the plan's convention is to mark such rules explicitly.

**Edit**: §6.1d(B) marks the ORDERING half knowingly UNANCHORED with the divergence condition, the
precedent list, and the two-link both-per-event value a test-author could add to anchor it.

## 17. LOW / tests §9.1 `graphed.variations` — undefined "kinds", unpinned shape

**Verdict: APPLIED.** grep over the plan: "kinds" as a VARIATION property occurs only at the §9.1
entry and m50's anchor; every other occurrence is a §6.1d link kind or a `NodeKey` kind. The entry
carried no return type and no freeze-pinning clause, unlike its neighbours.

**Edit**: §9.1 fixes the two-word vocabulary (`"weight"` = overload (b), `"shift"` = overload (c);
overload (a) is loose and reaches no context), the return type `{name: {tag: (kind, value | None)}}`
and "spelling pinned at m50 freeze"; m50's anchor registers one of each and asserts both strings.

## 18. LOW / tests m49 §8.2(i) — repo assigned, directory not

**Verdict: APPLIED.** Verified §10's partition names a directory for every other m49 anchor, and
that placement is mechanically load-bearing: `graphed scripts/run-tests.sh:16` (`SUITES`) and `:30`
(`SPLIT_PKGS="frontend numpy awkward"`) — frontend runs one process per milestone subdir, core and
checkpoint one per package.

**Edit**: the bullet names both directories — accessor half in `tests/frozen/frontend/m49`, the
plan-byte determinism half in `tests/frozen/checkpoint/m49` beside §7.3 whose `DurablePlan`-by-value
construction it shares — both under the unique-basename rule, with the measured run-tests citation.

---

## Bookkeeping

- Status line: "draft for review (r23)" → "(r24)".
- Revision history: new `r24 (2026-07-30)` entry summarizing the above by section, recording zero
  rejections and zero deferrals.
- No "OPEN ITEMS (owner)" block added: none of the 16 findings could only be resolved by reversing
  an owner-locked decision (naming, functional surface, e-form tags, event-context attachment,
  record-time expansion, m48–m51 scope, Phase-2 pull-in). The two findings closest to a locked
  decision — #6 (per-idiom `Varied`) and #7 (`unweighted=`) — touch only how the plan SPECIFIES
  surfaces the owner did not fix, and #7 was resolved in the direction that preserves the already
  frozen-anchored r19 semantics.
- Files changed: `systematics-vary-plan.md` and this notes file only.
