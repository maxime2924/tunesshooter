import pygame

class Scene:
    """Classe de base pour toutes les scènes du jeu."""
    def __init__(self, manager):
        self.manager = manager
        self.next_scene = None

    def handle_input(self, events):
        """Gestion des entrées utilisateur."""
        pass

    def update(self):
        """Mise à jour logique."""
        pass

    def draw(self, screen):
        """Rendu à l'écran."""
        pass

    def on_enter(self, **kwargs):
        """Appelé à l'entrée de la scène (passage de données via kwargs)."""
        pass

    def on_exit(self):
        """Appelé à la sortie de la scène."""
        pass

class SceneManager:
    """Gestionnaire des scènes actives."""
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
