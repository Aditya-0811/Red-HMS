/**
 * Red HMS – Hotel & Listing Module
 *
 * Handles:
 *   - Instant client-side hotel card search / filter
 *   - Animated star ratings via data-rating attribute
 *   - AJAX bookmark (wishlist) toggle with heart icon feedback
 *   - Hotel gallery lightbox (CSS-only fallback)
 *   - Scroll-triggered card fade-in animations
 *   - Share URL clipboard copy
 */

import { csrfToken, showToast } from "./utils.js";

// ── Types ─────────────────────────────────────────────────

interface BookmarkResponse {
  success: boolean;
  bookmarked: boolean;
  message: string;
}

// ── Star rating renderer ──────────────────────────────────

/**
 * Converts numeric data-rating="4.5" into filled/half/empty star icons.
 * Uses the reference stylesheet's .utf_star_rating_section class.
 */
function renderStarRatings(): void {
  document.querySelectorAll<HTMLElement>(".utf_star_rating_section[data-rating]").forEach((el) => {
    const rawRating = parseFloat(el.dataset.rating || "0");
    if (!rawRating) return;

    const starsContainer = document.createElement("div");
    starsContainer.className = "utf_star_rating_stars";

    for (let i = 1; i <= 5; i++) {
      const star = document.createElement("i");
      if (rawRating >= i) {
        star.className = "fa fa-star";
      } else if (rawRating >= i - 0.5) {
        star.className = "fa fa-star-half-o";
      } else {
        star.className = "fa fa-star-o";
      }
      star.style.color = "#c0392b";
      star.style.fontSize = "13px";
      starsContainer.appendChild(star);
    }

    // Insert before the counter text
    const counter = el.querySelector<HTMLElement>(".utf_counter_star_rating");
    if (counter) el.insertBefore(starsContainer, counter);
  });
}

// ── Client-side hotel card search ────────────────────────

function initHotelSearch(): void {
  const searchInput = document.querySelector<HTMLInputElement>("#hotel-search-input");
  const cards = document.querySelectorAll<HTMLElement>(".utf_listing_item-container, .hotel-card");

  if (!searchInput || cards.length === 0) return;

  searchInput.addEventListener("input", () => {
    const q = searchInput.value.toLowerCase().trim();
    let visibleCount = 0;

    cards.forEach((card) => {
      const text = card.textContent?.toLowerCase() || "";
      const visible = !q || text.includes(q);
      card.style.display = visible ? "" : "none";
      if (visible) visibleCount++;
    });

    // Update result count display
    const countEl = document.querySelector<HTMLElement>("#search-result-count");
    if (countEl) countEl.textContent = `${visibleCount} hotel(s) found`;
  });
}

// ── AJAX Bookmark toggle ──────────────────────────────────

async function toggleBookmark(
  slug: string,
  heartIcon: HTMLElement
): Promise<void> {
  heartIcon.style.opacity = "0.5";

  try {
    const response = await fetch(`/guests/bookmark/${slug}/`, {
      method: "GET",
      headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    if (response.redirected) {
      // User not logged in – redirect to login
      window.location.href = response.url;
      return;
    }

    // Toggle heart colour optimistically
    const isCurrentlyRed = heartIcon.style.color === "rgb(192, 57, 43)" ||
                            heartIcon.style.color === "#c0392b";

    if (isCurrentlyRed) {
      heartIcon.style.color = "#aaa";
      showToast("info", "Removed from wishlist.");
    } else {
      heartIcon.style.color = "#c0392b";
      showToast("success", "Saved to wishlist!");

      // Heart bounce animation
      heartIcon.style.transform = "scale(1.4)";
      setTimeout(() => { heartIcon.style.transform = "scale(1)"; }, 300);
    }
  } catch {
    showToast("error", "Could not update wishlist.");
  } finally {
    heartIcon.style.opacity = "1";
  }
}

function initBookmarkButtons(): void {
  document.querySelectorAll<HTMLElement>("[data-bookmark-slug]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const slug = btn.dataset.bookmarkSlug || "";
      const icon = btn.querySelector<HTMLElement>("i.fa-heart") || btn;
      icon.style.transition = "color .2s, transform .3s";
      void toggleBookmark(slug, icon);
    });
  });
}

// ── Scroll-triggered card animations ─────────────────────

function initCardAnimations(): void {
  const cards = document.querySelectorAll<HTMLElement>(
    ".utf_listing_item-container, .utf_dashboard_stat"
  );

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          (entry.target as HTMLElement).classList.add("fade-in-up");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  cards.forEach((card) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(20px)";
    card.style.transition = "opacity .4s ease, transform .4s ease";
    observer.observe(card);
  });

  // CSS class that triggers the animation
  const style = document.createElement("style");
  style.textContent = `.fade-in-up { opacity: 1 !important; transform: translateY(0) !important; }`;
  document.head.appendChild(style);
}

// ── Share URL clipboard copy ──────────────────────────────

function initShareButton(): void {
  const btn = document.querySelector<HTMLElement>("#clipboard");
  if (!btn) return;

  btn.addEventListener("click", (e) => {
    e.preventDefault();
    navigator.clipboard
      .writeText(window.location.href)
      .then(() => {
        const original = btn.innerHTML;
        btn.innerHTML = '<i class="fa fa-check-circle"></i> URL Copied!';
        setTimeout(() => { btn.innerHTML = original; }, 2500);
      })
      .catch(() => {
        // Fallback for older browsers
        const tmp = document.createElement("textarea");
        tmp.value = window.location.href;
        document.body.appendChild(tmp);
        tmp.select();
        document.execCommand("copy");
        document.body.removeChild(tmp);
        btn.innerHTML = '<i class="fa fa-check-circle"></i> URL Copied!';
        setTimeout(() => {
          btn.innerHTML = '<i class="fa fa-share"></i> Share';
        }, 2500);
      });
  });
}

// ── Review form popup (Magnific Popup fallback) ───────────

function initReviewPopup(): void {
  const triggerBtn = document.querySelector<HTMLAnchorElement>("#add-review-button");
  const dialog = document.querySelector<HTMLElement>("#small-dialog");
  if (!triggerBtn || !dialog) return;

  // If Magnific Popup is loaded, it handles this via .popup-with-zoom-anim.
  // This is a typed CSS-only fallback overlay.
  triggerBtn.addEventListener("click", (e) => {
    if (typeof ($ as JQuery)?.fn?.magnificPopup === "undefined") {
      e.preventDefault();
      dialog.style.cssText =
        "display:block;position:fixed;inset:0;z-index:9999;" +
        "background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;";
      const inner = document.createElement("div");
      inner.style.cssText =
        "background:#fff;padding:30px;border-radius:8px;max-width:500px;width:90%;position:relative;";
      inner.innerHTML = dialog.innerHTML;
      const closeBtn = document.createElement("button");
      closeBtn.innerHTML = "✕";
      closeBtn.style.cssText =
        "position:absolute;top:10px;right:14px;border:none;background:none;" +
        "font-size:1.2rem;cursor:pointer;color:#aaa;";
      closeBtn.addEventListener("click", () => overlay.remove());
      inner.prepend(closeBtn);
      const overlay = document.createElement("div");
      overlay.style.cssText = "position:fixed;inset:0;z-index:9998;background:rgba(0,0,0,.6);" +
                               "display:flex;align-items:center;justify-content:center;";
      overlay.appendChild(inner);
      overlay.addEventListener("click", (ev) => {
        if (ev.target === overlay) overlay.remove();
      });
      document.body.appendChild(overlay);
    }
  });
}

// ── Main init ─────────────────────────────────────────────

export function initHotel(): void {
  renderStarRatings();
  initHotelSearch();
  initBookmarkButtons();
  initCardAnimations();
  initShareButton();
  initReviewPopup();
}
