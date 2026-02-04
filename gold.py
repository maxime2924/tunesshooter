import pygame
from settings import *

class Gold(pygame.sprite.Sprite):
    def __init__(self, pos, value=5):
        super().__init__()
        size = 8
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GOLD_COLOR, (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=pos)
        self.value = value
