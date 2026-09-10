from pxr import Usd, UsdGeom, UsdShade, UsdPhysics
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output" / "demo"

def get_category_status(checks):
    for check in checks:
        if check["status"] == "FAIL":
            return "FAIL"

    return "PASS"


def check_stage_opens(asset_path):
    try:
        stage = Usd.Stage.Open(str(asset_path))

        if stage is None:
            return {
                "name": "stage_opens",
                "status": "FAIL",
                "message": "USD stage could not be opened"
            }

        return {
            "name": "stage_opens",
            "status": "PASS",
            "message": "USD stage opened successfully"
        }

    except Exception as e:
        return {
            "name": "stage_opens",
            "status": "FAIL",
            "message": f"USD stage open failed: {e}"
        }

def check_default_prim(asset_path):
    try:
        stage = Usd.Stage.Open(str(asset_path))

        if stage is None:
            return {
                "name": "default_prim_present",
                "status": "FAIL",
                "message": "USD stage could not be opened"
            }

        default_prim = stage.GetDefaultPrim()

        if not default_prim or not default_prim.IsValid():
            return {
                "name": "default_prim_present",
                "status": "FAIL",
                "message": "USD stage does not define a valid defaultPrim"
            }

        return {
            "name": "default_prim_present",
            "status": "PASS",
            "message": f"defaultPrim is {default_prim.GetPath()}"
        }

    except Exception as e:
        return {
            "name": "default_prim_present",
            "status": "FAIL",
            "message": f"defaultPrim check failed: {e}"
        }

def check_composition_errors(asset_path):
    try:
        stage = Usd.Stage.Open(str(asset_path))

        if stage is None:
            return {
                "name": "composition_resolves",
                "status": "FAIL",
                "message": "USD stage could not be opened"
            }

        errors = stage.GetCompositionErrors()

        if errors:
            error_messages = [str(error) for error in errors]

            return {
                "name": "composition_resolves",
                "status": "FAIL",
                "message": "USD stage contains composition errors",
                "details": error_messages
            }

        return {
            "name": "composition_resolves",
            "status": "PASS",
            "message": "No USD composition errors detected"
        }

    except Exception as e:
        return {
            "name": "composition_resolves",
            "status": "FAIL",
            "message": f"Composition check failed: {e}"
        }


def check_ovrtx_execution(output_dir):
    summary_path = output_dir / "summary.json"

    if not summary_path.exists():
        return {
            "name": "ovrtx_execution",
            "status": "FAIL",
            "message": "Demo summary.json was not found",
            "artifact": str(summary_path)
        }

    try:
        with open(summary_path, "r") as f:
            summary = json.load(f)

        if summary.get("ovrtx") != "PASS":
            return {
                "name": "ovrtx_execution",
                "status": "FAIL",
                "message": "Demo workflow did not report OVRTX as PASS"
            }

        return {
            "name": "ovrtx_execution",
            "status": "PASS",
            "message": "Demo workflow reported successful OVRTX execution"
        }

    except Exception as e:
        return {
            "name": "ovrtx_execution",
            "status": "FAIL",
            "message": f"Could not read demo summary: {e}"
        }


def check_render_output(output_dir):
    render_path = output_dir / "render.png"

    if not render_path.exists():
        return {
            "name": "render_output_exists",
            "status": "FAIL",
            "message": "OVRTX render output was not found",
            "artifact": str(render_path)
        }

    if render_path.stat().st_size == 0:
        return {
            "name": "render_output_exists",
            "status": "FAIL",
            "message": "OVRTX render output exists but is empty",
            "artifact": str(render_path)
        }

    return {
        "name": "render_output_exists",
        "status": "PASS",
        "message": "OVRTX produced a non-empty render output",
        "artifact": str(render_path)
    }


def check_ovphysx_execution(output_dir):
    summary_path = output_dir / "summary.json"

    if not summary_path.exists():
        return {
            "name": "ovphysx_execution",
            "status": "FAIL",
            "message": "Demo summary.json was not found",
            "artifact": str(summary_path)
        }

    try:
        with open(summary_path, "r") as f:
            summary = json.load(f)

        if summary.get("ovphysx") != "PASS":
            return {
                "name": "ovphysx_execution",
                "status": "FAIL",
                "message": "Demo workflow did not report OVPhysX as PASS"
            }

        return {
            "name": "ovphysx_execution",
            "status": "PASS",
            "message": "Demo workflow reported successful OVPhysX execution"
        }

    except Exception as e:
        return {
            "name": "ovphysx_execution",
            "status": "FAIL",
            "message": f"Could not read demo summary: {e}"
        }



def check_physics_output_exists(output_dir):
    physics_path = output_dir / "physics_results.json"

    if not physics_path.exists():
        return {
            "name": "physics_output_exists",
            "status": "FAIL",
            "message": "physics_results.json was not found",
            "artifact": str(physics_path)
        }

    if physics_path.stat().st_size == 0:
        return {
            "name": "physics_output_exists",
            "status": "FAIL",
            "message": "physics_results.json exists but is empty",
            "artifact": str(physics_path)
        }

    return {
        "name": "physics_output_exists",
        "status": "PASS",
        "message": "Physics result artifact was produced",
        "artifact": str(physics_path)
    }


def check_pose_changed(output_dir):
    physics_path = output_dir / "physics_results.json"

    if not physics_path.exists():
        return {
            "name": "pose_changed",
            "status": "FAIL",
            "message": "Cannot evaluate pose change because physics_results.json is missing"
        }

    try:
        with open(physics_path, "r") as f:
            results = json.load(f)

        if results.get("pose_changed") is not True:
            return {
                "name": "pose_changed",
                "status": "FAIL",
                "message": "Simulation ran but no expected rigid-body pose change was observed"
            }

        return {
            "name": "pose_changed",
            "status": "PASS",
            "message": "Rigid-body pose changed after OVPhysX simulation"
        }

    except Exception as e:
        return {
            "name": "pose_changed",
            "status": "FAIL",
            "message": f"Could not evaluate pose change: {e}"
        }


def check_rigidbody_mass(asset_path, prim_path):
    try:
        stage, prim = get_prim(asset_path, prim_path)

        if prim is None:
            return {
                "name": "rigidbody_has_mass",
                "status": "FAIL",
                "message": f"Could not find prim {prim_path}",
                "prim_path": prim_path
            }

        mass_attr = prim.GetAttribute("physics:mass")
        value = mass_attr.Get() if mass_attr and mass_attr.IsValid() else None

        if value is None or value <= 0:
            return {
                "name": "rigidbody_has_mass",
                "status": "FAIL",
                "message": f"Rigid body does not have a valid mass: {value}",
                "prim_path": prim_path
            }

        return {
            "name": "rigidbody_has_mass",
            "status": "PASS",
            "message": f"Rigid body mass is {value}",
            "prim_path": prim_path
        }

    except Exception as e:
        return {
            "name": "rigidbody_has_mass",
            "status": "FAIL",
            "message": f"Mass check failed: {e}",
            "prim_path": prim_path
        }


def check_rigidbody_collider(asset_path, prim_path):
    try:
        stage, prim = get_prim(asset_path, prim_path)

        if prim is None:
            return {
                "name": "rigidbody_has_collider",
                "status": "FAIL",
                "message": f"Could not find prim {prim_path}",
                "prim_path": prim_path
            }

        has_collider = any(
            descendant.HasAPI(UsdPhysics.CollisionAPI)
            for descendant in Usd.PrimRange(prim)
        )

        if not has_collider:
            return {
                "name": "rigidbody_has_collider",
                "status": "FAIL",
                "message": "Rigid body has no collider",
                "prim_path": prim_path
            }

        return {
            "name": "rigidbody_has_collider",
            "status": "PASS",
            "message": "Rigid body has a collider",
            "prim_path": prim_path
        }

    except Exception as e:
        return {
            "name": "rigidbody_has_collider",
            "status": "FAIL",
            "message": f"Collider check failed: {e}",
            "prim_path": prim_path
        }



def check_material_bindings(asset_path):
    try:
        stage = Usd.Stage.Open(str(asset_path))

        if stage is None:
            return {
                "name": "material_bindings_resolve",
                "status": "FAIL",
                "message": "Could not open USD stage"
            }

        unbound_meshes = []

        for prim in stage.Traverse():
            if not prim.IsA(UsdGeom.Gprim):
                continue

            binding_api = UsdShade.MaterialBindingAPI(prim)
            material, _ = binding_api.ComputeBoundMaterial()

            if not material or not material.GetPrim().IsValid():
                unbound_meshes.append(str(prim.GetPath()))

        if unbound_meshes:
            return {
                "name": "material_bindings_resolve",
                "status": "FAIL",
                "message": "One or more renderable meshes have no resolved material binding",
                "details": unbound_meshes
            }

        return {
            "name": "material_bindings_resolve",
            "status": "PASS",
            "message": "All renderable meshes have resolved material bindings"
        }

    except Exception as e:
        return {
            "name": "material_bindings_resolve",
            "status": "FAIL",
            "message": f"Material binding check failed: {e}"
        }

def get_prim(asset_path, prim_path):
    # The returned prim is only valid while its stage is alive, so the caller
    # must hold on to the stage for as long as it uses the prim.
    stage = Usd.Stage.Open(str(asset_path))

    if stage is None:
        return None, None

    prim = stage.GetPrimAtPath(prim_path)

    if not prim or not prim.IsValid():
        return stage, None

    return stage, prim

def check_nominal_power(asset_path, prim_path):
    try:
        stage, prim = get_prim(asset_path, prim_path)

        if prim is None:
            return {
                "name": "nominal_power_present",
                "status": "FAIL",
                "message": f"Could not find prim {prim_path}",
                "prim_path": prim_path
            }

        attr = prim.GetAttribute(
            "aifactory:electrical:nominalPowerDrawW"
        )

        if not attr or not attr.IsValid():
            return {
                "name": "nominal_power_present",
                "status": "FAIL",
                "message": "Nominal power draw attribute is missing",
                "prim_path": prim_path
            }

        value = attr.Get()

        if value is None or value <= 0:
            return {
                "name": "nominal_power_present",
                "status": "FAIL",
                "message": f"Nominal power draw is invalid: {value}",
                "prim_path": prim_path
            }

        return {
            "name": "nominal_power_present",
            "status": "PASS",
            "message": f"Nominal power draw is {value} W",
            "prim_path": prim_path
        }

    except Exception as e:
        return {
            "name": "nominal_power_present",
            "status": "FAIL",
            "message": f"Power metadata check failed: {e}",
            "prim_path": prim_path
        }

def check_cooling_type(asset_path, prim_path):
    try:
        stage, prim = get_prim(asset_path, prim_path)

        if prim is None:
            return {
                "name": "cooling_type_present",
                "status": "FAIL",
                "message": f"Could not find prim {prim_path}",
                "prim_path": prim_path
            }

        attr = prim.GetAttribute(
            "aifactory:thermal:coolingType"
        )

        if not attr or not attr.IsValid():
            return {
                "name": "cooling_type_present",
                "status": "FAIL",
                "message": "Cooling type attribute is missing",
                "prim_path": prim_path
            }

        value = attr.Get()

        if not value:
            return {
                "name": "cooling_type_present",
                "status": "FAIL",
                "message": "Cooling type is empty",
                "prim_path": prim_path
            }

        return {
            "name": "cooling_type_present",
            "status": "PASS",
            "message": f"Cooling type is {value}",
            "prim_path": prim_path
        }

    except Exception as e:
        return {
            "name": "cooling_type_present",
            "status": "FAIL",
            "message": f"Cooling metadata check failed: {e}",
            "prim_path": prim_path
        }


    
def build_evaluation(asset_path, output_dir, require_runtime=True):
    rack_prim_path = "/World/Rack"
    structural_checks = [
        check_stage_opens(asset_path),
        check_default_prim(asset_path),
        check_composition_errors(asset_path)
    ]

    # material_bindings_resolve is a static asset check — it always runs.
    # ovrtx_execution / render_output_exists are runtime smoke tests: did the
    # real consumer actually execute. Those only apply when evaluating a
    # real demo.py run, not when evaluating a fixture in isolation.
    render_checks = [check_material_bindings(asset_path)]
    if require_runtime:
        render_checks = [
            check_ovrtx_execution(output_dir),
            check_render_output(output_dir),
        ] + render_checks

    # rigidbody_has_mass / rigidbody_has_collider are static asset checks —
    # they always run. ovphysx_execution / physics_output_exists /
    # pose_changed are runtime smoke tests, same reasoning as above.
    physics_checks = [
        check_rigidbody_mass(asset_path, rack_prim_path),
        check_rigidbody_collider(asset_path, rack_prim_path),
    ]
    if require_runtime:
        physics_checks = [
            check_ovphysx_execution(output_dir),
            check_physics_output_exists(output_dir),
            check_pose_changed(output_dir),
        ] + physics_checks

    domain_checks = [
        check_nominal_power(asset_path, rack_prim_path),
        check_cooling_type(asset_path, rack_prim_path)
    ]

    categories = {
        "structural": {
            "status": get_category_status(structural_checks),
            "checks": structural_checks
        },
        "render": {
            "status": get_category_status(render_checks),
            "checks": render_checks
        },
        "physics": {
            "status": get_category_status(physics_checks),
            "checks": physics_checks
        },
        "domain": {
            "status": get_category_status(domain_checks),
            "checks": domain_checks
        }
    }

    overall_status = "PASS"
    for category in categories.values():
        if category["status"] == "FAIL":
            overall_status = "FAIL"
            break

    evaluation = {
        "asset": asset_path.name,
        "overall_status": overall_status,
        "categories": categories
    }

    return evaluation


def save_evaluation(evaluation, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "evaluation.json"

    with open(output_file, "w") as f:
        json.dump(evaluation, f, indent=2)

    print(f"Evaluation written to: {output_file}")


def save_evaluation_markdown(evaluation, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# SimReady POC Evaluation")
    lines.append("")
    lines.append(f"**Asset:** `{evaluation['asset']}`")
    lines.append("")
    lines.append(f"**Overall Result:** {evaluation['overall_status']}")
    lines.append("")

    for category_name, category in evaluation["categories"].items():
        lines.append(f"## {category_name.title()} — {category['status']}")
        lines.append("")

        for check in category["checks"]:
            line = f"- {check['status']} — {check['name']}: {check['message']}"

            if "prim_path" in check:
                line += f" (`{check['prim_path']}`)"

            if "artifact" in check:
                line += f" — artifact: `{check['artifact']}`"

            lines.append(line)

        lines.append("")

    lines.append("## Conclusion")
    lines.append("")

    if evaluation["overall_status"] == "PASS":
        lines.append(
            "The asset satisfied all blocking POC evaluation categories."
        )
    else:
        lines.append(
            "The asset did not satisfy all blocking POC evaluation categories."
        )
    lines.append("")

    output_file = output_dir / "evaluation.md"

    with open(output_file, "w") as f:
        f.write("\n".join(lines))

    print(f"Markdown evaluation written to: {output_file}")


if __name__ == "__main__":
    asset_path = Path(sys.argv[1])
    output_dir = OUTPUT_DIR

    result = build_evaluation(asset_path, output_dir)

    save_evaluation(result, output_dir)
    save_evaluation_markdown(result, output_dir)