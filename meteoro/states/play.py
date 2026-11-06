"""La partida. También hace de "mundo" para los sprites: les da imágenes, sonido,
entrada, nivel, dificultad y formas de crear balas o enemigos."""
import math
import random

import pygame

from .. import collisions, hud, rules, ui
from .. import config as C
from ..effects import Particles
from ..i18n import t
from ..spawner import Spawner
from ..sprites import EnemyBullet, Explosion, Player, PowerUp
from .base import State


class PlayState(State):
    def __init__(self, game):
        super().__init__(game)
        self.images = game.images
        self.audio = game.audio
        self.input = game.input
        self.difficulty = game.settings["difficulty"]
        self.particles = Particles()

        self.now = 0.0                  # reloj de la partida (se detiene en pausa)
        self.world_now = 0.0            # reloj de meteoros y enemigos (va lento con la cámara lenta)
        self.score = 0
        self.level = 1
        self.lives = C.PLAYER_LIVES
        self.combo = 0
        self.best_combo = 0
        self.phase = "playing"          # playing | respawning | dying
        self.phase_until = 0.0
        self.shake_until = 0.0
        self.flash_until = 0.0
        self.magnet_until = 0.0
        self.slow_until = 0.0
        self.banner = None              # (texto, color, desde, hasta)
        self.popups = []                # [texto, x, y, vida, color]

        self.meteors = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bosses = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()

        self.player = Player(self)
        self.player.invulnerable_until = C.INVULNERABLE_TIME
        self.spawner = Spawner(self)
        self.spawner.fill_meteors()
        self.audio.play_music()

    # --- Interfaz que usan los sprites ---
    def spawn_enemy_bullet(self, pos, velocity, big=False):
        if big:
            bullet = EnemyBullet(self.images.boss_bullet, pos, velocity, radius=9)
        else:
            bullet = EnemyBullet(self.images.enemy_bullet, pos, velocity)
        self.enemy_bullets.add(bullet)

    def spawn_enemy(self, kind, pos=None):
        return self.spawner.spawn_enemy(kind, pos)

    def on_miss(self):
        self.combo = 0

    def magnet_active(self):
        return self.now < self.magnet_until

    def slow_active(self):
        return self.now < self.slow_until

    # --- Utilidades ---
    @property
    def boss(self):
        return next(iter(self.bosses), None)

    def multiplier(self):
        return rules.multiplier_for_combo(self.combo)

    def add_score(self, points, pos=None, color=C.WHITE):
        gained = points * self.multiplier()
        old = self.score
        self.score += gained
        if pos is not None:
            label = "+{}".format(gained)
            if self.multiplier() > 1:
                label += " x{}".format(self.multiplier())
            self.popup(label, pos, color)
        if rules.lives_earned(old, self.score) > 0:
            self.gain_life()

    def gain_life(self):
        if self.lives < C.MAX_LIVES:
            self.lives += 1
            self.audio.play("life")
            self.popup(t("popup.life"), self.player.rect.midtop, C.GREEN)

    def popup(self, text, pos, color=C.WHITE):
        # Si hay textos recientes en el mismo sitio, el nuevo se coloca encima
        x, y = pos
        for other in self.popups:
            if other[3] > 0.55 and abs(other[1] - x) < 80 and abs(other[2] - y) < 20:
                y = other[2] - 22
        self.popups.append([text, x, y, 0.8, color])

    def show_banner(self, key, color=C.WHITE, duration=C.LEVEL_MSG_TIME, **values):
        # Se guarda la clave (no el texto) para que el idioma se aplique al dibujar
        self.banner = ({"key": key, "values": values}, color, self.now, self.now + duration)

    def shake(self, duration=C.SHAKE_TIME):
        self.shake_until = max(self.shake_until, self.now + duration)

    def explode(self, pos, size, particles=1.0, sound=True):
        self.explosions.add(Explosion(self, pos, size))
        self.particles.explosion(pos, particles)
        if sound:
            self.audio.play("explosion")

    def maybe_drop_powerup(self, pos, chance):
        if random.random() < chance:
            self.powerups.add(PowerUp(self, pos))

    # --- Destrucción de cosas ---
    def destroy_meteor(self, meteor, split=True):
        meteor.kill()
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        self.add_score(rules.meteor_points(meteor.size), meteor.rect.center)
        scale = {"big": 1.4, "med": 1.0, "small": 0.7, "tiny": 0.5}[meteor.size]
        self.explode(meteor.rect.center, C.METEOR_EXPLOSION[meteor.size], scale)
        self.maybe_drop_powerup(meteor.rect.center, C.POWERUP_CHANCE)
        if split:
            self.meteors.add(*meteor.fragments())

    def destroy_ship(self, ship):
        if ship.kind == "boss":
            self.destroy_boss(ship)
            return
        ship.kill()
        self.combo += 1
        self.best_combo = max(self.best_combo, self.combo)
        self.add_score(ship.points, ship.rect.center, C.YELLOW)
        self.explode(ship.rect.center, 90, 1.5)
        self.maybe_drop_powerup(ship.rect.center, 0.4)

    def destroy_boss(self, boss):
        boss.kill()
        self.add_score(boss.points, boss.rect.center, C.PURPLE)
        for _ in range(6):
            offset = pygame.Vector2(random.uniform(-70, 70), random.uniform(-60, 60))
            self.explode(boss.pos + offset, random.choice((100, 130, 160)), 2.0, sound=False)
        self.audio.play("bomb")
        self.shake(0.8)
        for kind in ("shield", "weapon", random.choice(("bubble", "magnet", "life"))):
            pos = boss.pos + pygame.Vector2(random.uniform(-60, 60), 0)
            self.powerups.add(PowerUp(self, pos, kind))
        self.show_banner("banner.boss_down", C.YELLOW)

    def detonate_bomb(self):
        self.audio.play("bomb")
        self.flash_until = self.now + 0.15
        self.shake(0.5)
        for meteor in list(self.meteors):
            self.destroy_meteor(meteor, split=False)
        for enemy in list(self.enemies):
            self.destroy_ship(enemy)
        self.enemy_bullets.empty()
        boss = self.boss
        if boss and boss.damage(10, self.world_now):
            self.destroy_boss(boss)

    def apply_powerup(self, kind):
        player = self.player
        pos = player.rect.midtop
        if kind == "shield":
            player.shield = min(100, player.shield + C.SHIELD_RESTORE)
            self.popup(t("popup.shield"), pos, C.GREEN)
        elif kind == "weapon":
            player.upgrade_weapon(self.now)
            self.popup(t("popup.double") if player.weapon_level == 2 else t("popup.triple"), pos, C.YELLOW)
        elif kind == "bomb":
            self.detonate_bomb()
        elif kind == "bubble":
            player.bubble = True
            self.popup(t("popup.bubble"), pos, C.CYAN)
        elif kind == "magnet":
            self.magnet_until = self.now + C.MAGNET_TIME
            self.popup(t("popup.magnet"), pos, C.ORANGE)
        elif kind == "slow":
            self.slow_until = self.now + C.SLOW_TIME
            self.popup(t("popup.slow"), pos, C.BLUE)
        elif kind == "life":
            self.gain_life()
            return  # gain_life ya suena
        self.audio.play(kind)

    def damage_player(self, damage, pos):
        player = self.player
        self.combo = 0
        self.shake()
        if player.bubble:
            # La burbuja absorbe el golpe entero
            player.bubble = False
            player.invulnerable_until = self.now + C.INVULNERABLE_TIME
            self.audio.play("bubble_pop")
            self.particles.emit(player.rect.center, 24, [(120, 220, 255), (200, 240, 255)],
                                speed=(120, 260), life=(0.3, 0.6))
            return
        player.take_hit(rules.scaled_damage(damage, self.difficulty), self.now)
        self.explode(pos, 60, 0.8)
        if player.shield <= 0:
            self.lose_life()

    def lose_life(self):
        player = self.player
        self.lives -= 1
        player.alive_ship = False
        player.shield = 0
        self.explode(player.rect.center, 150, 2.5)
        self.shake(0.6)
        if self.lives > 0:
            self.phase, self.phase_until = "respawning", self.now + C.RESPAWN_DELAY
        else:
            self.phase, self.phase_until = "dying", self.now + C.DEATH_DELAY
            self.audio.stop_music()

    # --- Eventos ---
    def handle(self, event, actions):
        if "pause" in actions or event.type == pygame.WINDOWFOCUSLOST:
            if self.phase != "dying":
                self.game.go("pause", self, fade=False)

    # --- Lógica ---
    def update(self, dt):
        self.now += dt
        world_dt = dt * (C.SLOW_FACTOR if self.slow_active() else 1.0)
        self.world_now += world_dt
        self.game.starfield.update(world_dt, 1.6)

        if self.input.fire_held() and self.phase == "playing":
            new_bullets = self.player.try_shoot(self.now)
            if new_bullets:
                self.bullets.add(*new_bullets)
                self.audio.play("laser")

        # Meteoros, enemigos y sus balas usan el reloj lento; el resto, el normal
        for group in (self.meteors, self.enemy_bullets, self.enemies, self.bosses):
            group.update(world_dt, self.world_now)
        for group in (self.bullets, self.powerups, self.explosions):
            group.update(dt, self.now)
        self.player.update(dt, self.now)
        self.particles.update(dt)
        self._update_popups(dt)

        self.spawner.update()
        collisions.resolve(self)
        self._progress()
        self._phases()

    def _progress(self):
        new_level = rules.level_for_score(self.score)
        if new_level > self.level:
            self.level = new_level
            if not rules.is_boss_level(self.level):
                self.show_banner("banner.level", n=self.level)
            self.audio.play("level")
            self.particles.emit((C.WIDTH // 2, C.HEIGHT // 3 + 20), 40,
                                [(120, 220, 255), (255, 255, 255), (255, 220, 60)],
                                speed=(150, 380), life=(0.5, 1.0), size=(2, 4))

    def _phases(self):
        now = self.now
        if self.phase == "respawning" and now >= self.phase_until:
            player = self.player
            player.alive_ship = True
            player.shield = 100
            player.weapon_level = 1
            player.bubble = False
            player.reset_position()
            player.invulnerable_until = now + C.RESPAWN_INVULNERABLE_TIME
            self.enemy_bullets.empty()
            self.phase = "playing"
        elif self.phase == "dying" and now >= self.phase_until:
            self.game.go("gameover", self.score, self.level, self.best_combo, self.difficulty)

    def _update_popups(self, dt):
        for p in self.popups:
            p[2] -= 40 * dt
            p[3] -= dt
        self.popups = [p for p in self.popups if p[3] > 0]

    # --- Dibujo ---
    def offset(self):
        if self.now < self.shake_until and self.game.settings["screen_shake"]:
            return (random.randint(-C.SHAKE_INTENSITY, C.SHAKE_INTENSITY),
                    random.randint(-C.SHAKE_INTENSITY, C.SHAKE_INTENSITY))
        return (0, 0)

    def draw(self, surface):
        self.game.starfield.draw(surface)
        if self.slow_active():
            ui.dim(surface, 50)
        pulse = 150 + int(80 * math.sin(self.now * 6))
        for powerup in self.powerups:
            glow = powerup.glow
            glow.set_alpha(pulse)
            surface.blit(glow, glow.get_rect(center=powerup.rect.center))
        for group in (self.powerups, self.meteors, self.enemies, self.bosses):
            group.draw(surface)
        self.particles.draw(surface)
        self.bullets.draw(surface)
        self.enemy_bullets.draw(surface)
        player = self.player
        surface.blit(player.image, player.rect)
        if player.bubble and player.alive_ship:
            bubble = self.images.bubble
            surface.blit(bubble, bubble.get_rect(center=(player.rect.centerx, player.rect.centery - 6)))
        self.explosions.draw(surface)
        for text, x, y, _life, color in self.popups:
            ui.draw_text(surface, text, 22, x, y, color=color, anchor="center")
        hud.draw(self, surface)
        if self.now < self.flash_until:
            surface.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)
