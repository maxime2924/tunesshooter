import pygame
from entities.entity import Entity
from core.settings import *

class Wall(Entity):
    def __init__(self, groups, pos, size, color=(20, 20, 20), border_color=NEON_BLUE):
        super().__init__(groups, pos=pos)
        self.image = pygame.Surface(size)
        self.image.fill(color)
        if border_color:
            pygame.draw.rect(self.image, border_color, (0, 0, size[0], size[1]), 2)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect

class Obstacle(Entity):
    def __init__(self, groups, pos, size, color=(50, 50, 50)):
        super().__init__(groups, pos=pos)
        self.image = pygame.Surface(size)
        self.image.fill(color)
        # Random visual detail to look like "crate" or "debris"
        pygame.draw.rect(self.image, (min(255, color[0]+20), min(255, color[1]+20), min(255, color[2]+20)), (5, 5, size[0]-10, size[1]-10), 2)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect
