import threading
from src.cajero.paso6_cobro.motor_pagos.comandos.persistir_cobro import persistir_cobro
from src.cajero.paso6_cobro.motor_pagos.comandos.post_cobro import post_cobro
from src.cajero.paso6_cobro.motor_pagos.consultas.venta import carrito_valido


def ejecutar_comun(datos, extra_validar=None):
    if not carrito_valido(datos.get("items_carrito")):
        return False, "El carrito esta vacio."
    if extra_validar:
        err = extra_validar(datos)
        if err:
            return False, err
    id_v, resultado = persistir_cobro(datos)
    if not id_v:
        return False, (resultado or {}).get("error") or "Error al guardar la venta en la base de datos."
    if resultado.get("cliente_nombre"):
        datos["cliente_nombre"] = resultado["cliente_nombre"]
    threading.Thread(target=post_cobro, args=(datos, id_v, resultado), daemon=True).start()
    try:
        from src.notificaciones.motor.estado import publicar
        from src.hardware.cash_drawer import drawer_manager

        # Verificar si el cajón está realmente abierto (físicamente)
        cajon_realmente_abierto = drawer_manager.is_open

        # Mensaje con indicación REAL de cajón abierto
        if cajon_realmente_abierto:
            mensaje = f"✅ COBRO EXITOSO — ticket {id_v} · Cajón abierto"
        else:
            mensaje = f"✅ COBRO EXITOSO — ticket {id_v}"

        publicar("cobro_ok", mensaje, segundos=10)
    except Exception:
        pass
    return True, None
