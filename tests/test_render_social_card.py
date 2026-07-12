from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from xml.etree import ElementTree


MODULE_PATH = Path(__file__).parents[1] / "tools" / "render_social_card.py"
SPEC = importlib.util.spec_from_file_location("render_social_card", MODULE_PATH)
cards = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cards)


class SocialCardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "card.svg"

    def test_renders_bounded_card_without_placeholders(self) -> None:
        cards.render_card(cards.TEMPLATE, self.output, chapter=7, title_lines=["Agents are a portfolio,", "not pets"], slug="agent-portfolio")
        root = ElementTree.parse(self.output).getroot()
        text = " ".join((element.text or "") for element in root.iter())
        self.assertIn("CHAPTER 07", text)
        self.assertIn("selamy.dev/agent-fleets/07-agent-portfolio/", text)
        self.assertIn("not architecture", text)
        self.assertNotIn("[", text)

    def test_rejects_chapter_lines_slug_overwrite_and_missing_nodes(self) -> None:
        cases = (
            ({"chapter": 0, "title_lines": ["Title"], "slug": "title"}, "chapter"),
            ({"chapter": 1, "title_lines": [], "slug": "title"}, "one to three"),
            ({"chapter": 1, "title_lines": ["x" * 29], "slug": "title"}, "at most 28"),
            ({"chapter": 1, "title_lines": ["W" * 13], "slug": "title"}, "rendered-width"),
            ({"chapter": 1, "title_lines": ["Title"], "slug": "Bad Slug"}, "kebab"),
            ({"chapter": 1, "title_lines": ["Title"], "slug": "wide-" + "m" * 28}, "chapter URL"),
        )
        for values, message in cases:
            with self.subTest(values=values), self.assertRaisesRegex(cards.SocialCardError, message):
                cards.render_card(cards.TEMPLATE, self.output, **values)
        with self.assertRaisesRegex(cards.SocialCardError, "overwrite"):
            cards.render_card(cards.TEMPLATE, cards.TEMPLATE, chapter=1, title_lines=["Title"], slug="title")
        broken = Path(self.directory.name) / "broken.svg"
        broken.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>', encoding="utf-8")
        with self.assertRaisesRegex(cards.SocialCardError, "required bounded"):
            cards.render_card(broken, self.output, chapter=1, title_lines=["Title"], slug="title")

    def test_width_budget_accepts_narrow_and_mixed_case_lines(self) -> None:
        cards.render_card(
            cards.TEMPLATE,
            self.output,
            chapter=3,
            title_lines=["Skills instead of a", "monolithic framework", "iiiiiiiiiiiiiiiiiiiiiiiiiiii"],
            slug="skills-and-context-routing",
        )
        text = " ".join((element.text or "") for element in ElementTree.parse(self.output).getroot().iter())
        self.assertIn("selamy.dev/agent-fleets/03-skills-and-context-routing/", text)
        self.assertTrue(self.output.is_file())
        self.assertLess(cards.text_units("mixed Case"), cards.text_units("WWWWWWWWWW"))

    def test_cli_success_and_failure(self) -> None:
        stdout = io.StringIO()
        with mock.patch("sys.argv", ["render", "--output", str(self.output), "--chapter", "1", "--title-line", "A title", "--slug", "a-title"]), mock.patch("sys.stdout", stdout):
            self.assertEqual(cards.main(), 0)
        self.assertIn("rendered social card", stdout.getvalue())
        stderr = io.StringIO()
        with mock.patch("sys.argv", ["render", "--output", str(self.output), "--chapter", "9", "--title-line", "A title", "--slug", "a-title"]), mock.patch("sys.stderr", stderr):
            self.assertEqual(cards.main(), 1)
        self.assertIn("render failed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
