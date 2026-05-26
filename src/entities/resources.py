import pygame
from .item_drop import ItemDrop

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

        # NUEVO: Hitbox física del obstáculo (reducida para permitir perspectiva)
        if self.type == "tree":
            self.hitbox = self.rect.copy().inflate(-20, -40) # Solo el centro inferior es sólido
        else:
            self.hitbox = self.rect.copy().inflate(-6, -6)   # La roca es casi sólida por complet

    def hit(self, damage, drop_groups):
        """Disminuye la vida del recurso y genera el drop si es destruido"""
        self.health -= damage
        print(f"¡Impacto en {self.type}! Vida restante: {self.health}/{self.max_health}")
        
        # Si la vida llega a 0, el recurso expulsa el ítem al suelo y se destruye
        if self.health <= 0:
            print(f"El {self.type} ha sido destruido por completo.")
            
            # Definir cantidad según tipo de recurso
            qty = 15 if self.type == "tree" else 8
            
            # Instanciamos el ítem físico flotando en la posición del recurso
            ItemDrop(
                pos = self.rect.center,
                groups = drop_groups,
                item_id = self.item_yield,
                amount = qty
            )
            
            self.kill() # Desaparece el árbol/roca