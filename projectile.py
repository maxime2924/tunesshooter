import pygame

class Projectile(pygame.sprite.Sprite):
    def __init__(self, pos, velocity, screen_rect=None, damage=1):
        super().__init__()
        size = 6
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 0), (size//2, size//2), size//2)
        self.rect = self.image.get_rect(center=pos)
        self.vel = pygame.math.Vector2(velocity)
        self.screen_rect = screen_rect
        self.damage = damage

    def update(self, *args):
        self.rect.x += self.vel.x
        self.rect.y += self.vel.y
        if self.screen_rect and not self.screen_rect.colliderect(self.rect):
            self.kill()
