"""Efectos visuales: fondo con estrellas en movimiento (parallax) y partículas."""
import random

import pygame

from . import config as C


class Starfield:
    """Fondo que se desplaza despacio con tres capas de estrellas a distinta velocidad."""

    LAYERS = (  # (cantidad, velocidad px/s, brillo, tamaño)
        (60, 25, 110, 1),
        (35, 60, 180, 1),
        (15, 120, 255, 2),
    )
    BACKGROUND_SPEED = 12

    def __init__(self, background):
        self.background = background
        self.bg_offset = 0.0
        self.layers = []
        for count, speed, brightness, size in self.LAYERS:
            stars = [[random.uniform(0, C.WIDTH), random.uniform(0, C.HEIGHT)] for _ in range(count)]
            self.layers.append((stars, speed, (brightness,) * 3, size))

    def update(self, dt, speed_factor=1.0):
        bg_height = self.background.get_height()
        self.bg_offset = (self.bg_offset + self.BACKGROUND_SPEED * dt * speed_factor) % bg_height
        for stars, speed, _, _ in self.layers:
            for star in stars:
                star[1] += speed * dt * speed_factor
                if star[1] > C.HEIGHT:
                    star[0] = random.uniform(0, C.WIDTH)
                    star[1] -= C.HEIGHT

    def draw(self, surface):
        bg_height = self.background.get_height()
        y = int(self.bg_offset)
        surface.blit(self.background, (0, y - bg_height))
        surface.blit(self.background, (0, y))
        for stars, _, color, size in self.layers:
            for x, y in stars:
                if size == 1:
                    surface.set_at((int(x), int(y)), color)
                else:
                    pygame.draw.circle(surface, color, (int(x), int(y)), size)


class Particles:
    """Sistema de partículas simple (chispas de explosiones y propulsor de la nave)."""

    def __init__(self):
        self.items = []  # [x, y, vx, vy, vida, vida_total, color, tamaño]

    def emit(self, pos, count, colors, speed=(40, 220), life=(0.3, 0.8), size=(2, 4),
             direction=None, spread=None):
        for _ in range(count):
            if direction is None:
                velocity = pygame.Vector2(random.uniform(*speed), 0).rotate(random.uniform(0, 360))
            else:
                velocity = pygame.Vector2(direction).rotate(random.uniform(-spread, spread))
                velocity.scale_to_length(random.uniform(*speed))
            total = random.uniform(*life)
            self.items.append([pos[0], pos[1], velocity.x, velocity.y, total, total,
                               random.choice(colors), random.uniform(*size)])

    def explosion(self, pos, scale=1.0):
        count = int(18 * scale)
        self.emit(pos, count, [(255, 230, 120), (255, 160, 50), (255, 90, 30), (200, 200, 200)],
                  speed=(60 * scale, 260 * scale), size=(1.5, 2.5 + scale))

    def update(self, dt):
        alive = []
        for p in self.items:
            p[4] -= dt
            if p[4] > 0:
                p[0] += p[2] * dt
                p[1] += p[3] * dt
                p[2] *= 0.97
                p[3] *= 0.97
                alive.append(p)
        self.items = alive

    def draw(self, surface):
        for x, y, _, _, life, total, color, size in self.items:
            k = life / total
            radius = max(1, int(size * k + 0.5))
            faded = (int(color[0] * k), int(color[1] * k), int(color[2] * k))
            pygame.draw.circle(surface, faded, (int(x), int(y)), radius)

    def clear(self):
        self.items.clear()
