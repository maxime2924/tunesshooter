import pygame

def separate_sprites(a: pygame.sprite.Sprite, b: pygame.sprite.Sprite, push_a: bool = True, push_b: bool = True):
    """Sépare deux sprites qui se chevauchent (AABB).
    - Si push_a et push_b sont True, on déplace les deux de moitié.
    - Si seul push_b est True, on déplace seulement b (utile pour pousser les ennemis hors du joueur).
    """
    overlap = a.rect.clip(b.rect)
    if overlap.width == 0 or overlap.height == 0:
        return

    # Choisir la plus petite pénétration (x ou y)
    if overlap.width < overlap.height:
        # Séparer sur l'axe X
        if a.rect.centerx < b.rect.centerx:
            # a à gauche, b à droite
            move_x = overlap.width
            move_a = -move_x // 2 if push_a and push_b else (-move_x if push_a else 0)
            move_b = move_x // 2 if push_a and push_b else (move_x if push_b else 0)
        else:
            move_x = overlap.width
            move_a = move_x // 2 if push_a and push_b else (move_x if push_a else 0)
            move_b = -move_x // 2 if push_a and push_b else (-move_x if push_b else 0)

        a.rect.x += int(move_a)
        b.rect.x += int(move_b)
    else:
        # Séparer sur l'axe Y
        if a.rect.centery < b.rect.centery:
            move_y = overlap.height
            move_a = -move_y // 2 if push_a and push_b else (-move_y if push_a else 0)
            move_b = move_y // 2 if push_a and push_b else (move_y if push_b else 0)
        else:
            move_y = overlap.height
            move_a = move_y // 2 if push_a and push_b else (move_y if push_a else 0)
            move_b = -move_y // 2 if push_a and push_b else (-move_y if push_b else 0)

        a.rect.y += int(move_a)
        b.rect.y += int(move_b)
