// ==========================================================================
// GOOSE TECNOLOGIA — Lógica Interativa do Editor Markdown & Ensaio Técnico
// ==========================================================================

let previewDebounceTimer = null;

function showEditorNotification(msg, isError = false) {
  const existing = document.getElementById("editor-toast");
  if (existing) existing.remove();

  const el = document.createElement("div");
  el.id = "editor-toast";
  el.className = `fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-2xl font-telemetry-code text-body-sm flex items-center gap-2 border border-white/10 ${
    isError ? "bg-error-container text-on-error-container" : "bg-secondary-container text-on-secondary-container"
  }`;
  el.innerHTML = `<span class="material-symbols-outlined text-[18px]">${
    isError ? "error" : "check_circle"
  }</span><span>${msg}</span>`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

window.switchView = function (mode) {
  const editorCol = document.getElementById("markdown-col");
  const previewCol = document.getElementById("preview-col");
  const container = document.getElementById("editor-preview-container");
  const btnSplit = document.getElementById("view-split");
  const btnEditor = document.getElementById("view-editor");
  const btnPreview = document.getElementById("view-preview");

  [btnSplit, btnEditor, btnPreview].forEach((btn) => {
    if (btn) {
      btn.className =
        "flex items-center gap-1.5 px-3 py-1.5 rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container/50 font-telemetry-code text-body-sm transition-all";
    }
  });

  if (mode === "split") {
    container.className =
      "col-span-12 xl:col-span-9 grid grid-cols-1 lg:grid-cols-2 gap-space-md transition-all duration-300";
    editorCol.style.display = "flex";
    previewCol.style.display = "flex";
    if (btnSplit) {
      btnSplit.className =
        "flex items-center gap-1.5 px-3 py-1.5 rounded text-on-surface bg-surface-container font-telemetry-code text-body-sm font-semibold shadow-sm transition-all";
    }
  } else if (mode === "editor") {
    container.className =
      "col-span-12 xl:col-span-9 grid grid-cols-1 gap-space-md transition-all duration-300";
    editorCol.style.display = "flex";
    previewCol.style.display = "none";
    if (btnEditor) {
      btnEditor.className =
        "flex items-center gap-1.5 px-3 py-1.5 rounded text-on-surface bg-surface-container font-telemetry-code text-body-sm font-semibold shadow-sm transition-all";
    }
  } else if (mode === "preview") {
    container.className =
      "col-span-12 xl:col-span-9 grid grid-cols-1 gap-space-md transition-all duration-300";
    editorCol.style.display = "none";
    previewCol.style.display = "flex";
    if (btnPreview) {
      btnPreview.className =
        "flex items-center gap-1.5 px-3 py-1.5 rounded text-on-surface bg-surface-container font-telemetry-code text-body-sm font-semibold shadow-sm transition-all";
    }
  }
};

window.toggleZen = function () {
  const sidebar = document.getElementById("metadata-sidebar");
  const container = document.getElementById("editor-preview-container");
  if (!sidebar || !container) return;

  if (sidebar.style.display === "none") {
    sidebar.style.display = "flex";
    container.classList.remove("xl:col-span-12");
    container.classList.add("xl:col-span-9");
  } else {
    sidebar.style.display = "none";
    container.classList.remove("xl:col-span-9");
    container.classList.add("xl:col-span-12");
  }
};

window.toggleSidebar = function () {
  window.toggleZen();
};

window.togglePublishDropdown = function () {
  const dd = document.getElementById("publish-dropdown");
  if (dd) dd.classList.toggle("hidden");
};

window.switchMetaTab = function (tabName) {
  const tabs = ["editorial", "cover", "checks"];
  tabs.forEach((t) => {
    const pane = document.getElementById("pane-" + t);
    const btn = document.getElementById("tab-" + t);
    if (!pane || !btn) return;
    if (t === tabName) {
      pane.classList.remove("hidden");
      pane.classList.add("flex");
      btn.className =
        "flex-1 py-1.5 px-2 rounded-lg bg-surface-container font-headline-sm text-[12px] font-bold text-on-surface text-center transition-all shadow-sm";
    } else {
      pane.classList.remove("flex");
      pane.classList.add("hidden");
      btn.className =
        "flex-1 py-1.5 px-2 rounded-lg text-on-surface-variant hover:text-on-surface font-headline-sm text-[12px] font-semibold text-center transition-all";
    }
  });
};

function updateLineNumbers() {
  const textarea = document.getElementById("markdown-textarea");
  const gutter = document.getElementById("line-numbers-gutter");
  const cursorStat = document.getElementById("editor-cursor-stat");
  if (!textarea || !gutter) return;

  const linesCount = Math.max(32, textarea.value.split("\n").length);
  let html = "";
  for (let i = 1; i <= linesCount; i++) {
    html += `<span>${String(i).padStart(2, "0")}</span>`;
  }
  gutter.innerHTML = html;

  if (cursorStat) {
    const upto = textarea.value.slice(0, textarea.selectionStart || 0);
    const lines = upto.split("\n");
    const ln = lines.length;
    const col = lines[lines.length - 1].length + 1;
    cursorStat.innerText = `Ln ${ln}, Col ${col}`;
  }
}

async function refreshLivePreview() {
  const textarea = document.getElementById("markdown-textarea");
  const titleInput = document.getElementById("editor-title-input");
  if (!textarea) return;

  try {
    const resp = await fetch("/api/cms/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content_markdown: textarea.value }),
    });
    if (!resp.ok) return;
    const data = await resp.json();

    const previewBody = document.getElementById("live-preview-body");
    const previewTitle = document.getElementById("live-preview-title");
    const wordCounter = document.getElementById("stat-words-count");
    const readingCounter = document.getElementById("stat-reading-time");
    const scriptsCounter = document.getElementById("stat-scripts-count");
    const autosaveLabel = document.getElementById("autosave-status-label");

    if (previewBody) previewBody.innerHTML = data.rendered_html;
    if (previewTitle && titleInput) previewTitle.innerText = titleInput.value;
    if (wordCounter) wordCounter.innerText = `${data.word_count} palavras`;
    if (readingCounter) readingCounter.innerText = `~${data.reading_time_minutes} min de leitura`;
    if (scriptsCounter) scriptsCounter.innerText = `${data.script_blocks_count} blocos de script`;
    if (autosaveLabel) autosaveLabel.innerText = "Rascunho salvo localmente (agora)";

    localStorage.setItem("goose_editor_buffer", textarea.value);
  } catch (err) {
    console.error("Erro no preview live:", err);
  }
}

window.insertMarkdownSnippet = function (type) {
  const textarea = document.getElementById("markdown-textarea");
  if (!textarea) return;

  const snippets = {
    h1: "\n# Título Principal do Ensaio\n",
    h2: "\n## Nova Seção Técnica\n",
    h3: "\n### Subtópico de Arquitetura\n",
    bold: "**destaque técnico**",
    italic: "*termo de protocolo*",
    quote: "\n> Nota de Engenharia: mantenha o anúncio de prefixos /22 agregados no eBGP.\n",
    list: "\n* Roteador de Borda CCR2216\n* Sessão eBGP + BFD Ativo\n* Peering IX.br Regional\n",
    link: "[Documentação RFC 1997](https://datatracker.ietf.org/doc/html/rfc1997)",
    "script-mikrotik":
      '\n```mikrotik|MikroTik RouterOS v7 Script\n/routing bgp template\nadd name="GOOSE-TRANSITO" as=263481 router-id=187.60.10.1 use-bfd=yes\n\n/routing filter rule\nadd chain="IXBR-IN" rule="if (bgp-communities includes 26162:*) { set bgp-local-pref 200; accept; }"\n```\n',
    "script-bgp":
      '\n```bgp|BGP Bird2 / FRR Routing Conf\nprotocol bgp TRANSITO_TIER1 {\n    local as 263481;\n    neighbor 177.10.20.1 as 6762;\n    bfd on;\n}\n```\n',
    "script-cgnat":
      '\n```bash|Linux nftables / CGNAT Deterministic PBA\nnft add rule ip nat POSTROUTING ip saddr 100.64.0.0/22 snat to 187.60.12.0/24 persistent\n```\n',
    "script-python":
      '\n```python|Python Netmiko / Automação de Borda\nfrom netmiko import ConnectHandler\nconn = ConnectHandler(device_type="mikrotik_routeros", host="10.254.0.1", username="noc", password="***")\nprint(conn.send_command("/routing bgp session print"))\n```\n',
    "script-json":
      '\n```json|JSON Optical Telemetry Readout\n{\n  "olt_slot": "GPON-0/1/4",\n  "rx_power_dbm": -18.4,\n  "bfd_status": "UP_148MS"\n}\n```\n',
    topology: "\n:::topology-bgp:::\n",
    "noc-alert":
      "\n:::noc-warning\ntitle: Aviso Crítico de Operação em Produção (NOC)\nValide o buffer de rotas e aplique os filtros BGP antes de estabelecer a sessão em horário de pico.\n:::\n",
    benchmark:
      "\n| Operadora | Comunidade | Ação Executada no Backbone | Eficácia Goose |\n| :--- | :--- | :--- | ---: |\n| **Lumen (CenturyLink)** | `3549:2000` | Aplica Local-Pref 70 em nós internacionais | **99.8%** |\n| **Telxius (Telefônica)** | `12956:0` | Não anunciar rota para pares IX europeus | **100%** |\n",
    goocast:
      "\n> **GOOCAST #28 Integrado**: *Episódio sincronizado no player de áudio superior deste artigo.*\n",
  };

  const insertion = snippets[type] || "";
  const start = textarea.selectionStart || 0;
  const end = textarea.selectionEnd || 0;
  textarea.value = textarea.value.substring(0, start) + insertion + textarea.value.substring(end);
  textarea.focus();
  textarea.selectionStart = textarea.selectionEnd = start + insertion.length;

  updateLineNumbers();
  refreshLivePreview();
};

// Gerenciamento de Tags no Sidebar
window.removeEditorTag = function (tagSpan) {
  tagSpan.remove();
  updateTagsCountBadge();
};

function updateTagsCountBadge() {
  const count = document.querySelectorAll("#editor-tags-list .editor-tag-chip").length;
  const badge = document.getElementById("editor-tags-count");
  if (badge) badge.innerText = `${count} ativas`;
}

function getEditorTagsArray() {
  return Array.from(document.querySelectorAll("#editor-tags-list .editor-tag-chip")).map((el) =>
    el.dataset.tagName.trim()
  );
}

window.saveArticleFromEditor = async function (targetStatus = null) {
  const articleIdEl = document.getElementById("editor-article-id");
  const titleInput = document.getElementById("editor-title-input");
  const slugInput = document.getElementById("editor-slug-input");
  const textarea = document.getElementById("markdown-textarea");
  const authorSelect = document.getElementById("editor-author-select");
  const pubDateInput = document.getElementById("editor-pubdate-input");
  const categorySelect = document.getElementById("editor-category-select");
  const metaDescInput = document.getElementById("editor-metadesc-input");
  const coverUrlInput = document.getElementById("editor-cover-url-input");
  const switchHero = document.getElementById("editor-switch-hero");
  const switchZen = document.getElementById("editor-switch-zen");
  const switchGoocast = document.getElementById("editor-switch-goocast");

  const statusToSave =
    targetStatus || document.getElementById("editor-current-status")?.value || "published";

  const payload = {
    id: articleIdEl?.value ? parseInt(articleIdEl.value, 10) : null,
    title: titleInput?.value || "",
    slug: slugInput?.value || "",
    content_markdown: textarea?.value || "",
    status: statusToSave,
    author_key: authorSelect?.value || "duo",
    published_at: pubDateInput?.value || "",
    category_id: categorySelect?.value ? parseInt(categorySelect.value, 10) : null,
    meta_description: metaDescInput?.value || "",
    cover_image_url: coverUrlInput?.value || "",
    is_hero: switchHero ? switchHero.checked : false,
    enable_zen_mode: switchZen ? switchZen.checked : true,
    enable_goocast: switchGoocast ? switchGoocast.checked : false,
    tags: getEditorTagsArray(),
  };

  try {
    const resp = await fetch("/api/cms/articles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!resp.ok || !data.ok) {
      showEditorNotification(data.error || "Falha ao salvar o ensaio.", true);
      return;
    }

    if (articleIdEl && data.article?.id) {
      articleIdEl.value = data.article.id;
    }
    const slugDisplay = document.getElementById("permalink-slug-display");
    if (slugDisplay && data.article?.slug) {
      slugDisplay.innerText = data.article.slug;
    }
    if (slugInput && data.article?.slug) {
      slugInput.value = data.article.slug;
    }

    document.getElementById("publish-dropdown")?.classList.add("hidden");
    showEditorNotification(
      statusToSave === "published"
        ? "Ensaio publicado e sincronizado no Blog Público!"
        : `Ensaio salvo com status '${statusToSave.toUpperCase()}'!`
    );
  } catch (err) {
    showEditorNotification("Erro de comunicação ao salvar o artigo.", true);
  }
};

window.triggerCoverUpload = function () {
  const fileInput = document.getElementById("cover-file-upload-input");
  if (fileInput) fileInput.click();
};

document.addEventListener("DOMContentLoaded", () => {
  const textarea = document.getElementById("markdown-textarea");
  const titleInput = document.getElementById("editor-title-input");
  const slugInput = document.getElementById("editor-slug-input");
  const metaDescInput = document.getElementById("editor-metadesc-input");
  const addTagInput = document.getElementById("editor-add-tag-input");
  const fileInput = document.getElementById("cover-file-upload-input");

  if (textarea) {
    updateLineNumbers();
    textarea.addEventListener("input", () => {
      updateLineNumbers();
      clearTimeout(previewDebounceTimer);
      previewDebounceTimer = setTimeout(refreshLivePreview, 250);
    });
    textarea.addEventListener("click", updateLineNumbers);
    textarea.addEventListener("keyup", updateLineNumbers);
  }

  if (titleInput) {
    titleInput.addEventListener("input", () => {
      const previewTitle = document.getElementById("live-preview-title");
      const ogTitle = document.getElementById("editor-og-title-preview");
      if (previewTitle) previewTitle.innerText = titleInput.value;
      if (ogTitle) ogTitle.innerText = titleInput.value;
    });
  }

  if (slugInput) {
    slugInput.addEventListener("input", () => {
      const slugDisplay = document.getElementById("permalink-slug-display");
      if (slugDisplay) slugDisplay.innerText = slugInput.value;
    });
  }

  if (metaDescInput) {
    const countEl = document.getElementById("metadesc-char-count");
    const updateCount = () => {
      if (countEl) countEl.innerText = `${metaDescInput.value.length} / 160 chars`;
    };
    metaDescInput.addEventListener("input", updateCount);
    updateCount();
  }

  if (addTagInput) {
    addTagInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const val = addTagInput.value.trim().replace(/^#/, "");
        if (!val) return;
        const container = document.getElementById("editor-tags-list");
        if (container) {
          const span = document.createElement("span");
          span.className =
            "editor-tag-chip flex items-center gap-1 px-2 py-0.5 rounded bg-surface-container text-secondary font-telemetry-code text-[11px]";
          span.dataset.tagName = val;
          span.innerHTML = `#${val} <span class="material-symbols-outlined text-[12px] cursor-pointer hover:text-primary" onclick="removeEditorTag(this.parentElement)">close</span>`;
          container.appendChild(span);
          addTagInput.value = "";
          updateTagsCountBadge();
        }
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", async () => {
      if (!fileInput.files || !fileInput.files[0]) return;
      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      try {
        const resp = await fetch("/api/cms/upload", {
          method: "POST",
          body: formData,
        });
        const data = await resp.json();
        if (resp.ok && data.ok) {
          const url = data.asset.file_url;
          const coverUrlInput = document.getElementById("editor-cover-url-input");
          const coverImg1 = document.getElementById("editor-cover-img-preview");
          const coverImg2 = document.getElementById("editor-og-img-preview");
          const coverImg3 = document.getElementById("live-preview-cover-img");
          if (coverUrlInput) coverUrlInput.value = url;
          if (coverImg1) coverImg1.src = url;
          if (coverImg2) coverImg2.src = url;
          if (coverImg3) coverImg3.src = url;
          showEditorNotification("Imagem enviada e aplicada à capa!");
        }
      } catch (e) {
        showEditorNotification("Erro ao enviar imagem.", true);
      }
    });
  }

  // Atalho Ctrl+S / Cmd+S para salvar rapidamente
  window.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
      e.preventDefault();
      window.saveArticleFromEditor();
    }
  });

  // Fechar dropdown de publicação ao clicar fora
  document.addEventListener("click", (e) => {
    const dd = document.getElementById("publish-dropdown");
    const btn = document.getElementById("publish-dropdown-btn");
    if (dd && btn && !dd.contains(e.target) && !btn.contains(e.target)) {
      dd.classList.add("hidden");
    }
  });
});

// ==========================================================================
// GESTÃO RÁPIDA DE AUTORES & REDATORES DIRETO NO EDITOR (SEM PERDER RASCUNHO)
// ==========================================================================

window.openEditorAuthorsModal = function () {
  const modal = document.getElementById("editor-authors-modal");
  if (modal) modal.classList.remove("hidden");
};

window.closeEditorAuthorsModal = function () {
  const modal = document.getElementById("editor-authors-modal");
  if (modal) modal.classList.add("hidden");
};

window.resetEditorModalAuthorForm = function () {
  const idEl = document.getElementById("em-author-id");
  const nameEl = document.getElementById("em-author-name");
  const roleEl = document.getElementById("em-author-role");
  const userEl = document.getElementById("em-author-username");
  const emailEl = document.getElementById("em-author-email");
  const avatarEl = document.getElementById("em-author-avatar");
  const bioEl = document.getElementById("em-author-bio");
  const labelEl = document.getElementById("editor-modal-form-label");

  if (idEl) idEl.value = "";
  if (nameEl) nameEl.value = "";
  if (roleEl) roleEl.value = "";
  if (userEl) userEl.value = "";
  if (emailEl) emailEl.value = "";
  if (avatarEl) avatarEl.value = "";
  if (bioEl) bioEl.value = "";
  if (labelEl) labelEl.innerText = "Novo Autor / Redator";
  nameEl?.focus();
};

window.loadAuthorIntoEditorModal = function (rowEl) {
  if (!rowEl) return;
  const idEl = document.getElementById("em-author-id");
  const nameEl = document.getElementById("em-author-name");
  const roleEl = document.getElementById("em-author-role");
  const userEl = document.getElementById("em-author-username");
  const emailEl = document.getElementById("em-author-email");
  const avatarEl = document.getElementById("em-author-avatar");
  const bioEl = document.getElementById("em-author-bio");
  const labelEl = document.getElementById("editor-modal-form-label");

  if (idEl) idEl.value = rowEl.dataset.id || "";
  if (nameEl) nameEl.value = rowEl.dataset.displayName || "";
  if (roleEl) roleEl.value = rowEl.dataset.roleTitle || "";
  if (userEl) userEl.value = rowEl.dataset.username || "";
  if (emailEl) emailEl.value = rowEl.dataset.email || "";
  if (avatarEl) avatarEl.value = rowEl.dataset.avatarUrl || "";
  if (bioEl) bioEl.value = rowEl.dataset.bio || "";
  if (labelEl) labelEl.innerText = `Editando: ${rowEl.dataset.displayName}`;
  nameEl?.focus();
};

async function refreshEditorAuthorsState(selectedUsername) {
  try {
    const resp = await fetch("/api/cms/authors");
    const data = await resp.json();
    if (!resp.ok || !data.ok) return;

    const selectEl = document.getElementById("editor-author-select");
    const currentVal = selectedUsername || selectEl?.value || "duo";
    if (selectEl) {
      let opts = `<option value="duo" ${currentVal === "duo" ? "selected" : ""}>Co-autoria: Francisco & Wandeson (Telecom Ops)</option>`;
      data.authors.forEach((u) => {
        const sel = currentVal === u.username ? "selected" : "";
        opts += `<option value="${u.username}" ${sel}>${u.display_name} (${u.role_title})</option>`;
      });
      opts += `<option value="guest" ${currentVal === "guest" ? "selected" : ""}>Tony Sanderson (Convidado GOOCAST)</option>`;
      selectEl.innerHTML = opts;
    }

    const listEl = document.getElementById("editor-modal-authors-list");
    if (listEl) {
      listEl.innerHTML = data.authors
        .map((u) => {
          const initials = (u.display_name || "AU").slice(0, 2).toUpperCase();
          const avatarHtml = u.avatar_url
            ? `<img src="${u.avatar_url}" alt="${u.display_name}" class="w-full h-full object-cover" />`
            : initials;
          return `
          <div class="p-3 rounded-lg bg-surface-container-lowest border border-white/5 flex items-center justify-between gap-3"
               data-id="${u.id}"
               data-username="${u.username}"
               data-email="${u.email || ""}"
               data-display-name="${(u.display_name || "").replace(/"/g, "&quot;")}"
               data-role-title="${(u.role_title || "").replace(/"/g, "&quot;")}"
               data-bio="${(u.bio || "").replace(/"/g, "&quot;")}"
               data-avatar-url="${u.avatar_url || ""}">
            <div class="flex items-center gap-3 min-w-0">
              <div class="w-9 h-9 rounded-full bg-surface-container-high flex items-center justify-center font-headline-sm text-xs font-bold text-tertiary shrink-0 overflow-hidden">
                ${avatarHtml}
              </div>
              <div class="flex flex-col min-w-0">
                <span class="font-headline-sm text-body-sm font-bold text-on-surface truncate">${u.display_name}</span>
                <span class="font-telemetry-code text-[11px] text-tertiary truncate">${u.role_title} • @${u.username}</span>
              </div>
            </div>
            <div class="flex items-center gap-1.5 shrink-0">
              <button type="button" onclick="loadAuthorIntoEditorModal(this.closest('[data-id]'))" class="px-2.5 py-1 rounded bg-surface-container hover:bg-surface-bright text-on-surface font-body-sm text-xs">
                Editar
              </button>
              <button type="button" onclick="deleteAuthorFromEditorModal(${u.id}, '${(u.display_name || "").replace(/'/g, "\\'")}')" class="px-2 py-1 rounded bg-surface-container hover:bg-error-container/40 text-on-surface-variant hover:text-error font-body-sm text-xs">
                Excluir
              </button>
            </div>
          </div>`;
        })
        .join("");
    }
  } catch (err) {
    console.error("Erro ao atualizar lista de autores:", err);
  }
}

window.saveAuthorFromEditorModal = async function (e) {
  e.preventDefault();
  const id = document.getElementById("em-author-id")?.value || "";
  const display_name = document.getElementById("em-author-name")?.value || "";
  const role_title = document.getElementById("em-author-role")?.value || "";
  const username = document.getElementById("em-author-username")?.value || "";
  const email = document.getElementById("em-author-email")?.value || "";
  const avatar_url = document.getElementById("em-author-avatar")?.value || "";
  const bio = document.getElementById("em-author-bio")?.value || "";

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
        avatar_url,
        bio,
      }),
    });
    const data = await resp.json();
    if (resp.ok && data.ok) {
      showEditorNotification(
        id ? "Autor atualizado com sucesso!" : "Novo autor cadastrado e selecionado!"
      );
      window.resetEditorModalAuthorForm();
      await refreshEditorAuthorsState(data.author.username);
    } else {
      showEditorNotification(data.error || "Erro ao salvar autor.", true);
    }
  } catch (err) {
    showEditorNotification("Falha de conexão ao salvar autor.", true);
  }
};

window.deleteAuthorFromEditorModal = async function (userId, displayName) {
  if (!confirm(`Deseja excluir o autor/redator "${displayName}"?`)) return;
  try {
    const resp = await fetch(`/api/cms/authors/${userId}`, { method: "DELETE" });
    const data = await resp.json();
    if (resp.ok && data.ok) {
      showEditorNotification(`Autor "${displayName}" removido.`);
      window.resetEditorModalAuthorForm();
      await refreshEditorAuthorsState("duo");
    } else {
      showEditorNotification(data.error || "Erro ao excluir autor.", true);
    }
  } catch (err) {
    showEditorNotification("Falha ao excluir autor.", true);
  }
};

