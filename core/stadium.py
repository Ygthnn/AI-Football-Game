class Stadium:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.score_red = 0
        self.score_blue = 0
        self.winner = None
        self.last_out_type = None
        self.last_out_pos = None

    def draw(self, screen):
        import pygame
        green = (0, 128, 0)
        white = (255, 255, 255)
        net_color = (200, 200, 200)
        screen.fill(green)

        # Saha çizgileri
        pygame.draw.rect(screen, white, (0, 0, self.width, self.height), 5)
        pygame.draw.line(screen, white, (self.width // 2, 0), (self.width // 2, self.height), 2)
        pygame.draw.circle(screen, white, (self.width // 2, self.height // 2), 70, 2)
        pygame.draw.circle(screen, white, (self.width // 2, self.height // 2), 4)

        # Kale çizgileri ve ağları (görsel olarak içte)
        goal_height = 160
        goal_top = self.height // 2 - goal_height // 2
        pygame.draw.rect(screen, net_color, (0, goal_top, 10, goal_height))  # sol kale ağı
        pygame.draw.rect(screen, net_color, (self.width - 10, goal_top, 10, goal_height))  # sağ kale ağı
        pygame.draw.rect(screen, white, (0, goal_top, 5, goal_height))  # sol kale direk
        pygame.draw.rect(screen, white, (self.width - 5, goal_top, 5, goal_height))  # sağ kale direk

        # Ceza sahaları
        penalty_box_width = 100
        penalty_box_height = 200
        pygame.draw.rect(screen, white, (0, self.height // 2 - penalty_box_height // 2, penalty_box_width, penalty_box_height), 2)
        pygame.draw.rect(screen, white, (self.width - penalty_box_width, self.height // 2 - penalty_box_height // 2, penalty_box_width, penalty_box_height), 2)

    def check_goal(self, ball):
        if 220 < ball.y < 380:
            if ball.x <= 0:
                self.score_blue += 1
                return "blue"
            elif ball.x >= self.width:
                self.score_red += 1
                return "red"
        return None

    def is_out(self, ball):
        if ball.x < 0:
            self.last_out_type = "sideline"
            self.last_out_pos = (15, ball.y)
            return True
        elif ball.x > self.width:
            self.last_out_type = "sideline"
            self.last_out_pos = (self.width - 15, ball.y)
            return True
        elif ball.y < 0:
            self.last_out_type = "corner"
            self.last_out_pos = (ball.x, 15)
            return True
        elif ball.y > self.height:
            self.last_out_type = "corner"
            self.last_out_pos = (ball.x, self.height - 15)
            return True
        return False

    def reset_ball_position(self, ball, use_last_out=False):
        if use_last_out and self.last_out_pos:
            ball.x, ball.y = self.last_out_pos
        else:
            ball.x = self.width // 2
            ball.y = self.height // 2
        ball.vel_x = 0
        ball.vel_y = 0
