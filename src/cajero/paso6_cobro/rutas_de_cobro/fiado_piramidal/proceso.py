def salir(ventana):
    panel = getattr(ventana, "panel_fiado", None)
    if panel is None:
        return
    if hasattr(panel, "reiniciar"):
        try:
            panel.reiniciar()
            return
        except Exception:
            pass
    if hasattr(panel, "ocultar"):
        try:
            panel.ocultar()
        except Exception:
            pass


def entrar(ventana, modo="Clientes"):
    ventana.stack.setCurrentIndex(1)
    if modo == "Fiado":
        ventana._activar_fiado_express()
    else:
        ventana._activar_cliente_express()
