"""The public site must open the stats page on the same host."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SiteLinkTests(unittest.TestCase):
    def test_pages_do_not_point_at_localhost(self) -> None:
        for path in ROOT.glob("*.html"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("127.0.0.1", text, path.name)
            if path.name != "stats.html":
                self.assertIn("stats.html", text, path.name)

    def test_published_snapshot_has_last_season_only(self) -> None:
        data = json.loads((ROOT / "stats-data.json").read_text(encoding="utf-8"))
        self.assertEqual(data["current_rows"], 0)
        self.assertGreater(data["previous_rows"], 0)
        olympiacos = next(team for team in data["teams"] if team["name"] == "Olympiacos")
        self.assertIsNone(olympiacos["current"])
        self.assertEqual(len(olympiacos["logs"]["euroleague"]), 43)
        self.assertIn("ολυμπιακοσ", olympiacos["search"])


if __name__ == "__main__":
    unittest.main()
