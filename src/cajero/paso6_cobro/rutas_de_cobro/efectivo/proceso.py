def salir(ventana):
    pago = getattr(ventana, "txt_pago", None)
    if pago is not None:
        try:
            pago.setReadOnly(False)
            pago.clear()
        except Exception:
            pass
    vuelto = getattr(ventana, "resumen_vuelto", None)
    if vuelto is not None:
        vuelto.hide()
    aviso = getattr(ventana, "aviso_monto", None)
    if aviso is not None:
        aviso.hide()


def entrar(ventana):
    ventana.stack.setCurrentIndex(1)
    ventana.set_metodo("Efectivo")
