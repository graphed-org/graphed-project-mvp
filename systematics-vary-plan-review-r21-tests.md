# Review r21 — TEST ARCHITECTURE lens (review round 13)

- **Document under review:** `systematics-vary-plan.md`, revision **r21** (5069 lines; read in full,
  incl. Part I, every PART II section, §10 milestones, the Anchors appendix and the revision history).
- **Lens:** test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10),
  R0.10a (no wall-clock/size thresholds in frozen tests), determinism-gate compatibility,
  freeze-order hazards, traceability requirement ⇄ anchor, and buildability of every named fixture.
- **Date:** 2026-07-30.
- **Verification roots used** (every code fact below was measured in these, never in the workdir
  submodules):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (consolidated `graphed`, own `.venv`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (own `.venv`, boost_histogram 1.8.0)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42`
- **Owner-locked decisions were not relitigated.** No finding below asks for a different design
  choice; each is an internal inconsistency, a vacuity/buildability defect, or a coverage gap in how
  a locked decision is *tested*.

## What I re-verified green (no finding)

Recorded so the next round does not re-spend the probes:

- **§3.3 / §5.2a / m49 §8.2(i) integers.** Rebuilt the §3.3 topology (D=500, K=50) against
  `graphed-latest@ff7c607`: N=16 → `stages 17`, `reduced_nodes 34`, `reachable 1333`, 3.91 ms;
  N=128 → `129 / 258 / 7157`, 21.68 ms (ratio 5.55 — inside the r18-bound 16.0 gate with the claimed
  headroom). Reduced kinds `{source: 1, stage: N+1, reduction: N}`, i.e. `2N+2` total — matches
  r19/r20's corrected cardinality clause exactly. Arena Δ(N=1→2) with the terminating reduction = **52**.
- **§7.2's r21 derivation.** Reproduced the probe: record ids `src 0, dead 1, b 2, e 3, c 2`
  (`c` interning with `b`) → `GraphStore.deserialize(compile_ir(s,b,e,c).ir).outputs() == [1, 2]` and
  `s._store.outputs() == []`. The first-occurrence-over-distinct-record-ids derivation is sound for
  every program m48 admits.
- **m48 §7.2 schema-absence literals.** `dataclasses.fields` on `graphed-latest`:
  `Plan` = `{process, combine, empty, tasks, next_tasks, stop, open_once}`,
  `ExecResult` = `{value, n_partitions, n_combines, stopped}`,
  `TaskEvent` = `{phase, key, worker, t, partition, n_entries, bytes_read, error}` — all three literal
  sets in §10/m48 are correct, so the anchor freezes a set an implementer can actually hit.
- **m48 property gate (r19/r20).** On a 1-D `graphed.numpy` source: `dtype`/`ndim`/`shape` →
  `Session.node_count()` delta 0; `.T` → delta 1; `gnp.ones(s,(4,3)).T` → `GraphedTypeError …
  displacing the partitioned axis 0`. Both the three-class rule and the r20 1-D fixture pin are right.
- **§6.3 params key set.** `Histogram.fill` records exactly
  `{"spec","n_axes","weighted","sampled"}` (+`n_weights` only when `len(weights) > 1`),
  `graphed-histogram src/graphed_histogram/boost.py:198-212` — the literal set is correct.
- **§4.3 extraction operands.** `inputs = list(args)` then weights then `sample`
  (`boost.py:175-178`), `params["n_axes"]` present, and `GraphStore.nodes()` is id-indexed
  (`nodes()[i]["id"] == i`) — `store.nodes()[fill_id]["inputs"][:n_axes]` is directly buildable.
- **m49 JER partition-invariance witness is order-safe.** `aggregate_plan` keys tasks by the integer
  partition index (`tasks = tuple(Task(i, p) …)`, `python/graphed/aggregate.py:107`) and
  `SequentialRunner` folds `sorted(plan.tasks, key=lambda t: t.key)`
  (`python/graphed/core/execution.py:450`), so a concatenating combine yields the same event order at
  two different `steps_per_file` values. The r15/r16 narrowing of the compared quantity holds.
- **m50's r21 storage pin is correct and the fixture is buildable.** bh 1.8.0: `Double()` and
  `Weight()` both raise `TypeError: Keyword(s) sample not expected`; `Mean()` accepts `sample=` *and*
  `weight=`; `WeightedMean()` accepts both. A two-axis `Regular × StrCategory` `Mean()` histogram
  round-trips `spec_of → zero_of` with `[a.__dict__.get("name") for a in z.axes] == [None,"variation"]`,
  adds under `+`, and accepts a scalar-string category value.
- **m23 citations.** `tests/frozen/m23/test_group_plan.py` indexes the plan value by **bare** output
  name at `:74-75`, `:86`, `:89`, `:99` over a `ChunkedSource` counting `part_reads` — §6.1a's r19
  scoping is genuinely load-bearing and correctly justified, and the §5.2b read witness has a real
  in-repo pattern to copy.
- **m48/m49 fixture feasibility.** `graphed-histogram`'s `dev` extra already carries
  `graphed[awkward,numpy]`, `awkward>=2.6`, `hist>=2.7`, `pyarrow`, `graphed-executors`
  (`pyproject.toml:24-38`), so the vendored corpus matrix (which imports `awkward` + `hist`) runs
  there. `read_columns` returns `None` on conservative consumption (`projection.py:145-146`) — the
  m49 `None`-vs-`()` assertion is real.
- **R0.10a (c) is clean.** The only frozen wall-clock gate is §3.3's ratio bound, explicitly carved
  out against the project plan's M4 mandate; §6.2's scaling claim is frozen as a payload-entry COUNT,
  §6.4c's compression and m50's object count are R0.11 report items, and m51's representation anchors
  are structural. I found no other timing or size threshold inside a frozen anchor.
- **Determinism (d) is clean.** §3.2 (m48 IR bytes, fresh processes, differing `PYTHONHASHSEED`),
  m49 (`DurablePlan.to_bytes`/`task_id` with the §8.2(i) field, by-value construction with
  module-level operands), m51 (manifest bytes) — the three levels are each anchored, and r21's
  withdrawal of the unreproducible `80e8024dc8f3b77d` digest leaves the qualitative claim intact.

---

## Findings

### 1. MID — m48's four-way fold-order anchor uses a varied `sample=` with no storage pin: on the default storage the fixture dies at EVALUATION, exactly the trap r21 fixed one milestone later

**Section:** §10/m48 ("§2.4 label-aligned combination … and §6.1d's FOUR-way fill fold order"), §6.1d.

**Detail.** m48's anchor bullet requires "a fill with varied values in TWO axes plus an ambient weight
plus an explicit `weight=[…]` factor **plus a varied `sample=`** …, asserting the bound operand order
… and that the varied `sample=` is ACCEPTED/expanded rather than raising `AttributeError`". Nothing
pins the fixture's storage. r21 established, for m50's sample-only-label anchor, that this is fatal —
and the identical reasoning applies here, one milestone earlier, in a *fill-shaped* anchor that lives
in `graphed-histogram`'s flat `tests/frozen/m48` where running the plan is the natural way to observe
a label ORDER (the fold order is most directly read off the result mapping's keys, i.e. off an
executed plan).

Measured (bh 1.8.0, `graphed-histogram-latest/.venv`): `Double()` and `Weight()` storages both raise
`TypeError: Keyword(s) sample not expected` on `h.fill(x, sample=s)`; only `Mean()`/`WeightedMean()`
accept it. `graphed-histogram`'s `FillEvaluator` passes `sample` straight through to `h.fill`
(`src/graphed_histogram/boost.py:60-71`) and `Histogram.fill` type-checks nothing about the sample at
record time (`:160-178`), so the fixture RECORDS cleanly and only dies when the plan runs — after the
freeze, against a correct implementation. The plan itself states this failure mode verbatim in §6.1b
r21 but applies it only to m50.

**Evidence.**
```
$ /private/tmp/claude-501/graphed-histogram-latest/.venv/bin/python  (bh 1.8.0)
Double ['sample']            -> TypeError: Keyword(s) sample not expected
Weight ['weight', 'sample']  -> TypeError: Keyword(s) sample not expected
Mean   ['weight', 'sample']  -> OK
WeightedMean ['weight','sample'] -> OK
```
plus `src/graphed_histogram/boost.py:60-71` (`sample = _flat(rest.pop(0)) if self.has_sample else None;
h.fill(*axes, weight=weight, sample=sample)`) and `:152-178` (no storage check at record time).

**Suggested fix.** Add the same one-line pin r21 gave m50 to the m48 bullet: *"the fixture's histogram
MUST use a `Mean`/`WeightedMean` storage — measured, bh 1.8.0 rejects `sample=` on `Double()` and
`Weight()`"*; or, if m48 deliberately wants a record-time-only assertion, say so explicitly ("asserted
over the recorded fill node's `inputs` order; this fixture is never executed") so the test-author does
not build a plan run around it.

---

### 2. MID — m49's §5.3 anchor puts a CONSERVATIVE label "in the same fixture" as the union-growth assertion; measured, one conservative label collapses the whole union to `None`, making the union half tautological

**Section:** §10/m49 ("§5.3 projection-union test … with a CONSERVATIVE label in the same fixture"), §5.3.

**Detail.** §5.3's binding requirement has two halves: (i) "m49 pins a test where a shift needs an
extra column … and **the union grows by exactly that field**", and (ii) the per-label stats verb
reports that extra column, with r17 adding "**with a CONSERVATIVE label in the same fixture** … one gak
op applied directly to the source … asserting that label maps to `None` and not to `()`".

Measured, `read_columns` carries a single `conservative` flag across *all* arrays it is given and
returns `None` if any one of them consumes the whole record:

```python
# graphed-latest python/graphed/projection.py:122-147
conservative = False
...
    else:  # a non-field op consumes the whole source record -> cannot narrow
        conservative = True
...
for array in arrays:
    array.session.walk(array, source=on_source, op=on_op, external=lambda *_a: None)
if conservative or not needed:
    return None
return tuple(sorted(needed))
```

§2.3d states the same semantics for the varied case ("the union is `None` … if ANY member's read set
is `None`"). So if the conservative label is a label of the **same varied program**, the varied
union is `None` and half (i) degenerates to `None == None` — vacuous — or, if the test-author asserts
a grown tuple, red against a correct implementation. The two halves cannot share one program.

**Suggested fix.** Scope the conservative label explicitly: *"the conservative label is carried by a
SEPARATE program (or a separate output set) in the same test module — a conservative member makes the
whole union `None` (`projection.py:145-146`), so the union-growth assertion must be taken over the
nominal + shifted outputs only."* Optionally restate half (i) per label through the stats verb
(`stats[jes_up] == stats[nominal] + ("Jet.eta",)`), which is immune to the interaction.

---

### 3. MID — after r21 the §8.2(i) closure field lands at **m48**, not m49, so §7.3's churn sentence and m50's frozen docs anchor name the wrong milestone

**Section:** §7.2 (β), §10/m48 ("the RETURN-CHANNEL assertion, r21"), §7.3, §10/m50 (docs anchor).

**Detail.** r21 binds (β) as the hook's return channel: *"its RETURN VALUE (the per-plan variation
metadata, or `None`) is attached to the shipped closure as the additive §8.2(i) field"*, and m48's
(α) anchor freezes *"a value returned from the hook — a dummy at m48 — is carried onto the SHIPPED
closure and is readable there (`plan.process`)"*. `plan.process` for an `aggregate_plan` plan is a
`_PartitionReduce` instance — a `@dataclass(frozen=True)` with fields
`ir, source_name, backend_factory, reader, columns, externals, reduce`
(`graphed-latest python/graphed/aggregate.py:44-65`, constructed at `:96-104`). Making a returned
payload readable off it requires the additive field to exist **in m48**.

But §7.3 still binds: *"**One-time churn on landing m49**, SCOPED: §8.2(i) adds a field to
`_PartitionReduce`, so every journal whose `DurablePlan.process` `OpSpec` embeds `_PartitionReduce` by
value is invalidated once, *unvaried* programs included (the field is unconditional)"* — and m50's
**frozen docs anchor** requires the design.rst text to cover "all three invalidation classes, each
with the scope §7.3 binds: … the label-RENAME class and **m49's one-time closure churn**".

Under r21 the unconditional, all-programs churn happens when the field is *added* (m48); m49 only
changes the field's VALUE, which for unvaried programs is unchanged. So m50 freezes a documentation
statement that the plan's own m48 target makes false, and §7.3 mis-scopes the churn. (This is a
documentation-correctness anchor, so the error is frozen read-only for the rest of the arc.)

**Evidence.** `python/graphed/aggregate.py:44-55` (the frozen dataclass and its field list),
`:96-104` (construction from parameters, one line after `compiled = compile_ir(session, *outputs)` at
`:95`); `python/graphed/core/plan.py:72-77,164-176` (an opaque `OpSpec.identity()` is the cloudpickle
blob, which folds instance state into `task_id`).

**Suggested fix.** Either (a) state in §7.2/§7.3 that the closure field is added at **m48** as a
defaulted pass-through and re-scope the churn sentence to m48 (m49 then changes only varied programs'
values), or (b) if m48 is meant to carry the payload without a persistent field, re-word m48's
return-channel assertion so it does not read the payload off `plan.process`. Update m50's docs anchor
to whichever milestone the field actually lands in.

---

### 4. MID — §6.4f's m51 optimizer-merge shortfall check is binding new source with no m51 frozen anchor

**Section:** §6.4f (last third), §10/m51 anchor list.

**Detail.** §6.4f settles a binding requirement: *"Whether §7.2's optimizer-merge REFUSAL also guards
the write path is settled here: **it does** … so at m51 the same
distinct-outputs-vs-distinct-marked-ids shortfall check runs in the varied `to_parquet` path
(record-time, at the call) with §7.2's message and workaround"*. m51's anchor list (superset rows,
bit-exact round-trip, `graphed.selection` bridge, entry checks (1)/(2a)/(2b)/(2c)/level-≥1,
representation anchors, manifest determinism, manifest content, structure refusal, `to_parquet`'s
§2.3d entry, ROOT half, docs, single-read witness) contains **no** anchor for it.

This is precisely the coverage class the plan repairs elsewhere (r14 moved §3.4 out of m48, r16 gave
§5.3's stats verb an anchor, r17 anchored `graphed.selection`'s two return shapes, r18 dropped
`to_parquet` from m48's table): new source with zero frozen-suite diff coverage either fails the DoD's
≥90 % diff-coverage-from-the-frozen-suite gate or is covered only by `tests/extra/**`, which the gate
excludes. It is also cheap to trigger — the check is record-time and `to_parquet` already compiles at
the call (`compiled = compile_ir(session, array)`, `graphed-latest python/graphed/awkward/io.py:229`),
and §1.1 makes the triggering spelling (`variations={s: w * float(s)}`, containing a literal
`w * 1.0`) first-class.

**Evidence.** `python/graphed/awkward/io.py:206-235` (the `to_parquet` entry compiles at the call);
`src/optimizer/engine.rs:22-31` identity tokens; the plan's own measured probe (two fills weighted `w`
vs `w * 1.0` → fill node ids `2`,`4` → `outputs() == [2]`).

**Suggested fix.** Add to m51's anchor list: *"**§6.4f write-path merge refusal**: a varied
`to_parquet` whose per-label `select=`/field expressions include an optimizer-mergeable spelling
(e.g. a label whose value is `w * 1.0`) is REFUSED at the `to_parquet` call with §7.2's message and
workaround, with an UNVARIED positive control that today's write path is unchanged (§6.3)."*

---

### 5. MID — the §2.3e propagation gate's test-owned primary operand has no bound way to match each function's required operand KIND; measured, at least one enumerated *broadcast* member raises on a mismatched primary

**Section:** §2.3e(2) (r16/r17), §10/m48 ("§2.3e context-handle propagation is a SEPARATE, SCOPED gate").

**Detail.** The gate is bound as: the frozen test *owns* the contexted primary operand and substitutes
it into a named slot, while `src` fixtures supply "only the auxiliary/typed operands the measured
surface needs (`concatenate`'s second array, `unflatten`'s counts, `where`'s branches, `linear_fit`'s
operands)". r16 deliberately forbids the fixture from supplying the primary (a fixture-supplied
primary degrades the assertion to `None == None`).

But the enumerated classes (*broadcast* + *container-traversing* + *tuple-returning*) span functions
with incompatible primary-operand types, and graphed type-checks the primary at RECORD time through
the backend's `op_form`. Measured against `graphed-latest@ff7c607` with a jagged-numeric contexted
primary:

```
num(jagged numeric)          -> OK
unzip(jagged numeric)        -> OK (tuple)
unflatten(jagged, counts)    -> OK
with_field(jagged numeric)   -> GraphedTypeError: ill-typed op 'ak.with_field' …
                                no tuples or records in array; cannot add a new field
```

`gak.with_field`/`without_field`/`unzip` want a RECORD primary; `num`/`firsts`/`flatten`/
`local_index`/`combinations` want JAGGED; `where`'s primary is a boolean `cond`;
`drop_none`/`singletons` want an option type; `unflatten`'s primary is flat with matching counts
(measured surface: 65 public functions, enumerated in-session). One test-owned array cannot serve
them all, and the only lever the plan gives (the `src` fixture) is barred from carrying the primary.
A test-author will have to invent a convention (e.g. a fixture-declared operand KIND drawn from a
frozen-test-owned menu of contexted arrays); the wrong first guess reds the gate for a reason
unrelated to handle propagation, and TEST_SANITY's "fails the stub for the RIGHT reason" clause is
what will catch it — i.e. avoidable authoring churn on m48's largest gate.

**Suggested fix.** Bind the missing half: *"each `src` fixture's substitution slot declares the
operand KIND it needs (flat numeric / jagged numeric / record / boolean mask / option), and the frozen
test owns one contexted `Array` of each kind, all read through the SAME context; the gate substitutes
the kind the slot names and asserts the substitution happened."* The context stays test-owned (r16's
property is preserved) while the type requirement, which is a property of the function and belongs
beside its classification, stays in `src`.

---

### 6. LOW — §6.4e's r21 "MUST NOT import `awkward._connect.*`" rule is binding but unanchored, and is not marked knowingly-unanchored

**Section:** §6.4e (r21 ROUTE paragraph), §10/m51.

**Detail.** r21 binds: *"the varied write **MUST NOT import `awkward._connect.*`** … and its route is
the PUBLIC composition"*. m51's manifest anchor asserts only the OUTCOME — that the augmented file
round-trips through `ak.from_parquet`, i.e. that `awkward_array_metadata` survives. Measured (awkward
2.12.0 in `graphed-latest`'s venv), that key is produced only by
`awkward/_connect/pyarrow/table_conv.py`, which `ak.to_parquet` imports at
`awkward/operations/ak_to_parquet.py:14`; so an implementer who simply imports the private helper
satisfies every m51 anchor while violating the binding rule. This document's own convention is to say
so when a rule is deliberately left without a frozen witness (§7.2's "MUST NOT compile a second time",
§1.1's `"1e1000000000"`, §2.2's `vary`-link-walking half); this rule carries no such note.

**Suggested fix.** Either add a one-line witness to m51 (*"the written module's source contains no
`awkward._connect` import"* — a static assertion, or fold it into the repo's integrity scan), or mark
it knowingly unanchored with the reason, in the shape §7.2 already uses.

---

### 7. LOW — m48's §4.1 correctionlib anchor names a `systematic=` param that the recorded node does not have

**Section:** §10/m48 ("§4.1 correctionlib single-payload multi-parameterization"), §4.1.

**Detail.** The anchor's stated observable is *"all labels' `External` nodes share ONE
`PayloadDescriptor.content_hash` and differ only in the `systematic=` param"*. Measured, the
preservation-aligned recording path stores params `{"name": name, "args": json.dumps(args)}` —
the systematic value rides inside the `args` JSON string, and there is no `systematic` key:

```python
# graphed-latest python/graphed/awkward/functions.py:500-509
return session.record_external(
    "correction", _fn, list(inputs),
    {"name": name, "args": json.dumps(args, sort_keys=False)},
    descriptor=payloads.correctionlib_contents_descriptor(blob, name), …)
```

The m9 fixture the anchor cites confirms the shape: `systematic` is a correctionlib *input name*
inside the payload (`tests/frozen/preserve/m9/agc.py:52-58`), consumed through `args=[…]`. A
test-author will find this in a minute, but every neighbouring m48 bullet spends a sentence sparing
exactly this class of mid-freeze discovery (`gak.full_like`, `stable()` rounding, `h.axes.name`, the
pt-cut jets, same-granularity axis values).

**Suggested fix.** Re-word to the measured observable: *"…share ONE `PayloadDescriptor.content_hash`
and differ only in the recorded `args` param (the correctionlib `systematic` category value rides in
the `args` template; `python/graphed/awkward/functions.py:500-509`)."*

---

## Verdict

**DIRTY — 5 MID, 2 LOW, no HIGH, no BLOCKER.**

The test architecture is in good shape and materially better than r20: every r21 change I checked is
correct where it lands (the §7.2 first-occurrence derivation, the m50 sample-storage pin, the
`context_of` identity-link fixture, the §2.2 term-(c) third program, the `(2c)` depth predicate, the
withdrawn digest), and the four lens dimensions that are easiest to get wrong — R0.10a, determinism
compatibility, freeze-order scoping, and the arithmetic in every frozen literal — are clean under
re-measurement.

The residue is of one recognisable kind: **r21's own edits propagated to the clause that states a
rule but not to every clause that consumes it.** Finding 3 is the sharpest instance (the churn
milestone moved when (β) became a return channel, and m50 freezes the stale milestone in user docs);
findings 1 and 2 are the same shape a milestone earlier (a storage pin and a projection interaction
that were reasoned out correctly in one place and not applied in the other); finding 4 is a
requirement settled in §6 that never reached §10; finding 5 is the one genuinely unfinished mechanism
in the m48 skeleton. All seven fixes are local wording changes; none touches an owner-locked decision
and none requires re-opening a design.
