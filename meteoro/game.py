"""Bucle principal y estados del juego (menú, partida, pausa, game over...)."""
import random

import pygame

from . import config as C
from . import rules, storage, ui
from .assets import Audio, Images, path as asset_path
from .controls import Input
from .effects import Particles, Starfield
from .sprites import Boss, Bullet, Enemy, EnemyBullet, Explosion, Meteor, Player, PowerUp

NEW_METEOR_SIZES = ("big", "med", "small", "tiny")
NEW_METEOR_WEIGHTS = (50, 30, 14, 6)
NAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass  # sin dispositivo de sonido: el juego funciona en silencio

        self.settings = storage.load_settings()
        try:
            pygame.display.set_icon(pygame.image.load(asset_path("player.png")))
        except pygame.error:
            pass
        # SCALED: el juego se dibuja a 800x600 y se escala a la ventana o pantalla completa
        self.screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT), pygame.SCALED | pygame.RESIZABLE)
        pygame.display.set_caption(C.TITLE)
        if self.settings["fullscreen"]:
            self._toggle_fullscreen_display()

        self.canvas = pygame.Surface((C.WIDTH, C.HEIGHT))
        self.clock = pygame.time.Clock()
        self.images = Images()
        self.audio = Audio(self.settings)
        self.input = Input()
        self.starfield = Starfield(self.images.background)
        self.scores = storage.load_scores()
        self.running = True
        self.state = MenuState(self)

    # --- Opciones -------------------------------------------------------
    def save_settings(self):
        storage.save_settings(self.settings)

    def _toggle_fullscreen_display(self):
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            pass

    def toggle_fullscreen(self):
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        self._toggle_fullscreen_display()
        self.save_settings()

    def toggle_mute(self):
        self.audio.toggle_mute()
        self.save_settings()

    @property
    def high_score(self):
        return storage.top_score(self.scores)

    # --- Bucle principal --------------------------------------------------
    def set_state(self, state):
        self.state = state

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = min(self.clock.tick(C.FPS) / 1000.0, C.MAX_DT)
            self.step(dt, pygame.event.get())
        pygame.quit()

    def step(self, dt, events):
        """Un cuadro del juego: eventos, lógica y dibujo."""
        for event in events:
            if event.type == pygame.QUIT:
                self.quit()
                return
            if event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self.input.handle_device_event(event)
            actions = self.input.actions(event)
            if "mute" in actions:
                self.toggle_mute()
            if "fullscreen" in actions:
                self.toggle_fullscreen()
            self.state.handle(event, actions)

        self.state.update(dt)
        self.state.draw(self.canvas)
        self.screen.fill(C.BLACK)
        self.screen.blit(self.canvas, self.state.offset())
        pygame.display.flip()


class State:
    def __init__(self, game):
        self.game = game

    def handle(self, event, actions):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def offset(self):
        return (0, 0)


class WaitingState(State):
    """Pantalla que ignora teclas durante un instante, para no saltarla sin querer."""

    def __init__(self, game):
        super().__init__(game)
        self.elapsed = 0.0

    @property
    def ready(self):
        return self.elapsed >= C.START_DELAY

    def update(self, dt):
        self.elapsed += dt
        self.game.starfield.update(dt)


# --- Menús -------------------------------------------------------------------

class MenuState(WaitingState):
    OPTIONS = ("Jugar", "Opciones", "Controles", "Récords", "Salir")

    def __init__(self, game, selected=0):
        super().__init__(game)
        self.selected = selected
        self.elapsed = C.START_DELAY  # el menú responde al instante

    def handle(self, event, actions):
        if "up" in actions:
            self.selected = (self.selected - 1) % len(self.OPTIONS)
            self.game.audio.play("select")
        elif "down" in actions:
            self.selected = (self.selected + 1) % len(self.OPTIONS)
            self.game.audio.play("select")
        elif "accept" in actions:
            choice = self.OPTIONS[self.selected]
            if choice == "Jugar":
                self.game.set_state(PlayState(self.game))
            elif choice == "Opciones":
                self.game.set_state(OptionsState(self.game, back=lambda: MenuState(self.game, 1)))
            elif choice == "Controles":
                self.game.set_state(ControlsState(self.game))
            elif choice == "Récords":
                self.game.set_state(RecordsState(self.game))
            else:
                self.game.quit()

    def draw(self, surface):
        self.game.starfield.draw(surface)
        ui.draw_text(surface, "=[METEORO SHOOTER]=", 50, C.WIDTH // 2, 95, bold=True)
        ui.draw_text(surface, "Récord: {}".format(self.game.high_score), 26, C.WIDTH // 2, 175,
                     color=C.YELLOW)
        ui.draw_menu(surface, self.OPTIONS, self.selected, 250)
        ui.draw_text(surface, "Flechas / mando para elegir · ENTER para aceptar", 18,
                     C.WIDTH // 2, C.HEIGHT - 40, color=C.GREY)


class OptionsState(WaitingState):
    def __init__(self, game, back):
        super().__init__(game)
        self.back = back
        self.selected = 0
        self.elapsed = C.START_DELAY

    def _items(self):
        s = self.game.settings
        on_off = lambda v: "Sí" if v else "No"
        return [
            ("music", "Música: {}".format(self._bar(s["music_volume"]))),
            ("sfx", "Efectos: {}".format(self._bar(s["sfx_volume"]))),
            ("mute", "Silencio (M): {}".format(on_off(s["muted"]))),
            ("fullscreen", "Pantalla completa (F11): {}".format(on_off(s["fullscreen"]))),
            ("back", "Volver"),
        ]

    @staticmethod
    def _bar(value):
        filled = int(round(value * 10))
        return "[" + "|" * filled + "·" * (10 - filled) + "]"

    def _change_volume(self, key, delta):
        s = self.game.settings
        s[key] = round(min(1.0, max(0.0, s[key] + delta)), 1)
        self.game.audio.apply_volume()
        self.game.audio.play("select")

    def handle(self, event, actions):
        items = self._items()
        key = items[self.selected][0]
        if "up" in actions:
            self.selected = (self.selected - 1) % len(items)
        elif "down" in actions:
            self.selected = (self.selected + 1) % len(items)
        elif "left" in actions or "right" in actions:
            delta = 0.1 if "right" in actions else -0.1
            if key == "music":
                self._change_volume("music_volume", delta)
            elif key == "sfx":
                self._change_volume("sfx_volume", delta)
        elif "accept" in actions:
            if key == "mute":
                self.game.toggle_mute()
            elif key == "fullscreen":
                self.game.toggle_fullscreen()
            elif key == "back":
                self._leave()
        elif "back" in actions:
            self._leave()

    def _leave(self):
        self.game.save_settings()
        self.game.set_state(self.back())

    def draw(self, surface):
        self.game.starfield.draw(surface)
        ui.draw_text(surface, "OPCIONES", 56, C.WIDTH // 2, 70, bold=True)
        labels = [label for _, label in self._items()]
        ui.draw_menu(surface, labels, self.selected, 190, size=30, spacing=55)
        ui.draw_text(surface, "← → cambia el volumen · ENTER activa · ESC vuelve", 18,
                     C.WIDTH // 2, C.HEIGHT - 40, color=C.GREY)


class ControlsState(WaitingState):
    LINES = (
        ("Mover", "← →  o  A D  ·  stick / cruceta"),
        ("Disparar", "Mantén ESPACIO  ·  botón A"),
        ("Pausa", "P o ESC  ·  START"),
        ("Silencio", "M"),
        ("Pantalla completa", "F11"),
    )
    POWERUPS = (
        ("shield", "Escudo: recupera {} de escudo".format(C.SHIELD_RESTORE)),
        ("weapon", "Arma: disparo doble y luego triple ({} s)".format(int(C.WEAPON_TIME))),
        ("bomb", "Bomba: destruye todo lo que hay en pantalla"),
    )

    def __init__(self, game):
        super().__init__(game)
        self.elapsed = C.START_DELAY

    def handle(self, event, actions):
        if "accept" in actions or "back" in actions:
            self.game.set_state(MenuState(self.game, 2))

    def draw(self, surface):
        self.game.starfield.draw(surface)
        ui.draw_text(surface, "CONTROLES", 56, C.WIDTH // 2, 40, bold=True)
        y = 130
        for name, keys in self.LINES:
            ui.draw_text(surface, name, 24, C.WIDTH // 2 - 20, y, color=C.YELLOW, anchor="topright")
            ui.draw_text(surface, keys, 24, C.WIDTH // 2 + 20, y, anchor="topleft")
            y += 36
        y += 20
        for kind, text in self.POWERUPS:
            icon = self.game.images.powerups[kind]
            surface.blit(icon, icon.get_rect(midleft=(150, y + 14)))
            ui.draw_text(surface, text, 22, 195, y, anchor="topleft")
            y += 40
        ui.draw_text(surface, "Meteoros pequeños = más puntos · Aciertos seguidos = multiplicador",
                     19, C.WIDTH // 2, y + 15, color=C.CYAN)
        ui.draw_text(surface, "Vida extra cada {} puntos · Jefe cada {} niveles".format(
            C.EXTRA_LIFE_EVERY, C.BOSS_EVERY), 19, C.WIDTH // 2, y + 42, color=C.CYAN)
        ui.draw_text(surface, "ENTER o ESC para volver", 18, C.WIDTH // 2, C.HEIGHT - 40, color=C.GREY)


class RecordsState(WaitingState):
    def __init__(self, game, highlight=None, after_game=False):
        super().__init__(game)
        self.highlight = highlight
        self.after_game = after_game
        if not after_game:
            self.elapsed = C.START_DELAY

    def handle(self, event, actions):
        if not self.ready:
            return
        if self.after_game and "accept" in actions:
            self.game.set_state(PlayState(self.game))
        elif "accept" in actions or "back" in actions:
            self.game.set_state(MenuState(self.game, 3))

    def draw(self, surface):
        self.game.starfield.draw(surface)
        ui.draw_text(surface, "RÉCORDS", 56, C.WIDTH // 2, 35, bold=True)
        scores = self.game.scores
        if not scores:
            ui.draw_text(surface, "Todavía no hay récords. ¡Juega una partida!", 26,
                         C.WIDTH // 2, C.HEIGHT // 2 - 20)
        else:
            ui.draw_text(surface, "#", 22, 230, 115, color=C.GREY, anchor="topright")
            ui.draw_text(surface, "NOMBRE", 22, 270, 115, color=C.GREY, anchor="topleft")
            ui.draw_text(surface, "PUNTOS", 22, 520, 115, color=C.GREY, anchor="topright")
            ui.draw_text(surface, "NIVEL", 22, 600, 115, color=C.GREY, anchor="topright")
            for i, entry in enumerate(scores):
                y = 150 + i * 34
                color = C.YELLOW if i == self.highlight else C.WHITE
                ui.draw_text(surface, i + 1, 26, 230, y, color=color, anchor="topright")
                ui.draw_text(surface, entry["name"], 26, 270, y, color=color, anchor="topleft")
                ui.draw_text(surface, entry["score"], 26, 520, y, color=color, anchor="topright")
                ui.draw_text(surface, entry["level"], 26, 600, y, color=color, anchor="topright")
        hint = ("ENTER: jugar de nuevo · ESC: menú" if self.after_game else "ENTER o ESC para volver")
        if self.ready:
            ui.draw_text(surface, hint, 18, C.WIDTH // 2, C.HEIGHT - 40, color=C.GREY)


# --- Partida -----------------------------------------------------------------

class PlayState(State):
    """La partida. También hace de "mundo" para los sprites (imágenes, sonido, entrada...)."""

    def __init__(self, game):
        super().__init__(game)
        self.images = game.images
        self.audio = game.audio
        self.input = game.input
        self.particles = Particles()

        self.now = 0.0
        self.score = 0
        self.level = 1
        self.lives = C.PLAYER_LIVES
        self.combo = 0
        self.best_combo = 0
        self.phase = "playing"          # playing | respawning | dying
        self.phase_until = 0.0
        self.shake_until = 0.0
        self.flash_until = 0.0
        self.banner = None              # (texto, color, hasta)
        self.popups = []                # [texto, x, y, vida, color]
        self.next_enemy_at = 8.0
        self.boss_levels = set()

        self.meteors = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bosses = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()

        self.player = Player(self)
        self.player.invulnerable_until = C.INVULNERABLE_TIME
        self._fill_meteors()
        self.audio.play_music()

    # --- Interfaz que usan los sprites ---
    def spawn_enemy_bullet(self, pos, velocity):
        self.enemy_bullets.add(EnemyBullet(self.images.enemy_bullet, pos, velocity))

    def on_miss(self):
        self.combo = 0

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
        extra = rules.lives_earned(old, self.score)
        if extra > 0 and self.lives < C.MAX_LIVES:
            self.lives = min(C.MAX_LIVES, self.lives + extra)
            self.audio.play("life")
            self.popup("+1 VIDA", self.player.rect.midtop, C.GREEN)

    def popup(self, text, pos, color=C.WHITE):
        self.popups.append([text, pos[0], pos[1], 0.8, color])

    def show_banner(self, text, color=C.WHITE, duration=C.LEVEL_MSG_TIME):
        self.banner = (text, color, self.now + duration)

    def shake(self, duration=C.SHAKE_TIME):
        self.shake_until = max(self.shake_until, self.now + duration)

    def explode(self, pos, size, particles=1.0, sound=True):
        self.explosions.add(Explosion(self, pos, size))
        self.particles.explosion(pos, particles)
        if sound:
            self.audio.play("explosion")

    def _fill_meteors(self):
        target = rules.meteor_target(self.level, self.boss is not None)
        while len(self.meteors) < target:
            size = random.choices(NEW_METEOR_SIZES, NEW_METEOR_WEIGHTS)[0]
            self.meteors.add(Meteor(self, size))

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

    def destroy_enemy(self, enemy):
        enemy.kill()
        self.combo += 1
        self.add_score(C.ENEMY_POINTS, enemy.rect.center, C.YELLOW)
        self.explode(enemy.rect.center, 90, 1.5)
        self.maybe_drop_powerup(enemy.rect.center, 0.5)

    def destroy_boss(self, boss):
        boss.kill()
        self.add_score(C.BOSS_POINTS, boss.rect.center, C.PURPLE)
        for _ in range(6):
            offset = pygame.Vector2(random.uniform(-70, 70), random.uniform(-60, 60))
            self.explode(boss.pos + offset, random.choice((100, 130, 160)), 2.0, sound=False)
        self.audio.play("bomb")
        self.shake(0.8)
        for kind in ("shield", "weapon", random.choice(PowerUp.KINDS)):
            pos = boss.pos + pygame.Vector2(random.uniform(-60, 60), 0)
            self.powerups.add(PowerUp(self, pos, kind))
        self.show_banner("¡JEFE DERROTADO!", C.YELLOW)

    def detonate_bomb(self):
        self.audio.play("bomb")
        self.flash_until = self.now + 0.15
        self.shake(0.5)
        for meteor in list(self.meteors):
            self.destroy_meteor(meteor, split=False)
        for enemy in list(self.enemies):
            self.destroy_enemy(enemy)
        self.enemy_bullets.empty()
        boss = self.boss
        if boss and boss.damage(10, self.now):
            self.destroy_boss(boss)

    def apply_powerup(self, kind):
        player = self.player
        if kind == "shield":
            player.shield = min(100, player.shield + C.SHIELD_RESTORE)
            self.popup("+ESCUDO", player.rect.midtop, C.GREEN)
        elif kind == "weapon":
            player.upgrade_weapon(self.now)
            self.popup("DISPARO {}".format("DOBLE" if player.weapon_level == 2 else "TRIPLE"),
                       player.rect.midtop, C.CYAN)
        elif kind == "bomb":
            self.detonate_bomb()
        self.audio.play(kind)

    def damage_player(self, damage, pos):
        self.player.take_hit(damage, self.now)
        self.combo = 0
        self.shake()
        self.explode(pos, 60, 0.8)
        if self.player.shield <= 0:
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
                self.game.set_state(PauseState(self.game, self))

    # --- Lógica ---
    def update(self, dt):
        self.now += dt
        now = self.now
        self.game.starfield.update(dt, 1.6)

        if self.input.fire_held() and self.phase == "playing":
            new_bullets = self.player.try_shoot(now)
            if new_bullets:
                self.bullets.add(*new_bullets)
                self.audio.play("laser")

        for group in (self.meteors, self.bullets, self.enemy_bullets, self.enemies, self.bosses,
                      self.powerups, self.explosions):
            group.update(dt, now)
        self.player.update(dt, now)
        self.particles.update(dt)
        self._update_popups(dt)

        self._spawn(now)
        self._collisions(now)
        self._progress()
        self._phases(now)

    def _spawn(self, now):
        self._fill_meteors()
        if rules.is_boss_level(self.level) and self.level not in self.boss_levels:
            self.boss_levels.add(self.level)
            if self.boss is None:
                self.bosses.add(Boss(self, now, rules.boss_hp(self.level)))
                self.show_banner("¡CUIDADO: JEFE!", C.PURPLE, 2.5)
        if (now >= self.next_enemy_at and self.boss is None
                and len(self.enemies) < rules.max_enemies(self.level)):
            self.enemies.add(Enemy(self, now))
            self.next_enemy_at = now + random.uniform(C.ENEMY_SPAWN_MIN, C.ENEMY_SPAWN_MAX)

    def _collisions(self, now):
        circle = pygame.sprite.collide_circle

        # Balas del jugador contra meteoros, naves y jefe
        hits = pygame.sprite.groupcollide(self.meteors, self.bullets, False, True, circle)
        for meteor, bullets in hits.items():
            for bullet in bullets:
                bullet.volley.bullet_hit()
            if meteor.alive():
                self.destroy_meteor(meteor)

        for group, on_kill in ((self.enemies, self.destroy_enemy), (self.bosses, self.destroy_boss)):
            hits = pygame.sprite.groupcollide(group, self.bullets, False, True, circle)
            for ship, bullets in hits.items():
                for bullet in bullets:
                    bullet.volley.bullet_hit()
                if ship.alive() and ship.damage(len(bullets), now):
                    on_kill(ship)
                elif ship.alive():
                    self.audio.play("hit")
                    self.particles.emit(bullets[0].rect.midtop, 6, [(255, 255, 200), (255, 180, 80)],
                                        speed=(60, 180), life=(0.15, 0.35))

        player = self.player
        if not player.alive_ship:
            return

        # Power-ups: se recogen aunque la nave esté parpadeando
        for powerup in pygame.sprite.spritecollide(player, self.powerups, True, circle):
            self.apply_powerup(powerup.kind)

        if player.is_invulnerable(now):
            return

        hits = pygame.sprite.spritecollide(player, self.meteors, True, circle)
        if hits:
            damage = sum(rules.meteor_damage(m.size) for m in hits)
            for meteor in hits:
                self.explode(meteor.rect.center, C.METEOR_EXPLOSION[meteor.size], sound=False)
            self.damage_player(damage, hits[0].rect.center)
            return

        hits = pygame.sprite.spritecollide(player, self.enemy_bullets, True, circle)
        if hits:
            self.damage_player(C.ENEMY_BULLET_DAMAGE * len(hits), hits[0].rect.center)
            return

        hits = pygame.sprite.spritecollide(player, self.enemies, False, circle)
        if hits:
            self.destroy_enemy(hits[0])
            self.damage_player(C.ENEMY_DAMAGE, hits[0].rect.center)
            return

        boss = self.boss
        if boss and circle(player, boss):
            self.damage_player(C.BOSS_DAMAGE, player.rect.midtop)

    def _progress(self):
        new_level = rules.level_for_score(self.score)
        if new_level > self.level:
            self.level = new_level
            if not rules.is_boss_level(self.level):
                self.show_banner("NIVEL {}".format(self.level))
            self.audio.play("level")

    def _phases(self, now):
        if self.phase == "respawning" and now >= self.phase_until:
            player = self.player
            player.alive_ship = True
            player.shield = 100
            player.weapon_level = 1
            player.reset_position()
            player.invulnerable_until = now + C.RESPAWN_INVULNERABLE_TIME
            self.enemy_bullets.empty()
            self.phase = "playing"
        elif self.phase == "dying" and now >= self.phase_until:
            self.game.set_state(GameOverState(self.game, self.score, self.level, self.best_combo))

    def _update_popups(self, dt):
        for p in self.popups:
            p[2] -= 40 * dt
            p[3] -= dt
        self.popups = [p for p in self.popups if p[3] > 0]

    # --- Dibujo ---
    def offset(self):
        if self.now < self.shake_until:
            return (random.randint(-C.SHAKE_INTENSITY, C.SHAKE_INTENSITY),
                    random.randint(-C.SHAKE_INTENSITY, C.SHAKE_INTENSITY))
        return (0, 0)

    def draw(self, surface):
        self.game.starfield.draw(surface)
        for group in (self.powerups, self.meteors, self.enemies, self.bosses):
            group.draw(surface)
        self.particles.draw(surface)
        self.bullets.draw(surface)
        self.enemy_bullets.draw(surface)
        surface.blit(self.player.image, self.player.rect)
        self.explosions.draw(surface)
        for text, x, y, life, color in self.popups:
            ui.draw_text(surface, text, 18, x, y, color=color, anchor="center")
        self._draw_hud(surface)
        if self.now < self.flash_until:
            surface.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_ADD)

    def _draw_hud(self, surface):
        player = self.player
        # Escudo, nivel y vidas (izquierda)
        fraction = max(0, player.shield) / 100
        ui.draw_bar(surface, 8, 8, 130, 12, fraction, ui.shield_color(fraction))
        ui.draw_text(surface, "Nivel {}".format(self.level), 20, 8, 26, anchor="topleft")
        for i in range(self.lives):
            surface.blit(self.images.player_life, (8 + i * 26, 52))
        if player.weapon_level > 1:
            left = max(0.0, (player.weapon_until - self.now) / C.WEAPON_TIME)
            ui.draw_bar(surface, 8, 80, 80, 6, left, C.CYAN)

        # Puntaje y combo (centro)
        ui.draw_text(surface, self.score, 28, C.WIDTH // 2, 6, bold=True)
        if self.multiplier() > 1:
            ui.draw_text(surface, "x{}".format(self.multiplier()), 22, C.WIDTH // 2 + 70, 10,
                         color=C.YELLOW, anchor="topleft", bold=True)

        # Récord (derecha)
        ui.draw_text(surface, "Récord: {}".format(max(self.game.high_score, self.score)), 20,
                     C.WIDTH - 8, 8, anchor="topright")

        boss = self.boss
        if boss:
            ui.draw_bar(surface, C.WIDTH // 2 - 150, 42, 300, 10, boss.hp / boss.max_hp, C.PURPLE)

        if self.banner and self.now < self.banner[2]:
            ui.draw_text(surface, self.banner[0], 56, C.WIDTH // 2, C.HEIGHT // 3,
                         color=self.banner[1], bold=True)


class PauseState(State):
    OPTIONS = ("Continuar", "Opciones", "Salir al menú")

    def __init__(self, game, play):
        super().__init__(game)
        self.play = play
        self.selected = 0
        game.audio.pause_music(True)

    def _resume(self):
        self.game.audio.pause_music(False)
        self.game.set_state(self.play)

    def handle(self, event, actions):
        if "pause" in actions or "back" in actions:
            self._resume()
        elif "up" in actions:
            self.selected = (self.selected - 1) % len(self.OPTIONS)
        elif "down" in actions:
            self.selected = (self.selected + 1) % len(self.OPTIONS)
        elif "accept" in actions:
            choice = self.OPTIONS[self.selected]
            if choice == "Continuar":
                self._resume()
            elif choice == "Opciones":
                self.game.set_state(OptionsState(self.game, back=lambda: self))
            else:
                self.game.audio.stop_music()
                self.game.set_state(MenuState(self.game))

    def draw(self, surface):
        self.play.draw(surface)
        ui.dim(surface)
        ui.draw_text(surface, "PAUSA", 72, C.WIDTH // 2, 140, bold=True)
        ui.draw_menu(surface, self.OPTIONS, self.selected, 270)


class GameOverState(WaitingState):
    def __init__(self, game, score, level, best_combo):
        super().__init__(game)
        self.score = score
        self.level = level
        self.best_combo = best_combo
        self.new_record = score > game.high_score
        self.qualifies = storage.qualifies(game.scores, score)
        game.audio.stop_music()

    def handle(self, event, actions):
        if not self.ready:
            return
        if self.qualifies and ("accept" in actions or "back" in actions):
            self.game.set_state(NameEntryState(self.game, self.score, self.level))
        elif "accept" in actions:
            self.game.set_state(PlayState(self.game))
        elif "back" in actions:
            self.game.set_state(MenuState(self.game))

    def draw(self, surface):
        self.game.starfield.draw(surface)
        ui.draw_text(surface, "GAME OVER", 80, C.WIDTH // 2, 110, bold=True)
        ui.draw_text(surface, "Puntaje: {}".format(self.score), 36, C.WIDTH // 2, 240)
        ui.draw_text(surface, "Nivel alcanzado: {}   ·   Mejor combo: {}".format(
            self.level, self.best_combo), 24, C.WIDTH // 2, 290)
        if self.new_record:
            ui.draw_text(surface, "¡NUEVO RÉCORD!", 40, C.WIDTH // 2, 340, color=C.YELLOW, bold=True)
        elif self.qualifies:
            ui.draw_text(surface, "¡Entraste al top {}!".format(C.HIGHSCORE_SLOTS), 32,
                         C.WIDTH // 2, 340, color=C.YELLOW)
        else:
            ui.draw_text(surface, "Récord: {}".format(self.game.high_score), 26, C.WIDTH // 2, 345)
        if self.ready:
            hint = ("ENTER para escribir tu nombre" if self.qualifies
                    else "ENTER: jugar de nuevo · ESC: menú")
            ui.draw_text(surface, hint, 20, C.WIDTH // 2, C.HEIGHT - 120)


class NameEntryState(WaitingState):
    """Ingreso de iniciales al estilo arcade: ↑↓ cambia la letra, ←→ cambia de posición,
    o se puede escribir directamente con el teclado."""

    def __init__(self, game, score, level):
        super().__init__(game)
        self.score = score
        self.level = level
        self.letters = list(game.settings["player_name"])
        self.cursor = 0
        self.elapsed = C.START_DELAY

    def _set_char(self, char):
        self.letters[self.cursor] = char
        self.cursor = min(C.NAME_LENGTH - 1, self.cursor + 1)

    def _cycle(self, step):
        index = NAME_CHARS.find(self.letters[self.cursor])
        self.letters[self.cursor] = NAME_CHARS[(index + step) % len(NAME_CHARS)]

    def _confirm(self):
        name = "".join(self.letters)
        self.game.settings["player_name"] = name
        self.game.save_settings()
        self.game.scores, position = storage.insert_score(self.game.scores, name, self.score, self.level)
        storage.save_scores(self.game.scores)
        self.game.set_state(RecordsState(self.game, highlight=position, after_game=True))

    def handle(self, event, actions):
        if event.type == pygame.KEYDOWN:
            # Las letras se escriben tal cual (incluidas W, A, S y D, que en los menús mueven)
            char = event.unicode.upper() if event.unicode else ""
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._confirm()
                return
            if event.key == pygame.K_BACKSPACE:
                self.cursor = max(0, self.cursor - 1)
                return
            if len(char) == 1 and char in NAME_CHARS:
                self._set_char(char)
                return
        if "up" in actions:
            self._cycle(1)
        elif "down" in actions:
            self._cycle(-1)
        elif "left" in actions:
            self.cursor = max(0, self.cursor - 1)
        elif "right" in actions:
            self.cursor = min(C.NAME_LENGTH - 1, self.cursor + 1)
        elif "accept" in actions:
            if self.cursor < C.NAME_LENGTH - 1:
                self.cursor += 1
            else:
                self._confirm()

    def draw(self, surface):
        self.game.starfield.draw(surface)
        ui.draw_text(surface, "¡NUEVO RÉCORD!", 56, C.WIDTH // 2, 80, color=C.YELLOW, bold=True)
        ui.draw_text(surface, "Puntaje: {}".format(self.score), 32, C.WIDTH // 2, 160)
        ui.draw_text(surface, "Escribe tus iniciales", 26, C.WIDTH // 2, 230)
        for i, letter in enumerate(self.letters):
            x = C.WIDTH // 2 + (i - 1) * 70
            active = i == self.cursor
            color = C.YELLOW if active else C.WHITE
            ui.draw_text(surface, letter, 64, x, 290, color=color, bold=True)
            if active:
                pygame.draw.rect(surface, C.YELLOW, (x - 25, 370, 50, 5))
        ui.draw_text(surface, "Escribe letras o usa ↑↓ ←→ · ENTER para guardar", 18,
                     C.WIDTH // 2, C.HEIGHT - 60, color=C.GREY)


def main():
    Game().run()
