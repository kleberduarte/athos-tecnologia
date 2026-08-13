"""
Regras de mapeamento: resultado do scan → categoria/prioridade sugerida.

Cada regra tem uma condição (callable que recebe ScanResult) e os campos
sugeridos. As regras são avaliadas em ordem; a primeira que bater vence.
Edite aqui para ajustar a lógica sem tocar no scanner ou nas rotas.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scanner import ScanResult

# Statuses que indicam problema na impressora
_IMPRESSORA_BLOQUEANTE = frozenset({"sem_papel", "fila_travada"})
_IMPRESSORA_DEGRADADA = frozenset({"sem_toner", "erro"})

# Statuses que indicam totem inacessível
_OFFLINE = frozenset({"offline", "timeout"})

RULES: list[dict] = [
    {
        "condition": lambda r: r.conectividade.status in _OFFLINE,
        "prioridade": "alta",
        "nota": "Totem inacessível — nenhuma resposta no prazo configurado.",
    },
    {
        "condition": lambda r: r.display.status in ("sem_sinal", "travado"),
        "prioridade": "alta",
        "nota": "Display sem sinal ou travado — totem inutilizável para operação.",
    },
    {
        "condition": lambda r: r.impressora.status in _IMPRESSORA_BLOQUEANTE,
        "prioridade": "alta",
        "nota": f"Impressora com problema bloqueante: {'{status}'}.",
    },
    {
        "condition": lambda r: r.display.status == "erro",
        "prioridade": "media",
        "nota": "Display reporta erro — operação pode estar degradada.",
    },
    {
        "condition": lambda r: r.impressora.status in _IMPRESSORA_DEGRADADA,
        "prioridade": "media",
        "nota": "Impressora com problema não-bloqueante (toner/erro).",
    },
]


def aplicar_regras(result: "ScanResult") -> dict:
    """Retorna {'prioridade': str, 'nota': str} com base no resultado do scan."""
    for rule in RULES:
        if rule["condition"](result):
            nota = rule["nota"]
            if "{status}" in nota:
                nota = nota.replace(
                    "{status}", result.impressora.status.replace("_", " ")
                )
            return {"prioridade": rule["prioridade"], "nota": nota}
    return {
        "prioridade": "baixa",
        "nota": "Diagnóstico concluído — nenhum problema crítico detectado.",
    }
