"""Controles: teclado (teclas reasignables) y mando (gamepad).

Los eventos se traducen a acciones ("up", "down", "left", "right", "accept",
"back", "pause", "mute", "fullscreen") para que menús y juego no dependan de la
tecla o botón concreto. En los menús siempre funcionan flechas, WASD, ENTER y ESC."""
import pygame

from . import config as C
from .i18n import get_language

AXIS_DEADZONE = 0.35
MENU_AXIS_THRESHOLD = 0.6

# Botones de un mando tipo Xbox en SDL (otros mandos suelen usar los mismos números)
BUTTON_ACCEPT = (0,)          # A
BUTTON_BACK = (1,)            # B
BUTTON_FIRE = (0, 2, 5)       # A, X, RB
BUTTON_PAUSE = (6, 7, 9)      # Back / Start / Options

MENU_KEYS = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_RETURN: "accept", pygame.K_KP_ENTER: "accept", pygame.K_SPACE: "accept",
    pygame.K_BACKSPACE: "back",
    pygame.K_m: "mute",
    pygame.K_F11: "fullscreen",
}
# Teclas que no se pueden asignar a una acción del juego
RESERVED_KEYS = (pygame.K_ESCAPE, pygame.K_m, pygame.K_F11, pygame.K_RETURN, pygame.K_KP_ENTER)


def key_code(name, default):
    try:
        return pygame.key.key_code(name)
    except (ValueError, TypeError):
        return pygame.key.key_code(default)


def key_label(name):
    """Nombre legible de una tecla para mostrar en pantalla."""
    # Sin flechas (← →): la fuente incluida no tiene esos símbolos
    names = {
        "es": {"left": "FLECHA IZQ.", "right": "FLECHA DER.", "up": "FLECHA ARRIBA",
               "down": "FLECHA ABAJO", "space": "ESPACIO"},
        "en": {"left": "LEFT ARROW", "right": "RIGHT ARROW", "up": "UP ARROW",
               "down": "DOWN ARROW", "space": "SPACE"},
    }
    return names.get(get_language(), names["es"]).get(name, name.upper())


class Input:
    def __init__(self, settings):
        self.settings = settings
        self.joysticks = {}
        self._axis_state = {}  # para detectar el movimiento del stick en los menús
        for i in range(pygame.joystick.get_count()):
            self._add_joystick(i)

    # --- Teclas asignadas ---
    def binding(self, action):
        return key_code(self.settings["keys"].get(action, C.DEFAULT_KEYS[action]), C.DEFAULT_KEYS[action])

    def bind(self, action, key):
        """Asigna una tecla a una acción. Si otra acción la usaba, intercambia sus teclas."""
        name = pygame.key.name(key)
        keys = self.settings["keys"]
        for other, other_name in keys.items():
            if other != action and other_name == name:
                keys[other] = keys[action]
        keys[action] = name

    def _alternate(self, key, action):
        """A y D sirven siempre para moverse, salvo que estén asignadas a otra acción."""
        bound = {self.binding(a): a for a in C.DEFAULT_KEYS}
        return key not in bound or bound[key] == action

    # --- Mandos ---
    def _add_joystick(self, index):
        try:
            joy = pygame.joystick.Joystick(index)
            self.joysticks[joy.get_instance_id()] = joy
        except pygame.error:
            pass

    def handle_device_event(self, event):
        if event.type == pygame.JOYDEVICEADDED:
            self._add_joystick(event.device_index)
        elif event.type == pygame.JOYDEVICEREMOVED:
            self.joysticks.pop(event.instance_id, None)

    # --- Eventos -> acciones ---
    def actions(self, event):
        """Acciones generadas por un evento (lista vacía si no corresponde a ninguna)."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return ["back", "pause"]
            result = []
            action = MENU_KEYS.get(event.key)
            if action:
                result.append(action)
            if event.key == self.binding("pause"):
                result.append("pause")
            if event.key == self.binding("fire") and "accept" not in result:
                result.append("accept")
            return result
        if event.type == pygame.JOYBUTTONDOWN:
            result = []
            if event.button in BUTTON_ACCEPT:
                result.append("accept")
            if event.button in BUTTON_BACK:
                result.append("back")
            if event.button in BUTTON_PAUSE:
                result.append("pause")
            return result
        if event.type == pygame.JOYHATMOTION:
            x, y = event.value
            return [a for a, on in (("left", x < 0), ("right", x > 0), ("up", y > 0), ("down", y < 0)) if on]
        if event.type == pygame.JOYAXISMOTION and event.axis in (0, 1):
            key = (event.instance_id, event.axis)
            previous = self._axis_state.get(key, 0)
            current = 0
            if event.value > MENU_AXIS_THRESHOLD:
                current = 1
            elif event.value < -MENU_AXIS_THRESHOLD:
                current = -1
            self._axis_state[key] = current
            if current != previous and current != 0:
                if event.axis == 0:
                    return ["left" if current < 0 else "right"]
                return ["up" if current < 0 else "down"]
        return []

    # --- Estado continuo (durante la partida) ---
    def horizontal(self):
        """Dirección horizontal entre -1 (izquierda) y 1 (derecha)."""
        keys = pygame.key.get_pressed()
        value = 0.0
        if keys[self.binding("left")] or (keys[pygame.K_a] and self._alternate(pygame.K_a, "left")):
            value -= 1
        if keys[self.binding("right")] or (keys[pygame.K_d] and self._alternate(pygame.K_d, "right")):
            value += 1
        for joy in self.joysticks.values():
            if joy.get_numhats() > 0:
                value += joy.get_hat(0)[0]
            if joy.get_numaxes() > 0:
                axis = joy.get_axis(0)
                if abs(axis) > AXIS_DEADZONE:
                    value += axis
        return max(-1.0, min(1.0, value))

    def fire_held(self):
        if pygame.key.get_pressed()[self.binding("fire")]:
            return True
        for joy in self.joysticks.values():
            for button in BUTTON_FIRE:
                if button < joy.get_numbuttons() and joy.get_button(button):
                    return True
        return False
