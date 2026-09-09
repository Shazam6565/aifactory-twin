from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output" / "demo"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def run_validation():
    print("\n[1/3] Validating asset...", flush=True)

    result = subprocess.run(
        [
            sys.executable,
            "src/aifactory_twin/validate/run.py",
        ],
        cwd=ROOT,
    )

    if result.returncode != 0:
        raise RuntimeError("Validation failed")

    print("Validation PASS", flush=True)

def run_ovrtx():
    print("\n[2/3] Running OVRTX render...", flush=True)

    consumer = ROOT / "src" / "aifactory_twin" / "consume" / "render_ovrtx.py"
    # render_ovrtx.py writes to _output/render.png, relative to its cwd, when
    # passed --png. Run it from ROOT and relocate that file into OUTPUT_DIR
    # so the demo's artifact path is predictable regardless of where the
    # consumer script decides to write.
    scratch_render = ROOT / "_output" / "render.png"
    render_path = OUTPUT_DIR / "render.png"

    subprocess.run(
        [
            sys.executable,
            str(consumer),
            "--png",
        ],
        cwd=ROOT,
        check=True,
    )

    if not scratch_render.exists():
        raise RuntimeError(f"OVRTX did not produce {scratch_render}")

    scratch_render.replace(render_path)
    try:
        scratch_render.parent.rmdir()
    except OSError:
        pass

    print(f"Render written to {render_path}", flush=True)
    print("OVRTX PASS", flush=True)

def run_ovphysx():
    print("\n[3/3] Running OVPhysX simulation...", flush=True)

    subprocess.run(
        [
            sys.executable,
            "src/aifactory_twin/consume/physics_ovphysx.py",
        ],
        cwd=ROOT,
        check=True,
    )

    results_path = OUTPUT_DIR / "physics_results.json"
    if not results_path.exists():
        raise RuntimeError(f"OVPhysX did not produce {results_path}")

    with open(results_path) as f:
        results = json.load(f)

    before_z = results["before"]["z"]
    after_z = results["after"]["z"]
    print(
        f"Z before: {before_z:.3f} -> after: {after_z:.3f} "
        f"(pose_changed={results['pose_changed']})",
        flush=True,
    )

    print("OVPhysX PASS", flush=True)

def main():
    print("=== SimReady POC Demo ===", flush=True)
    print(f"Output directory: {OUTPUT_DIR}", flush=True)

    run_validation()
    run_ovrtx()
    run_ovphysx()

    print("\n=== POC RESULT: PASS ===", flush=True)


if __name__ == "__main__":
    main()