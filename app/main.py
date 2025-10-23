from fastapi import FastAPI, HTTPException
from app.db.connection import get_connection
import requests
import json
import mysql.connector

app = FastAPI(title="Check Consolidator", version="0.1.0")


@app.get("/clients")
def get_clients():
    """Obtiene la lista de clientes desde la base de datos"""
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
    1️⃣ Recibe el ID del cliente.
    2️⃣ Consulta el cliente en la base de datos.
    3️⃣ Llama a su endpoint remoto `${url}/api/administracion/get_check_info/`.
    4️⃣ Guarda el campo data->results->resultado_json en la BD.
    """
    try:
        # 1. Conexión a la base de datos
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 2. Buscar cliente por ID
        cursor.execute("SELECT * FROM inventario_clientes WHERE id = %s", (id,))
        cliente = cursor.fetchone()

        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        base_url = cliente["url"].rstrip("/")
        endpoint = f"{base_url}/api/administracion/get_check_info/"

        # 3. Llamar al endpoint remoto
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(endpoint, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.HTTPError as http_err:
            raise HTTPException(status_code=response.status_code,
                                detail=f"HTTP error: {http_err}")
        except Exception as e:
            raise HTTPException(status_code=502,
                                detail=f"Error al consultar el endpoint remoto: {e}")

        # 4. Extraer data->results->resultado_json
        try:
            resultado_json = data["data"]["results"]["resultado_json"]
        except KeyError:
            raise HTTPException(status_code=500, detail="Estructura JSON inesperada")

        # 5. Guardar en la BD
        cursor.execute(
            "UPDATE inventario_clientes SET resultado_json = %s, updated_at = UNIX_TIMESTAMP() WHERE id = %s",
            (resultado_json, id),
        )
        conn.commit()

        return {
            "status": "ok",
            "cliente_id": id,
            "endpoint_consultado": endpoint,
            "resultado_guardado": True,
            "timestamp": data["data"]["results"].get("timestamp")
        }

    except mysql.connector.Error as db_err:
        raise HTTPException(status_code=500, detail=f"Error en la base de datos: {db_err}")

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
