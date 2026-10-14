"""Qué medio es el ticket: digital (firma MP), cuenta/DNI, u otro."""


def clase(metodo: str) -> str:
    m = (metodo or "").upper().replace("É", "E")
    if any(x in m for x in ("CLIENTES", "FIADO", "MASCREDITO", "CTA CTE", "CUENTA CORRIENTE")):
        return "cuenta"
    if "EFECTIVO" in m:
        return "efectivo"
    if any(x in m for x in ("QR", "TARJETA", "TRANSFER", "POINT", "MERCADOPAGO", "DEBITO")):
        return "digital"
    if "CREDITO" in m:
        return "digital"
    if m == "MP" or m.startswith("MP ") or " MP" in m:
        return "digital"
    return "otro"
