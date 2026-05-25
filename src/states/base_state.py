import pygame

class BaseState:
    def __init__(self, state_manager):
        """
        Clase abstracta/madre para todos los estados del juego.
        Guarda una referencia al manager para poder ordenar cambios de pantalla.
        """
        self.manager = state_manager

    def handle_events(self, events):
        """Procesa clicks, teclas y entradas del usuario específicas de esta pantalla"""
        pass

    def update(self, dt):
        """Procesa la física, IA y lógica interna de esta pantalla"""
        pass

    def draw(self, surface):
        """Dibuja los elementos visuales de esta pantalla en la ventana principal"""
        pass