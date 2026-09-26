"""Abonos, cupo, mixto con cliente y el gris detrás de las ventanas de caja."""
import inspect
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QWidget

_APP = QApplication.instance() or QApplication([])


def test_pin_admin_solo_cuatro_digitos_y_rol_admin(monkeypatch):
    from src.clientes_fiado.interfaz.cobro.pin_admin import quien_autoriza
    import hashlib

    filas = [
        {"username": "cajero", "rol": "cajero", "pin": "1234"},
        {"username": "jefe", "rol": "jefe", "pin": "1234"},
        {"username": "cesar", "rol": "admin", "pin": hashlib.sha256(b"4321").hexdigest()},
        {"username": "ana", "rol": "Admin", "pin": "9999"},
    ]
    monkeypatch.setattr(
        "src.base_de_datos.database.db_manager.execute_query",
        lambda *_a, **_k: filas,
    )
    assert quien_autoriza("12") == ""
    assert quien_autoriza("1234") == ""
    assert quien_autoriza("4321") == "cesar"
    assert quien_autoriza("9999") == "ana"
    assert quien_autoriza("0000") == ""


def test_excepcion_vale_una_vez_y_solo_ese_monto(monkeypatch):
    from src.clientes_fiado.cerebro.cerebro import cerebro
    from src.clientes_fiado.garante.orden.orden import OrdenCobro

    cerebro.soltar_excepcion()
    cerebro.conceder_excepcion(7, 100100, "César")
    assert cerebro.excepcion_vigente(7, 100100)
    assert cerebro.excepcion_vigente(7, 100) is False
    monkeypatch.setattr(cerebro.cuenta, "obtener", lambda _cid: {"id": 7, "nombre": "Ana"})
    orden = cerebro.autorizar("Clientes", 7, 100100)
    assert orden.ok is True
    assert orden.excepcion == "César"
    assert cerebro.excepcion_vigente(7, 100100) is False
    monkeypatch.setattr(
        cerebro.cliente,
        "autorizar",
        lambda *_a, **_k: OrdenCobro(False, "Clientes", motivo="cupo"),
    )
    otra = cerebro.autorizar("Clientes", 7, 100100)
    assert otra.ok is False


def test_abonar_caja_firma_perfil_medio(monkeypatch):
    from src.clientes_fiado.cerebro.cerebro import cerebro

    visto = {}

    def falso(_cid, _monto, descripcion, medio, perfil, quien):
        visto.update(descripcion=descripcion, medio=medio, perfil=perfil, quien=quien)
        return True, 40.0, "Ana"

    monkeypatch.setattr(cerebro, "abonar", falso)
    monkeypatch.setattr(
        "src.hardware.printer.printer_manager.imprimir_saldo_fiado",
        lambda *_a, **_k: None,
    )
    ok, saldo, nombre = cerebro.abonar_caja(
        3, 10, 50, medio="Transferencia", perfil="Admin", quien="César"
    )
    assert ok is True
    assert saldo == 40.0
    assert nombre == "Ana"
    assert visto["descripcion"] == "Admin César (Transferencia)"
    assert visto["medio"] == "Transferencia"


def test_cargo_nombra_la_excepcion():
    from src.base_de_datos.repos.ventas import _texto_cargo

    assert _texto_cargo(12, {"cliente_id": 1}) == "Venta a crédito Ticket #12"
    assert _texto_cargo(12, {"excepcion": "César"}) == "Venta a crédito Ticket #12 (excepción César)"


def test_mixto_cliente_completa_el_resto_y_cuenta_como_medio():
    from src.cajero.paso6_cobro.mixto_en_cobro.panel import PanelMixtoCobro
    from src.cajero.paso6_cobro.mixto_en_cobro.confirmar import pasos_vivos, vivo
    from src.cajero.paso6_cobro.componentes_paso6_cobro.logica.cobro_controller import CobroController

    panel = PanelMixtoCobro()
    panel.fijar_total(100100)
    panel.txt_efectivo.setText("10000")
    panel.completar_cliente()
    assert panel.valores()["cliente"] == 90100.0
    panel.txt_tarjeta.setText("1")
    assert panel.valores()["tarjeta"] == 0.0
    otro = PanelMixtoCobro()
    otro.fijar_total(100)
    otro.txt_efectivo.setText("40")
    otro.txt_tarjeta.setText("10")
    otro.completar_cliente()
    assert otro.valores()["cliente"] == 0.0
    assert vivo({"tarjeta": 50, "mercadopago": 0, "qr": 0, "cliente": 10}) == (50.0, 0.0, 0.0)
    assert pasos_vivos({"tarjeta": 50, "mercadopago": 0, "qr": 0, "cliente": 10}) == [("tarjeta", 50.0)]

    p1, p2 = CobroController.validar_monto_suficiente(
        "Mixto", 100, 0, valores_mixtos={"efectivo": 40, "cliente": 60, "tarjeta": 0, "mercadopago": 0, "qr": 0}
    )
    assert p1 == 40
    assert p2 == 60
    assert CobroController.validar_monto_suficiente(
        "Mixto", 100, 0, valores_mixtos={"efectivo": 10, "cliente": 0, "tarjeta": 0, "mercadopago": 0, "qr": 0}
    ) == (None, None)


def test_aviso_de_cupo_en_tres_lineas(monkeypatch):
    from src.clientes_fiado.interfaz.cobro.hoja import HojaCuentaCobro
    from src.clientes_fiado.cerebro.cerebro import cerebro

    monkeypatch.setattr(cerebro, "credito_disponible", lambda _c: 99900)
    monkeypatch.setattr(
        "src.clientes_fiado.interfaz.cobro.hoja.sonar_alarma_limite_fiado",
        lambda: None,
    )
    hoja = HojaCuentaCobro()
    hoja._monto = 100100
    hoja._avisar_cupo({"limite_credito": 100000, "nombre": "Ana"}, "Ana")
    texto = hoja.aviso.text()
    assert "Límite superado" in texto
    assert "crédito: $ 100,000" in texto
    assert "exceso: $ 200.00" in texto
    assert "#047857" in texto
    assert "#EF4444" in texto
    assert "color:" not in hoja.aviso.styleSheet()
    assert hoja._pidiendo_pin is True


def test_pago_de_clientes_no_suma_otra_vez_el_esperado():
    from src.ui_global.cierre_diario_ui.componentes.panel_arqueo import PanelArqueo
    import src.cerebro_global.cierre_caja_cerebro.procesos.totales as totales

    panel = PanelArqueo()
    panel.set_esperado(500)
    panel.set_pago_clientes(80)
    assert panel.esperado == 500
    assert "Pago de clientes" in panel.lbl_pago_clientes.text()
    panel.set_pago_clientes(0)
    assert panel.lbl_pago_clientes.text() == ""
    fuente = inspect.getsource(totales)
    assert "LIKE ?" in fuente
    assert '["Pago de clientes%", desde]' in fuente or "Pago de clientes%" in fuente
    assert "LIKE 'Pago de clientes%'" not in fuente


def test_auditoria_marca_el_ticket_sin_cargo():
    from src.clientes_fiado.oficina.cobradas.auditoria import cruzar

    cruce = cruzar(
        [
            {"id": 1089686, "total": 100, "metodo_pago": "Fiado"},
            {"id": 1089689, "total": 100, "metodo_pago": "Clientes"},
            {"id": 1089690, "total": 100100, "metodo_pago": "Clientes"},
        ],
        [
            {"venta_id": None, "monto": 100, "descripcion": "Cargo manual"},
            {"venta_id": 1089690, "monto": 100100},
        ],
    )
    assert cruce["ventas_credito"] == 100300
    assert cruce["cargos_venta"] == 100100
    assert cruce["faltan"] == 200
    assert cruce["manual"] == 100
    assert [v["id"] for v in cruce["sin_cargo"]] == [1089686, 1089689]


def test_planilla_lee_el_medio_registrado():
    from src.clientes_fiado.oficina.cobradas.lista import armar, medio_de

    assert medio_de({"medio_pago": "QR"}) == "QR"
    assert medio_de({"descripcion": "Cajero María (Transferencia)"}) == "Transferencia"
    fila = armar({
        "fecha": "2026-09-25 21:00:00",
        "nombre": "Ana",
        "dni": "94707566",
        "monto": 10000,
        "medio_pago": "Efectivo",
        "perfil": "Cajero",
        "registrado_por": "María",
        "saldo_resultante": 90000,
    })
    assert fila["medio"] == "Efectivo"
    assert fila["quien"] == "María"
    assert fila["monto"] == 10000


def test_el_abono_del_cajero_no_tira(monkeypatch):
    from src.clientes_fiado.interfaz.cobro.medios import cerrar

    def rompe(*_a, **_k):
        raise RuntimeError("medio caido")

    monkeypatch.setattr(
        "src.clientes_fiado.interfaz.cobro.medio.pedir_medio", rompe,
    )
    assert cerrar.pedir(None, 100) is None

    class Roto:
        ok = True
        medio = "Efectivo"
        entra_caja = True
        monto_caja = 10
        detalle = ""

    def rompe_caja(*_a, **_k):
        raise RuntimeError("base caida")

    from src.clientes_fiado.cerebro.cerebro import cerebro

    monkeypatch.setattr(cerebro, "abonar_caja", rompe_caja)
    hecho = cerrar.asentar(1, 10, 20, "Cajero", "Maria", Roto())
    assert hecho["ok"] is False
    assert "venta sigue" in hecho["aviso"]


def test_f6_dibuja_el_qr_con_el_motor():
    from pathlib import Path

    carpeta = Path("src/cajero/ingresar_efectivo/fiado/cobro")
    textos = "\n".join(ruta.read_text(encoding="utf-8") for ruta in carpeta.glob("*.py"))
    assert "pedir_qr_pos" in textos
    assert "enviar_monto" in textos
    assert "Paso6Cobro" not in textos
    assert "DialogoPIN" in textos
    assert "EscuchaMP" in textos
    assert "Key_F9" in textos
    assert "F9 MANUAL" in textos
    assert "Asociar" in textos
    assert "drawer_manager" in textos
    from src.cajero.ingresar_efectivo.fiado.cobro.pagina import PaginaCobroAbono
    assert PaginaCobroAbono.__name__ == "PaginaCobroAbono"


def test_medios_del_abono_no_pasan_por_la_venta():
    import inspect
    from pathlib import Path

    from src.clientes_fiado.interfaz.cobro.medio import MEDIOS
    from src.clientes_fiado.interfaz.cobro.medios.puerta import cobrar

    assert MEDIOS == ("Efectivo", "Transferencia", "Tarjeta", "QR", "Mixto")
    efectivo = cobrar("Efectivo", 100)
    assert efectivo.ok and efectivo.entra_caja and efectivo.medio == "Efectivo"
    assert efectivo.monto_caja == 100
    mixto = cobrar("Mixto", 150, {"Efectivo": 100, "Tarjeta": 50})
    assert mixto.ok and mixto.medio == "Mixto" and mixto.monto_caja == 100
    assert cobrar("Mixto", 150, {"Efectivo": 10, "Tarjeta": 20, "QR": 120}).ok is False
    assert cobrar("Mixto", 150, {"Efectivo": 100, "Tarjeta": 40}).ok is False
    for nombre in ("Transferencia", "Tarjeta", "QR"):
        resultado = cobrar(nombre, 50)
        assert resultado.ok and resultado.entra_caja is False and resultado.medio == nombre
    assert cobrar("Fiado", 10).ok is False
    assert cobrar("Efectivo", 0).ok is False
    carpeta = Path(__file__).resolve().parents[1] / "src" / "clientes_fiado" / "interfaz" / "cobro" / "medios"
    for archivo in carpeta.glob("*.py"):
        assert "paso6" not in archivo.read_text(encoding="utf-8")
    assert "paso6" not in inspect.getsource(cobrar)


def test_f6_abre_tres_tarjetas_blancas_sobre_gris():
    from src.cajero.ingresar_efectivo.dialogo import DialogoIngresoEfectivo
    from src.utils.fondo_gris import GRIS

    padre = QWidget()
    padre.setFixedSize(900, 700)
    dlg = DialogoIngresoEfectivo(padre)
    dlg.panel_fiado.cargar_clientes_abono = lambda: None
    dlg.show()
    assert GRIS == "#334155"
    assert dlg.width() == 900
    assert dlg.height() == 700
    assert dlg.paginas.currentIndex() == 0
    assert dlg.paginas.width() == 680
    assert "#FFFFFF" in dlg.paginas.widget(0).styleSheet()
    assert dlg.btn_cambio is not None and dlg.btn_fiado is not None and dlg.btn_otros is not None
    from PyQt6.QtWidgets import QLabel
    textos = [etiqueta.text() for etiqueta in dlg.paginas.widget(0).findChildren(QLabel)]
    assert "CENTRO DE COBRANZAS" in textos
    assert "CAMBIO" in textos and "FIADO" in textos and "OTROS" in textos
    assert inspect.getsource(DialogoIngresoEfectivo).count("def showEvent") == 1
    dlg.abrir_para_cliente({"dni": "94707566", "nombre": "Ana"})
    assert dlg._directo is True
    assert dlg.paginas.currentIndex() == 1
    assert "94707566" in dlg.panel_fiado.txt_buscar.text()
    dlg.close()
    padre.close()


def test_f11_arma_el_formulario_antes_de_pintar():
    from src.inicio_y_perfiles.login_pantalla import LoginPantalla

    assert "UsuarioCampo" not in inspect.getsource(LoginPantalla.paintEvent)
    assert "self.txt_user" in inspect.getsource(LoginPantalla._setup_ui)
    padre = QWidget()
    padre.setFixedSize(1000, 800)
    login = LoginPantalla("admin", parent=padre, fondo_gris=True)
    assert login.txt_user is not None
    assert login.txt_pass is not None
    login.show()
    assert login.width() == 1000
    assert login._fondo_gris is True
    login.close()
    padre.close()


def test_retiro_historial_y_cierre_tapan_con_gris():
    from src.cajero.sacar_efectivo.dialogo_retiro import DialogoRetiroEfectivo
    from src.cajero.paso8_historial.dialogo import DialogoHistorialDia
    from src.ui_global.cierre_diario_ui.cierre_main_ui import DialogoCierreCaja
    from src.utils.fondo_gris import cubrir, pintar

    assert "cubrir" in inspect.getsource(DialogoRetiroEfectivo.showEvent)
    assert "pintar" in inspect.getsource(DialogoRetiroEfectivo.paintEvent)
    assert "cubrir" in inspect.getsource(DialogoHistorialDia.showEvent)
    assert "cubrir" in inspect.getsource(DialogoCierreCaja.showEvent)
    assert "pintar" in inspect.getsource(DialogoCierreCaja.paintEvent)
    retiro = DialogoRetiroEfectivo(12000)
    assert retiro.txt_monto is not None
    retiro.close()
    assert cubrir and pintar


def test_titulo_del_candado_se_lee_sobre_blanco():
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    base = (raiz / "src" / "ui_components" / "base.qss").read_text(encoding="utf-8")
    dia = (raiz / "src" / "ui_components" / "estilo_dia.qss").read_text(encoding="utf-8")
    noche = (raiz / "src" / "ui_components" / "estilo_noche.qss").read_text(encoding="utf-8")
    titulo = base.split("QLabel#DialogoCandadoTitulo")[1].split("}")[0]
    assert "#0F172A" in titulo
    assert "#FFFFFF" not in titulo
    assert "QFrame#DialogoCandadoFondo { background: #334155; }" in dia
    assert "QFrame#DialogoCandadoFondo { background: #334155; }" in noche
    assert "QFrame#DialogoCandadoContenedor { background: white;" in dia


class _Libro:
    def __init__(self, falla_ancho=False, falla_corto=False):
        self.falla_ancho = falla_ancho
        self.falla_corto = falla_corto
        self.committed = False
        self.rolled = False
        self.queries = []

    def cursor(self):
        return self

    def execute(self, query, params=None):
        self.queries.append(query)
        if "medio_pago" in query and self.falla_ancho:
            raise RuntimeError("Unknown column 'medio_pago'")
        if self.falla_corto and "VALUES (?, 'ABONO'" in query and "medio_pago" not in query:
            raise RuntimeError("insert corto")

    def fetchone(self):
        return {"deuda_actual": 80.0, "nombre": "Ana"}

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled = True

    def close(self):
        pass


def test_abono_es_una_sola_transaccion_y_cae_al_insert_corto(monkeypatch):
    from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta

    ancho = _Libro(falla_ancho=True)
    monkeypatch.setattr(
        "src.clientes_fiado.oficina.cuenta.motor.db_manager.get_connection",
        lambda: ancho,
    )
    ok, saldo, nombre = MotorCuenta().abonar(3, 10, "Admin Ana (Efectivo)", "Efectivo", "Admin", "Ana")
    assert ok is True
    assert saldo == 70.0
    assert nombre == "Ana"
    assert ancho.committed is True
    assert any("medio_pago" in q for q in ancho.queries)
    assert any("VALUES (?, 'ABONO'" in q and "medio_pago" not in q for q in ancho.queries)

    roto = _Libro(falla_ancho=True, falla_corto=True)
    monkeypatch.setattr(
        "src.clientes_fiado.oficina.cuenta.motor.db_manager.get_connection",
        lambda: roto,
    )
    ok, saldo, _nombre = MotorCuenta().abonar(3, 10, "x", "Efectivo", "Admin", "Ana")
    assert ok is False
    assert saldo == 0.0
    assert roto.committed is False
    assert roto.rolled is True


def test_planilla_repite_la_lectura_si_falta_la_columna(monkeypatch):
    from src.base_de_datos.database import db_manager
    from src.clientes_fiado.oficina.cuenta.motor import MotorCuenta

    def query(sql, params=()):
        if "medio_pago" in sql:
            db_manager.last_error = "Unknown column 'medio_pago'"
            return []
        db_manager.last_error = ""
        return [{
            "fecha": "2026-09-25 18:00:00",
            "monto": 10,
            "saldo_resultante": 0,
            "descripcion": "Admin Ana (Efectivo)",
            "nombre": "Ana",
            "dni": "1",
        }]

    monkeypatch.setattr(db_manager, "execute_query", query)
    filas = MotorCuenta().listar_cobros()
    assert filas[0]["medio"] == "Efectivo"
    assert filas[0]["nombre"] == "Ana"


def test_emparejar_solo_cuando_el_nombre_es_unico():
    from src.clientes_fiado.oficina.cuenta.cuadre import emparejar

    ventas = [
        {"id": 1, "fecha": "2026-09-25", "total": 100, "metodo_pago": "Fiado", "cliente_nombre": "César"},
        {"id": 2, "fecha": "2026-09-25", "total": 50, "metodo_pago": "Clientes", "cliente_nombre": "Ana"},
        {"id": 3, "fecha": "2026-09-25", "total": 20, "metodo_pago": "Fiado", "cliente_nombre": ""},
    ]
    clientes = [
        {"id": 9, "nombre": "Cesar"},
        {"id": 4, "nombre": "Ana"},
        {"id": 5, "nombre": "ANA"},
    ]
    pares = emparejar(ventas, clientes)
    assert pares[0]["cliente_id"] == 9
    assert pares[1]["cliente_id"] is None
    assert pares[2]["cliente_id"] is None
    express = emparejar(
        [{"id": 8, "total": 100, "metodo_pago": "Fiado", "cliente_nombre": "Express 94707566"}],
        [{"id": 2, "nombre": "cesar", "dni": "94707566"}],
    )
    assert express[0]["cliente_id"] == 2
    assert express[0]["nombre"] == "cesar"


class _Cur:
    def __init__(self, filas):
        self._filas = list(filas)
        self.sql = []

    def execute(self, query, params=None):
        self.sql.append((query, params))

    def fetchone(self):
        if not self._filas:
            return None
        return self._filas.pop(0)


def test_cupo_frena_la_venta_si_otra_caja_ya_cargo():
    from src.base_de_datos.repos.ventas import CreditoInsuficiente, _aplicar_fiado

    cur = _Cur([{"deuda_actual": 90, "nombre": "Ana", "limite_credito": 100}])
    try:
        _aplicar_fiado(cur, {"cliente_id": 1, "total": 20}, 9)
        raise AssertionError("tenía que frenar")
    except CreditoInsuficiente as err:
        assert "insuficiente" in str(err).lower()
    assert not any("INSERT INTO cuenta_corriente" in q for q, _p in cur.sql)


def test_ticket_ya_vendido_carga_aunque_supere_el_cupo():
    from src.base_de_datos.repos.ventas import _aplicar_fiado

    cur = _Cur([
        {"deuda_actual": 90, "nombre": "Ana", "limite_credito": 100},
        {"deuda_actual": 110, "nombre": "Ana"},
    ])
    nombre = _aplicar_fiado(
        cur, {"cliente_id": 1, "total": 20, "ya_vendido": True, "nota": "cuadre"}, 9
    )
    assert nombre == "Ana"
    cargo = [p for q, p in cur.sql if q.startswith("INSERT INTO cuenta_corriente")]
    assert cargo and "cuadre" in cargo[0][4]


def test_anular_baja_la_deuda_una_sola_vez():
    from src.base_de_datos.repos.ventas import _anular_cargo

    cur = _Cur([
        {"cliente_id": 3, "monto": 100},
        None,
        {"deuda_actual": 100},
    ])
    _anular_cargo(cur, 12)
    updates = [p for q, p in cur.sql if q.startswith("UPDATE clientes")]
    assert updates == [(0.0, 3)]
    altas = [p for q, p in cur.sql if q.startswith("INSERT INTO cuenta_corriente")]
    assert altas and altas[0][0] == 3
    assert altas[0][3].startswith("Anulación Ticket #12")

    otra = _Cur([{"cliente_id": 3, "monto": 100}, {"id": 1}])
    _anular_cargo(otra, 12)
    assert not any(q.startswith("UPDATE") for q, _p in otra.sql)


def test_persistir_avisa_credito_insuficiente(monkeypatch):
    from src.base_de_datos.database import db_manager
    from src.base_de_datos.repos.ventas import CreditoInsuficiente
    from src.cajero.paso6_cobro.motor_pagos.comandos.persistir_cobro import persistir_cobro

    def boom(*_a, **_k):
        raise CreditoInsuficiente("Crédito insuficiente")

    monkeypatch.setattr(db_manager, "guardar_venta_completa", boom)
    id_v, resultado = persistir_cobro({
        "metodo": "Efectivo",
        "total_final": 10,
        "p1": 10,
        "p2": 0,
        "items_carrito": [],
    })
    assert id_v is None
    assert resultado["error"] == "Crédito insuficiente"
