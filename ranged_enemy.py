import pygame
import random
import math
from settings import *
from asset_manager import AssetManager

class RangedEnemy(pygame.sprite.Sprite):
    def __init__(self, screen_rect, hp=2, damage=1):
        super().__init__()
        # TODO: Avoir un asset spécifique pour le ranged
        self.image = pygame.Surface((25, 25))
        self.image.fill((255, 165, 0))  # orange legacy
        
        self.rect = self.image.get_rect(center=(random.randint(50, screen_rect.width-50), random.randint(50, screen_rect.height-50)))
        self.speed = 1
        self.screen_rect = screen_rect
        self.hp = hp
        self.damage = damage
        # Tir
        self.last_shot = 0
        self.shot_cooldown = 1500
        self.projectile_speed = 5

    def update(self, target):
        # Se rapprocher du joueur mais moins vite
        direction = pygame.math.Vector2(target.rect.center) - pygame.math.Vector2(self.rect.center)
        if direction.length() > 0:
            move = direction.normalize() * self.speed
            self.rect.x += move.x
            self.rect.y += move.y
        # Empêcher de sortir de l'écran
        if hasattr(self, 'screen_rect') and self.screen_rect:
            self.rect.clamp_ip(self.screen_rect)

    def shoot(self, target, now):
        """Return a projectile aimed at target or None if on cooldown."""
        if now - self.last_shot < self.shot_cooldown:
            return None
        
        from projectile import Projectile
        start = pygame.math.Vector2(self.rect.center)
        target_pos = pygame.math.Vector2(target.rect.center)
        direction = target_pos - start
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        velocity = direction.normalize() * self.projectile_speed
        self.last_shot = now
        return Projectile(self.rect.center, velocity, self.screen_rect, damage=max(1, int(self.damage * 0.5)), is_enemy=True)

    def take_damage(self, amount=1):
        self.hp -= amount
        return self.hp <= 0
