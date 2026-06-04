/**
 * Red HMS – Shared Utility Functions
 * Typed helper functions used across all modules.
 */

/**
 * Read a browser cookie by name.
 * Used primarily to retrieve the Django CSRF token.
 */
export function getCookie(name: string): string {
  const cookies = document.cookie.split(";");
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split("=");
    if (key === name) return decodeURIComponent(value);
  }
  return "";
}

/**
 * Return the Django CSRF token from the cookie.
 */
export function csrfToken(): string {
  return getCookie("csrftoken");
}

/**
 * Perform a typed POST request to a Django endpoint.
 * Automatically attaches the CSRF token and JSON headers.
 */
export async function djangoPost<T>(
  url: string,
  data: Record<string, unknown>
): Promise<T> {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken(),
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

/**
 * Perform a typed GET request.
 */
export async function djangoGet<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    method: "GET",
    headers: { "X-Requested-With": "XMLHttpRequest" },
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

/**
 * Show a SweetAlert2 toast notification.
 */
export function showToast(
  icon: "success" | "error" | "warning" | "info",
  title: string,
  timer = 2500
): void {
  Swal.fire({
    icon,
    title,
    timer,
    toast: true,
    position: "top-end",
    showConfirmButton: false,
    timerProgressBar: true,
  });
}

/**
 * Show a SweetAlert2 confirmation dialog.
 * Returns true if the user confirmed.
 */
export async function confirmDialog(
  title: string,
  text: string
): Promise<boolean> {
  const result = await Swal.fire({
    icon: "warning",
    title,
    text,
    showConfirmButton: true,
    confirmButtonText: "Yes, proceed",
    showCancelButton: true,
    cancelButtonText: "Cancel",
    confirmButtonColor: "#c0392b",
  });
  return result.isConfirmed;
}

/**
 * Format a decimal number as a currency string.
 */
export function formatCurrency(amount: number, symbol = "$"): string {
  return `${symbol}${amount.toFixed(2)}`;
}

/**
 * Calculate the number of nights between two ISO date strings.
 */
export function calcNights(checkin: string, checkout: string): number {
  const ci = new Date(checkin);
  const co = new Date(checkout);
  const diff = co.getTime() - ci.getTime();
  return Math.max(Math.round(diff / (1000 * 60 * 60 * 24)), 1);
}

/**
 * Animate a numeric counter from 0 to a target value.
 * Used for dashboard stat cards.
 */
export function animateCounter(
  element: HTMLElement,
  target: number,
  duration = 1200,
  prefix = "",
  suffix = ""
): void {
  const start = performance.now();
  const update = (time: number) => {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = Math.floor(eased * target);
    element.textContent = `${prefix}${current.toLocaleString()}${suffix}`;
    if (progress < 1) requestAnimationFrame(update);
  };
  requestAnimationFrame(update);
}

/**
 * Debounce a function call.
 */
export function debounce<T extends (...args: unknown[]) => void>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  };
}

/**
 * Get today's date as an ISO string (YYYY-MM-DD).
 */
export function todayISO(): string {
  return new Date().toISOString().split("T")[0];
}
