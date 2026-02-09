import pygame
from core.settings import *

class DialogueManager:
    def __init__(self, font):
        self.font = font
        self.active = False
        self.current_dialogue = None
        self.on_option_select = None 

    def start_dialogue(self, name, text, options=None, callback=None):
        self.active = True
        self.current_dialogue = {
            "name": name,
            "text": text,
            "options": options if options else [] 
        }
        self.on_option_select = callback

    def handle_input(self, event):
        if not self.active: return False

        if event.type == pygame.KEYDOWN:
            if self.current_dialogue["options"]:
                idx = -1
                if pygame.K_1 <= event.key <= pygame.K_9:
                    idx = event.key - pygame.K_1
                elif pygame.K_KP1 <= event.key <= pygame.K_KP9:
                    idx = event.key - pygame.K_KP1
                
                if 0 <= idx < len(self.current_dialogue["options"]):
                    _, action_id = self.current_dialogue["options"][idx]
                    if self.on_option_select:
                        self.on_option_select(action_id)
                    return True 
            
            elif event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_e, pygame.K_ESCAPE]:
                self.active = False
                if not self.current_dialogue["options"] and self.on_option_select:
                     self.on_option_select(None)
                self.current_dialogue = None
                return True

        return False

    def draw(self, screen):
        if not self.active or not self.current_dialogue: return

        box_height = 200
        box_margin = 50
        box_rect = pygame.Rect(box_margin, HEIGHT - box_height - 20, WIDTH - 2 * box_margin, box_height)

        pygame.draw.rect(screen, (10, 10, 25), box_rect) 
        pygame.draw.rect(screen, NEON_BLUE, box_rect, 2) 

        text_x = box_rect.x + 20
        current_y = box_rect.y + 15

        name_surf = self.font.render(f"--- {self.current_dialogue['name']} ---", True, GOLD_COLOR)
        screen.blit(name_surf, (text_x, current_y))
        current_y += 40

        lines = self.current_dialogue['text'].split('\\n')
        for line in lines:
            txt_surf = self.font.render(line, True, WHITE)
            screen.blit(txt_surf, (text_x, current_y))
            current_y += 30
        
        current_y += 10

        if self.current_dialogue["options"]:
            for i, (opt_text, _) in enumerate(self.current_dialogue["options"]):
                opt_surf = self.font.render(f"[{i+1}] {opt_text}", True, NEON_GREEN)
                screen.blit(opt_surf, (text_x + 20, current_y))
                current_y += 30
        else:
            hint = self.font.render("[ESPACE] Continuer...", True, (150, 150, 150))
            screen.blit(hint, (box_rect.right - hint.get_width() - 20, box_rect.bottom - 30))
