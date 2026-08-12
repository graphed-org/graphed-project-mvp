# systematics-vary-plan r13 — review round 5, DESIGN SOUNDNESS lens

- **Lens**: design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections; unhandled interactions; under-specified Implementation Targets; package-boundary
  / factorization violations; milestone-boundary consistency.
- **Plan revision reviewed**: r13 (`systematics-vary-plan.md`, 2512 lines, read in full).
- **Date**: 2026-07-30.
- **Verification roots used** (all code facts below were measured in-session against these, never
  against the stale submodules in the workdir):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, ff7c607)
  - `/private/tmp/claude-501/graphed-histogram-latest` (211cbbe) — plus a live `boost_histogram
    1.8.0` / `awkward` / `numpy` interpreter for the runtime probes
  - `/private/tmp/claude-501/graphed-exec-check`, `/private/tmp/claude-501/uproot5-graphed`
    (consulted, no finding rests on them)
- **Owner-locked decisions** were treated as fixed. No finding below asks for a different choice;
  every one is an internal inconsistency, an unbound mechanism, or a measurably false premise in how
  a locked decision is *specified*.

Findings are ordered by severity. Each carries the evidence I personally read or ran.

---

## HIGH-1 — §2.3e binds handle *propagation* but no handle *origination*, so a derived context's reads provably carry its PARENT's handle (§6.1d then applies the wrong ambient weight, silently)

**Section**: §2.3e (with §2.6b, §6.1d).

**Detail.** §2.3e (`:506-546`) binds three things: the carrier (an added `__slots__` slot on the
frontend wrapper), a **merge rule** ("inputs whose handles lie on ONE ancestry chain propagate the
most-derived handle"), and a **drop rule** ("an op that cannot propagate a handle (no contexted
input) yields a context-free result"). It binds the merge at the five `Session` construction sites
and says "the merge rule is implemented ONCE there; gak functions and module verbs inherit it by
construction" (`:528-532`). Nowhere does the plan say how an `Array` acquires its *first* handle, or
what a **context** does when it hands out a read.

That gap is load-bearing, not cosmetic, because of the plan's own measurement: §2.3e states (and I
re-verified the mechanism) that two sibling contexts derived from one root expose collections whose
reads intern to the SAME node id. Measured in `graphed-latest`:

- `Session.record_op` ends `return self._array_cls(self, node_id)` (`python/graphed/session.py:168`)
  — a **fresh wrapper object every call**, so per-context wrappers are available; but its only
  inputs are `inputs: Sequence[Array]`, so under the bound merge rule the handle it can produce is
  the merge of the *input* handles.
- `Session.source(self, name, *, form, data, **params)` (`python/graphed/session.py:133-140`)
  receives **no `Array` and no context at all**, so it has nothing to merge — yet §2.3e names it as
  a site whose omission "drops the handle at every tree read" (`:523-525`). Under the bound rules,
  `source` cannot set a handle; something else must.

Now take the owner-locked mainline (`:648-662`): `events` (root context) → `events2 =
graphed.vary(events, "pu", …, is_weight=True)`. Both contexts wrap the same root record. `events2.Jet`
records a `field` op whose input is the root `Array`; under the bound merge rule the result carries
**the root context's** handle, not `events2`'s. §6.1d then "auto-applies that context's ambient
weight" (`:910-916`) — i.e. the *pre-`vary`* registry — and the pileup universes silently vanish
from the fill. That is precisely the §2.5 confidently-wrong class the whole functional respin exists
to delete, and §2.6c's "a fill from a pre-`vary` context is unaffected by later `vary` calls *by
construction*" is the property that breaks in the wrong direction.

The obvious implementation (the context stamps its own handle on every `Array` it hands out, and on
the root wrapper it holds) is fine — but it is an **override**, which the plan never grants; §2.3e
only says a handle that is *lost* is a bug (`:541-543`), and the merge rule as written would be
violated by an op whose output handle is not derived from its inputs.

**Evidence**: `python/graphed/session.py:133-140` (`source` — no Array/context input), `:142-168`
(`record_op` — merges from `inputs`, returns a fresh wrapper); plan `:506-546`, `:610-614`,
`:910-916`; `grep -n "handle" systematics-vary-plan.md` — no origination/stamping sentence anywhere
(the 20 hits are carrier, merge, drop, fill-unification and prose).

**Suggested fix**: add an origination clause to §2.3e: *a context STAMPS its own handle on every
`Array`/`Varied` it produces (the root wrapper it holds and every read performed through it),
overriding the input-merge result; the merge rule governs only ops whose inputs already carry
handles.* State that two contexts sharing a node id are distinguished purely by which wrapper object
the user reached the value through, and add an m48 anchor: a read from a `vary`-derived context and
the same read from its parent produce the SAME node id but different handles, and a fill from each
yields different label sets.

---

## HIGH-2 — §2.3d's "discovery rule, not this literal list" provably misses four of the ten verbs it disposes (measured first-parameter annotations)

**Section**: §2.3d (`:501-505`) and its m48 anchor (`:1660-1673`).

**Detail.** §2.3d declares: "**Exhaustiveness is kept by a DISCOVERY RULE, not by this literal
list** … the m48 anchor enumerates `graphed.__all__` dynamically, filtered to callables whose FIRST
positional parameter is annotated `Array`, and asserts every discovered verb carries a disposition —
so a verb added later cannot arrive undisposed, and this list is the freeze-time floor rather than
the definition." The m48 anchor repeats it ("so the table cannot silently miss a verb", `:1665-1667`).

Measured against `graphed-latest`, the filter does not select what the paragraph assumes:

| verb (in `graphed.__all__`) | first parameter, as annotated | discovered by the bound rule? |
|---|---|---|
| `join(left: Array, right: Array, …)` `shuffle.py:92` | `Array` | yes |
| `repartition(array: Array, …)` `shuffle.py:68-69` | `Array` | yes |
| `pack_key(array: Array, *, on)` `shuffle.py:84` | `Array` | yes |
| `shuffle_plan(output: Array, …)` `shuffle.py:142-143` | `Array` | yes |
| `join_plan(output: Array, …)` `shuffle.py:208-209` | `Array` | yes |
| `aggregate_plan(*outputs: Array, …)` `aggregate.py:68-69` | `Array` (VAR_POSITIONAL) | only if var-positional counts |
| **`apply(fn: Callable[…, object], *arrays: Array, …)`** `array.py:397` | `Callable[..., object]` | **NO** |
| **`read_columns(arrays: Sequence[Array], source_nid: int)`** `projection.py:109` | `Sequence[Array]` | **NO** |
| **`compile_ir(session: Session, *outputs: Any, …)`** `execute.py:54-55` | `Session` | **NO** |
| **`evaluate_ir(compiled: CompiledGraph \| bytes, …)`** `execute.py:85-86` | `CompiledGraph \| bytes` | **NO** |

The four misses are exactly the four whose disposition carries the safety argument: §2.3d itself
says an undisposed verb is *not harmless* because "`Varied`'s field-access `getattr` (§2.2) turns an
unhandled duck-typed read into a recorded op rather than an error" (`:482-484`), and names
`compile_ir`/`evaluate_ir`/`aggregate_plan` as the ones that "consume `arr.node_id`/`arr.session`
directly" (`:496-499`). The rule also structurally cannot reach the two non-`graphed` members of the
same enumeration — `graphed.awkward.to_parquet` (whose first parameter is annotated `Any`,
`awkward/io.py:206-207`) and `Histogram.fill` — so "EXHAUSTIVE over `graphed`'s public
Array-consuming surface" and the anti-drift claim are both weaker than stated.

**Evidence**: annotations read directly at `python/graphed/array.py:397`,
`python/graphed/projection.py:109`, `python/graphed/execute.py:54-55,85-86`,
`python/graphed/aggregate.py:68-69`, `python/graphed/shuffle.py:68-69,84,92,142-143,208-209`,
`python/graphed/awkward/io.py:206-207`; `__all__` at `python/graphed/__init__.py:27-58`.

**Suggested fix**: replace the annotation filter with one that actually covers the surface — e.g.
*every callable in `graphed.__all__` any of whose parameter annotations mentions `Array` (including
`Sequence[Array]`, unions, and var-positional), plus the named non-`graphed` members
(`graphed.awkward.to_parquet`, `graphed_histogram.Histogram.fill`)* — and give this gate the same
**non-vacuity floor** §2.3a/c carry: the discovered set is non-empty, ≥ the freeze-time count, and
names at least one member of each disposition class (refuse / expand). Without the floor, an
over-narrow filter passes tautologically, which is how this defect would survive the freeze.

---

## HIGH-3 — m48's §2.3d anchor freezes ONE error contract for verbs §2.3d binds to TWO, and freezes §5.4's message in the milestone before §5.4 is a target

**Section**: m48 anchor `:1660-1673` vs §2.3d `:485-499` vs §5.4 `:835-840` vs the m48 gak bullet
`:1709-1711`.

**Detail.** §2.3d binds two distinct refusal contracts:

- `join`, `repartition`, `pack_key`, `shuffle_plan`, `join_plan` — "**refuse** with the §5.4 error"
  (`:486-492`). §5.4's error is "a clear `NotImplementedError` **naming the label and the boundary**"
  (`:835-836`).
- `compile_ir`, `evaluate_ir`, `aggregate_plan` — "**refuse** a `Varied` output with an error
  **naming `graphed.universe`**" (`:495-497`).

The m48 frozen anchor collapses both into one assertion: "every refusing verb (`join`,
`repartition`, `pack_key`, `shuffle_plan`, `join_plan`, `compile_ir`, `evaluate_ir`,
`aggregate_plan`) raises a **`graphed` error naming `graphed.universe`**" (`:1667-1669`). A
test-author starting from the anchor freezes "`graphed.join(varied)` raises a `graphed` error
mentioning `graphed.universe`"; an implementer reading §2.3d raises `NotImplementedError` naming the
label and the boundary — which is not a `graphed` error class and does not mention
`graphed.universe`. Frozen tests are read-only after freeze, so the resolution is a Test Dispute, not
an edit.

Second-order: §5.4 is an **m49** target (`:1810`), and the m48 gak bullet says explicitly "the
*behaviour* of the `refusing` class is an m49 anchor, since §5.4 (the refusal message and its
positive control) is an m49 target" (`:1709-1711`). m48's own §2.3d anchor nonetheless freezes
refusal behaviour for five verbs whose message contract §5.4 owns. Either the message contract for
those five moves into m48, or the anchor must be worded so it does not freeze §5.4's message a
milestone early.

**Evidence**: plan lines above, read verbatim; the two error contracts are textually distinct
(`NotImplementedError` naming label+boundary vs a `graphed` error naming `graphed.universe`).

**Suggested fix**: split the m48 anchor's assertion by class — *the plan/boundary verbs (`join`,
`repartition`, `pack_key`, `shuffle_plan`, `join_plan`) refuse with the §5.4 message shape; the
compile/execute verbs (`compile_ir`, `evaluate_ir`, `aggregate_plan`) refuse with an error naming
`graphed.universe`* — and either promote §5.4's message contract into m48's target list or word the
m48 half over "raises a refusal that names the offending container", leaving the exact §5.4 message
to m49.

---

## HIGH-4 — r13's rescoping of the `.plan()` refusal to sibling mode permits an axis-mode `.plan()` that measurably crashes (`_SumFills`/`_ZeroHist` use the `__init__`-time spec)

**Section**: §6.1c (`:886-908`), the m48 `.plan()` anchor (`:1631-1644`), §6.2(i) (`:1021-1032`).

**Detail.** §6.1c's body still says "`.plan()` on a varied `Histogram` **raises**, pointing at the
group API" (`:889-890`). r13 then re-words the m48 anchor over **sibling mode only** (`:1636-1644`),
justifying it with a measurement of `_SumFills.__call__` — "`total = zero_of(spec); for f in fills:
total = total + f` … plain histogram addition, which over disjoint variation-axis bins merges
nothing". Two problems:

1. **The body and the anchor now disagree** — one says any varied `.plan()` raises, the other says
   only sibling-mode does.
2. **The measurement omits which `spec` `_SumFills` receives, and that is the whole issue.**
   Measured in `graphed-histogram-latest`: `Histogram.plan` passes `_SumFills(self._spec)` and
   `_ZeroHist(self._spec)` (`src/graphed_histogram/boost.py:245-255`), and `self._spec` is fixed in
   `__init__` (`:146-150`) — which is exactly the fact §6.2(i) uses to prove that a plan-time
   variation axis is unimplementable (`:1025-1032`). Under §6.2(i) the frontend declares the
   `"variation"` axis **at fill time**, so the fill nodes' results carry it and `self._spec` does
   not. `_SumFills` therefore starts from `zero_of(<spec without the variation axis>)` and adds a
   histogram that has it.

   Measured, boost_histogram 1.8.0:
   ```
   bh.Histogram(Regular(3,0,1)) + bh.Histogram(Regular(3,0,1), StrCategory(['nominal','jes_up']))
   -> ValueError: axes have different length
   ```

   So an axis-mode `.plan()` — the exact program r13's rewording exists to permit — dies inside the
   reducer. §6.1c's binding repair is scoped to "**the layout's third element** — the per-slot spec"
   of `_GroupReduce` (`:902-908`); it does not reach `_SumFills`/`_ZeroHist`, which take a single
   spec and have no "slot". Nothing in §6.2 binds them either.

**Evidence**: `graphed-histogram-latest/src/graphed_histogram/boost.py:88-98` (`_SumFills`),
`:127-130` (`_GroupZero`), `:245-255` (`Histogram.plan` passing `self._spec`), `:146-150`
(`self._spec = spec_of(self)` in `__init__`); runtime probe above (bh 1.8.0).

**Suggested fix**: pick one and bind it. Either (a) keep the refusal general — an axis-mode
`Histogram` also routes through the group path, so `.plan()` raises for **any** varied histogram and
the r13 rewording is reverted (simplest, and consistent with §6.1c's body); or (b) if axis-mode
`.plan()` is to work, extend §6.1c's spec binding to `Histogram.plan`: *`_SumFills`/`_ZeroHist` take
the spec baked into the staged fill nodes' params, not `self._spec`* — and add an m50 anchor that
an axis-mode `.plan()` result equals the group-path result bin-for-bin.

---

## MID-5 — §6.4a's level-0 predicate parenthetical inverts the lineage direction and would refuse the canonical spelling it binds

**Section**: §6.4a (`:1165-1168`) vs the canonical skim spelling (`:1180-1183`) and the m51 anchor
(`:1981-1987`).

**Detail.** Predicate (2), level 0, reads: "the mask must be the selection deriving directly from the
context the record was read from (**`graphed.selection(ctx)` of the record's own context handle**,
§2.3e)". §9.1 defines `graphed.selection(ctx)` as "the `Varied` mask that derived a context **from
its parent**, `None` for a root context" (`:1462-1464`).

Apply that to the canonical spelling the same section binds: `to_parquet(events.Jet,
select=graphed.selection(sel))` where `sel = events[mask]` (`:1182-1183`). The record's own context
handle is `events` — a **root** context — so `graphed.selection(events)` is `None`, and the check as
parenthesised demands `select=None`, refusing the one call the section exists to enable. The prose
clause before the parenthesis ("the selection deriving directly from the context the record was read
from") and the m51 anchor ("a record whose context is not the one the supplied `select=` mask
**derives from**", `:1981-1983`) both state the correct direction: *the mask's parent context must be
the record's context*.

**Evidence**: plan `:1165-1168`, `:1180-1183`, `:1462-1464`, `:1981-1983` (read verbatim).

**Suggested fix**: delete the parenthetical or invert it — *the supplied level-0 mask MUST be
`graphed.selection(c)` for some context `c` whose PARENT is the record's own context handle;
equivalently `parent_of(mask.origin) is record.context`*. Keep the m51 anchor wording as the
normative statement.

---

## MID-6 — §6.4a's level-0 "runtime row-count equality" is bound as a record-time check, contradicting the section's own argument that data is not available at record time

**Section**: §6.4a (`:1165-1168`, `:1174-1175`, `:1184-1194`).

**Detail.** The level-0 half of predicate (2) is "decidable frontend-side because lineage is a Python
object chain, **plus a runtime row-count equality between the record and that mask**". The "where
each runs" binding then says: "(predicate (2) **level 0 is record-time**; predicate (1) and predicate
(2)'s level-≥1 structural half are execution-time, per partition)" (`:1174-1175`), and "predicate
(2)'s **level-0 lineage** half IS a record-time check and raises from the `to_parquet` call"
(`:1189-1190`).

A row count is data, by the section's own argument three lines earlier: "**Offsets are data.** At the
`to_parquet` call the frontend holds a recorded graph and typetracer forms, not per-label offsets"
(`:1185-1187`). Row counts are exactly as unavailable as offsets. So the level-0 predicate has a
runtime half whose raiser and site are unbound: `:1189` names only the *lineage* half as
record-time, and the execution-time list (`:1190-1192`) names only predicate (1) and the level-≥1
structural half. m51's anchor inherits the ambiguity (`:1981-1987` freezes the level-0 refusal "at
the `to_parquet` call"), so a test-author cannot tell whether the row-count mismatch case is a
record-time or an execution-time raise — and freezing the wrong one is the failure r12 already had
to repair once for the offsets predicate.

**Evidence**: plan `:1165-1168`, `:1174-1175`, `:1184-1194`, `:1981-1987`.

**Suggested fix**: split the level-0 predicate explicitly into **(2a) lineage — record-time, raised
from the `to_parquet` call** and **(2b) row-count equality — execution-time, per partition, raised
by `_WritePart` before any buffer is stored**, and word the m51 anchor over both halves separately
(the "do NOT freeze a record-time raise for any offsets-shaped predicate" instruction at `:1193-1194`
should extend to the row-count half).

---

## MID-7 — §6.4c's XOR/packbits representation has no bound computation site, and the reading §6.4f invites is measurably not expressible in the IR

**Section**: §6.4c (`:1216-1226`) vs §6.4f (`:1271-1277`).

**Detail.** §6.4c binds the default representation as "same-dtype **XOR bit-delta** vs nominal for
value columns … **`packbits`** for masks stored as nominal + XOR-vs-nominal diffs". §6.4f binds the
seam as "appended columns are **extra marked outputs of the SAME `compile_ir`** (variadic by design),
so the M4 optimizer shares the pass with the primary expression — appended between the evaluate and
write steps of `_WritePart.__call__`". Those two clauses admit two readings, and one of them is
measurably impossible:

- If the *delta* columns are the extra marked outputs, the XOR must be a recorded graph op. Measured:
  `Array.__xor__` exists (`python/graphed/array.py:257`) but **bitwise XOR on float dtypes is a
  `TypeError`** in both backends — `numpy`: `ufunc 'bitwise_xor' not supported for the input types`;
  `awkward 2.12`: same message via the ufunc path. A bit-preserving reinterpretation would need a
  `view`-style verb, and **gak has none**: enumerating every `^def ` in
  `python/graphed/awkward/functions.py` (73 defs) shows `values_astype` (`:673`) — a *value cast*,
  measured `values_astype([1.5,2.5],'int32') -> [1,2]`, not a bit view — and no `packbits`, no
  `view`, no `frombuffer`. So neither named representation is IR-expressible for the float columns
  that are the whole point.
- If the extra marked outputs are the per-label **values** and the XOR/packbits happen in
  `_WritePart` after `evaluate_ir` (numpy `.view(uintN)` — measured to work:
  `a.view(np.uint32) ^ b.view(np.uint32)`), everything is fine — but then §6.4f's sentence is false
  as written for delta columns, and the projection/read-list widening it binds
  (`_evaluation_columns`) has to cover per-label values, not deltas.

An m51 implementer taking §6.4f literally spends the iteration discovering the TypeError.

**Evidence**: `python/graphed/array.py:257` (`__xor__`); measured (awkward 2.12.0 / numpy):
`float32 ^ float32 -> TypeError: ufunc 'bitwise_xor' not supported…` for both `np.ndarray` and
`ak.Array`; `ak.values_astype(...,'int32')` on `[1.5,2.5]` → `[1,2]`; `grep -nE "^def "
python/graphed/awkward/functions.py` — 73 defs, no `view`/`packbits`/`frombuffer`.

**Suggested fix**: bind the site. E.g. *the per-label VALUES (and per-label masks) are the extra
marked outputs of the same `compile_ir`; the XOR bit-delta and `packbits` are computed in
`_WritePart` on the evaluated buffers (`ndarray.view(uintN)`), after `evaluate_ir` and before the
write* — and add one sentence to §6.4c naming that site, since §6.4c is where the representation is
bound. Note in §11 that an in-IR bit-view verb is not scoped.

---

## MID-8 — §6.4e's reader is spelled in the neutral namespace while §6.4a binds the writer as awkward-idiom; `graphed` proper has no parquet/awkward runtime dependency

**Section**: §6.4e (`:1268-1270`) vs §6.4a (`:1109-1114`) / §6.4f (`:1280-1282`).

**Detail.** §6.4a goes out of its way to bind the writer as the **awkward-idiom** verb: "`to_parquet`
is exported only from `graphed.awkward` … the numpy idiom having its own 1-D-capped implementation …
§6.4f's 'numpy backend EXEMPT' therefore means *the numpy-idiom function refuses*, not that a new
neutral dispatcher is introduced" (`:1109-1114`). §6.4e then names the reverse-direction surface as
"**`graphed.read_varied(path)`**-shaped" — the neutral top-level namespace.

Measured: `graphed`'s runtime dependencies are `["executing>=2.0", "cloudpickle"]`
(`pyproject.toml:27`); awkward and pyarrow are optional extras (`:29-46`). Both parquet entry points
today live in the awkward idiom: `from_parquet`/`to_parquet` are exported from
`python/graphed/awkward/__init__.py:14,30`. A `graphed.read_varied` returning `{label: awkward
array}` would put pyarrow+awkward behind the neutral namespace — the factorization rule §6.4a just
enforced for the writer, and the root `CLAUDE.md` rule that the `graphed` frontend stays
backend-agnostic.

**Evidence**: `graphed-latest/pyproject.toml:27,29-46`; `python/graphed/awkward/__init__.py:14,30`;
`python/graphed/awkward/io.py:206-216`; plan `:1109-1114`, `:1268-1270`.

**Suggested fix**: respell as `graphed.awkward.read_varied(path)` (freeze-time spelling), with the
ROOT-side equivalent in the uproot fork, and add the numpy-idiom refusal to §6.4f's exemption
sentence so read and write are symmetric.

---

## MID-9 — §6.1a/§6.2(i-bis) put `bh.Histogram` knowledge (and the `bh.loc` spelling) inside `graphed` proper, which has no runtime histogram dependency

**Section**: §6.1a (`:874-878`), §6.2(i-bis) (`:1036-1067`), §2.2 (`:384-399`).

**Detail.** The narrowing helper is bound as `graphed.labels` / `graphed.universe` — module functions
of `graphed` — and §6.2(i-bis) requires them to be "uniform over all THREE shapes (bare-unvaried,
`{label: hist}`, bare-axis-mode)", where the third shape is a bare `bh.Histogram`: "`graphed.labels(h)`
= the variation axis's bin set", "`graphed.universe(h, label)` = that label's slice along the
variation axis", resolved by reading `axis.__dict__["name"]` and slicing positionally with "**the
only working form … `h[{axis_index: bh.loc(label)}]`**" (`:1051`).

Measured, `graphed`'s runtime deps are `["executing>=2.0", "cloudpickle"]` (`pyproject.toml:27`);
`boost-histogram` appears only in the `dev` extra (`:46`) — a fact the plan itself relies on twice
for its m48/m49 fixture analysis (`:1567-1573`, `:1819-1826`). Constructing `bh.loc(label)` requires
importing `boost_histogram` at runtime inside `graphed`. Detection of "is this a histogram?" is
duck-typable (`.axes`), and the slice can be done with a plain integer bin index
(`axis.index(label)`), so the requirement is satisfiable without the dependency — but the plan binds
the `bh.loc` spelling and says nothing about the import contract, and mypy-strict on `src` (DoD)
makes an unguarded optional import a visible cost.

**Evidence**: `graphed-latest/pyproject.toml:27,42-46`; plan `:874-878`, `:1036-1067`, and its own
citations of the same dependency fact at `:1567-1573`.

**Suggested fix**: bind the mechanism as *duck-typed detection (an object exposing `.axes`) plus a
positional integer bin index derived from `axis.__dict__["name"]` and `axis.index(label)` — no
`boost_histogram` import in `graphed` proper*, and note that the m50 anchor's oracle is a manually
sliced reference (which it already is, `:1927-1932`), so nothing downstream depends on the `bh.loc`
spelling.

---

## MID-10 — §2.2's "SUPERSET of any §6.1d fill's label set" is false for two expressible programs

**Section**: §2.2 (`:392-399`) vs §6.1d (`:913-916`) and §2.1(a) (`:347-349`).

**Detail.** r13 binds `graphed.labels(ctx)` as the §2.4-ordered union of (a) ambient-weight labels,
(b) varied-collection labels, (c) the derivation mask's labels, and justifies it as "**by
construction the SUPERSET of any §6.1d fill's label set from that context**". §6.1d defines the
fill's label set as the union of **value-borne labels**, **ambient-weight labels**, and **explicit
`weight=[...]` factor labels** (`:913-916`). Two expressible programs break the superset claim:

1. An explicit loose factor: `h.fill(sel.Jet.pt, weight=[loose_varied])` where `loose_varied` came
   from `graphed.vary(some_array, "lumi", up=…, down=…)` (overload (a), which the plan keeps public,
   `:686-687`). `lumi_*` is in the fill's label set and in no clause of §2.2's union.
2. A loose `vary` applied to a value read from the context: `jets2 = graphed.vary(sel.Jet, "jer",
   up=…, down=…)` then `h.fill(jets2.pt)`. `jer_*` is value-borne, carried by an object whose context
   handle is `sel`, and again in no clause of the union.

The union rule itself is fine and is what the m48 anchor freezes (`:1777-1780`); the *superset*
sentence is a stated invariant that a test-author could reasonably freeze as a property
(`set(labels(fill_result)) <= set(labels(ctx))`) and that a correct implementation then fails.

**Evidence**: plan `:392-399`, `:686-687`, `:347-349`, `:913-916` (read verbatim); no code needed.

**Suggested fix**: weaken the sentence to what is true — *the union of the CONTEXT-borne label
sources; a fill may additionally carry labels from loose `Varied` values or explicit `weight=[…]`
factors that no context knows about* — and, if a superset property is wanted, state it over
context-only fills.

---

## MID-11 — `graphed.universe`/`graphed.nominal` on a CONTEXT have no bound return type or lineage relationship, and §6.1d cannot classify the result

**Section**: §2.2 (`:387-399`), §6.1d (`:924-932`), m48 anchor (`:1785-1786`).

**Detail.** §2.2 binds `graphed.labels`/`nominal`/`universe` to accept "a `Varied` OR an event
context", and r13 adds "`graphed.universe(ctx, label)` returns **that label's universe of the
context** (its collections and ambient weight taken at `label`…)". What that *is* — a new context
object? the same context with collapsed collections? — is not bound, and neither is its position in
the lineage chain. That matters because §6.1d's unification is defined over lineage: "inputs whose
contexts sit on one ancestry chain unify to the **most-derived** context … Contexts on **divergent
branches are a hard error**" (`:924-932`). If `graphed.nominal(sel)` returns a NEW context object,
then `h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)` mixes two handles whose ancestry relationship
is undefined — the fill either unifies them (on what rule?) or raises the divergence error on a
program that is obviously legitimate. m48 freezes "§2.2 `graphed.universe`/`labels`/`nominal` on both
`Varied` and contexts" (`:1785-1786`) without saying what the context-valued answers are, so the
test-author must invent the semantics.

**Evidence**: plan `:387-399`, `:924-932`, `:1785-1786`.

**Suggested fix**: bind it in §2.2 — e.g. *on a context, `universe`/`nominal` return a context that
is a CHILD of the argument in the lineage chain (so §6.1d unification treats it as more-derived and
never diverges), carrying that label's collections and ambient weight; its own
`graphed.selection(...)` is the argument's selection at that label* — and extend the m48 anchor to
assert the ancestry relationship (a fill mixing `graphed.nominal(sel)`-derived and `sel`-derived
values unifies silently).

---

## LOW-12 — §10's m49 paragraph puts the §3.3 benchmark in `tests/frozen/frontend/m49`, contradicting §10's own pin and §3.3

**Section**: §10 header (`:1494-1496`), §3.3 (`:704-706`), §10 m49(i) (`:1829-1830`).

**Detail.** §10's header pins "**`tests/frozen/frontend/m48`, `tests/frozen/frontend/m49`,
`tests/frozen/preserve/m50`, `tests/frozen/awkward/m51`**, plus the §3.3 benchmark in
`tests/frozen/core/m49`", and §3.3 says "a new frozen benchmark (`tests/frozen/core/m49/…`)". The
m49 paragraph then says "`tests/frozen/frontend/m49` in `graphed` keeps m49's NON-fill anchors
(§5.2a arena delta, §5.2c stage shape, §3.4 impact sets, §5.3 projection, §5.4 refusal, **§3.3
benchmark**)". The unique-basename binding r13 adds (`:1499-1508`) is written for `core/m49`
specifically, so putting the benchmark in `frontend/m49` also drops the collision guard it was
written for (`frontend` is in `SPLIT_PKGS`, `core` is not).

**Suggested fix**: strike "§3.3 benchmark" from the `frontend/m49` list.

---

## LOW-13 — §2.6d's "data fills nominal-only is structural, not a convention" over-claims: overload (a) on a value read from a data context is not refused

**Section**: §2.6d (`:638-644`) vs §2.1(a) (`:347-349`), §2.3b (`:449-455`).

**Detail.** §2.6d refuses both *context* forms on a data context and concludes: "'Data fills
nominal-only' is therefore **structural, not a convention**." But the loose primitive stays public
(`:686-687`), and nothing refuses `graphed.vary(data_events.Jet, "jes", up=…, down=…)` — the result
is an ordinary `Varied`, §2.3b lets it index plain Arrays, and §6.1d's union puts its labels in the
fill. So the property is structural only against the context API. Since the survey's universal
convention ("data special-cased: no shifts, no variation axis") is the thing being made structural,
the gap is worth naming rather than leaving a reader to assume the stronger guarantee.

**Suggested fix**: scope the sentence ("structural **for every context-borne registration**") or
extend the guard: a `Varied` whose members carry a data context's handle is refused at the fill.

---

## LOW-14 — §6.1d's "loose inputs adopt the unified context" has no re-indexing path, so the bound refusal message misdiagnoses the common failure

**Section**: §6.1d (`:924-932`, `:938-939`, `:986-992`).

**Detail.** §6.1d binds re-indexing for **ancestor-context values** ("every ancestor-context VALUE is
re-indexed to the unified context by the intervening derivation mask(s)"), and separately says
"Context-free (loose) inputs alongside contexted ones **adopt** the unified context". A loose value
has no handle, so no intervening mask is known and no re-indexing is possible — but it may well sit
in the root row space (e.g. an array read from the source outside the context API) while the unified
context's ambient weight is at `|sel|` rows. The result is the bound execution-time refusal, whose
message contract names "the OFFENDING FACTOR — the ambient weight or the explicit `weight=[…]` entry
by position — and … pointing at 'pass the value unflattened'" (`:986-992`): both diagnoses are wrong
for this case, where the offender is a loose *value* in the wrong row space.

**Suggested fix**: add a clause — *a loose input adopts the unified context only for label alignment;
its row space is not adjusted, and a length mismatch traceable to a loose value reports the VALUE, not
the weight factor* — or refuse loose values at a fill whose unified context is not the root.

---

## LOW-15 — m48's split says `graphed` takes §1.2 "except its dedup half", then assigns half of the dedup half to `graphed`

**Section**: m48 split (`:1544-1546`) vs the straddling-anchor assignment (`:1554-1557`).

**Detail.** The repo partition says `graphed`/`tests/frozen/frontend/m48` takes "§1.2
label-out-of-identity **except its dedup half**"; four lines later, "(1) §1.2's *dedup* half … **its
first half (arena Δ = 0, same node id, `compile_ir` returning one value) stays in `graphed`** and the
result-mapping half goes to `graphed-histogram`". Both statements are binding for a test-author
deciding where to write the file.

**Suggested fix**: reword the first as "except the **result-mapping** half of its dedup clause".

---

## Verdict

**DIRTY.** Four HIGH findings, seven MID, four LOW; **no BLOCKER** — every defect has a local repair
that leaves the owner-locked decisions intact, and none makes a milestone unimplementable on its own.

The plan's older machinery (§1.1 canonicalization, §2.4 label-aligned union, §3.x, §4.x, §5.x, §7.x,
§8.2's three-part transport) held up under this pass: I probed the e-canonicalization edge cases
(exact-decimal unification across `"2"`/`"2.0"`/`"2e0"`/`"20e-1"`, the never-bare-`e` argument for
fractional values, negative zero, the integer-magnitude-vs-32-char interaction, cross-notation
p-form rejection) and found the grammar internally closed; §2.4's union order, §2.6c's per-label
re-indexing and §6.1d's three-way fold order compose correctly on the corpus b-tag-on-JES case
(`old_ambient[jes_up] × central_SF(jes_up jets)` falls out of label alignment as claimed); §6.2's
axis-mode arity `1 + |S|`, the fill-time declaration argument, and §6.1c's indices-based layout are
consistent with each other and with the measured `_GroupReduce` slicing; §5.4/§6.4/§7.3 do not
collide (write plans build no boundary); and no binding requirement puts awkward into core or a
backend idiom into a neutral verb — except MID-8 and MID-9, which are the two places the r6 neutral-
verb discipline slipped.

The concentration of findings is exactly where the task predicted the review debt would be: the
newest surfaces. HIGH-1 (§2.3e origination), HIGH-2 (§2.3d discovery rule), HIGH-4 (§6.1c/§6.2
`.plan()`) and MID-5/6/7 (§6.4a/c/f) are all r10-or-later material. HIGH-1 and HIGH-4 are the two I
would fix first: the first silently produces wrong physics under the plan's own mainline idiom, the
second makes an m50 program crash inside the reducer.
