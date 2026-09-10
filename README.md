# aifactory-twin

**A SimReady OpenUSD asset pipeline and validation harness for AI factory digital twins.**

Raw vendor assets in. A validated, layered, instanced, multi-consumer OpenUSD scene out —
plus a CI gate that fails the build when the scene is not simulation-ready.

> **Status: the rack component, CPU-side validation, and both GPU consumers (OVRTX render,
> OVPhysX physics) all run end-to-end.** A standalone asset evaluator (`evaluation.py`) and a
> five-fixture regression suite (`run_fixtures.py`) prove the validation contract correctly
> classifies each class of defect. `datahall.usda` scales to N scenegraph-instanced racks; a
> registered `UsdValidation` gate and floor-tile point instancing are not built yet.
> Every milestone below is marked honestly. Nothing is claimed until it runs.
> See [Status](#status) and [POC_SCOPE.MD](POC_SCOPE.MD).

---

## What this is

A miniature, architecturally honest AI-factory digital twin: one data hall of `N` compute
racks in rows, a liquid cooling loop, power distribution units, a floor shell, and one mobile
robot imported from URDF.

The interesting claim is not that it renders. It is that:

1. **Four owners edit one scene without merge conflicts**, because ownership is encoded in the
   layer stack instead of in a process document nobody reads.
2. **The scene's declared engineering data is readable without loading geometry.** Every rack's
   declared power draw can be read with all 4M triangles still on disk, because domain metadata
   lives above the payload arc rather than inside it.
3. **CI gates on consumer fitness, not just file validity.** A rigid body with no mass, a
   material binding that resolves to nothing, a collision mesh left at full resolution —
   `usdchecker` passes all three and `ovphysx` and `ovrtx` do not. `ci/validate.sh` exits
   non-zero and names the prim.

Point 3 is the thesis. **Valid USD and usable-by-`ovphysx` are different claims. `usdchecker`
makes the first. This harness makes the second.**

## What this is not

A digital-twin product, an engineering analysis tool, or a decision system for whether a
facility should be built. **It is a SimReady asset pipeline with a validation gate.**

`SCOPE.md` is the contract. Everything below is out of scope, stated up front rather than
discovered later:

- **Cross-component engineering consistency.** `power_budget_consistent` — summing rack draw
  against declared distribution capacity — is specified in `SIMREADY_SPEC.md` and **not
  implemented**. It needs a topology model of which racks feed from which unit. Designed, not
  built.
- **CFD, thermal solving, electrical solving.** Never intended. Thermal and electrical values
  are declared attributes, not solved fields.
- **Real geometry.** Components use dimensionally-plausible proxy boxes. The pipeline is the
  artifact; the geometry is a placeholder.
- **LOD variant sets.** Designed, not built.
- **`ovstorage`, `ovstream`, MCP/agent query tooling.** Out of scope entirely.
- **URDF import.** Not covered by this repo.
- **Production scale.** Demonstrated to N = 4096 on one machine. The architecture is the claim;
  the scale is an illustration.

---

## The layer architecture

This is the part worth reading. The current, as-built V1 story is in
[ARCHITECTURE.md](ARCHITECTURE.md). The full rationale, a glossary of the terms used precisely
below (*component*, *interface layer*, *stage consumer*), and the decision log live in
[DESIGN_NOTES.md](DESIGN_NOTES.md).

### Per component

```
rack_gb300.usda                      ← INTERFACE LAYER — the only file the scene references
│
│  subLayers, listed strongest first:
├── domain_electrical.usda           ← site/electrical engineer owns   (strongest)
├── physics.usda                     ← simulation engineer owns
├── mtl.usda                         ← look-dev owns
│
└── payload → geo.usdc               ← vendor owns                     (weakest, lazily loaded)
```

Two decisions are doing all the work here.

**Geometry is a payload, not a sublayer.** It is the heaviest data and the thing you least
often need. A validation run that only checks electrical metadata should never pay to load
4M triangles, and a power-topology view should be able to unload geometry entirely. Sublayers
are always composed; payloads can be loaded and unloaded at runtime. That single distinction
is why the scene scales *and* why the metadata stays queryable when it doesn't.

**Geometry is the weakest opinion.** By USD's LIVRPS strength ordering, everything in the
interface layer's local layer stack (the sublayers) outranks anything arriving through a
payload arc. So when the vendor ships `rack_gb300_v2`, you swap one payload target and every
collider, mass value, material binding, power rating and semantic label authored above it
survives untouched.

> **The ordering is a governance decision disguised as a technical one.** The question asked
> first was *"who is allowed to override whom"*, not *"what composes fastest."* The vendor owns
> geometry, so geometry has to be the weakest opinion in the stack — otherwise a routine asset
> update destroys the site engineer's work and the pipeline is worth nothing.

### Per scene

```
datahall.usda
│
├── sublayer: session.usda           ← runtime / live telemetry   (strongest, ephemeral, gitignored)
├── sublayer: site_overrides.usda    ← this deployment's deviations
├── sublayer: layout.usda            ← placement, rows, instancing
└── sublayer: catalog.usda           ← references published components (weakest)
```

Four owners, four layers, no merge conflicts. That is the entire pitch for OpenUSD as a shared
source of truth across disciplines, demonstrated rather than asserted.

---

## Repository layout

```
aifactory-twin/
├── SCOPE.md                     # THE CONTRACT — what this repo does and does not claim
├── POC_SCOPE.MD                 # the POC's customer story, hypothesis, success/kill criteria
├── README.md                    # this file — the reference architecture
├── ARCHITECTURE.md              # current, as-built V1 architecture story
├── DESIGN_NOTES.md              # layer strategy, composition decisions, decision log
├── SIMREADY_SPEC.md             # the three validation tiers and the six custom rules
├── BENCHMARKS.md                # CPU-only method stated; numbers unpopulated
├── docs/GETTING_STARTED.md      # step-by-step build order
│
├── demo.py                      # runs validation → OVRTX render → OVPhysX physics, end to end
├── evaluation.py                # evaluate any USD scene's sim-readiness — see below
├── run_fixtures.py              # regression suite: each fixture must fail for its own reason
│
├── assets/
│   ├── source/                  # raw inputs — NEVER edited in place
│   └── published/               # pipeline OUTPUT — NEVER hand-edited
│       ├── components/          # per-component SimReady assets
│       └── scenes/              # assembled scenes
│
├── examples/fixtures/           # one deliberate defect per fixture, used by run_fixtures.py
│   ├── valid/                   #   every check passes
│   ├── missing_mass/            #   fails rigidbody_has_mass only
│   ├── missing_collider/        #   fails rigidbody_has_collider only
│   ├── broken_material/         #   fails material_bindings_resolve only
│   └── invalid_domain/          #   fails nominal_power_present only
│
├── output/                      # evaluator/demo output — render.png, evaluation.json/md, etc.
│
├── src/aifactory_twin/
│   ├── ingest/                  # source → normalized USD (units, naming, xforms, manifest)
│   ├── author/                  # layer authoring (simready, domain, assemble)
│   ├── optimize/                # instancing strategies
│   ├── validate/                # component-level custom rules + unloaded-stage query
│   └── consume/                 # ovrtx render, ovphysx physics
│
├── tests/broken/                # deliberately broken fixtures the gate must reject
└── ci/                          # not built yet — see Status
```

**The discipline is the point.** `assets/source/` is never modified. `assets/published/` is
never hand-edited. Everything in between is code. When someone asks *"how do you handle a
vendor shipping updated geometry?"*, the answer is **"I re-run the pipeline"** — and that
answer is only credible if the repo is actually structured this way.

---

## Conventions

Stated once, enforced by validator, never negotiated afterwards.

| Convention | Value | Why |
|---|---|---|
| Up axis | **Z-up** | Omniverse, Isaac Sim and URDF are all Z-up. USD's default is Y-up; following it here would mean a rotation fixup on every robot import. |
| Linear units | **meters** (`metersPerUnit = 1.0`) | Physics and electrical data are SI. Mixed units are the single most common source of real-world twin bugs. |
| Component origin | floor-centred, +Y forward | Placement math in `layout.usda` stays trivial and readable. |
| Prim naming | `snake_case`, valid USD identifiers, deterministic from source | Diffable output; re-running the pipeline produces byte-identical results. |
| Published format | `.usda` for anything a human reviews, `.usdc` for geometry | Layer files stay reviewable in a PR; heavy meshes stay compact. |

Disagreement about up-axis and units is the number one source of real-world twin bugs. Pick
one, state it, enforce it in CI.

---

## Quickstart

```bash
uv sync            # CPU side only: usd-core + pytest. Never pulls anything GPU-related.

# normalize the vendor drop into a proxy-box geometry layer
python src/aifactory_twin/ingest/normalize_rack.py

# author the physics / material / domain sublayers, then the interface layer
python src/aifactory_twin/author/create_physics_layer.py
python src/aifactory_twin/author/create_material_layer.py
python src/aifactory_twin/author/create_domain_layer.py
python src/aifactory_twin/author/create_rack_component.py

# component-level validation — the six consumer-fitness rules
python src/aifactory_twin/validate/run.py

# read declared power draw with geometry unloaded (Usd.Stage.LoadNone)
python src/aifactory_twin/validate/query_rack.py

# assemble a data hall of N scenegraph-instanced racks
python src/aifactory_twin/author/assemble.py --racks 512

# evaluate any scene's sim-readiness — see "Testing your own asset" below
python evaluation.py assets/published/scenes/rack_render.usda

# regression suite: every fixture must fail for its own declared reason
python run_fixtures.py

# full runtime POC — validation, then OVRTX render, then OVPhysX physics
# (Linux + NVIDIA GPU only; requires the opt-in under "Platform split" first)
python demo.py
```

---

## Platform split

The pipeline is deliberately split so that most of it needs no GPU:

| Work | Runs on | Needs |
|---|---|---|
| Ingest, layer authoring, instancing, validation, stage-side benchmarks (M1–M5, M7a) | macOS or x86_64 Linux laptop, no GPU | `usd-core` only (default `uv sync`) |
| ovrtx render, ovphysx physics, ovstage multi-rate consumers, GPU benchmarks (M6, M7b) | Linux + NVIDIA RTX GPU + driver | `gpu` dependency group and the `third_party/ovrtx` and `third_party/physx` submodules, see below |

**`usd-core`** is Pixar's OpenUSD library packaged for Python and published on PyPI. It provides
the `pxr` module — `Usd`, `Sdf`, `UsdGeom`, `UsdPhysics`, `UsdShade`, `Gf` — that every script
under `src/aifactory_twin/` imports. The "core" build ships the composition engine and schemas
without the imaging stack, `usdview` or any Hydra render delegate, which is exactly enough to
author and validate a stage on a CPU. It is pinned to 26.8 so the numbers in `BENCHMARKS.md`
stay reproducible.

Two platform caveats:

- **`usd-core` has no aarch64 Linux wheel** in any released version, so `pyproject.toml`
  declares it with `platform_machine != 'aarch64'`. On an arm64 box such as a DGX Spark / GB10
  the CPU side (ingest, author, validate) is therefore not installable and `pxr` will not
  import; that machine is a **consume-only host** and runs the GPU side only. To author on
  arm64 you would need an OpenUSD built from source or the one bundled with Isaac Sim /
  Omniverse Kit.
- **`ovrtx`, `ovphysx`, `ovstage` and `ovstorage` publish Linux x86_64/aarch64 and Windows
  builds only — there is no macOS build of any of them.** All four install from PyPI. The
  `ovrtx` entry on PyPI is a small stub that fetches the ~1.7 GB renderer from
  `pypi.nvidia.com` at install time; the same bundle is also on the ovrtx GitHub Releases page.

Not paying for GPU time to check whether a rack declares its electrical phase is also a
cost-awareness argument, and it is the honest reason for the split.

### Opting in to the GPU side

Two NVIDIA SDKs are vendored as git submodules, each pinned to the release tag that matches
the wheel:

| Submodule | Upstream | Pinned at | Covers |
|---|---|---|---|
| `third_party/ovrtx` | [NVIDIA-Omniverse/ovrtx](https://github.com/NVIDIA-Omniverse/ovrtx) | `v0.4.1` | the RTX render consumer |
| `third_party/physx` | [NVIDIA-Omniverse/PhysX](https://github.com/NVIDIA-Omniverse/PhysX.git) | `ovphysx-0.5.11` | the PhysX SDK and the `ovphysx` physics consumer built from it |

Both are marked `update = none` in `.gitmodules`, so a plain `git clone`, `git clone
--recurse-submodules` or `git submodule update --init` all leave the directories empty. The
`gpu` dependency group is likewise skipped by a plain `uv sync`, and its entries carry a
`sys_platform == 'linux'` marker.

On a Linux machine with an RTX-capable GPU and a supported NVIDIA driver, and **only there**:

```bash
git submodule update --init --checkout third_party/ovrtx third_party/physx
uv sync --group gpu
uv run python -m aifactory_twin.consume.render_ovrtx --png   # writes _output/render.png
```

Run consumers as modules from the repo root, as above, so the package guard executes. If the
machine also carries a hand-built venv (JupyterLab, torch), point uv at its own directory first
with `export UV_PROJECT_ENVIRONMENT=.venv-twin`; a bare `uv sync` otherwise reconciles `.venv`
to the lockfile and removes everything it does not know about.

The second command is deliberately not part of the default setup because of the ~1.7 GB
download described above. As a last line of defence, `aifactory_twin.consume` exits with a
clear message on import when `nvidia-smi` is not on `PATH`.

To move to a newer release, check out the new tag inside the submodule, commit the moved
pointer, and bump the matching version in the `gpu` group of `pyproject.toml`:

```bash
git -C third_party/ovrtx fetch --tags && git -C third_party/ovrtx checkout v0.5.0
git -C third_party/physx fetch --tags && git -C third_party/physx checkout ovphysx-0.5.11
git add third_party/ovrtx third_party/physx pyproject.toml && uv lock
```

`third_party/physx` is shallow-cloned, so `fetch --tags` is required before any tag other than
the pinned one resolves.

---

## Status

One row per `SCOPE.md` deliverable. **A row reads `built` only when its done-condition in
`SCOPE.md` is demonstrably met.** `designed, not built` is a deliberate exclusion, not pending
work. `partial` means real, running code that does not yet meet the full stated condition —
named honestly rather than rounded up.

| # | Deliverable | Done when | Status |
|---|---|---|---|
| 1 | One layered component (`rack_gb300`) — interface layer, geometry payload, physics / material / domain sublayers | Each sublayer contains only its own opinions when opened in a text editor | ✅ built |
| 2 | Unloaded-stage domain query | A script opens with `Usd.Stage.LoadNone` and prints power draw plus a composed prim count, no geometry loaded | ✅ built — `validate/query_rack.py`; prints a prim count, not yet a composed *count across N racks* |
| 3 | Six custom validators in `UsdValidation.ValidationRegistry` | They run alongside the 28 built-ins and report through the same `ValidationError` type | 🟡 partial — the six rules exist in `validate/rules.py`, run via `validate/run.py`, and all pass; not yet registered into `UsdValidation.ValidationRegistry` alongside the built-ins |
| 4 | `datahall.usda` — N racks scenegraph-instanced, floor tiles via `UsdGeomPointInstancer` | N is a CLI parameter; the gate passes at N = 64, 512, 4096 | 🟡 partial — `author/assemble.py --racks N` builds N scenegraph-instanced racks (demonstrated at N=4, committed); no floor tiles / `PointInstancer` yet, not demonstrated at N=512/4096 |
| 5 | `ci/validate.sh` and a deliberately broken fixture | Running the gate against `tests/broken/` exits nonzero and names the offending prim | ⬜ not started |
| — | Tier 3 engineering consistency — cross-prim comparison, aggregation | — | 📐 designed, not built |
| — | LOD variant sets | — | 📐 designed, not built |

Supporting docs, which exist but are not deliverables: `ARCHITECTURE.md`, `DESIGN_NOTES.md`,
`SIMREADY_SPEC.md`, `SCOPE.md`, `BENCHMARKS.md` (method stated, numbers unpopulated).

### POC evaluator and regression suite

A second, separate initiative — not a `SCOPE.md` deliverable, scoped instead by
[`POC_SCOPE.MD`](POC_SCOPE.MD) — proves the validation *contract* itself, and that the two GPU
consumers actually execute:

| Deliverable | Status |
|---|---|
| `demo.py` — validation → OVRTX render → OVPhysX physics, one command | ✅ built and run on GPU hardware — `output/demo/{render.png, physics_results.json, summary.json}` are the committed evidence |
| `evaluation.py` — 4-category sim-readiness evaluator for any scene | ✅ built — see [Testing your own asset's sim-readiness](#testing-your-own-assets-sim-readiness) below |
| `run_fixtures.py` + `examples/fixtures/` — 5-fixture regression suite | ✅ built — each fixture fails for exactly one declared reason; `Fixture suite: PASS` |

---

## Simulated vs. approximated

Stated up front rather than buried, because every one of these is somewhere a reader could
otherwise catch the project overclaiming.

| Claim | Reality |
|---|---|
| Rack / CDU / PDU geometry | **Procedurally generated** to representative dimensions and mass. Not vendor CAD. Every dimension and power figure is chosen as representative, not sourced from a vendor spec sheet — see `SIMREADY_SPEC.md` §7. |
| Thermal data | **Declared, not solved.** No CFD anywhere in this repo. Validators check the data was **authored**, not that it is correct. |
| Electrical data | **Declared, not solved.** Presence and token validity only. **No rule compares declared values across prims or aggregates them.** |
| Power / heat figures | Order-of-magnitude representative of a liquid-cooled AI rack. Not measured. |
| Robot | Real URDF (NVIDIA Carter), really imported, with post-import authoring done by this pipeline. |
| Benchmarks | Real measurements on stated hardware, or absent. Never estimated. |
| Partner validation | **None.** No partner or customer has reviewed this. |

---

## Testing your own asset's sim-readiness

`evaluation.py` takes any composed USD scene and reports whether it is usable by its intended
consumers — not just whether it is valid USD (ADR-11 in `DESIGN_NOTES.md`: it does not assume
this repo produced the asset):

```bash
python evaluation.py /path/to/your/scene.usda
```

This writes `output/demo/evaluation.json` and `output/demo/evaluation.md`, and checks four
independent categories:

| Category | Checks | Static or runtime |
|---|---|---|
| **structural** | stage opens, `defaultPrim` is valid, no composition errors | static — reads only the asset |
| **render** | material bindings resolve on every `Gprim`; plus, when evaluating a real `demo.py` run, that OVRTX actually executed and produced an image | static + runtime |
| **physics** | every `RigidBodyAPI` prim has mass and a collider; plus, when evaluating a real `demo.py` run, that OVPhysX actually executed and the pose changed | static + runtime |
| **domain** | engineering metadata (`aifactory:electrical:...`, `aifactory:thermal:...`) is present and non-zero on the rack prim | static — reads only the asset |

The static checks run on the asset alone and need no GPU. The runtime checks
(`ovrtx_execution`, `render_output_exists`, `ovphysx_execution`, `physics_output_exists`,
`pose_changed`) read `output_dir/summary.json`, `render.png`, and `physics_results.json` — the
artifacts a real `demo.py` run produces — and only make sense there
(`build_evaluation(asset_path, output_dir, require_runtime=...)`). `run_fixtures.py` sets
`require_runtime=False` so a fixture with no `demo.py` run behind it is judged purely on its
own USD content.

A `FAIL` in any single check fails its whole category; any category `FAIL` fails
`overall_status`. The output names the exact check and prim:

```json
{
  "name": "nominal_power_present",
  "status": "FAIL",
  "message": "Nominal power draw is invalid: 0.0",
  "prim_path": "/World/Rack"
}
```

**Prove the evaluator itself is trustworthy before trusting its verdict on your asset** — run
the regression suite:

```bash
python run_fixtures.py
```

This runs the static checks (no GPU, no `demo.py` run needed) against five fixtures under
`examples/fixtures/`, each with exactly one deliberate defect, and asserts each one fails in
the expected category and nowhere else:

```
valid              PASS   — every static check passes
missing_mass       FAIL   — physics.rigidbody_has_mass only
missing_collider   FAIL   — physics.rigidbody_has_collider only
broken_material    FAIL   — render.material_bindings_resolve only
invalid_domain     FAIL   — domain.nominal_power_present only

Fixture suite: PASS
```

If you are adding your own domain rule, the fixture pattern is the fastest way to prove it
fires — and only on the case it is meant to catch: clone `examples/fixtures/valid/`, break
exactly one value, register the fixture and its expected failing category in
`run_fixtures.py`'s `FIXTURES` dict.

## How to adapt this to your assets

1. Drop your source geometry in `assets/source/` and leave it alone forever.
2. Edit the conventions table above if your site disagrees — then change the `valid_units`
   validator to match, so the convention and its enforcement never drift apart.
3. Rewrite `SIMREADY_SPEC.md` for your domain. The electrical and thermal rules here are one
   worked example of a domain spec; yours will differ in content and not in shape.
4. Add domain rules to `validate/rules.py`, and a matching static check to `evaluation.py`. The
   interface a rule implements is deliberately small so that a domain expert who is not a USD
   expert can contribute one.
5. Add a fixture for the new rule under `examples/fixtures/` and register it in
   `run_fixtures.py`, per the section above.
6. Everything else — layering, instancing policy — should carry over unchanged.

---

## Further reading

- [SCOPE.md](SCOPE.md) — **the contract.** What this repo claims, and what it does not
- [POC_SCOPE.MD](POC_SCOPE.MD) — the POC's customer story, hypothesis, and success/kill criteria
- [ARCHITECTURE.md](ARCHITECTURE.md) — the current, as-built V1 architecture story
- [DESIGN_NOTES.md](DESIGN_NOTES.md) — layer strategy, LIVRPS reasoning, validation tiers, decision log
- [SIMREADY_SPEC.md](SIMREADY_SPEC.md) — the three tiers and the six custom validators
- [BENCHMARKS.md](BENCHMARKS.md) — CPU-only benchmark method
- [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) — build it yourself: commands, signatures and a verification per step
