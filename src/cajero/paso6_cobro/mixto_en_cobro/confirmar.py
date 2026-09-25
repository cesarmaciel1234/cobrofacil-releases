from src.utils.dinero import redondear_dinero


def pasos_vivos(valores):
    """Lo que hay que cobrar en vivo, en orden. El efectivo no tiene paso."""
    pasos = []
    tarjeta = redondear_dinero((valores or {}).get("tarjeta") or 0)
    transferencia = redondear_dinero((valores or {}).get("mercadopago") or 0)
    qr = redondear_dinero((valores or {}).get("qr") or 0)
    if tarjeta > 0.009:
        pasos.append(("tarjeta", tarjeta))
    if transferencia > 0.009:
        pasos.append(("transferencia", transferencia))
    if qr > 0.009:
        pasos.append(("qr", qr))
    return pasos
