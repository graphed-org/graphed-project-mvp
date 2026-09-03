# vary-m51 — DECOMPOSE artifact

> **Milestone** m51 — variation-aware write-out (skim augmentation).
> **Plan** `systematics-vary-plan.md` r47 (`8cdf7d4`); m51 surface = §10/m51 (the FROZEN acceptance
> skeleton) and the sections it binds (§6.4a–g, §9.1's `graphed.selection`, §2.3d's `to_parquet`
> table entry, §7.2 node-id resolution, §2.6 context idiom, §1.1 e-form, §6.1d link kinds).
> **Repos and baselines** `graphed` @ HEAD of `main` (the merged m50 tip) · `uproot5-graphed-mvp`
> @ HEAD of its default branch. Probe measurements below are against these working trees.
> **Closed review** `wific067v.output` (session scratchpad): 10 findings, 0 surviving BLOCKER, all
> HIGH downgraded to MED/REFUTED. Cited as context; the design is FROZEN and NOT re-litigated here.
>
> This is the frozen DECOMPOSE artifact the isolated test-authors work from. It fixes trees, briefs,
> commit partition and gates — NOT the implementation.

Work items are labelled `vary-m51-<item>` (root prompt: `<arc>-<milestone>-<item>`).

---

## 0. Scope & boundaries

**What m51 builds.** Variation-aware skim write-out. The **awkward idiom** gains a
`to_parquet(record, select=…)` that materializes the **superset** of rows passing any universe's
selection (level-0 OR), augments the nominal record with per-label reconstruction data (same-dtype
**XOR** value deltas + **packbits** validity masks, computed in the worker on evaluated buffers),
and records a **parquet key-value manifest** (labels → columns → representation + the stored
selection LEVELS) built through the PUBLIC arrow recompose route (`Table.replace_schema_metadata`,
never an `awkward._connect` import). A frontend **`graphed.selection(ctx)`** bridges the §2.6 context
idiom into `select=`; a symmetric **`read_varied(path)`** reconstructs `{label: array}` per universe.
Entry checks decide "the record is pre-selection": **multiplicity** (1), **row-space per level**
(2a lineage record-time, 2b row-count exec-time, 2c depth record-time via typetracer `.tt.ndim`),
bare-key ambiguity, and the §6.4b stored-field row-space refusal. Output resolution is **by node id**
per §7.2, never positional. The **numpy idiom refuses** a varied write. The **ROOT half** (uproot
fork) gains **derived-column IR evaluation only** in `graphed_write`.

**Out of scope — Phase 2 (§11), do NOT scope into m51:**
- variation-aware ROOT write-out/reader (its own manifest channel + delta storage on TBranches);
- multiplicity-changing stored variations (a shift that moves objects across a multiplicity is
  refused, not stored);
- lossy "1+ratio" delta storage (XOR is exact-by-construction; ratio is a Phase-2 opt-in);
- an in-IR bit-view verb (the XOR/packbits are computed in `_WritePart`, not recorded as IR ops).

---

## 1. Baseline — what already ships on merged `main` (do NOT re-assert; vacuous → REJECT at TEST_SANITY)

Measured on the working trees (`wc -l`, `grep`), controls in parentheses.

| Shipped (do not re-prove) | Evidence |
|---|---|
| `graphed.awkward.to_parquet` — deferred write, one parquet part/partition, per-task read list from projection | `python/graphed/awkward/io.py` `to_parquet`; `_WritePart.__call__` does read-partition → `(out,) = evaluate_ir(...)` → `ak.to_parquet(payload, path)` (SINGLE-output unpack today) |
| Read-list computer | `io.py` `_evaluation_columns` (syntactic field walk refined by buffer projection) |
| `graphed.numpy.to_parquet` — 1-D-capped, signature `(array, destination, *, steps_per_file, compute, executor, prefix, column)`, **no `select=`**, absent from the `graphed.numpy` namespace/`__all__` | `python/graphed/numpy/io.py` `to_parquet` |
| Write task-graph builder | `python/graphed/write.py` (`write_plan`, `file_bases`, `blind_part_index`, `part_path`) |
| §9.1 accessors: `context_of`/`weight`/`variations`/`unify_contexts`/`reindex_to`/`labels`/`universe`/`nominal`/`member_of` | `python/graphed/accessors.py`; exported in `python/graphed/__init__.py` `__all__` + disposition map |
| §6.1d link kinds + private lineage walk | `context.py`: `Link = ("mask"|"vary"|"project", payload)`, `_selection()` (skips vary, returns mask, **`None` on a project link**), `_links_below`, `_is_ancestor_of`, `_project`, `_derive` |
| ROOT `graphed_write` copies branches **verbatim**, zero IR eval | fork `src/uproot/writing/_graphed_write.py` `_write_partition`: `record = {name: chunk[name] for name in chunk.fields}` → `uproot.recreate(...)`; `grep -c compile_ir\|evaluate_ir` = 0 (control: `src/uproot/_graphed.py` `graphed_head` = 1, the eval pattern the ROOT half follows) |

**Confirmed ABSENT on merged `main`** (grep, controls in parens):
`graphed.selection` — `hasattr(graphed, "selection")` = False (control: `context_of`, `weight`,
`variations` present); `select=` on either `to_parquet`; any `read_varied`; any XOR/packbits/bit-view
verb in `graphed.awkward`; any `awkward_array_metadata`/`replace_schema_metadata` use in graphed;
`tests/frozen/awkward/m51`, `tests/frozen/numpy/m51`, and the fork's `tests/frozen/` (the fork has
only flat `tests/test_*.py`).

**Measured file sizes** (LOC-estimate calibration): `awkward/io.py` 287 · `write.py` 97 ·
`numpy/io.py` 238 · `accessors.py` 230 · `context.py` 417 · fork `_graphed_write.py` 158 ·
fork `_graphed.py` 383. **m48–m50 commit precedent** (`vary-m50-decomposition.md` §3): graphed src
+573/−72 across 16 files at m49; graphed-histogram +370/−63 (m48), +114/−37 (m49); m50 commits
H1 ~250–400, H2 ~80–150, G1 ~150–300, D1 ~100–200 LOC.

---

## 2. Commit partition

Five graphed commits + one fork commit. CLAUDE.md band: **each commit ≤ 1–2k LOC, one
compartmentalized concern**; a PR is one complete thought (several commits, ≤ ~30k added review
surface). No commit below approaches the band ceiling; the whole graphed side is one PR, the fork
one PR (§5).

### C1 — `graphed.selection` + numpy-idiom refusal (`graphed`)

- **Concern.** The two frontend seams that do NOT need the write machinery: the §2.6→`select=`
  bridge accessor, and the numpy refusal.
- **Files.** `python/graphed/accessors.py` (new `selection`), `python/graphed/context.py` (case-2
  walk), `python/graphed/__init__.py` (export + `"selection": "eager-metadata"` disposition),
  `python/graphed/numpy/io.py` (`to_parquet` guard).
- **What.** `graphed.selection(ctx)` implements §9.1's FULL three-case contract — case-1
  (mask-derived, skipping any number of `vary` identity links) reuses `context._selection()`; **case-2
  (universe/nominal-derived) is NEW** — the private `_selection()` returns `None` on a `project`
  link (measured: `context.py` `_selection` `if kind == "project": return None`), so case-2 adds a
  context method that walks to the projected context's parent, takes the parent's selection `Varied`,
  and returns `member_of(mask, label)` — an unvaried `Array` in the GRANDparent's row space (`None`
  when that parent is root); case-3 (root) returns `None`. numpy refusal: `graphed.numpy.io.to_parquet`
  raises a graphed error naming the awkward backend when the **first positional** is a `Varied`
  (NOT on a `select=` kwarg — none is added; a `select=` call stays a plain `TypeError`).
- **LOC.** ~70–140 (accessors `selection` ~20, context case-2 method ~25, `__init__` export ~4,
  numpy guard ~10; the rest fixtures-adjacent). Far inside band.
- **Depends on / order.** No graphed dependency; **C1 → C2** (C2's 2a lineage check and the bridge
  `select=graphed.selection(sel)` need this verb). numpy refusal is order-free.
- **§10 anchors made pass.** graphed.selection bridge (root-`None`, universe/nominal case-2 half (a));
  numpy-backend refusal (L).

### C2 — `select=` API + record-time entry checks + superset rows (`graphed`)

- **Concern.** The `to_parquet(record, select=…)` entry point, the record-time predicates raised at
  the call, and the level-0 OR that defines the superset.
- **Files.** `python/graphed/awkward/io.py` (`to_parquet` signature + record-time checks + superset),
  `python/graphed/write.py` (plumb the validated `select` mapping + superset into the per-partition
  task graph).
- **What.** `select=` accepts a single `Varied` row mask OR a mapping `{0: mask, ("Jet", 1): mask, …}`
  (§6.4a key space: bare depth `0`/`k` for the record's own axis, `(field, k≥1)` field-scoped).
  Record-time raises at the call: **(2a) lineage** — `graphed.context_of(select_mask)` equals or is
  reachable across `vary` IDENTITY links only from `graphed.context_of(record)` (bare equality, the
  vary-link admission in either direction, the two absent-operand cases, and the §2.3e origination
  positive); **(2c) depth at every supplied level** via `session.form(array).tt.ndim` (NOT
  `_form_meta` — measured: `AwkwardForm` exposes no depth accessor and `_form_meta("depth")` raises
  `GraphedTypeError`; the plan r46 already names `.tt.ndim`); **bare-key ambiguity** (a record jagged
  at depth `k` with ≥2 independently jagged fields refuses a bare `k` key). The **level-0 OR** over
  the per-label masks is recorded as ordinary graph ops (`getitem`/`gak.mask`) and restricts the
  stored rows to the superset. `_WritePart` gains the `select`/superset fields (still a frozen
  picklable dataclass).
- **LOC.** ~220–360 (io.py write-path is 287 today; this adds the checks + superset + signature, the
  densest predicate block). Inside band.
- **Depends on / order.** **C1 → C2 → C3.** C2 produces the validated `select` mapping + superset
  that C3's augmentation and exec-time predicates consume.
- **§10 anchors made pass.** graphed.selection bridge (vary-derived-context; E1/E2 vary-link
  discriminator; re-recorded-mask; universe/nominal half (b) REFUSE); entry-checks record-time half
  (2a lineage + absent-operand + origination; 2c depth + level-≥1 mirror; bare-key ambiguity);
  superset-row anchor (write side); §2.3d table entry (J — accepting behavior first appears here).

### C3 — column augmentation + delta encoding + §7.2 node-id unpack + exec-time checks (`graphed`)

- **Concern.** Everything `_WritePart.__call__` does that is variation-aware: mark the per-label
  values/masks as extra `compile_ir` outputs, resolve them **by node id**, encode deltas, name the
  columns, and raise the execution-time predicates.
- **Files.** `python/graphed/awkward/io.py` (`to_parquet` output marking + `_WritePart.__call__`
  widened unpack/encode + `_evaluation_columns` read-list widening).
- **What.** For every stored field that IS `Varied` structurally (record-time), mark a same-shaped
  per-label VALUE output and per-label MASK output on the SAME `compile_ir` call (variadic); the
  read-list widens at `_evaluation_columns` or projection starves the task. `_WritePart` carries a
  driver-derived **`record node id → output position` table** (§7.2) and unpacks the multi-output
  `evaluate_ir` **by node id, replicating** a shared value into every label that maps to it — the
  single-output `(out,) = evaluate_ir(...)` today becomes the widened unpack; a POSITIONAL unpack
  silently misassigns every label after an all-zero-delta collapse (`mark_output` de-dups on the
  reduced store, so `evaluate_ir` returns FEWER values than marked outputs). Deltas: same-dtype
  **XOR** value deltas + **packbits** mask diffs computed on EVALUATED buffers
  (`ndarray.view(uintN)`), after `evaluate_ir`, before the write — NOT recordable as IR
  (`float32 ^ float32` raises `TypeError`; gak has no bit-view verb, both measured). Names:
  `__vary_{label}__{field}` with the field path `_`-flattened per level; **collision refused in BOTH
  directions** (derived-vs-derived and derived-vs-stored). The **§6.4b stored-field row-space
  refusal** (a `graphed.weight(sel)` for a selection-derived `sel` is refused naming the row-space
  mismatch, not offsets). **§6.4f write-path optimizer-merge refusal** (record-time at the call): the
  §7.2 distinct-outputs-vs-distinct-marked-ids shortfall check with §7.2's message. Exec-time
  predicates raised by `_WritePart` before any buffer is stored: **(1) multiplicity**, **(2b)
  row-count** level-0, **level-≥1 structural** (offsets).
- **LOC.** ~320–500 (the milestone's densest source concern; still inside band). **Band-risk note:**
  if augmentation + the §7.2 unpack + the four refusals + exec-time predicates measure toward the
  upper end during implementation, split at the natural seam **C3a** (marking + §7.2 node-id unpack
  + XOR/packbits encode) / **C3b** (naming + collision + §6.4b row-space refusal + exec-time
  predicates). Not pre-split; flagged.
- **Depends on / order.** **C2 → C3 → C4.**
- **§10 anchors made pass.** bit-exact round-trip (all-zero-delta REPLICATION witness; weight-only
  `graphed.weight(c)` across vary; write-side values); entry-checks exec-time half (multiplicity,
  row-count, level-≥1 structural) + §6.4b row-space refusal; representation (XOR/packbits + names +
  collision); structure refusal (H, §6.4d — the multiplicity mechanism); §6.4f optimizer-merge
  refusal (I); single-read witness (N).

### C4 — parquet-KV manifest + `read_varied` reader (`graphed`)

- **Concern.** Persist the manifest deterministically through the public arrow route and read the
  universes back.
- **Files.** `python/graphed/awkward/io.py` (manifest build + conditional writer swap + `read_varied`).
- **What.** A manifest (`{label: {column: representation}}` + the stored selection LEVELS) travels in
  parquet key-value file metadata. **Conditional writer swap:** an UNVARIED write keeps `ak.to_parquet`
  untouched (§6.4g byte-golden); a VARIED write builds the file `ak.to_parquet` would, re-reads the
  table, merges the manifest via **public** `Table.replace_schema_metadata` + `pq.write_table` (NO
  `awkward._connect` import — the no-private-import half rides code review + integrity scan, optionally
  a one-line `tests/extra` static assertion). Serialization: **mapping keys SORTED**; the LEVELS entry
  is a **list** of `int` or `[field_path, depth]` elements ordered by `(depth, field_path or "")` —
  `sorted()` over the heterogeneous list is a `TypeError` and `json.dumps(sort_keys=True)` never
  reorders a list's elements (both measured), so the order is an explicit key. `read_varied(path)`
  (awkward-idiom, symmetric with the writer) reconstructs `{label: array}` per universe THROUGH the
  manifest (never by parsing stored names).
- **LOC.** ~240–400 (manifest serialize + swap + reader). Inside band.
- **Depends on / order.** **C3 → C4** (the reader inverts C3's representation). Last graphed source
  commit.
- **§10 anchors made pass.** bit-exact round-trip (read-back reconstruction; e-canonical `murf_5em1`
  label verbatim); superset-row anchor (per-universe reconstruction); manifest determinism (F);
  manifest key-set + levels-list + `ak.from_parquet` round-trip + unvaried same-process byte-identity
  (G).

### D1 — docs (`graphed`; ~60–150 LOC)

- **Concern.** The §7.3 checkpoint paragraph gains m51's write-path scope (widening `_WritePart`
  churns no shipped journal — `write_plan` builds a plain-callable `Plan`, the checkpoint runner takes
  a `DurablePlan`; the churn sentence is scoped to a journal a caller built via `OpSpec.from_callable`);
  and a "How variation-aware write-out works" `design.rst` section. **Examples MUST be executed before
  commit** (docs-sweep rule); Sphinx `-W` gate. After C4 (examples run against the finished surface).
- **§10 anchors made pass.** Docs (M).

### R1 — ROOT derived-column IR evaluation (`uproot5-graphed-mvp`)

- **Concern.** `graphed_write` gains derived-column IR evaluation ONLY (§10: "no varied ROOT
  reader/manifest is frozen at m51").
- **Files.** `src/uproot/writing/_graphed_write.py` (`graphed_write` + `_write_partition`); the read
  list already exists (`src/uproot/_graphed.py` `_evaluation_columns`); the eval pattern already
  exists (`_graphed.py` `graphed_head`: `compiled = compile_ir(session, array)`, `(out,) =
  evaluate_ir(compiled, session.backend, {source_name: chunk})`). Plus the fork's first
  `tests/frozen/` harness + its CI collection/cov/mypy gates (config, ride this PR).
- **What.** Today `_write_partition` copies branches verbatim (`record = {name: chunk[name] …}`, zero
  `compile_ir`/`evaluate_ir`). The change: compute the read list via `_evaluation_columns`, `compile_ir`
  the recorded array in `graphed_write`, ship the `compiled` into `_write_partition`, `evaluate_ir` per
  partition, and write the DERIVED record via `uproot.recreate`. Derived-column round-trip = write a
  computed branch, read it back with plain `uproot.open`, compare (no `read_varied`, no manifest).
- **LOC.** ~50–120 source (mirrors `graphed_head`), + modest fork CI/harness config. Far inside band.
- **Depends on / order.** **Independent of C1–C4** — uses only graphed's already-shipped public IR
  API (`compile_ir`/`evaluate_ir`/`Array`/`Session`, all ≥ m10), no m51-new graphed symbol (see §5).
- **§10 anchors made pass.** ROOT half derived-column round-trip (K).

**Whole-PR sizing.** graphed source ~880–1500 across C1–C4 + docs; the frozen suite over the ~14 §10
anchor bullets is m50-scale (~1.5–3k test LOC) → graphed PR ~2.4–4.6k added, one complete thought,
≪ 30k. Fork PR ~0.4–1k added. **Each commit ≪ 1–2k band; the whole fits ONE PR per repo.**

---

## 3. Frozen test trees

Three source-carrying repos-scopes; the graphed side splits by idiom because the **required
awkward-free 3.14t `test-freethreaded` gate** collects `tests/frozen/{core,frontend,numpy}` each
**whole in one process** (`.github/workflows/ci.yml` `test-freethreaded`: `pytest tests/frozen/numpy
--ignore=…/m40`), while `tests/frozen/awkward` is **never** collected whole (awkward wheels lag on
3.14t; `scripts/run-tests.sh` `SPLIT_PKGS="frontend numpy awkward"` runs each awkward milestone dir in
its OWN process, and the freethreaded gate excludes awkward entirely).

| Tree | Widest collecting process | Basename ceiling | Kind |
|---|---|---|---|
| `graphed` `tests/frozen/awkward/m51` **(new)** | `run-tests.sh` per-milestone dir (isolated) | unique **inside the m51 dir only** (helpers still `m51_`-prefixed per m49/m50) | source + tests |
| `graphed` `tests/frozen/numpy/m51` **(new)** | **freethreaded** `pytest tests/frozen/numpy` collects the subtree WHOLE | unique across the **whole `tests/frozen/numpy` subtree** | source + tests (numpy refusal is awkward-free) |
| `uproot5-graphed-mvp` `tests/frozen/m51` **(new; fork's first frozen tree)** | fork `graphed.yml` frozen collection | unique in the new fork frozen tree | source + tests |

**Awkward-free discipline (numpy/m51).** The refusal fixture builds a `Varied` via the numpy idiom /
bare `graphed.Varied` and calls `graphed.numpy.io.to_parquet` — it MUST NOT import `awkward`/`gak`
(the freethreaded gate installs only `pytest hypothesis numpy`). Proposed basename
`test_varied_write_refusal.py` — walked against the 26 live `tests/frozen/numpy` basenames; no
collision.

**awkward/m51 basenames** (fresh dir; within-dir unique; helper `m51_write_fixtures.py`):

| # | §10 anchor | file | commit(s) that satisfy |
|---|---|---|---|
| A | superset-row (independent eager reference; written = union; per-universe reconstructed = eager) | `test_superset_rows.py` | C2 (write union) + C4 (reconstruct) |
| B | bit-exact round-trip — object-migration multi-field `select={0, ("Jet",1)}`; **bare-key** `to_parquet(events.Jet, select={0,1})`; weight-only `graphed.weight(c)` across vary; **all-zero-delta REPLICATION**; e-canonical `murf_5em1` | `test_roundtrip_universes.py` | C2 (select) + C3 (encode/node-id) + C4 (manifest/reader) |
| C | `graphed.selection` bridge (root-`None`; vary-derived-context; E1/E2 vary-link discriminator; re-recorded-mask; universe/nominal (a)) | `test_selection_bridge.py` | C1 (verb) + C2 (2a admission) |
| D | entry checks — (1) multiplicity; (2a) lineage + absent-operand + origination; (2c) depth + level-≥1 mirror; (2b) row-count + level-≥1 structural; bare-key ambiguity; §6.4b row-space refusal | `test_entry_checks.py` | C2 (record-time) + C3 (exec-time + row-space) |
| E | representation — XOR/packbits + identifier names verified via raw schema+manifest; nested `Jet.pt` flatten; collision refused naming both source fields (vary BOTH `Jet.pt` AND flat `Jet_pt`); non-varying `Jet_pt` NOT a collision | `test_representation.py` | C3 (encode/name/collision) + C4 (manifest read) |
| F | manifest determinism (two `PYTHONHASHSEED` processes → byte-identical; sorted mapping keys; levels list `(depth, field_path or "")` order) | `test_manifest_determinism.py` | C4 |
| G | manifest key-set incl. levels entry (literal list in bound order); `ak.from_parquet` round-trip of augmented file; unvaried write keeps `ak.to_parquet`, NO manifest, **same-process** byte-identity | `test_manifest.py` | C4 |
| H | structure refusal (§6.4d: differing per-label offsets refused naming label+field; positive = same-multiplicity object-migration writes+round-trips) | `test_structure_refusal.py` | C3 |
| I | §6.4f write-path optimizer-merge refusal (`w * 1.0` label REFUSED with §7.2 message; unvaried positive) | `test_optmerge_refusal.py` | C3 |
| J | §2.3d table entry (`to_parquet` accepting; `Varied` record and/or `Varied` `select=` consumed internally, no per-label result) | `test_to_parquet_disposition.py` | C2 |
| N | single-read witness on the augmented write run (§5.2b form) | `test_single_read.py` | C3 |

**numpy/m51:** L — numpy-backend refusal → `test_varied_write_refusal.py` (C1).
**fork `tests/frozen/m51`:** K — ROOT derived-column round-trip → `test_derived_columns.py` (R1).

Every §10/m51 anchor bullet (A–N + K + L + M-docs) maps to exactly one tree/file above; no anchor is
orphaned, and each frozen file is satisfied by the commit(s) named.

---

## 4. Gated pipeline plan

State machine + roles as always (§12.1): `PENDING → DECOMPOSE → TEST_AUTHORING → TEST_SANITY →
FROZEN → IMPLEMENTING → REVIEW → DONE`; disputes at `.graphed/m51/disputes/<test_id>.md` and STOP;
iterations logged to `.graphed/m51/attempts.md` in each repo.

**Test-authors (one per repo family; NEVER see implementation):**
- **graphed test-author** — authors `tests/frozen/awkward/m51` (A–N) + `tests/frozen/numpy/m51` (L).
  Picks the m51-freeze spellings the plan defers: exact `select=` key spelling, `__vary_{label}__{field}`
  literal, manifest KEY names, `read_varied`/`graphed.selection` exact names, the numpy refusal
  message. Non-vacuity is load-bearing here: the all-zero-delta REPLICATION anchor (B) must FAIL a
  positional unpack, the collision anchor (E) must vary BOTH `Jet.pt` and flat `Jet_pt`, the depth
  anchor (D/2c) must refuse a jagged level-0 mask that passes 2a+2b.
- **fork test-author** — authors `tests/frozen/m51` (K, derived-column round-trip) + the fork's first
  frozen harness.

**TEST_SANITY (pre-freeze), per tree:** suite collects; is **non-vacuous** (fails the stub for the
right reason — e.g. the refusal anchors fail because the guard is absent, not because of an import
error); deterministic across two runs; coverage instrumentation wired (`COV=1 ./scripts/run-tests.sh`
for graphed). Run the **unique-basename check**, mirroring CI's `--ignore=tests/frozen/numpy/m40` so the
PRE-EXISTING m5↔m40 `test_projection.py` duplicate (which CI tolerates ONLY via that ignore) does
not false-flag: `find tests/frozen/numpy -path tests/frozen/numpy/m40 -prune -o -name 'test_*.py'
-print | xargs -n1 basename | sort | uniq -d` (numpy whole-subtree minus m40) and the same over
`tests/frozen/awkward/m51` (within dir); each is absence-shaped, so run its positive control once (a
known duplicate — e.g. drop the `test_*.py` filter to surface a shared helper basename) to prove the
instrument is live.

**Freeze tags** (each repo's live convention): `graphed` → `m51-freeze` (re-freeze `m51-freeze-fixup`
if needed); `uproot5-graphed-mvp` → `freeze-m51` (re-freeze `freeze-m51-fixup`).

**Implementers (one per repo; NEVER touch `tests/frozen/**`; may add `tests/extra/**`):**
- **graphed implementer** — C1 → C2 → C3 → C4 → D1, in order (the dependency chain of §2). Logs each
  iteration to `.graphed/m51/attempts.md`.
- **fork implementer** — R1 (independent).

**Mechanical gates (§B.3), every iteration:** frozen suite green + UNMODIFIED since freeze; ≥90%
line+branch **diff** coverage from the FROZEN suite (graphed: combined `coverage report
--fail-under=90` after all subtrees; the awkward/m51 tree covers `io.py`+`accessors.py`+`write.py`
diff, numpy/m51 covers the numpy guard); `ruff` + `clippy` clean; `mypy --strict` over each repo's
configured scope (graphed `files=["python"]`); determinism (byte-identical manifest); Sphinx `-W`;
integrity scan clean (never the dropped leg — it guards the no-`awkward._connect` rule). graphed runs
`python -m graphed_orchestrator.precommit . --fast` + `COV=1 ./scripts/run-tests.sh`.

**Three-lens implementation review (design / integrity / mutation), cycling until clean.** Every
mutating lens gets an isolated detached worktree with an import-provenance assert. Delta re-reviews
read the diff since the last reviewed version. The mutation lens is pointed at the trap ledger (§6).

---

## 5. Cross-repo landing

**Two independent PRs.** graphed PR (C1–C4 + D1) and fork PR (R1). Both repos use **merge queues**
(`gh pr merge` fails; GraphQL `enqueuePullRequest` works).

**No temporary cross-repo pin is required for m51.** The fork's m51 scope is derived-column IR
evaluation ONLY (§10: "no varied ROOT reader/manifest is frozen at m51"), so the fork's frozen suite
and source reference **only graphed's already-shipped public IR API** (`compile_ir`, `evaluate_ir`,
`Array`, `Session` — all ≥ m10; the pattern already lives in the fork's `graphed_head`). No m51-new
graphed symbol (`graphed.selection`, `select=`, `read_varied`) reaches the fork. Therefore the fork's
TEST_SANITY is collectible against `graphed@main` with **no `graphed.yml` GRAPHED-env repoint and no
reshuffle** — unlike the m50 arc. Recommended landing: graphed PR first (tidiness), fork PR any time
(before or after graphed merges — the fork depends on no m51 graphed symbol).

> **RESOLVED in plan r47 (§10(d)); retained here as rationale.** The task's §5 brief and the closed
> review's MED#5 ("fork suite needs the new `graphed.selection` symbol → temporary pin") were both
> predicated on the OLD reading where the ROOT half was VARIED. The FINAL §10 (`402ec46`) scopes the
> ROOT half to **derived columns only**, which removes that premise. Evidence: fork `graphed_write`
> writes `.root` via `uproot.recreate` (a separate sink from graphed's parquet `to_parquet`); the
> derived-column round-trip reads back with plain `uproot.open`; `grep` finds no `graphed.selection`
> usage anywhere the fork would author. If team-lead still wants the pin mechanism available (e.g. to
> exercise the fork against the exact graphed m51 tip), it costs a reshuffle for no correctness
> benefit; I recommend omitting it. This is the one divergence from the task framing I surfaced; the
> plan itself is self-consistent.

---

## 6. Trap ledger (implementer/test-author must witness)

Review-surfaced traps the mutation lens and the frozen anchors must catch:

1. **§7.2 node-id-not-positional unpack.** `mark_output` de-dups on the reduced store (`src/store.rs`)
   and `evaluate_ir` returns one value per DISTINCT output, so on an all-zero-delta label a POSITIONAL
   unpack in `_WritePart` misassigns every label after the collapse. Witness: anchor B's all-zero-delta
   REPLICATION (the value must be replicated into every label that maps to the shared node id). The
   `record node id → output position` table is a driver-derived `_WritePart` field (the frozen
   dataclass cannot recompute it in the worker).
2. **XOR/packbits computed in `_WritePart` on EVALUATED buffers.** `float32 ^ float32` raises
   `TypeError` (np AND ak) and gak has no bit-view verb (measured), so the delta is NOT expressible as
   an IR op — it is `ndarray.view(uintN)` after `evaluate_ir`, before the write. Trap: an implementer
   who tries to record the XOR as a graph op fails; the marked outputs are the per-label VALUES and
   MASKS, not the encoded deltas.
3. **Collision refusal BOTH directions.** derived-vs-derived AND derived-vs-stored. The real class:
   both `Jet.pt` and a flat `Jet_pt` varying → both derive to `__vary_L__Jet_pt`. Anchor E must vary
   BOTH; a varying `Jet.pt` beside a NON-varying `Jet_pt` is a LEGAL nested skim, not a refusal.
4. **Manifest sorted-keys + heterogeneous levels-LIST order.** `sorted()` over `[int, [str,int]]` is a
   `TypeError`; `json.dumps(sort_keys=True)` never orders a list's elements (both measured). The levels
   list needs the explicit key `(depth, field_path or "")` — bare-depth before field-scoped of the same
   depth. Without it the manifest bytes depend on `PYTHONHASHSEED` and anchor F reds.
5. **numpy refusal triggers on a `Varied` FIRST-POSITIONAL, not `select=`.** No `select=` kwarg is added
   to the numpy idiom; a `select=` call stays a plain `TypeError` (do NOT freeze a graphed error for
   it). Entry point is the MODULE path `graphed.numpy.io.to_parquet` (absent from the `graphed.numpy`
   namespace/`__all__`).
6. **Depth via `session.form(array).tt.ndim`, NOT `_form_meta`.** `AwkwardForm` exposes no depth
   accessor; `_form_meta("depth")` records a bogus `field` op and raises `GraphedTypeError` (measured;
   confirmed MED, already corrected in plan r46). This is the 2c mechanism at every supplied level.
7. **Record-time vs exec-time split.** Record-time at the `to_parquet` call: 2a lineage, 2c depth,
   bare-key ambiguity, §6.4f optimizer-merge, §6.4b row-space. Execution-time in `_WritePart` before
   any buffer is stored (surfacing through the executor error path): (1) multiplicity, (2b) row-count
   level-0, level-≥1 structural (offsets). Do NOT freeze a record-time raise for any offsets/row-count
   predicate.
8. **`graphed.selection` is NOT a thin wrapper over `_selection()`.** `_selection()` returns `None` on
   a `project` link (measured), but §9.1 case-2 must return that label's member of the parent's
   selection (an unvaried `Array` in the grandparent's row space) — else the universe/nominal REFUSE
   control (D/2a) cannot fire for the specified reason.
9. **Conditional writer swap.** UNVARIED write keeps `ak.to_parquet` untouched (§6.4g byte-golden);
   VARIED write must NOT import `awkward._connect.*` — route is PUBLIC `Table.replace_schema_metadata`
   + `pq.write_table`. (`ak.to_parquet` has no `metadata=` param and the naive arrow write produces
   different bytes — both measured; the "dropping `awkward_array_metadata` breaks round-trip" clause
   was the one measured claim that did NOT reproduce, so do NOT freeze a "naive arrow write breaks
   round-trip" test.)
10. **Byte-identity is a SAME-PROCESS comparison, never a committed `.parquet` fixture** (§6.4g: the
    parquet footer embeds the writer version — `created_by = 'parquet-cpp-arrow version …'`, measured
    — so a committed blob reds on a pyarrow bump and across §A.5 legs while behavior is correct).

---

## 7. Notes for the orchestrator

1. **The m51-freeze spellings** the plan defers (exact `select=` key form, `__vary_{label}__{field}`
   literal, manifest KEY names, `read_varied`/`graphed.selection` names, numpy refusal message) are
   freeze-time naming choices inside already-bound rules — the test-author picks them at freeze, the
   implementer inherits them.
2. **The no-`awkward._connect`-import rule is knowingly UNANCHORED** (§6.4e) — it rides code review +
   the integrity scan; the implementer MAY discharge it with a one-line `tests/extra` static assertion.
3. **C3 band-risk** — if augmentation + §7.2 unpack + four refusals + exec-time predicates measure
   toward the upper band during implementation, split at C3a/C3b (§2). Decided by measured LOC, not
   pre-split.
4. **Cross-repo pin** — omitted by design (§5). If team-lead's fact-check restores the varied-ROOT
   reading (it should not, per `402ec46`), the m50-style pin+reshuffle is the fallback.
