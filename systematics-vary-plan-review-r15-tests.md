# systematics-vary-plan — review round 7, TEST ARCHITECTURE lens

- **Lens:** test architecture (non-vacuity/discrimination, R0.10 mechanism witness, R0.10a
  determinism, determinism-gate compatibility, freeze-order hazards, traceability, testability
  as stated).
- **Plan revision reviewed:** r15 (`systematics-vary-plan.md`, 3171 lines, read in full including
  Part I, every PART II section, §10 milestones, the Anchors appendix and the revision history).
- **Date:** 2026-07-30.
- **Verification roots used** (every code fact below was measured in-session against these, never
  against the stale submodules in `/Users/lgray/vibe-coding/graphed-workdir`):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, ff7c607) — including its
    `.venv` for runtime probes
  - `/private/tmp/claude-501/graphed-histogram-latest` (211cbbe)
  - `/private/tmp/claude-501/graphed-corpus-latest` (49650e4)
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md` (R0.10 / R0.10a / R0.11 text
    re-read at `:196-225`)

Owner-locked decisions were treated as fixed; nothing below asks for a different choice, only for
internally consistent specification of the choices already made. Nothing below re-raises an item
already listed in the plan's own header.

**Clean areas, stated explicitly so the absence of findings is not read as absence of review:**

- **R0.10a compliance is clean.** I re-checked every frozen anchor in §10 for wall-clock and size
  thresholds. The only wall-clock gate is §3.3's `time(128)/time(16) < 24.0`, which the plan names
  as a deliberate carve-out; the precedent it replicates is real — `tests/frozen/core/m4/
  test_benchmark.py:38-43` (`base = max(times[SIZES[0]], 1e-4)`, `assert growth < 24.0`), and
  `_time_reduce` is best-of-3 at `:27-32`. §6.4c compression and §6.2's N≈100 comparison are both
  explicitly demoted to R0.11 implementer-report measurements; m50's scaling anchor is structural
  (slot count), and the r13 removal of the allocation-count half was the right call.
- **The §3.3 / §5.2a / §5.2c pinned integers are correct.** Re-measured against `graphed-latest`
  with D=500, K=50: N=16 → `stages` 17 / `reduced_nodes` 34; N=128 → 129 / 258; and
  `node_count()` delta for the complete N=1 → complete N=2 program = **52** (553 → 605). The r15
  SPAN/ORACLE re-binding of §5.2a is sound: bracketing the `vary` call really cannot observe
  `K+2` under record-time expansion, and the independently hand-built second universe is a genuine
  oracle rather than the self-derived `delta == len(cone)` comparison review r0 named.
- **Determinism-gate compatibility is clean.** The `frozenset` → sorted-tuple fix (§8.2(i)), the
  sorted manifest keys (§6.4e) with m51's new manifest-determinism anchor, m48's fresh-process
  differing-`PYTHONHASHSEED` IR anchor and m49's plan-byte twin all line up. I also checked the
  one place where a float-summation-order hazard could have bitten a byte-identity claim that r15
  did *not* narrow — m49's §7.3 interrupt/resume anchor — and it is safe: `_reduce_partials` folds
  the partials in **sorted task-key order** (`python/graphed/checkpoint/runner.py:151-158`), so a
  resumed run reproduces the uninterrupted combine order exactly, float storage or not.
- **§2.3c's discovery rule is measured-correct.** Under the bound rule
  (`inspect.getmembers(..., inspect.isfunction)` filtered to `__module__ ==
  "graphed.awkward.functions"`), `graphed.awkward.functions` yields **65** public functions and the
  package alias `graphed.awkward` yields **0** — both re-measured this session. The r15 correction
  to name the module rather than the alias is right.
- **§4.3's operand extraction is buildable as described.** `Session.walk`
  (`python/graphed/session.py:245-286`) takes caller-supplied `source`/`op`/`external` handlers, so
  a reachability set can be computed without evaluating any data; it does take an `Array`, and the
  `Array(session, nid)` note is the right service to the test-author. (The *predicate* it feeds is
  a separate matter — finding 1.)

---

## Findings

### 1. HIGH — §4.3 / m48: the bound selection-invariance predicate is satisfied by construction (a new tautology in the slot where r0 removed the old one)

**Section:** §4.3 (`:892-922`) and the m48 anchor that "quotes it verbatim" (`:1996-2005`).

**Detail.** §4.3 binds: "compute `reachable(fill_node[label])` per label via `session.walk`, take
`reachable(selection_mask)` the same way, and assert that its **intersection** with each label's
reachable set is IDENTICAL across labels (and equal to `reachable(selection_mask)` itself)."

For any weight-variation program, the filled value is post-selection —
`h.fill(obs, weight=[...])` with `obs = x[mask]` — and `Histogram.fill` records ONE External node
whose `inputs` are the axis args followed by the weights
(`graphed-histogram src/graphed_histogram/boost.py:176-212`; the frozen m29 test asserts exactly
this input layout, `tests/frozen/m29/test_multi_weight_fills.py:84-86`). Therefore
`reachable(selection_mask) ⊆ reachable(fill_node[L])` **for every L, in every implementation that
fills selected data**. The intersection is consequently a constant equal to
`reachable(selection_mask)`, and both halves of the assertion ("identical across labels", "equal to
`reachable(selection_mask)`") are true by construction. The predicate carries no information about
the property §4.3's own binding sentence states — "the selection cone's node ids MUST be **identical**
across all weight labels" — because a containment test cannot detect a label whose selection cone is
a strict **superset** of nominal's.

**Evidence (verified).** `boost.py:176-178` (`inputs = list(args); inputs.extend(weights)`),
`:205-212` (one `record_external` with those inputs); `session.walk`'s post-order traversal over
`inputs_of` (`python/graphed/session.py:255-286`) makes the cone of a node the transitive closure of
its inputs, so the containment above is structural, not incidental.

**Failure scenario the anchor accepts.** An implementation in which a weight label's universe
*extends* the selection cone — per-label mask `mask_L = mask & g_L` (a per-universe guard, a
per-label re-indexing node landing inside the mask cone under §2.6c, or any per-label refinement) —
violates §4.3's binding sentence, produces per-label divergent selections, and still passes the
anchored predicate, because `reachable(mask) ⊆ reachable(mask_L) ⊆ reachable(fill[L])`. The anchor
only catches the narrower class where a label's mask is rebuilt from a *different* expression that
does not contain nominal's mask.

**Suggested fix.** Freeze the containment's converse, which is directly readable and is literally
the binding sentence: assert that the per-label fill nodes agree on their **non-weight input node
ids** — i.e. for every label, `store.nodes()[fill_id]["inputs"][:n_axes]` equals nominal's (by
interning, identical id ⇒ identical cone). Optionally keep the reachability form as a redundant
check in the stronger shape `reachable(fill[L]) − reachable(weight_input[L]) − {fill[L]}` identical
across labels. Either form fails the `mask & g_L` implementation; the current one does not.

---

### 2. HIGH — m48's §2.3d disposition gate is assigned to a repo that measurably cannot satisfy its own bound floor list

**Section:** §2.3d (`:569-570`, the named floor list) and the m48 anchor at `:2046-2062`
("One table-driven test in `graphed`'s `tests/frozen/frontend/m48`, driven by the §2.3d discovery
rule … **UNION the named floor list `{graphed.compile_ir, graphed.awkward.to_parquet,
graphed_histogram.Histogram.fill}`** …"), plus the non-vacuity floor "contains every member of the
named floor list".

**Detail.** The test is bindingly placed in `graphed`'s frozen tree, and its floor bindingly
requires `graphed_histogram.Histogram.fill`. Measured: `graphed` declares **no**
`graphed-histogram` in any dependency or extra (`graphed pyproject.toml:29-48`; the only occurrence
of the name in the whole file is a mypy `ignore_missing_imports` entry at `:91`), and CI installs
`.[dev]` (`.github/workflows/ci.yml:34`). The house pattern for reaching it from `graphed` is
`pytest.importorskip("graphed_histogram")` — measured at
`tests/frozen/preserve/m25/test_histogram_preservation.py:31` (module level),
`m27/test_variadic_call_templates.py:185,207`, `m30/test_producer_cross_seam.py:155`.

So the m48 test-author has exactly three options, all bad: (a) module-level `importorskip` → the
**entire** table-driven test SKIPs in CI, silently discharging §2.3d's dispositions *and* §2.2's
reserved `node_id`/`session` anchor (which r13 added to the same test) and contributing zero
frozen-suite diff coverage — precisely the failure mode the plan itself forbids twice for the matrix
anchors; (b) drop the member and fail the bound floor assertion; (c) file a Test Dispute before
freeze. This is the same repo-partition analysis the plan performs correctly for the corpus matrix
and for m49(i)/(ii), simply not applied to the floor list r15 introduced.

**Suggested fix.** Split the floor by repo: `graphed`'s gate takes
`{graphed.compile_ir, graphed.awkward.to_parquet}` (both importable there — `awkward` and `pyarrow`
are in the `dev` extra, `pyproject.toml:42-48`), and the `graphed_histogram.Histogram.fill`
disposition is asserted in **`graphed-histogram`'s flat `tests/frozen/m48`**, which already depends
on `graphed` (`graphed-histogram pyproject.toml:21`) and is where every other fill-shaped m48 anchor
already lives per §10.

---

### 3. MID — §6.1d's r15 `sample=` binding has no anchor, and the fold-order anchor it belongs to enumerates only three of the four operand kinds

**Section:** §6.1d (`:1121-1127`, "`sample=` folds LAST, after the explicit factors") vs the m48
anchor at `:2156-2160` ("a fill with varied values in TWO axes plus an ambient weight plus an
explicit `weight=[…]` factor, asserting the bound operand order (axis values in argument order, then
ambient, then explicit factors in list order)").

**Detail.** r15 added `sample=` to the bound fold order *and* documented why it matters — measured,
`fill` type-checks `args` and `weights` but appends `sample` to the same `inputs` list with **no**
check (`graphed-histogram src/graphed_histogram/boost.py:160-178`: `if not all(isinstance(a, Array)
for a in args)`, `if not all(isinstance(w, Array) for w in weights)`, then bare
`if sample is not None: inputs.append(sample)`), so a `Varied` sample falls through into
`record_external` and dies on `.node_id`. The anchor that freezes the fold order was not extended,
and no other m48/m49/m50 anchor mentions `sample`. A new binding requirement with zero frozen
coverage either ships unimplemented behind a green suite or is covered only by `tests/extra`, which
the DoD's ≥90 % diff-coverage-from-the-frozen-suite gate excludes — the exact reasoning r14 used to
move §3.4 out of m48's targets.

**Suggested fix.** Extend the m48 fold-order anchor's program to carry a varied `sample=` as a
fourth operand and assert it folds last; add the type-check half (a `Varied` sample is accepted and
expanded, not an `AttributeError` on `.node_id`).

---

### 4. MID — two m48 clauses that require a `Histogram.fill` are assigned to `graphed`'s half of the split

**Section:** §10 m48's split rule (3) (`:1946-1950`) vs the mega-bullet clauses at `:2209-2224`.

**Detail.** The split enumerates the pure-frontend clauses that "stay in `graphed`" — a list written
in r12 — and the fill-shaped clauses that go to `graphed-histogram`. Two clauses added since then
are fill-dependent but land on the `graphed` side:

- **`graphed.labels` on a Varied-derived context** is named explicitly in the `graphed` list, but
  r14's discriminating second program ends "…and that it remains **a superset of the context-borne
  half of a fill's label set**, §2.2" (`:2217-2219`). Computing a fill's label set requires
  `graphed_histogram`.
- **`graphed.universe(ctx,label)`/`graphed.nominal(ctx)` return a CHILD context** (`:2219-2223`) is
  in neither list (closest match: "lineage" → `graphed`), and r15 strengthened it to be "**asserted
  over the resulting VALUE** … compared elementwise against a manually projected reference" — where
  the value in question is produced by `h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)`.

Both would need `pytest.importorskip("graphed_histogram")` in `graphed` (measured, finding 2), i.e.
they would SKIP in CI.

**Suggested fix.** State the split as a **rule** rather than a frozen enumeration ("any clause whose
assertion requires a fill lives in `graphed-histogram`'s flat `tests/frozen/m48`"), and move these
two clauses' fill-dependent halves there explicitly, leaving the frontend-observable halves
(`graphed.labels(ctx)` reports the shift labels; the ancestry relation itself) in `graphed`.

---

### 5. MID — m49's §8.2(i) accessor anchor: the "shared node" clause has no operand in the topology it is bound to (the same gap r15 just closed for the DCE clause)

**Section:** m49 anchor at `:2358-2369`.

**Detail.** The anchor is bound "over the §3.3 builder topology … EXTENDED with one deliberately
unmarked branch" and asserts three things, the third being "**two labels' shared node maps to ONE
reduced id** — which doubles as the non-vacuity witness for §8.2's keying claim". §3.3's builder is
`source → shared prefix of D ops → per universe {one varied fork op, K chain ops, exactly one
terminating reduction}` (`:831-834`). Every non-prefix node belongs to **exactly one** universe, and
prefix nodes are shared by *all* labels including nominal. There is therefore no node "shared by two
labels" in §3.4's sense ("a node shared by `jes_up` and `jes_down` but not nominal", `:854-856`), and
the clause degenerates to "the map is a function", which it is by type. r15 correctly noticed this
exact shape for the DCE clause ("nothing in that topology is dead and the DCE clause below has no
operand") and fixed it by adding an unmarked branch; the shared-node clause needs the same
treatment.

**Suggested fix.** Extend the anchor's topology the same way it was extended for DCE: add one
derived node consumed by two *non-nominal* universes (§3.4's own anchor already requires such a
fixture — "three labels where two share a derived node", `:2347-2348`), and assert that node's
`variation_labels` entry carries **both** labels, which is the actual non-vacuity witness for the
set-valued keying claim at `:1782-1786`.

---

### 6. MID — §5.3's per-label projection-stats surface is bound and anchored, but never named or pinned

**Section:** §5.3 (`:991-998`) and the m49 anchor at `:2353-2355`.

**Detail.** §5.3 binds "Per-label projection stats are exposed via §3.4 so the read-width cost of a
shift is visible — and that exposure is **anchored in the same m49 test** … the same test asserts
the stats report the shifted label's extra column." But §3.4's API is defined as a *reachability
difference* over node sets (`:851-857`), not read widths, and §5.3 itself concedes "§3.4's own anchor
covers impact sets, not read widths". No name, shape or return type is given for the stats surface,
and — unlike `graphed.context_of`, `graphed.weight`, `graphed.selection`, the per-label fill-node
accessor, the §6.2 opt-in spelling, `graphed.broadcast_like`, `read_varied`, the data-context flag
and the §2.5 diagnostic channel — it carries **no** "spelling pinned at m49 freeze" clause and is
absent from §9.1's introspection list (`:1799-1834`). This is the defect class r15 just fixed for
§2.5 ("the requirement was unwritable as stated … a test-author had to invent both it and its shape
… with a wrong guess frozen read-only").

**Suggested fix.** Either add the stats surface to §9.1 with its spelling pinned at m49 freeze and a
stated shape (e.g. `{label: tuple[str, ...]}` of per-label read columns), or reduce the m49 anchor to
the union-growth assertion and park the stats surface in §11.

---

### 7. MID — §6.4b's on-disk name collision check is vacuous under the convention it is written against, and its worked example is not a collision; m51 freezes it

**Section:** §6.4b (`:1508-1518`) and the m51 anchor at `:2507-2514`.

**Detail.** The bound convention is `__vary_{label}__{field}` with the field path flattened by `_`
per level (`:1505`, `:1512-1513`). The bound check is: "the resulting on-disk name is checked for
COLLISION **against every other stored name** — a collision (a real field literally named `Jet_pt`
alongside the derived name for `Jet.pt`) is REFUSED at m51's entry check, naming both."

Two problems, both frozen by the m51 anchor ("a name COLLISION (a real field literally named
`Jet_pt` alongside the derived name for `Jet.pt`) is refused naming both"):

1. **The named example is not a collision.** The derived name for `Jet.pt` is
   `__vary_{label}__Jet_pt`; the stored user field is `Jet_pt`. These are distinct strings. Under the
   bound prefix, a derived name can collide with a *plain* stored name only if the user has a real
   field literally called `__vary_L__Jet_pt`. So "checked against every other stored name" is very
   nearly a no-op.
2. **The real collision class is derived-vs-derived** and is not the one described: if both
   `Jet.pt` and `Jet_pt` vary, their derived names are both `__vary_L__Jet_pt`. That is a genuine
   corruption and is what the check should catch.

A test-author freezing the sentence as written will most plausibly write the fixture from the
example — a record with a varying `Jet.pt` and a **non-varying** `Jet_pt` — and freeze a refusal for
a program that is perfectly legal under the convention, hard-blocking a legitimate nested-field
skim in read-only tests.

**Suggested fix.** Re-word the check as derived-vs-derived plus derived-vs-stored: "the derived
on-disk names of all augmented columns MUST be pairwise distinct and MUST NOT equal any stored field
name; a collision is refused naming both source fields", and re-write the m51 fixture so **both**
`Jet.pt` and `Jet_pt` vary.

---

### 8. MID — §2.3e's propagation gate takes its call arguments from implementer-owned `src` fixtures, so its core assertion can degrade to `None == None`

**Section:** §2.3e (`:656-673`, binding clause (2)) and the m48 anchor at `:2119-2130`.

**Detail.** r15 closed one half of this hole: because "classification and its fixtures are
implementer-editable `src`", the exempt-set assertion gained a membership floor. The other half is
untouched. Clause (2) binds "…derives its call arguments from **argument fixtures that live in `src`
beside the classification**", while the gate's substance is that the context handle is *preserved*.
If a fixture supplies a **context-free** primary `Array`, both the input handle and the output
handle are `None` and the assertion passes while witnessing nothing — for every function whose
fixture the implementer wrote. The prose "A propagation gate must CALL each function with a
contexted `Array`" states the intent but is in tension with "derives its call arguments from
fixtures", and the frozen test is the artifact that must enforce it.

**Suggested fix.** Bind the split: the **frozen test** constructs the context and owns the contexted
`Array` operand (substituting it into the primary position); `src` fixtures supply only the
auxiliary/typed operands the measured surface needs (`zip`'s mapping, `concatenate`'s second array,
`unflatten`'s counts, `where`'s branches, `linear_fit`'s operands). Add the discriminator: the gate
asserts the returned object's handle **is not None and is** the input's handle, not merely that it
equals it.

---

### 9. MID — §10/m49's placement rationale for the JER-SF fixture points at a partition-blind API, which would make the partition-invariance witness vacuous

**Section:** §10 m49 (`:2298-2301`): "the **JER-SF stochastic fixture** goes there too, since its
partition-invariance witness needs a plan run at two `steps_per_file` values and its comparison
quantities (§5.5a r15) are **materialized through the same Session**."

**Detail.** Measured, `Session.materialize` (`python/graphed/session.py:291-301`) evaluates the whole
graph in one shot through `walk`, reading the source via `self._sources[node_id]` — it takes **no
partition and no `steps_per_file`**. Comparison quantities obtained that way are byte-identical
across any partitioning by construction, so a test-author who takes the sentence literally writes a
witness that cannot observe `steps_per_file` at all — and the failure §5.5(a)/r13 added this witness
to catch (a per-partition `np.random.default_rng(0)`) survives it untouched, together with the other
four witnesses which r13 already showed cannot discriminate it.

r15's narrowing of the compared quantity (smeared values and selection masks, never a weighted float
histogram) is correct and important; the placement sentence undercuts it. Note the mechanism to do
this *properly* does exist and is deterministic: an `aggregate_plan` whose `reduce` returns the
partition-local arrays and whose `combine` concatenates is deterministic under `SequentialRunner`,
which runs and folds tasks in **sorted key order** (`python/graphed/core/execution.py:451-457`).

**Suggested fix.** Replace "materialized through the same Session" with the operative requirement:
the compared quantities are produced by a **plan run** (per-partition values concatenated in task
order) at two different `steps_per_file` values; `Session.materialize` MUST NOT be the oracle,
because it is partition-blind.

---

### 10. LOW — §9.1's plan-level `{output: [labels]}` listing is anchored to a test that cannot exercise it

**Section:** §9.1 (`:1832-1834`): "…and a plan-level listing of `{output: [labels]}` constitute the
introspection surface (RDF `GetVariations` analogue); the listing is frozen-anchored inside m50's
`inspect()` test (§9.2)"; m50's anchor list at `:2451-2453` ("+ `inspect()` label listing (§9.1)").

**Detail.** Measured, `inspect(bundle: Bundle) -> str`
(`python/graphed/preserve/bundle.py:268-288`) renders a **preservation bundle** as a human-readable
string — it takes a bundle, not a plan, and returns text, not a mapping. A string-containment
assertion over a bundle rendering cannot exercise a plan-level `{output: [labels]}` API. The listing
is the only §9.1 member with neither a pinned spelling nor a milestone tag, and as anchored it would
ship uncovered (DoD ≥90 % diff coverage from the frozen suite).

**Suggested fix.** Either give it a milestone, a pinned spelling and its own anchor (natural home:
m50's `graphed` half, `tests/frozen/preserve/m50`, asserting the mapping for a two-output varied
program), or delete it from §9.1 and let `inspect()`'s label listing be the whole claim.

---

### 11. LOW — §5.2b's placement pointer contradicts §10/m49(i)

**Section:** §5.2b (`:974-978`): "…on the SAME Session/plan that reproduces the corpus references
(**the m49 frontend half, §10, where the vendored references live**)".

**Detail.** r12 moved m49's reference matrix out of `graphed` into `graphed-histogram`'s flat
`tests/frozen/m49` (§10 m49(i), `:2260-2275`, which says explicitly "The §5.2b read witness binds to
THIS run"), and r14 assigned `graphed`'s `tests/frozen/frontend/m49` the **non-fill** anchors. The
§5.2b parenthetical still names the frontend half. Since §5.2b is the mechanism witness for §7.1
("no per-variation execution loop"), an author following §5.2b instead of §10 would place it in the
one repo that measurably cannot host a fill-based matrix without skipping (finding 2's evidence).

**Suggested fix.** Change the parenthetical to "the m49 `graphed-histogram` half, §10 m49(i), where
m48's vendored references live", and note the same for m48's matrix.

---

### 12. LOW — §2.3a never states the `inspect.isfunction` enumeration filter that its own reserved-name reasoning presupposes

**Section:** §2.3a (`:459-463`, "enumerated dynamically from `type(graphed.nominal(v))` at test
time … not from a literal list") vs §2.2 (`:440-442`) and the m48 bullet (`:2046-2050`), both of
which assert as fact that "the §2.3a parity gate cannot reach them, since `node_id`/`session` are
plain properties that `inspect.isfunction` does not enumerate".

**Detail.** The filter is stated twice as a *property* of the gate but never bound *in* the gate.
Measured, an unfiltered enumeration is materially different: `dir(Array)` public surface is
`['filter','map','node_id','reduce','repartition','session']`, of which `node_id` and `session` are
non-functions; on the numpy idiom `dir(NumpyArray)` adds `T`, `dtype`, `ndim`, `shape` (32 public
names total). r15's new per-name rule ("each discovered name is resolved ON THE CLASS … and MUST be
a real attribute") applied to an unfiltered enumeration would demand `Varied.node_id`/`.session`
exist, while the reserved-name anchor in the same milestone demands instance access raise
`AttributeError` — reconcilable only by a specific implementation spelling (a raising property), and
it would additionally demand dispositions for `T`/`dtype`/`ndim`/`shape` that §2.3a never assigns.

**Suggested fix.** One clause in §2.3a: enumeration is
`inspect.getmembers(type(graphed.nominal(v)), inspect.isfunction)` plus the dunder set, filtered to
non-underscore names for the method half — the same spelling §2.3c and §2.3d already bind.

---

### 13. LOW — m50's "user-declared variation axis is refused" anchor does not bind the recognition rule, and the natural fixture spelling is a measured `TypeError`

**Section:** m50 anchor at `:2412-2413`: "a user-constructed histogram that already carries a
`"variation"` axis is refused with an error pointing at the opt-in mode".

**Detail.** §6.2(i-bis) establishes that `bh.axis.StrCategory(..., name="variation")` is itself a
`TypeError` (measured on 1.7.2 and 1.8.0, Anchors row at `:2683`) and that the name carrier is
`axis.__dict__["name"]`. So the anchor's fixture cannot construct its subject the obvious way; it
must poke `axis.__dict__` — implementable, but unstated. More importantly the **recognition rule** is
unstated, and the two plausible readings differ materially: name-based recognition (`axis.__dict__
["name"] == "variation"`) is correct, whereas "any `StrCategory` axis" would refuse a perfectly
legitimate user category axis (a `region` axis) and freeze that refusal read-only.

**Suggested fix.** State it: recognition is by `axis.__dict__.get("name") == "variation"`, and the
m50 fixture sets the name that way; a user `StrCategory` under any other name is untouched and the
frontend still appends its own variation axis.

---

## Verdict

**Dirty** — two HIGH findings, seven MID, four LOW; no BLOCKER.

Nothing here would make a milestone unimplementable, and the plan's overall test architecture is in
good shape: the R0.10a discipline is consistently applied with one honestly-named carve-out, every
pinned integer I re-measured is correct, the determinism-gate story now closes (sorted tuple, sorted
manifest, both with anchors), and the freeze-order scoping (sibling vs axis mode, m48 vs m49 refusal
contracts, key sets vs plan bytes) survived a deliberate hunt for r8/r9-era leftovers — I found none.

The two HIGH items are of different kinds and both are worth fixing before freeze. Finding 1 is a
substantive tautology sitting in the slot where review r0 removed the previous one: the anchor the
plan calls the *structural* replacement for the equal-counts tautology is itself true by
construction, and its repair is a two-line change to what the test compares. Finding 2 is a
placement defect of the exact kind this plan has been systematically eliminating for four
revisions — a bound floor list that the assigned repo measurably cannot import, whose most likely
resolution (`importorskip`) silently voids the whole gate.

The MID cluster shares one root cause worth naming: **r13–r15 added binding requirements faster than
they added or re-partitioned the anchors that carry them.** Findings 3, 4, 5, 6 and 8 are all
"requirement strengthened, anchor not updated" or "anchor placed before the clause that made it
fill-dependent". A short sweep with that single question — *for every sentence added since r12, which
§10 bullet freezes it, and in which repo can that bullet actually run?* — would clear most of this
list.
