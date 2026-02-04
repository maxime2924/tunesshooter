import pygame
from player import Player
from asset_manager import AssetManager

class Moto(Player):
    def __init__(self, screen_rect):
        super().__init__(screen_rect)
        assets = AssetManager()
        
        # Utilisation du nouveau sprite Daft Punk RÉALISTE
        original_image = assets.get_image('player_realistic_gold.png')
        if not original_image: # Fallback au cas ou
             original_image = assets.get_image('player_daft.png')
        
        # SUPPRESSION DE LA ZONE GRISE (Background removal hack)
        # Si l'image a un fond plein, on prend la couleur du pixel (0,0) comme colorkey
        image_to_process = original_image.copy()
        bg_color = image_to_process.get_at((0, 0))
        if bg_color.a > 0: # Si ce n'est pas déjà transparent
            image_to_process.set_colorkey(bg_color)
             
        self.image = pygame.transform.scale(image_to_process, (60, 60)) 
        
        # Mettre à jour le rect pour la nouvelle image
        self.rect = self.image.get_rect(center=self.rect.center)
