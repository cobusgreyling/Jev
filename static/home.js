/* Smart-home demo — speculative fan-out, then code acts. */

async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    let detail = r.statusText;
    try {
      const j = await r.json();
      detail = j.detail || j.error || JSON.stringify(j);
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

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function post(path, body) {
  return fetchJSON(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

let homes = [];
let examples = [];
let house = null;
let homeId = "1br";
let speakingTo = null;
let flashing = new Set();

function renderHome() {
  if (!house) return;
  $("rooms").innerHTML = house.rooms
    .map(
      (room) => `<div class="room">
        <h3>${esc(room.icon)} ${esc(room.name)}</h3>
        <div class="devices">${room.devices
          .map(
            (d) => `<div class="device ${d.active ? "active" : ""} ${
              flashing.has(d.id) ? "flash" : ""
            } ${speakingTo === d.id ? "ctx" : ""}">
            <span class="ico">${esc(d.icon)}</span>
            <div>
              <div class="name">${esc(d.name)}</div>
              <div class="st">${esc(d.status)}</div>
            </div>
            <span class="dot"></span>
          </div>`
          )
          .join("")}</div>
      </div>`
    )
    .join("");
}

function contextDevices() {
  if (!house) return [];
  return house.rooms
    .flatMap((r) => r.devices.map((d) => ({ ...d, room: r.id, roomName: r.name })))
    .filter((d) => d.type === "speaker" || d.type === "thermostat");
}

function renderContextPicker() {
  const opts = contextDevices()
    .map((d) => `<option value="${esc(d.id)}">Talking to: ${esc(d.name)}</option>`)
    .join("");
  $("ctx").innerHTML = `<option value="">No Device Context</option>${opts}`;
  $("ctx").value = speakingTo ?? "";
}

function confClass(c) {
  if (c == null) return "mid";
  return c >= 0.8 ? "hi" : c >= 0.5 ? "mid" : "lo";
}

function fmt(n) {
  const x = Number(n);
  return Number.isFinite(x) ? x.toFixed(2) : "—";
}

function traceHtml(trace) {
  return (trace || [])
    .map((row) => {
      let probs;
      let conf;
      if (row.type === "noul") {
        probs = `<span class="top">p(yes) ${fmt(row.noul)}</span>`;
        const c = Math.abs(Number(row.noul || 0) - 0.5) * 2;
        conf = `<span class="conf ${confClass(c)}">${fmt(row.noul)}</span>`;
      } else {
        const entries = Object.entries(row.probabilities || {}).sort((a, b) => b[1] - a[1]);
        probs = entries
          .filter(([, p], i) => i < 4 || p >= 0.01)
          .map(([k, p], i) => `<span class="${i === 0 ? "top" : ""}">${esc(k)} ${fmt(p)}</span>`)
          .join(" · ");
        conf = `<span class="conf ${confClass(row.confidence)}">${fmt(row.confidence)}</span>`;
      }
      const title = esc(row.instructions || "");
      return `<div class="row ${row.used ? "used" : ""}" title="${title}">
        <span class="tag">${row.used ? "+ " : ""}${esc(row.type)}</span>
        <div>
          <div class="label">${esc(row.label)}</div>
          <div class="probs">${probs}</div>
        </div>
        ${conf}
      </div>`;
    })
    .join("");
}

function replyHtml(kind, text, extra = "") {
  const cls = kind === "confirm" ? "warn" : kind;
  return `<div class="reply ${cls}">${text}${extra}</div>`;
}

function footHtml(payload) {
  const n = payload.question_count ?? (payload.trace || []).length;
  const tokens = (payload.usage?.input_tokens || 0) + (payload.usage?.output_tokens || 0);
  const src = payload.source === "live" ? payload.model : payload.source;
  return `<div class="foot">${esc(src || "jev")} · ${n} prompts · ${payload.latency_ms}ms · ${tokens} tokens</div>`;
}

async function judge(request, { force = false } = {}) {
  return post("/api/home/run", {
    request,
    home_id: homeId,
    speaking_to: speakingTo,
    house,
    force,
  });
}

function markChanged(ids) {
  flashing = new Set(ids || []);
}

async function run(request) {
  const log = $("log");
  $("send").disabled = true;
  $("traceQ").textContent = `"${request}"`;
  $("timing").textContent = "";
  log.innerHTML = `<div class="spin">asking Jev…</div>`;
  flashing = new Set();

  try {
    const ev = await judge(request);
    house = ev.house;
    const srcLabel = ev.source === "live" ? "TypeSafe" : "offline mock";
    $("timing").innerHTML = `${srcLabel} <b>${ev.latency_ms}ms</b>`;
    const trace = traceHtml(ev.trace);
    const foot = footHtml(ev);
    const kind = ev.plan.kind;

    if (kind === "general") {
      const reply = ev.reply || "Classified as general.";
      log.innerHTML = replyHtml("", `💬 ${esc(reply)}`) + trace + foot;
    } else if (kind === "compound") {
      log.innerHTML = `<div class="spin">compound request → splitting…</div>` + trace + foot;
      const split = await post("/api/home/split", { request });
      const parts = [];
      let slowest = 0;
      for (const cmd of split.commands) {
        const sub = await judge(cmd, { force: true });
        house = sub.house;
        slowest = Math.max(slowest, sub.latency_ms);
        markChanged([...(flashing), ...(sub.result?.changed || [])]);
        const status = sub.result?.status || "ok";
        const msg = esc(sub.result?.message || "").replace(/\n/g, "<br>");
        parts.push(
          `<div class="sub"><p class="q">↳ "${esc(cmd)}"</p>${replyHtml(
            status === "confirm" ? "warn" : status,
            msg
          )}${traceHtml(sub.trace)}</div>`
        );
      }
      $("timing").innerHTML += ` · split (${esc(split.via)}) · TypeSafe ×${split.commands.length} <b>${slowest}ms</b>`;
      log.innerHTML =
        replyHtml("", `Split into ${split.commands.length} commands.`) +
        parts.join("") +
        `<div class="sub"><p class="q">Original request</p>${trace}</div>` +
        foot;
    } else if (ev.result?.status === "confirm") {
      log.innerHTML =
        replyHtml(
          "warn",
          esc(ev.result.message),
          `<div><button type="button" id="yes">Do it</button><button type="button" id="no">Cancel</button></div>`
        ) +
        trace +
        foot;
      $("yes").onclick = async () => {
        const applied = await post("/api/home/apply", {
          home_id: homeId,
          house,
          plan: ev.plan,
          force: true,
        });
        house = applied.house;
        markChanged(applied.result.changed);
        log.querySelector(".reply").outerHTML = replyHtml(
          applied.result.status,
          esc(applied.result.message)
        );
        renderHome();
      };
      $("no").onclick = () => {
        log.querySelector(".reply").outerHTML = replyHtml("", "Okay, nothing changed.");
      };
    } else {
      markChanged(ev.result?.changed);
      const msg = esc(ev.result?.message || "").replace(/\n/g, "<br>");
      log.innerHTML = replyHtml(ev.result?.status || "ok", msg) + trace + foot;
    }
    renderHome();
  } catch (err) {
    log.innerHTML = replyHtml("bad", `Error: ${esc(err.message)}`);
  } finally {
    $("send").disabled = false;
  }
}

async function loadHome(id) {
  homeId = id;
  const boot = await fetchJSON("/api/home/bootstrap");
  house = boot.houses[id];
  speakingTo = null;
  renderContextPicker();
  renderHome();
}

async function boot() {
  const boot = await fetchJSON("/api/home/bootstrap");
  homes = boot.homes;
  examples = boot.examples;
  $("modeBadge").textContent = boot.live ? "live API ready" : "offline mock";
  $("homeSel").innerHTML = homes
    .map((h) => `<option value="${esc(h.id)}">${esc(h.label)}</option>`)
    .join("");
  $("chips").innerHTML = examples
    .map((e) => `<button class="chip" type="button">${esc(e)}</button>`)
    .join("");
  $("chips").onclick = (e) => {
    if (!e.target.classList.contains("chip")) return;
    $("prompt").value = e.target.textContent;
    run(e.target.textContent);
  };
  $("form").onsubmit = (e) => {
    e.preventDefault();
    const text = $("prompt").value.trim();
    if (text) run(text);
  };
  $("homeSel").onchange = (e) => loadHome(e.target.value);
  $("reset").onclick = () => loadHome(homeId);
  $("ctx").onchange = (e) => {
    speakingTo = e.target.value || null;
    renderHome();
  };

  const params = new URLSearchParams(location.search);
  const startHome = params.get("home") && boot.houses[params.get("home")] ? params.get("home") : "1br";
  $("homeSel").value = startHome;
  await loadHome(startHome);
  if (params.get("ctx")) {
    speakingTo = params.get("ctx");
    $("ctx").value = speakingTo;
    renderHome();
  }
  if (params.get("q")) {
    $("prompt").value = params.get("q");
    run(params.get("q"));
  }
}

boot().catch((err) => {
  $("log").innerHTML = replyHtml("bad", `Error: ${esc(err.message)}`);
});
