import pygame
import math
from core.settings import *
from states.scenes import Scene
from ui.dialogue import DialogueManager
from core.shop_system import Merchant, ShopItem
from core.asset_manager import AssetManager
from core.camera import CameraGroup
from entities.entity import Entity, AnimatedEntity
from entities.obstacles import Pyramid
from entities.player import Player

class AnimatedSmoke(pygame.sprite.Sprite):
    def __init__(self, groups, image, pos, frame_delay=100, lifetime=4000):
        super().__init__(groups)
        
        self.sprite_sheet = image
        sheet_width = self.sprite_sheet.get_width()
        sheet_height = self.sprite_sheet.get_height()
        
        self.frames = []
        
        FRAME_SIZE = 256
        
        cols = sheet_width // FRAME_SIZE
        rows = sheet_height // FRAME_SIZE
        self.frame_count = cols * rows
        
        for row in range(rows):
            for col in range(cols):
                try:
                    frame = pygame.Surface((FRAME_SIZE, FRAME_SIZE), pygame.SRCALPHA)
                    frame.blit(self.sprite_sheet, (0, 0), 
                              (col * FRAME_SIZE, row * FRAME_SIZE, FRAME_SIZE, FRAME_SIZE))
                    
                    scaled_frame = pygame.transform.scale(frame, (FRAME_SIZE // 3, FRAME_SIZE // 3))
                    self.frames.append(scaled_frame)
                except Exception as e:
                    print(f"[ERROR] Frame {row},{col}: {e}")
                    break
        
        if len(self.frames) == 0:
            print("[WARNING] No frames extracted, using full image")
            scaled_img = pygame.transform.scale(self.sprite_sheet, 
                                               (sheet_width // 3, sheet_height // 3))
            self.frames.append(scaled_img)
        
        self.current_frame = 0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)
        
        self.frame_delay = frame_delay
        self.last_update = pygame.time.get_ticks()
        
        self.lifetime = lifetime
        self.spawn_time = pygame.time.get_ticks()
        self.fade_duration = 1000
        self.alpha = 255
        
    def update(self):
        now = pygame.time.get_ticks()
        
        elapsed = now - self.spawn_time
        if elapsed > self.lifetime:
            self.kill()
            return
        
        if elapsed > self.lifetime - self.fade_duration:
            fade_progress = (elapsed - (self.lifetime - self.fade_duration)) / self.fade_duration
            self.alpha = int(255 * (1 - fade_progress))
        
        if now - self.last_update > self.frame_delay:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame].copy()
            
            if self.alpha < 255:
                self.image.set_alpha(self.alpha)


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

        # Shopkeepers & NPCs
        self.merchants_data = []
        self.lore_npcs = []
        
        # Mission menu
        self.show_mission_menu = False
        
        # Shop UI
        self.show_shop_ui = False
        self.active_merchant = None
        
        # Spawn system
        self.spawn_point = (self.width // 2, self.height // 2 + 400)  # Below pyramid
        self.spawn_platform = None
        self.smoke_sprites = []
        
        # Add Player
        if self.player not in self.camera_group:
            self.camera_group.add(self.player)
        
        # Dialogue
        self.dialogue_mgr = DialogueManager(self.assets.get_font(None, 24))
        
        # Setup
        self._setup_world()
        self._setup_spawn_zone()  # Spawn zone with smoke effect
        self._setup_decor()
        self._setup_merchants()
        self._setup_npcs()
        
        # Teleport player to spawn
        self.player.rect.center = self.spawn_point

        # UI State
        self.unlocked_missions = self.manager.shared_data.get("unlocked_missions", ["Extraction Illimitée"])

    def on_enter(self, **kwargs):
        died = kwargs.get('died', False)
        if died:
            self.player.hp = self.player.max_hp
            self.player.rect.center = self.spawn_point
            print("💀 Respawned at spawn zone")
        else:
            spawn_point = kwargs.get('spawn_pos', self.spawn_point)
            self.player.rect.center = spawn_point

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

    def _setup_spawn_zone(self):
        platform_size = 150
        platform_x = self.spawn_point[0] - platform_size // 2
        platform_y = self.spawn_point[1] - platform_size // 2
        
        platform_tile_size = 50
        for row in range(3):
            for col in range(3):
                x = platform_x + col * platform_tile_size
                y = platform_y + row * platform_tile_size
                
                tile = pygame.Surface((platform_tile_size, platform_tile_size))
                
                distance_to_center = math.sqrt((col - 1)**2 + (row - 1)**2)
                brightness = int(120 - (distance_to_center * 15))
                brightness = max(80, min(brightness, 140))
                
                tile.fill((brightness // 2, brightness // 1.5, brightness))
                
                if row == 1 and col == 1:
                    tile.fill((60, 180, 220))
                    pygame.draw.rect(tile, (100, 220, 255), (0, 0, platform_tile_size, platform_tile_size), 3)
                
                tile_entity = Entity([self.camera_group], image=tile, pos=(x + 25, y + 25), scale=None)
                tile_entity.rect = tile.get_rect(center=(x + 25, y + 25))
        
        smoke_img = self.assets.get_image("Free Smoke Fx Pixel 2/Free Smoke Fx  Pixel 07.png")
        if smoke_img:
            smoke_sprite = AnimatedSmoke(
                [self.camera_group],
                image=smoke_img,
                pos=self.spawn_point,
                frame_delay=80,
                lifetime=4000
            )
            self.smoke_sprites.append(smoke_sprite)

    def _setup_concert_elements(self):
        """Add concert theme: barriers, guards, speakers, amps"""
        cx, cy = self.width // 2, self.height // 2
        
        # 1. CONCERT BARRIERS (autour de la scène centrale)
        # Créer barrières métalliques pour délimiter la zone de concert
        barrier_positions = [
            # Barrière haut (devant la scène)
            (cx - 400, cy - 300, 800, 20, "horizontal"),
            # Barrières latérales
            (cx - 400, cy - 300, 20, 250, "vertical"),  # Gauche
            (cx + 400, cy - 300, 20, 250, "vertical"),  # Droite
        ]
        
        for bx, by, bw, bh, orientation in barrier_positions:
            # Créer barrière métallique avec effet grillage
            barrier = pygame.Surface((bw, bh))
            barrier.fill((40, 40, 40))  # Gris sombre
            
            # Motif grillage
            if orientation == "horizontal":
                for i in range(0, bw, 20):
                    pygame.draw.line(barrier, (80, 80, 80), (i, 0), (i, bh), 2)
                pygame.draw.rect(barrier, (100, 100, 100), (0, 0, bw, bh), 3)
            else:
                for i in range(0, bh, 20):
                    pygame.draw.line(barrier, (80, 80, 80), (0, i), (bw, i), 2)
                pygame.draw.rect(barrier, (100, 100, 100), (0, 0, bw, bh), 3)
            
            barrier_entity = Entity([self.camera_group, self.collision_sprites], 
                                   image=barrier, pos=(bx + bw//2, by + bh//2), scale=None)
            barrier_entity.hitbox = pygame.Rect(bx, by, bw, bh)
        
        # 2. GARDES / VIGILES
        guard_img = self.assets.get_image("vigilante_guard.png")
        if guard_img:
            # Positions des gardes (aux coins des barrières)
            guard_positions = [
                (cx - 450, cy - 320, "Garde Gauche"),
                (cx + 450, cy - 320, "Garde Droite"),
                (cx - 450, cy + 50, "Garde Bas Gauche"),
                (cx + 450, cy + 50, "Garde Bas Droite"),
            ]
            
            for gx, gy, name in guard_positions:
                guard = Entity([self.camera_group, self.collision_sprites, self.npcs],
                             image=guard_img, pos=(gx, gy), scale=(60, 80))
                guard.hitbox = pygame.Rect(gx - 30, gy - 40, 60, 80)
                guard.name = name
                guard.dialogue = "🎵 La musique doit continuer ! Protégez la scène !"
        
        # 3. SPEAKERS / ENCEINTES GÉANTES
        # Créer grosses enceintes sur les côtés de la scène
        speaker_positions = [
            (cx - 500, cy - 150, "left"),
            (cx + 500, cy - 150, "right"),
            (cx - 500, cy + 150, "left"),
            (cx + 500, cy + 150, "right"),
        ]
        
        for sx, sy, side in speaker_positions:
            # Créer enceinte stylisée
            speaker = pygame.Surface((80, 120), pygame.SRCALPHA)
            
            # Corps noir
            speaker.fill((20, 20, 20))
            pygame.draw.rect(speaker, (10, 10, 10), (0, 0, 80, 120), 5)
            
            # Haut-parleurs (cercles)
            pygame.draw.circle(speaker, (30, 30, 30), (40, 30), 20)
            pygame.draw.circle(speaker, (50, 50, 50), (40, 30), 15)
            pygame.draw.circle(speaker, NEON_BLUE, (40, 30), 15, 2)
            
            pygame.draw.circle(speaker, (30, 30, 30), (40, 70), 15)
            pygame.draw.circle(speaker, (50, 50, 50), (40, 70), 10)
            pygame.draw.circle(speaker, NEON_GREEN, (40, 70), 10, 2)
            
            pygame.draw.circle(speaker, (30, 30, 30), (40, 100), 10)
            pygame.draw.circle(speaker, (50, 50, 50), (40, 100), 7)
            pygame.draw.circle(speaker, NEON_PINK, (40, 100), 7, 2)
            
            speaker_entity = Entity([self.camera_group, self.collision_sprites],
                                   image=speaker, pos=(sx, sy), scale=None)
            speaker_entity.hitbox = pygame.Rect(sx - 40, sy - 60, 80, 120)
        
        # 4. AMPLIS (plus petits, près des marchands)
        amp_positions = [
            (cx - 350, cy + 300),
            (cx + 350, cy + 300),
            (cx - 200, cy + 400),
            (cx + 200, cy + 400),
        ]
        
        for ax, ay in amp_positions:
            # Ampli guitare style Marshall
            amp = pygame.Surface((50, 60))
            amp.fill((10, 10, 10))
            pygame.draw.rect(amp, (30, 30, 30), (5, 5, 40, 20))
            # Grille
            for i in range(0, 40, 5):
                pygame.draw.line(amp, (60, 60, 60), (5+i, 5), (5+i, 25), 1)
            # LED
            pygame.draw.circle(amp, (255, 50, 50), (25, 35), 3)
            # Boutons
            for bx in [10, 20, 30, 40]:
                pygame.draw.circle(amp, (200, 200, 200), (bx, 45), 2)
            
            amp_entity = Entity([self.camera_group, self.collision_sprites],
                               image=amp, pos=(ax, ay), scale=None)
            amp_entity.hitbox = pygame.Rect(ax - 25, ay - 30, 50, 60)
        
        # 5. SPOTLIGHTS (effets lumineux)
        spotlight_positions = [
            (cx - 300, cy - 350),
            (cx, cy - 350),
            (cx + 300, cy - 350),
        ]
        
        for slx, sly in spotlight_positions:
            # Spot lumineux qui "éclaire" vers le bas
            spotlight = pygame.Surface((40, 80), pygame.SRCALPHA)
            # Base du spot
            pygame.draw.rect(spotlight, (50, 50, 50), (10, 0, 20, 20))
            # Faisceau lumineux
            pygame.draw.polygon(spotlight, (255, 255, 100, 80), 
                              [(20, 20), (5, 80), (35, 80)])
            pygame.draw.polygon(spotlight, (255, 255, 200, 120), 
                              [(20, 20), (10, 70), (30, 70)])
            
            spot_entity = Entity([self.camera_group], image=spotlight, 
                                pos=(slx, sly), scale=None)


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
        self.player.update()
        
        for smoke in self.smoke_sprites:
            smoke.update()
        
        self.camera_group.update()
        
        for sprite in self.collision_sprites:
            if hasattr(sprite, 'hitbox'):
                if self.player.rect.colliderect(sprite.hitbox):
                    overlap_x = min(self.player.rect.right - sprite.hitbox.left,
                                   sprite.hitbox.right - self.player.rect.left)
                    overlap_y = min(self.player.rect.bottom - sprite.hitbox.top,
                                   sprite.hitbox.bottom - self.player.rect.top)
                    
                    if overlap_x < overlap_y:
                        if self.player.rect.centerx < sprite.hitbox.centerx:
                            self.player.rect.right = sprite.hitbox.left
                        else:
                            self.player.rect.left = sprite.hitbox.right
                    else:
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
        
        # NPCs (use npcs_data with hitboxes)
        if hasattr(self, 'npcs_data'):
            for npc in self.npcs_data:
                if self.player.rect.colliderect(npc["sprite"].hitbox.inflate(80, 80)):
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
        
        # Prompts
        if not self._is_ui_open():
            font = self.dialogue_mgr.font
            for m in self.merchants_data:
                if self.player.rect.colliderect(m["sprite"].hitbox.inflate(120, 120)):
                    self._draw_prompt(screen, f"[E] {m['name']}", font)
            
            # NPCs prompts
            if hasattr(self, 'npcs_data'):
                for npc in self.npcs_data:
                    if self.player.rect.colliderect(npc["sprite"].hitbox.inflate(80, 80)):
                        self._draw_prompt(screen, f"[E] Parler à {npc['name']}", font)
            
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
        
        # Draw solid black background first (opaque)
        pygame.draw.rect(screen, (0, 0, 0), menu_rect)
        # Then draw dark blue overlay
        pygame.draw.rect(screen, (10, 10, 20), menu_rect)
        # Border
        pygame.draw.rect(screen, NEON_PINK, menu_rect, 3)
        
        font = self.dialogue_mgr.font
        
        title = font.render("SÉLECTION DE MISSION", True, NEON_PINK)
        screen.blit(title, (menu_rect.centerx - title.get_width()//2, menu_rect.y + 30))
        
        # Mission buttons
        for i, (name, desc) in enumerate([("Mission 1", "Tutoriel"), ("Mission 2", "Vertical Assault")]):
            btn_y = menu_rect.y + 100 + i * 80
            btn_rect = pygame.Rect(menu_rect.centerx - 200, btn_y, 400, 60)
            pygame.draw.rect(screen, (30, 30, 40), btn_rect)
            pygame.draw.rect(screen, NEON_BLUE, btn_rect, 2)
            
            txt = font.render(name, True, WHITE)
            screen.blit(txt, (btn_rect.x + 20, btn_rect.y + 10))
            desc_txt = font.render(desc, True, (150, 150, 150))
            screen.blit(desc_txt, (btn_rect.x + 20, btn_rect.y + 35))
        
        # Close button
        close_txt = font.render("[ESC] Fermer", True, (200, 200, 200))
        screen.blit(close_txt, (menu_rect.centerx - close_txt.get_width()//2, menu_rect.bottom - 40))
