# Architecture

This project converts source engineering assets into layered, validated SimReady OpenUSD
components that can be independently consumed by OVRTX and OVPhysX.

For the deeper rationale behind the decisions summarized here — LIVRPS reasoning, the full
decision log, provenance, instancing policy — see [`DESIGN_NOTES.md`](DESIGN_NOTES.md). This
document only states what is already true of V1.

---

## Current V1 Scope

What exists and runs today, and nothing more:

- The rack asset (`rack_gb300`) is authored as a **layered OpenUSD component**: one interface
  layer (`rack.usda`) that attaches a geometry payload and sublayers separate material,
  physics, and engineering-domain opinions.
- **Geometry, material, physics, and domain opinions are separate files**, not one monolithic
  asset — each with a different owner and a different reason to change.
- The published component is checked for **consumer fitness**, not just USD validity, by a set
  of custom rules (`src/aifactory_twin/validate/rules.py`) that check for things like a rigid
  body with no mass, or a mesh with no material binding.
- The same `rack.usda` component is **reused unmodified through scene composition** into two
  different scenes built for two different consumers: `rack_render.usda` and `rack_physics.usda`.
- **OVRTX produced a render.** `consume/render_ovrtx.py` opens `rack_render.usda` and writes a
  rendered frame to `_output/render.png`.
- **OVPhysX stepped the rigid body and changed its pose.** `consume/physics_ovphysx.py` opens
  `rack_physics.usda`, steps the simulation, and the rack's rigid body falls under gravity and
  is stopped by a static ground collider — a measured pose change, not just a stage that opens.

Nothing below is future work smuggled in as scope — see "Known Limitations of V1".

---

## Pipeline

```text
Source Asset
    ↓
Normalization / Authoring
    ↓
SimReady OpenUSD Component
    ↓
Validation
    ↓
Scene Composition
    ↓
Consumer Validation
   / \
OVRTX OVPhysX
```

---

## Component Layers

```text
rack.usda
├── geometry layer              (geo.usda, attached as a payload)
├── material layer              (material.usda)
├── physics layer               (physics.usda)
└── engineering-domain layer    (domain.usda)
```

These are separate files because they are separate **concerns**, separate **owners** (vendor
geometry, look-dev, simulation, site engineering), and separate **update cycles** — changing
one should never require touching or re-validating the others.

---

## Role of Geometry

Geometry is the base source representation; higher-level material, physics, and engineering
opinions are authored separately so source-geometry updates do not require rebuilding every
downstream concern.

---

## Validation: Two Levels

- **USD validity** — can the stage compose and open correctly?
- **Consumer fitness** — is it actually usable by the intended consumer?

A stage can pass the first and fail the second. For example:

- **OVRTX** cares about renderable/material state — a mesh with no resolved material binding
  is valid USD but renders wrong.
- **OVPhysX** cares about rigid-body/physics state — a `RigidBodyAPI` prim with no mass or no
  collider is valid USD but will not simulate correctly.

---

## Consumers

**OVRTX**
```text
Input:    composed USD scene (rack_render.usda)
Purpose:  rendering
Evidence: render image produced (_output/render.png)
```

**OVPhysX**
```text
Input:    composed USD scene with physics opinions (rack_physics.usda)
Purpose:  rigid-body simulation
Evidence: simulated pose changed after stepping — the rack fell under gravity and
          was stopped by the ground's static collider
```

---

## What is shared vs. consumer-specific?

| Shared | OVRTX-specific | OVPhysX-specific |
|---|---|---|
| geometry | render/material readiness | mass/collision/rigid body |
| composition | render product setup | physics step |
| engineering metadata | rendering output | simulated pose |

This is why the project builds **one** asset consumed two ways, instead of two separate
assets: the geometry, the composition, and the engineering metadata are identical no matter
which consumer opens the stage. Only the consumer-specific opinions layered on top, and the
outputs each consumer produces, differ.

---

## Known Limitations of V1

- No formal benchmark yet.
- No packaged one-command demo yet.
- No customer POC report yet.
- No agent skill yet.
- Limited scene scale tested — one rack, not a full data hall.

---

**The key architectural decision is that the OpenUSD asset remains the reusable source of
truth, while rendering and physics are independent downstream consumers with their own
validation requirements.**
