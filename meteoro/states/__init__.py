"""Pantallas del juego. Game.go("nombre", ...) crea la pantalla por su nombre, así
las pantallas no necesitan importarse entre sí."""
from .endgame import GameOverState, NameEntryState
from .menus import ControlsState, KeysState, MenuState, OptionsState, RecordsState
from .pause import PauseState
from .play import PlayState

STATES = {
    "menu": MenuState,
    "options": OptionsState,
    "keys": KeysState,
    "controls": ControlsState,
    "records": RecordsState,
    "play": PlayState,
    "pause": PauseState,
    "gameover": GameOverState,
    "name": NameEntryState,
}
