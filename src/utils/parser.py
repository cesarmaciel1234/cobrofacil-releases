def parse_float_regional(val_str):
    """
    Parses a string representing a float with potential regional formatting
    (dots or commas as thousands/decimal separators) into a Python float.
    """
    if val_str is None:
        return 0.0
    val_str = str(val_str).strip().replace("$", "").replace(" ", "")
    if not val_str:
        return 0.0
        
    # Caso 1: Tiene tanto puntos como comas (ej: 1.500,50 o 1,500.50)
    if "." in val_str and "," in val_str:
        if val_str.rfind(".") < val_str.rfind(","):
            # Formato local: 1.500,50 -> Quitar puntos, cambiar coma por punto
            val_str = val_str.replace(".", "").replace(",", ".")
        else:
            # Formato estándar/US: 1,500.50 -> Quitar comas
            val_str = val_str.replace(",", "")
            
    # Caso 2: Solo tiene comas (ej: 1500,50 o 1,500)
    elif "," in val_str:
        parts = val_str.split(",")
        if len(parts) == 2 and len(parts[1]) == 3:
            # Si son exactamente 3 dígitos al final (ej: 1,500 o 12,500), probablemente es miles
            if len(parts[0]) <= 3:
                val_str = val_str.replace(",", "")
            else:
                val_str = val_str.replace(",", ".")
        else:
            val_str = val_str.replace(",", ".")
            
    # Caso 3: Solo tiene puntos (ej: 1500.50 o 1.500)
    elif "." in val_str:
        parts = val_str.split(".")
        if len(parts) == 2 and len(parts[1]) == 3:
            if len(parts[0]) <= 3:
                val_str = val_str.replace(".", "")
                
    try:
        return float(val_str)
    except ValueError:
        return 0.0
