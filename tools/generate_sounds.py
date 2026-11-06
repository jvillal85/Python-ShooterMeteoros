"""Genera los efectos de sonido sintetizados del juego en assets/sfx/.

Solo hace falta ejecutarlo si se quieren cambiar estos sonidos:
    pip install soundfile
    python tools/generate_sounds.py
Se guardan en formato OGG porque la versión web (pygbag) no acepta WAV.
"""
import math
import os
import random

try:
    import soundfile
except ImportError:
    raise SystemExit("Falta soundfile: pip install soundfile") from None

RATE = 22050
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sfx")


def render(duration, wave_fn, volume=0.5):
    n = int(RATE * duration)
    return [max(-1.0, min(1.0, wave_fn(i / RATE, i / n))) * volume for i in range(n)]


def sweep(f0, f1):
    """Onda cuadrada suave que va de f0 a f1 Hz, con caída de volumen."""
    phase = [0.0]

    def fn(t, p):
        phase[0] += (f0 + (f1 - f0) * p) / RATE
        return math.copysign(1.0, math.sin(2 * math.pi * phase[0])) * 0.5 * (1 - p)
    return fn


def arpeggio(notes):
    def fn(t, p):
        idx = min(int(p * len(notes)), len(notes) - 1)
        local = p * len(notes) - idx
        return math.sin(2 * math.pi * notes[idx] * t) * (1 - local * 0.6)
    return fn


def boom(t, p):
    return (random.uniform(-1, 1) * 0.7 + math.sin(2 * math.pi * 55 * t) * 0.6) * (1 - p) ** 2


def wobble(t, p):
    freq = 300 + 120 * math.sin(2 * math.pi * 8 * t)
    return math.sin(2 * math.pi * freq * t) * (1 - p)


def slowdown(t, p):
    freq = 700 * (1 - p * 0.75)
    return math.sin(2 * math.pi * freq * t) * (1 - p) * 0.8


SOUNDS = {
    "bomb": (0.8, boom, 0.6),
    "life": (0.5, arpeggio([784, 988, 1175, 1568]), 0.35),
    "select": (0.06, sweep(700, 900), 0.2),
    "hit": (0.08, sweep(500, 200), 0.25),
    "magnet": (0.45, wobble, 0.35),
    "slow": (0.6, slowdown, 0.35),
}


def main():
    random.seed(1)  # el ruido de la bomba sale siempre igual
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, (duration, fn, volume) in SOUNDS.items():
        path = os.path.join(OUT_DIR, name + ".ogg")
        soundfile.write(path, render(duration, fn, volume), RATE, format="OGG", subtype="VORBIS")
        print("creado", os.path.relpath(path))


if __name__ == "__main__":
    main()
