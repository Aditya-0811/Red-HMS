/**
 * Red HMS – Main Entry Point
 *
 * Bootstraps all TypeScript modules based on which page is active.
 * Each module is only initialised when its relevant DOM elements exist,
 * so every script is safe to load on every page.
 *
 * Build command:  npm run build   (outputs to static/scripts/)
 * Watch command:  npm run watch
 */

import { initUI }           from "./ui.js";
import { initHotel }        from "./hotel.js";
import { initRoomSelection } from "./roomSelection.js";
import { initBooking }       from "./booking.js";
import { initDashboard }     from "./dashboard.js";

// ── Page detection helpers ────────────────────────────────

const body = document.body;

function onPage(...selectors: string[]): boolean {
  return selectors.some((sel) => document.querySelector(sel) !== null);
}

// ── Bootstrap on DOM ready ────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {

  // Global UI (runs on every page)
  initUI();

  // Hotel listing & detail pages
  if (onPage(".utf_listing_item-container", "#utf_listing_gallery_part", ".utf_star_rating_section")) {
    initHotel();
  }

  // Room type detail + selected-rooms page
  if (onPage(".add-to-selection", ".remove-room-btn", "#checkin-input", '[name="checkin"]')) {
    initRoomSelection();
  }

  // Checkout + payment pages
  if (onPage(".checkout-form", "#pay-btn", "#apply-coupon-btn")) {
    initBooking();
  }

  // Dashboard (staff & guest)
  if (onPage("#dashboard", ".utf_dashboard_stat", "[data-stat-value]")) {
    initDashboard();
  }

  // ── Date range picker init (global, for search forms) ──
  initDateRangePicker();

  // ── Chosen.js init (for select dropdowns) ─────────────
  initChosenSelects();

  // ── Slick carousel (hotel cards on homepage) ───────────
  initSlickCarousel();
});

// ── DateRangePicker wrapper ───────────────────────────────

function initDateRangePicker(): void {
  const searchDateInput = document.querySelector<HTMLInputElement>("#booking-date-search");
  if (!searchDateInput || typeof ($ as JQuery).fn?.daterangepicker === "undefined") return;

  const $input = $(searchDateInput);
  const start  = moment();
  const end    = moment().add(2, "days");

  $input.daterangepicker(
    {
      opens: "right",
      autoUpdateInput: true,
      alwaysShowCalendars: true,
      startDate: start,
      endDate: end,
      minDate: moment(),
      locale: { format: "YYYY-MM-DD" },
    },
    (s: ReturnType<typeof moment>, e: ReturnType<typeof moment>) => {
      searchDateInput.value = `${s.format("YYYY-MM-DD")} / ${e.format("YYYY-MM-DD")}`;

      // Also populate hidden checkin/checkout fields if present
      const checkinInput  = document.querySelector<HTMLInputElement>('[name="checkin"]');
      const checkoutInput = document.querySelector<HTMLInputElement>('[name="checkout"]');
      if (checkinInput)  checkinInput.value  = s.format("YYYY-MM-DD");
      if (checkoutInput) checkoutInput.value = e.format("YYYY-MM-DD");
    }
  );

  // Clear on load
  window.addEventListener("load", () => { searchDateInput.value = ""; });
}

// ── Chosen.js select enhancement ─────────────────────────

function initChosenSelects(): void {
  const selects = document.querySelectorAll<HTMLSelectElement>("select.utf_chosen_select_single");
  if (selects.length === 0) return;
  if (typeof ($ as JQuery).fn?.chosen === "undefined") return;

  selects.forEach((sel) => {
    $(sel).chosen({ disable_search_threshold: 10, width: "100%" });
  });
}

// ── Slick carousel for hotel cards ───────────────────────

function initSlickCarousel(): void {
  const slider = document.querySelector<HTMLElement>(".slick_carousel_slider .row");
  if (!slider) return;
  if (typeof ($ as JQuery).fn?.slick === "undefined") return;

  const $slider = $(slider);
  if ($slider.children().length > 3) {
    $slider.slick({
      dots: true,
      infinite: true,
      speed: 400,
      slidesToShow: 3,
      slidesToScroll: 1,
      autoplay: true,
      autoplaySpeed: 4000,
      responsive: [
        { breakpoint: 992, settings: { slidesToShow: 2 } },
        { breakpoint: 600, settings: { slidesToShow: 1 } },
      ],
    });
  }
}
