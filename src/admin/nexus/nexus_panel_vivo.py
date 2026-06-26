from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from src.base_de_datos.database import db_manager
import time

class LiveTicketsWorker(QThread):
    # Emitirá el ID, caja, fecha, observaciones (el string de ticket formateado)
    new_ticket_signal = pyqtSignal(int, str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.last_id = -1

    def run(self):
        while self.running:
            try:
                # Buscamos registros de tickets/ventas (excluimos corazón y alertas puras aquí)
                query = "SELECT id, caja_id, fecha, observaciones FROM movimientos_caja WHERE observaciones LIKE '[TICKET]%' OR tipo LIKE '[TICKET]%' OR tipo='VENTA' ORDER BY id ASC"
                rows = db_manager.execute_query(query)
                
                if rows:
                    for row in rows:
                        row_id = row['id']
                        if row_id > self.last_id:
                            c_id = row['caja_id']
                            caja_str = f"PC-0{c_id}" if c_id and int(c_id) < 10 else f"PC-{c_id}"
                            obs = str(row['observaciones'])
                            
                            # Limpiar tag para mostrar amigable
                            obs_clean = obs.replace("[TICKET]", "").replace("[VENTA]", "").strip()
                            fecha_corta = str(row['fecha'])[11:16] if row['fecha'] and len(str(row['fecha'])) >= 16 else "00:00"

                            self.new_ticket_signal.emit(row_id, caja_str, fecha_corta, obs_clean)
                            self.last_id = row_id
            except Exception as e:
                pass
            time.sleep(2)

    def stop(self):
        self.running = False

class BurbujaTicket(QFrame):
    def __init__(self, caja, hora, detalle, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                border-left: 4px solid #10B981;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        
        lbl_head = QLabel(f"🕒 {hora}  |  💻 {caja}")
        lbl_head.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        
        lbl_det = QLabel(f"👉 {detalle}")
        lbl_det.setWordWrap(True)
        lbl_det.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold; margin-top: 4px; border: none; background: transparent;")
        
        lay.addWidget(lbl_head)
        lay.addWidget(lbl_det)


class NexusPanelVivo(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #0F172A; border-radius: 8px;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_titulo = QLabel("📡 FLUJO DE VENTAS EN VIVO")
        lbl_titulo.setStyleSheet("color: #10B981; font-weight: 900; font-size: 14px; letter-spacing: 2px;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_titulo)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: #0F172A; width: 8px; }
            QScrollBar::handle:vertical { background: #334155; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.content_layout.setContentsMargins(0,0,10,0)
        self.content_layout.addStretch()
        
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)
        
        self.worker = LiveTicketsWorker()
        self.worker.new_ticket_signal.connect(self._add_ticket)
        self.worker.start()
        
        # Auto-scroll flag
        self.scroll.verticalScrollBar().rangeChanged.connect(self._scroll_down)

    def _add_ticket(self, r_id, caja, hora, obs):
        burbuja = BurbujaTicket(caja, hora, obs)
        # Insertar justo antes del stretch
        count = self.content_layout.count()
        self.content_layout.insertWidget(count - 1, burbuja)
        
        # Mantener solo los ultimos 50 tickets para no saturar memoria
        if count > 50:
            item = self.content_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()

    def _scroll_down(self, min_val, max_val):
        self.scroll.verticalScrollBar().setValue(max_val)

    def closeEvent(self, event):
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)
