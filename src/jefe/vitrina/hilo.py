"""Números de la vitrina fuera de la ventana. La cara solo pinta."""

from PyQt6.QtCore import QThread, pyqtSignal


def _aud_vacio():
    return {
        "digitales_sin_firma": 0,
        "digitales_total": 0,
        "cuenta_dni": 0,
        "mp_sin_ticket": 0,
        "sin_ticket_monto": 0.0,
        "tickets_digitales": 0.0,
        "firmados": 0.0,
        "sin_firmar_monto": 0.0,
        "cliente": 0.0,
        "bruto": 0.0,
    }


def paquete(desde, hasta) -> dict:
    """Todo lo que pinta la vitrina. No toca widgets. Si una cuenta falla, esa queda en cero."""
    from src.jefe.nodo_portable.espejo import en_copia, leyenda
    from src.jefe.vitrina import metricas

    datos = {
        "origen": "",
        "ganancia": None,
        "inventario": 0.0,
        "pagos": 0.0,
        "deuda": 0.0,
        "redondeo": 0.0,
        "descuento": 0.0,
        "aud": _aud_vacio(),
        "tickets": (0, 0.0),
        "cancel": {"cant": 0, "monto": 0.0, "cuando": "", "usuario": ""},
    }
    try:
        datos["origen"] = leyenda()
    except Exception:
        pass
    try:
        datos["ganancia"] = metricas.ganancia(desde, hasta)
    except Exception:
        pass
    try:
        datos["inventario"] = metricas.inventario_costo()
    except Exception:
        pass
    try:
        datos["pagos"] = metricas.pagos_clientes(desde, hasta)
    except Exception:
        pass
    try:
        if en_copia():
            datos["deuda"] = metricas.deuda_clientes()
        else:
            from src.clientes_fiado.cerebro.cerebro import cerebro

            _pagos, deuda = cerebro.resumen_cuentas()
            datos["deuda"] = deuda
    except Exception:
        try:
            datos["deuda"] = metricas.deuda_clientes()
        except Exception:
            pass
    try:
        datos["redondeo"], datos["descuento"] = metricas.redondeo_y_descuento(desde, hasta)
    except Exception:
        pass
    try:
        datos["aud"] = metricas.cobros_auditoria(desde, hasta)
    except Exception:
        pass
    try:
        datos["tickets"] = metricas.tickets(desde, hasta)
    except Exception:
        pass
    try:
        datos["cancel"] = metricas.cancelaciones(desde, hasta)
    except Exception:
        pass
    return datos


class HiloVitrina(QThread):
    """Una vuelta. `listo` trae la generación y el paquete."""

    listo = pyqtSignal(int, object)

    def __init__(self, generacion: int, desde: str, hasta: str, parent=None):
        super().__init__(parent)
        self._generacion = int(generacion)
        self._desde = desde
        self._hasta = hasta

    def run(self):
        self.listo.emit(self._generacion, paquete(self._desde, self._hasta))
