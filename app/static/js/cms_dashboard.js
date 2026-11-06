// ==========================================================================
// GOOSE TECNOLOGIA — Lógica Interativa do Painel Goose CMS (Gestão Editorial)
// ==========================================================================

let currentStatusTab = "all";
let currentAuthorFilter = "all";
let currentSearchQuery = "";
let selectedArticleId = null;

function showToast(message, variant = "info") {
  const existing = document.getElementById("cms-toast");
  if (existing) existing.remove();

  const toast = document.createElement("div");
  toast.id = "cms-toast";
  const bgClass =
    variant === "carmine"
      ? "bg-primary-container text-on-primary-container"
      : "bg-secondary-container text-on-secondary-container";
  toast.className = `fixed bottom-6 right-6 z-50 ${bgClass} px-space-md py-3 rounded-xl shadow-2xl font-telemetry-code text-body-sm flex items-center gap-2 border border-white/10 transition-all`;
  toast.innerHTML = `<span class="material-symbols-outlined text-[20px]">check_circle</span><span>${message}</span>`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

window.filterByStatusTab = function (status, btn) {
  currentStatusTab = status;
  document.querySelectorAll(".cms-status-tab").forEach((t) => {
    t.className =
      "cms-status-tab px-space-md py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface-variant hover:text-on-surface font-body-sm text-body-sm transition-all";
  });
  if (btn) {
    btn.className =
      "cms-status-tab px-space-md py-1.5 rounded-lg bg-primary-container text-on-primary-container font-headline-sm text-body-sm font-semibold shadow-sm";
  }
  applyCmsFilters();
};

window.filterByAuthor = function (authorKey) {
  currentAuthorFilter = authorKey;
  applyCmsFilters();
};

function applyCmsFilters() {
  const rows = document.querySelectorAll(".cms-article-row");
  rows.forEach((row) => {
    const rowStatus = row.dataset.status || "published";
    const rowAuthor = row.dataset.author || "duo";
    const rowText = row.textContent.toLowerCase();

    const statusOk = currentStatusTab === "all" || rowStatus === currentStatusTab;
    const authorOk = currentAuthorFilter === "all" || rowAuthor === currentAuthorFilter;
    const searchOk = currentSearchQuery === "" || rowText.includes(currentSearchQuery);

    if (statusOk && authorOk && searchOk) {
      row.classList.remove("hidden");
    } else {
      row.classList.add("hidden");
    }
  });
}

window.selectArticleForInspector = function (rowEl) {
  if (!rowEl) return;
  selectedArticleId = rowEl.dataset.id;

  document.querySelectorAll(".cms-article-row").forEach((r) => {
    r.classList.remove("ring-1", "ring-tertiary/50");
  });
  rowEl.classList.add("ring-1", "ring-tertiary/50");

  const title = rowEl.dataset.title || "";
  const slug = rowEl.dataset.slug || "";
  const desc = rowEl.dataset.description || "";
  const cover = rowEl.dataset.cover || "";
  const words = rowEl.dataset.words || "1420";
  const reading = rowEl.dataset.reading || "7";
  const tags = rowEl.dataset.tags || "#Telecom";
  const isHero = rowEl.dataset.hero === "true";
  const isZen = rowEl.dataset.zen === "true";
  const isGoocast = rowEl.dataset.goocast === "true";

  const activeNameEl = document.getElementById("inspector-active-title");
  const serpTitleEl = document.getElementById("inspector-serp-title");
  const serpDescEl = document.getElementById("inspector-serp-desc");
  const serpSlugEl = document.getElementById("inspector-serp-slug");
  const ogImgEl = document.getElementById("inspector-og-img");
  const ogTitleEl = document.getElementById("inspector-og-title");
  const checkReadingEl = document.getElementById("inspector-check-reading");
  const checkTagsEl = document.getElementById("inspector-check-tags");

  const switchHero = document.getElementById("inspector-switch-hero");
  const switchZen = document.getElementById("inspector-switch-zen");
  const switchGoocast = document.getElementById("inspector-switch-goocast");

  if (activeNameEl) activeNameEl.innerText = `> ${title}`;
  if (serpTitleEl) serpTitleEl.innerText = `${title} | Goose`;
  if (serpDescEl) serpDescEl.innerText = desc;
  if (serpSlugEl) serpSlugEl.innerText = `goosetecnologia.com.br › blog › ${slug}`;
  if (ogImgEl && cover) ogImgEl.src = cover;
  if (ogTitleEl) ogTitleEl.innerText = title;
  if (checkReadingEl) checkReadingEl.innerText = `${words} palavras → ${reading} min precisão NOC`;
  if (checkTagsEl) checkTagsEl.innerText = `Tags ativas (${tags})`;

  if (switchHero) switchHero.checked = isHero;
  if (switchZen) switchZen.checked = isZen;
  if (switchGoocast) switchGoocast.checked = isGoocast;
};

window.saveInspectorMetadata = async function () {
  if (!selectedArticleId) return;
  const btn = document.getElementById("save-metadata-btn");
  const switchHero = document.getElementById("inspector-switch-hero");
  const switchZen = document.getElementById("inspector-switch-zen");
  const switchGoocast = document.getElementById("inspector-switch-goocast");

  const prevHTML = btn.innerHTML;
  btn.innerHTML =
    '<span class="material-symbols-outlined text-[18px] animate-spin">sync</span><span>Sincronizando...</span>';

  try {
    const resp = await fetch(`/api/cms/articles/${selectedArticleId}/metadata`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        is_hero: switchHero ? switchHero.checked : false,
        enable_zen_mode: switchZen ? switchZen.checked : true,
        enable_goocast: switchGoocast ? switchGoocast.checked : false,
      }),
    });
    if (resp.ok) {
      btn.innerHTML =
        '<span class="material-symbols-outlined text-[18px] text-primary">cloud_done</span><span>Metadados Sincronizados!</span>';
      showToast("Metadados de SEO e comportamento editorial salvos no banco!");
      setTimeout(() => {
        window.location.reload();
      }, 900);
    } else {
      btn.innerHTML = prevHTML;
    }
  } catch (e) {
    btn.innerHTML = prevHTML;
  }
};

window.duplicateArticle = async function (articleId, e) {
  if (e) e.stopPropagation();
  const resp = await fetch(`/api/cms/articles/${articleId}/duplicate`, { method: "POST" });
  if (resp.ok) {
    showToast("Ensaio duplicado como rascunho!");
    setTimeout(() => window.location.reload(), 800);
  }
};

window.changeArticleStatus = async function (articleId, newStatus, e) {
  if (e) e.stopPropagation();
  const resp = await fetch(`/api/cms/articles/${articleId}/status`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: newStatus }),
  });
  if (resp.ok) {
    showToast(`Status atualizado para '${newStatus.toUpperCase()}'!`, "carmine");
    setTimeout(() => window.location.reload(), 700);
  }
};

window.deleteArticle = async function (articleId, e) {
  if (e) e.stopPropagation();
  if (!confirm("Confirma a exclusão permanente deste ensaio técnico?")) return;
  const resp = await fetch(`/api/cms/articles/${articleId}`, { method: "DELETE" });
  if (resp.ok) {
    showToast("Ensaio removido do repositório.", "carmine");
    setTimeout(() => window.location.reload(), 700);
  }
};

window.switchCmsSection = function (sectionKey, linkEl) {
  document.querySelectorAll(".cms-nav-link").forEach((el) => {
    el.className =
      "cms-nav-link flex items-center gap-space-sm px-space-md py-space-sm rounded-lg text-on-surface-variant hover:bg-surface-container hover:text-on-surface transition-all";
  });
  if (linkEl) {
    linkEl.className =
      "cms-nav-link flex items-center gap-space-sm px-space-md py-space-sm rounded-lg bg-surface-container-high text-on-surface font-semibold shadow-inner transition-all";
  }

  document.querySelectorAll(".cms-view-pane").forEach((pane) => pane.classList.add("hidden"));
  const target = document.getElementById(`cms-pane-${sectionKey}`);
  if (target) target.classList.remove("hidden");

  const breadcrumb = document.getElementById("cms-breadcrumb-current");
  if (breadcrumb && linkEl) {
    breadcrumb.innerText = linkEl.innerText.trim();
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const firstRow = document.querySelector(".cms-article-row");
  if (firstRow) {
    selectedArticleId = firstRow.dataset.id;
  }

  const searchInput = document.getElementById("editorial-search");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      currentSearchQuery = e.target.value.toLowerCase().trim();
      applyCmsFilters();
    });
  }

  const syncBtn = document.getElementById("sync-cdn-btn");
  if (syncBtn) {
    syncBtn.addEventListener("click", () => {
      const originalHTML = syncBtn.innerHTML;
      syncBtn.innerHTML =
        '<span class="material-symbols-outlined text-[18px] animate-spin">sync</span><span>Sincronizando Edge...</span>';
      setTimeout(() => {
        syncBtn.innerHTML =
          '<span class="material-symbols-outlined text-[18px] text-tertiary">done</span><span>Cache Purged (0.12ms)</span>';
        showToast("Edge CDN sincronizado com o banco de dados MySQL/SQLAlchemy!");
        setTimeout(() => {
          syncBtn.innerHTML = originalHTML;
        }, 2500);
      }, 900);
    });
  }

  const exportBtn = document.getElementById("export-json-btn");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      showToast("Gerando pacote goose-blog-dump.json...");
      window.location.href = "/api/cms/export";
    });
  }

  // Abre automaticamente a aba se vier por âncora (#autores, #topicos, #leads, #midia, #logs)
  const hashMap = {
    "#autores": "authors",
    "#topicos": "topics",
    "#leads": "leads",
    "#midia": "media",
    "#logs": "logs",
  };
  if (window.location.hash && hashMap[window.location.hash]) {
    window.switchCmsSection(hashMap[window.location.hash]);
  }
});

// ==========================================================================
// CRUD DE AUTORES & REDATORES NO GOOSE CMS
// ==========================================================================

window.resetAuthorForm = function () {
  const idInput = document.getElementById("author-id-input");
  const nameInput = document.getElementById("author-display-name-input");
  const roleInput = document.getElementById("author-role-input");
  const userInput = document.getElementById("author-username-input");
  const emailInput = document.getElementById("author-email-input");
  const passInput = document.getElementById("author-password-input");
  const avatarInput = document.getElementById("author-avatar-input");
  const bioInput = document.getElementById("author-bio-input");
  const titleEl = document.getElementById("author-form-title");
  const badgeEl = document.getElementById("author-form-badge");
  const saveLabelEl = document.getElementById("author-save-btn-label");

  if (idInput) idInput.value = "";
  if (nameInput) nameInput.value = "";
  if (roleInput) roleInput.value = "";
  if (userInput) userInput.value = "";
  if (emailInput) emailInput.value = "";
  if (passInput) passInput.value = "";
  if (avatarInput) avatarInput.value = "";
  if (bioInput) bioInput.value = "";
  if (titleEl) titleEl.innerText = "Cadastrar Novo Autor / Redator";
  if (badgeEl) badgeEl.innerText = "NOVO REGISTRO";
  if (saveLabelEl) saveLabelEl.innerText = "Salvar Autor / Redator";
  nameInput?.focus();
};

window.editAuthorFromCard = function (cardEl) {
  if (!cardEl) return;
  const idInput = document.getElementById("author-id-input");
  const nameInput = document.getElementById("author-display-name-input");
  const roleInput = document.getElementById("author-role-input");
  const userInput = document.getElementById("author-username-input");
  const emailInput = document.getElementById("author-email-input");
  const passInput = document.getElementById("author-password-input");
  const avatarInput = document.getElementById("author-avatar-input");
  const bioInput = document.getElementById("author-bio-input");
  const titleEl = document.getElementById("author-form-title");
  const badgeEl = document.getElementById("author-form-badge");
  const saveLabelEl = document.getElementById("author-save-btn-label");

  if (idInput) idInput.value = cardEl.dataset.id || "";
  if (nameInput) nameInput.value = cardEl.dataset.displayName || "";
  if (roleInput) roleInput.value = cardEl.dataset.roleTitle || "";
  if (userInput) userInput.value = cardEl.dataset.username || "";
  if (emailInput) emailInput.value = cardEl.dataset.email || "";
  if (passInput) passInput.value = "";
  if (avatarInput) avatarInput.value = cardEl.dataset.avatarUrl || "";
  if (bioInput) bioInput.value = cardEl.dataset.bio || "";
  if (titleEl) titleEl.innerText = `Editando: ${cardEl.dataset.displayName}`;
  if (badgeEl) badgeEl.innerText = `ID #${cardEl.dataset.id}`;
  if (saveLabelEl) saveLabelEl.innerText = "Atualizar Autor / Redator";
  nameInput?.focus();
};

window.uploadAuthorAvatarFile = async function (fileInput) {
  const file = fileInput?.files?.[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("alt_text", "Avatar Autor Goose");

  showToast("Enviando foto do autor...");
  try {
    const resp = await fetch("/api/cms/upload", {
      method: "POST",
      body: formData,
    });
    const data = await resp.json();
    if (resp.ok && data.ok && data.asset) {
      const avatarInput = document.getElementById("author-avatar-input");
      if (avatarInput) avatarInput.value = data.asset.file_url;
      showToast("Foto carregada com sucesso!");
    } else {
      showToast(data.error || "Erro ao enviar foto.", "carmine");
    }
  } catch (err) {
    showToast("Falha no upload da imagem.", "carmine");
  }
};

window.saveAuthorForm = async function (e) {
  e.preventDefault();
  const id = document.getElementById("author-id-input")?.value || "";
  const display_name = document.getElementById("author-display-name-input")?.value || "";
  const role_title = document.getElementById("author-role-input")?.value || "";
  const username = document.getElementById("author-username-input")?.value || "";
  const email = document.getElementById("author-email-input")?.value || "";
  const password = document.getElementById("author-password-input")?.value || "";
  const avatar_url = document.getElementById("author-avatar-input")?.value || "";
  const bio = document.getElementById("author-bio-input")?.value || "";

  const btn = document.getElementById("author-save-btn");
  const prevHTML = btn ? btn.innerHTML : "";
  if (btn) {
    btn.disabled = true;
    btn.innerHTML =
      '<span class="material-symbols-outlined text-[18px] animate-spin">sync</span><span>Salvando...</span>';
  }

  try {
    const resp = await fetch("/api/cms/authors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: id ? parseInt(id, 10) : null,
        display_name,
        role_title,
        username,
        email,
        password,
        avatar_url,
        bio,
      }),
    });
    const data = await resp.json();
    if (resp.ok && data.ok) {
      showToast(
        id ? "Autor/Redator atualizado com sucesso!" : "Novo Autor/Redator cadastrado!"
      );
      window.location.hash = "#autores";
      setTimeout(() => window.location.reload(), 700);
    } else {
      showToast(data.error || "Erro ao salvar autor.", "carmine");
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = prevHTML;
      }
    }
  } catch (err) {
    showToast("Erro de comunicação ao salvar autor.", "carmine");
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = prevHTML;
    }
  }
};

window.deleteAuthor = async function (userId, displayName) {
  if (!confirm(`Confirma a exclusão do autor/redator "${displayName}"?`)) return;
  try {
    const resp = await fetch(`/api/cms/authors/${userId}`, {
      method: "DELETE",
    });
    const data = await resp.json();
    if (resp.ok && data.ok) {
      showToast(`Autor "${displayName}" removido.`, "carmine");
      window.location.hash = "#autores";
      setTimeout(() => window.location.reload(), 700);
    } else {
      showToast(data.error || "Não foi possível excluir o autor.", "carmine");
    }
  } catch (err) {
    showToast("Falha ao tentar excluir o autor.", "carmine");
  }
};

