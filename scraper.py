"""Pull team averages from Euroleague and RealGM into a DataFrame.

RealGM sits behind Cloudflare and the Euroleague stats site is a JavaScript
app. ``requests`` hits each source directly. When the HTML has no stats
table, the same URL is read again through a text reader. If the Euroleague
page still has no table, the public team-statistics feed for season E2025
is used, and only when the RealGM Euroleague table is missing, so a club is
not counted twice.
"""

from __future__ import annotations

import logging
import re
import time
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

LEAGUES: list[dict[str, str]] = [
    {
        "league_code": "euroleague",
        "league_name": "Euroleague",
        "scope": "europe",
        "country": "Ευρώπη",
        "season": "2025-26",
        "url": (
            "https://basketball.realgm.com/international/league/1/Euroleague/"
            "team-stats/2026/Averages/Team_Totals"
        ),
    },
    {
        "league_code": "eurocup",
        "league_name": "Eurocup",
        "scope": "europe",
        "country": "Ευρώπη",
        "season": "2025-26",
        "url": "https://basketball.realgm.com/international/league/2/Eurocup/team-stats/2026/Averages",
    },
    {
        "league_code": "aba",
        "league_name": "Liga ABA",
        "scope": "regional",
        "country": "Αδριατική",
        "season": "2025-26",
        "url": (
            "https://basketball.realgm.com/international/league/18/"
            "Adriatic-League-Liga-ABA/team-stats/2026/Averages"
        ),
    },
    {
        "league_code": "acb",
        "league_name": "Spanish ACB",
        "scope": "domestic",
        "country": "Ισπανία",
        "season": "2025-26",
        "url": "https://basketball.realgm.com/international/league/4/Spanish-ACB/team-stats/2026/Averages",
    },
    {
        "league_code": "greek_a1",
        "league_name": "Greek HEBA A1",
        "scope": "domestic",
        "country": "Ελλάδα",
        "season": "2025-26",
        "url": "https://basketball.realgm.com/international/league/8/Greek-HEBA-A1/team-stats/2026/Averages",
    },
    {
        "league_code": "turkish_bsl",
        "league_name": "Turkish BSL",
        "scope": "domestic",
        "country": "Τουρκία",
        "season": "2025-26",
        "url": "https://basketball.realgm.com/international/league/7/Turkish-BSL/team-stats/2026/Averages",
    },
    {
        "league_code": "israeli_bsl",
        "league_name": "Israeli BSL",
        "scope": "domestic",
        "country": "Ισραήλ",
        "season": "2025-26",
        "url": "https://basketball.realgm.com/international/league/11/Israeli-BSL/team-stats/2026/Averages",
    },
    {
        "league_code": "lega_a",
        "league_name": "Italian Lega Basket Serie A",
        "scope": "domestic",
        "country": "Ιταλία",
        "season": "2025-26",
        "url": (
            "https://basketball.realgm.com/international/league/6/"
            "Italian-Lega-Basket-Serie-A/team-stats/2026/Averages"
        ),
    },
    {
        "league_code": "jeep_elite",
        "league_name": "French Jeep Elite",
        "scope": "domestic",
        "country": "Γαλλία",
        "season": "2025-26",
        "url": (
            "https://basketball.realgm.com/international/league/12/"
            "French-Jeep-Elite/team-stats/2026/Averages"
        ),
    },
    {
        "league_code": "bbl",
        "league_name": "German BBL",
        "scope": "domestic",
        "country": "Γερμανία",
        "season": "2025-26",
        "url": "https://basketball.realgm.com/international/league/15/German-BBL/team-stats/2026/Averages",
    },
    {
        "league_code": "lkl",
        "league_name": "Lithuanian LKL",
        "scope": "domestic",
        "country": "Λιθουανία",
        "season": "2025-26",
        "url": "https://basketball.realgm.com/international/league/10/Lithuanian-LKL/team-stats/2026/Averages",
    },
]

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
            time.sleep(1.2 * (attempt + 1))
            continue
        if _is_challenge(response.text) or parse_stats_document(response.text).empty:
            last_error = "Η σελίδα απάντησε χωρίς πίνακα στατιστικών."
            time.sleep(1.2 * (attempt + 1))
            continue
        return response.text
    raise RuntimeError(last_error)


def fetch_page(url: str) -> str:
    """Download a stats page with requests, rendering it if the table is missing."""
    direct = _fetch_direct(url)
    if direct is not None and not parse_stats_document(direct).empty:
        return direct
    return _fetch_rendered(url)


def scrape_league(league: dict[str, str]) -> pd.DataFrame:
    """Scrape one competition table into a clean DataFrame."""
    document = fetch_page(league["url"])
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
                "ftm": parse_number(item.get("freeThrowsMade")),
                "fta": parse_number(item.get("freeThrowsAttempted")),
                "ft_pct": parse_percent(item.get("freeThrowsPercentage")),
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


def euroleague_fallback(league_code: str) -> pd.DataFrame:
    """Official team averages used only when that RealGM table is missing."""
    league = next(item for item in LEAGUES if item["league_code"] == league_code)
    if league_code == "euroleague":
        competition, season_code = "E", "E2025"
    elif league_code == "eurocup":
        competition, season_code = "U", "U2025"
    else:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)
    rows = fetch_euroleague_team_api(competition, season_code)
    frame = annotate(pd.DataFrame(rows), league, "Euroleague API")
    if not frame.empty:
        frame["source_url"] = EUROLEAGUE_TEAM_API.format(competition=competition) + f"?SeasonCode={season_code}"
    return frame


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


def scrape_all(progress: ProgressCallback | None = None) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    """Scrape every configured competition and return one combined DataFrame."""
    frames: list[pd.DataFrame] = []
    reports: list[dict[str, object]] = []
    total = len(LEAGUES) + 1
    succeeded: set[str] = set()

    for index, league in enumerate(LEAGUES):
        if progress:
            progress(index, total, f"Ανάγνωση {league['league_name']}...")
        try:
            frame = scrape_league(league)
        except Exception as exc:  # noqa: BLE001 - one league should not abort the rest
            logger.warning("Failed to scrape %s: %s", league["league_name"], exc)
            reports.append(
                {
                    "league": league["league_name"],
                    "league_code": league["league_code"],
                    "ok": False,
                    "rows": 0,
                    "error": str(exc),
                    "url": league["url"],
                }
            )
            continue
        frames.append(frame)
        succeeded.add(league["league_code"])
        reports.append(
            {
                "league": league["league_name"],
                "league_code": league["league_code"],
                "ok": True,
                "rows": int(len(frame)),
                "url": league["url"],
            }
        )
        time.sleep(0.25)

    if progress:
        progress(len(LEAGUES), total, "Έλεγχος επίσημης σελίδας Euroleague...")
    site = probe_euroleague_site()
    if "euroleague" in succeeded:
        reports.append(
            {
                "league": "Euroleague (επίσημη σελίδα)",
                "league_code": "euroleague_site",
                "ok": True,
                "rows": 0,
                "url": EUROLEAGUE_PLAYERS_URL,
                "note": (
                    "Ο πίνακας ομάδων της Euroleague ήρθε από τη RealGM, "
                    "ώστε η ίδια διοργάνωση να μην μετρήσει δύο φορές."
                ),
            }
        )
    elif site.get("ok"):
        euro_league = next(item for item in LEAGUES if item["league_code"] == "euroleague")
        frame = annotate(parse_stats_document(str(site["document"])), euro_league, "Euroleague")
        if not frame.empty and len(frame) <= 40:
            frames.append(frame)
            succeeded.add("euroleague")
            reports.append(
                {
                    "league": "Euroleague (επίσημη σελίδα)",
                    "league_code": "euroleague",
                    "ok": True,
                    "rows": int(len(frame)),
                    "url": EUROLEAGUE_PLAYERS_URL,
                }
            )
    else:
        reports.append(
            {
                "league": "Euroleague (επίσημη σελίδα)",
                "league_code": "euroleague_site",
                "ok": False,
                "rows": 0,
                "error": str(site.get("detail") or "Χωρίς πίνακα ομάδων."),
                "url": EUROLEAGUE_PLAYERS_URL,
            }
        )

    for league_code, label in (("euroleague", "Euroleague"), ("eurocup", "Eurocup")):
        if league_code in succeeded:
            continue
        try:
            frame = euroleague_fallback(league_code)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Euroleague API fallback failed for %s: %s", league_code, exc)
            continue
        if frame.empty:
            continue
        frames.append(frame)
        reports.append(
            {
                "league": f"{label} (επίσημο feed)",
                "league_code": league_code,
                "ok": True,
                "rows": int(len(frame)),
                "url": EUROLEAGUE_TEAM_API.format(competition="E" if league_code == "euroleague" else "U"),
                "note": "Εναλλακτική πηγή επειδή ο πίνακας της RealGM δεν διαβάστηκε.",
            }
        )

    if progress:
        progress(total, total, "Ολοκληρώθηκε η άντληση")

    if not frames:
        return pd.DataFrame(columns=OUTPUT_COLUMNS), reports
    combined = pd.concat(frames, ignore_index=True)
    return combined, reports


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    from database import init_db, upsert_team_stats

    def _print_progress(done: int, total: int, label: str) -> None:
        print(f"[{done}/{total}] {label}")

    init_db()
    scraped, scrape_reports = scrape_all(_print_progress)
    saved = upsert_team_stats(scraped)
    print(f"Saved {saved} team-competition rows.")
    for report in scrape_reports:
        state = "OK" if report.get("ok") else "FAIL"
        print(f"{state:4} {report.get('league')}: {report.get('rows', 0)} {report.get('error') or report.get('note') or ''}")
