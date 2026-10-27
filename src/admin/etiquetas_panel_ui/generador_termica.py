"""Generador industrial de etiquetas de góndola para impresora térmica (ESC/POS).

Diseñado específicamente para pequeños y medianos comercios (carnicerías, almacenes,
fiambrerías, minimarkets) que no disponen de impresora convencional A4 láser/tinta.
Permite imprimir etiquetas de estantería/vitrina directamente en la ticketera (58mm u 80mm)
con corte automático de papel por cada producto.
"""

from __future__ import annotations

import textwrap
from datetime import datetime

# Constantes ESC/POS estándar
ESC = b"\x1b"
GS = b"\x1d"

RESET = ESC + b"\x40"
CUT_PAPER = GS + b"\x56\x41\x00"  # Feed and full/partial cut

ALIGN_LEFT = ESC + b"\x61\x00"
ALIGN_CENTER = ESC + b"\x61\x01"
ALIGN_RIGHT = ESC + b"\x61\x02"

BOLD_ON = ESC + b"\x45\x01"
BOLD_OFF = ESC + b"\x45\x00"

DOUBLE_HW_ON = ESC + b"\x21\x30"   # Doble altura y doble ancho
DOUBLE_HW_OFF = ESC + b"\x21\x00"  # Tamaño normal

DOUBLE_HEIGHT_ON = ESC + b"\x21\x10"
DOUBLE_HEIGHT_OFF = ESC + b"\x21\x00"

CHICO_ON = ESC + b"\x21\x01"
CHICO_OFF = ESC + b"\x21\x00"

INVERT_ON = GS + b"\x42\x01"       # Blanco sobre negro (modo inverso)
INVERT_OFF = GS + b"\x42\x00"


def formatear_precio_argentino(monto: float | str) -> str:
    """Formatea el precio en formato visual limpio con separador de miles."""
    try:
        val = float(monto)
    except (TypeError, ValueError):
        val = 0.0

    # Si no tiene centavos significativos, mostrar redondeado o con dos decimales según convención
    if val.is_integer():
        txt = f"{int(val):,}".replace(",", ".")
    else:
        txt = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${txt}"


def normalizar_unidad(unidad: str | None, es_pesable: int | bool = False) -> str:
    """Retorna etiqueta de unidad entendible para góndola."""
    u = str(unidad or "").strip().upper()
    if es_pesable or u in ("KG", "KILO", "KILOS"):
        return "KILO"
    if u in ("UN", "U", "UND", "UNIDAD", "UNIDADES"):
        return "UNIDAD"
    if u in ("LT", "LITRO", "LITROS"):
        return "LITRO"
    if u in ("GR", "G", "GRAMO", "GRAMOS"):
        return "100 GR"
    return u or "UNIDAD"


def generar_codigo_barras_escpos(codigo_str: str) -> bytes:
    """Genera secuencia ESC/POS para imprimir código de barras 1D si es válido.
    
    Compatible con la mayoría de impresoras térmicas ESC/POS (Epson, 3nStar, Xprinter, etc.).
    """
    cod = str(codigo_str or "").strip()
    if not cod:
        return b""

    res = bytearray()
    res.extend(ALIGN_CENTER)
    res.extend(GS + b"\x68\x1C")  # Altura de código de barras compacta para góndola: 28 puntos (~3.5mm)
    res.extend(GS + b"\x77\x02")  # Ancho de módulo: 2
    res.extend(GS + b"\x48\x02")  # Posición de texto HRI: debajo del código
    res.extend(GS + b"\x66\x01")  # Fuente HRI Font B (compacta)

    # 1. EAN-13 (12 o 13 dígitos numéricos)
    if cod.isdigit() and len(cod) in (12, 13):
        cod_13 = cod.zfill(13)[:13]
        payload = cod_13.encode("ascii")
        res.extend(GS + b"\x6b\x43" + bytes([len(payload)]) + payload)
        res.extend(b"\n")
        return bytes(res)

    # 2. EAN-8 (7 u 8 dígitos numéricos)
    if cod.isdigit() and len(cod) in (7, 8):
        cod_8 = cod.zfill(8)[:8]
        payload = cod_8.encode("ascii")
        res.extend(GS + b"\x6b\x44" + bytes([len(payload)]) + payload)
        res.extend(b"\n")
        return bytes(res)

    # 3. CODE 39 (Alfanumérico estándar para códigos de PLU o internos)
    valid_c39 = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%")
    if all(c in valid_c39 for c in cod.upper()) and 1 <= len(cod) <= 16:
        payload = cod.upper().encode("ascii")
        res.extend(GS + b"\x6b\x45" + bytes([len(payload)]) + payload)
        res.extend(b"\n")
        return bytes(res)

    # 4. CODE 128 (Juego de caracteres B para códigos variados)
    try:
        raw_ascii = cod.encode("ascii")
        # Prefijo {B selecciona el code set B en ESC/POS Code128
        payload = b"{B" + raw_ascii
        res.extend(GS + b"\x6b\x49" + bytes([len(payload)]) + payload)
        res.extend(b"\n")
        return bytes(res)
    except Exception:
        return b""


def armar_etiqueta_termica(
    producto: dict,
    rubro: str = "CARNICERÍA",
    negocio: str = "MACIEL",
    columnas: int = 32,
    cortar: bool = True,
    incluir_barcode: bool = True,
    incluir_marca: bool = True,
    incluir_fecha: bool = True,
    numero_item: int | None = None,
    total_items: int | None = None,
) -> bytes:
    """Construye los bytes ESC/POS de una etiqueta individual de góndola."""
    cols = max(24, int(columnas))
    data = bytearray()

    # Reset de la impresora para evitar arrastrar estilos previos
    data.extend(RESET)

    p_id = str(producto.get("id") or "").strip()
    codigo = str(producto.get("codigo") or p_id).strip()
    nombre = str(producto.get("nombre") or "PRODUCTO").strip()
    is_oferta = bool(producto.get("is_oferta", False))
    precio_str = str(producto.get("precio", "0"))
    precio_reg_str = str(producto.get("precio_regular", precio_str))
    unidad_str = normalizar_unidad(producto.get("unidad"), producto.get("es_pesable", False))

    precio_fmt = formatear_precio_argentino(precio_str)
    precio_reg_fmt = formatear_precio_argentino(precio_reg_str)

    linea_doble = b"=" * cols + b"\n"
    linea_simple = b"-" * cols + b"\n"

    # --- 1. CABECERA COMPACTA (1 renglón) ---
    data.extend(linea_doble)
    data.extend(ALIGN_CENTER)
    data.extend(BOLD_ON)
    if is_oferta:
        data.extend(INVERT_ON)
        aviso_oferta = f"*** OFERTA: {negocio.upper()} ***" if cols <= 32 else f"*** OFERTA DESTACADA: {negocio.upper()} - {rubro.upper()} ***"
        data.extend(aviso_oferta[:cols].center(cols).encode("cp850", errors="replace") + b"\n")
        data.extend(INVERT_OFF)
    elif incluir_marca:
        marca_texto = f"{negocio.upper()} - {rubro.upper()}"
        data.extend(marca_texto[:cols].center(cols).encode("cp850", errors="replace") + b"\n")
    data.extend(BOLD_OFF)
    data.extend(linea_simple)

    # --- 2. NOMBRE DEL ARTÍCULO (1-2 renglones) ---
    data.extend(ALIGN_CENTER)
    data.extend(BOLD_ON)
    pedazos_nombre = textwrap.wrap(nombre.upper(), cols) or [nombre.upper()[:cols]]
    for pedazo in pedazos_nombre[:2]:  # Máximo 2 líneas para preservar tamaño góndola
        data.extend(pedazo.center(cols).encode("cp850", errors="replace") + b"\n")
    data.extend(BOLD_OFF)

    # --- 3. PRECIO GIGANTE ESTÁNDAR GÓNDOLA ---
    data.extend(ALIGN_CENTER)
    cant_of = float(producto.get("cant_oferta") or 0)
    tipo_un_of = producto.get("tipo_unidad_oferta") or "Unidades"
    if is_oferta and cant_of > 1:
        data.extend(BOLD_ON)
        data.extend(f"PROMO: LLEVA {cant_of:g} {tipo_un_of.upper()}\n".encode("cp850", errors="replace"))
        data.extend(BOLD_OFF)

    # Impresión de precio gigante en góndola
    data.extend(BOLD_ON)
    data.extend(DOUBLE_HW_ON)
    data.extend(f"{precio_fmt}\n".encode("cp850", errors="replace"))
    data.extend(DOUBLE_HW_OFF)

    # Unidad de venta y referencia de oferta anterior
    data.extend(BOLD_ON)
    if is_oferta and precio_reg_str and precio_reg_str != precio_str:
        detalle_u = f"x {unidad_str}  (Antes: {precio_reg_fmt})"
    else:
        detalle_u = f"x {unidad_str}"
    data.extend(detalle_u[:cols].center(cols).encode("cp850", errors="replace") + b"\n")
    data.extend(BOLD_OFF)
    data.extend(linea_simple)

    # --- 4. IDENTIFICACIÓN / FECHA / PLU (1 renglón) ---
    if incluir_fecha:
        fecha_txt = datetime.now().strftime("%d/%m/%Y")
        conteo_txt = f"[{numero_item}/{total_items}] " if (numero_item and total_items and total_items > 1) else ""
        plu_txt = f"{conteo_txt}PLU: {p_id}"
        espacio = cols - len(plu_txt) - len(fecha_txt)
        if espacio < 1:
            espacio = 1
        pie_id_fecha = f"{plu_txt}{' ' * espacio}{fecha_txt}"
        data.extend(ALIGN_LEFT)
        data.extend(CHICO_ON)
        data.extend(pie_id_fecha[:cols].encode("cp850", errors="replace") + b"\n")
        data.extend(CHICO_OFF)

    # --- 5. CÓDIGO DE BARRAS TÉRMICO COMPACTO ---
    if incluir_barcode and codigo:
        bc_bytes = generar_codigo_barras_escpos(codigo)
        if bc_bytes:
            data.extend(bc_bytes)
        else:
            data.extend(ALIGN_CENTER)
            data.extend(BOLD_ON)
            data.extend(f"[{codigo}]\n".encode("cp850", errors="replace"))
            data.extend(BOLD_OFF)

    data.extend(linea_doble)

    # --- 6. CORTE LIMPIO (Avance mínimo exacto para el cutter) ---
    if cortar:
        data.extend(b"\n\n")
        data.extend(CUT_PAPER)
    else:
        data.extend(b"\n")

    return bytes(data)


def armar_preview_texto(
    producto: dict,
    rubro: str = "CARNICERÍA",
    negocio: str = "MACIEL",
    columnas: int = 32,
    cortar: bool = True,
    incluir_barcode: bool = True,
    incluir_marca: bool = True,
    incluir_fecha: bool = True,
    numero_item: int | None = None,
    total_items: int | None = None,
) -> str:
    """Genera representación textual idéntica a la etiqueta estándar de góndola."""
    cols = max(24, int(columnas))
    p_id = str(producto.get("id") or "").strip()
    codigo = str(producto.get("codigo") or p_id).strip()
    nombre = str(producto.get("nombre") or "PRODUCTO").strip()
    is_oferta = bool(producto.get("is_oferta", False))
    precio_str = str(producto.get("precio", "0"))
    precio_reg_str = str(producto.get("precio_regular", precio_str))
    unidad_str = normalizar_unidad(producto.get("unidad"), producto.get("es_pesable", False))

    precio_fmt = formatear_precio_argentino(precio_str)
    precio_reg_fmt = formatear_precio_argentino(precio_reg_str)

    lineas = []
    linea_doble = "=" * cols
    linea_simple = "-" * cols

    # 1. Cabecera
    lineas.append(linea_doble)
    if is_oferta:
        aviso = f"*** OFERTA: {negocio.upper()} ***" if cols <= 32 else f"*** OFERTA DESTACADA: {negocio.upper()} - {rubro.upper()} ***"
        lineas.append(aviso[:cols].center(cols))
    elif incluir_marca:
        marca_texto = f"{negocio.upper()} - {rubro.upper()}"
        lineas.append(marca_texto[:cols].center(cols))
    lineas.append(linea_simple)

    # 2. Nombre
    pedazos = textwrap.wrap(nombre.upper(), cols) or [nombre.upper()[:cols]]
    for ped in pedazos[:2]:
        lineas.append(ped.center(cols))

    # 3. Promo y Precio gigante
    cant_of = float(producto.get("cant_oferta") or 0)
    tipo_un_of = producto.get("tipo_unidad_oferta") or "Unidades"
    if is_oferta and cant_of > 1:
        lineas.append(f"PROMO: LLEVA {cant_of:g} {tipo_un_of.upper()}".center(cols))

    lineas.append(precio_fmt.center(cols))

    if is_oferta and precio_reg_str and precio_reg_str != precio_str:
        lineas.append(f"x {unidad_str}  (Antes: {precio_reg_fmt})".center(cols))
    else:
        lineas.append(f"x {unidad_str}".center(cols))

    lineas.append(linea_simple)

    # 4. PLU y Fecha
    if incluir_fecha:
        fecha_txt = datetime.now().strftime("%d/%m/%Y")
        conteo_txt = f"[{numero_item}/{total_items}] " if (numero_item and total_items and total_items > 1) else ""
        plu_txt = f"{conteo_txt}PLU: {p_id}"
        espacio = cols - len(plu_txt) - len(fecha_txt)
        if espacio < 1:
            espacio = 1
        lineas.append(f"{plu_txt}{' ' * espacio}{fecha_txt}")

    # 5. Barcode
    if incluir_barcode and codigo:
        bc_chars = "|" * min(cols - 4, 30 if cols <= 32 else 42)
        lineas.append(bc_chars.center(cols))
        lineas.append(codigo.center(cols))

    lineas.append(linea_doble)
    h_mm = "32 mm" if cols <= 32 else "35 mm"
    if cortar:
        lineas.append("✂️ [CORTE AUTOMÁTICO DE PAPEL]".center(cols))
    else:
        lineas.append("--- (Fin de etiqueta continua) ---".center(cols))

    return "\n".join(lineas)


def armar_lote_etiquetas_termica(
    productos: list[dict],
    rubro: str = "CARNICERÍA",
    negocio: str = "MACIEL",
    columnas: int = 32,
    copias: int = 1,
    cortar_por_etiqueta: bool = True,
    incluir_barcode: bool = True,
    incluir_marca: bool = True,
    incluir_fecha: bool = True,
) -> bytes:
    """Construye el flujo completo de bytes ESC/POS para todo el lote de productos."""
    total_data = bytearray()
    num_copias = max(1, int(copias))
    total_prods = len(productos or [])

    for idx, prod in enumerate(productos or [], 1):
        for _ in range(num_copias):
            etiqueta_bytes = armar_etiqueta_termica(
                producto=prod,
                rubro=rubro,
                negocio=negocio,
                columnas=columnas,
                cortar=cortar_por_etiqueta,
                incluir_barcode=incluir_barcode,
                incluir_marca=incluir_marca,
                incluir_fecha=incluir_fecha,
                numero_item=idx if total_prods > 1 else None,
                total_items=total_prods if total_prods > 1 else None,
            )
            total_data.extend(etiqueta_bytes)

    # Si se configuró corte solo al final del lote
    if not cortar_por_etiqueta and productos:
        total_data.extend(b"\n\n\n\n")
        total_data.extend(CUT_PAPER)

    return bytes(total_data)
