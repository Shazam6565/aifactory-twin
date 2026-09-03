from pxr import Usd

path = "assets/published/components/rack_gb300/rack.usda"

stage = Usd.Stage.Open(
    path,
    load=Usd.Stage.LoadNone
)

rack = stage.GetPrimAtPath("/Rack")

print("Rack exists:", rack.IsValid())
print("Has payload:", rack.HasPayload())
print("Payload loaded:", rack.IsLoaded())

stage.Load("/Rack")

rack = stage.GetPrimAtPath("/Rack")

print("\nAfter loading:")
print("Payload loaded:", rack.IsLoaded())

for prim in stage.Traverse():
    print(prim.GetPath())