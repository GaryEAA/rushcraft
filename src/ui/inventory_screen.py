import pygame

class InventoryScreen:
    def __init__(self):
        self.is_open = False
        self.font = pygame.font.SysFont("Arial", 14)
        self.title_font = pygame.font.SysFont("Arial", 20, bold=True)
        self.debug_font = pygame.font.SysFont("Arial", 12, italic=True)
        
        # Dimensiones de la ventana del inventario completo
        self.width = 600
        self.height = 300
        self.rect = pygame.Rect((800 - self.width) // 2, (600 - self.height) // 2 - 40, self.width, self.height)

        # Configuración de la cuadrícula de slots
        self.slot_size = 40
        self.slot_margin = 6
        
        # Cálculo matemático para centrar perfectamente las 12 columnas
        grid_width = (12 * self.slot_size) + (11 * self.slot_margin)
        self.start_x = self.rect.x + (self.width - grid_width) // 2
        self.start_y = self.rect.y + 100

    def toggle(self):
        """Abre o cierra la pantalla de la mochila"""
        self.is_open = not self.is_open

    def draw(self, surface, inventory):
        if not self.is_open:
            return

        # 1. Dibujar el fondo de la mochila (Estilo panel de madera/cuero oscuro)
        pygame.draw.rect(surface, (30, 25, 20), self.rect)
        pygame.draw.rect(surface, (180, 130, 90), self.rect, 4) # Borde de cuero claro

        # 2. Título dinámico según el nivel
        level_names = {1: "Ninguna (Mochila Requerida)", 2: "Mochila de Montañero", 3: "Mochila de Expedición"}
        title_text = f"ALMACENAMIENTO: {level_names.get(inventory.backpack_level, 'Mochila')}"
        title_surface = self.title_font.render(title_text, True, (230, 200, 160))
        surface.blit(title_surface, (self.rect.x + 30, self.rect.y + 25))

        # Texto explicativo de cambio de nivel
        dev_text = self.font.render("[Debug: Presiona F1, F2 o F3 para alterar nivel de mochila]", True, (150, 150, 150))
        surface.blit(dev_text, (self.rect.x + 25, self.rect.y + 48))

        # Texto explicativo para recordar la inyección de recursos masivos
        inject_text = self.debug_font.render("[Debug: Presiona 'I' en el mundo para inyectar +200 recursos de prueba]", True, (140, 170, 140))
        surface.blit(inject_text, (self.rect.x + 25, self.rect.y + 68))

        # 3. Dibujar la matriz de 3 hileras x 12 columnas
        allowed_slots = inventory.get_allowed_slots()

        # Iteramos sobre 2 filas (24 slots de mochila). La fila 1 representa los slots 12-23, la fila 2 los slots 24-35.
        for row in range(2):
            for col in range(12):
                # El índice lógico arranca en 12 porque los primeros 12 pertenecen a la Hotbar externa.
                slot_index = 12 + (row * 12 + col)
                
                # Calcular la posición X, Y de este cuadradito en la pantalla
                x = self.start_x + col * (self.slot_size + self.slot_margin)
                y = self.start_y + row * (self.slot_size + self.slot_margin)
                slot_rect = pygame.Rect(x, y, self.slot_size, self.slot_size)

                # Verificación de si el slot actual está desbloqueado por el nivel de mochila de expansión
                if slot_index < allowed_slots and slot_index < len(inventory.slots):
                    # Slot DESBLOQUEADO
                    pygame.draw.rect(surface, (60, 55, 50), slot_rect)
                    pygame.draw.rect(surface, (120, 110, 100), slot_rect, 2)
                    
                    # Si el slot tiene un objeto, dibujarlo
                    item_data = inventory.slots[slot_index]
                    if item_data:
                        short_name = item_data["item_id"][:3].upper()
                        item_text = self.font.render(short_name, True, (255, 255, 255))
                        surface.blit(item_text, (x + 6, y + 6))
                        
                        if item_data["quantity"] > 1:
                            qty_text = self.font.render(str(item_data["quantity"]), True, (255, 200, 100))
                            surface.blit(qty_text, (x + 22, y + 22))
                else:
                    # Slot BLOQUEADO (Mochila no equipada o nivel insuficiente)
                    pygame.draw.rect(surface, (20, 20, 20), slot_rect)
                    pygame.draw.rect(surface, (40, 40, 40), slot_rect, 1)
                    # Dibujar la "X" decorativa de bloqueo
                    pygame.draw.line(surface, (100, 40, 40), (x+12, y+12), (x+28, y+28), 2)
                    pygame.draw.line(surface, (100, 40, 40), (x+28, y+12), (x+12, y+28), 2)