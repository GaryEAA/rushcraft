import pygame
 
 
class Entity(pygame.sprite.Sprite):
    """
    Clase base para entidades móviles (player, enemigos).
 
    Modelo de geometría:
      - hitbox  → zona de colisión real, usada por move() y check_collisions()
      - rect    → coincide con hitbox (mismas dimensiones y posición)
      - image   → superficie del mismo tamaño que hitbox (sin píxeles sobrantes)
 
    La cámara dibuja usando hitbox directamente, así que lo que ves
    ES exactamente la zona de colisión.
    """
 
    # Tamaño de la hitbox de entidades (override en subclases si es necesario)
    HITBOX_W = 28
    HITBOX_H = 28
 
    def __init__(self, x, y, speed, max_health):
        super().__init__()
 
        self.pos       = pygame.math.Vector2(x, y)
        self.direction = pygame.math.Vector2(0, 0)
        self.speed     = speed
        self.max_health = max_health
        self.health    = max_health
 
        # Imagen = exactamente hitbox (placeholder; los sprites reales van aquí)
        self.image = pygame.Surface((self.HITBOX_W, self.HITBOX_H))
        self.image.fill((200, 200, 200))
 
        # rect y hitbox coinciden desde el inicio
        self.rect   = self.image.get_rect(topleft=(x, y))
        self.hitbox = self.rect.copy()
 
    # ──────────────────────────────────────────────────────────────────
    #  Movimiento
    # ──────────────────────────────────────────────────────────────────
 
    def move(self, dt, obstacle_sprites):
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
 
        # Eje horizontal
        self.pos.x    += self.direction.x * self.speed * dt
        self.hitbox.x  = round(self.pos.x)
        self.rect.x    = self.hitbox.x
        self.check_collisions("horizontal", obstacle_sprites)
        self.pos.x     = self.hitbox.x
 
        # Eje vertical
        self.pos.y    += self.direction.y * self.speed * dt
        self.hitbox.y  = round(self.pos.y)
        self.rect.y    = self.hitbox.y
        self.check_collisions("vertical", obstacle_sprites)
        self.pos.y     = self.hitbox.y
 
    # ──────────────────────────────────────────────────────────────────
    #  Colisiones
    # ──────────────────────────────────────────────────────────────────
 
    def check_collisions(self, direction, obstacle_sprites):
        for sprite in obstacle_sprites:
            obstacle_box = sprite.hitbox if hasattr(sprite, "hitbox") else sprite.rect
 
            if self.hitbox.colliderect(obstacle_box):
                if direction == "horizontal":
                    if self.direction.x > 0:
                        self.hitbox.right = obstacle_box.left
                    elif self.direction.x < 0:
                        self.hitbox.left = obstacle_box.right
                    self.pos.x  = self.hitbox.x
                    self.rect.x = self.hitbox.x
 
                elif direction == "vertical":
                    if self.direction.y > 0:
                        self.hitbox.bottom = obstacle_box.top
                    elif self.direction.y < 0:
                        self.hitbox.top = obstacle_box.bottom
                    self.pos.y  = self.hitbox.y
                    self.rect.y = self.hitbox.y
 
    def update(self, dt, obstacle_sprites):
        self.move(dt, obstacle_sprites)
 