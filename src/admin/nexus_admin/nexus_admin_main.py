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
        from src.central_red_global.network_engine import get_network_engine
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
        from src.central_red_global.network_engine import get_network_engine
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

    def _aplicar_estilos(self, theme="light"):
        if theme == "dark":
            bg_main = "#0F172A"
            text_color = "#F8FAFC"
            header_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:1 #3B82F6)"
        else:
            bg_main = "#F8FAFC"
            text_color = "#1E293B"
            header_bg = "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D97706, stop:1 #3B82F6)"

        self.setStyleSheet(f"QWidget#NexusExtremeControl {{ background: {bg_main}; }}")
        
        if hasattr(self, 'lbl_titulo'):
            self.lbl_titulo.setStyleSheet(f"""
                font-size: 18px; font-weight: 900; letter-spacing: 5px;
                background: {header_bg}; color: white; padding: 5px 15px; border-radius: 5px;
            """)
        if hasattr(self, 'lbl_reloj'):
            self.lbl_reloj.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {text_color}; background: transparent; border: none;")

        # Apply to sub-panels if they have an update_theme method
        if hasattr(self, 'panel_cen') and hasattr(self.panel_cen, 'update_theme'):
            self.panel_cen.update_theme(theme)
        if hasattr(self, 'panel_izq') and hasattr(self.panel_izq, 'update_theme'):
            self.panel_izq.update_theme(theme)
        if hasattr(self, 'panel_der') and hasattr(self.panel_der, 'update_theme'):
            self.panel_der.update_theme(theme)

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

        self.lbl_titulo = QLabel("N E X U S  //  CONTROL CENTER")
        self.lbl_titulo.setStyleSheet("""
            font-size: 16px; font-weight: 900; letter-spacing: 5px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #D97706, stop:0.5 #6366F1, stop:1 #0284C7);
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
        lay_h.addWidget(self.lbl_titulo)
        lay_h.addStretch()
        lay_h.addWidget(self.lbl_reloj)
        main_layout.addWidget(hdr)

        # --- ESTRUCTURA DE 3 PANES (IZQUIERDA, CENTRO, DERECHA) ---
        layout_paneles = QHBoxLayout()
        layout_paneles.setSpacing(10)
        layout_paneles.setContentsMargins(0, 0, 0, 0)

        # Importar paneles modulares originales
        from src.admin.nexus_admin.componentes.nexus_panel_izq import NexusPanelIzq
        from src.admin.nexus_admin.componentes.nexus_panel_cen import NexusPanelCen
        from src.utils.theme_manager import theme_manager
        from src.admin.nexus_admin.componentes.nexus_panel_izq import NexusPanelIzq
        from src.admin.nexus_admin.componentes.nexus_panel_cen import NexusPanelCen
        from src.admin.nexus_admin.componentes.nexus_panel_der import NexusPanelDer

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

        main_layout.addLayout(layout_paneles, 1)
        self._aplicar_estilos(theme_manager.current_theme)
        theme_manager.theme_changed.connect(self._aplicar_estilos) # Ocupará el resto del espacio
        
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
        self._force_z_close_from_panel(0.0)

    def _force_z_close_from_panel(self, monto_fisico):
        from src.admin.cierre.cierre_main import Admin7Cierre
        from PyQt6.QtCore import Qt
        
        self._play_sound("alert")
        
        if not hasattr(self, 'ventana_cierre') or not self.ventana_cierre.isVisible():
            self.ventana_cierre = Admin7Cierre(parent_main=self)
            self.ventana_cierre.setWindowFlags(Qt.WindowType.Window)
            self.ventana_cierre.resize(1100, 750)
            self.ventana_cierre.setWindowTitle("NEXUS PRO - Control de Cierre Ejecutivo")
            self.ventana_cierre.request_dashboard.connect(self.ventana_cierre.close)
            self.ventana_cierre.turno_cerrado.connect(self._sync_live_data)
            self.ventana_cierre.show()
            self.ventana_cierre.raise_()
            self.ventana_cierre.activateWindow()

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
            from src.cerebro_global.nexus_cerebro import CerebroNexus
            from datetime import datetime
            import random

            # 1. Actualizar metricas
            metrics = CerebroNexus.obtener_metricas_live(self.current_caja_filter)
            
            str_efectivo = f"$ {int(metrics['total_efectivo']):,}"
            str_digital  = f"$ {int(metrics['total_digital']):,}"
            
            if hasattr(self, 'panel_cen'):
                self.panel_cen.lbl_efectivo.val_label.setText(str_efectivo)
                self.panel_cen.lbl_digital.val_label.setText(str_digital)
                self.panel_cen.lbl_fondo.val_label.setText(f"$ {int(metrics['fondo_inicial']):,}")
                self.panel_cen.lbl_live_esperado.setText(f"$ {int(metrics['esperado_live']):,}")

            # 2. Buscar ventas nuevas
            nuevas_ventas = CerebroNexus.obtener_nuevas_ventas(self.last_sale_id)
            
            if nuevas_ventas:
                for v in nuevas_ventas:
                    self.last_sale_id = v['id']
                    tot_str = f"{int(v['total']):,}"
                    try:
                        fecha_val = v['fecha']
                        if isinstance(fecha_val, str):
                            sale_date = datetime.strptime(fecha_val, "%Y-%m-%d %H:%M:%S")
                        else:
                            sale_date = fecha_val
                    except:
                        sale_date = None
                    self._registrar_evento_caja(v['caja_id'], "VENTA", f"{v['metodo_pago']} - ", sale_date)
            else:
                if random.random() > 0.8:
                    self._inyectar_ruido_red()
        except Exception as e:
            import traceback
            print(f"Error _sync_live_data: {e}")

    def _registrar_evento_caja(self, origen_id, cat, msg, sale_date=None):
        self._play_sound("sale" if cat == "VENTA" else "alert")
        fg_color = "#10B981" if cat == "VENTA" else "#F43F5E"
        
        from src.cerebro_global.nexus_cerebro import CerebroNexus
        CerebroNexus.registrar_evento_caja(origen_id, cat, msg, sale_date)
        
        if cat != "VENTA":
            self._agregar_log_tabla(str(origen_id), f"[{cat}] {msg}", fg_color)
            
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
