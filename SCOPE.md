# Scope — `aifactory-twin`

> This document is the contract for what this repo claims. If something is not listed
> under "In scope" below, this repo does not do it. Status is kept honest — a milestone is
> marked done only when its done-condition is demonstrably met.

---

## What this is, in one sentence

One rack asset, built as a layered OpenUSD component, replicated into a data hall, and
gated by a validation harness that checks the asset is usable by `ovrtx` and `ovphysx`.

## What this is not

A digital-twin product, an engineering analysis tool, or a decision system for whether a
facility should be built. It is a **SimReady asset pipeline with a validation gate**.

---

## In scope

| # | Deliverable | Done when |
|---|---|---|
| 1 | One layered component (`rack_gb300`) — interface layer, geometry payload, physics / material / domain sublayers | Each sublayer file contains only its own opinions when opened in a text editor |
| 2 | Unloaded-stage domain query | A script opens the stage with `Usd.Stage.LoadNone` and prints power draw plus a composed prim count, with no geometry loaded |
| 3 | Six custom validators registered into `UsdValidation.ValidationRegistry` | They run alongside the 28 built-in validators and report through the same `ValidationError` type |
| 4 | `datahall.usda` — N racks via scenegraph instancing, floor tiles via `UsdGeomPointInstancer` | N is a CLI parameter; the gate passes at N = 64, 512, 4096 |
| 5 | `ci/validate.sh` and a deliberately broken fixture | Running the gate against `tests/broken/` exits nonzero and names the offending prim |

### The six custom validators

All six are **consumer-fitness** checks. None of them compare values across prims.

| Rule | Protects | Checks |
|---|---|---|
| `rigidbody_has_mass` | `ovphysx` | Any `RigidBodyAPI` prim declares mass > 0 |
| `rigidbody_has_collider` | `ovphysx` | Any `RigidBodyAPI` prim has at least one collision prim |
| `all_meshes_bound` | `ovrtx` | Every renderable mesh has a resolved material binding |
| `semantics_present` | SDG consumers | Every asset-root prim carries a `UsdSemantics` label |
| `electrical_complete` | domain consumers | Powered equipment declares power draw and phase (**presence only**) |
| `thermal_complete` | domain consumers | Heat-generating equipment declares heat output and cooling type (**presence only**, no cross-prim comparison) |

---

## Out of scope

Stated up front rather than discovered later.

- **Cross-component engineering consistency.** `power_budget_consistent` — summing rack
  draw against declared PDU capacity — is specified in `SIMREADY_SPEC.md` and **not
  implemented**. It requires a topology model of which racks feed from which PDU. Designed,
  not built.
- **CFD, thermal solving, electrical solving.** Never intended. Thermal and electrical
  values are declared attributes, not solved fields.
- **Real geometry.** Components use dimensionally-plausible proxy boxes. The pipeline is
  the artifact; the geometry is a placeholder.
- **LOD variant sets — not built.**
- **`ovstorage`, `ovstream`, MCP/agent query tooling.** Out of scope entirely.
- **URDF import.** Not covered by this repo.
- **Production scale.** Demonstrated to N = 4096 on one machine. The architecture is the
  claim; the scale is an illustration.

---

## Benchmark method

Measured on CPU with `usd-core` only — no GPU required, so the numbers are reproducible on
any laptop.

**Measured:** stage-open wall time, and composed prim count.
**Not measured:** VRAM, frame time, render throughput. Those need a GPU and are excluded
deliberately rather than estimated.

**Method:** three runs per configuration, median reported, cold process each time. Python
version, `usd-core` version, OS and CPU recorded in `BENCHMARKS.md`.

| Config | Stage open (s) | Composed prims |
|---|---|---|
| Flattened, N=512 | | |
| + geometry as payload | | |
| + scenegraph instancing (racks) | | |
| + PointInstancer (floor tiles) | | |

---

## Build order

Each step ends in a demonstrable state. If work stops at any boundary, what exists is still
coherent and still explainable.

1. **Vertical slice.** One cube → `geo.usdc`. Interface layer with payload and three
   sublayers. Author mass, collider, material binding, semantics and the `aifactory:`
   attributes — domain attributes on the **asset-root prim** (see ADR-05).
   *Ends with:* the unloaded-stage query printing a power value and a prim count.
2. **The gate.** Six validators registered. `ci/validate.sh`. Broken fixture under
   `tests/broken/`.
   *Ends with:* a red exit code naming the prim.
3. **The hall.** `assemble.py`, N as a CLI flag, `SetInstanceable(True)` on rack
   references, `PointInstancer` for floor tiles.
   *Ends with:* the gate passing on a 4096-rack hall.
4. **Benchmarks and docs.** The four-row table. `README.md` and `ARCHITECTURE.md` brought
   in line with what exists.
5. **Consumers (GPU, time-boxed).** Install `ovrtx` and `ovphysx` wheels. Render one frame
   to PNG; load the hall in `ovphysx` and step once, printing the rigid-body count.
   *If the wheels do not install within half a day, stop and record what failed.* An
   Early Access install failure is a legitimate documented outcome, not a gap to hide.

---

## Honesty guardrails

- The status table in `README.md` never claims a milestone whose done-condition is unmet.
- Benchmarks state method and hardware, or they are not published.
- Anything stubbed because an Early Access API moved is marked `# STUB:` in code and named
  in the README.
- No partner or customer validation is claimed, because none exists.
