import random
from src.entities.resources import Resource

class WorldGenerator:
    def __init__(self, seed, grid_manager):
        self.seed = seed
        self.grid_manager = grid_manager
        random.seed(self.seed)

    def generate_chunk(self, chunk_x, chunk_y, sprite_group):
        """Genera recursos para un chunk específico usando la seed."""
        # Usamos la posición para que siempre sea igual
        random.seed(f"{self.seed}_{chunk_x}_{chunk_y}")
        
        # 1. Determinar el bioma del chunk
        bioma = "forest" if (chunk_x + chunk_y) % 2 == 0 else "mountain"
        
        # 2. Spawneo de recursos
        num_resources = random.randint(3, 8)

        print(f"DEBUG: Generando nuevo chunk en coordenadas: ({chunk_x}, {chunk_y})")
        for _ in range(num_resources):
            x = (chunk_x * self.grid_manager.cell_size) + random.randint(50, 590)
            y = (chunk_y * self.grid_manager.cell_size) + random.randint(50, 590)
            
            resource_type = "tree" if (chunk_x + chunk_y) % 2 == 0 else "iron_rock"
            
            res = Resource(x, y, resource_type, health=30, item_yield="wood")
            
            sprite_group.add(res) 
            self.grid_manager.add_resource(res)
