import unittest

from meteoro import config as C
from meteoro import rules


class LevelTests(unittest.TestCase):
    def test_level_starts_at_one(self):
        self.assertEqual(rules.level_for_score(0), 1)
        self.assertEqual(rules.level_for_score(C.POINTS_PER_LEVEL - 1), 1)

    def test_level_thresholds_grow(self):
        self.assertEqual(rules.level_for_score(C.POINTS_PER_LEVEL), 2)
        self.assertEqual(rules.level_for_score(C.POINTS_PER_LEVEL * 3 - 1), 2)
        self.assertEqual(rules.level_for_score(C.POINTS_PER_LEVEL * 3), 3)
        for level in range(1, 30):
            self.assertEqual(rules.level_for_score(rules.score_for_level(level)), level)
            self.assertEqual(rules.level_for_score(rules.score_for_level(level + 1) - 1), level)
            self.assertGreater(rules.score_for_level(level + 2) - rules.score_for_level(level + 1),
                               rules.score_for_level(level + 1) - rules.score_for_level(level))

    def test_meteor_count_grows_and_is_capped(self):
        self.assertEqual(rules.meteors_for_level(1), C.BASE_METEORS)
        self.assertEqual(rules.meteors_for_level(2), C.BASE_METEORS + C.METEORS_PER_LEVEL)
        self.assertEqual(rules.meteors_for_level(100), C.MAX_METEORS)

    def test_fewer_meteors_during_boss(self):
        self.assertLess(rules.meteor_target(5, True), rules.meteor_target(5, False))
        self.assertGreaterEqual(rules.meteor_target(1, True), 3)

    def test_meteor_speed_increases_with_level_and_is_capped(self):
        slow1, fast1 = rules.meteor_speed_range(1)
        slow3, fast3 = rules.meteor_speed_range(3)
        self.assertLess(slow1, fast1)
        self.assertGreater(fast3, fast1)
        self.assertEqual(rules.meteor_speed_range(50), rules.meteor_speed_range(100))


class MeteorTests(unittest.TestCase):
    def test_smaller_meteors_give_more_points(self):
        points = [rules.meteor_points(s) for s in C.METEOR_SIZES]
        self.assertEqual(points, sorted(points))

    def test_bigger_meteors_do_more_damage(self):
        damage = [rules.meteor_damage(s) for s in C.METEOR_SIZES]
        self.assertEqual(damage, sorted(damage, reverse=True))

    def test_split_chain(self):
        self.assertEqual(rules.split_size("big"), "med")
        self.assertEqual(rules.split_size("med"), "small")
        self.assertIsNone(rules.split_size("small"))
        self.assertIsNone(rules.split_size("tiny"))


class ComboAndLivesTests(unittest.TestCase):
    def test_multiplier(self):
        self.assertEqual(rules.multiplier_for_combo(0), 1)
        self.assertEqual(rules.multiplier_for_combo(C.COMBO_STEP - 1), 1)
        self.assertEqual(rules.multiplier_for_combo(C.COMBO_STEP), 2)
        self.assertEqual(rules.multiplier_for_combo(1000), C.MAX_MULTIPLIER)

    def test_lives_earned(self):
        step = C.EXTRA_LIFE_EVERY
        self.assertEqual(rules.lives_earned(0, step - 1), 0)
        self.assertEqual(rules.lives_earned(step - 10, step + 10), 1)
        self.assertEqual(rules.lives_earned(0, step * 2), 2)
        self.assertEqual(rules.lives_earned(step, step + 5), 0)


class EnemyTests(unittest.TestCase):
    def test_boss_levels(self):
        self.assertFalse(rules.is_boss_level(4))
        self.assertTrue(rules.is_boss_level(C.BOSS_EVERY))
        self.assertTrue(rules.is_boss_level(C.BOSS_EVERY * 2))

    def test_boss_gets_tougher(self):
        self.assertEqual(rules.boss_hp(C.BOSS_EVERY), C.BOSS_BASE_HP)
        self.assertGreater(rules.boss_hp(C.BOSS_EVERY * 2), rules.boss_hp(C.BOSS_EVERY))

    def test_enemies_only_from_first_level(self):
        self.assertEqual(rules.max_enemies(C.ENEMY_FIRST_LEVEL - 1), 0)
        self.assertEqual(rules.max_enemies(C.ENEMY_FIRST_LEVEL), 1)
        self.assertEqual(rules.max_enemies(100), 3)


if __name__ == "__main__":
    unittest.main()
