"""MariaDB fuera de la pantalla. Si se cae, el panel sigue."""

from __future__ import annotations

import logging

from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger("CarteleriaConfig")


class HiloCargar(QThread):
    listo = pyqtSignal(object)

    def run(self):
        try:
            from src.carteleria.configuracion.motor.cargar import leer_db

            datos = leer_db()
            logger.info("config TV: lectura DB %s", "ok" if datos else "vacia")
            self.listo.emit(datos)
        except Exception as exc:
            logger.warning("config TV: lectura DB falló: %s", exc)
            self.listo.emit(None)


class HiloGuardar(QThread):
    listo = pyqtSignal(bool, str)

    def __init__(self, datos: dict, parent=None):
        super().__init__(parent)
        self.datos = datos

    def run(self):
        try:
            from src.carteleria.configuracion.motor.guardar import persistir_db

            ok, err = persistir_db(self.datos)
            if ok:
                logger.info("config TV: guardado DB ok")
            else:
                logger.warning("config TV: guardado DB falló: %s", err)
            self.listo.emit(bool(ok), err or "")
        except Exception as exc:
            logger.warning("config TV: guardado DB falló: %s", exc)
            self.listo.emit(False, str(exc))
