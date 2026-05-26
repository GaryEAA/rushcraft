import pygame
import json
import random
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.resources import Resource
from src.core.camera import CameraGroup
from src.managers.game_clock import GameClock
from src.effects.night_filter import NightFilter

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
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.manager.change_state("menu")
                    
                # MECÁNICA DE INTERACCIÓN FÍSICA (Pulsar ESPACIO para recolectar)
                if event.key == pygame.K_SPACE:
                    self.check_resource_interaction()

    def check_resource_interaction(self):
        """Busca si hay algún recurso lo suficientemente cerca del jugador para golpearlo"""
        # Rango de alcance del jugador (Leemos el rango del ataque desde su configuración o usamos 60)
        interaction_range = 60
        
        for resource in self.resource_sprites:
            # Calcular la distancia matemática entre el centro del jugador y el recurso
            player_center = pygame.math.Vector2(self.player.rect.center)
            resource_center = pygame.math.Vector2(resource.rect.center)
            distance = player_center.distance_to(resource_center)
            
            # Si el recurso está en rango de golpe
            if distance <= interaction_range:
                # El jugador golpea el recurso aplicando su daño por defecto (10)
                is_destroyed = resource.hit(damage=10)
                
                if is_destroyed:
                    # Dar la recompensa directo al inventario del jugador
                    # Un árbol da 15 de madera, una roca da 8 de piedra
                    qty = 15 if resource.type == "tree" else 8
                    self.player.inventory.add_item(item_id=resource.item_yield, quantity=qty)
                    
                    # Hacer desaparecer el recurso del juego
                    resource.kill() 
                    self.player.inventory.debug_display()
                break # Solo golpear un recurso a la vez

    def update(self, dt):
        # Actualizar el reloj global
        self.clock.update(dt)
        # Actualizar la opacidad del filtro de noche
        self.night_filter.update(self.clock.hour, self.clock.minute)
        # El jugador necesita saber dónde están los recursos para no atravesarlos
        self.player.update(dt, self.resource_sprites)

    def draw(self, surface):
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
        self.player.inventory.draw_hotbar(surface)