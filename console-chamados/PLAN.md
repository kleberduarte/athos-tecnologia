# PLAN.md — Console de Chamados
**Athos Tecnologia · Projeto Interno**
Plano Técnico de Implementação (retroativo + roadmap) — Fase 3
Data: 2026-08-03

---

## Legenda de Status

| Símbolo | Significado |
|---|---|
| ✅ | Concluído |
| 🔄 | Em andamento |
| ⏳ | Pendente |

---

## Sprint 0 — Fundação

| # | Tarefa | Responsável | Status |
|---|---|---|---|
| S0-01 | Criar schema.sql com tabelas iniciais (usuarios, setores, chamados, movimentacoes, comentarios) | Beta Backend | ✅ |
| S0-02 | Implementar migrate_db() com migrações incrementais sem perda de dados | Beta Backend | ✅ |
| S0-03 | Configurar Flask app: secret_key, CSRFProtect, Limiter, upload dir | Beta Backend | ✅ |
| S0-04 | Implementar get_db() com row_factory e close_db teardown | Beta Backend | ✅ |
| S0-05 | Criar seed.py com dados de exemplo (usuários, setores, chamados) | Beta Backend | ✅ |
| S0-06 | Configurar estrutura de pastas: templates/, static/css/, static/js/, equipment_scan/ | Beta Frontend | ✅ |

---

## Sprint 1 — Autenticação e Acesso

| # | Tarefa | Responsável | Status |
|---|---|---|---|
| S1-01 | Rota GET/POST /login com validação de e-mail/senha e sessão Flask | Beta Backend | ✅ |
| S1-02 | Rota GET /logout com limpeza de sessão | Beta Backend | ✅ |
| S1-03 | Decorator @login_required | Beta Backend | ✅ |
| S1-04 | Decorator @admin_required com retorno JSON 403 | Beta Backend | ✅ |
| S1-05 | Rota GET/POST /cadastro (papel=solicitante, ativo=0) | Beta Backend | ✅ |
| S1-06 | Rate limiting em /login (10/min) e /cadastro (5/min) | Beta Backend | ✅ |
| S1-07 | Template login.html com validação e mensagens de erro | Beta Frontend | ✅ |
| S1-08 | Template cadastro.html | Beta Frontend | ✅ |
| S1-09 | context_processor com contador de pendentes para admin | Beta Backend | ✅ |
| S1-10 | Testes: login válido, login inválido, conta inativa, rate limit | Gamma | ✅ |

---

## Sprint 2 — Board Kanban e Chamados

| # | Tarefa | Responsável | Status |
|---|---|---|---|
| S2-01 | Rota GET / com query de chamados agrupados por status e KPIs | Beta Backend | ✅ |
| S2-02 | KPI: Total ativos, Em andamento, Aguardando, SLA em risco, MTTR 30d, % SLA cumprido | Beta Backend | ✅ |
| S2-03 | Rota POST /chamados (criar chamado, SLA automático por prioridade) | Beta Backend | ✅ |
| S2-04 | Rota POST /chamados/<id>/status (JSON, registra movimentacao) | Beta Backend | ✅ |
| S2-05 | Rota POST /chamados/<id>/atribuir (JSON) | Beta Backend | ✅ |
| S2-06 | Rota POST /chamados/<id>/prioridade (JSON, recalcula SLA) | Beta Backend | ✅ |
| S2-07 | Rota DELETE /chamados/<id> (somente admin) | Beta Backend | ✅ |
| S2-08 | Rota GET /chamados/<id> com timeline unificada (movimentacoes + comentarios) | Beta Backend | ✅ |
| S2-09 | Rota POST /chamados/<id>/comentarios (com anexo opcional) | Beta Backend | ✅ |
| S2-10 | Upload de anexos: validação de extensão, uuid no filename, save em static/uploads/ | Beta Backend | ✅ |
| S2-11 | Rota GET /chamados/exportar (CSV com 12 colunas) | Beta Backend | ✅ |
| S2-12 | Template board.html: 6 colunas, KPI cards, modal novo chamado | Beta Frontend | ✅ |
| S2-13 | Template chamado_detalhe.html: timeline, sidebar SLA, formulário comentário | Beta Frontend | ✅ |
| S2-14 | static/js/board.js: drag-and-drop, clique para detalhe, API calls | Beta Frontend | ✅ |
| S2-15 | Barra de progresso SLA com cores dinâmicas | Beta Frontend | ✅ |
| S2-16 | Testes: criar chamado, SLA por prioridade, comentar, mover status, exportar CSV | Gamma | ✅ |

---

## Sprint 3 — Usuários e Equipamentos

| # | Tarefa | Responsável | Status |
|---|---|---|---|
| S3-01 | Rota GET /usuarios (lista com contador de chamados ativos) | Beta Backend | ✅ |
| S3-02 | Rota POST /usuarios (criar) | Beta Backend | ✅ |
| S3-03 | Rota POST /usuarios/<id>/editar (nome, papel, senha opcional) | Beta Backend | ✅ |
| S3-04 | Rota POST /usuarios/<id>/toggle (ativar/desativar) | Beta Backend | ✅ |
| S3-05 | Rota DELETE /usuarios/<id> | Beta Backend | ✅ |
| S3-06 | Template usuarios.html | Beta Frontend | ✅ |
| S3-07 | Migração 6: tabela equipamentos | Beta Backend | ✅ |
| S3-08 | Migração 8: coluna equipamento_id em chamados | Beta Backend | ✅ |
| S3-09 | Rota GET/POST /equipamentos (lista + criar) | Beta Backend | ✅ |
| S3-10 | Rota POST /equipamentos/<id>/editar e /toggle | Beta Backend | ✅ |
| S3-11 | Template equipamentos.html | Beta Frontend | ✅ |
| S3-12 | Testes: CRUD usuários, toggle, acesso admin-only | Gamma | ✅ |

---

## Sprint 4 — Scanner de Equipamentos

| # | Tarefa | Responsável | Status |
|---|---|---|---|
| S4-01 | Criar módulo equipment_scan/__init__.py | Beta Backend | ✅ |
| S4-02 | Implementar equipment_scan/scanner.py: CheckResult, ScanResult, EquipmentScanner | Beta Backend | ✅ |
| S4-03 | Implementar equipment_scan/rules.py: engine de diagnóstico por flags | Beta Backend | ✅ |
| S4-04 | Rota POST /api/equipamentos/<id>/scan (scan por equipamento cadastrado) | Beta Backend | ✅ |
| S4-05 | Rota POST /api/scan/ip (scan por IP avulso) | Beta Backend | ✅ |
| S4-06 | Rota GET /api/equipamentos (JSON para seletor no formulário de chamado) | Beta Backend | ✅ |
| S4-07 | Rota POST /api/equipamentos (criar via API JSON) | Beta Backend | ✅ |
| S4-08 | Migração 7: tabela equipment_scan_results | Beta Backend | ✅ |
| S4-09 | Persistência de resultados de scan em equipment_scan_results | Beta Backend | ✅ |
| S4-10 | Escrever ADR: protocolo HTTP vs SNMP vs SSH | Alpha Architect | ✅ |
| S4-11 | Testes unitários: CheckResult, ScanResult, EquipmentScanner (online/offline/timeout/impressora sem papel) | Gamma | ✅ |
| S4-12 | Teste de integração: chamado com scan | Gamma | ✅ |
| S4-13 | Documentação: docs/configurar-totem.md | Alpha PM | ✅ |

---

## Sprint 5 — Relatórios e Incidentes

| # | Tarefa | Responsável | Status |
|---|---|---|---|
| S5-01 | Rota GET /relatorios com sumário, MTTR, taxa SLA, charts, ranking atendentes | Beta Backend | ✅ |
| S5-02 | Template relatorios.html com Chart.js (pizza status, pizza prioridade, linha 30d) | Beta Frontend | ✅ |
| S5-03 | Migração 9: tabelas incidentes e incidente_eventos | Beta Backend | ✅ |
| S5-04 | Rota GET /incidentes com KPIs e ordenação por severidade | Beta Backend | ✅ |
| S5-05 | Rota POST /incidentes (criar) | Beta Backend | ✅ |
| S5-06 | Rota GET /incidentes/<id> com timeline de eventos | Beta Backend | ✅ |
| S5-07 | Rotas POST: /incidentes/<id>/status, /severidade, /atribuir, /eventos | Beta Backend | ✅ |
| S5-08 | Rota DELETE /incidentes/<id> (admin) | Beta Backend | ✅ |
| S5-09 | Templates incidentes.html e incidente_detalhe.html | Beta Frontend | ✅ |
| S5-10 | Restrição de acesso a incidentes: admin + atendente only | Beta Backend | ✅ |

---

## Sprint 6 — CRM

| # | Tarefa | Responsável | Status |
|---|---|---|---|
| S6-01 | Migração 10: tabelas clientes, oportunidades, interacoes + coluna cliente_id em chamados | Beta Backend | ✅ |
| S6-02 | Rota GET/POST /crm/clientes (lista + criar) | Beta Backend | ✅ |
| S6-03 | Rota GET /crm/cliente/<id> com interações e chamados vinculados | Beta Backend | ✅ |
| S6-04 | Rota POST /crm/cliente/<id>/interacao (registrar contato) | Beta Backend | ✅ |
| S6-05 | Rota GET /crm/funil (Kanban de oportunidades) | Beta Backend | ✅ |
| S6-06 | Rota POST /crm/oportunidades (criar) | Beta Backend | ✅ |
| S6-07 | Rota GET /crm/oportunidade/<id> (detalhe) | Beta Backend | ✅ |
| S6-08 | Rota POST /crm/oportunidade/<id>/estagio (mover no funil) | Beta Backend | ✅ |
| S6-09 | Rota POST /crm/oportunidade/<id>/editar | Beta Backend | ✅ |
| S6-10 | Endpoints JSON: /crm/_clientes_json, /crm/_usuarios_json (para selects dinâmicos) | Beta Backend | ✅ |
| S6-11 | Templates: crm_clientes.html, crm_cliente_detalhe.html, crm_funil.html, crm_oportunidade_detalhe.html | Beta Frontend | ✅ |
| S6-12 | seed_crm.py: dados de exemplo para o módulo CRM | Beta Backend | ✅ |

---

## Sprint 7 (Futuro) — DevOps e Notificações

| # | Tarefa | Responsável | Status | Prioridade |
|---|---|---|---|---|
| S7-01 | Criar Dockerfile multi-stage | Delta DevOps | ⏳ | Alta |
| S7-02 | docker-compose.yml (app + volume para console.db) | Delta DevOps | ⏳ | Alta |
| S7-03 | GitHub Actions: lint (flake8) + pytest em cada PR | Delta DevOps | ⏳ | Alta |
| S7-04 | Variáveis de ambiente: SECRET_KEY, DB_PATH, AGENT_PORT, SCAN_TIMEOUT_S via .env | Delta DevOps | ⏳ | Alta |
| S7-05 | Notificação e-mail: chamado atribuído ao atendente | Beta Backend | ⏳ | Alta |
| S7-06 | Notificação e-mail: SLA em risco (job periódico ou trigger) | Beta Backend | ⏳ | Alta |
| S7-07 | Notificação e-mail: novo cadastro pendente de aprovação | Beta Backend | ⏳ | Média |
| S7-08 | HTTPS: configurar nginx como reverse proxy | Delta DevOps | ⏳ | Média |
| S7-09 | Backup automático do console.db (cron + S3 ou drive local) | Delta DevOps | ⏳ | Média |

---

## Resumo de Progresso

| Sprint | Tarefas | Concluídas | Status |
|---|---|---|---|
| Sprint 0 — Fundação | 6 | 6 | ✅ Completo |
| Sprint 1 — Auth | 10 | 10 | ✅ Completo |
| Sprint 2 — Kanban | 16 | 16 | ✅ Completo |
| Sprint 3 — Usuários/Equipamentos | 12 | 12 | ✅ Completo |
| Sprint 4 — Scanner | 13 | 13 | ✅ Completo |
| Sprint 5 — Relatórios/Incidentes | 10 | 10 | ✅ Completo |
| Sprint 6 — CRM | 12 | 12 | ✅ Completo |
| Sprint 7 — DevOps/Notificações | 9 | 0 | ⏳ Pendente |
| **TOTAL** | **88** | **79** | **90% concluído** |
