"""Consola del proceso `--server`. Muestra el log en vivo, en el hilo de la ventana."""

from __future__ import annotations

import html
import logging
from datetime import datetime

from PyQt6.QtCore import QObject, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor
from PyQt6.QtWidgets import QTextEdit

_TOPE = 400
_ENGANCHADA = False


class _Senal(QObject):
    lista = pyqtSignal(int, str)


class _Puente(logging.Handler):
    def __init__(self, senal: _Senal):
        super().__init__(level=logging.INFO)
        self.senal = senal

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.senal.lista.emit(record.levelno, record.getMessage())
        except Exception:
            pass


class ConsolaViva(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setUndoRedoEnabled(False)
        fuente = QFont("Consolas", 10)
        fuente.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(fuente)
        self.setObjectName("ConsolaServidor")
        self._base = ""
        self._visible = ""
        self._n = 0
        self._inicio = None
        self._senal = _Senal(self)
        self._senal.lista.connect(self._recibir)

    def escribir(self, texto: str, nivel: int = logging.INFO, con_hora: bool = False) -> None:
        self._recibir(nivel, texto, con_hora)

    def limpiar(self) -> None:
        self.clear()
        self._base = ""
        self._visible = ""
        self._n = 0
        self._inicio = None

    def enganchar(self) -> None:
        """Una sola vez por proceso. El log de cualquier hilo llega acá."""
        global _ENGANCHADA
        if _ENGANCHADA:
            return
        _ENGANCHADA = True
        puente = _Puente(self._senal)
        puente.setFormatter(
            logging.Formatter(
                "%(asctime)s  %(levelname)-5s  %(name)s  %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        raiz = logging.getLogger()
        if raiz.level == logging.NOTSET or raiz.level > logging.INFO:
            raiz.setLevel(logging.INFO)
        raiz.addHandler(puente)

    def _color(self, nivel: int) -> str:
        if nivel >= logging.ERROR:
            return "#FCA5A5"
        if nivel >= logging.WARNING:
            return "#FCD34D"
        return "#86EFAC"

    def _recibir(self, nivel: int, texto: str, con_hora: bool = False) -> None:
        texto = " ".join(str(texto).split())
        if not texto:
            return
        if texto == self._base:
            self._n += 1
            self._poner(self._visible, nivel, self._n, reescribir=True)
            return
        self._base = texto
        self._n = 1
        hora = datetime.now().strftime("%H:%M:%S  ") if con_hora else ""
        self._visible = hora + texto
        self._poner(self._visible, nivel, 1, reescribir=False)
        self._recortar()

    def _poner(self, texto: str, nivel: int, n: int, reescribir: bool) -> None:
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if reescribir and self._inicio is not None:
            cursor.setPosition(self._inicio, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        self._inicio = cursor.position()
        color = self._color(nivel)
        seguro = html.escape(texto)
        cursor.insertHtml(f'<span style="color:{color};">{seguro}</span>')
        if n > 1:
            cursor.insertHtml(f'<span style="color:#64748B;">  ×{n}</span>')
        cursor.insertBlock()
        self.setTextCursor(cursor)
        self.ensureCursorVisible()

    def _recortar(self) -> None:
        doc = self.document()
        while doc.blockCount() > _TOPE:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()
            self._inicio = None
