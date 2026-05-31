import pygame
import math
 
 
class ItemDrop(pygame.sprite.Sprite):
    """
    Ítem dropeado en el suelo. Flota con seno.
    Color leído de drop_color en items_db.json (via data_manager) — sin JSON separado.
    """
 
    def __init__(self, pos, groups, item_id, amount, data_manager=None):
        super().__init__(groups)
        self.item_id = item_id
        self.amount  = amount
 
        # Buscar drop_color directamente en el ítem; magenta si falta (alerta visual)
        color = (255, 0, 255)
        if data_manager is not None:
            item = data_manager.get_item(item_id)
            if item and "drop_color" in item:
                color = tuple(item["drop_color"])
 
        self.image = pygame.Surface((14, 14))
        self.image.fill(color)
        pygame.draw.rect(self.image, (255, 255, 255), self.image.get_rect(), 1)
 
        self.rect = self.image.get_rect(center=pos)
        self.pos  = pygame.math.Vector2(pos)
 
    def update(self, dt):
        self.rect.centery = int(self.pos.y + math.sin(pygame.time.get_ticks() * 0.004) * 4)
 