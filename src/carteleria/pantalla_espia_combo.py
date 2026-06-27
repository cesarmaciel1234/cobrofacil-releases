"""Pantalla espía: animación de combo detectado (precios bajan, tachado, total final)."""
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
)
from src.carteleria.theme import C_THEME


class _LineaCombo(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame { background: #FFFFFF; border-radius: 14px; border: 2px solid #E2E8F0; }"
        )
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 25))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 12)

        self.lbl_nombre = QLabel()
        self.lbl_nombre.setWordWrap(True)
        self.lbl_nombre.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {C_THEME['text']}; border: none;"
        )

        col = QVBoxLayout()
        col.setSpacing(2)
        self.lbl_cant = QLabel()
        self.lbl_cant.setAlignment(Qt.AlignRight)
        self.lbl_cant.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #64748B; border: none;"
        )
        self.lbl_precio_lista = QLabel()
        self.lbl_precio_lista.setAlignment(Qt.AlignRight)
        self.lbl_precio_lista.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: rgba(0,0,0,0.35); border: none;"
        )
        self.lbl_precio_oferta = QLabel()
        self.lbl_precio_oferta.setAlignment(Qt.AlignRight)
        self.lbl_precio_oferta.setStyleSheet(
            "font-size: 22px; font-weight: 900; color: #059669; border: none;"
        )
        self.lbl_precio_oferta.hide()
        col.addWidget(self.lbl_cant)
        col.addWidget(self.lbl_precio_lista)
        col.addWidget(self.lbl_precio_oferta)

        lay.addWidget(self.lbl_nombre, 1)
        lay.addLayout(col, 0)

        self._precio_anim_timer = None
        self._precio_actual = 0.0
        self._precio_objetivo = 0.0

    def configurar(self, nombre, cantidad, precio_lista, precio_oferta):
        self.lbl_nombre.setText(nombre)
        self.lbl_cant.setText(f"x {cantidad:g}")
        self.lbl_precio_lista.setText(f"${precio_lista:,.2f}")
        self.lbl_precio_lista.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: rgba(0,0,0,0.35); border: none;"
        )
        self.lbl_precio_oferta.hide()
        self._precio_actual = precio_lista
        self._precio_objetivo = precio_oferta
        self._cant_objetivo = cantidad

    def animar_linea(self, on_done=None):
        """Tacha precio lista y baja el número hasta precio oferta."""
        self.lbl_precio_lista.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: rgba(0,0,0,0.35); "
            "text-decoration: line-through; border: none;"
        )
        pasos = 12
        delta = (self._precio_actual - self._precio_objetivo) / pasos
        step = [0]

        def tick():
            step[0] += 1
            self._precio_actual = max(self._precio_objetivo, self._precio_actual - delta)
            self.lbl_precio_lista.setText(f"${self._precio_actual:,.2f}")
            if step[0] >= pasos:
                self.lbl_precio_lista.setText(f"${self._precio_objetivo:,.2f}")
                self.lbl_precio_oferta.setText(f"→ ${self._precio_objetivo:,.2f}")
                self.lbl_precio_oferta.show()
                if on_done:
                    on_done()
                return
            QTimer.singleShot(45, tick)

        QTimer.singleShot(80, tick)


class PantallaEspiaCombo(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            "stop:0 #ECFDF5, stop:1 #D1FAE5);"
        )
        self._lineas = []
        self._combo_data = None

        root = QVBoxLayout(self)
        root.setContentsMargins(36, 28, 36, 28)
        root.setSpacing(16)

        self.lbl_titulo = QLabel("🎯 ¡COMBO ACTIVADO!")
        self.lbl_titulo.setAlignment(Qt.AlignCenter)
        self.lbl_titulo.setStyleSheet(
            f"font-size: 42px; font-weight: 900; color: {C_THEME['accent']}; background: transparent;"
        )
        root.addWidget(self.lbl_titulo)

        self.lbl_subtitulo = QLabel("")
        self.lbl_subtitulo.setAlignment(Qt.AlignCenter)
        self.lbl_subtitulo.setStyleSheet(
            "font-size: 22px; font-weight: 700; color: #334155; background: transparent;"
        )
        root.addWidget(self.lbl_subtitulo)

        self.cont_lineas = QVBoxLayout()
        self.cont_lineas.setSpacing(10)
        root.addLayout(self.cont_lineas, 1)

        footer = QFrame()
        footer.setStyleSheet(
            "QFrame { background: rgba(255,255,255,0.85); border-radius: 18px; border: 2px solid #6EE7B7; }"
        )
        fl = QVBoxLayout(footer)
        fl.setContentsMargins(24, 16, 24, 16)

        self.lbl_subtotal = QLabel()
        self.lbl_subtotal.setAlignment(Qt.AlignCenter)
        self.lbl_subtotal.setStyleSheet(
            "font-size: 20px; color: #64748B; font-weight: 600; border: none;"
        )
        self.lbl_descuento = QLabel()
        self.lbl_descuento.setAlignment(Qt.AlignCenter)
        self.lbl_descuento.setStyleSheet(
            "font-size: 24px; color: #DC2626; font-weight: 800; border: none;"
        )
        self.lbl_total = QLabel()
        self.lbl_total.setAlignment(Qt.AlignCenter)
        self.lbl_total.setStyleSheet(
            "font-size: 52px; font-weight: 900; color: #059669; border: none;"
        )
        self.lbl_total.hide()
        self.lbl_subtotal.hide()
        self.lbl_descuento.hide()

        fl.addWidget(self.lbl_subtotal)
        fl.addWidget(self.lbl_descuento)
        fl.addWidget(self.lbl_total)
        root.addWidget(footer)

        self._eff_total = QGraphicsOpacityEffect(self.lbl_total)
        self.lbl_total.setGraphicsEffect(self._eff_total)
        self._anim_bum = QPropertyAnimation(self._eff_total, b"opacity")

    def _limpiar_lineas(self):
        while self.cont_lineas.count():
            item = self.cont_lineas.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._lineas = []

    def iniciar_animacion(self, combo_data: dict):
        self._combo_data = combo_data or {}
        self._limpiar_lineas()
        self.lbl_subtitulo.setText(self._combo_data.get("nombre", "Combo especial"))
        self.lbl_subtotal.hide()
        self.lbl_descuento.hide()
        self.lbl_total.hide()
        self._eff_total.setOpacity(0.0)

        articulos = self._combo_data.get("articulos") or []
        for art in articulos:
            linea = _LineaCombo()
            linea.configurar(
                art.get("nombre", "Producto"),
                float(art.get("cantidad") or 1),
                float(art.get("precio_lista") or art.get("precio_unitario") or 0),
                float(art.get("precio_combo_unit") or art.get("precio_unitario") or 0),
            )
            self.cont_lineas.addWidget(linea)
            self._lineas.append(linea)

        QTimer.singleShot(400, self._secuencia_lineas)

    def _secuencia_lineas(self):
        idx = [0]

        def siguiente():
            if idx[0] >= len(self._lineas):
                QTimer.singleShot(300, self._mostrar_total_bum)
                return
            linea = self._lineas[idx[0]]
            idx[0] += 1
            linea.animar_linea(on_done=siguiente)

        if self._lineas:
            siguiente()
        else:
            self._mostrar_total_bum()

    def _mostrar_total_bum(self):
        d = self._combo_data or {}
        total_lista = float(d.get("total_lista") or 0)
        ahorro = float(d.get("ahorro") or 0)
        total_combo = float(d.get("total_combo") or total_lista - ahorro)

        self.lbl_subtotal.setText(f"Subtotal: ${total_lista:,.2f}")
        self.lbl_descuento.setText(f"Descuento combo: −${ahorro:,.2f}")
        self.lbl_total.setText(f"TOTAL A PAGAR: ${total_combo:,.2f}")

        self.lbl_subtotal.show()
        self.lbl_descuento.show()
        self.lbl_total.show()

        self._anim_bum.stop()
        self._anim_bum.setStartValue(0.0)
        self._anim_bum.setEndValue(1.0)
        self._anim_bum.setDuration(550)
        self._anim_bum.setEasingCurve(QEasingCurve.OutBack)
        self._anim_bum.start()

    def hideEvent(self, event):
        super().hideEvent(event)
        try:
            self._anim_bum.stop()
        except Exception:
            pass
