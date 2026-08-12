# systematics-vary-plan — revision r16 audit trail (review round 7)

Input: three independent r15 reviews (facts / design / tests),
`systematics-vary-plan-review-r15-{facts,design,tests}.md` — 29 findings after NIT exclusion
(0 BLOCKER, 4 HIGH, 13 MID, 12 LOW). Every finding was re-verified in this session against the
pinned verification roots (`graphed-latest` ff7c607, `graphed-histogram-latest` 211cbbe,
`graphed-exec-check` 201ea42, `uproot5-graphed` 393ecef, `graphed-corpus-latest` 49650e4,
`coffea-workdir` f34b8bdf) before any edit. **Nothing rejected, nothing deferred**; no finding's
resolution touched an owner-locked decision, so no "OPEN ITEMS (owner)" block was added.

Line numbers below are r15's (the reviewers') for the plan and current for source files.

---

## HIGH

### H1 — design §9.1/§6.4a(2a)/§6.1d/§2.6: `graphed.selection` undefined on a `vary`-derived context — APPLIED

**Verified.** §6.1d enumerates three lineage link kinds (plan :1139-1146); §9.1 stated
`graphed.selection` for the mask link and the universe/nominal link only (:1815-1824) while closing
"One rule, stated per lineage link kind"; §6.4a(2a) requires the mask to be `graphed.selection(c)`
for a `c` whose PARENT is the record's context and whose link is a MASK DERIVATION (:1434-1449).
§2.6's own sketch rebinds `sel = graphed.vary(sel, "btag", …, is_weight=True, …)` after
`sel = events[mask]` (:783-786), and §6.4b's stored varied weight factors are reached via
`graphed.weight(ctx)` (:1500-1504), so a weight-storing skim is written from a `vary`-derived
context by construction. m51's bridge anchor (:2479-2483) dodges it only by using the un-rebound
`sel`.

**Edits.** (a) §9.1 — added the `vary` (identity) link rule: `graphed.selection` walks `vary`
identity links and answers as of the first non-identity link, `None` when that walk reaches a root.
(b) §6.4a(2a) — the predicate is now "exactly one MASK DERIVATION plus any number of `graphed.vary`
identity links"; universe/nominal projection links remain excluded, with r15's rationale preserved.
(c) m51 bridge anchor — added the `vary`-derived-context write as an explicit accepted case
round-tripping identically to the pre-`vary` spelling.

### H2 — design §5.2c: frozen stage-count literal with no oracle + post-freeze re-measurement escape — APPLIED

**Verified.** §5.2a was repaired in r15 for exactly this defect (:957-971); §5.2c kept
"re-measured through the frontend at implementation time if the frontend construction differs"
(:979-990) over literals whose provenance the same paragraph attributes to the raw
`graphed.core.GraphStore` builder. §12.1 (:2578-2589) freezes before implementation, so the escape
instructs a post-freeze edit of a read-only test.

**Edit.** §5.2c now binds an ORACLE — the same N-universe topology hand-built WITHOUT `vary` in a
separate `Session`, reduced, its stage count taken as the expected integer — plus "the shared prefix
appears in exactly ONE stage"; §3.3's raw-builder shape is the expectation for the ORACLE, not for
the `vary`-built program; the re-measurement clause is deleted. §10/m49's `§5.2 witnesses` bullet
was updated to match.

### H3 — tests §4.3 + m48 anchor: the bound selection-invariance predicate is satisfied by construction — APPLIED

**Verified in code.** `graphed-histogram src/graphed_histogram/boost.py:176-178`
(`inputs = list(args)` then `inputs.extend(weights)`, then `sample`) and `:205-212` (one
`record_external` over that list); `graphed python/graphed/session.py:255-286` — `walk`'s post-order
over `inputs_of` makes a node's cone the transitive closure of its inputs. Therefore
`reachable(selection_mask) ⊆ reachable(fill_node[L])` for every label whenever the filled value is
post-selection, the intersection is the constant `reachable(selection_mask)`, and both halves of
r12–r15's predicate hold in every implementation — including `mask_L = mask & g_L`, since
`reachable(mask) ⊆ reachable(mask & g_L)`. Frozen precedent for the inputs layout:
`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84-86` (`len(node["inputs"]) == 4`
for one axis + three weights).

**Edit.** §4.3 withdraws the intersection predicate explicitly (with the measurement) and binds the
converse: per label, the fill node's recorded non-weight input prefix
(`store.nodes()[fill_id]["inputs"][:n_axes]`) equals nominal's — identical ids ⇒ identical cones by
interning. An optional reachability cross-check survives only in the discriminating shape
`reachable(fill[L]) − reachable(weight_input[L]) − {fill[L]}`. m48's §4.3 anchor bullet rewritten to
freeze the new form and to state the old one is NOT frozen.

### H4 — tests §2.3d + m48 anchor: disposition gate assigned to a repo that cannot satisfy its floor — APPLIED

**Verified.** `graphed pyproject.toml:29-48` — the `dev` extra carries `boost-histogram>=1.4` and
`hist>=2.7` but no `graphed-histogram`; the only occurrence of the name in the file is a mypy
`ignore_missing_imports` entry. CI installs `.[dev]` (`.github/workflows/ci.yml:34`). House pattern
for reaching it is module-level `pytest.importorskip("graphed_histogram")` —
`tests/frozen/preserve/m25/test_histogram_preservation.py:31`, `m27/…:185,207`, `m30/…:155`.
`awkward`+`pyarrow` ARE in the dev extra, so `graphed.awkward.to_parquet` is fine.

**Edit.** §2.3d's named floor is now asserted PER REPO — `graphed`'s gate takes
`{graphed.compile_ir, graphed.awkward.to_parquet}`; `graphed_histogram.Histogram.fill`'s disposition
is asserted in `graphed-histogram`'s flat `tests/frozen/m48`. m48's table-driven anchor bullet
mirrors the split, with the measured fixture facts inline.

---

## MID

### M1 — design §8.2(i)/(iii): the output-position fallback is unimplementable — APPLIED

**Verified.** `graphed python/graphed/execute.py:96-126` — `evaluate_ir` is one flat
`for nd in store.nodes():` loop appending into `vals`, no `try`/`except`, no per-node annotation;
outputs are selected only at `return [vals[o] for o in store.outputs()]`. A mid-loop failure carries
neither node id nor output identity, and most nodes are not outputs.

**Edit.** §8.2 restates the fallback: an output-position key is NOT implementable either; without
(iii) the only truthful attribution is plan-wide (the sorted union of all labels registered on that
plan). The "(iii) descoped ⇒ output-position fallback promoted" sentence was corrected accordingly.

### M2 — design §2.3d: disposition class set never enumerated — APPLIED

**Verified.** §2.3d's floor named "refusing / expanding / broadcasting" (:576-581) while
`to_parquet` and `Histogram.fill` — both members of its own named floor list — carried prose
dispositions in none of the three, and `graphed.context_of` was classified *eager-metadata*
(:598-600), a fourth class borrowed from §2.3c.

**Edit.** The legal class set is now enumerated exhaustively —
refusing / expanding / broadcasting / eager-metadata / accepting — with *accepting* defined and
assigned to `to_parquet` and `Histogram.fill`; both floors (§2.3d body and the m48 anchor) restated
over that set.

### M3 — design §1.1 vs §2.1: "reject a label equal to `nominal`" is unreachable — APPLIED

**Verified.** §1.1 binds `label = f"{name}_{tag}"` with a non-empty identifier `name` and a
non-empty `[A-Za-z0-9_]+` tag, so every user label contains at least one `_`; `"nominal"` does not.
§2.1 (:342-350) makes `nominal` a legal TAG that must arrive through `variations=`, yielding
`pu_nominal`. m48 freezes "every listed rejection" (:2226-2250).

**Edit.** The rejection is removed from §1.1's list and replaced by a reserved-by-construction
statement that keeps the legal `nominal` TAG explicit; the m48 grammar anchor says so too.

### M4 — design §2.1/§2.6b/§2.5: shift-after-weight is silently wrong — APPLIED

**Verified in the plan.** §2.1(b) binds the weight-on-shift direction (`old_ambient[L] × factor[L]`,
:365-382) — the reverse is unaddressed; §2.1(a)/(c) say inherited members pass through unchanged and
§2.6b's shift form registers nothing on the weight side (:727-732); Part I §2 records the exemplars
handling exactly this by hand ("these weights can go outside the sys loop…", :114-116).

**Edit.** §2.1 binds the ordering rule (a shift `vary` does NOT re-derive the ambient registry; a
weight depending on a collection MUST be registered after that collection is varied). §2.5 gains a
diagnostic on the named channel — a registered factor whose §3.4 cone contains a node a later shift
`vary` replaces is reported — declared an m49 target (where §3.4 lands), with an m49 anchor bullet
including its positive control.

### M5 — design §7.3/§8.2(i)/§1.2: invalidation list omits label RENAMING — APPLIED

**Verified in code.** `graphed python/graphed/core/plan.py:164-176` —
`task_id = sha256(_TASK_DOMAIN, self.ir, self.process.identity(), partition_bytes)`; `:72-76` —
`OpSpec.identity()` for an opaque spec returns `b"opaque\0" + <cloudpickle blob>`. m49's §8.2(i) adds
label STRINGS to `_PartitionReduce`, the opaque `process` spec, so a rename changes `task_id` while
the IR stays byte-identical (§1.2's own m48 anchor).

**Edit.** §7.3 documents the third invalidation class with the measurement and scopes §1.2's
no-recompute promise to the IR/interning level; m50's docs anchor now requires all three classes.

### M6 — design §10/m48 vs §6.1c vs §10/m50: axis-mode slot dragged into m48 — APPLIED

**Verified.** §6.1c's axis-mode paragraph (:1089-1099) carried no milestone scoping while m48's
target line named "§6.1 (incl. §6.1d ambient fills)" (:1907-1912) and m50's named only
§6.2/§9.1-variations/§9.2 (:2383-2385); m50's scaling anchor (:2432-2444) is worded over exactly
that paragraph. Same coverage argument r14 used to move §3.4 out of m48 (:1918-1922).

**Edit.** §6.1c's axis-mode paragraph is scoped "(m50, with §6.2)"; m48's target line excludes it
explicitly; m50's target line names it.

### M7 — tests §6.1d + m48 fold-order anchor: `sample=` fold-last has no anchor — APPLIED

**Verified in code.** `graphed-histogram src/graphed_histogram/boost.py:160-178` — `fill`
type-checks `args` and `weights` and then does a bare `if sample is not None: inputs.append(sample)`
with no check, so a `Varied` sample falls into `record_external` and dies on `.node_id`.

**Edit.** The m48 fold-order anchor is now four-way: two varied axes + ambient + explicit factor +
a varied `sample=`, asserting `sample=` folds last and is accepted/expanded rather than raising.

### M8 — tests §10/m48 split rule: two fill-dependent clauses on `graphed`'s side — APPLIED

**Verified.** The split enumeration (:1946-1950) is r12-era; the `graphed.labels` clause ends
"…remains a superset of the context-borne half of a FILL's label set" (:2217-2219) and the
universe/nominal clause was strengthened in r15 to assert the resulting VALUE of
`h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)` (:2219-2223). Fixture facts as in H4.

**Edit.** The split is stated as a RULE ("any clause whose assertion requires a `Histogram.fill`
lives in `graphed-histogram`'s flat `tests/frozen/m48`"), with the frontend-observable halves of
both clauses kept in `graphed` and their fill-dependent halves (plus §6.1d's fold order) moved.

### M9 — tests m49 §8.2(i) anchor: "two labels' shared node" has no operand — APPLIED

**Verified.** §3.3's builder (:831-834) gives each universe its own fork + K chain ops + terminating
reduction off a shared prefix, so no node is shared by two labels in §3.4's sense (:854-856, "shared
by `jes_up` and `jes_down` but NOT nominal"); prefix nodes are shared by all labels. The clause
degenerates to "the map is a function". Same shape r15 repaired for the DCE clause by extending the
topology.

**Edit.** The anchor's topology gains a second extension — one derived node consumed by TWO
NON-nominal universes — and asserts that node's `variation_labels` entry carries BOTH labels.

### M10 — tests §5.3: per-label projection-stats surface never named or pinned — APPLIED

**Verified.** §5.3 (:991-998) said only "exposed via §3.4", while §3.4 (:851-857) is a reachability
difference over node SETS; §9.1's surface list (:1799-1834) did not include it, and it carried no
"spelling pinned at freeze" clause, unlike every other new surface here.

**Edit.** §5.3 names it — a read-only `graphed` verb over `read_columns`' operands returning
`{label: tuple[str, ...]}` (per-label sorted read set, `projection.py:109-147`), spelling pinned at
m49 freeze — and it is listed in §9.1; m49's §5.3 anchor bullet now reads through it.

### M11 — tests §6.4b + m51 anchor: collision check vacuous, example is not a collision — APPLIED

**Verified in the plan.** The convention is `__vary_{label}__{field}` (:1505); r15's check and its
example (:1512-1515) and the m51 anchor (:2510-2513) both compare a derived name against a plain
stored name, which under the bound prefix can only collide if the user literally has a field named
`__vary_L__Jet_pt`. The real class is derived-vs-derived (`Jet.pt` and `Jet_pt` both varying).

**Edit.** §6.4b binds pairwise-distinct derived names AND no equality with any stored field name,
refusing while naming both source fields; the m51 fixture is respecified to vary BOTH `Jet.pt` and a
flat `Jet_pt`, with an explicit "a varying `Jet.pt` alongside a NON-varying `Jet_pt` is NOT a
collision and MUST NOT be frozen as a refusal".

### M12 — tests §2.3e clause (2): call arguments from implementer-owned `src` fixtures — APPLIED

**Verified in the plan.** Clause (2) (:656-673) binds the gate's call arguments to `src` fixtures
while its substance is handle PRESERVATION; a context-free primary operand makes both handles `None`
and the assertion passes vacuously. r15's own membership floor (:663-671) exists because
classification and fixtures are implementer-editable `src` — the same hole, other half.

**Edit.** Clause (2) now splits ownership: the FROZEN TEST constructs the context and owns the
contexted primary operand; `src` fixtures supply only auxiliary/typed operands
(`zip`'s mapping, `concatenate`'s second array, `unflatten`'s counts, `where`'s branches,
`linear_fit`'s operands); the gate asserts the returned handle is not `None` AND is the input's.
m48's propagation-gate anchor bullet mirrors it.

### M13 — tests §10/m49: JER-SF oracle is a partition-blind API — APPLIED

**Verified in code.** `graphed python/graphed/session.py:291-301` — `materialize(self, array)` calls
`self.walk(...)`; no partition, no `steps_per_file` anywhere. `python/graphed/core/execution.py:450-457`
— `SequentialRunner` iterates `sorted(plan.tasks, key=lambda t: t.key)`, so a plan run's per-partition
outputs fold deterministically.

**Edit.** §10/m49's placement rationale now requires a PLAN RUN at two `steps_per_file` values with
per-partition values concatenated in task order, and states explicitly that `Session.materialize`
MUST NOT be the oracle, with the measurement and the deterministic alternative.

---

## LOW

### L1 — facts §2.3d :567 + appendix :2705: `__init__.py:12,44` → `:12,46` — APPLIED

**Verified.** `grep -n '"compile_ir"|"apply"|"aggregate_plan"' python/graphed/__init__.py` →
`43: "aggregate_plan",` / `44: "apply",` / `46: "compile_ir",`; line 12 is
`from .execute import CompiledGraph, compile_ir, evaluate_ir`. Both places corrected, each noting
`:44` is `"apply"`.

### L2 — facts appendix :2694: `projection.py:109-121` → `:147` — APPLIED

**Verified.** `def read_columns(...)` at `projection.py:109`, `return tuple(sorted(needed))` at
`:147`. The appendix row now carries `:147` (span `:109-147`), matching §8.2(i)'s r15 correction.

### L3 — facts §6.4a(2a) :1451: dangling `(:590-592)` — APPLIED

**Verified.** No file is named in that clause; plan lines 590-592 are §2.3e's `__slots__` text, while
the Drop rule is at plan :640. Replaced with a plain reference to §2.3e's Drop rule.

### L4 — facts §2.3c :494-500: "an `__all__`-driven test would discover nothing" — APPLIED

**Verified.** In `graphed-latest/.venv`:
`[n for n in graphed.awkward.__all__ if inspect.isfunction(getattr(graphed.awkward, n))]` →
`['from_awkward','from_parquet','project','project_buffers','read_parquet_partition','to_parquet']`;
`graphed.awkward.functions` discovers 65, the package alias 0.

**Edit.** The sentence now says an `__all__`-driven test discovers a WRONG six-name set — non-empty,
so a bare non-emptiness floor would not catch it — with the measured names.

### L5 — design §7.1 vs §6.2: "no per-variation execution loop anywhere" — APPLIED

**Verified.** §7.1 (:1642-1644) is absolute; §6.2 (:1225-1231) binds an evaluator-side loop as m50's
mechanism. **Edit:** §7.1 scoped to per-variation RE-EXECUTION of the graph or the plan, naming
§6.2's in-fill loop as not one, and pointing at §5.2b as its mechanism witness.

### L6 — design §2.6a: context `[]` with a slice or int undefined — APPLIED

**Verified in code.** `python/graphed/array.py:344-371` — `__getitem__` branches on
`Array`/`str`/`list[str]`/`slice`/`int` before its final `TypeError`. §2.6a bound only the string and
mask forms while claiming to mirror it. **Edit:** a `slice`/`int` subscript on a CONTEXT is REFUSED,
naming the supported forms (row-slicing has no defined effect on §2.6c re-indexing).

### L7 — design §6.3(2) vs §6.1d: two incompatible broadcast-seam triggers — APPLIED

**Verified.** §6.1d (:1166-1179) binds "every weight factor the fill applies"; §6.3(2) (:1357-1364)
scopes the seam to "the varied/ambient path", leaving the contexted-but-unvaried fill undecided.
**Edit:** ONE trigger stated in §6.3(2) — a handle OR any `Varied` input; neither ⇒ byte-identical to
today — and §6.1d cross-references it.

### L8 — design §2.3e(3)/(4): "§5.4 boundary set" never enumerated; (4) inherits non-transferable clauses — APPLIED

**Verified in code.** Public `def`s in `python/graphed/awkward/functions.py`: the only boundary verb
is `join` at `:18` (no repartition/exchange/pack_key in gak). **Edit:** the refusing class is
enumerated as `{gak.join}` at freeze time; §2.3e(4) gets its own one-line `Array`-surface floor
(refusing = `{repartition}`, broadcast count ≥ freeze-time) instead of "gated the same way". The m48
anchor bullet carries both.

### L9 — tests §9.1 + m50: plan-level `{output: [labels]}` anchored to a test that cannot exercise it — APPLIED

**Verified in code.** `python/graphed/preserve/bundle.py:268-288` — `def inspect(bundle: Bundle) -> str`
renders manifest + sourcemap lines. **Edit:** the listing gets m50, a spelling pinned at m50 freeze
and its own frozen anchor in `graphed`'s `tests/frozen/preserve/m50` over a two-output varied
program; `inspect()`'s own label listing stays where it was; m50's target line updated.

### L10 — tests §5.2b vs §10/m49(i): placement pointer contradicts §10 — APPLIED

**Verified.** §5.2b said "the m49 frontend half"; §10/m49(i) puts the matrix in `graphed-histogram`'s
flat `tests/frozen/m49` and says "The §5.2b read witness binds to THIS run"; fixture facts as in H4.
**Edit:** the parenthetical now points at the m49 `graphed-histogram` half, noting the same for m48's
matrix.

### L11 — tests §2.3a: enumeration filter never stated — APPLIED

**Verified in the venv.** `[n for n in dir(Array) if not n.startswith("_")]` →
`['filter','map','node_id','reduce','repartition','session']`, of which `node_id`/`session` are not
functions (`array.py:137-143`); `dir(NumpyArray)` has 32 public names. **Edit:** §2.3a states the
filter — `inspect.getmembers(type(graphed.nominal(v)), inspect.isfunction)`, non-underscore, plus the
dunder set — with the reason (r15's per-name rule over an unfiltered enumeration would contradict
§2.2's reserved-name anchor in the same milestone).

### L12 — tests m50: user-declared-axis refusal does not bind the recognition rule — APPLIED

**Verified.** §6.2(i-bis) establishes `StrCategory(..., name="variation")` is a `TypeError`
(appendix row :2683, bh 1.7.2/1.8.0) and that the name carrier is per-axis `__dict__`, round-tripped
by `graphed-histogram src/graphed_histogram/_spec.py:31-37,81-84` (`_metadata_of` harvests
`__dict__`; `_restore_metadata` writes it back). **Edit:** the m50 anchor binds recognition as
`axis.__dict__.get("name") == "variation"`, states the fixture sets the name that way, and states a
user `StrCategory` under any other name is untouched.

---

## Rejected

None.

## Deferred (owner-locked)

None. No finding's resolution required reversing owner-locked decisions 1-7; no "OPEN ITEMS (owner)"
block was needed.
