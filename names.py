"""Canonical team names and Greek-friendly search aliases."""

from __future__ import annotations

import re
import unicodedata

# Folded keys are built at import so spelling, sponsors, and Greek aliases
# all point at the display name used in the database.
_RAW_ALIASES: dict[str, str] = {
    "Olympiacos": "Olympiacos",
    "Olympiacos Piraeus": "Olympiacos",
    "Ολυμπιακός": "Olympiacos",
    "ΟΣΦΠ": "Olympiacos",
    "osfp": "Olympiacos",
    "Panathinaikos": "Panathinaikos",
    "Panathinaikos AKTOR Athens": "Panathinaikos",
    "Παναθηναϊκός": "Panathinaikos",
    "ΠΑΟ": "Panathinaikos",
    "pao": "Panathinaikos",
    "PAOK BC": "PAOK BC",
    "ΠΑΟΚ": "PAOK BC",
    "Aris Midea Thessaloniki": "Aris Midea Thessaloniki",
    "Aris Thessaloniki": "Aris Midea Thessaloniki",
    "Aris Thessaloniki Betsson": "Aris Midea Thessaloniki",
    "Άρης": "Aris Midea Thessaloniki",
    "AEK Athens": "AEK Athens",
    "ΑΕΚ": "AEK Athens",
    "ASP Promitheas Patras": "ASP Promitheas Patras",
    "Προμηθέας": "ASP Promitheas Patras",
    "Peristeri Betsson": "Peristeri Betsson",
    "Περιστέρι": "Peristeri Betsson",
    "Maroussi BC": "Maroussi BC",
    "Μαρούσι": "Maroussi BC",
    "Panionios BC": "Panionios BC",
    "Panionios Cosmorama Travel Athens": "Panionios BC",
    "Πανιώνιος": "Panionios BC",
    "Kolossos Rodou BC": "Kolossos Rodou BC",
    "Κολοσσός": "Kolossos Rodou BC",
    "Iraklis BC": "Iraklis BC",
    "Ηρακλής": "Iraklis BC",
    "Mykonos": "Mykonos",
    "Μύκονος": "Mykonos",
    "AS Karditsas": "AS Karditsas",
    "Καρδίτσα": "AS Karditsas",
    "Real Madrid": "Real Madrid",
    "Ρεάλ": "Real Madrid",
    "Ρεάλ Μαδρίτης": "Real Madrid",
    "Barca": "Barca",
    "FC Barcelona": "Barca",
    "Barcelona": "Barca",
    "Μπαρτσελόνα": "Barca",
    "Μπάρτσα": "Barca",
    "Baskonia": "Baskonia",
    "Baskonia Vitoria-Gasteiz": "Baskonia",
    "Kosner Baskonia Vitoria-Gasteiz": "Baskonia",
    "Μπασκόνια": "Baskonia",
    "Valencia Basket": "Valencia Basket",
    "Βαλένθια": "Valencia Basket",
    "BAXI Manresa": "BAXI Manresa",
    "Kids&Us Manresa": "BAXI Manresa",
    "Fenerbahce Beko": "Fenerbahce Beko",
    "Fenerbahce Beko Istanbul": "Fenerbahce Beko",
    "Fenerbahce": "Fenerbahce Beko",
    "Φενέρμπαχτσε": "Fenerbahce Beko",
    "Anadolu Efes": "Anadolu Efes",
    "Anadolu Efes Istanbul": "Anadolu Efes",
    "Εφές": "Anadolu Efes",
    "Maccabi FOX Tel Aviv": "Maccabi FOX Tel Aviv",
    "Maccabi Rapyd Tel Aviv": "Maccabi FOX Tel Aviv",
    "Maccabi Tel Aviv": "Maccabi FOX Tel Aviv",
    "Μακάμπι": "Maccabi FOX Tel Aviv",
    "Hapoel Tel Aviv": "Hapoel Tel Aviv",
    "Hapoel IBI Tel Aviv": "Hapoel Tel Aviv",
    "Χάποελ Τελ Αβίβ": "Hapoel Tel Aviv",
    "Hapoel Bank Yahav Jerusalem": "Hapoel Bank Yahav Jerusalem",
    "Hapoel Midtown Jerusalem": "Hapoel Bank Yahav Jerusalem",
    "Zalgiris": "Zalgiris",
    "Zalgiris Kaunas": "Zalgiris",
    "Ζαλγκίρις": "Zalgiris",
    "KK Crvena Zvezda": "KK Crvena Zvezda",
    "Crvena Zvezda Meridianbet Belgrade": "KK Crvena Zvezda",
    "Crvena Zvezda": "KK Crvena Zvezda",
    "Ερυθρός Αστέρας": "KK Crvena Zvezda",
    "KK Partizan": "KK Partizan",
    "Partizan Mozzart Bet Belgrade": "KK Partizan",
    "Partizan": "KK Partizan",
    "Παρτιζάν": "KK Partizan",
    "Virtus Bologna": "Virtus Bologna",
    "Βίρτους": "Virtus Bologna",
    "AX Armani Exchange Milan": "AX Armani Exchange Milan",
    "EA7 Emporio Armani Milan": "AX Armani Exchange Milan",
    "Olimpia Milano": "AX Armani Exchange Milan",
    "Αρμάνι": "AX Armani Exchange Milan",
    "Μιλάνο": "AX Armani Exchange Milan",
    "Bayern Munich": "Bayern Munich",
    "FC Bayern Munich": "Bayern Munich",
    "Μπάγερν": "Bayern Munich",
    "AS Monaco Basket": "AS Monaco Basket",
    "AS Monaco": "AS Monaco Basket",
    "Monaco": "AS Monaco Basket",
    "Μονακό": "AS Monaco Basket",
    "Paris Basketball": "Paris Basketball",
    "Παρίσι": "Paris Basketball",
    "ASVEL Basket": "ASVEL Basket",
    "LDLC ASVEL Villeurbanne": "ASVEL Basket",
    "Dubai": "Dubai",
    "Dubai Basketball": "Dubai",
    "Neptunas": "Neptunas",
    "Neptunas Klaipeda": "Neptunas",
    "Besiktas Icrypex": "Besiktas Icrypex",
    "Besiktas Istanbul": "Besiktas Icrypex",
    "Besiktas GAIN Istanbul": "Besiktas Icrypex",
    "Umana Venezia": "Umana Venezia",
    "Umana Reyer Venice": "Umana Venezia",
    "Buducnost Voli Podgorica": "Buducnost Voli Podgorica",
    "KK Buducnost": "Buducnost Voli Podgorica",
    "KK Cedevita Olimpija Ljubljana": "KK Cedevita Olimpija Ljubljana",
    "KK Cedevita Olimpija": "KK Cedevita Olimpija Ljubljana",
    "Cedevita Olimpija Ljubljana": "KK Cedevita Olimpija Ljubljana",
    "Turk Telekom": "Turk Telekom",
    "Turk Telekom Ankara": "Turk Telekom",
    "Bahcesehir Koleji": "Bahcesehir Koleji",
    "Bahcesehir Koleji Istanbul": "Bahcesehir Koleji",
    "Bahcesehir College Istanbul": "Bahcesehir Koleji",
    "JL Bourg-en-Bresse": "JL Bourg-en-Bresse",
    "JL Bourg": "JL Bourg-en-Bresse",
    "Cosea JL Bourg-en-Bresse": "JL Bourg-en-Bresse",
    "Veolia Towers Hamburg": "Veolia Towers Hamburg",
    "Hamburg Towers": "Veolia Towers Hamburg",
    "Ratiopharm Ulm": "Ratiopharm Ulm",
    "ratiopharm ulm": "Ratiopharm Ulm",
    "BV Chemnitz 99": "BV Chemnitz 99",
    "NINERS Chemnitz": "BV Chemnitz 99",
    "7Bet-Lietkabelis Panevezys": "7Bet-Lietkabelis Panevezys",
    "Lietkabelis Panevezys": "7Bet-Lietkabelis Panevezys",
    "U-Banca Transilvania Cluj Napoca": "U-Banca Transilvania Cluj Napoca",
    "U-BT Cluj-Napoca": "U-Banca Transilvania Cluj Napoca",
    "London Lions": "London Lions",
    "WKS Slask Wroclaw": "WKS Slask Wroclaw",
    "Slask Wroclaw": "WKS Slask Wroclaw",
    "Dolomiti Energia Trento": "Dolomiti Energia Trento",
    "ALBA Berlin": "ALBA Berlin",
    "Άλμπα": "ALBA Berlin",
}


def fold(value: str) -> str:
    """Lowercase, strip accents, and collapse punctuation for matching."""
    text = unicodedata.normalize("NFD", value or "")
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("ς", "σ").lower()
    text = text.replace("&", " ")
    text = re.sub(r"[^0-9a-zα-ω\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


ALIASES: dict[str, str] = {fold(key): name for key, name in _RAW_ALIASES.items()}


def _has_greek(text: str) -> bool:
    return any("α" <= char <= "ω" for char in fold(text))


GREEK_LABELS: dict[str, str] = {}
for _raw, _canonical in _RAW_ALIASES.items():
    if not _has_greek(_raw):
        continue
    _current = GREEK_LABELS.get(_canonical)
    if _current is None or len(_raw) > len(_current):
        GREEK_LABELS[_canonical] = _raw


def option_label(name: str) -> str:
    """Label used by the search box, including a Greek alias when we have one."""
    extra = GREEK_LABELS.get(name)
    if extra and fold(extra) != fold(name):
        return f"{name} · {extra}"
    return name


def canonical_team_name(name: str) -> str:
    """Return the display name shared across competitions."""
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    if not cleaned:
        return ""
    return ALIASES.get(fold(cleaned), cleaned)


def matching_names(query: str, names: list[str]) -> list[str]:
    """Filter team names by substring or by a known alias."""
    query = (query or "").strip()
    if not query:
        return list(names)
    key = fold(query)
    target = ALIASES.get(key)
    hits: list[str] = []
    for name in names:
        folded = fold(name)
        if key in folded or (target is not None and folded == fold(target)):
            hits.append(name)
    if target and target in names and target not in hits:
        hits.insert(0, target)
    return hits


def resolve_team_name(query: str, names: list[str]) -> str | None:
    """Pick one stored team name from a search query."""
    key = fold(query or "")
    if not key:
        return None
    target = ALIASES.get(key)
    if target and target in names:
        return target
    for name in names:
        if fold(name) == key:
            return name
    hits = matching_names(query, names)
    if len(hits) == 1:
        return hits[0]
    return None
