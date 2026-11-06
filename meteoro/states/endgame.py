"""Fin de la partida: pantalla de Game Over e ingreso de iniciales para el récord."""
import pygame

from .. import config as C
from .. import storage, ui
from ..i18n import t
from .base import WAIT_AFTER_GAME, WaitingState

NAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


class GameOverState(WaitingState):
    wait = WAIT_AFTER_GAME

    def __init__(self, game, score, level, best_combo, difficulty):
        super().__init__(game)
        self.score = score
        self.level = level
        self.best_combo = best_combo
        self.difficulty = difficulty
        self.new_record = score > game.high_score
        self.qualifies = storage.qualifies(game.scores, score)
        game.audio.stop_music()
        game.audio.play("gameover")

    def handle(self, event, actions):
        if not self.ready:
            return
        if self.qualifies and ("accept" in actions or "back" in actions):
            self.game.go("name", self.score, self.level, self.difficulty)
        elif "accept" in actions:
            self.game.go("play")
        elif "back" in actions:
            self.game.go("menu")

    def draw(self, surface):
        super().draw(surface)
        ui.draw_title(surface, t("gameover.title"), 110, size=64)
        ui.draw_text(surface, t("gameover.score", score=self.score), 42, C.WIDTH // 2, 235)
        ui.draw_text(surface, t("gameover.stats", level=self.level, combo=self.best_combo), 28,
                     C.WIDTH // 2, 290)
        if self.new_record:
            ui.draw_title(surface, t("gameover.new_record"), 340, size=34, color=C.YELLOW)
        elif self.qualifies:
            ui.draw_text(surface, t("gameover.top", n=C.HIGHSCORE_SLOTS), 36, C.WIDTH // 2, 340,
                         color=C.YELLOW)
        else:
            ui.draw_text(surface, t("record", score=self.game.high_score), 30, C.WIDTH // 2, 345)
        if self.ready:
            hint = t("gameover.hint_name") if self.qualifies else t("gameover.hint_again")
            ui.draw_text(surface, hint, 26, C.WIDTH // 2, C.HEIGHT - 120)


class NameEntryState(WaitingState):
    """Ingreso de iniciales al estilo arcade: ↑↓ cambia la letra, ←→ cambia de posición,
    o se puede escribir directamente con el teclado."""
    allows_shortcuts = False  # la M se escribe, no silencia

    def __init__(self, game, score, level, difficulty):
        super().__init__(game)
        self.score = score
        self.level = level
        self.difficulty = difficulty
        self.letters = list(game.settings["player_name"])
        self.cursor = 0

    def _set_char(self, char):
        self.letters[self.cursor] = char
        self.cursor = min(C.NAME_LENGTH - 1, self.cursor + 1)

    def _cycle(self, step):
        index = NAME_CHARS.find(self.letters[self.cursor])
        self.letters[self.cursor] = NAME_CHARS[(index + step) % len(NAME_CHARS)]

    def _confirm(self):
        name = "".join(self.letters)
        game = self.game
        game.settings["player_name"] = name
        game.save_settings()
        game.scores, position = storage.insert_score(game.scores, name, self.score, self.level,
                                                     self.difficulty)
        storage.save_scores(game.scores)
        game.go("records", highlight=position, after_game=True)

    def handle(self, event, actions):
        if event.type == pygame.KEYDOWN:
            # Las letras se escriben tal cual (incluidas W, A, S y D, que en los menús mueven)
            char = event.unicode.upper() if event.unicode else ""
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._confirm()
                return
            if event.key == pygame.K_BACKSPACE:
                self.cursor = max(0, self.cursor - 1)
                return
            if len(char) == 1 and char in NAME_CHARS:
                self._set_char(char)
                return
        if "up" in actions:
            self._cycle(1)
        elif "down" in actions:
            self._cycle(-1)
        elif "left" in actions:
            self.cursor = max(0, self.cursor - 1)
        elif "right" in actions:
            self.cursor = min(C.NAME_LENGTH - 1, self.cursor + 1)
        elif "accept" in actions:
            if self.cursor < C.NAME_LENGTH - 1:
                self.cursor += 1
            else:
                self._confirm()

    def draw(self, surface):
        super().draw(surface)
        ui.draw_title(surface, t("name.title"), 80, size=46, color=C.YELLOW)
        ui.draw_text(surface, t("name.score", score=self.score), 38, C.WIDTH // 2, 160)
        ui.draw_text(surface, t("name.prompt"), 30, C.WIDTH // 2, 230)
        for i, letter in enumerate(self.letters):
            x = C.WIDTH // 2 + (i - 1) * 80
            active = i == self.cursor
            ui.draw_text(surface, letter, 90, x, 280, color=C.YELLOW if active else C.WHITE)
            if active:
                pygame.draw.rect(surface, C.YELLOW, (x - 28, 370, 56, 5))
        ui.draw_hint(surface, t("name.hint"), C.HEIGHT - 60)
