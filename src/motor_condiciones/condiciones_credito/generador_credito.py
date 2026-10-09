def generar_texto(subcontexto: str = "", saldo_anterior: float = 0.0, monto_actual: float = 0.0, **kwargs) -> str:
    if subcontexto == "abono":
        return f"ABONO A CUENTA. Saldo anterior: ${saldo_anterior:.2f}. Monto abonado: ${monto_actual:.2f}. Nuevo saldo: ${(saldo_anterior - monto_actual):.2f}. Conserve este ticket como comprobante de pago."
    elif subcontexto == "estado_cuenta":
        return f"ESTADO DE CUENTA. Saldo adeudado: ${saldo_anterior:.2f}. Favor de realizar su pago a la brevedad."
    else: # Venta a crédito
        return f"VENTA A CREDITO. Pagaré incondicional por la cantidad de ${monto_actual:.2f}. El cliente acepta los cargos y condiciones de crédito de la tienda."
