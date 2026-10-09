"""Generación de tickets de cierre de caja (Reporte Z/X).

Este módulo contiene funciones para formatear e imprimir el reporte de cierre
de caja con desglose completo de métodos de pago, abonos de clientes y
diferencias acumuladas.

Funciones:
    - formatear_ticket_z: Genera el contenido ESC/POS del ticket Z
    - imprimir_ticket_z: Envía el ticket a la impresora
"""

from datetime import datetime


def _formatear_moneda(valor: float) -> str:
    """Formatea un valor numérico como moneda Argentina.

    Args:
        valor: Valor numérico a formatear

    Returns:
        String con formato "$1,234.56"
    """
    try:
        return f"${valor:,.2f}"
    except:
        return f"${valor}"


def _obtener_linea_metodo_pago(nombre: str, valor: float, indent: int = 19) -> bytes:
    """Genera una línea de método de pago con formato alineado.

    Args:
        nombre: Nombre del método de pago
        valor: Monto del método
        indent: Espacios para alineación del valor

    Returns:
        Línea formateada como bytes "Nombre:           $1,234.56\n"
    """
    espacios = indent - len(nombre)
    if espacios < 1:
        espacios = 1
    return f"{nombre}{' ' * espacios}{_formatear_moneda(valor)}\n".encode('cp850', errors='replace')


def formatear_ticket_z(
    usuario: str,
    fisico: float,
    dif: float,
    datos_z: dict,
) -> bytes:
    """Genera el contenido ESC/POS del ticket de cierre de caja.

    Args:
        usuario: Nombre del cajero
        fisico: Efectivo contado en caja
        dif: Diferencia (físico - esperado)
        datos_z: Diccionario con todos los datos del cierre:
            - fondo: Fondo de apertura
            - turno_efectivo: Ventas en efectivo del turno
            - turno_tarjeta: Ventas con tarjeta
            - turno_transferencia: Ventas con transferencia
            - turno_vales: Vales de despensa
            - turno_cheque: Cheques
            - turno_credito: Ventas a crédito (fiado)
            - turno_total: Total de ventas del turno
            - dia_tarjeta: Ventas con tarjeta del día
            - dia_total: Total del día
            - efectivo_esperado: Efectivo esperado en caja
            - modo: 'turno' o 'dia'
            - abonos_efectivo_detalle: Abonos en efectivo
            - abonos_transferencia: Abonos por transferencia
            - abonos_digital: Abonos digitales (QR)
            - entradas_efectivo: Ingresos manuales
            - salidas_efectivo: Egresos manuales
            - es_automatico: True si es cierre programado
            - es_cajero: True si es desde paso5 (cajero)
            - diferencia_mes: Acumulado del mes
            - diferencia_historica: Acumulado histórico

    Returns:
        Bytes en formato ESC/POS listos para enviar a la impresora
    """
    # Comandos ESC/POS
    ESC = b'\x1B'
    GS = b'\x1D'
    ALIGN_CENTER = ESC + b'\x61\x01'
    ALIGN_LEFT = ESC + b'\x61\x00'
    BOLD_ON = ESC + b'\x45\x01'
    BOLD_OFF = ESC + b'\x45\x00'
    CUT_PAPER = GS + b'\x56\x41\x00'

    # Mapeo de datos con valores por defecto
    fondo = float(datos_z.get('fondo') or 0.0)
    t_efec = float(datos_z.get('turno_efectivo') or datos_z.get('t_efec') or 0.0)
    t_tarj = float(datos_z.get('turno_tarjeta') or datos_z.get('t_tarj') or 0.0)
    t_trans = float(datos_z.get('turno_transferencia') or datos_z.get('t_trans') or 0.0)
    t_vales = float(datos_z.get('turno_vales') or datos_z.get('t_vales') or 0.0)
    t_cheque = float(datos_z.get('turno_cheque') or datos_z.get('t_cheque') or 0.0)
    t_credito = float(datos_z.get('turno_credito') or datos_z.get('t_credito') or 0.0)
    t_tot = float(datos_z.get('turno_total') or datos_z.get('t_total') or 0.0)

    d_tarj = float(datos_z.get('dia_tarjeta') or datos_z.get('d_tarj') or 0.0)
    d_tot = float(datos_z.get('dia_total') or datos_z.get('d_total') or 0.0)

    esp = float(datos_z.get('efectivo_esperado') or datos_z.get('esperado') or 0.0)
    modo = datos_z.get('modo', 'turno')

    # Datos de abonos
    abonos_efectivo = float(datos_z.get('abonos_efectivo_detalle') or datos_z.get('abonos_efectivo') or 0.0)
    abonos_transferencia = float(datos_z.get('abonos_transferencia') or 0.0)
    abonos_digital = float(datos_z.get('abonos_digital') or 0.0)
    total_abonos = abonos_efectivo + abonos_transferencia + abonos_digital

    # Movimientos manuales
    entradas_manuales = float(datos_z.get('entradas_efectivo') or 0.0)
    salidas_manuales = float(datos_z.get('salidas_efectivo') or 0.0)

    # Tipo de cierre
    es_automatico = datos_z.get('es_automatico', False)
    es_cajero = datos_z.get('es_cajero', False)

    if es_cajero:
        tipo_cierre = "cierre diario automatico"
    elif es_automatico:
        tipo_cierre = "cierre diario automatico"
    else:
        tipo_cierre = "IMPRESO MANUAL"

    # Diferencias
    dif_mes = float(datos_z.get('diferencia_mes') or 0.0)
    dif_historica = float(datos_z.get('diferencia_historica') or 0.0)

    # Construir ticket
    data = bytearray()
    data.extend(ESC + b'\x40')  # Reset

    # Header
    data.extend(ALIGN_CENTER)
    data.extend(BOLD_ON)

    if modo == 'turno':
        data.extend(b"REPORTE DE TURNO - CIERRE DE CAJA\n")
    else:
        data.extend(b"REPORTE Z - CIERRE DE CAJA\n")

    data.extend(BOLD_OFF)
    data.extend(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('cp850'))
    data.extend(f"Cajero: {usuario}\n".encode('cp850'))
    data.extend(f"{tipo_cierre}\n".encode('cp850'))
    data.extend(b"--------------------------------\n")

    # Cuerpo
    data.extend(ALIGN_LEFT)
    data.extend(b"--- TURNO CAJERO ---\n")
    data.extend(f"Fondo Inicial:     {_formatear_moneda(fondo)}\n".encode('cp850'))

    # Métodos de pago
    data.extend(b"\n--- METODOS DE PAGO ---\n")
    data.extend(_obtener_linea_metodo_pago("Efectivo:", t_efec))
    data.extend(_obtener_linea_metodo_pago("Tarjeta Cred/Deb:", t_tarj))

    if t_trans > 0:
        data.extend(_obtener_linea_metodo_pago("Transferencia:", t_trans))
    if t_vales > 0:
        data.extend(_obtener_linea_metodo_pago("Vales Despensa:", t_vales))
    if t_cheque > 0:
        data.extend(_obtener_linea_metodo_pago("Cheques:", t_cheque))

    # Pagos con QR
    if t_trans > 0 or abonos_digital > 0:
        data.extend(_obtener_linea_metodo_pago("Pagos con QR:", t_trans + abonos_digital))

    # Clientes crédito
    if t_credito > 0:
        data.extend(_obtener_linea_metodo_pago("Clientes Credito:", t_credito))

    # Total digital
    total_digital = t_tarj + t_trans + t_vales + t_cheque
    data.extend(_obtener_linea_metodo_pago("TOTAL DIGITAL:", total_digital))

    data.extend(BOLD_ON)
    data.extend(_obtener_linea_metodo_pago("TOTAL TURNO:", t_tot))
    data.extend(BOLD_OFF)
    data.extend(b"--------------------------------\n")

    # Abonos de clientes
    if total_abonos > 0:
        data.extend(b"\n--- ABONOS DE CLIENTES ---\n")
        if abonos_transferencia > 0:
            data.extend(_obtener_linea_metodo_pago("Transferencia:", abonos_transferencia))
        if abonos_efectivo > 0:
            data.extend(_obtener_linea_metodo_pago("Efectivo:", abonos_efectivo))
        if abonos_digital > 0:
            data.extend(_obtener_linea_metodo_pago("Digital QR:", abonos_digital))
        data.extend(BOLD_ON)
        data.extend(_obtener_linea_metodo_pago("TOTAL ABONADOS:", total_abonos))
        data.extend(BOLD_OFF)
        data.extend(b"--------------------------------\n")

    # Movimientos manuales
    if entradas_manuales > 0 or salidas_manuales > 0:
        data.extend(b"\n--- MOVIMIENTOS MANUALES ---\n")
        if entradas_manuales > 0:
            data.extend(_obtener_linea_metodo_pago("Ingreso Efectivo:", entradas_manuales))
        if salidas_manuales > 0:
            data.extend(_obtener_linea_metodo_pago("Egreso Efectivo:", salidas_manuales))
        data.extend(b"--------------------------------\n")

    # Global del día (solo en modo Z)
    if modo != 'turno':
        data.extend(b"--- GLOBAL DEL DIA ---\n")
        data.extend(_obtener_linea_metodo_pago("Ventas Tarjeta:", d_tarj))
        data.extend(BOLD_ON)
        data.extend(_obtener_linea_metodo_pago("TOTAL DIA:", d_tot))
        data.extend(BOLD_OFF)
        data.extend(b"--------------------------------\n")

    # Cuadre físico
    data.extend(b"--- CUADRE FISICO ---\n")
    data.extend(_obtener_linea_metodo_pago("Efectivo Esperado:", esp))
    data.extend(b"(Fondo + Ventas Efec + Ingresos - Egresos)\n")
    data.extend(_obtener_linea_metodo_pago("Efectivo Contado:", fisico))

    # Diferencia
    if abs(dif) < 0.01:
        dif_txt = "CUADRE PERFECTO"
    elif dif > 0:
        dif_txt = f"SOBRANTE: +{_formatear_moneda(dif)}"
    else:
        dif_txt = f"FALTANTE: -{_formatear_moneda(abs(dif))}"

    data.extend(f"Diferencia: {dif_txt}\n".encode('cp850', errors='replace'))
    data.extend(b"--------------------------------\n")

    # Diferencia del mes
    if abs(dif_mes) > 0.01:
        data.extend(b"\n--- DIFERENCIA MES ---\n")
        if dif_mes > 0:
            data.extend(f"Acumulado: +{_formatear_moneda(dif_mes)}\n".encode('cp850', errors='replace'))
        else:
            data.extend(f"Acumulado: -{_formatear_moneda(abs(dif_mes))}\n".encode('cp850', errors='replace'))
        data.extend(b"--------------------------------\n")

    # Diferencia histórica
    if abs(dif_historica) > 0.01:
        data.extend(b"\n--- DIFERENCIA HISTORICA ---\n")
        if dif_historica > 0:
            data.extend(f"Acumulado: +{_formatear_moneda(dif_historica)}\n".encode('cp850', errors='replace'))
        else:
            data.extend(f"Acumulado: -{_formatear_moneda(abs(dif_historica))}\n".encode('cp850', errors='replace'))
        data.extend(b"--------------------------------\n")

    # Footer
    data.extend(b"\n\n\n\n\n")
    data.extend(CUT_PAPER)

    return bytes(data)
