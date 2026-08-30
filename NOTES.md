# Engineering log

Running record of things that surprised us, and what changed as a result. Newest first.

---

## 2026-08-29 · Step 1 — environment

**Toolchain**

| | |
|---|---|
| `usd-core` | **26.8**, pinned exactly in `pyproject.toml` (M7 benchmarks need it) |
| `numpy` | 2.5.2 |
| `pytest` | 9.1.1 |
| Python | 3.12 |
| Platform | macOS (darwin), Apple silicon |

**`UsdUtils.ComplianceChecker` does not exist in usd-core 26.8.**

Neither the class nor the `pxr.UsdUtils.complianceChecker` module. There is also no
`usdchecker` binary in the venv — `usd-core` is a minimal build and ships no command line
tools. The plan for step 10 assumed this API would be there.

It has been superseded. OpenUSD now has a **`UsdValidation` framework**, and it *is* present:

```python
from pxr import UsdValidation
registry = UsdValidation.ValidationRegistry()
registry.GetAllValidatorMetadata()   # 28 validators registered
```

Types available: `ValidationRegistry`, `ValidationContext`, `ValidationError`,
`ValidationErrorSite`, `ValidationErrorType`, `ValidationFixer`, `ValidationTimeRange`.
Registration hooks for prim / stage / layer validators, and for suites.

**This is better than what we planned for**, not worse. 28 validators ship built in, and
several are rules we were going to write by hand:

| Built-in | Rule it covers from `SIMREADY_SPEC.md` |
|---|---|
| `usdUtilsValidators:MissingReferenceValidator` | `no_unresolved_references` |
| `usdPhysicsValidators:RigidBodyChecker` | part of `rigidbody_has_mass` |
| `usdPhysicsValidators:ColliderChecker` | part of `rigidbody_has_collider` |
| `usdPhysicsValidators:ArticulationChecker` | M2 robot articulation sanity |
| `usdShadeValidators:MaterialBindingApiAppliedValidator` | part of `all_meshes_bound` |
| `usdShadeValidators:MaterialBindingRelationships` | part of `all_meshes_bound` |
| `usdValidation:StageMetadataChecker`, `usdGeomValidators:StageMetadataChecker` | part of `valid_units` |
| `usdValidation:AttributeTypeMismatch` | catches the ADR-09 typed-attribute risk directly |

**Change to the plan for step 10.** Do not write a bespoke `Rule` class and runner. Register
the AI-factory domain validators into `UsdValidation.ValidationRegistry` as first-class
validators, so they run alongside the 28 built-ins and report through the same
`ValidationError` type. One report, one severity model, one runner.

Still to confirm at step 10: whether `ValidationContext` can be driven against a `LoadNone`
stage, which is what the fast domain gate in `ARCHITECTURE.md` §3 depends on. If it cannot, the
domain rules run standalone against an unloaded stage and the built-ins run in the full pass.

Fallback if ever needed: a full OpenUSD build with `usdchecker` exists locally at
`OpenUSD-NVIDIA/usd_root/bin/`. Not portable, so not the CI answer.

**`UsdSemantics` is available — `LabelsAPI`, `LabelsQuery`, `Tokens`.**

Settles the open question from the M0 docs. Use core `UsdSemantics.LabelsAPI` at step 8; the
older Omniverse `Semantics` extension is not needed and is not present.

**`PhysxSchema` is not available — expected.**

NVIDIA extension, ships with Omniverse/Isaac, not with core USD. Core `UsdPhysics` is present
and is all steps 7 and 10 need. PhysX-specific solver tuning stays Brev-only work, as planned.
