import pygame
import math
import random
from pathlib import Path

# Garde tes configurations précédentes (WIDTH, HEIGHT, ASSETS_DIR)
WIDTH, HEIGHT = 800, 600
ASSETS_DIR = Path(__file__).parent / "assets"


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # ... (Garde ton code d'image et chargement ici) ...
        self.image = pygame.Surface((40, 40))  # Placeholder si pas d'image
        self.image.fill((0, 255, 255))
        self.original_image = self.image

        self.rect = self.image.get_rect(center=(x, y))
        self.hitbox = self.rect.inflate(-10, -10)

        # STATS MODIFIABLES (Améliorations)
        self.base_speed = 5
        self.speed = self.base_speed
        self.damage = 1

        # INVENTAIRE
        self.gold_bank = 0  # Or sécurisé (dans la base)
        self.current_loot = 0  # Or de la mission actuelle (à risque)
        self.hp = 3

    def update(self):
        # ... (Garde ton code de déplacement ZQSD et visée souris ici) ...
        # (Copie le code de déplacement de l'étape précédente)
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_q]: dx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx = self.speed
        if keys[pygame.K_UP] or keys[pygame.K_z]:    dy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:  dy = self.speed

        self.rect.x += dx
        self.rect.y += dy
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))

        # Rotation (Code souris de l'étape précédente)
        mouse_x, mouse_y = pygame.mouse.get_pos()
        rel_x, rel_y = mouse_x - self.rect.centerx, mouse_y - self.rect.centery
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) - 90
        self.image = pygame.transform.rotate(self.original_image, int(angle))
        self.rect = self.image.get_rect(center=self.rect.center)


class ExtractionZone(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((100, 100))
        # Zone verte semi-transparente pour dire "C'est la sortie !"
        self.image.fill((0, 255, 0))
        self.image.set_alpha(150)
        self.rect = self.image.get_rect()
        # Apparaît aléatoirement sur un bord
        self.rect.x = random.choice([0, WIDTH - 100])
        self.rect.y = random.choice([0, HEIGHT - 100])


# ... (Garde tes classes Note, Enemy et Loot comme avant) ...
# Pense juste à ajouter une variable "self.damage" au joueur pour gérer les upgrades
class Note(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, target_x, target_y):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 255, 0))
        self.rect = self.image.get_rect(center=(start_x, start_y))
        angle = math.atan2(target_y - start_y, target_x - start_x)
        self.dx = math.cos(angle) * 12
        self.dy = math.sin(angle) * 12

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        if not (0 <= self.rect.x <= WIDTH and 0 <= self.rect.y <= HEIGHT):
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, target):  # On lui passe la cible (joueur)
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.target = target
        self.speed = 2

    def update(self):
        # Avance vers le joueur
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 0:
            self.rect.x += (dx / dist) * self.speed
            self.rect.y += (dy / dist) * self.speed


class Loot(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((15, 15))
        self.image.fill((255, 215, 0))  # Or
        self.rect = self.image.get_rect(center=(x, y))
        self.value = 10