"""Dibujo de textos, barras y menús.

Las fuentes van incluidas con el juego (la de títulos en assets/kenney y la de
texto es la que trae pygame), así el juego se ve igual en todos los sistemas.
Los textos ya dibujados se guardan en caché: el HUD no se vuelve a renderizar en
cada cuadro si no cambia."""
from collections import OrderedDict

import pygame

from . import config as C
from .assets import path

_fonts = {}
_text_cache = OrderedDict()
TEXT_CACHE_SIZE = 400


def reset_caches():
    """Vacía las cachés (necesario si pygame se reinicia, por ejemplo entre tests)."""
    _fonts.clear()
    _text_cache.clear()


def font(size, title=False):
    key = (size, title)
    if key not in _fonts:
        if title:
            try:
                _fonts[key] = pygame.font.Font(path("kenney", "kenvector_future.ttf"), size)
            except (OSError, pygame.error):
                _fonts[key] = pygame.font.Font(None, int(size * 1.3))
        else:
            _fonts[key] = pygame.font.Font(None, size)
    return _fonts[key]


def render_text(text, size, color=C.WHITE, title=False, shadow=True):
    key = (str(text), size, tuple(color), title, shadow)
    surf = _text_cache.get(key)
    if surf is not None:
        _text_cache.move_to_end(key)
        return surf
    f = font(size, title)
    rendered = f.render(str(text), True, color)
    if shadow:
        offset = 2 if size < 40 else 3
        surf = pygame.Surface((rendered.get_width() + offset, rendered.get_height() + offset),
                              pygame.SRCALPHA)
        surf.blit(f.render(str(text), True, C.BLACK), (offset, offset))
        surf.blit(rendered, (0, 0))
    else:
        surf = rendered
    _text_cache[key] = surf
    if len(_text_cache) > TEXT_CACHE_SIZE:
        _text_cache.popitem(last=False)
    return surf


def draw_text(surface, text, size, x, y, color=C.WHITE, anchor="midtop", title=False,
              shadow=True, alpha=None, scale=1.0):
    surf = render_text(text, size, color, title, shadow)
    if scale != 1.0:
        surf = pygame.transform.smoothscale_by(surf, scale)
    if alpha is not None and alpha < 255:
        surf = surf.copy()
        surf.set_alpha(alpha)
    rect = surf.get_rect(**{anchor: (round(x), round(y))})
    surface.blit(surf, rect)
    return rect


def draw_bar(surface, x, y, width, height, fraction, color, border=C.WHITE):
    fraction = max(0.0, min(1.0, fraction))
    pygame.draw.rect(surface, (30, 30, 30), (x, y, width, height))
    pygame.draw.rect(surface, color, (x, y, round(width * fraction), height))
    pygame.draw.rect(surface, border, (x, y, width, height), 2)


def shield_color(fraction):
    if fraction > 0.5:
        return C.GREEN
    if fraction > 0.25:
        return C.YELLOW
    return C.RED


def dim(surface, alpha=150):
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    surface.blit(overlay, (0, 0))


def draw_title(surface, text, y, size=44, color=C.WHITE):
    # La fuente del logo (Kenvector) dibuja la V y la N de forma muy estilizada
    # ("GAME OUER"), así que los títulos usan la fuente normal, más grande.
    return draw_text(surface, text, int(size * 1.45), C.WIDTH // 2, y, color=color)


def draw_hint(surface, text, y=C.HEIGHT - 40):
    return draw_text(surface, text, 22, C.WIDTH // 2, y, color=C.GREY)


def draw_menu(surface, options, selected, y, size=36, spacing=48):
    for i, label in enumerate(options):
        active = i == selected
        text = "> {} <".format(label) if active else label
        draw_text(surface, text, size, C.WIDTH // 2, y + i * spacing,
                  color=C.YELLOW if active else C.WHITE)
