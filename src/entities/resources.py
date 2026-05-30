import random
import pygame
from .item_drop import ItemDrop
 
class Resource(pygame.sprite.Sprite):
    def __init__(self, x, y, resource_type, config):
        super().__init__()
        self.type        = resource_type
        self.health      = config.get("health", 10)
        self.max_health  = self.health
        self.item_yield  = config.get("item_yield", "wood")
        self.is_solid    = config.get("is_solid", False)
        self.min_tool_tier = config.get("min_tool_tier", 0)
 
        # Drop amount: [min, max] desde JSON, fallback 1-3
        drop = config.get("drop_amount", [1, 3])
        self.drop_min = drop[0]
        self.drop_max = drop[1]
 
        # Visual: cuadrado de 40x40 con el color del JSON
        color = config.get("color", [255, 0, 255])
        self.image = pygame.Surface((40, 40))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
 
        # Hitbox: [ancho, alto] en píxeles absolutos (NO inflate)
        hb_data = config.get("hitbox", [30, 30])
        hb_w = max(4, hb_data[0])
        hb_h = max(4, hb_data[1])
        self.hitbox = pygame.Rect(0, 0, hb_w, hb_h)
        self.hitbox.midbottom = self.rect.midbottom
 
    def hit(self, damage, drop_groups, tool_tier=0):
        """
        Aplica daño al recurso. Si el tier de la herramienta es insuficiente,
        el daño se penaliza fuertemente (pero no bloquea, para dar feedback).
        """
        if tool_tier < self.min_tool_tier:
            damage = max(1, damage // 4)
            print(f"[Resource] Herramienta insuficiente para '{self.type}'. Daño reducido a {damage}.")
 
        self.health -= damage
 
        if self.health <= 0:
            qty = random.randint(self.drop_min, self.drop_max)
            ItemDrop(
                pos    = self.rect.center,
                groups = drop_groups,
                item_id= self.item_yield,
                amount = qty
            )
            self.kill()