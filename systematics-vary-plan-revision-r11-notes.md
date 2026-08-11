# systematics-vary-plan r11 — revision notes (review round 2 audit trail)

Input: three independent r10 reviews (`systematics-vary-plan-review-r10-{facts,design,tests}.md`),
40 findings excluding NITs. After cross-lens merge: **39 unique — 1 BLOCKER, 7 HIGH, 15 MID,
16 LOW**. (design `§6.1a vs §6.2` HIGH and tests `§6.1a + §6.2` MID are the same defect; merged and
resolved once, at the higher severity.)

**Verdict summary: 39 applied, 0 rejected, 0 deferred.** Every finding's evidence was re-derived in
this session against the pinned verification roots before any edit; nothing was taken on the
reviewer's word. No finding's resolution required reversing an owner-locked decision, so no
`OPEN ITEMS (owner)` block was added.

Verification roots used: `/private/tmp/claude-501/graphed-latest` (ff7c607),
`graphed-histogram-latest` (211cbbe), `graphed-corpus-latest` (49650e4), `uproot5-graphed`
(393ecef), plus `/Users/lgray/vibe-coding/graphed-workdir/.venv` for runtime probes.

---

## BLOCKER

### 1. design §6.4a/§6.4d/m51 — object-level cutflow data no bound API can supply — **APPLIED**

**Re-verified.** The write path has one output and no mask input:
`graphed-latest/python/graphed/awkward/io.py:111-127` (`(out,) = evaluate_ir(...)`;
`ak.to_parquet(payload, path)`); `to_parquet`'s signature (`io.py:206-216`) has no selection
channel at all. Plan §6.4a bound exactly one event-level row mask, while §6.4d requires per-label
validity masks "at every selection level that varies — event-level AND object-level", and m51
freezes an object-migration positive control. Both reachable spellings fail as the reviewer states:
post-object-cut record → §6.4d's offsets refusal fires on the case being tested; pre-object-cut
record → the writer has no knowledge of the inner cut. §6.4a's own argument forecloses inferring it
from the expression.

**Edit.** §6.4a: `select=` re-bound to be **per selection level** — either one `Varied` row mask or
an ordered per-depth mapping (`{0: event_mask, 1: jet_mask, …}`); the writer applies none of them
to stored buffers, stores one packed per-label validity mask per supplied level, and builds the
level-0 OR for the superset. §6.4d: states that the object-level half is expressible *only* because
of that channel. m51 round-trip anchor: names the per-level channel explicitly. (Chose the
reviewer's primary fix over the "park object-level masks in Phase 2" alternative — the latter would
delete a requirement §6.4d states emphatically, and the channel is a one-parameter change.)

## HIGH

### 2. facts §2.6 sketch — `lhe_w[:, 0]` / `lhe_w[:, i]` not expressible — **APPLIED**

**Re-verified + extended by measurement.** `Array.__getitem__` accepts Array/str/list[str]/slice/int
and raises otherwise (`array.py:344-371`); measured: `w[:, 1]` →
`TypeError: unsupported index (slice(None, None, None), 1)`. Tuple subscripts are numpy-idiom only
(`numpy/array.py:132-136`, the `"subscript"` op). `grep '^def ' python/graphed/awkward/functions.py`
→ 73 defs, no inner-index verb.

**I measured a spelling that does work today**, which the reviewer did not: with an
`AwkwardBackend` session over `{"w": [[1,2,3],[4,5,6]]}`,
`gak.firsts(w[gak.local_index(w) == 1])` records and materializes `[2.0, 5.0]`.

**Edit.** Sketch respelled to `member = lambda i: gak.firsts(lhe_w[gak.local_index(lhe_w) == i])`;
a new note (i) after the sketch records the measured `TypeError`, the numpy-idiom anchor, and the
working spelling. §11 parks a first-class gak inner-index verb as ergonomics, explicitly NOT scoped
into m48–m51 — so no milestone silently acquires frontend work.

### 3. design §6.2 — "the FRONTEND declares the axis at plan time" vs record-time spec identity — **APPLIED**

**Re-verified.** `graphed-histogram/src/graphed_histogram/boost.py:144-150`
(`self._spec = spec_of(self)` in `__init__`) and `:180-212` (`chash = content_hash(self._spec)`;
`params={"spec": self._spec, …}`; `self._evaluators[chash] = evaluator`); `_spec.py:115-122`
(`spec_of` = f(axes, storage)), `:129-135` (`zero_of`). Adding an axis after the fills exist leaves
nodes, evaluators, `_GroupReduce`'s per-slot spec and `_GroupZero` disagreeing.

**Edit.** §6.2(i) re-bound to **fill time** with the measured argument stated inline, plus the
cross-fill agreement rule (a second fill with a differing inferred label set is a hard error naming
the mismatch). Noted that each fill node's params/evaluator already carry their own spec, so
fill-time declaration needs no new machinery. m50 gains a cross-fill-agreement anchor clause.

### 4. design §6.1a / tests §6.1a+§6.2 (MERGED) — no axis-mode result shape; narrowing helper is wrong there — **APPLIED**

**Re-verified.** §6.1a binds two shapes and "a bare hist reads as the single label nominal"; §6.2's
axis mode produces a third (one bare histogram carrying all labels), indistinguishable by type.
Runtime confirms nothing disambiguates: `_GroupReduce` returns `{label: hist}`
(`boost.py:100-122`), `_add_groups` combines key-wise over `a`'s keys (`:120-122`).

**Edit.** New §6.2 clause **(i-bis)** binds the axis-mode result shape (bare hist carrying the
`"variation"` axis) and makes `graphed.labels`/`graphed.universe` recognise it (labels = the axis
bin set; universe = the `h[{"variation": label}]` slice), keeping the helper uniform over all three
shapes. §6.1a scoped to "the DEFAULT sibling-fill lowering". m48's result-shape anchor re-worded to
sibling mode so it cannot freeze a rule m50 must contradict; m50 gains an (i-bis) anchor.

### 5. design §6.1d/§2.3e — the fill is itself a combining point; the divergence error had no raiser — **APPLIED**

**Re-verified.** `Histogram.fill` collects args + weights + sample into ONE `inputs` list and
records ONE External node (`boost.py:154-212`), so `h.fill(a_from_ctx1, b_from_ctx2,
weight=[w_from_ctx3])` is the first place those handles meet — no op combined them.

**Edit.** §2.3e: "The op is not the only raiser — every *combining point* runs the same
unification, and the fill is one of them"; op-level detection re-framed as *early*, not sole.
§6.1d: the fill runs its own most-derived unification and divergence check across all axis values,
all explicit weight factors, and the ambient weight. m48's context anchor gains an explicit
divergent-lineage-AT-THE-FILL case.

### 6. design §6.1d — the "already-flattened value" refusal had no mechanism and no discriminator — **APPLIED**

**Re-verified.** The evaluator flattens each input independently
(`_flat = ak.flatten(values, axis=None)`, `boost.py:39-47,60-71`). A per-event value
(`gak.firsts`, `gak.num`, `MET.pt`) and a flattened per-object value have identical 1-D forms and
differ only in runtime length; the cone-walk alternative false-positives on
`gak.flatten(x, axis=2)` (still jagged).

**Edit.** §6.1d binds the refusal at **execution time**: `FillEvaluator` raises when a weight
input's flattened length differs from the axis values', naming the ambient weight and pointing at
"pass the value unflattened". The m48 anchor is re-worded to that contract, with an explicit
instruction NOT to freeze a record-time raise.

### 7. design §2.1 — "members pass through unchanged" is wrong for the weight form — **APPLIED**

**Re-verified in the corpus source.** `graphed-corpus/src/graphed_corpus/analyses/systematics.py`:
`sel_jets = good[sel]` then `weight = _btag_weight(sel_jets, variation=variation)` (`:73-75`), and
`_btag_weight` returns the **central** SF unless `variation` is `btag_up`/`btag_down` (`:25-36`).
So `ttbar_4j1b_jes_up` IS b-tag weighted with the SF computed on JES-shifted, JES-selected jets —
the naive "inherited labels keep the old ambient" reading omits it entirely. Freeze risk confirmed:
m48's matrix is weight-only (no shift labels), so a wrong reading survives m48's stacking anchor.

**Edit.** §2.1's stacking paragraph split per overload: (a)/(c) members pass through unchanged;
**(b)** the new factor combines into the ambient weight label-aligned per §2.4, so inherited label
L becomes `old_ambient[L] × factor[L]` (the factor's own L universe; its central universe only when
L is new). The corpus evidence is quoted inline with file:line. m48's stacking anchor extended to a
weight `vary` on a context already carrying shift labels, asserting the inherited label's ambient
member.

### 8. tests m48 — headline anchor not buildable in either repo; anchor list not partitioned — **APPLIED**

**Re-verified, every fact.** `graphed`'s `dev` extra lists `boost-histogram>=1.4` and `hist>=2.7`
and never `graphed-histogram`; CI installs `.[dev]` (`.github/workflows/ci.yml:34,57,143`); the
house pattern is `pytest.importorskip("graphed_histogram")`
(`tests/frozen/preserve/m25/…:31`, `m27/…:185,207`, `m30/…:155`) → an anchor there SKIPS in CI.
`graphed-histogram`: `grep -rn "corpus" tests/ .github/workflows/` → 0 hits; runtime deps are
`["graphed", "boost-histogram>=1.4", "numpy>=1.24"]`. Corpus wheel packages only
`src/graphed_corpus` (`pyproject.toml:28-30`) while `ls corpus/references | wc -l` → 23, and
`graphed` vendors those 23 JSONs at `tests/_corpus/references` (on `pythonpath`).

**Edit.** m48 gains a repo-partitioning paragraph mirroring m49(i)/(ii): pure-frontend anchors in
`graphed tests/frozen/frontend/m48`; every fill-dependent anchor (corpus weight matrix + §5.2b
witness, §6.1a, §6.1c, §6.1d, §4.1, §6.3) in `graphed-histogram tests/frozen/m48`. Binds the
dependency edit (add `graphed-corpus` to `graphed-histogram`'s `dev` extra and vendor the 23
reference JSONs the way `graphed` does) and states the matrix anchor MUST NOT be `importorskip`-
guarded, with the diff-coverage consequence spelled out.

## MID

### 9. facts §10 — `uproot5-graphed-mvp` has no existing frozen layout — **APPLIED**

**Re-verified at 393ecef.** `find . -type d -name "*frozen*"` → empty; graphed tests are 14 flat
`tests/test_graphed_*.py` files; no `tests/frozen` reference repo-wide.
**Edit.** §10's frozen-layout paragraph replaced with the measured fact plus the decision: m51
CREATES `tests/frozen/m51/` there; existing flat tests stay unfrozen.

### 10. design §2.3e — the bound "plain Python attribute" is impossible on a `__slots__`-ed Array — **APPLIED**

**Re-verified.** `array.py:127-128` (`__slots__ = ("_node_id", "_session")`),
`numpy/array.py:71-74` (`__slots__ = ()`), `__getattr__` underscore guard `array.py:332-335`.
Propagation chokepoint confirmed: `session.py:140,168,183,204,242` all `return self._array_cls(self,
node_id)` — **five** sites, not the four the reviewer counted; the plan states the fact, not a count.
**Edit.** §2.3e binds one added underscore-prefixed slot as an Implementation Target and names
`Session`'s construction sites as the single propagation site, re-framing "every op, every gak
function, every module verb" as inherited-by-construction with the dynamic test as the anti-drift
gate over bypassers.

### 11. design §7.2/§6.1c — node-id unpacking unreachable through `_GroupReduce`'s count layout — **APPLIED**

**Re-verified.** `boost.py:100-117` (`layout: tuple[tuple[str, int, str], ...]`,
`for j in range(i, i + k)`), built from `len(h._fill_nodes)` at `:198`; `aggregate.py:57-65` passes
`evaluate_ir`'s values straight to `reduce`; `src/store.rs:147-156` (`mark_output` de-dups);
`execute.py:126`. So two marked fills interning to one node makes `sum(k) > len(values)`.
**Edit.** §6.1c binds the layout change explicitly — per-slot output **INDICES**
(`tuple[tuple[str, tuple[int, ...], str], ...]`, or `{(output,label): [indices]}` two-level) derived
frontend-side per §7.2 — with the note that "generalized to two-level keys" is satisfiable while
shipping the bug.

### 12. design §2.1 — `collections=` missing from the bound signature — **APPLIED**

**Confirmed by reading.** The signature omitted it while the next sentences mandate it, and m48's
grammar anchor freezes "reachable only through `variations=` / `collections=`".
**Edit.** `collections=None` added to the signature; the shadowing clause now covers **four** names
with `collections`' self-reference rule (`collections={"collections": {...}}`); m48's grammar anchor
updated to FOUR.

### 13. design §2.4/§6.1d — the fill's three-way union has no bound order — **APPLIED**

**Confirmed by reading**; §2.4 binds order only for a BINARY combination and states the dependence
(§3.2 determinism, `_GroupReduce` layout).
**Edit.** §6.1d binds a left fold in a fixed operand order: axis values in argument order, then the
ambient weight, then explicit `weight=[…]` factors in list order. m48's union-order anchor extended
to a fill with two varied axes + ambient + explicit factor.

### 14. design §6.1d — only the ambient weight is broadcast; explicit factors still mismatch — **APPLIED**

**Re-verified.** `boost.py:60-71`: `axes = [_flat(v) …]`, `weight = _flat(rest.pop(0))`,
`weight = weight * _flat(rest.pop(0))` — every input flattened independently, factors multiplied
after flattening. A per-event `weight=[events.genWeight]` in a per-object fill flattens to
`n_events` against `n_objects`.
**Edit.** §6.1d's broadcast rule extended to "every weight factor the fill applies — the ambient one
AND explicit `weight=[…]` factors"; the m48 broadcast anchor covers the mixed case.

### 15. design §6.4a — "pre-selection by construction" unenforced; refusal predicate undecidable — **APPLIED**

**Confirmed by reading** §6.4a/§6.4b/§1.2: a values-varied record and a mask-varied record are both
just `Varied` containers, labels are outside the IR, and the NON-varied embedded selection
(`sel = events[nominal_mask]` + `select=varied_mask`) passes the r10 refusal and silently writes
wrong rows.
**Edit.** §6.4a replaces "by construction" + the embedded-`Varied`-selection refusal with a
**decidable entry check**: at entry, every per-label member's offsets must equal nominal's at every
level to be stored (§6.4d's own rule, run once up front) — one predicate catching the embedded
selection and the multiplicity case together. m51 gains an entry-check anchor with the
silent-corruption case as a named positive.

### 16. design §6.1b — the `1+|S|+|W|` arity is unconditional; axis mode contradicts it — **APPLIED**

**Confirmed by reading.** §6.1b was frozen-counted in m49; axis mode's arity is `1+|S|`.
**Edit.** §6.1b scoped to sibling mode with a forward pointer; §6.2 states `1 + |S|` next to the
m50 structural anchor.

### 17. design §2.6a — "`[]` resolves ONLY tree content" contradicts `events[mask]` — **APPLIED**

**Confirmed by reading** §2.6a vs §2.6c and the sketch (`sel = events[gak.num(jets) >= 4]`); m48
freezes §2.6a's clause.
**Edit.** §2.6a re-worded: `[]` with a string (or list of strings) resolves tree content; `[]` with
an `Array`/`Varied` mask derives a new context, mirroring `Array.__getitem__`'s own split
(`array.py:344-371`). Headline re-cast as "reserves NO NAMES".

### 18. design §6.1d — the bound broadcast mechanism is awkward-only on a neutral seam — **APPLIED**

**Re-verified.** `python/graphed/awkward/functions.py:677-685` records the awkward-namespaced op
`"ak.broadcast_arrays"`; `grep -rn broadcast python/graphed/numpy/*.py` → a docstring mention only;
`graphed-histogram pyproject.toml:20-21` runtime deps carry no awkward (`:24-38` dev extra does).
**Edit.** §6.1d re-binds the broadcast as a **neutral, backend-dispatched seam** supplied by the
event context (already backend-flavored), with the awkward implementation recording
`ak.broadcast_arrays` and the numpy idiom documenting a no-op/refusal; ownership stated
(seam in `graphed`, implementation in `graphed.awkward`, no awkward dep for `graphed-histogram`).

### 19. design §6.4a — `select=` has no relationship to the §2.6 context idiom — **APPLIED**

**Confirmed by reading** §2.2/§9.1 (contexts expose `labels`/`universe`/`nominal`/`variations`
only) against §6.4a's mask requirement.
**Edit.** §6.4a binds **`graphed.selection(ctx)`** → the `Varied` mask that derived a context
(`None` for a root context), added to §9.1's introspection surface and anchored in m51 with a
round-trip-equivalence assertion against the hand-passed mask.

### 20. tests §6.2 — the declaration contract's only measured-silent failure has no anchor — **APPLIED**

**Confirmed by reading** m50's anchor list (equality, combine-safety, allocation count — no
undeclared-label case) against §6.2's own measured basis (bh 1.7.2: `sum 2.0` vs
`sum(flow=True) 3.0`, `Traits(overflow=True, growth=False)`).
**Edit.** New m50 anchor: undeclared label → hard error naming it, with the
`h.sum(flow=True) == h.sum()` discriminator on the positive control; declared-but-unreached bin →
§2.5 diagnostic; unsorted user bin order → same spec as sorted; plus the cross-fill agreement error
from finding 3.

### 21. tests §2.3 — dynamic enumeration can pass vacuously; the stated discovery mechanism doesn't exist — **APPLIED**

**Re-verified.** `grep -c "__all__" python/graphed/awkward/functions.py` → **0**; the package
`__all__` (`awkward/__init__.py:17-31`) lists modules/classes, not gak functions;
`grep -c "^def " functions.py` → 73 including private helpers.
**Edit.** §2.3c binds the discovery rule (`inspect.getmembers(gak, inspect.isfunction)` filtered on
`__module__ == gak.__name__`, no leading underscore) AND a **non-vacuity floor** (non-empty, ≥ the
freeze-time count, one named member per classification class); §2.3a inherits it; the m48 anchor
requires the floor in the same frozen test and names `__array_ufunc__`, `__getitem__` and a bitwise
dunder for the dunder gate.

### 22. tests §2.3b — binding but unanchored; wrong implementation is a deep AttributeError — **APPLIED**

**Re-verified.** `array.py:343-369` (final `raise TypeError`), `:374-375`
(`def filter(self, mask): return self._session.record_op("filter", [self, mask])` — no check);
corpus `systematics.py:91-92` indexes unvaried photons by a JES-varied selection. No m48/m49 anchor
named it.
**Edit.** New m48 anchor: `plain_array[varied_mask]` and `plain_array.filter(varied_mask)` return a
`Varied` label-aligned per §2.4, with negative controls for both wrong-implementation shapes and a
still-`TypeError`s control so the branch cannot be a blanket `except`.

### 23. tests §6.4g — a committed parquet golden embeds its writer version — **APPLIED**

**Re-verified by probe** (`.venv`, pyarrow 24.0.0 / awkward 2.9.0): an `ak.to_parquet` file contains
`parquet-cpp-arrow version 24.0.0`; two writes of the same array **in one process** are
byte-identical (`True`). GIR precedent confirmed at
`tests/frozen/core/m40/test_join_serialize.py:83-99` (literal `b"GIR1\x03…"`).
**Edit.** §6.4g re-words the byte-identity as a **same-process comparison** (feature-present path vs
`ak.to_parquet` directly, plus manifest-KV absence), never a committed `.parquet` fixture, with the
R0.10a reasoning; m51's manifest anchor updated to match; committed byte oracles explicitly retained
for GIR/IR.

## LOW

### 24. facts §2.3(c) — the m24 anti-drift literal is 39 names, not 41 — **APPLIED**

**Re-counted.** The tuple holds exactly 39 names; the test starts at `:37`, the literal spans
`:39-79`. **Edit.** §2.3c now says "a **39**-name literal (`:39-79`)"; an anchors row records it.

### 25. facts Part I §3 — `D` means two different things — **APPLIED**

**Confirmed by reading** Part I §3 ("Δ = D+2") against §3.3 (D = shared prefix, K = chain,
Δ = K+2 = 52). **Edit.** Part I §3 now reads "Δ = K+2 = 52 nodes on the §3.3 builder" with an
explicit "§3.3 uses D for the shared prefix" warning.

### 26. facts m49(ii) — "the `graphed` repo contains no process pool" is false — **APPLIED**

**Re-verified.** `tests/frozen/debug/m6/test_process_boundary.py:7` imports `multiprocessing`,
`:16` is `with ctx.Pool(processes=1) as pool:` (spawn context). **Edit.** Re-worded to "ships no
`Executor` implementation … its only cross-process frozen test is the M6 error-transport pool", with
the file:line; anchors row added.

### 27. facts Anchors — two rows cite a "write-seam report" that exists nowhere — **APPLIED**

**Re-verified.** No such file in the working area. Both underlying facts re-derived independently:
`NodeKey` has no write/sink variant (enum `src/node.rs:41-85`); the only `metadata` uses on the
write/read path are `ParquetFile(path).metadata.num_rows`
(`python/graphed/parquet.py:77,107,118`) and `key_value_metadata`/`with_metadata` appear nowhere in
`graphed-latest/python` or `uproot5-graphed/src` (I ran both greps).
**Edit.** Both anchors rows replaced with those reproducible commands / file:line.

### 28. facts Anchors — `src/node.rs:41-70` doesn't span the enum whose completeness it establishes — **APPLIED**

**Re-verified.** `pub enum NodeKey {` at `:41`, closing `}` at `:85`; variant heads 42/46/51/56/64/
72/81 — `:41-70` omits Exchange and Join. **Edit.** Row re-cited as `:41-85` with the variant-head
list and the reason a completeness claim needs the full span.

### 29. facts §2.6 sketch — `h.fill(pt=…)` is a named-axis fill — **APPLIED**

**Re-verified.** `boost.py:153-163`: `fill(self, *args: Array, weight=…, sample=…, threads=…)` —
positional; kwarg axis names exist only in `hist.graphed`, not in m48's repo scope.
**Edit.** Sketch → `h.fill(sel.Jet.pt)`; note (ii) after the sketch records the signature and the
fork caveat; anchors row added.

### 30. design §6.4 — `to_parquet` is `graphed.awkward.to_parquet` — **APPLIED**

**Re-verified.** Exported only from `graphed/awkward/__init__.py:14,30`
(`awkward/io.py:206-216`); numpy has its own 1-D-capped writer (`numpy/io.py:158-173`, the
`result.ndim != 1` raise). **Edit.** §6.4a names the awkward-idiom spelling and states that §6.4f's
"numpy EXEMPT" means the numpy-idiom function refuses — no new neutral dispatcher; anchors row added.

### 31. design §2.6a — `graphed.variations` is load-bearing in m48 but anchored in m50 — **APPLIED**

**Confirmed by reading** m48's introspection anchor (universe/labels/nominal only) vs m50's.
**Edit.** §2.6a's list now says "and `graphed.variations` — §9.1, whose surface lands in m50", so
the m48 section no longer implies an m48 surface.

### 32. design §1.1 — "usable verbatim as a kwarg name" contradicted two paragraphs later — **APPLIED**

**Confirmed by reading.** Canonical numeric tags are digit-leading; `0p5=`/`2=` are SyntaxErrors.
**Edit.** Clause dropped from the identifier list and replaced with the explicit caveat plus the
pointer to `variations=` as the channel that exists for it.

### 33. design §1.1 — the 32-character cap bounds the tag, not what it is justified by — **APPLIED**

**Confirmed by reading.** The label is `f"{name}_{tag}"` and the on-disk name is
`__vary_{label}__{field}`, both unbounded.
**Edit.** Re-stated as "a tag-sanity bound and nothing more", with the explicit note that it does
NOT bound the label or the on-disk name.

### 34. design §1.1 — non-minimal hand-typed e-forms are legal and un-canonicalized — **APPLIED**

**Confirmed by reading** the input-sugar grammar `-?\d+(\.\d+)?([eE][+-]?\d+)?`, which cannot match
`50em2` (it contains `m`), so such a tag rides through as an ordinary identifier tag.
**Edit.** Chose the invariant-preserving option: a tag already matching the canonical numeric
grammar is **re-rendered minimally** (`"50em2"` → `5em1`, `"05"` → `5`). Near-free — the
cross-notation check already parses every tag under both parsers. Rationale stated inline; the m48
grammar anchor covers it.

### 35. tests m48 — the schema-absence anchor must be scoped to key sets; m49 churns `task_id` — **APPLIED**

**Re-verified.** `_PartitionReduce` is a frozen dataclass shipped as the plan's `process`
(`aggregate.py:44-65`); `OpSpec.identity()` returns `b"opaque\0" + blob` for embedded callables
(`core/plan.py:72-90`) and `task_id` folds `self.process.identity()` (`:164-176`).
**Edit.** §7.2 and the m48 anchor re-worded over **schema KEY SETS** (not plan bytes / the process
spec); §7.3 gains the one-time, ALL-programs journal invalidation that m49's closure field causes.

### 36. tests §1.1 — "unify" is ambiguous for a canonical/spelled pair in one call — **APPLIED**

**Confirmed by reading** §1.1's duplicate-after-canonicalization rejection against the m48 anchor's
bare "unify" sitting in a list of rejections.
**Edit.** §1.1 states the split explicitly ("**'Unify' means ACROSS calls**" …, within one call it
is a rejection); the m48 grammar anchor freezes both readings separately.

### 37. tests m48 — the corpus `stable()` rounding is not stated for the test-author — **APPLIED**

**Re-verified.** `tests/_corpus/graphed_corpus/analyses/systematics.py:79,102` round pre-fill,
`:50` rounds the view; `histograms.py:20` `STABLE_DECIMALS = 6`, `:34-37` `bin_values` rounds,
`:39-42` `fingerprint` hashes rounded values. gak has no `round(decimals)` — `rint` appears only in
the ufunc map (`array.py:54`).
**Edit.** The m48 corpus anchor gains the clause in the style of the `full_like` note: re-express
the pre-fill rounding (`rint(x*1e6)/1e6` is the expressible form), ride `bin_values`/`fingerprint`
for the comparison, and do NOT assert raw-view bit-identity against the references.

### 38. tests §2.5 / §8.1 — two binding clauses with no anchor — **APPLIED**

**Re-verified.** `debug/errors.py:74-77` (`__eq__` compares `self.__dict__` — a new field rides
free) vs `:79-81` (`__hash__` is a hand-written 5-tuple — it does not).
**Edit.** New m48 anchor for §2.5's unreached-label **diagnostic** (present when a registered label
reaches no output, absent otherwise); m49's §8.2 anchor gains "two `StageError`s differing only in
`variation` are unequal AND hash differently".

### 39. tests §10 — m50's histogram-side frozen directory is unpinned — **APPLIED**

**Re-verified.** `graphed-histogram tests/frozen/` contains only `m23` and `m29`; its pytest
`pythonpath` is `["src", "tests/frozen/m23"]`.
**Edit.** §10 now pins **`tests/frozen/m48` and `tests/frozen/m50`** for `graphed-histogram` and
notes m50's `graphed` half is `tests/frozen/preserve/m50` (preservation/docs only).

---

## Rejected

None. Every finding's evidence reproduced.

## Deferred (owner-locked tension)

None. No finding's resolution required reversing an owner-locked decision, so no
`OPEN ITEMS (owner)` block was added to the plan header.

## Notes for round 3

- The BLOCKER fix introduces a new API shape (`select=` accepting a per-depth mapping) and finding
  19 introduces `graphed.selection(ctx)`. Both are bound in §6.4a/§9.1 and anchored in m51, but they
  are the r11 surface additions most worth a fresh design read.
- §6.1c's re-bound `_GroupReduce.layout` (indices, not counts) is a change to a **shipped** class in
  `graphed-histogram`; it fixes a latent pre-existing bug (two unvaried histograms with identical
  fills), which m48 will surface. Checked for a freeze-order hazard: **none** —
  `grep -rn "layout\|_GroupReduce" graphed-histogram-latest/tests/frozen/` returns only two awkward
  `events.layout.to_typetracer` hits (`m23/test_process_executor_witnesses.py:87,109`); no frozen
  test pins the layout tuple's shape.
- Counts stated in the r11 revision-history entry (40 findings, 39 after merge; +19 anchors rows)
  were counted, not estimated.
