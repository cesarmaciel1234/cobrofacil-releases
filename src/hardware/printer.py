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

def _impresora_cajero_activo():
    """Tiketera/cajón según CajeroActivo (1 titular, 2 auxiliar tras F8+PIN)."""
    try:
        from src.cajero.cajero_activo import CajeroActivo
        destino = CajeroActivo.get_drawer_target()
        if destino:
            return destino
    except Exception:
        pass
    return config.get('ticket_printer', config.get('printer_name', ''))


def _fecha_ord_movimiento(mov):
    return str((mov or {}).get("fecha") or "").split(".")[0].strip()


def _ordenar_movimientos_cronologico(movimientos):
    """Ordena movimientos de cuenta del más antiguo al más reciente."""
    movs = list(movimientos or [])
    if len(movs) < 2:
        return movs
    orden_desc = _fecha_ord_movimiento(movs[0]) > _fecha_ord_movimiento(movs[-1])
    return [
        m
        for _, m in sorted(
            enumerate(movs),
            key=lambda par: (_fecha_ord_movimiento(par[1]), -par[0] if orden_desc else par[0]),
        )
    ]


def resumen_corte_cuenta(movimientos, deuda_actual):
    """Calcula los cierres en $0.00 y el alcance de deuda actual sobre movimientos."""
    movs = _ordenar_movimientos_cronologico(movimientos)
    saldado_indices = set()
    for idx, mov in enumerate(movs):
        t_up = str(mov.get("etiqueta") or mov.get("tipo") or "").strip().upper()
        if not (t_up.startswith("COBRO") or t_up.startswith("ABONO")):
            continue
        s_raw = mov.get("saldo_resultante")
        if s_raw is None:
            continue
        try:
            if abs(float(s_raw)) <= 0.01:
                saldado_indices.add(idx)
        except (TypeError, ValueError):
            pass

    ultimo_saldado_idx = None
    try:
        deuda_num = float(deuda_actual or 0)
    except (TypeError, ValueError):
        deuda_num = 0.0
    if deuda_num > 0.009:
        prev_zeros = [i for i in saldado_indices if i < len(movs) - 1]
        if prev_zeros:
            ultimo_saldado_idx = max(prev_zeros)

    tiene_corte = ultimo_saldado_idx is not None
    cant_actual = (len(movs) - ultimo_saldado_idx - 1) if tiene_corte else len(movs)
    return {
        "movs": movs,
        "saldado_indices": saldado_indices,
        "ultimo_saldado_idx": ultimo_saldado_idx,
        "tiene_corte": tiene_corte,
        "cant_actual": cant_actual,
        "cant_total": len(movs),
    }

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
DOUBLE_HW_ON = ESC + b'\x21\x30'
DOUBLE_HW_OFF = ESC + b'\x21\x00'
DOUBLE_HEIGHT_ON = ESC + b'\x21\x10'
DOUBLE_HEIGHT_OFF = ESC + b'\x21\x00'
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
        self.header_dir = config.get('business_address', 'Direccion Local')
        self.header_tel = config.get('business_phone', '')
        self._last_serial_error_time = 0.0

    def _send_raw_data(self, raw_data, printer_name_override=None):
        """ Envía bytes RAW a la impresora (Windows Spooler o Serial Directo). """
        # Prioridad: override > printer_name (si está set) > config
        p_name = printer_name_override
        if not p_name:
            p_name = self.printer_name if self.printer_name else config.get('ticket_printer', config.get('printer_name', ''))

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

    def cortar_papel(self, printer_name_override=None):
        """ Envía el comando ESC/POS para cortar el papel sin imprimir texto. """
        p_name = printer_name_override or _impresora_cajero_activo()
        logger.info(f"Enviando señal de corte de papel a {p_name}...")
        self._send_raw_data(CUT_PAPER, p_name)

    def abrir_cajon(self, printer_name_override=None):
        """ Envía el comando ESC/POS estándar para patear el cajón de dinero. """
        # Prioridad: override > printer_name (si está set) > config > CajeroActivo
        p_name = printer_name_override
        if not p_name:
            p_name = self.printer_name if self.printer_name else _impresora_cajero_activo()
        logger.info(f"Enviando señal de apertura a {p_name}...")

        # Seleccionar pin (0=Pin 2, 1=Pin 5)
        pin = config.get("drawer_kick_pin", 0)
        comando = KICK_DRAWER_P5 if pin == 1 else KICK_DRAWER

        # Si es 3nstar o requiere reporte proactivo, enviamos GS a 1
        if config.get("printer_3nstar_mode", False):
            comando = GS_A_1 + comando

        ok = self._send_raw_data(comando, printer_name_override=p_name)
        try:
            from src.notificaciones.motor.estado import publicar

            publicar("cajon", "💵 CAJÓN ABIERTO", segundos=12)
        except Exception:
            pass
        return ok

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
        from src.base_de_datos.database import db_manager

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

    def imprimir_ticket_venta(self, num_venta, items, total, pago, cambio, abrir_cajon=True, estado='COMPLETADA', discount_amount=0, surcharge_amount=0, cajero='', cajero_secundario='', segunda_tiketera=False, metodo_pago='Efectivo', force_fiscal=False, cliente_nombre=None, saldo_anterior=None, saldo_disponible=None, abono_cuenta=0.0, mensaje_extra_condiciones=None):

        """ Formatea e imprime un ticket de venta. Soporta dos cajeros y dos tiketeras. """

        afip_global_enabled = config.get("facturacion_afip_global", False)
        
        metodo_clean = str(metodo_pago).strip().upper()
        is_credito = metodo_clean in ("FIADO", "CLIENTES", "CUENTA CORRIENTE")
        is_digital = metodo_clean in ("TARJETA", "CREDITO", "DEBITO", "TRANSFERENCIA", "TRANSF.", "TRANSF", "QR", "MIXTO")
        
        should_use_afip = False
        if not is_credito and afip_global_enabled:
            should_use_afip = force_fiscal or is_digital or self._should_route_fiscal(metodo_pago)

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
                from src.afip.facturacion_service import FacturacionService
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

        from src.hardware.constructor_ticket.constructor import ConstructorTicketVenta

        config_drawer_pin = config.get("drawer_kick_pin", 0)
        config_3nstar = config.get("printer_3nstar_mode", False)

        ticket_bytes = ConstructorTicketVenta.construir(
            empresa=self.header_empresa,
            cuit=self.header_cuit,
            telefono=self.header_tel,
            direccion=self.header_dir,
            num_venta=num_venta,
            items=items,
            total=total,
            pago=pago,
            cambio=cambio,
            estado=estado,
            discount_amount=discount_amount,
            surcharge_amount=surcharge_amount,
            cajero=cajero,
            cajero_secundario=cajero_secundario,
            metodo_pago=metodo_pago,
            cliente_nombre=cliente_nombre,
            saldo_anterior=saldo_anterior,
            saldo_disponible=saldo_disponible,
            abono_cuenta=abono_cuenta,
            mensaje_extra_condiciones=mensaje_extra_condiciones,
            factura_electronica_data=factura_electronica_data,
            abrir_cajon=abrir_cajon,
            config_drawer_pin=config_drawer_pin,
            config_3nstar=config_3nstar,
            calcular_iva_func=self._calcular_iva_desagregado
        )
        data = bytearray(ticket_bytes)

        p_principal = _impresora_cajero_activo()
        result = self._send_raw_data(bytes(data), printer_name_override=p_principal)

        # Copia en la otra estación solo si se pidió explícitamente (no duplicar al cobrar auxiliar)
        if segunda_tiketera:
            otra = config.get('ticket_printer_2', '') if p_principal == config.get('ticket_printer', '') else config.get('ticket_printer', '')
            if otra and otra != p_principal:
                self._send_raw_data(bytes(data), printer_name_override=otra)

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

        p_principal = _impresora_cajero_activo()
        result = self._send_raw_data(bytes(data), printer_name_override=p_principal)
        return result

    def imprimir_ticket_saldos_compra(self, cliente_nombre, saldo_anterior, compra, saldo_disponible):
        """Ticket extra automático para la VENTA por Cuenta Corriente/Fiado. 
        Muestra saldo anterior, compra, y el crédito disponible (o saldo actual)"""
        def linea(etiqueta, valor):
            monto = f"${float(valor or 0):,.2f}"
            hueco = 32 - len(etiqueta) - len(monto)
            if hueco < 1:
                return f"{etiqueta}\n{monto}\n"
            return f"{etiqueta}{' ' * hueco}{monto}\n"

        data = bytearray()
        data.extend(ESC + b'\x40')
        data.extend(ALIGN_CENTER)
        data.extend(BOLD_ON)
        data.extend(f"{self.header_empresa}\n".encode('cp850', errors='replace'))
        data.extend(f"{cliente_nombre}\n".encode('cp850', errors='replace'))
        data.extend(b"CREDITO\n")
        data.extend(BOLD_OFF)
        data.extend(b"--------------------------------\n")
        data.extend(ALIGN_LEFT)
        data.extend(linea("Saldo anterior", saldo_anterior).encode('cp850', errors='replace'))
        data.extend(linea("Compra", compra).encode('cp850', errors='replace'))
        data.extend(BOLD_ON)
        data.extend(linea("Saldo disponible", saldo_disponible).encode('cp850', errors='replace'))
        data.extend(BOLD_OFF)
        data.extend(b"--------------------------------\n")
        data.extend(b"\n\n\n\n\n")
        data.extend(CUT_PAPER)

        p_principal = _impresora_cajero_activo()
        return self._send_raw_data(bytes(data), printer_name_override=p_principal)

    def imprimir_saldo_fiado(self, cliente_nombre, saldo_anterior, credito, saldo_restante):
        """Ticket del cajero: saldo anterior, crǸdito y saldo restante."""
        from src.config import config
        config._load_config()
        ancho_mm = config.get("printer_paper_width_mm", 58)
        columnas = 48 if ancho_mm == 80 else 32

        def linea(etiqueta, valor):
            monto = f"${float(valor or 0):,.2f}"
            hueco = columnas - len(etiqueta) - len(monto)
            if hueco < 1:
                return f"{etiqueta}\n{monto}\n"
            return f"{etiqueta}{' ' * hueco}{monto}\n"

        data = bytearray()
        data.extend(ESC + b'\x40')
        data.extend(ALIGN_CENTER)
        data.extend(BOLD_ON)
        data.extend(f"{self.header_empresa}\n".encode('cp850', errors='replace'))
        data.extend(b"\n")
        data.extend(b"*** ABONO DE CUENTA ***\n")
        data.extend(f"Cliente: {cliente_nombre}\n".encode('cp850', errors='replace'))
        data.extend(b"\n")
        data.extend(BOLD_OFF)
        data.extend((b"-" * columnas) + b"\n")
        data.extend(ALIGN_LEFT)
        data.extend(linea("Deuda Anterior", saldo_anterior).encode('cp850', errors='replace'))
        data.extend(linea("Abono Entregado", credito).encode('cp850', errors='replace'))
        data.extend((b"-" * columnas) + b"\n")
        data.extend(BOLD_ON)
        data.extend(linea("SALDO ACTUAL", saldo_restante).encode('cp850', errors='replace'))
        data.extend(BOLD_OFF)
        data.extend((b"-" * columnas) + b"\n")
        
        # Uso del nuevo Motor Empresarial para condiciones globales
        try:
            from src.motor_condiciones.motor_central import MotorCondiciones
            import textwrap
            
            # Si el abono es 0, es un Estado de Cuenta. Si es mayor a 0, es un Abono.
            subcontexto = "abono" if float(credito or 0) > 0.009 else "estado_cuenta"
            condiciones = MotorCondiciones.obtener_condiciones(
                "credito", subcontexto=subcontexto, 
                saldo_anterior=float(saldo_anterior or 0), 
                monto_actual=float(credito or 0),
                cliente_nombre=cliente_nombre
            )
            data.extend(b"\n")
            data.extend(ALIGN_CENTER)
            data.extend(b"\n".join(line.encode('cp850', errors='replace') for line in textwrap.wrap(condiciones, columnas)))
            data.extend(b"\n")
        except Exception as e:
            import logging
            logging.getLogger("PunPro").error(f"Fallo al cargar motor_condiciones en ticket fiado: {e}")

        data.extend(b"\n\n\n\n")
        data.extend(CUT_PAPER)

        p_principal = _impresora_cajero_activo()
        result = self._send_raw_data(bytes(data), printer_name_override=p_principal)
        return result

    def imprimir_historial_cuenta(self, cliente, movimientos, totales, solo_deuda_actual=False):
        """Estado de cuenta térmico (completo o solo deuda vigente). Admin y Fiado."""
        import re
        from src.config import config

        config._load_config()
        ancho_mm = config.get("printer_paper_width_mm", 58)
        columnas = 48 if ancho_mm == 80 else 32
        ficha = dict(cliente or {})
        nombre = str(ficha.get("nombre") or "Cliente").strip() or "Cliente"
        dni_raw = str(ficha.get("dni") or "").strip()
        dni = "" if not dni_raw or dni_raw in ("—", "-") else dni_raw
        telefono = str(ficha.get("telefono") or "").strip()
        if telefono in ("—", "-"):
            telefono = ""
        try:
            deuda = float(ficha.get("deuda_actual") or 0)
        except (TypeError, ValueError):
            deuda = 0.0
        try:
            limite = float(ficha.get("limite_credito") or 0)
        except (TypeError, ValueError):
            limite = 0.0
        tot = dict(totales or {})
        corte_info = resumen_corte_cuenta(movimientos, deuda)
        movs = corte_info["movs"]
        saldado_indices = corte_info["saldado_indices"]
        ultimo_saldado_idx = corte_info["ultimo_saldado_idx"]

        solo_periodo_corte = bool(solo_deuda_actual and ultimo_saldado_idx is not None)
        if solo_periodo_corte:
            movs_cuerpo = movs[ultimo_saldado_idx + 1 :]
            offset_idx = ultimo_saldado_idx + 1
        elif solo_deuda_actual and deuda <= 0.009 and saldado_indices:
            ult_cero = max(saldado_indices)
            movs_cuerpo = [movs[ult_cero]]
            offset_idx = ult_cero
        else:
            movs_cuerpo = movs
            offset_idx = 0

        if "mantenimiento" in tot:
            try:
                mantenimiento = float(tot.get("mantenimiento") or 0)
            except (TypeError, ValueError):
                mantenimiento = 0.0
        elif deuda > 0.009:
            mantenimiento = sum(
                float(m.get("interes_acumulado") or 0)
                for m in movs
                if str(m.get("tipo") or "").strip().upper() == "CARGO"
                and not m.get("es_interes")
                and not m.get("borrado")
                and not m.get("cancelado")
            )
        else:
            mantenimiento = 0.0
        if deuda <= 0.009:
            mantenimiento = 0.0
        total_estimado = deuda + mantenimiento

        def linea(etiqueta, valor, texto_val=None):
            monto = texto_val if texto_val is not None else f"${float(valor or 0):,.2f}"
            hueco = columnas - len(etiqueta) - len(monto)
            if hueco < 1:
                return f"{etiqueta}\n{monto}\n"
            return f"{etiqueta}{' ' * hueco}{monto}\n"

        def centrado_marca(texto):
            t = f" {texto.strip()} "
            if len(t) >= columnas:
                return t[:columnas] + "\n"
            izq = (columnas - len(t)) // 2
            der = columnas - len(t) - izq
            return f"{'-' * izq}{t}{'-' * der}\n"

        def fecha_corta(fecha):
            f = str(fecha or "").split(".")[0]
            if len(f) >= 16 and f[4] == "-" and f[7] == "-":
                return f"{f[8:10]}/{f[5:7]} {f[11:16]}"
            return f[:16]

        def fecha_dia_corta(fecha, con_anio=False):
            f = str(fecha or "").split(".")[0].strip()
            if len(f) >= 10 and f[4] == "-" and f[7] == "-":
                base = f"{f[8:10]}/{f[5:7]}"
                return f"{base}/{f[2:4]}" if con_anio else base
            return ""

        def rango_periodo(lista_movs):
            fechas = [fecha_dia_corta(m.get("fecha"), con_anio=True) for m in lista_movs]
            fechas = [f for f in fechas if f]
            if not fechas:
                return ""
            if fechas[0] == fechas[-1]:
                return fechas[0]
            return f"{fechas[0]} al {fechas[-1]}"

        def recortar(texto, max_len):
            t = " ".join(str(texto or "").split())
            if len(t) <= max_len:
                return t
            return t[: max(0, max_len - 1)] + "."

        def nota_movimiento(mov, marca_tipo, es_ticket):
            if es_ticket:
                return ""
            desc = " ".join(str(mov.get("descripcion") or "").split())
            if not desc or desc in ("—", "-"):
                return ""
            low = desc.lower()
            if marca_tipo == "COBRO":
                m_met = re.search(r"\(([^)]+)\)", desc)
                txt_abono = m_met.group(1).strip() if m_met else desc
                txt_abono = re.sub(r":\s*F9\s*MANUAL", "", txt_abono, flags=re.IGNORECASE)
                txt_abono = re.sub(r"F9\s*MANUAL", "Manual", txt_abono, flags=re.IGNORECASE).strip()
                txt_abono = txt_abono.replace("\ufffd", "")
                return "" if txt_abono.lower() in ("abono a cuenta", "cobro", "manual") else txt_abono
            if marca_tipo.startswith("CARGO"):
                if low.startswith("cargo manual"):
                    return ""
                return desc.replace("\ufffd", "")
            return desc.replace("\ufffd", "")

        def fmt_monto(monto_val, signo="", parentesis=False):
            base = f"${abs(float(monto_val or 0)):,.2f}"
            if parentesis:
                return f"({base})"
            return f"{signo}{base}" if signo else base

        sep_simple = (b"-" * columnas) + b"\n"
        sep_doble = (b"=" * columnas) + b"\n"
        ahora = datetime.now()

        data = bytearray()
        data.extend(ESC + b"\x40")
        data.extend(ALIGN_CENTER)
        data.extend(BOLD_ON)
        data.extend(f"{self.header_empresa}\n".encode("cp850", errors="replace"))
        data.extend(BOLD_OFF)
        dir_txt = " ".join(str(self.header_dir or "").split())
        if dir_txt and dir_txt.lower() != "direccion local":
            data.extend(f"{recortar(dir_txt, columnas)}\n".encode("cp850", errors="replace"))
        tel_txt = " ".join(str(self.header_tel or "").split())
        if tel_txt:
            data.extend(f"Tel: {recortar(tel_txt, columnas - 5)}\n".encode("cp850", errors="replace"))
        data.extend(BOLD_ON)
        data.extend(b"ESTADO DE CUENTA\n")
        data.extend(BOLD_OFF)
        data.extend(b"DOCUMENTO NO FISCAL\n")
        data.extend(f"{ahora.strftime('%d/%m/%Y %H:%M')}\n".encode("cp850", errors="replace"))
        data.extend(sep_doble)
        data.extend(ALIGN_LEFT)
        data.extend(BOLD_ON)
        data.extend(f"Cliente: {recortar(nombre, columnas - 9)}\n".encode("cp850", errors="replace"))
        data.extend(BOLD_OFF)
        if dni:
            data.extend(f"DNI: {recortar(dni, columnas - 5)}\n".encode("cp850", errors="replace"))
        if telefono:
            data.extend(f"Tel: {recortar(telefono, columnas - 5)}\n".encode("cp850", errors="replace"))
        if limite > 0.009:
            data.extend(linea("Limite", limite).encode("cp850", errors="replace"))
            disponible = max(0.0, limite - deuda)
            data.extend(linea("Disponible", disponible).encode("cp850", errors="replace"))
        periodo_txt = rango_periodo(movs_cuerpo)
        if periodo_txt:
            data.extend(f"Periodo: {recortar(periodo_txt, columnas - 9)}\n".encode("cp850", errors="replace"))

        cant_ventas = cant_manuales = cant_cobros = 0
        vig_cargos = vig_cobros = 0.0
        vig_cant_cargos = vig_cant_cobros = 0

        data.extend(sep_doble)
        data.extend(BOLD_ON)
        if solo_periodo_corte:
            data.extend(f"DEUDA ACTUAL ({len(movs_cuerpo)})\n".encode("cp850", errors="replace"))
        elif ultimo_saldado_idx is not None:
            cant_saldado = ultimo_saldado_idx + 1
            data.extend(f"HISTORIAL SALDADO ({cant_saldado})\n".encode("cp850", errors="replace"))
        else:
            data.extend(f"MOVIMIENTOS ({len(movs_cuerpo)})\n".encode("cp850", errors="replace"))
        data.extend(BOLD_OFF)
        data.extend(sep_simple)

        fecha_corte_corta = (
            fecha_dia_corta(movs[ultimo_saldado_idx].get("fecha"))
            if ultimo_saldado_idx is not None
            else ""
        )

        for pos, mov in enumerate(movs_cuerpo):
            idx = offset_idx + pos
            tipo = str(mov.get("etiqueta") or mov.get("tipo") or "").strip().upper()
            borrado = bool(mov.get("borrado"))
            cancelado = bool(mov.get("cancelado"))
            inactivo = borrado or cancelado
            if tipo.startswith("VENTA"):
                marca = "VENTA"
            elif tipo.startswith("CARGO"):
                marca = "CARGO"
            elif tipo.startswith("COBRO") or tipo.startswith("ABONO"):
                marca = "COBRO"
            elif "ANUL" in tipo:
                marca = "ANULA"
            else:
                marca = recortar(tipo, 7) or "MOV"

            try:
                monto = float(mov.get("monto") or 0)
            except (TypeError, ValueError):
                monto = 0.0

            raw_venta_id = str(mov.get("venta_id") or "").strip()
            es_venta = bool(raw_venta_id and raw_venta_id not in ("0", "None"))
            if not inactivo:
                if marca == "COBRO":
                    cant_cobros += 1
                    if ultimo_saldado_idx is not None and idx > ultimo_saldado_idx:
                        vig_cobros += monto
                        vig_cant_cobros += 1
                elif marca == "VENTA" or (marca == "CARGO" and es_venta):
                    cant_ventas += 1
                    if ultimo_saldado_idx is not None and idx > ultimo_saldado_idx:
                        vig_cargos += monto
                        vig_cant_cargos += 1
                elif marca == "CARGO":
                    cant_manuales += 1
                    if ultimo_saldado_idx is not None and idx > ultimo_saldado_idx:
                        vig_cargos += monto
                        vig_cant_cargos += 1

            if borrado:
                marca_vis = f"{marca} [BORRADO]"
            elif cancelado:
                marca_vis = f"{marca} [ANULADA]"
            else:
                marca_vis = marca

            ref = str(mov.get("referencia") or mov.get("venta_id") or "").strip()
            if ref in ("—", "-"):
                ref = ""
            if ref and not ref.startswith("#") and not ref.upper().startswith("COB"):
                ref = f"#{ref}"
            f_txt = fecha_corta(mov.get("fecha"))
            es_ticket = es_venta or ref.startswith("#")

            nota = nota_movimiento(mov, marca, es_ticket)
            if not ref and marca == "CARGO":
                ref = nota or "Cargo a mano"
                nota = ""

            if ref:
                ref_txt = recortar(ref, max(1, columnas - len(f_txt) - 2))
                encabezado = f"{f_txt}  {ref_txt}"
            else:
                encabezado = f_txt[:columnas]

            data.extend(BOLD_ON)
            data.extend((encabezado + "\n").encode("cp850", errors="replace"))
            data.extend(BOLD_OFF)

            if inactivo:
                monto_txt = fmt_monto(monto, parentesis=True)
            elif marca in ("COBRO", "ANULA"):
                monto_txt = fmt_monto(monto, signo="-")
            else:
                monto_txt = fmt_monto(monto, signo="+")
            data.extend(linea(f"  {marca_vis}", monto, texto_val=monto_txt).encode("cp850", errors="replace"))

            if nota:
                data.extend(f"  {recortar(nota, columnas - 2)}\n".encode("cp850", errors="replace"))

            if idx in saldado_indices:
                data.extend(centrado_marca("Cuenta en $0.00").encode("cp850", errors="replace"))
                if not solo_periodo_corte and ultimo_saldado_idx is not None and idx == ultimo_saldado_idx:
                    cant_vig = len(movs) - idx - 1
                    data.extend(sep_doble)
                    data.extend(BOLD_ON)
                    data.extend(f"DEUDA ACTUAL ({cant_vig})\n".encode("cp850", errors="replace"))
                    data.extend(BOLD_OFF)
                    data.extend(sep_simple)
                elif pos < len(movs_cuerpo) - 1:
                    data.extend(b"\n")
            elif pos < len(movs_cuerpo) - 1:
                data.extend(b"\n")

        data.extend(sep_doble)
        data.extend(BOLD_ON)
        data.extend(b"RESUMEN DEL PERIODO\n" if solo_periodo_corte else b"RESUMEN DE CUENTA\n")
        data.extend(BOLD_OFF)
        data.extend(sep_simple)

        if solo_periodo_corte:
            etq_ant = f"Saldo ant. ({fecha_corte_corta})" if fecha_corte_corta else "Saldo anterior"
            data.extend(linea(etq_ant, 0.0).encode("cp850", errors="replace"))
            data.extend(linea(f"Cargos periodo ({vig_cant_cargos})", vig_cargos).encode("cp850", errors="replace"))
            if vig_cobros > 0.009:
                data.extend(
                    linea(
                        f"Cobros periodo ({vig_cant_cobros})",
                        vig_cobros,
                        texto_val=fmt_monto(vig_cobros, signo="-"),
                    ).encode("cp850", errors="replace")
                )
        else:
            ventas_tot = float(tot.get("ventas") or 0)
            manuales_tot = float(tot.get("manuales") or 0)
            abonos_tot = float(tot.get("abonos") if tot.get("abonos") is not None else (tot.get("cobros") or 0))
            if ventas_tot > 0.009 or manuales_tot > 0.009:
                if ventas_tot > 0.009:
                    etq_v = f"Ventas ({cant_ventas})" if cant_ventas else "Ventas"
                    data.extend(linea(etq_v, ventas_tot).encode("cp850", errors="replace"))
                if manuales_tot > 0.009:
                    etq_m = f"Cargos a mano ({cant_manuales})" if cant_manuales else "Cargos a mano"
                    data.extend(linea(etq_m, manuales_tot).encode("cp850", errors="replace"))
            else:
                data.extend(linea("Total fiado", tot.get("cargos", 0)).encode("cp850", errors="replace"))
            etq_a = f"Cobros ({cant_cobros})" if cant_cobros else "Total abonado"
            abonos_txt = fmt_monto(abonos_tot, signo="-") if abonos_tot > 0.009 else "$0.00"
            data.extend(linea(etq_a, abonos_tot, texto_val=abonos_txt).encode("cp850", errors="replace"))
            if float(tot.get("borrados") or 0) > 0.009:
                data.extend(linea("Borrados", tot.get("borrados", 0)).encode("cp850", errors="replace"))
            if float(tot.get("cancelados") or 0) > 0.009:
                data.extend(linea("Cancelados F3", tot.get("cancelados", 0)).encode("cp850", errors="replace"))
            if ultimo_saldado_idx is not None and abs((vig_cargos - vig_cobros) - deuda) <= 0.05:
                data.extend(sep_simple)
                data.extend(linea("Saldo anterior", 0.0).encode("cp850", errors="replace"))
                data.extend(linea(f"Cargos periodo ({vig_cant_cargos})", vig_cargos).encode("cp850", errors="replace"))
                if vig_cobros > 0.009:
                    data.extend(
                        linea(
                            f"Cobros periodo ({vig_cant_cobros})",
                            vig_cobros,
                            texto_val=fmt_monto(vig_cobros, signo="-"),
                        ).encode("cp850", errors="replace")
                    )

        data.extend(sep_simple)
        if mantenimiento > 0.009:
            data.extend(linea("Capital actual", deuda).encode("cp850", errors="replace"))
            data.extend(linea("Mantenimiento", 0, f"+${mantenimiento:,.2f}").encode("cp850", errors="replace"))
            data.extend(BOLD_ON)
            data.extend(DOUBLE_HEIGHT_ON)
            data.extend(linea("TOTAL ESTIMADO", total_estimado).encode("cp850", errors="replace"))
            data.extend(DOUBLE_HEIGHT_OFF)
            data.extend(BOLD_OFF)
        else:
            data.extend(BOLD_ON)
            data.extend(DOUBLE_HEIGHT_ON)
            if deuda < -0.009:
                data.extend(linea("SALDO A FAVOR", 0, f"+${abs(deuda):,.2f}").encode("cp850", errors="replace"))
            else:
                data.extend(linea("SALDO ACTUAL", deuda).encode("cp850", errors="replace"))
            data.extend(DOUBLE_HEIGHT_OFF)
            data.extend(BOLD_OFF)
        data.extend(sep_doble)
        data.extend(ALIGN_CENTER)
        if mantenimiento > 0.009:
            data.extend(f"* Valido al {ahora.strftime('%d/%m/%Y')} *\n".encode("cp850", errors="replace"))
        data.extend(b"Gracias\n\n\n\n")
        data.extend(CUT_PAPER)

        p_principal = _impresora_cajero_activo()
        return self._send_raw_data(bytes(data), printer_name_override=p_principal)

    def imprimir_ticket_z(self, usuario, fisico, dif, datos_z):
        """Imprime el ticket de cierre de caja (Reporte Z) usando el módulo especializado.

        Args:
            usuario: Nombre del cajero
            fisico: Efectivo contado en caja
            dif: Diferencia (físico - esperado)
            datos_z: Diccionario con todos los datos del cierre

        Returns:
            True si se imprimió correctamente, False en caso contrario
        """
        try:
            from src.hardware.ticket_z import formatear_ticket_z
        except ImportError:
            from hardware.ticket_z import formatear_ticket_z

        # Generar contenido del ticket
        ticket_bytes = formatear_ticket_z(usuario, fisico, dif, datos_z)

        # Enviar a impresora principal
        p_principal = config.get('ticket_printer', config.get('printer_name', ''))
        result = self._send_raw_data(ticket_bytes, printer_name_override=p_principal)

        # Copia de seguridad en la Segunda Tiketera (Control de Cajeros Simultáneos)
        if datos_z.get('segunda_tiketera', False):
            printer2 = config.get('ticket_printer_2', '')
            if printer2:
                self._send_raw_data(ticket_bytes, printer_name_override=printer2)

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

    def imprimir_volumen_articulos(self, filas, periodo, tickets) -> bool:
        """Desglose del día o del mes, al ancho configurado (58 mm o 80 mm)."""
        from src.historial_ventas.ticket_volumen import armar_ticket_volumen

        config._load_config()
        raw = armar_ticket_volumen(filas, periodo, tickets)
        return self._send_raw_data(bytes(raw), printer_name_override=_impresora_cajero_activo())

    def imprimir_etiquetas_gondola(self, raw_bytes: bytes, printer_name_override=None) -> bool:
        """Envía lote de etiquetas de góndola térmicas con corte a la impresora configurada."""
        p_name = printer_name_override or _impresora_cajero_activo()
        logger.info(f"Enviando {len(raw_bytes)} bytes de etiquetas de góndola a {p_name or 'Simulación'}...")
        return self._send_raw_data(raw_bytes, printer_name_override=p_name)


printer_manager = PosPrinter()
