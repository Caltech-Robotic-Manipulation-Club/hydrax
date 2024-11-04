import jax
import jax.numpy as jnp
import mujoco
from mujoco import mjx

from hydrax import ROOT
from hydrax.task_base import Task


class CartPole(Task):
    """A cart-pole swingup task."""

    def __init__(self):
        """Load the MuJoCo model and set task parameters."""
        mj_model = mujoco.MjModel.from_xml_path(
            ROOT + "/models/cart_pole/scene.xml"
        )

        super().__init__(
            mj_model,
            planning_horizon=10,
            sim_steps_per_control_step=5,
            trace_sites=["tip"],
        )

    def _distance_to_upright(self, state: mjx.Data) -> jax.Array:
        """Get a measure of distance to the upright position."""
        theta = state.qpos[1] - jnp.pi
        theta_err = jnp.array([jnp.cos(theta) - 1, jnp.sin(theta)])
        return jnp.sum(jnp.square(theta_err))

    def running_cost(self, state: mjx.Data, control: jax.Array) -> jax.Array:
        """The running cost ℓ(xₜ, uₜ)."""
        theta_cost = self._distance_to_upright(state)
        theta_dot_cost = 0.01 * jnp.sum(jnp.square(state.qvel))
        control_cost = 0.001 * jnp.sum(jnp.square(control))
        total_cost = theta_cost + theta_dot_cost + control_cost
        return total_cost

    def terminal_cost(self, state: mjx.Data) -> jax.Array:
        """The terminal cost ϕ(x_T)."""
        theta_cost = self._distance_to_upright(state)
        theta_dot_cost = 0.01 * jnp.sum(jnp.square(state.qvel))
        return theta_cost + theta_dot_cost