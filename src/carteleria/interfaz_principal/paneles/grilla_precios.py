import os
from PyQt6.QtWidgets import QScrollArea, QFrame, QVBoxLayout, QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from src.carteleria.theme import C_THEME, apply_apple_shadow

def _resolver_icono_png(categoria_nombre):
    cat_upper = str(categoria_nombre).upper().strip()
    base_dir = os.path.join(os.getcwd(), "Catalogos", "iconos_rubros")
    
    # 1. Buscar en BD si el departamento tiene ícono específico asignado
    try:
        from src.motor_inventario.motor_departamentos import MotorDepartamentos
        deps = MotorDepartamentos().obtener_departamentos()
        for d in deps:
            if d.get('nombre', '').upper().strip() == cat_upper and d.get('icono'):
                fpath = os.path.join(base_dir, d['icono'])
                if os.path.exists(fpath):
                    return fpath
    except Exception:
        pass

    # 2. Buscar por mapeo automático de palabras clave
    kw_map = [
        (["CARNE", "VACUNO", "ASADO", "LOMO", "BIFE", "TERNERA", "ACHURA", "MONDONGO"], "carne.png"),
        (["POLLO", "AVE", "PATA", "SUPREMA", "PECHUGA", "ALITA"], "pollo.png"),
        (["CERDO", "BONDIOLA", "PECHITO", "CHUCHETO", "LECHON"], "cerdo.png"),
        (["QUESO", "FIAMBRE", "LACTEO", "JAMON", "PROVOLETA", "EMBUTIDO", "CHORIZO", "MORCILLA", "SALCHICHA"], "fiambreria.png"),
        (["PAN", "PANADERIA", "FACTURA", "BIZCOCHO", "TORTA"], "panaderia.png"),
        (["VERDURA", "VERDULERIA", "FRUTA", "FRUTAL"], "verduleria.png"),
        (["BEBIDA", "GASEOSA", "CERVEZA", "VINO", "AGUA", "JUGO"], "bebidas.png"),
        (["LIMPIEZA", "JABON", "DETERGENTE", "LAVANDINA"], "limpieza.png"),
        (["PESCADO", "MARISCO", "FILET"], "pescado.png"),
        (["OFERTA", "PROMO", "COMBO", "DESTACADO", "RELAMPAGO"], "oferta.png"),
        (["ALMACEN", "MERCADERIA", "ABARROTES"], "almacen.png")
    ]
    for kws, fname in kw_map:
        if any(w in cat_upper for w in kws):
            fpath = os.path.join(base_dir, fname)
            if os.path.exists(fpath):
                return fpath

    return None

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
        if get_active_theme_name() == "temu":
            # Estilo asiático: Borde sólido Naranja brillante sin defectos de renderización
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 20px; border: 4px solid #FF5722;")
        else:
            self.setStyleSheet(f"background: {C_THEME['surface']}; border-radius: 24px; border: 1px solid rgba(255,255,255,0.4);")
            apply_apple_shadow(self, blur=40, alpha=20, y_offset=15)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20) # Margen amplio para que el contenido no pise los bordes redondeados
        
        from PyQt6.QtWidgets import QSizePolicy
        self.scroll_area = _AutoScrollList()
        self.scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.layout.addWidget(self.scroll_area)
        
        self.last_items = {}

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
        self.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.viewport().setStyleSheet("background: transparent;")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        
        # ¡BLINDAJE DEFINITIVO CONTRA RECORTE HORIZONTAL!
        # Sobreescribimos minimumSizeHint para que el ancho mínimo sea 0 y Qt NUNCA extienda el contenedor más allá del viewport
        from PyQt6.QtCore import QSize
        self.container.minimumSizeHint = lambda: QSize(0, self.container.layout().minimumSize().height() if self.container.layout() else 0)
        
        self.inner_layout = QVBoxLayout(self.container)
        self.inner_layout.setContentsMargins(2, 4, 2, 4) # Márgenes internos compactos
        self.inner_layout.setSpacing(10)
        self.setWidget(self.container)
        
        self._scroll_pos = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._do_scroll)
        self.current_mode = 4

    def set_items(self, items_by_category):
        # Evitar reconstruir la UI si los datos no cambiaron (previene congelamiento)
        current_data_repr = str(items_by_category)
        if getattr(self, '_last_data_repr', None) == current_data_repr:
            return
        self._last_data_repr = current_data_repr

        for i in reversed(range(self.inner_layout.count())):
            item = self.inner_layout.itemAt(i)
            if item is not None:
                if item.widget():
                    w = item.widget()
                    self.inner_layout.removeWidget(w)
                    w.setParent(None)
                    w.deleteLater()
                else:
                    self.inner_layout.removeItem(item)
                
        self.container.adjustSize()
                
        self.blocks = []
        # Añadimos 4 bloques para asegurar suficiente margen de scroll infinito
        for _ in range(4): 
            block = QWidget()
            block.setStyleSheet("background: transparent;")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(0, 0, 0, 0)
            block_layout.setSpacing(10)
            
            for categoria, productos in items_by_category.items():
                if not productos:
                    continue # Nunca dibujar categorías vacías
                
                # ── CATEGORÍA: BANNER MODULAR CON CÁPSULA DE ÍCONO Y TITULO RESPONSIVE ──
                from src.carteleria.interfaz_principal.componentes_base.banner_categoria import BannerCategoria
                from src.carteleria.theme import get_active_theme_name
                is_temu = (get_active_theme_name() == "temu")

                banner = BannerCategoria(categoria, modo_tv=self.current_mode, is_temu=is_temu, parent=block)
                block_layout.addWidget(banner)
                
                # ── PRODUCTOS: TARJETAS MODULARES CON SUB-CONTENEDORES ESTRICTOS ──
                from src.carteleria.interfaz_principal.tarjetas.tarjeta_producto import TarjetaProducto
                for nombre, precio, precio_oferta, regla in productos:
                    if not nombre or not nombre.strip():
                        continue
                    tarjeta = TarjetaProducto(nombre, precio, precio_oferta, regla, modo_tv=self.current_mode, parent=block)
                    block_layout.addWidget(tarjeta)
                    
            self.inner_layout.addWidget(block)
            self.blocks.append(block)
                    
        # IMPORTANTE: Eliminamos el stretch inferior para que los bloques sean matemáticamente idénticos
        # y no haya huecos vacíos en el bucle infinito.
        
        # Forzar recálculo para que height() devuelva el valor real
        self.container.layout().update()
        self.timer.start(50)

    def _do_scroll(self):
        bar = self.verticalScrollBar()
        max_val = bar.maximum()
        if max_val == 0: return
        
        if not hasattr(self, 'blocks') or not self.blocks:
            return
            
        # Distancia exacta entre el inicio del bloque 1 y el inicio del bloque 2
        block_height = self.blocks[0].height() + self.inner_layout.spacing()
        
        # Freno de seguridad: si la lista es tan corta que todos los ítems caben en la pantalla
        # detenemos el scroll para evitar parpadeos, ya que no es necesario navegar.
        if block_height <= 0 or max_val < block_height:
            return
            
        self._scroll_pos += 2
        
        # El salto infinito: Si hemos scrolleado la altura de un bloque entero, 
        # retrocedemos matemáticamente al mismo píxel del bloque anterior. Es imperceptible.
        if self._scroll_pos >= block_height:
            self._scroll_pos -= block_height
            
        bar.setValue(self._scroll_pos)
