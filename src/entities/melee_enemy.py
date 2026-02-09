import pygame
import random
from core.settings import *
from core.asset_manager import AssetManager

class MeleeEnemy(pygame.sprite.Sprite):
    def __init__(self, screen_rect, hp=5, damage=2):
        super().__init__()
        assets = AssetManager()
        
        try:
            raw_image = assets.get_image("enemy_melee.png")
            if raw_image:
                self.image = pygame.transform.scale(raw_image, (80, 80)).convert_alpha()
            else:
                self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
                self.image.fill((255, 50, 50))
        except Exception as e:
            print(f"Error loading melee enemy sprite: {e}")
            self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
            self.image.fill((255, 50, 50))
        
        self.rect = self.image.get_rect(center=(random.randint(50, screen_rect.width-50), random.randint(50, screen_rect.height-50)))
        self.speed = 3
        self.screen_rect = screen_rect
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
        self.attack_range = 40
        self.attack_cooldown = 1000
        self.last_attack = 0
    
    def update(self, target):
        direction = pygame.math.Vector2(target.rect.center) - pygame.math.Vector2(self.rect.center)
        distance = direction.length()
        
        if distance > self.attack_range:
            if direction.length() > 0:
                move = direction.normalize() * self.speed
                self.rect.x += move.x
                self.rect.y += move.y
        
        if hasattr(self, 'screen_rect') and self.screen_rect:
            self.rect.clamp_ip(self.screen_rect)
    
    def can_attack(self, target, now):
        distance = pygame.math.Vector2(target.rect.center).distance_to(self.rect.center)
        return distance <= self.attack_range and (now - self.last_attack) >= self.attack_cooldown
    
    def attack(self, target, now):
        if self.can_attack(target, now):
            self.last_attack = now
            return self.damage
        return 0
    
    def take_damage(self, amount=1):
        self.hp -= amount
        return self.hp <= 0
    
    def draw_health_bar(self, surface, camera_offset):
        if self.hp >= self.max_hp:
            return
        
        bar_width = 50
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
