from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush
from datetime import datetime
from src.cajero.paso8_historial.componentes_paso8_historial.stamp_label import StampLabel

def fmt_moneda(val):
    try:
        return f"${val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return f"${val}"

class PanelDetalle(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.ticket_seleccionado = None
        
        right_vbox = QVBoxLayout(self)
        right_vbox.setContentsMargins(0, 0, 0, 0)
        right_vbox.setSpacing(10)
        
        self.lbl_preview_title = QLabel("Seleccione un Ticket")
        self.lbl_preview_title.setObjectName("lblTicketPreview")
        self.lbl_preview_title.setAlignment(Qt.AlignCenter)
        right_vbox.addWidget(self.lbl_preview_title)
        
        self.frame_det = QFrame()
        self.frame_det.setObjectName("frameDetalle")
        det_layout = QVBoxLayout(self.frame_det)
        det_layout.setContentsMargins(20, 20, 20, 20)
        det_layout.setSpacing(10)
        
        info_grid = QGridLayout()
        info_grid.addWidget(QLabel("<b>Folio:</b>"), 0, 0)
        self.lbl_det_folio = QLabel("-")
        info_grid.addWidget(self.lbl_det_folio, 0, 1)
        
        info_grid.addWidget(QLabel("<b>Cajero:</b>"), 1, 0)
        self.lbl_det_cajero = QLabel("-")
        info_grid.addWidget(self.lbl_det_cajero, 1, 1)
        
        info_grid.addWidget(QLabel("<b>Cliente:</b>"), 2, 0)
        self.lbl_det_cliente = QLabel("Público en general")
        info_grid.addWidget(self.lbl_det_cliente, 2, 1)
        
        info_grid.addWidget(QLabel("<b>Pago:</b>"), 3, 0)
        self.lbl_det_metodo = QLabel("-")
        self.lbl_det_metodo.setStyleSheet("color: #1C2E85; font-weight: bold;")
        info_grid.addWidget(self.lbl_det_metodo, 3, 1)
        
        det_layout.addLayout(info_grid)
        
        self.lbl_det_fecha = QLabel("01 de Enero 2026 12:00 am")
        self.lbl_det_fecha.setAlignment(Qt.AlignCenter)
        det_layout.addWidget(self.lbl_det_fecha)
        
        self.tabla_detalle = QTableWidget()
        self.tabla_detalle.setColumnCount(3)
        self.tabla_detalle.setHorizontalHeaderLabels(["Cant.", "Descripción", "Importe"])
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_detalle.setColumnWidth(0, 56)
        self.tabla_detalle.setColumnWidth(2, 110)
        self.tabla_detalle.verticalHeader().setVisible(False)
        self.tabla_detalle.setFixedHeight(255)
        det_layout.addWidget(self.tabla_detalle)
        
        # --- SELLO CANCELADO (Overlay) ---
        self.sello_cancelado = StampLabel("CANCELADO", self.frame_det)
        self.sello_cancelado.move(80, 205)
        
        pago_layout = QGridLayout()
        pago_layout.setSpacing(6)
        
        self.lbl_det_desc_tit = QLabel("<b>Descuento:</b>")
        self.lbl_det_desc_tit.setStyleSheet("color: #10B981; font-size: 14px;")
        self.lbl_det_desc = QLabel("-$0,00")
        self.lbl_det_desc.setStyleSheet("color: #10B981; font-size: 14px; font-weight: bold;")
        self.lbl_det_desc.setAlignment(Qt.AlignRight)
        
        self.lbl_det_rec_tit = QLabel("<b>Recargo:</b>")
        self.lbl_det_rec_tit.setStyleSheet("color: #F59E0B; font-size: 14px;")
        self.lbl_det_rec = QLabel("+$0,00")
        self.lbl_det_rec.setStyleSheet("color: #F59E0B; font-size: 14px; font-weight: bold;")
        self.lbl_det_rec.setAlignment(Qt.AlignRight)
        
        pago_layout.addWidget(self.lbl_det_desc_tit, 0, 0)
        pago_layout.addWidget(self.lbl_det_desc, 0, 1)
        pago_layout.addWidget(self.lbl_det_rec_tit, 1, 0)
        pago_layout.addWidget(self.lbl_det_rec, 1, 1)
        
        pago_layout.addWidget(QLabel("<font size='5'><b>Pago con:</b></font>"), 2, 0)
        self.lbl_det_pago = QLabel("<font size='5'>$0,00</font>")
        self.lbl_det_pago.setAlignment(Qt.AlignRight)
        pago_layout.addWidget(self.lbl_det_pago, 2, 1)
        
        pago_layout.addWidget(QLabel("<font size='5'><b>Total:</b></font>"), 3, 0)
        self.lbl_det_total = QLabel("<font size='5'>$0,00</font>")
        self.lbl_det_total.setAlignment(Qt.AlignRight)
        pago_layout.addWidget(self.lbl_det_total, 3, 1)
        det_layout.addLayout(pago_layout)
        
        right_vbox.addWidget(self.frame_det)
        
        # Bottom Buttons Right
        btn_row = QHBoxLayout()
        self.btn_notas = QPushButton("📝 Notas")
        self.btn_notas.setObjectName("btnNotas")
        self.btn_notas.setFixedWidth(100)
        
        self.btn_cancelar = QPushButton("⛔ Cancelar Venta")
        self.btn_cancelar.setObjectName("btnCancelVenta")
        
        self.btn_reimprimir = QPushButton("🖨️ Imprimir copia")
        self.btn_reimprimir.setObjectName("btnImprimir")
        
        btn_row.addWidget(self.btn_notas)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_cancelar)
        btn_row.addWidget(self.btn_reimprimir)
        right_vbox.addLayout(btn_row)

    def set_callbacks(self, on_cancel, on_print):
        self.btn_cancelar.clicked.connect(on_cancel)
        self.btn_reimprimir.clicked.connect(on_print)

    def mostrar_venta(self, v, items):
        self.ticket_seleccionado = v['id']
        self.lbl_preview_title.setText(f"Ticket {v['id']}")
        self.lbl_det_folio.setText(str(v['id']))
        self.lbl_det_cajero.setText(str(v['usuario']).upper())
        self.lbl_det_metodo.setText(str(v['metodo_pago'] if 'metodo_pago' in v.keys() else 'Efectivo').upper())
        
        try:
            fecha_str = str(v['fecha'])
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d"):
                try: dt = datetime.strptime(fecha_str, fmt); break
                except: continue
            if dt:
                meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                fecha_fmt = f"{dt.day:02d} de {meses[dt.month-1]} {dt.year} {dt.strftime('%I:%M %p').lower()}"
            else: fecha_fmt = fecha_str
        except: fecha_fmt = "Fecha: " + str(v['fecha'])
            
        self.lbl_det_fecha.setText(fecha_fmt)
        self.lbl_det_total.setText(f"<font size='5'>{fmt_moneda(v['total'])}</font>")
        self.lbl_det_pago.setText(f"<font size='5'>{fmt_moneda(v['pago_con'])}</font>")
        
        # Cargar descuento y recargo en vivo si existen en la venta
        desc_val = float(v['descuento']) if ('descuento' in v.keys() and v['descuento'] is not None) else 0.0
        rec_val = float(v['recargo']) if ('recargo' in v.keys() and v['recargo'] is not None) else 0.0
        
        if desc_val > 0:
            self.lbl_det_desc.setText(f"-{fmt_moneda(desc_val)}")
            self.lbl_det_desc_tit.show()
            self.lbl_det_desc.show()
        else:
            self.lbl_det_desc_tit.hide()
            self.lbl_det_desc.hide()
            
        if rec_val > 0:
            self.lbl_det_rec.setText(f"+{fmt_moneda(rec_val)}")
            self.lbl_det_rec_tit.show()
            self.lbl_det_rec.show()
        else:
            self.lbl_det_rec_tit.hide()
            self.lbl_det_rec.hide()
        
        self.tabla_detalle.setRowCount(0)
        
        estado = str(v['estado']).upper()
        if "CANCELADA" in estado:
            self.sello_cancelado.show()
            self.sello_cancelado.raise_()
            self.btn_cancelar.setEnabled(False)
            self.btn_cancelar.setStyleSheet("background: #f1f5f9; color: #94a3b8; border-color: #e2e8f0;")
        else:
            self.sello_cancelado.hide()
            self.btn_cancelar.setEnabled(True)
            self.btn_cancelar.setStyleSheet("")
            self.btn_cancelar.setObjectName("btnCancelVenta")
        
        if items:
            self.tabla_detalle.setRowCount(len(items))
            for i, it in enumerate(items):
                self.tabla_detalle.setItem(i, 0, QTableWidgetItem(f"{it['cantidad']:g}"))
                self.tabla_detalle.setItem(i, 1, QTableWidgetItem(str(it['nombre_producto'])))
                it_imp = QTableWidgetItem(fmt_moneda(it['subtotal']))
                it_imp.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tabla_detalle.setItem(i, 2, it_imp)
