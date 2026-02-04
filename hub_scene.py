import pygame
from settings import *
from scenes import Scene
from dialogue import DialogueManager
from shop_system import Merchant, ShopItem
from asset_manager import AssetManager
from camera import CameraGroup
from base import Entity, Pyramid, AnimatedEntity # Keep entities in base.py for now to avoid circular imports? actually we should move them.
# For now we assume base.py still has Entity/Pyramid classes but we are rewriting BaseZone -> HubScene

class HubScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.width, self.height = MAP_WIDTH, MAP_HEIGHT
        self.assets = AssetManager()
        
        # Shared Player
        self.player = self.manager.shared_data.get('player')
        if not self.player:
            # Create player if not exists (should be done in manager usually, but fallback here)
            from player import Player
            self.player = Player(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))
            self.manager.shared_data['player'] = self.player

        # Camera & Groups
        self.camera_group = CameraGroup()
        self.camera_group.set_tiled_background("grass.png", MAP_WIDTH, MAP_HEIGHT)
        
        self.interactables = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group() 
        self.npcs = pygame.sprite.Group()

        # Add Player
        self.player.groups_list = [self.camera_group] # Helper to track groups?
        self.camera_group.add(self.player)
        
        # Dialogue
        self.dialogue_mgr = DialogueManager(self.assets.get_font(None, 24))
        
        self._setup_world()
        self._setup_merchants()
        self._setup_npcs()

        # UI State
        self.show_shop_ui = False
        self.active_merchant = None
        self.show_mission_menu = False
        self.unlocked_missions = self.manager.shared_data.get("unlocked_missions", ["Extraction Illimitée"])

    def on_enter(self, **kwargs):
        # Reset position if coming from somewhere specific
        spawn_point = kwargs.get('spawn_pos', (MAP_WIDTH//2, MAP_HEIGHT//2 + 500))
        self.player.rect.center = spawn_point
        # Re-add player to this scene's camera group just in case
        if self.player not in self.camera_group:
            self.camera_group.add(self.player)

    def _setup_world(self):
        # Pyramide logic (simplified)
        pyramid_img = self.assets.get_image("pyramid.png")
        if pyramid_img:
            new_size = (300, 200)
            px = MAP_WIDTH // 2 - new_size[0] // 2
            py = MAP_HEIGHT // 2 - new_size[1] // 2
            self.pyramid = Pyramid([self.camera_group, self.collision_sprites], image=pyramid_img, pos=(px, py), scale=new_size)
            # Hitbox plus petite au centre
            self.pyramid.hitbox = pygame.Rect(px + 40, py + 80, new_size[0] - 80, new_size[1] - 80)
            
            # DJ
            dj_x = px + new_size[0] // 2 - 20
            dj_y = py + new_size[1] // 3 
            self.dj = AnimatedEntity([self.camera_group], "daft_dj.png", pos=(dj_x, dj_y), scale=(40, 40))
            
            self.mission_rect = pygame.Rect(px + new_size[0]//2 - 60, py + new_size[1] + 10, 120, 60)
        else:
            self.mission_rect = pygame.Rect(MAP_WIDTH//2 - 50, MAP_HEIGHT//2 - 50, 100, 100)
            
        self.backstage_rect = pygame.Rect(MAP_WIDTH // 2 - 100, MAP_HEIGHT // 2 - 850, 200, 100)

    def _setup_merchants(self):
        self.merchants_data = [] 
        # Helpers
        def add(img_name, pos, name, text, type_filter):
            img = self.assets.get_image(img_name)
            sprite = Entity([self.camera_group, self.interactables, self.collision_sprites], image=img, pos=pos, scale=(200, 200))
            # Set explicit small hitbox for collision at bottom
            sprite.hitbox = pygame.Rect(pos[0] + 50, pos[1] + 150, 100, 50)
            
            m_obj = Merchant()
            # Filter
            m_obj.items = [item for item in m_obj.items if item.effect_type == type_filter or type_filter == "all"]
            if not m_obj.items:
                 m_obj.items = [ShopItem(f"Module {type_filter}", 100, 1, type_filter, 1, "Upgrade standard")]
            self.merchants_data.append({"sprite": sprite, "obj": m_obj, "name": name, "dialogue": text})

        add("merchant_stand.png", (MAP_WIDTH//2 - 800, MAP_HEIGHT//2), "Armurier Cyber", "Le son, c'est l'arme ultime.", "damage")
        add("merchant_base_upgrade.png", (MAP_WIDTH//2 + 800, MAP_HEIGHT//2), "Ingénieur Système", "Optimise tes circuits.", "hp")
        add("merchant_vehicle_garage.png", (MAP_WIDTH//2 - 600, MAP_HEIGHT//2 + 800), "Garagiste", "Ta mobylette est naze.", "speed")
        add("merchant_stand.png", (MAP_WIDTH//2 + 600, MAP_HEIGHT//2 + 800), "Fixer Info", "Infos sur cibles prioritaires.", "passive_gold")

    def _setup_npcs(self):
        self.lore_npcs = []
        npc_data = [
            ("L'Ancien", "J'ai vu le premier concert... C'était légendaire.", (MAP_WIDTH//2 - 200, MAP_HEIGHT//2 - 600)),
            ("Rescapée", "Ils ont pris mon frère. Il faut nettoyer la Zone 4.", (MAP_WIDTH//2 + 200, MAP_HEIGHT//2 - 600)),
            ("Fan Hardcore", "Si tu trouves un vinyle original, je te le rachete !", (MAP_WIDTH//2, MAP_HEIGHT//2 - 700))
        ]
        img = self.assets.get_image("punk_npc.png")
        for name, txt, pos in npc_data:
            npc = Entity([self.camera_group, self.interactables, self.npcs], image=img, pos=pos, scale=(50, 80))
            self.lore_npcs.append({"sprite": npc, "name": name, "dialogue": txt})

    def update(self):
        self.camera_group.update()
        
        if self._is_ui_open(): return

        # Movement
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        speed = 8 
        if keys[pygame.K_z] or keys[pygame.K_UP]: dy -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += speed
        if keys[pygame.K_q] or keys[pygame.K_LEFT]: dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += speed
        
        if dx != 0 and dy != 0: dx, dy = dx*0.707, dy*0.707

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

    def handle_input(self, events):
        # Dialogue
        if self.dialogue_mgr.active:
            for event in events:
                self.dialogue_mgr.handle_input(event)
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.show_shop_ui: self.show_shop_ui = False
                    elif self.show_mission_menu: self.show_mission_menu = False
                    else: 
                        self.manager.switch_to('menu')

                if event.key == pygame.K_e:
                    self._check_interactions()

                if self.show_mission_menu:
                    self._handle_mission_menu(event)
                elif self.show_shop_ui:
                    self._handle_shop_keyboard(event)

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.show_shop_ui: self._handle_shop_mouse(event)

    def _check_interactions(self):
        # Merchants
        for m in self.merchants_data:
            if self.player.rect.colliderect(m["sprite"].hitbox.inflate(100, 100)):
                self.active_merchant = m["obj"]
                self.dialogue_mgr.start_dialogue(m["name"], m["dialogue"], 
                    options=[("Ouvrir Magasin", "shop"), ("Au revoir", "bye")],
                    callback=self._on_merchant_dialogue)
                return
        
        # NPCs
        for npc in self.lore_npcs:
            if self.player.rect.colliderect(npc["sprite"].rect.inflate(60, 60)):
                self.dialogue_mgr.start_dialogue(npc["name"], npc["dialogue"])
                # Unlock mission logic simplified
                if "Rescapée" in npc["name"] and "Mission Sauvetage" not in self.unlocked_missions:
                    self.unlocked_missions.append("Mission Sauvetage")
                    self.manager.shared_data["unlocked_missions"] = self.unlocked_missions
                return

        # Mission
        if self.player.rect.colliderect(self.mission_rect):
            self.show_mission_menu = True
            return

        # Backstage
        if self.player.rect.colliderect(self.backstage_rect):
            self.manager.switch_to("backstage")

    def _on_merchant_dialogue(self, action_id):
        self.dialogue_mgr.active = False
        if action_id == "shop":
            self.show_shop_ui = True

    def _handle_mission_menu(self, event):
        if pygame.K_1 <= event.key <= pygame.K_9:
            idx = event.key - pygame.K_1
            if idx < len(self.unlocked_missions):
                 mission = self.unlocked_missions[idx]
                 self.manager.switch_to("mission", mission_type=mission)
    
    def _handle_shop_keyboard(self, event):
        if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                idx = event.key - pygame.K_1
                if self.active_merchant and 0 <= idx < len(self.active_merchant.items):
                    item = self.active_merchant.items[idx]
                    self.active_merchant.buy_item(item, self.player)

    def _handle_shop_mouse(self, event):
        if hasattr(self, 'current_shop_buttons'):
            for rect, item in self.current_shop_buttons:
                if rect.collidepoint(event.pos):
                    if item == "close":
                        self.show_shop_ui = False
                        self.active_merchant = None
                        return
                    self.active_merchant.buy_item(item, self.player)

    def _is_ui_open(self):
        return self.show_shop_ui or self.dialogue_mgr.active or self.show_mission_menu

    def draw(self, screen):
        self.camera_group.custom_draw(self.player)
        
        # Prompts
        if not self._is_ui_open():
            font = self.dialogue_mgr.font
            for m in self.merchants_data:
                if self.player.rect.colliderect(m["sprite"].hitbox.inflate(120, 120)):
                    self._draw_prompt(screen, f"[E] {m['name']}", font)
            for npc in self.lore_npcs:
                 if self.player.rect.colliderect(npc["sprite"].rect.inflate(80, 80)):
                      self._draw_prompt(screen, "[E] Parler", font)
            if self.player.rect.colliderect(self.mission_rect):
                self._draw_prompt(screen, "[E] MISSIONS", font, NEON_PINK)
            if self.player.rect.colliderect(self.backstage_rect):
                self._draw_prompt(screen, "[E] BACKSTAGE", font, GOLD_COLOR)

        # UIs
        self.dialogue_mgr.draw(screen)
        
        if self.show_mission_menu:
            self._draw_mission_menu(screen)
        
        if self.show_shop_ui and self.active_merchant:
            self.current_shop_buttons = self.active_merchant.draw_shop_interface(screen, self.player)

        if not self.show_shop_ui and not self.show_mission_menu:
             self._draw_hud(screen)

    def _draw_prompt(self, screen, text, font, color=NEON_GREEN):
        txt = font.render(text, True, color)
        surf_rect = txt.get_rect(center=(WIDTH//2, HEIGHT - 150))
        pygame.draw.rect(screen, (0, 0, 0, 180), surf_rect.inflate(20, 10))
        screen.blit(txt, surf_rect)

    def _draw_hud(self, screen):
        font = self.dialogue_mgr.font
        # Simple HUD reuse
        bg = pygame.Surface((280, 110))
        bg.fill(BLACK)
        bg.set_alpha(150)
        screen.blit(bg, (10, 10))
        screen.blit(font.render(f"Poches: {int(self.player.gold)} G", True, WHITE), (20, 20))
        screen.blit(font.render(f"Banque: {int(self.player.banked_gold)} G", True, GOLD_COLOR), (20, 45))
        screen.blit(font.render(f"Niveau: {self.player.level}", True, NEON_BLUE), (20, 70))

    def _draw_mission_menu(self, screen):
        menu_rect = pygame.Rect(0, 0, 500, 400)
        menu_rect.center = (WIDTH//2, HEIGHT//2)
        pygame.draw.rect(screen, (10, 10, 20), menu_rect)
        pygame.draw.rect(screen, NEON_PINK, menu_rect, 3)
        font = self.dialogue_mgr.font
        
        title = font.render("SÉLECTION DE MISSION", True, NEON_PINK)
        screen.blit(title, (menu_rect.centerx - title.get_width()//2, menu_rect.y + 30))
        
        for i, m in enumerate(self.unlocked_missions):
            txt = font.render(f"{i+1}. {m}", True, NEON_BLUE if i == 0 else WHITE)
            screen.blit(txt, (menu_rect.x + 40, menu_rect.y + 100 + i*45))
