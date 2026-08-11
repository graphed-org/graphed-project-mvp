# systematics-vary plan — review r12, FACTS / HALLUCINATION AUDIT

- **Lens:** facts / hallucination audit — every `file:line` anchor (body + Anchors appendix), every
  measured claim, every citation into the two research docs, prior-art claims, arithmetic and counts.
- **Plan revision reviewed:** r12 (`systematics-vary-plan.md`, 2205 lines, read in full).
- **Date:** 2026-07-30.
- **Verification roots used** (all code facts come from these, never the workdir submodules):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (consolidated `graphed`; its `.venv` used for
    in-context probes)
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42` (`graphed-executors`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (its `.venv` ships bh **1.8.0**)
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecef` (branch `graphed-mvp`)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718}`
  - `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf`
  - pinned-version probes via `uv run --no-project --with awkward==2.12.0 --with pyarrow==25.0.0`
- **Coverage:** ~110 distinct anchors opened at the cited lines; 9 measured claims re-run in this
  session (reduced-shape/arena-delta integers, interning + output dedup, bh StrCategory overflow +
  name lookup, `ak.broadcast_arrays` mismatch, `ak.to_parquet` vs `pq.write_table`, dotted parquet
  column read, `**`-unpacking, awkward tuple-subscript + masked inner index, gak surface counts);
  prior-art claims spot-verified against the clones (byte-identical `ApplyJetSystematics`, zero dask
  surface, exclusion rule, `hout = {}` scoping, cloudpickle "Does not work").

**Headline: the factual substrate is in very good shape.** Every load-bearing measurement I re-ran
reproduced *exactly* — the §3.3/§5.2a integers (17/34, 129/258, Δ=52, and the without-reduction
17/18, 129/130, Δ=51), the §7.2 dedup measurement (1 value vs 2), the §2.3e interning measurement
(node id 1 twice), the bh non-growth overflow (`sum 2.0` / `sum(flow=True) 3.0`), the
`ak.broadcast_arrays` message verbatim, `ak.from_parquet(columns=["murf_0.5"])` returning no fields,
CPython `**`-unpacking of `'0.5'`, `w[:, 1]` raising, `gak.firsts(w[gak.local_index(w)==1])` →
`[2, 5]`, and 73 defs / 65 public / 0 `__all__` in gak. No BLOCKER and no HIGH. What follows is
three MID defects, three LOW, three NIT.

---

## MID-1 — §2.3d's "EXHAUSTIVE" module-verb enumeration is measurably not exhaustive: `pack_key`, `shuffle_plan`, `join_plan` are undisposed

**Section:** §2.3(d) (plan `:464-476`); Anchors row (plan `:1926`).

**Detail.** §2.3d opens: *"Module verbs and sinks — the enumeration is EXHAUSTIVE over `graphed`'s
public Array-consuming surface (r12; the r11 list named three and left the rest undisposed, which is
not harmless…)"*, then enumerates `join`, `repartition`, `apply`, `read_columns`, `compile_ir`,
`evaluate_ir`, `aggregate_plan`, `graphed.awkward.to_parquet`, `Histogram.fill`. Measured against the
cited surface (`python/graphed/__init__.py:8-25` + `__all__` `:27-58`), **three exported public verbs
take an `Array` as their first parameter and receive no disposition**:

```
/private/tmp/claude-501/graphed-latest/python/graphed/shuffle.py
  84: def pack_key(array: Array, *, on: Sequence[str]) -> Array:
 142: def shuffle_plan(output: Array, *, reduce=…, combine=…, empty=…, …) -> DurablePlanV2:
 208: def join_plan(output: Array, *, backend=None, steps_per_file: int = 1) -> DurablePlanV2:
```
All three are in `__all__` (`__init__.py:50-57`: `join`, `join_plan`, `pack_key`, `read_columns`,
`repartition`, `shuffle_plan`). `pack_key` does `array.session.record_op(...)` (`:89`);
`shuffle_plan`/`join_plan` do `session = output.session` (`:155`, `:220`).

The failure mode §2.3d itself names (an unhandled duck-typed read becoming a recorded `field` op) does
*not* bite here, because §2.2 makes `Varied.session` raise `AttributeError` — so a `Varied` passed to
any of the three dies with an opaque `AttributeError`, not a guided refusal. That is a smaller harm
than the plan's own worst case, but the requirement is stated as an exhaustiveness claim the m48
test-author is meant to work from, and as written it is false.

**Evidence.** `grep -n "^def " …/shuffle.py`; signatures read at `shuffle.py:84,142,208`;
`__init__.py:27-58` read in full.

**Suggested fix.** Add one clause to §2.3d disposing all three (the natural reading: they **refuse**
with the §5.4/§2.2-shaped error naming `graphed.universe`, since a varied shuffle/join is already
refused by §5.4 and a varied `pack_key` has no defined semantics), and make the m48 anchor's
enumeration dynamic over `graphed.__all__` filtered to Array-first-parameter callables, so a future
verb cannot arrive undisposed — the same self-repairing rule §2.3a/c already adopt.

---

## MID-2 — §6.2(i-bis)'s supporting measurement (`h.axes.name == ('variation',)`) holds only for a one-axis histogram; in every configuration axis mode can actually produce, it raises `AttributeError`

**Section:** §6.2(i-bis) (plan `:993-1000`, esp. `:998`); Anchors row (plan `:1918`).

**Detail.** The plan binds: *"(1) the frontend **writes the axis name into
`axis.__dict__["name"] = "variation"`** … so the handle survives the spec/`zero_of` rebuild
(measured: after setting it, `h.axes.name == ('variation',)`); (2) `graphed.labels`/`graphed.universe`
resolve the axis POSITION from that name and slice by index."*

`bh.Histogram.axes.__getattr__` maps the attribute over **every** axis
(`boost_histogram/axis/__init__.py:925`), and an axis without the key raises. So the measurement is
true only for a histogram whose *sole* axis is the variation axis — which axis mode never produces
(the variation axis is added alongside the user's ≥1 value axes). Measured, bh **1.8.0**:

```
single-axis axes.name: ('variation',)
two-axis  axes.name -> AttributeError            # bh.Histogram(Regular(3,0,1), named StrCategory)
per-axis dict get:    [None, 'variation']
spec roundtrip names: [None, 'variation']        # graphed_histogram._spec.spec_of -> zero_of
```

The *binding* half — (2), resolve position from the name — remains implementable (iterate
`axis.__dict__.get("name")`), and the round-trip through `_spec.py:31-37`/`:81-84` is confirmed. But
the only evidence the plan offers for "the handle survives" is an unrepresentative configuration, and
an m50 test-author writing the obvious oracle (`h.axes.name`) gets an `AttributeError` on a correct
implementation — avoidable churn inside a frozen suite.

**Evidence.** Probe run against `graphed-histogram-latest/.venv` (bh 1.8.0), shown above; the other
claims in the same anchor row reproduce exactly (`StrCategory(name=…)` → `TypeError: unexpected
keyword argument 'name'`; `h[{'variation': bh.loc('jes_up')}]` → `TypeError: list indices must be
integers or slices, not str`; `h[{1: bh.loc('jes_up')}]` works).

**Suggested fix.** Restate the measurement as what it is: *"the name survives the spec/`zero_of`
rebuild — measured on a two-axis histogram, `[a.__dict__.get('name') for a in z.axes]` ==
`[None, 'variation']`; note `h.axes.name` raises `AttributeError` unless EVERY axis carries a name, so
the position lookup must read `axis.__dict__`, not `h.axes.name`."* Add the same caution to the m50
(i-bis) anchor line (plan `:1696-1706`).

---

## MID-3 — internal contradiction: m49's repo list and §10's directory pins both exclude a `graphed-histogram tests/frozen/m49`, which m49 anchor (i) bindingly requires

**Section:** §10 preamble (plan `:1356-1366`, esp. `:1364-1365`); m49 header (plan `:1612`); m49
anchor (i) (plan `:1616-1631`).

**Detail.** Three statements in the same section disagree after r12 moved the 15-reference matrix:

1. §10 preamble `:1364-1365`: *"`graphed-executors` = flat `tests/frozen/m49`; **`graphed-histogram`
   = flat `tests/frozen/m48` and `tests/frozen/m50`** (its existing shape — `m23/`, `m29/`; m50's
   primary target §6.2 lives there, so its directory is pinned too …)"* — no m49 directory for
   `graphed-histogram`.
2. m49 header `:1612`: *"**m49 — shift path + impact + executor end-to-end** (repos: `graphed` +
   `graphed-executors`)."* — `graphed-histogram` is not a listed m49 repo.
3. m49 anchor (i) `:1616`: *"(i) **`graphed-histogram`, flat `tests/frozen/m49`** — the matrix through
   the frontend … **Moved out of `graphed` in r12** …"*.

The §10 preamble explicitly exists to make "which anchor is frozen where" decided (it is the reason
m48's split was written out); leaving m49 with two contradictory answers reintroduces exactly the gap
it closes. Mechanically the move is fine (that repo's tree is flat `m23/`, `m29/` — verified), so this
is bookkeeping, not design.

**Evidence.** Plan lines quoted above; `ls /private/tmp/claude-501/graphed-histogram-latest/tests/frozen`
→ `m23  m29`.

**Suggested fix.** In `:1364-1365` write `**graphed-histogram** = flat tests/frozen/m48,
tests/frozen/m49 and tests/frozen/m50`, and amend the m49 header repo list to
`graphed` + `graphed-histogram` + `graphed-executors`.

---

## LOW-1 — three stale line anchors (meaning unchanged), plus three off-by-one range starts

**Sections/anchors:**

| Cited | Actual (verified) | Where in the plan |
|---|---|---|
| `execute.py:74` for `ids = [arr.node_id for arr in outputs]` | `python/graphed/execute.py:70` (`:74` is `blob = bytes(`) | `:407`, `:473`, Anchors `:1926` |
| `aggregate.py:66-72` for "consume `arr.node_id`/`arr.session` directly" | `aggregate.py:86` (`session = outputs[0].session`); `:66-72` is the blank line + `def aggregate_plan` signature head | `:473`, Anchors `:1926` |
| `io.py:122` for `(out,) = evaluate_ir(...)` | `python/graphed/awkward/io.py:121` (`:122` is `result = ak.Array(out)`) | `:1185` |
| `graphed pyproject.toml:41-48` for the `dev` extra | `dev` is `:42-48` (`:41` closes the `all` extra) | `:1414`, `:1624`, Anchors `:1929` |
| `graphed-histogram pyproject.toml:24-38` for the dev extra | `dev` is `:25-39` (`:24` is a comment) | `:900-901`, Anchors `:1917` |
| `scripts/run-tests.sh:16-24,29` | `SUITES` is `:16-25`; `SPLIT_PKGS` is `:30` (`:27-29` is its comment) | `:1371-1372` |

None of these changes a claim's meaning — each cited range is within a few lines of the real content
and the surrounding claim is true. Reported per the lens's "stale line numbers even if the claim is
otherwise true" rule.

**Suggested fix.** Repoint the six.

---

## LOW-2 — §4.3's "(`Histogram._fill_nodes` is private)" is false: a public `fill_nodes()` accessor exists

**Section:** §4.3 (plan `:746-748`); echoed by the m48 §4.3 anchor (`:1447-1453`).

**Detail.** The plan justifies routing per-label fill-node extraction through the §7.2 map with
*"the only public per-label fill-node channel (`Histogram._fill_nodes` is private)"*. Measured:

```
graphed-histogram/src/graphed_histogram/boost.py
 215:    def staged_fills(self) -> int:      return len(self._fill_nodes)
 218:    def fill_nodes(self) -> list[Array]: return list(self._fill_nodes)
 221:    def evaluators(self) -> dict[str, FillEvaluator]:
```
`fill_nodes()` is public and already used by frozen tests (`graphed-histogram
tests/frozen/m29/test_multi_weight_fills.py:84`, `:95` — `h.fill_nodes()[0].node_id`).

The *substantive* claim survives: `fill_nodes()` returns an unlabeled list, so it is not a per-**label**
channel. But the stated reason is wrong, and an m48 test-author reading it may conclude the staged
node list is unreachable when it is one public call away (paired with the §2.4/§6.1d bound label
order, it is a plausible alternative oracle).

**Suggested fix.** Replace the parenthetical with: *"(`Histogram.fill_nodes()` is public but
UNLABELED — it returns the staged nodes in fill order with no label attribution, so it is not a
per-label channel)"*.

---

## LOW-3 — §6.4e's recorded KV-metadata sets are incomplete and array-dependent; the sha256 pair is not reproducible from the plan as stated

**Section:** §6.4(e) (plan `:1164-1174`); Anchors row (plan `:1869`).

**Detail.** The plan records: *"measured this session (awkward 2.12.0 / pyarrow 25.0.0),
`ak.to_parquet(a, p)` and `pq.write_table(ak.to_arrow_table(a), p)` produce different bytes
(sha256[:16] `ad1725aca34f2bbb` vs `43b093e8bc616bd7`) and different key-value metadata sets
(`{awkward_array_metadata, ak:parameters}` vs `{ak:parameters}` …)"*.

Re-measured at the same pinned versions:

```
record array : sha 585c0194791aaf08 / e0ee265f2c7989e4
  kv ak = ['ARROW:schema', 'ak:parameters', 'awkward_array_metadata']
  kv pq = ['ARROW:schema', 'ak:parameters']
list-of-float: sha 879dccec67293a60 / 703527583227e976
  kv ak = ['ARROW:schema', 'awkward_array_metadata']
  kv pq = ['ARROW:schema']
'metadata' in signature(ak.to_parquet) -> False ;  created_by = 'parquet-cpp-arrow version 25.0.0'
```

Three corrections: (a) **both** files always carry `ARROW:schema`, which the recorded sets omit — a
test-author freezing "KV set == {awkward_array_metadata, ak:parameters}" writes a red test; (b)
`ak:parameters` appears only for arrays that carry awkward parameters (records), not for a plain
numeric array — so the set is array-dependent, not a property of the two writers; (c) the sha256
pair is unreproducible as stated because the plan does not name the array written (my two probes give
four different digests), and the worklog does not record that probe's input either.

The **binding conclusions are all verified true**: different bytes, the arrow path loses
`awkward_array_metadata`, and `ak.to_parquet` has no `metadata` parameter — so §6.4e's conditional
writer swap stands.

**Suggested fix.** Restate as *"the arrow path drops awkward's `awkward_array_metadata` KV entry
(both paths keep `ARROW:schema`; `ak:parameters` appears when the array carries parameters), and the
two files differ byte-for-byte"* and either drop the two digests or name the probe array.

---

## NIT-1 — §8.2's "enumerated every `#[pymethods]` fn in `src/lib.rs:106-543`" omits 13 of them (conclusion still correct)

**Section:** §8.2(i) (plan `:1284-1288`); Anchors row (plan `:1921`).

The listed 15 names are `PyGraphStore`'s methods. `src/lib.rs:106-543` also contains
`PyPayloadDescriptor`'s 7 (`new`, `kind`, `content_hash`, `framework`, `version`, `io_schema`,
`preprocessing_ref`, `:106-147`) and `PyIncrementalReducer`'s 6 (`new`, `step`, `watermark`,
`total_work`, `canonical_count`, `finalize`, `:473-539`). I checked the omitted ones independently:
`reduce`/`reduce_incremental`/`finalize` all return `(PyGraphStore, HashMap<String, usize>)`
(`lib.rs:365-399`, `:515-538`), so **the conclusion — no record→reduced id map on the PyO3 surface,
hence a new read-only accessor is an m49 Implementation Target — is verified true.** Only the
"enumerated every" phrasing is wrong.

**Suggested fix.** "…enumerated every `#[pymethods]` fn on `PyGraphStore` (`src/lib.rs:159-468`);
`PyPayloadDescriptor` and `PyIncrementalReducer` expose only descriptor fields and reduce/report
returns of shape `(store, report_map)`."

---

## NIT-2 — the naming note's "matches RDataFrame's `Vary` precedent" overreaches on the label separator

**Section:** naming callout (plan `:16-20`).

The plan says labels are `f"{name}_{tag}"` and that *"This matches RDataFrame's `Vary` precedent
(lit §rdf-vary §6)"*. The cited section records RDF's key as **`variationName + ":" + tag`**
(`"pt:down"`) — a colon (`systematics-vary-litsearch.md:76`). The underscore matches RDF's *Snapshot
column* convention (`<col>__<variationName>_<tag>`, same line) and the corpus reference names
(verified: `ttbar_4j1b_btag_up`, `ttgamma_pho_down`, … 15 files under
`graphed-corpus-latest/corpus/references/`), not RDF's result keys. The naming decision is
owner-locked and not at issue; only the citation is imprecise.

**Suggested fix.** "…matches RDF's *vocabulary* (`vary`/variation/reserved `"nominal"`; RDF's result
keys use `:`, its Snapshot columns use `_`) and — verbatim — the 15 stored corpus reference names."

---

## NIT-3 — §2.3b: only `photons` is sliced by the JES-varied selection at `systematics.py:91-92`, not `photons`/`muons`

**Section:** §2.3(b) (plan `:436-438`); m48 anchor (plan `:1490-1495`).

Verified at `graphed-corpus-latest/src/graphed_corpus/analyses/systematics.py`:

```
 91:  sel = (ak.num(photons, axis=1) >= 1) & (ak.num(muons, axis=1) >= 1) & (ak.num(good_jets, axis=1) >= 2)
 92:  lead_pho_pt = ak.firsts(photons[sel].pt)
```
`muons` contributes to building `sel` but is never indexed by it. The requirement (plain-`Array`
`__getitem__`/`filter` must learn a `Varied` mask) is unaffected — `photons[sel]` alone establishes it.

**Suggested fix.** Drop `/muons` from the two sentences.

---

## Things I re-measured that were EXACT (no finding — recorded for the file)

| Claim | Result |
|---|---|
| §3.3 reduced shape, D=500/K=50: N=16 → (stages 17, reduced 34); N=128 → (129, 258) | exact |
| §3.3 without the terminating reduction: N=16 → 18, N=128 → 130 | exact |
| §5.2a arena Δ(N=1→2) = 52 with reduction / 51 without | exact |
| §3.3 headroom: time(128)/time(16) ≈ 5.3 vs the 24.0 gate (cba records 3.1/16.7 ms ⇒ ≈5.4) | consistent |
| Part I §3 "12.9× nodes → 11.9× time" | consistent — it is the cba table's N=1→N=128 span (7157/553, 16.7/1.4), not 16→128 |
| §7.2 dedup: `compile_ir(s,b,c)` identical → 1 value; `compile_ir(s,b,d)` → 2 | exact |
| §2.3e interning: `src * 2.0` twice → node id 1 both times | exact |
| §6.2 non-growth StrCategory silently overflows: `sum 2.0` vs `sum(flow=True) 3.0`, `Traits(overflow=True, growth=False)` | exact (on bh 1.8.0) |
| §6.2(i-bis) `StrCategory(name=…)` / `h[{"variation": …}]` both `TypeError`; `h[{1: bh.loc(…)}]` works | exact |
| §6.1d `ak.broadcast_arrays` 7 vs 3 → `ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`; jagged 3-row broadcasts fine | verbatim |
| §1.1 `ak.from_parquet(columns=["murf_0.5"])` silently empty; `[["murf_0.5"]]` works | exact |
| §1.1 CPython 3.12.10 `f(**{'0.5': 1})` accepted | exact |
| §2.6(i) `w[:, 1]` → `TypeError: unsupported index (slice(None, None, None), 1)`; `gak.firsts(w[gak.local_index(w)==1])` → `[2, 5]` | exact |
| §2.3c/e gak surface: 73 `def`s / 65 public / 0 `__all__`; `_comb_params` `:42`, `_reduce` `:154`; every cited function line (`join :18`, `zip :118`, `linear_fit :346`, `concatenate :383`, `where :400`, `apply_correction :476`, `onnx_inference :513`, `unflatten :600`, `full_like :612`, `broadcast_arrays :677`, `unzip :687`, `to_list :693`, `fields :717`, `type_of :722`, `backend_of :727`, `head :732`, `sample :737`) | all exact |
| §2.3a `Array` methods `filter/map/reduce/repartition` `:374-391`; numpy idiom 25 methods in `:92-190`, tuple `__getitem__` `:132-136`, `__slots__ = ()` `:71-74` | exact (25 counted) |
| §2.3e five `_array_cls` call sites `:140,168,183,204,242`, none outside `session.py` | exact |
| §6.4g parquet footer `created_by = parquet-cpp-arrow version <arrow version>`; repeat writes byte-identical | exact (25.0.0 under pyarrow 25.0.0) |
| §6.4c compression numbers (2.88/3.55/3.28 MB; masks 798 KB → 169 KB ≈ 4.7×) | consistent with the worklog's recorded methodology (float32, 1M, zlib-6, seed 42) and self-consistent (798/169 = 4.72) |
| m48 count "9 of the 15 refs" (6 ttbar + 3 ttgamma; 6 shift refs remain) | arithmetic correct against the 15 files on disk |
| §6.1b `1 + \|S\| + \|W\|` vs §6.2 `1 + \|S\|` | internally consistent with §2.4's no-cross-product rule and with `_fill_nodes` being a staged-fill list |
| m24 anti-drift pin is a **39**-name literal at `:39-79` | exact (counted) |
| uproot repo: no frozen tree, 12 flat `test_graphed_*.py` + 2 helpers, zero `tests/frozen` strings, `_graphed_write.py:59-64` with zero `compile_ir`/`evaluate_ir` | exact |
| RNTuple `:1560-1562` exact-first / `:1564-1569` dot-split / `to_akform` `:562,567`; TBranch `:2015-2017` exact-first / `:2019-2024` `/`-split; `_cascadetree.py:1606` `.`-join | all exact |
| coffea `CorrectedJetsFactory.py:36-47` content-seeded PCG64; `:64-95` one shared `jet_resolution_rand_gauss`, `jersf = …[:, variation]` `:84`, signed `deltaPtRel` `:85`, hybrid det/stoch `:88-89` | exact — §5.5's non-monotonicity claim is sound |
| prior art: `ewkcoffea@063e8d7` exclusion rule `:1204-1207`, impact-partition comment `:396-397`; `@63abb06` `masked_val_cache`/`masked_weights_cache` `:808-809`, `hout = {}` inside the loop `:807`, `# Does not work` + commented `cloudpickle.dump` `run_wwz4l.py:259-261`; `wwz4l@cc71718` byte-identical `ApplyJetSystematics`, zero dask surface, `:395-400` shift list, `:711-718` exclusion rule | all confirmed |
| "522 identical processor lines" (lit) | corroborated: my independent difflib run gives 658 matching lines / 509 matching non-blank — same order, methodology-dependent |
| lit §coffea-sys #469 caveat is at `systematics-vary-litsearch.md:236` and does carry the UNVERIFIED wording | exact |
| root prompt `:25`, `:1262`, `:1282`, `:1284`, `:1286`; `ops_catalog.md:75` in both copies | exact, quoted text matches |
| fixture facts: `graphed` has no `graphed-histogram` in ANY extra; CI installs `.[dev]` at `ci.yml:34,57,143`; `importorskip` at m25`:31`/m27`:185,207`/m30`:155`; `graphed-histogram` has 0 corpus hits; corpus wheel packages only `src/graphed_corpus`; `graphed-executors` has no histogram dep and does carry `graphed-corpus`; 23 vendored JSONs; `graphed`'s only cross-process frozen test is m6's pool | all exact |
| core/IR anchors: `store.rs:73-88`, `:147-156`, `:152-153`; `node.rs:39-41`, `:41-85` (variant heads `42/46/51/56/64/72/81`), `:102-103`; `engine.rs:7-13`, `:54-56`; `optimizer/mod.rs:1-11`, `:88-116` (`remap` never returned) | all exact |
| frontend/exec anchors: `array.py:54,127-128,137-143,156,245-275,332-335,344-371,369-371,374-391,397-410`; `session.py:30,39,113-125,133-242,245-252`; `execute.py:36-45,54-70,99-126,104-105,110-117,126`; `aggregate.py:44-65,57-65,89-93,95-97,101`; `projection.py:109`; `provenance.py:26-33,66-79`; `debug/errors.py:29-81` (`__reduce__` via `__dict__` `:67-68`, hand-written `__hash__` `:80-81`); `debug/runner.py:6-7,37,57-69`; exactly two `StageError(` hits; `plan.py:72-90,164-176,286-301`; `checkpoint/store.py:31-41,62-73`; `checkpoint/runner.py:100-109`; `shuffle.py:5-8,92-96,170,232`; `write.py:32-43,77-79`; `numpy/io.py:158-173,163-171`; `numpy/creation.py:27-28,31-75` + `numpy/__init__.py:578`; `awkward/io.py:111-127,157-185,206-216`; `awkward/__init__.py:14,17-31,30`; `parquet.py:77` (+ no `key_value_metadata`/`with_metadata` anywhere) | all exact |
| histogram anchors: `boost.py:39-47,60-71,88-98,100-122,146-150,153-163,160-161,166-174,180-212,205-206,245-255,282`; `_spec.py:31-37,70,74,81-84,115-135` | all exact |
| corpus anchors: `systematics.py:25-36,39-45,50,60-61,74-76,79,102,107-112`; `:73` blank, `:75` the `ht` sum; frozen `corpus/m05/test_systematics.py` both named tests | all exact |
| m9/preserve anchors: `agc.py:38-66,56-62,94-118,106-107`; `bundle.py:103-123,206-210`; `test_reproduce.py:19-23` | all exact |
| golden/witness patterns: `core/m40/test_join_serialize.py:83-99` (literal `b"GIR1\x03…"`); `m29/test_multi_weight_fills.py:82-99,93-99`; `m23/test_group_plan.py:60-66,68-77`; `m7/analyses.py:118-127`; `m7/adl.py:124-158,156-158`; `submit/engine.py:381-396` | all exact |

---

## Verdict

**DIRTY — but only just, and with no BLOCKER and no HIGH.**

3 MID / 3 LOW / 3 NIT. Two MIDs are evidence defects that would mislead a test-author into a red
frozen assertion (MID-2) or leave a real surface undisposed at freeze (MID-1); the third (MID-3) is a
bookkeeping contradiction introduced by r12's own anchor move. Everything else is line-number drift
and citation phrasing.

The measured substrate of this plan is the strongest I have audited in this series: every integer,
every probe result, and every prior-art claim I could re-run came back exact, and the two claims that
r10/r11/r12 explicitly withdrew-and-rebound (§8.2's transport channel, §6.2's declaration point) are
correctly grounded at r12 — including the non-obvious one I re-derived independently, that
`reduce`/`finalize` return only `(store, report_map)` and therefore no record→reduced id map exists.

Fixing MID-1 through MID-3 and repointing the six stale anchors should close this lens.
