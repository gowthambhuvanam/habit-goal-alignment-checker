"use strict";

const $ = id => document.getElementById(id);

const SAMPLE_GOALS = ["Get fit and lose 10kg", "Save money for a house", "Grow as a senior engineer"];
const SAMPLE_HABITS = ["Gym 3 times a week", "Order takeout 4 times a week", "Scroll phone 2 hours at night", "Cook at home on weekdays", "Build side projects on weekends"];

function addRow(target, value = "") {
  const list = $(target + "-list");
  const row = document.createElement("div");
  row.className = "entry-row";
  const placeholder = target === "goals" ? "e.g. Run a marathon" : "e.g. Sleep by 11pm";
  row.innerHTML = `
    <input type="text" value="${value.replace(/"/g, "&quot;")}" placeholder="${placeholder}" />
    <button class="del-btn" title="Remove">&times;</button>
  `;
  row.querySelector(".del-btn").addEventListener("click", () => row.remove());
  list.appendChild(row);
}

// Seed with sample rows
SAMPLE_GOALS.forEach(g => addRow("goals", g));
SAMPLE_HABITS.forEach(h => addRow("habits", h));

document.querySelectorAll(".add-btn").forEach(btn => {
  btn.addEventListener("click", () => addRow(btn.dataset.target));
});

function collect(target) {
  return Array.from($(target + "-list").querySelectorAll("input"))
    .map(i => i.value.trim())
    .filter(Boolean);
}

$("analyze-btn").addEventListener("click", async () => {
  const goals = collect("goals");
  const habits = collect("habits");

  if (goals.length < 1) { alert("Add at least one goal."); return; }
  if (habits.length < 1) { alert("Add at least one habit."); return; }

  $("input-section").classList.add("hidden");
  $("loading-section").classList.remove("hidden");
  $("results-section").classList.add("hidden");

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goals, habits }),
    });
    let data;
    try { data = await res.json(); }
    catch (_) { throw new Error("The server took too long. Please try again."); }
    if (data.detail) throw new Error(data.detail);
    renderResults(data);
  } catch (err) {
    $("loading-section").classList.add("hidden");
    $("input-section").classList.remove("hidden");
    alert("Analysis failed: " + err.message);
  }
});

function scoreColor(s) {
  if (s >= 70) return "#16a34a";
  if (s >= 40) return "#d97706";
  return "#dc2626";
}

function renderResults(data) {
  $("overall-summary").textContent = data.overall_summary || "";

  // Goal scores
  const scoresEl = $("goal-scores");
  scoresEl.innerHTML = "";
  (data.goals || []).sort((a, b) => (a.alignment_score || 0) - (b.alignment_score || 0)).forEach(g => {
    const s = g.alignment_score ?? 0;
    const color = scoreColor(s);
    const row = document.createElement("div");
    row.className = "score-row";
    row.innerHTML = `
      <div class="score-top">
        <span class="score-name">${escapeHtml(g.name)}</span>
        <span class="score-num" style="color:${color}">${s}</span>
      </div>
      <div class="score-bar"><div class="score-fill" style="width:0%;background:${color}"></div></div>
      <p class="score-verdict">${escapeHtml(g.verdict || "")}</p>
    `;
    scoresEl.appendChild(row);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { row.querySelector(".score-fill").style.width = s + "%"; });
    });
  });

  // Blind spots
  const blindEl = $("blind-spots");
  const blinds = data.blind_spots || [];
  blindEl.innerHTML = blinds.length
    ? blinds.map(b => `<div class="blind-item">No habit supports: <strong>${escapeHtml(b)}</strong></div>`).join("")
    : `<div class="blind-empty">Every goal has at least one supporting habit. Nice.</div>`;

  // Recommendations
  const recEl = $("recommendations");
  recEl.innerHTML = (data.recommendations || []).map(r => `
    <div class="rec-item">
      <div class="rec-action">${escapeHtml(r.action || "")}</div>
      ${r.helps_goal ? `<div class="rec-goal">helps: ${escapeHtml(r.helps_goal)}</div>` : ""}
    </div>
  `).join("");

  // Graph
  $("loading-section").classList.add("hidden");
  $("results-section").classList.remove("hidden");

  if (data.figure && data.figure.data) {
    Plotly.newPlot("graph", data.figure.data, data.figure.layout, {
      displayModeBar: false, responsive: true,
    });
  }
}

$("reset-btn").addEventListener("click", () => {
  $("results-section").classList.add("hidden");
  $("input-section").classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
});

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
