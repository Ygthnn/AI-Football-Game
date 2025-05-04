"""
Football RL – curriculum env matching the May-2025 game build
=============================================================

Reward summary (unchanged from the original)
--------------------------------------------
−0.002 · dist                 (every frame)
+0.10  · Δdist                (only until first touch)
+3·cosθ    on any kick left   (θ = angle to horizontal)
−0.2        on any kick right
−0.01       while holding and not kicking
+30         score left goal   (−2 if ball crosses own goal line)
"""

from __future__ import annotations  # keep first!

import math, random
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces
import pygame                                    # real video backend

from core.ball   import Ball
from core.player import Player


# ── geometry / physics ──────────────────────────────────────────────
W, H        = 800, 600
TOP_MARGIN  = 40
FIELD_H     = H - TOP_MARGIN

FOOT_R      = 40           # ← kick / possession radius (foot-to-ball)
MAX_V       = 10.0
MAX_STEPS   = 1_000

# ── reward weights (identical to original) ──────────────────────────
DIST_PEN    = -0.002
SHRINK_BON  =  0.10
KICK_LEFT_W =  3.0
KICK_RIGHT  = -0.2
HOLD_PEN    = -0.01
GOAL_REW    = 30.0          # own-goal penalty handled in step()


class FootballEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 60}

    # ------------------------------------------------------------------
    def __init__(self, phase: int = 0, render_mode: str | None = None):
        super().__init__()
        self.phase       = int(phase)
        self.render_mode = render_mode
        self.viewer      = None
        self.clock       = None

        # 0 noop, 1-4 move, 5 kick
        self.action_space = spaces.Discrete(6)

        # [p_x, p_y-TM, b_x, b_y-TM, v_x/10, v_y/10]
        self.observation_space = spaces.Box(
            low  = np.array([0, 0, 0, 0, -1, -1], np.float32),
            high = np.array([W, FIELD_H, W, FIELD_H, 1, 1], np.float32),
            dtype=np.float32,
        )

        self.reset()

    # ------------------------------------------------------------------
    def reset(self, seed: int | None = None,
              options: dict[str, Any] | None = None):
        super().reset(seed=seed)
        self.t = 0

        # curriculum spawn rectangles (x ranges unchanged; y shifted)
        if self.phase == 0:                           # tight ±60 px box
            bx = random.randint(500, 750)
            by = random.randint(
                TOP_MARGIN + FIELD_H//2 - 60,
                TOP_MARGIN + FIELD_H//2 + 60)
        elif self.phase == 1:                         # mid-field box
            bx = random.randint(250, 750)
            by = random.randint(
                TOP_MARGIN + FIELD_H//2 - 150,
                TOP_MARGIN + FIELD_H//2 + 150)
        else:                                         # anywhere
            bx = random.randint(50, 750)
            by = random.randint(TOP_MARGIN + 50,
                                TOP_MARGIN + FIELD_H - 50)

        self.ball   = Ball(bx, by)
        self.player = Player(700, TOP_MARGIN + FIELD_H//2, team="blue")

        self.player.has_ball = False
        self.prev_dist       = self._foot_dist()

        return self._obs(), {}

    # ------------------------------------------------------------------
    def step(self, action: int):
        self.t += 1
        r = 0.0
        did_kick = False
        kick_left = False

        # movement / kick ------------------------------------------------
        if action in (1, 2, 3, 4):
            self.player.move(("noop", "up", "down", "left", "right")[action])
        elif action == 5 and self._foot_dist() < FOOT_R:
            self.player.kick_ball(self.ball)
            did_kick  = True
            kick_left = self.ball.vel_x < 0

        # physics --------------------------------------------------------
        self.ball.move()
        self.player.has_ball = self._foot_dist() < FOOT_R

        # distance shaping ----------------------------------------------
        dist = self._foot_dist()
        r += DIST_PEN * dist
        if not self.player.has_ball:
            r += SHRINK_BON * (self.prev_dist - dist)
        self.prev_dist = dist

        # kick reward ----------------------------------------------------
        if did_kick:
            if kick_left:
                cos = abs(self.ball.vel_x) / (
                        abs(self.ball.vel_x) + abs(self.ball.vel_y) + 1e-6)
                r += KICK_LEFT_W * cos
            else:
                r += KICK_RIGHT

        # holding penalty ------------------------------------------------
        if self.player.has_ball and not did_kick:
            r += HOLD_PEN

        # goals & termination -------------------------------------------
        terminated = False
        if self.ball.x <= 5:                      # scored left
            r += GOAL_REW
            terminated = True
        elif self.ball.x >= W - 5:                # own goal
            r -= 2.0
            terminated = True

        truncated = self.t >= MAX_STEPS
        return self._obs(), r, terminated, truncated, {}

    # ------------------------------------------------------------------
    # helpers
    def _foot(self) -> tuple[float, float]:
        """Return (x, y) of the player’s foot point."""
        return (self.player.x + self.player.width / 2,
                self.player.y + self.player.height)

    def _foot_dist(self) -> float:
        fx, fy = self._foot()
        return math.hypot(self.ball.x - fx, self.ball.y - fy)

    def _obs(self):
        vx = np.clip(self.ball.vel_x / MAX_V, -1, 1)
        vy = np.clip(self.ball.vel_y / MAX_V, -1, 1)
        return np.array([
            self.player.x,
            self.player.y - TOP_MARGIN,
            self.ball.x,
            self.ball.y - TOP_MARGIN,
            vx, vy
        ], np.float32)

    # (render() and close() are unchanged; include if you need them)
