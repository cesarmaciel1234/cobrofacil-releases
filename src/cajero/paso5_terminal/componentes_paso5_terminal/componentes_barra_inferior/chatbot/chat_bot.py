from src.utils.qt_compat import qt_exec
import os
import sys
import json
import unicodedata
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QLineEdit,
    QPushButton,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

_DIR = os.path.dirname(os.path.abspath(__file__))
MANUAL_JSON = os.path.join(_DIR, "manual_cajero.json")

PASOS_TUTOR = [
    {"msg": "Hola. Soy el asistente de CobroFacil. Estoy para ayudarte.", "espera": 3},
    {"msg": "Terminal: pasá el código de barras con el lector.", "espera": 4},
    {"msg": "Multiplicador: CANTIDAD * CÓDIGO (ej. 6*779001234) y ENTER.", "espera": 4},
    {"msg": "Sin código: +PRECIO (ej. +500) y ENTER.", "espera": 4},
    {"msg": "Balanza: escaneá el código. El precio sale solo.", "espera": 4},
    {"msg": "Cobrar: F12, o ENTER con el buscador vacío.", "espera": 4},
    {"msg": "Elegí el medio con las flechas y ENTER.", "espera": 4},
    {"msg": "F1 imprime el ticket. F2 cierra sin ticket. ENTER es como F2.", "espera": 4},
    {"msg": "En el cobro, F3 es redondeo y F4 es recargo.", "espera": 4},
    {"msg": "Si el cajón queda abierto, cerralo. Se destraba solo.", "espera": 4},
    {"msg": "F11 llama al supervisor.", "espera": 4},
    {"msg": "F3 en la venta abre el historial del día.", "espera": 4},
    {"msg": "F4 cierra el turno: contá el efectivo e ingresá el total.", "espera": 4},
    {"msg": "F1 ticket. F2 sin ticket. F3 historial. F4 cierre. F5 retiro. F11 supervisor. F12 cobrar.", "espera": 5},
    {"msg": "Listo. Escribí la consulta acá.", "espera": 3},
]


def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^\w\s]", "", sin_tildes).strip()


class ChatManual:
    def __init__(self):
        self.entradas = None

    def _cargar(self):
        try:
            with open(MANUAL_JSON, "r", encoding="utf-8") as f:
                self.entradas = json.load(f).get("entradas", [])
        except Exception as e:
            self.entradas = [{"id": "error", "preguntas": [], "respuesta": f"Error cargando manual: {e}"}]

    def consultar(self, texto: str) -> str:
        if self.entradas is None:
            self._cargar()
        q = _normalizar(texto.strip())
        if not q:
            return ""
        mejor_score, mejor_resp = 0, None
        for entrada in self.entradas:
            if not entrada.get("preguntas"):
                continue
            score = sum(len(kw) for kw in entrada["preguntas"] if _normalizar(kw) in q)
            if score > mejor_score:
                mejor_score, mejor_resp = score, entrada["respuesta"]
        if mejor_resp:
            return mejor_resp
        for entrada in self.entradas:
            if entrada.get("id") == "no_encontrado":
                return entrada["respuesta"]
        return "No encontré eso. Consultá al supervisor."


class ChatManualWidget(QWidget):
    """Panel del asistente. No abre Chromium ni otra ventana."""

    request_dashboard = pyqtSignal()
    chat_closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.resize(420, 520)
        self.motor = ChatManual()
        self._tutor_idx = 0
        self._tutor_activo = False
        self._tutor_timer = QTimer(self)
        self._tutor_timer.setSingleShot(True)
        self._tutor_timer.timeout.connect(self._tutor_ejecutar_paso)
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("AsistenteCajero")
        self.setStyleSheet(
            "QWidget#AsistenteCajero { background: #0F172A; border: 1px solid #334155; }"
            "QLabel#AsistenteTitulo { color: #F8FAFC; font-size: 16px; font-weight: 800; background: transparent; border: none; }"
            "QTextEdit#AsistenteTexto { background: #1E293B; color: #F8FAFC; border: none; font-size: 15px; }"
            "QLineEdit#AsistenteEntrada { background: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; "
            "border-radius: 8px; padding: 8px; font-size: 15px; }"
            "QPushButton { background: #1E293B; color: #F8FAFC; border: 1px solid #334155; "
            "border-radius: 8px; font-weight: 800; padding: 8px 12px; }"
            "QPushButton#AsistenteEnviar { background: #2563EB; color: white; border: none; }"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        cabeza = QHBoxLayout()
        titulo = QLabel("Asistente")
        titulo.setObjectName("AsistenteTitulo")
        cabeza.addWidget(titulo)
        cabeza.addStretch(1)
        tutorial = QPushButton("Tutorial")
        tutorial.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        tutorial.clicked.connect(self._empezar_tutor)
        cerrar = QPushButton("Cerrar")
        cerrar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        cerrar.clicked.connect(self.cerrar_chat)
        cabeza.addWidget(tutorial)
        cabeza.addWidget(cerrar)
        lay.addLayout(cabeza)

        self.texto = QTextEdit()
        self.texto.setObjectName("AsistenteTexto")
        self.texto.setReadOnly(True)
        self.texto.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        lay.addWidget(self.texto, 1)

        fila = QHBoxLayout()
        self.entrada = QLineEdit()
        self.entrada.setObjectName("AsistenteEntrada")
        self.entrada.setPlaceholderText("Escribí la consulta")
        self.entrada.returnPressed.connect(self._preguntar)
        enviar = QPushButton("Enviar")
        enviar.setObjectName("AsistenteEnviar")
        enviar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        enviar.clicked.connect(self._preguntar)
        fila.addWidget(self.entrada, 1)
        fila.addWidget(enviar)
        lay.addLayout(fila)
        self._linea("Asistente", "Escribí una consulta o tocá Tutorial.")

    def _linea(self, quien, mensaje):
        self.texto.append(f"{quien}: {mensaje}")
        self.texto.verticalScrollBar().setValue(self.texto.verticalScrollBar().maximum())

    def _preguntar(self):
        texto = self.entrada.text().strip()
        if not texto:
            return
        self.entrada.clear()
        self._linea("Vos", texto)
        self._linea("Asistente", self.motor.consultar(texto))

    def _empezar_tutor(self):
        self._tutor_timer.stop()
        self._tutor_idx = 0
        self._tutor_activo = True
        self._tutor_ejecutar_paso()

    def _tutor_ejecutar_paso(self):
        if not self._tutor_activo:
            return
        if self._tutor_idx >= len(PASOS_TUTOR):
            self._tutor_activo = False
            return
        paso = PASOS_TUTOR[self._tutor_idx]
        self._linea("Asistente", paso["msg"])
        self._tutor_idx += 1
        if self._tutor_idx < len(PASOS_TUTOR):
            self._tutor_timer.start(int(paso.get("espera", 3) * 1000))
        else:
            self._tutor_activo = False

    def actualizar_posicion(self):
        pw = self.parent_window or self.parent()
        if not pw:
            return
        margen = 96
        alto = min(560, max(320, pw.height() - margen - 24))
        ancho = min(440, max(320, pw.width() - 40))
        self.resize(ancho, alto)
        x = pw.width() - self.width() - 16
        y = pw.height() - self.height() - margen
        self.move(max(0, x), max(0, y))

    def abrir_y_desplegar(self):
        self.actualizar_posicion()
        self.show()
        self.raise_()

    def cerrar_chat(self):
        self._tutor_activo = False
        self._tutor_timer.stop()
        self.hide()
        self.chat_closed.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ChatManualWidget()
    win.setWindowTitle("Asistente")
    win.resize(440, 560)
    win.show()
    sys.exit(qt_exec(app))
