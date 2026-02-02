import pygame
import os
import math
import struct
import wave
import random

# Création du dossier assets s'il n'existe pas
if not os.path.exists("assets"):
    os.makedirs("assets")

pygame.init()


def create_player_img():
    # Un casque de robot stylisé (Daft Punk style)
    surf = pygame.Surface((64, 64), pygame.SRCALPHA)
    # Le casque (Gris argenté)
    pygame.draw.rect(surf, (192, 192, 192), (10, 10, 44, 50), border_radius=10)
    # La visière (Noire/Or)
    pygame.draw.rect(surf, (20, 20, 20), (12, 20, 40, 25), border_radius=5)
    # Reflet sur la visière (Cyan néon)
    pygame.draw.rect(surf, (0, 255, 255), (15, 22, 34, 5), border_radius=2)
    # Sauvegarde
    pygame.image.save(surf, "assets/player.png")
    print("✅ player.png créé")


def create_enemy_img():
    # Un "Glitch" rouge et noir
    surf = pygame.Surface((50, 50), pygame.SRCALPHA)
    # Fond rouge semi-transparent
    surf.fill((255, 0, 0, 100))
    # Dessin aléatoire de pixels pour faire "buggé"
    for _ in range(20):
        w = random.randint(5, 40)
        h = random.randint(2, 10)
        x = random.randint(0, 50 - w)
        y = random.randint(0, 50 - h)
        color = (random.randint(100, 255), 0, 0)
        pygame.draw.rect(surf, color, (x, y, w, h))
    pygame.image.save(surf, "assets/enemy.png")
    print("✅ enemy.png créé")


def create_note_img():
    # Une note de musique Jaune Néon
    surf = pygame.Surface((30, 50), pygame.SRCALPHA)
    # La tige
    pygame.draw.rect(surf, (255, 255, 0), (20, 5, 5, 35))
    # La boule
    pygame.draw.circle(surf, (255, 255, 0), (15, 40), 10)
    # Le crochet
    pygame.draw.polygon(surf, (255, 255, 0), [(20, 5), (20, 15), (30, 20), (30, 5)])
    pygame.image.save(surf, "assets/note.png")
    print("✅ note.png créé")


def create_background():
    # "The Grid" - Une grille style TRON
    width, height = 800, 600
    surf = pygame.Surface((width, height))
    surf.fill((10, 10, 20))  # Bleu nuit très sombre

    # Lignes verticales violettes
    for x in range(0, width, 50):
        pygame.draw.line(surf, (50, 0, 100), (x, 0), (x, height), 1)

    # Lignes horizontales violettes
    for y in range(0, height, 50):
        pygame.draw.line(surf, (50, 0, 100), (0, y), (width, y), 1)

    # Une ligne d'horizon brillante
    pygame.draw.line(surf, (0, 255, 255), (0, height - 50), (width, height - 50), 2)

    pygame.image.save(surf, "assets/background.png")
    print("✅ background.png créé")


def create_laser_sound():
    # Génère un son "Pew" mathématiquement
    sample_rate = 44100
    duration = 0.2  # secondes
    n_samples = int(sample_rate * duration)

    with wave.open("assets/laser.wav", 'w') as obj:
        obj.setnchannels(1)  # Mono
        obj.setsampwidth(2)  # 2 bytes par sample
        obj.setframerate(sample_rate)

        for i in range(n_samples):
            # La fréquence descend de 880Hz à 220Hz (effet "Pew")
            frequency = 880 * (1 - (i / n_samples))
            value = int(32767.0 * 0.5 * math.sin(2.0 * math.pi * frequency * (i / sample_rate)))
            data = struct.pack('<h', value)
            obj.writeframesraw(data)

    print("✅ laser.wav créé")


if __name__ == "__main__":
    print("🎨 Génération des assets en cours...")
    create_player_img()
    create_enemy_img()
    create_note_img()
    create_background()
    create_laser_sound()
    print("✨ Tout est prêt ! Lance tune.py maintenant.")
    pygame.quit()