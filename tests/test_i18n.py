import string
import unittest

from meteoro import i18n


class TextsTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_language("es")

    def test_all_languages_have_the_same_keys(self):
        base = set(i18n.TEXTS["es"])
        for lang, texts in i18n.TEXTS.items():
            self.assertEqual(set(texts), base, lang)

    def test_placeholders_match(self):
        fields = lambda s: {f for _, f, _, _ in string.Formatter().parse(s) if f}  # noqa: E731
        for key, text in i18n.TEXTS["es"].items():
            for lang, texts in i18n.TEXTS.items():
                self.assertEqual(fields(texts[key]), fields(text), "{} ({})".format(key, lang))

    def test_translate_and_format(self):
        i18n.set_language("en")
        self.assertEqual(i18n.t("hud.level", n=3), "Level 3")
        i18n.set_language("es")
        self.assertEqual(i18n.t("hud.level", n=3), "Nivel 3")

    def test_unknown_language_falls_back_to_spanish(self):
        i18n.set_language("xx")
        self.assertEqual(i18n.get_language(), "es")


if __name__ == "__main__":
    unittest.main()
