# systematics-vary plan — revision r15 notes (review round 6, r14 reviews)

Isolated plan reviser, 2026-07-30. Inputs: `systematics-vary-plan-review-r14-{facts,design,tests}.md`
(26 findings, NITs excluded). Verification roots used for every code fact below:
`/private/tmp/claude-501/graphed-latest` (@ff7c607, with its built extension + `.venv`),
`/private/tmp/claude-501/graphed-histogram-latest` (@211cbbe),
`/private/tmp/claude-501/graphed-exec-check` (@201ea42). Every finding was re-verified in-session
before acting; nothing was taken on the reviewers' word.

**Outcome: 23 findings after cross-lens merge — all APPLIED. Nothing rejected, nothing deferred.**
No finding's resolution required reversing an owner-locked decision, so no `OPEN ITEMS (owner)`
block was added.

## Cross-lens merges

- `compile_ir` missing from §2.3d's discovery rule — raised by **facts + design + tests** (three
  separate findings) → one fix.
- §5.2c bound to the raw-`GraphStore` §3.3 fixture — raised by **design (MID) + tests (HIGH)**;
  tests additionally caught the double placement → one fix covering both.
- §5.2a: tests raised both the span/oracle defect (HIGH) and the false discriminator claim (MID);
  both are edits to the same paragraph, applied as two distinct bindings.

## Per-finding record

### HIGH — §2.3d discovery rule misses `compile_ir` (facts + design + tests) — APPLIED
**Verified.** In `graphed-latest`'s own `.venv`, implementing the r14 rule verbatim over
`graphed.__all__` (keep callables any of whose parameter annotations mentions `Array`) discovers
exactly `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition',
'shuffle_plan']`. `inspect.signature(graphed.compile_ir)` →
`(session: 'Session', *outputs: 'Any', optimize: 'bool' = True, maximal_fusion: 'bool' = False)` —
no annotation mentions `Array`. `compile_ir` IS exported (`python/graphed/__init__.py:12` and `:44`
in `__all__`), so r14's "named non-`__all__` members" hatch did not reach it either.
**Edit** — §2.3d (rule) and the m48 anchor: the discovery set is `inspect.isfunction` members whose
annotations mention `Array`, **UNION a named freeze-time floor list `{graphed.compile_ir,
graphed.awkward.to_parquet, graphed_histogram.Histogram.fill}`, MINUS `graphed.vary`**; the floor is
no longer scoped to non-`__all__` members; the non-vacuity floor now also asserts the named list is
contained. The design lens's over-fire half (`graphed.vary`/`graphed.Varied` discovered with no
disposition once m48 lands) is closed by the `isfunction` filter (excludes the `Varied` class) plus
the explicit `vary` exclusion. `aggregate_plan`'s "var-positional and ambiguous" parenthetical
softened to "reachability depends on the filter's `*args` handling" (a plain first-parameter check
does reach it). Appendix: existing row softened, one new measured row added.

### HIGH — §6.1d re-indexing defined only over derivation masks (design) — APPLIED
**Verified textually**: §6.1d bound re-indexing "by the intervening derivation mask(s)", while r14's
§2.2 makes `graphed.universe`/`nominal` return a CHILD context (no mask) and §2.6b's `vary` link has
none either — including in this plan's own cited example
`h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)`.
**Edit** — §6.1d now states the rule PER LINK KIND: mask link → re-index by that mask (label-aligned
§2.4); `vary` link → identity; universe/nominal link → project each ancestor `Varied` to that label's
member (nominal fallback), then continue below the link; links compose parent-to-child. The m48
anchor for the child-context case is re-worded over the resulting VALUE (elementwise vs a manually
projected reference), not merely "unifies instead of diverging".

### HIGH — §6.2's per-fill variation label has no carrier (design) — APPLIED
**Verified in `graphed-histogram-latest`**: `src/graphed_histogram/boost.py:180-212` —
`chash = content_hash(self._spec)`, `PayloadDescriptor(content_hash=chash, …)`,
`self._evaluators[chash] = evaluator`; `:283-286` merges every histogram's registry into one dict;
`graphed python/graphed/execute.py:116-124` dispatches an external node by
`nd["descriptor"]["content_hash"]`. So with one spec per axis-mode histogram (forced by §6.2(i)'s
cross-fill agreement rule) all `1 + |S|` fill nodes resolve to a single evaluator.
**Edit** — §6.2 binds the carrier: the per-fill variation payload is a `FillEvaluator` field AND
enters the External content hash (`content_hash((spec, variation_payload))`) in axis mode only, so
M29 identity discipline is preserved; cross-referenced from §6.1c. m50's equality anchor gains a
distinct-`content_hash`/distinct-evaluator witness (bin-for-bin equality alone can mask the defect
when two siblings agree).

### HIGH — §6.4a predicate (2a) undefined for absent operands (design) — APPLIED
**Verified textually**: (2a) is stated purely in lineage terms; §2.3e's drop rule (`:590-592`)
produces context-free results and a hand-built `Varied` mask need never have derived a context;
§6.4a itself calls the loose §2.1a style the alternative sink.
**Edit** — §6.4a binds both cases: record with no handle → (2a) SKIPPED, (2b)'s per-partition
row-count equality decides (keeps the loose sink reachable); contexted record + mask that derived no
context → refused naming the record's context. m51's entry-check anchor gains the loose-style write
as an explicit positive control.

### HIGH — §5.2a's bound span cannot observe K+2; its oracle is unobtainable at freeze (tests) — APPLIED
**Verified.** Plan Part I §3 binds record-time expansion ("the frontend re-records the downstream ops
per variation"), so the `vary` call itself introduces only the fork member; the K chain ops and the
terminating reduction are recorded when the chain is applied to the returned container.
`Session.node_count()` is at `python/graphed/session.py:50-51`. The freeze-order half is a plan
fact (§12.1: the test-author freezes before any implementation exists).
**Edit** — §5.2a binds (1) SPAN = `node_count()` after the complete N=1 program vs after the complete
N=2 program in the SAME Session, and (2) ORACLE = the same second universe hand-built WITHOUT `vary`
in a separate Session — an independent construction, runnable at freeze time, not a self-derived
`delta == len(cone)`.

### HIGH — §2.3a's public-surface parity gate is vacuous as bound (tests) — APPLIED
**Verified**: `python/graphed/array.py:332-335` — `__getattr__` raises only for leading underscores
and otherwise records a `field` op for ANY name; `:374-391` — `filter`/`map`/`reduce`/`repartition`
are real methods and therefore in the enumerated inventory. So instance-level `hasattr` is True on a
`Varied` broadcasting zero methods, and `varied.repartition` resolves to a container whose call
raises `TypeError: not callable`.
**Edit** — §2.3a binds the per-name ASSERTION: resolve on the CLASS
(`getattr(type(varied), name, None)`, which the instance `__getattr__` never intercepts) and require
a real attribute, plus one behavioural probe per disposition class in the same test (broadcast method
returns a `Varied` with matching `graphed.labels`; `repartition` raises the §5.4 refusal, not
`TypeError`). §2.3e(4)'s `Array`-surface gate inherits the rule; the m48 anchor states it.

### HIGH/MID — §5.2c bound to the raw-`GraphStore` topology and placed twice (tests HIGH + design MID) — APPLIED
**Verified**: `tests/frozen/core/m4/test_benchmark.py:1-25` builds with `import graphed.core as gc`,
`gc.GraphStore()`, `add_source`/`add_op` — no frontend, no `vary`; §3.3 tells the author to replicate
that file. `scripts/run-tests.sh:16-25` runs `core` as one process, `:30` `SPLIT_PKGS="frontend numpy
awkward"`.
**Edit** — §5.2c is now a frontend, `vary`-built program in `tests/frozen/frontend/m49` (matching
§10/m49's own assignment), the "rides the §3.3 fixture, so it is one assertion in that file" sentence
is deleted, and `tests/frozen/core/m49` is stated to keep the raw-`GraphStore` scaling benchmark only.

### MID — §5.2a's stated discriminator is unachievable by any arena-delta form (tests) — APPLIED
**Verified in-session** (`graphed-latest/.venv`, toy backend from `tests/frozen/frontend/m11`):
recording the same op twice in one Session returns node id 1 both times and leaves `node_count()`
at 2 → re-recording the shared prefix adds ZERO nodes.
**Edit** — §5.2a restates what the delta does discriminate (no per-universe copy enters the arena;
labels out of node identity; interning engaged through the public path) and points the re-recording
concern at §5.2b's single-read `part_reads == n_partitions`.

### MID — §6.1c: axis-mode slot keying and per-output value shape unbound (design) — APPLIED
**Verified**: `boost.py:100-130` — `layout: tuple[tuple[str, int, str], ...]` summed positionally
into `out[label]`; `_add_groups` = `{label: a[label] + b[label] for label in a}` (homogeneous values
required per key); `plan()` builds the layout at `:282` from `(output_name, Histogram)` pairs.
**Edit** — §6.1c binds one slot per axis-mode output, keyed `(output, None)`, gathering all that
output's fill-node indices, value = the bare histogram, with the per-slot value TYPE recorded in the
layout so a mixed sibling/axis plan is well-typed. m50's scaling anchor re-worded accordingly and
scoped to weight labels so the 1-vs-`N+1` count is unambiguous.

### MID — §6.4b's `{field}` half re-opens the dotted-name hazards (design) — APPLIED
**Verified textually**: §6.4b argues the LABEL half is dot-free via §1.1 and then shows
`__vary_murf_5em1__Jet_pt` without binding the `.`→`_` transform; §1.1 explicitly says the 32-char
cap does not bound `__vary_{label}__{field}`. The cited hazards (appendix rows) are properties of the
whole column name.
**Edit** — §6.4b binds per-level flattening of the field path, a COLLISION refusal at m51's entry
check (real `Jet_pt` vs derived name for `Jet.pt`), and restates §6.4e's manifest as the sole machine
resolver. m51's representation anchor gains a nested-field round-trip + the collision refusal.

### MID — §5.5(a)'s "byte-identical" is unsafe for aggregated float results (tests) — APPLIED
**Verified**: `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:75-79` — `array_equal`
run-to-run at FIXED partitioning, `allclose(rtol=1e-12)` vs eager, with the comment naming
float-summation order; `graphed tests/frozen/checkpoint/m8/test_resume.py:51-58` is the
partition-count-invariance precedent and `analyses.py:29-30` returns `np.int64` counts.
**Edit** — §5.5(a) and the m49 JER anchor bind the compared quantity to partition-local objects that
concatenate deterministically (smeared VALUES, per-label selection MASKS) or an integer-storage count
histogram; never a weighted float histogram.

### MID — §2.5's unreached-label diagnostic names no channel (tests) — APPLIED
**Verified**: `python/graphed/execute.py:36-45` — `CompiledGraph` is a frozen dataclass with `ir:
bytes` and `source_names: tuple[str, ...]` only.
**Edit** — §2.5 names the channel (an additive `CompiledGraph` field carrying a sorted tuple of
unreached labels, or an equivalent read-only accessor), adds the standard "spelling pinned at m48
freeze" clause, notes the interaction with m48's §7.2 schema-absence anchor (which is worded over
`ExecResult`/`Plan`/monitor, not `CompiledGraph`), and marks the weak-reference registration an m48
target whose spelling is likewise pinned.

### MID — §6.3's golden under-determined against §6.1d's unscoped broadcast seam (tests) — APPLIED
**Verified textually**: §6.1d binds "EVERY weight factor the fill applies … is broadcast" via a
recorded `graphed.broadcast_like` node with no scoping; §6.3 gates unvaried paths with a committed
GIR blob.
**Edit** — §6.3 binds both halves: the golden is captured from the PRE-m48 revision, and a fill with
no context handle and no `Varied` input records byte-identically to today (the seam is inserted only
on the varied/ambient path).

### MID — no public accessor for an `Array`'s context handle (tests) — APPLIED
**Verified**: `python/graphed/array.py:127-128` — `__slots__ = ("_node_id", "_session")`; §9.1's
surface list is entirely context-TAKING; m48's fill-shaped anchors are assigned to `graphed-histogram`
(§10).
**Edit** — §2.3e binds a read-only public seam `graphed.context_of(array)`-shaped (spelling pinned at
m48 freeze, returns the handle or `None`) with an *eager-metadata* §2.3d disposition so the m48
exhaustiveness gate discovers it; listed in §9.1 and added to m48's §9.1 target line.

### MID — §2.3e's propagation-gate exemption constrains class NAMES, not membership (tests) — APPLIED
**Verified**: the gate's clause (3) asserts "the exemption set is exactly those two classes";
classification and fixtures live in implementer-editable `src`; measured gak public surface is 65
functions, of which only four are pinned by name in m48's per-class bullet.
**Edit** — §2.3e(3) and the m48 anchor gain a MEMBERSHIP floor: the refusing class is exactly the
§5.4 boundary set, every eager-metadata member's return annotation is non-`Array`, and the
broadcast-class count is ≥ the freeze-time count.

### MID — §10/m49's "covers EVERY anchor" partition leaves two anchors unassigned (tests) — APPLIED
**Verified textually**: the enumeration lists frontend/core/histogram/checkpoint/executors halves;
the m05 ordering witness and the JER-SF fixture appear in none.
**Edit** — both assigned to `graphed-histogram`'s flat `tests/frozen/m49` (histogram-observable;
the JER partition-invariance witness needs a plan run at two `steps_per_file` values), with the
importorskip reasoning restated.

### LOW — §1.1 enumerates two tag channels; the shift form uses a third (design) — APPLIED
**Verified textually** (§1.1 vs §2.1(c): `variations=` is REJECTED in the shift form, whose tags are
the inner keys of the collection mappings).
**Edit** — §1.1 names three channels and keeps validation/canonicalization channel-independent across
all three; the m48 grammar anchor gains a shift-form case (`Jet={"0.5": …}` → `murf_5em1`) plus a
duplicate-after-canonicalization rejection inside one collection mapping.

### LOW — `sample=` undisposed at the fill (design) — APPLIED
**Verified**: `graphed-histogram src/graphed_histogram/boost.py:160-178` — `args` and `weights` are
`isinstance`-checked; `if sample is not None: inputs.append(sample)` is unguarded.
**Edit** — §6.1d binds `sample=` into the fold order (LAST, after explicit factors), with the
measured basis noted.

### LOW — `graphed.selection` has two different definitions (design) — APPLIED
**Verified textually**: §9.1 (the `Varied` mask that derived ctx from its parent) vs §2.2 ("equal to
the argument's selection at that label").
**Edit** — §9.1 states the universe/nominal-derived case explicitly (that label's member of the
argument's own selection: an unvaried `Array` in the grandparent's row space; `None` for a root
argument), and §6.4a(2a) now tests the link KIND ("…and whose lineage link to that parent is a MASK
DERIVATION"), not only the parent relation.

### LOW — m49's §8.2(i) accessor anchor needs a DCE-eliminated id its fixture lacks (tests) — APPLIED
**Verified textually**: §3.3's builder marks every universe's terminating reduction as an output, so
nothing in that topology is dead.
**Edit** — the anchor states the fixture EXTENDS the §3.3 shape with one deliberately unmarked branch
and names the construction (frontend `compile_ir`, the accessor's key space).

### LOW — §6.1d's loose-VALUE refusal message is binding but unanchored (tests) — APPLIED
**Verified textually** (§6.1d binds a distinct message; the m48 execution-time refusal anchor named
only the ambient weight and an explicit factor).
**Edit** — the loose-value case added as a third assertion inside the same m48 anchor.

### LOW — m48's §4.1 correctionlib anchor is a bare title (tests) — APPLIED
**Edit** — the observable stated: all labels' `External` nodes share one
`PayloadDescriptor.content_hash` and differ only in the `systematic=` param (fixture precedent
`preserve/m9/agc.py:56-62`).

### LOW — §2.3c's discovery target "gak" is ambiguous (tests) — APPLIED
**Verified in-session**: `inspect.getmembers(graphed.awkward, inspect.isfunction)` filtered to
`__module__ == graphed.awkward.__name__` discovers **0**; against `graphed.awkward.functions` it
discovers **65**; `graphed.awkward.num` raises `AttributeError` (the functions are not re-exported at
package level).
**Edit** — §2.3c names `graphed.awkward.functions` explicitly, with the measured 0-vs-65 basis.

### LOW — stale line numbers (facts ×3) — APPLIED
- `root = array.node_id` is at `session.py:268`, not `:269` (measured `grep -n`) — corrected in §4.3
  and in the anchors appendix row.
- `graphed-histogram pyproject.toml`: `dependencies = […]` at `:21`; `dev = [` `:25` … `]` `:39`
  (measured `sed -n '18,42p' | cat -n`) — §6.1d's `:20-21,24-38` corrected to `:21` / `:25-39`,
  matching the appendix row r13 already fixed.
- `read_columns` sorts at `projection.py:147` (`return tuple(sorted(needed))`); `:109` is the def and
  `:110-121` the docstring — §8.2(i)'s pointer corrected.

## Bookkeeping

- Status line → **draft for review (r15)**.
- Revision history entry added summarizing the above by severity and section.
- Anchors appendix: +1 measured row (the annotation-wide filter's discovered set vs `compile_ir`),
  2 rows rewritten (the `Array`-FIRST row's `aggregate_plan` parenthetical; the `fill_nodes()` row's
  `:269`→`:268`).
- Only `systematics-vary-plan.md` and this notes file were edited.
