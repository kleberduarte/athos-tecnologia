# SPEC.md — Athos Page
**Projeto:** athos-page | **Cliente:** Athos Tecnologia (Interno)
**Versão:** 1.0 | **Data:** 2026-08-04
**Responsável:** Agent Product Manager (Squad Alpha)
**Metodologia:** BDD — Dado / Quando / Então

---

## Visão Geral

Landing page institucional da Athos Tecnologia com objetivo de:
1. Apresentar a empresa e posicionamento de mercado
2. Demonstrar portfólio de serviços (software + hardware/YEP)
3. Capturar leads qualificados via formulário de contato
4. Converter visitantes em primeiras reuniões comerciais

**KPIs de Sucesso:**
- Taxa de cliques no CTA "Fale conosco" ≥ 5% dos visitantes
- Formulário submetido com sucesso ≥ 2% dos visitantes
- Bounce rate < 55%
- Tempo médio na página > 90 segundos
- Lighthouse Score ≥ 90 (Performance, Acessibilidade, SEO)

---

## Módulo 1 — Navegação & Header

### Caso de Uso 1.1 — Menu Desktop
**Dado** que o usuário acessa a página em viewport ≥ 992px
**Quando** a página carrega
**Então** o header deve exibir: logo ATHOS à esquerda + links de âncora (Serviços, Automação, Sobre, Diferenciais, Contato) + CTA "Fale conosco" à direita

### Caso de Uso 1.2 — Menu Mobile (Hambúrguer)
**Dado** que o usuário acessa a página em viewport < 992px
**Quando** a página carrega
**Então** os links de navegação ficam ocultos e o botão hambúrguer é exibido
**E quando** o usuário clica no botão hambúrguer
**Então** o menu abre com todos os links + CTA em modo vertical

### Caso de Uso 1.3 — Navegação por Âncora
**Dado** que o menu está visível (mobile ou desktop)
**Quando** o usuário clica em qualquer link de âncora (ex: "Serviços")
**Então** a página rola suavemente (smooth scroll) até a seção correspondente
**E** o menu mobile fecha automaticamente (se aberto)

### Caso de Uso 1.4 — Header Sticky com Blur
**Dado** que o usuário rola a página para baixo além de 80px
**Quando** o scroll ultrapassa esse threshold
**Então** o header ganha backdrop-blur e reduz levemente a altura (efeito de contração)
**E** permanece visível em todas as seções

### Caso de Borda 1.5 — Foco por Teclado
**Dado** que o usuário navega via teclado (Tab)
**Quando** foca em um item do menu
**Então** o item exibe outline de foco visível (WCAG 2.1 SC 2.4.7)

---

## Módulo 2 — Hero

### Caso de Uso 2.1 — Canvas Animado
**Dado** que o usuário acessa a página
**Quando** o Hero renderiza
**Então** um canvas com grid animado (linhas brancas de baixa opacidade) é exibido como fundo
**E** a animação é suave (requestAnimationFrame), sem causar jank (CLS = 0)

### Caso de Uso 2.2 — Conteúdo Principal
**Dado** que o Hero está visível
**Quando** a página carrega
**Então** exibe: eyebrow "Arquitetura · Dados · Produtos Digitais" + H1 "Engenharia para demandas exigentes" + lead text + dois CTAs ("Nossos serviços" e "Entre em contato")

### Caso de Uso 2.3 — CTAs do Hero
**Dado** que o usuário vê o Hero
**Quando** clica em "Nossos serviços"
**Então** rola suavemente até a seção #servicos
**Quando** clica em "Entre em contato"
**Então** rola suavemente até a seção #contato

### Caso de Borda 2.4 — Desempenho do Canvas
**Dado** que o dispositivo é low-end (mobile)
**Quando** o canvas é iniciado
**Então** o sistema deve reduzir a densidade do grid ou pausar a animação se `prefers-reduced-motion: reduce` estiver ativo

---

## Módulo 3 — Serviços

### Caso de Uso 3.1 — Grid de Cards
**Dado** que o usuário rola até a seção #servicos
**Quando** os cards entram na viewport
**Então** exibem animação de reveal (fade-in + translateY)
**E** os 4 cards são apresentados: Arquitetura de Software, Engenharia de Dados, Produtos Digitais, Segurança & Compliance

### Caso de Uso 3.2 — Hover nos Cards
**Dado** que o usuário está em desktop
**Quando** passa o cursor sobre um card
**Então** o card eleva levemente (transform: translateY(-4px)) com transição suave
**E** o ícone SVG ganha brilho (opacidade aumenta)

### Caso de Borda 3.3 — Touch em Mobile
**Dado** que o usuário está em mobile (sem hover)
**Quando** toca em um card
**Então** nenhum estado de hover permanente é aplicado (sem sticky hover)

---

## Módulo 4 — Automação & Auto-Atendimento (YEP Solutions)

### Caso de Uso 4.1 — Badge de Parceria
**Dado** que a seção #automacao está visível
**Quando** renderiza
**Então** o badge "Parceiro Credenciado YEP Solutions" é exibido em destaque no topo da seção

### Caso de Uso 4.2 — Grid de Produtos YEP
**Dado** que o usuário rola até #automacao
**Quando** os cards entram na viewport
**Então** 6 cards de produtos são exibidos com animação de reveal:
  1. Totens de Auto-Atendimento
  2. Coletores de Dados (Zebra, Bluebird, Unitech)
  3. Impressoras Térmicas (Zebra ZT410/ZT411, TSC MB241)
  4. RFID & Rastreabilidade
  5. Tablets & PDV Dupla Tela
  6. Câmeras Inteligentes (Dahua)

### Caso de Uso 4.3 — Banner de Locação
**Dado** que os cards de produto estão visíveis
**Quando** o usuário vê o banner abaixo
**Então** exibe: 4 métricas (33% IR, 100% SLA, +5k cidades, R$ 0 manutenção) + CTA "Solicitar proposta de locação" + link "Conhecer portfólio YEP"

### Caso de Uso 4.4 — CTA de Locação
**Dado** que o usuário clica em "Solicitar proposta de locação"
**Quando** o clique ocorre
**Então** rola até #contato
**Dado** que o usuário clica em "Conhecer portfólio YEP"
**Quando** o clique ocorre
**Então** abre o site YEP Solutions em nova aba (target="_blank", rel="noopener noreferrer")

---

## Módulo 5 — Segmentos

### Caso de Uso 5.1 — Cards de Segmentos
**Dado** que o usuário acessa #segmentos
**Quando** os cards entram na viewport
**Então** exibe 3 segmentos com ícone, título, descrição e tags:
  - Varejo (Auto-atendimento, PDV, Estoque, Etiquetagem)
  - Saúde (RFID hospitalar, Triagem, Rastreabilidade, Compliance)
  - Logística & Manufatura (WMS, Expedição, Chão de fábrica, Inventário)

---

## Módulo 6 — Sobre

### Caso de Uso 6.1 — Métricas Animadas (Counter)
**Dado** que o usuário rola até #sobre
**Quando** a seção entra na viewport
**Então** os contadores animam de 0 até o valor final:
  - +50 Projetos entregues
  - +8 Anos de experiência
  - 99% Uptime garantido
  - 24/7 Suporte dedicado

### Caso de Uso 6.2 — Texto Institucional
**Dado** que #sobre está visível
**Quando** renderiza
**Então** exibe o texto de apresentação da empresa (vertente do Grupo DOC Partners) + CTA "Fale com um especialista"

---

## Módulo 7 — Diferenciais

### Caso de Uso 7.1 — Cards de Diferencial
**Dado** que o usuário acessa #diferenciais
**Quando** os cards entram na viewport
**Então** 4 cards são exibidos com linha decorativa + título + descrição:
  1. Profundidade técnica
  2. Governança integrada
  3. Foco em resultado
  4. Cobertura nacional via YEP (destacado como card parceiro)

---

## Módulo 8 — Formulário de Contato

### Caso de Uso 8.1 — Exibição do Formulário
**Dado** que o usuário chega ao #contato
**Quando** a seção está visível
**Então** exibe: headline "Pronto para o próximo nível?" + formulário com campos:
  - Nome completo (obrigatório)
  - E-mail corporativo (obrigatório, validado)
  - Empresa (obrigatório)
  - Segmento (select: Varejo / Saúde / Logística / TI / Outro)
  - Mensagem (textarea, obrigatório, mín. 20 chars)
  - Botão "Enviar mensagem"

### Caso de Uso 8.2 — Validação Client-Side
**Dado** que o usuário preenche o formulário
**Quando** tenta submeter com campos inválidos
**Então** mensagens de erro específicas aparecem abaixo de cada campo inválido
**E** o foco move para o primeiro campo com erro

### Caso de Uso 8.3 — Submissão com Sucesso
**Dado** que todos os campos são válidos
**Quando** o usuário clica em "Enviar mensagem"
**Então** o botão exibe estado de loading (spinner)
**E** a API Route `/api/contato` processa a solicitação
**E** um e-mail é enviado para `contato@athostecnologia.com.br` via Resend
**E** o formulário é substituído pela mensagem: "Mensagem enviada! Retornaremos em até 24h úteis."

### Caso de Uso 8.4 — Submissão com Erro
**Dado** que o servidor retorna erro (timeout, falha de envio)
**Quando** a resposta chega
**Então** o botão volta ao estado normal
**E** exibe mensagem de erro: "Ocorreu um problema ao enviar. Por favor, tente novamente ou entre em contato direto pelo e-mail."

### Caso de Borda 8.5 — Proteção Contra Spam
**Dado** que um bot tenta submeter o formulário
**Quando** a requisição chega na API Route
**Então** o campo honeypot invisível (se preenchido) descarta silenciosamente a submissão
**E** rate limiting de 3 submissões/hora por IP é aplicado

---

## Módulo 9 — Performance & SEO

### Caso de Uso 9.1 — Core Web Vitals
**Dado** que a página está em produção
**Quando** medida pelo Google PageSpeed Insights
**Então** LCP < 2,5s | FID/INP < 200ms | CLS < 0,1

### Caso de Uso 9.2 — Open Graph
**Dado** que a URL da página é compartilhada em redes sociais
**Quando** o preview é gerado
**Então** exibe: og:title, og:description, og:image (imagem de preview 1200x630px), og:url, og:type

### Caso de Uso 9.3 — SEO On-Page
**Dado** que bots de busca indexam a página
**Quando** analisam o HTML
**Então** encontram: 1 H1, H2s por seção, meta description < 160 chars, canonical URL, robots.txt, sitemap.xml, dados estruturados JSON-LD (Organization)

---

## Módulo 10 — Acessibilidade

### Caso de Uso 10.1 — Navegação por Teclado
**Dado** que o usuário navega apenas com teclado
**Quando** pressiona Tab
**Então** todos os elementos interativos são atingíveis em ordem lógica com outline visível

### Caso de Uso 10.2 — Screen Reader
**Dado** que o usuário usa leitor de tela (NVDA, VoiceOver)
**Quando** navega pela página
**Então** aria-labels, aria-hidden nos SVGs decorativos, e role="main" estão corretamente definidos

### Caso de Uso 10.3 — Contraste de Cor
**Dado** que a paleta dark (fundo #000, texto #fff) é usada
**Quando** medida pelo WCAG 2.1
**Então** todos os textos têm relação de contraste ≥ 4,5:1 (AA)

---

## Casos de Borda Globais

| Cenário | Comportamento Esperado |
|---------|----------------------|
| JavaScript desabilitado | Página exibe conteúdo estático; formulário mostra link mailto: fallback |
| Sem conexão com Google Fonts | Fontes fallback (monospace, system-ui) mantêm legibilidade |
| Imagem logo-athos.png indisponível | alt text "Athos Tecnologia" é exibido |
| URL inválida compartilhada | Redirect 404 → página principal |
| Viewport < 320px | Layout não quebra; scroll horizontal ausente |
