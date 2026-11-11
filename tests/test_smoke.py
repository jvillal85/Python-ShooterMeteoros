"""Prueba de humo: juega partidas completas sin ventana ni sonido (SDL "dummy") y
recorre todas las pantallas, para detectar errores que los tests de lógica no ven.
Se salta si pygame no está instalado."""
import os
import random
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

try:
    import pygame
except ImportError:  # pragma: no cover
    pygame = None

from meteoro import config as C
from meteoro import i18n


def key(k, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=unicode, mod=0, scancode=0)


@unittest.skipIf(pygame is None, "pygame no está instalado")
class SmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = (C.HIGHSCORES_FILE, C.SETTINGS_FILE, C.LEGACY_HIGHSCORE_FILE)
        C.HIGHSCORES_FILE = os.path.join(self.tmp.name, "highscores.json")
        C.SETTINGS_FILE = os.path.join(self.tmp.name, "settings.json")
        C.LEGACY_HIGHSCORE_FILE = os.path.join(self.tmp.name, "highscore.txt")
        random.seed(1)
        from meteoro.game import Game
        self.game = Game()

    def tearDown(self):
        C.HIGHSCORES_FILE, C.SETTINGS_FILE, C.LEGACY_HIGHSCORE_FILE = self.saved
        i18n.set_language("es")
        pygame.quit()
        self.tmp.cleanup()

    # --- ayudas ---
    def frames(self, n=1, events=()):
        for i in range(n):
            self.game.step(1 / 60, list(events) if i == 0 else [])

    def press(self, k, unicode=""):
        self.frames(1, [key(k, unicode)])

    def state(self):
        return type(self.game.state).__name__

    def choose(self, index):
        self.game.state.selected = index
        self.press(pygame.K_RETURN)

    # --- pruebas ---
    def test_menus_options_and_keys(self):
        game = self.game
        self.choose(1)
        self.assertEqual(self.state(), "OptionsState")
        for i, item in enumerate(game.state.items()):
            game.state.selected = i
            if item not in ("keys", "back"):
                self.press(pygame.K_RIGHT)
                self.press(pygame.K_LEFT)
                self.press(pygame.K_RIGHT)
            self.frames(2)
        self.assertEqual(game.settings["language"], "en")
        self.assertEqual(i18n.t("menu.play"), "Play")

        game.state.selected = game.state.items().index("keys")
        self.press(pygame.K_RETURN)
        self.assertEqual(self.state(), "KeysState")
        self.press(pygame.K_RETURN)          # cambiar "izquierda"
        self.press(pygame.K_j)
        self.assertEqual(game.settings["keys"]["left"], "j")
        game.state.selected = 2
        self.press(pygame.K_RETURN)          # "disparar" pasa a la J: se intercambian
        self.press(pygame.K_j)
        self.assertEqual(game.settings["keys"]["fire"], "j")
        self.assertEqual(game.settings["keys"]["left"], "space")
        game.state.selected = 4
        self.press(pygame.K_RETURN)          # restaurar
        self.assertEqual(game.settings["keys"], C.DEFAULT_KEYS)
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.state(), "OptionsState")
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.state(), "MenuState")

        for index, name in ((2, "ControlsState"), (3, "RecordsState")):
            self.choose(index)
            self.assertEqual(self.state(), name)
            self.frames(30)
            self.press(pygame.K_ESCAPE)
            self.assertEqual(self.state(), "MenuState")
        self.assertTrue(os.path.exists(C.SETTINGS_FILE))

    def test_full_game(self):
        game = self.game
        self.choose(0)
        play = game.state
        self.assertEqual(self.state(), "PlayState")
        game.input.fire_held = lambda: True
        game.input.horizontal = lambda: random.uniform(-1, 1)

        self.frames(60 * 10)
        self.assertGreater(play.score, 0)

        # Pausa y opciones desde la pausa
        self.press(pygame.K_p)
        self.assertEqual(self.state(), "PauseState")
        self.choose(1)
        self.assertEqual(self.state(), "OptionsState")
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.state(), "PauseState")
        self.press(pygame.K_p)
        self.assertIs(game.state, play)

        # Todos los power-ups
        play.player.invulnerable_until = 1e9
        for kind in C.POWERUP_WEIGHTS:
            play.apply_powerup(kind)
        play.apply_powerup("weapon")
        self.assertEqual(play.player.weapon_level, 3)
        self.assertTrue(play.slow_active() and play.magnet_active() and play.player.bubble)
        self.frames(60 * 3)

        # La burbuja absorbe un golpe
        shield = play.player.shield
        play.player.invulnerable_until = 0
        play.damage_player(50, play.player.rect.center)
        self.assertEqual(play.player.shield, shield)
        self.assertFalse(play.player.bubble)
        play.player.invulnerable_until = 1e9

        # Cada tipo de enemigo y el jefe con todos sus ataques
        for kind in C.ENEMY_TYPES:
            play.spawn_enemy(kind)
        play.score = 5000 * 21  # nivel ~ 18: tercer jefe
        self.frames(60 * 12)
        self.assertGreaterEqual(play.level, 15)
        self.assertEqual(play.spawner.bosses_spawned, play.level // C.BOSS_EVERY)
        boss = play.boss
        if boss:
            self.assertIn("summon", boss.attacks)
            boss.damage(boss.hp - 1, play.world_now)
            play.detonate_bomb()
            self.assertIsNone(play.boss)

        # Un paso de tiempo largo se divide en subpasos sin errores
        game.step(0.1, [])

        # Perder todas las vidas
        play.player.invulnerable_until = 0
        for _ in range(60 * 30):
            if self.state() != "PlayState":
                break
            if play.phase == "playing" and not play.player.is_invulnerable(play.now):
                play.player.bubble = False
                play.damage_player(500, play.player.rect.center)
            self.frames(1)
        self.assertEqual(self.state(), "GameOverState")

        # Récord: escribir iniciales y verlas en la tabla
        self.frames(60)
        self.press(pygame.K_RETURN)
        self.assertEqual(self.state(), "NameEntryState")
        for ch in "mdw":
            self.press(getattr(pygame, "K_" + ch), ch)
        self.press(pygame.K_RETURN)
        self.assertEqual(self.state(), "RecordsState")
        self.assertEqual(game.scores[0]["name"], "MDW")
        self.assertFalse(game.settings["muted"])  # la M se escribió, no silenció
        self.frames(60)
        self.press(pygame.K_ESCAPE)
        self.assertEqual(self.state(), "MenuState")
        self.assertTrue(os.path.exists(C.HIGHSCORES_FILE))

    def test_every_screen_draws_in_english(self):
        game = self.game
        game.set_language("en")
        from meteoro.states import STATES
        play = STATES["play"](game)
        screens = [
            STATES["menu"](game), STATES["options"](game, back=("menu", 0)),
            STATES["keys"](game, back_options=None), STATES["controls"](game),
            STATES["records"](game), play, STATES["pause"](game, play),
            STATES["gameover"](game, 1234, 3, 12, "hard"), STATES["name"](game, 1234, 3, "hard"),
        ]
        for screen in screens:
            game.set_state(screen)
            self.frames(5)


if __name__ == "__main__":
    unittest.main()
