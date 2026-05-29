import pygame

class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, max_health):
        """Clase base para todos los objetos móviles y vivos en RushCraft"""
        super().__init__()
        
        # Posición usando vectores matemáticos de Pygame (hace el movimiento más suave)
        self.pos = pygame.math.Vector2(x, y)
        self.direction = pygame.math.Vector2(0, 0)
        self.speed = speed
        
        # Estadísticas básicas
        self.max_health = max_health
        self.health = max_health
        
        # Gráficos provisionales (un rectángulo) hasta que carguemos los spritesheets
        self.image = pygame.Surface((32, 48)) # Proporción estándar
        self.image.fill((200, 200, 200))      # Gris por defecto
        self.rect = self.image.get_rect(topleft=self.pos)

        # Guardamos un rectángulo más pequeño en la base para los pies (Hitbox real de colisión)
        # Esto permite que la cabeza del jugador tape los objetos por perspectiva antes de chocar
        self.hitbox = self.rect.copy().inflate(-4, -24)

    def move(self, dt, obstacle_sprites):
        """Mueve la entidad y resuelve colisiones en ejes separados (X e Y)"""
        # Normalizar el vector para evitar que camine más rápido en diagonal
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
            
        # --- EJE HORIZONTAL ---
        self.pos.x += self.direction.x * self.speed * dt
        self.hitbox.x = round(self.pos.x)
        self.rect.centerx = self.hitbox.centerx
        self.check_collisions("horizontal", obstacle_sprites)
        
        # --- EJE VERTICAL ---
        self.pos.y += self.direction.y * self.speed * dt
        self.hitbox.y = round(self.pos.y)
        self.rect.bottom = self.hitbox.bottom # Vincula la base visual con la base física
        self.check_collisions("vertical", obstacle_sprites)

    def check_collisions(self, direction, obstacle_sprites):
        """Detecta la intersección de hitboxes y frena el avance en seco"""
        for sprite in obstacle_sprites:
            # Comprobar si la hitbox de la entidad choca con la de algún obstáculo
            # Usamos hasattr por si el objeto tiene una hitbox personalizada o usa su rect estándar
            obstacle_box = sprite.hitbox if hasattr(sprite, "hitbox") else sprite.rect
            
            if self.hitbox.colliderect(obstacle_box):
                if direction == "horizontal":
                    if self.direction.x > 0: # Caminando a la derecha
                        self.hitbox.right = obstacle_box.left
                    if self.direction.x < 0: # Caminando a la izquierda
                        self.hitbox.left = obstacle_box.right
                    self.pos.x = self.hitbox.x
                    self.rect.centerx = self.hitbox.centerx
                    
                if direction == "vertical":
                    if self.direction.y > 0: # Caminando hacia abajo
                        self.hitbox.bottom = obstacle_box.top
                    if self.direction.y < 0: # Caminando hacia arriba
                        self.hitbox.top = obstacle_box.bottom
                    self.pos.y = self.hitbox.y
                    self.rect.bottom = self.hitbox.bottom

    def update(self, dt, obstacle_sprites):
        """Ahora requiere obligatoriamente conocer los obstáculos del mapa"""
        self.move(dt, obstacle_sprites)