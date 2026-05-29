import pygame
import json
import sys
from src.managers.data_manager import DataManager
from src.managers.state_manager import StateManager

class Game:
    def __init__(self):
        pygame.init()

        self.data_manager = DataManager()

        # 1. Cargar configuraciones desde nuestra base de datos JSON
        self.settings = self.load_settings()
        
        # 2. Configurar la pantalla leyendo el modo desde el JSON
        flags = 0
        if self.settings.get("fullscreen", False):
            flags |= pygame.FULLSCREEN
            
        self.screen = pygame.display.set_mode(
            (self.settings["screen_width"], self.settings["screen_height"]),
            flags
        )
        pygame.display.set_caption("RushCraft - Modular Sandbox")
        
        # 3. Control de tiempo (FPS)
        self.clock = pygame.time.Clock()
        self.fps = self.settings["fps"]
        self.running = True
        
        # 4. Inicializar el Gestor de Estados del núcleo
        self.state_manager = StateManager(self.data_manager)

        # Importar y registrar el estado del Menú Principal
        from src.states.menu_state import MenuState
        self.state_manager.add_state("menu", MenuState(self.state_manager))

        # Importar, instanciar y registrar el estado del Mundo de Juego
        from src.states.world_state import WorldState
        self.state_manager.add_state("world", WorldState(self.state_manager))
        
        # Definir que el juego debe arrancar mostrando esta pantalla de inmediato
        self.state_manager.change_state("menu")

    def load_settings(self):
        """Lee los parámetros de video iniciales desde el JSON maestro"""
        try:
            with open("data/settings.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"No se pudo cargar settings.json ({e}). Usando valores por defecto.")
            return {"screen_width": 800, "screen_height": 600, "fps": 60}

    def run(self):
        """El bucle principal del juego (Game Loop) desacoplado"""
        while self.running:
            # Calcular el Delta Time (tiempo en segundos que tardó el frame anterior)
            dt = self.clock.tick(self.fps) / 1000.0
            
            # 1. Capturar eventos globales del sistema
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
            
            # 2. Pasar eventos y actualización al Estado Activo del manager
            self.state_manager.handle_events(events)
            self.state_manager.update(dt)
            
            # 3. Renderizar el Estado Activo
            self.screen.fill((0, 0, 0)) # Fondo negro de seguridad
            self.state_manager.draw(self.screen)
            
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()

def main():
    game = Game()
    game.run()