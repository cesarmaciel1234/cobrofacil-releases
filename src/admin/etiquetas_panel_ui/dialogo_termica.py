"""Diálogo de configuración interactivo para impresión de etiquetas de góndola en ticketera térmica.

Permite al comerciante seleccionar ancho (58mm/80mm), cantidad de copias, corte automático
por cada etiqueta, y previsualizar en tiempo real el resultado en pantalla antes de imprimir.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QRadioButton, QCheckBox, QSpinBox, QTextEdit, QFrame,
    QButtonGroup, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.config import config
from src.utils.theme_manager import theme_manager
from src.utils.letra import fuente_id, fuente_nombre, QSS_TITULO
from src.admin.etiquetas_panel_ui.generador_termica import armar_preview_texto


class ConfigurarTermicaDialog(QDialog):
    def __init__(self, productos: list[dict], rubro: str, negocio: str, parent=None):
        super().__init__(parent)
        self.productos = productos or []
        self.rubro = rubro
        self.negocio = negocio

        self.setWindowTitle("Impresión Térmica de Góndola (Ticketera)")
        self.setFixedSize(680, 560)

        self._setup_ui()
        self._aplicar_estilos()
        self.actualizar_preview()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(14)

        # Encabezado
        lbl_titulo = QLabel("🖨️ ETIQUETAS DE GÓNDOLA EN TICKETERA TÉRMICA")
        lbl_titulo.setStyleSheet("font-size: 16px; font-weight: 900; color: #10B981; letter-spacing: 0.5px;")
        main_layout.addWidget(lbl_titulo)

        sub_titulo = QLabel("Diseñado para pequeños comercios: corte automático listo para encastrar en perfiles de góndola.")
        sub_titulo.setStyleSheet("font-size: 11px; opacity: 0.75; font-weight: 600;")
        main_layout.addWidget(sub_titulo)

        # Contenedor de 2 columnas (Izquierda: Opciones / Derecha: Previsualización en vivo)
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(16)

        # --- COLUMNA IZQUIERDA: OPCIONES ---
        left_widget = QWidget()
        left_lay = QVBoxLayout(left_widget)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(10)

        # 1. Ancho de papel
        lbl_ancho = QLabel("<b>1. Ancho de Ticketera:</b>")
        left_lay.addWidget(lbl_ancho)

        ancho_conf = int(config.get("printer_paper_width_mm", 58) or 58)
        self.bg_ancho = QButtonGroup(self)
        self.rb_58 = QRadioButton("58 mm (Estándar 32 col)")
        self.rb_80 = QRadioButton("80 mm (Ticket ancho 48 col)")
        self.bg_ancho.addButton(self.rb_58)
        self.bg_ancho.addButton(self.rb_80)

        if ancho_conf == 80:
            self.rb_80.setChecked(True)
        else:
            self.rb_58.setChecked(True)

        self.rb_58.toggled.connect(self.actualizar_preview)
        self.rb_80.toggled.connect(self.actualizar_preview)
        left_lay.addWidget(self.rb_58)
        left_lay.addWidget(self.rb_80)

        # 2. Copias por producto
        copias_layout = QHBoxLayout()
        lbl_copias = QLabel("<b>2. Copias por producto:</b>")
        self.spn_copias = QSpinBox()
        self.spn_copias.setRange(1, 50)
        self.spn_copias.setValue(1)
        self.spn_copias.setFixedWidth(70)
        self.spn_copias.setStyleSheet("padding: 4px; font-weight: bold;")
        copias_layout.addWidget(lbl_copias)
        copias_layout.addWidget(self.spn_copias)
        copias_layout.addStretch()
        left_lay.addLayout(copias_layout)

        # 3. Modo de corte
        lbl_corte = QLabel("<b>3. Corte de Papel:</b>")
        left_lay.addWidget(lbl_corte)

        self.bg_corte = QButtonGroup(self)
        self.rb_corte_individual = QRadioButton("✂️ Corte automático por etiqueta (Recomendado)")
        self.rb_corte_lote = QRadioButton("📜 Corte único al final (Tira continua)")
        self.bg_corte.addButton(self.rb_corte_individual)
        self.bg_corte.addButton(self.rb_corte_lote)
        self.rb_corte_individual.setChecked(True)
        self.rb_corte_individual.toggled.connect(self.actualizar_preview)
        left_lay.addWidget(self.rb_corte_individual)
        left_lay.addWidget(self.rb_corte_lote)

        # 4. Opciones de contenido
        lbl_contenido = QLabel("<b>4. Opciones de Contenido:</b>")
        left_lay.addWidget(lbl_contenido)

        self.chk_marca = QCheckBox("Mostrar Nombre de Negocio y Rubro")
        self.chk_marca.setChecked(True)
        self.chk_marca.toggled.connect(self.actualizar_preview)
        left_lay.addWidget(self.chk_marca)

        self.chk_barcode = QCheckBox("Imprimir Código de Barras (ESC/POS)")
        self.chk_barcode.setChecked(True)
        self.chk_barcode.toggled.connect(self.actualizar_preview)
        left_lay.addWidget(self.chk_barcode)

        self.chk_fecha = QCheckBox("Mostrar Fecha de Actualización y PLU")
        self.chk_fecha.setChecked(True)
        self.chk_fecha.toggled.connect(self.actualizar_preview)
        left_lay.addWidget(self.chk_fecha)

        left_lay.addStretch()

        # Badge estado ticketera
        printer_nombre = config.get("ticket_printer", config.get("printer_name", "")) or "Simulación / Conexión Activa"
        self.lbl_printer = QLabel(f"Ticketera: <b>{printer_nombre}</b>")
        self.lbl_printer.setStyleSheet("font-size: 11px; padding: 6px; background: rgba(59, 130, 246, 0.1); border-radius: 6px; border: 1px solid #3B82F6; color: #2563EB;")
        self.lbl_printer.setWordWrap(True)
        left_lay.addWidget(self.lbl_printer)

        cols_layout.addWidget(left_widget, 1)

        # --- COLUMNA DERECHA: PREVIEW EN VIVO ---
        right_widget = QWidget()
        right_lay = QVBoxLayout(right_widget)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(6)

        lbl_prev_title = QLabel("👁️ Vista Previa (Simulación Térmica):")
        lbl_prev_title.setStyleSheet("font-size: 12px; font-weight: bold;")
        right_lay.addWidget(lbl_prev_title)

        self.txt_preview = QTextEdit()
        self.txt_preview.setReadOnly(True)
        self.txt_preview.setFont(QFont("Consolas", 9))
        self.txt_preview.setStyleSheet("border-radius: 8px; padding: 10px; font-family: 'Consolas', monospace;")
        right_lay.addWidget(self.txt_preview)

        cols_layout.addWidget(right_widget, 1)
        main_layout.addLayout(cols_layout)

        # --- BOTONES INFERIORES ---
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(12)

        self.btn_cancelar = QPushButton("CANCELAR")
        self.btn_cancelar.setCursor(Qt.PointingHandCursor)
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_imprimir = QPushButton("🖨️ INICIAR IMPRESIÓN TÉRMICA")
        self.btn_imprimir.setCursor(Qt.PointingHandCursor)
        self.btn_imprimir.setStyleSheet("background: #059669; color: white; font-weight: 900; font-size: 14px; padding: 12px 24px; border-radius: 8px; border: none;")
        self.btn_imprimir.clicked.connect(self.accept)

        btn_bar.addWidget(self.btn_cancelar)
        btn_bar.addStretch()
        btn_bar.addWidget(self.btn_imprimir)
        main_layout.addLayout(btn_bar)

    def _aplicar_estilos(self):
        is_dark = theme_manager.current_theme == "dark"
        bg = "#0F172A" if is_dark else "#FFFFFF"
        fg = "#F8FAFC" if is_dark else "#0F172A"
        border = "#334155" if is_dark else "#CBD5E1"
        prev_bg = "#030712" if is_dark else "#F1F5F9"
        prev_fg = "#4ADE80" if is_dark else "#0F172A"

        self.setStyleSheet(f"""
            QDialog {{ background: {bg}; color: {fg}; font-family: 'Segoe UI'; font-size: 13px; }}
            QLabel {{ color: {fg}; }}
            QRadioButton, QCheckBox {{ spacing: 8px; color: {fg}; font-weight: 500; }}
            QRadioButton::indicator, QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid {border}; border-radius: 8px; background: {bg}; }}
            QCheckBox::indicator {{ border-radius: 4px; }}
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {{ background: #10B981; border-color: #10B981; }}
            QTextEdit {{ background: {prev_bg}; color: {prev_fg}; border: 1px solid {border}; }}
            QPushButton#btn_cancelar {{ background: transparent; color: #EF4444; border: 1px solid #EF4444; border-radius: 8px; padding: 10px 20px; font-weight: bold; }}
            QPushButton#btn_cancelar:hover {{ background: rgba(239, 68, 68, 0.1); }}
        """)

        self.btn_cancelar.setObjectName("btn_cancelar")

    def actualizar_preview(self):
        """Genera el texto de previsualización basado en el primer producto del lote."""
        if not self.productos:
            self.txt_preview.setText("(No hay productos seleccionados)")
            return

        primer_prod = self.productos[0]
        columnas = 48 if self.rb_80.isChecked() else 32
        total_prods = len(self.productos)

        prev_texto = armar_preview_texto(
            producto=primer_prod,
            rubro=self.rubro,
            negocio=self.negocio,
            columnas=columnas,
            cortar=self.rb_corte_individual.isChecked(),
            incluir_barcode=self.chk_barcode.isChecked(),
            incluir_marca=self.chk_marca.isChecked(),
            incluir_fecha=self.chk_fecha.isChecked(),
            numero_item=1 if total_prods > 1 else None,
            total_items=total_prods if total_prods > 1 else None,
        )

        copias = self.spn_copias.value()
        banner_resumen = f"--- LOTE DE {total_prods} PRODUCTO(S) x {copias} COPIA(S) = {total_prods * copias} ETIQUETAS ---\n\n"

        self.txt_preview.setText(banner_resumen + prev_texto)

    def obtener_configuracion(self) -> dict:
        """Devuelve diccionario con todos los parámetros elegidos por el usuario."""
        return {
            "columnas": 48 if self.rb_80.isChecked() else 32,
            "copias": self.spn_copias.value(),
            "cortar_por_etiqueta": self.rb_corte_individual.isChecked(),
            "incluir_barcode": self.chk_barcode.isChecked(),
            "incluir_marca": self.chk_marca.isChecked(),
            "incluir_fecha": self.chk_fecha.isChecked(),
        }
