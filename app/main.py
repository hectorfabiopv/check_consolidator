from fastapi import FastAPI, HTTPException
from app.db.connection import get_connection
from app.services.sync_service import sync_cliente_by_id, sync_all_clients
from app.services.client_service import fetch_and_insert_clients
import mysql.connector

app = FastAPI(title="Check Consolidator", version="0.2.0")


@app.get("/clients")
def get_clients():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre, url, estado, director, usuario_ejecutor, created_at, updated_at 
            FROM inventario_clientes
            ORDER BY id ASC;
        """)
        data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not data:
            return {"message": "No hay clientes registrados."}
        return {"total": len(data), "clientes": data}

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/clientes/sync")
def sync_cliente(id: int):
    """
    Endpoint para sincronizar un cliente específico
    """
    detalle = sync_cliente_by_id(id)
    if detalle:
        return detalle
    raise HTTPException(status_code=500, detail=f"Error al sincronizar cliente {id}")


@app.post("/clientes/sync_all")
def sync_all_endpoint():
    """
    Endpoint para sincronizar todos los clientes
    """
    resumen = sync_all_clients()
    return {"message": "Sincronización completada", "resumen": resumen}


@app.post("/clientes/importar")
def importar_clientes():
    """
    Endpoint que obtiene clientes desde la API externa y los inserta en inventario_clientes.
    """
    resumen = fetch_and_insert_clients()
    if "error" in resumen:
        raise HTTPException(status_code=500, detail=resumen["error"])
    return {"message": "Clientes importados", "resumen": resumen}


    