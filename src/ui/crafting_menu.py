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

    def toggle(self):
        """Abre o cierra el menú"""
        self.is_open = not self.is_open
        print(f"Menú de Crafteo: {'ABIERTO' if self.is_open else 'CERRADO'}")

    def handle_click(self, mouse_pos, inventory):
        """Detecta si el jugador hizo clic en alguna receta para fabricarla"""
        if not self.is_open:
            return

        for recipe_id, button_rect in self.recipe_buttons.items():
            if button_rect.collidepoint(mouse_pos):
                # Intentar craftear usando nuestro RecipeManager
                self.recipe_manager.check_and_craft(recipe_id, inventory)
                break

    def draw(self, surface):
        """Dibuja el panel visual y las opciones de crafteo"""
        if not self.is_open:
            return

        # 1. Dibujar el fondo del panel (Gris oscuro con borde blanco)
        pygame.draw.rect(surface, (40, 40, 40), self.rect)
        pygame.draw.rect(surface, (200, 200, 200), self.rect, 3)

        # 2. Título del menú
        title_surface = self.title_font.render("FABRICACIÓN", True, (255, 255, 255))
        surface.blit(title_surface, (self.rect.x + 20, self.rect.y + 15))

        # Limpiar los botones anteriores para recalcular posiciones
        self.recipe_buttons.clear()

        # 3. Listar las recetas verticalmente
        start_y = self.rect.y + 60
        
        for recipe_id, data in self.recipe_manager.recipes.items():
            # Crear un rectángulo para la fila/botón de esta receta
            button_rect = pygame.Rect(self.rect.x + 20, start_y, self.width - 40, 45)
            self.recipe_buttons[recipe_id] = button_rect

            # Detectar si el ratón está encima del botón (Hover effect)
            mouse_pos = pygame.mouse.get_pos()
            bg_color = (60, 60, 60) if button_rect.collidepoint(mouse_pos) else (50, 50, 50)
            
            # Dibujar el botón de la receta
            pygame.draw.rect(surface, bg_color, button_rect)
            pygame.draw.rect(surface, (100, 100, 100), button_rect, 1)

            # Nombre de la receta
            name_text = self.text_font.render(data["name"], True, (255, 255, 255))
            surface.blit(name_text, (button_rect.x + 10, button_rect.y + 5))

            # Mostrar los ingredientes requeridos abajo del nombre
            ingredients_str = "Requiere: " + ", ".join([f"{qty} {item}" for item, qty in data["ingredients"].items()])
            ing_text = self.text_font.render(ingredients_str, True, (200, 150, 100))
            surface.blit(ing_text, (button_rect.x + 10, button_rect.y + 23))

            start_y += 55