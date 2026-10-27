"""Sin maestra, clientes y pagos se leen de la copia, no de la SQLite vacía."""

import sqlite3

from src.base_de_datos.core.executor import QueryExecutorMixin


def test_sin_maestra_la_lectura_sale_de_la_copia(tmp_path, monkeypatch):
    copia_db = tmp_path / "espejo_tienda.db"
    conn = sqlite3.connect(copia_db)
    conn.execute("CREATE TABLE clientes (id INTEGER, nombre TEXT)")
    conn.execute("INSERT INTO clientes (id, nombre) VALUES (7, 'Ana')")
    conn.execute("CREATE TABLE mp_pagos (payment_id TEXT, monto REAL)")
    conn.execute("INSERT INTO mp_pagos (payment_id, monto) VALUES ('mp1', 1500)")
    conn.commit()
    conn.close()

    import src.jefe.nodo_portable.espejo.copia as copia

    monkeypatch.setattr(copia, "existe", lambda path=None: True)
    monkeypatch.setattr(copia, "ruta", lambda: str(copia_db))

    caja = object.__new__(QueryExecutorMixin)
    caja._forced_local_offline = True
    caja.is_master = False

    clientes = caja._filas_copia("SELECT nombre FROM clientes WHERE id = ?", (7,))
    assert clientes[0]["nombre"] == "Ana"
    assert clientes[0][0] == "Ana"

    pagos = caja._filas_copia("SELECT monto FROM mp_pagos WHERE payment_id = ?", ("mp1",))
    assert pagos[0]["monto"] == 1500

    caja._forced_local_offline = False
    assert caja._filas_copia("SELECT nombre FROM clientes") is None


def test_la_nutricion_no_se_dispara_dos_veces(monkeypatch):
    import threading

    from src.base_de_datos import offline_sync as modulo

    sync = object.__new__(modulo.OfflineSync)
    sync._nutriendo = False
    sync._nutri_lock = threading.Lock()
    arrancados = []

    class _Hilo:
        def __init__(self, target, daemon, name):
            arrancados.append(name)

        def start(self):
            return None

    monkeypatch.setattr(modulo.threading, "Thread", _Hilo)
    sync.nutrir_ya()
    sync.nutrir_ya()
    assert arrancados == ["nutricion-maestra"]
    assert sync._nutriendo is True
