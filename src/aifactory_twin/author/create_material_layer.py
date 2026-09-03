from pathlib import Path

from pxr import Usd, UsdShade, Sdf, Gf

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = REPO_ROOT / "assets/published/components/rack_gb300/material.usda"

stage = Usd.Stage.CreateNew(str(OUTPUT_PATH))

material = UsdShade.Material.Define(
    stage,
    "/Looks/RackMaterial"
)

shader = UsdShade.Shader.Define(
    stage,
    "/Looks/RackMaterial/Shader"
)

shader.CreateIdAttr("UsdPreviewSurface")

shader.CreateInput(
    "diffuseColor",
    Sdf.ValueTypeNames.Color3f
).Set(Gf.Vec3f(0.2, 0.2, 0.2))

body = stage.OverridePrim("/Rack/Body")

UsdShade.MaterialBindingAPI.Apply(body)

UsdShade.MaterialBindingAPI(body).Bind(material)

stage.GetRootLayer().Save()