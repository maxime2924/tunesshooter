import pygame
import math
from core.settings import *
from entities.entity import Entity

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
        pygame.draw.rect(self.image, (min(255, color[0]+20), min(255, color[1]+20), min(255, color[2]+20)), (5, 5, size[0]-10, size[1]-10), 2)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect

class Building:
    def __init__(self, x, y, name, description, color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.name = name
        self.description = description
        self.color = color
        self.level = 0
        self.max_level = 10
        self.upgrade_costs = [0, 20, 40, 70, 110, 160, 220, 290, 370, 460]

    def get_upgrade_cost(self):
        if self.level >= self.max_level:
            return 0
        return self.upgrade_costs[self.level] if self.level < len(self.upgrade_costs) else 100 + (self.level * 50)

    def upgrade(self):
        if self.level < self.max_level:
            self.level += 1
            return True
        return False

    def draw(self, surface, font):
        color = self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        
        text = font.render(self.name, True, (255, 255, 255))
        surface.blit(text, (self.rect.x + 5, self.rect.y + 5))
        
        level_text = font.render(f"Lvl {self.level}", True, (100, 255, 100))
        surface.blit(level_text, (self.rect.x + 5, self.rect.y + 25))
        
        if self.level < self.max_level:
            cost = self.get_upgrade_cost()
            price_text = font.render(f"+: {cost}g", True, (255, 215, 0))
            surface.blit(price_text, (self.rect.x + 5, self.rect.y + 55))

    def collidepoint(self, pos):
        return self.rect.collidepoint(pos)

class Pyramid(Entity):
    def __init__(self, groups, image, pos, scale):
        super().__init__(groups, image=image, pos=pos, scale=scale)
        self.original_image = self.image.copy()
        self.pulse_timer = 0

    def update(self):
        self.pulse_timer += 0.07
        t = pygame.time.get_ticks()
        
        pulse = (math.sin(self.pulse_timer) + 1) / 2
        
        temp_img = self.original_image.copy()
        w, h = self.image.get_size()
        
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        scan_y = int((t // 5) % h)
        pygame.draw.line(overlay, (*NEON_BLUE, 100), (0, scan_y), (w, scan_y), 2)
        
        grid = 40
        for x in range(0, w, grid):
            for y in range(0, h, grid):
                if (x + y + (t//100)*grid) % (grid*3) == 0:
                     pygame.draw.polygon(overlay, (*NEON_PINK, 150), [(x, y+grid), (x+grid//2, y), (x+grid, y+grid)], 1)
        
        temp_img.blit(overlay, (0, 0))
        
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        color = NEON_BLUE if math.sin(t/500) > 0 else NEON_PINK
        glow.fill((*color, 30 + int(pulse * 40)))
        temp_img.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
        self.image = temp_img
