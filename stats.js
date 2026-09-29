const I18N = {
  el: {
    title: "Στατιστικά ομάδων",
    kicker: "EuroLeague · EuroCup · εγχώρια",
    intro: "Η σελίδα δείχνει τη σεζόν 2026-27. Ο ενιαίος μέσος σταθμίζεται μόνο μέσα σε αυτή τη σεζόν. Η περσινή αντίστοιχη αγωνιστική μένει χωριστή επιλογή.",
    back: "Πίσω στο site",
    search: "Αναζήτηση ομάδας",
    placeholder: "π.χ. Ολυμπιακός, Real Madrid, Partizan",
    unavailable: "Μη διαθέσιμων στατιστικών",
    hint: "Διάλεξε ομάδα για να δεις την κάρτα με τους μέσους όρους και τα γραφήματα.",
    cross: "Ομάδες με Ευρώπη και πρωτάθλημα τη σεζόν 2025-26",
    previous: "Εμφάνιση στατιστικών αντίστοιχης αγωνιστικής 2025-26",
    loadError: "Τα στατιστικά δεν φορτώθηκαν. Άνοιξε τη σελίδα από το site, όχι ως μεμονωμένο αρχείο.",
    notYet: "ακόμη",
    advanced: "Προηγμένα",
    byCompetition: "Ανα διοργάνωση",
    gamesShort: "αγ.",
    sameRound: (season) => `Σεζόν ${season} · αντίστοιχη αγωνιστική`,
    seasonHeading: (season) => `Σεζόν ${season}`,
    seasonLine: (season, when) => `Σεζόν ${season} · ενημέρωση ${when}`,
    summary: (data, when) => `Σεζόν ${data.current_season}: ${data.current_rows} γραμμές · αποθηκευμένη σεζόν ${data.previous_season}: ${data.previous_rows} γραμμές · τελευταία αποθήκευση ${when}`,
    previousNote: "Μέσοι όροι μόνο από τους πρώτους αγώνες της περσινής σεζόν, όσους έχει δώσει η ομάδα φέτος σε κάθε διοργάνωση. Δεν προστίθενται στον μέσο όρο του 2026-27.",
    missingLogs: (names) => `Χωρίς αρχείο αγώνα-αγώνα για: ${names}.`,
    ratingGap: "Το αμυντικό και το καθαρό rating εμφανίζονται όπου υπάρχουν πόντοι αντιπάλου.",
    insightSame: "Η παραγωγή πόντων στην Ευρώπη και στο πρωτάθλημα είναι σχεδόν ίδια.",
    insightDomestic: (diff) => `Στο πρωτάθλημα σκοράρει ${diff} πόντους περισσότερους ανά αγώνα από ό,τι στην Ευρώπη.`,
    insightEurope: (diff) => `Στην Ευρώπη σκοράρει ${diff} πόντους περισσότερους ανά αγώνα από ό,τι στο πρωτάθλημα.`,
    weight: (parts) => `Ο ενιαίος μέσος σταθμίζεται με τους αγώνες: ${parts.join(", ")}.`,
    weightTotal: (games) => `${games} αγώνες συνολικά`,
    weightEurope: (games) => `${games} στην Ευρώπη`,
    weightRegional: (games) => `${games} στη Liga ABA`,
    weightDomestic: (games) => `${games} στο πρωτάθλημα`,
    charts: {
      production: "Παραγωγή ανά αγώνα",
      shooting: "Ποσοστά σουτ",
      radar: "Προφίλ σε κοινή κλίμακα",
      extras: "Ριμπάουντ, λάθη και φάουλ",
      ratings: "Rating ανά 100 κατοχές",
      efficiency: "eFG% και TS%",
      possessions: "Κατοχές ανά αγώνα",
    },
    columns: ["Διοργάνωση", "Κατηγορία", "Χώρα", "Αγώνες", "Πόντοι", "Ριμπάουντ", "Ασίστ", "Εντός", "Τρίποντα", "Βολές", "Κατοχές", "Επιθ. rating", "Αμυν. rating", "Καθαρό rating", "eFG%", "TS%"],
    scopes: { combined: "Ενιαίος μέσος", europe: "Ευρώπη", domestic: "Πρωτάθλημα", regional: "Liga ABA" },
    scopeTable: { europe: "Ευρώπη", domestic: "Πρωτάθλημα", regional: "Liga ABA" },
    stats: {
      ppg: "Πόντοι", rpg: "Ριμπάουντ", apg: "Ασίστ", spg: "Κλεψίματα", bpg: "Κοψίματα", tov: "Λάθη", pf: "Φάουλ",
      orb: "Επιθ. ριμπ.", drb: "Αμυν. ριμπ.", fg_pct: "Εντός πεδιάς", tp_pct: "Τρίποντα", ft_pct: "Βολές", mpg: "Λεπτά",
      possessions: "Κατοχές", off_rtg: "Επιθετικό rating", def_rtg: "Αμυντικό rating", net_rtg: "Καθαρό rating", efg_pct: "eFG%", ts_pct: "TS%",
    },
    countries: {},
  },
  en: {
    title: "Team statistics",
    kicker: "EuroLeague · EuroCup · domestic",
    intro: "The page shows the 2026-27 season. The combined average is weighted only within that season. Last year's matching round stays a separate option.",
    back: "Back to the site",
    search: "Search for a team",
    placeholder: "e.g. Olympiacos, Real Madrid, Partizan",
    unavailable: "No statistics available",
    hint: "Pick a team to see the averages and the charts.",
    cross: "Teams with Europe and a domestic league in 2025-26",
    previous: "Show 2025-26 stats through the same round",
    loadError: "Statistics did not load. Open the page from the site, not as a standalone file.",
    notYet: "not yet",
    advanced: "Advanced",
    byCompetition: "By competition",
    gamesShort: "GP",
    sameRound: (season) => `Season ${season} · same round`,
    seasonHeading: (season) => `Season ${season}`,
    seasonLine: (season, when) => `Season ${season} · updated ${when}`,
    summary: (data, when) => `Season ${data.current_season}: ${data.current_rows} rows · stored season ${data.previous_season}: ${data.previous_rows} rows · last save ${when}`,
    previousNote: "Averages only from the first games of last season, as many as the team has played this year in each competition. They are not added to the 2026-27 average.",
    missingLogs: (names) => `No game-by-game log for: ${names}.`,
    ratingGap: "Defensive and net rating appear where opponent points are available.",
    insightSame: "Scoring in Europe and in the domestic league is almost the same.",
    insightDomestic: (diff) => `The domestic league scores ${diff} more points per game than Europe.`,
    insightEurope: (diff) => `Europe scores ${diff} more points per game than the domestic league.`,
    weight: (parts) => `The combined average is weighted by games: ${parts.join(", ")}.`,
    weightTotal: (games) => `${games} games overall`,
    weightEurope: (games) => `${games} in Europe`,
    weightRegional: (games) => `${games} in Liga ABA`,
    weightDomestic: (games) => `${games} in the domestic league`,
    charts: {
      production: "Production per game",
      shooting: "Shooting percentages",
      radar: "Profile on a common scale",
      extras: "Rebounds, turnovers and fouls",
      ratings: "Rating per 100 possessions",
      efficiency: "eFG% and TS%",
      possessions: "Possessions per game",
    },
    columns: ["Competition", "Category", "Country", "Games", "Points", "Rebounds", "Assists", "FG", "Threes", "Free throws", "Possessions", "Off. rating", "Def. rating", "Net rating", "eFG%", "TS%"],
    scopes: { combined: "Combined average", europe: "Europe", domestic: "Domestic", regional: "Liga ABA" },
    scopeTable: { europe: "Europe", domestic: "Domestic", regional: "Liga ABA" },
    stats: {
      ppg: "Points", rpg: "Rebounds", apg: "Assists", spg: "Steals", bpg: "Blocks", tov: "Turnovers", pf: "Fouls",
      orb: "Off. reb.", drb: "Def. reb.", fg_pct: "Field goals", tp_pct: "Three-pointers", ft_pct: "Free throws", mpg: "Minutes",
      possessions: "Possessions", off_rtg: "Offensive rating", def_rtg: "Defensive rating", net_rtg: "Net rating", efg_pct: "eFG%", ts_pct: "TS%",
    },
    countries: {
      "Ευρώπη": "Europe",
      "Αδριατική": "Adriatic",
      "Ισπανία": "Spain",
      "Ελλάδα": "Greece",
      "Τουρκία": "Turkey",
      "Ισραήλ": "Israel",
      "Ιταλία": "Italy",
      "Γαλλία": "France",
      "Γερμανία": "Germany",
      "Λιθουανία": "Lithuania",
    },
  },
};

let lang = "en";
try {
  const queryLang = typeof window === "undefined" ? null : new URLSearchParams(window.location.search).get("lang");
  const stored = localStorage.getItem("stats-lang");
  const preferred = queryLang || stored;
  if (preferred === "el" || preferred === "en") lang = preferred;
} catch (error) {
  lang = "en";
}

function copy() {
  return I18N[lang];
}

function statLabel(key) {
  return copy().stats[key] || key;
}

function scopeLabel(key) {
  return copy().scopes[key] || key;
}

function countryName(name) {
  return copy().countries[name] || name;
}

const SCOPE_COLORS = {
  combined: "#f5b942",
  europe: "#4c8dff",
  domestic: "#3dbe86",
  regional: "#e07a3d",
};
const RADAR_SCALES = {
  ppg: [70, 102],
  rpg: [28, 42],
  apg: [14, 26],
  spg: [4, 10],
  bpg: [1.2, 4.5],
  fg_pct: [0.42, 0.55],
  tp_pct: [0.3, 0.42],
  ft_pct: [0.68, 0.88],
};
const SCOPE_ORDER = { europe: 0, regional: 1, domestic: 2 };

function fold(value) {
  let text = (value || "").normalize("NFD").replace(/\p{M}/gu, "");
  text = text.replace(/ς/g, "σ").toLowerCase().replace(/&/g, " ");
  text = text.replace(/[^0-9a-zα-ω\s]/g, " ");
  return text.replace(/\s+/g, " ").trim();
}

function fmt(key, value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  const number = Number(value);
  if (key.endsWith("_pct")) return `${(number * 100).toFixed(1)}%`;
  if (key === "gp") return `${Math.round(number)}`;
  return number.toFixed(1);
}

function formatWhen(value) {
  if (!value) return copy().notYet;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(parsed.getUTCDate())}/${pad(parsed.getUTCMonth() + 1)}/${parsed.getUTCFullYear()} ${pad(parsed.getUTCHours())}:${pad(parsed.getUTCMinutes())} UTC`;
}

function num(value) {
  if (value == null || value === "" || Number.isNaN(Number(value))) return null;
  return Number(value);
}

function applyAdvanced(row) {
  const fga = num(row.fga);
  const orb = num(row.orb);
  const tov = num(row.tov);
  const fta = num(row.fta);
  const points = num(row.ppg);
  const allowed = num(row.opp_ppg);
  const poss = [fga, orb, tov, fta].some((value) => value == null)
    ? null
    : 0.96 * (fga - orb + tov + 0.44 * fta);
  const rate = (scored, possessions) => {
    if (scored == null || possessions == null || possessions === 0) return null;
    return (scored * 100) / possessions;
  };
  row.possessions = poss;
  row.off_rtg = rate(points, poss);
  row.def_rtg = rate(allowed, poss);
  row.net_rtg = row.off_rtg == null || row.def_rtg == null ? null : row.off_rtg - row.def_rtg;
  const fgm = num(row.fgm);
  const tpm = num(row.tpm);
  row.efg_pct = fga && fgm != null && tpm != null ? (fgm + 0.5 * tpm) / fga : null;
  const denominator = fga == null || fta == null ? null : 2 * (fga + 0.44 * fta);
  row.ts_pct = points == null || !denominator ? null : points / denominator;
  return row;
}

function weightedPercent(rows, madeKey, attemptedKey, percentKey) {
  let made = 0;
  let attempted = 0;
  let saw = false;
  rows.forEach((row) => {
    const games = Number(row.gp || 0);
    if (row[madeKey] == null || row[attemptedKey] == null) return;
    saw = true;
    made += Number(row[madeKey]) * games;
    attempted += Number(row[attemptedKey]) * games;
  });
  if (saw && attempted > 0) return made / attempted;
  let weighted = 0;
  let weight = 0;
  rows.forEach((row) => {
    if (row[percentKey] == null) return;
    const games = Number(row.gp || 0);
    weighted += Number(row[percentKey]) * games;
    weight += games;
  });
  return weight > 0 ? weighted / weight : null;
}

function weighted(rows) {
  const games = rows.reduce((sum, row) => sum + Number(row.gp || 0), 0);
  const summary = { gp: games, competitions: rows.length };
  const counting = ["mpg", "ppg", "fgm", "fga", "tpm", "tpa", "ftm", "fta", "orb", "drb", "rpg", "apg", "spg", "bpg", "tov", "pf"];
  if (games <= 0) {
    counting.forEach((field) => {
      summary[field] = null;
    });
    summary.fg_pct = summary.tp_pct = summary.ft_pct = null;
    summary.opp_ppg = null;
    return applyAdvanced(summary);
  }
  counting.forEach((field) => {
    let total = 0;
    let weight = 0;
    rows.forEach((row) => {
      if (row[field] == null) return;
      const rowGames = Number(row.gp || 0);
      total += Number(row[field]) * rowGames;
      weight += rowGames;
    });
    summary[field] = weight ? total / weight : null;
  });
  summary.fg_pct = weightedPercent(rows, "fgm", "fga", "fg_pct");
  summary.tp_pct = weightedPercent(rows, "tpm", "tpa", "tp_pct");
  summary.ft_pct = weightedPercent(rows, "ftm", "fta", "ft_pct");
  if (rows.every((row) => row.opp_ppg != null)) {
    let total = 0;
    let weight = 0;
    rows.forEach((row) => {
      const rowGames = Number(row.gp || 0);
      total += Number(row.opp_ppg) * rowGames;
      weight += rowGames;
    });
    summary.opp_ppg = weight ? total / weight : null;
  } else {
    summary.opp_ppg = null;
  }
  return applyAdvanced(summary);
}

function scopesFrom(competitions) {
  const has = (scope) => competitions.some((row) => row.scope === scope);
  return {
    combined: weighted(competitions),
    europe: has("europe") ? weighted(competitions.filter((row) => row.scope === "europe")) : null,
    domestic: has("domestic") ? weighted(competitions.filter((row) => row.scope === "domestic")) : null,
    regional: has("regional") ? weighted(competitions.filter((row) => row.scope === "regional")) : null,
  };
}

function availableScopes(scopes) {
  const parts = ["europe", "regional", "domestic"].filter((key) => scopes[key]);
  const order = parts.concat(parts.length > 1 ? ["combined"] : []);
  if (!order.length && scopes.combined) order.push("combined");
  return order.map((key) => [key, scopes[key]]);
}

function logRow(fields, values) {
  const row = {};
  fields.forEach((field, index) => {
    row[field] = values[index];
  });
  return row;
}

function averageLogs(rows, leagueCode, season, leagues) {
  const meta = leagues[leagueCode];
  const count = rows.length;
  const total = (key) => rows.reduce((sum, row) => sum + Number(row[key] || 0), 0);
  const ratio = (made, attempted) => (total(attempted) > 0 ? total(made) / total(attempted) : null);
  const line = {
    league_code: leagueCode,
    league_name: meta.league_name,
    scope: meta.scope,
    country: meta.country,
    season,
    source_name: "Αρχείο αγώνων",
    gp: count,
    mpg: total("minutes") / count,
    ppg: total("points") / count,
    fgm: total("fgm") / count,
    fga: total("fga") / count,
    fg_pct: ratio("fgm", "fga"),
    tpm: total("tpm") / count,
    tpa: total("tpa") / count,
    tp_pct: ratio("tpm", "tpa"),
    ftm: total("ftm") / count,
    fta: total("fta") / count,
    ft_pct: ratio("ftm", "fta"),
    orb: total("orb") / count,
    drb: total("drb") / count,
    rpg: total("reb") / count,
    apg: total("ast") / count,
    spg: total("stl") / count,
    bpg: total("blk") / count,
    tov: total("tov") / count,
    pf: total("pf") / count,
    opp_ppg: rows.every((row) => row.points_allowed != null)
      ? rows.reduce((sum, row) => sum + Number(row.points_allowed), 0) / count
      : null,
  };
  return applyAdvanced(line);
}

function comparisonProfile(team, limits, data) {
  const positive = Object.entries(limits).filter(([, games]) => Number(games) > 0);
  if (!positive.length) return null;
  const competitions = [];
  const missing = [];
  positive.forEach(([code, gamesPlayed]) => {
    const games = Number(gamesPlayed);
    if (!data.leagues[code]) {
      missing.push(code);
      return;
    }
    const stored = (team.logs[code] || []).map((values) => logRow(data.log_fields, values));
    const seasonGp = team.previous_gp[code];
    if (seasonGp != null && stored.length < Number(seasonGp)) {
      missing.push(code);
      return;
    }
    const rows = stored.filter((row) => Number(row.game_index) <= games);
    if (rows.length < games) {
      missing.push(code);
      return;
    }
    competitions.push(averageLogs(rows, code, data.previous_season, data.leagues));
  });
  if (!competitions.length) return null;
  competitions.sort((a, b) => (SCOPE_ORDER[a.scope] ?? 9) - (SCOPE_ORDER[b.scope] ?? 9) || a.league_name.localeCompare(b.league_name));
  return {
    team: team.name,
    season: data.previous_season,
    updated_at: "",
    competitions,
    scopes: scopesFrom(competitions),
    missing_leagues: missing,
  };
}

function scoringInsight(scopes) {
  const europe = scopes.europe;
  const domestic = scopes.domestic;
  const strings = copy();
  if (!europe || !domestic || europe.ppg == null || domestic.ppg == null) return null;
  const diff = Number(domestic.ppg) - Number(europe.ppg);
  if (Math.abs(diff) < 0.15) return strings.insightSame;
  if (diff > 0) return strings.insightDomestic(diff.toFixed(1));
  return strings.insightEurope(Math.abs(diff).toFixed(1));
}

function weightSentence(scopes) {
  const strings = copy();
  const games = Number(scopes.combined.gp).toFixed(0);
  const parts = [strings.weightTotal(games)];
  if (scopes.europe) parts.push(strings.weightEurope(Number(scopes.europe.gp).toFixed(0)));
  if (scopes.regional) parts.push(strings.weightRegional(Number(scopes.regional.gp).toFixed(0)));
  if (scopes.domestic) parts.push(strings.weightDomestic(Number(scopes.domestic.gp).toFixed(0)));
  return strings.weight(parts);
}

function chartLayout(title) {
  return {
    title: { text: title, x: 0, xanchor: "left", font: { size: 16 } },
    barmode: "group",
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: "#e8edf7", family: "Arial" },
    legend: { orientation: "h", yanchor: "top", y: -0.2, x: 0 },
    margin: { l: 40, r: 16, t: 48, b: 72 },
    height: 420,
    bargap: 0.28,
    xaxis: { showgrid: false },
    yaxis: { gridcolor: "rgba(255,255,255,0.06)", zeroline: false },
  };
}

function groupedBars(scopes, keys, title, asPercent, showZero) {
  const traces = availableScopes(scopes).map(([key, block]) => ({
    type: "bar",
    name: scopeLabel(key),
    x: keys.map((stat) => statLabel(stat)),
    y: keys.map((stat) => (block[stat] == null ? null : asPercent ? Number(block[stat]) * 100 : Number(block[stat]))),
    marker: { color: SCOPE_COLORS[key] },
    hovertemplate: "%{y:.1f}<extra>%{fullData.name}</extra>",
  }));
  const layout = chartLayout(title);
  if (asPercent) layout.yaxis.ticksuffix = "%";
  if (showZero) layout.yaxis.zeroline = true;
  return { data: traces, layout };
}

function radarChart(scopes) {
  const stats = ["ppg", "rpg", "apg", "spg", "bpg", "fg_pct", "tp_pct", "ft_pct"];
  const labels = stats.map((stat) => statLabel(stat));
  const traces = [];
  availableScopes(scopes).forEach(([key, block]) => {
    if (key === "combined" && ["europe", "domestic", "regional"].some((other) => scopes[other])) return;
    const radii = [];
    const custom = [];
    stats.forEach((stat) => {
      const raw = block[stat];
      if (raw == null) {
        radii.push(0);
        custom.push("—");
      } else {
        const [low, high] = RADAR_SCALES[stat];
        radii.push(Math.max(0, Math.min(100, ((Number(raw) - low) / (high - low)) * 100)));
        custom.push(fmt(stat, raw));
      }
    });
    traces.push({
      type: "scatterpolar",
      r: radii.concat(radii[0]),
      theta: labels.concat(labels[0]),
      name: scopeLabel(key),
      fill: "toself",
      line: { color: SCOPE_COLORS[key], width: 2 },
      customdata: custom.concat(custom[0]),
      hovertemplate: "%{theta}: %{customdata}<extra>%{fullData.name}</extra>",
    });
  });
  return {
    data: traces,
    layout: {
      title: { text: copy().charts.radar, x: 0, xanchor: "left" },
      paper_bgcolor: "rgba(0,0,0,0)",
      font: { color: "#e8edf7" },
      legend: { orientation: "h", yanchor: "top", y: -0.12, x: 0 },
      margin: { l: 40, r: 40, t: 56, b: 64 },
      height: 430,
      polar: {
        bgcolor: "rgba(0,0,0,0)",
        radialaxis: { visible: false, range: [0, 100] },
        angularaxis: { gridcolor: "rgba(255,255,255,0.08)" },
      },
    },
  };
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function renderProfile(mount, profile, data, showTitle) {
  mount.replaceChildren();
  if (showTitle) mount.append(el("h2", "team-title", profile.team));
  const pills = el("div", "pills");
  const strings = copy();
  profile.competitions.forEach((row) => {
    const color = SCOPE_COLORS[row.scope] || "#8892a8";
    const pill = el("span", "pill", `${row.league_name} · ${countryName(row.country)} · ${Number(row.gp).toFixed(0)} ${strings.gamesShort}`);
    pill.style.background = `${color}22`;
    pill.style.color = color;
    pill.style.borderColor = `${color}55`;
    pills.append(pill);
  });
  mount.append(pills);
  mount.append(el("p", "subtle", strings.seasonLine(profile.competitions[0].season, formatWhen(profile.updated_at))));
  const insight = scoringInsight(profile.scopes);
  if (insight) mount.append(el("div", "insight", insight));
  mount.append(el("p", "caption", weightSentence(profile.scopes)));

  const metrics = el("div", "metrics");
  ["ppg", "rpg", "apg", "fg_pct", "tp_pct", "ft_pct"].forEach((key) => {
    const card = el("div", "metric");
    card.append(el("span", "metric-label", statLabel(key)));
    card.append(el("strong", "metric-value", fmt(key, profile.scopes.combined[key])));
    metrics.append(card);
  });
  mount.append(metrics);
  mount.append(el("p", "caption", strings.advanced));
  const advanced = el("div", "metrics");
  ["possessions", "off_rtg", "def_rtg", "net_rtg", "efg_pct", "ts_pct"].forEach((key) => {
    const card = el("div", "metric");
    card.append(el("span", "metric-label", statLabel(key)));
    card.append(el("strong", "metric-value", fmt(key, profile.scopes.combined[key])));
    advanced.append(card);
  });
  mount.append(advanced);
  if (profile.scopes.combined.off_rtg != null && profile.scopes.combined.def_rtg == null) {
    mount.append(el("p", "caption", strings.ratingGap));
  }

  const charts = el("div", "charts");
  const titles = strings.charts;
  [
    groupedBars(profile.scopes, ["ppg", "rpg", "apg", "spg", "bpg"], titles.production, false),
    groupedBars(profile.scopes, ["fg_pct", "tp_pct", "ft_pct"], titles.shooting, true),
    radarChart(profile.scopes),
    groupedBars(profile.scopes, ["orb", "drb", "tov", "pf"], titles.extras, false),
    groupedBars(profile.scopes, ["off_rtg", "def_rtg", "net_rtg"], titles.ratings, false, true),
    groupedBars(profile.scopes, ["efg_pct", "ts_pct"], titles.efficiency, true),
    groupedBars(profile.scopes, ["possessions"], titles.possessions, false),
  ].forEach((figure) => {
    const box = el("div", "chart");
    charts.append(box);
    window.Plotly.newPlot(box, figure.data, figure.layout, { displayModeBar: false, responsive: true });
  });
  mount.append(charts);

  mount.append(el("h3", "section", strings.byCompetition));
  const table = document.createElement("table");
  const head = document.createElement("tr");
  strings.columns.forEach((label) => {
    const cell = document.createElement("th");
    cell.textContent = label;
    head.append(cell);
  });
  table.append(head);
  const scopeNames = strings.scopeTable;
  profile.competitions.forEach((row) => {
    const line = document.createElement("tr");
    [row.league_name, scopeNames[row.scope] || row.scope, countryName(row.country), fmt("gp", row.gp), fmt("ppg", row.ppg), fmt("rpg", row.rpg), fmt("apg", row.apg), fmt("fg_pct", row.fg_pct), fmt("tp_pct", row.tp_pct), fmt("ft_pct", row.ft_pct), fmt("possessions", row.possessions), fmt("off_rtg", row.off_rtg), fmt("def_rtg", row.def_rtg), fmt("net_rtg", row.net_rtg), fmt("efg_pct", row.efg_pct), fmt("ts_pct", row.ts_pct)].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      line.append(cell);
    });
    table.append(line);
  });
  const wrap = el("div", "table-wrap");
  wrap.append(table);
  mount.append(wrap);
}

function boot(data) {
  const search = document.querySelector("#team-search");
  const results = document.querySelector("#team-results");
  const currentMount = document.querySelector("#current-season");
  const previousMount = document.querySelector("#previous-season");
  const toggle = document.querySelector("#show-previous");
  const empty = document.querySelector("#empty-state");
  const cross = document.querySelector("#cross-picks");
  const caption = document.querySelector("#summary");

  let selected = null;

  function applyChrome() {
    const strings = copy();
    document.documentElement.lang = lang;
    document.title = strings.title;
    document.querySelector("#kicker").textContent = strings.kicker;
    document.querySelector("#page-title").textContent = strings.title;
    document.querySelector("#intro").textContent = strings.intro;
    document.querySelector("#back-link").textContent = strings.back;
    document.querySelector("#search-label").textContent = strings.search;
    search.placeholder = strings.placeholder;
    document.querySelector("#load-error").textContent = strings.loadError;
    empty.textContent = strings.unavailable;
    document.querySelector("#pick-hint").textContent = strings.hint;
    cross.setAttribute("aria-label", strings.cross);
    document.querySelector("#previous-label").textContent = strings.previous;
    caption.textContent = strings.summary(data, formatWhen(data.refreshed_at));
    document.querySelectorAll(".lang-switch button").forEach((button) => {
      button.setAttribute("aria-pressed", button.dataset.lang === lang ? "true" : "false");
    });
  }
  const params = new URLSearchParams(window.location.search);
  const requested = params.get("team");

  function matches(query) {
    const key = fold(query);
    if (!key) return [];
    return data.teams.filter((team) => team.search.includes(key) || fold(team.label).includes(key)).slice(0, 8);
  }

  function showResults(query) {
    results.replaceChildren();
    matches(query).forEach((team) => {
      const button = el("button", "result", team.label);
      button.type = "button";
      button.addEventListener("click", () => choose(team));
      results.append(button);
    });
  }

  function choose(team) {
    selected = team;
    search.value = team.label;
    results.replaceChildren();
    empty.hidden = true;
    cross.hidden = true;
    document.querySelector("#pick-hint").hidden = true;
    currentMount.replaceChildren();
    currentMount.append(el("h2", "team-title", team.name));
    currentMount.append(el("h3", "section", copy().seasonHeading(data.current_season)));
    if (!team.current) {
      currentMount.append(el("div", "notice", copy().unavailable));
    } else {
      const card = el("div");
      renderProfile(card, team.current, data, false);
      currentMount.append(card);
    }
    renderPrevious();
  }

  function renderPrevious() {
    previousMount.replaceChildren();
    if (!selected || !toggle.checked) return;
    const limits = {};
    if (selected.current) {
      selected.current.competitions.forEach((row) => {
        limits[row.league_code] = Number(row.gp || 0);
      });
    }
    if (!Object.values(limits).some((games) => games > 0)) {
      previousMount.append(el("div", "notice", copy().unavailable));
      return;
    }
    const previous = comparisonProfile(selected, limits, data);
    if (!previous) {
      previousMount.append(el("div", "notice", copy().unavailable));
      return;
    }
    previousMount.append(el("h3", "section", copy().sameRound(data.previous_season)));
    previousMount.append(el("p", "caption", copy().previousNote));
    const card = el("div");
    renderProfile(card, previous, data, false);
    previousMount.append(card);
    const missing = (previous.missing_leagues || []).map((code) => data.leagues[code]?.league_name).filter(Boolean);
    if (missing.length) previousMount.append(el("p", "caption", copy().missingLogs(missing.join(", "))));
  }

  function setLanguage(next) {
    if (next !== "el" && next !== "en") return;
    lang = next;
    try {
      localStorage.setItem("stats-lang", lang);
    } catch (error) {
      lang = next;
    }
    applyChrome();
    if (selected) choose(selected);
  }

  search.addEventListener("input", () => {
    selected = null;
    showResults(search.value);
  });
  toggle.addEventListener("change", renderPrevious);
  document.querySelectorAll(".lang-switch button").forEach((button) => {
    button.addEventListener("click", () => setLanguage(button.dataset.lang));
  });
  applyChrome();

  data.cross.forEach((name) => {
    const team = data.teams.find((item) => item.name === name);
    if (!team) return;
    const button = el("button", "chip", team.label);
    button.type = "button";
    button.addEventListener("click", () => choose(team));
    cross.append(button);
  });

  if (data.current_rows === 0) empty.hidden = false;
  if (params.get("compare") === "1") toggle.checked = true;
  const initial = data.teams.find((team) => team.name === requested || team.label === requested);
  if (initial) choose(initial);
}

fetch("stats-data.json")
  .then((response) => {
    if (!response.ok) throw new Error(String(response.status));
    return response.json();
  })
  .then(boot)
  .catch(() => {
    document.querySelector("#load-error").hidden = false;
  });
