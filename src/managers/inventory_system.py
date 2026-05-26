import pygame

class InventorySystem:
    def __init__(self, total_slots=8):
        """
        Gestiona la lógica abstracta de almacenamiento de ítems.
        Cada slot será un diccionario: {"item_id": str, "quantity": int} o None si está vacío.
        """
        self.total_slots = total_slots
        self.slots = [None] * self.total_slots

    def add_item(self, item_id, quantity=1, max_stack=64):
        """
        Intenta añadir un ítem al inventario gestionando el stacking automático.
        Retorna True si se pudo añadir todo, o False si el inventario está lleno.
        """
        # 1. PASO 1: Buscar si ya existe el ítem en algún slot para acumularlo (Stacking)
        for i in range(self.total_slots):
            if self.slots[i] and self.slots[i]["item_id"] == item_id:
                # Comprobar si el slot aún tiene espacio antes de llegar al límite
                current_qty = self.slots[i]["quantity"]
                if current_qty < max_stack:
                    # Calcular cuánto espacio queda en este slot
                    available_space = max_stack - current_qty
                    amount_to_add = min(quantity, available_space)
                    
                    self.slots[i]["quantity"] += amount_to_add
                    quantity -= amount_to_add
                    
                    print(f"Inventario: Acumulado {amount_to_add} de '{item_id}' en slot {i}. Restan: {quantity}")
                    
                    if quantity == 0:
                        return True

        # 2. PASO 2: Si aún queda cantidad por añadir, buscar el primer slot completamente vacío
        for i in range(self.total_slots):
            if self.slots[i] is None:
                amount_to_add = min(quantity, max_stack)
                self.slots[i] = {"item_id": item_id, "quantity": amount_to_add}
                quantity -= amount_to_add
                
                print(f"Inventario: Asignado nuevo slot {i} para {amount_to_add} de '{item_id}'. Restan: {quantity}")
                
                if quantity == 0:
                    return True

        # Si salimos del bucle y todavía queda cantidad, significa que el inventario se llenó
        if quantity > 0:
            print(f"Inventario LLENO: No se pudieron guardar {quantity} unidades de '{item_id}'")
            return False
        return True

    def remove_item(self, slot_index, quantity=1):
        """Elimina una cantidad específica de un slot determinado"""
        if 0 <= slot_index < self.total_slots and self.slots[slot_index]:
            if self.slots[slot_index]["quantity"] >= quantity:
                self.slots[slot_index]["quantity"] -= quantity
                # Si el slot se queda en 0, lo vaciamos por completo
                if self.slots[slot_index]["quantity"] <= 0:
                    self.slots[slot_index] = None
                return True
        return False

    def debug_display(self):
        """Imprime de forma visual el contenido actual en la consola para desarrollo"""
        print("\n--- CONTENIDO DEL INVENTARIO ---")
        for i, slot in enumerate(self.slots):
            if slot:
                print(f"Slot {i}: [{slot['item_id']}] x{slot['quantity']}")
            else:
                print(f"Slot {i}: [ VACÍO ]")
        print("--------------------------------\n")

    def draw_hotbar(self, surface):
        """Dibuja la barra de inventario visual en la parte inferior de la pantalla"""
        # 1. Configuración de dimensiones
        slot_size = 48
        padding = 8
        # Calcular el ancho total de la hotbar para poder centrarla horizontalmente
        total_width = (slot_size * self.total_slots) + (padding * (self.total_slots - 1))
        
        # Posición inicial X (centrada) e Y (cerca del borde inferior)
        start_x = (surface.get_width() - total_width) // 2
        start_y = surface.get_height() - slot_size - 20
        
        # Fuente para las cantidades
        font = pygame.font.SysFont("Arial", 14, bold=True)
        
        # 2. Dibujar slot por slot
        for i in range(self.total_slots):
            slot_x = start_x + i * (slot_size + padding)
            slot_rect = pygame.Rect(slot_x, start_y, slot_size, slot_size)
            
            # Dibujar el fondo del slot (Gris oscuro con borde gris claro)
            pygame.draw.rect(surface, (40, 40, 40), slot_rect)
            pygame.draw.rect(surface, (100, 100, 100), slot_rect, 2) # Borde de 2 px
            
            # 3. Si el slot tiene un ítem, dibujar su información visual
            slot_data = self.slots[i]
            if slot_data:
                # TODO: (Provisional) Dibujar las iniciales del ítem en grande
                item_label = slot_data["item_id"][:2].upper()
                label_font = pygame.font.SysFont("Arial", 18, bold=True)
                label_text = label_font.render(item_label, True, (240, 240, 240))
                
                # Centrar las iniciales del texto dentro del slot
                text_x = slot_rect.x + (slot_size - label_text.get_width()) // 2
                text_y = slot_rect.y + (slot_size - label_text.get_height()) // 2
                surface.blit(label_text, (text_x, text_y))
                
                # Dibujar la cantidad en la esquina inferior derecha del slot
                qty_text = font.render(str(slot_data["quantity"]), True, (255, 215, 0)) # Dorado
                qty_x = slot_rect.right - qty_text.get_width() - 4
                qty_y = slot_rect.bottom - qty_text.get_height() - 4
                surface.blit(qty_text, (qty_x, qty_y))