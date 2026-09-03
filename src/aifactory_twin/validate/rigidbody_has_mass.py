from pxr import Usd, UsdPhysics
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PATH = REPO_ROOT / "assets/published/components/rack_gb300/rack.usda"

stage = Usd.Stage.Open(str(PATH))

failed = False

for prim in stage.Traverse():
    # Only rigid bodies are required to carry mass. Checking every prim in the
    # stage would fail on materials, shaders, and scopes that were never
    # meant to have MassAPI applied in the first place.
    if not prim.HasAPI(UsdPhysics.RigidBodyAPI):
        continue

    print("Rigid body:", prim.GetPath())

    if not prim.HasAPI(UsdPhysics.MassAPI):
        print("FAIL:", prim.GetPath(), "has no MassAPI")
        # A missing MassAPI is a real failure too, so it must set `failed`
        # the same as the mass <= 0 case below — otherwise this prints FAIL
        # but the exit code still reports success.
        failed = True
        continue

    mass_api = UsdPhysics.MassAPI(prim)
    mass = mass_api.GetMassAttr().Get()
    print("Mass:", mass)

    if mass is None or mass <= 0:
        print("FAIL:", prim.GetPath(), "must declare mass > 0")
        failed = True
    else:
        print("PASS:", prim.GetPath(), "mass =", mass)

if failed:
    raise SystemExit(1)

raise SystemExit(0)