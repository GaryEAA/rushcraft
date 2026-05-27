class GameClock:
    def __init__(self, time_scale=60.0):
        """
        Gestiona el tiempo global del juego (Minutos, Horas, Días).
        """
        self.time_scale = time_scale
        
        # El juego empieza a las 6:00 AM
        self.total_game_seconds = 6.0 * 3600.0 
        
        self.minute = 0
        self.hour = 6
        self.day = 1
        
        self.is_daytime = True

    def update(self, dt):
        """Avanza el reloj del juego basándose en el Delta Time real"""
        self.total_game_seconds += dt * self.time_scale
        
        total_minutes = int(self.total_game_seconds // 60)
        
        self.minute = total_minutes % 60
        self.hour = (total_minutes // 60) % 24
        self.day = (total_minutes // 1440) + 1 
        
        # Es de noche desde las 18:00 (Fase Noche) hasta las 05:59 (Madrugada)
        if self.hour >= 18 or self.hour < 6:
            if self.is_daytime:
                self.is_daytime = False
                print("Ha caído la noche sobre RushCraft... Mobs activados.")
        else:
            if not self.is_daytime:
                self.is_daytime = True
                print("El sol está saliendo de nuevo... Mobs disolviéndose.")

    # Desacoplado y listo para futuros cambios (como climas o estaciones)
    def get_current_phase_data(self):
        """
        Devuelve una tupla con (nombre_fase, color_rgb) según la hora actual.
        Fases exactas de 6 horas basadas en la Opción 1.
        """
        if 6 <= self.hour < 12:
            return "Día", (255, 255, 255)        # Blanco puro
        elif 12 <= self.hour < 18:
            return "Tarde", (255, 200, 100)      # Tono cálido/anaranjado
        elif 18 <= self.hour < 24:
            return "Noche", (180, 180, 255)      # Azul noche
        else: # De 00:00 a 05:59
            return "Madrugada", (130, 130, 200)  # Azul oscuro/frío

    def get_time_string(self):
        """Devuelve una cadena con formato bonito tipo reloj digital de 24h"""
        return f"Día {self.day} - {self.hour:02d}:{self.minute:02d}"