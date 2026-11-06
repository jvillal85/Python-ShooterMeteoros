"""Guardado de récords (top 10 con iniciales) y opciones en archivos JSON."""
import json
import os

from . import config as C

DEFAULT_SETTINGS = {
    "music_volume": 0.4,
    "sfx_volume": 0.7,
    "muted": False,
    "fullscreen": False,
    "player_name": "AAA",
}


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _write_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False  # si no se puede guardar, el juego sigue igual


def _clean_entry(entry):
    if not isinstance(entry, dict):
        return None
    try:
        score = int(entry.get("score", 0))
    except (TypeError, ValueError):
        return None
    name = str(entry.get("name", "---"))[:C.NAME_LENGTH].upper() or "---"
    try:
        level = int(entry.get("level", 1))
    except (TypeError, ValueError):
        level = 1
    return {"name": name, "score": max(0, score), "level": max(1, level)}


def sort_scores(scores):
    return sorted(scores, key=lambda e: e["score"], reverse=True)[:C.HIGHSCORE_SLOTS]


def load_scores(path=None, legacy_path=None):
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
                return [{"name": "---", "score": old, "level": 1}]
        except (OSError, ValueError):
            pass
    return []


def save_scores(scores, path=None):
    return _write_json(path or C.HIGHSCORES_FILE, sort_scores(scores))


def qualifies(scores, score):
    if score <= 0:
        return False
    if len(scores) < C.HIGHSCORE_SLOTS:
        return True
    return score > min(e["score"] for e in scores)


def insert_score(scores, name, score, level):
    """Devuelve (nueva tabla, posición de la nueva entrada o None)."""
    entry = {"name": name[:C.NAME_LENGTH].upper() or "---", "score": score, "level": level}
    new = sort_scores(scores + [entry])
    for i, e in enumerate(new):
        if e is entry:
            return new, i
    return new, None


def top_score(scores):
    return scores[0]["score"] if scores else 0


def load_settings(path=None):
    data = _read_json(path or C.SETTINGS_FILE)
    settings = dict(DEFAULT_SETTINGS)
    if isinstance(data, dict):
        for key, default in DEFAULT_SETTINGS.items():
            value = data.get(key, default)
            if isinstance(default, bool):
                settings[key] = bool(value)
            elif isinstance(default, str):
                name = str(value)[:C.NAME_LENGTH].upper()
                settings[key] = name if len(name) == C.NAME_LENGTH else default
            elif isinstance(value, (int, float)) and not isinstance(value, bool):
                settings[key] = min(1.0, max(0.0, float(value)))
    return settings


def save_settings(settings, path=None):
    return _write_json(path or C.SETTINGS_FILE, settings)
