/**
 * Red HMS – Room Selection Module
 * Compiled from src/ts/roomSelection.ts
 */
import { csrfToken, showToast, confirmDialog, calcNights, formatCurrency } from "./utils.js";

function updateCartBadge(count) {
  document.querySelectorAll(".room-count").forEach((badge) => {
    badge.textContent = String(count);
    badge.classList.remove("pulse");
    void badge.offsetWidth;
    badge.classList.add("pulse");
  });
}

async function addRoomToSelection(btn, payload) {
  const original = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Adding…';

  const form = new FormData();
  Object.entries(payload).forEach(([k, v]) => form.append(k, String(v)));
  form.append("csrfmiddlewaretoken", csrfToken());

  try {
    const response = await fetch("/guests/add/", {
      method: "POST", body: form,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    if (response.redirected) { window.location.href = response.url; return; }
    const data = await response.json();
    if (data.success) {
      showToast("success", data.message || "Room added!");
      updateCartBadge(data.cart_count);
      btn.innerHTML = '<i class="fa fa-check"></i> Added';
      btn.classList.add("button-added");
    } else {
      showToast("info", data.message || "Room already selected.");
      btn.disabled = false;
      btn.innerHTML = original;
    }
  } catch { btn.closest("form")?.submit(); }
}

async function removeRoomFromSelection(roomId, rowElement) {
  const confirmed = await confirmDialog("Remove Room?", "This room will be removed from your selection.");
  if (!confirmed) return;

  rowElement.style.opacity = "0.4";
  rowElement.style.pointerEvents = "none";

  try {
    const response = await fetch(`/guests/remove/${roomId}/`, {
      method: "GET", headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    if (response.ok || response.redirected) {
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
    showToast("error", "Could not remove room.");
  }
}

function recalculateTotal() {
  let total = 0;
  document.querySelectorAll("[data-room-subtotal]").forEach((el) => {
    total += parseFloat(el.dataset.roomSubtotal || "0");
  });
  const totalEl = document.querySelector(".cart-total-value");
  if (totalEl) totalEl.textContent = formatCurrency(total);
  const countEl = document.querySelector(".cart-room-count");
  const items = document.querySelectorAll("[data-room-subtotal]").length;
  if (countEl) countEl.textContent = String(items);
  const checkoutBtn = document.querySelector(".proceed-checkout-btn");
  if (checkoutBtn) checkoutBtn.disabled = items === 0;
}

function initDateValidation() {
  const checkinInput  = document.querySelector('input[name="checkin"], #checkin-input');
  const checkoutInput = document.querySelector('input[name="checkout"], #checkout-input');
  const nightsDisplay   = document.querySelector("#nights-display");
  const estimateDisplay = document.querySelector("#price-estimate");
  if (!checkinInput || !checkoutInput) return;

  const today = new Date().toISOString().split("T")[0];
  checkinInput.min  = today;
  checkoutInput.min = today;

  function updateNights() {
    if (!checkinInput.value || !checkoutInput.value) return;
    if (checkoutInput.value <= checkinInput.value) {
      const next = new Date(checkinInput.value);
      next.setDate(next.getDate() + 1);
      checkoutInput.value = next.toISOString().split("T")[0];
    }
    const nights = calcNights(checkinInput.value, checkoutInput.value);
    if (nightsDisplay) nightsDisplay.textContent = `${nights} night(s)`;
    const priceEl = document.querySelector("[data-room-price]");
    if (estimateDisplay && priceEl) {
      estimateDisplay.textContent = formatCurrency(parseFloat(priceEl.dataset.roomPrice || "0") * nights);
    }
  }

  checkinInput.addEventListener("change", () => { checkoutInput.min = checkinInput.value; updateNights(); });
  checkoutInput.addEventListener("change", updateNights);
}

function initQuantityButtons() {
  document.querySelectorAll("[data-qty-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = document.querySelector(`#${btn.dataset.qtyTarget}`);
      if (!input) return;
      const val = parseInt(input.value) || 0;
      const min = parseInt(input.min) || 0;
      const max = parseInt(input.max) || 99;
      if (btn.dataset.qtyAction === "inc" && val < max) input.value = String(val + 1);
      if (btn.dataset.qtyAction === "dec" && val > min) input.value = String(val - 1);
    });
  });
}

export function initRoomSelection() {
  document.querySelectorAll(".add-to-selection").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const form = btn.closest("form");
      if (!form) return;
      const g = (n) => form.querySelector(`[name="${n}"]`)?.value || "";
      const payload = {
        hotel_id: g("hotel_id"), room_type_id: g("room_type_id"), room_id: g("room_id"),
        checkin: g("checkin"), checkout: g("checkout"),
        adult: parseInt(g("adult") || "1"), children: parseInt(g("children") || "0"),
      };
      void addRoomToSelection(btn, payload);
    });
  });

  document.querySelectorAll(".remove-room-btn").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const row = btn.closest("li, .room-cart-row");
      if (btn.dataset.roomId && row) void removeRoomFromSelection(btn.dataset.roomId, row);
    });
  });

  initDateValidation();
  initQuantityButtons();
  recalculateTotal();
}
