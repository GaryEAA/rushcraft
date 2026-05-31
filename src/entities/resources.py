import random
import pygame
from .item_drop import ItemDrop
 
 
class Resource(pygame.sprite.Sprite):
    """
    Recurso del mundo. Imagen = tamaño exacto de hitbox.
    Soporta daño por contacto (ej: cactus) además del hit() normal.
    """
 
    def __init__(self, x, y, resource_type, config):
        super().__init__()
        self.type          = resource_type
        self.health        = config.get("health", 10)
        self.max_health    = self.health
        self.item_yield    = config.get("item_yield", "wood")
        self.is_solid      = config.get("is_solid", False)
        self.min_tool_tier = config.get("min_tool_tier", 0)
        self.contact_damage = config.get("contact_damage", 0)   # daño por tocar (cactus=5)
 
        drop = config.get("drop_amount", [1, 3])
        self.drop_min = drop[0]
        self.drop_max = drop[1]
 
        hb_data = config.get("hitbox", [28, 28])
        hb_w = max(4, hb_data[0])
        hb_h = max(4, hb_data[1])
 
        color = config.get("color", [255, 0, 255])
        self.image = pygame.Surface((hb_w, hb_h))
        self.image.fill(color)
 
        self.rect    = self.image.get_rect(topleft=(x, y))
        self.hitbox  = self.rect.copy()
 
        self._grid_manager  = None
        self._data_manager  = None
 
    def register_grid(self, grid_manager):
        self._grid_manager = grid_manager
 
    def register_data(self, data_manager):
        self._data_manager = data_manager
 
    # ──────────────────────────────────────────────────
    #  Daño por herramienta
    # ──────────────────────────────────────────────────
 
    def hit(self, damage, drop_groups, tool_tier=0):
        if tool_tier < self.min_tool_tier:
            damage = max(1, damage // 4)
            print(f"[Resource] Herramienta insuficiente para '{self.type}'. Daño: {damage}")
 
        self.health -= damage
        if self.health <= 0:
            self._destroy(drop_groups)
 
    # ──────────────────────────────────────────────────
    #  Destrucción
    # ──────────────────────────────────────────────────
 
    def _destroy(self, drop_groups):
        qty = random.randint(self.drop_min, self.drop_max)
        ItemDrop(
            pos          = self.rect.center,
            groups       = drop_groups,
            item_id      = self.item_yield,
            amount       = qty,
            data_manager = self._data_manager
        )
        if self._grid_manager:
            self._grid_manager.remove_resource(self)
        self.kill()
 