from PyQt6.QtCore import QPoint
from src.carteleria.theme import C_THEME
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGraphicsDropShadowEffect, QGridLayout
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor
import os
from src.utils.paths import get_base_path

class MiniCardGastador(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 2px solid #FDA4AF; /* Rosa gastador */
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(15, 10, 15, 10)

        self.lbl_nombre = QLabel()
        self.lbl_nombre.setWordWrap(True)
        self.lbl_nombre.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 16px; font-weight: 800; color: {C_THEME['text']}; border: none;")

        self.lbl_diferencia = QLabel()
        self.lbl_diferencia.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_diferencia.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 18px; font-weight: 900; color: {C_THEME['accent']}; border: none;")

        self.lay.addWidget(self.lbl_nombre, 1)
        self.lay.addWidget(self.lbl_diferencia, 0)

    def set_datos(self, nombre, precio, ahorro_total):
        self.lbl_nombre.setText(nombre)
        if ahorro_total > 0:
            diferencia = precio - ahorro_total
            if diferencia <= 0:
                self.lbl_diferencia.setText("¡Es GRATIS!")
            else:
                self.lbl_diferencia.setText(f"Ponés solo:\n${diferencia:,.2f}")
        else:
            self.lbl_diferencia.setText(f"${precio:,.2f}")

class MiniCardAhorrador(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 2px solid #6EE7B7; /* Verde ahorrador */
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        self.lay = QHBoxLayout(self)
        self.lay.setContentsMargins(15, 10, 15, 10)

        self.lbl_nombre = QLabel()
        self.lbl_nombre.setWordWrap(True)
        self.lbl_nombre.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 16px; font-weight: 800; color: {C_THEME['text']}; border: none;")

        vbox = QVBoxLayout()
        vbox.setSpacing(0)
        
        self.lbl_precio_real = QLabel()
        self.lbl_precio_real.setAlignment(Qt.AlignRight)
        self.lbl_precio_real.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 14px; font-weight: bold; color: rgba(0,0,0,0.4); text-decoration: line-through; border: none;")

        self.lbl_precio_oferta = QLabel()
        self.lbl_precio_oferta.setAlignment(Qt.AlignRight)
        self.lbl_precio_oferta.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 18px; font-weight: 900; color: #059669; border: none;")

        self.lbl_suma_ahorro = QLabel()
        self.lbl_suma_ahorro.setAlignment(Qt.AlignRight)
        self.lbl_suma_ahorro.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 14px; font-weight: bold; color: #059669; border: none;")

        vbox.addWidget(self.lbl_precio_real)
        vbox.addWidget(self.lbl_precio_oferta)
        vbox.addWidget(self.lbl_suma_ahorro)

        self.lay.addWidget(self.lbl_nombre, 1)
        self.lay.addLayout(vbox, 0)

    def set_datos(self, nombre, precio_real, precio_oferta):
        self.lbl_nombre.setText(nombre)
        self.lbl_precio_real.setText(f"${precio_real:,.2f}")
        self.lbl_precio_oferta.setText(f"${precio_oferta:,.2f}")
        ganancia_extra = precio_real - precio_oferta
        if ganancia_extra > 0:
            self.lbl_suma_ahorro.setText(f"+ Sumás ${ganancia_extra:,.2f}")
        else:
            self.lbl_suma_ahorro.setText("")


class PantallaEspia(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FDF2F8, stop:1 #FCE7F3);")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # --- HEADER: LOBO + AHORRO ---
        header_lay = QHBoxLayout()
        header_lay.setSpacing(30)
        
        self.lbl_lobo = QLabel()
        path_lobo = os.path.join(os.path.dirname(__file__), "assets", "chef_lobo_wink.png")
        if os.path.exists(path_lobo):
            pix = QPixmap(path_lobo)
            self.lbl_lobo.setPixmap(pix.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.lbl_lobo.setText("🐺")
            self.lbl_lobo.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 80px; background: transparent;")
            
        header_lay.addWidget(self.lbl_lobo)
        
        text_lay = QVBoxLayout()
        self.lbl_ahorro = QLabel("🎉 ¡AHORRASTE $0.00!")
        self.lbl_ahorro.setStyleSheet(f"""
            font-family: 'Segoe UI', sans-serif; font-size: 48px; font-weight: 900; color: {C_THEME['accent']}; 
            background: transparent; text-shadow: 2px 2px 5px rgba(0,0,0,0.2);
        """)
        
        self.lbl_mensaje_ia = QLabel("¿Cómo querés exprimir tu ganancia?")
        self.lbl_mensaje_ia.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 24px; font-weight: bold; color: {C_THEME['text']}; background: transparent;")
        self.lbl_mensaje_ia.setWordWrap(True)
        
        self.lbl_clima = QLabel()
        self.lbl_clima.setStyleSheet("""
            font-family: 'Segoe UI', sans-serif; 
            font-size: 24px; 
            font-weight: 800; 
            color: #64748B; 
            background: rgba(255, 255, 255, 0.7);
            border-radius: 15px;
            padding: 10px 20px;
        """)
        self.lbl_clima.setAlignment(Qt.AlignCenter)
        
        text_lay.addStretch()
        text_lay.addWidget(self.lbl_ahorro)
        text_lay.addWidget(self.lbl_mensaje_ia)
        text_lay.addStretch()
        
        header_lay.addLayout(text_lay)
        header_lay.addStretch()
        header_lay.addWidget(self.lbl_clima, 0, Qt.AlignTop | Qt.AlignRight)
        
        main_layout.addLayout(header_lay)
        
        # --- CUERPO: SPLIT SCREEN ---
        split_lay = QHBoxLayout()
        split_lay.setSpacing(30)
        
        # Lado Izquierdo: GASTADOR
        gastador_widget = QFrame()
        gastador_widget.setStyleSheet("background: rgba(254, 226, 226, 0.5); border-radius: 20px; border: 2px dashed #FDA4AF;")
        gastador_lay = QVBoxLayout(gastador_widget)
        gastador_lay.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_titulo_g = QLabel("🔥 Perfil Gastador (Llevate más)")
        self.lbl_titulo_g.setAlignment(Qt.AlignCenter)
        self.lbl_titulo_g.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 22px; font-weight: 900; color: {C_THEME['accent']}; border: none; background: transparent;")
        gastador_lay.addWidget(self.lbl_titulo_g)
        
        self.cards_gastador = []
        for i in range(3):
            card = MiniCardGastador()
            gastador_lay.addWidget(card)
            self.cards_gastador.append(card)
        gastador_lay.addStretch()
        
        # Lado Derecho: AHORRADOR
        ahorrador_widget = QFrame()
        ahorrador_widget.setStyleSheet("background: rgba(209, 250, 229, 0.5); border-radius: 20px; border: 2px dashed #6EE7B7;")
        ahorrador_lay = QVBoxLayout(ahorrador_widget)
        ahorrador_lay.setContentsMargins(20, 20, 20, 20)
        
        self.lbl_titulo_a = QLabel("💸 Perfil Ahorrador (Stockeate)")
        self.lbl_titulo_a.setAlignment(Qt.AlignCenter)
        self.lbl_titulo_a.setStyleSheet(f"font-family: 'Segoe UI', sans-serif; font-size: 22px; font-weight: 900; color: #059669; border: none; background: transparent;")
        ahorrador_lay.addWidget(self.lbl_titulo_a)
        
        self.cards_ahorrador = []
        for i in range(3):
            card = MiniCardAhorrador()
            ahorrador_lay.addWidget(card)
            self.cards_ahorrador.append(card)
        ahorrador_lay.addStretch()
        
        split_lay.addWidget(gastador_widget, 1)
        split_lay.addWidget(ahorrador_widget, 1)
        
        main_layout.addLayout(split_lay)
        main_layout.setStretch(1, 1) 
        
        # Animación de latido en el Chef Lobo (Opacidad)
        from PyQt6.QtWidgets import QGraphicsOpacityEffect
        self.eff_lobo = QGraphicsOpacityEffect(self.lbl_lobo)
        self.lbl_lobo.setGraphicsEffect(self.eff_lobo)
        
        self.anim_lobo = QPropertyAnimation(self.eff_lobo, b"opacity")
        
    def showEvent(self, event):
        super().showEvent(event)
        try:
            # Animación de respiración/latido usando opacidad suave (entre 60% y 100%)
            self.anim_lobo.setStartValue(1.0)
            self.anim_lobo.setEndValue(0.6)
            self.anim_lobo.setDuration(1200)
            self.anim_lobo.setLoopCount(-1)
            self.anim_lobo.setEasingCurve(QEasingCurve.InOutSine)
            self.anim_lobo.start()
            print("[ESPIA_DEBUG] Animacion del lobo iniciada correctamente.")
        except Exception as e:
            print(f"[ESPIA_DEBUG] Error en animacion showEvent: {e}")

    def hideEvent(self, event):
        super().hideEvent(event)
        try:
            self.anim_lobo.stop()
        except:
            pass

    def actualizar(self, ahorro_total, mensaje_ia, lista_gastador, lista_ahorrador, clima_completo=("sol", "20°C Pilar")):
        import datetime
        hora = datetime.datetime.now().hour
        
        if 5 <= hora < 12:
            momento = "la mañana"
        elif 12 <= hora < 16:
            momento = "el almuerzo"
        elif 16 <= hora < 20:
            momento = "la merienda o por si cae visita"
        else:
            momento = "la cena"
            
        clima_icono, clima_txt_full = clima_completo
            
        if clima_icono == "lluvia":
            clima_txt = "lluvia"
            emoji_clima = "🌧️"
        elif clima_icono == "sol":
            clima_txt = "calor"
            emoji_clima = "🔴"
        else:
            clima_txt = "nublados"
            emoji_clima = "☁️"
            
        self.lbl_clima.setText(f"{emoji_clima} {clima_txt_full}")
            
        if ahorro_total > 0:
            self.lbl_ahorro.setText(f"🎉 ¡AHORRASTE ${ahorro_total:,.2f}!")
            self.lbl_titulo_g.setText(f"🔥 Ganaste ${ahorro_total:,.0f}, ¿canjeamos para {momento}?")
            self.lbl_titulo_a.setText(f"💰 Ganaste ${ahorro_total:,.0f}, ¿ganás más comprando para días de {clima_txt}?")
        else:
            self.lbl_ahorro.setText("✨ ¡EXCELENTE ELECCIÓN!")
            self.lbl_titulo_g.setText(f"🔥 Complementá tu compra para {momento}")
            self.lbl_titulo_a.setText(f"💰 Aprovechá estas ofertas para días de {clima_txt}")
            
        self.lbl_mensaje_ia.setText(mensaje_ia)
        
        # Actualizar lado gastador
        for i, card in enumerate(self.cards_gastador):
            if i < len(lista_gastador):
                card.show()
                p = lista_gastador[i]
                card.set_datos(p['nombre'], p['precio'], ahorro_total)
            else:
                card.hide()
                
        # Actualizar lado ahorrador
        for i, card in enumerate(self.cards_ahorrador):
            if i < len(lista_ahorrador):
                card.show()
                p = lista_ahorrador[i]
                poferta = p.get('precio_oferta', 0)
                if poferta == 0: poferta = p['precio'] * 0.9 # Fallback por seguridad
                card.set_datos(p['nombre'], p['precio'], poferta)
            else:
                card.hide()
