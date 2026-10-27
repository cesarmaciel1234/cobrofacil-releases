from src.utils.qt_compat import qt_exec
from src.utils.theme_manager import theme_manager
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit,
    QDialog, QFormLayout, QComboBox, QRadioButton, QFrame, QGridLayout,
    QCheckBox, QAbstractItemView
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QBrush, QFont, QKeyEvent

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

from src.creador_pdf_global.motor_pdf import EtiquetaRenderer, abrir_archivo_pdf
from src.utils.letra import fuente_id, fuente_nombre, fuente_numero, QSS_KPI, QSS_TITULO
from src.hardware.printer import printer_manager
from src.admin.etiquetas_panel_ui.generador_termica import armar_lote_etiquetas_termica
from src.admin.etiquetas_panel_ui.dialogo_termica import ConfigurarTermicaDialog


class TablaEtiquetas(QTableWidget):
    """Tabla optimizada para etiquetado: soporta barra espaciadora para marcar/desmarcar filas."""
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Space:
            row = self.currentRow()
            if row >= 0:
                item = self.item(row, 0)
                if item:
                    nuevo_estado = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
                    item.setCheckState(nuevo_estado)
                    event.accept()
                    return
        super().keyPressEvent(event)


class AdminEtiquetas(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.productos_impresos_etiquetas = set()
        self.productos_impresos_ofertas = set()
        self.productos_seleccionados = {}

        self.setup_ui()
        self.cargar_categorias()
        self.cargar_productos()
        self.actualizar_materia_prima_count()

        try:
            theme_manager.theme_changed.connect(self._apply_theme)
        except Exception:
            pass
        QTimer.singleShot(50, self._apply_theme)

    def _create_shadow(self):
        return None

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # --- HEADER PRINCIPAL ---
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)

        self.btn_back = QPushButton("⬅ VOLVER", objectName="btnBack")
        self.btn_back.clicked.connect(self.request_dashboard.emit)
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setFixedHeight(36)
        header_layout.addWidget(self.btn_back)

        self.header_title = QLabel("🏭 PLANTA DE IMPRESIÓN & ETIQUETADO")
        self.header_title.setStyleSheet(QSS_TITULO + " font-size: 20px;")
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()

        self.lbl_status = QLabel("🟢 MOTOR EN LÍNEA")
        self.lbl_status.setStyleSheet(
            "font-weight: 900; font-size: 12px; border-radius: 8px; padding: 6px 14px; "
            "border: 1px solid #10B981; color: #10B981; background: rgba(16, 185, 129, 0.1);"
        )
        header_layout.addWidget(self.lbl_status)
        main_layout.addLayout(header_layout)

        # --- HERO CARDS COMPACTAS ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)

        self.card_materia, self.lbl_stat_materia, self.lbl_sub_materia = self._build_hero_card(
            "📦 CATÁLOGO DISPONIBLE", "Cargando...", "Inventario cargado", "#2563EB"
        )
        cards_layout.addWidget(self.card_materia)

        self.card_lote, self.lbl_stat_lote, self.lbl_sub_lote = self._build_hero_card(
            "⚡ LOTE SELECCIONADO", "0 Productos", "Listos para imprimir", "#059669"
        )
        cards_layout.addWidget(self.card_lote)

        self.card_marca, self.lbl_stat_marca, self.lbl_sub_marca = self._build_hero_card(
            "🏢 MEMBRETE COMERCIAL", "MACIEL - CARNICERÍA", "Encabezado de góndola", "#D97706"
        )
        cards_layout.addWidget(self.card_marca)

        main_layout.addLayout(cards_layout)

        # --- BARRA DE FILTROS Y BÚSQUEDA ---
        filter_box = QFrame()
        filter_box.setObjectName("FilterBox")
        filter_box.setStyleSheet("""
            QFrame#FilterBox {
                background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px 12px;
            }
        """)
        filter_lay = QHBoxLayout(filter_box)
        filter_lay.setContentsMargins(10, 8, 10, 8)
        filter_lay.setSpacing(12)

        # Buscador en tiempo real
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Escanea código de barras, PLU o escribe el nombre del producto...")
        self.txt_search.setClearButtonEnabled(True)
        self.txt_search.setStyleSheet(
            "font-size: 14px; padding: 8px 12px; font-weight: 600; border-radius: 8px; "
            "border: 1px solid #CBD5E1; background: #FFFFFF; color: #1E293B;"
        )
        self.txt_search.textChanged.connect(self.cargar_productos)
        filter_lay.addWidget(self.txt_search, stretch=3)

        # Filtro de categorías
        self.cmb_categoria = QComboBox()
        self.cmb_categoria.setStyleSheet(
            "font-size: 13px; font-weight: 700; padding: 8px 14px; border-radius: 8px; "
            "border: 1px solid #CBD5E1; background: #FFFFFF; color: #1E293B;"
        )
        self.cmb_categoria.currentIndexChanged.connect(self.cargar_productos)
        filter_lay.addWidget(self.cmb_categoria, stretch=1)

        # Separador visual
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        filter_lay.addWidget(sep)

        # Configuración ágil de Membrete
        lbl_brand_tag = QLabel("🏷️ Membrete:")
        lbl_brand_tag.setStyleSheet("font-weight: 800; font-size: 11px; color: #64748B;")
        filter_lay.addWidget(lbl_brand_tag)

        self.txt_negocio = QLineEdit()
        self.txt_negocio.setPlaceholderText("Negocio (Ej: MACIEL)")
        self.txt_negocio.setText("MACIEL")
        self.txt_negocio.setFixedWidth(120)
        self.txt_negocio.setStyleSheet(
            "font-size: 12px; font-weight: 700; padding: 6px 8px; border-radius: 6px; "
            "border: 1px solid #CBD5E1; background: #FFFFFF; color: #1E293B;"
        )
        self.txt_negocio.textChanged.connect(self.actualizar_marca_de_impresion)
        filter_lay.addWidget(self.txt_negocio)

        self.txt_rubro = QLineEdit()
        self.txt_rubro.setPlaceholderText("Rubro (Ej: CARNICERÍA)")
        self.txt_rubro.setText("CARNICERÍA")
        self.txt_rubro.setFixedWidth(130)
        self.txt_rubro.setStyleSheet(
            "font-size: 12px; font-weight: 700; padding: 6px 8px; border-radius: 6px; "
            "border: 1px solid #CBD5E1; background: #FFFFFF; color: #1E293B;"
        )
        self.txt_rubro.textChanged.connect(self.actualizar_marca_de_impresion)
        filter_lay.addWidget(self.txt_rubro)

        main_layout.addWidget(filter_box)

        # --- TABLA DE PRODUCTOS ---
        self.tabla = TablaEtiquetas()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "PROCESAR", "ID / PLU", "DESCRIPCIÓN DEL PRODUCTO", "PRECIO DE VENTA", "CATEGORÍA"
        ])
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.verticalHeader().setDefaultSectionSize(38)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(0, 85)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(1, 130)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(3, 160)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(4, 150)

        self.tabla.itemChanged.connect(self.actualizar_contador_seleccionados)
        self.tabla.cellClicked.connect(self._on_cell_clicked)
        main_layout.addWidget(self.tabla, stretch=1)

        # --- BARRA DE ACCIÓN INFERIOR INDUSTRIAL ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self.btn_select_all = QPushButton("☑️ Marcar Todo")
        self.btn_select_all.clicked.connect(self.seleccionar_todo)
        self.btn_select_all.setCursor(Qt.PointingHandCursor)
        self.btn_select_all.setFixedHeight(42)
        btn_layout.addWidget(self.btn_select_all)

        self.btn_deselect_all = QPushButton("◻️ Desmarcar")
        self.btn_deselect_all.clicked.connect(self.desmarcar_todo)
        self.btn_deselect_all.setCursor(Qt.PointingHandCursor)
        self.btn_deselect_all.setFixedHeight(42)
        btn_layout.addWidget(self.btn_deselect_all)

        self.lbl_seleccion_badge = QLabel("0 productos seleccionados")
        self.lbl_seleccion_badge.setStyleSheet(
            "font-weight: 700; font-size: 13px; color: #64748B; background: #F1F5F9; "
            "border-radius: 8px; padding: 10px 16px;"
        )
        btn_layout.addWidget(self.lbl_seleccion_badge)

        btn_layout.addStretch()

        self.btn_print_thermal = QPushButton("🖨️ IMPRIMIR EN TÉRMICA (CON CORTE)", objectName="btnPrintThermal")
        self.btn_print_thermal.clicked.connect(self.imprimir_termica)
        self.btn_print_thermal.setCursor(Qt.PointingHandCursor)
        self.btn_print_thermal.setFixedHeight(44)
        self.btn_print_thermal.setStyleSheet(
            "background: #059669; color: white; font-size: 14px; font-weight: 900; "
            "padding: 10px 24px; border-radius: 8px; border: none;"
        )
        btn_layout.addWidget(self.btn_print_thermal)

        self.btn_print = QPushButton("📄 LANZAR IMPRESIÓN GÓNDOLA (PDF)", objectName="btnPrint")
        self.btn_print.clicked.connect(self.generar_pdf)
        self.btn_print.setCursor(Qt.PointingHandCursor)
        self.btn_print.setFixedHeight(44)
        self.btn_print.setStyleSheet(
            "background: #2563EB; color: white; font-size: 14px; font-weight: 900; "
            "padding: 10px 24px; border-radius: 8px; border: none;"
        )
        btn_layout.addWidget(self.btn_print)

        main_layout.addLayout(btn_layout)

    def _build_hero_card(self, title, initial_val, subtitle, accent_color):
        card = QFrame()
        card.setObjectName("HeroCard")
        card.setFixedHeight(84)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 12, 18, 12)
        lay.setSpacing(2)

        lbl_tit = QLabel(title)
        lbl_tit.setStyleSheet("font-size: 11px; font-weight: 800; letter-spacing: 0.5px; opacity: 0.75;")

        lbl_val = QLabel(initial_val)
        lbl_val.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {accent_color};")
        lbl_val.setWordWrap(False)

        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("font-size: 11px; font-weight: 500; opacity: 0.6;")

        lay.addWidget(lbl_tit)
        lay.addWidget(lbl_val)
        lay.addWidget(lbl_sub)

        return card, lbl_val, lbl_sub

    def _on_cell_clicked(self, row, col):
        """Al hacer clic en cualquier celda de la fila, alternar el estado de selección."""
        if col != 0:
            item = self.tabla.item(row, 0)
            if item:
                new_state = Qt.CheckState.Unchecked if item.checkState() == Qt.CheckState.Checked else Qt.CheckState.Checked
                item.setCheckState(new_state)

    def cargar_categorias(self):
        """Carga las categorías disponibles en el inventario para el filtro rápido."""
        try:
            self.cmb_categoria.blockSignals(True)
            self.cmb_categoria.clear()
            self.cmb_categoria.addItem("🏷️ Todas las Categorías", "")

            query = "SELECT DISTINCT categoria FROM productos WHERE categoria IS NOT NULL AND categoria != '' ORDER BY categoria"
            rows = db_manager.execute_query(query)
            for r in rows or []:
                row_dict = dict(r) if hasattr(r, 'keys') else dict(r)
                cat = str(row_dict.get('categoria', '')).strip().upper()
                if cat:
                    self.cmb_categoria.addItem(f"📁 {cat}", cat)
        except Exception:
            pass
        finally:
            self.cmb_categoria.blockSignals(False)

    def _apply_theme(self):
        is_dark = theme_manager.current_theme == "dark"
        card_bg = "#1E293B" if is_dark else "#FFFFFF"
        card_border = "#334155" if is_dark else "#E2E8F0"
        text_color = "#F8FAFC" if is_dark else "#0F172A"

        hero_style = f"""
            QFrame#HeroCard {{
                background: {card_bg};
                border: 1px solid {card_border};
                border-radius: 10px;
            }}
        """
        self.card_materia.setStyleSheet(hero_style)
        self.card_lote.setStyleSheet(hero_style)
        self.card_marca.setStyleSheet(hero_style)

        filter_style = f"""
            QFrame#FilterBox {{
                background: {'#0F172A' if is_dark else '#F8FAFC'};
                border: 1px solid {card_border};
                border-radius: 10px;
            }}
        """
        filter_box = self.findChild(QFrame, "FilterBox")
        if filter_box:
            filter_box.setStyleSheet(filter_style)

        btn_bg = theme_manager.get_color("btn_bg")
        btn_text = theme_manager.get_color("btn_text")
        btn_border = theme_manager.get_color("btn_border")
        btn_hover = theme_manager.get_color("btn_hover")

        self.btn_back.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: #EF4444; font-weight: bold; border: 1px solid #EF4444; border-radius: 6px; padding: 6px 14px;
            }}
            QPushButton:hover {{
                background: rgba(239, 68, 68, 0.1);
            }}
        """)

        btn_secondary_qss = f"""
            QPushButton {{
                background: {btn_bg}; color: {btn_text}; border: 1px solid {btn_border}; font-weight: bold; border-radius: 8px; padding: 8px 18px; font-size: 13px;
            }}
            QPushButton:hover {{
                background: {btn_hover};
            }}
        """
        self.btn_select_all.setStyleSheet(btn_secondary_qss)
        self.btn_deselect_all.setStyleSheet(btn_secondary_qss)

        self.btn_print_thermal.setStyleSheet("""
            QPushButton#btnPrintThermal {
                background: #059669; color: white; font-size: 14px; font-weight: 900; padding: 10px 22px; border-radius: 8px; border: none;
            }
            QPushButton#btnPrintThermal:hover {
                background: #047857;
            }
        """)

        self.btn_print.setStyleSheet("""
            QPushButton#btnPrint {
                background: #2563EB; color: white; font-size: 14px; font-weight: 900; padding: 10px 22px; border-radius: 8px; border: none;
            }
            QPushButton#btnPrint:hover {
                background: #1D4ED8;
            }
        """)

        self.cargar_productos()

    def cargar_productos(self):
        try:
            self._llenar_tabla()
        except Exception as e:
            self.tabla.blockSignals(False)
            from src.logger import logger
            logger.exception("Etiquetas de góndola: %s", e)

    def _llenar_tabla(self):
        txt = self.txt_search.text().strip()
        cat_filtro = self.cmb_categoria.currentData() if hasattr(self, 'cmb_categoria') else None
        is_dark = theme_manager.current_theme == "dark"

        self.tabla.blockSignals(True)
        self.tabla.setRowCount(0)

        query = "SELECT id, codigo, nombre, precio, categoria, unidad, cant_oferta, precio_oferta, tipo_unidad_oferta FROM productos WHERE 1=1"
        params = []
        if txt:
            query += " AND (id LIKE ? OR nombre LIKE ? OR codigo LIKE ?)"
            params.extend([f"%{txt}%", f"%{txt}%", f"%{txt}%"])

        if cat_filtro:
            query += " AND categoria = ?"
            params.append(cat_filtro)

        prods = db_manager.execute_query(query, tuple(params))
        for i, raw_p in enumerate(prods or []):
            # Conversión segura y universal de sqlite3.Row o dict
            p = dict(raw_p) if hasattr(raw_p, 'keys') else dict(raw_p)
            self.tabla.insertRow(i)

            p_id_str = str(p['id'])
            is_etiqueta = p_id_str in self.productos_impresos_etiquetas
            is_oferta = p_id_str in self.productos_impresos_ofertas
            is_printed = is_etiqueta or is_oferta
            is_ambos = is_etiqueta and is_oferta

            # Checkbox de selección
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            chk.setCheckState(Qt.CheckState.Checked if p_id_str in self.productos_seleccionados else Qt.CheckState.Unchecked)

            p_codigo = p.get('codigo') or p_id_str
            p_data_payload = {
                "id": p["id"],
                "codigo": p_codigo,
                "nombre": p.get("nombre") or "",
                "precio": p.get("precio") or 0.0,
                "categoria": p.get("categoria") or 'GENERAL',
                "unidad": p.get("unidad") or 'UN',
                "cant_oferta": p.get("cant_oferta") or 0.0,
                "precio_oferta": p.get("precio_oferta") or 0.0,
                "tipo_unidad_oferta": p.get("tipo_unidad_oferta") or "Unidades"
            }
            chk.setData(Qt.ItemDataRole.UserRole, p_data_payload)
            self.tabla.setItem(i, 0, chk)

            # ID / PLU
            id_text = p_codigo if p_codigo else p_id_str
            if is_printed:
                id_text += " ✓"
            id_item = QTableWidgetItem(id_text)
            id_item.setFont(fuente_id())
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 1, id_item)

            # Nombre / Descripción
            nom_text = str(p.get('nombre') or '')
            if is_printed:
                if is_ambos:
                    nom_text = "🏷️🔥 [AMBOS] " + nom_text
                elif is_oferta:
                    nom_text = "🔥 [OFERTA] " + nom_text
                else:
                    nom_text = "🏷️ [ETIQUETA] " + nom_text
            nom_item = QTableWidgetItem(nom_text)
            nom_item.setFont(fuente_nombre())
            self.tabla.setItem(i, 2, nom_item)

            # Precio de venta
            try:
                precio_txt = f"${float(p.get('precio') or 0.0):,.2f}"
            except (TypeError, ValueError):
                precio_txt = "$0.00"
            pr_item = QTableWidgetItem(precio_txt)
            pr_item.setFont(fuente_numero())
            pr_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla.setItem(i, 3, pr_item)

            # Categoría
            cat = p.get('categoria') or 'GENERAL'
            cat_item = QTableWidgetItem(str(cat).upper())
            cat_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            cat_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 4, cat_item)

            self.tabla.item(i, 1).setData(Qt.ItemDataRole.UserRole, p_data_payload)

            # Colores inteligentes para artículos ya impresos vs pendientes
            if is_printed:
                if is_ambos:
                    bg_color = QColor(139, 92, 246, 30 if is_dark else 50)
                    fg_color = QColor("#C4B5FD") if is_dark else QColor("#6D28D9")
                elif is_oferta:
                    bg_color = QColor(249, 115, 22, 30 if is_dark else 50)
                    fg_color = QColor("#FDBA74") if is_dark else QColor("#C2410C")
                else:
                    bg_color = QColor(59, 130, 246, 30 if is_dark else 50)
                    fg_color = QColor("#93C5FD") if is_dark else QColor("#1D4ED8")
            else:
                bg_color = QColor(0, 0, 0, 0)
                fg_color = QColor("#F8FAFC") if is_dark else QColor("#0F172A")

            for col in range(5):
                item = self.tabla.item(i, col)
                if item:
                    item.setBackground(QBrush(bg_color))
                    if col > 0:
                        item.setForeground(QBrush(fg_color))

        self.tabla.blockSignals(False)
        self.actualizar_contador_seleccionados()

    def actualizar_materia_prima_count(self):
        try:
            res = db_manager.execute_query("SELECT COUNT(*) as cant FROM productos")
            count = dict(res[0])['cant'] if res else 0
            self.lbl_stat_materia.setText(f"{count} Productos")
        except Exception:
            self.lbl_stat_materia.setText("Error en catálogo")

    def actualizar_contador_seleccionados(self, item=None):
        if item is not None and item.column() == 0:
            p_data = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(p_data, dict):
                p_id_str = str(p_data["id"])
                if item.checkState() == Qt.CheckState.Checked:
                    self.productos_seleccionados[p_id_str] = p_data
                else:
                    self.productos_seleccionados.pop(p_id_str, None)

        seleccionados = len(self.productos_seleccionados)
        self.lbl_stat_lote.setText(f"{seleccionados} Productos")

        if seleccionados > 0:
            self.lbl_seleccion_badge.setText(f"📌 {seleccionados} producto(s) marcado(s)")
            self.lbl_seleccion_badge.setStyleSheet(
                "font-weight: 900; font-size: 13px; color: #047857; background: #ECFDF5; "
                "border: 1px solid #10B981; border-radius: 8px; padding: 10px 16px;"
            )
            self.btn_print_thermal.setText(f"🖨️ IMPRIMIR EN TÉRMICA ({seleccionados})")
            self.btn_print.setText(f"📄 LANZAR GÓNDOLA PDF ({seleccionados})")
        else:
            self.lbl_seleccion_badge.setText("0 productos seleccionados")
            self.lbl_seleccion_badge.setStyleSheet(
                "font-weight: 700; font-size: 13px; color: #64748B; background: #F1F5F9; "
                "border-radius: 8px; padding: 10px 16px;"
            )
            self.btn_print_thermal.setText("🖨️ IMPRIMIR EN TÉRMICA (CON CORTE)")
            self.btn_print.setText("📄 LANZAR IMPRESIÓN GÓNDOLA (PDF)")

    def actualizar_marca_de_impresion(self):
        rubro = self.txt_rubro.text().strip().upper() or "CARNICERÍA"
        negocio = self.txt_negocio.text().strip().upper() or "MACIEL"
        self.lbl_stat_marca.setText(f"{negocio} - {rubro}")

    def seleccionar_todo(self):
        self.tabla.blockSignals(True)
        for i in range(self.tabla.rowCount()):
            item = self.tabla.item(i, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)
                p_data = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(p_data, dict):
                    p_id_str = str(p_data["id"])
                    self.productos_seleccionados[p_id_str] = p_data
        self.tabla.blockSignals(False)
        self.actualizar_contador_seleccionados()

    def desmarcar_todo(self):
        self.tabla.blockSignals(True)
        for i in range(self.tabla.rowCount()):
            item = self.tabla.item(i, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)
        self.productos_seleccionados.clear()
        self.tabla.blockSignals(False)
        self.actualizar_contador_seleccionados()

    def generar_pdf(self):
        try:
            self._armar_pdf_gondola()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {e}")

    def _armar_pdf_gondola(self):
        rubro = self.txt_rubro.text().strip() or "CARNICERÍA"
        negocio = self.txt_negocio.text().strip() or "MACIEL"

        if not self.productos_seleccionados:
            QMessageBox.warning(self, "Aviso", "Selecciona al menos un producto de la materia prima para imprimir.")
            return

        LIMIT_MAX = 1000
        if len(self.productos_seleccionados) > LIMIT_MAX:
            QMessageBox.warning(
                self,
                "Límite de Impresión Excedido",
                f"⚠️ Lote de Impresión Demasiado Grande\n\n"
                f"Para garantizar un procesamiento instantáneo en Windows y evitar congelamientos de la cola de impresión, "
                f"el límite de seguridad configurado es de {LIMIT_MAX} etiquetas por lote.\n\n"
                f"Seleccionaste: {len(self.productos_seleccionados)} etiquetas.\n"
                f"Por favor, reduce la selección e imprime en lotes más pequeños."
            )
            return

        seleccionados = []
        for p_data in self.productos_seleccionados.values():
            p_id = str(p_data["id"])
            try:
                cant_of = float(p_data.get("cant_oferta") or 0)
            except (TypeError, ValueError):
                cant_of = 0.0
            try:
                precio_of = float(p_data.get("precio_oferta") or 0)
            except (TypeError, ValueError):
                precio_of = 0.0
            is_db_oferta = (cant_of > 0 and precio_of > 0)
            is_oferta = is_db_oferta or (p_id in self.productos_impresos_ofertas)
            precio_final = precio_of if (is_db_oferta and precio_of > 0) else p_data["precio"]

            seleccionados.append({
                "id": p_id,
                "codigo": p_data.get("codigo") or p_id,
                "nombre": p_data["nombre"],
                "precio": str(precio_final),
                "precio_regular": str(p_data["precio"]),
                "categoria": p_data.get("categoria") or "GENERAL",
                "unidad": p_data.get("unidad") or "UN",
                "is_oferta": is_oferta,
                "cant_oferta": cant_of,
                "precio_oferta": precio_of,
                "tipo_unidad_oferta": p_data.get("tipo_unidad_oferta") or "Unidades"
            })

        # Diálogo de configuración moderno
        dlg = QDialog(self)
        dlg.setWindowTitle("Configuración de Etiquetas de Góndola")
        dlg.setFixedSize(500, 480)

        is_dark = theme_manager.current_theme == "dark"
        dlg_bg = "#0F172A" if is_dark else "#FFFFFF"
        dlg_fg = "#F8FAFC" if is_dark else "#0F172A"
        dlg_brd = "#334155" if is_dark else "#E2E8F0"
        dlg_inp = "#1E293B" if is_dark else "#F8FAFC"

        dlg.setStyleSheet(f"""
            QDialog {{ background: {dlg_bg}; color: {dlg_fg}; font-family: 'Segoe UI'; font-size: 14px; }}
            QLabel {{ color: {dlg_fg}; }}
            QPushButton {{ background: #2563EB; color: white; font-weight: bold; padding: 12px; border-radius: 8px; border: none; font-size: 15px; }}
            QPushButton:hover {{ background: #1D4ED8; }}
            QLineEdit, QComboBox {{ padding: 10px; border: 1px solid {dlg_brd}; border-radius: 8px; background: {dlg_inp}; color: {dlg_fg}; }}
            QRadioButton, QCheckBox {{ spacing: 10px; font-weight: 500; color: {dlg_fg}; }}
            QRadioButton::indicator, QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {dlg_brd}; border-radius: 9px; background: {dlg_inp}; }}
            QCheckBox::indicator {{ border-radius: 4px; }}
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {{ background: #3B82F6; border-color: #3B82F6; }}
        """)
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(15)

        lbl_tit = QLabel("🖨️ Formato de Etiquetas")
        lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; margin-bottom: 10px;")
        lay.addWidget(lbl_tit)

        form = QFormLayout()
        form.setSpacing(15)

        cmb_estilo = QComboBox()
        cmb_estilo.addItem("⚪ Estilo Minimalista (Limpio)", "minimalista")
        cmb_estilo.addItem("🔵 Estilo Clásico (Azul)", "clasico")
        cmb_estilo.addItem("⚡ Estilo Neón (Borde Moderno)", "neon")
        form.addRow("<b>Estilo Visual:</b>", cmb_estilo)
        lay.addLayout(form)

        lay.addWidget(QLabel("<b>Distribución de Página (Grilla A4):</b>"))
        lay_grid = QVBoxLayout()
        lay_grid.setSpacing(8)
        rb_3x7 = QRadioButton("Estándar: 21 etiquetas por hoja (3x7)")
        rb_3x7.setChecked(True)
        rb_3x10 = QRadioButton("Compacto: 30 etiquetas por hoja (3x10)")
        rb_4x10 = QRadioButton("Mini: 40 etiquetas por hoja (4x10)")
        lay_grid.addWidget(rb_3x7)
        lay_grid.addWidget(rb_3x10)
        lay_grid.addWidget(rb_4x10)
        lay.addLayout(lay_grid)

        lay.addWidget(QLabel("<b>Opciones de Contenido:</b>"))
        lay_opts = QVBoxLayout()
        lay_opts.setSpacing(8)
        chk_barcode = QCheckBox("Mostrar Código de Barras")
        chk_barcode.setChecked(True)
        chk_marca = QCheckBox("Mostrar Nombre de Negocio / Rubro")
        chk_marca.setChecked(True)
        chk_fecha = QCheckBox("Mostrar Fecha de Impresión y PLU")
        chk_fecha.setChecked(True)
        lay_opts.addWidget(chk_barcode)
        lay_opts.addWidget(chk_marca)
        lay_opts.addWidget(chk_fecha)
        lay.addLayout(lay_opts)

        lay.addStretch()
        btn_ok = QPushButton("🏭 Iniciar Imprenta y Generar PDF")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(dlg.accept)
        lay.addWidget(btn_ok)

        if qt_exec(dlg):
            grilla = "3x7"
            if rb_3x10.isChecked():
                grilla = "3x10"
            elif rb_4x10.isChecked():
                grilla = "4x10"

            try:
                renderer = EtiquetaRenderer()
                pdf_path = renderer.generar_pdf_gondola_personalizado(
                    productos=seleccionados,
                    rubro=rubro,
                    negocio=negocio,
                    grilla_tipo=grilla,
                    mostrar_barcode=chk_barcode.isChecked(),
                    mostrar_marca=chk_marca.isChecked(),
                    mostrar_fecha=chk_fecha.isChecked(),
                    estilo_tipo=cmb_estilo.currentData()
                )

                abrir_archivo_pdf(pdf_path)

                for p in seleccionados:
                    p_id = str(p['id'])
                    if p.get('is_oferta'):
                        self.productos_impresos_ofertas.add(p_id)
                    else:
                        self.productos_impresos_etiquetas.add(p_id)

                self.productos_seleccionados.clear()
                self.cargar_productos()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo generar el PDF: {str(e)}")

    def imprimir_termica(self):
        try:
            self._lanzar_impresion_termica()
        except Exception as e:
            from src.logger import logger
            logger.exception("Etiquetas térmicas: %s", e)
            QMessageBox.critical(self, "Error", f"No se pudo completar la impresión térmica: {e}")

    def _lanzar_impresion_termica(self):
        rubro = self.txt_rubro.text().strip() or "CARNICERÍA"
        negocio = self.txt_negocio.text().strip() or "MACIEL"

        if not self.productos_seleccionados:
            QMessageBox.warning(self, "Aviso", "Selecciona al menos un producto de la materia prima para imprimir.")
            return

        LIMIT_MAX = 500
        if len(self.productos_seleccionados) > LIMIT_MAX:
            QMessageBox.warning(
                self,
                "Límite de Impresión Excedido",
                f"⚠️ Lote de Impresión Demasiado Grande\n\n"
                f"Para garantizar un procesamiento instantáneo en la ticketera y evitar desbordes de papel, "
                f"el límite de seguridad configurado es de {LIMIT_MAX} etiquetas por lote.\n\n"
                f"Seleccionaste: {len(self.productos_seleccionados)} etiquetas.\n"
                f"Por favor, reduce la selección e imprime en lotes más pequeños."
            )
            return

        seleccionados = []
        for p_data in self.productos_seleccionados.values():
            p_id = str(p_data["id"])
            try:
                cant_of = float(p_data.get("cant_oferta") or 0)
            except (TypeError, ValueError):
                cant_of = 0.0
            try:
                precio_of = float(p_data.get("precio_oferta") or 0)
            except (TypeError, ValueError):
                precio_of = 0.0
            is_db_oferta = (cant_of > 0 and precio_of > 0)
            is_oferta = is_db_oferta or (p_id in self.productos_impresos_ofertas)
            precio_final = precio_of if (is_db_oferta and precio_of > 0) else p_data["precio"]

            seleccionados.append({
                "id": p_id,
                "codigo": p_data.get("codigo") or p_id,
                "nombre": p_data["nombre"],
                "precio": str(precio_final),
                "precio_regular": str(p_data["precio"]),
                "categoria": p_data.get("categoria") or "GENERAL",
                "unidad": p_data.get("unidad") or "UN",
                "is_oferta": is_oferta,
                "cant_oferta": cant_of,
                "precio_oferta": precio_of,
                "tipo_unidad_oferta": p_data.get("tipo_unidad_oferta") or "Unidades"
            })

        dlg = ConfigurarTermicaDialog(seleccionados, rubro, negocio, self)
        if qt_exec(dlg):
            cfg = dlg.obtener_configuracion()
            lote_bytes = armar_lote_etiquetas_termica(
                productos=seleccionados,
                rubro=rubro,
                negocio=negocio,
                columnas=cfg["columnas"],
                copias=cfg["copias"],
                cortar_por_etiqueta=cfg["cortar_por_etiqueta"],
                incluir_barcode=cfg["incluir_barcode"],
                incluir_marca=cfg["incluir_marca"],
                incluir_fecha=cfg["incluir_fecha"]
            )

            printer_manager.imprimir_etiquetas_gondola(lote_bytes)

            for p in seleccionados:
                p_id = str(p['id'])
                if p.get('is_oferta'):
                    self.productos_impresos_ofertas.add(p_id)
                else:
                    self.productos_impresos_etiquetas.add(p_id)

            total_impresas = len(seleccionados) * cfg["copias"]
            self.productos_seleccionados.clear()
            self.cargar_productos()

            corte_txt = "con corte individual tras cada etiqueta" if cfg["cortar_por_etiqueta"] else "en tira continua"
            QMessageBox.information(
                self,
                "Impresión Térmica Finalizada",
                f"✅ Se enviaron con éxito {total_impresas} etiqueta(s) a la ticketera ({corte_txt}).\n\n"
                f"Listas para colocar en los perfiles de góndola o vitrina."
            )


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = AdminEtiquetas()
    window.show()
    sys.exit(qt_exec(app))
