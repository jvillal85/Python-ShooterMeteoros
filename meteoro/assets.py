"""Carga de imágenes y sonidos. Los gráficos y sonidos que no existen en assets/
(enemigos, power-ups, efectos nuevos) se generan por código."""
import math
import os
import random
import re
from array import array

import pygame

from . import config as C


def path(name):
    return os.path.join(C.ASSETS_DIR, name)


def load_image(name, colorkey=C.BLACK):
    """Carga una imagen con fondo negro y la convierte a transparencia por píxel,
    para que se pueda rotar y escalar sin bordes negros."""
    img = pygame.image.load(path(name)).convert()
    img.set_colorkey(colorkey)
    return img.convert_alpha()


def tint(image, color):
    tinted = image.copy()
    tinted.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


def _powerup_icon(color, letter):
    size = 30
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.circle(surf, (*color, 90), (size // 2, size // 2), size // 2)
    pygame.draw.circle(surf, color, (size // 2, size // 2), size // 2 - 3, 3)
    font = pygame.font.SysFont("arial", 18, bold=True)
    text = font.render(letter, True, C.WHITE)
    surf.blit(text, text.get_rect(center=(size // 2, size // 2 + 1)))
    return surf


def _enemy_bullet():
    surf = pygame.Surface((10, 18), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (255, 80, 60), surf.get_rect())
    pygame.draw.ellipse(surf, (255, 220, 160), surf.get_rect().inflate(-5, -8))
    return surf


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

        base_explosion = [load_image("regularExplosion0{}.png".format(i)) for i in range(9)]
        self._explosion_base = base_explosion
        self._explosions = {}

        enemy = pygame.transform.flip(self.player, False, True)
        self.enemy = tint(pygame.transform.smoothscale(enemy, (64, 64)), (255, 90, 90))
        self.boss = tint(pygame.transform.smoothscale(enemy, (190, 190)), (200, 110, 255))
        self.enemy_bullet = _enemy_bullet()

        self.powerups = {
            "shield": _powerup_icon(C.GREEN, "S"),
            "weapon": _powerup_icon(C.CYAN, "W"),
            "bomb": _powerup_icon(C.ORANGE, "B"),
        }

        background = pygame.image.load(path("background.png")).convert()
        background = pygame.transform.smoothscale(background, (C.WIDTH, C.HEIGHT))
        # Imagen + su reflejo vertical: se puede repetir sin que se note el corte
        self.background = pygame.Surface((C.WIDTH, C.HEIGHT * 2)).convert()
        self.background.blit(background, (0, 0))
        self.background.blit(pygame.transform.flip(background, False, True), (0, C.HEIGHT))

    def explosion(self, size):
        """Animación de explosión escalada al tamaño pedido (se guarda en caché)."""
        if size not in self._explosions:
            self._explosions[size] = [pygame.transform.smoothscale(img, (size, size))
                                      for img in self._explosion_base]
        return self._explosions[size]


# --- Sonido -----------------------------------------------------------------

class _SilentSound:
    def play(self, *args, **kwargs):
        pass

    def set_volume(self, *args):
        pass


def _synth(duration, wave, volume=0.5):
    """Genera un sonido corto. wave(t, progreso) devuelve una muestra entre -1 y 1."""
    freq, _, channels = pygame.mixer.get_init()
    n = int(freq * duration)
    samples = array("h")
    for i in range(n):
        t = i / freq
        value = wave(t, i / n)
        sample = int(max(-1.0, min(1.0, value)) * volume * 32767)
        samples.extend([sample] * channels)
    return pygame.mixer.Sound(buffer=samples.tobytes())


def _sweep(f0, f1):
    """Onda cuadrada suave cuya frecuencia va de f0 a f1, con caída de volumen."""
    phase = [0.0]

    def wave(t, p):
        phase[0] += (f0 + (f1 - f0) * p) / pygame.mixer.get_init()[0]
        return math.copysign(1.0, math.sin(2 * math.pi * phase[0])) * 0.5 * (1 - p)
    return wave


def _arpeggio(notes):
    def wave(t, p):
        idx = min(int(p * len(notes)), len(notes) - 1)
        local = p * len(notes) - idx
        return math.sin(2 * math.pi * notes[idx] * t) * (1 - local * 0.6)
    return wave


def _boom(t, p):
    return (random.uniform(-1, 1) * 0.7 + math.sin(2 * math.pi * 55 * t) * 0.6) * (1 - p) ** 2


class Audio:
    """Música y efectos. Si no hay dispositivo de sonido, el juego funciona en silencio."""

    def __init__(self, settings):
        self.settings = settings
        self.enabled = pygame.mixer.get_init() is not None
        self.sounds = {}
        self.music_loaded = False
        if not self.enabled:
            return
        try:
            self.sounds["laser"] = pygame.mixer.Sound(path("laser5.ogg"))
            self.sounds["explosion"] = pygame.mixer.Sound(path("explosion.wav"))
            self.sounds["enemy_laser"] = _synth(0.15, _sweep(900, 300), 0.25)
            self.sounds["shield"] = _synth(0.35, _arpeggio([523, 659, 784, 1047]), 0.35)
            self.sounds["weapon"] = _synth(0.3, _sweep(300, 1400), 0.3)
            self.sounds["bomb"] = _synth(0.8, _boom, 0.6)
            self.sounds["life"] = _synth(0.5, _arpeggio([784, 988, 1175, 1568]), 0.35)
            self.sounds["level"] = _synth(0.4, _arpeggio([440, 554, 659]), 0.3)
            self.sounds["hit"] = _synth(0.08, _sweep(500, 200), 0.25)
            self.sounds["select"] = _synth(0.06, _sweep(700, 900), 0.2)
            pygame.mixer.music.load(path("music.ogg"))
            self.music_loaded = True
        except pygame.error:
            self.enabled = False
            self.sounds = {}
        self.apply_volume()

    def apply_volume(self):
        if not self.enabled:
            return
        muted = self.settings["muted"]
        sfx = 0.0 if muted else self.settings["sfx_volume"]
        for sound in self.sounds.values():
            sound.set_volume(sfx)
        if self.music_loaded:
            pygame.mixer.music.set_volume(0.0 if muted else self.settings["music_volume"] * 0.5)

    def play(self, name):
        self.sounds.get(name, _SilentSound()).play()

    def play_music(self):
        if self.enabled and self.music_loaded:
            pygame.mixer.music.play(loops=-1)

    def stop_music(self):
        if self.enabled and self.music_loaded:
            pygame.mixer.music.stop()

    def pause_music(self, paused):
        if self.enabled and self.music_loaded:
            if paused:
                pygame.mixer.music.pause()
            else:
                pygame.mixer.music.unpause()

    def toggle_mute(self):
        self.settings["muted"] = not self.settings["muted"]
        self.apply_volume()
