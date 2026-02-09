import pygame
import random
import math
from core.settings import *
from entities.entity import Entity
from core.asset_manager import AssetManager
from entities.enemy import Enemy
from entities.melee_enemy import MeleeEnemy
from entities.ranged_enemy import RangedEnemy
from entities.enemies_variants import Zombie, Robot
from ui.dialogue import DialogueManager

class LoreNPC(Entity):
    def __init__(self, groups, pos, color, name, dialogue_text):
        assets = AssetManager()
        img = assets.get_image("punk_npc.png")
        if not img:
            img = pygame.Surface((50, 80))
            img.fill(color)
        super().__init__(groups, image=img, pos=pos, scale=(50, 80))
        
        self.indicator = pygame.Surface((10, 10))
        self.indicator.fill(color)
        
        self.name = name
        self.dialogue_text = dialogue_text

    def update(self):
        pass

class MissionHelpers:
    
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
            e.rect.center = (random.randint(50, MAP_WIDTH-50), random.randint(50, MAP_HEIGHT-50))
            self.enemies.add(e)
            self.camera_group.add(e)

    def _spawn_lore_npc(self, x, name, color, text):
        y = random.choice([100, self.corridor_height - 150])
        npc = LoreNPC([self.camera_group, self.interactables, self.npcs], (x, y), color, name, text)

    def _manage_spawning_open(self, now):
        if len(self.enemies) < MAX_ENEMIES and random.random() < 0.02:
             e = self._create_enemy(random.choice(["basic", "drone", "zombie"]))
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
        if hasattr(self, 'boss') and self.boss not in self.enemies:
            if not hasattr(self, 'boss_defeated') or not self.boss_defeated:
                self.boss_defeated = True
                print("BOSS VAINCU ! Mission accomplie !")
                self.dialogue_mgr.start_dialogue(
                    "VICTOIRE", 
                    "Boss vaincu ! Mission accomplie. Retour au hub...",
                    callback=lambda x: self.manager.switch_to("hub")
                )
