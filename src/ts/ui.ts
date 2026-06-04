/**
 * Red HMS – UI / UX Module
 *
 * Handles all global UI interactions:
 *   - Preloader hide on page load
 *   - Back-to-top button show/hide & scroll
 *   - Auto-dismiss SweetAlert-style Django message toasts
 *   - Sticky header on scroll
 *   - Mobile mmenu hamburger trigger
 *   - Notification badge live-update via polling
 *   - Closeable notification banners (.notification.closeable)
 *   - Image preview for file inputs
 */

import { showToast } from "./utils.js";

// ── Preloader ─────────────────────────────────────────────

function initPreloader(): void {
  const loader = document.querySelector<HTMLElement>("#preloader");
  if (!loader) return;

  window.addEventListener("load", () => {
    loader.style.transition = "opacity .4s";
    loader.style.opacity = "0";
    setTimeout(() => loader.remove(), 450);
  });
}

// ── Back-to-top ───────────────────────────────────────────

function initBackToTop(): void {
  const btn = document.querySelector<HTMLElement>("#bottom_backto_top");
  if (!btn) return;

  window.addEventListener("scroll", () => {
    if (window.scrollY > 350) {
      btn.classList.add("visible");
    } else {
      btn.classList.remove("visible");
    }
  }, { passive: true });

  btn.querySelector("a")?.addEventListener("click", (e) => {
    e.preventDefault();
    window.scrollTo({ top: 0, behavior: "smooth" });
  });
}

// ── Sticky header ─────────────────────────────────────────

function initStickyHeader(): void {
  const header = document.querySelector<HTMLElement>("#header_part");
  if (!header) return;

  window.addEventListener(
    "scroll",
    () => {
      header.classList.toggle("cloned-class", window.scrollY > 80);
    },
    { passive: true }
  );
}

// ── Mobile nav ────────────────────────────────────────────

function initMobileNav(): void {
  const hamburger = document.querySelector<HTMLButtonElement>(".utfbutton_collapse");
  if (!hamburger) return;

  hamburger.addEventListener("click", () => {
    document.body.classList.toggle("mmenu-open");
  });

  // Close when clicking outside
  document.addEventListener("click", (e) => {
    if (
      document.body.classList.contains("mmenu-open") &&
      !(e.target as HTMLElement).closest("#navigation, .utfbutton_collapse")
    ) {
      document.body.classList.remove("mmenu-open");
    }
  });
}

// ── Closeable notification banners ───────────────────────

function initCloseableNotifications(): void {
  document.querySelectorAll<HTMLElement>(".notification.closeable .close").forEach((closeBtn) => {
    closeBtn.addEventListener("click", (e) => {
      e.preventDefault();
      const banner = closeBtn.closest<HTMLElement>(".notification");
      if (banner) {
        banner.style.transition = "opacity .3s, max-height .3s";
        banner.style.opacity = "0";
        banner.style.maxHeight = "0";
        banner.style.overflow = "hidden";
        setTimeout(() => banner.remove(), 320);
      }
    });
  });
}

// ── Image preview for profile / identity upload ───────────

function initImagePreviews(): void {
  // Triggered by onchange="loadFile(event)" in the template
  (window as Window & { loadFile: (event: Event) => void }).loadFile = (event: Event) => {
    const input = event.target as HTMLInputElement;
    if (!input.files?.[0]) return;
    const preview = document.querySelector<HTMLImageElement>("#profile-preview");
    if (preview) {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) preview.src = e.target.result as string;
      };
      reader.readAsDataURL(input.files[0]);
    }
  };
}

// ── Live notification badge polling ──────────────────────

function initNotificationPolling(): void {
  const badges = document.querySelectorAll<HTMLElement>("[data-unread-badge]");
  if (badges.length === 0) return;

  const poll = async () => {
    try {
      const resp = await fetch("/accounts/unread-count/", {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      });
      if (!resp.ok) return;
      const data: { count: number } = await resp.json();
      badges.forEach((badge) => {
        badge.textContent = data.count > 0 ? String(data.count) : "";
        badge.style.display = data.count > 0 ? "inline-flex" : "none";
      });
    } catch {
      // Silent fail – don't spam console in production
    }
  };

  // Poll every 60 seconds
  setInterval(poll, 60_000);
}

// ── Data-confirm attribute for dangerous actions ──────────

function initConfirmActions(): void {
  document.querySelectorAll<HTMLElement>("[data-confirm]").forEach((el) => {
    el.addEventListener("click", async (e) => {
      e.preventDefault();
      const message = el.dataset.confirm || "Are you sure?";
      const result = await Swal.fire({
        icon: "warning",
        title: "Confirm Action",
        text: message,
        showConfirmButton: true,
        confirmButtonText: "Yes, proceed",
        confirmButtonColor: "#c0392b",
        showCancelButton: true,
        cancelButtonText: "Cancel",
      });
      if (result.isConfirmed) {
        if (el instanceof HTMLAnchorElement) {
          window.location.href = el.href;
        } else if (el instanceof HTMLButtonElement) {
          el.closest("form")?.submit();
        }
      }
    });
  });
}

// ── Smooth scroll for anchor links ───────────────────────

function initSmoothScroll(): void {
  document.querySelectorAll<HTMLAnchorElement>('a[href^="#"]').forEach((link) => {
    link.addEventListener("click", (e) => {
      const id = link.getAttribute("href");
      if (!id || id === "#") return;
      const target = document.querySelector<HTMLElement>(id);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
}

// ── Tooltip init (Bootstrap-compatible) ──────────────────

function initTooltips(): void {
  document.querySelectorAll<HTMLElement>("[data-tooltip]").forEach((el) => {
    el.setAttribute("title", el.dataset.tooltip || "");
    el.style.cursor = "help";
  });
}

// ── Main init ─────────────────────────────────────────────

export function initUI(): void {
  initPreloader();
  initBackToTop();
  initStickyHeader();
  initMobileNav();
  initCloseableNotifications();
  initImagePreviews();
  initNotificationPolling();
  initConfirmActions();
  initSmoothScroll();
  initTooltips();
}
