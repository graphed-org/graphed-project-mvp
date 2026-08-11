# `systematics-vary-plan.md` r11 — review round 3, FACTS / HALLUCINATION lens

- **Lens:** facts / hallucination audit — every `file:line` anchor (body + Anchors appendix), every
  measured claim, every citation into the two research docs, prior-art claims, arithmetic and counts.
- **Plan revision reviewed:** r11 (1804 lines).
- **Date:** 2026-07-30.
- **Reviewer stance:** isolated context; every statement below rests on a file I opened or a command
  I ran in this session (R0.11). Owner-locked decisions were not relitigated.

**Verification roots used (revisions confirmed in-session with `git log --oneline -1`):**

| Root | Revision |
|---|---|
| `/private/tmp/claude-501/graphed-latest` | `ff7c607` |
| `/private/tmp/claude-501/graphed-exec-check` | `201ea42` |
| `/private/tmp/claude-501/graphed-histogram-latest` | `211cbbe` |
| `/private/tmp/claude-501/uproot5-graphed` (branch `graphed-mvp`) | `393ecef` |
| `/private/tmp/claude-501/graphed-corpus-latest` | `49650e4` |
| `/private/tmp/claude-501/prior-art/{ewkcoffea, ewkcoffea-coffea2023, wwz4l, WRemnants, narf, mkShapesRDF, PocketCoffea, boostedhiggs, topeft}` | `063e8d7`, `63abb06`, `cc71718`, `c5be6c60`, `7d73361`, `b89a71f`, `b29e33b`, `a33dca8`, `bbb23cad` |
| `/Users/lgray/vibe-coding/coffea-workdir` | `f34b8bdf` |

Probe environment for re-runs: CPython 3.12.10; `awkward 2.12.0`, `pyarrow 25.0.0`,
`boost_histogram 1.7.2` and `1.8.0` (pinned per probe via `uv run --no-project --with …`); the
`graphed` extension imported directly from `graphed-latest/python` (prebuilt
`graphed_core.cpython-312-darwin.so`).

---

## What I re-measured (all CONFIRMED)

These are the plan's load-bearing "measured this session" numbers. I re-derived each one
independently; every one reproduced exactly.

| Plan claim | My measurement |
|---|---|
| §3.3 reduced shape on the bound builder (D=500, K=50, per-universe terminating reduction, every reduction marked): `stages == N+1`, `reduced_nodes == 2N+2` | N=16 → stages 17 / reduced 34; N=128 → stages 129 / reduced 258 — exact |
| §3.3 "the same builder WITHOUT the reduction reports `reduced_nodes == N+2`" | N=16 → 18; N=128 → 130 — exact |
| §5.2a / Part I §3 arena delta `Δ(N=1→2) = K+2 = 52` (and 51 without the reduction) | 553→605 = **52**; without reduction 552→603 = **51** — exact |
| §2.3e / §7.2 interning: "`src * 2.0` recorded twice returns node id 1 both times" | `src` 0, `b` 1, `c` 1, `d` 2 — exact |
| §7.2 `compile_ir` dedup: two structurally identical outputs → ONE value; distinct → two | `evaluate_ir` returned 1 and 2 values respectively — exact |
| §6.1c premise (two marked fills interning to one node) | two independent `graphed_histogram` `Histogram`s with identical spec + identical fill → **same fill-node id (1, 1)** |
| §6.2 non-growth `StrCategory` silently overflows an undeclared label (bh 1.7.2) | `Traits(underflow=False, overflow=True, growth=False, …)`; `h.sum() == 2.0`, `h.sum(flow=True) == 3.0` — exact |
| §6.4e `ak.to_parquet` vs `pq.write_table`: different bytes, different KV sets, no `metadata` param | different sha256; KV `{ak:parameters, awkward_array_metadata}` vs `{ak:parameters}`; `'metadata' in signature(ak.to_parquet)` → `False` — exact |
| §6.4g repeat writes of one array in one process are byte-identical | `True` |
| §1.1 rationale: `ak.from_parquet(columns=["murf_0.5"])` silently empty; list-path works; identifier name works | `[]` / `['murf_0.5']` / `['murf_5em1']` — exact |
| §1.1 rationale: uproot 5.7.5 RNTuple dotted field — `__getitem__` reachable, `RField.array()` fails, `ntuple.arrays([name])` works | `RField murf_0.5` returned; `array()` → `KeyInFileError: not found: 'murf_0'`; `arrays(['murf_0.5'])` → `['murf_0.5']` — exact |
| §1.1 channel-independence: CPython `**`-unpacking admits non-identifier keys | `f(**{'0.5':1,'2p5':2})` accepted on 3.12.10 — exact |
| §2.6 note (i): no tuple subscript on the awkward idiom; `gak.firsts(w[gak.local_index(w)==1])` works | `TypeError: unsupported index (slice(None, None, None), 1)`; masked form materializes `[2, 5]` |
| §2.6 note (ii): `Histogram.fill` is positional | `boost.py:153-163` — `fill(self, *args, weight=, sample=, threads=)` |

Prior-art re-verification (independent of the litsearch): `grep -rEn "\.Vary\(|VariationsFor"` over
`WRemnants` + `narf` → **0 hits** (lit §rdf-users §1); `ewkcoffea@063e8d7` weight bases = 10 common
+ 2 R2-only = **12 → 24 labels** (`wwz4l.py:439-449`), obj-shift bases 3 → **6 labels**
(`:454-459`), outer loop `["nominal"] + 6` = **7 passes** (`:462-467`), `skip_obj_systematics`
(`:462`), `copy.deepcopy(weights_obj_base)` (`:470`) — all as the plan states; the exclusion rule
(`:1204-1207`) and the impact-partitioned Weights comment (`:396-397`) are verbatim.
`ewkcoffea@63abb06`: `masked_val_cache`/`masked_weights_cache` (`:808-809`), `hout = {}` **inside**
the shift loop (`:807`, loop at `:339`, `return hout` at `:892`), empty `obj_correction_systs`
(`:331`), `# Does not work` above the commented `cloudpickle.dump` (`run_wwz4l.py:259-261`), timing
block (`:302-313`) — all confirmed. `FNALLPC/wwz4l@cc71718`: 3 shift bases (`:395-400`), exclusion
rule verbatim (`:711-718`), **zero** dask/`dataset_tools`/`hist.dask` hits repo-wide. coffea
`f34b8bdf`: `rand_gauss` seeds PCG64 from the array's own bytes (`CorrectedJetsFactory.py:36-47`);
`jer_smear` takes ONE `jet_resolution_rand_gauss` while only `jersf` varies per label, with a signed
`deltaPtRel` and a signed-gaussian stochastic branch (`:64-95`) — non-monotone by construction, as
the plan says.

Arithmetic/counts checked and correct: 15 corpus systematics references (10 ttbar + 5 ttgamma out of
23 total, `test_fixtures_reproduce.py:19-21`); **9 of 15** for the m48 weight matrix (6 ttbar + 3
ttgamma); m24 anti-drift literal = **39** names (`test_interface_parity.py:39-79`, counted);
`grep -c "__all__" awkward/functions.py` → 0 and `grep -c "^def "` → 73; `2N+2`/`N+1`; `Δ=K+2=52`;
16.7/3.1 ≈ **5.4** headroom against the 24.0 gate; §6.4c compression figures match the worklog
(`raw 3.551 / ratio 2.883 / xor 3.280 MB`; masks `798 KB → 169 KB` = 4.72×); `1+|S|+|W|` vs axis
mode's `1+|S|` are mutually consistent; the e-form arithmetic (`0.5→5em1`, `2.5→25em1`,
`1.2345→12345em4`, `-1.5→m15em1`, `1e-8→1em8`, `50em2→5em1`, `20e-1→2`) is correct throughout, and
every canonical tag stays inside `[A-Za-z0-9_]+` so `f"{name}_{tag}"` is an identifier.

Anchors appendix: I opened **every** row's cited file at the cited lines. All but the five noted
below are accurate, including the ones that are easy to get wrong — `src/node.rs:41-85` (whole
`NodeKey` enum, variant heads at 42/46/51/56/64/72/81), `store.rs:73-88` and `:152-153`,
`optimizer/mod.rs:1-11,88-116` (the `remap` vector), `engine.rs:7-13,54-56`,
`array.py:127-128,156,245-275,332-335,344-371,374-375,377-379`, `numpy/array.py:71-74,132-136`,
`session.py:30,113-125,140,152,159,168,183,204,242`, `provenance.py:26-33,66-79`,
`execute.py:54-70,99-126`, `aggregate.py:44-65,89-93,101,95-97`, `shuffle.py:5-8,92-96,170,232`,
`plan.py:72-90,164-176,286-301`, `debug/runner.py:6-7,37,57-69` (and the "exactly two
`StageError(` hits" grep), `preserve/bundle.py:103-123,206-210`, `awkward/functions.py:612-616,
677-685`, `awkward/io.py:111-127,157-185,206-216`, `numpy/io.py:163-171`, `write.py:77-79`,
`parquet.py:77,107,118` (the only `metadata` uses; zero `key_value_metadata`/`with_metadata`
anywhere in `graphed-latest/python` or `uproot5-graphed/src`), `projection.py:109-147`,
`graphed-histogram boost.py:39-47,60-71,88-98,100-122,146-150,153-163,166-174,180-212` and
`_spec.py:70,74,115-122,129-135`, `graphed-executors submit/engine.py:381-396` and
`tests/frozen/m7/{analyses.py:118-127, adl.py:124-158}`, the frozen fixtures
(`core/m4/test_systematics.py:28-53`, `core/m4/test_benchmark.py:10,28-33,40-53`,
`core/m40/test_join_serialize.py:83-99` incl. the literal `b"GIR1\x03…"`,
`corpus/m05/test_systematics.py:26-38`, `preserve/m9/{agc.py:38-66,94-118,106-107,
test_reproduce.py:19-23}`, `debug/m6/{test_process_boundary.py:7,16, analyses.py:52-56}`,
`m23/test_group_plan.py:60-66,68-77`, `m29/test_multi_weight_fills.py:82-99`), the uproot rows
(`RNTuple.py:558-570,1560-1569`, `_cascadetree.py:1606`, `TBranch.py:2015-2024`,
`_graphed_write.py:59-64` with zero `compile_ir`/`evaluate_ir` hits, no frozen tree), the fixture
rows (`graphed pyproject.toml:103-130,115-117` + `ci.yml:34,57,143` + the four `importorskip`
sites; `graphed-histogram` zero corpus hits; `graphed-executors pyproject.toml:20-35` with no
histogram dep; `graphed-corpus pyproject.toml:28-30` vs `corpus/references/`), the root-prompt rows
(`:25` quoted verbatim, `:1262,1282,1284,1286`) and `ops_catalog.md:75` (verbatim).

Citations into the research docs check out: cba §optimizer §2's table (3.1 ms @ N=16, 16.7 ms @
N=128, 12.9× nodes → 11.9× time, `2N+2`/`stages=N+1`) and §5's "no dirty-set/invalidation machinery"
grep; cba §histogram §1's constant-Array grep being module-scoped (§4.1's correction is right about
*why* the earlier grep missed `gak.full_like`); cba §exec-checkpoint §1/§4's `R`-is-opaque and
whole-IR `task_id`; lit §rdf-vary §5/§6 (the arXiv:2212.04889 quote at `litsearch:67`, the naming
vocabulary at `:75`, the `Report`/`Snapshot` restriction and the bitmask at `:48-49`, the name-clash
forum thread at `:69`); lit §coffea-sys §1-§5 including the **explicitly carried UNVERIFIED caveat**
on Discussion #469 at `litsearch:236` — the plan reproduces that caveat faithfully;
lit §pythonic-analyses' cross-cutting conventions (`:329-333`) and failure modes (`:337-343`),
including PocketCoffea's `sorted(set(...))`, `growth=False` pre-declared variation axis
(`:309`) that §6.2 cites, and the OR-of-preselections skim lesson (`:307,341`);
lit §ewkcoffea-confirmed's `27 = 1 + 20 + 6` derivation and the `522` identical-line count.

Nothing in the plan is a fabricated anchor, and no measured claim I re-ran came out different in
direction or magnitude. The findings below are all small.

---

## Findings

### F1 — MID — §6.2(i-bis) and the m50 anchor bind a histogram-slicing spelling that does not exist on `bh.Histogram`

**Section:** §6.2(i-bis); m50 frozen anchor "§6.2(i-bis) axis-mode result shape" (plan lines
858-865, 1381-1385).

**Detail.** The plan binds: *"`graphed.labels(h)` = the variation axis's bin set …,
`graphed.universe(h, label)` = the `h[{"variation": label}]` slice"*, and the m50 anchor repeats the
spelling verbatim. But §6.2's own result shape is *"a bare `bh.Histogram` carrying the `"variation"`
axis"*, and §6.1a declares the result type as `dict[str, bh.Histogram | dict[str, bh.Histogram]]` —
so the object being sliced is a plain boost-histogram. Boost-histogram has **no axis `name=`** and
**no string-keyed UHI dict indexing**; named-axis dict access is a `hist`-package feature, and
`hist.graphed` is explicitly out of m48's repo scope (§2.6 note (ii)) and is not named in m50's repo
scope either (m50 = `graphed-histogram` + `graphed` preserve/docs).

**Evidence (measured this session).**

```
bh 1.7.2: bh.axis.StrCategory([...], name='variation')      -> TypeError: unexpected keyword 'name'   (also on 1.8.0)
bh 1.7.2: h[{'variation': 'jes_up'}]                        -> TypeError: list indices must be integers or slices, not str
bh 1.7.2: h[{'variation': bh.loc('jes_up')}]                -> TypeError: list indices must be integers or slices, not str
          (still TypeError after setting ax.__dict__['name'] = 'variation'; h.axes.name is None)
bh 1.7.2: h[{1: 'jes_up'}]                                  -> ValueError: invalid literal for int() ...
bh 1.7.2: h[{1: bh.loc('jes_up')}]                          -> [0. 1. 0.]      # the only working form
```

Axis "names" in `graphed-histogram` ride in `axis.__dict__` and round-trip through the spec as
strings (`graphed-histogram src/graphed_histogram/_spec.py:31-37` `_metadata_of`, `:81-84`
`_restore_metadata`) — they are metadata, not a UHI lookup key.

**Why it matters.** A test-author freezing the m50 anchor as written writes an oracle expression
that raises `TypeError`. The requirement's *intent* (the helper narrows an axis-mode histogram to a
label's slice) is sound and implementable; only the spelling is wrong — and it is exactly the class
of defect r11 itself fixed twice for the §2.6 sketch (`lhe_w[:, i]`, `h.fill(pt=…)`).

**Suggested fix.** Replace the spelling with the measured one and say why:
*"`graphed.universe(h, label)` = that label's slice along the variation axis (boost-histogram has no
axis `name=` and no string-keyed dict index — measured, bh 1.7.2/1.8.0 — so the implementation
resolves the axis position from the spec and slices `h[{axis_index: bh.loc(label)}]`; the
`"variation"` naming lives in axis metadata, `_spec.py:31-37,81-84`)."* Word the m50 anchor over the
semantics (`graphed.universe(h, "jes_up")` equals the manually sliced reference) rather than over a
literal subscript expression.

---

### F2 — LOW — §4.1's non-existence claim ("no constant Array from *nothing*") is false as stated: the numpy idiom ships `full`/`ones`/`zeros`

**Section:** §4.1 (plan lines 644-647); §11's parked item (line 1468-1469); m48 corpus anchor
(lines 1190-1194).

**Detail.** §4.1 says *"What does NOT exist is a constant Array from **nothing** (no shape donor)"*
and §11 parks *"a constant/scalar-Array broadcast helper needing NO shape donor"*. Measured, the
numpy idiom does have donor-free constant constructors:

```
python/graphed/numpy/creation.py:31  def zeros(session, shape, dtype=float, *, name=None) -> Array
python/graphed/numpy/creation.py:36  def ones(session, shape, dtype=float, *, name=None) -> Array
python/graphed/numpy/creation.py:41  def full(session, shape, fill_value, dtype=None, *, name=None) -> Array
python/graphed/numpy/__init__.py:578-598  __all__ includes "full", "ones", "zeros", "empty", "arange", "linspace"
```

The claim is *practically* right for what §4.1 needs, and the reason is worth stating rather than
eliding: these record an eager, fixed-shape **in-memory Source** (`creation.py:27-28`
`session.source(name, form=…, data=arr)`), so they cannot be per-partition — a plan built through
`aggregate_plan` binds exactly one source (`aggregate.py:96-101`, `_PartitionReduce.__call__` passes
`{self.source_name: chunk}`, `aggregate.py:57-63`) and `evaluate_ir` raises
`"evaluate_ir: no data bound for source …"` for any other (`execute.py:104-105`). So the real gap is
"no *partition-aligned, donor-free* constant", not "no constant".

**Suggested fix.** Scope both sentences: *"What does not exist is a **partition-aligned** constant
Array with no shape donor — `graphed.numpy.full/ones/zeros` (`numpy/creation.py:31-45`) record eager
fixed-shape in-memory sources, which a one-partitioned-source plan cannot bind
(`aggregate.py:96-101`, `execute.py:104-105`)."*

---

### F3 — LOW — §6.1c and its appendix row cite the wrong line for `_GroupReduce.layout`'s construction

**Section:** §6.1c (plan line 749: *"built from `len(h._fill_nodes)` at `:198`"*); Anchors row
"`_GroupReduce.layout` is COUNT-based positional slicing" (line 1570).

**Detail.** `graphed-histogram src/graphed_histogram/boost.py:198` is inside `record_external`
(`evaluator,`). The layout is actually built at **`:282`**:

```
282:    layout = tuple((label, len(h._fill_nodes), h._spec) for label, h in items)
288:        reduce=_GroupReduce(layout),
```

The substantive claim (count-based positional slicing, `for j in range(i, i + k)` at `:113`,
mis-slicing when two marked fills intern to one node) is correct — I confirmed the premise
empirically: two independent `Histogram`s with identical spec and identical fill produced the **same
fill-node id**.

**Suggested fix.** `:198` → `:282` in both places.

---

### F4 — LOW — §2.1's corpus stacking anchor is off by one and disagrees with the plan's own appendix

**Section:** §2.1 (plan lines 365-368, cites `graphed-corpus src/graphed_corpus/analyses/
systematics.py:73-75`); Anchors rows at lines 1516 (`systematics.py:74-76,31-36`) and 1579
(`systematics.py:73-75,25-36`).

**Detail.** Measured in `graphed-corpus-latest`:

```
74:    sel_jets = good[sel]
75:    ht = ak.sum(sel_jets.pt, axis=1)
76:    weight = _btag_weight(sel_jets, variation=variation)
```

The two lines §2.1 quotes are **74** and **76**; `:73-75` includes a blank line and *excludes* the
`_btag_weight` call the argument turns on. The appendix row at line 1516 already uses the correct
`74-76`, so the document contradicts itself.

**Suggested fix.** Make all three citations `systematics.py:74-76` (with `:25-36` for `_btag_weight`).

---

### F5 — LOW — `StageError.__eq__` anchor is off by one

**Section:** m49 anchor (plan line 1364) and Anchors row (line 1580):
`python/graphed/debug/errors.py:74-77` vs `:79-81`.

**Detail.** Measured: `__eq__` spans **75-78** (`:78` is the `self.__dict__ == other.__dict__`
comparison the claim rests on); `__hash__` spans **80-81**. `:74-77` starts on a blank line and
misses the dict comparison; `:79-81` starts on a blank line. The claim itself — `__eq__` is
`__dict__`-based so a new field rides free, `__hash__` is a hand-written tuple that must be edited —
is correct.

**Suggested fix.** `errors.py:75-78` vs `:80-81`.

---

### F6 — LOW — §6.4g's quoted parquet writer-version string contradicts the plan's own stated pyarrow version

**Section:** §6.4g (plan lines 1019-1021) and Anchors row "Parquet footers embed the WRITER VERSION"
(line 1577): *"measured this session, an `ak.to_parquet` file contains the ASCII string
`parquet-cpp-arrow version 24.0.0`"*.

**Detail.** Every other parquet probe in the plan states the environment as **pyarrow 25.0.0**
(§6.4b, §6.4e, Anchors). Re-measured under exactly that environment (awkward 2.12.0 / pyarrow
25.0.0), the only writer-version string in the file is `parquet-cpp-arrow version 25.0.0`
(`ParquetFile(p).metadata.created_by` = same). The footer string is the Arrow C++ version, so a
25.0.0 writer cannot emit `24.0.0`; the quoted string came from a different environment than the one
the plan names.

The claim's *direction* is unaffected and in fact strengthened: the footer does embed the writer
version, so a committed `.parquet` byte oracle breaks on a pyarrow bump — §6.4g's same-process
comparison is the right call, and I confirmed repeat writes in one process are byte-identical
(`True`).

**Suggested fix.** Restate as version-agnostic and reproducible: *"an `ak.to_parquet` file's footer
carries `parquet-cpp-arrow version <arrow version>` (measured `25.0.0` under pyarrow 25.0.0;
`ParquetFile(path).metadata.created_by`)"*.

---

### F7 — LOW — the appendix's uproot-fork file count is wrong (12, not 14)

**Section:** Anchors row "`uproot5-graphed-mvp` has NO frozen tree (m51 creates one)" (line 1576):
*"14 flat `tests/test_graphed_*.py`"*; §10 (line 1155) says *"… 14 files"*.

**Detail.** Measured at `393ecef`: `ls tests/ | grep '^test_graphed' | wc -l` → **12**. There are 14
graphed-named files under `tests/` only if the two helper modules `graphed_uproot_analysis.py` and
`graphed_uproot_report.py` are counted, and those are not `test_graphed_*.py`.

The load-bearing half of the row is confirmed: `find . -type d -name "*frozen*"` → empty and
`grep -rn "tests/frozen"` → no hits repo-wide, so m51 genuinely creates the frozen tree.

**Suggested fix.** "12 flat `tests/test_graphed_*.py` (+2 shared helper modules)".

---

### F8 — LOW — §2.3e's prose names three `Session` construction sites while binding five

**Section:** §2.3e (plan lines 452-456): *"every frontend `Array` is constructed in `Session`
(`record_op`/`record_external`/`record_exchange` all end `return self._array_cls(self, node_id)` —
`python/graphed/session.py:140,168,183,204,242`)"*.

**Detail.** The line list is complete and correct — I verified those are the **only** five
`_array_cls(...)` call sites in the whole repo (`grep -rn "_array_cls" python/` returns the
definition at `session.py:39` plus exactly those five returns) — but the prose enumerates only three
methods. The two it omits are `Session.source` (`:133` → return `:140`) and `Session.record_join`
(`:185` → return `:204`). Since §2.3e is an Implementation Target whose whole point is "the merge
rule is implemented ONCE at the chokepoint", an implementer reading the prose can wire three of five
sites and leave a context handle dropped at a source read or across a join.

**Suggested fix.** *"…`source`/`record_op`/`record_exchange`/`record_join`/`record_external` — all
five end `return self._array_cls(self, node_id)` (`session.py:140,168,183,204,242`), and they are the
only `_array_cls` call sites in the repo."*

---

### F9 — NIT — §2.3c mischaracterises the `graphed.awkward` package `__all__`

**Section:** §2.3c (plan lines 418-421): *"the package `__all__` lists modules/classes, not gak's
functions (`python/graphed/awkward/__init__.py:17-31`)"*.

**Detail.** That `__all__` also lists five *functions* — `from_parquet`, `to_parquet`, `project`,
`project_buffers`, `read_parquet_partition` (`__init__.py:14-15,21,26-30`) — alongside the modules
and classes. The operative conclusion is untouched (none of them are gak functions, and
`functions.py` has no `__all__` — `grep -c` → 0, confirmed), and the plan itself relies on
`to_parquet` being exported there in §6.4a.

**Suggested fix.** *"…lists modules, classes and the io/projection functions — but none of gak's."*

---

### F10 — NIT — Part I §2 says the coffea prototype "stalled for ~4 years"; the cited section says ~3

**Section:** Part I §2 (plan line 98); source: lit §coffea-sys §2 (`systematics-vary-litsearch.md:214`).

**Detail.** The litsearch records: created 2021-05-13, docstrings 2022-03-07, then dormant, dask-mode
support merged 2025-07-12 — *"a ~3-year stall on the prototype"*. The plan rounds the
creation-to-revival span instead. Non-binding rationale either way; just pick the number the evidence
states, or say "created 2021-05, dormant from 2022-03 until 2025-07".

---

### F11 — NIT — the r11 revision-history entry is dated 2026-07-30; the worklog records the real date as 2026-08-11

**Section:** Revision history, r11 header (plan line 1588).

**Detail.** `systematics-vary-worklog.md:315,336-337` records the round-2 revision as done on
**2026-08-11** and notes the r11 entry's `2026-07-30` is *"the script's hard-coded date; kept to
preserve the round-1 cache — cosmetic only, real date 2026-08-11"*. Since this plan is committed as a
durable project record, its own history line is the wrong place to carry a known-wrong date.

**Suggested fix.** `**r11 (2026-08-11)**` (or `2026-07-30 drafting / 2026-08-11 landed`), with the
worklog note as the justification.

---

## Verdict

**CLEAN for this lens — no BLOCKER, no HIGH.** The plan's factual substrate is in unusually good
shape for a 1800-line document: every anchor in the Anchors appendix resolves, every prior-art claim
matches the pinned clones, every re-runnable measurement reproduced exactly (including the three
pinned integer families `2N+2` / `N+1` / `Δ=52`, the interning and `compile_ir` dedup facts that
§7.2 and §6.1c hang on, the `StrCategory` overflow behaviour, and the whole parquet/uproot
name-hazard chain), and the two research docs say what the plan says they say — with the #469
UNVERIFIED caveat carried forward honestly.

One MID (**F1**) should be fixed before m50 test-authoring: the `h[{"variation": label}]` spelling is
measurably not expressible on the `bh.Histogram` §6.2 returns, and it appears inside a frozen anchor.
The rest are line-number drift (F3-F5, F7), one over-broad non-existence claim (F2), one
environment-inconsistent quoted string (F6), one incomplete enumeration in a binding Implementation
Target (F8), and three cosmetic items (F9-F11). None of them changes a requirement's meaning or the
shape of any milestone.
