from pxr import UsdPhysics, Usd, UsdGeom, UsdShade
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PATH = REPO_ROOT / "assets/published/components/rack_gb300/rack.usda"

stage = Usd.Stage.Open(str(PATH))


def rigidbody_has_mass(stage):
    errors = []

    for prim in stage.Traverse():
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            continue

        if not prim.HasAPI(UsdPhysics.MassAPI):
            errors.append(
                f"{prim.GetPath()}: rigid body has no MassAPI"
            )
            continue

        mass = UsdPhysics.MassAPI(
            prim
        ).GetMassAttr().Get()

        if mass is None or mass <= 0:
            errors.append(
                f"{prim.GetPath()}: mass must be > 0"
            )

    return errors

def rigidbody_has_collider(stage):
    errors = []

    for prim in stage.Traverse():
        if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            continue

        found_collider = False

        for child in Usd.PrimRange(prim):
            if child.HasAPI(UsdPhysics.CollisionAPI):
                found_collider = True
                break

        if not found_collider:
            errors.append(
                f"{prim.GetPath()}: rigid body has no collider"
            )

    return errors

def all_renderables_bound(stage):
    errors = []

    for prim in stage.Traverse():

        if not prim.IsA(UsdGeom.Gprim):
            continue

        binding_api = UsdShade.MaterialBindingAPI(prim)

        material, relationship = (
            binding_api.ComputeBoundMaterial()
        )

        if not material:
            errors.append(
                f"{prim.GetPath()}: no resolved material binding"
            )

    return errors

def all_renderables_bound(stage):
    errors = []

    for prim in stage.Traverse():

        if not prim.IsA(UsdGeom.Gprim):
            continue

        binding_api = UsdShade.MaterialBindingAPI(prim)

        material, relationship = (
            binding_api.ComputeBoundMaterial()
        )

        if not material:
            errors.append(
                f"{prim.GetPath()}: no resolved material binding"
            )

    return errors

def semantics_present(stage):
    errors = []

    rack = stage.GetPrimAtPath("/Rack")

    attr = rack.GetAttribute(
        "aifactory:semantic:class"
    )

    value = attr.Get() if attr else None

    if not value:
        errors.append(
            "/Rack: semantic class missing"
        )

    return errors

def electrical_complete(stage):
    errors = []

    rack = stage.GetPrimAtPath("/Rack")

    power = rack.GetAttribute(
        "aifactory:electrical:nominalPowerDrawW"
    ).Get()

    phase = rack.GetAttribute(
        "aifactory:electrical:phase"
    ).Get()

    if power is None:
        errors.append(
            "/Rack: electrical power draw missing"
        )

    if not phase:
        errors.append(
            "/Rack: electrical phase missing"
        )

    return errors

def thermal_complete(stage):
    errors = []

    rack = stage.GetPrimAtPath("/Rack")

    heat = rack.GetAttribute(
        "aifactory:thermal:heatOutputW"
    ).Get()

    cooling = rack.GetAttribute(
        "aifactory:thermal:coolingType"
    ).Get()

    if heat is None:
        errors.append(
            "/Rack: heat output missing"
        )

    if not cooling:
        errors.append(
            "/Rack: cooling type missing"
        )

    return errors