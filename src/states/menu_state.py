import pygame
from src.states.base_state import BaseState
 
 
class MenuState(BaseState):
    """
    Menu principal con:
    - Titulo y opcion de inicio
    - Seccion de teclas debug visible
    - Solo fuentes del sistema (sin caracteres especiales)
    """
 
    # Teclas debug — lista de (tecla, descripcion) en ASCII puro
    DEBUG_KEYS = [
        ("F1", "Toggle tiempo rapido / normal"),
        ("F2", "Spawnear mob del bioma actual"),
        ("F3", "Toggle grid de chunks y tiles"),
        ("F4", "Inyectar recursos de prueba"),
        ("E",  "Abrir / cerrar mochila"),
        ("TAB","Abrir / cerrar crafteo"),
        ("R",  "Respawnear (si muerto)"),
        ("ESC","Volver al menu"),
    ]
 
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.title_font  = pygame.font.SysFont("Arial", 56, bold=True)
        self.header_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.key_font    = pygame.font.SysFont("Courier New", 16, bold=True)
        self.desc_font   = pygame.font.SysFont("Arial", 16)
 
        self.color_title  = (255, 215,   0)
        self.color_white  = (255, 255, 255)
        self.color_grey   = (180, 180, 180)
        self.color_key_bg = ( 40,  40,  55)
        self.color_key    = (120, 220, 120)
        self.color_bg     = ( 18,  18,  28)
        self.color_panel  = ( 28,  28,  42)
 
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.manager.change_state("world")
 
    def update(self, dt):
        pass
 
    def draw(self, surface):
        sw, sh = surface.get_width(), surface.get_height()
        surface.fill(self.color_bg)
 
        # ── Titulo ───────────────────────────────────────────────────
        title_surf = self.title_font.render("RUSHCRAFT", True, self.color_title)
        surface.blit(title_surf, title_surf.get_rect(center=(sw // 2, 70)))
 
        subtitle = self.desc_font.render("Supervivencia en mundo abierto procedural", True, self.color_grey)
        surface.blit(subtitle, subtitle.get_rect(center=(sw // 2, 115)))
 
        # ── Panel debug keys ─────────────────────────────────────────
        panel_w, panel_h = 420, 240
        panel_x = sw // 2 - panel_w // 2
        panel_y = 150
 
        panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel.fill((*self.color_panel, 220))
        surface.blit(panel, (panel_x, panel_y))
        pygame.draw.rect(surface, (60, 60, 90), (panel_x, panel_y, panel_w, panel_h), 2)
 
        header = self.header_font.render("[ TECLAS DE DEBUG ]", True, self.color_key)
        surface.blit(header, header.get_rect(center=(sw // 2, panel_y + 18)))
 
        pygame.draw.line(surface, (60, 60, 90),
                         (panel_x + 10, panel_y + 32),
                         (panel_x + panel_w - 10, panel_y + 32), 1)
 
        for i, (key, desc) in enumerate(self.DEBUG_KEYS):
            row_y = panel_y + 44 + i * 23
 
            # Fondo de la tecla
            key_surf = self.key_font.render(f" {key:<5}", True, self.color_key)
            key_bg   = pygame.Rect(panel_x + 12, row_y - 1, 54, 18)
            pygame.draw.rect(surface, (50, 60, 50), key_bg, border_radius=3)
            surface.blit(key_surf, (panel_x + 14, row_y))
 
            desc_surf = self.desc_font.render(desc, True, self.color_white)
            surface.blit(desc_surf, (panel_x + 76, row_y + 1))
 
        # ── Prompt inicio ────────────────────────────────────────────
        prompt = self.header_font.render("[ ENTER ] para comenzar", True, self.color_white)
        surface.blit(prompt, prompt.get_rect(center=(sw // 2, panel_y + panel_h + 35)))
 
        version = self.desc_font.render("branch: feature/procedural-world-gen", True, (80, 80, 100))
        surface.blit(version, version.get_rect(center=(sw // 2, sh - 18)))