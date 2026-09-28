"""Huella de clientes: casa (sin red) → pendrive → tienda. Sin red real: dos SQLite en tmp."""

import json
import sqlite3

import pytest

from src.clientes_fiado.oficina.huella import absorber, consulta, eventos, tabla
from src.clientes_fiado.oficina.huella import pc as huella_pc

ESQUEMA = """
CREATE TABLE clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, telefono TEXT, email TEXT, dni TEXT,
    direccion TEXT, limite_credito REAL DEFAULT 0, deuda_actual REAL DEFAULT 0, tipo_cliente TEXT
);
CREATE TABLE cuenta_corriente (
    id INTEGER PRIMARY KEY AUTOINCREMENT, cliente_id INTEGER, fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    tipo TEXT, monto REAL, saldo_resultante REAL, descripcion TEXT, venta_id INTEGER
);
"""


class BaseFalsa:
    """Imita a db_manager sobre un archivo SQLite."""

    db_engine_type = "sqlite"

    def __init__(self, path, tienda):
        self.path = str(path)
        self.tienda = tienda
        con = sqlite3.connect(self.path)
        con.executescript(ESQUEMA)
        con.close()

    def get_connection(self):
        con = sqlite3.connect(self.path)
        con.row_factory = lambda c, r: {d[0]: r[i] for i, d in enumerate(c.description)}
        return con

    def execute_query(self, sql, params=()):
        con = self.get_connection()
        try:
            return con.execute(sql, params).fetchall()
        except Exception:
            return []
        finally:
            con.close()

    def execute_non_query(self, sql, params=()):
        con = self.get_connection()
        try:
            con.execute(sql, params)
            con.commit()
            return True
        except Exception:
            return False
        finally:
            con.close()


@pytest.fixture
def bases(tmp_path, monkeypatch):
    tienda = BaseFalsa(tmp_path / "tienda.db", tienda=True)
    casa = BaseFalsa(tmp_path / "punpro_casa.db", tienda=False)
    actual = {"db": casa}

    def _db():
        return actual["db"]

    for modulo in (eventos, tabla, absorber, consulta):
        monkeypatch.setattr(modulo, "_db", _db)
    monkeypatch.setattr(tabla, "es_tienda", lambda db=None: (db or actual["db"]).tienda)
    monkeypatch.setattr(huella_pc, "usuario", lambda: "cesar")
    monkeypatch.setattr(huella_pc, "caja", lambda: "1")
    tabla.olvidar()
    return tienda, casa, actual


def _uno(db, sql, params=()):
    filas = db.execute_query(sql, params)
    return filas[0] if filas else None


def _cargo_en(db, cliente_id, monto, accion="CARGO", desc="Saldo inicial"):
    con = db.get_connection()
    cur = con.cursor()
    signo = 1 if accion == "CARGO" else -1
    cur.execute("UPDATE clientes SET deuda_actual = deuda_actual + ? WHERE id = ?", (signo * monto, cliente_id))
    assert eventos.movimiento_en(cur, accion, cliente_id, monto, desc)
    con.commit()
    con.close()


def _alta_casa(actual, casa, nombre="Juan Perez", dni="30111222"):
    actual["db"] = casa
    assert eventos.alta(
        {"nombre": nombre, "telefono": "11", "limite_credito": 20000, "dni": dni, "tipo_cliente": "regular"},
        via="cartera",
    )
    return _uno(casa, "SELECT * FROM clientes WHERE nombre = ?", (nombre,))


# ── Identidad ────────────────────────────────────────────────────────────────

def test_uid_dice_pc_y_hora():
    uid = huella_pc.nuevo_uid()
    assert uid.startswith(huella_pc.pc_id() + "-")
    assert len(uid) <= 64
    assert huella_pc.nuevo_uid() != uid


def test_pc_id_es_estable():
    assert huella_pc.pc_id() == huella_pc.pc_id()


# ── Casa: alta y movimientos quedan sellados ─────────────────────────────────

def test_alta_en_casa_queda_sellada(bases):
    _tienda, casa, actual = bases
    c = _alta_casa(actual, casa)
    assert c["uid"].startswith(huella_pc.pc_id())
    assert c["origen_pc"] == huella_pc.pc_id()
    assert c["creado_por"] == "cesar"
    assert c["creado_en"]
    ev = _uno(casa, "SELECT * FROM clientes_auditoria WHERE accion = 'ALTA'")
    assert ev["base"] == "LOCAL" and ev["llego_via"] is None
    assert json.loads(ev["detalle"])["ficha"]["dni"] == "30111222"


# ── Tienda chupa ─────────────────────────────────────────────────────────────

def test_cliente_de_casa_llega_con_saldo_y_no_se_duplica(bases):
    tienda, casa, actual = bases
    c = _alta_casa(actual, casa)
    _cargo_en(casa, c["id"], 5000)

    actual["db"] = tienda
    r1 = absorber.aplicar(absorber.leer_eventos(casa.path), "NODO", tienda)
    assert r1["aplicado"] == 2

    t = _uno(tienda, "SELECT * FROM clientes WHERE uid = ?", (c["uid"],))
    assert t["nombre"] == "Juan Perez"
    assert t["deuda_actual"] == 5000
    assert t["origen_pc"] == huella_pc.pc_id() and t["creado_por"] == "cesar"
    mov = _uno(tienda, "SELECT * FROM cuenta_corriente WHERE cliente_id = ?", (t["id"],))
    assert mov["tipo"] == "CARGO" and mov["monto"] == 5000
    assert "cargado en" in mov["descripcion"]

    r2 = absorber.aplicar(absorber.leer_eventos(casa.path), "NODO", tienda)
    assert r2["aplicado"] == 0 and r2["repetido"] == 2
    assert _uno(tienda, "SELECT deuda_actual FROM clientes WHERE uid = ?", (c["uid"],))["deuda_actual"] == 5000
    assert len(tienda.execute_query("SELECT * FROM clientes")) == 1


def test_mismo_dni_se_une_y_suma_el_cargo(bases):
    tienda, casa, actual = bases
    actual["db"] = tienda
    tabla.asegurar(tienda)
    tienda.execute_non_query(
        "INSERT INTO clientes (nombre, dni, deuda_actual, uid) VALUES ('Juan P.', '30111222', 1000, 'TIENDA-1')"
    )
    c = _alta_casa(actual, casa)
    _cargo_en(casa, c["id"], 500)

    actual["db"] = tienda
    absorber.aplicar(absorber.leer_eventos(casa.path), "NODO", tienda)
    assert len(tienda.execute_query("SELECT * FROM clientes")) == 1
    assert _uno(tienda, "SELECT deuda_actual FROM clientes WHERE uid = 'TIENDA-1'")["deuda_actual"] == 1500
    fus = _uno(tienda, "SELECT * FROM clientes_auditoria WHERE accion = 'FUSION'")
    assert fus["cliente_uid"] == c["uid"]


def test_edicion_vieja_no_pisa_a_la_tienda(bases):
    tienda, _casa, actual = bases
    actual["db"] = tienda
    tabla.asegurar(tienda)
    tienda.execute_non_query(
        "INSERT INTO clientes (nombre, telefono, uid, actualizado_en) VALUES ('Ana', '999', 'U1', '2026-09-27 10:00:00')"
    )
    base = {"cliente_uid": "U1", "nombre": "Ana", "pc": "CASA-1", "caja": "", "usuario": "cesar", "base": "LOCAL",
            "cliente_id": 7, "llego_en": None, "llego_via": None, "accion": "EDICION"}
    vieja = dict(base, evento="E-VIEJA", fecha="2026-09-26 21:00:00",
                 detalle=json.dumps({"antes": {"telefono": "1"}, "despues": {"telefono": "111"}}))
    nueva = dict(base, evento="E-NUEVA", fecha="2026-09-28 09:00:00",
                 detalle=json.dumps({"antes": {"telefono": "999"}, "despues": {"telefono": "222"}}))
    assert absorber.aplicar_evento(vieja, "NODO", tienda) == "aplicado"
    assert _uno(tienda, "SELECT telefono FROM clientes WHERE uid = 'U1'")["telefono"] == "999"
    assert _uno(tienda, "SELECT llego_via FROM clientes_auditoria WHERE evento = 'E-VIEJA'")["llego_via"] == \
        "NODO:TIENDA_MAS_NUEVA"
    assert absorber.aplicar_evento(nueva, "NODO", tienda) == "aplicado"
    assert _uno(tienda, "SELECT telefono FROM clientes WHERE uid = 'U1'")["telefono"] == "222"


def test_evento_de_cliente_que_no_llego_queda_pendiente(bases):
    tienda, _casa, actual = bases
    actual["db"] = tienda
    tabla.asegurar(tienda)
    ev = {"evento": "E-HUERFANO", "fecha": "2026-09-26 21:00:00", "accion": "CARGO", "cliente_uid": "NADIE",
          "cliente_id": 1, "nombre": "x", "pc": "CASA-1", "caja": "", "usuario": "cesar", "base": "LOCAL",
          "detalle": json.dumps({"monto": 100}), "llego_en": None, "llego_via": None}
    assert absorber.aplicar_evento(ev, "NODO", tienda) == "pendiente"
    assert _uno(tienda, "SELECT * FROM clientes_auditoria WHERE evento = 'E-HUERFANO'") is None


def test_abono_no_deja_deuda_negativa(bases):
    tienda, casa, actual = bases
    c = _alta_casa(actual, casa)
    _cargo_en(casa, c["id"], 300)
    _cargo_en(casa, c["id"], 1000, accion="ABONO", desc="Pagó")
    actual["db"] = tienda
    absorber.aplicar(absorber.leer_eventos(casa.path), "NODO", tienda)
    assert _uno(tienda, "SELECT deuda_actual FROM clientes WHERE uid = ?", (c["uid"],))["deuda_actual"] == 0


def test_casa_deja_eventos_en_el_pendrive_y_la_tienda_los_toma(bases, tmp_path):
    tienda, casa, actual = bases
    nodo = tmp_path / "nodo_negocio.db"
    sqlite3.connect(nodo).close()
    c = _alta_casa(actual, casa)
    assert absorber.llevar_al_nodo(str(nodo), casa) == 1
    assert absorber.llevar_al_nodo(str(nodo), casa) == 0
    actual["db"] = tienda
    r = absorber.aplicar(absorber.leer_eventos(str(nodo)), "NODO", tienda)
    assert r["aplicado"] == 1
    ev = _uno(tienda, "SELECT * FROM clientes_auditoria WHERE accion = 'ALTA'")
    assert ev["llego_via"] == "NODO" and ev["llego_en"]
    assert _uno(tienda, "SELECT uid FROM clientes")["uid"] == c["uid"]


def test_en_tienda_el_evento_es_directo(bases):
    tienda, _casa, actual = bases
    actual["db"] = tienda
    assert eventos.alta({"nombre": "Directo", "dni": "", "limite_credito": 0, "tipo_cliente": "regular"}, via="cartera")
    ev = _uno(tienda, "SELECT * FROM clientes_auditoria")
    assert ev["base"] == "TIENDA" and ev["llego_via"] == "DIRECTO"
    assert absorber.leer_eventos(tienda.path) == []


def test_editar_guarda_antes_y_despues_y_no_toca_deuda(bases):
    tienda, _casa, actual = bases
    actual["db"] = tienda
    eventos.alta({"nombre": "Luis", "telefono": "1", "dni": "", "limite_credito": 100, "tipo_cliente": "regular"},
                 via="cartera")
    cid = _uno(tienda, "SELECT id FROM clientes")["id"]
    assert eventos.editar(cid, {"telefono": "2", "deuda_actual": 999999})
    fila = _uno(tienda, "SELECT * FROM clientes WHERE id = ?", (cid,))
    assert fila["telefono"] == "2" and fila["deuda_actual"] == 0
    ev = _uno(tienda, "SELECT * FROM clientes_auditoria WHERE accion = 'EDICION'")
    assert json.loads(ev["detalle"]) == {"antes": {"telefono": "1"}, "despues": {"telefono": "2"}}


# ── Pantalla ─────────────────────────────────────────────────────────────────

def test_resumen_y_llegada_se_leen():
    assert "límite $20.000,00" in consulta.resumen(
        {"accion": "ALTA", "detalle": json.dumps({"via": "cartera", "ficha": {"limite_credito": 20000}})})
    assert consulta.resumen(
        {"accion": "EDICION", "detalle": json.dumps({"antes": {"telefono": "1"}, "despues": {"telefono": "2"}})}
    ) == "telefono: 1 → 2"
    assert consulta.llegada({"llego_via": "NODO", "llego_en": "2026-09-27 08:10:00"}) == "Pendrive · 27/09/2026 08:10"
    assert "no aplicado" in consulta.llegada({"llego_via": "NODO:TIENDA_MAS_NUEVA"})


def test_huella_texto():
    assert "Creado en CASA-1 por cesar" in consulta.huella_texto(
        {"uid": "CASA-1-x", "origen_pc": "CASA-1", "creado_por": "cesar", "creado_en": "2026-09-26 21:57:00"})
    assert "antes de la huella" in consulta.huella_texto({"uid": "TIENDA-5"})


def test_nodo_viejo_recibe_columnas_y_libro(tmp_path):
    from src.jefe.nodo_portable.motor_nodo import _ensure_negocio_schema

    con = sqlite3.connect(tmp_path / "viejo.db")
    con.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nombre TEXT)")
    _ensure_negocio_schema(con)
    cols = {r[1] for r in con.execute("PRAGMA table_info(clientes)")}
    assert {"uid", "origen_pc", "creado_por", "creado_en", "actualizado_en"} <= cols
    assert con.execute("SELECT COUNT(*) FROM clientes_auditoria").fetchone()[0] == 0
    con.close()
