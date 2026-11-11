"""Núcleo del juego: ventana, bucle principal y cambio entre pantallas (estados)."""
import asyncio
import math

import pygame

from . import config as C
from . import i18n, storage, ui
from .assets import Audio, Images
from .assets import path as asset_path
from .controls import Input
from .effects import Starfield


class Game:
    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        try:
            pygame.mixer.init()
        except pygame.error:
            pass  # sin dispositivo de sonido: el juego funciona en silencio

        ui.reset_caches()
        self.settings = storage.load_settings()
        i18n.set_language(self.settings["language"])
        try:
            pygame.display.set_icon(pygame.image.load(asset_path("player.png")))
        except pygame.error:
            pass
        # SCALED: el juego se dibuja a 800x600 y se escala a la ventana o pantalla completa
        flags = 0 if C.IS_WEB else pygame.SCALED | pygame.RESIZABLE
        self.screen = pygame.display.set_mode((C.WIDTH, C.HEIGHT), flags)
        pygame.display.set_caption(C.TITLE)
        if self.settings["fullscreen"] and not C.IS_WEB:
            self._toggle_fullscreen_display()

        self.canvas = pygame.Surface((C.WIDTH, C.HEIGHT))
        self.clock = pygame.time.Clock()
        self.images = Images()
        self.audio = Audio(self.settings)
        self.input = Input(self.settings)
        self.starfield = Starfield(self.images.background)
        self.scores = storage.load_scores()
        self.running = True
        self.fade = 0.0
        self.state = None
        self.go("menu", fade=False)

    # --- Opciones -------------------------------------------------------
    def save_settings(self):
        storage.save_settings(self.settings)

    def _toggle_fullscreen_display(self):
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            pass

    def toggle_fullscreen(self):
        if C.IS_WEB:
            return
        self.settings["fullscreen"] = not self.settings["fullscreen"]
        self._toggle_fullscreen_display()
        self.save_settings()

    def toggle_mute(self):
        self.audio.toggle_mute()
        self.save_settings()

    def set_language(self, code):
        self.settings["language"] = code
        i18n.set_language(code)

    @property
    def high_score(self):
        return storage.top_score(self.scores)

    # --- Pantallas --------------------------------------------------------
    def go(self, name, *args, fade=True, **kwargs):
        """Cambia a una pantalla nueva por su nombre (ver STATES)."""
        from .states import STATES  # import tardío: los estados importan este módulo
        self.set_state(STATES[name](self, *args, **kwargs), fade)

    def set_state(self, state, fade=False):
        self.state = state
        if fade:
            self.fade = 1.0

    def quit(self):
        self.running = False

    # --- Bucle principal --------------------------------------------------
    def run(self):
        while self.running:
            dt = min(self.clock.tick(C.FPS) / 1000.0, C.MAX_DT)
            self.step(dt, pygame.event.get())
        pygame.quit()

    async def run_async(self):
        """Bucle para la versión web (pygbag): cede el control al navegador en cada cuadro."""
        while self.running:
            dt = min(self.clock.tick(C.FPS) / 1000.0, C.MAX_DT)
            self.step(dt, pygame.event.get())
            await asyncio.sleep(0)

    def step(self, dt, events):
        """Un cuadro del juego: eventos, lógica (en pasos pequeños) y dibujo."""
        for event in events:
            if event.type == pygame.QUIT:
                self.quit()
                return
            if event.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
                self.input.handle_device_event(event)
            actions = self.input.actions(event)
            if "mute" in actions and self.state.allows_shortcuts:
                self.toggle_mute()
            if "fullscreen" in actions:
                self.toggle_fullscreen()
            self.state.handle(event, actions)

        # Si el cuadro duró mucho, la lógica avanza en varios pasos pequeños: así una bala
        # rápida no atraviesa un meteoro sin chocar aunque el juego vaya lento.
        steps = max(1, math.ceil(dt / C.STEP_DT - 1e-9))
        for _ in range(steps):
            self.state.update(dt / steps)
        self.fade = max(0.0, self.fade - dt / C.FADE_TIME)

        self.state.draw(self.canvas)
        self.screen.fill(C.BLACK)
        self.screen.blit(self.canvas, self.state.offset())
        if self.fade > 0:
            overlay = pygame.Surface((C.WIDTH, C.HEIGHT))
            overlay.set_alpha(int(255 * self.fade))
            self.screen.blit(overlay, (0, 0))
        pygame.display.flip()


def main():
    Game().run()


async def main_async():
    await Game().run_async()
