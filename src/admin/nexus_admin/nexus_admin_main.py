from src.utils.theme_manager import theme_manager
import sys, random, math
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QApplication, QGridLayout, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QRect
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen
from datetime import datetime, timedelta
import threading

try:
    import winsound
    AUDIO_ENABLED = True
except ImportError:
    AUDIO_ENABLED = False

try:
    import psutil
    PSUTIL_ENABLED = True
except ImportError:
    PSUTIL_ENABLED = False

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

# ==============================================================================
# HOJA DE ESTILOS "NEXUS WARM-COLD 2026"
# ==============================================================================
EXTREME_STYLE = """
#NexusExtremeControl {
    background: #0F172A;
    font-family: 'Segoe UI', 'Consolas', monospace;
}

/* Paneles laterales */
#NexusExtremeControl QFrame.CyberPanel {
    background-color: rgba(15, 23, 42, 0.9);
    border: 1px solid #1E293B;
    border-radius: 8px;
    border-left: 3px solid #D97706;
}

/* Botones generales — frío (azul) */
#NexusExtremeControl QPushButton {
    background-color: rgba(2, 132, 199, 0.10);
    color: #7DD3FC;
    border: 1px solid rgba(2, 132, 199, 0.45);
    border-radius: 6px;
    padding: 10px 16px;
    font-weight: 900;
    font-size: 12px;
    letter-spacing: 1.5px;
    font-family: 'Segoe UI', sans-serif;
}
#NexusExtremeControl QPushButton:hover {
    background-color: rgba(2, 132, 199, 0.22);
    color: #E0F2FE;
    border: 1.5px solid #0284C7;
}

/* Botón crítico — cálido (rojo-ámbar) */
#NexusExtremeControl QPushButton#BtnCritical {
    background-color: rgba(239, 68, 68, 0.10);
    color: #FCA5A5;
    border: 1.5px solid rgba(239, 68, 68, 0.55);
    border-radius: 8px;
    padding: 10px 22px;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 2px;
}
#NexusExtremeControl QPushButton#BtnCritical:hover {
    background-color: rgba(239, 68, 68, 0.22);
    color: #FECACA;
    border-color: #EF4444;
}

/* Campo de texto — borde ámbar cálido */
#NexusExtremeControl QLineEdit {
    background: rgba(15, 23, 42, 0.7);
    color: #FDE68A;
    border: 1.5px solid rgba(217, 119, 6, 0.50);
    border-bottom: 3px solid #D97706;
    font-size: 26px;
    font-weight: 900;
    padding: 6px;
    border-radius: 6px;
    font-family: 'Segoe UI', sans-serif;
}
#NexusExtremeControl QLineEdit:focus {
    border-color: #F59E0B;
    background: rgba(217, 119, 6, 0.08);
}

#NexusExtremeControl QTextEdit {
    background-color: transparent;
    color: #CBD5E1;
    border: none;
    font-size: 12px;
    font-family: 'Consolas', monospace;
}

/* Tabla — oscuro con grid templado */
#NexusExtremeControl QTableWidget {
    background-color: rgba(3, 7, 18, 0.7);
    color: #E2E8F0;
    border: none;
    font-size: 11px;
    font-weight: 600;
    gridline-color: #1E293B;
    font-family: 'Segoe UI', sans-serif;
}
#NexusExtremeControl QTableWidget::item:selected {
    background: rgba(99, 102, 241, 0.20);
    color: #E0E7FF;
    font-weight: bold;
}
QHeaderView::section {
    background: rgba(30, 41, 59, 0.95);
    color: #94A3B8;
    font-weight: 900;
    font-size: 10px;
    letter-spacing: 1.5px;
    border: none;
    border-bottom: 2px solid #D97706;
    padding: 6px 8px;
    font-family: 'Segoe UI', sans-serif;
}
"""

# La clase CyberRadar ha sido movida a nexus_panel_izq.py

class NexusExtremeControl(QWidget):
    request_dashboard = pyqtSignal()
    request_z_close = pyqtSignal(float, int) # (monto_fisico, caja_id)

    def __init__(self):
        super().__init__()
        self.setObjectName("NexusExtremeControl")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("")
        
        # Obtener el máximo ID de venta hoy para no duplicar ventas históricas al abrir la pantalla
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            max_id = db_manager.execute_scalar("SELECT MAX(id) FROM ventas WHERE DATE(fecha) = ?", (hoy,))
            self.last_sale_id = max_id if max_id is not None else 0
        except Exception as e:
            print(f"Error inicializando last_sale_id: {e}")
            self.last_sale_id = 0
            
        self.total_esperado_cache = 0.0
        
        self._setup_ui()
        self._start_timers()
        self._connect_to_network()
        
        # Aplicar modo claro permanentemente a los paneles
        if hasattr(self, "panel_cen") and hasattr(self.panel_cen, "aplicar_tema"): self.panel_cen.aplicar_tema(False)
        if hasattr(self.panel_der, "aplicar_tema"): self.panel_der.aplicar_tema(False)
        if hasattr(self.panel_izq, "aplicar_tema"): self.panel_izq.aplicar_tema(False)

    def hideEvent(self, event):
        if hasattr(self, 't_matrix'): self.t_matrix.stop()
        if hasattr(self, 'panel_izq') and hasattr(self.panel_izq, 'spectrum') and hasattr(self.panel_izq.spectrum, 'timer'): 
            self.panel_izq.spectrum.timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        if hasattr(self, 't_matrix'): self.t_matrix.start(3000) 
        if hasattr(self, 'panel_izq') and hasattr(self.panel_izq, 'spectrum') and hasattr(self.panel_izq.spectrum, 'timer'): 
            self.panel_izq.spectrum.timer.start(100)
            
        # Al mostrarse, actualizar last_sale_id al máximo actual de hoy para no procesar como "nuevas"
        # las ventas que ocurrieron mientras Nexus estaba cerrado y que ya fueron registradas via UDP.
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            max_id = db_manager.execute_scalar("SELECT MAX(id) FROM ventas WHERE DATE(fecha) = ?", (hoy,))
            self.last_sale_id = max_id if max_id is not None else 0
        except Exception as e:
            print(f"Error actualizando last_sale_id en showEvent: {e}")
            
        super().showEvent(event)

    def closeEvent(self, event):
        if hasattr(self, 'panel_izq') and hasattr(self.panel_izq, 'closeEvent'):
            self.panel_izq.closeEvent(event)
        super().closeEvent(event)

    def _connect_to_network(self):
        from src.network.network_engine import get_network_engine
        engine = get_network_engine()
        if engine:
            engine.message_received.connect(self._on_udp_message)
            engine.heartbeat_received.connect(self._on_udp_heartbeat)
            engine.connection_lost.connect(self._on_connection_lost)

    def _on_udp_heartbeat(self, origen):
        # Registrar en memoria dinámica sin usar SQLite
        import time
        self.active_terminals[origen] = time.time()
        
        # Actualizar estado de terminales en el switchboard y agregar blip al radar
        if hasattr(self, 'panel_cen'):
            self.panel_cen.mark_active(origen)
            self.panel_cen.registrar_nodo_dinamico(origen)
        if hasattr(self, 'panel_izq') and hasattr(self.panel_izq, 'spectrum'):
            self.panel_izq.spectrum.add_blip(origen, is_heartbeat=True)

    def _on_udp_message(self, origen, tipo, datos):
        # Actualizar estado de terminales en el switchboard y agregar blip al radar
        if hasattr(self, 'panel_cen'):
            self.panel_cen.mark_active(origen)
            self.panel_cen.registrar_nodo_dinamico(origen)
        if hasattr(self, 'panel_izq') and hasattr(self.panel_izq, 'spectrum'):
            self.panel_izq.spectrum.add_blip(origen, is_heartbeat=False)

        if tipo == "VENTA":
            total = datos.get("total", 0)
            metodo = datos.get("metodo_pago", "Efectivo")
            self._registrar_evento_caja(origen, "VENTA", f"{metodo} - ${int(total):,}")
        elif tipo == "ALERTA_SEGURIDAD":
            msg = datos.get("mensaje", "Brecha de seguridad")
            self._registrar_evento_caja(origen, "ALERTA", msg)
            self._trigger_glitch()

    def _on_connection_lost(self, origen):
        self._play_sound("alert")
        src = str(origen).upper()
        self._append_terminal(f"⚠️ CONEXIÓN PERDIDA CON {src}", "#EF4444")
        self._registrar_evento_caja(origen, "ALERTA", "CONEXIÓN PERDIDA (Pérdida de latido)")
        self._trigger_glitch()
        
        # Emitir Alerta Sonora de Caída (Tres Beeps)
        try:
            import winsound
            winsound.Beep(1000, 200)
            winsound.Beep(1000, 200)
            winsound.Beep(1000, 200)
        except:
            pass

    def _play_sound(self, sound_type):
        pass # Desactivado temporalmente para prevenir RPC_E_CANTCALLOUT_ININPUTSYNCCALL en Windows

    def _start_timers(self):
        self.t_reloj = QTimer(self)
        self.t_reloj.timeout.connect(self._update_hud_status)
        self.t_reloj.start(1000)

        self.t_matrix = QTimer(self)
        self.t_matrix.timeout.connect(self._sync_live_data)
        self.t_matrix.start(2000)

    def _update_hud_status(self):
        import time
        now = time.time()
        
        # Mantener el rol local activo permanentemente para que no expire en la matriz
        from src.network.network_engine import get_network_engine
        engine = get_network_engine()
        if engine and engine.role:
            self.active_terminals[engine.role] = now
            if hasattr(self, 'panel_izq') and hasattr(self.panel_izq, 'spectrum'):
                # Enviar blip del local cada 15 segundos para no saturar el radar
                if not hasattr(self, '_last_local_blip') or now - self._last_local_blip >= 15:
                    self.panel_izq.spectrum.add_blip(engine.role, is_heartbeat=True)
                    self._last_local_blip = now

        # Limpiar terminales inactivas (timeout 45s) y sincronizar el switchboard con las pcs activas
        activos = 0
        for origen in list(self.active_terminals.keys()):
            if now - self.active_terminals[origen] > 45:
                del self.active_terminals[origen]
            else:
                activos += 1
                if hasattr(self, 'panel_cen'):
                    self.panel_cen.mark_active(origen)
                    self.panel_cen.registrar_nodo_dinamico(origen)
                
        time_str = datetime.now().strftime("%H:%M:%S // %d-%m-%Y")
        self.lbl_reloj.setText(f"{time_str}  |  🟢 TERMINALES ACTIVAS: {activos}")

    def keyPressEvent(self, event):
        import time
        if not hasattr(self, 'last_action_time'):
            self.last_action_time = 0
            
        key = event.key()
        
        # Filtro antirrebote de 1500ms para Reporte Z
        if key == Qt.Key_F12:
            if time.time() - self.last_action_time < 1.5:
                return
            self.last_action_time = time.time()
            self._mostrar_reporte_rapido()
        elif key in (Qt.Key_Right, Qt.Key_Down):
            self.focusNextChild()
        elif key in (Qt.Key_Left, Qt.Key_Up):
            self.focusPreviousChild()
        elif key in (Qt.Key_Enter, Qt.Key_Return):
            fw = QApplication.focusWidget()
            if isinstance(fw, QPushButton):
                fw.click()
                self._append_terminal(f"> COMANDO EJECUTADO: {fw.text()}")
        elif key == Qt.Key_Escape:
            self.request_dashboard.emit()
        else:
            super().keyPressEvent(event)

    def _setup_ui(self):
        self.is_dark_mode = False
        self.setStyleSheet("")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # --- HEADER HUD ---
        hdr = QFrame()
        hdr.setFixedHeight(45) 
        lay_h = QHBoxLayout(hdr)
        lay_h.setContentsMargins(0, 0, 0, 0)
        
        self.btn_abort = QPushButton("← SALIR DE NEXUS")
        self.btn_abort.setObjectName("BtnCritical")
        self.btn_abort.clicked.connect(self.request_dashboard.emit)

        lbl_titulo = QLabel("N E X U S  //  CONTROL CENTER")
        lbl_titulo.setStyleSheet("""
            font-size: 16px; font-weight: 900; letter-spacing: 5px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #D97706, stop:0.5 #6366F1, stop:1 #0284C7);
            -webkit-background-clip: text;
            color: #E0F2FE;
            font-family: 'Segoe UI', sans-serif;
        """)

        self.lbl_reloj = QLabel("00:00:00  //  00-00-0000")
        self.lbl_reloj.setStyleSheet("""
            font-size: 12px; font-weight: 700; color: #94A3B8;
            font-family: 'Consolas', monospace;
            background: transparent; border: none;
        """)

        lay_h.addWidget(self.btn_abort)
        lay_h.addStretch()
        lay_h.addWidget(lbl_titulo)
        lay_h.addStretch()
        lay_h.addWidget(self.lbl_reloj)
        main_layout.addWidget(hdr)

        # --- ESTRUCTURA DE 3 PANES (IZQUIERDA, CENTRO, DERECHA) ---
        layout_paneles = QHBoxLayout()
        layout_paneles.setSpacing(10)
        layout_paneles.setContentsMargins(0, 0, 0, 0)

        # Importar paneles modulares originales
        from src.admin.nexus.nexus_panel_izq import NexusPanelIzq
        from src.admin.nexus.nexus_panel_cen import NexusPanelCen
        from src.admin.nexus.nexus_panel_der import NexusPanelDer

        # 1. PANEL IZQ (Logs de terminal y CyberRadar con flujo en vivo de tickets)
        self.panel_izq = NexusPanelIzq()
        layout_paneles.addWidget(self.panel_izq, 25) # 25% del ancho

        # 2. PANEL CEN (Switchboard táctico de terminales y tarjetas métricas)
        self.panel_cen = NexusPanelCen()
        layout_paneles.addWidget(self.panel_cen, 35) # 35% del ancho

        # Conectar señales del panel central
        self.panel_cen.request_z_close.connect(self._force_z_close_from_panel)
        self.panel_cen.caja_selected.connect(self._on_caja_selected)

        # 3. PANEL DER (Auditoría y Bitácora histórica/eventos)
        self.panel_der = NexusPanelDer()
        layout_paneles.addWidget(self.panel_der, 40) # 40% del ancho

        main_layout.addLayout(layout_paneles, 1) # Ocupará el resto del espacio
        
        # Diccionario local en memoria para monitoreo de cajas
        self.active_terminals = {}
        self.current_caja_filter = "todas"

    def _toggle_theme(self):
        pass # Función eliminada, modo claro forzado

    def _on_caja_selected(self, caja_id):
        self.current_caja_filter = caja_id
        if caja_id != "todas":
            self._append_terminal(f"> [SYSTEM] FILTRO ACTIVADO: {str(caja_id).upper()}", "#6366F1")
        else:
            self._append_terminal("> [SYSTEM] FILTRO GLOBAL (TODAS LAS CAJAS)", "#10B981")
            
        # Refrescar los totales en el panel izquierdo (con cache bypassing para refresco inmediato)
        self._sync_live_data()
        
        # Filtrar también la tabla de auditoría del panel derecho
        self.panel_der.set_caja_filter(caja_id)

    def _append_terminal(self, texto, color_override=None):
        if color_override:
            color = color_override
        else:
            if "[FATAL]" in texto or "[CRITICAL]" in texto:
                color = "#E11D48" # Rose oscuro
            elif "[WARN]" in texto:
                color = "#D97706" # Amber oscuro
            elif "[OK]" in texto:
                color = "#059669" # Emerald oscuro
            elif "[TX]" in texto:
                color = "#38BDF8" # Azul neon
            else:
                color = "#94A3B8" # Slate claro
        
        self.panel_izq.append_terminal(texto, color)

    def _trigger_glitch(self):
        self._play_sound("critical")
        self.glitch_count = 0
        self.original_style = self.styleSheet()
        self.t_glitch = QTimer(self)
        self.t_glitch.timeout.connect(self._do_glitch_flash)
        self.t_glitch.start(100)

    def _do_glitch_flash(self):
        if self.glitch_count > 15:
            self.t_glitch.stop()
            self.setStyleSheet(self.original_style)
            return
            
        if self.glitch_count % 2 == 0:
            self.setStyleSheet(self.original_style + "\nQWidget {   font-weight: bold; }")
        else:
            self.setStyleSheet(self.original_style)
            
        self.glitch_count += 1

    def _force_z_close(self):
        # Esta función fue adaptada porque panel_cen ha sido removido
        # TODO: Implementar un nuevo diálogo para Cierre Z Global
        self._play_sound("alert")
        QMessageBox.warning(self, "Aviso", "El panel central manual fue removido. Usa el panel de auditoría o los comandos de consola para realizar cierres globales.")
        return

    def _force_z_close_from_panel(self, monto_fisico):
        if monto_fisico < 0:
            self._play_sound("alert")
            QMessageBox.critical(self, "ERROR CRÍTICO", "INPUT FÍSICO CORRUPTO.")
            return
        self._ejecutar_cierre_z_db(monto_fisico)

    def _ejecutar_cierre_z_db(self, monto_fisico):
        # ── Guard: el Cierre Z solo puede ejecutarlo el MAESTRO ────────────────────
        if not getattr(db_manager, 'is_master', True):
            self._append_terminal(
                "> [BLOCKED] CIERRE Z DENEGADO: esta terminal corre en modo ESCLAVO."
                " Solo el servidor maestro puede ejecutar cierres fiscales.", "#F43F5E")
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Operación No Permitida",
                "El Cierre Z solo puede ejecutarse desde la PC MAESTRA.\n"
                "Esta terminal está conectada como ESCLAVA a la red."
            )
            return

        caja_num = 0
        if self.current_caja_filter != "todas":
            try:
                import re
                num_match = re.search(r'\d+', str(self.current_caja_filter))
                caja_num = int(num_match.group()) if num_match else 0
            except:
                caja_num = 0

        if caja_num <= 0:
            self._append_terminal("> [ERROR] NO SE PUEDE FORZAR CIERRE GLOBAL. SELECCIONA UNA CAJA ESPECÍFICA PRIMERO.", "#E11D48")
            self._play_sound("error")
            return

        # Calcular si hay descuadre en la caja seleccionada
        total_efectivo = 0.0
        fondo_inicial = 0.0
        esperado = 0.0
        diferencia = monto_fisico
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            total_efectivo = db_manager.execute_scalar(
                "SELECT SUM(total) FROM ventas WHERE fecha LIKE ? AND metodo_pago = 'Efectivo' AND caja_id = ?",
                (f"{hoy}%", caja_num)
            ) or 0.0
            
            # Ajustar por el fondo inicial
            fondo_inicial = float(db_manager.execute_scalar(
                "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' AND caja_id = ? ORDER BY id DESC LIMIT 1",
                (caja_num,)
            ) or 0.0)
            
            esperado = total_efectivo + fondo_inicial
            diferencia = monto_fisico - esperado
            
            if diferencia < 0:
                self._append_terminal(
                    f"> [FATAL] DESCUADRE CRÍTICO EN CAJA {caja_num}"
                    f" DE ${diferencia:.2f}. INICIANDO PROTOCOLOS DE AUDITORÍA.")
            elif diferencia > 1000.0:
                self._play_sound("alert")
                self._append_terminal(
                    f"> [WARN] EXCESO NO JUSTIFICADO EN CAJA {caja_num}"
                    f" DE ${diferencia:.2f}.")
        except Exception as e:
            print(f"Error calculando cuadre en F12: {e}")

        self._append_terminal(
            f"> [CRITICAL] SECUENCIA F12 INICIADA. EJECUTANDO CIERRE Z "
            f"CAJA {caja_num} (FÍSICO: {monto_fisico})")

        # Confirmar y ejecutar
        try:
            from PyQt6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Confirmación Crítica — NEXUS OVERRIDE",
                f"¿Estás seguro de emitir el CIERRE Z DEFINITIVO para la CAJA {caja_num}?\n"
                f"Monto Físico Declarado: ${monto_fisico:,.2f}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                self._append_terminal("> [ABORT] SECUENCIA DE CIERRE Z ABORTADA POR EL USUARIO.")
                return

            db_manager.execute_non_query(
                "INSERT INTO movimientos_caja (tipo, monto, usuario, observaciones, caja_id)"
                " VALUES (?, ?, ?, ?, ?)",
                ("CIERRE_Z", diferencia, "nexus_admin",
                 f"Modo:global | Fis:${monto_fisico:.2f} | Esp:${esperado:.2f}",
                 caja_num)
            )
            db_manager.execute_non_query(
                "UPDATE ventas SET estado='CERRADA' WHERE estado='COMPLETADA' AND caja_id=?",
                (caja_num,)
            )

            # Imprimir ticket Z
            try:
                from src.hardware.printer import printer_manager
                printer_manager.imprimir_control_x({
                    "fondo": fondo_inicial, "t_efec": total_efectivo, "t_tarj": 0,
                    "t_total": total_efectivo, "esperado": esperado, "alertas": 0,
                    "dia_tarjeta": 0, "dia_total": total_efectivo,
                    "efectivo_esperado": esperado, "segunda_tiketera": False
                })
            except Exception as e_print:
                self._append_terminal(f"> [WARN] Error de impresión: {e_print}", "#F59E0B")

            QMessageBox.information(
                self, "Cierre Exitoso",
                f"Cierre Z completado para Caja {caja_num}.")
            self._append_terminal("> [OK] CIERRE Z EJECUTADO Y SESIÓN FINALIZADA.", "#10B981")

        except Exception as e:
            self._append_terminal(f"> [FATAL] ERROR EN DB DURANTE CIERRE Z: {e}", "#E11D48")

    def _mostrar_reporte_rapido(self):
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            hoy = datetime.now().strftime("%Y-%m-%d")
            
            # Caja Total y Transacciones
            cursor.execute("SELECT SUM(total), COUNT(id) FROM ventas WHERE DATE(fecha) = ? AND estado != 'CANCELADA'", (hoy,))
            row = cursor.fetchone()
            total_caja = float(row[0] or 0.0)
            transacciones = int(row[1] or 0)
            
            # Kilos Vendidos (solo productos pesables o asumido si la unidad es KG)
            kilos_totales = 0.0
            try:
                # Intenta buscar por departamento carniceria o unidad KG
                cursor.execute("""
                    SELECT SUM(d.cantidad) FROM detalles_ventas d
                    JOIN ventas v ON d.id_venta = v.id
                    JOIN productos p ON d.id_producto = p.codigo
                    WHERE DATE(v.fecha) = ? AND p.unidad IN ('KG', 'Kg', 'kg') AND v.estado != 'CANCELADA'
                """, (hoy,))
                kilos_totales = float(cursor.fetchone()[0] or 0.0)
            except: pass
            
            # ROI Carteleria Inteligente
            roi_carteleria = 0.0
            producto_estrella = "Ninguno"
            try:
                cursor.execute("""
                    SELECT SUM(d.subtotal) FROM detalles_ventas d
                    JOIN ventas v ON d.id_venta = v.id
                    WHERE DATE(v.fecha) = ? AND d.vendido_por_carteleria = 1 AND v.estado != 'CANCELADA'
                """, (hoy,))
                res_roi = cursor.fetchone()
                roi_carteleria = float(res_roi[0] or 0.0)
                
                cursor.execute("""
                    SELECT d.nombre_producto, COUNT(d.id) as ventas_count FROM detalles_ventas d
                    JOIN ventas v ON d.id_venta = v.id
                    WHERE DATE(v.fecha) = ? AND d.vendido_por_carteleria = 1 AND v.estado != 'CANCELADA'
                    GROUP BY d.nombre_producto
                    ORDER BY ventas_count DESC LIMIT 1
                """, (hoy,))
                res_estrella = cursor.fetchone()
                if res_estrella:
                    producto_estrella = res_estrella[0]
            except Exception as e:
                pass
            
            conn.close()
            
            QMessageBox.information(
                self, "📊 Reporte Rápido (F12)",
                f"RESUMEN DEL DÍA ({hoy})\n\n"
                f"💰 Caja Total: ${total_caja:,.2f}\n"
                f"🛒 Transacciones: {transacciones}\n"
                f"🥩 Kilos Vendidos: {kilos_totales:,.2f} kg\n\n"
                f"--- 🤖 IMPACTO IA (CARTELERÍA) ---\n"
                f"📈 Retorno Generado: +${roi_carteleria:,.2f}\n"
                f"🌟 Producto Estrella: {producto_estrella}"
            )
            self._append_terminal("> [INFO] Reporte rápido consultado vía teclado (F12).", "#3B82F6")
        except Exception as e:
            self._append_terminal(f"> [ERROR] Fallo al generar reporte rápido: {e}", "#EF4444")

    # ==============================================================================
    # MOTOR DE DATOS REALES (CONEXIÓN A DATABASE)
    # ==============================================================================

    def _sync_live_data(self):
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")

            # 1. Actualizar métricas (Globales o por Caja)
            # DATE(fecha) = ? funciona en SQLite y MariaDB (columna DATETIME)
            params_totales = [hoy]
            filtro_caja_sql = ""
            if self.current_caja_filter != "todas":
                import re
                num_match = re.search(r'\d+', str(self.current_caja_filter))
                caja_num = int(num_match.group()) if num_match else 1
                filtro_caja_sql = " AND caja_id = ?"
                params_totales.append(caja_num)

            total_efectivo = db_manager.execute_scalar(
                f"SELECT SUM(total) FROM ventas"
                f" WHERE DATE(fecha) = ? AND metodo_pago = 'Efectivo'{filtro_caja_sql}",
                tuple(params_totales)
            ) or 0.0
            total_digital = db_manager.execute_scalar(
                f"SELECT SUM(total) FROM ventas"
                f" WHERE DATE(fecha) = ? AND metodo_pago != 'Efectivo'{filtro_caja_sql}",
                tuple(params_totales)
            ) or 0.0

            self.total_esperado_cache = total_efectivo

            str_efectivo = f"$ {int(total_efectivo):,}"
            str_digital  = f"$ {int(total_digital):,}"

            # Actualizar tarjetas métricas del panel central
            if hasattr(self, 'panel_cen'):
                self.panel_cen.lbl_efectivo.val_label.setText(str_efectivo)
                self.panel_cen.lbl_digital.val_label.setText(str_digital)
                
                # Obtener fondo de apertura para la caja seleccionada
                fondo_inicial = 0.0
                if self.current_caja_filter != "todas":
                    import re
                    num_match = re.search(r'\d+', str(self.current_caja_filter))
                    caja_num = int(num_match.group()) if num_match else 1
                    fondo_inicial = float(db_manager.execute_scalar(
                        "SELECT monto FROM movimientos_caja WHERE tipo='APERTURA' AND caja_id = ? ORDER BY id DESC LIMIT 1",
                        (caja_num,)
                    ) or 0.0)
                else:
                    # Sumar fondos de todas las terminales activas hoy
                    fondo_inicial = float(db_manager.execute_scalar(
                        "SELECT SUM(monto) FROM movimientos_caja WHERE tipo='APERTURA' AND DATE(fecha) = ?",
                        (hoy,)
                    ) or 0.0)
                
                self.panel_cen.lbl_fondo.val_label.setText(f"$ {int(fondo_inicial):,}")
                self.panel_cen.lbl_live_esperado.setText(f"$ {int(total_efectivo + fondo_inicial):,}")

            # 2. Buscar ventas nuevas desde la última consulta
            query_nuevas = (
                "SELECT id, caja_id, metodo_pago, total, usuario, fecha"
                " FROM ventas WHERE DATE(fecha) = ?"
            )
            params_nuevas = [hoy]
            if self.last_sale_id:
                query_nuevas += " AND id > ?"
                params_nuevas.append(self.last_sale_id)
            query_nuevas += " ORDER BY id ASC LIMIT 5"

            nuevas_ventas = db_manager.execute_query(query_nuevas, tuple(params_nuevas))
            
            if nuevas_ventas:
                for v in nuevas_ventas:
                    self.last_sale_id = v['id']
                    tot_str = f"{int(v['total']):,}"
                    # Parsear la fecha del registro en ventas
                    try:
                        fecha_val = v['fecha']
                        if isinstance(fecha_val, str):
                            sale_date = datetime.strptime(fecha_val, "%Y-%m-%d %H:%M:%S")
                        else:
                            sale_date = fecha_val
                    except:
                        sale_date = None
                    self._registrar_evento_caja(v['caja_id'], "VENTA", f"{v['metodo_pago']} - ${tot_str}", sale_date)
            else:
                if random.random() > 0.8:
                    self._inyectar_ruido_red()
        except Exception as e:
            import traceback
            with open("error_sync.log", "w") as f:
                f.write(traceback.format_exc())
            print(f"Error _sync_live_data: {e}")

    def _registrar_evento_caja(self, origen_id, cat, msg, sale_date=None):
        self._play_sound("sale" if cat == "VENTA" else "alert")
        
        fg_color = "#10B981" if cat == "VENTA" else "#F43F5E"
        bg_color = "#065F46" if cat == "VENTA" else "#991B1B"
        
        origen = str(origen_id)
        src = origen.upper()
        
        # Intentamos extraer el ID de caja numérico (ej. de 'CAJERO-PC-02' -> 2)
        c_id = 1
        try:
            import re
            match = re.search(r'\d+', src)
            if match:
                c_id = int(match.group())
        except:
            pass

        # Formatear tipo y observaciones para la BD
        if cat == "VENTA":
            tipo_db = "[TICKET] Venta Remota"
            obs_db = f"[TICKET] {msg}"
        else:
            tipo_db = "ALERTA_SEGURIDAD" if cat == "ALERTA" else cat.upper()
            obs_db = f"[{cat}] {msg}"

        # Guardar en la base de datos para persistencia total y bitácora
        try:
            ts_now = datetime.now()
            # Usar fecha exacta de venta si viene del sync de DB para mantener orden cronológico
            ref_date = sale_date if sale_date is not None else ts_now
            ts = ref_date.strftime("%Y-%m-%d %H:%M:%S")

            # Chequeo de duplicados robusto
            if cat == "VENTA":
                # Validar en un rango de +/- 60 segundos alrededor de la fecha de la venta
                ts_min = (ref_date - timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")
                ts_max = (ref_date + timedelta(seconds=60)).strftime("%Y-%m-%d %H:%M:%S")
                existe = db_manager.execute_scalar(
                    "SELECT COUNT(id) FROM movimientos_caja WHERE observaciones = ? AND caja_id = ? AND fecha BETWEEN ? AND ?",
                    (obs_db, c_id, ts_min, ts_max)
                )
            else:
                ts_limite = (ts_now - timedelta(seconds=5)).strftime("%Y-%m-%d %H:%M:%S")
                existe = db_manager.execute_scalar(
                    "SELECT COUNT(id) FROM movimientos_caja WHERE observaciones = ? AND tipo = ? AND caja_id = ? AND fecha >= ?",
                    (obs_db, tipo_db, c_id, ts_limite)
                )

            if not existe or existe == 0:
                db_manager.execute_non_query(
                    "INSERT INTO movimientos_caja (fecha, tipo, observaciones, caja_id, usuario, monto) VALUES (?, ?, ?, ?, ?, ?)",
                    (ts, tipo_db, obs_db, c_id, "SISTEMA", 0.0)
                )
        except Exception as e:
            print(f"Error insertando evento de caja en DB: {e}")

        # Si el evento no es una venta, o si es para actualizar la tabla del panel derecho
        if cat != "VENTA":
            self._agregar_log_tabla(src, f"[{cat}] {msg}", fg_color)
            
        # Refrescar la tabla de auditoría del panel derecho directamente desde la base de datos
        if hasattr(self, 'panel_der'):
            self.panel_der.filtrar_auditoria()

    def _restaurar_estilo_boton(self, boton, origen):
        pass # Función deprecada (Solid State UI)

    def _inyectar_ruido_red(self):
        eventos = [
            ("SYNC", "Push a DB SQLite Exitoso", "#8B5CF6", "#5B21B6"),
            ("ACCESS", "Apertura Cajón (Shift)", "#94A3B8", "#475569")
        ]
        cat, msg, fg_color, bg_color = random.choice(eventos)
        caja_idx = random.randint(0, 3)
        self._agregar_log_tabla(f"CAJA {caja_idx+1}", f"[{cat}] {msg}", fg_color)

    def _agregar_log_tabla(self, src, payload, fg_color):
        self.panel_der.agregar_log(src, payload, fg_color)
