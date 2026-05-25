import pygame
from src.states.base_state import BaseState

class WorldState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        # Color verde césped para identificar que ya estamos "dentro" del mundo de juego
        self.color_grass = (34, 139, 34)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Si el jugador presiona ESCAPE, podríamos regresarlo al menú (o pausar)
                if event.key == pygame.K_ESCAPE:
                    self.manager.change_state("menu")

    def update(self, dt):
        # Aquí procesaremos las físicas, movimientos y spawn de enemigos más adelante
        pass

    def draw(self, surface):
        # Pintar el fondo verde del mapa
        surface.fill(self.color_grass)