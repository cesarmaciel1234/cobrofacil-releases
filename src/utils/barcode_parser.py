"""
Motor de Procesamiento de Códigos de Barras y Balanzas Comerciales
Extraído de paso5_terminal.py para aislar la lógica de negocio.
"""
from src.config import config

class BarcodeParser:
    @staticmethod
    def parse_scan_text(txt_raw: str):
        """
        Analiza el texto escaneado y extrae multiplicadores (ej. 5*123) 
        y el código limpio.
        """
        txt = txt_raw.strip()
        cantidad_multiplicador = 1.0
        
        if not txt:
            return None, 1.0

        if '*' in txt:
            partes = txt.split('*', 1)
            try:
                cantidad_multiplicador = float(partes[0].replace(',', '.'))
                txt = partes[1].strip()
                if not txt: 
                    return None, cantidad_multiplicador
            except ValueError:
                pass
                
        return txt, cantidad_multiplicador

    @staticmethod
    def try_parse_manual_item(txt: str):
        """
        Lógica PRO: Artículo Común intencional usando el prefijo '+'
        Retorna (dict_producto, True) si fue exitoso, o (None, False).
        """
        if txt.startswith('+'):
            try:
                precio_manual = float(txt[1:].replace(',', '.'))
                p = {"id": "000", "nombre": "ARTICULO COMUN", "precio": precio_manual}
                return p, True
            except ValueError:
                return None, False
        return None, False

    @staticmethod
    def parse_balanza_code(txt: str, precio_unitario: float):
        """
        Lógica PRO: Analiza códigos de barras generados por balanzas comerciales (Systel, Kretz, etc.)
        Retorna la cantidad final (peso o importe calculado) basándose en la configuración.
        """
        if not (len(txt) in [12, 13] and txt.isdigit() and config.get("balanza_habilitada", True)):
            return None, None

        prefijo_balanza = str(config.get("balanza_prefijo", "20"))
        is_balanza = txt.startswith(prefijo_balanza) or txt.startswith("21")
        
        if not is_balanza:
            return None, None

        try:
            # Si el código tiene 12 dígitos, suele ser un UPC-A donde se omitió el 0 a la izquierda del PLU.
            # Lo normalizamos a 13 para que la configuración de la balanza (índices) funcione perfecto.
            if len(txt) == 12:
                txt = txt[:2] + "0" + txt[2:]
                
            # Extraer PLU
            p_start = max(0, int(config.get("balanza_plu_inicio", 3)) - 1)
            p_len   = int(config.get("balanza_plu_largo", 5))
            plu     = txt[p_start : p_start + p_len]
            plu_limpio = plu.lstrip('0') or '0'
            
            # Extraer Valor
            v_start = max(0, int(config.get("balanza_val_inicio", 8)) - 1)
            v_len   = int(config.get("balanza_val_largo", 5))
            v_raw   = txt[v_start : v_start + v_len]
            
            modo = config.get("balanza_modo", "Importe Total ($)")
            divisor = int(config.get("balanza_divisor", 1000))
            
            if txt.startswith("21"):
                # MODO UNIDADES: El valor es la cantidad de piezas (ej: 00001 = 1 unidad)
                cantidad = float(int(v_raw))
            else:
                # MODO BALANZA (PESO O IMPORTE)
                valor_numerico = float(v_raw) / divisor
                if "Importe" in modo:
                    if precio_unitario > 0:
                        cantidad = valor_numerico / precio_unitario
                    else:
                        cantidad = 1.0 # Fallback
                else:
                    # Modo Peso
                    cantidad = valor_numerico
                    
            return plu_limpio, cantidad
        except (ValueError, IndexError):
            return None, None
