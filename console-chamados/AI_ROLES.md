# AI_ROLES.md — Console de Chamados
**Athos Tecnologia · Projeto Interno**
Documento de Constituição — Mapeamento de Squads (retroativo)
Data: 2026-08-03

---

## Squads Ativas neste Projeto

### Squad Alpha — Product & Architecture

**Agent Product Manager Staff**
- Traduziu a demanda de suporte interno fragmentado (chat/e-mail) em especificação BDD (`SPEC.md`)
- Priorizou módulos: Kanban + SLA primeiro; CRM e Incidentes em iterações seguintes
- Mantém rastreabilidade entre cenários BDD e rotas implementadas

**Agent Software Architect**
- Decidiu stack (Flask + SQLite puro + Jinja2) e documentou justificativas em `CONTEXT.md` seção 4
- Definiu modelo de dados em `schema.sql` com migrações incrementais inline em `migrate_db()`
- Aprovou ADR de protocolo HTTP para scan de equipamentos (`docs/adr/scan-equipamento.md`)
- Guardião da separação entre módulo `equipment_scan/` (isolado e testável) e monolito `app.py`

---

### Squad Beta — Core Engineering

**Agent Senior Backend Engineer**
- Implementou `app.py` (2.216 linhas): autenticação, todas as rotas, SLA, KPIs, relatórios, incidentes, CRM
- Implementou `equipment_scan/scanner.py` e `equipment_scan/rules.py` com separação de responsabilidades
- Escreveu `schema.sql`, `seed.py` e `seed_crm.py`
- Padrão: SQL puro via `sqlite3`, sem ORM, `row_factory = sqlite3.Row`

**Agent Senior Frontend Engineer**
- Implementou templates Jinja2: `board.html`, `chamado_detalhe.html`, `relatorios.html`, `incidentes.html`, `crm_*.html`, `usuarios.html`, `equipamentos.html`, `login.html`, `cadastro.html`
- Implementou `static/js/board.js`: drag-and-drop Kanban, navegação por clique, API calls JSON
- Tema visual: navy/amber com CSS vanilla em `static/css/style.css`

---

### Squad Gamma — Quality & Assurance

**Agent Senior SDET**
- Escreveu 120 testes em 4 arquivos (`test_app.py`, `test_api.py`, `test_scanner.py`, `test_chamado_com_scan.py`)
- Configurou `tests/conftest.py` com fixtures de banco em memória
- Cobertura: autenticação, CRUD de chamados, movimentações, scanner (unitário puro), integração chamado+scan
- Ferramenta de carga: `locustfile.py` (Locust) para testes de performance

---

### Squad Delta — Platform & DevOps

**Agent Senior DevOps/SRE**
- Estado atual: deploy manual (`python app.py`)
- Pendente: Dockerização e CI/CD (escopo futuro, ver `PLAN.md` Sprint 3)

---

### Squad Omega — Commercial & Growth

**Agent Account Executive Staff**
- Projeto interno — sem proposta comercial externa
- CRM integrado ao console serve como ferramenta do próprio Squad Omega para gestão de pipeline

---

## Responsabilidades por Artefato

| Artefato | Squad responsável |
|---|---|
| `CONTEXT.md` | Alpha (Architect) |
| `AI_ROLES.md` | Alpha (Architect) |
| `SPEC.md` | Alpha (PM) |
| `PLAN.md` | Alpha + Beta + Delta |
| `app.py` | Beta (Backend) |
| `equipment_scan/` | Beta (Backend) |
| `templates/` | Beta (Frontend) |
| `static/` | Beta (Frontend) |
| `schema.sql` | Beta (Backend) + Alpha (Architect) |
| `tests/` | Gamma (SDET) |
| `docs/adr/` | Alpha (Architect) |
