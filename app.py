"""Interactive browser for European basketball team averages."""

from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from database import (
    comparison_profile,
    dataset_summary,
    get_team_stats,
    init_db,
    list_cross_competition_teams,
    list_team_names,
    upsert_team_stats,
)
from export_web import write_payload
from names import option_label
from scraper import CURRENT_SEASON, LEAGUE_META, PREVIOUS_SEASON, scrape_all

UNAVAILABLE = "Μη διαθέσιμων στατιστικών"

st.set_page_config(
    page_title="Στατιστικά ομάδων",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SCOPE_LABELS = {
    "combined": "Ενιαίος μέσος",
    "europe": "Ευρώπη",
    "domestic": "Πρωτάθλημα",
    "regional": "Liga ABA",
}
SCOPE_COLORS = {
    "combined": "#f5b942",
    "europe": "#4c8dff",
    "domestic": "#3dbe86",
    "regional": "#e07a3d",
}
STAT_LABELS = {
    "ppg": "Πόντοι",
    "rpg": "Ριμπάουντ",
    "apg": "Ασίστ",
    "spg": "Κλεψίματα",
    "bpg": "Κοψίματα",
    "tov": "Λάθη",
    "pf": "Φάουλ",
    "orb": "Επιθ. ριμπ.",
    "drb": "Αμυν. ριμπ.",
    "fg_pct": "Εντός πεδιάς",
    "tp_pct": "Τρίποντα",
    "ft_pct": "Βολές",
    "mpg": "Λεπτά",
    "possessions": "Κατοχές",
    "off_rtg": "Επιθετικό rating",
    "def_rtg": "Αμυντικό rating",
    "net_rtg": "Καθαρό rating",
    "efg_pct": "eFG%",
    "ts_pct": "TS%",
}
RADAR_SCALES = {
    "ppg": (70, 102),
    "rpg": (28, 42),
    "apg": (14, 26),
    "spg": (4, 10),
    "bpg": (1.2, 4.5),
    "fg_pct": (0.42, 0.55),
    "tp_pct": (0.30, 0.42),
    "ft_pct": (0.68, 0.88),
}


def inject_css() -> None:
    st.markdown(
        """
        <style>
          .stApp {
            background:
              radial-gradient(1200px 500px at 10% -10%, rgba(245, 185, 66, 0.16), transparent 55%),
              radial-gradient(900px 420px at 100% 0%, rgba(76, 141, 255, 0.14), transparent 50%),
              #0b1020;
          }
          .block-container { padding-top: 1.4rem; max-width: 1180px; }
          h1, h2, h3 { letter-spacing: -0.03em; }
          div[data-testid="stMetric"] {
            background: rgba(20, 26, 46, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 0.7rem 0.9rem 0.4rem;
          }
          div[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
          .hero-kicker {
            color: #f5b942;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            margin-bottom: 0.2rem;
          }
          .team-title { font-size: 2.1rem; font-weight: 750; margin: 0.15rem 0 0.35rem; }
          .subtle { color: #a9b4cc; font-size: 0.95rem; }
          .pill {
            display: inline-block;
            margin: 0 0.4rem 0.4rem 0;
            padding: 0.28rem 0.7rem;
            border-radius: 999px;
            font-size: 0.82rem;
            font-weight: 650;
            border: 1px solid transparent;
          }
          .insight {
            background: rgba(245, 185, 66, 0.1);
            border: 1px solid rgba(245, 185, 66, 0.28);
            border-radius: 14px;
            padding: 0.8rem 1rem;
            color: #f3e2b8;
            margin: 0.4rem 0 0.8rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_when(value: str | None) -> str:
    if not value:
        return "ακόμη"
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.strftime("%d/%m/%Y %H:%M UTC")


def fmt_stat(key: str, value: object) -> str:
    if value is None:
        return "—"
    number = float(value)
    if key.endswith("_pct"):
        return f"{number * 100:.1f}%"
    if key == "gp":
        return f"{number:.0f}"
    return f"{number:.1f}"


def chart_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0, xanchor="left", font=dict(size=16)),
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e8edf7", family="Arial"),
        legend=dict(orientation="h", yanchor="top", y=-0.2, x=0),
        margin=dict(l=10, r=10, t=48, b=72),
        height=420,
        bargap=0.28,
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)", zeroline=False)
    return fig


def available_scopes(scopes: dict) -> list[tuple[str, dict]]:
    """Parts of the profile, plus the combined line when more than one exists."""
    parts = [key for key in ("europe", "regional", "domestic") if scopes.get(key)]
    order = parts + (["combined"] if len(parts) > 1 else [])
    if not order and scopes.get("combined"):
        order = ["combined"]
    return [(key, scopes[key]) for key in order]


def grouped_bars(
    scopes: dict,
    keys: list[str],
    title: str,
    as_percent: bool = False,
    show_zero: bool = False,
) -> go.Figure:
    fig = go.Figure()
    for key, block in available_scopes(scopes):
        values = []
        for stat in keys:
            raw = block.get(stat)
            if raw is None:
                values.append(None)
            else:
                values.append(float(raw) * 100 if as_percent else float(raw))
        fig.add_trace(
            go.Bar(
                name=SCOPE_LABELS[key],
                x=[STAT_LABELS[stat] for stat in keys],
                y=values,
                marker_color=SCOPE_COLORS[key],
                hovertemplate="%{y:.1f}<extra>%{fullData.name}</extra>",
            )
        )
    chart_layout(fig, title)
    if as_percent:
        fig.update_yaxes(ticksuffix="%")
    if show_zero:
        fig.update_yaxes(zeroline=True, zerolinecolor="rgba(255,255,255,0.28)")
    return fig


def scale_value(stat: str, value: float) -> float:
    low, high = RADAR_SCALES[stat]
    if high == low:
        return 0
    return max(0, min(100, (value - low) / (high - low) * 100))


def radar_chart(scopes: dict) -> go.Figure:
    stats = ["ppg", "rpg", "apg", "spg", "bpg", "fg_pct", "tp_pct", "ft_pct"]
    labels = [STAT_LABELS[stat] for stat in stats]
    fig = go.Figure()
    for key, block in available_scopes(scopes):
        if key == "combined" and any(scopes.get(other) for other in ("europe", "domestic", "regional")):
            continue
        radii = []
        custom = []
        for stat in stats:
            raw = block.get(stat)
            if raw is None:
                radii.append(0)
                custom.append("—")
            else:
                radii.append(scale_value(stat, float(raw)))
                custom.append(fmt_stat(stat, raw))
        fig.add_trace(
            go.Scatterpolar(
                r=radii + [radii[0]],
                theta=labels + [labels[0]],
                name=SCOPE_LABELS[key],
                fill="toself",
                line=dict(color=SCOPE_COLORS[key], width=2),
                customdata=custom + [custom[0]],
                hovertemplate="%{theta}: %{customdata}<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(
        title=dict(text="Προφίλ σε κοινή κλίμακα", x=0, xanchor="left"),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e8edf7"),
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0),
        margin=dict(l=40, r=40, t=56, b=64),
        height=430,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=False, range=[0, 100]),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)"),
        ),
    )
    return fig


def competition_table(competitions: list[dict]) -> pd.DataFrame:
    scope_names = {"europe": "Ευρώπη", "domestic": "Πρωτάθλημα", "regional": "Liga ABA"}
    records = []
    for row in competitions:
        records.append(
            {
                "Διοργάνωση": row["league_name"],
                "Κατηγορία": scope_names.get(row["scope"], row["scope"]),
                "Χώρα": row["country"],
                "Αγώνες": fmt_stat("gp", row["gp"]),
                "Πόντοι": fmt_stat("ppg", row["ppg"]),
                "Ριμπάουντ": fmt_stat("rpg", row["rpg"]),
                "Ασίστ": fmt_stat("apg", row["apg"]),
                "Εντός": fmt_stat("fg_pct", row["fg_pct"]),
                "Τρίποντα": fmt_stat("tp_pct", row["tp_pct"]),
                "Βολές": fmt_stat("ft_pct", row["ft_pct"]),
                "Κλεψίματα": fmt_stat("spg", row["spg"]),
                "Κοψίματα": fmt_stat("bpg", row["bpg"]),
                "Λάθη": fmt_stat("tov", row["tov"]),
                "Κατοχές": fmt_stat("possessions", row.get("possessions")),
                "Επιθετικό rating": fmt_stat("off_rtg", row.get("off_rtg")),
                "Αμυντικό rating": fmt_stat("def_rtg", row.get("def_rtg")),
                "Καθαρό rating": fmt_stat("net_rtg", row.get("net_rtg")),
                "eFG%": fmt_stat("efg_pct", row.get("efg_pct")),
                "TS%": fmt_stat("ts_pct", row.get("ts_pct")),
                "Πηγή": row["source_name"],
            }
        )
    return pd.DataFrame(records)


def scoring_insight(scopes: dict) -> str | None:
    europe = scopes.get("europe")
    domestic = scopes.get("domestic")
    if not europe or not domestic or europe.get("ppg") is None or domestic.get("ppg") is None:
        return None
    diff = float(domestic["ppg"]) - float(europe["ppg"])
    if abs(diff) < 0.15:
        return "Η παραγωγή πόντων στην Ευρώπη και στο πρωτάθλημα είναι σχεδόν ίδια."
    if diff > 0:
        return (
            f"Στο πρωτάθλημα σκοράρει {diff:.1f} πόντους περισσότερους ανά αγώνα "
            "από ό,τι στην Ευρώπη."
        )
    return (
        f"Στην Ευρώπη σκοράρει {abs(diff):.1f} πόντους περισσότερους ανά αγώνα "
        "από ό,τι στο πρωτάθλημα."
    )


def weight_sentence(scopes: dict) -> str:
    parts = [f"{float(scopes['combined']['gp']):.0f} αγώνες συνολικά"]
    for key, label in (
        ("europe", "στην Ευρώπη"),
        ("regional", "στη Liga ABA"),
        ("domestic", "στο πρωτάθλημα"),
    ):
        block = scopes.get(key)
        if block:
            parts.append(f"{float(block['gp']):.0f} {label}")
    return "Ο ενιαίος μέσος σταθμίζεται με τους αγώνες: " + ", ".join(parts) + "."


def render_refresh() -> None:
    if st.button("Ανανέωση Στατιστικών", type="primary", width="content"):
        progress = st.progress(0, text="Ξεκινά η άντληση πινάκων...")

        def on_progress(done: int, total: int, label: str) -> None:
            progress.progress(min(done / total, 1) if total else 1, text=label)

        try:
            frame, reports = scrape_all(on_progress)
            saved = upsert_team_stats(frame) if not frame.empty else 0
        except Exception as exc:  # noqa: BLE001 - show the failure in the page
            st.error(f"Η ανανέωση δεν ολοκληρώθηκε: {exc}")
            return
        try:
            write_payload()
        except Exception as exc:  # noqa: BLE001 - the database is already saved
            st.session_state["last_publish_error"] = str(exc)
            published = False
        else:
            st.session_state["last_publish_error"] = None
            published = True
        st.session_state["last_report"] = reports
        st.session_state["last_saved"] = saved
        st.session_state["last_published"] = published
        st.session_state.pop("team_choice", None)
        st.rerun()

    reports = st.session_state.get("last_report")
    if not reports:
        return
    saved = st.session_state.get("last_saved", 0)
    failed = [item["league"] for item in reports if not item.get("ok") and item.get("error")]
    empty = [item for item in reports if item.get("empty")]
    if saved:
        st.success(f"Αποθηκεύτηκαν {saved} γραμμές για τη σεζόν {CURRENT_SEASON}. Το site ενημερώθηκε από τη βάση.")
    elif empty and not failed:
        st.info(UNAVAILABLE)
        if st.session_state.get("last_published"):
            st.caption("Το site διαβάστηκε ξανά από τη βάση. Δεν προστέθηκαν αγώνες για τη σεζόν 2026-27.")
    elif failed:
        st.error("Δεν ενημερώθηκε καμία διοργάνωση. Τα προηγούμενα δεδομένα έμειναν ως έχουν.")
        if st.session_state.get("last_published"):
            st.caption("Το site έμεινε ίδιο με τη βάση, χωρίς νέες γραμμές.")
    if st.session_state.get("last_publish_error"):
        st.error("Η βάση ενημερώθηκε, αλλά το site δεν γράφτηκε: " + st.session_state["last_publish_error"])
    if failed:
        st.warning("Δεν διαβάστηκαν: " + ", ".join(failed))
    with st.expander("Λεπτομέρειες άντλησης"):
        for item in reports:
            if item.get("ok"):
                note = item.get("note") or ""
                st.write(f"✓ {item['league']}: {item.get('rows', 0)} ομάδες. {note}")
            elif item.get("error"):
                st.write(f"✕ {item['league']}: {item.get('error')}")
            elif item.get("note"):
                st.write(f"• {item['league']}: {item['note']}")


def render_team(profile: dict, *, show_title: bool = True) -> None:
    competitions = profile["competitions"]
    scopes = profile["scopes"]
    combined = scopes["combined"]

    if show_title:
        st.markdown(f"<div class='team-title'>{profile['team']}</div>", unsafe_allow_html=True)
    pills = []
    for row in competitions:
        color = SCOPE_COLORS.get(row["scope"], "#8892a8")
        pills.append(
            "<span class='pill' style='background:"
            f"{color}22;color:{color};border-color:{color}55'>"
            f"{row['league_name']} · {row['country']} · {float(row['gp']):.0f} αγ."
            "</span>"
        )
    st.markdown("".join(pills), unsafe_allow_html=True)
    st.markdown(
        f"<div class='subtle'>Σεζόν {competitions[0]['season']} · "
        f"ενημέρωση {format_when(str(profile['updated_at']))}</div>",
        unsafe_allow_html=True,
    )

    insight = scoring_insight(scopes)
    if insight:
        st.markdown(f"<div class='insight'>{insight}</div>", unsafe_allow_html=True)
    st.caption(weight_sentence(scopes))

    cards = [
        ("Πόντοι", "ppg"),
        ("Ριμπάουντ", "rpg"),
        ("Ασίστ", "apg"),
        ("Εντός πεδιάς", "fg_pct"),
        ("Τρίποντα", "tp_pct"),
        ("Βολές", "ft_pct"),
    ]
    for row_cards in (cards[:3], cards[3:]):
        columns = st.columns(3)
        for column, (label, key) in zip(columns, row_cards):
            column.metric(label, fmt_stat(key, combined.get(key)))

    st.caption("Προηγμένα")
    advanced_cards = [
        ("Κατοχές", "possessions"),
        ("Επιθετικό rating", "off_rtg"),
        ("Αμυντικό rating", "def_rtg"),
        ("Καθαρό rating", "net_rtg"),
        ("eFG%", "efg_pct"),
        ("TS%", "ts_pct"),
    ]
    for row_cards in (advanced_cards[:3], advanced_cards[3:]):
        columns = st.columns(3)
        for column, (label, key) in zip(columns, row_cards):
            column.metric(label, fmt_stat(key, combined.get(key)))
    if combined.get("off_rtg") is not None and combined.get("def_rtg") is None:
        st.caption("Το αμυντικό και το καθαρό rating εμφανίζονται όπου υπάρχουν πόντοι αντιπάλου.")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            grouped_bars(scopes, ["ppg", "rpg", "apg", "spg", "bpg"], "Παραγωγή ανά αγώνα"),
            width="stretch",
        )
    with right:
        st.plotly_chart(
            grouped_bars(scopes, ["fg_pct", "tp_pct", "ft_pct"], "Ποσοστά σουτ", as_percent=True),
            width="stretch",
        )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(radar_chart(scopes), width="stretch")
    with right:
        st.plotly_chart(
            grouped_bars(scopes, ["orb", "drb", "tov", "pf"], "Ριμπάουντ, λάθη και φάουλ"),
            width="stretch",
        )

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            grouped_bars(
                scopes,
                ["off_rtg", "def_rtg", "net_rtg"],
                "Rating ανά 100 κατοχές",
                show_zero=True,
            ),
            width="stretch",
        )
    with right:
        st.plotly_chart(
            grouped_bars(scopes, ["efg_pct", "ts_pct"], "eFG% και TS%", as_percent=True),
            width="stretch",
        )
    st.plotly_chart(
        grouped_bars(scopes, ["possessions"], "Κατοχές ανά αγώνα"),
        width="stretch",
    )

    st.subheader("Ανα διοργάνωση")
    st.dataframe(competition_table(competitions), width="stretch", hide_index=True)


def main() -> None:
    if st.session_state.get("pending_team"):
        pending = st.session_state.pop("pending_team")
        st.session_state["team_choice"] = option_label(pending)
        st.session_state["cross_picks"] = None

    inject_css()
    init_db()
    summary = dataset_summary()

    title_col, action_col = st.columns([4, 1.3])
    with title_col:
        st.markdown("<div class='hero-kicker'>EuroLeague · EuroCup · εγχώρια</div>", unsafe_allow_html=True)
        st.title("Στατιστικά ομάδων")
        st.markdown(
            "<div class='subtle'>Η ανανέωση διαβάζει τη σεζόν 2026-27. "
            "Ο ενιαίος μέσος σταθμίζεται μόνο μέσα σε αυτή τη σεζόν. "
            "Η περσινή αντίστοιχη αγωνιστική μένει χωριστή επιλογή και δεν μπαίνει στον μέσο όρο.</div>",
            unsafe_allow_html=True,
        )
    with action_col:
        st.write("")
        render_refresh()

    st.caption(
        f"Σεζόν {CURRENT_SEASON}: {summary['current_rows']} γραμμές · "
        f"αποθηκευμένη σεζόν {PREVIOUS_SEASON}: {summary['previous_rows']} γραμμές · "
        f"τελευταία αποθήκευση {format_when(summary['refreshed_at'])}"
    )

    if summary["teams"] == 0:
        st.info("Η βάση είναι άδεια. Πάτησε «Ανανέωση Στατιστικών» για να διαβαστούν οι πίνακες.")
        return

    names = list_team_names()
    labels = {option_label(name): name for name in names}
    options = list(labels)
    if "team_choice" in st.session_state and st.session_state["team_choice"] not in options:
        st.session_state.pop("team_choice", None)

    select_kwargs = {}
    if "team_choice" not in st.session_state:
        select_kwargs["index"] = None
    selected_label = st.selectbox(
        "Αναζήτηση ομάδας",
        options,
        placeholder="π.χ. Ολυμπιακός, Real Madrid, Partizan",
        key="team_choice",
        **select_kwargs,
    )
    selected = labels.get(selected_label) if selected_label else None

    if not selected:
        picks = list_cross_competition_teams(PREVIOUS_SEASON)
        if picks:
            picked = st.pills(
                "Ομάδες με Ευρώπη και πρωτάθλημα τη σεζόν 2025-26",
                picks,
                selection_mode="single",
                key="cross_picks",
                wrap=True,
            )
            if picked and option_label(picked) != st.session_state.get("team_choice"):
                st.session_state["pending_team"] = picked
                st.rerun()

    if not selected:
        if summary["current_rows"] == 0:
            st.info(UNAVAILABLE)
        st.markdown(
            "<div class='subtle'>Διάλεξε ομάδα για να δεις την κάρτα με τους μέσους όρους "
            "και τα γραφήματα.</div>",
            unsafe_allow_html=True,
        )
        return

    st.markdown(f"<div class='team-title'>{selected}</div>", unsafe_allow_html=True)
    st.subheader(f"Σεζόν {CURRENT_SEASON}")
    current = get_team_stats(selected, CURRENT_SEASON)
    if current is None:
        st.info(UNAVAILABLE)
    else:
        render_team(current, show_title=False)

    show_previous = st.toggle(
        f"Εμφάνιση στατιστικών αντίστοιχης αγωνιστικής {PREVIOUS_SEASON}",
        key="show_previous_round",
    )
    if not show_previous:
        return

    limits = {}
    if current is not None:
        limits = {
            row["league_code"]: int(float(row["gp"] or 0))
            for row in current["competitions"]
        }
    if not any(limits.values()):
        st.info(UNAVAILABLE)
        return

    previous = comparison_profile(selected, limits, PREVIOUS_SEASON)
    if previous is None:
        st.info(UNAVAILABLE)
        return
    st.subheader(f"Σεζόν {PREVIOUS_SEASON} · αντίστοιχη αγωνιστική")
    st.caption(
        "Μέσοι όροι μόνο από τους πρώτους αγώνες της περσινής σεζόν, "
        "όσους έχει δώσει η ομάδα φέτος σε κάθε διοργάνωση. "
        "Δεν προστίθενται στον μέσο όρο του 2026-27."
    )
    render_team(previous, show_title=False)
    missing = previous.get("missing_leagues") or []
    if missing:
        labels = [LEAGUE_META[code]["league_name"] for code in missing if code in LEAGUE_META]
        if labels:
            st.caption("Χωρίς αρχείο αγώνα-αγώνα για: " + ", ".join(labels) + ".")


if __name__ == "__main__":
    main()
