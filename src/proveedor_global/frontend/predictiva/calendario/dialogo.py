"""La tuerca. El centro de la pantalla no carga estos botones."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QWidget,
)
from PyQt6.QtCore import Qt

_DIAS = ("Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom")
_FORMULAS = ("Pollo", "Carne", "Cerdo", "Congelado", "Huevo")
_QSS_ON = (
    "QPushButton { background: #1D4ED8; color: white; border: none; border-radius: 8px; "
    "font-weight: 700; padding: 0 10px; }"
)
_QSS_OFF = (
    "QPushButton { background: white; color: #1E293B; border: 1px solid #CBD5E1; "
    "border-radius: 8px; font-weight: 700; padding: 0 10px; }"
)
_QSS_HORA = (
    "QLineEdit { background: white; color: #0F172A; border: 1px solid #CBD5E1; "
    "border-radius: 8px; padding: 0 8px; }"
)


class DialogoConfiguracion(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setMinimumSize(980, 640)
        self.setStyleSheet("QDialog { background: #F8FAFC; } QLabel { background: transparent; color: #334155; }")
        self._formulas = {}
        self._llega = {}
        self._dias = []
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(20, 16, 20, 16)
        raiz.setSpacing(12)
        titulo = QLabel("Configuración del local")
        titulo.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        raiz.addWidget(titulo)
        nota = QLabel(
            "Acá se marcan los repartos, los días abiertos y el horario. "
            "El pedido queda en el centro de Compra predictiva."
        )
        nota.setWordWrap(True)
        raiz.addWidget(nota)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        cuerpo = QWidget()
        lay = QVBoxLayout(cuerpo)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(16)
        lay.addWidget(self._seccion("Días de reparto"))
        for nombre in _FORMULAS:
            lay.addWidget(self._fila_dias(nombre, self._formulas))
        lay.addWidget(self._seccion("Llegada de la mercadería fresca"))
        lay.addWidget(self._fila_llegada())
        lay.addWidget(self._seccion("Horario"))
        pista = QLabel("El día marcado abre. Corrido usa el primer horario. Doble turno usa los dos, uno al lado del otro.")
        pista.setWordWrap(True)
        lay.addWidget(pista)
        for indice, dia in enumerate(_DIAS):
            lay.addWidget(self._fila_dia(indice, dia))
        lay.addWidget(self._fila_feriado())
        lay.addStretch(1)
        scroll.setWidget(cuerpo)
        raiz.addWidget(scroll, 1)
        acciones = QHBoxLayout()
        acciones.addStretch(1)
        cancelar = QPushButton("Cancelar")
        cancelar.setFixedHeight(38)
        cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        cancelar.setStyleSheet(_QSS_OFF)
        cancelar.clicked.connect(self.reject)
        acciones.addWidget(cancelar)
        guardar = QPushButton("Guardar")
        guardar.setFixedHeight(38)
        guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        guardar.setStyleSheet(_QSS_ON)
        guardar.clicked.connect(self._guardar)
        acciones.addWidget(guardar)
        raiz.addLayout(acciones)
        self._cargar()

    def _seccion(self, texto: str) -> QLabel:
        rotulo = QLabel(texto)
        rotulo.setStyleSheet("font-size: 14px; font-weight: 700; color: #0F172A;")
        return rotulo

    def _fila_dias(self, nombre, destino) -> QWidget:
        caja = QWidget()
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(8)
        rotulo = QLabel(nombre)
        rotulo.setFixedWidth(90)
        rotulo.setStyleSheet("font-weight: 700;")
        fila.addWidget(rotulo)
        botones = []
        for dia in _DIAS:
            boton = self._boton(dia)
            boton.clicked.connect(self._pintar)
            botones.append(boton)
            fila.addWidget(boton)
        fila.addStretch(1)
        destino[nombre] = botones
        return caja

    def _fila_llegada(self) -> QWidget:
        caja = QWidget()
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(8)
        for clave, texto in (("manana", "Mañana"), ("tarde", "Tarde")):
            boton = self._boton(texto)
            boton.clicked.connect(lambda _estado, turno=clave: self._elegir_llegada(turno))
            self._llega[clave] = boton
            fila.addWidget(boton)
        fila.addStretch(1)
        return caja

    def _fila_dia(self, indice: int, dia: str) -> QWidget:
        caja = QWidget()
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(8)
        abierto = self._boton(dia)
        abierto.setFixedWidth(58)
        abierto.clicked.connect(self._pintar)
        fila.addWidget(abierto)
        corrido = self._boton("Corrido")
        doble = self._boton("Doble")
        corrido.clicked.connect(lambda _estado, n=indice: self._modo_dia(n, "corrido"))
        doble.clicked.connect(lambda _estado, n=indice: self._modo_dia(n, "doble"))
        fila.addWidget(corrido)
        fila.addWidget(doble)
        abre, cierra, _uno = self._par_horas(fila, "", "a")
        abre2, cierra2, segundo = self._par_horas(fila, "y de", "a")
        fila.addStretch(1)
        self._dias.append({
            "abierto": abierto,
            "corrido": corrido,
            "doble": doble,
            "abre": abre,
            "cierra": cierra,
            "abre2": abre2,
            "cierra2": cierra2,
            "segundo": segundo,
        })
        return caja

    def _fila_feriado(self) -> QWidget:
        from datetime import date

        from src.proveedor_global.frontend.predictiva.motor.feriados import de

        caja = QWidget()
        fila = QHBoxLayout(caja)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(8)
        nombre = QLabel("Feriado")
        nombre.setFixedWidth(58)
        nombre.setStyleSheet("font-weight: 700; color: #0F172A;")
        fila.addWidget(nombre)
        estado = QLabel("No abre")
        estado.setStyleSheet("font-weight: 700; color: #B45309;")
        fila.addWidget(estado)
        fechas = "  ".join(dia.strftime("%d/%m") for dia in sorted(de(date.today().year)))
        lista = QLabel(fechas)
        lista.setWordWrap(True)
        fila.addWidget(lista, 1)
        return caja

    def _par_horas(self, fila, antes, medio):
        rotulos = []
        if antes:
            rotulo = QLabel(antes)
            rotulos.append(rotulo)
            fila.addWidget(rotulo)
        abre = self._hora()
        fila.addWidget(abre)
        rotulo_medio = QLabel(medio)
        rotulos.append(rotulo_medio)
        fila.addWidget(rotulo_medio)
        cierra = self._hora()
        fila.addWidget(cierra)
        return abre, cierra, rotulos

    def _hora(self) -> QLineEdit:
        caja = QLineEdit()
        caja.setFixedWidth(68)
        caja.setFixedHeight(34)
        caja.setStyleSheet(_QSS_HORA)
        return caja

    def _boton(self, texto: str) -> QPushButton:
        boton = QPushButton(texto)
        boton.setCheckable(True)
        boton.setFixedHeight(34)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)
        return boton

    def _cargar(self):
        from src.proveedor_global.frontend.predictiva.calendario.jornada import leer
        from src.proveedor_global.frontend.predictiva.motor.memoria import leer as leer_reparto
        from src.proveedor_global.frontend.predictiva.motor.memoria import reparto_de

        datos = leer()
        reparto = leer_reparto()
        for nombre, botones in self._formulas.items():
            self._marcar(botones, reparto_de(reparto, nombre))
        self._elegir_llegada(datos.get("turno") or "manana", guardar=False)
        abiertos = set(int(dia) for dia in (datos.get("abiertos") or []))
        propios = datos.get("horarios") or {}
        for indice, fila in enumerate(self._dias):
            propio = propios.get(str(indice)) or {}
            fila["abierto"].setChecked(indice in abiertos)
            fila["abre"].setText(propio.get("abre") or datos.get("abre") or "08:00")
            fila["cierra"].setText(propio.get("cierra") or datos.get("cierra") or "20:00")
            fila["abre2"].setText(propio.get("turno2_abre") or datos.get("turno2_abre") or "17:00")
            fila["cierra2"].setText(propio.get("turno2_cierra") or datos.get("turno2_cierra") or "21:00")
            self._modo_dia(indice, propio.get("modo") or datos.get("modo") or "corrido", guardar=False)
        self._pintar()

    def _marcar(self, botones, puestos):
        elegidos = {int(dia) for dia in puestos}
        for indice, boton in enumerate(botones):
            boton.setChecked(indice in elegidos)

    def _elegir_llegada(self, turno, guardar=True):
        for clave, boton in self._llega.items():
            boton.setChecked(clave == turno)
        if guardar:
            self._pintar()

    def _modo_dia(self, indice, modo, guardar=True):
        fila = self._dias[indice]
        fila["corrido"].setChecked(modo != "doble")
        fila["doble"].setChecked(modo == "doble")
        if guardar:
            self._pintar()

    def _pintar(self):
        for botones in list(self._formulas.values()) + [list(self._llega.values())]:
            for boton in botones:
                boton.setStyleSheet(_QSS_ON if boton.isChecked() else _QSS_OFF)
        for fila in self._dias:
            abierto = fila["abierto"].isChecked()
            for clave in ("corrido", "doble", "abre", "cierra", "abre2", "cierra2"):
                fila[clave].setEnabled(abierto)
            for pieza in fila["segundo"]:
                pieza.setEnabled(abierto and fila["doble"].isChecked())
            for boton in (fila["abierto"], fila["corrido"], fila["doble"]):
                boton.setStyleSheet(_QSS_ON if boton.isChecked() else _QSS_OFF)

    def _guardar(self):
        from src.proveedor_global.frontend.predictiva.calendario.jornada import guardar as guardar_local
        from src.proveedor_global.frontend.predictiva.calendario.jornada import leer as leer_local
        from src.proveedor_global.frontend.predictiva.motor.memoria import guardar, leer

        datos = leer()
        formulas = {}
        for nombre, botones in self._formulas.items():
            formulas[nombre] = {"reparto": [i for i, boton in enumerate(botones) if boton.isChecked()]}
        datos["formulas"] = formulas
        datos["reparto"] = list((formulas.get("Pollo") or {}).get("reparto") or [])
        guardar(datos)
        actual = leer_local()
        abiertos = [i for i, fila in enumerate(self._dias) if fila["abierto"].isChecked()]
        filas = {}
        for indice, fila in enumerate(self._dias):
            if indice not in abiertos:
                continue
            filas[str(indice)] = {
                "modo": "doble" if fila["doble"].isChecked() else "corrido",
                "abre": _hhmm(fila["abre"].text(), "08:00"),
                "cierra": _hhmm(fila["cierra"].text(), "20:00"),
                "turno2_abre": _hhmm(fila["abre2"].text(), "17:00"),
                "turno2_cierra": _hhmm(fila["cierra2"].text(), "21:00"),
            }
        patron = _patron(filas) or {
            "modo": "corrido", "abre": "08:00", "cierra": "20:00",
            "turno2_abre": "17:00", "turno2_cierra": "21:00",
        }
        distintos = {
            clave: valor for clave, valor in filas.items()
            if valor["modo"] != patron["modo"]
            or valor["abre"] != patron["abre"] or valor["cierra"] != patron["cierra"]
            or valor["turno2_abre"] != patron["turno2_abre"]
            or valor["turno2_cierra"] != patron["turno2_cierra"]
        }
        guardar_local({
            "abiertos": abiertos,
            "modo": patron["modo"],
            "abre": patron["abre"],
            "cierra": patron["cierra"],
            "turno2_abre": patron["turno2_abre"],
            "turno2_cierra": patron["turno2_cierra"],
            "turno": "tarde" if self._llega["tarde"].isChecked() else "manana",
            "turnos": actual.get("turnos") or {},
            "horarios": distintos,
            "cierres": actual.get("cierres") or [],
        })
        self.accept()


def _hhmm(texto, respaldo: str) -> str:
    partes = str(texto or "").strip().split(":")
    if len(partes) != 2:
        return respaldo
    try:
        hora, minuto = int(partes[0]), int(partes[1])
    except ValueError:
        return respaldo
    if 0 <= hora <= 23 and 0 <= minuto <= 59:
        return f"{hora:02d}:{minuto:02d}"
    return respaldo


def _patron(filas: dict) -> dict:
    """La jornada más larga. Un día más corto queda como excepción."""
    if not filas:
        return {}

    def minutos(fila) -> int:
        primero = _tramo(fila["abre"], fila["cierra"])
        if fila["modo"] == "doble":
            return primero + _tramo(fila["turno2_abre"], fila["turno2_cierra"])
        return primero

    return filas[max(filas, key=lambda clave: minutos(filas[clave]))]


def _tramo(abre, cierra) -> int:
    ah, am = str(abre).split(":", 1)
    ch, cm = str(cierra).split(":", 1)
    return max(0, (int(ch) * 60 + int(cm)) - (int(ah) * 60 + int(am)))
