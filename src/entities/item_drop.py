import pygame
import math

class ItemDrop(pygame.sprite.Sprite):
    def __init__(self, pos, groups, item_id, amount):
        super().__init__(groups)
        self.item_id = item_id
        self.amount = amount
        
        # Aspecto visual (un cuadradito pequeño representativo)
        self.image = pygame.Surface((16, 16))
        
        # 1. DICCIONARIO DE COLORES ASOCIADOS A CADA ÍTEM
        colores_items = {
            "wood": (150, 75, 0),       # Marrón madera
            "stone": (120, 120, 120),   # Gris roca
            "apple": (230, 30, 30),     # Rojo manzana
            "meat": (255, 105, 180)     # Rosado carne
        }
        
        # 2. Si el item_id no existe en el diccionario, 
        # usa el color Magenta (255, 0, 255) como alerta visual de error.
        color = colores_items.get(self.item_id, (255, 0, 255))
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