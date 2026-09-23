"""UI checks for the empty 2026-27 season and the separate 2025-26 round."""

from __future__ import annotations

import unittest

from streamlit.testing.v1 import AppTest

from names import option_label

UNAVAILABLE = "Μη διαθέσιμων στατιστικών"


class AppSeasonTests(unittest.TestCase):
    def test_empty_current_season_stays_separate_from_last_year(self) -> None:
        app = AppTest.from_file("/workspace/app.py", default_timeout=40)
        app.run()
        self.assertFalse(app.exception)
        info = " ".join(block.value for block in app.info)
        self.assertIn(UNAVAILABLE, info)

        app.selectbox[0].set_value(option_label("Olympiacos")).run()
        self.assertFalse(app.exception)
        text = " ".join(
            part
            for part in (
                " ".join(block.value for block in app.info),
                " ".join(block.value for block in app.subheader),
                " ".join(block.value for block in app.markdown),
            )
        )
        self.assertIn("Σεζόν 2026-27", text)
        self.assertIn(UNAVAILABLE, text)
        self.assertNotIn("92.7", text)

        app.toggle[0].set_value(True).run()
        self.assertFalse(app.exception)
        toggled = " ".join(block.value for block in app.info)
        self.assertIn(UNAVAILABLE, toggled)
        self.assertEqual(
            [block.value for block in app.subheader if "2025-26" in block.value],
            [],
        )


if __name__ == "__main__":
    unittest.main()
