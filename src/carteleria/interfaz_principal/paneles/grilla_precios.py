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
        if self._theme_name == "temu":
            # Estilo asiático: Borde sólido Naranja brillante sin defectos de renderización
            self.setStyleSheet(
                f"background: {C_THEME['surface']}; border-radius: {self._corner_radius}px; "
                f"border: 4px solid #FF5722;"
            )
        else:
            self.setStyleSheet(
                f"background: {C_THEME['surface']}; border-radius: {self._corner_radius}px; "
                f"border: 1px solid rgba(255,255,255,0.4);"
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
        """Recorta hijos al rectángulo redondeado (evita overflow hacia el Mensaje)."""
        if self.width() <= 0 or self.height() <= 0:
            return
        path = QPainterPath()
        # -1 px: no dibujar encima del borde de 4px
        inset = 2.0
        path.addRoundedRect(
            QRectF(inset, inset, self.width() - 2 * inset, self.height() - 2 * inset),
            float(self._corner_radius),
            float(self._corner_radius),
        )
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

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

        self.timer.stop()
        self._scroll_pos = 0
        self._block_height = 0
        bar = self.verticalScrollBar()
        bar.setValue(0)

        self._clear_layout(self.inner_layout)
        app = QApplication.instance()
        if app:
            app.processEvents()

        self.blocks = []
        # 3 bloques idénticos bastan para loop infinito sin tanto peso de paint
        for _ in range(3):
            block = QWidget()
            block.setAutoFillBackground(True)
            block.setStyleSheet("background: #FFFFFF;")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 0, 0, 8)
            block_layout.setSpacing(12)
            
            for categoria, productos in items_by_category.items():
                if not productos:
                    continue
                
                from src.carteleria.interfaz_principal.componentes_base.banner_categoria import BannerCategoria
                from src.carteleria.theme import get_active_theme_name
                is_temu = (get_active_theme_name() == "temu")

                banner = BannerCategoria(categoria, modo_tv=self.current_mode, is_temu=is_temu, parent=block)
                block_layout.addWidget(banner)
                
                from src.carteleria.interfaz_principal.tarjetas.tarjeta_producto import TarjetaProducto
                for nombre, precio, precio_oferta, regla in productos:
                    if not nombre or not nombre.strip():
                        continue
                    tarjeta = TarjetaProducto(
                        nombre, precio, precio_oferta, regla,
                        modo_tv=self.current_mode, parent=block,
                    )
                    block_layout.addWidget(tarjeta)
                    
            self.inner_layout.addWidget(block)
            self.blocks.append(block)

        self.container.adjustSize()
        self.container.updateGeometry()
        if app:
            app.processEvents()
        self._block_height = self._measure_block_height()
        self.viewport().update()
        self.timer.start(50)

    def _do_scroll(self):
        bar = self.verticalScrollBar()
        max_val = bar.maximum()
        if max_val <= 0:
            return
        
        if not self.blocks:
            return

        block_height = self._block_height or self._measure_block_height()
        if block_height <= 0:
            return
        self._block_height = block_height

        # Lista corta: no scrollear (evita saltos / solapes)
        if max_val < block_height:
            return
            
        self._scroll_pos += 2
        
        # Loop infinito alineado a la altura real del bloque
        while self._scroll_pos >= block_height:
            self._scroll_pos -= block_height
            
        bar.setValue(int(self._scroll_pos))
