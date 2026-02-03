import pygame
from building import Building

class BaseZone:
    def __init__(self, width, height, player):
        self.width = width
        self.height = height
        self.player = player
        self.font_title = pygame.font.SysFont(None, 48)
        self.font_text = pygame.font.SysFont(None, 28)
        self.font_small = pygame.font.SysFont(None, 20)
        
        # Caméra / déplacement
        self.camera_x = 0
        self.camera_y = 0
        self.player_x = 100
        self.player_y = 100
        self.player_speed = 5
        
        # Bâtiments du village (gratuits, mais améliorables)
        self.buildings = [
            Building(150, 200, "Armurerie", "Améliore les armes", (150, 50, 50)),
            Building(300, 200, "Forge", "Augmente la vitesse", (100, 100, 100)),
            Building(450, 200, "Marché", "Gagne plus d'or", (200, 200, 50)),
            Building(150, 400, "Temple", "Restaure la vie", (200, 100, 200)),
            Building(300, 400, "Bibliothèque", "Boost XP", (100, 150, 200)),
        ]
        
        # Boutons
        self.launch_mission_btn = pygame.Rect(self.width // 2 - 120, self.height - 100, 240, 60)
        self.menu_btn = pygame.Rect(20, 20, 100, 40)
        self.selected_building = None
        self.message = None
        self.message_timer = 0

    def update(self):
        """Gérer le déplacement du joueur."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.player_y -= self.player_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.player_y += self.player_speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player_x -= self.player_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player_x += self.player_speed
        
        # Contraindre le joueur dans les limites du village
        self.player_x = max(0, min(self.player_x, 600 - 30))
        self.player_y = max(0, min(self.player_y, 600 - 30))
        
        # Mettre à jour la caméra pour suivre le joueur
        self.camera_x = self.player_x - self.width // 2 + 15
        self.camera_y = self.player_y - self.height // 2 + 15
        self.camera_x = max(0, min(self.camera_x, 600 - self.width))
        self.camera_y = max(0, min(self.camera_y, 600 - self.height))

    def draw(self, screen):
        screen.fill((34, 139, 34))  # Vert foncé pour le terrain
        
        # Titre
        title = self.font_title.render("Village - Utilisez les flèches pour vous déplacer", True, (100, 255, 100))
        screen.blit(title, (20, 20))
        
        # Afficher les bâtiments (avec offset caméra)
        for building in self.buildings:
            adjusted_rect = pygame.Rect(building.rect.x - self.camera_x, building.rect.y - self.camera_y, 
                                        building.rect.width, building.rect.height)
            pygame.draw.rect(screen, building.color, adjusted_rect)
            pygame.draw.rect(screen, (255, 255, 255), adjusted_rect, 2)
            
            text = self.font_small.render(building.name, True, (255, 255, 255))
            screen.blit(text, (adjusted_rect.x + 5, adjusted_rect.y + 5))
            
            # Afficher le niveau
            level_text = self.font_small.render(f"Lvl {building.level}", True, (100, 255, 100))
            screen.blit(level_text, (adjusted_rect.x + 5, adjusted_rect.y + 25))
            
            # Afficher le coût du prochain upgrade si possible
            if building.level < building.max_level:
                cost = building.get_upgrade_cost()
                price_text = self.font_small.render(f"+: {cost}g", True, (255, 215, 0))
                screen.blit(price_text, (adjusted_rect.x + 5, adjusted_rect.y + 55))
            else:
                max_text = self.font_small.render("MAX", True, (100, 255, 100))
                screen.blit(max_text, (adjusted_rect.x + 5, adjusted_rect.y + 55))
        
        # Afficher le joueur
        player_screen_x = self.player_x - self.camera_x
        player_screen_y = self.player_y - self.camera_y
        pygame.draw.rect(screen, (0, 100, 255), (player_screen_x, player_screen_y, 30, 30))
        pygame.draw.rect(screen, (255, 255, 255), (player_screen_x, player_screen_y, 30, 30), 2)
        
        # Afficher les stats du joueur en bas
        y_offset = self.height - 120
        stats = [
            f"Niveau: {self.player.level} | XP: {self.player.xp} | Or banké: {self.player.gold}",
        ]
        for stat in stats:
            text = self.font_small.render(stat, True, (255, 255, 255))
            screen.blit(text, (20, y_offset))
            y_offset += 25
        
        # Message temporaire
        if self.message and self.message_timer > 0:
            msg_text = self.font_small.render(self.message, True, (255, 200, 0))
            screen.blit(msg_text, (self.width // 2 - msg_text.get_width() // 2, 100))
            self.message_timer -= 1
        
        # Bouton Lancer Mission
        mouse_pos = pygame.mouse.get_pos()
        hover_launch = self.launch_mission_btn.collidepoint(mouse_pos)
        btn_color = (0, 200, 0) if hover_launch else (0, 150, 0)
        pygame.draw.rect(screen, btn_color, self.launch_mission_btn)
        pygame.draw.rect(screen, (255, 255, 255), self.launch_mission_btn, 2)
        launch_text = self.font_text.render("LANCER MISSION", True, (255, 255, 255))
        screen.blit(launch_text, (self.launch_mission_btn.x + self.launch_mission_btn.width // 2 - launch_text.get_width() // 2,
                                   self.launch_mission_btn.y + self.launch_mission_btn.height // 2 - launch_text.get_height() // 2))
        
        # Bouton Menu
        hover_menu = self.menu_btn.collidepoint(mouse_pos)
        menu_color = (150, 150, 150) if hover_menu else (100, 100, 100)
        pygame.draw.rect(screen, menu_color, self.menu_btn)
        pygame.draw.rect(screen, (255, 255, 255), self.menu_btn, 2)
        menu_text = self.font_small.render("Menu", True, (255, 255, 255))
        screen.blit(menu_text, (self.menu_btn.x + self.menu_btn.width // 2 - menu_text.get_width() // 2,
                                self.menu_btn.y + self.menu_btn.height // 2 - menu_text.get_height() // 2))

    def handle_click(self, pos):
        """Gérer les clics sur les bâtiments et boutons."""
        # Vérifier les boutons
        if self.launch_mission_btn.collidepoint(pos):
            return "launch"
        elif self.menu_btn.collidepoint(pos):
            return "menu"
        
        # Vérifier les bâtiments (avec offset caméra)
        for building in self.buildings:
            adjusted_rect = pygame.Rect(building.rect.x - self.camera_x, building.rect.y - self.camera_y, 
                                        building.rect.width, building.rect.height)
            if adjusted_rect.collidepoint(pos):
                return ("building", building)
        
        return None
    
    def upgrade_building(self, building, banked_gold):
        """Améliorer un bâtiment."""
        cost = building.get_upgrade_cost()
        if building.level < building.max_level and banked_gold >= cost:
            building.upgrade()
            self.message = f"{building.name} amélioré au niveau {building.level}!"
            self.message_timer = 120  # 2 secondes à 60 FPS
            return cost
        elif building.level >= building.max_level:
            self.message = f"{building.name} est au maximum!"
            self.message_timer = 120
        else:
            self.message = f"Or insuffisant! Il vous faut {cost}g"
            self.message_timer = 120
        return 0
