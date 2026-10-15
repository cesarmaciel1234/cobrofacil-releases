def salir(ventana):
    panel = getattr(ventana, "panel_mixto", None)
    if panel is not None:
        try:
            if hasattr(panel, "vaciar"):
                panel.vaciar()
            if hasattr(panel, "ocultar"):
                panel.ocultar()
        except Exception:
            pass
    ventana.valores_mixtos = None
    ventana._mixto_vivo_hecho = None
    ventana._mixto_pasos = None
    ventana._mixto_confirmado = False
    ventana._mixto_espera_cuenta = False
    ventana._mixto_esperando_qr = False
    ventana._mixto_espera_transferencia = None


def entrar(ventana):
    ventana.stack.setCurrentIndex(1)
    ventana.set_metodo("Mixto")
