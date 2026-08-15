import os
import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap

from src.carteleria.theme import C_THEME, set_theme, get_active_theme_name
from src.carteleria.configuraciones.info_negocio import InfoNegocio
from src.carteleria.motor_carteleria.web_server import CarteleriaWebServer

logger = logging.getLogger("Carteleria_Autonoma")


class CarteleriaMain(QWidget):
    """Cartelería Main - Solo interfaz web, sin componentes Qt"""
    request_screen = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setObjectName("CarteleriaMain")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        
        # Cargar tema
        from src.config import config
        theme_name = config.get("carteleria_theme", "temu")
        set_theme(theme_name)
        print(f"[Carteleria] Tema activado: {theme_name}")

        # Datos para API web
        self.rows_precios = []
        self.sos_data = []
        self.top10_data = {}
        self.web_server = None
        self.web_view = None
        
        # Componentes básicos
        self.info_negocio = InfoNegocio()
        self.info_negocio.config_requested.connect(self._abrir_configuracion)
        
        # Cargar productos iniciales desde inventario
        self._cargar_productos_inventario()
        
        # Variables de estado
        self.rotacion_ms = 16000
        self.tiempo_sos_ms = 10000
        self.frec_sos = 3
        
        # Fondo según tema
        self._setup_background()
        
        # Construir UI web-only
        self._build_ui_web_only()
        
        # Iniciar workers de datos
        self._start_data_workers()
        
    def _setup_background(self):
        """Configurar fondo según tema"""
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(False)
        self._bg_image_path = None
        from src.utils.paths import get_resource_path
        
        tema_actual = get_active_theme_name()
        if tema_actual == "temu":
            self.bg_label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.bg_label.setAutoFillBackground(True)
            self.bg_label.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FFFF00, stop:0.5 #FFCC00, stop:1 #FF6600);
            """)
        elif tema_actual == "blackfriday":
            self.bg_label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.bg_label.setAutoFillBackground(True)
            self.bg_label.setStyleSheet("background: #050507;")
        else:
            img_path = get_resource_path(os.path.join("src", "carteleria", "assets", "macos_bg.png"))
            if os.path.exists(img_path):
                self._bg_image_path = img_path
                self._refresh_background_pixmap()
            else:
                self.bg_label.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
                self.bg_label.setAutoFillBackground(True)
                self.bg_label.setStyleSheet(f"background-color: {C_THEME['bg']};")
    
    def _refresh_background_pixmap(self):
        """Refrescar pixmap de fondo"""
        path = getattr(self, "_bg_image_path", None)
        if not path or not hasattr(self, "bg_label"):
            return
        try:
            from src.carteleria.escala_tv import load_pixmap_for_size
            sz = self.size()
            if sz.width() < 2 or sz.height() < 2:
                return
            self.bg_label.setPixmap(load_pixmap_for_size(path, sz, widget=self))
        except Exception:
            try:
                self.bg_label.setPixmap(QPixmap(path))
            except Exception:
                pass

    def _build_ui_web_only(self):
        """Construir interfaz solo con web view"""
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        
        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
            from PyQt6.QtCore import QUrl

            self.web_view = QWebEngineView(self)
            self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
            self.web_view.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            self.web_view.page().setBackgroundColor(Qt.GlobalColor.black)

            self.web_server = CarteleriaWebServer(self)
            self.web_server.start()
            if self.web_server.port:
                self.web_view.setUrl(QUrl(f"http://127.0.0.1:{self.web_server.port}/"))
            root.addWidget(self.web_view)
        except Exception as e:
            print(f"[CarteleriaWeb] No se pudo iniciar UI web: {e}")
            error_label = QLabel("Error: Interfaz web no disponible")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            error_label.setStyleSheet("font-size: 24px; color: red;")
            root.addWidget(error_label)
    
    def _start_data_workers(self):
        """Iniciar workers de datos para la API"""
        from src.carteleria.motor_carteleria.db_sync_worker import DbSyncWorker
        from src.carteleria.motor_carteleria.clima_worker import ClimaWorker

        self.db_worker = DbSyncWorker(self)
        self.db_worker.sync_finished.connect(self._on_db_sync_finished)
        self.db_worker.start()

        self.clima_pilar = ("sol", "22°C Pilar")
        self.clima_worker = ClimaWorker(self)
        self.clima_worker.clima_actualizado.connect(self._on_clima_actualizado)
        
        # Iniciar clima solo si es maestra
        from src.config import config
        from src.base_de_datos.database import db_manager
        _host = str(config.get("db_host", "") or "").strip().lower()
        is_slave = (
            config.get("carteleria_is_slave", False)
            or (not getattr(db_manager, "is_master", True))
            or (_host and _host not in ("localhost", "127.0.0.1", ""))
        )
        
        if not is_slave:
            self.clima_worker.start()
        
        # Timer para refrescar datos
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.db_worker.start)
        self.refresh_timer.start(15000)  # Reducido de 30s a 15s
    
    def _cargar_productos_inventario(self):
        """Cargar productos iniciales desde inventario"""
        try:
            from src.base_de_datos.database import db_manager
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
                LIMIT 20
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
                    else:
                        # Fallback para tuple
                        productos.append({
                            'id': r[0] if len(r) > 0 else 0,
                            'nombre': r[1] if len(r) > 1 else '',
                            'precio': r[2] if len(r) > 2 else 0,
                            'precio_oferta': r[3] if len(r) > 3 else 0,
                            'cant_oferta': r[4] if len(r) > 4 else 0,
                            'tipo_unidad_oferta': r[5] if len(r) > 5 else '',
                            'departamento': r[6] if len(r) > 6 else '',
                            'categoria': r[7] if len(r) > 7 else '',
                            'stock': r[8] if len(r) > 8 else 0
                        })
            self.rows_precios = productos
            logger.info(f"[Carteleria] Cargados {len(productos)} productos iniciales del inventario")
            if productos:
                logger.info(f"[Carteleria] Primer producto: {productos[0].get('nombre')} - ${productos[0].get('precio')}")
        except Exception as e:
            logger.warning(f"Error cargando inventario inicial: {e}")
            self.rows_precios = []
    
    def _on_clima_actualizado(self, icon_name, text):
        self.clima_pilar = (icon_name, text)
    
    def _on_db_sync_finished(self, data, status):
        """Procesar datos sincronizados desde inventario real"""
        try:
            if status == "online":
                self.info_negocio.set_estado_red("online")
            elif status == "offline":
                self.info_negocio.set_estado_red("offline", "Modo Offline (Caché)")
            else:
                return
            
            if not data: return
            
            # Configuración
            cfg_data = data.get("config", {})
            nombre_negocio = cfg_data.get("business_name", "Carnicería")
            self.info_negocio.actualizar_nombre(nombre_negocio)
            
            # Cargar productos desde inventario real (tabla productos)
            from src.base_de_datos.database import db_manager
            try:
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
                self.rows_precios = productos
                logger.info(f"[Carteleria] Cargados {len(productos)} productos del inventario")
            except Exception as e:
                logger.warning(f"Error cargando inventario: {e}")
                self.rows_precios = []
            
            # Datos para API web
            self.sos_data = []
            self.top10_data = {}
            
            # Actualizar tiempos
            nueva_rotacion = cfg_data.get("carteleria_rotacion", 15) * 1000
            if hasattr(self, 'rotacion_ms') and nueva_rotacion != self.rotacion_ms:
                self.rotacion_ms = nueva_rotacion
                    
            self.tiempo_sos_ms = cfg_data.get("carteleria_tiempo_sos", 10) * 1000
            self.frec_sos = max(3, cfg_data.get("carteleria_frec_sos", 3))
            
        except Exception as e:
            logger.warning(f"Error procesando datos: {e}")
    
    def _abrir_configuracion(self):
        """Abrir diálogo de configuración"""
        from PyQt6.QtWidgets import QInputDialog, QMessageBox
        from src.config import config
        
        current_ip = config.get("carteleria_master_ip", "") or config.get("db_host", "")
        ip, ok = QInputDialog.getText(
            self,
            "Configuración de Cartelería",
            "IP del Servidor de Tienda (PC Maestra):\n"
            "(Vacío = esta PC es maestra. No hace falta abrir el cajero.)",
            text=current_ip if current_ip not in ("localhost", "127.0.0.1") else "",
        )
        if ok:
            ip = ip.strip()
            config.set("carteleria_master_ip", ip)
            config.set("carteleria_is_slave", bool(ip))
            config.save()
            QMessageBox.information(
                self,
                "Configuración",
                "Guardado.\nEn la otra PC debe estar el Servidor de Tienda (sin cajero).",
            )
    
    def get_web_state(self):
        """Obtener estado para la interfaz web"""
        return {
            "config": {
                "business_name": getattr(self.info_negocio, 'nombre', 'Cartelería'),
                "phone": getattr(self.info_negocio, 'telefono', 'No disponible'),
                "carteleria_rotacion": self.rotacion_ms // 1000,
                "carteleria_tiempo_sos": self.tiempo_sos_ms // 1000,
                "carteleria_frec_sos": self.frec_sos,
                "mensaje_zocalo": "",
                "carteleria_theme": self._get_current_theme()
            },
            "layout_mode": 4,
            "view_state": "normal",
            "sos": {
                "active": False,
                "index": 0,
                "items": self.sos_data or []
            },
            "precios": self.rows_precios or [],
            "top10": self.top10_data or {},
        }
    
    def _get_current_theme(self):
        """Obtener el tema actual"""
        try:
            from src.config import config
            return config.get("carteleria_theme", "temu")
        except Exception:
            return "temu"
    
    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        self._refresh_background_pixmap()
        super().resizeEvent(event)
