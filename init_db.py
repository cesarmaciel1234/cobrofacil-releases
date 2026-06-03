import sqlite3
import os
import hashlib

DB_PATH = os.path.join(os.path.dirname(__file__), "punpro.db")

def get_hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_database(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        precio REAL
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        total REAL,
        efectivo REAL,
        vuelto REAL,
        metodo_pago TEXT,
        tarjeta REAL,
        carrito TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password_hash TEXT,
        rol TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_comercio TEXT,
        cuit TEXT,
        direccion TEXT,
        telefono TEXT,
        mensaje_ticket TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_caja (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        tipo TEXT, -- 'APERTURA' o 'CIERRE'
        monto REAL,
        usuario TEXT,
        observaciones TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS licencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        clave TEXT,
        tipo TEXT,
        vencimiento TEXT
    )
    """)

    try:
        cur.execute("INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?)", ("admin", get_hash("admin"), "admin"))
    except sqlite3.IntegrityError:
        pass

    try:
        cur.execute("INSERT INTO configuracion (nombre_comercio) VALUES (?)", ("Mi Comercio",))
    except Exception:
        pass

    productos = [
        ("Carne vacuna", 1200),
        ("Pollo", 800),
        ("Chorizo", 400),
        ("Queso", 600),
        ("Pan", 100)
    ]

    for nombre, precio in productos:
        try:
            cur.execute("INSERT INTO productos (nombre, precio) VALUES (?, ?)", (nombre, precio))
        except:
            pass

    con.commit()
    con.close()

if __name__ == "__main__":
    init_database()
    print("Base de datos inicializada con productos ✅")
