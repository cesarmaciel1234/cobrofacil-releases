# tabla_inventario.py - Grilla de visualizacion de productos con scroll infinito.
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from src.utils.theme_manager import theme_manager

class TablaInventario(QTableWidget):
    producto_doble_clic = pyqtSignal(str) # Emite el ID del producto
    seleccion_cambiada = pyqtSignal(int)  # Emite la cantidad de filas seleccionadas

    HEADERS = [
        "", "ID/Cod", "Descripcion del Producto", "Departamento", "IVA (%)",
        "Costo", "P. Venta", "C. Mayoreo", "P. Mayoreo", "Regla Promo", 
        "Of. Relampago", "Of. Promedio", "Existencia", "Inv. Minimo", "Inv. Maximo", "Tipo de Venta"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.DEPTO_COLORS = theme_manager.get_depto_colors()
        self._depto_color_map = {}
        self.all_rows = []
        self.loaded_count = 0
        self._loading_page = False
        self._setup_ui()

    def _setup_ui(self):
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setObjectName("catalogoTable")
        self.verticalHeader().setDefaultSectionSize(40)

        # Configurar anchos de columna (16 columnas)
        col_widths = [28, 80, -1, 100, 60, 75, 85, 90, 90, 110, 105, 105, 95, 85, 85, 90]
        hh = self.horizontalHeader()
        for i, w in enumerate(col_widths):
            if w == -1:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(i, w)

        # Conectar eventos
        self.doubleClicked.connect(self._on_double_click)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)

    def set_datos(self, filas):
        """Asigna todas las filas y carga la primera pagina."""
        self.all_rows = filas
        self._depto_color_map = {}
        self.loaded_count = 0
        self.setRowCount(0)
        self.cargar_siguiente_pagina()

    def cargar_siguiente_pagina(self):
        """Carga la siguiente tanda de 50 productos en la grilla."""
        if self._loading_page:
            return
        self._loading_page = True
        try:
            if self.loaded_count >= len(self.all_rows):
                return
                
            inicio = self.loaded_count
            fin = min(inicio + 50, len(self.all_rows))
            
            self.blockSignals(True)
            self.setRowCount(fin)
            
            for i in range(inicio, fin):
                r = self.all_rows[i]
                dep = r.get('departamento') or ''
                stock = r.get('stock') or 0.0
                uni = (r.get('unidad') or 'UN').upper()
                tipo = "KILO" if uni == 'KG' else "UNIDAD"
                
                depto_iva = r.get('depto_iva')
                if depto_iva is None:
                    from src.config import config
                    depto_iva = float(config.get("tax_percentage", 21.0))
                else:
                    depto_iva = float(depto_iva)

                dep_key = (dep or "GENERAL").upper()
                if dep_key not in self._depto_color_map:
                    idx = len(self._depto_color_map) % len(self.DEPTO_COLORS)
                    self._depto_color_map[dep_key] = self.DEPTO_COLORS[idx]
                base_hex = self._depto_color_map[dep_key]
                
                if i % 2 == 1 and base_hex == "#FFFFFF":
                    base_hex = theme_manager.get_color("bg_fila_impar")
                row_bg = QColor(base_hex)
                
                # Checkbox item (columna 0)
                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                chk.setCheckState(Qt.CheckState.Unchecked)
                chk.setBackground(row_bg)
                self.setItem(i, 0, chk)

                # Cargar valores restantes
                vals = [
                    (str(r.get('id')),       Qt.AlignmentFlag.AlignRight),
                    (r.get('nombre') or '',  Qt.AlignmentFlag.AlignLeft),
                    (dep,                    Qt.AlignmentFlag.AlignLeft),
                    (f"{depto_iva:.1f}%",    Qt.AlignmentFlag.AlignCenter),
                    (f"${r.get('costo', 0.0):.2f}", Qt.AlignmentFlag.AlignRight),
                    (f"${r.get('precio', 0.0):.2f}", Qt.AlignmentFlag.AlignRight),
                    (f"{r.get('cant_mayoreo', 0.0):g}" if r.get('cant_mayoreo', 0.0) > 0 else "-", Qt.AlignmentFlag.AlignCenter),
                    (f"${r.get('precio_mayoreo', 0.0):.2f}" if r.get('precio_mayoreo', 0.0) > 0 else "-", Qt.AlignmentFlag.AlignRight),
                    (f"{r.get('cant_oferta', 0.0):g} x ${r.get('precio_oferta', 0.0):.2f}" if r.get('precio_oferta', 0.0) else "-", Qt.AlignmentFlag.AlignCenter),
                    (f"${r.get('precio_oferta_relampago', 0.0):.2f}" if r.get('precio_oferta_relampago', 0.0) else "-", Qt.AlignmentFlag.AlignCenter),
                    (f"${r.get('precio_oferta_promedio', 0.0):.2f}" if r.get('precio_oferta_promedio', 0.0) else "-", Qt.AlignmentFlag.AlignCenter),
                    (f"{stock:.2f}",         Qt.AlignmentFlag.AlignRight),
                    (f"{r.get('stock_minimo', 0.0) or 0:.2f}", Qt.AlignmentFlag.AlignCenter),
                    (f"{r.get('stock_maximo', 0.0) or 0:.2f}", Qt.AlignmentFlag.AlignCenter),
                    (tipo,                   Qt.AlignmentFlag.AlignCenter),
                ]

                for j, (v, align) in enumerate(vals, 1):
                    it = QTableWidgetItem(v)
                    it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | align)
                    it.setBackground(row_bg)
                    it.setForeground(QColor(theme_manager.get_color("texto_primario")))

                    # Ofertas
                    if j in (9, 10) and v != "-":
                        it.setForeground(QColor(theme_manager.get_color("oferta")))
                        it.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

                    # Stock colores
                    if j == 12:
                        if stock <= 0:
                            it.setForeground(QColor(theme_manager.get_color("stock_agotado")))
                            it.setBackground(QColor(theme_manager.get_color("bg_stock_agotado")))
                        elif stock < 5:
                            it.setForeground(QColor(theme_manager.get_color("stock_bajo")))
                            it.setBackground(QColor(theme_manager.get_color("bg_stock_bajo")))
                        else:
                            it.setForeground(QColor(theme_manager.get_color("stock_saludable")))

                    # Tipo
                    if j == 15:
                        it.setForeground(QColor(theme_manager.get_color("tipo_producto")))
                        it.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

                    self.setItem(i, j, it)
                    
            self.loaded_count = fin
        finally:
            self.blockSignals(False)
            self._loading_page = False

    def _al_hacer_scroll(self, value):
        bar = self.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() - 15:
            self.cargar_siguiente_pagina()

    def _on_selection_changed(self):
        sel = len(self.selectedItems()) // len(self.HEADERS)
        self.seleccion_cambiada.emit(sel)

    def _on_double_click(self):
        row = self.currentRow()
        if row != -1:
            item_id = self.item(row, 1)
            if item_id:
                self.producto_doble_clic.emit(item_id.text())

    def obtener_producto_id_seleccionado(self):
        row = self.currentRow()
        if row == -1:
            return None
        item_id = self.item(row, 1)
        return item_id.text() if item_id else None

    def aplicar_tema(self, bg, text, border, hover, sel_bg, sel_text, header_bg, header_text):
        self.setStyleSheet(f"""
            QTableWidget {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 12px;
                gridline-color: transparent;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 8px 10px;
                color: {text};
                border-bottom: 1px solid {hover};
            }}
            QTableWidget::item:hover {{
                background-color: {hover};
            }}
            QTableWidget::item:selected {{
                background-color: {sel_bg};
                color: {sel_text};
                border-bottom: 2px solid #3B82F6;
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                color: {header_text};
                font-weight: 900;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid {border};
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
        """)
