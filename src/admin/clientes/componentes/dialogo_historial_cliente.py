from src.utils.qt_compat import qt_exec
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QLineEdit, QMessageBox, QDialog, 
                             QFormLayout, QDoubleSpinBox, QGraphicsDropShadowEffect, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QCursor
from src.base_de_datos.database import db_manager
from src.repositories.cliente_repository import ClienteRepository, FIADO_EXPRESS_LIMITE_DEFAULT


from src.admin.clientes.theme import _CLI

class DialogoHistorialCliente(QDialog):
    """Historial de cuenta corriente del cliente (cargos fiado + abonos)."""

    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.db = db_manager
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


