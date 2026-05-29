import json
import os

class DataManager:
    def __init__(self, data_path="data"):
        self.data_path = data_path

        # Cargamos los archivos fundamentales
        self.entities = self.load("entities.json")
        self.spawn_rules = self.load("spawn_rules.json")
        self.resources = self.load("resources.json")
        self.biomes = self.load("biomes.json")

        # Cargamos la nueva base de datos de ítems
        self.items_db = self.load("items_db.json")
        self.item_defs = self.load("item_definitions.json")
        self.materials = self.load("materials_db.json")

    def load(self, filename):
        file_path = os.path.join(self.data_path, filename)
        if not os.path.exists(file_path):
            print(f"Error: No se encontró el archivo {file_path}")
            return {}
        with open(file_path, "r") as f:
            return json.load(f)

    def get_item_properties(self, item_id, target_type="enemy"):
        """
        Motor central unificado. Calcula propiedades para herramientas (con daño según objetivo)
        y para consumibles (con sus efectos).
        """
        # 1. Buscamos el ítem
        item = self.items_db.get(item_id)
        if not item:
            return self.item_defs.get("hand_base", {"type": "tool", "base_damage": 2}).copy()

        # 2. Obtenemos propiedades base
        props = self.item_defs.get(item["base_id"], {}).copy()

        # 3. Lógica para Herramientas (incluye cálculo de daño dinámico)
        if props.get("type") == "tool":
            # Modificador de material
            mat_mod = self.materials.get(item["material"], {}).get("dmg_mod", 1.0)
            
            # Modificador de efectividad (usamos get con 1.0 por defecto si no está definido)
            eff_mod = props.get("effectiveness", {}).get(target_type, 1.0)
            
            # Aplicar cálculo: Base * Material * Eficacia
            props["base_damage"] = int(props["base_damage"] * mat_mod * eff_mod)
        
        # 4. Lógica para Consumibles
        elif props.get("type") == "consumable":
            props["hunger"] = item.get("hunger", 0)
            props["heal"] = item.get("heal", 0)
            props["message"] = item.get("message", "Has consumido un ítem.")

        return props

    def get_resource(self, res_name):
        return self.resources.get("resources", {}).get(res_name)