# systematics-vary-plan r26 — review round 18, FACTS / HALLUCINATION AUDIT

- **Lens**: facts / hallucination audit — every file:line anchor (body + Anchors appendix), every
  measured claim, every citation into the two research docs, every prior-art claim, and all
  arithmetic/counts.
- **Plan revision reviewed**: r26 (`systematics-vary-plan.md`, 6250 lines, read in full: Part I,
  every PART II section, §10 milestones, the Anchors appendix, and the complete revision history
  r0→r26).
- **Date**: 2026-07-30.
- **Verification roots used** (fresh clones at the revisions the plan cites; the stale submodules
  under `/Users/lgray/vibe-coding/graphed-workdir` were NOT used for any code fact):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (consolidated `graphed`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (bh 1.8.0 in its `.venv`)
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42` (`graphed-executors`)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf` (the local coffea the JER-SF row names)
  - research docs: `systematics-vary-{litsearch,codebase-analysis,worklog}.md`;
    `graphed-root-prompt.md`
- **Owner-locked decisions**: not relitigated. No finding below proposes a different choice on
  naming, the functional module-verb surface, the e-form canonical float-tag encoding, context
  attachment, record-time expansion + hash-consing, the m48–m51 scope (incl. §6.4 and the JER-SF
  non-monotone contract), or the Phase-2 pull-in.

---

## Findings (ordered by severity)

### LOW — §3.4's `session.walk` anchor does not cover the "returns the root's value" half

**Where**: body §3.4, line 1422-1423; repeated in the revision history r24 entry, line 5269-5270.

**Claim as written**: "`session.walk` exposes ids only through caller-supplied handlers and returns
the root's value (`python/graphed/session.py:245-255`)".

**Evidence I verified myself** (`/private/tmp/claude-501/graphed-latest@ff7c607`,
`python/graphed/session.py`):

```
245: def walk(
246:     self,
247:     array: Array,
248:     *,
249:     source: Callable[[int], object],
250:     op: Callable[[int, str, list[object], Mapping[str, ParamValue]], object],
251:     external: Callable[[int, Callable[..., object], list[object]], object],
252: ) -> object:
253:     """Evaluate the graph from ``array`` with caller-supplied handlers for sources, ops, and
254:     externals. `materialize` evaluates real data; projection evaluates reporting tracers."""
255:     cache: dict[int, object] = {}
...
268:     root = array.node_id
...
288:     return cache[root]
```

The first half of the claim is squarely inside the cited span (the `int`-typed handler callbacks at
`:249-251` are the only channel through which node ids escape). The second half — "returns the root's
value" — is **not** at `:245-255`: the reader sees only `-> object` at `:252`. The supporting line is
`return cache[root]` at `:288` (with `root = array.node_id` at `:268`). The claim is TRUE; the
anchor is simply incomplete for the compound sentence it supports, and the plan itself cites `:268`
for the neighbouring claim at lines 1500 and 5120, so the two spans are already known to it.

**Severity rationale**: no meaning changes and the design consequence (the `{label: tuple[int, ...]}`
return shape is a free implementation choice, so it must be pinned) is unaffected. This is a
citation-completeness defect only.

**Suggested fix**: cite `python/graphed/session.py:245-255,288` (or `:245-255` + `:288`) in both
places, matching the `:245-252` + `:268` pattern the plan already uses at lines 1500 and 5120.

---

### NIT — §6.1d's `Histogram.fill` signature anchor is off by one at both ends

**Where**: body §6.1d, line 1933-1934: "today's signature is `fill(self, *args, weight=None,
sample=None, threads=None)`, `graphed-histogram src/graphed_histogram/boost.py:152-158`, with no
such parameter" (the `unweighted=True` binding).

**Evidence I verified myself** (`/private/tmp/claude-501/graphed-histogram-latest@211cbbe`,
`src/graphed_histogram/boost.py`):

```
152:     # ---- recording ------------------------------------------------------------------------
153:     def fill(
154:         self,
155:         *args: Array,
156:         weight: Array | Sequence[Array] | None = None,
157:         sample: Array | None = None,
158:         threads: int | None = None,
159:     ) -> Histogram:
```

`def fill` opens at `:153`, not `:152`; the cited span starts on the section comment and stops one
line before the return annotation. The claim is nevertheless **fully supported inside the cited
span**: the entire parameter list (`:154-158`) is within `:152-158`, so a reader checking "no
`unweighted=` parameter" sees everything needed. Note the plan's other anchors on the same function
are exact — `:153-163` (positional fill, lines 1334 and 5093) and `:153-212` (the fill body / "a
different distribution", lines 1977 and 5509) both verified correct.

**Suggested fix**: `boost.py:153-159`.

---

## Non-findings worth recording (checked, and clean)

These are things a later reader may reasonably suspect; I checked each and they hold.

- **§3.3's wall-clock gate reproduces.** I rebuilt the §3.3 topology against
  `graphed-latest@ff7c607` (`add_source` + D=500 prefix ops + per universe 1 + K=50 ops +
  `add_reduction`, reduce over the N reduction outputs, best-of-5): N=16 → `node_count 1333`,
  `{'stages': 17, 'reduced_nodes': 34, 'reachable_nodes': 1333}`, 3.66 ms; N=128 → 7157, `{'stages':
  129, 'reduced_nodes': 258}`, 21.07 ms; **time ratio 5.76** vs the plan's 5.64, node ratio
  7157/1333 = 5.37. Every literal in §3.3 (1333 / 7157, 17 / 129, 34 / 258, 5.37×, `2N+2`, `N+1`)
  reproduces exactly, and the 16.0 gate keeps ≈2.8× headroom. `reachable_nodes` is indeed in
  `reduce()`'s returned report, so the self-scaling alternative at line 1392 is buildable as stated.
- **All boost_histogram claims re-run on bh 1.8.0** (the version actually installed in
  `graphed-histogram-latest/.venv`): non-growth `StrCategory` silent overflow → `sum 2.0` vs
  `sum(flow=True) 3.0`, `Traits(..., overflow=True, growth=False)` (appendix row for §6.2's
  declaration contract, verbatim); 2-D weight → `ValueError: spans must have compatible lengths`;
  mismatched non-growth axes → `ValueError: axes not mergable`; `sample=` → `TypeError: Keyword(s)
  sample not expected` on `Double()` **and** `Weight()`, accepted on `Mean()`/`WeightedMean()`
  (m50's storage pin). The appendix's mixed bh **1.7.2** (cba probes) vs **1.8.0** (r12–r22
  re-measures) attributions are not an inconsistency: cba records its scratch venv at 1.7.2
  (`systematics-vary-codebase-analysis.md:190`), and I confirmed both readings agree at 1.8.0.
- **The JER-SF prior-art anchor verifies at the named local revision.** `coffea-workdir` is at
  `f34b8bdf`; `src/coffea/jetmet_tools/CorrectedJetsFactory.py:36-47` is `rand_gauss` seeding
  `numpy.random.PCG64` from array **content** (`:37-40`), and `:64-95` is `jer_smear` with the
  single shared `jet_resolution_rand_gauss` draw (`:83`), `jersf = ...[:, variation]` (`:84`),
  `doHybrid` (`:86`), `detSmear`/`stochSmear` (`:88-89`) — i.e. content-seeded, one draw for all
  variations, signed/non-monotone, exactly as §5.5 states.
- **`src/node.rs:41-85` completeness claim exact**: `pub enum NodeKey` at `:41`, variant heads
  `Source :42`, `Op :46`, `Reduction :51`, `External :56`, `Stage :64`, `Exchange :72`, `Join :81`,
  enum closes `:85` — all seven as the appendix row enumerates, and no write/sink variant.
- **m4 precedent anchors exact**: `tests/frozen/core/m4/test_benchmark.py:10` (`SIZES`), `:28-33`
  (best-of-N), `:40-43` (`base = max(times[SIZES[0]], 1e-4)`, `assert growth < 24.0`, 8× span),
  `:46-53` (per-size budget); `m4/test_systematics.py:28-53` (variation-count independence at `:28`,
  <1 s at ~10⁴ nodes at `:39-53`).
- **gak discovery counts exact**: `graphed.awkward` as the discovery target yields **0** functions
  under the `__module__ == "graphed.awkward.functions"` filter (its six package-level functions are
  `from_awkward/from_parquet/project/project_buffers/read_parquet_partition/to_parquet`, and
  `graphed.awkward.num` raises `AttributeError`), while `graphed.awkward.functions` yields **65** —
  precisely §2.3c's binding.
- **Worklog compression figures match §6.4c/§11 word for word** (`systematics-vary-worklog.md:181-188`:
  `raw=3.551MB ratio=2.883 delta=3.193 xor=3.280`, reconstruction "measured False" for the ratio
  form; masks `798KB / 614KB / 169KB (~4.7×)`), with methodology stated (float32, 1M elems, zlib-6,
  seed 42) as R0.11 requires.
- **Fixture/packaging facts verified**: corpus wheel packages only `src/graphed_corpus`
  (`graphed-corpus pyproject.toml:28-30`) so it ships no reference JSONs, while `graphed` vendors
  **23** of them at `tests/_corpus/references` and the vendored
  `tests/_corpus/graphed_corpus/analyses/systematics.py` carries the SAME line numbers `:50,79,102`
  the appendix cites; `graphed`'s only cross-process frozen test is
  `tests/frozen/debug/m6/test_process_boundary.py:7,16`; PyPI live-checked — `graphed-histogram`
  resolves to `0.0.1`, equal to the repo's own `pyproject.toml:7` version, which is exactly why
  m49(ii)'s git-URL install pair is required.
- Arithmetic and counts re-derived: 9-of-15 corpus systematics refs (6 ttbar weight + 3 ttgamma of
  23 JSONs); `1 + 500 + N·52` → 1333 / 7157; `ln24/ln8 = 1.53`; `ln24/ln5.37 = 1.89`; `5.37² ≈ 28.8`;
  `16/5.64 ≈ 2.8`; m24's 39-name literal; 73 `def`s / 65 public gak functions; §1.1's e-form digit
  counts (`1e40` → 41 digits; `1e-40` → the 5-char `1em40`; `1.5e31` → 32 digits, at the cap;
  `1.5e32` → 33; `-1.5e31` → 32 digits / 33 rendered chars; the fractional 31-mantissa case
  31 − 35 = −4 normalized vs 35 rendered) and §6.2's lexicographic ordering examples
  (`btag_down < btag_up < jes_down < nominal < pu_up`, `murf_10 < murf_2`) — all internally
  consistent.

---

## Verdict

**CLEAN.** r26 survives the facts lens with two citation-precision items and nothing else: one LOW
(an anchor covering only half of its own compound claim, fix = add `session.py:288`) and one NIT (a
one-line-off span that still contains all its supporting evidence). I found **no** fabricated
anchor, no unsupported measured claim, no misquoted research-doc or prior-art citation, and no
arithmetic error. Every cheap probe I re-ran — the §3.3 benchmark topology and timing, every
boost_histogram behaviour, the gak discovery counts, the corpus/packaging/PyPI facts — reproduced
the plan's stated values, and the two expensive/foreign-environment claims I could not re-run
(pyarrow-dependent parquet byte/KV probes; the cloudpickle digest triples) are internally consistent
with the worklog's recorded methodology and already carry their toolchain versions and, where
appropriate, explicit withdrawal notes for the non-reproducible digests.
