"""The public site must open the stats page on the same host."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from database import upsert_team_stats
from export_web import write_payload
from scraper import annotate

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
        self.assertGreater(data["previous_rows"], 0)
        olympiacos = next(team for team in data["teams"] if team["name"] == "Olympiacos")
        self.assertEqual(len(olympiacos["logs"]["euroleague"]), 43)
        if olympiacos["current"] is not None:
            self.assertEqual(olympiacos["current"]["season"], "2026-27")
        self.assertIn("ολυμπιακοσ", olympiacos["search"])

    def test_saved_stats_are_published_to_the_site_file(self) -> None:
        league = {
            "league_code": "euroleague",
            "league_name": "Euroleague",
            "scope": "europe",
            "country": "Ευρώπη",
            "season": "2026-27",
            "url": "https://example.test/euroleague",
        }
        frame = annotate(
            pd.DataFrame(
                [
                    {
                        "team_name": "Olympiacos",
                        "gp": 2,
                        "mpg": 40,
                        "ppg": 81,
                        "fgm": 28,
                        "fga": 60,
                        "fg_pct": 28 / 60,
                        "tpm": 9,
                        "tpa": 25,
                        "tp_pct": 9 / 25,
                        "ftm": 16,
                        "fta": 20,
                        "ft_pct": 0.8,
                        "orb": 10,
                        "drb": 24,
                        "rpg": 34,
                        "apg": 18,
                        "spg": 7,
                        "bpg": 3,
                        "tov": 11,
                        "pf": 19,
                    }
                ]
            ),
            league,
            "RealGM",
        )
        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "basketball.db"
            site_file = Path(folder) / "stats-data.json"
            self.assertEqual(upsert_team_stats(frame, db_path), 1)
            write_payload(site_file, db_path)
            published = json.loads(site_file.read_text(encoding="utf-8"))
            olympiacos = next(team for team in published["teams"] if team["name"] == "Olympiacos")
            self.assertEqual(published["current_rows"], 1)
            self.assertAlmostEqual(olympiacos["current"]["scopes"]["combined"]["ppg"], 81)


if __name__ == "__main__":
    unittest.main()
