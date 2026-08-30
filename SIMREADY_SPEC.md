# SimReady specification

What an asset must satisfy to be called simulation-ready in this project.

This document is the source of truth. `src/aifactory_twin/validate/` enforces it and
`ci/validate.sh` gates on it. **When the two disagree, this document is right and the code is
wrong.** Rules are written here in English first, on purpose: it forces the rule to encode
intent rather than whatever the implementation happened to do, and it keeps the spec readable
by a domain expert who does not know USD.

**The claim this harness makes:** valid USD and usable-by-`ovphysx` are different claims.
`usdchecker` makes the first. This harness makes the second.

> **Draft.** The numbers in §7 are representative placeholders and are labelled as such.
> Replace any you can source properly, and do not present them as sourced until you have.

---

## 1. The three tiers

Every rule sits in exactly one tier. The tier says who owns the rule and what it claims.

| Tier | Question | Owner | Status |
|---|---|---|---|
| **Tier 1 — Structural validity** | Is this valid USD? | The 28 built-in `UsdValidation` validators shipped with OpenUSD | delegated |
| **Tier 2 — Consumer fitness** | Is this asset usable by `ovphysx` and `ovrtx`? | Us. These are the rules we write | **the harness** |
| **Tier 3 — Engineering consistency** | Are the declared engineering values consistent with each other? | — | **designed, not built** — see §6 |

Tier 2 is the point of the project. Tier 1 is table stakes and we delegate it. Tier 3 is
specified and deliberately unimplemented.

## 2. How to read a rule

| Column | Meaning |
|---|---|
| **ID** | Stable. Reports cite it. Never renumber. |
| **Rule** | The requirement, in one line. |
| **Protects** | Which consumer breaks if this is violated. A Tier 2 rule with no answer here should be deleted. |
| **Sev** | `error` blocks the gate. `warning` is reported and does not block. |
| **Payload** | Whether the rule needs geometry loaded. Drives the two-pass runner — see §4. |

## 3. Severity

**error** — the asset is not simulation-ready. The gate exits non-zero.

**warning** — worth a human look. The gate still passes.

**Neither is "pass".** A rule that cannot evaluate — missing data, unloaded geometry it needed,
an unexpected schema — must report an explicit **skip** with a reason. A validator that passes
on absent input is worse than no validator, because it manufactures confidence.

## 4. Scope and the two passes

Rules apply to a **component** (one published asset under `assets/published/components/`) or a
**scene** (an assembled stage under `assets/published/scenes/`). Every component rule also runs
over the components a scene references.

`ARCHITECTURE.md` §3 puts domain metadata on the asset-root prim so it survives with geometry
unloaded. This spec is written to exploit that.

- **Fast pass** — every rule marked `Payload: no`, run against a `LoadNone` stage.
- **Full pass** — everything else, against a loaded stage.

If a rule is marked `no`, it must genuinely work unloaded. Verify it, do not assume it.

---

## 5. The rules

### Tier 1 — Structural validity

**Is this valid USD?** Delegated in full to the built-in `UsdValidation` validators. We register
no rule here and write no code; we run the suite and report what it returns.

| ID | Rule | Built-in validator |
|---|---|---|
| SR-STRUCT-003 | Every reference and payload resolves | `usdUtilsValidators:MissingReferenceValidator` |
| SR-STRUCT-005 | Attribute values match their declared type | `usdValidation:AttributeTypeMismatch` |
| SR-PHYS-002 | Any `RigidBodyAPI` prim has at least one collision prim beneath it | `usdPhysicsValidators:ColliderChecker` |
| SR-PHYS-004 | An articulated asset declares an articulation root | `usdPhysicsValidators:ArticulationChecker` |
| — | The remaining built-ins run as a suite: encapsulation, subset families, material binding relationships, skel bindings, package and file-extension checks | 24 others |

> **Confirm at step 10.** These attributions come from validator *names* registered by
> `usd-core` 26.8. What each actually checks has **not** been verified. Run them against a
> known-bad asset first. Where a built-in covers only part of a rule, the remainder moves to
> Tier 2 and says so.

---

### Tier 2 — Consumer fitness

**Is this asset usable by the consumers that will read it?** These are the rules we write. Each
names the consumer it protects.

#### 2.1 Physics consumer — `ovphysx`

| ID | Rule | Protects | Sev | Payload |
|---|---|---|---|---|
| SR-PHYS-001 | Any `RigidBodyAPI` prim declares mass > 0 | `ovphysx`: zero-mass rigid bodies are undefined in PhysX — they explode, sink, or stall the solver | error | no |
| SR-PHYS-003 | Mesh colliders above the triangle threshold (§7) declare an approximation | `ovphysx`: full-resolution mesh colliders are the classic cause of a scene that renders at 60 fps and simulates at 2 | error | yes |
| SR-PHYS-005 | Collision prims have a bound physics material | `ovphysx`: URDF friction lives in vendor extensions, so it is lost on import unless authored back, and contact behaviour silently falls to defaults | warning | yes |

#### 2.2 Render and sensor consumer — `ovrtx`

| ID | Rule | Protects | Sev | Payload |
|---|---|---|---|---|
| SR-RENDER-001 | Every renderable mesh resolves to a bound material | `ovrtx`: a binding that exists but does not resolve is silent — `ComputeBoundMaterial()` returns invalid and the mesh renders as default surface | error | yes |
| SR-RENDER-002 | Collision-only meshes are marked non-renderable (`purpose` = `guide` or `proxy`) | `ovrtx`: otherwise collision proxies appear in renders and in sensor output, and they also fail SR-RENDER-001 spuriously | error | yes |
| SR-RENDER-003 | Unique texture memory is under budget (§7) | `ovrtx`: texture memory, not triangle count, is what actually ends a large scene on a given GPU | warning | yes |
| SR-STRUCT-004 | Every texture asset path resolves | `ovrtx`: missing textures render as a default surface — wrong, but not visibly broken | error | yes |

#### 2.3 Synthetic data consumer

| ID | Rule | Protects | Sev | Payload |
|---|---|---|---|---|
| SR-SDG-001 | The asset-root prim carries a semantic class label | SDG: without labels, rendered images have no ground truth and the asset cannot produce training data | error | no |
| SR-SDG-002 | The label is drawn from the allowed class set (§7) | SDG: free-text labels fragment a dataset — `rack`, `Rack` and `rack_gb300` become three classes | error | no |

#### 2.4 Composition consumers — any referencing layer

| ID | Rule | Protects | Sev | Payload |
|---|---|---|---|---|
| SR-STRUCT-001 | `metersPerUnit == 1.0` and `upAxis == "Z"` | Every consumer: mixed units silently corrupt every mass and distance downstream. The built-in `StageMetadataChecker` confirms the metadata exists; this rule checks it holds our values | error | no |
| SR-STRUCT-002 | The layer declares a `defaultPrim` | Any referencing layer: without it, referencing the component requires an explicit prim path, so every consumer must know our internal naming | error | no |
| SR-STRUCT-006 | Nothing references a component's sublayer directly — only its interface layer | Every consumer: ADR-04. Referencing `geo.usdc` yields geometry with materials, mass and colliders silently absent, and it looks correct in a viewport | error | no |
| SR-STRUCT-007 | Prim names are valid USD identifiers | Every consumer: invalid names break path expressions and round-tripping | error | no |

#### 2.5 Domain layer contract — presence only

These rules check that the domain layers were **authored**. They check that an attribute exists
and is non-null, and they check that a token is drawn from its allowed set.

**They do not compare values, across prims or otherwise, and make no claim that the declared
values are correct or mutually consistent.** That is Tier 3, and it is not built.

| ID | Rule | Protects | Sev | Payload |
|---|---|---|---|---|
| SR-ELEC-001 | Powered equipment declares `aifactory:electrical:nominalPowerDrawW` and `:phase`, both non-null | Any consumer of the electrical layer: this rule exists because ADR-09 chose untyped custom attributes, where a typo becomes a new attribute rather than an error | error | no |
| SR-ELEC-002 | Declared draw is positive and within the sanity range (§7) | Any consumer of the electrical layer: catches unit errors — a value entered in kW rather than W is off by a thousand and otherwise passes every rule. A single-value bounds check, not a comparison | error | no |
| SR-ELEC-003 | `:phase` is drawn from the allowed token set (§7) | Any consumer of the electrical layer: untyped tokens accept anything, and `"3P"`, `"three-phase"` and `"3-phase"` cannot be compared | error | no |
| SR-THERM-001 | Heat-generating equipment declares `aifactory:thermal:heatOutputW` and `:coolingType`, both non-null | Any consumer of the thermal layer: same reasoning as SR-ELEC-001, for the second domain | error | no |
| SR-THERM-003 | `:coolingType` is drawn from the allowed token set (§7) | Any consumer of the thermal layer: as SR-ELEC-003 | error | no |

#### 2.6 Pipeline provenance

| ID | Rule | Protects | Sev | Payload |
|---|---|---|---|---|
| SR-PROV-001 | Every published component has a `manifest.json` entry with a source hash | Anyone auditing the pipeline: without it, "which source produced this, with which pipeline version" is archaeology | error | no |
| SR-PROV-002 | A scene references only published components, never anything in `assets/source/` | The pipeline itself: ADR-08. A scene reaching into source assets means the pipeline was bypassed | error | no |

---

## 6. Tier 3 — Engineering consistency

**Designed, not built.** No rule in this tier is implemented, registered, or run. Nothing in
this repository compares declared engineering values across prims or aggregates them.

Two rules were specified and then cut from the build:

- **Row power budget.** Sum declared draw across the equipment fed by a distribution unit and
  compare it against that unit's declared capacity.
- **Heat against draw.** Compare a component's declared heat output against its declared power
  draw, within a tolerance.

They are recorded here because the layer architecture was designed to make them possible — the
domain data is authored, sits on the asset root, and is readable with geometry unloaded — and
because a future implementation should reuse those IDs rather than inventing new ones. The
parameters they would need, including distribution-unit capacity and a heat-to-draw tolerance,
are deliberately **not fixed** in §7, because fixing them would imply a rule that does not exist.

See §8.

---

## 7. The numbers

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
| Racks per row | 8 | design parameter for assembly (M4) |

### Thresholds

| Quantity | Value | Provenance |
|---|---|---|
| Mesh-collider triangle threshold (SR-PHYS-003) | 10,000 | chosen; PhysX convex hulls degrade well before this |
| Power draw sanity range (SR-ELEC-002) | 100 W – 500,000 W | chosen to catch unit errors, not to be tight |
| Texture memory budget, component (SR-RENDER-003) | 512 MB | chosen |
| Texture memory budget, scene (SR-RENDER-003) | 4 GB | chosen |

### Allowed token sets

| Attribute | Allowed values |
|---|---|
| `aifactory:electrical:phase` | `1P`, `3P` |
| `aifactory:thermal:coolingType` | `air`, `liquid`, `hybrid` |
| semantic class (SR-SDG-002) | `rack`, `cdu`, `pdu`, `floor_tile`, `robot` |

---

## 8. What this spec does not check

Stated plainly, because every omission below is somewhere a reader could otherwise think this
claims more than it does.

- **No cross-prim engineering consistency.** Nothing here compares a declared value on one prim
  against a declared value on another, and nothing aggregates values across a row, a scene, or
  any other grouping. The domain data is authored and its **presence** is validated. Its
  **correctness and mutual consistency are not.** See §6.
- **Not load-flow.** No phase imbalance, inrush, power factor, derating, fault current, or
  selective coordination.
- **Not CFD.** Nothing computes airflow, a temperature field, or hot spots.
- **Not structural.** No floor loading, no seismic, no weight distribution.
- **Not code compliance.** Not NEC, not ASHRAE, not IEC, not any standard. This is one worked
  example of a domain spec, mirroring how real partners define theirs.
- **Not thermal-hydraulic.** Cooling type is a label. There is no loop model, no flow rate, no
  approach temperature.

## 9. Adding a rule

The interface is deliberately small so that a domain expert who is not a USD expert can add one.

1. Write the row here first — ID, rule, the consumer it protects, severity, payload.
2. **If it has no consumer to protect, it is not a Tier 2 rule.** Do not add it.
3. Check whether a built-in already covers it. Run that built-in against a known-bad asset to be
   sure, rather than trusting its name.
4. If not, implement it in `src/aifactory_twin/validate/rules.py` and register it into
   `UsdValidation.ValidationRegistry`, so it reports through the same error type as the
   built-ins.
5. Add a deliberately broken fixture under `tests/fixtures/` and a test asserting the rule fires
   on it. **A rule that has never been watched to fail is not known to work.**
6. The failure message says what to do, not just what is wrong. Compare:
   - Bad: `validation failed`
   - Good: `SR-ELEC-001: /rack_gb300 declares no power draw; set aifactory:electrical:nominalPowerDrawW in domain_electrical.usda`
