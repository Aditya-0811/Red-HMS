/**
 * Red HMS – Global TypeScript Type Declarations
 * These types cover the Django context variables passed to templates
 * and third-party globals (Stripe, SweetAlert2, daterangepicker).
 */

// ── Django CSRF token helper ──────────────────────────────
declare function getCookie(name: string): string | null;

// ── SweetAlert2 (loaded via CDN) ──────────────────────────
declare const Swal: {
  fire(options: {
    icon?: "success" | "error" | "warning" | "info" | "question";
    title?: string;
    text?: string;
    html?: string;
    timer?: number;
    timerProgressBar?: boolean;
    showConfirmButton?: boolean;
    confirmButtonText?: string;
    showCancelButton?: boolean;
    cancelButtonText?: string;
    confirmButtonColor?: string;
    toast?: boolean;
    position?: string;
  }): Promise<{ isConfirmed: boolean; isDenied: boolean; isDismissed: boolean }>;
};

// ── Stripe.js (loaded via CDN) ────────────────────────────
declare const Stripe: (publicKey: string) => {
  redirectToCheckout(options: { sessionId: string }): Promise<{ error?: { message: string } }>;
};

// ── moment.js (loaded via CDN) ────────────────────────────
declare const moment: (date?: string | Date) => {
  format(fmt: string): string;
  add(amount: number, unit: string): ReturnType<typeof moment>;
  subtract(amount: number, unit: string): ReturnType<typeof moment>;
};

// ── daterangepicker jQuery plugin ─────────────────────────
interface JQuery {
  daterangepicker(options?: object, callback?: Function): JQuery;
  chosen(options?: object): JQuery;
}

// ── Red HMS – Room selection session item ─────────────────
interface RoomSelectionItem {
  hotel_id: string;
  room_type_id: string;
  room_id: string;
  checkin: string;
  checkout: string;
  adults: number;
  children: number;
}

// ── Django JSON response shapes ───────────────────────────
interface DjangoResponse {
  success: boolean;
  message?: string;
  error?: string;
}

interface BookmarkResponse extends DjangoResponse {
  bookmarked: boolean;
  hotel_id: number;
}

interface RoomSelectionResponse extends DjangoResponse {
  cart_count: number;
  total: string;
}

interface CouponResponse extends DjangoResponse {
  new_total: string;
  discount: string;
  coupon_code: string;
}

interface CheckoutSessionResponse {
  session_id?: string;
  stripe_public_key?: string;
  error?: string;
}

// ── Hotel card data (embedded in template) ────────────────
interface HotelData {
  id: number;
  name: string;
  slug: string;
  average_rating: number | null;
  views: number;
}

// ── Notification item ─────────────────────────────────────
interface NotificationItem {
  id: number;
  type: string;
  message: string;
  is_read: boolean;
  date: string;
}

// ── Dashboard stats (for chart rendering) ────────────────
interface DashboardStats {
  labels: string[];
  revenue: number[];
  bookings: number[];
  occupancy: number[];
}
