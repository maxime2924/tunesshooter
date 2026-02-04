import pygame
import random
import math
from settings import *
from scenes import Scene
from asset_manager import AssetManager
from camera import CameraGroup
from particles import ParticleSystem
from entity import separate_sprites, Entity, AnimatedEntity
from dialogue import DialogueManager
from enemy import Enemy
from ranged_enemy import RangedEnemy
from enemies_variants import Zombie, Robot
from gold import Gold

class Wall(Entity):
    def __init__(self, groups, pos, size):
        super().__init__(groups, pos=pos)
        self.image = pygame.Surface(size)
        self.image.fill((20, 20, 20)) # Gris foncé / Noir
        pygame.draw.rect(self.image, NEON_BLUE, (0, 0, size[0], size[1]), 2)
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect

class LoreNPC(Entity):
    def __init__(self, groups, pos, color, name, dialogue_text):
        assets = AssetManager()
        img = assets.get_image("punk_npc.png")
        if not img:
            img = pygame.Surface((50, 80))
            img.fill(color)
        super().__init__(groups, image=img, pos=pos, scale=(50, 80))
        
        # Tinting / Coloring (Optional, maybe just a colored circle overhead?)
        # For now, let's just use the sprite.
        # But user wants "colored square" style or distinction?
        # User said "I didn't find the png". 
        # I will add a colored indicator above the NPC.
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
            self.width, self.height = MAP_WIDTH, MAP_HEIGHT
            self.camera_group.set_tiled_background("grass.png", MAP_WIDTH, MAP_HEIGHT)
            self.player.rect.center = (MAP_WIDTH // 2, MAP_HEIGHT // 2)
            self._build_level_open()

        if self.player not in self.camera_group:
            self.camera_group.add(self.player)

    def _build_level_linear(self):
        # 1. Murs (Haut et Bas)
        wall_thick = 50
        self.walls.add(Wall([self.camera_group, self.walls], (0, 0), (self.level_length, wall_thick)))
        self.walls.add(Wall([self.camera_group, self.walls], (0, self.corridor_height - wall_thick), (self.level_length, wall_thick)))
        self.walls.add(Wall([self.camera_group, self.walls], (-wall_thick, 0), (wall_thick, self.corridor_height)))

        # 2. Ennemis (Progressif)
        self._spawn_enemy_wave_linear(500, self.corridor_height//2, count=1, type="basic")
        self._spawn_enemy_wave_linear(1500, self.corridor_height//2, count=2, type="drone")
        self._spawn_enemy_wave_linear(2500, self.corridor_height//2, count=3, type="zombie")
        self._spawn_enemy_wave_linear(4000, self.corridor_height//2, count=4, type="mixed")
        self._spawn_enemy_wave_linear(6000, self.corridor_height//2, count=6, type="elite")

        # 3. Lore
        self._spawn_lore_npc(1000, "Le Rescapé", (0, 255, 255), "Ils arrivent... Ne les laisse pas couper la musique !")
        
        # 4. Fin
        self.extraction_zone = pygame.Rect(self.level_length - 400, 200, 300, 400)

    def _build_level_open(self):
        # Spawn initial
        self._spawn_initial_enemies_open(20)
        # Extraction (Activée plus tard ou dispo ?)
        self.extraction_active = False 
        self.extraction_timer = pygame.time.get_ticks() + 60000 # 60s avant extraction
        self.extraction_zone = pygame.Rect(0, 0, 0, 0) # Hidden

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
        rect = pygame.Rect(0, 0, 100, 100) # Dummy
        if type == "basic": return Enemy(rect, hp=3, damage=1)
        elif type == "drone": return RangedEnemy(rect, hp=2, damage=1)
        elif type == "zombie": return Zombie(rect, hp=5, damage=2)
        elif type == "mixed": return Robot(rect, hp=4, damage=1) 
        elif type == "elite": return Robot(rect, hp=10, damage=3)
        return Enemy(rect, hp=3, damage=1)

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
        
        if self.mission_type == "open":
            self._manage_spawning_open(now)
            self._manage_extraction_open(now)
            self.player.rect.clamp_ip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))
        else:
             self._check_objective_linear()
             self.player.rect.clamp_ip(pygame.Rect(0, 0, self.level_length, self.corridor_height))
             # Collisions Murs (Lié par défaut seulement en linear)
             for w in self.walls:
                if self.player.rect.colliderect(w.rect):
                    separate_sprites(self.player, w, True, False)

    def _manage_spawning_open(self, now):
        if len(self.enemies) < MAX_ENEMIES and random.random() < 0.02:
             e = self._create_enemy(random.choice(["basic", "drone", "zombie"]))
             # Spawn around player but not too close
             angle = random.uniform(0, 6.28)
             dist = random.uniform(500, 900)
             ex = self.player.rect.centerx + math.cos(angle)*dist
             ey = self.player.rect.centery + math.sin(angle)*dist
             e.rect.center = (max(50, min(ex, MAP_WIDTH-50)), max(50, min(ey, MAP_HEIGHT-50)))
             self.enemies.add(e)
             self.camera_group.add(e)

    def _manage_extraction_open(self, now):
        # Afficher extraction après delai
        if not self.extraction_active and hasattr(self, 'extraction_timer') and now > self.extraction_timer:
             self.extraction_active = True
             # Random spot far away
             while True:
                ex = random.randint(200, MAP_WIDTH-200)
                ey = random.randint(200, MAP_HEIGHT-200)
                if pygame.math.Vector2(ex - self.player.rect.centerx, ey - self.player.rect.centery).length() > 1500:
                    self.extraction_zone = pygame.Rect(ex, ey, 200, 200)
                    break
             print("Extraction Disponible !")

    def _check_objective_linear(self):
        # Verification de fin faite via interaction 'E', mais on pourrait avoir d'autres triggers
        pass

    def handle_input(self, events):
        if self.dialogue_mgr.active:
            for event in events:
                self.dialogue_mgr.handle_input(event)
            return

        now = pygame.time.get_ticks()
        keys = pygame.key.get_pressed()
        
        # Tir
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
                    self.manager.switch_to("hub")
                elif event.key == pygame.K_e:
                    self._check_interactions()

    def _check_interactions(self):
        # NPCs
        for npc in self.npcs:
            if self.player.rect.colliderect(npc.rect.inflate(80, 80)):
                self.dialogue_mgr.start_dialogue(npc.name, npc.dialogue_text)
                return
        
        # Objectif Fin
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
        # On peut viser le plus proche devant soi
        coda = sorted(self.enemies.sprites(), key=lambda e: (pygame.math.Vector2(e.rect.center) - p_pos).length_squared())
        return coda[0].rect.center

    def _handle_combat(self, now):
        # Collisions / Dégâts (Similaire à avant)
        hits = pygame.sprite.spritecollide(self.player, self.enemies, False)
        if hits:
            self.player.hp -= 1
            self.particles.add_explosion(self.player.rect.center, RED, 5)
            if self.player.hp <= 0: self.manager.switch_to("hub")

        pygame.sprite.groupcollide(self.projectiles, self.walls, True, False)
        
        hits = pygame.sprite.groupcollide(self.projectiles, self.enemies, True, False)
        for proj, enemies in hits.items():
            self.particles.add_explosion(proj.rect.center, NEON_GREEN, 5)
            for e in enemies:
                if e.take_damage(getattr(proj, 'damage', 1)):
                    e.kill()
                    self.player.add_xp(10)

        hits = pygame.sprite.spritecollide(self.player, self.enemy_projectiles, True)
        if hits:
            self.player.hp -= 1
            if self.player.hp <= 0: self.manager.switch_to("hub")

    def _check_objective(self):
        pass

    def draw(self, screen):
        self.camera_group.custom_draw(self.player)
        self.particles.draw(screen) 
        
        # UI Objectif
        self._draw_hud(screen)

        # Zone de fin
        fin_rect = self.extraction_zone.copy()
        fin_rect.topleft -= self.camera_group.offset
        pygame.draw.rect(screen, NEON_PINK, fin_rect, 4)
        ts = self.assets.get_font(None, 30).render("CIBLE / FIN DE MISSION", True, NEON_PINK)
        screen.blit(ts, (fin_rect.centerx - ts.get_width()//2, fin_rect.y - 40))

        # Prompts
        if not self.dialogue_mgr.active:
            for npc in self.npcs:
                if self.player.rect.colliderect(npc.rect.inflate(80, 80)):
                    txt = self.assets.get_font(None, 24).render("[E] Parler", True, GREEN)
                    rect = txt.get_rect(center=(npc.rect.centerx - self.camera_group.offset.x, npc.rect.top - 20 - self.camera_group.offset.y))
                    screen.blit(txt, rect)
            
            if self.player.rect.colliderect(self.extraction_zone):
                 txt = self.assets.get_font(None, 24).render("[E] TERMINER", True, NEON_PINK)
                 rect = txt.get_rect(center=(WIDTH//2, HEIGHT - 100))
                 screen.blit(txt, rect)

        self.dialogue_mgr.draw(screen)

    def _draw_hud(self, screen):
        # Barre de vie
        pygame.draw.rect(screen, RED, (10, 10, 200, 20))
        ratio = max(0, self.player.hp / self.player.max_hp)
        pygame.draw.rect(screen, GREEN, (10, 10, 200 * ratio, 20))
        pygame.draw.rect(screen, WHITE, (10, 10, 200, 20), 2)
