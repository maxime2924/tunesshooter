import pygame
import random
from entities.enemy import Enemy
from core.asset_manager import AssetManager

class Zombie(Enemy):
    def __init__(self, screen_rect, hp=5, damage=2):
        super().__init__(screen_rect, hp, damage)
        assets = AssetManager()
        img = assets.get_image("enemy_zombie.png")
        if img:
            self.image = pygame.transform.scale(img, (40, 40))
        else:
            self.image.fill((50, 150, 50)) # Green fallback
        
        self.speed = 2 # Plus lent
        self.rect = self.image.get_rect(center=self.rect.center)
        self.hp = hp * 1.5 # Plus de vie (Tank)

class Robot(Enemy):
    def __init__(self, screen_rect, hp=3, damage=1):
        super().__init__(screen_rect, hp, damage)
        assets = AssetManager()
        img = assets.get_image("enemy_robot.png")
        if img:
            self.image = pygame.transform.scale(img, (30, 30))
        else:
            self.image.fill((150, 150, 150)) # Grey fallback
            
        self.speed = 4.5 # Rapide
        self.rect = self.image.get_rect(center=self.rect.center)
        self.hp = hp * 0.8 # Moins de vie (Glass cannon)
