import pygame

class Resource(pygame.sprite.Sprite):
    def __init__(self, x, y, resource_type, health, item_yield):
        """
        Clase base para objetos recolectables del mapa (Árboles, Rocas, etc.)
        """
        super().__init__()
        self.type = resource_type
        self.health = health
        self.max_health = health
        self.item_yield = item_yield  # El ID del ítem que otorgará al romperse (ej: "wood")
        
        # Configuración gráfica provisional
        self.image = pygame.Surface((48, 64) if resource_type == "tree" else (40, 40))
        
        # Asignar colores según el tipo de recurso
        if self.type == "tree":
            self.image.fill((139, 69, 19)) # Café Madera
        else:
            self.image.fill((128, 128, 128)) # Gris para rocas
            
        self.rect = self.image.get_rect(topleft=(x, y))

    def hit(self, damage=10):
        """Disminuye la vida del recurso cuando el jugador lo golpea"""
        self.health -= damage
        print(f"¡Impacto en {self.type}! Vida restante: {self.health}/{self.max_health}")
        
        # Si la vida llega a 0, el recurso se destruye
        if self.health <= 0:
            print(f"El {self.type} ha sido destruido por completo.")
            return True # Indica que debe ser removido y dar su recompensa
        return False