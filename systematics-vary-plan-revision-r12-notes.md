# systematics-vary-plan — revision r12 audit trail (review round 3, r11 reviews)

Reviser: isolated plan-reviser agent, fresh context. Input: 32 findings from three independent
r11 lenses (`systematics-vary-plan-review-r11-{facts,design,tests}.md`). Every finding was
re-verified in-session against the pinned verification roots before acting (R0.11 binds the
reviser as much as the reviewers). Commands and file:line citations below are ones I ran/read
myself in this session.

Verification roots used: `/private/tmp/claude-501/graphed-latest` (ff7c607),
`/private/tmp/claude-501/graphed-histogram-latest` (211cbbe),
`/private/tmp/claude-501/graphed-corpus-latest` (49650e4),
`/private/tmp/claude-501/uproot5-graphed` (393ecef).

**Outcome: 30 applied (after merging 2 cross-lens duplicate pairs), 0 rejected, 0 deferred.**
No finding's resolution required reversing an owner-locked decision, so no OPEN ITEMS block was
added.

Duplicate merges:
- FACTS "axis-mode narrowing binds a histogram-slicing spelling that does not exist" (MID) ==
  DESIGN "`graphed.universe(h, label)` = `h[{"variation": label}]` measurably does not work" (MID).
  Merged; one edit to §6.2(i-bis) + the m50 anchor.
- DESIGN "user-declared variation axes left optional while m50 presupposes them" (HIGH) ==
  TESTS "m50 declaration anchors freeze behaviour §6.2 leaves optional" (HIGH). Merged; one
  decision in §6.2(ii) + one m50 anchor rewrite + one §11 parking.

---

## HIGH

### H1 (design) — §8.2 label transport keyed on post-reduction ids no channel produces — APPLIED

**Verified.** `python/graphed/execute.py:36-45` — `CompiledGraph` is a frozen dataclass with
exactly `ir: bytes` and `source_names: tuple[str, ...]`; `compile_ir` (`:54-80`) returns exactly
that, no remap, no id table. I enumerated every `#[pymethods]` fn in `src/lib.rs` (grep `^ *fn `,
`:106-543`): `add_source`, `add_op`, `add_reduction`, `add_external`, `add_exchange`, `add_join`,
`node_count`, `to_dot`, `serialize`, `deserialize`, `nodes`, `outputs`, `reduce`,
`reduce_incremental`, `reduction_report` — none returns a record→reduced mapping. The `remap`
vector is local to `dead_code_elimination` (`src/optimizer/mod.rs:88-116`) and never escapes.
Fusion point confirmed: `execute.py:110-117` evaluates `stage` members inline, so a universe's
chain has no per-op reduced id (consistent with the plan's own §3.3 measurement, 129 stages / 258
nodes at N=128). `Session._provenance` is record-time keyed (`session.py:30`), inheriting the same
problem — §8.2(ii)'s premise fails identically.

**Edit** (§8.2(i)/(ii)): added the measured evidence block and bound a **read-only `graphed-core`
accessor** `record_node_id -> (reduced_node_id, member_index | None)` as an explicit m49
Implementation Target, with the explicit note that §3.1 still holds (read-only over data the
reducer already computes; no NodeKey, no serialize tag, no optimizer arm). Stated the honest
coarser fallback (key on output position, which the frontend already owns per §7.2) if the
accessor is descoped. §8.2(ii) now says the provenance ships re-keyed through the same accessor.

### H2 (design) — §6.4a offsets predicate cannot refuse the embedded-selection case — APPLIED

**Verified by reading the plan's own text** (no code claim to check): the predicate is a
within-record, across-label offsets comparison; the corruption the m51 anchor names as its positive
control (`sel = events[nominal_mask]`, then `select=varied_mask`) is a record-vs-mask row-space
mismatch. With a non-varied embedding, either the record has no per-label members (predicate
vacuous) or all members were masked identically (offsets all equal nominal's) — it passes both
ways. The chained-context case the r11 `graphed.selection(ctx)` bridge creates has the same shape.

**Edit** (§6.4a): replaced the single predicate with **two**, each with its own message —
(1) multiplicity (the offsets rule, unchanged), (2) row-space agreement, bound structurally via
§2.6b lineage (the mask must be `graphed.selection` of the record's own context handle) plus a
runtime row-count equality. m51's entry-check anchor rewritten so each positive control names the
predicate that decides it.

### H3 (design + tests, merged) — §6.2 user-declared axis optional; fill cannot accept one — APPLIED

**Verified.** `graphed-histogram src/graphed_histogram/boost.py:160-161`:
`if len(args) != len(self.axes): raise TypeError(f"this histogram has {len(self.axes)} axes; fill
got {len(args)} arrays")`. A user-constructed variation `StrCategory` therefore rejects the user's
N-array fill outright. The §6.2(i) frontend-declares-at-fill-time rule makes the declared set equal
the inferred set by construction, so "a label not among the declared bins" is unreachable under it.

**Edit** (§6.2(ii)/(iii) + m50 anchor + §11): deleted the "if a user-declared axis is supported at
all" hedge and bound **frontend-declared only in v1**, with the arity measurement as the reason.
Kept the silent-overflow discriminator by re-pointing it: declared bin set == inferred label set,
witnessed by `h.sum(flow=True) == h.sum()`. Deleted the "undeclared label" and "unsorted
user-supplied bin order" m50 anchors; kept cross-fill agreement; added a refusal anchor for a
user-constructed variation axis. Parked user-declared axes in §11. Also added the missing
**"opt-in spelling pinned at m50 freeze"** clause to §6.2's opening (every other new surface in
this plan carries one).

### H4 (design) — §2.3(d) omits Array-consuming module verbs; `Varied` getattr hides it — APPLIED

**Verified.** `python/graphed/__init__.py:8-25` and `__all__` `:27-58` export `apply`,
`compile_ir`, `evaluate_ir`, `aggregate_plan`, `read_columns` alongside `join`/`repartition`.
`Array.node_id`/`session` are plain properties (`array.py:137-143`), not dunders, and
`Array.__getattr__` raises only for leading underscores (`:332-335`). Consumers read them directly:
`execute.py:74` (`ids = [arr.node_id for arr in outputs]`), `aggregate.py:66-72`
(`outputs[0].session`, `o.session is not session`).

**Edit** (§2.3d + §2.2): §2.3d now enumerates the measured public surface with a bound disposition
each (refuse / expand-into-universes), and §2.2 binds `Varied` to reserve `node_id`/`session` as
`AttributeError`s rather than field accesses, with the `compile_ir` failure spelled out. The m48
parity anchor already names "string getitem = field access"; the reserved-name assertion rides in
§2.2's binding text and the §2.3d dispositions.

### H5 (tests) — §6.1d's refusal names a raiser the bound mechanism never reaches — APPLIED

**Verified by measurement**, awkward 2.12.0:
`ak.broadcast_arrays(ak.Array(np.arange(7.0)), ak.Array(np.arange(3.0)+1))` →
`ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7`; the same call
against a jagged 3-row value succeeds (`[3, 3]`). Since §6.1d binds the broadcast as a recorded
graph node UPSTREAM of the fill, that node dies first and `FillEvaluator` is never entered.
`FillEvaluator.__call__` read and confirmed (`boost.py:39-47` `_flat`, `:58-71` the factor loop).

**Edit** (§6.1d + m48 anchor): the refusal is now bound as a **message contract at execution
time** — naming the offending factor (ambient or explicit-by-position) and, when a per-event
factor meets a per-object value, pointing at "pass the value unflattened" — with the seam's
awkward implementation binding to translate awkward's `ValueError`. The literal `FillEvaluator`
naming is gone from both the requirement and the anchor.

### H6 (tests) — m49(i) pinned to a repo that cannot fill a histogram — APPLIED

**Verified.** `graphed pyproject.toml:41-48` — the `dev` extra is
`pytest/pytest-cov/…/boost-histogram>=1.4/hist>=2.7`; no `graphed-histogram` anywhere in the file.
`.github/workflows/ci.yml:34,57,143` all install `-e ".[dev]"`. House pattern confirmed at
`tests/frozen/preserve/m30/test_producer_cross_seam.py:155`
(`gh = pytest.importorskip("graphed_histogram")`). This is r11's own m48 analysis, unapplied to
m49's headline matrix.

**Edit** (m49 anchor (i)): moved the 15-reference matrix + the §5.2b single-read witness to
`graphed-histogram`, flat `tests/frozen/m49` (which after m48's bound dependency edit already
carries the corpus dep and the vendored references), with the "MUST NOT be guarded by
`importorskip`" clause. `tests/frozen/frontend/m49` in `graphed` keeps m49's non-fill anchors,
listed explicitly.

### H7 (tests) — §2.3e's dynamic propagation gate is not buildable over the measured surface — APPLIED

**Verified.** Census run over `python/graphed/awkward/functions.py`: 73 `def`s, **65** public.
Signatures read and confirmed: `apply_correction` `:476` and `onnx_inference` `:513` take a payload
first, not an `Array`; `to_list` `:693`, `head` `:732`, `sample` `:737` are eager; `fields` `:717`,
`type_of` `:722`, `backend_of` `:727` return `list[str]`/`str`; `join` `:18` must refuse;
`zip` `:118`, `concatenate` `:383`, `where` `:400`, `unflatten` `:600`, `linear_fit` `:346` need
typed/extra operands. A behavioural "call each and assert the handle survives" gate over that set
needs per-function fixtures the plan never bound, and a frozen test cannot grow them later.

**Edit** (§2.3e + m48 anchor): split the gates. (c)'s classification gate stays metadata-only over
all 65. The propagation gate enumerates only *broadcast* / *container-traversing* /
*tuple-returning*, takes call arguments from fixtures living in `src` beside the classification
(preserving the self-repairing property), and asserts the exempt set is exactly
{*eager-metadata*, *refusing*} — an exemption by classification, not by silent omission.

---

## MID

### M1 (facts + design, merged) — `graphed.universe(h, label)` = `h[{"variation": label}]` — APPLIED

**Verified by measurement on BOTH versions I ran myself.**
boost_histogram **1.8.0**: `bh.axis.StrCategory([...], name="variation")` →
`TypeError: StrCategory.__init__() got an unexpected keyword argument 'name'`;
`h[{'variation':'jes_up'}]` and `h[{'variation': bh.loc('jes_up')}]` →
`TypeError: list indices must be integers or slices, not str`; `h[{0: 'jes_up'}]` → `IndexError`;
`h[{0: bh.loc('jes_up')}]` → works. After `ax.__dict__['name'] = 'variation'`,
`h.axes.name == ('variation',)`.
boost_histogram **1.7.2** (re-run independently): identical `TypeError`s; positional `bh.loc` works.
Spec codec confirmed: `_spec.py:31-37` `_metadata_of` harvests `axis.__dict__`, `:81-84`
`_restore_metadata` writes it back — so `name` survives the spec round-trip as metadata, but is
not a lookup key.

**Edit** (§6.2(i-bis) + m50 anchor): restated as "that label's slice along the variation axis",
with the measurement, and bound the two implementation halves — write
`axis.__dict__["name"] = "variation"` (the `hist` convention the codec already round-trips) and
resolve the axis POSITION from that name. The m50 anchor is worded over semantics (equality against
a manually sliced reference), not over a subscript expression.

### M2 (design) — §6.1d's broadcast mechanism can only supply the ambient factor — APPLIED

**Verified.** `boost.py:58-71`: `weight = _flat(rest.pop(0))` then
`weight = weight * _flat(rest.pop(0))` — each factor flattened independently, multiplied after.
So an unbroadcast per-event explicit factor length-mismatches in a per-object fill, exactly as the
requirement says — but the r11 mechanism ("the event context supplies ITS AMBIENT WEIGHT … through
one neutral entry point") cannot reach a user-owned `weight=[events.genWeight]`, cannot be spelled
as a gak call inside `graphed-histogram`, and does not exist at all in an all-loose fill.

**Edit** (§6.1d): the seam is now `graphed.broadcast_like(value, factor) -> Array` (spelling pinned
at m48 freeze), owned by `graphed` proper, dispatched to the backend idiom, taking an arbitrary
factor; the fill applies it to the ambient weight and every explicit factor alike. The refusal
message names WHICH factor (see H5).

### M3 (design) — axis mode leaves the reduce/zero spec sourced from `h._spec` — APPLIED

**Verified.** `boost.py:146-150` `self._spec = spec_of(self)` in `__init__`; `:282`
`layout = tuple((label, len(h._fill_nodes), h._spec) for label, h in items)`; `:127-130`
`_GroupZero` builds `zero_of(spec)` from the layout; `:245-255` `Histogram.plan` passes
`_SumFills(self._spec)`/`_ZeroHist(self._spec)`. Under §6.2's fill-time declaration the fill node's
spec carries the variation axis and `h._spec` does not.

**Edit** (§6.1c): bound the layout's third element to the **fill node's** spec (`boost.py:180-212`),
with the disagreement spelled out.

### M4 (design) — §6.4a's entry check is execution-time, not "up front" — APPLIED

**Verified.** `python/graphed/awkward/io.py:111-127` — `_WritePart.__call__` reads the partition,
then `(out,) = evaluate_ir(self.compiled, backend, {self.source_name: chunk})`, then writes one
part; `:206-216` is `to_parquet`; the per-partition task graph is built by
`python/graphed/write.py:32-43`. Offsets are data and do not exist at the API call.

**Edit** (§6.4a + m51 anchor): added a "Where the checks RUN" binding — predicate (2)
(row-space/lineage) is record-time and raises from the `to_parquet` call; predicate (1) (offsets)
is per-partition, raised by `_WritePart` before any buffer is stored, surfacing through the
executor's error path (the same treatment §6.1d already takes). §6.4f additionally names the
single-output unpack (`(out,) = …`, `io.py:122`) as part of the target.

### M5 (design) — no ambient-weight accessor, yet §6.4b expects varied factors to be nameable — APPLIED

**Verified against the plan's own surface list** (§9.1 lists `labels`/`universe`/`nominal`/
`variations`/`selection` + the impact API; `graphed.variations` is bound to report tags/kinds/parsed
values, i.e. metadata, and lands in m50). §2.6a reserves no attribute names, so a factor handed to
`graphed.vary(..., is_weight=True)` is unreachable.

**Edit** (§9.1 + §2.6a + §6.4b + m48 anchors): added **`graphed.weight(ctx)`** (m48, read-only,
`None` when nothing is registered) as the weight-side twin of `graphed.selection`, cross-referenced
from §6.4b, and used it to make the §2.1 stacking anchor frontend-observable (see M11).

### M6 (design) — "the writer applies NONE of them" contradicts the superset row rule — APPLIED

**Verified by reading §6.4a/§6.4b/§6.4d**: two defensible readings (store every row plus masks vs
store superset rows plus masks) producing different files.

**Edit** (§6.4a): re-worded to the intended rule — the level-0 OR applies to the stored ROWS (that
IS the superset), no other supplied mask touches the buffers, and every supplied level, level 0
included, is stored as packed per-label validity masks.

### M7 (design) — only the Array dunder surface is bound — APPLIED

**Verified.** `python/graphed/array.py:374-391` — `filter`, `map`, `reduce`, `repartition`.
`python/graphed/numpy/array.py:92-190` — `sum`, `prod`, `mean`, `std`, `var`, `min`, `max`, `any`,
`all`, `argmin`, `argmax`, `cumsum`, `cumprod`, `reshape`, `ravel`, `squeeze`, `transpose`,
`swapaxes`, `astype`, `clip`, `round`, `take`, … plus tuple `__getitem__` at `:132-136`.

**Edit** (§2.3a + m48 anchor): widened to the Array **public** surface (dunders AND methods),
enumerated dynamically from `type(graphed.nominal(v))` so idiom subclasses are covered, with the
per-class disposition (broadcast; refusing for `repartition`), and the non-vacuity floor extended
to name at least one method.

### M8 (tests) — three of five gak classification classes have no behavioural anchor — APPLIED

**Verified.** Searched all four milestone anchor lists: no mention of `zip`, `unzip`,
`concatenate`, `broadcast_arrays`, `fields` or `type_of`. Corpus fixture uses `ak.with_field`
(`graphed-corpus src/graphed_corpus/analyses/systematics.py:39-45`), never `ak.zip`, so the
matrices cannot reach them. Signatures confirmed: `zip` `:118` (Mapping|Sequence), `unzip` `:687`
(tuple return), `fields` `:717`, `type_of` `:722`.

**Edit** (m48 anchors): added one named representative per unanchored class —
`gak.zip({"pt": varied_pt, "eta": plain})` returns a `Varied`; `gak.unzip(varied_record)` returns a
tuple of `Varied`; `gak.fields`/`gak.type_of` answer on the nominal member.

### M9 (tests) — fill-observable clauses inside `graphed`-assigned m48 anchors — APPLIED

**Verified.** The per-label result mapping is `_GroupReduce`'s `{label: hist}`
(`graphed-histogram src/graphed_histogram/boost.py:100-122`), which does not exist in `graphed`;
§2.1's `old_ambient[L] × factor[L]` had no frontend accessor; the §2.6/§6.1d bullet mixed
pure-frontend and fill-shaped clauses in one undivided list.

**Edit** (m48 partition paragraph): the three straddling anchors are now assigned explicitly —
§1.2's dedup half splits (arena/node-id/one-value stays in `graphed`, the result mapping goes to
`graphed-histogram`); §2.1's stacking assertion reads through `graphed.weight(ctx)` and stays in
`graphed`; the §2.6/§6.1d bullet is split clause-by-clause between the two directories.

### M10 (tests) — §4.3's structural predicate names no extraction mechanism — APPLIED

**Verified.** `python/graphed/session.py:245-252` — `walk(array, *, source, op, external)` takes an
Array plus handlers. `Histogram._fill_nodes` is private (`boost.py:149`). Nothing in the plan said
how to obtain either operand of the node-id predicate.

**Edit** (§4.3 + m48 anchor): bound the mechanism — `reachable(fill_node[label])` per label via
`session.walk`, `fill_node[label]` from the §7.2 map / §6.1c layout, asserting the intersection
with `reachable(selection_mask)` is identical across labels; the repaired impact-set form is named
as an optional public cross-check.

### M11 (tests) — the §2.6c re-indexing anchor asserts length only — APPLIED

**Verified by reading §2.6c and the anchor**: under §2.6c a derived context can carry per-label row
sets, so re-indexing every label by nominal's mask yields right-length, silently mis-weighted
arrays whenever per-label counts coincide. The manually re-indexed reference is already in the test.

**Edit** (m48 anchor): changed to elementwise equality **per label** against the manually
re-indexed reference, with the varied-mask (per-label row sets) case explicitly inside the same
anchor.

### M12 (tests) — the op-level divergence error has no anchor — APPLIED

**Verified by reading §2.3e** ("handles on divergent branches are an error at that op naming both";
"The op-level rule is *early* detection, not the sole raiser") against the m48 anchor list, which
freezes only the fill-level raiser.

**Edit** (m48 anchor): added divergent-lineage detection **AT THE OP** — a binary op over Arrays
from two divergent contexts raises there naming both — with an ancestor-chain positive control.

---

## LOW

### L1 (facts) — "no constant Array from nothing" is false as stated — APPLIED

**Verified.** `python/graphed/numpy/creation.py:31` `zeros`, `:36` `ones`, `:41` `full`, `:48`
`empty`, `:57` `arange`, `:70` `linspace`, all routed through `_source` `:27-28`
(`session.source(name, form=…, data=arr)`); all in `__all__`
(`python/graphed/numpy/__init__.py:578-598`). Single-source binding at
`python/graphed/aggregate.py:57-63,96-101`; `python/graphed/execute.py:104-105` raises
`"evaluate_ir: no data bound for source"`.

**Edit** (§4.1 + m48 corpus anchor + §11): scoped the sentence to "a **partition-aligned** constant
Array with no shape donor", with the eager-Source / one-source-binding mechanism named.

### L2 (facts) — `_GroupReduce.layout` cited at `:198` instead of `:282` — APPLIED

**Verified.** `boost.py:282` is `layout = tuple((label, len(h._fill_nodes), h._spec) …)`;
`:288` `reduce=_GroupReduce(layout)`; `:195-200` is inside `session.record_external(...)`.

**Edit**: `:198` → `:282` in §6.1c and in the Anchors row (which also gained the per-slot-spec
line numbers for M3).

### L3 (facts) — corpus stacking anchor off by one (73-75 vs 74-76) — APPLIED

**Verified.** `graphed-corpus src/graphed_corpus/analyses/systematics.py:74` `sel_jets = good[sel]`,
`:75` `ht = ak.sum(sel_jets.pt, axis=1)`, `:76` `weight = _btag_weight(sel_jets, ...)`;
`_btag_weight` def at `:25`, body through `:36`.

**Edit**: `:73-75` → `:74-76` in §2.1 and in the Anchors row at the appendix (the second Anchors
row already read `:74-76`; both now carry `_btag_weight` at `:25-36`).

### L4 (facts) — `StageError.__eq__`/`__hash__` line ranges off by one — APPLIED

**Verified.** `python/graphed/debug/errors.py:75` `def __eq__`, `:78`
`return self.__dict__ == other.__dict__`, `:80` `def __hash__`, `:81` the tuple.

**Edit**: `:74-77`/`:79-81` → `:75-78`/`:80-81` in the m49 anchor and the Anchors row.

### L5 (facts) — parquet writer-version string contradicts the stated pyarrow version — APPLIED

**Verified by measurement** (awkward 2.12.0 / pyarrow 25.0.1): the only writer-version string in an
`ak.to_parquet` file is `parquet-cpp-arrow version 25.0.1`, and
`ParquetFile(p).metadata.created_by` returns the same. A 25.x writer cannot emit `24.0.0`.

**Edit** (§6.4g + m51 anchor + Anchors row): restated version-agnostically as
`parquet-cpp-arrow version <arrow version>` with the reproducible accessor and my re-measured
value, noting the r11 `24.0.0` came from a different environment. The conclusion (same-process
comparison, never a committed blob) is unchanged and independently sound.

### L6 (facts) — uproot-fork test-file count is 12, not 14 — APPLIED

**Verified.** `ls tests/ | grep '^test_graphed' | wc -l` at `393ecef` → **12**; the two extra
graphed-named files are `graphed_uproot_analysis.py` and `graphed_uproot_report.py`, which are not
`test_graphed_*.py`.

**Edit**: §10 header and the Anchors row now say 12 (+2 shared helper modules).

### L7 (facts) — §2.3e prose names three `Session` construction sites while binding five — APPLIED

**Verified.** `python/graphed/session.py:39` `_array_cls`; call sites at `:140` (`source`, def
`:133`), `:168` (`record_op`, def `:142`), `:183` (`record_exchange`, def `:170`), `:204`
(`record_join`, def `:185`), `:242` (`record_external`, def `:206`) — and no `_array_cls` hit
outside `session.py`.

**Edit** (§2.3e + Anchors row): all five named in the prose with def/return line pairs, and the
consequence of omitting `source`/`record_join` stated.

### L8 (design) — `Varied.apply` collides with the module verb `graphed.apply` — APPLIED

**Verified.** `python/graphed/array.py:397-410` — `def apply(fn, *arrays, name=None)` records an
External `"map"` node; the docstring says "With one array this IS `Array.map` (interns with it)";
exported at `python/graphed/__init__.py:9` and in `__all__`. So the stated criterion ("an
execution-time data callable; the two contracts must not share a name") does disqualify `apply`.

**Edit** (§2.2): recorded the collision knowingly rather than renaming — the two names live on
different objects with no dispatch path, whereas r1's rejected `Varied.map` would have shadowed
`Array.map` on the very surface §2.3a mirrors — and named `Varied.per_label` as the fallback,
with the standard "spelling pinned at m48 freeze" clause. Renaming would churn m48 anchors for a
collision that costs nothing mechanically.

### L9 (design + tests, merged) — m50's `graphed` directory pinned "preservation/docs only" — APPLIED

**Verified.** §10 pins `tests/frozen/preserve/m50` as "preservation/docs only" while m50's anchor
list includes §9.1 `graphed.variations(ctx)` and §6.2(i-bis)'s narrowing-helper behaviour, both
frontend. The tests lens's mechanical check is consistent with what I read: frozen tests already
import across package boundaries.

**Edit** (§10 header): dropped "preservation/docs only"; the directory is now described as hosting
m50's preservation, docs **and frontend-introspection** anchors, with the cross-package precedent
cited.

### L10 (design) — m48's target list omits §7.2 — APPLIED

**Verified by reading §10**: m48 Targets are "§1, §2, §3.2/§3.4 (API only), §4, §6.1, §6.3" while
m48 freezes the §7.2 schema-absence anchor and §6.1a/§6.1c depend on §7.2's map.

**Edit**: added §7.2 to m48's targets with the reason, scoping §7.1/§7.3/§7.4 to m49.

### L11 (design) — "unify to the most-derived context" says nothing about row-count agreement — APPLIED

**Verified by reading §6.1d/§2.6c**: §2.6c re-indexes the ambient weight to the derived row count,
so a value read at an ancestor's row count meets a weight at the derived count, and the only
symptom is the execution-time length check whose message is about the wrong thing.

**Edit** (§6.1d): bound ancestor-context VALUES to be re-indexed to the unified context by the
intervening derivation mask(s), label-aligned per §2.4 — the same operation §2.6c already binds,
applied to values. The refusal message widening is covered by H5.

### L12 (tests) — the m49 arity anchor is not scoped to sibling mode — APPLIED

**Verified by reading §6.1b's prose ("again sibling-mode only") against the bare m49 anchor line.**

**Edit**: copied the §6.1a treatment onto the m49 line — "in SIBLING mode … axis mode's `1 + |S|`
is m50, §6.2; word the anchor so it does not freeze a general rule m50 must contradict".

### L13 (tests) — the `.plan()` refusal may over-freeze the weight-only axis-mode case — APPLIED

**Verified.** `boost.py:88-98` `_SumFills` sums all fills; in m50's axis mode with weight labels
only the arity is `1 + |S|` = one fill node, where the merge hazard does not exist.

**Edit** (m48 anchor): re-worded over the fill-node count — "a `Histogram` carrying more than one
staged fill node with varied labels" — keeping the unvaried positive control.

### L14 (tests) — §5.3's per-label projection-stats surface is binding but unanchored — APPLIED

**Verified by reading §5.3 against m49's anchor list**: the union-growth test and the §3.4
impact-set anchor cover neither the stats.

**Edit** (§5.3 + m49 anchor): folded it into the §5.3 anchor — the stats must report the shifted
label's extra column.

---

## Rejected

None. Every finding was reproduced against the verification roots.

## Deferred (owner-locked tension)

None. No finding's resolution required reversing an owner-locked decision, so no
"OPEN ITEMS (owner)" block was added to the plan header. Two findings touched
owner-adjacent ground and were resolved without reversal:
- L8 (`Varied.apply` naming) — the owner-locked naming decision covers `vary`/`Varied`/label style
  and the module-function introspection surface, not this method name; resolved by recording the
  collision and naming the fallback spelling, not by renaming.
- H3 (§6.2 user-declared axes) — the owner-locked scope is m48–m51 including §6.4; nothing locks
  user-declared axes, which are now explicitly Phase 2.
