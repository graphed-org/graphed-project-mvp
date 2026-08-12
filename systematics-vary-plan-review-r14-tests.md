# `systematics-vary-plan.md` review — round 6, **TEST ARCHITECTURE** lens

- **Plan revision reviewed:** r14 (2837 lines, read in full: Part I rationale, PART II §§1–12, §10 milestones m48–m51, Anchors appendix, revision history).
- **Date:** 2026-07-30
- **Reviewer context:** isolated agent, fresh context. Every claim below rests on a file I read or a command I ran in this session.
- **Verification roots used** (never the stale submodules in the workdir):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, verified `git log -1` → `ff7c607`) — including its built `.venv` (`graphed` importable, awkward 2.12.0), used for live probes.
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`)
  - `/private/tmp/claude-501/graphed-exec-check` (`graphed-executors`, `201ea42`)
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md` (R0.10 `:196-202`, R0.10a `:203-215`, R0.11 `:216-`)
- **Owner-locked decisions** (naming, functional surface, e-form canonical tags, context attachment, record-time expansion + interning, m48–m51 scope incl. §6.4, JER-SF non-ordering, the Phase-2 pull-in) were treated as fixed; nothing below asks for a different choice.
- The plan header carries no `OPEN ITEMS (owner)` block, so nothing was excluded on that ground.

**Verdict up front: DIRTY — 4 HIGH, 7 MID, 4 LOW, 0 BLOCKER.** The suite skeleton is in far better shape than the finding count suggests: every trap the earlier rounds named (equal-counts tautology, self-derived delta, wall-clock gates, freeze-order over-scoping, `importorskip`-skippable headline gates) is closed, and the r9 e-form switch is coherent everywhere I checked. The HIGHs are all *new* instances of the same two classes the plan itself hunts: a witness bound to a surface that cannot observe the mechanism (§5.2a, §5.2c), and a gate whose bound mechanism passes tautologically (§2.3a parity, §2.3d discovery).

---

## HIGH

### H1 — §5.2a: the bound arena-delta measurement span cannot observe `K + 2`, and the literal it pins is unobtainable at freeze

**Section:** §5.2(a) (plan `:865-884`), m49 anchor list (`:2092`).

**Detail.** r14 correctly moved this witness off the raw `GraphStore` surface, but the replacement binds a *span* that the plan's own architecture excludes: “the arena delta is read as `Session.node_count()` **before/after adding the SECOND label through `graphed.vary`** … on the §3.3 shape”. Under the chosen architecture (Part I §3: “the frontend **re-records the downstream ops** per variation”), the `graphed.vary(...)` call itself only introduces the fork member; the `K = 50` chain ops and the terminating reduction that make up `K + 2 = 52` are recorded **after** the call, when the user applies the downstream chain to the `Varied`. Bracketing the `vary` call therefore measures Δ ∈ {0, 1}, not 52 — a test-author following the sentence literally freezes a wrong integer or (worse) an integer that a semantic stub also produces.

Second half: “The expected integer is **re-measured through the frontend at freeze** and travels with that fixture”. Under the gated pipeline the test-author writes and freezes the suite **before any implementation exists** (§12.1; root `CLAUDE.md` Part B), so there is no frontend `vary` to measure through. The one number the plan does supply (52) is explicitly disclaimed (“MUST NOT be assumed to carry over unchecked”), leaving the author with no obtainable literal.

**Evidence.**
- Plan `:878-882` (the binding sentence quoted above); Part I §3 `:158-160` (“The frontend re-records the downstream ops per variation”); §3.3 `:762-766` (per-universe suffix = 1 fork + K chain + 1 reduction).
- `Session.node_count()` exists and is a pure arena read: `/private/tmp/claude-501/graphed-latest/python/graphed/session.py:50-51`.
- Measured in-session (that repo's `.venv`): recording ops through the frontend grows the arena one node per recorded op (`n0=1` source → `src.x * 2.0` → `n1=3`), i.e. the chain nodes appear at *chain-recording* time, not at container-construction time.

**Suggested fix.** Bind the span and the oracle explicitly, both obtainable pre-implementation:
1. *Span*: “build the complete N=1 program, read `Session.node_count()`; build the complete N=2 program **in the same Session** (nominal re-records for free by interning), read again; the delta is the second universe's suffix.”
2. *Oracle*: “the expected literal is obtained by hand-building the second universe **without `vary`** (the same K chain ops + reduction on a forked input) in a separate Session and reading its own delta” — an independent construction, not a self-derived `len(cone)`, and writable at freeze.

---

### H2 — §2.3a: the public-surface parity gate is vacuous as bound (`Varied`'s field-access `__getattr__` answers every name)

**Section:** §2.3(a) (`:439-458`), m48 anchor “§2.3 **public-surface** parity” (`:1892-1913`).

**Detail.** The gate is bound as “a frozen test **iterating the inventory** enumerated dynamically from `type(graphed.nominal(v))`”, with a non-vacuity floor that constrains only the *discovered set* (“non-empty, at least the freeze-time count, names `__array_ufunc__`, `__getitem__`, a bitwise dunder and at least one public METHOD”). Nothing binds **what is asserted per name**. Because `Varied` implements field access by mapping over labels — mirroring `Array.__getattr__`, which records a `field` op for **any** non-underscore name — `hasattr(varied, "filter")`, `hasattr(varied, "sum")`, `hasattr(varied, "argsort")` are all `True` on a `Varied` that broadcasts **zero** methods. A presence-based iteration is therefore green against exactly the failure mode §2.3a itself names three lines earlier (“an unimplemented one does not raise cleanly: `Varied`'s label-mapping field access turns `varied.filter` into a recorded `field` op”).

The METHOD half — the half r12 added, and the half the floor makes mandatory — is precisely the vacuous half: dunders are safe (implicit dunder lookup and `hasattr("__and__")` both fall through the leading-underscore guard and raise), while the ~29 public methods (`filter`/`map`/`reduce`/`repartition` plus the numpy idiom's ~25) all resolve as field ops. Worse for the *refusing* disposition: `varied.repartition` resolves to a `Varied`, and calling it raises `TypeError: 'Varied' object is not callable` — which a loosely written `pytest.raises` refusal check would accept as “it refused”.

**Evidence.**
- `python/graphed/array.py:332-335` (read in-session): `def __getattr__(self, name): if name.startswith("_"): raise AttributeError(name); return self._session.record_op("field", [self], {"field": name})`.
- `python/graphed/array.py:374-391` (`filter`/`map`/`reduce`/`repartition` are real methods, so they are in the inventory the gate enumerates).
- Plan `:449-453` (the plan's own statement of the failure mode) and `:454-458` (the floor, which constrains discovery only).

**Suggested fix.** Bind the assertion, not just the enumeration: for each discovered name, resolve it **on the class** (`getattr(type(varied), name, None)` — a class lookup is not intercepted by the instance `__getattr__`) and require a real attribute; plus one behavioural probe per disposition class in the same test (one broadcast method returning a `Varied` whose `graphed.labels` match, and `repartition` raising the §5.4 refusal rather than `TypeError: not callable`). Same treatment for §2.3e's `Array`-surface propagation gate, which inherits the identical hole.

---

### H3 — §2.3d / m48: the r14 discovery rule provably still misses `compile_ir`, and the anchor is “driven by” that rule

**Section:** §2.3(d) (`:492-541`), m48 anchor “§2.3d module-verb dispositions” (`:1831-1856`), Anchors row `:2429`.

**Detail.** r14 withdrew the r13 `Array`-**first**-parameter filter because it “provably MISSES four of the verbs disposed above: `compile_ir` …, `evaluate_ir` …, `read_columns` … and `apply` …”, and replaced it with “callables **any of whose parameter annotations MENTIONS `Array`**”. Measured, the new rule **still misses `compile_ir`**, whose parameters are annotated `Session` and `Any` — no annotation mentions `Array`. Since `compile_ir` *is* in `graphed.__all__`, it is not rescued by the “plus the named non-`__all__` members” clause either. The m48 anchor says the table-driven test is “**driven by** the §2.3d discovery rule”, so a literal implementation of the anchor contains no row for `compile_ir` — dropping the frozen coverage of one of the two safety-bearing dispositions (the one whose absence, per §2.2/§2.3d, otherwise lets a duck-typed read compile a `field` op into a plan).

**Evidence.** Run in-session against `graphed-latest@ff7c607` (its `.venv`), implementing the bound rule verbatim:

```
$ python -c "enumerate graphed.__all__, keep callables with any param annotation containing 'Array'"
aggregate_plan  apply  join  join_plan  pack_key  read_columns  repartition  shuffle_plan
total 8
```

`compile_ir` is absent. Source: `python/graphed/execute.py:54-58` — `def compile_ir(session: Session, *outputs: Any, optimize: bool = True, maximal_fusion: bool = False) -> CompiledGraph`. (`read_columns` and `apply` *are* discovered, so the r14 widening did fix three of the four; `evaluate_ir` is correctly out of scope per r14.)

**Suggested fix.** Either (a) state the rule as “discovered ∪ an explicitly enumerated freeze-time floor list that **includes `compile_ir`**”, and have the gate assert the floor list is a subset of the disposition table; or (b) additionally match callables whose annotations mention `Any` *and* which are named in §2.3d, and drop the implication that the filter is drift-proof for `compile_ir` (that phrasing should be withdrawn the way “cannot silently miss a verb” already was).

---

### H4 — §5.2c: the reduced-stage witness is bound to the raw-`GraphStore` topology (witnesses nothing about `vary`), and is assigned to two different files

**Section:** §5.2(c) (`:888-893`), §10/m49 per-repo partition (`:2032-2039`), m49 anchor list (`:2092`).

**Detail.** Two defects in one anchor.

1. *Surface.* r14 fixed §5.2a by binding it to the public `graphed.vary` surface, with the stated reason that §3.3's builder is raw `GraphStore` so “a `vary` implementation that re-recorded the shared prefix per universe would still pass … the R0.10 semantic-stub shape”. §5.2c was left as “on the §3.3 topology, with its literal … **It rides the §3.3 fixture**”. §3.3's fixture is measurably a raw-`GraphStore` construction (it is bound to replicate `tests/frozen/core/m4/test_benchmark.py`, which builds with `import graphed.core as gc` / `add_source` / `add_op`). So §5.2c — a section titled “**Witnesses that sharing engaged**” — asserts `stages == N + 1` over a graph built without ever calling `vary`, re-asserting the M4 frozen contract and witnessing nothing about the feature under test. This is the identical hole r14 closed for (a), left open for (c).
2. *Location.* §5.2c says it “is one assertion in **that file**” (the §3.3 benchmark, which §10 pins to `graphed`'s `tests/frozen/core/m49`), while §10/m49's per-repo partition assigns “§5.2c stage shape” to `tests/frozen/frontend/m49`. Those are different directories in **different pytest process scopes** (`core` runs as one process; `frontend` runs per-milestone — `scripts/run-tests.sh:16-25`, `SPLIT_PKGS="frontend numpy awkward"` at `:30`). “Which anchor is frozen where” is exactly the gap §10 spends two paragraphs closing.

**Evidence.** Plan `:888-893`, `:2036-2039`, `:757-770`. `tests/frozen/core/m4/test_benchmark.py:11-25` (read in-session: `import graphed.core as gc`, `gc.GraphStore()`, `add_source`/`add_op`). `scripts/run-tests.sh:16-25,30` (read in-session).

**Suggested fix.** Bind §5.2c the same way as §5.2a: assert `stages == N + 1` on a **frontend, `vary`-built** N-universe program (the same fixture §5.2a needs), placed in `tests/frozen/frontend/m49`, and say so in both §5.2 and §10. Leave the raw-`GraphStore` `stages == N+1` / `reduced == 2N+2` assertions where they are — in the §3.3 benchmark in `core/m49` — as the *scaling* pins they are, not as mechanism witnesses.

---

## MID

### M1 — §5.2a's stated discriminator is unachievable by any arena-delta form (interning makes prefix re-recording free)

**Section:** §5.2(a) (`:873-878`).

**Detail.** The r14 rationale for moving the witness to the frontend is that on the raw builder “a `vary` implementation that re-recorded the shared prefix per universe would still pass”. Moving to the frontend does not fix that: re-recording the shared prefix **through the same `Session`** interns to the *same* node ids and adds **zero** nodes, so the arena delta is identical for a sharing implementation and a re-recording one. The witness genuinely discriminates other things (a per-universe store, a label leaking into `NodeKey` params — which would fork identity and blow the delta up), but not the failure the plan names.

**Evidence.** Measured in-session (`graphed-latest/.venv`): recording `src.x * 2.0` twice in one `Session` returns the **same** node id (`2` both times) and leaves `node_count()` unchanged (`3` → `3`). Interning lookup: `src/store.rs:73-88` (the plan's own anchor).

**Suggested fix.** Restate what the delta discriminates (no per-universe copy enters the arena ⇒ labels are out of node identity and interning is engaged through `vary`) and point the “re-recording” concern at the witness that actually catches it — §5.2b's single-read `part_reads == n_partitions`, which a per-variation re-run loop cannot pass.

### M2 — §10/m49's “covers EVERY m49 anchor” partition leaves two anchors unassigned

**Section:** §10/m49 (`:2032-2049`), anchors at `:2077-2091`.

**Detail.** r14 added “**The per-repo partition covers EVERY m49 anchor**, not only (i) and (ii)” and then enumerates: `frontend/m49` (§5.2a, §5.2c, §3.4, §5.3, §5.4), `core/m49` (§3.3), `graphed-histogram m49` (matrix (i) + arity), `checkpoint/m49` (§7.3, §7.4), `graphed-executors m49` (matrix (ii), §8.1, §8.2), plus §8.2(i) in `graphed`. The **m05 ordering witness** and the **JER-SF stochastic fixture** — two of m49's named anchors — appear in neither list. Placement is not cosmetic here: the plan establishes twice (m48 fixture analysis `:1735-1750`, m49(i) `:2022-2031`) that a fill-based anchor placed in `graphed` `importorskip`-SKIPs in CI, and the JER fixture's partition-invariance witness needs a plan run at two `steps_per_file` values.

**Suggested fix.** Assign both explicitly, with the same reasoning as the others (if their observables are histograms → `graphed-histogram tests/frozen/m49`; if selection counts / masks materialized through `Session.materialize` → `graphed tests/frozen/frontend/m49`).

### M3 — the JER partition-invariance witness's “byte-identical” is not a safe invariant for aggregated float results

**Section:** §5.5(a) (`:915-921`), m49 anchor (`:2085-2091`).

**Detail.** The anchor freezes “the identical event set run at two different `steps_per_file` values yields **byte-identical** per-label results”. `steps_per_file` is a plan parameter, so the compared object is a plan result. If that result is a **weighted** histogram (which the m49 matrix's are), the assertion is not implied by content-seeded randomness: changing the partitioning changes the grouping of float additions in the combine tree, so a *correct* implementation can differ in the last ulp. The plan itself concedes the effect in the m48 matrix bullet (“`bin_values`' driver-side rounding is what absorbs the **float-summation-order differences a per-partition fill introduces**”), and the house precedent measures it: the m29 frozen suite asserts `array_equal` only **run-to-run at fixed partitioning** and drops to `allclose(rtol=1e-12)` against the eager reference. The existing exact partition-count-invariance precedent (`checkpoint/m8`) works because its result is an **int64** histogram.

**Evidence.** `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:75-79` (read in-session — comment: “per-partition fills sum in tree order: deterministic (byte-identical across runs), and equal to the single-pass eager fill **up to float-summation order**”; `:77` `array_equal` run-to-run, `:78-79` `allclose(rtol=1e-12)` vs eager). `graphed tests/frozen/checkpoint/m8/test_resume.py:51-58` + `analyses.py:29-30` (`np.histogram(...).astype(np.int64)`).

**Suggested fix.** Bind the compared quantity: per-event/per-object smeared **values** and per-label selection **masks** (or an unweighted integer-storage count histogram), which are partition-local and concatenate deterministically — not a weighted float histogram.

### M4 — §2.5's unreached-label diagnostic names no channel, and its m48 anchor is therefore unwritable as stated

**Section:** §2.5 (`:636-638`), m48 anchor (`:1879-1882`).

**Detail.** The requirement is “`compile_ir` **diagnostics** report any registered label that reaches no marked output”, and the anchor asserts presence/absence of that report. Measured, `compile_ir` returns a frozen `CompiledGraph` dataclass carrying **only** `ir: bytes` and `source_names: tuple[str, ...]` — there is no diagnostics channel, and the plan (unlike every other new surface here: `graphed.broadcast_like`, `fill_nodes_by_label`, `read_varied`, the §6.2 opt-in spelling, the data-context flag) carries **no “spelling pinned at m48 freeze”** clause for it. The test-author must invent both the channel *and* its shape (returned field? `warnings.warn`? a separate `graphed.diagnostics(session)`?), and a wrong guess is frozen. The companion mechanism — “`vary()` registers each container with its Session (weak reference)” — is likewise unbound.

**Evidence.** `python/graphed/execute.py:36-45` (read in-session: `@dataclass(frozen=True) class CompiledGraph: ir: bytes; source_names: tuple[str, ...]`).

**Suggested fix.** Name the channel (an additive `CompiledGraph` field or a separate read-only accessor) and add the standard “exact spelling pinned at m48 freeze” clause; note the interaction with the m48 §7.2 schema-absence anchor if the field lands on `CompiledGraph`.

### M5 — §6.3's “no-variation paths unchanged” golden is under-determined against §6.1d's unconditional broadcast seam

**Section:** §6.3 (`:1189-1192`), §6.1d (`:1024-1052`), m48 anchor (`:1891`).

**Detail.** §6.3 gates “data / no-variation paths are unchanged” with a **committed golden GIR blob** for an unvaried fill graph. For that gate to have content the blob must be captured from the **pre-m48** revision; the plan never says so, and captured post-implementation it is a no-op. Worse, §6.1d binds “**Every** weight factor the fill applies — the ambient one AND explicit `weight=[...]` factors — is broadcast to the fill's value structure” via a *recorded* `graphed.broadcast_like` node, with no scoping to varied/contexted fills. Under a literal reading, an ordinary unvaried `h.fill(x, weight=[w])` gains a broadcast node and its IR bytes change — which makes the m48 golden either red against a correct implementation (frozen ⇒ Test Dispute) or silently reduced to a tautology.

**Suggested fix.** Bind both halves in §6.3: (1) the golden is captured from the pre-m48 revision of the fill graph; (2) a fill with **no** context handle and **no** `Varied` input records byte-identically to today — i.e. the broadcast seam is inserted only on the varied/ambient path.

### M6 — no bound public accessor for an `Array`'s context handle, while the anchors that need it are frozen in another repo

**Section:** §2.3(e) (`:542-581`), §6.1(d) (`:988-1016`), m48 split (`:1715-1735`).

**Detail.** §6.1d requires `Histogram.fill` to “read its input Arrays' **context handle**”, unify along ancestry, and raise the divergence error. `Histogram.fill` lives in `graphed-histogram`; the handle is bound as “**one added slot, underscore-prefixed** (e.g. `_context`)” on `graphed`'s `Array`. No §9.1 entry exposes an `Array → context` read (the §9.1 list is `labels`/`universe`/`nominal`/`weight`/`variations`/`selection` — all context-*taking*). So the m48 anchors assigned to `graphed-histogram` (ambient fill, divergence at the fill, the re-indexing comparison) are implementable only by reaching across a package boundary into a private slot, and the plan's “spelling pinned at freeze” discipline has nothing to pin.

**Suggested fix.** Bind a read-only public seam (`graphed.context_of(array) -> Context | None`-shaped, spelling pinned at m48 freeze) and give it a §2.3d disposition — note it would then be *discovered* by the m48 exhaustiveness gate, which is the desired anti-drift property.

### M7 — the §2.3e propagation gate's exemption guard does not constrain class membership

**Section:** §2.3(e) (`:604-614`), m48 anchor (`:1899-1913`).

**Detail.** The gate enumerates only the *broadcast*, *container-traversing* and *tuple-returning* classes, takes its call arguments “from **fixtures that live in `src`** beside the classification”, and its integrity guard is “the gate asserts the exemption set is **exactly those two classes**”. That guard constrains the set of exempt *class names*, not their *membership*: an implementer who cannot make `gak.where` (or `concatenate`, `unflatten`, …) propagate the handle can re-classify it as *eager-metadata* in `src`, keep the exemption set exactly `{eager-metadata, refusing}`, and stay green — while the classification and its fixtures are both implementer-editable production code. Only the four representatives named in m48's per-class behaviour bullet (`zip`, `unzip`, `fields`, `type_of`) are pinned against this.

**Suggested fix.** Add a membership floor to the same test: the *refusing* class is exactly the bound boundary set; every *eager-metadata* member's return annotation is non-`Array`; and the count of *broadcast*-classified functions is ≥ the freeze-time count.

---

## LOW

### L1 — §8.2(i)'s m49 accessor anchor requires a DCE-eliminated record id that its bound fixture does not contain

**Section:** m49 anchor (`:2104-2110`). The anchor is worded “over the **§3.3 builder topology**” and asserts, inter alia, “a DCE-eliminated record id maps to `None`”. §3.3's builder marks **every** universe's terminating reduction as an output (`:762-765`), so nothing in that topology is dead. **Fix:** say the fixture extends the §3.3 shape with one deliberately unmarked branch (and note that the accessor's key space is `compile_ir`'s, while §3.3's builder is raw `GraphStore` — name which construction the anchor uses).

### L2 — §6.1d's loose-VALUE refusal message is binding but unanchored

**Section:** §6.1d (`:1017-1024`), m48 anchor (`:1936-1946`). r14 bound a *distinct* message for the loose-value case (“its message names **that value** — not ‘the offending factor' and not ‘pass the value unflattened', both of which are the wrong diagnosis there”), but m48's anchor freezes only the ambient-weight and explicit-factor messages. An implementation emitting the anchored message for the loose-value case passes every anchor while violating the sentence. **Fix:** add the loose-value case to the same execution-time refusal anchor.

### L3 — m48's §4.1 correctionlib anchor is a bare title with no bound assertion

**Section:** m48 anchor (`:1930`): “§4.1 correctionlib single-payload multi-parameterization.” Every neighbouring anchor states its observable; this one does not, and the property it stands for is precise and checkable. **Fix:** state it — all labels' `External` nodes share one `PayloadDescriptor.content_hash` while differing only in the `systematic=` param (the `preserve/m9/agc.py:38-66` fixture shape).

### L4 — §2.3c's discovery target `gak` is ambiguous between the package and the module, and one reading discovers nothing

**Section:** §2.3(c) (`:475-487`). The rule is `inspect.getmembers(gak, inspect.isfunction)` filtered to `__module__ == gak.__name__`. Measured in-session: under `import graphed.awkward as gak` (the package) the filter discovers **0** functions; under `graphed.awkward.functions` it discovers **65**. The codebase's own alias resolves the ambiguity (`python/graphed/awkward/__init__.py:12`, `from . import functions as gak`) and the bound non-vacuity floor would catch the empty case at freeze — so this is a readability fix, not a hole. **Fix:** name `graphed.awkward.functions` explicitly in the rule.

---

## Checked and clean (this lens)

- **(c) R0.10a — no wall-clock or size thresholds in frozen tests.** Verified across all four milestones: the only frozen wall-clock gate is §3.3's `time(128)/time(16) < 24.0`, which the plan names as a deliberate, argued carve-out discharging the project plan's M4 mandate, with the frozen precedent (`tests/frozen/core/m4/test_benchmark.py:34-42`, read in-session) and measured headroom (≈5.4 vs 24.0). Every other performance claim — §6.2's N≈100 sibling-vs-axis comparison, §6.2's allocation count, §6.4c's compression ratio, m51's skim sizes — is explicitly demoted to R0.11 implementer-report measurement with a structural frozen invariant left in its place. §3.3 does **not** replicate m4's absolute `elapsed < 1.0` budget. Clean.
- **(a) the two named historical traps.** The §4.3 equal-counts tautology is replaced by a genuinely discriminating structural predicate (per-label `reachable(fill_node[L]) ∩ reachable(selection_mask)` identical and equal to `reachable(selection_mask)`; under interning, identical ids ⟺ identical content, so a selection that depended on the weight label would fork ids and fail). The §5.2a self-derived `delta == len(cone)` trap is closed, and m51's superset anchor is correctly re-based on an **eager, plain-awkward, outside-graphed** reference (`:2194-2201`). §6.2's over-declaration hole is closed with a literally spelled expected label list rather than a circular read-back.
- **(d) determinism-gate compatibility.** §3.2's m48 anchor is in the strong R22.3 form (fresh processes, differing `PYTHONHASHSEED`); m49 adds the plan-byte twin with the `frozenset`→sorted-tuple defect measured and closed; m51 adds the manifest-determinism anchor that makes §6.4e's sorted-key rule observable; §6.4g correctly refuses a committed `.parquet` blob (writer version in the footer) in favour of a same-process comparison, while keeping committed byte oracles for GIR. §5.5's content-seeded randomness is the right shape.
- **(e) freeze-order hazards.** I hunted specifically for r8-era (p-form) survivals after the r9 e-form switch: none. m48's grammar anchor, §6.4b's on-disk shape (`__vary_murf_5em1__Jet_pt`), m51's numeric-tag round-trip label and §9.1/m50's dual e-form+p-form parser are mutually consistent. The sibling-vs-axis scoping is now consistent in all three places that need it (§6.1a, §6.1b/m49 arity, §1.2/m48), and r14's restoration of the `.plan()` refusal to GENERAL is measurably correct (`Histogram.plan` passes the `__init__`-time `self._spec` — `graphed-histogram src/graphed_histogram/boost.py:245-255,146-150`, read in-session — which under fill-time axis declaration cannot combine with the fill results). m48's split of the refusal table by contract (`NotImplementedError` vs `GraphedError`, with the §5.4 message shape deferred to m49) removes a guaranteed Test Dispute.
- **(f) traceability.** I walked every binding PART II clause against the m48–m51 anchor lists. Coverage is otherwise complete; the orphans I found are M2 (two m49 anchors unassigned to a repo), M4, M6 and L2. No orphan anchors — every anchor traces to a §.
- **(g) testability of the corpus fixtures.** Verified the m48/m49 matrix is buildable: the corpus analysis is plain eager awkward (`tests/_corpus/graphed_corpus/analyses/systematics.py`, read in full), and every op it uses has a gak counterpart (`with_field`, `num`, `sum`, `prod`, `firsts`, `drop_none`, `full_like` — enumerated in-session from `python/graphed/awkward/functions.py`, 73 defs / 65 public, matching the plan). `gak.full_like` exists at `functions.py:612-616` as cited. The plan's `rint(x * 1e6) / 1e6` spelling for the corpus's `stable()` rounding is exactly what `np.round(x, 6)` does, so the pre-fill rounding is reproducible; its cited lines (`systematics.py:79,102,50`) are correct. The vendoring binding for `graphed-histogram` and the git-URL install pair for `graphed-executors` are both grounded in the real CI shapes I read (`graphed-executors .github/workflows/ci.yml:14-17,36-39`; `graphed-histogram .github/workflows/ci.yml:36-44`), and both headline matrices carry the no-`importorskip` clause. §10's unique-basename rule is well-founded (`scripts/run-tests.sh:16-25,30`; `pythonpath` exports `tests/frozen/checkpoint/m8`, so a new `checkpoint/m49/analyses.py` would indeed collide).
- **§7.3's interrupt/resume anchor** is R0.10a-safe by precedent: the house mechanism is a deterministic `_SimulatedInterrupt` + `_kill_after=N` fault injection, not timing (`tests/frozen/checkpoint/m8/test_resume.py:27-45`, read in-session).

---

## Verdict

**DIRTY.** 0 BLOCKER / 4 HIGH / 7 MID / 4 LOW. None of the findings requires reversing an owner-locked decision, and none is structural: H1/H4 are one paragraph each (bind the span and the surface), H2/H3 are one clause each (bind the assertion; add a floor list including `compile_ir`). The plan's acceptance skeleton is otherwise the strongest I have reviewed in this series — R0.10a is respected with a single argued carve-out, every previously named tautology is closed, and the per-repo fixture analysis is measured rather than assumed. Fixing H1–H4 and M1–M7 should be a mechanical r15 pass; the LOWs are one-liners.
