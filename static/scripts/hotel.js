/**
 * Red HMS – Hotel & Listing Module
 * Compiled from src/ts/hotel.ts
 */
import { showToast } from "./utils.js";

function renderStarRatings() {
  document.querySelectorAll(".utf_star_rating_section[data-rating]").forEach((el) => {
    const rawRating = parseFloat(el.dataset.rating || "0");
    if (!rawRating) return;
    const container = document.createElement("div");
    container.className = "utf_star_rating_stars";
    for (let i = 1; i <= 5; i++) {
      const star = document.createElement("i");
      star.className = rawRating >= i ? "fa fa-star" : rawRating >= i - 0.5 ? "fa fa-star-half-o" : "fa fa-star-o";
      star.style.color = "#c0392b"; star.style.fontSize = "13px";
      container.appendChild(star);
    }
    const counter = el.querySelector(".utf_counter_star_rating");
    if (counter) el.insertBefore(container, counter);
  });
}

function initHotelSearch() {
  const searchInput = document.querySelector("#hotel-search-input");
  const cards = document.querySelectorAll(".utf_listing_item-container, .hotel-card");
  if (!searchInput || cards.length === 0) return;
  searchInput.addEventListener("input", () => {
    const q = searchInput.value.toLowerCase().trim();
    let count = 0;
    cards.forEach((card) => {
      const visible = !q || card.textContent?.toLowerCase().includes(q);
      card.style.display = visible ? "" : "none";
      if (visible) count++;
    });
    const el = document.querySelector("#search-result-count");
    if (el) el.textContent = `${count} hotel(s) found`;
  });
}

async function toggleBookmark(slug, heartIcon) {
  heartIcon.style.opacity = "0.5";
  try {
    const response = await fetch(`/guests/bookmark/${slug}/`, {
      method: "GET", headers: { "X-Requested-With": "XMLHttpRequest" },
    });
    if (response.redirected) { window.location.href = response.url; return; }
    const isRed = heartIcon.style.color === "rgb(192, 57, 43)" || heartIcon.style.color === "#c0392b";
    if (isRed) { heartIcon.style.color = "#aaa"; showToast("info", "Removed from wishlist."); }
    else {
      heartIcon.style.color = "#c0392b"; showToast("success", "Saved to wishlist!");
      heartIcon.style.transform = "scale(1.4)";
      setTimeout(() => { heartIcon.style.transform = "scale(1)"; }, 300);
    }
  } catch { showToast("error", "Could not update wishlist."); }
  finally { heartIcon.style.opacity = "1"; }
}

function initBookmarkButtons() {
  document.querySelectorAll("[data-bookmark-slug]").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const icon = btn.querySelector("i.fa-heart") || btn;
      icon.style.transition = "color .2s, transform .3s";
      void toggleBookmark(btn.dataset.bookmarkSlug || "", icon);
    });
  });
}

function initCardAnimations() {
  const cards = document.querySelectorAll(".utf_listing_item-container, .utf_dashboard_stat");
  const style = document.createElement("style");
  style.textContent = `.fade-in-up { opacity: 1 !important; transform: translateY(0) !important; }`;
  document.head.appendChild(style);
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) { entry.target.classList.add("fade-in-up"); observer.unobserve(entry.target); }
    });
  }, { threshold: 0.1, rootMargin: "0px 0px -40px 0px" });
  cards.forEach((card) => {
    card.style.opacity = "0"; card.style.transform = "translateY(20px)";
    card.style.transition = "opacity .4s ease, transform .4s ease";
    observer.observe(card);
  });
}

function initShareButton() {
  const btn = document.querySelector("#clipboard");
  if (!btn) return;
  btn.addEventListener("click", (e) => {
    e.preventDefault();
    const restore = () => setTimeout(() => { btn.innerHTML = '<i class="fa fa-share"></i> Share'; }, 2500);
    navigator.clipboard.writeText(window.location.href)
      .then(() => { btn.innerHTML = '<i class="fa fa-check-circle"></i> URL Copied!'; restore(); })
      .catch(() => {
        const tmp = document.createElement("textarea");
        tmp.value = window.location.href;
        document.body.appendChild(tmp); tmp.select(); document.execCommand("copy"); document.body.removeChild(tmp);
        btn.innerHTML = '<i class="fa fa-check-circle"></i> URL Copied!'; restore();
      });
  });
}

export function initHotel() {
  renderStarRatings();
  initHotelSearch();
  initBookmarkButtons();
  initCardAnimations();
  initShareButton();
}
