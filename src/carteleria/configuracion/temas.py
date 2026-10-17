"""Claves de vestuario que elige Admin y que carga la TV."""

TEMAS_TV = (
    ("apple", "Tema Elegante (Apple Style)"),
    ("temu", "Tema Temu (Vende Humo)"),
    ("premium", "Tema Premium Mutación (Oro + Naranja + Cian)"),
    ("black", "Black Super Premium (Oro y Plata)"),
    ("blackfriday", "Black Friday (Negro y Naranja)"),
)

ALIAS_TEMA = {"negro_temu": "premium", "auto": "premium"}
TEMA_DEFECTO = "premium"


def clave_tema(valor) -> str:
    clave = str(valor or TEMA_DEFECTO)
    return ALIAS_TEMA.get(clave, clave)
