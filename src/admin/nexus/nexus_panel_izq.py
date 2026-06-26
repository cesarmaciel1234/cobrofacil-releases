import random
import math
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from src.base_de_datos.database import db_manager

class CyberRadar(QWidget):
    """Grafo de topología de red en tiempo real (Reemplaza al viejo Radar)"""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(120)
        self.nodes = []
        self.packets = []
        self.center_pulse = 0
        self.angle_offset = 0
        self.port_leds = [0 for _ in range(20)] # LEDs del router (0=off, 1=green, 2=orange, 3=red)
        self.node_activity = [0 for _ in range(20)] # Última actividad de cada nodo
        self.node_mapping = {} # Mapea 'origen' -> índice 0-19
        self.next_node_idx = 0
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(30) # 33 fps para fluidez extrema

    def _animate(self):
        self.angle_offset = (self.angle_offset + 0.5) % 360
        if self.center_pulse > 0:
            self.center_pulse -= 4
        
        # Mover paquetes
        for p in self.packets:
            p['progress'] += 0.05 # Velocidad del paquete
            
        self.packets = [p for p in self.packets if p['progress'] < 1.0]
        
        # Lógica de LEDs de conexión (Sincronizado con PCs activas)
        now = time.time()
        for i in range(20):
            if i < self.next_node_idx:
                segundos = now - self.node_activity[i]
                if segundos < 32:
                    self.port_leds[i] = 1 # Activa (Verde)
                elif segundos < 45:
                    self.port_leds[i] = 2 # Esperando (Amarillo)
                else:
                    self.port_leds[i] = 3 # Caída (Rojo)
            else:
                self.port_leds[i] = 0 # Puerto Libre/Apagado

        self.update()

    def add_blip(self, origen="desconocido", is_heartbeat=False):
        if origen not in self.node_mapping:
            if self.next_node_idx < 20:
                self.node_mapping[origen] = self.next_node_idx
                self.next_node_idx += 1
            else:
                return # Máximo 20 nodos visuales en el radar
                
        idx = self.node_mapping[origen]
        self.packets.append({'node': idx, 'progress': 0.0, 'is_heartbeat': is_heartbeat})
        self.node_activity[idx] = time.time()
        
        if not is_heartbeat:
            self.center_pulse = min(255, self.center_pulse + 80)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        
        # Desplazar el centro un poco hacia arriba para dejar espacio a los LEDs
        cx = w // 2
        cy = (h - 25) // 2 
        
        # Posición del Servidor (Izquierda)
        sx = 40
        sy = cy
        
        # Dibujar Panel de Switch/Router en la base (para llenar el vacío)
        panel_y = h - 22
        
        # Ancho del switch para 20 LEDs (8px ancho + 2px gap = 10px por LED) -> 200px
        switch_width = 20 * 10 + 4
        painter.setPen(QPen(QColor(51, 65, 85), 1))
        painter.setBrush(QColor(15, 23, 42)) # Fondo oscuro del chasis
        painter.drawRect(cx - (switch_width // 2), panel_y, switch_width, 14)
        
        for i in range(20):
            lx = cx - (switch_width // 2) + 2 + (i * 10)
            ly = panel_y + 3
            
            if self.port_leds[i] == 1:
                color = QColor(16, 185, 129) # Verde brillante (Activa)
                painter.setBrush(QColor(16, 185, 129, 100))
                painter.setPen(Qt.NoPen)
                painter.drawRect(lx-1, ly-1, 8, 10)
            elif self.port_leds[i] == 2:
                color = QColor(245, 158, 11) # Amarillo/Naranja (Esperando)
                painter.setBrush(QColor(245, 158, 11, 80))
                painter.setPen(Qt.NoPen)
                painter.drawRect(lx-1, ly-1, 8, 10)
            elif self.port_leds[i] == 3:
                color = QColor(239, 68, 68) # Rojo (Caída)
                painter.setBrush(QColor(239, 68, 68, 80))
                painter.setPen(Qt.NoPen)
                painter.drawRect(lx-1, ly-1, 8, 10)
            else:
                color = QColor(30, 41, 59) # Gris oscuro (Apagado)
                
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRect(lx, ly, 6, 8)
        
        # Calcular posiciones de los nodos periféricos (Derecha, en 2 columnas de 10)
        node_pos = []
        for i in range(20):
            col = i // 10  # 0 a 1
            row = i % 10   # 0 a 9
            
            nx = w - 50 + (col * 25)
            # Distribuir los 10 nodos verticalmente
            ny = 10 + (row * ((h - 45) / 9)) if h > 45 else 10 + (row * 8)
            node_pos.append((nx, ny))
            
            # Dibujar cable de fibra óptica al centro
            painter.setPen(QPen(QColor(51, 65, 85, 100), 1))
            painter.drawLine(sx + 15, int(sy), int(nx), int(ny))
            
            # Dibujar la PC nodo (Punto cyan)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(56, 189, 248))
            painter.drawRect(int(nx) - 3, int(ny) - 3, 6, 6)
            
        # Dibujar paquetes de datos en tránsito
        for p in self.packets:
            idx = p['node']
            prog = p['progress']
            is_hb = p.get('is_heartbeat', False)
            nx, ny = node_pos[idx]
            
            # Viaja desde el nodo hacia el servidor
            px = nx + (sx + 15 - nx) * prog
            py = ny + (sy - ny) * prog
            
            painter.setPen(Qt.NoPen)
            if is_hb:
                painter.setBrush(QColor(14, 165, 233, 150)) # Cyan tenue para latidos
                painter.drawEllipse(int(px) - 2, int(py) - 2, 4, 4)
            else:
                painter.setBrush(QColor(244, 63, 94)) # Magenta brillante para ventas/eventos
                painter.drawEllipse(int(px) - 3, int(py) - 3, 6, 6)

        # Dibujar servidor central (Rack a la izquierda)
        painter.setPen(QPen(QColor(51, 65, 85), 2))
        painter.setBrush(QColor(15, 23, 42))
        painter.drawRect(sx - 15, int(sy - 30), 30, 60) # Rack
        
        # Pulso de recepción de datos (Luces del rack)
        glow = min(255, max(40, self.center_pulse))
        for i in range(4): # 4 bahías/discos
            slot_y = int(sy - 22 + (i * 13))
            painter.setBrush(QColor(16, 185, 129, glow))
            painter.setPen(Qt.NoPen)
            painter.drawRect(sx - 10, slot_y, 20, 6)


class LiveTicketsWorker(QThread):
    new_ticket_signal = pyqtSignal(int, str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.last_id = -1

    def run(self):
        while self.running:
            try:
                # Inicializar al id máximo para no cargar histórico enorme
                if self.last_id == -1:
                    max_row = db_manager.execute_query("SELECT MAX(id) as max_id FROM movimientos_caja")
                    if max_row and max_row[0]['max_id'] is not None:
                        self.last_id = max(0, max_row[0]['max_id'] - 8)
                    else:
                        self.last_id = 0

                query = "SELECT id, caja_id, fecha, observaciones FROM movimientos_caja WHERE (observaciones LIKE '[TICKET]%%' OR tipo LIKE '[TICKET]%%' OR tipo='VENTA') AND id > ? ORDER BY id ASC"
                rows = db_manager.execute_query(query, (self.last_id,))
                
                if rows:
                    for row in rows:
                        row_id = row['id']
                        c_id = row['caja_id']
                        caja_str = f"PC-0{c_id}" if c_id and int(c_id) < 10 else f"PC-{c_id}"
                        obs = str(row['observaciones'])
                        
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


class TextLogWidget(QFrame):
    def __init__(self, texto, color, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(30, 41, 59, 0.70); border-radius: 5px; border: none;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        
        lbl = QLabel(texto)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f"color: {color}; font-family: Consolas, monospace; font-size: 11px; font-weight: bold; background: transparent; border: none;")
        lay.addWidget(lbl)


class NexusPanelIzq(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: transparent;")
        lay_diag = QVBoxLayout(self)
        lay_diag.setContentsMargins(12, 12, 12, 12)
        lay_diag.setSpacing(10)

        lbl_term = QLabel("▶  TERMINAL SYS.OP")
        lbl_term.setStyleSheet("""
            font-size: 12px; font-weight: 900; letter-spacing: 2px;
            color: #D97706;
            background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        lay_diag.addWidget(lbl_term)

        self.terminal = QListWidget()
        self.terminal.setStyleSheet("""
            QListWidget {
                background-color: #0A0F1E;
                border: 1.5px solid #1E3A5F;
                border-left: 3px solid #6366F1;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                background: transparent;
                border: none;
                padding: 0px;
                margin: 3px;
            }
            QListWidget::item:selected {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #0A0F1E;
                width: 5px;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        lay_diag.addWidget(self.terminal)

        lbl_radar = QLabel("▶  TOPOLOGÍA DE RED  //  LIVE")
        lbl_radar.setStyleSheet("""
            font-size: 12px; font-weight: 900; letter-spacing: 2px;
            color: #0284C7;
            background: transparent; border: none;
            font-family: 'Segoe UI', sans-serif;
        """)
        lay_diag.addWidget(lbl_radar)

        self.spectrum = CyberRadar()
        lay_diag.addWidget(self.spectrum)

        # Iniciar worker para tickets en vivo
        self.worker = LiveTicketsWorker(self)
        self.worker.new_ticket_signal.connect(self.add_ticket_bubble)
        self.worker.start()

    def append_terminal(self, texto, color="#7DD3FC"):
        log_widget = TextLogWidget(texto, color)
        item = QListWidgetItem()
        log_widget.adjustSize()
        item.setSizeHint(log_widget.sizeHint())
        self.terminal.addItem(item)
        self.terminal.setItemWidget(item, log_widget)
        self.terminal.scrollToBottom()
        
        if self.terminal.count() > 50:
            old_item = self.terminal.takeItem(0)
            if old_item:
                del old_item

    def add_ticket_bubble(self, r_id, caja, hora, obs):
        burbuja = BurbujaTicket(caja, hora, obs)
        item = QListWidgetItem()
        burbuja.adjustSize()
        item.setSizeHint(burbuja.sizeHint())
        self.terminal.addItem(item)
        self.terminal.setItemWidget(item, burbuja)
        self.terminal.scrollToBottom()
        
        if self.terminal.count() > 50:
            old_item = self.terminal.takeItem(0)
            if old_item:
                del old_item

    def closeEvent(self, event):
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        super().closeEvent(event)

    def aplicar_tema(self, is_dark):
        # Mantenemos firma por compatibilidad, no hace falta hacer nada ya que los colores son oscuros estilizados
        pass
