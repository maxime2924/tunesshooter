import pygame
import math
from core.settings import *
from entities.entity import Entity

class Building:
    def __init__(self, x, y, name, description, color=(100, 100, 100)):
        self.rect = pygame.Rect(x, y, 80, 80)
        self.name = name
        self.description = description
        self.color = color
        self.level = 0  # Niveau du bâtiment (commence à 0, gratuit)
        self.max_level = 10
        self.upgrade_costs = [0, 20, 40, 70, 110, 160, 220, 290, 370, 460]  # Coût pour chaque niveau

    def get_upgrade_cost(self):
        """Retourne le coût pour upgrader au niveau suivant."""
        if self.level >= self.max_level:
            return 0
        return self.upgrade_costs[self.level] if self.level < len(self.upgrade_costs) else 100 + (self.level * 50)

    def upgrade(self):
        """Améliore le bâtiment d'un niveau."""
        if self.level < self.max_level:
            self.level += 1
            return True
        return False

    def draw(self, surface, font):
        color = self.color
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, 2)
        
        # Afficher le nom
        text = font.render(self.name, True, (255, 255, 255))
        surface.blit(text, (self.rect.x + 5, self.rect.y + 5))
        
        # Afficher le niveau
        level_text = font.render(f"Lvl {self.level}", True, (100, 255, 100))
        surface.blit(level_text, (self.rect.x + 5, self.rect.y + 25))
        
        # Afficher le coût du prochain upgrade si possible
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
        # Animation : LATTICE Coachella (LED Triangles)
        self.pulse_timer += 0.07
        t = pygame.time.get_ticks()
        
        # Base pulse
        pulse = (math.sin(self.pulse_timer) + 1) / 2
        
        # New Coachella effect: Triangle Lattice Overlay
        temp_img = self.original_image.copy()
        w, h = self.image.get_size()
        
        # On dessine des triangles néon sur la pyramide
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        # Scanline effect
        scan_y = int((t // 5) % h) # Cast to int for draw.line
        pygame.draw.line(overlay, (*NEON_BLUE, 100), (0, scan_y), (w, scan_y), 2)
        
        # Lattice triangles
        grid = 40
        for x in range(0, w, grid):
            for y in range(0, h, grid):
                if (x + y + (t//100)*grid) % (grid*3) == 0:
                     pygame.draw.polygon(overlay, (*NEON_PINK, 150), [(x, y+grid), (x+grid//2, y), (x+grid, y+grid)], 1)
        
        temp_img.blit(overlay, (0, 0))
        
        # Glowing tint
        glow = pygame.Surface((w, h), pygame.SRCALPHA)
        color = NEON_BLUE if math.sin(t/500) > 0 else NEON_PINK
        glow.fill((*color, 30 + int(pulse * 40)))
        temp_img.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
        
        self.image = temp_img
