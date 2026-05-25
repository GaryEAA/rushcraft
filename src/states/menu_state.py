import pygame
from src.states.base_state import BaseState

class MenuState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        
        # Fuentes del sistema provisionales (Tamaño grande para título, mediano para opciones)
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)
        self.font = pygame.font.SysFont("Arial", 32)
        
        # Colores de la interfaz
        self.color_title = (255, 215, 0)      # Dorado
        self.color_text = (255, 255, 255)     # Blanco
        self.color_bg = (20, 20, 30)          # Azul oscuro neutro para el fondo

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                # Si el jugador presiona ENTER, ordenamos al manager cambiar al estado de juego
                if event.key == pygame.K_RETURN:
                    # 'world' será el identificador de la pantalla de supervivencia activa
                    self.manager.change_state("world")

    def update(self, dt):
        # Por ahora el menú es estático, no requiere físicas ni cálculos de tiempo
        pass

    def draw(self, surface):
        # 1. Limpiar la pantalla pintando el fondo oscuro del menú
        surface.fill(self.color_bg)
        
        # 2. Renderizar el texto del Título
        title_surf = self.title_font.render("RUSHCRAFT", True, self.color_title)
        title_rect = title_surf.get_rect(center=(surface.get_width() // 2, surface.get_height() // 3))
        surface.blit(title_surf, title_rect)
        
        # 3. Renderizar las instrucciones para el usuario
        prompt_surf = self.font.render("Presiona [ ENTER ] para comenzar", True, self.color_text)
        prompt_rect = prompt_surf.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2 + 50))
        surface.blit(prompt_surf, prompt_rect)