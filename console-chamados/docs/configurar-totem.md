# Configurar um totem para scan remoto

Este guia descreve como instalar e configurar o agente HTTP em um totem novo para que o Console de Chamados consiga executar diagnósticos remotos.

---

## Pré-requisitos

- Totem com **Windows, Linux ou Android** (mínimo Android 8).
- Python 3.8+ instalado (ou runtime equivalente para o agente).
- O IP do totem deve ser **estático** (ou reservado via DHCP) e acessível pelo servidor do Console de Chamados.
- Porta **8765** liberada no firewall local do totem (entrada TCP).

---

## Contrato da API do agente

O agente deve expor os seguintes endpoints via HTTP na porta `8765` (configurável em `AGENT_PORT`):

### `GET /status/display`

```json
{
  "status": "ok",
  "brilho": 80,
  "resolucao": "1920x1080"
}
```

Valores válidos para `status`: `ok` | `travado` | `sem_sinal` | `erro`

---

### `GET /status/hardware`

```json
{
  "status": "ok",
  "modelo": "iMin S1",
  "serial": "SN-IMIN-001",
  "firmware": "2.3.1",
  "so": "Android 10"
}
```

Valores válidos para `status`: `ok` | `erro`

---

### `GET /status/printer`

```json
{
  "status": "online",
  "papel_presente": true,
  "toner_nivel": 85,
  "fila_tamanho": 0
}
```

Valores válidos para `status`: `online` | `sem_papel` | `sem_toner` | `fila_travada` | `erro`

---

### `GET /status/connectivity`

```json
{
  "status": "ok",
  "uptime_s": 86400,
  "latencia_ms": 3
}
```

Valores válidos para `status`: `ok` | `erro`

---

## Implementação de referência (Python/Flask)

Crie um arquivo `agente_totem.py` no totem:

```python
from flask import Flask, jsonify
import subprocess, platform, socket, time

app = Flask(__name__)
START_TIME = time.time()

@app.get("/status/display")
def display():
    # Adapte a lógica para o hardware específico
    return jsonify({"status": "ok"})

@app.get("/status/hardware")
def hardware():
    return jsonify({
        "status": "ok",
        "so": platform.system() + " " + platform.release(),
        "hostname": socket.gethostname(),
    })

@app.get("/status/printer")
def printer():
    # Adapte para o modelo de impressora do totem
    return jsonify({"status": "online", "papel_presente": True})

@app.get("/status/connectivity")
def connectivity():
    return jsonify({
        "status": "ok",
        "uptime_s": int(time.time() - START_TIME),
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765)
```

Instale as dependências: `pip install flask`

---

## Instalação por sistema operacional

### Linux (systemd)

Crie `/etc/systemd/system/agente-totem.service`:

```ini
[Unit]
Description=Agente de diagnóstico — Console de Chamados
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/agente-totem/agente_totem.py
Restart=on-failure
User=nobody

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl enable --now agente-totem
```

### Windows (como serviço)

Use `NSSM` (Non-Sucking Service Manager):

```cmd
nssm install AgenteTotem "C:\Python311\python.exe" "C:\agente-totem\agente_totem.py"
nssm start AgenteTotem
```

Regra de firewall:
```cmd
netsh advfirewall firewall add rule name="Agente Totem" protocol=TCP dir=in localport=8765 action=allow
```

### Android

Use o app **Termux** (F-Droid):

```bash
pkg install python
pip install flask
python agente_totem.py
```

Para inicialização automática, use **Termux:Boot** e adicione o script ao diretório `~/.termux/boot/`.

---

## Cadastrar o totem no sistema

Após o agente estar rodando, cadastre o totem via API do Console de Chamados:

```bash
curl -X POST https://seu-servidor/api/equipamentos \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: <token>" \
  -d '{
    "nome": "Totem iMin S1 — Loja Centro",
    "ip": "192.168.1.101",
    "modelo": "iMin S1",
    "serial": "SN-IMIN-001",
    "setor_id": 2
  }'
```

Somente usuários com papel `admin` podem cadastrar equipamentos.

---

## Verificar o scan manualmente

```bash
curl -X POST https://seu-servidor/api/equipamentos/<id>/scan \
  -H "X-CSRFToken: <token>"
```

---

## Variáveis de ambiente no servidor

| Variável         | Padrão | Descrição                              |
|------------------|--------|----------------------------------------|
| `AGENT_PORT`     | `8765` | Porta do agente HTTP no totem          |
| `SCAN_TIMEOUT_S` | `10`   | Timeout por verificação (segundos)     |
