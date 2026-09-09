# m57 — the weight form's nominal names the factor being varied (dedupe by node)

Owner decision (2026-09-09): the ambient weight must not multiply a factor in twice when a
registration's nominal is a weight already in the ambient. Both idioms are to be correct: a family
that re-uses an absolute weight (the b-tag SF central) as its starting point along another path,
and a relative-delta ("shift-style") family whose members are the whole ambient rescaled.

## §1 The gap (measured, `scratchpad/dedupe/probe.py` on main 3b00157)

`_vary_weight` appends every registration's nominal as a new factor and `_compose` multiplies all
factors, with no identity detection. With `SF = [1, 2, 4]`:

- (a) two families on the same central node (`hf` then `lf`, both `sf`): nominal `[1, 4, 16]`
  (SF²), `hf_up = 1.1·SF²`, `lf_up = 1.2·SF²`; physics: SF once, `hf_up = SF(up_hf)`,
  `lf_up = SF(up_lf)`.
- (b) the tour idiom, the ambient as the next family's nominal (`mu` with `weight(c1)`,
  `up = ambient * 1.05`): nominal SF², `hf_up = 1.21·SF²` (the hf member is read through both
  factors), `mu_up = 1.05·SF²`; physics: nominal SF, `hf_up = SF(up_hf)`, `mu_up = 1.05·SF`.
- (c) a masked child of (a)'s first registration, `lf` registered on the child with `sf`: SF² on
  the child's rows; the child's single factor is the adopted composed container, whose nominal
  node equals the re-indexed `sf` node (one parent factor).
- (d) a masked child whose parent carries two factors (`pu = 0.5`, `hf` on `sf`), `lf` on `sf` at
  the child: nominal `[2, 8]` where physics gives `pu·SF = [1, 2]`; here `sf` is no factor node of
  the child at all — it is inside the adopted product.

- (e) the two idioms in sequence (`scratchpad/dedupe/absorbed.py`): `pu` and `hf` on `sf`, then
  `mu` on the ambient, then `lf` on `sf` — a design that folds the ambient into one container when
  `mu` registers loses the names of `pu` and `hf`, and `lf` squares `sf` again (nominal
  `[0.5, 2, 8]` for `pu·SF = [0.5, 1, 2]`).

No frozen or extra test registers the ambient as a nominal (grep, 0 hits); tour cells 14, 34, 36
and 38 do (only labels are printed in 14 and 38, and every printed line of the four cells is
unchanged by the design — their values are). Two frozen m56 tests and three extra tests build two
families on one central node (§2.6).

## §2 Contract

1. **The nominal names the factor.** The ambient weight is a registration-ordered list of
   OPERATIONS: a *factor* multiplies its two-level member at the label, an *overlay* — a family
   whose nominal named the whole ambient — replaces the running product at every label its family
   has a coordinate on and leaves every other label alone. In the weight form the central is
   compared BY NODE (§2.3) against the nominal of every live factor and against the composition's
   nominal, decided before anything is minted:
   - **new**: no match — a new factor is appended, exactly as today;
   - **joins a factor**: the node is a live factor's nominal — the family's members join that
     factor's container as its values in their universes; the factor keeps its position, its tag
     map gains `name`, and the composition at `name_t` multiplies the member ONCE with the other
     operations (the absolute-weight idiom: `hf_up = SF(up_hf)`, `lf_up = SF(up_lf)`, nominal
     `SF`). The container's NOMINAL MEMBER becomes the UNION of the two centrals' coordinate universes:
     the shared node at `nominal`, and at every coordinate either central declares (a central built
     over shifted objects is a container whose universes ARE the weight's dependence on that shift,
     one level below the family's own labels, where `_two_level` reads them) that central's
     universe — so the ambient reads the weight at each label's own objects whichever family
     registered first. A coordinate both centrals declare with different nodes is refused before
     anything is minted, naming the family, the coordinate and both member-node tuples. A union
     that would ADD universes to a nominal member an overlay was read over is refused too (the
     overlay's members are the composition the user read, and that composition would change
     underneath them), naming the overlay family and the order that works: the absolute family
     first, the relative-delta family on a handle read after it;
   - **overlay**: the node is the nominal of a composition this lineage has READ — the current
     one, or an earlier one whose FACTORS are a prefix of the live factors (overlays never change
     the nominal, so those already inserted among them do not count) — and no live factor's: the
     family's members are that composition in their universes (the relative-delta idiom:
     `mu_up = 1.05 · P` is the member node itself). The overlay is placed right after the last
     factor it was read over and after any overlay already anchored there, so a factor registered
     after the read or after the overlay multiplies its result (`w = weight(ctx)` over `pu, hf`,
     then `trig`, then `mu` on `w`: `mu_up = 1.05 · pu · SF · trig`), and a family that later joins
     a factor registered before it keeps that factor's slot, so the overlay still replaces the
     product of the factors it was built from (§1(e): `lf_up = pu · SF(up_lf)`,
     `mu_up = 1.05 · pu · SF`). The read that minted the handle is what records the composition,
     so inserting or removing a `weight()` read between registrations changes no decision and no
     value, and neither does the order of two relative-delta registrations on handles read at
     different times. A handle read before a join that added universes to a nominal member it was
     read over is STALE and refused, naming the read to repeat (`weight(ctx)` after the join): its
     universes are no longer the composition's. With one live factor the factor outcome answers
     first and the two coincide (its nominal IS the composition's), so an overlay exists only over
     two or more live factors. A joint of two overlays is composed (m56) and, when placed, reads
     the later overlay's member two-level, which carries the earlier overlay's delta only if its
     handle was read after that overlay registered.
   Two families on one factor share its container, so a JOINT label of the two reads that container
   two-level: the cross member the fanned-out family minted for that point (in m56's fixture
   `hf_up__jes_up = SF(jes_up jets, HF-up table)`), and the other family's one-at-a-time member is
   NOT also multiplied in — both are absolute values of one weight, and their product is the
   squaring this milestone removes. A joint that carries both variations is spelled by building
   the cross members from the other family's varied member (the ratio idiom), which m56 composes
   and a `points=` placement keeps. The comparison is node identity, never value: a different
   expression with equal values is a new factor (§1(a) with a recomputed `sf` stays a product),
   which the docs say.
2. **Two-level reads are preserved.** A member built from the ambient container
   (`weight(ctx) * 1.05`, a `Varied` over the ambient's labels) is read at a joint label through
   its own coordinate (`_two_level`), so `hf_up__mu_up` is `P(hf_up) · 1.05`; a member built from
   shifted objects is read as today. The m56 composition test (`AmbientCarrier.resolve` over the
   lineage factors) sees an extended container as one factor and an overlay as a factor whose
   varied members are the ambient's values at its labels, and decides as before: members computed
   from the ambient are composition, members reached through shifted objects fan out — including
   the members of a family that extends a factor (§4's extend-and-fan-out leg).
3. **Lineage, and what "the same node" means.** The candidates are the LIVE operations — the
   ones whose composition IS the context's ambient, in registration order: a row-space change
   adopts one composed container that stands for the adopting parent's own live list, and the walk
   goes back through such adoptions (never `_lineage_factors`, which also answers with containers an
   extension has since replaced and with the adopted products themselves). A family registered on a
   mask-derived child therefore extends the parent's factor: the child's adopted product is replaced,
   for that context, by the parent's live operations re-indexed to the child with the matched one
   extended, order and kinds preserved, plus whatever the child registered after the adoption
   (§1(c), (d): nominal `[1, 2]`, `lf_up = [1.2, 2.4]`). Two handles are the same node when their
   node ids are equal AND no mask link lies between their contexts on one lineage: a mask makes
   one id two values (the only container that can match across it is the adopted one, which sits
   in the child's own list), while a `vary` link and a projection to the NOMINAL universe keep the row space and the
   identity, so a central re-derived at `graphed.nominal(ctx)` interns to the parent's node and
   names the parent's factor; a projection to any other universe re-indexes each entry to its
   member there, so, as across a mask, the only candidate is the adopted entry. Nothing is composed or re-indexed to DECIDE: a central re-indexed for
   the comparison or an ambient composed for it would mint nodes on programs that name nothing,
   shifting every later node id and the fold memo (§2.6). The compositions a central can name are
   those a read has recorded on the lineage (nominal node and the entry slots it composed); a
   central nested past §2.2's one level names nothing (the form check reports it as today).
4. **Kinds, records, diagnostics.** `variations(ctx)` reports the extending family as
   `Kind.WEIGHT` (union with `SHIFT` under name identity); `_weight_tags[name]` is written as for
   a new factor; the §2.5 shift-after-weight diagnostic names a family that joined a factor when the objects
   its members read are later shifted, as it names a new factor (`_weight_factors` carries the
   joined container's, or the overlay's, member nodes); `labels(weight(ctx))` gains the family's labels in
   registration order. Name identity composes with extension: a `jes` weight whose nominal is `hf`'s central
   extends that factor, so `jes_up = SF(up_jes)` alone inside the jes universe.
5. **Refusals and knobs unchanged.** `check_family`'s repeated-tag refusal, the "label already
   carried" refusal, `nominal=` in the shift form, `composes_as_union`, `points=` declares and
   placements, `max_universes` and the m53 fan-out all behave as today; a refusal after the match
   leaves the operation list, its member nodes and the registries exactly as before the call (the
   §4.5 rollback's epoch bump already remakes the memo container, as for any refusal).
6. **No silent change.** A program whose registrations never re-use a nominal node serializes
   byte-identically to today, node counts included (the operation list and every minted node are
   unchanged for it). The programs that change are exactly those §1 describes. Two frozen m56 tests
   are Test Disputes (`.graphed/m57/disputes/`, decided by the owner): the joint-oracle test pins
   the ambient's nominal as `SF²` and the joint as the product of two absolute members, because the
   fixture's JES and HF tables share the nominal `1.0` and the two centrals intern to one node; the
   label-precision test builds its probe from the second family's nominal re-evaluated on the shifted
   jets, a node that is no longer in the shared container, so the probe's `jes` coordinate is a
   dependency and fans out. No other frozen test changes outcome; m56's order-independence property — the label set and every label's value — holds under the
   join because the joined nominal member is the union of the centrals' coordinates (symmetric),
   which §4 pins with a weight the shift moves; the two orders agree on every member's serialized IR as well, and only the session-local node
   ids differ. Three extra registration-refusal tests deliberately build two
   factors from one expression to provoke a product-form clash; they are given distinct centrals by
   the implementer, which keeps the property they test.
Out of scope: dedupe by value; extension across two DIFFERENT centrals of one SF table (a family
whose nominal is `SF(central)` computed from other jets is a new factor); a family whose nominal is
a varied MEMBER of the ambient (`universe(weight(ctx), "mu_up")`) — a new factor, as today; changing
what a shift family's `nominal=` may be.

## §3 Design

In `python/graphed/context.py`, `_factors` becomes the operation list, each entry in a SLOT
(`_slots`, parallel ids minted at append: a join replaces the object in its slot, an overlay takes
a new slot inserted after the entries it was read over); the overlays are named by slot in a
context set (`_overlays`). Every return of `_ambient_weight` (a fresh composition, a memo hit, an adopted member) records
on the context (the handle's member nodes, the LIVE factor slots it stands for, their generations)
in `_reads` — keyed by the whole member map, since a join leaves the nominal node alone and a
nominal-keyed record could not tell a stale handle from a fresh one. A factor slot's generation
counts the unions that added universes to its nominal member (never node stamps, which a
re-index at a masked child would also move), so a record whose generations no longer match is
stale; the factors an overlay covers are those before it in the live list, so nothing is stored
for it — which a `vary`
link SHARES with its parent (one row space, so a handle read at the parent after the child was
built still decides at the child, and a divergent branch's slots can never prefix another's);
`_child_of` copies `_slots` and `_overlays`; `_adopt_ambient` resets all three (a row-space change
makes every earlier id a different value; the adopted container is one entry standing for the
parent's live list, which `_live_factors` walks back through, as it walks through a projection's).
The overlay's position is after the prefix's last factor slot and any overlay already anchored
there when that slot is the context's own, and right after the adopted head (and its anchored
overlays) when the context adopted; any other prefix answers no match.
`_compose` (told the overlays by slot, mapped to the entries it holds) composes each product RUN
between overlays with today's balanced tree (so a program
without an overlay is byte-identical to today, node counts included, and an overlay leaves the
cost class of the tree) and applies the overlay by replacement at the labels its family covers (an
entry whose two-level member at a label is its nominal has no coordinate there, the test the tree
walk already makes). The fold memo is unchanged for appends: a new factor folds onto the
overlay-applied composition, a new overlay at the end of the list replaces the folded composition
at its own labels; a join, or an overlay inserted before the end, drops the memo so the composition
is remade from the list. `_check_forms` walks what the read composes, so it takes the slots and
overlays too.

In `_vary_weight`, before `gather_members`, `_extension(ctx, central)` answers `("factor", slot)`
for the first live factor whose nominal is `_same_node` with the central's nominal
(`_two_level(central, "nominal")`; a `Varied` answer names nothing), else `("ambient", slots)` for
a recorded read whose nominal is that node and whose factor slots are a prefix of the live factor
slots (a stale record — a generation moved — is refused at the registration, naming the family and
the read to repeat), else
`None`. `_same_node`: equal node ids, then the two handles' contexts on one lineage with no mask
link and no projection to a non-nominal universe between them. Minting is unchanged. Then `_extend` builds the new list: an overlay inserts the
family's container (nominal = the recorded composition's nominal node, members = the family's)
after the last slot of the prefix; a join replaces the slot's container by `_joined(factor,
central, members)` — the union nominal (§2.1: the shared node at `nominal`, each central's
universe at the coordinates it declares, a coordinate both declare with different nodes refused
before anything is minted), the factor's members plus the family's, its tag map plus `name` — in
`ctx`'s own list or, for an ancestor's slot, in the re-indexed live list (each re-indexed entry
already carries the tags a mask leaked in). A union that adds universes to a nominal member some
overlay is anchored after is refused before anything is minted; the two refusals are the two
orders of one program, and each names the other order as the one that works. `_weight_tags`, `record_labels`,
`_weight_factors` and `_recorded` are written as for a new factor; the child's `_adopted` survives
only while the adopted container is still the list's head. The prototype is
`scratchpad/dedupe/prototype.diff` (branch `dedupe/prototype` of the m52 clone).

Docs: `docs/frontend/design.rst`'s weight-form section states the rule (the nominal names the
factor; the three outcomes; node not value; the union nominal; the joint of two families on one
factor; a read records the composition a handle names) with an executed example of both idioms
printing the nominal and one universe each.

## §4 Frozen suite (test author, isolated; `tests/frozen/awkward/m57/`, `m57_` prefix)

Fixtures follow m53's tree; every new behaviour is reached inside test bodies so the tree collects
on a pre-m57 tree and fails at run time on the squared values. One test per property:

- two families on one central: every universe's weight equals the one-SF oracle by value, and the
  nominal universe's weight is the central node (node identity);
- the ambient as nominal over two factors: `mu_up` is the member node itself, `hf_up` and nominal
  unchanged from the context before the registration (values and nodes); then a family on one of the
  absorbed centrals (§1(e)) and a new factor after the overlay, each universe against the one-SF
  oracle (`lf_up = pu · SF(up_lf)`, `mu_up = 1.05 · pu · SF · trig`);
- the handle's read decides nothing: a join that leaves the nominal member unchanged followed by a
  relative-delta family on a handle read BEFORE the join, spelled with and without an intervening
  `weight()` read, gives the same one-SF universes and the same ambient nominal node; a handle read
  over a prefix (`pu, hf` read, `trig` registered, `mu` on the handle) gives `mu_up = 1.05 · pu ·
  SF · trig` and `trig_up` unchanged; two relative-delta families, one on an older handle and one on
  the current composition's, agree universe-by-universe in both registration orders and both read
  spellings; the same at a masked child whose adopted ambient was read before a factor was
  registered there (the read that returns the adopted member, then the overlay after the head);
- staleness is loud: a join whose union adds a shift universe to a nominal member (a jes-varied
  second central) is refused when an overlay was read over that factor, and a handle read before
  such a join is refused as a relative-delta nominal, each error naming the order that works; the
  same program with the handle read after the join gives `mu_up__jes_up = 1.05 · jes_up` (an SF the
  shift moves, so the joint discriminates);
- two centrals sharing a nominal node with different shift coordinates (one on the nominal jets,
  one on the jes-varied jets), registered in both orders, agree universe-by-universe with the one-SF
  oracle read at each label's own jets, and the same coordinate declared by both with different
  nodes (two loose-form containers on one central with different `up` members) is refused before
  anything is minted; the m56 capstone shape with a weight the shift MOVES
  (a pT-dependent SF) minting the same labels and per-label values in both registration orders;
- a joint of two families on one factor is the container read two-level at that label — the
  fanned-out family's cross member (the m56 fixture's shape, the oracle `SF(jes_up jets, HF-up
  table)`), beside the ratio spelling whose placed joint carries both variations;
- a family extending a factor still fans out over the shift its members read (labels and the
  one-SF oracle at each joint's own jets);
- an overlay leaves the composition's cost class: with one overlay inserted among F factors, the
  composition work of the ambient read (the operations recorded on the Session during it) stays
  within a constant factor of the same read over the F factors alone across a range of F wide
  enough that a walk re-multiplying the list per label leaves it (interning makes minted-node
  counts blind to that walk, so the leg counts recorded operations, with the minted nodes pinned
  only as a ceiling: the plain read's plus one product per label plus the overlay's members), and
  every universe's value is the tree's product rescaled;
- lineage: one parent factor and two parent factors, the second family registered on a masked
  child, values against the one-SF oracle on the child's rows; the parent's ambient is unchanged;
  the same central re-computed at the masked child, and a central that is a nested container, are
  new factors (controls); at `graphed.nominal(ctx)` over two factors a central re-derived from the
  projected collections interns to the parent's node and joins (one-SF oracle), while at
  `graphed.universe(ctx, L)` for a weight label `L` the same registration leaves the projected
  ambient's nominal universe unchanged in value and node;
- node identity, not value: a recomputed central with equal values is a new factor (values are the
  product — today's answer, the control);
- name identity extends: a `jes` weight registered on `hf`'s central inside a jes-shifted context
  gives `jes_up = SF(up_jes)` alone, and m56's fan-out over the shifted jets still mints its joints,
  each read two-level from the one container;
- relative-delta members over an ambient that carries another family's labels: `hf_up__mu_up`
  absent (composition), `mu_up` exact, `hf_up` unchanged;
- `variations` reports the extending family as `Kind.WEIGHT` with its tags and `labels(weight(ctx))`
  keeps registration order (guards the join path's record writes); the shift-after-weight
  diagnostic names a family that joined a factor when its members' jets are later shifted;
- transactional: a refused registration (repeated tag) after a match leaves `weight(ctx)` node- and
  label-identical to before;
- determinism: the extending program serializes byte-identically across two Sessions, and a
  program that names nothing serializes byte-identically to its pre-m57 answer, node count included
  (the pinned bytes regenerate from the test's own program, not from a stored blob).

## §5 Work items and gates

| item | what | where |
|---|---|---|
| W1 | the operation list, `_extension`/`_same_node`/`_live_factors`/`_extend`, the adopted-container marker and the overlay set; the three extra refusal tests re-based on distinct centrals and the `_check_forms` spy's arity | `python/graphed/context.py`, `tests/extra/awkward/test_weight_registration_refusals.py`, `tests/extra/frontend/test_weight_composition.py` |
| W2 | executed docs example | `docs/frontend/design.rst` |
| W3 | frozen suite (test author); the two m56 disputes re-frozen on the owner's affirmation | `tests/frozen/awkward/m57/`, `tests/frozen/awkward/m56/`, `.graphed/m57/disputes/` |
| W4 | tour: cells 14/34/36/38 re-executed (their printed lines are unchanged, their values are not); the Level 6/17 markdown states the rule | `coffea-benchmarks-graphed-mvp/graphed-vary-systematics-tour.ipynb` |
| W5 | systematics plan §2.1(b) weight-form paragraph states the nominal rule; root prompt R24.5; memory `weight-form-factor-semantics.md` retired | `graphed-workdir/systematics-vary-plan.md`, `graphed-root-prompt.md` |

One implementation commit (W1+W2) and the test commit; W4/W5 land with the pin bump. Gates as for
every milestone: frozen suite green and unmodified, `scripts/run-tests.sh` all green, diff coverage
≥ 90 % line+branch from the frozen suite, ruff/format/mypy strict clean, Sphinx `-W` clean,
determinism.
