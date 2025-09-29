from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import random
import asyncio
import os

app = FastAPI(title="Check Consolidator", version="0.1.0")

class ClientStatus(BaseModel):
    client_id: str
    critical_ok: bool
    score: float
    checked_at: datetime

# --------- INVENTARIO EN MEMORIA (demo) ---------
# Simula un inventario de clientes (en producción vendrá de DB)
INVENTORY = ["cliente_a", "cliente_b", "cliente_c", "cliente_d"]

# Estado / resultados en memoria (demo)
results: dict[str, ClientStatus] = {}

# --------- FUNCIONES SIMULADAS ---------
async def simulate_check(client_id: str) -> ClientStatus:
    # simula tiempo de respuesta y resultado
    await asyncio.sleep(random.uniform(0.2, 1.0))
    score = round(random.uniform(0.6, 1.0), 2)
    # critical_ok: ejemplo de regla simple (score > 0.9)
    critical_ok = score > 0.9
    return ClientStatus(client_id=client_id, critical_ok=critical_ok, score=score, checked_at=datetime.utcnow())

async def run_checks_all():
    # corre checks en paralelo y guarda en results
    tasks = [simulate_check(cid) for cid in INVENTORY]
    completed = await asyncio.gather(*tasks, return_exceptions=False)
    for st in completed:
        results[st.client_id] = st

# --------- STARTUP (opcional run inicial) ---------
@app.on_event("startup")
async def startup_event():
    # Lanza una ejecución inicial (no bloqueante)
    asyncio.create_task(run_checks_all())

# --------- ENDPOINTS ---------
@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}

@app.get("/status")
def status():
    last_check = max((r.checked_at for r in results.values()), default=None)
    return {
        "uptime": os.getenv("SERVICE_UPTIME", "demo"),
        "total_clients": len(INVENTORY),
        "processed_clients": len(results),
        "last_check": last_check.isoformat() if last_check else None
    }

@app.get("/reports/summary")
def summary():
    total = len(results)
    avg_score = round(sum(r.score for r in results.values())/total, 2) if total else 0.0
    critical_fail = [c for c, r in results.items() if not r.critical_ok]
    return {
        "total_clients": total,
        "avg_score": avg_score,
        "critical_failures": critical_fail,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/reports/client/{client_id}")
def client_report(client_id: str):
    if client_id not in INVENTORY:
        return {"error": "Client not found", "client_id": client_id}
    return results.get(client_id, {"status": "not_checked"})

# Endpoint para forzar ejecución manual (útil en demo)
@app.post("/run_checks")
async def run_checks(background_tasks: BackgroundTasks):
    # se dispara en background y responde rápido
    background_tasks.add_task(run_checks_all)
    return {"status": "started", "timestamp": datetime.utcnow().isoformat()}

# -------------------------------------------------------------------
# ENDPOINTS DE REPORTES ADICIONALES (datos de ejemplo)
# -------------------------------------------------------------------

from collections import defaultdict

# ======= Datos falsos para demo =======
# Historial por cliente: lista de checks con fecha y puntaje
FAKE_HISTORY = {
    "cliente_a": [
        {"timestamp": "2025-09-20T03:15:00Z", "score": 0.78, "critical_ok": False},
        {"timestamp": "2025-09-25T03:15:00Z", "score": 0.85, "critical_ok": True},
        {"timestamp": "2025-09-29T03:15:00Z", "score": 0.92, "critical_ok": True},
    ],
    "cliente_b": [
        {"timestamp": "2025-09-21T04:20:00Z", "score": 0.70, "critical_ok": False},
        {"timestamp": "2025-09-27T04:20:00Z", "score": 0.74, "critical_ok": False},
        {"timestamp": "2025-09-29T04:20:00Z", "score": 0.80, "critical_ok": True},
    ]
}

# Módulos críticos y cantidad de clientes con fallo en cada uno
FAKE_CRITICAL_MODULES = [
    {"module": "Base de Datos",   "failed_clients": 15},
    {"module": "Autenticación",   "failed_clients": 9},
    {"module": "Notificaciones",  "failed_clients": 4},
]

# Cumplimiento promedio por departamento (Colombia)
FAKE_DEPARTMENTS = [
    {"department": "Antioquia",       "avg_score": 0.91, "critical_failures": 3},
    {"department": "Cundinamarca",    "avg_score": 0.88, "critical_failures": 5},
    {"department": "Valle del Cauca", "avg_score": 0.84, "critical_failures": 4},
    {"department": "Atlántico",       "avg_score": 0.90, "critical_failures": 2},
]
# ======= Fin datos falsos =======


@app.get("/reports/history/{client_id}")
def history(client_id: str):
    """
    Devuelve la evolución de cumplimiento de un cliente a lo largo del tiempo.
    """
    history_data = FAKE_HISTORY.get(client_id)
    if not history_data:
        return {"client_id": client_id, "history": [], "message": "Sin datos de historial"}
    return {"client_id": client_id, "history": history_data}


@app.get("/reports/critical-modules")
def critical_modules():
    """
    Ranking de módulos críticos con mayor número de fallos en todos los clientes.
    """
    return {
        "total_modules": len(FAKE_CRITICAL_MODULES),
        "modules": FAKE_CRITICAL_MODULES,
        "timestamp": datetime.utcnow()
    }


@app.get("/reports/compliance-by-department")
def compliance_by_department():
    """
    Cumplimiento promedio y cantidad de fallos críticos por departamento de Colombia.
    """
    total_clients = sum(dep["critical_failures"] for dep in FAKE_DEPARTMENTS) + 100  # dato ficticio
    return {
        "total_clients_estimated": total_clients,
        "departments": FAKE_DEPARTMENTS,
        "timestamp": datetime.utcnow()
    }

