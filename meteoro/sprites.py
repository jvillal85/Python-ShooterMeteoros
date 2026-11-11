"""Sprites del juego. Todos se mueven en píxeles por segundo: update(dt, now) recibe
el tiempo del paso (dt) y el reloj de la partida (now), que se detiene en pausa.
Con la cámara lenta, meteoros, enemigos y sus balas reciben un dt y un reloj más lentos."""
import math
import random

import pygame

from . import config as C
from . import rules


def flash_image(image):
    """Versión blanqueada de una imagen, para el destello al recibir un golpe."""
    flashed = image.copy()
    flashed.fill((180, 180, 180, 0), special_flags=pygame.BLEND_RGBA_ADD)
    return flashed


class Player(pygame.sprite.Sprite):
    def __init__(self, world):
        super().__init__()
        self.world = world
        self.base_image = world.images.player
        self.blank = pygame.Surface(self.base_image.get_size(), pygame.SRCALPHA)
        self.image = self.base_image
        self.rect = self.image.get_rect()
        # Radio de colisión algo menor que la imagen, para que los choques sean justos
        self.radius = int(self.rect.width * 0.36)
        self.pos = pygame.Vector2(C.WIDTH / 2, C.HEIGHT - 10 - self.rect.height / 2)
        self.rect.center = self.pos
        self.shield = 100
        self.invulnerable_until = 0.0
        self.weapon_level = 1
        self.weapon_until = 0.0
        self.bubble = False
        self.last_shot = -1.0
        self.alive_ship = True

    def reset_position(self):
        self.pos.x = C.WIDTH / 2
        self.rect.center = self.pos

    def is_invulnerable(self, now):
        return now < self.invulnerable_until or not self.alive_ship

    def take_hit(self, damage, now):
        self.shield -= damage
        self.invulnerable_until = now + C.INVULNERABLE_TIME

    def upgrade_weapon(self, now):
        self.weapon_level = min(3, self.weapon_level + 1)
        self.weapon_until = now + C.WEAPON_TIME

    def try_shoot(self, now):
        """Dispara si ya pasó la pausa mínima entre disparos. Devuelve las balas creadas."""
        if not self.alive_ship or now - self.last_shot < C.FIRE_COOLDOWN:
            return []
        self.last_shot = now
        x, y = self.rect.centerx, self.rect.top + 10
        volley = Volley(self.world)
        if self.weapon_level == 1:
            shots = [(x, y, 0)]
        elif self.weapon_level == 2:
            shots = [(x - 18, y + 8, 0), (x + 18, y + 8, 0)]
        else:
            shots = [(x, y, 0), (x - 20, y + 8, -12), (x + 20, y + 8, 12)]
        return [Bullet(self.world.images.bullet, sx, sy, angle, volley) for sx, sy, angle in shots]

    def update(self, dt, now):
        if self.weapon_level > 1 and now >= self.weapon_until:
            self.weapon_level = 1

        if self.alive_ship:
            self.pos.x += self.world.input.horizontal() * C.PLAYER_SPEED * dt
            half = self.rect.width / 2
            self.pos.x = max(half, min(C.WIDTH - half, self.pos.x))
            self.rect.center = (round(self.pos.x), round(self.pos.y))
            # Propulsor
            if random.random() < dt * 60:
                self.world.particles.emit(
                    (self.rect.centerx + random.uniform(-6, 6), self.rect.bottom - 18), 1,
                    [(255, 200, 80), (255, 140, 40), (120, 180, 255)],
                    speed=(80, 160), life=(0.15, 0.35), size=(1.5, 3.5), direction=(0, 1), spread=12)

        # Parpadeo mientras la nave es invulnerable (o invisible si fue destruida)
        if not self.alive_ship:
            self.image = self.blank
        elif now < self.invulnerable_until and int(now / C.BLINK_TIME) % 2:
            self.image = self.blank
        else:
            self.image = self.base_image


class Meteor(pygame.sprite.Sprite):
    def __init__(self, world, size, pos=None, velocity=None):
        super().__init__()
        self.world = world
        self.size = size
        self.base_image = random.choice(world.images.meteors[size])
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.radius = int(min(self.rect.width, self.rect.height) * 0.45)
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-90, 90)
        if pos is None:
            self.pos = pygame.Vector2(random.uniform(self.rect.width / 2, C.WIDTH - self.rect.width / 2),
                                      random.uniform(-140, -60))
            slow, fast = rules.meteor_speed_range(world.level, world.difficulty)
            self.vel = pygame.Vector2(random.uniform(-120, 120), random.uniform(slow, fast))
        else:
            self.pos = pygame.Vector2(pos)
            self.vel = pygame.Vector2(velocity)
        self.rect.center = self.pos

    def update(self, dt, now):
        self.pos += self.vel * dt
        self.angle = (self.angle + self.rot_speed * dt) % 360
        self.image = self.world.images.rotated(self.base_image, self.angle)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        if self.pos.y - 80 > C.HEIGHT or self.pos.x < -80 or self.pos.x > C.WIDTH + 80:
            self.kill()

    def fragments(self):
        """Meteoros más pequeños que salen al destruir este, o [] si no se parte."""
        new_size = rules.split_size(self.size)
        if not new_size:
            return []
        result = []
        for i in range(C.METEOR_FRAGMENTS):
            side = -1 if i % 2 == 0 else 1
            vel = pygame.Vector2(side * random.uniform(60, 160),
                                 max(120.0, self.vel.y * random.uniform(0.7, 1.1)))
            pos = self.pos + pygame.Vector2(side * self.rect.width / 4, 0)
            result.append(Meteor(self.world, new_size, pos, vel))
        return result


class Volley:
    """Grupo de balas disparadas juntas. Si ninguna acierta, se pierde el combo."""

    def __init__(self, world):
        self.world = world
        self.hit = False

    def bullet_hit(self):
        self.hit = True

    def bullet_missed(self):
        if not self.hit:
            self.hit = True  # cuenta solo una vez por ráfaga
            self.world.on_miss()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, image, x, y, angle, volley):
        super().__init__()
        self.image = pygame.transform.rotate(image, -angle) if angle else image
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.Vector2(self.rect.center)
        self.vel = pygame.Vector2(0, -C.BULLET_SPEED).rotate(angle)
        self.volley = volley
        self.radius = 6  # la imagen tiene mucho borde vacío: el choque usa solo el centro

    def update(self, dt, now):
        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > C.WIDTH:
            self.volley.bullet_missed()
            self.kill()


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, image, pos, velocity, radius=5):
        super().__init__()
        angle = pygame.Vector2(0, 1).angle_to(velocity)
        self.image = pygame.transform.rotate(image, -angle)
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(velocity)
        self.rect = self.image.get_rect(center=self.pos)
        self.radius = radius

    def update(self, dt, now):
        self.pos += self.vel * dt
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        if not (-30 < self.pos.y < C.HEIGHT + 30 and -30 < self.pos.x < C.WIDTH + 30):
            self.kill()


class Ship(pygame.sprite.Sprite):
    """Base de las naves enemigas: vida, destello al recibir daño y disparos."""
    kind = "ship"
    points = 0

    def __init__(self, world, image, hp):
        super().__init__()
        self.world = world
        self.base_image = image
        self.flash = flash_image(image)
        self.image = image
        self.rect = image.get_rect()
        self.radius = int(self.rect.width * 0.4)
        self.hp = self.max_hp = hp
        self.flash_until = 0.0

    def damage(self, amount, now):
        self.hp -= amount
        self.flash_until = now + 0.08
        return self.hp <= 0

    def fire_interval(self, low, high):
        return rules.enemy_fire_interval(random.uniform(low, high), self.world.difficulty)

    def shoot_at(self, target, speed, spread=0.0, count=1, origin=None, big=False):
        origin = pygame.Vector2(origin or self.rect.midbottom)
        direction = pygame.Vector2(target) - origin
        if direction.length_squared() == 0:
            direction = pygame.Vector2(0, 1)
        direction.scale_to_length(speed)
        for i in range(count):
            offset = (i - (count - 1) / 2) * spread
            self.world.spawn_enemy_bullet(origin, direction.rotate(offset), big)

    def _update_image(self, now):
        self.image = self.flash if now < self.flash_until else self.base_image


class Shooter(Ship):
    """Nave enemiga: baja, se mueve de lado a lado disparando al jugador y luego se va."""
    kind = "shooter"

    def __init__(self, world, now):
        data = C.ENEMY_TYPES[self.kind]
        super().__init__(world, world.images.enemies[self.kind], data["hp"])
        self.points = data["points"]
        self.pos = pygame.Vector2(random.uniform(60, C.WIDTH - 60), -40)
        self.target_y = random.uniform(60, 170)
        self.base_x = self.pos.x
        self.phase = random.uniform(0, math.tau)
        self.born = now
        self.leave_at = now + random.uniform(10, 14)
        self.next_shot = now + random.uniform(1.0, 2.0)
        self.amplitude = 150
        self.sway_speed = 1.3
        self.rect.center = self.pos

    def attack(self):
        self.shoot_at(self.world.player.rect.center, C.ENEMY_BULLET_SPEED)
        self.next_shot_delay = self.fire_interval(1.2, 2.2)

    def update(self, dt, now):
        if now >= self.leave_at:
            self.pos.y += 220 * dt
            if self.pos.y > C.HEIGHT + 50:
                self.kill()
        elif self.pos.y < self.target_y:
            self.pos.y += 160 * dt
        else:
            t = now - self.born
            self.pos.x = self.base_x + math.sin(t * self.sway_speed + self.phase) * self.amplitude
            self.pos.x = max(40, min(C.WIDTH - 40, self.pos.x))
            if now >= self.next_shot and self.world.player.alive_ship:
                self.attack()
                self.next_shot = now + self.next_shot_delay
                self.world.audio.play("enemy_laser")
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self._update_image(now)


class Spreader(Shooter):
    """Nave más resistente que dispara abanicos de tres balas."""
    kind = "spreader"

    def __init__(self, world, now):
        super().__init__(world, now)
        self.amplitude = 100
        self.sway_speed = 0.8

    def attack(self):
        self.shoot_at(self.world.player.rect.center, C.ENEMY_BULLET_SPEED * 0.85, spread=18, count=3)
        self.next_shot_delay = self.fire_interval(2.0, 2.8)


class Kamikaze(Ship):
    """Baja, apunta un instante (parpadea) y se lanza en línea recta hacia el jugador."""
    kind = "kamikaze"

    def __init__(self, world, now, pos=None):
        data = C.ENEMY_TYPES[self.kind]
        super().__init__(world, world.images.enemies[self.kind], data["hp"])
        self.points = data["points"]
        self.pos = pygame.Vector2(pos) if pos else pygame.Vector2(random.uniform(60, C.WIDTH - 60), -40)
        self.target_y = random.uniform(70, 150)
        self.state = "enter"
        self.aim_until = 0.0
        self.vel = pygame.Vector2()
        self.rect.center = self.pos

    def update(self, dt, now):
        if self.state == "enter":
            self.pos.y += 180 * dt
            if self.pos.y >= self.target_y:
                self.state, self.aim_until = "aim", now + 0.7
        elif self.state == "aim":
            self.pos.x += math.sin(now * 40) * 60 * dt
            self.flash_until = now + 0.05 if int(now * 12) % 2 else 0
            if now >= self.aim_until:
                direction = pygame.Vector2(self.world.player.rect.center) - self.pos
                if direction.length_squared() == 0:
                    direction = pygame.Vector2(0, 1)
                self.vel = direction.normalize() * C.KAMIKAZE_SPEED
                self.state = "dive"
        else:
            self.pos += self.vel * dt
            if not (-80 < self.pos.y < C.HEIGHT + 80 and -80 < self.pos.x < C.WIDTH + 80):
                self.kill()
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self._update_image(now)


ENEMY_CLASSES = {"shooter": Shooter, "kamikaze": Kamikaze, "spreader": Spreader}


class Boss(Ship):
    """Jefe: entra, se mueve de lado a lado y alterna ataques. Cada aparición suma uno nuevo:
    abanico, ráfaga dirigida, espiral y, desde el tercer jefe, llamar a kamikazes."""
    kind = "boss"

    def __init__(self, world, now, level):
        super().__init__(world, world.images.boss, rules.boss_hp(level))
        self.points = C.BOSS_POINTS
        self.radius = int(self.rect.width * 0.4)
        self.pos = pygame.Vector2(C.WIDTH / 2, -110)
        self.target_y = 130
        self.born = now
        self.next_attack = now + 2.0
        self.attacks = rules.boss_attacks(level)
        self.attack_index = 0
        self.spiral_angle = 0.0
        self.rect.center = self.pos

    @property
    def angry(self):
        return self.hp < self.max_hp / 2

    def update(self, dt, now):
        if self.pos.y < self.target_y:
            self.pos.y += 90 * dt
        else:
            speed = 1.1 if self.angry else 0.7
            self.pos.x = C.WIDTH / 2 + math.sin((now - self.born) * speed) * (C.WIDTH / 2 - 120)
            if now >= self.next_attack and self.world.player.alive_ship:
                self._attack()
                delay = 1.1 if self.angry else 1.6
                self.next_attack = now + rules.enemy_fire_interval(delay, self.world.difficulty)
        self.rect.center = (round(self.pos.x), round(self.pos.y))
        self._update_image(now)

    def _attack(self):
        attack = self.attacks[self.attack_index % len(self.attacks)]
        self.attack_index += 1
        bottom = (self.rect.centerx, self.rect.bottom - 30)
        if attack == "fan":
            count = 7 if self.angry else 5
            self.shoot_at((self.rect.centerx, C.HEIGHT), 230, spread=16, count=count, origin=bottom, big=True)
        elif attack == "aimed":
            for dx in (-55, 55):
                origin = (self.rect.centerx + dx, self.rect.bottom - 40)
                self.shoot_at(self.world.player.rect.center, 340, spread=8,
                              count=3 if self.angry else 2, origin=origin)
        elif attack == "spiral":
            count = 14
            for i in range(count):
                direction = pygame.Vector2(0, 170).rotate(self.spiral_angle + i * 360 / count)
                self.world.spawn_enemy_bullet(self.rect.center, direction, True)
            self.spiral_angle += 12
        elif attack == "summon":
            for dx in (-90, 90):
                self.world.spawn_enemy("kamikaze", (self.rect.centerx + dx, self.rect.centery))
        self.world.audio.play("enemy_laser")


class PowerUp(pygame.sprite.Sprite):
    def __init__(self, world, pos, kind=None):
        super().__init__()
        self.world = world
        kinds = list(C.POWERUP_WEIGHTS)
        self.kind = kind or random.choices(kinds, [C.POWERUP_WEIGHTS[k] for k in kinds])[0]
        self.image = world.images.powerups[self.kind]
        self.glow = world.images.powerup_glows[self.kind]
        self.pos = pygame.Vector2(pos)
        self.rect = self.image.get_rect(center=self.pos)
        self.radius = self.rect.width // 2 + 6
        self.phase = random.uniform(0, math.tau)

    def update(self, dt, now):
        player = self.world.player
        to_player = pygame.Vector2(player.rect.center) - self.pos
        if (self.world.magnet_active() and player.alive_ship
                and 0 < to_player.length() < C.MAGNET_RADIUS):
            self.pos += to_player.normalize() * C.MAGNET_PULL * dt
        else:
            self.pos.y += C.POWERUP_SPEED * dt
        x = self.pos.x + math.sin(now * 4 + self.phase) * 6
        self.rect.center = (round(x), round(self.pos.y))
        if self.rect.top > C.HEIGHT:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    FRAME_TIME = 0.05

    def __init__(self, world, center, size):
        super().__init__()
        self.frames = world.images.explosion(size)
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=center)
        self.frame = 0
        self.elapsed = 0.0

    def update(self, dt, now):
        self.elapsed += dt
        while self.elapsed >= self.FRAME_TIME:
            self.elapsed -= self.FRAME_TIME
            self.frame += 1
            if self.frame >= len(self.frames):
                self.kill()
                return
            center = self.rect.center
            self.image = self.frames[self.frame]
            self.rect = self.image.get_rect(center=center)
