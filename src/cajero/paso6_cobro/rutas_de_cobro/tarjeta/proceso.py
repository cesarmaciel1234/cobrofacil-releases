def salir(ventana):
    panel = getattr(ventana, "panel_tarjeta", None)
    if panel is not None and hasattr(panel, "ocultar"):
        try:
            panel.ocultar()
        except Exception:
            pass


def entrar(ventana):
    ventana.stack.setCurrentIndex(1)
    ventana.set_metodo("Tarjeta")
