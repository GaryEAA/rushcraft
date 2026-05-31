import pygame
 
 
class CameraGroup(pygame.sprite.Group):
    """
    Grupo de sprites con cámara suave (lerp) centrada en el jugador.
    Cada sprite se dibuja mostrando SOLO su hitbox coloreada.
    Sin imágenes sobrantes: lo que ves es exactamente la zona de colisión.
    """
 
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset          = pygame.math.Vector2()
        self.half_width      = self.display_surface.get_width()  // 2
        self.half_height     = self.display_surface.get_height() // 2
 
    def update_offset(self, player):
        target_x = player.rect.centerx - self.half_width
        target_y = player.rect.centery - self.half_height
        lerp     = 0.10
        self.offset.x += (target_x - self.offset.x) * lerp
        self.offset.y += (target_y - self.offset.y) * lerp
 
    def draw(self, draw_offset):
        """
        Dibuja cada sprite usando su hitbox como área visual.
        Orden de dibujado por profundidad (centery), igual que antes.
        """
        surf = self.display_surface
 
        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):
 
            # Obtener hitbox del sprite (todos los nuestros la tienen)
            hb = sprite.hitbox if hasattr(sprite, "hitbox") else sprite.rect
 
            # Posición en pantalla
            screen_x = hb.x - int(draw_offset.x)
            screen_y = hb.y - int(draw_offset.y)
            screen_rect = pygame.Rect(screen_x, screen_y, hb.width, hb.height)
 
            # ── Player ───────────────────────────────────────────────
            if hasattr(sprite, "facing_direction"):
                # Relleno sólido de la hitbox
                pygame.draw.rect(surf, sprite.image.get_at((0, 0)), screen_rect)
                # Borde blanco para distinguirlo
                pygame.draw.rect(surf, (255, 255, 255), screen_rect, 2)
 
                # Indicador de dirección (triángulo pequeño)
                self._draw_direction_indicator(surf, screen_rect,
                                               sprite.facing_direction)
 
            # ── Enemigos ─────────────────────────────────────────────
            elif hasattr(sprite, "update_ai"):
                color = sprite.image.get_at((0, 0))
                pygame.draw.rect(surf, color, screen_rect)
                pygame.draw.rect(surf, (220, 50, 50), screen_rect, 2)
 
            # ── Recursos y demás ─────────────────────────────────────
            else:
                # La imagen ya tiene el tamaño exacto de la hitbox
                surf.blit(sprite.image, (screen_x, screen_y))
                # Borde fino para ver el contorno de la celda ocupada
                pygame.draw.rect(surf, (0, 0, 0), screen_rect, 1)
 
    # ──────────────────────────────────────────────────────────────────
 
    def _draw_direction_indicator(self, surf, rect, direction):
        """Dibuja una flechita pequeña que indica a dónde mira el player."""
        cx, cy = rect.centerx, rect.centery
        size   = 6
        color  = (0, 0, 0)
 
        if direction == "up":
            pts = [(cx, cy - rect.height // 2 - size),
                   (cx - size // 2, cy - rect.height // 2),
                   (cx + size // 2, cy - rect.height // 2)]
        elif direction == "down":
            pts = [(cx, cy + rect.height // 2 + size),
                   (cx - size // 2, cy + rect.height // 2),
                   (cx + size // 2, cy + rect.height // 2)]
        elif direction == "left":
            pts = [(cx - rect.width // 2 - size, cy),
                   (cx - rect.width // 2, cy - size // 2),
                   (cx - rect.width // 2, cy + size // 2)]
        else:  # right
            pts = [(cx + rect.width // 2 + size, cy),
                   (cx + rect.width // 2, cy - size // 2),
                   (cx + rect.width // 2, cy + size // 2)]
 
        pygame.draw.polygon(surf, color, pts)
 