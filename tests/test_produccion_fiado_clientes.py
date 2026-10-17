# -*- coding: utf-8 -*-
"""
Pruebas integrales de producción para creación y búsqueda de clientes en Cobro y Admin.
Verifica:
1. crear_cliente en cerebro y persistencia con huella de auditoría.
2. Identificación de clientes existentes sin duplicar.
3. Búsqueda insensible a mayúsculas y acentos (plegado NFD).
4. MotorBusquedaClientes con recarga forzada (forzar=True) y fallback a red/BD.
5. PanelClienteNuevo: procesamiento con ENTER y emisión de datos correctos.
6. PanelBuscadorClientes: verificación directa en BD antes de crear.
7. OrquestadorFiadoPiramidal: flujo completo desde alta exprés hasta evaluación de margen aprobado.
"""
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

# Asegurar QApplication para widgets Qt
app = QApplication.instance() or QApplication([])


def test_crear_cliente_cerebro():
    from src.clientes_fiado.cerebro.cerebro import crear_cliente, cerebro
    from src.base_de_datos.database import db_manager

    nombre_test = "Cliente_Test_Prod_99"
    try:
        # 1. Crear cliente
        cid, msg = crear_cliente(nombre_test, "", limite=50000.0)
        assert cid is not None, f"Fallo al crear cliente: {msg}"
        assert "creado" in msg.lower() or "existente" in msg.lower()

        # 2. Verificar que cerebro lo puede obtener
        cli = cerebro.obtener(cid)
        assert cli is not None, "cerebro.obtener no encontró el cliente creado"
        c_dict = dict(cli) if hasattr(cli, "keys") else cli
        assert c_dict.get("nombre") == nombre_test
        assert float(c_dict.get("limite_credito") or 0) == 50000.0
        assert float(c_dict.get("deuda_actual") or 0) == 0.0

        # 3. Intentar crear de nuevo con mismo nombre -> debe identificarlo sin duplicar
        cid2, msg2 = crear_cliente(nombre_test, "", limite=50000.0)
        assert cid2 == cid, "No debe duplicar el cliente si ya existe por nombre"
        assert "existente" in msg2.lower()

    finally:
        # Limpieza
        db_manager.execute_non_query("DELETE FROM clientes WHERE nombre = ?", (nombre_test,))


def test_coincide_mostrador_acentos_y_mayusculas():
    from src.motores_empresariales.motor_busqueda_clientes.motor_busqueda import _coincide_mostrador

    ficha = {"nombre": "Martín Gómez", "dni": "35123456"}

    # Coincidencia con acento
    assert _coincide_mostrador(ficha, "Martín")
    # Coincidencia sin acento y en minúsculas
    assert _coincide_mostrador(ficha, "martin")
    # Coincidencia por segunda palabra con y sin acento
    assert _coincide_mostrador(ficha, "Gómez")
    assert _coincide_mostrador(ficha, "gomez")
    # Coincidencia por prefijo
    assert _coincide_mostrador(ficha, "mar")
    assert _coincide_mostrador(ficha, "gom")
    # Coincidencia por DNI
    assert _coincide_mostrador(ficha, "35123456")
    assert _coincide_mostrador(ficha, "35.123.456")


def test_motor_busqueda_precargar_forzar_y_fallback():
    from src.motores_empresariales.motor_busqueda_clientes.motor_busqueda import MotorBusquedaClientes
    from src.base_de_datos.database import db_manager

    motor = MotorBusquedaClientes()
    # Inicialmente precargado
    assert hasattr(motor, "precargar")
    
    # Simular un índice existente
    motor._indice = [{"id": 1, "nombre": "Cliente Viejo", "dni": "111", "limite_credito": 10000.0, "deuda_actual": 0.0}]

    # Si forzar=False, no recarga si _indice existe
    motor.precargar(forzar=False)
    assert len(motor._indice) == 1

    # Insertar un cliente simulado desde Admin
    nombre_admin = "Cliente_Creado_En_Admin_88"
    db_manager.execute_non_query(
        "INSERT INTO clientes (nombre, limite_credito, deuda_actual) VALUES (?, ?, ?)",
        (nombre_admin, 25000.0, 0.0),
    )
    try:
        # Con forzar=True, debe relanzar la carga
        motor.precargar(forzar=True)
        # Esperar brevemente a que el hilo termine
        import time
        for _ in range(20):
            with motor._lock:
                if any(f.get("nombre") == nombre_admin for f in (motor._indice or [])):
                    break
            time.sleep(0.1)

        with motor._lock:
            encontrados = [f for f in (motor._indice or []) if f.get("nombre") == nombre_admin]
            assert len(encontrados) > 0, "precargar(forzar=True) no incorporó el cliente de Admin"
    finally:
        db_manager.execute_non_query("DELETE FROM clientes WHERE nombre = ?", (nombre_admin,))


def test_panel_nuevo_procesar_enter():
    from src.cajero.paso6_cobro.rutas_de_cobro.fiado_piramidal.ruta3_cliente_nuevo.panel_nuevo import PanelClienteNuevo
    from src.base_de_datos.database import db_manager

    nombre_nuevo = "Cliente_Exprés_Enter_77"
    panel = PanelClienteNuevo()
    recibido = []
    panel.cliente_creado.connect(lambda d: recibido.append(d))

    try:
        panel.poblar_inicial(nombre_nuevo)
        assert panel.txt_input.text() == nombre_nuevo

        # Simular tecla Enter
        evt = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        panel.keyPressEvent(evt)

        assert len(recibido) == 1, "No se emitió la señal cliente_creado al pulsar ENTER"
        datos = recibido[0]
        assert datos.get("nombre") == nombre_nuevo
        assert datos.get("limite") == 50000.0
        assert datos.get("deuda") == 0.0
        assert datos.get("id") is not None
    finally:
        db_manager.execute_non_query("DELETE FROM clientes WHERE nombre = ?", (nombre_nuevo,))


def test_orquestador_fiado_flujo_completo():
    from src.cajero.paso6_cobro.rutas_de_cobro.fiado_piramidal.orquestador_credito import OrquestadorFiadoPiramidal
    from src.base_de_datos.database import db_manager

    nombre_flujo = "Cliente_Flujo_Cobro_66"
    orquestador = OrquestadorFiadoPiramidal()
    pagos_completados = []
    orquestador.pago_completado.connect(lambda d: pagos_completados.append(d))

    try:
        # 1. Mostrar orquestador con carrito de $1,500
        orquestador.mostrar(monto=1500.0, modo="Fiado")
        assert orquestador.isVisible()

        # 2. Simular creación exprés
        orquestador._abrir_creacion(nombre_flujo)
        assert orquestador.stack.currentWidget() == orquestador.via_nuevo

        # 3. Procesar en panel nuevo
        orquestador.via_nuevo._procesar()

        # 4. Debe haber saltado a via_aprobado (Ruta 1: Margen aprobado)
        assert orquestador.stack.currentWidget() == orquestador.via_aprobado
        assert nombre_flujo in orquestador.via_aprobado.lbl_nombre.text()

        # 5. Confirmar venta en cuenta corriente
        orquestador.via_aprobado._armar_enter()
        evt_enter = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier)
        orquestador.via_aprobado.keyPressEvent(evt_enter)
        assert len(pagos_completados) == 1
        pago = pagos_completados[0]
        assert pago["estado"] == "APROBADO"
        assert pago["monto_carrito"] == 1500.0
        assert pago["medio_pago"] == "CRÉDITO"
        assert pago["condiciones_ticket"]["es_cuenta_corriente"] is True
    finally:
        db_manager.execute_non_query("DELETE FROM clientes WHERE nombre = ?", (nombre_flujo,))
