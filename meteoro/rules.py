"""Reglas del juego sin dependencias de pygame (se pueden probar con tests)."""
from . import config as C


def score_for_level(level):
    """Puntos necesarios para llegar a un nivel. Cada nivel pide más que el anterior:
    nivel 2 = 700, nivel 3 = 2100, nivel 4 = 4200, nivel 5 = 7000..."""
    return C.POINTS_PER_LEVEL * (level - 1) * level // 2


def level_for_score(points):
    level = 1
    while score_for_level(level + 1) <= points:
        level += 1
    return level


def meteors_for_level(level):
    return min(C.BASE_METEORS + (level - 1) * C.METEORS_PER_LEVEL, C.MAX_METEORS)


def meteor_speed_range(level):
    """Velocidad vertical (mín, máx) de los meteoros en píxeles por segundo."""
    bonus = min(level - 1, C.MAX_SPEED_BONUS)
    return (60 + bonus * 30, 540 + bonus * 60)


def meteor_points(size):
    return C.METEOR_POINTS[size]


def meteor_damage(size):
    return C.METEOR_DAMAGE[size]


def split_size(size):
    """Tamaño de los fragmentos al destruir un meteoro, o None si no se parte."""
    return C.METEOR_SPLIT[size]


def multiplier_for_combo(combo):
    return min(1 + combo // C.COMBO_STEP, C.MAX_MULTIPLIER)


def lives_earned(old_score, new_score):
    """Vidas extra ganadas al pasar de old_score a new_score."""
    return new_score // C.EXTRA_LIFE_EVERY - old_score // C.EXTRA_LIFE_EVERY


def is_boss_level(level):
    return level % C.BOSS_EVERY == 0


def boss_hp(level):
    appearance = level // C.BOSS_EVERY
    return C.BOSS_BASE_HP + (appearance - 1) * C.BOSS_HP_PER_APPEARANCE


def max_enemies(level):
    if level < C.ENEMY_FIRST_LEVEL:
        return 0
    return min(1 + (level - C.ENEMY_FIRST_LEVEL) // 2, 3)


def meteor_target(level, boss_alive):
    """Meteoros en pantalla: con un jefe presente hay la mitad."""
    target = meteors_for_level(level)
    return max(3, target // 2) if boss_alive else target
