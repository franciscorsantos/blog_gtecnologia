from datetime import datetime, timezone
from app.extensions import db
from app.models import User, Category, Tag, Article, Lead, MediaAsset, AuditLog


BGP_ARTICLE_CONTENT = """# Arquitetura BGP Multihomed com Comunidades de Trânsito IP para Provedores de Alta Disponibilidade

:::noc-warning
title: Protocolo de Segurança NOC Goose
Atenção ao tempo de convergência durante o anúncio das rotas completas (*Full-Routing*). Aplique os `routing filter rule` antes de habilitar as sessões eBGP em produção durante horários de pico.
:::

## Topologia de Borda & Requisitos Físicos

O crescimento vertiginoso de assinantes FTTH impõe uma exigência inegociável aos Sistemas Autônomos (ASNs): o fim da dependência de um trânsito IP monopolista. Manter uma única operadora de trânsito em um POP de borda cria um ponto único de falha (*SPOF - Single Point of Failure*) inaceitável para contratos corporativos e conexões residenciais de alta densidade.

Para atingir alta disponibilidade real, o cenário recomendado pela Goose Tecnologia utiliza duas operadoras Tier-1 fisicamente desconectadas em portas de 10Gbps/100Gbps QSFP28, além de uma ligação direta com o PTT local (**IX.br**), controlados por uma caixa de altíssimo throughput como a MikroTik Cloud Core Router CCR2216-1G-12XS-2XQ.

:::topology-bgp:::

## Alinhamento de ASN & Roteamento eBGP

No RouterOS v7, a stack de roteamento foi totalmente reescrita sobre o kernel Linux 5.x. As antigas instâncias do v6 foram substituídas pela estrutura de **BGP Templates** e conexões explícitas. Isso confere suporte a multithreading real, reduzindo o tempo de convergência de uma tabela completa de 4 minutos para meros 12 segundos.

Abaixo disponibilizamos a receita padrão de template para eBGP multihomed com ativação de BFD (Bidirectional Forwarding Detection) e suporte estendido a comunidades de 32-bits.

```mikrotik|RouterOS v7.14+ CLI — Template eBGP
# Goose Telecom Lab - BGP Template Borda Multihomed
/routing bgp template
add name="GOOSE-TRANSITO-BASE" \\
    as=263481 \\
    router-id=187.60.10.1 \\
    address-families=ip,ipv6 \\
    keepalive-time=10s \\
    hold-time=30s \\
    multihop=no \\
    use-bfd=yes \\
    output.redistribute="" \\
    output.network="bgp-networks"
```

## Filtros RouterOS v7 (Routing Filter Rule)

No RouterOS v7, a sintaxe de filtros BGP mudou radicalmente para um formato de lógica condicional programática: `if (...) { ... }`. Filtros mal dimensionados podem fazer com que seu provedor se torne acidentalmente um sistema de trânsito aberto, gerando congestionamento catastrófico.

```routeros|RouterOS v7 Routing Filter Rules — Tratamento de Comunidade
/routing filter rule
# 1. Preferencia para PTT Local (IX.br)
add chain="IXBR-IN" rule="if (bgp-communities includes 26162:*) { set bgp-local-pref 200; accept; }"

# 2. Transito A: Atribui comunidade de descarte de anuncio regional
add chain="TRANSITO-A-OUT" rule="if (dst in 187.60.10.0/22) { set bgp-communities append:6762:100; accept; }"

# 3. Transito B (Backup): Prepend duplo como contingencia passiva
add chain="TRANSITO-B-OUT" rule="if (dst in 187.60.10.0/22) { set bgp-path-prepend 2; accept; }"
```

## BGP Prepend vs Comunidades de Trânsito RFC 1997

O erro mais recorrente encontrado nos provedores regionais brasileiros é a insistência em manipular o tráfego de download (Downstream) unicamente através de **AS-Path Prepend** repetido (ex: 3 a 5 vezes o mesmo ASN).

Muitos nós transatlânticos e sistemas Tier-1 ignoram comprimentos excessivos de AS-Path em virtude de políticas agressivas de `Local-Preference` configuradas em seus próprios roteadores. A forma determinística e profissional de balancear tráfego é o envio das *BGP Action Communities* estipuladas pela sua operadora:

| Operadora | Comunidade | Ação Executada no Backbone | Eficácia Goose |
| :--- | :--- | :--- | ---: |
| **Lumen (CenturyLink)** | `3549:2000` | Aplica Local-Pref 70 em nós internacionais | **99.8%** |
| **Telxius (Telefônica)** | `12956:0` | Não anunciar rota para pares IX europeus | **100%** |
| **Claro / Embratel** | `4230:80` | Aplica Local-Pref 80 nos PIXs brasileiros | **98.4%** |

## Telemetria e Detecção com BFD (<180ms)

Sem o protocolo BFD (*Bidirectional Forwarding Detection*), uma queda silenciosa na fibra óptica (onde a porta física permanece UP mas o tráfego pára de passar pelo equipamento intermediário DWDM) levará até 90 segundos para expirar o BGP Hold-Timer padrão. Durante esse minuto e meio, 100% do tráfego do provedor é descartado no limbo.

Com o BFD habilitado no RouterOS v7 e alinhado ao peer da operadora, pacotes de keepalive ultraleves são trocados a cada 50ms com multiplicador de 3. O tempo de detecção de falha cai para **150ms**, permitindo que a segunda operadora assuma o tráfego sem que os usuários finais percebam queda em sessões de streaming, chamadas VoIP ou conexões de jogos online.
"""

ROBO_BURRO_CONTENT = """# O Fim do Robô Burro no Provedor: Como usamos IA no WhatsApp sem perder a essência humana

:::noc-warning
title: Alerta de Retenção & Experiência do Assinante (CX)
Nunca force um assinante com perda óptica (*LOS*) na ONU a navegar por menus numéricos de 2ª via de boleto. O cruzamento prévio com telemetria RADIUS e OLT é obrigatório antes da primeira mensagem.
:::

## O Problema da URA Numérica no WhatsApp

O assinante não odeia tecnologia; ele odeia a frieza de um menu numérico circular enquanto sua casa está sem conexão. Quando o provedor implanta um chatbot tradicional baseado em árvore de decisão rígida ("Digite 1 para Financeiro, 2 para Suporte"), o cliente frustrado digita qualquer número apenas para tentar falar com um humano.

Ao cruzar modelos generativos com telemetria direta de **RADIUS** e diagnósticos via **TR-069**, transformamos chamados tensos em respostas resolutivas em **4.8 segundos**.

## Arquitetura de Telemetria Pré-Atendimento

Antes mesmo de o modelo de linguagem processar a mensagem recebida no WhatsApp, o orquestrador da Goose Tecnologia executa três consultas síncronas em menos de 350ms:

* **Consulta ERP & RADIUS**: Verifica status do contrato, histórico de quedas PPPoE nas últimas 24h e se há bloqueio parcial por inadimplência.
* **Leitura Óptica na OLT (SNMP / CLI)**: Mede a potência RX da ONU (`-18.4 dBm` normal vs `-29.5 dBm` atenuação crítica ou `LOS`).
* **Sonda ACS / TR-069**: Inspeciona a tabela de dispositivos conectados no Wi-Fi 2.4GHz/5GHz e nível de interferência RSSI.

```json|Payload de Telemetria Injetado no Contexto do Agente IA
{
  "subscriber_id": 48291,
  "pppoe_user": "marcos.silva.ftth",
  "olt_port": "GPON-0/1/4:CTO-04B",
  "onu_rx_dbm": -28.9,
  "optical_status": "CRITICAL_LOS_DETECTED",
  "tr069_wifi_rssi_avg": -64,
  "active_mass_outage": "ROMPIMENTO_CTO_04B_PREVISAO_15H20"
}
```

## Resultados Práticos em ISPs Regionais

A retenção no primeiro contato subiu **+42%** em ISPs com mais de 10 mil assinantes ativos, mantendo a equipe humana de N2 dedicada a atendimentos complexos e retenção estratégica.

| Métrica Operacional | Bot Tradicional (Menu) | Copiloto IA + Telemetria Goose | Impacto Real |
| :--- | :--- | :--- | ---: |
| **Tempo Médio de 1ª Resposta** | 14 min (fila N1) | `4.8 segundos` | **-99.4%** |
| **Resolução no 1º Contato (FCR)** | 31% | `73%` | **+42%** |
| **Chamados Improdutivos de Campo** | 18% das OS | `4.2% das OS` | **-76%** |
"""

GESTAO_2026_CONTENT = """# Ainda vale a pena abrir Provedor de Internet em 2026? A verdade nua e crua

:::noc-warning
title: Análise Financeira & CAPEX de Rede
O ciclo de crescimento desordenado por ocupação predatória de postes acabou. A rentabilidade líquida em 2026 exige rigor no controle de Churn, ocupação de portas CTO acima de 65% e ticket médio blindado por SVA real.
:::

## A Nova Realidade do Mercado ISP Brasileiro

Consolidação de operadoras neutras, saturação de postes e guerra de preços em grandes centros urbanos mudaram completamente a matemática de retorno sobre o capital investido (ROIC) no setor de telecomunicações.

Enquanto provedores amadores disputam assinantes por R$ 59,90 sem calcular o custo de reposição de ONUs Wi-Fi 6 e o aluguel de pontos de fixação, operações enxutas com engenharia de rede bem desenhada atingem margens EBITDA superiores a **38%**.

## Onde Está a Margem Líquida em 2026?

* **Densificação de CTOs Existentes**: Vender em caixas já lançadas custa 70% menos CAPEX do que abrir novas rotas de backbone sem âncora comercial.
* **Redução Drástica de Opex Operacional**: Cada visita técnica evitada via diagnóstico remoto TR-069 preserva a margem líquida de até 3 mensalidades daquele assinante.
* **Atendimento B2B e Links Dedicados**: O mercado corporativo regional continua subatendido em SLA real de 4 horas e dupla abordagem física.

```python|Simulador de Payback por Porta CTO (Python Financial CLI)
def calcular_payback_assinante(ticket_medio=109.90, custo_instalacao=480.0, margem_op=0.62):
    contribuicao_mensal = ticket_medio * margem_op
    meses_payback = custo_instalacao / contribuicao_mensal
    return round(meses_payback, 1)

# Com ONU Wi-Fi 6 em comodato + mão de obra própria:
print(f"Payback estimado: {calcular_payback_assinante()} meses")  # 7.1 meses
```
"""

WHATSAPP_BOT_CONTENT = """# Atendimento no WhatsApp: onde o bot ajuda na 2ª via e onde ele destrói a base

:::noc-warning
title: Regra de Ouro do CX em Provedores
Automatizar Pix e 2ª via é obrigação. O erro fatal é submeter assinantes com instabilidade física ou lentidão severa ao mesmo funil burocrático de faturamento.
:::

## Quando a Automação Salva a Operação Financeira

Nos dias de vencimento (5, 10, 15 e 20), até **68% do volume de mensagens** no WhatsApp de um provedor refere-se exclusivamente a segunda via de boleto, código Pix Copia e Cola ou desbloqueio em confiança.

Para esse perfil de demanda, o fluxo rápido sem atrito resolve a solicitação em menos de 15 segundos, liberando o caixa do provedor imediatamente via integração webhook com o gateway bancário e desbloqueio automático no RADIUS.

## Onde o Bot Tradicional Destrói a Base (Churn Invisível)

Quando o cliente reclama pela terceira vez no mês que a internet cai às 20h durante jogos ou chamadas de vídeo, qualquer resposta robotizada mandando "tirar o roteador da tomada por 30 segundos" funciona como um gatilho imediato de cancelamento.

```mikrotik|Script RouterOS / RADIUS Disconnect para Reconexão Limpa de PPPoE
# Reconexao cirurgica de sessao PPPoE travada apos manobra de CGNAT
/ppp active
:foreach idx in=[find where name="cliente.fibra.01"] do={
    :log info "Goose CX: Reiniciando sessao PPPoE para renovacao de perfil"
    remove $idx
}
```
"""

WIFI_MESH_CONTENT = """# Wi-Fi MESH na prática: acabando com chamados de lentidão doméstica

:::noc-warning
title: Diagnóstico de Espectro RF Residencial
Mais de 70% dos chamados de "internet lenta" em planos acima de 400 Mega têm fibra óptica perfeita na ONU (-18 dBm), mas degradação severa de sinal Wi-Fi (-78 dBm) nos cômodos distantes.
:::

## Por que o Roteador Único Não Entrega 600 Mega na Casa Toda?

A física das ondas de rádio em **5GHz (802.11ac/ax)** impõe alta atenuação ao atravessar alvenaria, lajes e espelhos. Quando o smartphone do assinante perde o sinal de 5GHz no quarto e faz *fallback* para 2.4GHz congestionado, a banda despenca de 500 Mbps para menos de 25 Mbps.

## Protocolos 802.11k/v/r e Fast Roaming

A implementação de redes **Wi-Fi MESH gerenciadas via TR-069** resolve o problema na raiz através de três pilares:

* **802.11k (Radio Resource Measurement)**: Auxilia o dispositivo a descobrir rapidamente o nó Mesh mais próximo.
* **802.11v (Wireless Network Management)**: Direciona ativamente o cliente (*Band Steering* e *Client Steering*) antes que o sinal caia abaixo de `-72 dBm`.
* **802.11r (Fast BSS Transition)**: Realiza a troca de antena em menos de 40ms sem derrubar chamadas WhatsApp ou partidas online.

```json|Perfil TR-069 de Provisionamento Automático Mesh (ACS Goose)
{
  "Device.WiFi.MultiAP.Enable": true,
  "Device.WiFi.AccessPoint.1.BandSteering.RSSIThreshold": -70,
  "Device.WiFi.AccessPoint.1.IEEE80211kEnabled": true,
  "Device.WiFi.AccessPoint.1.IEEE80211vEnabled": true,
  "Device.WiFi.AccessPoint.1.IEEE80211rEnabled": true
}
```
"""

TONY_SANDERSON_CONTENT = """# Estratégias Comerciais para Provedores Regionais com Tony Sanderson

:::noc-warning
title: Episódio Especial GOOCAST #2
Como alinhar a engenharia de rede (portas livres por CTO) com a máquina comercial PAP (Porta a Porta) e tráfego pago geolocalizado.
:::

## Venda Orientada à Viabilidade Óptica por CTO

Um dos maiores desperdícios financeiros nos provedores regionais é investir em mídia aberta para bairros inteiros onde 80% das CTOs já estão lotadas, enquanto caixas recém-ativadas permanecem com 14 portas ociosas.

Neste episódio de 1h14m do **GOOCAST**, Francisco e Wandeson recebem **Tony Sanderson** para detalhar o método de mapeamento comercial por mancha de calor das CTOs.

## Principais Tópicos do Episódio

* **Mapeamento de Portas Livres**: Como transformar o inventário do sistema de georreferenciamento (Ozmap / Geosite) na rota diária dos vendedores PAP.
* **Comissionamento Inteligente**: Premiar mais o vendedor que ocupa CTOs com baixa penetração e que vende planos com Wi-Fi Mesh incluso.
* **Redução da Inadimplência da 1ª Mensalidade**: Filtros de pré-qualificação comercial que evitam o "cliente nômade".
"""

IPV6_DRAFT_CONTENT = """# Migração IPv6 nativa em CGNAT: Guia definitivo para NOC de Provedor

:::noc-warning
title: Rascunho Técnico em Validação no Lab Goose
Atenção ao dimensionamento de pools PD (Prefix Delegation /56) no servidor RADIUS para evitar exaustão prematura ou quebra de rotas estáticas em clientes corporativos.
:::

## Por que o Dual-Stack com IPv6 /56 Alivia 65% do seu CGNAT?

Grandes provedores de conteúdo (Google/YouTube, Meta, Netflix, Akamai e Cloudflare) priorizam conexões nativas em **IPv6** via algoritmo *Happy Eyeballs (RFC 8305)*. Quando o seu assinante recebe um bloco IPv6 funcional na WAN e `/64` na LAN via SLAAC/DHCPv6-PD, a maior parte do tráfego pesado deixa de passar pelas caixas de CGNAT IPv4.

## Configuração Base de DHCPv6-PD e ND no RouterOS v7

```mikrotik|Configuração de Pool IPv6 /56 para Assinantes PPPoE
/ipv6 pool
add name=POOL-ASSINANTES-PD prefix=2804:49fc:1000::/40 prefix-length=56
add name=POOL-ASSINANTES-WAN prefix=2804:49fc:0f00::/44 prefix-length=64

/ppp profile
set [find name="PERFIL-FIBRA-PADRAO"] dhcpv6-pd-pool=POOL-ASSINANTES-PD remote-ipv6-prefix-pool=POOL-ASSINANTES-WAN
```
"""


def seed_database() -> None:
    """Popula o banco de dados com usuários, categorias, tags e artigos do design Stitch caso esteja vazio."""
    if User.query.first() is not None:
        return

    # 1. Usuários / Autores
    francisco = User(
        username="francisco",
        email="francisco@goose.tec.br",
        display_name="Francisco",
        role_title="CEO & CTO • Lead Telecom Ops",
        avatar_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCv2wN6Zl7YGCG44IolCNUScJ9kzQwH4ou8YYmvT8DbT5KBbGi4LOXzsVjFMcQlDhliLO5SJiH9HqmzRmaYWeO1N6vZIdkqSfDkOCKJ5e20cYUraU22Ysk-jfB2adM45hzWGs6bKago7yoNPH5QLO2knCSq0J932Ak_DeOpKkt6eEzSX62lbP83ezejW3QorHKjLQJhiksTfZ6OgmY4h4aixpFvsx3RUyFSJFR4hkk",
        bio="Especialista em arquitetura de redes autônomas (BGP), engenharia de tráfego IP e operação de provedores de alta disponibilidade.",
    )
    francisco.set_password("goose2026")

    wandeson = User(
        username="wandeson",
        email="wandeson@goose.tec.br",
        display_name="Wandeson",
        role_title="CX & Operações • Telecom Experience Lead",
        avatar_url="https://lh3.googleusercontent.com/aida-public/AB6AXuB4DNJwAxi9EJ6hISdJbD5hiZH7dNR6ZHV1e7lXiDuLfiS-IWIrvYi5ZXEHPRjWtcm5ykWuUsp-Fn7k0XTUN8ICnYe1KBfRywiLRR-V7VzOwPBdbyk29HAlmgiAbK9t1x3Hc-LDvn-8iTWwl1_jl5Fo4xdA-R0CVyUp2WjmI1TGBB0iKWu7N3ewQyPm7dW4DF-rvs83tclP362-qxkT56zWSUA2_xi7V0DpINMwalY",
        bio="Especialista em experiência do assinante, automação inteligente de suporte N1/N2 com telemetria TR-069 e retenção para ISPs.",
    )
    wandeson.set_password("goose2026")

    db.session.add_all([francisco, wandeson])
    db.session.flush()

    # 2. Categorias
    cat_eng = Category(slug="engenharia-pop", name="Engenharia & POP", color_theme="petroleum")
    cat_gestao = Category(slug="gestao-isp", name="Gestão de ISP", color_theme="petroleum")
    cat_comercial = Category(slug="comercial-atendimento", name="Comercial & Atendimento", color_theme="carmine")
    cat_goocast = Category(slug="goocast", name="GOOCAST", color_theme="carmine")

    db.session.add_all([cat_eng, cat_gestao, cat_comercial, cat_goocast])
    db.session.flush()

    # 3. Tags
    tag_names = [
        "BGP",
        "MikroTik",
        "WhatsApp",
        "Wi-Fi",
        "MESH",
        "TR-069",
        "RADIUS",
        "GestãoISP",
        "OperadorasNeutras",
        "Atendimento",
        "Pix",
        "TrânsitoIP",
        "AltaDisponibilidade",
        "Peering",
        "RFC1997",
        "GOOCAST",
        "IPv6",
        "CGNAT",
    ]
    tags_map = {}
    for tname in tag_names:
        slug = tname.lower().replace(" ", "-")
        tag_obj = Tag(name=tname, slug=slug)
        db.session.add(tag_obj)
        tags_map[tname] = tag_obj
    db.session.flush()

    default_checklist = [
        {
            "text": "1. Validar Looking Glass externo (Hurricane Electric bgp.he.net) para verificar visibilidade do prefixo /22.",
            "checked": True,
        },
        {
            "text": "2. Confirmar que nenhuma rota da tabela global está sendo redistribuída de volta para a operadora vizinha.",
            "checked": True,
        },
        {
            "text": "3. Simular corte de fibra na porta SFP28 do Trânsito A e mensurar tempo de comutação no gráfico de tráfego.",
            "checked": True,
        },
        {
            "text": "4. Validar registro RPKI válido (ROA cadastrado no Registro.br com Max Length correto).",
            "checked": False,
        },
    ]

    default_telemetry = {
        "routeros_version": "v7.15.2",
        "ipv4_table": "942.310 prefixes",
        "bfd_convergence": "148 ms",
    }

    # 4. Artigos Principais (fiéis ao Stitch)
    # Artigo Hero Principal (Home + CMS Row 1)
    art_hero = Article(
        title="O Fim do Robô Burro no Provedor: Como usamos IA no WhatsApp sem perder a essência humana.",
        subtitle="O assinante não odeia tecnologia; ele odeia a frieza de um menu numérico circular enquanto sua casa está sem conexão. Ao cruzar modelos generativos com telemetria direta de RADIUS e diagnósticos via TR-069, transformamos chamados tensos em respostas resolutivas em 4.8 segundos.",
        slug="fim-do-robo-burro-provedor-ia-whatsapp",
        summary="Ao cruzar modelos generativos com telemetria direta de RADIUS e diagnósticos via TR-069, transformamos chamados tensos em respostas resolutivas em 4.8 segundos e elevamos a retenção em +42%.",
        content_markdown=ROBO_BURRO_CONTENT,
        status="published",
        category_id=cat_comercial.id,
        author_id=francisco.id,
        author_key="duo",
        author_display="Francisco & Wandeson",
        author_footer_label="Francisco & Wandeson • Founders",
        author_role_badge="Goose Founders",
        cover_image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuB8IkUcSrLxG_JbukHHX5reRgGS9jjHj4R5VAwwMcghudnJ_we_XxWhskKLupVEvciz5IvhCjDVStbTeqeyYlXmp7tBET7eSRDsviqLxmrXjP6kZ2x_EGB6EeJCVcz8qyYsiZu2B6PJ5T66W76gJHblc_uOqUgrXz993jIrLdOnsk8rAYdPuqitg2cyVAYAvZRSvoLH3yuPc-GaQDy9QhW8YiOnRJp-JBhz7EOOESU",
        cover_caption="Francisco e Wandeson - NOC Goose Tecnologia",
        meta_description="Descubra como integrar IA generativa ao WhatsApp do seu ISP sem desumanizar o suporte. Integração com TR-069, RADIUS e redução drástica de chamados N1.",
        reading_time_minutes=7,
        views_count=24100,
        is_hero=True,
        is_featured_double=False,
        enable_zen_mode=True,
        enable_goocast=True,
        goocast_episode_label="GOOCAST #28",
        goocast_title="IA Generativa + Telemetria TR-069 e RADIUS no WhatsApp do Provedor",
        goocast_duration="24:18",
        telemetry_box_json=default_telemetry,
        checklist_json=default_checklist,
        published_at=datetime(2026, 3, 28, 14, 0, tzinfo=timezone.utc),
        tags=[tags_map["WhatsApp"], tags_map["TR-069"], tags_map["RADIUS"]],
    )

    # Artigo BGP Multihomed (Tela 2 - Artigo Completo + Editor Markdown)
    art_bgp = Article(
        title="Arquitetura BGP Multihomed com Comunidades de Trânsito IP para Provedores de Alta Disponibilidade",
        subtitle="Como orquestrar engenharia de tráfego, mitigar assimetria severa e padronizar comunidades RFC 1997 com múltiplas operadoras Tier-1 mantendo redundância instantânea e convergência sub-segundo via BFD.",
        slug="arquitetura-bgp-multihomed-transito-ip",
        summary="Análise prática de tráfego de streaming, balanceamento com comunidades BGP RFC 1997 e como o tráfego IX.br e detecção BFD (<180ms) protegem a margem e a disponibilidade do provedor.",
        content_markdown=BGP_ARTICLE_CONTENT,
        status="published",
        category_id=cat_eng.id,
        author_id=francisco.id,
        author_key="francisco",
        author_display="Francisco (CTO)",
        author_footer_label="Francisco • CTO",
        author_role_badge="Goose Founders",
        cover_image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCsyDi9qum4Wx5HxlfQzSlxYFD5jGfyizGrM_rIF8bSh4dFkOABuQYCF3_bRoBF9PTLvrgajgmLTRdpBGcA9u-SbAAfXrq3RIDaIJprmeuk08t0j_yxgH8BrKf5MqvIqZ9hy6J3sClAh0Px8arp0IEOVfxTRTII6KKD8CNRRQ7u7kWjhBuLL_b017i40s2hbuOb-FBTUDWO73r3qrX0mdQgmfiV75kTC4-8fS-M_kc",
        cover_caption="Topologia de Borda AS263481 • PoP SP-01",
        code_card_preview='/routing bgp connection\nadd name="Transit-SP" local.role=ebgp ...',
        meta_description="Guia técnico para engenheiros de rede e ISPs: como estruturar BGP Multihomed com comunidades de trânsito IP, RouterOS v7 e mitigação de rotas assimétricas.",
        reading_time_minutes=9,
        views_count=16100,
        is_hero=False,
        is_featured_double=False,
        enable_zen_mode=True,
        enable_goocast=True,
        goocast_episode_label="GOOCAST #28",
        goocast_title="Engenharia BGP: Prepend vs Local-Pref em Backbone ISP",
        goocast_duration="24:12",
        telemetry_box_json=default_telemetry,
        checklist_json=default_checklist,
        published_at=datetime(2026, 3, 22, 10, 30, tzinfo=timezone.utc),
        tags=[
            tags_map["BGP"],
            tags_map["MikroTik"],
            tags_map["TrânsitoIP"],
            tags_map["AltaDisponibilidade"],
            tags_map["RFC1997"],
        ],
    )

    # Artigo 1 da Grade Home: Gestão de ISP 2026
    art_gestao = Article(
        title="Ainda vale a pena abrir Provedor de Internet em 2026? A verdade nua e crua",
        subtitle="Consolidação de operadoras neutras, saturação de postes e guerra de preços. Francisco e Wandeson desmistificam a rentabilidade líquida real no mercado de ISPs.",
        slug="vale-a-pena-provedor-2026",
        summary="Consolidação de operadoras neutras, saturação de postes e guerra de preços. Francisco e Wandeson desmistificam a rentabilidade líquida real.",
        content_markdown=GESTAO_2026_CONTENT,
        status="published",
        category_id=cat_gestao.id,
        author_id=francisco.id,
        author_key="francisco",
        author_display="Francisco (CEO)",
        author_footer_label="Francisco • CEO",
        author_role_badge="Goose Founders",
        cover_image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuC_W-VolZ9Ndl6CicvM5aFdnowiMZ_SHVjdTK-RuNRrbRy5V_V2FhV_YeePR19c_-iw1eAOuuI8YeCiia1XukkQm6aQZPpWCY-BBT2pLV4PCUMQyvPo1NHPo34biFG_5MhByJFfntG0jCteNs24dGApzkYe-TZy3RwXQuf2NZkCy1_m19QJO1r2k2kvVzRx3vBEaMX2oOOPrdufNro27pc8N11XeGbxnTWuo45NNKk",
        cover_caption="Planejamento Financeiro & Expansão FTTH",
        meta_description="Análise de rentabilidade líquida, payback por porta CTO, operadoras neutras e desafios para provedores de internet em 2026.",
        reading_time_minutes=11,
        views_count=19420,
        is_hero=False,
        is_featured_double=False,
        enable_zen_mode=True,
        enable_goocast=False,
        telemetry_box_json=default_telemetry,
        checklist_json=default_checklist,
        published_at=datetime(2026, 3, 20, 9, 0, tzinfo=timezone.utc),
        tags=[tags_map["GestãoISP"], tags_map["OperadorasNeutras"]],
    )

    # Artigo 2 da Grade Home: Atendimento WhatsApp
    art_whatsapp = Article(
        title="Atendimento no WhatsApp: onde o bot ajuda na 2ª via e onde ele destrói a base",
        subtitle="Automatizar Pix é simples. O erro fatal é submeter assinantes com instabilidade física ao funil de faturamento sem diagnóstico óptico prévio.",
        slug="atendimento-whatsapp-bot-provedor",
        summary="Automatizar Pix é simples. O erro fatal é submeter assinantes com instabilidade física ao funil de faturamento.",
        content_markdown=WHATSAPP_BOT_CONTENT,
        status="published",
        category_id=cat_comercial.id,
        author_id=wandeson.id,
        author_key="wandeson",
        author_display="Wandeson (CX)",
        author_footer_label="Wandeson • CX",
        author_role_badge="CX & Telecom Lead",
        cover_image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCcnfDgQx6G9GYUpy7ZV5M9KL1Ur7YsUtu98Om8C2I8QWbem6km_YMwcRmdudfEx0K_x2vR0ADpcYPqwQTZ6HxxOWMtqjMXtWm1JHnUJEETmwWaYsyyldOfC2MgexqufNtPvCllhZicdjAi-JkjxSpRPBi9ADInO47sEOpAApBRX7wdaoBLF8MmjsM4BHrf01Xf0bNETfV6eyMN77tp-10LwgGVrHRfEDAaS8DJZyA",
        cover_caption="Central de Experiência do Assinante (CX) Goose",
        meta_description="Onde os bots tradicionais falham no suporte técnico de provedores e como separar o fluxo financeiro de Pix do diagnóstico de rede.",
        reading_time_minutes=6,
        views_count=28350,
        is_hero=False,
        is_featured_double=False,
        enable_zen_mode=True,
        enable_goocast=False,
        telemetry_box_json=default_telemetry,
        checklist_json=default_checklist,
        published_at=datetime(2026, 3, 24, 15, 0, tzinfo=timezone.utc),
        tags=[tags_map["WhatsApp"], tags_map["Atendimento"], tags_map["Pix"]],
    )

    # Artigo 4 da Grade Home: Wi-Fi MESH
    art_mesh = Article(
        title="Wi-Fi MESH na prática: acabando com chamados de lentidão doméstica",
        subtitle="Protocolos 802.11k/v/r aplicados à realidade dos clientes residenciais e como monetizar roteadores gerenciados via TR-069 sem aumentar o churn.",
        slug="wifi-mesh-na-pratica-suporte-isp",
        summary="Mais de 70% dos chamados de lentidão são interferência em 2.4GHz na residência. Análise de modelos de locação rentáveis.",
        content_markdown=WIFI_MESH_CONTENT,
        status="published",
        category_id=cat_eng.id,
        author_id=wandeson.id,
        author_key="wandeson",
        author_display="Wandeson (Suporte)",
        author_footer_label="Wandeson • Suporte",
        author_role_badge="CX & Telecom Lead",
        cover_image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuBnhojYJUXeR6m5kaqILURbK9Lh1duyqPBacWpCtOhOQrADsnvshUifFt3qVdVj6ech5T77xGeqixV5gRD6Bby2amcGP0kMSiYvo9y4WTbFW7WCmtqXRbDC6R0PW8-mpVkgBhT9MJNNGDfdF5rZCwJCiQ44TF5gJs7VdGbzhfPwPzMuhwIeY5xtRupS_pt9a1fSNQTNQzDEwgHDz9aJDKyZ6danixFA6rxfxMzySWs",
        cover_caption="Topologia Wi-Fi 6 Mesh Gerenciada via ACS",
        meta_description="Como resolver chamados recorrentes de lentidão no Wi-Fi residencial com redes MESH 802.11k/v/r e gerência remota TR-069.",
        reading_time_minutes=8,
        views_count=11200,
        is_hero=False,
        is_featured_double=False,
        enable_zen_mode=True,
        enable_goocast=False,
        telemetry_box_json=default_telemetry,
        checklist_json=default_checklist,
        published_at=datetime(2026, 3, 15, 11, 0, tzinfo=timezone.utc),
        tags=[tags_map["Wi-Fi"], tags_map["MESH"], tags_map["TR-069"]],
    )

    # Artigo 5 da Grade Home: GOOCAST #2 (Tony Sanderson) - Destaque Duplo
    art_goocast = Article(
        title="Estratégias Comerciais para Provedores Regionais com Tony Sanderson",
        subtitle="Como organizar equipes comerciais PAP (porta a porta) com metas orientadas à viabilidade óptica por CTO sem desperdício de investimento publicitário.",
        slug="estrategias-comerciais-provedores-tony-sanderson",
        summary="Como organizar equipes comerciais PAP (porta a porta) com metas orientadas à viabilidade óptica por CTO sem desperdício de investimento publicitário.",
        content_markdown=TONY_SANDERSON_CONTENT,
        status="published",
        category_id=cat_goocast.id,
        author_id=francisco.id,
        author_key="guest",
        author_display="Tony Sanderson (Convidado)",
        author_footer_label="Participação Especial",
        author_role_badge="GOOCAST #2",
        cover_image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuCSdkxez3PJesqVMw1iSWXEMPHVN1aadheECGKaMsKFc8wrgh-4gOA7ITy58LgBNOqZuIvn5FaqysYuRCeYoTB6YSVxlPwyu-7EtdkgrhnBt9CM68i14tS4HSqJ5vdnhQ7R1f38BFgmpzZgGvPkXwovYy50hgmdFPS5gxaG9Ek_ROTYhHZcNw9RQLKDkIZgviKaFWzvQuysfBos1xdJAYcM97Jxfk_uX2Mw106xGFU",
        cover_caption="Tony Sanderson no estúdio GOOCAST",
        meta_description="Episódio completo do GOOCAST #2 com Tony Sanderson sobre vendas PAP orientadas à ocupação de CTOs para provedores de internet.",
        reading_time_minutes=12,
        views_count=34900,
        is_hero=False,
        is_featured_double=True,
        enable_zen_mode=True,
        enable_goocast=True,
        goocast_episode_label="GOOCAST #2",
        goocast_title="Estratégias Comerciais PAP e Ocupação de CTOs com Tony Sanderson",
        goocast_duration="1h 14m",
        telemetry_box_json=default_telemetry,
        checklist_json=default_checklist,
        published_at=datetime(2026, 3, 26, 18, 0, tzinfo=timezone.utc),
        tags=[tags_map["GOOCAST"], tags_map["GestãoISP"]],
    )

    # Artigo Rascunho (Row 6 do CMS)
    art_draft = Article(
        title="Migração IPv6 nativa em CGNAT: Guia definitivo para NOC de Provedor",
        subtitle="Como implementar Dual-Stack com Prefix Delegation /56 via RADIUS e reduzir em 65% o consumo de sessões nas caixas de CGNAT IPv4.",
        slug="migracao-ipv6-cgnat-guia-noc",
        summary="Guia prático de implementação IPv6 /56 em assinantes PPPoE com RouterOS v7 e alívio imediato de portas CGNAT.",
        content_markdown=IPV6_DRAFT_CONTENT,
        status="draft",
        category_id=cat_eng.id,
        author_id=francisco.id,
        author_key="francisco",
        author_display="Francisco (CTO)",
        author_footer_label="Francisco • CTO",
        author_role_badge="Goose Founders",
        cover_image_url="https://lh3.googleusercontent.com/aida-public/AB6AXuBpEsndlmZZ4epYID3u9dOrEl9IKN4mBZyhoJiOj78Q-CdLEusGY6l_edLMBqBgVgBFd7_OHT7dfY4pZIWMGR5AmCYokT_VL8bPolPQNvlhoaQmyFvBOmkrvHRZHhdnEtH0goB1OFyTdeytelV49UJxWshSqg7VaASNuvu8KOe_WSETe1qYu5sMBbvBJimOdHbj4K6Q7Kq1bRujwaOUNF_LR4dZ4wUEwJDWodhvYGw",
        cover_caption="Arquitetura Dual-Stack IPv6 /56 + CGNAT Determinístico",
        meta_description="Guia definitivo para NOC de Provedor: migração IPv6 nativa em CGNAT com Prefix Delegation /56 no MikroTik RouterOS v7.",
        reading_time_minutes=14,
        views_count=0,
        is_hero=False,
        is_featured_double=False,
        enable_zen_mode=True,
        enable_goocast=False,
        telemetry_box_json=default_telemetry,
        checklist_json=default_checklist,
        published_at=datetime(2026, 3, 29, 10, 0, tzinfo=timezone.utc),
        tags=[tags_map["IPv6"], tags_map["CGNAT"], tags_map["MikroTik"]],
    )

    db.session.add_all([art_hero, art_bgp, art_gestao, art_whatsapp, art_mesh, art_goocast, art_draft])

    # 5. Mídia inicial e Logs de Auditoria para o CMS
    media_items = [
        MediaAsset(
            filename="goose_logo_horizontal.png",
            file_url="/static/img/goose_logo_horizontal.png",
            alt_text="Logo Oficial Goose Tecnologia Horizontal",
            mime_type="image/png",
        ),
        MediaAsset(
            filename="noc_goose_goocast_28.jpg",
            file_url=art_hero.cover_image_url,
            alt_text="Francisco e Wandeson - NOC Goose Tecnologia",
            mime_type="image/jpeg",
        ),
        MediaAsset(
            filename="topologia_borda_bgp_sp01.jpg",
            file_url=art_bgp.cover_image_url,
            alt_text="Topologia de Borda AS263481 • PoP SP-01",
            mime_type="image/jpeg",
        ),
    ]
    db.session.add_all(media_items)

    logs = [
        AuditLog(
            action="DEPLOY_EDGE_SYNC",
            actor_name="Francisco & Wandeson",
            target_slug="fim-do-robo-burro-provedor-ia-whatsapp",
            details="Artigo fixado no Hero Principal e sincronizado com Edge CDN (0.14ms).",
        ),
        AuditLog(
            action="PUBLISH_ARTICLE",
            actor_name="Francisco (CTO)",
            target_slug="arquitetura-bgp-multihomed-transito-ip",
            details="Validação RouterOS v7 e comunidades RFC 1997 aprovadas (3/3 checks).",
        ),
        AuditLog(
            action="DRAFT_AUTOSAVE",
            actor_name="Francisco (CTO)",
            target_slug="migracao-ipv6-cgnat-guia-noc",
            details="Rascunho técnico IPv6 /56 salvo no buffer editorial.",
        ),
    ]
    db.session.add_all(logs)

    # Lead de exemplo
    sample_lead = Lead(
        name="Roberto Silva",
        isp_asn="FibraNet Telecom (AS263410)",
        whatsapp="(11) 99812-4400",
        source_page="/",
    )
    db.session.add(sample_lead)

    db.session.commit()

