# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause

# NOTE: This file is included verbatim in documentation via literalinclude.
# Tutorial marker comments below define the included range.

# [tutorial-start]
import ovphysx
from ovphysx import PhysX, TensorType
from pathlib import Path
import numpy as np


print("Using ovphysx version: ", ovphysx.__version__)

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

script_dir = Path(__file__).resolve().parent
usd_path = script_dir / "/home/as22cq/Projects/aifactory-twin/assets/published/scenes/rack_physics.usda"

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

    print("BEFORE pose:", poses[0])
    print("BEFORE Z:", poses[0][2])

    # SIMULATE
    dt = 1.0 / 60.0
    num_steps = 120

    for _ in range(num_steps):
        physx.step(dt)

    # AFTER
    pose_binding.read(poses)

    print("AFTER pose:", poses[0])
    print("AFTER Z:", poses[0][2])

    pose_binding.destroy()
    print("Simulation step completed successfully")
finally:
    if stage is not None:
        physx.detach_ovstage()
        stage.destroy()
    physx.release()
    print("Cleanup complete")
# [tutorial-end]
