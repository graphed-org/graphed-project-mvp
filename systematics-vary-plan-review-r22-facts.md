# systematics-vary plan — review round 14, FACTS / HALLUCINATION lens

- **Lens:** facts / hallucination audit (file:line anchors, measured claims, research-doc citations,
  prior-art claims, arithmetic and counts).
- **Plan revision reviewed:** r22 (`systematics-vary-plan.md`, 5356 lines).
- **Date:** 2026-07-30 (plan-series date; session run 2026-08-12).
- **Verification roots used (all facts below come from these, never from the stale submodules):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607a8ba637ebc1b5db37316adf6e10028dcc` (+ its `.venv`:
    CPython 3.12.10, awkward 2.12.0, cloudpickle 3.1.2)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe22497b64ce624d4880005af7faddf74f7`
    (+ its `.venv`: boost_histogram 1.8.0)
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea4231b8e2329dbee366ef1064db00888e5f6`
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4a628201cfac569b1829aaa6c32655ec92`
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecefee80aa4fdf563d938e4ff906f329126d8` (branch `graphed-mvp`)
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718, WRemnants, narf, mkShapesRDF}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf`
  - clean ephemeral env (`uv run --no-project --with awkward --with pyarrow`): awkward 2.12.0 / pyarrow 25.0.1
  - `graphed-root-prompt.md`, `systematics-vary-{codebase-analysis,litsearch,worklog}.md`

## Scope of what was actually checked

Roughly 120 distinct anchors/claims were opened at the cited lines or re-run as probes. Re-run and
**reproduced exactly**: the §3.3/§5.2a topology numbers (N=16 → stages 17 / reduced 34 / 1333
reachable; N=128 → 129 / 258 / 7157; no-reduction variant 18 / 130; Δ(N=1→2) = 52 with the
terminating reduction, 51 without; reduced kinds `{source:1, stage:N+1, reduction:N}`), the §7.2 r21
compile probe (record ids `0,1,2,3,2` → `outputs() == [1,2]`, two values in first-occurrence order,
`s._store.outputs() == []`), the optimizer-merge probes (`w, w*1.0, w*2.0, w*0.5` → `outputs() ==
[0,1,2]`, 3 values; **fill path: fill node ids `2`,`4` → `outputs() == [2]`, reproduced exactly with a
two-source fixture**), the §2.2/§2.3a property measurements (`dtype`/`ndim`/`shape` delta 0, `T` delta
1; `gnp.ones(s,(4,3)).T` → `GraphedTypeError`), the surface enumerations (`dir(Array)` public =
`['filter','map','node_id','reduce','repartition','session']`; `dir(NumpyArray)` = 32 public;
discovered properties `['T','dtype','ndim','node_id','session','shape']`; annotation-wide filter over
`graphed.__all__` = exactly the 8 verbs with `compile_ir` absent; 65 public gak functions;
`graphed.awkward.num` → `AttributeError`; no `__all__` in `functions.py`; package `__all__` = the six
non-gak functions; m24's 39-name literal), the r22 gak operand-kind probe
(`num`/`unzip`/`drop_none`/`singletons`/`firsts`/`where`/`unflatten` OK, `with_field` →
`GraphedTypeError: … no tuples or records in array`), every boost_histogram probe (sample rejected on
`Double()`/`Weight()`, accepted on `Mean()`/`WeightedMean()` — including with `weight=`; StrCategory
under-declaration `2.0` vs `3.0` flow and over-declaration invisibility; `StrCategory(name=…)`
`TypeError`; string-keyed dict index `TypeError`; `h[{1: ax.index(l)}] == h[{1: bh.loc(l)}]`;
`h.axes.name` `AttributeError` on a two-axis histogram with per-axis `__dict__` names `[None,
'variation']` surviving `spec_of`→`zero_of`, Mean/WeightedMean included; cross-axis add and
multi-axis length `ValueError`s), the awkward/pyarrow probes (broadcast 7-vs-3 `ValueError`;
`float32 ^ float32` `TypeError` in numpy AND awkward with the buffer view working; `metadata` absent
from `ak.to_parquet`'s signature; `ak.to_parquet` vs `pq.write_table` differing bytes for
record/list/flat with `awkward_array_metadata` dropped on the arrow path, `ARROW:schema` always
present, `ak:parameters` array-dependent; `created_by = parquet-cpp-arrow version 25.0.1`; repeat
writes byte-identical; `ak.from_parquet(columns=["murf_0.5"])` → `[]`; `AWKWARD_INFO_KEY` and the
`_connect` route incl. `ak_to_parquet.py:14,417,424-431`), the frontend sketch spellings (`w[:,1]`
`TypeError`, `gak.firsts(w[gak.local_index(w)==1])` → `[2.0, 5.0]`, slice/int accepted on `Array`),
and every grep-shaped claim (five `_array_cls` sites and no other; exactly two `StageError(` hits;
zero `DurablePlan(` in `python/`; `OpSpec.from_callable` only at `shuffle.py:181,188,245,259`; zero
`key_value_metadata`/`with_metadata`; `parquet.py:77` the only metadata use; three `#[pymethods]`
blocks at `:102/:159/:470` with the GraphStore impl closing at `:416` and no id-mapping accessor).

Line anchors opened and confirmed include: `src/{store.rs:73-88,147-156,152-153,185-200},
{node.rs:39-41,102-103}, optimizer/{engine.rs:7-13,22-31, mod.rs:88-116}`;
`python/graphed/{session.py:30,50-51,113,133-140,142-168,170-183,185-204,206-242,245-252,255-286,268,291},
{execute.py:36-45,54,70,85,99-126,104-105,110-117,116-124,126},
{array.py:54,127-128,137-143,283,332-335,344-371,374-391,397-410},
{numpy/array.py:71-74,76-86,132-136,156-161}, {aggregate.py:44-55,68,86,89-93,95,96-104,101},
{projection.py:109-147}, {core/execution.py:206-217,219-224,335-351,378-384,450-457},
{core/plan.py:54,72-76,126,164-176,286-301}, {debug/errors.py:29,75-78,80-81},
{debug/runner.py:6-7,37,57-69}, {provenance.py:26-33,66-79}, {write.py:32-43,77-79},
{numpy/io.py:164-165}, {awkward/io.py:100-127,121,157-185,206-216,230-231},
{numpy/creation.py:27-28,31-75}, {preserve/bundle.py:103-123,206-210,268-288},
{preserve/externals/_base.py:215-248}, {awkward/functions.py:18,118,346,383,400,476,505-509,513,600,612,673,677,687,693,717,722,727,732,737}`;
`graphed-histogram src/graphed_histogram/{boost.py:39-47,55-71,88-98,100-122,127-130,144-150,152-219,244-253,256-295,262,281,282,286}, {_spec.py:19-27}`;
the frozen suites (`core/m4/test_benchmark.py:10,28-33,40-43`,
`core/m4/test_systematics.py:28-53`, `corpus/m05/test_systematics.py:25,33` vs
`graphed-corpus tests/frozen/m05/test_systematics.py:26,34`, `frontend/m5/test_aggregate_plan.py:77,88,102`,
`frontend/m39/test_shuffle_plan_builder.py:58-64`, `checkpoint/m8/{test_resume.py:51-57,analyses.py:114-123}`,
`debug/m6/test_process_boundary.py:7,16`, `preserve/m9/{agc.py:38-66,113-115,test_reproduce.py:19-23}`,
`preserve/m25/…:31`, `awkward/m24/test_interface_parity.py:39-79`,
`graphed-histogram tests/frozen/m23/test_group_plan.py:60-66,68-77,74-75,86,89,99`,
`m29/test_multi_weight_fills.py:75-79,84-87,96`); the repo-fixture facts (23 vendored reference JSONs
of which 15 are systematics; corpus wheel packaging `:28-30`; `graphed` deps/extras/CI `.[dev]` at
`:34,57,143`; `graphed-histogram` runtime deps `:21`, `pythonpath` `:50`, CI `:44,67`, zero corpus
references; `graphed-executors` env `GRAPHED`+`CORPUS` only, 15 frozen dirs, `pythonpath` `:54`, zero
`__init__.py`; `scripts/run-tests.sh:16-25,30`; `graphed-histogram` on PyPI = `0.0.1`); the uproot
fork (`_graphed_write.py:59-64` with zero `compile_ir`/`evaluate_ir`, no frozen tree, 12 flat
`test_graphed_*.py` + 2 helpers, `behaviors/RNTuple.py:1560-1562,1564-1569,562,567`,
`writing/_cascadetree.py:1606`, `behaviors/TBranch.py:2015-2017,2019-2024`); the prior art
(coffea `CorrectedJetsFactory.py:36-47` content-seeded PCG64 and `:64-95` one shared draw with
`jersf = …[:, variation]`, signed `deltaPtRel`; `ewkcoffea@063e8d7:1204-1207,396-397`;
`ewkcoffea-coffea2023@63abb06 wwz4l.py:807-809`, `run_wwz4l.py:259-261,302-313`; zero `.Vary(` in
WRemnants and narf; zero dask surface in `wwz4l@cc71718` with a byte-identical
`ApplyJetSystematics`); the research-doc citations (cba §optimizer §2/§5's Δ = D+2 = 52 table,
12.9× nodes → 11.9× time, 16.7 ms, `stages = N+1` / `2N+2`, the grep-verified absence of invalidation
machinery; cba §histogram §1's session/array-scoped "no constant-Array constructor" grep, §3's
StrCategory probes; cba §corpus §1–§4; lit `systematics-vary-litsearch.md:236` carrying the explicit
word-level-UNVERIFIED caveat on coffea #469's 2-3×/7-8×); the root-prompt anchors (`:25`, `:1262`,
`:1282`, `:1284` header / `:1285` blank / `:1286-1287` sentence, `ops_catalog.md:75`); and the
arithmetic (9-of-15 refs and their filenames; 6 refusing + 2 expanding = the 8 discovered verbs;
`ln24/ln8 = 1.53`, `ln24/ln5.37 = 1.89`, `5.37² ≈ 28.8`, `28.8/24 ≈ 1.2`, `16/5.64 ≈ 2.8`,
`28.8/16 ≈ 1.8`; the e-form renderings and both r22 length formulas — `5em1` = 1+2+1 = 4 chars,
`1.5e31` = 32 plain digits, `-1.5e31` = 33 rendered characters, the 31-digit-mantissa case 31−35 = −4
vs 35 rendered; §6.4c's 3.551 / 2.883 / 3.280 MB and 798 → 169 KB ≈ 4.7× against
`systematics-vary-worklog.md:183,187`).

**Result: the factual substrate of r22 is in very good shape.** No BLOCKER and no HIGH. One measured
literal is contradicted by re-measurement (MID); the rest are evidence-quality and line-precision
items.

---

## Findings

### F1 — MID — m48's §4.1 anchor states a correctionlib `content_hash` literal that does not reproduce against the fixture it names

**Where:** §10/m48 §4.1 anchor bullet (plan `:3564-3566`) and Anchors appendix row "The m9
correctionlib recording path DOES put `systematic` in params" (plan `:4486`); introduced by r22 as
the REJECTED-finding counter-evidence (revision history `:4545-4551`).

**Claim:** "measured r22 vs `graphed-latest@ff7c607`: three labels give three External nodes sharing
`descriptor.content_hash = sha256:cae4dd4b0c20d72dc81b28e8dd877841ff4d452dbc57a18007001318965ae94e`
and differing ONLY in `params["systematic"]`", attributed to the fixture spelling at
`tests/frozen/preserve/m9/agc.py:113-115` with `graphed.preserve.record_external(…)`.

**Evidence (this session, `graphed-latest@ff7c607`, its own `.venv`):** I executed exactly that
spelling — `correctionlib_json()` from `tests/frozen/preserve/m9/agc.py:38-66` (only the
`from graphed_corpus import make_events` line stripped, which the JSON builder does not touch), then
three `record_external(s, CORRECTIONLIB_PLUGIN, corr, [njet], params={"name": "event_sf",
"systematic": syst})` calls. Result: three External nodes (ids 2/3/4) that **do** share ONE
`descriptor.content_hash` and differ only in `params["systematic"]` — but the hash is
`sha256:e72c0da3cb6614cfaf50cea8c93ab740e8229986024a8bad4361e9ae82f4b5cd`, not `cae4dd4b…`. The hash
is a pure function of the payload (`correctionlib_content_hash` = sha256 over
`b"correctionlib-contents-v1"` + canonical JSON, `python/graphed/preserve/externals/correctionlib_external.py:14-18`),
so it is environment-independent and fully determined by the payload. I scanned the fixture's only
degree of freedom, `scale` (`agc.py:38`, default 1.0; the only non-default caller is
`tests/frozen/preserve/m9/test_fingerprint.py:26,46` with `sf_scale=1.10`): `1.0 → e72c0da3…`,
`1.10 → db233194…`, and 1.01/0.99/1.05/0.95/2.0 all differ; the plugin's own two validation samples
hash to `d4855491…`/`9af22f9b…`. Nothing at the pinned revision produces `cae4dd4b…`.

**Impact:** the anchor's *binding* observable (one shared payload hash, `systematic` the only
differing param) is TRUE and reproduces — that half of r22's REJECTED verdict stands. The digest
itself is unverifiable as stated and violates the plan's own reproducibility standard (the standard
it invoked at r13/r14 to withdraw the §6.4e digest pair and at r21 to withdraw `80e8024dc8f3b77d`: a
digest row must name its payload). A test-author or m48 implementer reaching for it burns time and
may file a Test Dispute over a number that was never part of the requirement.

**Suggested fix:** drop the digest from both the anchor bullet and the appendix row, keeping the
qualitative sentence ("three External nodes share ONE `descriptor.content_hash` and differ only in
`params["systematic"]`"); or, if a literal is wanted, name the payload exactly
(`agc.correctionlib_json()` at `scale=1.0`) and use the measured
`sha256:e72c0da3cb6614cfaf50cea8c93ab740e8229986024a8bad4361e9ae82f4b5cd`.

---

### F2 — LOW — r22's cloudpickle digest pair is not re-runnable (the defect the plan twice used to withdraw other digests)

**Where:** §7.3 (`:2725-2728`), Anchors appendix row "Adding ONE defaulted field to the worker closure
dataclass changes its cloudpickle bytes" (`:4485`), revision history (`:4503-4505`).

**Claim:** "Measured r22 (cloudpickle 3.1.2, CPython 3.12.10): the SAME module name, class name and
field names, with vs without one `variation_labels: tuple | None = None` field → sha256[:16]
`8d058bf867dc6bcd` vs `22a566276fd6077d`".

**Evidence:** the toolchain is right (the pinned venv is CPython 3.12.10 / cloudpickle 3.1.2,
verified), and the **qualitative claim reproduces**: two importable module-level frozen dataclasses
differing only by one defaulted field pickle to different bytes (my probe: `c81bb31973fa2464` vs
`e64112899925b336`). But the row names neither the module, nor the class, nor the field list, nor the
instance values, all of which enter cloudpickle's bytes for an importable class — which is verbatim
the deficiency §7.3 itself cites when withdrawing r18–r20's `80e8024dc8f3b77d` ("cloudpickle bytes
for an importable class embed its module, qualname and field names, none of which that row named, so
the digest is not re-runnable") and which r13 cited when withdrawing the r12 §6.4e digest pair. The
neighbouring §8.2(i) triple (`b7984b3c…`/`2778da7a…`/`97429e59…`) is the counter-example done right:
it names its payload verbatim.

**Impact:** evidence-quality only; the milestone correction (churn lands at m48, m49 only populates)
rests on the qualitative fact, which holds.

**Suggested fix:** replace the pair with the qualitative statement (the shape §7.3 already adopted
for the withdrawn r21 digest), or name the payload fully — module name, class name, the exact field
list and the instance's field values.

---

### F3 — LOW — "`mypy --strict` on src AND tests" is cited to a line that does not establish the "AND tests" half

**Where:** §7.2 (`:2568-2569`) — "m48 freezes a 'dummy' read-back under the DoD's `mypy --strict` on
src AND tests (measured, `graphed pyproject.toml:83` → `strict = true`)"; the same phrasing recurs in
§6.1a (`:1572-1573`) and §10's DoD line (`:4305`).

**Evidence:** `graphed pyproject.toml:83` IS `strict = true` (verified) — but the very next line,
`:84`, is `files = ["python"]`, i.e. the test tree is **outside** mypy's file set; the pre-commit
`mypy` hook runs with `pass_filenames: false` on that config (`.pre-commit-config.yaml`), and CI runs
the hook (`.github/workflows/ci.yml:38`). `graphed-histogram` is the same shape:
`pyproject.toml:70-73` → `strict = true`, `files = ["src"]`. So today neither repo type-checks tests.
The root prompt's R0.4a does bind the wider scope and explicitly says so —
`graphed-root-prompt.md:147-153`, closing with "(Repos still configured `src`-only are a known
cross-cutting cleanup — widen each `mypy`/lint config and annotate the tests.)".

**Impact:** the requirement is real (R0.4a binds), so nothing in m48 changes; but the parenthetical
presents `:83` as *measurement* of a property the file's next line contradicts, and it is the sole
stated ground for r22's `()`-dummy binding. A reader checking it finds a src-only config and may
conclude the dummy-type argument is unfounded.

**Suggested fix:** re-word to cite R0.4a as the binding source and note the measured state, e.g.
"under R0.4a's `mypy --strict` over src AND tests (`graphed-root-prompt.md:147-153`; `graphed` is
still configured `files = ["python"]`, `pyproject.toml:84`, one of the repos R0.4a names as a pending
cleanup — m48's own suite must type-check either way)".

---

### F4 — LOW — the appendix `read_columns` row misattributes two of its four spans

**Where:** Anchors appendix row "`read_columns` carries ONE conservative flag across ALL arrays
passed" (`:4487`).

**Evidence (`python/graphed/projection.py`, measured by `grep -n`):** `conservative = False` is at
**`:123`**, not `:130` — `:130` is `nonlocal conservative` inside `on_op`. The
`for array in arrays:` / `array.session.walk(...)` pair is at **`:143-144`**, not `:142-143`. The
other two pointers are right: `conservative = True` at `:140`, `if conservative or not needed: return
None` at `:145-146`, and the function span `:109-147` is exact. The body's r22 citations in §5.3
(`:130-146`, `:140`, `:145`) and §2.3d (`:109-115,145-146`) are all correct, so only the appendix row
drifts.

**Impact:** none on meaning; a reader following `:130` lands on a `nonlocal` declaration.

**Suggested fix:** `conservative = False` `:123`; `for array in arrays: … walk(...)` `:143-144`.

---

### F5 — LOW — one Anchors-appendix row still attributes the closure churn to m49 after r22 moved it to m48

**Where:** appendix row `:4450`, header text: "…and no `Plan → DurablePlan` bridge ships (**why
§7.3's m49 churn is SCOPED**, r17)".

**Evidence:** r22 bindingly relocates the churn: §7.3 `:2719-2732` ("One-time churn on landing m48,
SCOPED (r17; the MILESTONE corrected from m49 in r22) … r17–r21 attributed this to m49 and m50's
FROZEN docs anchor repeated it; both are corrected"), m50's docs anchor `:4127-4131` ("**m48's**
one-time closure churn (**milestone corrected in r22**)"), and the sibling appendix row `:4485`
("why §7.3's one-time churn lands at m48 … not at m49"). Row `:4450` was not swept.

**Impact:** two appendix rows now disagree about the milestone; m50's docs anchor is written to be
frozen, and §10 calls this document "the acceptance skeleton the test-author starts from", so a
stale milestone in the anchors table is exactly the false-attribution class r22's own correction
exists to prevent.

**Suggested fix:** row `:4450` → "why §7.3's **m48** churn is SCOPED (r17; milestone corrected r22)".

---

### F6 — LOW — a cluster of meaning-preserving span drifts (grouped)

All verified this session; each claim is otherwise true, only the span is imprecise:

| Cited as | Measured | Where cited |
|---|---|---|
| `graphed-histogram …/boost.py:254-292` / `:255-292` / `:256-292` for `plan()` | `def plan(` at `:256`, closing `)` at `:295` | §6.1a `:1548`, §7.2 `:2632`, §10 `:3084`, `:4104`, `:4479` |
| `boost.py:245-255` for `Histogram.plan` passing `_SumFills`/`_ZeroHist` | the `return aggregate_plan(` block is `:244-253` (`_SumFills` `:246`, `_ZeroHist` `:248`) | §6.1c `:1618`, `:1683`, `:3236`, `:4478` |
| `boost.py:101-118` for `_GroupReduce.__call__`'s `-> dict[str, bh.Histogram]` | the method is `:108-117` (class `:101-117`) | §10 `:3433` |
| `python/graphed/numpy/io.py:158-173` as "the numpy idiom having its own 1-D-capped implementation" | the numpy-idiom `def to_parquet` is at `:182`; `:158-173` is the middle of `_WritePart.__call__`, whose cap is `:164-165` | §6.4a `:2073`, appendix `:4451` |
| `graphed pyproject.toml:114-127` for `tests/_corpus` on `pythonpath` | `pythonpath = [` at `:115`, `"tests/_corpus"` at `:117`, list closes `:127` | `:3148`, `:4468` |
| `graphed-executors .github/workflows/ci.yml:44,67,101` as "runs `pytest tests/frozen` in one process" | `:44` and `:67` run the whole tree; `:101` runs the m42–m45 subset only (`:153` the m46/m47 subset) | §10 `:3006` |

**Suggested fix:** correct the spans; none changes a requirement.

---

### F7 — NIT — `histograms.py` is cited beside an `analyses/` path but does not live there

**Where:** §10/m48 matrix anchor (`:3168-3169`) and appendix row `:4447`:
"`tests/_corpus/graphed_corpus/analyses/systematics.py:79,102,50`; `histograms.py:20`, `:35-37`,
`:40-43`".

**Evidence:** the corpus package's `histograms.py` is at
`tests/_corpus/graphed_corpus/histograms.py` — one level ABOVE `analyses/`
(`tests/_corpus/graphed_corpus/analyses/` contains `__init__.py`, `adl.py`, `systematics.py` only).
The line numbers themselves are exactly right, and r22's correction of them is verified:
`STABLE_DECIMALS = 6` at `:20`, `bin_values` `:35-37`, `fingerprint` `:40-43` with the
`return hashlib.sha256(payload).hexdigest()[:16]` at `:43`. The `systematics.py:79,102,50` triple is
also verified (pre-fill `np.round` at `:79` and `:102`, the view rounding at `:50`).

**Suggested fix:** spell the bare filename as `graphed_corpus/histograms.py` (or give the full
vendored path) so the adjacent `analyses/` prefix cannot be read as applying to it.

---

## Verdict

**CLEAN for this lens at the BLOCKER/HIGH level** — nothing in r22's factual substrate would make a
milestone unimplementable or freeze a wrong test, and every load-bearing measured claim I re-ran
reproduced (including all of r22's new probes: the gak operand-kind matrix, the `sample=` storage
matrix, `to_parquet`'s compile-at-the-call, the `read_columns` single-`conservative`-flag behaviour,
and the corrected m05 / `histograms.py` spans).

**DIRTY at MID/LOW**: one measured digest is contradicted by re-measurement against the fixture it
names (F1), one is not re-runnable by the plan's own standard (F2), one citation does not establish
the claim it is offered for (F3), and four line/attribution drifts remain (F4–F7). All have
mechanical fixes and none touches a requirement's meaning.
