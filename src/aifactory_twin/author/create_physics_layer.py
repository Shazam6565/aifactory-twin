from pathlib import Path

from pxr import Usd, UsdPhysics

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = REPO_ROOT / "assets/published/components/rack_gb300/physics.usda"

stage = Usd.Stage.CreateNew(str(OUTPUT_PATH))

rack = stage.OverridePrim("/Rack")

UsdPhysics.RigidBodyAPI.Apply(rack)
mass_api = UsdPhysics.MassAPI.Apply(rack)
mass_api.CreateMassAttr(1000.0)

# It gives the prim rigid-body behavior so a physics solver can treat it as a dynamic physical object.


body = stage.OverridePrim("/Rack/Body")
UsdPhysics.CollisionAPI.Apply(body)



stage.GetRootLayer().Save()

print("Created physics.usda")


stage.GetRootLayer().Save()

