/**
 * Red HMS – Room Selection Module
 *
 * Handles the full AJAX-driven room cart:
 *   - Adding rooms to the session-based selection
 *   - Removing rooms with confirmation
 *   - Live cart count update in the navbar badge
 *   - Live total price recalculation on the selected-rooms page
 */

import { csrfToken, showToast, confirmDialog, calcNights, formatCurrency } from "./utils.js";

// ── Types ─────────────────────────────────────────────────

interface AddToSelectionPayload {
  hotel_id: string;
  room_type_id: string;
  room_id: string;
  checkin: string;
  checkout: string;
  adult: number;
  children: number;
}

interface SelectionResponse {
  success: boolean;
  message: string;
  cart_count: number;
  total?: string;
}

// ── Cart badge update ─────────────────────────────────────

function updateCartBadge(count: number): void {
  const badges = document.querySelectorAll<HTMLElement>(".room-count");
  badges.forEach((badge) => {
    badge.textContent = String(count);
    // Pulse animation
    badge.classList.remove("pulse");
    void badge.offsetWidth; // reflow trick
    badge.classList.add("pulse");
  });
}

// ── Add room to session cart via AJAX ─────────────────────

async function addRoomToSelection(
  btn: HTMLButtonElement,
  payload: AddToSelectionPayload
): Promise<void> {
  const original = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Adding…';

  const form = new FormData();
  Object.entries(payload).forEach(([k, v]) => form.append(k, String(v)));
  form.append("csrfmiddlewaretoken", csrfToken());

  try {
    const response = await fetch("/guests/add/", {
      method: "POST",
      body: form,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    if (response.redirected) {
      // Non-AJAX fallback: follow the redirect
      window.location.href = response.url;
      return;
    }

    const data: SelectionResponse = await response.json();

    if (data.success) {
      showToast("success", data.message || "Room added to selection!");
      updateCartBadge(data.cart_count);
      btn.innerHTML = '<i class="fa fa-check"></i> Added';
      btn.classList.add("button-added");
    } else {
      showToast("info", data.message || "Room already selected.");
      btn.disabled = false;
      btn.innerHTML = original;
    }
  } catch {
    // Fallback to normal form submit if AJAX fails
    btn.closest("form")?.submit();
  }
}

// ── Remove room from cart ─────────────────────────────────

async function removeRoomFromSelection(
  roomId: number | string,
  rowElement: HTMLElement
): Promise<void> {
  const confirmed = await confirmDialog(
    "Remove Room?",
    "This room will be removed from your selection."
  );
  if (!confirmed) return;

  rowElement.style.opacity = "0.4";
  rowElement.style.pointerEvents = "none";

  try {
    const response = await fetch(`/guests/remove/${roomId}/`, {
      method: "GET",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    if (response.ok || response.redirected) {
      // Animate removal
      rowElement.style.transition = "all .3s";
      rowElement.style.maxHeight = `${rowElement.offsetHeight}px`;
      requestAnimationFrame(() => {
        rowElement.style.maxHeight = "0";
        rowElement.style.overflow = "hidden";
        rowElement.style.opacity = "0";
      });
      setTimeout(() => {
        rowElement.remove();
        recalculateTotal();
        showToast("info", "Room removed from selection.");
      }, 320);
    }
  } catch {
    rowElement.style.opacity = "1";
    rowElement.style.pointerEvents = "auto";
    showToast("error", "Could not remove room. Please try again.");
  }
}

// ── Recalculate total on selected-rooms page ──────────────

function recalculateTotal(): void {
  let total = 0;
  document.querySelectorAll<HTMLElement>("[data-room-subtotal]").forEach((el) => {
    total += parseFloat(el.dataset.roomSubtotal || "0");
  });
  const totalEl = document.querySelector<HTMLElement>(".cart-total-value");
  if (totalEl) totalEl.textContent = formatCurrency(total);

  const countEl = document.querySelector<HTMLElement>(".cart-room-count");
  const items = document.querySelectorAll("[data-room-subtotal]").length;
  if (countEl) countEl.textContent = String(items);

  // Disable checkout if empty
  const checkoutBtn = document.querySelector<HTMLButtonElement>(".proceed-checkout-btn");
  if (checkoutBtn) checkoutBtn.disabled = items === 0;
}

// ── Date validation for the room type detail page ─────────

function initDateValidation(): void {
  const checkinInput = document.querySelector<HTMLInputElement>(
    'input[name="checkin"], #checkin-input'
  );
  const checkoutInput = document.querySelector<HTMLInputElement>(
    'input[name="checkout"], #checkout-input'
  );
  const nightsDisplay = document.querySelector<HTMLElement>("#nights-display");
  const estimateDisplay = document.querySelector<HTMLElement>("#price-estimate");

  if (!checkinInput || !checkoutInput) return;

  const today = new Date().toISOString().split("T")[0];
  checkinInput.min = today;
  checkoutInput.min = today;

  function updateNights(): void {
    if (!checkinInput!.value || !checkoutInput!.value) return;
    if (checkoutInput!.value <= checkinInput!.value) {
      // Auto-advance checkout by 1 day
      const next = new Date(checkinInput!.value);
      next.setDate(next.getDate() + 1);
      checkoutInput!.value = next.toISOString().split("T")[0];
    }
    const nights = calcNights(checkinInput!.value, checkoutInput!.value);
    if (nightsDisplay) nightsDisplay.textContent = `${nights} night(s)`;

    // Live price estimate
    const priceEl = document.querySelector<HTMLElement>("[data-room-price]");
    if (estimateDisplay && priceEl) {
      const pricePerNight = parseFloat(priceEl.dataset.roomPrice || "0");
      estimateDisplay.textContent = formatCurrency(pricePerNight * nights);
    }
  }

  checkinInput.addEventListener("change", () => {
    checkoutInput!.min = checkinInput!.value;
    updateNights();
  });
  checkoutInput.addEventListener("change", updateNights);
}

// ── Quantity buttons (adults / children) ─────────────────

function initQuantityButtons(): void {
  document.querySelectorAll<HTMLElement>("[data-qty-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.qtyTarget!;
      const action = btn.dataset.qtyAction as "inc" | "dec";
      const input = document.querySelector<HTMLInputElement>(`#${targetId}`);
      if (!input) return;
      const val = parseInt(input.value) || 0;
      const min = parseInt(input.min) || 0;
      const max = parseInt(input.max) || 99;
      if (action === "inc" && val < max) input.value = String(val + 1);
      if (action === "dec" && val > min) input.value = String(val - 1);
    });
  });
}

// ── Initialise all room-selection event listeners ─────────

export function initRoomSelection(): void {
  // Add-to-selection buttons
  document.querySelectorAll<HTMLButtonElement>(".add-to-selection").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const form = btn.closest("form");
      if (!form) return;

      const payload: AddToSelectionPayload = {
        hotel_id:     (form.querySelector<HTMLInputElement>('[name="hotel_id"]')?.value   || ""),
        room_type_id: (form.querySelector<HTMLInputElement>('[name="room_type_id"]')?.value || ""),
        room_id:      (form.querySelector<HTMLInputElement>('[name="room_id"]')?.value    || ""),
        checkin:      (form.querySelector<HTMLInputElement>('[name="checkin"]')?.value    || ""),
        checkout:     (form.querySelector<HTMLInputElement>('[name="checkout"]')?.value   || ""),
        adult:        parseInt(form.querySelector<HTMLInputElement>('[name="adult"]')?.value || "1"),
        children:     parseInt(form.querySelector<HTMLInputElement>('[name="children"]')?.value || "0"),
      };
      void addRoomToSelection(btn, payload);
    });
  });

  // Remove buttons on selected-rooms page
  document.querySelectorAll<HTMLElement>(".remove-room-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const roomId = btn.dataset.roomId;
      const row = btn.closest<HTMLElement>("li, .room-cart-row");
      if (roomId && row) void removeRoomFromSelection(roomId, row);
    });
  });

  initDateValidation();
  initQuantityButtons();
  recalculateTotal();
}
