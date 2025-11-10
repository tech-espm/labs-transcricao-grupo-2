from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from collections import deque
from datetime import datetime, timedelta
from flask import Response
import threading

# --- Contadores acumulados (Prometheus) ---
#Prometheus é uma biblioteca que transforma seu código Flask em um sistema monitorável, permitindo acompanhar em tempo real quantas operações deram certo, 
# quantas falharam e qual é a taxa de sucesso.
UPLOADS_VALIDOS = Counter(
    "uploads_validos_total",
    "Quantidade de uploads que passaram na validacao"
)
PROCESSAMENTOS_OK = Counter(
    "processamentos_ok_total",
    "Quantidade de uploads validos que processaram sem erro"
)
PROCESSAMENTOS_ERRO = Counter(
    "processamentos_erro_total",
    "Quantidade de uploads validos que falharam no processamento"
)

# --- Janela deslizante em memoria (ultimas 24h) ---
_EVENTOS = deque()  # cada item: (timestamp: datetime, valido: bool, sucesso: bool)
_LOCK = threading.Lock()

def registrar_upload_valido():
    with _LOCK:
        _EVENTOS.append((datetime.utcnow(), True, None))
    UPLOADS_VALIDOS.inc()

def registrar_processamento(sucesso: bool):
    with _LOCK:
        _EVENTOS.append((datetime.utcnow(), True, sucesso))
    if sucesso:
        PROCESSAMENTOS_OK.inc()
    else:
        PROCESSAMENTOS_ERRO.inc()

def _limpar_janela_24h(agora=None):
    if agora is None:
        agora = datetime.utcnow()
    limite = agora - timedelta(hours=24)
    while _EVENTOS and _EVENTOS[0][0] < limite:
        _EVENTOS.popleft()

def taxa_sucesso_24h():
    with _LOCK:
        _limpar_janela_24h()
        # Consideramos apenas eventos de processamento (onde sucesso é True/False)
        proc = [e for e in _EVENTOS if e[2] is not None]
        if not proc:
            return 1.0  # se não houve processamentos nas últimas 24h, adotamos 100% (ajuste se desejar)
        ok = sum(1 for e in proc if e[2] is True)
        return ok / len(proc)

def resumo_24h():
    with _LOCK:
        _limpar_janela_24h()
        validos = sum(1 for e in _EVENTOS if e[1] is True and e[2] is None)  # registros de "validou upload"
        proc = [e for e in _EVENTOS if e[2] is not None]
        ok = sum(1 for e in proc if e[2] is True)
        falha = sum(1 for e in proc if e[2] is False)
    return {
        "validos_registrados": validos,
        "processamentos_total": len(proc),
        "processamentos_ok": ok,
        "processamentos_erro": falha,
        "taxa_sucesso_24h": round(taxa_sucesso_24h(), 4),
    }

def metricas_endpoint():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
