from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from src.base_de_datos.database import db_manager
from src.cerebro_global.auditoria.motor_auditoria import MotorAuditoria
from src.utils.theme_manager import theme_manager
from src.config import config

class AuditoriaMain(QWidget):
    def __init__(self):
        super().__init__()
        self.user_role = "admin"
        self.setup_ui()
        self.cargar_datos()
        self.aplicar_permisos_perfil()

    def showEvent(self, event):
        super().showEvent(event)
        self.aplicar_permisos_perfil()
        self._apply_theme()

    def _apply_theme(self):
        is_dark = theme_manager.is_dark()
        bg = "#1E293B" if is_dark else "#FFFFFF"
        text = "#F8FAFC" if is_dark else "#0F172A"
        border = "#334155" if is_dark else "#E2E8F0"
        main_bg = "#0F172A" if is_dark else "#F8FAFC"
        
        self.setStyleSheet(f"background-color: {main_bg}; color: {text};")
        self.txt_buscar.setStyleSheet(
            f"padding: 10px; font-size: 14px; border: 1px solid {border}; "
            f"border-radius: 8px; background-color: {bg}; color: {text};"
        )
        
        header_style = f"QHeaderView::section {{ background-color: {'#1E293B' if is_dark else '#F8FAFC'}; color: {'#94A3B8' if is_dark else '#64748B'}; font-weight: bold; border: 1px solid {border}; }}"
        self.tabla.setStyleSheet(
            f"QTableWidget {{ background-color: {bg}; color: {text}; gridline-color: {border}; font-size: 15px; border-radius: 8px; border: 1px solid {border}; }}"
            f"QTableWidget::item {{ padding: 6px; }}"
            f"{header_style}"
        )

    def aplicar_permisos_perfil(self):
        rol = config.current_user.get("role", "cajero")
        self.user_role = str(rol).lower()
        
        es_lectura = (self.user_role == "cajero")
        self.btn_aplicar.setEnabled(not es_lectura)
        
        if es_lectura:
            self.btn_aplicar.setStyleSheet(
                "background: #64748B; color: #94A3B8; font-weight: bold; font-size: 16px; padding: 12px 24px; border-radius: 8px; border: none;"
            )
            self.btn_aplicar.setToolTip("Tu perfil de cajero no tiene permiso para aplicar ajustes de stock.")
        else:
            self.btn_aplicar.setStyleSheet(
                "background: #10B981; color: white; font-weight: bold; font-size: 16px; padding: 12px 24px; border-radius: 8px; border: none;"
            )
            self.btn_aplicar.setToolTip("")

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(25, 25, 25, 25)
        root.setSpacing(15)

        # Encabezado
        nav = QHBoxLayout()
        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setStyleSheet("""
            QPushButton {
                background: #64748B; color: white; padding: 10px 20px; 
                border-radius: 8px; font-weight: bold; font-size: 12px; border: none;
            }
            QPushButton:hover { background: #475569; }
        """)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._volver)
        
        title = QLabel("INSPECCIÓN DE INVENTARIO (AUDITORÍA)")
        title.setStyleSheet("font-size: 18px; font-weight: 900; letter-spacing: 0.5px;")
        
        nav.addWidget(btn_back)
        nav.addSpacing(20)
        nav.addWidget(title)
        nav.addStretch()
        root.addLayout(nav)
        
        # Filtro
        filtro_lay = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Filtrar productos por código, nombre o depto...")
        self.txt_buscar.textChanged.connect(self._filtrar)
        
        lbl_buscar = QLabel("🔍 FILTRAR:")
        lbl_buscar.setStyleSheet("font-weight: bold; font-size: 13px;")
        filtro_lay.addWidget(lbl_buscar)
        filtro_lay.addWidget(self.txt_buscar)
        root.addLayout(filtro_lay)

        # Tabla
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["ID", "Código", "Nombre", "Depto", "Stock Sist.", "Conteo Real", "Diferencia"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setDefaultSectionSize(40)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.itemChanged.connect(self._on_item_changed)
        root.addWidget(self.tabla)

        # Bottom
        bot_lay = QHBoxLayout()
        self.btn_aplicar = QPushButton("CONFIRMAR Y APLICAR AJUSTES")
        self.btn_aplicar.setCursor(Qt.PointingHandCursor)
        self.btn_aplicar.clicked.connect(self._aplicar_ajustes)
        bot_lay.addStretch()
        bot_lay.addWidget(self.btn_aplicar)
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
        
        is_dark = theme_manager.is_dark()
        for i, row in enumerate(productos):
            self.tabla.insertRow(i)
            
            p_id = str(row.get('id') or '')
            codigo = str(row.get('codigo') or '')
            nombre = str(row.get('nombre') or '')
            depto = str(row.get('departamento') or 'GENERAL')
            stock = f"{float(row.get('stock') or 0.0):.2f}"
            
            # Celdas solo lectura
            for col, val in enumerate([p_id, codigo, nombre, depto, stock]):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla.setItem(i, col, item)
            
            # Conteo Real (Editable si es admin)
            item_conteo = QTableWidgetItem("")
            if self.user_role == "cajero":
                item_conteo.setFlags(item_conteo.flags() & ~Qt.ItemFlag.ItemIsEditable)
                item_conteo.setBackground(QColor("#334155" if is_dark else "#E2E8F0"))
            else:
                item_conteo.setBackground(QColor("#7C2D12" if is_dark else "#FEF3C7")) # Tono cálido/amarillo premium
            
            self.tabla.setItem(i, 5, item_conteo)
            
            # Diferencia (Solo lectura)
            item_dif = QTableWidgetItem("0.00")
            item_dif.setFlags(item_dif.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.tabla.setItem(i, 6, item_dif)
            
        self.tabla.blockSignals(False)
        self._apply_theme()

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
                dif_item.setText("0.00")
                is_dark = theme_manager.is_dark()
                item.setBackground(QColor("#7C2D12" if is_dark else "#FEF3C7"))
                return
                
            try:
                conteo = float(str_val)
                stock_sis = float(stock_sist_item.text())
                dif = conteo - stock_sis
                
                dif_item.setText(f"{dif:.2f}")
                
                is_dark = theme_manager.is_dark()
                if dif > 0:
                    dif_item.setForeground(QColor("#60A5FA" if is_dark else "#1D4ED8")) # Azul
                elif dif < 0:
                    dif_item.setForeground(QColor("#F87171" if is_dark else "#B91C1C")) # Rojo
                else:
                    dif_item.setForeground(QColor("#F8FAFC" if is_dark else "#0F172A"))
                    
                item.setBackground(QColor("#1E293B" if is_dark else "#FFFFFF"))
            except ValueError:
                pass

    def _aplicar_ajustes(self):
        if self.user_role == "cajero":
            QMessageBox.warning(self, "Acceso Denegado", "Tu perfil de cajero no tiene permiso para modificar o aplicar ajustes de stock.")
            return

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
            self, "Confirmar Ajustes", 
            f"Se aplicarán ajustes de stock a {len(ajustes)} producto(s).\n¿Estás seguro de continuar con la modificación?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            exito = MotorAuditoria.procesar_auditoria(ajustes, config.current_user.get("nombre", "Admin"), db_manager)
            if exito:
                QMessageBox.information(self, "Éxito", "¡El inventario ha sido ajustado y auditado con éxito!")
                self.cargar_datos()
                self.txt_buscar.clear()
            else:
                QMessageBox.warning(self, "Error", "Ocurrió un error al guardar los ajustes en la base de datos.")
