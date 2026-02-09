import pygame
import math
from core.settings import *
from core.asset_manager import AssetManager


class SmartEnemy(pygame.sprite.Sprite):
    STATE_PATROL = "patrol"
    STATE_ALERT = "alert"
    STATE_CHASE = "chase"
    STATE_ATTACK = "attack"
    
    def __init__(self, pos, patrol_points=None, hp=5, damage=1):
        super().__init__()
        
        assets = AssetManager()
        self.frames = []
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 150
        
        try:
            sprite_path = "assset-mob+boss/assset-mob+boss/Mob Ranged/Idle.png"
            sprite_sheet = assets.get_image(sprite_path)
            if sprite_sheet:
                sheet_width = sprite_sheet.get_width()
                sheet_height = sprite_sheet.get_height()
                frame_width = sheet_width // 4
                
                for i in range(4):
                    frame = pygame.Surface((frame_width, sheet_height), pygame.SRCALPHA)
                    frame.blit(sprite_sheet, (0, 0), (i * frame_width, 0, frame_width, sheet_height))
                    scaled_frame = pygame.transform.scale(frame, (60, 60)).convert_alpha()
                    self.frames.append(scaled_frame)
                
                self.image = self.frames[0]
            else:
                self.image = pygame.Surface((50, 50))
                self.image.fill((200, 50, 50))
        except Exception as e:
            print(f"Failed to load enemy sprite: {e}")
            self.image = pygame.Surface((50, 50))
            self.image.fill((200, 50, 50))
        
        self.rect = self.image.get_rect(center=pos)
        
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
        self.speed = 2
        self.chase_speed = 3
        
        self.vision_range = 300
        self.vision_angle = 90
        self.facing_angle = 0
        
        self.state = self.STATE_PATROL
        self.target = None
        self.alert_timer = 0
        self.alert_duration = 1000
        
        self.patrol_points = patrol_points or [pos]
        self.current_patrol_index = 0
        self.patrol_wait_time = 2000
        self.patrol_timer = 0
        
        self.last_shot = 0
        self.shot_cooldown = 1500
        self.projectile_speed = 6
        self.attack_range = 250
        
    def can_see_player(self, player_pos, walls):
        dx = player_pos[0] - self.rect.centerx
        dy = player_pos[1] - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > self.vision_range:
            return False
        
        angle_to_player = math.degrees(math.atan2(dy, dx))
        angle_diff = abs(angle_to_player - self.facing_angle)
        
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        if angle_diff > self.vision_angle / 2:
            return False
        
        if self._wall_blocks_view(player_pos, walls):
            return False
        
        return True
    
    def _wall_blocks_view(self, target_pos, walls):
        if not walls:
            return False
        
        start = pygame.math.Vector2(self.rect.center)
        end = pygame.math.Vector2(target_pos)
        
        for wall in walls:
            if self._line_rect_collision(start, end, wall.rect):
                return True
        
        return False
    
    def _line_rect_collision(self, start, end, rect):
        if rect.collidepoint(start) or rect.collidepoint(end):
            return True
        
        rect_center = pygame.math.Vector2(rect.center)
        to_center = rect_center - start
        to_end = end - start
        
        if to_end.length() == 0:
            return False
        
        projection = to_center.dot(to_end) / to_end.length_squared()
        
        if 0 <= projection <= 1:
            closest_point = start + to_end * projection
            if rect.collidepoint(closest_point):
                return True
        
        return False
    
    def update_ai(self, player, walls, now):
        player_pos = player.rect.center
        can_see = self.can_see_player(player_pos, walls)
        
        if self.state == self.STATE_PATROL:
            if can_see:
                self.state = self.STATE_ALERT
                self.alert_timer = now
                self.target = player
        
        elif self.state == self.STATE_ALERT:
            if can_see:
                self.state = self.STATE_CHASE
                self.target = player
            elif now - self.alert_timer > self.alert_duration:
                self.state = self.STATE_PATROL
                self.target = None
        
        elif self.state == self.STATE_CHASE:
            if not can_see:
                self.state = self.STATE_ALERT
                self.alert_timer = now
            else:
                distance = math.sqrt((player_pos[0] - self.rect.centerx)**2 + 
                                   (player_pos[1] - self.rect.centery)**2)
                if distance <= self.attack_range:
                    self.state = self.STATE_ATTACK
        
        elif self.state == self.STATE_ATTACK:
            if not can_see:
                self.state = self.STATE_ALERT
                self.alert_timer = now
            else:
                distance = math.sqrt((player_pos[0] - self.rect.centerx)**2 + 
                                   (player_pos[1] - self.rect.centery)**2)
                if distance > self.attack_range * 1.2:
                    self.state = self.STATE_CHASE
    
    def update_movement(self, now):
        if self.state == self.STATE_PATROL:
            self._patrol(now)
        elif self.state == self.STATE_ALERT:
            pass
        elif self.state == self.STATE_CHASE:
            if self.target:
                self._chase_target()
        elif self.state == self.STATE_ATTACK:
            if self.target:
                self._strafe_target()
        
        if self.frames and len(self.frames) > 0:
            if now - self.animation_timer > self.animation_speed:
                self.animation_timer = now
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
    
    def _patrol(self, now):
        if not self.patrol_points:
            return
        
        target_point = self.patrol_points[self.current_patrol_index]
        dx = target_point[0] - self.rect.centerx
        dy = target_point[1] - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 10:
            if now - self.patrol_timer > self.patrol_wait_time:
                self.current_patrol_index = (self.current_patrol_index + 1) % len(self.patrol_points)
                self.patrol_timer = now
        else:
            if distance > 0:
                move_x = (dx / distance) * self.speed
                move_y = (dy / distance) * self.speed
                self.rect.x += move_x
                self.rect.y += move_y
                self.facing_angle = math.degrees(math.atan2(dy, dx))
    
    def _chase_target(self):
        if not self.target:
            return
        
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            move_x = (dx / distance) * self.chase_speed
            move_y = (dy / distance) * self.chase_speed
            self.rect.x += move_x
            self.rect.y += move_y
            self.facing_angle = math.degrees(math.atan2(dy, dx))
    
    def _strafe_target(self):
        if not self.target:
            return
        
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        optimal_distance = self.attack_range * 0.8
        
        if distance > optimal_distance + 20:
            if distance > 0:
                move_x = (dx /distance) * self.speed
                move_y = (dy / distance) * self.speed
                self.rect.x += move_x
                self.rect.y += move_y
        elif distance < optimal_distance - 20:
            if distance > 0:
                move_x = -(dx / distance) * self.speed
                move_y = -(dy / distance) * self.speed
                self.rect.x += move_x
                self.rect.y += move_y
        
        if distance > 0:
            self.facing_angle = math.degrees(math.atan2(dy, dx))
    
    def shoot(self, now):
        if self.state != self.STATE_ATTACK or not self.target:
            return None
        
        if now - self.last_shot < self.shot_cooldown:
            return None
        
        from entities.collectibles import Projectile
        
        start = pygame.math.Vector2(self.rect.center)
        target_pos = pygame.math.Vector2(self.target.rect.center)
        direction = target_pos - start
        
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        
        velocity = direction.normalize() * self.projectile_speed
        self.last_shot = now
        
        return Projectile(self.rect.center, velocity, None, damage=self.damage, is_enemy=True)
    
    def take_damage(self, amount=1):
        self.hp -= amount
        return self.hp <= 0
    
    def draw_debug(self, surface, camera_offset):
        cone_color = (255, 255, 0, 50) if self.state == self.STATE_PATROL else (255, 0, 0, 100)
        center = (self.rect.centerx - camera_offset[0], self.rect.centery - camera_offset[1])
        
        left_angle = math.radians(self.facing_angle - self.vision_angle / 2)
        left_point = (
            center[0] + math.cos(left_angle) * self.vision_range,
            center[1] + math.sin(left_angle) * self.vision_range
        )
        
        right_angle = math.radians(self.facing_angle + self.vision_angle / 2)
        right_point = (
            center[0] + math.cos(right_angle) * self.vision_range,
            center[1] + math.sin(right_angle) * self.vision_range
        )
        
        pygame.draw.polygon(surface, cone_color, [center, left_point, right_point], 2)
        
        state_colors = {
            self.STATE_PATROL: (0, 255, 0),
            self.STATE_ALERT: (255, 255, 0),
            self.STATE_CHASE: (255, 165, 0),
            self.STATE_ATTACK: (255, 0, 0)
        }
        pygame.draw.circle(surface, state_colors.get(self.state, (255, 255, 255)), 
                         (int(center[0]), int(center[1]) - 20), 5)
