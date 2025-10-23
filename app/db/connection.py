import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

# Cargar variables del entorno (.env)
load_dotenv()

# Crear un pool de conexiones (mejor para Cloud Run)
dbconfig = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
    "use_unicode": True
}

try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="mypool",
        pool_size=5,
        pool_reset_session=True,
        **dbconfig
    )
except Exception as e:
    print("❌ Error creando el pool de conexiones MySQL:", e)
    connection_pool = None

def get_connection():
    """Obtiene una conexión desde el pool"""
    if connection_pool is None:
        raise Exception("No se pudo crear el pool de conexiones.")
    return connection_pool.get_connection()
