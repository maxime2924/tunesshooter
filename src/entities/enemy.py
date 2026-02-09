import pygame
import random
from core.settings import *
from core.asset_manager import AssetManager

class Enemy(pygame.sprite.Sprite):
    def __init__(self, screen_rect, hp=3, damage=1):
        super().__init__()
        assets = AssetManager()
        try:
            raw_image = assets.get_image("enemy_ranged.png")
            if raw_image:
                self.image = pygame.transform.scale(raw_image, (50, 50)).convert_alpha()
            else:
                self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
                self.image.fill(RED)
        except Exception as e:
            print(f"Error loading enemy sprite: {e}")
            self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
            self.image.fill(RED)
        
        self.rect = self.image.get_rect(center=(random.randint(50, screen_rect.width-50), random.randint(50, screen_rect.height-50)))
        self.speed = 2
        self.screen_rect = screen_rect
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
    
    def update(self, target):
        direction = pygame.math.Vector2(target.rect.center) - pygame.math.Vector2(self.rect.center)
        if direction.length() > 0:
            move = direction.normalize() * self.speed
            self.rect.x += move.x
            self.rect.y += move.y
        if hasattr(self, 'screen_rect') and self.screen_rect:
            self.rect.clamp_ip(self.screen_rect)

    def take_damage(self, amount=1):
        self.hp -= amount
        return self.hp <= 0
    
    def draw_health_bar(self, surface, camera_offset):
        if self.hp >= self.max_hp:
            return
        
        bar_width = 40
        bar_height = 4
        bar_x = self.rect.centerx - bar_width // 2 - camera_offset[0]
        bar_y = self.rect.top - 10 - camera_offset[1]
        
        pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        health_percent = self.hp / self.max_hp
        fill_width = int(bar_width * health_percent)
        
        if health_percent > 0.5:
            color = (0, 255, 0)
        elif health_percent > 0.25:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)
        
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)

