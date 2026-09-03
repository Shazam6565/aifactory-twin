from pxr import Usd
from pathlib import Path



from rules import (
    rigidbody_has_mass,
    rigidbody_has_collider,
    all_renderables_bound,
    semantics_present,
    electrical_complete,
    thermal_complete,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
path = REPO_ROOT / "assets/published/components/rack_gb300/rack.usda"
stage = Usd.Stage.Open(str(path))


RULES = [
    ("rigidbody_has_mass", rigidbody_has_mass),
    ("rigidbody_has_collider", rigidbody_has_collider),
    ("all_renderables_bound", all_renderables_bound),
    ("semantics_present", semantics_present),
    ("electrical_complete", electrical_complete),
    ("thermal_complete", thermal_complete),
]


failed = False


for name, rule in RULES:

    errors = rule(stage)

    if errors:
        failed = True

        print(f"\nFAIL: {name}")

        for error in errors:
            print("  ", error)

    else:
        print(f"PASS: {name}")


raise SystemExit(1 if failed else 0)