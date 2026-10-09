from src.hardware.printer import ALIGN_CENTER, ALIGN_LEFT, BOLD_ON, BOLD_OFF, DOUBLE_HEIGHT_ON, DOUBLE_HEIGHT_OFF

def generar_totales(columnas, total, pago, cambio, metodo_pago, items, discount_amount, surcharge_amount, factura_electronica_data, calcular_iva_func):
    data = bytearray()
    data.extend(ALIGN_CENTER)

    # Extraer descuento de productos vs redondeo general
    desc_productos = 0.0
    for it in items:
        precio_orig = it.get('precio', 0.0)
        if precio_orig > 0:
            diff = round((precio_orig * it['cant']) - it['subtotal'], 2)
            if diff > 0:
                desc_productos += diff

    redondeo = round((discount_amount or 0.0) - desc_productos, 2)
    if redondeo < 0: redondeo = 0.0

    # Mostrar Descuento si existe
    if (discount_amount and discount_amount > 0) or (surcharge_amount and surcharge_amount > 0):
        data.extend(ALIGN_LEFT)
        total_bruto = total + (discount_amount or 0) - (surcharge_amount or 0)
        
        bruto_str = f"${total_bruto:.2f}"
        data.extend((f"Subtotal:" + " " * max(1, columnas - 9 - len(bruto_str)) + bruto_str + "\n").encode('cp850'))

        if desc_productos > 0:
            dp_str = f"-${desc_productos:.2f}"
            data.extend((f"Descuento:" + " " * max(1, columnas - 10 - len(dp_str)) + dp_str + "\n").encode('cp850'))

        if redondeo > 0:
            desc_str = f"-${redondeo:.2f}"
            data.extend((f"Redondeo:" + " " * max(1, columnas - 9 - len(desc_str)) + desc_str + "\n").encode('cp850'))

        if surcharge_amount and surcharge_amount > 0:
            rec_str = f"+${surcharge_amount:.2f}"
            data.extend((f"Recargo:" + " " * max(1, columnas - 8 - len(rec_str)) + rec_str + "\n").encode('cp850'))
            
        data.extend(ALIGN_CENTER)

    # Desglose de Neto e IVA en Factura Electronica ARCA
    if factura_electronica_data:
        neto, iva_tot, iva_t_map = calcular_iva_func(items, total)
        data.extend(f"NETO GRAVADO:  ${neto:.2f}\n".encode('cp850'))
        for tasa, m_iva in iva_t_map.items():
            if m_iva > 0:
                data.extend(f"IVA ({tasa:.1f}%):    ${m_iva:.2f}\n".encode('cp850'))

    data.extend((b"-" * columnas) + b"\n")
    
    # Total a Pagar en Fuente Doble Alto para resaltar
    data.extend(DOUBLE_HEIGHT_ON)
    data.extend(BOLD_ON)
    data.extend(f"TOTAL A PAGAR: ${total:.2f}\n".encode('cp850'))
    data.extend(DOUBLE_HEIGHT_OFF)
    data.extend(BOLD_OFF)
    
    data.extend(ALIGN_LEFT)
    data.extend(f"Pago: ${pago:.2f}\n".encode('cp850'))
    data.extend(f"Vuelto: ${cambio:.2f}\n".encode('cp850'))
    data.extend(f"Forma Pago: {metodo_pago}\n".encode('cp850', errors='replace'))
    
    # Conteo de articulos
    cant_articulos = sum(it['cant'] for it in items)
    data.extend(f"Cant. Artículos: {cant_articulos:g}\n".encode('cp850'))
    
    return data
