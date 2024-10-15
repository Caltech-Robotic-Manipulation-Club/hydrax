import sys

import mujoco
import numpy as np

from hydrax import ROOT
from hydrax.algs import MPPI, PredictiveSampling
from hydrax.mpc import run_interactive
from hydrax.tasks.cube import CubeRotation

"""
Run an interactive simulation of the walker task.
"""

# Define the task (cost and dynamics)
task = CubeRotation()

# Set the controller based on command-line arguments
if len(sys.argv) == 1 or sys.argv[1] == "ps":
    print("Running predictive sampling")
    ctrl = PredictiveSampling(task, num_samples=1024, noise_level=0.2)
elif sys.argv[1] == "mppi":
    print("Running MPPI")
    ctrl = MPPI(task, num_samples=1024, noise_level=0.2, temperature=0.001)
else:
    print("Usage: python leap_hand.py [ps|mppi]")
    sys.exit(1)

# Define the model used for simulation
mj_model = mujoco.MjModel.from_xml_path(ROOT + "/models/cube/scene.xml")
start_state = np.concatenate([mj_model.qpos0, np.zeros(mj_model.nv)])

# Run the interactive simulation
run_interactive(
    mj_model,
    ctrl,
    start_state,
    frequency=25,
    fixed_camera_id=None,
    show_traces=True,
    max_traces=1,
    trace_color=[1.0, 1.0, 1.0, 1.0],
)