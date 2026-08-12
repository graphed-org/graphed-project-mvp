# systematics-vary-plan — closure verification (pass 1)

Verifier: isolated closure-verifier agent, 2026-08-12. Scope: **only** the 18 round-18 severe
findings and the r27 reviser's claimed resolutions
(`systematics-vary-plan-revision-r27-notes.md`). Not a fresh full-document review; no findings
outside the 18 are reported (owner decision).

Target: `systematics-vary-plan.md` @ r27 (working tree, 6437 lines; HEAD r26 = 6250 lines;
`git diff` = 242 insertions / 55 deletions, matching the notes).

Verification roots used (all re-measured in this session, nothing taken from the notes on trust):
`/private/tmp/claude-501/graphed-latest` @ `ff7c607` (its own `.venv`, CPython 3.12, awkward 2.12.0),
`/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`.

## Measurements reproduced in this session

| Probe | Result | Used by finding |
|---|---|---|
| `b = a*2.0; c = a*2.0` on one `Session` | `b.node_id == c.node_id == 1`, `b is c` False, `node_count()==2` | 11 |
| `type(b == c)` / `bool(b == c)` | `graphed.array.Array` / `True` | 11 |
| `Array.__eq__` / `__slots__` / `__bool__` / `__len__` | `array.py:236` / `:128` / absent / absent | 11 |
| `GraphStore::intern` (interning basis) | `src/store.rs:73-88` | 11 |
| `Session.materialize` | `session.py:291` (body to `:301`) | 11 |
| `NodeKey::is_boundary` | `!matches!(self, NodeKey::Op { .. })`, `src/node.rs:102-104` (doc comment `:100-101`) | 1/12 |
| `plan()` in graphed-histogram | `fill_nodes` `boost.py:281`, `layout` `:282`, `aggregate_plan` `:286`; `fill_nodes() -> list[Array]` `:218-219` | 1/12, 2 |
| `read_columns` nested record | `[ev.Jet.pt]` → `('Jet',)`; `[ev.Jet.pt, ev.Jet.eta]` → `('Jet',)` | 13 |
| `read_columns` flat record | `[ev2.Jet_pt]` → `('Jet_pt',)`; `+ Jet_eta` → `('Jet_eta','Jet_pt')` (extra column sorts FIRST) | 13, 14 |
| `reads_source` mechanism / sorted return | `projection.py:131-141` / `:147` `tuple(sorted(needed))` | 13, 14 |
| `sorted([0, ["Jet", 1]])` | `TypeError: '<' not supported between instances of 'list' and 'int'` | 15 |
| `json.dumps({"levels":[0,["Jet",1]]}, sort_keys=True)` | `{"levels": [0, ["Jet", 1]]}` (element order untouched) | 15, 17 |
| `hasattr(graphed.numpy, "to_parquet")` / `"to_parquet" in graphed.numpy.__all__` | `False` / `False` | 4 |
| `graphed.numpy.io.to_parquet` signature | `(array, destination, *, steps_per_file, compute, executor, prefix, column)` — no `select=`, `numpy/io.py:182-191` | 4 |
| `graphed.awkward.io.to_parquet` signature | same + `behavior`, `awkward/io.py:206-216` | 9 |
| `project` / `project_buffers` | `-> Projection` `awkward/projection.py:105` / `-> BufferProjection` `:119`; classes `projection.py:35-38` / `:60-67` | 5 |
| annotation-wide `Array` filter over `graphed.__all__` | `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']` | 6 |
| `FORMAT_VERSION` / `canonical_bytes` / `fingerprint` | `manifest.py:17` / `:20-22` / `:25-27` (docstring `:26` states "SHA-256 of the canonical manifest") | 16 |
| `session.walk` | `def walk(` `:245`, `-> object:` `:252`, `root = array.node_id` `:268`, `return cache[root]` `:288` | 18 |
| `_WritePart.__call__` | `awkward/io.py:111` | 7 |

## Per-finding verdicts

**Resolved: 17 of 18. Not resolved: 1 (finding 6).**

1 + 12 (HIGH, §8.2(i) producer) — **RESOLVED.** `:3271-3283` now binds the per-label record-CONE
walk (`session.walk` from each label's marked output, every reached id through the m49 accessor,
labels UNIONed per `(reduced_node_id, member_index)` key), with the `(output, label)` map re-cast as
cone ROOTS. Every fact re-measured: `plan()` holds the `Array` fill nodes (hence a `Session`),
`boost.py:281,286`; an `External` fill is a stage boundary, `src/node.rs:100-104`. The set-valuedness
argument at `:3277` and (iii)'s op-dispatch lookups are now both served, and §10/m49's population
bullet (`:4665-4668`) pins the shared node UPSTREAM of the label fork so the fixture the recipe
serves is the fixture the anchor freezes. Cost ledgered at §12.4(3) — a legitimate descope.

2 (MID, `Sequence[Varied]` unformable for the primary sink) — **RESOLVED (widening).** All five
sites carry `Sequence[Varied] | Mapping[str, Sequence[Array]]`: §3.4 `:1437`, §5.3 `:1657`, §9.1
`:3416` and `:3422`, §10/m49 `:4534`; §5.3's computation sentence handles both arms (`:1665-1666`).
Nit inside the ledgered item: §9.1 binds the accessor as `dict[str, Array]` (one `Array` per label),
so "the labelled mapping is what the fill-node accessor above returns" (`:3416-3417`) is off by one
container level — a caller wraps as `{L: [a]}`. §12.4(1) explicitly defers "the exact annotation" to
m49 freeze, so this is inside the descope, not a re-opening; the finding's defect (no formable
operand for the sink) is gone.

3 (MID, §2.1 row-space vs §2.6c per-label rows) — **RESOLVED (ordering).** `:544-552` adopts the
suggested ordering verbatim in substance: reduce AS SUPPLIED, then re-index LABEL-ALIGNED per §2.4,
and restates the invariant per label. Consistent with §2.6c (`:1296-1305`) and with §6.1d(B)'s
identity clause as cited. No new verb, no new check.

4 (MID, §6.4f numpy refusal) — **RESOLVED (with a declared partial descope).** `:2863-2872` pins the
entry point (`graphed.numpy.io.to_parquet`; measured, not a package attribute and not in
`graphed.numpy.__all__`) and the trigger (a `Varied` first positional), and bindingly refuses to add
a `select=` keyword (measured signature, `numpy/io.py:182-191`). §10/m51 `:5069-5073` is worded over
exactly that trigger and forbids freezing a `select=` arm. Declining the suggested `select=` arm is a
legitimate smaller contract, not an evasion. Error class/message ledgered at §12.4(2). Consistent
with §2.3d's numpy notes at `:2381-2382` and `:3954`.

5 (LOW, `project_buffers` return type) — **RESOLVED.** §2.3d `:981-984` and §10/m48 `:3947-3949` now
say `{label: Projection}` / `{label: BufferProjection}` respectively, with `projection.py:105,119`
and `:34-44,60-72` cited. Both return types re-measured.

6 (LOW, §2.3d r20's classification ground) — **NOT RESOLVED.** The replacement clause at `:1015-1021`
asserts "Their operands are LABELLED CONTAINERS after r26/r27
(`Sequence[Varied] | Mapping[str, Sequence[Array]]`), **so the annotation-wide filter does NOT
discover them**". The plan defines that filter three pages earlier, in the same subsection, as
`inspect.isfunction` members "any of whose parameter annotations MENTIONS `Array` (**including**
`Sequence[Array]`, **unions** and `*args: Array`)" (`:919-920`). The r27 operand is a union that
literally mentions `Array`, so under the plan's own filter the m49 verbs **would** be discovered when
they land — the new ground is false in the opposite direction from r20's, and the measured evidence
offered (today's eight-name result over `graphed.__all__`) cannot support a claim about verbs that do
not exist yet. The finding's own suggested fix anticipated this: "(If the operand becomes the
labelled mapping per the §3.4/§5.3 finding, state it there instead.)" — the r27 fix to finding 2 made
that conditional live and it was not applied. The revision-history restatement at `:5330-5331`
carries the same false claim. Nothing reds (the floor is a containment floor, as the clause itself
says), but the stated ground is wrong, which is precisely what finding 6 was about. Minimal repair:
say the union DOES mention `Array`, so the filter discovers them one milestone after the freeze
(r20's original prediction is restored by r27's widening), and keep the "nothing reds / containment
floor" half.

7 (LOW, §6.4a stored-mask row space + check ordering) — **RESOLVED.** `:2602-2607` binds every stored
per-label mask (level 0 and every k ≥ 1) to the SUPERSET rows, with the level-≥1 structural predicate
running against the offsets as evaluated and the restriction applied afterwards to mask and buffers
alike. Consistent with §6.4b's "on superset rows" (`:2637-2638`, `:2648`) and §6.4c's reconstruction
contract. Prose nit only: the pre-existing sentence "That is predicate (1)'s comparison at the same
level…" (`:2607-2609`) now sits after the insertion and its antecedent reads as the new restriction
clause rather than the structural predicate.

8 (LOW, m48 `context_of` fixture rationale) — **RESOLVED.** Both ends of the argument now agree:
§10/m48 `:4008-4013` replaces the r21 rationale, and §2.1's mirror sentence `:539-541` was updated in
the same direction. No residual reading in which the mask-derived spelling is "kept unfrozen to
preserve a construction check".

9 (LOW, `to_parquet` accepting disposition) — **RESOLVED.** §2.3d `:878-881` and §10/m51 `:5062-5064`
both read "a `Varied` RECORD and/or a `Varied` `select=`". Matches §6.4's canonical
`to_parquet(events.Jet, select=…)` skim and §6.4b's record rule; measured signature
`awkward/io.py:206-216` unchanged.

10 (LOW, §2.6c vs §2.2 term (b)) — **RESOLVED.** `:1299-1303` now says the collections READ as
`Varied` as an implicit property of the derivation, NOT a shift-form registration, so term (b) does
not count them and the mask's labels enter through term (c) — matching §2.2's own exclusion at
`:617-621` at the definition site.

11 (HIGH, m48 stacking anchor `==`) — **RESOLVED.** `:3800-3810` respells the assertion with
`.node_id` on both sides and records the measurement (`Array.__eq__` → `Array`, no `__bool__`,
`bool(a==b)` True; interning `src/store.rs:73-88`, two independent `a*2.0` share `node_id == 1`),
naming `Session.materialize` (`session.py:291-301`) as the equally acceptable elementwise form. The
class is closed as well as the instance: §2.2 gains the general prose rule at `:660-665`. I grepped
for other prose `Array`-vs-`Array` equalities (`== graphed.`, `graphed.universe(...) ==`,
`== old_ambient`) — none remain. Prose nit: the trailing "— naming the ONE-LEVEL answer …" clause now
attaches after the inserted paragraph.

13 (HIGH, §5.3 `Jet.eta` union-growth) — **RESOLVED.** §5.3 `:1637-1647` withdraws the nested example,
states the granularity with `projection.py:129-141`, and pins the m49 fixture FLAT
(`Jet_pt`/`Jet_eta`/`Muon_pt`); §10/m49 `:4544-4549` carries the same pin where the test-author reads
it. Both measurements reproduced. No stale nested `Jet.eta` assertion survives (remaining hits are
the withdrawal statements and revision history).

14 (MID, sorted vs concatenation) — **RESOLVED.** Both occurrences (§5.3 `:1683-1689`, §10/m49
`:4561-4565`) now use the order-insensitive pair `set(jes_up) - set(nominal) == {"Jet_eta"}` AND
`set(nominal) - set(jes_up) == set()`, mark plain concatenation RED with its reason, and give
`tuple(sorted(...))` as the acceptable concatenation form. Reproduced: on the flat fixture the extra
column sorts FIRST. The second conjunct keeps the assertion discriminating (not a containment test).

15 (MID, §6.4e "SORTED" list) — **RESOLVED.** `:2814-2824` drops the undefined adjective and binds the
total order `(depth, field_path or "")` with both measurements as the reason (`sorted()` TypeError;
`sort_keys=True` never reorders list elements; house serializer `manifest.py:20-22`). §10/m51's
determinism anchor `:5019-5022` is reworded over that order.

16 (MID, `FORMAT_VERSION` bump unwitnessed) — **RESOLVED.** §10/m50 `:4823-4830` adds two assertions
on fixtures the anchor already builds (varied bundle carries the bumped `format_version`, unvaried
control still `1`) with the reason. Facts check out: `FORMAT_VERSION = 1` `manifest.py:17`; the
fingerprint is SHA-256 of the canonical manifest (`:20-27`; the cited `:20-26` span ends on the
docstring stating exactly that, so the citation substantiates the claim).

17 (LOW, m51 levels SET vs LIST) — **RESOLVED.** `:5023-5028` asserts the literally spelled expected
LIST in §6.4e's r27 order — `[0, ["Jet", 1]]` / `[0]`. Cross-checked against the new total order:
`0` → key `(0, "")`, `["Jet", 1]` → key `(1, "Jet")`, so the spelled order is the bound order.

18 (LOW, `session.walk` span) — **RESOLVED.** Both occurrences of the compound claim now cite
`python/graphed/session.py:245-255,288` (§3.4 body `:1455`, r24 history `:5457`). Verified `:288` is
`return cache[root]`. The other `:245-252` citations (`:1532`, `:3717`, `:5266`) support a different
claim ("takes an `Array`, not an id") and are correctly left alone.

## Bottom line

17/18 resolutions verified, each against re-measured evidence at the pinned revisions; no resolution
was found to contradict its surrounding spec text except as noted. One resolution (finding 6) is not
resolved: its replacement justification is falsified by the r27 fix to finding 2 within the same
document, and needs a one-sentence correction (or reversion to r20's prediction) before closure.

---

# systematics-vary-plan — closure verification (pass 2)

Verifier: second isolated closure-verifier agent, 2026-08-12. Scope identical to pass 1: **only**
the 18 round-18 severe findings and the reviser's claimed resolutions
(`systematics-vary-plan-revision-r27-notes.md`, incl. its "Repair pass" section). Nothing outside
the 18 is reported (owner decision). Every measurement below was re-run in THIS session; nothing
was taken on trust from pass 1 or from the reviser's notes.

Target: `systematics-vary-plan.md` working tree, 6444 lines (HEAD `f9934e1` = r26, 6250 lines;
`git diff` = 249 insertions / 55 deletions — 7 lines more than pass 1 saw, exactly the finding-6
repair pass). Roots: `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (its own `.venv`,
CPython 3.12, awkward 2.12.0), `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`.

## Measurements re-run in pass 2

| Probe | Result | Finding |
|---|---|---|
| `b = a*2.0; c = a*2.0` on one `Session` | `b.node_id == c.node_id == 1`, `b is c` False, `node_count() == 2` | 11 |
| `type(b == c)` / `bool(b == c)` / `Array` dunders | `graphed.array.Array` / `True` / no `__bool__`, no `__len__`, `__slots__ = ('_node_id','_session')`; `__eq__` at `array.py:236` | 11 |
| `GraphStore::intern` | `src/store.rs:73-88` (dedups on the interned key) | 11 |
| `Session.materialize` | `session.py:291-301` | 11 |
| `read_columns` nested / flat | `('Jet',)` and `('Jet',)`; `('Jet_pt',)` → `('Jet_eta','Jet_pt')` (extra column sorts FIRST) | 13, 14 |
| `reads_source` / sorted return | `projection.py:129-141` / `:147` `tuple(sorted(needed))` | 13, 14 |
| `sorted([0, ["Jet", 1]])` / `json.dumps(..., sort_keys=True)` | `TypeError: '<' not supported…` / `{"levels": [0, ["Jet", 1]]}` unchanged | 15, 17 |
| `hasattr(graphed.numpy,"to_parquet")` / in `__all__` | `False` / `False`; signature `(array, destination, *, steps_per_file, compute, executor, prefix, column)` — no `select=`, `numpy/io.py:182-191`; 1-D cap `:164-165` | 4 |
| `graphed.awkward.io.to_parquet` | same + `behavior`, `awkward/io.py:206-216` | 9 |
| `project` / `project_buffers` | `-> Projection` `awkward/projection.py:105` / `-> BufferProjection` `:119`; `Projection.read_columns` `projection.py:34-44`, `BufferProjection.read_buffers` `:60-72` | 5 |
| annotation-wide `Array` filter over `graphed.__all__` | `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']` | 6 |
| `NodeKey::is_boundary` | `!matches!(self, NodeKey::Op { .. })`, `src/node.rs:102-104` (doc comment `:100-101`) | 1/12 |
| `plan()` / `fill_nodes()` in graphed-histogram | `plan` `boost.py:256`, `fill_nodes` `:281`, `layout` `:282`, `aggregate_plan(...)` `:286-295`; `fill_nodes() -> list[Array]` `:218-219` | 1/12, 2 |
| `session.walk` | `def walk(` `:245`, `-> object:` `:252`, `root = array.node_id` `:268`, `return cache[root]` `:288`; `inputs_of` traverses `_externals` inputs `:259-262` | 18, 2 |
| `Session.record_op` | validates only `op_form`, `session.py:142-168` | 3 |
| `_WritePart.__call__` | `awkward/io.py:111` | 7 |
| `FORMAT_VERSION` / `canonical_bytes` / `fingerprint` | `= 1` `manifest.py:17` / `:20-22` / `:25-27`, docstring "SHA-256 of the canonical manifest" at `:26` | 16 |

## Per-finding verdicts — 18 of 18 RESOLVED

1 + 12 (HIGH, §8.2(i) producer) — **RESOLVED.** `:3273-3286` replaces "compose the map with the
accessor" with the per-label record-CONE walk (`session.walk` from each label's marked output →
m49 accessor → labels UNIONed per `(reduced_node_id, member_index)` key), the `(output, label)` map
re-cast as cone ROOTS. Facts re-measured: `plan()` holds `Array` fill nodes hence a `Session`
(`boost.py:281,286-295`); an `External` fill is a stage boundary (`src/node.rs:100-104`), so the
"no entry for the node a failure raises at" argument holds; `walk` reaches external inputs
(`session.py:259-262`), so the cone is well-defined. §8.2's set-valuedness paragraph and (iii)'s
op-dispatch lookups are now both served; §10/m49 `:4667-4671` pins the shared node UPSTREAM of the
label fork. Cost descoped to §12.4(3) — a legitimate ledger entry, not an evasion.

2 (MID, unformable `Sequence[Varied]` operand) — **RESOLVED (widening).** Five sites carry
`Sequence[Varied] | Mapping[str, Sequence[Array]]`: §3.4 `:1439`, §5.3 `:1659`, §9.1 `:3417`/`:3423`,
§10/m49 `:4536`; §5.3's computation sentence covers both arms `:1667-1668`. §4.3 does reach
`fill_node[label]` through the §9.1 accessor (`:1537-1540`), so the edit's justification is true.
Residual looseness: §9.1 binds the accessor as `dict[str, Array]`, so "the labelled mapping is what
the fill-node accessor returns" is one container level off (a caller wraps `{L: [a]}`) — the
finding's own suggested fix carried the same looseness, and §12.4(1) explicitly defers the exact
annotation to m49 freeze. The defect (no formable operand for the primary sink) is gone.

3 (MID, §2.1 row space vs §2.6c) — **RESOLVED.** `:544-552` orders the rules exactly as the finding
asked (reduce AS SUPPLIED, then re-index LABEL-ALIGNED per §2.4) and restates the invariant per
label. Consistent with §2.6c (`:1299-1305`) and §6.1d(B). No new verb or check; `record_op`'s
validate-only-`op_form` basis re-measured.

4 (MID, §6.4f numpy refusal) — **RESOLVED (declared partial descope).** `:2864-2873` pins the entry
point `graphed.numpy.io.to_parquet` (measured: not a package attribute, not in `__all__`) and the
trigger (a `Varied` first positional), and bindingly adds NO `select=` keyword (measured signature).
§10/m51 `:5070-5075` is worded over that trigger and forbids freezing a `select=` arm. Consistent
with §2.3d's numpy note at `:3956`. Declining the suggested `select=`-then-refuse arm is the smaller
contract, correctly recorded; message/class ledgered at §12.4(2).

5 (LOW, `project_buffers` return type) — **RESOLVED.** §2.3d `:983-986` and §10/m48 `:3949-3951`
now read `{label: Projection}` / `{label: BufferProjection}` with `projection.py:105,119` and
`:34-44,60-72`; both return annotations and both dataclass fields re-measured.

6 (LOW, §2.3d classification ground) — **RESOLVED by the repair pass** (this is the item pass 1
returned NOT RESOLVED). `:1014-1023` now reads "Their r27 operand
`Sequence[Varied] | Mapping[str, Sequence[Array]]` MENTIONS `Array`, so the annotation-wide filter
DOES discover them one milestone after the m48 freeze", records all three states (r20 / r26 / r27)
and re-labels the eight-name measurement as taken on a repo where neither verb exists yet. This
agrees with the filter's own definition at `:919-922` ("MENTIONS `Array` … including `Sequence[Array]`,
unions and `*args: Array`") and with `:1012-1013` ("a verb whose signature mentions no `Array` … is
out of scope"). The "nothing reds / containment floor / self-repair in `src`" half is retained and is
consistent with `:907`, `:1180`. Revision history `:5333` and the repair-pass note `:5340-5344`
carry the corrected claim; the false wording pass 1 flagged is gone from both.

7 (LOW, stored-mask row space + check ordering) — **RESOLVED.** `:2604-2610` binds every stored
per-label mask (level 0 and each k ≥ 1) to the SUPERSET rows, with the level-≥1 structural predicate
running against the offsets AS EVALUATED and the restriction applied afterwards to mask and buffers
alike — the finding's suggested clause in substance. Consistent with §6.4b's superset-rows wording
and §6.4c's reconstruction contract. Legibility nit carried over from pass 1: the pre-existing
"That is predicate (1)'s comparison at the same level…" now sits after the insertion, so its
antecedent reads loosely; no spec contradiction.

8 (LOW, m48 `context_of` fixture rationale) — **RESOLVED.** §10/m48 `:4010-4015` replaces the r21
rationale (identity link kept, justified by row-space stability + §6.4a(2a) proximity) and §2.1's
mirror sentence `:539-541` was corrected in the same direction. No residual "kept unfrozen to
preserve a construction check" reading survives.

9 (LOW, `to_parquet` accepting disposition) — **RESOLVED.** §2.3d `:878-882` and §10/m51 `:5065-5067`
both read "a `Varied` RECORD and/or a `Varied` `select=`", matching §6.4's canonical
`to_parquet(events.Jet, select=…)` and §2.6b. Measured signature unchanged (`awkward/io.py:206-216`).

10 (LOW, §2.6c vs §2.2 term (b)) — **RESOLVED.** `:1301-1305` states the collections READ as `Varied`
as an implicit property of the derivation, NOT a shift-form registration, so term (b) does not count
them and the mask's labels enter through term (c) — matching §2.2's exclusion at its own definition
site. Resolved where the reader hits it.

11 (HIGH, m48 stacking anchor `==`) — **RESOLVED.** `:3802-3812` respells both sides with `.node_id`
and records the measurement + interning basis, naming `Session.materialize` as the equally acceptable
elementwise form; §2.2 gains the general prose rule at `:658-666`, closing the class. Re-measured:
`Array.__eq__` records (`array.py:236`), no `__bool__`/`__len__`, `bool(b == c)` is `True`, and two
independent `a*2.0` share `node_id == 1` — so the old spelling was vacuous and the new one
discriminates the one-level answer. Legibility nit: the trailing "— naming the ONE-LEVEL answer…"
clause now attaches after a long insertion.

13 (HIGH, §5.3 `Jet.eta` union growth) — **RESOLVED.** §5.3 `:1639-1649` withdraws the nested example,
states the granularity with `projection.py:129-141` and both measurements, and pins the m49 fixture
FLAT (`Jet_pt`/`Jet_eta`/`Muon_pt`); §10/m49 `:4546-4551` repeats the pin where the test-author reads
it. Both measurements reproduced. Remaining `Jet.eta` hits (`:1644`, `:1648`, `:4550`, history) are
withdrawal statements, not live assertions.

14 (MID, sorted vs concatenation) — **RESOLVED.** §5.3 `:1685-1691` and §10/m49 `:4563-4567` use the
order-insensitive pair (`set(jes_up) - set(nominal) == {"Jet_eta"}` AND `set(nominal) - set(jes_up)
== set()`), mark plain concatenation RED with `projection.py:147` and the measured `('Jet_eta',
'Jet_pt')`, and give `tuple(sorted(...))` as the acceptable concatenation form. The second conjunct
preserves discrimination.

15 (MID, §6.4e "SORTED" list) — **RESOLVED.** `:2816-2826` drops the undefined adjective and binds the
total order `(depth, field_path or "")` with both measurements (TypeError; `sort_keys=True` never
reorders list elements; house serializer `manifest.py:20-22`). §10/m51's determinism anchor
`:5021-5024` is reworded over that order.

16 (MID, `FORMAT_VERSION` bump unwitnessed) — **RESOLVED.** §9.2 binds the bump at `:3461`; §10/m50
`:4825-4832` now asserts `format_version == <bumped>` on the varied bundle and `1` on the unvaried
control, on fixtures the anchor already builds, with the fingerprint reason. `FORMAT_VERSION = 1`
(`manifest.py:17`) and the SHA-256-of-canonical-manifest fingerprint (`:25-27`, docstring `:26`)
re-measured; the cited `:20-26` span substantiates the claim.

17 (LOW, m51 levels SET vs LIST) — **RESOLVED.** `:5025-5030` asserts the literally spelled expected
LIST in §6.4e's r27 order (`[0, ["Jet", 1]]` / `[0]`). Cross-checked against the new total order:
`0` → `(0, "")`, `["Jet", 1]` → `(1, "Jet")`, so the spelled order IS the bound order.

18 (LOW, `session.walk` span) — **RESOLVED.** Both occurrences of the compound claim cite
`python/graphed/session.py:245-255,288` (§3.4 `:1457`, r24 history `:5462`); `:288` is
`return cache[root]`, verified. The other `:245-252` citations support a different claim ("takes an
`Array`, not a node id") and are correctly untouched.

## Bottom line (pass 2)

**18/18 resolved.** The one pass-1 dissent (finding 6) is repaired in place and now agrees with the
filter definition eight lines above it, with the revision history corrected as well. No resolution
introduces a false factual claim against the pinned roots — every file:line and every measured
statement in the r27 text was re-run or re-read this session — and no resolution contradicts the
spec text it sits in; two carried-over items (findings 7 and 11) are prose-antecedent legibility
nits inside otherwise correct edits. Three deferrals to §12.4 (two-form operand annotation, numpy
refusal error class, cone-walk cost) are legitimate closure descopes, each attached to a rule that is
itself bound. Closure verified.
