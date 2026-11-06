# Goose Tecnologia — Blog Minimalista Telecom & ISPs + Goose CMS v2.4

Portal editorial técnico de **Engenharia Telecom, Redes BGP/ASN, Gestão de NOC e Automação com IA para Provedores de Internet (ISPs)**, acompanhado do painel administrativo **Goose CMS v2.4** com editor Markdown Split-Screen em tempo real.

Este projeto foi projetado e construído a partir das especificações visuais do projeto Stitch **`ID: 2523588531873957096`** (*Blog Goose Tecnologia*), utilizando **HTML5, CSS3 (Tailwind CSS + Estilos Customizados), Vanilla JavaScript (ES6+), Python Flask, MySQL e SQLAlchemy**.

---

## Sumário

1. [Contexto e Identidade Visual (Design System)](#1-contexto-e-identidade-visual-design-system)
2. [Decisões Arquiteturais e de Produto (ADRs)](#2-decisões-arquiteturais-e-de-produto-adrs)
3. [Stack Tecnológica](#3-stack-tecnológica)
4. [Arquitetura e Estrutura de Diretórios](#4-arquitetura-e-estrutura-de-diretórios)
5. [Modelagem do Banco de Dados (MySQL + SQLAlchemy)](#5-modelagem-do-banco-de-dados-mysql--sqlalchemy)
6. [Detalhamento da Construção por Tela](#6-detalhamento-da-construção-por-tela)
7. [Motor de Markdown Técnico e Sintaxes Customizadas](#7-motor-de-markdown-técnico-e-sintaxes-customizadas)
8. [ Catálogo de Rotas e APIs REST](#8-catálogo-de-rotas-e-apis-rest)
9. [Instalação, Configuração do MySQL e Execução](#9-instalação-configuração-do-mysql-e-execução)
10. [Testes Automatizados](#10-testes-automatizados)

---

## 1. Contexto e Identidade Visual (Design System)

O portal segue a filosofia estética **"Precision Connectivity"** da Goose Tecnologia — combinando a clareza editorial de publicações de engenharia com a estética de terminais de operação de rede (NOC):

- **Paleta de Cores**:
  - **Goose Primary Orange**: `#EE7D1E` (hover `#D56B12`)
  - **Superfícies Light Mode (Portal Público e Leitura)**: `#FAFAFA` (background principal), `#FFFFFF` (cards e superfícies), `#F8FAFC` (painéis técnicos), `#09090B` (textos de alto contraste).
  - **Superfícies Dark Mode (Terminais CLI e Editor Split-Screen)**: `#0B0F19` / `#0F172A` com bordas `#1E293B`.
- **Tipografia**:
  - **Títulos e Headlines (`font-display`)**: `Manrope` (pesos 600, 700, 800)
  - **Corpo Editorial e Leitura Longa (`font-sans`)**: `Inter` (pesos 300, 400, 500, 600, 700)
  - **Código, Topologias ASCII, Slugs e Metadados (`font-mono`)**: `JetBrains Mono` (pesos 400, 500, 600, 700)
- **Mapeamento de Telas do Stitch (`Project ID: 2523588531873957096`)**:
  1. `67b5e20430d0432f9134d2ae075a3590` — *GOOSE TECNOLOGIA - Blog Minimalista Telecom & ISPs*
  2. `9e3dec84ff7a43d0ba1ed25758f3a7b6` — *GOOSE TECNOLOGIA - Artigo Minimalista: Arquitetura BGP (Light Mode & PDF)*
  3. `3a8ecfd5784b4e13b4d17045da987846` — *GOOSE TECNOLOGIA - CMS & Gestão Editorial do Blog*
  4. `920d16d542ae44579d74c25499c01b06` — *GOOSE TECNOLOGIA - Editor Markdown & Ensaio Técnico*

---

## 2. Decisões Arquiteturais e de Produto (ADRs)

Durante a fase de planejamento (`/plan`), três decisões fundamentais definiram a arquitetura final:

### Decisão 1 — Escopo da Home Pública
- **Contexto**: O projeto no Stitch possuía 4 telas ativas no canvas e 1 tela oculta de versão anterior.
- **Decisão**: Seguir **estritamente a tela ativa** *"GOOSE TECNOLOGIA - Blog Minimalista Telecom & ISPs"*, composta por Header minimalista com busca rápida (`⌘K`), Artigo Principal em Destaque (*Hero Badge*), Grid de Artigos com filtros dinâmicos por categoria/tags/ordenação, Modal de Leitura Rápida, Modal de Diagnóstico Técnico (captura de leads) e navegação direta para as páginas completas de artigo.

### Decisão 2 — Autenticação e Controle de Acesso do Goose CMS
- **Contexto**: Necessidade de proteger as rotas de gestão editorial (`/cms`, `/cms/editor` e endpoints `/api/cms/*`) mantendo suporte aos dois autores técnicos exibidos no design (**Francisco Santos** e **Wandeson**).
- **Decisão**: Implementar autenticação baseada em banco de dados com usuário/e-mail e senha criptografada via `werkzeug.security` (`generate_password_hash` / `check_password_hash`).
  - As contas dos autores são criadas automaticamente pelo seed inicial (`francisco@goose.tec.br` e `wandeson@goose.tec.br`).
  - Em `app/extensions.py`, foi construída uma camada de autenticação compatível tanto com `Flask-Login` quanto com sessão nativa do `Flask` (`session` + `g`), garantindo funcionamento imediato mesmo em ambientes restritos ou offline.

### Decisão 3 — Banco de Dados MySQL com Fallback Resiliente e Auto-Seed
- **Contexto**: A stack requer **Flask + MySQL + SQLAlchemy**, mas o ambiente de desenvolvimento ou testes pode eventualmente rodar sem o serviço MySQL ativo no momento do boot.
- **Decisão**:
  1. Configurar a conexão primária via `PyMySQL` e variáveis de ambiente (`.env`: `DATABASE_URL=mysql+pymysql://root:@localhost:3306/blog_gtecnologia?charset=utf8mb4`).
  2. Implementar em `config.py` (`resolve_database_uri`) a tentativa automática de conexão ao servidor MySQL e execução de `CREATE DATABASE IF NOT EXISTS blog_gtecnologia CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`.
  3. Caso o MySQL não esteja acessível e `ALLOW_SQLITE_FALLBACK=true`, realizar fallback transparente para SQLite (`blog_gtecnologia.db`) sem interromper a aplicação.
  4. Executar em `app/seed.py` um seed **idempotente** que popula autores, categorias, tags e os **7 ensaios técnicos** do design no primeiro boot.

---

## 3. Stack Tecnológica

| Camada | Tecnologias Utilizadas |
| :--- | :--- |
| **Frontend** | HTML5 Semântico (Jinja2), Tailwind CSS, CSS3 Customizado (`@media print` A4), Vanilla JavaScript (ES6+), Web Speech API (GooCast TTS) |
| **Backend** | Python 3.10+, Flask 3.x, Blueprints modulares (`public`, `auth`, `cms`) |
| **ORM & Banco de Dados** | SQLAlchemy 2.x, Flask-SQLAlchemy, MySQL 8+ (`PyMySQL`), Fallback SQLite |
| **Processamento Editorial** | Python `Markdown` + Pipeline Regex Customizado (`app/utils/markdown_renderer.py`) |
| **Segurança** | `Werkzeug Security` (Password Hashing PBKDF2/Scrypt), Proteção de rotas `@login_required` |
| **Testes** | `unittest` (Standard Library) com banco em memória (`sqlite:///:memory:`) |

---

## 4. Arquitetura e Estrutura de Diretórios

```mermaid
flowchart TB
    subgraph Client["Camada Cliente (Browser)"]
        PUB["Portal Público\nblog.js / article.js"]
        ADM["Goose CMS v2.4\ncms_dashboard.js / cms_editor.js"]
    end

    subgraph FlaskApp["Aplicação Flask (app/)"]
        INIT["Application Factory\napp/__init__.py"]
        BP_PUB["Blueprint Público\napp/routes/public.py"]
        BP_AUTH["Blueprint Auth\napp/routes/auth.py"]
        BP_CMS["Blueprint CMS\napp/routes/cms.py"]
        MDR["Motor Markdown + TOC\napp/utils/markdown_renderer.py"]
        SEED["Seed Idempotente\napp/seed.py"]
    end

    subgraph DataLayer["Camada de Dados"]
        ORM["Modelos SQLAlchemy\napp/models.py"]
        MYSQL[("MySQL 8+\nblog_gtecnologia")]
        SQLITE[("SQLite Fallback\nblog_gtecnologia.db")]
    end

    PUB --> BP_PUB
    ADM --> BP_AUTH
    ADM --> BP_CMS
    BP_PUB --> MDR
    BP_CMS --> MDR
    BP_PUB --> ORM
    BP_AUTH --> ORM
    BP_CMS --> ORM
    INIT --> SEED
    SEED --> ORM
    ORM --> MYSQL
    ORM -. "Fallback se MySQL offline" .-> SQLITE
```

### Árvore de Arquivos do Projeto

```text
blog_gtecnologia/
├── .env                          # Variáveis de ambiente ativas (MySQL URL, Secret Key, Fallback)
├── .env.example                  # Template de variáveis de ambiente
├── config.py                     # Configuração Flask, resolução de URI MySQL e auto-create DB
├── requirements.txt              # Lista de dependências Python
├── run.py                        # Ponto de entrada da aplicação (servidor local porta 5000)
├── README.md                     # Documentação completa do projeto
├── app/
│   ├── __init__.py               # Application Factory (create_app), filtros Jinja e boot do banco
│   ├── extensions.py             # Instâncias SQLAlchemy e gerenciador de autenticação
│   ├── models.py                 # Modelos: User, Category, Tag, Article, Lead e article_tags
│   ├── seed.py                   # População inicial idempotente (autores, categorias e 7 artigos)
│   ├── utils/
│   │   └── markdown_renderer.py  # Parser Markdown técnico, terminais CLI, topologia ASCII e TOC
│   ├── routes/
│   │   ├── public.py             # Rotas do blog (/ e /blog/<slug>) e APIs públicas (/api/articles, /api/leads)
│   │   ├── auth.py               # Login e logout do CMS (/cms/login, /cms/logout)
│   │   └── cms.py                # Rotas do CMS (/cms, /cms/editor) e APIs CRUD (/api/cms/*)
│   ├── static/
│   │   ├── css/
│   │   │   └── styles.css        # Estilos customizados, Modo Zen, animações e @media print (PDF A4)
│   │   ├── img/
│   │   │   └── goose_logo_horizontal.png # Logo oficial extraída do projeto Stitch
│   │   └── js/
│   │       ├── blog.js           # Filtros, busca, ordenação, modal de leitura e modal de leads
│   │       ├── article.js        # Barra de leitura, Modo Zen, GooCast Audio Player, PDF e copiar código
│   │       ├── cms_dashboard.js  # Filtros da tabela CMS, Inspetor de Metadados e ações rápidas
│   │       └── cms_editor.js     # Editor Split-Screen, preview live, snippets, atalhos e autosave
│   └── templates/
│       ├── base_public.html      # Layout mestre do portal público (Header, Modais, Footer)
│       ├── base_cms.html         # Layout mestre do Goose CMS
│       ├── public/
│       │   ├── index.html        # Tela 1: Home Minimalista Telecom & ISPs
│       │   └── article.html      # Tela 2: Página de Artigo Minimalista (Light Mode & PDF)
│       └── cms/
│           ├── login.html        # Tela de autenticação do Goose CMS
│           ├── dashboard.html    # Tela 3: CMS & Gestão Editorial do Blog
│           └── editor.html       # Tela 4: Editor Markdown & Ensaio Técnico
└── tests/
    └── test_app.py               # Suíte de testes automatizados de ponta a ponta
```

---

## 5. Modelagem do Banco de Dados (MySQL + SQLAlchemy)

```mermaid
erDiagram
    USERS ||--o{ ARTICLES : "escreve (author_id)"
    CATEGORIES ||--o{ ARTICLES : "classifica (category_id)"
    ARTICLES }o--o{ TAGS : "possui (article_tags)"

    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string name
        string role_title
        text bio
        string avatar_initials
        string avatar_color
        datetime created_at
    }

    CATEGORIES {
        int id PK
        string name
        string slug UK
        string badge_color
        string icon_name
    }

    TAGS {
        int id PK
        string name
        string slug UK
    }

    ARTICLES {
        int id PK
        string title
        string subtitle
        string slug UK
        text excerpt
        string meta_description
        longtext content_markdown
        string status "published | review | draft"
        boolean is_hero
        boolean enable_zen_mode
        boolean enable_goocast
        string goocast_duration
        int reading_time_minutes
        int views_count
        string doc_id
        string version_label
        int category_id FK
        int author_id FK
        datetime published_at
        datetime created_at
        datetime updated_at
    }

    LEADS {
        int id PK
        string name
        string isp_asn
        string whatsapp
        string source_page
        datetime created_at
    }
```

---

## 6. Detalhamento da Construção por Tela

### Tela 1: Blog Minimalista Telecom & ISPs (`GET /`)
- **Arquivos**: `app/templates/public/index.html` e `app/static/js/blog.js`.
- **Funcionalidades**:
  - **Header Minimalista**: Logo oficial Goose Tecnologia, links de navegação editorial, atalho de busca rápida (`⌘K` / `Ctrl+K`), link para o CMS e CTA *"Agendar Conversa"*.
  - **Artigo em Destaque (Hero Card)**: Exibe dinamicamente o artigo marcado com `is_hero = True` no banco de dados (por padrão: *"O Fim do Robô Burro no Provedor: Como Agentes de IA Resolvem 74% do Nível 1"*), com metadados do autor, tempo de leitura, botão para leitura completa e botão de resumo rápido.
  - **Barra de Filtros e Pesquisa em Tempo Real**:
    - Filtro instantâneo por abas de categoria (`Todos os Artigos`, `Redes & BGP`, `Gestão & NOC`, `Automação & IA`, `Vendas & Escala`).
    - Filtro cumulativo por *Quick Tags* (`#MikroTik`, `#BGP`, `#OLT`, `#WhatsAppAPI`, `#Churn`, `#Observabilidade`).
    - Busca textual por título, resumo, autor ou tag com contador dinâmico de resultados.
    - Ordenação por **Mais Recentes**, **Mais Lidos (Popularidade)** ou **Menor Tempo de Leitura**.
  - **Modal de Leitura Rápida**: Consome `GET /api/articles/<slug>` para abrir o ensaio técnico formatado sem sair da Home, incluindo botão de compartilhamento e link para a visão completa.
  - **Modal de Diagnóstico Técnico (Captura de Leads)**: Formulário conectado a `POST /api/leads`, validando e gravando `Nome`, `Provedor / ASN` e `WhatsApp` diretamente na tabela `leads`.

### Tela 2: Página de Artigo Minimalista — Light Mode & PDF (`GET /blog/<slug>`)
- **Arquivos**: `app/templates/public/article.html` e `app/static/js/article.js`.
- **Funcionalidades**:
  - **Barra de Progresso de Leitura**: Indicador superior fixo calculado conforme o scroll do artigo e tempo restante de leitura.
  - **Player GooCast Audio com Narração Real (`Web Speech API` `pt-BR`)**:
    - Ao clicar em **Play**, extrai automaticamente o título e os parágrafos do artigo (ignorando blocos de código) e **narra o artigo em voz alta em Português (`pt-BR`)**, selecionando a melhor voz natural instalada no navegador.
    - Suporta **Pause / Resume**, alternância de velocidade em tempo real (**`1.0x` / `1.25x` / `1.5x` / `2.0x`**) e clique direto nas barras de onda sonora (`scrubAudio`) para avançar ou retroceder pelos parágrafos.
  - **Alternância Light Mode / Dark Mode & Modo Leitura Zen**:
    - Botão de troca instantânea entre o tema escuro NOC e o *Engineering Light Mode* (persistido em `localStorage`).
    - **Modo Zen**: Oculta cabeçalho, barra lateral e seções extras para foco total na leitura técnica (acionável também via `ESC` para sair).
  - **Exportação PDF Técnico (A4)**: Botão *"PDF"* que aciona `window.print()` com folha de estilo `@media print` dedicada em `app/static/css/styles.css`, formatando cabeçalho técnico, blocos de código com bordas claras e ocultando elementos interativos.
  - **Sidebar Esquerda (Sticky)**: Sumário Técnico (`TOC`) gerado automaticamente a partir dos cabeçalhos `H2` (`##`) do Markdown com *scrollspy* ativo.
  - **Card Dinâmico de Assinatura & Bio do Autor**: Exibe automaticamente a foto, nome, cargo/especialidade e mini bio do autor/redator responsável pelo artigo (ou o card de co-autoria *Francisco & Wandeson*).

### Tela 3: CMS & Gestão Editorial do Blog (`GET /cms`)
- **Arquivos**: `app/templates/cms/dashboard.html` e `app/static/js/cms_dashboard.js`.
- **Funcionalidades**:
  - **KPIs de Engenharia Editorial**: Total de artigos, publicados ativos, ensaios em revisão/rascunho, visualizações acumuladas e total de leads capturados.
  - **Tabela de Artigos com Filtros Combinados**: Filtragem instantânea por status (`Todos`, `Publicados`, `Rascunhos`, `Em Revisão`, `Arquivados`), autor dinâmico e busca por título/slug/tag.
  - **Ações Rápidas por Linha**: Editar no Editor Markdown, visualizar página pública, duplicar artigo (`POST /api/cms/articles/<id>/duplicate`), publicar imediatamente (`POST /api/cms/articles/<id>/status`) e excluir (`DELETE /api/cms/articles/<id>`).
  - **Inspetor Lateral de Metadados**: Ao clicar em qualquer artigo da tabela, o painel direito atualiza o preview SERP do Google, o card OpenGraph e os switches de comportamento editorial (**Fixar no Hero (`is_hero`)**, **Modo Zen (`enable_zen_mode`)** e **GooCast Podcast (`enable_goocast`)**).
  - **Gestão Completa de Autores & Redatores (`/cms#autores`)**:
    - Painel CRUD completo na aba **Autores & Redatores** para **Criar, Editar e Excluir** autores e redatores técnicos;
    - Campos para **Nome de Exibição**, **Cargo / Especialidade**, **Identificador (`username`)**, **E-mail**, **Senha de acesso ao CMS**, **Foto / Avatar** (via URL ou upload direto de arquivo) e **Mini Bio Técnica**;
    - Atualização em cascata: ao editar o nome ou cargo de um autor, todos os artigos vinculados a ele são atualizados automaticamente.
  - **Painéis Secundários Integrados**:
    - **Tópicos & Telecom (`/cms#topicos`)**: Visualização de categorias e taxonomia de tags;
    - **Métricas & Leads (`/cms#leads`)**: Tabela de leads de provedores/ASNs capturados no portal;
    - **Mídia & Diagramas (`/cms#midia`)**: Galeria de imagens e diagramas enviados;
    - **Logs de Publicação (`/cms#logs`)**: Trilha de auditoria (`AuditLog`) de todas as ações feitas no CMS.
  - **Exportação JSON**: Botão *"Exportar Markdown/JSON"* conectado a `GET /api/cms/export` para download imediato de backup estruturado de todos os artigos.

### Tela 4: Editor Markdown & Ensaio Técnico (`GET /cms/editor` e `GET /cms/editor/<id>`)
- **Arquivos**: `app/templates/cms/editor.html` e `app/static/js/cms_editor.js`.
- **Funcionalidades**:
  - **Interface Split-Screen**:
    - **Painel Esquerdo (`raw_post_buffer.md`)**: Buffer de escrita em fonte monoespaçada (`JetBrains Mono`) com numeração de linhas sincronizada, estatísticas de cursor (`Ln / Col`), contagem de palavras e blocos de script.
    - **Painel Direito (`Preview do Leitor`)**: Preview em tempo real (via `POST /api/cms/preview`) que renderiza exatamente o visual final do artigo.
  - **Gestão Rápida de Autores sem Sair do Editor**:
    - Ao lado do seletor **"Autor Técnico Responsável"**, o botão **`+ Criar / Editar`** abre um modal rápido que permite cadastrar, editar ou excluir autores/redatores e atualizar a lista imediatamente **sem recarregar a página e sem perder o rascunho Markdown**.
  - **Inserção Rápida de Snippets de Engenharia**:
    - Botões dedicados na toolbar para inserir blocos prontos de **CLI MikroTik RouterOS v7**, **BGP Bird2 / FRR**, **Linux CGNAT**, **Python Netmiko**, **JSON Telemetry**, **Alerta NOC**, **Diagrama Topológico SVG** e **Tabela Benchmark RFC 1997**.
  - **Upload de Capa & Atalho `Ctrl+S` / `⌘S`**:
    - Upload direto de imagem de capa (`POST /api/cms/upload`) com atualização imediata do preview OpenGraph.

---

## 7. Motor de Markdown Técnico e Sintaxes Customizadas

O módulo `app/utils/markdown_renderer.py` estende a sintaxe Markdown padrão com blocos voltados para documentação de redes, telecomunicações e multimídia:

### 1. Blocos de Código CLI com Botão de Cópia
Use ` ```mikrotik `, ` ```bgp `, ` ```bash `, ` ```python ` ou ` ```json ` (opcionalmente seguido de `|Título Customizado`):

````markdown
```mikrotik|MikroTik RouterOS v7.14+ CLI
/routing bgp connection
add name="TRANSITO-OPERADORA-A" \
    remote.address=198.51.100.1/32 .as=65001 \
    local.role=ebgp .as=265432
```
````

### 2. Callouts de Alerta Operacional (NOC)
Use `:::noc-warning` com `title:` opcional na primeira linha:

```markdown
:::noc-warning
title: Protocolo de Segurança NOC Goose
Nunca aplique filtros de comunidades BGP em produção sem antes validar a tabela recebida usando `print where` no RouterOS v7.
:::
```

### 3. Diagrama Topológico BGP SVG
Use a tag `:::topology-bgp:::` para incorporar o diagrama vetorial de borda multihomed:

```markdown
:::topology-bgp:::
```

### 4. Checklists Operacionais Interativos no Markdown
Qualquer lista Markdown com `- [x]` ou `- [ ]` é automaticamente convertida em cards interativos de checklist no artigo:

```markdown
- [x] Sessões eBGP IPv4 e IPv6 em estado `established`
- [x] Filtro de Bogons e prefixos maiores que `/24` ativo em `in-filter`
- [ ] Teste de failover desligando interface de uplink primário
```

### 5. Incorporação Responsiva de Vídeos (YouTube / Vimeo)
Qualquer `<iframe ...>` colado no Markdown é automaticamente ajustado pelo CSS (`styles.css`) para `width: 100%`, `max-width: 100%` e proporção `16:9`, sem ultrapassar a largura da coluna do artigo (`818px` no desktop):

```html
<iframe width="100%" height="450" style="max-width: 100%; aspect-ratio: 16 / 9; height: auto; border-radius: 12px;" src="https://www.youtube.com/embed/G4Wg8ZV2mak" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
```

---

## 8. Catálogo de Rotas e APIs REST

### Rotas Públicas e APIs do Portal (`app/routes/public.py`)
| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/` | Renderiza a Home Minimalista com artigo Hero, filtros, categorias e grid de artigos publicados. |
| `GET` | `/blog/<slug>` | Renderiza a página completa do ensaio técnico com Light/Dark Mode, TOC, GooCast TTS e suporte a PDF. |
| `GET` | `/api/articles/<slug>` | Retorna o JSON completo do artigo + `rendered_html` e `toc_items` para o Modal de Leitura Rápida. |
| `POST` | `/api/leads` | Registra um novo lead de diagnóstico técnico (`name`, `isp_asn`, `whatsapp`, `source_page`). |

### Rotas de Autenticação (`app/routes/auth.py`)
| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET, POST` | `/cms/login` | Autentica editores por usuário ou e-mail e senha com hash seguro. |
| `GET` | `/cms/logout` | Encerra a sessão autenticada do editor. |

### Rotas e APIs do Goose CMS (`app/routes/cms.py`)
| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/cms` | Dashboard de gestão editorial, KPIs, tabela filtrável, Inspetor de Metadados e aba de Autores. |
| `GET` | `/cms/editor` | Abre o Editor Markdown Split-Screen para criação ou edição de ensaios técnicos. |
| `GET` | `/cms/editor/<id>` | Abre o Editor Markdown Split-Screen carregando um artigo específico pelo ID. |
| `POST` | `/api/cms/articles` | Cria ou atualiza um artigo completo (título, slug, autor, categoria, tags, flags e Markdown). |
| `POST` | `/api/cms/articles/<id>/metadata` | Salva alterações rápidas de SEO e switches feitas no Inspetor de Metadados da Dashboard. |
| `POST` | `/api/cms/articles/<id>/status` | Alterna o status do artigo (`published`, `review`, `draft`, `archived`). |
| `POST` | `/api/cms/articles/<id>/duplicate` | Cria uma cópia em rascunho (`draft`) de um artigo existente. |
| `DELETE` | `/api/cms/articles/<id>` | Remove permanentemente um artigo do banco de dados. |
| `GET` | `/api/cms/authors` | Lista todos os autores e redatores técnicos cadastrados. |
| `POST` | `/api/cms/authors` | Cria um novo autor/redator ou atualiza um existente (sincronizando artigos vinculados). |
| `DELETE` | `/api/cms/authors/<id>` | Remove um autor/redator (mantendo integridade referencial dos artigos). |
| `POST` | `/api/cms/upload` | Realiza upload de imagens de capa, diagramas ópticos e avatares de autores para `/static/uploads/`. |
| `POST` | `/api/cms/preview` | Recebe Markdown bruto e devolve HTML técnico renderizado + TOC + tempo de leitura em tempo real. |
| `GET` | `/api/cms/export` | Exporta um arquivo `.json` com o dump completo de todos os artigos cadastrados. |

---

## 9. Instalação, Configuração do MySQL e Execução

### Pré-requisitos
- **Python 3.10+**
- **MySQL 8.0+** (Opcional para desenvolvimento rápido caso `ALLOW_SQLITE_FALLBACK=true` esteja ativo no `.env`)

### Passo 1 — Instalar Dependências
No diretório raiz do projeto, execute:

```powershell
python -m pip install -r requirements.txt
```

### Passo 2 — Configurar Variáveis de Ambiente (`.env`)
O arquivo `.env` na raiz do projeto já está configurado com os valores padrão:

```ini
FLASK_ENV=development
SECRET_KEY=goose-tecnologia-isp-telecom-secret-key-2026
DATABASE_URL=mysql+pymysql://root:@localhost:3306/blog_gtecnologia?charset=utf8mb4
ALLOW_SQLITE_FALLBACK=true
```
- Se o seu MySQL local possuir senha para o usuário `root`, ajuste `DATABASE_URL=mysql+pymysql://root:SUA_SENHA@localhost:3306/blog_gtecnologia?charset=utf8mb4`.
- Na inicialização, a aplicação criará automaticamente o banco `blog_gtecnologia`, todas as tabelas e fará o seed dos **7 artigos técnicos** e dos **2 autores**.

### Passo 3 — Iniciar o Servidor
```powershell
python run.py
```

Acesse no navegador:
- **Portal Público (Home)**: `http://localhost:5000/`
- **Artigo Técnico BGP**: `http://localhost:5000/blog/arquitetura-bgp-multihomed-transito-ip`
- **Painel Administrativo (Goose CMS)**: `http://localhost:5000/cms`
- **Editor Markdown Split-Screen**: `http://localhost:5000/cms/editor`

### Credenciais Padrão do Goose CMS
| Autor | E-mail / Usuário | Senha | Cargo |
| :--- | :--- | :--- | :--- |
| **Francisco Santos** | `francisco@goose.tec.br` ou `francisco` | `goose2026` | Principal Network Architect |
| **Wandeson** | `wandeson@goose.tec.br` ou `wandeson` | `goose2026` | Head de Operações & Automação ISP |

---

## 10. Testes Automatizados

O projeto conta com uma suíte de testes de integração em `tests/test_app.py` que valida:
1. Criação de tabelas e população do seed inicial (autores, categorias, tags e os 7 artigos do design Stitch);
2. Renderização da Home pública (`/`) e da página de artigo (`/blog/arquitetura-bgp-multihomed-transito-ip`) com blocos MikroTik, callout NOC, topologia ASCII e checklist;
3. Endpoint JSON do modal de leitura rápida (`/api/articles/<slug>`) e submissão de leads (`/api/leads`);
4. Proteção de rotas do CMS (`/cms` redirecionando visitantes anônimos para `/cms/login`) e login com credenciais de autor;
5. Fluxo completo de CRUD no CMS: criação de ensaio via API do Editor, atualização de flags no Inspetor de Metadados, duplicação, exclusão e exportação JSON (`/api/cms/export`).

Para executar os testes:

```powershell
python -m unittest discover -s tests -v
```

