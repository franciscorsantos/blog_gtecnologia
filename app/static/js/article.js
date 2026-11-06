// ==========================================================================
// GOOSE TECNOLOGIA — Lógica Interativa da Página de Artigo Completo
// (Barra de Progresso, Light/Dark Mode, Impressão PDF, Modo Zen, GOOCAST, TOC)
// ==========================================================================

let isLightMode = false;
let zenModeActive = false;
let isPodcastPlaying = false;
let isPodcastPaused = false;
let podcastInterval = null;
let currentAudioSeconds = 0;
let totalAudioSeconds = 6 * 60;
let speechChunks = [];
let currentChunkIndex = 0;
let currentSpeechRate = 1.0;
let activeUtterance = null;

function updateArticleProgress() {
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
    if (winScroll > 80) {
      badge.classList.remove("opacity-0");
      badge.classList.add("opacity-100");
    } else {
      badge.classList.remove("opacity-100");
      badge.classList.add("opacity-0");
    }
  }

  if (timeEl) {
    const totalMin = parseInt(timeEl.dataset.totalMinutes || "9", 10);
    const rem = Math.max(1, Math.ceil(totalMin * (1 - scrolled / 100)));
    if (scrolled >= 97) {
      timeEl.innerText = "Concluído";
    } else {
      timeEl.innerText = `~${rem} min rest.`;
    }
  }
}

window.toggleThemeMode = function () {
  isLightMode = !isLightMode;
  const html = document.documentElement;
  const icon = document.getElementById("theme-icon");
  const btn = document.getElementById("theme-toggle-btn");

  if (isLightMode) {
    html.classList.remove("dark");
    html.classList.add("light-mode");
    if (icon) icon.innerText = "dark_mode";
    if (btn) btn.setAttribute("title", "Mudar para Modo Escuro");
    localStorage.setItem("goose_theme", "light");
  } else {
    html.classList.add("dark");
    html.classList.remove("light-mode");
    if (icon) icon.innerText = "light_mode";
    if (btn) btn.setAttribute("title", "Mudar para Modo Claro");
    localStorage.setItem("goose_theme", "dark");
  }
};

window.toggleZenMode = function () {
  zenModeActive = !zenModeActive;
  const body = document.body;
  const zenBar = document.getElementById("zen-floating-bar");
  const zenBtn = document.getElementById("zen-mode-toggle-btn");

  if (zenModeActive) {
    body.classList.add("zen-mode");
    zenBar?.classList.remove("hidden");
    zenBar?.classList.add("flex");
    zenBtn?.classList.add("border-[#4A90E2]", "text-white", "bg-[#101930]");
  } else {
    body.classList.remove("zen-mode");
    zenBar?.classList.add("hidden");
    zenBar?.classList.remove("flex");
    zenBtn?.classList.remove("border-[#4A90E2]", "text-white", "bg-[#101930]");
  }
};

function parseDurationToSeconds(label) {
  if (!label || !label.includes(":")) return 360;
  const parts = label.split(":").map((n) => parseInt(n, 10));
  if (parts.length === 2 && !isNaN(parts[0]) && !isNaN(parts[1])) {
    return Math.max(30, parts[0] * 60 + parts[1]);
  }
  return 360;
}

function formatSecondsToMMSS(secTotal) {
  const safeSec = Math.max(0, Math.floor(secTotal));
  const min = Math.floor(safeSec / 60).toString().padStart(2, "0");
  const sec = (safeSec % 60).toString().padStart(2, "0");
  return `${min}:${sec}`;
}

function buildArticleSpeechChunks() {
  const chunks = [];
  const titleEl = document.querySelector("h1");
  if (titleEl && titleEl.innerText.trim()) {
    chunks.push(titleEl.innerText.trim());
  }

  const proseContainer =
    document.getElementById("article-prose-body") || document.querySelector("article");
  if (proseContainer) {
    const blocks = proseContainer.querySelectorAll("h2, h3, p, li");
    blocks.forEach((node) => {
      if (node.closest("pre") || node.closest("code") || node.closest("#sec-checklist")) return;
      const txt = (node.innerText || "").replace(/\s+/g, " ").trim();
      if (!txt) return;
      // Quebra parágrafos muito longos em sentenças para evitar corte de 15s no Chrome/Edge
      if (txt.length > 220) {
        const sentences = txt.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [txt];
        sentences.forEach((s) => {
          const clean = s.trim();
          if (clean.length > 2) chunks.push(clean);
        });
      } else {
        chunks.push(txt);
      }
    });
  }

  if (chunks.length === 0) {
    chunks.push("Artigo técnico Goose Tecnologia.");
  }
  return chunks;
}

function getBestPortugueseVoice() {
  if (!("speechSynthesis" in window)) return null;
  const voices = window.speechSynthesis.getVoices() || [];
  const ptBrVoices = voices.filter((v) => v.lang && v.lang.toLowerCase().startsWith("pt-br"));
  const naturalVoice = ptBrVoices.find(
    (v) =>
      v.name.toLowerCase().includes("natural") ||
      v.name.toLowerCase().includes("francisca") ||
      v.name.toLowerCase().includes("antonio") ||
      v.name.toLowerCase().includes("google")
  );
  if (naturalVoice) return naturalVoice;
  if (ptBrVoices.length > 0) return ptBrVoices[0];
  return voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("pt")) || null;
}

function renderAudioTime(secTotal) {
  const timeDisplay = document.getElementById("audio-current-time");
  const durationLabel = formatSecondsToMMSS(totalAudioSeconds);
  const currentLabel = formatSecondsToMMSS(secTotal);
  if (timeDisplay) timeDisplay.innerText = `${currentLabel} / ${durationLabel}`;

  // Atualiza barras de onda sonora
  const bars = document.querySelectorAll("#goocast-waveform > div");
  if (bars.length > 0) {
    const ratio = totalAudioSeconds > 0 ? Math.min(1, secTotal / totalAudioSeconds) : 0;
    const activeCount = Math.round(ratio * bars.length);
    bars.forEach((bar, idx) => {
      bar.classList.remove("bg-[#4A90E2]", "bg-[#E12B4A]", "bg-[#1C2742]");
      if (idx < activeCount - 2) {
        bar.classList.add("bg-[#4A90E2]");
      } else if (idx < activeCount) {
        bar.classList.add("bg-[#E12B4A]");
      } else {
        bar.classList.add("bg-[#1C2742]");
      }
    });
  }
}

function stopPodcastTimer() {
  if (podcastInterval) {
    clearInterval(podcastInterval);
    podcastInterval = null;
  }
}

function startPodcastTimer() {
  stopPodcastTimer();
  podcastInterval = setInterval(() => {
    if (!isPodcastPlaying) return;
    currentAudioSeconds = Math.min(totalAudioSeconds, currentAudioSeconds + 1);
    renderAudioTime(currentAudioSeconds);
  }, 1000);
}

function speakChunkAt(index) {
  if (!("speechSynthesis" in window)) return;
  if (index >= speechChunks.length) {
    // Fim da narração do artigo
    isPodcastPlaying = false;
    isPodcastPaused = false;
    currentChunkIndex = 0;
    currentAudioSeconds = totalAudioSeconds;
    renderAudioTime(currentAudioSeconds);
    stopPodcastTimer();
    const btnIcon = document.getElementById("podcast-play-icon");
    if (btnIcon) btnIcon.innerText = "play_arrow";
    return;
  }

  currentChunkIndex = index;
  // Sincroniza o tempo estimado com a posição do parágrafo atual
  currentAudioSeconds = Math.floor((currentChunkIndex / speechChunks.length) * totalAudioSeconds);
  renderAudioTime(currentAudioSeconds);

  const utterance = new SpeechSynthesisUtterance(speechChunks[index]);
  utterance.lang = "pt-BR";
  utterance.rate = currentSpeechRate;
  const voice = getBestPortugueseVoice();
  if (voice) utterance.voice = voice;

  utterance.onend = () => {
    if (isPodcastPlaying && !isPodcastPaused) {
      speakChunkAt(index + 1);
    }
  };

  utterance.onerror = (evt) => {
    if (evt.error === "interrupted" || evt.error === "canceled") return;
    if (isPodcastPlaying && !isPodcastPaused) {
      speakChunkAt(index + 1);
    }
  };

  activeUtterance = utterance;
  window.speechSynthesis.speak(utterance);
}

window.togglePlayPodcast = function () {
  const btnIcon = document.getElementById("podcast-play-icon");
  const timeDisplay = document.getElementById("audio-current-time");

  if (speechChunks.length === 0) {
    speechChunks = buildArticleSpeechChunks();
    const fullText = speechChunks.join(" ");
    const wordCount = fullText.split(/\s+/).filter(Boolean).length;
    // Calcula duração real aproximada da narração (~145 palavras por minuto)
    const estimatedSec = Math.max(45, Math.round((wordCount / 145) * 60));
    totalAudioSeconds = timeDisplay?.dataset.duration
      ? Math.min(estimatedSec, parseDurationToSeconds(timeDisplay.dataset.duration))
      : estimatedSec;
    totalAudioSeconds = estimatedSec;
  }

  if (!isPodcastPlaying) {
    isPodcastPlaying = true;
    if (btnIcon) btnIcon.innerText = "pause";

    if ("speechSynthesis" in window) {
      if (isPodcastPaused && window.speechSynthesis.paused) {
        isPodcastPaused = false;
        window.speechSynthesis.resume();
      } else {
        isPodcastPaused = false;
        window.speechSynthesis.cancel();
        if (currentChunkIndex >= speechChunks.length) {
          currentChunkIndex = 0;
          currentAudioSeconds = 0;
        }
        speakChunkAt(currentChunkIndex);
      }
    }
    startPodcastTimer();
  } else {
    isPodcastPlaying = false;
    isPodcastPaused = true;
    if (btnIcon) btnIcon.innerText = "play_arrow";
    if ("speechSynthesis" in window && window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
    }
    stopPodcastTimer();
  }
};

window.changeAudioSpeed = function (btn) {
  const speeds = [1.0, 1.25, 1.5, 2.0];
  const nextIdx = (speeds.indexOf(currentSpeechRate) + 1) % speeds.length;
  currentSpeechRate = speeds[nextIdx];
  if (btn) btn.innerText = `${currentSpeechRate}x`;

  if (isPodcastPlaying && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
    speakChunkAt(currentChunkIndex);
  }
};

window.scrubAudio = function (e) {
  const rect = e.currentTarget.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const width = rect.width;
  const percentage = Math.min(1, Math.max(0, clickX / width));

  if (speechChunks.length === 0) {
    speechChunks = buildArticleSpeechChunks();
  }

  currentAudioSeconds = Math.floor(percentage * totalAudioSeconds);
  currentChunkIndex = Math.min(
    speechChunks.length - 1,
    Math.floor(percentage * speechChunks.length)
  );
  renderAudioTime(currentAudioSeconds);

  if (isPodcastPlaying && "speechSynthesis" in window) {
    isPodcastPaused = false;
    window.speechSynthesis.cancel();
    speakChunkAt(currentChunkIndex);
  }
};

window.copyArticleLink = function (btn) {
  navigator.clipboard.writeText(window.location.href);
  const originalHTML = btn.innerHTML;
  btn.innerHTML = '<span class="material-symbols-outlined text-xs align-middle">check</span> Copiado!';
  setTimeout(() => {
    btn.innerHTML = originalHTML;
  }, 2000);
};

window.copyCodeSnippet = function (btn, codeBlockId) {
  const codeElement = document.getElementById(codeBlockId);
  if (!codeElement) return;
  navigator.clipboard.writeText(codeElement.innerText);
  const textSpan = btn.querySelector(".copy-text");
  if (textSpan) {
    const prev = textSpan.innerText;
    textSpan.innerText = "Copiado!";
    setTimeout(() => {
      textSpan.innerText = prev;
    }, 2000);
  }
};

function setupTocScrollSpy() {
  const tocLinks = Array.from(document.querySelectorAll(".toc-link"));
  if (tocLinks.length === 0) return;

  const sectionIds = tocLinks.map((link) => link.getAttribute("href")?.replace("#", "")).filter(Boolean);

  window.addEventListener(
    "scroll",
    () => {
      const scrollPos = window.scrollY + 220;
      let activeIndex = 0;

      sectionIds.forEach((id, index) => {
        const el = document.getElementById(id);
        if (el && el.offsetTop <= scrollPos) {
          activeIndex = index;
        }
      });

      const indicator = document.getElementById("toc-reading-indicator");
      if (indicator) {
        indicator.innerText = `${activeIndex + 1}/${sectionIds.length}`;
      }

      tocLinks.forEach((link, idx) => {
        if (idx === activeIndex) {
          link.classList.add("bg-[#101930]", "text-white", "font-medium");
          link.classList.remove("text-[#8E9EB5]");
        } else {
          link.classList.remove("bg-[#101930]", "text-white", "font-medium");
          link.classList.add("text-[#8E9EB5]");
        }
      });
    },
    { passive: true }
  );
}

// ==========================================================================
// COMENTÁRIOS E DISCUSSÃO TÉCNICA NOS ARTIGOS
// ==========================================================================

function escapeCommentHtml(str) {
  return String(str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

window.prepareCommentReply = function (commentId, authorName) {
  const parentInput = document.getElementById("comment-parent-id");
  const banner = document.getElementById("comment-reply-banner");
  const targetNameEl = document.getElementById("comment-reply-target-name");
  const textarea = document.getElementById("comment-content");

  if (parentInput) parentInput.value = String(commentId);
  if (targetNameEl) targetNameEl.innerText = authorName;
  if (banner) {
    banner.classList.remove("hidden");
    banner.classList.add("flex");
  }
  if (textarea) {
    textarea.focus();
    textarea.scrollIntoView({ behavior: "smooth", block: "center" });
  }
};

window.cancelCommentReply = function () {
  const parentInput = document.getElementById("comment-parent-id");
  const banner = document.getElementById("comment-reply-banner");
  if (parentInput) parentInput.value = "";
  if (banner) {
    banner.classList.add("hidden");
    banner.classList.remove("flex");
  }
};

function buildCommentCardHtml(c, canModerate) {
  const safeName = escapeCommentHtml(c.author_name);
  const safeIsp = escapeCommentHtml(c.author_role_isp);
  const safeContent = escapeCommentHtml(c.content);
  const safeInitials = escapeCommentHtml(c.initials || "IS");

  const badgeHtml = c.is_author_badge
    ? `<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-[#E12B4A]/20 text-[#E12B4A] border border-[#E12B4A]/30 uppercase font-semibold">Equipe Goose</span>`
    : "";
  const ispHtml = safeIsp
    ? `<span class="text-[10px] font-mono px-2 py-0.5 rounded bg-[#101930] text-[#4A90E2] border border-[#1C2742]">${safeIsp}</span>`
    : "";
  const deleteBtnHtml = canModerate
    ? `<button type="button" onclick="deleteArticleComment(${c.id})" title="Excluir comentário (Admin CMS)" class="p-1 rounded bg-[#101930] hover:bg-[#E12B4A]/20 text-[#8E9EB5] hover:text-[#E12B4A] transition-colors flex items-center cursor-pointer"><span class="material-symbols-outlined text-xs">delete</span></button>`
    : "";

  if (c.parent_id) {
    return `
      <div class="p-3.5 rounded-lg bg-[#101930]/75 border-l-2 border-[#4A90E2] border-y border-r border-[#1C2742] flex flex-col gap-2" id="comment-card-${c.id}">
        <div class="flex items-start justify-between gap-2">
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-full bg-[#080D1A] border border-[#1C2742] flex items-center justify-center font-mono text-[10px] font-bold ${c.is_author_badge ? "text-[#E12B4A]" : "text-[#4A90E2]"} shrink-0">
              ${safeInitials}
            </div>
            <div class="flex flex-col">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="font-heading font-semibold text-xs text-white">${safeName}</span>
                ${badgeHtml}
                ${ispHtml}
              </div>
              <span class="text-[10px] font-mono text-[#8E9EB5]/75">${escapeCommentHtml(c.created_at)}</span>
            </div>
          </div>
          ${deleteBtnHtml}
        </div>
        <p class="text-xs sm:text-sm text-[#E2E8F0] leading-relaxed whitespace-pre-line pl-9">${safeContent}</p>
      </div>
    `;
  }

  return `
    <div class="p-4 sm:p-5 rounded-xl bg-[#080D1A]/75 border border-[#1C2742] flex flex-col gap-3" id="comment-card-${c.id}">
      <div class="flex items-start justify-between gap-3">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-full bg-[#101930] border border-[#1C2742] flex items-center justify-center font-mono text-xs font-bold ${c.is_author_badge ? "text-[#E12B4A] border-[#E12B4A]/50" : "text-[#4A90E2]"} shrink-0">
            ${safeInitials}
          </div>
          <div class="flex flex-col">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-heading font-semibold text-sm text-white">${safeName}</span>
              ${badgeHtml}
              ${ispHtml}
            </div>
            <span class="text-[11px] font-mono text-[#8E9EB5]/75">${escapeCommentHtml(c.created_at)}</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button type="button" onclick='prepareCommentReply(${c.id}, ${JSON.stringify(c.author_name)})' class="px-2.5 py-1 rounded bg-[#101930] hover:bg-[#1C2742] text-[11px] font-mono text-[#8E9EB5] hover:text-white transition-colors flex items-center gap-1 cursor-pointer">
            <span class="material-symbols-outlined text-xs">reply</span> Responder
          </button>
          ${deleteBtnHtml}
        </div>
      </div>
      <p class="text-xs sm:text-sm text-[#E2E8F0] leading-relaxed whitespace-pre-line pl-12">${safeContent}</p>
      <div class="flex flex-col gap-3 pl-6 sm:pl-12 mt-1 hidden" id="comment-replies-${c.id}"></div>
    </div>
  `;
}

window.submitArticleComment = async function (e) {
  e.preventDefault();
  const section = document.getElementById("comentarios");
  const slug = section?.dataset.articleSlug;
  if (!slug) return;

  const nameInput = document.getElementById("comment-author-name");
  const ispInput = document.getElementById("comment-author-isp");
  const contentInput = document.getElementById("comment-content");
  const parentInput = document.getElementById("comment-parent-id");
  const submitBtn = document.getElementById("comment-submit-btn");
  const feedbackEl = document.getElementById("comment-form-feedback");

  const author_name = (nameInput?.value || "").trim();
  const author_role_isp = (ispInput?.value || "").trim();
  const content = (contentInput?.value || "").trim();
  const parent_id = (parentInput?.value || "").trim();

  if (!author_name || !content) return;

  if (submitBtn) submitBtn.disabled = true;

  try {
    const resp = await fetch(`/api/articles/${encodeURIComponent(slug)}/comments`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        author_name,
        author_role_isp,
        content,
        parent_id: parent_id ? parseInt(parent_id, 10) : null,
      }),
    });

    const data = await resp.json();
    if (!resp.ok || !data.ok) {
      if (feedbackEl) {
        feedbackEl.innerHTML = `<span class="text-[#E12B4A]">${escapeCommentHtml(data.error || "Erro ao publicar comentário.")}</span>`;
      }
      return;
    }

    localStorage.setItem("goose_reader_name", author_name);
    if (author_role_isp) localStorage.setItem("goose_reader_isp", author_role_isp);

    const emptyState = document.getElementById("comments-empty-state");
    if (emptyState) emptyState.remove();

    const c = data.comment;
    const cardHtml = buildCommentCardHtml(c, Boolean(data.can_moderate));

    if (c.parent_id) {
      const repliesBox = document.getElementById(`comment-replies-${c.parent_id}`);
      if (repliesBox) {
        repliesBox.classList.remove("hidden");
        repliesBox.insertAdjacentHTML("beforeend", cardHtml);
      }
    } else {
      const listContainer = document.getElementById("comments-list-container");
      if (listContainer) {
        listContainer.insertAdjacentHTML("afterbegin", cardHtml);
      }
    }

    const totalBadge = document.getElementById("comments-total-badge");
    if (totalBadge && typeof data.total === "number") {
      totalBadge.innerText = String(data.total);
    }

    if (contentInput) contentInput.value = "";
    window.cancelCommentReply();

    if (feedbackEl) {
      feedbackEl.innerHTML = `<span class="text-emerald-400">✓ Comentário publicado com sucesso!</span>`;
      setTimeout(() => {
        feedbackEl.innerText = "Comentários abertos para engenheiros, gestores e equipes de ISPs.";
      }, 4000);
    }
  } catch (err) {
    if (feedbackEl) {
      feedbackEl.innerHTML = `<span class="text-[#E12B4A]">Falha de conexão ao enviar comentário.</span>`;
    }
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
};

window.deleteArticleComment = async function (commentId) {
  if (!confirm("Deseja realmente excluir este comentário?")) return;

  try {
    const resp = await fetch(`/api/comments/${commentId}`, { method: "DELETE" });
    const data = await resp.json();
    if (resp.ok && data.ok) {
      const card = document.getElementById(`comment-card-${commentId}`);
      if (card) card.remove();
      const totalBadge = document.getElementById("comments-total-badge");
      if (totalBadge && typeof data.total === "number") {
        totalBadge.innerText = String(data.total);
      }
    } else {
      alert(data.error || "Não foi possível excluir o comentário.");
    }
  } catch (err) {
    alert("Erro de conexão ao tentar excluir o comentário.");
  }
};

document.addEventListener("DOMContentLoaded", () => {
  // Restaura preferência de tema se salva
  if (localStorage.getItem("goose_theme") === "light") {
    window.toggleThemeMode();
  }

  // Preenche nome e ISP salvos anteriormente pelo leitor (caso não esteja logado no CMS)
  const nameInput = document.getElementById("comment-author-name");
  const ispInput = document.getElementById("comment-author-isp");
  if (nameInput && !nameInput.value && localStorage.getItem("goose_reader_name")) {
    nameInput.value = localStorage.getItem("goose_reader_name");
  }
  if (ispInput && !ispInput.value && localStorage.getItem("goose_reader_isp")) {
    ispInput.value = localStorage.getItem("goose_reader_isp");
  }

  window.addEventListener("scroll", updateArticleProgress, { passive: true });
  updateArticleProgress();
  setupTocScrollSpy();

  if ("speechSynthesis" in window) {
    window.speechSynthesis.getVoices();
    window.addEventListener("beforeunload", () => {
      window.speechSynthesis.cancel();
    });
  }

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && zenModeActive) {
      window.toggleZenMode();
    }
  });

  const backToTopBtn = document.getElementById("back-to-top");
  window.addEventListener(
    "scroll",
    () => {
      if (window.scrollY > 300) {
        backToTopBtn?.classList.remove("opacity-0", "pointer-events-none");
        backToTopBtn?.classList.add("opacity-100", "pointer-events-auto");
      } else {
        backToTopBtn?.classList.add("opacity-0", "pointer-events-none");
        backToTopBtn?.classList.remove("opacity-100", "pointer-events-auto");
      }
    },
    { passive: true }
  );
});

