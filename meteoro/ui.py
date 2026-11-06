"""Dibujo de textos, barras e interfaz (HUD)."""
import pygame

from . import config as C

_fonts = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("serif", size, bold=bold)
    return _fonts[key]


def draw_text(surface, text, size, x, y, color=C.WHITE, anchor="midtop", bold=False, shadow=True):
    rendered = font(size, bold).render(str(text), True, color)
    rect = rendered.get_rect(**{anchor: (round(x), round(y))})
    if shadow:
        shade = font(size, bold).render(str(text), True, C.BLACK)
        surface.blit(shade, rect.move(2, 2))
    surface.blit(rendered, rect)
    return rect


def draw_bar(surface, x, y, width, height, fraction, color, border=C.WHITE):
    fraction = max(0.0, min(1.0, fraction))
    pygame.draw.rect(surface, (30, 30, 30), (x, y, width, height))
    pygame.draw.rect(surface, color, (x, y, width * fraction, height))
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


def draw_menu(surface, options, selected, y, size=34, spacing=48):
    for i, label in enumerate(options):
        active = i == selected
        text = "> {} <".format(label) if active else label
        draw_text(surface, text, size, C.WIDTH // 2, y + i * spacing,
                  color=C.YELLOW if active else C.WHITE, bold=active)
