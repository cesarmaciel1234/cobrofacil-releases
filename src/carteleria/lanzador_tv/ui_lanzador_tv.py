"""Consola de lanzamiento para la cartelería pública en TV."""

from datetime import datetime
import json
import os

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtGui import QKeyEvent


class CarteleriaMainTV(QWidget):
    """Lanzador autónomo: sincroniza datos y abre la TV en modo kiosk."""

    request_screen = pyqtSignal(int)
    request_back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CarteleriaMainTV")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._cerebro = None
        self._iniciado = False
        self.rows_precios, self.sos_data, self.top10_data = [], [], {}
        self._paneles = {"hero": None, "destacados": [], "rotacion": [], "combos": [], "columna3": [], "ia": []}
        self._sync_status, self._ultima_sincro, self._clima = "Preparando datos", None, "Información local"
        self._clima_icon = "sol"
        self._apply_theme()
        self._build_ui()
        self._cargar_cache_inicial()
        self._setup_motores()
        self._sincronizar()

    def _apply_theme(self):
        """Aplicar tema autónomo del sistema de cartelería (temu/apple/blackfriday)"""
        try:
            from src.config import config
            from src.carteleria.theme import set_theme, C_THEME
            self._theme_name = config.get("carteleria_theme", "temu")
            set_theme(self._theme_name)
            
            # Aplicar estilos según el tema de cartelería
            if self._theme_name == "temu":
                # Tema vibrante Temu
                self.setStyleSheet("""
                    #CarteleriaMainTV { background: linear-gradient(135deg, #FFE500 0%, #FFCC00 50%, #FF6600 100%); }
                    QLabel { color: #111111; background: transparent; }
                    QFrame#hero, QFrame#metric { background: rgba(255, 255, 255, 0.95); border: 2px solid #111111; border-radius: 18px; }
                    QLabel#eyebrow { color: #DC2626; font-size: 12px; font-weight: 800; letter-spacing: 1.2px; }
                    QLabel#title { color: #111111; font-size: 30px; font-weight: 900; }
                    QLabel#muted { color: #DC2626; font-size: 13px; }
                    QLabel#metricValue { color: #111111; font-size: 22px; font-weight: 800; }
                    QLabel#status { color: #10B981; font-size: 13px; font-weight: 700; }
                    QPushButton { border: 2px solid #111111; border-radius: 10px; padding: 12px 18px; font-size: 14px; font-weight: 800; }
                    QPushButton#start { background: #DC2626; color: white; border-color: #DC2626; }
                    QPushButton#start:hover { background: #FF3B00; border-color: #FF3B00; }
                    QPushButton#stop { background: #111111; color: white; }
                    QPushButton#stop:hover { background: #333333; }
                    QPushButton#secondary { background: rgba(255, 255, 255, 0.9); color: #111111; border: 2px solid #111111; }
                    QPushButton#secondary:hover { background: #FFCC00; }
                """)
            elif self._theme_name == "blackfriday":
                # Tema Black Friday
                self.setStyleSheet("""
                    #CarteleriaMainTV { background: #050507; }
                    QLabel { color: #FFFFFF; background: transparent; }
                    QFrame#hero, QFrame#metric { background: #1A1A1A; border: 1px solid #FF0000; border-radius: 18px; }
                    QLabel#eyebrow { color: #FF0000; font-size: 12px; font-weight: 800; letter-spacing: 1.2px; }
                    QLabel#title { color: #FFFFFF; font-size: 30px; font-weight: 900; }
                    QLabel#muted { color: #888888; font-size: 13px; }
                    QLabel#metricValue { color: #FFFFFF; font-size: 22px; font-weight: 800; }
                    QLabel#status { color: #00FF00; font-size: 13px; font-weight: 700; }
                    QPushButton { border: 1px solid #FF0000; border-radius: 10px; padding: 12px 18px; font-size: 14px; font-weight: 800; }
                    QPushButton#start { background: #FF0000; color: white; }
                    QPushButton#start:hover { background: #CC0000; }
                    QPushButton#stop { background: #333333; color: white; border-color: #666666; }
                    QPushButton#stop:hover { background: #555555; }
                    QPushButton#secondary { background: #1A1A1A; color: #FFFFFF; border: 1px solid #FF0000; }
                    QPushButton#secondary:hover { background: #330000; }
                """)
            else:
                # Tema Apple (default)
                self.setStyleSheet("""
                    #CarteleriaMainTV { background: #F8F9FA; }
                    QLabel { color: #1A1A1A; background: transparent; }
                    QFrame#hero, QFrame#metric { background: rgba(255, 255, 255, 0.95); border: 1px solid rgba(0, 0, 0, 0.08); border-radius: 18px; }
                    QLabel#eyebrow { color: #007AFF; font-size: 12px; font-weight: 800; letter-spacing: 1.2px; }
                    QLabel#title { color: #1A1A1A; font-size: 30px; font-weight: 900; }
                    QLabel#muted { color: #6B7280; font-size: 13px; }
                    QLabel#metricValue { color: #1A1A1A; font-size: 22px; font-weight: 800; }
                    QLabel#status { color: #34C759; font-size: 13px; font-weight: 700; }
                    QPushButton { border: none; border-radius: 10px; padding: 12px 18px; font-size: 14px; font-weight: 800; }
                    QPushButton#start { background: #007AFF; color: white; }
                    QPushButton#start:hover { background: #0056CC; }
                    QPushButton#stop { background: #FF3B30; color: white; }
                    QPushButton#stop:hover { background: #CC2E25; }
                    QPushButton#secondary { background: rgba(255, 255, 255, 0.9); color: #007AFF; border: 1px solid rgba(0, 122, 255, 0.2); }
                    QPushButton#secondary:hover { background: rgba(0, 122, 255, 0.1); }
                """)
        except Exception as e:
            print(f"Error aplicando tema de cartelería: {e}")
            # Fallback a estilos básicos
            self.setStyleSheet("""
                #CarteleriaMainTV { background: #08111F; }
                QLabel { color: #E5EDF8; background: transparent; }
                QFrame#hero, QFrame#metric { background: #101D30; border: 1px solid #243654; border-radius: 18px; }
                QPushButton { border: 0; border-radius: 10px; padding: 12px 18px; font-size: 14px; font-weight: 800; }
                QPushButton#start { background: #2563EB; color: white; }
                QPushButton#stop { background: #DC2626; color: white; }
            """)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(46, 38, 46, 38)
        root.setSpacing(18)
        hero = QFrame(objectName="hero")
        hero_lay = QVBoxLayout(hero)
        hero_lay.setContentsMargins(28, 24, 28, 24)
        hero_lay.addWidget(QLabel("TV CONTROL CENTER", objectName="eyebrow"))
        hero_lay.addWidget(QLabel("Cartelería viva, lista para vender", objectName="title"))
        self.lbl_subtitulo = QLabel("Sincronizando inventario, promociones y configuración…", objectName="muted")
        hero_lay.addWidget(self.lbl_subtitulo)
        root.addWidget(hero)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.lbl_productos = self._metric(metrics, "PRODUCTOS DISPONIBLES", "—")
        self.lbl_ofertas = self._metric(metrics, "OFERTAS ACTIVAS", "—")
        self.lbl_estado = self._metric(metrics, "ESTADO DE DATOS", "INICIANDO")
        root.addLayout(metrics)
        self.lbl_status = QLabel("● Preparando la TV", objectName="status")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self.lbl_status)
        root.addStretch(1)

        actions = QHBoxLayout()
        self.btn_control = QPushButton("INICIAR EN PANTALLA TV", objectName="start")
        self.btn_control.setMinimumHeight(56)
        self.btn_control.clicked.connect(self._on_control_clicked)
        actions.addWidget(self.btn_control, 2)
        self.btn_pantalla = QPushButton("MONITOR TV · F10", objectName="secondary")
        self.btn_pantalla.setMinimumHeight(56)
        self.btn_pantalla.clicked.connect(self._toggle_fullscreen)
        actions.addWidget(self.btn_pantalla, 1)
        self.btn_emergency = QPushButton("🚨 EMERGENCIA F11", objectName="stop")
        self.btn_emergency.setMinimumHeight(40)
        self.btn_emergency.clicked.connect(self._emergency_stop)
        actions.addWidget(self.btn_emergency, 1)
        root.addLayout(actions)
        footer = QLabel("F10 elige el monitor de la TV. F11 cierra el kiosk. Los precios salen del TPV.", objectName="muted")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

    @staticmethod
    def _metric(layout, title, value):
        card = QFrame(objectName="metric")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(18, 14, 18, 14)
        caption = QLabel(title, objectName="eyebrow")
        caption.setStyleSheet("font-size: 10px;")
        card_lay.addWidget(caption)
        label = QLabel(value, objectName="metricValue")
        card_lay.addWidget(label)
        layout.addWidget(card)
        return label

    def _setup_motores(self):
        """Conecta los motores existentes: sync, clima, publicidad y ventana."""
        from src.carteleria.motor_carteleria.db_sync_worker import DbSyncWorker
        from src.carteleria.motor_carteleria.clima_worker import ClimaWorker
        from src.carteleria.lanzador_tv.window_manager import WindowManager
        self._sync_worker = DbSyncWorker(self)
        self._sync_worker.sync_finished.connect(self._on_sync_finished)
        self._clima_worker = ClimaWorker(self)
        self._clima_worker.clima_actualizado.connect(self._on_clima_actualizado)
        self._window_manager = WindowManager(self)
        self._sync_timer = QTimer(self)
        self._sync_timer.timeout.connect(self._sincronizar)
        self._sync_timer.start(15000)
        self._clima_worker.start()

    def _cargar_cache_inicial(self):
        """Muestra datos útiles desde el primer fotograma, aun sin red."""
        try:
            from src.utils.paths import get_base_path
            cache_path = os.path.join(get_base_path(), "carteleria_cache.json")
            with open(cache_path, "r", encoding="utf-8") as cache_file:
                data = json.load(cache_file)
            if isinstance(data, dict) and data.get("precios"):
                self._on_sync_finished(data, "offline")
        except (OSError, ValueError, TypeError):
            # Sin caché es un arranque limpio; DbSyncWorker resolverá la carga.
            pass

    def _sincronizar(self):
        if not self._sync_worker.isRunning():
            self._sync_worker.start()

    @staticmethod
    def _normalizar_producto(row):
        from src.carteleria.motor_carteleria.estado_tv import num
        if isinstance(row, dict):
            return {
                "id": row.get("id"), "nombre": row.get("nombre", "") or "",
                "precio": num(row.get("precio")), "precio_oferta": num(row.get("precio_oferta")),
                "precio_oferta_relampago": num(row.get("precio_oferta_relampago")),
                "cant_oferta": num(row.get("cant_oferta")),
                "tipo_unidad_oferta": row.get("tipo_unidad_oferta", "") or "",
                "unidad": row.get("unidad", "") or "",
                "es_pesable": row.get("es_pesable") or 0,
                "departamento": row.get("departamento") or row.get("categoria", "") or "",
                "categoria": row.get("categoria", "") or "", "stock": num(row.get("stock")),
                "icono": row.get("icono") or "",
                "es_publicidad": False,
            }
        row = list(row) if isinstance(row, (list, tuple)) else []
        return {
            "id": None, "categoria": row[0] if len(row) > 0 else "", "departamento": row[0] if len(row) > 0 else "",
            "nombre": row[1] if len(row) > 1 else "", "precio": num(row[2] if len(row) > 2 else 0),
            "precio_oferta": num(row[3] if len(row) > 3 else 0),
            "precio_oferta_relampago": num(row[4] if len(row) > 4 else 0),
            "cant_oferta": num(row[6] if len(row) > 6 else 0),
            "tipo_unidad_oferta": row[7] if len(row) > 7 else "",
            "stock": num(row[8] if len(row) > 8 else 0),
            "unidad": row[9] if len(row) > 9 else "",
            "es_pesable": row[10] if len(row) > 10 else 0,
            "es_publicidad": False,
        }

    def _refrescar_paneles(self):
        try:
            from src.carteleria.motor_carteleria.estado_tv import armar_paneles
            self._paneles = armar_paneles(self.rows_precios, self._clima_icon, self._clima)
        except Exception:
            self._paneles = self._paneles or {"hero": None, "destacados": [], "rotacion": [], "combos": [], "columna3": [], "ia": []}

    def _on_sync_finished(self, data, status):
        data = data or {}
        productos = [self._normalizar_producto(row) for row in data.get("precios", [])]
        try:
            from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad
            motor_publicidad.cargar_configuracion()
            for item in productos:
                item["es_publicidad"] = motor_publicidad.is_promocionado(item["nombre"])
        except Exception:
            pass
        if productos:
            self.rows_precios = productos
        self.sos_data = data.get("sos", []) or []
        self.top10_data = data.get("top10", {}) or {}
        self._sync_status, self._ultima_sincro = status, datetime.now()
        self._refrescar_paneles()
        self._actualizar_resumen()

    def _on_clima_actualizado(self, icon_name, text):
        self._clima_icon = icon_name or "sol"
        self._clima = text
        if self.rows_precios:
            self._refrescar_paneles()

    def _actualizar_resumen(self):
        total = len(self.rows_precios)
        ofertas = sum(1 for item in self.rows_precios if float(item.get("precio_oferta") or 0) > 0 and float(item.get("precio_oferta") or 0) < float(item.get("precio") or 0))
        conectado = self._sync_status == "online"
        self.lbl_productos.setText(str(total))
        self.lbl_ofertas.setText(str(ofertas))
        self.lbl_estado.setText("EN LÍNEA" if conectado else "CACHÉ LOCAL")
        self.lbl_estado.setStyleSheet("color: #86EFAC;" if conectado else "color: #FCD34D;")
        origen = "Inventario sincronizado" if conectado else "Modo seguro: últimos datos disponibles"
        self.lbl_subtitulo.setText(f"{origen} · {self._clima}")
        hora = self._ultima_sincro.strftime("%H:%M:%S") if self._ultima_sincro else "—"
        self.lbl_status.setText(f"● {origen} · actualización {hora}")
        self.lbl_status.setStyleSheet("color: #86EFAC;" if conectado else "color: #FCD34D;")

    def get_web_state(self):
        """Contrato de datos para app.js; lo consulta el servidor del lanzador."""
        try:
            from src.config import config
            business_name, phone = config.get("business_name", "Cartelería"), config.get("phone", "")
            theme, mensaje = config.get("carteleria_theme", self._theme_name or "temu"), config.get("mensaje_zocalo", "")
        except Exception:
            business_name, phone, theme, mensaje = "Cartelería", "", self._theme_name, ""
        if not mensaje:
            mensaje = f"{business_name} • {self._clima} • Ofertas sujetas a stock •"
        try:
            from src.carteleria.motor_carteleria.iconos_tv import enriquecer_iconos
            enriquecer_iconos(self.rows_precios)
        except Exception:
            pass
        if not self._paneles or not self._paneles.get("rotacion"):
            self._refrescar_paneles()
        return {
            "config": {
                "business_name": business_name, "phone": phone,
                "carteleria_theme": theme, "mensaje_zocalo": mensaje,
                "data_status": self._sync_status,
            },
            "precios": self.rows_precios,
            "sos": self.sos_data,
            "top10": self.top10_data,
            "hero": self._paneles.get("hero"),
            "destacados": self._paneles.get("destacados") or [],
            "rotacion": self._paneles.get("rotacion") or [],
            "combos": self._paneles.get("combos") or [],
            "columna3": self._paneles.get("columna3") or [],
            "ia": self._paneles.get("ia") or [],
            "climaData": self._armar_clima(),
        }

    def _armar_clima(self):
        hora = datetime.now().hour
        noche = hora >= 18 or hora < 6
        texto = str(self._clima or "").lower()
        if noche:
            mensaje = "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR"
        elif "lluvia" in texto:
            mensaje = "DÍA DE LLUVIA, PERFECTO PARA PRODUCTOS DE OLLA"
        elif "nublado" in texto:
            mensaje = "DÍA NUBLADO, IDEAL PARA COMPRAS EN ABRIGO"
        else:
            mensaje = "PARA ESTE MOMENTO DEL DÍA, TE RECOMENDAMOS LLEVAR"
        producto = "BOLSA DE MENUDENCIOS" if "lluvia" in texto else "POLLO ENTERO"
        precio = 4900
        for prod in self.rows_precios or []:
            nombre = str(prod.get("nombre") or "").lower()
            if producto.lower() in nombre:
                precio = prod.get("precio_oferta") or prod.get("precio") or 4900
                break
        temp = self._clima if "°" in str(self._clima or "") else "22°C"
        return {
            "icono": self._clima_icon or "sol",
            "temperatura": temp,
            "mensaje": mensaje,
            "producto_recomendado": producto,
            "precio": precio,
        }

    def _on_control_clicked(self):
        self._detener() if self._iniciado else self._iniciar()

    def _iniciar(self, screen_index=None):
        from .cerebro_lanzador_tv import ServidorCuello
        self._sincronizar()
        if self._cerebro is None:
            self._cerebro = ServidorCuello(self)
        if not self._cerebro.iniciar(screen_index=screen_index):
            self.lbl_status.setText("● No se pudo iniciar el servidor de TV")
            self.lbl_status.setStyleSheet("color: #FCA5A5;")
            return
        self._iniciado = True
        self.btn_control.setText("DETENER TV")
        self.btn_control.setObjectName("stop")
        self.btn_control.style().unpolish(self.btn_control)
        self.btn_control.style().polish(self.btn_control)
        self.lbl_status.setText(f"● TV emitiendo en http://127.0.0.1:{self._cerebro.port}")
        self.lbl_status.setStyleSheet("color: #86EFAC;")

    def iniciar_carteleria(self):
        """Entrada pública para el dashboard legado de Cartelería."""
        if not self._iniciado:
            self._iniciar()

    def emitir_en_monitor(self, screen_index):
        """F10: mueve el kiosk al monitor elegido, sin arrastrar la consola Qt."""
        if self._iniciado and self._cerebro:
            self._cerebro.reubicar(screen_index)
            self.lbl_status.setText(f"● TV en monitor {screen_index + 1}")
            return
        self._iniciar(screen_index=screen_index)

    def _detener(self):
        if self._cerebro:
            self._cerebro.detener()
        self._iniciado = False
        self.btn_control.setText("INICIAR EN PANTALLA TV")
        self.btn_control.setObjectName("start")
        self.btn_control.style().unpolish(self.btn_control)
        self.btn_control.style().polish(self.btn_control)
        self.lbl_status.setText("● TV detenida. Los datos siguen en caché.")
        self.lbl_status.setStyleSheet("color: #FCD34D;")

    def on_tv_control(self, action):
        """F10/F11/Esc desde el navegador o el gancho global (hilo HTTP)."""
        action = str(action or "").strip().lower()
        if action in ("stop", "f11", "esc"):
            QTimer.singleShot(0, self.detener_carteleria)
        elif action in ("monitor", "f10"):
            QTimer.singleShot(0, self._toggle_fullscreen)

    def detener_carteleria(self):
        """Entrada pública para cerrar la emisión desde otros módulos."""
        if self._iniciado:
            self._detener()

    def _toggle_fullscreen(self):
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app and len(app.screens()) > 1:
            self._window_manager.mostrar_selector_monitor()
            return
        if self._iniciado:
            self.emitir_en_monitor(0)
            return
        self._window_manager.f10_pressed()

    def _emergency_stop(self):
        """Botón de emergencia para detener la cartelería (F11 alternativo)."""
        if hasattr(self, '_window_manager'):
            self._window_manager.f11_pressed()

    def closeEvent(self, event):
        if self._cerebro:
            self._cerebro.detener()
        self._sync_timer.stop()
        if self._sync_worker.isRunning():
            self._sync_worker.requestInterruption()
            self._sync_worker.wait(1000)
        if self._clima_worker.isRunning():
            self._clima_worker.wait(1000)
        super().closeEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Capturar F10 y F11 cuando la ventana Qt tiene el foco."""
        if event.key() == Qt.Key.Key_F10:
            if hasattr(self, '_window_manager'):
                self._window_manager.f10_pressed()
            event.accept()
        elif event.key() == Qt.Key.Key_F11:
            if hasattr(self, '_window_manager'):
                self._window_manager.f11_pressed()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape:
            if hasattr(self, '_window_manager'):
                self._window_manager.f11_pressed()
            event.accept()
        else:
            super().keyPressEvent(event)
