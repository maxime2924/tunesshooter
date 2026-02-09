from core.settings import *
from core.asset_manager import AssetManager
from states.scenes import Scene
import math
import random

class MainMenu(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.width = manager.screen.get_width()
        self.height = manager.screen.get_height()
        assets = AssetManager()
        
        self.font_title = assets.get_font(None, 84)
        self.font_subtitle = assets.get_font(None, 28)
        self.font_btn = assets.get_font(None, 40)
        
        self.time = 0
        self.pulse = 0
        
        cx, cy = self.width // 2, self.height // 2
        
        bw = 300
        bh = 70
        spacing = 25
        start_y = cy + 50
        
        self.play_btn = pygame.Rect(cx - bw // 2, start_y, bw, bh)
        self.settings_btn = pygame.Rect(cx - bw // 2, start_y + bh + spacing, bw, bh)
        self.quit_btn = pygame.Rect(cx - bw // 2, start_y + (bh + spacing) * 2, bw, bh)
        
        self.particles = []
        for _ in range(50):
            self.particles.append({
                'x': random.randint(0, self.width),
                'y': random.randint(0, self.height),
                'speed': random.uniform(0.5, 2),
                'size': random.randint(1, 3)
            })

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

    def update(self):
        self.time += 0.05
        self.pulse = abs(math.sin(self.time)) * 20
        
        for p in self.particles:
            p['y'] += p['speed']
            if p['y'] > self.height:
                p['y'] = 0
                p['x'] = random.randint(0, self.width)

    def draw(self, screen):
        screen.fill((10, 10, 30))
        
        # gradient
        for y in range(self.height):
            progress = y / self.height
            r = int(10 + progress * 15)
            g = int(10 + progress * 20)
            b = int(30 + progress * 40)
            pygame.draw.line(screen, (r, g, b), (0, y), (self.width, y))
        
        for p in self.particles:
            alpha = int(150 + 105 * math.sin(self.time + p['x'] * 0.01))
            color = (0, alpha, alpha)
            pygame.draw.circle(screen, color, (int(p['x']), int(p['y'])), p['size'])
        
        title_text = "TUNESHOOTER"
        
        # glow
        for offset in [6, 4, 2]:
            glow_color = (int(255 * (offset / 6)), 0, int(255 * (offset / 6)))
            glow_surf = self.font_title.render(title_text, True, glow_color)
            glow_rect = glow_surf.get_rect(center=(self.width // 2, 120))
            screen.blit(glow_surf, glow_rect)
        
        title_surf = self.font_title.render(title_text, True, NEON_PINK)
        title_rect = title_surf.get_rect(center=(self.width // 2, 120))
        screen.blit(title_surf, title_rect)
        
        subtitle_text = "Cyberpunk Rhythm Shooter"
        subtitle_color = (100 + int(self.pulse), 200 + int(self.pulse), 255)
        subtitle_surf = self.font_subtitle.render(subtitle_text, True, subtitle_color)
        subtitle_rect = subtitle_surf.get_rect(center=(self.width // 2, 190))
        screen.blit(subtitle_surf, subtitle_rect)
        
        line_y = 240
        line_width = 400
        pygame.draw.line(screen, NEON_BLUE, 
                        (self.width // 2 - line_width // 2, line_y),
                        (self.width // 2 + line_width // 2, line_y), 2)
        
        game_started = self.manager.shared_data.get('game_started', False)
        play_label = "CONTINUE" if game_started else "NEW GAME"
        
        buttons = [
            (self.play_btn, play_label, NEON_GREEN, "▶"),
            (self.settings_btn, "SETTINGS", NEON_BLUE, "⚙"),
            (self.quit_btn, "QUIT", NEON_PINK, "✕")
        ]
        
        mouse_pos = pygame.mouse.get_pos()
        
        for btn, label, color, icon in buttons:
            hover = btn.collidepoint(mouse_pos)
            
            if hover:
                pygame.draw.rect(screen, (color[0] // 3, color[1] // 3, color[2] // 3), btn, border_radius=10)
                glow_rect = btn.inflate(10, 10)
                pygame.draw.rect(screen, (color[0] // 2, color[1] // 2, color[2] // 2), glow_rect, 3, border_radius=12)
            else:
                pygame.draw.rect(screen, (20, 20, 40), btn, border_radius=10)
            
            border_color = color if hover else (color[0] // 2, color[1] // 2, color[2] // 2)
            pygame.draw.rect(screen, border_color, btn, 3, border_radius=10)
            
            icon_surf = self.font_btn.render(icon, True, color if hover else border_color)
            icon_x = btn.x + 30
            icon_y = btn.y + btn.height // 2 - icon_surf.get_height() // 2
            screen.blit(icon_surf, (icon_x, icon_y))
            
            text_color = WHITE if hover else (180, 180, 200)
            text = self.font_btn.render(label, True, text_color)
            text_x = btn.x + btn.width // 2 - text.get_width() // 2 + 20
            text_y = btn.y + btn.height // 2 - text.get_height() // 2
            screen.blit(text, (text_x, text_y))
