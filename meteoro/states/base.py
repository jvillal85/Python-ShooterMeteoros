"""Clase base de las pantallas (estados) del juego."""
from .. import config as C


class State:
    allows_shortcuts = True  # M silencia; se desactiva donde se escriben letras

    def __init__(self, game):
        self.game = game

    def handle(self, event, actions):
        pass

    def update(self, dt):
        pass

    def draw(self, surface):
        pass

    def offset(self):
        return (0, 0)


class WaitingState(State):
    """Pantalla con fondo animado que puede ignorar teclas durante un instante,
    para no saltarla sin querer al llegar desde la partida."""
    wait = 0.0

    def __init__(self, game):
        super().__init__(game)
        self.elapsed = 0.0

    @property
    def ready(self):
        return self.elapsed >= self.wait

    def update(self, dt):
        self.elapsed += dt
        self.game.starfield.update(dt)

    def draw(self, surface):
        self.game.starfield.draw(surface)


class MenuListState(WaitingState):
    """Pantalla con una lista de opciones que se recorre con ↑ ↓."""

    def __init__(self, game, selected=0):
        super().__init__(game)
        self.selected = selected

    def items(self):
        return []

    def move(self, actions):
        """Mueve la selección; devuelve True si hubo movimiento."""
        count = len(self.items())
        if "up" in actions:
            self.selected = (self.selected - 1) % count
        elif "down" in actions:
            self.selected = (self.selected + 1) % count
        else:
            return False
        self.game.audio.play("select")
        return True


WAIT_AFTER_GAME = C.START_DELAY
