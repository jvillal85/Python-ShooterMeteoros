# Python-ShooterMeteoros

Shooter Meteoros es un juego desarrollado en Python utilizando la biblioteca Pygame. En este juego, el jugador controla una nave espacial que debe disparar y destruir meteoros para ganar puntos. El juego incluye gráficos, sonidos y animaciones para una experiencia de juego completa.

## Instrucciones

- **Mover Izquierda:** Presiona la flecha izquierda `←`
- **Mover Derecha:** Presiona la flecha derecha `→`
- **Disparar:** Presiona la tecla `ESPACIO`

Al recibir un golpe, la nave parpadea y queda invulnerable por un momento.

## Niveles y récord

- Cada 200 puntos subes de nivel: aparecen más meteoros y caen más rápido.
- Al perder, la pantalla de Game Over muestra tu puntaje, el nivel alcanzado y el récord.
- El récord se guarda en `highscore.txt`, junto al juego.

## Requisitos

Para ejecutar este juego necesitas Python y [pygame-ce](https://pyga.me/), una versión de Pygame mantenida por la comunidad que funciona con las versiones recientes de Python (incluida la 3.14). Se usa igual que Pygame (`import pygame`). Instálala con el archivo `requirements.txt`:

```sh
pip install -r requirements.txt
```

Si ya tenías instalado el `pygame` clásico, desinstálalo antes, porque los dos paquetes usan el mismo nombre de módulo:

```sh
pip uninstall pygame
```

Para jugar:

```sh
python shooter.py
```

## Crear un ejecutable (.exe) para Windows

Con [PyInstaller](https://pyinstaller.org/) puedes generar un único `.exe` que incluye Python, pygame y todos los recursos. Así se puede jugar en otro PC sin instalar nada:

```sh
pip install pyinstaller
pyinstaller --onefile --windowed --name MeteoroShooter --add-data "assets;assets" shooter.py
```

El ejecutable queda en `dist/MeteoroShooter.exe`. El récord se guarda en un archivo `highscore.txt` junto al `.exe`.