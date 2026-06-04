/**
 * Red HMS – Dashboard Module
 * Compiled from src/ts/dashboard.ts
 */
import { animateCounter, formatCurrency } from "./utils.js";

function initStatCounters() {
  document.querySelectorAll("[data-stat-value]").forEach((el) => {
    const raw    = el.dataset.statValue || "0";
    const prefix = el.dataset.statPrefix || "";
    const suffix = el.dataset.statSuffix || "";
    const target = parseFloat(raw.replace(/[^0-9.]/g, "")) || 0;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { animateCounter(el, target, 1400, prefix, suffix); observer.unobserve(el); }
      });
    }, { threshold: 0.3 });
    observer.observe(el);
  });
}

function drawBarChart(canvasId, dataset, labelPrefix = "$") {
  const canvas = document.querySelector(`#${canvasId}`);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const W = canvas.width, H = canvas.height, PAD = 40, BAR_GAP = 8;
  const max = Math.max(...dataset.values, 1);
  const barW = Math.floor((W - PAD * 2) / dataset.labels.length) - BAR_GAP;
  const color = dataset.color || "#c0392b";
  let frame = 0;
  const totalFrames = 45;

  const drawGrid = () => {
    ctx.strokeStyle = "#f0f0f0"; ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = PAD + ((H - PAD * 2) * i) / 4;
      ctx.beginPath(); ctx.moveTo(PAD, y); ctx.lineTo(W - PAD, y); ctx.stroke();
      ctx.fillStyle = "#aaa"; ctx.font = "11px Open Sans";
      ctx.fillText(`${labelPrefix}${Math.round((max * (4 - i)) / 4)}`, 2, y + 4);
    }
  };

  const animate = () => {
    ctx.clearRect(0, 0, W, H);
    const progress = Math.min(frame / totalFrames, 1);
    const eased = 1 - Math.pow(1 - progress, 2);
    drawGrid();
    dataset.values.forEach((val, i) => {
      const x = PAD + i * (barW + BAR_GAP);
      const barH = ((H - PAD * 2) * (val / max)) * eased;
      const y = H - PAD - barH;
      ctx.fillStyle = color;
      if (ctx.roundRect) { ctx.beginPath(); ctx.roundRect(x, y, barW, barH, [3, 3, 0, 0]); ctx.fill(); }
      else { ctx.fillRect(x, y, barW, barH); }
      ctx.fillStyle = "#666"; ctx.font = "10px Open Sans"; ctx.textAlign = "center";
      ctx.fillText(dataset.labels[i], x + barW / 2, H - PAD + 14);
      if (frame === totalFrames) {
        ctx.fillStyle = color; ctx.font = "bold 10px Open Sans";
        ctx.fillText(`${labelPrefix}${val}`, x + barW / 2, y - 4);
      }
      ctx.textAlign = "left";
    });
    if (frame < totalFrames) { frame++; requestAnimationFrame(animate); }
  };
  requestAnimationFrame(animate);
}

function drawDonutChart(canvasId, occupied, total) {
  const canvas = document.querySelector(`#${canvasId}`);
  if (!canvas || total === 0) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const cx = canvas.width / 2, cy = canvas.height / 2;
  const radius = Math.min(cx, cy) - 10;
  const pct = occupied / total;
  let frame = 0;
  const totalFrames = 60;
  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const progress = Math.min(frame / totalFrames, 1);
    const eased = 1 - Math.pow(1 - progress, 2);
    ctx.beginPath(); ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
    ctx.strokeStyle = "#f0f0f0"; ctx.lineWidth = 20; ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, radius, -Math.PI / 2, -Math.PI / 2 + 2 * Math.PI * pct * eased);
    ctx.strokeStyle = "#c0392b"; ctx.lineWidth = 20; ctx.lineCap = "round"; ctx.stroke();
    ctx.fillStyle = "#333"; ctx.font = `bold ${Math.floor(radius * 0.4)}px Open Sans`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(`${Math.round(pct * 100 * eased)}%`, cx, cy - 8);
    ctx.font = "12px Open Sans"; ctx.fillStyle = "#aaa";
    ctx.fillText("Occupied", cx, cy + radius * 0.35);
    ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
    if (frame < totalFrames) { frame++; requestAnimationFrame(animate); }
  };
  requestAnimationFrame(animate);
}

function initLiveClock() {
  const clockEl = document.querySelector("#live-clock");
  if (!clockEl) return;
  const update = () => {
    clockEl.textContent = new Date().toLocaleTimeString("en-US", {
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  };
  update(); setInterval(update, 1000);
}

function initNotificationDropdown() {
  document.querySelectorAll(".js-item-menu").forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      trigger.querySelector(".js-dropdown")?.classList.toggle("active");
    });
  });
  document.addEventListener("click", () => {
    document.querySelectorAll(".js-dropdown.active").forEach((d) => d.classList.remove("active"));
  });
}

function initDashboardSidebar() {
  const trigger = document.querySelector(".utf_dashboard_nav_responsive");
  const nav     = document.querySelector(".utf_dashboard_navigation");
  trigger?.addEventListener("click", (e) => { e.preventDefault(); nav?.classList.toggle("responsive-open"); });
}

function initRevenueChart() {
  const dataScript = document.querySelector("#revenue-chart-data");
  if (!dataScript) return;
  try { drawBarChart("revenue-bar-chart", JSON.parse(dataScript.textContent || "{}"), "$"); }
  catch { console.warn("Red HMS: Could not parse revenue chart data."); }
}

function initOccupancyChart() {
  const canvas = document.querySelector("#occupancy-donut-chart");
  if (!canvas) return;
  drawDonutChart("occupancy-donut-chart",
    parseInt(canvas.dataset.occupied || "0"),
    parseInt(canvas.dataset.total    || "0"));
}

export function initDashboard() {
  initStatCounters();
  initLiveClock();
  initNotificationDropdown();
  initDashboardSidebar();
  initRevenueChart();
  initOccupancyChart();
}
