from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

_HOJA = """
QFrame#PanelRedondeoRecargo {
    background: transparent;
    border: none;
}
QFrame#CajaRedondeo, QFrame#CajaRecargo {
    background: transparent;
    border: none;
}
QLabel#TituloRedondeo, QLabel#TituloRecargo {
    color: #1E3A8A;
    font-size: 13px;
    font-weight: 900;
    letter-spacing: 0.4px;
    background: transparent;
    border: none;
}
QPushButton#BtnSimboloRedondeo, QPushButton#BtnSimboloRecargo {
    background: #FACC15;
    color: #0F172A;
    border: none;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 900;
}
QPushButton#BtnSimboloRedondeo:hover, QPushButton#BtnSimboloRecargo:hover {
    background: #EAB308;
}
QLineEdit#MontoRedondeo, QLineEdit#MontoRecargo {
    background: #FFFFFF;
    color: #0F172A;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    font-size: 16px;
    font-weight: 900;
    padding: 4px 8px;
}
QLineEdit#MontoRedondeo:focus {
    border: 2px solid #10B981;
}
QLineEdit#MontoRecargo:focus {
    border: 2px solid #F59E0B;
}
"""


class PanelRedondeoRecargo(QFrame):
    """Redondeo y recargo compactos. Letras en negrita. $ por defecto; solo clic cambia a %."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PanelRedondeoRecargo")
        self.setStyleSheet(_HOJA)
        fila = QHBoxLayout(self)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(10)

        self.lbl_desc, self.btn_tipo_desc, self.txt_desc = self._grupo(
            fila, "REDONDEO", "CajaRedondeo", "TituloRedondeo",
            "BtnSimboloRedondeo", "MontoRedondeo",
        )
        self.lbl_rec, self.btn_tipo_rec, self.txt_rec = self._grupo(
            fila, "RECARGO", "CajaRecargo", "TituloRecargo",
            "BtnSimboloRecargo", "MontoRecargo",
        )
        self.resetear_pesos()

    def _grupo(self, fila, titulo, id_caja, id_lbl, id_btn, id_txt):
        caja = QFrame()
        caja.setObjectName(id_caja)
        caja_lay = QHBoxLayout(caja)
        caja_lay.setContentsMargins(0, 0, 0, 0)
        caja_lay.setSpacing(6)
        lbl = QLabel(titulo)
        lbl.setObjectName(id_lbl)
        fuente = QFont()
        fuente.setPixelSize(13)
        fuente.setBold(True)
        lbl.setFont(fuente)
        txt = QLineEdit("")
        txt.setObjectName(id_txt)
        txt.setFixedHeight(32)
        txt.setFont(QFont("Segoe UI", 11, QFont.Weight.Black))
        txt.setPlaceholderText("0,00")
        btn = QPushButton("$")
        btn.setObjectName(id_btn)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        btn.setDefault(False)
        btn.setAutoDefault(False)
        btn.setFixedSize(32, 32)
        btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Black))
        btn.setToolTip("Clic para %. Enter no lo cambia.")
        caja_lay.addWidget(lbl, 0)
        caja_lay.addWidget(txt, 1)
        caja_lay.addWidget(btn, 0)
        fila.addWidget(caja, 1)
        return lbl, btn, txt

    def resetear_pesos(self):
        self.btn_tipo_desc.setText("$")
        self.btn_tipo_rec.setText("$")
