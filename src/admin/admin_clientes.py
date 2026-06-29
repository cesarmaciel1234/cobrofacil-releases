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

# Paleta admin clientes — clara 2026, coherente con reportes
_CLI = {
    "bg": "#F0F4F8",
    "card": "#FFFFFF",
    "border": "#E2E8F0",
    "row_alt": "#F8FAFC",
    "text": "#0F172A",
    "text_soft": "#475569",
    "accent": "#3B82F6",
    "accent_light": "#EFF6FF",
    "accent_hover": "#2563EB",
    "header_bg": "#F1F5F9",
}

class MetricCard(QFrame):
    def __init__(self, titulo, icon, color="#3B82F6", parent=None):
        super().__init__(parent)
        self.setFixedHeight(108)
        self.setStyleSheet(
            f"background: {_CLI['card']}; border: 1px solid {_CLI['border']}; border-radius: 18px;"
        )
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(32)
        shadow.setColor(QColor(15, 23, 42, 18))
        shadow.setOffset(0, 8)
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
        self.lbl_tit.setStyleSheet(
            f"color: {_CLI['text_soft']}; font-size: 11px; font-weight: 900; "
            "letter-spacing: 1px; border: none;"
        )
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
        self.setStyleSheet(f"""
            QDialog {{ background: {_CLI['bg']}; }}
            QLabel {{ color: {_CLI['text_soft']}; font-weight: bold; border: none; }}
            QLineEdit, QDoubleSpinBox {{
                padding: 10px 12px; border: 1px solid {_CLI['border']}; border-radius: 8px;
                background: white; color: {_CLI['text']};
            }}
            QLineEdit:focus, QDoubleSpinBox:focus {{ border: 1px solid {_CLI['accent']}; }}
            QPushButton {{
                background: {_CLI['accent']}; color: white; border: none; border-radius: 8px;
                padding: 10px 18px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {_CLI['accent_hover']}; }}
        """)
        
        lay = QVBoxLayout(self)
        form = QFormLayout()
        
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Juan Pérez")
        
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Opcional")

        self.txt_dni = QLineEdit()
        self.txt_dni.setPlaceholderText("Opcional — 7+ dígitos")

        self.spin_limite = QDoubleSpinBox()
        self.spin_limite.setMaximum(9999999)
        self.spin_limite.setValue(10000.00)
        self.spin_limite.setPrefix("$ ")
        
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("DNI:", self.txt_dni)
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
        dni_raw = self.txt_dni.text().strip()
        dni = ClienteRepository.normalizar_dni(dni_raw) if dni_raw else ""
        return {
            "nombre": self.txt_nombre.text().strip(),
            "telefono": self.txt_telefono.text().strip(),
            "limite_credito": self.spin_limite.value(),
            "dni": dni or None,
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


class DialogoEditarCliente(QDialog):
    """Editar nombre, teléfono, dirección y perfil del cliente."""

    def __init__(self, cliente_id: int, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.db = DatabaseManager()
        self.cliente = ClienteRepository.obtener_por_id(cliente_id) or {}
        self.setWindowTitle("Editar cliente")
        self.setFixedSize(420, 440)
        self.setStyleSheet(f"""
            QDialog {{ background: {_CLI['bg']}; }}
            QLabel {{ color: #334155; font-weight: 700; border: none; }}
            QLineEdit, QComboBox {{
                padding: 10px 12px; border: 1px solid {_CLI['border']};
                border-radius: 10px; background: white; font-size: 14px; color: {_CLI['text']};
            }}
            QLineEdit:focus, QComboBox:focus {{ border: 1px solid {_CLI['accent']}; }}
        """)
        self._build()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)

        tit = QLabel("✏️  EDITAR DATOS DEL CLIENTE")
        tit.setStyleSheet("font-size: 16px; font-weight: 900; color: #1E293B;")
        lay.addWidget(tit)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_nombre = QLineEdit(dict(self.cliente).get("nombre", ""))
        self.txt_nombre.setPlaceholderText("Nombre completo")

        dni_guardado = (dict(self.cliente).get("dni") or "").strip()
        self.txt_dni = QLineEdit(dni_guardado)
        self.txt_dni.setPlaceholderText("7+ dígitos")

        telefono = (dict(self.cliente).get("telefono") or "").strip()
        if telefono and telefono == dni_guardado:
            telefono = ""
        self.txt_telefono = QLineEdit(telefono)
        self.txt_telefono.setPlaceholderText("Teléfono / WhatsApp (opcional)")

        self.txt_direccion = QLineEdit(dict(self.cliente).get("direccion") or "")
        self.txt_direccion.setPlaceholderText("Calle, número, barrio…")

        self.cmb_perfil = QComboBox()
        self.cmb_perfil.addItem("⚡ Express (fiado mostrador)", "express")
        self.cmb_perfil.addItem("Regular (cuenta habitual)", "regular")
        tipo = (dict(self.cliente).get("tipo_cliente") or "regular").lower()
        self.cmb_perfil.setCurrentIndex(0 if tipo == "express" else 1)

        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("DNI:", self.txt_dni)
        form.addRow("Teléfono:", self.txt_telefono)
        form.addRow("Dirección:", self.txt_direccion)
        form.addRow("Perfil:", self.cmb_perfil)
        lay.addLayout(form)
        lay.addStretch()

        foot = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet(
            "QPushButton { background: #E2E8F0; color: #475569; font-weight: 700; "
            "padding: 10px 20px; border-radius: 8px; border: none; }"
        )
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("Guardar")
        btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ok.setStyleSheet(
            "QPushButton { background: #10B981; color: white; font-weight: 900; "
            "padding: 10px 24px; border-radius: 8px; border: none; }"
            "QPushButton:hover { background: #059669; }"
        )
        btn_ok.clicked.connect(self._guardar)
        foot.addWidget(btn_cancel)
        foot.addStretch()
        foot.addWidget(btn_ok)
        lay.addLayout(foot)

        self.txt_nombre.setFocus()
        self.txt_nombre.selectAll()

    def _guardar(self):
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Datos incompletos", "El nombre es obligatorio.")
            return

        dni_raw = self.txt_dni.text().strip()
        dni = ClienteRepository.normalizar_dni(dni_raw) if dni_raw else None
        if dni_raw and not dni:
            QMessageBox.warning(self, "DNI inválido", "El DNI debe tener al menos 7 dígitos.")
            return
        if dni:
            otro = ClienteRepository.buscar_por_dni(dni)
            if otro and int(dict(otro).get("id", 0)) != int(self.cliente_id):
                QMessageBox.warning(self, "DNI duplicado", f"El DNI {dni} ya pertenece a otro cliente.")
                return

        telefono = self.txt_telefono.text().strip()
        direccion = self.txt_direccion.text().strip()
        tipo = self.cmb_perfil.currentData() or "regular"
        ok = self.db.execute_non_query(
            "UPDATE clientes SET nombre = ?, dni = ?, telefono = ?, direccion = ?, tipo_cliente = ? WHERE id = ?",
            (nombre, dni, telefono or None, direccion or None, tipo, self.cliente_id),
        )
        if ok:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "No se pudieron guardar los cambios.")


class DialogoHistorialCliente(QDialog):
    """Historial de cuenta corriente del cliente (cargos fiado + abonos)."""

    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.db = DatabaseManager()
        self.cliente = ClienteRepository.obtener_por_id(cliente_id) or {}
        self._datos_editados = False
        self.setWindowTitle("Historial del cliente")
        self.setMinimumSize(820, 560)
        self.resize(860, 600)
        self.setStyleSheet(f"QDialog {{ background: {_CLI['bg']}; }}")
        self._build()
        self._cargar_movimientos()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(16)

        panel = QFrame()
        panel.setStyleSheet(
            f"QFrame {{ background: {_CLI['card']}; border: 1px solid {_CLI['border']}; border-radius: 18px; }}"
        )
        p_shadow = QGraphicsDropShadowEffect(panel)
        p_shadow.setBlurRadius(32)
        p_shadow.setOffset(0, 8)
        p_shadow.setColor(QColor(15, 23, 42, 16))
        panel.setGraphicsEffect(p_shadow)
        p_lay = QVBoxLayout(panel)
        p_lay.setContentsMargins(22, 20, 22, 20)
        p_lay.setSpacing(12)

        tit_row = QHBoxLayout()
        self.lbl_tit = QLabel()
        self.lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E293B; border: none;")
        tit_row.addWidget(self.lbl_tit, stretch=1)

        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(44, 44)
        btn_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_edit.setToolTip("Editar nombre, teléfono, dirección y perfil")
        btn_edit.setStyleSheet(
            "QPushButton { background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 10px; "
            "font-size: 18px; }"
            "QPushButton:hover { background: #FDE68A; border-color: #F59E0B; }"
        )
        btn_edit.clicked.connect(self._editar_cliente)
        tit_row.addWidget(btn_edit)
        p_lay.addLayout(tit_row)

        self.lbl_meta = QLabel()
        self.lbl_meta.setWordWrap(True)
        self.lbl_meta.setStyleSheet("font-size: 13px; color: #64748B; border: none;")
        p_lay.addWidget(self.lbl_meta)

        self.lbl_contacto = QLabel()
        self.lbl_contacto.setWordWrap(True)
        self.lbl_contacto.setStyleSheet("font-size: 12px; color: #94A3B8; border: none;")
        p_lay.addWidget(self.lbl_contacto)

        self._actualizar_cabecera()

        sub = QLabel("Movimientos de cuenta corriente (fiados y abonos), del más reciente al más antiguo.")
        sub.setStyleSheet("font-size: 12px; color: #94A3B8; border: none;")
        p_lay.addWidget(sub)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Monto", "Saldo", "Descripción", "Ticket",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(48)
        self.tabla.horizontalHeader().setMinimumHeight(44)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #E2E8F0; border-radius: 10px;
                font-size: 13px; background: white; alternate-background-color: #F8FAFC;
            }
            QHeaderView::section {
                font-weight: 900; border: none; padding: 12px 8px;
                background: #F1F5F9; color: #334155; font-size: 11px;
            }
            QTableWidget::item { padding: 10px 8px; }
        """)
        p_lay.addWidget(self.tabla)

        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setStyleSheet("font-size: 13px; font-weight: 700; color: #475569; border: none;")
        p_lay.addWidget(self.lbl_resumen)

        lay.addWidget(panel)

        foot = QHBoxLayout()
        foot.addStretch()
        btn_cerrar = QPushButton("CERRAR")
        btn_cerrar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cerrar.setStyleSheet(
            "QPushButton { background: #3B82F6; color: white; font-weight: 900; "
            "padding: 12px 28px; border-radius: 8px; border: none; font-size: 13px; }"
            "QPushButton:hover { background: #2563EB; }"
        )
        btn_cerrar.clicked.connect(self.accept)
        foot.addWidget(btn_cerrar)
        lay.addLayout(foot)

    def _actualizar_cabecera(self):
        nombre = dict(self.cliente).get("nombre", "—")
        dni = (dict(self.cliente).get("dni") or "").strip() or "—"
        tipo = (dict(self.cliente).get("tipo_cliente") or "regular").lower()
        tipo_txt = "⚡ Express" if tipo == "express" else "Regular"
        limite = float(dict(self.cliente).get("limite_credito") or 0)
        deuda = float(dict(self.cliente).get("deuda_actual") or 0)
        if tipo == "express" and limite <= 0:
            limite = FIADO_EXPRESS_LIMITE_DEFAULT
        disponible = ClienteRepository.credito_disponible(self.cliente)
        telefono = (dict(self.cliente).get("telefono") or "").strip()
        direccion = (dict(self.cliente).get("direccion") or "").strip()

        self.lbl_tit.setText(f"📋  HISTORIAL — {nombre.upper()}")
        self.lbl_meta.setText(
            f"DNI: {dni}  ·  Tipo: {tipo_txt}  ·  "
            f"Límite: ${limite:,.2f}  ·  Deuda: ${deuda:,.2f}  ·  Disponible: ${disponible:,.2f}"
        )
        partes = []
        if telefono:
            partes.append(f"📞 {telefono}")
        if direccion:
            partes.append(f"📍 {direccion}")
        self.lbl_contacto.setText("  ·  ".join(partes) if partes else "Sin teléfono ni dirección — use ✏️ para completar")

    def _editar_cliente(self):
        dlg = DialogoEditarCliente(self.cliente_id, self)
        if qt_exec(dlg) == QDialog.DialogCode.Accepted:
            self._datos_editados = True
            self.cliente = ClienteRepository.obtener_por_id(self.cliente_id) or {}
            self._actualizar_cabecera()
            parent = self.parent()
            if parent and hasattr(parent, "cargar_clientes"):
                parent.cargar_clientes()

    def _cargar_movimientos(self):
        movs = self.db.execute_query(
            "SELECT fecha, tipo, monto, saldo_resultante, descripcion, venta_id "
            "FROM cuenta_corriente WHERE cliente_id = ? ORDER BY fecha DESC, id DESC",
            (self.cliente_id,),
        )
        self.tabla.setRowCount(0)
        if not movs:
            self.lbl_resumen.setText("Sin movimientos registrados para este cliente.")
            return

        total_cargos = 0.0
        total_abonos = 0.0
        for m in movs:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setRowHeight(row, 48)

            fecha_raw = str(dict(m).get("fecha") or "")
            fecha_txt = fecha_raw.split(".")[0] if fecha_raw else "—"
            tipo = (dict(m).get("tipo") or "").upper()
            monto = float(dict(m).get("monto") or 0)
            saldo = float(dict(m).get("saldo_resultante") or 0)
            desc = (dict(m).get("descripcion") or "—").strip()
            venta_id = dict(m).get("venta_id")
            ticket = f"#{venta_id}" if venta_id else "—"

            if tipo == "CARGO":
                total_cargos += monto
            elif tipo == "ABONO":
                total_abonos += monto

            self.tabla.setItem(row, 0, QTableWidgetItem(fecha_txt))

            it_tipo = QTableWidgetItem(tipo)
            it_tipo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            if tipo == "CARGO":
                it_tipo.setForeground(QColor("#DC2626"))
            elif tipo == "ABONO":
                it_tipo.setForeground(QColor("#059669"))
            self.tabla.setItem(row, 1, it_tipo)

            it_monto = QTableWidgetItem(f"${monto:,.2f}")
            if tipo == "CARGO":
                it_monto.setForeground(QColor("#DC2626"))
            elif tipo == "ABONO":
                it_monto.setForeground(QColor("#059669"))
            self.tabla.setItem(row, 2, it_monto)

            self.tabla.setItem(row, 3, QTableWidgetItem(f"${saldo:,.2f}"))
            self.tabla.setItem(row, 4, QTableWidgetItem(desc))
            self.tabla.setItem(row, 5, QTableWidgetItem(ticket))

        self.lbl_resumen.setText(
            f"{len(movs)} movimiento(s)  ·  "
            f"Total fiado: ${total_cargos:,.2f}  ·  "
            f"Total abonado: ${total_abonos:,.2f}"
        )


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
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(9, QHeaderView.ResizeToContents)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(58)
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
                
                btn_sim = QPushButton("Ver Actualizado")
                btn_sim.setCursor(Qt.PointingHandCursor)
                btn_sim.setMinimumHeight(36)
                if deuda > 0:
                    btn_sim.setStyleSheet(
                        "font-weight: bold; border-radius: 8px; padding: 8px 14px; font-size: 12px;"
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
                acc_lay.setContentsMargins(8, 6, 8, 6)
                acc_lay.setSpacing(8)

                btn_abonar = QPushButton("Abonar")
                btn_abonar.setCursor(Qt.PointingHandCursor)
                btn_abonar.setMinimumHeight(36)
                btn_abonar.setMinimumWidth(72)
                if deuda <= 0:
                    btn_abonar.setEnabled(False)
                    btn_abonar.setStyleSheet(
                        "background-color: #94A3B8; color: white; border-radius: 8px; "
                        "padding: 8px 14px; font-size: 12px; font-weight: bold;"
                    )
                else:
                    btn_abonar.setStyleSheet(
                        "background-color: #3b82f6; color: white; border-radius: 8px; "
                        "padding: 8px 14px; font-size: 12px; font-weight: bold;"
                    )
                    btn_abonar.clicked.connect(
                        lambda ch, cid=c['id'], cnom=c['nombre'], cdeu=deuda: self.abonar_deuda_admin(cid, cnom, cdeu)
                    )
                acc_lay.addWidget(btn_abonar)

                btn_limite = QPushButton("Límite")
                btn_limite.setCursor(Qt.PointingHandCursor)
                btn_limite.setMinimumHeight(36)
                btn_limite.setMinimumWidth(72)
                btn_limite.setToolTip("Ampliar cupo de fiado (Express o habitual)")
                btn_limite.setStyleSheet(
                    "background-color: #10B981; color: white; border-radius: 8px; "
                    "padding: 8px 14px; font-size: 12px; font-weight: bold;"
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
