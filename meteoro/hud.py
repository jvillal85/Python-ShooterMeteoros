"""Interfaz durante la partida: escudo, vidas, puntaje, combo, power-ups activos,
progreso de nivel, vida del jefe y avisos."""
import pygame

from . import config as C
from . import rules, ui
from .i18n import t


def draw(play, surface):
    player = play.player
    images = play.images

    # Escudo, nivel y vidas (izquierda)
    fraction = max(0, player.shield) / 100
    ui.draw_bar(surface, 8, 8, 130, 12, fraction, ui.shield_color(fraction))
    if player.bubble:
        pygame.draw.circle(surface, C.CYAN, (152, 14), 7, 2)
    ui.draw_text(surface, t("hud.level", n=play.level), 24, 8, 26, anchor="topleft")
    for i in range(play.lives):
        surface.blit(images.player_life, (8 + i * 26, 48))

    # Power-ups con tiempo: icono + barra de tiempo restante
    y = 76
    timers = (
        ("weapon", player.weapon_until if player.weapon_level > 1 else 0, C.WEAPON_TIME, C.YELLOW),
        ("magnet", play.magnet_until, C.MAGNET_TIME, C.ORANGE),
        ("slow", play.slow_until, C.SLOW_TIME, C.BLUE),
    )
    for kind, until, total, color in timers:
        left = until - play.now
        if left > 0:
            icon = pygame.transform.smoothscale(images.powerups[kind], (18, 18))
            surface.blit(icon, (8, y))
            ui.draw_bar(surface, 30, y + 5, 70, 8, left / total, color)
            y += 22

    # Puntaje, combo y progreso al siguiente nivel (centro)
    ui.draw_text(surface, play.score, 36, C.WIDTH // 2, 4)
    multiplier = play.multiplier()
    if multiplier > 1:
        ui.draw_text(surface, "x{}".format(multiplier), 30, C.WIDTH // 2 + 80, 6,
                     color=C.YELLOW, anchor="topleft")
    progress = rules.level_progress(play.score)
    pygame.draw.rect(surface, (60, 60, 80), (C.WIDTH // 2 - 60, 38, 120, 3))
    pygame.draw.rect(surface, C.CYAN, (C.WIDTH // 2 - 60, 38, round(120 * progress), 3))

    # Récord (derecha)
    ui.draw_text(surface, t("record", score=max(play.game.high_score, play.score)), 24,
                 C.WIDTH - 8, 8, anchor="topright")

    boss = play.boss
    if boss:
        ui.draw_bar(surface, C.WIDTH // 2 - 150, 48, 300, 10, boss.hp / boss.max_hp, C.PURPLE)

    _draw_banner(play, surface)


def _draw_banner(play, surface):
    """Aviso grande (nivel nuevo, jefe...) que entra creciendo y se desvanece al final."""
    if not play.banner:
        return
    text, color, start, end = play.banner
    if play.now >= end:
        return
    elapsed = play.now - start
    remaining = end - play.now
    scale = 1.0 + max(0.0, 0.25 - elapsed) * 2.4   # de 1.6 a 1.0 en 0.25 s
    alpha = 255 if remaining > 0.4 else int(255 * remaining / 0.4)
    ui.draw_text(surface, t(text["key"], **text["values"]), 64, C.WIDTH // 2, C.HEIGHT // 3,
                 color=color, alpha=alpha, scale=scale, anchor="center")
