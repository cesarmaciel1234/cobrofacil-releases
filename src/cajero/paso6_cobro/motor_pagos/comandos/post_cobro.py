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
    pago = datos.get("mp_pago") or {}
    if pago.get("id"):
        try:
            from src.cajero.paso6_cobro.vinculo_mp.libro import asociar

            asociar(pago.get("id"), pago.get("monto"), id_v)
            from src.admin.mercadopago.mercadopago_main import Admin10MP

            vista = getattr(Admin10MP, "vista", None)
            if vista is not None:
                vista.cargar_datos_locales()
        except Exception as e:
            logger.warning("No se vinculo el pago MP %s: %s", pago.get("id"), e)
    try:
        from src.base_de_datos.diario_ventas_externo import encolar_venta

        encolar_venta(id_v, resultado_venta, datos.get("items_carrito") or [])
    except Exception as e:
        logger.warning("No se encolo la venta %s en diario externo: %s", id_v, e)
