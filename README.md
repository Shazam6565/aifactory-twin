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
2. **The scene answers engineering questions without loading geometry.** Total power draw of
   row B is computable with all 4M triangles still on disk, because domain metadata lives above
   the payload arc rather than inside it.
3. **CI catches design errors, not just malformed files.** If the racks in a row draw more
   power than their PDU can supply, `ci/validate.sh` exits non-zero and names the prim.

Point 3 is the whole thesis. A twin that only checks file validity is a viewer. A twin that
checks *design* validity is a decision layer, and that is the difference between a graphics
asset and an engineering artifact.

## What this is not

Scoping honestly is itself the signal, so:

- **Not CFD.** There is no fluid solve. Thermal data is *declared* per component and checked
  for consistency. It is a spec conformance check, not a simulation.
- **Not electrical solving.** No load-flow, no fault current, no harmonics. `power_budget_consistent`
  sums declared draw against declared capacity. That is arithmetic on a scene graph, and it is
  deliberately all it claims to be.
- **Not photoreal.** Materials are correct and bound, not art-directed.
- **Not gigawatt scale.** `N` tops out at a few thousand racks on one workstation.
- **Not a product.** No UI, no persistence layer, no auth.

The geometry is representative, not vendor CAD — see [Simulated vs. approximated](#simulated-vs-approximated).

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

Four owners, four layers, no merge conflicts. That is the entire pitch for OpenUSD as a
decision layer, demonstrated rather than asserted.

---

## Repository layout

```
aifactory-twin/
├── README.md                    # this file — the reference architecture
├── ARCHITECTURE.md              # layer strategy, composition decisions, decision log
├── SIMREADY_SPEC.md             # the domain spec the validators encode  (planned)
├── BENCHMARKS.md                # reproducible numbers, method stated    (planned)
├── docs/BUILD_GUIDE.md          # step-by-step build order
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
│   ├── optimize/                # instancing strategies, LOD variant sets
│   ├── validate/                # usdchecker + custom SimReady rules → report
│   └── consume/                 # ovrtx render, ovphysx physics
│
├── tests/
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

Guarded table. **A row flips to ✅ only when the milestone genuinely runs.**

| Milestone | What it delivers | Status |
|---|---|---|
| M0 | Reference architecture + layer diagram | ✅ done |
| M1 | Ingest + normalize + provenance manifest | ⬜ not started |
| M2 | URDF interop — import, then author what URDF cannot express | ⬜ not started |
| M3 | SimReady authoring — physics, materials, semantics, domain layers | ⬜ not started |
| M4 | Assembly + both instancing strategies at N = 64 / 512 / 4096 | ⬜ not started |
| M5 | Validation harness + CI gate | ⬜ not started |
| M6 | Two consumers (ovrtx, ovphysx) over one stage at independent rates | ⬜ not started |
| M7 | Reproducible benchmarks | ⬜ not started |
| M8 | Packaged reference architecture | ⬜ not started |

---

## Simulated vs. approximated

Stated up front rather than buried, because every one of these is somewhere a reader could
otherwise catch the project overclaiming.

| Claim | Reality |
|---|---|
| Rack / CDU / PDU geometry | **Procedurally generated** to representative dimensions and mass. Not vendor CAD. Dimensions and power figures are drawn from public spec sheets and are approximate. |
| Thermal data | **Declared, not solved.** No CFD anywhere in this repo. Validators check declarations are complete and self-consistent. |
| Electrical data | **Declared, not solved.** `power_budget_consistent` is a summation against declared capacity, not a load-flow study. |
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

- [ARCHITECTURE.md](ARCHITECTURE.md) — layer strategy, LIVRPS reasoning, decision log, URDF gap analysis
- [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) — follow-along: commands, signatures, verification per step
- [docs/BUILD_GUIDE.md](docs/BUILD_GUIDE.md) — why each step exists, the gotchas, and what it earns you
