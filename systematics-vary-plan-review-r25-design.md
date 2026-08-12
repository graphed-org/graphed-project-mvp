# systematics-vary-plan — review round 17, DESIGN SOUNDNESS lens

- **Lens**: design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections; unhandled interactions; under-specified Implementation Targets; package-boundary
  / factorization violations; milestone-target consistency.
- **Plan revision reviewed**: **r25** (`systematics-vary-plan.md`, 6036 lines, read in full including
  Part I, every PART II section, §10 milestones, §11, §12, the Anchors appendix and the r25/r24
  revision-history entries).
- **Date**: 2026-07-30.
- **Verification roots used** (every code fact below was measured by me in this session, in these
  trees, not taken from the plan):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607`) — including its
    `.venv` for runtime probes.
  - `/private/tmp/claude-501/graphed-exec-check` (`graphed-executors`, `201ea42`),
    `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`),
    `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`),
    `/private/tmp/claude-501/uproot5-graphed` (`393ecef`) — consulted for cross-checks; no finding
    below rests on them alone.
- **Owner-locked decisions** (naming, functional surface, e-form encoding, event-context attachment,
  record-time expansion, m48–m51 scope incl. §6.4, the Phase-2 pull-in) were treated as settled. No
  finding below asks for a different choice; each is an internal-consistency or
  unimplementable-as-stated defect.
- The plan header carries no `OPEN ITEMS (owner)` block (grep: 0 hits), so nothing was suppressed on
  that ground.

Nine findings: seven MID, two LOW. No BLOCKER and no HIGH. The plan is implementable as a whole; the
defects are localized, each has a one- or two-sentence fix, and five of the seven MIDs sit in text
that r24/r25 introduced or last touched — i.e. exactly the new-surface priority this round was asked
to probe (§2.3d's idiom-package sweep, §3.4/§5.3's verb operands, §6.1d's label set, §9.2's varied
bundle).

---

## MID-1 — §6.1d's binding fill-label-set enumeration omits `sample=`, contradicting §6.1b r19, §6.2 and m50's r20 anchor

**Section**: §6.1d (label set) vs §6.1b (r19 `S`/`W`) vs §6.2 (axis arity) vs §10/m50.

**Detail.** §6.1d's binding sentence enumerates three label sources:

> `systematics-vary-plan.md:1846-1847` — "the fill's label set is the §2.4 union of value-borne
> labels, ambient-weight labels, and explicit `weight=[...]` factor labels — **computed on the inputs
> AFTER the lineage step below** …"

`sample=` is not in that union. But §6.1b r19 defines the sibling classes over it:

> `:1707-1708` — "`S` = the labels that require their own SIBLING fill node — those borne by any AXIS
> value **or by a `Varied` `sample=`**"

and §6.2 (`:2083-2086`) repeats it for axis mode, and §10/m50's r20 anchor (`:4412-4425`) bindingly
requires a program whose label is **borne ONLY by a `Varied` `sample=`** to lower as a SIBLING and to
make the axis-mode result equal its sibling decomposition.

Under §6.1d's literal enumeration such a program's fill label set is **empty**: the fill is UNVARIED,
§6.1a gives it a BARE `hist` under a bare slot key, and no sibling fill node is recorded at all — the
exact opposite of what m50 freezes. Two binding sentences give one legal program two mutually
exclusive lowerings and two mutually exclusive frozen result shapes.

This is the same three-item-enumeration defect r25 repaired one paragraph later, in the same section:
r25 added `sample=` to §6.1d's *unification/divergence* enumeration (`:1983-1992`, "the binding
enumeration named only three operands") but did not sweep the *label-set* enumeration 140 lines
above it. The fold-order clause (`:1863`, "`sample=` folds LAST, after the explicit factors … each
fold applying §2.4") rescues the intent for a careful reader, which is why this is MID and not HIGH —
but the label-set sentence is the one an implementer and a test-author work from, and m48's own
four-way fold anchor cannot discriminate the two readings (its axis values are varied, so the union
is non-empty either way). The contradiction therefore survives the m48 freeze and detonates at m50.

**Evidence.** `systematics-vary-plan.md:1846-1847` (three-source union); `:1707-1708` (`S` includes
`sample=`-borne labels); `:2083-2086`; `:4412-4425` (m50 anchor). Measured at
`graphed-histogram@211cbbe`: `Histogram.fill` type-checks `args` and `weights` and appends `sample`
to the same `inputs` list with no check (`src/graphed_histogram/boost.py:160-178`), so nothing
downstream catches the discrepancy either.

**Suggested fix.** In §6.1d change the union to "value-borne labels, ambient-weight labels, explicit
`weight=[...]` factor labels **and `sample=`-borne labels**", matching the fold order already bound
two clauses below. One phrase; no other text moves.

---

## MID-2 — §9.2's varied preservation bundle needs a manifest label channel that does not exist and is bound nowhere

**Section**: §9.2 (+ §10/m50's §9.2 anchor, §9.1's `inspect()` clause).

**Detail.** §9.2 (`:3259-3271`) binds three things for m50: `build_bundle` accepts a `Varied`
`value=`/`weight=`; `reproduce(bundle)` returns `{label: array}`; and "`inspect()` lists the labels
without executing". It then says only "Exact spellings pinned at m50 freeze."

Measured at `graphed-latest@ff7c607`, the durable channel these need is singular and carries no label
slot anywhere:

- `python/graphed/preserve/bundle.py:184-193` — the manifest is
  `{"format_version": …, "analysis": {"ir": …, "outputs": {"value": int, "weight": int|None},
  "histogram": …}, "sources": …, "externals": …, "opaque_nodes": …, "provenance": …, …}`.
  `analysis.outputs` is a two-key record of **record node ids**.
- `:250-252` — `reproduce` ends `return values[out["value"]]` (or the value/weight/spec triple),
  i.e. one output id.
- `:267-288` — `inspect()` renders from `m['environment']`, `m['config']`, `m['analysis']['histogram']`,
  the deserialized IR nodes and the stored sourcemap. **There is no other input.**
- §1.2 keeps labels out of the IR entirely, so the IR nodes cannot supply them.

So `inspect()` listing labels and `reproduce` returning `{label: array}` both require a **new manifest
field** — a label→output-id map — on the project's canonical durable preservation artifact, plus a
decision about `FORMAT_VERSION` (measured `python/graphed/preserve/manifest.py:17` → `FORMAT_VERSION = 1`;
no frozen test asserts it, so a bump is safe, but nothing says whether to bump).

This is precisely the "the channel does not exist" defect class the plan repairs five times elsewhere
and names as such — §2.5's diagnostics channel (r15), §5.3's stats verb (r16), §6.1a's unpacker (r18),
§3.4's impact verb (r24), §8.2(i)'s record→reduced carrier (r25). §9.2 is the one remaining binding
requirement that names a durable output shape and leaves its carrier unbound, and it is the only one
whose carrier is an **on-disk format** rather than an in-process surface.

**Evidence.** `python/graphed/preserve/bundle.py:103-123` (singular `build_bundle` signature),
`:130-193` (manifest construction incl. `"outputs": {"value": …, "weight": …}`), `:206-252`
(`reproduce`), `:267-288` (`inspect`); `python/graphed/preserve/manifest.py:17`; plan `:3259-3271`,
`:4536-4538` (m50's §9.2 anchor).

**Suggested fix.** Add one sentence to §9.2 binding the carrier the way §8.2(i) r25 binds its own:
"the varied bundle's manifest gains an additive per-label output map — `analysis.outputs` extended to
`{label: {"value": id, "weight": id|None}}` (or an additive sibling key), sorted by label so the
canonical bytes stay deterministic; `FORMAT_VERSION` bumps with it; an unvaried bundle keeps today's
singular shape and version. Exact key spelling pinned at m50 freeze." Note the `canonical_bytes`
determinism requirement explicitly — the §6.4e sorted-keys argument applies verbatim.

---

## MID-3 — §2.3d r25's numpy gate: "the same containment floor" is unsatisfiable per-enumeration, and §10/m48's anchor bullet was not swept

**Section**: §2.3d (r25's `graphed.numpy` clause) vs §2.3d's floor clause vs §10/m48.

**Detail.** r25 binds (`:912-930`):

> "the m48 gate runs the identical dynamic enumeration over `graphed.numpy.__all__`, in the same repo
> and the same anchor, **with the same containment floor** (never an exact set)."

The floor it points at is (`:936-946`): "the discovered set is non-empty, is at least the freeze-time
count, **contains every member of the named floor list**, and contains at least one member of each
class in the bound class set above **that the repo's own table can host**". Named floor list at m48 =
`{graphed.compile_ir, graphed.context_of, graphed.broadcast_like}`.

Applied to the numpy enumeration as its own floor, both clauses are **unsatisfiable against a correct
implementation**:

- Measured (`graphed-latest@ff7c607`, its own `.venv`): the same annotation-wide filter over
  `graphed.numpy.__all__` (22 names) discovers exactly
  `apply_gufunc`, `empty_like`, `full_like`, `ones_like`, `project`, `zeros_like` — none of which is
  `compile_ir`/`context_of`/`broadcast_like`, so the named-floor half can never pass.
- r25 classifies five of those *broadcast* and one (`project`) *expanding*. There is no *refusing*,
  no *eager-metadata* and no *accepting* verb in `graphed.numpy.__all__`, so a per-class floor over
  that enumeration can never pass either.

Read the other way — one merged table for both enumerations — the floor is satisfied trivially by the
`graphed.__all__` half and the sentence constrains nothing. So the binding phrase has one reading that
reds a correct implementation and one that is vacuous, with nothing choosing between them. That is the
"a test-author's coin-flip frozen read-only" class the plan closes elsewhere (§6.1a r19, §6.2 i-bis
r17, §6.1d r23).

Compounding it: **§10 contains no reference to the numpy gate at all** (grep over `:3273-4773` for
`graphed.numpy` / `numpy.__all__` → 0 hits). §10/m48's §2.3d bullet (`:3682-3724`) still describes only
"dynamic over `graphed.__all__`" plus the named floor. §10 is declared "the acceptance skeleton the
test-author starts from", and the plan repairs this exact annotation defect four times (§3.4→m49,
§2.5's diagnostic→m49, §6.1c's axis slot→m50, `to_parquet`→m51).

**Evidence.** Plan `:912-930`, `:936-946`, `:3682-3724`; measurement (this session, `graphed-latest`'s
`.venv`): `inspect.isfunction` members of `graphed.numpy.__all__` whose parameter annotations mention
`Array` = `apply_gufunc(fn, signature, *arrays: NumpyArray, output_dtype, name)`,
`empty_like(array: Array)`, `full_like(array: Array, fill_value: float)`, `ones_like(array: Array)`,
`project(array: Array, *, on_fail)`, `zeros_like(array: Array)` — six, confirming r25's own count and
showing the class coverage.

**Suggested fix.** State the scoping explicitly: "the numpy enumeration joins the SAME table and the
SAME floor — the named floor list and the per-class floor are asserted over the UNION of the two
enumerations, never per enumeration (measured, `graphed.numpy.__all__` hosts only *broadcast* and
*expanding*, and none of the named floor members)". Then add one clause to §10/m48's §2.3d bullet
naming the second enumeration and the same union scoping.

---

## MID-4 — §2.3d's "per idiom package" sweep still leaves `graphed.awkward`'s package-level Array-consuming verbs undisposed

**Section**: §2.3d (r25) vs §2.3c's discovery rule.

**Detail.** r25's stated rationale for adding the numpy verbs is (`:912-920`) that a numpy-idiom user
handing a `Varied` to an idiom-package verb "reached NO bound behaviour (loud only by accident,
through §2.2's reserved-name `AttributeError` on `varied.session`, whose message points at the wrong
thing)". That argument holds verbatim for the **awkward** idiom package — the default idiom for the
corpus matrices, §6.4's `to_parquet` and every m48/m49 fill anchor — and its verbs are disposed
nowhere:

- §2.3c's gate is scoped to the *module* `graphed.awkward.functions` (bound explicitly at `:770-776`),
  and §2.3c itself observes (`:762-768`) that the package `__all__` "lists modules, classes and **six
  package-level functions — none of them gak's**".
- §2.3d's dynamic half enumerates `graphed.__all__`; r25 adds `graphed.numpy.__all__`. Neither reaches
  `graphed.awkward.__all__`.

Measured (`graphed-latest@ff7c607`), of those six, two take an `Array` and read `array.session`:

```
project(array: 'Array', *, on_fail: 'str' = 'raise') -> 'Projection'          # awkward/projection.py:105
project_buffers(array: 'Array', *, on_fail: 'str' = 'raise') -> 'BufferProjection'   # :119
```

both routing through `_replay(array, on_fail)`, whose first statement is `session = array.session`
(`python/graphed/awkward/projection.py:65-68`) and which then calls `session.walk(array, …)` (`:92`).
`from_awkward`/`from_parquet`/`read_parquet_partition` take a `Session`/`Partition` (no `Array`), and
`to_parquet(array: Any, …)` is disposed at m51 (§2.3d r18) — so the gap is exactly two verbs, and one
of them (`project`) is the direct awkward twin of the numpy `project` r25 just classified.

The consequence is the one r25 names: `graphed.awkward.project(varied)` dies on `varied.session` with
§2.2's reserved-name `AttributeError`, a message about the wrong thing, on the idiom the whole plan is
written for — and the m48 gate, which now calls itself exhaustive "PER IDIOM PACKAGE", does not
discover it.

**Evidence.** Measured this session: `graphed.awkward.__all__` =
`['AwkwardBackend','AwkwardForm','from_awkward','from_parquet','functions','gak','io','payloads',
'project','project_buffers','read_parquet_partition','shuffle','to_parquet']`; signatures as quoted
above; `python/graphed/awkward/projection.py:65-68,92,105,119`. Plan `:762-776`, `:912-930`.

**Suggested fix.** Extend r25's clause from `graphed.numpy.__all__` to "each idiom package's
`__all__` — `graphed.numpy` and `graphed.awkward`", and give the two awkward verbs their
classification in the same sentence (`project`/`project_buffers` **expand**, matching their numpy
twin — see MID-7 for the semantics that classification needs). Sweep §10/m48's bullet with MID-3's fix.

---

## MID-5 — §3.4's and §5.3's verbs cannot produce their bound `{label: …}` return from the operand type the plan binds

**Section**: §3.4 (r24/r25), §5.3 (r16/r17), §9.1's two entries.

**Detail.** Both new m49 verbs are bound as label-keyed returns over an **unlabelled** operand:

- §3.4 (`:1361-1374`): "a **read-only `graphed` module verb over the per-label output Arrays — the
  `Sequence[Array]` half of `read_columns`' operands and NOT its `source_nid`** … **returning
  `{label: tuple[int, ...]}`**", computing `reachable(label's outputs) − reachable(nominal outputs)`.
  §9.1 repeats it (`:3241-3243`): "over the per-label output Arrays — `read_columns`' `Sequence[Array]`
  operand WITHOUT `source_nid`, r25".
- §5.3 (`:1568-1571`): "a **read-only `graphed` module verb over the same operands as `read_columns`,
  returning `{label: tuple[str, ...] | None}`** — per label, that label's SORTED read set, computed by
  applying `read_columns` … **to each label's outputs**". §9.1 repeats it (`:3245-3247`).

Measured, `read_columns(arrays: Sequence[Array], source_nid: int) -> tuple[str, ...] | None`
(`python/graphed/projection.py:109`). A `Sequence[Array]` carries no label attribution whatsoever —
`Array` is `__slots__ = ("_node_id","_session")` (`python/graphed/array.py:127-128`) — so neither verb
can compute "label's outputs", and neither can key its return by label. Under the DoD's
`mypy --strict`, passing a `Sequence[Varied]` where `Sequence[Array]` is declared is also a type error
(§2.2 makes `Varied` a distinct class, not an `Array` subclass).

The obvious intent is `Sequence[Varied]` (or `Mapping[str, Sequence[Array]]`) — each output handed in
as its container, labels read off it, `graphed.universe(v, L)` per label. But that is exactly what the
r25 edit removed: r25's LOW finding replaced r24's "the same operands as `read_columns`/`graphed.labels`"
with a single concrete type, and picked the element type that cannot work. m49 freezes assertions
through both verbs (`:4264-4284` asserts MEMBERSHIP in the per-label impact value; `:4289-4302`
asserts `stats[jes_up] == stats[nominal] + ("Jet.eta",)`), so the operand type is load-bearing for the
test-author, not decorative.

**Evidence.** Plan `:1361-1374`, `:1568-1577`, `:3241-3249`; measured
`inspect.signature(graphed.read_columns)` → `(arrays: 'Sequence[Array]', source_nid: 'int') -> 'tuple[str, ...] | None'`;
`python/graphed/array.py:127-128`.

**Suggested fix.** In both places change the operand to the container form and say why: "over the
per-label output CONTAINERS — `Sequence[Varied]` (the labelled analogue of `read_columns`' first
operand; a bare `Sequence[Array]` carries no label attribution, `array.py:127-128`), plus
`read_columns`' `source_nid` for §5.3 and not for §3.4". Both verbs then apply
`graphed.universe(v, L)` per label and delegate.

---

## MID-6 — §2.1's construction checks accept a loose container whose members live in different row spaces; §6.1d/`reindex_to` then silently mis-index it

**Section**: §2.1 (construction checks, overload (a)) vs §2.1(b) r19/r20 vs §2.6c vs §6.1d(B).

**Detail.** §2.1's construction checks are (`:519-531`): one Session, `op_form`-compatible forms, one
partitioned-source set, and — r18 — "all members' handles MUST lie on ONE ancestry chain, the
container carries the most-derived one, and divergent handles are a construction-time error". Row
space is **not** checked for overload (a)/(c) members.

But handles on one ancestry chain do **not** imply one row space: §6.1d's link kind (1) (a
mask-derivation link) moves it, and §2.6c makes a read through a derived context sit at that context's
per-label row counts. So `graphed.vary(events.Jet, "jes", up=sel.Jet, down=sel.Jet_dn)` with
`sel = events[mask]` is ACCEPTED — handles `events` and `sel` are on one chain — while its `"nominal"`
member sits at root rows and its varied members at `|sel|` rows. `graphed.context_of` then answers with
the CONTAINER's most-derived handle, `sel` (§2.3e r20, `:976-989`), so at a fill `graphed.reindex_to`
treats the whole container as already in `sel`'s row space and re-indexes nothing; the nominal member
is silently one row space up. Measured, nothing upstream catches it: `Session.record_op` validates only
the backend's `op_form`, never lengths or row spaces (`python/graphed/session.py:142-168`) — the same
measurement §2.1(b) r20 cites for the weight-factor case. The program records cleanly and dies at
execution with a length message about the wrong thing, or — when the counts coincide — produces a
silently wrong histogram: the §2.5 confidently-wrong class.

The plan **notices** this shape but binds no rule. §10/m48's r21 fixture note (`:3771-3782`) pins the
`context_of`-on-a-`Varied` discriminator to a `graphed.vary` IDENTITY link and explains: "the
mask-derived spelling builds a container whose members sit in DIFFERENT row spaces, and freezing it
read-only would pin such a container as CONSTRUCTIBLE for three milestones — **foreclosing any §2.1
construction check of the kind §2.1(b) r20 just added for the analogous weight-factor mis-spelling**."
That is the right instinct about the *anchor*, but the *requirement* was never written: §2.1(b) r19/r20
bind row space and direction for a registered weight **factor** (and its members) only, and overloads
(a)/(c) are left with the handle-chain check alone. So the plan deliberately keeps the anchor free for a
future check, and then does not state the check.

**Evidence.** Plan `:519-531` (§2.1 construction checks), `:441-465` (§2.1(b)'s factor-only row-space
and DIRECTION rules), `:976-989` (`context_of` on a container = the most-derived handle),
`:1934-1937` (`reindex_to` is identity when the value already carries the target's handle),
`:1213-1223` (§2.6c: a read through a derived context is in that context's row space),
`:3771-3782` (m48's fixture note naming the hazard). Measured `python/graphed/session.py:142-168`
(`record_op` performs no length/row-space validation).

**Suggested fix.** Generalize §2.1(b)'s r19/r20 rule to every overload, in §2.1's construction-check
paragraph: "**all members MUST live in ONE row space** — the container's most-derived handle's — an
ancestor-handled member being re-indexed across the intervening links per §6.1d kinds (1)-(3) exactly
as a §2.1(b) factor is, and a member reached across a link that no re-indexing can invert (a
DESCENDANT handle) being a construction-time error naming both contexts and the DIRECTION." m48's
existing `vary`-construction divergence anchor (`:3992-3997`) can carry one extra negative control at
no fixture cost.

---

## MID-7 — §2.3d r25 gives `graphed.numpy.project` two incompatible *expanding* semantics and cites a `None` channel its return type does not have

**Section**: §2.3d (r25's numpy classifications) vs §2.3d's own definition of *expanding* vs §5.3.

**Detail.** r25 binds (`:927-928`):

> "and `project` **expands** (per-label results, `graphed.read_columns`' treatment incl. its
> conservative-`None` union rule, §5.3)"

Those are two different contracts, and the second one has no operand:

- *expanding* is defined (`:799-803`) as "per-label results", and `read_columns`' treatment is
  explicitly the **opposite** of per-label results — §2.3d itself binds `read_columns` to return "the
  union over all labels' members … the union is `None` … else the sorted set union", and §10/m48's
  expanding bullet (`:3739-3742`) freezes exactly that asymmetry per verb ("`apply` returns a
  `Varied`; `read_columns` returns the SINGLE union read set … NOT a per-label mapping"). So
  "per-label results, `read_columns`' treatment" names both halves of a distinction the plan spent r17
  separating.
- Measured, `project` returns a `Projection` (`python/graphed/numpy/projection.py:39`,
  `python/graphed/awkward/projection.py:105`), a frozen dataclass with the single field
  `read_columns: Mapping[str, frozenset[str]]` (`python/graphed/projection.py:34-44`). There is **no
  `None`** anywhere in it: conservative projection is expressed by returning *all* columns
  (`awkward/projection.py:110-113`, `cols = set(key_map.values())` when `conservative`), not by a
  sentinel. So "its conservative-`None` union rule" has nothing to apply to.

Net effect: an implementer cannot tell whether `graphed.numpy.project(varied)` must return
`{label: Projection}` or one merged `Projection`, and the merge rule the sentence cites is
inapplicable. The m48 gate is metadata-only ("asserts a classification EXISTS, not that it is RIGHT",
`:3897-3898`) and §10's per-verb behavioural list does not name `project`, so no frozen test
discriminates — the wrong pick ships silently.

**Evidence.** Plan `:927-928`, `:799-803`, `:3739-3742`; measured
`python/graphed/projection.py:34-44` (`Projection.read_columns: Mapping[str, frozenset[str]]`,
`columns_for`, `total_columns` — no `None`), `python/graphed/awkward/projection.py:105-116`,
`python/graphed/numpy/projection.py:39-56`.

**Suggested fix.** Pick one and drop the cross-reference: "`project`/`project_buffers` **expand** —
per-label results, `{label: Projection}` (NOT `read_columns`' union treatment: `Projection` is
per-SOURCE with no conservative `None` sentinel — conservative projection is expressed as the full
column set, `awkward/projection.py:110-113` — so the §5.3 union rule has no operand here)". Add
`project` to §10/m48's per-verb expanding assertions so the pick is witnessed.

---

## LOW-8 — m49's target line re-adds "§7.2's seam half (β)" after excepting §7.2 to m48, contradicting §7.2 r21/r23 and m48's own target line

**Section**: §10/m49 target line vs §10/m48 target line vs §7.2 (r21/r23).

**Detail.** m49's target line now reads (`:4146-4157`):

> "Targets: §3.3, §3.4 (frozen anchor), §5, **§7 — EXCEPT §7.2, which lands at m48** …, **§8 — EXCEPT
> §8.2(i)'s `variation_labels` FIELD DECLARATION, which lands at m48** …, **plus §2.5's
> shift-after-weight diagnostic** …, **plus §9.1's per-label projection-stats verb … and §7.2's
> `aggregate_plan` seam half (β)** (r20 — …)"

It excepts §7.2 to m48 and then re-adds a piece of §7.2 as an m49 target — carrying the **r20-era**
justification, which §7.2 itself has since withdrawn. §7.2 r23 (`:2861-2867`) binds:

> "**(β)'s return CHANNEL is anchored at m48 WITH (α)** … **while (β)'s per-plan PAYLOAD is anchored at
> m49 alongside §8.2(i)** (r23; the r20 '(β) carries its anchor at m49' predates r21's return-channel
> binding and r22's milestone correction)"

and m48's target line (`:3377-3391`) takes "§7.2 … **including §7.2's r19 `aggregate_plan` SEAM**"
plus §8.2(i)'s field declaration. So the return channel *and* the field are m48; the only m49 residue
is populating `variation_labels`, which m49's `§8` target line already covers. r25 repaired the
"§7 — EXCEPT §7.2" half of this same line as a LOW but left the "plus (β)" clause behind it, so the
DoD's "targets exactly as specified" check still has two answers for the same milestone pair the plan
has corrected three times (r17, r22, r23).

**Evidence.** Plan `:4146-4157`, `:2861-2867`, `:3377-3391`, `:5024-5025` (r25's own repair of the
sibling half).

**Suggested fix.** Replace "and §7.2's `aggregate_plan` seam half (β)" with "and the POPULATION of
§7.2's seam-half-(β) payload (the return CHANNEL and §8.2(i)'s field declaration land at m48, §7.2
r23)" — or delete the clause, since m49's `§8` line already carries it.

---

## LOW-9 — axis mode and sibling mode return different `graphed.labels` ORDER for one program, and nothing binds or disclaims it

**Section**: §6.2(i-bis) vs §2.2 vs §10/m50's equality anchor.

**Detail.** §2.2 (`:568-570`) binds `graphed.labels` order as "nominal first, then insertion order;
inherited labels before new ones under stacking" — which for a sibling-mode `{label: hist}` result is
§6.1d's fold order. §6.2(i-bis) (`:2151-2158`) binds the axis-mode answer to "the axis's bin set
RE-ORDERED to §2.2's rule — `"nominal"` first, then **the remaining bins in axis (lexicographic)
order**", because the stored bin order is lexicographic (§6.2 iii).

For any realistic family these differ: §6.2(iii) itself gives the example
`btag_down < btag_up < jes_down < nominal < pu_up`, whereas the fold order is
axis values → ambient → explicit factors → `sample=`, in registration/argument order. So the SAME
program run in the two modes reports two different `graphed.labels` sequences, while §6.2's opt-in is
presented as an equivalent lowering ("equal to its sibling-fill decomposition", `:2072-2073`, `:4409-4418`).

Nothing binds them equal and nothing disclaims the difference. m50's equality anchor is worded
"bin-for-bin" and per label, so a per-label comparison is safe — but a test-author economically writing
`assert graphed.labels(axis_h) == graphed.labels(sibling_result)` as the equality anchor's label oracle
would go red against a correct implementation, and the plan has no sentence to point at. §6.2(i-bis)
already contains the analogous disclaimer for one narrower case ("§6.2's declaration anchor deliberately
forbids using `graphed.labels(h)` as its oracle"), so the pattern for the fix is in place.

**Evidence.** Plan `:568-570` (§2.2 order), `:2151-2158` (§6.2 i-bis order), `:2214-2219` (§6.2 iii
lexicographic, with the worked ordering example), `:4409-4418` (m50 equality anchor).

**Suggested fix.** One sentence in §6.2(i-bis): "The two modes do NOT agree on label ORDER — sibling
mode reports §6.1d's fold order, axis mode reports nominal-first-then-lexicographic — so m50's equality
anchor compares PER LABEL and MUST NOT use `graphed.labels` equality across modes as its oracle."

---

## Verdict

**Dirty — but only marginally, and none of it structural.** No BLOCKER and no HIGH: PART II is a
coherent, implementable specification and its hardest interactions hold up under probing. I
specifically checked and found **sound**:

- §2.4 label-aligned union vs §2.6c lineage unification, including the two-level `factor[L]` rule (r24)
  against the corpus's central-b-tag-on-JES-jets semantics (`graphed-corpus@49650e4
  src/graphed_corpus/analyses/systematics.py:25-36,60-76`);
- §2.1 stacking vs the context shift form, including the r16 shift-after-weight ordering rule;
- §1.1's e-canonicalization edge cases — exact-decimal normalization at the cap boundary
  (`"1.5e31"` → 32 digits accepted vs the naive 2+31=33), the r22 split-by-CAUSE of the two refusals,
  negative-zero, integer rendering, non-minimal canonical re-rendering, cross-notation numeric-equal,
  and the three-channel independence including the shift form's inner keys — all internally consistent;
- §6.1d ambient broadcast vs §2.4 at a fill mixing loose and contexted inputs, and the link-kind-(3)
  ordering that makes m48's `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` a BARE `hist`;
- §6.2 axis mode vs shift-sibling scalar labels — the `1+|S|` arity, the per-fill variation payload in
  `content_hash((spec, payload))`, the single axis-mode slot and `_GroupZero`'s per-slot spec all
  compose correctly;
- §6.4's structure rule vs jagged object-level migration: the pre-object-cut record keeps offsets equal
  across labels, so the XOR same-shape requirement and the per-level inner masks are consistent, and
  r24/r25's bare-depth-`k` exception is decidable from a record-time FORM property;
- §6.4a's five/six lineage controls under the r23 `vary`-link admission — I re-derived all of them and
  every verdict lands as the plan states;
- §7.3 checkpoint invalidation vs m51 writes (write plans carry no journal), and §5.4's boundary
  refusal vs the write path;
- the numpy-backend exemptions (fills supported, writes refused) — stated and consistent;
- package boundaries: `graphed` proper imports no `boost_histogram` and no awkward; `broadcast_like` is
  a neutral dispatched seam; the §6.4e reader is awkward-idiom; r24's per-idiom `Varied` keeps the 26
  numpy-only names out of `graphed` proper. **No factorization violation found.**
- The §7.2 optimizer-merge collapse hazard does **not** leak into §9.2's preservation path: measured,
  `build_bundle` serializes with `optimize=False` (`python/graphed/preserve/bundle.py:132`;
  `session.serialized_ir(..., optimize=False)` returns `self._store.serialize(outputs=ids)` without
  reduction, `python/graphed/session.py:69-73`), so no third guard is needed there.

The seven MIDs are all local text fixes — two enumeration sweeps (MID-1, MID-4), one carrier binding
(MID-2), one scoping sentence (MID-3), one operand type (MID-5), one generalized construction check
(MID-6), one disambiguated classification (MID-7) — plus two LOW annotations. None touches an
owner-locked decision; none requires re-architecting a milestone. Applying them should produce a
design-clean round.
