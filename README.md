# Python-ShooterMeteoros

Shooter Meteoros es un juego arcade de naves desarrollado en Python con [pygame-ce](https://pyga.me/). Controlas una nave que debe destruir meteoros, naves enemigas y jefes para sumar puntos, recogiendo power-ups por el camino.

## Controles

| Acción | Teclado | Mando |
| --- | --- | --- |
| Mover | `←` `→` o `A` `D` | Stick izquierdo o cruceta |
| Disparar | Mantener `ESPACIO` | Botón A (o X / RB) |
| Pausa | `P` o `ESC` | START |
| Silenciar | `M` | — |
| Pantalla completa | `F11` | — |

En los menús se navega con las flechas (o el mando) y se acepta con `ENTER`. El juego se pausa solo si la ventana pierde el foco.

## Cómo se juega

- **Meteoros que se parten:** los grandes se dividen en dos medianos, y los medianos en dos pequeños. Los meteoros giran mientras caen.
- **Puntos y daño según el tamaño:** los pequeños son más difíciles de acertar y dan más puntos (grande 10, mediano 20, pequeño 40, diminuto 60). Los grandes quitan más escudo al chocar.
- **Combo:** cada 10 aciertos seguidos sube el multiplicador de puntos (×2, ×3, hasta ×4). Fallar un disparo o recibir un golpe lo reinicia.
- **Vidas:** empiezas con 3 naves. Al vaciarse el escudo pierdes una y reapareces con el escudo lleno. Ganas una vida extra cada 5000 puntos (máximo 5).
- **Niveles:** cada nivel pide más puntos que el anterior (700, 2100, 4200, 7000…). En cada uno aparecen más meteoros y caen más rápido.
- **Naves enemigas:** desde el nivel 3 aparecen naves que disparan hacia ti. Necesitan 3 impactos.
- **Jefe:** cada 5 niveles aparece un jefe con barra de vida, que dispara abanicos y ráfagas. Al derrotarlo suelta power-ups.
- **Power-ups** (caen de meteoros y enemigos):
  - **S (verde)**: recupera escudo.
  - **W (celeste)**: disparo doble; si recoges otro mientras dura, disparo triple (10 s).
  - **B (naranja)**: bomba que destruye todo lo que hay en pantalla.

## Récords y opciones

- Se guardan los **10 mejores puntajes** con tus iniciales en `highscores.json`. Si tenías un récord en el antiguo `highscore.txt`, se importa automáticamente.
- En **Opciones** puedes ajustar el volumen de la música y de los efectos, silenciar el juego y activar la pantalla completa. Se guardan en `settings.json`.
- La ventana se puede redimensionar: el juego se escala manteniendo la proporción.

## Requisitos

Necesitas Python y [pygame-ce](https://pyga.me/), una versión de Pygame mantenida por la comunidad que funciona con las versiones recientes de Python. Se usa igual que Pygame (`import pygame`). Instálala con:

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

## Estructura del código

```
shooter.py            Punto de entrada
meteoro/
  config.py           Constantes: tamaños, velocidades, dificultad, rutas
  rules.py            Reglas puras (niveles, puntos, combo, vidas, jefes)
  storage.py          Récords y opciones en JSON
  assets.py           Carga de imágenes y sonidos (y los que se generan por código)
  controls.py         Teclado y mando
  effects.py          Fondo con estrellas en movimiento y partículas
  sprites.py          Nave, meteoros, balas, enemigos, jefe, power-ups, explosiones
  ui.py               Textos, barras y menús
  game.py             Bucle principal y estados (menú, partida, pausa, game over...)
tests/                Pruebas automáticas de rules.py y storage.py
```

Todo el movimiento usa el tiempo real transcurrido (*delta time*), así que la velocidad del juego no depende de los FPS. Para cambiar la dificultad basta con editar los valores de `meteoro/config.py`.

## Pruebas

```sh
python -m unittest discover -s tests -v
```

Las pruebas no necesitan pygame. GitHub Actions las ejecuta en cada *push* a `main` y en cada *pull request*.

## Crear un ejecutable (.exe) para Windows

### Automáticamente con GitHub Actions

Al subir una etiqueta de versión, GitHub genera el `.exe` y lo adjunta a la *release*:

```sh
git tag v1.1
git push origin v1.1
```

También se puede lanzar a mano desde la pestaña **Actions → Publicar .exe → Run workflow**. El `.exe` queda como artefacto descargable.

### A mano

Con [PyInstaller](https://pyinstaller.org/):

```sh
pip install pyinstaller
pyinstaller --onefile --windowed --name MeteoroShooter --add-data "assets;assets" shooter.py
```

El ejecutable queda en `dist/MeteoroShooter.exe`. Los récords y las opciones se guardan junto al `.exe`.
