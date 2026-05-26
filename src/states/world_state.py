import pygame
import json
import random
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

            # 2. Manejo de la rueda del ratón (Scroll)
            if event.type == pygame.MOUSEWHEEL:
                self.crafting_menu.handle_scroll(event)

            # 3. Detección de clics (UNIFICADA)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Clic izquierdo
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
            # Usamos spritecollide para verificar colisiones de rectángulos de forma masiva
            collided_enemies = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False)
            for enemy in collided_enemies:
                # El jugador intenta tomar daño basado en el stat .damage del enemigo (leído del JSON)
                if self.player.take_damage(enemy.damage):
                    # Generamos partículas de golpe de tipo "blood" o efectos visuales en la posición del jugador
                    self.particle_manager.create_hit_particles(self.player.rect.center, "rock") # Usamos rock provisionalmente

        self.particle_manager.update(dt)

        # Lógica de recolección (Pickup)
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

        # La hotbar se dibuja SIEMPRE abajo fija
        # permitiendo interactuar visualmente con ella en tiempo real aunque la mochila esté superpuesta arriba.
        self.player.inventory.draw_hotbar(surface, self.player.active_slot)

        # Pantalla de Mochila Completa (Tecla E)
        self.inventory_screen.draw(surface, self.player.inventory)

        # Menú de Crafteo (Tecla TAB)
        self.crafting_menu.draw(surface)

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
                
                # Si está lo suficientemente cerca, lo atacamos
                if distance <= attack_range:
                    # Obtenemos el daño dinámico de la herramienta activa del jugador
                    # TODO: (PROVISIONAL) Si no hay método adaptado para enemigos, usamos el daño base del jugador por ahora
                    damage_inflicted = player_stats.get("damage", 10)
                    
                    # Hacer parpadear partículas en el enemigo
                    self.particle_manager.create_hit_particles(enemy.rect.center, "tree") # Usamos partículas de árbol provisionalmente
                    
                    # Aplicar daño al enemigo
                    enemy.take_damage(damage_inflicted)
                    return True # Retornamos True para indicar que sí hubo ataque y no pique un árbol por accidente
                else:
                    print("¡El enemigo está demasiado lejos para atacar!")
                    return True # Bloquea el golpe al árbol porque tu intención era atacar al enemigo
                    
        return False # No se clickeó ningún enemigo