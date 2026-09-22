import logging

from src.cajero.paso6_cobro.componentes_paso6_cobro.logica.cobro_controller import CobroController

logger = logging.getLogger(__name__)


def post_cobro(datos, id_v, resultado_venta):
    descuento_total = float(datos.get("descuento") or 0) + float(datos.get("oferta") or 0)
    CobroController.procesar_cajon_impresion(
        datos.get("metodo"),
        datos.get("imprimir", True),
        id_v,
        datos.get("items_carrito") or [],
        datos.get("total_final"),
        resultado_venta,
        datos.get("cajero") or "",
        descuento_total,
        datos.get("recargo") or 0,
        datos.get("force_fiscal", False),
    )
    try:
        from src.base_de_datos.diario_ventas_externo import encolar_venta

        encolar_venta(id_v, resultado_venta, datos.get("items_carrito") or [])
    except Exception as e:
        logger.warning("No se encolo la venta %s en diario externo: %s", id_v, e)
