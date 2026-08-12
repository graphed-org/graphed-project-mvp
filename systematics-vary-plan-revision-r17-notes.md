# systematics-vary-plan r17 — revision notes (review round 8, r16 reviews)

Isolated reviser, fresh context. Every finding below was re-verified in-session against the pinned
verification roots (`graphed-latest@ff7c607`, `graphed-exec-check@201ea42`,
`graphed-histogram-latest@211cbbe`, `uproot5-graphed@393ecef`, plus the repos' own `.venv`s) before
acting. 24 findings after NIT exclusion: 0 BLOCKER, 2 HIGH, 11 MID, 11 LOW.
**23 applied, 1 sub-item rejected with counter-evidence, 0 deferred** — no finding's resolution
required reversing an owner-locked decision, so no OPEN ITEMS block was added.

---

## FACTS lens

### F1 — HIGH — `_PartitionReduce`/`_WritePart` are not "the plan's opaque `process` spec"; the ALL-programs / WRITE-plan-journal / label-RENAME churn claims are false as stated — **APPLIED**

**Verification (mine, this session).**
- `python/graphed/core/execution.py:206-217` — `class Plan(Generic[R])` with
  `process: Callable[[Partition, WorkerResources], R]`. No `identity()`, no `task_id`.
- `python/graphed/aggregate.py:95-108` — `aggregate_plan` returns `Plan(process=_PartitionReduce(...))`;
  `python/graphed/write.py:32-43` — `write_plan` returns `Plan(process=write_part, …)`.
- `task_id` exists only on `DurablePlan` (`core/plan.py:126,164-176`) / `DurablePlanV2` (`:267,286`),
  whose `process` is an `OpSpec` (`:54-90`).
- `grep -rn "DurablePlan(" python/` → **0 hits**; all constructions are in hand-written tests
  (`tests/frozen/checkpoint/m8/{analyses.py:115,176,deployment.py:146,test_no_source.py:41}`,
  `tests/frozen/core/m8/…`, `tests/frozen/core/m39/…`, `tests/frozen/frontend/m8/…`).
- `grep -rn "OpSpec.from_callable" python/` → only `shuffle.py:181,188,245,259` (V2 shuffle/join).
- `grep -rn "task_id|DurablePlan|run_resumable" /private/tmp/claude-501/graphed-exec-check/src` → 0.
- `python/graphed/checkpoint/runner.py:77-91` — `run_resumable` calls `plan.process.resolve()` and
  `plan.task_id(part)`, i.e. it requires a `DurablePlan`; a plain `Plan` cannot reach it.
- Documented idiom: `docs/checkpoint/design.rst:20,58-65` — "its process/combine/empty operations as
  import-referenced ``OpSpec``\ s" … `process=OpSpec.from_ref("myanalysis:hist_chunk")`; the frozen
  m8 fixtures mirror it (`analyses.py:114-123`). `grep aggregate_plan|_PartitionReduce
  tests/frozen/checkpoint/` → 0.
- Sub-claim re-measured: `OpSpec.from_callable(_PartitionReduce(...)).kind` → `"opaque"` (true — a
  dataclass instance carries no `__qualname__` — but unreached by any shipped caller).

**Edits.** §7.2's closing sentence now scopes the `identity()`/`task_id` consequence to "wherever
that closure is wrapped for checkpointing", with the measured no-bridge evidence inline. §7.3:
(a) the m49 interrupt/resume anchor gains its `DurablePlan` construction path (m8 `OpSpec.from_ref`
pattern or `OpSpec.from_callable(plan.process)`); (b) "One-time, ALL-programs churn" → "One-time
churn … SCOPED", explicitly withdrawing "every existing journal" and naming the by-reference idiom
as unaffected; (c) the label-RENAME class inherits the same scope; (d) the m51 WRITE-plan-journal
paragraph is **withdrawn** and replaced by the measured fact that write plans carry no journal.
m50's docs anchor now requires all three invalidation classes *with their scopes*; m51's docs anchor
re-worded likewise. Two anchors-appendix rows (`_PartitionReduce …`, `_WritePart …`) rewritten with
the measured evidence.

### F2 — LOW — six stale/imprecise line spans — **APPLIED for 5, 1 sub-item REJECTED**

| # | claim | verdict |
|---|---|---|
| 1 | `boost.py:176-178` should include `:175` (`inputs = list(args)`) | CONFIRMED (`:175` is `inputs: list[Array] = list(args)`, `:176` the extend) → `:175-178` |
| 2 | `m29/test_multi_weight_fills.py:84-86` misses the `len(inputs) == 4` assert at `:87` | CONFIRMED (grep: `:87`) → `:84-87` |
| 3 | §8.2(ii) "`Session._provenance` written at `:141-166`" | CONFIRMED — the five `setdefault` sites are `session.py:138,166,181,202,240` → corrected |
| 4 | appendix parquet-metadata row: `:107,118` are docstrings | CONFIRMED (`grep -n metadata python/graphed/parquet.py`); the load-bearing half re-verified (0 `key_value_metadata`/`with_metadata` in `graphed-latest/python` or `uproot5-graphed/src`) → row rewritten |
| 5 | root prompt `:1286` → `:1285-1286` | CONFIRMED (the bullet begins on `:1285` and wraps) → corrected in the header, §12.3(b) and the appendix |
| 6 | `checkpoint/m8/test_resume.py:51-58` is stale; the test is `:54-58` | **REFUTED** — `grep -n` gives `def test_result_is_invariant_to_partition_count` at **`:51`** and its assert at `:57`; the plan's `:51-58` is correct and the proposed `:54-58` would point into the loop body. No edit. |

---

## DESIGN lens

### D1 — HIGH — the `node id → position` derivation is unsound: the OPTIMIZER collapses distinct record ids — **APPLIED**

**Verification (mine).** `src/optimizer/engine.rs:22-31` (`SYMMETRIC_OPS`, `IDENTITY_TOKENS` for
`x+0.0`/`x*1.0`), `:67-80` (rules), `:89-110` (saturate + quotient). Two probes:
- `graphed-latest/.venv`: `w = gnp.from_array(...)`; `nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5` →
  record ids `0,1,2,3`; `compile_ir(s, nom, m1, m2, mh)` → `GraphStore.deserialize(ir).outputs() ==
  [0,1,2]`, `evaluate_ir` returns **3** values.
- `graphed-histogram-latest/.venv` (the load-bearing path): two `Histogram.fill`s differing only in
  `weight=[w]` vs `weight=[w*1.0]` → `fill_nodes()` ids `[2, 4]`, `compile_ir(s, *fill_nodes)` →
  `outputs() == [2]`. One value for two fill nodes ⇒ `_GroupReduce` mis-slices/`IndexError`s.
The frontend cannot key on this (distinct record ids); the sound key is §8.2(i)'s record→reduced
map, which that section itself establishes does not exist and makes an m49 target.

**Edit.** §7.2 gains a binding paragraph with both probes and an **m48 refusal**: compare
`len(GraphStore.deserialize(ir).outputs())` against the number of distinct marked record ids and,
on a shortfall, raise a `graphed` error naming the outputs/labels plus the workaround (spell the
equal-valued label with the SAME expression — `variations={"1": w}` — routing it through §1.2's
supported record-time dedup). Never slice. m48's §1.2 dedup anchor gains the non-record-time case as
a refusal assertion. Full support (replication through §8.2(i)'s map) parked in §11. New appendix
row records the measurement. Chose the guard over moving the Rust accessor into m48: it is the
smaller commitment, keeps m48's scope, and leaves a documented, expressible workaround.

### D2 — MID — `graphed.labels` on an axis-mode histogram vs §2.2's nominal-first order — **APPLIED**
Verified from the plan (§2.2 nominal-first; §6.2(iii) lexicographic bins; §6.2(i-bis) labels = bin
set) — under any realistic family `"nominal"` is not the lexicographic first. §6.2(i-bis) now binds:
`graphed.labels(h)` returns the bin set RE-ORDERED to §2.2's rule while the stored order stays
lexicographic; the m50 (i-bis) anchor asserts it.

### D3 — MID — `{label: tuple[str, ...]}` cannot express `read_columns`' `None` — **APPLIED**
Verified: `projection.py:109` signature `-> tuple[str, ...] | None`, docstring `:111-113`
("Returns None (meaning 'read every column')"), `:146-147` `if conservative or not needed: return
None`. §5.3 and §9.1 now bind `{label: tuple[str, ...] | None}`; §2.3d's `Varied` union is `None` if
any member's is; the m49 anchor gains a conservative label asserting `None` (not `()`).

### D4 — MID — mixed axis-mode/sibling-mode fills into one histogram undecided — **APPLIED**
Verified the collision: §6.1c keys axis-mode `(output, None)` vs sibling `(output, label)`, and
`_add_groups`/`_GroupZero` (`boost.py:120-130`) are key-wise over per-slot specs that differ by the
variation axis. §6.2(i) now binds the mode as a property of the HISTOGRAM (first fill fixes it;
the other mode is a hard error naming both) and m50's declaration anchor freezes it.

### D5 — MID — "a shift sibling MAY target the same pre-declared variation axis" — **APPLIED**
The MAY contradicted the very next sentence (`1 + |S|` arity), §6.1c's one-slot rule, and m50's
frozen equality anchor. Replaced with a binding statement (targets the axis, writes its label as the
scalar category value, contributes no sibling slot).

### D6 — MID — "family" undefined — **APPLIED**
`grep -n "family|families"` → 8 body hits, always a loose noun, never a definition. §1.1 now defines
a family as one `name`'s tags on one container including inherited labels, so the numeric-equal
check spans stacking calls; the m48 grammar anchor gains the two-call cross-notation case.

### D7 — MID — the per-class floor depends on post-freeze annotations — **APPLIED**
Measured in `graphed-latest/.venv`: the annotation-wide filter over `graphed.__all__` yields
`['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`
— all refusing/expanding. `graphed.context_of` (*eager-metadata*) and `graphed.broadcast_like`
(*broadcasting*) are the sole representatives of their classes and were not in the floor list. Both
added to §2.3d's named list and to `graphed`'s per-repo list in the m48 anchor.

### D8 — LOW — the derived-context READ rule was never bound — **APPLIED**
§2.6c now states it: `sel.Jet` IS `events.Jet` re-indexed by `sel`'s derivation mask, label-aligned
per §2.4 — the rule §6.1d link kind (1), §6.4a's predicates and m48's anchor are all defined against.

### D9 — LOW — m48 anchor's "every expanding verb returns the bound per-label shape" — **APPLIED**
Re-worded per verb (`apply` → `Varied`; `read_columns` → the single union, not a per-label mapping,
which is §5.3's separate m49 verb).

### D10 — LOW — m50 anchor's "empty/`["nominal"]`" either/or — **APPLIED**
Resolved to `["nominal"]`, with §6.1a's bare-`hist`-reads-as-nominal rule as the reason.

### D11 — LOW — §6.4b "every stored field whose VALUE differs per label" — **APPLIED**
Verified the per-partition computation site (`awkward/io.py:111-127`). Re-worded to "IS `Varied`
(structurally, at record time)" plus an explicit "identical across partitions by construction".

### D12 — LOW — §6.1c's per-slot value type / combine branch — **APPLIED**
Verified `_add_groups` is `{label: a[label] + b[label] …}` (`boost.py:120-122`) and `_GroupZero`
uses the per-slot spec (`:127-130`). Re-bound to record the per-OUTPUT MODE (what the frontend
unpacker needs) and dropped "the combine branches on it".

### D13 — LOW — how "the supplied mask IS `graphed.selection(c)`" is decided — **APPLIED**
§6.4a(2a) now binds per-label NODE-ID equality with object identity as a fast path (interning
re-verified: recording one op twice returns the same node id, `src/store.rs:73-88`).

### D14 — LOW — `nominal=` undefined in the shift form — **APPLIED**
§2.1(c) now REJECTS it with an error naming `collections=`; the m48 grammar anchor covers it.

---

## TESTS lens

### T1 — MID — `variation_labels`' declared int key vs the bound `(reduced_id, member_index)` key — **APPLIED**
Confirmed the contradiction inside §8.2 itself (declaration vs "the map keys on
`(reduced_node_id, member_index)` accordingly" vs (iii)'s hook). Re-declared as
`tuple[tuple[tuple[int, int | None], tuple[str, ...]], ...]` (still sorted, so the determinism
argument is untouched); the m49 anchor now says "the map entry keyed `(reduced_id, member_index)`".

### T2 — MID — m50's plan-level `{output: [labels]}` anchor is fill-shaped but placed in `graphed` — **APPLIED**
Verified: named outputs exist only in `graphed-histogram`'s group API
(`plan(histograms: Mapping[str, Histogram] | Sequence[Histogram])`, `boost.py:256-292`), while
`aggregate_plan(*outputs: Array, …)` (`aggregate.py:68-107`) has none; `graphed` declares no
`graphed-histogram` (`pyproject.toml:29-48` vs CI `.[dev]`) and the house pattern is
`importorskip` (`tests/frozen/preserve/m25/…:31`). Anchor moved to `graphed-histogram`'s flat
`tests/frozen/m50` (already a pinned m50 directory).

### T3 — MID — the r16 "frozen test owns the contexted operand" rule is unsatisfiable for the container-traversing class — **APPLIED**
Verified `gak.zip(fields: Mapping[str, Array] | Sequence[Array], …)` at
`python/graphed/awkward/functions.py:118-119` — the mapping is the only array-bearing operand.
§2.3e(2) now binds each `src` fixture as a TEMPLATE with a named substitution SLOT (fillable inside
a Mapping/Sequence) plus an assertion that the substitution happened; `zip`'s mapping removed from
the fixture-owned operand list; the m48 bullet mirrors it.

### T4 — MID — two binding universe/nominal rules in the m51 sink have no anchor — **APPLIED**
Confirmed by reading the whole m51 anchor block (the "chained-context" positive is a second MASK
link, not a projection link). m51's bridge anchor gains (a) `graphed.selection(graphed.nominal(sel))`
returning an unvaried `Array` in the grandparent row space, asserted against a manual projection,
and (b) its refusal as `select=` by predicate (2a).

### T5 — MID — m48 freezes `to_parquet` as the *accepting* representative, false until m51 — **APPLIED**
Confirmed `select=` is §6.4, an m51 target. §2.3d now makes the disposition milestone-dependent
(*refusing* at m48 with an error naming `select=`/m51; *accepting* at m51), the per-class floor is
scoped to the classes a repo's table can host at that milestone (graphed's m48 half hosts four; the
*accepting* representative at m48 is `Histogram.fill` in `graphed-histogram`), and m51 gains the
re-classification anchor.

### T6 — LOW — §2.6a's slice/int context-subscript refusal had no anchor — **APPLIED**
Verified `Array.__getitem__` accepts `slice`/`int` (`python/graphed/array.py:344-371`). One clause
added to m48's context bullet with the mask/string subscripts as positive controls.

### T7 — LOW — §6.3's params-key-absence half is under-determined and vacuous at m48 — **APPLIED**
Verified the M29 precedent (`tests/frozen/m29/test_multi_weight_fills.py:96`) and today's recorded
params (`boost.py:198-212`: `spec`, `n_axes`, `weighted`, `sampled`, plus `n_weights` only when
`len(weights) > 1`). §6.3 and the m48 bullet now bind a KEY-SET equality against a literally spelled
set.

### T8 — LOW — the integer-magnitude rejection message is unanchored — **APPLIED**
m48's grammar anchor gains `"1e40"` (integer-valued, 41 plain digits) asserting the error NAMES THE
MAGNITUDE, distinct from the generic >32-char tag-length rejection.

---

## Bookkeeping

- Status line → `draft for review (r17)`.
- Revision-history entry added summarising the applied fixes by section, the single rejection with
  its counter-evidence, and the absence of deferrals.
- Anchors appendix: +1 measured row (optimizer-merged distinct record ids), 2 rows rewritten
  (`_PartitionReduce`, `_WritePart`), 1 row corrected (parquet KV metadata), 1 row corrected (root
  prompt Out-of-scope span).
