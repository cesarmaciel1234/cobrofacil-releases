from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

class MetricCard(QFrame):
    def __init__(self, titulo, icon, color="#3B82F6", parent=None):
        super().__init__(parent)
        self.setObjectName("MetricCard")
        self.color = color
        self.setMinimumHeight(88)
        self.setMaximumHeight(110)
        self.setStyleSheet(f"""
            QFrame#MetricCard {{
                background: white; border: 1px solid #E2E8F0; border-radius: 14px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(14)

        icon_frame = QFrame()
        icon_frame.setObjectName("MetricIconFrame")
        icon_frame.setFixedSize(42, 42)

        i_lay = QVBoxLayout(icon_frame)
        i_lay.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(icon)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        i_lay.addWidget(icon_lbl)
        lay.addWidget(icon_frame)

        v_lay = QVBoxLayout()
        v_lay.setSpacing(4)
        v_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.lbl_tit = QLabel(titulo.upper())
        self.lbl_tit.setObjectName("MetricTit")
        self.lbl_tit.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #475569; letter-spacing: 0.5px;"
        )

        v_lay.addWidget(self.lbl_tit)

        self.lbl_val = QLabel("••••••")
        self.lbl_val.setStyleSheet(f"font-size: 22px; font-weight: 900; color: {self.color};")

        v_lay.addWidget(self.lbl_val)
        lay.addLayout(v_lay, 1)

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(30)
        self._anim_timer.setSingleShot(True)
        self._anim_timer.timeout.connect(self._anim_tick)

    def revelar(self, valor, formato=True):

        self._animar(valor, formato)

    def _lbl_alive(self):
        try:
            from shiboken6 import isValid
            return bool(isValid(self.lbl_val))
        except Exception:
            try:
                self.lbl_val.objectName()
                return True
            except RuntimeError:
                return False

    def _animar(self, final, formato):
        self._anim_final = final
        self._anim_formato = formato
        self._anim_steps = 15
        self._curr_step = 0
        self._anim_timer.stop()
        self._anim_tick()

    def _anim_tick(self):
        if not self._lbl_alive():
            self._anim_timer.stop()
            return
        steps = self._anim_steps
        final = self._anim_final
        formato = self._anim_formato
        self._curr_step += 1
        v = final * (self._curr_step / steps)
        if formato:
            self.lbl_val.setText(f"$ {v:,.2f}")
        else:
            self.lbl_val.setText(f"{int(v)}")
        if self._curr_step >= steps:
            self._anim_timer.stop()
            if formato:
                self.lbl_val.setText(f"$ {final:,.2f}")
            else:
                self.lbl_val.setText(f"{int(final)}")
        else:
            self._anim_timer.start()
