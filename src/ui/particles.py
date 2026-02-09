import pygame
import random
import math

class Particle:
    def __init__(self, pos, color, speed, lifetime, size):
        self.x, self.y = pos
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.lifetime = lifetime
        self.original_lifetime = lifetime
        self.size = size
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        
    def draw(self, screen):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.original_lifetime))
            current_size = max(1, int(self.size * (self.lifetime / self.original_lifetime)))
            
            surf = pygame.Surface((current_size*2, current_size*2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*self.color, alpha), (current_size, current_size), current_size)
            screen.blit(surf, (int(self.x - current_size), int(self.y - current_size)))

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def add_explosion(self, pos, color, count=10):
        for _ in range(count):
            speed = random.uniform(1, 4)
            lifetime = random.randint(20, 40)
            size = random.randint(2, 5)
            self.particles.append(Particle(pos, color, speed, lifetime, size))
            
    def add_trail(self, pos, color):
        self.particles.append(Particle(pos, color, 0.5, 10, 3))

    def update(self):
        self.particles = [p for p in self.particles if p.lifetime > 0]
        for p in self.particles:
            p.update()
            
    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)
