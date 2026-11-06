"""Pausa: congela la partida y la dibuja oscurecida debajo del menú."""
from .. import config as C
from .. import ui
from ..i18n import t
from .base import MenuListState


class PauseState(MenuListState):
    def __init__(self, game, play):
        super().__init__(game)
        self.play = play
        game.audio.pause_music(True)

    def items(self):
        return ["resume", "options", "quit"]

    def update(self, dt):
        pass  # la partida (y el fondo) quedan congelados

    def _resume(self):
        self.game.audio.pause_music(False)
        self.game.set_state(self.play)

    def handle(self, event, actions):
        if "pause" in actions or "back" in actions:
            self._resume()
        elif self.move(actions):
            return
        elif "accept" in actions:
            choice = self.items()[self.selected]
            if choice == "resume":
                self._resume()
            elif choice == "options":
                self.game.go("options", back=self, fade=False)
            else:
                self.game.audio.stop_music()
                self.game.go("menu")

    def draw(self, surface):
        self.play.draw(surface)
        ui.dim(surface)
        ui.draw_title(surface, t("pause.title"), 150, size=56)
        labels = [t("pause.resume"), t("menu.options"), t("pause.quit")]
        ui.draw_menu(surface, labels, self.selected, 270)
        ui.draw_hint(surface, t("menu.hint"), C.HEIGHT - 40)
