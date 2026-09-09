# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

# NOTE: This file is included verbatim in documentation via literalinclude.
# Tutorial marker comments below define the included range.

# [tutorial-start]
import json
import ovphysx
from ovphysx import PhysX, TensorType
from pathlib import Path
import numpy as np


print("Using ovphysx version: ", ovphysx.__version__)

REPO_ROOT = Path(__file__).resolve().parents[3]

def attach_scene(physx, usd_path):
    import ovstage

    if not ovstage.population.available():
        raise RuntimeError("ovstage population bridge is unavailable")

    stage = ovstage.Stage("ovphysx-hello-world")
    ordinal = 1
    try:
        ovstage.population.open_usd(stage, str(usd_path), ordinal=ordinal, domains=ovstage.PopulationDomain.PHYSICS)
        # Population does not seal: the caller owns ordinal lifecycle, and
        # attach_ovstage() reads at a sealed ordinal.
        stage.advance_write_floor(ordinal=ordinal).wait()
        physx.attach_ovstage(stage, read_ordinal=ordinal)
        print("Loaded scene through ovstage")
        return stage
    except Exception:
        stage.destroy()
        raise

usd_path = REPO_ROOT / "assets/published/scenes/rack_physics.usda"

# Initialize PhysX
physx = PhysX()
stage = attach_scene(physx, usd_path)

try:
    pose_binding = physx.create_tensor_binding(
        pattern="/World/Rack",
        tensor_type=TensorType.RIGID_BODY_POSE,
    )

    print("Rigid bodies found:", pose_binding.count)
    print("Pose shape:", pose_binding.shape)

    poses = np.zeros(
        pose_binding.shape,
        dtype=np.float32
    )

    # BEFORE
    pose_binding.read(poses)
    before_pose = poses[0].copy()

    print("BEFORE pose:", before_pose)
    print("BEFORE Z:", before_pose[2])

    # SIMULATE
    dt = 1.0 / 60.0
    num_steps = 120

    for _ in range(num_steps):
        physx.step(dt)

    # AFTER
    pose_binding.read(poses)
    after_pose = poses[0].copy()

    print("AFTER pose:", after_pose)
    print("AFTER Z:", after_pose[2])

    pose_binding.destroy()
    print("Simulation step completed successfully")

    before_x, before_y, before_z = (float(v) for v in before_pose[:3])
    after_x, after_y, after_z = (float(v) for v in after_pose[:3])

    results = {
        "before": {
            "x": before_x,
            "y": before_y,
            "z": before_z,
        },
        "after": {
            "x": after_x,
            "y": after_y,
            "z": after_z,
        },
        "pose_changed": bool(not np.array_equal(before_pose, after_pose)),
    }

    output_path = REPO_ROOT / "output" / "demo" / "physics_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Results written to {output_path}")
finally:
    if stage is not None:
        physx.detach_ovstage()
        stage.destroy()
    physx.release()
    print("Cleanup complete")
# [tutorial-end]
