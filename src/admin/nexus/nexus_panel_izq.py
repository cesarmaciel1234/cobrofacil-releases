import random
import math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QPainter, QBrush, QPen

class CyberRadar(QWidget):
    """Grafo de topología de red en tiempo real (Reemplaza al viejo Radar)"""
    def __init__(self):
        super().__init__()
        self.setFixedHeight(120)
        self.nodes = []
        self.packets = []
        self.center_pulse = 0
        self.angle_offset = 0
        self.port_leds = [0 for _ in range(16)] # LEDs del router
        
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
        
        # Parpadeo aleatorio de LEDs del router
        for i in range(16):
            if random.random() < 0.15:
                self.port_leds[i] = 1 if self.port_leds[i] == 0 else 0

        self.update()

    def add_blip(self):
        # Disparar un paquete desde un nodo aleatorio (0 a 15)
        node_idx = random.randint(0, 15)
        self.packets.append({'node': node_idx, 'progress': 0.0})
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
        painter.setPen(QPen(QColor(51, 65, 85), 1))
        painter.setBrush(QColor(15, 23, 42)) # Fondo oscuro del chasis
        painter.drawRect(cx - 82, panel_y, 164, 18)
        
        for i in range(16):
            lx = cx - 77 + (i * 10)
            ly = panel_y + 5
            
            if self.port_leds[i] == 1:
                color = QColor(16, 185, 129) if random.random() > 0.1 else QColor(250, 204, 21)
                painter.setBrush(QColor(16, 185, 129, 100))
                painter.setPen(Qt.NoPen)
                painter.drawRect(lx-1, ly-1, 8, 10)
            else:
                color = QColor(30, 41, 59)
                
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawRect(lx, ly, 6, 8)
        
        # Calcular posiciones de los nodos periféricos (Derecha, en 2 columnas)
        node_pos = []
        for i in range(16):
            col = i // 8  # 0 o 1
            row = i % 8   # 0 a 7
            
            nx = w - 50 + (col * 25)
            # Distribuir los 8 nodos verticalmente
            ny = 10 + (row * ((h - 45) / 7))
            node_pos.append((nx, ny))
            
            # Dibujar cable de fibra óptica al centro
            painter.setPen(QPen(QColor(51, 65, 85, 100), 1))
            # Conectar a la cara derecha del servidor
            painter.drawLine(sx + 15, int(sy), int(nx), int(ny))
            
            # Dibujar la PC nodo (Punto cyan)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(56, 189, 248))
            painter.drawRect(int(nx) - 3, int(ny) - 3, 6, 6)
            
        # Dibujar paquetes de datos en tránsito (Puntos neon magenta)
        for p in self.packets:
            idx = p['node']
            prog = p['progress']
            nx, ny = node_pos[idx]
            
            # Viaja desde el nodo hacia el servidor
            px = nx + (sx + 15 - nx) * prog
            py = ny + (sy - ny) * prog
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(244, 63, 94))
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
                background-color: rgba(30, 41, 59, 0.80);
                border-radius: 5px;
                padding: 8px 10px;
                margin: 2px;
                font-family: Consolas, monospace;
                font-size: 11px;
                font-weight: 700;
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

    def append_terminal(self, texto, color="#7DD3FC"):
        item = QListWidgetItem(texto)
        item.setForeground(QColor(color))
        self.terminal.addItem(item)
        self.terminal.scrollToBottom()
