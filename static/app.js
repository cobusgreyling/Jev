/* Jev Showcase — front-end */

async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const j = await r.json();
      detail = j.detail || JSON.stringify(j);
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return r.json();
}

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(s) {
  return escapeHtml(s);
}

function initTabs() {
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const panel = $(`tab-${btn.dataset.tab}`);
      if (panel) panel.classList.add("active");
    });
  });
}

async function loadHealth() {
  const badge = $("liveBadge");
  try {
    const h = await fetchJSON("/api/health");
    if (h.live) {
      badge.textContent = "live API ready";
      badge.classList.add("ok");
    } else {
      badge.textContent = "offline · fixtures OK";
      badge.classList.add("warn");
    }
  } catch {
    badge.textContent = "server offline";
    badge.classList.add("warn");
  }
}

function renderHidden(data) {
  $("hiddenSub").textContent = data.subtitle || "";
  $("hiddenNote").textContent = data.source_note || "";
  const root = $("hiddenRoot");
  root.innerHTML = "";
  (data.items || []).forEach((item, idx) => {
    const el = document.createElement("article");
    el.className = "scenario" + (idx === 0 ? " open" : "");
    const docs = (item.docs || [])
      .map((u) => `<a href="${escapeAttr(u)}" target="_blank" rel="noopener">docs</a>`)
      .join(" · ");
    el.innerHTML = `
      <div class="scenario-top">
        <h3><span class="rank">#${item.rank}</span> ${escapeHtml(item.title)}</h3>
        <span class="tag tag-accent">${escapeHtml(item.badge)}</span>
      </div>
      <p style="margin:0.45rem 0 0;color:var(--muted);font-size:0.9rem">${escapeHtml(item.summary)}</p>
      <div class="scenario-body">
        <p>${escapeHtml(item.detail)}</p>
        <p><strong>Do this:</strong> ${escapeHtml(item.action)}</p>
        <p>${docs}</p>
      </div>
    `;
    el.addEventListener("click", () => el.classList.toggle("open"));
    root.appendChild(el);
  });
}

function pct(n) {
  return `${Math.round(Number(n) * 1000) / 10}%`;
}

function distBars(obj, fillClass) {
  const entries = Object.entries(obj || {});
  if (!entries.length) return "";
  return entries
    .map(([k, v]) => {
      const w = Math.max(0, Math.min(100, Number(v) * 100));
      return `<div class="bar-line">
        <span class="bar-label">${escapeHtml(k)}</span>
        <span class="bar-track"><span class="bar-fill ${fillClass || ""}" style="width:${w}%"></span></span>
        <span class="bar-val">${pct(v)}</span>
      </div>`;
    })
    .join("");
}

function renderAnswers(answers, targetId) {
  const root = $(targetId);
  if (!answers) {
    root.innerHTML = "";
    return;
  }
  const cards = [];
  if (answers.department) {
    const a = answers.department;
    cards.push(`<article class="answer-card">
      <h3>Choice · department</h3>
      <div class="answer-value">${escapeHtml(a.choice || "—")}</div>
      ${distBars(a.probabilities)}
      <p class="footnote">confidence ${a.confidence ?? "—"}</p>
    </article>`);
  }
  if (answers.frustration) {
    const a = answers.frustration;
    cards.push(`<article class="answer-card">
      <h3>Score · frustration</h3>
      <div class="answer-value">${escapeHtml(String(a.score ?? "—"))}</div>
      ${distBars(a.probabilities, "cyan")}
      <p class="footnote">confidence ${a.confidence ?? "—"}</p>
    </article>`);
  }
  if (answers.is_urgent) {
    const a = answers.is_urgent;
    const n = Number(a.noul || 0);
    cards.push(`<article class="answer-card">
      <h3>Noul · is_urgent</h3>
      <div class="answer-value">${n.toFixed(3)}</div>
      <div class="bar-line">
        <span class="bar-label">P(yes)</span>
        <span class="bar-track"><span class="bar-fill green" style="width:${n * 100}%"></span></span>
        <span class="bar-val">${pct(n)}</span>
      </div>
      <p class="footnote">Noul has no separate confidence field</p>
    </article>`);
  }
  root.innerHTML = `<div class="answer-grid">${cards.join("")}</div>`;
}

function renderPolicy(policy, targetId) {
  const el = $(targetId);
  if (!policy) {
    el.innerHTML = "";
    return;
  }
  const cls = policy.lane === "human" ? "human" : policy.lane === "confirm" ? "warn" : "";
  el.innerHTML = `<div class="policy-box ${cls}">
    <strong>Code would:</strong> <code>${escapeHtml(policy.action)}</code>
    · lane <code>${escapeHtml(policy.lane)}</code>
    · priority <code>${escapeHtml(policy.priority)}</code>
    <p class="footnote" style="margin:0.4rem 0 0">
      Thresholds live in <code>jev_lab/policy.py</code>, not in the model.
      Changing a weight re-scores for free.
    </p>
  </div>`;
}

let playground = { presets: [], questions: {} };
let activePreset = "stripe-outage";

function stateToText(state) {
  return typeof state === "string" ? state : JSON.stringify(state, null, 2);
}

function textToState(text) {
  const t = text.trim();
  if (t.startsWith("{") || t.startsWith("[")) {
    try {
      return JSON.parse(t);
    } catch {
      return t;
    }
  }
  return t;
}

function setPreset(id) {
  activePreset = id;
  const p = playground.presets.find((x) => x.id === id);
  if (p) $("playState").value = stateToText(p.state);
  document.querySelectorAll("#presetChips .chip").forEach((c) => {
    c.classList.toggle("on", c.dataset.id === id);
  });
}

async function runFixture() {
  const data = await fetchJSON(`/api/fixtures/${activePreset}`);
  renderAnswers(data.response.answers, "playAnswers");
  const policy = await fetchJSON("/api/policy/ticket", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ answers: data.response.answers }),
  });
  renderPolicy(policy, "playPolicy");
  $("playMeta").innerHTML = `<h4>${data.live ? "Live capture" : "Offline fixture"}</h4>
    <p>model <code>${escapeHtml(data.response.model)}</code> ·
    ${data.latency_ms} ms ·
    ${data.response.usage?.input_tokens ?? "?"} in /
    ${data.response.usage?.output_tokens ?? "?"} out (free)</p>`;
}

function renderCost(data) {
  const j = data.jev;
  const l = data.llm_stand_in;
  $("costResult").innerHTML = `<h4>$${j.total_usd.toFixed(6)}</h4>
    <p>Jev input $${j.input_usd.toFixed(6)} · output $${j.output_usd.toFixed(6)} (free)</p>
    <p>LLM stand-in (${l.calls} serial calls): $${l.total_usd.toFixed(6)}</p>
    <p>Rough savings vs stand-in: <strong>${Math.round(data.savings_vs_llm * 100)}%</strong></p>`;
}

async function loadCard() {
  const card = await fetchJSON("/api/model-card");
  const rows = [
    ["Name", card.name],
    ["Model id", card.model_id],
    ["Alias", card.alias],
    ["Class", card.class],
    ["Released", card.released],
    ["Context", `${card.context_window} tokens / request`],
    ["State + longest question", `${card.state_plus_longest_question} tokens`],
    ["Input", (card.modalities.input || []).join(", ")],
    ["Output", (card.modalities.output || []).join(", ")],
    ["Not supported", (card.modalities.not_supported || []).join(", ")],
    ["Input price", `$${card.pricing.input_per_mtok_usd} / MTok`],
    ["Output price", "free"],
    ["Latency", `${card.latency_ms.typical_low}–${card.latency_ms.typical_high} ms`],
    ["Training", card.training.method],
    ["Fine-tune", card.training.fine_tune ? "yes" : "no — shape via request"],
    ["Endpoint", card.endpoint],
  ];
  $("cardTable").innerHTML = `<tbody>${rows
    .map(([k, v]) => `<tr><td>${escapeHtml(k)}</td><td>${escapeHtml(String(v))}</td></tr>`)
    .join("")}</tbody>`;
  $("gotchaGrid").innerHTML = (card.operator_gotchas || [])
    .map((g) => `<article class="pill"><p>${escapeHtml(g)}</p></article>`)
    .join("");
  $("cardDisclaimer").textContent = card.disclaimer || "";
}

async function boot() {
  initTabs();
  loadHealth();

  const hidden = await fetchJSON("/api/hidden-knowledge");
  renderHidden(hidden);

  playground = await fetchJSON("/api/playground");
  const chips = $("presetChips");
  chips.innerHTML = "";
  playground.presets.forEach((p) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.dataset.id = p.id;
    b.textContent = p.label;
    b.addEventListener("click", () => setPreset(p.id));
    chips.appendChild(b);
  });
  setPreset("stripe-outage");
  $("playBtn").addEventListener("click", () => runFixture().catch((e) => {
    $("playMeta").innerHTML = `<h4>Error</h4><p class="err">${escapeHtml(e.message)}</p>`;
  }));
  runFixture().catch(() => {});

  $("costBtn").addEventListener("click", async () => {
    const data = await fetchJSON("/api/cost/estimate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        input_tokens: Number($("cIn").value),
        output_tokens: Number($("cOut").value),
        questions: Number($("cQ").value),
      }),
    });
    renderCost(data);
  });
  $("costFanout").addEventListener("click", async () => {
    const data = await fetchJSON("/api/cost/fanout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ state_tokens: 3000, question_tokens: 80, n_questions: 13 }),
    });
    const box = $("fanoutResult");
    box.style.display = "block";
    box.innerHTML = `<h4>13 questions, one article</h4>
      <p>Batched: ${data.batched_input_tokens} tokens · $${data.batched_usd}</p>
      <p>Serial: ${data.serial_input_tokens} tokens · $${data.serial_usd}</p>
      <p><strong>${data.cheaper_factor}×</strong> cheaper to fan out (state paid once).
      Official cookbook: ~12.2× cheaper, ~10× faster.</p>`;
  });
  $("costBtn").click();

  const patterns = await fetchJSON("/api/patterns");
  $("patternRoot").innerHTML = (patterns.items || [])
    .map(
      (p) => `<article class="pill">
        <h3>${escapeHtml(p.name)}</h3>
        <p>${escapeHtml(p.what)}</p>
        <p style="margin-top:0.45rem"><strong>Code owns:</strong> ${escapeHtml(p.code_owns)}</p>
      </article>`
    )
    .join("");

  const jagged = await fetchJSON("/api/jaggedness");
  const jroot = $("jaggedRoot");
  jroot.innerHTML = "";
  (jagged.items || []).forEach((item) => {
    const el = document.createElement("article");
    el.className = "scenario";
    el.innerHTML = `
      <div class="scenario-top">
        <h3>${escapeHtml(item.title)}</h3>
      </div>
      <div class="scenario-body" style="display:block">
        <p><strong>Do this instead:</strong> ${escapeHtml(item.instead)}</p>
      </div>`;
    jroot.appendChild(el);
  });

  const scenarios = await fetchJSON("/api/scenarios");
  const sroot = $("scenarioRoot");
  sroot.innerHTML = "";
  (scenarios.items || []).forEach((item, idx) => {
    const el = document.createElement("article");
    el.className = "scenario" + (idx === 0 ? " open" : "");
    const steps = (item.steps || []).map((s) => `<li>${escapeHtml(s)}</li>`).join("");
    el.innerHTML = `
      <div class="scenario-top">
        <h3>${escapeHtml(item.title)}</h3>
        <span class="tag tag-accent">${escapeHtml(item.badge)}</span>
      </div>
      <p style="margin:0.45rem 0 0;color:var(--muted);font-size:0.9rem">${escapeHtml(item.summary)}</p>
      <div class="scenario-body">
        <ol class="steps">${steps}</ol>
      </div>`;
    el.addEventListener("click", () => el.classList.toggle("open"));
    sroot.appendChild(el);
  });

  $("liveBtn").addEventListener("click", async () => {
    $("liveErr").hidden = true;
    try {
      const data = await fetchJSON("/api/judge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ state: textToState($("liveState").value) }),
      });
      renderAnswers(data.answers, "liveAnswers");
      renderPolicy(data.policy, "livePolicy");
    } catch (e) {
      $("liveErr").hidden = false;
      $("liveErr").textContent = e.message;
    }
  });
  $("liveClear").addEventListener("click", () => {
    $("liveAnswers").innerHTML = "";
    $("livePolicy").innerHTML = "";
    $("liveErr").hidden = true;
  });

  loadCard().catch(() => {});
}

boot().catch((err) => {
  console.error(err);
});
