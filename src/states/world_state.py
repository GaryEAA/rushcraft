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
            
            # Si el recurso está dentro del rango de interacción, lo golpeamos
            if distance <= interaction_range:
                # Calcular dinámicamente el daño basado en lo que el jugador tiene en la mano
                dynamic_damage = self.player.get_current_tool_damage(resource.type)
                
                print(f"Golpeando con herramienta activa. Daño calculado: {dynamic_damage}")

                # NUEVO: Generar ráfaga de partículas en el centro del recurso antes de aplicar el daño
                self.particle_manager.create_hit_particles(resource.rect.center, resource.type)

                # Pasar el daño dinámico calculado al recurso
                resource.hit(
                    damage = dynamic_damage, 
                    drop_groups = [self.visible_sprites, self.drop_sprites]
                )
                break # Solo golpear un recurso a la vez

    def update(self, dt):
        # Actualizar el reloj global
        self.clock.update(dt)
        # Actualizar la opacidad del filtro de noche
        self.night_filter.update(self.clock.hour, self.clock.minute)
        # El jugador necesita saber dónde están los recursos para no atravesarlos
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