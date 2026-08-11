# Review r12 — TEST ARCHITECTURE lens

- **Plan under review:** `systematics-vary-plan.md` revision **r12** (draft for review), read in full
  (Part I, PART II §§1–12, §10 milestones m48–m51, Anchors appendix, revision history).
- **Lens:** test architecture — non-vacuity/discrimination, mechanism witnesses (R0.10), R0.10a
  (no wall-clock/size thresholds in frozen tests), determinism-gate compatibility, freeze-order
  hazards, requirement↔anchor traceability, and buildability of the fixtures the anchors presume.
- **Date:** 2026-07-30. **Review round:** 4.
- **Verification roots used** (all code facts below were read/executed by me in this session):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607`)
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`)
  - `/private/tmp/claude-501/graphed-exec-check` (`graphed-executors`, `201ea42`)
  - `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`)
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md` (R0.10/R0.10a/R0.11, R22.3)
  - live probes: CPython + cloudpickle (frozenset pickle stability), pytest 8 (duplicate-basename
    collection), boost_histogram 1.8.0 (StrCategory over/under-declaration).
- Owner-locked decisions were not relitigated. Nothing below asks for a different design choice;
  every finding is about how a bound requirement is (or is not) pinned by a frozen anchor.

Ten findings: 2 HIGH, 4 MID, 4 LOW. No BLOCKER. Detail per finding, most severe first.

---

## HIGH-1 — §8.2(i)'s `frozenset[str]` transport field makes the serialized plan seed-dependent; no anchor would catch it

**Section:** §8.2(i), §7.2, §7.3, §3.2; m48 "§7.2 schema absence" anchor; m49 §7.3 resume anchor.

**Detail.** §8.2(i) binds the transport as
`variation_labels: tuple[tuple[int, frozenset[str]], ...]` added to `_PartitionReduce`
(plan lines 1273–1275). The plan itself states the consequence chain (§7.3): `_PartitionReduce` is
the plan's **opaque** `process` spec and `task_id` folds `self.process.identity()`. A `frozenset`
of `str` iterates in hash order, so its pickle bytes are **PYTHONHASHSEED-dependent** — which makes
`OpSpec.identity()`, `DurablePlan.task_id()` and `DurablePlan.fingerprint()/to_bytes()` differ
across processes for one identical program. That directly contradicts §3.2's own determinism
requirement in "the strong R22.3 form (fresh processes, differing `PYTHONHASHSEED`)" and the DoD's
determinism gate ("byte-identical … serialized plan across two runs"), and it silently destroys
cross-run checkpoint reuse (every `task_id` differs run to run, not just across plan revisions).

**Evidence (measured this session).**

```
$ for seed in 1 7 12345; do PYTHONHASHSEED=$seed uv run python -c "
import cloudpickle, hashlib
from dataclasses import dataclass
@dataclass(frozen=True)
class T: labels: tuple
d = T((( 3, frozenset({'jes_up','jes_down','btag_up','pu_down','pdf_17'})),))
print(hashlib.sha256(cloudpickle.dumps(d)).hexdigest()[:16], list(d.labels[0][1]))"; done
1      4d5af3b1647cd4a0 ['jes_up', 'pu_down', 'btag_up', 'pdf_17', 'jes_down']
7      685a6be5573eb698 ['pu_down', 'jes_down', 'btag_up', 'pdf_17', 'jes_up']
12345  ec6d0c3175d3bad2 ['jes_down', 'btag_up', 'jes_up', 'pu_down', 'pdf_17']
```

- `_PartitionReduce` is a frozen dataclass instance and is the plan's `process`
  (`graphed-latest/python/graphed/aggregate.py:44-65,94-105`).
- `OpSpec.from_callable` falls through to `kind="opaque"` for it — the `from_ref` round-trip
  resolves the *class*, not the instance, so `resolve() is fn` is False
  (`python/graphed/core/plan.py:95-108`); `identity()` returns the raw cloudpickle bytes
  (`plan.py:72-77`); `task_id` folds them (`plan.py:164-176`), as does `DurablePlanV2.task_id`
  (`plan.py:286-301`).
- The codebase already applies this discipline elsewhere: `read_columns` returns the read set
  **sorted** precisely so a `set` never reaches the plan (`python/graphed/projection.py:109-121`,
  "every field accessed … , sorted").

**No anchor catches it.** m48's schema-absence anchor is deliberately worded over **key sets**, not
plan bytes (§10/m48, and §7.2 says so). §3.2's determinism anchor covers `compile_ir` output only.
m49's §7.3 anchor is an interrupt/resume inside one process, where the seed is constant.

**Suggested fix.** (1) Bind the field as an **ordered, sorted** shape —
`tuple[tuple[int, tuple[str, ...]], ...]` with labels sorted (the §8.2 rendering already sorts, so
nothing else changes). (2) Add an m49 frozen anchor: the same varied program built in **two fresh
processes under differing `PYTHONHASHSEED`** yields a byte-identical `DurablePlan.to_bytes()` /
identical `task_id` per partition — the plan-level twin of §3.2's IR-level anchor. (3) While there:
state that the §6.4e manifest is serialized with sorted keys, for the same reason.

---

## HIGH-2 — §2.3d's module-verb dispositions and §2.2's reserved `node_id`/`session` are binding and unanchored anywhere in m48–m51

**Section:** §2.2 (reserved `Array`-protocol attribute names), §2.3d (exhaustive module-verb
enumeration); m48 anchor list.

**Detail.** r12 added both as guards against the plan's own named failure class: because `Varied`
implements field access by mapping over labels, an unhandled duck-typed read becomes a **recorded
`field` op**, so `compile_ir(session, varied)` "would silently compile that nonsense instead of
raising" (§2.2, lines 402–410) and an undisposed module verb "silently compiles nonsense" (§2.3d,
lines 464–476). Both requirements then get **no frozen anchor**:

- m48's anchor list contains no bullet for `graphed.compile_ir` / `evaluate_ir` /
  `aggregate_plan` refusing a `Varied`, none for `graphed.apply` / `read_columns` expanding into
  universes, and none for `Varied.node_id` / `Varied.session` raising `AttributeError`.
- The §2.3a parity gate does not reach them: it enumerates **dunders and methods**
  (§2.3a, m48 bullet at lines 1514–1519), while `node_id`/`session` are plain **properties**
  (`graphed-latest/python/graphed/array.py:137-143`), which `inspect.isfunction` does not return.
- m49's "§5.4 refusal + positive control" anchor is the *boundary-crossing* refusal (a variation
  whose cone crosses `Exchange`/`Join`), not `graphed.join(varied)` / `graphed.repartition(varied)`.

This is exactly the gap r12 itself closed for §5.3 ("it was binding but unanchored … so it could
have shipped unimplemented with every m49 anchor green", lines 783–786). Left as is, the whole
§2.3d disposition table can ship unimplemented with every m48 anchor green, and the observable
symptom is a *compiled graph*, not an error.

**Suggested fix.** One m48 anchor in `graphed`'s `tests/frozen/frontend/m48`, table-driven over the
§2.3d enumeration measured from `python/graphed/__init__.py:8-25`/`__all__ :27-58`: each *refusing*
verb raises a `graphed` error naming `graphed.universe` (positive control: the same verb on a plain
`Array` still works); each *expanding* verb returns the per-label shape §2.3d binds; and
`varied.node_id` / `varied.session` raise `AttributeError` rather than returning a recorded op
(negative control: `varied["node_id"]` — string getitem — still resolves as field access, so the
rule cannot be implemented as a blanket `__getattr__` refusal).

---

## MID-3 — the m49 JER-SF anchor's four witnesses cannot discriminate a constant-seeded RNG, which §5.5(a) forbids

**Section:** §5.5(a); m49 anchor "A JER-SF-style stochastic shift fixture" (lines 1651–1657).

**Detail.** §5.5(a) binds "randomness MUST be a deterministic pure function of **event content** …
global RNG state, wall-clock, or **per-run seeds** are forbidden". The anchor's witnesses are:
run-to-run byte-identical results; pairwise-distinct selected counts; bidirectional migration; and
the shared draw node interned once. A fixture that draws `np.random.default_rng(0).normal(size=n)`
**per partition** — a fixed constant seed, not content-seeded — passes **all four**: it is
reproducible run to run, it migrates events both ways, and it still interns as one draw node. Only
the *content* dependence is untested, and that is the property with physical consequences: with a
constant seed the same event gets a different smear when the dataset is repartitioned, so two runs
that differ only in `steps_per_file` disagree — a silent, data-dependent nondeterminism the
determinism gate (same partitioning both runs) never sees.

**Evidence.** §5.5(a) text at plan lines 795–800; the anchor's witness list at lines 1653–1657;
the coffea precedent the plan cites seeds PCG64 from the input array's own bytes
(`coffea jetmet_tools/CorrectedJetsFactory.py:36-47`, cited by the plan and consistent with its
own §5.5 statement).

**Suggested fix.** Add one witness to the same anchor: **partition invariance** — the identical
event set run at two different partitionings (e.g. `steps_per_file=1` and `4`) produces
byte-identical per-label histograms/row sets. That is precisely what content-seeding buys, is a
deterministic invariant (R0.10a-safe), and is the only listed check a constant seed fails.

---

## MID-4 — two of the four pinned frozen directories are collected in ONE pytest process, and the natural filenames collide

**Section:** §10 directory pins (`tests/frozen/core/m49`, `tests/frozen/preserve/m50`); §3.3
("replicating the `test_benchmark.py:10,40-53` pattern"); m50 §9.2/`inspect()` anchors.

**Detail.** §10 pins directories and warns that "duplicate basenames have bitten it before", but the
per-file hazard is not closed for the two new directories that land in **non-split** suites:

- `scripts/run-tests.sh:15-24` lists `core:tests/frozen/core` and `preserve:tests/frozen/preserve`
  as single suites; `SPLIT_PKGS="frontend numpy awkward"` (`:29`) — so `core` and `preserve` are each
  collected in **one** prepend-import pytest process.
- There is no `__init__.py` anywhere under `tests/frozen` (measured:
  `find tests/frozen -name __init__.py` → empty), so duplicate top-level basenames are a collection
  **error**, not a shadowing subtlety.
- The colliding names are the *natural* ones: `tests/frozen/core/m4/test_benchmark.py` already
  exists and §3.3 tells the author to replicate it; `tests/frozen/preserve/m9/test_reproduce.py` and
  `tests/frozen/preserve/…/test_inspect.py` already exist and m50's anchors are "one-bundle-N-labels
  preservation (m9 comparison form)" and "`inspect()` label listing".

**Evidence (measured).**

```
$ mkdir -p dupcheck/m4 dupcheck/m49 && echo 'def test_a(): pass' > dupcheck/m4/test_benchmark.py \
  && echo 'def test_b(): pass' > dupcheck/m49/test_benchmark.py && pytest dupcheck -q
ERROR collecting dupcheck/m49/test_benchmark.py
import file mismatch: imported module 'test_benchmark' has this __file__ attribute: …/m4/test_benchmark.py
HINT: … use a unique basename for your test file modules
```

**Suggested fix.** One sentence in §10: files added under `tests/frozen/core/m49` and
`tests/frozen/preserve/m50` MUST carry basenames unique across their whole *package* subtree
(`core`, `preserve` are collected per package, not per milestone —
`scripts/run-tests.sh:15-24,29`); name them e.g. `test_variation_benchmark.py`,
`test_varied_bundle_reproduce.py`, `test_varied_inspect.py`. (`frontend/m48`, `frontend/m49` and
`awkward/m51` are safe — those packages run per milestone.)

---

## MID-5 — §4.3's bound extraction mechanism names a channel that is not a bound public API, and misdescribes the alternative that is

**Section:** §4.3 (lines 739–751) and the m48 §4.3 anchor (lines 1447–1453).

**Detail.** §4.3 binds the anchor's operands: "`fill_node[label]` comes from the §6.1c per-slot
output indices / §7.2 `(output, label) → node id` map, **the only public per-label fill-node
channel** (`Histogram._fill_nodes` is private)". Two problems for a test-author:

1. §7.2 never binds that map as a *public API with a pinned spelling* — it says only "the frontend
   owns `(output, label) → node id`", and every other new surface in this plan carries an explicit
   "spelling pinned at m48/m50/m51 freeze" clause. A frozen test cannot import an unnamed internal.
2. `Histogram._fill_nodes` being private is true but the stated consequence is not: a **public**
   accessor `Histogram.fill_nodes() -> list[Array]` exists
   (`graphed-histogram-latest/src/graphed_histogram/boost.py:218-219`, alongside
   `staged_fills()` `:215-216` and `evaluators()` `:221-223`). What it does *not* give is the
   label↔node correspondence, and the plan binds no rule pairing staged-fill order with
   `graphed.labels` order — so neither route is usable as written.

Secondary note, in favour of the mechanism: `session.walk` *can* serve as the reachability
primitive with side-effecting handlers, but it takes an **`Array`**, not a node id
(`python/graphed/session.py:245-252`, `root = array.node_id` at `:269`). Reconstructing
`graphed.Array(session, nid)` is possible (`array.py:133-135`; `Array` is exported,
`python/graphed/__init__.py:9,29`), but that is worth one sentence rather than a mid-freeze
discovery — the same service §4.1's `full_like` note and §2.6's `lhe_w[:, i]` note already provide.

**Suggested fix.** In §7.2, pin the accessor spelling at m48 freeze (e.g.
`graphed_histogram.fill_nodes_by_label(h) -> dict[str, Array]`, or a `labels=` return from the
group API), and in §4.3 replace "the only public per-label fill-node channel
(`Histogram._fill_nodes` is private)" with the accurate statement: `fill_nodes()` is public but
carries no labels, hence the m48 accessor; and note the `Array(session, node_id)` wrapping needed
to call `session.walk` on a node id.

---

## MID-6 — the bound cross-repo dependency edits are incomplete: the corpus/histogram packages are git-only and their CI install lines are not bound

**Section:** §10/m48 ("m48 adds `graphed-corpus` to `graphed-histogram`'s `dev` extra AND vendors
the 23 reference JSONs there the way `graphed` already does", lines 1423–1426) and §10/m49(ii)
("m49 adds `graphed-histogram` to `graphed-executors`' `dev` extra", lines 1643–1644).

**Detail.** The plan closed the "headline anchor would `importorskip`-SKIP in CI" hazard carefully,
but the replacement edits it binds do not stand alone:

- `graphed-corpus` is **not resolvable by name** in this org's CI: the working precedent installs it
  from a git URL first — `graphed-exec-check/.github/workflows/ci.yml:17`
  `CORPUS: "graphed-corpus @ git+https://github.com/graphed-org/graphed-corpus-mvp@main"`, then
  `:38,65,94,136` `pip install "${{ env.GRAPHED }}" "${{ env.CORPUS }}"` **before**
  `pip install -e ".[dev]"`. `graphed-histogram`'s workflow has no such env/line
  (`graphed-histogram-latest/.github/workflows/ci.yml:13-17,38,65`), so a bare `graphed-corpus`
  added to its `dev` extra fails to resolve at install time.
- "the way `graphed` already does" is in fact the **vendor-only** pattern, not a dependency:
  `graphed` has **no** `graphed-corpus` in any extra and no corpus install in CI — it vendors the
  whole package (`graphed-latest/tests/_corpus/graphed_corpus` + `tests/_corpus/references`, 23
  JSONs) with `tests/_corpus` on `pythonpath` (`pyproject.toml:117`). So the plan's "dev extra AND
  vendor" mixes two mechanisms, one of which the cited precedent does not use.
- The same shape applies to m49(ii): `graphed-executors`' CI env has `GRAPHED` and `CORPUS` only, no
  histogram URL (`graphed-exec-check/.github/workflows/ci.yml:13-17`).

This is not a silent failure (it is a red install), but it lands on the milestone's *headline*
anchor at freeze time, which is what the plan's own fixture analysis exists to prevent.

**Suggested fix.** Bind the edit as a pair, per repo: the `dev`-extra name **plus** a CI env git URL
and its `pip install` line in every job that runs the frozen suite (the
`graphed-exec-check/.github/workflows/ci.yml:17,38` pattern) — or, simpler and matching the cited
`graphed` precedent exactly, vendor `graphed_corpus` + `references` under
`graphed-histogram/tests/_corpus` and add it to that repo's `pythonpath`
(`graphed-histogram pyproject.toml:50`), taking no new dependency at all.

---

## LOW-7 — §6.2's "direct discriminator" catches only *under*-declaration; over-declaration passes it

**Section:** §6.2(i)/(ii) and the m50 "§6.2 declaration contract" anchor (lines 1682–1695).

**Detail.** The anchor says the declared bin set equals the inferred label set exactly "with the
direct discriminator that `h.sum(flow=True) == h.sum()` (a **stale** or partial declaration
otherwise buries the difference in the overflow bin)". Measured: a *partial* declaration is caught;
a *stale/over*-declaration (a bin declared that no fill reaches) is invisible to it.

**Evidence (measured, boost_histogram 1.8.0).**

```
StrCategory(['nominal','jes_up','jes_down','stale_extra']), fill 3 real labels
  -> sum 3.0, sum(flow=True) 3.0, equal: True      # over-declaration NOT caught
StrCategory(['nominal','jes_up']),                fill 3 labels
  -> sum 2.0, sum(flow=True) 3.0                   # under-declaration caught (plan's number)
```

**Suggested fix.** Keep the flow check (it is the right under-declaration witness) and add the
equality that actually closes the set: assert the axis's bin tuple equals a **literally spelled**
expected label list in the test (not one read back from the same histogram or from
`graphed.labels(h)`, which §6.2(i-bis) defines *as* the axis bin set and would make the assertion
circular). Drop "stale" from the discriminator's description.

---

## LOW-8 — m50's structural scaling anchor has one half with no observation seam

**Section:** m50 anchor "per partition, axis mode allocates **1 histogram object** and ships 1
combine payload entry vs `N+1` in sibling mode (countable at the `FillEvaluator`/`_GroupReduce`
seam, `boost.py:100-117`)" (lines 1707–1712).

**Detail.** The payload half is countable from the plan's own per-partition result: the reducer
returns a mapping and `len()` of it is `1` vs `N+1` (`_GroupReduce.__call__`,
`graphed-histogram-latest/src/graphed_histogram/boost.py:100-117`). "Allocates 1 histogram object"
has no such seam — counting allocations in a frozen test needs monkeypatching production code or
a `gc`/`tracemalloc` heuristic, both fragile across the §A.5 matrix and neither bound anywhere.

**Suggested fix.** Word the anchor over the countable invariant only ("ships exactly 1 combine
payload entry per partition, vs `N+1` in sibling mode, plus bin-for-bin equality"), and leave the
object-count claim to the R0.11 implementer report where §3.3 already sends the wall-clock half.

---

## LOW-9 — m48's §1.2 anchor is worded unscoped, while §1.2's own §6.2 carve-out makes the wording false in axis mode

**Section:** m48 anchor "§1.2 label-out-of-identity" (lines 1454–1460) vs §1.2's carve-out
(lines 318–321) and §6.2.

**Detail.** The anchor reads "**for a varied program**, NO node in the store carries any label
string in its params or token, AND renaming every label leaves `compile_ir(...).ir` byte-identical".
In m50's axis mode both clauses are false **by design** — labels become StrCategory bin identities
inside the spec, which is hashed into node params (`content_hash(self._spec)`, `params={"spec": …}`,
`graphed-histogram-latest/src/graphed_histogram/boost.py:180-212`). The frozen test itself stays
green (its program is sibling-mode and fixed at m48), so this is a wording hazard, not a breakage —
but every other anchor with the same exposure carries the scoping clause explicitly (§6.1a
"in SIBLING mode", §6.1b/m49 arity, §6.1c "worded over the fill-node count, not over 'a varied
Histogram'"), and this one was left general.

**Suggested fix.** Add the same four words: "…for a varied program **in the default sibling
lowering**…", with the §1.2 carve-out cross-referenced, so no test-author generalises it into a
store-wide invariant that m50 must contradict.

---

## LOW-10 — §8.2's new read-only core accessor is an m49 Implementation Target with no anchor in the repo that owns it

**Section:** §8.2(i) (lines 1279–1300); m49 anchor list.

**Detail.** r12 scopes a **new read-only `graphed-core` accessor** returning
`record_node_id -> (reduced_node_id, member_index | None)` as an explicit m49 Implementation Target
(Rust + PyO3 in the consolidated `graphed` repo). m49's `graphed` half is enumerated as "§5.2a arena
delta, §5.2c stage shape, §3.4 impact sets, §5.3 projection, §5.4 refusal, §3.3 benchmark" — none of
which touches the accessor; the only anchors that exercise it are the cross-process `StageError`
anchors, which the plan places in `graphed-executors`' flat `tests/frozen/m49`. The DoD requires
≥90 % line+branch **diff** coverage with covering hits from the **frozen** suite of the repo the
code lands in, so the accessor risks landing uncovered where it lives — and, more to the lens,
its own correctness (fusion collapses a universe's chain into one `Stage`, so most record ids have
**no** reduced id of their own — the plan says so at lines 1289–1291) is never asserted.

**Suggested fix.** Add one m49 anchor in `graphed` (`tests/frozen/frontend/m49` or
`tests/frozen/core/m49`) over the §3.3 builder topology: every surviving record id maps to a
`(reduced_id, member_index)` whose reduced id is in the compiled output/stage set; a DCE-eliminated
record id maps to `None`; and two labels' shared node maps to one reduced id. That is also the
non-vacuity witness for §8.2's keying claim, which is otherwise asserted only indirectly through a
`StageError` string in another repo.

---

## Verdict — DIRTY (one determinism-compatibility defect + one traceability gap; both cheap to fix)

The suite skeleton is in good shape overall. The traps the plan documents for itself are genuinely
closed: the m51 superset anchor is based on an eager, out-of-graphed reference rather than the
self-derived `OR(masks) == OR(masks)` form; §4.3 is structural rather than the equal-counts
tautology; §5.2a carries a literal expected integer travelling with a fully specified builder;
§3.3 is the single, explicitly named R0.10a carve-out and every other performance claim (§6.2 axis
scaling, §6.4c compression, the N≈100 comparison) is demoted to an R0.11 implementer measurement;
the three dynamic gates carry an explicit non-vacuity floor and a bound discovery rule; and the
sibling-vs-axis-mode scoping now protects m48/m49 anchors from m50's contradictions. I found no new
tautology of the §4.3/§5.2a class, no wall-clock or size threshold hiding in a frozen anchor, and no
anchor left describing r8-era p-form semantics after the r9 e-form switch.

What blocks a clean round is narrower:

- **HIGH-1** is a contradiction *between two binding requirements* — §8.2(i)'s `frozenset` field
  cannot coexist with §3.2's cross-process determinism form, and nothing in m48–m51 would surface
  it before the mechanical determinism gate goes red (or, worse, before checkpoint reuse silently
  stops hitting). One-word fix in §8.2(i), plus one plan-bytes anchor in m49.
- **HIGH-2** is the plan's own r12 standard applied to r12's own additions: §2.3d and §2.2's
  reserved names were introduced *as* silent-corruption guards and were not anchored, so they can
  ship unimplemented with every m48 anchor green.

The four MIDs are all buildability rather than semantics — a discrimination gap in the JER fixture,
two fixture/CI mechanics that would burn a freeze-time round each, and one anchor whose named
operand channel does not exist as a public API. Fixing HIGH-1, HIGH-2 and MID-3 is what I would
require before m48 test-authoring starts; MID-4/5/6 and the LOWs are editorial once decided.
