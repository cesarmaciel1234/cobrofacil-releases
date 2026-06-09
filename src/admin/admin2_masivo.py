from src.utils.theme_manager import theme_manager
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
    QPushButton, QAbstractItemView, QCheckBox, QMessageBox,
    QDialog, QGridLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

class Admin2Masivo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cambio de Precios Masivo"); self.setFixedSize(1100, 750)
        self.setup_ui(); self.cargar_datos()
    def setup_ui(self):
        self.setStyleSheet(" font-family: 'Segoe UI';")
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(0)
        header = QFrame(); header.setFixedHeight(35); header.setStyleSheet("")
        h_layout = QHBoxLayout(header); h_layout.addWidget(QLabel("💹 CAMBIO MASIVO"))
        self.main_layout.addWidget(header)
        search_f = QFrame(); s_layout = QGridLayout(search_f)
        self.txt_f1 = QLineEdit(); s_layout.addWidget(QLabel("Código:"), 0, 0); s_layout.addWidget(self.txt_f1, 0, 1)
        self.main_layout.addWidget(search_f)
        self.tabla = QTableWidget(); self.tabla.setColumnCount(11); self.tabla.setHorizontalHeaderLabels(["✅", "Código", "Nombre", "Unidad", "Categoría", "Costo", "Precio", "Anterior", "Fecha", "Stock", "Margen"])
        self.tabla.setStyleSheet("QHeaderView::section {  }")
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.main_layout.addWidget(self.tabla)
        footer = QFrame(); footer.setFixedHeight(100); f_layout = QHBoxLayout(footer)
        self.btn_conf = QPushButton("💾 CONFIRMAR"); f_layout.addWidget(self.btn_conf)
        self.main_layout.addWidget(footer)
    def cargar_datos(self):
        res = db_manager.execute_query("SELECT id, nombre, precio, stock FROM productos") or []
        self.tabla.setRowCount(len(res))
        for i, row in enumerate(res):
            chk = QTableWidgetItem(); chk.setCheckState(Qt.Unchecked); self.tabla.setItem(i, 0, chk)
            self.tabla.setItem(i, 1, QTableWidgetItem(str(row['id']))); self.tabla.setItem(i, 2, QTableWidgetItem(row['nombre']))
            it_p = QTableWidgetItem(f"{row['precio']:.2f}"); it_p.setBackground(QColor("#E1FFE1")); self.tabla.setItem(i, 6, it_p)
            self.tabla.setItem(i, 9, QTableWidgetItem(str(row['stock'] if 'stock' in row.keys() else 0)))
