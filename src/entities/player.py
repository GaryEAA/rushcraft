import pygame
from src.entities.entity import Entity
from src.managers.inventory_system import InventorySystem

class Player(Entity):
    def __init__(self, x, y, stats):
        """
        Instancia al jugador leyendo sus estadísticas iniciales 
        (las cuales vendrán desde nuestro entities.json)
        """
        super().__init__(x, y, stats["speed"], stats["max_health"])
        
        # Personalizar el color del cuadrado del jugador para diferenciarlo de un enemigo
        self.image.fill((30, 144, 255)) # Azul brillante (Dodger Blue)
        
        # Inyectar el componente de inventario leyendo la capacidad desde el JSON
        slots_capacity = stats.get("inventory_size", 8)
        self.inventory = InventorySystem(total_slots=slots_capacity)
        self.active_slot = 0 # Guarda el índice del slot seleccionado (0 al 11)


    def input(self):
        """Escucha el teclado y altera la dirección del vector de movimiento"""
        keys = pygame.key.get_pressed()
        
        # Resetear dirección en cada frame
        self.direction.x = 0
        self.direction.y = 0

        # TODO: MOVIMIENTO CON TECLAS WASD O FLECHAS
        # Movimiento en Eje Y (Arriba / Abajo)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.direction.y = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction.y = 1
            
        # Movimiento en Eje X (Izquierda / Derecha)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.direction.x = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction.x = 1

        # TODO: SELECCIÓN DE LA HOTBAR
        # Teclas del 1 al 9 (Índices 0 al 8)
        for i in range(9):
            if keys[pygame.K_1 + i]:
                self.active_slot = i

        # Tecla 0 (Slot 10, Índice 9)
        if keys[pygame.K_0]:
            self.active_slot = 9

        # Tecla "," (Slot 11, Índice 10)
        if keys[pygame.K_COMMA]:
            self.active_slot = 10
            
        # Tecla "." (Slot 12, Índice 11)
        if keys[pygame.K_PERIOD]:
            self.active_slot = 11
            
    def update(self, dt, obstacle_sprites):
        """Actualización frame a frame del jugador con conocimiento de obstáculos"""
        self.input()
        # Le pasamos los obstáculos al método move de la clase madre (Entity)
        self.move(dt, obstacle_sprites)