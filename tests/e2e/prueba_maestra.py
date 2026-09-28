"""
Prueba de punta a punta contra una maestra de PRUEBA (MariaDB). Escribe y después borra lo suyo.

    python tests/e2e/prueba_maestra.py --host 192.168.0.13

No correr contra la maestra del negocio. Ver tests/e2e/README.md.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from datetime import datetime

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, RAIZ)

MARCA = "PRUEBA E2E"
DNI_TIENDA = "99000111"
DNI_CASA = "99000222"
PC_CASA = "CASA-E2E"

fallas: list[str] = []


def ver(nombre: str, ok: bool, detalle="") -> None:
    print(f"  {'OK   ' if ok else 'FALLA'} {nombre}" + (f"  ({detalle})" if detalle else ""))
    if not ok:
        fallas.append(nombre)


def uno(db, sql, params=()):
    filas = db.execute_query(sql, params) or []
    return dict(filas[0]) if filas else {}


def conectar(host: str):
    from src.base_de_datos.database import db_manager

    if getattr(db_manager, "db_engine_type", "") != "mariadb" or host not in str(getattr(db_manager, "db_path", "")):
        db_manager.reconectar_mariadb(host)
    if db_manager.db_engine_type != "mariadb":
        raise SystemExit(f"No hay MariaDB en {host}")
    return db_manager


def esquema(db) -> None:
    print("\n1. Esquema (lo que hace la maestra al arrancar + huella)")
    db._create_tables()
    db._migrate_db()
    from src.clientes_fiado.oficina.huella import tabla

    tabla.olvidar()
    ver("huella: columnas, índice y clientes_auditoria", tabla.asegurar(db))
    cols = {dict(r)["Field"] for r in db.execute_query("SHOW COLUMNS FROM clientes")}
    faltan = {"uid", "origen_pc", "creado_por", "creado_en", "actualizado_en"} - cols
    ver("clientes tiene las 5 columnas de huella", not faltan, ", ".join(sorted(faltan)))
    idx = db.execute_query("SHOW INDEX FROM clientes WHERE Key_name = 'ux_clientes_uid'")
    ver("índice único ux_clientes_uid", bool(idx))
    cc = {dict(r)["Field"] for r in db.execute_query("SHOW COLUMNS FROM cuenta_corriente")}
    ver("cuenta_corriente tiene saldo_resultante", "saldo_resultante" in cc)


def cartera(db) -> int:
    print("\n2. Cartera en la tienda (alta, ficha, límite, cargo, abono)")
    from src.clientes_fiado.cerebro.cerebro import cerebro

    m = cerebro.cuenta
    m.alta_regular(f"{MARCA} Tienda", "111", 5000, DNI_TIENDA)
    c = uno(db, "SELECT * FROM clientes WHERE dni = ?", (DNI_TIENDA,))
    cid = c.get("id")
    ver("alta con uid y PC", bool(c.get("uid")) and bool(c.get("origen_pc")), c.get("uid"))
    m.actualizar_ficha(cid, f"{MARCA} Tienda", DNI_TIENDA, "222", "Calle 1", "regular")
    m.fijar_limite(cid, 8000)
    m.cargar_manual(cid, 1500, "cargo de prueba")
    m.abonar(cid, 500, "abono de prueba", medio="Efectivo", perfil="jefe", quien="e2e")
    c = uno(db, "SELECT * FROM clientes WHERE id = ?", (cid,))
    ver("deuda = 1500 - 500", abs(float(c.get("deuda_actual") or 0) - 1000) < 0.01, c.get("deuda_actual"))
    ver("límite 8000", abs(float(c.get("limite_credito") or 0) - 8000) < 0.01)
    acciones = [dict(r)["accion"] for r in db.execute_query(
        "SELECT accion FROM clientes_auditoria WHERE cliente_uid = ? ORDER BY evento", (c.get("uid"),))]
    esperadas = ["ALTA", "EDICION", "LIMITE", "CARGO", "ABONO"]
    ver("libro: ALTA, EDICION, LIMITE, CARGO, ABONO", sorted(acciones) == sorted(esperadas), acciones)
    return cid


def _evento(accion, uid, detalle, n):
    from src.clientes_fiado.oficina.huella import pc

    return {
        "evento": f"{PC_CASA}-{pc.nuevo_evento().split('-', 2)[-1]}-{n}",
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accion": accion, "cliente_uid": uid, "cliente_id": None, "nombre": f"{MARCA} Casa",
        "pc": PC_CASA, "caja": "1", "usuario": "jefe", "base": "LOCAL",
        "detalle": json.dumps(detalle), "llego_en": None, "llego_via": None,
    }


def casa(db, cid_tienda: int, carpeta: str) -> str:
    print("\n3. Cargado en casa sin red → la tienda lo toma")
    from src.clientes_fiado.oficina.huella import absorber, tabla

    u1, u2, u9 = f"{PC_CASA}-U1", f"{PC_CASA}-U2", f"{PC_CASA}-U9"
    eventos = [
        _evento("ALTA", u1, {"ficha": {"nombre": f"{MARCA} Casa", "dni": DNI_CASA, "telefono": "9",
                                        "limite_credito": 3000}}, 1),
        _evento("CARGO", u1, {"monto": 2000, "descripcion": "saldo inicial"}, 2),
        _evento("ABONO", u1, {"monto": 500, "descripcion": "pagó en casa"}, 3),
        _evento("EDICION", u1, {"antes": {"telefono": "9"}, "despues": {"telefono": "333"}}, 4),
        _evento("ALTA", u2, {"ficha": {"nombre": f"{MARCA} Tienda", "dni": DNI_TIENDA}}, 5),
        _evento("CARGO", u2, {"monto": 100, "descripcion": "fiado en casa"}, 6),
        _evento("CARGO", u9, {"monto": 999, "descripcion": "cliente que no llegó"}, 7),
    ]
    archivo = os.path.join(carpeta, "casa.db")
    conn = sqlite3.connect(archivo)
    conn.execute(tabla.DDL_EVENTOS)
    cols = tabla.COLUMNAS_EVENTO
    conn.executemany(f"INSERT INTO clientes_auditoria ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                     [tuple(e[c] for c in cols) for e in eventos])
    conn.commit()
    conn.close()

    r1 = absorber.aplicar(absorber.leer_eventos(archivo), "NODO", db)
    ver("primera vuelta: 6 aplicados, 1 pendiente", r1 == {"aplicado": 6, "repetido": 0, "pendiente": 1, "error": 0}, r1)
    r2 = absorber.aplicar(absorber.leer_eventos(archivo), "NODO", db)
    ver("segunda vuelta: nada dos veces", r2 == {"aplicado": 0, "repetido": 6, "pendiente": 1, "error": 0}, r2)
    c = uno(db, "SELECT * FROM clientes WHERE dni = ?", (DNI_CASA,))
    ver("cliente de casa con deuda 1500", abs(float(c.get("deuda_actual") or 0) - 1500) < 0.01, c.get("deuda_actual"))
    ver("cliente de casa con su uid y PC", c.get("uid") == u1 and c.get("origen_pc") == PC_CASA)
    ver("edición de casa aplicada", str(c.get("telefono")) == "333", c.get("telefono"))
    t = uno(db, "SELECT deuda_actual FROM clientes WHERE id = ?", (cid_tienda,))
    ver("mismo DNI → fusión, cargo al de la tienda (1000+100)", abs(float(t.get("deuda_actual") or 0) - 1100) < 0.01,
        t.get("deuda_actual"))
    n = uno(db, "SELECT COUNT(*) AS n FROM clientes WHERE dni IN (?, ?)", (DNI_TIENDA, DNI_CASA)).get("n")
    ver("sin clientes duplicados", int(n or 0) == 2, n)
    return archivo


def venta(db) -> int:
    print("\n4. Venta en la tienda")
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute_non_query(
        "INSERT INTO ventas (fecha, total, usuario, estado, metodo_pago, caja_id, cliente_nombre) "
        "VALUES (?, 1234.5, 'e2e', 'COMPLETADA', 'QR', 1, ?)", (ahora, MARCA))
    vid = uno(db, "SELECT MAX(id) AS id FROM ventas WHERE cliente_nombre = ?", (MARCA,)).get("id")
    from src.jefe.vitrina import metricas

    cant, total = metricas.tickets()
    ver("vitrina en vivo ve la venta", cant >= 1 and total >= 1234.5, (cant, total))
    return int(vid)


def copia_y_nodo(db, carpeta: str) -> None:
    print("\n5. Copia de la tienda en esta PC y pendrive")
    from src.jefe.nodo_portable import motor_nodo
    from src.jefe.nodo_portable.espejo import copia, lector

    copia.carpeta = lambda: os.path.join(carpeta, "espejo")
    res = copia.refrescar(completo=True)
    ver("copia completa", res.get("estado") == "ok", res.get("detalle") or res.get("ventas"))
    ver("tienda sana (no rota)", copia.tienda_rota() == "")
    lector._hay_tienda = lambda: False
    lector._ruta_lectura = lambda: copia.ruta()
    from src.jefe.vitrina import metricas

    cant, total = metricas.tickets()
    ver("sin red, la vitrina lee la copia", cant >= 1 and total >= 1234.5, (cant, total))
    ver("deuda de clientes en la copia", metricas.deuda_clientes() >= 2600, metricas.deuda_clientes())
    ver("franja ámbar", "Sin red" in lector.leyenda(), lector.leyenda())

    root = os.path.join(carpeta, "USB", motor_nodo.NODO_DIR_NAME)
    os.makedirs(root)
    sqlite3.connect(os.path.join(root, motor_nodo.NODO_NEGOCIO)).close()
    motor_nodo._save_meta(root, {"version": 2})
    motor_nodo._sync_catalogos_dir = lambda *a, **k: None
    stats = motor_nodo.sincronizar_faltantes(path=root)
    ver("sincronizar al pendrive", bool(stats.get("copia_de")) and not stats.get("aviso"), stats)
    conn = sqlite3.connect(os.path.join(root, motor_nodo.NODO_NEGOCIO))
    n = conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
    modo = conn.execute("PRAGMA journal_mode").fetchone()[0]
    conn.close()
    ver("pendrive con ventas y modo DELETE", n >= 1 and modo == "delete", (n, modo))


def limpiar(db, vid) -> None:
    print("\n6. Limpieza")
    ids = [dict(r)["id"] for r in db.execute_query("SELECT id FROM clientes WHERE dni IN (?, ?)", (DNI_TIENDA, DNI_CASA))]
    for cid in ids:
        db.execute_non_query("DELETE FROM cuenta_corriente WHERE cliente_id = ?", (cid,))
    db.execute_non_query("DELETE FROM clientes_auditoria WHERE nombre LIKE ? OR pc = ? OR cliente_uid LIKE ?",
                         (f"{MARCA}%", PC_CASA, f"{PC_CASA}%"))
    db.execute_non_query("DELETE FROM clientes WHERE dni IN (?, ?)", (DNI_TIENDA, DNI_CASA))
    if vid:
        db.execute_non_query("DELETE FROM ventas WHERE id = ?", (vid,))
    quedan = uno(db, "SELECT COUNT(*) AS n FROM clientes WHERE nombre LIKE ?", (f"{MARCA}%",)).get("n")
    ver("sin rastros de la prueba", int(quedan or 0) == 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", required=True, help="IP de la maestra de PRUEBA")
    host = ap.parse_args().host
    db = conectar(host)
    print(f"Maestra de prueba: {host}")
    carpeta = tempfile.mkdtemp(prefix="e2e_tpv_")
    vid = None
    try:
        esquema(db)
        cid = cartera(db)
        casa(db, cid, carpeta)
        vid = venta(db)
        copia_y_nodo(db, carpeta)
    finally:
        limpiar(db, vid)
        shutil.rmtree(carpeta, ignore_errors=True)
    print("\nRESULTADO:", "TODO OK" if not fallas else f"{len(fallas)} FALLA(S): {fallas}")
    sys.exit(1 if fallas else 0)


if __name__ == "__main__":
    main()
