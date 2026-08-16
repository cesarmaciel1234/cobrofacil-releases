"""Lanzador directo de cartelería TV: datos + ServidorCuello (HTTP y kiosk)."""

import logging

from PyQt6.QtCore import QObject, QTimer

from src.carteleria.motor_carteleria.db_sync_worker import DbSyncWorker
from src.carteleria.motor_carteleria.clima_worker import ClimaWorker
from src.carteleria.motor_carteleria.estado_tv import armar_paneles

logger = logging.getLogger("LanzadorDirectoTV")

SYNC_MS = 15_000
CLIMA_MS = 15 * 60 * 1000


class LanzadorDirectoTV(QObject):
    """Kiosk de TV sin consola Qt: un solo HTTP (cerebro_lanzador_tv)."""

    def __init__(self):
        super().__init__()
        self.screen_index = None
        self._cuello = None
        self._sync_worker = None
        self._clima_worker = None
        self._sync_timer = None
        self._clima_timer = None
        self._sync_status = "offline"
        self._clima_icon = "sol"
        self._clima = ""
        self.rows_precios = []
        self.sos_data = []
        self.top10_data = {}
        self._paneles = {}

    def lanzar(self, screen_index=None):
        try:
            if self._cuello:
                self.detener()
            self.screen_index = screen_index
            self._cargar_datos_iniciales()
            self._iniciar_motores()
            from src.carteleria.lanzador_tv.cerebro_lanzador_tv import ServidorCuello
            self._cuello = ServidorCuello(self)
            if not self._cuello.iniciar(screen_index=screen_index):
                self.detener()
                return False
            logger.info(
                "Cartelería TV en http://127.0.0.1:%s/  (F10 monitor · F11/ESC salir)",
                self._cuello.port,
            )
            return True
        except Exception as e:
            logger.error("Error lanzando cartelería directa: %s", e)
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
                            self._aplicar_catalogo(productos)
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
                    es_pesable,
                    icono
                FROM productos 
                WHERE COALESCE(stock, 0) > 0
                ORDER BY nombre
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
                            'icono': r.get('icono') or '',
                        })
            
            if productos:
                self._aplicar_catalogo(productos)
                logger.info(f"Cargados {len(self.rows_precios)} productos desde DB")
            else:
                logger.warning("No se encontraron productos en la base de datos")
                
        except Exception as e:
            logger.error(f"Error cargando datos iniciales: {e}")

    def _iniciar_motores(self):
        """Hilos de sync/clima + timers (el padre es QObject para que Qt no trague el arranque)."""
        try:
            if self._sync_worker is None:
                self._sync_worker = DbSyncWorker(self)
                self._sync_worker.sync_finished.connect(self._on_sync_finished)
            if self._clima_worker is None:
                self._clima_worker = ClimaWorker(self)
                self._clima_worker.clima_actualizado.connect(self._on_clima_actualizado)
            if self._sync_timer is None:
                self._sync_timer = QTimer(self)
                self._sync_timer.timeout.connect(self._sincronizar)
            if self._clima_timer is None:
                self._clima_timer = QTimer(self)
                self._clima_timer.timeout.connect(self._sincronizar_clima)
            self._sync_timer.start(SYNC_MS)
            self._clima_timer.start(CLIMA_MS)
            self._sincronizar()
            self._sincronizar_clima()
        except Exception as e:
            logger.warning(f"Error iniciando motores: {e}")

    def _sincronizar(self):
        if self._sync_worker and not self._sync_worker.isRunning():
            self._sync_worker.start()

    def _sincronizar_clima(self):
        if self._clima_worker and not self._clima_worker.isRunning():
            self._clima_worker.start()

    def detener(self):
        try:
            if self._sync_timer:
                self._sync_timer.stop()
            if self._clima_timer:
                self._clima_timer.stop()
            if self._sync_worker and self._sync_worker.isRunning():
                self._sync_worker.requestInterruption()
                self._sync_worker.wait(2000)
            if self._clima_worker and self._clima_worker.isRunning():
                self._clima_worker.requestInterruption()
                self._clima_worker.wait(6000)
            if self._cuello:
                self._cuello.detener()
                self._cuello = None
            logger.info("Cartelería TV directa detenida")
        except Exception as e:
            logger.error("Error deteniendo cartelería: %s", e)

    def on_tv_control(self, action):
        action = str(action or "").strip().lower()
        if action in ("stop", "f11", "esc"):
            self.detener()
        elif action in ("monitor", "f10"):
            self._handle_f10()
    
    def _handle_f10(self):
        """Maneja F10: cambiar monitor."""
        logger.info("F10 presionado - cambiando monitor")
        try:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            n = len(app.screens()) if app else 1
        except Exception:
            n = 1
        self.screen_index = ((self.screen_index or 0) + 1) % max(n, 1)
        if self._cuello:
            self._cuello.reubicar(self.screen_index)
    
    def _handle_f11(self):
        """Maneja F11: detener cartelería."""
        logger.info("F11 presionado - deteniendo cartelería")
        self.detener()
    
    def _handle_esc(self):
        """Maneja ESC: detener cartelería (alternativa a F11)."""
        logger.info("ESC presionado - deteniendo cartelería")
        self.detener()
    
    def _on_sync_finished(self, data, status):
        """Aplica HTTP/MariaDB o caché; no tira el catálogo si el pulso vino vacío."""
        try:
            data = data or {}
            productos = data.get("precios") or []
            if not productos:
                if status:
                    self._sync_status = status
                return
            self._sync_status = status or "online"
            self.sos_data = data.get("sos") or []
            self.top10_data = data.get("top10") or {}
            self._aplicar_catalogo(productos)
            logger.info(
                "Sync %s: %s productos (rotacion=%s)",
                self._sync_status,
                len(self.rows_precios),
                len(self._paneles.get("rotacion") or []),
            )
        except Exception as e:
            logger.warning(f"Error procesando sync: {e}")
    
    def _on_clima_actualizado(self, icon_name, text):
        self._clima_icon = icon_name or "sol"
        self._clima = text
        if self.rows_precios:
            self._refrescar_paneles()
    
    def _normalizar_productos(self, productos):
        """Dict de MariaDB/HTTP o tupla del SELECT de sync."""
        result = []
        for item in productos or []:
            if isinstance(item, dict):
                result.append({
                    "id": item.get("id"),
                    "nombre": item.get("nombre", "") or "",
                    "precio": float(item.get("precio") or 0),
                    "precio_oferta": float(item.get("precio_oferta") or 0),
                    "precio_oferta_relampago": float(item.get("precio_oferta_relampago") or 0),
                    "cant_oferta": float(item.get("cant_oferta") or 0),
                    "tipo_unidad_oferta": item.get("tipo_unidad_oferta") or "",
                    "unidad": item.get("unidad") or "",
                    "es_pesable": item.get("es_pesable") or 0,
                    "departamento": item.get("departamento") or item.get("categoria") or "",
                    "categoria": item.get("categoria") or "",
                    "stock": float(item.get("stock") or 0),
                    "icono": item.get("icono") or "",
                    "es_publicidad": False,
                })
                continue
            row = list(item) if isinstance(item, (list, tuple)) else []
            if len(row) < 3:
                continue
            result.append({
                "id": None,
                "categoria": row[0] if len(row) > 0 else "",
                "nombre": row[1] if len(row) > 1 else "",
                "precio": float(row[2] or 0) if len(row) > 2 else 0,
                "precio_oferta": float(row[3] or 0) if len(row) > 3 else 0,
                "precio_oferta_relampago": float(row[4] or 0) if len(row) > 4 else 0,
                "cant_oferta": float(row[6] or 0) if len(row) > 6 else 0,
                "tipo_unidad_oferta": row[7] if len(row) > 7 else "",
                "stock": float(row[8] or 0) if len(row) > 8 else 0,
                "unidad": row[9] if len(row) > 9 else "",
                "es_pesable": row[10] if len(row) > 10 else 0,
                "departamento": (row[11] if len(row) > 11 else "") or (row[0] if row else ""),
                "icono": row[12] if len(row) > 12 else "",
                "es_publicidad": False,
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

    def _aplicar_catalogo(self, productos):
        self.rows_precios = self._marcar_publicidad(self._normalizar_productos(productos))
        self._refrescar_paneles()

    def _paneles_vacios(self):
        self._paneles = {
            "hero": None,
            "destacados": [],
            "rotacion": [],
            "combos": [],
            "columna3": [],
            "ia": [],
        }

    def _refrescar_paneles(self):
        if not self.rows_precios:
            self._paneles_vacios()
            return
        self._paneles = armar_paneles(self.rows_precios, self._clima_icon, self._clima)

    def get_web_state(self):
        """Estado para la API web conectado con motores globales."""
        try:
            from src.config import config
            from src.carteleria.motor_carteleria.iconos_tv import enriquecer_iconos
            enriquecer_iconos(self.rows_precios)
            if not self._paneles or not self._paneles.get("rotacion"):
                self._refrescar_paneles()
            
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
                    "data_status": self._sync_status,
                },
                "precios": self.rows_precios,
                "sos": self.sos_data,
                "top10": self.top10_data,
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
            
            clima = str(self._clima or "").lower()
            if 18 <= hora_actual or hora_actual < 6:
                mensaje = "PARA ESTE MOMENTO DE LA NOCHE, TE RECOMENDAMOS LLEVAR"
                producto_recomendado = "BOLSA DE MENUDENCIOS" if "lluvia" in clima else "POLLO ENTERO"
            else:
                if "nublado" in clima:
                    mensaje = "Día nublado, ideal para compras en abrigo"
                    producto_recomendado = "POLLO ENTERO"
                elif "lluvia" in clima:
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


# Instancia global singleton
_lanzador_directo = None

def get_lanzador_directo():
    """Obtiene instancia singleton del lanzador directo."""
    global _lanzador_directo
    if _lanzador_directo is None:
        _lanzador_directo = LanzadorDirectoTV()
    return _lanzador_directo