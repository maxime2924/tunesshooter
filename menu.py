import pygame

class MainMenu:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font_title = pygame.font.SysFont(None, 72)
        self.font_btn = pygame.font.SysFont(None, 36)
        self.font_small = pygame.font.SysFont(None, 24)
        
        # Boutons
        self.play_btn = pygame.Rect(self.width // 2 - 100, self.height // 2 - 50, 200, 60)
        self.settings_btn = pygame.Rect(self.width // 2 - 100, self.height // 2 + 30, 200, 60)
        self.quit_btn = pygame.Rect(self.width // 2 - 100, self.height // 2 + 110, 200, 60)
        
        self.hovered = None

    def draw(self, screen):
        screen.fill((20, 20, 30))
        
        # Titre
        title = self.font_title.render("Vampire Survivor", True, (255, 100, 100))
        screen.blit(title, (self.width // 2 - title.get_width() // 2, 50))
        
        # Boutons
        buttons = [
            (self.play_btn, "PLAY", (0, 150, 0)),
            (self.settings_btn, "SETTINGS", (100, 100, 150)),
            (self.quit_btn, "QUIT", (150, 0, 0))
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        for btn, label, color in buttons:
            hover = btn.collidepoint(mouse_pos)
            btn_color = tuple(min(255, c + 50) for c in color) if hover else color
            pygame.draw.rect(screen, btn_color, btn)
            pygame.draw.rect(screen, (255, 255, 255), btn, 2)
            text = self.font_btn.render(label, True, (255, 255, 255))
            screen.blit(text, (btn.x + btn.width // 2 - text.get_width() // 2, btn.y + btn.height // 2 - text.get_height() // 2))

    def handle_click(self, pos):
        if self.play_btn.collidepoint(pos):
            return "play"
        elif self.settings_btn.collidepoint(pos):
            return "settings"
        elif self.quit_btn.collidepoint(pos):
            return "quit"
        return None
