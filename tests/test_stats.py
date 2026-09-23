"""Tests for parsing, name matching, and weighted averages."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from database import get_team_stats, list_team_names, search_team_names, upsert_team_stats
from names import canonical_team_name, fold, option_label
from scraper import (
    OUTPUT_COLUMNS,
    annotate,
    parse_html_table,
    parse_percent,
    parse_stats_document,
)

MARKDOWN = """
## 2025-2026 Euroleague Averages - Team Totals

| # | Team | GP | MPG | PPG | FGM | FGA | FG% | 3PM | 3PA | 3P% | FTM | FTA | FT% | ORB | DRB | RPG | APG | SPG | BPG | TOV | PF |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. | [Olympiacos](https://basketball.realgm.com/team/120/Olympiacos) | 40 | 40.1 | 90.0 | 30.0 | 60.0 | .500 | 10.0 | 28.0 | .357 | 20.0 | 25.0 | .800 | 11.0 | 24.0 | 35.0 | 20.0 | 6.0 | 2.0 | 12.0 | 18.0 |
| 2. | [Real Madrid](https://basketball.realgm.com/team/52/Real-Madrid) | 38 | 39.7 | 88.1 | 30.8 | 63.7 | .484 | 10.0 | 26.6 | .377 | 16.4 | 20.8 | .789 | 12.0 | 25.6 | 37.6 | 19.2 | 6.3 | 3.9 | 12.3 | 19.9 |
"""

HTML = """
<html><body>
<table>
  <tr><th>#</th><th>Team</th><th>GP</th><th>MPG</th><th>PPG</th><th>FGM</th><th>FGA</th><th>FG%</th>
      <th>3PM</th><th>3PA</th><th>3P%</th><th>FTM</th><th>FTA</th><th>FT%</th>
      <th>ORB</th><th>DRB</th><th>RPG</th><th>APG</th><th>SPG</th><th>BPG</th><th>TOV</th><th>PF</th></tr>
  <tr><td>1</td><td>Panathinaikos AKTOR Athens</td><td>20</td><td>40.0</td><td>80.0</td>
      <td>20.0</td><td>50.0</td><td>40.0%</td><td>8</td><td>24</td><td>33.3%</td>
      <td>16</td><td>20</td><td>80%</td><td>10</td><td>22</td><td>32</td>
      <td>18</td><td>6</td><td>2</td><td>11</td><td>19</td></tr>
</table>
</body></html>
"""

LEAGUE = {
    "league_code": "euroleague",
    "league_name": "Euroleague",
    "scope": "europe",
    "country": "Ευρώπη",
    "season": "2025-26",
    "url": "https://example.test/euroleague",
}
DOMESTIC = {
    "league_code": "greek_a1",
    "league_name": "Greek HEBA A1",
    "scope": "domestic",
    "country": "Ελλάδα",
    "season": "2025-26",
    "url": "https://example.test/greece",
}


class ParseTests(unittest.TestCase):
    def test_markdown_table(self) -> None:
        frame = parse_stats_document(MARKDOWN)
        self.assertEqual(list(frame["team_name"]), ["Olympiacos", "Real Madrid"])
        olympiacos = frame.iloc[0]
        self.assertEqual(olympiacos["gp"], 40)
        self.assertEqual(olympiacos["ppg"], 90.0)
        self.assertAlmostEqual(olympiacos["fg_pct"], 0.5)
        self.assertAlmostEqual(olympiacos["tp_pct"], 0.357)

    def test_html_table_and_canonical_name(self) -> None:
        frame = parse_html_table(HTML)
        self.assertEqual(frame.iloc[0]["team_name"], "Panathinaikos")
        self.assertAlmostEqual(frame.iloc[0]["fg_pct"], 0.4)
        self.assertAlmostEqual(frame.iloc[0]["ft_pct"], 0.8)

    def test_percent_formats(self) -> None:
        self.assertAlmostEqual(parse_percent(".492"), 0.492)
        self.assertAlmostEqual(parse_percent("51.7%"), 0.517)
        self.assertAlmostEqual(parse_percent("33%"), 0.33)

    def test_challenge_page_is_ignored(self) -> None:
        page = "<title>Just a moment...</title><p>Performing security verification</p>"
        self.assertTrue(parse_stats_document(page).empty)

    def test_greek_alias(self) -> None:
        self.assertEqual(canonical_team_name("Ολυμπιακός"), "Olympiacos")
        self.assertEqual(canonical_team_name("FC Barcelona"), "Barca")
        self.assertEqual(fold("Άρης"), fold("αρης"))
        self.assertIn("Ολυμπιακός", option_label("Olympiacos"))
        self.assertIn("Partizan", option_label("KK Partizan"))


class DatabaseTests(unittest.TestCase):
    def test_upsert_search_and_weighted_average(self) -> None:
        europe = annotate(parse_stats_document(MARKDOWN), LEAGUE, "RealGM")
        domestic_row = pd.DataFrame(
            [
                {
                    "team_name": "Olympiacos",
                    "gp": 20,
                    "mpg": 40,
                    "ppg": 80,
                    "fgm": 20,
                    "fga": 50,
                    "fg_pct": 0.4,
                    "tpm": 8,
                    "tpa": 24,
                    "tp_pct": 1 / 3,
                    "ftm": 16,
                    "fta": 20,
                    "ft_pct": 0.8,
                    "orb": 10,
                    "drb": 22,
                    "rpg": 32,
                    "apg": 16,
                    "spg": 5,
                    "bpg": 2,
                    "tov": 13,
                    "pf": 20,
                }
            ]
        )
        domestic = annotate(domestic_row, DOMESTIC, "RealGM")
        combined = pd.concat([europe, domestic], ignore_index=True)

        with tempfile.TemporaryDirectory() as folder:
            db_path = Path(folder) / "basketball.db"
            saved = upsert_team_stats(combined, db_path)
            self.assertEqual(saved, 3)
            self.assertEqual(list_team_names(db_path), ["Olympiacos", "Real Madrid"])
            self.assertEqual(search_team_names("ολυμπιακός", db_path), ["Olympiacos"])

            profile = get_team_stats("ΟΣΦΠ", db_path)
            self.assertIsNotNone(profile)
            assert profile is not None
            self.assertEqual(profile["team"], "Olympiacos")
            self.assertEqual(len(profile["competitions"]), 2)
            combined_stats = profile["scopes"]["combined"]
            self.assertAlmostEqual(float(combined_stats["ppg"]), (90 * 40 + 80 * 20) / 60)
            self.assertAlmostEqual(float(combined_stats["fg_pct"]), (30 * 40 + 20 * 20) / (60 * 40 + 50 * 20))
            self.assertEqual(profile["scopes"]["europe"]["gp"], 40)
            self.assertEqual(profile["scopes"]["domestic"]["gp"], 20)
            self.assertIsNone(get_team_stats("Άγνωστη", db_path))

            columns = set(combined.columns)
            self.assertTrue(set(OUTPUT_COLUMNS).issubset(columns))


if __name__ == "__main__":
    unittest.main()
