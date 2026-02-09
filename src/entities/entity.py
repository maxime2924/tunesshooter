import pygame
import math
import os
from core.asset_manager import AssetManager
from core.settings import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, groups, image=None, pos=(0,0), scale=None):
        super().__init__(groups)
        if image:
             self.image = image
             if scale:
                 self.image = pygame.transform.scale(self.image, scale)
             self.rect = self.image.get_rect(center=pos)
        else:
             self.image = pygame.Surface((32, 32))
             self.image.fill(WHITE)
             self.rect = self.image.get_rect(center=pos)

    def take_damage(self, amount):
        if hasattr(self, 'hp'):
            self.hp -= amount
            return self.hp <= 0
        return False

class AnimatedEntity(Entity):
    def __init__(self, groups, image_path, pos, scale=None):
        assets = AssetManager()
        img = assets.get_image(image_path)
        super().__init__(groups, image=img, pos=pos, scale=scale)
        self.start_y = self.rect.y
        self.start_x = self.rect.x
    
    def update(self):
        # DJ bobbing animation
        t = pygame.time.get_ticks()
        self.rect.y = self.start_y + math.sin(t / 150) * 8
        self.rect.x = self.start_x + math.cos(t / 300) * 15

def separate_sprites(a: pygame.sprite.Sprite, b: pygame.sprite.Sprite, push_a: bool = True, push_b: bool = True):
    # separates overlapping sprites
    overlap = a.rect.clip(b.rect)
    if overlap.width == 0 or overlap.height == 0:
        return

    if overlap.width < overlap.height:
        # push on X axis
        if a.rect.centerx < b.rect.centerx:
            move_x = overlap.width
            move_a = -move_x // 2 if push_a and push_b else (-move_x if push_a else 0)
            move_b = move_x // 2 if push_a and push_b else (move_x if push_b else 0)
        else:
            move_x = overlap.width
            move_a = move_x // 2 if push_a and push_b else (move_x if push_a else 0)
            move_b = -move_x // 2 if push_a and push_b else (-move_x if push_b else 0)

        a.rect.x += int(move_a)
        b.rect.x += int(move_b)
    else:
        # push on Y
        if a.rect.centery < b.rect.centery:
            move_y = overlap.height
            move_a = -move_y // 2 if push_a and push_b else (-move_y if push_a else 0)
            move_b = move_y // 2 if push_a and push_b else (move_y if push_b else 0)
        else:
            move_y = overlap.height
            move_a = move_y // 2 if push_a and push_b else (move_y if push_a else 0)
            move_b = -move_y // 2 if push_a and push_b else (-move_y if push_b else 0)

        a.rect.y += int(move_a)
        b.rect.y += int(move_b)
