import re
import html
import unicodedata
import markdown


def slugify_heading(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return f"sec-{slug}" if slug else "sec-topico"


SYNTAX_LABELS = {
    "mikrotik": "MikroTik RouterOS v7.14+ CLI",
    "mikrotik-routeros": "MikroTik RouterOS v7 Script",
    "routeros": "RouterOS v7 Routing Filter Rules",
    "bgp": "BGP Bird2 / FRR Conf",
    "bash": "Linux CLI / CGNAT Shell",
    "python": "Python Netmiko / Telecom Automation",
    "json": "JSON Optical Telemetry",
}


def highlight_routeros_code(raw_code: str) -> str:
    """Realça sintaxe técnica de scripts RouterOS / BGP no padrão NOC Goose."""
    escaped = html.escape(raw_code.strip())
    lines = escaped.split("\n")
    styled_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            styled_lines.append(f'<span class="text-[#8E9EB5]">{line}</span>')
        elif stripped.startswith("/"):
            styled_lines.append(f'<span class="text-[#E12B4A] font-semibold">{line}</span>')
        else:
            # Realça chaves de comando add/set e strings entre aspas
            line = re.sub(
                r'(&quot;[^&]*&quot;)',
                r'<span class="text-[#4A90E2]">\1</span>',
                line,
            )
            line = re.sub(
                r"\b(add|set|accept|reject|if)\b",
                r'<span class="text-white font-semibold">\1</span>',
                line,
            )
            styled_lines.append(line)
    return "\n".join(styled_lines)


def _format_math_subscripts(expr: str) -> str:
    """Converte subscritos e sobrescritos matemáticos (ex: S_m, V_h, ALQ_{inter}, x^{2}) dentro de expressões."""
    expr = re.sub(r"([A-Za-z0-9\)\]])_\{([^}]+)\}", r"\1<sub>\2</sub>", expr)
    expr = re.sub(r"([A-Za-z0-9\)\]])_([a-zA-Z0-9]{1,4})(?![a-zA-Z0-9])", r"\1<sub>\2</sub>", expr)
    expr = re.sub(r"([A-Za-z0-9\)\]])\^\{([^}]+)\}", r"\1<sup>\2</sup>", expr)
    return expr


def _format_frac(match: re.Match) -> str:
    num = match.group(1).strip()
    den = match.group(2).strip()
    if "+" in den or "-" in den:
        den = f"({den})"
    if "+" in num or "-" in num:
        num = f"({num})"
    if " " in num or " " in den:
        return f"{num} / {den}"
    return f"{num}/{den}"


def normalize_inline_latex(text: str) -> str:
    """
    Converte notações matemáticas inline e de bloco LaTeX geradas por IAs
    (ex: $24\\times7$, $+20\\%$, $7^\\circ$, $2^\\text{a}$, $\\Delta V_h$, $$...$$)
    em texto legível normal, preservando valores monetários como R$ 1.500
    e mantendo intacta toda a estrutura de parágrafos e títulos do Markdown.
    """
    # Passo 0: Resolve wrappers de texto (\text{...}, \mathrm{...}) e subscritos com chaves (_{...})
    # ANTES do \frac{...}{...} para que chaves internas não quebrem frações como \frac{1 - ALQ_{inter}}{1 - ALQ_{intra}}
    for _ in range(2):
        text = re.sub(r"\\(?:text|textbf|textit|mathrm|mathbf|mathit)\{([^}]*)\}", r"\1", text)

    latex_replacements = [
        # Ordinais femininos e masculinos ($2^\text{a}$, $1^\text{o}$, $7^\circ$)
        (r"\^\{\\text\{a\}\}|\^\\text\{a\}|\^\{a\}|\^a(?![a-zA-Z])", "ª"),
        (r"\^\{\\text\{o\}\}|\^\\text\{o\}|\^\{o\}|\^o(?![a-zA-Z])", "º"),
        (r"\^\{\\circ\}|\^\\circ(?![a-zA-Z])", "º"),
        (r"\\circ(?![a-zA-Z])", "°"),
        # Subscritos e sobrescritos entre chaves (ex: MVA_{original}, ALQ_{inter}) antes do \frac
        (r"([A-Za-z0-9\)\]])_\{([^}]+)\}", r"\1<sub>\2</sub>"),
        (r"([A-Za-z0-9\)\]])\^\{([^}]+)\}", r"\1<sup>\2</sup>"),
        # Frações (\frac{a}{b}) - executado 2x para suportar frações aninhadas
        (r"\\frac\{([^}]*)\}\{([^}]*)\}", _format_frac),
        (r"\\frac\{([^}]*)\}\{([^}]*)\}", _format_frac),
        # Delimitadores (\left(, \right), \left\{, \right\}, \left[, \right])
        (r"\\(?:left|right)\s*\\?([\(\)\[\]\{\}|.])", lambda m: "" if m.group(1) == "." else m.group(1)),
        (r"\\([\{\}])", r"\1"),
        # Letras gregas e símbolos comuns em engenharia e finanças
        (r"\\Delta(?![a-zA-Z])", "Δ"),
        (r"\\delta(?![a-zA-Z])", "δ"),
        (r"\\Sigma(?![a-zA-Z])", "Σ"),
        (r"\\sigma(?![a-zA-Z])", "σ"),
        (r"\\Omega(?![a-zA-Z])", "Ω"),
        (r"\\omega(?![a-zA-Z])", "ω"),
        (r"\\alpha(?![a-zA-Z])", "α"),
        (r"\\beta(?![a-zA-Z])", "β"),
        (r"\\gamma(?![a-zA-Z])", "γ"),
        (r"\\lambda(?![a-zA-Z])", "λ"),
        (r"\\mu(?![a-zA-Z])", "μ"),
        (r"\\pi(?![a-zA-Z])", "π"),
        # Operadores matemáticos
        (r"\\times(?![a-zA-Z])", "x"),
        (r"\\%", "%"),
        (r"\\\$", "$"),
        (r"\\pm(?![a-zA-Z])", "±"),
        (r"\\geq?(?![a-zA-Z])", "≥"),
        (r"\\leq?(?![a-zA-Z])", "≤"),
        (r"\\approx(?![a-zA-Z])", "≈"),
        (r"\\neq?(?![a-zA-Z])", "≠"),
        (r"\\(?:rightarrow|to|Rightarrow)(?![a-zA-Z])", "→"),
        (r"\\(?:leftarrow|Leftarrow)(?![a-zA-Z])", "←"),
        (r"\\(?:leftrightarrow|Leftrightarrow)(?![a-zA-Z])", "↔"),
        (r"\\(?:cdot|bullet)(?![a-zA-Z])", "·"),
        (r"\\div(?![a-zA-Z])", "÷"),
        (r"\\infty(?![a-zA-Z])", "∞"),
        (r"\\(?:quad|qquad|enspace|[,;])", " "),
        (r"\\!", ""),
    ]

    # Passo 1: Substitui todos os comandos LaTeX (\times, ^\circ, \frac, \left\{, \Delta, etc.)
    for pattern, repl in latex_replacements:
        text = re.sub(pattern, repl, text)

    # Passo 2: Converte blocos de equação $$ ... $$ (mesmo se quebrados em múltiplas linhas) em destaque técnico legível
    def replace_display_math(match: re.Match) -> str:
        inner = re.sub(r"\s+", " ", match.group(1)).strip()
        inner = _format_math_subscripts(inner)
        inner = re.sub(r"\^([aAoO])(?![a-zA-Z])", lambda m: "ª" if m.group(1).lower() == "a" else "º", inner)
        return (
            '<div class="my-3 p-3.5 rounded-xl bg-[#080D1A] border border-[#1C2742] '
            'font-mono text-xs sm:text-sm text-white text-center overflow-x-auto">'
            f"{inner}</div>"
        )

    text = re.sub(r"\$\$([^\$]+?)\$\$", replace_display_math, text)

    # Passo 3: Remove cifrões de expressões inline $...$ (preservando R$ e US$) e formata subscritos
    def replace_inline_math(match: re.Match) -> str:
        inner = _format_math_subscripts(match.group(1))
        inner = re.sub(r"\^([aAoO])(?![a-zA-Z])", lambda m: "ª" if m.group(1).lower() == "a" else "º", inner)
        return inner

    text = re.sub(
        r"(?<![A-Za-z\\])\$(?!\s)([^\$\n]{1,160}?)(?<!\s)\$",
        replace_inline_math,
        text,
    )

    return text


def normalize_markdown_lists(text: str) -> str:
    """
    Garante que listas Markdown (*, -, 1.) iniciadas logo após um parágrafo comum
    ou dentro de blockquotes (> * item) tenham linha em branco antes para o parser
    Python-Markdown criar <ul>/<ol> corretamente, além de converter sub-listas de 2 espaços para 4 espaços.
    """
    lines = text.split("\n")
    out = []
    list_item_re = re.compile(r"^(\s*)(?:[\*\-]|\d+\.)\s+")
    quote_list_re = re.compile(r"^>\s*(?:[\*\-]|\d+\.)\s+")

    for line in lines:
        # Expande sub-listas indentadas com 2 ou 3 espaços para 4 espaços (padrão Python-Markdown)
        line = re.sub(r"^(\s{2,3})([\*\-]|\d+\.)\s+", r"    \2 ", line)

        if out:
            prev = out[-1]
            prev_stripped = prev.strip()
            # Caso 1: Linha de lista normal logo após parágrafo de texto (sem linha vazia antes)
            if list_item_re.match(line) and prev_stripped and not list_item_re.match(prev) and not prev_stripped.startswith("#") and not prev_stripped.startswith(">"):
                out.append("")
            # Caso 2: Linha de lista dentro de blockquote (> * item) logo após texto de blockquote (> texto)
            elif quote_list_re.match(line.strip()) and prev_stripped.startswith(">") and not quote_list_re.match(prev_stripped) and prev_stripped != ">":
                out.append(">")

        out.append(line)

    return "\n".join(out)


def render_article_markdown(md_text: str) -> tuple[str, list[dict]]:
    """
    Converte o Markdown estendido do Goose CMS em HTML estilizado com:
    - Callouts :::noc-warning ... :::
    - Blocos de código com header de terminal e botão Copiar Script
    - Diagramas topológicos :::topology-bgp :::
    - Seções numeradas (01., 02.) e extração automática de Sumário Técnico (TOC)
    """
    if not md_text:
        return "", []

    text = md_text.replace("\r\n", "\n")

    # Remove H1 inicial caso seja duplicado do título do artigo
    text = re.sub(r"^\s*#\s+[^\n]+\n+", "", text)

    # 1. Processa Callout :::noc-warning [Título Opcional] ... :::
    def replace_noc_warning(match):
        body = match.group(1).strip()
        lines = body.split("\n")
        title = "Protocolo de Segurança NOC Goose"
        if lines and lines[0].startswith("title:"):
            title = lines[0].replace("title:", "").strip()
            body = "\n".join(lines[1:]).strip()
        body_html = re.sub(
            r"`([^`]+)`",
            r'<code class="font-mono text-[#E12B4A] bg-[#080D1A] px-1.5 py-0.5 rounded text-xs">\1</code>',
            body,
        )
        body_html = re.sub(r"\*([^*]+)\*", r'<em class="text-white">\1</em>', body_html)
        return (
            '<div class="p-4 sm:p-5 rounded-xl bg-[#101930]/90 border-l-2 border-[#E12B4A] '
            'border-y border-r border-[#1C2742] flex items-start gap-3.5 shadow-sm my-4">'
            '<span class="material-symbols-outlined text-[#E12B4A] text-xl shrink-0 mt-0.5">warning</span>'
            '<div class="flex flex-col gap-1">'
            f'<span class="font-heading font-semibold text-sm text-white">{title}</span>'
            f'<p class="text-xs sm:text-sm text-[#8E9EB5] leading-relaxed">{body_html}</p>'
            "</div></div>"
        )

    text = re.sub(r":::noc-warning\s*\n(.*?)\n:::", replace_noc_warning, text, flags=re.DOTALL)

    # 2. Processa Diagrama Topológico embutido :::topology-bgp:::
    topology_svg = """
<div class="my-4 bg-[#080D1A] rounded-xl border border-[#1C2742] p-5 flex flex-col gap-3">
  <div class="flex items-center justify-between pb-2 border-b border-[#1C2742]/50 text-xs font-mono">
    <span class="text-[#4A90E2] uppercase tracking-wider font-semibold">DIAGRAMA TOPOLÓGICO: POP BORDER MULTIHOMED</span>
    <span class="text-[#8E9EB5]/70">ITU-T / IEEE 802.3ae</span>
  </div>
  <div class="w-full flex justify-center py-2">
    <svg class="w-full max-w-lg text-[#E2E8F0]" fill="none" viewBox="0 0 600 230" xmlns="http://www.w3.org/2000/svg">
      <rect class="fill-[#101930] stroke-[#1C2742]" height="48" rx="6" stroke-width="1" width="130" x="45" y="20"></rect>
      <text class="fill-white font-sans text-xs font-semibold" text-anchor="middle" x="110" y="44">Trânsito A (Tier-1)</text>
      <text class="fill-[#8E9EB5] font-mono text-[10px]" text-anchor="middle" x="110" y="58">AS 6762 • BGP+BFD</text>
      <rect class="fill-[#101930] stroke-[#4A90E2]/40" height="48" rx="6" stroke-width="1" width="130" x="235" y="20"></rect>
      <text class="fill-white font-sans text-xs font-semibold" text-anchor="middle" x="300" y="44">IX.br (PTT Local)</text>
      <text class="fill-[#4A90E2] font-mono text-[10px]" text-anchor="middle" x="300" y="58">AS 26162 • Baixa Latência</text>
      <rect class="fill-[#101930] stroke-[#1C2742]" height="48" rx="6" stroke-width="1" width="130" x="425" y="20"></rect>
      <text class="fill-white font-sans text-xs font-semibold" text-anchor="middle" x="490" y="44">Trânsito B (Tier-1)</text>
      <text class="fill-[#8E9EB5] font-mono text-[10px]" text-anchor="middle" x="490" y="58">AS 12956 • Backup</text>
      <path d="M110 68 L260 155" stroke="#E12B4A" stroke-dasharray="3 3" stroke-width="1.5"></path>
      <path d="M300 68 L300 155" stroke="#4A90E2" stroke-width="2"></path>
      <path d="M490 68 L340 155" stroke="#8E9EB5" stroke-dasharray="3 3" stroke-width="1.5"></path>
      <rect class="fill-[#101930] stroke-[#4A90E2]/60" height="54" rx="6" stroke-width="1.5" width="170" x="215" y="155"></rect>
      <text class="fill-white font-sans text-xs font-bold" text-anchor="middle" x="300" y="179">CCR2216 BORDA ISP</text>
      <text class="fill-[#E12B4A] font-mono text-[10px]" text-anchor="middle" x="300" y="196">AS 263481 • Goose Optimized</text>
    </svg>
  </div>
  <p class="font-mono text-[11px] text-[#8E9EB5] text-center">
    Figura 1.0: Roteamento simétrico inteligente com failover automático direcionado por comunidades RFC 1997.
  </p>
</div>
"""
    text = text.replace(":::topology-bgp:::", topology_svg)

    # 3. Processa blocos de código cercados ```lang ... ```
    code_counter = 0
    code_placeholders = {}

    def replace_fenced_code(match):
        nonlocal code_counter
        code_counter += 1
        lang_raw = (match.group(1) or "mikrotik-routeros").strip()
        parts = lang_raw.split("|", 1)
        lang_key = parts[0].strip().lower()
        custom_title = parts[1].strip() if len(parts) > 1 else SYNTAX_LABELS.get(lang_key, "RouterOS v7 CLI — Terminal Script")
        code_body = match.group(2)
        block_id = f"code-block-{code_counter}"
        styled_code = highlight_routeros_code(code_body)

        html_block = f"""
<div class="rounded-xl border border-[#1C2742] bg-[#080D1A] overflow-hidden flex flex-col my-3">
  <div class="bg-[#101930] px-4 py-2 flex items-center justify-between border-b border-[#1C2742]">
    <div class="flex items-center gap-2">
      <span class="w-2.5 h-2.5 rounded-full bg-[#E12B4A]"></span>
      <span class="w-2.5 h-2.5 rounded-full bg-[#4A90E2]"></span>
      <span class="font-mono text-xs text-white pl-2">{html.escape(custom_title)}</span>
    </div>
    <button type="button" class="copy-code-btn flex items-center gap-1.5 px-2.5 py-1 rounded bg-[#0B1326] hover:bg-[#1C2742] text-[#4A90E2] text-xs font-mono transition-all" onclick="copyCodeSnippet(this, '{block_id}')">
      <span class="material-symbols-outlined text-xs">content_copy</span>
      <span class="copy-text">Copiar Script</span>
    </button>
  </div>
  <pre class="p-4 overflow-x-auto font-mono text-xs text-[#E2E8F0] leading-relaxed" id="{block_id}"><code>{styled_code}</code></pre>
</div>
"""
        placeholder = f"@@CODE_BLOCK_PLACEHOLDER_{code_counter}@@"
        code_placeholders[placeholder] = html_block
        return placeholder

    text = re.sub(r"```([^\n]*)\n(.*?)```", replace_fenced_code, text, flags=re.DOTALL)

    # Normaliza expressões LaTeX inline ($24\times7$, $+20\%$, $16,7\%$) e espaçamento de listas
    text = normalize_inline_latex(text)
    text = normalize_markdown_lists(text)

    # 4. Extrai H2 (ou H3 caso não haja H2) para construir o Sumário Técnico (TOC) e envolver seções
    toc_items = []
    sec_index = 0

    def replace_h2(match):
        nonlocal sec_index
        sec_index += 1
        raw_heading = match.group(1).strip()
        clean_heading = re.sub(r"^\d+[\.\)]\s*", "", raw_heading)
        clean_heading = re.sub(r"\*\*([^*]+)\*\*", r"\1", clean_heading)
        sec_id = slugify_heading(clean_heading)
        toc_items.append(
            {
                "index": sec_index,
                "id": sec_id,
                "title": f"{sec_index}. {clean_heading}",
                "clean_title": clean_heading,
            }
        )
        num_badge = f"{sec_index:02d}."
        return (
            f'<div class="flex items-center gap-2.5 pt-6 scroll-mt-24" id="{sec_id}">'
            f'<span class="font-mono text-xs text-[#E12B4A] font-bold">{num_badge}</span>'
            f'<h2 class="font-heading font-bold text-xl sm:text-2xl text-white tracking-tight">{clean_heading}</h2>'
            f"</div>"
        )

    if re.search(r"^##\s+.+$", text, flags=re.MULTILINE):
        text = re.sub(r"^##\s+(.+)$", replace_h2, text, flags=re.MULTILINE)
    elif re.search(r"^###\s+.+$", text, flags=re.MULTILINE):
        text = re.sub(r"^###\s+(.+)$", replace_h2, text, flags=re.MULTILINE)

    # 5. Converte o restante via Markdown (com extensão de tabelas)
    rendered = markdown.markdown(text, extensions=["tables", "nl2br"])

    # 6. Estiliza H3, H4, Blockquote (>), HR (---), Links e Listas Numeradas
    rendered = rendered.replace(
        "<h3>",
        '<h3 class="font-heading font-bold text-lg sm:text-xl text-white tracking-tight pt-4 pb-1">',
    )
    rendered = rendered.replace(
        "<h4>",
        '<h4 class="font-heading font-semibold text-base sm:text-lg text-white tracking-tight pt-3 pb-0.5">',
    )
    rendered = rendered.replace(
        "<blockquote>",
        '<blockquote class="p-4 sm:p-5 rounded-xl bg-[#101930]/85 border-l-4 border-[#4A90E2] border-y border-r border-[#1C2742] text-sm sm:text-base text-[#E2E8F0] my-3 flex flex-col gap-2 shadow-sm">',
    )
    rendered = rendered.replace(
        "<hr />",
        '<hr class="border-t border-[#1C2742]/80 my-6" />',
    ).replace(
        "<hr>",
        '<hr class="border-t border-[#1C2742]/80 my-6" />',
    )

    # Estiliza tabelas Markdown no padrão RFC 1997 do Stitch
    rendered = rendered.replace(
        "<table>",
        '<div class="overflow-x-auto rounded-xl border border-[#1C2742] bg-[#080D1A] my-3"><table class="w-full text-left font-mono text-xs">',
    ).replace("</table>", "</table></div>")
    rendered = rendered.replace(
        "<thead>", '<thead class="bg-[#101930] text-white border-b border-[#1C2742]">'
    )
    rendered = rendered.replace(
        "<tbody>", '<tbody class="divide-y divide-[#1C2742]/50 text-[#8E9EB5]">'
    )
    rendered = re.sub(r"<th(\s+[^>]*)?>", r'<th class="p-3 font-semibold"\1>', rendered)
    rendered = re.sub(r"<td(\s+[^>]*)?>", r'<td class="p-3 align-top"\1>', rendered)
    rendered = rendered.replace("<tr>", '<tr class="hover:bg-[#101930]/40 transition-colors">')

    # Estiliza inline code e listas
    rendered = re.sub(
        r"<code>([^<]+)</code>",
        r'<code class="font-mono text-[#4A90E2] bg-[#080D1A] px-1.5 py-0.5 rounded text-xs">\1</code>',
        rendered,
    )
    # Estiliza itens de checklist Markdown (- [x] ou - [ ])
    rendered = re.sub(
        r"<li>\s*\[([xX])\]\s*(.*?)</li>",
        r'<li class="list-none -ml-4"><label class="flex items-start gap-3 p-3 rounded-lg bg-[#080D1A] border border-[#1C2742] hover:border-[#4A90E2] cursor-pointer transition-colors font-mono text-xs"><input checked class="w-4 h-4 mt-0.5 rounded bg-[#101930] border-[#1C2742] text-[#E12B4A] focus:ring-0 cursor-pointer" type="checkbox" /><span class="text-white">\2</span></label></li>',
        rendered,
    )
    rendered = re.sub(
        r"<li>\s*\[\s*\]\s*(.*?)</li>",
        r'<li class="list-none -ml-4"><label class="flex items-start gap-3 p-3 rounded-lg bg-[#080D1A] border border-[#1C2742] hover:border-[#4A90E2] cursor-pointer transition-colors font-mono text-xs"><input class="w-4 h-4 mt-0.5 rounded bg-[#101930] border-[#1C2742] text-[#E12B4A] focus:ring-0 cursor-pointer" type="checkbox" /><span class="text-white">\1</span></label></li>',
        rendered,
    )

    rendered = rendered.replace("<strong>", '<strong class="text-white font-semibold">')
    rendered = rendered.replace("<em>", '<em class="text-white">')
    rendered = rendered.replace(
        "<ul>",
        '<ul class="list-disc list-inside flex flex-col gap-2 text-sm sm:text-base text-[#8E9EB5] my-2">',
    )
    rendered = rendered.replace(
        "<ol>",
        '<ol class="list-decimal list-inside flex flex-col gap-2 text-sm sm:text-base text-[#8E9EB5] my-2">',
    )
    rendered = re.sub(
        r'<a href="([^"]+)">',
        r'<a href="\1" target="_blank" rel="noopener noreferrer" class="text-[#4A90E2] hover:underline font-medium">',
        rendered,
    )

    # 7. Restaura os blocos de código de terminal
    for placeholder, block_html in code_placeholders.items():
        rendered = rendered.replace(f"<p>{placeholder}</p>", block_html)
        rendered = rendered.replace(placeholder, block_html)

    return rendered, toc_items

