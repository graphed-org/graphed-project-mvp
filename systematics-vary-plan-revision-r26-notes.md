# Plan revision r26 — audit trail (review round 17, reviews of r25)

Reviser: isolated agent, fresh context. Inputs: the three r25 reviews (facts / design / tests),
18 findings after NIT exclusion. Verification roots used for every code fact:
`/private/tmp/claude-501/graphed-latest` (`ff7c607`), `/private/tmp/claude-501/graphed-histogram-latest`
(`211cbbe`). **Verdict summary: 17 unique findings (the two numpy-gate findings merge into one
sweep), ALL confirmed and applied. Nothing rejected, nothing deferred** — no finding's resolution
touched an owner-locked decision, so no `OPEN ITEMS (owner)` block was opened.

---

## HIGH

### H1 — tests — §8.2(i)/§10-m49: `variation_labels` has no bound PRODUCER — **APPLIED**

*Verified myself.* Plan `:3044-3114` declares the field and `:2794` binds §7.2's (β) as the hook's
RETURN value; `:2887-2890` puts the label→node ownership in `graphed-histogram`'s `plan()`;
`:803-807` makes `compile_ir`/`aggregate_plan` REFUSE a `Varied` output; §10/m49 places the anchor in
`graphed`'s `tests/frozen/frontend/m49` as "a `compile_ir`-shaped program". Grepped the whole plan
for a producer binding: none — every occurrence of `variation_labels` states WHEN it is populated,
never by what code. Measured that the `graphed`-side accessor's own map is
`record_node_id -> (reduced_node_id, member_index | None)` — a function by type, carrying no labels —
so the r16 "carries BOTH labels" clause is unwritable there without a self-supplied hook
(self-derived) or an `importorskip` (a CI SKIP).

Edits: (a) §8.2(i) gains a bound PRODUCER paragraph — the hook supplier = `graphed-histogram`'s
group-plan builder, composing its `(output, label) → record id` map with the m49 accessor — plus the
consequence for §10 (the `graphed` half witnesses the ACCESSOR, the label association is witnessed in
`graphed-histogram`); (b) §10/m49's clause re-worded over the accessor: the shared node maps to ONE
key **reached from BOTH labels' record cones**, which is what makes any label map over that key space
set-valued (the non-vacuity claim survives, the false "the map carries labels" reading does not),
with §3.4's impact verb named as the `graphed`-side label→record-id channel; (c) a NEW
`graphed-histogram tests/frozen/m49` anchor bullet for the `variation_labels` POPULATION through the
bound owner; (d) the downstream PARTITIONING clause's "(3) one key carrying BOTH labels" re-worded to
"one key reached from both labels" for consistency.

---

## MID

### M1 — design — §6.1d's fill label set omits `sample=` — **APPLIED**

*Verified.* Plan `:1846-1847` (three-source union) vs `:1707-1708` (§6.1b r19 puts `sample=`-borne
labels in `S`), `:2083-2086` (§6.2 repeats), m50's sample-only-label anchor (`:4412-4425`), and
§6.1d's own fold order which already folds `sample=` LAST. Measured at `graphed-histogram@211cbbe`:
`Histogram.fill` type-checks `args` and `weights` and appends `sample` to the same `inputs` list with
no check (`src/graphed_histogram/boost.py:160-178`), so nothing downstream catches the divergence.

Edit: the union now reads "value-borne labels, ambient-weight labels, explicit `weight=[...]` factor
labels **and `sample=`-borne labels**", with the m50 contradiction named as the reason.

### M2 — design — §9.2's varied bundle needs a manifest label channel — **APPLIED**

*Verified at `graphed-latest@ff7c607`.* `build_bundle` is singular (`preserve/bundle.py:103-123`);
the manifest's `analysis.outputs` is `{"value": int(value.node_id), "weight": None if weight is None
else int(weight.node_id)}` (`:184-193`); `reproduce` ends `return values[out["value"]]` (`:250-252`);
`inspect()` renders from `m['environment']`, `m['config']`, `m['analysis']['histogram']`, the
deserialized IR nodes and the sourcemap only (`:267-288`); `FORMAT_VERSION = 1`
(`preserve/manifest.py:17`), `canonical_bytes` = `json.dumps(..., sort_keys=True)` (`:20-22`).
No label slot anywhere, and §1.2 keeps labels out of the IR.

Edit: §9.2 binds the carrier the way §8.2(i) r25 binds its own — an ADDITIVE per-label output map
(`analysis.outputs` extended to `{label: {"value": id, "weight": id|None}}` or an additive sibling
key), SORTED by label so `canonical_bytes` stays deterministic, `FORMAT_VERSION` bumped, unvaried
bundles unchanged; exact spellings pinned at m50 freeze.

### M3 + M12 (merged) — design + tests — §2.3d's numpy gate floor / §10-m48's missing numpy bullet — **APPLIED**

*Verified by running the discovery rule myself in `graphed-latest@ff7c607`'s `.venv`*: annotation-wide
filter over `graphed.__all__` → `['aggregate_plan','apply','join','join_plan','pack_key',
'read_columns','repartition','shuffle_plan']`; over `graphed.numpy.__all__` (22 names) →
`['apply_gufunc','empty_like','full_like','ones_like','project','zeros_like']`. None of the named
floor members (`compile_ir`/`context_of`/`broadcast_like`) is in `graphed.numpy.__all__`, and the six
discovered numpy verbs are only *broadcast*/*expanding* — so r25's "the same containment floor"
applied per-enumeration is unsatisfiable on BOTH of its clauses. Grepped §10 (`:3273-4773`) for
`graphed.numpy` / `numpy.__all__`: 0 hits (the only numpy mentions are the property fixture's idiom
and m51's backend refusal).

Edits: (a) §2.3d states the scoping — the floor is asserted over the UNION of the enumerations, never
per enumeration, with the measurement as its basis; (b) §10/m48's §2.3d bullet gains the
idiom-package enumerations, their per-verb classifications, the union-scoped floor, and the
freeze-order check.

### M4 — design — `graphed.awkward`'s package-level Array-consuming verbs undisposed — **APPLIED**

*Verified.* `graphed.awkward.__all__` = `['AwkwardBackend','AwkwardForm','from_awkward',
'from_parquet','functions','gak','io','payloads','project','project_buffers',
'read_parquet_partition','shuffle','to_parquet']`; the annotation-wide filter over it discovers
exactly `project` and `project_buffers` — `project(array: Array, *, on_fail='raise') -> Projection`
(`python/graphed/awkward/projection.py:105`), `project_buffers(...)` (`:119`), both through `_replay`
whose first statement is `session = array.session` (`:65-68`). `to_parquet` annotates `array: Any`
(`awkward/io.py:206-207`) so it is NOT discovered — the m51 freeze-order trap stays closed, which I
checked because my edit newly points the gate at that `__all__`.

Edit: §2.3d's idiom-package clause extended from `graphed.numpy.__all__` to both idiom packages, with
`project`/`project_buffers` classified *expanding* (same as their numpy twin) and the measured
signatures cited; §10/m48's bullet swept with M3.

### M5 — design — §3.4's and §5.3's verbs cannot key on labels from a `Sequence[Array]` — **APPLIED**

*Verified.* `inspect.signature(graphed.read_columns)` → `(arrays: 'Sequence[Array]', source_nid:
'int') -> 'tuple[str, ...] | None'` (`python/graphed/projection.py:109`); `Array.__slots__ =
("_node_id", "_session")` (`python/graphed/array.py:127-128`) — no label attribution of any kind.

Edits: §3.4 and §5.3 take the per-label output CONTAINERS (`Sequence[Varied]`) — §3.4 without
`source_nid` (a reachability difference is source-agnostic), §5.3 with it (it CALLS `read_columns`
per label) — both resolving labels via `graphed.universe(v, L)`; §9.1's two entries updated to match.

### M6 — design — §2.1 accepts a container whose members live in different row spaces — **APPLIED**

*Verified.* §2.1's construction checks are Session + `op_form` + partitioned-source set + (r18)
one-ancestry-chain handles — no row space; `context_of` on a container answers with the most-derived
handle (`:976-989`), and `reindex_to` is the identity when the value already carries the target
handle (`:1934-1937`), so nothing re-indexes the ancestor-handled member. Measured basis re-checked:
`Session.record_op` validates only the backend's `op_form`, never lengths or row spaces
(`python/graphed/session.py:142-168`). §10/m48's own r21 fixture note names this hazard and
deliberately keeps the check open.

Edit: §2.1's construction-check paragraph generalizes §2.1(b)'s r19/r20 rule to EVERY overload —
one row space (the target's for (b)/(c), the container's most-derived handle's for (a)),
ancestor-handled members re-indexed across the intervening §6.1d links (a `Varied` result then
reduced to its central universe per the (a)/(c) member rule), a DESCENDANT-handled member a
construction-time error naming both contexts and the DIRECTION; m48's existing `vary`-construction
divergence anchor carries the extra negative control.

### M7 — design — `graphed.numpy.project`'s two incompatible *expanding* semantics — **APPLIED**

*Verified.* `Projection` is `@dataclass(frozen=True)` with the single field
`read_columns: Mapping[str, frozenset[str]]` plus `columns_for`/`total_columns`
(`python/graphed/projection.py:34-44`) — no `None` sentinel; conservative projection returns the FULL
column set (`python/graphed/awkward/projection.py:110-113`, `cols = set(key_map.values())`). So the
cited `read_columns` conservative-`None` union rule has no operand.

Edit: §2.3d pins `project`/`project_buffers` to per-label `{label: Projection}` results and
explicitly withdraws the `read_columns`-union cross-reference, with the measurement as the reason;
§10/m48's new idiom bullet asserts the classification so the pick is witnessed.

### M11 — tests — r25 made `sample=` a first-class fill operand with no anchor — **APPLIED**

*Verified.* §6.1d r25 (`:1978-1992`) binds `sample=` into the fill's unification/divergence check and
binds ancestor-context `sample=` re-indexing. m48's divergence-at-the-fill anchor is worded over two
AXIS values (`h.fill(a_from_ctx1, b_from_ctx2)`) and the link-kind-(1) anchor is
`h.fill(events.MET.pt, sel.MET.pt)` — neither carries a `sample=`; the two anchors that do (m48's
four-way fold order, m50's sample-only label) build it from ONE context.

Edit: m48's divergence anchor gains a third assertion (`sample=` from a divergent context raises,
naming both contexts — record-time, so no storage constraint) and the link-kind-(1) fixture gains an
ancestor-context `sample=`, with the `Mean`/`WeightedMean` storage pin carried over from the r22
fold-order pin (or the `sample=` half rides that fixture).

---

## LOW

### L8 — design — m49's target line re-adds "§7.2's seam half (β)" — **APPLIED**

*Verified.* m49's line (`:4146-4157`) vs §7.2 r23 (`:2861-2867`: (β)'s return CHANNEL at m48 with
(α), (β)'s PAYLOAD at m49) and m48's target line, which takes §7.2 including the r19 seam and
§8.2(i)'s field declaration. Edit: the clause narrows to "the POPULATION of §7.2's seam-half-(β)
payload", noting the channel and field are m48 and that m49's `§8` clause already carries it.

### L9 — design — axis vs sibling mode return different `graphed.labels` ORDER — **APPLIED**

*Verified.* §2.2's order rule (`:568-570`), §6.2(i-bis)'s nominal-first-then-lexicographic rule
(`:2151-2158`), §6.2(iii)'s own `btag_down < btag_up < jes_down < nominal < pu_up`, §6.1d's fold
order, and m50's equality anchor. Edit: §6.2(i-bis) states the disagreement and binds m50's anchor to
compare PER LABEL, never by `graphed.labels` equality across modes.

### L13 — tests — m51's numpy-backend refusal anchor has no pinned directory — **APPLIED**

*Verified.* §10 pins `graphed`'s m51 home as `tests/frozen/awkward/m51`; m51's bullet groups the
numpy refusal under the ROOT half. Measured: `ls tests/frozen` → awkward, checkpoint, core, corpus,
debug, frontend, numpy, preserve; `scripts/run-tests.sh:16-25` runs `numpy:tests/frozen/numpy
tests/extra/numpy` as its own suite with `SPLIT_PKGS="frontend numpy awkward"` (`:30`); the source is
`python/graphed/numpy/io.py`. Edit: `tests/frozen/numpy/m51` added to §10's pin list with the
rationale, and the anchor split into its own bullet out of the ROOT half.

### L14 — tests — m48's stacking anchor uses the `Varied[label]` subscript §2.2 deleted — **APPLIED**

*Verified.* `:3596` vs §2.2's removal of `[label]` indexing (`:628-630`) and §2.1 r24's two-level
resolution. Edit (two places, minimal): §2.2 declares `x[L]` PROSE notation for
`graphed.universe(x, L)` throughout, and m48's anchor is respelled in the bound surface —
`graphed.universe(graphed.weight(sel2), "jes_up") == old_ambient_jes_up *
graphed.universe(graphed.nominal(factor), "jes_up")`.

### L15 — tests — r25's `Varied`-target class-pairing rule is exercised by no m48 anchor — **APPLIED**

*Verified* by enumerating every `graphed.vary(` occurrence in §10: `:3773`, `:3816`, `:4044`, `:4078`,
`:3586-3599` — all target an `Array` or a context; none a loose `Varied`. Edit: m48's stacking bullet
names the base case's target as a LOOSE `Varied` and asserts the result's container class pairs with
`type(graphed.nominal(x))` plus unchanged inherited members.

### L16 — tests — m51's manifest levels assertion has no bound serialized shape — **APPLIED**

*Verified.* §6.4a's key space is heterogeneous (bare `0`, field-scoped `("Jet", 1)`, bare `k` for the
record's own structure — r22/r24), the manifest is serialized with sorted keys into parquet KV
metadata, and a `(path, depth)` tuple has no JSON-native rendering; m51's anchor asserts the entry's
value against the supplied levels. Edit: §6.4e binds the entry as a SORTED list of either an integer
depth or a two-element `[field_path, depth]` array (`field_path` = §6.4b's `_`-flattened path), exact
key spelling pinned at m51 freeze.

### L17 — tests — m49's §3.4 fixture is spelled only in raw-`GraphStore` terms — **APPLIED**

*Verified.* The r24 measurement is stated entirely as `add_op` calls while §3.4's verb consumes
per-label containers; §5.2a/§5.2c each carry the explicit "built through the public `graphed.vary`
surface" correction and §3.4's anchor did not. Edit: that one-liner added, sharpened by M5's operand
fix (a raw `GraphStore` supplies no Session, no `Array`s and no labels), with the cheap frontend
spelling stated.

### L18 — tests — §6.2(3)'s no-`boost_histogram`-import rule is unmarked — **APPLIED**

*Verified.* The plan marks knowingly-unanchored rules four times (§6.1d's reindex ordering, §6.4e's
no-private-import rule, §7.2's no-second-compile, §1.1's `"1e1000000000"`); §6.2(3) is the same shape
and unmarked. Edit: marked knowingly UNANCHORED on the §6.4e footing, with the same optional
`tests/extra` static assertion.

---

## Rejected / deferred

None. Every finding was reproduced against the pinned roots before editing; no fix required
reversing an owner-locked decision (naming, functional surface, e-form encoding, context attachment,
record-time expansion, m48–m51 scope, the Phase-2 pull-in), so no `OPEN ITEMS (owner)` entry was
added.
