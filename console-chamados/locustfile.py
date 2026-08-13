"""
Teste de carga — Console de Chamados
Locust com exporter Prometheus (porta 9646) para visualizacao em Grafana.

Iniciar:
  locust -f locustfile.py --host http://127.0.0.1:5000
  (abra http://localhost:8089, configure usuarios/rampa e clique Start)

Ou headless:
  locust -f locustfile.py --headless -u 50 -r 5 -t 60s --host http://127.0.0.1:5000
"""
import json
import random
import time

from locust import HttpUser, TaskSet, between, task, events
from prometheus_client import Counter, Histogram, Gauge, start_http_server

_prom_started = False
_requests_total = Counter(
    "locust_requests_total",
    "Total requests",
    ["method", "name", "status"],
)
_response_time = Histogram(
    "locust_response_time_seconds",
    "Response time in seconds",
    ["method", "name"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
)
_users_active = Gauge("locust_users_active", "Active users")
_failures_total = Counter(
    "locust_failures_total",
    "Total failures",
    ["method", "name"],
)


@events.init.add_listener
def on_locust_init(environment, **kwargs):
    global _prom_started
    if not _prom_started:
        start_http_server(9646)
        _prom_started = True


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    status = "failure" if exception else "success"
    _requests_total.labels(method=request_type, name=name, status=status).inc()
    _response_time.labels(method=request_type, name=name).observe(response_time / 1000)
    if exception:
        _failures_total.labels(method=request_type, name=name).inc()


@events.spawning_complete.add_listener
def on_spawning_complete(user_count, **kwargs):
    _users_active.set(user_count)


@events.quitting.add_listener
def on_quitting(environment, **kwargs):
    _users_active.set(0)


def _csrf(response):
    import re
    m = re.search(rb'name="csrf-token"\s+content="([^"]+)"', response.content)
    return m.group(1).decode() if m else ""


# ─────────────────────────────────────────────────────────────────────────────
# TASKSETS
# ─────────────────────────────────────────────────────────────────────────────

class TarefasAdmin(TaskSet):
    csrf = ""

    def on_start(self):
        r = self.client.post("/login",
                             data={"email": "admin@ci.test", "senha": "senha123"},
                             allow_redirects=True)
        self.csrf = _csrf(r)

    @task(5)
    def board(self):
        r = self.client.get("/", name="GET /board")
        self.csrf = _csrf(r)

    @task(3)
    def listar_usuarios(self):
        self.client.get("/usuarios", name="GET /usuarios")

    @task(3)
    def listar_equipamentos(self):
        self.client.get("/equipamentos", name="GET /equipamentos")

    @task(2)
    def api_equipamentos_json(self):
        self.client.get("/api/equipamentos", name="GET /api/equipamentos")

    @task(2)
    def relatorios(self):
        self.client.get("/relatorios", name="GET /relatorios")

    @task(2)
    def crm_clientes(self):
        self.client.get("/crm/clientes", name="GET /crm/clientes")

    @task(2)
    def crm_funil(self):
        self.client.get("/crm/funil", name="GET /crm/funil")

    @task(1)
    def exportar_csv(self):
        self.client.get("/chamados/exportar", name="GET /chamados/exportar")

    @task(2)
    def ver_chamado(self):
        cid = random.randint(1, 10)
        self.client.get(f"/chamados/{cid}", name="GET /chamados/<id>")

    @task(1)
    def atualizar_status_chamado(self):
        cid = random.randint(1, 10)
        status = random.choice(["aberto", "andamento", "aguardando"])
        self.client.post(
            f"/chamados/{cid}/status",
            data=json.dumps({"status": status}),
            headers={"Content-Type": "application/json", "X-CSRFToken": self.csrf},
            name="POST /chamados/<id>/status",
        )

    @task(1)
    def ver_incidentes(self):
        self.client.get("/incidentes", name="GET /incidentes")


class TarefasAtendente(TaskSet):
    csrf = ""

    def on_start(self):
        r = self.client.post("/login",
                             data={"email": "atend@ci.test", "senha": "senha123"},
                             allow_redirects=True)
        self.csrf = _csrf(r)

    @task(6)
    def board(self):
        r = self.client.get("/", name="GET /board")
        self.csrf = _csrf(r)

    @task(4)
    def ver_chamado(self):
        cid = random.randint(1, 10)
        self.client.get(f"/chamados/{cid}", name="GET /chamados/<id>")

    @task(3)
    def relatorios(self):
        self.client.get("/relatorios", name="GET /relatorios")

    @task(3)
    def crm_funil(self):
        self.client.get("/crm/funil", name="GET /crm/funil")

    @task(2)
    def crm_clientes(self):
        self.client.get("/crm/clientes", name="GET /crm/clientes")

    @task(2)
    def ver_incidentes(self):
        self.client.get("/incidentes", name="GET /incidentes")

    @task(1)
    def mover_oportunidade(self):
        oid = random.randint(1, 12)
        estagio = random.choice(["Prospeccao", "Qualificacao", "Proposta"])
        self.client.post(
            f"/crm/oportunidade/{oid}/estagio",
            data=json.dumps({"estagio": estagio}),
            headers={"Content-Type": "application/json", "X-CSRFToken": self.csrf},
            name="POST /crm/oportunidade/<id>/estagio",
        )

    @task(1)
    def atribuir_chamado(self):
        cid = random.randint(1, 10)
        self.client.post(
            f"/chamados/{cid}/atribuir",
            data=json.dumps({"usuario_id": 2}),
            headers={"Content-Type": "application/json", "X-CSRFToken": self.csrf},
            name="POST /chamados/<id>/atribuir",
        )


class TarefasSolicitante(TaskSet):
    csrf = ""

    def on_start(self):
        r = self.client.post("/login",
                             data={"email": "solic@ci.test", "senha": "senha123"},
                             allow_redirects=True)
        self.csrf = _csrf(r)

    @task(8)
    def board(self):
        self.client.get("/", name="GET /board")

    @task(4)
    def ver_proprio_chamado(self):
        self.client.get("/chamados/1", name="GET /chamados/<id>")

    @task(1)
    def abrir_chamado(self):
        self.client.post(
            "/chamados",
            data={"titulo": f"Chamado perf {random.randint(1000, 9999)}",
                  "descricao": "Gerado por teste de carga",
                  "prioridade": "baixa"},
            name="POST /chamados",
        )


# ─────────────────────────────────────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────────────────────────────────────

class AdminUser(HttpUser):
    tasks = [TarefasAdmin]
    weight = 1
    wait_time = between(1, 3)


class AtendenteUser(HttpUser):
    tasks = [TarefasAtendente]
    weight = 4
    wait_time = between(0.5, 2)


class SolicitanteUser(HttpUser):
    tasks = [TarefasSolicitante]
    weight = 5
    wait_time = between(1, 4)
