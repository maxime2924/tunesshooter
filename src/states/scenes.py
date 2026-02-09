import pygame

class Scene:
    def __init__(self, manager):
        self.manager = manager
        self.next_scene = None

    def handle_input(self, events):
        pass

    def update(self):
        pass

    def draw(self, screen):
        pass

    def on_enter(self, **kwargs):
        pass

    def on_exit(self):
        pass

class SceneManager:
    def __init__(self, screen):
        self.screen = screen
        self.current_scene = None
        self.scenes = {} 
        self.shared_data = {} 

    def switch_to(self, scene_id, **kwargs):
        if scene_id in self.scenes:
            scene_factory = self.scenes[scene_id]
            
            new_scene = None
            if isinstance(scene_factory, type):
                new_scene = scene_factory(self)
            else:
                new_scene = scene_factory 
                new_scene.manager = self

            if self.current_scene:
                self.current_scene.on_exit()
            
            self.current_scene = new_scene
            self.current_scene.on_enter(**kwargs)
        else:
            print(f"Erreur : Scène {scene_id} introuvable.")

    def run(self):
        if self.current_scene:
            self.current_scene.update()
            self.current_scene.draw(self.screen)
            
    def handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                return False
        
        if self.current_scene:
            self.current_scene.handle_input(events)
            
        return True
