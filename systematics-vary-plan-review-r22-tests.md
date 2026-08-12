# systematics-vary-plan review — round 14, lens: TEST ARCHITECTURE

- **Document reviewed:** `systematics-vary-plan.md` **r22** (5356 lines; read in full — Part I, §§1–12,
  Anchors appendix, revision history through r19).
- **Lens:** test architecture — non-vacuity/discrimination of every §10 anchor and every
  "frozen-witnessed/-anchored" claim in §§1–9; witness-of-mechanism (R0.10); R0.10a (no wall-clock /
  size thresholds in frozen tests); determinism-gate compatibility; freeze-order hazards;
  traceability (requirement ↔ anchor, both directions); testability of the fixtures as stated.
- **Date:** 2026-07-30 (review executed 2026-08-12 against the pinned roots).
- **Verification roots used (every code fact below was read or executed by me in this session):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607a8ba637ebc1b5db37316adf6e10028dcc`
    (probes run in its `.venv`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe22497b64ce624d4880005af7faddf74f7`
    (probes run in its `.venv`, boost_histogram 1.8.0)
  - `/private/tmp/claude-501/graphed-exec-check` (graphed-executors)
  - `/private/tmp/claude-501/uproot5-graphed` @ `393ecefee80aa4fdf563d938e4ff906f329126d8`
    (branch `graphed-mvp`)
  - `graphed-root-prompt.md` (R0.4a read verbatim at `:147-153`)

## What I checked and found clean (recorded so the next round need not redo it)

Positive verifications, all measured this session:

- **`store.nodes()` is index-aligned with node ids**, so §4.3's spelling
  `store.nodes()[fill_id]["inputs"][:n_axes]` is valid (probe vs `graphed-latest`: ids `[0,1,2]`,
  `all(n["id"] == i)` → `True`). The m29 house pattern uses the search form
  (`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84`); both work.
- **§2.2/§2.3a's property classification is measurably right**: on a 1-D `graphed.numpy` partitioned
  source, `dtype`/`ndim`/`shape` give `Session.node_count()` delta **0** and `T` gives delta **1**
  (`python/graphed/numpy/array.py:76-86,159-161`). r19's three-class rule and r20's 1-D fixture pin
  both hold; a blanket "delta 0 for every property" would indeed red on `T`.
- **m48's four-way fold-order anchor is buildable with r22's storage pin.** Measured, bh 1.8.0:
  `Double`/`Weight` reject `sample=`; `Mean()` accepts `weight=` **and** `sample=` together
  (`Mean` with weight alone raises "Sample key-argument (sample=) needs to be provided"),
  `WeightedMean()` likewise. Since the four-way fixture necessarily carries weights, `Mean()` works —
  r22's pin does not create a second, hidden fixture problem.
- **§5.3 r22's scoping is correct**: `read_columns` carries ONE `conservative` flag across all arrays
  (`python/graphed/projection.py:130,140,142-146`), so a conservative label inside the same varied
  program does collapse the union to `None`.
- **§6.1c/§7.2 r21's operands hold**: `fill_nodes` at `graphed-histogram
  src/graphed_histogram/boost.py:281`, `layout` at `:282`, `aggregate_plan` at `:286`; `_add_groups`
  is a key-wise `+` at `:120-122`; `FillEvaluator.__call__` passes `weight=`/`sample=` straight to
  `h.fill` at `:60-71`.
- **§7.3's resume anchor is safe for a float result at fixed partitioning**, which the plan never
  argues but is load-bearing: `run_resumable` collects `(task_index, partial)` and
  `_reduce_partials` folds `sorted(partials, key=index)`
  (`python/graphed/checkpoint/runner.py:149-158`), so a resumed run reduces in exactly the
  uninterrupted order. §5.5a's "byte-identity is unsafe for aggregated floats" caveat is about
  changing `steps_per_file`, and does **not** infect the m49 interrupt/resume anchor.
- **m48's §4.1 correctionlib anchor is buildable in `graphed-histogram` without a `correctionlib`
  dependency**: `record_external` computes `plugin.content_hash(payload)` at record time and defers
  `plugin.load` (which is the only place `import correctionlib` happens,
  `python/graphed/preserve/externals/correctionlib_external.py:20-24`), and no external plugin module
  imports its framework at module scope. The anchor's observable is record-time only.
- **The 15 corpus references exist with the names m48/m49 assume** (`tests/_corpus/references/`:
  `ttbar_4j1b|4j2b_{nominal,btag_up,btag_down,jes_up,jes_down}`, `ttgamma_{nominal,pho_up,pho_down,
  jes_up,jes_down}`), and `fingerprint`/`bin_values` both round to `STABLE_DECIMALS = 6`
  (`tests/_corpus/graphed_corpus/histograms.py:20,35-37,40-43`), so m48/m49's comparison form does
  absorb per-partition summation order as claimed.
- **R0.10a**: I found exactly one wall-clock threshold in the whole anchor set (§3.3's
  `time(128)/time(16) < 16.0`), and it is the named, argued carve-out with the m4 precedent. m50's
  scaling anchor is a payload-entry COUNT, m51's representation anchors are schema/manifest reads,
  and both explicitly demote their size/time halves to R0.11 reports. No other anchor carries a
  wall-clock or size threshold.
- **Freeze-order sweep**: I re-checked every anchor m50/m51 could contradict — §6.1a's bare-key rule
  (r22 scoping makes axis mode safe), §1.2's label-out-of-identity (sibling-scoped, r13), the §2.3d
  per-class floor and gak/`Array` refusing-class floors (all containment + monotone counts, r18),
  `graphed_histogram.unpack`'s declared union (axis-mode outputs stay inside it), the §7.2
  schema-key-set anchor (§8.2(i)'s field is on `_PartitionReduce`, not on the three named
  dataclasses), and §6.3's pre-m48 golden (nothing in m48 changes unvaried IR recording: the
  `_context` slot, the layout keying, the seam and the diagnostics channel are all outside node
  identity). **No new instance of the r7 "grammar anchor freezes a superseded rejection" class, and
  no anchor left describing r8-era p-form canonical semantics** — §9.1's `variations` anchor names
  both parsers deliberately, and §6.4b's p-form line is explicitly labelled carried-over evidence.
- **Self-derived-oracle sweep** (the §4.3 equal-counts and §5.2a `delta == len(cone)` trap classes):
  I found no new instance. m48's manual-broadcast and manually-re-indexed references are genuine
  independent constructions (the test performs the operation the fill is supposed to perform), m51's
  superset anchor is bound to an eager out-of-graphed oracle, m49(ii) recomputes references
  in-process via `graphed_corpus`, and §5.2a/§5.2c are bound to hand-built no-`vary` oracles.

## Findings

### 1. MID — m51's ROOT half lands in a repo with no coverage instrumentation, no type gate, and a reduced CI matrix; §10 never analyses it

**Section:** §10/m51, §6.4f, DoD line at §10 close.

**Detail.** §10 does a careful per-repo CI analysis for `graphed`, `graphed-histogram` and
`graphed-executors` — it is the reason three anchors were relocated, two install pairs were bound and
the unique-basename rule exists. For `uproot5-graphed-mvp` it establishes only that no frozen tree
exists today and that m51 creates `tests/frozen/m51/`. It never checks whether that tree is *gated*.
Measured at `393ecef`:

- `pyproject.toml:136` → `testpaths = ["tests"]`, so `tests/frozen/m51` **is** collected (good), but
- the only workflow that installs graphed and runs the graphed tests is `.github/workflows/graphed.yml`,
  which runs `python -m pytest -vv tests -m "not xrootd" …` (`:55`) with **zero `--cov`**
  (`grep -c cov .github/workflows/graphed.yml` → `0`), on `ubuntu-latest` only, python `["3.11","3.12"]`
  only, and `on: push: branches: [graphed-mvp]` + `workflow_dispatch` — **not on pull requests**;
- the repo has **no `[tool.mypy]` section at all** and no coverage config (`grep -n
  "cov\|fail_under\|\[tool.mypy\]" pyproject.toml` → only `testpaths` and `[tool.ruff]`).

§6.4f calls the ROOT half ("`graphed_write` gains IR evaluation") **"the larger half of m51"**, and the
DoD requires ≥90 % diff coverage **from the frozen suite**, `mypy --strict`, and full-§A.5-matrix CI
green (R0.5). As configured, none of the three can be discharged for that half: nothing measures its
coverage, nothing type-checks it, and the matrix is one OS × two Pythons.

**Evidence.** `uproot5-graphed .github/workflows/graphed.yml:7-10,26-32,55`; `pyproject.toml:136,143`
(no `[tool.mypy]`); `grep -c "cov" .github/workflows/graphed.yml` → `0`. Contrast the analysis §10
performs for the other three repos (`graphed-histogram .github/workflows/ci.yml:44` with
`--cov=graphed_histogram`, verified in-session).

**Suggested fix.** Give m51 the same treatment §10 gives the other repos: bind (a) a `--cov` invocation
over `src/uproot/writing/_graphed_write.py` (or the milestone's touched modules) in the graphed job, with
the ≥90 % diff-coverage gate; (b) a `[tool.mypy]` config covering the new source and the new frozen
tree; (c) an explicit statement of the CI matrix m51's DONE is keyed on for this repo (either widen
`graphed.yml`, or record in §10 that R0.5's full-matrix requirement is discharged for the `graphed`
side only and name the reduced matrix as the accepted scope). Also add `pull_request` to the trigger,
or state that DONE is keyed on a branch push.

### 2. MID — the DoD's "mypy --strict on src AND tests" is unconfigured in every target repo, and r22 uses it as the sole justification for a frozen anchor's content

**Section:** §10 DoD line; §7.2 / §8.2(i) (the r22 `()` dummy); m48's §6.1a wholly-unvaried control.

**Detail.** The plan's DoD reads "ruff/clippy/mypy-strict (**src AND tests**, R0.4a)", and r22 justifies
two binding decisions with it: the §8.2(i) field type `… | None = None` and the m48 dummy `()` —
*"m48 freezes a 'dummy' read-back under the DoD's `mypy --strict` on src AND tests (measured, `graphed
pyproject.toml:83` → `strict = true`)"*. The cited line is real but does not establish what it is cited
for. Measured at the pinned revisions:

| repo | mypy config | covers tests? |
|---|---|---|
| `graphed` | `pyproject.toml:80-84` — `strict = true` (`:83`), **`files = ["python"]` (`:84`)** | no |
| `graphed-histogram` | `pyproject.toml:70-73` — `strict = true`, **`files = ["src"]`** | no |
| `graphed-executors` | `pyproject.toml:108-111` — `strict = true`, **`files = ["src"]`** | no |
| `uproot5-graphed-mvp` | no `[tool.mypy]` at all | no |

and in both `graphed` and `graphed-histogram` the mypy hook is `pass_filenames: false, always_run:
true` (`.pre-commit-config.yaml:25-35` / `:30-35`), i.e. it runs plain `mypy` and takes `files` from
the config. R0.4a (`graphed-root-prompt.md:147-153`) *does* bind the wider gate and explicitly names
src-only repos as "a known cross-cutting cleanup — widen each `mypy`/lint config and annotate the
tests", so the plan is not wrong to state it — but the widening is a **prerequisite of m48 that no
target line names**, and it is concentrated on the most reflective frozen suite in the project.

The concrete test-architecture consequence, if the retrofit lands with m48 (as R0.4a requires): m48's
(α) return-channel anchor reads the returned dummy off `plan.process`, and `Plan.process` is declared
`Callable[[Partition, WorkerResources], R]` (`python/graphed/core/execution.py:210`), so
`plan.process.variation_labels == ()` is an `attr-defined` error under strict; the test needs a cast to
the module-private `_PartitionReduce` (`python/graphed/aggregate.py:44-55`) or a targeted ignore. Every
other new read-only surface in this plan is pinned in §9.1 with a spelling *precisely* so a test-author
does not freeze a guess (§4.3's own words: "ownership is not an importable surface, and a frozen test
cannot import an internal"); this one is not. The same retrofit also lands on the dynamic gates
(`inspect.getmembers` enumerations, `getattr(type(varied), name, None)`, `s._store.nodes()`), all of
which are `Any`-heavy.

**Evidence.** Files and lines as tabulated above, all read this session; `graphed
.pre-commit-config.yaml:30-35`; `graphed-root-prompt.md:147-153`; `python/graphed/core/execution.py:206-217`.

**Suggested fix.** Either (a) name the R0.4a mypy/lint widening as an explicit m48 target in each repo
(and note that `graphed`'s frozen tree is currently exempt from `ruff format` only, by the recorded
`.graphed/m41/disputes/frozen_format.md` dispute — `pyproject.toml:72-78` — so `ruff check` already
covers it), and bind the (α) anchor's read-back route (a public accessor, or an explicit
"cast to `graphed.aggregate._PartitionReduce`" instruction) the way §9.1 pins every other new read
surface; or (b) restate r22's justification for `()` without leaning on tests being type-checked (the
choice is still right for the *field's* declared type, which is src and is checked).

### 3. LOW — §8.2(i)'s closure field now lands at m48 but appears on no milestone target line, and §7.2's "(β) carries its anchor at m49" is stale

**Section:** §7.2, §7.3, §8.2(i), §10/m48 and §10/m49 target lines.

**Detail.** r22 moved the `variation_labels` field onto `_PartitionReduce` at **m48** (§7.3: "which
forces the additive §8.2(i) field onto `_PartitionReduce` at **m48**"; §8.2(i): "the field is ADDED at
m48 as a defaulted pass-through"). m48's target line names §1, §2, §3.2, §4, §6.1, §6.3, §7.2, §9.1
(partial) — no §8 anything; m49's names "§8" whole. This plan annotates every other cross-milestone
split on those lines explicitly (§2.5's diagnostic → m49; §3.4 → m49, "NOT m48"; §6.1c's axis slot →
m50; `to_parquet` → m51; and r22 itself added "§6.1b's arity anchor is m49's"), each time for the
stated reason that "the DoD scopes an implementer off the target line". §7.2 does say "The field
therefore EXISTS from m48", so the requirement is reachable — but a reviewer checking "targets exactly
as specified" gets two answers, which is the exact defect r18/r19/r20 repaired three times.

Second half: §7.2 still reads "**(α)** carries a `graphed`-side m48 anchor … and **(β)** carries its
anchor at m49". After r21/r22, m48's (α) anchor bullet freezes (β)'s mechanism — "a value returned from
the hook … is carried onto the SHIPPED closure and is readable there (`plan.process`)". (β) is now
anchored at m48 for its channel and at m49 for its payload.

**Evidence.** Plan §10/m48 target line ("Targets: §1, §2 …, §3.2, §4, §6.1 …, §6.3, **§7.2** …, §9.1
partially"); §10/m49 target line ("Targets: §3.3, §3.4 …, §5, §7, §8, plus …"); §7.2's "Each half is
anchored in the repo whose source it is, r20" paragraph; §7.3's r22 churn paragraph; §8.2(i)'s r22
parenthetical; m48's `§7.2's r19 aggregate_plan SEAM (α)` anchor bullet.

**Suggested fix.** Add to m48's target line "**plus §8.2(i)'s FIELD DECLARATION (the defaulted
`variation_labels` pass-through) — m49 only POPULATES it**", annotate m49's "§8" with the same
exception, and re-word §7.2's sentence to "(β)'s return CHANNEL is anchored at m48 with (α); its
per-plan PAYLOAD is anchored at m49 with §8.2(i)".

### 4. LOW — §2.3e's r22 slot-KIND vocabulary is a closed list owned by the FROZEN test, re-introducing the property §10/m48 gives as the reason fixtures live in `src`

**Section:** §2.3e(2) (r22), §10/m48's propagation-gate bullet.

**Detail.** §10/m48 states the design rule verbatim: the propagation gate takes its auxiliary
arguments from `src` fixtures because "a frozen test cannot grow arguments for a function added
later". r22 then binds: "each `src` fixture's substitution slot names its operand KIND (flat numeric /
jagged numeric / record / boolean mask / option type); **the frozen test owns one contexted `Array`
per kind**". The kind vocabulary is therefore frozen: a gak function added later whose primary operand
falls outside those five kinds arrives with its classification and fixture in `src` (as designed) and
still cannot be exercised, because the frozen test has no operand of its kind — it would need editing.
This is the same shape as the r18 finding on `refusing == {gak.join}` (a frozen equality that a future
`src`-side classification reds), which the plan chose to record rather than ignore.

Nothing in m48–m51 trips it: I enumerated the 65 public gak functions
(`python/graphed/awkward/functions.py`, `join combinations cartesian zip with_field num count sum …
head sample`) and every primary operand among the *broadcast* / *container-traversing* /
*tuple-returning* classes falls inside the five kinds.

**Evidence.** Plan §2.3e(2) r22 clause; §10/m48's "a frozen test cannot grow arguments for a function
added later"; function list measured this session (`grep "^def [a-z]" …/functions.py`, 73 defs / 65
public).

**Suggested fix.** Record the trap the way r18 recorded its twin — one sentence noting that the kind
vocabulary is frozen at m48 and that a future function needing a sixth kind requires a Test Dispute or
a new milestone's gate — or make the kind→operand table itself a `src`-side fixture the frozen test
iterates (keeping r16's property by asserting the test, not the fixture, owns the *context*: the test
can supply the context object and have `src` supply only the form/layout for each kind).

### 5. LOW — r22's new "an axis-mode output with no variations is still keyed `(output, None)`" rule is witnessable but unanchored

**Section:** §6.1a (r22 scoping), §6.1c, §10/m50's mixed-mode anchor.

**Detail.** r22 added the rule because "the MODE, not the variation count, decides an axis-mode
output's key" and because "m48/m50 freeze the plan value's slot-keyed shape directly, so without the
scoping the test-author's pick between two defensible key forms is frozen read-only for the wrong
reason". The rule is directly observable (the anchors assert the plan value's KEY SET), yet no anchor
carries the program it protects: m50's mixed-mode anchor carries an axis-mode **varied** output, a
sibling-mode varied output, and a third output "no variation reaches" whose asserted key is **bare**
— i.e. sibling-mode. So an implementation that keys an unvaried axis-mode output bare passes every
m48–m51 anchor while contradicting the rule. (This is not the r19 MODE-field situation: that field was
deleted *because* it was unwitnessable; this one is witnessable and simply uncovered.)

**Evidence.** Plan §6.1a's r22 paragraph; §6.1c's r22 sentence; §10/m50's "MIXED-MODE PLAN" anchor
("plus a third output no variation reaches … the unvaried output to a BARE `hist` under its bare key").

**Suggested fix.** Add a fourth output to m50's mixed-mode program — axis-mode opt-in, no variations —
and assert its slot key is `(output, None)` and that it unpacks to a bare 1-bin-variation-axis
histogram. Cost: one histogram in an existing fixture.

### 6. LOW — m49's §3.4 impact-set anchor names a fixture shape the test-author cannot build by any other route, and the plan never says which route it is

**Section:** §3.4, §10/m49's impact-set anchor.

**Detail.** The anchor is "three labels where two share a derived node — the shared node appears in
both impact sets". Under hash-consing, two labels share a node **iff** that node's inputs are the same
ids, which (transitively, back to the fork) requires their `vary` members to be *structurally
identical* — verified: interning returns the existing id for an identical key
(`src/store.rs:73-88`; probe this session: `a = src * 2.0; b = src * 2.0` → `a.node_id == b.node_id ==
1`, `node_count() == 2`). There is no partial-sharing construction: any op whose inputs differ per
label produces a distinct id. So the only frontend fixture is `vary(x, "jes", up=e, down=e)` with one
expression under two labels — which is §1.2's dedup case, and under it the two impact sets are
*identical*, not merely overlapping. That is fine for the assertion's real purpose (it discriminates
the id-watermark implementation §3.4 rejects, which would hand `jes_down` an EMPTY set, since the
second label records no new nodes), but the plan spares the test-author a mid-freeze discovery for
`gak.full_like`, the corpus `stable()` rounding, `h.axes.name`, the pt-cut jets, the correctionlib
recording spelling and the `Mean` storage — and not for this one, where the naive fixture (two labels
with *different* members and a "shared" downstream op) does not exist.

**Evidence.** `src/store.rs:73-88` (interning); probe above; §3.4's own "a node shared by `jes_up` and
`jes_down` but not nominal appears in **both** impact sets"; §10/m49's impact-set bullet.

**Suggested fix.** State the fixture in the anchor: "the shared node is obtained by giving two labels
the SAME member expression (§1.2's dedup case), which is the only construction interning admits; the
discriminator is that a watermark-based implementation gives the second label an EMPTY impact set."

### 7. NIT — §2.3d decides the discovery status of five of the nine new `graphed.__all__` verbs and is silent on the other four

**Section:** §2.3d (discovery rule + exclusions), §9.1.

**Detail.** The m48 gate enumerates `graphed.__all__`, keeps `inspect.isfunction` members "any of whose
parameter annotations MENTIONS `Array`", and asserts every member of that union carries a disposition.
m48 adds nine public verbs: `vary` (excluded by name, r15), `context_of` (*eager-metadata*),
`broadcast_like` (*broadcasting*), `reindex_to` (*broadcasting*, r20), `unify_contexts` (no
disposition, justified: "takes context handles rather than `Array`s"), and `labels`, `universe`,
`nominal`, `weight` — for which the plan says nothing. Their natural annotations (a `Varied`, a
context, or §6.1a's histogram/dict result shapes) mention no `Array`, so nothing reds today; but the
identical silence about `broadcast_like` cost r14 a revision and about `vary` cost r15 one, and r20
went out of its way to pre-classify m49's two future verbs for exactly this reason.

**Evidence.** Plan §2.3d's "Two exclusions are bound too (r15)" and "The m49 verbs this plan itself
adds enter the table *expanding* when they land, r20"; §9.1's surface list; §2.6a's module-function
enumeration.

**Suggested fix.** One sentence in §2.3d: "`graphed.labels`/`universe`/`nominal`/`weight` take a
`Varied`, a context or a result mapping — never an `Array` — so they are outside the
`Array`-consuming surface and carry no disposition, like `unify_contexts`."

## Verdict

**Dirty, but shallow — nothing blocks starting m48's TEST_AUTHORING.**

No BLOCKER and no HIGH. I could not find a single anchor that is vacuous as worded, that would pass a
plausible wrong implementation, that would red against a correct one, that violates R0.10a, that
breaks the determinism gate, or that freezes a semantic a later milestone must contradict — the r7/r9
freeze-order sweeps and the r19–r22 message/storage/scoping repairs have left the anchor set in good
shape, and the four r22 changes I could check by measurement (the `Mean`/`WeightedMean` pin, the
`read_columns` conservative scoping, the per-link-kind `reindex_to` split, the m51 write-path merge
refusal) are all correct and all buildable.

The two MID findings are both *gating* defects rather than anchor defects: the frozen suites as
specified are fine, but for one repo (`uproot5-graphed-mvp`) nothing measures or type-checks what they
cover, and for all four repos the DoD names a type gate that is not configured — with r22 having
leaned on that gate to justify a frozen anchor's content. Both are cheap to fix in the plan text
(name the retrofit, bind the (α) read-back route, bind m51's coverage/type/matrix scope). The four
LOW/NIT findings are all one-sentence or one-fixture additions.
