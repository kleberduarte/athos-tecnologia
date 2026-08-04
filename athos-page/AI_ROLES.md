# AI_ROLES.md — Athos Page
**Projeto:** athos-page | **Cliente:** Athos Tecnologia (Interno)
**Versão:** 1.0 | **Data:** 2026-08-04

---

## Constituição de Squads — Projeto athos-page

Mapeamento de responsabilidades por Squad para o projeto de landing page institucional da Athos Tecnologia.

---

### 💼 Squad Omega — Commercial & Growth

**Contexto:** Projeto interno. Não há proposta comercial para cliente externo. Squad Omega atua em papéis de crescimento e otimização.

| Agente | Responsabilidade no Projeto |
|--------|---------------------------|
| **Agent SDR Staff** | Análise de conversão da landing page; benchmarking de competidores; inteligência de mercado para posicionamento |
| **Agent Tech Estimator** | Estimativa de esforço para cada sprint; custo de infraestrutura (Vercel, Resend, domínio) |
| **Agent Account Executive** | N/A para projeto interno — foco em otimização de CTA e copy para maximizar leads |

**Artefatos:** `PROPOSAL.md` (escopo e roadmap interno)

---

### 🔹 Squad Alpha — Product & Architecture

| Agente | Responsabilidade no Projeto |
|--------|---------------------------|
| **Agent Product Manager** | Definição de KPIs da landing page (taxa de conversão, bounce rate, tempo na página); roadmap de funcionalidades; `SPEC.md` |
| **Agent Software Architect** | Decisão de stack (ver `CONTEXT.md`); arquitetura de componentes Next.js; estrutura de pastas; performance strategy |

**Artefatos:** `CONTEXT.md`, `SPEC.md`, `PLAN.md`

---

### 🔹 Squad Beta — Core Engineering

| Agente | Responsabilidade no Projeto |
|--------|---------------------------|
| **Agent Senior Frontend Engineer** | Implementação das seções em React/Next.js + Tailwind; componentização; animações; formulário de contato; responsividade |
| **Agent Senior Backend Engineer** | API Route para formulário de contato; integração Resend; validação Zod server-side |

**Artefatos:** Código-fonte em `src/`, componentes React, API Routes

---

### 🔹 Squad Gamma — Quality & Assurance

| Agente | Responsabilidade no Projeto |
|--------|---------------------------|
| **Agent Senior SDET (QA)** | Testes Playwright (fluxo de formulário, navegação, responsividade); auditoria de acessibilidade WCAG 2.1 AA; Lighthouse CI |

**Artefatos:** `tests/`, `playwright.config.ts`, relatórios Lighthouse

---

### 🔹 Squad Delta — Platform & DevOps

| Agente | Responsabilidade no Projeto |
|--------|---------------------------|
| **Agent Senior DevOps/SRE** | Configuração Vercel (domínio, env vars, preview deployments); GitHub Actions CI/CD; sitemap.xml; robots.txt; SSL/CDN |

**Artefatos:** `.github/workflows/`, `vercel.json`, `next.config.ts`

---

## Fluxo de Trabalho por Fase

```
FASE 0 → Alpha (Architect): CONTEXT.md + stack decision
FASE 1 → Alpha (PM): SPEC.md com BDD
FASE 2 → Omega (Estimator): PROPOSAL.md com esforço e roadmap
FASE 3 → Alpha + Beta + Delta: PLAN.md com sprints
FASE 4 → Beta: Implementação sprint a sprint
FASE 5 → Gamma + Delta: Testes + deploy + VALIDATE.md
```

---

## Padrão de Design — Design Bar Athos

Todos os componentes implementados devem atender:

| Critério | Padrão |
|---------|--------|
| Tipografia | Escala consistente (text-sm → text-5xl via Tailwind) |
| Paleta | Dark mode como default; contraste AA (4.5:1 mínimo) |
| Estados | Loading, erro, vazio e sucesso tratados em formulários |
| Responsividade | Mobile (375px), Tablet (768px), Desktop (1280px) |
| Componentização | DRY — sem duplicação de lógica entre seções |
| Microinterações | Reveal no scroll, hover nos cards, feedback no formulário |
| Performance | LCP < 2,5s; nenhuma imagem sem width/height explícitos |

---

## Paleta de Cores (Identidade Atual — Preservar na Migração)

```
Background:      #000000 (preto absoluto)
Surface:         #0a0a0a / #111111 (dark cards)
Border:          rgba(255,255,255,0.08-0.12)
Text Primary:    #ffffff
Text Secondary:  rgba(255,255,255,0.6)
Accent:          #ffffff (sem cor de destaque adicional — pureza visual)
YEP Accent:      linha dourada/âmbar para cards parceiro YEP
```
