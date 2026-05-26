import pygame
import math

class ItemDrop(pygame.sprite.Sprite):
    def __init__(self, pos, groups, item_id, amount):
        super().__init__(groups)
        self.item_id = item_id
        self.amount = amount
        
        # Aspecto visual (un cuadradito pequeño representativo)
        self.image = pygame.Surface((16, 16))
        color = (150, 75, 0) if item_id == "wood" else (120, 120, 120)
        self.image.fill(color)
        
        self.rect = self.image.get_rect(center = pos)
        
        # Para el efecto de "flotar" (animación)
        self.pos = pygame.math.Vector2(pos)
        self.offset = 0
        self.start_time = pygame.time.get_ticks()

    def update(self, dt):
        # Efecto de levitación usando la función Seno
        self.offset = math.sin(pygame.time.get_ticks() * 0.005) * 5
        self.rect.centery = self.pos.y + self.offset