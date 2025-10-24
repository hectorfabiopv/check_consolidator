# app/services/client_service.py
import requests
import logging
from datetime import datetime
from app.db.connection import get_connection
import mysql.connector
import os

# Logging
os.makedirs("app/logs", exist_ok=True)
logging.basicConfig(
    filename="app/logs/sync_errors.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

EXTERNAL_API_URL = "https://servicios.nexura.com/api/servicios/get_clientes_cc"

def fetch_and_insert_clients() -> dict:
    """
    Obtiene clientes desde la API externa y los inserta en inventario_clientes.
    Evita duplicados basados en la URL.
    Retorna un resumen de la operación.
    """
    resultados = {"total": 0, "insertados": 0, "duplicados": 0, "fallidos": 0, "errores": []}

    # Obtener datos de la API externa
    try:
        response = requests.get(EXTERNAL_API_URL, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logging.error(f"Error al obtener clientes de API externa: {e}")
        return {"error": str(e)}

    try:
        results = data.get("data", {}).get("results", [])
    except KeyError:
        logging.error("Estructura JSON inesperada de la API externa")
        return {"error": "Estructura JSON inesperada"}

    # Conexión a la base de datos
    conn = get_connection()
    cursor = conn.cursor()

    for cliente in results:
        resultados["total"] += 1
        nombre = cliente.get("nombre")
        url = cliente.get("url")
        director = cliente.get("director")

        # Validación de datos completos
        if not nombre or not url or not director:
            msg = f"Datos incompletos para cliente: {cliente}"
            resultados["fallidos"] += 1
            resultados["errores"].append(msg)
            logging.error(msg)
            continue

        # Validar duplicados por URL
        cursor.execute("SELECT COUNT(*) FROM inventario_clientes WHERE url = %s", (url,))
        if cursor.fetchone()[0] > 0:
            resultados["duplicados"] += 1
            continue  # saltar este cliente

        # Insertar registro
        try:
            timestamp = int(datetime.utcnow().timestamp())
            cursor.execute(
                """
                INSERT INTO inventario_clientes
                (nombre, url, estado, director, resultado_json, usuario_ejecutor, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (nombre, url, 0.00, director, '', 'micro-servicio', timestamp, timestamp)
            )
            resultados["insertados"] += 1
        except mysql.connector.Error as e:
            resultados["fallidos"] += 1
            msg = f"Error DB al insertar cliente {nombre}: {e}"
            resultados["errores"].append(msg)
            logging.error(msg)

    conn.commit()
    cursor.close()
    conn.close()

    return resultados
