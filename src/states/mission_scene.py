import pygame
import random
import math
from core.settings import *
from states.scenes import Scene
from core.asset_manager import AssetManager
from core.camera import CameraGroup
from ui.particles import ParticleSystem
from entities.entity import separate_sprites, Entity, AnimatedEntity
from ui.dialogue import DialogueManager
from entities.enemy import Enemy
from entities.ranged_enemy import RangedEnemy
from entities.enemies_variants import Zombie, Robot
from entities.gold import Gold

from entities.walls import Wall

class LoreNPC(Entity):
    def __init__(self, groups, pos, color, name, dialogue_text):
        assets = AssetManager()
        img = assets.get_image("punk_npc.png")
        if not img:
            img = pygame.Surface((50, 80))
            img.fill(color)
        super().__init__(groups, image=img, pos=pos, scale=(50, 80))
        
        # Tinting / Coloring (Optional, maybe just a colored circle overhead?)
        self.indicator = pygame.Surface((10, 10))
        self.indicator.fill(color)
        
        self.name = name
        self.dialogue_text = dialogue_text

    def update(self):
        # Allow simple bobbing
        pass

class MissionScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.assets = AssetManager()
        
        # Dimensions du niveau linéaire
        self.level_length = 8000
        self.corridor_height = 800
        self.width = self.level_length
        self.height = self.corridor_height
        
        self.player = self.manager.shared_data.get('player')
        
        # Groupes
        self.camera_group = CameraGroup()
        # Fond "Cyber" pour le couloir
        self.camera_group.set_tiled_background("concert_floor.png", self.level_length, self.corridor_height)
        
        self.enemies = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.golds = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()
        self.interactables = pygame.sprite.Group()
        
        self.particles = ParticleSystem() 
        self.dialogue_mgr = DialogueManager(self.assets.get_font(None, 24))
        
        # Ajout Joueur
        self.camera_group.add(self.player)
        
        # État
        self.failed = False
        self.finished = False
        self.extraction_zone = pygame.Rect(self.level_length - 400, 200, 300, 400)

    def on_enter(self, **kwargs):
        # Configuration
        self.mission_type = kwargs.get('mission_type', 'linear')
        
        # Default is Open if specific name
        if self.mission_type == "Extraction Illimitée": self.mission_type = "open"
        else: self.mission_type = "linear"

        print(f"Lancement Mission : {self.mission_type}")
        
        # Reset Common
        self.enemies.empty()
        self.projectiles.empty()
        self.enemy_projectiles.empty()
        self.golds.empty()
        self.walls.empty()
        self.npcs.empty()
        self.interactables.empty()
        self.particles.particles = []
        self.failed = False
        self.finished = False
        self.player.hp = self.player.max_hp

        if self.mission_type == "linear":
            self.level_length = 8000
            self.corridor_height = 800
            self.width = self.level_length
            self.height = self.corridor_height
            self.camera_group.set_tiled_background("concert_floor.png", self.level_length, self.corridor_height)
            self.player.rect.topleft = (100, self.corridor_height // 2)
            self._build_level_linear()
            
        else: # Open World
            self.width, self.height = OPEN_WORLD_WIDTH, OPEN_WORLD_HEIGHT
            self.camera_group.set_tiled_background("grass.png", OPEN_WORLD_WIDTH, OPEN_WORLD_HEIGHT)
            self.player.rect.center = (OPEN_WORLD_WIDTH // 2, OPEN_WORLD_HEIGHT // 2)
            self._build_level_open()

        if self.player not in self.camera_group:
            self.camera_group.add(self.player)

    def _build_level_linear(self):
        # Configuration Zig-Zag
        # Segment: (x, y, width, height, type='h'/'v')
        segments = []
        
        # Start Bottom Center
        start_x = self.level_length // 2
        start_y = self.corridor_height - 600
        current_x, current_y = start_x, start_y
        
        # Room Base
        segments.append(pygame.Rect(current_x - 300, current_y - 300, 600, 600))
        
        # Generation Loop
        steps = 8
        direction = 1 # 1: Right, -1: Left
        
        for i in range(steps):
             # 1. Vertical Up
             v_height = random.randint(600, 1000)
             new_y = current_y - v_height
             segments.append(pygame.Rect(current_x - 200, new_y - 200, 400, v_height + 400)) # Corridor V
             current_y = new_y
             
             # 2. Horizontal
             if i < steps - 1:
                 h_width = random.randint(800, 1500)
                 new_x = current_x + (h_width * direction)
                 # Ensure bounds
                 if new_x > self.level_length - 200: new_x = self.level_length - 200; direction *= -1
                 if new_x < 200: new_x = 200; direction *= -1
                 
                 # Corridor H
                 left = min(current_x, new_x)
                 width = abs(new_x - current_x)
                 segments.append(pygame.Rect(left - 200, current_y - 200, width + 400, 400))
                 
                 current_x = new_x
                 direction *= -1 # Toggle direction
        
        # Final Room
        segments.append(pygame.Rect(current_x - 400, current_y - 400, 800, 800))
        self.extraction_zone = pygame.Rect(current_x - 100, current_y - 100, 200, 200) # End zone at the very end
        self.player.rect.center = (start_x, start_y)

        # Wall Generation
        candidate_walls = []
        wt = 50
        for r in segments:
             candidate_walls.append(pygame.Rect(r.left, r.top - wt, r.width, wt)) # Top
             candidate_walls.append(pygame.Rect(r.left, r.bottom, r.width, wt)) # Bottom
             candidate_walls.append(pygame.Rect(r.left - wt, r.top, wt, r.height)) # Left
             candidate_walls.append(pygame.Rect(r.right, r.top, wt, r.height)) # Right
             
        final_walls = []
        for w in candidate_walls:
             # Check collision with "Walkable Area" (any segment)
             is_blocking_path = False
             w_center = w.center
             for s in segments:
                 if s.collidepoint(w_center):
                     is_blocking_path = True
                     break
             
             if not is_blocking_path:
                 final_walls.append(w)
        
        for w_rect in final_walls:
             self.walls.add(Wall([self.camera_group, self.walls], w_rect.topleft, w_rect.size))
             
        # Spawn Enemies
        for seg in segments[1:]: # Skip safe room
            if random.random() < 0.7:
                self._spawn_enemy_wave_linear(seg.centerx, seg.centery, random.randint(1, 3), "mixed")
                
        # Lore NPC
        if len(segments) > 3:
            r = segments[3]
            self._spawn_lore_npc(r.centerx, "Le Rescapé", (0, 255, 255), "Ils arrivent... Ne les laisse pas couper la musique !")

    def _build_level_open(self):
        # Spawn initial decorations (Fake PNGs/Obstacles)
        import random
        from entities.walls import Obstacle
        for _ in range(40): # 40 obstacles
             ox = random.randint(100, self.width - 100)
             oy = random.randint(100, self.height - 100)
             if pygame.Vector2(ox - self.width//2, oy - self.height//2).length() > 300: # Clear spawn
                 Obstacle([self.camera_group, self.walls], (ox, oy), (random.randint(60, 120), random.randint(60, 120)))

        # Spawn initial (Increased to 50)
        self._spawn_initial_enemies_open(50)
        # Extraction (Reduced delay to 10s)
        self.extraction_active = False 
        self.extraction_timer = pygame.time.get_ticks() + 10000 
        self.extraction_zone = pygame.Rect(0, 0, 0, 0)

    def _spawn_enemy_wave_linear(self, x_start, y_center, count, type):
        for i in range(count):
            x = x_start + random.randint(-100, 100)
            y = y_center + random.randint(-200, 200)
            y = max(60, min(y, self.corridor_height - 60))
            e = self._create_enemy(type)
            e.rect.center = (x, y)
            self.enemies.add(e)
            self.camera_group.add(e)

    def _create_enemy(self, type="basic"):
        # Fix: Pass actual map bounds, not dummy rect
        map_rect = pygame.Rect(0, 0, self.width, self.height)
        
        if type == "basic": return Enemy(map_rect, hp=3, damage=1)
        elif type == "drone": return RangedEnemy(map_rect, hp=2, damage=1)
        elif type == "zombie": return Zombie(map_rect, hp=5, damage=2)
        elif type == "mixed": return Robot(map_rect, hp=4, damage=1) 
        elif type == "elite": return Robot(map_rect, hp=10, damage=3)
        return Enemy(map_rect, hp=3, damage=1)

    def _spawn_initial_enemies_open(self, count):
        for _ in range(count):
            e = self._create_enemy(random.choice(["basic", "drone", "zombie"]))
            # Random Pos in MAP_WIDTH/HEIGHT
            e.rect.center = (random.randint(50, MAP_WIDTH-50), random.randint(50, MAP_HEIGHT-50))
            self.enemies.add(e)
            self.camera_group.add(e)

    def _spawn_lore_npc(self, x, name, color, text):
        y = random.choice([100, self.corridor_height - 150])
        npc = LoreNPC([self.camera_group, self.interactables, self.npcs], (x, y), color, name, text)

    def update(self):
        if self.dialogue_mgr.active: return

        now = pygame.time.get_ticks()
        
        self.player.update()
        self.enemies.update(self.player)
        self.npcs.update() 
        self.projectiles.update()
        self.enemy_projectiles.update()
        self.particles.update()

        self._handle_combat(now)
        self._check_projectiles_wall_collision()
        
        if self.mission_type == "open":
            self._manage_spawning_open(now)
            self._manage_extraction_open(now)
            self.player.rect.clamp_ip(pygame.Rect(0, 0, OPEN_WORLD_WIDTH, OPEN_WORLD_HEIGHT))
            
            # Collisions Obstacles (Open World uses walls group)
            for w in self.walls: 
                 if self.player.rect.colliderect(w.rect):
                     separate_sprites(self.player, w, True, False)

        else:
             self._check_objective_linear()
             self.player.rect.clamp_ip(pygame.Rect(0, 0, self.level_length, self.corridor_height))
             for w in self.walls:
                if self.player.rect.colliderect(w.rect):
                    separate_sprites(self.player, w, True, False)

    def _check_projectiles_wall_collision(self):
        pygame.sprite.groupcollide(self.projectiles, self.walls, True, False)
        pygame.sprite.groupcollide(self.enemy_projectiles, self.walls, True, False)

    def _handle_combat(self, now):
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if hits:
            self.player.hp -= 1
            self.particles.add_explosion(self.player.rect.center, RED, 5)
            if self.player.hp <= 0: self.manager.switch_to("hub")

        hits = pygame.sprite.groupcollide(self.projectiles, self.enemies, True, False)
        for proj, enemies in hits.items():
            self.particles.add_explosion(proj.rect.center, NEON_GREEN, 5)
            for e in enemies:
                if e.take_damage(getattr(proj, 'damage', 1)):
                    # Gold Drop Logic
                    g = Gold(e.rect.center, value=10)
                    self.golds.add(g)
                    self.camera_group.add(g)
                    
                    self.player.xp += 10
                    e.kill()
        
        # Player -> Gold
        hits = pygame.sprite.spritecollide(self.player, self.golds, True)
        if hits:
             for g in hits:
                 self.player.gold += g.value

    def _manage_spawning_open(self, now):
        if len(self.enemies) < MAX_ENEMIES and random.random() < 0.02:
             e = self._create_enemy(random.choice(["basic", "drone", "zombie"]))
             # Spawn around player
             angle = random.uniform(0, 6.28)
             dist = random.uniform(500, 900)
             ex = self.player.rect.centerx + math.cos(angle)*dist
             ey = self.player.rect.centery + math.sin(angle)*dist
             e.rect.center = (max(50, min(ex, OPEN_WORLD_WIDTH-50)), max(50, min(ey, OPEN_WORLD_HEIGHT-50)))
             self.enemies.add(e)
             self.camera_group.add(e)

    def _manage_extraction_open(self, now):
        if not self.extraction_active and hasattr(self, 'extraction_timer') and now > self.extraction_timer:
             self.extraction_active = True
             while True:
                ex = random.randint(200, OPEN_WORLD_WIDTH-200)
                ey = random.randint(200, OPEN_WORLD_HEIGHT-200)
                if pygame.math.Vector2(ex - self.player.rect.centerx, ey - self.player.rect.centery).length() > 1500:
                    self.extraction_zone = pygame.Rect(ex, ey, 200, 200)
                    break
             print("Extraction Disponible !")

    def _check_objective_linear(self):
        pass

    def handle_input(self, events):
        if self.dialogue_mgr.active:
            for event in events:
                self.dialogue_mgr.handle_input(event)
            return

        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        
        if keys[pygame.K_SPACE]:
            if now - self.player.last_shot >= self.player.shot_cooldown // 2:
                 target = self._get_nearest_target()
                 self._shoot(target, now)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                 world_pos = pygame.math.Vector2(event.pos) + self.camera_group.offset
                 self._shoot(world_pos, now)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # PAUSE MENU
                    self.manager.switch_to("pause", previous_scene=self)
                elif event.key == pygame.K_e:
                    self._check_interactions()

    def _check_interactions(self):
        for npc in self.npcs:
            if self.player.rect.colliderect(npc.rect.inflate(80, 80)):
                self.dialogue_mgr.start_dialogue(npc.name, npc.dialogue_text)
                return
        
        if self.player.rect.colliderect(self.extraction_zone):
            self.dialogue_mgr.start_dialogue("SYSTÈME", "Cible neutralisée. Mission accomplie.", 
                                             callback=lambda x: self.manager.switch_to("hub"))

    def _shoot(self, target_pos, now):
        proj = self.player.shoot(target_pos, now)
        if proj:
            self.projectiles.add(proj)
            self.camera_group.add(proj)

    def _get_nearest_target(self):
        if not self.enemies: return pygame.mouse.get_pos() + self.camera_group.offset
        p_pos = pygame.math.Vector2(self.player.rect.center)
        coda = sorted(self.enemies.sprites(), key=lambda e: (pygame.math.Vector2(e.rect.center) - p_pos).length_squared())
        return coda[0].rect.center

    def _check_objective(self):
        pass

    def draw(self, screen):
        self.camera_group.custom_draw(self.player)
        self.particles.draw(screen) 
        
        # UI Objectif
        self._draw_hud(screen)
        
        # Extraction Arrow
        if self.mission_type == "open" and self.extraction_active:
             self._draw_extraction_arrow(screen)

        # Zone de fin (Visual)
        fin_rect = self.extraction_zone.copy()
        fin_rect.topleft -= self.camera_group.offset
        # Only draw if on screen roughly? Pygame handles it but optimization is good.
        pygame.draw.rect(screen, NEON_PINK, fin_rect, 4)
        ts = self.assets.get_font(None, 30).render("CIBLE / FIN DE MISSION", True, NEON_PINK)
        screen.blit(ts, (fin_rect.centerx - ts.get_width()//2, fin_rect.y - 40))

        # Prompts
        if not self.dialogue_mgr.active:
            for npc in self.npcs:
                 # Check proximity properly
                if self.player.rect.colliderect(npc.rect.inflate(80, 80)):
                    txt = self.assets.get_font(None, 24).render("[E] Parler", True, GREEN)
                    rect = txt.get_rect(center=(npc.rect.centerx - self.camera_group.offset.x, npc.rect.top - 20 - self.camera_group.offset.y))
                    screen.blit(txt, rect)
            
            if self.player.rect.colliderect(self.extraction_zone):
                 txt = self.assets.get_font(None, 24).render("[E] TERMINER", True, NEON_PINK)
                 rect = txt.get_rect(center=(WIDTH//2, HEIGHT - 100))
                 screen.blit(txt, rect)

        self.dialogue_mgr.draw(screen)

    def _draw_extraction_arrow(self, screen):
        # Calculate angle
        p_pos = pygame.math.Vector2(self.player.rect.center)
        t_pos = pygame.math.Vector2(self.extraction_zone.center)
        diff = t_pos - p_pos
        
        if diff.length() < 0.1: return # Too close
        
        # If onscreen, maybe unnecessary? But safe.
        angle = math.degrees(math.atan2(diff.y, diff.x))
        
        # Draw Arrow at edge of screen
        cx, cy = WIDTH // 2, HEIGHT // 2
        radius = 250
        
        arrow_pos = pygame.math.Vector2(cx, cy) + diff.normalize() * radius
        
        # Draw Arrow shape (Triangle)
        # Rotate triangle
        # Tip
        tip = arrow_pos
        # Base
        base_center = arrow_pos - diff.normalize() * 20
        # Perpendicular
        perp = pygame.math.Vector2(-diff.y, diff.x).normalize() * 10
        
        left = base_center + perp
        right = base_center - perp
        
        pygame.draw.polygon(screen, NEON_PINK, [tip, left, right])

    def _draw_hud(self, screen):
        # Barre de vie
        pygame.draw.rect(screen, RED, (10, 10, 200, 20))
        ratio = max(0, self.player.hp / self.player.max_hp)
        pygame.draw.rect(screen, GREEN, (10, 10, 200 * ratio, 20))
        pygame.draw.rect(screen, WHITE, (10, 10, 200, 20), 2)
        
        # Gold
        font = self.assets.get_font(None, 24)
        g_txt = font.render(f"GOLD: {int(self.player.gold)}", True, GOLD_COLOR)
        screen.blit(g_txt, (10, 40))
        
        # Extraction Timer
        if self.mission_type == "open":
            now = pygame.time.get_ticks()
            if not self.extraction_active:
                remaining = max(0, (self.extraction_timer - now) // 1000)
                timer_txt = font.render(f"EXTRACTION DANS: {remaining}s", True, NEON_BLUE)
                screen.blit(timer_txt, (WIDTH//2 - timer_txt.get_width()//2, 50))
            else:
                # Direction Text
                p_pos = pygame.math.Vector2(self.player.rect.center)
                t_pos = pygame.math.Vector2(self.extraction_zone.center)
                diff = t_pos - p_pos
                
                # Determine Cardinal Direction
                direction_str = ""
                if diff.y < -diff.x and diff.y < diff.x: direction_str = "NORD"
                elif diff.y > -diff.x and diff.y > diff.x: direction_str = "SUD"
                elif diff.y > -diff.x and diff.y < diff.x: direction_str = "EST"
                elif diff.y < -diff.x and diff.y > diff.x: direction_str = "OUEST"
                
                # Refined diagonals
                angle = math.degrees(math.atan2(diff.y, diff.x))
                if -22.5 < angle <= 22.5: direction_str = "EST"
                elif 22.5 < angle <= 67.5: direction_str = "SUD-EST"
                elif 67.5 < angle <= 112.5: direction_str = "SUD"
                elif 112.5 < angle <= 157.5: direction_str = "SUD-OUEST"
                elif 157.5 < angle <= 180 or -180 <= angle <= -157.5: direction_str = "OUEST"
                elif -157.5 < angle <= -112.5: direction_str = "NORD-OUEST"
                elif -112.5 < angle <= -67.5: direction_str = "NORD"
                elif -67.5 < angle <= -22.5: direction_str = "NORD-EST"

                status_txt = font.render(f"EXTRACTION DISPONIBLE: {direction_str}", True, NEON_PINK)
                screen.blit(status_txt, (WIDTH//2 - status_txt.get_width()//2, 50))
