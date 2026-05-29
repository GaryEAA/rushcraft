import pygame

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        # Obtener la superficie de la pantalla principal para saber las dimensiones
        self.display_surface = pygame.display.get_surface()
        
        # El vector de desfase (offset). Guardará cuánto debemos mover los objetos en X e Y
        self.offset = pygame.math.Vector2()
        
        # Mitad de la pantalla (para centrar al jugador)
        self.half_width = self.display_surface.get_width() // 2
        self.half_height = self.display_surface.get_height() // 2

    def update_offset(self, player):
        target_x = player.rect.centerx - self.half_width
        target_y = player.rect.centery - self.half_height
        
        lerp_speed = 0.1
        
        self.offset.x += (target_x - self.offset.x) * lerp_speed
        self.offset.y += (target_y - self.offset.y) * lerp_speed

    def draw(self, player, draw_offset):
        """Dibuja todo usando el draw_offset pasado desde fuera."""
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            if hasattr(sprite, 'visual_scale_x'):
                new_width = int(sprite.rect.width * sprite.visual_scale_x)
                new_height = int(sprite.rect.height * sprite.visual_scale_y)
                
                scaled_image = pygame.transform.scale(sprite.image, (new_width, new_height))
                scaled_rect = scaled_image.get_rect()
                
                scaled_rect.center = sprite.rect.center - draw_offset
                
                self.display_surface.blit(scaled_image, scaled_rect.topleft)
                
                indicator_size = 8
                indicator_rect = pygame.Rect(0, 0, indicator_size, indicator_size)
                
                if hasattr(sprite, 'facing_direction'):
                    if sprite.facing_direction == "up":
                        indicator_rect.midtop = scaled_rect.midtop
                    elif sprite.facing_direction == "down":
                        indicator_rect.midbottom = scaled_rect.midbottom
                    elif sprite.facing_direction == "left":
                        indicator_rect.midleft = scaled_rect.midleft
                    elif sprite.facing_direction == "right":
                        indicator_rect.midright = scaled_rect.midright
                
                pygame.draw.rect(self.display_surface, (0, 0, 0), indicator_rect)
            else:
                offset_position = sprite.rect.topleft - draw_offset
                self.display_surface.blit(sprite.image, offset_position)