# m55 — lockstep by propagation: the shift form accepts a `Varied` collection member

Owner request (2026-09-08): let the shift form of `graphed.vary` take a `Varied` as a collection
member, so a collection that is a *function* of another varied collection (Type-1 MET of the
varied jets) moves in lockstep by ordinary propagation instead of a hand-built `{tag: record}`
map; then rewrite the tour capstone's `lockstep()` helper with it.

## §1 The gap (measured)

`graphed.vary(ctx, "jes", collections={"Jet": v, "MET": m})` with `v = graphed.vary(jet, "jes",
up=…, down=…)` (the loose form on the context's central jets) and `m = type1_met(raw_met, raw, v,
in_type1)` (propagation) is refused today by `_check_lockstep` in `python/graphed/context.py`:
`collection 'Jet' needs a {tag: record} mapping, got Varied`. Unpacking the same containers by
hand, `{"Jet": {t: member_of(v, f"jes_{t}") …}, "MET": {t: member_of(m, f"jes_{t}") …}}`, is
accepted and mints the same `jes_up` MET node the capstone's `lockstep()` builds, and the
propagated container's nominal interns to the context's own MET node; §4's first test pins the
same facts.

The convenience is therefore an unpack plus the one validation the hand form cannot do (it has no
nominal to check). It is deliberately **narrow**: a container carrying anything beyond the family
being registered is refused loudly, and the hand form stays the spelling for every other program.
A wider rule ("accept any container whose extra labels the context already carries") kept admitting
members it dropped or wrongly refused; this one admits nothing it does not fully unpack.

## §2 Contract

1. **Shape.** In the shift form (`graphed.vary(ctx, name, collections={...})` and the `**tags`
   spelling), a collection's value may be a `{tag: record}` mapping (unchanged) **or** a `Varied`.
   The two may be mixed across collections in one call. `nominal=` stays refused with today's
   message; the declaring channel of `points=` (a mapping, or `(tag, member)` tuples inside an
   iterable — what `_parse_points` routes to declares) stays refused, its message widened to name
   both accepted collection-value shapes (`{tag: record}` and a `Varied`); the placement channel
   of `points=` (`{nuisance: coordinate}` entries) is refused when any value is a `Varied`, naming
   the hand form: such a member unpacks to dependency-free members, so a placement has no fan-out
   to prune and would re-point the label instead.
2. **Exactly this family, nothing else.** A `Varied` member's labels must be exactly `"nominal"`
   plus `f"{name}_{tag}"` for the tags of the one family it carries, and that family must be
   `name`: `set(varied._tags) == {name}` and `set(labels_of(varied)) == {"nominal", *labels}`. Any
   other label — another family's, a joint (`"__"`), a label no family covers — is refused with a
   `GraphedError` naming the collection, the family, the extra labels, and the two spellings that
   work: the loose form on the context's central collection (`graphed.nominal(ctx["Jet"])`, or the
   array that IS that node) with only the tags being added, or `{tag: record}`. This covers,
   loudly: a container built on `ctx["Jet"]` after another family varied it (it inherits that
   family's labels); one whose members read another varied collection (the loose form mints joint
   labels for the cross terms). It does *not* cover stacking new tags onto `name` on the context's
   own varied collection: those labels are exactly this family's, so item 2 admits it, and a
   re-offered tag is refused before anything is minted by `check_family` (`variation tag 'up' is
   already registered under 'jes'`), as the hand form is.
3. **The nominal is the context's.** `accessors.reindex_to(member_of(varied, "nominal"), ctx)`
   must be the same node as the context's current central member of that collection
   (`member_of(current, "nominal")` when the collection is already `Varied`, else the collection
   itself); a different node is refused with a `GraphedError` naming the collection and both
   nodes, because members built from another nominal are not shifts of this collection (a handle
   `reindex_to` itself cannot bring to `ctx` — a descendant's, or a divergent branch's — surfaces
   `reindex_to`'s own error, as it does for a hand-form member). The comparison is on nodes after
   the reindex — the lineage path fixes what the nominal reindexes to; the node equality decides
   admission, not where the container was built; the reindex is the normalisation `_vary_shift`
   already applies to resolved members.
   Wherever the reindexed nominal and the context's central member are different nodes the call is
   refused by this same message even though the hand unpack may succeed there (§4's projected-child
   and record-read legs); the hand form stays those programs' spelling.
4. **Equivalence.** After items 2–3 the container is unpacked to `{tag: member_of(varied,
   f"{name}_{tag}") for tag in varied._tags[name]}` and the existing path runs unchanged
   (`_check_lockstep`, `gather_members` with `composes_as_union=` / `max_universes=`, collision
   checks, `reindex_to`, registration). The universe minted for each `{name}_{tag}` holds the same
   node the hand-unpacked call mints, for every collection in the call.
5. **Transactional.** Every refusal above happens before `gather_members` mints anything, so the
   §4.5 rollback in `graphed.vary` has nothing to undo; the session's point registry after a
   refused call equals the registry before it.
6. **Loose-form registration is unchanged.** Building the container with the loose form registers
   `name`'s label→point pairs; the shift-form call re-mints identical pairs, which the registry
   already tolerates (measured in §1).

Out of scope: accepting a `Varied` in the weight form (`is_weight=True` already takes a container
through `nominal=`/tags), carrying joints or other families through the container form, any
change to the tag grammar.

## §3 Design

One normalisation step in `_vary_shift` (`python/graphed/context.py`), applied to each collection's
value before `_check_lockstep`:

```python
if isinstance(inner, Varied):
    inner = _unpack_varied(ctx, name, collection_name, inner, points)  # `points` = placements
```

`_unpack_varied` refuses per items 1–3 and returns item 4's `{tag: member}` mapping. The nominal
comparison uses node ids of the *reindexed* nominal, never object identity (`ctx._read` hands back
a re-stamped handle). `_check_lockstep`'s "needs a {tag: record} mapping" message widens to name
both accepted shapes. Nothing else changes: `gather_members`, `_vary_loose`, `Varied`, the
registry and the Rust IR are untouched.

Docs: extend the shift-form section of `docs/frontend/design.rst` (near the existing
`vary(ctx, "jes", collections={"Jet": {...` example) with an executed example — jets varied by the
loose form, MET computed from them, both passed as `Varied`s, and the printed proof that the
`jes_up` universe's MET is the MET of the `jes_up` jets. `docs/quickstart.rst` keeps the hand form
(one collection, nothing gained).

## §4 Frozen suite (test author, isolated; `tests/frozen/awkward/m55/`)

Properties to pin, each as its own test; fixtures follow the m53 tree (`m55_` helper prefix, every
new behaviour reached only inside test bodies so the tree collects on a pre-m55 tree and fails at
run time with the pre-m55 `needs a {tag: record} mapping, got Varied` error):

- a `Varied` jets member plus a propagated `Varied` MET member is accepted; for every label the
  universe's Jet and MET nodes equal the nodes the hand-unpacked call mints, and the materialised
  `jes_up` MET equals the MET function applied to the `jes_up` jets;
- mixing a `{tag: record}` Jet with a `Varied` MET is accepted; a `Varied` whose tag set differs
  from the mapping's is refused by the lockstep check;
- item 2's refusals, one leg each, every error naming the collection and the extra labels: a
  container built on `ctx["Jet"]` after `jes` varied it (registered as `jer`); a container whose
  members read another varied collection (joint labels); a container varying a family other than
  `name`. Paired accept: the same `jer` container built on `graphed.nominal(ctx["Jet"])` is
  accepted and its universes' Jet and MET nodes equal the hand unpack's;
- stacking: with `jes` (`up`/`down`) registered, a container built on the nominal with `flat`
  only, plus MET propagated from it, adds `jes_flat` on both collections with the hand call's
  nodes; the same container built on `ctx["Jet"]` re-offers `up`/`down` and is refused with a
  `GraphedError` matched on `already registered under 'jes'`, not on the class alone;
- lineage, each leg at its own context: a container built at `c0` is accepted with the hand
  unpack's nodes both at a masked child `c0[mask]` and at a vary-link descendant
  `graphed.vary(c0, "unclustered", collections={"MET": {...}})` (the ordinary
  build-then-register idiom); three refusals of item 3's message naming both nodes, each failing
  if accepted instead: a rescaled nominal at `c0[mask]`, the `c0`-built container at a projected
  child `graphed.universe(c0, "jes_up")`, and a collection the context reads off the record
  registered at `c0[mask]` — whose twin at `c0` itself is accepted. The last two refuse programs
  the hand unpack accepts today;
- a `points=` placement beside a `Varied` member is refused naming the hand form; the declaring
  spelling's refusal is a regression control;
- after any refusal the session's point registry is unchanged and a following valid registration
  of the same family succeeds.

## §5 Work items and gates

| item | what | where |
|---|---|---|
| W1 | `_unpack_varied` + the normalisation line + widened lockstep message | `python/graphed/context.py` |
| W2 | executed docs example | `docs/frontend/design.rst` |
| W3 | frozen suite (test author) | `tests/frozen/awkward/m55/` |
| W4 | tour capstone: drop `lockstep()`; `jets = graphed.vary(jet, "jes", up=…, down=…)` on the central jets and `collections={"Jet": jets, "MET": type1_met(raw_met, raw, jets, in_type1)}`, the `jer` leg built on `nominal_jets` likewise; re-execute; every pre-existing cell byte-identical modulo timings; the capstone checks still all OK | `coffea-benchmarks-graphed-mvp/graphed-vary-systematics-tour.ipynb` |
| W5 | systematics plan §2 overload (c): widen its "each value maps tags to varied records" — the sentence that states the shift form's accepted collection value — to admit a `Varied`; §2.6 is untouched (it governs name resolution and the result, not the input shape) | `graphed-workdir/systematics-vary-plan.md` |

One implementation commit (W1+W2) and the test commit; W4/W5 land with the pin bump. Gates as for
every milestone: frozen suite green and unmodified, `scripts/run-tests.sh` all green, diff coverage
≥ 90 % line+branch from the frozen suite, ruff/format/mypy strict clean, Sphinx `-W` clean,
determinism (the container-form program and the hand-form program, each in its own Session,
compile to byte-identical stages).
