import pygame
import random
from core.settings import *
from core.asset_manager import AssetManager

class Enemy(pygame.sprite.Sprite):
    def __init__(self, screen_rect, hp=3, damage=1):
        super().__init__()
        assets = AssetManager()
        # On tente de charger une image si elle existe, sinon carré rouge
        # Pour l'instant on garde le carré rouge s'il n'y a pas d'image spécifique prête
        # Mais préparons le terrain pour 'enemy.png' qui était dans la liste
        try:
            self.image = assets.get_image("enemy.png")
            self.image = pygame.transform.scale(self.image, (30, 30))
        except:
             self.image = pygame.Surface((30, 30))
             self.image.fill(RED)
        
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

