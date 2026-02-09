import pygame
from core.asset_manager import AssetManager


class Player(pygame.sprite.Sprite):
    def __init__(self, screen_rect):
        super().__init__()
        
        import os
        assets = AssetManager()

        sprite_path = os.path.join(assets.assets_path, "player_daft_clean.png")
        try:
            raw_image = assets.get_image("player_daft_clean.png")
            
            if raw_image:
                self.cell_width = 100
                self.cell_height = 100
                
                self.sprites = {
                    'down': [],
                    'up': [],
                    'left': [],
                    'right': []
                }
                
                direction_map = {
                    'down': 0,
                    'up': 1,
                    'right': 3,
                    'left': 4
                }
                
                for direction, row in direction_map.items():
                    for col in range(5):
                        rect = pygame.Rect(col * self.cell_width, row * self.cell_height, 
                                         self.cell_width, self.cell_height)
                        frame = raw_image.subsurface(rect)
                        scaled = pygame.transform.scale(frame, (64, 64))
                        self.sprites[direction].append(scaled)

                self.current_direction = 'down'
                self.current_frame = 0
                self.image = self.sprites[self.current_direction][0]
            else:
                raise Exception("Image loaded as None")
            
        except Exception as e:
            print(f"Failed to load Daft Punk sprite: {e}")
            self.image = pygame.Surface((40, 40))
            self.image.fill((0, 0, 255))
            self.current_direction = 'down'
            self.current_frame = 0
            self.sprites = None
        
        self.rect = self.image.get_rect(center=(screen_rect.width // 2, screen_rect.height // 2))
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        self.screen_rect = screen_rect

        self.gold = 100
        self.banked_gold = 50
        self.gold_per_second = 0
        self.last_passive_income = 0

        self.last_shot = 0
        self.shot_cooldown = 150
        self.projectile_speed = 18
        self.projectile_damage = 2

        self.xp = 0
        self.level = 1
        self.xp_to_next_level = 100

        self.upgrade_levels = {
            'rapid_fire': 0,
            'move_speed': 0,
            'projectile_damage': 0,
            'projectile_speed': 0
        }
    
    def add_xp(self, amount):
        self.xp += amount
        
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            print(f"LEVEL UP! Now level {self.level}. Next level needs {self.xp_to_next_level} XP")


    def update_passive_income(self, current_time):
        if self.gold_per_second > 0:
            if current_time - self.last_passive_income >= 1000:
                self.banked_gold += self.gold_per_second
                self.last_passive_income = current_time
                print(f"Revenu passif: +{self.gold_per_second}g (Total Banque: {self.banked_gold})")

    def add_xp(self, amount):
        self.xp += amount
        req_xp = self.level * 100
        while self.xp >= req_xp:
            self.xp -= req_xp
            self.level += 1
            self.max_hp += 10
            self.hp = self.max_hp
            print(f"LEVEL UP! Niveau {self.level}")
            req_xp = self.level * 100

    def handle_input(self, keys):
        dx = 0
        dy = 0
        
        moved = False
        new_direction = self.current_direction
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q]:
            dx -= self.speed
            new_direction = 'left'
            moved = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.speed
            new_direction = 'right'
            moved = True
        
        if keys[pygame.K_UP] or keys[pygame.K_w] or keys[pygame.K_z]:
            dy -= self.speed
            if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q] or 
                   keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                new_direction = 'up'
            moved = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.speed
            if not (keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q] or 
                   keys[pygame.K_RIGHT] or keys[pygame.K_d]):
                new_direction = 'down'
            moved = True
        
        return dx, dy, moved, new_direction

    def update(self):
        keys = pygame.key.get_pressed()
        
        dx, dy, moved, new_direction = self.handle_input(keys)
        
        if moved and new_direction != self.current_direction:
            self.current_direction = new_direction
            if hasattr(self, 'sprites') and self.sprites:
                if self.current_direction in self.sprites and len(self.sprites[self.current_direction]) > 0:
                    self.image = self.sprites[self.current_direction][0]
        
        self.rect.x += dx
        self.rect.y += dy
        
        if self.screen_rect:
            self.rect.clamp_ip(self.screen_rect)

    def shoot(self, target_pos, now):
        if now - self.last_shot < self.shot_cooldown:
            return None
        from entities.collectibles import Projectile
        start = pygame.math.Vector2(self.rect.center)
        target = pygame.math.Vector2(target_pos)
        direction = target - start
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        velocity = direction.normalize() * self.projectile_speed
        self.last_shot = now
        
        assets = AssetManager()
        laser = assets.get_sound("laser.wav")
        if laser:
            laser.set_volume(0.4)
            laser.play()
            
        return Projectile(self.rect.center, velocity, self.screen_rect, damage=self.projectile_damage)

    def heal_full(self):
        self.hp = self.max_hp

    def reset(self):
        self.hp = self.max_hp
        self.gold = 0
        self.last_shot = 0
        self.rect.center = (self.screen_rect.width // 2, self.screen_rect.height // 2)

    @staticmethod
    def get_upgrade_caps(buildings):
        caps = {
            'rapid_fire': 50,
            'move_speed': 50,
            'projectile_damage': 50,
            'projectile_speed': 50
        }

        for building in buildings:
            if building.level > 0:
                if building.name == "Armurerie":
                    caps['projectile_damage'] = building.level * 5
                elif building.name == "Forge":
                    caps['move_speed'] = building.level * 5
                elif building.name == "Temple":
                    caps['rapid_fire'] = building.level * 5
                elif building.name == "Bibliothèque":
                    caps['projectile_speed'] = building.level * 5
        return caps

    def apply_upgrade_bonuses(self, buildings):
        self.speed = 5
        self.projectile_damage = 1
        self.max_hp = 100
        self.shot_cooldown = 250

        for building in buildings:
            if building.name == "Armurerie":
                self.projectile_damage += building.level * 0.5
            elif building.name == "Forge":
                self.speed += building.level * 0.5
            elif building.name == "Temple":
                self.max_hp += building.level * 5
                self.hp = self.max_hp
            elif building.name == "Marché":
                pass
            elif building.name == "Bibliothèque":
                pass

        self.projectile_damage = max(1, self.projectile_damage)