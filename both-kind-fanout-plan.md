# m56 — fan-out decided on nodes: a nuisance that is both a shift and a weight

Owner request (2026-09-08): in the tour capstone, `btag_hf` registered over the jes+jer-varied jets
mints only the hf × jer joints; the hf × jes joints are missing although the b-tag SF depends on
the jes-shifted jets exactly as it depends on the jer-shifted ones. Fix it.

## §1 The gap (measured)

`_foreign` in `python/graphed/vary.py` (m53) drops a member's foreign coordinate when its nuisance
is a family the ambient weight registers as a weight (`composed`), on the premise that such a
coordinate came from weight composition and fanning it out would double-count the factor through
`_two_level`. The premise is a property of the *member's dataflow*, but the test is on the
*family's kind*, so it misfires for a nuisance that is both a shift and a weight: in the capstone
`jes` moves the jets (shift) and swaps the b-tag SF table by name identity (weight), and hf's
members reach `jes_up` through the shifted jets, not through the ambient. Measured on the capstone
program (`scratchpad/lockstep/hf_jes.py`): registering the jes weight first then hf over the varied
jets gives 4 joints (hf × jer); registering hf first then the jes weight gives 8 (hf × jes and
hf × jer), and the reversed order composes the joint correctly (`btag_hf_up__jes_up` weight
= SF(up_jes) × ratio(up_hf), both on the jes_up jets). The same registrations therefore mint
different universe sets depending on order. `scratchpad/m56/cases.py` isolates the cases: a
shift-only nuisance fans out (A); the both-kind case is dropped (B, the defect); a member computed
from the ambient is dropped (D, E) and a pure-weight family stays composed (C), which are the
behaviours the rule exists for; a spectator coordinate collapses (F). The misfire is also a
lineage inconsistency on main: a family whose members read the jes-varied MET, registered on a
context whose ambient carries `pu` as a weight and `jes` as a leaked shift, mints `sf_up__jes_up`
at the parent but not at its masked child, because the child's adopted ambient container carries
`jes` in its tag map (`scratchpad/m56/m48probe.py`).

## §2 Contract

1. **Composition is a fact about nodes.** A foreign coordinate `(X, tag)` carried by a member at
   label `L` is *composition* — excluded from fan-out — iff `X` is a family the ambient registers
   as a weight AND the member's node at `L` reads (is in the input cone of) a registered factor's
   *varied* member at `L`: the factor's member under the two-level, point-restricted resolution
   the composition itself performs there (`_two_level` → `Varied._key_for`, so a joint label
   resolves each factor to the member of its own coordinate), taken only where that member is a
   different node from the factor's nominal. A factor whose member at `L` is its nominal — the
   context's seed weight, a weight family with no coordinate on `L` — carries nothing of `L`, so
   reading it is not composition at `L`. The factors are those of the whole context lineage (a
   mask-derived context's ancestors included; §2.1(b)'s ancestor-handled factor reads the
   parent's factor nodes, never the adopted composed node). Every other foreign coordinate of a
   registered nuisance on a carried container is a dependency and fans out, whatever kind `X`
   is; the own-family skip and the spectator gate are unchanged. The target set is empty at a
   label where no factor varies (nothing registered, or only shift coordinates on `L`), and then
   nothing is composed. The read is a cone test, so a non-arithmetic read of a varied member — a
   row cut on the composed ambient at a label where a factor varies, `ctx[weight(ctx) > 0]` — is
   judged composition and keeps the pre-m56 answer; no program in the corpus, the tour or the
   suites cuts on the ambient, and a rule that tells a boolean read from a product is a separate
   design.
2. **Order independence.** For a family registered over objects shifted by `X` and a weight family
   `X` registered by name identity, the joint label set and, per label, the materialised values of
   every universe's Jet, MET and ambient weight are the same whichever registration comes first.
3. **The joint composes two-level.** In `f_t__X_u` the ambient weight is the product over factors
   of each factor's member at that point: the `X` factor's `X_u` member times `f`'s cross member
   (measured: SF(up_jes) × ratio(up_hf), both on the jes_up jets). The one-at-a-time `X_u`
   universe's weight is unchanged.
4. **What stays excluded, and what does not.** A member computed from the ambient weight, or
   from a registered factor's varied member at that label (cases D and E, including a member
   that reads both the shifted objects and the ambient), stays composed — at one-at-a-time labels and at joint labels alike
   (two shift families under a both-kind nuisance: the ambient-derived member mints nothing, the
   mixed member mints only the non-composed family's joints, as main does), and on a mask-derived
   context whose factor was computed at the parent as on the parent itself; a pure-weight family's
   coordinate on a member computed from the ambient stays composed (C); a spectator coordinate
   still collapses (F). A member that also reads a factor whose member at that label is its
   nominal — the seed weight (`EventContext(..., weight=genWeight)`, member
   `genWeight * SF(varied jets)`), an unrelated weight family's central member
   (`SF(varied jets) * pu_central`) — carries its coordinate through the shifted objects alone
   and fans out exactly as the bare `SF(varied jets)` sibling does; a family registered on a cut
   over the seed weight (`ctx[genWeight > 0]`) fans out as on a kinematic cut.
5. **Everything downstream is untouched.** `composes_as_union=True` collapses the new joints with
   the rest; a `points=` placement can keep a named hf × jes joint; the `max_universes` guard counts
   them; `_route`, `_guard`, minting and the registry are unchanged.
6. **No silent change elsewhere.** Every frozen program of m48–m55 mints the same labels and
   serializes byte-identically, with one measured exception: the m48 masked-child program above
   now mints its joints at the child as it does at the parent, and each joint is re-indexed to its
   coordinate's row space (`sf_up__jes_up` has the mask's rows at `jes_up`). The frozen test that
   pins the child's missing joints is a Test Dispute (`.graphed/m56/disputes/`), re-frozen only on
   the owner's affirmation; no other frozen test changes outcome.

Out of scope: the ambient-as-member idiom of tour Levels 6/17 (open owner item), any change to how
weight families compose, joints between two weight families.

## §3 Design

`AmbientCarrier` (`vary.py`) gains `resolve: Callable[[str], frozenset[int]]`: for a label, over
every factor of the context lineage (`context._lineage_factors`, the `_factors` of the context
and each ancestor, once each), the node ids of `_two_level(factor, label)` minus those of
`_two_level(factor, "nominal")` (a bare factor resolves to itself at every label and contributes
nothing). `_foreign` takes the ambient carrier and replaces
`nuisances & composed` with `nuisances & composed and _reads_ambient(ambient, member._members[L], L)`,
where `_reads_ambient` is `ambient.resolve(L) & cone(session, node)` over the member's nodes
(`by_label.cone`, the walk `_report_shift_after_weight` already uses). `_member_nodes` is defined
once, in `vary.py`, and imported by `context.py`. Cost: one cone walk per member node per composed
foreign label, only when a composed nuisance's label is on the member; `_two_level` is memoised
on the Session. The prototype is `scratchpad/m56/prototype.diff`.

Docs: the fan-out paragraph of `docs/frontend/design.rst` states the node rule with the capstone
shape as the executed example (hf over jets varied by a nuisance that is also a weight: eight
joints, the joint's weight as the two-level product).

## §4 Frozen suite (test author, isolated; `tests/frozen/awkward/m56/`)

Fixtures follow m53's tree (`m56_` helper prefix; every new behaviour reached only inside test
bodies, so the tree collects on a pre-m56 tree and fails at run time on the missing joints).
Properties, one test each:

- hf over jets shifted by a both-kind nuisance mints the joints over that nuisance as well as over
  the shift-only one; each joint resolves to the member's own cross node (not nominal);
- the coordinate survives an incidental factor read (item 4's inclusion class), one leg each,
  each asserting the same four joints as a bare `SF(varied jets)` sibling registered in the same
  test: the member multiplies the context's seed weight; the member multiplies an unrelated
  weight family's central member; the family is registered on a cut over the seed weight
  (control: the same family on a kinematic cut). Each fails on a rule whose targets are every
  lineage factor's member at `L`;
- order independence (item 2): the two registration orders give the same label set and, per
  label, equal materialised Jet, MET and weight values;
- the joint's weight is the two-level product by value against a hand-built oracle, and the
  one-at-a-time `X_u` universe's weight is the name-identity factor on the shifted objects;
- exclusions (item 4), one leg each, asserting the joint label set against the pre-m56 answer
  (each leg's live instrument is a sibling registration in the same test that DOES mint, so an
  empty set is a decision, not a dead fixture): a member computed from the ambient under a
  both-kind nuisance, at one-at-a-time labels and with a second shift family so joint labels are
  on the ambient; a member reading both the shifted objects and the ambient under the same two
  families (only the non-composed family's joints); a pure-weight family's coordinate on a member
  computed from the ambient (control: the carried shift's joints still appear); a member computed
  from the PARENT's ambient registered on a mask-derived child (item 4's lineage clause; fails on
  a rule that reads only the child's adopted factor); a spectator coordinate;
- `composes_as_union=True` collapses the new joints; a placement keeps a named cross-kind joint and
  prunes the rest; the guard's bound — the product of family sizes, this family times each
  foreign family, nominal included — refuses the capstone-shaped registration under a budget the
  pre-m56 rule admits (the guard bounds, it does not count minted joints).

## §5 Work items and gates

| item | what | where |
|---|---|---|
| W1 | node-based composition test (§3) | `python/graphed/vary.py`, `python/graphed/context.py` |
| W2 | executed docs example | `docs/frontend/design.rst` |
| W3 | frozen suite (test author) | `tests/frozen/awkward/m56/` |
| W4 | tour capstone: re-execute; the `grid`/`union`/`diag` cells and their markdown (hf × jes joints now present; "jes is stacked" explanation replaced by the node rule); every other cell's text output unchanged | `coffea-benchmarks-graphed-mvp/graphed-vary-systematics-tour.ipynb` |
| W5 | systematics plan: the stacked-weight sentence of the fan-out rule states the node test; root prompt R24.3 | `graphed-workdir/systematics-vary-plan.md`, `graphed-root-prompt.md` |

One implementation commit (W1+W2) and the test commit; W4/W5 land with the pin bump. Gates as for
every milestone: frozen suite green and unmodified, `scripts/run-tests.sh` all green, diff coverage
≥ 90 % line+branch from the frozen suite, ruff/format/mypy strict clean, Sphinx `-W` clean,
determinism.
