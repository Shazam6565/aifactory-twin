# POC Scope — SimReady Asset Pipeline Evaluation

## Customer

A hypothetical engineering-software ISV with an existing
3D/CAD asset pipeline and its own application runtime.


## Existing Environment

The customer already has:

- engineering 3D assets
- an existing asset pipeline
- an existing application/runtime
- engineering metadata associated with its assets

## Customer Problem

The customer wants to determine whether its existing engineering
assets can be converted into reusable simulation-ready OpenUSD
components that can support both RTX rendering and rigid-body
physics without requiring the customer to replatform its entire
application around a new runtime.

## Decision This POC Must Enable

At the end of the POC, the customer should be able to decide whether
to proceed with integrating the SimReady OpenUSD + Omniverse
Libraries workflow into its existing product architecture.

## POC Hypothesis

A layered SimReady OpenUSD component can act as the shared asset
representation while OVRTX and OVPhysX consume the appropriate
scene opinions independently, allowing the customer to add rendering
and physics capabilities without rebuilding separate asset pipelines.

## Constraints

1. Existing source assets must not be modified in place.
2. The customer retains ownership of its application lifecycle.
3. Rendering and physics must not require separate canonical assets.
4. Existing engineering metadata must survive the workflow.
5. Validation failures must identify actionable asset-level blockers.
6. The POC is limited to rigid-body physics and rendering.

## Out of Scope

- production deployment
- real thermal or CFD simulation
- full CAD conversion coverage
- application UI integration
- networking or streaming
- ovStorage integration
- production-scale performance validation

## Success Criteria

The POC succeeds if:

1. The source asset remains unchanged.
2. The asset can be published as a layered OpenUSD component.
3. The component passes structural validation.
4. The component passes OVRTX-specific readiness validation.
5. OVRTX produces rendered output.
6. The component passes OVPhysX-specific readiness validation.
7. OVPhysX advances the rigid body and produces a measurable pose change.
8. Engineering-domain metadata survives composition.
9. Both consumers operate from the same reusable component architecture.
10. Any failed requirement produces an actionable validation result.

## Failure / Kill Criteria

The POC does not support adoption if:

- the customer's assets require destructive modification to become usable;
- rendering and physics require maintaining separate canonical asset representations;
- required engineering metadata cannot survive the composition workflow;
- failures cannot be detected before runtime;
- integration requires unacceptable ownership changes to the customer's application architecture.



## An engineering ISV already owns a 3D application and asset pipeline. It wants to evaluate NVIDIA rendering and physics capabilities without replatforming its existing product. The POC tests whether its engineering asset can be transformed into one validated SimReady OpenUSD component consumed independently by OVRTX and OVPhysX while preserving application ownership and engineering metadata. Success is measured through explicit validation, rendered output, and simulated state change. The result determines whether the partner should proceed to a deeper product integration.