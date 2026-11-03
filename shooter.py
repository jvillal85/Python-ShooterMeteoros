import os
import random
import sys

import pygame

WIDTH = 800
HEIGHT = 600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

# Rutas relativas al archivo, para que el juego funcione desde cualquier carpeta.
# Empaquetado como .exe (PyInstaller), los recursos están en sys._MEIPASS y el
# récord se guarda junto al ejecutable.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCES_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCES_DIR = BASE_DIR
ASSETS_DIR = os.path.join(RESOURCES_DIR, "assets")


def asset(name):
    return os.path.join(ASSETS_DIR, name)


INVULNERABLE_MS = 1500   # tiempo de invulnerabilidad tras recibir un golpe
BLINK_MS = 100           # velocidad del parpadeo de la nave
SHAKE_MS = 300           # duración de la sacudida de pantalla
SHAKE_INTENSITY = 8      # desplazamiento máximo en píxeles
START_DELAY_MS = 600     # tiempo antes de aceptar teclas en la pantalla de inicio

# Dificultad
POINTS_PER_LEVEL = 200   # puntos necesarios para subir de nivel
BASE_METEORS = 8         # meteoros en pantalla en el nivel 1
METEORS_PER_LEVEL = 2    # meteoros extra por cada nivel
MAX_METEORS = 20         # límite de meteoros en pantalla
MAX_SPEED_BONUS = 6      # velocidad extra máxima de los meteoros
LEVEL_MSG_MS = 1500      # duración del aviso "NIVEL X"

HIGHSCORE_FILE = os.path.join(BASE_DIR, "highscore.txt")

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("shooter - By jvilla")
clock = pygame.time.Clock()

# Todo se dibuja en este lienzo y luego se copia a la pantalla (permite la sacudida)
canvas = pygame.Surface((WIDTH, HEIGHT))

# Las fuentes se crean una sola vez y se reutilizan
_fonts = {}


def get_font(size):
    if size not in _fonts:
        _fonts[size] = pygame.font.SysFont("serif", size)
    return _fonts[size]


def quit_game():
    pygame.quit()
    sys.exit()


def load_high_score():
    try:
        with open(HIGHSCORE_FILE, encoding="utf-8") as f:
            return int(f.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def save_high_score(value):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            f.write(str(value))
    except OSError:
        pass  # si no se puede guardar, el juego sigue igual


def level_for_score(points):
    return 1 + points // POINTS_PER_LEVEL


def meteors_for_level(lvl):
    return min(BASE_METEORS + (lvl - 1) * METEORS_PER_LEVEL, MAX_METEORS)


def draw_text(surface, text, size, x, y):
    text_surface = get_font(size).render(text, True, WHITE)
    text_rect = text_surface.get_rect()
    text_rect.midtop = (x, y)
    surface.blit(text_surface, text_rect)


def draw_shield_bar(surface, x, y, percentage):
    BAR_LENGTH = 100
    BAR_HEIGHT = 10
    percentage = max(0, percentage)
    fill_width = (percentage / 100) * BAR_LENGTH
    border = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill = pygame.Rect(x, y, fill_width, BAR_HEIGHT)
    pygame.draw.rect(surface, GREEN, fill)
    pygame.draw.rect(surface, WHITE, border, 2)


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.base_image = player_img
        self.image = self.base_image
        self.rect = self.image.get_rect()
        # Radio de colisión algo menor que la imagen, para que los choques sean justos
        self.radius = int(self.rect.width * 0.4)
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - 10
        self.speed_x = 0
        self.shield = 100
        self.invulnerable_until = 0

    def is_invulnerable(self):
        return pygame.time.get_ticks() < self.invulnerable_until

    def take_hit(self, damage):
        self.shield -= damage
        self.invulnerable_until = pygame.time.get_ticks() + INVULNERABLE_MS

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)
        laser_sound.play()

    def update(self):
        self.speed_x = 0
        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            self.speed_x = -5
        if keystate[pygame.K_RIGHT]:
            self.speed_x = 5
        self.rect.x += self.speed_x

        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

        # Parpadeo mientras la nave es invulnerable
        if self.is_invulnerable() and (pygame.time.get_ticks() // BLINK_MS) % 2:
            self.image = blank_img
        else:
            self.image = self.base_image


class Meteor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = random.choice(meteor_images)
        self.rect = self.image.get_rect()
        self.radius = int(self.rect.width * 0.42)
        self.respawn()

    def respawn(self):
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-140, -100)
        # Cuanto mayor el nivel, más rápido caen los meteoros
        bonus = min(level - 1, MAX_SPEED_BONUS)
        self.speedy = random.randrange(1 + bonus // 2, 10 + bonus)
        self.speedx = random.randint(-5, 5)

    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx
        if self.rect.top > HEIGHT + 10 or self.rect.left < -40 or self.rect.right > WIDTH + 40:
            self.respawn()


# Carga y da movimiento a las balas.
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.y = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super().__init__()
        self.image = explosion_anim[0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50  # velocidad de la explosión

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.frame_rate:
            self.last_update = now
            self.frame += 1
            if self.frame == len(explosion_anim):
                self.kill()
            else:
                center = self.rect.center
                self.image = explosion_anim[self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center


# Pantalla de inicio (first_time=True) o de game over
def show_go_screen(first_time, final_score=0, new_record=False):
    screen.blit(background, [0, 0])
    if first_time:
        draw_text(screen, "=[METEORO SHOOTER]=", 65, WIDTH // 2, HEIGHT // 4)
        draw_text(screen, "Récord: {}".format(high_score), 27, WIDTH // 2, HEIGHT // 4 + 85)
        draw_text(screen, "Instrucciones:", 27, WIDTH // 2, HEIGHT // 2)
        draw_text(screen, "ESPACIO = Disparar", 27, WIDTH // 2, (HEIGHT // 2) + 30)
        draw_text(screen, "Flecha izquierda = Mover a la izquierda", 27, WIDTH // 2, (HEIGHT // 2) + 60)
        draw_text(screen, "Flecha derecha = Mover a la derecha", 27, WIDTH // 2, (HEIGHT // 2) + 90)
        draw_text(screen, "Presiona una tecla para comenzar", 20, WIDTH // 2, HEIGHT * 3 / 4 + 20)
    else:
        draw_text(screen, "GAME OVER", 80, WIDTH // 2, HEIGHT // 4)
        draw_text(screen, "Puntaje: {}".format(final_score), 36, WIDTH // 2, HEIGHT // 2 - 20)
        draw_text(screen, "Nivel alcanzado: {}".format(level_for_score(final_score)), 27,
                  WIDTH // 2, HEIGHT // 2 + 25)
        if new_record:
            draw_text(screen, "¡NUEVO RÉCORD!", 36, WIDTH // 2, HEIGHT // 2 + 65)
        else:
            draw_text(screen, "Récord: {}".format(high_score), 27, WIDTH // 2, HEIGHT // 2 + 65)
        draw_text(screen, "Presiona una tecla para jugar de nuevo", 20, WIDTH // 2, HEIGHT * 3 / 4 + 20)
    pygame.display.flip()

    # Descarta teclas presionadas durante la partida anterior y espera un instante,
    # para no empezar una partida nueva sin querer.
    shown_at = pygame.time.get_ticks()
    pygame.event.clear()
    while True:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_game()
            if (event.type == pygame.KEYDOWN
                    and pygame.time.get_ticks() - shown_at > START_DELAY_MS):
                return


# Cargar imágenes
def load_image(name, colorkey=BLACK):
    img = pygame.image.load(asset(name)).convert()
    img.set_colorkey(colorkey)
    return img


player_img = load_image("player.png")
blank_img = pygame.Surface(player_img.get_size(), pygame.SRCALPHA)
bullet_img = load_image("laser1.png")

meteor_files = ["meteorGrey_big1.png", "meteorGrey_big2.png", "meteorGrey_big3.png", "meteorGrey_big4.png",
                "meteorGrey_med1.png", "meteorGrey_med2.png",
                "meteorGrey_small1.png", "meteorGrey_small2.png",
                "meteorGrey_tiny1.png", "meteorGrey_tiny2.png"]
meteor_images = [load_image(f) for f in meteor_files]

# Explosiones
explosion_anim = []
for i in range(9):
    img = load_image("regularExplosion0{}.png".format(i))
    explosion_anim.append(pygame.transform.scale(img, (70, 70)))

background = pygame.image.load(asset("background.png")).convert()

# Cargar sonidos
laser_sound = pygame.mixer.Sound(asset("laser5.ogg"))
explosion_sound = pygame.mixer.Sound(asset("explosion.wav"))
pygame.mixer.music.load(asset("music.ogg"))
pygame.mixer.music.set_volume(0.1)


def add_meteor():
    meteor = Meteor()
    all_sprites.add(meteor)
    meteors.add(meteor)


high_score = load_high_score()
game_over = True
first_game = True
running = True
shake_until = 0
score = 0
level = 1
level_msg_until = 0

while running:
    if game_over:
        if first_game:
            show_go_screen(first_time=True)
            first_game = False
        else:
            pygame.mixer.music.stop()
            new_record = score > high_score
            if new_record:
                high_score = score
                save_high_score(high_score)
            show_go_screen(first_time=False, final_score=score, new_record=new_record)

        game_over = False
        all_sprites = pygame.sprite.Group()
        meteors = pygame.sprite.Group()
        bullets = pygame.sprite.Group()

        score = 0
        level = 1
        level_msg_until = 0
        shake_until = 0

        player = Player()
        all_sprites.add(player)
        for i in range(meteors_for_level(level)):
            add_meteor()

        pygame.mixer.music.play(loops=-1)

    clock.tick(60)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    all_sprites.update()

    # Colisiones meteoro - láser
    hits = pygame.sprite.groupcollide(meteors, bullets, True, True)
    for hit in hits:
        score += 10
        explosion_sound.play()
        all_sprites.add(Explosion(hit.rect.center))
        add_meteor()

    # Subida de nivel: más meteoros y más rápidos
    new_level = level_for_score(score)
    if new_level > level:
        level = new_level
        level_msg_until = pygame.time.get_ticks() + LEVEL_MSG_MS
        while len(meteors) < meteors_for_level(level):
            add_meteor()

    # Colisiones jugador - meteoro (círculos, y solo si la nave no es invulnerable)
    if not player.is_invulnerable():
        hits = pygame.sprite.spritecollide(player, meteors, True, pygame.sprite.collide_circle)
        if hits:
            hit = hits[0]
            player.take_hit(25 * len(hits))
            explosion_sound.play()
            all_sprites.add(Explosion(hit.rect.center))
            shake_until = pygame.time.get_ticks() + SHAKE_MS
            for _ in hits:
                add_meteor()
            if player.shield <= 0:
                game_over = True

    canvas.blit(background, [0, 0])
    all_sprites.draw(canvas)
    draw_text(canvas, str(score), 25, WIDTH // 2, 10)
    draw_shield_bar(canvas, 5, 5, player.shield)
    draw_text(canvas, "Nivel {}".format(level), 20, 45, 20)
    draw_text(canvas, "Récord: {}".format(max(high_score, score)), 20, WIDTH - 70, 10)
    if pygame.time.get_ticks() < level_msg_until:
        draw_text(canvas, "NIVEL {}".format(level), 60, WIDTH // 2, HEIGHT // 3)

    # Sacudida de pantalla tras recibir un golpe
    offset = (0, 0)
    if pygame.time.get_ticks() < shake_until:
        offset = (random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY),
                  random.randint(-SHAKE_INTENSITY, SHAKE_INTENSITY))
    screen.fill(BLACK)
    screen.blit(canvas, offset)
    pygame.display.flip()

pygame.quit()
