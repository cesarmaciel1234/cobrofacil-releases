from src.cajero.paso6_cobro.motor_pagos.motores._comun import ejecutar_comun


class MotorMixto:
    def ejecutar(self, datos):
        from src.utils.dinero import redondear_dinero

        datos = dict(datos)
        parte = redondear_dinero(datos.get("fiado_parcial") or 0)
        
        datos["metodo"] = "Mixto (Cliente)" if parte > 0.009 else "Mixto"
        
        if parte > 0.009:
            from src.clientes_fiado.cerebro.cerebro import cerebro

            cid = datos.get("cliente_id")
            if not cid:
                return False, "Falta el cliente para el resto a cuenta."
            orden = cerebro.autorizar("Clientes", cid, parte)
            if not orden.ok:
                return False, orden.motivo or "La cuenta no autorizó ese resto."
            datos["excepcion"] = getattr(orden, "excepcion", "") or ""
        return ejecutar_comun(datos)
