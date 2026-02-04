import pygame
from core.asset_manager import AssetManager


class Player(pygame.sprite.Sprite):
    def __init__(self, screen_rect):
        super().__init__()
        
        # Load sprite sheet
        import os
        assets = AssetManager()

        sprite_path = os.path.join(assets.assets_path, "Tech Dungeon Roguelite - Asset Pack (DEMO)", "Players", "players blue x2.png")
        
        try:
            self.sprite_sheet = pygame.image.load(sprite_path).convert_alpha()
            # Sheet is 8 columns x 13 rows (from 8x13 Cells.txt)
            # Each cell is approximately sprite_sheet.width / 8
            self.cell_width = self.sprite_sheet.get_width() // 8
            self.cell_height = self.sprite_sheet.get_height() // 13
            
            # Extract idle frame (row 0, col 0)
            self.image = pygame.Surface((self.cell_width, self.cell_height), pygame.SRCALPHA)
            self.image.blit(self.sprite_sheet, (0, 0), (0, 0, self.cell_width, self.cell_height))
            # Scale up 2x for visibility
            self.image = pygame.transform.scale(self.image, (self.cell_width * 2, self.cell_height * 2))
        except Exception as e:
            print(f"Failed to load player sprite: {e}")
            # Fallback
            self.image = pygame.Surface((40, 40))
            self.image.fill((0, 0, 255))
        
        self.rect = self.image.get_rect(center=(screen_rect.width // 2, screen_rect.height // 2))
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        self.screen_rect = screen_rect

        # --- ECONOMIE ---
        self.gold = 10000  # Start with 10k as requested
        self.banked_gold = 500  # Some initial banked gold too
        self.gold_per_second = 0  # Revenu passif
        self.last_passive_income = 0  # Timer pour le revenu

        # Stats de tir
        self.last_shot = 0
        self.shot_cooldown = 150  # ms (Plus rapide)
        self.projectile_speed = 18 # Plus rapide
        self.projectile_damage = 2 # Un peu plus de degats de base

        # XP / leveling
        self.xp = 0
        self.level = 1

        # Suivi des améliorations
        self.upgrade_levels = {
            'rapid_fire': 0,
            'move_speed': 0,
            'projectile_damage': 0,
            'projectile_speed': 0
        }


    def update_passive_income(self, current_time):
        """Génère de l'or automatiquement si on a des équipements."""
        if self.gold_per_second > 0:
            if current_time - self.last_passive_income >= 1000:  # Toutes les 1000ms (1s)
                self.banked_gold += self.gold_per_second
                self.last_passive_income = current_time
                print(f"Revenu passif: +{self.gold_per_second}g (Total Banque: {self.banked_gold})")

    def add_xp(self, amount):
        self.xp += amount
        # Level up basique : 100 * niveau actuel requis
        req_xp = self.level * 100
        while self.xp >= req_xp:
            self.xp -= req_xp
            self.level += 1
            self.max_hp += 10
            self.hp = self.max_hp
            print(f"LEVEL UP! Niveau {self.level}")
            req_xp = self.level * 100

    def update(self):
        """Smooth free movement."""
        keys = pygame.key.get_pressed()
        
        # Movement
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a] or keys[pygame.K_q]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        
        # Keep in bounds
        if self.screen_rect:
            self.rect.clamp_ip(self.screen_rect)

    def shoot(self, target_pos, now):
        """Return a Projectile instance aimed at target_pos or None if on cooldown."""
        if now - self.last_shot < self.shot_cooldown:
            return None
        from entities.projectile import Projectile
        start = pygame.math.Vector2(self.rect.center)
        target = pygame.math.Vector2(target_pos)
        direction = target - start
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        velocity = direction.normalize() * self.projectile_speed
        self.last_shot = now
        
        # Son
        assets = AssetManager()
        laser = assets.get_sound("laser.wav")
        if laser:
            laser.set_volume(0.4)
            laser.play()
            
        return Projectile(self.rect.center, velocity, self.screen_rect, damage=self.projectile_damage)

    def heal_full(self):
        self.hp = self.max_hp

    def reset(self):
        """Réinitialise le joueur pour une nouvelle partie."""
        self.hp = self.max_hp
        self.gold = 0
        self.last_shot = 0
        # On ne reset plus les stats pour garder les upgrades du shop.
        self.rect.center = (self.screen_rect.width // 2, self.screen_rect.height // 2)

    @staticmethod
    def get_upgrade_caps(buildings):
        """
        Retourne les caps d'améliorations basés sur les niveaux des bâtiments.
        (Méthode statique car elle n'utilise pas 'self')
        """
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
        """Applique les bonus permanents des bâtiments au joueur."""
        # Reset stats de base
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