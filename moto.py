import pygame
from player import Player
import os

class Moto(Player):
    def __init__(self, screen_rect):
        super().__init__(screen_rect)
        # Charger l'image moto depuis le dossier Image
        image_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Image', 'moto-removebg-preview.png')
        try:
            self.image = pygame.image.load(image_path)
            # Convertir en RGBA pour garantir la transparence
            self.image = self.image.convert_alpha()
            # Redimensionner à 30x30 pour correspondre à la taille des ennemis
            self.image = pygame.transform.scale(self.image, (30, 30))
        except pygame.error as e:
            print(f"Erreur: Impossible de charger {image_path}: {e}")
            # Fallback: créer une image par défaut si le PNG ne charge pas
            self.image = pygame.Surface((60, 40), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (200, 50, 50), (10, 15, 40, 15))
            pygame.draw.circle(self.image, (50, 50, 50), (8, 30), 6)
            pygame.draw.circle(self.image, (50, 50, 50), (52, 30), 6)
        
        # Mettre à jour le rect pour la nouvelle image
        self.rect = self.image.get_rect(center=self.rect.center)
