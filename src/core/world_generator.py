import math
import random as _rnd
from src.entities.resources import Resource
 
 
# ══════════════════════════════════════════════════════
#  Perlin Noise 2D  (implementación propia, sin librerías)
# ══════════════════════════════════════════════════════
 
class PerlinNoise:
    """
    Perlin Noise 2D clásico basado en tabla de permutaciones.
    Produce valores en [-1, 1].
    """
 
    def __init__(self, seed: int):
        rng = _rnd.Random(seed)
        perm = list(range(256))
        rng.shuffle(perm)
        self._p = perm * 2                  # duplicamos para evitar módulo
 
    # Gradientes en 2D
    _GRAD = [(1, 1), (-1, 1), (1, -1), (-1, -1),
             (1, 0), (-1, 0), (0, 1),  (0, -1)]
 
    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)
 
    @staticmethod
    def _lerp(a, b, t):
        return a + t * (b - a)
 
    def _grad(self, h, x, y):
        gx, gy = self._GRAD[h & 7]
        return gx * x + gy * y
 
    def noise(self, x: float, y: float) -> float:
        xi, yi = int(math.floor(x)) & 255, int(math.floor(y)) & 255
        xf, yf = x - math.floor(x), y - math.floor(y)
        u, v   = self._fade(xf), self._fade(yf)
 
        p = self._p
        aa = p[p[xi    ] + yi    ]
        ab = p[p[xi    ] + yi + 1]
        ba = p[p[xi + 1] + yi    ]
        bb = p[p[xi + 1] + yi + 1]
 
        return self._lerp(
            self._lerp(self._grad(aa, xf,     yf    ),
                       self._grad(ba, xf - 1, yf    ), u),
            self._lerp(self._grad(ab, xf,     yf - 1),
                       self._grad(bb, xf - 1, yf - 1), u),
            v
        )
 
    def octaves(self, x: float, y: float, octs: int = 4,
                persistence: float = 0.5, lacunarity: float = 2.0) -> float:
        """Suma varias octavas de ruido para más detalle natural."""
        val, amp, freq, max_val = 0.0, 1.0, 1.0, 0.0
        for _ in range(octs):
            val     += self.noise(x * freq, y * freq) * amp
            max_val += amp
            amp     *= persistence
            freq    *= lacunarity
        return val / max_val   # normalizado a [-1, 1]
 
 
# ══════════════════════════════════════════════════════
#  RNG aislado por chunk
# ══════════════════════════════════════════════════════
 
class SeededRNG:
    def __init__(self, seed: int):
        self._base = seed
 
    def for_chunk(self, cx: int, cy: int) -> _rnd.Random:
        rng = _rnd.Random()
        pair = ((cx + cy) * (cx + cy + 1) // 2) + cy
        rng.seed(self._base ^ (pair & 0xFFFFFFFF))
        return rng
 
    def for_tile(self, cx: int, cy: int, tx: int, ty: int) -> _rnd.Random:
        rng = _rnd.Random()
        combined = (cx * 1000003) ^ (cy * 999983) ^ (tx * 1009) ^ ty
        rng.seed(self._base ^ (combined & 0xFFFFFFFF))
        return rng
 
 
# ══════════════════════════════════════════════════════
#  WorldGenerator
# ══════════════════════════════════════════════════════
 
class WorldGenerator:
    """
    Genera el mundo dividido en Chunks → Tiles.
 
    Estructura espacial:
      mundo  →  chunks (coordenadas enteras, infinitas)
             →  cada chunk tiene TILES_PER_CHUNK × TILES_PER_CHUNK tiles
             →  cada tile tiene TILE_SIZE × TILE_SIZE píxeles
             →  chunk_pixel_size = TILES_PER_CHUNK × TILE_SIZE
                                 = 16 × 32 = 512 px  (coincide con cell_size del GridManager)
    """
 
    TILES_PER_CHUNK = 16    # 16×16 tiles por chunk (como Minecraft)
    TILE_SIZE       = 32    # píxeles por tile
 
    # Escala del ruido: valores pequeños → transiciones suaves entre biomas
    _BIOME_SCALE        = 0.07   # temperatura / humedad general
    _BIOME_DETAIL_SCALE = 0.20   # detalle fino del borde
 
    def __init__(self, seed, grid_manager, biomes_data, resources_data):
        self.seed             = seed
        self.grid_manager     = grid_manager
        self.biomes_config    = biomes_data.get("biomes", {})
        self.resources_config = resources_data.get("resources", {})
        self.rng              = SeededRNG(seed)
        self._data_manager    = None
 
    def register_data(self, data_manager):
        """Llamado desde world_state para pasar el DataManager a los recursos."""
        self._data_manager = data_manager
 
        # Dos capas de ruido independientes = mapa 2D de biomas
        self._noise_temp = PerlinNoise(self.seed ^ 0xDEADBEEF)   # temperatura
        self._noise_hum  = PerlinNoise(self.seed ^ 0xCAFEBABE)   # humedad
        self._noise_elev = PerlinNoise(self.seed ^ 0xABADCAFE)   # elevación (montaña)
 
    # ──────────────────────────────────────────────────
    #  Bioma natural por ruido
    # ──────────────────────────────────────────────────
 
    def get_biome(self, chunk_x: int, chunk_y: int) -> str:
        """
        Clasifica el bioma usando tres capas de Perlin noise.
 
        Ejes conceptuales:
          temperatura  alta  + humedad baja  → desierto
          temperatura  alta  + humedad alta  → pantano / swamp
          temperatura  baja  + humedad alta  → nieve / tundra
          temperatura  media + humedad media → bosque (default)
          elevación muy alta                 → montaña (bioma override)
        """
        x = chunk_x * self._BIOME_SCALE
        y = chunk_y * self._BIOME_SCALE
 
        temp = self._noise_temp.octaves(x, y, octs=4, persistence=0.5)
        hum  = self._noise_hum .octaves(x, y, octs=4, persistence=0.5)
        elev = self._noise_elev.octaves(
            chunk_x * self._BIOME_DETAIL_SCALE,
            chunk_y * self._BIOME_DETAIL_SCALE,
            octs=3, persistence=0.4
        )
 
        # Montaña: elevación extrema → override independiente de temp/hum
        if elev > 0.52:
            return "mountain"
 
        # Tabla de clasificación temperatura × humedad
        if temp > 0.15:                         # cálido
            return "desert" if hum < 0.0 else "swamp"
        elif temp < -0.15:                      # frío
            return "snow"
        else:                                   # templado
            return "forest"
 
    # ──────────────────────────────────────────────────
    #  Tile helpers
    # ──────────────────────────────────────────────────
 
    def tile_world_pos(self, chunk_x, chunk_y, tile_x, tile_y):
        """Devuelve la posición en píxeles (topleft) de un tile."""
        chunk_px = self.TILES_PER_CHUNK * self.TILE_SIZE
        wx = chunk_x * chunk_px + tile_x * self.TILE_SIZE
        wy = chunk_y * chunk_px + tile_y * self.TILE_SIZE
        return wx, wy
 
    # ──────────────────────────────────────────────────
    #  Selección ponderada de recurso
    # ──────────────────────────────────────────────────
 
    def _weighted_choice(self, rng, resource_list):
        total = sum(r["weight"] for r in resource_list)
        roll  = rng.uniform(0, total)
        cumul = 0
        for entry in resource_list:
            cumul += entry["weight"]
            if roll <= cumul:
                return entry["id"]
        return resource_list[-1]["id"]
 
    # ──────────────────────────────────────────────────
    #  Generación de chunk (tile por tile)
    # ──────────────────────────────────────────────────
 
    def generate_chunk(self, chunk_x, chunk_y, visible_group, resource_group=None):
        """
        Recorre las 16×16 celdas del chunk.
        Cada celda decide independientemente si genera un recurso
        basándose en la densidad del bioma → máximo 1 recurso por celda.
        """
        biome_id   = self.get_biome(chunk_x, chunk_y)
        biome_data = self.biomes_config.get(biome_id, {})
 
        resource_list = biome_data.get("resources", [])
        if not resource_list:
            return
 
        # tile_density: probabilidad [0-1] de que una celda tenga un recurso
        tile_density = biome_data.get("tile_density", 0.18)
        T = self.TILES_PER_CHUNK
        S = self.TILE_SIZE
 
        for ty in range(T):
            for tx in range(T):
                # RNG determinista e independiente por tile
                rng = self.rng.for_tile(chunk_x, chunk_y, tx, ty)
 
                # ¿Se genera algo en esta celda?
                if rng.random() > tile_density:
                    continue
 
                # Qué recurso
                item_id     = self._weighted_choice(rng, resource_list)
                item_config = self.resources_config.get(item_id)
                if not item_config:
                    print(f"[WorldGen] WARNING: '{item_id}' no existe en resources.json")
                    continue
 
                # Posición: el recurso se centra en la celda.
                # Su imagen tiene el tamaño exacto de su hitbox (config["hitbox"]),
                # así que lo alineamos topleft = centro_celda - mitad_hitbox.
                wx, wy = self.tile_world_pos(chunk_x, chunk_y, tx, ty)
                cell_cx = wx + S // 2   # centro X de la celda en píxeles
                cell_cy = wy + S // 2   # centro Y de la celda en píxeles
 
                hb = item_config.get("hitbox", [28, 28])
                hb_w, hb_h = max(4, hb[0]), max(4, hb[1])
 
                # topleft para que el sprite quede centrado en la celda
                fx = cell_cx - hb_w // 2
                fy = cell_cy - hb_h // 2
 
                res = Resource(fx, fy, item_id, item_config)
                res.register_grid(self.grid_manager)
                if hasattr(self, '_data_manager') and self._data_manager:
                    res.register_data(self._data_manager)
                visible_group.add(res)
                if resource_group is not None:
                    resource_group.add(res)
                self.grid_manager.add_resource(res)
 
    # ──────────────────────────────────────────────────
    #  Unload de chunk (gestión de memoria)
    # ──────────────────────────────────────────────────
 
    def unload_chunk(self, chunk_pos, visible_group, resource_group=None):
        resources_in_chunk = self.grid_manager.get_resources_in_chunk(chunk_pos)
        for res in list(resources_in_chunk):
            res.kill()
            if resource_group:
                resource_group.remove(res)
        self.grid_manager.mark_unloaded(chunk_pos)
 