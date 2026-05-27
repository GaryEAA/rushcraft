import pygame
from src.entities.entity import Entity
from src.managers.inventory_system import InventorySystem

class Player(Entity):
    def __init__(self, x, y, stats):
        """
        Instancia al jugador leyendo sus estadísticas iniciales.
        Ahora el jugador inicia con las manos 100% vacías.
        """
        super().__init__(x, y, stats["speed"], stats["max_health"])
        
        # Personalizar el color del cuadrado del jugador para diferenciarlo de un enemigo
        self.image.fill((30, 144, 255)) # Azul brillante (Dodger Blue)
        
        # Inyectar el componente de inventario leyendo la capacidad desde el JSON
        slots_capacity = stats.get("inventory_size", 36) # Valor por defecto de 36 slots si no se especifica
        self.inventory = InventorySystem(total_slots=slots_capacity)
        self.active_slot = 0 # Guarda el índice del slot seleccionado (0 al 11)
        
        # Cargar datos dinámicos de los ítems
        self.item_data = self.load_item_data()

        # Control de vida dinámico basado en las stats del JSON
        self.max_health = stats.get("max_health", 100)
        self.current_health = self.max_health
        
        # Temporizadores para evitar daño masivo continuo
        self.invulnerable_timer = 0.0
        self.invulnerable_duration = 0.5 # Medio segundo de inmunidad tras ser golpeado

        # Estado de vida del jugador
        self.is_dead = False

    # Carga de forma segura el archivo JSON de configuración de balanceo
    def load_item_data(self):
        """Carga la configuración de combate y materiales desde el JSON"""
        import json
        try:
            with open("data/items.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar data/items.json: {e}. Usando backup de emergencia.")
            # Respaldo en memoria por si el archivo JSON no existe o está mal formateado
            return {
                "hand_damage": 2,
                "materials": {"wood": {"multiplier": 1.0}, "stone": {"multiplier": 2.0}},
                "tools": {
                    "axe": {"base_damage": {"tree": 15, "rock": 1}},
                    "pickaxe": {"base_damage": {"tree": 1, "rock": 25}}
                }
            }

    def input(self):
        """Escucha el teclado y altera la dirección del vector de movimiento"""
        keys = pygame.key.get_pressed()
        
        # Resetear dirección en cada frame
        self.direction.x = 0
        self.direction.y = 0

        # TODO: MOVIMIENTO CON TECLAS WASD O FLECHAS
        # Movimiento en Eje Y (Arriba / Abajo)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.direction.y = -1
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.direction.y = 1
            
        # Movimiento en Eje X (Izquierda / Derecha)
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.direction.x = -1
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.direction.x = 1

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

    def get_current_tool_damage(self, resource_type):
        """
        Calcula el daño proporcional cruzando el tipo de herramienta, 
        el recurso golpeado y el multiplicador del material desde el JSON.
        """
        # 1. Obtener los datos del slot que tenemos seleccionado en la mano
        active_item = self.inventory.slots[self.active_slot]
        
        # 2. Si la mano está vacía (None), devolvemos el daño base de puños desde el JSON
        if active_item is None:
            return self.item_data.get("hand_damage", 2)
            
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
                self.is_dead = True # 🚨 [NUEVO] ¡El jugador ha muerto oficialmente!
                print("¡Has muerto! Movimiento bloqueado.")
            else:
                print(f"¡Jugador golpeado! Vida restante: {self.current_health}/{self.max_health}")
            return True
        return False

    # Para cuando el jugador presione la tecla de revivir
    def reset(self, start_x, start_y):
        """Restablece los valores del jugador para una nueva partida"""
        self.current_health = self.max_health
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