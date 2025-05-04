# C:\Users\yigit\OneDrive\Desktop\aigame\AI-Football-Game\core\player.py

import os
import pygame

# Dosya yollarını tanımlıyoruz
_BASE_DIR      = os.path.dirname(__file__)                  # ...\AI-Football-Game\core
_PROJECT_DIR   = os.path.dirname(_BASE_DIR)                 # ...\AI-Football-Game
ROOT_DIR       = os.path.dirname(_PROJECT_DIR)              # ...\aigame
_ASSET_DIR     = os.path.join(ROOT_DIR, "assets")           # ...\aigame\assets
SPRITE_FILES   = {
    "red":  os.path.join(_ASSET_DIR, "sprite_team1.png"),
    "blue": os.path.join(_ASSET_DIR, "sprite_team2.png"),
}
KICK_SOUND    = os.path.join(_ASSET_DIR, "kick.wav")

class Player:
    # Sprite ve vuruş sesi sınıf bazında cache’lenir
    _sprite_cache = {}
    _kick_sound   = None

    def __init__(self, x, y, team, is_ai=False, player_id=""):
        self.x = x
        self.y = y
        self.team = team
        self.is_ai = is_ai
        self.player_id = player_id
        self.speed = 2.5

        # Lazy-load ve ölçekleme: 50×50 sprite
        if team not in Player._sprite_cache:
            img = pygame.image.load(SPRITE_FILES[team]).convert_alpha()
            Player._sprite_cache[team] = pygame.transform.scale(img, (50, 50))
        self.sprite = Player._sprite_cache[team]

        # Boyutlar artık sprite ile uyumlu
        self.width  = 40
        self.height = 40

        # Lazy-load vuruş sesi
        if Player._kick_sound is None:
            Player._kick_sound = pygame.mixer.Sound(KICK_SOUND)
            Player._kick_sound.set_volume(0.5)

        self.has_ball = False

    def move(self, direction):
        min_x, max_x = 0, 800 - self.width
        min_y, max_y = 0, 600 - self.height

        if direction == "up":
            self.y -= self.speed
        elif direction == "down":
            self.y += self.speed
        elif direction == "left":
            self.x -= self.speed
        elif direction == "right":
            self.x += self.speed

        self.x = max(min_x, min(self.x, max_x))
        self.y = max(min_y, min(self.y, max_y))

    def kick_ball(self, ball):
        # Ayak noktasına göre çarpışma
        foot_x = self.x + self.width  / 2
        foot_y = self.y + self.height

        dx = ball.x - foot_x
        dy = ball.y - foot_y
        dist = (dx**2 + dy**2)**0.5
        if dist < 40 and dist != 0:
            power = 2.5
            self.has_ball = False
            ball.kick(dx / dist * power, dy / dist * power)
            Player._kick_sound.play()

    def pass_to(self, teammate, ball):
        # Ayak noktasına göre pas
        foot_x = self.x + self.width  / 2
        foot_y = self.y + self.height

        dx = teammate.x - foot_x
        dy = teammate.y - foot_y
        dist_to_ball = ((ball.x - foot_x)**2 + (ball.y - foot_y)**2)**0.5
        if dist_to_ball > 20 or dist_to_ball == 0:
            return

        power = 2.5
        self.has_ball = False
        teammate.has_ball = True
        ball.kick(dx / dist_to_ball * power, dy / dist_to_ball * power)
        Player._kick_sound.play()

    def dribble(self, ball):
        # Ayak noktasına göre dripling
        foot_x = self.x + self.width  / 2
        foot_y = self.y + self.height

        dx = ball.x - foot_x
        dy = ball.y - foot_y
        dist = (dx**2 + dy**2)**0.5
        if dist < 20 and dist != 0:
            power = 0.5
            ball.kick(dx / dist * power, dy / dist * power)

    def draw(self, screen):
        """ Oyuncu sprite’ını ve isteğe bağlı ID’sini çizer. """
        screen.blit(self.sprite, (int(self.x), int(self.y)))
        if self.player_id:
            font     = pygame.font.SysFont(None, 16)
            txt_surf = font.render(self.player_id, True, (255, 255, 255))
            screen.blit(txt_surf, (self.x, self.y - 12))
