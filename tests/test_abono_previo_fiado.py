from types import SimpleNamespace


def test_abono_previo_registra_cobranza_y_solo_el_efectivo_en_caja(monkeypatch):
    from src.cajero.paso6_cobro.fiado_en_cobro import cobranza

    eventos = {}

    class Dialogo:
        tipo_ingreso = "FIADO"
        cliente_id = "42"
        monto_ingresado = 75.0
        deuda_actual = 300.0
        resultado = SimpleNamespace(ok=True, entra_caja=True, monto_caja=25.0)

        def __init__(self, parent=None):
            eventos["parent"] = parent

        def abrir_para_cliente(self, cliente):
            eventos["cliente"] = cliente

    monkeypatch.setattr(
        "src.cajero.ingresar_efectivo.DialogoIngresoEfectivo", Dialogo
    )
    monkeypatch.setattr("src.utils.qt_compat.qt_exec", lambda _dialogo: True)
    monkeypatch.setattr(
        "src.clientes_fiado.interfaz.cobro.medios.cerrar.asentar",
        lambda *args, **kwargs: eventos.update(
            asentar=(args, kwargs)
        ) or {
            "ok": True,
            "entra_caja": True,
            "monto_caja": 25.0,
            "motivo": "Pago de clientes: Ana (Mixto)",
            "nombre": "Ana",
            "saldo": 225.0,
        },
    )
    monkeypatch.setattr(
        "src.cajero.cajero_activo.CajeroActivo.nombre", "Cajera"
    )
    monkeypatch.setattr(
        "src.config.config.get", lambda _key, default=None: default
    )

    def registrar(self, monto, usuario, motivo, caja_id, **kwargs):
        eventos["caja"] = (monto, usuario, motivo, caja_id, kwargs)
        return True

    monkeypatch.setattr(
        "src.cajero.paso5_terminal.logica.movimientos_caja_service."
        "MovimientosCajaService.registrar_ingreso_efectivo",
        registrar,
    )

    cliente = {"id": 42, "nombre": "Ana", "deuda_actual": 300.0}
    resultado = cobranza.cobrar_deuda_previa(object(), cliente)

    assert resultado.ok is True
    assert resultado.cliente_id == 42
    assert resultado.monto == 75.0
    assert resultado.deuda_anterior == 300.0
    assert eventos["asentar"][1]["imprimir_saldo"] is False
    assert eventos["caja"][0:2] == (25.0, "Cajera")
    assert eventos["caja"][4] == {"abrir_cajon": False, "imprimir": False}


def test_ticket_fiado_muestra_saldo_anterior_abono_y_compra(monkeypatch):
    from src.cajero.paso6_cobro.componentes_paso6_cobro.logica.cobro_controller import (
        CobroController,
    )
    from src.config import config
    from src.hardware.printer import printer_manager

    capturado = {}
    monkeypatch.setattr(config, "get", lambda _key, default=None: default)
    from src.repositories.cliente_repository import ClienteRepository

    monkeypatch.setattr(
        ClienteRepository, "obtener_por_id",
        staticmethod(lambda _cliente_id: {"nombre": "Ana", "deuda_actual": 550.0}),
    )
    monkeypatch.setattr(
        ClienteRepository, "credito_disponible",
        staticmethod(lambda _cliente: 450.0),
    )
    monkeypatch.setattr(
        printer_manager,
        "imprimir_ticket_venta",
        lambda *args, **kwargs: capturado.update(args=args, kwargs=kwargs),
    )

    CobroController.procesar_cajon_impresion(
        "Fiado",
        True,
        10899983,
        [],
        150.0,
        {"cliente_id": 42, "pago_con": 150.0, "cambio": 0.0},
        "Cajera",
        0.0,
        0.0,
        False,
        100.0,
        500.0,
    )

    assert capturado["args"][2] == 150.0
    assert capturado["kwargs"]["saldo_anterior"] == 500.0
    assert capturado["kwargs"]["abono_cuenta"] == 100.0
    assert capturado["kwargs"]["saldo_disponible"] == 450.0


def test_abono_previo_no_modifica_total_y_acumula_importes():
    from src.cajero.paso6_cobro.paso6_cobro import Paso6Cobro

    avisos = []
    estado = SimpleNamespace(
        total_final=150.0,
        deuda_adicional_cobrada=0.0,
        deuda_adicional_saldo_anterior=None,
        _avisar=avisos.append,
    )

    Paso6Cobro._abono_cuenta_registrado(
        estado, SimpleNamespace(monto=25.0, deuda_anterior=300.0)
    )
    Paso6Cobro._abono_cuenta_registrado(
        estado, SimpleNamespace(monto=10.0, deuda_anterior=275.0)
    )

    assert estado.total_final == 150.0
    assert estado.deuda_adicional_cobrada == 35.0
    assert estado.deuda_adicional_saldo_anterior == 300.0
    assert len(avisos) == 2


def test_ticket_impreso_ordena_abono_entre_saldo_y_compra(monkeypatch):
    from src.config import config
    import src.hardware.printer as printer_module
    from src.hardware.printer import printer_manager

    enviados = []
    monkeypatch.setattr(config, "get", lambda _key, default=None: default)
    monkeypatch.setattr(printer_module, "_impresora_cajero_activo", lambda: "test")
    monkeypatch.setattr(
        printer_manager, "_send_raw_data", lambda data, **_kwargs: enviados.append(data) or True
    )

    assert printer_manager.imprimir_ticket_venta(
        10899983,
        [],
        150.0,
        150.0,
        0.0,
        metodo_pago="Fiado",
        cliente_nombre="Ana",
        saldo_anterior=500.0,
        saldo_disponible=450.0,
        abono_cuenta=100.0,
    )

    ticket = enviados[0]
    saldo = ticket.index(b"Saldo anterior:   $500.00")
    abono = ticket.index(b"Abono a cuenta:   $100.00")
    compra = ticket.index(b"Compra actual:    $150.00")
    assert saldo < abono < compra
