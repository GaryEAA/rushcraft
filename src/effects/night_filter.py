import pygame

class NightFilter:
    def __init__(self, width, height):
        """
        Gestiona la opacidad ambiental del mapa de forma gradual y sincronizada.
        """
        self.surface = pygame.Surface((width, height))
        self.surface.fill((10, 10, 35)) # Azul noche profundo
        self.alpha = 0 

    def update(self, current_hour, current_minute):
        """Calcula el nivel de oscuridad (alpha) sincronizado con las fases de 6 horas"""
        time_decimal = current_hour + (current_minute / 60.0)
        
        # --- LÓGICA DE TRANSICIÓN UNIFICADA ---
        
        # 1. ATARDECER/ANOCHECER GRADUAL: De 18:00 a 19:30 el filtro sube de 0 a 180
        if 18.0 <= time_decimal < 19.5:
            progress = (time_decimal - 18.0) / 1.5  # Transición suave de 1 hora y media
            self.alpha = int(progress * 180)
            
        # 2. NOCHE Y MADRUGADA PROFUNDA: De 19:30 a 05:00 máxima oscuridad fija
        elif time_decimal >= 19.5 or time_decimal < 5.0:
            self.alpha = 180
            
        # 3. AMANECER GRADUAL: De 05:00 a 06:00 la oscuridad se disipa de 180 a 0
        elif 5.0 <= time_decimal < 6.0:
            progress = (time_decimal - 5.0) / 1.0  # Dura exactamente 1 hora de juego
            self.alpha = int(180 * (1.0 - progress))
            
        # 4. PLENO DÍA Y TARDE: De 06:00 a 18:00 es completamente transparente
        else:
            self.alpha = 0

        self.surface.set_alpha(self.alpha)

    def draw(self, target_surface):
        """Dibuja la capa de oscuridad sobre la pantalla si es necesario"""
        if self.alpha > 0:
            target_surface.blit(self.surface, (0, 0))