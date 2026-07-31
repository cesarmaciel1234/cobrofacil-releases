from src.utils.qt_compat import qt_exec
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QMessageBox, QDialog, 
                             QFormLayout, QDoubleSpinBox, QGraphicsDropShadowEffect, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor
from src.base_de_datos.database import DatabaseManager
from src.repositories.cliente_repository import ClienteRepository, FIADO_EXPRESS_LIMITE_DEFAULT


from src.admin.clientes.theme import _CLI

from src.admin.clientes.componentes.metric_card import MetricCard
from src.admin.clientes.componentes.dialogo_nuevo_cliente import DialogoNuevoCliente
from src.admin.clientes.componentes.dialogo_recalculo_fiado import DialogoRecalculoFiado
from src.admin.clientes.componentes.dialogo_editar_cliente import DialogoEditarCliente
from src.admin.clientes.componentes.dialogo_historial_cliente import DialogoHistorialCliente

class AdminClientes(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.initUI()
        
    def initUI(self):
        self.setStyleSheet(f"background: {_CLI['bg']};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)
        
        # Header
        header_lay = QHBoxLayout()
        
        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: white; color: {_CLI['text']}; font-weight: 800; border-radius: 10px;
                padding: 10px 20px; border: 1px solid {_CLI['border']}; font-size: 12px; letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: {_CLI['accent_light']}; color: {_CLI['accent']}; border-color: #BFDBFE; }}
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        
        header_lay.addWidget(btn_back)
        header_lay.addSpacing(15)
        
        lbl_titulo = QLabel("💎 CARTERA DE CLIENTES Y CRÉDITO")
        lbl_titulo.setStyleSheet(
            f"font-size: 22px; font-weight: 900; color: {_CLI['text']}; letter-spacing: 0.5px; border: none;"
        )
        
        self.btn_nuevo = QPushButton("+ NUEVO CLIENTE")
        self.btn_nuevo.setCursor(Qt.PointingHandCursor)
        self.btn_nuevo.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {_CLI['accent']}, stop:1 {_CLI['accent_hover']});
                color: white; padding: 12px 24px; font-weight: 900; border-radius: 10px; font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{ background: {_CLI['accent_hover']}; }}
        """)
        self.btn_nuevo.clicked.connect(self.nuevo_cliente)
        
        header_lay.addWidget(lbl_titulo)
        header_lay.addStretch()
        header_lay.addWidget(self.btn_nuevo)
        lay.addLayout(header_lay)
        
        # Tarjetas 3D
        cards_lay = QHBoxLayout()
        cards_lay.setSpacing(20)
        self.card_deuda = MetricCard("Deuda Total en la Calle", "💸", "#EF4444")
        self.card_activos = MetricCard("Deudores Activos", "👥", "#3B82F6")
        self.card_mayor = MetricCard("Mayor Deuda", "🏆", "#F59E0B")
        cards_lay.addWidget(self.card_deuda)
        cards_lay.addWidget(self.card_activos)
        cards_lay.addWidget(self.card_mayor)
        lay.addLayout(cards_lay)
        
        # Tabla
        panel_tabla = QFrame()
        panel_tabla.setStyleSheet(
            f"background: {_CLI['card']}; border: 1px solid {_CLI['border']}; border-radius: 18px;"
        )
        tbl_shadow = QGraphicsDropShadowEffect(panel_tabla)
        tbl_shadow.setBlurRadius(36)
        tbl_shadow.setOffset(0, 8)
        tbl_shadow.setColor(QColor(15, 23, 42, 16))
        panel_tabla.setGraphicsEffect(tbl_shadow)
        pt_lay = QVBoxLayout(panel_tabla)
        pt_lay.setContentsMargins(20, 20, 20, 20)
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por nombre o DNI...")
        self.txt_buscar.setStyleSheet(f"""
            QLineEdit {{
                padding: 14px 16px; border: 1px solid {_CLI['border']}; border-radius: 10px;
                font-size: 14px; background: {_CLI['row_alt']}; color: {_CLI['text']};
            }}
            QLineEdit:focus {{
                border: 1px solid {_CLI['accent']}; background: white;
            }}
        """)
        self.txt_buscar.textChanged.connect(self.cargar_clientes)
        pt_lay.addWidget(self.txt_buscar)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(10)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Nombre", "DNI", "Tipo", "Límite", "Deuda", "Disponible",
            "Días", "Recálculo", "Acciones",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeMode.Interactive)
        self.tabla.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(8, 135)
        self.tabla.setColumnWidth(9, 175)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(54)
        self.tabla.horizontalHeader().setMinimumHeight(46)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                border: none; font-size: 13px; gridline-color: transparent;
                background: white; alternate-background-color: {_CLI['row_alt']};
                color: {_CLI['text']};
            }}
            QHeaderView::section {{
                font-weight: 900; border: none; padding: 14px 10px;
                background: {_CLI['header_bg']}; color: #334155; font-size: 11px;
                border-bottom: 2px solid {_CLI['accent']};
            }}
            QTableWidget::item {{ padding: 14px 10px; }}
            QTableWidget::item:selected {{ background: {_CLI['accent_light']}; color: #1E40AF; }}
        """)
        self.tabla.setToolTip("Clic en una fila para ver el historial del cliente")
        self.tabla.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.tabla.cellClicked.connect(self._on_fila_cliente_clic)
        pt_lay.addWidget(self.tabla)
        lay.addWidget(panel_tabla)
        
        self.cargar_clientes()
        
    def cargar_clientes(self):
        self.tabla.setRowCount(0)
        busqueda = self.txt_buscar.text().strip()
        
        clientes = self.db.execute_query(
            "SELECT * FROM clientes WHERE nombre LIKE ? OR COALESCE(dni, '') LIKE ? "
            "ORDER BY deuda_actual DESC, nombre ASC",
            (f"%{busqueda}%", f"%{busqueda}%"),
        )
        
        total_deuda = 0
        deudores = 0
        max_deuda = 0
        
        if clientes:
            for i, c in enumerate(clientes):
                deuda = float(dict(c).get('deuda_actual') or 0)
                limite = float(dict(c).get('limite_credito') or 0)
                disponible = ClienteRepository.credito_disponible(c)
                dni = (dict(c).get('dni') or '').strip()
                tipo = (dict(c).get('tipo_cliente') or 'regular').lower()
                tipo_txt = "⚡ Express" if tipo == 'express' else "Regular"
                if tipo == 'express' and limite <= 0:
                    limite = FIADO_EXPRESS_LIMITE_DEFAULT

                if deuda > 0:
                    total_deuda += deuda
                    deudores += 1
                    if deuda > max_deuda:
                        max_deuda = deuda
                    
                self.tabla.insertRow(i)
                self.tabla.setRowHeight(i, 58)
                it_id = QTableWidgetItem(str(c['id']))
                it_id.setData(Qt.ItemDataRole.UserRole, int(c['id']))
                self.tabla.setItem(i, 0, it_id)
                self.tabla.setItem(i, 1, QTableWidgetItem(c['nombre']))
                self.tabla.setItem(i, 2, QTableWidgetItem(dni or "—"))
                it_tipo = QTableWidgetItem(tipo_txt)
                if tipo == 'express':
                    it_tipo.setForeground(QColor("#059669"))
                    it_tipo.setFont(QFont("Arial", 10, QFont.Bold))
                self.tabla.setItem(i, 3, it_tipo)
                self.tabla.setItem(i, 4, QTableWidgetItem(f"${limite:,.2f}"))
                
                it_deuda = QTableWidgetItem(f"${deuda:,.2f}")
                if deuda > 0:
                    it_deuda.setForeground(QColor("#EF4444"))
                    it_deuda.setFont(QFont("Arial", 10, QFont.Bold))
                self.tabla.setItem(i, 5, it_deuda)

                it_disp = QTableWidgetItem(f"${disponible:,.2f}")
                if disponible <= 0:
                    it_disp.setForeground(QColor("#DC2626"))
                elif disponible < limite * 0.2:
                    it_disp.setForeground(QColor("#F59E0B"))
                self.tabla.setItem(i, 6, it_disp)
                
                dias_atraso = 0
                if deuda > 0:
                    ultima_compra = self.db.execute_scalar(
                        "SELECT fecha FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'CARGO' ORDER BY fecha DESC LIMIT 1",
                        (c['id'],)
                    )
                    if ultima_compra:
                        try:
                            dt = datetime.strptime(str(ultima_compra).split('.')[0], "%Y-%m-%d %H:%M:%S")
                            dias_atraso = (datetime.now() - dt).days
                        except Exception:
                            pass
                        
                it_dias = QTableWidgetItem(f"{dias_atraso} días")
                if dias_atraso > 30:
                    it_dias.setForeground(QColor("#DC2626"))
                    it_dias.setFont(QFont("Arial", 10, QFont.Bold))
                self.tabla.setItem(i, 7, it_dias)
                
                btn_sim = QPushButton("🔄 Recalcular")
                btn_sim.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_sim.setFixedHeight(32)
                if deuda > 0:
                    btn_sim.setStyleSheet(
                        "background-color: #F8FAFC; color: #2563EB; border: 1px solid #CBD5E1; "
                        "font-weight: bold; border-radius: 6px; padding: 4px 10px; font-size: 12px;"
                    )
                    btn_sim.clicked.connect(
                        lambda ch, cid=c['id'], cnom=c['nombre']: self._abrir_recalculo(cid, cnom)
                    )
                else:
                    btn_sim.setEnabled(False)
                    btn_sim.setStyleSheet("background: transparent; color: transparent; border: none;")
                self.tabla.setCellWidget(i, 8, btn_sim)
                
                acc_w = QWidget()
                acc_lay = QHBoxLayout(acc_w)
                acc_lay.setContentsMargins(4, 2, 4, 2)
                acc_lay.setSpacing(6)

                btn_abonar = QPushButton("Abonar")
                btn_abonar.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_abonar.setFixedHeight(32)
                btn_abonar.setMinimumWidth(68)
                if deuda <= 0:
                    btn_abonar.setEnabled(False)
                    btn_abonar.setStyleSheet(
                        "background-color: #94A3B8; color: white; border-radius: 6px; "
                        "padding: 4px 10px; font-size: 12px; font-weight: bold; border: none;"
                    )
                else:
                    btn_abonar.setStyleSheet(
                        "background-color: #3B82F6; color: white; border-radius: 6px; "
                        "padding: 4px 10px; font-size: 12px; font-weight: bold; border: none;"
                    )
                    btn_abonar.clicked.connect(
                        lambda ch, cid=c['id'], cnom=c['nombre'], cdeu=deuda: self.abonar_deuda_admin(cid, cnom, cdeu)
                    )
                acc_lay.addWidget(btn_abonar)

                btn_limite = QPushButton("Límite")
                btn_limite.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_limite.setFixedHeight(32)
                btn_limite.setMinimumWidth(68)
                btn_limite.setToolTip("Ampliar cupo de fiado (Express o habitual)")
                btn_limite.setStyleSheet(
                    "background-color: #10B981; color: white; border-radius: 6px; "
                    "padding: 4px 10px; font-size: 12px; font-weight: bold; border: none;"
                )
                btn_limite.clicked.connect(
                    lambda ch, cid=c['id'], cnom=c['nombre'], lim=limite: self.editar_limite_credito(cid, cnom, lim)
                )
                acc_lay.addWidget(btn_limite)

                self.tabla.setCellWidget(i, 9, acc_w)
                
        self.card_deuda.set_valor(total_deuda, True)
        self.card_activos.set_valor(deudores)
        self.card_mayor.set_valor(max_deuda, True)

    def _on_fila_cliente_clic(self, row, col):
        """Abre historial al clic en datos del cliente (no en botones de acción)."""
        if col >= 8:
            return
        item = self.tabla.item(row, 0)
        if not item:
            return
        cliente_id = item.data(Qt.ItemDataRole.UserRole)
        if cliente_id is None:
            try:
                cliente_id = int(item.text())
            except (TypeError, ValueError):
                return
        self._abrir_historial_cliente(int(cliente_id))

    def _abrir_historial_cliente(self, cliente_id):
        dlg = DialogoHistorialCliente(cliente_id, self)
        qt_exec(dlg)

    def _abrir_recalculo(self, cliente_id, nombre):
        dlg = DialogoRecalculoFiado(cliente_id, nombre, self)
        qt_exec(dlg)

    def nuevo_cliente(self):
        dlg = DialogoNuevoCliente(self)
        if qt_exec(dlg):
            data = dlg.get_data()
            if not data['nombre']:
                QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
                return
            if data['dni']:
                if ClienteRepository.buscar_por_dni(data['dni']):
                    QMessageBox.warning(self, "Error", f"Ya existe un cliente con DNI {data['dni']}.")
                    return
            elif dlg.txt_dni.text().strip() and not data['dni']:
                QMessageBox.warning(self, "Error", "DNI inválido (mínimo 7 dígitos).")
                return
            self.db.execute_non_query(
                "INSERT INTO clientes (nombre, telefono, limite_credito, dni, tipo_cliente) "
                "VALUES (?, ?, ?, ?, 'regular')",
                (data['nombre'], data['telefono'], data['limite_credito'], data['dni']),
            )
            self.cargar_clientes()

    def editar_limite_credito(self, cliente_id, nombre, limite_actual):
        from PyQt6.QtWidgets import QInputDialog
        nuevo, ok = QInputDialog.getDouble(
            self,
            "Límite de crédito",
            f"Cliente: {nombre}\nLímite actual: ${limite_actual:,.2f}\n\nNuevo límite ($):",
            limite_actual,
            0,
            99_999_999,
            2,
        )
        if ok and nuevo >= 0:
            self.db.execute_non_query(
                "UPDATE clientes SET limite_credito = ? WHERE id = ?",
                (nuevo, cliente_id),
            )
            QMessageBox.information(self, "Listo", f"Límite actualizado a ${nuevo:,.2f}")
            self.cargar_clientes()

    def abonar_deuda_admin(self, cliente_id, nombre, deuda_actual):
        from PyQt6.QtWidgets import QInputDialog
        monto, ok = QInputDialog.getDouble(
            self,
            "Abonar a Deuda",
            f"Cliente: {nombre}\nDeuda actual: ${deuda_actual:,.2f}\n\nIngrese monto a abonar ($):",
            0, 0, deuda_actual, 2,
        )
        if ok and monto > 0:
            nuevo_saldo = deuda_actual - monto
            self.db.execute_non_query("UPDATE clientes SET deuda_actual = ? WHERE id = ?", (nuevo_saldo, cliente_id))
            self.db.execute_non_query(
                "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) "
                "VALUES (?, ?, ?, ?, ?)",
                (cliente_id, 'ABONO', monto, nuevo_saldo, 'Abono manual desde panel Admin'),
            )
            QMessageBox.information(self, "Éxito", f"Abono registrado.\nNuevo saldo: ${nuevo_saldo:,.2f}")
            self.cargar_clientes()
