import json
import os
import sqlite3
import pytest
from unittest.mock import MagicMock
from src.base_de_datos.offline_nutricion import OfflineNutricionManager
from src.base_de_datos.offline_sync import offline_sync_manager


@pytest.fixture
def temp_nutricion(tmp_path):
    mgr = OfflineNutricionManager()
    mgr.base_path = str(tmp_path)
    mgr.outbox_file = os.path.join(str(tmp_path), "offline_cambios.json")
    mgr._ensure_file()
    return mgr


def test_encolar_producto_offline(temp_nutricion):
    prod_data = {
        "codigo": "7791234567890",
        "nombre": "Yerba Mate 1kg",
        "precio": 2500.0,
        "costo": 1800.0,
        "stock": 45.0,
        "departamento": "ALMACEN"
    }
    assert temp_nutricion.encolar_producto(prod_data) is True

    resumen = temp_nutricion.obtener_resumen_pendientes()
    assert resumen["productos"] == 1
    assert resumen["total"] == 1

    # Actualizar producto existente en la cola (idéntico código)
    prod_data_edit = dict(prod_data, precio=2700.0)
    temp_nutricion.encolar_producto(prod_data_edit)

    resumen2 = temp_nutricion.obtener_resumen_pendientes()
    assert resumen2["productos"] == 1  # No se duplica, se actualiza el registro en cola

    cola = temp_nutricion._leer_cola()
    assert cola["productos"][0]["datos"]["precio"] == 2700.0


def test_encolar_recepcion_offline(temp_nutricion):
    items = [
        {"id": 1, "codigo": "779111", "nombre": "Fideos Tallarín", "cantidad": 10, "costo": 800.0},
        {"id": 2, "codigo": "779222", "nombre": "Salsa de Tomate", "cantidad": 20, "costo": 500.0}
    ]
    ok = temp_nutricion.encolar_recepcion(
        proveedor="Molinos Río de la Plata",
        items=items,
        total_bultos=30.0,
        total_monto=18000.0,
        condicion_pago="A Pagar",
        perfil="dueño"
    )
    assert ok is True

    resumen = temp_nutricion.obtener_resumen_pendientes()
    assert resumen["recepciones"] == 1
    assert resumen["total"] == 1

    cola = temp_nutricion._leer_cola()
    assert len(cola["recepciones"]) == 1
    rec = cola["recepciones"][0]
    assert rec["proveedor"] == "Molinos Río de la Plata"
    assert rec["total_monto"] == 18000.0
    assert len(rec["items"]) == 2


def test_encolar_recepcion_es_idempotente_por_sync_id(temp_nutricion):
    kwargs = {
        "proveedor": "Proveedor",
        "items": [{"id": 1, "cantidad": 2, "costo": 100}],
        "total_bultos": 2,
        "total_monto": 200,
        "sync_id": "recepcion-1",
        "fecha": "2026-11-07 17:00:00",
    }
    assert temp_nutricion.encolar_recepcion(**kwargs) is True
    assert temp_nutricion.encolar_recepcion(**kwargs) is True
    cola = temp_nutricion._leer_cola()
    assert len(cola["recepciones"]) == 1
    assert cola["recepciones"][0]["sync_id"] == "recepcion-1"
    assert temp_nutricion.encolar_recepcion(
        **dict(kwargs, total_monto=201)
    ) is False


def test_journal_local_recupera_receipt_si_falta_json_outbox(temp_nutricion, tmp_path):
    registro = {
        "sync_id": "recepcion-journal",
        "proveedor": "Proveedor",
        "items": [{"id": 1, "cantidad": 2, "costo": 100}],
        "total_bultos": 2.0,
        "total_monto": 200.0,
        "condicion_pago": "Contado",
        "perfil": "admin",
        "timestamp": 1730000000.0,
        "fecha": "2026-11-07 17:00:00",
    }
    ruta = os.path.join(str(tmp_path), "punpro.db")
    with sqlite3.connect(ruta) as conn:
        conn.execute(
            """CREATE TABLE offline_recepciones (
                sync_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            "INSERT INTO offline_recepciones (sync_id, payload) VALUES (?, ?)",
            (registro["sync_id"], json.dumps(registro)),
        )

    cola = temp_nutricion._leer_cola(estricto=True)
    ok, journal_ids = temp_nutricion._incorporar_recepciones_persistentes(cola)

    assert ok is True
    assert journal_ids == {"recepcion-journal"}
    assert cola["recepciones"] == [registro]


def test_journal_local_se_limpia_despues_del_ack_maestro(temp_nutricion, tmp_path, monkeypatch):
    registro = {
        "sync_id": "recepcion-confirmada",
        "proveedor": "Proveedor",
        "items": [{"id": 1, "cantidad": 2, "costo": 100}],
        "total_bultos": 2.0,
        "total_monto": 200.0,
        "condicion_pago": "Contado",
        "perfil": "admin",
        "timestamp": 1730000000.0,
        "fecha": "2026-11-07 17:00:00",
    }
    ruta = os.path.join(str(tmp_path), "punpro.db")
    with sqlite3.connect(ruta) as conn:
        conn.execute(
            """CREATE TABLE offline_recepciones (
                sync_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            "INSERT INTO offline_recepciones (sync_id, payload) VALUES (?, ?)",
            (registro["sync_id"], json.dumps(registro)),
        )
    monkeypatch.setattr(
        temp_nutricion,
        "_aplicar_recepcion_maestra",
        lambda _db, recibida: recibida == registro,
    )
    db = MagicMock()
    db.db_engine_type = "mariadb"
    db.is_connected.return_value = True

    exito, _mensaje, estadisticas = temp_nutricion.nutrir_maestra(db)

    assert exito is True
    assert estadisticas["recepciones"] == 1
    with sqlite3.connect(ruta) as conn:
        assert conn.execute("SELECT COUNT(*) FROM offline_recepciones").fetchone()[0] == 0
    assert temp_nutricion._leer_cola(estricto=True)["recepciones"] == []


def test_journal_no_se_limpia_si_sqlite_rechaza_el_ack(temp_nutricion, tmp_path, monkeypatch):
    ruta = os.path.join(str(tmp_path), "punpro.db")
    with sqlite3.connect(ruta) as conn:
        conn.execute(
            """CREATE TABLE offline_recepciones (
                sync_id TEXT PRIMARY KEY, payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        conn.execute(
            "INSERT INTO offline_recepciones (sync_id, payload) VALUES (?, ?)",
            ("recepcion-pendiente", "{}"),
        )

    connect_original = sqlite3.connect

    def connect_bloqueada(*_args, **_kwargs):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(sqlite3, "connect", connect_bloqueada)
    assert temp_nutricion._confirmar_recepciones_persistentes({"recepcion-pendiente"}) is False
    monkeypatch.setattr(sqlite3, "connect", connect_original)
    with connect_original(ruta) as conn:
        assert conn.execute("SELECT COUNT(*) FROM offline_recepciones").fetchone()[0] == 1


def test_outbox_con_recepcion_invalida_no_se_abre_en_modo_estricto(temp_nutricion):
    with open(temp_nutricion.outbox_file, "w", encoding="utf-8") as archivo:
        json.dump({"recepciones": [None]}, archivo)

    assert temp_nutricion._leer_cola(estricto=True) is None


def test_recepcion_offline_se_recupera_del_journal_si_falla_el_outbox(
    temp_nutricion, tmp_path, monkeypatch
):
    from src.base_de_datos.database import db_manager
    from src.base_de_datos import offline_nutricion
    from src.motor_inventario.planilla.orquestador import MotorPlanilla
    from src.proveedor_global.backend import recepcion_service

    ruta = os.path.join(str(tmp_path), "punpro.db")
    with sqlite3.connect(ruta) as conn:
        conn.executescript(
            """
            CREATE TABLE romaneos (
                id INTEGER PRIMARY KEY, fecha TEXT, proveedor TEXT, tropa TEXT,
                tipo_carne TEXT, precio_unitario REAL, total_kilos REAL,
                monto_total REAL, estado_pago TEXT, registrado_por TEXT
            );
            CREATE TABLE productos (
                id INTEGER PRIMARY KEY, stock REAL, costo REAL
            );
            CREATE TABLE romaneo_items (
                id INTEGER PRIMARY KEY, romaneo_id INTEGER,
                nro_garrote TEXT, peso REAL
            );
            CREATE TABLE gastos (
                id INTEGER PRIMARY KEY, fecha TEXT, categoria TEXT,
                descripcion TEXT, monto REAL, status TEXT, usuario TEXT
            );
            INSERT INTO productos (id, stock, costo) VALUES (1, 0, 0);
            """
        )

    monkeypatch.setattr(db_manager, "db_engine_type", "sqlite")
    monkeypatch.setattr(db_manager, "_forced_local_offline", True, raising=False)
    monkeypatch.setattr(db_manager, "get_connection", lambda: sqlite3.connect(ruta))
    monkeypatch.setattr(offline_nutricion, "offline_nutricion_manager", temp_nutricion)
    monkeypatch.setattr(MotorPlanilla, "avisar", staticmethod(lambda: None))
    monkeypatch.setattr(
        temp_nutricion,
        "encolar_recepcion",
        lambda *_args, **_kwargs: False,
    )

    ok, _mensaje, resumen = recepcion_service.RecepcionService.procesar_ingreso_mercaderia(
        "Proveedor",
        [{"id": 1, "codigo": "1", "nombre": "Producto", "cantidad": 2, "costo": 100}],
    )

    assert ok is True
    assert "sync_error" in resumen
    with sqlite3.connect(ruta) as conn:
        payload = conn.execute(
            "SELECT payload FROM offline_recepciones WHERE sync_id = ?",
            (resumen["sync_id"],),
        ).fetchone()[0]
        assert conn.execute("SELECT stock FROM productos WHERE id = 1").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM romaneos").fetchone()[0] == 1
    registro = json.loads(payload)
    cola = temp_nutricion._leer_cola(estricto=True)
    recuperado, ids = temp_nutricion._incorporar_recepciones_persistentes(cola)
    assert recuperado is True
    assert ids == {resumen["sync_id"]}
    assert cola["recepciones"] == [registro]


def test_encolar_cliente_offline(temp_nutricion):
    cli_data = {
        "nombre": "Juan Pérez",
        "dni": "35123456",
        "telefono": "1122334455",
        "limite_credito": 50000.0,
        "tipo_cliente": "regular"
    }
    assert temp_nutricion.encolar_cliente("ALTA", cli_data) is True

    resumen = temp_nutricion.obtener_resumen_pendientes()
    assert resumen["clientes"] == 1
    assert resumen["total"] == 1

    cola = temp_nutricion._leer_cola()
    assert cola["clientes"][0]["accion"] == "ALTA"
    assert cola["clientes"][0]["datos"]["nombre"] == "Juan Pérez"


def test_encolar_auditoria_idempotente_y_visible(temp_nutricion):
    evento = {
        "sync_id": "evento-auditoria-1",
        "timestamp": 1730000000,
        "fecha": "2026-11-07 17:00:00",
        "producto_id": 7,
        "nombre_producto": "Yerba",
        "stock_sistema": 10,
        "stock_fisico": 8,
        "diferencia": -2,
        "responsable": "admin",
        "motivo": "Conteo",
    }

    assert temp_nutricion.encolar_auditoria(evento) is True
    assert temp_nutricion.encolar_auditoria(evento) is True
    assert temp_nutricion.obtener_resumen_pendientes()["auditorias"] == 1
    assert temp_nutricion._leer_cola()["auditorias"] == [evento]


def test_outbox_corrupto_no_se_sobrescribe(temp_nutricion):
    contenido = '{"productos": '
    with open(temp_nutricion.outbox_file, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)

    assert temp_nutricion.encolar_auditoria({"sync_id": "evento-1"}) is False
    assert temp_nutricion.obtener_resumen_pendientes()["error"] == 1
    with open(temp_nutricion.outbox_file, "r", encoding="utf-8") as archivo:
        assert archivo.read() == contenido


def test_auditoria_se_aplica_una_vez_aunque_quede_en_outbox(temp_nutricion):
    class DbSQLite:
        db_engine_type = "sqlite"

        def __init__(self):
            self.conn = sqlite3.connect(":memory:")
            self.conn.row_factory = sqlite3.Row
            self.execute_non_query(
                """CREATE TABLE auditorias_inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha DATETIME,
                    producto_id INTEGER,
                    nombre_producto TEXT,
                    stock_sistema REAL,
                    stock_fisico REAL,
                    diferencia REAL,
                    responsable TEXT,
                    motivo TEXT
                )"""
            )

        def execute_query(self, query, params=()):
            return self.conn.execute(query, params).fetchall()

        def execute_non_query(self, query, params=()):
            self.conn.execute(query, params)
            self.conn.commit()
            return True

    db = DbSQLite()
    evento = {
        "sync_id": "evento-reintento",
        "fecha": "2026-11-07 17:00:00",
        "producto_id": 7,
        "nombre_producto": "Yerba",
        "stock_sistema": 10,
        "stock_fisico": 8,
        "diferencia": -2,
        "responsable": "admin",
        "motivo": "Conteo",
    }
    assert temp_nutricion._aplicar_auditoria_maestra(db, evento) is True
    assert temp_nutricion._aplicar_auditoria_maestra(db, evento) is True
    cantidad = db.execute_query("SELECT COUNT(*) AS n FROM auditorias_inventario")[0]["n"]
    assert cantidad == 1


def test_auditoria_offline_se_almacena_con_el_mismo_sync_id(temp_nutricion, monkeypatch):
    class DbSQLite:
        db_engine_type = "sqlite"
        is_master = False

        def __init__(self):
            self.conn = sqlite3.connect(":memory:")
            self.conn.row_factory = sqlite3.Row
            self.execute_non_query(
                """CREATE TABLE auditorias_inventario (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATETIME,
                    producto_id INTEGER, nombre_producto TEXT, stock_sistema REAL,
                    stock_fisico REAL, diferencia REAL, responsable TEXT, motivo TEXT
                )"""
            )

        def execute_query(self, query, params=()):
            return self.conn.execute(query, params).fetchall()

        def execute_non_query(self, query, params=()):
            self.conn.execute(query, params)
            self.conn.commit()
            return True

    from src.base_de_datos.offline_nutricion import offline_nutricion_manager
    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria

    guardados = []
    monkeypatch.setattr(
        offline_nutricion_manager,
        "encolar_auditoria",
        lambda registro: guardados.append(dict(registro)) or True,
    )
    db = DbSQLite()
    assert MotorAuditoria.registrar_ajuste(
        db,
        {"id": 7, "nombre": "Yerba", "stock_sistema": 10, "stock_fisico": 8, "diferencia": -2},
        "admin",
        "Conteo",
    ) is True
    assert len(guardados) == 1
    fila = db.execute_query("SELECT sync_id FROM auditorias_inventario")[0]
    assert fila["sync_id"] == guardados[0]["sync_id"]


@pytest.mark.parametrize("aplicar_ok", [True, False])
def test_nutrir_maestra_confirma_auditoria_solo_tras_aplicarla(
    temp_nutricion, monkeypatch, aplicar_ok
):
    evento = {
        "sync_id": "evento-confirmacion",
        "fecha": "2026-11-07 17:00:00",
        "producto_id": 7,
        "nombre_producto": "Yerba",
        "stock_sistema": 10,
        "stock_fisico": 8,
        "diferencia": -2,
        "responsable": "admin",
        "motivo": "Conteo",
    }
    assert temp_nutricion.encolar_auditoria(evento) is True
    monkeypatch.setattr(
        temp_nutricion,
        "_aplicar_auditoria_maestra",
        lambda _db, _registro: aplicar_ok,
    )
    db = MagicMock()
    db.db_engine_type = "mariadb"
    db.is_connected.return_value = True

    exito, _mensaje, estadisticas = temp_nutricion.nutrir_maestra(db)

    assert estadisticas["auditorias"] == int(aplicar_ok)
    assert exito is aplicar_ok
    assert temp_nutricion.obtener_resumen_pendientes()["auditorias"] == int(not aplicar_ok)


def test_recepcion_antigua_recibe_sync_id_persistido_antes_del_reintento(
    temp_nutricion, monkeypatch
):
    temp_nutricion.encolar_recepcion(
        "Proveedor",
        [{"id": 1, "cantidad": 1}],
        1,
        10,
        fecha="2026-11-07 17:00:00",
    )
    cola = temp_nutricion._leer_cola(estricto=True)
    cola["recepciones"][0].pop("sync_id")
    assert temp_nutricion._escribir_cola(cola) is True

    intentados = []
    monkeypatch.setattr(
        temp_nutricion,
        "_aplicar_recepcion_maestra",
        lambda _db, registro: intentados.append(registro["sync_id"]) or False,
    )
    db = MagicMock()
    db.db_engine_type = "mariadb"
    db.is_connected.return_value = True

    exito, _mensaje, _estadisticas = temp_nutricion.nutrir_maestra(db)

    guardado = temp_nutricion._leer_cola(estricto=True)["recepciones"][0]["sync_id"]
    assert exito is False
    assert intentados == [guardado]


def _crear_db_recepcion_sqlite(tmp_path):
    class DbSQLite:
        db_engine_type = "mariadb"

        def __init__(self):
            self.path = os.path.join(str(tmp_path), "recepcion.db")
            with sqlite3.connect(self.path) as conn:
                conn.executescript(
                    """
                    CREATE TABLE romaneos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, proveedor TEXT,
                        tropa TEXT, tipo_carne TEXT, precio_unitario REAL, total_kilos REAL,
                        cantidad_cajas INTEGER, monto_total REAL, estado_pago TEXT,
                        registrado_por TEXT
                    );
                    CREATE TABLE romaneo_items (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, romaneo_id INTEGER,
                        nro_garrote TEXT, peso REAL
                    );
                    CREATE TABLE productos (
                        id INTEGER PRIMARY KEY, codigo TEXT, nombre TEXT, stock REAL,
                        costo REAL, precio REAL, categoria TEXT, departamento TEXT
                    );
                    CREATE TABLE gastos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, categoria TEXT,
                        descripcion TEXT, monto REAL, status TEXT, usuario TEXT
                    );
                    INSERT INTO productos
                        (id, codigo, nombre, stock, costo, precio, categoria, departamento)
                    VALUES (1, '7791', 'Yerba', 10, 50, 100, 'ALMACEN', 'ALMACEN');
                    """
                )

        def get_connection(self, caer_si_maestra_caida=True):
            conn = sqlite3.connect(self.path)
            conn.row_factory = sqlite3.Row
            return conn

        def execute_query(self, query, params=()):
            with self.get_connection() as conn:
                if query.startswith("SHOW COLUMNS FROM romaneos"):
                    return [{"Field": fila["name"]} for fila in conn.execute("PRAGMA table_info(romaneos)")]
                if query.startswith("SHOW INDEX FROM romaneos"):
                    indices = conn.execute("PRAGMA index_list(romaneos)").fetchall()
                    resultado = []
                    for indice in indices:
                        if indice["unique"]:
                            cols = conn.execute(
                                f'PRAGMA index_info("{indice["name"]}")'
                            ).fetchall()
                            resultado.extend(
                                {
                                    "Key_name": indice["name"],
                                    "Seq_in_index": columna["seqno"] + 1,
                                    "Column_name": columna["name"],
                                    "Non_unique": 0,
                                }
                                for columna in cols
                            )
                    return resultado
                return conn.execute(query, params).fetchall()

        def execute_non_query(self, query, params=()):
            with self.get_connection() as conn:
                conn.execute(query, params)
            return True

    return DbSQLite()


def test_recepcion_maestra_es_atomica_e_idempotente(temp_nutricion, tmp_path):
    db = _crear_db_recepcion_sqlite(tmp_path)
    evento = {
        "sync_id": "recepcion-idempotente",
        "proveedor": "Proveedor",
        "items": [{"id": 1, "codigo": "7791", "nombre": "Yerba", "cantidad": 2, "costo": 60}],
        "total_bultos": 2,
        "total_monto": 120,
        "condicion_pago": "Cta. Cte.",
        "perfil": "admin",
        "fecha": "2026-11-07 17:00:00",
    }

    assert temp_nutricion._aplicar_recepcion_maestra(db, evento) is True
    assert temp_nutricion._aplicar_recepcion_maestra(db, evento) is True
    assert db.execute_query("SELECT stock FROM productos WHERE id = 1")[0]["stock"] == 12
    assert db.execute_query("SELECT COUNT(*) AS n FROM romaneos")[0]["n"] == 1
    assert db.execute_query("SELECT COUNT(*) AS n FROM romaneo_items")[0]["n"] == 1
    assert db.execute_query("SELECT COUNT(*) AS n FROM gastos")[0]["n"] == 1


def test_recepcion_maestra_revierte_todo_si_falla_el_gasto(temp_nutricion, tmp_path):
    db = _crear_db_recepcion_sqlite(tmp_path)
    db.execute_non_query(
        """CREATE TRIGGER rechazar_gasto BEFORE INSERT ON gastos
        BEGIN SELECT RAISE(FAIL, 'error de prueba'); END"""
    )
    evento = {
        "sync_id": "recepcion-rollback",
        "proveedor": "Proveedor",
        "items": [{"id": 1, "codigo": "7791", "nombre": "Yerba", "cantidad": 2, "costo": 60}],
        "total_bultos": 2,
        "total_monto": 120,
        "condicion_pago": "Contado",
        "perfil": "admin",
        "fecha": "2026-11-07 17:00:00",
    }

    assert temp_nutricion._aplicar_recepcion_maestra(db, evento) is False
    assert db.execute_query("SELECT stock FROM productos WHERE id = 1")[0]["stock"] == 10
    assert db.execute_query("SELECT COUNT(*) AS n FROM romaneos")[0]["n"] == 0
    assert db.execute_query("SELECT COUNT(*) AS n FROM romaneo_items")[0]["n"] == 0
    assert db.execute_query("SELECT COUNT(*) AS n FROM gastos")[0]["n"] == 0


def test_recepcion_maestra_delega_formulas_sin_sumar_dos_veces(
    temp_nutricion, tmp_path, monkeypatch
):
    db = _crear_db_recepcion_sqlite(tmp_path)
    llamadas = []
    monkeypatch.setattr(
        "src.proveedor_global.backend.recepcion_service._avisar_formula",
        lambda cursor, items, db=None: llamadas.append((items, db)),
    )
    evento = {
        "sync_id": "recepcion-formula",
        "proveedor": "Proveedor",
        "items": [
            {
                "id": 1, "codigo": "7791", "nombre": "Caja base",
                "cantidad": 1, "costo": 100, "desde_formula": True,
                "bultos": 1, "precio_bulto": 100, "formula": "Pollo",
            },
            {
                "id": 1, "codigo": "7791", "nombre": "Corte",
                "cantidad": 2, "costo": 50, "desde_formula": True, "kilos": 2,
            },
        ],
        "total_bultos": 2,
        "total_monto": 100,
        "condicion_pago": "Contado",
        "perfil": "admin",
        "fecha": "2026-11-07 17:00:00",
    }

    assert temp_nutricion._aplicar_recepcion_maestra(db, evento) is True
    assert db.execute_query("SELECT stock FROM productos WHERE id = 1")[0]["stock"] == 10
    assert len(llamadas) == 1
    assert llamadas[0][0] == evento["items"]


def test_esquema_auditoria_migra_a_identidad_unica():
    class DbSQLite:
        db_engine_type = "sqlite"

        def __init__(self):
            self.conn = sqlite3.connect(":memory:")
            self.conn.row_factory = sqlite3.Row

        def execute_query(self, query, params=()):
            return self.conn.execute(query, params).fetchall()

        def execute_non_query(self, query, params=()):
            self.conn.execute(query, params)
            self.conn.commit()
            return True

    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria

    db = DbSQLite()
    db.execute_non_query(
        """CREATE TABLE auditorias_inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT, fecha DATETIME,
            producto_id INTEGER, nombre_producto TEXT, stock_sistema REAL,
            stock_fisico REAL, diferencia REAL, responsable TEXT, motivo TEXT
        )"""
    )
    assert MotorAuditoria.asegurar_tabla_auditorias(db) is True
    columnas = {fila["name"] for fila in db.execute_query("PRAGMA table_info(auditorias_inventario)")}
    assert "sync_id" in columnas
    indices = db.execute_query("PRAGMA index_list(auditorias_inventario)")
    assert any(indice["name"] == "idx_auditorias_sync_id" and indice["unique"] for indice in indices)


def test_esquema_auditoria_usa_sintaxis_mariadb():
    class DbMariaDB:
        db_engine_type = "mariadb"

        def __init__(self):
            self.escritas = []

        def execute_query(self, query, params=()):
            if query.startswith("SHOW COLUMNS"):
                return [{"Field": nombre} for nombre in (
                    "id", "fecha", "producto_id", "nombre_producto",
                    "stock_sistema", "stock_fisico", "diferencia",
                    "responsable", "motivo", "sync_id",
                )]
            if query.startswith("SHOW INDEX"):
                return [{"Column_name": "sync_id", "Non_unique": 0}]
            return []

        def execute_non_query(self, query, params=()):
            self.escritas.append(query)
            return True

    from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria

    db = DbMariaDB()
    assert MotorAuditoria.asegurar_tabla_auditorias(db) is True
    crear_tabla = db.escritas[0]
    assert "AUTO_INCREMENT" in crear_tabla
    assert "AUTOINCREMENT" not in crear_tabla


def test_nutrir_maestra_ejecucion(temp_nutricion, monkeypatch):
    # Encolar un producto, una recepción y un cliente
    temp_nutricion.encolar_producto({"codigo": "999", "nombre": "Galletitas", "precio": 1200, "stock": 10})
    temp_nutricion.encolar_recepcion("Arcor", [{"id": 10, "codigo": "999", "cantidad": 5, "costo": 700}], 5, 3500)
    temp_nutricion.encolar_cliente("ALTA", {"nombre": "Ana Gomez", "dni": "40111222"})

    assert temp_nutricion.obtener_resumen_pendientes()["total"] == 3

    # Simular db_manager conectado a MariaDB
    mock_db = MagicMock()
    mock_db.db_engine_type = "mariadb"
    mock_db.is_connected.return_value = True
    mock_db.execute_query.return_value = []
    mock_db.execute_non_query.return_value = True
    monkeypatch.setattr(
        temp_nutricion,
        "_aplicar_recepcion_maestra",
        lambda _db, _registro: True,
    )

    # Ejecutar nutrición
    ok, msg, stats = temp_nutricion.nutrir_maestra(mock_db)
    assert ok is True
    assert stats["productos"] == 1
    assert stats["recepciones"] == 1
    assert stats["clientes"] == 1

    # Verificar que el outbox quedó limpio tras el éxito
    assert temp_nutricion.obtener_resumen_pendientes()["total"] == 0
