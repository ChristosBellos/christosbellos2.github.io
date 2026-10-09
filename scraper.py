"""Pull team averages from Euroleague and RealGM into a DataFrame.

RealGM sits behind Cloudflare and the Euroleague stats site is a JavaScript
app. ``requests`` hits each source directly. When the HTML has no stats
table, the same URL is read again through a text reader. If the Euroleague
page still has no table, the public team-statistics feed for season E2025
is used, and only when the RealGM Euroleague table is missing, so a club is
not counted twice.
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import pandas as pd
import requests
from bs4 import BeautifulSoup

from names import canonical_team_name

logger = logging.getLogger(__name__)

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,el;q=0.8",
}

READER_PREFIX = "https://r.jina.ai/"

EUROLEAGUE_PLAYERS_URL = (
    "https://www.euroleaguebasketball.net/en/euroleague/stats/players/"
    "?size=1000&viewType=traditional&statisticMode=perGame"
    "&seasonCode=E2025&seasonMode=Single&sortDirection=ascending&statistic="
)

EUROLEAGUE_TEAM_API = (
    "https://api-live.euroleague.net/v3/competitions/"
    "{competition}/statistics/teams/traditional"
)
EUROLEAGUE_GAMES_URL = (
    "https://api-live.euroleague.net/v2/competitions/{competition}/seasons/{season_code}/games"
)
EUROLEAGUE_GAME_STATS_URL = (
    "https://api-live.euroleague.net/v2/competitions/"
    "{competition}/seasons/{season_code}/games/{game_code}/stats"
)

CURRENT_SEASON = "2026-27"
PREVIOUS_SEASON = "2025-26"

LEAGUES: list[dict[str, str]] = [
    {
        "league_code": "euroleague",
        "league_name": "Euroleague",
        "scope": "europe",
        "country": "Ευρώπη",
        "season": CURRENT_SEASON,
        "url": (
            "https://basketball.realgm.com/international/league/1/Euroleague/"
            "team-stats/2027/points/Team_Totals"
        ),
    },
    {
        "league_code": "eurocup",
        "league_name": "Eurocup",
        "scope": "europe",
        "country": "Ευρώπη",
        "season": CURRENT_SEASON,
        "url": "https://basketball.realgm.com/international/league/2/Eurocup/team-stats/2027/points/Team_Totals",
    },
    {
        "league_code": "aba",
        "league_name": "Liga ABA",
        "scope": "regional",
        "country": "Αδριατική",
        "season": CURRENT_SEASON,
        "url": (
            "https://basketball.realgm.com/international/league/18/"
            "Adriatic-League-Liga-ABA/team-stats/2027/points/Team_Totals"
        ),
    },
    {
        "league_code": "acb",
        "league_name": "Spanish ACB",
        "scope": "domestic",
        "country": "Ισπανία",
        "season": CURRENT_SEASON,
        "url": "https://basketball.realgm.com/international/league/4/Spanish-ACB/team-stats/2027/points/Team_Totals",
    },
    {
        "league_code": "greek_a1",
        "league_name": "Greek HEBA A1",
        "scope": "domestic",
        "country": "Ελλάδα",
        "season": CURRENT_SEASON,
        "url": "https://basketball.realgm.com/international/league/8/Greek-HEBA-A1/team-stats/2027/points/Team_Totals",
    },
    {
        "league_code": "turkish_bsl",
        "league_name": "Turkish BSL",
        "scope": "domestic",
        "country": "Τουρκία",
        "season": CURRENT_SEASON,
        "url": "https://basketball.realgm.com/international/league/7/Turkish-BSL/team-stats/2027/points/Team_Totals",
    },
    {
        "league_code": "israeli_bsl",
        "league_name": "Israeli BSL",
        "scope": "domestic",
        "country": "Ισραήλ",
        "season": CURRENT_SEASON,
        "url": "https://basketball.realgm.com/international/league/11/Israeli-BSL/team-stats/2027/points/Team_Totals",
    },
    {
        "league_code": "lega_a",
        "league_name": "Italian Lega Basket Serie A",
        "scope": "domestic",
        "country": "Ιταλία",
        "season": CURRENT_SEASON,
        "url": (
            "https://basketball.realgm.com/international/league/6/"
            "Italian-Lega-Basket-Serie-A/team-stats/2027/points/Team_Totals"
        ),
    },
    {
        "league_code": "jeep_elite",
        "league_name": "French Jeep Elite",
        "scope": "domestic",
        "country": "Γαλλία",
        "season": CURRENT_SEASON,
        "url": (
            "https://basketball.realgm.com/international/league/12/"
            "French-Jeep-Elite/team-stats/2027/points/Team_Totals"
        ),
    },
    {
        "league_code": "bbl",
        "league_name": "German BBL",
        "scope": "domestic",
        "country": "Γερμανία",
        "season": CURRENT_SEASON,
        "url": "https://basketball.realgm.com/international/league/15/German-BBL/team-stats/2027/points/Team_Totals",
    },
    {
        "league_code": "lkl",
        "league_name": "Lithuanian LKL",
        "scope": "domestic",
        "country": "Λιθουανία",
        "season": CURRENT_SEASON,
        "url": "https://basketball.realgm.com/international/league/10/Lithuanian-LKL/team-stats/2027/points/Team_Totals",
    },
]

LEAGUE_META = {
    league["league_code"]: {
        "league_name": league["league_name"],
        "scope": league["scope"],
        "country": league["country"],
    }
    for league in LEAGUES
}

HEADER_MAP = {
    "#": None,
    "team": "team_name",
    "gp": "gp",
    "mpg": "mpg",
    "ppg": "ppg",
    "fgm": "fgm",
    "fga": "fga",
    "fg%": "fg_pct",
    "3pm": "tpm",
    "3pa": "tpa",
    "3p%": "tp_pct",
    "ftm": "ftm",
    "fta": "fta",
    "ft%": "ft_pct",
    "orb": "orb",
    "drb": "drb",
    "rpg": "rpg",
    "apg": "apg",
    "spg": "spg",
    "bpg": "bpg",
    "tov": "tov",
    "pf": "pf",
}

STAT_FIELDS = [
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
]

OUTPUT_COLUMNS = [
    "team_name",
    "league_code",
    "league_name",
    "scope",
    "country",
    "season",
    "source_name",
    "source_url",
    *STAT_FIELDS,
]

ProgressCallback = Callable[[int, int, str], None]

_session = requests.Session()
_session.headers.update(BROWSER_HEADERS)


def parse_number(value: object) -> float | None:
    """Parse a table cell into a float."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace(",", ".")
    if text.lower() in {"", "-", "—", "na", "n/a", "none"}:
        return None
    text = text.replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None


def parse_percent(value: object) -> float | None:
    """Parse a shooting percentage into a 0-1 ratio."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    raw = str(value).strip()
    marked = raw.endswith("%")
    number = parse_number(raw)
    if number is None:
        return None
    if marked or number > 1:
        return number / 100.0
    return number


def _is_challenge(text: str) -> bool:
    sample = text[:4000].lower()
    markers = (
        "just a moment",
        "performing security verification",
        "security checkpoint",
        "maybe requiring captcha",
        "enable javascript and cookies",
    )
    return any(marker in sample for marker in markers)


def _split_markdown_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _clean_team(cell: str) -> str:
    match = re.search(r"\[([^\]]+)\]", cell)
    text = match.group(1) if match else cell
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_stats_header(headers: list[str]) -> bool:
    folded = {header.strip().lower() for header in headers}
    return "team" in folded and "gp" in folded and ("ppg" in folded or "pts" in folded)


def _frame_from_rows(headers: list[str], records: list[list[str]]) -> pd.DataFrame:
    index: dict[str, int] = {}
    for position, header in enumerate(headers):
        field = HEADER_MAP.get(header.strip().lower())
        if field:
            index[field] = position
    if "team_name" not in index:
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in records:
        if index["team_name"] >= len(record):
            continue
        team_name = canonical_team_name(_clean_team(record[index["team_name"]]))
        if not team_name or fold_token(team_name) in {"team", "totals", "average"}:
            continue
        item: dict[str, object] = {"team_name": team_name}
        for field, position in index.items():
            if field == "team_name":
                continue
            raw = record[position] if position < len(record) else None
            item[field] = parse_percent(raw) if field.endswith("_pct") else parse_number(raw)
        games = item.get("gp")
        if not isinstance(games, (int, float)) or games <= 0:
            continue
        if team_name in seen:
            continue
        seen.add(team_name)
        rows.append(item)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def fold_token(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def parse_markdown_table(text: str) -> pd.DataFrame:
    """Read the first markdown stats table in a rendered page."""
    lines = text.splitlines()
    header_at = None
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        headers = _split_markdown_row(line)
        if _is_stats_header(headers):
            header_at = index
            break
    if header_at is None:
        return pd.DataFrame()

    headers = _split_markdown_row(lines[header_at])
    records: list[list[str]] = []
    for line in lines[header_at + 1 :]:
        if not line.strip().startswith("|"):
            if records:
                break
            continue
        cells = _split_markdown_row(line)
        if cells and set(cells[0]) <= set("-: "):
            continue
        records.append(cells)
    return _frame_from_rows(headers, records)


def parse_html_table(html: str) -> pd.DataFrame:
    """Read the first HTML stats table."""
    if "<table" not in html.lower():
        return pd.DataFrame()
    soup = BeautifulSoup(html, "lxml")
    for table in soup.find_all("table"):
        header_row = table.find("tr")
        if header_row is None:
            continue
        headers = [cell.get_text(" ", strip=True) for cell in header_row.find_all(["th", "td"])]
        if not _is_stats_header(headers):
            continue
        records: list[list[str]] = []
        for row in table.find_all("tr")[1:]:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
            if cells:
                records.append(cells)
        frame = _frame_from_rows(headers, records)
        if not frame.empty:
            return frame
    return pd.DataFrame()


def season_unavailable(text: str) -> bool:
    """True when the stats page exists but the season has no games yet."""
    return "stats are not available for this season" in (text or "").lower()


def parse_stats_document(text: str) -> pd.DataFrame:
    """Parse either a markdown reader page or raw HTML into team averages."""
    if not text or _is_challenge(text):
        return pd.DataFrame()
    if "| Team |" in text or "| # | Team |" in text:
        frame = parse_markdown_table(text)
        if not frame.empty:
            return frame
    frame = parse_html_table(text)
    if not frame.empty:
        return frame
    return parse_markdown_table(text)


def annotate(frame: pd.DataFrame, league: dict[str, str], source_name: str) -> pd.DataFrame:
    """Attach league metadata to a parsed stats table."""
    if frame.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    annotated = frame.copy()
    annotated["league_code"] = league["league_code"]
    annotated["league_name"] = league["league_name"]
    annotated["scope"] = league["scope"]
    annotated["country"] = league["country"]
    annotated["season"] = league["season"]
    annotated["source_name"] = source_name
    annotated["source_url"] = league["url"]
    for field in STAT_FIELDS:
        if field not in annotated.columns:
            annotated[field] = None
    return annotated[OUTPUT_COLUMNS]


def _fetch_direct(url: str) -> str | None:
    try:
        response = _session.get(url, timeout=20)
    except requests.RequestException as exc:
        logger.info("Direct request failed for %s: %s", url, exc)
        return None
    if response.status_code >= 400 or _is_challenge(response.text):
        logger.info("Direct request blocked for %s (%s)", url, response.status_code)
        return None
    if season_unavailable(response.text):
        return response.text
    if parse_stats_document(response.text).empty and "application/json" not in response.headers.get(
        "content-type", ""
    ):
        return None
    return response.text


def _fetch_rendered(url: str) -> str:
    last_error = "Ο πίνακας στατιστικών δεν ήταν διαθέσιμος."
    reader_url = READER_PREFIX + url
    for attempt in range(3):
        try:
            response = _session.get(
                reader_url,
                headers={"Accept": "text/plain", "User-Agent": BROWSER_HEADERS["User-Agent"]},
                timeout=75,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            last_error = str(exc)
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 403:
                break
            time.sleep(1.2 * (attempt + 1))
            continue
        if season_unavailable(response.text):
            return response.text
        if _is_challenge(response.text) or parse_stats_document(response.text).empty:
            last_error = "Η σελίδα απάντησε χωρίς πίνακα στατιστικών."
            time.sleep(1.2 * (attempt + 1))
            continue
        return response.text
    raise RuntimeError(last_error)


def fetch_page(url: str) -> str:
    """Download a stats page with requests, rendering it if the table is missing."""
    direct = _fetch_direct(url)
    if direct is not None and (
        season_unavailable(direct) or not parse_stats_document(direct).empty
    ):
        return direct
    return _fetch_rendered(url)


def scrape_league(league: dict[str, str]) -> pd.DataFrame:
    """Scrape one competition table into a clean DataFrame.

    An empty frame means the season page loaded and has no games yet.
    """
    document = fetch_page(league["url"])
    if season_unavailable(document):
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    frame = parse_stats_document(document)
    if frame.empty:
        raise RuntimeError(f"Δεν βρέθηκε πίνακας για {league['league_name']}.")
    return annotate(frame, league, "RealGM")


def _percent_or_ratio(made: float, attempted: float, fallback: object) -> float | None:
    if attempted:
        return made / attempted
    return parse_percent(fallback)


def fetch_euroleague_team_api(competition: str, season_code: str) -> list[dict[str, object]]:
    """Read traditional per-game team stats from the Euroleague stats feed."""
    response = _session.get(
        EUROLEAGUE_TEAM_API.format(competition=competition),
        params={
            "statisticMode": "PerGame",
            "SeasonMode": "Single",
            "SeasonCode": season_code,
            "limit": 200,
        },
        headers={"Accept": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    rows: list[dict[str, object]] = []
    for item in payload.get("teams", []):
        team = item.get("team") or {}
        name = canonical_team_name(str(team.get("name") or ""))
        two_made = parse_number(item.get("twoPointersMade")) or 0.0
        two_attempted = parse_number(item.get("twoPointersAttempted")) or 0.0
        three_made = parse_number(item.get("threePointersMade")) or 0.0
        three_attempted = parse_number(item.get("threePointersAttempted")) or 0.0
        free_made = parse_number(item.get("freeThrowsMade")) or 0.0
        free_attempted = parse_number(item.get("freeThrowsAttempted")) or 0.0
        made = two_made + three_made
        attempted = two_attempted + three_attempted
        rows.append(
            {
                "team_name": name,
                "gp": parse_number(item.get("gamesPlayed")),
                "mpg": parse_number(item.get("minutesPlayed")),
                "ppg": parse_number(item.get("pointsScored")),
                "fgm": made,
                "fga": attempted,
                "fg_pct": _percent_or_ratio(made, attempted, None),
                "tpm": three_made,
                "tpa": three_attempted,
                "tp_pct": _percent_or_ratio(
                    three_made, three_attempted, item.get("threePointersPercentage")
                ),
                "ftm": free_made,
                "fta": free_attempted,
                "ft_pct": _percent_or_ratio(free_made, free_attempted, item.get("freeThrowsPercentage")),
                "orb": parse_number(item.get("offensiveRebounds")),
                "drb": parse_number(item.get("defensiveRebounds")),
                "rpg": parse_number(item.get("totalRebounds")),
                "apg": parse_number(item.get("assists")),
                "spg": parse_number(item.get("steals")),
                "bpg": parse_number(item.get("blocks")),
                "tov": parse_number(item.get("turnovers")),
                "pf": parse_number(item.get("foulsCommited")),
            }
        )
    return rows


def euroleague_api_codes(league_code: str, season: str) -> tuple[str, str] | None:
    """Map a league and season label to the Euroleague feed codes."""
    start_year = season.split("-")[0]
    if league_code == "euroleague":
        return "E", f"E{start_year}"
    if league_code == "eurocup":
        return "U", f"U{start_year}"
    return None


def _averages_from_logs(logs: pd.DataFrame, league: dict[str, str]) -> pd.DataFrame:
    """Turn per-game lines into one GP-weighted average row per team."""
    if logs is None or logs.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    rows: list[dict[str, object]] = []
    for name, games in logs.groupby("team_name", sort=False):
        played = len(games)

        def total(column: str) -> float:
            return float(games[column].fillna(0).sum())

        fgm, fga = total("fgm"), total("fga")
        tpm, tpa = total("tpm"), total("tpa")
        ftm, fta = total("ftm"), total("fta")
        opponent = None
        if "points_allowed" in games.columns and games["points_allowed"].notna().all():
            opponent = total("points_allowed") / played
        rows.append(
            {
                "team_name": name,
                "gp": float(played),
                "mpg": total("minutes") / played,
                "ppg": total("points") / played,
                "fgm": fgm / played,
                "fga": fga / played,
                "fg_pct": fgm / fga if fga else None,
                "tpm": tpm / played,
                "tpa": tpa / played,
                "tp_pct": tpm / tpa if tpa else None,
                "ftm": ftm / played,
                "fta": fta / played,
                "ft_pct": ftm / fta if fta else None,
                "orb": total("orb") / played,
                "drb": total("drb") / played,
                "rpg": total("reb") / played,
                "apg": total("ast") / played,
                "spg": total("stl") / played,
                "bpg": total("blk") / played,
                "tov": total("tov") / played,
                "pf": total("pf") / played,
                "opp_ppg": opponent,
            }
        )
    frame = pd.DataFrame(rows)
    annotated = annotate(frame, league, "Euroleague API")
    if not annotated.empty and "opp_ppg" in frame.columns:
        annotated = annotated.merge(frame[["team_name", "opp_ppg"]], on="team_name", how="left")
    return annotated


def played_euro_games(league_code: str, season: str) -> int | None:
    """How many Euroleague or Eurocup games have a final score, if the feed answers."""
    codes = euroleague_api_codes(league_code, season)
    if codes is None:
        return None
    competition, season_code = codes
    payload = _fetch_json(
        EUROLEAGUE_GAMES_URL.format(competition=competition, season_code=season_code) + "?limit=600"
    )
    return sum(1 for game in payload.get("data", []) if game.get("played"))


def euroleague_fallback(league: dict[str, str]) -> pd.DataFrame:
    """Official team averages used only when that RealGM page cannot be read."""
    codes = euroleague_api_codes(league["league_code"], league["season"])
    if codes is None:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    competition, season_code = codes
    rows = fetch_euroleague_team_api(competition, season_code)
    frame = annotate(pd.DataFrame(rows), league, "Euroleague API")
    if not frame.empty:
        frame["source_url"] = (
            EUROLEAGUE_TEAM_API.format(competition=competition) + f"?SeasonCode={season_code}"
        )
        return frame
    logs = collect_euro_game_logs(competition, season_code, league["league_code"], league["season"])
    averaged = _averages_from_logs(logs, league)
    if not averaged.empty:
        averaged["source_url"] = EUROLEAGUE_GAMES_URL.format(
            competition=competition, season_code=season_code
        )
    return averaged


def probe_euroleague_site() -> dict[str, object]:
    """Request the Euroleague stats URL from the project brief."""
    try:
        response = _session.get(EUROLEAGUE_PLAYERS_URL, timeout=20)
    except requests.RequestException as exc:
        return {"ok": False, "detail": str(exc)}
    if response.ok and not _is_challenge(response.text):
        frame = parse_stats_document(response.text)
        if not frame.empty:
            return {"ok": True, "rows": len(frame), "document": response.text}
    return {
        "ok": False,
        "status": response.status_code,
        "detail": "Η σελίδα της Euroleague δεν απέδωσε πίνακα ομάδων.",
    }


def _season_not_started(league: dict[str, str]) -> bool:
    """True when the Euroleague feed confirms this competition has no results yet."""
    try:
        played = played_euro_games(league["league_code"], league["season"])
    except Exception:  # noqa: BLE001 - a feed miss is not proof that the season is empty
        return False
    return played == 0


def scrape_all(progress: ProgressCallback | None = None) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Scrape the current season and return one combined DataFrame.

    Leagues with no games yet are reported as empty. They are not filled
    with the previous season.
    """
    frames: list[pd.DataFrame] = []
    reports: list[dict[str, object]] = []
    total = len(LEAGUES)

    for index, league in enumerate(LEAGUES):
        if progress:
            progress(index, total, f"Ανάγνωση {league['league_name']} ({CURRENT_SEASON})...")
        try:
            frame = scrape_league(league)
        except Exception as exc:  # noqa: BLE001 - one league should not abort the rest
            logger.warning("Failed to scrape %s: %s", league["league_name"], exc)
            fallback = pd.DataFrame(columns=OUTPUT_COLUMNS)
            try:
                fallback = euroleague_fallback(league)
            except Exception as fallback_exc:  # noqa: BLE001
                logger.warning("Euroleague API fallback failed for %s: %s", league["league_name"], fallback_exc)
            if not fallback.empty:
                frames.append(fallback)
                reports.append(
                    {
                        "league": league["league_name"],
                        "league_code": league["league_code"],
                        "season": league["season"],
                        "ok": True,
                        "rows": int(len(fallback)),
                        "url": league["url"],
                        "note": "Εναλλακτική πηγή επειδή ο πίνακας της RealGM δεν διαβάστηκε.",
                    }
                )
            elif _season_not_started(league):
                reports.append(
                    {
                        "league": league["league_name"],
                        "league_code": league["league_code"],
                        "season": league["season"],
                        "ok": True,
                        "rows": 0,
                        "empty": True,
                        "url": league["url"],
                        "note": "Δεν έχουν παιχτεί αγώνες.",
                    }
                )
            else:
                reports.append(
                    {
                        "league": league["league_name"],
                        "league_code": league["league_code"],
                        "season": league["season"],
                        "ok": False,
                        "rows": 0,
                        "error": str(exc),
                        "url": league["url"],
                    }
                )
            continue
        if frame.empty:
            reports.append(
                {
                    "league": league["league_name"],
                    "league_code": league["league_code"],
                    "season": league["season"],
                    "ok": True,
                    "rows": 0,
                    "empty": True,
                    "url": league["url"],
                    "note": "Δεν έχουν παιχτεί αγώνες.",
                }
            )
            continue
        frames.append(frame)
        reports.append(
            {
                "league": league["league_name"],
                "league_code": league["league_code"],
                "season": league["season"],
                "ok": True,
                "rows": int(len(frame)),
                "url": league["url"],
            }
        )
        time.sleep(0.25)

    if progress:
        progress(total, total, "Ολοκληρώθηκε η άντληση")

    if not frames:
        return pd.DataFrame(columns=OUTPUT_COLUMNS), reports
    combined = pd.concat(frames, ignore_index=True)
    return combined, reports


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": BROWSER_HEADERS["User-Agent"], "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)


def _game_row(
    total: dict,
    team_name: str,
    league_code: str,
    season: str,
    round_number: int,
    points_allowed: float | None = None,
) -> dict:
    made = float(total.get("fieldGoalsMadeTotal") or 0)
    attempted = float(total.get("fieldGoalsAttemptedTotal") or 0)
    return {
        "team_name": canonical_team_name(team_name),
        "league_code": league_code,
        "season": season,
        "round_number": round_number,
        "points": float(total.get("points") or 0),
        "fgm": made,
        "fga": attempted,
        "tpm": float(total.get("fieldGoalsMade3") or 0),
        "tpa": float(total.get("fieldGoalsAttempted3") or 0),
        "ftm": float(total.get("freeThrowsMade") or 0),
        "fta": float(total.get("freeThrowsAttempted") or 0),
        "orb": float(total.get("offensiveRebounds") or 0),
        "drb": float(total.get("defensiveRebounds") or 0),
        "reb": float(total.get("totalRebounds") or 0),
        "ast": float(total.get("assistances") or 0),
        "stl": float(total.get("steals") or 0),
        "blk": float(total.get("blocksFavour") or 0),
        "tov": float(total.get("turnovers") or 0),
        "pf": float(total.get("foulsCommited") or 0),
        "minutes": float(total.get("timePlayed") or 0) / 60.0,
        "points_allowed": points_allowed,
    }


def collect_euro_game_logs(
    competition: str,
    season_code: str,
    league_code: str,
    season: str,
    workers: int = 4,
) -> pd.DataFrame:
    """Per-game team lines for one Euroleague or Eurocup season, in round order."""
    games_payload = _fetch_json(
        EUROLEAGUE_GAMES_URL.format(competition=competition, season_code=season_code) + "?limit=600"
    )
    games = [game for game in games_payload.get("data", []) if game.get("played")]
    games.sort(key=lambda game: (game.get("round") or 0, game.get("utcDate") or "", game.get("gameCode") or 0))

    def one_game(game: dict) -> list[dict]:
        stats = None
        for attempt in range(5):
            time.sleep(0.15 * (attempt + 1))
            try:
                stats = _fetch_json(
                    EUROLEAGUE_GAME_STATS_URL.format(
                        competition=competition,
                        season_code=season_code,
                        game_code=game["gameCode"],
                    )
                )
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning("Game %s failed (%s): %s", game.get("gameCode"), attempt + 1, exc)
                time.sleep(0.8 * (attempt + 1))
        if not stats:
            return []
        prepared = []
        for side in ("local", "road"):
            club = (game.get(side) or {}).get("club") or {}
            total = (stats.get(side) or {}).get("total") or {}
            name = club.get("name") or ""
            if not name or not total:
                continue
            prepared.append((side, str(name), total))
        points = {side: float(total.get("points") or 0) for side, _name, total in prepared}
        opposite = {"local": "road", "road": "local"}
        rows = []
        for side, name, total in prepared:
            allowed = points.get(opposite[side]) if opposite[side] in points else None
            rows.append(
                _game_row(
                    total,
                    name,
                    league_code,
                    season,
                    int(game.get("round") or 0),
                    points_allowed=allowed,
                )
            )
        return rows

    ordered: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for game_rows in pool.map(one_game, games):
            ordered.extend(game_rows)

    buckets: dict[str, list[dict]] = defaultdict(list)
    for row in ordered:
        buckets[row["team_name"]].append(row)
    indexed: list[dict] = []
    for team_rows in buckets.values():
        for index, row in enumerate(team_rows, start=1):
            indexed.append({**row, "game_index": index})
    return pd.DataFrame(indexed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from database import init_db, upsert_team_stats
    from export_web import write_payload

    def _print_progress(done: int, total: int, label: str) -> None:
        print(f"[{done}/{total}] {label}")

    init_db()
    scraped, scrape_reports = scrape_all(_print_progress)
    saved = upsert_team_stats(scraped)
    published = write_payload()
    print(f"Saved {saved} team-competition rows.")
    print(f"Updated {published.name} for the site.")
    for report in scrape_reports:
        state = "OK" if report.get("ok") else "FAIL"
        print(f"{state:4} {report.get('league')}: {report.get('rows', 0)} {report.get('error') or report.get('note') or ''}")
