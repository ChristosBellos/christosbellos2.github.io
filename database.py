"""SQLite storage for team averages across European competitions."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from names import matching_names, resolve_team_name
from scraper import STAT_FIELDS

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "basketball.db"

SCOPE_ORDER = {"europe": 0, "regional": 1, "domestic": 2}
COUNTING_FIELDS = [field for field in STAT_FIELDS if not field.endswith("_pct") and field != "gp"]


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: Path | str | None = None) -> None:
    """Create tables if they do not exist."""
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS teams (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS competition_stats (
                id INTEGER PRIMARY KEY,
                team_id INTEGER NOT NULL REFERENCES teams(id),
                league_code TEXT NOT NULL,
                league_name TEXT NOT NULL,
                scope TEXT NOT NULL,
                country TEXT NOT NULL,
                season TEXT NOT NULL,
                source_name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                gp REAL,
                mpg REAL,
                ppg REAL,
                fgm REAL,
                fga REAL,
                fg_pct REAL,
                tpm REAL,
                tpa REAL,
                tp_pct REAL,
                ftm REAL,
                fta REAL,
                ft_pct REAL,
                orb REAL,
                drb REAL,
                rpg REAL,
                apg REAL,
                spg REAL,
                bpg REAL,
                tov REAL,
                pf REAL,
                updated_at TEXT NOT NULL,
                UNIQUE (team_id, league_code, season)
            );

            CREATE TABLE IF NOT EXISTS refresh_log (
                id INTEGER PRIMARY KEY,
                refreshed_at TEXT NOT NULL,
                rows_saved INTEGER NOT NULL,
                leagues_ok INTEGER NOT NULL,
                leagues_failed INTEGER NOT NULL
            );
            """
        )


def _number(value: object) -> float | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def upsert_team_stats(frame: pd.DataFrame, db_path: Path | str | None = None) -> int:
    """Insert or replace competition averages for the leagues present in ``frame``.

    Leagues that are absent from the frame are left untouched, so a failed
    scrape does not wipe the previous snapshot.
    """
    init_db(db_path)
    if frame is None or frame.empty:
        return 0

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    saved = 0
    leagues = sorted({str(code) for code in frame["league_code"].dropna().unique()})
    with connect(db_path) as connection:
        for league_code in leagues:
            connection.execute(
                "DELETE FROM competition_stats WHERE league_code = ?",
                (league_code,),
            )
        for record in frame.to_dict(orient="records"):
            team_name = str(record.get("team_name") or "").strip()
            if not team_name:
                continue
            connection.execute("INSERT OR IGNORE INTO teams (name) VALUES (?)", (team_name,))
            team_id = connection.execute(
                "SELECT id FROM teams WHERE name = ?",
                (team_name,),
            ).fetchone()["id"]
            payload = [_number(record.get(field)) for field in STAT_FIELDS]
            connection.execute(
                f"""
                INSERT INTO competition_stats (
                    team_id, league_code, league_name, scope, country, season,
                    source_name, source_url, {", ".join(STAT_FIELDS)}, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, {", ".join("?" for _ in STAT_FIELDS)}, ?
                )
                """,
                [
                    team_id,
                    record.get("league_code"),
                    record.get("league_name"),
                    record.get("scope"),
                    record.get("country"),
                    record.get("season"),
                    record.get("source_name") or "",
                    record.get("source_url") or "",
                    *payload,
                    now,
                ],
            )
            saved += 1
        connection.execute("DELETE FROM teams WHERE id NOT IN (SELECT team_id FROM competition_stats)")
        connection.execute(
            """
            INSERT INTO refresh_log (refreshed_at, rows_saved, leagues_ok, leagues_failed)
            VALUES (?, ?, ?, ?)
            """,
            (now, saved, len(leagues), 0),
        )
        connection.commit()
    return saved


def list_team_names(db_path: Path | str | None = None) -> list[str]:
    """Return every stored team name, sorted for the search bar."""
    init_db(db_path)
    with connect(db_path) as connection:
        rows = connection.execute("SELECT name FROM teams ORDER BY name COLLATE NOCASE").fetchall()
    return [row["name"] for row in rows]


def list_cross_competition_teams(db_path: Path | str | None = None) -> list[str]:
    """Teams that have both a European cup and a domestic league."""
    init_db(db_path)
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT t.name
            FROM teams t
            JOIN competition_stats c ON c.team_id = t.id
            GROUP BY t.id
            HAVING SUM(CASE WHEN c.scope = 'europe' THEN 1 ELSE 0 END) > 0
               AND SUM(CASE WHEN c.scope = 'domestic' THEN 1 ELSE 0 END) > 0
            ORDER BY t.name COLLATE NOCASE
            """
        ).fetchall()
    return [row["name"] for row in rows]


def search_team_names(query: str, db_path: Path | str | None = None) -> list[str]:
    """Filter stored names for the search bar, including Greek aliases."""
    return matching_names(query, list_team_names(db_path))


def _weighted(rows: list[dict[str, object]]) -> dict[str, float | int | None]:
    games = sum(float(row["gp"] or 0) for row in rows)
    summary: dict[str, float | int | None] = {
        "gp": games,
        "competitions": len(rows),
    }
    if games <= 0:
        for field in COUNTING_FIELDS:
            summary[field] = None
        summary["fg_pct"] = summary["tp_pct"] = summary["ft_pct"] = None
        return summary

    for field in COUNTING_FIELDS:
        weighted = 0.0
        weight = 0.0
        for row in rows:
            if row.get(field) is None:
                continue
            row_games = float(row["gp"] or 0)
            weighted += float(row[field]) * row_games
            weight += row_games
        summary[field] = weighted / weight if weight else None

    summary["fg_pct"] = _weighted_percent(rows, "fgm", "fga", "fg_pct", games)
    summary["tp_pct"] = _weighted_percent(rows, "tpm", "tpa", "tp_pct", games)
    summary["ft_pct"] = _weighted_percent(rows, "ftm", "fta", "ft_pct", games)
    return summary


def _weighted_percent(
    rows: list[dict[str, object]],
    made_key: str,
    attempted_key: str,
    percent_key: str,
    games: float,
) -> float | None:
    made = 0.0
    attempted = 0.0
    saw_attempts = False
    for row in rows:
        row_games = float(row["gp"] or 0)
        made_value = row.get(made_key)
        attempted_value = row.get(attempted_key)
        if made_value is None or attempted_value is None:
            continue
        saw_attempts = True
        made += float(made_value) * row_games
        attempted += float(attempted_value) * row_games
    if saw_attempts and attempted > 0:
        return made / attempted

    weighted = 0.0
    weight = 0.0
    for row in rows:
        if row.get(percent_key) is None:
            continue
        row_games = float(row["gp"] or 0)
        weighted += float(row[percent_key]) * row_games
        weight += row_games
    if weight <= 0:
        return None
    return weighted / weight if games else None


def _competition_dict(row: sqlite3.Row) -> dict[str, object]:
    item = {key: row[key] for key in row.keys()}
    for field in STAT_FIELDS:
        item[field] = _number(item.get(field))
    return item


def get_team_stats(name: str, db_path: Path | str | None = None) -> dict[str, object] | None:
    """Return one team's competition rows plus Europe, domestic, and combined averages."""
    init_db(db_path)
    names = list_team_names(db_path)
    resolved = resolve_team_name(name, names)
    if resolved is None:
        return None

    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT c.*
            FROM competition_stats c
            JOIN teams t ON t.id = c.team_id
            WHERE t.name = ?
            """,
            (resolved,),
        ).fetchall()
    competitions = [_competition_dict(row) for row in rows]
    competitions.sort(key=lambda item: (SCOPE_ORDER.get(str(item["scope"]), 9), str(item["league_name"])))
    if not competitions:
        return None

    scopes = {
        "combined": _weighted(competitions),
        "europe": _weighted([row for row in competitions if row["scope"] == "europe"])
        if any(row["scope"] == "europe" for row in competitions)
        else None,
        "domestic": _weighted([row for row in competitions if row["scope"] == "domestic"])
        if any(row["scope"] == "domestic" for row in competitions)
        else None,
        "regional": _weighted([row for row in competitions if row["scope"] == "regional"])
        if any(row["scope"] == "regional" for row in competitions)
        else None,
    }
    updated = max(str(row["updated_at"]) for row in competitions)
    return {
        "team": resolved,
        "updated_at": updated,
        "competitions": competitions,
        "scopes": scopes,
    }


def dataset_summary(db_path: Path | str | None = None) -> dict[str, object]:
    """Counts and the timestamp of the latest saved snapshot."""
    init_db(db_path)
    with connect(db_path) as connection:
        teams = connection.execute("SELECT COUNT(*) AS n FROM teams").fetchone()["n"]
        leagues = connection.execute(
            "SELECT COUNT(DISTINCT league_code) AS n FROM competition_stats"
        ).fetchone()["n"]
        rows = connection.execute("SELECT COUNT(*) AS n FROM competition_stats").fetchone()["n"]
        latest = connection.execute(
            "SELECT refreshed_at, rows_saved FROM refresh_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return {
        "teams": teams,
        "leagues": leagues,
        "rows": rows,
        "refreshed_at": latest["refreshed_at"] if latest else None,
        "rows_saved": latest["rows_saved"] if latest else 0,
    }
