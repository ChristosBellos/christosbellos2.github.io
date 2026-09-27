"""Publish the stored team averages as a static file the site can open."""

from __future__ import annotations

import json
from pathlib import Path

from database import (
    connect,
    dataset_summary,
    get_team_stats,
    init_db,
    list_cross_competition_teams,
    list_team_names,
)
from names import ALIASES, fold, option_label
from scraper import CURRENT_SEASON, LEAGUE_META, PREVIOUS_SEASON

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "stats-data.json"

KEEP_FIELDS = (
    "league_code",
    "league_name",
    "scope",
    "country",
    "season",
    "source_name",
    "gp",
    "mpg",
    "ppg",
    "fgm",
    "fga",
    "fg_pct",
    "tpm",
    "tpa",
    "tp_pct",
    "ftm",
    "fta",
    "ft_pct",
    "orb",
    "drb",
    "rpg",
    "apg",
    "spg",
    "bpg",
    "tov",
    "pf",
)
LOG_FIELDS = (
    "game_index",
    "points",
    "fgm",
    "fga",
    "tpm",
    "tpa",
    "ftm",
    "fta",
    "orb",
    "drb",
    "reb",
    "ast",
    "stl",
    "blk",
    "tov",
    "pf",
    "minutes",
)


def _slim(profile: dict | None) -> dict | None:
    if profile is None:
        return None
    competitions = [{field: row.get(field) for field in KEEP_FIELDS} for row in profile["competitions"]]
    return {
        "team": profile["team"],
        "season": profile["season"],
        "updated_at": profile["updated_at"],
        "competitions": competitions,
        "scopes": profile["scopes"],
    }


def _search_text(name: str) -> str:
    pieces = [name, option_label(name)]
    for key, canonical in ALIASES.items():
        if canonical == name:
            pieces.append(key)
    return " ".join(fold(piece) for piece in pieces)


def _logs_and_gp(db_path: Path | None = None) -> tuple[dict[str, dict], dict[str, dict[str, float]]]:
    logs: dict[str, dict[str, list]] = {}
    previous_gp: dict[str, dict[str, float]] = {}
    with connect(db_path) as connection:
        for row in connection.execute(
            """
            SELECT t.name, g.league_code, g.game_index, g.points, g.fgm, g.fga, g.tpm, g.tpa,
                   g.ftm, g.fta, g.orb, g.drb, g.reb, g.ast, g.stl, g.blk, g.tov, g.pf, g.minutes
            FROM game_logs g
            JOIN teams t ON t.id = g.team_id
            WHERE g.season = ?
            ORDER BY t.name, g.league_code, g.game_index
            """,
            (PREVIOUS_SEASON,),
        ):
            logs.setdefault(row["name"], {}).setdefault(row["league_code"], []).append(
                [row[field] for field in LOG_FIELDS]
            )
        for row in connection.execute(
            """
            SELECT t.name, c.league_code, c.gp
            FROM competition_stats c
            JOIN teams t ON t.id = c.team_id
            WHERE c.season = ?
            """,
            (PREVIOUS_SEASON,),
        ):
            previous_gp.setdefault(row["name"], {})[row["league_code"]] = row["gp"]
    return logs, previous_gp


def build_payload(db_path: Path | None = None) -> dict:
    init_db(db_path)
    summary = dataset_summary(db_path)
    logs, previous_gp = _logs_and_gp(db_path)
    teams = []
    for name in list_team_names(db_path):
        teams.append(
            {
                "name": name,
                "label": option_label(name),
                "search": _search_text(name),
                "current": _slim(get_team_stats(name, CURRENT_SEASON, db_path)),
                "logs": logs.get(name, {}),
                "previous_gp": previous_gp.get(name, {}),
            }
        )
    return {
        "current_season": CURRENT_SEASON,
        "previous_season": PREVIOUS_SEASON,
        "current_rows": summary["current_rows"],
        "previous_rows": summary["previous_rows"],
        "refreshed_at": summary["refreshed_at"],
        "cross": list_cross_competition_teams(PREVIOUS_SEASON, db_path),
        "leagues": LEAGUE_META,
        "log_fields": list(LOG_FIELDS),
        "teams": teams,
    }


def write_payload(path: Path = OUTPUT, db_path: Path | None = None) -> Path:
    payload = build_payload(db_path)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return path


if __name__ == "__main__":
    target = write_payload()
    print(f"Wrote {target}")
