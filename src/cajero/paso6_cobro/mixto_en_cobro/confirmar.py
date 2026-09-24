def pasos_vivos(valores):
    """Lo que hay que cobrar en vivo, en orden. El efectivo no tiene paso."""
    pasos = []
    tarjeta = float((valores or {}).get("tarjeta") or 0)
    transferencia = float((valores or {}).get("mercadopago") or 0)
    qr = float((valores or {}).get("qr") or 0)
    if tarjeta > 0.009:
        pasos.append(("tarjeta", tarjeta))
    if transferencia > 0.009:
        pasos.append(("transferencia", transferencia))
    if qr > 0.009:
        pasos.append(("qr", qr))
    return pasos
