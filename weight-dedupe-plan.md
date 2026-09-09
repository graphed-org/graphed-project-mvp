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
   - **extends a factor**: the node is a live factor's nominal — the family's members join that
     factor's container as its values in their universes; the factor keeps its position and its
     nominal, its tag map gains `name`, and the composition at `name_t` multiplies the member ONCE
     with the other operations (the absolute-weight idiom: `hf_up = SF(up_hf)`,
     `lf_up = SF(up_lf)`, nominal `SF`);
   - **overlay**: the node is the composition's nominal and no live factor's — the family's members
     are the whole ambient in their universes (the relative-delta idiom: `mu_up = 1.05 · P` is the
     member node itself). A factor registered AFTER the overlay multiplies its result
     (`mu_up` then `trig`: `1.05 · P · trig`); a family that later extends a factor registered
     BEFORE it keeps that factor's position, so the overlay still replaces the product of the
     factors it was built from (§1(e): `lf_up = pu · SF(up_lf)`, `mu_up = 1.05 · pu · SF`). With
     one live factor the factor outcome answers first and the two coincide (its nominal IS the
     composition's), so an overlay exists only over two or more factors.
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
   node ids are equal AND they are at most `vary`-link separated on one lineage: a mask or a
   projection makes one id two values, and the only container that can match across a row-space
   change is the adopted one, which sits in the child's own list. Nothing is composed or re-indexed
   to DECIDE: a central re-indexed for the comparison or an ambient composed for it would mint nodes
   on programs that name nothing, shifting every later node id and the fold memo (§2.6). The
   composition's nominal is read off the memo, which passing the ambient has filled; a central
   nested past §2.2's one level names nothing (the form check reports it as today).
4. **Kinds, records, diagnostics.** `variations(ctx)` reports the extending family as
   `Kind.WEIGHT` (union with `SHIFT` under name identity); `_weight_tags[name]` is written as for
   a new factor; the §2.5 shift-after-weight record and `_weight_factors` carry the extended
   container's (or the overlay's) member nodes; `labels(weight(ctx))` gains the family's labels in
   registration order; the extended factor keeps the tag map the container it replaces carried
   (the shifts a row-space change leaked in stay candidates for m56's node test). Name identity composes with extension: a `jes` weight whose nominal is `hf`'s central
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
   dependency and fans out. No other frozen test changes outcome. Three extra registration-refusal
   tests deliberately build two factors from one expression to provoke a product-form clash; they
   are given distinct centrals by the implementer, which keeps the property they test.
Out of scope: dedupe by value; extension across two DIFFERENT centrals of one SF table (a family
whose nominal is `SF(central)` computed from other jets is a new factor); a family whose nominal is
a varied MEMBER of the ambient (`universe(weight(ctx), "mu_up")`) — a new factor, as today; changing
what a shift family's `nominal=` may be.

## §3 Design

In `python/graphed/context.py`, `_factors` becomes the operation list: entries are containers as
today, the overlays named by id in a context slot (`_overlays`; a mark on the container would not
survive `reindex_to`, a position would not survive the lineage merge) — copied by `_child_of`,
cleared by `_adopt_ambient`, re-keyed by the ancestor branch of `_extend`. `_compose` keeps today's
balanced product tree when the set is empty (§2.6's byte identity) and otherwise walks the list in
order — a factor multiplies its two-level member, an overlay replaces the running value at the
labels its family covers (an entry whose two-level member at a label is its nominal has no
coordinate there, the test the product walk already makes). The fold memo is unchanged for
appends of either kind: a new factor folds onto the overlay-applied composition, which is §2.1's
answer, and a new overlay replaces the folded composition exactly at its own labels; joining a
factor drops the memo so the composition is remade from the new list. `_check_forms` walks what
the read composes, so it takes the overlay set too. `_adopt_ambient` marks
the adopted container (`_adopted`, copied by `_child_of`); `_live_factors(ctx)` walks back through
adoptions and returns the live operations root-first, once each.

In `_vary_weight`, before `gather_members`, `_extension(ctx, central)` answers `("factor", f)` for
the first live factor whose nominal is `_same_node` with the central's (`_two_level(central,
"nominal")`; a `Varied` answer names nothing), else `("ambient", None)` when the memo covers every
operation and its nominal is the central's node, else `None`. `_same_node`: equal node ids, then
the two handles' contexts on one lineage with no mask or projection link between them. Minting is
unchanged. Then `_extend` builds the new list: an overlay appends the family's container (nominal
= the composition's nominal read off the central the caller passed, members = the family's — an
ordinary append, nothing composed); a factor of `ctx`'s own list is replaced in
place by `_joined(factor, members)` (the factor's members plus the family's, its tag map plus
`name`); a factor of an ancestor's list is replaced in the re-indexed live list, the extended one
also carrying the tag map of the adopted container it displaces; an overlay re-indexed there keeps
its P, equal in value to the rebuilt running product but a different node, which nothing depends on
since the overlay replaces. `_check_forms` runs on the new
list; `_weight_tags`, `record_labels`, `_weight_factors` and `_recorded` are written as for a new
factor; the child's `_adopted` survives only while the adopted container is still the list's head.
The prototype is `scratchpad/dedupe/prototype.diff` (branch `dedupe/prototype` of the m52 clone).

Docs: `docs/frontend/design.rst`'s weight-form section states the rule (the nominal names the
factor; the three outcomes; node not value; the joint of two families on one factor) with an
executed example of both idioms printing the nominal and one universe each.

## §4 Frozen suite (test author, isolated; `tests/frozen/awkward/m57/`, `m57_` prefix)

Fixtures follow m53's tree; every new behaviour is reached inside test bodies so the tree collects
on a pre-m57 tree and fails at run time on the squared values. One test per property:

- two families on one central: every universe's weight equals the one-SF oracle by value, and the
  nominal universe's weight is the central node (node identity);
- the ambient as nominal over two factors: `mu_up` is the member node itself, `hf_up` and nominal
  unchanged from the context before the registration (values and nodes); then a family on one of the
  absorbed centrals (§1(e)) and a new factor after the overlay, each universe against the one-SF
  oracle (`lf_up = pu · SF(up_lf)`, `mu_up = 1.05 · pu · SF · trig`);
- a joint of two families on one factor reads the cross member alone (the m56 fixture's shape, the
  oracle `SF(jes_up jets, HF-up table)`), beside the ratio spelling whose placed joint carries both
  variations;
- a family extending a factor still fans out over the shift its members read (labels and the
  one-SF oracle at each joint's own jets);
- lineage: one parent factor and two parent factors, the second family registered on a masked
  child, values against the one-SF oracle on the child's rows; the parent's ambient is unchanged;
  the same central re-computed at the child, and a central that is a nested container, are new
  factors (controls);
- node identity, not value: a recomputed central with equal values is a new factor (values are the
  product — today's answer, the control);
- name identity extends: a `jes` weight registered on `hf`'s central inside a jes-shifted context
  gives `jes_up = SF(up_jes)` alone, and m56's fan-out over the shifted jets still mints its joints
  with the two-level product as the joint weight;
- relative-delta members over an ambient that carries another family's labels: `hf_up__mu_up`
  absent (composition), `mu_up` exact, `hf_up` unchanged;
- `variations` reports the extending family as `Kind.WEIGHT` with its tags; `labels(weight(ctx))`
  order;
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
