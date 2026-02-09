import pygame
from states.scenes import Scene
from core.settings import *
from core.asset_manager import AssetManager

class PauseMenu(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.assets = AssetManager()
        self.font = self.assets.get_font(None, 48)
        self.previous_scene = None
        
        cx, cy = WIDTH // 2, HEIGHT // 2
        self.resume_btn = pygame.Rect(cx - 150, cy - 60, 300, 50)
        self.abandon_btn = pygame.Rect(cx - 150, cy + 20, 300, 50)
        self.quit_btn = pygame.Rect(cx - 150, cy + 100, 300, 50)

    def on_enter(self, **kwargs):
        self.previous_scene = kwargs.get('previous_scene')

    def handle_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._resume()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.resume_btn.collidepoint(event.pos):
                    self._resume()
                elif self.abandon_btn.collidepoint(event.pos):
                    self.manager.switch_to("hub")
                elif self.quit_btn.collidepoint(event.pos):
                    pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _resume(self):
        if self.previous_scene:
            self.manager.current_scene = self.previous_scene

    def draw(self, screen):
        if self.previous_scene:
            self.previous_scene.draw(screen)
        
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        self._draw_btn(screen, self.resume_btn, "Reprendre", NEON_GREEN)
        self._draw_btn(screen, self.abandon_btn, "Abandonner Mission", RED)
        self._draw_btn(screen, self.quit_btn, "Quitter Jeu", WHITE)

    def _draw_btn(self, screen, rect, text, color):
        mouse_pos = pygame.mouse.get_pos()
        hover = rect.collidepoint(mouse_pos)
        draw_color = color if not hover else (min(255, color[0]+50), min(255, color[1]+50), min(255, color[2]+50))
        
        pygame.draw.rect(screen, draw_color, rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, rect, 2, border_radius=10)
        
        txt_surf = self.font.render(text, True, BLACK if hover else WHITE)
        screen.blit(txt_surf, (rect.centerx - txt_surf.get_width()//2, rect.centery - txt_surf.get_height()//2))
