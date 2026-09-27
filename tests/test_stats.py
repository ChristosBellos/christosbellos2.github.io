"""Tests for parsing, name matching, and weighted averages."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from advanced import apply_advanced, effective_fg, possessions, true_shooting
from database import (
    comparison_profile,
    get_team_stats,
    list_team_names,
    replace_game_logs,
    search_team_names,
    upsert_team_stats,
)
from names import canonical_team_name, fold, option_label
from scraper import (
    OUTPUT_COLUMNS,
    _averages_from_logs,
    annotate,
    parse_html_table,
    parse_percent,
    parse_stats_document,
    season_unavailable,
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

    def test_game_logs_become_a_weighted_average(self) -> None:
        logs = pd.DataFrame(
            [
                {"team_name": "Olympiacos", "points": 80, "fgm": 30, "fga": 60, "tpm": 8, "tpa": 20, "ftm": 12, "fta": 15, "orb": 8, "drb": 20, "reb": 28, "ast": 18, "stl": 6, "blk": 2, "tov": 10, "pf": 18, "minutes": 40},
                {"team_name": "Olympiacos", "points": 100, "fgm": 36, "fga": 70, "tpm": 12, "tpa": 30, "ftm": 16, "fta": 20, "orb": 12, "drb": 24, "reb": 36, "ast": 22, "stl": 8, "blk": 4, "tov": 14, "pf": 20, "minutes": 40},
            ]
        )
        frame = _averages_from_logs(logs, LEAGUE)
        self.assertEqual(len(frame), 1)
        row = frame.iloc[0]
        self.assertEqual(row["gp"], 2)
        self.assertEqual(row["ppg"], 90)
        self.assertAlmostEqual(row["fg_pct"], 66 / 130)

    def test_advanced_formulas_and_opponent_points(self) -> None:
        self.assertAlmostEqual(possessions(60, 8, 10, 15), 0.96 * (60 - 8 + 10 + 0.44 * 15))
        rated = apply_advanced(
            {"ppg": 80, "fgm": 30, "fga": 60, "tpm": 8, "fta": 15, "orb": 8, "tov": 10, "opp_ppg": 70}
        )
        poss = 0.96 * (60 - 8 + 10 + 0.44 * 15)
        self.assertAlmostEqual(rated["off_rtg"], 80 * 100 / poss)
        self.assertAlmostEqual(rated["def_rtg"], 70 * 100 / poss)
        self.assertAlmostEqual(rated["net_rtg"], rated["off_rtg"] - rated["def_rtg"])
        self.assertAlmostEqual(rated["efg_pct"], effective_fg(30, 8, 60))
        self.assertAlmostEqual(rated["ts_pct"], true_shooting(80, 60, 15))
        missing = apply_advanced({"ppg": 80, "fgm": 30, "fga": 60, "tpm": 8, "fta": 15, "orb": 8, "tov": 10})
        self.assertIsNone(missing["def_rtg"])
        self.assertIsNone(missing["net_rtg"])
        self.assertIsNotNone(missing["off_rtg"])

    def test_unstarted_season_is_recognized(self) -> None:
        page = "## 2026-2027 Euroleague Averages - Team Totals\n\nStats are not available for this season."
        self.assertTrue(season_unavailable(page))
        self.assertTrue(parse_stats_document(page).empty)

    def test_greek_alias(self) -> None:
        self.assertEqual(canonical_team_name("Ολυμπιακός"), "Olympiacos")
        self.assertEqual(canonical_team_name("FC Barcelona"), "Barca")
        self.assertEqual(canonical_team_name("Kosner Baskonia Vitoria-Gasteiz"), "Baskonia")
        self.assertEqual(canonical_team_name("Hapoel IBI Tel Aviv"), "Hapoel Tel Aviv")
        self.assertEqual(canonical_team_name("Aris Thessaloniki Betsson"), "Aris Midea Thessaloniki")
        self.assertEqual(canonical_team_name("Cosea JL Bourg-en-Bresse"), "JL Bourg-en-Bresse")
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

            profile = get_team_stats("ΟΣΦΠ", db_path=db_path)
            self.assertIsNotNone(profile)
            assert profile is not None
            self.assertEqual(profile["team"], "Olympiacos")
            self.assertEqual(len(profile["competitions"]), 2)
            combined_stats = profile["scopes"]["combined"]
            self.assertAlmostEqual(float(combined_stats["ppg"]), (90 * 40 + 80 * 20) / 60)
            self.assertAlmostEqual(float(combined_stats["fg_pct"]), (30 * 40 + 20 * 20) / (60 * 40 + 50 * 20))
            europe_only = profile["scopes"]["europe"]
            fga = 60 * 40 + 50 * 20
            self.assertAlmostEqual(float(combined_stats["efg_pct"]), ((30 + 0.5 * 10) * 40 + (20 + 0.5 * 8) * 20) / fga)
            self.assertIsNotNone(europe_only["possessions"])
            self.assertIsNone(europe_only["def_rtg"])
            self.assertEqual(profile["scopes"]["europe"]["gp"], 40)
            self.assertEqual(profile["scopes"]["domestic"]["gp"], 20)
            self.assertIsNone(get_team_stats("Άγνωστη", db_path=db_path))
            self.assertIsNone(get_team_stats("Olympiacos", "2026-27", db_path))

            fresh = europe.copy()
            fresh["season"] = "2026-27"
            fresh["ppg"] = 10
            upsert_team_stats(fresh, db_path)
            kept = get_team_stats("Olympiacos", "2025-26", db_path)
            assert kept is not None
            self.assertAlmostEqual(float(kept["scopes"]["europe"]["ppg"]), 90.0)
            current = get_team_stats("Olympiacos", "2026-27", db_path)
            assert current is not None
            self.assertAlmostEqual(float(current["scopes"]["combined"]["ppg"]), 10.0)

            logs = pd.DataFrame(
                [
                    {
                        "team_name": "Olympiacos",
                        "league_code": "euroleague",
                        "season": "2025-26",
                        "game_index": 1,
                        "round_number": 1,
                        "points": 80,
                        "fgm": 30,
                        "fga": 60,
                        "tpm": 10,
                        "tpa": 20,
                        "ftm": 10,
                        "fta": 10,
                        "orb": 10,
                        "drb": 20,
                        "reb": 30,
                        "ast": 15,
                        "stl": 5,
                        "blk": 2,
                        "tov": 12,
                        "pf": 18,
                        "minutes": 40,
                    },
                    {
                        "team_name": "Olympiacos",
                        "league_code": "euroleague",
                        "season": "2025-26",
                        "game_index": 2,
                        "round_number": 2,
                        "points": 100,
                        "fgm": 40,
                        "fga": 70,
                        "tpm": 10,
                        "tpa": 30,
                        "ftm": 10,
                        "fta": 20,
                        "orb": 12,
                        "drb": 22,
                        "reb": 34,
                        "ast": 25,
                        "stl": 7,
                        "blk": 4,
                        "tov": 14,
                        "pf": 20,
                        "minutes": 40,
                    },
                    {
                        "team_name": "Olympiacos",
                        "league_code": "euroleague",
                        "season": "2025-26",
                        "game_index": 3,
                        "round_number": 3,
                        "points": 60,
                        "fgm": 20,
                        "fga": 50,
                        "tpm": 5,
                        "tpa": 15,
                        "ftm": 15,
                        "fta": 20,
                        "orb": 8,
                        "drb": 18,
                        "reb": 26,
                        "ast": 10,
                        "stl": 4,
                        "blk": 1,
                        "tov": 10,
                        "pf": 16,
                        "minutes": 40,
                    },
                ]
            )
            short_season = europe[europe["team_name"] == "Olympiacos"].copy()
            short_season["gp"] = 3
            upsert_team_stats(short_season, db_path)
            self.assertEqual(replace_game_logs(logs, "euroleague", "2025-26", db_path), 3)
            paced = comparison_profile("Olympiacos", {"euroleague": 2}, "2025-26", db_path)
            assert paced is not None
            self.assertAlmostEqual(float(paced["scopes"]["europe"]["ppg"]), 90.0)
            self.assertEqual(paced["scopes"]["europe"]["gp"], 2)
            self.assertIsNotNone(paced["scopes"]["europe"]["efg_pct"])
            self.assertIsNone(paced["scopes"]["europe"]["def_rtg"])
            allowed = logs.copy()
            allowed["points_allowed"] = [70, 88, 60]
            replace_game_logs(allowed, "euroleague", "2025-26", db_path)
            defended = comparison_profile("Olympiacos", {"euroleague": 2}, "2025-26", db_path)
            assert defended is not None
            slice_poss = possessions((60 + 70) / 2, (10 + 12) / 2, (12 + 14) / 2, (10 + 20) / 2)
            self.assertAlmostEqual(float(defended["scopes"]["europe"]["def_rtg"]), ((70 + 88) / 2) * 100 / slice_poss)
            self.assertIsNone(comparison_profile("Olympiacos", {"euroleague": 0}, "2025-26", db_path))
            self.assertIsNone(comparison_profile("Olympiacos", {"greek_a1": 2}, "2025-26", db_path))
            incomplete = short_season.copy()
            incomplete["gp"] = 10
            upsert_team_stats(incomplete, db_path)
            self.assertIsNone(comparison_profile("Olympiacos", {"euroleague": 2}, "2025-26", db_path))

            columns = set(combined.columns)
            self.assertTrue(set(OUTPUT_COLUMNS).issubset(columns))


if __name__ == "__main__":
    unittest.main()
