# systematics-vary-plan — r19 revision notes (review round 10, over r18)

Audit trail for the r18 → r19 revision. Three independent r18 reviews (facts / design / tests)
produced 22 findings after NIT exclusion; three cross-lens duplicate pairs merge to **19 unique**
(2 BLOCKER, 6 HIGH, 3 MID, 8 LOW).

**Every finding was re-verified in this session** against the pinned verification roots before any
edit — `/private/tmp/claude-501/graphed-latest@ff7c607`,
`/private/tmp/claude-501/graphed-histogram-latest@211cbbe`,
`/private/tmp/claude-501/graphed-corpus-latest`, each repo's own `.venv`.

**Outcome: 19 applied, 0 rejected, 0 deferred.** No finding's resolution required reversing an
owner-locked decision, so no "OPEN ITEMS (owner)" block was added.

Only two files were edited: `systematics-vary-plan.md` and this notes file.

---

## Merged duplicates

| Merged finding | Lenses |
|---|---|
| `NumpyArray.T` breaks the r18 PROPERTY rule and its m48 gate | facts BLOCKER + tests BLOCKER |
| m49 §8.2(i) image cardinality is 2N+2, not N+1 | facts HIGH + tests HIGH |
| §9.1 `unpack(value)` arity vs §6.1c's per-output MODE | design MID + tests MID |

---

## BLOCKER 1 — §2.2 / §2.3a / m48: the r18 PROPERTY disposition rule is false for `T`

**Verdict: APPLIED.**

**Verified myself.** `graphed-latest@ff7c607`:

```
python/graphed/numpy/array.py:156-157   return self._session.record_op("transpose", [self], params)
python/graphed/numpy/array.py:159-161   @property
                                        def T(self) -> Array:  # numpy parity name
                                            return self.transpose()
python/graphed/numpy/array.py:76-86     shape/dtype/ndim -> self._form_meta(...)
python/graphed/array.py:283-290         _form_meta: answers from the form only when hasattr(form, name),
                                        otherwise records a `field` op
```

Runtime probe (repo `.venv`, `Session(NumpyBackend())`, `gnp.arange(s, 0, 12)`):

```
discovered properties on NumpyArray: ['T', 'dtype', 'ndim', 'node_id', 'session', 'shape']
dtype -> node_count delta 0 (Int64DType)
ndim  -> delta 0 (int)
shape -> delta 0 (tuple)
T     -> delta 1 (NumpyArray)
```

So r18's premise ("every other property … already answered from the form and never recorded") is
false for `T`; the m48 gate's blanket "delta 0" reds a correct `Varied`, and the rule read literally
makes `varied.T` drop every non-nominal universe.

**Edits.** §2.2's rule replaced by a three-class split by MECHANISM: (1) `node_id`/`session` raise;
(2) a FORM-ANSWERED property (measured delta 0 on the plain nominal `Array`) is eager; (3) a
RECORDING property (`T` today) takes its underlying method's §2.3a disposition — *broadcast*. §2.3a's
property enumeration now asserts per name against the measured delta and names **both**
representatives (`varied.dtype`, `varied.T`). m48's parity anchor restated the same way, with the
measurement quoted so a test-author can classify pre-implementation.

## BLOCKER 2 — §6.1a: r18's flat slot-keyed plan value is unscoped and breaks frozen m23

**Verdict: APPLIED.**

**Verified myself.** `graphed-histogram-latest@211cbbe`:

```
src/graphed_histogram/boost.py:108-117  _GroupReduce.__call__ -> out[label] = total, label = OUTPUT name
src/graphed_histogram/boost.py:282      layout = tuple((label, len(h._fill_nodes), h._spec) for label, h in items)
                                        items = [(output_name, Histogram), ...]
src/graphed_histogram/boost.py:262      def plan(...) -> Plan[dict[str, bh.Histogram]]
tests/frozen/m23/test_group_plan.py:74  out["hi"]      :75 out["lo"]
                                   :86  grouped["0"]   :89 grouped["1"]
                                   :99  zero["hi"]
```

All five index `SequentialRunner().run(gh.plan({…})).value` by bare output name. Sibling mode is the
default for every program, so r18's unqualified "the plan's combined value is the FLAT slot-keyed
mapping … `{(output, label) → bh.Histogram}` in sibling mode" re-keys a wholly unvaried group plan
and raises `KeyError` in five already-frozen assertions, against §10's "the frozen m05/m4/m9/m23/m29
artifacts are binding and unchanged" — and changes `plan()`'s declared return type under the DoD's
`mypy --strict`.

**Edits.** §6.1a scopes the slot keying to outputs a variation reaches: an unvaried output keeps its
bare `output_name` key; `(output, label)` for a varied sibling output; `(output, None)` for an
axis-mode output. All three carry a plain `bh.Histogram`, so `_add_groups` stays a homogeneous
key-wise `+`. m48's §6.1a anchor gains a wholly-unvaried positive control naming the m23 file:lines.

## HIGH 3 — m49 §8.2(i): the image cardinality is 2N+2, not N+1

**Verdict: APPLIED.**

**Verified myself.** §3.3 builder replicated against `graphed-latest@ff7c607` (source → D prefix ops
→ per universe {fork, K chain ops, terminating reduction}, all reductions as outputs), reduced store
deserialized and node kinds counted:

```
N=3   -> stages 4   reduced_nodes 8   kinds {'source': 1, 'stage': 4,   'reduction': 3}
N=16  -> stages 17  reduced_nodes 34  kinds {'source': 1, 'stage': 17,  'reduction': 16}
N=128 -> stages 129 reduced_nodes 258 kinds {'source': 1, 'stage': 129, 'reduction': 128}
```

The accessor is bound over EVERY surviving record id, which includes the source and each universe's
reduction — neither a stage — so the image is `2N + 2`, exactly the `reduced_nodes` literal §3.3
itself pins. `len({rid for rid, _ in m.values()}) == N + 1` reds a correct accessor by ~2×. The
companion clause ("reduced id is in the compiled output/stage set") is likewise false for the source.

**Edits.** Clause restated as "exactly `2N + 2` distinct reduced ids, of which exactly `N + 1` are of
kind `stage`", with the measured kind counts quoted; the membership clause widened to "a node id of
the compiled reduced store". Both halves stay non-degenerate — the constant map still fails the
per-universe-distinctness half.

## HIGH 4 — §6.4a(2a): the lineage predicate is not decidable in the direction lineage runs

**Verdict: APPLIED.**

**Verified myself** (an absence finding — read, not probed). Plan §2.6b: "Each returned context links
to its **parent**" — upward only. §9.1's `graphed.selection` runs context→mask. §2.5's weak-reference
registration is scoped to `Varied` containers, not contexts. Nothing in §2.2/§2.6/§9.1 exposes a
child-ward or mask→context traversal, while (2a) requires finding a context `c` *reachable FROM* the
record's context by one mask-derivation link. Absent-operand case (ii) ("the supplied mask derived no
context") is undecidable for the same reason. m51 freezes four controls on the predicate.

**Edits.** (2a) re-expressed over the operand that exists:
`graphed.context_of(select_mask) is graphed.context_of(record)`. Checked against all four m51
controls in the plan text — canonical skim ACCEPT, silent-corruption REFUSE, chained-context REFUSE,
universe/nominal REFUSE — and both absent-operand cases are preserved unchanged (a loose mask carries
no handle by §2.3e's Drop rule, so (ii) still refuses; a handle-free record still short-circuits to
(i)). The r16 admission of `vary` identity links becomes automatic. r17's per-label node-id-equality
rule is withdrawn along with the search it served; m51's re-recorded-mask positive control is
re-worded (its purpose — forbidding `mask is ctx._selection` — is unchanged and still witnessed).
The (2a) opening sentence now points forward to the operative rule so a test-author cannot freeze the
retained rationale.

## HIGH 5 — §2.1(b): no row-space contract on a registered weight factor

**Verdict: APPLIED.**

**Verified myself.**

```
graphed-latest python/graphed/session.py:142-168   record_op validates only backend.op_form;
                                                   no length / row-space check anywhere
graphed-corpus .../analyses/systematics.py:60-76   jets = _apply_jes(events.Jet, …)
                                                   good = jets[jets.pt > 25]
                                                   sel_jets = good[sel]
                                                   weight = _btag_weight(sel_jets, …)
                                     :25-36        _btag_weight = ak.prod(per-jet SF, axis=1)
```

§2.1(b) and §2.6b bind only "a per-event weight factor". §2.6c re-indexes a derived context's
inherited members to `|sel_L|`; a factor computed from a value read at the PARENT sits at the
parent's row count, carries a legal one-ancestry-chain handle (so §2.1's divergence check does not
catch it), and §2.1's stacking product `old_ambient[L] × factor[L]` records cleanly — dying at
execution outside §6.1d's refusal contract, which is scoped to a fill's weight factors and applies
its link-kind re-indexing at the FILL, after the mismatch is interned. §6.4b's r18 precondition
already assumes the invariant this finding says is unbound.

**Edits.** §2.1(b) binds the factor (and every member of a `Varied` factor) to the target context's
row space, with ancestor-handled factors re-indexed per §6.1d link kinds (1)-(3) and divergent
handles falling to the existing construction-time error; states the resulting invariant
(`graphed.weight(ctx)` answers in `ctx`'s row space). m48's stacking anchor gains a positive control
registering a parent-computed factor.

## HIGH 6 — §6.1c / §7.2 / §8.2(i): no seam delivers the compiled artifact where it is needed

**Verdict: APPLIED.**

**Verified myself.**

```
graphed-latest python/graphed/aggregate.py:44-55   @dataclass(frozen=True) class _PartitionReduce
                                                   fields: ir/source_name/backend_factory/reader/
                                                   columns/externals/reduce  (no variation_labels)
graphed-latest python/graphed/aggregate.py:68-108  compiled = compile_ir(session, *outputs)  (:95)
                                                   then _PartitionReduce(...)  (:96-104)
                                                   reduce/combine/empty arrive pre-built
graphed-histogram src/graphed_histogram/boost.py:282,286-291
                                                   layout built BEFORE the aggregate_plan call
```

So §6.1c's index-based layout (a constructor argument of `_GroupReduce`), §7.2's m48 merge refusal
(needs the compiled outputs inside the group-plan builder) and m49's `variation_labels` (a field of
the frozen `_PartitionReduce` keyed on post-reduction ids) all need the compiled artifact at a site
that lacks it. The only alternatives are a second `compile_ir` (doubling the reduction the §3.3
anti-quadratic benchmark bounds), `object.__setattr__` on a frozen dataclass, or a signature change
nothing pins.

**Edits.** §7.2 binds ONE `aggregate_plan` seam (spelling pinned at m48 freeze) with two duties —
(α) expose the compiled output list before the worker closure is finalized, (β) accept per-plan
variation metadata carried as an additive closure field — plus an explicit "`plan()` MUST NOT compile
twice" and a note that a function signature is not one of the schemas m48's §7.2 anchor freezes.
Cross-referenced from §6.1c and named on m48's target line. (I did **not** add it to §9.1: that
section is the read-only introspection surface and a plumbing parameter does not belong there; the
§7.2 binding plus the m48 target-line mention is sufficient for the test-author.)

## HIGH 7 — m48 §7.2 schema-absence anchor is vacuous

**Verdict: APPLIED.**

**Verified myself**, `graphed-latest python/graphed/core/execution.py`:

```
:206-217  @dataclass class Plan        (process, combine, empty, tasks, next_tasks, stop, open_once)
:219-224  @dataclass(frozen=True) class ExecResult   (value, n_partitions, n_combines, stopped)
:335-351  @dataclass(frozen=True) class TaskEvent    (phase, key, worker, t, partition,
                                                      n_entries, bytes_read, error)
:378-384  emit_task -> monitor.on_task(event)   # the instance, no per-event dict
```

All three are dataclasses with class-level field lists, so a varied and an unvaried program yield
instances of the SAME classes and their key sets are equal by construction — including after a field
is added, the only thing the anchor exists to detect. This is exactly the defect r17 repaired for
§6.3 by replacing a placeholder key-absence check with a literal key-set equality.

**Edits.** The m48 anchor now asserts each schema's key set against a LITERALLY SPELLED expected set
(all three spelled out, with the file:lines), states that the varied-vs-unvaried comparison is
vacuous and may only ride along as a sanity assertion, and notes the monitor payload is `TaskEvent`
rather than a dict. §7.2's own sentence about the anchor carries the same qualifier — which also
keeps §6.1a's "adding a `Plan` field is foreclosed by §7.2's anchor" argument true.

## HIGH 8 — m48 anchors specify fill programs that cannot execute

**Verdict: APPLIED.**

**Verified myself.**

```
graphed-histogram src/graphed_histogram/boost.py:39-47  _flat(values) -> 1-D per input
                                              :60-71    axes = [_flat(v) for v in values[:n_axes]]
                                                        h.fill(*axes, weight=..., sample=...)
```

Probe in that repo's `.venv`, boost_histogram 1.8.0:

```
bh.Histogram(Regular(3,0,10), Regular(3,0,10)).fill(np.arange(3.0), np.arange(5.0))
-> ValueError: spans must have compatible lengths
```

`h.fill(events.MET.pt, sel.Jet.pt)` (link kind 1) and `h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)`
(link kind 3) each put a per-event and a per-object value in two AXES. §6.1d's re-indexing fixes the
row COUNT, not the structure, and its broadcast seam is bound only for WEIGHT factors — nothing
broadcasts one axis value against another. Both anchors would red for a reason unrelated to what they
assert.

**Edits.** Both fixtures restated at same granularity throughout the document (4 occurrences of
`h.fill(events.MET.pt, sel.Jet.pt)` → `sel.MET.pt`; 3 of `graphed.nominal(sel).Jet.pt, sel.MET.pt` →
`.MET.pt`). §6.1d gains a binding note stating why (with the measured `ValueError`) and that
mixed-granularity multi-axis fills are NOT scoped in m48–m51; both m48 anchors carry a "MUST NOT be
'improved' to a per-object second axis" clause. The link-kind-(1) anchor still discriminates on row
count alone, and the link-kind-(3) anchor still compares against a manually projected reference.

## MID 9 — §9.1's one-argument `unpack(value)` vs §6.1c's per-output MODE

**Verdict: APPLIED (horn 1 of the finding's two — drop MODE).**

**Verified myself.** `Plan` has no layout accessor and `ExecResult` carries only
`value`/`n_partitions`/`n_combines`/`stopped` (`core/execution.py:206-224`); the layout lives on
`_GroupReduce`, the plan's `process` (`boost.py:106-117,288`), and `plan()` returns the `Plan` and
nothing else (`:256-295`). So a one-argument verb cannot reach the layout. Independently, §6.1c's
MODE is redundant: with BLOCKER 2's scoping the three key forms — bare `output_name`,
`(output, label)`, `(output, None)` — are disjoint and per OUTPUT, and §1.1 makes labels non-empty
strings while a varied sibling output always carries ≥ 2 labels, so the shape is decidable from the
keys even in a mixed plan. An implementation omitting MODE passes m50's mixed-mode anchor verbatim,
i.e. the field has no discriminating witness anywhere in m48–m51.

**Edits.** §6.1c deletes the MODE field and says why; §6.1a and §9.1 keep `unpack(value)` and bind
the SLOT KEY FORM as the discriminator; m50's target line drops the field; m50's mixed-mode anchor is
re-headlined as the mixed-unpacking + per-slot-spec anchor it actually is, and gains a third
(unvaried) output so all three key forms are exercised.

## MID 10 — a varied `sample=` has no lowering class

**Verdict: APPLIED.**

**Verified myself.** `graphed-histogram src/graphed_histogram/boost.py:160-178`: `fill` type-checks
`args` and `weights` but appends `sample` with no `isinstance` guard, and `:198-212` records
`"sampled": sample is not None` — so a sample-borne label is a real recordable program shape, and
r15/r16 made it first-class with m48 freezing a four-way fold in which the varied `sample=` is
ACCEPTED/expanded. §6.1b's `S`/`W` and §6.2's split cover only axis-borne and weight-borne labels; a
sample-only label can not ride the evaluator's weight loop (which re-fills against a FIXED sample
column), so it must lower as a sibling, and both frozen arity formulas were wrong for such a program.

**Edits.** §6.1b defines `S` and `W` by lowering behaviour — `S` = labels needing their own sibling
fill node (borne by any axis value OR by `sample=`), `W` = labels borne only by weight factors — with
the same definitions restated in §6.2, so `1 + |S| + |W|` and `1 + |S|` both stay correct and §6.2's
shift-sibling rule extends verbatim.

## MID 11 — m48's gak floor still freezes the superseded `refusing == {gak.join}`

**Verdict: APPLIED.**

**Verified myself.** §2.3e(3) was rebound in r18 to "`gak.join` IS IN the refusing class and the
refusing COUNT is ≥ the freeze-time count — containment plus a monotone count, never an exact set",
while the m48 anchor bullet still carried r16's "the refusing class is exactly `{gak.join}` at freeze
time". §10 states the anchors are "the acceptance skeleton the test-author starts from", so the stale
spelling re-installs the trap r18 removed. The operand is right: measured against
`graphed-latest@ff7c607`, `inspect.getmembers(graphed.awkward.functions, inspect.isfunction)` filtered
to `__module__ == "graphed.awkward.functions"` and no leading underscore yields 65 public functions,
of which `join` (`functions.py:18`) is the only boundary verb.

**Edits.** m48's parenthetical replaced by §2.3e(3)'s r18 form (containment + monotone count), with
the reason recorded so it is not "corrected" back.

## LOW 12 — `projection.py:146-147` cited for a snippet at `:145-146`

**Verdict: APPLIED.** Verified: `awk` over `graphed-latest python/graphed/projection.py` gives
`145| if conservative or not needed: …` / `146| return None` / `147| return tuple(sorted(needed))`.
Replaced both `projection.py:109-115,146-147` occurrences and both bare `projection.py:146-147`
occurrences with `145-146`. The Anchors-appendix row citing `:147` for `return tuple(sorted(needed))`
is exact and was left alone.

## LOW 13 — `boost.py:205-212` cited for a `record_external` call at `:196-210`

**Verdict: APPLIED.** Verified: `record_external(` opens at `:196` and closes at `:210`; `:205-206` is
the `n_weights` conditional inside the params dict and `:211-212` is `self._fill_nodes.append(node)` /
`self._evaluators[chash] = evaluator`. §4.3's citation corrected to `:196-210` (matching the plan's
own cited cba §histogram §1). Neighbouring citations (`:198-212`, `:166-174,205-206`) verified exact
and left alone.

## LOW 14 — m48's §9.1 target list says "only" and omits the r18 unpack verb

**Verdict: APPLIED.** §9.1 marks `graphed_histogram.unpack` m48 with its spelling pinned at m48
freeze and m48's §6.1a anchor is bindingly worded over it, while the target line's "only" excluded
it. Added to the list with the reason.

## LOW 15 — m48 targets "§2" unqualified while §2.5's diagnostic is bindingly m49

**Verdict: APPLIED.** §2.5 says "and it is an m49 target" (it needs §3.4's cone, which r14 moved to
m49) and r18 added it to m49's target line. m48's line now reads "§2 … except §2.5's
shift-after-weight ordering diagnostic, which is m49's".

## LOW 16 — `unweighted=True`'s interaction with an explicit `weight=[…]` is undefined

**Verdict: APPLIED.** Verified: today's signature is
`fill(self, *args, weight=None, sample=None, threads=None)`
(`graphed-histogram src/graphed_histogram/boost.py:152-158`) — `unweighted` is NEW m48 source with a
frozen m48 anchor naming it bare. Bound: it suppresses the ambient weight AND any explicit
`weight=[…]`, and supplying both in one call is a record-time error naming both (the
§2.5 validation-over-convention shape). m48's anchor now names that answer.

## LOW 17 — the §2.6 sketch's `btag_sf(sel.Jet)` is not the corpus semantics

**Verdict: APPLIED.** Verified in `graphed-corpus-latest src/graphed_corpus/analyses/systematics.py`:
`:60-61` `jets = _apply_jes(events.Jet, …)` / `good = jets[jets.pt > 25]`, `:74-76`
`sel_jets = good[sel]` then `_btag_weight(sel_jets, …)`, `:25-36` `_btag_weight` products a per-jet SF
over `axis=1`. §2.6c binds `sel.Jet` to the UNCUT collection re-indexed by `sel`'s mask, so sub-25 GeV
jets would enter the product and the 15 stored references would be missed. Sketch changed to
`sjets = sel.Jet[sel.Jet.pt > 25]` (object cut and event re-index commute, and it is read THROUGH
`sel`, so it also satisfies the new §2.1(b) row-space rule); a sketch note (iii) and a matching
mid-freeze-discovery note in m48's matrix anchor record why.

## LOW 18 — the r18 digit-count formula is off by one at the cap for a dotted mantissa

**Verdict: APPLIED.** `"1.5e31"` renders as `15` followed by 30 zeros = 32 plain digits — exactly at
the cap and legal — while r18's literal "mantissa digits + exponent" gives 33 and rejects it. Since
m48 freezes the magnitude message as a case DISTINCT from the generic tag-length one, the boundary is
exactly where it matters. §1.1 now states the normalization: mantissa digits after removing the
decimal point and stripping leading zeros, plus the exponent adjusted for where that point sat.

## LOW 19 — m48's §1.2 anchor asserts over a node "token" no public surface exposes

**Verdict: APPLIED.** Verified against `graphed-latest@ff7c607`: `GraphStore.nodes()` yields
`{id, output, inputs, kind, name, params}`, a stage adding `n_members`/`members` (each member with its
own `kind`/`name`/`params`); the public `#[pymethods]` surface is
`add_source/add_op/add_reduction/add_external/add_exchange/add_join/node_count/to_dot/serialize/
deserialize/nodes/outputs/reduce/reduce_incremental/reduction_report` — no token. Anchor re-worded to
`name`/`params` **including a stage's `members`' names and params**, with "or token" dropped (the
byte-identity clause subsumes it) and the house `s._store.nodes()` access pattern named
(`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84,95`).

---

## Rejected

None.

## Deferred (owner)

None. No finding's resolution touched an owner-locked decision: the naming/functional surface, the
e-form encoding, event-context attachment, record-time expansion, the m48–m51 scope including §6.4,
the JER-SF non-monotone contract, and the Phase-2 pull-in are all untouched by r19.
