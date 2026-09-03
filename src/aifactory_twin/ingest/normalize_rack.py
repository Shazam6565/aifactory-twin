"""Normalize the vendor rack drop into a published proxy-box component.

Reads `assets/source/rack_raw.usda` and writes
`assets/published/components/rack_gb300/geo.usda` in project conventions:
metres, Z-up, origin-centred, no residual transform.

Per SCOPE.md, published components are dimensionally-plausible proxy boxes. So
this step reduces whatever the vendor shipped to its world bounding box and
re-authors that as a clean axis-aligned box. Going through the bounding box is
what lets the source carry arbitrary transforms without any of them leaking
into the output.

Nothing here guesses. If the source's declared units produce an implausible
rack, the numbers are reported as they are and the source is wrong.
"""

from pathlib import Path

from pxr import Gf, Usd, UsdGeom

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / "assets/source/rack_raw.usda"
PUBLISHED = REPO_ROOT / "assets/published/components/rack_gb300/geo.usda"

ASSET_NAME = "Rack"


def read_source(path: Path) -> dict:
    """Measure the source asset and report its declared conventions.

    Returns the asset's size in METRES, still in the source's own axis
    convention, plus everything needed to explain the conversion.
    """
    stage = Usd.Stage.Open(str(path))
    if not stage:
        raise RuntimeError(f"could not open source stage: {path}")

    meters_per_unit = UsdGeom.GetStageMetersPerUnit(stage)
    up_axis = UsdGeom.GetStageUpAxis(stage)

    # The source declares no defaultPrim, so fall back to the first root prim.
    # Setting one on the output is part of normalizing.
    prim = stage.GetDefaultPrim()
    if not prim:
        roots = [p for p in stage.GetPseudoRoot().GetChildren()]
        if not roots:
            raise RuntimeError(f"source stage has no root prims: {path}")
        prim = roots[0]

    bbox = UsdGeom.BBoxCache(
        Usd.TimeCode.Default(), [UsdGeom.Tokens.default_]
    ).ComputeWorldBound(prim)
    aligned = bbox.ComputeAlignedRange()

    size_units = aligned.GetSize()
    center_units = aligned.GetMidpoint()

    return {
        "source_prim": prim.GetPath().pathString,
        "meters_per_unit": meters_per_unit,
        "up_axis": up_axis,
        # Unit conversion happens here and only here.
        "size_m": Gf.Vec3d(size_units) * meters_per_unit,
        "center_m": Gf.Vec3d(center_units) * meters_per_unit,
    }


def to_z_up(size_m: Gf.Vec3d, up_axis: str) -> Gf.Vec3d:
    """Re-express an axis-aligned size vector in Z-up.

    Y-up to Z-up is a +90 degree rotation about X, which maps (x, y, z) to
    (x, -z, y). For an axis-aligned box that is exactly a swap of the Y and Z
    extents. Because we re-author the box rather than transform it, the
    rotation is baked and the output carries no orientation of its own.
    """
    if up_axis == UsdGeom.Tokens.z:
        return size_m
    if up_axis == UsdGeom.Tokens.y:
        return Gf.Vec3d(size_m[0], size_m[2], size_m[1])
    raise ValueError(f"unhandled upAxis: {up_axis!r}")


def author_proxy_box(size_m: Gf.Vec3d, out_path: Path) -> None:
    """Write the normalized component: metres, Z-up, origin-centred."""
    # In-memory then Export, so a partial failure leaves no file behind and a
    # re-run overwrites cleanly. Stage.CreateNew would truncate the target on
    # open, which makes a failed run look like an authoring bug.
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    rack = UsdGeom.Xform.Define(stage, f"/{ASSET_NAME}")
    body = UsdGeom.Cube.Define(stage, f"/{ASSET_NAME}/Body")

    # A unit cube scaled to the measured size. Extent is authored in LOCAL
    # space, so it tracks size and not scale; leaving it at the schema default
    # of +/-1 would declare a bounding box twice the real geometry.
    body.CreateSizeAttr(1.0)
    body.CreateExtentAttr([Gf.Vec3f(-0.5, -0.5, -0.5), Gf.Vec3f(0.5, 0.5, 0.5)])
    UsdGeom.XformCommonAPI(body).SetScale(Gf.Vec3f(size_m))

    stage.SetDefaultPrim(rack.GetPrim())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    stage.GetRootLayer().Export(str(out_path))


def main() -> None:
    src = read_source(SOURCE)
    size_z_up = to_z_up(src["size_m"], src["up_axis"])
    author_proxy_box(size_z_up, PUBLISHED)

    w, d, h = size_z_up[0], size_z_up[1], size_z_up[2]
    print(f"source     : {SOURCE.relative_to(REPO_ROOT)}  prim {src['source_prim']}")
    print(f"  declared : metersPerUnit={src['meters_per_unit']}  upAxis={src['up_axis']}")
    print(f"  measured : {tuple(round(v, 6) for v in src['size_m'])} m (source axes)")
    if src["center_m"] != Gf.Vec3d(0, 0, 0):
        print(f"  recentred: discarded offset {tuple(round(v, 6) for v in src['center_m'])} m")
    print(f"converted  : metersPerUnit=1.0  upAxis=Z")
    print(f"  W x D x H: {w:.4f} x {d:.4f} x {h:.4f} m")
    print(f"           : {w * 1000:.1f} x {d * 1000:.1f} x {h * 1000:.1f} mm")
    print(f"published  : {PUBLISHED.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
