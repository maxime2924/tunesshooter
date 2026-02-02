import pygame
import random
from pathlib import Path
from sprites import Player, Note, Enemy, Loot, ExtractionZone

# CONFIG
WIDTH, HEIGHT = 800, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (25, 25, 30)
GOLD_COLOR = (255, 215, 0)


def draw_text(screen, text, size, color, x, y):
    font = pygame.font.SysFont("arial", size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(x, y))
    screen.blit(surf, rect)


def spawn_enemy_edge(player):
    # Apparition sur les bords
    enemy = Enemy(player)
    side = random.randint(0, 3)
    if side == 0:
        enemy.rect.midbottom = (random.randint(0, WIDTH), 0)
    elif side == 1:
        enemy.rect.midleft = (WIDTH, random.randint(0, HEIGHT))
    elif side == 2:
        enemy.rect.midtop = (random.randint(0, WIDTH), HEIGHT)
    else:
        enemy.rect.midright = (0, random.randint(0, HEIGHT))
    return enemy


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    # Le joueur est créé UNE SEULE FOIS pour garder son or "Bank"
    player = Player(WIDTH // 2, HEIGHT // 2)

    # Groupes
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    notes = pygame.sprite.Group()
    loots = pygame.sprite.Group()
    extraction_group = pygame.sprite.Group()

    # Timer pour l'apparition de l'extraction
    EXTRACTION_TIME = 10000  # 10 secondes pour tester (mets 30000+ après)
    mission_start_time = 0

    # Etats : "HUB", "RUN", "GAMEOVER"
    game_state = "HUB"

    # Event custom pour spawn ennemis
    SPAWN_ENEMY = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_ENEMY, 800)

    running = True
    while running:
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

            # --- ACTIONS DANS LE HUB (BASE) ---
            if game_state == "HUB":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # LANCER LA MISSION
                        game_state = "RUN"
                        # Reset de la map pour la mission
                        enemies.empty()
                        loots.empty()
                        notes.empty()
                        extraction_group.empty()
                        player.rect.center = (WIDTH // 2, HEIGHT // 2)
                        player.current_loot = 0  # On commence poches vides
                        player.hp = 3
                        mission_start_time = current_time
                        all_sprites = pygame.sprite.Group(player)

                    # ACHAT D'AMÉLIORATION (Exemple: Touche U pour Upgrade vitesse)
                    if event.key == pygame.K_u:
                        cost = 50
                        if player.gold_bank >= cost:
                            player.gold_bank -= cost
                            player.speed += 1
                            print("Vitesse augmentée !")

            # --- ACTIONS EN MISSION ---
            elif game_state == "RUN":
                if event.type == SPAWN_ENEMY:
                    e = spawn_enemy_edge(player)
                    all_sprites.add(e)
                    enemies.add(e)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    n = Note(player.rect.centerx, player.rect.centery, mx, my)
                    all_sprites.add(n)
                    notes.add(n)

        # --- LOGIQUE (UPDATE) ---
        if game_state == "RUN":
            all_sprites.update()

            # Collisions Tir / Ennemi
            hits = pygame.sprite.groupcollide(enemies, notes, True, True)
            for hit in hits:
                loot = Loot(hit.rect.centerx, hit.rect.centery)
                all_sprites.add(loot)
                loots.add(loot)

            # Ramasser Loot
            loot_hits = pygame.sprite.spritecollide(player, loots, True)
            for l in loot_hits:
                player.current_loot += l.value

            # Collision Joueur / Ennemi (Dégâts)
            if pygame.sprite.spritecollide(player, enemies, True):
                player.hp -= 1
                if player.hp <= 0:
                    game_state = "GAMEOVER"  # Mort = tout perdu

            # Apparition de l'extraction après le temps imparti
            if len(extraction_group) == 0 and (current_time - mission_start_time > EXTRACTION_TIME):
                zone = ExtractionZone()
                extraction_group.add(zone)
                all_sprites.add(zone)
                print("L'EXTRACTION EST ARRIVÉE !")

            # Extraction réussie ?
            if pygame.sprite.spritecollide(player, extraction_group, False):
                # SUCCESS ! On sécurise le butin
                player.gold_bank += player.current_loot
                player.current_loot = 0
                game_state = "HUB"  # Retour à la base

        # --- DESSIN (RENDER) ---
        screen.fill(BLACK)

        if game_state == "HUB":
            # Ecran de base
            draw_text(screen, "--- STUDIO DAFT PUNK (BASE) ---", 40, WHITE, WIDTH // 2, 100)
            draw_text(screen, f"OR EN BANQUE : {player.gold_bank}", 30, GOLD_COLOR, WIDTH // 2, 200)
            draw_text(screen, f"Vitesse actuelle : {player.speed}", 20, WHITE, WIDTH // 2, 250)
            draw_text(screen, "[ESPACE] Partir en Live (Mission)", 25, WHITE, WIDTH // 2, 400)
            draw_text(screen, "[U] Améliorer Vitesse (50 Gold)", 25, WHITE, WIDTH // 2, 450)

        elif game_state == "RUN":
            all_sprites.draw(screen)
            # HUD
            draw_text(screen, f"Sac: {player.current_loot} G", 20, GOLD_COLOR, 60, 20)
            draw_text(screen, f"PV: {player.hp}", 20, (255, 50, 50), WIDTH - 50, 20)

            # Info Extraction
            time_left = max(0, EXTRACTION_TIME - (current_time - mission_start_time))
            if time_left > 0:
                draw_text(screen, f"Extraction dans: {time_left // 1000}s", 20, WHITE, WIDTH // 2, 20)
            else:
                draw_text(screen, "TROUVEZ LA ZONE VERTE !", 30, (0, 255, 0), WIDTH // 2, 50)

        elif game_state == "GAMEOVER":
            draw_text(screen, "ECHEC DE LA MISSION", 50, (255, 0, 0), WIDTH // 2, HEIGHT // 2)
            draw_text(screen, "Loot perdu...", 30, WHITE, WIDTH // 2, HEIGHT // 2 + 50)
            draw_text(screen, "Appuie sur ESPACE pour rentrer (honteux)", 20, WHITE, WIDTH // 2, HEIGHT - 100)

            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                player.current_loot = 0  # Perdu !
                game_state = "HUB"

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()