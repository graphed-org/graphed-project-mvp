# Review — `systematics-vary-plan.md` r10 — LENS: TEST ARCHITECTURE (round 2)

- **Lens**: test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), R0.10a
  (no wall-clock/size thresholds in frozen tests), determinism-gate compatibility, freeze-order
  hazards, requirement↔anchor traceability, and buildability of the fixtures the anchors presume.
- **Plan revision reviewed**: r10 (2026-07-30), full document (Part I, PART II §§1–12, §10
  milestones m48–m51, Anchors appendix, revision history).
- **Date**: 2026-07-30.
- **Verification roots used** (fresh clones at the revisions the plan pins — the stale submodules
  under `/Users/lgray/vibe-coding/graphed-workdir` were NOT used for any code fact):
  - `/private/tmp/claude-501/graphed-latest` (`ff7c607`)
  - `/private/tmp/claude-501/graphed-exec-check` (`201ea42`)
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`)
  - `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`)
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md` (R0.10/R0.10a/R0.11/R22.3)
  - one runtime probe in `/Users/lgray/vibe-coding/graphed-workdir/.venv` (pyarrow 24.0.0 /
    awkward 2.9.0) — used only for the parquet-footer fact in finding 6, which is version-generic.

Owner-locked decisions (naming, functional surface, e-form canonical tags, context attachment,
record-time expansion + interning, m48–m51 scope incl. §6.4, JER-SF non-ordering, the Phase-2
pull-in) are taken as given; nothing below relitigates them.

---

## Findings

### 1. HIGH — m48's headline anchor (the 9 corpus weight references) is not buildable in either named repo, and m48's anchor list is not partitioned across its two repos

**Section**: §10 m48 (frozen anchors, bullets 1 and "Single-pass read witness"), §4.2, §5.2b.

**Detail.** m48's acceptance rests on reproducing 9 of the 15 stored corpus references *through a
varied `Histogram.fill`* (§4.2/§6.1), and the §5.2b single-pass read witness is explicitly bound to
that same run. That needs, in ONE test process: (a) the 15 stored reference JSONs and (b)
`graphed_histogram`. Neither repo named for m48 has both, and the plan binds no dependency change —
even though it performed exactly this analysis for m49(ii) and bound "m49 adds `graphed-histogram`
to `graphed-executors`' `dev` extra".

**Evidence** (all measured this session):
- `graphed` has the references (`tests/_corpus/references/`, 23 files, on `pythonpath` via
  `pyproject.toml` `pythonpath = ["python", "tests/_corpus", …]`) but **no `graphed-histogram`
  dependency in any extra** — `graphed/pyproject.toml` `[project.optional-dependencies] dev`
  lists `boost-histogram>=1.4`, `hist>=2.7`, never `graphed-histogram`; CI installs `.[dev]`
  (`.github/workflows/ci.yml:34,57,143,205`). The house consequence is measured: every existing
  `graphed` frozen test that needs it uses `pytest.importorskip("graphed_histogram")`
  (`tests/frozen/preserve/m25/test_histogram_preservation.py:31`,
  `preserve/m27/test_variadic_call_templates.py:185,207`,
  `preserve/m30/test_producer_cross_seam.py:155`) — i.e. an m48 anchor written there would
  **SKIP in CI**, silently discharging the milestone's headline gate and contributing no frozen-suite
  diff coverage (§10 DoD requires ≥90% diff coverage *from the frozen suite*).
- `graphed-histogram` has the fill sink but **no corpus at all**: `pyproject.toml` `dev` =
  `{pytest, pytest-cov, hypothesis, mypy, ruff, graphed[awkward,numpy], awkward, graphed-executors,
  hist, pyarrow, pandas}` — no `graphed-corpus`; `grep -rn "graphed_corpus\|corpus" tests/
  .github/workflows/*.yml` returns **zero hits**. And the references are not installable anyway:
  `graphed-corpus/pyproject.toml` packages only `src/graphed_corpus` while the JSONs live in the
  repo directory `corpus/references/` (23 files) — the plan itself verified this for m49.
- m49 splits its matrix anchor across repos explicitly ((i)/(ii), with the fixture facts). m48's
  anchor list is a single flat list for two repos, so it is also undecided *where* each of the
  ~14 m48 anchors is frozen — and the frozen-layout rules in §10 pin directories per repo, so the
  test-author cannot start without that assignment.

**Suggested fix.** Give m48 the same explicit split m49 got: (i) `graphed`
`tests/frozen/frontend/m48` — the pure-frontend anchors (§1.1 grammar, §1.2 identity, §2.1
stacking, §2.2, §2.3 parity/classification/handle gates, §2.4 order, §2.6 context lineage, §3.2
determinism, §3.4 API, §6.3 goldens, §7.2 schema absence); (ii) `graphed-histogram`
`tests/frozen/m48` — the fill-dependent anchors (corpus 9-reference weight matrix, §5.2b read
witness, §6.1a result shapes, §6.1c `.plan()` refusal, §6.1d ambient fills, §4.1 correctionlib).
Bind the dependency for whichever repo hosts the matrix, in the m49(ii) style: either
"m48 adds `graphed-corpus` to `graphed-histogram`'s `dev` extra **and** vendors/points at the
reference JSONs (they are not in the wheel)", or "m48 adds `graphed-histogram` to `graphed`'s `dev`
extra and CI installs it" — and state that the anchor must NOT be guarded by `importorskip`.

---

### 2. MID — §6.1a's frozen result-shape rule collides with §6.2's axis mode (m50), and the narrowing-helper contract is false there

**Section**: §6.1a + m48 anchor "§6.1a result shapes"; §6.2 + m50.

**Detail.** §6.1a binds, and m48 freezes, "a varied output is `{label: hist}`; an output no
variation reaches is a BARE `hist`", plus "a bare `hist` reads as the single label `"nominal"`" for
`graphed.labels`/`graphed.universe`. §6.2's axis mode (m50) puts *many* labels in ONE histogram, so
an axis-mode varied output is a single `bh.Histogram` — which under the frozen m48 rule is
indistinguishable from "an output no variation reaches", and for which `graphed.labels(...) ==
["nominal"]` is simply wrong. The plan never states the axis-mode result shape, so m50's implementer
inherits a frozen rule that contradicts the mode m50 must ship.

The m48 test itself will not break (axis mode does not exist yet, so its fixture is sibling-mode),
but the *requirement* it freezes is stated generally, and the narrowing helper is bound generally in
§6.1a — which is the freeze-order hazard class the r7 sweep already caught once.

**Evidence.** §6.1a (plan:648–659) vs §6.2 (plan:692–704) and the m50 anchor (plan:1068–1071);
`_GroupReduce.layout: tuple[tuple[str,int,str],…]` returns `{label: hist}` keyed by *output* label
today (`graphed-histogram src/graphed_histogram/boost.py:100-122`), and `_add_groups` combines
key-wise over `a`'s keys (`boost.py:120-122`) — so nothing in the runtime distinguishes the two
readings either.

**Suggested fix.** In §6.1a add one sentence: the result-shape rule and the "bare `hist` = single
label `nominal`" narrowing are scoped to **sibling-fill (default) mode**; bind the axis-mode result
shape explicitly (a single histogram whose labels live on the `"variation"` axis) and state what
`graphed.labels`/`graphed.universe` return for it (e.g. labels read off the axis; `universe` slices
the axis, or both refuse with a message pointing at the axis). Mirror the scoping in the m48 anchor
wording so the frozen test is explicitly about sibling mode.

---

### 3. MID — the §6.2 declaration contract's only *silent* failure has no anchor

**Section**: §6.2 (ii)/(iii); m50 anchors.

**Detail.** §6.2 binds a three-part declaration contract precisely because the plan **measured**
that a non-growth `StrCategory` swallows an undeclared label into an overflow bin instead of
raising (`h.sum() == 2.0` vs `h.sum(flow=True) == 3.0`, boost_histogram 1.7.2 — Anchors row). Part
(ii) — "a label not among the declared bins is a hard error naming it, and a declared bin no label
reaches is a diagnostic" — is the guard against exactly the survey failure mode §2.5 exists to
delete. m50's anchors cover equality-with-siblings, combine-safety ("identical spec, deterministic
label order") and the structural allocation count; **nothing covers (ii)**. Part (iii) (frontend
normalizes a user-supplied bin ORDER to sorted) is only indirectly touched by "deterministic label
order".

Because (ii) is conditional ("if a user-declared axis is supported at all"), this is a MID, not a
HIGH — but as it stands the one behaviour the plan proved is silent ships unfrozen.

**Suggested fix.** Add an m50 anchor: with a user-declared axis, filling a label outside the
declared set raises naming the label (positive control: the same program with the label declared
fills it, and `h.sum(flow=True) == h.sum()` — the direct discriminator against the measured
silent-overflow behaviour); a declared-but-unreached bin produces the §2.5 diagnostic; and a
user-supplied unsorted bin order yields the same spec as the sorted one. If user-declared axes are
NOT supported in v1, say so in §6.2 and freeze the refusal instead.

---

### 4. MID — the three dynamically-enumerated exhaustiveness gates can pass vacuously; "`dir`/`__all__`-driven" is not implementable as stated

**Section**: §2.3a (dunder parity), §2.3c (gak classification), §2.3e (context-handle
propagation); m48 anchor "dunder-parity and gak-classification exhaustiveness tests, both
dynamically enumerated".

**Detail.** r10 correctly replaced literal name lists with dynamic enumeration (self-repairing, no
frozen-test edit when `src` grows). But a dynamic gate whose discovery step returns an empty or
wrong set passes **tautologically** — and the plan's stated discovery mechanism does not exist:
`graphed.awkward.functions` (= `gak`) defines **no `__all__`** (`grep -c "__all__"
python/graphed/awkward/functions.py` → `0`), and the package-level
`graphed/awkward/__init__.py:17-31` `__all__` lists *modules and classes*
(`functions`, `gak`, `io`, `payloads`, `shuffle`, `AwkwardBackend`, …), not gak's ~60 public
functions (`grep -c "^def " functions.py` → 73, including private helpers). So a literal
`getattr(gak, "__all__", [])`-driven test discovers **nothing** and asserts nothing; a naive
`dir(gak)` discovers imported symbols (`Sequence`, `Array`, `annotations`) and over-fires. The
same hazard applies to "enumerated dynamically from `Array` at test time" and to the §2.3e handle
gate that reuses the same enumeration.

**Suggested fix.** Bind the discovery rule (e.g. `inspect.getmembers(gak, inspect.isfunction)`
filtered by `fn.__module__ == gak.__name__` and no leading underscore) **and** a non-vacuity floor
in the same frozen test: the discovered set is non-empty, has at least the count present at freeze,
contains a named member of every classification class (one *broadcast*, one *container-traversing*,
one *tuple-returning*, one *eager-metadata*, one *refusing*), and — for the dunder gate — contains
`__array_ufunc__`, `__getitem__` and one bitwise dunder. The floor is what makes the gate
discriminating; the dynamic part is what keeps it self-repairing.

---

### 5. MID — §2.3b (plain-`Array` entry points learning `Varied`) is binding but has no anchor, and its wrong-implementation shape is a deep `AttributeError`

**Section**: §2.3b; m48/m49 anchor lists.

**Detail.** §2.3b binds two specific surfaces: `Array.__getitem__` gaining a `Varied`-mask branch and
`Array.filter` gaining one. No milestone anchor names it. The m48 "dunder-parity" anchor is the
*mirror* property (`Varied` implements `Array`'s dunders), which does not exercise a plain `Array`
indexed by a `Varied`. The behaviour reaches the suite only implicitly, one milestone later, inside
m49's 15-reference matrix (the corpus ttgamma path indexes unvaried `photons` by a JES-varied
selection, `graphed-corpus src/graphed_corpus/analyses/systematics.py:91-92` → `photons[sel]`) —
which is precisely the argument r10 used to add the m48 §2.1-stacking anchor.

**Evidence.** Today's behaviour, read this session in `graphed-latest`:
`Array.__getitem__` accepts `Array`/`str`/`list[str]`/`slice`/`int` and ends
`raise TypeError(f"unsupported index {key!r}; …")` (`python/graphed/array.py:343-369`);
`Array.filter` has **no check at all** — `def filter(self, mask: Array) -> Array: return
self._session.record_op("filter", [self, mask])` (`array.py:374-375`) — so a `Varied` falls into
`record_op` and dies as an `AttributeError` on `.node_id`. Both failure shapes are invisible to a
histogram-value comparison.

**Suggested fix.** Add an m48 anchor: `plain_array[varied_mask]` and `plain_array.filter(varied_mask)`
each return a `Varied` with the mask's labels (label-aligned per §2.4), and a *negative* control
that neither raises `TypeError`/`AttributeError` — plus the still-`TypeError`ing control for a
genuinely unsupported index type, so the new branch cannot be implemented as a blanket `except`.

---

### 6. MID — m51's "unvaried write is byte-identical to today (golden, the §6.3 pattern)" transplants a committed-byte oracle onto a file format that embeds its writer's version

**Section**: §6.4g; m51 anchor "an unvaried write keeps the `ak.to_parquet` path, carries NO
manifest, and is byte-identical to today (§6.4g golden)".

**Detail.** §6.3's golden pattern is a **committed literal byte oracle of graphed's own GIR
format** — deterministic by construction and versioned by graphed itself
(`tests/frozen/core/m40/test_join_serialize.py:83-99`: a literal `b"GIR1\x03…"` compared to
`g.serialize(...)`). Parquet is not that: the footer carries the writer version, so a committed
parquet golden turns red on any pyarrow bump and can differ across §A.5 matrix legs while the
behaviour is perfectly correct — the R0.10a spirit ("must hold on every run on every matrix leg").

**Evidence** (measured this session, `/Users/lgray/vibe-coding/graphed-workdir/.venv`, pyarrow
24.0.0 / awkward 2.9.0): `ak.to_parquet` output contains the ASCII string
`parquet-cpp-arrow version 24.0.0`; two writes of the same array **in one process** are
byte-identical (`True`). So the invariant is available — but only as an in-run comparison, not as a
committed blob.

**Suggested fix.** Re-word §6.4g/m51: the unvaried-write invariant is frozen as a **same-process
comparison** — write the same record through the (feature-present) write path and through
`ak.to_parquet` directly, assert byte equality and that the KV metadata carries no manifest key —
never as a committed `.parquet` fixture. Keep the committed-blob pattern for the GIR/IR goldens
where it belongs.

---

### 7. LOW — m48's "§7.2 schema absence" anchor must be scoped to public schema field sets, because m49 adds a field to the shipped worker closure

**Section**: m48 anchor "§7.2 schema absence"; §8.2(i).

**Detail.** §8.2(i) adds `variation_labels: tuple[tuple[int, frozenset[str]], …]` to
`_PartitionReduce` in m49 and argues "`Plan`/`ExecResult` schemas stay untouched (§7.2)". That is
true of the *public* schemas, but `_PartitionReduce` is an instance embedded in the plan as an
**opaque cloudpickle `OpSpec`**, whose bytes are folded into `process.identity()` and hence into
`task_id` and `fingerprint()`. So (a) the m48 frozen anchor must be written over schema *field
sets/keys*, not over plan bytes or the process spec, or m49 breaks a frozen test; and (b) the m49
field bump silently invalidates every checkpoint journal, including for **unvaried** programs —
a wider blast radius than §7.3's documented "adding a variation invalidates every task_id".

**Evidence.** `python/graphed/aggregate.py:45-96` (`_PartitionReduce` frozen dataclass, instantiated
as `process=`); `python/graphed/core/plan.py:72-90` (`OpSpec.identity()` returns
`b"opaque\0" + blob` for embedded callables), `:164-176` (`task_id` folds `self.process.identity()`).
No frozen test pins a literal `task_id`/`fingerprint` hex (checked: all
`tests/frozen/**` assertions on `task_id`/`fingerprint()` are relative), so nothing breaks today.

**Suggested fix.** Word the m48 anchor as "the `ExecResult`/`Plan`/monitor **payload key sets** are
identical for a varied and an unvaried program" and add one sentence to §8.2(i) noting the
`process.identity()` → `task_id` consequence of the added field (a one-time, all-programs cache
invalidation at the m49 upgrade), so §7.3's documented limitation covers it.

---

### 8. LOW — the m48 grammar anchor's "unify" is ambiguous for a canonical/spelled pair in one call

**Section**: §1.1; m48 grammar anchor ("`"0.5"` and hand-typed `"5em1"` unify").

**Detail.** §1.1 says `"0.5"` canonicalizes to `5em1`, and separately that `vary` MUST reject
"duplicate labels after canonicalization (within the call…)". So `{"0.5": a, "5em1": b}` in one
call is a **rejection**, while across two calls the two spellings name the SAME label. The anchor
says only "unify", next to a list of rejections — a test-author can reasonably freeze either
reading, and the two are incompatible.

**Suggested fix.** Split the anchor clause: "two *separate* `vary` calls spelling `"0.5"` and
`"5em1"` produce the identical label `murf_5em1`; the same two spellings *within one call* are a
duplicate-after-canonicalization rejection" — the same shape already used for the cross-notation
`{"0.5","0p5"}` case.

---

### 9. LOW — the m48 corpus-matrix anchor omits the corpus's `stable()` rounding, the one fixture detail that decides bit-comparability

**Section**: m48 anchor bullet 1 ("the `m05/test_fixtures_reproduce.py` comparison form").

**Detail.** The stored references are produced by an eager pipeline that rounds the **observable to
6 decimals before the fill** and the histogram view after it; the comparison helpers round again.
Through a deferred, partitioned fill, (a) the pre-fill rounding has to be re-expressed in the
recorded graph if bin-edge decisions are to match the corpus's cross-platform-stability intent, and
`gak` has **no `round(x, decimals)`** — only the `rint` ufunc mapping — so the expressible form is
`rint(x * 1e6) / 1e6`; (b) conversely, `bin_values`' driver-side 6-decimal rounding is what absorbs
the float-summation-order differences a per-partition fill introduces, so no raw-view bit-identity
should be attempted. Neither is stated. This is the same mid-freeze surprise the plan pre-empted for
`gak.full_like` in the very next sentence of the same bullet.

**Evidence** (`graphed-latest`, vendored corpus):
`tests/_corpus/graphed_corpus/analyses/systematics.py:79` `h.fill(np.round(ak.to_numpy(ht),
STABLE_DECIMALS), weight=…)`, `:102` (same for ttgamma), `:50` `view[...] = np.round(view,
STABLE_DECIMALS)`; `tests/_corpus/graphed_corpus/histograms.py:20` `STABLE_DECIMALS = 6`, `:34-37`
`bin_values` rounds, `:39-42` `fingerprint` hashes the rounded values; `grep "^def " 
python/graphed/awkward/functions.py` shows no `round` (`rint` is in the ufunc map,
`python/graphed/array.py:53`).

**Suggested fix.** One clause in the anchor, in the same spirit as the `full_like` note: "the
recorded program reproduces the corpus's `stable()` 6-decimal pre-fill rounding (`gak` has no
`round(decimals)`; `rint`-scaling is the expressible form); the comparison rides `bin_values`/
`fingerprint`, whose rounding is what makes a partitioned fill comparable — do not assert raw-view
bit-identity against the references."

---

### 10. LOW — two binding clauses with no anchor: §2.5's unreached-label diagnostic, and §8.1's `__hash__` participation

**Section**: §2.5, §8.1; m48/m49 anchor lists.

**Detail.**
- §2.5 binds a **diagnostic** (not an error): `compile_ir` reports any registered label that reaches
  no marked output — the guard against the mkShapesRDF silent-cost case. m48 covers only "§2
  validation errors (§1.1, §2.5)", which a test-author will read as the raising cases.
- §8.1 binds `variation` participating in `__eq__` **and** `__hash__`. Measured: `StageError.__eq__`
  compares `self.__dict__` (so a new field participates for free), but `__hash__` is an explicit
  tuple `(op, frames, partition, cause_type, cause_message)` that must be edited by hand
  (`python/graphed/debug/errors.py:74-81`). Nothing in m49 asserts it; the "wrong implementation"
  here (forgetting the `__hash__` edit) is invisible to the cross-process label anchor.
  (No freeze hazard from the `summary()` change: the m6 frozen test compares
  `str(e2) == _err().summary()` relatively, `tests/frozen/debug/m6/test_stage_error.py:46-49`.)

**Suggested fix.** Name both explicitly: an m48 anchor asserting the unreached-label diagnostic is
emitted (and is absent when every label reaches an output), and one clause in the m49 §8.2 anchor
asserting two `StageError`s differing only in `variation` are unequal **and** hash differently.

---

### 11. LOW — m50's histogram-side frozen directory is unpinned

**Section**: §10 preamble.

**Detail.** §10 pins the consolidated repo's directories (`frontend/m48`, `frontend/m49`,
`preserve/m50`, `awkward/m51`, `core/m49`) precisely because duplicate basenames have bitten that
repo, and names `graphed-histogram = flat tests/frozen/m48…`. But m50's *primary* target (§6.2 axis
mode) lives in `graphed-histogram`, and only the `graphed` preserve half gets a pinned path. The
trailing "…" is doing load-bearing work.

**Suggested fix.** Say "`graphed-histogram` = flat `tests/frozen/m48`, `tests/frozen/m50`" and note
that m50's `graphed` half is `tests/frozen/preserve/m50` (docs/preservation only).

---

### 12. NIT — m49's JER fixture asks for one brittle assertion next to the real discriminator

**Section**: m49 anchor, JER-SF stochastic fixture.

**Detail.** "selected counts pairwise distinct across {nominal, jer_up, jer_down}" is fixture luck
(content-seeded, so deterministic — but the test-author may have to hunt a seed), while "no
universe's selection mask is a subset of another's" is the actual non-monotonicity discriminator
and is unaffected by coincidental count equality. Keeping both is harmless; keeping only the second
is stronger per unit of fixture fragility.

---

## Verdict — DIRTY (no blockers)

The lens is clean on the two things it most often catches: **R0.10a discipline is exemplary** — the
m50 wall-clock comparison and the §6.4c compression win are both explicitly demoted to R0.11
implementer-report measurements with structural frozen invariants in their place, and the one
frozen wall-clock gate (§3.3) is a properly named carve-out whose precedent I verified
(`tests/frozen/core/m4/test_benchmark.py` frozen today with `growth < 24.0` over an 8× size ratio
and `elapsed < 1.0` budgets; the plan's 16→128 ratio is the same 8× shape, with measured 5.4×
headroom). **Determinism-gate compatibility checks out** (§3.2's fresh-process/differing-
`PYTHONHASHSEED` form matches the R22.3 house form; the corpus comparison path rounds at 6 decimals
via `bin_values`, which absorbs partition-order float noise). r10's own anti-tautology work is
sound: the §4.3 withdrawal, the m51 superset anchor re-based on an *eager, outside-graphed*
reference, the §5.2a literal-Δ witness travelling with its builder, and the §7.2 node-id (not
positional) binding all survive scrutiny — I found **no new instance** of the §4.3/§5.2a tautology
class.

What blocks a clean round is one HIGH and five MIDs, all of the "test-author cannot start / would
freeze the wrong thing" kind: m48's headline anchor has no buildable home (finding 1); §6.1a would
freeze a result-shape rule m50 must contradict (2); the one measured *silent* histogram failure has
no anchor (3); the three dynamic exhaustiveness gates can discover nothing and pass (4); §2.3b is
unanchored with an `AttributeError`-shaped wrong implementation (5); and the m51 parquet golden as
worded is a version-fragile frozen test (6). All six have narrow, mechanical fixes that touch
anchor wording and two dependency bindings — none requires reopening an owner-locked decision.
