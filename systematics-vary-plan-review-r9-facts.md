# Review — `systematics-vary-plan.md` r9, lens: FACTS / HALLUCINATION AUDIT (round 1)

- **Plan revision reviewed:** r9 (2026-07-30), `/Users/lgray/vibe-coding/graphed-workdir/systematics-vary-plan.md` (1052 lines, read in full).
- **Lens:** facts. Every `file:line` anchor in the body and the Anchors appendix opened at the cited
  lines; measured claims re-run where cheap and cross-checked against the worklog methodology where
  expensive; research-doc citations opened; prior-art claims checked against the clones; arithmetic
  and counts recomputed.
- **Date:** 2026-07-30.
- **Verification roots used (all read-only, at the revisions the plan cites):**
  - `/private/tmp/claude-501/graphed-latest` (`ff7c607`)
  - `/private/tmp/claude-501/graphed-exec-check` (`201ea42`)
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`)
  - `/private/tmp/claude-501/uproot5-graphed` (branch `graphed-mvp`, `393ecef`)
  - `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`)
  - `/private/tmp/claude-501/prior-art/{ewkcoffea@063e8d7, ewkcoffea-coffea2023@63abb06, wwz4l@cc71718, WRemnants@c5be6c6, narf@7d73361, mkShapesRDF@b89a71f, PocketCoffea@b29e33b, topeft@bbb23ca, boostedhiggs@a33dca8}`
  - `/Users/lgray/vibe-coding/coffea-workdir` (`f34b8bdf`)
  - `graphed-root-prompt.md`, `CLAUDE.md`, the two research docs and the worklog in the meta repo.
- **Probes re-run in-session** (`uv run --no-project`): the r6 compression probe (numpy/zlib), the r7
  awkward/pyarrow dotted-column probe, the r7 CPython `**`-unpacking probe, and a new uproot 5.7.5
  RNTuple dotted-field read probe (finding F3).

Owner-locked decisions (naming, functional surface, e-form canonical encoding, event-context
attachment, record-time expansion, m48–m51 scope incl. §6.4, the Phase-2 pull-in) were **not**
relitigated; findings below concern only whether stated facts are true as stated.

---

## Findings (ordered by severity)

### F1 — HIGH — §8.2: the bound label-transport mechanism cites a channel that does not exist, and would key on the wrong node ids

**Claim (binding, §8.2):** "the frontend's **node-id → label map travels the same process-closure
channel that already delivers per-node provenance to worker-side StageError construction**
(`debug/runner.py:20-45`; closures ship via the plan's OpSpec payload, `aggregate.py:54,96-104`) —
no `Plan`/`ExecResult` schema change; the worker sets `StageError.variation` from the failing node
id at construction."

**Evidence I gathered myself:**

1. `debug/runner.py` is a **driver-side** debug runner over a live `Session`:
   `run(session, array, *, opt_level, partition)` at `python/graphed/debug/runner.py:57-60` calls
   `lower(session, array, …)`; `_stage_error(lowered, node_id, …)` (`:34-45`) needs that
   `LoweredGraph`. Its own module docstring says so: *"This is a debug runner, not the M7 executor"*
   (`:6-7`).
2. Per-node provenance is a **driver-side dict**: `Session._provenance: dict[int, Provenance]`
   (`python/graphed/session.py:30`, populated at `:138,166,181,202,240`), exposed only via
   `Session.sourcemap()` (`:113-125`), whose consumers are `preserve/manifest.py` / `preserve/bundle.py`
   (grep over `python/graphed`: no executor/worker consumer).
3. The cited worker closure carries none of it: `_PartitionReduce`
   (`python/graphed/aggregate.py:44-65`) has fields `ir, source_name, backend_factory, reader,
   columns, externals, reduce`, and `__call__` (`:57-65`) calls `evaluate_ir` — no provenance, no
   node-id map, and **no StageError construction at all**.
4. Every existing cross-process `StageError` carrying real per-node provenance is produced by
   **rebuilding the graph inside the worker**, not by shipping a map:
   `tests/frozen/debug/m6/analyses.py:52-56` (`run_numpy_oob_and_raise` → `gd.run(s, bad, opt_level=1)`,
   docstring: *"build + run in THIS process"*) and `graphed-exec-check tests/frozen/m7/analyses.py:118-127`.
   The executors' own failure translation is driver-side and synthesizes
   `SourceFrame(filename=…, lineno=0)` (`graphed-exec-check src/graphed_executors/submit/engine.py:381-396`).
5. **Id-space mismatch.** Even if a map were shipped, record-time node ids are not the ids the worker
   sees: DCE compacts and remaps (`src/optimizer/mod.rs:88-116`, the `remap` vector), and the
   pipeline "rebuild[s] stages into a fresh interned GraphStore" (`src/optimizer/mod.rs:1-11`). The
   worker evaluates `compiled.ir` (`aggregate.py:95-97`), i.e. post-reduction ids.

**Why it matters:** §8.2 is written as "wire up an existing channel"; an implementer following it
literally finds no channel and, if they invent one from the session's node ids, ships a map that
does not key the IR the worker evaluates. The m49 frozen anchor (`variation == "jes_up"` across a
process boundary) is still achievable, so this is HIGH, not BLOCKER.

**Suggested fix:** restate §8.2 as NEW work and name the concrete carrier, e.g. *"a
`variation_labels: tuple[tuple[int, str], ...]` field is added to the worker process closure
(`_PartitionReduce`, `aggregate.py:44-55`) — an additive dataclass field, so `Plan`/`ExecResult`
schemas are untouched — keyed on **post-reduction** node ids taken from the same `compile_ir` call
that produced the shipped `ir` (`aggregate.py:95-97`; ids are remapped by DCE, `src/optimizer/mod.rs:88-116`).
Worker-side `StageError` construction is added at the `evaluate_ir` call site (there is none today —
`debug/runner.py` runs driver-side over a live Session)."*

---

### F2 — LOW — §1.1: "correctionlib scale-variation sets natively key on such strings" is unsupported, and the §4.1 cross-reference does not support it

§1.1 justifies float-spelled tags with "(μR/μF scale factors, σ-scans; **correctionlib
scale-variation sets natively key on such strings, §4.1**)". `grep -i correctionlib` over
`systematics-vary-litsearch.md`, `systematics-vary-codebase-analysis.md` and
`systematics-vary-worklog.md` returns no such claim; §4.1 documents only the `systematic` **category
parameter**, whose measured keys in the cited fixture are `"nominal"`/`"up"`/`"down"`
(`tests/frozen/preserve/m9/agc.py:30-34,56-62`). The claim is presented as fact with a dead-end
citation (R0.11).

**Suggested fix:** either cite a concrete correctionlib set that keys on float-spelled strings (URL
+ key list), or weaken to the supportable form: *"correctionlib category inputs are arbitrary strings
(`agc.py:56-62`), so a float-spelled key is expressible."* Nothing binding changes.

---

### F3 — LOW — §1.1/§6.4b: the uproot RNTuple hazard is mis-attributed to `__getitem__`, and the anchor range points at a re-raise rather than the split

**Claim:** "uproot RNTuple `__getitem__` splits on `.`" (§1.1) / "uproot 5.7.5 RNTuple `__getitem__`
dot-split, `behaviors/RNTuple.py:1573-1576`" (§6.4b, Anchors).

**Measured in-session** (`uv run --no-project --with uproot==5.7.5 --with awkward --with pyarrow`;
uproot 5.7.5 / awkward 2.12.0 / pyarrow 25.0.0), writing an RNTuple with a field literally named
`murf_0.5`:

```
keys: ['murf_0.5', 'plain']
nt["murf_0.5"]                -> RField murf_0.5          (SUCCEEDS)
nt["murf_0.5"].array()        -> KeyInFileError: 'murf_0'  (raised inside to_akform)
nt.arrays(["murf_0.5"])       -> [{'murf_0.5': 0}, ...]    (SUCCEEDS)
```

Traceback of the failing call: `models/RNTuple.py:1989 array` → `behaviors/RNTuple.py:761 arrays` →
`behaviors/RNTuple.py:567 to_akform` (`tmp_field = tmp_field[key]`) → `behaviors/RNTuple.py:1593`.
Reading the fork source confirms the code shape: `__getitem__` does an **exact lookup first**
(`/private/tmp/claude-501/uproot5-graphed/src/uproot/behaviors/RNTuple.py:1558-1562`,
`got = self._lookup.get(where); if got is not None: return got`) and only falls back to
`where.split(".")` at `:1564-1569`; the cited `:1573-1576` is the `keys=`/`file_path=`/`object_path=`
argument block of the fallback's re-raise.

So the hazard is real (a dotted RNTuple field cannot be read through `RField.array()`), but it is
neither "`__getitem__` splits on `.`" nor "unreadable by name" in general (`arrays([...])` works).
The owner-locked identifier-only decision is unaffected — this is about the stated fact.

**Suggested fix:** replace the mechanism sentence with the measured one and re-anchor:
*"uproot 5.7.5: a dotted RNTuple field is reachable via `__getitem__` (exact lookup first,
`behaviors/RNTuple.py:1558-1562`) but `RField.array()` fails — `to_akform` splits the name on `.`
(`behaviors/RNTuple.py:567`, falling into the `:1564-1569` split path → `KeyInFileError: 'murf_0'`);
`ntuple.arrays(["murf_0.5"])` still works."*

---

### F4 — LOW — Anchors appendix: "TTree lookup exact-first | `behaviors/TBranch.py:2098`" is a stale line

`/private/tmp/claude-501/uproot5-graphed/src/uproot/behaviors/TBranch.py:2098` is `def array(`. The
exact-first lookup the row means is `HasBranches.__getitem__` at `:1999-2052`, specifically
`got = self._lookup.get(where); if got is not None: return got` at **`:2015-2017`**; note also that
this getitem splits on `/` (`:2019-2024`), never on `.`, which is why the TTree hazard in §1.1 is
correctly attributed to the *writer* (`writing/_cascadetree.py:1606`, verified:
`out[field_name + "." + subfield_name] = subfield`) and not to the reader.

**Suggested fix:** `behaviors/TBranch.py:2015-2017` (and, if the `/`-only split is worth stating,
`:2019-2024`).

---

### F5 — LOW — §2.3b mis-describes current `Array.__getitem__` / `Array.filter` behaviour

**Claim:** "`Array.__getitem__` and `Array.filter` currently reject non-Array keys (`array.py:344-375`)".

**Measured:** `python/graphed/array.py:344-371` accepts an `Array` mask (`:345-346`), a `str` field
(`:347-348`), a `list[str]` field subset (`:351-354`), a `slice` (`:358-366`) and an `int`
(`:367-368`), raising `TypeError` only for anything else (`:369-371`). `filter` (`:374-375`) performs
**no** check — a non-`Array` argument reaches `Session.record_op`, which raises `AttributeError` on
`a.node_id` (`python/graphed/session.py:152,159`). The plan itself relies on the `str` branch
elsewhere (§2.2: "String subscription `v["pt"]` is field access"), so the two statements read
inconsistently.

**Suggested fix:** *"`Array.__getitem__` accepts only Array/str/list/slice/int keys and raises
`TypeError` on anything else (`array.py:344-371`); `Array.filter` has no runtime check and a `Varied`
would surface as an `AttributeError` inside `record_op` (`session.py:152`). Both gain an explicit
`Varied` branch."*

---

### F6 — LOW — Part I §2 presents coffea Discussion #469's "2-8×" as measured; the cited source flags it as unverified

The plan: "coffea Discussion #469 **measured** 2-8× wins for vectorized (extra-axis) systematics over
re-run loops." The cited source, `systematics-vary-litsearch.md:236`, records the number **with an
explicit caveat**: *"(Content read via summarizing fetch; exact attributions/quotes UNVERIFIED at word
level — the URL is the evidence.)"* Under R0.11 the caveat should travel with the number. Impact is
low: Part I binds nothing, and no PART II requirement rests on it (§6.2's axis mode is grounded in the
`cba §histogram §3` bh 1.7.2 probes and the exemplar layout, both of which I verified).

**Suggested fix:** "…Discussion #469 reports ~2-3× (up to ~7-8× for many systematics) for vectorized
extra-axis systematics — read via summarizing fetch, word-level unverified (lit §coffea-sys)."

---

### F7 — LOW — §6.1d overloads the word "provenance" against the plan's own anchored meaning

§6.1d: "`fill` **walks its input Arrays' provenance** to their event context". In this codebase
`provenance` is source-location capture only — `Provenance(filename, lineno, function, source)`,
`capture()` at `python/graphed/provenance.py:66-79`, which the plan itself anchors with that meaning
in §2.3 and in the Anchors row "Provenance skips graphed frames". The mechanism §6.1d needs is the
r6 **object lineage** of §2.6b, which is a different thing. An implementer could reasonably go looking
at `Session._provenance` / `sourcemap()`.

**Suggested fix:** "`fill` follows its input Arrays' **context lineage** (§2.6b) to their event
context" — and, if useful, name where the link is stored.

---

### F8 — NIT — Anchors row `tests/frozen/corpus/m05/test_systematics.py:26-38` is off by one at both ends

The two named behavioural tests are `test_kinematic_variation_changes_selection` at **`:25-30`** and
`test_weight_variation_preserves_selection` at **`:33-37`** (`:38` is blank). The claim is otherwise
exactly right — including the strict `assert jes_up > nominal > jes_dn` at `:30` that §5.1 scopes to
the JES fixture. Suggested fix: `:25-37`.

---

### F9 — NIT — §12.3(d) un-parks one `ops_catalog.md`; there are two synchronized copies

`ops_catalog.md:75` exists identically in **both** `graphed-corpus-latest/docs/requirements/ops_catalog.md:75`
and `graphed-latest/docs/corpus/requirements/ops_catalog.md:75` (verified byte-equal line). The frozen
`tests/frozen/corpus/m05/test_catalog.py:12-13` reads the **consolidated** copy. Editing only one
leaves them drifted. (The lock-step-preserved claim itself checks out: `test_catalog.py` is
text-presence-only — `:22-52` assert substrings `adl_q*`/`ttbar_`/`ttgamma_`/`M3,M4,M7,M9`/`"weight
systematic"`/`"kinematic systematic"`/`"onnx"`/`"phase-2"`; moving the row into Section C keeps every
assertion green.)

---

### F10 — NIT — the header's source mirror is a session-scratchpad path, not a durable one

The header cites the source directive as "mirrored at `scratchpad/systematics-plan.txt`" in a document
that is explicitly "Committed in the meta repo … as a durable reference". The file exists only at
`/private/tmp/claude-501/-Users-lgray-vibe-coding-graphed-workdir/8f54f531-a6e8-4340-a81d-efa35f73b6f6/scratchpad/systematics-plan.txt`
(session-scoped, ephemeral). Its content does corroborate the quoted open question — verbatim:
*"it is worth considering if it is useful to add to the optimization impact analysis to isolate
subgraphs that a systematic variation needs to re-run"* (line 12), which Part I §3 paraphrases inside
quote marks. Suggested fix: commit the mirror beside the plan, or cite only the Google Doc id.

---

## Verified clean (what I checked and found true)

Reported so the record shows the audit's coverage, not just its complaints.

**Rust IR / optimizer.** `src/store.rs:73-88` (intern, exact-key reuse) ✓; `src/node.rs:39-41`
(NodeKey identity), `:41-70` (no write/sink kind — Source/Op/Reduction/External/Stage/Exchange/Join),
`:102-103` (`is_boundary = !Op`) ✓; `src/optimizer/engine.rs:7-13` (the O(N)-extractor note, verbatim
"blows up … on the deep chains a systematics graph produces"), `:54-56` (`boundary_from_token`) ✓.

**Frozen anchors.** `tests/frozen/core/m4/test_systematics.py:28-53` — the 3300-variation/~10⁴-node
`< 1 s` test and the variation-count-independence test, both exactly in that range ✓; the §3.3 claim
that `_systematics` funnels all variations into ONE output (`:20-25`, `acc = add(acc, w)`) — so the
"separately marked output" respin is genuinely needed ✓. `test_benchmark.py:10` (`SIZES`) and
`:40-53` (`assert growth < 24.0`, per-size budget) ✓. `core/m40/test_join_serialize.py:84-99`
(golden GIR bytes) ✓; `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:82-99` and the
params-absence pattern `:93-99` ✓; `m23/test_group_plan.py:68-77` (`len(src.part_reads) == 4`) ✓;
`preserve/m9/test_reproduce.py:19-23` (`np.array_equal` comparison form) ✓;
`corpus/m05/test_fixtures_reproduce.py:34-35` — exactly the `bin_values`/`fingerprint` pair m48 cites ✓.

**Frontend anchors.** `array.py:156` (`__array_ufunc__`), `:245-275` (`__and__`…`__invert__`),
`:377-379` (`map` = record_external, hence the `.apply` rename) ✓; `execute.py:54-70` (variadic
`compile_ir`, "EXACTLY the requested outputs (M22)" verbatim at `:64`), `:99-126` (positional outputs,
unknown-kind raise) ✓; `core/plan.py:164-176` and `:286-301` (both `task_id`s fold `self.ir`) ✓;
`shuffle.py:5-8,92-96` (neutral-verb factorization), `:170` (`exchanges[0]`), `:232` (first `join`
node — the r1 `:233`→`:232` correction is right) ✓; `aggregate.py:54,89-93,96-104,101` ✓;
`projection.py:109-147` (`read_columns(arrays: Sequence[Array], …)`, union by construction) ✓;
`provenance.py:66-79` (skips `graphed*` frames) ✓; `debug/errors.py:29-81` (keyword-only ctor at
`:32-42`, `summary()` `:57-62`, `__reduce__` over `__dict__` `:67-68`, `__eq__`/`__hash__` `:75-81` —
so §8.1's "rides `__reduce__` for free" and "`__eq__`/`__hash__` participation" are both right, and
`__hash__` does need the one-line edit the plan implies) ✓; `checkpoint/runner.py:100-109`
(partition-atomic dead-letter), `checkpoint/store.py:31-41` (defaulted-field precedent), `:62-73`
(content-deduped blobs) ✓; `core/execution.py:276-284` (AddressTable "ephemeral state must not be
folded into content-addressed ids") ✓.

**Write seam (§6.4).** `awkward/io.py:111-127` (`_WritePart.__call__`: single-output
`(out,) = evaluate_ir`, record-vs-column at `:123`, `ak.to_parquet` at `:126`, no metadata),
`:113`, `:157-185` (`_evaluation_columns`) ✓; `numpy/io.py:163-171` (1-D single-column hard cap) ✓;
`write.py:77-79` (`part_path` prefix/suffix) ✓; `uproot5-graphed src/uproot/writing/_graphed_write.py:59-64`
(verbatim branch copy; `grep -c "compile_ir\|evaluate_ir"` → **0**) ✓; parquet KV metadata unused —
`grep -rn "key_value_metadata\|custom_metadata\|schema.with_metadata"` over `graphed-latest/python` +
`uproot5-graphed/src` → **0 hits** ✓; `writing/_cascadetree.py:1606` (`.` as nesting separator) ✓.

**Histogram layer.** `boost.py:88-98` (`_SumFills` sums ALL fills — the §6.1c refusal is justified),
`:100-122` (`_GroupReduce` `{label: hist}` with `layout=(label, n_fills, spec)`), `:100-117` (the
countable m50 seam), `:166-174` (M29 weight factor list), `:205-206` (`n_weights` only when >1) ✓;
`_spec.py:70,74` (growth axes raise) ✓; the "no constant-Array constructor" claim (cba §histogram §1)
re-checked — `FillEvaluator._flat` (`boost.py:39-47,60-71`) flattens each input independently, and
`boost.py:162-163` requires Arrays, so §4.1/m48's warning about the flat ttgamma SF is correct and
the §6.1d event→object broadcast is genuinely new work ✓.

**Corpus.** `systematics.py:25-112` fixture; `:31-36` (`_btag_weight`), `:39-45` (`_apply_jes` via
`ak.with_field` — the lockstep record precedent), `:60-61` (JES before the pt cut), `:74-76` (central
b-tag on shifted jets), `:91-92` (unvaried photons/muons sliced by a JES-varied selection — §2.3b's
motivating case), `:99` (`np.full` flat SF) ✓; **15** systematics references on disk (10 ttbar + 5
ttgamma; 23 total with 8 ADL) ✓; **9 of 15** for the m48 weight matrix (2 regions × 3 + 3) ✓;
`ops_catalog.md:75` ✓; `docs/graph_bloat_note.md` O(10⁴)-node claim ✓.

**Root prompt / CLAUDE.md.** `:25` ("On real analyses with many systematic variations the graph
reaches tens of thousands…"), `:1284` (Out-of-scope header), `:1286` ("treating systematic variations
as a graph axis"), `:1262` (R22.0) and `:1282` (R22.10) both containing "systematics-as-a-graph-axis
… stay Phase 2", plus `CLAUDE.md:240` Part F — the "four places" count is exact ✓.

**Measured claims re-verified.**
- Compression probe (§6.4c) re-run independently (float32, 1e6, zlib-6, seed 42): raw 3.506 MB /
  ratio 2.888 MB **exact: False** / subtract-delta 3.177 MB exact: True (data-dependent) / XOR
  3.273 MB exact: True; masks ×5 raw 795 KB, packbits 625 KB, XOR-diff+packbits 169 KB = **4.7×**.
  Matches the plan's 3.55 / 2.88 / 3.28 / 169 vs 798 / ~4.7× within construction noise, and the
  worklog's stated methodology is reproducible as written ✓.
- `ak.from_parquet(columns=["murf_0.5"])` → `fields == []` (silently empty); list-path
  `columns=[["murf_0.5"]]` → works — awkward 2.12.0 / pyarrow 25.0.0 ✓.
- CPython 3.12.10 `f(**{"0.5": 1, "0p5": 2})` accepted → channel-independent validation is required ✓.
- cba §optimizer §2 expansion table: Δ = D+2 = 52 for a 50-op chain (so §5.2a's "adds exactly 52
  nodes" is right), 128 variations 7157 nodes / 16.7 ms vs 553 / 1.4 ms = **12.9× nodes → 11.9× time**,
  `stages = N+1`, `reduced = 2N+2` — all three §3.3 pins check out arithmetically for N ∈ {16,32,64,128}
  (N=1 is the only degenerate row, and it is outside the pinned set) ✓.
- e-form arithmetic: `0.5→5em1`, `2.5→25em1`, `1.2345→12345em4`, `-1.5→m15em1`, `1e-8→1em8`, and
  `"2"≡"2.0"≡"2e0"≡"20e-1"→2` all correct; "a fractional value's exponent is negative by construction"
  holds; `murf_10 < murf_2` lexicographically ✓.

**Research-doc citations.** lit §rdf-vary: "largest pain point in analysis software"
(arXiv:2212.04889) at lit`:67` ✓; `Experimental` 4+ years at `:83` ✓; copy-on-write `RColumnRegister`
`:39,:57`, `RDefine::MakeVariations` skip-when-unaffected `:59`, `RFilter::GetVariedFilter` `:60`,
Snapshot's `fIncludeVariations` per-event validity **bitmask** `:49,:70,:82`, `"nominal"` reserved +
`RVariationsDescription`/`GetVariations()` `:75` ✓. mkShapesRDF: the OR-of-cuts re-implementation
verified in the clone — `mkShapesRDF/processor/framework/mRDF.py:249-283`, *"Only events that pass at
least one of the varied `CUT` (or the nominal)"* + `" || ".join(nom_and_variations)` ✓; prune `:149`,
rename-to-dodge-clashes `:142` ✓. WRemnants/narf "zero uses of `Vary`" — re-grepped both clones,
`Vary(`/`VariationsFor` over `*.py|*.cpp|*.h` → **0** ✓.

**Prior art (clones).** `ewkcoffea@063e8d7`: 10 common weight bases + 2 R2-only = **12 bases → 24
labels** (`analysis/wwz/wwz4l.py:439-449`), **6** object-shift labels (`:454-459`), **7-pass** loop
(`:462-467`), nominal-only exclusion at `:1204-1207` verbatim, impact-partitioned Weights comment at
`:396` verbatim ✓. `@63abb06`: `masked_val_cache`/`masked_weights_cache` at `:808-809` used at
`:851-865`, `copy.copy(...) # TODO do we need copy here?` at `:342`, `obj_correction_systs = []` at
`:331`, `hout = {}` at `:807` inside the shift loop (`:339`) with `return hout` at `:892` — the latent
last-shift-wins bug is real; `run_wwz4l.py:259-261` `# Does not work` above the commented
`cloudpickle.dump`, `:302-313` timing ✓. `FNALLPC/wwz4l@cc71718`: 764-line processor,
`:395-400` shift bases, `:711-718` exclusion rule, **0** dask/`dataset_tools`/`hist.dask` hits
repo-wide; the "**27 labels**" figure is the Run-3 count (`1 + 20 + 6`), consistent with the litsearch's
"31 (R2) / 27 (R3)" and with the fork shipping Run-3 skims only — correct as stated ✓; "522 identical
processor lines" and byte-identical `ApplyJetSystematics` traced to lit`:545,:549` ✓.
`coffea@f34b8bdf`: `rand_gauss` content-seeded PCG64 at `jetmet_tools/CorrectedJetsFactory.py:36-47`
✓; `jer_smear` takes ONE `jet_resolution_rand_gauss` (`:70`) while only `jersf = …[:, variation]`
(`:84`) varies, with signed `deltaPtRel` (`:85`) and `detSmear`/`stochSmear` (`:88-89`) — the
non-monotone-by-construction claim is exactly right ✓.

**Milestone bookkeeping.** Frozen layouts as stated: `graphed-histogram tests/frozen/{m23,m29}` (flat),
`graphed-exec-check tests/frozen/{m7,m10,m31,…,m47}` (flat, m47 highest — "the executors repo froze
m47 last" ✓), `graphed-latest tests/frozen/<pkg>/mXX` ✓. `gak.join/zip/concatenate/unzip/
broadcast_arrays/fields/type_of` all exist (`python/graphed/awkward/functions.py:18,118,383,677,687,717,722`)
so §2.3c's classification names real functions ✓. `Array.__getattr__` = field access
(`array.py:332-335`) — the §2.6a "any reserved attribute is a latent collision" rationale is grounded ✓.

---

## Verdict

**Dirty — but only lightly, and at one load-bearing spot.**

One HIGH (F1: §8.2's "already delivers" channel does not exist and the id space is wrong), six LOW,
three NIT. No BLOCKER. The plan's factual substrate is, with those exceptions, unusually solid: of the
~60 distinct `file:line` anchors I opened, **two** were wrong (F3, F4, both in the uproot rows) and one
was off by a line at each end (F8); every arithmetic claim I recomputed (15 refs, 9-of-15, Δ = D+2 = 52,
2N+2 / N+1, 12.9×/11.9×, 12→24 / 6 / 7-pass / 27, 4.7×, the e-form conversions) checked out; every
measured probe I re-ran reproduced; and every prior-art claim I sampled was verifiable in the pinned
clones. F1 should be fixed before m49 test authoring (it is the anchor a test-author would build the
cross-process label test around); F2–F7 are one-sentence edits; F8–F10 are hygiene.
