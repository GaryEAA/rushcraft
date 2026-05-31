class GameClock:
    """
    Reloj del juego. Un día real = 24 minutos reales con time_scale=60.
    Soporta aceleración de tiempo para debug (toggle externo).
    """
 
    TIME_SCALE_NORMAL = 60.0    # 1 seg real = 1 min juego  → día de 24 min reales
    TIME_SCALE_FAST   = 300.0   # 1 seg real = 5 min juego  → día de ~5 min reales (debug)
 
    def __init__(self):
        self.time_scale = self.TIME_SCALE_NORMAL
        self._debug_fast = False
 
        # El juego empieza a las 6:00 AM
        self.total_game_seconds = 6.0 * 3600.0
 
        self.minute    = 0
        self.hour      = 6
        self.day       = 1
        self.is_daytime = True
 
    # ──────────────────────────────────────────────────
    #  Debug: toggle tiempo rápido
    # ──────────────────────────────────────────────────
 
    def toggle_fast_time(self):
        self._debug_fast = not self._debug_fast
        self.time_scale  = self.TIME_SCALE_FAST if self._debug_fast else self.TIME_SCALE_NORMAL
        mode = "RÁPIDO" if self._debug_fast else "NORMAL"
        print(f"[DEBUG] Tiempo en modo {mode} (scale={self.time_scale})")
        return self._debug_fast
 
    # ──────────────────────────────────────────────────
    #  Update
    # ──────────────────────────────────────────────────
 
    def update(self, dt):
        self.total_game_seconds += dt * self.time_scale
 
        total_minutes = int(self.total_game_seconds // 60)
 
        self.minute = total_minutes % 60
        self.hour   = (total_minutes // 60) % 24
        self.day    = (total_minutes // 1440) + 1
 
        if self.hour >= 18 or self.hour < 6:
            if self.is_daytime:
                self.is_daytime = False
                print("Ha caído la noche sobre RushCraft... Mobs activados.")
        else:
            if not self.is_daytime:
                self.is_daytime = True
                print("El sol está saliendo de nuevo... Mobs disolviéndose.")
 
    # ──────────────────────────────────────────────────
    #  Helpers
    # ──────────────────────────────────────────────────
 
    def get_current_phase_data(self):
        if 6 <= self.hour < 12:
            return "Día",        (255, 255, 255)
        elif 12 <= self.hour < 18:
            return "Tarde",      (255, 200, 100)
        elif 18 <= self.hour < 24:
            return "Noche",      (180, 180, 255)
        else:
            return "Madrugada",  (130, 130, 200)
 
    def get_time_string(self):
        fast_tag = " [FAST]" if self._debug_fast else ""
        return f"Día {self.day} - {self.hour:02d}:{self.minute:02d}{fast_tag}"