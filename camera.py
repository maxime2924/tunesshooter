import pygame
from settings import *

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.half_width = self.display_surface.get_size()[0] // 2
        self.half_height = self.display_surface.get_size()[1] // 2
        self.offset = pygame.math.Vector2()

        # Background
        self.floor_surf = None
        self.floor_rect = None

    def set_tiled_background(self, image_path, map_width, map_height):
        # Charger l'image de texture
        try:
            from asset_manager import AssetManager
            assets = AssetManager()
            # On essaye de charger par nom si asset manager le permet, sinon path direct
            if "/" in image_path or "\\" in image_path:
                 bg_image = pygame.image.load(image_path).convert()
            else:
                 bg_image = assets.get_image(image_path)
            
            if not bg_image:
                 print(f"Erreur chargement fond {image_path}, utilisation noir.")
                 self.floor_surf = pygame.Surface((map_width, map_height))
                 self.floor_surf.fill((10, 10, 10))
            else:
                self.floor_surf = pygame.Surface((map_width, map_height))
                cols = map_width // bg_image.get_width() + 1
                rows = map_height // bg_image.get_height() + 1
                for col in range(cols):
                    for row in range(rows):
                        self.floor_surf.blit(bg_image, (col * bg_image.get_width(), row * bg_image.get_height()))
            
            self.floor_rect = self.floor_surf.get_rect(topleft=(0, 0))

        except Exception as e:
            print(f"Erreur creation fond tiled: {e}")
            self.floor_surf = pygame.Surface((map_width, map_height))
            self.floor_surf.fill((20, 0, 20)) # Fail safe purple
            self.floor_rect = self.floor_surf.get_rect()

    def custom_draw(self, player):
        # Center camera on player
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height
        
        # Clamp camera to map bounds if needed (optional, keeping limitless for now or clamped usually)
        # Clamping is better for immersion
        if self.floor_rect:
             self.offset.x = max(0, min(self.offset.x, self.floor_rect.width - WIDTH))
             self.offset.y = max(0, min(self.offset.y, self.floor_rect.height - HEIGHT))

        # Draw Floor
        if self.floor_surf:
             floor_offset_pos = self.floor_rect.topleft - self.offset
             self.display_surface.blit(self.floor_surf, floor_offset_pos)

        # Draw Sprites sorted by Y (Bas de l'image = devant)
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.bottom):
            offset_pos = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_pos)
            
            # Debug Rect
            # pygame.draw.rect(self.display_surface, (255, 0, 0), (*offset_pos, sprite.rect.width, sprite.rect.height), 1)
