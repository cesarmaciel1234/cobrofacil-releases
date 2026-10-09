from datetime import datetime
from src.hardware.printer import ESC, ALIGN_CENTER, BOLD_ON, BOLD_OFF

def generar_encabezado(columnas, empresa, cuit, direccion, telefono, estado, num_venta, cajero, cajero_secundario, factura_electronica_data=None):
    data = bytearray()
    data.extend(ESC + b'\x40') # Reset
    data.extend(ALIGN_CENTER)
    
    # Header
    
    hora = datetime.now().hour
    if 5 <= hora < 13:
        saludo = "Buenos dias!"
    elif 13 <= hora < 20:
        saludo = "Buenas tardes!"
    else:
        saludo = "Buenas noches!"
        
    data.extend(f"{saludo}\n".encode('cp850', errors='ignore'))
    
    data.extend(BOLD_ON)
    data.extend(f"{empresa}\n".encode('cp850', errors='ignore'))
    data.extend(BOLD_OFF)
    if cuit:
        data.extend(f"{cuit}\n".encode('cp850', errors='ignore'))
    if direccion:
        data.extend(f"{direccion}\n".encode('cp850', errors='ignore'))
    if telefono:
        data.extend(f"Tel: {telefono}".encode('cp850', errors='ignore') + b"\n")

    if str(estado).upper() == "CANCELADA":
        data.extend(BOLD_ON)
        data.extend(f"{'*** VENTA CANCELADA ***'.center(columnas)}\n".encode('cp850'))
        data.extend(BOLD_OFF)

    data.extend((b"-" * columnas) + b"\n")

    # Cabecera de Factura Electrnica Oficial si corresponde
    if factura_electronica_data:
        data.extend(BOLD_ON)
        data.extend(f"{'FACTURA B'.center(columnas)}\n".encode('cp850'))
        data.extend(f"{'COMPROBANTE AUTORIZADO'.center(columnas)}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend((b"-" * columnas) + b"\n")

    data.extend(f"Ticket Nro: {num_venta:08d}".center(columnas).encode('cp850') + b"\n")
    data.extend(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}".center(columnas).encode('cp850') + b"\n")
    if cajero:
        data.extend(f"Cajero:  {cajero}".center(columnas).encode('cp850', errors='ignore') + b"\n")
    if cajero_secundario:
        data.extend(f"Cobro:   {cajero_secundario}".center(columnas).encode('cp850', errors='ignore') + b"\n")
    data.extend((b"-" * columnas) + b"\n")
    
    return data
