# PROPOSAL.md — Console de Chamados
**Athos Tecnologia · Projeto Interno**
Proposta Técnica e Estimativa de Esforço (retroativa) — Fase 2
Data: 2026-08-03

---

## Natureza do Projeto

Projeto interno da própria Athos Tecnologia. Não há cliente externo nem contrato comercial. Este documento serve como registro de esforço investido, custo de oportunidade e base para priorização de roadmap futuro.

---

## Escopo Entregue (v1.0)

| Módulo | Complexidade | Horas estimadas |
|---|---|---|
| Autenticação + autorização por papel | Média | 8h |
| Board Kanban + drag-and-drop | Alta | 16h |
| CRUD de chamados + timeline unificada | Alta | 20h |
| SLA automático + barra progressiva | Média | 8h |
| KPIs em tempo real (6 cards) | Média | 6h |
| Relatórios analíticos + gráficos | Alta | 14h |
| Exportação CSV | Baixa | 3h |
| Gestão de usuários (CRUD admin) | Média | 8h |
| Upload de anexos (chamados + comentários) | Média | 6h |
| Módulo de equipamentos + CRUD | Média | 8h |
| Scan remoto via agente HTTP (module isolado) | Alta | 20h |
| Gestão de incidentes (P0/P1/P2) | Alta | 18h |
| CRM (clientes, oportunidades, funil) | Alta | 22h |
| Schema + migrações incrementais | Média | 8h |
| Testes automatizados (120 testes) | Alta | 16h |
| Seed de dados de exemplo | Baixa | 4h |
| **TOTAL ESTIMADO** | — | **~185 horas** |

---

## Custo de Oportunidade (Referência Interna)

| Item | Valor referência |
|---|---|
| Taxa horária sênior interna | R$ 150/h |
| Custo total estimado (desenvolvimento) | R$ 27.750 |
| Infra (SQLite local, sem servidor de banco) | R$ 0/mês |
| Hosting atual (manual, sem servidor dedicado) | R$ 0/mês |
| **Custo total de propriedade (Ano 1)** | **~R$ 27.750** |

---

## ROI Estimado

- Eliminação de chamados perdidos em chat/e-mail: estimativa de **2h/semana** de retrabalho evitado por atendente
- Visibilidade de SLA: permite identificar gargalos e melhorar MTTR em até 30%
- Funil CRM integrado: consolida pipeline que antes estava em planilhas — elimina ferramenta externa (CRM SaaS: ~R$ 500/mês)
- **Payback estimado:** < 3 meses de uso com equipe de 3 atendentes

---

## Aprovação

- [x] Escopo técnico aprovado pela Squad Alpha
- [x] Estimativa de horas validada pela Squad Omega
- [x] Implementação autorizada (projeto interno — aprovação tácita da liderança técnica)

---

## Roadmap Futuro (não incluído no escopo atual)

| Feature | Estimativa | Prioridade |
|---|---|---|
| Dockerização + CI/CD (GitHub Actions) | 12h | Alta |
| Notificações por e-mail (chamado atribuído, SLA em risco) | 10h | Alta |
| Portal do solicitante (visão simplificada) | 8h | Média |
| Migração para PostgreSQL | 16h | Média |
| WebSocket para atualização em tempo real do board | 14h | Baixa |
| App mobile (PWA ou React Native) | 40h | Baixa |
