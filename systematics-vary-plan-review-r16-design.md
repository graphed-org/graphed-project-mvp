# systematics-vary plan — review round 8, DESIGN SOUNDNESS lens

- **Lens:** design soundness (is PART II a coherent, implementable specification: contradictions,
  unhandled interactions, under-specified Implementation Targets, milestone-boundary consistency,
  package-boundary/factorization compliance).
- **Plan revision reviewed:** r16 (`systematics-vary-plan.md`, 3516 lines, read in full — PART I,
  every PART II section, §10 milestones, §11, §12, Anchors appendix, revision history).
- **Date:** 2026-07-30.
- **Verification roots used (all code facts below were re-measured in-session against these, never
  against the stale submodules in `graphed-workdir`):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (consolidated `graphed`, incl. its `.venv`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`
  - `/private/tmp/claude-501/graphed-exec-check` @ `201ea42`, `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
    (consulted, no finding rests on them)
- **Owner-locked decisions were not relitigated.** No finding below asks for a different naming,
  surface, encoding, attachment point, architecture, scope or Phase-2 pull-in choice; every finding
  is about internal consistency or implementability of what the plan already specifies.

---

## HIGH

### H1 — §7.2/§6.1c: the frontend's `node id → position` derivation is unsound; the OPTIMIZER collapses distinct record-id outputs, and the fix for that is an m49 target while §7.2/§6.1c are m48

**Section:** §7.2 (m48 target), §6.1c, §1.2's m48 dedup anchor, §8.2(i).

**Detail.** §7.2 binds: *"The frontend owns `(output, label) → node id` — NOT `→ position` — and derives
`node id → position` from the compiled output list, so many labels MAY resolve to one position and the
unpacker replicates that value."* Its entire measured basis is **record-time interning**: *"compiling two
structurally identical outputs returns ONE value … `mark_output` de-duplicates"*. That covers the case
where two labels share the *same record node id*, which the frontend can dedup itself.

There is a **second, independent collapse mechanism the plan never considers**: the M4 reducer's equality
saturation merges *distinct* record-time nodes. Measured this session against `graphed-latest@ff7c607`
(its own `.venv`), with the `graphed.numpy` idiom:

```
w   = gnp.from_array(s, "w", np.array([1.,2.,3.]))
nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5      # a mu_R/mu_F family: nominal + tags "1","2","0.5"
distinct record ids: [0, 1, 2, 3]
compile_ir(s, nom, m1, m2, mh) -> evaluate_ir returns 3 values
reduced outputs: [0, 1, 2]
```

and, on the M2 list backend, the commutativity half:

```
o1 = x + y ; o2 = y + x        # record ids 2 and 3 — DISTINCT
compile_ir(s, o1, o2)          -> evaluate_ir returns 1 value
compile_ir(s, o1, z, o2)       -> 2 values; reduced outputs [2, 3]
```

The mechanism is `EggEngine`'s sound rule set: `SYMMETRIC_OPS = ["add","mul","and","or","eq","ne",
"maximum","minimum"]` and `IDENTITY_TOKENS` = `x + 0.0` / `0.0 + x` / `x * 1.0` / `1.0 * x`
(`src/optimizer/engine.rs:22-31,67-80`), extracted by quotienting the IR by the e-graph
(`engine.rs:89-110`).

This is **not a contrived case for this plan**: §1.1 makes stringified-float tags first class and names
*"μR/μF scale factors"* as the motivating family, and a μR/μF family spelled the obvious way
(`variations={s: w * float(s) for s in scales}`) contains a **literal `w * 1.0` member**, which the
identity rule merges with the nominal weight. The two members have *different* record ids, so:

- §1.2's m48 dedup anchor does **not** cover it — that anchor asserts "arena Δ = 0, the same node id,
  … ONE evaluated fill", i.e. exactly the record-time case (Δ ≠ 0 and the ids differ here);
- §7.2's stated derivation gives the frontend 4 positions for 3 values, so `_GroupReduce` (whether
  count-sliced as today, `boost.py:100-117`, or index-keyed per §6.1c) indexes past the end of `fills`
  and raises an opaque `IndexError` inside the worker — precisely the failure §6.1c/§7.2 exist to
  prevent, one layer deeper;
- the only sound key is the **record → reduced id map**, and §8.2(i) establishes that no such channel
  exists (`CompiledGraph` carries `ir` + `source_names` only, `python/graphed/execute.py:36-45`;
  the `remap` vector is never returned, `src/optimizer/mod.rs:88-116`) and adds it as an **m49**
  Implementation Target — while §7.2 and §6.1c are **m48** targets (§10/m48).

**Evidence.** In-session probes above; `python/graphed/execute.py:54-80,126`;
`src/optimizer/engine.rs:22-31,67-110`; `src/store.rs:152-153`;
`graphed-histogram src/graphed_histogram/boost.py:100-117,282`; §7.2 (plan `:1801-1817`);
§8.2(i) (plan `:1897-1919`); §10/m48 target line (plan `:2101-2117`).
Note the frontend *can* observe the count today — `graphed.core.GraphStore.deserialize(bytes(c.ir)).outputs()`
returned `[0,1,2]` above — but those are reduced ids, so the *correspondence* is not recoverable.

**Suggested fix.** Pick one and bind it in §7.2, with an m48 anchor:
1. **Move §8.2(i)'s read-only record→reduced accessor into m48** (it is the only sound key, m49 needs
   it anyway, and it is read-only per §3.1's r13 wording); or
2. bind an **m48 guard**: after `compile_ir`, the frontend compares `len(deserialize(ir).outputs())`
   against its own distinct-record-id count and, on a mismatch, raises a clear `graphed` error naming
   the collapsed labels' outputs rather than mis-slicing — a refusal, not a crash; plus
3. either way, extend m48's §1.2 dedup anchor with a **second, non-record-time case**: a label whose
   member is `nominal * 1.0` (or `x+y` vs `y+x`), asserting the result mapping still carries both keys
   with one evaluated fill — the current anchor's `Δ = 0` / same-node-id wording cannot reach it.

---

## MID

### M1 — §6.2(i-bis)'s `graphed.labels(h)` (sorted axis bin set) contradicts §2.2's "nominal first" ordering guarantee for the same verb

**Section:** §2.2 vs §6.2(iii)/§6.2(i-bis); m50 anchor "§6.2(i-bis) axis-mode result shape".

**Detail.** §2.2 binds `graphed.labels(x)` as *"ordered: nominal first, then insertion order; inherited
labels before new ones under stacking"*. §6.1a then declares the helper *"uniform"* over the histogram
result shapes, and §6.2(i-bis) binds `graphed.labels(h)` on an axis-mode histogram to *"the variation
axis's bin set"* — while §6.2(iii) binds that axis to be **sorted lexicographically** ("`murf_10` sorts
before `murf_2`"). Lexicographically, `"nominal"` is not first in any realistic family
(`btag_down < btag_up < jes_down < nominal < pu_up`). So on the third shape the verb either violates
§2.2's ordering rule or silently re-orders the bin set (in which case it is not "the axis bin set" as
bound, and nothing says so). m50 freezes this verb's behaviour and the §6.2 declaration anchor
deliberately forbids using `graphed.labels(h)` as the oracle there (circularity), so the ordering is
pinned nowhere.

**Evidence.** Plan §2.2 (`:409-414`), §6.1a (`:1179-1182`), §6.2(iii) (`:1477-1484`), §6.2(i-bis)
(`:1418-1426`), m50 anchors (`:2689-2704`, `:2662-2688`).

**Suggested fix.** One sentence in §6.2(i-bis): `graphed.labels` on an axis-mode histogram returns the
axis's bin set **re-ordered to §2.2's rule** (nominal first, then the remaining bins in the axis's own
order) — and say explicitly that the *storage* order stays lexicographic. Add the ordering to the m50
i-bis anchor.

### M2 — §5.3's projection-stats verb type `{label: tuple[str, ...]}` cannot express `read_columns`' `None` ("read every column"), and §2.3d's union rule for `read_columns` has the same hole

**Section:** §5.3 / §9.1 (m49), §2.3d.

**Detail.** §5.3 r16 pins the new verb as *"returning `{label: tuple[str, ...]}` — per label, that
label's SORTED read set, computed by applying `read_columns` … to each label's outputs"*. Measured,
`read_columns(arrays, source_nid) -> tuple[str, ...] | None`, and `None` is a **live, semantically
inverted** answer: `return None` on whole-record consumption or a bare source read, documented as
*"meaning 'read every column'"* (`python/graphed/projection.py:109-121,145-147`). Under the bound return
type an implementer must render that as `()` — which reads as *"reads nothing"*, the exact opposite —
or violate the frozen type. The same gap sits in §2.3d, which binds `read_columns` over a `Varied` to
*"the union over all labels' members"* without saying that the union is `None` when any member is `None`
(a set union would silently narrow a conservative label's read list and starve its task).

**Evidence.** `python/graphed/projection.py:109-147` (read in session); plan §5.3 (`:1117-1125`),
§9.1 (`:2016-2019`), §2.3d (`:562-565`).

**Suggested fix.** Bind `{label: tuple[str, ...] | None}` in §5.3/§9.1, and one clause in §2.3d: the
`Varied` union is `None` if any label's read set is `None`, else the sorted union. Add the conservative
label to the m49 §5.3 anchor (it is free — one `gak` op applied directly to the source).

### M3 — §6.2: nothing binds what happens when axis-mode and sibling-mode fills land in the SAME histogram

**Section:** §6.2(i) cross-fill agreement, §6.1c axis-mode slot (m50), §6.1a.

**Detail.** §6.2 calls axis mode *"an opt-in **fill** mode"* with the *"opt-in spelling pinned at m50
freeze"* — i.e. plausibly a per-`fill()` argument. The only cross-fill rule bound is about **label
sets**: *"a second fill into the same axis-mode histogram whose inferred label set differs from the
first's is a hard error"*. Nothing decides the case where fill 1 opts in and fill 2 does not. That case
is not benign: §6.1c binds an axis-mode output to contribute **exactly ONE slot, keyed `(output, None)`,
gathering ALL that output's fill-node indices**, while sibling mode keys `(output, label)` — a
mixed-mode histogram would produce both key forms for one output, and §6.1a/§6.2(i-bis) then give it two
contradictory result shapes (`{label: hist}` and a bare axis histogram). It also breaks the reducer:
`_GroupZero` builds one `zero_of(spec)` per slot and `_add_groups` is a key-wise `+`
(`graphed-histogram src/graphed_histogram/boost.py:120-130`), and the two modes' specs differ by the
variation axis (measured, bh 1.8.0, per the plan's own §6.1c evidence: cross-axis addition raises).

**Evidence.** Plan §6.2 (`:1357-1361`, `:1415-1417`), §6.1c (`:1216-1230`), §6.1a (`:1171-1182`);
`graphed-histogram src/graphed_histogram/boost.py:100-130,236-292` (read in session).

**Suggested fix.** Add one clause to §6.2(i)'s cross-fill agreement rule: the mode is a property of the
**histogram** — the first fill fixes it, and a later fill in the other mode is a hard error naming both
(the same shape as the label-set mismatch error). Add it to m50's §6.2 declaration anchor.

### M4 — §6.2's "a shift sibling **MAY** target the same pre-declared variation axis" is an either/or that §6.1c and m50's frozen anchor both treat as mandatory

**Section:** §6.2 vs §6.1c (axis-mode slot) and m50's equality/scaling anchors.

**Detail.** §6.2 says shift labels *"always lower as sibling fill nodes … **but a shift sibling MAY**
target the same pre-declared variation axis"*, then immediately asserts *"Axis-mode fill-node arity is
therefore `1 + |S|`"* and §6.1c binds the axis-mode output to ONE slot gathering **all** its fill-node
indices whose value is a **bare** histogram. m50 freezes *"a mixed shift+weight program lands in ONE
axis-mode histogram equal to its sibling-fill decomposition"*. An implementer who reads "MAY" as
optional and lowers shift labels in axis mode as ordinary sibling slots conforms to §6.2 and fails the
frozen m50 anchor. This is the same "left an either/or to the implementer" class r13 closed for the
numpy broadcast seam (§6.1d: *"the r12 wording left 'a no-op … or a refusal' to the implementer, and the
two are not interchangeable"*).

**Evidence.** Plan §6.2 (`:1363-1373`), §6.1c (`:1216-1230`), m50 anchors (`:2651-2661`, `:2705-2723`).

**Suggested fix.** Replace "MAY" with a binding statement: **in axis mode a shift sibling writes its
label as the scalar category value of its own fill** (no per-label sibling slot). One word, and the
arity/slot/anchor triple becomes consistent.

### M5 — §1.1: the numeric-equal rejection is scoped to an undefined "family"; under the natural reading a cross-notation duplicate built across two stacking `vary` calls is admitted

**Section:** §1.1 (m48 grammar anchor), §2.1 stacking.

**Detail.** §1.1 binds the cross-notation guard as *"two tags in **one family** that both parse as
numbers … MUST NOT parse numerically equal"* and lists the rejection as *"numeric-equal tag pairs
**within a family**"*. **"Family" is never defined anywhere in the plan** (grep: the word appears at
`:243,244,260,280,297,306,321,1483` and only ever as a loose noun). Every *other* §1.1 rejection is
scoped explicitly — *"duplicate labels after canonicalization (within the call, within the container, or
colliding with inherited labels)"* — and §1.1 goes out of its way to bind that **"Unify" means ACROSS
calls** for canonical spellings. So under the natural per-call reading of "family":

```
ctx = graphed.vary(ctx, "murf", w, is_weight=True, variations={"0.5": a})   # label murf_5em1
ctx = graphed.vary(ctx, "murf", w, is_weight=True, variations={"0p5": b})   # label murf_0p5
```

is accepted — two labels, two universes, two StrCategory bins and two content hashes for **one value**,
which is verbatim the hazard §1.1 says the rule exists to prevent, and it is *unconstructible* to catch
later because the p-form deliberately does not canonicalize. The m48 anchor freezes the within-one-call
pairs (`{"0.5","0p5"}`, `{"2","2p0"}`) and therefore pins the weaker reading.

**Evidence.** Plan §1.1 (`:276-300`, `:318-322`), §2.1 stacking (`:372-390`), m48 grammar anchor
(`:2465-2488`); `grep -n "family" systematics-vary-plan.md`.

**Suggested fix.** Define the scope once in §1.1 — e.g. *"a family is the set of tags carried by one
`name` on one container, INCLUDING inherited labels"* — and extend the numeric-equal check to inherited
labels of the same name (it is the same parse the check already performs). Add the two-call
cross-notation case to the m48 anchor's rejection list.

### M6 — §2.3d's per-class non-vacuity floor is unsatisfiable-by-construction in `graphed`'s half unless two m48-NEW verbs happen to be annotated with `Array`

**Section:** §2.3d discovery rule + floor; m48 anchor "§2.3d module-verb dispositions".

**Detail.** m48's gate must contain *"at least one member of **each class** in §2.3d's bound class set
(refusing / expanding / broadcasting / eager-metadata / accepting)"*, over
`discovered ∪ named-floor-list`, where `graphed`'s floor list is `{graphed.compile_ir,
graphed.awkward.to_parquet}`. Re-measured in `graphed-latest`'s own venv, the annotation-wide filter
over `graphed.__all__` discovers exactly
`['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`.
Mapping those through §2.3d: **refusing** (6) ✓, **expanding** (`apply`, `read_columns`) ✓,
**accepting** (`to_parquet`, floor) ✓ — but **broadcasting** is supplied *only* by
`graphed.broadcast_like` and **eager-metadata** *only* by `graphed.context_of`, both **new in m48** and
neither named in the floor list. Whether the frozen gate can find them depends entirely on how the
implementer annotates their parameters after the freeze (`broadcast_like(value, factor)` is described as
a *neutral* seam taking an arbitrary factor — `value: Any` is a plausible annotation). If either is
missed, the frozen floor goes **red against a correct implementation** — the exact shape r14 fixed when
it gave `broadcast_like` a disposition, and r15 fixed by naming `compile_ir`.

**Evidence.** In-session enumeration (above); plan §2.3d (`:600-635`), §2.3e (`:645-654`),
§6.1d (`:1320-1326`), m48 anchor (`:2261-2285`).

**Suggested fix.** Add **`graphed.context_of` and `graphed.broadcast_like` to §2.3d's named floor list**
(and to m48's `graphed`-half list). They are the sole representatives of two of the five classes; naming
them costs nothing and removes the dependency on post-freeze annotation style.

---

## LOW

### L1 — §2.6 never binds that a read through a derived context is re-indexed by that context's derivation mask

**Section:** §2.6a/§2.6b/§2.6c (m48 target; m48 freezes context semantics).

**Detail.** §2.6c bindingly re-indexes the **ambient weight registry** ("every member RE-INDEXED by the
derivation mask, label-aligned per §2.4") and, for a `Varied` mask, says the derived context's
collections *"are `Varied` per §2.6b"*. It never states the central rule of the whole idiom: that
`sel.Jet` is `events.Jet` **re-indexed by `sel`'s derivation mask** (label-aligned when the mask is
`Varied`). The rule is only *asserted in passing*, inside §6.1d's rationale for value re-indexing
("`h.fill(events.MET.pt, sel.Jet.pt)` … a value read at `events`' row count"), and implied by the §2.6
sketch. Everything downstream (§6.1d's link kind (1), §6.4a's row-space predicates, the m48 re-indexing
anchor) is defined against it.

**Suggested fix.** One sentence in §2.6a or §2.6b: *"A read performed through a derived context yields
that context's row space — the parent's value re-indexed by the derivation mask, label-aligned per §2.4
(each label's member by that label's mask, nominal's by nominal's)."*

### L2 — m48's anchor line says every expanding verb "returns the bound per-label shape", which is false for `read_columns`

**Section:** m48 anchor bullet "§2.3d module-verb dispositions" (`:2300`), vs §2.3d (`:562-565`) and §5.3.

**Detail.** §2.3d's own parenthetical is per-verb and correct (`apply` → a `Varied`; `read_columns` →
*the union over all labels' members*), but the m48 anchor collapses both into *"the bound **per-label**
shape"*. A test-author working from the anchor could freeze `read_columns(varied_outputs)` returning
`{label: …}` — which contradicts §2.3d and duplicates the separate m49 per-label projection-stats verb
(§5.3), one milestone early and read-only.

**Suggested fix.** Word the anchor per verb: *"`apply` returns a `Varied`; `read_columns` returns the
single union read set (§2.3d), NOT a per-label mapping — that is §5.3's separate m49 verb."*

### L3 — §9.1's plan-level `{output: [labels]}` anchor freezes an unresolved either/or

**Section:** §9.1 / m50 anchor (`:2727-2732`).

**Detail.** The new m50 anchor requires *"the unvaried output maps to the **empty/`["nominal"]`** shape
§6.1a's bare-`hist` rule implies"*. `[]` and `["nominal"]` are different frozen assertions and §6.1a
does not settle it (it settles the *histogram* shape, not the listing's). Same class as the defects r12
and r13 fixed elsewhere ("a no-op … or a refusal", "the two are not interchangeable").

**Suggested fix.** Pick one — `["nominal"]` is the consistent choice, since §6.1a already binds a bare
`hist` to "read as the single label `nominal`" through the narrowing helper — and delete the slash.

### L4 — §6.4b's "every stored field **whose value differs per label**" reads data-dependently; a per-partition decision would diverge the parquet schema across parts

**Section:** §6.4b, §6.4c, m51 representation anchor.

**Detail.** The deltas are computed in `_WritePart` on evaluated buffers (§6.4c r14), i.e. **per
partition**, so a literal reading of "whose value differs per label" makes the augmented column set
data-dependent: partition 0 (where a label happens to agree with nominal everywhere) writes fewer
columns than partition 1, giving parts with different schemas and different manifests in one dataset.
m51's own anchor settles the intent the other way — *"a label structurally equal to nominal (all-zero
delta)"* is written — so this is wording, not a design conflict, but m51 freezes the file layout.

**Suggested fix.** Say "every stored field that **is `Varied`** (structurally, at record time)", and
state that the augmented column set is identical across partitions by construction.

### L5 — §6.1c's "per-slot VALUE TYPE is recorded in the layout and the combine branches on it" is not needed under the keying §6.1c itself binds

**Section:** §6.1c (m48 sibling half / m50 axis half).

**Detail.** Under the bound keying every slot's value is a plain `bh.Histogram`: a sibling slot is
`(output, label)` → one histogram; an axis-mode slot is `(output, None)` → one histogram carrying the
variation axis. What actually varies per slot is the **spec**, which §6.1c already binds separately (the
fill node's spec). Measured, `_add_groups` is a key-wise `+`
(`graphed-histogram src/graphed_histogram/boost.py:120-122`) and needs no branch; the information the
**frontend unpacker** needs is the per-OUTPUT *mode* (to choose between `{label: hist}` and a bare
histogram in §6.1a/§6.2(i-bis)), not a per-slot value type in the reducer.

**Suggested fix.** Move the requirement to where it bites: the layout records the per-**output** mode
(sibling / axis) for the frontend unpack; drop "the combine branches on it".

### L6 — §6.4a(2a) does not say how "the supplied mask **is** `graphed.selection(c)`" is decided

**Section:** §6.4a predicate (2a) (record-time), m51 entry-check anchor.

**Detail.** The record-time lineage predicate compares a user-supplied `Varied` mask against the mask a
context retains. Object identity and per-label node-id equality give different answers for a legal
program: a user who re-records the same selection expression (`select=(gak.num(jets) >= 4)`) gets a
*different Python object* that interns to the *same node ids*. Under identity the write is refused;
under node-id comparison it is accepted. m51's anchor ("round-trips identically to the same skim written
with the mask passed by hand") uses the same object either way, so the freeze does not disambiguate and
an implementer must guess.

**Suggested fix.** Bind the comparison as **per-label node-id equality against the retained mask**
(identity is a sufficient fast path), so a re-recorded but structurally identical mask is accepted.

### L7 — §2.1: `nominal=` is bound in overload (b) and refused in (a), but undefined in the shift form (c)

**Section:** §2.1.

**Detail.** §2.1 binds *"`is_weight=True` and `nominal=` are invalid here"* for overload (a) and defines
`nominal` as the central weight factor for (b). For the shift form (c) the collections' central members
come from the target context, so `nominal=` has no meaning — but nothing says whether
`graphed.vary(events, "jes", nominal=X, Jet={...})` is an error (it is one of the four shadowed names,
so it cannot be a tag). m48's grammar anchor covers the four shadowed names but not this.

**Suggested fix.** One clause: `nominal=` is REJECTED in the shift form (c), with an error naming
`collections=` — mirroring the existing `variations=`-in-(c) refusal.

---

## Probed and found clean (no finding)

Stated so the next round does not re-walk them; each was checked against the code, not read past:

- **§2.4 label-aligned union vs §2.6c lineage unification** — coherent end to end. A derived context's
  ambient registry acquires the mask's labels through the §2.4 union (fallback-to-nominal covers
  ambient labels absent from the mask and vice versa), and `graphed.labels(ctx)`'s three-term union
  (§2.2 r13/r14) is exactly that set. Per-label row counts line up at the fill for both the
  weight-label and shift-label halves.
- **§2.1 stacking (weight-on-shift) and the r16 reverse ordering rule** — the `old_ambient[L] × factor[L]`
  rule needs no extra machinery: the factor is itself `Varied` when it reads a varied collection, so
  §2.4 supplies `factor[L]`; the shift-after-weight case is correctly diagnosed rather than silently
  repaired, and §3.4's reachability machinery is the right operand (m49, where §3.4 lands).
- **§6.1d ambient broadcast vs §2.4 with mixed loose/contexted inputs** — the fold order (axis args →
  ambient → explicit factors → `sample=`) is total and deterministic; the loose-value row-space carve-out
  and its distinct message are consistent with the execution-time refusal contract. Verified
  `Histogram.fill` appends `sample` to the same `inputs` list with no type check
  (`graphed-histogram src/graphed_histogram/boost.py:160-178`), so the r15/r16 `sample=` binding is
  well-founded.
- **§4.3's r16 replacement predicate** — implementable exactly as bound: `n_axes` IS a recorded param
  and the axis args ARE the leading `inputs` prefix (`boost.py:176-212`, read in session), and the
  predicate genuinely fails a `mask_L = mask & g_L` implementation (the axis arg's node id changes)
  while the withdrawn intersection form passes it.
- **§6.4 structure rule vs jagged object-level migration** — the per-level `select=` channel, the
  never-apply-inner-masks rule, the offsets refusal and the XOR/packbits reconstruction compose
  correctly; a record read through a varied-selection context is refused by predicate (1) rather than
  silently written, which is the right outcome.
- **§6.4a's two absent-operand cases, the `vary`-identity-link transitivity (r16) and
  `graphed.selection`'s three per-link-kind answers** — mutually consistent, including the chained
  `sel2 = sel[mask2]` refusal and the canonical `to_parquet(events.Jet, select=graphed.selection(sel))`
  spelling.
- **§5.4 boundary refusal vs §6.4 write plans** — no interaction: the write path builds its own
  `write_plan` and `to_parquet` already requires exactly one source
  (`python/graphed/awkward/io.py:206-274`, read in session).
- **numpy-backend exemptions** — §6.4f (the numpy-idiom write refuses, no `read_varied` counterpart) and
  §6.1d (the numpy `broadcast_like` is a bound no-op) are consistent with `to_parquet` being
  awkward-idiom only (`python/graphed/awkward/__init__.py`, `python/graphed/numpy/io.py:158-173`).
- **Package-boundary / factorization compliance** — clean. No binding requirement puts awkward or
  `boost_histogram` behind a neutral namespace: §6.1d's seam is neutral with the awkward implementation
  in `graphed.awkward`, §6.2(i-bis) slices by integer index with duck-typed detection, §6.4e's reader is
  awkward-idiom, and no rule pushes variation awareness into `graphed-core` (§3.1's one addition is a
  read-only accessor).
- **Milestone boundaries** — m48/m49/m50/m51 target lines now agree with the section targets they cite
  (incl. r16's §6.1c-axis-slot move to m50, §3.4 → m49, §9.1's per-verb milestone split, and the
  refusal-contract split between m48 and m49). The only residual is H1's: §7.2 is m48 while the accessor
  that makes its binding sound is m49.

---

## Verdict

**DIRTY — one HIGH, six MID, seven LOW.**

The plan is in good shape: at r16 the specification is internally consistent across the interactions
this lens probed hardest, and the newer surfaces (§2.6 functional context, §6.1d, §6.4/m51, §1.1's
e-canonicalization) hold up under adversarial reading. The one finding that must not be waved through is
**H1**: a measured second collapse mechanism (the M4 reducer's identity/commutativity rewrites, not
record-time interning) breaks §7.2's positional derivation on a program the plan's own §1.1 names as
motivating (a μR/μF family containing a `× 1.0` member), and the map that fixes it is scoped one
milestone later than the requirement that needs it. The MIDs are all one-or-two-sentence repairs; none
touches an owner-locked decision.
