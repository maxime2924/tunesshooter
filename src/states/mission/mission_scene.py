import pygame
import random
import math
from core.settings import *
from states.scenes import Scene
from core.asset_manager import AssetManager
from core.camera import CameraGroup
from ui.particles import ParticleSystem
from entities.entity import separate_sprites
from ui.dialogue import DialogueManager
from entities.player import Player
from entities.enemy import Enemy
from entities.melee_enemy import MeleeEnemy
from entities.ranged_enemy import RangedEnemy
from entities.collectibles import Projectile, Gold

from states.mission.level_builders import LevelBuilders
from states.mission.mission_helpers import MissionHelpers

class MissionScene(Scene, LevelBuilders, MissionHelpers):
    def __init__(self, manager):
        super().__init__(manager)
        self.assets = AssetManager()
        
        self.level_length = 8000
        self.corridor_height = 800
        self.width = self.level_length
        self.height = self.corridor_height
        
        self.player = self.manager.shared_data.get('player')
        
        self.camera_group = CameraGroup()
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
        
        self.camera_group.add(self.player)
        
        self.failed = False
        self.finished = False
        self.extraction_zone = pygame.Rect(self.level_length - 400, 200, 300, 400)
        
        self.lore_npcs = []

    def on_enter(self, **kwargs):
        self.mission_type = kwargs.get('mission_type', 'linear')
        
        if self.mission_type == "Extraction Illimitée": self.mission_type = "open"
        else: self.mission_type = "linear"

        print(f"Lancement Mission : {self.mission_type}")
        
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
            self._setup_vertical_mission()
            
        elif self.mission_type == "Promenade Zen":
            self.level_length = 20000 
            self.corridor_height = 1200
            self.width = self.level_length
            self.height = self.corridor_height
            self.camera_group.set_tiled_background("grass.png", self.level_length, self.corridor_height)
            self.player.rect.topleft = (100, self.corridor_height // 2)
            self._build_level_zen()
            
        else:
            self.width, self.height = OPEN_WORLD_WIDTH, OPEN_WORLD_HEIGHT
            self.camera_group.set_tiled_background("grass.png", OPEN_WORLD_WIDTH, OPEN_WORLD_HEIGHT)
            self.player.rect.center = (OPEN_WORLD_WIDTH // 2, OPEN_WORLD_HEIGHT // 2)
            
            for _ in range(15):
                if random.random() < 0.5:
                    e = MeleeEnemy(pygame.Rect(0, 0, self.width, self.height), hp=5, damage=2)
                else:
                    e = RangedEnemy(pygame.Rect(0, 0, self.width, self.height), hp=3, damage=1)
                
                self.enemies.add(e)
                self.camera_group.add(e)
            self._build_level_open()

    def update(self):
        if self.dialogue_mgr.active: return

        now = pygame.time.get_ticks()
        
        self.player.update()
        
        for enemy in self.enemies:
            if hasattr(enemy, 'update_ai'):
                enemy.update_ai(self.player, self.walls, now)
                enemy.update_movement(now)
                
                projectile = enemy.shoot(now)
                if projectile:
                    self.enemy_projectiles.add(projectile)
                    self.camera_group.add(projectile)
            
            elif hasattr(enemy, 'phase'):
                enemy.update(self.player, now)
                
                projectiles = enemy.shoot(self.player, now)
                if projectiles:
                    for proj in projectiles:
                        self.enemy_projectiles.add(proj)
                        self.camera_group.add(proj)
            
            elif hasattr(enemy, 'shoot') and hasattr(enemy, 'can_shoot'):
                enemy.update(self.player)
                proj_data = enemy.shoot(self.player, now)
                if proj_data:
                    from entities.collectibles import Projectile
                    velocity = proj_data['direction'] * proj_data['speed']
                    proj = Projectile(
                        proj_data['pos'],
                        velocity,
                        damage=proj_data['damage'],
                        is_enemy=True
                    )
                    self.enemy_projectiles.add(proj)
                    self.camera_group.add(proj)
            
            elif hasattr(enemy, 'attack') and hasattr(enemy, 'can_attack'):
                enemy.update(self.player)
                damage = enemy.attack(self.player, now)
                if damage > 0:
                    self.player.hp -= damage
                    print(f"Player hit by melee! HP: {self.player.hp}")
            
            else:
                enemy.update(self.player)
        
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
            
            for w in self.walls: 
                 if self.player.rect.colliderect(w.rect):
                     separate_sprites(self.player, w, True, False)

        else:
             self._check_objective_linear()
             self.player.rect.clamp_ip(pygame.Rect(0, 0, self.width, self.height))
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
                    gold_value = 3
                    xp_value = 15
                    
                    g = Gold(e.rect.center, value=gold_value)
                    self.golds.add(g)
                    self.camera_group.add(g)
                    
                    self.player.add_xp(xp_value)
                    e.kill()
        
        hits = pygame.sprite.spritecollide(self.player, self.golds, True)
        if hits:
             for g in hits:
                 self.player.gold += g.value

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
        
        camera_offset = (int(self.camera_group.offset.x), int(self.camera_group.offset.y))
        for enemy in self.enemies:
            if hasattr(enemy, 'draw_health_bar'):
                enemy.draw_health_bar(screen, camera_offset)
        
        self._draw_hud(screen)
        
        self.dialogue_mgr.draw(screen)
        
        if self.mission_type == "open" and self.extraction_active:
             self._draw_extraction_arrow(screen)

        fin_rect = self.extraction_zone.copy()
        fin_rect.topleft -= self.camera_group.offset
        pygame.draw.rect(screen, NEON_PINK, fin_rect, 4)
        ts = self.assets.get_font(None, 30).render("CIBLE / FIN DE MISSION", True, NEON_PINK)
        screen.blit(ts, (fin_rect.centerx - ts.get_width()//2, fin_rect.y - 40))

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

    def _draw_extraction_arrow(self, screen):
        p_pos = pygame.math.Vector2(self.player.rect.center)
        t_pos = pygame.math.Vector2(self.extraction_zone.center)
        diff = t_pos - p_pos
        
        if diff.length() < 0.1: return

        cx, cy = WIDTH // 2, HEIGHT // 2
        radius = 250
        
        arrow_pos = pygame.math.Vector2(cx, cy) + diff.normalize() * radius
        
        tip = arrow_pos
        base_center = arrow_pos - diff.normalize() * 20
        perp = pygame.math.Vector2(-diff.y, diff.x).normalize() * 10
        
        left = base_center + perp
        right = base_center - perp
        
        pygame.draw.polygon(screen, NEON_PINK, [tip, left, right])

    def _draw_hud(self, screen):
        pygame.draw.rect(screen, RED, (10, 10, 200, 20))
        ratio = max(0, self.player.hp / self.player.max_hp)
        pygame.draw.rect(screen, GREEN, (10, 10, 200 * ratio, 20))
        pygame.draw.rect(screen, WHITE, (10, 10, 200, 20), 2)
        
        font = self.assets.get_font(None, 24)
        g_txt = font.render(f"GOLD: {int(self.player.gold)}", True, GOLD_COLOR)
        screen.blit(g_txt, (10, 40))
        
        if self.mission_type == "open":
            now = pygame.time.get_ticks()
            if not self.extraction_active:
                remaining = max(0, (self.extraction_timer - now) // 1000)
                timer_txt = font.render(f"EXTRACTION DANS: {remaining}s", True, NEON_BLUE)
                screen.blit(timer_txt, (WIDTH//2 - timer_txt.get_width()//2, 50))
            else:
                p_pos = pygame.math.Vector2(self.player.rect.center)
                t_pos = pygame.math.Vector2(self.extraction_zone.center)
                diff = t_pos - p_pos
                
                angle = math.degrees(math.atan2(diff.y, diff.x))
                if -22.5 < angle <= 22.5: direction_str = "EST"
                elif 22.5 < angle <= 67.5: direction_str = "SUD-EST"
                elif 67.5 < angle <= 112.5: direction_str = "SUD"
                elif 112.5 < angle <= 157.5: direction_str = "SUD-OUEST"
                elif 157.5 < angle <= 180 or -180 <= angle <= -157.5: direction_str = "OUEST"
                elif -157.5 < angle <= -112.5: direction_str = "NORD-OUEST"
                elif -112.5 < angle <= -67.5: direction_str = "NORD"
                elif -67.5 < angle <= -22.5: direction_str = "NORD-EST"
                else: direction_str = "?"

                status_txt = font.render(f"EXTRACTION DISPONIBLE: {direction_str}", True, NEON_PINK)
                screen.blit(status_txt, (WIDTH//2 - status_txt.get_width()//2, 50))
