const UNAVAILABLE = "Μη διαθέσιμων στατιστικών";
const SCOPE_LABELS = {
  combined: "Ενιαίος μέσος",
  europe: "Ευρώπη",
  domestic: "Πρωτάθλημα",
  regional: "Liga ABA",
};
const SCOPE_COLORS = {
  combined: "#f5b942",
  europe: "#4c8dff",
  domestic: "#3dbe86",
  regional: "#e07a3d",
};
const STAT_LABELS = {
  ppg: "Πόντοι",
  rpg: "Ριμπάουντ",
  apg: "Ασίστ",
  spg: "Κλεψίματα",
  bpg: "Κοψίματα",
  tov: "Λάθη",
  pf: "Φάουλ",
  orb: "Επιθ. ριμπ.",
  drb: "Αμυν. ριμπ.",
  fg_pct: "Εντός πεδιάς",
  tp_pct: "Τρίποντα",
  ft_pct: "Βολές",
  mpg: "Λεπτά",
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
  if (!value) return "ακόμη";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  const pad = (n) => String(n).padStart(2, "0");
  return `${pad(parsed.getUTCDate())}/${pad(parsed.getUTCMonth() + 1)}/${parsed.getUTCFullYear()} ${pad(parsed.getUTCHours())}:${pad(parsed.getUTCMinutes())} UTC`;
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
    return summary;
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
  return summary;
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
  return {
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
  };
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
  if (!europe || !domestic || europe.ppg == null || domestic.ppg == null) return null;
  const diff = Number(domestic.ppg) - Number(europe.ppg);
  if (Math.abs(diff) < 0.15) return "Η παραγωγή πόντων στην Ευρώπη και στο πρωτάθλημα είναι σχεδόν ίδια.";
  if (diff > 0) return `Στο πρωτάθλημα σκοράρει ${diff.toFixed(1)} πόντους περισσότερους ανά αγώνα από ό,τι στην Ευρώπη.`;
  return `Στην Ευρώπη σκοράρει ${Math.abs(diff).toFixed(1)} πόντους περισσότερους ανά αγώνα από ό,τι στο πρωτάθλημα.`;
}

function weightSentence(scopes) {
  const parts = [`${Number(scopes.combined.gp).toFixed(0)} αγώνες συνολικά`];
  [["europe", "στην Ευρώπη"], ["regional", "στη Liga ABA"], ["domestic", "στο πρωτάθλημα"]].forEach(([key, label]) => {
    if (scopes[key]) parts.push(`${Number(scopes[key].gp).toFixed(0)} ${label}`);
  });
  return `Ο ενιαίος μέσος σταθμίζεται με τους αγώνες: ${parts.join(", ")}.`;
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

function groupedBars(scopes, keys, title, asPercent) {
  const traces = availableScopes(scopes).map(([key, block]) => ({
    type: "bar",
    name: SCOPE_LABELS[key],
    x: keys.map((stat) => STAT_LABELS[stat]),
    y: keys.map((stat) => (block[stat] == null ? null : asPercent ? Number(block[stat]) * 100 : Number(block[stat]))),
    marker: { color: SCOPE_COLORS[key] },
    hovertemplate: "%{y:.1f}<extra>%{fullData.name}</extra>",
  }));
  const layout = chartLayout(title);
  if (asPercent) layout.yaxis.ticksuffix = "%";
  return { data: traces, layout };
}

function radarChart(scopes) {
  const stats = ["ppg", "rpg", "apg", "spg", "bpg", "fg_pct", "tp_pct", "ft_pct"];
  const labels = stats.map((stat) => STAT_LABELS[stat]);
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
      name: SCOPE_LABELS[key],
      fill: "toself",
      line: { color: SCOPE_COLORS[key], width: 2 },
      customdata: custom.concat(custom[0]),
      hovertemplate: "%{theta}: %{customdata}<extra>%{fullData.name}</extra>",
    });
  });
  return {
    data: traces,
    layout: {
      title: { text: "Προφίλ σε κοινή κλίμακα", x: 0, xanchor: "left" },
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
  profile.competitions.forEach((row) => {
    const color = SCOPE_COLORS[row.scope] || "#8892a8";
    const pill = el("span", "pill", `${row.league_name} · ${row.country} · ${Number(row.gp).toFixed(0)} αγ.`);
    pill.style.background = `${color}22`;
    pill.style.color = color;
    pill.style.borderColor = `${color}55`;
    pills.append(pill);
  });
  mount.append(pills);
  mount.append(el("p", "subtle", `Σεζόν ${profile.competitions[0].season} · ενημέρωση ${formatWhen(profile.updated_at)}`));
  const insight = scoringInsight(profile.scopes);
  if (insight) mount.append(el("div", "insight", insight));
  mount.append(el("p", "caption", weightSentence(profile.scopes)));

  const metrics = el("div", "metrics");
  [["Πόντοι", "ppg"], ["Ριμπάουντ", "rpg"], ["Ασίστ", "apg"], ["Εντός πεδιάς", "fg_pct"], ["Τρίποντα", "tp_pct"], ["Βολές", "ft_pct"]].forEach(([label, key]) => {
    const card = el("div", "metric");
    card.append(el("span", "metric-label", label));
    card.append(el("strong", "metric-value", fmt(key, profile.scopes.combined[key])));
    metrics.append(card);
  });
  mount.append(metrics);

  const charts = el("div", "charts");
  [
    groupedBars(profile.scopes, ["ppg", "rpg", "apg", "spg", "bpg"], "Παραγωγή ανά αγώνα", false),
    groupedBars(profile.scopes, ["fg_pct", "tp_pct", "ft_pct"], "Ποσοστά σουτ", true),
    radarChart(profile.scopes),
    groupedBars(profile.scopes, ["orb", "drb", "tov", "pf"], "Ριμπάουντ, λάθη και φάουλ", false),
  ].forEach((figure) => {
    const box = el("div", "chart");
    charts.append(box);
    window.Plotly.newPlot(box, figure.data, figure.layout, { displayModeBar: false, responsive: true });
  });
  mount.append(charts);

  mount.append(el("h3", "section", "Ανα διοργάνωση"));
  const table = document.createElement("table");
  const head = document.createElement("tr");
  ["Διοργάνωση", "Κατηγορία", "Χώρα", "Αγώνες", "Πόντοι", "Ριμπάουντ", "Ασίστ", "Εντός", "Τρίποντα", "Βολές"].forEach((label) => {
    const cell = document.createElement("th");
    cell.textContent = label;
    head.append(cell);
  });
  table.append(head);
  const scopeNames = { europe: "Ευρώπη", domestic: "Πρωτάθλημα", regional: "Liga ABA" };
  profile.competitions.forEach((row) => {
    const line = document.createElement("tr");
    [row.league_name, scopeNames[row.scope] || row.scope, row.country, fmt("gp", row.gp), fmt("ppg", row.ppg), fmt("rpg", row.rpg), fmt("apg", row.apg), fmt("fg_pct", row.fg_pct), fmt("tp_pct", row.tp_pct), fmt("ft_pct", row.ft_pct)].forEach((value) => {
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
  caption.textContent = `Σεζόν ${data.current_season}: ${data.current_rows} γραμμές · αποθηκευμένη σεζόν ${data.previous_season}: ${data.previous_rows} γραμμές · τελευταία αποθήκευση ${formatWhen(data.refreshed_at)}`;

  let selected = null;
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
    currentMount.append(el("h3", "section", `Σεζόν ${data.current_season}`));
    if (!team.current) {
      currentMount.append(el("div", "notice", UNAVAILABLE));
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
      previousMount.append(el("div", "notice", UNAVAILABLE));
      return;
    }
    const previous = comparisonProfile(selected, limits, data);
    if (!previous) {
      previousMount.append(el("div", "notice", UNAVAILABLE));
      return;
    }
    previousMount.append(el("h3", "section", `Σεζόν ${data.previous_season} · αντίστοιχη αγωνιστική`));
    previousMount.append(el("p", "caption", "Μέσοι όροι μόνο από τους πρώτους αγώνες της περσινής σεζόν, όσους έχει δώσει η ομάδα φέτος σε κάθε διοργάνωση. Δεν προστίθενται στον μέσο όρο του 2026-27."));
    const card = el("div");
    renderProfile(card, previous, data, false);
    previousMount.append(card);
    const missing = (previous.missing_leagues || []).map((code) => data.leagues[code]?.league_name).filter(Boolean);
    if (missing.length) previousMount.append(el("p", "caption", `Χωρίς αρχείο αγώνα-αγώνα για: ${missing.join(", ")}.`));
  }

  search.addEventListener("input", () => {
    selected = null;
    showResults(search.value);
  });
  toggle.addEventListener("change", renderPrevious);

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
