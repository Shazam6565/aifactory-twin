from pathlib import Path
from evaluation import (
    build_evaluation,
    save_evaluation,
    save_evaluation_markdown,
)

ROOT = Path(__file__).resolve().parent

FIXTURES = {
    "valid": {
        "expected": {
            "structural": "PASS",
            "render": "PASS",
            "physics": "PASS",
            "domain": "PASS",
        }
    },
    "missing_mass": {
        "expected": {
            "physics": "FAIL",
        }
    },
    "missing_collider": {
        "expected": {
            "physics": "FAIL",
        }
    },
    "broken_material": {
        "expected": {
            "render": "FAIL",
        }
    },
    "invalid_domain": {
        "expected": {
            "domain": "FAIL",
        }
    },
}


def get_asset_path(name):
    return (
        ROOT
        / "examples"
        / "fixtures"
        / name
        / "scenes"
        / "rack_render.usda"
    )


def get_output_dir(name):
    return ROOT / "output" / "fixtures" / name


def run_fixture(name, config):
    asset_path = get_asset_path(name)
    output_dir = get_output_dir(name)

    evaluation = build_evaluation(
        asset_path,
        output_dir,
        require_runtime=False
    )

    save_evaluation(evaluation, output_dir)
    save_evaluation_markdown(evaluation, output_dir)

    expected = config["expected"]

    errors = []

    for category, expected_status in expected.items():
        actual_status = evaluation["categories"][category]["status"]

        if actual_status != expected_status:
            errors.append(
                f"{category}: expected {expected_status}, got {actual_status}"
            )

    return errors


def main():
    suite_failed = False

    for name, config in FIXTURES.items():
        errors = run_fixture(name, config)

        if errors:
            suite_failed = True
            print(f"{name:<20} FAIL")

            for error in errors:
                print(f"  - {error}")

        else:
            print(f"{name:<20} PASS")

    if suite_failed:
        raise SystemExit(1)

    print("\nFixture suite: PASS")


if __name__ == "__main__":
    main()
