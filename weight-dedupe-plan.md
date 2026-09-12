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

The frozen m52 point fixtures, the m53b off-grid fixtures and one m53 extra test register a
`graphed.weight()` handle as a nominal, every one over ONE live factor (the set regenerates from
`scratchpad/dedupe/handle_centrals.py`, an AST walk binding names assigned from `*.weight(...)`
and reporting the `vary(..., is_weight=True)` calls whose central is such a name); their ambients
change value under the design while what they assert — labels and points — does not (§2.6). Tour
cells 14, 34, 36 and 38 do too (only labels are printed in 14 and 38, and every printed line of the
four cells is unchanged by the design — their values are). Two frozen m56 tests and three extra tests build two
families on one central node (§2.6).

## §2 Contract

1. **The nominal names the factor.** The ambient weight is a registration-ordered list of
   OPERATIONS: a *factor* multiplies its two-level member at the label, an *overlay* — a family
   whose nominal named the whole ambient — replaces the running product at every label its family
   has a coordinate on and leaves every other label alone, except a universe another family PLACED
   at a point carrying that coordinate (`points=` with a coordinate map, the tour's diagonal
   `scale_upup` over a `muR` factor and a relative-delta `muF`): the member declared there is the
   user's value for that point, and the join reads the same member two-level, so the two outcomes
   agree there as everywhere. In the weight form the central is
   compared BY NODE (§2.3) against the compositions this lineage has READ and then against the
   nominal of every live factor, decided before anything is minted — the read first, because a
   handle over ONE factor carries that factor's nominal as its own, and joining it would union the
   handle's labels into the factor's nominal member: the same nodes under new coordinates, a
   widening in name only that moves the slot's generation and fires both §2.1 refusals on
   programs this section admits:
   - **new**: no match — a new factor is appended, exactly as today;
   - **joins a factor**: the node is a live factor's nominal and no read recorded it — the family's members join that
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
     and so does an adoption at a row-space change, which records the adopted member as the
     child's own read (§2.3), so inserting or removing a `weight()` read between registrations —
     at the parent or at a child — changes no decision and no value, and neither does the order
     of two relative-delta registrations on handles read at different times. A handle read before a join that added universes to a nominal member it was
     read over is STALE and refused, naming the read to repeat (`weight(ctx)` after the join): its
     universes are no longer the composition's, and a stale record is refused even where the
     factor outcome could answer (its members lack the universes the join added). A handle read
     over one factor is an overlay anchored after it, and its every value equals the join's. A
     joint of two overlays is composed (m56) and, when placed, reads
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
   names the parent's factor; a projection to any other universe `L` keeps the entries' identity
   too (it re-indexes the composed product, not the nodes a central names), so a central built
   above the projection names its factor there as at the parent, and an expansion at the
   projection re-indexes each entry to what the ambient at `L` READS of it, decided from the
   entry's RIDER (§3: what an entry is, kept beside its slot and never read off a re-indexed
   object): a factor to its two-level member at `L` (a factor over shifted objects carries its
   dependence on a shift label one level down, so `L` a shift label keeps it) — except the factor
   that OWNS `L` (a family of its rider is a coordinate of `L`'s point, so a joint or placed label
   has several owners): its member at `L` is the universe projected into, not the central, and
   naming it there is refused — and the rider records every entry's member at `L`, so a central
   node-identical to a recorded member, however built — at the parent (the node handed to
   `vary()` as the owner's `up=`, or the SF over the parent's shifted jets), at the projection,
   or after an unrelated expansion — names the entry as it stands at `L`: refused when the
   entry owns `L`, joined when it does not (inside `jes_up` the SF re-derived over this
   context's shifted jets is the jes-dependent factor's member there and joins it; a new factor
   would square it), in both registration orders, whatever else was registered at the
   projection before it (a central re-derived from the projected collections that interns to
   the parent's NOMINAL node is not a recorded member and stays a new factor, §4's control).
   Below stacked projections the context is still inside every universe projected into, so
   ownership is tested against ALL of them — the owner of an outer universe named by its
   recorded member is refused below a further projection exactly as it is when named by its
   nominal — while the member matched is the one the entry became at the innermost label (for
   an entry re-indexed once, the same node at every label below). A node that is both a live
   factor's nominal in the central's own row space and another entry's recorded member is
   decided by the nominal first: it joins that factor, in either registration order, since the
   join keeps the universe projected into and the refusal would not; an overlay whose family has a coordinate on `L` to its member
   there, which then replaces the running product of its prefix at every value (inside its own
   universe every value is that universe), so an operation that would land INSIDE the factors it
   covers — a family joining one of them, a handle read over a strict prefix of them — is refused
   there (the overlay's member is the user's node over the old product, and nothing is minted to
   re-derive it over a new one), while a family joining a factor registered after the overlay
   multiplies its result as at the parent; an overlay that no earlier projection fixed and that
   has no coordinate on `L` contributes nothing at `L` and is left out, while an overlay already
   fixed stays fixed through every further row-space link and is never re-tested against its
   re-indexed member. The refusals name the spellings that work: register the
   family, or read the handle, at the parent before projecting; or read the handle at the
   projection, whose record is the projected composition's — and the adoption itself records
   the adopted member as the child's read, so a family whose nominal is that node, whether the
   handle was read at the projection or `universe(weight(ctx), L)` was built at the context the
   projection is taken from, is an overlay after the head with or without a read in between
   (built above a mask that lies between, that expression is the adopted node only while the
   masked child registered nothing before the projection — the child's head is then the parent's
   composition on its rows — and is an overlay there too; once the child registered a factor its
   head is another node and the expression stays a new factor as today, Out of scope's clause). A handle read above the projection
   over the whole head anchors after it as at any row-space change, the projected nominal
   unmoved; over a strict prefix it expands the head as a join does, under the same rules. A handle READ at
   an ancestor before a row-space change is matched at the child as any record is — its factor
   slots a prefix of the live factor slots, its generations current — because the adopted head
   stands for the ancestor's live factors and their generations at the adoption, and an expansion
   of the head (a family joining an ancestor's factor, §1(c)/(d)) leaves those slots and
   generations in the child's own list, re-indexed — each re-indexed entry keeping the nominal it
   had in every row space it came through, so a central built at an ancestor still names its
   factor after the expansion (the factor arm compares the central against the nominal the entry
   had in the central's own row space): a second family naming the ancestor's factor at the
   masked child joins it as the first did, and a family joining an ancestor's factor after a
   strict-prefix crossed overlay joins it as it would before, both orders agreeing at the masked
   child (at a nominal projection the crossed overlay contributes the parent's labels as
   dependencies only while the head is unexpanded, so the two orders' label sets differ there
   while every shared label's value agrees). A record equal to the head's tuple is an
   overlay anchored right after the head, its nominal the head's node (the handle's own node at a
   nominal projection; that node re-indexed across a mask, as the family's members are): the
   tour's `w = weight(ctx)`, then a cut, then `mu` on `w` at the child — with or without a family
   that joined an ancestor's factor at the child in between, in either order. A record that is a
   strict prefix of the head's tuple expands the head exactly as that join does (the ancestor's
   live operations re-indexed to the child, order, kinds and slots preserved) and anchors after
   its prefix, its nominal the recorded composition's node re-indexed. A record whose generations
   are not the child's — a handle read over a factor a join later widened, the cut taken after the
   join — is stale and refused as at the parent, naming the read to repeat at the registering
   context; a handle read on a branch that diverged from the child is refused by the row-space
   check as today. Nothing is composed or re-indexed to DECIDE: a central re-indexed for
   the comparison or an ambient composed for it would mint nodes on programs that name nothing,
   shifting every later node id and the fold memo (§2.6). The compositions a central can name are
   those a read has recorded on the lineage (nominal node and the entry slots it composed); a
   central whose own member at `nominal` is a container (nested past §2.2's one level, buildable
   only through the public `Varied(...)` constructor) names nothing, and the form check refuses it
   as today.
4. **Kinds, records, diagnostics.** `variations(ctx)` reports the extending family as
   `Kind.WEIGHT` (union with `SHIFT` under name identity); `_weight_tags[name]` is written as for
   a new factor; the §2.5 shift-after-weight diagnostic names a family that joined a factor when the objects
   its members read are later shifted, as it names a new factor (`_weight_factors` carries the
   joined container's, or the overlay's, member nodes); `labels(weight(ctx))` gains the family's labels in
   registration order. Name identity composes with extension: a `jes` weight whose nominal is `hf`'s central
   extends that factor, so `jes_up = SF(up_jes)` alone inside the jes universe.
5. **Refusals and knobs unchanged.** `check_family`'s repeated-tag refusal, the "label already
   carried" refusal, `nominal=` in the shift form, `composes_as_union`, `points=` declares and
   placements (a placed universe keeps its declared member under an overlay whose coordinate its
   point carries), `max_universes` and the m53 fan-out all behave as today, with one repair the
   work uncovered: a placed universe minted AFTER an ambient read resolves to its point — the
   pre-m57 fold onto the memoised composition froze it at nominal, because a composed container
   restricts the label's point to its merged axes and matches no own label
   (`scratchpad/dedupe/review/whole/compose/P18_foldfreeze.py`, main gives the frozen value with
   the read and the declared one without); a refusal after the match
   leaves the operation list, its member nodes and the registries exactly as before the call (the
   §4.5 rollback's epoch bump already remakes the memo container, as for any refusal).
6. **No silent change.** A program whose registrations never re-use a nominal node serializes
   byte-identically to today, node counts included (the operation list and every minted node are
   unchanged for it), except one that reads the ambient and then mints a placement the memoised
   composition cannot resolve — the §2.5 repair composes it from the list. The programs that change
   are exactly those §1 describes, that one, and the registrations at a projection to a
   non-nominal universe §2.3 decides — a central naming an ancestor factor, a handle read above
   the projection over a strict prefix — which today multiply the factor in again without a
   word, and are now joined once or refused (the owner of `L`; inside an overlay's own universe,
   an operation inside its prefix). Two frozen m56 tests
   are Test Disputes (`.graphed/m57/disputes/`, decided by the owner): the joint-oracle test pins
   the ambient's nominal as `SF²` and the joint as the product of two absolute members, because the
   fixture's JES and HF tables share the nominal `1.0` and the two centrals intern to one node; the
   label-precision test builds its probe from the second family's nominal re-evaluated on the shifted
   jets, a node that is no longer in the shared container, so the probe's `jes` coordinate is a
   dependency and fans out. The §1 fixtures that register a handle over one factor change their
ambient's values (those entries become overlays) and keep every label and point they assert. No other frozen test changes outcome; m56's order-independence property — the label set and every label's value — holds under the
   join because the joined nominal member is the union of the centrals' coordinates (symmetric),
   which §4 pins with a weight the shift moves; the two orders agree on every member's serialized IR as well, and only the session-local node
   ids differ. The extra registration-refusal tests that build two factors from one expression to
   provoke a product-form clash are given distinct centrals by the implementer, which keeps the
   property they test.
7. **Explaining the variations.** `graphed.explain(ctx)` returns an `Explanation` — a frozen
   record with a one-line-per-item text rendering (`str()`) — that shows a user how their sources
   of uncertainty became this context's variations: (a) every family registered on the lineage,
   in registration order, with its name, `Kind`, tags, the context that registered it (its links
   from the root: a cut, `graphed.nominal`, `graphed.universe(..., L)`, a `vary` child) and how it
   entered — the shift form with the collections it shifts, or the weight form's outcome: a new
   factor, a join naming the factor's other families, an overlay over the families it was read
   over, and its placements with their points; (b) the ambient's operations here, as the ambient
   at this context composes them (a left-out overlay absent, a fixed one marked), one line per
   entry from its rider — its position in the list (the slot lives in the record, since slot ids
   are process-wide), kind, the families it carries with their coordinates, the row-space links
   it came through; (c) the variations here: every label the ambient carries and
   every label a shifted collection carries, each with its origin — a family's one-at-a-time
   member, a joint minted by fan-out (the family and the dependency it read), a placement (the
   family and the point), an overlay's own universe — and, per weight family, the WEIGHT families
   it composes with: those it shares no registered point with (no label either minted and no
   placement carries both families' coordinates — a symmetric relation, so on the §1 tour chain
   `hf` composes with `pu` alone, the placed diagonal carrying `hf` and `mu`, and `mu` with `pu`
   and `lf`), so a user sees why `hf_up__mu_up` is not in the list; a family that joined a factor SHARES it with the
   factor's other families and is reported so, never as composing with them (their joint is
   absent because they are two values of one operation, not because it is a product); and
   separately the shift families it fans out over and those it is independent of (a shift is
   never "composed with": either a minted label carries its coordinate or the family does not
   read the shifted objects) — except a weight family registered BEFORE the shift of the objects
   its central read, the case §2.5's shift-after-weight diagnostic names, which is reported as
   reading objects a later shift moved, naming the order, never as independent. Relations and
   placements quantify over the family's registered points on the lineage, not over the labels
   this context carries, so a projection that drops a label drops neither. An operation
   registered at the context it is read at has come through no row-space link, and the line
   says so in words rather than with a placeholder. The origins are derived from the labels'
   registered points and the riders, never by re-deciding. `explain` is a read: it reads the
   ambient exactly as `weight(ctx)` does, records as a read does, and mints nothing else, so the
   Session's node count after `explain` is the count after a `weight` read (with §2.6's one
   exception, a placement minted after it, as after any read), and because an adoption records
   the adopted member (§2.3), neither a read nor `explain` between registrations changes a later
   decision or value. The text carries no integer node id (the record does), so it is
   byte-identical across two Sessions.
Out of scope: dedupe by value; extension across two DIFFERENT centrals of one SF table (a family
whose nominal is `SF(central)` computed from other jets is a new factor); a family whose nominal is
a varied MEMBER of the ambient (`universe(weight(ctx), "mu_up")`) — a new factor, as today, at the
context whose ambient it is a member of (inside the projection into that universe the same node
is the ambient's nominal and the family is an overlay, §2.3); changing
what a shift family's `nominal=` may be.

## §3 Design

In `python/graphed/systematics/ambient.py` (the rider and the operation list; `EventContext` stays in `python/graphed/context.py`), `_factors` becomes the operation list, each entry in a SLOT
(`_slots`, parallel ids minted at append: a join replaces the object in its slot, an overlay takes
a new slot inserted after the entries it was read over); the overlays are named by slot in a
context set (`_overlays`). Every composition handed out is recorded once, on the context (the handle's member nodes, the LIVE factor slots it stands for, their generations)
in `_reads` — a fresh composition and a memo hit by `_ambient_weight`, the adopted member by
`_adopt_ambient` at the adoption, so a read at the child that returns the adopted member records
nothing new — — keyed by the whole member map, since a join leaves the nominal node alone and a
nominal-keyed record could not tell a stale handle from a fresh one. A factor slot's generation
counts the unions that added universes to its nominal member (never node stamps, which a
re-index at a masked child would also move), so a record whose generations no longer match is
stale; the factors an overlay covers are those before it in the live list, so nothing is stored
for it — which a `vary`
link SHARES with its parent (one row space, so a handle read at the parent after the child was
built still decides at the child, and a divergent branch's slots can never prefix another's);
`_child_of` copies `_slots` and `_overlays`; `_adopt_ambient` starts the child's own list, slots
and overlays afresh and stores what its head stands for — the parent's live factor slots and
their generations at that moment, the tuple a read records — while the ancestors' records stay
reachable: `_extension` walks the lineage's records back through every row-space link, adopted
or since expanded (the records are keyed by the ancestor's nodes, which a crossed handle carries),
and matches them by slot prefix against the live factor slots — the head's tuple while the
context adopted, the child's own re-indexed slots once a join or an overlay expanded the head.
The overlay's position is after the prefix's last factor slot and any overlay already anchored
there; a record equal to the head's tuple anchors right after the head (and its anchored
overlays) without expanding it, and a prefix ending inside the head expands it first — the
ancestor's live entries re-indexed to the child exactly as an ancestor-factor join does, slots
kept. An expansion builds the child's list from provenance, never from the order a lineage walk
meets the entries: the ancestor's live entries in their list order, then each entry the child
registered in the child's own order, every overlay at the position its rider gives it — right
after the last factor slot of its recorded prefix and after overlays already anchored there —
so an overlay anchored after the head stays before a factor the child registered after it and
its universe is unchanged across the expansion. The principle: every node a later registration may name is recorded in PROVENANCE the
moment it comes to exist — an entry's nominal in each row space, its member at each projected
label, a composition handed out by a read (`_reads`) or by an adoption — and every decision
reads provenance, never the object as it currently stands: no DECISION reads a live entry's own
attributes (its two-level members, its tags), while composing — `_compose`, `_check_forms`, the
m56 fan-out test and the label-clash check, both fed by `_ambient_tags` — reads entries because
composing is what they are for; what enforces the
principle is §4's legs (the owner refused after an unrelated expansion, the rider leg), no grep
can. Every entry's provenance is a RIDER kept
beside its slot on the context and never read off the entry object, which a re-index replaces
with a bare member: its kind (factor or overlay), the families it carries with their
coordinates (the point registry of its container at registration, extended at a join), its
nominal identity in every row space it came through (one per row space crossed; a join keeps
the nominal node, so a joined entry's identity is unchanged) and the member it became at each
projected label it was re-indexed through, an overlay's prefix (the factor slots before it) and
whether a projection fixed it, and its history — the context that registered it and each
row-space link it has been re-indexed through since, a mask or a projection with its label.
`_adopt_ambient` records the adopted member as the child's read (keyed as any read is: its
member nodes, the head's slots and generations), so the head has provenance before anyone reads
at the child. The riders are read by a walk over the same chain `_live_factors` walks; the
factor arm's candidates are the rider's nodes only — the identity in the central's own row
space, with `_same_node`'s lineage test as before, and the member at a projected label — the
member as it stands in the entry's OWN row space, recorded when the projection is taken and
never re-indexed or re-stamped onto the projected context, recorded across a mask too — matched
by equal node id on one lineage with no mask between the central's context and that row space
(which is what admits a central built at the parent and one built at or below the projection
alike, and what refuses the same expression built above a mask that lies between once the child
has registered below it: a member of a different ambient); the nominal arm answers first over every live slot, then the projected
member, the match refused when the entry owns the label — any label the context is still inside
— and a join when it does not (§2.3); ownership of a projected label is
decided from the rider's families against the label's point; `reindex_to` through a project link re-indexes an entry per
its rider (§2.3): a fixed overlay stays fixed, an unfixed one with no coordinate on the label is
left out, and `_compose` replaces with a fixed overlay at every value.
`graphed.systematics.ambient_entries(ctx)` (also re-exported from `graphed.context`) returns the operations as the ambient at `ctx` composes
them — in the list's order, the order `_compose` applies (an overlay at its anchored position,
before a factor the child registered after it), never the order a lineage walk meets them; a
left-out overlay absent, a fixed one marked; the same slots, kinds and order before and after a
registration that changes no value, a joining family entering its slot's families — as
`(slot, rider, entry)` records, the record's position its index in that order: the
instrument a person (or the frozen suite) reads to see what the ambient is made of, where each
entry came from and what it has been re-indexed through; the docs example prints it. `graphed.explain(ctx)` (in
`python/graphed/systematics/explain.py`, exported from `graphed` and `graphed.systematics`) builds its record from what the context
already keeps — the family registrations (`_weight_tags`, the shift registry, the placements),
the riders through `ambient_entries` (each `Operation` carries the rider's `fixed` mark, and the
line of a fixed overlay names the universe that fixed it), the link chain from the root, and the labels of the ambient
and of each shifted collection with their registered points — and renders it; a joint's origin
is its point's families, a placement's is the family that registered the point, and "composes
with" is the set of weight families with which it shares no registered point (§2.7), computed
over every registered label's point, so the relation is symmetric.
`_compose` (told the overlays by slot, mapped to the entries it holds) composes each product RUN
between overlays with today's balanced tree (so a program
without an overlay is byte-identical to today, node counts included, and an overlay leaves the
cost class of the tree) and applies the overlay by replacement at the labels its family covers (an
entry whose two-level member at a label is its nominal has no coordinate there, the test the tree
walk already makes) and never at a universe another family placed — a label whose registered
point carries no coordinate that renders it (the placing family's own axis is not in its point,
which is how `_route` registers a placement); the overlay's own universes, a joint it minted
included, are told apart by membership in its container, so they are still replaced. The fold memo is unchanged for appends: a new factor folds onto the
overlay-applied composition, a new overlay at the end of the list replaces the folded composition
at its own labels; a join, or an overlay inserted before the end, drops the memo so the composition
is remade from the list, and so does a registration that mints a label the memo base cannot resolve
(its point restricted to the base's axes is non-empty and the base answers `nominal` — the §2.5
repair, decided at the fold choice in `_vary_weight`; the memo tuple and `_foldable` are
unchanged). `_check_forms` walks what the read composes, so it is told the overlay entries too.

In `_vary_weight`, before `gather_members`, `_extension(ctx, central)` answers nothing for a
central whose member at `nominal` is itself a container (one level in, not the two-level read,
which peels a level further), else the overlay for a recorded read whose member map is the
central's and whose factor slots are a prefix of the live factor slots (a stale record — a
generation moved — is refused at the registration, naming the family and the read to repeat, and
so is a record whose prefix ends inside the factors an overlay covers at a projection into that
overlay's own universe, naming the read to repeat at the projection into that universe — the
link that fixed the overlay, from its rider, not the last link taken), else the join for the
first live factor whose nominal is `_same_node` with the central's nominal
(`_two_level(central, "nominal")`), else `None`. `_same_node`: equal node ids, then the two handles' contexts on one lineage with no mask
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
  spellings, with the older handle read over ONE factor and over two (both ends of the prefix
  length; at one the join outcome would refuse both orders), and a handle read over the full list
  before the one-factor registration stays fresh after it (its slot's generation unmoved); the
  same at a masked child whose adopted ambient was read before a factor was registered there
  (a memo hit on the adopted container, then the overlay after the head), and at
  `graphed.nominal(ctx)` over two factors, where the read returns the adopted member itself, with a
  factor registered there before the relative-delta family — there the two orders agree on the
  label set and every value; WITHOUT the child factor the two orders' label sets differ at the
  nominal projection while every shared label's value agrees (the parent's labels the older
  handle carries are dependencies there only while the head is unexpanded, main's shape) — and, at the masked child and
  at the nominal projection alike, an ancestor-factor join registered AFTER the overlay leaves it
  anchored after its prefix with its universe unchanged across the expansion (failing direction:
  that universe divided by the factor the child registered before the overlay, `[0.525, 1.05,
  2.1]` for `[1.05, 2.1, 4.2]`); the fresh-composition and memo-hit records each have a leg that
  fails when the record is dropped, and the adoption record's is the adoption-read leg below; at `graphed.universe(ctx, L)` over two factors
  with the parent's own central: naming a factor that does not own `L` joins it and keeps the
  projected universe (`pu` named inside `hf_up`: nominal stays `pu · SF(up_hf)`), and naming the
  factor that owns `L` is refused with the projected ambient node-identical across the refused
  call (fails on a build that joins it and answers `pu · SF`), each before and after a cross-row
  join at the projection and after an expansion at a masked child before it (fails on a build
  that reads the families off the re-indexed entry, which joins the owner after one expansion),
  and at a placed label whose point carries two families' coordinates, where both owners are
  refused and a third factor joins (fails on a build that decides ownership by the label's
  name); a central node-identical to a factor's member there (the universe projected into) is
  refused whether built AT the projection or at the parent — the node handed to `vary()` as the
  owner's `up=` — registered with and without an unrelated expansion at the projection first and
  in both orders with an unrelated family, the parent-built spelling also with a mask between
  the parent and the projection, the projected ambient node-identical across every refused call
  (fails on a build whose candidates include the re-indexed entry's own nominal: a new factor
  without the expansion, `[4.5, 18, 72]`, a join of the owner with it, `[1.5, 3, 6]`; and on a
  build that records the member re-stamped onto the projected context, which accepts the
  parent-built member across the mask: `[4.5, 18, 72]`, `[9, 36, 144]` after an expansion),
  while the member re-derived AT the projection across that mask is a new factor (`[2.25, 9,
  36]`, main's answer, the control), and the refusal names the two spellings that work (register
  at the parent before projecting; read the handle at the projection) and never a re-derivation
  at this context, which interns to the refused node; below a SECOND non-nominal projection the
  owner of the outer universe named by its recorded member is refused as by its nominal, and the
  owner of the inner one too (fails on a build testing ownership at the innermost label alone: a
  join, the ambient times the family's member; and on one matching every recorded member: the
  inner universe erased, `[1.05, 2.1, 4.2]` for `[1.575, 3.15, 6.3]`); a node that is both a
  live factor's nominal and the owner's recorded member joins that factor in both registration
  orders, the projected universe kept (fails on a build that lets registration order decide:
  refused in one order); at `L` a shift label, the SF re-derived over this context's shifted jets —
  node-identical to the jes-dependent factor's recorded member there, which does not own `L` —
  joins that factor: nominal `[4.5, 4.5, 4.5]` unmoved, the family's `up` twice it (fails on a
  build that refuses every recorded member, and on one that makes a new factor, `81`); at `L` a shift label, a family
  joining the factor WITHOUT a coordinate on that shift keeps the other factor's dependence
  (nominal reads the SF at the shifted jets; fails on a one-level re-index, `[1.5, 1.5, 1.5]`
  where the projected ambient was `[4.5, 4.5, 4.5]`), beside the join of the jes-dependent
  factor as the positive control; at `L` a relative-delta family's own label, a family joining a
  factor registered after the overlay multiplies its result (`1.05 · P · SF(up_mf)`), one joining
  a factor the overlay covers is refused, a handle read over a strict prefix of the covered
  factors is refused, the whole-head handle anchors (`mu2_up = 1.05 ·` the projected value,
  nominal unmoved), a handle read AT the projection is an overlay there, and below a SECOND
  non-nominal projection the post-overlay join still keeps the overlay's factor (failing
  direction: the ambient divided by `1.05`) while the covered join is refused on the same list,
  the refusal naming the universe that fixed the overlay (`mu_up`) below the further projection
  too (fails on a build naming the last link taken: the second projection's label); and after an expansion at the
  overlay's own universe followed by a further row-space link carrying a registration, the
  overlay stays fixed, its universe `1.05 ·` the projected value (fails on a build that re-tests
  a fixed overlay against its re-indexed member and leaves it out: `÷ 1.05`, the rider's mark
  false);
  at `graphed.universe(ctx, L)` a family whose nominal is `universe(weight(ctx), L)` built at the
  parent is an overlay after the head with and without a `weight(prj)` or `explain(prj)` read in
  between, the same values and nominal node (fails on a build that records only reads: a new
  factor without the read, squaring the projected ambient), while the same expression built
  above a mask that lies between the parent and the projection, with a factor registered at the
  masked child before the projection, is a new factor (main's answer, the control); a rider leg: the entries reported by
  `ambient_entries` after a family has joined an ancestor's factor at `graphed.universe(ctx, L)`,
  and at a masked child, carry the families, kind and identity chain the parent's do, with the
  link each came through (fails on a build that reports the re-indexed object's own tags, which
  are empty on the unjoined slot), listed in the order `_compose` applies them — an overlay
  anchored after the head before a factor the child registered later (fails on a build listing
  the lineage walk's order) — and the listing at a projection keeps its slots, kinds and order
  across a join that changes no value, the joining family entering its slot's families; a handle read BEFORE the row-space change
  and registered at the child — a masked child and a `graphed.nominal(ctx)` projection, the parent
  over two factors — gives the one-SF oracle on the child's rows (the failing direction is the
  squared nominal; at the projection the members carry the parent's labels, which the projected
  context no longer composes, so m53 fans them out as dependencies there, as main does on the same
  program), in one program with a family that joins an ancestor's factor at the child, in both
  orders (the failing direction is the squared nominal, `[1.0, 4.0]` for `pu · SF = [1.0, 2.0]`);
  the same handle read over a strict prefix of the parent's list anchors after that prefix at the
  child (`mu_up = 1.05 · pu · SF` on the child's rows with `hf` registered after the read), and a
  handle read over a factor a join later widened, the cut taken after the join, is refused at the
  child as stale (fails on a build that matches a crossed record without its generations); after
  an expansion at a masked child a central built at the ancestor still names its factor — two
  families on one ancestor central at the child (nominal `SF`, not `SF²`), two families on two
  different ancestor factors at one child, a family joining an ancestor's factor after a
  strict-prefix crossed overlay in both orders, and a central built at the top of a two-mask
  chain named after an expansion at the child and again after one at the grandchild — the
  ancestor's factor appears in the product once, each leg failing on a build without the
  identity and the last on a build that keeps only the last row space's;
- staleness is loud: a join whose union adds a shift universe to a nominal member (a jes-varied
  second central) is refused when an overlay was read over that factor, and a handle read before
  such a join is refused as a relative-delta nominal whether or not a `weight()` read intervenes
  between the join and the registration (a record keyed on anything the join leaves untouched
  accepts the second spelling), each error naming the order that works; the
  same program with the handle read after the join gives `mu_up__jes_up = 1.05 · jes_up` (an SF the
  shift moves, so the joint discriminates);
- two centrals sharing a nominal node with different shift coordinates (one on the nominal jets,
  one on the jes-varied jets), registered in both orders, agree universe-by-universe with the one-SF
  oracle read at each label's own jets, and the same coordinate declared by both with different
  nodes (two loose-form containers on one central with different `up` members) is refused before
  anything is minted: with two or more factors live at the conflicting registration and no
  ambient read since the last of them registered (a cold memo, so a build that composes to decide
  mints inside the refused call), the Session's node count, read after the members are built, is
  unmoved across the refused call, and moved across the accepted registration of the same shape
  followed by the ambient read that composes it — the refused leg first, or each leg in its own
  Session, since a control that ran first would have interned the very product a composing build
  mints (the leg fails on a build that composes to decide); the m56 capstone shape with a weight the shift MOVES
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
  the same central re-computed at the masked child is a new factor (control), and a bare
  `Varied({"nominal": <container>})` built with the public constructor over a live factor's
  central, declaring nothing else, is refused with the pre-m57 error (fails on a build that joins
  it; a spelling that also declares its own tag is refused on such a build too, by the form check,
  so it discriminates nothing); at
  `graphed.nominal(ctx)` over two factors a central re-derived from the
  projected collections interns to the parent's node and joins (one-SF oracle), while at
  `graphed.universe(ctx, L)` for a weight label `L` the same registration is a new factor: the
  projected ambient's nominal becomes the projected universe times the central (the pre-m57
  answer) and the variation projected into survives, where a match reaching through that
  projection replaces it by the parent's nominal product;
- node identity, not value: a recomputed central with equal values is a new factor (values are the
  product — today's answer, the control);
- name identity extends: a `jes` weight registered on `hf`'s central inside a jes-shifted context
  gives `jes_up = SF(up_jes)` alone, and m56's fan-out over the shifted jets still mints its joints,
  each read two-level from the one container;
- relative-delta members over an ambient that carries another family's labels: `hf_up__mu_up`
  absent (composition), `mu_up` exact, `hf_up` unchanged;
- a placement minted after an ambient read, whose point names the coordinates of two earlier
  factors, has its declared member with and without the intervening read (fails on the pre-m57
  fold, which freezes the label at nominal after the read);
- a placement by a family registered after an overlay, at a point carrying the overlay's
  coordinate (the tour's diagonal `scale_upup`), keeps its declared member at both prefix lengths,
  while the overlay's own universe is still its member (fails on a build that replaces at every
  label carrying the coordinate), and the overlay family placing its OWN universe at a point made
  only of other families' coordinates keeps that declared member (fails on a build that exempts
  by the point alone);
- `variations` reports the extending family as `Kind.WEIGHT` with its tags and `labels(weight(ctx))`
  keeps registration order (guards the join path's record writes); the shift-after-weight
  diagnostic names a family that joined a factor when its members' jets are later shifted;
- transactional: a refusal that fires after the match — the union conflict above — leaves the
  live list and its generations as before: a handle read before the refused call registers a
  relative-delta family right after it, with no `weight()` read in between (a read would re-record
  the handle), fresh not stale, and `weight(ctx)` read then is node- and label-identical to the
  read before the refused call (fails on a build that stamps a generation or splices the list
  before refusing);
- explain: on the §1 tour chain (two factors, a family that joined one, an overlay read over
  both, a placement at the diagonal), the record reports each family's entry form — the joined
  family names the factor's other family, the overlay names the two families it was read over,
  the placement its point — and lists every ambient label with its origin, the overlay's own
  universe included, and each weight family's "composes with" set as §2.7 states it for the
  chain (`hf` with `pu` alone, `mu` with `pu` and `lf`);
  at a masked child that joined an ancestor's factor and at a `graphed.universe(ctx, L)` child,
  the registering context's links and the entries' row-space links are the links the lineage
  took — a mask, a projection into `hf_up` — compared by kind and label against the lineage the
  test built (the record's link fields, never a quoted rendering), not against
  `ambient_entries`, which explain is built from (fails on a build reporting the parent's entries
  unre-indexed, whose links are empty); below a projection into an overlay's own universe and a
  further projection, the fixed overlay's operation record has `fixed` true and its line names
  the universe that fixed it (fails on a build that drops the mark); and a family whose label the
  projection dropped keeps the relations and the placement it reports at the parent (fails on a
  build deriving them from the labels carried here); the m56 capstone with the pure-weight
  family registered AFTER the shift of the jets its central read reports `hf` fanning out
  over `jes` (the dependency it read) and composing with the pure-weight family, the pure-weight
  family independent of `jes`, never composing with it, and the same capstone with that family
  registered before the shift reports it as reading objects a later shift moved (the §2.5
  registry is collection-level, so a central reading any field of the shifted collection is
  named; failing direction: the word independent); the joined family of the tour chain reports
  sharing the factor, not composing with its other family; the Session's node count after
  `explain` equals the count after a `weight` read, before and after a further registration
  (fails on a build that composes to explain); the text rendering is byte-identical across two
  Sessions of the same program in which the record's node ids DIFFER — the second Session mints
  an unrelated node before the program, so the ids cannot coincide and a build that prints a
  record id in the text fails the comparison (the rendering compared whole, no tokeniser);
- determinism: the extending program serializes byte-identically across two Sessions, and a
  program that names nothing, among its registrations one at a masked child whose central is not
  the parent's, serializes byte-identically to its pre-m57 answer, node count included (the pinned
  bytes regenerate from the test's own program, not from a stored blob).

## §5 Work items and gates

| item | what | where |
|---|---|---|
| W1 | the operation list with its per-slot riders (identity and projected member per row space, fixed mark, adoption read), `ambient_entries` and `graphed.explain`, `_extension`/`_same_node`/`_live_factors`/`_extend`, the provenance-ordered expansion, the adopted-container marker and the overlay set, the rider-decided project re-index; the extra refusal tests re-based on distinct centrals and the `_check_forms` spy's arity | `python/graphed/systematics/ambient.py`, `python/graphed/systematics/explain.py`, `python/graphed/context.py`, `tests/extra/awkward/test_weight_registration_refusals.py`, `tests/extra/frontend/test_weight_composition.py` |
| W2 | executed docs example, printing `explain(ctx)` after a cut and a projection | `docs/frontend/design.rst` |
| W3 | frozen suite (test author); the two m56 disputes re-frozen on the owner's affirmation | `tests/frozen/awkward/m57/`, `tests/frozen/awkward/m56/`, `.graphed/m57/disputes/` |
| W4 | tour: cells 14/34/36/38 re-executed (their printed lines are unchanged, their values are not); the Level 6/17 markdown states the rule | `coffea-benchmarks-graphed-mvp/graphed-vary-systematics-tour.ipynb` |
| W5 | systematics plan §2.1(b) weight-form paragraph states the nominal rule; root prompt R24.5; memory `weight-form-factor-semantics.md` retired | `graphed-workdir/systematics-vary-plan.md`, `graphed-root-prompt.md` |
| W6 | the `graphed.systematics` package (owner request 2026-09-11): the vary machinery moves out of the top-level modules as PURE MOVES — `kinds`, `tags`, `points`, `varied`, `accessors`, `by_label` (one module each, from `_kinds`/`_tags`/`_points`/`varied`/`accessors`/`by_label`), `registration` (from `vary.py`: `vary`, `gather_members`, `AmbientCarrier`, the checks and `register`), `ambient` (from `context.py`: the rider, the operation list and its decisions — `_extension`, `_extend`, `_joined`, `_compose`, the record and adoption helpers — and `ambient_entries`) and `explain`; `EventContext` stays in `graphed/context.py` (the context tree: links, collections, selection, its state fields) and calls into `systematics.ambient`, which removes the `vary` ↔ `context` deferred-import cycle; `graphed.vary` stays the entrypoint through `graphed/__init__.py`, and `graphed/vary.py`, `varied.py`, `accessors.py`, `by_label.py`, `_kinds.py`, `_points.py`, `_tags.py` become one-line re-exports so every existing import (the frozen suites import `graphed.context` and `graphed.varied`) keeps working; `systematics/__init__.py` exports the narrow surface for exact work. Lands as ONE `refactor(systematics)` commit after the design round on v11 is clean and before the test author, gated by `git diff -M` rename detection, the full runner, ruff/mypy/Sphinx and the byte-identity sweep; the m57 frozen suite imports from `graphed.systematics` | `python/graphed/systematics/`, the shims, `docs/frontend/design.rst` (module map) |

One implementation commit (W1+W2) and the test commit; W4/W5 land with the pin bump. Gates as for
every milestone: frozen suite green and unmodified, `scripts/run-tests.sh` all green, diff coverage
≥ 90 % line+branch from the frozen suite, ruff/format/mypy strict clean, Sphinx `-W` clean,
determinism.
