"""Ratings and shooting efficiency from the collected per-game averages.

The same ratios come out of season totals, because every term scales with
games played. Defensive and net rating stay empty until points allowed exist.
"""

from __future__ import annotations

EXTRA_FIELDS = (
    "opp_ppg",
    "possessions",
    "off_rtg",
    "def_rtg",
    "net_rtg",
    "efg_pct",
    "ts_pct",
)


def _as_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if number != number:
        return None
    return number


def possessions(fga: object, orb: object, tov: object, fta: object) -> float | None:
    """0.96 × (FGA − ORB + TO + 0.44 × FTA)."""
    attempts = _as_float(fga)
    offensive_rebounds = _as_float(orb)
    turnovers = _as_float(tov)
    free_throws = _as_float(fta)
    if None in {attempts, offensive_rebounds, turnovers, free_throws}:
        return None
    assert attempts is not None and offensive_rebounds is not None
    assert turnovers is not None and free_throws is not None
    return 0.96 * (attempts - offensive_rebounds + turnovers + 0.44 * free_throws)


def offensive_rating(points: object, poss: object) -> float | None:
    """(Points scored × 100) / possessions."""
    scored = _as_float(points)
    possessions_value = _as_float(poss)
    if scored is None or possessions_value is None or possessions_value == 0:
        return None
    return (scored * 100.0) / possessions_value


def defensive_rating(points_allowed: object, poss: object) -> float | None:
    """(Points allowed × 100) / possessions."""
    allowed = _as_float(points_allowed)
    possessions_value = _as_float(poss)
    if allowed is None or possessions_value is None or possessions_value == 0:
        return None
    return (allowed * 100.0) / possessions_value


def net_rating(off_rtg: object, def_rtg: object) -> float | None:
    """Offensive rating − defensive rating."""
    offensive = _as_float(off_rtg)
    defensive = _as_float(def_rtg)
    if offensive is None or defensive is None:
        return None
    return offensive - defensive


def effective_fg(fgm: object, tpm: object, fga: object) -> float | None:
    """(FGM + 0.5 × 3PM) / FGA."""
    made = _as_float(fgm)
    threes = _as_float(tpm)
    attempts = _as_float(fga)
    if made is None or threes is None or attempts is None or attempts == 0:
        return None
    return (made + 0.5 * threes) / attempts


def true_shooting(points: object, fga: object, fta: object) -> float | None:
    """Points scored / (2 × (FGA + 0.44 × FTA))."""
    scored = _as_float(points)
    attempts = _as_float(fga)
    free_throws = _as_float(fta)
    if scored is None or attempts is None or free_throws is None:
        return None
    denominator = 2.0 * (attempts + 0.44 * free_throws)
    if denominator == 0:
        return None
    return scored / denominator


def apply_advanced(stats: dict) -> dict:
    """Fill possessions, ratings, eFG% and TS% on a per-game stat row."""
    poss = possessions(stats.get("fga"), stats.get("orb"), stats.get("tov"), stats.get("fta"))
    points = _as_float(stats.get("ppg"))
    allowed = _as_float(stats.get("opp_ppg"))
    off_rtg = offensive_rating(points, poss)
    def_rtg = defensive_rating(allowed, poss)
    stats["possessions"] = poss
    stats["off_rtg"] = off_rtg
    stats["def_rtg"] = def_rtg
    stats["net_rtg"] = net_rating(off_rtg, def_rtg)
    stats["efg_pct"] = effective_fg(stats.get("fgm"), stats.get("tpm"), stats.get("fga"))
    stats["ts_pct"] = true_shooting(points, stats.get("fga"), stats.get("fta"))
    return stats
