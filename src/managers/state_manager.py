import pygame

class StateManager:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.states = {}
        self.current_state = None

    def add_state(self, state_name, state_instance):
        """Registra un nuevo estado en la máquina"""
        self.states[state_name] = state_instance

    def change_state(self, state_name):
        """Cambia el estado activo actual de forma segura"""
        if state_name in self.states:
            self.current_state = self.states[state_name]
            print(f"Máquina de Estados: Cambiado al estado '{state_name}'")
        else:
            print(f"Error: El estado '{state_name}' no está registrado en el manager.")

    def handle_events(self, events):
        """Delega los inputs recibidos al estado activo"""
        if self.current_state:
            self.current_state.handle_events(events)

    def update(self, dt):
        """Delega la actualización lógica al estado activo"""
        if self.current_state:
            self.current_state.update(dt)

    def draw(self, surface):
        """Delega el renderizado visual al estado activo"""
        if self.current_state:
            self.current_state.draw(surface)