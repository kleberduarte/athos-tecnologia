-- Console de Chamados — Athos Tecnologia
-- Schema SQLite completo (sem ORM, sqlite3 puro).
-- Estado atual: inclui todas as colunas adicionadas pelas migrações.

DROP TABLE IF EXISTS equipment_scan_results;
DROP TABLE IF EXISTS movimentacoes;
DROP TABLE IF EXISTS comentarios;
DROP TABLE IF EXISTS chamados;
DROP TABLE IF EXISTS equipamentos;
DROP TABLE IF EXISTS setores;
DROP TABLE IF EXISTS usuarios;

CREATE TABLE usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    senha_hash  TEXT NOT NULL,
    papel       TEXT NOT NULL CHECK (papel IN ('solicitante', 'atendente', 'admin')) DEFAULT 'atendente',
    setor       TEXT,
    ativo       INTEGER NOT NULL DEFAULT 1,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE setores (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

CREATE TABLE equipamentos (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    ip        TEXT NOT NULL,
    modelo    TEXT,
    serial    TEXT,
    setor_id  INTEGER REFERENCES setores(id),
    ativo     INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL
);

CREATE TABLE chamados (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo         TEXT NOT NULL,
    descricao      TEXT,
    prioridade     TEXT NOT NULL CHECK (prioridade IN ('alta', 'media', 'baixa')) DEFAULT 'media',
    status         TEXT NOT NULL CHECK (status IN ('aberto', 'andamento', 'aguardando', 'impedido', 'resolvido', 'cancelado')) DEFAULT 'aberto',
    sla_horas      INTEGER NOT NULL DEFAULT 24,
    setor_id       INTEGER REFERENCES setores(id),
    atribuido_a    INTEGER REFERENCES usuarios(id),
    criado_por     INTEGER REFERENCES usuarios(id),
    equipamento_id INTEGER REFERENCES equipamentos(id),
    anexo          TEXT,
    anexo_nome     TEXT,
    criado_em      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    atualizado_em  TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    resolvido_em   TEXT
);

CREATE TABLE movimentacoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chamado_id      INTEGER NOT NULL REFERENCES chamados(id),
    status_anterior TEXT,
    status_novo     TEXT NOT NULL,
    usuario_id      INTEGER REFERENCES usuarios(id),
    criado_em       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE comentarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    chamado_id  INTEGER NOT NULL REFERENCES chamados(id),
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    texto       TEXT NOT NULL,
    anexo       TEXT,
    anexo_nome  TEXT,
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE equipment_scan_results (
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
);

CREATE INDEX idx_chamados_status      ON chamados(status);
CREATE INDEX idx_movimentacoes_chamado ON movimentacoes(chamado_id);
CREATE INDEX idx_comentarios_chamado  ON comentarios(chamado_id);
CREATE INDEX idx_scan_chamado         ON equipment_scan_results(chamado_id);
CREATE INDEX idx_scan_equipamento     ON equipment_scan_results(equipamento_id);

CREATE TABLE incidentes (
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
);

CREATE TABLE incidente_eventos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    incidente_id INTEGER NOT NULL REFERENCES incidentes(id) ON DELETE CASCADE,
    tipo         TEXT NOT NULL CHECK (tipo IN ('status','comentario')),
    status_novo  TEXT,
    texto        TEXT,
    usuario_id   INTEGER REFERENCES usuarios(id),
    criado_em    TEXT NOT NULL
);

CREATE INDEX idx_incidentes_status   ON incidentes(status);
CREATE INDEX idx_inc_eventos_inc     ON incidente_eventos(incidente_id);
