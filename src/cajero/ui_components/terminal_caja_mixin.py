from src.utils.qt_compat import qt_exec
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem, QAbstractItemView
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from src.base_de_datos.database import db_manager
from src.config import config
from src.cajero.paso5_terminal import parse_float_safe, fmt_moneda_sin_centavos
import logging
logger = logging.getLogger(__name__)
try:
    from src.ui_components.toast import Toast
except:
    pass

class TerminalCajaMixin:
    def actualizar_totales(self):
        # Refrescar en cascada los estilos para que el destaque azul y el subtotal verde agua se muevan dinámicamente
        for i in range(self.tabla.rowCount()):
            self._reaplicar_estilo_fila(i)
            
        total = sum(parse_float_safe(self.tabla.item(i, 5).text()) for i in range(self.tabla.rowCount()))
        cant = sum(float(self.tabla.item(i, 3).text()) for i in range(self.tabla.rowCount()))
        total_desc = sum(parse_float_safe(self.tabla.item(i, 4).text()) for i in range(self.tabla.rowCount()))
        
        # El total grande vuelve a usar el formato sin centavos con comas de miles
        total_str = fmt_moneda_sin_centavos(total)
        self.lbl_total_val.setText(total_str)
        self.lbl_cant_val.setText(f"{int(cant)}")
        
        # Notificar al Chatbot Espía (Che Lobo)
        if self.en_venta and total > 0:
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                msg = f"TICKET_UPDATE|{total_str}".encode('utf-8')
                sock.sendto(msg, ("127.0.0.1", 45680))
                sock.close()
            except: pass
        
        # Si estamos agregando items, limpiamos los "Pagos" y "Cambio" de la venta anterior
        if self.en_venta:
            self.lbl_side_cant.setText(f"CANTIDAD:    {cant:>10.2f}" if cant % 1 != 0 else f"CANTIDAD:    {int(cant):>10,}")
            total_sin = fmt_moneda_sin_centavos(total)
            desc_sin = fmt_moneda_sin_centavos(total_desc)
            if total_desc > 0:
                self.lbl_side_total.setText(f"TOTAL VENTA: {total_sin:>10}\nAHORRO OFER: {desc_sin:>10}")
            else:
                self.lbl_side_total.setText(f"TOTAL VENTA: {total_sin:>10}")
            self.lbl_side_pagos.setText(f"PAGOS:       {'0':>10}")
            self.lbl_side_cambio.setText(f"CAMBIO:      {'0':>10}")
            self.lbl_side_cambio.setStyleSheet("font-size: 14px; color: #475569; font-weight: 800; font-family: 'Consolas', monospace;")
            
        # Gatillar la animación interactiva de ahorro total
        self.animar_ahorro(total_desc)
    def animar_ahorro(self, nuevo_ahorro):
        """ 
        Animación interactiva premium tipo 'saldo ascendente' (+100).
        Incrementa el valor del ahorro de forma asíncrona y fluida.
        """
        if not hasattr(self, 'current_ahorro'):
            self.current_ahorro = 0.0
            
        # Detener respiración si el ahorro es 0 o está cambiando
        if hasattr(self, '_respiracion_anim') and self._respiracion_anim:
            self._respiracion_anim.stop()
            self._respiracion_anim = None
            
        if nuevo_ahorro <= 0:
            self.current_ahorro = 0.0
            self.lbl_ahorro_val.hide()
            return
            
        self.lbl_ahorro_val.show()
        
        # Color y tamaño de impacto (Naranja vibrante para el incremento)
        self.lbl_ahorro_val.setStyleSheet("font-size: 48px; color: #FF4500; font-weight: 900; border: none;")
        
        from src.utils.qt_compat import VariantFloatAnimation
        if hasattr(self, '_ahorro_anim') and self._ahorro_anim:
            self._ahorro_anim.stop()
            
        self._ahorro_anim = VariantFloatAnimation(self)
        self._ahorro_anim.setStartValue(self.current_ahorro)
        self._ahorro_anim.setEndValue(nuevo_ahorro)
        self._ahorro_anim.setDuration(2000) # 2000ms (2.0s) de animación suave e impactante
        
        def on_value_changed(value):
            self.lbl_ahorro_val.setText(f"🎉 +${value:,.2f}")
            
        def on_finished():
            self.current_ahorro = nuevo_ahorro
            self.lbl_ahorro_val.setText(f"🎉 AHORRAS: ${nuevo_ahorro:,.2f}")
            # Al terminar el conteo, iniciar el bucle continuo de respiración (zoom + glow flash)
            self.iniciar_respiracion_ahorro()
            
        self._ahorro_anim.valueChanged.connect(on_value_changed)
        self._ahorro_anim.finished.connect(on_finished)
        self._ahorro_anim.start()
    def iniciar_respiracion_ahorro(self):
        """
        Inicia un efecto continuo de respiración (zoom + brillo intermitente) 
        en la etiqueta de ahorro para que se vea súper llamativa y orgánica.
        """
        from src.utils.qt_compat import VariantFloatAnimation, QEasingCurve
        
        if hasattr(self, '_respiracion_anim') and self._respiracion_anim:
            return
            
        self._respiracion_anim = VariantFloatAnimation(self)
        self._respiracion_anim.setStartValue(0.0)
        self._respiracion_anim.setEndValue(1.0)
        self._respiracion_anim.setDuration(1500) # Ciclo suave de 1.5 segundos
        self._respiracion_anim.setEasingCurve(QEasingCurve.SineCurve)
        self._respiracion_anim.setLoopCount(-1) # Bucle infinito
        
        def on_step(t):
            # Normalizar el valor del seno (-1.0 a 1.0) a un rango limpio de 0.0 a 1.0
            val_norm = (t + 1.0) / 2.0
            
            # 1. Efecto Zoom: Oscila suavemente entre 36px y 46px
            size = int(36 + (10 * val_norm))
            
            # 2. Efecto Brillo (Glow Flash): El radio va de 10 a 30 y la opacidad de 80 a 230
            glow_radius = int(10 + (20 * val_norm))
            alpha = int(80 + (150 * val_norm))
            
            # Aplicar estilos con naranja vibrante premium (#FF4500)
            self.lbl_ahorro_val.setStyleSheet(f"font-size: {size}px; color: #FF4500; font-weight: 900; border: none;")
            
            if hasattr(self, 'ahorro_glow') and self.ahorro_glow:
                self.ahorro_glow.setBlurRadius(glow_radius)
                self.ahorro_glow.setColor(QColor(255, 69, 0, alpha))
                
        self._respiracion_anim.valueChanged.connect(on_step)
        self._respiracion_anim.start()
    def abrir_retiro_efectivo(self):
        """Abre el panel rápido de retiro de efectivo de caja (F5)."""
        from src.config import config
        c_id = config.get("caja_id", 1)
        efectivo = db_manager.get_efectivo_en_caja(c_id)
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.setGraphicsEffect(blur)
        
        dlg = DialogoRetiroEfectivo(efectivo, parent=self)
        if qt_exec(dlg) and dlg.monto_retirado > 0:
            # Solicitar PIN de confirmación del operador activo
            pin_dlg = DialogoPIN(CajeroActivo.nombre, parent=self)
            if qt_exec(pin_dlg) and pin_dlg.ok:
                monto = dlg.monto_retirado
                motivo = getattr(dlg, "motivo", "Retiro rápido de efectivo en terminal")
                usuario = CajeroActivo.nombre
                from src.config import config
                c_id = config.get("caja_id", 1)
                query = "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id) VALUES ('RETIRO', ?, ?, ?, ?)"
                if db_manager.execute_non_query(query, (monto, usuario, motivo, c_id)):
                    self.flash_feedback(success=True)
                    # Marcar apertura como autorizada para el monitor de seguridad
                    self._apertura_autorizada = True
                    # Abrir cajón físicamente
                    printer_manager.abrir_cajon()
                    # Imprimir ticket de comprobante físico
                    printer_manager.imprimir_movimiento_caja('RETIRO DE EFECTIVO', monto, motivo, usuario, c_id)
                    self.monitor_cajon_bloqueante(manual=True)
                    self.check_alertas_efectivo()
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", "No se pudo registrar el retiro en la base de datos.")
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)
    def abrir_ingreso_efectivo(self):
        """Abre el panel de ingreso manual de dinero a la caja (F6)."""
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur = QGraphicsBlurEffect()
        blur.setBlurRadius(10)
        self.setGraphicsEffect(blur)
        
        dlg = DialogoIngresoEfectivo(parent=self)
        if qt_exec(dlg) and dlg.monto_ingresado > 0:
            # Solicitar PIN de confirmación del operador activo
            pin_dlg = DialogoPIN(CajeroActivo.nombre, parent=self)
            if qt_exec(pin_dlg) and pin_dlg.ok:
                monto = dlg.monto_ingresado
                motivo = getattr(dlg, "motivo", "Ingreso manual de efectivo en terminal")
                usuario = CajeroActivo.nombre
                from src.config import config
                c_id = config.get("caja_id", 1)
                
                # Novedad: Si es un abono a Fiado, procesar la deuda en DB
                if getattr(dlg, "tipo_ingreso", "") == "FIADO" and getattr(dlg, "cliente_id", None):
                    nuevo_saldo = dlg.deuda_actual - monto
                    db_manager.execute_non_query("UPDATE clientes SET deuda_actual = ? WHERE id = ?", (nuevo_saldo, dlg.cliente_id))
                    db_manager.execute_non_query(
                        "INSERT INTO cuenta_corriente (cliente_id, tipo, monto, saldo_resultante, descripcion) VALUES (?, ?, ?, ?, ?)",
                        (dlg.cliente_id, 'ABONO', monto, nuevo_saldo, 'Abono Fiado en Caja')
                    )

                query = "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id) VALUES ('INGRESO', ?, ?, ?, ?)"
                if db_manager.execute_non_query(query, (monto, usuario, motivo, c_id)):
                    self.flash_feedback(success=True)
                    # Abrir cajón físicamente
                    printer_manager.abrir_cajon()
                    # Imprimir ticket de comprobante físico
                    printer_manager.imprimir_movimiento_caja('INGRESO DE EFECTIVO', monto, motivo, usuario, c_id)
                    self.monitor_cajon_bloqueante(manual=True)
                    self.check_alertas_efectivo()
                else:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Error", "No se pudo registrar el ingreso en la base de datos.")
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)
    def finalizar_venta(self):
        # Evitar doble apertura accidental
        if hasattr(self, '_cobro_abierto') and self._cobro_abierto: return
        
        try: 
            # Como ahora el total visual no tiene decimales ni comas de miles (son puntos),
            # lo calculamos directamente de la tabla para no perder precisión
            total = sum(parse_float_safe(self.tabla.item(i, 5).text()) for i in range(self.tabla.rowCount()))
        except: return
        if total <= 0: return
        
        self._cobro_abierto = True
        items = []
        for i in range(self.tabla.rowCount()):
            it_name = self.tabla.item(i, 1)
            vendido_ia = 1 if it_name.data(Qt.UserRole) == 1 else 0
            items.append({
                "id": self.tabla.item(i, 0).text(),
                "nombre": it_name.text(),
                "precio": parse_float_safe(self.tabla.item(i, 2).text()),
                "cant": float(self.tabla.item(i, 3).text().replace(",", ".")),
                "subtotal": parse_float_safe(self.tabla.item(i, 5).text()),
                "vendido_por_carteleria": vendido_ia
            })
            
        # --- EFECTO DE DESENFOQUE CINEMÁTICO ---
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)
        
        from src.cajero.paso6_cobro import Paso6Cobro
        dlg = Paso6Cobro(total, items, self)
        dlg.descuentaso_oferta = sum(parse_float_safe(self.tabla.item(i, 4).text()) for i in range(self.tabla.rowCount()))
        
        # Ejecutamos el cobro
        qt_exec(ok = dlg)
        self._cobro_abierto = False
        
        # Quitamos el desenfoque
        self.setGraphicsEffect(None)
        
        if ok:
            # Capturar info de la venta exitosa antes de limpiar
            res = getattr(dlg, 'resultado_venta', None)
            
            # --- Auto-Destruccion de Ofertas Relampago ---
            for it in items:
                try:
                    p_id = it['id']
                    p_precio = it['precio']
                    p_cant = it['cant']
                    
                    db_prod = db_manager.execute_query("SELECT precio_oferta_relampago, limite_oferta_relampago, ventas_oferta_relampago FROM productos WHERE id=?", (p_id,))
                    if db_prod:
                        p_of_rel = db_prod[0].get('precio_oferta_relampago') or 0
                        limite = db_prod[0].get('limite_oferta_relampago') or 0
                        ventas_actuales = db_prod[0].get('ventas_oferta_relampago') or 0
                        
                        if p_of_rel > 0 and p_precio == p_of_rel:
                            nuevas_ventas = ventas_actuales + p_cant
                            
                            if limite > 0 and nuevas_ventas >= limite:
                                db_manager.execute_non_query(
                                    "UPDATE productos SET precio_oferta_relampago = 0, ventas_oferta_relampago = ? WHERE id = ?",
                                    (nuevas_ventas, p_id)
                                )
                                try:
                                    from src.ui_components.toast import Toast
                                    Toast.show_warning(self, f"⚡ Oferta Relámpago de '{it['nombre']}' agotada!")
                                except: pass
                            else:
                                db_manager.execute_non_query(
                                    "UPDATE productos SET ventas_oferta_relampago = ? WHERE id = ?",
                                    (nuevas_ventas, p_id)
                                )
                except Exception as e:
                    logger.error(f"Error procesando oferta relampago: {e}")
            
            self.tabla.setRowCount(0)
            self.en_venta = False
            self.actualizar_totales()
            self._volcar_carrito_a_carteleria(limpiar=True)
            self.flash_feedback(success=True)
            
            if res:
                # Mostrar resumen de la última venta
                self.lbl_side_total.setText(f"TOTAL VENTA: {fmt_moneda_sin_centavos(res['total']):>10}")
                self.lbl_side_pagos.setText(f"PAGOS:       {fmt_moneda_sin_centavos(res['pago_con']):>10}")
                self.lbl_side_cambio.setText(f"CAMBIO:      {fmt_moneda_sin_centavos(res['cambio']):>10}")
                self.lbl_side_cambio.setStyleSheet("font-size: 16px; color: #10b981; font-weight: 900; font-family: 'Consolas', monospace;")
                
                # EMITIR EVENTO UDP AL CEREBRO CONECTOR (NEXUS)
                if not getattr(self, '_autoproteccion_activa', False):
                    try:
                        from src.network.network_engine import get_network_engine
                        from src.config import config
                        engine = get_network_engine()
                        if engine:
                            engine.broadcast_message("VENTA", {
                                "total": res['total'],
                                "metodo_pago": res.get("metodo_pago", "Efectivo"),
                                "caja_id": config.get("caja_id", 1)
                            })
                    except Exception as e:
                        print(f"Error emitiendo VENTA UDP: {e}")
        else:
            self.flash_feedback(success=False)
            
        QTimer.singleShot(100, self.txt_scan.setFocus)

    def _hay_ticket_activo(self):
        if getattr(self, "_cobro_abierto", False):
            return True
        if getattr(self, "tabla", None) is not None and self.tabla.rowCount() > 0:
            return True
        if getattr(self, "tickets_espera", None) and len(self.tickets_espera) > 0:
            return True
        return False

    def abrir_cierre_caja(self):
        if self._hay_ticket_activo():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                "Ticket activo",
                "No podés cerrar turno con productos en el ticket.\n\n"
                "Cobrá la venta (F12) o vaciá el carrito antes de usar F4.",
            )
            QTimer.singleShot(50, self.txt_scan.setFocus)
            return

        # --- EFECTO DE DESENFOQUE CINEMÁTICO ---
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)

        cierre = Paso7CierreCaja(self)
        qt_exec(ok = cierre)
        
        # Quitamos el desenfoque
        self.setGraphicsEffect(None)

        if ok:
            from PyQt6.QtWidgets import QApplication
            from src.config import config
            config.current_user = None
            QApplication.processEvents()
            QApplication.exit(888)
        else:
            QTimer.singleShot(50, self.txt_scan.setFocus)
    def abrir_historial_dia(self):
        # --- EFECTO DE DESENFOQUE ---
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(10)
        self.setGraphicsEffect(blur_effect)
        
        dlg = DialogoHistorialDia(self)
        qt_exec(dlg)
        
        self.setGraphicsEffect(None)
        QTimer.singleShot(50, self.txt_scan.setFocus)
    def _reaplicar_estilo_fila(self, row):
        try:
            desc_val = parse_float_safe(self.tabla.item(row, 4).text())
        except Exception:
            desc_val = 0.0
            
        is_oferta = desc_val > 0
        is_ultimo = (row == getattr(self, "last_active_row", -1))
        
        # Fondo premium de fila
        if is_ultimo:
            bg_color = QColor("#EFF6FF") # Hermoso fondo azul real suave para el último escaneado
        elif is_oferta:
            bg_color = QColor("#FFEDD5") # Naranja suave para ofertas
        else:
            bg_color = QColor("#FFFFFF") if row % 2 == 0 else QColor("#F8FAFC")
            
        for col in range(self.tabla.columnCount()):
            it = self.tabla.item(row, col)
            if not it: continue
            
            # Reset/Apply background (El subtotal tiene fondo verde agua permanente tipo columna Excel)
            if col == 5:
                it.setBackground(QColor("#D1FAE5") if is_ultimo else QColor("#F0FAF4")) # Verde agua destacado o pastel Excel
            else:
                it.setBackground(bg_color)
            
            # Reapply font settings (El último escaneado tiene letra más grande)
            f = it.font()
            f.setBold(True)
            f.setPointSize(20 if is_ultimo else 16) # 20pt para fila activa y 16pt para el resto
            it.setFont(f)
            
            # Reapply foreground colors based on column type
            if col == 1:
                it.setForeground(QColor("#1E3A8A") if is_ultimo else (QColor("#C2410C") if is_oferta else QColor("#1E3A8A")))
            elif col == 4:
                it.setForeground(QColor("#1E3A8A") if is_ultimo else (QColor("#EA580C") if is_oferta else QColor("#EF4444")))
            elif col == 5:
                it.setForeground(QColor("#047857")) # Verde esmeralda oscuro
            else:
                it.setForeground(QColor("#1E3A8A") if is_ultimo else (QColor("#C2410C") if is_oferta else QColor("#1E293B")))