# graphed → coffea NanoEvents, fastjet, conda-forge — plan (r4, review-clean 2026-09-18)

Evidence lives in `coffea-fastjet-conda-findings/<lane>.md` (gap ids `lane:Gn`) and the probe
scripts under `<session scratchpad>/scout/lanes/<lane>/`; this file holds decisions only.
Work-item prefix: `integ-<milestone|arc>-<item>`.

## TOC
- [1. Shape](#1-shape)
- [2. Decisions](#2-decisions)
- [3. Work units, order, size](#3-work-units-order-size)
- [4. Process per unit](#4-process-per-unit)
- [5. Owner input needed](#5-owner-input-needed)
- [6. Named later phases](#6-named-later-phases)

## 1. Shape

**coffea NanoEvents, dask mode** (derived — coffea states it nowhere; trace
`NanoEventsFactory.from_root(mode="dask")` → `events()`, `nano-factory-seam.md` §Shape). Four parts, one
seam. `NanoEventsFactory` owns *when*: it stores `partial(uproot.dask, …, open_files=False)` and calls it
with `form_mapping=<schema mapper>` in `events()`, then plants `attrs["@original_array"]`.
`_map_schema_uproot` is the seam object (uproot's `ImplementsFormMapping` + `…Info`): form translation,
`buffer_key`, `keys_for_buffer_keys`, `load_buffers`. The schema owns names/shape, encoding each leaf's read
recipe in its `form_key`. `uproot._dask` owns partitioning, projection, reading. Boundary: uproot never
knows a schema, coffea never knows a graph layer. Behaviors (`nanoevents/methods/*`) add deferred support
through `dask_property`/`dask_method` descriptors (`coffea/util.py`) whose `.dask` arm receives the
collection as `dask_array`; cross-references resolve through `_events()` ← `attrs["@original_array"]`.

**fastjet, dask arm** (`fastjet-dask.md` §Shape): `ClusterSequence.__init__` dispatches on input type;
`_pyjet.py` holds the dask class whose every query is an independent `map_partitions` that re-clusters, with
meta from a length-zero run of the eager class.

**graphed seams** (`docs/architecture.rst`, `docs/frontend/design.rst`; `graphed-seams.md`):
`Session.source(name, form, data)` + `graphed.write.PartitionedSource` (partitions/read_partition) for
sources; `Session.record_external(descriptor=, form=)` for a third-party deferred op (graphed-histogram's
path): the evaluator passed to `record_external` is registered on the Session and `aggregate_plan`
wires every surviving External itself, keyed by `external_key` (content hash + params); behaviors via
`BoundMethod`/`method` ops; `aggregate_plan` decides each worker's read list.

## 2. Decisions

1. **coffea surface = `mode="graphed"`** in `NanoEventsFactory.from_root`, arms beside the dask arms
   (owner's framing). Graphed-specific code lives in one module `coffea/nanoevents/_graphed.py`; graphed is
   imported lazily; extra `graphed` gated `python_version >= "3.11"`.
2. **The reader boundary is kept**: the schema'd source is uproot's job. `uproot.graphed` gains
   `form_mapping=` (+ `known_base_form=`, first-file form as `_dask` does) and a mapped read path
   (`info.load_buffers` → `awkward.from_buffers`); `_map_schema_uproot` is reused unchanged. The
   dotted-path → buffer-key walk that feeds `keys_for_buffer_keys` lives in uproot (pure form walking).
   `uproot.graphed` today builds its own `Session(AwkwardBackend(behavior=…))`; it also gains a `backend=`
   parameter (a Backend instance) so coffea can supply the backend whose `array_type()` installs the
   subclass of decision 3. Pool workers get that backend the way graphed already provides: an import
   reference passed to `aggregate_plan(backend=)`, which coffea documents and exports as a module-level
   factory.
   Rejected: a coffea-owned `PartitionedSource` (`nano-behaviors:G9`) — it re-implements the reader in
   coffea and breaks the boundary.
3. **Cross-references are explicit graph edges, not attrs magic.** A coffea `graphed.Array` subclass
   (installed through the backend's `array_type()`) mirrors `dask_awkward.Array.__getattr__`. Every
   behavior name takes exactly one route, tried in this order: (a) a field → field access; (b) a
   `no_dispatch` descriptor → run eagerly on the session typetracer; (c) — none: a `.graphed`
   registration slot beside `.dask` was measured dead (the global-index methods record the identical
   `method` node through route (f)), so coffea's descriptors are untouched; (d) a refused name → `NotImplementedError` (the `Systematic` arms, which
   `map_partitions` and mutate); (e) a `_DaskProperty` with a `.dask` arm → that body, with the graphed
   array as `dask_array`; (f) anything else → `graphed.Array`'s own `__getattr__`, unchanged: plain
   `@property`s record as they do today, and methods — `_DaskMethod`s included (`metric_table`, `nearest`,
   `delta_r`) — come back as `BoundMethod` and record `method` ops; their `.dask` bodies never run on a
   graphed array. The route test's population is every name the subclass can be asked for on the admitted
   schemas — fields, descriptors (`no_dispatch` ones included) and plain properties, from an AST walk of
   the behavior classes — and asserts each route's representative bit-for-bit vs eager. Recorded cross-references are closure-free with both collections as operands (measured), so
   projection and workers need no attrs on chunks. Rejected as the primary design: running cross-references inside one `field` op via a
   self-referential `@original_array` on typetracer and chunks (`nano-factory-seam:G2/G6`) — hidden edges,
   and it needs attrs planted on every read.
4. **Read set for a schema'd source is the source's decision, not the user's.** One helper in graphed
   decides a partition read list: if the source object has a `projected_columns(outputs)` attribute
   (found with `getattr` — it is NOT added to the `runtime_checkable` `PartitionedSource` Protocol, whose
   `isinstance` check filters sources and would then reject every existing implementer) it is asked,
   otherwise today's computation stands. The helper replaces the computation at every site that feeds
   `read_partition` (regenerate with `grep -rn "read_partition(\|_evaluation_columns" python/graphed`):
   `aggregate_plan`, and the two write drivers in `graphed/awkward/io.py`. `read_columns_by_label` has no
   source object and stays the syntactic diagnostic it is documented as. uproot's mapped source
   implements it: the union over all outputs of graphed's buffer report (`project_buffers` — DATA *and*
   OFFSETS needs, so a count-only output still reads its counter), through the path→buffer-key walk, into
   `info.keys_for_buffer_keys`. The user's `aggregate_plan(...)` call is unchanged. Guard: two outputs, one
   count-only (`gak.num(events.Jet, axis=1)`), the plan's read list carries `nJet`, bit-for-bit vs eager.
5. **fastjet arm = `src/fastjet/_graphed.py`** mirroring the dask half of `_pyjet.py` method for method,
   one `isinstance` branch in `ClusterSequence.__init__` (bind the class via `from … import`, never
   `import fastjet._graphed` inside the method); a flat (single-event) particle collection is refused — a graphed array's first axis is the
   partition axis, so one event cannot be split across partitions and the length-zero form recipe crashes
   fastjet's single-event backend at record time, recording through `Session.record_external(descriptor=,
   form=)` with a content-hashed descriptor and a module-level picklable evaluator; forms from the
   length-zero recipe; Varied operands expanded per member. The descriptor hashes the jet definition;
   the query name and its arguments are the node's params, so two queries off one `JetDefinition` are
   distinct nodes with their own evaluators. The arm exposes no `externals` mapping: `record_external`
   registers the evaluator and `aggregate_plan(*queries, …)` wires it (guard: that two-query test, built
   with `aggregate_plan` alone, no private graphed attribute touched in `_graphed.py`). Dask parity on cost (re-cluster per query). The `graphed` extra
   carries `python_version >= "3.11"` (fastjet's floor and CI include 3.10). An AST test pins the method
   set equal to the awkward class's.
6. **fastjet list-starts bug** (`fastjet-dask:G6`) is fixed at its root in C++ — `interfacemulti` indexes
   the buffers by each event's own `[start, stop)` — as its own upstream PR, scikit-hep/fastjet#400
   (branch `fix-nonzero-list-starts` on the fork). The graphed arm (F1) branches from it and adds no
   packing of its own; its tests include a sliced in-memory input, which only a build with the fix passes.
7. **uproot**: a stacked branch on the fork (`graphed-form-mapping` on `graphed-mvp`); the upstream PR opens
   when #1720 merges. #1720 itself stays as reviewed.
8. **graphed changes ride the gated pipeline** as three milestones (§3), then one release request (0.0.3).
   coffea/fastjet/uproot upstream CI can only install released graphed, so their PRs raise the floor to the
   release that carries what they use.
9. **conda-forge**: one staged-recipes PR, three v1 `recipe.yaml` directories (graphed abi3 single build
   via `python-abi3` + `version_independent`, unpinned `${{ compiler('rust') }}`, `cargo-bundle-licenses`;
   the two pure packages `noarch: python`; executors' dask/parsl as `run_constraints`; fat LTO on; no
   free-threaded build). Submit at 0.0.2 with `LICENSE.txt` beside each recipe. The bump to 0.0.3 is
   version + sha256 + `license_file` repointed at the sdist's own `LICENSE` (keeping `THIRDPARTY.yml` for
   graphed) + deletion of the recipe-folder copies — conda-forge allows those only while the archive has
   none.
10. **LICENSE files** (MIT, "Copyright (c) 2026 graphed-org members" — owner's line): graphed#31,
    graphed-executors#16, graphed-histogram#16; both build backends ship the file with no configuration.
    They ride 0.0.3. The recipe-folder copies in `conda-recipes/` carry the same text.
11. **Not in the first coffea PR, refused loudly instead of failing open**: `maybe_map_partitions` raises
    `NotImplementedError` on a graphed array (today it silently runs eagerly). `analysis_tools` is left
    untouched — `_ensure_flat` already rejects a graphed array loudly, and admitting the type there would
    turn `PackedSelection.add` into a silent no-op (guard: `PackedSelection().add("cut", graphed_mask)`
    raises). In `from_root(mode="graphed")`: the `steps_per_file` parameter, and the
    `allow_read_errors_with_report` key of `uproot_options`, are rejected with pointers to
    `aggregate_plan(steps_per_file=)` and `graphed.checkpoint.run_resumable`; user callables (`metric=`)
    and the `Systematic` arms are rejected with a pointer to `graphed.vary`. `"graphed"` joins the shared
    `_allowed_modes`, so `from_parquet(mode="graphed")` raises `NotImplementedError` explicitly (its dask
    arm raises too; there is nothing to parallel). A schema is admitted only if `__graphed_capable__ = True`
    is in that class's OWN body (`vars(schemaclass).get(...)`, never inherited): NanoAODSchema and
    PFNanoAODSchema, each with a bit-for-bit parity test; ScoutingNanoAODSchema, user subclasses,
    `auto_schema` and a function-valued `schemaclass` raise (guard: one test carrying all of those).

## 3. Work units, order, size

Sizes are src+test LOC from the precedents named in the findings; each unit ≤ one ~1–2k commit unless split.

| # | Unit | Repo | Contents | Size | Needs |
|---|---|---|---|---|---|
| L | LICENSE | 3 graphed repos | PRs open (decision 10) | — | owner merge |
| C | conda | conda-forge/staged-recipes (owner's fork) | the drafts in `conda-recipes/` (recipes + LICENSE.txt) | ~290 | plan review |
| m58 | projection honours declarations | graphed | the read-list helper + `projected_columns` at its three call sites (decision 4; `nano-factory-seam:G3`), existing sources and frozen suites untouched; External stand-in built from the node's recorded form (`fastjet-dask:G2`) | ~80 + ~250 | — |
| m59 | awkward-idiom parity | graphed | tuple/`None` keys in `Array.__getitem__` (`nano-behaviors:G2`, `nano-factory-seam:G5`); numpy-scalar dtype preserved (`coffea-dask-surface:G1`); nested-tuple method outputs (`nano-behaviors:G3`) | ~250 + ~300, 2 commits | m58 DONE |
| m60 | library-integration seams | graphed | `provenance.register_internal(prefix)` (`nano-behaviors:G1`); `Session.record_external` refuses an input recorded in another Session, as `record_op` does (today it reads the foreign `node_id` at face value — silently wrong; F1's cross-session test lands on this); opaque-callable identity no longer `__name__`-only (`graphed-seams:G2`); `from_parquet` keeps record parameters (`fastjet-dask:G5`); export `expand`; architecture.rst: module-level-callables contract (`graphed-seams:G4`) | ~200 + ~250, 2 commits | m59 DONE |
| R | release request 0.0.3 | 3 graphed repos | owner cuts | — | L, m58–m60 |
| U | `uproot.graphed(form_mapping=, known_base_form=, backend=)` | uproot fork, stacked branch | mapped form + read path, `projected_columns` on the source (decision 4), path→buffer-key walk shared with `necessary_columns/_buffers`, `_evaluation_columns`, `graphed_head`; `typenames` + dict `ak_add_doc` honoured | ~280 + ~420 | dev: m58 · upstream: #1720 merged, R |
| F0 | list-starts fix | fastjet fork → upstream PR | scikit-hep/fastjet#400 open (decision 6) | — | upstream review |
| F1 | graphed arm | fastjet fork → upstream PR | §2.5 incl. the marked `graphed` extra, tests mirroring `tests/test_008-dask.py` (collected tests only) | ~430 + ~300 | dev: F0, m58 (`graphed.varied.expand` by module path until m60 exports it) · upstream: F0 merged, R |
| A1 | NanoEvents `mode="graphed"` | coffea fork → upstream PR | §2.1/2.3/2.11: factory arm, `_graphed.py` shim + route test, `__graphed_capable__`, refusals, extra on the four CI install lines gated off py3.10, parity tests vs eager over the dask-armed NanoAOD/PFNano tests, docs page | ~350 + ~800 + docs, 2 commits | dev: U, m58–m60 · upstream: R, an uproot release carrying #1720 + U |

Order: L, C, m58, F0 start now and are independent. m58 → m59 → m60 strictly (project rule); the fork
units are not gated milestones and run beside them. "dev" needs are what the unit's local environment
installs — graphed from `git+https://github.com/graphed-org/graphed@main`, uproot from the fork branch —
and nothing upstream resolves those. "upstream" needs are released artifacts: a unit's upstream PR opens
only when they exist, and the same diff raises the dependency floors to them. uproot's merge-to-release
wait has a median of 38 days (last five releases), so A1's upstream PR trails U by weeks; the owner holds
merge rights in coffea and fastjet.

Forks: `graphed-org/coffea-graphed-mvp`, `graphed-org/fastjet-graphed-mvp` (precedent naming), branch
`graphed-mvp`. fastjet dev loop: a local source build (submodules initialised; `uv pip install <clone>` with brew boost/gmp/mpfr/
swig and gnubin make/libtool on PATH; CGAL not needed; minutes), since F0 changes `_ext.cpp` and F1 sits
on it.

## 4. Process per unit

- graphed milestones: the gated three-role pipeline via `graphed-orchestrator` (test-author → TEST_SANITY →
  FROZEN → implementer → reviewer). A milestone is registered the way m52–m57 were: `python
  scripts/bookkeep.py --set-current m58 …` (`.graphed/state.json` + regenerated README; `python
  scripts/gen_readme.py --check` green) and an R-numbered rule section in `graphed-root-prompt.md`. The
  gated project plan itself is not edited.
- Fork units (U, F0, F1, A1): same three isolated roles, handed off through artifacts in this workdir; tests
  are written in the upstream suite's style from the start and no project machinery is committed to a fork.
  Upstream PR text opens with the robot line; hooks run by hand (org forks get no pre-commit.ci autofix).
- Every unit's tests are mutation-checked (each guards a branch it fails without) and witness the mechanism
  (recorded ops, read lists, clustering counts), not only results. Parity oracle for A1/U: coffea
  `mode="eager"`, bit-for-bit, NaN-aware comparison.
- C: `rattler-build` + `conda-smithy recipe-lint` locally (done for osx-arm64); conda-forge CI is the
  linux/win test.

## 5. Owner input needed

1. Milestone ids m58–m60 (free — no file in this workdir names them) and release 0.0.3 are proposals.
2. Merge calls on the three LICENSE PRs.

## 6. Named later phases (owner: this arc, after A1/F1 land)

- coffea follow-on PRs, in order: `analysis_tools` tri-state mode (PackedSelection/Weights; needs m59) →
  `lookup_base` arm (correctionlib documented as `apply_correction`-preferred) → `_get_hist_class`
  `hist.graphed` branch (needs a hist release) → `jetmet_tools` + a real `maybe_map_partitions` route →
  `lumi_tools`/`dataset_tools.preprocess` on `aggregate_plan`. `ml_tools`: docs pointing at graphed's
  native Externals.
- coffea systematics ↔ `graphed.vary` bridge; `"module:attr"` callable references for `metric=`.
- graphed: per-task scratch for External evaluators → fastjet "cluster once, query many"; public `form=`
  on `graphed.apply`; Session-registered evaluators so `externals=` disappears from call sites.
- Other schemas (PHYSLITE, EDM4HEP, FCC, …) under graphed mode: probe against data before claiming.
