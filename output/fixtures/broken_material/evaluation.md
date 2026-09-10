# SimReady POC Evaluation

**Asset:** `rack_render.usda`

**Overall Result:** FAIL

## Structural — PASS

- PASS — stage_opens: USD stage opened successfully
- PASS — default_prim_present: defaultPrim is /World
- PASS — composition_resolves: No USD composition errors detected

## Render — FAIL

- FAIL — material_bindings_resolve: One or more renderable meshes have no resolved material binding

## Physics — PASS

- PASS — rigidbody_has_mass: Rigid body mass is 1000.0 (`/World/Rack`)
- PASS — rigidbody_has_collider: Rigid body has a collider (`/World/Rack`)

## Domain — PASS

- PASS — nominal_power_present: Nominal power draw is 132000.0 W (`/World/Rack`)
- PASS — cooling_type_present: Cooling type is liquid (`/World/Rack`)

## Conclusion

The asset did not satisfy all blocking POC evaluation categories.
