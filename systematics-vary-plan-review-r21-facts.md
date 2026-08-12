# systematics-vary-plan review — round 13, revision r21 — FACTS / HALLUCINATION lens

- **Lens:** facts / hallucination audit (file:line anchors, measured claims, research-doc citations,
  prior-art claims, arithmetic and counts). Design and test-authoring concerns are out of scope for
  this lens and are not raised here.
- **Plan revision reviewed:** r21 (`systematics-vary-plan.md`, 5069 lines).
- **Date:** 2026-07-30.
- **Verification roots used** (all revisions confirmed in-session with `git rev-parse`):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (+ its `.venv`: awkward 2.12.0, numpy 2.5.2)
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42`
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (+ its `.venv`: boost_histogram 1.8.0)
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef`
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea @ 063e8d7, ewkcoffea-coffea2023 @ 63abb06, wwz4l @ cc71718}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf`
  - clean resolves via `uv run --no-project --with …` (awkward 2.12.0 / pyarrow 25.0.1 / cloudpickle 3.1.2 / CPython 3.12.10)

---

## Verdict

**CLEAN at BLOCKER / HIGH / MID.** Two LOW findings and three NITs, all line-span precision; none
changes the meaning of a requirement and none would mislead an implementer or a test-author into a
wrong assertion.

This is the most factually solid revision I have audited. Every r21-new measured claim reproduced
**exactly** — including the ones r21 itself introduced to *correct* an earlier revision. Two r21 acts
of self-policing deserve to be recorded as verified-correct rather than merely accepted:

- the **withdrawal of `80e8024dc8f3b77d`** (§7.3, m49 anchor) is right for the reason given. I built
  a module-level frozen dataclass carrying `(ir: bytes, variation_labels)` and ran it under
  `PYTHONHASHSEED ∈ {1,7,12345}` with cloudpickle 3.1.2 / CPython 3.12.10: sorted-tuple →
  **one** digest ×3 (`b413dfac51fd663b`), frozenset → **three** distinct, `__main__`-defined class →
  **three** distinct for *both* payload forms. The qualitative shape r21 kept reproduces exactly; the
  digest value does not (mine differs from the withdrawn one), which is precisely r21's stated
  ground — cloudpickle bytes for an importable class embed module/qualname/field names that the
  withdrawn row never named.
- the **§8.2(i) digest triple**, which r21 says "was re-run in r21 and reproduces exactly", does:
  `(3, frozenset({"btag_down","btag_up","jes_down","jes_up","nominal"}))` under seeds 1 / 7 / 12345 →
  `b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831`. Byte-for-byte match.

---

## Findings

### LOW-1 — the m05 `test_systematics.py` anchor carries the CORPUS-repo line numbers on the CONSOLIDATED path

**Section:** Anchors appendix, row "m05 behavioral invariants (weight preserves / shift orders
selection)"; the same numbers are echoed in Part I §1 and §10/m49's ordering-witness context.

**Claim as written:** `tests/frozen/corpus/m05/test_systematics.py:26-38`.

**Evidence (measured this session):**

```
$ grep -n "^def test_kinematic_variation_changes_selection\|^def test_weight_variation_preserves_selection" \
    /private/tmp/claude-501/graphed-latest/tests/frozen/corpus/m05/test_systematics.py
25:def test_kinematic_variation_changes_selection(events: ak.Array) -> None:
33:def test_weight_variation_preserves_selection(events: ak.Array) -> None:

$ grep -n … /private/tmp/claude-501/graphed-corpus-latest/tests/frozen/m05/test_systematics.py
26:def test_kinematic_variation_changes_selection(events: ak.Array) -> None:
34:def test_weight_variation_preserves_selection(events: ak.Array) -> None:
```

The two tests are at `:25-30` and `:33-37` on the **consolidated** path the anchor names; the cited
`:26-38` starts one line inside the first test's body and ends one past the second. The `:26`/`:34`
numbers are correct for the **corpus-repo** path — the one-blank-line difference `cba §corpus §3`
itself documents ("`test_systematics.py` differs by one blank line"). So the drift is inherited from
the research doc, not invented.

**Content is true either way**: `assert jes_up > nominal > jes_dn` and
`assert btag_up == nominal == btag_dn` are both present and are exactly what the plan says they are.

**Suggested fix:** cite `tests/frozen/corpus/m05/test_systematics.py:25-37` for the consolidated
path (or keep `:26-38` and name the `graphed-corpus` path). One-line edit in the appendix row.

---

### LOW-2 — `histograms.py:39-42` truncates `fingerprint`

**Section:** m48 matrix anchor ("Same service for the corpus's `stable()` rounding…") and the
Anchors row "Corpus rounds to 6 decimals PRE-fill and again in the comparison helpers".

**Claim as written:** `histograms.py:20,34-37,39-42`.

**Evidence (measured, `graphed-latest/tests/_corpus/graphed_corpus/histograms.py`):**

```
20: STABLE_DECIMALS = 6                         # exact
35: def bin_values(h: Hist) -> list[float]:     # body 36-37  -> ":34-37" covers it (34 is blank)
40: def fingerprint(h: Hist) -> str:            # body 41-43
43:     return hashlib.sha256(payload).hexdigest()[:16]
```

`fingerprint` spans `:40-43`; the cited `:39-42` opens on a blank line and stops before the return —
i.e. before the line that actually establishes "fingerprint = sha256 of the rounded bins". `cba §corpus §1`
cites `:40-44` for the same function, so the plan and its own source disagree by one here.

**Suggested fix:** `histograms.py:20,35-37,40-43`.

---

### NIT-1 — `graphed_histogram.plan()` cited as `:254-292` / `:255-292` in four places; `def plan(` is at `:256`

**Sections:** §6.1a (r18), §7.2 (r18 merge-guard SITE), §9.1 (unpack rationale), Anchors row
"`_GroupReduce.layout` is COUNT-based positional slicing" (`:255-292`).

**Evidence:** `grep -n "^def plan" src/graphed_histogram/boost.py` → `256`. Lines 254-255 are blank.
Two *other* citations of the same function — §10/m48's merge-guard assignment and §10/m50's
plan-level-listing placement — already say `:256-292` correctly.

These are supersets, not misses: every quoted fact inside them (`items = [(str(k), v) …]` at `:271`,
`fill_nodes` at `:281`, `layout` at `:282`, `aggregate_plan(` at `:286`, the declared
`Plan[dict[str, bh.Histogram]]` at `:262`) is at the stated line. Meaning unchanged.

**Suggested fix:** normalize all six citations to `:256-292`.

---

### NIT-2 — `graphed pyproject.toml:114-127` for the `pythonpath` list

**Section:** §10/m48 ("`tests/_corpus` on `pythonpath` `:114-127`"), Anchors row "`graphed` VENDORS
the corpus".

**Evidence:** `pythonpath = [` is at `:115` and the list closes at `:127`; `:114` is the last line of
the preceding comment block. `"tests/_corpus"` is at `:117`. The 23 vendored reference JSONs and the
`tests/_corpus/{graphed_corpus,references}` layout are confirmed
(`ls tests/_corpus/references | wc -l` → 23; `diff -q` of the vendored
`analyses/systematics.py` against the corpus repo → identical).

**Suggested fix:** `:115-127`.

---

### NIT-3 — the fill-path optimizer-merge probe's node ids (`2`, `4`) are fixture-dependent and the fixture is unnamed

**Sections:** §7.2 ("two `Histogram.fill`s differing only in `weight=[w]` versus `weight=[w * 1.0]`
record fill nodes `2` and `4` and compile to `outputs() == [2]`"); repeated in §10/m48's §1.2 anchor
bullet and in the Anchors row "The OPTIMIZER also merges DISTINCT record ids".

**Evidence (measured, `graphed-histogram-latest` venv, bh 1.8.0, graphed 0.0.1 from `graphed-latest`):**
with the minimal fixture — one source, `h1.fill(w, weight=[w])`, `h2.fill(w, weight=[w*1.0])` — the
fill node ids are **1** and **3**, and `compile_ir(s, n1, n2)` gives `outputs() == [1]`. The plan's
`2`/`4`/`[2]` are reproducible only with one extra recorded node upstream (e.g. a derived axis value),
which the plan does not name.

**The load-bearing half reproduces exactly and is unaffected**: two fill nodes differing only by an
`x * 1.0` identity token compile to ONE output, i.e. the optimizer merges distinct record ids and the
record-time `(output, label) → node id` map cannot see it. I also reproduced the non-fill twin
verbatim: `nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5` → record ids `0,1,2,3`,
`compile_ir(s, nom, m1, m2, mh).outputs() == [0,1,2]`, `evaluate_ir` returns 3 values.

By the plan's own r14 reproducibility standard ("the payload and toolchain NAMED so the probe is
reproducible") — the standard that withdrew the §6.4e digest pair and, in r21, the §7.3 digest —
these two integers do not meet it. Risk is minimal: no anchor asserts the ids; they are rationale.

**Suggested fix:** name the fixture (e.g. "over a source + one derived axis value") or drop the
literal ids and keep `outputs()` collapsing two fill nodes to one.

---

## Verification performed (coverage record)

Everything below was opened at the cited lines in the pinned roots, or re-run as a probe, and matched
the plan unless listed as a finding above.

**Rust / core (`graphed-latest@ff7c607`).** `src/store.rs:73-88` (`intern`), `:147-156` /`:152-153`
(`mark_output` dedup), `:185-200` (`from_reduced`, `mark_output(map[o])` at `:197`);
`src/node.rs:39-41`, `:41-85` whole `NodeKey` enum with variant heads at `:42/46/51/56/64/72/81`,
`:102-103` (`is_boundary` = `!Op`); `src/optimizer/engine.rs:7-13` (the O(N)-extractor note, verbatim
"blows up … on the deep chains a systematics graph produces"), `:22-31` (`SYMMETRIC_OPS`,
`IDENTITY_TOKENS` `x+0.0`/`x*1.0`), `:54-56`, `:67-80`, `:89-110`; `src/optimizer/mod.rs:1-11`,
`:88-116` (`remap` built locally, only `out_idx` returned — the claim "never returned" is exact);
`src/lib.rs` `#[pymethods]` at `:102`/`:159`/`:470` with the `PyGraphStore` impl closing at `:416` and
its full method list (no id mapping anywhere) — the r14 enumeration is complete.
`GraphStore.nodes()` keys measured `{id, inputs, kind, name, output, params}`, a stage adding
`n_members`/`members` with per-member `{inputs, kind, name, params}` — r19's "or token" drop is
correct: no public surface exposes a token.

**Frontend Python.** `array.py:54,127-128,137-143,156,245-275,283-290,332-335,344-371,374-391,397-410`;
`session.py:30,39,50-51,113-125,133-140,142-168,170-183,185-204,206-242,245-252,255-286` (`root =
array.node_id` at `:268`), `:291-301`; the five `_array_cls` return sites at `140/168/183/204/242` and
the five `_provenance.setdefault` sites at `138/166/181/202/240` — both exact, and
`grep -rn "_array_cls" python/` hits only `session.py`; `execute.py:36-45,54-58,70-80,85-91,96-126`
(incl. `:104-105` "no data bound for source", `:109` op dispatch, `:110-115` stage members, `:116-124`
external dispatch by content hash, `:126` `[vals[o] for o in store.outputs()]`);
`aggregate.py:44-55,57-65,68-77,86,89-93,95,96-104,101`; `projection.py:109-121,145-146,147`;
`shuffle.py:5-8,84,89,92-96,142,155,170,208,220,232`; `provenance.py:26-33,66-79`;
`errors.py` (`GraphedError(Exception)`, unrelated to `NotImplementedError`);
`debug/errors.py:29,32-81,75-78,80-81`; `debug/runner.py:6-7,37,57-69` and
`grep "StageError(" python/` → exactly two hits; `core/execution.py:206-217,219-224,276-284,335-351,
378-384,450-457` — the three literal key sets m48 freezes (`Plan`, `ExecResult`, `TaskEvent`) match
the source field-for-field; `core/plan.py:54,72-90,126,164-176,286-301`;
`checkpoint/runner.py:77-91,100-109`; `checkpoint/store.py:31-41,62-73`;
`preserve/bundle.py:103-123,206-210,268-288`; `write.py:32-43,77-79`; `parquet.py:77,107,118`
(the only `.metadata` use is `num_rows`; `:107,118` are docstring mentions — exact);
`numpy/array.py:71-74,76-86,132-136,154-161`; `numpy/creation.py:27-28,31-75`;
`numpy/__init__.py:8,578-598`; `numpy/io.py:163-171`; `awkward/io.py:111-127,121,122,157-185,
206-216,239,260,274`; `awkward/__init__.py:14,17-31,30`; `awkward/functions.py:18,118,346,383,400,
476,513,600,612-616,673,677-685,687,693,717,722,727,732,737`;
`__init__.py:8-25` and `__all__ :27-58` (`:44` = `"apply"`, `:46` = `"compile_ir"`, `:50-57` the
shuffle verbs) — all exact.
`grep -rn "DurablePlan(" python/` → **0**; `OpSpec.from_callable` only at `shuffle.py:181,188,245,259`;
`graphed-exec-check/src` → **0** `task_id`/`DurablePlan` hits.

**graphed-histogram (`211cbbe`).** `boost.py:39-47,60-71,88-98,100-122,108-117,120-122,127-130,
146-150,152-163,160-161,166-178,175-178,180-212,196-210,215-216,218-219,245-255,262,271,281,282,
283-286`; `_spec.py:19-27` (`_STORAGES` carries `Mean` and `WeightedMean` — r21's claim), `:31-37`,
`:70,74`, `:81-84`, `:115-122,129-135`; `pyproject.toml:21` (runtime deps), `:25-39` (dev), `:50`
(`pythonpath`); `.github/workflows/ci.yml:13-17` (GRAPHED + EXECLOCAL only, no CORPUS/HISTOGRAM),
`:44,67` (`pytest tests/frozen` in ONE process); `find tests -name __init__.py` → 0; frozen dirs
`{m23, m29}`; `grep -rn corpus tests/ .github/workflows/` → **0 hits**. Frozen anchors
`m23/test_group_plan.py:60-66,68-77,74-75,86,89,99` (`src.part_reads == 4` at `:77`) and
`m29/test_multi_weight_fills.py:75-79,84,87,95,96` — all exact, including that `:74-75/86/89/99`
index the plan value by **bare output name**, which is the fact §6.1a's r19 scoping rests on.

**Corpus (`49650e4`) and its vendored copy.** `analyses/systematics.py:25-36` (`ak.prod(…, axis=1)` at
`:36`), `:39-45` (`ak.with_field`), `:60-61` (JES before the pt cut), `:74-76` (`sel_jets = good[sel]`
at `:74`, `ht` at `:75`, `_btag_weight(sel_jets, …)` at `:76` — r12's "`:73` is blank, `:75` is the
`ht` sum" is exact), `:79`, `:91-92` (unvaried photons sliced by the varied selection), `:102`, `:50`;
`histograms.py:20`; 23 reference JSONs of which exactly **15** are the systematics set;
`diff -q` vendored-vs-repo `systematics.py` → identical. **Arithmetic checked:** m48's "ttbar
4j1b/4j2b × {nominal, btag_up, btag_down} (6) + ttgamma {nominal, pho_up, pho_down} (3) = 9 of the 15
refs" — the remaining 6 are exactly the `*_jes_{up,down}` files. Correct.

**graphed frozen tree / §10 mechanics.** `scripts/run-tests.sh:16-25` (SUITES), `:30`
(`SPLIT_PKGS="frontend numpy awkward"`); `find tests/frozen -name __init__.py` → **0**;
`tests/frozen/checkpoint/{m8,m39}` with `m8/test_resume.py` present; `tests/frozen/core/m4/
test_benchmark.py` and `preserve/m9/{test_reproduce.py,test_inspect.py}` present — every collision
the unique-basename rule names is real. `core/m4/test_benchmark.py:10,28-33,40-43` (gate `24.0` over
8× sizes) and `core/m4/test_systematics.py:28-53` (3300 variations, `< 1 s`, `reduced ≤ 8`);
`core/m40/test_join_serialize.py:83-99` (literal `b"GIR1\x03…"` golden);
`awkward/m24/test_interface_parity.py:39-79` — **39** literal names counted, `full_like` at `:75`;
`debug/m6/{analyses.py:52-56, test_process_boundary.py:7,16}`;
`preserve/m25/…:31`, `m27/…:185,207`, `m30/…:155` (the `importorskip` house pattern, verbatim);
`frontend/m5/test_aggregate_plan.py:77,88,102` (plain callables) and
`frontend/m39/test_shuffle_plan_builder.py:58-64` — **r21's correction to r20 ("m5's plus m39's") is
right**: `grep -rln aggregate_plan tests/frozen/` returns m5, m39, and m40, and m40's is a docstring
mention only. `frontend/m40/test_noninner_null_key_option.py:30` does import `graphed.awkward`
(cross-package frozen import precedent). `graphed pyproject.toml:27` (runtime = executing +
cloudpickle), `:29-48` (no `graphed-histogram` in any extra; `dev` = boost-histogram/hist),
`:103-130`; `ci.yml:34,57,143` (`pip install -e ".[dev]"`).

**graphed-executors (`201ea42`).** `submit/engine.py:381-396` (translate-only);
`pyproject.toml:20-35` (no histogram dep), `:54` (pythonpath); `ci.yml:13,15,17` (GRAPHED + CORPUS),
installs at `:38,65,94,136`, frozen runs at `:44,67,101,153`; 15 milestone dirs; 0 `__init__.py`;
`grep -rn histogram pyproject.toml .github/workflows/` → **0**; `tests/frozen/m7/adl.py:124-158`
(in-process corpus reference recompute) and `m7/analyses.py:118-127` (worker-side graph rebuild).

**uproot fork (`393ecef`).** `behaviors/RNTuple.py:1560-1562` (exact-first `__getitem__`),
`:1564-1569` (`.`-split fallback), `:562,567` (`to_akform` splits `self.path` on `.`);
`behaviors/TBranch.py:2015-2017` (exact-first), `:2019-2024` (`/`-split, never `.`);
`writing/_cascadetree.py:1606` (`out[field_name + "." + subfield_name]`);
`writing/_graphed_write.py:59-64` with `grep -c "compile_ir\|evaluate_ir"` → **0**;
no `tests/frozen` anywhere; **12** flat `tests/test_graphed_*.py` + the 2 named helper modules.

**Root prompt / catalog.** `graphed-root-prompt.md:25` (the "tens of thousands" sentence),
`:1262` (R22.0), `:1282` (R22.10), `:1284` header, **`:1285` blank**, `:1286-1287` the wrapped
"treating systematic variations as a graph / axis" bullet — r18's re-measurement is exact;
`ops_catalog.md:75` verbatim in both the corpus repo and the consolidated copy.

**Re-run probes (all reproduced).**
- §7.2 r21 output-order probe: record ids `src 0, dead 1, b 2, e 3, c 2`;
  `compile_ir(s, b, e, c)` → `GraphStore.deserialize(ir).outputs() == [1, 2]`; `evaluate_ir` returns
  **2** values, b's then e's; `s._store.outputs() == []`. Exact, digit for digit.
- §1.2 / §5.2a dedup: structurally identical outputs → 1 value, distinct → 2; `a = src*2.0; b = src*2.0`
  → same node id, `a is b` False.
- §7.2 r17 identity-token merge: `nom, m1, m2, mh` ids `0,1,2,3` → `outputs() == [0,1,2]`, 3 values;
  `compile_ir(s, b, b*1.0)` → **1** value (the m48 unvaried positive control is real).
- §3.3 / §5.2a topology (raw `GraphStore`, D=500, K=50): with a terminating reduction
  N=16 → stages **17** / reduced **34** / reachable **1333**; N=128 → **129** / **258** / **7157**;
  without it N=16 → (17, **18**), N=128 → (129, **130**); Δ(N=1→2) = **52** with, **51** without.
  Every pinned integer exact. (Wall clock on this machine: 3.26 ms → 16.94 ms, ratio 5.20 vs the
  plan's 5.64 — machine noise, and it moves *toward* more headroom under the 16.0 gate.)
- §3.3 gate arithmetic: ln24/ln8 = 1.53; node ratio 7157/1333 = **5.37**; ln24/ln5.37 = 1.89;
  5.37² = 28.8, /24 = 1.20; 16/5.64 = 2.84; 28.8/16 = 1.80. All exact.
- §8.2(i) accessor cardinality (D=20, K=5): base N=3 → 4 stages / 8 reduced /
  `{source:1, stage:4, reduction:3}`; N=16 → 17/34/`{1,17,16}`; N=128 → 129/258/`{1,129,128}`;
  the dead branch changes nothing (DCE); the shared-node extension gives N=3 → 9/`{1,5,3}` and
  N=16 → 35/`{1,18,16}` = `2N+3` / `N+2`. r19's correction and r20's base-fixture scoping are both
  exactly right.
- §2.2 / §2.3a property classification: on a 1-D `NumpyForm` source, `dtype`/`ndim`/`shape` →
  `node_count()` delta **0**, `T` → delta **1**; discovered properties on `NumpyArray` =
  `['T','dtype','ndim','node_id','session','shape']`; `dir(Array)` public =
  `['filter','map','node_id','reduce','repartition','session']`; `dir(NumpyArray)` = **32** public
  names. r19's BLOCKER fix is measured-correct. `gnp.ones(s, (4,3)).T` raises
  `GraphedTypeError: … transpose without axes reverses them, displacing the partitioned axis 0`
  — r20's 1-D fixture pin is necessary.
- §2.3c discovery: `grep -c "__all__" functions.py` → **0**; `grep -c "^def "` → **73**;
  module-filtered public functions → **65**; the *alias* `graphed.awkward` under the bound
  (module-filtered) rule discovers **0** while the module discovers **65** — r15's "0 vs 65" is
  exact; the package `__all__` lists exactly the six named package-level functions;
  `graphed.awkward.num` → `AttributeError`.
- §2.3d discovery: the annotation-wide filter over `graphed.__all__` yields exactly
  `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`
  (**8**), and `compile_ir(session: Session, *outputs: Any, …)` is **not** among them. Exact.
- §6.1b / m50 r21 storage pin: bh 1.8.0 → `Double()` and `Weight()` both raise
  `TypeError: Keyword(s) sample not expected`; `Mean()` and `WeightedMean()` accept `sample=`.
  The variation-axis spec round-trips `spec_of`→`zero_of` on both mean storages and the rebuilt
  histograms add. Exact.
- §6.2 bh probes: `StrCategory(name=…)` → `TypeError`; `h[{"variation": label}]` and the `bh.loc`
  variant → `TypeError: list indices must be integers or slices, not str`; `h[{1: bh.loc(l)}]` ==
  `h[{1: ax.index(l)}]`; `h.axes.name` → `AttributeError: object Regular has no attribute name`;
  under-declaration `sum 2.0` vs `sum(flow=True) 3.0` with `Traits(overflow=True, growth=False)`;
  over-declaration `sum == flow == 3.0`; cross-axis `+` → `ValueError: axes have different length`;
  unequal axis lengths → `ValueError: spans must have compatible lengths`. All exact.
- §6.1d awkward probes: `ak.broadcast_arrays` over lengths 7 and 3 →
  `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`; the jagged
  3-row case succeeds. Exact.
- §6.4c: `float32 ^ float32` → `TypeError: ufunc 'bitwise_xor' not supported…` for **both**
  `np.ndarray` and `ak.Array`; `a.view(np.uint32) ^ b.view(np.uint32)` works; gak ships no
  `view`/`packbits`/`frombuffer`.
- §6.4e r21 ROUTE: `AWKWARD_INFO_KEY = b"awkward_array_metadata"` at
  `awkward/_connect/pyarrow/table_conv.py:16`, written only by
  `convert_awkward_arrow_table_to_native` (`:19-40`), imported by `ak_to_parquet.py:14` and called at
  `:417`; the public `attrs` merge point `table.replace_schema_metadata(merged_metadata)` at `:431`
  (within the cited `:424-431`). Exact — the "no `awkward._connect` import" rule rests on a real fact.
- §6.4e/§6.4g parquet probes (clean resolve, awkward 2.12.0 / pyarrow 25.0.1): `ak.to_parquet` vs
  `pq.write_table(ak.to_arrow_table(a))` → **different bytes** for record / list-of-float / flat
  numeric; file-KV `{ARROW:schema, awkward_array_metadata}` vs `{ARROW:schema}` (list-of-float and
  flat) and `{ARROW:schema, ak:parameters, awkward_array_metadata}` vs
  `{ARROW:schema, ak:parameters}` (record) — matching the appendix row exactly, including that
  `ak:parameters` is array-dependent; `"metadata" in signature(ak.to_parquet)` → **False**;
  `ParquetFile(p).metadata.created_by` → `parquet-cpp-arrow version 25.0.1`; two writes of the same
  array in one process are byte-identical.
- §1.1 canonicalization rationale: `ak.from_parquet(p, columns=["murf_0.5"])` → **`[]`** (silently
  empty) while `columns=[["murf_0.5"]]`, the full read, and the identifier-shaped/p-form names all
  read back correctly. Exact.
- §2.6 note (i): `w[:, 1]` → `TypeError: unsupported index (slice(None, None, None), 1)`;
  `gak.firsts(w[gak.local_index(w) == 1])` over `[[1,2,3],[4,5,6]]` materializes `[2.0, 5.0]`. Exact.
- §6.4a(2c) r21 rationale: a jagged boolean over the record's own structure has the record's **outer**
  length (`len(mask) == len(a) == 2`) and `a[m]` keeps **every row** while filtering inner elements
  (`[[1,3],[5]]`) — so it does pass (2b) and would silently violate the superset-row contract. The
  new predicate's stated hazard is real.
- §7.3 / §8.2(i) cloudpickle determinism: covered under **Verdict** above.
- `OpSpec.from_callable(_PartitionReduce(...)).kind` → `"opaque"`, and the instance carries no
  `__qualname__` — exact.

**Arithmetic and counts.** §1.1 e-form: `0.5→5em1`, `2.5→25em1`, `1.2345→12345em4`, `-1.5→m15em1`,
`1e-8→1em8`, `"50em2"→5em1`, `"05"→5`, `{"2","2.0","2e0","20e-1"}→2` — all correct under the stated
minimal-mantissa rule, and every canonical form matches `m?\d+(em\d+)?`. The r19 normalization and
r20/r21 boundary pair check out: `"1e40"` renders 41 plain digits (naive sum also 41, hence
non-discriminating — the plan says so); `"1.5e31"` normalizes to 2 mantissa digits + (31−1) = **32**
digits, exactly at the cap, while the naive "2 + 31 = 33" would reject it (this is why the ACCEPTED
half is the discriminating one, as r20 states); `"1.5e32"` → 33 digits, rejected; `"-1.5e31"` → 32
digits **+1** for the `m` marker = 33 characters, which under a digit-only comparison would fall
through to the generic tag-sanity error — r21's `+1` is arithmetically necessary and its m48 anchor
addition is right. §2.3d class counts (6 refusing / 2 expanding among the 8 discovered) correct.
Four shadowed signature names correct. 15/12/6/26/32/65/73/39/23/8 counts all confirmed above.

**Research-doc citations.** `systematics-vary-litsearch.md:236` does carry the Discussion-#469
"~2-3× … up to ~7-8×" claim *with* the "Content read via summarizing fetch; exact attributions/quotes
UNVERIFIED at word level" caveat the plan cites it for — the line number is exact. lit
§ewkcoffea-confirmed supports every count the plan repeats (12 bases → 24 labels, 6 shift labels,
31/27 axis labels, 27 for wwz4l = 1+20+6, 522 identical processor lines, byte-identical
`ApplyJetSystematics`, 54→14 categories). cba §optimizer §2's table (N=16 → 1333 nodes / 3.1 ms /
34 reduced / 17 stages; N=128 → 7157 / 16.7 ms / 258 / 129; "12.9× nodes → 11.9× time") matches my
independent re-measurement on node counts exactly, and 16.7/3.1 = 5.39 ≈ the "≈5.4" the plan quotes.
cba §histogram §1's constant-Array grep is indeed scoped to "session/array modules", which is exactly
the scoping §4.1 r12 corrects — the plan's self-correction is honest and accurate. cba §corpus §5's
`graph_bloat_note` numbers (O(10⁴) nodes) are as described. The plan's own flag that "§3.3 uses D for
the *shared prefix*, so do not read the cba's letter here" is correct: cba writes Δ = "D+2" with D = the
50-op chain, the plan writes Δ = "K+2" with K = 50 — same 52.

**Prior art (direct clone checks).** `ewkcoffea@063e8d7 wwz4l.py:1204-1207` — the nominal-only
exclusion rule, verbatim; `:396` — "These weights can go outside of the outside sys loop since they do
not depend on pt of mu or jets", the sentence the plan quotes as the hand-partitioned impact analysis;
`ewkcoffea-coffea2023@63abb06 run_wwz4l.py:259-261` — `# Does not work` above the commented
`cloudpickle.dump`; `wwz4l.py:807` `hout = {}` inside the shift loop with `return hout` at `:892`
outside it; `masked_val_cache` **4** hits on the dask-era branch vs **0** on main; `copy.copy(…)
# TODO do we need copy here?` at `c2023:342` vs `copy.deepcopy(…)` at `main:470`. Every one exact.
`coffea @ f34b8bdf CorrectedJetsFactory.py:36-47` seeds PCG64 from the input array's own bytes
(`.to_numpy()[[0,-1]].view("i4")`); `:65-95` `jer_smear` takes ONE `jet_resolution_rand_gauss` while
only `jersf = …[:, variation]` varies, with a signed `deltaPtRel` and a `stochSmear` scaling a signed
gaussian — the non-monotone-by-construction claim is exactly what the code shows.

---

## Closing note

Nothing in this lens blocks the plan. The two LOW items are one-line appendix edits; the three NITs
are optional polish. I did not find a single false binding claim, a single fabricated measurement, or
a single citation into `cba`/`lit` that says something the source does not say.
