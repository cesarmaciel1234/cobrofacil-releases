"""
Motor de Procesamiento de Códigos de Barras y Balanzas Comerciales
Extraído de paso5_terminal.py para aislar la lógica de negocio.
"""
from src.config import config

class BarcodeParser:
    @staticmethod
    def _normalize_ean13(txt: str) -> str:
        """EAN-13 de balanza; algunos lectores envían 12 dígitos (UPC-A sin cero)."""
        if len(txt) == 12 and txt.isdigit():
            return txt[:2] + "0" + txt[2:]
        return txt

    @staticmethod
    def is_balanza_ean(txt: str) -> bool:
        txt = BarcodeParser._normalize_ean13(txt.strip())
        if not (len(txt) == 13 and txt.isdigit() and config.get("balanza_habilitada", True)):
            return False
        prefijo_balanza = str(config.get("balanza_prefijo", "20"))
        tipo = txt[:2]
        return txt.startswith(prefijo_balanza) or tipo in ("21", "22")

    @staticmethod
    def extract_plu_from_barcode(txt: str) -> tuple[str, str]:
        """Devuelve (plu_con_ceros, plu_sin_ceros) según config de balanza."""
        txt = BarcodeParser._normalize_ean13(txt.strip())
        p_start = max(0, int(config.get("balanza_plu_inicio", 3)) - 1)
        p_len = int(config.get("balanza_plu_largo", 5))
        plu = txt[p_start: p_start + p_len]
        plu_limpio = plu.lstrip("0") or "0"
        return plu, plu_limpio

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
        Retorna (plu_sin_ceros, cantidad). Prefijos:
          20 / config → peso o importe (según balanza_modo)
          21 → unidades (piezas)
          22 → importe total en etiqueta de unidad
        """
        txt = BarcodeParser._normalize_ean13(txt.strip())
        if not BarcodeParser.is_balanza_ean(txt):
            return None, None

        try:
            plu, plu_limpio = BarcodeParser.extract_plu_from_barcode(txt)

            v_start = max(0, int(config.get("balanza_val_inicio", 8)) - 1)
            v_len = int(config.get("balanza_val_largo", 5))
            v_raw = txt[v_start: v_start + v_len]

            modo = config.get("balanza_modo", "Importe Total ($)")
            divisor = int(config.get("balanza_divisor", 1000))
            tipo = txt[:2]

            if tipo == "21":
                # Unidades: entero directo; si viene 00000, algunas balanzas usan divisor (1 u = 1000)
                qty_int = int(v_raw)
                if qty_int > 0:
                    cantidad = float(qty_int)
                else:
                    cantidad = float(v_raw) / divisor
                    if cantidad <= 0:
                        cantidad = 1.0
            elif tipo == "22":
                # Importe total impreso en etiqueta de producto por unidad
                valor_numerico = float(v_raw) / divisor
                if precio_unitario > 0 and valor_numerico > 0:
                    cantidad = valor_numerico / precio_unitario
                else:
                    cantidad = 1.0
            else:
                valor_numerico = float(v_raw) / divisor
                if "Importe" in modo:
                    if precio_unitario > 0:
                        cantidad = valor_numerico / precio_unitario
                    else:
                        cantidad = 1.0
                else:
                    cantidad = valor_numerico

            if cantidad <= 0:
                cantidad = 1.0

            return plu_limpio, cantidad
        except (ValueError, IndexError):
            return None, None
