/**
 * Red HMS – Booking & Payment Module
 *
 * Handles:
 *   - Checkout form validation (typed)
 *   - Coupon/discount code AJAX application
 *   - Stripe checkout session creation & redirect
 *   - Payment page loading state
 */

import { csrfToken, showToast, formatCurrency } from "./utils.js";

// ── Coupon application ────────────────────────────────────

interface CouponResult {
  success: boolean;
  message: string;
  new_total: string;
  discount: string;
  coupon_code: string;
}

async function applyCoupon(
  couponCode: string,
  bookingId: string
): Promise<void> {
  const applyBtn = document.querySelector<HTMLButtonElement>("#apply-coupon-btn");
  if (applyBtn) {
    applyBtn.disabled = true;
    applyBtn.innerHTML = '<i class="fa fa-spinner fa-spin"></i>';
  }

  try {
    const form = new FormData();
    form.append("coupon_code", couponCode);
    form.append("booking_id", bookingId);
    form.append("csrfmiddlewaretoken", csrfToken());

    const resp = await fetch("/guests/apply-coupon/", {
      method: "POST",
      body: form,
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data: CouponResult = await resp.json();

    if (data.success) {
      showToast("success", `Coupon applied! You saved ${formatCurrency(parseFloat(data.discount))}`);

      const totalEl = document.querySelector<HTMLElement>(".booking-total-display");
      if (totalEl) totalEl.textContent = formatCurrency(parseFloat(data.new_total));

      const discountRow = document.querySelector<HTMLElement>(".discount-row");
      if (discountRow) {
        discountRow.style.display = "flex";
        const discountVal = discountRow.querySelector<HTMLElement>(".discount-value");
        if (discountVal) discountVal.textContent = `-${formatCurrency(parseFloat(data.discount))}`;
      }

      const couponInput = document.querySelector<HTMLInputElement>("#coupon-input");
      if (couponInput) {
        couponInput.disabled = true;
        couponInput.classList.add("coupon-applied");
      }
    } else {
      showToast("error", data.message || "Invalid coupon code.");
    }
  } catch {
    showToast("error", "Could not apply coupon. Please try again.");
  } finally {
    if (applyBtn) {
      applyBtn.disabled = false;
      applyBtn.innerHTML = "Apply";
    }
  }
}

// ── Checkout form validation ──────────────────────────────

interface CheckoutFields {
  full_name: string;
  email: string;
  phone?: string;
}

function validateCheckoutForm(fields: CheckoutFields): string[] {
  const errors: string[] = [];

  if (!fields.full_name.trim()) {
    errors.push("Full name is required.");
  } else if (fields.full_name.trim().length < 3) {
    errors.push("Full name must be at least 3 characters.");
  }

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!fields.email.trim()) {
    errors.push("Email address is required.");
  } else if (!emailPattern.test(fields.email.trim())) {
    errors.push("Please enter a valid email address.");
  }

  if (fields.phone && fields.phone.trim()) {
    const phonePattern = /^[\d\s\+\-\(\)]{7,20}$/;
    if (!phonePattern.test(fields.phone.trim())) {
      errors.push("Please enter a valid phone number.");
    }
  }

  return errors;
}

function showFormErrors(errors: string[]): void {
  let container = document.querySelector<HTMLElement>("#checkout-errors");
  if (!container) {
    container = document.createElement("div");
    container.id = "checkout-errors";
    container.className = "notification error closeable";
    const form = document.querySelector<HTMLElement>(".utf_booking_listing_section_form");
    form?.prepend(container);
  }
  container.innerHTML =
    `<ul style="margin:0;padding-left:18px;">` +
    errors.map((e) => `<li>${e}</li>`).join("") +
    `</ul>`;
  container.style.display = "block";
  container.scrollIntoView({ behavior: "smooth", block: "center" });
}

function clearFormErrors(): void {
  const container = document.querySelector<HTMLElement>("#checkout-errors");
  if (container) container.style.display = "none";
}

// ── Stripe payment ────────────────────────────────────────

interface StripeSessionResponse {
  session_id?: string;
  stripe_public_key?: string;
  error?: string;
}

async function initiateStripePayment(
  bookingId: string,
  stripePublicKey: string
): Promise<void> {
  const btn = document.querySelector<HTMLButtonElement>("#pay-btn");
  if (!btn) return;

  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa fa-spinner fa-spin"></i> Connecting to Stripe…';

  try {
    const response = await fetch(`/billing/api/checkout-session/${bookingId}/`, {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    const data: StripeSessionResponse = await response.json();

    if (data.session_id) {
      const stripe = Stripe(stripePublicKey);
      const { error } = await stripe.redirectToCheckout({ sessionId: data.session_id });
      if (error) {
        showToast("error", error.message || "Stripe redirect failed.");
        btn.disabled = false;
        btn.innerHTML = originalHtml;
      }
    } else {
      showToast("error", data.error || "Could not create payment session.");
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  } catch (err) {
    showToast("error", "Network error. Please check your connection.");
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
}

// ── Init ──────────────────────────────────────────────────

export function initBooking(): void {
  // Checkout form submit validation
  const checkoutForm = document.querySelector<HTMLFormElement>(".checkout-form");
  checkoutForm?.addEventListener("submit", (e) => {
    clearFormErrors();
    const fields: CheckoutFields = {
      full_name: (document.querySelector<HTMLInputElement>('[name="full_name"]')?.value || ""),
      email:     (document.querySelector<HTMLInputElement>('[name="email"]')?.value || ""),
      phone:     (document.querySelector<HTMLInputElement>('[name="phone"]')?.value || ""),
    };
    const errors = validateCheckoutForm(fields);
    if (errors.length > 0) {
      e.preventDefault();
      showFormErrors(errors);
    }
  });

  // Coupon button
  const couponBtn = document.querySelector<HTMLButtonElement>("#apply-coupon-btn");
  couponBtn?.addEventListener("click", () => {
    const code = document.querySelector<HTMLInputElement>("#coupon-input")?.value?.trim() || "";
    const bookingId = (document.querySelector<HTMLElement>("[data-booking-id]") as HTMLElement)
      ?.dataset?.bookingId || "";
    if (!code) {
      showToast("warning", "Please enter a coupon code.");
      return;
    }
    void applyCoupon(code, bookingId);
  });

  // Stripe pay button
  const payBtn = document.querySelector<HTMLButtonElement>("#pay-btn");
  if (payBtn) {
    const bookingId    = payBtn.dataset.bookingId || "";
    const stripeKey    = payBtn.dataset.stripeKey || "";
    payBtn.addEventListener("click", () => {
      void initiateStripePayment(bookingId, stripeKey);
    });
  }
}
