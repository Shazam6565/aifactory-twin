from pathlib import Path

from pxr import Usd, Sdf

REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT_PATH = REPO_ROOT / "assets/published/components/rack_gb300/domain.usda"

stage = Usd.Stage.CreateNew(str(OUTPUT_PATH))

rack = stage.OverridePrim("/Rack")

power_attr = rack.CreateAttribute(
    "aifactory:electrical:nominalPowerDrawW",
    Sdf.ValueTypeNames.Float
)

power_attr.Set(132000.0)

semantic_attr = rack.CreateAttribute(
    "aifactory:semantic:class",
    Sdf.ValueTypeNames.Token
)

semantic_attr.Set("compute_rack")

phase_attr = rack.CreateAttribute(
    "aifactory:electrical:phase",
    Sdf.ValueTypeNames.Token
)

phase_attr.Set("3P")

heat_attr = rack.CreateAttribute(
    "aifactory:thermal:heatOutputW",
    Sdf.ValueTypeNames.Float
)

heat_attr.Set(120000.0)

cooling_attr = rack.CreateAttribute(
    "aifactory:thermal:coolingType",
    Sdf.ValueTypeNames.Token
)

cooling_attr.Set("liquid")


stage.GetRootLayer().Save()
