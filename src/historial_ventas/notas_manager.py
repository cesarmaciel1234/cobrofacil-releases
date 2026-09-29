import sqlite3
import os

from src.utils.paths import get_base_path
DB_DIR = os.path.join(get_base_path(), "base_de_datos")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "notas_tickets.sqlite")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS notas (
        id_venta INTEGER PRIMARY KEY,
        nota TEXT
    )""")
    conn.commit()
    conn.close()

def guardar_nota(id_venta: int, nota: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    if not nota or not nota.strip():
        conn.execute("DELETE FROM notas WHERE id_venta = ?", (id_venta,))
    else:
        conn.execute("REPLACE INTO notas (id_venta, nota) VALUES (?, ?)", (id_venta, nota.strip()))
    conn.commit()
    conn.close()

def cargar_nota(id_venta: int) -> str:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT nota FROM notas WHERE id_venta = ?", (id_venta,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""

def cargar_todas_notas() -> dict:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT id_venta, nota FROM notas")
    res = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()
    return res
