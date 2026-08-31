# SimReady specification

What an asset must satisfy to be called simulation-ready in this project.

This document is the source of truth. `src/aifactory_twin/validate/` enforces it and
`ci/validate.sh` gates on it. **When the two disagree, this document is right and the code is
wrong.** Rules are written here in English first, on purpose: it forces the rule to encode
intent rather than whatever the implementation happened to do, and it keeps the spec readable
by a domain expert who does not know USD.

**The claim this harness makes:** valid USD and usable-by-`ovphysx` are different claims.
`usdchecker` makes the first. This harness makes the second.

> **Draft.** The numbers in §6 are representative placeholders and are labelled as such.
> Replace any you can source properly, and do not present them as sourced until you have.

---

## 1. The three tiers

Every rule sits in exactly one tier. The tier says who owns the rule and what it claims.

| Tier | Question | Owner | Status |
|---|---|---|---|
| **Tier 1 — Structural validity** | Is this valid USD? | The 28 built-in `UsdValidation` validators shipped with OpenUSD | delegated |
| **Tier 2 — Consumer fitness** | Is this asset usable by `ovphysx` and `ovrtx`? | Us. These are the rules we write | **the harness** |
| **Tier 3 — Engineering consistency** | Are the declared engineering values consistent with each other? | — | **designed, not built** — see §5 and §7 |

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

`SCOPE.md` is the contract. It names **six** custom validators. Everything else here is
delegated to the built-ins or is not built.

### Tier 1 — Structural validity

**Is this valid USD?** Delegated in full to the `UsdValidation` validators shipped with
`usd-core` 26.8. We register nothing here and write no code; we run the suite and report what
it returns.

| Structural concern | Built-in validator(s) |
|---|---|
| References and payloads resolve | `usdUtilsValidators:MissingReferenceValidator` |
| Composition errors surface | `usdValidation:CompositionErrorTest` |
| Attribute values match declared type | `usdValidation:AttributeTypeMismatch` |
| Stage metadata present and well-formed | `usdValidation:StageMetadataChecker`, `usdGeomValidators:StageMetadataChecker` |
| Prim encapsulation rules | `usdGeomValidators:EncapsulationChecker`, `usdLuxValidators:EncapsulationRulesValidator`, `usdShadeValidators:EncapsulationRulesValidator`, `usdShadeValidators:EncapsulationMaterialValidator` |
| Material binding relationships well-formed | `usdShadeValidators:MaterialBindingApiAppliedValidator`, `:MaterialBindingRelationships`, `:MaterialBindingCollectionValidator` |
| Shader and texture compliance | `usdShadeValidators:ShaderSdrCompliance`, `:NormalMapTextureValidator` |
| Geom subset families | `usdGeomValidators:SubsetFamilies`, `:SubsetParentIsImageable`, `usdShadeValidators:SubsetMaterialBindFamilyName`, `:SubsetsMaterialBindFamily` |
| Physics schema application | `usdPhysicsValidators:RigidBodyChecker`, `:ColliderChecker`, `:ArticulationChecker`, `:PhysicsJointChecker` |
| Skeleton bindings | `usdSkelValidators:SkelBindingApiAppliedValidator`, `:SkelBindingApiValidator` |
| Packaging and file extensions | `usdUtilsValidators:PackageEncapsulationValidator`, `:RootPackageValidator`, `:UsdzPackageValidator`, `:FileExtensionValidator` |

> **Not yet verified.** These attributions come from validator *names*. What each actually
> checks has not been confirmed. Run them against a known-bad asset before relying on the
> mapping. Two in particular — `RigidBodyChecker` and `ColliderChecker` — may overlap the
> custom rules below; if they fully cover them, the custom pair should be deleted rather than
> duplicated.

### Tier 2 — Consumer fitness

**Is this asset usable by `ovphysx` and by `ovrtx`?** These are the six custom validators from
`SCOPE.md`, registered into `UsdValidation.ValidationRegistry` so they report through the same
`ValidationError` type as the built-ins.

**None of them compare values across prims.** Every one is per-prim.

| ID | Rule | Protects | Checks | Sev | Payload |
|---|---|---|---|---|---|
| SR-PHYS-001 | `rigidbody_has_mass` | `ovphysx` — zero-mass rigid bodies are undefined in PhysX; they explode, sink, or stall the solver | Any `RigidBodyAPI` prim declares mass > 0 | error | no |
| SR-PHYS-002 | `rigidbody_has_collider` | `ovphysx` — a rigid body with no collider falls through the world | Any `RigidBodyAPI` prim has at least one collision prim | error | yes |
| SR-RENDER-001 | `all_meshes_bound` | `ovrtx` — a binding that exists but does not resolve is silent; `ComputeBoundMaterial()` returns invalid and the mesh renders as default surface | Every renderable mesh has a resolved material binding | error | yes |
| SR-SDG-001 | `semantics_present` | SDG consumers — without labels, rendered images have no ground truth and cannot produce training data | Every asset-root prim carries a `UsdSemantics` label | error | no |
| SR-ELEC-001 | `electrical_complete` | domain consumers — ADR-09 chose untyped custom attributes, where a typo becomes a new attribute rather than an error | Powered equipment declares power draw and phase. **Presence only:** the attribute exists and is non-null | error | no |
| SR-THERM-001 | `thermal_complete` | domain consumers — as `electrical_complete`, for the second domain | Heat-generating equipment declares heat output and cooling type. **Presence only**, no cross-prim comparison | error | no |

```
# TODO: verify against usdPhysicsValidators before implementing
#   SR-PHYS-001 rigidbody_has_mass      vs usdPhysicsValidators:RigidBodyChecker
#   SR-PHYS-002 rigidbody_has_collider  vs usdPhysicsValidators:ColliderChecker
# Both built-ins already ship. If either fully covers our rule, delete ours rather
# than duplicating it. Run both against a known-bad asset to settle it.
```

### Tier 3 — Engineering consistency

**Designed, not built.** Nothing in this repository compares declared engineering values across
prims, and nothing aggregates them. `power_budget_consistent` — summing rack draw against a
declared distribution capacity — is specified and deliberately unimplemented; it needs a
topology model of which racks feed from which unit, which this repo does not have. The layer
architecture was designed to make such a rule cheap, and that capability is unused. The domain
data is authored and its presence is validated; its correctness and mutual consistency are not.
See §7.

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
| Racks per row | 8 | design parameter for assembly |

### Thresholds

No thresholds remain. Every rule that needed one — collider triangle count, texture memory
budget, power-draw sanity range — was cut with Tier 3 or is not among the six.

### Allowed token sets

| Attribute | Allowed values |
|---|---|
| `aifactory:electrical:phase` | `1P`, `3P` |
| `aifactory:thermal:coolingType` | `air`, `liquid`, `hybrid` |
| semantic class (SR-SDG-001) | `rack`, `cdu`, `pdu`, `floor_tile` |

---

## 7. What this spec does not check

Mirrors the out-of-scope list in `SCOPE.md`. Stated plainly, because every omission below is
somewhere a reader could otherwise think this claims more than it does.

- **No cross-component engineering consistency.** Nothing compares a declared value on one prim
  against a declared value on another, and nothing aggregates across a row, a scene or any other
  grouping. `power_budget_consistent` is specified and **not implemented** — it needs a topology
  model of which racks feed from which distribution unit. Designed, not built.
- **No CFD, thermal solving, or electrical solving.** Never intended. Thermal and electrical
  values are declared attributes, not solved fields. No load-flow, no phase imbalance, no fault
  current, no airflow, no temperature field.
- **No real geometry.** Components use dimensionally-plausible proxy boxes. The pipeline is the
  artifact; the geometry is a placeholder.
- **No LOD variant sets.** Designed, not built.
- **No `ovstorage`, `ovstream`, or MCP/agent query tooling.** Out of scope entirely.
- **No URDF import.** Not covered by this repo.
- **No production scale.** Demonstrated to N = 4096 on one machine. The architecture is the
  claim; the scale is an illustration.
- **Not code compliance.** Not NEC, not ASHRAE, not IEC, not any standard. This is one worked
  example of a domain spec, mirroring how real partners define theirs.

## 8. Adding a rule

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
