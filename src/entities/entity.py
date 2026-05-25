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
        self.image = pygame.Surface((32, 48)) # Proporción estándar tipo Stardew Valley
        self.image.fill((200, 200, 200))      # Gris por defecto
        self.rect = self.image.get_rect(topleft=self.pos)

    def move(self, dt):
        """Aplica el movimiento basado en la dirección y el Delta Time"""
        # Normalizar el vector para evitar que camine más rápido en diagonal
        if self.direction.length() > 0:
            self.direction = self.direction.normalize()
            
        # Fórmula física estándar: Posición = Dirección * Velocidad * Tiempo
        self.pos += self.direction * self.speed * dt
        
        # Sincronizar el rectángulo de colisión de Pygame con la posición matemática
        self.rect.topleft = (round(self.pos.x), round(self.pos.y))

    def update(self, dt):
        """Cada entidad sobreescribirá este método con su propia lógica (IA o Teclado)"""
        self.move(dt)