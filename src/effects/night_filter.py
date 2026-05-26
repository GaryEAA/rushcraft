import pygame

class NightFilter:
    def __init__(self, width, height):
        """
        Gestiona el filtro de luz ambiental para el ciclo día/noche.
        Crea una capa translúcida que se superpone a todo el juego.
        """
        self.surface = pygame.Surface((width, height))
        self.surface.fill((10, 10, 35)) # Azul noche profundo
        self.alpha = 0 # 0 = Completamente invisible (Día), 255 = Oscuridad total

    def update(self, current_hour, current_minute):
        """Calcula el nivel de oscuridad (alpha) de forma gradual según la hora"""
        # Convertimos la hora actual a un valor decimal (ej: 18.5 para las 18:30)
        time_decimal = current_hour + (current_minute / 60.0)
        
        # --- LÓGICA DE TRANSICIÓN MATEMÁTICA ---
        # 1. ATARDECER: De 18:00 a 20:00 la oscuridad sube gradualmente de 0 a 180
        if 18.0 <= time_decimal < 20.0:
            progress = (time_decimal - 18.0) / 2.0 # Factor de 0.0 a 1.0
            self.alpha = int(progress * 180)
            
        # 2. NOCHE PROFUNDA: De 20:00 a 04:00 se mantiene en su punto más oscuro (180)
        elif time_decimal >= 20.0 or time_decimal < 4.0:
            self.alpha = 180
            
        # 3. AMANECER: De 04:00 a 06:00 la oscuridad baja gradualmente de 180 a 0
        elif 4.0 <= time_decimal < 6.0:
            progress = (time_decimal - 4.0) / 2.0 # Factor de 0.0 a 1.0
            self.alpha = int(180 * (1.0 - progress))
            
        # 4. PLENO DÍA: De 06:00 a 18:00 es completamente transparente
        else:
            self.alpha = 0

        # Aplicar el nivel de transparencia calculado a la capa
        self.surface.set_alpha(self.alpha)

    def draw(self, target_surface):
        """Dibuja la capa de oscuridad sobre la pantalla si es necesario"""
        if self.alpha > 0:
            target_surface.blit(self.surface, (0, 0))