from core.settings import *
from core.asset_manager import AssetManager
from states.scenes import Scene

class MainMenu(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.width = WIDTH
        self.height = HEIGHT
        assets = AssetManager()
        
        self.font_title = assets.get_font(None, 72)
        self.font_btn = assets.get_font(None, 36)
        
        # Boutons
        cx, cy = self.width // 2, self.height // 2
        self.play_btn = pygame.Rect(cx - 100, cy - 50, 200, 60)
        self.settings_btn = pygame.Rect(cx - 100, cy + 30, 200, 60)
        self.quit_btn = pygame.Rect(cx - 100, cy + 110, 200, 60)

    def handle_input(self, events):
        game_started = self.manager.shared_data.get('game_started', False)
        
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                 if game_started:
                     self.manager.switch_to("hub")
                 else:
                     self.manager.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.play_btn.collidepoint(event.pos):
                    if not game_started:
                        self.manager.shared_data['game_started'] = True
                    self.manager.switch_to("hub")
                elif self.settings_btn.collidepoint(event.pos):
                    print("Settings not implemented")
                elif self.quit_btn.collidepoint(event.pos):
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

    def draw(self, screen):
        screen.fill((20, 20, 30))
        
        # Titre
        title_surf = self.font_title.render("DAFT PUNK: EXTRACTION", True, NEON_PINK)
        screen.blit(title_surf, (self.width // 2 - title_surf.get_width() // 2, 50))
        
        # Boutons
        game_started = self.manager.shared_data.get('game_started', False)
        play_label = "RESUME" if game_started else "PLAY"
        
        buttons = [
            (self.play_btn, play_label, NEON_GREEN),
            (self.settings_btn, "SETTINGS", BLUE),
            (self.quit_btn, "QUIT", RED)
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        for btn, label, color in buttons:
            hover = btn.collidepoint(mouse_pos)
            draw_color = color if not hover else (min(255, color[0]+50), min(255, color[1]+50), min(255, color[2]+50))
            
            pygame.draw.rect(screen, draw_color, btn, border_radius=5)
            pygame.draw.rect(screen, WHITE, btn, 2, border_radius=5)
            
            text = self.font_btn.render(label, True, BLACK if hover else WHITE)
            screen.blit(text, (btn.x + btn.width // 2 - text.get_width() // 2, btn.y + btn.height // 2 - text.get_height() // 2))
