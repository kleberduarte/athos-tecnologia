# SPEC.md — Console de Chamados
**Athos Tecnologia · Projeto Interno**
Especificação BDD (retroativa) — Fase 1
Data: 2026-08-03

---

## Objetivo

Sistema web interno para gestão de chamados de suporte técnico, monitoramento de equipamentos em campo, resposta a incidentes e pipeline comercial (CRM) da Athos Tecnologia.

---

## Épicos e Histórias de Usuário

---

### ÉPICO 1 — Acesso e Identidade

#### HU-01: Login de usuário

> Como qualquer colaborador, quero fazer login com e-mail e senha para acessar o sistema.

**Cenário 1.1 — Login bem-sucedido**
```
Dado que sou um usuário ativo no sistema
Quando informo e-mail e senha corretos no formulário de login
Então sou redirecionado para o board principal
E meu nome aparece na barra de navegação
```

**Cenário 1.2 — Credenciais inválidas**
```
Dado que informo e-mail ou senha incorretos
Quando submeto o formulário
Então permaneço na tela de login
E vejo a mensagem "E-mail ou senha inválidos"
```

**Cenário 1.3 — Rate limiting**
```
Dado que tentei login com credenciais inválidas 10 vezes em 1 minuto
Quando faço uma nova tentativa
Então recebo erro 429 (Too Many Requests)
```

**Cenário 1.4 — Conta inativa**
```
Dado que minha conta está desativada
Quando faço login com credenciais corretas
Então vejo a mensagem "Conta desativada"
E não sou autenticado
```

---

#### HU-02: Cadastro de solicitante

> Como novo solicitante, quero me cadastrar para que um admin aprove meu acesso.

**Cenário 2.1 — Cadastro bem-sucedido**
```
Dado que acesso /cadastro sem estar logado
Quando preencho nome, e-mail, setor e senha válidos
Então minha conta é criada com status ativo=0
E vejo mensagem "Cadastro enviado. Aguarde aprovação"
```

**Cenário 2.2 — E-mail duplicado**
```
Dado que o e-mail informado já existe no banco
Quando submeto o formulário
Então vejo "E-mail já cadastrado" e o cadastro não é criado
```

**Cenário 2.3 — Aprovação pelo admin**
```
Dado que há um solicitante com conta pendente (ativo=0)
Quando o admin acessa /usuarios e ativa a conta
Então o solicitante pode fazer login normalmente
```

---

### ÉPICO 2 — Board Kanban e Chamados

#### HU-03: Visualização do board

> Como atendente, quero ver todos os chamados organizados em colunas para entender o estado geral do suporte.

**Cenário 3.1 — Board com chamados**
```
Dado que há chamados em diferentes status
Quando acesso "/"
Então vejo 6 colunas: Aberto, Em andamento, Aguardando, Impedido, Resolvido, Cancelado
E cada coluna exibe o número de chamados no cabeçalho
E os 6 cards de KPI aparecem no topo
```

**Cenário 3.2 — KPI: SLA em risco**
```
Dado que há chamados com SLA >= 75% consumido e status != resolvido/cancelado
Quando acesso o board
Então o card "SLA em risco" exibe a contagem correta
E o card é exibido em âmbar ou vermelho
```

---

#### HU-04: Abertura de chamado

> Como solicitante ou atendente, quero abrir um chamado informando título, descrição, prioridade e setor.

**Cenário 4.1 — Chamado criado com sucesso**
```
Dado que estou logado e acesso o board
Quando clico em "Novo chamado", preencho título, descrição, prioridade (alta/média/baixa) e setor
E submeto o formulário
Então o chamado é criado com status "aberto" e SLA definido automaticamente pela prioridade
E aparece na coluna "Aberto" do board
```

**Cenário 4.2 — SLA automático por prioridade**
```
Dado que crio um chamado
Quando a prioridade é "alta"
Então sla_horas = 4
Quando a prioridade é "media"
Então sla_horas = 24
Quando a prioridade é "baixa"
Então sla_horas = 48
```

**Cenário 4.3 — Chamado com anexo**
```
Dado que uploado um arquivo de até 10MB (jpg, pdf, doc, etc.)
Quando crio o chamado
Então o arquivo é salvo em static/uploads/
E o nome do arquivo aparece no detalhe do chamado
```

**Cenário 4.4 — Título muito longo**
```
Dado que digito um título com mais de 200 caracteres
Quando submeto o formulário
Então o chamado não é criado e vejo mensagem de erro de validação
```

---

#### HU-05: Detalhe e timeline do chamado

> Como atendente, quero ver o histórico completo de um chamado em ordem cronológica.

**Cenário 5.1 — Timeline unificada**
```
Dado que um chamado teve mudanças de status e comentários
Quando acesso o detalhe do chamado
Então vejo a timeline com eventos de status e comentários mesclados em ordem crescente de data
```

**Cenário 5.2 — Adicionar comentário**
```
Dado que estou no detalhe de um chamado
Quando escrevo um comentário e submeto
Então o comentário aparece imediatamente na timeline com meu nome e horário
```

**Cenário 5.3 — Movimentação de status via drag-and-drop**
```
Dado que estou no board
Quando arrasto um card de "Aberto" para "Em andamento"
Então o status é atualizado via API JSON sem recarregar a página
E uma movimentação é registrada em "movimentacoes" com status_anterior e status_novo
```

---

#### HU-06: SLA visual no detalhe

**Cenário 6.1 — Barra de progresso**
```
Dado que acesso o detalhe de um chamado ativo
Então vejo a barra de SLA com percentual consumido
E a cor é verde (<40%), âmbar (40–75%) ou vermelho (>75%)
```

**Cenário 6.2 — SLA vencido**
```
Dado que um chamado passou do prazo SLA
Então a barra aparece em vermelho com indicação de "Vencido"
```

---

#### HU-07: Exportação CSV

**Cenário 7.1**
```
Dado que sou atendente ou admin
Quando clico no botão de exportar no board
Então faço download de um arquivo .csv com todos os chamados
E o arquivo contém: ID, título, descrição, prioridade, status, SLA, setor, atribuído, criado por, criado_em, atualizado_em, resolvido_em
```

---

### ÉPICO 3 — Gestão de Usuários

#### HU-08: CRUD de usuários (admin)

**Cenário 8.1 — Criar usuário**
```
Dado que sou admin
Quando acesso /usuarios e crio um novo usuário com nome, e-mail, papel e senha
Então o usuário é criado e aparece na lista
```

**Cenário 8.2 — Desativar usuário**
```
Dado que sou admin
Quando desativo um usuário
Então ele não consegue mais fazer login
E seus chamados abertos permanecem atribuídos a ele
```

**Cenário 8.3 — Acesso negado para não-admin**
```
Dado que sou atendente
Quando acesso /usuarios diretamente
Então recebo erro 403
```

---

### ÉPICO 4 — Equipamentos e Scan Remoto

#### HU-09: Cadastro de equipamento

**Cenário 9.1**
```
Dado que sou admin ou atendente
Quando cadastro um equipamento com nome, IP, modelo, serial e setor
Então o equipamento aparece na lista em /equipamentos
```

#### HU-10: Scan remoto de totem

**Cenário 10.1 — Totem online**
```
Dado que o totem tem o agente HTTP rodando na porta 8765
Quando executo o scan em /api/equipamentos/<id>/scan
Então recebo status de display, hardware, impressora e conectividade
E o resultado é persistido em equipment_scan_results
```

**Cenário 10.2 — Totem offline**
```
Dado que o totem não responde ao agente HTTP (timeout)
Quando executo o scan
Então recebo status "offline" em conectividade
E posso abrir um chamado normalmente com essa informação como diagnóstico inicial
```

**Cenário 10.3 — Scan por IP avulso**
```
Dado que quero diagnosticar um equipamento não cadastrado
Quando acesso /api/scan/ip e informo um IP
Então recebo o mesmo diagnóstico de 4 checks
```

---

### ÉPICO 5 — Relatórios

#### HU-11: Dashboard analítico

**Cenário 11.1**
```
Dado que sou admin ou atendente
Quando acesso /relatorios
Então vejo:
- Cards de sumário (total, resolvidos, ativos, alta pendente, MTTR, taxa SLA)
- Gráfico de pizza por status
- Gráfico de pizza por prioridade
- Gráfico de linha (30 dias: abertos vs resolvidos)
- Ranking de atendentes
```

---

### ÉPICO 6 — Incidentes

#### HU-12: Abertura de incidente

**Cenário 12.1**
```
Dado que sou admin ou atendente
Quando acesso /incidentes e abro um incidente com título, severidade (P0/P1/P2) e serviço afetado
Então o incidente é criado com status "detectado"
E aparece no topo da lista (ordenado por severidade)
```

**Cenário 12.2 — Fluxo de status do incidente**
```
Dado que há um incidente ativo
Quando avanço o status de "detectado" → "reconhecido" → "mitigando" → "resolvido"
Então cada transição gera um evento na timeline com timestamp e usuário responsável
E ao resolver, registra resolvido_em automaticamente
```

**Cenário 12.3 — KPIs de incidentes**
```
Dado que acesso /incidentes
Então vejo: total ativos, P0 ativos, usuários impactados, MTTR de incidentes resolvidos
```

---

### ÉPICO 7 — CRM

#### HU-13: Gestão de clientes

**Cenário 13.1**
```
Dado que sou admin
Quando cadastro um cliente com nome, empresa, telefone, e-mail e origem
Então o cliente aparece na lista em /crm/clientes
E posso registrar interações no detalhe do cliente
```

#### HU-14: Funil de oportunidades

**Cenário 14.1**
```
Dado que há oportunidades em diferentes estágios
Quando acesso /crm/funil
Então vejo um Kanban com colunas: Prospecção → Qualificação → Proposta → Fechado → Perdido
E posso mover oportunidades entre estágios
```

**Cenário 14.2 — Vinculação chamado-cliente**
```
Dado que crio um chamado vinculando-o a um cliente CRM
Quando acesso o detalhe do cliente
Então os chamados vinculados aparecem no histórico do cliente
```

---

## Casos de Borda Mapeados

| Caso | Comportamento esperado |
|---|---|
| Usuário tenta acessar rota logada sem sessão | Redirecionado para `/login` |
| Solicitante tenta acessar `/relatorios` | Redirecionado para `/` (board) |
| Admin exclui chamado com comentários | Excluir em cascata (FK) |
| Upload de arquivo com extensão não permitida | Rejeição com mensagem de erro |
| Chamado atribuído a usuário desativado | Atribuição permanece; atendente aparece na lista como inativo |
| Scan com IP inválido | Retorna erro 400 com mensagem descritiva |
| Drag-and-drop para status terminal (resolvido) | Aceito; `resolvido_em` é preenchido automaticamente |
| Cancelar chamado já resolvido | Bloqueado (status terminais: resolvido, cancelado) |
| CSRF token ausente no POST | 400 Bad Request com página de erro CSRF |
