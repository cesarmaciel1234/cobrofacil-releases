# tests/test_paso6_efectivo_velocidad.py
import sys
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QMouseEvent

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app

def test_pantalla_mp_duracion_y_cierre_inmediato(qapp):
    from src.cajero.paso6_cobro.aviso_en_cobro.pantalla_mp import PantallaMP

    pantalla = PantallaMP()
    cerrado = []

    def on_finish():
        cerrado.append(True)

    # 1. Iniciar con duración reducida (efectivo: 400ms)
    pantalla.mostrar_aprobado("$5,000.00", on_finish=on_finish, duracion_ms=400)
    assert pantalla.isVisible()
    assert pantalla._timer.isActive()
    assert pantalla._timer.interval() == 400

    # 2. Pulsar tecla (Enter) debe cerrar de inmediato sin esperar el temporizador
    event_key = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.NoModifier)
    pantalla.keyPressEvent(event_key)

    assert not pantalla._timer.isActive()
    assert not pantalla.isVisible()
    assert len(cerrado) == 1

def test_pantalla_mp_click_cierra_inmediato(qapp):
    from src.cajero.paso6_cobro.aviso_en_cobro.pantalla_mp import PantallaMP
    from PyQt6.QtCore import QPointF

    pantalla = PantallaMP()
    cerrado = []

    def on_finish():
        cerrado.append(True)

    pantalla.mostrar_aprobado("$1,000.00", on_finish=on_finish, duracion_ms=2000)
    assert pantalla._timer.isActive()

    # Click con mouse
    event_mouse = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(10, 10),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.NoModifier
    )
    pantalla.mousePressEvent(event_mouse)

    assert not pantalla._timer.isActive()
    assert not pantalla.isVisible()
    assert len(cerrado) == 1

def test_resumen_vuelto_sin_recargar_css_innecesario(qapp):
    from src.cajero.paso6_cobro.componentes_paso6_cobro.resumen_vuelto.resumen_vuelto import ResumenVuelto

    rv = ResumenVuelto()
    # Cambio positivo inicial
    rv.actualizar_vuelto(500.0)
    assert rv.lbl_vuelto_tit.text() == "SU CAMBIO:"
    assert "$500.00" in rv.lbl_vuelto_val.text()
    assert rv._estado_color == "cambio"

    # Falta dinero (negativo)
    rv.actualizar_vuelto(-200.0)
    assert rv.lbl_vuelto_tit.text() == "FALTA:"
    assert "$200.00" in rv.lbl_vuelto_val.text()
    assert rv._estado_color == "falta"
