"""Tres tarjetas arriba y dos abajo. El orden de esta lista es el dibujo."""

ARRIBA = ("Efectivo", "Tarjeta", "Transferencia")
ABAJO = ("QR", "Mixto")

METODOS = (
    ("💰", "Efectivo", "Efectivo"),
    ("💳", "Crédito", "Tarjeta"),
    ("🏦", "Transf.", "Transferencia"),
    ("📱", "QR", "QR"),
    ("🔀", "Mixto", "Mixto"),
)


def es_de_arriba(indice):
    return indice < len(ARRIBA)
