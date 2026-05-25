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

    def custom_draw(self, player):
        """Calcula el desfase respecto al jugador y dibuja todo con esa diferencia"""
        
        # 1. Calcular el centro de la cámara basado en la posición del jugador
        self.offset.x = player.rect.centerx - self.half_width
        self.offset.y = player.rect.centery - self.half_height

        # 2. Dibujar todos los sprites aplicando el desfase matemático
        # Ordenamos los sprites por su propiedad 'rect.centery'
        # Esto hace que si el jugador camina detrás de un árbol, el árbol lo tape correctamente.
        for sprite in sorted(self.sprites(), key=lambda sprite: sprite.rect.centery):
            # Restamos el offset a la posición original del rectángulo para el dibujado en pantalla
            offset_position = sprite.rect.topleft - self.offset
            self.display_surface.blit(sprite.image, offset_position)