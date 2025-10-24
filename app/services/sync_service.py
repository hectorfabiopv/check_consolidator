# app/services/sync_service.py
import requests
import logging
from app.db.connection import get_connection
import mysql.connector
import os

# Configurar logging
os.makedirs("app/logs", exist_ok=True)
logging.basicConfig(
    filename="app/logs/sync_errors.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def sync_cliente_by_id(client_id: int) -> dict:
    """
    Sincroniza un cliente específico y actualiza la base de datos.
    Retorna True si fue exitoso, False si falló.
    """
    from datetime import datetime

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM inventario_clientes WHERE id = %s", (client_id,))
        cliente = cursor.fetchone()
        if not cliente:
            logging.error(f"Cliente {client_id} no encontrado.")
            return None

        base_url = cliente["url"].rstrip("/")
        endpoint = f"{base_url}/api/administracion/get_check_info/"

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logging.error(f"Error HTTP para cliente {client_id}: {e}")
            return None

        try:
            resultado_json = data["data"]["results"]["resultado_json"]
            timestamp = datetime.utcnow()
        except KeyError:
            logging.error(f"Estructura JSON inesperada para cliente {client_id}")
            return None

        cursor.execute(
            "UPDATE inventario_clientes SET resultado_json = %s, updated_at = UNIX_TIMESTAMP() WHERE id = %s",
            (resultado_json, client_id)
        )
        conn.commit()
        
        return {
            "status": "ok",
            "cliente_id": client_id,
            "endpoint_consultado": endpoint,
            "resultado_guardado": True,
            "timestamp": timestamp
        }

    except mysql.connector.Error as e:
        logging.error(f"Error en la base de datos para cliente {client_id}: {e}")
        return None
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


def sync_all_clients() -> dict:
    """
    Sincroniza todos los clientes en la tabla inventario_clientes.
    Retorna un resumen.
    """
    resultados = {"total": 0, "ok": 0, "failed": 0, "errores": [], "detalles": []}

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, url FROM inventario_clientes ORDER BY id ASC;")
        clientes = cursor.fetchall()

        for cliente in clientes:
            client_id = cliente["id"]
            resultados["total"] += 1

            detalle = sync_cliente_by_id(client_id)
            if detalle:
                resultados["ok"] += 1
                resultados["detalles"].append(detalle)
            else:
                resultados["failed"] += 1
                base_url = cliente["url"].rstrip("/")
                endpoint = f"{base_url}/api/administracion/get_check_info/"
                msg = f"En sync_all {endpoint} falló"
                resultados["errores"].append(msg)
                logging.error(msg)

        return resultados

    except mysql.connector.Error as e:
        logging.exception(f"Error general en sync_all: {e}")
        return resultados
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
