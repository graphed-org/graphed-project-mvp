# systematics-vary-plan — r14 revision notes (review round 5 audit trail)

Input: three independent reviews of r13 (`systematics-vary-plan-review-r13-{facts,design,tests}.md`),
33 findings (NITs excluded), 29 after cross-lens merge — 0 BLOCKER, 7 HIGH, 12 MID, 10 LOW.

Every finding was re-verified in this session against the pinned verification roots
(`/private/tmp/claude-501/{graphed-latest@ff7c607, graphed-exec-check@201ea42,
graphed-histogram-latest@211cbbe}`) plus live probes (awkward 2.12.0, numpy, boost_histogram 1.8.0,
cloudpickle 3.1.2, a clean `uv` resolve giving pyarrow 25.0.1) before any edit was made. Nothing was
rejected; nothing was deferred; no finding's resolution touched an owner-locked decision, so no
"OPEN ITEMS (owner)" block was added.

Merges: the §2.3d discovery-rule defect was raised by all three lenses (facts / design / tests) and
is one edit; the m48 single-refusal-contract defect was raised by design + tests; the
`§3.3`-benchmark directory contradiction (design, LOW) is folded into the tests lens's broader m49
partition finding (MID).

---

## HIGH

### 1. FACTS — `graphed.evaluate_ir` cannot receive a `Varied` (§2.3d + m48 anchor) — APPLIED
**Verified.** `python/graphed/execute.py:85-91`:
`def evaluate_ir(compiled: CompiledGraph | bytes, backend: Backend, sources: Mapping[str, object], *,
externals: Mapping[str, Callable[..., object]] | None = None) -> list[object]:` — no `Array`
parameter, no `arr.node_id`/`arr.session` read. The two cited anchors belong to the other two verbs
(`execute.py:70` `ids = [arr.node_id for arr in outputs]` inside `compile_ir`; `aggregate.py:86`
`session = outputs[0].session` inside `aggregate_plan`) — both re-read and correct.
**Edit:** §2.3d drops `evaluate_ir` from the refusing set and states it is outside the
`Array`-consuming surface (anchor `execute.py:85-91`); the m48 table anchor states explicitly that
`evaluate_ir` is NOT in the table and why the plain-`Array` positive control is false for it in the
other direction too. New Anchors row.

### 2. FACTS + DESIGN + TESTS (merged) — the `Array`-FIRST discovery rule (§2.3d + m48 anchor) — APPLIED
**Verified** by reading each signature in `graphed-latest`: DISCOVERED by an `Array`-first filter —
`repartition` `shuffle.py:68`, `pack_key` `:84`, `join` `:92`, `shuffle_plan` `:142`, `join_plan`
`:208`. MISSED — `compile_ir(session: Session, *outputs: Any)` `execute.py:54`,
`evaluate_ir(compiled: CompiledGraph | bytes, …)` `:85`,
`read_columns(arrays: Sequence[Array], source_nid: int)` `projection.py:109`,
`apply(fn: Callable[..., object], *arrays: Array)` `array.py:397`; `aggregate_plan(*outputs: Array)`
`aggregate.py:68` is VAR_POSITIONAL and ambiguous. `graphed.awkward.to_parquet(array: Any, …)`
`awkward/io.py:206` is not in `graphed.__all__` at all. The over-fire is real too:
`graphed.broadcast_like(value, factor) -> Array` is introduced by §6.1d in m48 and had no §2.3d
disposition, so a literal "every discovered verb carries a disposition" gate would go red against a
correct implementation.
**Edit:** §2.3d re-binds the filter to callables ANY of whose parameter annotations mentions `Array`
(incl. `Sequence[Array]`, unions, `*args: Array`) plus the named non-`__all__` members, withdraws
"the table cannot silently miss a verb", adds a disposition for `graphed.broadcast_like`
(broadcast, §2.4 label-aligned), and binds §2.3a/c's non-vacuity floor (non-empty, ≥ freeze-time
count, ≥ one member of each disposition class). m48's anchor bullet updated to match. New Anchors row.

### 3. DESIGN + TESTS (merged) — m48 freezes ONE refusal contract for two bound contracts — APPLIED
**Verified.** §2.3d binds `join`/`repartition`/`pack_key`/`shuffle_plan`/`join_plan` to "the §5.4
error" and §5.4 binds that to a `NotImplementedError` naming the label and the boundary, while
`compile_ir`/`aggregate_plan` get an error naming `graphed.universe`. Measured,
`python/graphed/errors.py` — `class GraphedError(Exception)`, `class GraphedTypeError(GraphedError)`
— has no relation to `NotImplementedError`, so the two contracts are not simultaneously satisfiable.
Freeze-order also matters: §5.4 is an m49 target and the same m48 bullet already defers refusing-class
behaviour to m49.
**Edit:** the m48 anchor is split by contract — boundary/plan verbs assert only that they refuse and
do not silently compile (the §5.4 message shape is frozen in m49); compile/aggregate verbs assert the
`graphed.universe` error with the plain-`Array` positive control. New Anchors row for the
`GraphedError` fact.

### 4. DESIGN — context-handle ORIGINATION unbound (§2.3e) — APPLIED
**Verified.** `python/graphed/session.py:133-140` — `source(self, name, *, form, data, **params)`
receives no `Array` and no context; `:142-168` — `record_op` merges only from `inputs` and returns a
fresh wrapper per call. With merge-from-inputs only, `events2 = graphed.vary(events, "pu", …,
is_weight=True)` wraps the same root record, so `events2.Jet` is a field op over an input carrying
the ROOT context's handle, and §6.1d then applies the pre-`vary` ambient registry. `grep -n handle`
over the plan confirmed no origination/stamping rule existed.
**Edit:** §2.3e gains a binding ORIGINATION clause — a context stamps its own handle on its root
wrapper and on every read performed through it, overriding the input merge; the merge rule governs
only ops whose inputs already carry handles. m48 gains the discriminating anchor (same read through
a derived context and its parent → same node id, different handles, different fill label sets).
New Anchors row.

### 5. DESIGN — r13's sibling-mode rescoping of the `.plan()` refusal opens a crash (§6.1c) — APPLIED
**Verified.** `graphed-histogram src/graphed_histogram/boost.py:245-255` — `Histogram.plan` passes
`_SumFills(self._spec)` and `_ZeroHist(self._spec)`; `:146-150` — `self._spec = spec_of(self)` in
`__init__`. Under §6.2's fill-time axis declaration the fill results carry the variation axis and
`self._spec` does not. Probe, boost_histogram 1.8.0:
`bh.Histogram(Regular(3,0,1)) + bh.Histogram(Regular(3,0,1), StrCategory(['nominal','jes_up']))` →
`ValueError: axes have different length`. §6.1c's per-slot spec repair is scoped to `_GroupReduce`'s
layout and does not reach `_SumFills`/`_ZeroHist`.
**Edit:** option (a) of the suggested fix — the refusal is restored to GENERAL (any varied
`Histogram`), in §6.1c's body and in the m48 anchor, with the measured reason recorded. Nothing in
m50's anchors needs `Histogram.plan` on an axis-mode histogram. New Anchors row.

### 6. TESTS — §5.2(a)'s sharing witness is satisfiable without calling `graphed.vary` — APPLIED
**Verified.** `tests/frozen/core/m4/test_benchmark.py:1-20` and `tests/frozen/core/m4/
test_systematics.py` both `import graphed.core as gc` and build via `add_source`/`add_op` — no
frontend. §3.3 tells the author to replicate that file, and §5.2a pins its integers "on the §3.3
topology", so the witness can be built entirely on `GraphStore::intern` (already frozen at m1/m4).
`Session.node_count()` exists (`python/graphed/session.py:50-51`), so a frontend-built delta IS
buildable.
**Edit:** §5.2a binds the delta to `Session.node_count()` before/after adding the SECOND label
through the public `graphed.vary` surface, states that the raw-`GraphStore` construction belongs to
§3.3's benchmark only, and requires the expected integer to be re-measured through the frontend at
freeze (`K + 2 = 52` is the raw-builder number and is explicitly not assumed to carry over).
New Anchors row for `Session.node_count`.

### 7. TESTS — m49(ii)'s fixture edit installs the wrong `graphed-histogram`; no no-`importorskip` clause — APPLIED
**Verified in-session.** `curl pypi.org/pypi/graphed-histogram/json` → name `graphed-histogram`,
version `0.0.1`, homepage `github.com/graphed-org/graphed-histogram`; the repo's own
`pyproject.toml` version is also `0.0.1`, so the PyPI release is not distinguishable by version.
`graphed-executors .github/workflows/ci.yml:13,15,17` carries `GRAPHED` + `CORPUS` git URLs only,
installed at `:38`, `:65`, `:94`, `:136`; the frozen suite runs at `:44`, `:67`, `:101`, `:153`.
Anchor (i) and m48's matrix carry a "MUST NOT be `importorskip`-guarded" clause; (ii) did not.
**Edit:** m49(ii) binds the dev-extra name PLUS a `HISTOGRAM` git-URL workflow env var and its
`pip install` line in every job that runs `tests/frozen`, and adds the no-`importorskip` clause.
New Anchors row.

---

## MID

### 8. DESIGN — §6.4a level-0 lineage parenthetical inverts the direction — APPLIED
**Verified** against the plan's own text: §9.1 defines `graphed.selection(ctx)` as the mask that
derived `ctx` from its PARENT (`None` for a root context), so for the canonical spelling
`to_parquet(events.Jet, select=graphed.selection(sel))` with `sel = events[mask]` the record's own
context is the root `events` and `graphed.selection(events)` is `None` — the parenthetical demanded
`select=None`. The m51 anchor's wording already had the correct direction.
**Edit:** the parenthetical is inverted — the supplied mask must be `graphed.selection(c)` for a
context `c` whose PARENT is the record's own context handle; the m51 wording is named normative.

### 9. DESIGN — level-0 row-count equality had no raiser and no site — APPLIED
**Verified**: §6.4a bound it inside the record-time clause while the section's own "offsets are data"
argument (and `_WritePart`'s per-partition evaluation, `awkward/io.py:111-127`) makes a row count
execution-time.
**Edit:** level 0 is split into (2a) lineage — record-time, raised from the `to_parquet` call — and
(2b) row-count equality — execution-time, per partition, from `_WritePart` before any buffer is
stored. The "where each runs" summary, the binding paragraph, the "do NOT freeze a record-time
raise" instruction and the m51 anchor are all updated.

### 10. DESIGN — §6.4c's XOR/`packbits` had no computation site — APPLIED
**Verified by probe** (awkward 2.12.0 / numpy): `float32 ^ float32` → `TypeError: ufunc
'bitwise_xor' not supported for the input types` for BOTH `np.ndarray` and `ak.Array`;
`a.view(np.uint32) ^ b.view(np.uint32)` works. `grep -c "^def " python/graphed/awkward/functions.py`
→ 73 with no `view`/`packbits`/`frombuffer` (`values_astype` `:673` is a value cast).
**Edit:** §6.4c binds the per-label VALUES and masks as the extra marked outputs and the
XOR/`packbits` encoding as `_WritePart`-side work on evaluated buffers; §6.4f is corrected to match
and to require the read-list widening to cover them; §11 parks an in-IR bit-view verb.
New Anchors row.

### 11. DESIGN — `graphed.read_varied` in the neutral namespace — APPLIED
**Verified.** `graphed pyproject.toml:27` — `dependencies = ["executing>=2.0", "cloudpickle"]`;
awkward/pyarrow only in extras `:29-46`; both parquet entry points live in `graphed.awkward`
(`python/graphed/awkward/__init__.py:14,30`).
**Edit:** respelled `graphed.awkward.read_varied(path)`, with the ROOT-side equivalent in the uproot
fork, and §6.4f's numpy exemption made symmetric (no numpy-idiom `read_varied`). New Anchors row.

### 12. DESIGN — `bh.loc` inside `graphed` proper (§6.2(i-bis)) — APPLIED
**Verified.** Same dependency fact as above (boost-histogram is only in `graphed`'s `dev` extra).
Probe, boost_histogram 1.8.0: `h[{1: ax.index('jes_up')}].values()` equals
`h[{1: bh.loc('jes_up')}].values()`; `hasattr(h, "axes")` is a usable duck-type discriminator.
**Edit:** §6.2(i-bis) gains clause (3) — duck-typed detection on `.axes`, position from
`axis.__dict__["name"]`, slice by `axis.index(label)`; no `boost_histogram` import in `graphed`
proper. New Anchors row.

### 13. DESIGN — §2.2's "SUPERSET of any §6.1d fill's label set" is false — APPLIED
**Verified** against the plan: §6.1d's fill label set unions value-borne labels, ambient labels AND
explicit `weight=[…]` factor labels; §2.1(a)'s loose `graphed.vary` stays public (§2.6 close), so
`h.fill(sel.Jet.pt, weight=[loose_varied])` and a loose vary on a context-read value both exceed the
union §2.2 defines.
**Edit:** the superset property is scoped to the CONTEXT-BORNE half, with both counterexamples named.
The union rule itself (what the m48 anchor freezes) is unchanged.

### 14. DESIGN — `graphed.universe`/`nominal` on a CONTEXT had no bound return type — APPLIED
**Verified**: §2.2 bound the verbs to accept a context but never said what the answer IS, and §6.1d's
unification is defined over lineage, so `h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)` was
undecidable.
**Edit:** §2.2 binds the result to be a CHILD context in the §2.6b lineage chain, carrying that
label's collections and ambient weight, with `graphed.selection(...)` equal to the argument's
selection at that label; the m48 anchor asserts the ancestry relation.

### 15. TESTS — the §6.4e sorted-manifest rule has no m51 anchor — APPLIED
**Verified**: every m51 manifest anchor is content-only, and the one byte-identity anchor is
explicitly the manifest-FREE unvaried write.
**Edit:** m51 gains a manifest-determinism anchor (two fresh processes, differing `PYTHONHASHSEED`,
byte-identical manifest bytes; minimally, sorted key order asserted), mirroring the m49 plan-byte
anchor r13 added for the same hazard.

### 16. TESTS (+ DESIGN, merged) — m49's anchor-to-repo partition is incomplete and self-contradictory — APPLIED
**Verified.** §10's header pins the §3.3 benchmark to `tests/frozen/core/m49` and §3.3 agrees, while
m49's paragraph listed it under `tests/frozen/frontend/m49` (different pytest process, different
basename rule). Unassigned anchors: §2.4/§6.1b arity (needs
`graphed_histogram.Histogram.staged_fills`/`fill_nodes`, `boost.py:215-219`, and `graphed` lists no
`graphed-histogram` in any extra); §7.3/§7.4 (machinery is `graphed`'s checkpoint package, whose
frozen tree holds only `checkpoint/m8` and `checkpoint/m39`); §8.1/§8.2 anchors (no repo named).
`graphed` CAN host a spawn-based cross-process test (`tests/frozen/debug/m6/
test_process_boundary.py:16`).
**Edit:** m49's partition now covers every anchor — §3.3 pinned to `core/m49` in both places, arity
to `graphed-histogram`'s `tests/frozen/m49`, a NEW `graphed tests/frozen/checkpoint/m49` for
§7.3/§7.4, and the §8.x anchors named per repo (with the §8.2(i) accessor anchor staying in
`graphed`).

### 17. TESTS — the unique-basename rule stops at `graphed` — APPLIED
**Verified.** `graphed-histogram`: `pytest tests/frozen` in one process (`ci.yml:44,67`),
`pythonpath = ["src","tests/frozen/m23"]` (`pyproject.toml:50`), zero `__init__.py` under `tests`,
existing `tests/frozen/{m23,m29}`. `graphed-executors`: same shape (`ci.yml:44,67`,
`pyproject.toml:54`, zero `__init__.py`, 15 existing milestone directories — I counted 15, not the
17 the finding stated, and used the measured number). `graphed`'s `checkpoint` subtree is not a
`SPLIT_PKG` (`scripts/run-tests.sh:16-25,30`) and already holds `checkpoint/m8/test_resume.py`.
**Edit:** §10 generalizes the rule to every new frozen directory in every repo this plan touches,
with the same cross-directory `pythonpath` clause. New Anchors row.

### 18. TESTS — §3.4 lands in m48 with no m48 frozen anchor — APPLIED
**Verified**: m48's target line said "§3.2/§3.4 (API only)" while §3.4 and m49's target line both
place the frozen anchor in m49, and §4.3's impact-set cross-check is explicitly optional ("MAY ride
along") — so new m48 source would carry zero m48 frozen-suite diff coverage, which the DoD gate
excludes `tests/extra` from.
**Edit:** §3.4 removed from m48's targets (it remains an m49 target with its m49 anchor); the reason
is recorded inline.

### 19. TESTS — the `graphed.labels(ctx)` anchor exercises two of three union terms — APPLIED
**Verified** against §2.2's r13 union and the m48 anchor's "registers a weight BEFORE the derivation"
program, in which the varied-collection labels are a subset of the mask's labels.
**Edit:** the anchor gains the discriminating second program — a shift-varied collection with an
UNVARIED derivation mask — asserting the collection's labels are still reported and the (now scoped)
superset property still holds.

---

## LOW

### 20. FACTS — §8.2(i)'s sha256 triple is not reproducible — APPLIED
**Verified by re-running**: cloudpickle 3.1.2, payload
`(3, frozenset({"btag_down","btag_up","jes_down","jes_up","nominal"}))`, `PYTHONHASHSEED` 1/7/12345 →
sha256[:16] `b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831` — three distinct digests
(the substantive claim holds) but none matching r13's, whose payload and cloudpickle version were
unnamed. The downstream chain re-verified: `OpSpec.identity()` `core/plan.py:72-77` →
`DurablePlan.task_id` `:164-176`.
**Edit:** §8.2(i) and the Anchors row now carry the named payload + toolchain and my measured
digests; r13's triple is explicitly withdrawn.

### 21. FACTS — the `#[pymethods]` enumeration is incomplete — APPLIED
**Verified**: `grep -n "#\[pymethods\]" src/lib.rs` → `:102`, `:159`, `:470` (three blocks:
`PayloadDescriptor`, `GraphStore`, `IncrementalReducer`); the `GraphStore` impl closes at `:416`.
The conclusion the claim supports (no record→reduced id map is exposed) is unaffected and true.
**Edit:** §8.2 and the Anchors row restate the enumeration over the three blocks with the correct
spans.

### 22. FACTS — pyarrow version stated inconsistently — APPLIED
**Verified by a clean resolve** (`uv run --no-project --with "awkward>=2.12" --with pyarrow`):
awkward 2.12.0 / pyarrow 25.0.1; in that environment the §6.4e content reproduces for the
list-of-float case (different bytes; KV `{ARROW:schema, awkward_array_metadata}` vs
`{ARROW:schema}`; `"metadata" in signature(ak.to_parquet)` → `False`;
`created_by == "parquet-cpp-arrow version 25.0.1"`).
**Edit:** the two r13-dated probe statements (§6.4e and its Anchors row) are corrected to 25.0.1 and
note the re-verification; the r7-era dotted-name probes (§1.1/§6.4b, taken under 25.0.0) are left
attributed as measured, with that explicitly stated so the two are no longer silently inconsistent.

### 23. DESIGN — §2.6d's "structural, not a convention" over-claims — APPLIED
**Verified** from the plan: the loose primitive stays public and §6.1d's union carries its labels
into the fill.
**Edit:** scoped to "structural for every context-borne registration", naming what would be required
to make it structural outright (a fill-time refusal on data-context handles), which v1 does not bind.

### 24. DESIGN — "loose inputs adopt the unified context" has no re-indexing path — APPLIED
**Verified** from the plan: re-indexing is bound for ancestor-CONTEXT values via the intervening
masks; a loose value has no handle and no known mask.
**Edit:** §6.1d binds adoption to LABEL ALIGNMENT only (row space not adjusted) and requires the
execution-time refusal message to name the offending VALUE when the offender is a loose value —
not "the offending factor" / "pass the value unflattened".

### 25. DESIGN + TESTS — the §3.3 benchmark's directory — APPLIED (folded into #16).

### 26. DESIGN — m48's split says "except its dedup half" then assigns half of it to `graphed` — APPLIED
**Verified**: the two statements are four lines apart and both bind a test-author.
**Edit:** re-worded to "except the RESULT-MAPPING half of its dedup clause".

### 27. TESTS — m48's §4.3 bullet still reaches for "the §7.2 map" — APPLIED
**Verified**: §4.3 (r13) obtains per-label fill nodes through §9.1's new accessor precisely because
§7.2 binds only ownership; the §10 bullet was not updated.
**Edit:** the bullet points at §9.1's per-label fill-node accessor by name.

### 28. TESTS — §5.2(c) names no program and no expected value — APPLIED
**Verified**: every sibling witness names both; on the §3.3 topology the shape is already pinned as
`stages == N + 1` (§3.3's own re-measured numbers: N=16 → 17, N=128 → 129).
**Edit:** §5.2c is bound to the §3.3 topology with that literal and folded into the §3.3 fixture as
one assertion.

### 29. TESTS — m50's scaling anchor points at a mapping keyed by output name — APPLIED
**Verified**: `graphed-histogram src/graphed_histogram/boost.py:255-292` —
`layout = tuple((label, len(h._fill_nodes), h._spec) for label, h in items)` where `items` are
`(output_name, Histogram)` pairs; consumed at `:100-117`. The 1-vs-`N+1` count only holds under
§6.1c's two-level key shape.
**Edit:** the anchor is worded over the per-partition combine payload under §6.1c's two-level
`(output, label)` key shape, with the fixture's output count pinned at 1. New Anchors row.

### 30. TESTS — §8.2's multi-label rendering anchor never reaches §10's m49 list — APPLIED
**Verified**: §8.2 states it inline as required; §10's m49 bullet carried only the single-label
anchor.
**Edit:** the clause is mirrored into §10's m49 bullet.

---

## Rejected

None. Every finding reproduced against the verification roots.

## Deferred (owner-locked)

None. No resolution required reversing an owner-locked decision (naming, functional surface, e-form
canonical tags, context attachment, record-time expansion + interning, m48–m51 scope incl. §6.4,
JER-SF non-ordering, the Phase-2 pull-in), so no "OPEN ITEMS (owner)" block was added to the header.

## Deviations from suggested fixes

- **#5 (§6.1c)**: the finding offered two options; option (a) (keep the refusal general) is taken —
  it is the smaller diff, matches §6.1c's own body sentence, and nothing in m50's anchors needs
  `Histogram.plan` on an axis-mode histogram. Option (b) would have required a second spec-plumbing
  target in m50.
- **#7 / #17**: the finding cited `graphed-executors ci.yml:38,:67,:101` as install lines; measured,
  the install lines are `:38`, `:65`, `:94`, `:136` and the frozen-suite runs are `:44`, `:67`,
  `:101`, `:153`. The plan records the measured numbers. The finding's "17 milestone dirs" is 15 as
  measured; the plan records 15.
- **#6 (§5.2a)**: the finding suggested re-measuring Δ through the frontend now. That measurement
  needs the unimplemented `graphed.vary`, so the plan binds the mechanism (`Session.node_count()`
  around the second label) and requires the literal to be measured at freeze rather than inventing a
  number.
