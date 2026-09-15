from PyQt6.QtCore import QObject, QTimer, Qt
from PyQt6.QtWidgets import QMessageBox
from src.cerebro_global.nexus_cerebro import CerebroNexus
from src.utils.theme_manager import theme_manager
import time
from datetime import datetime
import random

class NexusController(QObject):
    def __init__(self, view):
        super().__init__()
        self.view = view
        
        self.active_terminals = {}
        self.last_sale_id = self._get_initial_max_id()
        self.current_caja_filter = "todas"
        self.glitch_count = 0
        
        self._connect_signals()
        self._start_timers()
        self._connect_to_network()

    def _get_initial_max_id(self):
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            from src.base_de_datos.database import db_manager
            max_id = db_manager.execute_scalar("SELECT MAX(id) FROM ventas WHERE DATE(fecha) = ?", (hoy,))
            return max_id if max_id is not None else 0
        except Exception as e:
            return 0

    def _connect_signals(self):
        if hasattr(self.view.panel_cen, 'request_z_close'):
            self.view.panel_cen.request_z_close.connect(self._force_z_close_from_panel)
        if hasattr(self.view.panel_cen, 'caja_selected'):
            self.view.panel_cen.caja_selected.connect(self._on_caja_selected)

    def _start_timers(self):
        self.t_matrix = QTimer(self)
        self.t_matrix.timeout.connect(self._sync_live_data)
        self.t_matrix.start(3000)

        self.t_glitch = QTimer(self)
        self.t_glitch.timeout.connect(self._do_glitch_flash)

    def _do_glitch_flash(self):
        if self.glitch_count > 15:
            self.t_glitch.stop()
            self.view.setStyleSheet(self.view.original_style)
            return
            
        if self.glitch_count % 2 == 0:
            self.view.setStyleSheet(self.view.original_style + "\nQWidget { font-weight: bold; }")
        else:
            self.view.setStyleSheet(self.view.original_style)
            
        self.glitch_count += 1

    def _connect_to_network(self):
        try:
            from src.central_red_global.network_engine import get_network_engine
            engine = get_network_engine()
            if engine:
                engine.message_received.connect(self._on_udp_message)
                engine.heartbeat_received.connect(self._on_udp_heartbeat)
                engine.connection_lost.connect(self._on_connection_lost)
        except Exception as e:
            print(f"Error conectando Nexus Controller a Network Engine: {e}")

    def _on_udp_heartbeat(self, origen):
        self.active_terminals[origen] = time.time()
        if hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'log_udp'):
            self.view.panel_izq.log_udp(f"[{datetime.now().strftime('%H:%M:%S')}] HEARTBEAT -> {origen}")
        if hasattr(self.view, 'panel_cen'):
            self.view.panel_cen.registrar_nodo_dinamico(origen)

    def _on_udp_message(self, origen, tipo, datos):
        if hasattr(self.view, 'panel_cen'):
            self.view.panel_cen.mark_active(origen)
            self.view.panel_cen.registrar_nodo_dinamico(origen)
        if hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'log_udp'):
            self.view.panel_izq.log_udp(f"[{datetime.now().strftime('%H:%M:%S')}] {tipo} -> {origen}")

        if tipo == "VENTA_NUEVA":
            tot = datos.get('total', 0)
            mp = datos.get('metodo_pago', 'N/A')
            self._registrar_evento_caja(origen, "VENTA", f"{mp} - $ {tot}")
            self._sync_live_data()
        elif tipo == "CIERRE_TURNO":
            self._registrar_evento_caja(origen, "CIERRE", "Cierre de turno remoto detectado")
            self._sync_live_data()
        elif tipo == "ALERTA_SEGURIDAD":
            msg = datos.get("mensaje", "Alerta Desconocida")
            self._registrar_evento_caja(origen, "ALERTA", msg)
            if "CRITICO" in msg.upper():
                self.glitch_count = 0
                self.t_glitch.start(100)

    def _on_connection_lost(self, origen):
        if hasattr(self.view, 'panel_cen'):
            self.view.panel_cen.mark_inactive(origen)
        if hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'log_udp'):
            self.view.panel_izq.log_udp(f"[{datetime.now().strftime('%H:%M:%S')}] LOST -> {origen}")
        self._registrar_evento_caja(origen, "ALERTA", "Conexion perdida con la terminal")

    def _on_caja_selected(self, origen):
        self.current_caja_filter = str(origen)
        if hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'add_log'):
            self.view.panel_izq.add_log(f"[FILTRO APLICADO] Auditando: {origen}")
            
        if hasattr(self.view, 'panel_der'):
            self.view.panel_der.caja_filter = str(origen)
            if hasattr(self.view.panel_der, 'filtrar_auditoria'):
                self.view.panel_der.filtrar_auditoria()
        self._sync_live_data()

    def _force_z_close_from_panel(self, monto_fisico):
        from src.admin.cierre.cierre_main import Admin7Cierre
        if hasattr(self.view, '_play_sound'): self.view._play_sound("alert")
        if not hasattr(self, 'ventana_cierre') or not self.ventana_cierre.isVisible():
            self.ventana_cierre = Admin7Cierre(parent_main=self.view)
            self.ventana_cierre.setWindowFlags(Qt.WindowType.Window)
            self.ventana_cierre.resize(1100, 750)
            self.ventana_cierre.setWindowTitle("NEXUS PRO - Control de Cierre Ejecutivo")
            self.ventana_cierre.request_dashboard.connect(self.ventana_cierre.close)
            self.ventana_cierre.turno_cerrado.connect(self._sync_live_data)
            self.ventana_cierre.show()
            self.ventana_cierre.raise_()
            self.ventana_cierre.activateWindow()

    def _sync_live_data(self):
        try:
            metrics = CerebroNexus.obtener_metricas_live(self.current_caja_filter)
            
            str_efectivo = f"$ {int(metrics.get('total_efectivo', 0)):,}"
            str_digital  = f"$ {int(metrics.get('total_digital', 0)):,}"
            
            if hasattr(self.view, 'panel_cen'):
                self.view.panel_cen.lbl_efectivo.val_label.setText(str_efectivo)
                self.view.panel_cen.lbl_digital.val_label.setText(str_digital)
                self.view.panel_cen.lbl_fondo.val_label.setText(f"$ {int(metrics.get('fondo_inicial', 0)):,}")
                self.view.panel_cen.lbl_live_esperado.setText(f"$ {int(metrics.get('esperado_live', 0)):,}")

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
                    self._registrar_evento_caja(v.get('caja_id', 1), "VENTA", f"{v.get('metodo_pago')} - $ {tot_str}", sale_date)
            else:
                pass
                    
            # Actualizar reloj y contadores
            ahora = time.time()
            activos = 0
            for origen, ul in list(self.active_terminals.items()):
                if ahora - ul > 35:
                    del self.active_terminals[origen]
                    self._on_connection_lost(origen)
                else:
                    activos += 1
                    if hasattr(self.view, 'panel_cen'):
                        self.view.panel_cen.mark_active(origen)
            
            time_str = datetime.now().strftime("%H:%M:%S // %d-%m-%Y")
            if hasattr(self.view, 'lbl_reloj'):
                self.view.lbl_reloj.setText(f"{time_str}  |  ?? TERMINALES ACTIVAS: {activos}")

        except Exception as e:
            pass

    def _registrar_evento_caja(self, origen_id, cat, msg, sale_date=None):
        if hasattr(self.view, '_play_sound'):
            self.view._play_sound("sale" if cat == "VENTA" else "alert")
        
        CerebroNexus.registrar_evento_caja(origen_id, cat, msg, sale_date)
        
        if cat != "VENTA" and hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'add_log'):
            self.view.panel_izq.add_log(f"[{cat}] {msg} (ORG: {origen_id})")
            
        if hasattr(self.view, 'panel_der') and hasattr(self.view.panel_der, 'filtrar_auditoria'):
            self.view.panel_der.filtrar_auditoria()

    def _inyectar_ruido_red(self):
        eventos = [
            ("SYNC", "Protocolo DB Sincronizado"),
            ("ACCESS", "Apertura Cajon Detectada")
        ]
        cat, msg = random.choice(eventos)
        caja_idx = random.randint(0, 3)
        if hasattr(self.view, 'panel_izq') and hasattr(self.view.panel_izq, 'add_log'):
            self.view.panel_izq.add_log(f"[{cat}] {msg} (ORG: CAJA-{caja_idx})")
