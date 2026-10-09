# -*- coding: utf-8 -*-
def generar_texto(subcontexto: str = "", saldo_anterior: float = 0.0, monto_actual: float = 0.0, cliente_nombre: str = "", **kwargs) -> str:
    nombre = cliente_nombre if cliente_nombre else "Cliente"
    if subcontexto == "abono":
        nuevo_saldo = saldo_anterior - monto_actual
        if nuevo_saldo <= 0.01:
            return f"Hola {nombre}! Pagaste tu saldo pendiente y tu cuenta esta al dia. Muchas gracias por tu confianza! Conserva este ticket como comprobante de pago."
        else:
            return f"Hola {nombre}! Gracias por tu pago de ${monto_actual:.2f}. Tu nuevo saldo pendiente es de ${nuevo_saldo:.2f}. Conserva este ticket como comprobante."
    elif subcontexto == "estado_cuenta":
        if saldo_anterior <= 0.01:
            return f"Hola {nombre}! Tu cuenta esta al dia y no registras deuda. Gracias por elegirnos!"
        else:
            return f"Hola {nombre}! Te acercamos tu estado de cuenta. Actualmente tenes un saldo pendiente de ${saldo_anterior:.2f}. Te esperamos pronto!"
    else: # Venta a crédito
        return f"VENTA A CREDITO. Pagare incondicional por la cantidad de ${monto_actual:.2f}. El cliente acepta los cargos y condiciones de credito de la tienda."
