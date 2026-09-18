# m58 — projection honours what sources and Externals declare (decomposition)

Authority: `coffea-fastjet-conda-plan.md` §2.4, §3 row m58 (review-clean r4); root prompt R25.1.
Repo: `graphed-org/graphed`, branch `m58-projection-declarations` off `main`. Python only — no Rust.
Frozen suite: `tests/frozen/awkward/m58/` (own process, per the awkward per-milestone split), helper
prefix `m58_`, traceability `README.md`. Work-item prefix `integ-m58-`.

## Shape (where the two decisions live today)

A partition driver computes the column list each worker's `read_partition(partition, columns,
resources)` receives. Three sites decide it, each with the source DATA object in scope (regenerate:
`grep -rn "read_partition(\|_evaluation_columns" python/graphed`): `graphed.aggregate.aggregate_plan`
(`read_columns`), and in `graphed/awkward/io.py` the `to_parquet` driver (`_evaluation_columns`) and the
varied write (`_evaluation_columns_union`). `graphed.write.PartitionedSource` is a `runtime_checkable`
Protocol (`partitions`, `read_partition`) whose `isinstance` check is how drivers find the source.
`graphed/awkward/projection.py::_replay` replays a graph on typetracers; its `on_external` marks the
inputs' data touched and continues with `inputs[0]` as the External's stand-in.

## integ-m58-H — the source decides its read list

Contract (each line is one frozen property):
- H1. A source object with a callable `projected_columns` attribute is asked, driver-side, once per driver
  call, with the tuple of output `Array`s the driver was given (all of them, in the caller's order); its
  return, as a tuple, is exactly the `columns` every `read_partition` call of that plan receives. Holds for
  all three drivers.
- H2. A source without the attribute behaves as on `main`: same `columns`, and
  `isinstance(source, PartitionedSource)` is still true (the Protocol gains no member).
- H3. The hook is not called on workers: the plan carries the result (witness: a call counter on the source
  across plan build + a `ThreadExecutor` run; and the plan round-trips through `pickle` with a source whose
  hook raises if called again).
- H4. Determinism: two builds of the same program give byte-identical plans; graphed neither sorts nor
  dedupes the hook's answer.
- H5. `graphed.read_columns_by_label` is untouched (it has no source object): same answer with and without
  a hook on the source.
- Docs: the `PartitionedSource` docstring and the partitioned-read section of the awkward design page name
  the optional capability and who calls it.

## integ-m58-E — an External's stand-in is its declared form

- E1. In buffer/column projection, the value that stands in for an External's output is a typetracer of the
  node's RECORDED form, so an op downstream that is valid only on that form (e.g. `gak.num(x, axis=2)` on
  an External declared one level deeper than its first input) projects instead of raising; the External's
  inputs are reported fully read, as today.
- E2. For an External whose recorded form equals its first input's, reports are identical to `main`.
- E3. The stand-in carries the session backend's behavior (a behavior property read on the External's
  output resolves during projection).

## Non-goals

No change to `read_columns`' own answer, to `PartitionedSource`'s members, to the flat uproot source or the
parquet loader, to any existing frozen suite. No `columns=` argument on `aggregate_plan`.

## Size and commits

~80 src + ~250 test, one commit for the frozen suite (test-author), one for the implementation + extra
tests + docs (implementer).

## Gates

The project's mechanical gates (frozen green, diff coverage ≥ 90 % from the frozen suite, prek, mypy
--strict, determinism, integrity scan) via `python -m graphed_orchestrator.precommit`; TEST_SANITY before
the freeze tag `freeze-m58`: collects on `main`, every H/E property fails on `main` for its own reason
(H1/H3/H4: the hook is never consulted; E1/E3: the stand-in is the first input), H2/H5/E2 are the
regression controls and pass on `main`, two runs identical.
