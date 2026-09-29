import pytest

from src.cerebro_global.proveedor.motor_proveedor import MotorProveedor


class DbTiendaFalsa:
    db_engine_type = "mariadb"
    _forced_local_offline = False

    def __init__(self, filas=None):
        self.filas = filas or []
        self.queries = []
        self.escrituras = []

    def execute_query(self, sql, params=()):
        self.queries.append(sql)
        return self.filas

    def execute_non_query(self, sql, params=()):
        self.escrituras.append((sql, params))
        return True


class CopiaProveedorFalsa:
    def execute_query(self, sql, params=()):
        if "SELECT DISTINCT proveedor FROM romaneos" in sql:
            return [{"proveedor": "Frigorífico Nodo"}]
        if "SELECT descripcion FROM gastos" in sql:
            return []
        if "FROM gastos WHERE categoria" in sql:
            return [{
                "id": 43,
                "fecha": "2026-09-28",
                "descripcion": "Proveedor: Frigorífico Nodo\nTropa: 2",
                "monto": 12500,
                "status": "Pendiente",
            }]
        return []


def test_admin_consulta_la_copia_del_nodo_sin_red(monkeypatch):
    from src.jefe.nodo_portable import espejo

    copia = CopiaProveedorFalsa()
    monkeypatch.setattr(MotorProveedor, "_get_db", staticmethod(lambda *_: DbTiendaFalsa()))
    monkeypatch.setattr(MotorProveedor, "tienda_disponible", staticmethod(lambda: False))
    monkeypatch.setattr(espejo, "en_copia", lambda: "nodo_negocio.db")
    monkeypatch.setattr(espejo, "fuente", lambda: copia)

    proveedor, modo = MotorProveedor._get_read_db("admin")
    assert proveedor is copia and modo == "copia"
    assert MotorProveedor.get_proveedores_unicos("admin") == ["Frigorífico Nodo"]
    compras = MotorProveedor.load_proveedores("admin")
    assert len(compras) == 1
    assert compras[0]["proveedor"] == "Frigorífico Nodo"
    assert compras[0]["restante"] == 12500


def test_admin_sin_nodo_no_lee_punpro_como_respaldo(monkeypatch):
    from src.jefe.nodo_portable import espejo

    local_punpro = DbTiendaFalsa([{"id": 43}])
    monkeypatch.setattr(MotorProveedor, "_get_db", staticmethod(lambda *_: local_punpro))
    monkeypatch.setattr(MotorProveedor, "tienda_disponible", staticmethod(lambda: False))
    monkeypatch.setattr(espejo, "en_copia", lambda: "")
    monkeypatch.setattr(espejo.copia, "existe", lambda: False)

    db, modo = MotorProveedor._get_read_db("admin")
    assert db is None
    assert modo == "sin_copia"
    assert MotorProveedor.load_proveedores("admin") == []


def test_admin_usa_espejo_interno_si_no_hay_nodo_usb(monkeypatch):
    from src.jefe.nodo_portable import espejo

    copia = CopiaProveedorFalsa()
    monkeypatch.setattr(MotorProveedor, "_get_db", staticmethod(lambda *_: DbTiendaFalsa()))
    monkeypatch.setattr(MotorProveedor, "tienda_disponible", staticmethod(lambda: False))
    monkeypatch.setattr(espejo, "en_copia", lambda: "")
    monkeypatch.setattr(espejo.copia, "existe", lambda: True)
    monkeypatch.setattr(espejo.copia, "ruta", lambda: "espejo_tienda.db")
    monkeypatch.setattr(espejo.lector, "Lector", lambda _path: copia)

    db, modo = MotorProveedor._get_read_db("admin")
    assert db is copia and modo == "copia"


def test_jefe_conserva_lectura_de_su_contabilidad_portatil(monkeypatch):
    class DbJefeFalsa:
        def get_general_debts(self):
            return [(9, "Proveedor: Local\nDetalle", "Proveedor", 700, "2026-09-20", "pending", 0)]

    jefe = DbJefeFalsa()
    monkeypatch.setattr(MotorProveedor, "tienda_disponible", staticmethod(lambda: False))

    db, modo = MotorProveedor._get_read_db("jefe", jefe)
    assert db is jefe and modo == "local"
    assert MotorProveedor.load_proveedores("jefe", jefe)[0]["proveedor"] == "Local"


def test_compras_y_pagos_offline_se_bloquean_sin_escrituras(monkeypatch):
    db = DbTiendaFalsa()
    monkeypatch.setattr(MotorProveedor, "_get_db", staticmethod(lambda *_: db))

    result = MotorProveedor.save_proveedor(
        "2026-09-29", "Proveedor", "Lote 1", {("Cerdo", 100): [("1", 5)]},
        "Contado (Pago Inmediato)", 500, "admin",
    )
    assert result[0] is False
    assert "Solo consulta" in result[1]
    assert db.escrituras == []

    with pytest.raises(RuntimeError, match="requieren conexión"):
        MotorProveedor.pagar_proveedor(43, 500, "admin")
    assert db.escrituras == []


def test_compra_no_reintenta_en_sqlite_si_mariadb_se_cae(monkeypatch):
    from src.base_de_datos.database import db_manager

    llamadas = []

    class CursorConexion:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, *_args):
            pass

        def fetchone(self):
            return {"conectada": 1}

    def conexion_sin_tienda(**kwargs):
        llamadas.append(kwargs)
        if len(llamadas) == 1:
            return type(
                "ConexionProbe",
                (),
                {"cursor": lambda _self: CursorConexion(), "close": lambda _self: None},
            )()
        raise OSError("MariaDB dejó de responder")

    monkeypatch.setattr(db_manager, "db_engine_type", "mariadb")
    monkeypatch.setattr(db_manager, "_forced_local_offline", False)
    monkeypatch.setattr(db_manager, "get_connection", conexion_sin_tienda)
    monkeypatch.setattr(db_manager, "execute_non_query", lambda *_args, **_kwargs: pytest.fail(
        "La compra no debe usar el ejecutor con fallback a SQLite"
    ))

    result = MotorProveedor.save_proveedor(
        "2026-09-29", "Proveedor", "Lote 1", {("Cerdo", 100): [("1", 5)]},
        "Contado (Pago Inmediato)", 500, "admin",
    )

    assert result[0] is False
    assert llamadas == [{"caer_si_maestra_caida": False}] * 2
