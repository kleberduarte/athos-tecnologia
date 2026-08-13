"""
EquipmentScanner — diagnóstico remoto de totens via agente HTTP local (Opção A).

O agente que roda no totem deve expor os seguintes endpoints:
  GET /status/display       → {"status": "ok"|"travado"|"sem_sinal"|"erro"}
  GET /status/hardware      → {"status": "ok", "modelo": "...", "serial": "...", "firmware": "..."}
  GET /status/printer       → {"status": "online"|"sem_papel"|"sem_toner"|"fila_travada"|"erro"}
  GET /status/connectivity  → {"status": "ok", "uptime_s": 12345}

Timeout individual por verificação: SCAN_TIMEOUT_S (default 10s).
Porta do agente: AGENT_PORT (default 8765).
Verificações rodam em paralelo via ThreadPoolExecutor.
"""
from __future__ import annotations

import json
import logging
import os
import socket
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, wait as futures_wait, FIRST_EXCEPTION
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

TIMEOUT_PER_CHECK: int = int(os.environ.get("SCAN_TIMEOUT_S", "10"))
AGENT_PORT: int = int(os.environ.get("AGENT_PORT", "8765"))

# Statuses válidos por verificação (documentados para o agente)
STATUS_DISPLAY = ("ok", "travado", "sem_sinal", "erro", "offline", "timeout")
STATUS_HARDWARE = ("ok", "erro", "offline", "timeout")
STATUS_PRINTER = ("online", "sem_papel", "sem_toner", "fila_travada", "erro", "offline", "timeout")
STATUS_CONNECTIVITY = ("ok", "offline", "timeout", "erro")


@dataclass
class CheckResult:
    status: str
    payload: dict = field(default_factory=dict)
    erro: Optional[str] = None


@dataclass
class ScanResult:
    ip: str
    sucesso: bool
    display: CheckResult
    hardware: CheckResult
    impressora: CheckResult
    conectividade: CheckResult
    timestamp: str
    erro_geral: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "sucesso": self.sucesso,
            "timestamp": self.timestamp,
            "erro_geral": self.erro_geral,
            "display": {
                "status": self.display.status,
                "payload": self.display.payload,
                "erro": self.display.erro,
            },
            "hardware": {
                "status": self.hardware.status,
                "payload": self.hardware.payload,
                "erro": self.hardware.erro,
            },
            "impressora": {
                "status": self.impressora.status,
                "payload": self.impressora.payload,
                "erro": self.impressora.erro,
            },
            "conectividade": {
                "status": self.conectividade.status,
                "payload": self.conectividade.payload,
                "erro": self.conectividade.erro,
            },
        }

    def sugestao(self) -> dict:
        from .rules import aplicar_regras
        return aplicar_regras(self)


class EquipmentScanner:
    def __init__(
        self,
        timeout: int = TIMEOUT_PER_CHECK,
        port: int = AGENT_PORT,
    ) -> None:
        self.timeout = timeout
        self.port = port

    def scan(self, ip: str) -> ScanResult:
        """
        Executa as 4 verificações em paralelo.
        Falha em uma verificação não afeta as demais.
        Se o totem não responder à conexão TCP, retorna sucesso=False mas não lança exceção.
        """
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        checks = {
            "display": lambda: self._check_display(ip),
            "hardware": lambda: self._check_hardware(ip),
            "impressora": lambda: self._check_printer(ip),
            "conectividade": lambda: self._check_connectivity(ip),
        }

        results: dict[str, CheckResult] = {}
        _timeout_result = CheckResult(
            status="timeout", erro="verificação não completou no prazo"
        )

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_name = {executor.submit(fn): name for name, fn in checks.items()}
            done, not_done = futures_wait(
                future_to_name.keys(), timeout=self.timeout + 2
            )

            for future in done:
                name = future_to_name[future]
                try:
                    results[name] = future.result()
                except Exception as exc:
                    logger.warning("Verificação '%s' falhou para IP %s: %s", name, ip, exc)
                    results[name] = CheckResult(status="erro", erro=str(exc))

            for future in not_done:
                name = future_to_name[future]
                logger.warning(
                    "Verificação '%s' não completou no prazo para IP %s", name, ip
                )
                results[name] = _timeout_result
                future.cancel()

        conectividade = results.get("conectividade", _timeout_result)
        display = results.get("display", _timeout_result)
        hardware = results.get("hardware", _timeout_result)
        impressora = results.get("impressora", _timeout_result)

        sucesso = conectividade.status not in ("offline", "timeout", "erro")

        return ScanResult(
            ip=ip,
            sucesso=sucesso,
            display=display,
            hardware=hardware,
            impressora=impressora,
            conectividade=conectividade,
            timestamp=ts,
        )

    # ── verificações individuais ──────────────────────────────────────────────

    def _fetch_endpoint(self, ip: str, path: str) -> dict:
        url = f"http://{ip}:{self.port}{path}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return json.loads(resp.read().decode())

    def _check_connectivity(self, ip: str) -> CheckResult:
        try:
            t0 = time.monotonic()
            with socket.create_connection((ip, self.port), timeout=self.timeout):
                latencia_ms = round((time.monotonic() - t0) * 1000)

            try:
                data = self._fetch_endpoint(ip, "/status/connectivity")
                status = data.get("status", "ok")
                payload = {k: v for k, v in data.items() if k != "status"}
                payload["latencia_ms"] = latencia_ms
            except Exception:
                status, payload = "ok", {"latencia_ms": latencia_ms}

            return CheckResult(status=status, payload=payload)

        except socket.timeout:
            logger.warning("Totem %s: timeout na verificação de conectividade", ip)
            return CheckResult(
                status="timeout", erro=f"sem resposta após {self.timeout}s"
            )
        except OSError as exc:
            logger.warning("Totem %s: inacessível — %s", ip, exc)
            return CheckResult(status="offline", erro=str(exc))

    def _check_display(self, ip: str) -> CheckResult:
        return self._check_generic(ip, "/status/display", "display")

    def _check_hardware(self, ip: str) -> CheckResult:
        return self._check_generic(ip, "/status/hardware", "hardware")

    def _check_printer(self, ip: str) -> CheckResult:
        return self._check_generic(ip, "/status/printer", "impressora")

    def _check_generic(self, ip: str, path: str, nome: str) -> CheckResult:
        try:
            data = self._fetch_endpoint(ip, path)
            status = data.get("status", "ok")
            payload = {k: v for k, v in data.items() if k != "status"}
            return CheckResult(status=status, payload=payload)
        except urllib.error.URLError as exc:
            logger.warning("Totem %s: falha no check de %s — %s", ip, nome, exc.reason)
            return CheckResult(status="offline", erro=str(exc.reason))
        except Exception as exc:
            logger.warning(
                "Totem %s: erro inesperado no check de %s — %s", ip, nome, exc
            )
            return CheckResult(status="erro", erro=str(exc))
