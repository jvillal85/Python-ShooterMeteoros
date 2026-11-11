"""Constantes del juego y rutas de archivos. Para cambiar la dificultad basta con
editar los valores de este archivo."""
import os
import sys

TITLE = "Meteoro Shooter"
WIDTH = 800
HEIGHT = 600
FPS = 60
MAX_DT = 0.1             # tiempo máximo que se simula por cuadro (si el juego se traba)
STEP_DT = 1 / 60         # la física avanza en pasos de como mucho este tiempo

IS_WEB = sys.platform == "emscripten"  # versión para navegador (pygbag)

# Colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 220, 90)
RED = (230, 60, 60)
YELLOW = (255, 220, 60)
ORANGE = (255, 150, 40)
CYAN = (80, 220, 255)
BLUE = (90, 150, 255)
PURPLE = (190, 90, 255)
GREY = (150, 150, 150)

# Rutas: relativas al juego, para que funcione desde cualquier carpeta.
# Empaquetado (PyInstaller), los recursos están en sys._MEIPASS y los datos
# (récords, opciones) se guardan junto al ejecutable.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCES_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    RESOURCES_DIR = BASE_DIR
ASSETS_DIR = os.path.join(RESOURCES_DIR, "assets")
HIGHSCORES_FILE = os.path.join(BASE_DIR, "highscores.json")
LEGACY_HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")

# Jugador (velocidades en píxeles por segundo, tiempos en segundos)
PLAYER_SPEED = 330
PLAYER_LIVES = 3
MAX_LIVES = 5
EXTRA_LIFE_EVERY = 5000          # puntos para ganar una vida extra
FIRE_COOLDOWN = 0.22             # pausa mínima entre disparos al mantener ESPACIO
BULLET_SPEED = 620
INVULNERABLE_TIME = 1.5
RESPAWN_INVULNERABLE_TIME = 2.5
BLINK_TIME = 0.1
DEATH_DELAY = 1.6                # espera tras la última explosión antes del Game Over
RESPAWN_DELAY = 1.0              # espera antes de reaparecer tras perder una vida

# Efectos
SHAKE_TIME = 0.3
SHAKE_INTENSITY = 8
LEVEL_MSG_TIME = 1.6
START_DELAY = 0.5                # tiempo antes de aceptar teclas en pantallas de espera
FADE_TIME = 0.3                  # fundido al cambiar de pantalla

# Niveles
POINTS_PER_LEVEL = 700           # el nivel N pide 700 × (1 + 2 + ... + N-1) puntos
BASE_METEORS = 7
METEORS_PER_LEVEL = 2
MAX_METEORS = 18
MAX_SPEED_BONUS = 6

# Dificultades: multiplican la velocidad de los meteoros, el daño recibido y la
# frecuencia de disparo enemiga, y suman o restan meteoros en pantalla.
DIFFICULTIES = {
    "easy": {"speed": 0.8, "damage": 0.7, "enemy_fire": 0.7, "meteors": -2},
    "normal": {"speed": 1.0, "damage": 1.0, "enemy_fire": 1.0, "meteors": 0},
    "hard": {"speed": 1.2, "damage": 1.3, "enemy_fire": 1.35, "meteors": 2},
}
DIFFICULTY_ORDER = ("easy", "normal", "hard")

# Meteoros: puntos, daño, tamaño de la explosión y en qué se parten
METEOR_SIZES = ("big", "med", "small", "tiny")
METEOR_POINTS = {"big": 10, "med": 20, "small": 40, "tiny": 60}
METEOR_DAMAGE = {"big": 35, "med": 25, "small": 15, "tiny": 8}
METEOR_EXPLOSION = {"big": 100, "med": 64, "small": 44, "tiny": 30}
METEOR_SPLIT = {"big": "med", "med": "small", "small": None, "tiny": None}
METEOR_FRAGMENTS = 2
ROTATION_STEPS = 72              # ángulos precalculados por imagen de meteoro (cada 5°)

# Combo
COMBO_STEP = 10                  # aciertos seguidos para subir el multiplicador
MAX_MULTIPLIER = 4

# Power-ups
POWERUP_CHANCE = 0.08            # probabilidad de que un meteoro suelte un power-up
POWERUP_SPEED = 140
POWERUP_WEIGHTS = {"shield": 30, "weapon": 28, "bomb": 10, "bubble": 12,
                   "magnet": 10, "slow": 8, "life": 3}
SHIELD_RESTORE = 30
WEAPON_TIME = 10.0               # duración del disparo doble/triple
MAGNET_TIME = 10.0
MAGNET_RADIUS = 260
MAGNET_PULL = 420
SLOW_TIME = 6.0
SLOW_FACTOR = 0.45               # velocidad de meteoros y enemigos con la cámara lenta

# Naves enemigas: (nivel desde el que aparecen, vida, puntos, peso al elegir)
ENEMY_TYPES = {
    "shooter": {"level": 3, "hp": 3, "points": 150, "weight": 5},
    "kamikaze": {"level": 4, "hp": 1, "points": 100, "weight": 4},
    "spreader": {"level": 6, "hp": 5, "points": 200, "weight": 3},
}
ENEMY_DAMAGE = 30
ENEMY_BULLET_DAMAGE = 15
ENEMY_BULLET_SPEED = 300
ENEMY_SPAWN_MIN = 6.0
ENEMY_SPAWN_MAX = 11.0
KAMIKAZE_SPEED = 430

# Jefe
BOSS_EVERY = 5                   # aparece un jefe cada 5 niveles
BOSS_BASE_HP = 40
BOSS_HP_PER_APPEARANCE = 20
BOSS_POINTS = 1000
BOSS_DAMAGE = 50

# Récords
HIGHSCORE_SLOTS = 10
NAME_LENGTH = 3

# Teclas que se pueden reasignar (nombres de pygame.key.name)
DEFAULT_KEYS = {"left": "left", "right": "right", "fire": "space", "pause": "p"}
