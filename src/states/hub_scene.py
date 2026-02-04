import math
from core.settings import *
from states.scenes import Scene
from ui.dialogue import DialogueManager
from core.shop_system import Merchant, ShopItem
from core.asset_manager import AssetManager
from core.camera import CameraGroup
from entities.entity import Entity, AnimatedEntity
from entities.building import Pyramid
from entities.player import Player

class HubScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.width, self.height = HUB_WIDTH, HUB_HEIGHT
        self.assets = AssetManager()
        
        # Shared Player
        self.player = self.manager.shared_data.get('player')
        if not self.player:
            self.player = Player(pygame.Rect(0, 0, HUB_WIDTH, HUB_HEIGHT))
            self.manager.shared_data['player'] = self.player

        # Camera & Groups
        self.camera_group = CameraGroup()
        self.camera_group.set_tiled_background("grass.png", self.width, self.height)
        
        self.interactables = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group() 
        self.npcs = pygame.sprite.Group()

        # Add Player
        self.player.groups_list = [self.camera_group] 
        self.camera_group.add(self.player)
        
        # Dialogue
        self.dialogue_mgr = DialogueManager(self.assets.get_font(None, 24))
        
        self._setup_world()
        self._setup_decor()
        self._setup_merchants()
        self._setup_npcs()

        # UI State
        self.show_shop_ui = False
        self.active_merchant = None
        self.show_mission_menu = False
        self.unlocked_missions = self.manager.shared_data.get("unlocked_missions", ["Extraction Illimitée"])

    def on_enter(self, **kwargs):
        spawn_point = kwargs.get('spawn_pos', (self.width//2, self.height//2 + 500))
        self.player.rect.center = spawn_point
        if self.player not in self.camera_group:
            self.camera_group.add(self.player)

    def _setup_world(self):
        # Central Pyramid (Missions)
        pyramid_img = self.assets.get_image("pyramid.png")
        if pyramid_img:
            # Place at center
            pyramid_x = self.width // 2
            pyramid_y = self.height // 2
            
            self.pyramid = Pyramid(
                [self.camera_group, self.collision_sprites], 
                image=pyramid_img,
                pos=(pyramid_x, pyramid_y),
                scale=(300, 200)
            )
            
            # Pyramid hitbox for collisions
            # pos = center of sprite, so sprite rect goes from:
            # (pyramid_x - 150, pyramid_y - 100) to (pyramid_x + 150, pyramid_y + 100)
            # Make hitbox slightly smaller for better gameplay
            self.pyramid.hitbox = pygame.Rect(
                pyramid_x - 130,  # Slightly smaller than sprite
                pyramid_y - 80,   # Slightly smaller than sprite
                260,              # Width (was 300)
                160               # Height (was 200)
            )
            
            # Mission interaction zone (around pyramid)
            self.mission_rect = pygame.Rect(
                pyramid_x - 150, 
                pyramid_y - 150, 
                300, 
                300
            )
        else:
            self.mission_rect = pygame.Rect(self.width//2 - 50, self.height//2 - 50, 100, 100)

    def _setup_decor(self):
        # Visual path tiles around pyramid
        path_tile_size = 32
        path_color = (100, 120, 140)  # Gray-blue path color
        
        cx, cy = self.width // 2, self.height // 2
        path_positions = []
        
        # 1. CIRCULAR PATH around pyramid (radius = 250px)
        circle_radius = 250
        num_circle_tiles = 50  # Number of tiles in circle
        
        for i in range(num_circle_tiles):
            angle = (i / num_circle_tiles) * 2 * math.pi
            x = cx + circle_radius * math.cos(angle)
            y = cy + circle_radius * math.sin(angle)
            path_positions.append((x, y))
        
        # 2. BRANCHES from circle to each merchant
        # Merchant positions (from _setup_merchants)
        merchant_positions = [
            (cx - 400, cy),           # Armurier (West)
            (cx + 500, cy),           # Ingénieur (East)
            (cx - 300, cy + 400),     # Garagiste (South-West)
            (cx + 300, cy + 400),     # Passeur (South-East)
        ]
        
        # Create straight paths from circle to each merchant
        for merchant_pos in merchant_positions:
            # Find closest point on circle to merchant
            dx = merchant_pos[0] - cx
            dy = merchant_pos[1] - cy
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Circle edge point
            circle_x = cx + (dx / dist) * circle_radius
            circle_y = cy + (dy / dist) * circle_radius
            
            # Create tiles from circle to merchant
            num_branch_tiles = int(dist - circle_radius) // path_tile_size
            for i in range(num_branch_tiles):
                t = i / max(num_branch_tiles, 1)
                x = circle_x + (merchant_pos[0] - circle_x) * t
                y = circle_y + (merchant_pos[1] - circle_y) * t
                path_positions.append((x, y))
        
        # Draw all path tiles
        for pos in path_positions:
            path_tile = pygame.Surface((path_tile_size, path_tile_size))
            path_tile.fill(path_color)
            pygame.draw.rect(path_tile, (80, 100, 120), (0, 0, path_tile_size, path_tile_size), 2)
            
            tile_entity = Entity([self.camera_group], image=path_tile, pos=pos, scale=None)
            tile_entity.rect = path_tile.get_rect(center=pos)

    def _setup_merchants(self):
        self.merchants_data = [] 
        def add(img_name, pos, name, text, type_filter, action="shop"):
            img = self.assets.get_image(img_name)
            sprite = Entity([self.camera_group, self.interactables, self.collision_sprites], 
                          image=img, pos=pos, scale=(150, 150))
            
            # FIX: pos is the CENTER of the sprite (150x150)
            # So the sprite goes from (pos[0]-75, pos[1]-75) to (pos[0]+75, pos[1]+75)
            # Hitbox should be centered on sprite, slightly smaller
            sprite.hitbox = pygame.Rect(
                pos[0] - 60,  # 120 wide, centered on pos[0]
                pos[1] - 60,  # 120 tall, centered on pos[1]
                120,
                120
            )
            
            if action == "shop":
                m_obj = Merchant()
                m_obj.items = [item for item in m_obj.items if item.effect_type == type_filter or type_filter == "all"]
                if not m_obj.items:
                     m_obj.items = [ShopItem(f"Module {type_filter}", 100, 1, type_filter, 1, "Upgrade standard")]
                self.merchants_data.append({"sprite": sprite, "obj": m_obj, "name": name, "dialogue": text, "action": "shop"})
            elif action == "travel":
                 self.merchants_data.append({"sprite": sprite, "obj": None, "name": name, "dialogue": text, "action": "travel"})

        # Redimensionnement des positions pour 2000px
        cx, cy = self.width // 2, self.height // 2
        
        # Ecartement un peu plus grand
        add("merchant_stand.png", (cx - 400, cy), "Armurier", "Le son est une arme.", "damage")
        add("merchant_base_upgrade.png", (cx + 500, cy), "Ingénieur", "Garde le rythme.", "hp")  # Moved further right
        add("merchant_vehicle_garage.png", (cx - 300, cy + 400), "Garagiste", "Répare ta bécane.", "speed")
        add("merchant_stand.png", (cx + 300, cy + 400), "Passeur", "Tu veux voir l'envers du décor ?", "none", action="travel")


    def _setup_npcs(self):
        self.lore_npcs = []
        npc_data = [
            ("L'Ancien", "Tout a changé depuis le Silence.", (MAP_WIDTH//2, MAP_HEIGHT//2 - 500)),  # Much further up
        ]
        img = self.assets.get_image("punk_npc.png")
        for name, txt, pos in npc_data:
            # Add to collision_sprites so player can't walk through
            npc = Entity([self.camera_group, self.interactables, self.npcs, self.collision_sprites], 
                        image=img, pos=pos, scale=(50, 80))
            # Add proper hitbox for NPC
            npc.hitbox = pygame.Rect(
                pos[0] - 25,  # Center horizontally
                pos[1] - 40,  # Center vertically
                50,           # Width
                80            # Height
            )
            self.lore_npcs.append({"sprite": npc, "name": name, "dialogue": txt})

    def update(self):
        # Let player handle its own movement
        self.player.update()
        
        # Update camera group
        self.camera_group.update()
        
        # Manual collision with hitboxes
        for sprite in self.collision_sprites:
            if hasattr(sprite, 'hitbox'):
                if self.player.rect.colliderect(sprite.hitbox):
                    # Push player out of hitbox
                    # Simple overlap resolution
                    overlap_x = min(self.player.rect.right - sprite.hitbox.left,
                                   sprite.hitbox.right - self.player.rect.left)
                    overlap_y = min(self.player.rect.bottom - sprite.hitbox.top,
                                   sprite.hitbox.bottom - self.player.rect.top)
                    
                    if overlap_x < overlap_y:
                        # Push horizontally
                        if self.player.rect.centerx < sprite.hitbox.centerx:
                            self.player.rect.right = sprite.hitbox.left
                        else:
                            self.player.rect.left = sprite.hitbox.right
                    else:
                        # Push vertically
                        if self.player.rect.centery < sprite.hitbox.centery:
                            self.player.rect.bottom = sprite.hitbox.top
                        else:
                            self.player.rect.top = sprite.hitbox.bottom

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
                if m["action"] == "travel":
                     self.dialogue_mgr.start_dialogue(m["name"], m["dialogue"], 
                        options=[("Aller au Backstage", "go_backstage"), ("Rester ici", "stay")],
                        callback=self._on_travel_dialogue)
                else:
                    self.active_merchant = m["obj"]
                    self.dialogue_mgr.start_dialogue(m["name"], m["dialogue"], 
                        options=[("Ouvrir Magasin", "shop"), ("Au revoir", "bye")],
                        callback=self._on_merchant_dialogue)
                return
        
        # NPCs
        for npc in self.lore_npcs:
            if self.player.rect.colliderect(npc["sprite"].rect.inflate(60, 60)):
                self.dialogue_mgr.start_dialogue(npc["name"], npc["dialogue"])
                return

        # Mission
        if self.player.rect.colliderect(self.mission_rect):
            self.show_mission_menu = True
            return

    def _on_travel_dialogue(self, action_id):
        self.dialogue_mgr.active = False
        if action_id == "go_backstage":
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
        
        # === DEBUG: Draw Hitboxes ===
        # Draw hitboxes in red so we can see them
        for m in self.merchants_data:
            if hasattr(m["sprite"], 'hitbox'):
                # Convert world position to screen position
                offset_pos = self.camera_group.offset
                hitbox_screen = m["sprite"].hitbox.copy()
                hitbox_screen.x -= int(offset_pos.x)
                hitbox_screen.y -= int(offset_pos.y)
                pygame.draw.rect(screen, (255, 0, 0), hitbox_screen, 2)  # Red outline
        
        for npc in self.lore_npcs:
            if hasattr(npc["sprite"], 'hitbox'):
                offset_pos = self.camera_group.offset
                hitbox_screen = npc["sprite"].hitbox.copy()
                hitbox_screen.x -= int(offset_pos.x)
                hitbox_screen.y -= int(offset_pos.y)
                pygame.draw.rect(screen, (255, 0, 0), hitbox_screen, 2)
        
        # Pyramid hitbox
        if hasattr(self.pyramid, 'hitbox'):
            offset_pos = self.camera_group.offset
            hitbox_screen = self.pyramid.hitbox.copy()
            hitbox_screen.x -= int(offset_pos.x)
            hitbox_screen.y -= int(offset_pos.y)
            pygame.draw.rect(screen, (0, 255, 0), hitbox_screen, 3)  # Green outline
        # === END DEBUG ===
        
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
