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
from src.carteleria.info_negocio import InfoNegocio
from src.carteleria.mensaje import Mensaje
from src.carteleria.pantalla1 import Pantalla1
from src.carteleria.pantalla2 import Pantalla2
from src.carteleria.pantalla3 import Pantalla3
from src.carteleria.pantalla4 import Pantalla4
from src.carteleria.pantalla_espia import PantallaEspia
from src.carteleria.oferta_relampago import OfertaRelampago
from src.carteleria.banderin import BanderinVolador
from src.carteleria.motor_logico import MotorLogico
import time
from src.carteleria.gemini_worker import GeminiWorker

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    db_manager = None

logger = logging.getLogger("Carteleria_Autonoma")

from PyQt6.QtCore import QThread
class EspiaWorker(QThread):
    recomendacion_lista = pyqtSignal(float, str, list, list)
    limpiar_solicitado = pyqtSignal()

    def __init__(self, master_ip, path_local):
        super().__init__()
        self.master_ip = master_ip
        self.path_local = path_local
        self.live_scan_last_mtime = 0
        self.live_scan_processed = True
        self.live_scan_last_change_time = 0
        self.ultimo_espia_timestamp = 0
        self.running = True

    def espia_log(self, msg):
        print(msg)
        try:
            import os
            from datetime import datetime
            from src.utils.paths import get_base_path
            log_p = os.path.join(get_base_path(), "logs", "espia_debug.log")
            with open(log_p, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        except: pass

    def run(self):
        import json, os, urllib.request, time
        from src.utils.paths import get_base_path
        
        while self.running:
            data = None
            mtime = 0
            
            # Buscar IP dinamicamente si no hay
            master_ip = self.master_ip
            es_local = False
            if master_ip in ("127.0.0.1", "localhost", "0.0.0.0", ""): es_local = True
            try:
                import socket
                if master_ip == socket.gethostbyname(socket.gethostname()): es_local = True
            except: pass
            if es_local and os.path.exists(self.path_local): master_ip = ""

            if not master_ip and not os.path.exists(self.path_local):
                from src.network.network_engine import get_network_engine
                engine = get_network_engine()
                if engine and hasattr(engine, '_active_ips') and engine._active_ips:
                    for rol, ip in engine._active_ips.items():
                        if any(x in rol.upper() for x in ["CAJA", "CAJERO", "TERMINAL", "ADMIN", "JEFE"]):
                            master_ip = ip
                            break
                    if not master_ip and engine._active_ips:
                        master_ip = list(engine._active_ips.values())[0]

            try:
                if master_ip:
                    url = f"http://{master_ip}:8000/api/live_scan"
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=0.2) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        if data: mtime = data.get("timestamp", 0)
                else:
                    if os.path.exists(self.path_local):
                        mtime = os.path.getmtime(self.path_local)
                        with open(self.path_local, "r", encoding="utf-8") as f:
                            data = json.load(f)
            except Exception as e:
                time.sleep(0.2)
                continue

            if not data or mtime == 0:
                time.sleep(0.2)
                continue

            if data.get("limpiar", False):
                if mtime != self.live_scan_last_mtime:
                    self.live_scan_last_mtime = mtime
                    self.espia_log("[ESPIA_DEBUG] Limpiar = True detectado.")
                    self.limpiar_solicitado.emit()
                time.sleep(0.2)
                continue

            if mtime != self.live_scan_last_mtime:
                self.espia_log(f"[ESPIA_DEBUG] Nuevo mtime detectado: {mtime}. Cajero escaneando...")
                self.live_scan_last_mtime = mtime
                self.live_scan_last_change_time = time.time()
                self.live_scan_processed = False
                time.sleep(0.1)
                continue

            if not self.live_scan_processed:
                if time.time() - self.live_scan_last_change_time >= 0.5:
                    self.espia_log(f"[ESPIA_DEBUG] Han pasado 0.5s de inactividad. Procesando ticket final...")
                    self.live_scan_processed = True
                    
                    ts = data.get("timestamp", 0)
                    if ts > self.ultimo_espia_timestamp:
                        self.ultimo_espia_timestamp = ts
                        ahorro = data.get("ahorro", 0.0)
                        carrito = data.get("carrito", [])
                        prod = data.get("ultimo_escaneado", "")
                        
                        if ahorro > 0 or carrito or prod:
                            self.espia_log(f"[ESPIA_DEBUG] Evaluando salto Inteligencia Artificial (Ahorro=${ahorro}).")
                            cart_eval = carrito if carrito else [{'producto': prod, 'precio': 0}]
                            from src.carteleria.motor_ia import MotorIA
                            from src.base_de_datos.database import db_manager
                            clima_para_ia = ("sol", "20°C Pilar")
                            msg, l_gas, l_aho = MotorIA.generar_recomendacion_dual(db_manager, ahorro, cart_eval, clima_para_ia)
                            self.espia_log("[ESPIA_DEBUG] Recomendacion generada en Worker. Emitiendo...")
                            self.recomendacion_lista.emit(ahorro, msg or "¡EXCELENTE ELECCIÓN!", l_gas, l_aho)
            
            time.sleep(0.2)

class CarteleriaMain(QWidget):
    request_screen = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout_mode = 4 
        self.img_index = 0
        self.datos_destacados = []
        self.combos_relacionados = [
            ("Asado de Novillo", "Carbón 4kg y Limón fresco"),
            ("Vacío", "Provoleta y Pan de Campo"),
            ("Pechito de Cerdo", "Salsa BBQ y Papas Fritas")
        ]
        
        self.setObjectName("CarteleriaMain")
        
        # --- FONDO macOS ---
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        img_path = os.path.join(os.path.dirname(__file__), "assets", "macos_bg.png")
        if os.path.exists(img_path):
            self.bg_label.setPixmap(QPixmap(img_path))
        else:
            self.setStyleSheet(f"#CarteleriaMain {{ background-color: {C_THEME['bg']}; }}")

        # --- INSTANCIAR ZONAS MODULARES ---
        self.info_negocio = InfoNegocio()
        self.info_negocio.btn_modo.clicked.connect(self._ciclar_layout)
        self.info_negocio.config_requested.connect(self._abrir_configuracion)
        
        self.mensaje = Mensaje()
        self.zona1_carrusel = Pantalla1()
        self.zona2_precios = Pantalla2()
        self.zona3_extra1 = Pantalla3()
        self.zona4_extra2 = Pantalla4()
        
        self._build_ui()
        
        # ⏱️ TIMER ROTACIÓN PROMOCIONES
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._actualizar_pantallas_promocionales)
        self.rotacion_ms = 16000 # Por defecto
        self.timer.start(self.rotacion_ms) 
        
        self.timer_db = QTimer(self)
        self.timer_db.timeout.connect(self._sincronizar_todo_con_db)
        self.timer_db.start(10000)

        self.clima_pilar = ("sol", "22°C Pilar")
        self._obtener_clima()
        self.timer_clima = QTimer(self)
        self.timer_clima.timeout.connect(self._obtener_clima)
        self.timer_clima.start(3600000)

        self.timer_vuelo = QTimer(self)
        
        def intentar_lanzar_banderin():
            if self.stack.currentIndex() < 2:  # Solo lanzar en pantallas normales (0 o 1)
                self.banderin.lanzar(self.datos_destacados)
                
        self.timer_vuelo.timeout.connect(intentar_lanzar_banderin)
        self.timer_vuelo.start(35000) 
        
        self._sincronizar_todo_con_db() 
        
        # 🤖 INICIAR CEREBRO GEMINI EN SEGUNDO PLANO (Recolección 1 vez al día)
        GeminiWorker.start_worker()
        
        # 👀 OJO ESPÍA (WORKER EN BACKGROUND)
        from src.utils.paths import get_base_path
        from src.config import config
        path_ls = os.path.join(get_base_path(), "live_scan.json")
        master_ip = config.get("carteleria_master_ip", "")
        self.espia_worker = EspiaWorker(master_ip, path_ls)
        self.espia_worker.recomendacion_lista.connect(self._on_espia_recomendacion)
        self.espia_worker.limpiar_solicitado.connect(self._on_espia_limpiar)
        self.espia_worker.start()
        
        self.ultimo_cambio_ia = __import__('time').time() - 16

        # ── HEARTBEAT HACIA EL TERMINAL ─────────────────────────────────────
        # La cartelería emite un latido UDP cada 10s con rol "carteleria" para
        # que el terminal actualice su indicador ⚫ → 🟢.
        self.timer_heartbeat = QTimer(self)
        self.timer_heartbeat.timeout.connect(self._emitir_heartbeat)
        self.timer_heartbeat.start(10000)   # cada 10 segundos
        QTimer.singleShot(500, self._emitir_heartbeat)  # primer latido a los 0.5s

        # ── ESCUCHAR HEARTBEATS DEL TERMINAL ────────────────────────────────
        # Si el engine ya está inicializado (cajero/admin en el mismo proceso)
        # conectamos directamente sus señales al indicador del header.
        QTimer.singleShot(800, self._conectar_engine_indicador)

        # Botón de emergencia F11 (Global para esta ventana)
        from PyQt6.QtGui import QShortcut, QKeySequence
        self.shortcut_f11 = QShortcut(QKeySequence(Qt.Key_F11), self)
        self.shortcut_f11.activated.connect(self._f11_pressed)

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
        
        self._aplicar_layout()

    def _ciclar_layout(self):
        self.layout_mode += 1
        if self.layout_mode > 4:
            self.layout_mode = 1
        self._aplicar_layout()

    def _aplicar_layout(self):
        for i in reversed(range(self.grid.count())): 
            w = self.grid.itemAt(i).widget()
            if w:
                self.grid.removeWidget(w)
            
        for i in range(4): self.grid.setColumnStretch(i, 0)
        self.grid.setRowStretch(0, 0)
        self.grid.setRowStretch(1, 0)
            
        if self.layout_mode == 1:
            self.grid.addWidget(self.zona2_precios, 0, 0)
            self.grid.setColumnStretch(0, 1)
        elif self.layout_mode == 2:
            self.grid.addWidget(self.zona1_carrusel, 0, 0)
            self.grid.addWidget(self.zona2_precios, 0, 1)
            self.grid.setColumnStretch(0, 1)
            self.grid.setColumnStretch(1, 1)
        elif self.layout_mode == 3:
            self.grid.addWidget(self.zona1_carrusel, 0, 0)
            self.grid.addWidget(self.zona2_precios, 0, 1)
            self.grid.addWidget(self.zona3_extra1, 0, 2)
            self.grid.setColumnStretch(0, 1)
            self.grid.setColumnStretch(1, 1)
            self.grid.setColumnStretch(2, 1)
        elif self.layout_mode == 4:
            self.grid.addWidget(self.zona1_carrusel, 0, 0)
            self.grid.addWidget(self.zona2_precios, 0, 1) 
            self.grid.addWidget(self.zona3_extra1, 0, 2)
            self.grid.addWidget(self.zona4_extra2, 0, 3)
            self.grid.setColumnStretch(0, 1)
            self.grid.setColumnStretch(1, 1)
            self.grid.setColumnStretch(2, 1)
            self.grid.setColumnStretch(3, 1)
            
        self.grid.setRowStretch(0, 1) 
        self._actualizar_pantallas_promocionales()

    def _obtener_clima(self):
        try:
            import json
            # Coordenadas de Pilar, Buenos Aires
            url = "https://api.open-meteo.com/v1/forecast?latitude=-34.4587&longitude=-58.9142&current_weather=true"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                temp = data.get("current_weather", {}).get("temperature", 22)
                code = data.get("current_weather", {}).get("weathercode", 0)
                
                icon_name = "sol"
                if code in [1, 2, 3, 45, 48]:
                    icon_name = "nube"
                elif code >= 51:
                    icon_name = "lluvia"
                
                self.clima_pilar = (icon_name, f"{int(temp)}°C Pilar")
        except Exception as e:
            print(f"Error al obtener clima: {e}")

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

    def _sincronizar_todo_con_db(self):
        try:
            if db_manager:
                db = db_manager
                is_mariadb = getattr(db, "db_engine_type", "sqlite") == "mariadb"
                rand_func = "RAND()" if is_mariadb else "RANDOM()"
                
                # --- LECTURA DE CONFIGURACIÓN DIRECTA ---
                try:
                    import json
                    from src.utils.paths import get_base_path
                    config_path = os.path.join(get_base_path(), "config.json")
                    with open(config_path, "r", encoding="utf-8") as f:
                        cfg_data = json.load(f)
                    nombre_negocio = cfg_data.get("business_name", "Carnicería")
                    telefono_negocio = cfg_data.get("phone", "No disponible")
                    
                    self.info_negocio.actualizar_nombre(nombre_negocio)
                    msg_publicitario = f"👨‍👩‍👧‍👦 ¡La mejor calidad para disfrutar en familia! Más de 500 familias nos eligen cada semana. ¡Gracias por su apoyo! ❤️ | Consultas por WhatsApp al: {telefono_negocio}"
                    self.mensaje.actualizar_texto(msg_publicitario)
                    
                    # Actualizar tiempo de rotación
                    nueva_rotacion = cfg_data.get("carteleria_rotacion", 15) * 1000
                    if hasattr(self, 'rotacion_ms') and nueva_rotacion != self.rotacion_ms:
                        self.rotacion_ms = nueva_rotacion
                        if self.timer.isActive() and self.stack.currentIndex() == 0:
                            self.timer.setInterval(self.rotacion_ms)
                            
                    self.tiempo_sos_ms = cfg_data.get("carteleria_tiempo_sos", 10) * 1000
                    self.frec_sos = cfg_data.get("carteleria_frec_sos", 2)
                except Exception as e:
                    logger.warning(f"Error cargando config.json: {e}")
                
                sos_query = f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio FROM productos WHERE es_sos = 1 AND (precio > 0 OR precio_oferta > 0 OR precio_oferta_relampago > 0) ORDER BY {rand_func} LIMIT 1"
                oferta_sos = db.execute_query(sos_query)
                if oferta_sos:
                    r_sos = oferta_sos[0]
                    if isinstance(r_sos, dict):
                        nombre = r_sos.get('nombre') or ''
                        precio = float(r_sos.get('precio') or 0.0)
                        ofertas = [float(r_sos.get(k) or 0.0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
                        validas = [x for x in ofertas if x > 0]
                        precio_oferta = min(validas) if validas else 0.0
                    else:
                        nombre = r_sos[0] if r_sos[0] else ''
                        precio = float(r_sos[1] if r_sos[1] else 0.0)
                        ofertas = [float(r_sos[i] if len(r_sos)>i and r_sos[i] else 0.0) for i in (2, 3, 4)]
                        validas = [x for x in ofertas if x > 0]
                        precio_oferta = min(validas) if validas else 0.0
                    self.page_sos.actualizar(nombre, precio, precio_oferta)
                    self.hay_oferta_sos = True
                else:
                    self.hay_oferta_sos = False
                    if self.stack.currentIndex() == 1:
                        self._fade_to_index(0)
                
                precios_query = "SELECT categoria, nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio FROM productos WHERE precio > 0 ORDER BY categoria"
                rows_precios = db.execute_query(precios_query)
                import hashlib
                current_hash = hashlib.md5(str(rows_precios).encode()).hexdigest()
                if not hasattr(self, 'last_precios_hash') or self.last_precios_hash != current_hash:
                    self.last_precios_hash = current_hash
                    if rows_precios:
                        self.zona2_precios.set_items(self._agrupar(rows_precios))
                
                import time
                now = time.time()
                if not hasattr(self, 'last_top10_update') or (now - self.last_top10_update) > 60:
                    self.last_top10_update = now
                    
                    query_hoy = """
                    SELECT p.nombre, p.precio, p.precio_oferta, p.precio_oferta_relampago, p.precio_oferta_promedio, SUM(d.cantidad) as total_vendido
                    FROM detalles_ventas d
                    JOIN ventas v ON d.id_venta = v.id
                    JOIN productos p ON d.id_producto = p.id
                    WHERE DATE(v.fecha) = CURDATE() AND v.estado != 'CANCELADA' AND p.precio > 0
                    GROUP BY p.id
                    ORDER BY total_vendido DESC
                    LIMIT 10
                    """
                    query_semanal = """
                    SELECT p.nombre, p.precio, p.precio_oferta, p.precio_oferta_relampago, p.precio_oferta_promedio, SUM(d.cantidad) as total_vendido
                    FROM detalles_ventas d
                    JOIN ventas v ON d.id_venta = v.id
                    JOIN productos p ON d.id_producto = p.id
                    WHERE v.fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY) AND v.estado != 'CANCELADA' AND p.precio > 0
                    GROUP BY p.id
                    ORDER BY total_vendido DESC
                    LIMIT 10
                    """
                    query_mensual = """
                    SELECT p.nombre, p.precio, p.precio_oferta, p.precio_oferta_relampago, p.precio_oferta_promedio, SUM(d.cantidad) as total_vendido
                    FROM detalles_ventas d
                    JOIN ventas v ON d.id_venta = v.id
                    JOIN productos p ON d.id_producto = p.id
                    WHERE MONTH(v.fecha) = MONTH(CURDATE()) AND YEAR(v.fecha) = YEAR(CURDATE()) AND v.estado != 'CANCELADA' AND p.precio > 0
                    GROUP BY p.id
                    ORDER BY total_vendido DESC
                    LIMIT 10
                    """
                    try:
                        self.top10_hoy = db.execute_query(query_hoy) or []
                        self.top10_semanal = db.execute_query(query_semanal) or []
                        self.top10_mensual = db.execute_query(query_mensual) or []
                    except Exception as e:
                        logger.error(f"Error queries Top10: {e}")
                        self.top10_hoy = []
                        self.top10_semanal = []
                        self.top10_mensual = []
                        
                    all_tops = self.top10_hoy + self.top10_semanal + self.top10_mensual
                    if all_tops:
                        unique = {}
                        for r in all_tops:
                            if isinstance(r, dict):
                                ofertas = [float(r.get(k) or 0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
                                validas = [x for x in ofertas if x > 0]
                                p_of = min(validas) if validas else 0.0
                                unique[r['nombre']] = (r['nombre'], float(r['precio'] or 0), p_of)
                            else:
                                ofertas = [float(r[i] if len(r)>i and r[i] else 0) for i in (2, 3, 4)]
                                validas = [x for x in ofertas if x > 0]
                                p_of = min(validas) if validas else 0.0
                                unique[r[0]] = (r[0], float(r[1] or 0), p_of)
                        self.datos_destacados = list(unique.values())
                    else:
                        destacados_query = f"SELECT nombre, precio, precio_oferta, precio_oferta_relampago, precio_oferta_promedio FROM productos WHERE precio > 0 ORDER BY {rand_func} LIMIT 10"
                        rows_destacados = db.execute_query(destacados_query)
                        self.datos_destacados = []
                        if rows_destacados:
                            for r in rows_destacados:
                                if isinstance(r, dict):
                                    ofertas = [float(r.get(k) or 0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
                                    validas = [x for x in ofertas if x > 0]
                                    p_of = min(validas) if validas else 0.0
                                    self.datos_destacados.append((r.get('nombre', ''), float(r.get('precio', 0)), p_of))
                                else:
                                    ofertas = [float(r[i] if len(r)>i and r[i] else 0) for i in (2, 3, 4)]
                                    validas = [x for x in ofertas if x > 0]
                                    p_of = min(validas) if validas else 0.0
                                    self.datos_destacados.append((r[0], float(r[1] if r[1] else 0), p_of))
            else:
                self._cargar_demo_completa()
                
        except Exception as e:
            logger.warning(f"Simulando Base de Datos: {e}")
            self._cargar_demo_completa()

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
                self._fade_to_index(0)
                if hasattr(self, 'timer'): self.timer.start(self.rotacion_ms if hasattr(self, 'rotacion_ms') else 15000)
                if hasattr(self, 'timer_db'): self.timer_db.start(10000)

        if tiempo_abierto < 2.0:
            QTimer.singleShot(2500, forzar_cierre)
        else:
            forzar_cierre()

    def _on_espia_recomendacion(self, ahorro_total, msg, l_gastador, l_ahorrador):
        import time
        self._espia_ui_log(f"Slot Recomendacion ejecutado. Ahorro: {ahorro_total}")
        self.ultimo_cambio_ia = time.time()
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()
        if hasattr(self, 'timer_db') and self.timer_db.isActive(): self.timer_db.stop()
        
        clima_para_ia = getattr(self, 'clima_pilar', ("sol", "20°C Pilar"))
        try:
            self.page_espia.actualizar(ahorro_total, msg, l_gastador, l_ahorrador, clima_para_ia)
            self._espia_ui_log("page_espia.actualizar sin errores")
        except Exception as inner_e:
            import traceback
            self._espia_ui_log(f"ERROR CRITICO renderizando page_espia: {traceback.format_exc()}")
        
        if hasattr(self, 'banderin'): self.banderin.hide()
        QTimer.singleShot(10, lambda: self._fade_to_index(2))
        sugeridos = [p.get('nombre', '') for p in (l_gastador + l_ahorrador)]
        self._guardar_sugerencia_activa(sugeridos)
        self._espia_ui_log("Fade to index(2) programado y Timer de retorno fijado en 15s")
        
        def restaurar_estado():
            self._espia_ui_log("Restaurando estado tras 15s")
            self._fade_to_index(0)
            if hasattr(self, 'timer'): self.timer.start(self.rotacion_ms if hasattr(self, 'rotacion_ms') else 15000)
            if hasattr(self, 'timer_db'): self.timer_db.start(10000)
            
        QTimer.singleShot(15000, restaurar_estado)
    def _actualizar_pantallas_promocionales(self):
        import time
        inactividad = time.time() - getattr(self, 'ultimo_cambio_ia', 0)
        
        # --- Lógica de Protector de Pantalla (Oferta Relampago tras 10 min de inactividad) ---
        if getattr(self, 'hay_oferta_sos', False) and inactividad > 600:
            if self.stack.currentIndex() != 1:
                try:
                    import os, datetime
                    from src.utils.paths import get_base_path
                    log_p = os.path.join(get_base_path(), "logs", "espia_debug.log")
                    with open(log_p, "a", encoding="utf-8") as f:
                        f.write(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] [ESPIA_DEBUG] 10 minutos inactividad. Protector.\n")
                except: pass
                self._fade_to_index(1)
                self.timer.setInterval(10000) # Chequeo cada 10s mientras está en protector
            return # Se queda en pantalla completa SOS
            
        # Si estaba en SOS pero hubo actividad, vuelve a 0
        if self.stack.currentIndex() == 1 and inactividad <= 600:
            self._fade_to_index(0)
            self.timer.setInterval(getattr(self, 'rotacion_ms', 16000))

        # --- Flujo normal ---
        if self.stack.currentIndex() not in (0, 1):
            # Si estaba en IA (2 o 3), lo devolvemos a 0
            self._fade_to_index(0)
            
        if not self.datos_destacados: return
        
        self.img_index = (self.img_index + 1) % len(self.datos_destacados)
        prod_actual = self.datos_destacados[self.img_index]
        
        # --- PANTALLA 1 (Zona 1): Alternar Especial vs Top 10 ---
        def parse_top(top_list):
            parsed = []
            for r in top_list:
                if isinstance(r, dict):
                    ofertas = [float(r.get(k) or 0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
                    validas = [x for x in ofertas if x > 0]
                    p_of = min(validas) if validas else 0.0
                    parsed.append((r.get('nombre', ''), float(r.get('precio', 0)), p_of))
                else:
                    ofertas = [float(r[i] if len(r)>i and r[i] else 0) for i in (2, 3, 4)]
                    validas = [x for x in ofertas if x > 0]
                    p_of = min(validas) if validas else 0.0
                    parsed.append((r[0], float(r[1] if r[1] else 0), p_of))
            return parsed

        choice = random.randint(1, 4)
        if choice == 1:
            poferta = prod_actual[2] if len(prod_actual) > 2 else 0
            self.zona1_carrusel.actualizar_especial(prod_actual[0], prod_actual[1], poferta)
        elif choice == 2 and hasattr(self, 'top10_hoy') and self.top10_hoy:
            self.zona1_carrusel.actualizar_top10(parse_top(self.top10_hoy), "🔥 Top Ventas Hoy 🔥")
        elif choice == 3 and hasattr(self, 'top10_semanal') and self.top10_semanal:
            self.zona1_carrusel.actualizar_top10(parse_top(self.top10_semanal), "🔥 Top Ventas Semana 🔥")
        elif hasattr(self, 'top10_mensual') and self.top10_mensual:
            self.zona1_carrusel.actualizar_top10(parse_top(self.top10_mensual), "🔥 Top Ventas del Mes 🔥")
        else:
            poferta = prod_actual[2] if len(prod_actual) > 2 else 0
            self.zona1_carrusel.actualizar_especial(prod_actual[0], prod_actual[1], poferta)
            
        if len(self.datos_destacados) > 1:
            prod_siguiente = self.datos_destacados[(self.img_index + 1) % len(self.datos_destacados)]
            
            # --- PANTALLA 3 (Zona 3): Alternar Destacada vs Combo ---
            if random.choice([True, False]):
                poferta_dest = prod_siguiente[2] if len(prod_siguiente) > 2 else 0
                self.zona3_extra1.actualizar_destacada(prod_siguiente[0], prod_siguiente[1], poferta_dest)
            else:
                # Generar un combo real a partir del inventario
                nombres = []
                if db_manager:
                    is_mariadb = getattr(db_manager, "db_engine_type", "sqlite") == "mariadb"
                    rand_func = "RAND()" if is_mariadb else "RANDOM()"
                    res = db_manager.execute_query(f"SELECT nombre FROM productos WHERE precio > 0 ORDER BY {rand_func} LIMIT 3")
                    if res and len(res) >= 2:
                        nombres = [r.get('nombre', '') if isinstance(r, dict) else r[0] for r in res]
                        
                if nombres:
                    centro_compra_simulado = random.choice([prod_siguiente[0], prod_actual[0]])
                    self.zona3_extra1.actualizar_combo(centro_compra_simulado, nombres)
                else:
                    # Si falla, simplemente mostrar un destacado extra
                    poferta_dest = prod_siguiente[2] if len(prod_siguiente) > 2 else 0
                    self.zona3_extra1.actualizar_destacada(prod_siguiente[0], prod_siguiente[1], poferta_dest)
            
            prod_tercero = self.datos_destacados[(self.img_index + 2) % len(self.datos_destacados)]
            
            # --- PANTALLA 4 (Zona 4): Alternar Recomendacion vs IA ---
            if random.choice([True, False]):
                self.timer.setInterval(self.rotacion_ms if hasattr(self, 'rotacion_ms') else 16000) # Tiempo configurado
                poferta = prod_tercero[2] if len(prod_tercero) > 2 else 0
                self.zona4_extra2.actualizar_recomendacion(prod_tercero[0], prod_tercero[1], poferta)
            else:
                self.timer.setInterval((self.rotacion_ms if hasattr(self, 'rotacion_ms') else 16000) + 12000) # MÁS TIEMPO para IA
                msg, prod, precio, precio_oferta = MotorLogico.generar_recomendacion(
                    db_manager, 
                    self.clima_pilar, 
                    self.datos_destacados
                )
                self.zona4_extra2.actualizar_ia(msg, prod, precio, precio_oferta, self.clima_pilar)

    # ── SIMULACIÓN DE DATOS ──
    def _fade_to_index(self, index):
        if self.stack.currentIndex() == index:
            return
            
        # El QGraphicsOpacityEffect causaba pantalla en blanco en algunos entornos Windows,
        # así que revertimos al cambio de índice instantáneo para estabilizar.
        print(f'[DEBUG] Cambiando a indice {index}'); self.stack.setCurrentIndex(index)

    def _agrupar(self, rows):
        agrupados = {}
        for r in rows:
            if isinstance(r, dict):
                cat = r.get('categoria', 'OTROS')
                nombre = r.get('nombre', '')
                precio = float(r.get('precio', 0.0))
                ofertas = [float(r.get(k) or 0) for k in ('precio_oferta', 'precio_oferta_relampago', 'precio_oferta_promedio')]
                validas = [x for x in ofertas if x > 0]
                precio_oferta = min(validas) if validas else 0.0
            else:
                cat = str(r[0])
                nombre = str(r[1])
                precio = float(r[2]) if len(r) > 2 else 0.0
                ofertas = [float(r[i] if len(r)>i and r[i] else 0) for i in (3, 4, 5)]
                validas = [x for x in ofertas if x > 0]
                precio_oferta = min(validas) if validas else 0.0

            if cat not in agrupados: agrupados[cat] = []
            agrupados[cat].append((nombre, precio, precio_oferta))
        return agrupados

    def _cargar_destacados_demo(self):
        # 10 productos para que el Top 10 esté lleno
        self.datos_destacados = [
            ("Asado de Novillo", 7500, 0),
            ("Ojo de Bife Madurado", 12500, 0),
            ("Matambre de Cerdo", 8500, 0),
            ("Chorizo Casero", 4500, 0),
            ("Costillar Especial", 6800, 0),
            ("Bife Ancho", 9000, 0),
            ("Pechito con Manta", 5800, 0),
            ("Vacío Seleccionado", 8200, 0),
            ("Salchicha Parrillera", 5200, 0),
            ("Provoleta", 2500, 0)
        ]

    def _cargar_demo_completa(self):
        self._cargar_destacados_demo()
        demo_precios = {
            "CORTES VACUNOS": [
                ("Asado de Novillo", 7500, 0),
                ("Ojo de Bife Madurado", 12500, 0),
                ("Bife de Chorizo", 11000, 0),
                ("Roast Beef", 6200, 0),
                ("Tapa de Asado", 6800, 0),
                ("Paleta", 5900, 0)
            ],
            "CERDO": [
                ("Pechito", 5500, 0),
                ("Bondiola", 7200, 0),
                ("Carré", 6800, 0),
                ("Costillitas", 6000, 0),
                ("Matambrito", 8500, 0)
            ],
            "EMBUTIDOS": [
                ("Chorizo Puro Cerdo", 4500, 0),
                ("Morcilla Vasca", 3800, 0),
                ("Salchicha Parrillera", 5200, 0)
            ]
        }
        self.zona2_precios.set_items(demo_precios)

    def _conectar_engine_indicador(self):
        """Conecta las señales del NetworkEngine al indicador de red del header."""
        try:
            from src.network.network_engine import get_network_engine
            engine = get_network_engine()
            if not engine:
                return

            # Escuchar heartbeats que llegan al engine (de cajero u otros)
            # El engine emite heartbeat_received(origen) cuando recibe cualquier latido
            try:
                engine.heartbeat_received.connect(self._on_heartbeat_engine)
            except Exception:
                pass

            # Si se pierde conexión con algún nodo
            try:
                engine.connection_lost.connect(self._on_connection_lost_engine)
            except Exception:
                pass
            
            # Escuchar mensajes de prueba
            try:
                engine.message_received.connect(self._on_message_received_engine)
            except Exception:
                pass
        except Exception:
            pass

    def _on_message_received_engine(self, origen: str, tipo: str, datos: dict):
        if tipo == "TEST_PING":
            try:
                from src.ui_components.toast import Toast
                Toast.show_success(self, f"🔔 ¡PING recibido desde {origen}!")
            except:
                pass

    def _on_heartbeat_engine(self, origen: str):
        """Llega un heartbeat de cualquier origen. Si es del cajero → punto verde."""
        # El terminal envía con rol tipo 'cajero-HOSTNAME' o 'admin-HOSTNAME'
        origen_lower = origen.lower()
        if any(k in origen_lower for k in ('cajero', 'admin', 'terminal')):
            self.info_negocio.on_heartbeat_terminal(origen)

    def _on_connection_lost_engine(self, origen: str):
        """Se perdió conexión con un nodo del terminal."""
        origen_lower = origen.lower()
        if any(k in origen_lower for k in ('cajero', 'admin', 'terminal')):
            self.info_negocio.set_estado_red('lost', 'Terminal desconectado')

    def _emitir_heartbeat(self):
        """
        Emite 'carteleria|HEARTBEAT|{}' por dos canales en paralelo:
          1. UDP raw a 127.0.0.1:38000  → NetworkReceiverThread (mismo o distinto proceso)
          2. Emit directo en el engine  → inmediato, mismo proceso, thread-safe via singleShot(0)
        """
        # --- Canal 1: UDP raw ---
        try:
            import socket as _s
            msg = b"carteleria|HEARTBEAT|{}"
            sock = _s.socket(_s.AF_INET, _s.SOCK_DGRAM)
            sock.setsockopt(_s.SOL_SOCKET, _s.SO_REUSEADDR, 1)
            sock.setsockopt(_s.SOL_SOCKET, _s.SO_BROADCAST, 1)
            sock.sendto(msg, ('127.0.0.1', 38000))
            sock.sendto(msg, ('255.255.255.255', 38000))
            sock.close()
        except Exception:
            pass

        # --- Canal 2: emit directo (mismo proceso, garantizado en main thread) ---
        try:
            from src.network.network_engine import get_network_engine
            engine = get_network_engine()
            if engine:
                # singleShot(0) ejecuta en el event loop del hilo principal → thread-safe
                from PyQt6.QtCore import QTimer as _QT
                _QT.singleShot(0, lambda: engine.heartbeat_received.emit("carteleria"))
        except Exception:
            pass

    def _f11_pressed(self):
        try:
            self.request_screen.emit(0) # Retornar al Dashboard Admin
        except Exception: pass
        
        if self.isWindow():
            if self.isFullScreen():
                self.showNormal()
            else:
                self.close()

