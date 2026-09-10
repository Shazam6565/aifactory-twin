# SimReady POC Evaluation

**Asset:** `rack_render.usda`

**Overall Result:** FAIL

## Structural — PASS

- PASS — stage_opens: USD stage opened successfully
- PASS — default_prim_present: defaultPrim is /World
- PASS — composition_resolves: No USD composition errors detected

## Render — PASS

- PASS — material_bindings_resolve: All renderable meshes have resolved material bindings

## Physics — FAIL

- FAIL — rigidbody_has_mass: Rigid body does not have a valid mass: None (`/World/Rack`)
- PASS — rigidbody_has_collider: Rigid body has a collider (`/World/Rack`)

## Domain — PASS

- PASS — nominal_power_present: Nominal power draw is 132000.0 W (`/World/Rack`)
- PASS — cooling_type_present: Cooling type is liquid (`/World/Rack`)

## Conclusion

The asset did not satisfy all blocking POC evaluation categories.
