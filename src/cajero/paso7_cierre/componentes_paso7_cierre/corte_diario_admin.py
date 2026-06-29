from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton
from PyQt6.QtCore import Qt
from src.utils.qt_compat import qt_exec

class CorteDiarioDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(900, 600)
        self.setObjectName("CorteDiarioMain")
        
        l = QVBoxLayout(self)
        lbl = QLabel("📊 REPORTE DE CORTE DIARIO")
        lbl.setObjectName("CorteDiarioTit")
        l.addWidget(lbl)
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Usuario", "Efectivo", "Tarjeta", "Total", "Faltante"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setObjectName("CorteDiarioTable")
        table.horizontalHeader().setObjectName("CorteDiarioHeader")
        l.addWidget(table)
        
        btn = QPushButton("VOLVER")
        btn.setObjectName("BtnCorteDiario")
        btn.clicked.connect(self.accept)
        l.addWidget(btn)
        
    def mostrar(self):
        qt_exec(self)
