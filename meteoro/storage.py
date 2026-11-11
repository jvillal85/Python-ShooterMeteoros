"""Guardado de récords (top 10 con iniciales) y opciones en archivos JSON."""
from __future__ import annotations

import json
import os
from typing import Any

from . import config as C

Entry = dict[str, Any]

DEFAULT_SETTINGS: dict[str, Any] = {
    "music_volume": 0.4,
    "sfx_volume": 0.7,
    "muted": False,
    "fullscreen": False,
    "screen_shake": True,
    "difficulty": "normal",
    "language": "es",
    "player_name": "AAA",
    "keys": dict(C.DEFAULT_KEYS),
}
LANGUAGES = ("es", "en")


def _read_json(path: str) -> Any:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_json(path: str, data: Any) -> bool:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False  # si no se puede guardar, el juego sigue igual


def _to_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clean_entry(entry: Any) -> Entry | None:
    if not isinstance(entry, dict):
        return None
    score = _to_int(entry.get("score"), -1)
    if score < 0:
        return None
    name = str(entry.get("name", "---"))[:C.NAME_LENGTH].upper() or "---"
    difficulty = entry.get("difficulty", "normal")
    if difficulty not in C.DIFFICULTIES:
        difficulty = "normal"
    return {"name": name, "score": score, "level": max(1, _to_int(entry.get("level"), 1)),
            "difficulty": difficulty}


def sort_scores(scores: list[Entry]) -> list[Entry]:
    return sorted(scores, key=lambda e: e["score"], reverse=True)[:C.HIGHSCORE_SLOTS]


def load_scores(path: str | None = None, legacy_path: str | None = None) -> list[Entry]:
    """Carga la tabla de récords. Si no existe, importa el récord antiguo (highscore.txt)."""
    path = path or C.HIGHSCORES_FILE
    legacy_path = legacy_path or C.LEGACY_HIGHSCORE_FILE
    data = _read_json(path)
    if isinstance(data, list):
        return sort_scores([e for e in (_clean_entry(x) for x in data) if e])
    if os.path.exists(legacy_path):
        try:
            with open(legacy_path, encoding="utf-8") as f:
                old = int(f.read().strip() or 0)
            if old > 0:
                return [{"name": "---", "score": old, "level": 1, "difficulty": "normal"}]
        except (OSError, ValueError):
            pass
    return []


def save_scores(scores: list[Entry], path: str | None = None) -> bool:
    return _write_json(path or C.HIGHSCORES_FILE, sort_scores(scores))


def qualifies(scores: list[Entry], score: int) -> bool:
    if score <= 0:
        return False
    if len(scores) < C.HIGHSCORE_SLOTS:
        return True
    return score > min(int(e["score"]) for e in scores)


def insert_score(scores: list[Entry], name: str, score: int, level: int,
                 difficulty: str = "normal") -> tuple[list[Entry], int | None]:
    """Devuelve (nueva tabla, posición de la nueva entrada o None)."""
    entry = {"name": name[:C.NAME_LENGTH].upper() or "---", "score": score, "level": level,
             "difficulty": difficulty}
    new = sort_scores(scores + [entry])
    for i, e in enumerate(new):
        if e is entry:
            return new, i
    return new, None


def top_score(scores: list[Entry]) -> int:
    return scores[0]["score"] if scores else 0


def load_settings(path: str | None = None) -> dict[str, Any]:
    data = _read_json(path or C.SETTINGS_FILE)
    settings = dict(DEFAULT_SETTINGS)
    settings["keys"] = dict(C.DEFAULT_KEYS)
    if not isinstance(data, dict):
        return settings
    for key, default in DEFAULT_SETTINGS.items():
        if key not in data:
            continue
        value = data[key]
        if isinstance(default, bool):
            settings[key] = bool(value)
        elif key == "player_name":
            name = str(value)[:C.NAME_LENGTH].upper()
            if len(name) == C.NAME_LENGTH:
                settings[key] = name
        elif key == "difficulty":
            if value in C.DIFFICULTIES:
                settings[key] = value
        elif key == "language":
            if value in LANGUAGES:
                settings[key] = value
        elif key == "keys":
            if isinstance(value, dict):
                for action in C.DEFAULT_KEYS:
                    if isinstance(value.get(action), str) and value[action]:
                        settings["keys"][action] = value[action]
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            settings[key] = min(1.0, max(0.0, float(value)))
    return settings


def save_settings(settings: dict[str, Any], path: str | None = None) -> bool:
    return _write_json(path or C.SETTINGS_FILE, settings)
