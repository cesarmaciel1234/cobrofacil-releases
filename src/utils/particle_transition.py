import random
import math
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont

class Particle:
    def __init__(self, target_x, target_y, start_x, start_y, end_x, end_y, color, size):
        self.target_x = target_x
        self.target_y = target_y
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        self.color = color
        self.size = size
        
        # Posición actual e historial para efecto estela de luz (Motion Blur)
        self.x = start_x
        self.y = start_y
        self.prev_x = start_x
        self.prev_y = start_y

    def update(self, progress):
        # Guardar posición anterior antes de mover para la estela de luz
        self.prev_x = self.x
        self.prev_y = self.y
        
        # Fase 1: Entrada desde los bordes hacia el centro (0% a 50%)
        # Fase 2: Retroceso hacia los bordes (50% a 100%)
        if progress < 0.5:
            p_phase = progress * 2.0
            ease = 1.0 - math.pow(1.0 - p_phase, 3)
            self.x = self.start_x + (self.target_x - self.start_x) * ease
            self.y = self.start_y + (self.target_y - self.start_y) * ease
        else:
            p_phase = (progress - 0.5) * 2.0
            ease = math.pow(p_phase, 3)
            self.x = self.target_x + (self.end_x - self.target_x) * ease
            self.y = self.target_y + (self.end_y - self.target_y) * ease

class ParticleReconstructionOverlay(QWidget):
    """
    Efecto 'Estelas de Luz Simétricas' (De Esquinas a Centro y Viceversa).
    - Swarm de 1200 Partículas con Estela de Luz (Motion Blur): Los puntos viajan simétricamente
      desde las 4 esquinas de la pantalla hacia sus objetivos en la interfaz y luego regresan.
    - Dibujo con Estela: En lugar de puntos estáticos, se dibuja un trazo dinámico
      proporcional a la velocidad del movimiento.
    - Mensaje Central: Texto "BIENVENIDOS...." limpio en cristal oscuro.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.w = parent.width()
        self.h = parent.height()
        
        self.bg_alpha = 245
        
        # Generar nube de partículas de datos (1200 puntos)
        self.particles = []
        self.setup_particles()
        
        # Timer de animación (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        
        self.ticks_elapsed = 0
        self.max_ticks = 90 # ~1.5 segundos
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_alpha = 1.0

    def setup_particles(self):
        # Estructura del terminal
        struct_zones = [
            {"x1": 30, "x2": self.w - 30, "y1": 15, "y2": 70, "color": QColor(6, 182, 212)}, # Cyan
            {"x1": 30, "x2": int(self.w * 0.7), "y1": 95, "y2": self.h - 110, "color": QColor(16, 185, 129)}, # Esmeralda
            {"x1": int(self.w * 0.72), "x2": self.w - 30, "y1": 95, "y2": self.h - 110, "color": QColor(6, 182, 212)}, # Cyan
            {"x1": 30, "x2": self.w - 30, "y1": self.h - 85, "color": QColor(16, 185, 129)} # Esmeralda
        ]
        
        # Esquinas físicas de la pantalla
        corners = [
            (0, 0),             # Top-Left
            (self.w, 0),         # Top-Right
            (0, self.h),         # Bottom-Left
            (self.w, self.h)      # Bottom-Right
        ]
        
        for _ in range(1200):
            zone = random.choice(struct_zones)
            
            target_x = random.uniform(zone["x1"], zone.get("x2", zone["x1"] + 100))
            target_y = random.uniform(zone["y1"], zone.get("y2", zone["y1"] + 50))
            
            # Asignar una esquina de origen simétrica
            corner_x, corner_y = random.choice(corners)
            
            # Pequeño desplazamiento aleatorio para evitar que salgan exactamente de un solo píxel
            offset_x = random.uniform(-40, 40)
            offset_y = random.uniform(-40, 40)
            
            start_x = corner_x + offset_x
            start_y = corner_y + offset_y
            
            end_x = corner_x + offset_x
            end_y = corner_y + offset_y
            
            size = random.uniform(1.8, 3.2)
            color = zone["color"]
            
            self.particles.append(Particle(target_x, target_y, start_x, start_y, end_x, end_y, color, size))

    def tick(self):
        self.ticks_elapsed += 1
        progress = min(1.0, self.ticks_elapsed / float(self.max_ticks))
        
        # 1. Actualizar partículas
        for p in self.particles:
            p.update(progress)
            
        # 2. Reducir opacidad del fondo
        if progress > 0.4:
            self.bg_alpha = max(0, self.bg_alpha - 15)
            
        # 3. Desvanecimiento al final
        if self.ticks_elapsed >= self.max_ticks:
            self.fade_alpha -= 0.12
            if self.fade_alpha <= 0:
                self.timer.stop()
                self.close()
                return
            self.opacity_effect.setOpacity(self.fade_alpha)
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # A. Fondo cristal oscuro
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(10, 12, 20, self.bg_alpha)))
        painter.drawRect(self.rect())
        
        progress = min(1.0, self.ticks_elapsed / float(self.max_ticks))
        cam_alpha = min(self.bg_alpha, 200)
        cx = self.w / 2
        cy = self.h / 2

        # B. DIBUJAR NUBE DE PARTÍCULAS (Con Estelas de Luz / Motion Blur)
        p_alpha = int(min(self.bg_alpha, 255) * (1.0 - abs(progress - 0.5) * 1.5))
        p_alpha = max(15, min(255, p_alpha))
        
        for p in self.particles:
            # Si hay movimiento, dibujar estela de luz (línea de velocidad)
            dist_mov = math.hypot(p.x - p.prev_x, p.y - p.prev_y)
            if dist_mov > 0.8:
                # Estilo estela con borde redondeado
                pen_trail = QPen(QColor(p.color.red(), p.color.green(), p.color.blue(), p_alpha), p.size)
                pen_trail.setCapStyle(Qt.RoundCap)
                painter.setPen(pen_trail)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(QPointF(p.prev_x, p.prev_y), QPointF(p.x, p.y))
            else:
                # Dibujar punto estático simple si está cerca del destino
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(p.color.red(), p.color.green(), p.color.blue(), p_alpha)))
                painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)

        # C. TEXTO DE BIENVENIDA MINIMALISTA
        if self.bg_alpha > 30:
            # Texto principal "BIENVENIDOS...."
            font_title = QFont("Segoe UI", 16)
            font_title.setBold(True)
            font_title.setLetterSpacing(QFont.AbsoluteSpacing, 6)
            painter.setFont(font_title)
            painter.setPen(QColor(255, 255, 255, cam_alpha))
            
            rect_title = QRectF(0, cy - 30, self.w, 40)
            painter.drawText(rect_title, Qt.AlignCenter, "BIENVENIDOS....")
            
            # Subtexto sutil
            font_sub = QFont("Consolas", 9)
            font_sub.setBold(True)
            font_sub.setLetterSpacing(QFont.AbsoluteSpacing, 2)
            painter.setFont(font_sub)
            painter.setPen(QColor(16, 185, 129, int(cam_alpha * 0.85)))
            
            rect_sub = QRectF(0, cy + 15, self.w, 25)
            painter.drawText(rect_sub, Qt.AlignCenter, "SERVERONLINE")

    def resizeEvent(self, event):
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.w = self.width()
        self.h = self.height()
        self.particles = []
        self.setup_particles()
        super().resizeEvent(event)
