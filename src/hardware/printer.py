import logging
import time
import threading
from datetime import datetime
import sys
import os

# Asegurar que el directorio raíz esté en el path para importaciones absolutas
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if root_path not in sys.path:
    sys.path.append(root_path)

try:
    from src.config import config
except (ImportError, ModuleNotFoundError):
    from config import config

# Para Windows, usar pywin32 para enviar bytes directos a la impresora compartida
try:
    import win32print
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

try:
    import serial
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

logger = logging.getLogger(__name__)

# Comandos estándar ESC/POS
ESC = b'\x1B'
GS = b'\x1D'

# Comandos de Cajón (Pulso reforzado de 200ms/400ms: 0xC8)
KICK_DRAWER = ESC + b'\x70\x00\xC8\xC8' # Pin 2
KICK_DRAWER_P5 = ESC + b'\x70\x01\xC8\xC8' # Pin 5
CUT_PAPER = GS + b'\x56\x41\x00'
ALIGN_CENTER = ESC + b'\x61\x01'
ALIGN_LEFT = ESC + b'\x61\x00'
BOLD_ON = ESC + b'\x45\x01'
BOLD_OFF = ESC + b'\x45\x00'
DLE_EOT_1 = b'\x10\x04\x01' # Consulta en tiempo real
GS_R_2 = b'\x1D\x72\x02'    # Transmitir estado de cajón (más compatible)
GS_A_1 = b'\x1D\x61\x01'    # Habilitar ASB
# Nombres lógicos OPOS comunes
OPOS_LDNS = ["caja", "CashDrawer", "CashDrawer1", "3NSTAR_CASHDRAWER", "Drawer1", "POS-80", "EPSON_CASH_DRAWER"]

class PosPrinter:
    def __init__(self):
        # Lee la configuración de la impresora (ej. nombre de la impresora en Windows)
        # Si está vacío, modo "Simulación"
        self.printer_name = config.get('printer_name', '')
        self._lock = threading.Lock()
        self.header_empresa = config.get('business_name', 'MI EMPRESA')
        self.header_cuit = config.get('business_cuit', 'CUIT: 00-00000000-0')
        self.header_dir = config.get('business_address', 'Dirección Local')
        self._last_serial_error_time = 0.0

    def _send_raw_data(self, raw_data, printer_name_override=None):
        """ Envía bytes RAW a la impresora (Windows Spooler o Serial Directo). """
        p_name = printer_name_override if printer_name_override else config.get('ticket_printer', config.get('printer_name', ''))
        
        if not p_name:
            logger.info("Impresora no configurada. Simulando impresión.")
            return True

        # --- MODO SERIAL DIRECTO (COMx) ---
        if p_name.upper().startswith("COM"):
            if not SERIAL_AVAILABLE:
                logger.error("pyserial no instalado para comunicación COM.")
                return False
            try:
                with self._lock:
                    with serial.Serial(p_name, 9600, timeout=2) as ser:
                        ser.write(raw_data)
                    return True
            except Exception as e:
                logger.error(f"Error en puerto Serial {p_name}: {e}")
                return False

        # --- MODO WINDOWS SPOOLER (USB/Red) ---
        if not WIN32_AVAILABLE:
            logger.error("win32print no está instalado.")
            return False

        try:
            hPrinter = win32print.OpenPrinter(p_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Ticket PunPro", None, "RAW"))
                try:
                    win32print.StartPagePrinter(hPrinter)
                    win32print.WritePrinter(hPrinter, raw_data)
                    win32print.EndPagePrinter(hPrinter)
                finally:
                    win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
            return True
        except Exception as e:
            logger.error(f"Fallo al enviar a impresora {p_name}: {e}")
            return False

    def pitido(self):
        """ Envía el comando ESC/POS para hacer sonar el buzzer interno (si existe). """
        logger.info("Enviando comando de pitido (Buzzer)...")
        # Comando estándar: ESC B n t
        # n = número de veces, t = tiempo (t * 100ms)
        comando = ESC + b'\x42\x02\x01' 
        return self._send_raw_data(comando)

    def abrir_cajon(self):
        """ Envía el comando ESC/POS estándar para patear el cajón de dinero. """
        p_name = config.get('ticket_printer', config.get('printer_name', ''))
        logger.info(f"Enviando señal de apertura a {p_name}...")
        
        # Seleccionar pin (0=Pin 2, 1=Pin 5)
        pin = config.get("drawer_kick_pin", 0)
        comando = KICK_DRAWER_P5 if pin == 1 else KICK_DRAWER
        
        # Si es 3nstar o requiere reporte proactivo, enviamos GS a 1
        if config.get("printer_3nstar_mode", False):
            comando = GS_A_1 + comando
            
        return self._send_raw_data(comando, printer_name_override=p_name)

    def check_drawer_status(self, printer_name_override=None):
        """ 
        Consulta el estado del cajón vía Serial Directo o Windows Spooler.
        """
        # Evitar saturar el puerto COM si hubo un error reciente (ej: puerto ocupado por Spooler)
        if time.time() - self._last_serial_error_time < 15.0:
            return False

        p_name = printer_name_override if printer_name_override else (config.get('ticket_printer', self.printer_name))
        if not p_name: return False

        # --- PRIORIDAD 1: MODO SERIAL DIRECTO (COMx) ---
        if p_name.upper().startswith("COM") and SERIAL_AVAILABLE:
            try:
                with self._lock:
                    with serial.Serial(p_name, 9600, timeout=0.2) as ser:
                        # Triple intento de comunicación
                        for attempt in range(3):
                            ser.reset_input_buffer()
                            ser.reset_output_buffer()
                            
                            # RÁFAGA DE CAJÓN
                            ser.write(b'\x10\x04\x04\x1D\x72\x02')
                            time.sleep(0.1)
                            
                            res = ser.read(ser.in_waiting or 3)
                            if res:
                                # Detección inicial
                                is_open = any(bool(b & 0x01) or bool(b & 0x04) or bool(b & 0x08) for b in res)
                                
                                # Filtro de confirmación inmediata (Debounce)
                                if is_open:
                                    time.sleep(0.05)
                                    ser.write(b'\x10\x04\x04')
                                    res2 = ser.read(ser.in_waiting or 1)
                                    if res2:
                                        is_open = any(bool(b & 0x01) or bool(b & 0x04) or bool(b & 0x08) for b in res2)
                                
                                if config.get("drawer_sensor_inverted", False): is_open = not is_open
                                
                                logger.info(f"🛰️ HARDWARE STATUS: Pack={res.hex().upper()} (Intento {attempt+1}) -> {'ABIERTO' if is_open else 'CERRADO'}")
                                return is_open
                            
                        time.sleep(0.05) # Pequeña espera entre reintentos
                    
                    return False
            except Exception as e:
                logger.info(f"⚠️ SERIAL [{p_name}]: Error al intentar abrir el puerto: {e}")
                self._last_serial_error_time = time.time()
                return False

        # --- PRIORIDAD 2: MODO WINDOWS SPOOLER (DESACTIVADO POR BLOQUEOS) ---
        # Se ha detectado que StartDocPrinter puede congelar la app en impresoras USB.
        # Desactivado en favor de OPOS y Serial Directo.
        
        # --- PRIORIDAD 3: FALLBACK SERIAL (CON LOCK DE SEGURIDAD) ---
        # Si la ticketera principal es USB/Spooler pero el sensor está conectado a un puerto COM (configurado en printer_name)
        fallback_com = config.get('printer_name', '')
        if fallback_com.upper().startswith("COM") and fallback_com.upper() != p_name.upper() and SERIAL_AVAILABLE:
            try:
                with self._lock:
                    with serial.Serial(fallback_com, 9600, timeout=0.2) as ser:
                        for attempt in range(2):
                            ser.reset_input_buffer()
                            ser.reset_output_buffer()
                            ser.write(b'\x10\x04\x04\x1D\x72\x02')
                            time.sleep(0.05)
                            res = ser.read(ser.in_waiting or 3)
                            if res:
                                is_open = any(bool(b & 0x01) or bool(b & 0x04) or bool(b & 0x08) for b in res)
                                if config.get("drawer_sensor_inverted", False): is_open = not is_open
                                logger.info(f"🛰️ FALLBACK STATUS: Pack={res.hex().upper()} (Intento {attempt+1}) -> {'ABIERTO' if is_open else 'CERRADO'}")
                                return is_open
                            time.sleep(0.02)
            except Exception as e:
                logger.debug(f"⚠️ FALLBACK [{fallback_com}]: Puerto ocupado o no disponible: {e}")
                self._last_serial_error_time = time.time()
                return False

        return False

    def verificar_estado(self):
        """ Verifica si la impresora configurada está disponible en el sistema. """
        printer_name = config.get('ticket_printer', config.get('printer_name', ''))
        if not printer_name:
            # Modo Simulación: No es un error, es un estado válido
            return True, "Modo Simulación (Impresora no configurada)."
            
        if not WIN32_AVAILABLE:
            return False, "win32print no disponible (Instala pywin32)."

        try:
            hPrinter = win32print.OpenPrinter(printer_name)
            win32print.ClosePrinter(hPrinter)
            return True, f"Impresora {printer_name} conectada."
        except Exception as e:
            return False, f"Error de conexión con {printer_name}: {e}"

    def _should_route_fiscal(self, metodo_pago: str) -> bool:
        """Determina si el método de pago especificado debe emitir factura fiscal/ARCA."""
        target_methods = config.get("fiscal_payment_methods", ["Tarjeta", "Transferencia", "Mixto"])
        metodo_clean = str(metodo_pago).strip().upper()
        for m in target_methods:
            m_up = m.upper()
            if m_up == "TARJETA" and (metodo_clean in ("TARJETA", "CREDITO", "DEBITO")):
                return True
            if m_up == "TRANSFERENCIA" and (metodo_clean in ("TRANSFERENCIA", "TRANSF.", "TRANSF")):
                return True
            if m_up == metodo_clean:
                return True
        return False

    def _calcular_iva_desagregado(self, items, total):
        """
        Calcula el NETO e IVA total acumulado, desglosado por las tasas de IVA
        definidas en los departamentos de cada producto de la base de datos.
        """
        from src.database import db_manager
        
        neto_total = 0.0
        iva_total = 0.0
        iva_por_tasa = {}
        
        # Factor de ajuste para prorratear descuentos y recargos globales
        factor_ajuste = 1.0
        if total > 0:
            original_subtotal = sum(float(it.get('subtotal', 0.0)) for it in items)
            if original_subtotal > 0:
                factor_ajuste = total / original_subtotal
                
        for it in items:
            p_id = it.get('id')
            tasa_iva = float(config.get("tax_percentage", 21.0)) # Default
            if p_id and str(p_id) != '000':
                try:
                    res = db_manager.execute_query(
                        "SELECT d.iva FROM productos p JOIN departamentos d ON UPPER(p.departamento) = UPPER(d.nombre) WHERE p.id = ? OR p.codigo = ?",
                        (p_id, p_id)
                    )
                    if res and res[0]['iva'] is not None:
                        tasa_iva = float(res[0]['iva'])
                except Exception:
                    pass
            
            subt_item_ajustado = float(it.get('subtotal', 0.0)) * factor_ajuste
            neto_item = subt_item_ajustado / (1 + tasa_iva / 100)
            iva_item = subt_item_ajustado - neto_item
            
            neto_total += neto_item
            iva_total += iva_item
            iva_por_tasa[tasa_iva] = iva_por_tasa.get(tasa_iva, 0.0) + iva_item
            
        return neto_total, iva_total, iva_por_tasa

    def imprimir_ticket_venta(self, num_venta, items, total, pago, cambio, abrir_cajon=True, estado='COMPLETADA', discount_amount=0, surcharge_amount=0, cajero='', cajero_secundario='', segunda_tiketera=False, metodo_pago='Efectivo', force_fiscal=False):
        """ Formatea e imprime un ticket de venta. Soporta dos cajeros y dos tiketeras. """
        
        afip_global_enabled = config.get("facturacion_afip_global", False)
        should_use_afip = afip_global_enabled and (force_fiscal or self._should_route_fiscal(metodo_pago))
        
        # 1. ROUTING FISCAL HARDWARE: Si el modo fiscal real está activo Y el método de pago está habilitado
        if self._is_fiscal_mode() and should_use_afip:
            return self.imprimir_ticket_fiscal(
                num_venta=num_venta,
                items=items,
                total=total,
                pago=pago,
                cambio=cambio,
                metodo_pago=metodo_pago,
                cajero=cajero,
                discount_amount=discount_amount,
                surcharge_amount=surcharge_amount,
                tipo_comprobante="FACTURA_B"
            )

        # 2. ROUTING FACTURA ELECTRÓNICA ARCA: Si está activo Y el método de pago está habilitado
        factura_electronica_data = None
        if config.get("factura_electronica_mode", False) and should_use_afip:
            try:
                from src.services.facturacion_service import FacturacionService
                venta_data = {
                    'id': num_venta,
                    'total': total,
                    'metodo_pago': metodo_pago,
                    'items': items,
                    'discount_amount': discount_amount,
                    'surcharge_amount': surcharge_amount
                }
                factura_electronica_data = FacturacionService.procesar_factura_electronica(venta_data)
            except Exception as e:
                logger.error(f"Fallo al procesar Factura Electrónica ARCA: {e}")

        data = bytearray()
        data.extend(ESC + b'\x40') # Reset
        
        # Header
        data.extend(ALIGN_CENTER)
        data.extend(BOLD_ON)
        data.extend(f"{self.header_empresa}\n".encode('cp850', errors='replace'))
        data.extend(BOLD_OFF)
        data.extend(f"{self.header_cuit}\n".encode('cp850', errors='replace'))
        data.extend(f"{self.header_dir}\n".encode('cp850', errors='replace'))
        
        if str(estado).upper() == "CANCELADA":
            data.extend(BOLD_ON)
            data.extend(b"*** VENTA CANCELADA ***\n")
            data.extend(BOLD_OFF)
            
        data.extend(b"--------------------------------\n")

        # Cabecera de Factura Electrónica Oficial si corresponde
        if factura_electronica_data:
            data.extend(BOLD_ON)
            data.extend(b"          FACTURA B          \n")
            data.extend(b"    COMPROBANTE AUTORIZADO   \n")
            data.extend(BOLD_OFF)
            data.extend(b"--------------------------------\n")
        
        data.extend(f"Ticket Nro: {num_venta:08d}\n".encode('cp850'))
        data.extend(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('cp850'))
        if cajero:
            data.extend(f"Cajero:  {cajero}\n".encode('cp850', errors='replace'))
        if cajero_secundario:
            data.extend(f"Cobro:   {cajero_secundario}\n".encode('cp850', errors='replace'))
        data.extend(b"--------------------------------\n")
        
        # Items
        data.extend(ALIGN_LEFT)
        data.extend(b"Detalle / Cant x Unit.      Total\n")
        for it in items:
            clean_name = it['nombre'].replace("🏷️ ", "*OFER* ").replace("🔥 [OFERTA] ", "*OFER* ")
            data.extend(f"{clean_name}\n".encode('cp850', errors='replace'))
            
            cant_str = f"{it['cant']:g}"
            unit_price = it.get('precio', 0.0)
            if not unit_price and it['cant'] > 0:
                unit_price = it['subtotal'] / it['cant']
                
            calc_str = f"  {cant_str} x ${unit_price:.2f}"
            subt_str = f"${it['subtotal']:.2f}"
            
            espacios = 32 - len(calc_str) - len(subt_str)
            if espacios < 1:
                espacios = 1
            linea_detalle = calc_str + (" " * espacios) + subt_str + "\n"
            data.extend(linea_detalle.encode('cp850'))
            
        data.extend(b"--------------------------------\n")
        
        # Totales
        data.extend(ALIGN_CENTER)
        
        # Mostrar Descuento si existe
        if (discount_amount and discount_amount > 0) or (surcharge_amount and surcharge_amount > 0):
            total_bruto = total + (discount_amount or 0) - (surcharge_amount or 0)
            data.extend(f"TOTAL BRUTO:   ${total_bruto:.2f}\n".encode('cp850'))
            
            if discount_amount and discount_amount > 0:
                data.extend(BOLD_ON)
                data.extend(f"USTED AHORRO: -${discount_amount:.2f}\n".encode('cp850'))
                data.extend(BOLD_OFF)
                
            if surcharge_amount and surcharge_amount > 0:
                data.extend(f"RECARGO:      +${surcharge_amount:.2f}\n".encode('cp850'))

        # Desglose de Neto e IVA en Factura Electrónica ARCA
        if factura_electronica_data:
            neto, iva_tot, iva_t_map = self._calcular_iva_desagregado(items, total)
            data.extend(f"NETO GRAVADO:  ${neto:.2f}\n".encode('cp850'))
            for tasa, m_iva in iva_t_map.items():
                if m_iva > 0:
                    data.extend(f"IVA ({tasa:.1f}%):    ${m_iva:.2f}\n".encode('cp850'))

        data.extend(b"--------------------------------\n")
        data.extend(BOLD_ON)
        data.extend(f"TOTAL A PAGAR: ${total:.2f}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend(ALIGN_LEFT)
        data.extend(f"Pago: ${pago:.2f}\n".encode('cp850'))
        data.extend(f"Vuelto: ${cambio:.2f}\n".encode('cp850'))
        data.extend(f"Forma Pago: {metodo_pago}\n".encode('cp850', errors='replace'))
        
        # Footer y Firma Fiscal Electrónica ARCA
        data.extend(ALIGN_CENTER)
        if factura_electronica_data:
            data.extend(b"\n")
            data.extend(f"Pto. Venta: {factura_electronica_data['pto_venta']:04d} | Comp: {num_venta:08d}\n".encode('cp850'))
            data.extend(BOLD_ON)
            data.extend(f"CAE: {factura_electronica_data['cae']}\n".encode('cp850'))
            data.extend(f"Vence: {factura_electronica_data['vencimiento']}\n".encode('cp850'))
            data.extend(BOLD_OFF)
            data.extend(b"--------------------------------\n")
            data.extend(b" Comprobante Autorizado por ARCA\n")
            # Enlace abreviado del QR oficial de ARCA para cumplimiento legal
            data.extend(f"QR ARCA: {factura_electronica_data['qr_url'][:35]}...\n".encode('cp850'))
        else:
            data.extend(b"\n")
            data.extend(b"  NO VALIDO COMO FACTURA  \n")
            data.extend(b"*** GRACIAS POR SU COMPRA ***\n")
            
        data.extend(b"\n\n\n\n\n")
        
        # Cortar papel y opcionalmente abrir cajón
        data.extend(CUT_PAPER)
        if abrir_cajon:
            pin = config.get("drawer_kick_pin", 0)
            kick = KICK_DRAWER_P5 if pin == 1 else KICK_DRAWER
            if config.get("printer_3nstar_mode", False):
                data.extend(GS_A_1)
            data.extend(kick)
        
        p_principal = config.get('ticket_printer', config.get('printer_name', ''))
        result = self._send_raw_data(bytes(data), printer_name_override=p_principal)
        
        # Segunda tiketera: si está configurada y habilitada, imprimir copia
        if segunda_tiketera:
            printer2 = config.get('ticket_printer_2', '')
            if printer2:
                self._send_raw_data(bytes(data), printer_name_override=printer2)
        
        return result

    def imprimir_movimiento_caja(self, tipo, monto, motivo, usuario, caja_id):
        """ Imprime un comprobante de ingreso/egreso de efectivo """
        data = bytearray()
        data.extend(ESC + b'\x40') # Reset
        data.extend(ALIGN_CENTER)
        data.extend(BOLD_ON)
        data.extend(f"{self.header_empresa}\n".encode('cp850', errors='replace'))
        data.extend(f"COMPROBANTE DE {tipo}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend(f"Caja ID: {caja_id:02d}\n".encode('cp850'))
        data.extend(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n".encode('cp850'))
        data.extend(f"Operador: {usuario}\n".encode('cp850', errors='replace'))
        data.extend(b"--------------------------------\n")
        
        data.extend(ALIGN_LEFT)
        data.extend(BOLD_ON)
        data.extend(f"MONTO: ${monto:,.2f}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend(f"Motivo: {motivo}\n".encode('cp850', errors='replace'))
        data.extend(b"--------------------------------\n")
        data.extend(b"\n\n\n\n\n")
        data.extend(CUT_PAPER)
        
        p_principal = config.get('ticket_printer', config.get('printer_name', ''))
        result = self._send_raw_data(bytes(data), printer_name_override=p_principal)
        return result

    def imprimir_ticket_z(self, usuario, fisico, dif, datos_z):
        """ Imprime el Cierre de Caja (Reporte Z) """
        # Mapeo robusto de claves con soporte a ambos formatos de diccionario
        fondo = float(datos_z.get('fondo') or 0.0)
        t_efec = float(datos_z.get('turno_efectivo') or datos_z.get('t_efec') or 0.0)
        t_tarj = float(datos_z.get('turno_tarjeta') or datos_z.get('t_tarj') or 0.0)
        t_tot = float(datos_z.get('turno_total') or datos_z.get('t_total') or 0.0)
        
        d_tarj = float(datos_z.get('dia_tarjeta') or datos_z.get('d_tarj') or 0.0)
        d_tot = float(datos_z.get('dia_total') or datos_z.get('d_total') or 0.0)
        
        esp = float(datos_z.get('efectivo_esperado') or datos_z.get('esperado') or 0.0)

        data = bytearray()
        data.extend(ESC + b'\x40')
        data.extend(ALIGN_CENTER)
        data.extend(BOLD_ON)
        data.extend(b"REPORTE Z - CIERRE DE CAJA\n")
        data.extend(BOLD_OFF)
        data.extend(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('cp850'))
        data.extend(f"Cajero: {usuario}\n".encode('cp850'))
        data.extend(b"--------------------------------\n")
        
        data.extend(ALIGN_LEFT)
        data.extend(b"--- TURNO CAJERO ---\n")
        data.extend(f"Fondo Inicial:     ${fondo:.2f}\n".encode('cp850'))
        data.extend(f"Ventas Efectivo:   ${t_efec:.2f}\n".encode('cp850'))
        data.extend(f"Ventas Tarjeta:    ${t_tarj:.2f}\n".encode('cp850'))
        data.extend(BOLD_ON)
        data.extend(f"TOTAL TURNO:       ${t_tot:.2f}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend(b"--------------------------------\n")

        data.extend(b"--- GLOBAL DEL DIA ---\n")
        data.extend(f"Ventas Tarjeta:    ${d_tarj:.2f}\n".encode('cp850'))
        data.extend(BOLD_ON)
        data.extend(f"TOTAL DIA:         ${d_tot:.2f}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend(b"--------------------------------\n")
        
        data.extend(b"--- CUADRE FISICO ---\n")
        data.extend(f"Efectivo Esperado: ${esp:.2f}\n".encode('cp850'))
        data.extend(f"Efectivo Contado:  ${fisico:.2f}\n".encode('cp850'))
        
        if abs(dif) < 0.01: dif_txt = "CUADRE PERFECTO"
        elif dif > 0: dif_txt = f"SOBRANTE: +${dif:.2f}"
        else: dif_txt = f"FALTANTE: -${abs(dif):.2f}"
            
        data.extend(f"Diferencia: {dif_txt}\n".encode('cp850'))
        data.extend(b"\n\n\n\n\n")
        data.extend(CUT_PAPER)
        
        p_principal = config.get('ticket_printer', config.get('printer_name', ''))
        result = self._send_raw_data(bytes(data), printer_name_override=p_principal)
        
        # Copia de seguridad en la Segunda Tiketera (Control de Cajeros Simultáneos)
        if datos_z.get('segunda_tiketera', False):
            printer2 = config.get('ticket_printer_2', '')
            if printer2:
                self._send_raw_data(bytes(data), printer_name_override=printer2)
                
        return result

    # ══════════════════════════════════════════════════════════════════════
    # COMPATIBILIDAD CON IMPRESORA FISCAL (Hasar / Epson TM-H6000 Fiscal)
    # ══════════════════════════════════════════════════════════════════════
    def _is_fiscal_mode(self) -> bool:
        """Devuelve True si el sistema está configurado en modo impresora fiscal."""
        return bool(config.get("fiscal_printer_mode", False))

    def imprimir_ticket_fiscal(self, num_venta, items, total, pago, cambio,
                               metodo_pago="Efectivo", cajero="",
                               discount_amount=0, surcharge_amount=0,
                               tipo_comprobante="TICKET"):
        """
        Imprime un comprobante en formato fiscal argentino.
        Compatible con impresoras ESC/POS térmicas en modo fiscal simulado.
        Para impresoras fiscales reales (Hasar 320F / Epson TM-H6000):
          - Se requiere el driver COM del fabricante y comandos propietarios.
          - Este método genera el bloque de datos ESC/POS más cercano al estándar fiscal.

        Tipos soportados: 'TICKET', 'FACTURA_B', 'NOTA_CREDITO'
        """
        # ── Encabezado fiscal ──────────────────────────────────────────────
        cuit  = config.get("business_cuit", "CUIT: 00-00000000-0")
        iibb  = config.get("business_iibb", "")
        inicio_act = config.get("business_inicio_actividades", "")

        data = bytearray()
        data.extend(ESC + b'\x40')  # Reset impresora

        # Tipo de comprobante (borde fiscal)
        data.extend(ALIGN_CENTER)
        data.extend(BOLD_ON)
        data.extend(b"=" * 32 + b"\n")

        if tipo_comprobante == "FACTURA_B":
            data.extend(b"          FACTURA B          \n")
        elif tipo_comprobante == "NOTA_CREDITO":
            data.extend(b"       NOTA DE CREDITO B      \n")
        else:
            data.extend(b"            TICKET            \n")

        data.extend(b"=" * 32 + b"\n")
        data.extend(BOLD_OFF)

        # Datos del emisor (zona fiscal)
        data.extend(f"{self.header_empresa}\n".encode('cp850', errors='replace'))
        data.extend(f"{cuit}\n".encode('cp850', errors='replace'))
        data.extend(f"{self.header_dir}\n".encode('cp850', errors='replace'))
        if iibb:
            data.extend(f"Ing. Brutos: {iibb}\n".encode('cp850', errors='replace'))
        if inicio_act:
            data.extend(f"Inicio Actividades: {inicio_act}\n".encode('cp850', errors='replace'))

        data.extend(b"--------------------------------\n")
        data.extend(f"Nro: {num_venta:08d}\n".encode('cp850'))
        data.extend(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n".encode('cp850'))
        if cajero:
            data.extend(f"Operador: {cajero}\n".encode('cp850', errors='replace'))
        data.extend(b"--------------------------------\n")

        # ── Items ──────────────────────────────────────────────────────────
        data.extend(ALIGN_LEFT)
        data.extend(b"Detalle / Cant x Unit.      Total\n")
        for it in items:
            clean_name = it['nombre'].replace("🏷️ ", "*OFER* ").replace("🔥 [OFERTA] ", "*OFER* ")
            data.extend(f"{clean_name}\n".encode('cp850', errors='replace'))
            
            cant_str = f"{it['cant']:g}"
            unit_price = it.get('precio', 0.0)
            if not unit_price and it['cant'] > 0:
                unit_price = it['subtotal'] / it['cant']
                
            calc_str = f"  {cant_str} x ${unit_price:.2f}"
            subt_str = f"${it['subtotal']:.2f}"
            
            espacios = 32 - len(calc_str) - len(subt_str)
            if espacios < 1:
                espacios = 1
            linea_detalle = calc_str + (" " * espacios) + subt_str + "\n"
            data.extend(linea_detalle.encode('cp850'))

        data.extend(b"--------------------------------\n")

        # ── Totales ────────────────────────────────────────────────────────
        data.extend(ALIGN_CENTER)

        if (discount_amount and discount_amount > 0) or (surcharge_amount and surcharge_amount > 0):
            total_bruto = total + (discount_amount or 0) - (surcharge_amount or 0)
            data.extend(f"TOTAL BRUTO:  ${total_bruto:.2f}\n".encode('cp850'))
            
            if discount_amount and discount_amount > 0:
                data.extend(BOLD_ON)
                data.extend(f"USTED AHORRO:-${discount_amount:.2f}\n".encode('cp850'))
                data.extend(BOLD_OFF)
                
            if surcharge_amount and surcharge_amount > 0:
                data.extend(f"RECARGO:     +${surcharge_amount:.2f}\n".encode('cp850'))

        # IVA desglosado por departamento/tasa (Responsable Inscripto o Monotributista)
        neto, iva_tot, iva_t_map = self._calcular_iva_desagregado(items, total)
        data.extend(f"NETO:         ${neto:.2f}\n".encode('cp850'))
        for tasa, m_iva in iva_t_map.items():
            if m_iva > 0:
                data.extend(f"IVA ({tasa:.1f}%):   ${m_iva:.2f}\n".encode('cp850'))

        data.extend(b"--------------------------------\n")
        data.extend(BOLD_ON)
        data.extend(f"TOTAL A PAGAR:${total:.2f}\n".encode('cp850'))
        data.extend(BOLD_OFF)
        data.extend(ALIGN_LEFT)
        data.extend(f"Forma pago:   {metodo_pago}\n".encode('cp850', errors='replace'))
        data.extend(f"Recibido:     ${pago:.2f}\n".encode('cp850'))
        data.extend(f"Vuelto:       ${cambio:.2f}\n".encode('cp850'))

        # ── Leyenda legal (según AFIP) ─────────────────────────────────────
        data.extend(ALIGN_CENTER)
        data.extend(b"\n")
        if tipo_comprobante == "TICKET":
            data.extend(b"  NO VALIDO COMO FACTURA  \n")
        else:
            data.extend(b"  COMPROBANTE FISCAL VALIDO  \n")

        footer = config.get("footer_message", "Gracias por su compra!")
        data.extend(f"{footer}\n\n\n\n\n".encode('cp850', errors='replace'))

        data.extend(CUT_PAPER)

        # ── Envío ──────────────────────────────────────────────────────────
        p_principal = config.get('ticket_printer', config.get('printer_name', ''))
        result = self._send_raw_data(bytes(data), printer_name_override=p_principal)

        # Copia en segunda tiketera si está configurada
        printer2 = config.get('ticket_printer_2', '')
        if printer2:
            self._send_raw_data(bytes(data), printer_name_override=printer2)

        return result

    def verificar_impresora_fiscal(self):
        """
        Verifica el estado y compatibilidad de la impresora configurada para modo fiscal.
        Retorna (bool, str): (es_compatible, mensaje_detalle)
        """
        ok, msg = self.verificar_estado()
        if not ok:
            return False, msg

        fiscal_mode = self._is_fiscal_mode()
        printer_name = config.get('ticket_printer', config.get('printer_name', ''))

        if not fiscal_mode:
            return True, f"Modo Fiscal: DESACTIVADO. Impresora: {printer_name or 'Simulación'}"

        # En modo fiscal, verificar que la impresora sea compatible
        # Impresoras fiscales reales necesitan driver COM propietario
        es_fiscal_real = any(x in printer_name.upper() for x in [
            "HASAR", "EPSON TM-H", "BEMATECH", "STAR MICRONICS", "FISCAL"
        ])

        if es_fiscal_real:
            return True, f"✅ Impresora Fiscal Detectada: {printer_name}\nModo: FISCAL REAL (comandos propietarios habilitados)"
        else:
            return True, (
                f"⚠️ Modo Fiscal SIMULADO: {printer_name}\n"
                f"La impresora no es un modelo fiscal certificado.\n"
                f"Para facturación legal, configure una Hasar 320F o Epson TM-H6000."
            )


printer_manager = PosPrinter()

