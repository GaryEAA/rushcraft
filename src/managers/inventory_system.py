import pygame

class InventorySystem:
    def __init__(self, total_slots=36):
        """
        Gestiona la lógica abstracta de almacenamiento de ítems.
        Cada slot será un diccionario: {"item_id": str, "quantity": int} o None si está vacío.
        """
        # Forzamos a que el tamaño total físico en memoria sea siempre 36 
        # para evitar crashes si la clase Player lo instanció con un valor menor por defecto.
        self.total_slots = 36 
        self.backpack_level = 1 # Empezamos en Nivel 1 (Solo Hotbar visible en el mundo)
        # Inicializamos la lista completa con el espacio máximo físico
        self.slots = [None] * self.total_slots

    def get_allowed_slots(self):
        """Calcula cuántos slots totales están disponibles según el nivel de la mochila"""
        if self.backpack_level == 1:
            return 12  # Solo los 12 slots base de la Hotbar
        elif self.backpack_level == 2:
            return 24  # Hotbar (12) + 1 Hilera de mochila (12)
        else:
            return 36  # Hotbar (12) + 2 Hileras de mochila (24)
        
    def add_item(self, item_id, quantity=1, max_stack=99):
        """
        Intenta añadir un ítem al inventario gestionando el stacking automático
        y respetando los límites de slots desbloqueados por la mochila.
        """
        # Ahora limitamos la búsqueda de stacking únicamente a los slots permitidos
        allowed_slots = self.get_allowed_slots()
        
        # 1. PASO 1: Buscar si ya existe el ítem en algún slot permitido para acumularlo (Stacking)
        for i in range(allowed_slots):
            # Añadida validación de seguridad 'i < len(self.slots)' para blindar contra IndexErrors
            if i < len(self.slots) and self.slots[i] and self.slots[i]["item_id"] == item_id:
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
        for i in range(allowed_slots):
            # Añadida la misma validación de seguridad aquí para el llenado de slots vacíos
            if i < len(self.slots) and self.slots[i] is None:
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
        if 0 <= slot_index < self.get_allowed_slots() and self.slots[slot_index]:
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

    def draw_hotbar(self, surface, active_index):
        """Dibuja únicamente la barra inferior de 12 slots en el mundo abierto"""
        # 1. Configuración de dimensiones
        slot_size = 48
        padding = 8
        # Forzamos a que la barra mida siempre 12 ranuras para mantenerla centrada y limpia
        hotbar_slots = 12
        total_width = (slot_size * hotbar_slots) + (padding * (hotbar_slots - 1))
        
        # Posición inicial X (centrada) e Y (cerca del borde inferior)
        start_x = (surface.get_width() - total_width) // 2
        start_y = surface.get_height() - slot_size - 20
        
        # Fuente para las cantidades
        font = pygame.font.SysFont("Arial", 14, bold=True)
        
        # 2. Recorremos estrictamente del slot 0 al 11
        for i in range(hotbar_slots):
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

            # Si este slot es el seleccionado por el jugador, dibujar un borde dorado/blanco grueso
            if i == active_index:
                # Dibujamos un rectángulo ligeramente más grande o un borde resaltado alrededor
                pygame.draw.rect(surface, (255, 255, 255), slot_rect, 3) # Borde blanco de 3px de grosor

    def get_total_quantity(self, item_id):
        """Devuelve la cantidad total acumulada de un ítem en los slots permitidos"""
        total = 0
        # Evita buscar ingredientes en slots bloqueados
        for i in range(self.get_allowed_slots()):
            if self.slots[i] and self.slots[i]["item_id"] == item_id:
                total += self.slots[i]["quantity"]
        return total

    def remove_item_amount(self, item_id, amount_to_remove):
        """Busca y elimina una cantidad de un ítem a través de los slots permitidos"""
        # Consume materiales únicamente de los espacios accesibles
        for i in range(self.get_allowed_slots()):
            if self.slots[i] and self.slots[i]["item_id"] == item_id:
                if self.slots[i]["quantity"] > amount_to_remove:
                    self.slots[i]["quantity"] -= amount_to_remove
                    return
                else:
                    amount_to_remove -= self.slots[i]["quantity"]
                    self.slots[i] = None
                    
            if amount_to_remove <= 0:
                break

    def clear(self):
        """Vuelve a llenar la lista de slots con None, vaciando el inventario"""
        self.slots = [None] * self.total_slots
        print("Inventario: Todos los slots han sido vaciados.")