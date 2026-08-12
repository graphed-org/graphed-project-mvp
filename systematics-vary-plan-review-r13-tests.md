# systematics-vary plan — review round 5, TEST ARCHITECTURE lens

- **Lens**: test architecture (non-vacuity/discrimination, R0.10 mechanism witness, R0.10a
  deterministic-invariant rule, determinism-gate compatibility, freeze-order hazards, requirement↔anchor
  traceability, buildability of the fixtures the anchors presuppose).
- **Document reviewed**: `systematics-vary-plan.md` **revision r13** (read in full: Part I, PART II §§1–12,
  §10 milestones, Anchors appendix, revision history).
- **Date**: 2026-07-30.
- **Verification roots used** (all code facts below come from these, never from the stale submodules):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607`) — incl. its `.venv`, used
    to re-run the §3.3/§5.2a topology probe.
  - `/private/tmp/claude-501/graphed-exec-check` (`graphed-executors`, `201ea42`).
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`).
  - `/private/tmp/claude-501/uproot5-graphed` (uproot fork, `graphed-mvp`, `393ecef`).
  - `graphed-root-prompt.md` (R0.10 / R0.10a / R0.11 text read at `:196-220`).
  - PyPI project metadata for `graphed-histogram` / `graphed-executors` / `graphed-corpus` (fetched
    in-session).
- Owner-locked decisions were treated as fixed; nothing below asks for a different choice.

Findings are ordered by severity. Every one carries evidence I produced in this session.

---

## HIGH

### H1 — m48's §2.3d anchor freezes a refusal-message contract that contradicts §2.3d/§5.4 for five verbs (and pre-empts an m49 anchor)

**Section**: §10/m48 "§2.3d module-verb dispositions" bullet vs §2.3d and §5.4.

**Detail.** The m48 anchor says: *"every refusing verb (`join`, `repartition`, `pack_key`,
`shuffle_plan`, `join_plan`, `compile_ir`, `evaluate_ir`, `aggregate_plan`) raises a `graphed` error
naming `graphed.universe`"*. But §2.3d binds a **different** contract for the first five: *"`graphed.join`
and `graphed.repartition` **refuse** with the §5.4 error; `graphed.pack_key`, `graphed.shuffle_plan` and
`graphed.join_plan` refuse likewise … one refusal message covers all three"*, and §5.4's error is a
*"clear `NotImplementedError` naming the label and the boundary"*. Only `compile_ir`/`evaluate_ir`/
`aggregate_plan` are bound to *"an error naming `graphed.universe`"*.

The two are not satisfiable together: `NotImplementedError` is a builtin and `GraphedError(Exception)` is
graphed's own base class — measured, `python/graphed/errors.py` defines `class GraphedError(Exception)` and
`class GraphedTypeError(GraphedError)`, with no relation to `NotImplementedError`. And the message contents
differ (label+boundary vs `graphed.universe`).

Freeze-order makes it worse: §10/m48 itself states that *"the **behaviour** of the `refusing` class is an
m49 anchor, since §5.4 (the refusal message and its positive control) is an m49 target"*. So m48 would
freeze a message contract for `graphed.join`/`graphed.repartition` that m49's §5.4 anchor is separately
bound to pin — the r7-sweep hazard class (freezing a superseded contract into a read-only test).

**Evidence.** Plan `:1667-1669` (m48 anchor), `:486-497` (§2.3d), `:835-840` (§5.4), `:1710-1711` (the
"m49 owns the refusing behaviour" sentence); `/private/tmp/claude-501/graphed-latest/python/graphed/errors.py`
(class hierarchy, read in full).

**Suggested fix.** Split the m48 anchor's refusal table by contract, exactly as §2.3d does: the
boundary/plan verbs (`join`, `repartition`, `pack_key`, `shuffle_plan`, `join_plan`) assert the §5.4 error
shape; the compile/evaluate/aggregate verbs assert the `graphed.universe` error. And state which milestone
owns which message — if §5.4's message is m49's, m48's anchor for those five must assert only *that it
refuses* (type + "does not silently compile"), leaving the message text to m49.

---

### H2 — §5.2a's arena-delta witness (the plan's headline "sharing engaged" R0.10 witness) is satisfiable without ever calling `graphed.vary`

**Section**: §5.2(a) + §3.3 + §10/m49.

**Detail.** §5.2(a) binds the sharing witness *"on the §3.3 topology … going N=1→2 adds exactly `K + 2 = 52`
nodes"*. §3.3 specifies that topology purely as a **graph** ("source → a shared prefix of D ops → per
universe {one varied fork op, K chain ops, exactly one terminating reduction node}") and tells the author to
replicate `tests/frozen/core/m4/test_benchmark.py`, which is a **raw-core** builder: measured,
`tests/frozen/core/m4/test_benchmark.py` and `test_systematics.py` both `import graphed.core as gc` and build
with `GraphStore.add_source/add_op` — no frontend, no `Array`, no `vary`.

I re-ran the topology against `graphed-latest` through the **raw `GraphStore` API** and reproduced every
pinned integer exactly:

```
N=16  -> reduced_nodes 34,  stages 17
N=128 -> reduced_nodes 258, stages 129
arena delta N=1->2 (with terminating reduction)    : 52
arena delta N=1->2 (without terminating reduction) : 51
```

So a test-author can write §5.2a with `graphed.core.GraphStore` directly, pass every pinned number, and
witness **nothing about `vary`** — it would witness `GraphStore::intern`, which m1/m4 already freeze
(`tests/frozen/frontend/m2/test_recording.py:25-28` pins re-recording adds no node; m4 pins
variation-count-independent reduction). A `vary` implementation that re-recorded the *shared prefix* per
universe would still pass a raw-core-built anchor. That is precisely the R0.10 semantic-stub shape
("asserting only … equivalence for such a requirement is a test-sanity failure").

The plan half-hints at the right answer by assigning §5.2a to `tests/frozen/frontend/m49` while the §3.3
benchmark goes to `tests/frozen/core/m49` — but it never says the witness is built **through the public
`vary` surface**, and the number it pins was measured at the core level.

**Evidence.** Plan `:812-820` (§5.2a), `:704-717` (§3.3), `:1829-1830` (m49 split);
`graphed-latest/tests/frozen/core/m4/test_benchmark.py:1-20` and `test_systematics.py:1-25` (raw
`graphed.core` builders); my probe above run with `graphed-latest/.venv/bin/python`;
`graphed-latest/python/graphed/session.py:50-51` (`Session.node_count()` exists, so a frontend-built arena
delta IS buildable).

**Suggested fix.** Bind §5.2a explicitly: *the delta is measured on a program built with `graphed.vary`
through the public frontend (`Session.node_count()` before/after adding the second label), on the §3.3
topology's shape*; and state that the raw-`GraphStore` construction is the **benchmark's** (§3.3) builder,
not the witness's. Ideally re-measure Δ once through the frontend and record it, since the pinned 52 is
currently a core-level measurement.

---

### H3 — m49(ii)'s bound fixture edit installs the wrong `graphed-histogram` (and lacks the "no `importorskip`" clause its sibling anchor carries)

**Section**: §10/m49 anchor (ii).

**Detail.** The plan binds: *"**m49 adds `graphed-histogram` to `graphed-executors`' `dev` extra** and
compares against corpus references recomputed in-process via `graphed_corpus`"*. That is a **name-only**
dependency — the exact mechanism r13 measured to be insufficient for this org and corrected for m48
("A dependency edit alone also would not install … the working precedent pre-installs it from a git URL via
a workflow env var BEFORE `pip install -e .[dev]`"). For `graphed-histogram` the failure mode is subtler
than for the corpus, and worse:

- `graphed-histogram` **is** on PyPI: fetched in-session, `graphed-histogram 0.0.1`, homepage
  `github.com/graphed-org/graphed-histogram`. So the name-only dep *resolves* — to the **released 0.0.1**.
- The repo's own version is also `0.0.1` (`graphed-histogram-latest/pyproject.toml`, `version = "0.0.1"`),
  so the release is not distinguishable from, and predates, m48's varied-fill work.
- `graphed-executors`' workflow pre-installs only `GRAPHED` (git@main) and `CORPUS` (git URL) —
  `graphed-exec-check/.github/workflows/ci.yml:14-16`, installed at `:38`. Nothing pulls
  `graphed-histogram` from HEAD.

m49(ii) exists to exercise **§4.2/§6.1's varied-fill lowering** through a real executor. Against PyPI
0.0.1 `Histogram.fill` does not accept `Varied` at all, so the anchor cannot pass — and because m49(ii)
(unlike m49(i) and m48's matrix) carries **no "MUST NOT be guarded by `importorskip`" clause**, the path of
least resistance for a test-author is an `importorskip`/skip that silently discharges the executor-level
systematics end-to-end the plan calls *"the executor-level systematics end-to-end no frozen test currently
discharges"*.

**Evidence.** Plan `:1838-1845` (anchor (ii)), `:1581-1591` (r13's own binding for the m48 case);
PyPI JSON for `graphed-histogram` (name/version/homepage) fetched in-session;
`graphed-histogram-latest/pyproject.toml` (`version = "0.0.1"`);
`graphed-exec-check/.github/workflows/ci.yml:12-16,34-38,44`.

**Suggested fix.** Bind the pair, exactly as r13 did for m48: a `HISTOGRAM: "graphed-histogram @
git+https://github.com/graphed-org/graphed-histogram@main"` env var plus its `pip install` line in **every**
`graphed-executors` job that runs `tests/frozen` (`ci.yml:38` and the other `pytest tests/frozen`
invocations at `:67`, `:101`), alongside the dev-extra name; and add the "MUST NOT be `importorskip`-guarded"
clause to anchor (ii).

---

### H4 — the §2.3d discovery rule under-fires on four of the verbs the same anchor enumerates, and over-fires on a verb m48 itself introduces

**Section**: §2.3d + §10/m48 "§2.3d module-verb dispositions" anchor.

**Detail.** The rule: *"the m48 anchor enumerates `graphed.__all__` dynamically, filtered to callables whose
**FIRST positional parameter is annotated `Array`**, and asserts every discovered verb carries a
disposition — so a verb added later cannot arrive undisposed"*. Measured signatures in `graphed-latest`:

| verb | first positional parameter | discovered by the rule? |
|---|---|---|
| `join(left: Array, right: Array, …)` `shuffle.py:92` | `Array` | yes |
| `repartition(array: Array, …)` `shuffle.py:68` | `Array` | yes |
| `pack_key(array: Array, *, on)` `shuffle.py:84` | `Array` | yes |
| `shuffle_plan(output: Array, …)` `shuffle.py:142` | `Array` | yes |
| `join_plan(output: Array, …)` `shuffle.py:208` | `Array` | yes |
| `compile_ir(session: Session, *outputs: Any, …)` `execute.py:54-58` | `Session` | **no** |
| `evaluate_ir(compiled: CompiledGraph \| bytes, …)` `execute.py:85-90` | `CompiledGraph \| bytes` | **no** |
| `read_columns(arrays: Sequence[Array], source_nid: int)` `projection.py:109` | `Sequence[Array]` | **no** |
| `apply(fn: Callable[..., object], *arrays: Array, …)` `array.py:397` | `Callable` | **no** |
| `aggregate_plan(*outputs: Array, …)` `aggregate.py:68` | VAR_POSITIONAL `Array` | ambiguous |

So the "self-repairing, cannot silently miss a verb" gate misses **four of the ten** dispositions §2.3d
states and that the same m48 bullet asserts behaviour for — the test-author must hand-write them, which is
the literal list the rule was introduced to replace, and a future verb taking `Sequence[Array]` or an Array
in second position still arrives undisposed.

Conversely the rule **over**-fires: §6.1d introduces **`graphed.broadcast_like(value, factor) -> Array`**
in m48, a public neutral verb whose first positional parameter is an `Array` — it will be discovered, and
§2.3d gives it no disposition. As worded, the frozen gate ("every discovered verb carries a disposition")
goes red against a correct m48 implementation.

**Evidence.** Plan `:501-505` (the rule), `:1664-1673` (the anchor), `:959-960` (`broadcast_like`);
`graphed-latest/python/graphed/__init__.py:8-58` (exports/`__all__`), and the signature lines cited in the
table, all read in-session.

**Suggested fix.** Replace the annotation filter with one that matches the measured surface — e.g. "every
callable in `graphed.__all__` whose signature mentions `Array` in any parameter annotation (including
`Sequence[Array]`, `*args: Array`) or that is named in §2.3d" — and give `graphed.broadcast_like` an explicit
disposition in §2.3d (it is *broadcast*, or explicitly exempt as a seam). Keep the non-vacuity floor
(discovered set ⊇ the freeze-time enumerated verbs).

---

## MID

### M1 — the §6.4e sorted-manifest determinism rule, newly bound in r13, has no m51 anchor; the only byte-identity anchor is on the manifest-free path

**Section**: §6.4e / §10/m51.

**Detail.** r13 bound: *"the manifest maps each label to its stored column/branch names and per-column
representation, **serialized with SORTED keys** … a manifest serialized in set/dict-iteration order would make
the written bytes depend on `PYTHONHASHSEED`"*. Every m51 anchor that touches the manifest is content-only:
*"parquet KV metadata lists exactly the appended labels/columns/representations and reads back"* — which a
hash-order serialization satisfies perfectly. The one byte-identity anchor m51 does carry is explicitly the
**unvaried** write ("carries NO manifest, and is byte-identical to today — as a SAME-PROCESS comparison"),
so it can never see the varied path's manifest bytes.

This is the same defect shape r13 caught for §8.2(i)'s `frozenset` (and fixed with a plan-byte determinism
anchor in m49): a determinism requirement whose violation is invisible to every content-level assertion.

**Evidence.** Plan `:1263-1270` (§6.4e sorted keys), `:1997-2005` (m51 manifest + byte-identity anchors),
`:1880-1884` (the m49 precedent anchor r13 added for the analogous `frozenset` case).

**Suggested fix.** Add an m51 anchor mirroring m49's: the same varied write performed in **two fresh
processes under differing `PYTHONHASHSEED`** produces byte-identical manifest bytes (and, if the writer is
otherwise deterministic, byte-identical files); or, minimally, assert the manifest's serialized key order is
sorted.

---

### M2 — m49's anchor→repo/directory partition is incomplete, and the fill-shaped leftovers hit the fixture fact the plan measured twice

**Section**: §10 (directory pins) + §10/m49.

**Detail.** §10 pins m49 to `tests/frozen/frontend/m49` (graphed), `tests/frozen/core/m49` (benchmark),
`graphed-histogram tests/frozen/m49`, `graphed-executors tests/frozen/m49`, and then partitions only two
anchors explicitly ((i) matrix → graphed-histogram, (ii) executor matrix → graphed-executors) plus a
parenthetical listing six anchors for `graphed`'s frontend/m49 (§5.2a, §5.2c, §3.4, §5.3, §5.4, §3.3).
Unassigned m49 anchors:

- **§2.4/§6.1b structural arity** (`1 + |S| + |W|` fill nodes, *"frozen-counted via the staged-fill list"*) —
  this needs `graphed_histogram.Histogram`; measured, `staged_fills()`/`fill_nodes()` live at
  `graphed-histogram-latest/src/graphed_histogram/boost.py:215-219`. Placed in `graphed` by default it hits
  the plan's own measured fixture fact (`graphed` has no `graphed-histogram` in any extra;
  `graphed-latest/pyproject.toml` dev extra = `boost-histogram>=1.4`, `hist>=2.7`) and becomes an
  `importorskip` skip.
- **§7.3 interrupt/resume byte-identity** and **§7.4 dead-letter label** — the machinery is
  `graphed-latest/python/graphed/checkpoint/runner.py` and the frozen home for it is
  `tests/frozen/checkpoint/{m8,m39}`; §10 pins **no** checkpoint directory for m49.
- **§8.1 `__hash__`**, **§8.2 cross-process labeled StageError**, **§8.2 multi-label rendering** — no repo
  named. (`graphed` *can* host a cross-process test — `tests/frozen/debug/m6/test_process_boundary.py:15-17`
  uses `mp.get_context("spawn")` directly — but the plan should say so, since it elsewhere argues `graphed`
  ships no `Executor`.)

There is also a **direct contradiction** on §3.3's location: `:1495` pins the benchmark to
`tests/frozen/core/m49`, while `:1830` lists "§3.3 benchmark" among what `tests/frozen/frontend/m49`
"keeps". Those are different pytest processes with different basename rules (see M3).

**Evidence.** Plan `:1493-1496`, `:1829-1830`, `:1861-1890`; `graphed-histogram-latest/src/graphed_histogram/boost.py:215-219`;
`graphed-latest/pyproject.toml` dev extra; `graphed-latest/tests/frozen/checkpoint/{m8,m39}` listings;
`graphed-latest/tests/frozen/debug/m6/test_process_boundary.py:15-17`.

**Suggested fix.** Extend m49's per-repo partition to every anchor (as r13 did for m48): send §6.1b's arity
count to `graphed-histogram`'s `tests/frozen/m49`; pin a `tests/frozen/checkpoint/m49` for §7.3/§7.4 (see M3
for its basename constraint); name the repo for the §8.x anchors; and fix the §3.3 location to one directory.

---

### M3 — the r13 unique-basename rule stops at `graphed`; `graphed-histogram`, `graphed-executors` and `graphed`'s own checkpoint subtree have the identical hazard

**Section**: §10 (frozen layouts).

**Detail.** r13 bound unique basenames for `tests/frozen/core/m49` and `tests/frozen/preserve/m50` because
those suites run as ONE pytest process with no `__init__.py`. The same is true of the other repos the plan
adds directories to, and the plan says nothing:

- `graphed-histogram`: CI runs `pytest tests/frozen` (one process) — `.github/workflows/ci.yml:44`;
  `find tests -name __init__.py` → **0**; `testpaths = ["tests"]`. §10 adds **three** new flat dirs there
  (`m48`, `m49`, `m50`) whose natural file names collide with each other (m48's corpus-matrix file and
  m49's corpus-matrix file are the same natural basename) and with the existing
  `tests/frozen/m23/test_group_plan.py` / `m29/test_multi_weight_fills.py`.
- `graphed-executors`: `pytest tests/frozen` at `.github/workflows/ci.yml:44` (also `:67`, `:101`);
  `find tests -name __init__.py` → **0**; a new flat `tests/frozen/m49` joins 17 existing milestone dirs.
- `graphed`'s **checkpoint** subtree (where M2 says §7.3/§7.4 belong) is not a `SPLIT_PKG`
  (`scripts/run-tests.sh:30`, `SPLIT_PKGS="frontend numpy awkward"`) and already contains
  `tests/frozen/checkpoint/m8/test_resume.py` — the single most natural name for an m49 resume anchor.

Additionally, §10's "any helper imported ACROSS those directories must be added to `pythonpath`" rule is
stated only for `graphed`. `graphed-histogram`'s `pythonpath = ["src", "tests/frozen/m23"]` and
`graphed-executors`' `pythonpath = ["src", "tests/frozen/m7", …]` show the same convention is load-bearing
there; a shared `vary` fixture module in either repo needs the same edit.

**Evidence.** `graphed-histogram-latest/.github/workflows/ci.yml:44`, its `pyproject.toml`
(`testpaths`, `pythonpath`), `find tests -name "__init__.py" | wc -l` → 0;
`graphed-exec-check/.github/workflows/ci.yml:44,67,101`, `pyproject.toml:52-55`, `find` → 0;
`graphed-latest/scripts/run-tests.sh:16-25,30`; `graphed-latest/tests/frozen/checkpoint/m8/` listing.

**Suggested fix.** Generalize the r13 sentence: *files under any newly created frozen milestone directory in
`graphed-histogram`, `graphed-executors`, `graphed`'s `core`/`preserve`/`checkpoint` subtrees, and
`uproot5-graphed-mvp` MUST carry basenames unique across the whole pytest-process scope*, with the same
`pythonpath` clause for cross-directory helpers in each repo.

---

### M4 — §3.4's API lands in m48 with no m48 frozen anchor

**Section**: §10/m48 targets vs §3.4.

**Detail.** m48's targets are *"§1, §2 …, §3.2/**§3.4 (API only)**, §4, §6.1 …"* while §3.4 says it *"is
frozen-anchored in m49"*, and m49's targets repeat *"§3.4 (frozen anchor)"*. No m48 anchor exercises the
impact-set helper: §4.3's impact-set form is explicitly optional (*"MAY ride along"*). The per-milestone DoD
requires *"≥90% diff coverage **from the frozen suite**"* — new m48 source with zero m48 frozen coverage
either fails that gate or gets discharged by `tests/extra`, which the DoD forbids as the covering source.

**Evidence.** Plan `:1532-1535` (m48 targets), `:727-733` (§3.4), `:795-797` ("MAY ride along"),
`:2016-2019` (DoD restatement).

**Suggested fix.** Either move the §3.4 API to m49's targets (its anchor already lives there), or make the
§4.3 impact-set cross-check a **required** m48 anchor rather than an optional rider.

---

### M5 — the m48 `graphed.labels(ctx)` anchor exercises only two of the three union terms r13 bound

**Section**: §2.2 (r13 context-label rule) + §10/m48 event-context anchor.

**Detail.** §2.2 now binds `graphed.labels(ctx)` = §2.4-ordered union of **(a)** ambient-weight labels,
**(b)** the labels of any `Varied` collections on the context, **(c)** the derivation mask's labels. The m48
anchor asserts it *"on a program that registers a weight BEFORE the derivation, so the answer is
ambient-weight labels ∪ the mask's labels"* — i.e. (a) ∪ (c). In that program the collection labels (b) are a
**subset of the mask's labels** (the mask is varied *because* the collection is), so an implementation that
computes `ambient ∪ mask` and drops term (b) passes.

The discriminating case is real and mainline: `events = graphed.vary(events, "jes", Jet={...})` followed by a
derivation on an **unvaried** mask (`sel = events[gak.num(muons) >= 2]`). Term (b) is then the only source of
the `jes_*` labels, and the "superset of any §6.1d fill's label set" property — the whole point of the r13
rule — fails silently. That is the §2.5 confidently-wrong class the rule exists to delete.

**Evidence.** Plan `:392-399` (§2.2 r13 union), `:1777-1780` (the m48 anchor wording).

**Suggested fix.** Add the second program to the same anchor: a shift-varied collection plus an **unvaried**
derivation mask, asserting `graphed.labels(ctx)` still reports the collection's labels (and that it is a
superset of the label set a fill from that context produces).

---

## LOW

### L1 — §10/m48's §4.3 bullet still reaches for "the §7.2 map", which r13 established is not an importable surface

**Detail.** r13 corrected §4.3 to obtain per-label fill nodes through a **new §9.1 accessor**
(`graphed_histogram.fill_nodes_by_label(h)`-shaped), precisely because *"§7.2 says only that the frontend
owns the `(output, label) → node id` map — ownership is not an importable surface, and a frozen test cannot
import an internal"*. The §10 anchor bullet was not updated: it still reads *"`fill_node[label]` from the
§7.2 map"*.

**Evidence.** Plan `:1612-1618` (m48 anchor bullet) vs `:788-795` (§4.3 r13) and `:1465-1471` (§9.1 accessor).

**Fix.** Point the anchor at the §9.1 accessor by name.

### L2 — §5.2c ("reduced-stage shape") names no program and no expected value, and duplicates §3.3

**Detail.** §5.2(c) is one clause — *"reduced-stage shape — the shared prefix appears in exactly one stage"* —
and the m49 list carries it as *"§5.2 witnesses (a: …; c: reduced-stage shape)"*. Every other m49 anchor names
its program and its literal expectation. On the §3.3 topology this is already pinned as `stages == N + 1`
(re-measured above: N=16 → 17, N=128 → 129), so as written it is either a duplicate of the §3.3 assertion or
an unspecified test on an unspecified program.

**Evidence.** Plan `:825-826`, `:1861`; my probe output above.

**Fix.** Either bind §5.2c to a named program with a literal stage count (e.g. the corpus shift program: the
shared prefix is one stage, each universe one stage), or fold it into §3.3 and delete the separate anchor.

### L3 — m50's scaling anchor is phrased against a mapping whose keys are output names today

**Detail.** *"axis mode ships 1 combine payload entry vs `N+1` in sibling mode — the length of
`_GroupReduce.__call__`'s returned `{label: histogram}` mapping (`boost.py:100-117`)"*. Measured, that
mapping's key today is the **output name**, not a variation label: `layout = tuple((label, len(h._fill_nodes),
h._spec) for label, h in items)` where `items` are `(output_name, Histogram)` pairs
(`graphed-histogram-latest/src/graphed_histogram/boost.py:255-292`). The count "1 vs N+1" therefore only
holds once §6.1c's two-level `{(output, label): hist}` shape exists. The anchor is structural and R0.10a-safe
(good), but a test-author reading `boost.py` will find the current key means something else.

**Fix.** Say "the per-partition combine payload under §6.1c's two-level key shape (one entry per
(output, label))" and pin the output count as 1 in the fixture.

### L4 — several §§1–9 "frozen m49 anchors" never reach §10's m49 list

**Detail.** §8.2 states its own anchors inline (*"Frozen m49 anchors: … **plus a shared-node failure asserting
the multi-label rendering** — without it the single-label anchor passes under a pick-one-arbitrarily
implementation"*). §10's m49 list carries only *"§8.2 cross-process labeled StageError (incl. §7.4
dead-letter label)"*. Since §10 is described as *"the acceptance skeleton the test-author starts from"*, the
discriminating half of that anchor is easy to lose.

**Evidence.** Plan `:1438-1443` vs `:1885-1886`.

**Fix.** Mirror the multi-label-rendering clause into §10's m49 bullet (one line).

---

## NIT

### N1 — `read_columns` is filed under "expanding verbs return the bound per-label shape"

§2.3d says `read_columns` returns *"the union over all labels' members"* — a single column tuple, not a
per-label shape. The m48 anchor's phrase *"every expanding verb (`apply`, `read_columns`) returns the bound
per-label shape"* reads as if both return per-label results. One word ("its bound expanded shape") fixes it.
Plan `:493-495`, `:1670`.

---

## Items checked and found CLEAN (no finding)

Recorded so the next round does not re-litigate them:

- **R0.10a compliance.** Only one frozen wall-clock gate exists in m48–m51 (§3.3's `time(128)/time(16) <
  24.0`), it is named as a deliberate carve-out, it is grounded in the pre-existing frozen precedent I
  verified (`tests/frozen/core/m4/test_benchmark.py:36-42`, same `base = max(times[SIZES[0]], 1e-4)` /
  best-of-N shape), and its headroom is stated (≈5.4 measured vs 24.0). No absolute per-size wall-clock
  budget is added (the m4 precedent's `elapsed < 1.0` is *not* replicated). Every other perf claim is demoted
  to R0.11 reports — §6.2 scaling (structural payload count), §6.4c compression, m50's wall-clock and, in
  r13, the allocation-count half. No size thresholds appear in any frozen anchor.
- **Determinism-gate compatibility.** §3.2's m48 anchor and m49's plan-byte anchor are both in the strong
  R22.3 form (fresh processes, differing `PYTHONHASHSEED`); §6.4g's byte-identity is correctly re-based on a
  same-process comparison rather than a committed `.parquet` (the writer-version argument holds). The only
  gap is M1 above.
- **Known-trap recurrence.** I looked specifically for new instances of the §4.3 equal-counts tautology and
  the §5.2a self-derived-delta trap. m51's superset anchor is correctly based on an **eager, outside-graphed**
  reference; m49(ii) recomputes references in-process via `graphed_corpus` rather than materialize-then-fill;
  m50's declaration anchor now uses a literally spelled expected label list (the over-declaration half); the
  axis-vs-sibling equality anchor is a genuine differential against the m48/m49-frozen path. The one
  surviving instance is H2.
- **Fixture buildability of the corpus matrices.** The 23 reference JSONs and `graphed_corpus` are vendored
  in `graphed` (`tests/_corpus/{graphed_corpus,references}`, on `pythonpath` per `pyproject.toml:114-127`);
  m48's 9-of-15 weight split is exactly right (measured fixture names: `ttbar_4j{1b,2b}_{nominal,btag_up,
  btag_down}` = 6, `ttgamma_{nominal,pho_up,pho_down}` = 3, out of 23 total refs); the partitioned-source
  pattern the anchors need already exists (`tests/frozen/checkpoint/m8/analyses.py:146-164` slices
  `make_events()` per partition); `graphed-histogram`'s dev extra already carries `awkward`, `hist` and
  `graphed-executors`, so the m48 vendoring plan is executable.
- **`graphed-histogram` accessor facts** underpinning §4.3/§9.1: `fill_nodes()` is public and unlabeled
  (`boost.py:215-219`), `_SumFills` sums all staged fills (`:88-98`), `_GroupReduce.layout` is count-based
  positional (`:100-117`) — all as the plan states, so the §6.1c/§9.1 anchors rest on true premises.
- **`graphed`'s cross-process capability**: `tests/frozen/debug/m6/test_process_boundary.py` uses
  `mp.get_context("spawn")` directly, so §8.2's cross-process anchor is hostable in `graphed` if desired —
  it just needs to be said (folded into M2).
- **Traceability sweep.** Every binding PART II requirement I could enumerate maps to at least one anchor
  (§§1.1, 1.2, 2.1–2.6, 3.1–3.4, 4.1–4.3, 5.1–5.5, 6.1a–d, 6.2, 6.3, 6.4a–g, 7.1–7.4, 8.1–8.2, 9.1–9.2),
  and no anchor is an orphan. The only coverage holes are M4 (§3.4 in m48), M5 (§2.2 term (b)) and M1
  (§6.4e sorted keys). §8.3 is a no-op statement and correctly carries no anchor.

---

## Verdict

**DIRTY** — 4 HIGH, 5 MID, 4 LOW, 1 NIT; **no BLOCKER**.

The plan's test architecture is in far better shape than the finding count suggests: R0.10a discipline is
strict and explicitly reasoned, the r12/r13 sweeps closed the sibling-vs-axis freeze-order hazards, and the
known tautology traps are actively defended. The four HIGH findings are all of one family — **an anchor whose
stated mechanism does not actually engage the thing under test** (H2's core-level witness, H3's stale
dependency, H4's discovery filter) or **contradicts the requirement it anchors** (H1). Each has a
one-paragraph fix and none touches an owner-locked decision. One more revision addressing H1–H4 and M1–M5
should reach clean on this lens.
