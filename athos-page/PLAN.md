# PLAN.md — Athos Page
**Projeto:** athos-page | **Cliente:** Athos Tecnologia (Interno)
**Data:** 2026-08-04
**Responsável:** Squad Alpha + Beta + Delta
**Pré-requisito:** Aprovação da `PROPOSAL.md`

---

## Visão Geral do Roadmap

```
Sprint 0: Documentação ATHOS            → CONCLUÍDO (2026-08-04)
Sprint 1: Correções HTML + Deploy       → PENDENTE
Sprint 2: Migração Next.js              → PENDENTE
Sprint 3: Formulário + Testes + CI/CD  → PENDENTE
Sprint 4: Expansão (opcional)           → BACKLOG
```

---

## Sprint 1 — Correções Imediatas & Deploy Automatizado

**Objetivo:** Tornar o site atual production-ready sem mudar o design.
**Duração estimada:** 8 horas | **Squad:** Beta (Frontend) + Delta (DevOps)

### [S1-T01] — Conectar repositório ao Vercel/Netlify
- Criar conta no Vercel ou Netlify
- Conectar o repositório `athos-tecnologia` no GitHub
- Configurar domínio customizado `athostecnologia.com.br`
- Verificar SSL automático
- **Squad:** Delta | **Esforço:** 1h

### [S1-T02] — SEO — Meta Tags completas
- Adicionar `<meta name="description">` (já existe — revisar)
- Adicionar Open Graph: `og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `og:site_name`
- Adicionar Twitter Cards: `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`
- Adicionar canonical URL `<link rel="canonical">`
- **Squad:** Beta | **Esforço:** 1h

### [S1-T03] — SEO — Dados Estruturados JSON-LD
- Implementar schema `Organization` no `<head>`:
  - name, url, logo, contactPoint, sameAs (LinkedIn, etc.)
- Testar via Google Rich Results Test
- **Squad:** Beta | **Esforço:** 1h

### [S1-T04] — SEO — sitemap.xml + robots.txt
- Criar `sitemap.xml` com URL da página principal e data de modificação
- Criar `robots.txt` com `Allow: /` e referência ao sitemap
- **Squad:** Beta | **Esforço:** 30min

### [S1-T05] — Performance — Auto-hospedar Fontes Google
- Baixar Orbitron, JetBrains Mono e Share Tech Mono em WOFF2
- Servir localmente (eliminar request externo ao Google Fonts)
- Adicionar `font-display: swap`
- Remover `<link rel="preconnect">` para fonts.googleapis.com
- **Squad:** Beta | **Esforço:** 1h

### [S1-T06] — Performance — Otimizar imagem logo-athos.png
- Converter `logo-athos.png` para `.webp` com fallback `.png`
- Adicionar `width` e `height` explícitos na tag `<img>`
- Adicionar `loading="lazy"` em imagens abaixo do fold
- **Squad:** Beta | **Esforço:** 30min

### [S1-T07] — Formulário — Integração Formspree
- Criar conta Formspree (formspree.io)
- Substituir `mailto:` por `<form action="https://formspree.io/f/..." method="POST">`
- Campos: nome, e-mail, empresa, segmento (select), mensagem
- Adicionar AJAX submit com feedback de sucesso/erro
- Implementar honeypot field (anti-spam)
- **Squad:** Beta | **Esforço:** 2h

### [S1-T08] — Analytics — Google Analytics 4 ou Umami
- Opção A: Criar propriedade GA4, adicionar script via gtag.js
- Opção B: Self-host Umami (privacy-first, LGPD-friendly)
- Configurar eventos: clique em CTAs, scroll depth, submit de formulário
- **Squad:** Beta + Delta | **Esforço:** 1h

### [S1-T09] — Acessibilidade — Audit WCAG 2.1 AA
- Executar axe DevTools / WAVE na página
- Corrigir issues identificadas: foco visível, aria-labels ausentes, contraste
- Testar navegação por teclado (Tab order, skip links)
- Adicionar `<a href="#main" class="skip-link">Pular para o conteúdo</a>`
- **Squad:** Gamma | **Esforço:** 1h

---

## Sprint 2 — Migração Next.js 15 + Tailwind CSS 4

**Objetivo:** Reescrever a landing em Next.js preservando 100% do design atual.
**Duração estimada:** 24 horas | **Squad:** Beta (Frontend)

### [S2-T01] — Setup do Projeto Next.js
```bash
npx create-next-app@latest athos-page \
  --typescript --tailwind --app --src-dir \
  --import-alias "@/*"
```
- Instalar dependências: `react-hook-form`, `zod`, `resend`, `@vercel/analytics`
- Configurar `next.config.ts` (imagens, headers de segurança)
- Configurar fontes via `next/font/local`
- **Squad:** Beta | **Esforço:** 2h

### [S2-T02] — Estrutura de Componentes
Criar estrutura de pastas conforme `CONTEXT.md`:
```
src/
├── app/
│   ├── page.tsx
│   ├── layout.tsx
│   └── api/contato/route.ts
├── components/
│   ├── layout/Header.tsx
│   ├── layout/Footer.tsx
│   ├── sections/Hero.tsx
│   ├── sections/Servicos.tsx
│   ├── sections/Automacao.tsx
│   ├── sections/Segmentos.tsx
│   ├── sections/Sobre.tsx
│   ├── sections/Diferenciais.tsx
│   ├── sections/Contato.tsx
│   └── ui/Button.tsx, Card.tsx, Badge.tsx
├── lib/
│   ├── resend.ts
│   └── validations.ts
└── styles/globals.css
```
- **Squad:** Beta | **Esforço:** 2h

### [S2-T03] — Componente: Header
- Navbar responsiva (desktop + mobile hambúrguer)
- Smooth scroll para âncoras
- Sticky com backdrop-blur no scroll
- Dark mode como padrão (sem toggle — identidade da marca)
- **Squad:** Beta | **Esforço:** 2h

### [S2-T04] — Componente: Hero (Canvas Animado)
- Migrar lógica do canvas para React com `useEffect` + `useRef`
- Respeitar `prefers-reduced-motion`
- Decoração SVG circular à direita
- CTAs: "Nossos serviços" + "Entre em contato"
- **Squad:** Beta | **Esforço:** 3h

### [S2-T05] — Componente: Serviços
- 4 cards com ícones SVG inline (sem dependência externa)
- Animação de reveal no scroll via Intersection Observer
- Hover state (translateY + shadow)
- **Squad:** Beta | **Esforço:** 2h

### [S2-T06] — Componente: Automação & YEP
- Badge "Parceiro Credenciado YEP Solutions"
- 6 cards de produtos com ícones SVG
- Banner de locação com 4 métricas
- CTAs: "Solicitar proposta" → #contato | "Conhecer YEP" → external
- **Squad:** Beta | **Esforço:** 3h

### [S2-T07] — Componente: Segmentos
- 3 cards com ícone + título + descrição + tags
- Tags como `<ul>` semântica com styled chips
- **Squad:** Beta | **Esforço:** 1h

### [S2-T08] — Componente: Sobre (Counter Animado)
- Intersection Observer para disparar counter animation
- Respeitar `prefers-reduced-motion` (exibir valor final sem animação)
- useCountUp hook customizado
- **Squad:** Beta | **Esforço:** 2h

### [S2-T09] — Componente: Diferenciais
- 4 cards com linha decorativa + título + texto
- Card YEP com estilo diferenciado (accent âmbar)
- **Squad:** Beta | **Esforço:** 1h

### [S2-T10] — Componente: Footer
- Logo + copyright dinâmico (ano atual via `new Date().getFullYear()`)
- Links DOC Partners
- **Squad:** Beta | **Esforço:** 30min

### [S2-T11] — Otimizações Next.js
- `next/image` para logo-athos (com width/height e priority)
- Metadados via `generateMetadata()` no layout.tsx
- Open Graph image (og:image) gerada via `next/og` (ImageResponse)
- Configurar headers de segurança no `next.config.ts` (CSP, X-Frame-Options)
- **Squad:** Beta | **Esforço:** 2h

### [S2-T12] — Deploy do Projeto Next.js no Vercel
- Conectar novo repositório `athos-page` ao Vercel
- Configurar variáveis de ambiente (`RESEND_API_KEY`)
- Verificar preview URL funcionando
- Migrar domínio `athostecnologia.com.br` do Sprint 1
- **Squad:** Delta | **Esforço:** 1h

---

## Sprint 3 — Formulário Próprio + Testes + CI/CD

**Objetivo:** Formulário funcional com backend próprio + pipeline de qualidade automatizado.
**Duração estimada:** 16 horas | **Squad:** Beta + Gamma + Delta

### [S3-T01] — lib/validations.ts — Schema Zod
```typescript
const ContatoSchema = z.object({
  nome: z.string().min(3).max(100),
  email: z.string().email(),
  empresa: z.string().min(2).max(100),
  segmento: z.enum(['varejo', 'saude', 'logistica', 'ti', 'outro']),
  mensagem: z.string().min(20).max(2000),
  honeypot: z.string().max(0), // anti-bot
})
```
- **Squad:** Beta | **Esforço:** 1h

### [S3-T02] — lib/resend.ts — Cliente de E-mail
- Inicializar `new Resend(process.env.RESEND_API_KEY)`
- Função `sendContactEmail(data: ContatoData)` com template HTML
- Tratar erros da API Resend com classes tipadas
- **Squad:** Beta | **Esforço:** 1h

### [S3-T03] — app/api/contato/route.ts — API Route
- `POST /api/contato` com validação Zod server-side
- Rate limiting: 3 req/hora por IP (via `@upstash/ratelimit` ou header-based)
- Resposta tipada: `{ success: boolean; message: string }`
- **Squad:** Beta | **Esforço:** 2h

### [S3-T04] — Componente: Formulário de Contato (React Hook Form)
- 5 campos + validação client-side em tempo real
- Estado de loading (spinner no botão)
- Estado de sucesso (substituir formulário por mensagem)
- Estado de erro (mensagem inline)
- Honeypot field invisível (CSS: `display:none`)
- **Squad:** Beta | **Esforço:** 3h

### [S3-T05] — Testes Playwright — Configuração
```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests',
  use: { baseURL: 'http://localhost:3000' },
  projects: [
    { name: 'chromium' },
    { name: 'mobile', use: devices['Pixel 5'] },
  ],
})
```
- **Squad:** Gamma | **Esforço:** 1h

### [S3-T06] — Testes Playwright — Navegação
```
Cenário: Smooth scroll via menu
  - Clicar em cada link do menu
  - Verificar que a seção correspondente está visível
  - Verificar URL com âncora

Cenário: Menu mobile
  - Viewport 375px
  - Abrir/fechar hambúrguer
  - Clicar em link → menu fecha
```
- **Squad:** Gamma | **Esforço:** 2h

### [S3-T07] — Testes Playwright — Formulário
```
Cenário: Submissão válida
  - Preencher todos os campos com dados válidos
  - Submeter
  - Verificar mensagem de sucesso

Cenário: Validação de campos
  - Submeter formulário vazio
  - Verificar mensagens de erro em cada campo

Cenário: Campo e-mail inválido
  - Inserir "nao-e-um-email"
  - Verificar erro de formato
```
- **Squad:** Gamma | **Esforço:** 2h

### [S3-T08] — GitHub Actions — CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
jobs:
  quality:
    - Install dependencies (pnpm)
    - TypeScript check (tsc --noEmit)
    - Lint (next lint)
    - Build (next build)
  
  lighthouse:
    - Deploy preview via Vercel CLI
    - Run Lighthouse CI
    - Assert: performance ≥ 90, seo ≥ 90, accessibility ≥ 90
  
  e2e:
    - Start server
    - Run Playwright tests
    - Upload report as artifact
```
- **Squad:** Delta | **Esforço:** 3h

---

## Sprint 4 — Expansão (Backlog Priorizado)

**Objetivo:** Enriquecer conteúdo e capacidades de conversão.
**Duração estimada:** 32 horas | **Squad:** Alpha + Beta

| ID | Tarefa | Esforço |
|----|--------|---------|
| S4-T01 | Seção Portfólio — cards de projetos ATHOS (Cardtrack, BarberFlow, etc.) | 6h |
| S4-T02 | Página de Caso de Sucesso (rota `/cases/[slug]`) | 8h |
| S4-T03 | Blog técnico via MDX (`/blog/[slug]`) | 10h |
| S4-T04 | Vercel Analytics + Speed Insights integrado | 1h |
| S4-T05 | i18n — versão em inglês (next-intl) | 6h |
| S4-T06 | Teste A/B no CTA principal (Vercel Edge Config) | 2h |

---

## Mapeamento para Clean Architecture

| Camada | Localização | Conteúdo |
|--------|-------------|---------|
| **Domain** | `src/lib/validations.ts` | Regras de validação (schema Zod) — sem dependência de UI |
| **Application** | `src/app/api/contato/route.ts` | Orquestração: valida → envia → responde |
| **Infrastructure** | `src/lib/resend.ts` | Implementação concreta do envio de e-mail |
| **Interfaces** | `src/components/sections/Contato.tsx` | Formulário React que consome a API |

---

## Definição de Pronto por Tarefa (DoD)

Uma tarefa está concluída quando:
- [ ] Código implementado e sem erros de TypeScript
- [ ] ESLint sem warnings
- [ ] Funcionalidade verificada manualmente no browser
- [ ] Componente responsivo testado em 375px, 768px e 1280px
- [ ] Sem regressão nas outras seções
- [ ] Commit na branch feature com mensagem Conventional Commits
