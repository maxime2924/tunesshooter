import pygame
from settings import *
from asset_manager import AssetManager
from camera import CameraGroup
from entity import Entity, AnimatedEntity
import math

class BackstageZone:
    def __init__(self, width, height, player):
        self.width = width
        self.height = height
        self.player = player
        self.assets = AssetManager()
        
        # Camera & Groups
        self.camera_group = CameraGroup()
        self.interactables = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group() 
        self.npcs = pygame.sprite.Group()

        # FOND : Intérieur Loge (on utilise une texture sombre ou tech)
        # Pour l'instant on réutilise grass ou une couleur unie si on n'a pas backstage.png
        self.camera_group.set_tiled_background("concert_floor.png", width, height)
        
        # Position de spawn (Entrée de la loge)
        self.player.kill() 
        self.player.rect.center = (width // 2, height - 200)
        self.camera_group.add(self.player)
        
        # DÉCOR INTÉRIEUR (Murs pour faire une pièce)
        self._build_room()

        # NPCs de la Loge
        self.lore_npcs = []
        self._setup_npcs()

        # UI State
        self.font = pygame.font.SysFont("arial", 24)
        self.dialogue_tree = None # { "npc_name": ..., "current_node": ... }
        self.unlocked_missions = [] # Sera mis à jour par les dialogues

    def _build_room(self):
        # Murs pour faire une pièce
        # On va mettre des tapis rouges et des lumières
        self.props = []
        # Tapis central (simulé par un rect dessiné dans custom_draw ? Non, on ajoute des sprites)
        # On va juste garder les collision_sprites pour l'instant.

        # Sortie (Zone pour retourner au Hub)
        self.exit_rect = pygame.Rect(self.width // 2 - 150, self.height - 120, 300, 100)

    def _setup_npcs(self):
        npc_img = self.assets.get_image("punk_npc.png")
        # 1. Le Manager (Business & Sabotage)
        self.npc_configs = {
            "Le Manager": {
                "pos": (400, 400),
                "nodes": {
                    "start": {
                        "text": "Enfin là ! Les types de 'The Glitch' essaient de hacker notre système.",
                        "options": [
                            ("On fait quoi ?", "plan"),
                            ("Qui sont-ils ?", "lore"),
                            ("Je reviendrai.", "end")
                        ]
                    },
                    "plan": {
                        "text": "Il faut détruire leur serveur central dans la zone industrielle. Tu relèves le défi ?",
                        "options": [
                            ("J'y vais. [Mission Sabotage]", "unlock_sabotage"),
                            ("Pas maintenant.", "end")
                        ]
                    },
                    "lore": {
                        "text": "Des anciens DJ qui ont mal tourné. Ils veulent le silence radio.",
                        "options": [("Je vois...", "start")]
                    }
                }
            },
            "La Chanteuse": {
                "pos": (self.width - 400, 400),
                "nodes": {
                    "start": {
                        "text": "Mon micro est hanté par un virus synthétique... Tu peux m'aider ?",
                        "options": [
                            ("Comment ?", "how"),
                            ("Désolé, je suis occupé.", "end")
                        ]
                    },
                    "how": {
                        "text": "Il faut trouver le décodeur dans la Zone 2 et me protéger pendant que je l'installe.",
                        "options": [
                            ("C'est d'accord. [Mission Défense]", "unlock_defense"),
                            ("Un autre jour.", "end")
                        ]
                    }
                }
            },
            "Le Roadie": {
                "pos": (self.width // 2, 800),
                "nodes": {
                    "start": {
                        "text": "Pfff... encore un câble qui lâche. T'as pas un tournevis sonique ?",
                        "options": [
                            ("Où j'en trouve un ?", "where"),
                            ("Bon courage.", "end")
                        ]
                    },
                    "where": {
                        "text": "Les gardes de la Zone 3 en ont. Récupère s'en un et je te paierai bien.",
                        "options": [
                            ("Je vais voir ça. [Mission Récupération]", "unlock_fetch"),
                            ("Occupe-toi de tes câbles.", "end")
                        ]
                    }
                }
            }
        }

        for name, config in self.npc_configs.items():
            npc = Entity([self.camera_group, self.interactables, self.npcs], image=npc_img, pos=config["pos"], scale=(50, 80))
            self.lore_npcs.append({"sprite": npc, "name": name, "config": config})

    def update(self):
        # Mouvements
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
        
        speed = getattr(self.player, 'speed', 5)
        if dx != 0 or dy != 0:
            norm = (dx**2 + dy**2)**0.5
            dx, dy = (dx/norm) * speed, (dy/norm) * speed
            
        # Collisions
        self.player.rect.x += dx
        for sprite in self.collision_sprites:
            if self.player.rect.colliderect(sprite.rect):
                 if dx > 0: self.player.rect.right = sprite.rect.left
                 if dx < 0: self.player.rect.left = sprite.rect.right
        
        self.player.rect.y += dy
        for sprite in self.collision_sprites:
            if self.player.rect.colliderect(sprite.rect):
                    if dy > 0: self.player.rect.bottom = sprite.rect.top
                    if dy < 0: self.player.rect.top = sprite.rect.bottom
        
        self.player.rect.clamp_ip(pygame.Rect(0, 0, self.width, self.height))
        self.camera_group.update()

    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                # Si déjà en dialogue, on ne fait rien ici (géré par les chiffres)
                if self.dialogue_tree: return

                # Check NPCs
                for npc in self.lore_npcs:
                    if self.player.rect.colliderect(npc["sprite"].rect.inflate(80, 80)):
                        self.dialogue_tree = {
                            "name": npc["name"],
                            "config": npc["config"],
                            "current_node": "start"
                        }
                        return
                
                # Check Exit
                if self.player.rect.colliderect(self.exit_rect):
                    return "exit_backstage"

            # Dialogue Choices
            if self.dialogue_tree:
                node = self.dialogue_tree["config"]["nodes"][self.dialogue_tree["current_node"]]
                if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3]:
                    idx = event.key - pygame.K_1 if event.key < pygame.K_KP1 else event.key - pygame.K_KP1
                    if 0 <= idx < len(node["options"]):
                        choice_text, next_id = node["options"][idx]
                        
                        # Actions Spéciales
                        if next_id == "end":
                            self.dialogue_tree = None
                        elif next_id.startswith("unlock_"):
                             mission_name = next_id.replace("unlock_ sabotage", "Mission Sabotage") # Correction typo si besoin
                             # Mappage propre
                             mapping = {
                                 "unlock_sabotage": "Mission Sabotage",
                                 "unlock_defense": "Mission Protection",
                                 "unlock_fetch": "Mission Recup"
                             }
                             m_name = mapping.get(next_id, "Inconnue")
                             if m_name not in self.unlocked_missions:
                                self.unlocked_missions.append(m_name)
                             self.dialogue_tree = None # End after unlock
                        else:
                            self.dialogue_tree["current_node"] = next_id
                
                elif event.key == pygame.K_ESCAPE:
                    self.dialogue_tree = None

        return None

    def draw(self, screen):
        self.camera_group.custom_draw(self.player)
        
        # Interactions
        if not self.dialogue_tree:
            for npc in self.lore_npcs:
                if self.player.rect.colliderect(npc["sprite"].rect.inflate(80, 80)):
                    self.draw_prompt(screen, f"[E] Parler à {npc['name']}", npc["sprite"].rect)
            
            if self.player.rect.colliderect(self.exit_rect):
                self.draw_prompt(screen, "[E] Sortir vers le HUB", self.exit_rect)

        # UI Dialogue
        if self.dialogue_tree:
            node = self.dialogue_tree["config"]["nodes"][self.dialogue_tree["current_node"]]
            self.draw_dialogue_ui(screen, self.dialogue_tree["name"], node)

    def draw_prompt(self, screen, text, rect):
        surf = self.font.render(text, True, NEON_GREEN)
        pos = (WIDTH//2 - surf.get_width()//2, HEIGHT - 120)
        pygame.draw.rect(screen, (0,0,0,150), (pos[0]-10, pos[1]-5, surf.get_width()+20, surf.get_height()+10))
        screen.blit(surf, pos)

    def draw_dialogue_ui(self, screen, name, node):
        box_rect = pygame.Rect(100, HEIGHT - 250, WIDTH - 200, 200)
        pygame.draw.rect(screen, (10, 10, 25), box_rect)
        pygame.draw.rect(screen, NEON_BLUE, box_rect, 2)
        
        # Name
        n_surf = self.font.render(f"--- {name} ---", True, GOLD_COLOR)
        screen.blit(n_surf, (box_rect.x + 20, box_rect.y + 15))
        
        # Text
        txt_surf = self.font.render(node["text"], True, WHITE)
        screen.blit(txt_surf, (box_rect.x + 20, box_rect.y + 55))
        
        # Options
        for i, (opt_text, next_id) in enumerate(node["options"]):
            opt_surf = self.font.render(f"[{i+1}]: {opt_text}", True, NEON_GREEN)
            screen.blit(opt_surf, (box_rect.x + 40, box_rect.y + 100 + i*30))
