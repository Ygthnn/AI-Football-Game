import pygame
from utils.geometry import distance, direction_vector

class AIController:
    def __init__(self, player, role="striker"):
        self.player = player
        self.role = role
        self.zigzag_dir = 1

    def make_decision(self, ball, teammate=None, ball_owner=None, can_act_on_ball=True):
        ball_pos = (ball.x, ball.y)
        player_pos = (self.player.x, self.player.y)

        if self.role == "striker":
            self._play_striker(player_pos, ball_pos, teammate, ball, can_act_on_ball, ball_owner)
        elif self.role == "defender":
            self._play_defender(player_pos, ball_pos, teammate, ball, can_act_on_ball, ball_owner)

    def _play_striker(self, player_pos, ball_pos, teammate, ball, can_act_on_ball, ball_owner):
        if self.player.has_ball:    
            self.player.dribble(ball)
            goal = (780, 300)
            dir_x, dir_y = direction_vector(player_pos, goal)

            if pygame.time.get_ticks() % 300 < 10:
                self.zigzag_dir *= -1

            if dir_x < -0.2:
                self.player.move("left")
            elif dir_x > 0.2:
                self.player.move("right")

            if dir_y < -0.2:
                self.player.move("up" if self.zigzag_dir > 0 else "down")
            elif dir_y > 0.2:
                self.player.move("down" if self.zigzag_dir > 0 else "up")

            if distance(player_pos, goal) < 60:
                self.player.kick_ball(ball)

        else:
            self._move_toward(ball_pos)
            if can_act_on_ball:
                if teammate and distance(player_pos, (teammate.x, teammate.y)) < 120:
                    self.player.pass_to(teammate, ball)
                elif distance(player_pos, ball_pos) < 25:
                    self.player.kick_ball(ball)

    def _play_defender(self, player_pos, ball_pos, teammate, ball, can_act_on_ball, ball_owner):
        home_x = 700 if self.player.team == "blue" else 100

        if (self.player.team == "blue" and self.player.x > home_x) or (self.player.team == "red" and self.player.x < home_x):
            self.player.move("left" if self.player.team == "blue" else "right")

        if ball_owner and ball_owner.team != self.player.team and ball.x < 400:
            self._move_toward((ball_owner.x - 20, ball_owner.y))
        elif distance(player_pos, ball_pos) < 40:
            self._move_toward(ball_pos)

        if can_act_on_ball and distance(player_pos, ball_pos) < 25:
            if teammate:
                self.player.pass_to(teammate, ball)
            else:
                self.player.kick_ball(ball)

    def _move_toward(self, target_pos):
        dx, dy = direction_vector((self.player.x, self.player.y), target_pos)

        if dx < -0.2:
            self.player.move("left")
        elif dx > 0.2:
            self.player.move("right")

        if dy < -0.2:
            self.player.move("up")
        elif dy > 0.2:
            self.player.move("down")
