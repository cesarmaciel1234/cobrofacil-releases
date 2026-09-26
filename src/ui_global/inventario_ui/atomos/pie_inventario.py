# pie_inventario.py - Footer informativo del catalogo de productos.
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel
from src.utils.theme_manager import theme_manager


class PieInventario(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(46)
        self.setObjectName("catalogoFooter")
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)

        self.lbl_total = QLabel("0 productos")
        self.lbl_stock0 = QLabel("")
        self.lbl_sel = QLabel("")

        for lbl in [self.lbl_total, self.lbl_stock0, self.lbl_sel]:
            lbl.setStyleSheet("font-size: 13px; background: transparent; color: #0F172A;")
            layout.addWidget(lbl)
            if lbl != self.lbl_sel:
                layout.addSpacing(24)

        layout.removeWidget(self.lbl_sel)
        layout.addStretch()
        layout.addWidget(self.lbl_sel)

    def actualizar_totales(self, total, sin_stock):
        """Actualiza las etiquetas con la informacion de conteo y stock critico."""
        self.lbl_total.setText(f"📦 {total} PRODUCTOS EN INVENTARIO")
        self.lbl_total.setStyleSheet(
            "font-weight: 800; font-size: 13px; background: transparent; color: #0F172A;"
        )

        color_agotado = theme_manager.get_color("stock_agotado")
        color_saludable = theme_manager.get_color("stock_saludable")

        self.lbl_stock0.setText(
            f"⚠️ Stock crítico: {sin_stock}" if sin_stock else "✅ Stock saludable"
        )
        self.lbl_stock0.setStyleSheet(
            f"color: {color_agotado if sin_stock else color_saludable}; "
            "font-size: 13px; font-weight: 800; background: transparent;"
        )

    def actualizar_seleccion(self, cantidad):
        """Actualiza el indicador de productos seleccionados en la grilla."""
        self.lbl_sel.setText(f"Seleccionados: {cantidad}" if cantidad else "")
        self.lbl_sel.setStyleSheet(
            "font-size: 13px; font-weight: 700; background: transparent; color: #1E3A8A;"
        )
