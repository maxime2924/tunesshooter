import pygame
from settings import *
from shop_system import Merchant, ShopItem
from asset_manager import AssetManager
from camera import CameraGroup
from entity import Entity, AnimatedEntity
import math


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
        scan_y = (t // 5) % h
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

class BaseZone:
    def __init__(self, width, height, player):
        self.width = width
        self.height = height
        self.player = player
        self.assets = AssetManager()
        
        # Camera & Groupes
        self.camera_group = CameraGroup()
        self.interactables = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group() 
        self.npcs = pygame.sprite.Group()

        # FOND : IDENTIQUE AUX MISSIONS (Grass) - demandé par l'utilisateur
        self.camera_group.set_tiled_background("grass.png", MAP_WIDTH, MAP_HEIGHT)
        
        # Position de spawn sécurisée
        self.player.kill() 
        self.player.rect.center = (MAP_WIDTH // 2, MAP_HEIGHT // 2 + 500)
        self.camera_group.add(self.player)
        
        # 1. PYRAMIDE (Plus petite)
        pyramid_img = self.assets.get_image("pyramid.png")
        if pyramid_img:
            # Scale down significantly
            new_size = (300, 200) # Much smaller
            px = MAP_WIDTH // 2 - new_size[0] // 2
            py = MAP_HEIGHT // 2 - new_size[1] // 2
            self.pyramid = Pyramid([self.camera_group, self.collision_sprites], image=pyramid_img, pos=(px, py), scale=new_size)
            self.pyramid.hitbox = pygame.Rect(px + 40, py + 80, new_size[0] - 80, new_size[1] - 80)
            
            # DJ Animation (Smaller)
            dj_x = px + new_size[0] // 2 - 20
            dj_y = py + new_size[1] // 3 
            self.dj = AnimatedEntity([self.camera_group], "daft_dj.png", pos=(dj_x, dj_y), scale=(40, 40))
            
            # Mission Launch Zone
            self.mission_rect = pygame.Rect(px + new_size[0]//2 - 60, py + new_size[1] + 10, 120, 60)
        else:
            self.mission_rect = pygame.Rect(MAP_WIDTH//2 - 50, MAP_HEIGHT//2 - 50, 100, 100)

        # 2. MARCHANDS (4 Distincts, séparés sur la map)
        self.merchants_data = [] 

        # A. Armes (West)
        m_weap_img = self.assets.get_image("merchant_stand.png") # Reuse or gen new
        self._add_merchant(m_weap_img, (MAP_WIDTH//2 - 800, MAP_HEIGHT//2), "Armurier Cyber", "Le son, c'est l'arme ultime. Mais un laser ça aide.", "damage")

        # B. Base / Biotech (East)
        m_base_img = self.assets.get_image("merchant_base_upgrade.png")
        self._add_merchant(m_base_img, (MAP_WIDTH//2 + 800, MAP_HEIGHT//2), "Ingénieur Système", "Optimise tes circuits. Deviens meilleur, plus rapide, plus fort.", "hp")

        # C. Véhicules (South-West)
        m_vehicle_img = self.assets.get_image("merchant_vehicle_garage.png") 
        self._add_merchant(m_vehicle_img, (MAP_WIDTH//2 - 600, MAP_HEIGHT//2 + 800), "Garagiste", "Ta mobylette est naze. J'ai des moteurs ioniques.", "speed")
        
        # D. Quêtes Secondaires (South-East)
        # Note: Ce marchand donne des items "Quêtes" ou buffs speciaux
        m_quest_img = self.assets.get_image("merchant_stand.png")
        self._add_merchant(m_quest_img, (MAP_WIDTH//2 + 600, MAP_HEIGHT//2 + 800), "Fixer Info", "J'ai des infos sur des cibles prioritaires. Ca va te coûter.", "passive_gold")


        # 3. LORE ZONE (North)
        # Zone avec des NPCs pour l'histoire
        self.lore_npcs = []
        npc_data = [
            ("L'Ancien", "J'ai vu le premier concert... C'était légendaire.", (MAP_WIDTH//2 - 200, MAP_HEIGHT//2 - 600)),
            ("Rescapée", "Ils ont pris mon frère. Il faut nettoyer la Zone 4.", (MAP_WIDTH//2 + 200, MAP_HEIGHT//2 - 600)),
            ("Fan Hardcore", "Si tu trouves un vinyle original, je te le rachete !", (MAP_WIDTH//2, MAP_HEIGHT//2 - 700))
        ]
        
        npc_img = self.assets.get_image("punk_npc.png") # Fallback or specific
        for name, txt, pos in npc_data:
            npc = Entity([self.camera_group, self.interactables, self.npcs], image=npc_img, pos=pos, scale=(50, 80))
            self.lore_npcs.append({"sprite": npc, "name": name, "dialogue": txt})

        # 4. ENTRÉE BACKSTAGE (Loge)
        self.backstage_rect = pygame.Rect(MAP_WIDTH // 2 - 100, MAP_HEIGHT // 2 - 850, 200, 100)


        # UI State
        self.font = pygame.font.SysFont("arial", 24)
        self.dialogue_ui = None 
        self.active_merchant = None
        self.show_shop_ui = False
        self.show_mission_menu = False # Menu de choix mission

        # Quests State
        self.unlocked_missions = ["Extraction Illimitée"] # Default
        
    def _add_merchant(self, image, pos, name, text, type_filter):
        m_sprite = Entity([self.camera_group, self.interactables, self.collision_sprites], image=image, pos=pos, scale=(200, 200))
        m_obj = Merchant()
        # Filter items vaguely based on type for flavor (in a real game we'd have specific items lists)
        m_obj.items = [item for item in m_obj.items if item.effect_type == type_filter or type_filter == "all"]
        # Add basic items back if empty
        if not m_obj.items:
             m_obj.items = [ShopItem(f"Module {type_filter}", 100, 1, type_filter, 1, "Upgrade standard")]
             
        self.merchants_data.append({"sprite": m_sprite, "obj": m_obj, "name": name, "dialogue": text})

    def update(self):
        # Update animations
        for sprite in self.camera_group:
             if hasattr(sprite, 'update'):
                 sprite.update()
        
        if self.show_shop_ui or (self.dialogue_ui and self.dialogue_ui.get("options")) or self.show_mission_menu:
            return 

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        speed = 8 # Hub speed fast
        
        if keys[pygame.K_z] or keys[pygame.K_UP]: dy -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += speed
        if keys[pygame.K_q] or keys[pygame.K_LEFT]: dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += speed
        
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # Collisions
        self.player.rect.x += dx
        for sprite in self.collision_sprites:
            if hasattr(sprite, 'hitbox') and self.player.rect.colliderect(sprite.hitbox):
                 if dx > 0: self.player.rect.right = sprite.hitbox.left
                 if dx < 0: self.player.rect.left = sprite.hitbox.right
        
        self.player.rect.y += dy
        for sprite in self.collision_sprites:
            if hasattr(sprite, 'hitbox') and self.player.rect.colliderect(sprite.hitbox):
                   if dy > 0: self.player.rect.bottom = sprite.hitbox.top
                   if dy < 0: self.player.rect.top = sprite.hitbox.bottom
        
        self.player.rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))

    def handle_input(self, event):
        # 1. KEYBOARD Input
        if event.type == pygame.KEYDOWN:
            # Global Exit (ESC)
            if event.key == pygame.K_ESCAPE:
                if self.show_shop_ui:
                    self.show_shop_ui = False
                    self.active_merchant = None
                    return True
                if self.dialogue_ui:
                    self.dialogue_ui = None
                    return True
                if self.show_mission_menu:
                    self.show_mission_menu = False
                    return True

            # INTERACTION (E)
            if event.key == pygame.K_e:
                if self.show_mission_menu: return
                if not self.show_shop_ui and not self.dialogue_ui:
                    # Merchants
                    for m_data in self.merchants_data:
                        if self.player.rect.colliderect(m_data["sprite"].hitbox.inflate(100, 100)):
                            self.dialogue_ui = {
                                "text": m_data["dialogue"], 
                                "merchant": m_data["obj"], 
                                "name": m_data["name"],
                                "options": True
                            }
                            return
                    
                    # Lore NPCs
                    for npc in self.lore_npcs:
                         if self.player.rect.colliderect(npc["sprite"].rect.inflate(60, 60)):
                              self.dialogue_ui = {"text": npc["dialogue"], "name": npc["name"]}
                              if "Rescapée" in npc["name"] and "Mission Sauvetage" not in self.unlocked_missions:
                                  self.unlocked_missions.append("Mission Sauvetage")
                                  self.dialogue_ui["text"] += " (Nouvelle mission débloquée !)"
                              return

                    # Mission Check
                    if hasattr(self, 'mission_rect') and self.player.rect.colliderect(self.mission_rect):
                        self.show_mission_menu = True
                        return 
                    
                    # Backstage Check
                    if hasattr(self, 'backstage_rect') and self.player.rect.colliderect(self.backstage_rect):
                        return "enter_backstage"

            # Mission Menu Choices
            if self.show_mission_menu:
                if pygame.K_1 <= event.key <= pygame.K_9:
                     idx = event.key - pygame.K_1
                     if idx < len(self.unlocked_missions):
                          self.show_mission_menu = False
                          self.selected_mission = self.unlocked_missions[idx]
                          return "launch_choice"
                elif event.key == pygame.K_ESCAPE:
                    self.show_mission_menu = False

            # Dialogue Choices
            elif self.dialogue_ui and self.dialogue_ui.get("options"):
                 if event.key == pygame.K_1: # Converser
                     self.dialogue_ui["text"] = "C'est dur de survivre ici... Mais la musique nous tient en vie."
                     self.dialogue_ui["options"] = False 
                 elif event.key == pygame.K_2: # Acheter
                     self.active_merchant = self.dialogue_ui["merchant"]
                     self.show_shop_ui = True
                     self.dialogue_ui = None
            
            # Simple Dialogue Continue
            elif self.dialogue_ui and not self.dialogue_ui.get("options"):
                 if event.key in [pygame.K_SPACE, pygame.K_e, pygame.K_RETURN]:
                     self.dialogue_ui = None
            
            # Shop Select
            elif self.show_shop_ui:
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                     idx = event.key - pygame.K_1
                     if self.active_merchant and 0 <= idx < len(self.active_merchant.items):
                        item = self.active_merchant.items[idx]
                        self.active_merchant.buy_item(item, self.player)

        # 2. MOUSE Input
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.show_shop_ui:
                 if hasattr(self, 'current_shop_buttons'):
                    for rect, item in self.current_shop_buttons:
                        if rect.collidepoint(event.pos):
                            if item == "close":
                                self.show_shop_ui = False
                                self.active_merchant = None
                                return True
                            self.active_merchant.buy_item(item, self.player)
                            return True
            
            if self.dialogue_ui and not self.dialogue_ui.get("options"):
                 self.dialogue_ui = None

        return None

    def draw(self, screen):
        self.camera_group.custom_draw(self.player)

        # Labels
        if not self._is_ui_open():
            for m_data in self.merchants_data:
                if self.player.rect.colliderect(m_data["sprite"].hitbox.inflate(120, 120)):
                    self.draw_interaction_prompt(screen, f"[E] {m_data['name']}", m_data["sprite"].rect)
            
            for npc in self.lore_npcs:
                 if self.player.rect.colliderect(npc["sprite"].rect.inflate(80, 80)):
                      self.draw_interaction_prompt(screen, "[E] Parler", npc["sprite"].rect)

            if hasattr(self, 'mission_rect') and self.player.rect.colliderect(self.mission_rect):
                self.draw_interaction_prompt(screen, "[E] MISSIONS", self.mission_rect, color=NEON_PINK)
            
            if hasattr(self, 'backstage_rect') and self.player.rect.colliderect(self.backstage_rect):
                self.draw_interaction_prompt(screen, "[E] ENTRER LOGES", self.backstage_rect, color=GOLD_COLOR)

        if self.show_mission_menu:
            self.draw_mission_menu(screen)
        
        if self.dialogue_ui:
            self.draw_dialogue_box(screen, self.dialogue_ui["name"], self.dialogue_ui["text"], self.dialogue_ui.get("options"))

        if self.show_shop_ui and self.active_merchant:
            self.current_shop_buttons = self.active_merchant.draw_shop_interface(screen, self.player)

        if not self.show_shop_ui and not self.show_mission_menu:
            self.draw_hud(screen)

    def _is_ui_open(self):
        return self.show_shop_ui or self.dialogue_ui or self.show_mission_menu

    def draw_interaction_prompt(self, screen, text, target_rect, color=NEON_GREEN):
        txt = self.font.render(text, True, color)
        surf_rect = txt.get_rect(center=(WIDTH//2, HEIGHT - 150))
        pygame.draw.rect(screen, (0, 0, 0, 180), surf_rect.inflate(20, 10))
        screen.blit(txt, surf_rect)

    def draw_mission_menu(self, screen):
        # Menu simple au centre
        menu_rect = pygame.Rect(0, 0, 500, 400)
        menu_rect.center = (WIDTH//2, HEIGHT//2)
        pygame.draw.rect(screen, (10, 10, 20), menu_rect)
        pygame.draw.rect(screen, NEON_PINK, menu_rect, 3)
        
        title = self.font.render("SÉLECTION DE MISSION", True, NEON_PINK)
        screen.blit(title, (menu_rect.centerx - title.get_width()//2, menu_rect.y + 30))
        
        for i, m_name in enumerate(self.unlocked_missions):
            color = NEON_BLUE if i == 0 else WHITE
            txt = self.font.render(f"{i+1}. {m_name}", True, color)
            screen.blit(txt, (menu_rect.x + 40, menu_rect.y + 100 + i*45))
        
        note = self.font.render("[ESC] pour fermer", True, (150, 150, 150))
        screen.blit(note, (menu_rect.centerx - note.get_width()//2, menu_rect.bottom - 40))

    def draw_dialogue_box(self, screen, name, text, options=False):
        box_rect = pygame.Rect(50, HEIGHT - 150, WIDTH - 100, 140)
        pygame.draw.rect(screen, (10, 10, 20), box_rect)
        pygame.draw.rect(screen, NEON_BLUE, box_rect, 2)
        
        name_surf = self.font.render(f"--- {name} ---", True, GOLD_COLOR)
        screen.blit(name_surf, (box_rect.x + 20, box_rect.y + 15))
        
        text_surf = self.font.render(text, True, WHITE)
        screen.blit(text_surf, (box_rect.x + 20, box_rect.y + 55))
        
        if options:
            opt_surf = self.font.render("[1]: Discuter   [2]: Acheter", True, NEON_GREEN)
            screen.blit(opt_surf, (box_rect.x + 20, box_rect.y + 100))
        else:
            hint = self.font.render("Appuyez sur ESPACE...", True, (150, 150, 150))
            screen.blit(hint, (box_rect.right - hint.get_width() - 20, box_rect.bottom - 30))

    def draw_hud(self, screen):
        bg_hud = pygame.Surface((280, 110))
        bg_hud.fill(BLACK)
        bg_hud.set_alpha(150)
        screen.blit(bg_hud, (10, 10))
        
        gold_txt = self.font.render(f"Poches: {int(self.player.gold)} G", True, WHITE)
        bank_txt = self.font.render(f"Banque: {int(self.player.banked_gold)} G", True, GOLD_COLOR)
        lvl_txt = self.font.render(f"Niveau: {self.player.level}", True, NEON_BLUE)
        
        screen.blit(gold_txt, (20, 20))
        screen.blit(bank_txt, (20, 45))
        screen.blit(lvl_txt, (20, 70))
