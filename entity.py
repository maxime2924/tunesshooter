import pygame
import math
import os
from asset_manager import AssetManager
from settings import *

class Entity(pygame.sprite.Sprite):
    def __init__(self, groups, image=None, pos=(0,0), scale=None):
        super().__init__(groups)
        if image:
             self.image = image
             if scale:
                 self.image = pygame.transform.scale(self.image, scale)
             self.rect = self.image.get_rect(topleft=pos)
             # Hitbox plus petite pour "profondeur" (bas de l'objet)
             self.hitbox = pygame.Rect(self.rect.x, self.rect.bottom - 20, self.rect.width, 20)
        else:
             self.image = pygame.Surface((32, 32))
             self.image.fill(WHITE)
             self.rect = self.image.get_rect(topleft=pos)
             self.hitbox = self.rect

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
        # Animation DJ Coachella: Bobbing + Slide
        t = pygame.time.get_ticks()
        self.rect.y = self.start_y + math.sin(t / 150) * 8
        self.rect.x = self.start_x + math.cos(t / 300) * 15 # Slide left/right mixing

def separate_sprites(a: pygame.sprite.Sprite, b: pygame.sprite.Sprite, push_a: bool = True, push_b: bool = True):
    """Sépare deux sprites qui se chevauchent (AABB).
    - Si push_a et push_b sont True, on déplace les deux de moitié.
    - Si seul push_b est True, on déplace seulement b (utile pour pousser les ennemis hors du joueur).
    """
    overlap = a.rect.clip(b.rect)
    if overlap.width == 0 or overlap.height == 0:
        return

    # Choisir la plus petite pénétration (x ou y)
    if overlap.width < overlap.height:
        # Séparer sur l'axe X
        if a.rect.centerx < b.rect.centerx:
            # a à gauche, b à droite
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
        # Séparer sur l'axe Y
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
