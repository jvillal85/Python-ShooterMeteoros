# Python-ShooterMeteoros

Shooter Meteoros es un juego arcade de naves desarrollado en Python con [pygame-ce](https://pyga.me/). Controlas una nave que debe destruir meteoros, naves enemigas y jefes para sumar puntos, recogiendo power-ups por el camino. Se puede jugar en el escritorio (Windows, macOS, Linux) o en el navegador.

## Controles

| Acción | Teclado | Mando |
| --- | --- | --- |
| Mover | Flechas `←` `→` o `A` `D` | Stick izquierdo o cruceta |
| Disparar | Mantener `ESPACIO` | Botón A (o X / RB) |
| Pausa | `P` o `ESC` | START |
| Silenciar | `M` | — |
| Pantalla completa | `F11` | — |

Las teclas de mover, disparar y pausa se pueden cambiar en **Opciones → Cambiar teclas**. En los menús se navega con las flechas (o el mando) y se acepta con `ENTER`. El juego se pausa solo si la ventana pierde el foco.

## Cómo se juega

- **Meteoros que se parten:** los grandes se dividen en dos medianos, y los medianos en dos pequeños. Los meteoros giran mientras caen.
- **Puntos y daño según el tamaño:** los pequeños son más difíciles de acertar y dan más puntos (grande 10, mediano 20, pequeño 40, diminuto 60). Los grandes quitan más escudo al chocar.
- **Combo:** cada 10 aciertos seguidos sube el multiplicador de puntos (×2, ×3, hasta ×4). Fallar un disparo o recibir un golpe lo reinicia.
- **Vidas:** empiezas con 3 naves. Al vaciarse el escudo pierdes una y reapareces con el escudo lleno. Ganas una vida extra cada 5000 puntos (máximo 5).
- **Niveles:** cada nivel pide más puntos que el anterior (700, 2100, 4200, 7000…); la barrita bajo el puntaje muestra cuánto falta. En cada nivel aparecen más meteoros y caen más rápido.
- **Naves enemigas:**
  - Desde el nivel 3, naves rojas que te disparan (3 impactos).
  - Desde el nivel 4, kamikazes verdes: se detienen, parpadean y se lanzan contra ti (1 impacto).
  - Desde el nivel 6, naves azules que disparan en abanico (5 impactos).
- **Jefe cada 5 niveles**, con barra de vida. Cada jefe nuevo suma un ataque: abanico y ráfagas dirigidas; desde el segundo, una espiral de balas; desde el tercero, llama a kamikazes. Al derrotarlo suelta power-ups.
- **Power-ups** (caen de meteoros y enemigos):

  | Power-up | Efecto |
  | --- | --- |
  | Escudo (verde) | Recupera 30 de escudo |
  | Rayo (amarillo) | Disparo doble; si recoges otro mientras dura, triple (10 s) |
  | Estrella (roja) | Bomba: destruye todo lo que hay en pantalla |
  | Escudo (celeste) | Burbuja: absorbe el próximo golpe entero |
  | Imán (dorado) | Atrae los power-ups cercanos (10 s) |
  | Estrella (azul) | Cámara lenta: meteoros y enemigos van más despacio (6 s) |
  | Píldora (roja) | Vida extra |

## Opciones

- **Dificultad:** Fácil, Normal o Difícil. Cambia la velocidad de los meteoros, el daño que recibes y la frecuencia de disparo enemiga.
- **Volumen** de música y efectos, y **silencio**.
- **Sacudida de pantalla** activada o desactivada.
- **Idioma:** español o inglés.
- **Pantalla completa.** La ventana también se puede redimensionar: el juego se escala manteniendo la proporción.
- **Cambiar teclas.**

Las opciones se guardan en `settings.json`.

## Récords

Se guardan los **10 mejores puntajes** con tus iniciales, el nivel alcanzado y la dificultad, en `highscores.json`. Si tenías un récord en el antiguo `highscore.txt`, se importa automáticamente.

## Requisitos

Necesitas Python 3.9 o posterior y [pygame-ce](https://pyga.me/), una versión de Pygame mantenida por la comunidad que funciona con las versiones recientes de Python. Se usa igual que Pygame (`import pygame`). Instálala con:

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

## Jugar en el navegador

El workflow **Versión web** publica el juego en GitHub Pages en cada *push* a `main`, usando [pygbag](https://pygame-web.github.io/). Hay que activar Pages una sola vez: **Settings → Pages → Source: GitHub Actions**. El juego queda en `https://<usuario>.github.io/<repositorio>/`.

Para probar la versión web en tu equipo:

```sh
pip install pygbag
mkdir -p /tmp/meteoroshooter && cp -r main.py meteoro assets /tmp/meteoroshooter/
python -m pygbag /tmp/meteoroshooter
```

y abre http://localhost:8000. La primera vez el navegador descarga el intérprete de Python para la web, así que tarda unos segundos.

## Estructura del código

```
shooter.py              Punto de entrada (escritorio)
main.py                 Punto de entrada (navegador, pygbag)
meteoro/
  config.py             Constantes: tamaños, velocidades, dificultades, enemigos, power-ups
  rules.py              Reglas puras (niveles, puntos, combo, vidas, jefes)
  storage.py            Récords y opciones en JSON
  i18n.py               Textos en español e inglés
  assets.py             Carga de imágenes y sonidos (con caché de rotaciones)
  controls.py           Teclado (teclas reasignables) y mando
  effects.py            Fondo con estrellas en movimiento y partículas
  sprites.py            Nave, meteoros, balas, enemigos, jefe, power-ups, explosiones
  spawner.py            Aparición de meteoros, enemigos y jefes
  collisions.py         Choques
  hud.py                Interfaz durante la partida
  ui.py                 Textos (con caché), barras y menús
  game.py               Bucle principal, subpasos de física y fundidos entre pantallas
  states/               Pantallas: menús, partida, pausa, game over, récords
assets/                 Recursos originales del juego
assets/kenney/          Naves, power-ups, fuente y sonidos de Kenney (CC0)
assets/sfx/             Sonidos generados con tools/generate_sounds.py
tests/                  Tests de la lógica y prueba de humo (partidas completas sin ventana)
tools/                  Generador de sonidos
```

Todo el movimiento usa el tiempo real transcurrido (*delta time*), y si un cuadro tarda mucho la lógica avanza en varios pasos pequeños, para que las balas rápidas no atraviesen meteoros. Para cambiar la dificultad basta con editar los valores de `meteoro/config.py`.

## Pruebas y revisión de código

```sh
pip install -r requirements-dev.txt
ruff check .          # estilo y errores comunes
mypy                  # tipos de la lógica pura
python -m unittest discover -s tests -v
```

La prueba de humo (`tests/test_smoke.py`) juega partidas completas sin ventana ni sonido y recorre todas las pantallas; se salta si pygame no está instalado. GitHub Actions ejecuta todo esto en cada *push* a `main` y en cada *pull request*.

## Crear ejecutables

### Automáticamente con GitHub Actions

Al subir una etiqueta de versión, GitHub genera ejecutables para **Windows, macOS y Linux** y los adjunta a la *release*:

```sh
git tag v1.1
git push origin v1.1
```

También se puede lanzar a mano desde **Actions → Publicar ejecutables → Run workflow**; los archivos quedan como artefactos descargables.

### A mano

Con [PyInstaller](https://pyinstaller.org/) (en Windows el separador de `--add-data` es `;`, en macOS y Linux es `:`):

```sh
pip install pyinstaller
pyinstaller --onefile --windowed --name MeteoroShooter --add-data "assets;assets" shooter.py
```

El ejecutable queda en `dist/`. Los récords y las opciones se guardan junto a él.

## Créditos

- Naves enemigas, power-ups, fuente *Kenvector Future* y varios efectos de sonido: [Kenney](https://www.kenney.nl/) — *Space Shooter Redux*, licencia CC0 (ver `assets/kenney/LICENSE-kenney.txt`).
