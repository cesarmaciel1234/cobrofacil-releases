from src.hardware.printer import ALIGN_LEFT, BOLD_ON, BOLD_OFF

def generar_cuerpo(columnas, items):
    data = bytearray()
    
    data.extend(ALIGN_LEFT)
    data.extend(b"Detalle / Cant x Unit.      Total\n")
    for it in items:
        clean_name = it['nombre'].replace("🏷️ ", "*OFER* ").replace("🔥 [OFERTA] ", "*OFER* ")
        data.extend(BOLD_ON)
        data.extend(f"{clean_name}\n".encode('cp850', errors='replace'))
        data.extend(BOLD_OFF)

        cant_str = f"{it['cant']:g}"
        unit_price = it.get('precio', 0.0)
        if not unit_price and it['cant'] > 0:
            unit_price = it['subtotal'] / it['cant']

        calc_str = f"  {cant_str} x ${unit_price:.2f}"
        
        total_orig = round(unit_price * it['cant'], 2)
        subt_real = round(it['subtotal'], 2)
        diff = round(total_orig - subt_real, 2)

        if diff > 0:
            subt_str = f"${total_orig:.2f}"
            espacios = columnas - len(calc_str) - len(subt_str)
            if espacios < 1: espacios = 1
            data.extend((calc_str + " " * espacios + subt_str + "\n").encode('cp850'))
            
            lbl_desc = "  Descuento"
            val_desc = f"-${diff:.2f}"
            espacios_desc = columnas - len(lbl_desc) - len(val_desc)
            if espacios_desc < 1: espacios_desc = 1
            data.extend((lbl_desc + " " * espacios_desc + val_desc + "\n").encode('cp850'))
        else:
            subt_str = f"${subt_real:.2f}"
            espacios = columnas - len(calc_str) - len(subt_str)
            if espacios < 1: espacios = 1
            data.extend((calc_str + " " * espacios + subt_str + "\n").encode('cp850'))

    data.extend((b"-" * columnas) + b"\n")
    return data
