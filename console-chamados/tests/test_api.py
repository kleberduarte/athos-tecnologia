"""
Testes de integração — cobertura completa das APIs do Console de Chamados.
Usa as fixtures flask_app / client do conftest.py existente.
Banco é o mesmo temporário compartilhado na sessão de testes.
"""
import json
import os
import sqlite3

import pytest
from werkzeug.security import generate_password_hash


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _db():
    return sqlite3.connect(os.environ["DB_PATH"])


def _seed_extra(conn):
    """Insere dados complementares necessários para os testes desta suite."""
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES (?,?,?,?,?)",
        ("Atendente CI", "atend@ci.test", generate_password_hash("senha123"), "atendente", 1),
    )
    conn.execute(
        "INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES (?,?,?,?,?)",
        ("Solicitante CI", "solic@ci.test", generate_password_hash("senha123"), "solicitante", 1),
    )
    conn.execute(
        "INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel, ativo) VALUES (?,?,?,?,?)",
        ("Pendente CI", "pendente2@ci.test", generate_password_hash("senha123"), "solicitante", 0),
    )
    conn.execute("INSERT OR IGNORE INTO setores (nome) VALUES ('TI-CI')")
    conn.execute(
        "INSERT OR IGNORE INTO equipamentos (nome, ip, modelo, serial, ativo, criado_em)"
        " VALUES ('Totem CI','192.168.99.1','Mx','SN-CI',1,datetime('now'))",
    )
    conn.execute(
        "INSERT OR IGNORE INTO clientes (nome, empresa, email, origem, criado_em)"
        " VALUES ('Cliente CI','Empresa CI','ci@test.com','Site',datetime('now'))",
    )
    conn.commit()


@pytest.fixture(autouse=True, scope="module")
def seed(flask_app):
    with _db() as conn:
        _seed_extra(conn)

        # Garante pelo menos 1 chamado
        conn.execute(
            "INSERT OR IGNORE INTO chamados"
            " (id, titulo, prioridade, status, sla_horas, criado_por, criado_em, atualizado_em)"
            " VALUES (900,'Chamado CI','media','aberto',24,1,datetime('now'),datetime('now'))"
        )
        # Garante pelo menos 1 incidente
        conn.execute(
            "INSERT OR IGNORE INTO incidentes"
            " (id, titulo, severidade, status, criado_por, inicio_em, criado_em, atualizado_em)"
            " VALUES (900,'Inc CI','P1','detectado',1,datetime('now'),datetime('now'),datetime('now'))"
        )
        # Garante pelo menos 1 oportunidade
        cli_id = conn.execute(
            "SELECT id FROM clientes WHERE email='ci@test.com'"
        ).fetchone()
        if cli_id:
            conn.execute(
                "INSERT OR IGNORE INTO oportunidades"
                " (id, cliente_id, titulo, valor_estimado, estagio, responsavel_id, criado_em, atualizado_em)"
                " VALUES (900,?,?,10000,'Prospeccao',1,datetime('now'),datetime('now'))",
                (cli_id[0], "Op CI"),
            )
        conn.commit()


def _set_session(client, papel="admin"):
    """Define sessão autenticada com o papel solicitado."""
    conn = _db()
    emails = {"admin": "admin@ci.test", "atendente": "atend@ci.test", "solicitante": "solic@ci.test"}
    row = conn.execute(
        "SELECT id, nome FROM usuarios WHERE email=?", (emails[papel],)
    ).fetchone()
    conn.close()
    with client.session_transaction() as sess:
        sess["usuario_id"] = row[0]
        sess["nome"] = row[1]
        sess["papel"] = papel


CSRF_H = {"X-CSRFToken": "pytest-bypass"}
JSON_H = {"Content-Type": "application/json", **CSRF_H}


@pytest.fixture(autouse=True)
def bypass_manual_csrf(monkeypatch):
    """Rotas @csrf.exempt fazem validate_csrf() manual, ignorando WTF_CSRF_ENABLED.
    Este fixture garante que a validação sempre passe durante os testes."""
    import flask_wtf.csrf
    monkeypatch.setattr(flask_wtf.csrf, "validate_csrf", lambda *a, **kw: None)


def _chamado_id():
    return _db().execute("SELECT id FROM chamados ORDER BY id LIMIT 1").fetchone()[0]


def _incidente_id():
    return _db().execute("SELECT id FROM incidentes ORDER BY id LIMIT 1").fetchone()[0]


def _cliente_id():
    return _db().execute("SELECT id FROM clientes ORDER BY id LIMIT 1").fetchone()[0]


def _op_id():
    return _db().execute("SELECT id FROM oportunidades ORDER BY id LIMIT 1").fetchone()[0]


def _equip_id():
    return _db().execute("SELECT id FROM equipamentos ORDER BY id LIMIT 1").fetchone()[0]


# ─────────────────────────────────────────────────────────────────────────────
# BOARD
# ─────────────────────────────────────────────────────────────────────────────

class TestBoard:
    def test_board_admin_200(self, client):
        _set_session(client, "admin")
        assert client.get("/").status_code == 200

    def test_board_atendente_200(self, client):
        _set_session(client, "atendente")
        assert client.get("/").status_code == 200

    def test_board_solicitante_200(self, client):
        _set_session(client, "solicitante")
        assert client.get("/").status_code == 200

    def test_board_sem_sessao_redireciona(self, client):
        r = client.get("/", follow_redirects=False)
        assert r.status_code == 302 and "/login" in r.headers["Location"]


# ─────────────────────────────────────────────────────────────────────────────
# CHAMADOS — CRUD
# ─────────────────────────────────────────────────────────────────────────────

class TestChamados:
    def test_criar_chamado_302(self, client):
        _set_session(client)
        r = client.post("/chamados",
                        data={"titulo": "API Test", "descricao": "D", "prioridade": "media"},
                        follow_redirects=False)
        assert r.status_code == 302

    def test_criar_chamado_titulo_vazio_flash(self, client):
        _set_session(client)
        r = client.post("/chamados", data={"titulo": "", "prioridade": "media"},
                        follow_redirects=True)
        assert r.status_code == 200

    def test_criar_chamado_solicitante_prioridade_forcada_baixa(self, client):
        _set_session(client, "solicitante")
        client.post("/chamados", data={"titulo": "Solic chama", "prioridade": "alta"},
                    follow_redirects=False)
        conn = _db()
        row = conn.execute(
            "SELECT prioridade FROM chamados WHERE titulo='Solic chama' LIMIT 1"
        ).fetchone()
        conn.close()
        assert row and row[0] == "baixa"

    def test_detalhe_chamado_200(self, client):
        _set_session(client)
        cid = _chamado_id()
        assert client.get(f"/chamados/{cid}").status_code == 200

    def test_detalhe_chamado_inexistente_redireciona(self, client):
        _set_session(client)
        r = client.get("/chamados/999999", follow_redirects=False)
        assert r.status_code == 302

    def test_solicitante_nao_acessa_chamado_alheio(self, client):
        _set_session(client, "solicitante")
        cid = _chamado_id()
        r = client.get(f"/chamados/{cid}", follow_redirects=False)
        assert r.status_code == 302

    def test_atualizar_status_ok(self, client):
        _set_session(client)
        cid = _chamado_id()
        r = client.post(f"/chamados/{cid}/status",
                        data=json.dumps({"status": "andamento"}), headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_atualizar_status_invalido_400(self, client):
        _set_session(client)
        cid = _chamado_id()
        r = client.post(f"/chamados/{cid}/status",
                        data=json.dumps({"status": "voando"}), headers=JSON_H)
        assert r.status_code == 400

    def test_atualizar_status_solicitante_403(self, client):
        _set_session(client, "solicitante")
        r = client.post("/chamados/900/status",
                        data=json.dumps({"status": "andamento"}), headers=JSON_H)
        assert r.status_code == 403

    def test_atualizar_status_chamado_inexistente_404(self, client):
        _set_session(client)
        r = client.post("/chamados/999999/status",
                        data=json.dumps({"status": "andamento"}), headers=JSON_H)
        assert r.status_code == 404

    def test_atribuir_chamado_ok(self, client):
        _set_session(client)
        uid = _db().execute("SELECT id FROM usuarios WHERE email='atend@ci.test'").fetchone()[0]
        r = client.post("/chamados/900/atribuir",
                        data=json.dumps({"usuario_id": uid}), headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_atribuir_chamado_solicitante_403(self, client):
        _set_session(client, "solicitante")
        r = client.post("/chamados/900/atribuir",
                        data=json.dumps({"usuario_id": 1}), headers=JSON_H)
        assert r.status_code == 403

    def test_atualizar_prioridade_ok(self, client):
        _set_session(client)
        r = client.post("/chamados/900/prioridade",
                        data=json.dumps({"prioridade": "alta"}), headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_atualizar_prioridade_invalida_400(self, client):
        _set_session(client)
        r = client.post("/chamados/900/prioridade",
                        data=json.dumps({"prioridade": "megaurgente"}), headers=JSON_H)
        assert r.status_code == 400

    def test_atualizar_prioridade_solicitante_403(self, client):
        _set_session(client, "solicitante")
        r = client.post("/chamados/900/prioridade",
                        data=json.dumps({"prioridade": "alta"}), headers=JSON_H)
        assert r.status_code == 403

    def test_adicionar_comentario_ok(self, client):
        _set_session(client)
        cid = _chamado_id()
        r = client.post(f"/chamados/{cid}/comentarios",
                        data={"texto": "Comentário via teste"},
                        follow_redirects=False)
        assert r.status_code == 302

    def test_comentario_vazio_flash(self, client):
        _set_session(client)
        cid = _chamado_id()
        r = client.post(f"/chamados/{cid}/comentarios",
                        data={"texto": ""},
                        follow_redirects=True)
        assert r.status_code == 200

    def test_exportar_csv_ok(self, client):
        _set_session(client)
        r = client.get("/chamados/exportar")
        assert r.status_code == 200
        assert r.content_type.startswith("text/csv")
        assert b"ID" in r.data

    def test_exportar_csv_solicitante_redireciona(self, client):
        _set_session(client, "solicitante")
        r = client.get("/chamados/exportar", follow_redirects=False)
        assert r.status_code == 302

    def test_excluir_chamado_admin_ok(self, client):
        _set_session(client)
        conn = _db()
        conn.execute(
            "INSERT INTO chamados (titulo, prioridade, status, sla_horas, criado_por, criado_em, atualizado_em)"
            " VALUES ('Del CI','media','aberto',24,1,datetime('now'),datetime('now'))"
        )
        conn.commit()
        cid = conn.execute("SELECT id FROM chamados ORDER BY id DESC LIMIT 1").fetchone()[0]
        conn.close()

        r = client.delete(f"/chamados/{cid}", headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_excluir_chamado_atendente_403(self, client):
        _set_session(client, "atendente")
        r = client.delete("/chamados/900", headers=JSON_H)
        assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# EQUIPAMENTOS
# ─────────────────────────────────────────────────────────────────────────────

class TestEquipamentos:
    def test_listar_json_200(self, client):
        _set_session(client)
        r = client.get("/api/equipamentos")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)

    def test_criar_api_ok(self, client):
        _set_session(client)
        r = client.post("/api/equipamentos",
                        data=json.dumps({"nome": "Totem API-CI", "ip": "10.1.1.1"}),
                        headers=JSON_H)
        assert r.status_code == 201 and r.get_json()["ok"] is True

    def test_criar_api_sem_ip_400(self, client):
        _set_session(client)
        r = client.post("/api/equipamentos",
                        data=json.dumps({"nome": "Sem IP"}), headers=JSON_H)
        assert r.status_code == 400

    def test_criar_api_nao_admin_403(self, client):
        _set_session(client, "atendente")
        r = client.post("/api/equipamentos",
                        data=json.dumps({"nome": "X", "ip": "1.1.1.2"}), headers=JSON_H)
        assert r.status_code == 403

    def test_pagina_equipamentos_admin_200(self, client):
        _set_session(client)
        assert client.get("/equipamentos").status_code == 200

    def test_pagina_equipamentos_nao_admin_redireciona(self, client):
        _set_session(client, "atendente")
        r = client.get("/equipamentos", follow_redirects=False)
        assert r.status_code in (302, 403)

    def test_criar_form_ok(self, client):
        _set_session(client)
        r = client.post("/equipamentos",
                        data={"nome": "Form CI", "ip": "10.2.2.2",
                              "modelo": "M2", "serial": "SN-F"},
                        follow_redirects=False)
        assert r.status_code == 302

    def test_toggle_equipamento_ok(self, client):
        _set_session(client)
        eid = _equip_id()
        r = client.post(f"/equipamentos/{eid}/toggle", headers=CSRF_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True


# ─────────────────────────────────────────────────────────────────────────────
# RELATÓRIOS
# ─────────────────────────────────────────────────────────────────────────────

class TestRelatorios:
    def test_admin_200(self, client):
        _set_session(client)
        assert client.get("/relatorios").status_code == 200

    def test_atendente_200(self, client):
        _set_session(client, "atendente")
        assert client.get("/relatorios").status_code == 200

    def test_solicitante_redireciona(self, client):
        _set_session(client, "solicitante")
        r = client.get("/relatorios", follow_redirects=False)
        assert r.status_code == 302


# ─────────────────────────────────────────────────────────────────────────────
# USUÁRIOS
# ─────────────────────────────────────────────────────────────────────────────

class TestUsuarios:
    def test_listar_admin_200(self, client):
        _set_session(client)
        assert client.get("/usuarios").status_code == 200

    def test_listar_nao_admin_bloqueado(self, client):
        _set_session(client, "atendente")
        r = client.get("/usuarios", follow_redirects=False)
        assert r.status_code in (302, 403)

    def test_criar_usuario_ok(self, client):
        _set_session(client)
        r = client.post("/usuarios", data={
            "nome": "Novo CI", "email": "novo_ci@test.com",
            "senha": "senha123", "papel": "atendente",
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_toggle_usuario_ok(self, client):
        _set_session(client)
        uid = _db().execute(
            "SELECT id FROM usuarios WHERE email='solic@ci.test'"
        ).fetchone()[0]
        r = client.post(f"/usuarios/{uid}/toggle", headers=CSRF_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_nao_pode_deletar_si_mesmo(self, client):
        _set_session(client)
        uid = _db().execute(
            "SELECT id FROM usuarios WHERE email='admin@ci.test'"
        ).fetchone()[0]
        r = client.delete(f"/usuarios/{uid}", headers=JSON_H)
        assert r.status_code == 400

    def test_excluir_usuario_ok(self, client):
        """Rota só permite excluir solicitantes pendentes (ativo=0)."""
        _set_session(client)
        conn = _db()
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, papel, ativo)"
            " VALUES ('Pendente Del','pendente_del@ci.test',?,'solicitante',0)",
            (generate_password_hash("s"),),
        )
        conn.commit()
        uid = conn.execute(
            "SELECT id FROM usuarios WHERE email='pendente_del@ci.test'"
        ).fetchone()[0]
        conn.close()

        r = client.delete(f"/usuarios/{uid}", headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True


# ─────────────────────────────────────────────────────────────────────────────
# INCIDENTES
# ─────────────────────────────────────────────────────────────────────────────

class TestIncidentes:
    def test_listar_200(self, client):
        _set_session(client)
        assert client.get("/incidentes").status_code == 200

    def test_listar_solicitante_redireciona(self, client):
        _set_session(client, "solicitante")
        r = client.get("/incidentes", follow_redirects=False)
        assert r.status_code == 302

    def test_criar_ok(self, client):
        _set_session(client)
        r = client.post("/incidentes", data={
            "titulo": "Inc API CI", "descricao": "Desc",
            "severidade": "P1", "servico_afetado": "API",
            "usuarios_impactados": "5", "metodo_deteccao": "Alerta",
            "inicio_em": "2026-07-29T10:00",
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_criar_titulo_vazio(self, client):
        _set_session(client)
        r = client.post("/incidentes", data={
            "titulo": "", "severidade": "P2",
            "inicio_em": "2026-07-29T10:00",
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_detalhe_200(self, client):
        _set_session(client)
        iid = _incidente_id()
        assert client.get(f"/incidentes/{iid}").status_code == 200

    def test_detalhe_inexistente_redireciona(self, client):
        _set_session(client)
        r = client.get("/incidentes/999999", follow_redirects=False)
        assert r.status_code == 302

    def test_atualizar_status_ok(self, client):
        _set_session(client)
        r = client.post("/incidentes/900/status",
                        data=json.dumps({"status": "reconhecido"}), headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_atualizar_status_invalido_400(self, client):
        _set_session(client)
        r = client.post("/incidentes/900/status",
                        data=json.dumps({"status": "voando"}), headers=JSON_H)
        assert r.status_code == 400

    def test_atualizar_severidade_ok(self, client):
        _set_session(client)
        r = client.post("/incidentes/900/severidade",
                        data=json.dumps({"severidade": "P0"}), headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_atualizar_severidade_invalida_400(self, client):
        _set_session(client)
        r = client.post("/incidentes/900/severidade",
                        data=json.dumps({"severidade": "P9"}), headers=JSON_H)
        assert r.status_code == 400

    def test_atribuir_ok(self, client):
        _set_session(client)
        uid = _db().execute(
            "SELECT id FROM usuarios WHERE email='atend@ci.test'"
        ).fetchone()[0]
        r = client.post("/incidentes/900/atribuir",
                        data=json.dumps({"usuario_id": uid}), headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_adicionar_evento_ok(self, client):
        _set_session(client)
        iid = _incidente_id()
        r = client.post(f"/incidentes/{iid}/eventos",
                        data={"texto": "Evento CI"},
                        follow_redirects=False)
        assert r.status_code == 302

    def test_excluir_admin_ok(self, client):
        _set_session(client)
        conn = _db()
        conn.execute(
            "INSERT INTO incidentes (titulo,severidade,status,criado_por,inicio_em,criado_em,atualizado_em)"
            " VALUES ('Del Inc CI','P2','detectado',1,datetime('now'),datetime('now'),datetime('now'))"
        )
        conn.commit()
        iid = conn.execute(
            "SELECT id FROM incidentes ORDER BY id DESC LIMIT 1"
        ).fetchone()[0]
        conn.close()

        r = client.delete(f"/incidentes/{iid}", headers=JSON_H)
        assert r.status_code == 200

    def test_excluir_nao_admin_403(self, client):
        _set_session(client, "atendente")
        r = client.delete("/incidentes/900", headers=JSON_H)
        assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# CRM — CLIENTES
# ─────────────────────────────────────────────────────────────────────────────

class TestCRMClientes:
    def test_listar_200(self, client):
        _set_session(client)
        assert client.get("/crm/clientes").status_code == 200

    def test_listar_solicitante_redireciona(self, client):
        _set_session(client, "solicitante")
        r = client.get("/crm/clientes", follow_redirects=False)
        assert r.status_code == 302

    def test_busca_por_nome(self, client):
        _set_session(client)
        r = client.get("/crm/clientes?q=CI")
        assert r.status_code == 200 and b"CI" in r.data

    def test_criar_ok(self, client):
        _set_session(client)
        r = client.post("/crm/clientes", data={
            "nome": "Criado CI", "empresa": "Emp CI",
            "telefone": "11999990001", "email": "criado@ci.com", "origem": "Evento",
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_criar_sem_nome_flash(self, client):
        _set_session(client)
        r = client.post("/crm/clientes", data={"nome": "", "empresa": "X"},
                        follow_redirects=True)
        assert r.status_code == 200

    def test_detalhe_200(self, client):
        _set_session(client)
        cid = _cliente_id()
        assert client.get(f"/crm/cliente/{cid}").status_code == 200

    def test_detalhe_inexistente_redireciona(self, client):
        _set_session(client)
        r = client.get("/crm/cliente/999999", follow_redirects=False)
        assert r.status_code == 302

    def test_adicionar_interacao_ok(self, client):
        _set_session(client)
        cid = _cliente_id()
        r = client.post(f"/crm/cliente/{cid}/interacao", data={
            "tipo": "reuniao", "descricao": "Reunião CI",
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_clientes_json(self, client):
        _set_session(client)
        r = client.get("/crm/_clientes_json")
        assert r.status_code == 200 and isinstance(r.get_json(), list)

    def test_usuarios_json(self, client):
        _set_session(client)
        r = client.get("/crm/_usuarios_json")
        assert r.status_code == 200 and isinstance(r.get_json(), list)


# ─────────────────────────────────────────────────────────────────────────────
# CRM — FUNIL / OPORTUNIDADES
# ─────────────────────────────────────────────────────────────────────────────

class TestCRMOportunidades:
    def test_funil_200(self, client):
        _set_session(client)
        assert client.get("/crm/funil").status_code == 200

    def test_funil_solicitante_redireciona(self, client):
        _set_session(client, "solicitante")
        r = client.get("/crm/funil", follow_redirects=False)
        assert r.status_code == 302

    def test_criar_oportunidade_ok(self, client):
        _set_session(client)
        cid = _cliente_id()
        r = client.post("/crm/oportunidades", data={
            "cliente_id": str(cid), "titulo": "Nova Op CI",
            "valor_estimado": "8000", "estagio": "Prospeccao", "responsavel_id": "1",
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_criar_oportunidade_sem_titulo(self, client):
        _set_session(client)
        cid = _cliente_id()
        r = client.post("/crm/oportunidades", data={
            "cliente_id": str(cid), "titulo": "",
            "valor_estimado": "0", "estagio": "Prospeccao",
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_detalhe_oportunidade_200(self, client):
        _set_session(client)
        oid = _op_id()
        assert client.get(f"/crm/oportunidade/{oid}").status_code == 200

    def test_detalhe_oportunidade_inexistente_redireciona(self, client):
        _set_session(client)
        r = client.get("/crm/oportunidade/999999", follow_redirects=False)
        assert r.status_code == 302

    def test_atualizar_estagio_ok(self, client):
        _set_session(client)
        r = client.post("/crm/oportunidade/900/estagio",
                        data=json.dumps({"estagio": "Qualificacao"}), headers=JSON_H)
        assert r.status_code == 200 and r.get_json()["ok"] is True

    def test_atualizar_estagio_invalido_400(self, client):
        _set_session(client)
        r = client.post("/crm/oportunidade/900/estagio",
                        data=json.dumps({"estagio": "NaoExiste"}), headers=JSON_H)
        assert r.status_code == 400

    def test_atualizar_estagio_inexistente_404(self, client):
        _set_session(client)
        r = client.post("/crm/oportunidade/999999/estagio",
                        data=json.dumps({"estagio": "Proposta"}), headers=JSON_H)
        assert r.status_code == 404

    def test_atualizar_estagio_solicitante_bloqueado(self, client):
        _set_session(client, "solicitante")
        r = client.post("/crm/oportunidade/900/estagio",
                        data=json.dumps({"estagio": "Proposta"}), headers=JSON_H)
        assert r.status_code in (302, 403)

    def test_editar_oportunidade_ok(self, client):
        _set_session(client)
        oid = _op_id()
        r = client.post(f"/crm/oportunidade/{oid}/editar", data={
            "titulo": "Op Editada CI", "valor_estimado": "20000",
            "estagio": "Proposta", "responsavel_id": "1",
        }, follow_redirects=False)
        assert r.status_code == 302

    def test_editar_persiste_no_banco(self, client):
        _set_session(client)
        oid = _op_id()
        client.post(f"/crm/oportunidade/{oid}/editar", data={
            "titulo": "Persistencia CI", "valor_estimado": "12345",
            "estagio": "Fechado", "responsavel_id": "1",
        }, follow_redirects=False)
        row = _db().execute(
            "SELECT titulo, estagio, valor_estimado FROM oportunidades WHERE id=?", (oid,)
        ).fetchone()
        assert row[0] == "Persistencia CI"
        assert row[1] == "Fechado"
        assert row[2] == 12345.0
