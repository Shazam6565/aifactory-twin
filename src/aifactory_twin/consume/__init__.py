"""GPU consumers (ovrtx render, ovphysx physics). Linux + NVIDIA driver only."""

import shutil
import sys

if shutil.which("nvidia-smi") is None:
    sys.exit(
        "aifactory_twin.consume: NVIDIA driver stack not found. "
        "This package runs only on the Linux RTX box. See README 'Platform split'."
    )
