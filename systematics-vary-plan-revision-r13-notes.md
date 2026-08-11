# systematics-vary-plan r13 — revision notes (review round 4, r12 reviews)

Isolated reviser, fresh context. Every finding below was re-verified in-session against the pinned
verification roots (`/private/tmp/claude-501/graphed-latest@ff7c607`,
`graphed-exec-check@201ea42`, `graphed-histogram-latest@211cbbe`) or by re-running the probe, before
any edit. 28 findings in, 24 after cross-lens merge (0 BLOCKER, 5 HIGH, 9 MID, 10 LOW).
**All 24 APPLIED. Nothing rejected, nothing deferred** — no finding's resolution required reversing
an owner-locked decision, so no "OPEN ITEMS (owner)" block was added.

Merges: §2.3d exhaustiveness (facts + design); §10's un-followed m49 repo move (facts + design);
§4.3's missing per-label fill-node channel (design + tests), with the facts lens's
"`Histogram._fill_nodes` is private" correction folded into the same edit.

---

## HIGH

### H1 — design §8.2(i)/(ii): the bound transport can carry a label but nothing keys it — APPLIED

**Verified.** `python/graphed/aggregate.py:57-65`: `_PartitionReduce.__call__` is
`read_partition` → `evaluate_ir(...)` → `self.reduce(values)` — one call, no per-node context.
`python/graphed/execute.py:99-126`: `evaluate_ir` is a bare `for nd in store.nodes():` dispatch loop
with **no `try`/`except`** and no node-id annotation; op dispatch at `:109`, the `kind == "stage"`
branch evaluates members in an inner loop at `:110-115` annotating nothing (exact line numbers
re-grepped this session). So `except Exception` around the call yields an exception with no node id
→ no map key → no label; §8.2's m49 anchors are unsatisfiable by the bound mechanism.

**Edit.** §8.2 gains an explicit part **(iii)**: per-node failure attribution inside `evaluate_ir`
(an optional attribution hook or equivalent exception wrapper at the two dispatch points, annotating
`(reduced_node_id, member_index | None)`), stated as a change to `graphed`'s evaluation path — not
core, not the IR, not any schema — with the m49 anchors worded over the resulting `StageError`, and
the output-position fallback promoted to primary if (iii) is descoped.

### H2 — design §6.4a: entry predicate (2) unsatisfiable for level ≥ 1 — APPLIED

**Verified in the plan's own text** (r12 lines: §6.4a predicate (2); §6.4a per-level channel; §6.4d
"only expressible because §6.4a's `select=` is per LEVEL"; §9.1 `graphed.selection(ctx)` = the mask
that derived a CONTEXT; the m51 anchor "written through the per-LEVEL `select={0: event_mask,
1: jet_mask}` channel — §6.4a r11 is what makes this anchor satisfiable at all"). A level-1 mask is
per-object and jagged over the record's inner dimension, and is not `graphed.selection` of anything
because contexts are event-level (§2.6c `events[mask]`). The r12 runtime clause already narrowed
itself to "each level-0 mask", so the sentence disagreed with itself.

**Edit.** Predicate (2) is scoped per level: **level 0** keeps lineage identity + the runtime
row-count equality; **levels ≥ 1** use the structural check (each per-label member's offsets equal
the record's at that depth) — which is predicate (1)'s comparison, so it shares (1)'s raiser and
costs nothing extra. The "Where the checks RUN" paragraph and the adjacent "Both are
execution-time" sentence (itself inconsistent with that paragraph in r12) were re-worded to the same
split; the m51 entry-check anchor now names the positive control each level's check decides.

### H3 — design §2.6c/§2.2: a context's label set is a strict subset of what its fills produce — APPLIED

**Verified in-plan.** §2.2 accepted "a `Varied` OR an event context (uniform introspection)" but
defined the answer only for a `Varied`; §2.6c bound "`graphed.labels(ctx)` reports the mask's
labels"; §6.1d binds a fill's label set as the §2.4 union of value-borne, ambient-weight and
explicit-factor labels. On the plan's own sketch the two differ by 104 labels (pu = 2 + pdf = 102
registered on `events` before `sel = events[gak.num(jets) >= 4]` is derived by a JES-varied mask).
A root context carrying only weight registrations had no defined answer at all.

**Edit.** §2.2 binds the context answer once: `graphed.labels(ctx)` = the §2.4-ordered union of
(a) ambient-weight labels, (b) `Varied`-collection labels, (c) the derivation mask's labels
(`None` for a root context), `"nominal"` first — by construction a superset of any §6.1d fill's set;
`graphed.universe(ctx, label)` defined correspondingly. §2.6c re-worded to "INCLUDES the mask's
labels"; the m48 anchor now asserts the union on a program that registers a weight BEFORE the
derivation.

### H4 — tests §8.2(i): `frozenset[str]` makes the serialized plan seed-dependent — APPLIED

**Verified by re-running the probe.** One identical `(3, frozenset({5 labels}))` payload cloudpickled
under `PYTHONHASHSEED` 1 / 7 / 12345 → sha256[:16] `b33099e93b65735c` / `97af80b50319fead` /
`d0001d6ad5eb8f3b` (three distinct). Chain verified in code: `aggregate.py:96-107` makes
`_PartitionReduce` the `Plan`'s `process`; `core/plan.py:95-108` `from_callable` falls through to
`opaque` for an instance (the `from_ref` round-trip resolves the CLASS, not the instance);
`:72-77` `identity()` = the cloudpickle bytes; `:164-176` `task_id` folds `identity()`. House
discipline confirmed: `projection.py:109-121` documents `read_columns` returning a SORTED read set.

**Edit.** §8.2(i) re-binds the field as `tuple[tuple[int, tuple[str, ...]], ...]` — ordered, sorted,
never a set — with the measurement recorded inline; the "map is set-valued" sentence now says the
value is carried as that sorted tuple; §6.4e's manifest is bound to sorted keys for the same reason;
m49 gains a plan-byte determinism anchor (two fresh processes, differing `PYTHONHASHSEED`, identical
`DurablePlan.to_bytes()` and per-partition `task_id`). Anchors appendix gains the measurement row.

### H5 — tests §2.3d/§2.2: binding module-verb dispositions and reserved names are unanchored — APPLIED

**Verified.** m48's anchor list (read in full) contains no bullet for `compile_ir`/`evaluate_ir`/
`aggregate_plan` refusing a `Varied`, none for `apply`/`read_columns` expanding, none for
`Varied.node_id`/`session` raising. The parity gate cannot reach the latter: `array.py:137-143`
shows `node_id`/`session` are plain properties, which `inspect.isfunction` does not enumerate.

**Edit.** New m48 anchor in `graphed`'s `tests/frozen/frontend/m48`, table-driven off §2.3d's
discovery rule: each refusing verb raises a `graphed` error naming `graphed.universe` (positive
control: the same verb on a plain `Array` still works); each expanding verb returns the bound
per-label shape; `varied.node_id`/`varied.session` raise `AttributeError`, with a negative control
that `varied["node_id"]` (string getitem) still resolves as field access so the rule cannot be a
blanket `__getattr__` refusal. §2.2 cross-references the anchor.

---

## MID

### M1 — facts+design §2.3d: the "EXHAUSTIVE" enumeration is not exhaustive — APPLIED

**Verified.** `python/graphed/__init__.py:27-58` exports `pack_key`, `shuffle_plan`, `join_plan`
alongside the disposed verbs; `shuffle.py:84,89` (`pack_key(array, *, on)` → `array.session.
record_op`), `:142,155` (`shuffle_plan(output, …)` → `output.session`), `:208,220`
(`join_plan(output, …)` → `output.session`). All three take an `Array` first and were undisposed.

**Edit.** All three bound to **refuse** with the §5.4 boundary message (`pack_key` is a fusible `Op`
by its own docstring but exists to pre-key a source for a shuffle/join, and both plan builders ARE
the §5.4 path, so one message covers all three), plus a **discovery rule** making the list
self-repairing: the m48 anchor enumerates `graphed.__all__` dynamically, filtered to `Array`-first
callables, and asserts every discovered verb carries a disposition. Anchors appendix row added.

### M2 — facts §6.2(i-bis): `h.axes.name` holds only for a one-axis histogram — APPLIED

**Verified by re-running the probe** (boost_histogram 1.8.0): one-axis → `h.axes.name ==
('variation',)`; two-axis (`Regular` + named `StrCategory`) → `AttributeError: object Regular has no
attribute name`; `[a.__dict__.get('name') for a in h2.axes]` → `[None, 'variation']`, and the same
after a `spec_of` → `zero_of` round-trip through `graphed_histogram._spec` (run against that repo's
own `src`). The binding requirement stands; only the evidence was unrepresentative.

**Edit.** §6.2(i-bis) restates the measurement on a TWO-axis histogram (the round-trip invariant)
and binds "read `axis.__dict__`, never `h.axes.name`"; the m50 (i-bis) anchor carries the same
caution; the Anchors row is rewritten with both measurements.

### M3 — facts+design §10/m49: directory pins and repo list exclude a required `graphed-histogram/m49` — APPLIED

**Verified.** Plan §10 preamble pinned only `tests/frozen/m48` and `tests/frozen/m50` for
`graphed-histogram`; m49's header named `graphed` + `graphed-executors`; m49 anchor (i) requires
`graphed-histogram`, flat `tests/frozen/m49`. `ls /private/tmp/claude-501/graphed-histogram-latest/
tests/frozen` → `m23  m29` (flat), so the move is mechanically sound.

**Edit.** §10 pins `tests/frozen/m48`, `tests/frozen/m49` **and** `tests/frozen/m50` for
`graphed-histogram`; m49's header repo list becomes `graphed` + `graphed-histogram` +
`graphed-executors`, with the DoD/R0.5 reason stated (freeze tagging and full-matrix CI key on it).

### M4 — design §6.1c/m48: the `.plan()` refusal over-freezes m50's mixed axis-mode program — APPLIED

**Verified.** `graphed-histogram src/graphed_histogram/boost.py:88-98`: `_SumFills.__call__` is
`total = zero_of(spec); for f in fills: total = total + f` — plain histogram addition, which over
disjoint variation-axis bins merges nothing. §6.2 permits shift siblings targeting the same
pre-declared axis (`1 + |S| > 1` varied fill nodes) and m50 anchors exactly that program, so r12's
count-worded refusal ("more than one staged fill node with varied labels") would refuse a correct
path, permanently, from a read-only frozen test.

**Edit.** The m48 anchor is re-worded over **sibling mode** (varied staged fill nodes AND not in
§6.2's axis mode), noting the axis-mode opt-in is a recorder-side flag the frontend already owns per
§6.2(i), so the predicate is decidable at `.plan()`. §6.1c's own prose is unchanged (it already
scopes itself), only the anchor's predicate moved.

### M5 — design+tests (+facts) §4.3/§7.2/§9.1: the bound extraction channel does not exist as a public API — APPLIED

**Verified.** §7.2 says only that the frontend *owns* the `(output, label) → node id` map;
§9.1's enumerated surface has no node-id channel. `graphed-histogram boost.py:215-219`: `staged_fills()`
and a **public** `fill_nodes() -> list[Array]` exist (used at `tests/frozen/m29/
test_multi_weight_fills.py:84,95`) — so r12's "(`Histogram._fill_nodes` is private)" named the wrong
obstacle; the real one is the missing LABEL correspondence. `session.py:245-252` shows `walk(array,
…)` takes an `Array` (root at `:269`), not an id.

**Edit.** §9.1 gains the accessor (`graphed_histogram.fill_nodes_by_label(h) -> dict[str, Array]`
-shaped, or an equivalent labelled return from the §6.1c group API; **spelling pinned at m48
freeze**, m48 target, read-only) with the measured reason. §4.3 replaces the false parenthetical
with the accurate statement, cites the accessor, and adds the `Array(session, nid)` note for
`session.walk`. Because its operands come from a fill, the §4.3 anchor is explicitly assigned to
`graphed-histogram`'s half of the m48 split (r12 named the mechanism but assigned the anchor to
neither repo). Anchors appendix row added.

### M6 — design §9.1/§10: milestone target lists omit §9.1 although `graphed.weight` is m48 — APPLIED

**Verified in-plan.** §9.1 marks `graphed.weight(ctx)` m48 and §2.6a agrees; m48's target line
listed no §9 section while m50's said "Targets: §6.2, §9"; m48's stacking anchor says it MUST use
`graphed.weight(ctx)`, and §6.4b is stated to be unsatisfiable without it.

**Edit.** m48's targets gain "§9.1 partially — `labels`/`universe`/`nominal`/`weight` and the
per-label fill-node accessor only"; m50's narrow to "§9.1's `graphed.variations` only + §9.2";
m51 keeps `graphed.selection` (already carried by §6.4a's bridge text, now named in the same clause).

### M7 — tests §5.5(a)/m49: the JER-SF witnesses cannot discriminate a constant seed — APPLIED

**Verified in-plan.** §5.5(a) forbids per-run seeds and binds randomness to event content; the four
r12 witnesses (run-to-run byte identity, pairwise-distinct counts, bidirectional migration, one
interned draw node) are all satisfied by a fixed-constant-seed RNG drawn per partition, which
nonetheless smears the same event differently under a different partitioning — invisible to the
determinism gate, which holds partitioning fixed.

**Edit.** §5.5(a) states the observable consequence (partition invariance) and the m49 anchor gains
that fifth witness: the identical event set at two `steps_per_file` values yields byte-identical
per-label results. Deterministic, R0.10a-safe.

### M8 — tests §10: two pinned frozen directories collide on natural basenames — APPLIED

**Verified.** `scripts/run-tests.sh:16-25` lists `core:tests/frozen/core` and
`preserve:tests/frozen/preserve` as whole-package suites; `:30` `SPLIT_PKGS="frontend numpy awkward"`
— so `core` and `preserve` are one pytest process each. `find tests/frozen -name __init__.py` →
empty. Existing basenames: `tests/frozen/core/m4/test_benchmark.py` (which §3.3 tells the author to
replicate), `tests/frozen/preserve/m9/test_reproduce.py` and `.../test_inspect.py` (precisely m50's
§9.2 anchors).

**Edit.** One binding sentence in §10 with the measured citation and suggested names
(`test_variation_benchmark.py`, `test_varied_bundle_reproduce.py`, `test_varied_inspect.py`).
Anchors appendix row added.

### M9 — tests §10/m48+m49: the cross-repo dependency edits omit their CI install lines and misname the precedent — APPLIED

**Verified.** `graphed pyproject.toml:42-48` (`dev`) contains **no** `graphed-corpus`; the repo
vendors `tests/_corpus/{graphed_corpus,references}` (23 JSONs, counted) with `tests/_corpus` on
`pythonpath` (`:114-127`) — i.e. the cited precedent is VENDOR-only, not "dev extra AND vendor".
`graphed-exec-check/.github/workflows/ci.yml:13-17` carries `CORPUS: "graphed-corpus @
git+https://github.com/graphed-org/graphed-corpus-mvp@main"` and installs it at `:38` BEFORE
`pip install -e .[dev]` — so the name in that repo's `dev` extra resolves only because of the
pre-install. `graphed-histogram/.github/workflows/ci.yml:13-17` has `GRAPHED` + `EXECLOCAL` only.

**Edit.** m48's binding becomes **vendoring only** (copy `graphed_corpus` + the 23 JSONs to
`tests/_corpus/`, put it on that repo's `pythonpath`, no new dependency — matching the cited
precedent exactly and requiring no CI edit), with the measured reason recorded and an explicit
fallback clause: a future revision preferring the dependency route MUST bind the pair (dev-extra
name PLUS the env var and its `pip install` line in every job running the frozen suite). Anchors
appendix row added. The `importorskip` prohibition is unchanged.

---

## LOW

### L1 — facts: three stale line anchors + three off-by-one range starts — APPLIED

**Verified.** `grep -n 'arr.node_id' python/graphed/execute.py` → only `:70` (`:74` is `blob =
bytes(`). `aggregate.py`: the `aggregate_plan` def runs `:68-77`, `session = outputs[0].session` is
at `:86` (`:66-72` is a blank line + signature head). `awkward/io.py:121` is `(out,) =
evaluate_ir(...)`, `:122` is `result = ak.Array(out)`. `graphed pyproject.toml:41` closes the `all`
extra, `:42` is `dev = [`, `:48` closes it. `graphed-histogram pyproject.toml:25` is `dev = [`,
`:39` closes it (`:24` is a comment); its `dependencies` is the single line `:21`.
`scripts/run-tests.sh`: `SUITES=(` `:16` … `)` `:25`, `SPLIT_PKGS` `:30`.

**Edit.** All six repointed at every occurrence (body §2.2, §2.3d, §6.4f, m48/m49 fixture prose,
§10, and the three Anchors rows), each with the corrected value and a note of what actually sits at
the old line.

### L2 — facts §4.3: "`Histogram._fill_nodes` is private" is false — APPLIED (folded into M5)

Evidence and edit: see M5. The substantive claim (no per-LABEL channel) survives; the reason was
wrong and could have sent the m48 test-author looking for an oracle one public call away.

### L3 — facts §6.4e: KV sets incomplete/array-dependent, digests unreproducible — APPLIED

**Verified by re-running the probe** (awkward 2.12.0 / pyarrow 25.0.0): both writers' files always
carry `ARROW:schema`; `ak:parameters` appears for a record array and is absent for a list-of-float
and a flat numeric array — array-dependent, not writer-dependent; the arrow path always drops
`awkward_array_metadata`; `"metadata" in signature(ak.to_parquet)` → `False`; `created_by` →
`parquet-cpp-arrow version 25.0.0`. The r12 digests could not be reproduced (my record-array run
gives different values) because neither the plan nor the worklog names the array written.

**Edit.** §6.4e restated: different bytes for every array probed, the arrow path drops
`awkward_array_metadata`, `ARROW:schema` always present, `ak:parameters` array-dependent (a test
freezing a literal KV set would be red for the wrong reason). The two digests are withdrawn. All
BINDING conclusions (conditional writer swap, KV reproduction, `ak.from_parquet` round-trip) stand.
Anchors row rewritten.

### L4 — design §3.1 vs §8.2: absolute "no optimizer change" contradicts the m49 accessor — APPLIED

**Verified in-plan** (§3.1's absolute sentence; §8.2's "§3.1 still holds" over an accessor whose data
is the `remap` vector `dead_code_elimination` never returns, `src/optimizer/mod.rs:88-116`).

**Edit.** §3.1 re-worded to "no optimizer SEMANTICS change", naming the read-only remap accessor as
the one optimizer-adjacent addition in m48–m51; §8.2 cross-references the re-wording and states
plainly that it means retaining and returning data the reducer discards today.

### L5 — design §6.1d: `broadcast_like`'s numpy semantics left as an either/or — APPLIED

**Verified.** `grep -rn broadcast python/graphed/numpy/*.py` → one docstring mention
(`python/graphed/numpy/__init__.py:8`, "dtype promotion, broadcasting, and type errors are numpy's
own"): there is no existing numpy-side behaviour to inherit, and a no-op vs a refusal are
observably different for an all-numpy varied fill.

**Edit.** Bound as a **no-op** (rectilinear, already aligned; a genuine shape mismatch surfaces as
numpy's own error at execution — the same execution-time refusal shape §6.1d already binds).

### L6 — design §1.1: the input grammar admits magnitudes the integer rendering then rejects — APPLIED

**Verified in-plan**: the input-sugar grammar states no magnitude bound; integers render as plain
digits; a canonical tag > 32 characters is rejected. So `"1e40"` is legal input, canonicalizes to 41
digits, and dies with a tag-length message, while `"1e-40"` → `1em40` is accepted.

**Edit.** One clause in §1.1: an integer-valued input whose plain-digit rendering exceeds the cap is
rejected **at canonicalization with a message naming the magnitude**, not a generic length error,
with the `1e40` / `1e-40` asymmetry stated.

### L7 — design §7.3/§6.4f/m51: the one-time churn paragraph omits `_WritePart` — APPLIED

**Verified.** `awkward/io.py:239,260` construct `_WritePart`; `:274` passes it to
`gw.write_plan(partitions, writer)`; `write.py:32-43` builds `Plan(process=write_part, …)`;
`core/plan.py:164-176` folds `process.identity()` into `task_id`. §6.4f binds widening
`_WritePart.__call__`, so the m49 churn shape repeats at m51 for every write plan, unvaried included.

**Edit.** One sentence in §7.3 with those citations, plus an m51 docs anchor requiring the same
paragraph to record it. Anchors appendix row added.

### L8 — tests §6.2/m50: the "direct discriminator" catches only under-declaration — APPLIED

**Verified by re-running the probe** (bh 1.8.0): over-declaration (4 bins, 3 labels filled) →
`sum == sum(flow=True) == 3.0` (not caught); under-declaration (2 bins, 3 labels) → `sum 2.0` vs
`sum(flow=True) 3.0` (r12's numbers, reproduced).

**Edit.** §6.2(ii) and the m50 declaration anchor now state two assertions: the flow check as the
UNDER-declaration witness, plus an equality against a **literally spelled** expected label list —
explicitly not one read back from the histogram or from `graphed.labels(h)`, which §6.2(i-bis)
defines AS the axis bin set (circular). "Stale" dropped from the discriminator's description.
Anchors row added.

### L9 — tests m50: the structural scaling anchor's allocation half has no observation seam — APPLIED

**Verified.** `graphed-histogram boost.py:100-117`: `_GroupReduce.__call__` returns a
`{label: histogram}` mapping whose length IS the countable payload quantity; nothing in the plan
binds an allocation-counting seam, and counting objects needs monkeypatching or a
`gc`/`tracemalloc` heuristic.

**Edit.** The anchor is worded over the countable invariant only (1 combine payload entry vs `N+1`,
plus bin-for-bin equality); the allocation-count claim moves to the R0.11 implementer report beside
the wall-clock half.

### L10 — tests m48: the §1.2 anchor is worded unscoped while §1.2 carves out axis mode — APPLIED

**Verified in-plan** (§1.2's §6.2 carve-out; `graphed-histogram boost.py:180-212` shows the spec is
content-hashed into node params, so in axis mode labels DO enter identity by design). The frozen
test stays green (its program is sibling-mode), so this is a wording hazard, not a breakage — but
every comparably exposed anchor carries the scoping clause and this one did not.

**Edit.** The m48 §1.2 anchor now reads "for a varied program **in the DEFAULT SIBLING lowering**",
cross-referencing §1.2's carve-out with the measured reason.

### L11 — tests §8.2(i): the new core accessor has no anchor in the repo that owns it — APPLIED

**Verified in-plan**: m49's `graphed` half enumerates §5.2a, §5.2c, §3.4, §5.3, §5.4 and §3.3 — none
touches the accessor; the only anchors exercising it are the cross-process `StageError` anchors in
`graphed-executors`. The DoD requires ≥90% diff coverage from the frozen suite of the repo the code
lands in.

**Edit.** New m49 anchor in `graphed` over the §3.3 builder topology: every surviving record id maps
to a `(reduced_id, member_index)` whose reduced id is in the compiled output/stage set, a
DCE-eliminated record id maps to `None`, and two labels' shared node maps to ONE reduced id — which
doubles as the non-vacuity witness for §8.2's keying claim. The same bullet carries H4's plan-byte
determinism anchor.

---

## Consistency edits made while applying the above (no new findings)

- §6.4a's "Both are **execution-time**, per partition" sentence contradicted the r12 "Where the
  checks RUN" paragraph (which makes predicate (2) record-time). Re-worded to the r13 per-level
  split as part of H2 — the sentence would otherwise have been left flatly wrong by that edit.
- Status line → **draft for review (r13)**; revision-history entry added summarizing the applied
  fixes by section with the merge/rejection/deferral counts.
