_ALIAS = {
    "kg": "kilo",
    "kgs": "kilo",
    "kilo": "kilo",
    "kilos": "kilo",
    "kilogramo": "kilo",
    "kilogramos": "kilo",
    "peso": "kilo",
    "pesable": "kilo",
    "g": "gramo",
    "gr": "gramo",
    "gramo": "gramo",
    "gramos": "gramo",
    "l": "litro",
    "lt": "litro",
    "lts": "litro",
    "litro": "litro",
    "litros": "litro",
    "ml": "litro",
    "m": "metro",
    "mt": "metro",
    "mts": "metro",
    "metro": "metro",
    "metros": "metro",
    "cm": "metro",
    "un": "unidad",
    "u": "unidad",
    "ud": "unidad",
    "uds": "unidad",
    "unidad": "unidad",
    "unidades": "unidad",
    "pza": "unidad",
    "pieza": "unidad",
    "piezas": "unidad",
    "pack": "pack",
    "paq": "pack",
    "paquete": "pack",
    "docena": "docena",
    "docenas": "docena",
}


def normalizar_unidad(texto) -> str:
    raw = str(texto or "").strip().lower()
    if not raw:
        return ""
    compacto = raw.replace(".", "").replace(" ", "")
    if compacto in _ALIAS:
        return _ALIAS[compacto]
    for clave, dest in _ALIAS.items():
        if clave in raw:
            return dest
    return raw
