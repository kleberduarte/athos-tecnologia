"""Testes unitários do EquipmentScanner — todas as chamadas HTTP/rede são mockadas."""
import json
import socket
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from equipment_scan.scanner import CheckResult, EquipmentScanner, ScanResult


def _scanner():
    return EquipmentScanner(timeout=2, port=8765)


def _mock_socket_ok():
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=None)
    ctx.__exit__ = MagicMock(return_value=False)
    return ctx


# ── CheckResult ───────────────────────────────────────────────────────────────

class TestCheckResult:
    def test_defaults(self):
        r = CheckResult(status="ok")
        assert r.payload == {}
        assert r.erro is None

    def test_com_payload(self):
        r = CheckResult(status="sem_papel", payload={"fila": 3})
        assert r.payload["fila"] == 3


# ── ScanResult ────────────────────────────────────────────────────────────────

class TestScanResult:
    def _make(self, **kwargs):
        defaults = dict(
            ip="1.2.3.4", sucesso=True,
            display=CheckResult(status="ok"),
            hardware=CheckResult(status="ok"),
            impressora=CheckResult(status="online"),
            conectividade=CheckResult(status="ok"),
            timestamp="2024-01-01 12:00:00",
        )
        defaults.update(kwargs)
        return ScanResult(**defaults)

    def test_to_dict_serializavel(self):
        d = self._make().to_dict()
        assert json.dumps(d)
        assert d["ip"] == "1.2.3.4"
        assert "display" in d and "impressora" in d

    def test_sugestao_tudo_ok(self):
        sug = self._make().sugestao()
        assert sug["prioridade"] == "baixa"

    def test_sugestao_offline(self):
        sug = self._make(
            sucesso=False,
            conectividade=CheckResult(status="offline"),
        ).sugestao()
        assert sug["prioridade"] == "alta"

    def test_sugestao_sem_papel(self):
        sug = self._make(impressora=CheckResult(status="sem_papel")).sugestao()
        assert sug["prioridade"] == "alta"

    def test_sugestao_fila_travada(self):
        sug = self._make(impressora=CheckResult(status="fila_travada")).sugestao()
        assert sug["prioridade"] == "alta"

    def test_sugestao_display_sem_sinal(self):
        sug = self._make(display=CheckResult(status="sem_sinal")).sugestao()
        assert sug["prioridade"] == "alta"

    def test_sugestao_sem_toner(self):
        sug = self._make(impressora=CheckResult(status="sem_toner")).sugestao()
        assert sug["prioridade"] == "media"

    def test_sugestao_display_erro(self):
        sug = self._make(display=CheckResult(status="erro")).sugestao()
        assert sug["prioridade"] == "media"


# ── EquipmentScanner ──────────────────────────────────────────────────────────

class TestEquipmentScanner:
    def test_scan_totem_online(self):
        scanner = _scanner()

        def fake_fetch(ip, path):
            return {
                "/status/display":       {"status": "ok"},
                "/status/hardware":      {"status": "ok", "modelo": "iMin S1"},
                "/status/printer":       {"status": "online"},
                "/status/connectivity":  {"status": "ok", "uptime_s": 3600},
            }.get(path, {"status": "ok"})

        with patch.object(scanner, "_fetch_endpoint", side_effect=fake_fetch), \
             patch("socket.create_connection", return_value=_mock_socket_ok()):
            result = scanner.scan("192.168.1.10")

        assert result.sucesso is True
        assert result.ip == "192.168.1.10"
        assert result.display.status == "ok"
        assert result.impressora.status == "online"
        assert result.hardware.payload.get("modelo") == "iMin S1"

    def test_scan_totem_offline(self):
        scanner = _scanner()
        with patch("socket.create_connection", side_effect=OSError("connection refused")), \
             patch.object(scanner, "_fetch_endpoint", side_effect=OSError("connection refused")):
            result = scanner.scan("10.0.0.99")

        assert result.sucesso is False
        assert result.conectividade.status in ("offline", "timeout", "erro")

    def test_scan_totem_timeout(self):
        scanner = _scanner()
        with patch("socket.create_connection", side_effect=socket.timeout()), \
             patch.object(scanner, "_fetch_endpoint", side_effect=socket.timeout()):
            result = scanner.scan("10.0.0.88")

        assert result.sucesso is False
        assert result.conectividade.status in ("timeout", "offline", "erro")

    def test_falha_em_um_check_nao_afeta_outros(self):
        """Timeout no display não deve derrubar hardware e impressora."""
        scanner = _scanner()

        def fake_fetch(ip, path):
            if path == "/status/display":
                raise urllib.error.URLError("timeout")
            return {"status": "ok"} if "/hardware" in path else {"status": "online"}

        with patch.object(scanner, "_fetch_endpoint", side_effect=fake_fetch), \
             patch("socket.create_connection", return_value=_mock_socket_ok()):
            result = scanner.scan("192.168.1.10")

        assert result.display.status in ("offline", "erro", "timeout")
        assert result.hardware.status == "ok"
        assert result.impressora.status == "online"

    def test_impressora_sem_papel(self):
        scanner = _scanner()

        def fake_fetch(ip, path):
            if path == "/status/printer":
                return {"status": "sem_papel", "fila": 0}
            return {"status": "ok"}

        with patch.object(scanner, "_fetch_endpoint", side_effect=fake_fetch), \
             patch("socket.create_connection", return_value=_mock_socket_ok()):
            result = scanner.scan("192.168.1.10")

        assert result.impressora.status == "sem_papel"
        assert result.sucesso is True  # totem respondeu; só impressora com problema

    def test_resultado_preserva_payload(self):
        scanner = _scanner()

        def fake_fetch(ip, path):
            if path == "/status/hardware":
                return {"status": "ok", "modelo": "MEVAM V3", "serial": "SN007", "firmware": "2.1.0"}
            return {"status": "ok"}

        with patch.object(scanner, "_fetch_endpoint", side_effect=fake_fetch), \
             patch("socket.create_connection", return_value=_mock_socket_ok()):
            result = scanner.scan("192.168.1.20")

        assert result.hardware.payload["modelo"] == "MEVAM V3"
        assert result.hardware.payload["firmware"] == "2.1.0"

    def test_scan_result_to_dict_completo(self):
        scanner = _scanner()

        with patch.object(scanner, "_fetch_endpoint", return_value={"status": "ok"}), \
             patch("socket.create_connection", return_value=_mock_socket_ok()):
            result = scanner.scan("192.168.1.30")

        d = result.to_dict()
        assert all(k in d for k in ("ip", "sucesso", "timestamp", "display", "hardware",
                                    "impressora", "conectividade"))
        assert json.dumps(d)  # deve ser serializável
