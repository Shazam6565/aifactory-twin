# SimReady specification

What an asset must satisfy to be called simulation-ready in this project.

This document is the source of truth. `src/aifactory_twin/validate/` enforces it and
`ci/validate.sh` gates on it. **When the two disagree, this document is right and the code is
wrong.** Rules are written here in English first, on purpose: it forces the rule to encode
intent rather than whatever the implementation happened to do, and it keeps the spec readable
by a domain expert who does not know USD.

> **Draft.** Rules are settled. The numbers in §6 are representative placeholders and are
> labelled as such. Replace any you can source properly, and do not present them as sourced
> until you have.

---

## 1. How to read a rule

| Column | Meaning |
|---|---|
| **ID** | Stable. Reports cite it. Never renumber. |
| **Rule** | The requirement, in one line. |
| **Why** | What breaks downstream if it is violated. The column that justifies the rule existing. |
| **Sev** | `error` blocks the gate. `warning` is reported and does not block. |
| **Payload** | Whether the rule needs geometry loaded. Drives the two-pass runner — see §4. |
| **Source** | `built-in` = a validator that ships with OpenUSD. `ours` = we write it. |

## 2. Severity

**error** — the asset is not simulation-ready. The gate exits non-zero.

**warning** — worth a human look. The gate still passes.

**Neither is "pass".** A rule that cannot evaluate — missing data, unloaded geometry it needed,
an unexpected schema — must report an explicit **skip** with a reason. A validator that passes
on absent input is worse than no validator, because it manufactures confidence.

## 3. Scope

Rules apply to one of two things:

- **Component** — a single published asset under `assets/published/components/`.
- **Scene** — an assembled stage under `assets/published/scenes/`.

Every component rule also runs over the components a scene references.

## 4. The two passes

`ARCHITECTURE.md` §3 puts domain metadata on the asset-root prim so it survives with geometry
unloaded. This spec is written to exploit that.

- **Fast pass** — every rule marked `Payload: no`, run against a `LoadNone` stage. Cheap enough
  to run on every commit across the whole hall.
- **Full pass** — everything else, against a loaded stage.

If a rule is marked `no`, it must genuinely work unloaded. Verify it, do not assume it.

---

## 5. Rules

### 5.1 Structural — component

| ID | Rule | Why | Sev | Payload | Source |
|---|---|---|---|---|---|
| SR-STRUCT-001 | `metersPerUnit == 1.0` and `upAxis == "Z"` | Mixed units silently corrupt every mass, distance and power figure downstream. The single most common real-world twin bug | error | no | built-in + ours |
| SR-STRUCT-002 | The layer declares a `defaultPrim` | Without it, referencing the component requires an explicit prim path, so every consumer must know our internal naming | error | no | ours |
| SR-STRUCT-003 | Every reference and payload resolves | A broken arc composes to nothing and looks like an empty asset, not an error | error | no | built-in |
| SR-STRUCT-004 | Every texture asset path resolves | Missing textures render as a default surface — silently wrong, not visibly broken | error | yes | ours |
| SR-STRUCT-005 | Attribute values match their declared type | Guards ADR-09: domain data is untyped custom attributes, so a `Float` authored as a `Double` is otherwise invisible | error | no | built-in |
| SR-STRUCT-006 | Nothing references a component's sublayer directly — only its interface layer | ADR-04. Referencing `geo.usdc` gets geometry with materials, mass, colliders and power ratings silently absent. It looks correct in a viewport | error | no | ours |
| SR-STRUCT-007 | Prim names are valid USD identifiers | Invalid names break path expressions and round-tripping | error | no | ours |

### 5.2 Physics fitness — component

| ID | Rule | Why | Sev | Payload | Source |
|---|---|---|---|---|---|
| SR-PHYS-001 | Any `RigidBodyAPI` prim declares mass > 0 | Zero-mass rigid bodies behave undefined in PhysX — they explode, sink, or freeze the solver | error | no | built-in + ours |
| SR-PHYS-002 | Any `RigidBodyAPI` prim has at least one collision prim beneath it | A rigid body with no collider falls through the world | error | yes | built-in |
| SR-PHYS-003 | Mesh colliders above the triangle threshold (§6) declare an approximation | Full-resolution mesh colliders are the classic cause of a scene that renders at 60 fps and simulates at 2 | error | yes | ours |
| SR-PHYS-004 | An articulated asset declares an articulation root | URDF has a kinematic tree but no solver root. Without one the robot imports and then does not articulate | error | yes | built-in |
| SR-PHYS-005 | Collision prims have a bound physics material | URDF friction lives in vendor extensions, so it is lost on import unless authored back | warning | yes | ours |

### 5.3 Render fitness — component

| ID | Rule | Why | Sev | Payload | Source |
|---|---|---|---|---|---|
| SR-RENDER-001 | Every renderable mesh resolves to a bound material | A binding that exists but does not resolve is a silent failure — `ComputeBoundMaterial()` returns invalid and the mesh renders default | error | yes | built-in + ours |
| SR-RENDER-002 | Collision-only meshes are marked non-renderable (`purpose` = `guide` or `proxy`) | Otherwise they are counted as renderable, fail SR-RENDER-001, and tempt you to weaken the rule instead of fixing the asset | error | yes | ours |
| SR-RENDER-003 | Unique texture memory is under budget (§6) | Texture memory, not triangles, is what actually ends a large scene on a given GPU | warning | yes | ours |

### 5.4 Synthetic data fitness — component

| ID | Rule | Why | Sev | Payload | Source |
|---|---|---|---|---|---|
| SR-SDG-001 | The asset-root prim carries a semantic class label | Without labels, rendered images have no ground truth and the asset is useless for synthetic data generation | error | no | ours |
| SR-SDG-002 | The label is drawn from the allowed class set (§6) | Free-text labels fragment a dataset — `rack`, `Rack` and `rack_gb300` become three classes | error | no | ours |

### 5.5 Electrical domain — component and scene

| ID | Rule | Why | Sev | Payload | Source |
|---|---|---|---|---|---|
| SR-ELEC-001 | Powered equipment declares `aifactory:electrical:nominalPowerDrawW` and `:phase` | The twin cannot answer its main question without them. This rule exists specifically because ADR-09 chose untyped custom attributes, where a typo becomes a new attribute rather than an error | error | no | ours |
| SR-ELEC-002 | Declared draw is positive and within the sanity range (§6) | Catches unit errors — a rack declared in kW rather than W is off by a thousand and otherwise passes every other rule | error | no | ours |
| SR-ELEC-003 | `:phase` is drawn from the allowed token set (§6) | Untyped tokens accept anything. `"3P"`, `"three-phase"` and `"3-phase"` cannot be compared | error | no | ours |
| **SR-ELEC-004** | **Sum of declared draw across a row does not exceed the declared capacity of the PDU feeding it** | **The rule this project exists for. Over-subscribe a PDU on paper and you build a hall you cannot fully populate. Catching it here costs nothing; catching it after the concrete is poured costs a great deal** | **error** | **no** | **ours** |

### 5.6 Thermal domain — component

| ID | Rule | Why | Sev | Payload | Source |
|---|---|---|---|---|---|
| SR-THERM-001 | Heat-generating equipment declares `aifactory:thermal:heatOutputW` and `:coolingType` | Same reasoning as SR-ELEC-001, for the second domain | error | no | ours |
| SR-THERM-002 | Declared heat output is within tolerance (§6) of declared power draw | Nearly all electrical power into compute leaves as heat. A rack declaring 130 kW draw and 40 kW heat is a spec error, and no single-domain check can see it — **this rule only exists because electrical and thermal are separate layers that can be compared** | error | no | ours |
| SR-THERM-003 | `:coolingType` is drawn from the allowed token set (§6) | As SR-ELEC-003 | error | no | ours |

### 5.7 Provenance — component and scene

| ID | Rule | Why | Sev | Payload | Source |
|---|---|---|---|---|---|
| SR-PROV-001 | Every published component has a `manifest.json` entry with a source hash | Without it, "which source produced this, with which pipeline version" is archaeology | error | no | ours |
| SR-PROV-002 | A scene references only published components, never anything in `assets/source/` | ADR-08. A scene reaching into source assets means the pipeline was bypassed | error | no | ours |

> **Confirm at step 10.** The `built-in` attributions are candidates identified from the
> validator names registered by `usd-core` 26.8 (`MissingReferenceValidator`,
> `RigidBodyChecker`, `ColliderChecker`, `ArticulationChecker`,
> `MaterialBindingApiAppliedValidator`, `StageMetadataChecker`, `AttributeTypeMismatch`). What
> each one actually checks has **not** been verified. Run them against a known-bad asset first,
> then write ours for whatever they miss. `built-in + ours` means the built-in covers part of
> the rule and we extend it — for example `RigidBodyChecker` may check the API is applied
> without checking mass is greater than zero.

---

## 6. The numbers

> **Provenance warning.** Everything below is **chosen as representative** — order-of-magnitude
> figures for a liquid-cooled AI rack, not vendor data and not measured. `README.md` says so
> publicly. If you replace one with a sourced figure, cite the source in this table and nowhere
> else, so there is one place to check.

### Equipment

| Quantity | Value | Provenance |
|---|---|---|
| Rack nominal power draw | 132,000 W | representative |
| Rack heat output | 130,000 W | representative |
| Rack phase | `3P` | representative |
| Rack cooling type | `liquid` | representative |
| Rack mass | 1,400 kg | representative |
| CDU power draw | 12,000 W | representative |
| PDU capacity | 1,200,000 W | representative |
| Racks per row | 8 | design parameter |

**Row arithmetic, chosen deliberately.** Eight racks at 132 kW draw 1,056 kW against a 1,200 kW
PDU — compliant, with 144 kW of headroom, a little over one rack. **A ninth rack takes the row
to 1,188 kW and still passes; a tenth breaks it.** That is the deliberate failure used to prove
SR-ELEC-004 actually fires. Tune `racks per row` and watch the gate flip.

### Thresholds

| Quantity | Value | Provenance |
|---|---|---|
| Mesh-collider triangle threshold (SR-PHYS-003) | 10,000 | chosen; PhysX convex hulls degrade well before this |
| Heat / draw tolerance (SR-THERM-002) | ±10 % | chosen; covers fans, losses and rounding |
| Power draw sanity range (SR-ELEC-002) | 100 W – 500,000 W | chosen to catch kW/W unit errors, not to be tight |
| Texture memory budget, component (SR-RENDER-003) | 512 MB | chosen |
| Texture memory budget, scene (SR-RENDER-003) | 4 GB | chosen |

### Allowed token sets

| Attribute | Allowed values |
|---|---|
| `aifactory:electrical:phase` | `1P`, `3P` |
| `aifactory:thermal:coolingType` | `air`, `liquid`, `hybrid` |
| semantic class (SR-SDG-002) | `rack`, `cdu`, `pdu`, `floor_tile`, `robot` |

---

## 7. What this spec does not check

Stated plainly, because every omission below is somewhere a reader could otherwise think this
claims more than it does.

- **Not load-flow.** SR-ELEC-004 is a summation against a declared capacity. It cannot see phase
  imbalance, inrush, power factor, derating, fault current, or selective coordination.
- **Not CFD.** Nothing here computes airflow, a temperature field, or hot spots. SR-THERM-002
  compares two declared numbers.
- **Not structural.** No floor loading, no seismic, no weight distribution.
- **Not code compliance.** This is not NEC, not ASHRAE, not IEC, not any standard. It is one
  worked example of a domain spec, mirroring how real partners define theirs.
- **Not thermal-hydraulic.** Cooling type is a label. There is no loop model, no flow rate, no
  approach temperature.

## 8. Adding a rule

The interface is deliberately small so that a domain expert who is not a USD expert can add one.

1. Write the row here first — ID, rule, why, severity, payload, source.
2. Check whether a built-in already covers it. Run it against a known-bad asset to be sure.
3. If not, implement it in `src/aifactory_twin/validate/rules.py` and register it into
   `UsdValidation.ValidationRegistry`, so it reports through the same error type as the
   built-ins.
4. Add a deliberately broken fixture under `tests/fixtures/` and a test asserting the rule fires
   on it. **A rule that has never been watched to fail is not known to work.**
5. The failure message says what to do, not just what is wrong. Compare:
   - Bad: `validation failed`
   - Good: `SR-ELEC-001: /rack_gb300 declares no power draw; set aifactory:electrical:nominalPowerDrawW in domain_electrical.usda`
