import math
import random
from PyQt5.QtWidgets import QSplashScreen, QVBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect, QProgressBar
from PyQt5.QtCore import Qt, QTimer, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QColor, QPainter, QPainterPath, QLinearGradient, QRadialGradient, QPen, QBrush

class CobroFacilSplash(QSplashScreen):
    """
    Pantalla de Carga Inicial (Splash Screen) MAJESTUOSA para Cobro Fácil POS.
    Presenta:
      - Un Trofeo Holográfico Vectorial en el centro con una estrella brillante emergiendo.
      - Nebulosa radial pulsante de fondo.
      - Anillos de antigravedad girando en direcciones opuestas.
      - Contenedor de cristal templado traslúcido (Glassmorphism).
    """
    def __init__(self):
        # Lienzo de 440x350 para albergar el resplandor neón exterior sin recortes
        pixmap = QPixmap(440, 350)
        pixmap.fill(Qt.transparent)
        super().__init__(pixmap, Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Inicializar fases de animación
        self.rotation_angle = 0
        self.star_angle = 0  # Ángulo independiente para la estrella AI
        self.pulse_phase = 0.0
        
        # Sistema de partículas cósmicas (nebulosa interactiva)
        self.particles = []
        for _ in range(16):
            self.particles.append({
                'x': random.uniform(-90, 90),
                'y': random.uniform(-95, 65),
                'vx': random.uniform(-0.3, 0.3),
                'vy': random.uniform(-0.5, -0.15), # Flotan hacia arriba
                'size': random.uniform(1.2, 3.0),
                'color': random.choice([
                    QColor(96, 165, 250, 180),  # Azul brillante
                    QColor(167, 139, 250, 180), # Púrpura brillante
                    QColor(253, 224, 71, 180),  # Oro brillante
                ])
            })
        
        # Timer para renderizado fluido a 60 FPS (16ms)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.animate_frame)
        self.anim_timer.start(16)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)
        
        # Contenedor Base (Transparente para delegar el fondo al QPainter)
        self.container = QFrame()
        self.container.setObjectName("SplashContainer")
        self.container.setStyleSheet("background: transparent; border: none;")
        main_layout.addWidget(self.container)
        
        # Efecto de Resplandor Neón Externo
        glow = QGraphicsDropShadowEffect(self)
        glow.setBlurRadius(30)
        glow.setColor(QColor(99, 102, 241, 140)) # Resplandor índigo neón
        glow.setOffset(0, 0)
        self.container.setGraphicsEffect(glow)
        
        # Layout del contenido interno
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(15)
        
        # Espaciador vertical superior para dejar área libre al pintado del Trofeo y Órbitas
        layout.addSpacing(150)
        
        # Título y Subtítulo utilizando HTML y CSS en línea para renderizado nítido
        self.lbl_title = QLabel(self.container)
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setText("""
            <div style="text-align: center;">
                <span style="font-family: 'Segoe UI', 'Outfit', sans-serif; font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: 2px;">
                    CAJAFACIL <span style="color: #60A5FA;">PRO</span>
                </span>
                <br/>
                <span style="font-family: 'Segoe UI', 'Outfit', sans-serif; font-size: 10px; font-weight: 800; color: #94A3B8; letter-spacing: 5px; text-transform: uppercase;">
                    SISTEMA DE FACTURACIÓN POS
                </span>
            </div>
        """)
        self.lbl_title.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.lbl_title)
        
        # Separador Neón de Bordes Difusos
        self.separator = QFrame(self.container)
        self.separator.setFixedHeight(2)
        self.separator.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                stop:0 rgba(99, 102, 241, 0), 
                stop:0.5 rgba(99, 102, 241, 0.5), 
                stop:1 rgba(99, 102, 241, 0)
            );
            border: none;
        """)
        layout.addWidget(self.separator)
        
        layout.addStretch()
        
        # Barra de Progreso Neón
        self.progress_bar = QProgressBar(self.container)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                height: 6px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #8B5CF6);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Añadir un espaciador para separar el texto de estado de la barra de progreso
        layout.addSpacing(15)
        
        # Mensajes de Estado (Vacío para actuar como espaciador, pintado dinámico en paintEvent)
        self.lbl_status = QLabel("", self.container)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setFixedHeight(15)
        self.lbl_status.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.lbl_status)
        
        self.current_status_text = "Iniciando motor industrial..."
        
    def animate_frame(self):
        """Incrementa los parámetros de ángulo y fase, actualiza partículas y repinta el canvas."""
        self.rotation_angle = (self.rotation_angle + 1) % 360
        self.star_angle = (self.star_angle + 2) % 360  # velocidad ligera independiente
        self.pulse_phase += 0.04
        
        # Actualizar posiciones de las partículas
        for p in self.particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            
            # Envoltura en los bordes
            if p['x'] < -100: p['x'] = 100
            if p['x'] > 100: p['x'] = -100
            if p['y'] < -100: p['y'] = 80
            if p['y'] > 80: p['y'] = -100
            
        self.update()
        
    def paintEvent(self, event):
        """Dibuja el fondo de cristal y la majestuosa animación cósmica en 60 FPS con un trofeo 3D giratorio."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Obtener geometría del contenedor
        rect = self.container.geometry()
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        
        # 2. Dibujar fondo de cristal traslúcido (Glassmorphism 80% opaco)
        bg_grad = QLinearGradient(x, y, x + w, y + h)
        bg_grad.setColorAt(0.0, QColor(13, 17, 28, 215)) # Azul noche profundo
        bg_grad.setColorAt(1.0, QColor(6, 8, 14, 195))   # Carbón oscuro
        painter.setBrush(QBrush(bg_grad))
        
        border_grad = QLinearGradient(x, y, x + w, y + h)
        border_grad.setColorAt(0.0, QColor(99, 102, 241, 140)) # Indigo semi-transparente
        border_grad.setColorAt(1.0, QColor(59, 130, 246, 70))   # Azul sutil
        painter.setPen(QPen(border_grad, 2))
        
        painter.drawRoundedRect(x, y, w, h, 24, 24)
        
        # Coordenadas centrales para la animación (Tercio superior)
        cx = x + w // 2
        cy = y + 80
        
        # 3. Ondulación de brillo radial (Nebulosa Cósmica)
        pulse = (math.sin(self.pulse_phase) + 1.0) / 2.0 # Rango 0 a 1
        radial_r = 75 + int(12 * pulse)
        
        nebula_grad = QRadialGradient(cx, cy, radial_r)
        nebula_grad.setColorAt(0.0, QColor(139, 92, 246, 60)) # Púrpura central
        nebula_grad.setColorAt(0.5, QColor(59, 130, 246, 25))  # Azul medio
        nebula_grad.setColorAt(1.0, QColor(13, 17, 28, 0))     # Desvanecimiento
        
        painter.setBrush(QBrush(nebula_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(cx - radial_r, cy - radial_r, radial_r * 2, radial_r * 2)
        
        # Guardar estado para escalado y rotación de los elementos en 3D
        painter.save()
        painter.translate(cx, cy)
        scale = 1.0 + 0.05 * pulse
        painter.scale(scale, scale)
        
        # Parámetros 3D compartidos
        rotation_rad = math.radians(self.rotation_angle * 1.5) # Velocidad de giro del trofeo
        phi = math.radians(15) # Inclinación de cámara para perspectiva
        
        # Gradiente holográfico cósmico
        trophy_grad = QLinearGradient(-15, -15, 15, 25)
        trophy_grad.setColorAt(0.0, QColor(244, 63, 94))  # Rosa
        trophy_grad.setColorAt(0.5, QColor(139, 92, 246)) # Violeta
        trophy_grad.setColorAt(1.0, QColor(59, 130, 246))  # Azul
        
        # 3.1. Dibujar cono de proyección holográfica (Base -> Copa)
        proj_y = 38.0
        proj_r_x = 18.0
        proj_r_y = 4.0
        
        # Base de proyección de luz del emisor
        proj_grad = QRadialGradient(0.0, proj_y, proj_r_x)
        proj_grad.setColorAt(0.0, QColor(99, 102, 241, 180))
        proj_grad.setColorAt(1.0, QColor(13, 17, 28, 0))
        painter.setBrush(QBrush(proj_grad))
        painter.setPen(QPen(QColor(99, 102, 241, 100), 1.0))
        painter.drawEllipse(QPointF(0.0, proj_y), proj_r_x, proj_r_y)
        
        # Cono de luz difusa
        cone_path = QPainterPath()
        cone_path.moveTo(-proj_r_x, proj_y)
        cone_path.lineTo(-45, -35)
        cone_path.lineTo(45, -35)
        cone_path.lineTo(proj_r_x, proj_y)
        cone_path.closeSubpath()
        
        cone_grad = QLinearGradient(0, proj_y, 0, -35)
        cone_grad.setColorAt(0.0, QColor(99, 102, 241, 30))
        cone_grad.setColorAt(0.6, QColor(139, 92, 246, 12))
        cone_grad.setColorAt(1.0, QColor(59, 130, 246, 0))
        
        painter.setBrush(QBrush(cone_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(cone_path)
        
        # Haces de luz proyectados vibrantes (Rayos sutiles)
        painter.setBrush(Qt.NoBrush)
        for r_line in range(4):
            offset_x = 35.0 * math.sin(self.rotation_angle * 0.04 + r_line * 1.6)
            ray_opacity = int(12 + 8 * math.sin(self.rotation_angle * 0.08 + r_line))
            ray_pen = QPen(QColor(99, 102, 241, ray_opacity), 0.8)
            painter.setPen(ray_pen)
            painter.drawLine(QPointF(0.0, proj_y), QPointF(offset_x, -35.0))
            
        # 3.2. Sistema de constelaciones y partículas cósmicas (Drifting Nebula)
        # Dibujar enlaces de la constelación
        num_p = len(self.particles)
        for i in range(num_p):
            p1 = self.particles[i]
            for j in range(i + 1, num_p):
                p2 = self.particles[j]
                dx = p1['x'] - p2['x']
                dy = p1['y'] - p2['y']
                dist = math.hypot(dx, dy)
                if dist < 38.0:
                    alpha = int((1.0 - dist / 38.0) * 30)
                    pen_c = QPen(QColor(147, 197, 253, alpha), 0.6)
                    painter.setPen(pen_c)
                    painter.drawLine(QPointF(p1['x'], p1['y']), QPointF(p2['x'], p2['y']))
                    
        # Dibujar partículas brillantes
        for p in self.particles:
            twinkle = (math.sin(self.pulse_phase * 2.5 + p['x'] * 0.1) + 1.0) / 2.0
            r_size = p['size'] * (0.85 + 0.25 * twinkle)
            
            p_grad = QRadialGradient(p['x'], p['y'], r_size)
            p_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
            p_grad.setColorAt(0.4, p['color'])
            p_grad.setColorAt(1.0, QColor(p['color'].red(), p['color'].green(), p['color'].blue(), 0))
            
            painter.setBrush(QBrush(p_grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(p['x'], p['y']), r_size, r_size)
            
        # 4. Anillos Orbitales de Antigravedad en 3D
        def draw_tilted_orbit(radius, psi_deg, rot_angle_rad, color_primary, color_particle, is_dashed=False):
            psi = math.radians(psi_deg)
            orbit_path = QPainterPath()
            first = True
            for step in range(41):
                alpha = step * 2.0 * math.pi / 40.0
                
                # Coordenadas 3D en el plano del anillo
                x0 = radius * math.cos(alpha)
                z0 = radius * math.sin(alpha)
                y0 = 0.0
                
                # Rotación en el plano de la órbita (eje Z por psi)
                x1 = x0 * math.cos(psi) - y0 * math.sin(psi)
                y1 = x0 * math.sin(psi) + y0 * math.cos(psi)
                z1 = z0
                
                # Proyección de cámara inclinada por phi
                x_p = x1
                y_p = y1 * math.cos(phi) - z1 * math.sin(phi)
                
                if first:
                    orbit_path.moveTo(x_p, y_p)
                    first = False
                else:
                    orbit_path.lineTo(x_p, y_p)
            
            # Dibujar la línea de la órbita
            pen_style = Qt.DashLine if is_dashed else Qt.SolidLine
            pen_o = QPen(color_primary, 1.0, pen_style)
            painter.setPen(pen_o)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(orbit_path)
            
            # Calcular posición 3D de la partícula giratoria
            xp0 = radius * math.cos(rot_angle_rad)
            zp0 = radius * math.sin(rot_angle_rad)
            yp0 = 0.0
            
            xp1 = xp0 * math.cos(psi) - yp0 * math.sin(psi)
            yp1 = xp0 * math.sin(psi) + yp0 * math.cos(psi)
            zp1 = zp0
            
            xp_p = xp1
            yp_p = yp1 * math.cos(phi) - zp1 * math.sin(phi)
            
            # Dibujar partícula con resplandor radial
            part_r = 3.5 + 0.8 * pulse
            p_grad = QRadialGradient(xp_p, yp_p, part_r)
            p_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
            p_grad.setColorAt(0.4, color_particle)
            p_grad.setColorAt(1.0, QColor(color_particle.red(), color_particle.green(), color_particle.blue(), 0))
            
            painter.setBrush(QBrush(p_grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(xp_p, yp_p), part_r, part_r)
            
        # Dibujar órbita 1 (Azul neón, sentido antihorario, inclinación +25 grados)
        draw_tilted_orbit(
            radius=48, 
            psi_deg=25, 
            rot_angle_rad=-rotation_rad, 
            color_primary=QColor(59, 130, 246, 120), 
            color_particle=QColor(96, 165, 250),
            is_dashed=True
        )
        
        # Dibujar órbita 2 (Púrpura neón, sentido horario, inclinación -25 grados)
        draw_tilted_orbit(
            radius=58, 
            psi_deg=-25, 
            rot_angle_rad=rotation_rad * 1.2, 
            color_primary=QColor(139, 92, 246, 100), 
            color_particle=QColor(167, 139, 250),
            is_dashed=False
        )
        
        # 5. DIBUJAR TROFEO VECTORIAL HOLOGRÁFICO EN 3D
        # Función matemática del radio en función de Y
        def get_trophy_radius(y_val):
            if y_val <= 8.0: # Copa
                t = (8.0 - y_val) / 26.0
                return 4.5 + 10.5 * (t ** 1.5)
            elif y_val <= 18.0: # Tallo
                t = (y_val - 8.0) / 10.0
                return 3.5 - 1.2 * math.sin(math.pi * t)
            else: # Pedestal
                t = (y_val - 18.0) / 7.0
                return 3.5 + 8.5 * (t ** 2.0)
                
        # Dibujar paralelos (anillos horizontales de la copa y base)
        y_parallels = [-18, -11, -4, 3, 8, 13, 18, 21, 25]
        for yp in y_parallels:
            r_val = get_trophy_radius(yp)
            y_proj = yp * math.cos(phi)
            a = r_val
            b = r_val * math.sin(phi)
            
            # Anillo de apertura superior de la copa brilla más
            if yp == -18:
                pen_p = QPen(QColor(255, 255, 255, 180), 1.2)
            else:
                pen_p = QPen(QColor(139, 92, 246, 70), 0.8)
            painter.setPen(pen_p)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, y_proj), a, b)
            
        # Dibujar meridianos (líneas longitudinales en 3D)
        num_meridians = 8
        for i in range(num_meridians):
            theta = rotation_rad + (i * 2.0 * math.pi / num_meridians)
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)
            
            path = QPainterPath()
            first = True
            z_p = 0
            for y_val in range(-18, 26, 2):
                r_val = get_trophy_radius(y_val)
                x_3d = r_val * cos_theta
                z_3d = r_val * sin_theta
                
                x_p = x_3d
                y_p = y_val * math.cos(phi) - z_3d * math.sin(phi)
                z_p = y_val * math.sin(phi) + z_3d * math.cos(phi)
                
                if first:
                    path.moveTo(x_p, y_p)
                    first = False
                else:
                    path.lineTo(x_p, y_p)
            
            # Estilo del meridiano según si está de cara al usuario (Z >= 0) o detrás
                # Línea frontal (Z>=0) brillante, trasera (Z<0) tenue
                if z_p >= 0:
                    pen_m = QPen(QBrush(trophy_grad), 1.8)  # grueso y con gradiente neon
                else:
                    pen_m = QPen(QColor(99, 102, 241, 30), 0.7)  # semi‑transparente
            painter.setPen(pen_m)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)
            
        # Dibujar las dos asas (handles) del trofeo
        for angle_offset in [0.0, math.pi]:
            theta_h = rotation_rad + angle_offset
            sin_th = math.sin(theta_h)
            cos_th = math.cos(theta_h)
            
            h_path = QPainterPath()
            first = True
            z_p = 0
            for step in range(21):
                u = step / 20.0
                y_val = -15.0 + 19.0 * u
                r_c = get_trophy_radius(y_val)
                w = 11.0 * math.sin(math.pi * u)
                R_h = r_c + w
                
                x_3d = R_h * cos_th
                z_3d = R_h * sin_th
                
                x_p = x_3d
                y_p = y_val * math.cos(phi) - z_3d * math.sin(phi)
                z_p = y_val * math.sin(phi) + z_3d * math.cos(phi)
                
                if first:
                    h_path.moveTo(x_p, y_p)
                    first = False
                else:
                    h_path.lineTo(x_p, y_p)
                    
            # Estilo del asa (color y grosor según posición)
                # Asas: usar profundidad z para decidir estilo
                if z_p >= 0:
                    pen_h = QPen(QBrush(trophy_grad), 2.0)  # línea frontal más gruesa
                else:
                    pen_h = QPen(QColor(99, 102, 241, 30), 0.8)  # línea trasera tenue
            painter.setPen(pen_h)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(h_path)
            
        # 6. ESTRELLA DE INTELIGENCIA ARTIFICIAL EMERGIENDO DEL TROFEO (GIRATORIA)
        spark_cy = -23.0
        
        painter.save()
        painter.translate(0.0, spark_cy)
        painter.rotate(self.star_angle)  # Rotación independiente de la estrella AI
        
        spark_path = QPainterPath()
        spark_R = 12.0 + 2.0 * pulse
        spark_path.moveTo(0, -spark_R)
        spark_path.quadTo(0, 0, spark_R, 0)
        spark_path.quadTo(0, 0, 0, spark_R)
        spark_path.quadTo(0, 0, -spark_R, 0)
        spark_path.quadTo(0, 0, 0, -spark_R)
        
        spark_grad = QRadialGradient(0.0, 0.0, spark_R)
        spark_grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        spark_grad.setColorAt(0.4, QColor(253, 224, 71, 230)) # Oro brillante
        spark_grad.setColorAt(1.0, QColor(253, 224, 71, 0))
        
        painter.setBrush(QBrush(spark_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 200), 0.5))
        painter.drawPath(spark_path)
        
        # Núcleo brillante
        core_r = 2.5
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(0.0, 0.0), core_r, core_r)
        
        painter.restore()
        painter.restore()
        
        # 7. DIBUJAR MENSAJE DE ESTADO CON ANIMACIÓN (PULSO, ZOOM Y PARPADEO)
        label_rect = self.lbl_status.geometry()
        label_cx = label_rect.x() + label_rect.width() // 2
        label_cy = label_rect.y() + label_rect.height() // 2
        
        painter.save()
        painter.translate(label_cx, label_cy)
        
        is_final_step = "sistema" in self.current_status_text.lower()
        
        if is_final_step:
            # Verde brilloso con pequeño zoom parpadeando
            # El pulso va de 0 a 1
            pulse_text = (math.sin(self.pulse_phase * 3.0) + 1.0) / 2.0
            
            # Zoom muy pequeño para respetar el tamaño anterior
            scale_text = 1.0 + 0.03 * pulse_text
            painter.scale(scale_text, scale_text)
            
            # Fuente (mantenemos el tamaño original de 10px o 11px)
            font_status = painter.font()
            font_status.setFamily("Segoe UI")
            font_status.setPixelSize(11)
            font_status.setBold(True)
            painter.setFont(font_status)
            
            # Efecto de parpadeo (alfa variable para el glow)
            glow_alpha = int(40 + 80 * pulse_text)
            painter.setPen(QColor(74, 222, 128, glow_alpha))
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                painter.drawText(QRectF(-150 + dx, -7.5 + dy, 300, 15), Qt.AlignCenter, self.current_status_text)
                
            # Texto principal en verde brilloso
            main_alpha = int(180 + 75 * pulse_text)
            painter.setPen(QColor(74, 222, 128, main_alpha)) # #4ade80
            painter.drawText(QRectF(-150, -7.5, 300, 15), Qt.AlignCenter, self.current_status_text)
        else:
            # Gris elegante estándar
            font_status = painter.font()
            font_status.setFamily("Segoe UI")
            font_status.setPixelSize(11)
            font_status.setBold(True)
            painter.setFont(font_status)
            painter.setPen(QColor(148, 163, 184, 200)) # #94A3B8
            painter.drawText(QRectF(-150, -7.5, 300, 15), Qt.AlignCenter, self.current_status_text)
            
        painter.restore()
        
    def update_status(self, text, progress_val=None):
        """Actualiza el mensaje de estado, la barra de progreso y refresca la UI."""
        self.current_status_text = text
        if progress_val is not None:
            self.progress_bar.setValue(progress_val)
        self.update()
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.processEvents()
