import sys
import random
import math
import numpy as np

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QLabel,
    QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QPointF, QRect, QRectF, QEvent
from PyQt6.QtGui import (
    QPainter,
    QColor,
    QFont,
    QPen,
    QLinearGradient,
    QBrush,
    QPainterPath
)

# =========================
# CONFIGURACIÓN EXTREMA (OPTIMIZADA PARA RENDIMIENTO FLUIDO)
# =========================
PARTICLE_COUNT = 5000 # Reducido de 44000 a 5000 para garantizar 60 FPS estables (fluidez de videojuego)
ANIMATION_TIME = 120 # Más rápido, snappier

# =========================
# SISTEMA DE PARTÍCULAS
# =========================
class ParticleSystem:
    def __init__(self, count, cx, cy, w, h):
        self.count = count
        self.cx = cx
        self.cy = cy
        self.w = w
        self.h = h
        self.max_radius = math.hypot(w / 2, h / 2) + 100
        
        self.particles = np.zeros((count, 12))
        
        self.particles[:, 0] = cx + np.random.normal(0, 5, count)
        self.particles[:, 1] = cy + np.random.normal(0, 5, count)
        self.particles[:, 6] = self.particles[:, 0]
        self.particles[:, 7] = self.particles[:, 1]
        
        self.particles[:, 2] = self.max_radius * np.random.uniform(0.7, 1.7, count)
        self.particles[:, 3] = np.random.uniform(0, 2 * np.pi, count)
        self.particles[:, 4] = np.random.uniform(0.7, 1.5, count)
        self.particles[:, 5] = np.random.uniform(0.1, 0.9, count)
        self.particles[:, 10] = np.random.uniform(-0.8, 0.8, count)
        self.particles[:, 9] = np.random.uniform(30, 140, count) # Alpha estático puro

        self.current_border_radius = -1

    def update(self, progress):
        exp_progress = np.clip(progress / 0.60, 0.0, 1.0)
        p = np.minimum(exp_progress * self.particles[:, 4], 1.0)
        
        ease_p = (1.0 - self.particles[:, 5]) * np.power(p, 3) + \
                 self.particles[:, 5] * (1.0 - np.power(1.0 - p, 3))
        
        fluid_angles = self.particles[:, 3] + (self.particles[:, 10] * ease_p)
        current_natural_radius = self.particles[:, 2] * ease_p
        
        natural_x = self.cx + np.cos(fluid_angles) * current_natural_radius
        natural_y = self.cy + np.sin(fluid_angles) * current_natural_radius
        
        collapse_progress = np.clip((progress - 0.60) / 0.30, 0.0, 1.0)
        
        if collapse_progress > 0:
            border_radius = self.max_radius * (1.0 - np.power(collapse_progress, 2))
            self.current_border_radius = border_radius
        else:
            border_radius = float('inf')
            self.current_border_radius = -1
        
        dx = natural_x - self.cx
        dy = natural_y - self.cy
        distances = np.sqrt(dx*dx + dy*dy)
        
        mask_drag = distances > border_radius
        ruido_aplastamiento = np.abs(np.random.normal(0, 12, size=np.sum(mask_drag)))
        distances[mask_drag] = border_radius - ruido_aplastamiento
        
        angles = np.arctan2(dy, dx)
        self.particles[:, 6] = self.cx + np.cos(angles) * distances
        self.particles[:, 7] = self.cy + np.sin(angles) * distances
        self.particles[:, 8] = distances
        
        current_alpha = self.particles[:, 9].copy()
        
        if border_radius != float('inf'):
            shockwave_mask = (distances > border_radius - 25)
            current_alpha[shockwave_mask] = 255 
        
        fade_out_master = 1.0 - np.power(collapse_progress, 3)
        self.particles[:, 11] = current_alpha * fade_out_master

    def get_drawing_data(self):
        margin = 50
        mask = (self.particles[:, 6] >= -margin) & \
               (self.particles[:, 6] <= self.w + margin) & \
               (self.particles[:, 7] >= -margin) & \
               (self.particles[:, 7] <= self.h + margin)
        return self.particles[mask, 6:8], self.particles[mask, 11].astype(int)

# =========================
# OVERLAY TRANSICIÓN (EL TELÓN)
# =========================
class WelcomeOverlay(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setGeometry(parent.rect())
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        parent.installEventFilter(self)

        self.tick_count = 0
        self.max_ticks = ANIMATION_TIME
        self.progress = 0.0

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)

        self.w = self.width()
        self.h = self.height()
        self.cx = self.w / 2.0
        self.cy = self.h / 2.0
        
        self.particle_system = ParticleSystem(PARTICLE_COUNT, self.cx, self.cy, self.w, self.h)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        # La animación iniciará cuando se llame a showEvent()

    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == QEvent.Resize:
            self.setGeometry(self.parent().rect())
            self.w = self.width()
            self.h = self.height()
            self.cx = self.w / 2.0
            self.cy = self.h / 2.0
            
            if hasattr(self, 'particle_system'):
                self.particle_system.w = self.w
                self.particle_system.h = self.h
                self.particle_system.cx = self.cx
                self.particle_system.cy = self.cy
        return super().eventFilter(obj, event)

    def showEvent(self, event):
        super().showEvent(event)
        # Iniciar la animación sincronizada solo cuando la pantalla ya es visible
        if not self.timer.isActive():
            self.timer.start(16)

    def tick(self):
        self.tick_count += 1
        self.progress = min(1.0, self.tick_count / self.max_ticks)
        self.particle_system.update(self.progress)

        if self.progress > 0.85:
            fade = 1.0 - ((self.progress - 0.85) / 0.15)
            self.opacity_effect.setOpacity(max(0.0, fade))

        if self.progress >= 1.0:
            self.timer.stop()
            self.close()
            return

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        current_radius = self.particle_system.current_border_radius
        bg_color = QColor(5, 5, 5)
        
        # ==================================================
        # 1. MÁSCARAS DE RECORTE (El efecto Escáner)
        # ==================================================
        clip_chaos = QPainterPath()
        clip_purified = QPainterPath()
        
        if current_radius == -1: 
            clip_chaos.addRect(QRectF(self.rect()))
        elif current_radius > 0: 
            clip_chaos.addEllipse(QPointF(self.cx, self.cy), current_radius, current_radius)
            full_rect = QPainterPath()
            full_rect.addRect(QRectF(self.rect()))
            clip_purified = full_rect.subtracted(clip_chaos)
        else:
            clip_purified.addRect(QRectF(self.rect()))

        # ==================================================
        # 2. EL VACÍO NEGRO LISO (Solo dentro del aro)
        # ==================================================
        if not clip_chaos.isEmpty():
            painter.save()
            painter.setClipPath(clip_chaos)
            painter.fillRect(self.rect(), bg_color)
            painter.restore()

        if current_radius > 0:
            ring_pen = QPen(QColor(255, 255, 255, 180)) 
            ring_pen.setWidthF(2.0)
            painter.setPen(ring_pen)
            painter.drawEllipse(QPointF(self.cx, self.cy), current_radius, current_radius)

        # ==================================================
        # 3. POLVO DE PARTÍCULAS
        # ==================================================
        points, alphas = self.particle_system.get_drawing_data()
        
        for alpha_step in [40, 90, 140, 200, 255]:
            mask = (alphas >= alpha_step - 25) & (alphas <= alpha_step + 25)
            target_points = points[mask]
            
            if len(target_points) == 0: continue
            
            color_val = 200 if alpha_step < 200 else 255
            pen = QPen(QColor(color_val, color_val, color_val, alpha_step))
            pen.setWidth(2) # OPTIMIZACION: Tamaño mayor para llenar más espacio con menos partículas
            if alpha_step == 255: pen.setWidth(3) 
            
            painter.setPen(pen)
            qpoints = [QPointF(p[0], p[1]) for p in target_points]
            painter.drawPoints(qpoints)

        # ==================================================
        # 4. TEXTOS (Título, Subtítulo y Firma Corporativa)
        # ==================================================
        exp_progress = np.clip(self.progress / 0.60, 0.0, 1.0)
        assemble_ease = 1.0 - np.power(1.0 - exp_progress, 4)
        
        # Tipografías
        font_title = QFont("Arial Rounded MT Bold", 68, QFont.Bold)
        font_sub = QFont("Segoe UI", 20, QFont.Normal)
        font_footer = QFont("Segoe UI", 9, QFont.Bold) # Firma pequeña y pro
        
        tracking_title = 180 * (1.0 - assemble_ease) + 2
        tracking_sub = 8 
        tracking_footer = 10 # Tracking súper amplio para la firma
        
        # Textos
        text_title = "A H O R A"
        text_sub = "COBRAR ES FACIL"
        text_footer = "PENSADO PARA VOS   |   MACIEL COMPANY"
        
        # Posicionamiento absoluto
        rect_title = self.rect().adjusted(0, -30, 0, -30)
        rect_sub = self.rect().adjusted(0, 70, 0, 70)
        rect_footer = QRect(0, self.h - 60, self.w, 30) # Pegado al borde inferior

        # ==================================================
        # 4A. TEXTO DE CAOS (Contornos y Firma Opaca)
        # ==================================================
        if not clip_chaos.isEmpty() and exp_progress > 0.01:
            painter.save()
            painter.setClipPath(clip_chaos)
            
            text_alpha = int(assemble_ease * 255)
            
            # --- 1. Título Hueco (Contornos de Arena) ---
            font_title.setLetterSpacing(QFont.AbsoluteSpacing, tracking_title)
            painter.setFont(font_title)
            fuzziness = 20 * (1.0 - assemble_ease)
            edge_alpha = int(text_alpha / 2)
            
            thickness = 3
            for dx in [-thickness, 0, thickness]:
                for dy in [-thickness, 0, thickness]:
                    if dx == 0 and dy == 0: continue
                    rx = dx + random.uniform(-fuzziness, fuzziness)
                    ry = dy + random.uniform(-fuzziness, fuzziness)
                    painter.setPen(QColor(180, 180, 180, edge_alpha))
                    painter.drawText(rect_title.adjusted(int(rx), int(ry), int(rx), int(ry)), Qt.AlignCenter, text_title)

            painter.setPen(QColor(5, 5, 5, text_alpha)) 
            painter.drawText(rect_title, Qt.AlignCenter, text_title)

            # --- 2. Subtítulo (Gris apagado) ---
            font_sub.setLetterSpacing(QFont.AbsoluteSpacing, tracking_sub)
            painter.setFont(font_sub)
            painter.setPen(QColor(80, 80, 80, int(assemble_ease * 255)))
            painter.drawText(rect_sub, Qt.AlignCenter, text_sub)
            
            # --- 3. Firma Corporativa (Sutil emergiendo en la oscuridad) ---
            font_footer.setLetterSpacing(QFont.AbsoluteSpacing, tracking_footer)
            painter.setFont(font_footer)
            painter.setPen(QColor(60, 60, 60, int(assemble_ease * 255)))
            painter.drawText(rect_footer, Qt.AlignCenter, text_footer)
            
            painter.restore()

        # ==================================================
        # 4B. TEXTO PURIFICADO (3D Pastel y Firma Brillante)
        # ==================================================
        if not clip_purified.isEmpty():
            painter.save()
            painter.setClipPath(clip_purified)
            
            # --- 1. Título 3D ---
            font_title.setLetterSpacing(QFont.AbsoluteSpacing, 2)
            painter.setFont(font_title)
            
            depth = 8
            for i in range(depth, 0, -1):
                painter.setPen(QColor(40, 45, 60))
                painter.drawText(rect_title.adjusted(i, i, i, i), Qt.AlignCenter, text_title)

            face_grad = QLinearGradient(QPointF(self.cx - 200, self.cy - 100), QPointF(self.cx + 200, self.cy + 100))
            face_grad.setColorAt(0.0, QColor(160, 240, 250))
            face_grad.setColorAt(1.0, QColor(220, 180, 255))
            
            painter.setPen(QPen(QBrush(face_grad), 0))
            painter.drawText(rect_title, Qt.AlignCenter, text_title)

            # --- 2. Subtítulo (Cian puro) ---
            font_sub.setLetterSpacing(QFont.AbsoluteSpacing, tracking_sub)
            painter.setFont(font_sub)
            painter.setPen(QColor(160, 220, 230))
            painter.drawText(rect_sub, Qt.AlignCenter, text_sub)
            
            # --- 3. Firma Corporativa (Limpia y brillante) ---
            font_footer.setLetterSpacing(QFont.AbsoluteSpacing, tracking_footer)
            painter.setFont(font_footer)
            painter.setPen(QColor(160, 220, 230)) # Comparte el tono serio pero brillante del subtítulo
            painter.drawText(rect_footer, Qt.AlignCenter, text_footer)
            
            painter.restore()


