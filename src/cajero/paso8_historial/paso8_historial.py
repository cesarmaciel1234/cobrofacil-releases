from src.utils.qt_compat import qt_exec
import sys
from PyQt6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLineEdit, QPushButton, QGridLayout, QComboBox, QDateEdit, QTimeEdit
)
from PyQt6.QtCore import Qt, QDate, QTime, QTimer
from PyQt6.QtGui import QColor, QBrush, QPainter
from datetime import datetime
from src.cajero.paso8_historial.logica.historial_controller import HistorialController

def fmt_moneda(val):
    """ Formatea a moneda regional: $1.234,56 """
    try:
        return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"${val}"


def _fecha_a_texto(fecha_val):
    if fecha_val is None:
        return ""
    if hasattr(fecha_val, "strftime"):
        return fecha_val.strftime("%Y-%m-%d %H:%M:%S")
    return str(fecha_val)

from src.cajero.paso8_historial.componentes_paso8_historial.panel_detalle import PanelDetalle

class DialogoHistorialDia(QDialog):
    # Tamaño modal F3 — proporción lista (izq) / detalle ticket (der)
    _DLG_W = 1060
    _DLG_H = 820

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(self._DLG_W, self._DLG_H)
        
        self.ticket_seleccionado = None
        self.controller = HistorialController()
        self.setup_ui()
        self.apply_glow()
        self.cargar_ventas()

    def apply_glow(self):
        # Se elimina QGraphicsDropShadowEffect por rendimiento.
        pass

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        main_container = QFrame()
        main_container.setObjectName("HistorialMain")
        layout.addWidget(main_container)

        main_vbox = QVBoxLayout(main_container)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # 1. PREMIUM HEADER
        header = QFrame()
        header.setFixedHeight(70)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)
        
        lbl_icon = QLabel("📋")
        lbl_icon.setObjectName("HistorialIcon")
        h_layout.addWidget(lbl_icon)
        
        lbl_titulo = QLabel("HISTORIAL DE CAJA - TURNO ACTUAL")
        lbl_titulo.setObjectName("HistorialTitle")
        h_layout.addWidget(lbl_titulo)
        
        h_layout.addStretch()
        main_vbox.addWidget(header)

        # 2. CONTENT AREA
        content_hbox = QHBoxLayout()
        content_hbox.setContentsMargins(10, 10, 10, 10)
        content_hbox.setSpacing(15)

        # --- LEFT COLUMN (45%) ---
        left_vbox = QVBoxLayout()
        left_vbox.setSpacing(8)
        
        lbl_search = QLabel("Puedes buscar por folio o nombre del ticket:")
        left_vbox.addWidget(lbl_search)
        
        search_bar = QHBoxLayout()
        btn_search = QPushButton("🔍")
        btn_search.setFixedWidth(35)
        self.txt_search = QLineEdit()
        search_bar.addWidget(btn_search)
        search_bar.addWidget(self.txt_search)
        left_vbox.addLayout(search_bar)
        
        self.tabla_tickets = QTableWidget()
        self.tabla_tickets.setColumnCount(4)
        self.tabla_tickets.setHorizontalHeaderLabels(["Folio", "Arts", "Hora", "Total"])
        self.tabla_tickets.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla_tickets.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla_tickets.setColumnWidth(0, 68)
        self.tabla_tickets.setColumnWidth(1, 52)
        self.tabla_tickets.setColumnWidth(2, 96)
        self.tabla_tickets.verticalHeader().setVisible(False)
        self.tabla_tickets.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_tickets.setEditTriggers(QAbstractItemView.NoEditTriggers)
        left_vbox.addWidget(self.tabla_tickets)
        
        # Bottom Filters Left
        filter_grid = QGridLayout()
        filter_grid.setColumnStretch(1, 1)
        
        filter_grid.addWidget(QLabel("Del día:"), 0, 0)
        self.date_filt = QDateEdit(QDate.currentDate())
        self.date_filt.setCalendarPopup(True)
        self.date_filt.dateChanged.connect(self.cargar_ventas)
        filter_grid.addWidget(self.date_filt, 0, 1)
        
        btn_hoy = QPushButton("📅 Hoy")
        btn_hoy.clicked.connect(lambda: self.date_filt.setDate(QDate.currentDate()))
        filter_grid.addWidget(btn_hoy, 0, 2)
        
        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setObjectName("BtnRefresh")
        btn_refresh.setFixedHeight(40)
        btn_refresh.clicked.connect(self.cargar_ventas)
        filter_grid.addWidget(btn_refresh, 0, 3)
        
        # Auditoría / Vigilancia (OCULTO EN PASO 8)
        lbl_met = QLabel("Método:")
        lbl_met.hide()
        filter_grid.addWidget(lbl_met, 2, 0)
        self.cb_metodo = QComboBox()
        self.cb_metodo.addItems(["TODOS", "EFECTIVO", "TARJETA", "TRANSFERENCIA", "MIXTO"])
        self.cb_metodo.hide()
        filter_grid.addWidget(self.cb_metodo, 2, 1, 1, 2)
        
        time_layout = QHBoxLayout()
        self.time_desde = QTimeEdit(QTime(0, 0, 0))
        self.time_hasta = QTimeEdit(QTime(23, 59, 59))
        self.time_desde.hide()
        self.time_hasta.hide()
        lbl_de = QLabel("De:")
        lbl_de.hide()
        lbl_a = QLabel("A:")
        lbl_a.hide()
        time_layout.addWidget(lbl_de)
        time_layout.addWidget(self.time_desde)
        time_layout.addWidget(lbl_a)
        time_layout.addWidget(self.time_hasta)
        filter_grid.addLayout(time_layout, 3, 1, 1, 2)
        
        self.total_card = QFrame()
        self.total_card.hide()
        self.total_card.setObjectName("HistorialTotalCard")
        t_lay = QVBoxLayout(self.total_card)
        t_lay.setContentsMargins(15, 15, 15, 15)
        self.lbl_total_filtrado = QLabel("Ventas en tabla: $0.00")
        self.lbl_total_filtrado.setObjectName("HistorialTotalFiltered")
        self.lbl_total_filtrado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t_lay.addWidget(self.lbl_total_filtrado)
        filter_grid.addWidget(self.total_card, 4, 0, 1, 3)
        
        # --- CONEXIONES (Al final para evitar crashes por widgets no creados) ---
        self.txt_search.textChanged.connect(self.cargar_ventas)
        self.cb_metodo.currentIndexChanged.connect(self.cargar_ventas)
        self.time_desde.timeChanged.connect(self.cargar_ventas)
        self.time_hasta.timeChanged.connect(self.cargar_ventas)
        self.tabla_tickets.itemSelectionChanged.connect(self.mostrar_detalle)
        
        left_vbox.addLayout(filter_grid)
        content_hbox.addLayout(left_vbox, 45)

        # --- RIGHT COLUMN (55%) ---
        self.panel_detalle = PanelDetalle(self)
        self.panel_detalle.set_callbacks(self.cancelar_venta_accion, self.reimprimir_ticket_accion)
        content_hbox.addWidget(self.panel_detalle, 55)
        main_vbox.addLayout(content_hbox)

        # 3. FINAL BOTTOM BAR
        footer = QFrame()
        footer.setFixedHeight(80)
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(30, 0, 30, 0)
        btn_close = QPushButton("Salir")
        btn_close.setObjectName("BtnCloseHist")
        btn_close.setFixedWidth(250)
        btn_close.clicked.connect(self.accept)
        f_layout.addWidget(btn_close)
        f_layout.addStretch()
        main_vbox.addWidget(footer)

    def cargar_ventas(self):
        txt = self.txt_search.text().lower().strip()
        metodo_filt = self.cb_metodo.currentText().upper()
        q_date = self.date_filt.date()
        f_iso = q_date.toString("yyyy-MM-dd")
        f_l1 = q_date.toString("d/M/yyyy")
        f_l2 = q_date.toString("dd/MM/yyyy")
        
        t_desde = self.time_desde.time()
        t_hasta = self.time_hasta.time()
        is_default_time = (t_desde.toString("HH:mm") == "00:00" and t_hasta.toString("HH:mm") == "23:59")
        
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
            cant_arts = r['cant_arts'] if 'cant_arts' in r.keys() else 0
            try:
                f_raw = r['fecha']
                if not f_raw or f_raw == "None": hora_fmt = "00:00 --"
                else:
                    dt = None
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d"):
                        try: dt = datetime.strptime(str(f_raw), fmt); break
                        except: continue
                    hora_fmt = dt.strftime("%I:%M %p").lower() if dt else str(f_raw)
            except: hora_fmt = "S/D"
            
            self.tabla_tickets.setItem(i, 0, QTableWidgetItem(str(r['id'])))
            self.tabla_tickets.setItem(i, 1, QTableWidgetItem(str(int(cant_arts))))
            self.tabla_tickets.setItem(i, 2, QTableWidgetItem(hora_fmt))
            
            is_cancelled = str(r['estado']).upper().startswith("CANCELAD")
            
            it_total = QTableWidgetItem(fmt_moneda(r['total']))
            it_total.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # Use data role for styling in QSS or leave the colors if preferred
            # In QSS we can target properties but not item data easily. We'll use QColor for standard table items.
            color_est = "#ef4444" if is_cancelled else "#1E3A8A"
            it_total.setForeground(QColor(color_est))
            
            # Removido el setBackground manual para permitir que el QSS maneje el alternating row color y la seleccion
            
            self.tabla_tickets.setItem(i, 3, it_total)
            
        self.lbl_total_filtrado.setText(f"Total en pantalla: {fmt_moneda(total_exitoso)}")

    def mostrar_detalle(self):
        rows = self.tabla_tickets.selectedItems()
        if not rows: return
        
        row_idx = rows[0].row()
        id_venta = int(self.tabla_tickets.item(row_idx, 0).text())
        
        v, items = self.controller.get_detalle_venta(id_venta)
        if not v: return
        
        self.ticket_seleccionado = v['id']
        self.panel_detalle.mostrar_venta(v, items)

    def cancelar_venta_accion(self):
        from PyQt6.QtWidgets import QMessageBox
        if not self.ticket_seleccionado: return
        
        v, _ = self.controller.get_detalle_venta(self.ticket_seleccionado)
        if v and str(v['estado']).upper() == 'CANCELADA':
            QMessageBox.warning(self, "Aviso", "Esta venta ya se encuentra cancelada.")
            return

        role = self.controller.is_admin()
        username = self.controller.get_username()
        
        if not role:
            from src.cajero.paso5_terminal.dialogos.dialogo_pin import DialogoPIN
            pin_dlg = DialogoPIN("admin", parent=self)
            from src.utils.qt_compat import qt_exec
            if not qt_exec(pin_dlg) or not pin_dlg.ok:
                return
            username = f"{username} (Autorizado por Admin)"
            
        res = QMessageBox.question(self, "Cancelar Venta", f"¿Seguro que desea cancelar la venta #{self.ticket_seleccionado}?\\n\\n¡CUIDADO! Esto devolverá automáticamente el stock de todos los artículos al inventario.", QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            success = self.controller.cancelar_venta(self.ticket_seleccionado, username)
            if success:
                QMessageBox.information(self, "Éxito", f"Venta #{self.ticket_seleccionado} cancelada correctamente. El inventario ha sido actualizado.")
            else:
                QMessageBox.critical(self, "Error", f"No se pudo cancelar la venta #{self.ticket_seleccionado}. Consulte el archivo de registro.")
            self.cargar_ventas()
            self.mostrar_detalle()

    def reimprimir_ticket_accion(self):
        from PyQt6.QtWidgets import QMessageBox
        if not self.ticket_seleccionado: return
        try:
            self.controller.reimprimir_ticket(self.ticket_seleccionado)
            QMessageBox.information(self, "Éxito", f"Copia del ticket #{self.ticket_seleccionado} enviada a impresora.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo reimprimir: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape: self.accept()
        else: super().keyPressEvent(event)

if __name__ == "__main__":
    # Test block to verify the "Vista"
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # Mock de configuración para prueba local
    class MockConfig:
        current_user = {"username": "CAJERO_TEST", "role": "cajero"}
    
    # Inyectar mock si es necesario
    try:
        from src.config import config
        if not hasattr(config, 'current_user'):
            config.current_user = MockConfig.current_user
    except:
        pass

    dlg = DialogoHistorialDia()
    dlg.show()
    sys.exit(qt_exec(app))