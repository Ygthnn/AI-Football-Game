"""
Curriculum training without an opponent
=======================================

Phase 0 : ball near player   • 450 000 steps
Phase 1 : mid-field spawn    • 900 000 steps
Phase 2 : anywhere spawn     • 1 500 000 steps
Total   :                    • 2 850 000 steps
"""

from __future__ import annotations           # ← must stay first!

# ── head-less pygame safeguard ────────────────────────────────────
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN if hasattr(pygame, "HIDDEN") else 0)

# ── standard imports ──────────────────────────────────────────────
from pathlib import Path
from typing import Callable

import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

from rl_agent.environment import FootballEnv
from rl_agent.model import create_model


# ------------------------------------------------------------------
#                       TRAINING SCHEDULE
# ------------------------------------------------------------------
STEPS    = [400_000, 800_000, 1_200_000]      # per-phase timesteps
N_ENVS   = 8                                  # parallel workers
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)


# ------------------------------------------------------------------
#                   ENV & STAT-COPY HELPERS
# ------------------------------------------------------------------
def make_env(phase: int) -> Callable[[], FootballEnv]:
    """Factory so we can pass a lambda to DummyVecEnv."""
    return lambda: FootballEnv(phase=phase, render_mode=None)


def _copy(src: np.ndarray, dst: np.ndarray) -> None:
    """Robustly copy VecNormalize statistics (scalar or vector)."""
    if src.shape == ():
        dst[...] = src
    else:
        dst[:] = src


def clone_stats(src: VecNormalize, dst: VecNormalize) -> None:
    """Copy normalisation RMS stats from *src* to *dst*."""
    for attr in ("obs_rms", "ret_rms"):
        _copy(getattr(src, attr).mean, getattr(dst, attr).mean)
        _copy(getattr(src, attr).var,  getattr(dst, attr).var)
        getattr(dst, attr).count = getattr(getattr(src, attr), "count")

    dst.clip_obs    = src.clip_obs
    dst.norm_obs    = src.norm_obs
    dst.norm_reward = src.norm_reward
    dst.epsilon     = src.epsilon


def wrap_with_stats(prev: VecNormalize | None,
                    raw:  DummyVecEnv) -> VecNormalize:
    """Create a VecNormalize wrapper, cloning stats if *prev* exists."""
    v = VecNormalize(raw, norm_obs=True, norm_reward=True, clip_obs=10.0)
    if prev is not None:
        clone_stats(prev, v)
    return v


# ------------------------------------------------------------------
#                        TRAINING LOOP
# ------------------------------------------------------------------
def train_phase(phase: int,
                steps: int,
                model: PPO | None,
                stats: VecNormalize | None) -> tuple[PPO, VecNormalize]:
    """Train or continue training for one curriculum phase."""
    raw_env  = DummyVecEnv([make_env(phase) for _ in range(N_ENVS)])
    venv     = wrap_with_stats(stats, raw_env)

    if model is None:
        model = create_model(venv)
    else:
        model.set_env(venv)

    print(f"\n▶ Phase {phase}  |  {steps:,} steps")
    model.learn(total_timesteps=steps, progress_bar=True)
    return model, venv


# ------------------------------------------------------------------
#                          ENTRY POINT
# ------------------------------------------------------------------
def main() -> None:
    model: PPO | None          = None
    vec_stats: VecNormalize | None = None

    for phase, steps in enumerate(STEPS):
        model, vec_stats = train_phase(phase, steps, model, vec_stats)

    model.save(MODEL_DIR / "final_agent")
    vec_stats.save(MODEL_DIR / "final_vecnorm.pkl")
    print("✅ Training finished.")


if __name__ == "__main__":
    main()
