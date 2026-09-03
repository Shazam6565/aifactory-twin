from pxr import Usd

path = "assets/published/components/rack_gb300/rack.usda"

stage = Usd.Stage.Open(
    path,
    load=Usd.Stage.LoadNone
)

rack = stage.GetPrimAtPath("/Rack")

print("Rack valid:", rack.IsValid())
print("Rack loaded:", rack.IsLoaded())

power = rack.GetAttribute(
    "aifactory:electrical:nominalPowerDrawW"
).Get()

print("Power draw:", power)