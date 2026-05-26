import pygame
import random

class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, groups, color):
        super().__init__(groups)
        
        # Tamaño aleatorio para que los fragmentos no sean idénticos
        size = random.randint(3, 6)
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        
        # Físicas de la partícula (Posición flotante para precisión decimal)
        self.pos = pygame.math.Vector2(pos)
        
        # Dirección aleatoria: saltan hacia arriba y a los lados
        self.direction = pygame.math.Vector2(
            random.uniform(-1, 1), 
            random.uniform(-2, -0.5) # Vector negativo para que salte hacia arriba
        )
        # Velocidad aleatoria
        self.speed = random.uniform(100, 200)
        
        # Gravedad que empujará la partícula hacia abajo con el tiempo
        self.gravity = 400
        
        # Duración de la partícula (Transparencia/Alfa)
        self.alpha = 255
        self.fade_speed = random.uniform(300, 500) # Qué tan rápido desaparece

    def update(self, dt):
        # 1. Aplicar gravedad a la dirección vertical
        self.direction.y += (self.gravity * dt) / self.speed
        
        # 2. Mover la partícula basados en dirección, velocidad y Delta Time
        self.pos += self.direction * self.speed * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))
        
        # 3. Desvanecimiento gradual (Fade out)
        self.alpha -= self.fade_speed * dt
        if self.alpha <= 0:
            self.kill() # Se auto-elimina del juego cuando se vuelve completamente invisible
        else:
            self.image.set_alpha(int(self.alpha))


class ParticleManager:
    def __init__(self, visible_sprites_group):
        """
        Administra la creación en masa de efectos visuales.
        Necesita el grupo de renderizado de la cámara para que las partículas se dibujen en el mundo.
        """
        self.visible_sprites = visible_sprites_group
        self.particle_group = pygame.sprite.Group()

    def create_hit_particles(self, pos, resource_type):
        """Genera una ráfaga de fragmentos en la posición del impacto"""
        # Elegir el color del fragmento según lo que golpeamos
        color = (139, 69, 19) if resource_type == "tree" else (160, 160, 160)
        
        # Crear entre 5 y 8 partículas por cada golpe einzeln
        num_particles = random.randint(5, 8)
        for _ in range(num_particles):
            # Las metemos tanto en el renderizador de la cámara como en nuestro grupo de control
            Particle(pos, [self.visible_sprites, self.particle_group], color)

    def update(self, dt):
        """Actualiza la física y desvanecimiento de todas las partículas activas"""
        self.particle_group.update(dt)