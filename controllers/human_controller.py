import pygame

class HumanController:
    def __init__(self, player, control_scheme):
        self.player = player
        self.controls = control_scheme  # Dictionary with key mappings

    def handle_input(self, keys, ball, teammate=None, opponent_team=None):
        if keys[self.controls["up"]]:
            self.player.move("up")
        if keys[self.controls["down"]]:
            self.player.move("down")
        if keys[self.controls["left"]]:
            self.player.move("left")
        if keys[self.controls["right"]]:
            self.player.move("right")
        if keys[self.controls["kick"]]:
            self.player.kick_ball(ball)
        if teammate and keys[self.controls["pass"]]:
            self.player.pass_to(teammate, ball)
        
        # 🥾 Tackling input (e.g. Q or RSHIFT)
        if opponent_team and "tackle" in self.controls and keys[self.controls["tackle"]]:
            self.try_tackle(ball, opponent_team)

    def try_tackle(self, ball, opponents):
        for opponent in opponents.players:
            dx = self.player.x - opponent.x
            dy = self.player.y - opponent.y
            dist = (dx ** 2 + dy ** 2) ** 0.5
            if dist < 25 and opponent.has_ball:
                # Topu kap
                opponent.has_ball = False
                self.player.has_ball = True
                ball.vel_x = 0
                ball.vel_y = 0
                ball.x = self.player.x
                ball.y = self.player.y
                break
