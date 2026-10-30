# tabla_inventario.py - Grilla de visualizacion de productos con scroll infinito.
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from src.utils.theme_manager import theme_manager
from src.utils.letra import fuente_id, fuente_nombre, fuente_numero
from src.config import config


def _n(v, d=0.0):
    try:
        if v is None:
            return d
        return float(v)
    except (TypeError, ValueError):
        return d


def _fmt_plata(v):
    n = _n(v)
    if abs(n - round(n)) < 0.001:
        return f"${int(round(n)):,}"
    return f"${n:,.2f}"


def _fmt_num(v):
    n = _n(v)
    if abs(n - round(n)) < 0.001:
        return f"{int(round(n)):,}"
    return f"{n:,.2f}"


class TablaInventario(QTableWidget):
    producto_doble_clic = pyqtSignal(str)  # Emite el ID del producto
    seleccion_cambiada = pyqtSignal(int)  # Emite la cantidad de filas seleccionadas

    # Oferta (lectura; se edita en Ofertas). Mayoreo (Inventario + Promedios jefe).
    HEADERS = [
        "", "Código", "Producto", "Depto", "IVA %",
        "Costo", "P. venta",
        "Cant. of.", "P. oferta", "Relámpago",
        "Cant. may.", "P. mayoreo",
        "Mín", "Máx", "Tipo", "Stock",
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
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(True)
        self.setObjectName("catalogoTable")
        self.verticalHeader().setDefaultSectionSize(50)
        fuente = QFont("Segoe UI", 11)
        fuente.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.setFont(fuente)
        self.horizontalHeader().setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))

        col_widths = [36, 168, -1, 110, 64, 90, 100, 80, 96, 96, 80, 96, 70, 70, 80, 96]
        hh = self.horizontalHeader()
        hh.setMinimumSectionSize(56)
        hh.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        for i, w in enumerate(col_widths):
            if w == -1:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self.setColumnWidth(i, w)

        self.doubleClicked.connect(self._on_double_click)
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)

    def set_datos(self, filas):
        """Asigna todas las filas y carga la primera pagina."""
        try:
            from src.base_de_datos.database import db_manager
            from src.jefe.promedios.formula.intermediario import aplicar_filas
            filas = aplicar_filas(db_manager, filas)
        except Exception:
            pass
        self.all_rows = filas
        self._depto_color_map = {}
        self.loaded_count = 0
        self.setRowCount(0)
        self.cargar_siguiente_pagina()

    def cargar_siguiente_pagina(self):
        """Carga la siguiente tanda de 50 productos en la grilla sin congelar la interfaz."""
        if self._loading_page:
            return
        self._loading_page = True
        try:
            if self.loaded_count >= len(self.all_rows):
                return

            inicio = self.loaded_count
            fin = min(inicio + 50, len(self.all_rows))

            self.setUpdatesEnabled(False)
            self.blockSignals(True)
            self.setRowCount(fin)

            default_iva = float(config.get("tax_percentage", 21.0))
            f_id = fuente_id(10)
            f_nombre = fuente_nombre(11)
            f_numero = fuente_numero(11)

            color_normal_text = QColor("#0F172A")
            color_oferta = QColor(theme_manager.get_color("oferta"))
            color_mayoreo = QColor("#7C3AED")
            color_agotado = QColor(theme_manager.get_color("stock_agotado"))
            color_bg_agotado = QColor(theme_manager.get_color("bg_stock_agotado"))
            color_bajo = QColor(theme_manager.get_color("stock_bajo"))
            color_bg_bajo = QColor(theme_manager.get_color("bg_stock_bajo"))
            color_saludable = QColor(theme_manager.get_color("stock_saludable"))
            color_tipo = QColor(theme_manager.get_color("tipo_producto"))
            color_bg_impar = QColor(theme_manager.get_color("bg_fila_impar"))

            idx_stock = len(self.HEADERS) - 1
            idx_tipo = len(self.HEADERS) - 2

            for i in range(inicio, fin):
                r = self.all_rows[i]
                dep = r.get("departamento") or ""
                if r.get("stock_texto"):
                    stock = _n(r.get("stock_vista"))
                    texto_stock = str(r.get("stock_texto"))
                else:
                    stock = _n(r.get("stock"))
                    texto_stock = _fmt_num(stock)
                uni = (r.get("unidad") or "UN").upper()
                tipo = "KILO" if uni == "KG" else "UNIDAD"

                depto_iva = r.get("depto_iva")
                if depto_iva is None:
                    depto_iva = default_iva
                else:
                    depto_iva = float(depto_iva)

                dep_key = (dep or "GENERAL").upper()
                if dep_key not in self._depto_color_map:
                    idx = len(self._depto_color_map) % len(self.DEPTO_COLORS)
                    self._depto_color_map[dep_key] = self.DEPTO_COLORS[idx]
                base_hex = self._depto_color_map[dep_key]

                if i % 2 == 1 and base_hex == "#FFFFFF":
                    row_bg = color_bg_impar
                else:
                    row_bg = QColor(base_hex)

                chk = QTableWidgetItem()
                chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                chk.setCheckState(Qt.CheckState.Unchecked)
                chk.setBackground(row_bg)
                self.setItem(i, 0, chk)

                codigo = str(r.get("codigo") or "").strip()
                id_real = str(r.get("id") or "")
                cant_of = _n(r.get("cant_oferta"))
                precio_of = _n(r.get("precio_oferta"))
                relampago = _n(r.get("precio_oferta_relampago"))
                cant_may = _n(r.get("cant_mayoreo"))
                precio_may = _n(r.get("precio_mayoreo"))
                vals = [
                    (codigo or id_real, Qt.AlignmentFlag.AlignLeft, f_id),
                    (r.get("nombre") or "", Qt.AlignmentFlag.AlignLeft, f_nombre),
                    (dep, Qt.AlignmentFlag.AlignLeft, f_nombre),
                    (f"{depto_iva:.0f}%", Qt.AlignmentFlag.AlignCenter, f_numero),
                    (_fmt_plata(r.get("costo")), Qt.AlignmentFlag.AlignRight, f_numero),
                    (_fmt_plata(r.get("precio")), Qt.AlignmentFlag.AlignRight, f_numero),
                    (_fmt_num(cant_of) if cant_of > 0 else "—", Qt.AlignmentFlag.AlignCenter, f_numero),
                    (_fmt_plata(precio_of) if precio_of > 0 else "—", Qt.AlignmentFlag.AlignRight, f_numero),
                    (_fmt_plata(relampago) if relampago > 0 else "—", Qt.AlignmentFlag.AlignRight, f_numero),
                    (_fmt_num(cant_may) if cant_may > 0 else "—", Qt.AlignmentFlag.AlignCenter, f_numero),
                    (_fmt_plata(precio_may) if precio_may > 0 else "—", Qt.AlignmentFlag.AlignRight, f_numero),
                    (_fmt_num(r.get("stock_minimo")), Qt.AlignmentFlag.AlignCenter, f_numero),
                    (_fmt_num(r.get("stock_maximo")), Qt.AlignmentFlag.AlignCenter, f_numero),
                    (tipo, Qt.AlignmentFlag.AlignCenter, f_nombre),
                    (texto_stock, Qt.AlignmentFlag.AlignRight, f_numero),
                ]

                for j, (v, align, font_col) in enumerate(vals, 1):
                    it = QTableWidgetItem(v)
                    it.setFont(font_col)
                    it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | align)
                    it.setBackground(row_bg)
                    it.setForeground(color_normal_text)

                    if j in (7, 8, 9) and v != "—":
                        it.setForeground(color_oferta)

                    if j in (10, 11) and v != "—":
                        it.setForeground(color_mayoreo)

                    if j == idx_stock:
                        if stock <= 0:
                            it.setForeground(color_agotado)
                            it.setBackground(color_bg_agotado)
                        elif stock < 5:
                            it.setForeground(color_bajo)
                            it.setBackground(color_bg_bajo)
                        else:
                            it.setForeground(color_saludable)

                    if j == idx_tipo:
                        it.setForeground(color_tipo)

                    if j == 1:
                        it.setData(Qt.ItemDataRole.UserRole, id_real)
                        if codigo and codigo != id_real:
                            it.setToolTip(f"Id {id_real}")
                    self.setItem(i, j, it)

            self.loaded_count = fin
        finally:
            self.blockSignals(False)
            self.setUpdatesEnabled(True)
            self._loading_page = False

    def _al_hacer_scroll(self, value):
        bar = self.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() - 15:
            self.cargar_siguiente_pagina()

    def _on_selection_changed(self):
        sel = len(self.selectedItems()) // len(self.HEADERS)
        self.seleccion_cambiada.emit(sel)

    def id_de_fila(self, row):
        """El id real. La celda muestra el código de barras."""
        item = self.item(row, 1)
        if not item:
            return None
        guardado = item.data(Qt.ItemDataRole.UserRole)
        if guardado not in (None, ""):
            return str(guardado)
        return item.text() or None

    def _on_double_click(self):
        row = self.currentRow()
        if row != -1:
            pid = self.id_de_fila(row)
            if pid:
                self.producto_doble_clic.emit(pid)

    def obtener_producto_id_seleccionado(self):
        row = self.currentRow()
        if row == -1:
            return None
        return self.id_de_fila(row)

    def aplicar_tema(self, bg, text, border, hover, sel_bg, sel_text, header_bg, header_text):
        self.setStyleSheet(f"""
            QTableWidget {{
                background: {bg};
                border: 1px solid {border};
                border-radius: 12px;
                gridline-color: #CBD5E1;
                outline: none;
                font-size: 13px;
                color: #0F172A;
            }}
            QTableWidget::item {{
                padding: 10px 12px;
                color: #0F172A;
                border-bottom: 1px solid #E2E8F0;
            }}
            QTableWidget::item:hover {{
                background-color: {hover};
            }}
            QTableWidget::item:selected {{
                background-color: {sel_bg};
                color: {sel_text};
                border-bottom: 2px solid #2563EB;
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                color: #0F172A;
                font-weight: 800;
                padding: 14px 10px;
                border: none;
                border-bottom: 2px solid {border};
                border-right: 1px solid #E2E8F0;
                font-size: 12px;
                letter-spacing: 0.2px;
            }}
        """)
