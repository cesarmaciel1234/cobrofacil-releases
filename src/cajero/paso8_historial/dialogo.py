from PyQt6.QtWidgets import QDialog, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from datetime import datetime

from src.cajero.paso8_historial.logica.historial_controller import HistorialController
from src.cajero.paso8_historial.logica.formato import fmt_moneda
from src.cajero.paso8_historial.logica.teclas import aplicar_tecla
from src.cajero.paso8_historial.ui.armar import setup_ui


class DialogoHistorialDia(QDialog):
    _DLG_W = 1060
    _DLG_H = 820

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self._DLG_W, self._DLG_H)
        self.ticket_seleccionado = None
        self.controller = HistorialController()
        setup_ui(self)
        self.cargar_ventas()

    def cargar_ventas(self):
        txt = self.txt_search.text().lower().strip()
        metodo_filt = self.cb_metodo.currentText().upper()
        q_date = self.date_filt.date()
        f_iso = q_date.toString("yyyy-MM-dd")
        f_l1 = q_date.toString("d/M/yyyy")
        f_l2 = q_date.toString("dd/MM/yyyy")

        t_desde = self.time_desde.time()
        t_hasta = self.time_hasta.time()
        is_default_time = (
            t_desde.toString("HH:mm") == "00:00" and t_hasta.toString("HH:mm") == "23:59"
        )

        filtered_res, total_exitoso = self.controller.get_ventas(
            txt_search=txt, metodo_filt=metodo_filt,
            q_date_iso=f_iso, q_date_l1=f_l1, q_date_l2=f_l2,
            t_desde=t_desde, t_hasta=t_hasta, is_default_time=is_default_time
        )

        self.tabla_tickets.setRowCount(0)
        if not filtered_res:
            self.lbl_total_filtrado.setText("Sin resultados")
            return

        self.tabla_tickets.setRowCount(len(filtered_res))
        for i, r in enumerate(filtered_res):
            cant_arts = r["cant_arts"] if "cant_arts" in r.keys() else 0
            try:
                f_raw = r["fecha"]
                if not f_raw or f_raw == "None":
                    hora_fmt = "00:00 --"
                else:
                    dt = None
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d"):
                        try:
                            dt = datetime.strptime(str(f_raw), fmt)
                            break
                        except Exception:
                            continue
                    hora_fmt = dt.strftime("%I:%M %p").lower() if dt else str(f_raw)
            except Exception:
                hora_fmt = "S/D"

            self.tabla_tickets.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.tabla_tickets.setItem(i, 1, QTableWidgetItem(str(int(cant_arts))))
            self.tabla_tickets.setItem(i, 2, QTableWidgetItem(hora_fmt))

            is_cancelled = str(r["estado"]).upper().startswith("CANCELAD")
            it_total = QTableWidgetItem(fmt_moneda(r["total"]))
            it_total.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            it_total.setForeground(QColor("#ef4444" if is_cancelled else "#1E3A8A"))
            self.tabla_tickets.setItem(i, 3, it_total)

        self.lbl_total_filtrado.setText(f"Total en pantalla: {fmt_moneda(total_exitoso)}")

    def mostrar_detalle(self):
        rows = self.tabla_tickets.selectedItems()
        if not rows:
            return
        row_idx = rows[0].row()
        id_venta = int(self.tabla_tickets.item(row_idx, 0).text())
        v, items = self.controller.get_detalle_venta(id_venta)
        if not v:
            return
        self.ticket_seleccionado = v["id"]
        self.panel_detalle.mostrar_venta(v, items)

    def cancelar_venta_accion(self):
        if not self.ticket_seleccionado:
            return
        v, _ = self.controller.get_detalle_venta(self.ticket_seleccionado)
        if v and str(v["estado"]).upper() == "CANCELADA":
            QMessageBox.warning(self, "Aviso", "Esta venta ya se encuentra cancelada.")
            return

        role = self.controller.is_admin()
        username = self.controller.get_username()

        if not role:
            from src.cajero.paso5_terminal.dialogos.dialogo_pin import DialogoPIN
            from src.utils.qt_compat import qt_exec
            pin_dlg = DialogoPIN("admin", parent=self)
            if not qt_exec(pin_dlg) or not pin_dlg.ok:
                return
            username = f"{username} (Autorizado por Admin)"

        res = QMessageBox.question(
            self,
            "Cancelar Venta",
            f"¿Seguro que desea cancelar la venta #{self.ticket_seleccionado}?\n\n"
            "Esto devolverá el stock de todos los artículos al inventario.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if res == QMessageBox.Yes:
            success = self.controller.cancelar_venta(self.ticket_seleccionado, username)
            if success:
                QMessageBox.information(
                    self, "Éxito",
                    f"Venta #{self.ticket_seleccionado} cancelada. Inventario actualizado.",
                )
            else:
                QMessageBox.critical(
                    self, "Error",
                    f"No se pudo cancelar la venta #{self.ticket_seleccionado}.",
                )
            self.cargar_ventas()
            self.mostrar_detalle()

    def reimprimir_ticket_accion(self):
        if not self.ticket_seleccionado:
            return
        try:
            self.controller.reimprimir_ticket(self.ticket_seleccionado)
            QMessageBox.information(
                self, "Éxito",
                f"Copia del ticket #{self.ticket_seleccionado} enviada a impresora.",
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo reimprimir: {e}")

    def keyPressEvent(self, event):
        if not aplicar_tecla(self, event):
            super().keyPressEvent(event)
