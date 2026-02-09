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
        p_vec = pygame.math.Vector2(player_pos)
        s_vec = pygame.math.Vector2(self.rect.center)
        dist = p_vec.distance_to(s_vec)
        
        if dist < 200:
            direction = p_vec - s_vec
            if direction.length() > 0:
                self.rect.center += direction.normalize() * self.speed
                self.speed += 0.5

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, velocity, screen_rect=None, damage=1, is_enemy=False):
        super().__init__()
        size = 6
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = NEON_PINK if is_enemy else NEON_GREEN
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        
        self.rect = self.image.get_rect(center=pos)
        self.vel = pygame.math.Vector2(velocity)
        self.screen_rect = screen_rect
        self.damage = damage
        self.is_enemy = is_enemy
        self.trail_color = color

    def update(self, *args):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        if self.screen_rect and not self.screen_rect.colliderect(self.rect):
            self.kill()
