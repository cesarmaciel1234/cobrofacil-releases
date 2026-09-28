"""Elegir una copia (respaldo del admin o pendrive del jefe) y restaurar la tienda con el motor único."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from src.config import CLAVE_RED

CLAVE_JEFE = "209470"
BTN = (
    "QPushButton { background: #F1F5F9; color: #0F172A; border: 1px solid #E2E8F0; border-radius: 8px;"
    " padding: 8px 14px; font-size: 13px; font-weight: 600; }"
    "QPushButton:hover { background: #E2E8F0; } QPushButton:disabled { color: #94A3B8; }"
)
BTN_OK = (
    "QPushButton { background: #3B82F6; color: white; border: none; border-radius: 8px;"
    " padding: 10px 18px; font-size: 14px; font-weight: bold; }"
    "QPushButton:hover { background: #2563EB; } QPushButton:disabled { background: #BFDBFE; }"
)
TABLA = (
    "QTableWidget { background: white; border: 1px solid #E2E8F0; border-radius: 8px; font-size: 13px;"
    " selection-background-color: #DBEAFE; selection-color: #0F172A; }"
    "QHeaderView::section { background: #F8FAFC; color: #475569; border: none;"
    " border-bottom: 1px solid #E2E8F0; padding: 6px; font-weight: 600; }"
)
AVISO = "background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; border-radius: 8px; padding: 10px; font-size: 12px;"
BLOQUEO = "background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; border-radius: 8px; padding: 10px; font-size: 12px;"


class _Busqueda(QThread):
    listo = pyqtSignal(object, list, str)

    def __init__(self, rutas: list[str], parent=None):
        super().__init__(parent)
        self.rutas = rutas

    def run(self):
        from src.base_de_datos import restaurar

        destino, error = None, ""
        try:
            destino = restaurar.destino_actual()
        except Exception as e:
            error = str(e)
        try:
            fuentes = restaurar.buscar(*self.rutas)
        except Exception as e:
            fuentes, error = [], error or f"No se pudo buscar: {e}"
        self.listo.emit(destino, fuentes, error)


class _Trabajo(QThread):
    avance = pyqtSignal(int, str)
    listo = pyqtSignal(dict)
    fallo = pyqtSignal(str)

    def __init__(self, fuente, destino, parent=None):
        super().__init__(parent)
        self.fuente, self.destino = fuente, destino

    def run(self):
        from src.base_de_datos import restaurar

        try:
            self.listo.emit(restaurar.restaurar(self.fuente, self.destino, lambda p, t: self.avance.emit(p, t)))
        except Exception as e:
            self.fallo.emit(str(e))


def resumen(res: dict) -> str:
    if res.get("modo") != "suma":
        return "Respaldo aplicado. Las ventas de hoy se volvieron a cargar encima."
    lineas = [f"• {t}: {v['sumadas']} agregadas" for t, v in res.get("tablas", {}).items() if v["sumadas"]]
    texto = "Se agregó lo que faltaba:\n" + "\n".join(lineas) if lineas else "La tienda ya tenía todo lo de esta copia."
    if res.get("renumeradas"):
        texto += f"\n\n{res['renumeradas']} ventas chocaban de número con otras y entraron con número nuevo."
    if res.get("sin_lugar"):
        texto += "\n\nNo están en la tienda (no se sumaron): " + ", ".join(res["sin_lugar"])
    return texto


class DialogoRestaurar(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Restaurar la tienda")
        self.setMinimumSize(780, 540)
        self.setStyleSheet("QDialog { background: white; font-family: 'Segoe UI'; } QLabel { border: none; }")
        self.destino = None
        self.fuentes = []
        self._hilos = []
        self._build()
        self._buscar_en_pc()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)

        tit = QLabel("Restaurar la tienda")
        tit.setStyleSheet("font-size: 20px; font-weight: bold; color: #0F172A;")
        lay.addWidget(tit)
        desc = QLabel(
            "Sirve cualquier copia: los respaldos de Mantenimiento o el pendrive del jefe. "
            "Elegí una carpeta y queda marcada la más nueva; si querés otra, tocála."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; color: #475569;")
        lay.addWidget(desc)

        fila = QHBoxLayout()
        for texto, accion in (
            ("Copias de esta PC", self._buscar_en_pc),
            ("Elegir carpeta o pendrive…", self._elegir_carpeta),
            ("Elegir archivo…", self._elegir_archivo),
        ):
            b = QPushButton(texto)
            b.setStyleSheet(BTN)
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.clicked.connect(accion)
            fila.addWidget(b)
        fila.addStretch()
        lay.addLayout(fila)

        self.lbl_lugar = QLabel("")
        self.lbl_lugar.setStyleSheet("font-size: 12px; color: #64748B;")
        self.lbl_lugar.setWordWrap(True)
        lay.addWidget(self.lbl_lugar)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Datos al", "Qué es", "Tablas", "Archivo"])
        self.tabla.setStyleSheet(TABLA)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setTextElideMode(Qt.TextElideMode.ElideMiddle)
        self.tabla.setWordWrap(False)
        cab = self.tabla.horizontalHeader()
        cab.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        cab.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tabla.itemSelectionChanged.connect(self._al_elegir)
        lay.addWidget(self.tabla, 1)

        self.lbl_avisos = QLabel("")
        self.lbl_avisos.setWordWrap(True)
        self.lbl_avisos.hide()
        lay.addWidget(self.lbl_avisos)

        abajo = QHBoxLayout()
        self.lbl_estado = QLabel("")
        self.lbl_estado.setStyleSheet("font-size: 12px; color: #475569;")
        abajo.addWidget(self.lbl_estado, 1)
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setStyleSheet(BTN)
        self.btn_cerrar.clicked.connect(self.reject)
        abajo.addWidget(self.btn_cerrar)
        self.btn_ok = QPushButton("Restaurar la marcada")
        self.btn_ok.setStyleSheet(BTN_OK)
        self.btn_ok.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self._restaurar)
        abajo.addWidget(self.btn_ok)
        lay.addLayout(abajo)

    def _buscar_en_pc(self):
        from src.base_de_datos.restaurar import lugares_de_esta_pc

        self._buscar(lugares_de_esta_pc(), "Respaldos de esta PC, su copia de la tienda y el pendrive configurado.")

    def _elegir_carpeta(self):
        carpeta = QFileDialog.getExistingDirectory(self, "Carpeta de respaldos o pendrive del jefe")
        if carpeta:
            self._buscar([carpeta], carpeta)

    def _elegir_archivo(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Elegir copia", "", "Copias de la tienda (*.sql *.zip *.db);;Todos (*.*)"
        )
        if archivo:
            self._buscar([archivo], archivo)

    def _buscar(self, rutas: list[str], lugar: str):
        self.lbl_lugar.setText(f"Buscando en: {lugar}")
        self.tabla.setRowCount(0)
        self.btn_ok.setEnabled(False)
        self.lbl_avisos.hide()
        hilo = _Busqueda(rutas, self)
        hilo.listo.connect(lambda d, f, e: self._mostrar(d, f, e, lugar))
        self._hilos.append(hilo)
        hilo.start()

    def _mostrar(self, destino, fuentes: list, error: str, lugar: str):
        self.destino, self.fuentes = destino, fuentes
        self.lbl_lugar.setText(f"Buscado en: {lugar}")
        self.tabla.setRowCount(len(fuentes))
        for i, f in enumerate(fuentes):
            tipo = f.etiqueta + (f" · {f.detalle}" if f.detalle else "")
            if f.tipo == "copia" and not f.completa:
                tipo += " · parcial"
            celdas = (f"{f.fecha:%d/%m/%Y %H:%M}", tipo, str(f.tablas or "—"), f.ruta)
            for j, texto in enumerate(celdas):
                item = QTableWidgetItem(texto)
                item.setToolTip(f.ruta)
                self.tabla.setItem(i, j, item)
        if error:
            self._pintar_avisos([error], [])
        if not fuentes:
            self.lbl_estado.setText("No se encontraron copias de la tienda acá.")
            return
        self.lbl_estado.setText(f"{len(fuentes)} copias. Marcada: la más nueva.")
        self.tabla.selectRow(0)

    def _elegida(self):
        filas = self.tabla.selectionModel().selectedRows()
        if not filas or filas[0].row() >= len(self.fuentes):
            return None
        return self.fuentes[filas[0].row()]

    def _pintar_avisos(self, bloqueos: list[str], avisos: list[str]):
        self.lbl_avisos.setText("\n".join(f"• {t}" for t in bloqueos + avisos))
        self.lbl_avisos.setStyleSheet(BLOQUEO if bloqueos else AVISO)
        self.lbl_avisos.setVisible(bool(bloqueos or avisos))

    def _al_elegir(self):
        fuente = self._elegida()
        if fuente is None or self.destino is None:
            self.btn_ok.setEnabled(False)
            return
        from src.base_de_datos.restaurar import revisar

        bloqueos, avisos = revisar(fuente, self.destino)
        self._pintar_avisos(bloqueos, avisos)
        self.btn_ok.setEnabled(not bloqueos)

    def _restaurar(self):
        fuente = self._elegida()
        if fuente is None or self.destino is None:
            return
        pwd, ok = QInputDialog.getText(
            self, "Acceso restringido", "Contraseña de Super User (Jefe) para restaurar:", QLineEdit.EchoMode.Password
        )
        if not ok:
            return
        if pwd not in (CLAVE_RED, CLAVE_JEFE):
            QMessageBox.critical(self, "Acceso denegado", "Contraseña incorrecta. Solo el jefe puede restaurar.")
            return
        from src.base_de_datos.restaurar import revisar

        _, avisos = revisar(fuente, self.destino)
        destino = self.destino.host or self.destino.archivo
        texto = (
            f"Copia: {fuente.nombre}\nDatos al {fuente.fecha:%d/%m/%Y %H:%M}\nTienda: {destino}\n\n"
            + "\n".join(f"• {a}" for a in avisos)
            + "\n\n¿Restaurar?"
        )
        if QMessageBox.question(
            self, "Confirmar", texto, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) != QMessageBox.StandardButton.Yes:
            return
        for b in (self.btn_ok, self.btn_cerrar):
            b.setEnabled(False)
        self.tabla.setEnabled(False)
        hilo = _Trabajo(fuente, self.destino, self)
        hilo.avance.connect(lambda p, t: self.lbl_estado.setText(f"{p}% · {t}"))
        hilo.listo.connect(self._terminado)
        hilo.fallo.connect(self._fallo)
        self._hilos.append(hilo)
        hilo.start()

    def _liberar(self):
        self.btn_cerrar.setEnabled(True)
        self.tabla.setEnabled(True)
        self._al_elegir()

    def _terminado(self, res: dict):
        self._liberar()
        self.lbl_estado.setText("Restauración terminada.")
        QMessageBox.information(
            self, "Listo", resumen(res) + "\n\nReiniciá el programa en todas las PCs para ver los datos."
        )

    def _fallo(self, error: str):
        self._liberar()
        self.lbl_estado.setText("No se restauró.")
        QMessageBox.critical(
            self,
            "No se restauró",
            f"{error}\n\nUna copia del jefe no deja nada a medias. Si falló un respaldo, "
            "la foto de la tienda de antes quedó en los respaldos como pre_restore_….",
        )

    def reject(self):
        if any(h.isRunning() for h in self._hilos if isinstance(h, _Trabajo)):
            return
        for h in self._hilos:
            h.wait(15000)
        super().reject()
