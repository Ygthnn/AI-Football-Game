"""
Build a PPO agent for the football environment.
-----------------------------------------------

Key points
~~~~~~~~~~
* single 2×256 MLP with Tanh activations
* linear learning-rate decay 1 e-4 → 0
* no VecNormalize wrapper here — the caller decides when to wrap
"""

from __future__ import annotations

from typing import Callable

import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecEnv


# ------------------------------------------------------------------ #
#                       LR SCHEDULE HELPER                           #
# ------------------------------------------------------------------ #
def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """Return a function that linearly decays *initial_value* to 0."""
    assert initial_value > 0.0

    def schedule(progress_remaining: float) -> float:
        # progress_remaining: 1 → 0 during training
        return initial_value * progress_remaining

    return schedule


# ------------------------------------------------------------------ #
#                           CREATE MODEL                             #
# ------------------------------------------------------------------ #
def create_model(
    env: VecEnv,
    *,
    tensorboard_log: str | None = "./logs",
) -> PPO:
    """Return a configured PPO instance attached to *env*."""
    policy_kwargs = dict(
        net_arch=dict(pi=[256, 256], vf=[256, 256]),
        activation_fn=nn.Tanh,
    )

    model = PPO(
        policy="MlpPolicy",
        env=env,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        learning_rate=linear_schedule(1e-4),
        ent_coef=0.01,
        clip_range=0.2,
        vf_coef=0.5,
        policy_kwargs=policy_kwargs,
        verbose=1,
        tensorboard_log=tensorboard_log,
    )
    return model
