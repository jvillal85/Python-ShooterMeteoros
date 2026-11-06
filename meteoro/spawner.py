"""Aparición de meteoros, naves enemigas y jefes durante la partida."""
import random

from . import config as C
from . import rules
from .sprites import ENEMY_CLASSES, Boss, Meteor

NEW_METEOR_SIZES = ("big", "med", "small", "tiny")
NEW_METEOR_WEIGHTS = (50, 30, 14, 6)


class Spawner:
    def __init__(self, play):
        self.play = play
        self.next_enemy_at = 8.0
        self.bosses_spawned = 0  # jefes que ya aparecieron (uno cada BOSS_EVERY niveles)

    def fill_meteors(self):
        play = self.play
        target = rules.meteor_target(play.level, play.boss is not None, play.difficulty)
        while len(play.meteors) < target:
            size = random.choices(NEW_METEOR_SIZES, NEW_METEOR_WEIGHTS)[0]
            play.meteors.add(Meteor(play, size))

    def update(self):
        play = self.play
        now = play.world_now
        self.fill_meteors()

        # Toca un jefe nuevo al llegar a un nivel múltiplo de 5 (aunque se haya saltado ese
        # nivel justo). Si todavía queda uno vivo, el siguiente espera a que muera.
        due = play.level // C.BOSS_EVERY
        if due > self.bosses_spawned and play.boss is None:
            self.bosses_spawned = due
            play.bosses.add(Boss(play, now, play.level))
            play.show_banner("banner.boss", C.PURPLE, 2.5)

        if (now >= self.next_enemy_at and play.boss is None
                and len(play.enemies) < rules.max_enemies(play.level)):
            kinds = rules.enemy_types_for_level(play.level)
            kind = random.choices(kinds, [C.ENEMY_TYPES[k]["weight"] for k in kinds])[0]
            self.spawn_enemy(kind)
            self.next_enemy_at = now + random.uniform(C.ENEMY_SPAWN_MIN, C.ENEMY_SPAWN_MAX)

    def spawn_enemy(self, kind, pos=None):
        cls = ENEMY_CLASSES[kind]
        enemy = cls(self.play, self.play.world_now, pos) if pos else cls(self.play, self.play.world_now)
        self.play.enemies.add(enemy)
        return enemy
