import pygame
from src.entities.entity import Entity
from src.managers.inventory_system import InventorySystem

class Player(Entity):
    def __init__(self, x, y, stats, state_manager):
        """
        Instancia al jugador leyendo sus estadísticas iniciales.
        """
        speed = stats.get("speed")
        max_health = stats.get("max_health")
        super().__init__(x, y, speed, max_health)
        
        self.manager = state_manager
        
        self.item_data = self.manager.data_manager.items

        # Definir una base cuadrada fija
        self.image = pygame.Surface((40, 40))
        self.image.fill((30, 144, 255))
        
        centro_inicial = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = centro_inicial
        
        # Inyectar el componente de inventario
        slots_capacity = stats.get("inventory_size", 36)
        self.inventory = InventorySystem(total_slots=slots_capacity)
        self.active_slot = 0
        
        # Control de vida dinámico basado en las stats del JSON
        self.max_health = stats.get("max_health", 100)
        self.current_health = self.max_health
        
        # Control de Hambre dinámico basado en las stats del JSON
        self.max_hunger = stats.get("max_hunger", 100)
        self.current_hunger = self.max_hunger
        self.hunger_decay_rate = stats.get("hunger_decay_rate", 1.5)
        
        # Temporizadores internos para los procesos metabólicos
        self.regen_timer = 0.0
        self.starve_timer = 0.0

        # Temporizadores para evitar daño masivo continuo
        self.invulnerable_timer = 0.0
        self.invulnerable_duration = 0.5 # Medio segundo de inmunidad tras ser golpeado

        # Estado de vida del jugador
        self.is_dead = False

        # Control de orientación visual
        self.facing_direction = "down" # Puede ser: "up", "down", "left", "right"
        
        # Variables para la animación de ataque por código
        self.is_attacking = False
        self.attack_duration = 0.15  # Qué tan rápido es el "hachazo" (en segundos)
        self.attack_timer = 0.0
        self.visual_scale_x = 1.0
        self.visual_scale_y = 1.0

    def input(self):
        """Escucha el teclado y altera la dirección del vector de movimiento"""
        keys = pygame.key.get_pressed()
        
        # Resetear dirección en cada frame
        self.direction.x = 0
        self.direction.y = 0

        # TODO: MOVIMIENTO CON TECLAS WASD O FLECHAS
        # Movimiento en Eje Y y actualización de orientación
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.direction.y = -1
            self.facing_direction = "up"
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction.y = 1
            self.facing_direction = "down"
            
        # Movimiento en Eje X y actualización de orientación
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.facing_direction = "left"
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.facing_direction = "right"

        # TODO: SELECCIÓN DE LA HOTBAR
        # Teclas del 1 al 9 (Índices 0 al 8)
        for i in range(9):
            if keys[pygame.K_1 + i]:
                self.active_slot = i

        # Tecla 0 (Slot 10, Índice 9)
        if keys[pygame.K_0]:
            self.active_slot = 9

        # Tecla "," (Slot 11, Índice 10)
        if keys[pygame.K_COMMA]:
            self.active_slot = 10
            
        # Tecla "." (Slot 12, Índice 11)
        if keys[pygame.K_PERIOD]:
            self.active_slot = 11

    def update(self, dt, obstacle_sprites):
        """Actualización frame a frame del jugador con conocimiento de obstáculos"""
        # Si el jugador está muerto, no procesa movimiento ni inputs
        if self.is_dead:
            return
        
        self.input()
        # Le pasamos los obstáculos al método move de la clase madre (Entity)
        self.move(dt, obstacle_sprites)

        # Reducir el tiempo de invulnerabilidad frame a frame
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= dt

        # Controlar la animación de ataque
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False
                # Regresa a su tamaño original (cuadrado perfecto)
                self.visual_scale_x = 1.0
                self.visual_scale_y = 1.0

        # EJECUTAR METABOLISMO
        self.handle_metabolism(dt)

    def get_current_tool_damage(self, resource_type):
        """
        Calcula el daño proporcional cruzando el tipo de herramienta, 
        el recurso golpeado y el multiplicador del material desde el JSON.
        """

        data = self.manager.data_manager

        # 1. Obtener los datos del slot que tenemos seleccionado en la mano
        active_item = self.inventory.slots[self.active_slot]
        
        # 2. Si la mano está vacía (None), devolvemos el daño base de puños desde el JSON
        if active_item is None:
            return data.entities.get("player", {}).get("hand_damage", 2)
            
        item_id = active_item["item_id"] # Ejemplos: "axe", "pickaxe", "stone_axe", "stone_pickaxe"
        
        # 3. IDENTIFICAR EL MATERIAL Y TIPO DE HERRAMIENTA
        # Si es una herramienta básica inicial ("axe" o "pickaxe")
        if item_id == "axe" or item_id == "pickaxe":
            material = "wood"       # Las iniciales cuentan como madera por defecto
            tool_type = item_id     # El tipo es directamente el ID completo
        elif "_" in item_id:
            # Si tiene un guion bajo (como "stone_axe"), separamos el material del tipo
            material, tool_type = item_id.split("_", 1)
        else:
            # Si tiene cualquier otra cosa en la mano (como el recurso "wood" o "stone"), hace daño mínimo
            return self.item_data.get("hand_damage", 2)
        
        # 4. EXTRAER CONFIGURACIONES DEL DICCIONARIO JSON
        materials_config = self.item_data.get("materials", {})
        tools_config = self.item_data.get("tools", {})

        # 5. MATEMÁTICA PROPORCIONAL: Si existen en el JSON, calculamos dinámicamente
        if tool_type in tools_config and material in materials_config:
            base_damage_dict = tools_config[tool_type].get("base_damage", {})
            base_damage = base_damage_dict.get(resource_type, 1) # Por defecto 1 de daño si el recurso no califica
            multiplier = materials_config[material].get("multiplier", 1.0)
            
            # Retorna el daño final entero: Daño Base * Multiplicador
            return int(base_damage * multiplier)

        # Si algo falla en la lectura, daño base de seguridad por defecto
        return self.item_data.get("hand_damage", 2)

    def take_damage(self, amount):
        """Aplica daño al jugador si no es invulnerable y no está muerto"""
        if self.is_dead:
            return False
            
        if self.invulnerable_timer <= 0:
            self.current_health -= amount
            self.invulnerable_timer = self.invulnerable_duration
            
            if self.current_health <= 0:
                self.current_health = 0
                self.is_dead = True # ¡El jugador ha muerto oficialmente!
                print("¡Has muerto! Movimiento bloqueado.")
            else:
                print(f"¡Jugador golpeado! Vida restante: {self.current_health}/{self.max_health}")
            return True
        return False

    # Para cuando el jugador presione la tecla de revivir
    def reset(self, start_x, start_y):
        """Restablece los valores del jugador para una nueva partida"""
        self.current_health = self.max_health
        self.current_hunger = self.max_hunger
        self.is_dead = False
        self.invulnerable_timer = 0.0
        
        # Actualizamos el rectángulo físico
        self.rect.topleft = (start_x, start_y)
        
        # Si el jugador tiene un atributo de posición separado (como un vector), también lo actualizamos
        if hasattr(self, 'pos'):
            self.pos.x = start_x
            self.pos.y = start_y
            
        self.direction.x = 0
        self.direction.y = 0

    def drop_all_items(self):
        """Vacía el inventario del jugador y devuelve los ítems para spawnearlos en el suelo"""
        dropped_items = []
        
        # Al ser una lista, usamos enumerate para recorrer los slots de forma segura
        for slot_idx, item_data in enumerate(self.inventory.slots):
            # Si el slot no está vacío, extraemos su información para crear un drop en el suelo
            if item_data is not None:
                # Extraemos los datos usando las llaves de JSON/Diccionario: "item_id" y "quantity"
                dropped_items.append({
                    "item_id": item_data["item_id"],
                    "amount": item_data["quantity"]
                })
                
        # Vaciamos por completo el inventario llamando al nuevo método que agregamos
        self.inventory.clear()
        
        return dropped_items
    
    def trigger_attack_animation(self):
        """Activa un efecto visual de deformación al atacar"""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = self.attack_duration
            
            # Dependiendo de a dónde mira, se estira en un eje diferente
            if self.facing_direction in ["left", "right"]:
                self.visual_scale_x = 1.4  # Se estira hacia los lados
                self.visual_scale_y = 0.7  # Se aplana un poco
            else:
                self.visual_scale_x = 0.7
                self.visual_scale_y = 1.4  # Se estira hacia arriba/abajo

    def draw_custom(self, surface, camera_offset):
        """Dibuja al jugador aplicando el efecto de estiramiento por código"""
        # 1. Calculamos el nuevo tamaño de la superficie basado en la animación
        new_width = int(self.rect.width * self.visual_scale_x)
        new_height = int(self.rect.height * self.visual_scale_y)
        
        # 2. Escalamos la imagen original de forma temporal para el frame actual
        scaled_image = pygame.transform.scale(self.image, (new_width, new_height))
        
        # 3. Ajustamos la posición para que el estiramiento ocurra desde el centro del personaje
        scaled_rect = scaled_image.get_rect()
        scaled_rect.center = (self.rect.centerx - camera_offset.x, self.rect.centery - camera_offset.y)
        
        # 4. Lo dibujamos en la pantalla del juego
        surface.blit(scaled_image, scaled_rect)

    def handle_metabolism(self, dt):
        """Gestiona el consumo de comida, curación por saciedad y daño por hambre"""
        # 1. GASTO DINÁMICO DE HAMBRE
        # Si el jugador se está moviendo o ejecutando la animación de ataque, consume el doble de energía
        actual_decay = self.hunger_decay_rate
        if self.direction.length() > 0 or self.is_attacking:
            actual_decay *= 2.0
            
        self.current_hunger -= actual_decay * dt
        if self.current_hunger < 0:
            self.current_hunger = 0

        # 2. REGENERACIÓN PASIVA (Si la saciado a más del 80%)
        if self.current_hunger >= self.max_hunger * 0.80 and self.current_health < self.max_health:
            self.regen_timer += dt
            if self.regen_timer >= 4.0:  # Cada 4 segundos cura 5 puntos de vida
                self.current_health = min(self.max_health, self.current_health + 5)
                self.regen_timer = 0.0
                print(f"Regeneración por saciedad: {self.current_health}/{self.max_health}")
        else:
            self.regen_timer = 0.0

        # 3. INANICIÓN (Si el hambre llegó a 0)
        if self.current_hunger <= 0:
            self.starve_timer += dt
            if self.starve_timer >= 2.0:  # Cada 2 segundos pierde 5 puntos de vida
                self.take_damage(5)
                self.starve_timer = 0.0
                print("¡Te estás muriendo de hambre! Busca comida.")
        else:
            self.starve_timer = 0.0

    def consume_item(self, item_id, consumables_config):
        """Procesa el consumo de un ítem modificando las estadísticas del jugador de forma dinámica"""
        
        # 1. Verificar si el ítem existe en la configuración cargada del JSON
        if item_id not in consumables_config:
            print(f"DEBUG: El ítem '{item_id}' no es algo que te puedas comer o no está en el JSON.")
            return False

        # 2. Si el jugador ya está completamente lleno de vida Y hambre, no malgastar comida
        if self.current_hunger >= self.max_hunger and self.current_health >= self.max_health:
            print("Ya estás completamente lleno, no te cabe un bocado más.")
            return False

        # 3. Aplicar los efectos nutritivos leyendo las llaves correctas de tu JSON
        item_effects = consumables_config[item_id]
        
        # Extraemos los valores de restauración de hambre y salud, así como el mensaje personalizado para cada comida
        hunger_gain = item_effects.get("hunger_restore", 0)
        health_gain = item_effects.get("health_restore", 0)
        message = item_effects.get("message", "Te has comido algo.")
        
        self.current_hunger = min(self.max_hunger, self.current_hunger + hunger_gain)
        self.current_health = min(self.max_health, self.current_health + health_gain)
        
        print(message)
        print(f"Estado actual -> Hambre: {int(self.current_hunger)}/{self.max_hunger} | Vida: {self.current_health}/{self.max_health}")
        
        return True