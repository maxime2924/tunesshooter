import pygame
from settings import *

class ShopItem:
    def __init__(self, name, cost, min_level, effect_type, effect_value, description):
        self.name = name
        self.cost = cost
        self.min_level = min_level
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.description = description
        self.purchased_count = 0

    def apply_effect(self, player):
        if self.effect_type == "passive_gold":
            player.gold_per_second += self.effect_value
            player.gold_multiplier = getattr(player, 'gold_multiplier', 1.0) + 0.1
        elif self.effect_type == "damage":
            player.projectile_damage += self.effect_value
        elif self.effect_type == "speed":
            player.speed += self.effect_value
            player.base_speed = player.speed
        elif self.effect_type == "hp":
            player.max_hp += self.effect_value
            player.hp = player.max_hp


class Merchant:
    def __init__(self, x=0, y=0):
        self.items = [
            # PASSIVE GOLD (Fixer Info)
            ShopItem("Serveur de Minage v1", 100, 1, "passive_gold", 1, "Génère 1 or/sec"),
            ShopItem("Ferme de Crypto", 500, 3, "passive_gold", 5, "Génère 5 or/sec"),
            ShopItem("Data Center Illegal", 2000, 7, "passive_gold", 20, "Génère 20 or/sec"),
            
            # DAMAGE (Armurier)
            ShopItem("Puce d'Overclocking", 150, 2, "damage", 1, "+1 Dégât"),
            ShopItem("Condensateur Laser", 600, 5, "damage", 3, "+3 Dégâts"),
            ShopItem("Noyau de Fusion", 2500, 10, "damage", 10, "+10 Dégâts"),
            
            # HP (Ingénieur Système)
            ShopItem("Nano-Réparateurs", 200, 2, "hp", 20, "+20 PV Max"),
            ShopItem("Bio-Armure Plastique", 800, 4, "hp", 50, "+50 PV Max"),
            ShopItem("Exosquelette Combat", 3000, 8, "hp", 150, "+150 PV Max"),
            
            # SPEED (Garagiste)
            ShopItem("Propulseur Ionique", 300, 3, "speed", 1, "+1 Vitesse"),
            ShopItem("Turbo Compresseur", 900, 6, "speed", 2, "+2 Vitesse"),
            ShopItem("Moteur à Distorsion", 4000, 12, "speed", 5, "+5 Vitesse"),
        ]
        self.font_title = pygame.font.SysFont(None, 40)
        self.font_text = pygame.font.SysFont(None, 24)
        
        # Sprite representation for Hub
        self.image = pygame.Surface((40, 60))
        self.image.fill(GOLD_COLOR)
        # On peut dessiner un petit bonhomme ou stand
        pygame.draw.rect(self.image, (50, 50, 50), (0, 40, 40, 20)) # Base du stand
        self.rect = self.image.get_rect(topleft=(x, y))


    def buy_item(self, item, player):
        if player.level < item.min_level:
            return False, f"Niveau {item.min_level} requis !"

        if player.banked_gold >= item.cost:
            player.banked_gold -= item.cost
            item.purchased_count += 1
            item.apply_effect(player)
            # Inflation
            item.cost = int(item.cost * 1.3)
            return True, f"Acheté : {item.name}"
        else:
            return False, "Pas assez d'or en banque !"

    def draw_shop_interface(self, screen, player):
        screen_rect = screen.get_rect()
        bg = pygame.Surface((600, 500))
        bg.fill((20, 20, 30))
        bg.set_alpha(240)
        shop_rect = bg.get_rect(center=screen_rect.center)
        screen.blit(bg, shop_rect)

        title = self.font_title.render(f"MARCHÉ NOIR (Banque: {int(player.banked_gold)}g)", True, GOLD_COLOR)
        screen.blit(title, (shop_rect.x + 20, shop_rect.y + 20))

        buttons = []
        y_offset = shop_rect.y + 80
        for item in self.items:
            if player.level < item.min_level:
                color = (80, 80, 80)
                name_txt = f"[VERROUILLÉ - Lvl {item.min_level}] {item.name}"
            elif player.banked_gold < item.cost:
                color = RED
                name_txt = f"{item.name}"
            else:
                color = GREEN
                name_txt = f"{item.name}"

            btn_rect = pygame.Rect(shop_rect.x + 20, y_offset, 560, 60)
            pygame.draw.rect(screen, (40, 40, 50), btn_rect, border_radius=8)
            pygame.draw.rect(screen, color, btn_rect, 2, border_radius=8)

            name_surf = self.font_text.render(f"{name_txt} - Coût: {item.cost}g", True, color)
            desc_surf = self.font_text.render(f"   Effet: {item.description} (Possédé: {item.purchased_count})", True,
                                              WHITE)

            screen.blit(name_surf, (btn_rect.x + 10, btn_rect.y + 10))
            screen.blit(desc_surf, (btn_rect.x + 10, btn_rect.y + 35))

            buttons.append((btn_rect, item))
            y_offset += 70

        close_txt = self.font_text.render("Appuyez sur ECHAP pour fermer", True, WHITE)
        screen.blit(close_txt, (shop_rect.centerx - close_txt.get_width() // 2, shop_rect.bottom - 30))

        # Bouton Quitter (X)
        close_rect = pygame.Rect(shop_rect.right - 50, shop_rect.y + 10, 40, 40)
        pygame.draw.rect(screen, RED, close_rect, border_radius=5)
        close_txt = self.font_title.render("X", True, WHITE)
        screen.blit(close_txt, (close_rect.centerx - close_txt.get_width()//2, close_rect.centery - close_txt.get_height()//2))
        buttons.append((close_rect, "close"))

        return buttons