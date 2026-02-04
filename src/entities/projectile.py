import pygame
from core.settings import *

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, velocity, screen_rect=None, damage=1, is_enemy=False):
        super().__init__()
        size = 6
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = NEON_PINK if is_enemy else NEON_GREEN # Couleurs néon pour le tir
        pygame.draw.circle(self.image, color, (size//2, size//2), size//2)
        
        # Effet "Glow" simple (cercle plus grand transparent)
        # glow = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
        # pygame.draw.circle(glow, (*color, 100), (size, size), size)
        # self.image.blit(glow, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

        self.rect = self.image.get_rect(center=pos)
        self.vel = pygame.math.Vector2(velocity)
        self.screen_rect = screen_rect
        self.damage = damage
        self.is_enemy = is_enemy
        self.trail_color = color # Store color for trail

    def update(self, *args):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        if self.screen_rect and not self.screen_rect.colliderect(self.rect):
            self.kill()
