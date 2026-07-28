# Systematics-vary litsearch (agent fan-out, 2026-07-28)

Source: workflow wf_e7666c8a-794, 4 prior-art researchers (RDF Vary, RDF production analyses, coffea, pythonic analyses). URL-cited; UNVERIFIED items are labeled.



---

# [rdf-vary]

# ROOT RDataFrame `Vary` / `VariationsFor` — precedent deep-dive for a graphed systematics node

Sources verified 2026-07-28. `file:line` refs are to `root-project/root` **master**, fetched raw from GitHub (files also mirrored locally under the session scratchpad, e.g. `/private/tmp/claude-501/-Users-lgray-vibe-coding-graphed-workdir/8f54f531-a6e8-4340-a81d-efa35f73b6f6/scratchpad/RInterface.hxx`).

## VERIFIED FACTS

### 1. API surface

Doxygen: [ROOT::RDF::RInterface](https://root.cern/doc/master/classROOT_1_1RDF_1_1RInterface.html) lists **12 `Vary` overloads** = {single column, multi column} × {C++ callable, JITted string expression} × {explicit `variationTags`, auto-generated `nVariations` tags 0..N-1}.

Canonical single-column signature ([RInterface.hxx:874-883](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RInterface.hxx)):

```cpp
template <typename F>
RInterface<Proxied> Vary(std::string_view colName, F &&expression, const ColumnNames_t &inputColumns,
                         const std::vector<std::string> &variationTags, std::string_view variationName = "")
```

- Expression contract: "It must return an RVec of varied values, one for each variation tag, in the same order as the tags" (RInterface.hxx:831-832). The callable "will always receive their _nominal_ value in input" ([RDataFrame.cxx:1227-1229](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/src/RDataFrame.cxx)).
- `variationName` defaults to the column name for single-column Vary: `variationName.empty() ? colName : variationName` (RInterface.hxx:879).
- Multi-column ("lockstep") Vary: first arg is a list of columns, expression "returns an RVec of RVecs of values: one inner RVec for the variations of each affected column" (RInterface.hxx:938-940); `variationName` is **mandatory** there ("we also have to explicitly pass the variation name ... as the default column name does not exist", RDataFrame.cxx:1305-1323). Example produces keys `"ptAndEta:down"`, `"ptAndEta:up"` (RInterface.hxx:944-956).
- Extraction: `template<typename T> RResultMap<T> ROOT::RDF::Experimental::VariationsFor(RResultPtr<T> resPtr)`, header `ROOT/RDFHelpers.hxx` ([Experimental namespace docs](https://root.cern/doc/master/namespaceROOT_1_1RDF_1_1Experimental.html); RDataFrame.cxx:1186).
- Result-map keys: a `"nominal"` key identical to the original result, plus one key per variation, "a composition of variation names and tags, e.g. `pt:up` and `pt:down`" (RInterface.hxx:842-845); "The _full_ variation name will be composed of the varied column name and the variation tags" (RDataFrame.cxx:1218-1219). `RResultMap::GetKeys()` enumerates them (RDataFrame.cxx:1339-1341).
- Introspection: `RVariationsDescription GetVariations() const` on the node ([RInterfaceBase.hxx:218](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RInterfaceBase.hxx)); "A descriptor for the systematic variations known to a given RDataFrame node" ([RVariationsDescription.hxx:26-36](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RVariationsDescription.hxx)).

### 2. Semantics

- Two-step model: "a) register variations for one or more existing columns using Vary() and b) extract variations of normal RDataFrame results using VariationsFor(). In between these steps, no other change to the analysis code is required: the presence of systematic variations for certain columns is automatically propagated through filters, defines and actions" (RDataFrame.cxx:1181-1185; same text on the [RDataFrame class page](https://root.cern/doc/master/classROOT_1_1RDataFrame.html), anchor `systematics`, since v6.26).
- Registration point: `Vary` is a transformation like `Define` — it returns a new `RInterface` whose copy-on-write `RColumnRegister` carries the variation, so it affects only downstream nodes; the varied column must already exist (dataset column or prior `Define`).
- **Single event loop**: "RDataFrame computes all variations as part of a single loop over the data. In particular, this means that I/O and computation of values shared among variations only happen once for all variations. Thus, the event loop run-time typically scales much better than linearly with the number of variations" (RInterface.hxx:861-865).
- Laziness: "RDataFrame lazily computes the varied values required to produce the outputs of VariationsFor(). If VariationsFor() was not called for a result, the computations are only run for the nominal case" (RInterface.hxx:867-870). "VariationsFor does not trigger the event loop. The event loop is only triggered upon first access to a valid key, similarly to what happens with RResultPtr" ([Experimental namespace docs](https://root.cern/doc/master/namespaceROOT_1_1RDF_1_1Experimental.html)).
- Filters/cutflow re-run per variation: "To produce the varied results, RDataFrame will automatically execute the Filter and Define calls for each variation and fill the histogram with values and cuts that depend on the variation" (RDataFrame.cxx:1222-1224) — i.e. SHIFT-systematic semantics are native.
- **No combinatorics**: "only one variation is applied at a time, i.e. there will be no result produced by applying multiple systematic variations at the same time" — `{"nominal","pt:down","pt:up","eta:0","eta:1"}`, "but no `pt:up&&eta:0`" (RDataFrame.cxx:1325-1341).
- WEIGHT-systematic idiom is just Vary on the weight column: tutorial [df106_HiggsToFourLeptons.py](https://raw.githubusercontent.com/root-project/root/master/tutorials/analysis/dataframe/df106_HiggsToFourLeptons.py) line 195 `.Vary("weight", "variationsFactory(weight, goodlep_pt, goodlep_type)", ["up", "down"])`, line 198 `histos_mc = ROOT.RDF.Experimental.VariationsFor(df_variations_mc)` ([rendered tutorial](https://root.cern/doc/master/df106__HiggsToFourLeptons_8py.html)). RDF has no special weight-vs-shift distinction — both are column variations; the engine discovers the difference via dependencies.

### 3. What is / is not varied

- `VariationsFor` restrictions: "Currently, producing variations for the results of Display, Report and Snapshot actions is not supported" ([Experimental namespace docs](https://root.cern/doc/master/namespaceROOT_1_1RDF_1_1Experimental.html)).
- Snapshot has a *separate* mechanism: `RSnapshotOptions::fIncludeVariations` writes varied columns as `<ColumnName>__<VariationName>_<VariationTag>` plus per-event validity **bitmasks** (`R_rdf_mask_*`, a `std::bitset<64>` written as `uint64_t`, one mask column per 64 columns, with a name→(mask,bit) mapping object in the file), because a variation may fail a Filter the nominal passed; "If none of the filters pass ... the entire event is omitted." "Snapshot with variations is currently restricted to single-threaded TTree snapshots" (RDataFrame.cxx:1240-1303).
- `RResultMap`/`VariationsFor` still live in `ROOT::RDF::Experimental` "to indicate that these interfaces can still evolve" (RDataFrame.cxx:1230-1231).
- Distributed RDF: `Vary`/`VariationsFor` are in the supported distributed API subset with "zero code change between local and distributed" ([RDataFrame class ref v6.32](https://root.cern/doc/v632/classROOT_1_1RDataFrame.html); [distributed-RDF blog](https://root.cern/blog/distributed-rdataframe/)); `RVariedAction::GetMergeableValue` packages per-variation values for cross-process merging ([RVariedAction.hxx](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RVariedAction.hxx) ~line 221).

### 4. Internal architecture — the "impact analysis" precedent

The nominal graph is built once; **varied "universes" are materialized lazily and only for the sub-graph downstream of a varied column**:

- [RColumnRegister.hxx](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RColumnRegister.hxx): "A binder for user-defined columns, variations and aliases"; `fVariations` is an "Immutable multimap of Variations ... The key is the name of an existing column, the values are all variations that affect that column"; `GetVariationsFor()` / `GetVariationDeps()` compute which variations transitively affect a column list. Registers are copy-on-write: instances "are the same or only differ by a single extra defined/varied/aliased column."
- [RVariationBase.hxx](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RVariationBase.hxx): type-erased holder of `fColNames`, `fVariationNames` (tags), `fVariationName`; the concrete `RVariation` evaluates the user callable once per entry per slot and caches (`fLastCheckedEntry`, [RVariation.hxx:232-238](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RVariation.hxx)) — so one evaluation yields all tags' values for that entry.
- [RDefine.hxx:159-177](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RDefine.hxx) `MakeVariations`: "Create clones of this Define that work with values in varied 'universes'" — and it **skips cloning** when "this Defined quantity does not depend on this variation"; `GetVariedDefine` returns the nominal define if unaffected.
- [RFilter.hxx:207-234](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RFilter.hxx) `GetVariedFilter`: clones the filter per variation and recursively substitutes the upstream node only if the upstream chain is itself affected (`IsStrInVec(variationName, prevNode->GetVariations())`); unaffected upstream filters are shared.
- [RVariedAction.hxx](https://raw.githubusercontent.com/root-project/root/master/tree/dataframe/inc/ROOT/RDF/RVariedAction.hxx): when `VariationsFor` is called, the action is replaced by an `RVariedAction` holding "Action helpers per variation" (`fHelpers`, ~line 42) and per-variation upstream filter nodes (`fPrevNodes`, ~line 44; loop-manager upstream is reused); its `Run` iterates variations, checks each variation's filter chain, and fills that variation's helper — all inside the one event loop.

So RDF answers "what must re-run per variation?" structurally: **dependency-tracked shadow copies of only the affected Defines/Filters/action, sharing everything else** — I/O, unaffected columns, unaffected cuts. The design is described in Guiraud et al., ["RDataFrame enhancements for HEP analyses"](https://iopscience.iop.org/article/10.1088/1742-6596/2438/1/012116), J.Phys.Conf.Ser. 2438 (2023) 012116 (ACAT 2021): "a dedicated syntax to define systematic variations ... by giving RDataFrame semantic information about user intention, allows certain optimizations in the construction of its computation graph" (abstract; full text paywalled — deeper quotes UNVERIFIED).

### 5. Pain points (forum/community)

- Naive per-variation loops are the motivating pain: "book-keeping and processing of systematic uncertainties is the largest pain point in analysis software" ([Second Analysis Ecosystem Workshop Report, arXiv:2212.04889](https://arxiv.org/pdf/2212.04889)).
- Bootstrap use (100 weight variations in one `Vary` with generated tags `bs0..bs99`) works, but docs were unclear on the RVec contract and the provenance of the `"nominal"` key; Guiraud: "The 'nominal' key just points to the same histogram contained in your nominal variable, it's there as a usability thing" ([forum 51037](https://root-forum.cern.ch/t/question-on-rdataframe-vary-functionality-bootsrapping-samples-and-weights/51037)).
- All varied histograms share the nominal's `GetName()`, so writing an `RResultMap` to a file silently keeps only the last one until users rename each ([forum 57782](https://root-forum.cern.ch/t/using-rdataframe-vary-function-and-save-histograms/57782)) — varied results lack distinct identity metadata.
- Snapshot-with-variations semantics (bitmask validity encoding) are subtle enough to generate dedicated doc questions ([forum 64397](https://root-forum.cern.ch/t/documentation-on-bitmap-for-rdataframe-snapshot-with-variations/64397)) and it's single-thread-TTree-only (RDataFrame.cxx:1300).
- UNVERIFIED: claims of memory/JIT blow-up with O(100+) variations. Structurally plausible (per-variation cloned Defines/Filters/helpers ⇒ memory and JIT time linear in affected-subgraph × nVariations), but I found no forum/issue thread or measurement confirming it; do not cite as fact.

### 6. Naming vocabulary (exact)

`Vary` (verb, the registration call) · `variationTags` (e.g. `"up"`/`"down"`, or auto `"0".."N-1"`) · `variationName` (group name, defaults to column name) · `"nominal"` (reserved key) · full key = `variationName + ":" + tag` (`"pt:down"`) · `VariationsFor` (extraction) · `RResultMap<T>` (keyed results, `GetKeys()`) · `RVariationsDescription` / `GetVariations()` (introspection) · internal: "varied **universes**" (RDefine.hxx:159, RFilter.hxx:207), `RVariation`, `RVariedAction`, `MakeVariations`, `GetVariedFilter/GetVariedDefine`. Snapshot columns: `<col>__<variationName>_<tag>`.

## ASSESSMENT / LESSONS

- RDF's key win is **register-then-forget**: one call site attaches variations to columns; propagation is automatic dependency analysis, not user bookkeeping. Users never write per-variation analysis code.
- Weight vs shift systematics need no API distinction — vary the weight column vs vary a kinematic column; the dependency tracker automatically determines the re-run scope (weight ⇒ only the fill; kinematics ⇒ cuts + defines + fill).
- The clone-per-variation "universe" model is exactly graph-level impact analysis, done eagerly-on-demand at action registration; in graphed it maps naturally to IR: substitute varied source nodes, re-derive reachable cone, share the rest via hash-consing (CSE gives the sharing for free that RDF implements by hand with `GetVaried*` caches).
- RDF's weak spots: variations are invisible to results' identity (name-collision gotcha), no variation combinations, no varied `Report`/cutflow, Snapshot needs a bolt-on bitmask encoding because per-variation cutflows diverge — evidence that "varied write-out" and "varied event masks" need first-class design, not retrofit.
- `Experimental` namespace for 4+ years (v6.26 → master) shows extraction/result-map ergonomics are the unstable part, not `Vary` itself.

## Design implications for a graphed Vary-style node

- Adopt RDF's vocabulary verbatim — `vary(col, fn, tags, name=...)`, reserved `"nominal"`, keys `"name:tag"` — it is the established HEP precedent users already know.
- Make variation a **column-level annotation in the IR** (multimap varied-node → variation set, like `RColumnRegister::fVariations`), not a graph transform at registration time; expansion happens at plan time.
- Expansion = IR substitution + reachability: for each variation, substitute the varied column node(s) and rebuild only the downstream cone; hash-consing/CSE then shares all unaffected nodes automatically — graphed's interned IR does structurally what RDF hand-implements with `MakeVariations`/`GetVariedFilter` caches, and equality saturation can then fuse shared prefixes across universes.
- Preserve the two laziness guarantees: registering variations costs nothing until a `variations_for(result)`-style extraction is requested, and all universes execute in a **single pass over each input partition** (shared I/O + shared upstream compute).
- Support multi-column lockstep variation (one expression returning per-column varied values, mandatory group name) — required for real calibrations (e.g. jet pT/mass shifted together); require explicit `name` exactly when >1 column varies.
- The vary expression receives **nominal** inputs and returns one value per tag; evaluate it once per event for all tags (RVariation's caching) — for graphed, emit it as one stage-node with fan-out, not N nodes.
- No automatic variation cross-products; keys are flat `name:tag`. If combinations are ever wanted, that's an explicit user-level product, as in RDF.
- Give varied results first-class identity (variation key embedded in result/histogram metadata and in the Plan/checkpoint content hash) — fixes RDF's name-collision write bug and makes per-variation checkpoint resume natural.
- Decide write-out semantics up front: per-variation cutflows diverge, so varied materialization needs an explicit validity representation (RDF's bitmask precedent) or per-universe partitions; don't retrofit.
- Expose introspection (`get_variations()` per node, RDF's `RVariationsDescription` precedent) and make the varied-cone computation reusable — it doubles as generic "impact analysis" for cache invalidation in the M8 store.

---

# [rdf-users]

# Systematics in production RDataFrame analyses — prior-art report

Evidence base: shallow clones at `/private/tmp/claude-501/prior-art/{WRemnants,narf,mkShapesRDF}`.
Repo URLs + HEADs examined: WRemnants https://github.com/WMass/WRemnants @ `c5be6c6` (2026-07-22), narf https://github.com/bendavid/narf @ `7d73361` (2026-05-22), mkShapesRDF https://github.com/latinos/mkShapesRDF @ `b89a71f` (2026-07-13). All paths below are relative to the clone root; `file:line` refers to those clones.

## VERIFIED FACTS

### 1. WRemnants/narf: NO RDF `Vary` — boost-histogram TENSOR-weight fills

- **Zero uses of RDF `Vary`/`VariationsFor` in WRemnants and narf.** `grep -rn "Vary|VariationsFor"` over `WRemnants/wremnants`, `WRemnants/scripts`, `narf` (\*.py) returns nothing (measured; grep exit empty). narf's README literally opens "narf is not an rdf framework" (`narf/README.md:1-2`).
- Mechanism: narf pythonizes RDF with a custom `HistoBoost` action (`ROOT.pythonization` hook, `narf/narf/histutils.py:714-722`). If a fill column's C++ type is an `Eigen::TensorFixedSize` (detected via `ROOT.narf.tensor_traits[coltype].is_tensor`, `histutils.py:259-277`), the tensor dimensions are appended to the histogram as extra `hist.axis.Integer` axes (or caller-supplied axes) (`histutils.py:281-298`), and storage becomes `ROOT.narf.tensor_accumulator[scalar, Eigen::Sizes]` (`histutils.py:300-310`) — one accumulator per *kinematic* bin holding the whole variation vector (`narf/narf/include/tensorutils.hpp:18-40`).
- Fill is one loop, one atomic shared histogram: `FillBoostHelperAtomic` is a custom `RActionImpl` holding a single `shared_ptr<HISTFILL>` for all slots (`narf/narf/include/FillBoostHelperAtomic.hpp:79-81`); thread safety via `narf::atomic_adaptor` storage, enabled by default when IMT is on (`histutils.py:179-180`: `force_atomic = ROOT.ROOT.IsImplicitMTEnabled()`). So MT memory is O(1) in thread count, not RDF's per-slot histogram clones.
- Weight-vector production: C++ helper functors given as `df.Define(name, helper, [cols...])` return per-event Eigen tensors, e.g. per-eta-bin×up/down muon-scale weights (`WRemnants/wremnants/production/muon_calibration.py:1279-1295`), efficiency stat/syst tensors (`wremnants/production/systematics.py:962-975`), recoil stat/syst weight vectors (`wremnants/production/recoil_tools.py:1395-1414`). Helpers carry python-side `helper.tensor_axes` metadata used at booking (`systematics.py:970-976`, `muon_efficiencies_smooth.py:426,812`).
- Examples of tensor systematics filled into extra axes in ONE pass: mass weights 21/23 points (`systematics.py:127-224`), QCD scale 3×3 tensor from `LHEScaleWeight` (`systematics.py:1327-1342`), PDF Hessians ~100 members with `hist.axis.StrCategory(names, name="pdfVar")` (`systematics.py:450-495`).
- Driver: one RDF graph per dataset with nominal + all syst histograms booked, all run concurrently by `ROOT.narf.RunGraphsWithProgressBar(dfs, ...)` (`narf/narf/graph_builder.py:120`); results pickled lazily via `wums.ioutils.H5PickleProxy` (`graph_builder.py:158`; wums = https://github.com/WMass/wums, submodule per `WRemnants/.gitmodules`).
- The main W histmaker books 44 `HistoBoost` calls directly (measured, `scripts/histmakers/mw_with_mu_eta_pt.py`, 2577 lines) plus dozens through helper functions; `--onlyMainHistograms` exists to skip the systematic booking (`mw_with_mu_eta_pt.py:2134,2293`).

### 2. WRemnants: shift (kinematic) systematics

- **Even genuinely kinematic effects are converted to per-event WEIGHTS where possible.** Muon momentum scale/resolution: CLI-selectable `--muonScaleVariation` ∈ {`smearingWeightsGaus`, `smearingWeightsSplines`, `massWeights`} — all weight-tensor implementations (`wremnants/production/muon_calibration.py:1267-1345`). Recoil/MET calibration uncertainties are likewise weight vectors (`recoil_tools.py:1395-1414`).
- **Alternate-column trick** for smeared kinematics: the same axes are filled with substituted column lists — `make_alt_reco_and_gen_hists` clones the nominal column list and swaps `_pt0/_eta0/_charge0` → `_gen`/`_gen_smeared` variants (`muon_calibration.py:1573-1608`), i.e. "shift" = same graph, different columns into a parallel histogram, no second event loop.
- **Post-hoc transport**: smearing-weight variations computed on gen-smeared kinematics are transported to reco by histogram ratio after the loop: `hist_reco = nominal_reco × (hist_gensmear / nominal_gensmear)` (`muon_calibration.py:1514-1570`).
- Cut migration is handled by making cut-like quantities histogram AXES (e.g. `passIso`, `passMT` fakerate axes appear as `axes_fakerate`/`cols_fakerate` appended to syst hists, `recoil_tools.py:1434-1452`), so downstream selection happens at fit-prep time, not in the loop.

### 3. WRemnants: nuisance bookkeeping

- Histogram naming: `hist_name(baseName, syst)` → `"{base}_{syst}"` (`wremnants/utilities/common.py:98-105`); e.g. `nominal_pdfMSHT20`, `nominal_muonScaleSyst`.
- Fit-prep registry: `Datagroups.addSystematic(histname, name, processes, group/groups, splitGroup={regex}, systAxes=[...], preOp/action, passToFakes, symmetrize, ...)` (`wremnants/postprocessing/datagroups/datagroups.py:1361-1388`) maps a tensor-axis histogram → many named nuisances: `systAxes` names the tensor axes to unroll and `labelsByAxis`/`systNameReplace`/`formatWithValue` build nuisance-parameter names per bin (`datagroups.py:1589-1608,1726-1745`). ~49 `addSystematic`/`add_syst*` call sites in the fit-setup script (measured, `scripts/rabbit/setupRabbit.py`).
- Decorrelation by region: `decorrelateByAxes(hvar, hnom, axesToDecorrNames)` subtracts nominal, duplicates the chosen axes (e.g. eta → `eta_decorr`), rebins, and re-adds nominal — turning one correlated nuisance into per-bin independent ones (`wremnants/postprocessing/rabbit_helpers.py:33-70`; used with `systAxes=["eta_decorr"]` etc., `setupRabbit.py:2398,2029`).
- Central registry of theory-correction weight layouts: `theory_corr_weight_map` dict (`wremnants/production/theory_corrections.py:54+`).

### 4. mkShapesRDF (Latinos): config-driven, native `Vary` + custom mRDF `Vary`

Two-stage architecture:
- **Stage 1 (processor / ntuple production)** uses `mRDF`, a wrapper "that allows to define new columns, drop columns, and use Vary together with Snapshot" (`mkShapesRDF/processor/framework/mRDF.py:6-7`), because native RDF `Vary` is "not compatible with ``Snapshot``" (docstring, `mRDF.py:220-223`). `mRDF.Vary` materializes each variation as a suffixed Define `col_{variationName}{tag}` (`mRDF.py:17-41,185-247`); `mRDF.Define` parses C++ expressions (`ParseCpp`) and auto-propagates variations of dependencies into variations of the new column (`mRDF.py:144-179`); `mRDF.Filter` folds cuts into a `CUT` column and keeps the OR of nominal + all varied cuts so one Snapshot serves every variation (`mRDF.py:249-283`). Kinematic modules call this: lepton scale/resolution `df.Vary("Lepton_pt", "ROOT::RVec<ROOT::RVecF>{Lepton_pt_ScaleUp, Lepton_pt_ScaleDo}", ["up","do"], "leptonScale")` (`processor/modules/LeptonScaleSmearing.py:243-254`), JES/JER/MET sources (`processor/modules/JMECalculator.py:480-492`).
- **Stage 2 (shapeAnalysis / histogramming)** uses plain `ROOT.RDataFrame` + **native** `df.Vary` + `ROOT.RDF.Experimental.VariationsFor(histo)` (`shapeAnalysis/runner.py:281-285,521,587,663,977-980`).
- Nuisance config model (python dict `nuisances[...]`, `examples/test_folder/nuisances.py`): keys `name` (datacard name, era-encoded e.g. `CMS_scale_e_2016`), `type` ∈ {`lnN`, `shape`}, `kind` ∈ {`weight`, `suffix`, `weight_envelope`, `weight_rms`, `weight_square`}, per-sample applicability via `samples: {sampleKey: [upExpr, downExpr]}` (weight ratios like `puWeightUp/puWeight`, even with per-sample normalization factors baked into the expression string, `nuisances.py:233+`), and `AsLnN` to optionally flatten a shape to lnN.
  - `kind: weight` → runner Defines up/down weight exprs and native-Varies the global `weight` column (`runner.py:532-596`).
  - `kind: suffix` → varied kinematics come from **separate pre-produced friend-tree folders** (`folderUp`/`folderDown` per nuisance, `nuisances.py:133-142`); runner attaches them as TChain friends (`runner.py:103-139,255-280`), finds all columns ending with the suffix (`mapUp`/`mapDown`), and native-Varies each *used* base column to its friend-tree counterpart (`runner.py:441-530` — including a "baseCol is never used -> useless to register variation" pruning check, `runner.py:479-484`).
  - `kind: weight_envelope`/`weight_rms` → N-tag Vary with variation name suffixed `_SPECIAL_NUIS_{envelope|rms}` so post-processing knows to collapse N variations into ±1 (`runner.py:597-673`).
- Booking: one `Histo1D/2D/3D` per (cut, variable, sample) on the varied `weight`+columns, then `VariationsFor` per result; per-variation histograms extracted by key and renamed `{name}_{variation}_{sample}_{index}` to avoid ROOT `Replacing existing TH1` name clashes (`runner.py:886-980,1000-1012`).

### 5. Scale / hard-lesson evidence (measured in code, not hearsay)

- Weight pathologies are real: theory weight tensors are clamped, `wrem::makeScaleTensor(LHEScaleWeight, theory_weight_truncate)` and `clamp_tensor_safe(..., -theory_weight_truncate, theory_weight_truncate, 1.0)` (`systematics.py:619,646,1327-1342`; `theory_corrections.py:35-40,381-402`).
- Memory pressure countermeasures in narf/WRemnants: single atomic shared histogram instead of per-slot copies (`FillBoostHelperAtomic.hpp:79-81`); optional `SparseStorage` backed by a concurrent flat map for very sparse high-dim hists (`histutils.py:21-35,183-244`); lazy `H5PickleProxy` result wrappers (`graph_builder.py:158`); `--onlyMainHistograms` escape hatch (`mw_with_mu_eta_pt.py:55,2134`).
- Consistency guards: event-count vs weight-statistics cross-check raises on mismatch (`graph_builder.py:126-128`); mRDF errors when a suffix nuisance finds no varied columns (`runner.py:459-463`); mRDF warns when the same variation is registered with mismatched tags (`mRDF.py:227-234`).
- mkShapesRDF prunes variations whose base column is unused by any histogram/cut (`runner.py:479-484`) — variation registration is cost even before the loop.
- WRemnants example scale: PDF ~100-member StrCategory axis + alphaS (`systematics.py:476-515`), mass 21/23 points (`systematics.py:133-157`), efficiency stat tensors with per-(eta,pt,charge)-bin axes (`muon_efficiencies_smooth.py:812`), all resident in one output file per histmaker run.

### UNVERIFIED

- Why exactly the authors rejected RDF `Vary` in narf/WRemnants (performance vs. it not existing/maturing when narf started) — no written rationale found in either repo; the design itself (tensor fills, one loop, atomic storage) is verified above, the motivation is inference.
- Runtime/memory numbers (no benchmarks were run here; none are committed in the clones examined).
- mkShapesRDF batch-splitting behavior on clusters (`splitSamples`, `runner.py:16`) was not traced end-to-end.

## ASSESSMENT / LESSONS

- **Two ecosystems, two answers, same split.** Both frameworks converge on: WEIGHT systematics = extra data per event in the SAME loop (tensor weight in narf; `Vary`-of-weight in mkShapesRDF); SHIFT systematics = varied *columns* (alternate column lists / friend trees / `Vary` of kinematic columns), still avoiding a second event loop wherever possible.
- **The precision-analysis end (WRemnants) refuses per-variation control flow entirely.** Everything — even momentum scale and MET recoil — is beaten into a per-event weight vector or an alternate-column fill; cuts likely to migrate become histogram axes and are applied at fit-prep. Consequence: the event loop is variation-count-independent in structure; variation count only widens the weight tensor and the histogram.
- **The config-driven end (mkShapesRDF) shows what a *user-facing* nuisance registry looks like:** a flat dict of `{name, type, kind, samples: {sample: exprs}, AsLnN, folders}` that a runner compiles into Vary calls. Per-sample applicability and era-encoded names (`_2016`) are first-class; decorrelation by era = separate nuisance entries with different names.
- **RDF's native Vary was insufficient for both:** mkShapesRDF had to reimplement it for Snapshot (stage 1) and only uses the native one for terminal histogram actions; WRemnants never adopted it. Native Vary's per-variation re-execution of downstream logic is exactly what WRemnants' tensor approach avoids for the (dominant) weight case.
- **Bookkeeping lives OUTSIDE the loop.** WRemnants maps tensor axes → nuisance names late (`systAxes`/`labelsByAxis` at fit prep), so the loop-side artifact is just "histogram with extra labeled axes". Renaming, symmetrization, envelope/RMS collapse, decorrelation-by-axis, group/splitGroup assignment are all post-hoc histogram transforms.
- **Failure modes they defend against:** insane generator weights (clamp), silent variation loss (hard errors on missing varied columns / count mismatches), ROOT name collisions across thousands of per-variation hists, unused-variation cost (pruning), memory blowup (atomic shared storage, sparse storage, lazy proxies, "main histograms only" mode).

## Design implications for a graphed Vary-style node

- Support two distinct lowerings from day one: **weight variations → tensor axis on the fill** (one fused stage, weight becomes a vector; matches narf `HistoBoost` tensor path) and **shift variations → column substitution subgraph** (re-run only the cone from the varied column to affected sinks; matches WRemnants alternate-columns and mkShapesRDF suffix kinds).
- The weight-variation fast path must add a *labeled histogram axis* (StrCategory of variation names, à la `pdfVar`), never N separate histograms — that is the single biggest scaling win proven in WRemnants.
- Make the Vary node's effect set computable: graphed's DCE/reachability should prune variations whose varied column reaches no output (mkShapesRDF does this by hand, `runner.py:479-484`).
- Shift variations should share the un-affected prefix of the graph via CSE/hash-consing automatically — the "one loop, varied columns" pattern is exactly a diamond in the IR, and equality saturation should fuse the common parts; don't generate per-variation full re-runs.
- For selections downstream of a shift, provide both semantics: re-evaluated cuts per variation (native-Vary-style, correct cutflow migration) and cut-as-histogram-axis (WRemnants style) — production analyses use both deliberately.
- Nuisance metadata (name, up/down tag convention, group, era/decorrelation labels, per-dataset applicability, lnN-flattening flag) belongs in a registry attached to the Vary node but OUTSIDE the structural hash of the compute — post-hoc renaming/grouping must not invalidate checkpoints.
- Guarantee deterministic, collision-free naming `{base}_{syst}` / `{col}_{name}{tag}` (both frameworks converged on suffix conventions; ROOT name-clash bugs forced explicit renaming in mkShapesRDF).
- Provide envelope/RMS/symmetrize as post-aggregation graph ops on the variation axis, not as loop-time logic (`_SPECIAL_NUIS_` collapse, `symmetrize=` in `addSystematic`).
- Clamp/validate variation weights at the node boundary (configurable truncation like `theory_weight_truncate`) — pathological generator weights are a verified production hazard.
- Plan for memory: variation axes multiply histogram size, so the executor should keep one shared accumulator per histogram across workers/threads (atomic or merged), and consider sparse storage for high-dimensional variation hists — both already proven necessary in narf.

---

# [coffea-sys]

# Coffea systematics machinery — research report for graphed Vary-node design

**Primary evidence base**: local coffea checkout `/Users/lgray/vibe-coding/coffea-workdir` @ `f34b8bdf` (branch `lgray/coffea`, 2026-06-30; remote `upstream` = https://github.com/scikit-hep/coffea). Diff vs `upstream/master` (`77d1600`) on every file cited below is docstring whitespace + a 6-line JER refactor only (measured via `git diff --stat`), so local line numbers are representative of upstream. AGC file downloaded from https://raw.githubusercontent.com/iris-hep/analysis-grand-challenge/main/analyses/cms-open-data-ttbar/ttbar_analysis_pipeline.py to `/private/tmp/claude-501/.../scratchpad/agc_ttbar.py` (787 lines; line numbers below refer to that download).

---

## VERIFIED FACTS

### 1. `Weights` (coffea/analysis_tools.py) — the weight-systematic container

Class at `src/coffea/analysis_tools.py:196-646`. Docstring scopes it explicitly: "correction factors and systematic effects that **can be encoded as multiplicative modifiers to the event weight**" (:199-200) — weight-type only, no kinematic shifts.

**API shapes** (all verified in source):
- `Weights(size, storeIndividual=False)` (:213) — `size=None` ⇒ delayed (dask-awkward) mode; every op has dual eager/delayed implementations (`__add_eager` :227 / `__add_delayed` :267).
- `add(name, weight, weightUp=None, weightDown=None, shift=False)` (:292) — multiplies `self._weight *= weight`; rejects duplicate names and names ending `Up`/`Down` (:316-321); `shift=True` means up/down are *additive* deltas to nominal (:489-498). Weights must be flat per-event arrays (`_ensure_flat`, :322).
- `add_multivariation(name, weight, modifierNames, weightsUp, weightsDown, shift=False)` (:430) — one nominal, N up/down pairs; variation names rendered as `f"{name}_{modifier}"` (:360,419). Docstring: "particularly useful e.g. for btag SF variations" (:436).
- **Storage as ratios**: variations are stored in `self._modifiers` as `variation/nominal` (in-place divide at :491,499; dask `where(weight!=0, ...)` at :512,520). So a variation costs one extra float array, and the varied total weight is a single multiply.
- `weight(modifier=None)` (:554) — returns `_weight * _modifiers[modifier]`; **missing Down is auto-derived as symmetric inverse**: `self._weight / self._modifiers[...Up]` (:570-571).
- `partial_weight(include=[], exclude=[], modifier=None)` (:574) — subset product; requires `storeIndividual=True` (raises otherwise, :604-607); exactly one of include/exclude (:608-611); modifier must belong to the included set (:631-634). `storeIndividual` keeps every individual weight array alive (`self._weights[name] = weight`, :236) — a deliberate memory-for-flexibility trade.
- `variations` property (:639-646) — set of `nameUp`/`nameDown` strings; string-suffix convention is the whole variation namespace.
- Per-weight `WeightStatistics` (sumw, sumw2, min, max, n) accumulated on every `add` (:258-264).

### 2. The nanoevents `Systematic` prototype (the abandoned/stalled in-IR attempt)

`src/coffea/nanoevents/methods/base.py:54-232` (`Systematic` mixin) + `src/coffea/nanoevents/methods/systematics/` (`UpDownSystematic`, `UpDownMultiSystematic`).

- **API**: `events.add_systematic(name, kind, what, varying_function)` (base.py:146-153); `kind` must be pre-registered via `Systematic.add_kind(kind)` (:60-73); `what` = field name(s) or the literal string `"weight"`; `varying_function` "must close over all non-event-data arguments" (:167).
- **Rendering**: variations are *materialized as extra columns*, not deferred functions. A hidden `__systematics__` record field is broadcast onto the array (:80-81); `_build_variations` stores the varied values under `__systematics__.__{name}__` (UpDownSystematic.py:20-27); `get_variation` then **rebuilds an entire copy of the record** (`awkward.zip` of all fields with the one varied column swapped in, plus a `parameters["variation"] = f"{name}-{what}-{updown}"` tag) (UpDownSystematic.py:33-56). Weight systematics vary a synthetic `__ones__` column and surface as a new `weight_{name}` field (base.py:185-191; UpDownSystematic.py:44-46). Access pattern per docs: `events.systematics.RenFactScale.up.weight_RenFactScale`, `muons.systematics.PtScale.up.pt` (https://coffea-hep.readthedocs.io/en/latest/notebooks/systematics.html).
- **The unsolved core**: `explodes_how()` is an abstract method whose body is literally a placeholder joke — "This describes how a systematic uncertainty needs to be evaluated in the context of other systematic uncertainties… this function contains decades of thinking about iterate over systematics variations / your opinions about systematics go here. :D" (base.py:131-139). Never implemented in any subclass (grep of `systematics/` package). I.e. the *combinatorics/scheduling* of variations was explicitly deferred and never designed.
- **Selection propagation never solved**: the docs page ends with "TODO: Make it so that `syst_muons.Y > X` returns boolean values for all variations over Y. Requires some tracking of (pieces of) 'what'." (same URL) — varied cuts (the SHIFT-systematic cutflow problem) remained a TODO.
- **Timeline** (local `git log --follow`): created 2021-05-13 ("move systematics into nanoevents"), docstrings 2022-03-07, then dormant; dask-mode support only merged **2025-07-12** ("feat: systematics handling for dask mode (#786)") — a ~3-year stall on the prototype. AGC's own code comments still say "need to adjust schema to instead use coffea add_systematic feature" (agc_ttbar.py:208), i.e. even the flagship demo never adopted it.

### 3. The jetmet shift pattern (`CorrectedJetsFactory` / `CorrectedMETFactory`) — the pattern analyses actually use

`src/coffea/jetmet_tools/CorrectedJetsFactory.py:205-501` (`build(injets)`):
- Flattens jets, stashes originals (`pt_orig`, `mass_orig`, :242-243), computes JEC/JER/uncertainty arrays; in dask mode everything routes through `maybe_map_partitions` (lazy graph nodes, e.g. :300,305,474), eager mode computes immediately — "lazy" = dask-awkward delayed, not virtual columns (older 0.7.x used awkward virtual arrays; current code is dask-delayed).
- **Each variation is a full shifted copy of the jet record embedded as a nested field**: `out_dict["JER"] = awkward.zip({"up": up, "down": down}, with_name="JetSystematic")` (:411-413); per-uncertainty-source `out_dict[f"JES_{name}"] = ...build_variant...` (:472-483), where `build_variation` zips *all* jet fields with only pt/mass replaced (:432-453). Result: `corrected_jets.JES_jes.up.pt` etc. (verified in docs notebook `docs/source/notebooks/applying_corrections.ipynb`, cells printing `corrected_jets.JES_jes.up.pt / corrected_jets.pt_raw`).
- `CorrectedMETFactory.build(in_MET, in_corrected_jets)` propagates every jet variant into MET and adds `MET_UnclusteredEnergy` (CorrectedMETFactory.py:66-222).
- **The analysis loop** (real-world usage, verified in https://github.com/jennetd/hbb-coffea `boostedhiggs/vbfprocessor.py`): a `shifts` list of `(collection-replacement dict, name)` pairs, e.g. `({"Jet": jets.JES_jes.up, "FatJet": fatjets.JES_jes.up, "MET": met.JES_jes.up}, "JESUp")` (:128-144), then `return processor.accumulate(self.process_shift(update(events, collections), name) for collections, name in shifts)` (:149). **Cost model: the entire selection + observable + fill code (`process_shift`) re-executes once per shift**; only the raw file read and the correction-factor computation are shared. Nothing dedups the unaffected sub-computations between shifts.

### 4. AGC ttbar — the concrete systematics inventory + loop structure

From `agc_ttbar.py` (iris-hep/analysis-grand-challenge, `main`):
- **Shift-type** (`jet_kinematic_systs`, :215): `pt_scale_up` (flat 1.03, :211), `pt_res_up` (per-jet Gaussian resolution via `utils.systematics.jet_pt_resolution`, :212). Applied *inside* the variation loop by mutating the jet collection **before selection**: `jets["pt"] = jets.pt * events[syst_var]` (:234-236) — so cuts `jets.pt > 30` (:242) re-run per variation.
- **Weight-type** (`event_systs`, :216-218): `btag_var_0..3` (4 NPs) + `scale_var` (wjets only), evaluated at fill time via correctionlib: `wgt_variation = self.cset["event_systematics"].evaluate("btag_var", direction, region_jets.pt[:,i_jet])` (:327-332), filled with `weight=region_weights * wgt_variation` (:336).
- **Third tier — dataset-level 2-point systematics**: `variation = events.metadata["variation"]` (:186); e.g. `ttbar__scaledown`, `ttbar__ME_var` are *separate input datasets*; in-loop systematics run only when `variation == "nominal"` (:221-223), otherwise the whole job fills a single `variation=<dataset variation>` slice (:345-351).
- **Histograms**: every region hist carries `.StrCat([], name="variation", label="Systematic variation", growth=True)` (:136,156); variation names are strings like `btag_var_0_up` (:333), shift-types filled under their bare name with nominal weights (:346-351).
- Loop shape: single `for syst_var in syst_variations:` (:226) wrapping selection→observable→fill; weight-types redundantly re-run the selection too (they're iterations of the same loop) — the AGC paper describes exactly this split: kinematic-changing systematics "affect the selection of events" vs. others "that do not need to be evaluated at the stage of event processing" (https://arxiv.org/pdf/2401.02766).
- Boilerplate fragility acknowledged in-source: `i_jet = int(syst_var.rsplit("_",1)[-1])   # Kind of fragile` (:328).

### 5. Community friction / retrospectives

- https://github.com/CoffeaTeam/coffea/discussions/469 ("Efficient production of template histograms for statistical analysis"): raises that building nominal + weight-varied histograms in separate processors duplicates column reads and cut application; that systematic configuration is duplicated between processor code and the stat-model construction; vectorized (extra-axis) systematics measured ~2-3× faster, up to ~7-8× for many systematics. (Content read via summarizing fetch; exact attributions/quotes UNVERIFIED at word level — the URL is the evidence.)
- Coffea docs still present `Weights` (manual bookkeeping) and the jetmet shift loop as *the* supported paths; the `Systematic` mixin docs end on the unsolved-selection TODO (https://coffea-hep.readthedocs.io/en/latest/notebooks/systematics.html).
- UNVERIFIED (not found in searches): any written post-mortem explicitly declaring the nanoevents prototype abandoned; the evidence of stalling is circumstantial (git timeline, unimplemented `explodes_how`, AGC non-adoption, docs TODO).

---

## ASSESSMENT / LESSONS

1. **Coffea has three disjoint mechanisms** — `Weights` (weight-type, fill-time), jetmet factories + shift loop (shift-type, re-run everything), dataset-level variation samples — glued together by *string conventions* (`Up`/`Down` suffixes, `f"{name}_{modifier}"`, StrCategory labels). Nothing checks the three tiers agree; forgetting a variation is silent.
2. **The ratio-modifier trick is the right economics for weight systematics**: store `var/nominal` once, apply at fill; symmetric Down derived for free. Cost = one array per variation, co-computed with nominal in a single pass. This is what makes weight systematics "cheap" in coffea and what a Vary node should preserve natively.
3. **The shift pattern's cost model is brutal but honest**: whole-record shifted copies (`JES_jes.up` = every jet field re-zipped) + full re-execution of selection per shift. In dask mode the shared upstream (file read, correction eval) dedups via the graph, but the per-shift selection/observable subgraphs are structurally identical clones that nothing fuses. This is exactly the CSE/DCE opportunity graphed's interned IR gets for free — hash-consing makes N shift-variant subgraphs share every node not downstream of the varied column.
4. **Why the in-IR prototype stalled**: (a) it materialized variations eagerly as columns inside `__systematics__` (memory scales with variations × fields even if unused); (b) variation access returns a *detached copy* of the record, so downstream selection code must still be manually re-run per variation — it solved storage, not propagation; (c) the actual hard problem — which downstream computations must fork, and how variations combine (`explodes_how`) — was left as an abstract joke; (d) it fought awkward's records (rewrap/flatten gymnastics, base.py:180-219) instead of living at graph level. Lesson: **variation forking is a graph-transformation problem, not a data-layout problem**.
5. **Users' real pain** (Discussion #469 + AGC comments): duplicated computation, duplicated configuration, fragile name plumbing, and no way to declare "this systematic affects only X" and have the framework derive the minimal re-computation. The vectorized-extra-axis experiments (variations as an extra array dimension) showed big wins but were hand-rolled per analysis.
6. **The StrCategory `variation` axis is a de-facto standard** output shape (AGC, cabinetry/pyhf consumption). Whatever graphed generates should land variations as string categories on histograms to interoperate.

---

## Design implications for a graphed Vary-style node

- **One user-facing primitive, two lowering strategies**: `vary(name, {up, down, ...})` on a column/weight; the optimizer — not the user — decides weight-path (extra fill weight, single pass) vs shift-path (fork the dependent subgraph), by reachability from the varied node to reductions.
- **Make CSE do the shift-systematic work**: fork variant subgraphs in the IR and let hash-consing share every node not downstream of the varied column — this is precisely what coffea's per-shift re-run loop cannot do and the measured 2-8× vectorization wins in Discussion #469 point at.
- **Store weight variations as nominal-relative ratios** (coffea `Weights` semantics: multiplicative modifier, `shift=` additive option, auto-symmetric Down = 1/Up); co-schedule them in the nominal pass — never as separate graph executions.
- **Variation identity must be graph metadata, not string suffixes**: coffea's `Up`/`Down`/`name_modifier` conventions plus StrCategory labels are the dominant bug source (AGC's own "# Kind of fragile"). Intern (source, variation-label) pairs in the IR; render strings only at histogram output.
- **Emit the standard output shape**: a growable string "variation" category axis on histograms, `{name}_{modifier}_{up|down}` style labels, so pyhf/cabinetry workflows port directly (AGC :136, :333).
- **Support the three coffea tiers explicitly**: weight-at-fill, in-graph kinematic shift, and *dataset-level* variation (separate input sample mapped to a variation label, AGC :186) — the last is a partition-source-level tag, not a graph fork.
- **Vary must precede selection in the graph**: AGC mutates `jets.pt` *before* cuts; a Vary node's fork point is the varied column, and cutflow divergence falls out of DCE/reachability — don't reproduce the prototype's "vary a detached copy, user re-runs cuts manually" failure.
- **Do not materialize variant record copies**: coffea's `JES_jes.up` = full re-zipped jet record and the prototype's `__systematics__` columns both pay memory per variation per field; in graphed a variant is just an alternative node id — column projection already keeps only what's reached.
- **Multivariation (N nuisance parameters per source, e.g. 4 btag NPs) is a first-class arity**, not N separate calls — coffea added `add_multivariation` precisely because per-NP `add` was boilerplate.
- **Declare combination semantics up front** (one-at-a-time vs correlated groups): coffea left `explodes_how` unimplemented for 5 years; even a minimal "each Vary iterates independently, others held nominal" contract, recorded in the Plan, beats deferring it.

---

# [pythonic-analyses]

# Systematics patterns in real coffea-style analyses — prior-art report

Sources examined (shallow clones under `/private/tmp/claude-501/prior-art/`, cite as `repo:file:line` at pinned commit):

| Repo | URL | Commit examined |
|---|---|---|
| nsmith-/boostedhiggs | https://github.com/nsmith-/boostedhiggs | `a33dca8` (2022-04-19) |
| PocketCoffea/PocketCoffea | https://github.com/PocketCoffea/PocketCoffea | `b29e33b` (2026-07-27) |
| TopEFT/topeft | https://github.com/TopEFT/topeft | `bbb23ca` (2025-12-11) |
| cmstas/ewkcoffea | https://github.com/cmstas/ewkcoffea | `063e8d7` (2026-07-08) |

## Target identification: Kelci Mohrman

- `gh api users/kmohrman` resolves: login `kmohrman`, https://github.com/kmohrman (name field null on the API, so identity is inferred, **needs user confirmation**).
- `kmohrman` is the **#1 contributor to both `TopEFT/topeft` and `cmstas/ewkcoffea`** (`gh api repos/{TopEFT/topeft,cmstas/ewkcoffea}/contributors`). Her personal `kmohrman/topcoffea` is a fork (API: `"fork": true`, last push 2023).
- **Chosen repos: `TopEFT/topeft` (primary — the full Run-2 EFT analysis with the most complete systematics treatment: object-shift loop + weight loop + EFT coefficients) and `cmstas/ewkcoffea` (secondary — same author, newer, shows convention evolution).** `ewkcoffea` search hit: only `cmstas/ewkcoffea` (`gh search repos ewkcoffea`).

## VERIFIED FACTS

### 1. boostedhiggs (Nick Smith, Hbb)

**Shift systematics = outer loop of re-processing with column swapping.** `process()` builds a `shifts` list of `({"Jet": ..., "FatJet": ..., "MET": ...}, name)` pairs, using JEC-factory-produced varied collections (`jets.JES_jes.up`, `met.MET_UnclusteredEnergy.down`, …) plus a hand-built HEM18 shift via `copy.deepcopy` + pt/mass masking; then `processor.accumulate(self.process_shift(update(events, collections), name) for ...)` — **the entire analysis re-runs per shift** (`boostedhiggs/hbbprocessor.py:300-329`). Data short-circuits to nominal only (`:289-291`).

**Weight systematics = coffea `Weights(storeIndividual=True)`** (`:335`), populated via `weights.add(name, nom[, up, down])` (e.g. `:565` L1Prefiring) and helper functions `add_pdf_weight`, `add_ps_weight`, `add_pileup_weight`, … in `boostedhiggs/corrections.py:53-248`. On the nominal shift, the systematics list is `[None] + list(weights.variations)`; on a kinematic shift it is **only** `[shift_name]` — weight variations are not recomputed under shifted kinematics (`hbbprocessor.py:631-634`).

**Histogram schema: one hist, `systematic` as a growable StrCategory axis** (`hist2.axis.StrCategory([], name='systematic', growth=True)`, `:239,248,271,278`), filled by a local `fill(region, systematic, wmod=None)` closure that picks `weights.weight(modifier=systematic)` when the name is a weight variation, else nominal weight (`:636-658`). `sname='nominal'` when `None` (`:639`). LHE scale/PDF variations are injected as extra fill passes with `wmod` multipliers (`:718-722`). `sumw` and `weightStatistics` recorded only on the nominal shift (`:337-338`, `:726-727`).

### 2. PocketCoffea — config-driven weight vs shape ("shape" = calibrator) split

**Two declared kinds.** `Configurator` takes a `variations` dict with keys `"weights"` and `"shape"`; missing keys default to empty (`pocket_coffea/utils/configurator.py:266-272`). Weight-variation names must be names of declared weights; shape-variation names must be **calibrator names** (`configurator.py:541-551`), where the calibrator later *specializes* the generic name into concrete per-chunk variations.

**Applicability scoping** is uniform for weights and variations: `common.inclusive`, `common.bycategory`, and `bysample.<sample>.bycategory` (example config: `tests/test_full_configs/test_new_weights/config.py:55-98`). Config validation is eager — declaring a variation for a weight not applied to that sample/category raises at config time (`configurator.py:558-569`).

**Weights.** `WeightWrapper` ABC + registry metaclass; a weight declares `has_variations` and its variation names, which may be **multi-variation** (e.g. `sf_btag` → hf/lf/hfstats1/… per year in `pocket_coffea/parameters/variations.yaml:19-40`) and can differ per year/metadata (`lib/weights/weights.py:56-84,93-106`). `WeightsManager.compute(events, size, shape_variation="nominal")` builds a coffea-Weights per chunk **and per shape variation**; installed modifiers are named `f"{name}_{v}{Up|Down}"` for multi-variations (`lib/weights/weights_manager.py:126-175`), plain weights get `Up`/`Down` only (`:60-63`). During a shape-variation pass **only nominal weights are used** (`weights_manager.py:464` comment "Shape variation pass: only nominal weights are needed").

**Calibrators (shift systematics).** `Calibrator` ABC: `name`, `has_variations`, `calibrated_collections` ("collection.field"), `initialize(events)` once per chunk, `calibrate(events, ..., variation, already_applied_calibrators)` (`lib/calibrators/calibrator.py:36-81`). They run as an **ordered chain**; `CalibratorsManager.calibration_loop` yields `(variation, events_calibrated)` for `["nominal"] + requested`, **resetting events to the original collections after each yield** so on-the-fly calibrations stay correct (`lib/calibrators/calibrators_manager.py:147-178`). Jet calibrator variation names follow `f"{jet_type}_{variation}Up/Down"` and are parsed back by suffix-stripping (`lib/calibrators/common/common.py:172-173,316-323`).

**Re-run structure.** The base processor wraps the whole downstream chain in `for variation in self.loop_over_variations():` — object preselection, event preselection, category definition, and histogram fill all re-execute per shape variation (`pocket_coffea/workflows/base.py:892-932`). Weights/hist managers are built **once, before** the loop (`base.py:884-891`). Skim-with-variations requires an **OR of preselection masks across all variations** ("presel_any_variation" mode, `base.py:855-867` + `:726-728`).

**Histogram schema: one hist per variable with `cat` + `variation` StrCategory axes**, `growth=False`, the variation axis pre-populated deterministically (`sorted(set(...))` "to assure … the same order for all chunks") from the per-sample available weight+shape variations, filterable per-hist by `only_variations` with calibrator-name wildcards (`lib/hist_manager.py:300-337`). Data gets **no variation axis** (`:331-335`). During a shape pass, hists that don't carry that variation on their axis are skipped (`:439-446`); fill weights are cached keyed by `(category, subsample, variation)` (`:120-133`).

### 3. TopEFT/topeft (primary Mohrman-associated repo)

**Hand-rolled two-level loop, no framework.** Explicit name lists: `obj_correction_syst_lst` (JES/JER/MET, plus TES/FES for the tau analysis; `analysis/topeft_run2/analysis_processor.py:358-365`) and `wgt_correction_syst_lst` — a flat list of ~30 pre-suffixed strings, e.g. `"lepSF_muonUp"`, `f"btagSFbc_{year}Up"`, `"btagSFbc_corrUp"`, `"FSRUp"`, `"renormDown"` (`:367-375`), plus `data_syst_lst` for fake-factor variations on data (`:377`).

- **Outer loop over kinematic shifts** (`["nominal"] + obj_correction_syst_lst`): the *rest of the processor lives inside it* (banner comment `:418`, loop `:427`). Each iteration does `weights_obj_base_for_kinematic_syst = copy.deepcopy(weights_obj_base)` "so that each time through the loop we do not double count systs" (`:428-430`). Shifts applied by **column swapping** helpers: `ApplyJetSystematics(year, cleanedJets, syst_var)` returns `cleanedJets.JES_jes.up` etc. for the matching name, pass-through otherwise (`topeft/modules/corrections.py:1465-1480`); same pattern for TES/FES (`analysis_processor.py:454-455`).
- **Inner loop over weight flucts** at fill time: `wgt_var_lst = ["nominal"] + wgt_correction_syst_lst + data_syst_lst` **only when the outer shift is nominal**, else `[syst_var]` alone (`:1024-1037`) — same exclusion rule as boostedhiggs. Weight lookup: `weights_object.weight(wgt_fluct)` if `wgt_fluct in weights_object.variations` else `continue` (silently skip categories lacking that variation, `:1047-1056`). A runtime guard raises if data carries unexpected variations (`:1058-1065`).
- **Weights per lepton-category**: `weights_dict[ch_name] = copy.deepcopy(weights_obj_base_for_kinematic_syst)` because some SFs depend on the lepton channel (`:633`).

**Correlated vs uncorrelated split is done by naming convention**: btag has both `f"btagSFbc_{year}"` (uncorrelated across years, name carries the year) and `"btagSFbc_corr"` (correlated across years) registered as separate up/down pairs from decomposed correlated/uncorrelated error components (`:541-583`). **Theory systs need external sum-of-weights bookkeeping**: per-sample `nSumOfWeights_renormUp/Down`, `factUp/Down`, … pulled from sample metadata; LO samples deliberately use nominal SOW so the variation also covers xsec/acceptance, NLO samples use varied SOW (comments `:165-193`, `:394`).

**Histogram schema: single hist per dense axis with `systematic` StrCategory (`growth=True`) axis** (`:72`), filled with `"systematic": wgt_fluct` alongside `channel`/`appl`/`process` and optional EFT coefficient arrays (`:1113-1122`). Sample applicability is implicit: variations simply absent from a sample's `weights_object.variations` are skipped at fill.

### 4. cmstas/ewkcoffea (WWZ, same author — convention evolution)

Same two-level architecture as topeft: outer `obj_corr_syst_var_list` loop containing the rest of the processor, `copy.deepcopy(weights_obj_base)` per shift (`analysis/wwz/wwz4l.py:452-470`), `systematic` StrCategory growth axis (`:161`), `skip_obj_systematics` escape hatch (`:210`). Two notable changes: a helper `append_up_down_to_sys_base` generates Up/Down names instead of hand-writing them (`:29-30,449`), and systematic names are now **combine-datacard-style**, encoding correlation scope directly, e.g. `"CMS_l1_ecal_prefiring"`, `f"CMS_btag_fixedWP_incl_light_uncorrelated_{year}"` (`:447`).

## Cross-cutting VERIFIED conventions

- **`Up`/`Down` suffix on a base name is universal** (coffea `Weights.add(name, nom, up, down)` registers `nameUp`/`nameDown`; PocketCoffea multi-variations use `name_componentUp/Down`; PocketCoffea jet calibrator parses variation kind by stripping the suffix, `common.py:316-323`).
- **`"nominal"` is the reserved central-value name in the variation axis in all four repos** (boostedhiggs `:639`; PocketCoffea `calibrators_manager.py:163`; topeft `:421`; ewkcoffea `:462`).
- **Weight and shift variations are mutually exclusive by construction**: under a kinematic shift, only nominal weights fill (all four repos). The cross product (JES-up × pileup-up) is never produced.
- **Year-correlation is encoded in the variation name** (year-suffixed = uncorrelated, `_corr`/no-suffix = correlated): topeft `:368`, ewkcoffea `:447`, PocketCoffea per-year variation lists in `variations.yaml`.
- **Data is special-cased everywhere**: no shifts (boostedhiggs `:289`), no variation axis (PocketCoffea `hist_manager.py:331-335`), guard exceptions (topeft `:1058-1065`).

## Failure modes / boilerplate users visibly fight (all evidenced above)

1. **Whole-chain re-execution per shift** with nothing shared downstream of the swap — boostedhiggs re-runs `process_shift` ~8×, topeft/ewkcoffea nest 1000+ lines inside the shift loop. No system reuses shift-invariant sub-results (e.g. lepton-only selections under JES).
2. **Defensive `copy.deepcopy` of Weights objects** per shift *and* per channel to avoid double-registration (topeft `:428-430,633`, ewkcoffea `:468-470`, boostedhiggs `:320`) — accumulation-by-mutation forces copies.
3. **Name-list drift**: topeft's flat pre-suffixed string lists must be kept consistent by hand across registration, fill loop, and downstream datacard code; the `continue`-on-missing at `:1056` means a typo silently drops a systematic (compensated by explicit runtime guard exceptions `:1059-1065`).
4. **Nominal-only bookkeeping needs guards**: `sumw`/weightStatistics only on nominal (boostedhiggs `:337,726`); PocketCoffea had to add an explicit fix so per-variation preselection counts don't clobber the nominal cutflow entry (`base.py:912-921` comment) — cutflow-per-variation is a real bug source.
5. **Skimming vs shifts interacts badly**: a skim must keep the OR of all variations' preselections (PocketCoffea "presel_any_variation" machinery, `base.py:726-728,855-867`) — evidence that selection masks are variation-dependent state.
6. **Theory systematics need out-of-band per-sample normalization** (sum-of-weights per variation from preprocessing metadata, topeft `:174-204`) — the graph alone doesn't see it.
7. Commented-out variation filters left in fill code (boostedhiggs `:659`) — manual pruning of which (region × systematic) combos to fill.

## ASSESSMENT / LESSONS

- The field converged, independently, on exactly the two-kind model in the mission brief: **weight variations = extra fill weights at the sink (cheap, co-computed)**; **shift variations = swap input columns and re-run the dependent chain (expensive, outer loop)**. PocketCoffea is the only one that made this a declarative config split (`variations: {weights: ..., shape: ...}`); the others hand-roll it.
- The natural user mental model for a shift is **"replace collection X's fields, keep everything else"** — boostedhiggs' `{"Jet": jets.JES_jes.up, ...}` dict and PocketCoffea's `calibrated_collections` both express shifts as *column substitutions*, which maps directly onto graph-node substitution.
- PocketCoffea's calibrator chain shows shifts must compose **in order** (JEC then MET propagation) and that a variation's concrete name set can be **data-dependent** (per-year/per-chunk specialization of a generic "jets" variation).
- Everything downstream of the swap point that is *not* reachable from the swapped columns is recomputed wastefully today — CSE/DCE over a variation-expanded graph is precisely the missing optimization.
- Histogram convention to match: **one histogram, `variation`/`systematic` StrCategory axis, `"nominal"` entry, `Up`/`Down` suffixed names**; PocketCoffea's fixed, sorted, pre-declared axis (vs growth=True) exists for **cross-chunk determinism/mergeability** — directly relevant to graphed's determinism gate.

## Design implications for a graphed Vary-style node

- Model two primitives, not one: `vary_weight(name, up, down)` attaches extra scalar-per-event columns consumed only at fill (fan-out at the histogram sink), while `vary_columns(name, {collection.field: replacement})` substitutes source columns — the IR then derives the re-run cone as *reachability from the substituted nodes* (DCE dual), sharing all shift-invariant subgraphs automatically (fixes failure mode 1).
- Because graphed IR is immutable/hash-consed, variation expansion is copy-free node substitution — the `deepcopy`-of-Weights pathology (failure mode 2) cannot arise; CSE dedups identical sub-chains across variations for free.
- Enforce the observed exclusion rule as a default: under a column-shift variation, weight variations collapse to nominal (no cross product), with an explicit opt-in if a user ever wants the product.
- Reserve `"nominal"` and generate `Up`/`Down` suffixes from a base name in the IR itself (like ewkcoffea's `append_up_down_to_sys_base`), so name-list drift/typos (failure mode 3) become graph-validation errors, not silent drops.
- Variation names must be first-class strings the user controls (combine-style names encode correlation scope, e.g. `..._uncorrelated_{year}`); graphed should carry an optional correlation tag but never invent naming.
- The histogram node should take variation as a pre-declared, sorted StrCategory axis (PocketCoffea style, growth=False) — required anyway for graphed's byte-identical determinism gate and safe partition merging.
- Cutflow/`sumw`/weight-statistics nodes need an explicit variation scope attribute (nominal-only by default) — per-variation cutflow clobbering (failure mode 4) was a real PocketCoffea bug.
- Applicability (per-sample, per-era, per-category) is metadata-driven and known before graph build (PocketCoffea validates eagerly at config time) — graphed should validate variation↔sample applicability at graph construction, and let the concrete variation list of a generic knob (e.g. "jets") be resolved per-dataset like PocketCoffea calibrators do.
- Shift variations change selection masks, so any materialize/skim boundary must retain the OR of all live variations' selections — this must be a graph-level transform, not user code (PocketCoffea's hand-built "presel_any_variation" mode is the cautionary tale).
- Theory-style variations need out-of-band per-sample normalization inputs (sum-of-weights per variation); model these as ordinary graph inputs (per-partition metadata reductions) so the Plan stays self-contained instead of relying on side-channel sample dicts.