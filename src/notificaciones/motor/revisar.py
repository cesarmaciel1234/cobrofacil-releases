"""Elige un mensaje y el resto como lámparas. Si falla, no hay aviso."""

from src.notificaciones.motor.estado import vigentes_detalle

_URGENCIA = "🚨 URGENCIA ACTIVA — Venta permitida SIN STOCK"
_VACIO = {"mensaje": None, "iconos": []}
_ORDEN = ("cobro_cancelado", "cobro_ok", "cajon", "urgencia", "stock", "efectivo")


def revisar_notificaciones() -> dict:
    try:
        alertas = _alertas()
        if not alertas:
            return dict(_VACIO)
        mensaje = None
        iconos = []
        for alerta in alertas:
            if alerta["en_franja"] and mensaje is None:
                mensaje = alerta["texto"]
                continue
            iconos.append(
                {
                    "codigo": alerta["codigo"],
                    "nivel": alerta["nivel"],
                    "detalle": alerta["detalle"],
                }
            )
        return {"mensaje": mensaje, "iconos": iconos}
    except Exception:
        return dict(_VACIO)


def _alertas() -> list[dict]:
    vivos = {e["codigo"]: e for e in vigentes_detalle()}
    alertas = []
    if "cobro_cancelado" in vivos:
        alertas.append(_fila("cobro_cancelado", vivos["cobro_cancelado"]["texto"], "urgente", "Cobro cancelado", True))
    if "cobro_ok" in vivos:
        alertas.append(_fila("cobro_ok", vivos["cobro_ok"]["texto"], "ok", "Cobro exitoso", True))
    if "cajon" in vivos:
        alertas.append(_fila("cajon", "", "urgente", "Cajón abierto", False))
    urgencia = _urgencia()
    if urgencia:
        alertas.append(_fila("urgencia", "", "urgente", "Venta permitida sin stock", False))
    stock = _stock_critico()
    if stock:
        alertas.append(_fila("stock", "", "aviso", stock, False))
    efectivo = _efectivo()
    if efectivo:
        alertas.append(_fila("efectivo", "", efectivo["nivel"], efectivo["detalle"], False))
    alertas.sort(key=lambda a: _ORDEN.index(a["codigo"]))
    return alertas


def _fila(codigo: str, texto: str, nivel: str, detalle: str, en_franja: bool) -> dict:
    return {
        "codigo": codigo,
        "texto": texto,
        "nivel": nivel,
        "detalle": detalle,
        "en_franja": en_franja,
    }


def _urgencia() -> str | None:
    try:
        from src.config import config

        if config.get("opt_stock_negativo", False):
            return _URGENCIA
    except Exception:
        return None
    return None


def _stock_critico() -> str | None:
    try:
        from src.config import config

        if not config.get("stock_alerta_activa", True):
            return None
        from src.cajero.paso5_terminal.logica.stock_ofertas_service import StockOfertasService

        bajos = int(StockOfertasService().get_stock_critico_count() or 0)
        if bajos == 1:
            return "1 producto bajo el mínimo"
        if bajos > 1:
            return f"{bajos} productos bajo el mínimo"
    except Exception:
        return None
    return None


def _plata(valor) -> str:
    try:
        return f"${float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "$0,00"


def _efectivo() -> dict | None:
    try:
        from src.config import config
        from src.base_de_datos.database import db_manager

        caja_id = config.get("caja_id", 1)
        efectivo = float(db_manager.get_efectivo_en_caja(caja_id) or 0)
        rojo = float(config.get("limite_efectivo_rojo", 70000) or 70000)
        naranja = float(config.get("limite_efectivo_naranja", 50000) or 50000)
        monto = _plata(efectivo)
        if efectivo >= rojo:
            return {"nivel": "urgente", "detalle": f"Retiro urgente · {monto}"}
        if efectivo >= naranja:
            return {"nivel": "aviso", "detalle": f"Retiro de caja · {monto}"}
    except Exception:
        return None
    return None
