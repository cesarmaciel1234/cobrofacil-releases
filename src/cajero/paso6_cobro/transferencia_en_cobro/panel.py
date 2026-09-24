import threading

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from src.config import config
from src.cajero.paso6_cobro.transferencia_en_cobro.cuenta import datos_cuenta


class PanelAliasCobro(QFrame):
    """Alias y nombre de la cuenta. El monto lo mueven redondeo y recargo."""

    _llegada = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._editando = False
        self._llegada.connect(self._pintar)
        self.hide()
        self._armar()

    def _armar(self):
        from PyQt6.QtWidgets import QSizePolicy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("background: transparent; border: none;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 0, 0, 8)
        lay.setSpacing(6)

        techo = QHBoxLayout()
        techo.setContentsMargins(0, 0, 0, 0)
        rotulo = QLabel("ALIAS")
        rotulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rotulo.setStyleSheet(
            "color: #64748B; font-size: 16px; font-weight: 800; letter-spacing: 1px; "
            "background: transparent; border: none;"
        )
        self.lapiz = QPushButton("✎")
        self.lapiz.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lapiz.setFixedSize(52, 52)
        self.lapiz.setStyleSheet(
            "QPushButton { background: #FFFFFF; color: #1E3A8A; border: 2px solid #CBD5E1; "
            "border-radius: 14px; font-size: 26px; font-weight: 900; }"
            "QPushButton:hover { background: #EFF6FF; }"
        )
        self.lapiz.clicked.connect(self._lapiz)
        techo.addStretch(1)
        techo.addWidget(rotulo)
        techo.addStretch(1)
        techo.addWidget(self.lapiz, 0, Qt.AlignmentFlag.AlignTop)
        lay.addLayout(techo)

        self.alias = QLabel("Buscando alias…")
        self.alias.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alias.setWordWrap(True)
        self.alias.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.alias.setStyleSheet(
            "color: #1E3A8A; font-size: 64px; font-weight: 900; background: transparent; border: none;"
        )
        self.caja = QLineEdit()
        self.caja.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caja.setPlaceholderText("alias.mp")
        self.caja.setFixedHeight(92)
        self.caja.setStyleSheet(
            "font-size: 48px; font-weight: 900; border-radius: 16px; border: 2px solid #2563EB; "
            "color: #1E3A8A; background: #FFFFFF;"
        )
        self.caja.returnPressed.connect(self._guardar)
        self.caja.hide()
        lay.addWidget(self.alias, 1)
        lay.addWidget(self.caja)

        self.nombre = QLabel("")
        self.nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.nombre.setWordWrap(True)
        self.nombre.setStyleSheet(
            "color: #0F172A; font-size: 36px; font-weight: 900; background: transparent; border: none;"
        )
        lay.addWidget(self.nombre)

    def mostrar(self):
        config._load_config()
        previo = str(config.get("mp_alias", "") or "").strip()
        nombre = str(config.get("mp_nombre", "") or "").strip()
        if previo:
            self.alias.setText(previo)
        else:
            self.alias.setText("Buscando alias…")
        self.nombre.setText(nombre)
        self._cerrar_edicion()
        self.show()

        def _trabajo():
            self._llegada.emit(datos_cuenta())

        threading.Thread(target=_trabajo, daemon=True).start()

    def ocultar(self):
        self._cerrar_edicion()
        self.hide()

    def _pintar(self, datos):
        if not self.isVisible() or self._editando:
            return
        alias = str((datos or {}).get("alias") or "").strip()
        nombre = str((datos or {}).get("nombre") or "").strip()
        self.alias.setText(alias or "Sin alias")
        self.nombre.setText(nombre)
        if nombre:
            config.set("mp_nombre", nombre)

    def _lapiz(self):
        if self._editando:
            self._guardar()
            return
        self._editando = True
        texto = self.alias.text().strip()
        if texto in ("Buscando alias…", "Sin alias"):
            texto = ""
        self.caja.setText(texto)
        self.alias.hide()
        self.caja.show()
        self.caja.setFocus()
        self.caja.selectAll()
        self.lapiz.setText("✓")

    def _guardar(self):
        alias = self.caja.text().strip()
        config.set("mp_alias", alias)
        self.alias.setText(alias or "Sin alias")
        self._cerrar_edicion()

    def _cerrar_edicion(self):
        self._editando = False
        self.caja.hide()
        self.alias.show()
        self.lapiz.setText("✎")
