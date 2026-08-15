"""Lanzador directo de cartelería TV sin consola Qt intermedia."""

import os
import sys
import subprocess
import tempfile
import platform
import logging
import threading
import http.server
import socketserver
import json
import time

from src.utils.paths import get_resource_path
from src.carteleria.motor_carteleria.db_sync_worker import DbSyncWorker
from src.carteleria.motor_carteleria.clima_worker import ClimaWorker
from src.carteleria.motor_carteleria.estado_tv import armar_paneles

logger = logging.getLogger("LanzadorDirectoTV")


class GlobalHotkeyListener(threading.Thread):
    """Hilo para escuchar teclas globales F10/F11/ESC (Windows)."""
    
    def __init__(self, callback_f10, callback_f11, callback_esc):
        super().__init__(daemon=True)
        self.callback_f10 = callback_f10
        self.callback_f11 = callback_f11
        self.callback_esc = callback_esc
        self.running = False
        
    def run(self):
        """Escucha teclas globales usando pynput si está disponible."""
        self.running = True
        try:
            from pynput import keyboard
            logger.info("HotkeyListener iniciado con pynput (F10: monitor, F11/ESC: salir)")
            
            def on_press(key):
                try:
                    if key == keyboard.Key.f10:
                        self.callback_f10()
                    elif key == keyboard.Key.f11:
                        self.callback_f11()
                    elif key == keyboard.Key.esc:
                        self.callback_esc()
                except Exception:
                    pass
            
            listener = keyboard.Listener(on_press=on_press)
            listener.start()
            
            while self.running:
                time.sleep(0.1)
                
            listener.stop()
            
        except ImportError:
            logger.warning("pynput no disponible, hotkeys globales desactivados (usa teclas en navegador)")
        except Exception as e:
            logger.warning(f"Error en HotkeyListener: {e}")


class LanzadorDirectoTV:
    """Lanzador directo de cartelería TV: servidor HTTP + chromium kiosk sin consola Qt."""
    
    def __init__(self):
        self.httpd = None
        self.thread = None
        self.browser_process = None
        self.screen_index = None
        self.web_root = get_resource_path(
            os.path.join("src", "carteleria", "lanzador_tv", "la_cara_web")
        )
        self._kiosk_profile = os.path.join(tempfile.gettempdir(), "tpv-carteleria-kiosk")
        self._sync_worker = None
        self._clima_worker = None
        self._clima_icon = "sol"
        self._clima = ""
        self.rows_precios = []
        self._paneles = {}
        self._hotkey_listener = None
        
    def lanzar(self, screen_index=None):
        """Lanza directamente el servidor HTTP y chromium kiosk."""
        try:
            self.screen_index = screen_index
            
            # Cargar datos iniciales antes de iniciar servidor
            self._cargar_datos_iniciales()
            
            # Iniciar servidor HTTP
            if not self._iniciar_servidor():
                return False
            
            # Iniciar motores de datos
            self._iniciar_motores()
            
            # Lanzar navegador kiosk
            self._lanzar_navegador()
            
            # Iniciar hotkeys globales
            self._iniciar_hotkeys()
            
            logger.info(f"Cartelería TV lanzada directamente en http://127.0.0.1:{self.httpd.server_address[1]}/")
            logger.info("Controles: F10 = cambiar monitor | F11/ESC = detener cartelería")
            return True
            
        except Exception as e:
            logger.error(f"Error lanzando cartelería directa: {e}")
            return False
    
    def _cargar_datos_iniciales(self):
        """Carga datos iniciales desde la base de datos."""
        try:
            from src.base_de_datos.database import db_manager
            import json
            import os
            from src.utils.paths import get_base_path
            
            # Primero intentar desde caché local
            cache_path = os.path.join(get_base_path(), "carteleria_cache.json")
            if os.path.exists(cache_path):
                try:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        productos = data.get("precios", [])
                        if productos:
                            self.rows_precios = self._marcar_publicidad(self._normalizar_productos(productos))
                            self._paneles = armar_paneles(self.rows_precios, self._clima_icon, self._clima)
                            logger.info(f"Cargados {len(self.rows_precios)} productos desde caché")
                            return
                except Exception as e:
                    logger.warning(f"Error leyendo caché: {e}")
            
            # Si no hay caché, cargar directamente desde DB
            q = """
                SELECT 
                    id, 
                    nombre, 
                    precio, 
                    precio_oferta, 
                    cant_oferta, 
                    tipo_unidad_oferta,
                    departamento,
                    categoria,
                    stock,
                    unidad,
                    es_pesable
                FROM productos 
                WHERE COALESCE(stock, 0) > 0
                ORDER BY nombre
                LIMIT 50
            """
            filas = db_manager.execute_query(q)
            productos = []
            if filas:
                for r in filas:
                    if isinstance(r, dict):
                        productos.append({
                            'id': r.get('id'),
                            'nombre': r.get('nombre'),
                            'precio': r.get('precio') or 0,
                            'precio_oferta': r.get('precio_oferta') or 0,
                            'cant_oferta': r.get('cant_oferta') or 0,
                            'tipo_unidad_oferta': r.get('tipo_unidad_oferta') or '',
                            'departamento': r.get('departamento') or '',
                            'categoria': r.get('categoria') or '',
                            'stock': r.get('stock') or 0,
                            'unidad': r.get('unidad') or '',
                            'es_pesable': r.get('es_pesable') or 0,
                        })
            
            if productos:
                self.rows_precios = self._marcar_publicidad(self._normalizar_productos(productos))
                self._paneles = armar_paneles(self.rows_precios, self._clima_icon, self._clima)
                logger.info(f"Cargados {len(self.rows_precios)} productos desde DB")
            else:
                logger.warning("No se encontraron productos en la base de datos")
                
        except Exception as e:
            logger.error(f"Error cargando datos iniciales: {e}")
    
    def detener(self):
        """Detiene servidor HTTP, navegador y motores."""
        try:
            # Detener hotkeys
            if self._hotkey_listener:
                self._hotkey_listener.running = False
                self._hotkey_listener = None
            
            self._cerrar_navegador()
            
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()
                self.httpd = None
                
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1)
            self.thread = None
            
            if self._sync_worker and self._sync_worker.isRunning():
                self._sync_worker.requestInterruption()
                self._sync_worker.wait(1000)
                
            if self._clima_worker and self._clima_worker.isRunning():
                self._clima_worker.wait(1000)
                
            logger.info("Cartelería TV directa detenida")
            
        except Exception as e:
            logger.error(f"Error deteniendo cartelería: {e}")
    
    def _iniciar_servidor(self):
        """Inicia servidor HTTP estático."""
        try:
            from src.carteleria.lanzador_tv.cerebro_lanzador_tv import CarteleriaWebHandler, ThreadedHTTPServer
            
            handler = lambda *args, **kwargs: CarteleriaWebHandler(
                *args,
                web_root=self.web_root,
                main_window=self,
                **kwargs
            )
            self.httpd = ThreadedHTTPServer(("127.0.0.1", 0), handler)
            self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
            self.thread.start()
            logger.info(f"Servidor HTTP iniciado en puerto {self.httpd.server_address[1]}")
            return True
            
        except Exception as e:
            logger.error(f"Error iniciando servidor HTTP: {e}")
            return False
    
    def _iniciar_motores(self):
        """Inicia workers de sincronización y clima."""
        try:
            self._sync_worker = DbSyncWorker(self)
            self._sync_worker.sync_finished.connect(self._on_sync_finished)
            self._sync_worker.start()
            
            self._clima_worker = ClimaWorker(self)
            self._clima_worker.clima_actualizado.connect(self._on_clima_actualizado)
            self._clima_worker.start()
            
        except Exception as e:
            logger.warning(f"Error iniciando motores: {e}")
    
    def _iniciar_hotkeys(self):
        """Inicia hotkeys globales F10/F11/ESC."""
        try:
            self._hotkey_listener = GlobalHotkeyListener(
                callback_f10=self._handle_f10,
                callback_f11=self._handle_f11,
                callback_esc=self._handle_esc
            )
            self._hotkey_listener.start()
        except Exception as e:
            logger.warning(f"Error iniciando hotkeys: {e}")
    
    def _handle_f10(self):
        """Maneja F10: cambiar monitor."""
        logger.info("F10 presionado - cambiando monitor")
        self.screen_index = (self.screen_index or 0) + 1
        self._lanzar_navegador()
    
    def _handle_f11(self):
        """Maneja F11: detener cartelería."""
        logger.info("F11 presionado - deteniendo cartelería")
        self.detener()
    
    def _handle_esc(self):
        """Maneja ESC: detener cartelería (alternativa a F11)."""
        logger.info("ESC presionado - deteniendo cartelería")
        self.detener()
    
    def _on_sync_finished(self, data, status):
        """Procesa datos sincronizados."""
        try:
            if status == "online":
                productos = data.get("precios", [])
                self.rows_precios = self._marcar_publicidad(self._normalizar_productos(productos))
                self._paneles = armar_paneles(self.rows_precios, self._clima_icon, self._clima)
                logger.info(f"Sincronizados {len(self.rows_precios)} productos")
                logger.info(f"Paneles generados: rotacion={len(self._paneles.get('rotacion', []))}, combos={len(self._paneles.get('combos', []))}, ia={len(self._paneles.get('ia', []))}")
        except Exception as e:
            logger.warning(f"Error procesando sync: {e}")
            # Fallback: generar paneles vacíos pero válidos
            self._paneles = {
                "hero": None,
                "destacados": [],
                "rotacion": [],
                "combos": [],
                "columna3": [],
                "ia": []
            }
    
    def _on_clima_actualizado(self, icon_name, text):
        self._clima_icon = icon_name or "sol"
        self._clima = text
        if self.rows_precios:
            self._paneles = armar_paneles(self.rows_precios, self._clima_icon, self._clima)
    
    def _normalizar_productos(self, productos):
        """Normaliza productos al formato estándar."""
        result = []
        for item in productos:
            if isinstance(item, dict):
                result.append({
                    'id': item.get('id'),
                    'nombre': item.get('nombre', ''),
                    'precio': float(item.get('precio') or 0),
                    'precio_oferta': float(item.get('precio_oferta') or 0),
                    'precio_oferta_relampago': float(item.get('precio_oferta_relampago') or 0),
                    'cant_oferta': float(item.get('cant_oferta') or 0),
                    'tipo_unidad_oferta': item.get('tipo_unidad_oferta', ''),
                    'unidad': item.get('unidad', ''),
                    'es_pesable': item.get('es_pesable') or 0,
                    'departamento': item.get('departamento') or item.get('categoria', ''),
                    'categoria': item.get('categoria', ''),
                    'stock': float(item.get('stock') or 0),
                    'es_publicidad': False
                })
        return result

    def _marcar_publicidad(self, productos):
        try:
            from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad
            motor_publicidad.cargar_configuracion()
            for item in productos:
                item["es_publicidad"] = motor_publicidad.is_promocionado(item.get("nombre"))
        except Exception:
            pass
        return productos
    
    def get_web_state(self):
        """Estado para la API web conectado con motores globales."""
        try:
            from src.config import config
            
            # Si no hay paneles generados, generarlos desde productos
            if not self._paneles or not self._paneles.get("rotacion"):
                self._paneles = armar_paneles(self.rows_precios, self._clima_icon, self._clima)
            
            # Generar datos del clima para la columna 4
            clima_data = self._generar_datos_clima()
            
            # Generar mensaje dinámico para el banderín basado en clima y ofertas
            business_name = config.get("business_name", "Cartelería")
            mensaje_personalizado = self._generar_mensaje_banderin(business_name)
            
            return {
                "config": {
                    "business_name": business_name,
                    "phone": config.get("phone", ""),
                    "carteleria_theme": config.get("carteleria_theme", "temu"),
                    "mensaje_zocalo": mensaje_personalizado,
                    "data_status": "online"
                },
                "precios": self.rows_precios,
                "hero": self._paneles.get("hero"),
                "destacados": self._paneles.get("destacados", []),
                "rotacion": self._paneles.get("rotacion", []),
                "combos": self._paneles.get("combos", []),
                "columna3": self._paneles.get("columna3", []),
                "ia": self._paneles.get("ia", []),
                "climaData": clima_data
            }
        except Exception as e:
            logger.warning(f"Error generando web state: {e}")
            return {"config": {}, "precios": []}
    
    def _generar_datos_clima(self):
        """Genera datos del clima para la columna 4 con PNG y mensaje."""
        try:
            # Determinar icono y mensaje según el clima
            icono = self._clima_icon or "sol"
            temperatura = self._clima or "22°C"
            
            # Mensaje según el clima y hora (noche/día)
            import datetime
            hora_actual = datetime.datetime.now().hour
            
            if 18 <= hora_actual or hora_actual < 6:
                # Es noche
                if "nublado" in self._clima.lower():
                    mensaje = "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR"
                    producto_recomendado = "POLLO ENTERO"
                elif "lluvia" in self._clima.lower():
                    mensaje = "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR"
                    producto_recomendado = "BOLSA DE MENUDENCIOS"
                else:
                    mensaje = "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR"
                    producto_recomendado = "POLLO ENTERO"
            else:
                # Es día
                if "nublado" in self._clima.lower():
                    mensaje = "Día nublado, ideal para compras en abrigo"
                    producto_recomendado = "POLLO ENTERO"
                elif "lluvia" in self._clima.lower():
                    mensaje = "Día de lluvia, perfecto para productos de olla"
                    producto_recomendado = "BOLSA DE MENUDENCIOS"
                else:
                    mensaje = "Día soleado, perfecto para la parrilla"
                    producto_recomendado = "POLLO ENTERO"
            
            # Buscar precio del producto recomendado
            precio = 4900  # Precio default
            for prod in self.rows_precios:
                if producto_recomendado.lower() in prod.get('nombre', '').lower():
                    precio = prod.get('precio', 4900)
                    break
            
            return {
                "icono": icono,
                "temperatura": temperatura,
                "mensaje": mensaje,
                "producto_recomendado": producto_recomendado,
                "precio": precio
            }
        except Exception as e:
            logger.warning(f"Error generando datos clima: {e}")
            # Fallback a datos por defecto
            return {
                "icono": "sol",
                "temperatura": "22°C",
                "mensaje": "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR",
                "producto_recomendado": "POLLO ENTERO",
                "precio": 4900
            }
    
    def _generar_mensaje_banderin(self, business_name):
        """Genera mensaje dinámico para el banderín según clima y ofertas."""
        mensajes_base = [
            f"Bienvenido a {business_name} • Los mejores precios • Calidad garantizada",
            f"Calidad garantizada en {business_name} • Precios competitivos • Atención personalizada",
            f"{business_name} • Frescura garantizada • Productos de primera calidad"
        ]
        
        # Agregar mensaje basado en clima
        if self._clima and "nublado" in self._clima.lower():
            mensajes_base.append("Día ideal para compras en abrigo • Calidez en cada producto")
        elif self._clima and "sol" in self._clima.lower():
            mensajes_base.append("Día perfecto para la parrilla • Disfruta el buen clima")
        
        # Agregar mensaje basado en ofertas activas
        ofertas_activas = [p for p in self.rows_precios if p.get('precio_oferta', 0) > 0 and p.get('precio_oferta', 0) < p.get('precio', 0)]
        if ofertas_activas:
            mensajes_base.append(f"• {len(ofertas_activas)} ofertas activas hoy • Aprovechá las promociones")
        
        return " • ".join(mensajes_base)
    
    def _lanzar_navegador(self):
        """Lanza chromium en modo kiosk."""
        try:
            self._cerrar_navegador()
            url = f"http://127.0.0.1:{self.httpd.server_address[1]}/"
            sistema = platform.system()
            
            x, y, w, h = self._geometria_tv()
            flags = [
                f"--user-data-dir={self._kiosk_profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-features=Translate,InfiniteSessionRestore",
                "--disable-session-crashed-bubble",
                "--disable-infobars",
                "--disable-restore-session-state",
                "--noerrdialogs",
                "--kiosk",
                "--start-fullscreen",
                f"--window-position={x},{y}",
                f"--window-size={w},{h}",
                url,
            ]
            
            if sistema == "Windows":
                navegador = self._buscar_chrome_windows()
                if navegador:
                    self.browser_process = subprocess.Popen([navegador] + flags)
                else:
                    os.startfile(url)
            elif sistema == "Darwin":
                self.browser_process = subprocess.Popen(
                    ["open", "-a", "Google Chrome", "--args"] + flags
                )
            else:
                for binario in ("google-chrome", "chromium-browser", "chromium", "microsoft-edge"):
                    try:
                        self.browser_process = subprocess.Popen([binario] + flags)
                        break
                    except FileNotFoundError:
                        continue
                if self.browser_process is None:
                    subprocess.Popen(["xdg-open", url])
            
            logger.info(f"Navegador kiosk lanzado en {url}")
            
        except Exception as e:
            logger.error(f"Error lanzando navegador: {e}")
    
    def _cerrar_navegador(self):
        """Cierra el navegador kiosk."""
        if not self.browser_process:
            return
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.browser_process.pid)],
                    capture_output=True,
                    check=False,
                )
            else:
                self.browser_process.terminate()
                try:
                    self.browser_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.browser_process.kill()
        except Exception as e:
            logger.warning(f"Error cerrando navegador: {e}")
        self.browser_process = None
    
    def _geometria_tv(self):
        """Obtiene geometría del monitor TV."""
        try:
            from PyQt6.QtWidgets import QApplication
            from src.utils.qt_dpi import secondary_screen
            
            app = QApplication.instance()
            if not app:
                return 0, 0, 1920, 1080
            screens = app.screens()
            if not screens:
                return 0, 0, 1920, 1080
            if self.screen_index is not None and 0 <= self.screen_index < len(screens):
                screen = screens[self.screen_index]
            else:
                screen = secondary_screen(app) or (screens[-1] if len(screens) > 1 else screens[0])
            geo = screen.geometry()
            return geo.x(), geo.y(), geo.width(), geo.height()
        except Exception:
            return 0, 0, 1920, 1080
    
    def _buscar_chrome_windows(self):
        """Busca Chrome/Edge en Windows."""
        candidatos = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
            os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        ]
        for path in candidatos:
            if path and os.path.exists(path):
                return path
        return None


# Instancia global singleton
_lanzador_directo = None

def get_lanzador_directo():
    """Obtiene instancia singleton del lanzador directo."""
    global _lanzador_directo
    if _lanzador_directo is None:
        _lanzador_directo = LanzadorDirectoTV()
    return _lanzador_directo