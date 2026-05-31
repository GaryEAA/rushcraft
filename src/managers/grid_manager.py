class GridManager:
    """
    Gestiona la cuadrícula del mundo dividido en chunks.
    Cada chunk es una celda cuadrada de `cell_size` píxeles.
    Registra qué recursos viven en cada chunk y cuáles están activos.
    """
 
    UNLOAD_RADIUS = 4   # Chunks fuera de este radio se descargan
    LOAD_RADIUS   = 2   # Chunks dentro de este radio se generan
 
    def __init__(self, cell_size=512):
        self.cell_size = cell_size
 
        # Datos permanentes del chunk (nunca se borran; son el "mundo guardado")
        # { (cx, cy): {"resources": [sprite, ...], "decorations": [...]} }
        self.grid = {}
 
        # Set de chunks actualmente cargados (sprites vivos en memoria)
        self.loaded_chunks = set()
 
    # ─────────────────────────────────────────────────
    #  Conversiones de coordenadas
    # ─────────────────────────────────────────────────
 
    def get_chunk_coords(self, world_pos):
        """Convierte una posición del mundo (px) a coordenadas de chunk."""
        cx = int(world_pos[0] // self.cell_size)
        cy = int(world_pos[1] // self.cell_size)
        return (cx, cy)
 
    # Alias para compatibilidad con código existente
    def get_grid_coords(self, world_pos):
        return self.get_chunk_coords(world_pos)
 
    def chunk_to_world(self, chunk_coords):
        """Devuelve la esquina superior-izquierda de un chunk en píxeles."""
        return (chunk_coords[0] * self.cell_size,
                chunk_coords[1] * self.cell_size)
 
    def chunk_center_world(self, chunk_coords):
        """Devuelve el centro de un chunk en píxeles."""
        ox, oy = self.chunk_to_world(chunk_coords)
        half = self.cell_size // 2
        return (ox + half, oy + half)
 
    # ─────────────────────────────────────────────────
    #  Registro de recursos
    # ─────────────────────────────────────────────────
 
    def add_resource(self, resource):
        """Registra un sprite de recurso en su chunk correspondiente."""
        coords = self.get_chunk_coords(resource.rect.center)
        if coords not in self.grid:
            self.grid[coords] = {"resources": [], "decorations": []}
        self.grid[coords]["resources"].append(resource)
 
    def remove_resource(self, resource):
        """Elimina un recurso del registro del chunk (cuando es destruido)."""
        coords = self.get_chunk_coords(resource.rect.center)
        chunk_data = self.grid.get(coords)
        if chunk_data and resource in chunk_data["resources"]:
            chunk_data["resources"].remove(resource)
 
    def get_resources_in_chunk(self, chunk_coords):
        """Devuelve la lista de sprites de un chunk específico."""
        return self.grid.get(chunk_coords, {}).get("resources", [])
 
    def get_resources_near(self, world_pos, radius_chunks=1):
        """
        Devuelve todos los recursos en un radio de chunks alrededor de una posición.
        Útil para colisiones: solo revisa chunks cercanos al jugador.
        """
        cx, cy = self.get_chunk_coords(world_pos)
        result = []
        for dx in range(-radius_chunks, radius_chunks + 1):
            for dy in range(-radius_chunks, radius_chunks + 1):
                result.extend(self.get_resources_in_chunk((cx + dx, cy + dy)))
        return result
 
    # ─────────────────────────────────────────────────
    #  Chunk Loading / Unloading
    # ─────────────────────────────────────────────────
 
    def get_chunks_to_load(self, player_chunk):
        """
        Devuelve los chunks dentro del LOAD_RADIUS que aún no están cargados.
        """
        cx, cy = player_chunk
        to_load = []
        for dx in range(-self.LOAD_RADIUS, self.LOAD_RADIUS + 1):
            for dy in range(-self.LOAD_RADIUS, self.LOAD_RADIUS + 1):
                pos = (cx + dx, cy + dy)
                if pos not in self.loaded_chunks:
                    to_load.append(pos)
        return to_load
 
    def get_chunks_to_unload(self, player_chunk):
        """
        Devuelve los chunks cargados que están fuera del UNLOAD_RADIUS.
        """
        cx, cy = player_chunk
        to_unload = []
        for chunk_pos in list(self.loaded_chunks):
            dist_x = abs(chunk_pos[0] - cx)
            dist_y = abs(chunk_pos[1] - cy)
            if dist_x > self.UNLOAD_RADIUS or dist_y > self.UNLOAD_RADIUS:
                to_unload.append(chunk_pos)
        return to_unload
 
    def mark_loaded(self, chunk_pos):
        self.loaded_chunks.add(chunk_pos)
 
    def mark_unloaded(self, chunk_pos):
        self.loaded_chunks.discard(chunk_pos)
 
    def is_loaded(self, chunk_pos):
        return chunk_pos in self.loaded_chunks
 
    # ─────────────────────────────────────────────────
    #  Debug
    # ─────────────────────────────────────────────────
 
    def get_stats(self):
        total = sum(len(v["resources"]) for v in self.grid.values())
        return {
            "chunks_registrados": len(self.grid),
            "chunks_cargados":    len(self.loaded_chunks),
            "recursos_totales":   total,
        }