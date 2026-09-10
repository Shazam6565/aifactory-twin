# SimReady POC Evaluation

**Asset:** `rack_render.usda`

**Overall Result:** PASS

## Structural — PASS

- PASS — stage_opens: USD stage opened successfully
- PASS — default_prim_present: defaultPrim is /World
- PASS — composition_resolves: No USD composition errors detected

## Render — PASS

- PASS — ovrtx_execution: Demo workflow reported successful OVRTX execution
- PASS — render_output_exists: OVRTX produced a non-empty render output — artifact: `/Users/shauryatiwari/Desktop/Projects/gits/ai-factory-twin/output/demo/render.png`
- PASS — material_bindings_resolve: All renderable meshes have resolved material bindings

## Physics — PASS

- PASS — ovphysx_execution: Demo workflow reported successful OVPhysX execution
- PASS — physics_output_exists: Physics result artifact was produced — artifact: `/Users/shauryatiwari/Desktop/Projects/gits/ai-factory-twin/output/demo/physics_results.json`
- PASS — pose_changed: Rigid-body pose changed after OVPhysX simulation
- PASS — rigidbody_has_mass: Rigid body mass is 1000.0 (`/World/Rack`)
- PASS — rigidbody_has_collider: Rigid body has a collider (`/World/Rack`)

## Domain — PASS

- PASS — nominal_power_present: Nominal power draw is 132000.0 W (`/World/Rack`)
- PASS — cooling_type_present: Cooling type is liquid (`/World/Rack`)

## Conclusion

The asset satisfied all blocking POC evaluation categories.
