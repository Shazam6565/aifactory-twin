from pxr import Usd

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PATH = REPO_ROOT / "assets/published/components/rack_gb300/rack.usda"

stage = Usd.Stage.Open(str(PATH))

for prim in stage.Traverse():
    print(prim.GetPath())

rack = stage.GetPrimAtPath("/Rack")

print(
    rack.GetAttribute(
        "aifactory:electrical:nominalPowerDrawW"
    ).Get()
)

rack = stage.GetPrimAtPath("/Rack")
body = stage.GetPrimAtPath("/Rack/Body")

print("Rack APIs:", rack.GetAppliedSchemas())
print("Body APIs:", body.GetAppliedSchemas())

print(
    "Mass:",
    rack.GetAttribute("physics:mass").Get()
)