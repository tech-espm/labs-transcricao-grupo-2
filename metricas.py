from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from collections import deque
from datetime import datetime, timedelta
from flask import Response
import threading

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

_EVENTOS = deque()
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
        proc = [e for e in _EVENTOS if e[2] is not None]
        if not proc:
            return 1.0 
        ok = sum(1 for e in proc if e[2] is True)
        return ok / len(proc)

def resumo_24h():
    with _LOCK:
        _limpar_janela_24h()
        validos = sum(1 for e in _EVENTOS if e[1] is True and e[2] is None) 
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
