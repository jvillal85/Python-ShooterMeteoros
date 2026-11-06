"""Controles: teclado (flechas o A/D) y mando (gamepad).

Los eventos se traducen a acciones ("up", "down", "left", "right", "accept",
"back", "pause", "mute", "fullscreen") para que menús y juego no dependan de la
tecla o botón concreto."""
import pygame

AXIS_DEADZONE = 0.35
MENU_AXIS_THRESHOLD = 0.6

# Botones de un mando tipo Xbox en SDL (otros mandos suelen usar los mismos números)
BUTTON_ACCEPT = (0,)          # A
BUTTON_BACK = (1,)            # B
BUTTON_FIRE = (0, 2, 5)       # A, X, RB
BUTTON_PAUSE = (6, 7, 9)      # Back / Start / Options

KEY_ACTIONS = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
    pygame.K_RETURN: "accept", pygame.K_KP_ENTER: "accept", pygame.K_SPACE: "accept",
    pygame.K_ESCAPE: "back", pygame.K_BACKSPACE: "back",
    pygame.K_p: "pause",
    pygame.K_m: "mute",
    pygame.K_F11: "fullscreen",
}


class Input:
    def __init__(self):
        self.joysticks = {}
        self._axis_state = {}  # para detectar el movimiento del stick en los menús
        for i in range(pygame.joystick.get_count()):
            self._add_joystick(i)

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

    def actions(self, event):
        """Acciones generadas por un evento (lista vacía si no corresponde a ninguna)."""
        if event.type == pygame.KEYDOWN:
            action = KEY_ACTIONS.get(event.key)
            if event.key == pygame.K_ESCAPE:
                return ["back", "pause"]
            return [action] if action else []
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

    def horizontal(self):
        """Dirección horizontal entre -1 (izquierda) y 1 (derecha)."""
        keys = pygame.key.get_pressed()
        value = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            value -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
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
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            return True
        for joy in self.joysticks.values():
            for button in BUTTON_FIRE:
                if button < joy.get_numbuttons() and joy.get_button(button):
                    return True
        return False
