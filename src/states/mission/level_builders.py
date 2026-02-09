import pygame
import random
import math
import os
from core.settings import *
from entities.obstacles import Wall, Obstacle

class LevelBuilders:
    
    def _build_level_zen(self):
        path_y_center = self.corridor_height // 2
        path_width = 300
        
        pixel_assets = []
        base_path = os.path.join(self.assets.assets_path, "assets_pixel_50x50")
        if os.path.exists(base_path):
             pixel_assets = [os.path.join(base_path, f) for f in os.listdir(base_path) if f.endswith(".png")]
        
        self.walls.add(Wall([self.camera_group, self.walls], (0, -50), (self.level_length, 50)))
        self.walls.add(Wall([self.camera_group, self.walls], (0, self.corridor_height), (self.level_length, 50)))
        self.walls.add(Wall([self.camera_group, self.walls], (-50, 0), (50, self.corridor_height)))
        self.walls.add(Wall([self.camera_group, self.walls], (self.level_length, 0), (50, self.corridor_height)))

        for x in range(0, self.level_length, 100):
            y_offset = math.sin(x / 1000) * 300
            current_y = path_y_center + y_offset
            
            if pixel_assets:
                 img_path = random.choice(pixel_assets)
                 try:
                     img = pygame.image.load(img_path).convert_alpha()
                     img = pygame.transform.scale(img, (60, 60))
                     
                     if random.random() < 0.3:
                         oy = random.randint(50, int(current_y - path_width//2 - 60))
                         obs = Obstacle([self.camera_group, self.walls], (x, oy), (40, 40))
                         obs.image = img
                     
                     if random.random() < 0.3:
                         oy = random.randint(int(current_y + path_width//2), self.corridor_height - 100)
                         obs = Obstacle([self.camera_group, self.walls], (x, oy), (40, 40))
                         obs.image = img
                 except: pass

        self.extraction_zone = pygame.Rect(self.level_length - 400, path_y_center - 100, 200, 200)
        self.extraction_active = True

    def _build_level_linear(self):
        segments = []
        
        start_x = self.level_length // 2
        start_y = self.corridor_height - 600
        current_x, current_y = start_x, start_y
        
        segments.append(pygame.Rect(current_x - 300, current_y - 300, 600, 600))
        
        steps = 8
        direction = 1
        
        for i in range(steps):
             v_height = random.randint(600, 1000)
             new_y = current_y - v_height
             segments.append(pygame.Rect(current_x - 200, new_y - 200, 400, v_height + 400))
             current_y = new_y
             
             if i < steps - 1:
                 h_width = random.randint(800, 1500)
                 new_x = current_x + (h_width * direction)
                 if new_x > self.level_length - 200: new_x = self.level_length - 200; direction *= -1
                 if new_x < 200: new_x = 200; direction *= -1
                 
                 left = min(current_x, new_x)
                 width = abs(new_x - current_x)
                 segments.append(pygame.Rect(left - 200, current_y - 200, width + 400, 400))
                 
                 current_x = new_x
                 direction *= -1
        
        segments.append(pygame.Rect(current_x - 400, current_y - 400, 800, 800))
        self.extraction_zone = pygame.Rect(current_x - 100, current_y - 100, 200, 200)
        self.player.rect.center = (start_x, start_y)

        candidate_walls = []
        wt = 50
        for r in segments:
             candidate_walls.append(pygame.Rect(r.left, r.top - wt, r.width, wt))
             candidate_walls.append(pygame.Rect(r.left, r.bottom, r.width, wt))
             candidate_walls.append(pygame.Rect(r.left - wt, r.top, wt, r.height))
             candidate_walls.append(pygame.Rect(r.right, r.top, wt, r.height))
             
        final_walls = []
        for w in candidate_walls:
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
             
        for seg in segments[1:]:
            if random.random() < 0.7:
                self._spawn_enemy_wave_linear(seg.centerx, seg.centery, random.randint(1, 3), "mixed")
                
        if len(segments) > 3:
            r = segments[3]
            self._spawn_lore_npc(r.centerx, "Le Rescapé", (0, 255, 255), "Ils arrivent... Ne les laisse pas couper la musique !")

    def _build_level_open(self):
        for _ in range(40):
             ox = random.randint(100, self.width - 100)
             oy = random.randint(100, self.height - 100)
             if pygame.Vector2(ox - self.width//2, oy - self.height//2).length() > 300:
                 Obstacle([self.camera_group, self.walls], (ox, oy), (random.randint(60, 120), random.randint(60, 120)))

        self._spawn_initial_enemies_open(50)
        self.extraction_active = False 
        self.extraction_timer = pygame.time.get_ticks() + 10000 
        self.extraction_zone = pygame.Rect(0, 0, 0, 0)

    def _setup_vertical_mission(self):
        self.width = 1200
        self.height = 6000
        self.level_length = self.height
        self.corridor_height = self.height
        
        self.camera_group.set_tiled_background("concert_floor.png", self.width, self.height)
        
        spawn_x = self.width // 2
        spawn_y = self.height - 300
        self.player.rect.center = (spawn_x, spawn_y)
        
        self._create_corridor_walls()
        self._spawn_smart_enemies()
        self._spawn_boss()
        
        self.boss_defeated = False
        self.extraction_zone = pygame.Rect(self.width // 2 - 150, 100, 300, 200)

    def _create_corridor_walls(self):
        wall_thickness = 50
        segment_height = 200
        
        for y in range(0, self.height, segment_height):
            wall = Wall(
                [self.camera_group, self.walls],
                pos=(0, y),
                size=(wall_thickness, segment_height)
            )
        
        for y in range(0, self.height, segment_height):
            wall = Wall(
                [self.camera_group, self.walls],
                pos=(self.width - wall_thickness, y),
                size=(wall_thickness, segment_height)
            )
        
        obstacle_positions = [
            (300, 5200), (900, 5200),
            (200, 4500), (1000, 4500),
            (400, 3800), (800, 3800),
            (250, 3000), (950, 3000),
            (500, 2200), (700, 2200),
            (300, 1500), (900, 1500),
            (400, 800), (800, 800),
        ]
        
        for ox, oy in obstacle_positions:
            obstacle = Obstacle(
                [self.camera_group, self.walls],
                pos=(ox, oy),
                size=(100, 100)
            )

    def _spawn_smart_enemies(self):
        from entities.smart_enemy import SmartEnemy
        
        enemy_configs = [
            ((600, 5000), [(500, 5000), (700, 5000)], 5),
            ((300, 4600), [(200, 4600), (400, 4600)], 5),
            ((900, 4600), [(800, 4600), (1000, 4600)], 5),
            
            ((600, 4000), [(600, 3900), (600, 4100)], 6),
            ((400, 3500), [(300, 3500), (500, 3500)], 6),
            ((800, 3500), [(700, 3500), (900, 3500)], 6),
            
            ((300, 2800), [(250, 2700), (350, 2900)], 7),
            ((900, 2800), [(850, 2700), (950, 2900)], 7),
            
            ((600, 2000), [(500, 2000), (700, 2000)], 8),
            ((400, 1600), [(350, 1600), (450, 1600)], 8),
            ((800, 1600), [(750, 1600), (850, 1600)], 8),
            
            ((300, 1000), [(250, 900), (350, 1100)], 10),
            ((900, 1000), [(850, 900), (950, 1100)], 10),
            ((600, 600), [(500, 600), (700, 600)], 10),
        ]
        
        for spawn_pos, patrol_points, hp in enemy_configs:
            enemy = SmartEnemy(spawn_pos, patrol_points, hp=hp)
            self.enemies.add(enemy)
            self.camera_group.add(enemy)

    def _spawn_boss(self):
        from entities.boss import Boss
        
        boss_pos = (self.width // 2, 300)
        self.boss = Boss(boss_pos, hp=500)
        self.enemies.add(self.boss)
        self.camera_group.add(self.boss)
