import json
import os

class DataManager:
    def __init__(self, data_path="data"):
        self.data_path = data_path
        # Aquí cargamos todos tus archivos JSON de golpe
        self.entities = self.load("entities.json")
        self.items = self.load("items.json")
        self.resources = self.load("resources.json")
        self.biomes = self.load("biomes.json")

    def load(self, filename):
        file_path = os.path.join(self.data_path, filename)
        if not os.path.exists(file_path):
            print(f"Error: No se encontró el archivo {file_path}")
            return {}
        with open(file_path, "r") as f:
            return json.load(f)

    # Métodos de acceso rápido para leer datos específicos
    def get_resource(self, res_name):
        return self.resources.get("resources", {}).get(res_name)

    def get_tool_damage(self, tool_name, target_type):
        tool = self.items.get("tools", {}).get(tool_name)
        if tool:
            return tool.get("base_damage", {}).get(target_type, 1)
        return 1