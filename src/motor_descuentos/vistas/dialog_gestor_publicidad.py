from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QLineEdit,
)
from PyQt6.QtCore import Qt
from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad
from src.motor_descuentos.cerebro.motor_ofertas import MotorOfertas
import random


class DialogGestorPublicidad(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestor de publicidad")
        self.setModal(True)
        self.resize(520, 640)
        self.setStyleSheet("""
            QDialog { background: #F8FAFC; }
            QLabel { color: #334155; font-size: 13px; }
            QLineEdit {
                padding: 10px 12px; border: 1px solid #CBD5E1; border-radius: 8px;
                background: #FFFFFF; color: #0F172A;
            }
            QListWidget {
                background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px;
                color: #1E293B; font-size: 13px; padding: 6px;
            }
            QListWidget::item { padding: 6px 8px; border-radius: 6px; }
            QListWidget::item:hover { background: #F1F5F9; }
            QPushButton {
                background: #F1F5F9; color: #1E293B; border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 10px 14px; font-weight: 700;
            }
            QPushButton:hover { background: #E2E8F0; }
            QPushButton#primary {
                background: #FACC15; color: #1E293B; border: none;
            }
        """)
        self.motor_db = MotorOfertas()
        self._init_ui()
        self.cargar_datos()

    def _init_ui(self):
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        info = QLabel(
            "Marcá a mano o al azar qué producto querés empujar en la TV. "
            "Ese es el que se inserta <b>cada 4 tarjetas</b> (ej. ASADO). "
            "Las ofertas del motor de descuentos <b>no</b> entran solas."
        )
        info.setWordWrap(True)
        lay.addWidget(info)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar producto…")
        self.txt_buscar.textChanged.connect(self._filtrar)
        lay.addWidget(self.txt_buscar)

        top = QHBoxLayout()
        btn_azar = QPushButton("Seleccionar 5 al azar")
        btn_azar.clicked.connect(self.seleccionar_azar)
        btn_ofertas = QPushButton("Marcar ofertas")
        btn_ofertas.clicked.connect(self.marcar_ofertas)
        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.clicked.connect(self.limpiar_seleccion)
        top.addWidget(btn_azar)
        top.addWidget(btn_ofertas)
        top.addWidget(btn_limpiar)
        lay.addLayout(top)

        self.list_widget = QListWidget()
        lay.addWidget(self.list_widget)

        btn_guardar = QPushButton("Guardar publicidad")
        btn_guardar.setObjectName("primary")
        btn_guardar.clicked.connect(self.guardar_cambios)
        lay.addWidget(btn_guardar)

    def cargar_datos(self):
        self.list_widget.clear()
        productos = self.motor_db.buscar_productos("", None, False) or []
        motor_publicidad.cargar_configuracion()
        for row in productos:
            if not isinstance(row, dict):
                continue
            nombre = (row.get("nombre") or "").strip()
            if not nombre:
                continue
            pid = row.get("id")
            en_oferta = float(row.get("cant_oferta") or 0) > 0 or float(row.get("precio_oferta_relampago") or 0) > 0
            texto = nombre.upper()
            if en_oferta:
                texto += "  · oferta"
            item = QListWidgetItem(texto)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setData(Qt.ItemDataRole.UserRole, pid)
            item.setData(Qt.ItemDataRole.UserRole + 1, nombre)
            item.setData(Qt.ItemDataRole.UserRole + 2, bool(en_oferta))
            marcado = motor_publicidad.is_promocionado(nombre, pid)
            item.setCheckState(Qt.CheckState.Checked if marcado else Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)

    def _filtrar(self, texto):
        q = texto.lower().strip()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            nombre = str(item.data(Qt.ItemDataRole.UserRole + 1) or "").lower()
            item.setHidden(bool(q) and q not in nombre)

    def seleccionar_azar(self):
        self.limpiar_seleccion()
        visibles = [
            self.list_widget.item(i)
            for i in range(self.list_widget.count())
            if not self.list_widget.item(i).isHidden()
        ]
        random.shuffle(visibles)
        for item in visibles[:5]:
            item.setCheckState(Qt.CheckState.Checked)

    def marcar_ofertas(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole + 2):
                item.setCheckState(Qt.CheckState.Checked)

    def limpiar_seleccion(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)

    def guardar_cambios(self):
        nombres = []
        ids = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() != Qt.CheckState.Checked:
                continue
            nombres.append(item.data(Qt.ItemDataRole.UserRole + 1))
            pid = item.data(Qt.ItemDataRole.UserRole)
            if pid is not None:
                ids.append(pid)
        motor_publicidad.guardar_configuracion(nombres, ids)
        QMessageBox.information(self, "Publicidad", f"Se guardaron {len(nombres)} productos para la TV.")
        self.accept()
