import pygame
from core.settings import *
from states.scenes import Scene
from ui.dialogue import DialogueManager
from core.asset_manager import AssetManager
from core.camera import CameraGroup
from entities.entity import Entity
from entities.walls import Wall

class BackstageScene(Scene):
    def __init__(self, manager):
        super().__init__(manager)
        self.width = 1600
        self.height = 1200
        self.assets = AssetManager()
        
        # Données partagées
        self.player = self.manager.shared_data.get('player')

        # Caméra et Groupes
        self.camera_group = CameraGroup()
        # Fond Blanc Unis (Utilisation d'une surface blanche)
        self.bg_surf = pygame.Surface((self.width, self.height))
        self.bg_surf.fill(WHITE)
        self.camera_group.set_background_surface(self.bg_surf)
        
        self.interactables = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group() 
        self.walls = pygame.sprite.Group() # Dedicated wall group
        self.npcs = pygame.sprite.Group()

        # Ajout du Joueur
        self.camera_group.add(self.player)
        
        # Système de Dialogue
        self.dialogue_mgr = DialogueManager(self.assets.get_font(None, 24))
        
        self._build_room()
        self._setup_npcs()

        self.exit_rect = pygame.Rect(self.width // 2 - 100, self.height - 100, 200, 80)
        self.unlocked_missions = self.manager.shared_data.get("unlocked_missions", [])

    def on_enter(self, **kwargs):
        self.player.rect.center = (self.width // 2, self.height - 200)
        self.player.hp = self.player.max_hp # Heal in Backstage
        if self.player not in self.camera_group:
            self.camera_group.add(self.player)

    def _build_room(self):
        # Couleurs
        wall_c = (200, 200, 200) # Gris clair pour les murs
        
        # 1. Enceinte extérieure
        # Haut
        self._add_wall((0, 0), (self.width, 50), wall_c)
        # Bas (avec trou pour sortie)
        self._add_wall((0, self.height-50), (self.width//2 - 100, 50), wall_c)
        self._add_wall((self.width//2 + 100, self.height-50), (self.width//2 - 100, 50), wall_c)
        # Gauche
        self._add_wall((0, 0), (50, self.height), wall_c)
        # Droite
        self._add_wall((self.width-50, 0), (50, self.height), wall_c)

        # 2. Salle Centrale (Hub)
        # Pas de murs au milieu, c'est ouvert

        # 3. Salle Gauche (Sécurité) - Accès par l'est de la salle
        # Mur vertical séparateur à x=500
        # self._add_wall((500, 0), (50, 600), wall_c) 
        # On fait une structure en "Trèfle"
        
        # Mur Horizontal séparation HAUT
        self._add_wall((0, 400), (600, 50), wall_c) # Coin Haut Gauche fermé
        self._add_wall((1000, 400), (600, 50), wall_c) # Coin Haut Droit fermé
        
        # Mur Vertical séparation CENTRE
        self._add_wall((600, 0), (50, 300), wall_c)
        self._add_wall((950, 0), (50, 300), wall_c)

    def _add_wall(self, pos, size, color):
        w = Wall([self.camera_group, self.walls], pos, size, color=color, border_color=(150, 150, 150))
        # self.collision_sprites.add(w) # Walls are handled separately usually, but lets add to collision sprites logic if generic
        pass

    def _setup_npcs(self):
        npc_img = self.assets.get_image("punk_npc.png")
        self.npc_configs = {
            "Le Manager": {
                "pos": (self.width//2, 200), # Salle Haut Centre
                "nodes": {
                    "start": {
                        "text": "Enfin là ! Les types de 'The Glitch' essaient de hacker notre système.",
                        "options": [("On fait quoi ?", "plan"), ("Qui sont-ils ?", "lore"), ("Je reviendrai.", "end")]
                    },
                    "plan": {
                        "text": "Il faut détruire leur serveur central dans la zone industrielle. Tu relèves le défi ?",
                        "options": [("J'y vais. [Mission Sabotage]", "unlock_sabotage"), ("Pas maintenant.", "end")]
                    },
                    "lore": {
                        "text": "Des anciens DJ qui ont mal tourné. Ils veulent le silence radio.",
                        "options": [("Je vois...", "start")]
                    }
                }
            },
            "La Chanteuse": {
                "pos": (300, 200), # Salle Haut Gauche
                "nodes": {
                    "start": {
                        "text": "Mon micro est hanté par un virus synthétique... Tu peux m'aider ?",
                        "options": [("Comment ?", "how"), ("Désolé, je suis occupé.", "end")]
                    },
                    "how": {
                        "text": "Il faut trouver le décodeur dans la Zone 2 et me protéger pendant que je l'installe.",
                        "options": [("C'est d'accord. [Mission Défense]", "unlock_defense"), ("Un autre jour.", "end")]
                    }
                }
            },
            "Le Roadie": {
                "pos": (1300, 200), # Salle Haut Droite
                "nodes": {
                    "start": {
                        "text": "Pfff... encore un câble qui lâche. T'as pas un tournevis sonique ?",
                        "options": [("Où j'en trouve un ?", "where"), ("Bon courage.", "end")]
                    },
                    "where": {
                        "text": "Les gardes de la Zone 3 en ont. Récupère s'en un et je te paierai bien.",
                        "options": [("Je vais voir ça. [Mission Récupération]", "unlock_fetch"), ("Occupe-toi de tes câbles.", "end")]
                    }
                }
            }
        }
        
        self.lore_npcs = []
        for name, config in self.npc_configs.items():
            npc = Entity([self.camera_group, self.interactables, self.npcs], image=npc_img, pos=config["pos"], scale=(50, 80))
            self.lore_npcs.append({"sprite": npc, "name": name, "config": config})

    def update(self):
        self.camera_group.update()
        if self.dialogue_mgr.active: return

        # Mouvements
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        speed = 8 
        if keys[pygame.K_z] or keys[pygame.K_UP]: dy -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += speed
        if keys[pygame.K_q] or keys[pygame.K_LEFT]: dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += speed
        
        if dx != 0 and dy != 0: dx, dy = dx*0.707, dy*0.707

        # Collisions Generiques (avec self.collision_sprites si utilisé, ou self.walls)
        # X
        self.player.rect.x += dx
        for w in self.walls:
             if self.player.rect.colliderect(w.rect):
                 if dx > 0: self.player.rect.right = w.rect.left
                 if dx < 0: self.player.rect.left = w.rect.right
        
        # Y
        self.player.rect.y += dy
        for w in self.walls:
             if self.player.rect.colliderect(w.rect):
                 if dy > 0: self.player.rect.bottom = w.rect.top
                 if dy < 0: self.player.rect.top = w.rect.bottom
        
        self.player.rect.clamp_ip(pygame.Rect(0, 0, self.width, self.height))

    def handle_input(self, events):
        if self.dialogue_mgr.active:
            for event in events:
                self.dialogue_mgr.handle_input(event)
            return

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    # Vérifier interactions
                    if self._check_npc_interactions(): return
                    
                    if self.player.rect.colliderect(self.exit_rect):
                        # Retour au Hub
                        self.manager.switch_to("hub", spawn_pos=(MAP_WIDTH//2, MAP_HEIGHT//2 - 400))
                
                elif event.key == pygame.K_ESCAPE:
                    pass

    def _check_npc_interactions(self):
        for npc in self.lore_npcs:
            if self.player.rect.colliderect(npc["sprite"].rect.inflate(80, 80)):
                config = npc["config"]
                self._start_node_dialogue(npc["name"], config, "start")
                return True
        return False

    def _start_node_dialogue(self, name, config, node_id):
        node = config["nodes"][node_id]
        
        # Callback pour gérer la navigation dans l'arbre
        def callback(action_id):
            if action_id == "end":
                self.dialogue_mgr.active = False
            elif action_id.startswith("unlock_"):
                 self._unlock_mission(action_id)
                 self.dialogue_mgr.active = False
            else:
                 self._start_node_dialogue(name, config, action_id)

        self.dialogue_mgr.start_dialogue(name, node["text"], node["options"], callback)

    def _unlock_mission(self, unlock_id):
        mapping = {
             "unlock_sabotage": "Mission Sabotage",
             "unlock_defense": "Mission Protection",
             "unlock_fetch": "Mission Recup"
        }
        m_name = mapping.get(unlock_id)
        if m_name and m_name not in self.unlocked_missions:
            self.unlocked_missions.append(m_name)
            self.manager.shared_data["unlocked_missions"] = self.unlocked_missions
            print(f"Mission unlocked: {m_name}")

    def draw(self, screen):
        self.camera_group.custom_draw(self.player)
        
        # Prompts
        if not self.dialogue_mgr.active:
            font = self.dialogue_mgr.font
            for npc in self.lore_npcs:
                if self.player.rect.colliderect(npc["sprite"].rect.inflate(80, 80)):
                     self._draw_prompt(screen, f"[E] Parler à {npc['name']}", font)
            if self.player.rect.colliderect(self.exit_rect):
                 self._draw_prompt(screen, "[E] Sortir", font)

        self.dialogue_mgr.draw(screen)

    def _draw_prompt(self, screen, text, font, color=NEON_GREEN):
        txt = font.render(text, True, color)
        surf_rect = txt.get_rect(center=(WIDTH//2, HEIGHT - 150))
        pygame.draw.rect(screen, (0, 0, 0, 180), surf_rect.inflate(20, 10))
        screen.blit(txt, surf_rect)
