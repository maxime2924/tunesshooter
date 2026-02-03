import pygame
import random

class Enemy(pygame.sprite.Sprite):
    def __init__(self, screen_rect, hp=3, damage=1):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=(random.randint(50, screen_rect.width-50), random.randint(50, screen_rect.height-50)))
        self.speed = 2
        self.screen_rect = screen_rect
        self.hp = hp
        self.damage = damage
    
    def update(self, target):
        direction = pygame.math.Vector2(target.rect.center) - pygame.math.Vector2(self.rect.center)
        if direction.length() > 0:
            move = direction.normalize() * self.speed
            self.rect.x += move.x
            self.rect.y += move.y
        # Empêcher de sortir de l'écran
        if hasattr(self, 'screen_rect') and self.screen_rect:
            self.rect.clamp_ip(self.screen_rect)

    def take_damage(self, amount=1):
        self.hp -= amount
        return self.hp <= 0
