import pygame
import math
from src.entities.entity import Entity

class Enemy(Entity):
    def __init__(self, x, y, enemy_type, stats):
        """
        Instancia un enemigo leyendo sus estadísticas dinámicas del JSON.
        """
        # Inicializa la entidad madre (Entity) pasándole posición, velocidad y vida
        super().__init__(x, y, stats["speed"], stats["max_health"])
        
        self.enemy_type = enemy_type
        self.name = stats["name"]
        self.damage = stats["damage"]
        
        # Declaramos explícitamente la vida máxima y actual del enemigo aquí
        self.max_health = stats["max_health"]
        self.current_health = self.max_health

        # Le damos el tamaño estándar del sprite y lo pintamos con su color del JSON
        self.image = pygame.Surface((32, 32))
        self.image.fill(stats["color"])
        
        # El rect para colisiones físicas en el mapa
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Rango en píxeles para detectar al jugador y empezar a perseguirlo
        self.chase_radius = 300 

    def update_ai(self, player_rect):
        """
        Calcula la dirección hacia el jugador usando vectores matemáticos de Pygame.
        """
        # Convertimos las posiciones del enemigo y jugador a vectores de dos dimensiones (X, Y)
        enemy_vec = pygame.math.Vector2(self.rect.center)
        player_vec = pygame.math.Vector2(player_rect.center)
        
        # Restamos los vectores para obtener la distancia y la dirección hacia el jugador
        distance_vec = player_vec - enemy_vec
        distance = distance_vec.length() # Magnitud del vector (píxeles de distancia)

        # Si el jugador entra en su rango de visión (300px), lo empieza a seguir
        if distance <= self.chase_radius and distance > 5:
            # .normalize() transforma el vector para que mida exactamente 1 de longitud,
            # manteniendo la dirección exacta hacia el jugador sin alterar la velocidad.
            self.direction = distance_vec.normalize()
        else:
            # Si el jugador se escapa del rango o está demasiado cerca, el enemigo se frena
            self.direction.x = 0
            self.direction.y = 0

    def update(self, dt, obstacle_sprites, player_rect):
        """
        Ejecuta la IA y aplica el movimiento usando la lógica heredada de Entity.
        """
        # 1. Decidir hacia dónde moverse según la posición del jugador
        self.update_ai(player_rect)
        
        # 2. Moverse físicamente en el mapa respetando los obstáculos (resource_sprites)
        self.move(dt, obstacle_sprites)

    def take_damage(self, amount):
        """Resta vida al enemigo y devuelve True si muere"""
        self.current_health -= amount
        print(f"¡{self.name} golpeado! Vida restante: {self.current_health}/{self.max_health}")
        
        if self.current_health <= 0:
            print(f"¡{self.name} ha sido derrotado!")
            self.kill() # Elimina automáticamente al enemigo de todos los grupos de sprites de Pygame
            return True
        return False