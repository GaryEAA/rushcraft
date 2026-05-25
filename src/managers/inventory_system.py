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