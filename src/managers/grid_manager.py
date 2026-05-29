class GridManager:
    def __init__(self, cell_size=640):
        self.cell_size = cell_size
        self.grid = {}

    def get_grid_coords(self, world_pos):
        """Convierte una coordenada del mundo a coordenadas de cuadrícula"""
        grid_x = int(world_pos[0] // self.cell_size)
        grid_y = int(world_pos[1] // self.cell_size)
        return (grid_x, grid_y)

    def add_resource(self, resource):
        """Registra un recurso en el cuadrante correspondiente"""
        coords = self.get_grid_coords(resource.rect.center)
        if coords not in self.grid:
            self.grid[coords] = {"resources": [], "decorations": []}
        self.grid[coords]["resources"].append(resource)

    def get_resources_in_chunk(self, grid_coords):
        """Devuelve los recursos de un cuadrante específico"""
        return self.grid.get(grid_coords, {}).get("resources", [])