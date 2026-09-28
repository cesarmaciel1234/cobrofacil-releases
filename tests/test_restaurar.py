"""Motor único de restauración (src/base_de_datos/restaurar)."""

import datetime as dt
import os
import sqlite3

import pytest

from src.base_de_datos import restaurar
from src.base_de_datos.restaurar import Destino
from src.base_de_datos.restaurar.aplicar import motor

HOY = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _copia(path, servidor="MAESTRA", completa="1", ultima=HOY):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE espejo_meta (clave TEXT PRIMARY KEY, valor TEXT);
        CREATE TABLE productos (id INTEGER PRIMARY KEY, nombre TEXT, stock REAL);
        CREATE TABLE ventas (id INTEGER PRIMARY KEY, fecha TEXT, total REAL, request_id TEXT);
        CREATE TABLE detalles_ventas (id INTEGER PRIMARY KEY, id_venta INTEGER, nombre_producto TEXT, subtotal REAL);
        CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre TEXT);
        CREATE TABLE solo_en_copia (id INTEGER PRIMARY KEY, x TEXT);
        """
    )
    conn.executemany(
        "INSERT INTO espejo_meta VALUES (?, ?)",
        [("ultima_copia", ultima), ("servidor", servidor), ("completa", completa)],
    )
    conn.executemany("INSERT INTO productos VALUES (?,?,?)", [(1, "Pan", 99), (2, "Leche", 4)])
    conn.executemany(
        "INSERT INTO ventas VALUES (?,?,?,?)",
        [(1, HOY, 100, "A"), (2, HOY, 200, "B"), (3, HOY, 300, "C")],
    )
    conn.executemany(
        "INSERT INTO detalles_ventas VALUES (?,?,?,?)",
        [(10, 1, "Pan", 100), (11, 2, "Leche", 200), (12, 3, "Asado", 300)],
    )
    conn.execute("INSERT INTO usuarios VALUES (1, 'jefe')")
    conn.execute("INSERT INTO solo_en_copia VALUES (1, 'x')")
    conn.commit()
    conn.close()
    return str(path)


def _tienda(path):
    """La tienda restaurada: vende ticket 3 con otro request_id después de perder datos."""
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE productos (id INTEGER PRIMARY KEY, nombre TEXT, stock REAL);
        CREATE TABLE ventas (id INTEGER PRIMARY KEY, fecha TEXT, total REAL, request_id TEXT UNIQUE);
        CREATE TABLE detalles_ventas (id INTEGER PRIMARY KEY, id_venta INTEGER, nombre_producto TEXT, subtotal REAL);
        CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre TEXT);
        """
    )
    conn.execute("INSERT INTO productos VALUES (1, 'Pan', 5)")
    conn.execute("INSERT INTO ventas VALUES (1, ?, 100, 'A')", (HOY,))
    conn.execute("INSERT INTO ventas VALUES (3, ?, 50, 'Z')", (HOY,))
    conn.execute("INSERT INTO detalles_ventas VALUES (10, 1, 'Pan', 100)")
    conn.execute("INSERT INTO detalles_ventas VALUES (12, 3, 'Chorizo', 50)")
    conn.commit()
    conn.close()
    return Destino("sqlite", archivo=str(path), servidor="MAESTRA")


def test_buscar_ordena_de_la_mas_nueva_y_descarta_lo_ajeno(tmp_path):
    usb = tmp_path / "USB"
    (usb / "CobroFacil_Nodo").mkdir(parents=True)
    (usb / "respaldos").mkdir()
    _copia(usb / "CobroFacil_Nodo" / "nodo_negocio.db")
    sql = usb / "respaldos" / "backup_periodico_2026-09-20_101010.sql"
    sql.write_text("-- MariaDB dump 10.19\n" + "INSERT INTO ventas VALUES (1);\n" * 300, encoding="utf-8")
    conn = sqlite3.connect(usb / "CobroFacil_Nodo" / "contabilidad_jefe.db")
    conn.execute("CREATE TABLE asientos (id INTEGER)")
    conn.close()
    (usb / "respaldos" / "backup_diario_2026-09-20.zip").write_bytes(b"no es zip" * 10000)
    (usb / "respaldos" / "viejo.sql.bad_corrupt").write_text("x")

    fuentes = restaurar.buscar(str(usb))
    assert [f.tipo for f in fuentes] == ["copia", "sql"]
    assert fuentes[0].detalle == "pendrive" and fuentes[0].completa and fuentes[0].servidor == "MAESTRA"
    assert fuentes[1].fecha == dt.datetime(2026, 9, 20, 10, 10, 10)


def test_suma_agrega_lo_que_falta_sin_pisar(tmp_path):
    fuente = restaurar.analizar(_copia(tmp_path / "espejo_tienda.db"))
    destino = _tienda(tmp_path / "punpro.db")
    assert restaurar.modo(fuente, destino) == "suma"

    res = restaurar.aplicar.sumar(fuente.ruta, destino)

    conn = sqlite3.connect(destino.archivo)
    assert conn.execute("SELECT stock FROM productos WHERE id=1").fetchone()[0] == 5
    assert conn.execute("SELECT nombre FROM productos WHERE id=2").fetchone()[0] == "Leche"
    ventas = dict(conn.execute("SELECT request_id, id FROM ventas").fetchall())
    assert set(ventas) == {"A", "B", "C", "Z"}
    assert ventas["Z"] == 3 and ventas["C"] not in (1, 2, 3)
    nuevo = ventas["C"]
    assert conn.execute("SELECT nombre_producto FROM detalles_ventas WHERE id_venta=?", (nuevo,)).fetchone()[0] == "Asado"
    assert conn.execute("SELECT nombre_producto FROM detalles_ventas WHERE id=12").fetchone()[0] == "Chorizo"
    assert conn.execute("SELECT COUNT(*) FROM detalles_ventas").fetchone()[0] == 4
    assert conn.execute("SELECT nombre FROM usuarios").fetchone()[0] == "jefe"
    conn.close()
    assert res["renumeradas"] == 1
    assert res["tablas"]["ventas"] == {"sumadas": 2, "ya_estaban": 1}
    assert "solo_en_copia" in res["sin_lugar"]

    otra = restaurar.aplicar.sumar(fuente.ruta, destino)
    assert otra["tablas"]["ventas"]["sumadas"] == 0 and otra["renumeradas"] == 0
    conn = sqlite3.connect(destino.archivo)
    assert conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 4
    conn.close()


def test_suma_es_todo_o_nada(tmp_path):
    fuente = restaurar.analizar(_copia(tmp_path / "espejo_tienda.db"))
    destino = _tienda(tmp_path / "punpro.db")
    conn = sqlite3.connect(destino.archivo)
    conn.execute("CREATE TRIGGER no BEFORE INSERT ON usuarios BEGIN SELECT RAISE(ABORT, 'rota'); END")
    conn.commit()
    conn.close()
    with pytest.raises(sqlite3.Error):
        restaurar.aplicar.sumar(fuente.ruta, destino)
    conn = sqlite3.connect(destino.archivo)
    assert conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 1
    conn.close()


def test_revisar_avisa_y_bloquea(tmp_path, monkeypatch):
    copia = restaurar.analizar(_copia(tmp_path / "a.db", servidor="PRUEBA", completa="", ultima="2026-01-02 08:00:00"))
    maria = Destino("mariadb", host="192.168.0.50", servidor="NEGOCIO")
    bloqueos, avisos = restaurar.revisar(copia, maria)
    texto = " ".join(avisos)
    assert not bloqueos
    assert "otra maestra (PRUEBA)" in texto and "parcial" in texto and "02/01/2026" in texto

    zipf = restaurar.Fuente(str(tmp_path / "backup_x.zip"), "zip", dt.datetime.now(), True)
    monkeypatch.setattr(motor, "_mysql_exe", lambda: str(tmp_path / "no_esta.exe"))
    assert "sentado en la maestra" in restaurar.revisar(zipf, maria)[0][0]
    sqlf = restaurar.Fuente(str(tmp_path / "r.sql"), "sql", dt.datetime.now(), True)
    assert "mysql.exe" in restaurar.revisar(sqlf, maria)[0][0]
    assert "SQLite" in restaurar.revisar(sqlf, Destino("sqlite", archivo="x.db"))[0][0]


def test_restaurar_con_bloqueo_no_toca_nada(tmp_path):
    zipf = restaurar.Fuente(str(tmp_path / "backup_x.zip"), "zip", dt.datetime.now(), True)
    with pytest.raises(RuntimeError, match="SQLite"):
        restaurar.restaurar(zipf, Destino("sqlite", archivo=str(tmp_path / "p.db")))
    assert not os.path.exists(tmp_path / "p.db")


def test_restaurar_suma_saca_foto_antes(tmp_path, monkeypatch):
    pasos = []
    monkeypatch.setattr(motor, "_foto_antes", lambda d: pasos.append("foto"))
    monkeypatch.setattr(motor, "_respaldo_despues", lambda d: pasos.append("respaldo"))
    fuente = restaurar.analizar(_copia(tmp_path / "espejo_tienda.db"))
    res = restaurar.restaurar(fuente, _tienda(tmp_path / "punpro.db"))
    assert pasos == ["foto", "respaldo"] and res["modo"] == "suma"


def test_copia_del_espejo_se_puede_restaurar(tmp_path, monkeypatch):
    """La copia que arma el espejo (y va al pendrive) es una fuente válida del motor."""
    from tests.test_espejo_tienda import TiendaFalsa
    from src.jefe.nodo_portable.espejo import copia

    monkeypatch.setattr(copia, "carpeta", lambda: str(tmp_path / "espejo"))
    monkeypatch.setattr(copia, "_salud", {"hasta": 0.0, "rota": ""})
    t = TiendaFalsa()
    t.db.execute("INSERT INTO ventas (id, fecha, total, estado) VALUES (1, ?, 10, 'COMPLETADA')", (HOY,))
    t.db.execute("INSERT INTO usuarios VALUES (1, 'jefe', 'ADMIN')")
    t.db.commit()
    monkeypatch.setattr(copia, "_conectar_tienda", lambda: t)
    copia.refrescar()
    destino_pendrive = tmp_path / "USB" / "CobroFacil_Nodo" / "nodo_negocio.db"
    destino_pendrive.parent.mkdir(parents=True)
    copia.volcar_a(str(destino_pendrive))

    fuentes = restaurar.buscar(str(tmp_path / "USB"))
    assert len(fuentes) == 1 and fuentes[0].completa and fuentes[0].servidor == "MAESTRA-PRUEBA"
