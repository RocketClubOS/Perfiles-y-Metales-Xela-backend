import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "memoria_agente.db")


def crear_tabla():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mensaje_usuario TEXT,
        respuesta_agente TEXT,
        fecha_hora TEXT
    )
    """)

    conn.commit()
    conn.close()


def guardar_conversacion(mensaje_usuario, respuesta_agente):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO conversaciones (
        mensaje_usuario,
        respuesta_agente,
        fecha_hora
    )
    VALUES (?, ?, ?)
    """, (
        mensaje_usuario,
        respuesta_agente,
        datetime.now().isoformat()
    ))

    conn.commit()
    conn.close()