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
        self.offset.x = int(player.rect.centerx - self.half_width)
        self.offset.y = int(player.rect.centery - self.half_height)

    def draw(self, player):
        """Calcula el desfase respecto al jugador y dibuja todo con esa diferencia"""
        # Actualizamos el offset usando el jugador
        self.update_offset(player)
        # Dibujar todos los sprites aplicando el desfase matemático (Ordenados por profundidad Y)
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            # Si el sprite tiene animaciones de deformación por código
            if hasattr(sprite, 'visual_scale_x'):
                # 1. Calculamos las dimensiones con el estiramiento elástico del ataque
                new_width = int(sprite.rect.width * sprite.visual_scale_x)
                new_height = int(sprite.rect.height * sprite.visual_scale_y)
                
                scaled_image = pygame.transform.scale(sprite.image, (new_width, new_height))
                
                scaled_rect = scaled_image.get_rect()
                scaled_rect.center = sprite.rect.center - self.offset
                
                # 2. Dibujamos el cuerpo base del jugador
                self.display_surface.blit(scaled_image, scaled_rect.topleft)
                
                # Dibujar el indicador visual de dirección (Visor)
                # Creamos un pequeño cuadradito que simulará sus ojos/frente
                indicator_size = 8
                indicator_rect = pygame.Rect(0, 0, indicator_size, indicator_size)
                
                # Posicionamos el indicador en el borde correspondiente según hacia dónde mira
                if hasattr(sprite, 'facing_direction'):
                    if sprite.facing_direction == "up":
                        indicator_rect.midtop = scaled_rect.midtop
                    elif sprite.facing_direction == "down":
                        indicator_rect.midbottom = scaled_rect.midbottom
                    elif sprite.facing_direction == "left":
                        indicator_rect.midleft = scaled_rect.midleft
                    elif sprite.facing_direction == "right":
                        indicator_rect.midright = scaled_rect.midright
                
                # Pintamos el indicador de un color visible (ej: Negro o Amarillo para contrastar con el azul)
                pygame.draw.rect(self.display_surface, (0, 0, 0), indicator_rect)
                
            else:
                # Dibujado tradicional para recursos y enemigos
                offset_position = sprite.rect.topleft - self.offset
                self.display_surface.blit(sprite.image, offset_position)