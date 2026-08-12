# Review r26 — TEST ARCHITECTURE lens

- **Document reviewed:** `systematics-vary-plan.md`, revision **r26** (draft for review; 6250 lines,
  read in full — Part I, PART II §§1–12, §10 milestones m48–m51, Anchors appendix, revision history).
- **Lens:** test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), R0.10a
  (no wall-clock/size thresholds in frozen tests), determinism-gate compatibility, freeze-order
  hazards, traceability (requirement ↔ anchor), and testability-as-stated (can the test-author
  actually build the fixture from what the plan gives?).
- **Date:** 2026-07-30 (review round 18).
- **Verification roots used** (every code fact below was measured by me, in this session, against
  these revisions — no fact is carried over from the plan on trust):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607`), using its own
    `.venv` (awkward 2.12.0, numpy, boost-histogram) for runtime probes;
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`);
  - `/private/tmp/claude-501/graphed-exec-check` (`graphed-executors`, `201ea42`);
  - `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`);
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md` (R0.10 / R0.10a / R0.11 read
    at `:196-225`).
- **Owner-locked decisions were not relitigated.** Nothing below proposes a different naming,
  encoding, surface shape, architecture or scope choice; every finding is about whether a frozen
  anchor as worded can be built and can discriminate.

## What I checked and found clean (stated so the reviser knows the sweep was done)

- **R0.10a.** I scanned every anchor in §10 for wall-clock and size thresholds. The only wall-clock
  gate in m48–m51 is §3.3's `time(128)/time(16) < 16.0`, which the plan names as a deliberate
  carve-out and grounds in the frozen M4 precedent. I verified that precedent exists and has the
  shape the plan replicates: `graphed tests/frozen/core/m4/test_benchmark.py` — best-of-3 timing at
  `:27-33`, noise floor `base = max(times[SIZES[0]], 1e-4)` at `:40`, `assert growth < 24.0` at
  `:43`. Every other performance claim (§6.2 axis scaling, §6.4c compression, §7.2 compile count)
  is explicitly demoted to an R0.11 implementer-report measurement. Clean.
- **Determinism-gate anchors.** m48's §3.2 two-fresh-process `PYTHONHASHSEED` anchor, m49's
  plan-byte anchor (module-level `DurablePlan` **by value**, `OpSpec.from_callable`, sorted-tuple
  payload) and m51's manifest-determinism anchor are all in the R22.3 strong form and all carry the
  fixture constraint that makes them red-against-a-correct-implementation-proof. Clean.
- **The §7.2 schema-absence anchor's literal key sets are exactly right.** Measured against
  `graphed-latest@ff7c607`: `Plan` → `{combine, empty, next_tasks, open_once, process, stop, tasks}`,
  `ExecResult` → `{n_combines, n_partitions, stopped, value}`, `TaskEvent` →
  `{bytes_read, error, key, n_entries, partition, phase, t, worker}`. Matches the anchor verbatim.
- **§6.3's params key set is exactly right.** Measured at `graphed-histogram@211cbbe`
  `src/graphed_histogram/boost.py:200-207`: a single-weight fill records
  `{"spec","n_axes","weighted","sampled"}` (`n_weights` only when `len(weights) > 1`). Matches.
- **§4.3's extraction mechanism is buildable.** `inputs = list(args); inputs.extend(weights)`;
  `sample` appended last (`boost.py:175-178`), so `inputs[:n_axes]` is exactly the axis prefix, and
  `params["n_axes"]` is recorded (`:202`). `session.walk` handles sources, externals and everything
  else through one `op` handler (`python/graphed/session.py:245-287`), so a `reachable()` helper
  built from it covers reductions/exchanges/joins too. Clean.
- **The m48 property-classification fixture pin is sound.** Measured: `dir(Array)` public = 6
  names, `dir(NumpyArray)` = 32 (26 extra), discovered properties on `NumpyArray` =
  `['T','dtype','ndim','node_id','session','shape']`. On a 1-D `graphed.numpy` source
  `dtype`/`ndim`/`shape` give `Session.node_count()` delta 0 and `.T` gives delta 1; on a 2-D one
  `.T` raises `GraphedTypeError: ill-typed op 'transpose' … displacing the partitioned axis`. The
  r20 pin to a 1-D fixture is load-bearing and correct.
- **The §2.3d idiom-package enumerations (r26) reproduce exactly.** Annotation-wide filter over
  `graphed.__all__` → `['aggregate_plan','apply','join','join_plan','pack_key','read_columns',
  'repartition','shuffle_plan']` (8); over `graphed.numpy.__all__` (22 names) →
  `['apply_gufunc','empty_like','full_like','ones_like','project','zeros_like']` (6); over
  `graphed.awkward.__all__` → `['project','project_buffers']` (2). Freeze-order is clean for
  `to_parquet`: measured, both `graphed/awkward/io.py:206-207` and `graphed/numpy/io.py:182-183`
  annotate the first parameter `Any`, and `to_parquet` is absent from `graphed.numpy.__all__`, so
  neither idiom enumeration discovers it at m48 — the r18 argument holds. `Projection` really has
  no conservative `None` (frozen dataclass, one field `read_columns: Mapping[str, frozenset[str]]`,
  `python/graphed/projection.py:34-44`), so r26's `{label: Projection}` classification is right.
- **The m48/m49 corpus matrix fixtures are buildable.** `graphed-corpus@49650e4 corpus/references/`
  holds 23 JSONs, 15 of them systematics (10 ttbar + 5 ttgamma), so m48's weight subset
  (ttbar 4j1b/4j2b × {nominal, btag_up, btag_down} + ttgamma {nominal, pho_up, pho_down}) is
  exactly 9. `bin_values`/`fingerprint` (`src/graphed_corpus/histograms.py:35-43`) read `h.values()`
  and work on a bare `bh.Histogram`, so the comparison form transfers. The vendoring target has the
  deps: `graphed-histogram pyproject.toml` `dev` carries `graphed[awkward,numpy]`, `awkward>=2.6`,
  `hist>=2.7`. The §2.6 note (iii) pt-cut-jets correction is right: measured
  `graphed-corpus src/graphed_corpus/analyses/systematics.py:60-76` — `good = jets[jets.pt > 25]`,
  `sel_jets = good[sel]`, `_btag_weight(sel_jets, …)` with `ak.prod(…, axis=1)` at `:25-36`.
- **The m48 `aggregate_plan` (α) seam is anchorable where the plan says.** Measured
  `python/graphed/aggregate.py`: `compiled = compile_ir(session, *outputs)` at `:95`,
  `_PartitionReduce(...)` constructed at `:96-104`, `Plan(process=process, …)` at `:108` — a hook
  firing between `:95` and `:96` and returning a value attached to the frozen `_PartitionReduce`
  dataclass is implementable, and `plan.process` is the read-back route the anchor names.
- **Freeze-order sweep.** I re-walked every m48-frozen assertion against what m49/m50/m51 must
  contradict: §1.2's anchor is sibling-scoped (r13); §6.1a/§6.1b/§6.1c are sibling-scoped and the
  axis-mode slot is deferred to m50 (r16); `to_parquet` is out of m48's §2.3d table entirely (r18);
  the gak *refusing* class is a containment floor with a monotone count (r18); §6.1c's `.plan()`
  refusal is worded over the mode disjunction (r24/r25); the `graphed.labels` order pinned at m48
  is over `Varied`/contexts, not over the axis-mode histogram m50 re-orders (r17). I found **no new
  freeze-order hazard of the r7-sweep kind**, and no anchor still describing r8-era p-form
  canonicalization (the m48 grammar anchor is fully e-form, `"0.5"`→`murf_5em1`, `"50em2"`→`5em1`,
  with the cross-notation `{"0.5","0p5"}` rejection intact).
- **Traceability.** Every binding PART II requirement I could enumerate traces to at least one
  §10 anchor, except the two named below (§9.2's `FORMAT_VERSION`, and the §6.4e levels-entry
  shape). I found no orphan anchor — every §10 bullet names the requirement it discharges.

---

## Findings

### 1. HIGH — m48's §2.1 stacking anchor spells its central assertion as `==` between two recorded expressions; measured, that assertion is **unconditionally true**

**Section:** §10/m48, the §2.1 stacking bullet (`systematics-vary-plan.md:3707-3718`, the assertion
at `:3713-3714`); the rule it discharges is §2.1's r24 two-level `factor[L]` binding
(`:485-501`).

**Detail.** r25/r26 sharpened this anchor precisely so it discriminates the *one-level* reading of
§2.1's stacking rule (which would give the b-tag SF on **nominal** jets and miss the
`ttbar_4j1b_jes_up` reference) from the bound *two-level* reading. r26 then fixed the transcription
hazard in the same sentence — "`x[L]` in this document's PROSE … denotes `graphed.universe(x, L)`
and is NEVER a literal subscript" (§2.2, `:649-652`) — establishing that literal transcription of
this anchor's spelling *is* the expected test-author behaviour. The spelling it left is:

```
graphed.universe(graphed.weight(sel2), "jes_up") == old_ambient_jes_up *
graphed.universe(graphed.nominal(factor), "jes_up")
```

Both sides are deferred `Array`s. Measured against `graphed-latest@ff7c607`:

```
a = from_awkward(s, "events", ak.Array([[1.0,2.0],[3.0]])); b = a * 2.0; c = a * 2.0
type(b == c)  -> <class 'graphed.array.Array'>      # __eq__ RECORDS an elementwise op
bool(b == c)  -> True                                # no __bool__/__len__ override
```

`Array` defines no `__bool__` and no `__len__`, so `assert <Array>` is green for **every** operand
pair, including the one-level wrong answer this anchor exists to reject. Transcribed literally the
anchor also *records* a stray comparison op into the fixture's session, which perturbs any
`node_count()`-based sibling assertion in the same test module.

This is the failure shape the plan itself catalogues twice (§4.3's withdrawn containment predicate
"satisfied BY CONSTRUCTION and cannot fail"; §5.2a's self-derived `delta == len(cone)`), landing on
the anchor that r11/r25/r26 each strengthened. It is silent: the wrong implementation ships green
through m48 and detonates against m49's 15-reference matrix *after* m48 is frozen — verbatim the
exposure r11 opened this anchor to close.

Note this is the **only** Array-vs-Array `==` in the whole §10 anchor list — I grepped every `==`
between `:3457` and `:4955`; every other equality is over ints, tuples, key sets, node ids,
histogram views or `bin_values`, and the two other value-level anchors (§2.6c ambient re-index,
§6.1d link-kind (1)) already say "compared ELEMENTWISE … against a manually re-indexed reference".

**Suggested fix.** Bind the comparison mechanism in the anchor, the way the neighbouring anchors do.
Either (a) **node-id equality** — `graphed.universe(graphed.weight(sel2), "jes_up").node_id ==
(old_ambient_jes_up * graphed.universe(graphed.nominal(factor), "jes_up")).node_id`, sound because
interning makes structurally identical expressions share an id (`src/store.rs:73-88`; measured
`a = src*2.0; b = src*2.0` → both `node_id == 1`) and because this anchor is frontend-observable by
construction; or (b) **materialize both and compare elementwise** through `Session.materialize`
(`python/graphed/session.py:291-301`). Add one sentence to §2.2 beside the r26 `x[L]` prose rule:
"`==` between two recorded expressions in this document's prose denotes structural identity
(`.node_id` equality), never a Python `assert` on the recorded comparison — measured,
`Array.__eq__` returns an `Array` and `bool()` of it is unconditionally True."

---

### 2. HIGH — §8.2(i)'s newly bound PRODUCER for `variation_labels` cannot produce what two m49 anchors freeze: the recipe covers only fill nodes, while both anchors are about **cones**

**Section:** §8.2(i) r26 (`systematics-vary-plan.md:3194-3203`); the anchors it must serve are
§10/m49's `graphed-histogram` population bullet (`:4555-4561`) and §8.2's cross-process attribution
anchor (`:3251-3256`, listed at `:4562-4565`).

**Detail.** r26 closed a real gap (the field had a type, a transport and a carrier but no owner) and
named the producer as:

> the association list is computed by the HOOK SUPPLIER — `graphed-histogram`'s group-plan builder
> (`plan()`…), the sole owner of the `(output, label) → record node id` map (§7.2 r18) — **by
> composing that map with the m49 core accessor**

The m49 core accessor is `record_node_id -> (reduced_node_id, member_index | None)`. Composing a
map whose domain is **the per-label FILL node ids** with it yields, after inversion, a table keyed
on fill-node keys, each carrying exactly **one** label. That table cannot satisfy either anchor:

- **The set-valued anchor is unsatisfiable.** `:4557-4561` freezes "for a `(reduced_node_id,
  member_index)` key **two labels' cones** both reach, carries BOTH labels". Distinct labels have
  distinct fill nodes by construction (§6.1b's `1 + |S| + |W|`), so no fill-node key is ever reached
  by two labels. Under the bound recipe the "BOTH labels" clause has no witness — the implementer
  either files a Test Dispute or reaches outside the recipe.
- **The attribution anchor fails too.** `:3251-3256` freezes "a failure raised inside the `jes_up`
  universe on a worker … re-raises driver-side carrying `variation == 'jes_up'`". Measured, a fill
  is an `External` node and `NodeKey::is_boundary()` is `!matches!(self, NodeKey::Op { .. })`
  (`graphed-latest src/node.rs:100-104`), so the fill is a boundary and a universe's compute chain
  fuses into a **different** `Stage` node. A failure inside that chain produces a
  `(reduced_node_id, member_index)` key that is *not* a fill-node key, so the fill-derived table has
  no entry and no label. §8.2's own analysis says the same thing from the other side ("a universe's
  chain collapses into ONE `Stage` whose members are evaluated inline", `:3173-3175`).

What the recipe is missing is the **per-label CONE step**: walk each label's reachable *record* ids
(this is exactly §3.4's impact computation, `session.walk`-based) and map every one of them through
the accessor. That step is what makes the map set-valued and what §3.4 is cited for two paragraphs
later ("§3.4 proves it in this document: a node shared by `jes_up` and `jes_down` but not nominal
appears in BOTH impact sets", `:3246-3248`) — but the producer sentence never performs it. The
builder *can* do it (measured: `plan()` holds `fill_nodes` at
`graphed-histogram src/graphed_histogram/boost.py:281`, hence a `Session`), so this is
under-specification, not impossibility — but the plan's own standard for a bound recipe is that it
must be able to produce what the same milestone's frozen anchors assert.

**Suggested fix.** In §8.2(i) r26, extend the producer recipe by one clause: "…by taking, per label,
that label's **record-cone** (the reachable record ids from that label's marked output, `session.walk`
— the same computation §3.4's impact verb performs), mapping every id through the m49 accessor, and
unioning labels per resulting `(reduced_node_id, member_index)` key; the `(output, label) → record
node id` map supplies the cone ROOTS. The composition over roots alone is not sufficient: distinct
labels have distinct fill nodes, so it is single-valued by construction and carries no entry for the
Stage a universe's chain fuses into — which is where §8.2's own attribution anchor raises." Then
re-word §10/m49's `graphed-histogram` bullet to say the shared node is **upstream of the fork**
(the §3.4 r24 fixture shape), so the test-author builds a fixture the recipe can actually serve.

---

### 3. HIGH — m49's §5.3 union-growth anchor is not satisfiable in the shape the plan describes: `read_columns` reports **top-level source fields only**, so "the union grows by exactly `Jet.eta`" is false for a correct implementation on any nested record

**Section:** §5.3 (`systematics-vary-plan.md:1603-1610`) and §10/m49's projection bullet
(`:4448-4462`).

**Detail.** §5.3 binds: "m49 pins a test where a shift needs an extra column (e.g. binned SF needing
`Jet.eta`) and the union grows by exactly that field", and §10/m49 freezes "the per-label projection
stats reporting the **shifted label's extra column**". Measured against `graphed-latest@ff7c607`,
`read_columns` only records a `field`/`fields` op **whose input IS the source node**
(`python/graphed/projection.py:129-141`, `if reads_source: … needed.add(str(params["field"]))`), so
a second-level access contributes nothing:

```
data = ak.Array([{"Jet":[{"pt":1.0,"eta":0.5}], "Muon":[{"pt":2.0}]}])
read_columns([ev.Jet.pt], src)            -> ('Jet',)
read_columns([ev.Jet.pt, ev.Jet.eta], src) -> ('Jet',)      # union does NOT grow
```

`Jet.eta` is not a reportable column at all. The plan's own example name therefore describes an
assertion that is **red against a correct implementation** on a nested record — and the nested shape
is exactly what the plan's shift evidence uses everywhere else (`events.Jet` in the §2.6 sketch, the
corpus's `_apply_jes(events.Jet, …)`). Only a **flat** source makes the requirement expressible:

```
flat = ak.Array([{"Jet_pt":[1.0], "Jet_eta":[0.5], "Muon_pt":[2.0]}])
read_columns([ev2.Jet_pt], src2)                 -> ('Jet_pt',)
read_columns([ev2.Jet_pt, ev2.Jet_eta], src2)    -> ('Jet_eta', 'Jet_pt')
```

This is precisely the mid-freeze-discovery class m48 spares the test-author four times over
(`gak.full_like`, the `stable()` rounding, `h.axes.name`, the pt-cut jets) and that r21/r22 spared
for the `Mean`/`WeightedMean` storage — here it is unstated, and a test-author who transcribes the
`Jet.eta` example freezes an unsatisfiable assertion.

**Suggested fix.** State the granularity once, in §5.3, and pin the fixture shape in §10/m49:
"`read_columns` reports only fields read **directly off the source record** — measured,
`python/graphed/projection.py:129-141` counts a `field`/`fields` op only when its input is the
source node, so `read_columns([events.Jet.pt, events.Jet.eta], src)` is `('Jet',)` on a nested
record. The m49 fixture's source is therefore **FLAT** (branch-per-column, e.g.
`Jet_pt`/`Jet_eta`/`Muon_pt`), and the shift's extra column is a distinct top-level field
(`Jet_eta`). A nested `Jet.eta` example is not expressible through this verb; buffer-level
projection is not what §5.3 binds."

---

### 4. MID — the per-label restatement §5.3/§10 offers as the "immune" alternative is itself red against §5.3's own SORTED return

**Section:** §5.3 r22 (`systematics-vary-plan.md:1638-1639`) and §10/m49 (`:4460-4461`), both
spelling `stats[jes_up] == stats[nominal] + ("Jet.eta",)`.

**Detail.** §5.3 and §9.1 both bind the verb's value to "that label's **SORTED** read set"
(`{label: tuple[str, ...] | None}`), and the underlying `read_columns` returns
`tuple(sorted(needed))` (measured, `python/graphed/projection.py:147`). Tuple **concatenation**
appends the extra column at the end, so the offered assertion holds only when the extra column sorts
last. On the very fixture the fix to finding #3 requires, it does not:

```
stats["nominal"] == ('Jet_pt',)                      # measured
stats["jes_up"]  == ('Jet_eta', 'Jet_pt')            # measured — sorted, extra column FIRST
stats["nominal"] + ("Jet_eta",) == ('Jet_pt','Jet_eta')   # != stats["jes_up"]
```

Since r22 introduced this spelling explicitly as the form "immune to the interaction" — i.e. the one
a test-author is steered toward when the conservative-label interaction bites — a suite built from
it freezes an assertion no correct implementation can pass, and the only exits are a Test Dispute or
weakening §5.3's sortedness.

**Suggested fix.** Replace both occurrences with an order-insensitive difference over the sorted
tuples: `set(stats["jes_up"]) - set(stats["nominal"]) == {"Jet_eta"}` **and**
`set(stats["nominal"]) - set(stats["jes_up"]) == set()` (the second conjunct keeps it from
degenerating to a containment test), or equivalently
`stats["jes_up"] == tuple(sorted(stats["nominal"] + ("Jet_eta",)))`. Note in the same sentence that
plain concatenation is wrong because the returns are sorted.

---

### 5. MID — §6.4e's r26 "SORTED list" of selection levels has no defined total order; the natural implementation raises, and the two m51 anchors that consume it have no well-defined predicate

**Section:** §6.4e r26 (`systematics-vary-plan.md:2752-2760`); consumed by m51's manifest anchor
(`:4906-4915`) and m51's manifest-determinism anchor (`:4899-4905`).

**Detail.** r26 correctly closed an unwritable-as-stated gap (the levels entry had no serialized
shape) and bound: "the entry is a **SORTED list whose elements are either an integer depth or a
two-element `[field_path, depth]` array**". The element space is heterogeneous by construction
(§6.4a r22/r24: a bare depth `k` for level 0 and for the record's own structure, a `(field path,
depth)` pair otherwise), and nothing defines an order across the two element kinds. Measured, the
obvious implementation is an error, not a choice:

```
sorted([0, ["Jet", 1]])  ->  TypeError: '<' not supported between instances of 'list' and 'int'
json.dumps({"levels": [0, ["Jet", 1]]}, sort_keys=True)  ->  {"levels": [0, ["Jet", 1]]}
```

(`sort_keys=True` sorts *mapping keys*; it does not touch a list's element order, so
`canonical_bytes`-style serialization gives no help either.) The consequence for the frozen suite is
concrete: m51's manifest-determinism anchor says "minimally, the serialized key order is asserted
sorted", and for this entry "sorted" names no computable predicate — the test-author must invent
one and freeze it read-only, which is the exact defect class r15/r16 repaired for §2.5's diagnostics
channel and §5.3's stats verb, and which r26 opened this clause to repair.

**Suggested fix.** Bind the total order explicitly in §6.4e, e.g.: "ordered by the key
`(depth, field_path or "")` — bare-depth entries sort before field-scoped entries of the same depth,
field-scoped entries by `_`-flattened field path — so the list is a pure function of the supplied
`select=` keys and the manifest bytes are `PYTHONHASHSEED`-independent. `sorted()` over the raw
mixed elements is a `TypeError` (measured, CPython 3.12); the sort key above is what an
implementation applies." Then word m51's determinism anchor over that key.

---

### 6. MID — §9.2's bound `FORMAT_VERSION` bump is witnessed by no m50 anchor and is invisible to every anchor that exists

**Section:** §9.2 r26 (`systematics-vary-plan.md:3358-3373`, the bump at `:3372`); m50's §9.2 anchor
(`:4714-4716`).

**Detail.** r26 bound the varied bundle's manifest label channel (correctly — measured,
`python/graphed/preserve/bundle.py:184-193` writes `"outputs": {"value": …, "weight": …}` and
`reproduce` ends `return values[out["value"]]` at `:250-252`, so labels have nowhere to live) and
added: "`FORMAT_VERSION` (today `1`, `manifest.py:17`) **bumps with it**, and an UNVARIED bundle
keeps today's singular shape and version." I verified `FORMAT_VERSION = 1` at
`python/graphed/preserve/manifest.py:17` and that `canonical_bytes` is `json.dumps(..., sort_keys=True)`
at `:20-22`.

m50's §9.2 anchor asserts only the per-label `reproduce` round-trip, the unvaried backward-compat
control (a bare array), and `inspect()`'s label listing. All three are green against an
implementation that adds the label map and **never bumps the version** — the label map is exercised
behaviourally either way. This is the invisible-violation shape the plan itself repairs three times
(r13 for §8.2(i)'s `frozenset`, r14 for manifest determinism, r25 for §6.4e's levels entry): a
binding requirement whose violation no frozen test can see, and which is not on the plan's list of
knowingly-UNANCHORED rules (§6.1d's reindex ordering, §6.4e's no-private-import, §7.2's compile
count, §1.1's `"1e1000000000"`, §6.2(3)'s no-`boost_histogram`-import).

It also matters downstream: `fingerprint` is the SHA-256 of `canonical_bytes(manifest)`
(`manifest.py:26-...`), so the version field is part of the bundle's content hash — an unbumped
varied bundle is indistinguishable by version from a v1 bundle a v1 reader would mis-parse.

**Suggested fix.** Either add one clause to m50's §9.2 anchor — "and the varied bundle's manifest
carries `format_version == <the bumped value>` while the unvaried control still carries `1`" (two
assertions, both cheap, both on fixtures the anchor already builds) — or, if the owner prefers not
to spend the assertion, mark the bump knowingly UNANCHORED in §9.2 with the plan's standard sentence
and the reason.

---

### 7. LOW — m51's manifest anchor asserts the levels entry against a **set**, while §6.4e binds a sorted **list** of ints and pairs; the two are different frozen assertions

**Section:** m51 manifest anchor (`systematics-vary-plan.md:4906-4915`, "one assertion that the
levels entry's value **equals the set of levels** the fixture supplied through `select=`") vs
§6.4e r26 (`:2758-2760`, "the entry is a **SORTED list** whose elements are either an integer depth
or a two-element `[field_path, depth]` array").

**Detail.** For the object-migration coverage item the fixture supplies `{0: event_mask,
("Jet", 1): jet_mask}`, so the anchor's "set of levels" is `{0, ("Jet", 1)}` while the bound
on-disk value is the JSON list `[0, ["Jet", 1]]`. A test-author writing the anchor literally
compares a Python set against a list read back from parquet KV metadata — a type mismatch that
fails for a reason unrelated to the requirement, and one that pushes them to guess a normalization.
This is the same wording-vs-shape mismatch r25 fixed one clause earlier for the same anchor's
key-set half ("a literally spelled expected KEY SET", replacing "lists exactly the appended
labels/columns/representations").

**Suggested fix.** Re-word the anchor over the bound serialized shape, once finding #5 fixes the
order: "…and the levels entry equals the **literally spelled expected list** — `[0, ["Jet", 1]]`
for the object-migration item, `[0]` for the weight-only one — in §6.4e's bound order."

---

## Verdict

**DIRTY** for this lens — 3 HIGH, 3 MID, 1 LOW.

The HIGHs are all of the same species and all newly introduced or newly sharpened in r25/r26: an
anchor whose *spelling* cannot do the discriminating work the surrounding prose assigns it
(finding 1), a bound producer recipe that cannot produce what the same milestone's anchors freeze
(finding 2), and a bound assertion that is red against a correct implementation on the fixture shape
the plan's own evidence steers the test-author to (finding 3). None of them touches an owner-locked
decision and none requires re-opening a design choice — each is repairable by adding the missing
mechanism sentence in the style the plan already uses everywhere else ("stated here to spare the
mid-freeze discovery"). Findings 4–7 are cheap sweeps in the same paragraphs.

Everything else in this lens is clean, and notably so: the R0.10a discipline, the determinism-gate
anchor forms, the literal-key-set repairs (§6.3, §7.2, §6.4e, §2.3d floors), the per-repo anchor
partition with its `importorskip`-is-a-silent-skip reasoning, the sibling-vs-axis-mode scoping of
every m48 anchor m50 must extend, and the freeze-order sweep over the e-form grammar all hold up
against the pinned roots. I found no surviving r8-era anchor wording, no new instance of the
equal-counts or self-derived-delta traps beyond finding 1, and no orphan anchor.
