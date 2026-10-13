def salir(ventana):
    panel = getattr(ventana, "panel_mixto", None)
    if panel is not None and hasattr(panel, "ocultar"):
        try:
            panel.ocultar()
        except Exception:
            pass
    ventana._mixto_pasos = None
    ventana._mixto_confirmado = False
    ventana._mixto_espera_cuenta = False
    ventana._mixto_esperando_qr = False


def entrar(ventana):
    ventana.stack.setCurrentIndex(1)
    ventana.set_metodo("Mixto")
