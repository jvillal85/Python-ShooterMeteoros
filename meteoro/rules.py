"""Reglas del juego sin dependencias de pygame (se pueden probar con tests)."""
from __future__ import annotations

from . import config as C


def difficulty(name: str) -> dict[str, float]:
    return C.DIFFICULTIES.get(name, C.DIFFICULTIES["normal"])


def score_for_level(level: int) -> int:
    """Puntos necesarios para llegar a un nivel. Cada nivel pide más que el anterior:
    nivel 2 = 700, nivel 3 = 2100, nivel 4 = 4200, nivel 5 = 7000..."""
    return C.POINTS_PER_LEVEL * (level - 1) * level // 2


def level_for_score(points: int) -> int:
    level = 1
    while score_for_level(level + 1) <= points:
        level += 1
    return level


def level_progress(points: int) -> float:
    """Fracción (0 a 1) del camino hacia el siguiente nivel."""
    level = level_for_score(points)
    start, end = score_for_level(level), score_for_level(level + 1)
    return (points - start) / (end - start)


def meteors_for_level(level: int, difficulty_name: str = "normal") -> int:
    base = C.BASE_METEORS + (level - 1) * C.METEORS_PER_LEVEL + int(difficulty(difficulty_name)["meteors"])
    return max(3, min(base, C.MAX_METEORS))


def meteor_speed_range(level: int, difficulty_name: str = "normal") -> tuple[float, float]:
    """Velocidad vertical (mín, máx) de los meteoros en píxeles por segundo."""
    bonus = min(level - 1, C.MAX_SPEED_BONUS)
    factor = difficulty(difficulty_name)["speed"]
    return ((60 + bonus * 30) * factor, (540 + bonus * 60) * factor)


def meteor_points(size: str) -> int:
    return C.METEOR_POINTS[size]


def meteor_damage(size: str) -> int:
    return C.METEOR_DAMAGE[size]


def scaled_damage(damage: float, difficulty_name: str = "normal") -> int:
    return max(1, round(damage * difficulty(difficulty_name)["damage"]))


def enemy_fire_interval(base_seconds: float, difficulty_name: str = "normal") -> float:
    return base_seconds / difficulty(difficulty_name)["enemy_fire"]


def split_size(size: str) -> str | None:
    """Tamaño de los fragmentos al destruir un meteoro, o None si no se parte."""
    return C.METEOR_SPLIT[size]


def multiplier_for_combo(combo: int) -> int:
    return min(1 + combo // C.COMBO_STEP, C.MAX_MULTIPLIER)


def lives_earned(old_score: int, new_score: int) -> int:
    """Vidas extra ganadas al pasar de old_score a new_score."""
    return new_score // C.EXTRA_LIFE_EVERY - old_score // C.EXTRA_LIFE_EVERY


def is_boss_level(level: int) -> bool:
    return level % C.BOSS_EVERY == 0


def boss_appearance(level: int) -> int:
    """1 para el primer jefe (nivel 5), 2 para el segundo (nivel 10)..."""
    return max(1, level // C.BOSS_EVERY)


def boss_hp(level: int) -> int:
    return C.BOSS_BASE_HP + (boss_appearance(level) - 1) * C.BOSS_HP_PER_APPEARANCE


def boss_attacks(level: int) -> list[str]:
    """Ataques del jefe: cada aparición añade uno nuevo."""
    attacks = ["fan", "aimed"]
    appearance = boss_appearance(level)
    if appearance >= 2:
        attacks.append("spiral")
    if appearance >= 3:
        attacks.append("summon")
    return attacks


def max_enemies(level: int) -> int:
    if level < min(t["level"] for t in C.ENEMY_TYPES.values()):
        return 0
    first = C.ENEMY_TYPES["shooter"]["level"]
    return min(1 + (level - first) // 2, 3)


def enemy_types_for_level(level: int) -> list[str]:
    return [name for name, data in C.ENEMY_TYPES.items() if level >= data["level"]]


def meteor_target(level: int, boss_alive: bool, difficulty_name: str = "normal") -> int:
    """Meteoros en pantalla: con un jefe presente hay la mitad."""
    target = meteors_for_level(level, difficulty_name)
    return max(3, target // 2) if boss_alive else target
