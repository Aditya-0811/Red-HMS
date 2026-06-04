/**
 * Red HMS – Booking & Payment Module
 * Compiled from src/ts/booking.ts
 */
import { csrfToken, showToast, formatCurrency } from "./utils.js";

async function applyCoupon(couponCode, bookingId) {
  const applyBtn = document.querySelector("#apply-coupon-btn");
  if (applyBtn) { applyBtn.disabled = true; applyBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>'; }

  try {
    const form = new FormData();
    form.append("coupon_code", couponCode);
    form.append("booking_id", bookingId);
    form.append("csrfmiddlewaretoken", csrfToken());
    const resp = await fetch("/guests/apply-coupon/", {
      method: "POST", body: form, headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data = await resp.json();
    if (data.success) {
      showToast("success", `Coupon applied! Saved ${formatCurrency(parseFloat(data.discount))}`);
      const totalEl = document.querySelector(".booking-total-display");
      if (totalEl) totalEl.textContent = formatCurrency(parseFloat(data.new_total));
      const discountRow = document.querySelector(".discount-row");
      if (discountRow) {
        discountRow.style.display = "flex";
        const dv = discountRow.querySelector(".discount-value");
        if (dv) dv.textContent = `-${formatCurrency(parseFloat(data.discount))}`;
      }
      const couponInput = document.querySelector("#coupon-input");
      if (couponInput) { couponInput.disabled = true; couponInput.classList.add("coupon-applied"); }
    } else {
      showToast("error", data.message || "Invalid coupon code.");
    }
  } catch { showToast("error", "Could not apply coupon. Please try again."); }
  finally {
    if (applyBtn) { applyBtn.disabled = false; applyBtn.innerHTML = "Apply"; }
  }
}

function validateCheckoutForm(fields) {
  const errors = [];
  if (!fields.full_name.trim()) errors.push("Full name is required.");
  else if (fields.full_name.trim().length < 3) errors.push("Full name must be at least 3 characters.");
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!fields.email.trim()) errors.push("Email address is required.");
  else if (!emailPattern.test(fields.email.trim())) errors.push("Please enter a valid email address.");
  if (fields.phone?.trim()) {
    if (!/^[\d\s\+\-\(\)]{7,20}$/.test(fields.phone.trim())) errors.push("Please enter a valid phone number.");
  }
  return errors;
}

function showFormErrors(errors) {
  let container = document.querySelector("#checkout-errors");
  if (!container) {
    container = document.createElement("div");
    container.id = "checkout-errors";
    container.className = "notification error closeable";
    document.querySelector(".utf_booking_listing_section_form")?.prepend(container);
  }
  container.innerHTML = `<ul style="margin:0;padding-left:18px;">${errors.map(e => `<li>${e}</li>`).join("")}</ul>`;
  container.style.display = "block";
  container.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function initiateStripePayment(bookingId, stripePublicKey) {
  const btn = document.querySelector("#pay-btn");
  if (!btn) return;
  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Connecting to Stripe…';
  try {
    const response = await fetch(`/billing/api/checkout-session/${bookingId}/`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data = await response.json();
    if (data.session_id) {
      const stripe = Stripe(stripePublicKey);
      const { error } = await stripe.redirectToCheckout({ sessionId: data.session_id });
      if (error) { showToast("error", error.message || "Redirect failed."); btn.disabled = false; btn.innerHTML = originalHtml; }
    } else {
      showToast("error", data.error || "Could not create payment session.");
      btn.disabled = false; btn.innerHTML = originalHtml;
    }
  } catch { showToast("error", "Network error. Please check your connection."); btn.disabled = false; btn.innerHTML = originalHtml; }
}

export function initBooking() {
  const checkoutForm = document.querySelector(".checkout-form");
  checkoutForm?.addEventListener("submit", (e) => {
    const g = (n) => document.querySelector(`[name="${n}"]`)?.value || "";
    const errors = validateCheckoutForm({ full_name: g("full_name"), email: g("email"), phone: g("phone") });
    if (errors.length > 0) { e.preventDefault(); showFormErrors(errors); }
    else document.querySelector("#checkout-errors")?.remove();
  });

  document.querySelector("#apply-coupon-btn")?.addEventListener("click", () => {
    const code = document.querySelector("#coupon-input")?.value?.trim() || "";
    const bookingId = document.querySelector("[data-booking-id]")?.dataset?.bookingId || "";
    if (!code) { showToast("warning", "Please enter a coupon code."); return; }
    void applyCoupon(code, bookingId);
  });

  const payBtn = document.querySelector("#pay-btn");
  if (payBtn) {
    payBtn.addEventListener("click", () => {
      void initiateStripePayment(payBtn.dataset.bookingId || "", payBtn.dataset.stripeKey || "");
    });
  }
}
