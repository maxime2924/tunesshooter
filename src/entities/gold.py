import pygame
from core.settings import *

class Gold(pygame.sprite.Sprite):
    def __init__(self, pos, value=5):
        super().__init__()
        size = 8
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GOLD_COLOR, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=pos)
        self.value = value
        self.speed = 5
        
    def update(self, player_pos):
        # Magnet Effect
        p_vec = pygame.math.Vector2(player_pos)
        s_vec = pygame.math.Vector2(self.rect.center)
        dist = p_vec.distance_to(s_vec)
        
        if dist < 200: # Magnet Range
            direction = p_vec - s_vec
            if direction.length() > 0:
                self.rect.center += direction.normalize() * self.speed
                self.speed += 0.5 # Accelerate towards player
