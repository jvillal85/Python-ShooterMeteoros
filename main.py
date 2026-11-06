"""Punto de entrada de la versión web (pygbag). Para jugar en el escritorio usa shooter.py."""
import asyncio

from meteoro.game import main_async

asyncio.run(main_async())
