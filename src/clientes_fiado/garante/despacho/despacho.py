def entregar(orden, datos):
    """Manda la orden ok al comando de cobro. No abre el Point, ni el QR, ni la transferencia."""
    if orden is None or not orden.ok:
        motivo = getattr(orden, "motivo", None) or "El fiado no autorizó el cobro."
        return False, motivo
    payload = dict(datos or {})
    payload["metodo"] = orden.metodo
    payload["cliente_id"] = orden.cliente_id
    from src.cajero.paso6_cobro.motor_pagos.motores._comun import ejecutar_comun

    return ejecutar_comun(payload)
