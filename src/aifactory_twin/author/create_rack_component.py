"""Author the interface layer for the rack component.

The interface layer is the component's front door: it defines the asset-root
prim and attaches geometry as a PAYLOAD, so consumers reference one file and
geometry stays load-gated. See ARCHITECTURE.md section 3.

Paths are derived from this file, never from the working directory. USD
resolves an asset path like @./geo.usda@ relative to the LAYER that authors it,
so if the layer lands somewhere unexpected the payload silently fails to
resolve — and a relative output path resolved against the CWD is exactly how a
layer lands somewhere unexpected.
"""

from pathlib import Path

from pxr import Usd, UsdGeom

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPONENT_DIR = REPO_ROOT / "assets/published/components/rack_gb300"
INTERFACE = COMPONENT_DIR / "rack.usda"

ASSET_NAME = "Rack"
GEOMETRY = "./geo.usda"


def author_interface_layer(out_path: Path, geometry: str) -> None:
    """Define the asset root and attach geometry as a payload."""
    # Fail before touching the output. USD reports an unresolved payload as a
    # warning and composes an empty prim, which is easy to miss; a missing
    # geometry file should stop the run and say where it looked.
    target = (out_path.parent / geometry).resolve()
    if not target.is_file():
        raise SystemExit(
            f"payload target not found: {target}\n"
            f"  {geometry!r} resolves relative to the layer that authors it,\n"
            f"  which is {out_path.parent}"
        )

    # Author at the real location rather than in memory. An anonymous layer has
    # no filesystem anchor, so a relative payload cannot resolve while authoring
    # and USD warns on every recompose. Authoring in place also means an
    # unresolvable payload surfaces immediately, not after export.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(out_path))
    rack = UsdGeom.Xform.Define(stage, f"/{ASSET_NAME}")

    # Payload, not sublayer. Geometry is the heaviest data and the thing most
    # often not needed, and it is the single line that changes when the vendor
    # ships a new revision. ADR-02.
    stage.GetRootLayer().subLayerPaths = [
        "domain.usda",
        "physics.usda",
        "material.usda",
    ]
    rack.GetPrim().GetPayloads().AddPayload(geometry)
    

    stage.SetDefaultPrim(rack.GetPrim())
    stage.GetRootLayer().Save()


def verify(out_path: Path) -> None:
    """Open the layer and confirm the payload actually resolves.

    Authoring a payload always 'works'. Resolving one is a separate question,
    and an unresolved payload composes to an empty prim rather than an error.
    """
    unloaded = Usd.Stage.Open(str(out_path), Usd.Stage.LoadNone)
    n_unloaded = len(list(unloaded.Traverse()))

    loaded = Usd.Stage.Open(str(out_path), Usd.Stage.LoadAll)
    n_loaded = len(list(loaded.Traverse()))

    print(f"published : {out_path.relative_to(REPO_ROOT)}")
    print(f"  payload : {GEOMETRY}")
    print(f"  prims   : {n_unloaded} unloaded -> {n_loaded} loaded")

    if n_loaded <= n_unloaded:
        raise SystemExit(
            f"payload did not resolve: {GEOMETRY} is not readable from "
            f"{out_path.parent}. Loading it added no prims."
        )
    print("  payload resolves, and defers when unloaded")


def main() -> None:
    author_interface_layer(INTERFACE, GEOMETRY)
    verify(INTERFACE)


if __name__ == "__main__":
    main()


