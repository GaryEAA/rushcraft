import json
import os
 
class DataManager:
    def __init__(self, data_path="data"):
        self.data_path = data_path
 
        self.entities      = self.load("entities.json")
        self.spawn_rules   = self.load("spawn_rules.json")
        self.resources     = self.load("resources.json")
        self.biomes        = self.load("biomes.json")
        self.items_db      = self.load("items_db.json")
        self.item_defs     = self.load("item_definitions.json")
        self.materials     = self.load("materials_db.json")
 
        self._items_flat = {}
        for category_items in self.items_db.values():
            if isinstance(category_items, dict):
                for item_id, item_data in category_items.items():
                    self._items_flat[item_id] = item_data
 
    def load(self, filename):
        file_path = os.path.join(self.data_path, filename)
        if not os.path.exists(file_path):
            print(f"[DataManager] ERROR: No se encontró {file_path}")
            return {}
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
 
    def get_item(self, item_id):
        """Devuelve los datos crudos de un ítem buscando en todas las categorías."""
        return self._items_flat.get(item_id)
 
    def get_item_properties(self, item_id, target_type="enemy"):
        """
        Motor central. Calcula propiedades finales de herramientas (daño dinámico)
        y consumibles (efectos de hambre/curación).
        """
        item = self._items_flat.get(item_id)
 
        # Mano vacía como fallback
        if not item:
            props = self.item_defs.get("hand_base", {"type": "tool", "base_damage": 2}).copy()
            eff = props.get("effectiveness", {}).get(target_type, 1.0)
            props["base_damage"] = int(props["base_damage"] * eff)
            return props
 
        # Detectar comida por sus campos antes de buscar base_id
        if "hunger" in item or "heal" in item:
            props = self.item_defs.get("food_base", {"type": "consumable"}).copy()
            props["type"]    = "consumable"
            props["hunger"]  = item.get("hunger", 0)
            props["heal"]    = item.get("heal", 0)
            props["message"] = item.get("message", "Has consumido un ítem.")
            return props
 
        base_id = item.get("base_id", "hand_base")
        props = self.item_defs.get(base_id, {}).copy()
 
        if props.get("type") == "tool":
            material_key = item.get("material", "none")
            mat_data = self.materials.get("materials", {}).get(material_key, {})
            mat_mod = mat_data.get("dmg_mod", 1.0)
 
            eff_mod = props.get("effectiveness", {}).get(target_type, 1.0)
            props["base_damage"] = max(1, int(props["base_damage"] * mat_mod * eff_mod))
 
            props["material_tier"] = mat_data.get("tier", 0)
 
        elif props.get("type") == "consumable":
            props["hunger"]  = item.get("hunger", 0)
            props["heal"]    = item.get("heal", 0)
            props["message"] = item.get("message", "Has consumido un ítem.")
 
        return props
 
    def get_item_name(self, item_id):
        """Devuelve el nombre display de un ítem, o el item_id si no se encuentra."""
        item = self._items_flat.get(item_id)
        if item:
            return item.get("name", item_id)
        return item_id
 
    def get_max_stack(self, item_id):
        """Devuelve el stack máximo de un ítem (default 64)."""
        item = self._items_flat.get(item_id)
        if item:
            return item.get("max_stack", 64)
        return 64
 
    def get_resource(self, res_name):
        """Acceso rápido a un recurso del mundo."""
        return self.resources.get("resources", {}).get(res_name)
 
    def can_harvest(self, item_id, resource_config):
        """
        Verifica si la herramienta equipada puede cosechar un recurso
        según el tier mínimo requerido.
        """
        min_tier = resource_config.get("min_tool_tier", 0)
        if min_tier == 0:
            return True
        props = self.get_item_properties(item_id)
        return props.get("material_tier", 0) >= min_tier