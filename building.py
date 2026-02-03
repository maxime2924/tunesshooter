import pygame

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
