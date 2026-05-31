import math
 
import pygame
import random
from src.core.world_generator import WorldGenerator
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.resources import Resource
from src.entities.enemy import Enemy
from src.core.camera import CameraGroup
from src.managers.game_clock import GameClock
from src.effects.night_filter import NightFilter
from src.effects.particle_manager import ParticleManager
from src.managers.recipe_manager import RecipeManager
from src.ui.crafting_menu import CraftingMenu
from src.ui.inventory_screen import InventoryScreen
from src.entities.resources import Resource, ItemDrop
from src.managers.grid_manager import GridManager
 
class WorldState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.color_grass = (34, 139, 34)
        self.grid_manager = GridManager(cell_size=512)  # 16 tiles × 32px por tile
        # Obtenemos los datos desde el DataManager ya inyectado
        data = self.manager.data_manager
        # Definimos posición inicial
        start_x = 600
        start_y = 500
        # 3. Extraemos las stats del JSON a través del DataManager
        player_stats = data.entities.get("player")
 
        # 4. Instanciamos el Player
        self.player = Player(start_x, start_y, player_stats, self.manager)
 
        # Grupos de render y colisión
        self.visible_sprites = CameraGroup()
        self.resource_sprites = pygame.sprite.Group() 
        
        # Grupo lógico exclusivo para gestionar enemigos separados de los recursos
        self.enemy_sprites = pygame.sprite.Group()
        
        # Añadir al jugador al render
        self.visible_sprites.add(self.player)
        
        # La generación de recursos la maneja update_chunks() con WorldGenerator
 
        # Instanciar sistemas secundarios
        self.clock = GameClock()
        self.night_filter = NightFilter(800, 600)
        self.drop_sprites = pygame.sprite.Group()
        self.particle_manager = ParticleManager(self.visible_sprites)
        self.recipe_manager = RecipeManager()
 
        # Menús e Interfaces
        self.crafting_menu = CraftingMenu(self.recipe_manager)
        self.inventory_screen = InventoryScreen()
 
        # Spawner tipo Minecraft: timers independientes de spawn y despawn
        self.spawn_timer   = 0.0
        self.despawn_timer = 0.0
        self.SPAWN_RADIUS   = 3   # radio en chunks para spawnear mobs
        self.DESPAWN_RADIUS = 5   # radio en chunks para eliminar mobs lejanos

        self.world_seed = 12345   # TODO: cargar desde save o input del jugador
        self.generated_chunks = set()
        self.show_debug_grid = False  # F3 toggle (desactivado por defecto)
        self.world_generator = WorldGenerator(
            seed           = self.world_seed,
            grid_manager   = self.grid_manager,
            biomes_data    = data.biomes,
            resources_data = data.resources
        )
        self.world_generator.register_data(data)

    # ─────────────────────────────────────────────────────────────────────
    #  SPAWN / DESPAWN  (sistema tipo Minecraft por chunks)
    # ─────────────────────────────────────────────────────────────────────

    def _biome_spawn_cfg(self, chunk):
        """Devuelve (mob_pool, spawn_cfg) del bioma de un chunk dado."""
        biomes_data = self.manager.data_manager.biomes.get("biomes", {})
        biome_id    = self.world_generator.get_biome(*chunk)
        biome       = biomes_data.get(biome_id, {})
        cfg         = biome.get("spawn_config", {"spawn_rate": 10, "max_mobs": 5, "night_only": True})
        return biome.get("enemies", []), cfg

    def manage_enemy_spawning(self, dt):
        """
        Sistema de spawn/despawn tipo Minecraft:
        - De día: incinera todos los enemigos progresivamente.
        - De noche: rellena cada chunk cargado dentro del radio de spawn
          con mobs del bioma correspondiente, hasta alcanzar la densidad
          definida en spawn_config. Despawnea los mobs que salgan del radio.
        """
        player_chunk         = self.grid_manager.get_chunk_coords(self.player.rect.center)
        _, cfg_player        = self._biome_spawn_cfg(player_chunk)
        night_only           = cfg_player.get("night_only", True)

        # ── DE DÍA: incinerar y salir ────────────────────────────────────
        if night_only and self.clock.is_daytime:
            self.spawn_timer = self.despawn_timer = 0.0
            for enemy in list(self.enemy_sprites):
                self.particle_manager.create_hit_particles(enemy.rect.center, "tree")
                if enemy.take_damage(15 * dt):
                    print("El sol ha incinerado a un enemigo.")
            return

        # ── DESPAWN: limpiar mobs fuera del radio (cada 2 s) ─────────────
        self.despawn_timer += dt
        if self.despawn_timer >= 2.0:
            self.despawn_timer = 0.0
            px, py = player_chunk
            for enemy in list(self.enemy_sprites):
                ex, ey = self.grid_manager.get_chunk_coords(enemy.rect.center)
                if abs(ex - px) > self.DESPAWN_RADIUS or abs(ey - py) > self.DESPAWN_RADIUS:
                    enemy.kill()

        # ── SPAWN: rellenar chunks cercanos ──────────────────────────────
        self.spawn_timer += dt
        if self.spawn_timer < cfg_player.get("spawn_rate", 10):
            return
        self.spawn_timer = 0.0

        px, py         = player_chunk
        enemies_config = self.manager.data_manager.entities.get("enemies", {})
        cell           = self.grid_manager.cell_size

        # Límite global: max_mobs × área del radio de spawn
        area          = (self.SPAWN_RADIUS * 2 + 1) ** 2
        max_per_chunk = max(1, cfg_player.get("max_mobs", 5) // max(self.SPAWN_RADIUS, 1))
        global_cap    = cfg_player.get("max_mobs", 5) * self.SPAWN_RADIUS

        if len(self.enemy_sprites) >= global_cap:
            return

        for dx in range(-self.SPAWN_RADIUS, self.SPAWN_RADIUS + 1):
            for dy in range(-self.SPAWN_RADIUS, self.SPAWN_RADIUS + 1):
                chunk = (px + dx, py + dy)

                # Solo en chunks ya generados, y nunca en el del jugador
                if chunk not in self.generated_chunks or chunk == player_chunk:
                    continue

                mob_pool, cfg = self._biome_spawn_cfg(chunk)
                if not mob_pool:
                    continue

                # Contar mobs ya presentes en este chunk
                cx, cy     = self.grid_manager.chunk_to_world(chunk)
                chunk_rect = pygame.Rect(cx, cy, cell, cell)
                mobs_here  = sum(1 for e in self.enemy_sprites
                                 if chunk_rect.collidepoint(e.rect.center))

                if mobs_here >= max_per_chunk:
                    continue

                # Spawnear uno en posición aleatoria dentro del chunk
                margin  = 32
                spawn_x = random.randint(cx + margin, cx + cell - margin)
                spawn_y = random.randint(cy + margin, cy + cell - margin)
                mob     = random.choice(mob_pool)
                stats   = enemies_config.get(mob)
                if not stats:
                    continue

                new_enemy = Enemy(spawn_x, spawn_y, mob, stats)
                self.visible_sprites.add(new_enemy)
                self.enemy_sprites.add(new_enemy)
                print(f"[Spawn] {new_enemy.name} en chunk {chunk}")

                if len(self.enemy_sprites) >= global_cap:
                    return

    def spawn_enemy(self, mob_type):
        """Spawn manual (F2 debug): posición aleatoria alrededor del jugador."""
        enemies_config = self.manager.data_manager.entities.get("enemies", {})
        stats = enemies_config.get(mob_type)
        if not stats:
            print(f"[Spawn] Sin config para '{mob_type}'")
            return
        angle    = random.uniform(0, 2 * math.pi)
        distance = random.randint(300, 500)
        spawn_x  = self.player.rect.centerx + int(math.cos(angle) * distance)
        spawn_y  = self.player.rect.centery + int(math.sin(angle) * distance)
        new_enemy = Enemy(spawn_x, spawn_y, mob_type, stats)
        self.visible_sprites.add(new_enemy)
        self.enemy_sprites.add(new_enemy)
        print(f"[Debug spawn] {new_enemy.name} en ({spawn_x}, {spawn_y})")
 
    def handle_events(self, events):
        for event in events:
            # 1. Manejo de eventos de teclado
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.change_state("menu")
                    
                # Tecla 'TAB' abre/cierra Crafteo (Solo si la mochila está cerrada)
                if event.key == pygame.K_TAB and not self.inventory_screen.is_open:
                    self.crafting_menu.toggle()
                    
                # Tecla 'E' abre/cierra Mochila (Solo si el crafteo está cerrado)
                if event.key == pygame.K_e and not self.crafting_menu.is_open:
                    self.inventory_screen.toggle()
 
                # ── DEBUG KEYS ───────────────────────────────────────
                # F1 → Toggle tiempo rapido / normal
                if event.key == pygame.K_F1:
                    fast = self.clock.toggle_fast_time()
                    print(f"[DEBUG] Tiempo {'RAPIDO' if fast else 'NORMAL'}")
 
                # F2 → Spawnear mob del bioma actual
                if event.key == pygame.K_F2:
                    biome_id  = self.world_generator.get_biome(
                        *self.grid_manager.get_chunk_coords(self.player.rect.center)
                    )
                    biome_data = self.world_generator.biomes_config.get(biome_id, {})
                    mob_pool   = biome_data.get("enemies", ["slime", "zombie"])
                    self.spawn_enemy(random.choice(mob_pool))
                    print(f"[DEBUG] Mob spawneado en bioma '{biome_id}'")
 
                # F3 → Toggle grid/chunks debug
                if event.key == pygame.K_F3:
                    self.show_debug_grid = not self.show_debug_grid
                    state = "ON" if self.show_debug_grid else "OFF"
                    print(f"[DEBUG] Grid debug {state}")
 
                # F4 → Inyectar recursos de prueba
                if event.key == pygame.K_F4:
                    self.player.inventory.add_item("wood", 50)
                    self.player.inventory.add_item("stone", 50)
                    self.player.inventory.add_item("coal", 30)
                    self.player.inventory.add_item("copper_ore", 20)
                    self.player.inventory.add_item("iron_ore", 10)
                    self.player.inventory.add_item("fiber", 20)
                    self.player.inventory.add_item("apple", 5)
                    self.player.inventory.add_item("cooked_meat", 5)
                    print("[DEBUG] Recursos inyectados.")
 
                # Modo Survival: El mundo se conserva, el jugador reaparece en un punto aleatorio seguro
                if event.key == pygame.K_r and self.player.is_dead:
                    # Forzamos un Spawn considerablemente más lejano (entre 300 y 450 px)
                    # Esto garantiza que la cámara se desplace y NO recojas los ítems por accidente
                    spawn_offset_x = random.choice([-1, 1]) * random.randint(300, 450)
                    spawn_offset_y = random.choice([-1, 1]) * random.randint(300, 450)
                    
                    spawn_x = 400 + spawn_offset_x
                    spawn_y = 300 + spawn_offset_y
                    
                    # Reiniciamos al jugador en la nueva posición aleatoria y lejana
                    self.player.reset(spawn_x, spawn_y)
                    
                    # Vaciamos SOLAMENTE los enemigos para quitar los que estaban sobre tu cuerpo
                    for enemy in self.enemy_sprites:
                        enemy.kill()
                            
                    print(f"¡Respawn exitoso en ({spawn_x}, {spawn_y})! Camina hacia las coordenadas de tu muerte para recuperar tus cosas.")
            
            # 2. Manejo de la rueda del ratón (Scroll)
            if event.type == pygame.MOUSEWHEEL:
                self.crafting_menu.handle_scroll(event)
 
            # 3. Detección de clics (UNIFICADA)
            if event.type == pygame.MOUSEBUTTONDOWN:
                # ==========================================
                # CLIC IZQUIERDO (Atacar / Romper)
                # ==========================================
                if event.button == 1:
                    # Si el jugador está muerto, ignoramos por completo cualquier clic en el mundo
                    if self.player.is_dead:
                        continue
 
                    # Prioridad 1: Si el menú de crafteo está abierto, procesamos sus botones
                    if self.crafting_menu.is_open:
                        self.crafting_menu.handle_click(event.pos, self.player.inventory)
                    
                    # Prioridad 2: Si los menús están cerrados, interactuamos con el mundo (recursos)
                    elif not self.inventory_screen.is_open: 
                        # Primero intentamos golpear a un enemigo. 
                        # Si no golpeamos a ninguno, entonces verificamos los recursos.
                        if not self.check_enemy_interaction(event.pos):
                            self.check_resource_interaction(event.pos)
 
                # ==========================================
                # CLIC DERECHO (Consumir / Usar comida)
                # ==========================================
                elif event.button == 3:
                    if self.player.is_dead:
                        continue
                    
                    if not self.crafting_menu.is_open and not self.inventory_screen.is_open:
                        active_slot = self.player.active_slot
                        inventory = self.player.inventory
                        slot_data = inventory.slots[active_slot]
                        
                        if slot_data:
                            item_id = slot_data["item_id"]
                            
                            # NUEVO CÓDIGO: Usamos el motor central del DataManager
                            # El Player ya tiene el método consume_item actualizado
                            if self.player.consume_item(item_id):
                                # Si lo ingiere con éxito, lo borramos
                                inventory.remove_item(active_slot, quantity=1)
 
    def check_resource_interaction(self, mouse_pos):
        """Verifica interacción con recursos considerando el offset de la cámara"""
        # 1. Recuperar la configuración (¡Esto faltaba!)
        player_config = self.manager.data_manager.entities.get("player", {})
        interaction_range = player_config.get("interaction_range", 80)
 
        # 2. Convertir coordenadas
        world_mouse_x = mouse_pos[0] + self.visible_sprites.offset.x
        world_mouse_y = mouse_pos[1] + self.visible_sprites.offset.y
        coords = self.grid_manager.get_grid_coords((world_mouse_x, world_mouse_y))
 
        # 3. Buscar solo en el cuadrante del mouse
        resources_to_check = self.grid_manager.get_resources_in_chunk(coords)
 
        for resource in resources_to_check:            
            if resource.rect.collidepoint((world_mouse_x, world_mouse_y)):
                player_center = pygame.math.Vector2(self.player.rect.center)
                resource_center = pygame.math.Vector2(resource.rect.center)
                distance = player_center.distance_to(resource_center)
                
                if distance <= interaction_range:
                    dynamic_damage = self.player.get_current_tool_damage(resource.type)
                    tool_tier = self.player.get_current_tool_tier()
                    print(f"Clic en '{resource.type}'. Daño: {dynamic_damage} | Tier herramienta: {tool_tier}")
 
                    self.particle_manager.create_hit_particles(resource.rect.center, resource.type)
                    resource.hit(
                        damage     = dynamic_damage,
                        drop_groups= [self.visible_sprites, self.drop_sprites],
                        tool_tier  = tool_tier
                    )
                    self.player.trigger_attack_animation()

                    # Daño de rebote: si el recurso pincha (ej: cactus),
                    # el jugador recibe contact_damage al atacarlo con la mano
                    if resource.contact_damage > 0:
                        if self.player.take_damage(resource.contact_damage):
                            self.particle_manager.create_hit_particles(
                                self.player.rect.center, "rock"
                            )
                            print(f"[{resource.type}] ¡Te has pinchado! -{resource.contact_damage} HP")
                    break
                
    def update(self, dt):
        # 1. Actualización de sistemas de tiempo y efectos
        self.clock.update(dt)
        self.night_filter.update(self.clock.hour, self.clock.minute)
        
        # 2. Gestor del ciclo y spawneo de enemigos
        self.manage_enemy_spawning(dt)
 
        # 3. Lógica de juego activa (Solo si no hay menús abiertos)
        if not self.crafting_menu.is_open and not self.inventory_screen.is_open:
            
            # --- FILTRADO DE OBSTÁCULOS (CAPAS DE COLISIÓN) ---
            solid_obstacles = [res for res in self.resource_sprites if res.is_solid]
            
            # Actualizamos jugador (mueve + resuelve colisiones sólidas)
            self.player.update(dt, solid_obstacles)

            # Daño por contacto con recursos peligrosos (ej: cactus).
            # Se evalúa DESPUÉS de player.update para usar la posición final,
            # pero con inflate(+4,+4) para compensar el pixel-push de la colisión sólida.
            if not self.player.is_dead:
                player_zone = self.player.hitbox.inflate(4, 4)
                for res in self.resource_sprites:
                    if res.contact_damage > 0 and player_zone.colliderect(res.hitbox):
                        if self.player.take_damage(res.contact_damage):
                            self.particle_manager.create_hit_particles(
                                self.player.rect.center, "rock"
                            )
                            print(f"[{res.type}] Daño por contacto: -{res.contact_damage} HP")
            
            # Actualizamos generación de chunks
            self.update_chunks()

            # Actualizamos enemigos pasando solo los sólidos
            for enemy in self.enemy_sprites:
                enemy.update(dt, solid_obstacles, self.player.rect)

            # 4. Colisiones Jugador-Enemigo
            collided_enemies = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False)
            for enemy in collided_enemies:
                if self.player.take_damage(enemy.damage):
                    self.particle_manager.create_hit_particles(self.player.rect.center, "rock")
                    
                    # Lógica de muerte: tirar inventario
                    if self.player.is_dead:
                        items_to_drop = self.player.drop_all_items()
                        for item in items_to_drop:
                            offset_x, offset_y = random.randint(-20, 20), random.randint(-20, 20)
                            drop_pos = (self.player.rect.centerx + offset_x, self.player.rect.centery + offset_y)
                            
                            ItemDrop(
                                drop_pos, 
                                [self.visible_sprites, self.drop_sprites], 
                                item["item_id"], 
                                item["amount"]
                            )
 
        # 5. Actualización de partículas y drops (fuera del 'if' para que se vean aunque el menú esté abierto)
        self.particle_manager.update(dt)
        
        # Lógica de recolección (Pickup)
        if not self.player.is_dead:
            collided_drops = pygame.sprite.spritecollide(self.player, self.drop_sprites, False)
            for drop in collided_drops:
                max_stack = self.manager.data_manager.get_max_stack(drop.item_id)
                if self.player.inventory.add_item(drop.item_id, drop.amount, max_stack=max_stack):
                    drop.kill()
                    print(f"Recogido: {drop.amount}x {drop.item_id}")
 
        self.drop_sprites.update(dt)
 
    def update_chunks(self):
        player_chunk = self.grid_manager.get_chunk_coords(self.player.rect.center)
 
        # ── LOAD: generar chunks cercanos que no existen aún ──
        for chunk_pos in self.grid_manager.get_chunks_to_load(player_chunk):
            if chunk_pos not in self.generated_chunks:
                self.world_generator.generate_chunk(
                    chunk_pos[0], chunk_pos[1],
                    self.visible_sprites, self.resource_sprites
                )
                self.generated_chunks.add(chunk_pos)
            self.grid_manager.mark_loaded(chunk_pos)
 
        # ── UNLOAD: descargar chunks lejanos para liberar memoria ──
        for chunk_pos in self.grid_manager.get_chunks_to_unload(player_chunk):
            self.world_generator.unload_chunk(
                chunk_pos,
                self.visible_sprites,
                self.resource_sprites
            )
            # Al descargar, lo quitamos de generated_chunks para que
            # se regenere deterministamente si el jugador regresa
            self.generated_chunks.discard(chunk_pos)
 
    def _get_biome_vis(self, biome_id, key, fallback):
        """Lee colores visuales del bioma desde biomes.json via data_manager."""
        vis = self.manager.data_manager.biome_visual.get(biome_id, {})
        return tuple(vis.get(key, fallback))
 
    def draw_terrain(self, surface, offset_x, offset_y):
        """Dibuja el fondo de bioma de cada chunk visible. Siempre activo."""
        T    = self.world_generator.TILES_PER_CHUNK
        S    = self.world_generator.TILE_SIZE
        cell = T * S
        sw, sh = surface.get_width(), surface.get_height()
 
        col_start = int(offset_x // cell) - 1
        col_end   = int((offset_x + sw) // cell) + 1
        row_start = int(offset_y // cell) - 1
        row_end   = int((offset_y + sh) // cell) + 1
 
        for col in range(col_start, col_end + 1):
            for row in range(row_start, row_end + 1):
                biome_id = self.world_generator.get_biome(col, row)
                fill_col = self._get_biome_vis(biome_id, "color", [50, 50, 50])
                sx = int(col * cell - offset_x)
                sy = int(row * cell - offset_y)
                pygame.draw.rect(surface, fill_col, pygame.Rect(sx, sy, cell, cell))
 
    def draw_chunk_overlay(self, surface, offset_x, offset_y):
        """Dibuja la cuadricula de tiles y bordes de chunk. Toggle con F3."""
        T    = self.world_generator.TILES_PER_CHUNK
        S    = self.world_generator.TILE_SIZE
        cell = T * S
        font = pygame.font.SysFont("monospace", 10, bold=True)
        sw, sh = surface.get_width(), surface.get_height()
 
        col_start = int(offset_x // cell) - 1
        col_end   = int((offset_x + sw) // cell) + 1
        row_start = int(offset_y // cell) - 1
        row_end   = int((offset_y + sh) // cell) + 1
 
        player_chunk = self.grid_manager.get_chunk_coords(self.player.rect.center)
 
        for col in range(col_start, col_end + 1):
            for row in range(row_start, row_end + 1):
                biome_id   = self.world_generator.get_biome(col, row)
                tile_col   = self._get_biome_vis(biome_id, "tile_dark", [30, 30, 30])
                border_col = self._get_biome_vis(biome_id, "border",    [20, 20, 20])
 
                sx = int(col * cell - offset_x)
                sy = int(row * cell - offset_y)
 
                # Lineas de tiles internos
                for tx in range(T + 1):
                    x = sx + tx * S
                    pygame.draw.line(surface, tile_col, (x, sy), (x, sy + cell), 1)
                for ty in range(T + 1):
                    y = sy + ty * S
                    pygame.draw.line(surface, tile_col, (sx, y), (sx + cell, y), 1)
 
                # Highlight chunk del jugador
                if (col, row) == player_chunk:
                    hi = pygame.Surface((cell, cell), pygame.SRCALPHA)
                    hi.fill((255, 255, 255, 25))
                    surface.blit(hi, (sx, sy))
 
                # Borde del chunk
                pygame.draw.rect(surface, border_col,
                                 pygame.Rect(sx, sy, cell, cell), 3)
 
                # Etiqueta bioma + coords
                label  = f"{biome_id} [{col},{row}]"
                shadow = font.render(label, True, (0, 0, 0))
                text   = font.render(label, True, (255, 255, 255))
                surface.blit(shadow, (sx + 7, sy + 7))
                surface.blit(text,   (sx + 6, sy + 6))
 
    def draw_grid_debug(self, surface, offset_x, offset_y):
        T    = self.world_generator.TILES_PER_CHUNK   # 16
        S    = self.world_generator.TILE_SIZE         # 32 px
        cell = T * S                                  # chunk en px (512)
        font = pygame.font.SysFont("monospace", 10, bold=True)
        sw, sh = surface.get_width(), surface.get_height()
 
        col_start = int(offset_x // cell) - 1
        col_end   = int((offset_x + sw) // cell) + 1
        row_start = int(offset_y // cell) - 1
        row_end   = int((offset_y + sh) // cell) + 1
 
        player_chunk = self.grid_manager.get_chunk_coords(self.player.rect.center)
 
        for col in range(col_start, col_end + 1):
            for row in range(row_start, row_end + 1):
                biome_id   = self.world_generator.get_biome(col, row)
                fill_col   = self.BIOME_COLORS.get(biome_id,   ( 50,  50,  50))
                tile_col   = self.BIOME_TILE_DARK.get(biome_id,( 30,  30,  30))
                border_col = self.BIOME_BORDER.get(biome_id,   ( 20,  20,  20))
 
                chunk_sx = int(col * cell - offset_x)
                chunk_sy = int(row * cell - offset_y)
 
                # ── 1. Relleno del chunk ──────────────────────────────
                pygame.draw.rect(surface, fill_col,
                                 pygame.Rect(chunk_sx, chunk_sy, cell, cell))
 
                # ── 2. Líneas de tiles internos (16×16) ───────────────
                for tx in range(T + 1):
                    x = chunk_sx + tx * S
                    pygame.draw.line(surface, tile_col,
                                     (x, chunk_sy), (x, chunk_sy + cell), 1)
                for ty in range(T + 1):
                    y = chunk_sy + ty * S
                    pygame.draw.line(surface, tile_col,
                                     (chunk_sx, y), (chunk_sx + cell, y), 1)
 
                # ── 3. Highlight del chunk del jugador ────────────────
                if (col, row) == player_chunk:
                    hi = pygame.Surface((cell, cell), pygame.SRCALPHA)
                    hi.fill((255, 255, 255, 25))
                    surface.blit(hi, (chunk_sx, chunk_sy))
 
                # ── 4. Borde grueso del chunk ─────────────────────────
                pygame.draw.rect(surface, border_col,
                                 pygame.Rect(chunk_sx, chunk_sy, cell, cell), 3)
 
                # ── 5. Etiqueta bioma + coordenadas ───────────────────
                label  = f"{biome_id} [{col},{row}]"
                shadow = font.render(label, True, (0, 0, 0))
                text   = font.render(label, True, (255, 255, 255))
                surface.blit(shadow, (chunk_sx + 7, chunk_sy + 7))
                surface.blit(text,   (chunk_sx + 6, chunk_sy + 6))
 
    def draw(self, surface):
        # Actualizamos el offset (esto mueve la cámara suavemente)
        self.visible_sprites.update_offset(self.player)
        
        # Creamos el vector entero para el dibujo (esto evita el jittering)
        draw_offset = pygame.math.Vector2(int(self.visible_sprites.offset.x), int(self.visible_sprites.offset.y))
        
        # Terreno base siempre visible; grid encima solo si F3 activo
        self.draw_terrain(surface, int(draw_offset.x), int(draw_offset.y))
        if self.show_debug_grid:
            self.draw_chunk_overlay(surface, int(draw_offset.x), int(draw_offset.y))
        
        # Dibujar sprites pasando el offset ya calculado
        self.visible_sprites.draw(draw_offset)
        
        # Dibujar filtro de noche por encima de TODO lo demás para oscurecer el mundo
        self.night_filter.draw(surface)
 
        # Obtenemos los datos de la fase directamente del reloj
        fase_texto, fase_color = self.clock.get_current_phase_data()
 
        # Interfaz de la hora digital
        font = pygame.font.SysFont("Arial", 22, bold=True)
        time_str = f"{self.clock.get_time_string()} — {fase_texto}"
        time_text = font.render(time_str, True, fase_color)
 
        # Contenedor del reloj con fondo semitransparente oscuro
        bg_rect = pygame.Rect(10, 10, time_text.get_width() + 15, 35)
        pygame.draw.rect(surface, (0, 0, 0, 160), bg_rect, border_radius=5)
 
        # Pintar el texto sobre el rectángulo
        surface.blit(time_text, (18, 15))
 
        # Dibujamos primero la hotbar abajo fija
        self.player.inventory.draw_hotbar(surface, self.player.active_slot)
 
        # El HUD se dibuja DESPUÉS para que nunca quede oculto detrás
        self.draw_player_health_hud(surface)
 
        # Pantalla de Mochila Completa (Tecla E)
        self.inventory_screen.draw(surface, self.player.inventory)
 
        # Menú de Crafteo (Tecla TAB)
        self.crafting_menu.draw(surface)
 
        # Pantalla de Game Over (Se dibuja por encima de TODO si está muerto)
        if self.player.is_dead:
            # Creamos una capa negra semitransparente para oscurecer el fondo
            overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180)) # Negro con transparencia Alfa
            surface.blit(overlay, (0, 0))
            
            # Renderizar el texto de Muerte
            font_gameover = pygame.font.SysFont("Arial", 50, bold=True)
            font_sub = pygame.font.SysFont("Arial", 24)
            
            text_dead = font_gameover.render("HAS MUERTO", True, (255, 0, 0))
            text_retry = font_sub.render("Presiona 'R' para reintentar", True, (255, 255, 255))
            
            # Centrar los textos en la pantalla
            surface.blit(text_dead, (surface.get_width()//2 - text_dead.get_width()//2, surface.get_height()//2 - 50))
            surface.blit(text_retry, (surface.get_width()//2 - text_retry.get_width()//2, surface.get_height()//2 + 20))
 
 
    def check_enemy_interaction(self, mouse_pos):
        """Verifica si el jugador hizo clic sobre un enemigo dentro de su rango de ataque"""
        attack_range = self.manager.data_manager.entities.get("player", {}).get("attack_range", 60)        
        
        world_mouse_x = mouse_pos[0] + self.visible_sprites.offset.x
        world_mouse_y = mouse_pos[1] + self.visible_sprites.offset.y
        world_mouse_pos = (world_mouse_x, world_mouse_y)
        
        for enemy in self.enemy_sprites:
            if enemy.rect.collidepoint(world_mouse_pos):
                player_center = pygame.math.Vector2(self.player.rect.center)
                enemy_center = pygame.math.Vector2(enemy.rect.center)
                distance = player_center.distance_to(enemy_center)
                
                if distance <= attack_range:
                    damage_inflicted = self.player.get_current_tool_damage("enemy")
                    self.particle_manager.create_hit_particles(enemy.rect.center, "tree")
                    enemy.take_damage(damage_inflicted)
                    self.player.trigger_attack_animation()
                    print(f"¡Atacaste al {enemy.enemy_type}! Daño infligido: {damage_inflicted}")                    
                    return True 
                else:
                    print("¡El enemigo está demasiado lejos para atacar!")
                    return True
        return False
    
    def draw_player_health_hud(self, surface):
        """Dibuja la vida del jugador centrada justo arriba de la hotbar"""
        # =================================================================
        # BARRA DE VIDA (Columna Izquierda)
        # =================================================================
        # CONFIGURACIÓN DE LOS CONTENEDORES
        vida_por_corazon = 10
        max_corazones = self.player.max_health // vida_por_corazon
        # Evitamos que con 99.9 de vida se vacíe un corazón entero de golpe
        corazones_llenos = math.ceil(self.player.current_health / vida_por_corazon)        
        tamano_bloque = 14  
        separacion = 4
        
        # MATEMÁTICA DE POSICIONAMIENTO CENTRAL
        ancho_fila_completa = (max_corazones * tamano_bloque) + ((max_corazones - 1) * separacion)
        centro_pantalla_x = surface.get_width() // 2
        espacio_central = 15 
        
        inicio_x = centro_pantalla_x - espacio_central - ancho_fila_completa
        
        # Columna izquierda para vida, columna derecha para hambre (futura implementación)
        inicio_y = surface.get_height() - 95 
        
        # Colores de prototipo
        color_lleno = (255, 40, 40)      # Rojo Vida
        color_vacio = (50, 50, 50)       # Gris Contenedor
        color_borde = (0, 0, 0)
 
        # BUCLE DE DIBUJADO (Columna Izquierda - Vida)
        for i in range(max_corazones):
            x = inicio_x + i * (tamano_bloque + separacion)
            y = inicio_y
            
            rect_corazon = pygame.Rect(x, y, tamano_bloque, tamano_bloque)
            color_actual = color_lleno if i < corazones_llenos else color_vacio
                
            pygame.draw.rect(surface, color_actual, rect_corazon)
            pygame.draw.rect(surface, color_borde, rect_corazon, 2)
 
        # =================================================================
        # BARRA DE HAMBRE (Columna Derecha)
        # =================================================================
        inicio_hambre_x = centro_pantalla_x + espacio_central
        color_hambre_lleno = (210, 105, 30)  # Color café/pan
        
        # Traducir los puntos de hambre actuales a cuántos bloques de 10 puntos pintar
        hambre_por_bloque = 10
        max_bloques_hambre = self.player.max_hunger // hambre_por_bloque
        # Si tienes 99.9, se divide entre 10 (= 9.99) y math.ceil lo sube a 10 bloques pintados.
        bloques_hambre_llenos = math.ceil(self.player.current_hunger / hambre_por_bloque)
 
        for i in range(max_bloques_hambre):
            x = inicio_hambre_x + i * (tamano_bloque + separacion)
            rect_hambre = pygame.Rect(x, inicio_y, tamano_bloque, tamano_bloque)
            
            # Si el índice actual es menor que los bloques llenos, se pinta de color café;
            # de lo contrario, se queda con el color de contenedor vacío (gris)
            color_actual_hambre = color_hambre_lleno if i < bloques_hambre_llenos else color_vacio
            
            pygame.draw.rect(surface, color_actual_hambre, rect_hambre)
            pygame.draw.rect(surface, color_borde, rect_hambre, 2)
        # =================================================================
        # GUÍA FUTURA: FILA 2 (Armadura y Sed)
        # =================================================================