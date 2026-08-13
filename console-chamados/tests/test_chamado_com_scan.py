"""Testes de integração: fluxo completo de abertura de chamado com scan de equipamento."""
import json
import os
import sqlite3
from unittest.mock import patch

import pytest

from equipment_scan.scanner import CheckResult, ScanResult


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_admin_id(db_path):
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM usuarios WHERE email = 'admin@ci.test'"
        ).fetchone()
    return row[0] if row else 1


def _set_session(client, usuario_id, nome, papel):
    """Define sessão diretamente — mais confiável em testes que o fluxo de login."""
    with client.session_transaction() as sess:
        sess["usuario_id"] = usuario_id
        sess["nome"] = nome
        sess["papel"] = papel


def _login_admin(client):
    uid = _get_admin_id(os.environ["DB_PATH"])
    _set_session(client, uid, "Admin CI", "admin")


def _criar_equipamento(db_path, nome="Totem-CI", ip="192.168.99.1"):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO equipamentos (nome, ip, criado_em) VALUES (?, ?, datetime('now'))",
            (nome, ip),
        )
        conn.commit()
        return conn.execute("SELECT last_insert_rowid() AS id").fetchone()[0]


def _scan_ok(ip="192.168.99.1"):
    return ScanResult(
        ip=ip, sucesso=True,
        display=CheckResult(status="ok"),
        hardware=CheckResult(status="ok", payload={"modelo": "iMin S1"}),
        impressora=CheckResult(status="online"),
        conectividade=CheckResult(status="ok", payload={"latencia_ms": 4}),
        timestamp="2024-01-01 12:00:00",
    )


def _scan_offline(ip="192.168.99.1"):
    return ScanResult(
        ip=ip, sucesso=False,
        display=CheckResult(status="offline"),
        hardware=CheckResult(status="offline"),
        impressora=CheckResult(status="offline"),
        conectividade=CheckResult(status="offline"),
        timestamp="2024-01-01 12:00:00",
    )


def _scan_sem_papel(ip="192.168.99.1"):
    return ScanResult(
        ip=ip, sucesso=True,
        display=CheckResult(status="ok"),
        hardware=CheckResult(status="ok"),
        impressora=CheckResult(status="sem_papel"),
        conectividade=CheckResult(status="ok"),
        timestamp="2024-01-01 12:00:00",
    )


# ── proteção de rotas ─────────────────────────────────────────────────────────

def test_api_scan_exige_login(client):
    r = client.post("/api/equipamentos/1/scan", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_api_listar_equipamentos_exige_login(client):
    r = client.get("/api/equipamentos", follow_redirects=False)
    assert r.status_code == 302


# ── scan ──────────────────────────────────────────────────────────────────────

def test_api_scan_equipamento_nao_encontrado(client):
    _login_admin(client)
    r = client.post("/api/equipamentos/9999/scan")
    assert r.status_code == 404
    assert "não encontrado" in r.get_json().get("erro", "")


def test_api_scan_totem_online(client):
    _login_admin(client)
    equip_id = _criar_equipamento(os.environ["DB_PATH"], nome="Totem-Online")

    from equipment_scan import scanner as scanner_mod
    with patch.object(scanner_mod.EquipmentScanner, "scan", return_value=_scan_ok()):
        r = client.post(f"/api/equipamentos/{equip_id}/scan")

    assert r.status_code == 200
    data = r.get_json()
    assert data["sucesso"] is True
    assert "scan_id" in data
    assert isinstance(data["scan_id"], int)
    assert data["sugestao"]["prioridade"] == "baixa"
    assert "detalhes" in data


def test_api_scan_totem_offline_retorna_200(client):
    """Totem offline não deve ser erro HTTP — é informação válida."""
    _login_admin(client)
    equip_id = _criar_equipamento(os.environ["DB_PATH"], nome="Totem-Offline")

    from equipment_scan import scanner as scanner_mod
    with patch.object(scanner_mod.EquipmentScanner, "scan", return_value=_scan_offline()):
        r = client.post(f"/api/equipamentos/{equip_id}/scan")

    assert r.status_code == 200
    data = r.get_json()
    assert data["sucesso"] is False
    assert data["sugestao"]["prioridade"] == "alta"
    assert "inacessível" in data["resumo"].lower()


def test_api_scan_sem_papel_sugere_alta(client):
    _login_admin(client)
    equip_id = _criar_equipamento(os.environ["DB_PATH"], nome="Totem-SemPapel")

    from equipment_scan import scanner as scanner_mod
    with patch.object(scanner_mod.EquipmentScanner, "scan", return_value=_scan_sem_papel()):
        r = client.post(f"/api/equipamentos/{equip_id}/scan")

    data = r.get_json()
    assert data["sugestao"]["prioridade"] == "alta"
    assert data["detalhes"]["impressora"] == "sem_papel"


# ── persistência ──────────────────────────────────────────────────────────────

def test_scan_persiste_no_banco(client):
    _login_admin(client)
    equip_id = _criar_equipamento(os.environ["DB_PATH"], nome="Totem-Persist")

    from equipment_scan import scanner as scanner_mod
    with patch.object(scanner_mod.EquipmentScanner, "scan", return_value=_scan_ok()):
        r = client.post(f"/api/equipamentos/{equip_id}/scan")

    scan_id = r.get_json()["scan_id"]

    with sqlite3.connect(os.environ["DB_PATH"]) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM equipment_scan_results WHERE id = ?", (scan_id,)
        ).fetchone()

    assert row is not None
    assert row["equipamento_id"] == equip_id
    assert row["sucesso"] == 1
    assert row["chamado_id"] is None
    assert row["status_impressora"] == "online"
    assert row["status_display"] == "ok"
    payload = json.loads(row["payload_bruto"])
    assert payload["ip"] is not None


def test_scan_offline_persiste_sucesso_zero(client):
    _login_admin(client)
    equip_id = _criar_equipamento(os.environ["DB_PATH"], nome="Totem-OffPersist")

    from equipment_scan import scanner as scanner_mod
    with patch.object(scanner_mod.EquipmentScanner, "scan", return_value=_scan_offline()):
        r = client.post(f"/api/equipamentos/{equip_id}/scan")

    scan_id = r.get_json()["scan_id"]

    with sqlite3.connect(os.environ["DB_PATH"]) as conn:
        row = conn.execute(
            "SELECT sucesso, status_conectividade FROM equipment_scan_results WHERE id = ?",
            (scan_id,),
        ).fetchone()

    assert row[0] == 0
    assert row[1] == "offline"


# ── fluxo de abertura de chamado ──────────────────────────────────────────────

def test_criar_chamado_com_equipamento_e_scan(client):
    """Scan vinculado ao chamado deve ter chamado_id preenchido."""
    _login_admin(client)
    equip_id = _criar_equipamento(os.environ["DB_PATH"], nome="Totem-ChamadoLink")

    from equipment_scan import scanner as scanner_mod
    with patch.object(scanner_mod.EquipmentScanner, "scan", return_value=_scan_ok()):
        scan_resp = client.post(f"/api/equipamentos/{equip_id}/scan")

    scan_id = scan_resp.get_json()["scan_id"]

    r = client.post(
        "/chamados",
        data={
            "titulo": "Totem com falha diagnosticada",
            "descricao": "Detectado via scan prévio",
            "prioridade": "alta",
            "equipamento_id": str(equip_id),
            "scan_result_id": str(scan_id),
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    with sqlite3.connect(os.environ["DB_PATH"]) as conn:
        conn.row_factory = sqlite3.Row
        scan_row = conn.execute(
            "SELECT chamado_id FROM equipment_scan_results WHERE id = ?", (scan_id,)
        ).fetchone()
        assert scan_row["chamado_id"] is not None

        chamado_row = conn.execute(
            "SELECT equipamento_id FROM chamados WHERE id = ?", (scan_row["chamado_id"],)
        ).fetchone()
        assert chamado_row["equipamento_id"] == equip_id


def test_criar_chamado_sem_scan_totem_offline(client):
    """Chamado deve ser criável mesmo sem scan (totem offline)."""
    _login_admin(client)
    equip_id = _criar_equipamento(os.environ["DB_PATH"], nome="Totem-SemScan")

    r = client.post(
        "/chamados",
        data={
            "titulo": "Totem sem resposta — offline",
            "descricao": "Não foi possível realizar scan",
            "prioridade": "alta",
            "equipamento_id": str(equip_id),
        },
        follow_redirects=False,
    )
    assert r.status_code == 302

    with sqlite3.connect(os.environ["DB_PATH"]) as conn:
        conn.row_factory = sqlite3.Row
        chamado = conn.execute(
            "SELECT * FROM chamados WHERE titulo = 'Totem sem resposta — offline'"
        ).fetchone()
    assert chamado is not None
    assert chamado["equipamento_id"] == equip_id


def test_criar_chamado_scan_result_id_invalido_nao_explode(client):
    """scan_result_id com valor inválido deve ser ignorado silenciosamente."""
    _login_admin(client)
    r = client.post(
        "/chamados",
        data={
            "titulo": "Chamado scan_id inválido",
            "scan_result_id": "nao-e-numero",
        },
        follow_redirects=False,
    )
    assert r.status_code == 302


# ── CRUD de equipamentos ──────────────────────────────────────────────────────

def test_criar_equipamento_admin(client):
    _login_admin(client)
    r = client.post(
        "/api/equipamentos",
        json={"nome": "Totem API Test", "ip": "10.0.1.50", "modelo": "TestModel"},
        content_type="application/json",
    )
    assert r.status_code == 201
    data = r.get_json()
    assert data["ok"] is True
    assert isinstance(data["id"], int)


def test_criar_equipamento_sem_nome_retorna_400(client):
    _login_admin(client)
    r = client.post(
        "/api/equipamentos",
        json={"ip": "10.0.1.51"},
        content_type="application/json",
    )
    assert r.status_code == 400


def test_criar_equipamento_sem_admin_retorna_403(client):
    """Atendente não pode criar equipamento."""
    db_path = os.environ["DB_PATH"]
    with sqlite3.connect(db_path) as conn:
        from werkzeug.security import generate_password_hash
        conn.execute(
            "INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel, ativo) "
            "VALUES (?,?,?,?,?)",
            ("Atendente CI", "atend@ci.test", generate_password_hash("s3nh4"), "atendente", 1),
        )
        conn.commit()
        uid = conn.execute(
            "SELECT id FROM usuarios WHERE email = 'atend@ci.test'"
        ).fetchone()[0]

    _set_session(client, uid, "Atendente CI", "atendente")
    r = client.post(
        "/api/equipamentos",
        json={"nome": "Totem X", "ip": "10.0.0.1"},
        content_type="application/json",
    )
    assert r.status_code == 403


def test_listar_equipamentos(client):
    _login_admin(client)
    _criar_equipamento(os.environ["DB_PATH"], nome="Totem-Lista")
    r = client.get("/api/equipamentos")
    assert r.status_code == 200
    data = r.get_json()
    assert isinstance(data, list)
    nomes = [e["nome"] for e in data]
    assert any("Totem-Lista" in n for n in nomes)
