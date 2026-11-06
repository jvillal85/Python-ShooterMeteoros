import json
import os
import tempfile
import unittest

from meteoro import config as C
from meteoro import storage


class ScoresTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.scores_path = os.path.join(self.tmp.name, "highscores.json")
        self.legacy_path = os.path.join(self.tmp.name, "highscore.txt")

    def tearDown(self):
        self.tmp.cleanup()

    def load(self):
        return storage.load_scores(self.scores_path, self.legacy_path)

    def test_empty_when_no_files(self):
        self.assertEqual(self.load(), [])

    def test_imports_legacy_highscore(self):
        with open(self.legacy_path, "w", encoding="utf-8") as f:
            f.write("730")
        self.assertEqual(self.load(), [{"name": "---", "score": 730, "level": 1}])

    def test_save_and_load_roundtrip_sorted(self):
        scores = [{"name": "AAA", "score": 10, "level": 1}, {"name": "BBB", "score": 50, "level": 2}]
        storage.save_scores(scores, self.scores_path)
        loaded = self.load()
        self.assertEqual([e["name"] for e in loaded], ["BBB", "AAA"])

    def test_corrupt_file_is_ignored(self):
        with open(self.scores_path, "w", encoding="utf-8") as f:
            f.write("{esto no es json")
        self.assertEqual(self.load(), [])

    def test_bad_entries_are_dropped(self):
        with open(self.scores_path, "w", encoding="utf-8") as f:
            json.dump([{"name": "ok", "score": 5}, {"score": "x"}, 42], f)
        self.assertEqual(self.load(), [{"name": "OK", "score": 5, "level": 1}])

    def test_qualifies(self):
        self.assertFalse(storage.qualifies([], 0))
        self.assertTrue(storage.qualifies([], 10))
        full = [{"name": "AAA", "score": 100 + i, "level": 1} for i in range(C.HIGHSCORE_SLOTS)]
        self.assertFalse(storage.qualifies(full, 100))
        self.assertTrue(storage.qualifies(full, 101))

    def test_insert_returns_position_and_keeps_top_only(self):
        full = [{"name": "AAA", "score": 100 * (i + 1), "level": 1} for i in range(C.HIGHSCORE_SLOTS)]
        new, pos = storage.insert_score(full, "zed", 550, 3)
        self.assertEqual(len(new), C.HIGHSCORE_SLOTS)
        self.assertEqual(new[pos], {"name": "ZED", "score": 550, "level": 3})
        _, pos = storage.insert_score(full, "LOW", 1, 1)
        self.assertIsNone(pos)


class SettingsTests(unittest.TestCase):
    def test_defaults_and_sanitising(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "settings.json")
            self.assertEqual(storage.load_settings(path), storage.DEFAULT_SETTINGS)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"music_volume": 5, "sfx_volume": "x", "muted": 1, "player_name": "ab"}, f)
            settings = storage.load_settings(path)
            self.assertEqual(settings["music_volume"], 1.0)
            self.assertEqual(settings["sfx_volume"], storage.DEFAULT_SETTINGS["sfx_volume"])
            self.assertTrue(settings["muted"])
            self.assertEqual(settings["player_name"], "AAA")


if __name__ == "__main__":
    unittest.main()
