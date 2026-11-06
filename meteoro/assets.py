"""Carga de imágenes y sonidos.

- assets/            recursos originales del juego
- assets/kenney/     naves enemigas, power-ups, fuente y sonidos de Kenney (CC0)
- assets/sfx/        sonidos generados con tools/generate_sounds.py
"""
import os
import re

import pygame

from . import config as C


def path(*parts):
    return os.path.join(C.ASSETS_DIR, *parts)


def load_image(name, colorkey=C.BLACK):
    """Imagen con fondo negro, convertida a transparencia por píxel para poder
    rotarla y escalarla sin bordes negros."""
    img = pygame.image.load(path(name)).convert()
    img.set_colorkey(colorkey)
    return img.convert_alpha()


def load_kenney(name, size=None):
    img = pygame.image.load(path("kenney", name)).convert_alpha()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img


def scale_to_width(image, width):
    w, h = image.get_size()
    return pygame.transform.smoothscale(image, (width, round(h * width / w)))


def _glow(radius, color):
    """Halo suave para los power-ups."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -2):
        alpha = int(70 * (1 - r / radius) ** 1.5) + 4
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


POWERUP_FILES = {
    "shield": ("powerupGreen_shield.png", C.GREEN),
    "weapon": ("powerupYellow_bolt.png", C.YELLOW),
    "bomb": ("powerupRed_star.png", C.RED),
    "bubble": ("powerupBlue_shield.png", C.CYAN),
    "magnet": ("things_gold.png", C.ORANGE),
    "slow": ("powerupBlue_star.png", C.BLUE),
    "life": ("pill_red.png", C.RED),
}


class Images:
    def __init__(self):
        self.player = load_image("player.png")
        self.player_life = pygame.transform.smoothscale(self.player, (22, 22))
        self.bullet = load_image("laser1.png")

        self.meteors = {size: [] for size in C.METEOR_SIZES}
        for name in sorted(os.listdir(C.ASSETS_DIR)):
            match = re.fullmatch(r"meteorGrey_([a-z]+)\d+\.png", name)
            if match and match.group(1) in self.meteors:
                self.meteors[match.group(1)].append(load_image(name))
        self._rotations = {}

        self._explosion_base = [load_image("regularExplosion0{}.png".format(i)) for i in range(9)]
        self._explosions = {}

        self.enemies = {
            "shooter": scale_to_width(load_kenney("enemyRed1.png"), 70),
            "kamikaze": scale_to_width(load_kenney("enemyGreen3.png"), 62),
            "spreader": scale_to_width(load_kenney("enemyBlue2.png"), 86),
        }
        self.boss = scale_to_width(load_kenney("enemyBlack4.png"), 200)
        self.enemy_bullet = load_kenney("laserRed07.png", (7, 26))
        self.boss_bullet = load_kenney("laserRed08.png", (22, 22))
        bubble = load_kenney("shield1.png")
        self.bubble = scale_to_width(bubble, int(self.player.get_width() * 1.3))

        self.powerups = {}
        self.powerup_glows = {}
        for kind, (name, color) in POWERUP_FILES.items():
            img = load_kenney(name)
            if img.get_width() < 30:
                img = scale_to_width(img, 32)
            self.powerups[kind] = img
            self.powerup_glows[kind] = _glow(30, color)

        background = pygame.image.load(path("background.png")).convert()
        background = pygame.transform.smoothscale(background, (C.WIDTH, C.HEIGHT))
        # Imagen + su reflejo vertical: se puede repetir sin que se note el corte
        self.background = pygame.Surface((C.WIDTH, C.HEIGHT * 2)).convert()
        self.background.blit(background, (0, 0))
        self.background.blit(pygame.transform.flip(background, False, True), (0, C.HEIGHT))

    def rotated(self, image, angle):
        """Imagen rotada al ángulo más cercano de los precalculados (se guarda en caché),
        para no rotar cada meteoro en cada cuadro."""
        frames = self._rotations.get(id(image))
        if frames is None:
            frames = self._rotations[id(image)] = [None] * C.ROTATION_STEPS
        index = int(round(angle / 360 * C.ROTATION_STEPS)) % C.ROTATION_STEPS
        if frames[index] is None:
            frames[index] = pygame.transform.rotate(image, index * 360 / C.ROTATION_STEPS)
        return frames[index]

    def explosion(self, size):
        """Animación de explosión escalada al tamaño pedido (se guarda en caché)."""
        if size not in self._explosions:
            self._explosions[size] = [pygame.transform.smoothscale(img, (size, size))
                                      for img in self._explosion_base]
        return self._explosions[size]


# --- Sonido -----------------------------------------------------------------

SOUND_FILES = {
    "laser": ("laser5.ogg",),
    "explosion": ("explosion.ogg",),
    "enemy_laser": ("kenney", "sfx_laser2.ogg"),
    "shield": ("kenney", "sfx_shieldUp.ogg"),
    "bubble": ("kenney", "sfx_shieldUp.ogg"),
    "bubble_pop": ("kenney", "sfx_shieldDown.ogg"),
    "weapon": ("kenney", "sfx_zap.ogg"),
    "level": ("kenney", "sfx_twoTone.ogg"),
    "gameover": ("kenney", "sfx_lose.ogg"),
    "bomb": ("sfx", "bomb.ogg"),
    "life": ("sfx", "life.ogg"),
    "select": ("sfx", "select.ogg"),
    "hit": ("sfx", "hit.ogg"),
    "magnet": ("sfx", "magnet.ogg"),
    "slow": ("sfx", "slow.ogg"),
}
SOUND_VOLUME = {"enemy_laser": 0.5, "select": 0.8, "hit": 0.8}


class Audio:
    """Música y efectos. Si no hay dispositivo de sonido, el juego funciona en silencio."""

    def __init__(self, settings):
        self.settings = settings
        self.enabled = pygame.mixer.get_init() is not None
        self.sounds = {}
        self.music_loaded = False
        if not self.enabled:
            return
        for name, parts in SOUND_FILES.items():
            try:
                self.sounds[name] = pygame.mixer.Sound(path(*parts))
            except (pygame.error, FileNotFoundError):
                pass  # un sonido que falta no impide jugar
        try:
            pygame.mixer.music.load(path("music.ogg"))
            self.music_loaded = True
        except pygame.error:
            pass
        self.apply_volume()

    def apply_volume(self):
        if not self.enabled:
            return
        muted = self.settings["muted"]
        sfx = 0.0 if muted else self.settings["sfx_volume"]
        for name, sound in self.sounds.items():
            sound.set_volume(sfx * SOUND_VOLUME.get(name, 1.0))
        if self.music_loaded:
            pygame.mixer.music.set_volume(0.0 if muted else self.settings["music_volume"] * 0.5)

    def play(self, name):
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def play_music(self):
        if self.music_loaded:
            pygame.mixer.music.play(loops=-1)

    def stop_music(self):
        if self.music_loaded:
            pygame.mixer.music.stop()

    def pause_music(self, paused):
        if self.music_loaded:
            if paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    def toggle_mute(self):
        self.settings["muted"] = not self.settings["muted"]
        self.apply_volume()
