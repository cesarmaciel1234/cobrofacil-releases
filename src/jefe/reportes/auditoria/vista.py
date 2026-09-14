"""Cara clara de las líneas. El número sale de consulta.py."""

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.jefe.reportes.auditoria.consulta import comparativa, listar_lineas, totales
from src.jefe.reportes.auditoria.exportar import WorkerExportAudit
from src.jefe.reportes.auditoria.kpis import pie, tarjeta_comparativa
from src.jefe.reportes.financiero.dinero import fmt_plata
from src.jefe.reportes.financiero.paleta import _FIN, _aplicar_paleta_tabla
from src.jefe.reportes.letra import etiqueta, fuente_limpia
from src.jefe.reportes.periodo import montar_botones_periodo, pintar_activo, resolver_rango_periodo


class VistaAuditoria(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("VistaAuditoria")
        self.audit_all_rows = []
        self.audit_offset = 0
        self.is_loading_audit = False
        self._armar()
        self.cargar_datos("Hoy")

    def _armar(self):
        self.setStyleSheet(
            f"QWidget#VistaAuditoria {{ background: {_FIN['bg_page']}; letter-spacing: 0px; }}"
        )
        self.setFont(fuente_limpia(13))
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(12)

        idle = (
            f"QPushButton {{ background: white; color: {_FIN['text_soft']}; font-weight: 400; "
            f"border: 1px solid {_FIN['card_border']}; border-radius: 10px; padding: 8px 16px; letter-spacing: 0px; }}"
            f"QPushButton:hover {{ background: {_FIN['accent_light']}; color: {_FIN['accent']}; }}"
        )
        active = (
            f"QPushButton {{ background: {_FIN['accent']}; color: white; font-weight: 400; "
            f"border: none; border-radius: 10px; padding: 8px 16px; letter-spacing: 0px; }}"
        )
        self._period_btn_idle = idle
        self._period_btn_active = active
        chips = QHBoxLayout()
        self.period_buttons = montar_botones_periodo(chips, self.cargar_datos, idle, active)
        chips.addStretch()
        root.addLayout(chips)

        fila = QHBoxLayout()
        self.txt_audit_prod = QLineEdit()
        self.txt_audit_prod.setPlaceholderText("Producto o codigo")
        self.txt_audit_prod.setStyleSheet(
            f"background: white; border: 1px solid {_FIN['card_border']}; "
            f"border-radius: 8px; padding: 8px 12px; font-weight: 400;"
        )
        b1 = QPushButton("Filtrar")
        b1.clicked.connect(self._buscar_auditoria)
        b2 = QPushButton("Reiniciar")
        b2.clicked.connect(self._limpiar_filtros_audit)
        self.btn_audit_exportar = QPushButton("Exportar")
        self.btn_audit_exportar.clicked.connect(self._exportar_auditoria)
        for b in (b1, b2, self.btn_audit_exportar):
            b.setStyleSheet(idle)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
        fila.addWidget(self.txt_audit_prod, 1)
        fila.addWidget(b1)
        fila.addWidget(b2)
        fila.addWidget(self.btn_audit_exportar)
        root.addLayout(fila)

        self.audit_kpi_layout = QHBoxLayout()
        self.audit_kpi_layout.setSpacing(12)
        root.addLayout(self.audit_kpi_layout)

        self.table_audit = QTableWidget()
        self.table_audit.setColumnCount(11)
        self.table_audit.setHorizontalHeaderLabels([
            "Ticket", "Fecha", "Cajero", "Depto", "Producto",
            "Cant.", "Un.", "Unitario", "Subtotal", "Pago", "Estado",
        ])
        self.table_audit.verticalHeader().setVisible(False)
        self.table_audit.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_audit.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_audit.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        _aplicar_paleta_tabla(self.table_audit)
        self.table_audit.verticalScrollBar().valueChanged.connect(self._on_audit_scroll)
        root.addWidget(self.table_audit, 1)

        pie_f = QFrame()
        pie_f.setStyleSheet(
            f"background: {_FIN['card']}; border: 1px solid {_FIN['card_border']}; border-radius: 12px;"
        )
        pl = QHBoxLayout(pie_f)
        self.lbl_foot_regs = etiqueta("Tickets: 0")
        self.lbl_foot_unidades = etiqueta("Unidades: 0")
        self.lbl_foot_kilos = etiqueta("Peso: 0 kg")
        self.lbl_foot_depto1 = etiqueta("—")
        self.lbl_foot_depto2 = etiqueta("—")
        self.lbl_foot_depto3 = etiqueta("—")
        self.lbl_foot_monto = etiqueta("Facturado: —", 16)
        for w in (
            self.lbl_foot_regs, self.lbl_foot_unidades, self.lbl_foot_kilos,
            self.lbl_foot_depto1, self.lbl_foot_depto2, self.lbl_foot_depto3, self.lbl_foot_monto,
        ):
            pl.addWidget(w)
        root.addWidget(pie_f)

    def _limpiar_filtros_audit(self):
        self.txt_audit_prod.clear()
        self.cargar_datos("Hoy")

    def cargar_datos(self, periodo="Hoy"):
        self.current_period = periodo
        rango = resolver_rango_periodo(periodo, self)
        if rango is None:
            return
        start_str, end_str, etiqueta_r = rango
        self.current_start_str = start_str
        self.current_end_str = end_str
        pintar_activo(self.period_buttons, periodo, self._period_btn_active, self._period_btn_idle, etiqueta_r)
        self._buscar_auditoria()

    def _buscar_auditoria(self):
        start = getattr(self, "current_start_str", None)
        end = getattr(self, "current_end_str", None)
        if not start or not end:
            return
        self.audit_all_rows = listar_lineas(start, end, self.txt_audit_prod.text())
        tot = totales(self.audit_all_rows)
        textos = pie(tot)
        self.lbl_foot_regs.setText(textos["regs"])
        self.lbl_foot_unidades.setText(textos["unidades"])
        self.lbl_foot_kilos.setText(textos["kilos"])
        self.lbl_foot_depto1.setText(textos["depto1"])
        self.lbl_foot_depto2.setText(textos["depto2"])
        self.lbl_foot_depto3.setText(textos["otros"])
        self.lbl_foot_monto.setText(textos["monto"])
        self._pintar_kpis(tot["monto"])
        self.audit_offset = 0
        self.table_audit.setRowCount(0)
        self._load_more_audit_rows()

    def _pintar_kpis(self, monto):
        while self.audit_kpi_layout.count():
            it = self.audit_kpi_layout.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        _, diff = comparativa(self.current_start_str, self.current_end_str)
        comp, tono = tarjeta_comparativa(diff)
        for titulo, valor, bg in (
            ("Facturado", fmt_plata(monto), "#ECFDF5"),
            (f"Vs periodo anterior · {getattr(self, 'current_period', 'Hoy')}", comp, "#FEF2F2" if tono == "red" else "#ECFDF5"),
        ):
            f = QFrame()
            f.setStyleSheet(f"background: {bg}; border: 1px solid {_FIN['card_border']}; border-radius: 12px;")
            l = QVBoxLayout(f)
            l.addWidget(etiqueta(titulo, 12))
            l.addWidget(etiqueta(valor, 18))
            self.audit_kpi_layout.addWidget(f)

    def _load_more_audit_rows(self):
        if self.is_loading_audit or self.audit_offset >= len(self.audit_all_rows):
            return
        self.is_loading_audit = True
        lote = self.audit_all_rows[self.audit_offset:self.audit_offset + 100]
        base = self.table_audit.rowCount()
        self.table_audit.setRowCount(base + len(lote))
        for i, r in enumerate(lote):
            row = base + i
            f_raw = r["fecha"]
            fecha = f_raw.strftime("%Y-%m-%d %H:%M:%S") if hasattr(f_raw, "strftime") else str(f_raw or "")
            cant = f"{r['cantidad']:,.3f}" if r["unidad"] == "KG" else f"{r['cantidad']:,.2f}"
            vals = [
                str(r["id_venta"]), fecha, str(r["usuario"] or ""),
                r["depto"], r["nombre_producto"], cant, r["unidad"],
                fmt_plata(r["precio_unitario"]), fmt_plata(r["subtotal"]),
                str(r["metodo_pago"]), str(r["estado"]),
            ]
            bg = QColor("#FFFFFF" if row % 2 == 0 else "#F1F5F9")
            for c, txt in enumerate(vals):
                it = QTableWidgetItem(txt)
                it.setBackground(bg)
                it.setForeground(QColor("#0F172A"))
                it.setFont(QFont("Segoe UI", 9))
                if c in (5, 7, 8):
                    it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_audit.setItem(row, c, it)
        self.audit_offset += 100
        self.is_loading_audit = False

    def _on_audit_scroll(self, value):
        bar = self.table_audit.verticalScrollBar()
        if value >= bar.maximum() - 5:
            self._load_more_audit_rows()

    def _exportar_auditoria(self):
        if not self.audit_all_rows:
            QMessageBox.information(self, "Exportar", "No hay filas.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel", f"auditoria_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", "Excel (*.xlsx)"
        )
        if not path:
            return
        headers = [
            self.table_audit.horizontalHeaderItem(c).text()
            for c in range(self.table_audit.columnCount())
        ]
        data = []
        for r in self.audit_all_rows:
            f_raw = r["fecha"]
            fecha = f_raw.strftime("%Y-%m-%d %H:%M:%S") if hasattr(f_raw, "strftime") else str(f_raw or "")
            cant = f"{r['cantidad']:,.3f}" if r["unidad"] == "KG" else f"{r['cantidad']:,.2f}"
            data.append([
                str(r["id_venta"]), fecha, str(r["usuario"] or ""),
                r["depto"], r["nombre_producto"], cant, r["unidad"],
                fmt_plata(r["precio_unitario"]), fmt_plata(r["subtotal"]),
                str(r["metodo_pago"]), str(r["estado"]),
            ])
        self.btn_audit_exportar.setEnabled(False)
        self._worker_exp_audit = WorkerExportAudit(path, headers, data)

        def fin(ok, msg):
            self.btn_audit_exportar.setEnabled(True)
            if ok:
                QMessageBox.information(self, "Excel", msg)
            else:
                QMessageBox.warning(self, "Excel", msg)

        self._worker_exp_audit.finished.connect(fin)
        self._worker_exp_audit.start()
