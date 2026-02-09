import pygame
import os
from core.settings import *
from states.scenes import SceneManager
from states.menu import MainMenu
from states.hub_scene import HubScene
from states.backstage_scene import BackstageScene
from states.mission import MissionScene
from states.pause_menu import PauseMenu
from entities.player import Player
from core.asset_manager import AssetManager

class Game(SceneManager):
    def __init__(self):
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        pygame.init()
        info = pygame.display.Info()
        self.screen_width = info.current_w
        self.screen_height = info.current_h
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        
        super().__init__(self.screen)
        
        self.shared_data = {
            'player': Player(pygame.Rect(0, 0, 4000, 4000)),  
            'unlocked_missions': ["Extraction Illimitée", "Promenade Zen"],
            'inventory': [],
            'game_started': False
        }
        
        self.scenes = {
            'menu': MainMenu,
            'hub': HubScene,
            'backstage': BackstageScene,
            'mission': MissionScene,
            'pause': PauseMenu(self)
        }
        
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
                
                if not self.handle_events():
                    self.running = False
                
                super().run()
                
                pygame.display.flip()
        except Exception as e:
            print(f"CRASH: {e}")
            import traceback
            traceback.print_exc()
        finally:
            pygame.quit()
            import sys
            sys.exit()
