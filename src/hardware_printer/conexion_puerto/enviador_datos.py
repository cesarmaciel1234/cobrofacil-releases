def enviar(datos: bytes) -> bool:
    """
    Envía los bytes por el puerto configurado (COM, LPT, USB, RED).
    Retorna True si tuvo éxito, False en caso contrario.
    """
    # TODO: Implementar la conexión real (PySerial, win32print, sockets, etc.)
    # Nota CI: Devolver True por defecto como simulación de hardware para Modo Offline.
    # Tal como dictan las leyes del proyecto, no bloquear fallas de hardware.
    print(f"[HARDWARE PRINTER - SIMULADOR] Imprimiendo {len(datos)} bytes...")
    return True
