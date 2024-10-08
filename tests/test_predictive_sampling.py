import jax
import jax.numpy as jnp
import matplotlib.pyplot as plt
from mujoco import mjx

from hydra.algs.predictive_sampling import PredictiveSampling
from hydra.tasks.pendulum import Pendulum


def test_predictive_sampling() -> None:
    """Test the PredictiveSampling algorithm."""
    task = Pendulum()
    opt = PredictiveSampling(task, num_samples=32, noise_level=0.1)

    # Initialize the policy parameters
    params = opt.init_params()
    assert params.mean.shape == (task.planning_horizon - 1, 1)
    assert isinstance(params.rng, jax._src.prng.PRNGKeyArray)

    # Sample control sequences from the policy
    controls, new_params = opt.sample_controls(params)
    assert controls.shape == (opt.num_samples + 1, task.planning_horizon - 1, 1)
    assert new_params.rng != params.rng

    # Roll out the control sequences
    state = mjx.make_data(task.model)
    rollouts = opt.eval_rollouts(state, controls)

    assert rollouts.costs.shape == (
        opt.num_samples + 1,
        task.planning_horizon,
    )
    assert rollouts.observations.shape == (
        opt.num_samples + 1,
        task.planning_horizon,
        2,
    )
    assert rollouts.controls.shape == (
        opt.num_samples + 1,
        task.planning_horizon - 1,
        1,
    )

    # Pick the best rollout
    updated_params = opt.update_params(new_params, rollouts)
    assert updated_params.mean.shape == (task.planning_horizon - 1, 1)
    assert jnp.all(updated_params.mean != new_params.mean)


def test_open_loop() -> None:
    """Use predictive sampling for open-loop optimization."""
    # Task and optimizer setup
    task = Pendulum()
    opt = PredictiveSampling(task, num_samples=32, noise_level=0.1)
    jit_opt = jax.jit(opt.optimize)

    # Initialize the system state and policy parameters
    state = mjx.make_data(task.model)
    params = opt.init_params()

    for _ in range(100):
        # Do an optimization step
        params, rollouts = jit_opt(state, params)

    # Pick the best rollout
    total_costs = jnp.sum(rollouts.costs, axis=1)
    best_idx = jnp.argmin(total_costs)
    best_obs = rollouts.observations[best_idx]
    best_ctrl = rollouts.controls[best_idx]
    assert total_costs[best_idx] <= 9.0

    if __name__ == "__main__":
        # Plot the solution
        _, ax = plt.subplots(3, 1, sharex=True)

        ax[0].plot(best_obs[:, 0])
        ax[0].set_ylabel(r"$\theta$")

        ax[1].plot(best_obs[:, 1])
        ax[1].set_ylabel(r"$\dot{\theta}$")

        ax[2].plot(best_ctrl)
        ax[2].axhline(-1.0, color="black", linestyle="--")
        ax[2].axhline(1.0, color="black", linestyle="--")
        ax[2].set_ylabel("u")
        ax[2].set_xlabel("Time step")

        plt.show()


if __name__ == "__main__":
    test_predictive_sampling()
    test_open_loop()