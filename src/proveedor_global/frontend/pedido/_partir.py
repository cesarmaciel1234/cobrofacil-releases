from pathlib import Path

raiz = Path(__file__).resolve().parent
texto = (raiz / "panel.py").read_text(encoding="utf-8")
alta = texto.index("class DialogoAltaProveedor")
hilos = texto.index("class _HiloDepartamentos")
pantalla = texto.index("class PanelPedidosAutomaticos")

enc_alta = '''from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
)

from src.proveedor_global.backend.ficha import FichaProveedor


'''
enc_vinc = '''from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QMessageBox, QLineEdit,
    QAbstractItemView, QCompleter,
)
from PyQt6.QtCore import Qt, QTimer, QEvent, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QFont

from src.motor_abastecimiento import MotorAbastecimiento
from src.proveedor_global.backend.ficha import FichaProveedor, etiqueta
from src.proveedor_global.frontend.pedido.alta.dialogo import DialogoAltaProveedor
from src.utils.letra import vestir_id, vestir_nombre


'''
enc_pant = '''from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QFrame,
    QMessageBox, QTextEdit, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from src.config import config
from src.motor_abastecimiento.exportador import generar_texto_whatsapp, mensaje_general
from src.motor_abastecimiento.hilo.hilo import HiloReposicion
from src.motor_inventario.piso.hilo import HiloGuardarPiso
from src.motor_inventario.planilla.orquestador import _cantidad, _motivo
from src.proveedor_global.backend.moneda import texto
from src.proveedor_global.frontend.pedido.vincular.dialogo import DialogoVincularProveedor


'''

(raiz / "alta").mkdir(exist_ok=True)
(raiz / "vincular").mkdir(exist_ok=True)
(raiz / "pantalla").mkdir(exist_ok=True)
(raiz / "alta" / "__init__.py").write_text("", encoding="utf-8")
(raiz / "vincular" / "__init__.py").write_text("", encoding="utf-8")
(raiz / "pantalla" / "__init__.py").write_text("", encoding="utf-8")
(raiz / "alta" / "dialogo.py").write_text(enc_alta + texto[alta:hilos].strip() + "\n", encoding="utf-8")
(raiz / "vincular" / "dialogo.py").write_text(enc_vinc + texto[hilos:pantalla].strip() + "\n", encoding="utf-8")
(raiz / "pantalla" / "panel.py").write_text(enc_pant + texto[pantalla:].strip() + "\n", encoding="utf-8")
(raiz / "panel.py").write_text(
    '"""El pedido está partido: alta, vínculo y pantalla."""\n'
    "from src.proveedor_global.frontend.pedido.alta.dialogo import DialogoAltaProveedor\n"
    "from src.proveedor_global.frontend.pedido.vincular.dialogo import DialogoVincularProveedor\n"
    "from src.proveedor_global.frontend.pedido.pantalla.panel import PanelPedidosAutomaticos\n\n"
    '__all__ = ["DialogoAltaProveedor", "DialogoVincularProveedor", "PanelPedidosAutomaticos"]\n',
    encoding="utf-8",
)
print("listo", len((raiz / "pantalla" / "panel.py").read_text(encoding="utf-8").splitlines()))
