import pygame

class Player(pygame.sprite.Sprite):
    def __init__(self, screen_rect):
        super().__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill((0, 0, 255))
        self.rect = self.image.get_rect(center=(screen_rect.width // 2, screen_rect.height // 2))
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        self.gold = 0
        self.screen_rect = screen_rect
        # Shooting / upgradeable stats
        self.last_shot = 0
        self.shot_cooldown = 250  # ms
        self.projectile_speed = 10
        self.projectile_damage = 1
        # XP / leveling
        self.xp = 0
        self.level = 1
        # Upgrade tracking
        self.upgrade_levels = {
            'rapid_fire': 0,
            'move_speed': 0,
            'projectile_damage': 0,
            'projectile_speed': 0
        }

    def add_xp(self, amount: int):
        self.xp += amount
        # simple level-up: every 100 XP => level up
        while self.xp >= self.level * 100:
            self.xp -= self.level * 100
            self.level += 1
            # optional: reward on level up
            self.max_hp += 10
            self.hp = self.max_hp
    
    def update(self):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        
        if dx or dy:
            move = pygame.math.Vector2(dx, dy).normalize() * self.speed
            self.rect.x += move.x
            self.rect.y += move.y
        
        if self.screen_rect:
            self.rect.clamp_ip(self.screen_rect)

    def shoot(self, target_pos, now):
        """Return a Projectile instance aimed at target_pos or None if on cooldown."""
        if now - self.last_shot < self.shot_cooldown:
            return None
        from projectile import Projectile
        start = pygame.math.Vector2(self.rect.center)
        target = pygame.math.Vector2(target_pos)
        direction = target - start
        if direction.length() == 0:
            direction = pygame.math.Vector2(1, 0)
        velocity = direction.normalize() * self.projectile_speed
        self.last_shot = now
        return Projectile(self.rect.center, velocity, self.screen_rect, damage=self.projectile_damage)

    def heal_full(self):
        self.hp = self.max_hp

    def reset(self):
        """Réinitialise le joueur pour une nouvelle partie."""
        self.hp = self.max_hp
        self.gold = 0
        self.xp = 0
        # level is kept from previous run (stocké ailleurs si besoin)
        self.speed = 5
        self.last_shot = 0
        self.shot_cooldown = 250
        self.projectile_speed = 10
        self.projectile_damage = 1
        self.upgrade_levels = {
            'rapid_fire': 0,
            'move_speed': 0,
            'projectile_damage': 0,
            'projectile_speed': 0
        }
        self.rect.center = (self.screen_rect.width // 2, self.screen_rect.height // 2)

    def get_upgrade_caps(self, buildings):
        """
        Retourne les caps d'améliorations basés sur les niveaux des bâtiments.
        buildings: liste des objets Building
        """
        caps = {
            'rapid_fire': 50,           # Cap par défaut (pas de bâtiment ou niveau 0)
            'move_speed': 50,
            'projectile_damage': 50,
            'projectile_speed': 50
        }
        
        # Mapping bâtiments -> upgrades (cap = niveau * 5, seulement si niveau > 0)
        for building in buildings:
            if building.level > 0:  # Seulement si le bâtiment a été amélioré
                if building.name == "Armurerie":  # Weapon damage
                    caps['projectile_damage'] = building.level * 5
                elif building.name == "Forge":  # Speed
                    caps['move_speed'] = building.level * 5
                elif building.name == "Temple":  # HP and defense (rapid_fire)
                    caps['rapid_fire'] = building.level * 5
                elif building.name == "Bibliothèque":  # XP related (projectile_speed)
                    caps['projectile_speed'] = building.level * 5
        
        return caps
    
    def apply_upgrade_bonuses(self, buildings):
        """Applique les bonus permanents des bâtiments au joueur."""
        # Réinitialiser aux valeurs de base
        self.speed = 5
        self.projectile_damage = 1
        self.max_hp = 100
        self.shot_cooldown = 250
        
        for building in buildings:
            if building.name == "Armurerie":
                # Bonus de dégâts: +0.5 par niveau
                self.projectile_damage += building.level * 0.5
            elif building.name == "Forge":
                # Bonus de vitesse: +0.5 par niveau
                self.speed += building.level * 0.5
            elif building.name == "Temple":
                # Bonus de HP max: +5 par niveau
                self.max_hp += building.level * 5
                self.hp = self.max_hp  # Restaurer la vie au max
            elif building.name == "Marché":
                # Bonus d'or (appliqué à la récolte dans main.py)
                pass
            elif building.name == "Bibliothèque":
                # Bonus d'XP (appliqué à la récolte dans main.py)
                pass
        
        # Assurer que projectile_damage est au moins 1
        self.projectile_damage = max(1, self.projectile_damage)
