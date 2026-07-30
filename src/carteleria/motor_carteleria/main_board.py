import os
import random
import logging
import urllib.request
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QGridLayout, QLabel, QApplication, QGraphicsOpacityEffect
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap

# Componentes modulares
from src.carteleria.theme import C_THEME
from src.carteleria.configuraciones.info_negocio import InfoNegocio
from src.carteleria.interfaz_principal.mensaje import Mensaje
from src.carteleria.interfaz_principal.carrusel_destacados import CarruselDestacados
from src.carteleria.interfaz_principal.grilla_precios import GrillaPrecios
from src.carteleria.interfaz_principal.panel_combos import PanelCombos
from src.carteleria.interfaz_principal.panel_ia import PanelIA
from src.carteleria.interfaz_relampagos.pantalla_espia import PantallaEspia
from src.carteleria.interfaz_relampagos.oferta_relampago import OfertaRelampago
from src.carteleria.interfaz_relampagos.banderin import BanderinVolador
import time

db_manager = None  # Refactorizado a API REST

logger = logging.getLogger("Carteleria_Autonoma")

from src.carteleria.motor_carteleria.espia_worker import EspiaWorker
from src.carteleria.motor_carteleria.window_manager import WindowManager
from src.carteleria.motor_carteleria.layout_manager import LayoutManager
from src.carteleria.motor_carteleria.network_manager import NetworkManager



class CarteleriaMain(QWidget):
    request_screen = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_mode = 4 
        self.img_index = 0
        self.datos_destacados = []
        self.combos_relacionados = []
        
        self.setObjectName("CarteleriaMain")
        from PyQt6.QtCore import Qt
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        from src.config import config
        from src.carteleria.theme import set_theme, get_active_theme_name
        set_theme(config.get("carteleria_theme", "apple"))

        self.window_manager = WindowManager(self)
        self.layout_manager = LayoutManager(self)
        self.network_manager = NetworkManager(self)
        
        # --- FONDO ---
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        from src.utils.paths import get_resource_path
        
        if get_active_theme_name() == "temu":
            # Fondo vibrante para Temu (Gradiente Radial/Lineal de Amarillo a Naranja)
            self.setStyleSheet("""
                #CarteleriaMain {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                stop:0 #FFFF00, stop:1 #FF6600);
                }
            """)
        else:
            img_path = get_resource_path(os.path.join("src", "carteleria", "assets", "macos_bg.png"))
            if os.path.exists(img_path):
                self.bg_label.setPixmap(QPixmap(img_path))
            else:
                self.setStyleSheet(f"#CarteleriaMain {{ background-color: {C_THEME['bg']}; }}")

        # --- INSTANCIAR ZONAS MODULARES ---
        self.info_negocio = InfoNegocio()
        self.info_negocio.btn_modo.clicked.connect(self.layout_manager.ciclar_layout)
        self.info_negocio.config_requested.connect(self._abrir_configuracion)
        
        self.mensaje = Mensaje()
        self.zona1_carrusel = CarruselDestacados()
        self.zona2_precios = GrillaPrecios()
        self.zona3_extra1 = PanelCombos()
        self.zona4_extra2 = PanelIA()
        
        from src.carteleria.motor_carteleria.promo_manager import PromoManager
        self.promo_manager = PromoManager(self)
        
        self._build_ui()
        
        # ⚙️ TIMER ROTACIÓN PROMOCIONES
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._ciclo_inteligente)
        self.rotacion_ms = 16000 # Retraso normal (16s) para que intercale rápido
        self.timer.start(self.rotacion_ms) 
        
        self.contador_rotacion = 0
        self.frec_sos = 3 # Intercalado equilibrado: 3 ciclos de grilla por 1 aparición de Oferta Relámpago
        self.tiempo_sos_ms = 10000
        self.estado_sos_activo = False
        self.lista_ofertas_sos = []
        self.indice_sos_actual = 0
        
        from src.carteleria.motor_carteleria.db_sync_worker import DbSyncWorker
        from src.carteleria.motor_carteleria.clima_worker import ClimaWorker

        self.db_worker = DbSyncWorker(self)
        self.db_worker.sync_finished.connect(self._on_db_sync_finished)
        self.timer_db = QTimer(self)
        self.timer_db.timeout.connect(self.db_worker.start)
        self.timer_db.start(10000)

        self.clima_pilar = ("sol", "22°C Pilar")
        self.clima_worker = ClimaWorker(self)
        self.clima_worker.clima_actualizado.connect(self._on_clima_actualizado)
        self.timer_clima = QTimer(self)
        self.timer_clima.timeout.connect(self.clima_worker.start)
        self.timer_clima.start(3600000)

        self.timer_vuelo = QTimer(self)
        
        def intentar_lanzar_banderin():
            if self.stack.currentIndex() < 2:  # Solo lanzar en pantallas normales (0 o 1)
                self.banderin.lanzar(self.datos_destacados)
                
        self.timer_vuelo.timeout.connect(intentar_lanzar_banderin)
        self.timer_vuelo.start(35000) 
        
        self.db_worker.start()
        # 👀 OJO ESPÍA (WORKER EN BACKGROUND)
        from src.utils.paths import get_base_path
        from src.config import config
        is_slave = bool(config.get("db_host", "")) or config.get("carteleria_is_slave", False)
        
        # El clima solo lo consulta el maestro para no saturar APIs externas
        if not is_slave:
            self.clima_worker.start()
        
        path_ls = os.path.join(get_base_path(), "live_scan.json")
        master_ip = config.get("carteleria_master_ip", "")
        self.espia_worker = EspiaWorker(master_ip, path_ls)
        self.espia_worker.combo_triggered.connect(self._on_combo_triggered)
        self.espia_worker.limpiar_solicitado.connect(self._on_espia_limpiar)
        self.espia_worker.refresh_requested.connect(self.db_worker.start)
        
        # Si es esclavo, el espía solo escucha la red pasivamente y no interfiere con DB
        self.espia_worker.start()
        
        self.ultimo_cambio_ia = __import__('time').time() - 16

        # ── HEARTBEAT HACIA EL TERMINAL ─────────────────────────────────────
        # La cartelería emite un latido UDP cada 10s con rol "carteleria" para
        # que el terminal actualice su indicador ⚫ → 🟢.
        self.timer_heartbeat = QTimer(self)
        self.timer_heartbeat.timeout.connect(self.network_manager.emitir_heartbeat)
        self.timer_heartbeat.start(10000)   # cada 10 segundos
        QTimer.singleShot(500, self.network_manager.emitir_heartbeat)  # primer latido a los 0.5s

        # ── ESCUCHAR HEARTBEATS DEL TERMINAL ────────────────────────────────
        # Si el engine ya está inicializado (cajero/admin en el mismo proceso)
        # conectamos directamente sus señales al indicador del header.
        QTimer.singleShot(800, self.network_manager.conectar_engine_indicador)

        

    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        super().resizeEvent(event)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        self.stack = QStackedWidget()
        
        # --- PANTALLA NORMAL ---
        self.page_normal = QWidget()
        self.page_normal.setStyleSheet("background: transparent;")
        lay_normal = QVBoxLayout(self.page_normal)
        lay_normal.setContentsMargins(40, 40, 40, 40)
        
        lay_normal.addWidget(self.info_negocio)
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.grid_container)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(20)
        lay_normal.addWidget(self.grid_container, 1)
        
        lay_normal.addWidget(self.mensaje)
        
        # --- PANTALLA SOS ---
        self.page_sos = OfertaRelampago()
        self.page_espia = PantallaEspia(self)
        
        self.stack.addWidget(self.page_normal) # Index 0
        self.stack.addWidget(self.page_sos)    # Index 1
        self.stack.addWidget(self.page_espia) # Index 2
        root.addWidget(self.stack)

        # 🛸 WIDGET FLOTANTE MODULARIZADO
        self.banderin = BanderinVolador(self)
        
        self.layout_manager.aplicar_layout()

    def _on_clima_actualizado(self, icon_name, text):
        self.clima_pilar = (icon_name, text)
        if hasattr(self, 'zona4_extra2'):
            self.zona4_extra2.motor.set_clima((icon_name, text))

    def _abrir_configuracion(self):
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        from src.config import config
        
        current_ip = config.get("carteleria_master_ip", "")
        ip, ok = QInputDialog.getText(self, "Configuración de Cartelería", 
                                      "Ingresa la IP de la Caja Maestra:\n(Deja en blanco si esta es la caja maestra)",
                                      text=current_ip)
        if ok:
            config.set("carteleria_master_ip", ip.strip())
            config.save()
            QMessageBox.information(self, "Configuración", "Configuración guardada.\nRevisa que la IP sea correcta.")

    def _on_db_sync_finished(self, data, status):
        try:
            if status == "online":
                self.info_negocio.set_estado_red("online")
            elif status == "offline":
                self.info_negocio.set_estado_red("offline", "Modo Offline (Caché)")
            else:
                return
            
            if not data: return
            
            # 1. Configuracion
            cfg_data = data.get("config", {})
            nombre_negocio = cfg_data.get("business_name", "Carnicería")
            telefono_negocio = cfg_data.get("phone", "No disponible")
            
            self.info_negocio.actualizar_nombre(nombre_negocio)
            
            # 2. Zocalo globalizado
            msg_publicitario = cfg_data.get("mensaje_zocalo", "")
            if not msg_publicitario:
                msg_publicitario = f"👨‍👩‍👧‍👦 ¡La mejor calidad para disfrutar en familia! Más de 500 familias nos eligen cada semana. ¡Gracias por su apoyo! ❤️ | Consultas por WhatsApp al: {telefono_negocio}"
            self.mensaje.actualizar_texto(msg_publicitario)
            
            # Actualizar tiempo de rotación
            nueva_rotacion = cfg_data.get("carteleria_rotacion", 15) * 1000
            if hasattr(self, 'rotacion_ms') and nueva_rotacion != self.rotacion_ms:
                self.rotacion_ms = nueva_rotacion
                if self.timer.isActive() and self.stack.currentIndex() == 0:
                    self.timer.setInterval(self.rotacion_ms)
                    
            self.tiempo_sos_ms = cfg_data.get("carteleria_tiempo_sos", 10) * 1000
            # Garantizar al menos 3 ciclos de rotación normal antes del SOS para que la pantalla no parezca trabada
            self.frec_sos = max(3, cfg_data.get("carteleria_frec_sos", 3))

            # 2. Ofertas SOS (Múltiples y rotativas)
            oferta_sos = data.get("sos", [])
            self.lista_ofertas_sos = oferta_sos
            if self.lista_ofertas_sos:
                self.hay_oferta_sos = True
                if self.stack.currentIndex() == 1:
                    self._actualizar_datos_sos()
            else:
                self.hay_oferta_sos = False
                if self.stack.currentIndex() == 1:
                    self.layout_manager.fade_to_index(0)

            # 3. Precios Generales
            rows_precios = data.get("precios", [])
            import hashlib, json
            stable_str = json.dumps(rows_precios, sort_keys=True)
            current_hash = hashlib.md5(stable_str.encode()).hexdigest()
            if not hasattr(self, 'last_precios_hash') or self.last_precios_hash != current_hash:
                self.last_precios_hash = current_hash
                if hasattr(self, 'zona2_precios') and hasattr(self.zona2_precios, 'motor'):
                    self.zona2_precios.motor.start()
                    
            # 4. Top 10 para Banderin y Carrusel (Diccionario Hoy, Semana, Mes)
            rows_top10 = data.get("top10", {})
            if rows_top10:
                self.datos_destacados = rows_top10

        except Exception as e:
            logger.warning(f"Error procesando datos de carteleria (API o Caché): {e}")

    def _actualizar_datos_sos(self, rotar_indice=False):
        if not hasattr(self, 'lista_ofertas_sos') or not self.lista_ofertas_sos:
            return
        if rotar_indice:
            self.indice_sos_actual = (getattr(self, 'indice_sos_actual', 0) + 1) % len(self.lista_ofertas_sos)
        idx = min(getattr(self, 'indice_sos_actual', 0), len(self.lista_ofertas_sos) - 1)
        r_sos = self.lista_ofertas_sos[idx]
        if isinstance(r_sos, dict):
            nombre = r_sos.get('nombre') or ''
            precio = float(r_sos.get('precio') or 0.0)
            ofertas = [float(r_sos.get(k) or 0.0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
            validas = [x for x in ofertas if x > 0]
            precio_oferta = min(validas) if validas else 0.0
            
            cant_of = float(r_sos.get('cant_oferta') or 0)
            t_un = ""
            if cant_of > 0:
                t_un = str(r_sos.get('tipo_unidad_oferta', '')).strip().lower()
                t_un = "Unidades" if ('unidad' in t_un or t_un == 'u') else "Kilos"
        else:
            nombre = r_sos[0] if r_sos[0] else ''
            precio = float(r_sos[1] if r_sos[1] else 0.0)
            ofertas = [float(r_sos[i] if len(r_sos)>i and r_sos[i] else 0.0) for i in (2, 3, 4)]
            validas = [x for x in ofertas if x > 0]
            precio_oferta = min(validas) if validas else 0.0
            
            cant_of = float(r_sos[5]) if len(r_sos) > 5 and r_sos[5] else 0.0
            t_un = ""
            if cant_of > 0:
                t_un = str(r_sos[6]).strip().lower() if len(r_sos) > 6 and r_sos[6] else ''
                t_un = "Unidades" if ('unidad' in t_un or t_un == 'u') else "Kilos"
                
        self.page_sos.actualizar(nombre, precio, precio_oferta, cant_of, t_un)

    def _ciclo_inteligente(self):
        # Si estamos en la pantalla espía, no hacer nada automático
        if self.stack.currentIndex() == 2:
            return
            
        # Rotar e intercalar automáticamente entre Cartel de Combos/Promos y Chef Lobo
        if hasattr(self, 'promo_manager'):
            self.promo_manager.rotar()
            
        if self.estado_sos_activo:
            # Si estábamos en SOS, volver a la normalidad
            self.estado_sos_activo = False
            self.layout_manager.fade_to_index(0)
            # Restaurar el timer al tiempo normal de rotación de las grillas
            self.timer.start(self.rotacion_ms)
        else:
            # No rotar las grillas automáticamente, solo incrementar contador para el SOS
            self.contador_rotacion += 1
            
            # Verificar si toca Oferta Relámpago (SOS)
            if hasattr(self, 'hay_oferta_sos') and self.hay_oferta_sos:
                if self.contador_rotacion >= self.frec_sos:
                    self.contador_rotacion = 0
                    self.estado_sos_activo = True
                    self._actualizar_datos_sos(rotar_indice=True)
                    self.layout_manager.fade_to_index(1)
                    # Cambiar el timer al tiempo de SOS
                    self.timer.start(self.tiempo_sos_ms)


    def _guardar_sugerencia_activa(self, productos_sugeridos):
        import json, os, time
        from src.utils.paths import get_base_path
        path = os.path.join(get_base_path(), "sugerencia_activa.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "productos": productos_sugeridos,
                    "timestamp": time.time()
                }, f, ensure_ascii=False)
        except: pass

    def _espia_ui_log(self, msg):
        try:
            import os
            from datetime import datetime
            from src.utils.paths import get_base_path
            log_p = os.path.join(get_base_path(), "logs", "espia_debug.log")
            with open(log_p, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] [MAIN_THREAD] {msg}\n")
        except: pass

    def _on_espia_limpiar(self):
        import time
        self._espia_ui_log("Slot Limpiar ejecutado en hilo principal")
        tiempo_abierto = time.time() - getattr(self, 'ultimo_cambio_ia', 0)
        
        def forzar_cierre():
            self._espia_ui_log("Forzando cierre de Pantalla Espia")
            self.ultimo_cambio_ia = time.time() - 16
            if self.stack.currentIndex() == 2:
                self.layout_manager.fade_to_index(0)
                if hasattr(self, 'timer'): self.timer.start(self.rotacion_ms if hasattr(self, 'rotacion_ms') else 15000)
                if hasattr(self, 'timer_db'): self.timer_db.start(10000)

        if tiempo_abierto < 2.0:
            QTimer.singleShot(2500, forzar_cierre)
        else:
            forzar_cierre()

    def _on_combo_triggered(self, nombre_combo, precio_original, precio_final, ahorro):
        import time
        self._espia_ui_log(f"COMBO TRIGGERED. Ahorro: {ahorro}")
        self.ultimo_cambio_ia = time.time()
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()
        if hasattr(self, 'timer_db') and self.timer_db.isActive(): self.timer_db.stop()
        
        try:
            self.page_espia.play_combo(nombre_combo, precio_original, precio_final, ahorro)
        except Exception as inner_e:
            import traceback
            self._espia_ui_log(f"ERROR CRITICO play_combo: {traceback.format_exc()}")
        
        if hasattr(self, 'banderin'): self.banderin.hide()
        QTimer.singleShot(10, lambda: self.layout_manager.fade_to_index(2))
        
        def restaurar_estado():
            self._espia_ui_log("Restaurando estado tras 6s")
            self.layout_manager.fade_to_index(0)
            if hasattr(self, 'timer'): self.timer.start(self.rotacion_ms if hasattr(self, 'rotacion_ms') else 15000)
            if hasattr(self, 'timer_db'): self.timer_db.start(10000)
            
        QTimer.singleShot(6000, restaurar_estado)

    def closeEvent(self, event):
        threads = [
            getattr(self, 'espia_worker', None),
            getattr(self, 'db_worker', None),
            getattr(self, 'clima_worker', None),
            getattr(getattr(self, 'zona1_carrusel', None), 'motor', None),
            getattr(getattr(self, 'zona2_precios', None), 'motor', None),
            getattr(getattr(self, 'zona3_extra1', None), 'motor', None),
            getattr(getattr(self, 'zona4_extra2', None), 'motor', None),
        ]
        for t in threads:
            if t and hasattr(t, 'isRunning') and t.isRunning():
                try:
                    if hasattr(t, 'running'):
                        t.running = False
                    t.quit()
                    if not t.wait(400):
                        t.terminate()
                        t.wait(100)
                except Exception:
                    pass
        super().closeEvent(event)
