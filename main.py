import pygame
import random

pygame.init()

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tune Shooter")
clock = pygame.time.Clock()

# --- Couleurs ---
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

from player import Player
from enemy import Enemy
from entity import separate_sprites

from projectile import Projectile
from gold import Gold
from ranged_enemy import RangedEnemy
from moto import Moto
from menu import MainMenu
from base import BaseZone

# --- Création ---
screen_rect = screen.get_rect()
player = Moto(screen_rect)
# Système de difficulté progressive (doit être avant spawn_enemy)
difficulty_multiplier = 1.0  # augmente avec chaque extraction
extractions_count = 0

def spawn_enemy():
    global difficulty_multiplier
    # Calcul de la difficulté basée sur le niveau du joueur ET la difficulté générale
    player_level_multiplier = max(1.0, player.level * 0.2)  # +20% par niveau
    total_multiplier = difficulty_multiplier * player_level_multiplier
    
    base_hp = max(3, int(3 * total_multiplier))
    base_damage = max(1, int(1 * total_multiplier))
    
    # Spawner RangedEnemy à partir du niveau 3 du joueur
    if player.level >= 3 and random.random() < 0.4:  # 40% chance à partir du niveau 3
        ranged_hp = max(2, int(2 * total_multiplier))
        return RangedEnemy(screen_rect, hp=ranged_hp, damage=base_damage)
    else:
        return Enemy(screen_rect, hp=base_hp, damage=base_damage)

enemies = pygame.sprite.Group([spawn_enemy() for _ in range(5)])
# Spawn continu d'ennemis
ENEMY_SPAWN_INTERVAL_MS = 2000  # spawn un ennemi tous les 2 secondes
MAX_ENEMIES = 10                 # max d'ennemis simultanés
last_enemy_spawn = pygame.time.get_ticks()
EXTRACT_SIZE = 80
EXTRACT_DELAY_MS = 5000      # délai entre apparitions (ms)
EXTRACT_DURATION_MS = 5000   # durée active (ms)
extraction_rect = pygame.Rect(0, 0, EXTRACT_SIZE, EXTRACT_SIZE)
extraction_active = False
extraction_next_spawn = pygame.time.get_ticks() + EXTRACT_DELAY_MS
extraction_end_time = 0
projectiles = pygame.sprite.Group()
golds = pygame.sprite.Group()
banked_gold = 0
banked_xp = 0
enemy_projectiles = pygame.sprite.Group()  # Projectiles tirés par les ennemis
gold_multiplier = 1.0  # Multiplicateur d'or selon le Marché
xp_multiplier = 1.0    # Multiplicateur d'XP selon la Bibliothèque

# --- Menus principaux ---
main_menu = MainMenu(WIDTH, HEIGHT)
base_zone = BaseZone(WIDTH, HEIGHT, player)

# État du jeu
game_state = "main_menu"  # main_menu, base, game, settings

# Boucle des menus
while game_state != "quit" and game_state != "game":
    clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if game_state == "main_menu":
                action = main_menu.handle_click(event.pos)
                if action == "play":
                    game_state = "base"
                elif action == "quit":
                    pygame.quit()
                    raise SystemExit
            elif game_state == "base":
                action = base_zone.handle_click(event.pos)
                if action == "launch":
                    # Appliquer les bonus des bâtiments avant de lancer la mission
                    player.apply_upgrade_bonuses(base_zone.buildings)
                    
                    # Mettre à jour les multiplicateurs selon les bâtiments
                    gold_multiplier = 1.0
                    xp_multiplier = 1.0
                    for building in base_zone.buildings:
                        if building.name == "Marché" and building.level > 0:
                            gold_multiplier += building.level * 0.1  # +10% d'or par niveau
                        elif building.name == "Bibliothèque" and building.level > 0:
                            xp_multiplier += building.level * 0.1  # +10% d'XP par niveau
                    
                    # Réinitialiser les sprites et les groupes pour la nouvelle mission
                    enemies.empty()
                    projectiles.empty()
                    enemy_projectiles.empty()
                    golds.empty()
                    enemies.add([spawn_enemy() for _ in range(5)])
                    extraction_active = False
                    extraction_next_spawn = pygame.time.get_ticks() + EXTRACT_DELAY_MS
                    game_state = "game"
                elif action == "menu":
                    game_state = "main_menu"
                elif isinstance(action, tuple) and action[0] == "building":
                    building = action[1]
                    cost = base_zone.upgrade_building(building, banked_gold)
                    if cost > 0:
                        banked_gold -= cost
    
    # Mettre à jour la base zone (déplacement)
    if game_state == "base":
        base_zone.update()
    
    if game_state == "main_menu":
        main_menu.draw(screen)
    elif game_state == "base":
        base_zone.draw(screen)
    
    pygame.display.flip()

# --- Boucle principale ---
running = True
while running:
    clock.tick(FPS)
    now = pygame.time.get_ticks()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        # Tir: espace ou clic gauche
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            proj = player.shoot(pygame.mouse.get_pos(), now)
            if proj:
                projectiles.add(proj)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            proj = player.shoot(event.pos, now)
            if proj:
                projectiles.add(proj)
    
    # Mise à jour
    player.update()
    enemies.update(player)
    projectiles.update()
    enemy_projectiles.update()
    
    # Les ennemis à distance tirent
    for enemy in enemies:
        if isinstance(enemy, RangedEnemy):
            proj = enemy.shoot(player, now)
            if proj:
                enemy_projectiles.add(proj)
    
    # Détection des collisions (hitbox)
    # Vérifier les collisions avant séparation pour appliquer les dégâts
    hits = pygame.sprite.spritecollide(player, enemies, False)
    if hits:
        damage_taken = sum(getattr(e, 'damage', 1) for e in hits)
        player.hp -= damage_taken
        print(f"HP: {player.hp}")
        if player.hp <= 0:
            # Bank XP on death (no gold)
            banked_xp += getattr(player, 'xp', 0)
            print("Game Over!")
            print(f"Banked XP total: {banked_xp}")
            running = False
    
    # Collisions avec les projectiles ennemis
    enemy_proj_hits = pygame.sprite.spritecollide(player, enemy_projectiles, True)
    if enemy_proj_hits:
        damage_taken = sum(getattr(p, 'damage', 1) for p in enemy_proj_hits)
        player.hp -= damage_taken
        print(f"Hit by enemy projectile! HP: {player.hp}")

    # Résolution des collisions entre ennemis (ne doivent pas se chevaucher)
    enemy_list = list(enemies)
    for i in range(len(enemy_list)):
        for j in range(i + 1, len(enemy_list)):
            separate_sprites(enemy_list[i], enemy_list[j], push_a=True, push_b=True)

    # Empêcher les ennemis d'entrer dans le joueur: on pousse seulement l'ennemi
    for enemy in enemies:
        separate_sprites(player, enemy, push_a=False, push_b=True)

    # Projectiles qui touchent des ennemis
    proj_hits = pygame.sprite.groupcollide(projectiles, enemies, True, False)
    if proj_hits:
        for proj, hit_enemies in proj_hits.items():
            for enemy in hit_enemies:
                dmg = getattr(proj, 'damage', 1)
                died = enemy.take_damage(dmg)
                if died:
                    # spawn gold, remove enemy (no automatic respawn on kill)
                    xp_reward = int(10 * difficulty_multiplier * xp_multiplier)
                    gold_value = int(5 * difficulty_multiplier * gold_multiplier)
                    g = Gold(enemy.rect.center, value=gold_value)
                    golds.add(g)
                    enemy.kill()
                    # award XP to player for the kill
                    if hasattr(player, 'add_xp'):
                        player.add_xp(xp_reward)

    # Player collecte l'or
    collected = pygame.sprite.spritecollide(player, golds, True)
    if collected:
        for g in collected:
            player.gold += int(g.value * gold_multiplier)
        print(f"Gold: {player.gold}")

    # Spawn continu des ennemis (indépendant des kills)
    if now - last_enemy_spawn >= ENEMY_SPAWN_INTERVAL_MS and len(enemies) < MAX_ENEMIES:
        enemies.add(spawn_enemy())
        last_enemy_spawn = now

    # Gestion temporaire de la zone d'extraction (apparitions périodiques)
    if not extraction_active and now >= extraction_next_spawn:
        extraction_active = True
        # Place the extraction zone at a random location within the screen bounds (with margin)
        margin = 10
        x = random.randint(margin, screen_rect.width - EXTRACT_SIZE - margin)
        y = random.randint(margin, screen_rect.height - EXTRACT_SIZE - margin)
        extraction_rect.topleft = (x, y)
        extraction_end_time = now + EXTRACT_DURATION_MS
    if extraction_active and now >= extraction_end_time:
        extraction_active = False
        extraction_next_spawn = now + EXTRACT_DELAY_MS

    # Extraction: si la zone est active et le joueur y entre, fin de la partie
    if extraction_active and player.rect.colliderect(extraction_rect):
        # Bank the gold and XP on successful extraction
        banked_gold += player.gold
        # bank XP as well
        banked_xp += getattr(player, 'xp', 0)
        player.gold = 0
        player.xp = 0
        # Heal player fully on extraction
        if hasattr(player, 'heal_full'):
            player.heal_full()
        # Increase difficulty
        extractions_count += 1
        difficulty_multiplier = 1.0 + (extractions_count * 0.25)  # +25% per extraction
        print(f"Extraction reached. Banked gold total: {banked_gold}, Banked XP total: {banked_xp}")
        print(f"Difficulty increased to {difficulty_multiplier:.2f}x")
        
        # Retour au village pour les améliorations
        running = False
        # Réinitialiser le joueur pour la prochaine mission, mais garder le niveau et XP banké
        player_level_backup = player.level
        player.reset()
        player.level = player_level_backup
        # Réinitialiser aussi le statut du joueur
    
    # Affichage
    screen.fill(BLACK)
    screen.blit(player.image, player.rect)
    enemies.draw(screen)
    # Dessiner les barres de vie des ennemis
    for enemy in enemies:
        hp_ratio = max(0, enemy.hp / 3) if enemy.hp <= 3 else enemy.hp / max(enemy.hp, 1)
        bar_width = 25
        bar_height = 3
        bar_x = enemy.rect.centerx - bar_width // 2
        bar_y = enemy.rect.top - 8
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
    projectiles.draw(screen)
    enemy_projectiles.draw(screen)
    golds.draw(screen)
    # Dessiner la zone d'extraction si active
    if extraction_active:
        pygame.draw.rect(screen, BLUE, extraction_rect)
        pygame.draw.rect(screen, (255,255,255), extraction_rect, 2)
    
    # Affichage des barres de HP et XP (en bas au centre)
    bar_width = 300
    bar_height = 20
    bar_x = WIDTH // 2 - bar_width // 2
    bar_y_hp = HEIGHT - 80
    bar_y_xp = HEIGHT - 40
    
    # Barre de HP
    hp_ratio = max(0, player.hp / player.max_hp)
    pygame.draw.rect(screen, RED, (bar_x, bar_y_hp, bar_width, bar_height))
    pygame.draw.rect(screen, GREEN, (bar_x, bar_y_hp, int(bar_width * hp_ratio), bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y_hp, bar_width, bar_height), 2)
    hp_text = pygame.font.SysFont(None, 16).render(f"HP: {player.hp}/{player.max_hp}", True, (255, 255, 255))
    screen.blit(hp_text, (bar_x + 5, bar_y_hp + 2))
    
    # Barre d'XP
    xp_for_next_level = player.level * 100
    xp_ratio = min(1, player.xp / xp_for_next_level) if xp_for_next_level > 0 else 0
    pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y_xp, bar_width, bar_height))
    pygame.draw.rect(screen, (200, 200, 255), (bar_x, bar_y_xp, int(bar_width * xp_ratio), bar_height))
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y_xp, bar_width, bar_height), 2)
    xp_text = pygame.font.SysFont(None, 16).render(f"XP: {player.xp}/{xp_for_next_level} (Lvl {player.level})", True, (255, 255, 255))
    screen.blit(xp_text, (bar_x + 5, bar_y_xp + 2))
    
    pygame.display.flip()

pygame.quit()