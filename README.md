# aifactory-twin

**A SimReady OpenUSD asset pipeline and validation harness for AI factory digital twins.**

Raw vendor assets in. A validated, layered, instanced, multi-consumer OpenUSD scene out —
plus a CI gate that fails the build when the scene is not simulation-ready.

> **Status: M0 (architecture) complete. No pipeline code yet.**
> Every milestone below is marked honestly. Nothing is claimed until it runs.
> See [Status](#status).

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

This is the part worth reading. Full rationale, a glossary of the terms used precisely
below (*component*, *interface layer*, *stage consumer*), and the decision log live in
[ARCHITECTURE.md](ARCHITECTURE.md).

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
├── README.md                    # this file — the reference architecture
├── ARCHITECTURE.md              # layer strategy, composition decisions, decision log
├── SIMREADY_SPEC.md             # the three validation tiers and the five custom rules
├── BENCHMARKS.md                # CPU-only method stated; numbers unpopulated
├── docs/GETTING_STARTED.md      # step-by-step build order
│
├── assets/
│   ├── source/                  # raw inputs — NEVER edited in place
│   └── published/               # pipeline OUTPUT — NEVER hand-edited
│       ├── components/          # per-component SimReady assets
│       └── scenes/              # assembled scenes
│
├── src/aifactory_twin/
│   ├── ingest/                  # source → normalized USD (units, naming, xforms, manifest)
│   ├── author/                  # layer authoring (simready, domain, assemble)
│   ├── optimize/                # instancing strategies
│   ├── validate/                # built-in UsdValidation suite + 5 custom rules → report
│   └── consume/                 # ovrtx render, ovphysx physics
│
├── tests/broken/                # deliberately broken fixtures the gate must reject
└── ci/validate.sh               # the gate
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

> Nothing below runs yet — this is the shape the pipeline will take. Working commands land as
> milestones complete.

```bash
uv sync

# M1 — ingest a source asset into a normalized, layered component
python -m aifactory_twin.ingest assets/source/rack_gb300.usda

# M4 — assemble a data hall with N racks
python -m aifactory_twin.author.assemble --racks 512 --instancing scenegraph

# M5 — validate; this is the gate
./ci/validate.sh assets/published/scenes/datahall.usda

# M6 — two independent consumers over one stage (Linux + NVIDIA GPU only)
python -m aifactory_twin.consume.render_ovrtx   assets/published/scenes/datahall.usda
python -m aifactory_twin.consume.physics_ovphysx assets/published/scenes/datahall.usda
```

---

## Platform split

The pipeline is deliberately split so that most of it needs no GPU:

| Work | Runs on | Needs |
|---|---|---|
| Ingest, layer authoring, instancing, validation, stage-side benchmarks (M1–M5, M7a) | macOS laptop | `usd-core` only |
| ovrtx render, ovphysx physics, ovstage multi-rate consumers, GPU benchmarks (M6, M7b) | Linux + NVIDIA GPU | EA wheels, see below |

`ovrtx`, `ovphysx`, `ovstage` and `ovstorage` publish **Linux x86_64/aarch64 and Windows
builds only — there is no macOS build of any of them.** `ovphysx`, `ovstage` and `ovstorage`
install from PyPI; `ovrtx` ships as a ~1.8 GB bundle on its GitHub Releases page.

Not paying for GPU time to check whether a rack declares its electrical phase is also a
cost-awareness argument, and it is the honest reason for the split.

---

## Status

One row per `SCOPE.md` deliverable. **A row reads `built` only when its done-condition in
`SCOPE.md` is demonstrably met.** `designed, not built` is a deliberate exclusion, not pending
work.

| # | Deliverable | Done when | Status |
|---|---|---|---|
| 1 | One layered component (`rack_gb300`) — interface layer, geometry payload, physics / material / domain sublayers | Each sublayer contains only its own opinions when opened in a text editor | ⬜ not started |
| 2 | Unloaded-stage domain query | A script opens with `Usd.Stage.LoadNone` and prints power draw plus a composed prim count, no geometry loaded | ⬜ not started |
| 3 | Five custom validators in `UsdValidation.ValidationRegistry` | They run alongside the 28 built-ins and report through the same `ValidationError` type | ⬜ not started |
| 4 | `datahall.usda` — N racks scenegraph-instanced, floor tiles via `UsdGeomPointInstancer` | N is a CLI parameter; the gate passes at N = 64, 512, 4096 | ⬜ not started |
| 5 | `ci/validate.sh` and a deliberately broken fixture | Running the gate against `tests/broken/` exits nonzero and names the offending prim | ⬜ not started |
| — | Tier 3 engineering consistency — cross-prim comparison, aggregation | — | 📐 designed, not built |
| — | LOD variant sets | — | 📐 designed, not built |

Supporting docs, which exist but are not deliverables: `ARCHITECTURE.md`, `SIMREADY_SPEC.md`,
`SCOPE.md`, `BENCHMARKS.md` (method stated, numbers unpopulated).

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

## How to adapt this to your assets

There are two ways in, and the second is probably the one you want.

**Just validate a twin you already have** — the validator takes any USD stage and does not
assume this repo produced it (ADR-11):

```bash
./ci/validate.sh /path/to/your/scene.usda
```

**Run your assets through the whole pipeline:**

1. Drop your source geometry in `assets/source/` and leave it alone forever.
2. Edit the conventions table above if your site disagrees — then change the `valid_units`
   validator to match, so the convention and its enforcement never drift apart.
3. Rewrite `SIMREADY_SPEC.md` for your domain. The electrical and thermal rules here are one
   worked example of a domain spec; yours will differ in content and not in shape.
4. Add domain rules to `validate/rules.py`. The interface a rule implements is deliberately
   small so that a domain expert who is not a USD expert can contribute one.
5. Everything else — layering, instancing policy, the gate — should carry over unchanged.

---

## Further reading

- [SCOPE.md](SCOPE.md) — **the contract.** What this repo claims, and what it does not
- [ARCHITECTURE.md](ARCHITECTURE.md) — layer strategy, LIVRPS reasoning, validation tiers, decision log
- [SIMREADY_SPEC.md](SIMREADY_SPEC.md) — the three tiers and the five custom validators
- [BENCHMARKS.md](BENCHMARKS.md) — CPU-only benchmark method
- [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) — build it yourself: commands, signatures and a verification per step
