# systematics-vary-plan r9 → r10 — revision audit trail (review round 1)

Isolated reviser, 2026-07-30. Three independent r9 reviews (facts / design / tests) produced 32
findings; after cross-lens merge, **28 distinct**. Every one was re-verified in this session against
the pinned verification roots before acting (R0.11 binds the reviser too).

Verification roots used: `/private/tmp/claude-501/graphed-latest` (ff7c607),
`/private/tmp/claude-501/graphed-exec-check`, `/private/tmp/claude-501/graphed-histogram-latest`,
`/private/tmp/claude-501/uproot5-graphed`, `/private/tmp/claude-501/graphed-corpus-latest`, plus the
companion research docs in the working area.

**Outcome: 28 applied, 0 rejected, 0 deferred.** No finding's only resolution would have reversed an
owner-locked decision, so no "OPEN ITEMS (owner)" block was added.

Runnable probes were executed with `uv run --extra numpy` inside `graphed-latest` and with
`uv run --no-project --with …` for the uproot/awkward/pyarrow/boost-histogram probes.

---

## Merged findings

| Merged | Lenses |
|---|---|
| §8.2 label transport does not exist | FACTS HIGH + TESTS HIGH (identical mechanism claim) |
| §3.3 / §5.2a pinned integers wrong for the stated topology | DESIGN MID + TESTS MID |
| §6.4b stale r8 canonicalization citation | DESIGN LOW + TESTS LOW |
| §6.1d "provenance" word overload | FACTS LOW, subsumed by DESIGN BLOCKER's fix |

---

## BLOCKER

### D1 — §6.1d context inference names a mechanism that cannot carry a context — **APPLIED**

**Verified.** `Provenance` is a frozen `(filename, lineno, function, source)` dataclass and
`capture()` walks stack frames — `graphed-latest/python/graphed/provenance.py:26-33,66-79`; there is
no lineage channel. `Session._provenance` is a driver-side dict (`session.py:30`) surfaced only by
`sourcemap()` (`:113-125`). Interning makes a node-id-keyed map unusable for sibling contexts:
probe (`uv run --extra numpy`, `graphed-latest`) — `src * 2.0` recorded twice returns node id `1`
both times (`b.node_id == c.node_id → True`), i.e. two structurally identical recordings are the
same node. Context propagation appeared in no PART II dispatch point, had no exhaustiveness gate,
and was in no milestone's targets, while m48 froze five anchors on the resulting behaviour.

**Edit.** §2.3 header `four` → `five bound dispatch points`; new **§2.3(e)** binds context-tag
propagation: a Python-object attribute on the frontend wrapper, explicitly NOT part of node identity
(so §1.2 and interning stay intact), with the measured justification inline; propagation at every
frontend op / gak function / module verb; merge rule **at the op** (most-derived on one chain, error
on divergence); drop rule (context-free result is legal; silently losing a held handle is a bug);
gated by the SAME dynamic exhaustiveness test as the gak classification. §6.1d rewritten to read the
**context handle** and to name explicitly what it is *not* (`Provenance`, `sourcemap()`).

---

## HIGH

### D2 — content dedup breaks the positional `(output, label) → position` map — **APPLIED**

**Verified.** `mark_output` de-duplicates (`graphed-latest/src/store.rs:152-153`); `evaluate_ir`
returns `[vals[o] for o in store.outputs()]` (`python/graphed/execute.py:126`); `_GroupReduce`'s
layout is positional (`graphed-histogram-latest/src/graphed_histogram/boost.py:102-117`).
Probe: `compile_ir(s, b, c)` with `b`/`c` structurally identical → **1** value returned;
`compile_ir(s, b, d)` with distinct expressions → **2**.

**Edit.** §7.2 re-bound to `(output, label) → node id`, with `node id → position` derived from the
compiled output list and many labels allowed to resolve to one position (unpacker replicates); the
measurement is quoted inline. A frozen m48 dedup anchor added (see T2).

### D3 — §6.2's non-growth pre-declared axis silently swallows undeclared labels — **APPLIED**

**Verified.** Measured, boost_histogram 1.7.2:
`bh.Histogram(bh.axis.StrCategory(['nominal','jes_up','jes_down']), bh.axis.Regular(4,0,4))` filled
with `['nominal','bogus','jes_up']` gives `h.sum() == 2.0`, `h.sum(flow=True) == 3.0`; axis traits
`Traits(underflow=False, overflow=True, circular=False, growth=False, …)`. The label vanishes
silently — the §2.5 failure mode. §6.1d also made the label set inferred, so nobody declared bins.

**Edit.** §6.2 gains a bound declaration contract: (i) the FRONTEND declares the axis from the
inferred label set at plan time (identical spec per partition ⇒ combine-safe); (ii) if a
user-declared axis is supported, an exact-set check at fill (undeclared label = hard error naming
it, unreached declared bin = diagnostic); (iii) the frontend imposes the sort, so a user-supplied
order is normalized — resolving the "sorted" vs "pre-declared" ambiguity.

### D4 — §6.1d ambient broadcast contradicted by the plan's own sketch — **APPLIED**

**Verified.** `FillEvaluator` flattens each input independently — `_flat` at
`graphed-histogram-latest/src/graphed_histogram/boost.py:39-47`, applied per axis and per weight at
`:60-71`. The r9 sketch fill was `h.fill(pt=gak.flatten(sel.Jet.pt))`, so no jagged structure
reaches the fill to broadcast an event weight against.

**Edit.** Option (a) taken (smaller diff, uses the existing evaluator): §6.1d binds that a
per-object fill passes its value **unflattened**, the frontend records
`gak.broadcast_arrays(ambient, value)`, and the evaluator's existing per-input flatten does the
rest; a pre-flattened per-object value alongside a per-event ambient weight is REFUSED rather than
length-mismatched. The §2.6 sketch line changed to `h.fill(pt=sel.Jet.pt)` with an explanatory
comment. m48 anchor extended with the refusal.

### D5 — §6.4b stored fields need an expression-retargeting mechanism bound nowhere — **APPLIED**

**Verified.** `_WritePart.__call__` evaluates one compiled output and writes it — no selection
introspection or decomposition exists (`graphed-latest/python/graphed/awkward/io.py:111-127`). §3.1
forbids new IR machinery and nodes are immutable, so substituting the OR mask inside an
already-interned expression is not available.

**Edit.** §6.4a re-bound to the explicit user-facing form
`graphed.to_parquet(record, select=varied_mask)` (spelling at m51 freeze): the writer owns the mask,
builds both the OR and the per-label masks, and `record` is pre-selection by construction. A varied
write whose record already embeds a `Varied` selection is refused with an error pointing at
`select=`. The undecidability of the implicit form is stated as the reason.

### D6 — §2.6c derived contexts under-specified (re-indexing; Varied-mask derivation) — **APPLIED**

**Verified** by reading the plan: the sketch does `sel = events[gak.num(jets) >= 4]` with a
JES-varied `jets`, so `sel` is a label-plural context, and the very next line registers a
selection-scoped weight on it; §2.6c said only "inherit the ambient registry".

**Edit.** §2.6c now binds (a) inheritance **with every ambient member re-indexed by the derivation
mask, label-aligned per §2.4**, with the length-mismatch consequence stated; (b) a paragraph making
**varied contexts (per-label row sets)** first-class — collections `Varied`, `graphed.labels`
reports the mask's labels, per-label re-indexing, stacking per §2.1, fills label-aligned per §2.4,
and §6.4a's OR being exactly the union of these row sets. m48 anchors added for both.

### F1 + T1 — §8.2's bound label-transport channel does not exist — **APPLIED**

**Verified, all five sub-claims.**
- `_PartitionReduce` (`graphed-latest/python/graphed/aggregate.py:44-65`) has fields
  `ir/source_name/backend_factory/reader/columns/externals/reduce`; `__call__` reads the partition,
  calls `evaluate_ir`, reduces. No provenance, no node map, no try/except, no `StageError`.
- `grep -rn "StageError(" python/graphed/` → exactly **2** hits: `debug/errors.py:29` (the class)
  and `debug/runner.py:37` (the sole constructor call).
- `debug/runner.py` is driver-side: `run(session, array, …)` builds `lower(session, array)` and uses
  `session.source_value(nid)` (`:57-69`); its docstring says "This is a *debug* runner, not the M7
  executor" (`:6-7`).
- Executors only translate/propagate: `graphed-exec-check/src/graphed_executors/submit/engine.py:381-396`.
- Id space is wrong: DCE compacts and remaps (`graphed-latest/src/optimizer/mod.rs:88-116`, the
  `remap` vector) and the pipeline rebuilds "into a fresh interned GraphStore" (`mod.rs:1-11`),
  while the worker evaluates `compiled.ir` (`aggregate.py:95-97`).
- Existing cross-process StageErrors come from rebuild-in-worker closures
  (`graphed-latest/tests/frozen/debug/m6/analyses.py:52-56`;
  `graphed-exec-check/tests/frozen/m7/analyses.py:118-127`).

**Edit.** §8.2's r9 mechanism sentence explicitly **withdrawn**, with the evidence inline. Replaced
by NEW m49 work in two named parts: (i) transport — an additive
`variation_labels: tuple[tuple[int, frozenset[str]], ...]` field on `_PartitionReduce`, keyed on
**post-reduction** node ids from the same `compile_ir` that produced the shipped `ir`, so
`Plan`/`ExecResult` schemas stay untouched; (ii) attributed worker-side errors, which do not exist
today — wrap the `evaluate_ir` call site and ship the per-node provenance the map keys alongside.
Anchors appendix row replaced. (Merged with D11 below for the set-valued fix.)

### T2 — §1.2 and §6.1c had no frozen anchor at any milestone — **APPLIED**

**Verified.** Read every m48–m51 anchor bullet: no label-absence anchor, no dedup anchor, no
`.plan()`-refusal anchor; §5.2a's "witnessed separately as the dedup feature" had no referent in
§10. The hazards are real: `_SumFills` sums every staged fill into one histogram
(`graphed-histogram-latest/src/graphed_histogram/boost.py:88-98`) while `_GroupReduce` keys by label
(`:99-117`); and the params-absence pattern the plan cites
(`graphed-histogram-latest/tests/frozen/m29/test_multi_weight_fills.py:93-96`) is on a single-weight
UNVARIED node, constraining nothing about varied graphs.

**Edit.** Two m48 anchors added: **§1.2 label-out-of-identity** (no node in a varied program's store
carries a label string in params/token; renaming every label leaves `compile_ir(...).ir`
byte-identical) with the **dedup witness** folded in (Δ = 0, same node id, both keys present with
ONE evaluated fill per §7.2); and **§6.1c `.plan()` refusal** with a positive control that unvaried
`.plan()` still works. §5.2a's dangling "witnessed separately" now points at the m48 anchor.

---

## MID

### D7 — §6.4c/d assume multiplicity preservation; §2.1's form check does not — **APPLIED**

**Verified** by reading §2.1 ("compatible forms (backend `op_form`-checked)") against §6.4c/d. An
awkward form match is a type check; per-event multiplicity is not constrained by it, and XOR deltas
require identical buffer lengths.

**Edit.** §6.4d gains a **bound refusal**: a stored varied field whose per-label offsets differ from
nominal's is refused naming the label and the field; supported v1 model = same-multiplicity
variation + per-label validity masks. Frozen as an m51 negative anchor (with a positive control) and
parked in §11.

### D8 — §6.4e's writer swap contradicts §6.4g's byte identity — **APPLIED**

**Verified, measured** (awkward 2.12.0 / pyarrow 25.0.0): `ak.to_parquet` sha256[:16]
`ad1725aca34f2bbb` vs `pq.write_table(ak.to_arrow_table(a))` `43b093e8bc616bd7`; KV keys
`{awkward_array_metadata, ak:parameters}` vs `{ak:parameters}` — the arrow path loses awkward's own
metadata. `inspect.signature(ak.to_parquet)` confirms no metadata parameter, so the swap really is
needed for the manifest.

**Edit.** §6.4e binds the branch explicitly (unvaried keeps `ak.to_parquet` untouched; varied takes
the arrow path and MUST reproduce awkward's KV entries), with the measurement inline; m51 manifest
anchor gains an `ak.from_parquet` round-trip on the augmented file; new Anchors row.

### D9 + T3 — §3.3/§5.2a pin integers wrong for the stated topology — **APPLIED**

**Verified, measured this session** against `graphed-latest` (builder: source → 500-op shared prefix
→ per variation {shift, 50 chain ops, [reduction]}, all universes marked outputs):

| builder | N=16 | N=128 | Δ(N=1→2) |
|---|---|---|---|
| **with** per-universe reduction | stages 17, reduced 34 | stages 129, reduced 258 | **52** |
| without | stages 17, reduced 18 | stages 129, reduced 130 | 51 |

`2N+2` and `Δ = 52` hold only WITH the terminating reduction — matching cba §optimizer §2's measured
builder ("+ 1 reduction", cba:274) and its stated shape (cba:283). §3.3's prose omitted it.

**Edit.** §3.3 spells the builder explicitly (source → D-op prefix → per universe {1 fork op, K chain
ops, exactly one terminating reduction}, each reduction separately marked, N counting nominal), with
the both-ways measurement inline and the note that a fill IS a reduction. §5.2a likewise ties
`Δ = K + 2 = 52` to that builder and records the without-reduction 51.

### D10 — §4.3's structural predicate is false as literally written — **APPLIED**

**Verified** by construction from §3.4's own definition: impact set =
`reachable(label's outputs) − reachable(nominal outputs)`; the label's output IS its sibling fill
node, which is unreachable from nominal's output and sits downstream of (not inside) the
weight-input cone — so the r9 assertion fails a correct implementation.

**Edit.** The parenthetical is promoted to the binding form ("the selection cone's node ids are
identical across all weight labels"), the old wording explicitly withdrawn with the reason, and the
m48 anchor at §10 rewritten to quote the binding form.

### D11 — the node-id → label map is not a function — **APPLIED (merged into the §8.2 rewrite)**

**Verified** in-document: §3.4 states "a node shared by `jes_up` and `jes_down` but not nominal
appears in **both** impact sets." `StageError.__hash__` is an explicit tuple that must be extended
(`graphed-latest/python/graphed/debug/errors.py:80-81`), while `__eq__`/`__reduce__` ride `__dict__`.

**Edit.** §8.2's map is `frozenset[str]`-valued and the rendering is bound (singleton → that label;
multi → sorted, `,`-joined; empty → `""`). m49 anchor extended with a shared-node failure asserting
the multi-label rendering — without it a pick-one implementation passes.

### D12 — §2.4's union ORDER undefined — **APPLIED**

**Verified**: §2.2 orders only within a container; §3.2 requires "labels in `graphed.labels` order"
for deterministic expansion; `_GroupReduce`'s layout is positional in compiled-fill order
(`boost.py:102-117`), so the m48 byte-identical-compilation anchor rested on an unstated rule.

**Edit.** §2.4 binds the order (first operand's order, then labels new to the second in its own
order, nominal first); m48's §2.4 anchor pins it.

### D13 — `**tags` collides with `vary`'s own parameter names — **APPLIED**

**Verified** from the signature at §2.1 and §1.1's grammar `[A-Za-z0-9_]+`, which admits `nominal`,
`is_weight` and `variations`; overload (c) uses `**tags` for tree collection names, which are
analysis-controlled — the exact hazard class §2.6a calls load-bearing.

**Edit.** §2.1 states the shadowing and binds the escapes: `variations={tag: …}` for tags in
overloads (a)/(b), a `collections={Name: {tag: record}}` mapping for collections in (c), with
`variations=` REJECTED in the shift form. m48 grammar anchor covers all three names.

### D14 — §2.6d silently drops shift variations on a data context — **APPLIED**

**Verified**: §2.6d guarded only `is_weight=True` then said data contexts "fill nominal-only", so a
shift-form `vary` was accepted and its labels discarded — the §2.5 failure mode. The "data context"
predicate had no definition anywhere in the plan.

**Edit.** §2.6d refuses BOTH forms with an error naming the variation ("fill nominal-only" becomes
structural), and pins the data flag as an explicit constructor flag
(`gnano.events(src, is_data=True)`-shaped, spelling at m48 freeze). m48 anchor updated.

### T4 — m49's reference-matrix anchor is ambiguous and the fixtures are missing — **APPLIED**

**Verified.** `graphed-corpus-latest/pyproject.toml:28-30` packages only `src/graphed_corpus`, while
the 23 reference JSONs live in `corpus/references/` outside the packaged tree; `graphed-latest`
vendors them at `tests/_corpus/references` and puts `tests/_corpus` on `pythonpath`
(`pyproject.toml:115-117`). `graphed-exec-check/pyproject.toml:20-35` depends on `graphed` +
dev-extras `graphed[awkward,numpy]`, `graphed-corpus`, numpy, awkward — **no `graphed-histogram`**
(grep for "histogram" over its pyproject and workflows: no hits). The house pattern there recomputes
in-process (`tests/frozen/m7/adl.py:124-158`).

**Edit.** §10's m49 anchor split into (i) the `graphed` frontend half against the vendored
references — and the §5.2b read witness bound to THIS run — and (ii) the `graphed-executors` half,
which **adds `graphed-histogram` to that repo's dev extra as part of m49** and compares against
corpus references recomputed in-process; the weaker materialize-then-fill alternative is explicitly
rejected in the text with its reason.

### T5 — binding requirements with no milestone anchor — **APPLIED**

**Verified** by cross-checking every §§1–9 bullet against §10's anchor lists. Un-anchored: §2.1
stacking, §2.2 `Varied.apply` + its error contract, §6.1a shape rules, §9.1 `graphed.variations`
(both numeric parsers), §7.2 schema absence. Converse check clean — no orphan anchors. Corpus
evidence that stacking is real semantics: `graphed-corpus-latest/src/graphed_corpus/analyses/systematics.py`
(jes_up's b-tag weight is the central SF on shifted jets), reproduced only by m49's matrix.

**Edit.** Five anchors added — m48: §2.1 stacking (order, central-universe member, one knob per
label), §2.2 `.apply` incl. the Varied-return refusal, §6.1a shapes on a mixed varied/unvaried
output set, §7.2 schema absence; m50: §9.1 `graphed.variations` with both parsers and a non-numeric
tag returning no value.

### T6 — m51's superset anchor names a self-derived reference — **APPLIED**

**Verified** in-document: §6.4a records the OR "as ordinary graph ops over the per-label masks", so
comparing the written rows against per-label row sets from the same graph degenerates to
`OR(masks) == OR(masks)` under a wrong per-label mask — the trap §5.2a itself names. Independent-
reference house pattern exists (`graphed-histogram-latest/tests/frozen/m23/test_group_plan.py:60-66`;
`graphed-exec-check/tests/frozen/m7/adl.py:156-158`).

**Edit.** The m51 anchor now requires per-label reference row sets computed **eagerly with plain
awkward, outside graphed**, from the same input events; the written set equals their union and each
universe's reconstructed rows equal its eager set.

### T7 — §9.2's anchor presupposes an API that does not exist — **APPLIED**

**Verified.** `build_bundle(root, *, session, value, weight=None, …, histogram=None, …)` is strictly
singular and raises unless `weight=` and `histogram=` are given together
(`graphed-latest/python/graphed/preserve/bundle.py:103-123`); `reproduce(bundle) -> Any` returns "its
histogram" (`:206-210`).

**Edit.** §9.2 binds the varied input shape (a `Varied` `value=`/`weight=`, equivalently a per-label
mapping) and `reproduce` returning `{label: array}`, with the explicit backward-compat statement
that an unvaried bundle still returns a bare array; spellings pinned at m50 freeze. m50 anchor
updated.

### T8 — R0.10a applied inconsistently to §3.3 — **APPLIED**

**Verified.** `graphed-root-prompt.md:200-215` states R0.10a in full including "a frozen *gate* must
not depend on it"; `graphed-latest/tests/frozen/core/m4/test_benchmark.py:28-53` is the existing
frozen wall-clock ratio gate (`growth < 24.0`, per-size `elapsed < 1.0`, noise floor
`base = max(times[SIZES[0]], 1e-4)`), discharging the project plan's M4 anti-quadratic mandate. §3.3
replicated that shape without acknowledging the tension, while m50/m51 cite R0.10a to bar it.

**Edit.** §3.3 now names itself the deliberate M4 carve-out to R0.10a — the ONE frozen wall-clock
gate in m48–m51 — replicates the m4 noise floor and best-of-N timing explicitly, contrasts itself
with §6.2/§6.4c (demoted to R0.11 report measurements because they carry no such mandate), and
quotes the measured headroom (cba §optimizer §2: 3.1 ms at N=16, 16.7 ms at N=128 ⇒ ≈5.4× against
the 24.0 gate).

---

## LOW

### F2 — "correctionlib scale-variation sets natively key on such strings" unsupported — **APPLIED**

**Verified.** `grep -in correctionlib` over the litsearch, cba and worklog returns no float-keyed-set
claim anywhere. §4.1 documents only the `systematic` CATEGORY parameter, whose fixture keys are
"nominal"/"up"/"down" (`graphed-latest/tests/frozen/preserve/m9/agc.py:56-62` is the anchored input).
**Edit.** Weakened to the supportable form: correctionlib category inputs are arbitrary strings
(`agc.py:56-62`), so a float-spelled key is expressible.

### F3 — RNTuple dotted-name hazard mis-attributed and mis-anchored — **APPLIED**

**Verified twice.** Source (`uproot5-graphed/src/uproot/behaviors/RNTuple.py`): `__getitem__` does an
exact `self._lookup.get(where)` FIRST at `:1560-1562`, falling back to `where.split(".")` at
`:1564-1569`; the cited `:1573-1576` is the `keys=`/`file_path=`/`object_path=` argument block of the
fallback's re-raise. `to_akform` is what actually splits: `path_keys = self.path.split(".")` at `:562`
then `tmp_field = tmp_field[key]` at `:567`. Live probe (uproot 5.7.5 / awkward / pyarrow, RNTuple
with a field literally named `murf_0.5`): `keys ['murf_0.5','plain']`; `nt["murf_0.5"]` **succeeds**
(returns `<RField 'murf_0.5'>`); `.array()` raises `KeyInFileError: not found: 'murf_0'`;
`nt.arrays(["murf_0.5"])` **succeeds** and returns the data.
**Edit.** §1.1 and §6.4b restate the measured mechanism (exact-first getitem, `to_akform` splits,
`arrays([...])` still works); the Anchors row is re-pointed to `:1560-1562`, `:1564-1569`, `:562,567`.
The owner-locked identifier-only decision is untouched — only the stated fact changed.

### F4 — `behaviors/TBranch.py:2098` is `def array(`, not the exact-first lookup — **APPLIED**

**Verified.** `:2094-2102` is `def array(`; the exact-first lookup is
`got = self._lookup.get(where); if got is not None: return got` at `:2015-2017`, and this getitem
splits on `/` (`:2019-2024`), never on `.` — confirming the TTree hazard belongs to the WRITER
(`writing/_cascadetree.py:1600-1609`: `out[field_name + "." + subfield_name] = subfield`).
**Edit.** Anchors row split in two, citing `:2015-2017` (+`:2019-2024`) for the reader and
`_cascadetree.py:1606` for the writer, with the `/`-only note.

### F5 — §2.3(b) mis-describes today's `__getitem__`/`filter` — **APPLIED**

**Verified.** `graphed-latest/python/graphed/array.py:344-371`: `__getitem__` accepts an `Array` mask
(`:345-346`), a `str` field (`:347-348`), a `list[str]` subset (`:351-354`), a `slice` (`:358-366`)
and an `int` (`:367-368`), raising `TypeError` only otherwise (`:369-371`). `filter` (`:374-375`)
performs no check; a non-Array falls into `record_op` and `AttributeError`s on `a.node_id`
(`session.py:152,159`).
**Edit.** §2.3(b) rewritten to the measured behaviour; Anchors row corrected.

### F6 — Discussion #469's "2-8×" presented as measured — **APPLIED**

**Verified.** `systematics-vary-litsearch.md:236` records "~2-3× … up to ~7-8×" with the explicit
caveat "(Content read via summarizing fetch; exact attributions/quotes UNVERIFIED at word level —
the URL is the evidence.)"
**Edit.** Part I §2 now says "*reports*", quotes both figures, and carries the caveat with the line
citation. (Part I binds nothing and no PART II requirement rests on it — §6.2's axis mode is grounded
in the cba §histogram §3 bh 1.7.2 probes, verified independently.)

### F7 — §6.1d overloads the word "provenance" — **APPLIED (via D1)**

**Verified.** `provenance.py:66-79` is source-location capture, the sense the plan itself anchors in
§2.3 and the Anchors appendix.
**Edit.** §6.1d now names the **context handle** (§2.3e) and says explicitly it is not `Provenance`
and not `Session._provenance`/`sourcemap()`; a new Anchors row records the distinction.

### D15 + T12 — §6.4b's stale r8 citation and p-form lead — **APPLIED**

**Verified** against §1.1's r9 e-form paragraph and the r9 revision-history entry.
**Edit.** "§1.1 r8 canonicalization" → "**§1.1 canonicalization, r9 e-form**"; the canonical on-disk
shape `__vary_murf_5em1__Jet_pt` now leads, with the p-form fixture kept as carried-over probe
evidence.

### D16 — negative zero and exponent magnitude unspecified in the e-form — **APPLIED**

**Verified** from §1.1's own grammar: the input grammar `-?\d+(\.\d+)?([eE][+-]?\d+)?` admits `-0`,
`-0.0`, `-0e5`, and the canonical rendering rule did not say whether they render `0` or `m0`; nor was
any bound placed on the exponent, so `1e400` would canonicalize under exact decimal arithmetic to a
401-character label embedded in a parquet column name per §6.4b.
**Edit.** §1.1 adds: negative zero canonicalizes to `0` (never `m0`), and a canonical tag longer than
**32 characters is REJECTED** (covers every real σ-scan / μR-μF / PDF family). m48 grammar anchor
extended.

### D17 — §6.1a's heterogeneous result type is not typeable as stated — **APPLIED**

**Verified.** The DoD requires `mypy --strict` on src AND tests; `_add_groups` assumes a homogeneous
mapping (`graphed-histogram-latest/src/graphed_histogram/boost.py:120-122`).
**Edit.** §6.1a declares the union type `dict[str, bh.Histogram | dict[str, bh.Histogram]]`,
acknowledges the typing cost, binds the combine's branch, and binds
`graphed.universe`/`graphed.labels` as the narrowing helpers that work on both shapes (a bare hist
reading as the single label `"nominal"`). m48 anchor added (see T5).

### D18 — m48 freezes the gak `refusing` class whose contract is an m49 target — **APPLIED**

**Verified.** §2.3c's classification includes `refusing (gak.join and boundary verbs, per §5.4)`;
§5.4 (message + positive control) is an m49 target.
**Edit.** §10's m48 anchor now says the classification test freezes only that every DISCOVERED public
gak function HAS a classification, and that the *behaviour* of the refusing class is an m49 anchor
because §5.4 is an m49 target.

### T9 — "frozen exhaustiveness test" ambiguous against the repo's literal-list house style — **APPLIED**

**Verified.** `graphed-latest/tests/frozen/awkward/m24/test_interface_parity.py:37-78` iterates a
hand-written 41-name tuple — a future gak function would go silently unclassified.
**Edit.** §2.3(a) and §2.3(c) now require the inventory to be **dynamically enumerated at test time**
(with the m24 literal cited as the anti-pattern and the self-repairing rationale stated); §2.3(e)
inherits the same gate; the m48 anchor says "dynamically enumerated".

### T10 — "no constant-Array constructor exists" is too strong — **APPLIED**

**Verified.** `gak.full_like(arr, value, *, dtype=None)` records `ak.full_like`
(`graphed-latest/python/graphed/awkward/functions.py:612-616`) and is parity-pinned at
`tests/frozen/awkward/m24/test_interface_parity.py:74-76`. The cba grep behind the claim (cba:196)
was scoped to the session/array modules and did not cover `graphed/awkward/functions.py`.
**Edit.** §4.1 binds `gak.full_like(<per-event Array>, sf)` as the v1 form, states that what does not
exist is a constant Array with **no shape donor**, and re-scopes the §11 parking accordingly; the m48
ttgamma note points at the spelling; new Anchors row.

### T11 — consolidated-repo frozen directories unspecified — **APPLIED**

**Verified.** `graphed-latest/tests/frozen/` has 8 package subdirs; `pyproject.toml:103-130` documents
per-subtree, per-milestone isolation (naming the m39/m40 and m5/m40 basename collisions) and lists the
cross-dir helper providers on `pythonpath`.
**Edit.** §10's preamble pins `tests/frozen/frontend/m48`, `frontend/m49`, `preserve/m50`,
`awkward/m51`, plus the §3.3 benchmark in `core/m49`, and states that any cross-directory helper must
be added to `pythonpath` (a shared `vary` fixture module is expected).

---

## Rejected

None. Every finding survived independent verification.

## Deferred (owner-locked)

None. No finding's only resolution would have reversed an owner-locked decision. The owner-locked
set — naming/labels, the single functional module verb with no reserved names, e-form canonical
float tags, context attachment with simultaneous event+object application, record-time expansion +
hash-consing with no new Rust NodeKey, m48–m51 scope including §6.4, the JER-SF non-monotone
contract, and the deliberate Phase-2 pull-in — is unchanged by r10. No "OPEN ITEMS (owner)" block
was added.
