import pygame
import os
from settings import *
from scenes import SceneManager
from menu import MainMenu
from hub_scene import HubScene
from backstage_scene import BackstageScene
from mission_scene import MissionScene
from player import Player
from asset_manager import AssetManager

class Game(SceneManager):
    def __init__(self):
        pygame.init()
        # Fullscreen Support
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Initialisation du SceneManager
        super().__init__(self.screen)
        
        # Données partagées (Joueur global)
        # Note: MAP_WIDTH will be dynamic in MissionScene
        self.shared_data = {
            'player': Player(pygame.Rect(0, 0, 4000, 4000)),  
            'unlocked_missions': ["Extraction Illimitée"],
            'inventory': [],
            'game_started': False
        }
        
        # Enregistrement des scènes
        self.scenes = {
            'menu': MainMenu,
            'hub': HubScene,
            'backstage': BackstageScene,
            'mission': MissionScene
        }
        
        # Démarrage
        self.switch_to('menu')
        self._start_music()

    def _start_music(self):
        assets = AssetManager()
        music_file = "Daft Punk - One More Time (Radio Edit) - (320 Kbps) (mp3cut.net).mp3"
        try:
             path = os.path.join(assets.assets_path, music_file)
             if os.path.exists(path):
                 pygame.mixer.music.load(path)
                 pygame.mixer.music.set_volume(0.3)
                 pygame.mixer.music.play(-1) 
        except Exception as e:
            print(f"Erreur musique : {e}")

    def run(self):
        try:
            while self.running:
                self.clock.tick(FPS)
                
                # Gestion globale
                if not self.handle_events():
                    self.running = False
                
                # Update & Draw scène active
                super().run()
                
                pygame.display.flip()
        except Exception as e:
            print(f"CRASH: {e}")
            import traceback
            traceback.print_exc()
        finally:
            pygame.quit()
