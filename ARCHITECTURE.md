# Architecture

Layer strategy, composition decisions, and the reasoning behind each one.

`README.md` says what this repo does. This document says **why it is shaped this way**, and is
written so that every ordering decision can be defended rather than merely stated.

---

## Glossary — read this first

These five words are used precisely throughout this document, and two of them are overloaded
in ordinary USD conversation. Definitions here win.

| Term | Meaning in this repo |
|---|---|
| **Component** | One reusable, self-contained asset: a rack, a CDU, a PDU, a floor tile, the robot. Matches USD's `kind = "component"` in the model hierarchy — a leaf-level thing you would ship and reuse. Lives in one directory under `assets/published/components/`. |
| **Interface layer** | The single `.usda` file at the root of a component directory (`rack_gb300.usda`). It declares the asset-root prim, attaches geometry as a payload, and sublayers the material / physics / domain opinions. It is the component's public API. |
| **Referencing layer** | Any layer that pulls a component in by reference — in this repo, the scene's `catalog.usda` and `layout.usda`. Also anyone else's scene, in another repo, that references our published output. |
| **Stage consumer** | Software that opens a composed stage and does something with it: the validator, `usdview`, `ovrtx`, `ovphysx`, Isaac Sim, an MCP agent answering questions about the scene. Consumers **read**; the pipeline **writes**. |
| **Producer** | The pipeline itself — everything in `src/aifactory_twin/` except `consume/`. The only thing that writes to `assets/published/`. |

When this document says *"the only file a consumer names"*, it means both senses at once, and
the rule is the same for both: **reference `rack_gb300.usda`, never `geo.usdc`, never
`physics.usda`.** See ADR-04.

### Where a component comes from

```
   assets/source/rack_gb300.usda          a vendor drop. Immutable. Possibly wrong.
            │                             (in this repo, generated once by tools/ as a
            │                              stand-in, since we have no real vendor CAD)
            │
            ▼  ingest/normalize.py            M1 — units, up-axis, naming, xform reset
   normalized geometry + manifest.json        provenance: source sha256 → published path
            │
            ▼  author/simready.py             M3 — split into the layer stack, then author
   assets/published/components/rack_gb300/         physics, materials, semantics, domains
       rack_gb300.usda        ← interface layer
       geo.usdc               ← payload
       mtl.usda  physics.usda  domain_electrical.usda   ← sublayers
            │
            ▼  author/assemble.py             M4 — referenced N times, placed, instanced
   assets/published/scenes/datahall.usda
            │
            ▼
   stage consumers: validate/ · ovrtx · ovphysx · usdview · agents
```

**The component is the unit of reuse, of vendor ownership, and of validation.** Authoring work
spent once on a component is paid back `N` times in the scene — which is the entire reason the
pipeline is shaped as *component authoring* followed by *scene assembly*, rather than as one
script that builds a data hall.

---

## 1. The one-paragraph version

A component is a stack of independently ownable opinions over a single piece of vendor
geometry, where the geometry is the *weakest* opinion and arrives through a lazily loadable
payload. A scene is a stack of independently ownable opinions over a catalog of those
components. Every question this architecture answers reduces to **"who is allowed to override
whom, and what should I be able to read without loading the heavy data?"**

---

## 2. Composition primer — only the part that matters here

USD resolves conflicting opinions by **LIVRPS** strength order, strongest first:

| | Arc | Used here for |
|---|---|---|
| **L** | Local — the layer stack: a layer plus its `subLayers`, recursively | material, physics and domain opinions |
| **I** | Inherits | — |
| **V** | VariantSets | — (LOD switching was designed, not built) |
| **R** | References | scene → published components |
| **P** | Payloads | component → geometry |
| **S** | Specializes | — |

Two consequences drive the entire design:

1. **Local beats Payload, always.** Anything authored in a sublayer of the interface layer
   outranks anything arriving through the payload arc — regardless of sublayer ordering, and
   without needing to think about it. Layer *ordering* among the sublayers only matters for
   resolving conflicts between the sublayers themselves.
2. **Payloads can be unloaded; sublayers cannot.** `subLayers` are always composed. A payload
   is load-gated per stage, which makes it the only arc that lets you compose a scene's
   structure and metadata while leaving its geometry on disk.

Within `subLayers`, **earlier in the list is stronger.**

---

## 3. Per-component layer stack

```
rack_gb300.usda                    ← interface layer; the only file anything else names
  subLayers = [
      @./domain_electrical.usda@,  ← strongest sublayer
      @./physics.usda@,
      @./mtl.usda@                 ← weakest sublayer
  ]

  def Xform "rack_gb300" (
      payload = @./geo.usdc@       ← weakest opinion overall, load-gated
  )
```

### Why geometry is a payload and not a sublayer

Because the two things that make this pipeline worth building both depend on it:

- **Cost.** A validation pass that only checks electrical metadata must not pay to load four
  million triangles. With geometry payloaded, checking domain rules across a 4096-rack hall
  touches kilobytes.
- **Swappability.** The payload target is a single line. When the vendor ships v2, that line
  changes and nothing else does.

A sublayer would give you neither. It composes unconditionally and it is not a natural
substitution point.

### Why geometry is the weakest opinion

Because the vendor owns it and everyone else's work sits on top of it. If geometry were the
strongest layer, every routine vendor update would clobber the colliders, masses, material
bindings, semantic labels and power ratings authored above it — and a pipeline whose output is
destroyed by its own inputs is worthless.

Ordering the sublayers *domain → physics → materials* follows the same logic, from most
site-specific to most generic. A site electrical engineer's declared power draw for their
specific deployment should outrank a simulation default, which should outrank a look-dev
default. In practice these three rarely author the same attribute; the ordering exists so that
when they eventually do, the outcome is already decided and nobody has to negotiate.

### The asset-root authoring rule

> **Author load-independent data on the asset-root prim. Author geometry-dependent data on
> descendants.**

This is the sharpest constraint in the repo and it falls directly out of §2.

The asset-root prim (`/rack_gb300`) is `def`-ed in the **interface layer**, so it exists whether
or not the payload is loaded. Attributes authored on it in `domain_electrical.usda` — power
draw, phase, heat output, cooling type — and `UsdPhysics.MassAPI` mass are therefore readable
with geometry unloaded.

Descendant prims (the meshes) only exist once the payload loads. So collision APIs, mesh
approximations and material bindings are inherently load-dependent, and any `over` targeting
them is inert until then.

The practical payoff:

| Query | Payload state | Cost |
|---|---|---|
| Total power draw of row B | unloaded | kilobytes |
| Every rack declares phase and cooling type | unloaded | kilobytes |
| Read declared draw for every rack in the hall | unloaded | kilobytes |
| Every mesh has a bound material | **loaded** | full |
| No mesh collider above 10k tris | **loaded** | full |

The validation harness splits along exactly this line, which is why the domain gate can run on
every commit and the structural gate can run less often. **This is a load-gating strategy that
falls out of a governance decision** — and if the metadata had been authored one prim lower,
none of it would work.

---

## 4. Scene layer stack

```
datahall.usda
  subLayers = [
      @./session.usda@,          ← strongest — runtime, ephemeral, gitignored
      @./site_overrides.usda@,
      @./layout.usda@,
      @./catalog.usda@           ← weakest — references published components
  ]
```

| Layer | Owner | Contains | Lifetime |
|---|---|---|---|
| `session.usda` | runtime / telemetry | live values: measured draw, temperatures, robot pose | ephemeral — **not committed** |
| `site_overrides.usda` | site engineer | this deployment's deviations from catalog defaults | committed, per-site |
### What the reference arc actually looks like

"Scene → published components" is the **R** in LIVRPS, and on disk it is unremarkable — which
is the point. `catalog.usda` answers *which version of each part this scene uses*:

```usda
#usda 1.0
(
    defaultPrim = "Catalog"
)

class "Catalog"
{
    class "RackGB300" (
        prepend references = @../components/rack_gb300/rack_gb300.usda@
    ) { }
}
```

`layout.usda` answers *how many and where*, one prim per placed unit:

```usda
#usda 1.0

over "World"
{
    def Xform "Row_B"
    {
        def "rack_B14" (
            prepend references = @../components/rack_gb300/rack_gb300.usda@
            instanceable = true
        )
        {
            double3 xformOp:translate = (12.0, 4.8, 0.0)
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }
        # ... N of these, generated
    }
}
```

The reference pulls in the component's **entire composed opinion** — every sublayer and the
payload — under `rack_B14`. The scene then adds only what it owns: a transform and an
instancing flag.

Note the reference targets `rack_gb300.usda` and nothing else. Referencing `geo.usdc` directly
would also "work", in the sense that geometry would appear — with materials, colliders, mass,
semantics and power ratings silently absent. It would look correct in a viewport and fail every
validator, which is the failure mode ADR-04 exists to prevent.

**Open decision for M4:** whether placed prims reference the component directly (shown above)
or inherit from the `catalog.usda` class prims. The direct form is the standard idiom and is
known to instance cleanly; the class form centralises version changes in one place. Decide it
with a measurement at M4 rather than by assertion, and record which you chose here.

| `layout.usda` | layout / planning | placement, rows, instancing | committed |
| `catalog.usda` | asset pipeline | references to published components — the parts list | generated |

Four owners, four files, no merge conflicts, and a strict answer to "who wins" that nobody has
to litigate. `session.usda` is strongest and ephemeral on purpose: live telemetry should
override design intent for display, and should never be mistaken for design intent when
committed. It is in `.gitignore` for that reason, not by oversight.

---

## 5. Instancing policy

> **Addressability decides. Not performance.**

| | Scenegraph instancing | Point instancing |
|---|---|---|
| Mechanism | `prim.SetInstanceable(True)` on referenced prims | `UsdGeomPointInstancer` — prototypes + positions |
| Keeps | prim structure, per-prim addressing, selection, per-instance overrides | extreme scale, minimal memory |
| Loses | higher per-prim memory at extreme counts | per-instance addressing and overrides |
| Used for | **racks, CDUs, PDUs, the robot** | **floor tiles, cable trays, ceiling fixtures** |

For a twin used as a decision layer, an operator must be able to click rack B-14 and see its
telemetry. Point instancing makes that hard — instances are not prims and cannot carry
per-instance metadata or independent overrides. So racks get scenegraph instancing *despite*
it being the more expensive option, and point instancing is reserved for things nobody
addresses individually.

Both paths are built and both are benchmarked (M4, M7). The benchmark exists to quantify what
the addressability requirement costs — not to pick the winner. The requirement already picked it.

---

## 6. Provenance

`assets/source/` is immutable. `assets/published/` is generated and never hand-edited. The link
between them is `manifest.json`:

```json
{
  "generated_utc": "...",
  "pipeline_version": "...",
  "usd_version": "...",
  "components": {
    "rack_gb300": {
      "source": "assets/source/rack_gb300.usda",
      "source_sha256": "...",
      "published": "assets/published/components/rack_gb300/rack_gb300.usda",
      "layers": ["geo.usdc", "mtl.usda", "physics.usda", "domain_electrical.usda"]
    }
  }
}
```

This makes "which source produced this published asset, with which pipeline version" a lookup
rather than an archaeology exercise, and makes the pipeline's output verifiable: re-running on
unchanged sources must produce unchanged hashes. Determinism is a feature, and it is the reason
prim naming is derived from source rather than from iteration order.

---

## Validation tiers

**Valid USD and usable-by-`ovphysx` are different claims. `usdchecker` makes the first. This
harness makes the second.**

| Tier | Question | Owner | Status |
|---|---|---|---|
| **Tier 1 — Structural validity** | Is this valid USD? | The 28 built-in `UsdValidation` validators shipped with OpenUSD | delegated; we run the suite and report it |
| **Tier 2 — Consumer fitness** | Is this asset usable by `ovphysx` and by `ovrtx`? | Us — six custom validators | **this is the harness** |
| **Tier 3 — Engineering consistency** | Are the declared engineering values consistent with each other? | — | **designed, not built** |

A structurally valid asset can still be unusable. A rigid body with no mass, a material binding
that resolves to nothing, a `RigidBodyAPI` prim with no collider — `usdchecker` passes all
three; `ovphysx` and `ovrtx` do not. That gap is the harness.

The six Tier 2 rules, each registered into `UsdValidation.ValidationRegistry` and each per-prim:

| Rule | Protects |
|---|---|
| `rigidbody_has_mass` | `ovphysx` |
| `rigidbody_has_collider` | `ovphysx` |
| `all_meshes_bound` | `ovrtx` |
| `semantics_present` | SDG consumers |
| `electrical_complete` | domain consumers — **presence only** |
| `thermal_complete` | domain consumers — **presence only** |

Tier 3 is specified and cut from the build. The domain data it would read **is** authored and
its presence validated — see §9 and `SIMREADY_SPEC.md` §5.

Full rules, severities and payload flags: `SIMREADY_SPEC.md`. The contract: `SCOPE.md`.

---

## 7. URDF gap analysis

URDF describes a robot's kinematics and little else. Importing it to USD is the easy half;
**the pipeline's value is in what gets authored afterwards.** This table is the answer to
"what is lost on URDF import?"

| Concern | URDF | Authored after import |
|---|---|---|
| Articulation root | kinematic tree only, no solver root | `UsdPhysics.ArticulationRootAPI` on the correct prim |
| Joint drives | `effort` / `velocity` limits only | `UsdPhysics.DriveAPI` — type, stiffness, damping, target, max force |
| Solver tuning | none | PhysX articulation settings — iteration counts, sleep threshold, stabilization |
| Material identity | `<material>` with an RGBA colour | `UsdShade` network — albedo, roughness, metallic, normal |
| Physics materials | friction only via vendor extensions, not core URDF | `UsdPhysics.MaterialAPI` — static/dynamic friction, restitution, bound to collision prims |
| Sensors | **no concept whatsoever** | camera / lidar / IMU prims, render products |
| Semantic labels | **no concept** | semantics schema applied for SDG — verify the exact schema name against your runtime, it has changed across releases |
| Visual vs collision | `<visual>` and `<collision>` exist | verified preserved, `purpose` set correctly, collision meshes given approximations |
| Collider approximation | none | convex hull / convex decomposition / SDF chosen per part |
| Mass and inertia | `<inertial>` exists but is frequently zero or wrong in real files | validated, and corrected where wrong |
| Units | meters/radians **by convention only** — nothing declares or enforces it | asserted and enforced at ingest |
| Instancing, variants, LOD | no concept | authored |

Being able to say this out loud, unprompted, is the deliverable of M2 — more than the import
script is.

---

## 8. Decision log

Each entry: the question, the decision, the reason, and **what it costs** — because a decision
with no stated cost is usually one that wasn't actually made.

### ADR-01 — Z-up, meters
**Q:** USD defaults to Y-up. Which convention wins?
**D:** Z-up, `metersPerUnit = 1.0`.
**Why:** Omniverse, Isaac Sim and URDF are all Z-up. Following USD's default would mean a
rotation fixup on every robot import and every Isaac hand-off — a permanent tax to match a
default nobody downstream uses.
**Cost:** Assets authored in Y-up DCC tools need conversion at ingest. That conversion is in
one place and is validated, which is the trade being bought.

### ADR-02 — Geometry is a payload, not a sublayer
**D:** Geometry arrives via a payload arc on the asset-root prim.
**Why:** Load-gating (cheap metadata queries) and a single-line vendor swap point. §3.
**Cost:** Consumers must remember to load payloads before touching geometry, and a stale
payload target fails at composition rather than at author time — so `no_unresolved_references`
is a mandatory validator, not an optional one.

### ADR-03 — Domain layers are the strongest sublayer
**D:** `domain_electrical` > `physics` > `mtl`.
**Why:** Most site-specific opinion wins over most generic. Site engineering data should
outrank a simulation default.
**Cost:** A domain author can silently override a physics value. Mitigated by keeping the
domain namespace disjoint from the physics namespace in practice, and by the fact that a
deliberate override is the intended behaviour when they do collide.

### ADR-04 — The interface layer is the only public entry point
**D:** Consumers reference `rack_gb300.usda`. Never `geo.usdc`, never `physics.usda`.
**Why:** It is the seam that lets the internal layer structure change without breaking any
consumer. Referencing a sublayer directly gets you an unlayered fragment and silently drops
every opinion above it.
**Cost:** One more file per component, and a rule that has to be enforced by convention and
review rather than by USD itself.

### ADR-05 — Load-independent data lives on the asset-root prim
**D:** Domain metadata and mass on the root; colliders and bindings on descendants.
**Why:** Makes the whole domain rule set runnable with geometry unloaded. §3.
**Cost:** Per-sub-part domain data (per-tray power draw, say) does not get this property. If
that is ever needed, those prims must move into the interface layer or the fast path is lost
for them.

### ADR-06 — Instancing chosen by addressability, not performance
**D:** Scenegraph for anything an operator clicks; PointInstancer for anything they don't.
**Why:** §5. A decision-layer twin whose racks cannot be selected has failed at its purpose,
however fast it renders.
**Cost:** Measurably higher memory and prim count at high `N`. M7 quantifies exactly how much,
which turns an assertion into a number.

### ADR-07 — `.usda` for reviewed layers, `.usdc` for geometry
**D:** Interface, materials, physics, domain and scene layers are ASCII. Geometry is binary.
**Why:** Layer files should be diffable in a pull request — that is most of the value of
layering as a governance mechanism. Meshes should not be.
**Cost:** Slightly slower parse for the ASCII layers. Irrelevant at these sizes, and it would
matter if they held geometry — which is another argument for the split.

### ADR-08 — Source immutable, published generated
**D:** Nothing in `assets/source/` is ever edited. Nothing in `assets/published/` is ever
hand-edited.
**Why:** It is what makes "I re-run the pipeline" a true answer instead of an aspiration.
**Cost:** Every fix must be expressed as code, including one-off ones. That is the discipline
being bought, and it is genuinely slower on the first fix and much faster by the tenth.

### ADR-09 — Domain data as namespaced custom attributes, not a schema (yet)
**D:** `aifactory:electrical:nominalPowerDrawW` and friends, as custom attributes.
**Why:** Zero registration, works in every USD build, reviewable in ASCII. The productionisation
path is a codeless applied API schema, which changes the authoring call and nothing else.
Real DSX partners (ETAP for electrical, Cadence for thermal) define these as formal specs;
mirroring that structure is the point of the exercise.
**Cost:** No type safety and no USD-level validation — a typo silently becomes a new attribute
rather than an error. **This is precisely why `electrical_complete` and `thermal_complete`
exist as validators.** The weakness of the choice creates the requirement for the gate.

### ADR-10 — `session.usda` is strongest and gitignored
**D:** Runtime telemetry is the strongest scene layer and is never committed.
**Why:** Live values must override design intent for display, and must never be confused with
design intent afterwards.
**Cost:** A scene missing `session.usda` composes with a subLayer that does not resolve. The
layer is authored as optional and its absence is treated as normal, not as an error — one of
the few places the pipeline deliberately tolerates an unresolved path.

### ADR-11 — The validator accepts any USD stage, not just ours
**Q:** Is validation a step in *this* pipeline, or a tool that works on anyone's twin?
**D:** A tool. `validate/` takes a stage path and must not assume this repo's directory layout,
naming, or that the pipeline produced the input.
**Why:** The most likely external use of this repo is not "run my geometry through your
pipeline" — it is "point your gate at the twin I already have." A validator coupled to its
producer is a build step; a validator decoupled from it is a product. The decoupled version
also happens to be the one that can validate a *competitor's* output, which is what makes it
useful to a partner.
**Cost:** Rules cannot assume our conventions hold. Anything convention-dependent — Z-up,
`aifactory:` attribute namespace — has to be a configurable parameter with our values as the
default, rather than a hardcoded constant. Slightly more code, and worth it.

---

## 9. Known limitations

- Domain rules encode **one worked example** of a spec. They are not an electrical or thermal
  standard, are not endorsed by anyone, and check only that data was authored.
- **Cross-component engineering consistency checking is designed and specified but not
  implemented.** The domain data is authored and its presence is validated; **no rule compares
  declared values across prims, and nothing aggregates them.** The layer architecture was built
  to make such rules possible — domain data sits on the asset root and is readable with geometry
  unloaded — but that capability is unused. See `SIMREADY_SPEC.md` §6.
- Domain rules encode presence, not correctness. A rack declaring an implausible power draw
  passes every rule in this repository provided the attribute exists and is in range.
- No CFD. Thermal validation checks a declaration is present and its token is valid. It does
  not check the value, and does not compare it against anything.
- Instancing benchmarks reflect one GPU and one driver version. They are a reproducible method
  first and numbers second.
- The `ovrtx` / `ovphysx` / `ovstage` APIs are Early Access and may move. Anything stubbed
  against a changed API is marked `# STUB:` in code and called out in `README.md` rather than
  quietly left to look finished.
