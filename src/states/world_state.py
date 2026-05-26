from turtle import distance

import pygame
import json
import random
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.resources import Resource
from src.core.camera import CameraGroup
from src.managers.game_clock import GameClock
from src.effects.night_filter import NightFilter
from src.effects.particle_manager import ParticleManager
from src.managers.recipe_manager import RecipeManager
from src.ui.crafting_menu import CraftingMenu

class WorldState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        self.color_grass = (34, 139, 34)
        
        self.entities_data = self.load_entities_data()
        player_stats = self.entities_data["player"]
        self.player = Player(400, 300, player_stats)
        
        # Grupos de render y colisión
        self.visible_sprites = CameraGroup()
        self.resource_sprites = pygame.sprite.Group() # Grupo específico para interactuar
        
        # Añadir al jugador al render
        self.visible_sprites.add(self.player)
        
        # Generar el mapa con recursos reales en lugar de bloques de prueba
        self.generate_resources()

        # Instanciar el reloj del mundo
        self.clock = GameClock(time_scale=60.0) # 1 seg real = 1 min juego

        # Instanciar el filtro con las dimensiones de la pantalla
        self.night_filter = NightFilter(800, 600)

        # Grupo para objetos que caen al romper recursos
        self.drop_sprites = pygame.sprite.Group()

        # Instanciar el administrador de efectos visuales
        self.particle_manager = ParticleManager(self.visible_sprites)

        # Instanciar el administrador de recetas
        self.recipe_manager = RecipeManager()

        # Instanciar la interfaz gráfica del menú
        self.crafting_menu = CraftingMenu(self.recipe_manager)

    def load_entities_data(self):
        try:
            with open("data/entities.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar data/entities.json: {e}")
            return {"player": {"max_health": 100, "speed": 200}}

    def generate_resources(self):
        """Distribuye árboles y rocas reales por el mapa de manera aleatoria"""
        # Generar 10 árboles
        for _ in range(10):
            x = random.randint(0, 1200)
            y = random.randint(0, 1000)
            tree = Resource(x, y, resource_type="tree", health=30, item_yield="wood")
            self.visible_sprites.add(tree)
            self.resource_sprites.add(tree)
            
        # Generar 5 depósitos de piedra
        for _ in range(5):
            x = random.randint(0, 1200)
            y = random.randint(0, 1000)
            rock = Resource(x, y, resource_type="rock", health=50, item_yield="stone")
            self.visible_sprites.add(rock)
            self.resource_sprites.add(rock)

    def handle_events(self, events):
        for event in events:
            # Manejo de eventos de teclado
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.change_state("menu")
                    
                # Tecla 'E' para Abrir / Cerrar el menú visual de crafteo
                if event.key == pygame.K_e:
                    self.crafting_menu.toggle()

            # DETECCIÓN DE CLICS DEL RATÓN
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 1 = Clic Izquierdo
                    # Caso A: Si el menú de crafteo está abierto, el clic interactúa con la UI
                    if self.crafting_menu.is_open:
                        self.crafting_menu.handle_click(event.pos, self.player.inventory)
                    # Caso B: Si el menú está cerrado, el clic se usa para golpear recursos en el mundo
                    else:
                        self.check_resource_interaction(event.pos)

    def check_resource_interaction(self, mouse_pos):
        """
        Verifica si el jugador hizo clic sobre un recurso y si está lo 
        suficientemente cerca de él para golpearlo, considerando el desplazamiento de la cámara.
        """
        # 1. LEER DESDE CONFIGURACIÓN: Extraemos el rango dinámicamente del JSON cargado
        # Si por alguna razón no existe en el JSON, !!!Usa 80 por defecto de respaldo!!!
        interaction_range = self.entities_data["player"].get("interaction_range", 80)
        
        # 2. TRADUCIR COORDENADAS: Sumamos el offset de la cámara a la posición del mouse en pantalla
        # para obtener las coordenadas reales en la cuadrícula del mundo.
        world_mouse_x = mouse_pos[0] + self.visible_sprites.offset.x
        world_mouse_y = mouse_pos[1] + self.visible_sprites.offset.y
        world_mouse_pos = (world_mouse_x, world_mouse_y)
        
        for resource in self.resource_sprites:
            # Ahora la colisión compara coordenadas del mundo con rectángulos del mundo ✅
            if resource.rect.collidepoint(world_mouse_pos):
                
                # Calcular la distancia real entre el centro del jugador y el recurso
                player_center = pygame.math.Vector2(self.player.rect.center)
                resource_center = pygame.math.Vector2(resource.rect.center)
                distance = player_center.distance_to(resource_center)
                
                if distance <= interaction_range:
                    dynamic_damage = self.player.get_current_tool_damage(resource.type)
                    print(f"Clic detectado en {resource.type}. Daño: {dynamic_damage}")
                    
                    # Generar partículas en el lugar del impacto
                    self.particle_manager.create_hit_particles(resource.rect.center, resource.type)
                    
                    # Golpear el recurso
                    resource.hit(
                        damage = dynamic_damage, 
                        drop_groups = [self.visible_sprites, self.drop_sprites]
                    )
                    break
                
    def update(self, dt):
        # Actualizar el reloj global
        self.clock.update(dt)

        # Actualizar la opacidad del filtro de noche
        self.night_filter.update(self.clock.hour, self.clock.minute)

        # El jugador solo se mueve e interactúa si el menú está CERRADO
        if not self.crafting_menu.is_open:
            self.player.update(dt, self.resource_sprites)

        # Actualizar el comportamiento físico y desaparición de partículas
        self.particle_manager.update(dt)

        # TODO: Lógica de recolección (Pickup)
        collided_drops = pygame.sprite.spritecollide(self.player, self.drop_sprites, False)
        for drop in collided_drops:
            # Intentar añadir al inventario
            if self.player.inventory.add_item(drop.item_id, drop.amount):
                drop.kill() # Eliminar el ítem del suelo si se pudo recoger
                print(f"Recogido: {drop.amount} de {drop.item_id}")

        # Actualizar la animación de los drops
        self.drop_sprites.update(dt)

    def draw(self, surface):
        # TODO: Dibujar el mundo, las entidades y el filtro nocturno
        # Dibujar el mundo y las entidades (Abajo de todo)
        surface.fill(self.color_grass)
        self.visible_sprites.custom_draw(self.player)

        # Capa de oscuridad ambiental (Se aplica sobre el mundo)
        self.night_filter.draw(surface)

        # TODO: Dibujar el reloj digital en la esquina superior izquierda
        font = pygame.font.SysFont("Arial", 24, bold=True)
        time_text = font.render(self.clock.get_time_string(), True, (255, 255, 255))

        # Dibujar un pequeño fondo negro detrás del texto para que se lea bien
        bg_rect = pygame.Rect(10, 10, time_text.get_width() + 10, 35)
        pygame.draw.rect(surface, (0, 0, 0, 150), bg_rect)

        # Estampar el texto
        surface.blit(time_text, (15, 15))

        # TODO: Dibujar la Hotbar del inventario del jugador
        self.player.inventory.draw_hotbar(surface, self.player.active_slot)

        # TODO: Interfaz Gráfica del Menú de Crafteo (Al frente de todo)
        self.crafting_menu.draw(surface)