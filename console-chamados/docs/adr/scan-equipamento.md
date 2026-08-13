# ADR: Protocolo de Comunicação para Scan Remoto de Equipamentos

**Status:** Aceito  
**Data:** 2026-07-23  
**Contexto:** Implementação da funcionalidade de scan prévio de equipamento no fluxo de abertura de chamados.

---

## Contexto

O sistema precisa executar um diagnóstico remoto em totens (equipamentos de ponto de venda/atendimento) antes de registrar um chamado do tipo Hardware. Os totens operam com sistemas operacionais heterogêneos: **Windows, Linux e Android**.

Três opções foram avaliadas.

---

## Opções avaliadas

### Opção A — Agente HTTP local no totem

Um serviço leve roda no próprio totem e expõe endpoints REST:

```
GET /status/display
GET /status/hardware
GET /status/printer
GET /status/connectivity
```

O backend chama esses endpoints via IP.

**Prós:** Protocolo uniforme em qualquer OS; endpoints customizáveis; fácil de testar/mockar; sem overhead de configuração de SNMP ou gestão de chaves SSH.  
**Contra:** Exige instalação do agente em cada totem.

---

### Opção B — SNMP

Consulta via protocolo SNMP (OIDs padrão ou customizados).

**Prós:** Não exige agente se o totem já expõe SNMP.  
**Contra:** SNMP não está confirmado nos totens; OIDs para dados customizados (fila de impressão, status de display) exigem MIBs proprietárias; suporte a Android é marginal.

---

### Opção C — SSH remoto

Conecta via SSH e executa comandos de diagnóstico.

**Prós:** Flexível; sem agente necessário se SSH habilitado.  
**Contra:** SSH em Android é impraticável sem root; exige gestão de chaves por totem; latência maior; maior superfície de ataque.

---

## Decisão: Opção A — Agente HTTP local

### Justificativa

1. **Heterogeneidade de OS:** A única informação disponível sobre os totens é que rodam Windows, Linux ou Android. SSH em Android é inviável sem root/Termux; SNMP em Android não tem suporte nativo. O agente HTTP é o único protocolo que funciona uniformemente nos três sistemas.

2. **Dados customizados:** As informações necessárias (status de display, fila de impressora, firmware) não são mapeáveis via OIDs SNMP padrão. Exigiriam MIBs proprietárias — mesma complexidade de instalar um agente, porém com menos flexibilidade.

3. **Extensibilidade:** Novos endpoints podem ser adicionados ao agente sem alterar o backend — basta o agente expor um novo path.

4. **Testabilidade:** Chamadas HTTP são fáceis de mockar; outros protocolos (SNMP, SSH) têm dependências de sistema mais pesadas nos testes.

5. **Sem dependências externas:** A implementação usa apenas `urllib.request` e `socket` da stdlib Python — sem novos pacotes em `requirements.txt`.

---

## Consequências

- Cada novo totem precisa ter o agente instalado antes de ser cadastrado no sistema.
- O agente deve expor os 4 endpoints documentados em `docs/configurar-totem.md`.
- A porta padrão do agente é `8765` (configurável via `AGENT_PORT`).
- O timeout por verificação é `10s` (configurável via `SCAN_TIMEOUT_S`).
- Se o agente não estiver acessível, o sistema registra o totem como `offline` e permite abrir o chamado normalmente — "totem não responde" também é um sintoma válido.
