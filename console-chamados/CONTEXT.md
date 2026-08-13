# CONTEXT.md — Console de Chamados
**Athos Tecnologia · Projeto Interno**
Documento de Constituição — Fase 0 (retroativo)
Data de análise: 2026-08-03

---

## 1. Problema de Negócio

A Athos Tecnologia opera projetos para múltiplos clientes e mantém uma frota crescente de totens e equipamentos em campo. Sem um sistema centralizado, os chamados de suporte eram gerenciados via chat/e-mail, gerando:

- Perda de histórico e contexto entre atendentes
- Impossibilidade de medir SLA ou MTTR
- Nenhuma auditoria de movimentações
- Dificuldade de priorização em momentos de incidente simultâneo
- Ausência de visibilidade de oportunidades comerciais ligadas a chamados

**Solução:** console web interno que unifica ticket management, monitoramento de equipamentos, gestão de incidentes e pipeline comercial (CRM) em uma única interface.

---

## 2. Usuário Final

| Papel | Descrição | Acesso |
|---|---|---|
| **Solicitante** | Abre chamados, acompanha status, comenta | Limitado ao board e detalhe |
| **Atendente** | Atende, move status, atribui, comenta | Board + relatórios + equipamentos |
| **Admin** | Gestão total | Tudo, incluindo usuários, incidentes, CRM |

O cadastro de solicitantes requer aprovação manual de um admin (fluxo `ativo=0 → 1`).

---

## 3. Escopo Funcional Implementado

### Módulo 1 — Autenticação & Acesso
- Login/logout com sessão Flask nativa
- Cadastro de solicitante (aprovação admin obrigatória)
- Decorators `@login_required` e `@admin_required`
- Rate limiting em `/login` e `/cadastro`
- CSRF em todos os formulários POST

### Módulo 2 — Board Kanban
- 6 colunas: **Aberto → Em andamento → Aguardando → Impedido → Resolvido → Cancelado**
- Drag-and-drop via JS nativo (atualiza status via API JSON)
- Clique em card abre detalhe
- KPIs em tempo real: 6 cards (Total ativos, Em andamento, Aguardando, SLA em risco, MTTR 30d, % SLA cumprido)
- Paginação por coluna (50 cards/coluna)

### Módulo 3 — Chamado (detalhe)
- Criação com: título, descrição, prioridade, setor, equipamento vinculado, anexo (≤10MB)
- Timeline unificada: movimentações de status + comentários em ordem cronológica
- Comentários com anexo opcional
- Sidebar: seletor de status, atribuição, prioridade, barra de SLA progressiva
- Exclusão (somente admin, com confirmação)

### Módulo 4 — SLA Automático
| Prioridade | SLA |
|---|---|
| Alta (Crítico) | 4 horas |
| Média (Urgente) | 24 horas |
| Baixa (Comum) | 48 horas |
Barra de cor: verde (<40%), âmbar (40–75%), vermelho (>75% ou vencido).

### Módulo 5 — Relatórios
- Sumário geral (total, resolvidos, ativos, alta pendente, MTTR histórico, taxa SLA)
- Gráfico de pizza por status e por prioridade
- Tendência de 30 dias (abertos vs. resolvidos por dia)
- Ranking de atendentes (chamados abertos, resolvidos, MTTR por atendente)
- Exportação CSV com 12 colunas

### Módulo 6 — Gestão de Usuários (admin)
- CRUD: criar, editar (nome, papel, senha opcional), ativar/desativar
- Contador de chamados ativos por atendente
- Papéis: `solicitante`, `atendente`, `admin`

### Módulo 7 — Gestão de Equipamentos / Totens
- CRUD de equipamentos (nome, IP, modelo, serial, setor)
- Scan remoto via agente HTTP local (4 checks: display, hardware, impressora, conectividade)
- Scan por IP avulso (sem equipamento cadastrado)
- Histórico de scans persistido em `equipment_scan_results`
- Decisão de protocolo documentada em `docs/adr/scan-equipamento.md`

### Módulo 8 — Gestão de Incidentes
- Severidades: P0 (crítico), P1 (alto), P2 (médio)
- Status: Detectado → Reconhecido → Mitigando → Resolvido → Post-mortem
- Timeline de eventos (status + comentários)
- KPIs: total ativos, P0 ativos, usuários impactados, MTTR de incidentes
- Acesso restrito a admin e atendente

### Módulo 9 — CRM
- Clientes: CRUD com empresa, telefone, e-mail, origem
- Oportunidades: vinculadas a clientes, estágios (Prospecção → Qualificação → Proposta → Fechado/Perdido)
- Funil Kanban de oportunidades
- Interações: registro de histórico de contatos por cliente/oportunidade
- Chamados podem ser vinculados a um cliente CRM

---

## 4. Justificativa da Stack

### 4.1 Critérios Avaliados

| Critério | Análise |
|---|---|
| **Natureza** | App web interno de gestão (CRUD + dashboards) |
| **Escala** | Equipe interna pequena (<50 usuários simultâneos) |
| **Latência** | Tolerante (sem real-time obrigatório) |
| **Restrições** | Sem time dedicado de frontend; sem orçamento para infra complexa |
| **Prazo** | MVP urgente |
| **Manutenibilidade** | Único desenvolvedor/squad pequeno |

### 4.2 Escolhas e Justificativas

**Backend: Flask 3.0 + Python**
Flask foi escolhido sobre Django (overkill para o escopo) e FastAPI (sem SSR nativo). Oferece máxima flexibilidade com mínimo de convenção. Para um app interno com rotas simples, é a escolha de menor atrito.

**Banco: SQLite puro (sem ORM)**
PostgreSQL seria superdimensionado: volume esperado não ultrapassa dezenas de milhares de registros. SQLite elimina a necessidade de servidor de banco, simplifica deploy e backup. A ausência de ORM (sem SQLAlchemy) foi uma escolha deliberada de simplicidade — SQL explícito é mais previsível para um schema controlado e evoluído via migrações inline.

**Frontend: Jinja2 + CSS/JS vanilla**
Sem necessidade de SPA. SSR com Jinja2 reduz a superfície de erro (sem build pipeline, sem node_modules, sem estado frontend complexo). O drag-and-drop do Kanban é a única interação JS rica e foi implementada com ~200 linhas vanilla.

**Segurança: Flask-WTF (CSRF) + Flask-Limiter + bcrypt**
CSRF nativo via Flask-WTF. Rate limiting em rotas sensíveis (login, cadastro). Senhas hasheadas com `werkzeug.security` (bcrypt).

**Infra: Monolito simples**
Sem Docker ou CI/CD implementado (fase atual). O app roda com `python app.py`. Adequado para uso interno com deploy manual.

### 4.3 Trade-offs Aceitos Conscientemente

| Trade-off | Decisão | Consequência |
|---|---|---|
| SQLite vs PostgreSQL | SQLite | Sem suporte a múltiplas escritas concorrentes pesadas; limita escala |
| Monolito vs módulos | Monolito (`app.py` único) | Mais simples de manter agora; refatoração necessária se crescer |
| SSR vs SPA | SSR (Jinja2) | Sem atualizações em tempo real; usuário precisa recarregar para ver mudanças de outros |
| Sem ORM | SQL puro | Mais verboso, mas sem magic escondida; migrações manuais |

---

## 5. Arquitetura Aplicada

O projeto é um **monolito Flask deliberado**. A separação por camadas da Clean Architecture foi aplicada parcialmente:

- **Domínio/Regras de negócio:** concentradas em `app.py` (funções de SLA, helpers de auditoria, regras de papel)
- **Infraestrutura (banco):** acesso direto via `get_db()` dentro das rotas — sem repository pattern
- **Interface:** rotas Flask = controllers + views (Jinja2)
- **Módulo isolado:** `equipment_scan/` segue separação adequada (scanner.py, rules.py) e é 100% testável sem banco ativo

**Se o projeto escalar**, a refatoração prioritária seria:
1. Extrair um `services.py` (Application Layer) das rotas de `app.py`
2. Criar `repositories.py` (Infrastructure Layer) para isolar SQL
3. Considerar migração para PostgreSQL + Alembic

---

## 6. Banco de Dados — Modelo de Dados

```
usuarios        — contas (solicitante / atendente / admin), bcrypt
setores         — departamentos vinculados a chamados e equipamentos
equipamentos    — totens e dispositivos em campo (IP, modelo, serial)
chamados        — ticket principal (título, descrição, prioridade, status, SLA, equipamento_id, cliente_id)
movimentacoes   — auditoria imutável de cada mudança de status
comentarios     — anotações por chamado (com anexo opcional)
equipment_scan_results — histórico de diagnósticos remotos por equipamento/chamado
incidentes      — eventos de indisponibilidade (P0/P1/P2)
incidente_eventos — timeline de cada incidente
clientes        — entidades CRM
oportunidades   — pipeline comercial (funil 5 estágios)
interacoes      — histórico de contatos por cliente/oportunidade
```

---

## 7. Decisões de Arquitetura Registradas (ADRs)

| ADR | Status | Arquivo |
|---|---|---|
| Protocolo de scan de equipamentos (HTTP Agente vs SNMP vs SSH) | Aceito | `docs/adr/scan-equipamento.md` |
