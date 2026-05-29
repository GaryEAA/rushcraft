import math

import pygame
import json
import random
from src.entities import enemy
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
        self.grid_manager = GridManager(cell_size=640)
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
        
        # Generar el mapa con recursos reales
        self.generate_resources()

        # Instanciar sistemas secundarios
        self.clock = GameClock(time_scale=600.0) # 60 -> 600 para testear el ciclo día/noche rápidamente
        self.night_filter = NightFilter(800, 600)
        self.drop_sprites = pygame.sprite.Group()
        self.particle_manager = ParticleManager(self.visible_sprites)
        self.recipe_manager = RecipeManager()

        # Menús e Interfaces
        self.crafting_menu = CraftingMenu(self.recipe_manager)
        self.inventory_screen = InventoryScreen()

        # Variables de control para el Spawner Nocturno
        self.spawn_timer = 0
        self.spawn_cooldown = 4.0  # Intentar spawnear un enemigo cada 4 segundos de noche
        self.max_enemies_allowed = 8

        self.spawn_rules = data.spawn_rules

    def load_spawn_rules(self):
        try:
            with open("data/spawn_rules.json", "r", encoding="utf-8") as f:
                return json.load(f).get("spawn_rules", [])
        except Exception as e:
            print(f"Error cargando reglas de spawn: {e}")
            return []

    def load_entities_data(self):
        try:
            with open("data/entities.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar data/entities.json: {e}")
            return {"player": {"max_health": 100, "speed": 200}}

    def load_items_data(self):
        """Carga las configuraciones de herramientas, materiales y consumibles"""
        try:
            with open("data/items.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar data/items.json: {e}")
            return {"consumables": {}}

    def generate_resources(self):
        """Distribuye árboles y rocas reales por el mapa de manera aleatoria"""
        # PARA LOS ÁRBOLES
        for _ in range(10):
            x, y = random.randint(0, 1200), random.randint(0, 1000)
            tree = Resource(x, y, resource_type="tree", health=30, item_yield="wood")
            
            self.grid_manager.add_resource(tree)
            
            self.visible_sprites.add(tree)
            self.resource_sprites.add(tree)
            
        # PARA LAS ROCAS
        for _ in range(5):
            x = random.randint(0, 1200)
            y = random.randint(0, 1000)
            rock = Resource(x, y, resource_type="rock", health=50, item_yield="stone")
            
            self.grid_manager.add_resource(rock) 
            
            self.visible_sprites.add(rock)
            self.resource_sprites.add(rock)

    def manage_enemy_spawning(self, dt):
        # 1. ¿Hay alguna regla activa para esta hora?
        rules_list = self.spawn_rules.get("spawn_rules", [])
        
        active_rules = [
            rule for rule in rules_list 
            if rule["hours"][0] <= self.clock.hour < rule["hours"][1]
        ]
        
        # 2. Si no hay reglas, es momento de que el sol haga su trabajo
        if not active_rules:
            if not self.clock.is_daytime:
                self.clock.is_daytime = True # Sincronizamos estado
            
            self.spawn_timer = 0
            for enemy in list(self.enemy_sprites):
                self.particle_manager.create_hit_particles(enemy.rect.center, "tree")
                if enemy.take_damage(15 * dt):
                    print(f"El sol ha incinerado a un enemigo.")
            return

        # 3. Si hay reglas activas, spawneamos
        self.spawn_timer += dt
        # Usamos la primera regla activa encontrada
        rule = active_rules[0] 
        
        if self.spawn_timer >= rule["spawn_rate"]:
            self.spawn_timer = 0
            if len(self.enemy_sprites) < rule["max_mobs"]:
                self.spawn_enemy(random.choice(rule["mobs"]))

    def cooldown_or_spawn_time(self):
        # Retorna el cooldown base (se puede modificar según la hora exacta para dar más dificultad)
        return self.spawn_cooldown

    def spawn_enemy(self, mob_type):
        """Elige un enemigo según el tipo pasado por el JSON y lo spawnea."""
        enemies_config = self.manager.data_manager.entities.get("enemies", {})
        stats = enemies_config.get(mob_type)
        
        if not stats:
            print(f"Error: No se encontró la configuración para {mob_type}")
            return

        # Matemática de Spawn Seguro
        angle = random.uniform(0, 2 * math.pi)
        distance = random.randint(500, 700) 
        
        spawn_x = self.player.rect.centerx + int(math.cos(angle) * distance)
        spawn_y = self.player.rect.centery + int(math.sin(angle) * distance)

        # Limitar dentro de los bordes del mapa
        spawn_x = max(0, min(spawn_x, 1200))
        spawn_y = max(0, min(spawn_y, 1000))

        new_enemy = Enemy(spawn_x, spawn_y, mob_type, stats)
        self.visible_sprites.add(new_enemy)
        self.enemy_sprites.add(new_enemy)
        print(f"¡Un {new_enemy.name} ha aparecido en las sombras! ({spawn_x}, {spawn_y})")

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

                # TODO: (DEBUG) Presiona 'I' para inyectar recursos masivos
                if event.key == pygame.K_i:
                    # Añadimos 100 de madera y 100 de piedra de golpe
                    self.player.inventory.add_item("wood", 100)
                    self.player.inventory.add_item("stone", 100)
                    self.player.inventory.add_item("apple", 5)
                    self.player.inventory.add_item("cooked_meat", 5)
                    print("Debug: Recursos e ítems de comida inyectados correctamente.")

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
                    print(f"Clic detectado en {resource.type}. Daño: {dynamic_damage}")
                    
                    self.particle_manager.create_hit_particles(resource.rect.center, resource.type)
                    resource.hit(
                        damage = dynamic_damage, 
                        drop_groups = [self.visible_sprites, self.drop_sprites]
                    )
                    self.player.trigger_attack_animation()
                    break
                
    def update(self, dt):
        self.clock.update(dt)
        self.night_filter.update(self.clock.hour, self.clock.minute)
        
        # Ejecutar el gestor del ciclo y spawneo de enemigos constantemente
        self.manage_enemy_spawning(dt)

        # Bloquear movimiento del jugador si alguna interfaz está desplegada
        if not self.crafting_menu.is_open and not self.inventory_screen.is_open:
            self.player.update(dt, self.resource_sprites)

            # Actualizar la IA y movimiento de todos los enemigos en pantalla.
            # Les pasamos los recursos como obstáculos y el rectángulo del jugador para que lo persigan.
            for enemy in self.enemy_sprites:
                enemy.update(dt, self.resource_sprites, self.player.rect)

            # Detectar si algún enemigo está tocando físicamente al jugador
            collided_enemies = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False)
            for enemy in collided_enemies:
                if self.player.take_damage(enemy.damage):
                    self.particle_manager.create_hit_particles(self.player.rect.center, "rock")
                    
                    # Si este golpe mató al jugador, tiramos su inventario al suelo
                    if self.player.is_dead:
                        items_to_drop = self.player.drop_all_items()
                        
                        # Spawneamos cada ítem en el suelo
                        for item in items_to_drop:
                            offset_x = random.randint(-20, 20)
                            offset_y = random.randint(-20, 20)
                            
                            # Clase ItemDrop recibe: pos (tupla), groups (los grupos de Pygame)
                            drop_pos = (self.player.rect.centerx + offset_x, self.player.rect.centery + offset_y)
                            
                            # Al pasarle los grupos aquí, se añade automáticamente a render y lógica
                            ItemDrop(
                                drop_pos, 
                                [self.visible_sprites, self.drop_sprites], 
                                item["item_id"], 
                                item["amount"]
                            )
        self.particle_manager.update(dt)

        # Lógica de recolección (Pickup)
        if not self.player.is_dead:
            collided_drops = pygame.sprite.spritecollide(self.player, self.drop_sprites, False)
            for drop in collided_drops:
                if self.player.inventory.add_item(drop.item_id, drop.amount):
                    drop.kill()
                    print(f"Recogido: {drop.amount} de {drop.item_id}")

        self.drop_sprites.update(dt)

    def draw_grid_debug(self, surface, offset_x, offset_y):
        cell_size = self.grid_manager.cell_size
        
        # Calcular rango visible
        start_col = int(offset_x // cell_size)
        end_col = int((offset_x + surface.get_width()) // cell_size) + 1
        start_row = int(offset_y // cell_size)
        end_row = int((offset_y + surface.get_height()) // cell_size) + 1

        for col in range(start_col, end_col + 1):
            x = int((col * cell_size) - offset_x)
            pygame.draw.line(surface, (100, 150, 100), (x, 0), (x, surface.get_height()))

        for row in range(start_row, end_row + 1):
            y = int((row * cell_size) - offset_y)
            pygame.draw.line(surface, (100, 150, 100), (0, y), (surface.get_width(), y))

    def draw(self, surface):
        # Calculamos el offset UNA SOLA VEZ aquí
        self.visible_sprites.update_offset(self.player)

        # Guardamos en variables locales (esto bloquea el valor para este frame)
        current_offset = self.visible_sprites.offset

        # Dibujar base del mapa y terreno
        surface.fill(self.color_grass)

        # Dibujamos el grid pasando el offset fijo
        self.draw_grid_debug(surface, current_offset.x, current_offset.y)

        # Dibujar TODO lo que está en el grupo de cámara de forma automática
        self.visible_sprites.draw(self.player)

        # Filtro de iluminación solar / nocturna
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