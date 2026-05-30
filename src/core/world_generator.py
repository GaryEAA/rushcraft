import random
import math
from src.entities.resources import Resource
 
class WorldGenerator:
    def __init__(self, seed, grid_manager, biomes_data, resources_data):
        self.seed = seed
        self.grid_manager = grid_manager
        self.biomes_config = biomes_data.get("biomes", {})
        self.resources_config = resources_data.get("resources", {})
        random.seed(self.seed)
 
    def _get_biome(self, chunk_x, chunk_y):
        """
        Determina el bioma de un chunk usando distancia y ángulo.
        - Centro (dist <= 3): Bosque
        - Lejos en diagonal NE: Desierto
        - Norte: Nieve
        - Sur: Pantano
        - Muy lejos (dist > 6): Montaña
        """
        dist = math.sqrt(chunk_x**2 + chunk_y**2)
 
        if dist > 6:
            return "mountain"
 
        if dist <= 2:
            return "forest"
 
        # Usamos el ángulo para separar biomas en anillo intermedio
        angle = math.degrees(math.atan2(chunk_y, chunk_x))  # -180 a 180
 
        if chunk_y < -1 and dist > 2:   # Norte (y negativo en pygame = arriba)
            return "snow"
        elif chunk_y > 1 and dist > 2:  # Sur
            return "swamp"
        elif chunk_x > 1 and dist > 2:  # Este
            return "desert"
        else:
            return "forest"
 
    def _weighted_choice(self, resource_list):
        """Elige un recurso de la lista usando pesos (weight)."""
        total = sum(r["weight"] for r in resource_list)
        roll = random.uniform(0, total)
        cumulative = 0
        for entry in resource_list:
            cumulative += entry["weight"]
            if roll <= cumulative:
                return entry["id"]
        return resource_list[-1]["id"]
 
    def generate_chunk(self, chunk_x, chunk_y, visible_group, resource_group=None):
        """Genera recursos para un chunk basándose en bioma, densidad y pesos."""
        random.seed(f"{self.seed}_{chunk_x}_{chunk_y}")
 
        biome_id = self._get_biome(chunk_x, chunk_y)
        biome_data = self.biomes_config.get(biome_id, {})
 
        resource_list = biome_data.get("resources", [])
        if not resource_list:
            return
 
        # Leer rango de clusters desde el JSON (con fallback seguro)
        c_min, c_max = biome_data.get("cluster_count", [1, 3])
        d_min, d_max = biome_data.get("cluster_density", [3, 7])
 
        cell_size = self.grid_manager.cell_size
        base_x = chunk_x * cell_size
        base_y = chunk_y * cell_size
 
        num_clusters = random.randint(c_min, c_max)
 
        for _ in range(num_clusters):
            # Centro del cluster dentro del chunk (margen de 60px)
            cx = random.randint(60, cell_size - 60)
            cy = random.randint(60, cell_size - 60)
 
            # Elegir tipo de recurso con pesos
            item_id = self._weighted_choice(resource_list)
            item_config = self.resources_config.get(item_id)
 
            if not item_config:
                print(f"[WorldGen] WARNING: '{item_id}' no existe en resources.json — se omite.")
                continue
 
            density = random.randint(d_min, d_max)
 
            for _ in range(density):
                # Dispersión gaussiana alrededor del centro del cluster
                spread = 50
                ox = random.normalvariate(0, spread)
                oy = random.normalvariate(0, spread)
 
                fx = base_x + cx + ox
                fy = base_y + cy + oy
 
                # Clamp dentro del chunk con margen
                fx = max(base_x + 10, min(fx, base_x + cell_size - 10))
                fy = max(base_y + 10, min(fy, base_y + cell_size - 10))
 
                res = Resource(fx, fy, item_id, item_config)
 
                visible_group.add(res)
                if resource_group is not None:
                    resource_group.add(res)
                self.grid_manager.add_resource(res)
 