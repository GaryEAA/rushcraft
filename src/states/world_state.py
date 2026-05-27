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

class WorldState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.color_grass = (34, 139, 34)
        
        self.entities_data = self.load_entities_data()
        player_stats = self.entities_data["player"]
        self.player = Player(400, 300, player_stats)
        
        # Grupos de render y colisión
        self.visible_sprites = CameraGroup()
        self.resource_sprites = pygame.sprite.Group() 
        
        # Grupo lógico exclusivo para gestionar enemigos separados de los recursos
        self.enemy_sprites = pygame.sprite.Group()
        
        # Añadir al jugador al render
        self.visible_sprites.add(self.player)
        
        # Generar el mapa con recursos reales
        self.generate_resources()

        # Spawner de prueba para verificar que los enemigos funcionen
        self.spawn_test_enemies()

        # Instanciar sistemas secundarios
        self.clock = GameClock(time_scale=60.0) 
        self.night_filter = NightFilter(800, 600)
        self.drop_sprites = pygame.sprite.Group()
        self.particle_manager = ParticleManager(self.visible_sprites)
        self.recipe_manager = RecipeManager()

        # Menús e Interfaces
        self.crafting_menu = CraftingMenu(self.recipe_manager)
        self.inventory_screen = InventoryScreen()

    def load_entities_data(self):
        try:
            with open("data/entities.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar data/entities.json: {e}")
            return {"player": {"max_health": 100, "speed": 200}}

    def generate_resources(self):
        """Distribuye árboles y rocas reales por el mapa de manera aleatoria"""
        for _ in range(10):
            x = random.randint(0, 1200)
            y = random.randint(0, 1000)
            tree = Resource(x, y, resource_type="tree", health=30, item_yield="wood")
            self.visible_sprites.add(tree)
            self.resource_sprites.add(tree)
            
        for _ in range(5):
            x = random.randint(0, 1200)
            y = random.randint(0, 1000)
            rock = Resource(x, y, resource_type="rock", health=50, item_yield="stone")
            self.visible_sprites.add(rock)
            self.resource_sprites.add(rock)

    # Genera monstruos leyendo las estadísticas dinámicas del JSON
    def spawn_test_enemies(self):
        """Genera un par de enemigos de prueba en el mapa usando los datos del JSON"""
        enemies_config = self.entities_data.get("enemies", {})
        
        # Validar que existan las llaves en el JSON antes de intentar spawnear
        if "slime" in enemies_config:
            # Creamos un slime cerca de la zona inicial
            slime = Enemy(200, 200, "slime", enemies_config["slime"])
            self.visible_sprites.add(slime) # Para que la cámara lo dibuje
            self.enemy_sprites.add(slime)   # Para controlar su IA y colisiones
            
        if "zombie" in enemies_config:
            # Creamos un zombie un poco más alejado
            zombie = Enemy(600, 150, "zombie", enemies_config["zombie"])
            self.visible_sprites.add(zombie)
            self.enemy_sprites.add(zombie)

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
                    # Añadimos 200 de madera y 200 de piedra de golpe
                    self.player.inventory.add_item("wood", 200)
                    self.player.inventory.add_item("stone", 200)
                    print("Debug: Inyectados recursos de prueba en el inventario.")

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
                    
                    # Volvemos a spawnear enemigos limpios en sus posiciones de origen leyendo el JSON
                    self.spawn_test_enemies()
                            
                    print(f"¡Respawn exitoso en ({spawn_x}, {spawn_y})! Camina hacia las coordenadas de tu muerte para recuperar tus cosas.")
            
            # 2. Manejo de la rueda del ratón (Scroll)
            if event.type == pygame.MOUSEWHEEL:
                self.crafting_menu.handle_scroll(event)

            # 3. Detección de clics (UNIFICADA)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Clic izquierdo
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

    def check_resource_interaction(self, mouse_pos):
        """Verifica interacción con recursos considerando el offset de la cámara"""
        interaction_range = self.entities_data["player"].get("interaction_range", 80)
        
        world_mouse_x = mouse_pos[0] + self.visible_sprites.offset.x
        world_mouse_y = mouse_pos[1] + self.visible_sprites.offset.y
        world_mouse_pos = (world_mouse_x, world_mouse_y)
        
        for resource in self.resource_sprites:
            if resource.rect.collidepoint(world_mouse_pos):
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
                    # Desencadena el efecto visual de hachazo/picazo en el jugador
                    self.player.trigger_attack_animation()
                    break
                
    def update(self, dt):
        self.clock.update(dt)
        self.night_filter.update(self.clock.hour, self.clock.minute)

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

    def draw(self, surface):
        # Dibujar base del mapa y terreno
        surface.fill(self.color_grass)
        self.visible_sprites.custom_draw(self.player)

        # Filtro de iluminación solar / nocturna
        self.night_filter.draw(surface)

        # Interfaz de la hora digital
        font = pygame.font.SysFont("Arial", 24, bold=True)
        time_text = font.render(self.clock.get_time_string(), True, (255, 255, 255))
        bg_rect = pygame.Rect(10, 10, time_text.get_width() + 10, 35)
        pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect)
        surface.blit(time_text, (15, 15))

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
        # Leemos el rango de ataque y daño base desde las estadísticas del jugador
        player_stats = self.entities_data["player"]
        attack_range = player_stats.get("attack_range", 60)
        
        # Traducir la posición del ratón de la pantalla a coordenadas del mundo (con el offset de cámara)
        world_mouse_x = mouse_pos[0] + self.visible_sprites.offset.x
        world_mouse_y = mouse_pos[1] + self.visible_sprites.offset.y
        world_mouse_pos = (world_mouse_x, world_mouse_y)
        
        for enemy in self.enemy_sprites:
            # Verificar si el cursor está encima del rectángulo del enemigo
            if enemy.rect.collidepoint(world_mouse_pos):
                # Calcular la distancia entre el centro del jugador y el enemigo
                player_center = pygame.math.Vector2(self.player.rect.center)
                enemy_center = pygame.math.Vector2(enemy.rect.center)
                distance = player_center.distance_to(enemy_center)
                
                # Verificar si el enemigo está dentro del rango de ataque permitido
                if distance <= attack_range:
                    # ¡Daño escalado dinámico con herramientas!
                    # Usamos el método matemático pasándole "enemy" como el objetivo
                    damage_inflicted = self.player.get_current_tool_damage("enemy")
                    
                    # Hacer parpadear partículas en el enemigo
                    self.particle_manager.create_hit_particles(enemy.rect.center, "tree")
                    
                    # Aplicar daño al enemigo e imprimir en consola para validar
                    enemy.take_damage(damage_inflicted)

                    # Desencadena el efecto visual en el jugador
                    self.player.trigger_attack_animation()

                    print(f"¡Atacaste al {enemy.enemy_type}! Daño infligido: {damage_inflicted} usando el slot {self.player.active_slot}")                    
                    return True 
                else:
                    print("¡El enemigo está demasiado lejos para atacar!")
                    return True
                    
        return False # No se clickeó ningún enemigo
    
    def draw_player_health_hud(self, surface):
        """Dibuja la vida del jugador centrada justo arriba de la hotbar"""

        # CONFIGURACIÓN DE LOS CONTENEDORES
        vida_por_corazon = 10
        max_corazones = self.player.max_health // vida_por_corazon
        corazones_llenos = int(self.player.current_health // vida_por_corazon)
        
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
        # PROTOTIPO VISUAL: BARRA DE HAMBRE (Columna Derecha)
        # =================================================================
        inicio_hambre_x = centro_pantalla_x + espacio_central
        color_hambre_lleno = (210, 105, 30)  # Color café/pan
        
        for i in range(10):
            x = inicio_hambre_x + i * (tamano_bloque + separacion)
            rect_hambre = pygame.Rect(x, inicio_y, tamano_bloque, tamano_bloque)
            
            pygame.draw.rect(surface, color_hambre_lleno, rect_hambre)
            pygame.draw.rect(surface, color_borde, rect_hambre, 2)
        # =================================================================
        # GUÍA FUTURA: FILA 2 (Armadura y Sed)
        # =================================================================