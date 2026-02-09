import pygame
import os

class AssetManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AssetManager, cls).__new__(cls)
            cls._instance.images = {}
            cls._instance.sounds = {}
            cls._instance.fonts = {}
            cls._instance.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cls._instance.assets_path = os.path.join(cls._instance.base_path, 'assets')
        return cls._instance

    def get_image(self, name):
        if name not in self.images:
            path = os.path.join(self.assets_path, name)
            try:
                img = pygame.image.load(path).convert_alpha()
                self.images[name] = img
            except pygame.error as e:
                print(f"Error loading image {name}: {e}")
                surf = pygame.Surface((30, 30))
                surf.fill((255, 0, 255))
                self.images[name] = surf
        return self.images[name]

    def get_sound(self, name):
        if name not in self.sounds:
            path = os.path.join(self.assets_path, name)
            try:
                snd = pygame.mixer.Sound(path)
                self.sounds[name] = snd
            except pygame.error as e:
                print(f"Error loading sound {name}: {e}")
                self.sounds[name] = None
        return self.sounds[name]

    def get_font(self, name=None, size=24):
        key = (name, size)
        if key not in self.fonts:
            try:
                if name:
                    path = os.path.join(self.assets_path, name)
                    if os.path.exists(path):
                        font = pygame.font.Font(path, size)
                    else:
                        font = pygame.font.SysFont(name, size)
                else:
                    font = pygame.font.SysFont(None, size)
                self.fonts[key] = font
            except pygame.error as e:
                print(f"Error loading font {name}: {e}")
                self.fonts[key] = pygame.font.SysFont(None, size)
        return self.fonts[key]
