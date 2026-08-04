from PyQt6.QtWidgets import QFrame, QLabel, QScrollArea
from PyQt6.QtCore import Qt, QTimer, QRectF
from PyQt6.QtGui import QPainterPath, QRegion
from src.carteleria.theme import C_THEME, apply_apple_shadow


class Mensaje(QFrame):
    """
    Zócalo inferior con marquee.
    En .exe / HiDPI las fuentes en `pt` crecen y se salen: usamos `px` + QScrollArea
    como viewport (clip fiable) + máscara redondeada.
    """

    def __init__(
        self,
        texto_inicial="Novedad: Preguntá por nuestros cortes madurados. Descuento pagando en efectivo.",
        parent=None,
    ):
        super().__init__(parent)
        from src.carteleria.escala_tv import scaled_px

        self._h = scaled_px(52, self)
        self.setFixedHeight(self._h)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)

        from src.carteleria.theme import get_active_theme_name

        tema = get_active_theme_name()
        if tema == "temu":
            self.setStyleSheet(
                f"background: {C_THEME.get('surface', '#FFFFFF')}; "
                f"border-radius: 25px; border: 2px solid #F87171;"
            )
            color_texto = "#000000"
            apply_apple_shadow(self, blur=0, alpha=100, y_offset=6)
        else:
            self.setStyleSheet(
                f"background: {C_THEME.get('surface', '#FFFFFF')}; "
                f"border-radius: 25px; border: 1px solid rgba(255,255,255,0.5);"
            )
            color_texto = "#000000"
            apply_apple_shadow(self, blur=20, alpha=15, y_offset=5)

        # QScrollArea recorta el marquee (setMask solo a veces falla en exe HiDPI)
        self.viewport = QScrollArea(self)
        self.viewport.setFrameShape(QFrame.Shape.NoFrame)
        self.viewport.setWidgetResizable(False)
        self.viewport.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.viewport.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        self.viewport.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        fs = max(14, scaled_px(18, self))
        self.label = QLabel()
        self.label.setStyleSheet(
            f"color: {color_texto}; font-family: 'Segoe UI Black', 'Arial Black', sans-serif; "
            f"font-size: {fs}px; font-weight: 800; background: transparent; border: none;"
        )
        self.label.setFixedHeight(self._h)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.viewport.setWidget(self.label)

        self.texto_completo = ""
        self.offset = 30
        self.text_width = 0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animar)

        self.actualizar_texto(texto_inicial)

    def actualizar_texto(self, nuevo_texto):
        self.texto_completo = nuevo_texto or ""
        self._check_scroll()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Márgenes laterales: el texto no toca el borde curvo
        m = 36
        self.viewport.setGeometry(m, 0, max(0, self.width() - 2 * m), self._h)
        self._clip_rounded()
        self._check_scroll()

    def showEvent(self, event):
        super().showEvent(event)
        self._clip_rounded()

    def _clip_rounded(self):
        if self.width() <= 0 or self.height() <= 0:
            return
        path = QPainterPath()
        path.addRoundedRect(QRectF(0.5, 0.5, self.width() - 1.0, self.height() - 1.0), 25.0, 25.0)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def _check_scroll(self):
        w = self.viewport.width() if self.viewport.width() > 0 else self.width()
        if w <= 0:
            return
        from src.carteleria.theme import get_active_theme_name

        sep = "          ★          " if get_active_theme_name() == "temu" else "          •          "
        bloque = (self.texto_completo or " ") + sep
        texto_render = bloque * 4
        self.label.setText(texto_render)
        self.label.adjustSize()
        self.text_width = max(1, self.label.width() // 4)
        self.label.setFixedHeight(self._h)
        if not self.timer.isActive():
            self.timer.start(25)

    def _animar(self):
        self.offset -= 2
        if self.offset <= -self.text_width:
            self.offset += self.text_width
        self.label.move(int(self.offset), 0)
