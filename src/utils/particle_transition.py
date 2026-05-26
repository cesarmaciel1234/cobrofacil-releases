import random
import math
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient

class Particle:
    def __init__(self, target_x, target_y, cx, cy, color, size):
        self.target_x = target_x
        self.target_y = target_y
        self.cx = cx
        self.cy = cy
        self.color = color
        self.size = size
        
        # Parámetros espirales para fase de entrada
        self.angle_offset = random.uniform(0, 2 * math.pi)
        self.spiral_speed = random.choice([-1.2, 1.2])
        self.max_radius = math.hypot(target_x - cx, target_y - cy)
        
        # Posición actual
        self.x = cx
        self.y = cy
        self.prev_x = cx
        self.prev_y = cy

    def update(self, progress):
        self.prev_x = self.x
        self.prev_y = self.y
        
        if progress < 0.5:
            # Fase 1: Entrada desde vórtice espiral (0% -> 50%)
            t = progress * 2.0  # 0.0 -> 1.0
            ease = 1.0 - math.pow(1.0 - t, 3) # Cubic ease out
            
            # Espiral expandiéndose del centro al destino
            current_angle = self.angle_offset + t * 3.5 * math.pi * self.spiral_speed
            current_radius = self.max_radius * ease
            
            spiral_x = self.cx + current_radius * math.cos(current_angle)
            spiral_y = self.cy + current_radius * math.sin(current_angle)
            
            # Mezclamos para aterrizar exactamente en el target
            self.x = spiral_x * (1.0 - ease) + self.target_x * ease
            self.y = spiral_y * (1.0 - ease) + self.target_y * ease
        else:
            # Fase 2: Disolución / Dispersión (50% -> 100%)
            t = (progress - 0.5) * 2.0  # 0.0 -> 1.0
            ease = math.pow(t, 2) # Aceleración cuadrática
            
            # Se dispersan hacia afuera desde el centro de la pantalla
            angle = math.atan2(self.target_y - self.cy, self.target_x - self.cx) + self.angle_offset * 0.2
            dist = 300.0 * ease
            
            self.x = self.target_x + dist * math.cos(angle)
            self.y = self.target_y + dist * math.sin(angle)

class ParticleReconstructionOverlay(QWidget):
    """
    Efecto 'Vórtice Cósmico y Constelación Holográfica' (Light Mode Premium).
    - Swarm de 1500 Partículas con Estela de Luz en un fondo Glass claro.
    - Dibujo con Estela (Motion Blur) y enlaces de red neural entre nodos.
    - Elementos HUD Scifi: Scanline láser de barrido, telemetría y anillo de datos.
    - Mensaje Central: "INICIALIZANDO TERMINAL..." elegante en Slate.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(0, 0, parent.width(), parent.height())
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.w = parent.width()
        self.h = parent.height()
        
        self.bg_alpha = 240
        
        self.particles = []
        self.setup_particles()
        
        # Timer de animación (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)
        
        self.ticks_elapsed = 0
        self.max_ticks = 85 # ~1.4 segundos para una transición ágil
        
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.fade_alpha = 1.0

    def setup_particles(self):
        # Estructura del terminal
        struct_zones = [
            {"x1": 30, "x2": self.w - 30, "y1": 15, "y2": 70, "color": QColor(99, 102, 241)},     # Indigo
            {"x1": 30, "x2": int(self.w * 0.7), "y1": 95, "y2": self.h - 110, "color": QColor(16, 185, 129)}, # Esmeralda
            {"x1": int(self.w * 0.72), "x2": self.w - 30, "y1": 95, "y2": self.h - 110, "color": QColor(14, 165, 233)}, # Sky
            {"x1": 30, "x2": self.w - 30, "y1": self.h - 85, "color": QColor(139, 92, 246)}      # Púrpura
        ]
        
        cx = self.w / 2
        cy = self.h / 2
        
        for _ in range(1500):
            zone = random.choice(struct_zones)
            target_x = random.uniform(zone["x1"], zone.get("x2", zone["x1"] + 100))
            target_y = random.uniform(zone["y1"], zone.get("y2", zone["y1"] + 50))
            
            size = random.uniform(1.8, 3.2)
            color = zone["color"]
            
            self.particles.append(Particle(target_x, target_y, cx, cy, color, size))

    def tick(self):
        self.ticks_elapsed += 1
        progress = min(1.0, self.ticks_elapsed / float(self.max_ticks))
        
        # 1. Actualizar partículas
        for p in self.particles:
            p.update(progress)
            
        # 2. Reducir opacidad del fondo de cristal
        if progress > 0.45:
            self.bg_alpha = max(0, self.bg_alpha - 20)
            
        # 3. Desvanecimiento final suave
        if self.ticks_elapsed >= self.max_ticks:
            self.fade_alpha -= 0.15
            if self.fade_alpha <= 0:
                self.timer.stop()
                self.close()
                return
            self.opacity_effect.setOpacity(self.fade_alpha)
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # A. Fondo cristalino claro
        painter.setPen(Qt.NoPen)
        bg_col = QColor(244, 246, 251, self.bg_alpha)
        painter.setBrush(QBrush(bg_col))
        painter.drawRect(self.rect())
        
        progress = min(1.0, self.ticks_elapsed / float(self.max_ticks))
        cam_alpha = min(self.bg_alpha, 210)
        cx = self.w / 2
        cy = self.h / 2

        # B. Barrido Láser Holográfico
        if self.bg_alpha > 10:
            laser_y = (self.h * progress * 2.0) % self.h
            laser_grad = QLinearGradient(0, laser_y - 3, 0, laser_y + 3)
            laser_grad.setColorAt(0.0, QColor(99, 102, 241, 0))
            laser_grad.setColorAt(0.5, QColor(99, 102, 241, int(cam_alpha * 0.4)))
            laser_grad.setColorAt(1.0, QColor(99, 102, 241, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(laser_grad))
            painter.drawRect(0, int(laser_y - 6), self.w, 12)

        # C. Anillo HUD y brackets centrales
        if self.bg_alpha > 20:
            hud_angle = progress * 720.0
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(hud_angle)
            
            # Anillo punteado
            pen_hud = QPen(QColor(99, 102, 241, int(cam_alpha * 0.2)), 1.5, Qt.DashLine)
            painter.setPen(pen_hud)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), 140, 140)
            
            # Brackets de mira scifi
            pen_bracket = QPen(QColor(99, 102, 241, int(cam_alpha * 0.4)), 2)
            painter.setPen(pen_bracket)
            painter.drawArc(QRectF(-155, -155, 310, 310), 0 * 16, 30 * 16)
            painter.drawArc(QRectF(-155, -155, 310, 310), 120 * 16, 30 * 16)
            painter.drawArc(QRectF(-155, -155, 310, 310), 240 * 16, 30 * 16)
            
            painter.restore()

        # D. Constelación de Red de Nodos (Conexiones dinámicas)
        p_alpha = int(min(self.bg_alpha, 255) * (1.0 - abs(progress - 0.5) * 1.5))
        p_alpha = max(10, min(255, p_alpha))
        
        if self.bg_alpha > 15 and progress < 0.8:
            painter.setBrush(Qt.NoBrush)
            for i in range(min(len(self.particles), 150)):
                p1 = self.particles[i]
                for j in range(i + 1, min(len(self.particles), 280)):
                    p2 = self.particles[j]
                    dx = p1.x - p2.x
                    dy = p1.y - p2.y
                    dist = math.hypot(dx, dy)
                    if dist < 45:
                        alpha = int((1.0 - (dist / 45.0)) * 35 * (cam_alpha / 210.0))
                        painter.setPen(QPen(QColor(p1.color.red(), p1.color.green(), p1.color.blue(), alpha), 0.8))
                        painter.drawLine(QPointF(p1.x, p1.y), QPointF(p2.x, p2.y))

        # E. Dibujar Partículas con Estelas
        for p in self.particles:
            dist_mov = math.hypot(p.x - p.prev_x, p.y - p.prev_y)
            if dist_mov > 0.8:
                pen_trail = QPen(QColor(p.color.red(), p.color.green(), p.color.blue(), p_alpha), p.size)
                pen_trail.setCapStyle(Qt.RoundCap)
                painter.setPen(pen_trail)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(QPointF(p.prev_x, p.prev_y), QPointF(p.x, p.y))
            else:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(QColor(p.color.red(), p.color.green(), p.color.blue(), p_alpha)))
                painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)

        # F. Textos HUD de Telemetría
        if self.bg_alpha > 30:
            font_mono = QFont("Consolas", 8)
            font_mono.setBold(True)
            painter.setFont(font_mono)
            painter.setPen(QColor(71, 85, 105, int(cam_alpha * 0.6)))
            
            # Telemetría izquierda
            painter.drawText(36, 45, "STATUS: SYSTEM_ASSEMBLY_OK")
            painter.drawText(36, 60, f"LATENCY: {random.randint(6, 12)}ms")
            painter.drawText(36, 75, f"TELEMETRY_NODES: {len(self.particles)}")
            
            # Telemetría derecha
            painter.drawText(self.w - 200, 45, f"ENVIRONMENT: TPV_PRO_v2026")
            painter.drawText(self.w - 200, 60, "SECURITY: DECRYPT_LOCAL_PASS")
            painter.drawText(self.w - 200, 75, f"RECONSTRUCTION: {int(progress * 100)}%")

        # G. Mensaje central scifi
        if self.bg_alpha > 35:
            # Título principal
            font_title = QFont("Segoe UI", 16)
            font_title.setBold(True)
            font_title.setLetterSpacing(QFont.AbsoluteSpacing, 8)
            painter.setFont(font_title)
            painter.setPen(QColor(15, 23, 42, cam_alpha)) # Slate-900
            
            rect_title = QRectF(0, cy - 30, self.w, 40)
            painter.drawText(rect_title, Qt.AlignCenter, "INICIALIZANDO TERMINAL")
            
            # Subtítulo dinámico con cursor parpadeante
            cursor = "_" if (self.ticks_elapsed // 8) % 2 == 0 else ""
            font_sub = QFont("Consolas", 9)
            font_sub.setBold(True)
            font_sub.setLetterSpacing(QFont.AbsoluteSpacing, 2)
            painter.setFont(font_sub)
            painter.setPen(QColor(99, 102, 241, int(cam_alpha * 0.90))) # Indigo
            
            rect_sub = QRectF(0, cy + 15, self.w, 25)
            painter.drawText(rect_sub, Qt.AlignCenter, f"[ CARGANDO INTERFAZ EN RED LOCAL ]{cursor}")

    def resizeEvent(self, event):
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.w = self.width()
        self.h = self.height()
        self.particles = []
        self.setup_particles()
        super().resizeEvent(event)
