# filtros_inventario.py - Barra de busqueda, categoria y modo de urgencia.
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from src.config import config


class FiltrosInventario(QFrame):
    filtros_cambiados = pyqtSignal()
    urgencia_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(72)
        self.setObjectName("catalogoToolbar")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(14)

        ico_buscar = QLabel("🔍")
        ico_buscar.setStyleSheet("font-size: 18px; background: transparent;")
        layout.addWidget(ico_buscar)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar por nombre, código o ID...")
        self.txt_buscar.setMinimumWidth(320)
        self.txt_buscar.setMinimumHeight(42)
        layout.addWidget(self.txt_buscar)

        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filtros_cambiados.emit)
        self.txt_buscar.textChanged.connect(lambda: self.search_timer.start(400))

        lbl_dep = QLabel("Departamento")
        lbl_dep.setStyleSheet(
            "font-weight: 800; font-size: 12px; color: #334155; background: transparent;"
        )
        layout.addWidget(lbl_dep)

        self.cmb_depto = QComboBox()
        self.cmb_depto.setMinimumWidth(200)
        self.cmb_depto.setMinimumHeight(42)
        self.cmb_depto.currentIndexChanged.connect(self.filtros_cambiados.emit)
        layout.addWidget(self.cmb_depto)

        self.chk_urgencia = QCheckBox("Urgencia: vender sin stock")
        self.chk_urgencia.setToolTip(
            "Solo para emergencias. El cajero podrá vender aunque no haya existencia."
        )
        self.chk_urgencia.setStyleSheet(
            "QCheckBox { font-weight: 800; font-size: 13px; color: #991B1B; padding: 8px 12px; "
            "border: 1px solid #FECACA; border-radius: 8px; background: #FFF7ED; }"
            "QCheckBox::indicator { width: 20px; height: 20px; }"
        )
        self.chk_urgencia.setChecked(bool(config.get("opt_stock_negativo", False)))
        self.chk_urgencia.toggled.connect(self.urgencia_toggled.emit)
        layout.addWidget(self.chk_urgencia)

        layout.addStretch()

    def obtener_texto_buscar(self):
        return self.txt_buscar.text().strip()

    def obtener_departamento_seleccionado(self):
        return self.cmb_depto.currentData()

    def set_chk_urgencia_state(self, checked):
        self.chk_urgencia.blockSignals(True)
        self.chk_urgencia.setChecked(bool(checked))
        self.chk_urgencia.blockSignals(False)

    def set_departamentos(self, departamentos):
        self.cmb_depto.blockSignals(True)
        self.cmb_depto.clear()
        self.cmb_depto.addItem("— Todas las categorías —", None)
        for r in departamentos:
            dep = r.get("nombre") if isinstance(r, dict) else r[1]
            if dep and dep.upper() != "GENERAL":
                self.cmb_depto.addItem(dep, dep)
        self.cmb_depto.blockSignals(False)

    def aplicar_tema(self, bg, text, border):
        self.txt_buscar.setStyleSheet(f"""
            QLineEdit {{ background: {bg}; color: #0F172A; border: 1px solid {border};
            border-radius: 10px; padding: 10px 14px; font-size: 14px; font-weight: 600; }}
            QLineEdit:focus {{ border: 2px solid #2563EB; }}
        """)
        self.cmb_depto.setStyleSheet(f"""
            QComboBox {{ background: {bg}; color: #0F172A; border: 1px solid {border};
            border-radius: 10px; padding: 8px 12px; font-size: 14px; font-weight: 600; }}
            QComboBox:focus {{ border: 2px solid #2563EB; }}
        """)
