from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt
from src.base_de_datos.database import db_manager
from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
from src.utils.theme_manager import theme_manager

class AuditoriaMain(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(15)

        # Encabezado
        nav = QHBoxLayout()
        btn_back = QPushButton("← Volver")
        btn_back.setStyleSheet("background: #64748B; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        btn_back.clicked.connect(self._volver)
        
        title = QLabel("INSPECCIÓN DE INVENTARIO (AUDITORÍA)")
        title.setStyleSheet("font-size: 20px; font-weight: 900; color: #1E293B;")
        
        nav.addWidget(btn_back)
        nav.addSpacing(20)
        nav.addWidget(title)
        nav.addStretch()
        root.addLayout(nav)
        
        # Filtro
        filtro_lay = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar producto...")
        self.txt_buscar.setStyleSheet("padding: 8px; font-size: 14px; border: 1px solid #CBD5E1; border-radius: 4px;")
        
        # Debounce timer para evitar congelamientos con escáner de código de barras
        from PyQt6.QtCore import QTimer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self._filtrar(self.txt_buscar.text()))
        self.txt_buscar.textChanged.connect(lambda: self.search_timer.start(400))
        
        filtro_lay.addWidget(QLabel("🔍 Buscar:"))
        filtro_lay.addWidget(self.txt_buscar)
        filtro_lay.addStretch()
        root.addLayout(filtro_lay)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["ID", "Código", "Nombre", "Depto", "Stock Sist.", "Conteo Real", "Diferencia"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setDefaultSectionSize(45) # <-- Filas más altas
        self.tabla.setStyleSheet("""
            QTableWidget { font-size: 16px; }
            QTableWidget::item { padding: 5px; }
            QLineEdit { padding: 2px; font-size: 16px; font-weight: bold; }
        """)
        self.tabla.itemChanged.connect(self._on_item_changed)
        root.addWidget(self.tabla)

        # Bottom
        bot_lay = QHBoxLayout()
        btn_aplicar = QPushButton("CONFIRMAR Y APLICAR AJUSTES")
        btn_aplicar.setStyleSheet("background: #10B981; color: white; font-weight: bold; font-size: 16px; padding: 12px; border-radius: 8px;")
        btn_aplicar.clicked.connect(self._aplicar_ajustes)
        bot_lay.addStretch()
        bot_lay.addWidget(btn_aplicar)
        root.addLayout(bot_lay)

    def _volver(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        for widget in app.topLevelWidgets():
            if hasattr(widget, "switch_tab"):
                widget.switch_tab(0)  # Volver al dashboard de admin
                break

    def cargar_datos(self):
        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)
        productos = MotorAuditoria.obtener_inventario(db_manager)
        
        for i, row in enumerate(productos):
            self.tabla.insertRow(i)
            # ["id", "codigo", "nombre", "departamento", "precio", "stock"]
            p_id = str(row['id'] if isinstance(row, dict) else row[0])
            codigo = str(row['codigo'] if isinstance(row, dict) else row[1])
            nombre = str(row['nombre'] if isinstance(row, dict) else row[2])
            depto = str(row['departamento'] if isinstance(row, dict) else row[3])
            stock = str(row['stock'] if isinstance(row, dict) else row[5])
            
            # Celdas solo lectura
            for col, val in enumerate([p_id, codigo, nombre, depto, stock]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla.setItem(i, col, item)
            
            # Conteo Real (Editable)
            item_conteo = QTableWidgetItem("")
            item_conteo.setBackground(Qt.GlobalColor.yellow)
            self.tabla.setItem(i, 5, item_conteo)
            
            # Diferencia (Solo lectura)
            item_dif = QTableWidgetItem("0")
            item_dif.setFlags(item_dif.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(i, 6, item_dif)
            
        self.tabla.blockSignals(False)

    def _filtrar(self, texto):
        t = texto.lower()
        for i in range(self.tabla.rowCount()):
            match = False
            for col in [1, 2, 3]:  # Codigo, Nombre, Depto
                item = self.tabla.item(i, col)
                if item and t in item.text().lower():
                    match = True
                    break
            self.tabla.setRowHidden(i, not match)

    def _on_item_changed(self, item):
        if item.column() == 5:
            row = item.row()
            str_val = item.text().strip()
            
            stock_sist_item = self.tabla.item(row, 4)
            dif_item = self.tabla.item(row, 6)
            
            if not str_val:
                dif_item.setText("0")
                item.setBackground(Qt.GlobalColor.yellow)
                return
                
            try:
                conteo = float(str_val)
                stock_sis = float(stock_sist_item.text())
                dif = conteo - stock_sis
                
                dif_item.setText(f"{dif:.2f}")
                
                if dif > 0:
                    dif_item.setForeground(Qt.GlobalColor.blue)
                elif dif < 0:
                    dif_item.setForeground(Qt.GlobalColor.red)
                else:
                    dif_item.setForeground(Qt.GlobalColor.black)
                    
                item.setBackground(Qt.GlobalColor.white)
            except ValueError:
                pass # Ignorar caracteres no numericos temporales

    def _aplicar_ajustes(self):
        ajustes = []
        for i in range(self.tabla.rowCount()):
            conteo_item = self.tabla.item(i, 5)
            str_val = conteo_item.text().strip() if conteo_item else ""
            if str_val:
                try:
                    p_id = int(self.tabla.item(i, 0).text())
                    nombre = self.tabla.item(i, 2).text()
                    stock_sis = float(self.tabla.item(i, 4).text())
                    conteo = float(str_val)
                    dif = conteo - stock_sis
                    
                    if dif != 0:
                        ajustes.append({
                            "id": p_id,
                            "nombre": nombre,
                            "stock_sistema": stock_sis,
                            "stock_fisico": conteo,
                            "diferencia": dif
                        })
                except ValueError:
                    continue
        
        if not ajustes:
            QMessageBox.information(self, "Auditoría", "No hay conteos modificados para ajustar.")
            return
            
        reply = QMessageBox.question(
            self, "Confirmar", 
            f"Se aplicarán ajustes a {len(ajustes)} producto(s). ¿Estás seguro de modificar el stock?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            exito = MotorAuditoria.procesar_auditoria(ajustes, "Admin", db_manager)
            if exito:
                QMessageBox.information(self, "Éxito", "¡El stock ha sido ajustado correctamente!")
                self.cargar_datos() # Recargar la grilla para ver los nuevos stocks
                self.txt_buscar.clear()
            else:
                QMessageBox.warning(self, "Error", "Ocurrió un error al guardar los ajustes en la base de datos.")
