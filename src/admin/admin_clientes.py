from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
import sys
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,

                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QMessageBox, QDialog, 
                             QFormLayout, QDoubleSpinBox, QGraphicsDropShadowEffect, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor
from src.base_de_datos.database import DatabaseManager

class MetricCard(QFrame):
    def __init__(self, titulo, icon, color="#3B82F6", parent=None):
        super().__init__(parent)
        self.setFixedHeight(100)
        self.setStyleSheet(f"background: white; border: 1px solid #E2E8F0; border-radius: 16px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 10, 20, 10)
        lay.setSpacing(15)
        
        icon_frame = QFrame()
        icon_frame.setFixedSize(50, 50)
        icon_frame.setStyleSheet(f"background: {color}20; border-radius: 25px; border: none;")
        i_lay = QVBoxLayout(icon_frame)
        i_lay.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 24px; color: {color}; background: transparent; border: none;")
        i_lay.addWidget(icon_lbl)
        lay.addWidget(icon_frame)
        
        v_lay = QVBoxLayout()
        v_lay.setSpacing(2)
        v_lay.setAlignment(Qt.AlignVCenter)
        self.lbl_tit = QLabel(titulo.upper())
        self.lbl_tit.setStyleSheet(" font-size: 11px; font-weight: 900; letter-spacing: 1px; border: none;")
        v_lay.addWidget(self.lbl_tit)
        
        self.lbl_val = QLabel("0")
        self.lbl_val.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 900; border: none;")
        v_lay.addWidget(self.lbl_val)
        lay.addLayout(v_lay)
        lay.addStretch()

    def set_valor(self, val, is_money=False):
        if is_money:
            self.lbl_val.setText(f"${val:,.2f}")
        else:
            self.lbl_val.setText(str(val))

class DialogoNuevoCliente(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Cliente")
        self.setFixedSize(350, 200)
        self.setStyleSheet("""
            QDialog {  }
            QLabel { font-weight: bold;  }
            QLineEdit, QDoubleSpinBox { 
                padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; background: white; 
            }
            QPushButton {
                 color: #1e293b; border: none; border-radius: 4px; padding: 8px; font-weight: bold;
            }
            QPushButton:hover {  }
        """)
        
        lay = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Juan Pérez")
        
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Opcional")
        
        self.spin_limite = QDoubleSpinBox()
        self.spin_limite.setMaximum(9999999)
        self.spin_limite.setValue(10000.00)
        self.spin_limite.setPrefix("$ ")
        
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("Teléfono:", self.txt_telefono)
        form.addRow("Límite de Crédito:", self.spin_limite)
        
        lay.addLayout(form)
        lay.addStretch()
        
        btn_lay = QHBoxLayout()
        btn_guardar = QPushButton("Guardar Cliente")
        btn_guardar.clicked.connect(self.accept)
        btn_lay.addStretch()
        btn_lay.addWidget(btn_guardar)
        
        lay.addLayout(btn_lay)
        
    def get_data(self):
        return {
            "nombre": self.txt_nombre.text().strip(),
            "telefono": self.txt_telefono.text().strip(),
            "limite_credito": self.spin_limite.value()
        }

class DialogoRecalculoFiado(QDialog):
    def __init__(self, cliente_id, nombre, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.nombre = nombre
        self.db = DatabaseManager()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(650, 500)
        self.setStyleSheet("background: white; border-radius: 15px; border: 2px solid #3B82F6;")
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(25, 25, 25, 25)
        
        lbl_tit = QLabel(f"📈 SIMULADOR DE INFLACIÓN - {self.nombre.upper()}")
        lbl_tit.setStyleSheet("font-size: 16px; font-weight: 900;  border: none;")
        lay.addWidget(lbl_tit)
        
        lbl_sub = QLabel("Calcula la deuda si los productos fiados se cobraran a los precios de HOY.")
        lbl_sub.setStyleSheet(" font-size: 12px; border: none;")
        lay.addWidget(lbl_sub)
        
        self.tabla = QTableWidget(0, 5)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Producto", "Cant", "P. Original", "P. Hoy"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.setStyleSheet("QTableWidget { border: 1px solid #E2E8F0; border-radius: 8px; font-size: 12px; }")
        lay.addWidget(self.tabla)
        
        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet("font-size: 16px; font-weight: 900; border: none;")
        lay.addWidget(self.lbl_resumen)
        
        h_btns = QHBoxLayout()
        btn_cerrar = QPushButton("VOLVER")
        btn_cerrar.setStyleSheet("  padding: 10px 20px; border-radius: 8px; font-weight: 900;")
        btn_cerrar.clicked.connect(self.reject)
        
        btn_imprimir = QPushButton("🖨️ IMPRIMIR REPORTE")
        btn_imprimir.setStyleSheet(" background-color: #3b82f6; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 900;")
        btn_imprimir.clicked.connect(self._imprimir)
        
        h_btns.addWidget(btn_cerrar)
        h_btns.addStretch()
        h_btns.addWidget(btn_imprimir)
        lay.addLayout(h_btns)
        
        self._cargar_datos()

    def _cargar_datos(self):
        # Obtener los cargos (fiados) no pagados completamente
        # Simplificación: Asumimos que los detalles de la venta del cargo representan la deuda original
        res = self.db.execute_query('''
            SELECT c.fecha, v.id as venta_id
            FROM cuenta_corriente c
            JOIN ventas v ON c.venta_id = v.id
            WHERE c.cliente_id = ? AND c.tipo = 'CARGO'
            ORDER BY c.fecha DESC
        ''', (self.cliente_id,))
        
        if not res:
            self.lbl_resumen.setText("No hay registros de compras fiadas para analizar.")
            return

        total_original = 0.0
        total_hoy = 0.0
        
        self.detalles_impresion = []
        
        for cargo in res:
            detalles = self.db.execute_query('''
                SELECT dv.cantidad, dv.precio_unitario, p.nombre, p.precio as precio_hoy 
                FROM detalles_ventas dv
                JOIN productos p ON dv.id_producto = p.id OR dv.id_producto = p.codigo
                WHERE dv.id_venta = ?
            ''', (cargo['venta_id'],))
            
            for d in detalles:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)
                
                f_corta = cargo['fecha'].split(' ')[0]
                cant = float(d['cantidad'])
                p_orig = float(d['precio_unitario'])
                p_hoy = float(d['precio_hoy'])
                
                tot_orig = cant * p_orig
                tot_hoy = cant * p_hoy
                
                total_original += tot_orig
                total_hoy += tot_hoy
                
                self.tabla.setItem(row, 0, QTableWidgetItem(f_corta))
                self.tabla.setItem(row, 1, QTableWidgetItem(d['nombre']))
                self.tabla.setItem(row, 2, QTableWidgetItem(f"{cant:,.2f}"))
                self.tabla.setItem(row, 3, QTableWidgetItem(f"${p_orig:,.2f}"))
                
                it_hoy = QTableWidgetItem(f"${p_hoy:,.2f}")
                if p_hoy > p_orig:
                    it_hoy.setForeground(QColor("#DC2626"))
                self.tabla.setItem(row, 4, it_hoy)
                
                self.detalles_impresion.append({
                    "fecha": f_corta, "nombre": d['nombre'], "cant": cant, "p_orig": p_orig, "p_hoy": p_hoy
                })

        dif = total_hoy - total_original
        color = "#DC2626" if dif > 0 else "#10B981"
        self.lbl_resumen.setText(f"Deuda Histórica: ${total_original:,.2f}  |  Deuda a Precios de Hoy: <span style='color:{color}'>${total_hoy:,.2f}</span> (+${dif:,.2f})")

    def _imprimir(self):
        try:
            from src.hardware.printer import printer_manager
            printer_manager.conectar()
            printer_manager.printer.set(align='center', bold=True, double_height=True)
            printer_manager.printer.text("REPORTE DE INFLACION FIADO\n")
            printer_manager.printer.set(align='center', bold=False, double_height=False)
            printer_manager.printer.text(f"Cliente: {self.nombre}\n")
            printer_manager.printer.text("-" * 32 + "\n")
            
            tot_h = 0
            tot_o = 0
            for d in self.detalles_impresion:
                printer_manager.printer.set(align='left')
                printer_manager.printer.text(f"{d['fecha']} | {d['nombre']}\n")
                printer_manager.printer.text(f"Cant: {d['cant']} | P.Hoy: ${d['p_hoy']} (Antes: ${d['p_orig']})\n")
                tot_h += d['cant'] * d['p_hoy']
                tot_o += d['cant'] * d['p_orig']
                
            printer_manager.printer.text("-" * 32 + "\n")
            printer_manager.printer.set(align='right', bold=True)
            printer_manager.printer.text(f"Deuda Registrada: ${tot_o:,.2f}\n")
            printer_manager.printer.text(f"Deuda Actualizada: ${tot_h:,.2f}\n")
            printer_manager.printer.text(f"Diferencia a favor: ${tot_h - tot_o:,.2f}\n")
            printer_manager.printer.cut()
            QMessageBox.information(self, "Impreso", "Reporte impreso correctamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al imprimir: {e}")

class AdminClientes(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.initUI()
        
    def initUI(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(20)
        
        # Header
        header_lay = QHBoxLayout()
        
        btn_back = QPushButton("🔙 VOLVER AL PANEL")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton {
                background: white;  font-weight: 800; border-radius: 8px; 
                padding: 10px 20px; border: 1px solid #CBD5E1; font-size: 12px; letter-spacing: 1px;
            }
            QPushButton:hover {   }
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        
        header_lay.addWidget(btn_back)
        header_lay.addSpacing(15)
        
        lbl_titulo = QLabel("💎 CARTERA DE CLIENTES Y CRÉDITO")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: 900;  letter-spacing: 1px;")
        
        self.btn_nuevo = QPushButton("+ NUEVO CLIENTE")
        self.btn_nuevo.setCursor(Qt.PointingHandCursor)
        self.btn_nuevo.setStyleSheet("""
            QPushButton {  background-color: #3b82f6; color: white; padding: 12px 24px; font-weight: 900; border-radius: 8px; font-size: 13px; }
            QPushButton:hover {  }
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
        panel_tabla.setStyleSheet("background: white; border: 1px solid #E2E8F0; border-radius: 16px;")
        pt_lay = QVBoxLayout(panel_tabla)
        pt_lay.setContentsMargins(20, 20, 20, 20)
        
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar cliente por nombre...")
        self.txt_buscar.setStyleSheet("padding: 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; ")
        self.txt_buscar.textChanged.connect(self.cargar_clientes)
        pt_lay.addWidget(self.txt_buscar)
        
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Límite", "Deuda Actual", "Días Atraso", "Recálculo 📈", "Acciones"])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setStyleSheet("""
            QTableWidget { border: none; font-size: 13px; }
            QHeaderView::section {  font-weight: 900;  border: none; padding: 12px; }
            QTableWidget::item { padding: 5px; }
        """)
        pt_lay.addWidget(self.tabla)
        lay.addWidget(panel_tabla)
        
        self.cargar_clientes()
        
    def cargar_clientes(self):
        self.tabla.setRowCount(0)
        busqueda = self.txt_buscar.text().strip()
        
        clientes = self.db.execute_query("SELECT * FROM clientes WHERE nombre LIKE ? ORDER BY deuda_actual DESC, nombre ASC", (f"%{busqueda}%",))
        
        total_deuda = 0
        deudores = 0
        max_deuda = 0
        
        if clientes:
            for i, c in enumerate(clientes):
                deuda = float(c['deuda_actual'])
                if deuda > 0:
                    total_deuda += deuda
                    deudores += 1
                    if deuda > max_deuda: max_deuda = deuda
                    
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(c['id'])))
                self.tabla.setItem(i, 1, QTableWidgetItem(c['nombre']))
                self.tabla.setItem(i, 2, QTableWidgetItem(f"${float(c['limite_credito']):,.2f}"))
                
                it_deuda = QTableWidgetItem(f"${deuda:,.2f}")
                if deuda > 0:
                    it_deuda.setForeground(QColor("#EF4444"))
                    it_deuda.setFont(QFont("Arial", 10, QFont.Bold))
                self.tabla.setItem(i, 3, it_deuda)
                
                # Calcular días de atraso
                dias_atraso = 0
                if deuda > 0:
                    # Buscar última compra fiada
                    ultima_compra = self.db.execute_scalar(
                        "SELECT fecha FROM cuenta_corriente WHERE cliente_id = ? AND tipo = 'CARGO' ORDER BY fecha DESC LIMIT 1",
                        (c['id'],)
                    )
                    if ultima_compra:
                        try:
                            # Parse sqlite timestamp
                            dt = datetime.strptime(ultima_compra.split('.')[0], "%Y-%m-%d %H:%M:%S")
                            dias_atraso = (datetime.now() - dt).days
                        except: pass
                        
                it_dias = QTableWidgetItem(f"{dias_atraso} días")
                if dias_atraso > 30:
                    it_dias.setForeground(QColor("#DC2626"))
                    it_dias.setFont(QFont("Arial", 10, QFont.Bold))
                self.tabla.setItem(i, 4, it_dias)
                
                # Botón Simular Inflación
                btn_sim = QPushButton("Ver Actualizado")
                btn_sim.setCursor(Qt.PointingHandCursor)
                if deuda > 0:
                    btn_sim.setStyleSheet("  font-weight: bold; border-radius: 6px; padding: 6px;")
                    qt_exec(btn_sim.clicked.connect(lambda ch, cid=c['id'], cnom=c['nombre']: DialogoRecalculoFiado(cid, cnom, self)))
                else:
                    btn_sim.setEnabled(False)
                    btn_sim.setStyleSheet("background: transparent; color: transparent; border: none;")
                self.tabla.setCellWidget(i, 5, btn_sim)
                
                # Acciones: abono + editar límite de crédito
                acc_w = QWidget()
                acc_lay = QHBoxLayout(acc_w)
                acc_lay.setContentsMargins(2, 2, 2, 2)
                acc_lay.setSpacing(4)

                btn_abonar = QPushButton("Abonar")
                btn_abonar.setCursor(Qt.PointingHandCursor)
                if deuda <= 0:
                    btn_abonar.setEnabled(False)
                    btn_abonar.setStyleSheet("background-color: #94A3B8; color: white; border-radius: 6px; padding: 4px 8px;")
                else:
                    btn_abonar.setStyleSheet("background-color: #3b82f6; color: white; border-radius: 6px; padding: 4px 8px; font-weight: bold;")
                    btn_abonar.clicked.connect(
                        lambda ch, cid=c['id'], cnom=c['nombre'], cdeu=deuda: self.abonar_deuda_admin(cid, cnom, cdeu)
                    )
                acc_lay.addWidget(btn_abonar)

                limite = float(c['limite_credito'])
                btn_limite = QPushButton("Límite")
                btn_limite.setCursor(Qt.PointingHandCursor)
                btn_limite.setToolTip("Ampliar cupo de fiado (Express o habitual)")
                btn_limite.setStyleSheet("background-color: #10B981; color: white; border-radius: 6px; padding: 4px 8px; font-weight: bold;")
                btn_limite.clicked.connect(
                    lambda ch, cid=c['id'], cnom=c['nombre'], lim=limite: self.editar_limite_credito(cid, cnom, lim)
                )
                acc_lay.addWidget(btn_limite)

                self.tabla.setCellWidget(i, 6, acc_w)
                
        self.card_deuda.set_valor(total_deuda, True)
        self.card_activos.set_valor(deudores)
        self.card_mayor.set_valor(max_deuda, True)

    def nuevo_cliente(self):
        dlg = DialogoNuevoCliente(self)
        if qt_exec(dlg):
            data = dlg.get_data()
            if not data['nombre']:
                QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
                return
            self.db.execute_non_query("INSERT INTO clientes (nombre, telefono, limite_credito) VALUES (?, ?, ?)", (data['nombre'], data['telefono'], data['limite_credito']))
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
        monto, ok = QInputDialog.getDouble(self, "Abonar a Deuda", f"Cliente: {nombre}\\nDeuda actual: ${deuda_actual:,.2f}\\n\\nIngrese monto a abonar ($):", 0, 0, deuda_actual, 2)
        if ok and monto > 0:
            nuevo_saldo = deuda_actual - monto
            self.db.execute_non_query("UPDATE clientes SET deuda_actual = ? WHERE id = ?", (nuevo_saldo, cliente_id))
            self.db.execute_non_query("INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) VALUES (?, ?, ?, ?, ?)", (cliente_id, 'ABONO', monto, nuevo_saldo, 'Abono manual desde panel Admin'))
            QMessageBox.information(self, "Éxito", f"Abono registrado.\\nNuevo saldo: ${nuevo_saldo:,.2f}")
            self.cargar_clientes()