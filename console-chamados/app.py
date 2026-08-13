"""
Console de Chamados — Athos Tecnologia
Backend Flask + SQLite puro (sem SQLAlchemy), sessão simples para login.
"""
import csv
import io
import json
import logging
import os
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

from flask import Flask, current_app, g, render_template, request, redirect, url_for, session, jsonify, Response, flash
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

DB_PATH = os.environ.get("DB_PATH", "console.db")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
EXTENSOES_PERMITIDAS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "doc", "docx", "xls", "xlsx"}
STATUS_VALIDOS = ("aberto", "andamento", "aguardando", "impedido", "resolvido", "cancelado")
STATUS_TERMINAIS = frozenset({"resolvido", "cancelado"})
CHAMADOS_POR_COLUNA = 50
TITULO_MAX = 200


def agora() -> str:
    """Retorna datetime local formatado para persistência. Evita datetime('now') do SQLite que é UTC."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(32)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1 hora

csrf = CSRFProtect(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=[],
)


# ---------- Banco de dados ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.execute("PRAGMA foreign_keys = ON")   # BUG-08 fix
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def migrate_db():
    """Cria/atualiza tabelas sem apagar dados existentes."""
    with sqlite3.connect(DB_PATH) as conn:
        # Migração 1: tabela comentarios
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comentarios (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL REFERENCES chamados(id),
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
                texto      TEXT NOT NULL,
                criado_em  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_comentarios_chamado ON comentarios(chamado_id)"
        )

        # Migração 2: adiciona coluna setor + papel solicitante
        cols = [row[1] for row in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
        if "setor" not in cols:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("""
                CREATE TABLE usuarios_v2 (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome        TEXT NOT NULL,
                    email       TEXT NOT NULL UNIQUE,
                    senha_hash  TEXT NOT NULL,
                    papel       TEXT NOT NULL CHECK (papel IN ('solicitante', 'atendente', 'admin')) DEFAULT 'atendente',
                    setor       TEXT,
                    ativo       INTEGER NOT NULL DEFAULT 1,
                    criado_em   TEXT NOT NULL DEFAULT (datetime('now','localtime'))
                )
            """)
            conn.execute("""
                INSERT INTO usuarios_v2 (id, nome, email, senha_hash, papel, ativo, criado_em)
                SELECT id, nome, email, senha_hash, papel, ativo, criado_em FROM usuarios
            """)
            conn.execute("DROP TABLE usuarios")
            conn.execute("ALTER TABLE usuarios_v2 RENAME TO usuarios")
            conn.execute("PRAGMA foreign_keys = ON")

        # Migração 3: expande CHECK de status em chamados
        create_sql = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='chamados'"
        ).fetchone()[0]
        if "'cancelado'" not in create_sql:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("""
                CREATE TABLE chamados_v2 (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    titulo        TEXT NOT NULL,
                    descricao     TEXT,
                    prioridade    TEXT NOT NULL CHECK (prioridade IN ('alta','media','baixa')) DEFAULT 'media',
                    status        TEXT NOT NULL CHECK (status IN ('aberto','andamento','aguardando','impedido','resolvido','cancelado')) DEFAULT 'aberto',
                    sla_horas     INTEGER NOT NULL DEFAULT 24,
                    setor_id      INTEGER REFERENCES setores(id),
                    atribuido_a   INTEGER REFERENCES usuarios(id),
                    criado_por    INTEGER REFERENCES usuarios(id),
                    criado_em     TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                    atualizado_em TEXT NOT NULL DEFAULT (datetime('now','localtime')),
                    resolvido_em  TEXT
                )
            """)
            conn.execute("INSERT INTO chamados_v2 SELECT * FROM chamados")
            conn.execute("DROP TABLE chamados")
            conn.execute("ALTER TABLE chamados_v2 RENAME TO chamados")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status)")
            conn.execute("PRAGMA foreign_keys = ON")

        # Migração 4: colunas de anexo nos comentários
        cols_com = [row[1] for row in conn.execute("PRAGMA table_info(comentarios)").fetchall()]
        if "anexo" not in cols_com:
            conn.execute("ALTER TABLE comentarios ADD COLUMN anexo TEXT")
        if "anexo_nome" not in cols_com:
            conn.execute("ALTER TABLE comentarios ADD COLUMN anexo_nome TEXT")

        # Migração 5: colunas de evidência nos chamados
        cols_cha = [row[1] for row in conn.execute("PRAGMA table_info(chamados)").fetchall()]
        if "anexo" not in cols_cha:
            conn.execute("ALTER TABLE chamados ADD COLUMN anexo TEXT")
        if "anexo_nome" not in cols_cha:
            conn.execute("ALTER TABLE chamados ADD COLUMN anexo_nome TEXT")

        # Migração 6: tabela de equipamentos/totens
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equipamentos (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                nome      TEXT NOT NULL,
                ip        TEXT NOT NULL,
                modelo    TEXT,
                serial    TEXT,
                setor_id  INTEGER REFERENCES setores(id),
                ativo     INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL
            )
        """)

        # Migração 7: resultado persistido de cada scan
        conn.execute("""
            CREATE TABLE IF NOT EXISTS equipment_scan_results (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id           INTEGER REFERENCES chamados(id),
                equipamento_id       INTEGER REFERENCES equipamentos(id),
                ip_consultado        TEXT NOT NULL,
                timestamp            TEXT NOT NULL,
                status_display       TEXT,
                status_hardware      TEXT,
                status_impressora    TEXT,
                status_conectividade TEXT,
                payload_bruto        TEXT,
                sucesso              INTEGER NOT NULL DEFAULT 0,
                erro                 TEXT
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_scan_chamado ON equipment_scan_results(chamado_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_scan_equipamento ON equipment_scan_results(equipamento_id)"
        )

        # Migração 8: liga chamado ao equipamento
        cols_cha2 = [row[1] for row in conn.execute("PRAGMA table_info(chamados)").fetchall()]
        if "equipamento_id" not in cols_cha2:
            conn.execute(
                "ALTER TABLE chamados ADD COLUMN equipamento_id INTEGER REFERENCES equipamentos(id)"
            )

        # Migração 9: quadro de incidentes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidentes (
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo              TEXT NOT NULL,
                descricao           TEXT,
                severidade          TEXT NOT NULL DEFAULT 'P2'
                                        CHECK (severidade IN ('P0','P1','P2')),
                status              TEXT NOT NULL DEFAULT 'detectado'
                                        CHECK (status IN ('detectado','reconhecido','mitigando','resolvido','postmortem')),
                servico_afetado     TEXT,
                usuarios_impactados INTEGER DEFAULT 0,
                metodo_deteccao     TEXT,
                atribuido_a         INTEGER REFERENCES usuarios(id),
                criado_por          INTEGER NOT NULL REFERENCES usuarios(id),
                inicio_em           TEXT NOT NULL,
                mitigado_em         TEXT,
                resolvido_em        TEXT,
                criado_em           TEXT NOT NULL,
                atualizado_em       TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS incidente_eventos (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                incidente_id INTEGER NOT NULL REFERENCES incidentes(id) ON DELETE CASCADE,
                tipo         TEXT NOT NULL CHECK (tipo IN ('status','comentario')),
                status_novo  TEXT,
                texto        TEXT,
                usuario_id   INTEGER REFERENCES usuarios(id),
                criado_em    TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_incidentes_status ON incidentes(status)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_inc_eventos_inc ON incidente_eventos(incidente_id)"
        )

        # Migração 10: módulo CRM
        conn.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                nome       TEXT NOT NULL,
                empresa    TEXT,
                telefone   TEXT,
                email      TEXT,
                origem     TEXT,
                criado_em  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS oportunidades (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id       INTEGER NOT NULL REFERENCES clientes(id),
                titulo           TEXT NOT NULL,
                valor_estimado   REAL,
                estagio          TEXT NOT NULL DEFAULT 'Prospeccao'
                                     CHECK (estagio IN ('Prospeccao','Qualificacao','Proposta','Fechado','Perdido')),
                responsavel_id   INTEGER REFERENCES usuarios(id),
                criado_em        TEXT NOT NULL,
                atualizado_em    TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS interacoes (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id       INTEGER NOT NULL REFERENCES clientes(id),
                oportunidade_id  INTEGER REFERENCES oportunidades(id),
                tipo             TEXT,
                descricao        TEXT,
                usuario_id       INTEGER REFERENCES usuarios(id),
                criado_em        TEXT NOT NULL
            )
        """)
        cols_crm = [row[1] for row in conn.execute("PRAGMA table_info(chamados)").fetchall()]
        if "cliente_id" not in cols_crm:
            conn.execute(
                "ALTER TABLE chamados ADD COLUMN cliente_id INTEGER REFERENCES clientes(id)"
            )

        conn.commit()

    os.makedirs(UPLOAD_DIR, exist_ok=True)


migrate_db()

app.jinja_env.filters["iniciais"] = lambda nome: (
    "?" if not nome else (
        nome.strip().split()[0][:2].upper() if len(nome.strip().split()) == 1
        else (nome.strip().split()[0][0] + nome.strip().split()[-1][0]).upper()
    )
)


# ---------- Auth ----------

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("usuario_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_globals():
    pendentes = 0
    if session.get("papel") == "admin":
        try:
            db = get_db()
            row = db.execute(
                "SELECT COUNT(*) AS n FROM usuarios WHERE ativo = 0 AND papel = 'solicitante'"
            ).fetchone()
            pendentes = row["n"]
        except Exception:
            pass
    return {"pendentes_count": pendentes}


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("papel") != "admin":
            return jsonify({"erro": "acesso restrito ao administrador"}), 403
        return view(*args, **kwargs)
    return wrapped


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"erro": "token CSRF inválido ou expirado"}), 400
    flash("Sessão expirada. Por favor, tente novamente.", "erro")
    return redirect(request.referrer or url_for("login"))


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])   # BUG-05 fix — rate limiting
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        db = get_db()
        usuario = db.execute(
            "SELECT * FROM usuarios WHERE email = ? AND ativo = 1", (email,)
        ).fetchone()
        if usuario and check_password_hash(usuario["senha_hash"], senha):
            session["usuario_id"] = usuario["id"]
            session["nome"] = usuario["nome"]
            session["papel"] = usuario["papel"]
            return redirect(url_for("board"))
        pendente = db.execute(
            "SELECT id FROM usuarios WHERE email = ? AND ativo = 0 AND papel = 'solicitante'", (email,)
        ).fetchone()
        if pendente:
            return render_template("login.html", erro="Seu cadastro ainda está aguardando aprovação do administrador.")
        return render_template("login.html", erro="E-mail ou senha inválidos.")
    return render_template("login.html", erro=None)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if session.get("usuario_id"):
        return redirect(url_for("board"))

    if request.method == "POST":
        nome  = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        conf  = request.form.get("confirmar_senha", "")
        setor = request.form.get("setor", "").strip()

        if not all([nome, email, senha, conf, setor]):
            return render_template("cadastro.html", erro="Preencha todos os campos.")
        if len(senha) < 6:
            return render_template("cadastro.html", erro="A senha deve ter ao menos 6 caracteres.")
        if senha != conf:
            return render_template("cadastro.html", erro="As senhas não coincidem.")

        db = get_db()
        try:
            db.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, papel, setor, ativo) VALUES (?, ?, ?, 'solicitante', ?, 0)",
                (nome, email, generate_password_hash(senha), setor),
            )
            db.commit()
        except sqlite3.IntegrityError:
            return render_template("cadastro.html", erro="Este e-mail já está cadastrado.")

        return render_template("cadastro.html", sucesso=True)

    return render_template("cadastro.html", erro=None)


# ---------- SLA helpers ----------

def calcular_sla(chamado):
    if chamado["status"] == "resolvido":
        return {"classe": "sla-ok", "percentual": 100, "rotulo": "Concluído", "detalhe": "dentro do SLA"}
    if chamado["status"] == "cancelado":
        return {"classe": "sla-cancel", "percentual": 0, "rotulo": "Cancelado", "detalhe": "—"}

    criado_em = datetime.strptime(chamado["criado_em"], "%Y-%m-%d %H:%M:%S")
    prazo = criado_em + timedelta(hours=chamado["sla_horas"])
    agora = datetime.now()

    total_segundos = (prazo - criado_em).total_seconds()
    decorrido_segundos = (agora - criado_em).total_seconds()
    percentual = max(0, min(100, round((decorrido_segundos / total_segundos) * 100)))

    restante = prazo - agora
    if restante.total_seconds() <= 0:
        classe = "sla-danger"
        horas_atraso = abs(restante) // timedelta(hours=1)
        detalhe = f"{int(horas_atraso)}h em atraso"
    elif percentual >= 75:
        classe = "sla-danger"
        h, rem = divmod(int(restante.total_seconds()), 3600)
        m = rem // 60
        detalhe = f"{h}h{m:02d} restantes"
    elif percentual >= 40:
        classe = "sla-warn"
        h, rem = divmod(int(restante.total_seconds()), 3600)
        m = rem // 60
        detalhe = f"{h}h{m:02d} restantes"
    else:
        classe = "sla-ok"
        h, rem = divmod(int(restante.total_seconds()), 3600)
        m = rem // 60
        detalhe = f"{h}h{m:02d} restantes"

    return {
        "classe": classe,
        "percentual": percentual,
        "rotulo": f"SLA {chamado['sla_horas']}h",
        "detalhe": detalhe,
    }


def tempo_relativo(data_str):
    momento = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
    delta = datetime.now() - momento
    total = delta.total_seconds()   # BUG-09 fix — usa total_seconds para lidar com delta negativo
    if total < 60:
        return "agora mesmo"
    if total < 3600:
        return f"há {max(1, int(total // 60))} min"
    if total < 86400:
        return f"há {int(total // 3600)}h"
    dias = int(total // 86400)
    return f"há {dias} dia{'s' if dias > 1 else ''}"


def iniciais(nome):
    if not nome:
        return "?"
    partes = nome.strip().split()
    if len(partes) == 1:
        return partes[0][:2].upper()
    return (partes[0][0] + partes[-1][0]).upper()


# ---------- Board (Kanban) ----------

@app.route("/")
@login_required
def board():
    db = get_db()
    papel = session.get("papel")
    uid   = session.get("usuario_id")

    if papel == "solicitante":
        chamados_raw = db.execute(
            """SELECT c.*, s.nome AS setor_nome, u.nome AS atribuido_nome
               FROM chamados c
               LEFT JOIN setores s ON s.id = c.setor_id
               LEFT JOIN usuarios u ON u.id = c.atribuido_a
               WHERE c.criado_por = ?
               ORDER BY c.criado_em DESC""",
            (uid,),
        ).fetchall()
    else:
        chamados_raw = db.execute(
            """SELECT c.*, s.nome AS setor_nome, u.nome AS atribuido_nome
               FROM chamados c
               LEFT JOIN setores s ON s.id = c.setor_id
               LEFT JOIN usuarios u ON u.id = c.atribuido_a
               ORDER BY c.criado_em DESC"""
        ).fetchall()

    colunas = {status: [] for status in STATUS_VALIDOS}
    for c in chamados_raw:
        item = dict(c)
        item["sla"] = calcular_sla(c)
        item["tempo_aberto"] = tempo_relativo(c["criado_em"])
        item["atribuido_iniciais"] = iniciais(item["atribuido_nome"]) if item["atribuido_nome"] else "—"
        colunas[c["status"]].append(item)

    # M06 — paginação por coluna
    colunas_overflow = {}
    for s in STATUS_VALIDOS:
        total = len(colunas[s])
        colunas_overflow[s] = max(0, total - CHAMADOS_POR_COLUNA)
        colunas[s] = colunas[s][:CHAMADOS_POR_COLUNA]

    ATIVOS = ("aberto", "andamento", "aguardando", "impedido")

    if papel == "solicitante":
        kpis = {
            "total": sum(len(colunas[s]) for s in STATUS_VALIDOS) + sum(colunas_overflow.values()),
            "abertos": len(colunas["aberto"]),
            "em_andamento": len(colunas["andamento"]),
            "resolvidos": len(colunas["resolvido"]),
        }
        pendentes_count = 0
    else:
        mttr_row = db.execute(
            """SELECT AVG((julianday(resolvido_em) - julianday(criado_em)) * 24) AS mttr
               FROM chamados
               WHERE status = 'resolvido' AND resolvido_em IS NOT NULL
               AND criado_em >= datetime('now', '-30 days')"""
        ).fetchone()
        mttr = round(mttr_row["mttr"] or 0, 1)

        sla_stats = db.execute(
            """SELECT COUNT(*) AS total,
                      COALESCE(SUM(
                        CASE WHEN (julianday(resolvido_em) - julianday(criado_em)) * 24 <= sla_horas
                        THEN 1 ELSE 0 END
                      ), 0) AS dentro
               FROM chamados
               WHERE status = 'resolvido' AND resolvido_em IS NOT NULL"""
        ).fetchone()
        taxa_sla = round(
            (sla_stats["dentro"] / sla_stats["total"] * 100) if sla_stats["total"] else 0
        )

        kpis = {
            "total_ativos": sum(len(colunas[s]) for s in ATIVOS),
            "em_andamento": len(colunas["andamento"]),
            "aguardando_setor": len(colunas["aguardando"]),
            "impedido": len(colunas["impedido"]),
            "mttr": mttr,
            "taxa_sla": taxa_sla,
        }

        pendentes_count = 0
        if papel == "admin":
            row = db.execute(
                "SELECT COUNT(*) AS n FROM usuarios WHERE ativo = 0 AND papel = 'solicitante'"
            ).fetchone()
            pendentes_count = row["n"]

    setores  = db.execute("SELECT * FROM setores ORDER BY nome").fetchall()
    usuarios = db.execute("SELECT * FROM usuarios WHERE ativo = 1 ORDER BY nome").fetchall()
    equipamentos = db.execute(
        "SELECT id, nome, ip FROM equipamentos WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    setor_hw = db.execute("SELECT id FROM setores WHERE nome = 'Hardware'").fetchone()
    setor_inf = db.execute("SELECT id FROM setores WHERE nome = 'Infra'").fetchone()
    setor_hardware_id = str(setor_hw["id"]) if setor_hw else ""
    setor_infra_id = str(setor_inf["id"]) if setor_inf else ""

    return render_template(
        "board.html",
        colunas=colunas,
        colunas_overflow=colunas_overflow,
        kpis=kpis,
        setores=setores,
        usuarios=usuarios,
        equipamentos=equipamentos,
        setor_hardware_id=setor_hardware_id,
        setor_infra_id=setor_infra_id,
        usuario_nome=session.get("nome"),
        usuario_papel=papel,
        usuario_iniciais=iniciais(session.get("nome", "?")),
        pendentes_count=pendentes_count,
    )


# ---------- Chamados ----------

@app.route("/chamados", methods=["POST"])
@login_required
def criar_chamado():
    titulo = request.form.get("titulo", "").strip()
    # BUG-11 / BUG-12 fix — validação de título no backend
    if not titulo:
        flash("O título do chamado não pode estar vazio.", "erro")
        return redirect(url_for("board"))
    if len(titulo) > TITULO_MAX:
        titulo = titulo[:TITULO_MAX]

    dados = request.form
    db = get_db()
    prioridade = dados.get("prioridade", "baixa")
    if session.get("papel") == "solicitante":
        prioridade = "baixa"
    setor_id = dados.get("setor_id") or None
    if setor_id and not db.execute("SELECT id FROM setores WHERE id = ?", (setor_id,)).fetchone():
        setor_id = None

    # Equipamento vinculado (scan de hardware)
    equipamento_id = dados.get("equipamento_id") or None
    if equipamento_id:
        if not db.execute(
            "SELECT id FROM equipamentos WHERE id = ? AND ativo = 1", (equipamento_id,)
        ).fetchone():
            equipamento_id = None

    # Evidência anexada ao abrir o chamado
    anexo_filename = None
    anexo_nome = None
    arquivo = request.files.get("arquivo")
    if arquivo and arquivo.filename:
        ext = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
        if ext in EXTENSOES_PERMITIDAS:
            nome_seguro = secure_filename(arquivo.filename)
            anexo_filename = f"{uuid.uuid4().hex}.{ext}"
            arquivo.save(os.path.join(UPLOAD_DIR, anexo_filename))
            anexo_nome = nome_seguro

    ts = agora()
    db.execute(
        """INSERT INTO chamados (titulo, descricao, prioridade, setor_id, sla_horas, criado_por,
                                 anexo, anexo_nome, equipamento_id, criado_em, atualizado_em)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            titulo,
            dados.get("descricao", ""),
            prioridade,
            setor_id,
            sla_padrao_por_prioridade(prioridade),
            session["usuario_id"],
            anexo_filename,
            anexo_nome,
            equipamento_id,
            ts,
            ts,
        ),
    )
    chamado_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    # Vincula o resultado do scan ao chamado recém-criado
    scan_result_id = dados.get("scan_result_id") or None
    if scan_result_id:
        try:
            db.execute(
                "UPDATE equipment_scan_results SET chamado_id = ? WHERE id = ? AND chamado_id IS NULL",
                (chamado_id, int(scan_result_id)),
            )
        except (ValueError, sqlite3.Error):
            pass

    db.execute(
        "INSERT INTO movimentacoes (chamado_id, status_anterior, status_novo, usuario_id, criado_em) VALUES (?, NULL, 'aberto', ?, ?)",
        (chamado_id, session["usuario_id"], ts),
    )
    db.commit()
    return redirect(url_for("board"))


def sla_padrao_por_prioridade(prioridade):
    return {"alta": 4, "media": 24, "baixa": 48}.get(prioridade, 24)


def _resumo_scan(result) -> str:
    if not result.sucesso:
        return "Totem inacessível — nenhuma resposta no prazo configurado"
    problemas = []
    if result.impressora.status not in ("online", "ok"):
        problemas.append(f"impressora: {result.impressora.status.replace('_', ' ')}")
    if result.display.status != "ok":
        problemas.append(f"display: {result.display.status.replace('_', ' ')}")
    if problemas:
        return "Problemas detectados: " + ", ".join(problemas)
    return "Diagnóstico concluído — nenhum problema encontrado"


# ---------- Equipamentos ----------

@app.route("/api/equipamentos")
@login_required
def api_listar_equipamentos():
    db = get_db()
    rows = db.execute(
        """SELECT e.id, e.nome, e.ip, e.modelo, e.serial, e.ativo,
                  s.nome AS setor_nome
           FROM equipamentos e
           LEFT JOIN setores s ON s.id = e.setor_id
           ORDER BY e.nome"""
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/equipamentos", methods=["POST"])
@login_required
def api_criar_equipamento():
    if session.get("papel") != "admin":
        return jsonify({"erro": "acesso restrito ao administrador"}), 403
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "body JSON inválido"}), 400
    nome = (dados.get("nome") or "").strip()
    ip   = (dados.get("ip") or "").strip()
    if not nome or not ip:
        return jsonify({"erro": "nome e ip são obrigatórios"}), 400
    db = get_db()
    db.execute(
        """INSERT INTO equipamentos (nome, ip, modelo, serial, setor_id, criado_em)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (nome, ip, dados.get("modelo"), dados.get("serial"),
         dados.get("setor_id") or None, agora()),
    )
    equip_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.commit()
    return jsonify({"ok": True, "id": equip_id}), 201


@app.route("/api/equipamentos/<int:equip_id>/scan", methods=["POST"])
@login_required
@csrf.exempt
def api_scan_equipamento(equip_id):
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.headers.get("X-CSRFToken", "")
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(token)
        except Exception:
            return jsonify({"erro": "token CSRF inválido"}), 400

    db = get_db()
    equip = db.execute(
        "SELECT * FROM equipamentos WHERE id = ? AND ativo = 1", (equip_id,)
    ).fetchone()
    if not equip:
        return jsonify({"erro": "equipamento não encontrado"}), 404

    from equipment_scan.scanner import EquipmentScanner
    result = EquipmentScanner().scan(equip["ip"])

    db.execute(
        """INSERT INTO equipment_scan_results
               (equipamento_id, ip_consultado, timestamp,
                status_display, status_hardware, status_impressora, status_conectividade,
                payload_bruto, sucesso, erro)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            equip_id,
            result.ip,
            result.timestamp,
            result.display.status,
            result.hardware.status,
            result.impressora.status,
            result.conectividade.status,
            json.dumps(result.to_dict()),
            1 if result.sucesso else 0,
            result.erro_geral,
        ),
    )
    scan_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.commit()

    sugestao = result.sugestao()
    logger.info(
        "Scan equipamento id=%s ip=%s sucesso=%s", equip_id, equip["ip"], result.sucesso
    )

    return jsonify({
        "scan_id": scan_id,
        "sucesso": result.sucesso,
        "resumo": _resumo_scan(result),
        "sugestao": sugestao,
        "detalhes": {
            "display": result.display.status,
            "hardware": result.hardware.status,
            "impressora": result.impressora.status,
            "conectividade": result.conectividade.status,
        },
    })


@app.route("/api/scan/ip", methods=["POST"])
@login_required
@csrf.exempt
def api_scan_por_ip():
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.headers.get("X-CSRFToken", "")
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(token)
        except Exception:
            return jsonify({"erro": "token CSRF inválido"}), 400

    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "body JSON inválido"}), 400

    import re as _re
    ip = (dados.get("ip") or "").strip()
    if not ip:
        return jsonify({"erro": "IP obrigatório"}), 400
    if not _re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip):
        return jsonify({"erro": "Formato de IP inválido"}), 400

    from equipment_scan.scanner import EquipmentScanner
    result = EquipmentScanner().scan(ip)

    db = get_db()
    equip = db.execute(
        "SELECT id FROM equipamentos WHERE ip = ? AND ativo = 1", (ip,)
    ).fetchone()
    equipamento_id = equip["id"] if equip else None

    db.execute(
        """INSERT INTO equipment_scan_results
               (equipamento_id, ip_consultado, timestamp,
                status_display, status_hardware, status_impressora, status_conectividade,
                payload_bruto, sucesso, erro)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            equipamento_id,
            result.ip,
            result.timestamp,
            result.display.status,
            result.hardware.status,
            result.impressora.status,
            result.conectividade.status,
            json.dumps(result.to_dict()),
            1 if result.sucesso else 0,
            result.erro_geral,
        ),
    )
    scan_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.commit()

    sugestao = result.sugestao()
    logger.info("Scan por IP ip=%s sucesso=%s", ip, result.sucesso)

    return jsonify({
        "scan_id": scan_id,
        "sucesso": result.sucesso,
        "resumo": _resumo_scan(result),
        "sugestao": sugestao,
        "detalhes": {
            "display":       {"status": result.display.status,       "payload": result.display.payload},
            "hardware":      {"status": result.hardware.status,      "payload": result.hardware.payload},
            "impressora":    {"status": result.impressora.status,    "payload": result.impressora.payload},
            "conectividade": {"status": result.conectividade.status, "payload": result.conectividade.payload},
        },
        "equipamento_id": equipamento_id,
    })


@app.route("/chamados/exportar")
@login_required
def exportar_csv():
    if session.get("papel") == "solicitante":
        return redirect(url_for("board"))
    db = get_db()
    chamados = db.execute(
        """SELECT c.id, c.titulo, c.descricao, c.prioridade, c.status, c.sla_horas,
                  s.nome AS setor, ua.nome AS atribuido_a, uc.nome AS criado_por,
                  c.criado_em, c.atualizado_em, c.resolvido_em
           FROM chamados c
           LEFT JOIN setores s ON s.id = c.setor_id
           LEFT JOIN usuarios ua ON ua.id = c.atribuido_a
           LEFT JOIN usuarios uc ON uc.id = c.criado_por
           ORDER BY c.criado_em DESC"""
    ).fetchall()

    saida = io.StringIO()
    writer = csv.writer(saida)
    writer.writerow([
        "ID", "Título", "Descrição", "Prioridade", "Status", "SLA (h)",
        "Setor", "Atribuído a", "Criado por", "Criado em", "Atualizado em", "Resolvido em",
    ])
    for c in chamados:
        writer.writerow([
            c["id"], c["titulo"], c["descricao"], c["prioridade"], c["status"], c["sla_horas"],
            c["setor"], c["atribuido_a"], c["criado_por"],
            c["criado_em"], c["atualizado_em"], c["resolvido_em"],
        ])

    saida.seek(0)
    return Response(
        saida.getvalue().encode("utf-8"),
        content_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=chamados.csv"},
    )


@app.route("/chamados/<int:chamado_id>")
@login_required
def detalhe_chamado(chamado_id):
    db = get_db()
    chamado = db.execute(
        """SELECT c.*, s.nome AS setor_nome,
                  ua.nome AS atribuido_nome,
                  uc.nome AS criado_por_nome,
                  us.setor AS solicitante_setor
           FROM chamados c
           LEFT JOIN setores s ON s.id = c.setor_id
           LEFT JOIN usuarios ua ON ua.id = c.atribuido_a
           LEFT JOIN usuarios uc ON uc.id = c.criado_por
           LEFT JOIN usuarios us ON us.id = c.criado_por
           WHERE c.id = ?""",
        (chamado_id,),
    ).fetchone()

    if chamado is None:
        return redirect(url_for("board"))

    if session.get("papel") == "solicitante" and chamado["criado_por"] != session["usuario_id"]:
        return redirect(url_for("board"))

    chamado = dict(chamado)
    chamado["sla"] = calcular_sla(chamado)
    chamado["tempo_aberto"] = tempo_relativo(chamado["criado_em"])

    movimentacoes = db.execute(
        """SELECT m.*, u.nome AS usuario_nome
           FROM movimentacoes m
           LEFT JOIN usuarios u ON u.id = m.usuario_id
           WHERE m.chamado_id = ?
           ORDER BY m.criado_em ASC""",
        (chamado_id,),
    ).fetchall()

    comentarios_raw = db.execute(
        """SELECT c.*, u.nome AS usuario_nome
           FROM comentarios c
           LEFT JOIN usuarios u ON u.id = c.usuario_id
           WHERE c.chamado_id = ?
           ORDER BY c.criado_em ASC""",
        (chamado_id,),
    ).fetchall()

    timeline = []
    for m in movimentacoes:
        ev = dict(m)
        ev["tipo"] = "movimentacao"
        ev["tempo"] = tempo_relativo(ev["criado_em"])
        timeline.append(ev)
    for c in comentarios_raw:
        ev = dict(c)
        ev["tipo"] = "comentario"
        ev["tempo"] = tempo_relativo(ev["criado_em"])
        timeline.append(ev)
    timeline.sort(key=lambda x: x["criado_em"])

    usuarios = db.execute(
        "SELECT id, nome FROM usuarios WHERE ativo = 1 AND papel IN ('atendente','admin') ORDER BY nome"
    ).fetchall()

    return render_template(
        "chamado_detalhe.html",
        chamado=chamado,
        timeline=timeline,
        usuarios=usuarios,
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
        usuario_id=session.get("usuario_id"),
    )


@app.route("/chamados/<int:chamado_id>/comentarios", methods=["POST"])
@login_required
def adicionar_comentario(chamado_id):
    db = get_db()
    chamado = db.execute("SELECT criado_por FROM chamados WHERE id = ?", (chamado_id,)).fetchone()
    if not chamado:
        return redirect(url_for("board"))

    # Solicitante só pode comentar no próprio chamado
    if session.get("papel") == "solicitante" and chamado["criado_por"] != session["usuario_id"]:
        flash("Sem permissão para comentar neste chamado.", "erro")
        return redirect(url_for("detalhe_chamado", chamado_id=chamado_id))

    texto = request.form.get("texto", "").strip()
    arquivo = request.files.get("arquivo")
    anexo_filename = None
    anexo_nome = None

    if arquivo and arquivo.filename:
        ext = arquivo.filename.rsplit(".", 1)[-1].lower() if "." in arquivo.filename else ""
        if ext in EXTENSOES_PERMITIDAS:
            nome_seguro = secure_filename(arquivo.filename)
            anexo_filename = f"{uuid.uuid4().hex}.{ext}"
            arquivo.save(os.path.join(UPLOAD_DIR, anexo_filename))
            anexo_nome = nome_seguro

    if texto or anexo_filename:
        db = get_db()
        db.execute(
            "INSERT INTO comentarios (chamado_id, usuario_id, texto, anexo, anexo_nome, criado_em) VALUES (?, ?, ?, ?, ?, ?)",
            (chamado_id, session["usuario_id"], texto, anexo_filename, anexo_nome, agora()),
        )
        db.commit()
    else:
        # BUG-13 fix — feedback para comentário vazio
        flash("O comentário não pode estar vazio.", "erro")

    return redirect(url_for("detalhe_chamado", chamado_id=chamado_id))


@app.route("/chamados/<int:chamado_id>/status", methods=["POST"])
@login_required
@csrf.exempt  # protegido via X-CSRFToken no JS
def atualizar_status(chamado_id):
    if session.get("papel") == "solicitante":
        return jsonify({"erro": "sem permissão"}), 403

    # BUG-07 fix — trata JSON malformado de forma consistente
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "body JSON inválido"}), 400

    novo_status = dados.get("status")
    if novo_status not in STATUS_VALIDOS:
        return jsonify({"erro": "status inválido"}), 400

    # Valida X-CSRFToken manualmente pois a rota é @csrf.exempt
    token = request.headers.get("X-CSRFToken", "")
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(token)
    except Exception:
        return jsonify({"erro": "token CSRF inválido"}), 400

    db = get_db()
    atual = db.execute("SELECT status FROM chamados WHERE id = ?", (chamado_id,)).fetchone()
    if atual is None:
        return jsonify({"erro": "chamado não encontrado"}), 404

    if atual["status"] == "cancelado":
        return jsonify({"erro": "chamado cancelado não pode ser reaberto"}), 400

    ts = agora()
    db.execute(
        """UPDATE chamados
           SET status = ?,
               atualizado_em = ?,
               resolvido_em = CASE WHEN ? = 'resolvido' THEN ? ELSE NULL END
           WHERE id = ?""",
        (novo_status, ts, novo_status, ts, chamado_id),
    )
    db.execute(
        """INSERT INTO movimentacoes (chamado_id, status_anterior, status_novo, usuario_id, criado_em)
           VALUES (?, ?, ?, ?, ?)""",
        (chamado_id, atual["status"], novo_status, session["usuario_id"], ts),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/chamados/<int:chamado_id>/atribuir", methods=["POST"])
@login_required
@csrf.exempt
def atribuir_chamado(chamado_id):
    if session.get("papel") == "solicitante":
        return jsonify({"erro": "sem permissão"}), 403

    token = request.headers.get("X-CSRFToken", "")
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(token)
    except Exception:
        return jsonify({"erro": "token CSRF inválido"}), 400

    dados = request.get_json(silent=True)
    if dados is None:
        return jsonify({"erro": "body JSON inválido"}), 400

    usuario_id = dados.get("usuario_id") or None
    db = get_db()
    db.execute(
        "UPDATE chamados SET atribuido_a = ?, atualizado_em = ? WHERE id = ?",
        (usuario_id, agora(), chamado_id),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/chamados/<int:chamado_id>/prioridade", methods=["POST"])
@login_required
@csrf.exempt
def atualizar_prioridade(chamado_id):
    if session.get("papel") == "solicitante":
        return jsonify({"erro": "sem permissão"}), 403

    token = request.headers.get("X-CSRFToken", "")
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(token)
    except Exception:
        return jsonify({"erro": "token CSRF inválido"}), 400

    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "body JSON inválido"}), 400

    nova_prioridade = dados.get("prioridade")
    if nova_prioridade not in ("alta", "media", "baixa"):
        return jsonify({"erro": "prioridade inválida"}), 400

    db = get_db()
    db.execute(
        "UPDATE chamados SET prioridade = ?, sla_horas = ?, atualizado_em = ? WHERE id = ?",
        (nova_prioridade, sla_padrao_por_prioridade(nova_prioridade), agora(), chamado_id),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/chamados/<int:chamado_id>", methods=["DELETE"])
@login_required
@admin_required
@csrf.exempt
def excluir_chamado(chamado_id):
    token = request.headers.get("X-CSRFToken", "")
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(token)
    except Exception:
        return jsonify({"erro": "token CSRF inválido"}), 400

    db = get_db()
    db.execute("DELETE FROM comentarios WHERE chamado_id = ?", (chamado_id,))
    db.execute("DELETE FROM movimentacoes WHERE chamado_id = ?", (chamado_id,))
    db.execute("DELETE FROM chamados WHERE id = ?", (chamado_id,))
    db.commit()
    return jsonify({"ok": True})


# ---------- Relatórios ----------

@app.route("/relatorios")
@login_required
def relatorios():
    if session.get("papel") == "solicitante":
        return redirect(url_for("board"))
    db = get_db()

    sumario = dict(db.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'resolvido' THEN 1 ELSE 0 END) AS resolvidos,
            SUM(CASE WHEN status != 'resolvido' THEN 1 ELSE 0 END) AS ativos,
            SUM(CASE WHEN prioridade = 'alta' AND status != 'resolvido' THEN 1 ELSE 0 END) AS alta_pendente
        FROM chamados
    """).fetchone())
    sumario["pct_resolvidos"] = round(
        (sumario["resolvidos"] / sumario["total"] * 100) if sumario["total"] else 0
    )

    mttr_row = db.execute(
        """SELECT ROUND(AVG((julianday(resolvido_em) - julianday(criado_em)) * 24), 1) AS mttr
           FROM chamados WHERE status = 'resolvido' AND resolvido_em IS NOT NULL"""
    ).fetchone()
    sumario["mttr"] = mttr_row["mttr"] or 0

    sla_row = db.execute(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(CASE WHEN (julianday(resolvido_em)-julianday(criado_em))*24 <= sla_horas
                               THEN 1 ELSE 0 END), 0) AS dentro
           FROM chamados WHERE status = 'resolvido' AND resolvido_em IS NOT NULL"""
    ).fetchone()
    sumario["taxa_sla"] = round(
        (sla_row["dentro"] / sla_row["total"] * 100) if sla_row["total"] else 0
    )

    status_rows = db.execute(
        "SELECT status, COUNT(*) AS n FROM chamados GROUP BY status"
    ).fetchall()
    status_map = {r["status"]: r["n"] for r in status_rows}
    chart_status = {
        "labels": ["Aberto", "Em andamento", "Aguardando", "Com impedimento", "Resolvido", "Cancelado"],
        "data": [status_map.get(s, 0) for s in ("aberto", "andamento", "aguardando", "impedido", "resolvido", "cancelado")],
        "colors": ["#5b8def", "#00ff88", "#b07de0", "#ff3366", "#00d4ff", "#6b7280"],
    }

    prio_rows = db.execute(
        "SELECT prioridade, COUNT(*) AS n FROM chamados GROUP BY prioridade"
    ).fetchall()
    prio_map = {r["prioridade"]: r["n"] for r in prio_rows}
    chart_prioridade = {
        "labels": ["Crítico", "Urgente", "Comum"],
        "data": [prio_map.get(p, 0) for p in ("alta", "media", "baixa")],
        "colors": ["rgba(255,51,102,0.85)", "rgba(245,158,11,0.8)", "rgba(0,255,136,0.8)"],
    }

    hoje = date.today()
    dias_date = [hoje - timedelta(days=i) for i in range(29, -1, -1)]
    dias_str = [d.strftime("%Y-%m-%d") for d in dias_date]

    abertos_rows = db.execute(
        """SELECT DATE(criado_em) AS dia, COUNT(*) AS n FROM chamados
           WHERE DATE(criado_em) >= ? GROUP BY DATE(criado_em)""",
        (dias_str[0],),
    ).fetchall()
    resolvidos_rows = db.execute(
        """SELECT DATE(resolvido_em) AS dia, COUNT(*) AS n FROM chamados
           WHERE resolvido_em IS NOT NULL AND DATE(resolvido_em) >= ?
           GROUP BY DATE(resolvido_em)""",
        (dias_str[0],),
    ).fetchall()
    abertos_map = {r["dia"]: r["n"] for r in abertos_rows}
    resolvidos_map = {r["dia"]: r["n"] for r in resolvidos_rows}
    chart_evolucao = {
        "labels": [d.strftime("%d/%m") for d in dias_date],
        "abertos": [abertos_map.get(d, 0) for d in dias_str],
        "resolvidos": [resolvidos_map.get(d, 0) for d in dias_str],
    }

    setor_rows = db.execute(
        """SELECT COALESCE(s.nome, 'Sem setor') AS setor, COUNT(*) AS n
           FROM chamados c LEFT JOIN setores s ON s.id = c.setor_id
           GROUP BY c.setor_id ORDER BY n DESC LIMIT 8"""
    ).fetchall()
    chart_setor = {
        "labels": [r["setor"] for r in setor_rows],
        "data": [r["n"] for r in setor_rows],
    }

    atendente_rows = db.execute(
        """SELECT COALESCE(u.nome, 'Não atribuído') AS nome,
                  SUM(CASE WHEN c.status != 'resolvido' THEN 1 ELSE 0 END) AS ativos,
                  SUM(CASE WHEN c.status = 'resolvido' THEN 1 ELSE 0 END) AS resolvidos_n
           FROM chamados c LEFT JOIN usuarios u ON u.id = c.atribuido_a
           GROUP BY c.atribuido_a ORDER BY ativos DESC"""
    ).fetchall()
    chart_atendente = {
        "labels": [r["nome"] for r in atendente_rows],
        "ativos": [r["ativos"] for r in atendente_rows],
        "resolvidos": [r["resolvidos_n"] for r in atendente_rows],
    }

    mttr_p_rows = db.execute(
        """SELECT prioridade,
                  ROUND(AVG((julianday(resolvido_em)-julianday(criado_em))*24), 1) AS mttr
           FROM chamados WHERE status = 'resolvido' AND resolvido_em IS NOT NULL
           GROUP BY prioridade"""
    ).fetchall()
    mttr_map = {r["prioridade"]: (r["mttr"] or 0) for r in mttr_p_rows}
    chart_mttr = {
        "labels": ["Crítico", "Urgente", "Comum"],
        "data": [mttr_map.get(p, 0) for p in ("alta", "media", "baixa")],
        "colors": ["rgba(255,51,102,0.85)", "rgba(245,158,11,0.8)", "rgba(0,255,136,0.8)"],
    }

    return render_template(
        "relatorios.html",
        sumario=sumario,
        chart_status=chart_status,
        chart_prioridade=chart_prioridade,
        chart_evolucao=chart_evolucao,
        chart_setor=chart_setor,
        chart_atendente=chart_atendente,
        chart_mttr=chart_mttr,
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
    )


# ---------- Usuários ----------

@app.route("/usuarios")
@login_required
def listar_usuarios():
    if session.get("papel") != "admin":
        return redirect(url_for("board"))
    db = get_db()

    pendentes_raw = db.execute(
        "SELECT * FROM usuarios WHERE ativo = 0 AND papel = 'solicitante' ORDER BY criado_em DESC"
    ).fetchall()
    pendentes = []
    for u in pendentes_raw:
        d = dict(u)
        d["iniciais_u"] = iniciais(u["nome"])
        pendentes.append(d)

    usuarios_raw = db.execute(
        """SELECT u.*, COUNT(c.id) AS chamados_ativos
           FROM usuarios u
           LEFT JOIN chamados c ON c.atribuido_a = u.id AND c.status != 'resolvido'
           WHERE NOT (u.ativo = 0 AND u.papel = 'solicitante')
           GROUP BY u.id
           ORDER BY u.ativo DESC, u.papel, u.nome"""
    ).fetchall()

    usuarios_lista = []
    for u in usuarios_raw:
        d = dict(u)
        d["iniciais_u"] = iniciais(u["nome"])
        usuarios_lista.append(d)

    return render_template(
        "usuarios.html",
        usuarios=usuarios_lista,
        pendentes=pendentes,
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
        usuario_id=session.get("usuario_id"),
    )


@app.route("/usuarios", methods=["POST"])
@login_required
def criar_usuario():
    if session.get("papel") != "admin":
        return jsonify({"erro": "acesso restrito"}), 403
    dados = request.form

    # BUG-02 fix — valida senha não vazia
    senha = dados.get("senha", "").strip()
    if not senha:
        flash("A senha não pode estar vazia.", "erro")
        return redirect(url_for("listar_usuarios"))

    db = get_db()
    try:
        db.execute(
            "INSERT INTO usuarios (nome, email, senha_hash, papel, setor) VALUES (?, ?, ?, ?, ?)",
            (
                dados["nome"].strip(),
                dados["email"].strip().lower(),
                generate_password_hash(senha),
                dados.get("papel", "atendente"),
                dados.get("setor", "").strip() or None,
            ),
        )
        db.commit()
    except sqlite3.IntegrityError:
        flash("Este e-mail já está cadastrado.", "erro")
    return redirect(url_for("listar_usuarios"))


@app.route("/usuarios/<int:usuario_id>/toggle", methods=["POST"])
@login_required
@csrf.exempt
def toggle_usuario(usuario_id):
    if session.get("papel") != "admin":
        return jsonify({"erro": "acesso restrito"}), 403
    if usuario_id == session["usuario_id"]:
        return jsonify({"erro": "não é possível desativar a própria conta"}), 400

    token = request.headers.get("X-CSRFToken", "")
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(token)
    except Exception:
        return jsonify({"erro": "token CSRF inválido"}), 400

    db = get_db()
    db.execute(
        "UPDATE usuarios SET ativo = CASE WHEN ativo = 1 THEN 0 ELSE 1 END WHERE id = ?",
        (usuario_id,),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
@login_required
@csrf.exempt
def excluir_usuario(usuario_id):
    if session.get("papel") != "admin":
        return jsonify({"erro": "acesso restrito"}), 403

    token = request.headers.get("X-CSRFToken", "")
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(token)
    except Exception:
        return jsonify({"erro": "token CSRF inválido"}), 400

    db = get_db()
    usuario = db.execute(
        "SELECT papel, ativo FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()
    if usuario is None:
        return jsonify({"erro": "usuário não encontrado"}), 404
    if not (usuario["papel"] == "solicitante" and usuario["ativo"] == 0):
        return jsonify({"erro": "só é possível remover solicitantes pendentes"}), 400
    db.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    db.commit()
    return jsonify({"ok": True})


@app.route("/usuarios/<int:usuario_id>/editar", methods=["POST"])
@login_required
def editar_usuario(usuario_id):
    if session.get("papel") != "admin":
        return jsonify({"erro": "acesso restrito"}), 403
    dados = request.form
    setor = dados.get("setor", "").strip() or None
    db = get_db()
    if dados.get("senha"):
        db.execute(
            "UPDATE usuarios SET nome = ?, papel = ?, senha_hash = ?, setor = ? WHERE id = ?",
            (dados["nome"].strip(), dados["papel"], generate_password_hash(dados["senha"]), setor, usuario_id),
        )
    else:
        db.execute(
            "UPDATE usuarios SET nome = ?, papel = ?, setor = ? WHERE id = ?",
            (dados["nome"].strip(), dados["papel"], setor, usuario_id),
        )
    db.commit()
    return redirect(url_for("listar_usuarios"))


# ---------- Equipamentos (página de gestão) ----------

@app.route("/equipamentos")
@login_required
@admin_required
def listar_equipamentos():
    db = get_db()
    equipamentos = db.execute(
        """SELECT e.id, e.nome, e.ip, e.modelo, e.serial, e.ativo, e.setor_id,
                  s.nome AS setor_nome
           FROM equipamentos e
           LEFT JOIN setores s ON s.id = e.setor_id
           ORDER BY e.ativo DESC, e.nome"""
    ).fetchall()
    setores = db.execute("SELECT * FROM setores ORDER BY nome").fetchall()
    return render_template(
        "equipamentos.html",
        equipamentos=equipamentos,
        setores=setores,
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
    )


@app.route("/equipamentos", methods=["POST"])
@login_required
@admin_required
def criar_equipamento():
    dados = request.form
    nome = (dados.get("nome") or "").strip()
    ip   = (dados.get("ip") or "").strip()
    if not nome or not ip:
        flash("Nome e IP são obrigatórios.", "erro")
        return redirect(url_for("listar_equipamentos"))
    db = get_db()
    try:
        db.execute(
            "INSERT INTO equipamentos (nome, ip, modelo, serial, setor_id, criado_em) VALUES (?, ?, ?, ?, ?, ?)",
            (nome, ip, dados.get("modelo") or None, dados.get("serial") or None,
             dados.get("setor_id") or None, agora()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        flash("Erro ao cadastrar equipamento.", "erro")
    return redirect(url_for("listar_equipamentos"))


@app.route("/equipamentos/<int:equip_id>/editar", methods=["POST"])
@login_required
@admin_required
def editar_equipamento(equip_id):
    dados = request.form
    nome = (dados.get("nome") or "").strip()
    ip   = (dados.get("ip") or "").strip()
    if not nome or not ip:
        flash("Nome e IP são obrigatórios.", "erro")
        return redirect(url_for("listar_equipamentos"))
    db = get_db()
    db.execute(
        "UPDATE equipamentos SET nome = ?, ip = ?, modelo = ?, serial = ?, setor_id = ? WHERE id = ?",
        (nome, ip, dados.get("modelo") or None, dados.get("serial") or None,
         dados.get("setor_id") or None, equip_id),
    )
    db.commit()
    return redirect(url_for("listar_equipamentos"))


@app.route("/equipamentos/<int:equip_id>/toggle", methods=["POST"])
@login_required
@admin_required
@csrf.exempt
def toggle_equipamento(equip_id):
    token = request.headers.get("X-CSRFToken", "")
    from flask_wtf.csrf import validate_csrf
    try:
        validate_csrf(token)
    except Exception:
        return jsonify({"erro": "token CSRF inválido"}), 400

    db = get_db()
    equip = db.execute("SELECT id FROM equipamentos WHERE id = ?", (equip_id,)).fetchone()
    if not equip:
        return jsonify({"erro": "equipamento não encontrado"}), 404
    db.execute(
        "UPDATE equipamentos SET ativo = CASE WHEN ativo = 1 THEN 0 ELSE 1 END WHERE id = ?",
        (equip_id,),
    )
    db.commit()
    return jsonify({"ok": True})


# ---------- Incidentes ----------

_STATUS_INC_ATIVOS = ("detectado", "reconhecido", "mitigando")
_STATUS_INC_LABELS = {
    "detectado":   "Detectado",
    "reconhecido": "Reconhecido",
    "mitigando":   "Mitigando",
    "resolvido":   "Resolvido",
    "postmortem":  "Pós-mortem",
}


def _inc_acesso():
    if session.get("papel") == "solicitante":
        return False
    return True


def _csrf_json_check():
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        token = request.headers.get("X-CSRFToken", "")
        from flask_wtf.csrf import validate_csrf
        try:
            validate_csrf(token)
        except Exception:
            return False
    return True


@app.route("/incidentes")
@login_required
def listar_incidentes():
    if not _inc_acesso():
        return redirect(url_for("board"))
    db = get_db()
    incidentes = db.execute(
        """SELECT i.*, u.nome AS atribuido_nome, uc.nome AS criado_por_nome
           FROM incidentes i
           LEFT JOIN usuarios u  ON u.id  = i.atribuido_a
           LEFT JOIN usuarios uc ON uc.id = i.criado_por
           ORDER BY CASE i.severidade WHEN 'P0' THEN 0 WHEN 'P1' THEN 1 ELSE 2 END,
                    i.criado_em DESC"""
    ).fetchall()

    total_ativos = sum(1 for i in incidentes if i["status"] in _STATUS_INC_ATIVOS)
    p0_ativos    = sum(1 for i in incidentes if i["severidade"] == "P0" and i["status"] in _STATUS_INC_ATIVOS)
    impactados   = sum((i["usuarios_impactados"] or 0) for i in incidentes if i["status"] in _STATUS_INC_ATIVOS)

    mttr = "—"
    rows_res = [i for i in incidentes if i["resolvido_em"] and i["inicio_em"]]
    if rows_res:
        total_s = 0
        count   = 0
        for r in rows_res:
            try:
                ini = datetime.strptime(r["inicio_em"],    "%Y-%m-%d %H:%M:%S")
                res = datetime.strptime(r["resolvido_em"], "%Y-%m-%d %H:%M:%S")
                total_s += (res - ini).total_seconds()
                count   += 1
            except Exception:
                pass
        if count:
            avg_min = total_s / count / 60
            mttr = f"{avg_min / 60:.1f}h" if avg_min >= 60 else f"{int(avg_min)}min"

    inc_lista = []
    for i in incidentes:
        d = dict(i)
        d["tempo_aberto"] = tempo_relativo(i["criado_em"])
        inc_lista.append(d)

    usuarios = db.execute("SELECT id, nome FROM usuarios WHERE ativo=1 ORDER BY nome").fetchall()
    return render_template(
        "incidentes.html",
        incidentes=inc_lista,
        kpis={"total_ativos": total_ativos, "p0_ativos": p0_ativos, "mttr": mttr, "impactados": impactados},
        status_labels=_STATUS_INC_LABELS,
        usuarios=usuarios,
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
    )


@app.route("/incidentes", methods=["POST"])
@login_required
def criar_incidente():
    if not _inc_acesso():
        return redirect(url_for("board"))

    titulo = request.form.get("titulo", "").strip()
    if not titulo:
        flash("Título obrigatório.", "erro")
        return redirect(url_for("listar_incidentes"))
    if len(titulo) > 200:
        titulo = titulo[:200]

    severidade = request.form.get("severidade", "P2")
    if severidade not in ("P0", "P1", "P2"):
        severidade = "P2"

    descricao  = request.form.get("descricao", "")
    servico    = request.form.get("servico_afetado", "").strip() or None
    metodo     = request.form.get("metodo_deteccao", "").strip() or None

    try:
        impactados = int(request.form.get("usuarios_impactados", 0) or 0)
    except (ValueError, TypeError):
        impactados = 0

    inicio_raw = request.form.get("inicio_em", "").strip()
    try:
        inicio = datetime.strptime(inicio_raw, "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        inicio = agora()

    ts = agora()
    db = get_db()
    db.execute(
        """INSERT INTO incidentes
               (titulo, descricao, severidade, status, servico_afetado, usuarios_impactados,
                metodo_deteccao, criado_por, inicio_em, criado_em, atualizado_em)
           VALUES (?,?,?,'detectado',?,?,?,?,?,?,?)""",
        (titulo, descricao, severidade, servico, impactados, metodo,
         session["usuario_id"], inicio, ts, ts),
    )
    inc_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    db.execute(
        "INSERT INTO incidente_eventos (incidente_id, tipo, status_novo, usuario_id, criado_em) VALUES (?,?,?,?,?)",
        (inc_id, "status", "detectado", session["usuario_id"], ts),
    )
    db.commit()
    return redirect(url_for("detalhe_incidente", incidente_id=inc_id))


@app.route("/incidentes/<int:incidente_id>")
@login_required
def detalhe_incidente(incidente_id):
    if not _inc_acesso():
        return redirect(url_for("board"))
    db = get_db()
    inc = db.execute(
        """SELECT i.*, u.nome AS atribuido_nome, uc.nome AS criado_por_nome
           FROM incidentes i
           LEFT JOIN usuarios u  ON u.id  = i.atribuido_a
           LEFT JOIN usuarios uc ON uc.id = i.criado_por
           WHERE i.id = ?""",
        (incidente_id,),
    ).fetchone()
    if not inc:
        flash("Incidente não encontrado.", "erro")
        return redirect(url_for("listar_incidentes"))

    eventos_raw = db.execute(
        """SELECT e.*, u.nome AS usuario_nome
           FROM incidente_eventos e
           LEFT JOIN usuarios u ON u.id = e.usuario_id
           WHERE e.incidente_id = ?
           ORDER BY e.criado_em ASC""",
        (incidente_id,),
    ).fetchall()

    eventos = []
    for e in eventos_raw:
        ev = dict(e)
        ev["tempo"] = tempo_relativo(e["criado_em"])
        eventos.append(ev)

    usuarios = db.execute("SELECT id, nome FROM usuarios WHERE ativo=1 ORDER BY nome").fetchall()
    return render_template(
        "incidente_detalhe.html",
        incidente=dict(inc),
        eventos=eventos,
        status_labels=_STATUS_INC_LABELS,
        usuarios=usuarios,
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
        session_user_id=session.get("usuario_id"),
    )


@app.route("/incidentes/<int:incidente_id>/status", methods=["POST"])
@login_required
@csrf.exempt
def atualizar_status_incidente(incidente_id):
    if not _inc_acesso():
        return jsonify({"erro": "acesso negado"}), 403
    if not _csrf_json_check():
        return jsonify({"erro": "token CSRF inválido"}), 400

    dados = request.get_json(silent=True) or {}
    novo  = dados.get("status", "")
    if novo not in _STATUS_INC_LABELS:
        return jsonify({"erro": "status inválido"}), 400

    db  = get_db()
    inc = db.execute("SELECT status, mitigado_em FROM incidentes WHERE id=?", (incidente_id,)).fetchone()
    if not inc:
        return jsonify({"erro": "incidente não encontrado"}), 404

    ts = agora()
    if novo == "mitigando" and not inc["mitigado_em"]:
        db.execute(
            "UPDATE incidentes SET status=?, atualizado_em=?, mitigado_em=? WHERE id=?",
            (novo, ts, ts, incidente_id),
        )
    elif novo == "resolvido":
        db.execute(
            "UPDATE incidentes SET status=?, atualizado_em=?, resolvido_em=? WHERE id=?",
            (novo, ts, ts, incidente_id),
        )
    else:
        db.execute(
            "UPDATE incidentes SET status=?, atualizado_em=? WHERE id=?",
            (novo, ts, incidente_id),
        )
    db.execute(
        "INSERT INTO incidente_eventos (incidente_id, tipo, status_novo, usuario_id, criado_em) VALUES (?,?,?,?,?)",
        (incidente_id, "status", novo, session["usuario_id"], ts),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/incidentes/<int:incidente_id>/severidade", methods=["POST"])
@login_required
@csrf.exempt
def atualizar_severidade_incidente(incidente_id):
    if not _inc_acesso():
        return jsonify({"erro": "acesso negado"}), 403
    if not _csrf_json_check():
        return jsonify({"erro": "token CSRF inválido"}), 400

    dados = request.get_json(silent=True) or {}
    nova  = dados.get("severidade", "")
    if nova not in ("P0", "P1", "P2"):
        return jsonify({"erro": "severidade inválida"}), 400

    db = get_db()
    if not db.execute("SELECT id FROM incidentes WHERE id=?", (incidente_id,)).fetchone():
        return jsonify({"erro": "incidente não encontrado"}), 404

    ts = agora()
    db.execute(
        "UPDATE incidentes SET severidade=?, atualizado_em=? WHERE id=?",
        (nova, ts, incidente_id),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/incidentes/<int:incidente_id>/atribuir", methods=["POST"])
@login_required
@csrf.exempt
def atribuir_incidente(incidente_id):
    if not _inc_acesso():
        return jsonify({"erro": "acesso negado"}), 403
    if not _csrf_json_check():
        return jsonify({"erro": "token CSRF inválido"}), 400

    dados   = request.get_json(silent=True) or {}
    user_id = dados.get("usuario_id")
    if user_id is not None:
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = None

    db = get_db()
    if not db.execute("SELECT id FROM incidentes WHERE id=?", (incidente_id,)).fetchone():
        return jsonify({"erro": "incidente não encontrado"}), 404

    db.execute(
        "UPDATE incidentes SET atribuido_a=?, atualizado_em=? WHERE id=?",
        (user_id, agora(), incidente_id),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/incidentes/<int:incidente_id>/eventos", methods=["POST"])
@login_required
def adicionar_evento_incidente(incidente_id):
    if not _inc_acesso():
        return redirect(url_for("board"))
    db = get_db()
    if not db.execute("SELECT id FROM incidentes WHERE id=?", (incidente_id,)).fetchone():
        flash("Incidente não encontrado.", "erro")
        return redirect(url_for("listar_incidentes"))

    texto = request.form.get("texto", "").strip()
    if not texto:
        return redirect(url_for("detalhe_incidente", incidente_id=incidente_id))

    ts = agora()
    db.execute(
        "INSERT INTO incidente_eventos (incidente_id, tipo, texto, usuario_id, criado_em) VALUES (?,?,?,?,?)",
        (incidente_id, "comentario", texto, session["usuario_id"], ts),
    )
    db.execute("UPDATE incidentes SET atualizado_em=? WHERE id=?", (ts, incidente_id))
    db.commit()
    return redirect(url_for("detalhe_incidente", incidente_id=incidente_id))


@app.route("/incidentes/<int:incidente_id>", methods=["DELETE"])
@login_required
@csrf.exempt
def excluir_incidente(incidente_id):
    if session.get("papel") != "admin":
        return jsonify({"erro": "acesso restrito ao administrador"}), 403
    if not _csrf_json_check():
        return jsonify({"erro": "token CSRF inválido"}), 400

    db = get_db()
    db.execute("DELETE FROM incidente_eventos WHERE incidente_id=?", (incidente_id,))
    db.execute("DELETE FROM incidentes WHERE id=?", (incidente_id,))
    db.commit()
    return jsonify({"ok": True})


# ---------- CRM ----------

_ESTAGIOS_CRM = ("Prospeccao", "Qualificacao", "Proposta", "Fechado", "Perdido")


def _crm_acesso():
    if session.get("papel") == "solicitante":
        flash("Acesso restrito.", "erro")
        return False
    return True


def _crm_pendentes():
    pendentes_count = 0
    if session.get("papel") == "admin":
        row = get_db().execute(
            "SELECT COUNT(*) AS n FROM usuarios WHERE ativo = 0 AND papel = 'solicitante'"
        ).fetchone()
        pendentes_count = row["n"]
    return pendentes_count


@app.route("/crm/_clientes_json")
@login_required
def crm_clientes_json():
    if not _crm_acesso():
        return jsonify([])
    db = get_db()
    rows = db.execute("SELECT id, nome, empresa FROM clientes ORDER BY nome").fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/crm/_usuarios_json")
@login_required
def crm_usuarios_json():
    if not _crm_acesso():
        return jsonify([])
    db = get_db()
    rows = db.execute(
        "SELECT id, nome FROM usuarios WHERE ativo = 1 ORDER BY nome"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/crm/clientes")
@login_required
def crm_clientes():
    if not _crm_acesso():
        return redirect(url_for("board"))
    db = get_db()
    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        clientes = db.execute(
            """SELECT cl.*,
                      COUNT(DISTINCT op.id) AS total_oportunidades,
                      COUNT(DISTINCT ch.id) AS total_chamados
               FROM clientes cl
               LEFT JOIN oportunidades op ON op.cliente_id = cl.id
                   AND op.estagio NOT IN ('Fechado','Perdido')
               LEFT JOIN chamados ch ON ch.cliente_id = cl.id
               WHERE cl.nome LIKE ? OR cl.empresa LIKE ?
               GROUP BY cl.id
               ORDER BY cl.criado_em DESC""",
            (like, like),
        ).fetchall()
    else:
        clientes = db.execute(
            """SELECT cl.*,
                      COUNT(DISTINCT op.id) AS total_oportunidades,
                      COUNT(DISTINCT ch.id) AS total_chamados
               FROM clientes cl
               LEFT JOIN oportunidades op ON op.cliente_id = cl.id
                   AND op.estagio NOT IN ('Fechado','Perdido')
               LEFT JOIN chamados ch ON ch.cliente_id = cl.id
               GROUP BY cl.id
               ORDER BY cl.criado_em DESC"""
        ).fetchall()
    return render_template(
        "crm_clientes.html",
        clientes=clientes,
        q=q,
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
        pendentes_count=_crm_pendentes(),
    )


@app.route("/crm/clientes", methods=["POST"])
@login_required
def crm_criar_cliente():
    if not _crm_acesso():
        return redirect(url_for("board"))
    nome = request.form.get("nome", "").strip()
    if not nome:
        flash("Nome é obrigatório.", "erro")
        return redirect(url_for("crm_clientes"))
    db = get_db()
    db.execute(
        """INSERT INTO clientes (nome, empresa, telefone, email, origem, criado_em)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            nome,
            request.form.get("empresa", "").strip() or None,
            request.form.get("telefone", "").strip() or None,
            request.form.get("email", "").strip() or None,
            request.form.get("origem", "").strip() or None,
            agora(),
        ),
    )
    db.commit()
    return redirect(url_for("crm_clientes"))


@app.route("/crm/cliente/<int:cliente_id>")
@login_required
def crm_cliente_detalhe(cliente_id):
    if not _crm_acesso():
        return redirect(url_for("board"))
    db = get_db()
    cliente = db.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,)).fetchone()
    if not cliente:
        flash("Cliente não encontrado.", "erro")
        return redirect(url_for("crm_clientes"))

    oportunidades = db.execute(
        """SELECT op.*, u.nome AS responsavel_nome
           FROM oportunidades op
           LEFT JOIN usuarios u ON u.id = op.responsavel_id
           WHERE op.cliente_id = ?
           ORDER BY op.criado_em DESC""",
        (cliente_id,),
    ).fetchall()

    timeline_raw = db.execute(
        """SELECT 'interacao' AS tipo, id, descricao AS texto, tipo AS subtipo,
                  criado_em, usuario_id, NULL AS status, NULL AS titulo
           FROM interacoes WHERE cliente_id = ?
           UNION ALL
           SELECT 'chamado' AS tipo, id, descricao AS texto, NULL AS subtipo,
                  criado_em, criado_por AS usuario_id, status, titulo
           FROM chamados WHERE cliente_id = ?
           ORDER BY criado_em DESC""",
        (cliente_id, cliente_id),
    ).fetchall()

    usuarios_map = {
        u["id"]: u["nome"]
        for u in db.execute("SELECT id, nome FROM usuarios WHERE ativo = 1").fetchall()
    }

    timeline = []
    for item in timeline_raw:
        ev = dict(item)
        ev["usuario_nome"] = usuarios_map.get(ev["usuario_id"], "—")
        ev["tempo"] = tempo_relativo(ev["criado_em"])
        timeline.append(ev)

    usuarios = db.execute("SELECT id, nome FROM usuarios WHERE ativo = 1 ORDER BY nome").fetchall()

    return render_template(
        "crm_cliente_detalhe.html",
        cliente=dict(cliente),
        oportunidades=oportunidades,
        timeline=timeline,
        usuarios=usuarios,
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
        pendentes_count=_crm_pendentes(),
    )


@app.route("/crm/cliente/<int:cliente_id>/interacao", methods=["POST"])
@login_required
def crm_adicionar_interacao(cliente_id):
    if not _crm_acesso():
        return redirect(url_for("board"))
    db = get_db()
    if not db.execute("SELECT id FROM clientes WHERE id = ?", (cliente_id,)).fetchone():
        flash("Cliente não encontrado.", "erro")
        return redirect(url_for("crm_clientes"))

    tipo = request.form.get("tipo", "").strip() or None
    descricao = request.form.get("descricao", "").strip()
    oportunidade_id = request.form.get("oportunidade_id") or None
    if oportunidade_id:
        try:
            oportunidade_id = int(oportunidade_id)
        except (ValueError, TypeError):
            oportunidade_id = None

    if descricao:
        db.execute(
            """INSERT INTO interacoes (cliente_id, oportunidade_id, tipo, descricao, usuario_id, criado_em)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (cliente_id, oportunidade_id, tipo, descricao, session["usuario_id"], agora()),
        )
        db.commit()
    return redirect(url_for("crm_cliente_detalhe", cliente_id=cliente_id))


@app.route("/crm/funil")
@login_required
def crm_funil():
    if not _crm_acesso():
        return redirect(url_for("board"))
    db = get_db()
    oportunidades_raw = db.execute(
        """SELECT op.*, cl.nome AS cliente_nome, u.nome AS responsavel_nome
           FROM oportunidades op
           JOIN clientes cl ON cl.id = op.cliente_id
           LEFT JOIN usuarios u ON u.id = op.responsavel_id
           ORDER BY op.criado_em DESC"""
    ).fetchall()

    colunas = {e: [] for e in _ESTAGIOS_CRM}
    for op in oportunidades_raw:
        estagio = op["estagio"]
        if estagio in colunas:
            colunas[estagio].append(dict(op))

    return render_template(
        "crm_funil.html",
        colunas=colunas,
        estagios=list(_ESTAGIOS_CRM),
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
        pendentes_count=_crm_pendentes(),
    )


@app.route("/crm/oportunidades", methods=["POST"])
@login_required
def crm_criar_oportunidade():
    if not _crm_acesso():
        return redirect(url_for("board"))
    titulo = request.form.get("titulo", "").strip()
    cliente_id = request.form.get("cliente_id") or None
    if not titulo or not cliente_id:
        flash("Título e cliente são obrigatórios.", "erro")
        return redirect(url_for("crm_funil"))

    try:
        valor = float(request.form.get("valor_estimado") or 0) or None
    except (ValueError, TypeError):
        valor = None

    estagio = request.form.get("estagio", "Prospeccao")
    if estagio not in _ESTAGIOS_CRM:
        estagio = "Prospeccao"

    responsavel_id = request.form.get("responsavel_id") or None

    ts = agora()
    db = get_db()
    db.execute(
        """INSERT INTO oportunidades (cliente_id, titulo, valor_estimado, estagio, responsavel_id, criado_em, atualizado_em)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (cliente_id, titulo, valor, estagio, responsavel_id, ts, ts),
    )
    db.commit()
    return redirect(url_for("crm_funil"))


@app.route("/crm/oportunidade/<int:op_id>")
@login_required
def crm_oportunidade_detalhe(op_id):
    if not _crm_acesso():
        return redirect(url_for("board"))
    db = get_db()
    op = db.execute(
        """SELECT op.*, cl.nome AS cliente_nome, u.nome AS responsavel_nome
           FROM oportunidades op
           JOIN clientes cl ON cl.id = op.cliente_id
           LEFT JOIN usuarios u ON u.id = op.responsavel_id
           WHERE op.id = ?""",
        (op_id,),
    ).fetchone()
    if not op:
        flash("Oportunidade não encontrada.", "erro")
        return redirect(url_for("crm_funil"))

    interacoes_raw = db.execute(
        """SELECT i.*, u.nome AS usuario_nome
           FROM interacoes i
           LEFT JOIN usuarios u ON u.id = i.usuario_id
           WHERE i.oportunidade_id = ?
           ORDER BY i.criado_em DESC""",
        (op_id,),
    ).fetchall()

    interacoes = []
    for item in interacoes_raw:
        ev = dict(item)
        ev["tempo"] = tempo_relativo(ev["criado_em"])
        interacoes.append(ev)

    clientes = db.execute("SELECT id, nome FROM clientes ORDER BY nome").fetchall()
    usuarios = db.execute("SELECT id, nome FROM usuarios WHERE ativo = 1 ORDER BY nome").fetchall()

    return render_template(
        "crm_oportunidade_detalhe.html",
        op=dict(op),
        interacoes=interacoes,
        clientes=clientes,
        usuarios=usuarios,
        estagios=list(_ESTAGIOS_CRM),
        usuario_nome=session.get("nome"),
        usuario_papel=session.get("papel"),
        usuario_iniciais=iniciais(session.get("nome", "?")),
        pendentes_count=_crm_pendentes(),
    )


@app.route("/crm/oportunidade/<int:op_id>/estagio", methods=["POST"])
@login_required
@csrf.exempt
def crm_atualizar_estagio(op_id):
    if not _crm_acesso():
        return jsonify({"erro": "acesso negado"}), 403
    if not _csrf_json_check():
        return jsonify({"erro": "token CSRF inválido"}), 400

    dados = request.get_json(silent=True) or {}
    estagio = dados.get("estagio", "")
    if estagio not in _ESTAGIOS_CRM:
        return jsonify({"erro": "estágio inválido"}), 400

    db = get_db()
    if not db.execute("SELECT id FROM oportunidades WHERE id = ?", (op_id,)).fetchone():
        return jsonify({"erro": "oportunidade não encontrada"}), 404

    db.execute(
        "UPDATE oportunidades SET estagio = ?, atualizado_em = ? WHERE id = ?",
        (estagio, agora(), op_id),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/crm/oportunidade/<int:op_id>/editar", methods=["POST"])
@login_required
def crm_editar_oportunidade(op_id):
    if not _crm_acesso():
        return redirect(url_for("board"))
    db = get_db()
    if not db.execute("SELECT id FROM oportunidades WHERE id = ?", (op_id,)).fetchone():
        flash("Oportunidade não encontrada.", "erro")
        return redirect(url_for("crm_funil"))

    titulo = request.form.get("titulo", "").strip()
    if not titulo:
        flash("Título é obrigatório.", "erro")
        return redirect(url_for("crm_oportunidade_detalhe", op_id=op_id))

    try:
        valor = float(request.form.get("valor_estimado") or 0) or None
    except (ValueError, TypeError):
        valor = None

    estagio = request.form.get("estagio", "Prospeccao")
    if estagio not in _ESTAGIOS_CRM:
        estagio = "Prospeccao"

    responsavel_id = request.form.get("responsavel_id") or None

    db.execute(
        """UPDATE oportunidades
           SET titulo = ?, valor_estimado = ?, estagio = ?, responsavel_id = ?, atualizado_em = ?
           WHERE id = ?""",
        (titulo, valor, estagio, responsavel_id, agora(), op_id),
    )
    db.commit()
    return redirect(url_for("crm_oportunidade_detalhe", op_id=op_id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5000)
