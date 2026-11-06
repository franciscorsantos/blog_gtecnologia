// ==========================================================================
// GOOSE TECNOLOGIA — Lógica Interativa da Home do Blog Minimalista
// ==========================================================================

let currentSearchTerm = "";
let activeFilterCat = "all";
window.currentSortOrder = "recent";
window.zenModeActive = false;

function updateReadingProgress() {
  const winScroll = window.scrollY || document.documentElement.scrollTop;
  const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
  const scrolled = height > 0 ? Math.min(100, Math.max(0, (winScroll / height) * 100)) : 0;

  const progressBar = document.getElementById("reading-progress-bar");
  const percentEl = document.getElementById("reading-progress-percent");
  const timeEl = document.getElementById("reading-time-remaining");
  const badge = document.getElementById("reading-progress-badge");

  if (progressBar) progressBar.style.width = scrolled + "%";
  if (percentEl) percentEl.innerText = Math.round(scrolled) + "%";

  if (badge) {
    if (winScroll > 60) {
      badge.classList.remove("opacity-0");
      badge.classList.add("opacity-100");
    } else {
      badge.classList.remove("opacity-100");
      badge.classList.add("opacity-0");
    }
  }

  if (timeEl) {
    const totalMin = 7;
    const rem = Math.max(1, Math.ceil(totalMin * (1 - scrolled / 100)));
    if (scrolled >= 98) {
      timeEl.innerText = "Leitura concluída";
    } else {
      timeEl.innerText = `~${rem} min rest.`;
    }
  }
}

window.toggleZenMode = function () {
  window.zenModeActive = !window.zenModeActive;
  const body = document.body;
  const zenBar = document.getElementById("zen-floating-bar");
  const zenBtn = document.getElementById("zen-mode-toggle-btn");
  const articlesSec = document.getElementById("artigos");
  const dividers = document.querySelectorAll("main > div.w-full.flex");
  const heroSec = document.querySelector("main > section");
  const footer = document.querySelector("footer");

  if (window.zenModeActive) {
    body.classList.add("zen-active");
    if (zenBar) {
      zenBar.classList.remove("hidden");
      zenBar.classList.add("flex");
    }
    if (articlesSec) articlesSec.classList.add("hidden");
    dividers.forEach((d) => d.classList.add("hidden"));
    if (footer) footer.classList.add("hidden");
    if (heroSec) heroSec.classList.add("max-w-3xl", "mx-auto", "transition-all");
    if (zenBtn) zenBtn.classList.add("border-[#296B96]", "text-white", "bg-[#296B96]/20");
  } else {
    body.classList.remove("zen-active");
    if (zenBar) {
      zenBar.classList.add("hidden");
      zenBar.classList.remove("flex");
    }
    if (articlesSec) articlesSec.classList.remove("hidden");
    dividers.forEach((d) => d.classList.remove("hidden"));
    if (footer) footer.classList.remove("hidden");
    if (heroSec) heroSec.classList.remove("max-w-3xl", "mx-auto");
    if (zenBtn) zenBtn.classList.remove("border-[#296B96]", "text-white", "bg-[#296B96]/20");
  }
};

window.filterCategory = function (cat, element) {
  activeFilterCat = cat;
  document.querySelectorAll(".cat-pill").forEach((btn) => {
    btn.classList.remove("border-[#E12B4A]", "text-white", "bg-[#E12B4A]/10");
    btn.classList.add("border-[#1C2742]", "text-[#8E9EB5]");
  });
  if (element) {
    element.classList.add("border-[#E12B4A]", "text-white", "bg-[#E12B4A]/10");
    element.classList.remove("border-[#1C2742]", "text-[#8E9EB5]");
  }
  applyArticleFilters();
};

window.searchArticles = function (term) {
  currentSearchTerm = (term || "").trim().toLowerCase();
  const clearBtn = document.getElementById("clear-search-btn");
  if (clearBtn) {
    if (currentSearchTerm.length > 0) {
      clearBtn.classList.remove("hidden");
    } else {
      clearBtn.classList.add("hidden");
    }
  }
  document.querySelectorAll(".quick-tag-pill").forEach((pill) => {
    const tagVal = pill.innerText.replace("#", "").toLowerCase();
    if (currentSearchTerm.length > 0 && currentSearchTerm.includes(tagVal)) {
      pill.classList.add("border-[#296B96]", "text-white", "bg-[#296B96]/20");
      pill.classList.remove("text-[#8E9EB5]", "border-[#1C2742]");
    } else {
      pill.classList.remove("border-[#296B96]", "text-white", "bg-[#296B96]/20");
      pill.classList.add("text-[#8E9EB5]", "border-[#1C2742]");
    }
  });
  applyArticleFilters();
};

window.quickTagSearch = function (tag) {
  const input = document.getElementById("article-search-input");
  if (input) {
    input.value = tag;
    window.searchArticles(tag);
  }
};

window.clearArticleSearch = function () {
  const input = document.getElementById("article-search-input");
  if (input) input.value = "";
  window.searchArticles("");
};

window.sortArticles = function (order, btn) {
  window.currentSortOrder = order;
  document.querySelectorAll(".sort-pill").forEach((p) => {
    p.className =
      "sort-pill px-2.5 py-1 rounded text-[11px] font-mono border border-transparent text-[#8E9EB5] hover:text-white hover:border-[#1C2742] transition-all";
  });
  if (btn) {
    btn.className =
      "sort-pill px-2.5 py-1 rounded text-[11px] font-mono border border-[#296B96] text-white bg-[#296B96]/20 transition-all";
  }
  const container = document.getElementById("articles-container");
  if (!container) return;
  const items = Array.from(container.querySelectorAll(".article-item"));
  items.sort((a, b) => {
    if (order === "popular") {
      return (parseInt(b.dataset.views) || 0) - (parseInt(a.dataset.views) || 0);
    }
    return new Date(b.dataset.date).getTime() - new Date(a.dataset.date).getTime();
  });
  items.forEach((item) => container.appendChild(item));
  applyArticleFilters();
};

function applyArticleFilters() {
  const articles = document.querySelectorAll(".article-item");
  let visibleCount = 0;
  articles.forEach((art) => {
    const matchesCategory = activeFilterCat === "all" || art.dataset.category === activeFilterCat;
    const contentText = (art.innerText + " " + (art.dataset.tags || "")).toLowerCase();
    const matchesSearch = currentSearchTerm === "" || contentText.includes(currentSearchTerm);
    if (matchesCategory && matchesSearch) {
      art.style.display = "flex";
      visibleCount++;
    } else {
      art.style.display = "none";
    }
  });
  const counter = document.getElementById("articles-counter");
  if (counter) {
    counter.innerText = visibleCount + (visibleCount === 1 ? " artigo" : " artigos");
  }
  const noRes = document.getElementById("search-no-results");
  if (noRes) {
    if (visibleCount === 0) {
      noRes.classList.remove("hidden");
      noRes.classList.add("flex");
    } else {
      noRes.classList.add("hidden");
      noRes.classList.remove("flex");
    }
  }
}

window.openArticleModal = async function (slug) {
  const modal = document.getElementById("article-modal");
  if (!modal) return;

  if (slug) {
    try {
      const resp = await fetch(`/api/articles/${encodeURIComponent(slug)}`);
      if (resp.ok) {
        const data = await resp.json();
        const titleEl = document.getElementById("modal-article-title");
        const authorEl = document.getElementById("modal-article-author");
        const timeEl = document.getElementById("modal-article-time");
        const bodyEl = document.getElementById("modal-article-body");
        const fullLinkEl = document.getElementById("modal-full-article-link");

        if (titleEl) titleEl.innerText = data.title;
        if (authorEl) authorEl.innerText = data.author_display;
        if (timeEl) timeEl.innerText = `${data.reading_time_minutes} minutos de leitura`;
        if (bodyEl) bodyEl.innerHTML = data.rendered_html;
        if (fullLinkEl) fullLinkEl.href = `/blog/${data.slug}`;
      }
    } catch (e) {
      console.error("Erro ao carregar preview do ensaio:", e);
    }
  }
  modal.classList.remove("hidden");
};

window.copyCodeSnippet = function (btn, blockId) {
  let codeText = "";
  if (blockId) {
    const el = document.getElementById(blockId);
    if (el) codeText = el.innerText;
  } else if (btn.nextElementSibling) {
    codeText = btn.nextElementSibling.innerText;
  }
  if (codeText) {
    navigator.clipboard.writeText(codeText);
  }
  const textSpan = btn.querySelector(".copy-text");
  if (textSpan) {
    const orig = textSpan.innerText;
    textSpan.innerText = "Copiado!";
    setTimeout(() => {
      textSpan.innerText = orig;
    }, 1800);
  } else {
    const orig = btn.innerText;
    btn.innerText = "Copiado!";
    setTimeout(() => {
      btn.innerText = orig;
    }, 1800);
  }
};

window.handleLeadSubmit = async function (e) {
  e.preventDefault();
  const form = e.currentTarget;
  const btn = document.getElementById("lead-submit-btn");
  const name = form.querySelector('[name="name"]')?.value || "";
  const isp_asn = form.querySelector('[name="isp_asn"]')?.value || "";
  const whatsapp = form.querySelector('[name="whatsapp"]')?.value || "";

  if (btn) {
    btn.disabled = true;
    btn.innerText = "Enviando...";
  }

  try {
    const resp = await fetch("/api/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name,
        isp_asn,
        whatsapp,
        source_page: window.location.pathname,
      }),
    });
    if (resp.ok && btn) {
      btn.innerText = "Enviado com Sucesso!";
      btn.classList.remove("bg-[#E12B4A]");
      btn.classList.add("bg-[#296B96]");
      setTimeout(() => {
        document.getElementById("vip-modal")?.classList.add("hidden");
        form.reset();
        btn.disabled = false;
        btn.innerText = "Enviar Mensagem";
        btn.classList.add("bg-[#E12B4A]");
        btn.classList.remove("bg-[#296B96]");
      }, 1500);
    }
  } catch (err) {
    if (btn) {
      btn.disabled = false;
      btn.innerText = "Enviar Mensagem";
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  window.addEventListener("scroll", updateReadingProgress, { passive: true });
  updateReadingProgress();

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (window.zenModeActive) window.toggleZenMode();
      document.getElementById("article-modal")?.classList.add("hidden");
      document.getElementById("vip-modal")?.classList.add("hidden");
    }
  });

  const backToTopBtn = document.getElementById("back-to-top");
  if (backToTopBtn) {
    window.addEventListener(
      "scroll",
      () => {
        if (window.scrollY > 300) {
          backToTopBtn.classList.remove("opacity-0", "pointer-events-none");
          backToTopBtn.classList.add("opacity-100", "pointer-events-auto");
        } else {
          backToTopBtn.classList.add("opacity-0", "pointer-events-none");
          backToTopBtn.classList.remove("opacity-100", "pointer-events-auto");
        }
      },
      { passive: true }
    );
  }
});

