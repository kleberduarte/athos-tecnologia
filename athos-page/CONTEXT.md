# CONTEXT.md — Athos Page
**Cliente:** Athos Tecnologia (Projeto Interno)
**Projeto:** athos-page
**Data:** 2026-08-04
**Fase:** 0 — Análise de Demanda & Decisão de Stack
**Responsável:** Agent Software Architect (Squad Alpha)

---

## 1. PROBLEMA DE NEGÓCIO

A Athos Tecnologia, vertente de engenharia digital do Grupo DOC Partners, necessita de uma presença digital profissional que reflita a profundidade técnica e a seriedade da empresa. A landing page é o principal ponto de contato com potenciais clientes e parceiros, devendo transmitir autoridade técnica, gerar leads qualificados e apresentar o portfólio de serviços (desenvolvimento de software + locação de hardware via YEP Solutions).

**Usuário Final:**
- Gestores de TI e CTO's de médias e grandes empresas
- Diretores de operações interessados em automação industrial
- Empresas do setor de Varejo, Saúde e Logística/Manufatura

**Dor Principal:** Ausência de um canal digital que converta visitantes em leads qualificados e transmita credibilidade técnica ao nível das entregas da empresa.

---

## 2. ESTADO ATUAL DO PROJETO

A landing page já existe em produção. Localização do código-fonte:
```
C:\athos\projetos\athos-tecnologia\
├── index.html       # Página principal (523 linhas)
├── styles.css       # Estilos customizados
├── main.js          # Lógica de interação (canvas grid, animações, scroll)
├── logo-athos.png   # Logotipo
└── favicon.svg      # Favicon
```

**Seções implementadas:**
1. **Header** — navegação responsiva com menu hambúrguer mobile
2. **Hero** — canvas animado (grid), headline principal, CTAs
3. **Serviços** — 4 cards (Arquitetura, Dados, Produtos Digitais, Segurança)
4. **Automação & Auto-Atendimento** — 6 cards YEP Solutions + banner de locação
5. **Segmentos** — Varejo, Saúde, Logística & Manufatura
6. **Sobre** — métricas da empresa (+50 projetos, +8 anos, 99% uptime, 24/7)
7. **Diferenciais** — 4 cards de proposta de valor
8. **Contato** — CTA com e-mail direto
9. **Footer** — referência ao Grupo DOC Partners

---

## 3. ANÁLISE DA DEMANDA TÉCNICA

**Classificação:** Landing page corporativa / Geração de leads / Branding técnico

**Requisitos funcionais identificados:**
- Apresentação institucional da empresa
- Showcase de serviços de software (Squad-based development)
- Showcase de hardware em locação (parceria YEP Solutions)
- Formulário de contato / captura de lead
- Navegação fluida com âncoras
- Design responsivo (mobile-first)
- Animações de entrada no scroll (reveal)

**Requisitos não-funcionais:**
- Performance: LCP < 2,5s | FID < 100ms | CLS < 0,1 (Core Web Vitals)
- SEO: meta tags, estrutura semântica H1/H2/H3, Open Graph
- Acessibilidade: WCAG 2.1 AA (aria-labels, contraste, navegação por teclado)
- Disponibilidade: 99,9% (hosting estático)

**Gaps identificados no estado atual:**
- Ausência de formulário de contato funcional (apenas mailto:)
- Ausência de tracking / analytics (Google Analytics, Hotjar ou similar)
- Sem Open Graph / Twitter Cards para compartilhamento social
- Sem sitemap.xml e robots.txt para SEO
- JavaScript sem bundler/minificação (performance em produção)
- Sem testes automatizados de UI/acessibilidade
- Sem CI/CD configurado
- Dependência de CDN externo (Bootstrap, Google Fonts) — risco de SPOF

---

## 4. JUSTIFICATIVA DA STACK

### 4.1 Stack Atual (Fase de Manutenção Imediata)

| Camada | Tecnologia | Status |
|--------|-----------|--------|
| Markup | HTML5 semântico | Implementado |
| Estilos | CSS3 custom + Bootstrap 5.3 | Implementado |
| Interatividade | JavaScript vanilla (ES6+) | Implementado |
| Fontes | Google Fonts (Orbitron, JetBrains Mono, Share Tech Mono) | Implementado |
| Hospedagem | A definir (GitHub Pages / Vercel / Netlify) | Pendente |

**Justificativa de manter HTML/CSS/JS para o estado atual:**
A nature da demanda é uma landing page de marketing com conteúdo estático. Não há necessidade de SSR, autenticação, banco de dados ou rotas dinâmicas no escopo imediato. A stack atual é adequada, tem zero custo de hosting (GitHub Pages / Netlify Free), carrega rapidamente e é mantida por qualquer desenvolvedor.

### 4.2 Stack Alvo (Fase de Evolução — Sprint 2+)

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Framework | Next.js 15 + TypeScript | SEO superior (SSG/ISR), App Router, integração com Vercel Analytics, DX moderna |
| Estilos | Tailwind CSS 4 | Consistência com projetos ATHOS, purgação automática, DX superior ao Bootstrap custom |
| Formulário | React Hook Form + Zod | Validação tipada, UX de formulário superior |
| Backend (formulário) | Next.js API Route / Vercel Serverless | Envio de e-mail sem servidor dedicado |
| E-mail | Resend (API) | Developer-first, templates React Email, free tier generoso |
| Analytics | Vercel Analytics + Speed Insights | Zero-config, privacy-first, Core Web Vitals nativos |
| Hosting | Vercel | CI/CD automático por git, preview deployments, integração nativa Next.js |
| Testes UI | Playwright | E2E, testes de acessibilidade, visual regression |

**Justificativa da evolução para Next.js:**
1. **SEO estrutural:** SSG garante HTML pré-renderizado; o Bootstrap atual depende de JS para animações que podem atrasar o LCP.
2. **Analytics nativo:** Vercel Analytics é zero-config e não requer consent banner (privacy-first).
3. **Formulário funcional:** A única dependência externa atual é o mailto: — Next.js API Route + Resend elimina esse gap sem infraestrutura adicional.
4. **Consistência interna:** Todos os projetos de frontend da ATHOS já usam Next.js + Tailwind. Migrar reduz fragmentação de stack.
5. **Deploy automatizado:** Vercel oferece preview URL por PR, deploy automático na main, e rollback em 1 clique.

### 4.3 Decisão Final

- **Sprint 0–1:** Padronizar e corrigir gaps na versão HTML atual (SEO, acessibilidade, analytics, formulário via Formspree/Netlify Forms)
- **Sprint 2–3:** Migração para Next.js 15 + Tailwind CSS 4 + Vercel (preservando 100% do design)
- **Sprint 4:** Formulário próprio (React + API Route + Resend) + testes Playwright + CI/CD

---

## 5. ARQUITETURA — CLEAN ARCHITECTURE (ADAPTADA PARA LANDING PAGE)

Por ser um projeto frontend-only sem backend complexo, a Clean Architecture é aplicada na camada de componentes:

```
src/
├── app/                    # App Router Next.js (páginas e layouts)
│   ├── page.tsx            # Página principal (/ rota)
│   ├── layout.tsx          # Root layout (metadados, fontes, analytics)
│   └── api/
│       └── contato/
│           └── route.ts    # POST — recebe formulário, envia via Resend
├── components/
│   ├── sections/           # Componentes de seção (Hero, Servicos, Sobre...)
│   ├── ui/                 # Componentes atômicos (Button, Card, Badge...)
│   └── layout/             # Header, Footer, Nav
├── lib/
│   ├── resend.ts           # Cliente Resend (infrastructure layer)
│   └── validations.ts      # Schemas Zod (domain rules)
└── styles/
    └── globals.css         # Tailwind + custom CSS
```

**Regra de dependência:**
- `components/sections` depende de `components/ui` (nunca o contrário)
- `app/api` depende de `lib/` para validação e envio de e-mail
- `lib/validations.ts` não depende de nenhuma biblioteca de UI

---

## 6. RESTRIÇÕES E RISCOS

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| CDN Bootstrap offline afeta layout | Baixa | Migração para Tailwind elimina dependência |
| Google Fonts bloqueado (LGPD/firewall) | Média | Auto-hospedar fontes no Sprint 1 |
| Mailto: não funciona em todos os clientes | Alta | Formulário funcional no Sprint 1 |
| Ausência de analytics impede otimização | Alta | Implementar no Sprint 1 |

---

## 7. DEFINIÇÃO DE PRONTO (DoD)

Um sprint está concluído quando:
- [ ] Código commitado e revisado na branch `main`
- [ ] Deploy automático em produção via Vercel/Netlify
- [ ] Core Web Vitals: LCP < 2,5s, CLS < 0,1
- [ ] Lighthouse Score ≥ 90 em Performance, Acessibilidade e SEO
- [ ] Formulário de contato funcional (e-mail entregue)
- [ ] Sem erros no console do browser
