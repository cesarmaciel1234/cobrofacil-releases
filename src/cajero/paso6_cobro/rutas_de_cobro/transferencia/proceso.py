def salir(ventana):
    alias = getattr(ventana, "panel_alias", None)
    if alias is not None and hasattr(alias, "ocultar"):
        try:
            alias.ocultar()
        except Exception:
            pass
    estado = getattr(ventana, "lbl_mp_status", None)
    if estado is not None:
        estado.hide()
    aviso = getattr(ventana, "btn_aviso_mp", None)
    if aviso is not None:
        aviso.hide()


def entrar(ventana):
    ventana.stack.setCurrentIndex(1)
    ventana.set_metodo("Transferencia")
