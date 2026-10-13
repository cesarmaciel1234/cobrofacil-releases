"""Vuelta limpia a la grilla de medios. Sin MariaDB, sin recargar config, sin Point nuevo."""

from src.cajero.paso6_cobro.componentes_paso6_cobro.selector_metodo_pago.marco.marcar import (
    marcar_tarjeta,
)


def salir_a_metodos(ventana):
    if getattr(ventana, "_saliendo_a_metodos", False):
        return
    ventana._saliendo_a_metodos = True
    try:
        _parar_relojes(ventana)
        _soltar_point(ventana)
        from src.cajero.paso6_cobro.rutas_de_cobro.efectivo.proceso import salir as salir_efectivo
        from src.cajero.paso6_cobro.rutas_de_cobro.tarjeta.proceso import salir as salir_tarjeta
        from src.cajero.paso6_cobro.rutas_de_cobro.qr.proceso import salir as salir_qr
        from src.cajero.paso6_cobro.rutas_de_cobro.transferencia.proceso import salir as salir_transferencia
        from src.cajero.paso6_cobro.rutas_de_cobro.mixto.proceso import salir as salir_mixto
        from src.cajero.paso6_cobro.rutas_de_cobro.fiado_piramidal.proceso import salir as salir_credito

        salir_efectivo(ventana)
        salir_tarjeta(ventana)
        salir_qr(ventana)
        salir_transferencia(ventana)
        salir_mixto(ventana)
        salir_credito(ventana)

        ventana._fiado_flujo_activo = False
        ventana._fiado_cliente_id = None
        ventana._submetodo_cobranza = ""
        ventana._mixto_pasos = None
        ventana._mixto_confirmado = False
        ventana._mixto_espera_transferencia = None
        ventana._mixto_esperando_qr = False
        ventana._mixto_espera_cuenta = False
        ventana._ticket_al_pagar = None
        ventana._point_en_curso = False

        marcar_tarjeta(ventana, "Efectivo")
        if getattr(ventana, "stack", None) is not None:
            ventana.stack.setCurrentIndex(0)
        ventana.setFocus()
    finally:
        ventana._saliendo_a_metodos = False


def _parar_relojes(ventana):
    for nombre in ("timer_mp", "timer_spinner", "_qr_monto_timer", "_tarjeta_monto_timer"):
        reloj = getattr(ventana, nombre, None)
        if reloj is None:
            continue
        try:
            reloj.stop()
        except Exception:
            pass
    toast = getattr(ventana, "aviso_toast", None)
    if toast is not None:
        try:
            toast.cerrar()
        except Exception:
            pass


def _soltar_point(ventana):
    espera = getattr(ventana, "espera_point", None)
    if espera is None:
        return
    try:
        espera.soltar()
    except Exception:
        pass
