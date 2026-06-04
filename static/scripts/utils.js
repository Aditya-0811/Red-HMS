/**
 * Red HMS – Shared Utility Functions
 * Compiled from src/ts/utils.ts
 */

export function getCookie(name) {
  const cookies = document.cookie.split(";");
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split("=");
    if (key === name) return decodeURIComponent(value);
  }
  return "";
}

export function csrfToken() {
  return getCookie("csrftoken");
}

export async function djangoPost(url, data) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken(),
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  return response.json();
}

export async function djangoGet(url) {
  const response = await fetch(url, {
    method: "GET",
    headers: { "X-Requested-With": "XMLHttpRequest" },
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  return response.json();
}

export function showToast(icon, title, timer = 2500) {
  Swal.fire({ icon, title, timer, toast: true, position: "top-end",
              showConfirmButton: false, timerProgressBar: true });
}

export async function confirmDialog(title, text) {
  const result = await Swal.fire({
    icon: "warning", title, text,
    showConfirmButton: true, confirmButtonText: "Yes, proceed",
    showCancelButton: true, cancelButtonText: "Cancel",
    confirmButtonColor: "#c0392b",
  });
  return result.isConfirmed;
}

export function formatCurrency(amount, symbol = "$") {
  return `${symbol}${amount.toFixed(2)}`;
}

export function calcNights(checkin, checkout) {
  const ci = new Date(checkin);
  const co = new Date(checkout);
  return Math.max(Math.round((co - ci) / (1000 * 60 * 60 * 24)), 1);
}

export function animateCounter(element, target, duration = 1200, prefix = "", suffix = "") {
  const start = performance.now();
  const update = (time) => {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = `${prefix}${Math.floor(eased * target).toLocaleString()}${suffix}`;
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

export function debounce(fn, delay) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

export function todayISO() {
  return new Date().toISOString().split("T")[0];
}
