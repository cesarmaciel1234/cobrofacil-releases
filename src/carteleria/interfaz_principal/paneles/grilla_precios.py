import os
from PyQt6.QtWidgets import QScrollArea, QFrame, QVBoxLayout, QWidget, QLabel, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer, QSize, QRectF
from PyQt6.QtGui import QPainterPath, QRegion
from src.carteleria.theme import C_THEME, apply_apple_shadow

def _resolver_icono_png(categoria_nombre):
    # Misma resolución que BannerCategoria (dev + exe)
    from src.carteleria.interfaz_principal.componentes_base.banner_categoria import (
        resolver_icono_png,
    )
    return resolver_icono_png(categoria_nombre)

class GrillaPrecios(QFrame):
    """
    Zona 2: Lista AutoScroll (Envuelto en un Frame estilo Apple)
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        from src.carteleria.motor_carteleria.motor_grilla import MotorGrilla
        self.motor = MotorGrilla(self)
        self.motor.datos_listos.connect(self.set_items)
        
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self._refrescar_grilla)
        self.auto_refresh_timer.start(30000) # 30 segundos
        self._refrescar_grilla() # Carga inicial
        from src.carteleria.theme import get_active_theme_name
        self._theme_name = get_active_theme_name()
        self._corner_radius = 20 if self._theme_name == "temu" else 24
        # Selector por objectName: sin esto el borde naranja se hereda a los
        # 3 bloques del scroll y parecen "contenedores marcados" vacíos.
        self.setObjectName("GrillaPrecios")
        if self._theme_name == "temu":
            self.setStyleSheet(
                f"QFrame#GrillaPrecios {{"
                f" background: {C_THEME['surface']};"
                f" border-radius: {self._corner_radius}px;"
                f" border: 4px solid #FF5722;"
                f"}}"
            )
        else:
            self.setStyleSheet(
                f"QFrame#GrillaPrecios {{"
                f" background: {C_THEME['surface']};"
                f" border-radius: {self._corner_radius}px;"
                f" border: 1px solid rgba(255,255,255,0.4);"
                f"}}"
            )
            apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)

        # Sin esto Qt pinta el scroll FUERA del border-radius (ensucia el hueco hacia el zócalo)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(True)
        
        self.layout = QVBoxLayout(self)
        # Márgenes internos: el scroll no llega al borde naranja ni se vierte abajo
        self.layout.setContentsMargins(16, 16, 16, 16)
        
        from PyQt6.QtWidgets import QSizePolicy
        self.scroll_area = _AutoScrollList()
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.scroll_area)
        
        self.last_items = {}

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._clip_to_rounded_rect()

    def showEvent(self, event):
        super().showEvent(event)
        self._clip_to_rounded_rect()

    def _clip_to_rounded_rect(self):
        """Recorta hijos al rectángulo redondeado. En TVs 4K, setMask rompe el clipping de QScrollArea,
        así que dependemos de los márgenes del layout (16px) que ya evitan que pise el borde redondeado."""
        pass

    def _refrescar_grilla(self):
        if hasattr(self, 'motor') and self.motor and not self.motor.isRunning():
            self.motor.start()

    def closeEvent(self, event):
        self.cleanup()
        super().closeEvent(event)

    def cleanup(self):
        if hasattr(self, 'auto_refresh_timer') and self.auto_refresh_timer:
            self.auto_refresh_timer.stop()
        if hasattr(self, 'motor') and self.motor:
            try:
                self.motor.datos_listos.disconnect(self.set_items)
            except Exception:
                pass
            if self.motor.isRunning():
                self.motor.requestInterruption()
                self.motor.quit()
                self.motor.wait(500)

    def set_layout_mode(self, mode):
        self.scroll_area.current_mode = mode
        if self.last_items:
            self.set_items(self.last_items)
            
    def set_items(self, items_by_category):
        self.last_items = items_by_category
        self.scroll_area.set_items(items_by_category)


class _AutoScrollList(QScrollArea):
    """Componente interno que maneja el scroll y renderizado de ítems"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        # Fondo opaco: evita “fantasma” de filas viejas al hacer scroll / rebuild
        self.setStyleSheet(
            "QScrollArea { background: #FFFFFF; border: none; }"
        )
        self.viewport().setAutoFillBackground(True)
        self.viewport().setStyleSheet("background: #FFFFFF;")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.container.setAutoFillBackground(True)
        self.container.setStyleSheet("background: #FFFFFF;")
        
        # Ancho mínimo 0 (no forzar expansión horizontal); alto = layout real
        self.container.minimumSizeHint = lambda: QSize(
            0,
            self.container.layout().minimumSize().height() if self.container.layout() else 0,
        )
        
        self.inner_layout = QVBoxLayout(self.container)
        # Más aire abajo: la última tarjeta no pisa el borde naranja / zócalo
        self.inner_layout.setContentsMargins(2, 4, 2, 12)
        self.inner_layout.setSpacing(12)
        self.setWidget(self.container)
        
        self._scroll_pos = 0
        self._block_height = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._do_scroll)
        self.current_mode = 4
        self.blocks = []

    def _clear_layout(self, layout):
        """Borra widgets de inmediato (deleteLater deja pintura sucia al scrollear)."""
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.hide()
                w.setParent(None)
                w.deleteLater()
            elif item.layout() is not None:
                self._clear_layout(item.layout())

    def _measure_block_height(self) -> int:
        if not self.blocks:
            return 0
        b0 = self.blocks[0]
        # Preferir tamaño de layout (estable) sobre height() a medio pintar
        h = 0
        lay = b0.layout()
        if lay is not None:
            h = max(lay.sizeHint().height(), lay.minimumSize().height())
        h = max(h, b0.sizeHint().height(), b0.height())
        if len(self.blocks) >= 2:
            # Distancia real entre bloques gemelos (más fiable para el loop)
            y0 = self.blocks[0].y()
            y1 = self.blocks[1].y()
            if y1 > y0:
                return y1 - y0
        return h + self.inner_layout.spacing()

    def set_items(self, items_by_category):
        # Evitar reconstruir la UI si los datos no cambiaron (previene congelamiento)
        current_data_repr = str(items_by_category)
        if getattr(self, '_last_data_repr', None) == current_data_repr:
            return
        self._last_data_repr = current_data_repr

        try:
            self.timer.stop()
        except Exception:
            pass
        self._scroll_pos = 0
        self._block_height = 0
        try:
            self.verticalScrollBar().setValue(0)
        except Exception:
            pass

        self._clear_layout(self.inner_layout)
        # No processEvents aquí: reentra set_items y congela la TV

        self.blocks = []
        items_by_category = items_by_category or {}
        tiene_productos = any(bool(p) for p in items_by_category.values())
        if not tiene_productos:
            # Sin datos: no crear los 3 bloques vacíos (parecen cajas marcadas)
            try:
                self.viewport().update()
            except Exception:
                pass
            return

        try:
            from src.carteleria.interfaz_principal.componentes_base.banner_categoria import (
                BannerCategoria,
            )
            from src.carteleria.interfaz_principal.tarjetas.tarjeta_producto import (
                TarjetaProducto,
            )
            from src.carteleria.theme import get_active_theme_name

            is_temu = get_active_theme_name() == "temu"
            
            from src.carteleria.interfaz_principal.tarjetas.tarjeta_publicidad import TarjetaPublicidad
            from src.carteleria.motor_carteleria.motor_publicidad import motor_publicidad
            import random
            motor_publicidad.cargar_configuracion() # Sincronizar con Gestor solo 1 vez

            # 3 bloques idénticos bastan para loop infinito
            for _ in range(3):
                block = QWidget()
                block.setObjectName("GrillaScrollBlock")
                block.setAutoFillBackground(True)
                block.setStyleSheet(
                    "QWidget#GrillaScrollBlock { background: #FFFFFF; border: none; }"
                )
                block_layout = QVBoxLayout(block)
                block_layout.setContentsMargins(0, 0, 0, 8)
                block_layout.setSpacing(12)
                self.inner_layout.addWidget(block)
                self.blocks.append((block, block_layout))
                
            # Crear pool de anuncios
            pool_ads = []
            for cat, prods in items_by_category.items():
                for p in prods:
                    if motor_publicidad.is_promocionado(p[0]):
                        pool_ads.append(p)
            
            # Construir Plan de Orquestación (Tareas a pintar)
            self._render_queue = []
            for block, block_layout in self.blocks:
                for categoria, productos in items_by_category.items():
                    if not productos: continue
                    
                    # Tarea: Añadir Banner
                    self._render_queue.append((block, block_layout, 'banner', categoria, None))
                    
                    cat_card_count = 0
                    ad_injected_in_cat = False
                    
                    for prod in productos:
                        if not prod[0] or not str(prod[0]).strip(): continue
                        self._render_queue.append((block, block_layout, 'product', None, prod))
                        cat_card_count += 1
                        
                        if cat_card_count % 4 == 0 and pool_ads:
                            ad = random.choice(pool_ads)
                            self._render_queue.append((block, block_layout, 'ad', None, ad))
                            ad_injected_in_cat = True
                            
                    if not ad_injected_in_cat and pool_ads:
                        ad = random.choice(pool_ads)
                        self._render_queue.append((block, block_layout, 'ad', None, ad))
                        
            # Iniciar Orquestador
            self._process_render_queue()
            
        except Exception as e:
            try:
                from src.logger import logger
                logger.error(f"GrillaPrecios set_items: {e}")
            except Exception:
                pass
            self.blocks = []

    def _process_render_queue(self):
        """El Orquestador: Pinta un chunk de tarjetas y cede el control para no congelar la UI"""
        if not hasattr(self, '_render_queue') or not self._render_queue:
            # Terminado de pintar
            # Extraer solo los QWidget block para self.blocks (ya que guardamos tuplas)
            if self.blocks and isinstance(self.blocks[0], tuple):
                self.blocks = [b[0] for b in self.blocks]
            
            self.container.adjustSize()
            self.container.updateGeometry()
            self._block_height = self._measure_block_height()
            self.viewport().update()
            self.timer.start(16)
            return
            
        from src.carteleria.interfaz_principal.componentes_base.banner_categoria import BannerCategoria
        from src.carteleria.interfaz_principal.tarjetas.tarjeta_producto import TarjetaProducto
        from src.carteleria.interfaz_principal.tarjetas.tarjeta_publicidad import TarjetaPublicidad
        from src.carteleria.theme import get_active_theme_name
        is_temu = get_active_theme_name() == "temu"

        chunk_size = 15 # Número de tarjetas a pintar por "pincelada"
        for _ in range(min(chunk_size, len(self._render_queue))):
            block, block_layout, task_type, cat, prod = self._render_queue.pop(0)
            
            if task_type == 'banner':
                banner = BannerCategoria(cat, modo_tv=self.current_mode, is_temu=is_temu, parent=block)
                block_layout.addWidget(banner)
            elif task_type == 'product':
                tarjeta = TarjetaProducto(prod[0], prod[1], prod[2], prod[3], modo_tv=self.current_mode, parent=block)
                block_layout.addWidget(tarjeta)
            elif task_type == 'ad':
                tarjeta_ad = TarjetaPublicidad(prod[0], prod[1], prod[2], prod[3], modo_tv=self.current_mode, parent=block)
                block_layout.addWidget(tarjeta_ad)
                
        # Agendar la siguiente pincelada en el Event Loop
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(16, self._process_render_queue)
    def _do_scroll(self):
        bar = self.verticalScrollBar()
        max_val = bar.maximum()
        if max_val <= 0:
            return
        
        if not self.blocks or len(self.blocks) < 2:
            return

        # Calcular la altura del bloque en tiempo real.
        # Esto soluciona los saltos si las tarjetas de producto
        # crecen dinámicamente por tener nombres largos en múltiples líneas.
        y0 = self.blocks[0].y()
        y1 = self.blocks[1].y()
        
        if y1 > y0:
            block_height = y1 - y0
        else:
            block_height = self._block_height or self._measure_block_height()
            
        if block_height <= 0:
            return
            
        self._block_height = block_height

        # Lista corta: no scrollear (evita saltos / solapes)
        if max_val < block_height:
            return
            
        # Velocidad ajustada para 60fps (aprox 1px cada 16ms = ~60px/s)
        self._scroll_pos += 1.0
        
        # Loop infinito alineado a la altura real del bloque
        while self._scroll_pos >= block_height:
            self._scroll_pos -= block_height
            
        bar.setValue(int(self._scroll_pos))
