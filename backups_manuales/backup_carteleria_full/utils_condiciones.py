import re

def formatear_condicion_oferta(regla_raw: str, is_temu: bool = False) -> str:
    """
    Motor centralizado para procesar y formatear la regla/condición de una oferta.
    Limpia tags HTML, omite mínimos absurdos y aplica copywriting comercial de forma unificada.
    
    Retorna el texto limpio de la condición, o un string vacío si debe ocultarse.
    """
    if not regla_raw:
        return ""
        
    # 1. Limpiar tags HTML (por si vienen del Sincronizador)
    r_str = str(regla_raw).strip()
    r_str = re.sub(r'<[^>]+>', '', r_str).strip()
    
    if not r_str:
        return ""
        
    # 2. Filtrar condiciones absurdas (mínimos muy bajos que no vale la pena mostrar)
    bad_words = ["0.1", "0,1", "0.0", "0,0", "100 gs", "150 gs", "100gs", "150gs"]
    if any(bad in r_str.lower() for bad in bad_words):
        return ""
        
    # 3. Limpieza y estandarización visual
    r_str = r_str.replace("0.5 Kilos", "500 gs").replace("0,5 Kilos", "500 gs").replace("0.25 Kilos", "250 gs").replace("0,25 Kilos", "250 gs")
    
    if not r_str:
        return ""
        
    # 4. Formateo inteligente / Copywriting
    r_lower = r_str.lower()
    has_suffix = any(s in r_lower for s in ["o mas", "o más", "o +", "+"])
    
    if r_lower.startswith("llevando") or r_lower.startswith("comprando"):
        if has_suffix:
            return f"Oferta válida {r_lower}"
        else:
            return f"Oferta válida {r_lower} o más"
            
    elif not r_lower.startswith("oferta") and not r_lower.startswith("válida") and not r_lower.startswith("condiciones"):
        return f"Condiciones: {r_str}"
        
    return r_str
