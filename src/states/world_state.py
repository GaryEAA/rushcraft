import pygame
import json
from src.states.base_state import BaseState
from src.entities.player import Player
from src.core.camera import CameraGroup

class WorldState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.color_grass = (34, 139, 34)
        
        # 1. Cargar las estadísticas de las entidades desde el JSON maestro
        self.entities_data = self.load_entities_data()
        
        # 2. Instanciar al jugador en el centro de la pantalla (400, 300) con sus datos del JSON
        player_stats = self.entities_data["player"]
        self.player = Player(400, 300, player_stats)
        
        # 3. Crear un grupo de Sprites de Pygame para gestionar el dibujado de forma limpia
        self.visible_sprites = CameraGroup()
        self.visible_sprites.add(self.player)

        # TODO: (PROVISIONAL) Crear un par de cuadrados grises estáticos en el mapa para comprobar que la cámara se mueve respecto a ellos.
        self.create_test_environment()
        
    # TODO: Eliminar este entorno de prueba cuando implementemos el generador de mapas por chunks
    def create_test_environment(self):
        """Crea objetos fijos en el suelo para testear el movimiento de la cámara"""
        for pos in [(100, 100), (700, 200), (200, 600), (900, 500)]:
            test_sprite = pygame.sprite.Sprite()
            test_sprite.image = pygame.Surface((64, 64))
            test_sprite.image.fill((100, 100, 100)) # Bloques grises (rocas/árboles de prueba)
            test_sprite.rect = test_sprite.image.get_rect(topleft=pos)
            self.visible_sprites.add(test_sprite)

    def load_entities_data(self):
        """Carga la base de datos de entidades"""
        try:
            with open("data/entities.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar data/entities.json: {e}")
            # Valores de respaldo por si el JSON estuviera corrupto
            return {"player": {"max_health": 100, "speed": 200}}

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.change_state("menu")

    def update(self, dt):
        # Actualizar la lógica de todos los sprites dentro del mundo (incluye al jugador)
        self.visible_sprites.update(dt)

    def draw(self, surface):
        surface.fill(self.color_grass)
        
        # Método personalizado con cámara
        self.visible_sprites.custom_draw(self.player)