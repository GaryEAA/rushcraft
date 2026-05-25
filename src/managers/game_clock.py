class GameClock:
    def __init__(self, time_scale=60.0):
        """
        Gestiona el tiempo global del juego (Minutos, Horas, Días).
        'time_scale' define cuántas veces más rápido pasa el tiempo del juego respecto al real.
        Por defecto: 1 segundo real = 1 minuto de juego (Factor 60.0)
        """
        self.time_scale = time_scale
        
        # El tiempo se acumula en segundos de juego internamente
        self.total_game_seconds = 6.0 * 3600.0 # El juego empezará a las 6:00 AM (Amanecer)
        
        # Variables calculadas para fácil acceso
        self.minute = 0
        self.hour = 6
        self.day = 1
        
        # Estados del día
        self.is_daytime = True

    def update(self, dt):
        """Avanza el reloj del juego basándose en el Delta Time real"""
        # Sumamos el tiempo real transcurrido multiplicado por nuestra escala de velocidad
        self.total_game_seconds += dt * self.time_scale
        
        # Calcular los valores actuales de forma limpia mediante divisiones
        total_minutes = int(self.total_game_seconds // 60)
        
        self.minute = total_minutes % 60
        self.hour = (total_minutes // 60) % 24
        self.day = (total_minutes // 1440) + 1 # 1440 minutos = 24 horas = 1 día
        
        # Determinar si es de día o de noche (ej: De noche entre las 20:00 y las 5:59)
        if self.hour >= 20 or self.hour < 6:
            if self.is_daytime:
                self.is_daytime = False
                print("Ha caído la noche sobre RushCraft...")
        else:
            if not self.is_daytime:
                self.is_daytime = True
                print("El sol está saliendo de nuevo...")

    def get_time_string(self):
        """Devuelve una cadena con formato bonito tipo reloj digital de 24h"""
        return f"Día {self.day} - {self.hour:02d}:{self.minute:02d} [{'DÍA' if self.is_daytime else 'NOCHE'}]"