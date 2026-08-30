# Getting started — follow along, steps 1 to 10

Build the pipeline yourself, in ten steps covering M1, M3 and M5. Exact commands, the files to
create, the signatures to fill in, and a verification you can run before moving on.

**Function bodies are deliberately left to you.** Signatures and docstrings are given so you
never have to guess the shape; the logic inside is the part that becomes the thing you can talk
about. If you paste your way through this, the project has failed at its only real purpose.

---

## Progress

- [ ] 1 · Environment
- [ ] 2 · Repo skeleton
- [ ] 3 · `SIMREADY_SPEC.md`
- [ ] 4 · Source assets
- [ ] 5 · Ingest + normalize · **M1**
- [ ] 6 · Layer split ⭐
- [ ] 7 · `physics.usda` · **M3**
- [ ] 8 · `mtl.usda` + semantics · **M3**
- [ ] 9 · Domain layers ⭐ · **M3**
- [ ] 10 · Validation + gate ⭐ · **M5**

Commit after each. Flip the README status table only when a milestone genuinely runs.

---

## Step 1 · Environment

```bash
uv init --package --name aifactory-twin .
uv add usd-core numpy
uv add --dev pytest
```

If `uv init` objects to the directory not being empty, `uv init` without `.` and merge, or hand-write
`pyproject.toml` — either is fine. Then **pin the USD version** you got, so M7 is reproducible:

```toml
dependencies = ["usd-core==<the version you got>", "numpy"]
```

**Verify — and write the output into `NOTES.md`:**

```bash
uv run python - <<'PY'
from importlib.metadata import version
print("usd-core:", version("usd-core"))
from pxr import Usd, UsdGeom, UsdShade, UsdPhysics, UsdUtils, Sdf, Tf
print("core modules: OK")
print("ComplianceChecker:", hasattr(UsdUtils, "ComplianceChecker"))
for mod in ("UsdSemantics", "PhysxSchema"):
    try:
        __import__("pxr." + mod); print(mod + ": available")
    except ImportError:
        print(mod + ": NOT available")
PY
```

`PhysxSchema: NOT available` is **expected and correct** on `usd-core` — it is an NVIDIA
extension, not core USD. Note which semantics module you have; step 8 depends on it.

Then read `help(UsdUtils.ComplianceChecker)` and note its real signature. You call it at step 10.

- [ ] all core modules import
- [ ] USD version pinned in `pyproject.toml` and written in `NOTES.md`
- [ ] semantics module identified

---

## Step 2 · Repo skeleton

```bash
mkdir -p src/aifactory_twin/{ingest,author,optimize,validate,consume} \
         assets/source assets/published/{components,scenes} \
         tests/fixtures ci tools

for d in ingest author optimize validate consume; do
  touch "src/aifactory_twin/$d/__init__.py"
done

echo "Vendor drops. NEVER edited in place. Regenerate published assets instead." \
  > assets/source/README.md
echo "Pipeline output. NEVER hand-edited. Produced by src/aifactory_twin/." \
  > assets/published/README.md
```

**Verify:**

```bash
uv run python -c "import aifactory_twin; print('package OK')"
git add -A && git commit -m "Step 2: repo skeleton"
```

- [ ] package imports
- [ ] guard READMEs sit where the violation would happen

---

## Step 3 · `SIMREADY_SPEC.md`

No code. Create `SIMREADY_SPEC.md` with one table, and fill every row before writing any
validator.

| ID | Rule | Rationale — what breaks downstream | Severity | Payload needed |
|---|---|---|---|---|
| SR-STRUCT-001 | `metersPerUnit == 1.0` and `upAxis == Z` | Mixed units silently corrupt every physics and electrical figure | error | no |
| SR-PHYS-001 | Any `RigidBodyAPI` prim has mass > 0 | Zero-mass rigid bodies explode or fall through the floor in PhysX | error | no |
| SR-DOMAIN-001 | Powered equipment declares draw and phase | Power budget cannot be computed; the twin cannot answer its main question | error | no |
| … | | | | |

Then a second section fixing the **numbers**, each with its provenance:

| Quantity | Value | Where it came from |
|---|---|---|
| Rack nominal draw | | public spec sheet / chosen as representative |
| PDU capacity | | |
| Rack heat output | | |
| Mesh-collider triangle threshold | | |

The *Payload needed* column is the one that matters most — it is what splits the fast domain
gate from the full structural gate at step 10.

- [ ] every rule has an ID, a rationale, a severity and a payload flag
- [ ] every number has a stated source, including "chosen as representative"

---

## Step 4 · Source assets

Create `tools/make_source_assets.py`. **Not** under `src/` — it stands in for a vendor and is
not part of the pipeline.

```python
"""One-shot generator standing in for vendor CAD. Run once; commit the output;
never run it again. See ARCHITECTURE.md ADR-08."""

def make_rack(out_path: str) -> None:
    """Emit a rack at representative dimensions as simple box geometry.

    Deliberately imperfect, so that ingest has real work to do:
      - author it Y-up (the wrong convention) so normalize must rotate it
      - leave a non-identity transform on the root xform
      - use a prim name that is not a valid USD identifier
    """

def make_cdu(out_path: str) -> None: ...
def make_pdu(out_path: str) -> None: ...
def make_floor_tile(out_path: str) -> None: ...
```

Then bring in the real robot — it is not generated:

```bash
cp -R "$HOME/Desktop/Projects/gits/isaac-sim-workspace/carter 2" assets/source/robot
```

**Verify:**

```bash
uv run python tools/make_source_assets.py
uv run python -c "
from pxr import Usd, UsdGeom
s = Usd.Stage.Open('assets/source/rack_gb300.usda')
print('upAxis:', UsdGeom.GetStageUpAxis(s))
print('metersPerUnit:', UsdGeom.GetStageMetersPerUnit(s))
print('prims:', [p.GetPath() for p in s.Traverse()])
"
git add -A && git commit -m "Step 4: source assets (vendor stand-in), frozen from here"
```

You want that to print the **wrong** up-axis. That is the point.

- [ ] four components generated, at least two deliberately flawed
- [ ] robot URDF + meshes copied in
- [ ] committed, and never touched again

---

## Step 5 · Ingest + normalize — **M1**

`src/aifactory_twin/ingest/normalize.py`:

```python
def normalize_stage(stage) -> dict:
    """Force project conventions onto a source stage, in place.

    - set upAxis Z and metersPerUnit 1.0, converting geometry if the source disagrees
      (rotate the geometry AND re-author the metadata; doing only one is the classic bug)
    - rename prims to deterministic, valid identifiers (check with Tf.IsValidIdentifier)
    - bake root transforms into geometry so the component sits at origin
    - set defaultPrim on the output layer

    Returns a record of what was changed, for the manifest and the log.
    """

def ingest(source_path: str, out_dir: str) -> dict:
    """Normalize one source asset into a published component directory.

    Returns the manifest entry: source path, source sha256, output path,
    usd version, pipeline version, utc timestamp.
    """
```

`src/aifactory_twin/ingest/__main__.py` so `python -m aifactory_twin.ingest <path>` works.

**Verify — determinism is the check that matters:**

```bash
uv run python -m aifactory_twin.ingest assets/source/rack_gb300.usda
cp -R assets/published/components/rack_gb300 /tmp/run1
uv run python -m aifactory_twin.ingest assets/source/rack_gb300.usda
diff -r /tmp/run1 assets/published/components/rack_gb300 && echo "DETERMINISTIC ✓"
```

If that diff is non-empty, find out why before continuing — it is almost always unsorted
iteration or an embedded timestamp, and it gets much harder to unpick later.

- [ ] up-axis and units corrected, not merely flagged
- [ ] `defaultPrim` set
- [ ] `manifest.json` written with source sha256
- [ ] two consecutive runs byte-identical

---

## Step 6 · Layer split ⭐

Target on disk:

```
assets/published/components/rack_gb300/
  rack_gb300.usda          interface layer — defs the asset root, payloads geo, sublayers the rest
  geo.usdc                 binary geometry, own defaultPrim
  mtl.usda                 empty for now (needs the #usda 1.0 header)
  physics.usda             empty for now
  domain_electrical.usda   empty for now
```

`src/aifactory_twin/author/simready.py`:

```python
def split_into_layers(component_dir: str, asset_name: str) -> None:
    """Write the per-component layer stack described in ARCHITECTURE.md section 3.

    - geometry to geo.usdc with its own defaultPrim
    - interface layer defs the asset-root prim and attaches geometry as a PAYLOAD:
          prim.GetPayloads().AddPayload("./geo.usdc")
    - mtl / physics / domain_electrical created empty and wired as subLayers

    subLayers ordering: FIRST entry is STRONGEST. Build the list in the documented
    order and assign it, or use insert(0, ...). Do NOT reach for .append() and expect
    strongest — that silently gives you the exact reverse of the documented stack.
    Layers created with Sdf.Layer.CreateNew are not written until you Save() them.
    """
```

**Verify — this is the property everything else rests on:**

```bash
uv run python - <<'PY'
from pxr import Usd
p = "assets/published/components/rack_gb300/rack_gb300.usda"

s = Usd.Stage.Open(p, Usd.Stage.LoadNone)
unloaded = [str(x.GetPath()) for x in s.Traverse()]
print("unloaded:", len(unloaded), unloaded[:5])

s.Load("/rack_gb300")
loaded = [str(x.GetPath()) for x in s.Traverse()]
print("loaded:  ", len(loaded), loaded[:5])

assert len(loaded) > len(unloaded), "payload is not deferring — geometry is composing anyway"
print("PAYLOAD DEFERS ✓")
PY
```

Then confirm the sublayer order really is what you documented:

```bash
uv run python -c "
from pxr import Sdf
l = Sdf.Layer.FindOrOpen('assets/published/components/rack_gb300/rack_gb300.usda')
print('strongest first:', list(l.subLayerPaths))
"
```

Move the payload assertion into `tests/test_composition.py` now, while it is fresh. It is the
test most likely to catch a real regression later.

- [ ] payload defers, proven by the assertion
- [ ] sublayer order matches `ARCHITECTURE.md` §3, verified by printing it
- [ ] `usdcat --flatten` shows the composed result
- [ ] test committed

---

## Step 7 · `physics.usda` — **M3**

The new idea in this step is the **edit target**: opinions must land in the physics layer, not
the interface layer.

```python
from pxr import Usd, Sdf, UsdPhysics

def author_physics(stage, layer_path: str, asset_root: str, mass_kg: float) -> None:
    """Author physics into physics.usda specifically.

    layer = Sdf.Layer.FindOrOpen(layer_path)
    with Usd.EditContext(stage, Usd.EditTarget(layer)):
        ...   # everything authored in here lands in physics.usda

    On the ASSET ROOT (readable with geometry unloaded, per ADR-05):
        UsdPhysics.RigidBodyAPI.Apply, UsdPhysics.MassAPI.Apply + CreateMassAttr
    On MESH DESCENDANTS (requires the payload loaded):
        UsdPhysics.CollisionAPI.Apply, UsdPhysics.MeshCollisionAPI.Apply
        + CreateApproximationAttr("convexHull")
    """
```

**Verify — did the opinions land in the right file?**

```bash
grep -c "RigidBodyAPI\|physics:mass" assets/published/components/rack_gb300/physics.usda
grep -c "RigidBodyAPI\|physics:mass" assets/published/components/rack_gb300/rack_gb300.usda
```

First should be non-zero, **second must be zero**. If physics opinions appear in the interface
layer, the edit target was not applied and the architecture has quietly collapsed into one file.

Then confirm mass survives with geometry unloaded:

```bash
uv run python -c "
from pxr import Usd, UsdPhysics
s = Usd.Stage.Open('assets/published/components/rack_gb300/rack_gb300.usda', Usd.Stage.LoadNone)
m = UsdPhysics.MassAPI(s.GetPrimAtPath('/rack_gb300'))
print('mass with payload unloaded:', m.GetMassAttr().Get())
"
```

- [ ] physics opinions in `physics.usda` only
- [ ] mass readable unloaded
- [ ] colliders on descendants with an approximation set

---

## Step 8 · `mtl.usda` + semantics — **M3**

```python
def author_materials(stage, layer_path: str, asset_root: str) -> None:
    """UsdShade.Material + UsdPreviewSurface shader, bound via UsdShade.MaterialBindingAPI.
    Edit-target into mtl.usda, same pattern as step 7."""

def author_semantics(stage, layer_path: str, asset_root: str, class_label: str) -> None:
    """Apply the semantics schema identified in step 1 to the asset root.
    Without labels there is no SDG ground truth and the sensor story is empty."""
```

Also set `purpose` on collision-only meshes to `guide` or `proxy`, so they are not counted as
renderable at step 10.

**Verify — bindings must *resolve*, not merely exist:**

```bash
uv run python - <<'PY'
from pxr import Usd, UsdShade, UsdGeom
s = Usd.Stage.Open("assets/published/components/rack_gb300/rack_gb300.usda")
for prim in s.Traverse():
    if prim.IsA(UsdGeom.Mesh) and UsdGeom.Imageable(prim).ComputePurpose() == UsdGeom.Tokens.default_:
        mat, _ = UsdShade.MaterialBindingAPI(prim).ComputeBoundMaterial()
        print(prim.GetPath(), "->", mat.GetPath() if mat else "UNBOUND")
PY
```

Every renderable mesh must print a material path, not `UNBOUND`.

- [ ] every renderable mesh resolves to a material
- [ ] asset root carries a semantic class label
- [ ] collision-only meshes marked non-renderable

---

## Step 9 · Domain layers ⭐ — **M3**

```python
def author_electrical(stage, layer_path: str, asset_root: str,
                      power_w: float, phase: str) -> None:
    """Namespaced custom attributes on the ASSET ROOT (ADR-05, ADR-09):
        aifactory:electrical:nominalPowerDrawW   Sdf.ValueTypeNames.Float
        aifactory:electrical:phase               Sdf.ValueTypeNames.Token
    Values come from SIMREADY_SPEC.md. Set the value type explicitly and correctly —
    Float and Token are not interchangeable and the mistake surfaces much later."""

def author_thermal(stage, layer_path: str, asset_root: str,
                   heat_w: float, cooling: str) -> None:
    """Same, into a separate domain_thermal.usda. Two domains, two vendors, two layers."""
```

**Verify — and this is the demo, so record the numbers:**

```bash
uv run python - <<'PY'
import time
from pxr import Usd

p = "assets/published/components/rack_gb300/rack_gb300.usda"

for mode, load in (("unloaded", Usd.Stage.LoadNone), ("loaded", Usd.Stage.LoadAll)):
    t0 = time.perf_counter()
    s = Usd.Stage.Open(p, load)
    a = s.GetPrimAtPath("/rack_gb300").GetAttribute("aifactory:electrical:nominalPowerDrawW")
    val = a.Get()
    print(f"{mode:9s} draw={val}W  open+query={(time.perf_counter()-t0)*1000:.2f}ms")
PY
```

Both must return the same value. Put both timings in `NOTES.md` — that ratio is the measured
return on the payload decision, and a number is worth a paragraph of explanation.

- [ ] electrical and thermal in separate layers, on the asset root
- [ ] value read correctly with geometry unloaded
- [ ] both timings recorded

---

## Step 10 · Validation + the gate ⭐ — **M5**

`src/aifactory_twin/validate/rules.py` — keep the interface small enough that a domain expert
who is not a USD expert could add a rule:

```python
@dataclass
class Failure:
    rule_id: str
    prim_path: str
    message: str      # say what to DO, not just what is wrong
    severity: str     # "error" | "warning"

class Rule:
    id: str
    needs_payload: bool          # from the SIMREADY_SPEC.md column
    def check(self, stage) -> list[Failure]: ...
```

Implement six first, spanning the categories rather than the easy ones: `valid_units`,
`no_default_prim_missing`, `rigidbody_has_mass`, `all_meshes_bound`, `semantics_present`,
`electrical_complete`. Then `power_budget_consistent` — partial at component scope, completed
at M4.

`validate/runner.py` runs `UsdUtils.ComplianceChecker` for structure, then the rules — **in two
passes**: `needs_payload=False` rules against a `LoadNone` stage, the rest against a loaded one.
Report both timings.

Per ADR-11, the runner takes **any** stage path and must not assume this repo's layout.
Convention-dependent values (up-axis, the `aifactory:` namespace) are parameters with our
values as defaults, not constants.

`ci/validate.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
STAGE="${1:-assets/published/scenes/datahall.usda}"
uv run python -m aifactory_twin.validate "$STAGE" --json report.json --md report.md
```

**Verify — a gate nobody has watched fail is not known to work:**

```bash
# passes clean
./ci/validate.sh assets/published/components/rack_gb300/rack_gb300.usda; echo "exit=$?"

# now break it on purpose
cp -R assets/published/components/rack_gb300 tests/fixtures/rack_no_mass
# remove the mass attribute from tests/fixtures/rack_no_mass/physics.usda by hand

./ci/validate.sh tests/fixtures/rack_no_mass/rack_gb300.usda; echo "exit=$?"
```

Second run must exit non-zero and name the prim and the rule ID. Commit the broken fixture and
a test asserting it fails, so the failure path stays tested rather than tested once.

- [ ] six rules implemented and passing on good assets
- [ ] fast (unloaded) and full (loaded) passes, both timed
- [ ] runner works on a stage from outside this repo
- [ ] broken fixtures committed, gate proven to fail legibly
- [ ] **README status table: M1, M3, M5 → ✅**

---

## Done

M1, M3 and M5 complete. M4 — assembly and both instancing strategies — comes next, because
validation now exists to catch your mistakes at scale.
