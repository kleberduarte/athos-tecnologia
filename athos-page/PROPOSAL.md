# PROPOSAL.md — Athos Page
**Projeto:** athos-page | **Cliente:** Athos Tecnologia (Projeto Interno)
**Data:** 2026-08-04
**Responsável:** Squad Omega — Commercial & Growth
**Tipo:** Roadmap Interno (sem proposta comercial externa)

---

## 1. RESUMO EXECUTIVO

A landing page institucional da Athos Tecnologia é o principal ativo digital de aquisição de clientes. O projeto consiste em evoluir a implementação atual (HTML/CSS/JS estático) para uma solução moderna, rastreável e conversora, seguindo a metodologia ATHOS e a stack Next.js + Vercel.

O investimento é interno e representa o custo de oportunidade de horas de engenharia da Squad Beta + Delta, sem custo de licenciamento de software.

---

## 2. ESCOPO DO PROJETO

### Sprint 0 — Padronização & Documentação (ATUAL)
- Criação de `CONTEXT.md`, `AI_ROLES.md`, `SPEC.md`, `PROPOSAL.md`, `PLAN.md`
- Análise técnica do estado atual
- Identificação de gaps e roadmap

### Sprint 1 — Correções Imediatas (HTML Atual)
- SEO: meta tags Open Graph, Twitter Cards, dados estruturados JSON-LD
- Performance: auto-hospedar fontes Google (eliminar dependência CDN)
- Acessibilidade: audit completo WCAG 2.1 AA, aria-labels, foco por teclado
- Formulário: integração Formspree ou Netlify Forms (formulário funcional sem backend próprio)
- Analytics: Google Analytics 4 ou Umami (privacy-first)
- CI/CD: deploy automático via Vercel / Netlify conectado ao repositório GitHub
- sitemap.xml + robots.txt

### Sprint 2 — Migração Next.js
- Setup do projeto Next.js 15 + TypeScript + Tailwind CSS 4
- Migração fiel das 8 seções existentes (preservar 100% do design e copy)
- Componentização (Header, Footer, cada seção como componente)
- Otimização de imagens (next/image)
- Fontes locais via next/font

### Sprint 3 — Formulário Próprio + Testes
- API Route `/api/contato` com Resend
- Validação Zod server-side + React Hook Form client-side
- Proteção: honeypot + rate limiting
- Testes Playwright: fluxo de formulário, navegação, responsividade
- Lighthouse CI no GitHub Actions (score gate ≥ 90)

### Sprint 4 — Otimizações & Expansão (Opcional)
- Seção de Portfólio / Casos de Sucesso (cards de projetos)
- Blog / Insights técnicos (MDX via Next.js)
- Vercel Analytics + Speed Insights
- Teste A/B em CTAs (Vercel Edge Config)
- Versão em inglês (i18n via next-intl)

---

## 3. ESTIMATIVA DE ESFORÇO

| Sprint | Escopo | Esforço Estimado |
|--------|--------|-----------------|
| Sprint 0 | Documentação ATHOS | 4h (Squad Alpha) |
| Sprint 1 | Correções HTML atual | 8h (Beta + Delta) |
| Sprint 2 | Migração Next.js | 24h (Beta) |
| Sprint 3 | Formulário + Testes + CI/CD | 16h (Beta + Gamma + Delta) |
| Sprint 4 | Expansão (opcional) | 32h (Beta + Alpha) |

**Total Sprint 0–3:** ~52 horas
**Total com Sprint 4:** ~84 horas

---

## 4. CUSTO DE INFRAESTRUTURA (MENSAL)

| Serviço | Plano | Custo Mensal |
|---------|-------|--------------|
| Vercel | Hobby (até 100GB bandwidth) | R$ 0 |
| Vercel | Pro (se necessário) | ~R$ 100 |
| Resend | Free (100 e-mails/dia) | R$ 0 |
| Domínio athostecnologia.com.br | Registro.br | ~R$ 40/ano (~R$ 3,33/mês) |
| Google Analytics 4 | Free | R$ 0 |
| **Total mínimo** | | ~R$ 3,33/mês |

---

## 5. ROI ESPERADO

**Cenário conservador (conversão de 1% dos visitantes em lead):**
- 500 visitantes/mês × 1% = 5 leads/mês
- Taxa de fechamento de 20% = 1 novo cliente/mês
- Ticket médio projeto ATHOS = R$ 30.000
- **ROI mensal estimado: R$ 30.000 com custo de infraestrutura < R$ 5/mês**

**Prazo de recuperação do investimento de engenharia:**
- 52h × R$ 280/h (tarifa interna) = R$ 14.560
- 1 projeto fechado via landing page = payback imediato

---

## 6. CRITÉRIOS DE ACEITAÇÃO

| Critério | Meta |
|---------|------|
| Lighthouse Performance | ≥ 90 |
| Lighthouse SEO | ≥ 90 |
| Lighthouse Acessibilidade | ≥ 90 |
| Core Web Vitals (LCP) | < 2,5s |
| Formulário funcional | E-mail entregue em < 30s |
| Deploy automático | < 2min após push na main |
| Sem erros no console | 0 erros em prod |

---

## 7. APROVAÇÃO

| Papel | Nome | Status |
|-------|------|--------|
| Responsável Técnico | Squad Alpha (Architect) | Aprovado |
| Responsável Comercial | Squad Omega | Aprovado |
| Stakeholder | Athos Tecnologia (Interno) | ✅ **Aprovado em 2026-08-04** |

> *Sprint 1 iniciado em 2026-08-04.*
