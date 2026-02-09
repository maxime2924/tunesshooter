import pygame
import math
import random
from core.settings import *
from core.asset_manager import AssetManager


class Boss(pygame.sprite.Sprite):
    def __init__(self, pos, hp=500):
        super().__init__()
        
        assets = AssetManager()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 120
        
        try:
            sprite_path = "assset-mob+boss/assset-mob+boss/Boss/Idle.png"
            sprite_sheet = assets.get_image(sprite_path)
            if sprite_sheet:
                sheet_width = sprite_sheet.get_width()
                sheet_height = sprite_sheet.get_height()
                frame_width = sheet_width // 4
                
                for i in range(4):
                    frame = pygame.Surface((frame_width, sheet_height), pygame.SRCALPHA)
                    frame.blit(sprite_sheet, (0, 0), (i * frame_width, 0, frame_width, sheet_height))
                    scaled_frame = pygame.transform.scale(frame, (120, 120)).convert_alpha()
                    self.frames.append(scaled_frame)
                
                self.image = self.frames[0]
            else:
                self.image = pygame.Surface((100, 100))
                self.image.fill((150, 0, 150))
        except Exception as e:
            print(f"Failed to load boss sprite: {e}")
            self.image = pygame.Surface((100, 100))
            self.image.fill((150, 0, 150))
        
        self.rect = self.image.get_rect(center=pos)
        
        self.hp = hp
        self.max_hp = hp
        self.damage = 3
        self.speed = 1.5
        
        self.last_shot = 0
        self.shot_cooldown = 800
        self.projectile_speed = 7
        self.attack_range = 400
        
        self.phase = 1
        self.update_phase()
        
        self.attack_pattern = "burst"
        self.pattern_timer = 0
        self.pattern_duration = 3000
        
        self.move_timer = 0
        self.move_duration = 2000
        self.target_pos = pos
        
    def update_phase(self):
        hp_percent = self.hp / self.max_hp
        
        if hp_percent > 0.66:
            self.phase = 1
            self.shot_cooldown = 800
        elif hp_percent > 0.33:
            self.phase = 2
            self.shot_cooldown = 600
            self.speed = 2
        else:
            self.phase = 3
            self.shot_cooldown = 400
            self.speed = 2.5
    
    def update(self, player, now):
        self.update_phase()
        
        if now - self.move_timer > self.move_duration:
            self._choose_new_position(player)
            self.move_timer = now
        
        dx = self.target_pos[0] - self.rect.centerx
        dy = self.target_pos[1] - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 5:
            move_x = (dx / distance) * self.speed
            move_y = (dy / distance) * self.speed
            self.rect.x += move_x
            self.rect.y += move_y
        
        if now - self.pattern_timer > self.pattern_duration:
            self.attack_pattern = random.choice(["burst", "spiral", "spread"])
            self.pattern_timer = now
        
        if self.frames and len(self.frames) > 0:
            if now - self.animation_timer > self.animation_speed:
                self.animation_timer = now
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
    
    def _choose_new_position(self, player):
        arena_center = (600, 300)
        arena_radius = 200
        
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(50, arena_radius)
        
        self.target_pos = (
            arena_center[0] + math.cos(angle) * distance,
            arena_center[1] + math.sin(angle) * distance
        )
    
    def shoot(self, player, now):
        if now - self.last_shot < self.shot_cooldown:
            return []
        
        self.last_shot = now
        projectiles = []
        
        if self.attack_pattern == "burst":
            projectiles.append(self._create_aimed_projectile(player))
        
        elif self.attack_pattern == "spiral":
            num_projectiles = 8 if self.phase >= 2 else 5
            for i in range(num_projectiles):
                angle = (360 / num_projectiles) * i + (now / 10) % 360
                projectiles.append(self._create_angled_projectile(angle))
        
        elif self.attack_pattern == "spread":
            num_projectiles = 5 if self.phase >= 3 else 3
            base_angle = self._angle_to_player(player)
            spread = 30
            
            for i in range(num_projectiles):
                offset = (i - num_projectiles // 2) * (spread / num_projectiles)
                angle = base_angle + offset
                projectiles.append(self._create_angled_projectile(angle))
        
        return projectiles
    
    def _create_aimed_projectile(self, player):
        from entities.collectibles import Projectile
        
        start = pygame.math.Vector2(self.rect.center)
        target = pygame.math.Vector2(player.rect.center)
        direction = target - start
        
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        
        velocity = direction.normalize() * self.projectile_speed
        return Projectile(self.rect.center, velocity, None, damage=self.damage, is_enemy=True)
    
    def _create_angled_projectile(self, angle_degrees):
        from entities.collectibles import Projectile
        
        angle_rad = math.radians(angle_degrees)
        velocity = pygame.math.Vector2(
            math.cos(angle_rad) * self.projectile_speed,
            math.sin(angle_rad) * self.projectile_speed
        )
        
        return Projectile(self.rect.center, velocity, None, damage=self.damage, is_enemy=True)
    
    def _angle_to_player(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        return math.degrees(math.atan2(dy, dx))
    
    def take_damage(self, amount=1):
        self.hp -= amount
        return self.hp <= 0
    
    def draw_health_bar(self, surface, camera_offset):
        bar_width = 400
        bar_height = 30
        bar_x = (surface.get_width() - bar_width) // 2
        bar_y = 20
        
        pygame.draw.rect(surface, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        
        health_percent = max(0, self.hp / self.max_hp)
        fill_width = int(bar_width * health_percent)
        
        colors = {1: (255, 0, 0), 2: (255, 100, 0), 3: (255, 0, 255)}
        color = colors.get(self.phase, (255, 0, 0))
        
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height))
        pygame.draw.rect(surface, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 3)
        
        font = pygame.font.Font(None, 24)
        text = font.render(f"BOSS - Phase {self.phase}", True, (255, 255, 255))
        text_rect = text.get_rect(center=(bar_x + bar_width // 2, bar_y - 15))
        surface.blit(text, text_rect)
