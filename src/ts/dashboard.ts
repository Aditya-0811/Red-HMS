/**
 * Red HMS – Dashboard Module
 *
 * Handles:
 *   - Animated stat card counters
 *   - Revenue bar chart (Canvas API – no extra library needed)
 *   - Occupancy donut chart
 *   - Live clock in dashboard header
 *   - Booking status filter change
 *   - Notification dropdown toggle
 */

import { animateCounter, formatCurrency } from "./utils.js";

// ── Types ─────────────────────────────────────────────────

interface ChartDataset {
  labels: string[];
  values: number[];
  color?: string;
}

// ── Animated stat counters ────────────────────────────────

function initStatCounters(): void {
  document.querySelectorAll<HTMLElement>("[data-stat-value]").forEach((el) => {
    const raw = el.dataset.statValue || "0";
    const prefix = el.dataset.statPrefix || "";
    const suffix = el.dataset.statSuffix || "";
    const target = parseFloat(raw.replace(/[^0-9.]/g, "")) || 0;

    // Use IntersectionObserver so animation fires when card scrolls into view
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateCounter(el, target, 1400, prefix, suffix);
            observer.unobserve(el);
          }
        });
      },
      { threshold: 0.3 }
    );
    observer.observe(el);
  });
}

// ── Simple canvas bar chart ───────────────────────────────

function drawBarChart(
  canvasId: string,
  dataset: ChartDataset,
  labelPrefix = "$"
): void {
  const canvas = document.querySelector<HTMLCanvasElement>(`#${canvasId}`);
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const W = canvas.width;
  const H = canvas.height;
  const PAD = 40;
  const BAR_GAP = 8;
  const max = Math.max(...dataset.values, 1);
  const barW = Math.floor((W - PAD * 2) / dataset.labels.length) - BAR_GAP;
  const color = dataset.color || "#c0392b";

  ctx.clearRect(0, 0, W, H);

  // Grid lines
  ctx.strokeStyle = "#f0f0f0";
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = PAD + ((H - PAD * 2) * i) / 4;
    ctx.beginPath();
    ctx.moveTo(PAD, y);
    ctx.lineTo(W - PAD, y);
    ctx.stroke();
    ctx.fillStyle = "#aaa";
    ctx.font = "11px Open Sans";
    ctx.fillText(`${labelPrefix}${Math.round((max * (4 - i)) / 4)}`, 2, y + 4);
  }

  // Bars with animation
  let frame = 0;
  const totalFrames = 45;

  const animate = () => {
    ctx.clearRect(0, 0, W, H);
    const progress = Math.min(frame / totalFrames, 1);
    const eased = 1 - Math.pow(1 - progress, 2);

    // Re-draw grid
    ctx.strokeStyle = "#f0f0f0";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = PAD + ((H - PAD * 2) * i) / 4;
      ctx.beginPath();
      ctx.moveTo(PAD, y);
      ctx.lineTo(W - PAD, y);
      ctx.stroke();
      ctx.fillStyle = "#aaa";
      ctx.font = "11px Open Sans";
      ctx.fillText(`${labelPrefix}${Math.round((max * (4 - i)) / 4)}`, 2, y + 4);
    }

    dataset.values.forEach((val, i) => {
      const x = PAD + i * (barW + BAR_GAP);
      const barH = ((H - PAD * 2) * (val / max)) * eased;
      const y = H - PAD - barH;

      // Bar
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(x, y, barW, barH, [3, 3, 0, 0]);
      ctx.fill();

      // Label below
      ctx.fillStyle = "#666";
      ctx.font = "10px Open Sans";
      ctx.textAlign = "center";
      ctx.fillText(dataset.labels[i], x + barW / 2, H - PAD + 14);

      // Value above bar (only last frame)
      if (frame === totalFrames) {
        ctx.fillStyle = color;
        ctx.font = "bold 10px Open Sans";
        ctx.fillText(`${labelPrefix}${val}`, x + barW / 2, y - 4);
      }

      ctx.textAlign = "left";
    });

    if (frame < totalFrames) {
      frame++;
      requestAnimationFrame(animate);
    }
  };
  requestAnimationFrame(animate);
}

// ── Donut chart for occupancy ─────────────────────────────

function drawDonutChart(
  canvasId: string,
  occupied: number,
  total: number
): void {
  const canvas = document.querySelector<HTMLCanvasElement>(`#${canvasId}`);
  if (!canvas || total === 0) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const radius = Math.min(cx, cy) - 10;
  const pct = occupied / total;

  let frame = 0;
  const totalFrames = 60;

  const animate = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const progress = Math.min(frame / totalFrames, 1);
    const eased = 1 - Math.pow(1 - progress, 2);
    const endAngle = -Math.PI / 2 + 2 * Math.PI * pct * eased;

    // Background ring
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, 2 * Math.PI);
    ctx.strokeStyle = "#f0f0f0";
    ctx.lineWidth = 20;
    ctx.stroke();

    // Occupied arc
    ctx.beginPath();
    ctx.arc(cx, cy, radius, -Math.PI / 2, endAngle);
    ctx.strokeStyle = "#c0392b";
    ctx.lineWidth = 20;
    ctx.lineCap = "round";
    ctx.stroke();

    // Centre text
    ctx.fillStyle = "#333";
    ctx.font = `bold ${Math.floor(radius * 0.4)}px Open Sans`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`${Math.round(pct * 100 * eased)}%`, cx, cy - 8);
    ctx.font = `12px Open Sans`;
    ctx.fillStyle = "#aaa";
    ctx.fillText("Occupied", cx, cy + radius * 0.35);
    ctx.textAlign = "left";
    ctx.textBaseline = "alphabetic";

    if (frame < totalFrames) {
      frame++;
      requestAnimationFrame(animate);
    }
  };
  requestAnimationFrame(animate);
}

// ── Live clock ────────────────────────────────────────────

function initLiveClock(): void {
  const clockEl = document.querySelector<HTMLElement>("#live-clock");
  if (!clockEl) return;
  const update = () => {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString("en-US", {
      hour: "2-digit", minute: "2-digit", second: "2-digit",
    });
  };
  update();
  setInterval(update, 1000);
}

// ── Notification dropdown ─────────────────────────────────

function initNotificationDropdown(): void {
  document.querySelectorAll<HTMLElement>(".js-item-menu").forEach((trigger) => {
    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const dropdown = trigger.querySelector<HTMLElement>(".js-dropdown");
      if (dropdown) {
        dropdown.classList.toggle("active");
      }
    });
  });
  document.addEventListener("click", () => {
    document.querySelectorAll<HTMLElement>(".js-dropdown.active").forEach((d) =>
      d.classList.remove("active")
    );
  });
}

// ── Dashboard responsive sidebar toggle ──────────────────

function initDashboardSidebar(): void {
  const trigger = document.querySelector<HTMLAnchorElement>(".utf_dashboard_nav_responsive");
  const nav = document.querySelector<HTMLElement>(".utf_dashboard_navigation");
  trigger?.addEventListener("click", (e) => {
    e.preventDefault();
    nav?.classList.toggle("responsive-open");
  });
}

// ── Revenue chart bootstrap ───────────────────────────────

function initRevenueChart(): void {
  const chartContainer = document.querySelector<HTMLElement>("#revenue-chart-container");
  if (!chartContainer) return;

  // Data is embedded by Django in a <script id="chart-data"> tag
  const dataScript = document.querySelector<HTMLScriptElement>("#revenue-chart-data");
  if (!dataScript) return;

  try {
    const data: ChartDataset = JSON.parse(dataScript.textContent || "{}");
    drawBarChart("revenue-bar-chart", data, "$");
  } catch {
    console.warn("Red HMS: Could not parse revenue chart data.");
  }
}

// ── Occupancy chart bootstrap ─────────────────────────────

function initOccupancyChart(): void {
  const canvas = document.querySelector<HTMLCanvasElement>("#occupancy-donut-chart");
  if (!canvas) return;
  const occupied = parseInt(canvas.dataset.occupied || "0");
  const total    = parseInt(canvas.dataset.total    || "0");
  drawDonutChart("occupancy-donut-chart", occupied, total);
}

// ── Main init ─────────────────────────────────────────────

export function initDashboard(): void {
  initStatCounters();
  initLiveClock();
  initNotificationDropdown();
  initDashboardSidebar();
  initRevenueChart();
  initOccupancyChart();
}
