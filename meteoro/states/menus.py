"""Menú principal, opciones, teclas, controles y tabla de récords."""
import pygame

from .. import config as C
from .. import ui
from ..controls import RESERVED_KEYS, key_label
from ..i18n import LANGUAGE_NAMES, t
from ..storage import LANGUAGES
from .base import WAIT_AFTER_GAME, MenuListState, WaitingState


class MenuState(MenuListState):
    def items(self):
        keys = ["play", "options", "controls", "records"]
        if not C.IS_WEB:  # en el navegador no se puede "salir"
            keys.append("quit")
        return keys

    def handle(self, event, actions):
        if self.move(actions) or "accept" not in actions:
            return
        choice = self.items()[self.selected]
        if choice == "play":
            self.game.go("play")
        elif choice == "options":
            self.game.go("options", back=("menu", 1))
        elif choice == "controls":
            self.game.go("controls")
        elif choice == "records":
            self.game.go("records")
        else:
            self.game.quit()

    def draw(self, surface):
        super().draw(surface)
        ui.draw_text(surface, "METEORO SHOOTER", 50, C.WIDTH // 2, 95, title=True)  # logo
        ui.draw_text(surface, t("record", score=self.game.high_score), 30, C.WIDTH // 2, 172,
                     color=C.YELLOW)
        ui.draw_menu(surface, [t("menu." + k) for k in self.items()], self.selected, 240)
        ui.draw_hint(surface, t("menu.hint"))


class OptionsState(MenuListState):
    """Opciones. `back` indica a dónde volver: ("menu", posición) o un estado ya creado."""

    def __init__(self, game, back):
        super().__init__(game)
        self.back = back

    def items(self):
        keys = ["music", "sfx", "mute", "difficulty", "shake", "language"]
        if not C.IS_WEB:
            keys.append("fullscreen")
        return keys + ["keys", "back"]

    def label(self, key):
        s = self.game.settings
        on_off = lambda v: t("yes") if v else t("no")  # noqa: E731
        if key == "music":
            return t("options.music", bar=self._bar(s["music_volume"]))
        if key == "sfx":
            return t("options.sfx", bar=self._bar(s["sfx_volume"]))
        if key == "mute":
            return t("options.mute", value=on_off(s["muted"]))
        if key == "difficulty":
            return t("options.difficulty", value=t("difficulty." + s["difficulty"]))
        if key == "shake":
            return t("options.shake", value=on_off(s["screen_shake"]))
        if key == "language":
            return t("options.language", value=LANGUAGE_NAMES[s["language"]])
        if key == "fullscreen":
            return t("options.fullscreen", value=on_off(s["fullscreen"]))
        if key == "keys":
            return t("options.keys")
        return t("back")

    @staticmethod
    def _bar(value):
        filled = int(round(value * 10))
        return "[" + "|" * filled + "·" * (10 - filled) + "]"

    def _cycle(self, key, values, step):
        s = self.game.settings
        s[key] = values[(values.index(s[key]) + step) % len(values)]

    def _change(self, key, step):
        s = self.game.settings
        if key in ("music", "sfx"):
            setting = key + "_volume"
            s[setting] = round(min(1.0, max(0.0, s[setting] + 0.1 * step)), 1)
            self.game.audio.apply_volume()
        elif key == "difficulty":
            self._cycle("difficulty", list(C.DIFFICULTY_ORDER), step)
        elif key == "language":
            self.game.set_language(LANGUAGES[(LANGUAGES.index(s["language"]) + step) % len(LANGUAGES)])
        elif key == "shake":
            s["screen_shake"] = not s["screen_shake"]
        elif key == "mute":
            self.game.toggle_mute()
        elif key == "fullscreen":
            self.game.toggle_fullscreen()
        else:
            return
        self.game.audio.play("select")

    def handle(self, event, actions):
        if self.move(actions):
            return
        key = self.items()[self.selected]
        if "left" in actions or "right" in actions:
            self._change(key, 1 if "right" in actions else -1)
        elif "accept" in actions:
            if key == "back":
                self._leave()
            elif key == "keys":
                self.game.save_settings()
                self.game.go("keys", back_options=self)
            else:
                self._change(key, 1)
        elif "back" in actions:
            self._leave()

    def _leave(self):
        self.game.save_settings()
        if isinstance(self.back, tuple):
            self.game.go(self.back[0], self.back[1])
        else:
            self.game.set_state(self.back)

    def draw(self, surface):
        super().draw(surface)
        ui.draw_title(surface, t("options.title"), 40)
        labels = [self.label(k) for k in self.items()]
        ui.draw_menu(surface, labels, self.selected, 115, size=32, spacing=46)
        ui.draw_hint(surface, t("options.hint"), C.HEIGHT - 32)


class KeysState(MenuListState):
    """Reasignar las teclas de mover, disparar y pausa."""
    ACTIONS = ("left", "right", "fire", "pause")

    def __init__(self, game, back_options):
        super().__init__(game)
        self.back_options = back_options
        self.waiting = None  # acción que espera una tecla nueva

    @property
    def allows_shortcuts(self):
        return self.waiting is None

    def items(self):
        return list(self.ACTIONS) + ["reset", "back"]

    def handle(self, event, actions):
        if self.waiting:
            if event.type == pygame.KEYDOWN:
                if event.key not in RESERVED_KEYS:
                    self.game.input.bind(self.waiting, event.key)
                    self.game.audio.play("select")
                self.waiting = None
            return
        if self.move(actions):
            return
        choice = self.items()[self.selected]
        if "accept" in actions:
            if choice in self.ACTIONS:
                self.waiting = choice
            elif choice == "reset":
                self.game.settings["keys"] = dict(C.DEFAULT_KEYS)
                self.game.audio.play("select")
            else:
                self._leave()
        elif "back" in actions:
            self._leave()

    def _leave(self):
        self.game.save_settings()
        self.game.set_state(self.back_options)

    def draw(self, surface):
        super().draw(surface)
        ui.draw_title(surface, t("keys.title"), 50)
        keys = self.game.settings["keys"]
        labels = []
        for choice in self.items():
            if choice in self.ACTIONS:
                labels.append(t("keys." + choice, key=key_label(keys[choice])))
            else:
                labels.append(t("keys.reset") if choice == "reset" else t("back"))
        ui.draw_menu(surface, labels, self.selected, 150, size=34, spacing=52)
        if self.waiting:
            ui.dim(surface, 170)
            ui.draw_text(surface, t("keys.press"), 34, C.WIDTH // 2, C.HEIGHT // 2 - 20, color=C.YELLOW)
        else:
            ui.draw_hint(surface, t("keys.hint"))


class ControlsState(WaitingState):
    def handle(self, event, actions):
        if "accept" in actions or "back" in actions:
            self.game.go("menu", 2)

    def draw(self, surface):
        super().draw(surface)
        ui.draw_title(surface, t("controls.title"), 22)
        keys = {action: key_label(name) for action, name in self.game.settings["keys"].items()}
        lines = (
            (t("controls.move"), t("controls.move.keys", **keys)),
            (t("controls.fire"), t("controls.fire.keys", **keys)),
            (t("controls.pause"), t("controls.pause.keys", **keys)),
            (t("controls.gamepad"), t("controls.gamepad.keys")),
            (t("controls.mute"), "M"),
            (t("controls.fullscreen"), "F11"),
        )
        y = 82
        for name, value in lines:
            ui.draw_text(surface, name, 26, 290, y, color=C.YELLOW, anchor="topright")
            ui.draw_text(surface, value, 26, 310, y, anchor="topleft")
            y += 28
        y += 10
        durations = {"shield": C.SHIELD_RESTORE, "weapon": int(C.WEAPON_TIME),
                     "magnet": int(C.MAGNET_TIME), "slow": int(C.SLOW_TIME)}
        for kind in C.POWERUP_WEIGHTS:
            icon = self.game.images.powerups[kind]
            surface.blit(icon, icon.get_rect(center=(150, y + 9)))
            ui.draw_text(surface, t("powerup." + kind, n=durations.get(kind, "")), 24, 185, y,
                         anchor="topleft")
            y += 31
        ui.draw_text(surface, t("controls.tip1"), 22, C.WIDTH // 2, y + 4, color=C.CYAN)
        ui.draw_text(surface, t("controls.tip2", points=C.EXTRA_LIFE_EVERY, levels=C.BOSS_EVERY),
                     22, C.WIDTH // 2, y + 27, color=C.CYAN)
        ui.draw_hint(surface, t("back.hint"), C.HEIGHT - 26)


class RecordsState(WaitingState):
    def __init__(self, game, highlight=None, after_game=False):
        super().__init__(game)
        self.highlight = highlight
        self.after_game = after_game
        self.wait = WAIT_AFTER_GAME if after_game else 0.0

    def handle(self, event, actions):
        if not self.ready:
            return
        if self.after_game and "accept" in actions:
            self.game.go("play")
        elif "accept" in actions or "back" in actions:
            self.game.go("menu", 3)

    def draw(self, surface):
        super().draw(surface)
        ui.draw_title(surface, t("records.title"), 30)
        scores = self.game.scores
        if not scores:
            ui.draw_text(surface, t("records.empty"), 30, C.WIDTH // 2, C.HEIGHT // 2 - 20)
        else:
            cols = ((190, "#", "topright"), (230, t("records.name"), "topleft"),
                    (470, t("records.points"), "topright"), (560, t("records.level"), "topright"),
                    (640, t("records.difficulty"), "topright"))
            for x, label, anchor in cols:
                ui.draw_text(surface, label, 24, x, 105, color=C.GREY, anchor=anchor)
            for i, entry in enumerate(scores):
                y = 138 + i * 36
                color = C.YELLOW if i == self.highlight else C.WHITE
                values = (i + 1, entry["name"], entry["score"], entry["level"],
                          t("difficulty.short." + entry["difficulty"]))
                for (x, _, anchor), value in zip(cols, values):
                    ui.draw_text(surface, value, 30, x, y, color=color, anchor=anchor)
        if self.ready:
            ui.draw_hint(surface, t("records.hint_after") if self.after_game else t("back.hint"))
