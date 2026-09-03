from pxr import Usd, UsdGeom, Gf
import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--racks", type=int, default=4)

args = parser.parse_args()

N = args.racks

REPO_ROOT = Path(__file__).resolve().parents[3]
path = REPO_ROOT / "assets/published/scenes/datahall.usda"
stage = Usd.Stage.CreateNew(str(path))

UsdGeom.SetStageMetersPerUnit(stage, 1.0)
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

world = UsdGeom.Xform.Define(stage, "/World")
racks_root = UsdGeom.Xform.Define(stage, "/World/Racks")

stage.SetDefaultPrim(world.GetPrim())

for i in range(N):

    rack_path = f"/World/Racks/Rack_{i:03d}"

    rack = UsdGeom.Xform.Define(
        stage,
        rack_path
    )

    rack.GetPrim().GetReferences().AddReference(
    "../components/rack_gb300/rack.usda"
    )

    rack.GetPrim().SetInstanceable(True)

    xform = UsdGeom.XformCommonAPI(rack)

    x = (i % 4) * 2.0
    y = (i // 4) * 3.0

    xform.SetTranslate(
        Gf.Vec3d(x, y, 0.0)
    )

stage.GetRootLayer().Save()

print(f"Created datahall with {N} racks")