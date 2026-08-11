# `systematics-vary-plan.md` r10 — review round 2, FACTS / HALLUCINATION lens

- **Lens:** facts / hallucination audit — every `file:line` anchor (body + Anchors appendix), every
  measured/"re-measured this session" claim, every citation into the two research docs, every
  prior-art claim, and all arithmetic/counts.
- **Plan revision reviewed:** r10 (1389 lines).
- **Date:** 2026-07-30.
- **Verification roots used (revisions confirmed by `git log -1` in-session):**
  - `/private/tmp/claude-501/graphed-latest` — `ff7c607a8ba637ebc1b5db37316adf6e10028dcc`
  - `/private/tmp/claude-501/graphed-exec-check` — `201ea4231b8e2329dbee366ef1064db00888e5f6`
  - `/private/tmp/claude-501/graphed-histogram-latest` — `211cbbe22497b64ce624d4880005af7faddf74f7`
  - `/private/tmp/claude-501/uproot5-graphed` — `393ecefee80aa4fdf563d938e4ff906f329126d8` (branch `graphed-mvp`)
  - `/private/tmp/claude-501/graphed-corpus-latest` — `49650e4a628201cfac569b1829aaa6c32655ec92`
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718, WRemnants, narf, mkShapesRDF}`
  - `/Users/lgray/vibe-coding/coffea-workdir` — `f34b8bdf2bdf05754920b49d6b8d6de078b3884f`
  - companions on disk: `systematics-vary-codebase-analysis.md`, `systematics-vary-litsearch.md`,
    `systematics-vary-worklog.md`, `systematics-vary-plan-revision-r10-notes.md`, `graphed-root-prompt.md`
- **Probes re-run in-session:** the §3.3/§5.2a reduced-shape integers (both topologies), the §7.2
  `mark_output` dedup, the §2.3e interning identity, the §6.2 `StrCategory` overflow probe, the
  §1.1 `ak.from_parquet(columns=["a.b"])` hazard, `inspect.signature(ak.to_parquet)`, the §6.4e
  `ak.to_parquet` vs `pq.write_table` byte/KV difference, the CPython `**`-unpacking claim, and one
  new probe (`Array.__getitem__` with a tuple key) that produced finding F1.

---

## Findings

### F1 — HIGH — §2.6 binding sketch: `lhe_w[:, 0]` / `lhe_w[:, i]` is not expressible on the frontend `Array`

**Section:** §2.6 sketch (plan lines 492–494), feeding the m48 anchor "§1.1 tag grammar (kwarg tags +
`variations=` numeric-tag escape …)" (§10 m48).

**Detail.** The sketch spells the PDF-member family — the plan's *only* worked demonstration of the
`variations=` escape and of numeric tags beyond `up`/`down` — as

```python
events = graphed.vary(events, "pdf", lhe_w[:, 0], is_weight=True,
                      variations={f"{i}": lhe_w[:, i] for i in range(1, 103)})
```

`Array.__getitem__` (`/private/tmp/claude-501/graphed-latest/python/graphed/array.py:344-371`)
accepts only an `Array` mask, `str`, `list[str]`, `slice`, or `int`, and raises `TypeError` on
anything else at `:369-371`. A tuple key `(slice, int)` therefore raises. The numpy idiom *does*
support tuple subscripts (`python/graphed/numpy/array.py:132-136`, `"subscript"` op), but an event
context over nanoevents is awkward-idiom, where `lhe_w` is a plain `Array`. No `gak` function
supplies an arbitrary inner index either: the public surface
(`python/graphed/awkward/functions.py`) has `firsts` (index 0 only), `local_index`, `mask`,
`pad_none`, `singletons` — nothing equivalent to `arr[:, i]`. So the sketch's expression requires
frontend work that no milestone in §10 scopes.

This is precisely the failure mode §4.1/m48 already guards against for the flat-SF constant ("The
anchor says so to spare the test-author the mid-freeze discovery") — the same guard was not applied
here.

**Evidence (measured in-session, `graphed-latest` @ ff7c607):**

```
$ uv run --extra awkward python -c "... w = ev['w']; w[:, 0] ..."
tuple getitem FAILS: TypeError unsupported index (slice(None, None, None), 0);
  use an Array mask/index, a slice, an int, or a field name
```

and `python/graphed/array.py:369-371`:

```python
raise TypeError(
    f"unsupported index {key!r}; use an Array mask/index, a slice, an int, or a field name"
)
```

**Suggested fix.** Either (a) respell the sketch with an expression that exists today — e.g. LHE
weights stored as separate per-member fields, or `gak.firsts(...)` for member 0 plus an explicit
named-field/`gak.unzip` shape for the rest — and say so; or (b) if per-member inner indexing on the
awkward idiom is genuinely wanted, name it as a scoped m48 target (a `gak`-level inner-index verb)
with the measured gap stated, the way §4.1 handles the constant-Array gap. Add the note to the m48
grammar anchor bullet so the test-author does not discover it mid-freeze.

---

### F2 — MID — §10: `uproot5-graphed-mvp` has **no** existing frozen layout to follow

**Section:** §10, frozen-layout paragraph ("`uproot5-graphed-mvp` (m51 only) follows its existing
frozen layout, pinned at m51 freeze").

**Detail.** The fork has no `tests/frozen/` tree at all, and no `frozen` convention anywhere. Its
graphed tests are flat, ordinarily-named files directly under `tests/`. The surrounding paragraph
exists specifically to pin directories before freeze (because "duplicate basenames have bitten it
before"), so the one repo left un-pinned is the one with nothing to inherit — the m51 test-author
is pointed at a convention that does not exist, and the §12.1 gate + the root `CLAUDE.md`
integrity rule ("never edit `tests/frozen/**`") have no tree to bind in that repo.

**Evidence (`uproot5-graphed` @ 393ecef):**

```
$ find /private/tmp/claude-501/uproot5-graphed -type d -name "*frozen*"        # (no output)
$ grep -rl "tests/frozen" ... --include='*.py' --include='*.toml' --include='*.md' --include='*.yml'
                                                                               # (no output)
$ find .../tests -name "*graphed*"
tests/test_graphed_write.py  tests/test_graphed_to_parquet.py  tests/test_graphed_nanoaod.py  … (14 files)
```

**Suggested fix.** Replace the clause with the measured fact and a decision, e.g.: "`uproot5-graphed-mvp`
has **no** frozen tree today (verified at `393ecef`: graphed tests are flat `tests/test_graphed_*.py`,
zero `frozen` references repo-wide). m51 therefore **creates** `tests/frozen/m51/` there, and the
integrity rules bind it from freeze; existing `tests/test_graphed_*.py` stay unfrozen."

---

### F3 — LOW — §2.3c: the m24 anti-drift literal is **39** names, not 41

**Section:** §2.3(c) ("the `m24/test_interface_parity.py:37-78` anti-drift pin is a 41-name literal").

**Detail.** The argument (a hand-written literal list lets a new gak function go silently
unclassified, so the new gate must enumerate dynamically) is correct and unaffected; only the count
is wrong. Under R0.11 a stated count is a measured claim.

**Evidence (`graphed-latest` @ ff7c607):**

```
$ awk 'NR>=39 && NR<=79' tests/frozen/awkward/m24/test_interface_parity.py | grep -c '^\s*"'
39
```

(names: `sum … unflatten`; the enclosing test spans `:37-91`, the literal tuple `:39-79`.)

**Suggested fix.** "a **39**-name literal (`:39-79`)".

---

### F4 — LOW — Part I §3 uses `D` for the per-universe chain, while §3.3/§5.2a use `D` for the shared prefix

**Section:** Part I §3, bullet 3 ("going N=1→2 variations grows the arena by precisely the varied
suffix (Δ = D+2 nodes)") vs §3.3 ("a shared prefix of **D** ops → per universe {one varied fork op,
**K** chain ops, exactly one terminating reduction}") and §5.2a ("`K + 2 = 52` nodes … D=500, K=50").

**Detail.** Both statements are individually true — the cba's notation calls the 50-op downstream
chain `D`; the plan's own §3.3 notation calls the 500-op shared prefix `D`. Read with §3.3's
definitions, Part I §3's "Δ = D+2" evaluates to 502, contradicting the measured and pinned 52. Part
I is non-binding, but the same letter carrying two meanings in one document around the single most
load-bearing pinned integer invites exactly the arithmetic error the r10 revision just fixed.

**Evidence.** cba §optimizer §2: "shared prefix P=500 ops, per-variation `shift` + 50-op downstream
chain + 1 reduction … delta = 52 = D+2 nodes". Plan §3.3 defines D as the prefix. Re-measured
in-session against `graphed-latest` (builder: source → 500 `select` ops → per universe {1 `shift`,
50 `chain`, 1 `sum` reduction}, every universe marked as an output):

```
with_reduction=True   N=1 arena=553  N=2 arena=605  → Δ = 52
                      N=16  reduced=34  stages=17
                      N=128 reduced=258 stages=129     (t: 3.2 ms → 16.9 ms, ratio 5.3)
with_reduction=False  N=1 arena=552  N=2 arena=603  → Δ = 51
                      N=16  reduced=18   N=128 reduced=130
```

— i.e. every pinned integer in §3.3/§5.2a (`stages == N+1`, `reduced == 2N+2`, `Δ = K+2 = 52`, and
the without-reduction counter-values `N+2` / `51`) reproduces **exactly**.

**Suggested fix.** In Part I §3 write "Δ = K+2 = 52 nodes (the §3.3 builder's per-universe suffix)"
or drop the letter entirely.

---

### F5 — LOW — §10 m49(ii): "the `graphed` repo contains no process pool" is false as written

**Section:** §10, m49 anchor (ii), used as the justification for splitting the reference matrix
across two repos and for adding `graphed-histogram` to `graphed-executors`' `dev` extra.

**Detail.** The consolidated `graphed` repo's own frozen suite runs a real process pool. The
*decision* is still right — `graphed` ships no `Executor` implementation, and the executor-level
end-to-end genuinely belongs in `graphed-executors` — but the stated reason is not the true one, and
a test-author or reviewer checking it will find it contradicted immediately.

**Evidence (`graphed-latest` @ ff7c607, `tests/frozen/debug/m6/test_process_boundary.py`):**

```
7:import multiprocessing as mp
16:    with ctx.Pool(processes=1) as pool:
```

**Suggested fix.** "(the `graphed` repo ships no `Executor` implementation — the executors live in
`graphed-executors`; `graphed`'s only cross-process frozen test is the M6 error-transport pool,
`tests/frozen/debug/m6/test_process_boundary.py:16`)".

---

### F6 — LOW — Anchors appendix cites a "write-seam report" that does not exist as an artifact

**Section:** Anchors appendix, rows "No write/sink NodeKey … write-seam report §3" and "Parquet KV
metadata unused today … (write-seam report §1)"; also Part I §3 and §6.4 ("Anchors, write-seam rows").

**Detail.** The plan's header binds every design claim to "a `file:line` (Anchors appendix), a cited
section of `systematics-vary-codebase-analysis.md`, of `systematics-vary-litsearch.md`, or an
explicit stated assumption." "write-seam report §N" is none of the four; no such file exists in the
working area, and the worklog records it as "recovered from agent transcript
(idle-without-delivering again)" — i.e. it lives only in a transcript, not in a committed companion.
Since this plan is committed as a durable reference, two Anchors rows terminate in an unfollowable
citation.

The **underlying facts are true** — I re-derived both independently:
- `NodeKey` has no write/sink variant: the enum is `Source | Op | Reduction | External | Stage |
  Exchange | Join` (`src/node.rs:42,46,51,56,64,72,81`).
- Parquet key-value metadata is unused: the only `metadata` uses in the write/read path are
  `ParquetFile(path).metadata.num_rows` (`python/graphed/parquet.py:77,107,118`); no
  `key_value_metadata` / `schema.with_metadata` anywhere in `graphed-latest/python` or
  `uproot5-graphed/src`.

**Suggested fix.** Replace the "write-seam report §N" citations with the reproducible commands /
`file:line` above (both rows already carry a file anchor; the grep row can state the exact grep), or
commit the write-seam report next to the cba/lit docs and cite it by filename like the others.

---

### F7 — LOW — Anchors: `src/node.rs:41-70` does not cover the `NodeKey` enum it claims completeness over

**Section:** Anchors row "No write/sink NodeKey — write is driver-side Python only | `src/node.rs:41-70`".

**Detail.** The claim is a *completeness* claim ("no write/sink variant"), so the cited range must
span the whole enum. The enum is `41-85`; line 70 falls mid-way through the `Exchange` doc-comment,
so the cited range omits the `Exchange` (`:72`) and `Join` (`:81`) variants. The claim is true; the
anchor cannot establish it.

**Evidence (`graphed-latest` @ ff7c607):** `src/node.rs:41` `pub enum NodeKey {` … `:85` `}`;
variant heads at `42, 46, 51, 56, 64, 72, 81`.

**Suggested fix.** `src/node.rs:41-85` (the full enum).

---

### F8 — LOW — §2.6 sketch `h.fill(pt=sel.Jet.pt)` is a named-axis fill; `graphed-histogram` accepts positional only

**Section:** §2.6 sketch (plan line 502), and the m48 anchor "ambient fill on a per-object quantity
— the value passed **UNFLATTENED**".

**Detail.** `graphed_histogram.boost.Histogram.fill` is `fill(self, *args: Array, weight=…,
sample=…, threads=…)` and raises on an axis-count mismatch; a keyword `pt=` is an unexpected keyword
argument. Named-axis kwarg fills exist only in the `hist.graphed` fork (per cba §histogram §3:
`basehist.py:298` → `:338` routes kwargs → positional), and that fork is **not** listed among m48's
repos (§10 m48: "repos: `graphed` + `graphed-histogram`").

**Evidence (`graphed-histogram-latest` @ 211cbbe, `src/graphed_histogram/boost.py:153-163`):**

```python
def fill(self, *args: Array, weight: Array | Sequence[Array] | None = None,
         sample: Array | None = None, threads: int | None = None) -> Histogram:
    if len(args) != len(self.axes): raise TypeError(...)
    if not all(isinstance(a, Array) for a in args): raise TypeError(...)
```

**Suggested fix.** Spell the sketch positionally (`h.fill(sel.Jet.pt)`), or state that the sketch
uses `hist.graphed.Hist` and add that repo to m48's scope line.

---

### F9 — NIT — Part I §2 quote drift on the ewkcoffea impact-partition comment

**Section:** Part I §2 ("the Weights registry **hand-partitioned by shift-impact** ('these weights
can go outside the sys loop since they do not depend on pt of mu or jets')").

**Detail.** The source reads "These weights can go outside of the **outside** sys loop since they do
not depend on pt of mu or jets" (`ewkcoffea@063e8d7 analysis/wwz/wwz4l.py:396`). The paraphrase is
inside quotation marks. Substance unaffected.

**Suggested fix.** Quote verbatim or drop the quote marks.

---

### F10 — NIT — the §6.4e parquet sha256 literals are not reproducible as stated

**Section:** Anchors row "`ak.to_parquet` vs `pq.write_table` differ in bytes AND KV metadata …
sha256[:16] `ad1725aca34f2bbb` vs `43b093e8bc616bd7`".

**Detail.** Neither the plan, the worklog, nor `systematics-vary-plan-revision-r10-notes.md:181-185`
records the probe array, so the two hash literals cannot be re-derived by a later reader; R0.11 asks
for stated methodology. The **substantive** claims all reproduce (see below), so this is cosmetic —
but the two literals carry no information a reader can check.

**Evidence (re-run in-session, `awkward==2.12.0` / `pyarrow==25.0.0`, my own one-column array):**

```
sha1 0a6a392ff5f0e409   sha2 d54095ea5b68b993   differ True
kv1 ['ak:parameters', 'awkward_array_metadata']      # ak.to_parquet
kv2 ['ak:parameters']                                # pq.write_table(ak.to_arrow_table(a))
to_parquet sig has metadata? False
```

**Suggested fix.** State the array (`ak.Array({...})`, N rows, dtype) alongside the hashes, or drop
the hashes and keep the reproducible KV-set + no-`metadata`-parameter facts.

---

## What was verified clean

Everything below was checked against the pinned roots and is **accurate as stated**. Line numbers
were opened, not inferred.

**Rust IR / optimizer anchors.** `store.rs:73-88` (intern), `store.rs:152-153` (`mark_output`
de-dups), `node.rs:39-41` (identity), `node.rs:102-103` (`is_boundary = !Op`),
`engine.rs:7-13` (the O(N) extractor rationale, verbatim "blows up … on the deep chains a
systematics graph produces"), `engine.rs:54-56` (`boundary_from_token`), `optimizer/mod.rs:1-11`
(rebuild into a fresh interned store), `mod.rs:88-116` (DCE + `remap`).

**Frontend / execution anchors.** `array.py:156, 245-275, 344-371, 374-375, 377-379`;
`session.py:30, 113-125, 152, 159`; `provenance.py:26-33, 66-79`; `execute.py:54-70, 96-126`
(incl. `:126` verbatim `[vals[o] for o in store.outputs()]`); `aggregate.py:44-65` (bare
`evaluate_ir`, no try/except, no `StageError`), `:89-93`, `:95-97`, `:101`; `plan.py:164-176,
286-301`; `shuffle.py:5-8, 92-96, 170, 232`; `projection.py:109-147`; `write.py:77-79`;
`checkpoint/store.py:31-41, 62-73`; `checkpoint/runner.py:100-109`;
`core/execution.py:276-284` (AddressTable out-of-hash precedent);
`preserve/bundle.py:103-123, 206-210`; `awkward/io.py:111-127, 113, 157-185`;
`awkward/functions.py:612-616`; `numpy/io.py:163-171`.

**§8.2's central grep claim reproduces exactly:** `grep -rn "StageError(" python/` returns
**exactly two** hits — `debug/errors.py:29` (the class) and `debug/runner.py:37` (the driver-side
M6 debug runner, whose docstring at `:6-7` reads "This is a *debug* runner, not the M7 executor").
`graphed-executors submit/engine.py:381-396` translates worker death / re-raises (`:375-379`), and
the only cross-process `StageError`s with real provenance come from worker closures that rebuild the
graph (`tests/frozen/debug/m6/analyses.py:52-56`; `graphed-executors tests/frozen/m7/analyses.py:118-127`).

**Histogram anchors.** `boost.py:39-47` (`_flat`), `:60-71` (per-input flatten), `:88-98`
(`_SumFills` sums ALL fills), `:100-122` (`_GroupReduce` + `_add_groups`, the latter genuinely
assuming a homogeneous mapping), `:102-117`, `:166-174`, `:205-206`; `_spec.py:70,74` (growth-axis
refusal); `tests/frozen/m29/test_multi_weight_fills.py:82-99` and the params-absence pattern at
`:93-99`; `tests/frozen/m23/test_group_plan.py:60-66, 68-77`.

**Corpus / frozen artefacts.** `graphed_corpus/analyses/systematics.py:25-112` (incl. `:31-36`,
`:39-45`, `:60-61`, `:74-76`, `:91-92`); `tests/frozen/corpus/m05/test_systematics.py` (both
behavioral invariants, strict `jes_up > nominal > jes_down` at `:30`);
`test_fixtures_reproduce.py` comparison form (`bin_values(h) == ref["values"]` +
`fingerprint(h) == ref["fingerprint"]`); `tests/frozen/core/m4/test_systematics.py:28-53`
(3300 variations, `< 1 s`, count-independent) and the single-output builder the plan correctly flags
as vacuity-inducing; `tests/frozen/core/m4/test_benchmark.py:10, 28-33, 40-43, 40-53` (incl.
`base = max(times[SIZES[0]], 1e-4)` and `growth < 24.0` verbatim);
`tests/frozen/core/m40/test_join_serialize.py:84-99`; `tests/frozen/preserve/m9/agc.py:38-66,
56-62, 94-118, 106-107` and `test_reproduce.py:19-23`.

**Counts and arithmetic.** The corpus ships **23** reference JSONs = 8 ADL + 10 ttbar (2 regions × 5
variations) + 5 ttgamma; the systematics subset is exactly **15** ✓. m48's "ttbar 4j1b/4j2b ×
{nominal, btag_up, btag_down} (6) + ttgamma {nominal, pho_up, pho_down} (3) = **9 of the 15**" ✓ and
all nine are weight-only variations ✓. §3.3 headroom "3.1 ms at N=16, 16.7 ms at N=128, ratio ≈5.4
against 24.0" ✓ (and 12.9× nodes → 11.9× time ✓ from the cba table: 553→7157 nodes, 1.4→16.7 ms).
§6.4c compression numbers match the worklog probe line-for-line (raw 3.551 MB / ratio 2.883 /
XOR 3.280; masks 798 KB → 169 KB = 4.72× ≈ "~4.7×"). The §1.1 e-form examples are internally
consistent with the canonical grammar `m?\d+(em\d+)?` (`5em1`=0.5, `25em1`=2.5, `12345em4`=1.2345,
`m15em1`=−1.5, `1em8`=1e-8; `20e-1`→`2` as an integer) and the e-form/p-form parsers are disjoint on
full match. §6.2's "`murf_10` sorts before `murf_2`" ✓.

**Fixture facts behind the m49 repo split.** `graphed-corpus pyproject.toml:28-30` packages only
`src/graphed_corpus` while the references live in `corpus/references/` ✓; `graphed-executors
pyproject.toml:20-35` has no `graphed-histogram` dependency and no `histogram` hit in pyproject or
workflows ✓; `graphed tests/_corpus/references` vendors all 23 JSONs and `tests/_corpus` is on
`pythonpath` (`pyproject.toml:117`) ✓; `graphed-histogram` frozen tree is flat (`m23/`, `m29/`) ✓;
`graphed-executors` frozen tree is flat and its highest milestone is `m47` ✓ ("the executors repo
froze m47 last"); the `graphed` per-subtree/per-milestone rationale is at `pyproject.toml:106-114` ✓.

**Re-runnable probes — all reproduce.**
- boost_histogram `StrCategory` overflow: `Traits(underflow=False, overflow=True, growth=False, …)`,
  `h.sum() == 2.0` vs `h.sum(flow=True) == 3.0` for `['nominal','bogus','jes_up']` into
  `StrCategory(['nominal','jes_up','jes_down'])` — reproduced (on bh 1.8.0; the plan's 1.7.2 result
  is version-independent here).
- `ak.from_parquet(columns=["murf_0.5"])` → **empty** (`fields []`, `len 0`); the list-path form
  `columns=[["murf_0.5"]]` works — reproduced (awkward 2.12.0 / pyarrow 25.0.0).
- `inspect.signature(ak.to_parquet)` has **no** `metadata` parameter — reproduced.
- `ak.to_parquet` vs `pq.write_table(ak.to_arrow_table(a))`: different bytes, KV sets
  `{awkward_array_metadata, ak:parameters}` vs `{ak:parameters}` — reproduced (see F10 on the hashes).
- CPython 3.12.10 admits non-identifier keys through `**`-unpacking (`f(**{'0.5': 1, '0p5': 2})`) —
  reproduced.
- §7.2 dedup: `compile_ir(s, b, c)` with `b`/`c` structurally identical returns **1** value;
  `compile_ir(s, b, d)` returns **2** — reproduced exactly.
- §2.3e interning: `src * 2.0` recorded twice returns node id **1** both times — reproduced exactly.
- §3.3/§5.2a reduced shapes and arena deltas, both with and without the terminating reduction —
  reproduced exactly (table in F4).

**uproot fork anchors.** `behaviors/RNTuple.py:1560-1562` (exact lookup first) and `:1564-1569`
(dot-split fallback); `:562,567` inside `to_akform` (which begins at `:505`), i.e. the r10 correction
"`to_akform` is what splits" is right; `writing/_cascadetree.py:1606` (`.` as the nesting join);
`behaviors/TBranch.py:2015-2017` (exact-first) and `:2019-2024` (splits on `/`, never `.`);
`writing/_graphed_write.py:59-64` copies branches verbatim with **zero** `compile_ir`/`evaluate_ir`
hits (grep count 0) ✓.

**Prior art — independently re-verified against the clones.**
- WRemnants and narf: `grep -rnE "\bVary\(|VariationsFor" --include='*.py'` returns **0** in both ✓;
  `narf/README.md:1-2` "narf is not an rdf framework" ✓.
- mkShapesRDF: its own `mRDF.Vary` exists because native `Vary` is "not compatible with ``Snapshot``"
  (`mRDF.py:220`) ✓; the OR-of-cuts is literal (`mRDF.py:280` `" || ".join(nom_and_variations)`) ✓;
  suffixed-column defines ✓.
- ewkcoffea 0.7-era @063e8d7: **12** weight bases (10 common `:439-443` + 2 R2-only `:447`) →
  `append_up_down_to_sys_base` → **24 labels** ✓; **3** object-shift bases (`:454-458`) → **6 labels**
  ✓; the shift loop is **7-pass** (`["nominal"] + 6`, `:462`) ✓; the nominal-only exclusion rule is
  explicit at `:1204-1207` ✓; the impact-partitioned Weights comment at `:396-397` ✓ (see F9).
- ewkcoffea dask-era @63abb06: `obj_correction_systs = []` at `:331` with "Will have e.g. jes etc" —
  the empty list is real ✓; hand-written CSE `masked_val_cache`/`masked_weights_cache` at `:808-809`,
  used `:851-865` ✓; `copy.copy(...) # TODO do we need copy here?` at `:342` ✓;
  `run_wwz4l.py:259-261` "# Does not work" over the commented `cloudpickle.dump` ✓;
  `run_wwz4l.py:302-313` timing block ✓. The `hout = {}` bug is confirmed structurally: the shift
  loop opens at `:339` (indent 8), `hout = {}` sits at `:807` (indent 12) *inside* it, and
  `return hout` is at `:892` — so a non-empty shift list would keep only the last shift ✓.
- FNALLPC/wwz4l @cc71718: `obj_correction_systs` populated at `:395-400` ✓; exclusion rule
  `:711-718` ✓; shift loop `:408` … `:759` ✓; **zero** dask/`dataset_tools`/`hist.dask` hits
  repo-wide ✓; `ApplyJetSystematics` **byte-identical** to `ewkcoffea@main`'s (I extracted both
  function bodies: 606 chars each, `==` True) ✓; the 27-label arithmetic (1 + 20 + 6) and the
  522-identical-lines / 54→14-categories figures match lit §ewkcoffea-confirmed `:545,549,555` ✓.
- coffea @f34b8bdf: `rand_gauss` seeds PCG64 from the input array's own bytes
  (`CorrectedJetsFactory.py:38,40`) ✓; `jer_smear(:65-97)` takes a **single**
  `jet_resolution_rand_gauss` (`:70`) while only `jersf = …[:, variation]` varies (`:84`) ✓;
  `deltaPtRel` is signed (`:85`) and `stochSmear` scales a signed gaussian (`:89`) — non-monotone by
  construction ✓.

**Citations into the research docs.** Every `lit §…` / `cba §…` pointer I sampled says what the plan
says it says. Notably: the #469 "~2-3× (up to ~7-8×)" figure and its word-level-UNVERIFIED caveat
are at `systematics-vary-litsearch.md:236` **exactly** as cited; the RDF vocabulary/limitations
(§rdf-vary §4-§6), the WRemnants tensor-axis model (§rdf-users §1-§3), the mkShapesRDF config model
(§rdf-users §4), and cba §optimizer §2/§5, §corpus §1/§3/§4/§5, §histogram §1/§2/§3,
§exec-checkpoint §1/§4 all support their claims. §4.1's correction is itself accurate: cba
§histogram §1's "no constant-Array constructor" grep is explicitly scoped to "session/array modules"
and does not cover `graphed/awkward/functions.py`, so `gak.full_like` was genuinely missed there.

**Root-prompt / catalog anchors.** `graphed-root-prompt.md:25` (the "tens of thousands" founding
line, verbatim), `:1262` and `:1282` (the two inline R22 mentions), `:1284` (the Out-of-scope
header), `:1286` ("treating systematic variations as a graph axis") ✓;
`ops_catalog.md:75` verbatim in **both** the corpus repo (`docs/requirements/`) and the consolidated
copy (`docs/corpus/requirements/`) ✓; and §12.3(d)'s "`test_catalog.py` lock-step preserved —
verified text-presence-only" is correct — `test_catalog.py:44-48` asserts only that "onnx" and
"phase-2" appear, never that the systematics row stays parked ✓.

---

## Verdict

**DIRTY — but only just, and nothing owner-locked is implicated.**

One HIGH (F1: a binding sketch expression that measurably raises `TypeError`, with no existing gak
equivalent and no milestone scoping the gap) and one MID (F2: a frozen layout claimed to exist in the
uproot fork, which has none) must be fixed before test-authoring; both are the kind of thing that
costs a test-author a mid-freeze discovery. The remaining six findings are LOW/NIT anchor and
wording precision.

The factual substrate is otherwise in unusually good shape for a document this size: I opened
roughly sixty `file:line` anchors across six repositories and found **no** anchor whose claimed
content was absent, and **no** measured number that failed to reproduce. Every one of the eight
re-runnable probes reproduced — including all four "re-measured this session" claims r10 introduced
(`stages == N+1` / `reduced == 2N+2` / `Δ = 52` in both topologies, the `mark_output` dedup, the
interning identity, and the `StrCategory` silent-overflow hazard) — and the prior-art claims hold up
against the clones, including the two I expected to be soft (the `hout = {}` latent bug and the
byte-identical `ApplyJetSystematics`). The r10 corrections the revision history advertises are all
real corrections, not restatements.
