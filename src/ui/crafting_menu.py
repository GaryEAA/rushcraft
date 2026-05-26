import pygame

class CraftingMenu:
    def __init__(self, recipe_manager, width=400, height=300):
        self.recipe_manager = recipe_manager
        self.is_open = False
        
        # Dimensiones y posición del panel central
        self.width = width
        self.height = height
        self.rect = pygame.Rect((800 - width) // 2, (600 - height) // 2, width, height)
        
        # Fuentes para los textos
        self.title_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 16)
        
        # Lista para guardar los rectángulos de los botones de cada receta
        self.recipe_buttons = {}

        # Variables de control para el scroll
        self.scroll_y = 0
        self.scroll_speed = 20
        self.max_scroll = 0  # Se calculará dinámicamente en el draw()

    def toggle(self):
        """Abre o cierra el menú"""
        self.is_open = not self.is_open
        if not self.is_open:
            self.scroll_y = 0 # Reiniciar scroll al cerrar
        print(f"Menú de Crafteo: {'ABIERTO' if self.is_open else 'CERRADO'}")

    # Escucha la rueda del ratón desde los eventos globales del juego
    def handle_scroll(self, event):
        """Procesa el evento de la rueda del mouse para desplazar el menú"""
        if not self.is_open:
            return

        # El evento de scroll tiene un atributo 'y' que indica la dirección del scroll
        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y += event.y * self.scroll_speed
            
            # Limitar el scroll para que no suba más allá del inicio (0)
            # y tampoco baje más del contenido máximo calculado
            if self.scroll_y > 0:
                self.scroll_y = 0
            if self.scroll_y < -self.max_scroll:
                self.scroll_y = -self.max_scroll

    def handle_click(self, mouse_pos, inventory):
        """Detecta si el jugador hizo clic en alguna receta para fabricarla"""
        if not self.is_open:
            return
        
        # Comprobar colisión en los botones virtuales que ya tienen el scroll aplicado
        for recipe_id, button_rect in self.recipe_buttons.items():
            if button_rect.collidepoint(mouse_pos):
                # Intentar craftear usando nuestro RecipeManager
                self.recipe_manager.check_and_craft(recipe_id, inventory)
                break

    def draw(self, surface):
        """Dibuja el panel visual y las opciones de crafteo con soporte de Scroll"""
        if not self.is_open:
            return

        # 1. Dibujar el fondo del panel (Gris oscuro con borde blanco)
        pygame.draw.rect(surface, (40, 40, 40), self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 3)

        # Limpiar los botones anteriores para recalcular posiciones con scroll
        self.recipe_buttons.clear()

        # 2. Crear una superficie interna (Canvas) dedicada solo a la lista de recetas
        # Esto sirve para aplicar un "Clip" y que las recetas no se dibujen fuera del recuadro gris.
        padding_top = 60
        padding_bottom = 20
        list_width = self.width - 40
        list_height = self.height - padding_top - padding_bottom
        
        # El área física real donde se permiten ver las recetas
        clip_rect = pygame.Rect(self.rect.x + 20, self.rect.y + padding_top, list_width, list_height)
        
        # Guardamos el clip original de la pantalla y aplicamos el nuevo
        old_clip = surface.get_clip()
        surface.set_clip(clip_rect)

        # 3. Listar las recetas aplicando el desplazamiento vertical (scroll_y)
        # Nota: start_y se calcula de manera relativa al clip_rect
        start_y = clip_rect.y + self.scroll_y
        spacing = 55
        
        for recipe_id, data in self.recipe_manager.recipes.items():
            # El rectángulo visual del botón se desplaza según self.scroll_y
            button_rect = pygame.Rect(clip_rect.x, start_y, list_width, 45)
            
            # Guardamos el rectángulo del botón para detectar clics precisos
            self.recipe_buttons[recipe_id] = button_rect

            # Detectar hover effect
            mouse_pos = pygame.mouse.get_pos()
            bg_color = (60, 60, 60) if button_rect.collidepoint(mouse_pos) else (50, 50, 50)
            
            # Dibujar el botón si queda dentro de la pantalla (optimización visual)
            pygame.draw.rect(surface, bg_color, button_rect)
            pygame.draw.rect(surface, (100, 100, 100), button_rect, 1)

            # Nombre de la receta
            name_text = self.text_font.render(data["name"], True, (255, 255, 255))
            surface.blit(name_text, (button_rect.x + 10, button_rect.y + 5))

            # Mostrar los ingredientes requeridos abajo del nombre
            ingredients_str = "Requiere: " + ", ".join([f"{qty} {item}" for item, qty in data["ingredients"].items()])
            ing_text = self.text_font.render(ingredients_str, True, (200, 150, 100))
            surface.blit(ing_text, (button_rect.x + 10, button_rect.y + 23))

            start_y += spacing

        # Restaurar el clip original para poder dibujar el título encima sin problemas
        surface.set_clip(old_clip)

        # 4. Calcular dinámicamente el scroll máximo permitido
        # Altura total que ocupa la lista completa en memoria
        total_content_height = len(self.recipe_manager.recipes) * spacing
        # Si el contenido es mayor al espacio visual, calculamos la diferencia máxima de scroll
        self.max_scroll = max(0, total_content_height - list_height)

        # 5. Título del menú (Se dibuja al final para que quede siempre por encima de las recetas escroleadas)
        # Tapamos el área superior del título con un rectángulo sólido para que las recetas scroleadas no pasen por detrás del texto
        header_rect = pygame.Rect(self.rect.x + 3, self.rect.y + 3, self.width - 6, padding_top - 5)
        pygame.draw.rect(surface, (40, 40, 40), header_rect)
        
        title_surface = self.title_font.render("FABRICACIÓN", True, (255, 255, 255))
        surface.blit(title_surface, (self.rect.x + 20, self.rect.y + 15))