from src.hardware.printer import ALIGN_CENTER, ALIGN_LEFT, BOLD_ON, BOLD_OFF, CUT_PAPER, KICK_DRAWER, KICK_DRAWER_P5, GS_A_1

def generar_pie(columnas, num_venta, total, cliente_nombre, saldo_anterior, saldo_disponible, abono_cuenta, mensaje_extra_condiciones, factura_electronica_data, abrir_cajon, config_drawer_pin, config_3nstar):
    data = bytearray()

    # Inyectar saldos de Cuenta Corriente si corresponde
    if cliente_nombre and saldo_anterior is not None and saldo_disponible is not None:
        primer_nombre = cliente_nombre.split()[0] if cliente_nombre else ""
        data.extend(b"\n")
        data.extend((b"-" * columnas) + b"\n")
        data.extend(BOLD_ON)
        data.extend(f"Hola {primer_nombre}\n".encode('cp850', errors='replace'))
        data.extend(BOLD_OFF)
        data.extend(b"Resumen:\n")
        data.extend(f"Saldo anterior:   ${saldo_anterior:.2f}\n".encode('cp850'))
        if float(abono_cuenta or 0) > 0.009:
            data.extend(
                f"Abono a cuenta:   ${float(abono_cuenta):.2f}\n".encode('cp850')
            )
        data.extend(f"Compra actual:    ${total:.2f}\n".encode('cp850'))
        data.extend(BOLD_ON)
        data.extend(f"Saldo disponible: ${saldo_disponible:.2f}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend((b"-" * columnas) + b"\n")

    if mensaje_extra_condiciones:
        data.extend(BOLD_ON)
        for linea in mensaje_extra_condiciones.split("\n"):
            data.extend(f"{linea}\n".encode("cp850"))
        data.extend(BOLD_OFF)
        data.extend((b"-" * columnas) + b"\n")

    # Footer y Firma Fiscal Electrónica ARCA
    if factura_electronica_data:
        data.extend(b"\n")
        data.extend(f"Pto. Venta: {factura_electronica_data['pto_venta']:04d} | Comp: {num_venta:08d}\n".encode('cp850'))
        data.extend(BOLD_ON)
        data.extend(f"CAE: {factura_electronica_data['cae']}\n".encode('cp850'))
        data.extend(f"Vence: {factura_electronica_data['vencimiento']}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend((b"-" * columnas) + b"\n")
        data.extend(b" Comprobante Autorizado por ARCA\n")
        # Enlace abreviado del QR oficial de ARCA para cumplimiento legal
        data.extend(f"QR ARCA: {factura_electronica_data['qr_url'][:35]}...\n".encode('cp850'))
    else:
        data.extend(b"\n")
    from src.hardware.printer import ALIGN_CENTER
    data.extend(ALIGN_CENTER)
    data.extend(b"NO VALIDO COMO FACTURA\n")
    data.extend(b"\n")
    data.extend(b"Gracias por tu compra!\n")
    data.extend(b"Te esperamos pronto!\n")

    data.extend(b"\n\n\n")

    # Cortar papel y opcionalmente abrir cajón
    data.extend(CUT_PAPER)
    if abrir_cajon:
        kick = KICK_DRAWER_P5 if config_drawer_pin == 1 else KICK_DRAWER
        if config_3nstar:
            data.extend(GS_A_1)
        data.extend(kick)

    return data
