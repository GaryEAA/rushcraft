import pygame
import json
from src.states.base_state import BaseState
from src.entities.player import Player

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
        self.visible_sprites = pygame.sprite.Group()
        self.visible_sprites.add(self.player)

    def load_entities_data(self):
        """Carga la base de datos de entidades"""
        try:
            with open("data/entities.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error al cargar data/entities.json: {e}")
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
        
        # Dibujar todos los sprites en la pantalla automáticamente
        self.visible_sprites.draw(surface)