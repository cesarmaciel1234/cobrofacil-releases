from PyQt6.QtWidgets import QTableWidget, QAbstractItemView, QHeaderView, QTableWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont


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


def _fmt_stock(v):
    n = _n(v)
    if abs(n - round(n)) < 0.001:
        return f"{int(round(n)):,}"
    return f"{n:,.2f}"


def _texto_reglas(r):
    partes = []
    c_of = _n(r.get("cant_oferta"))
    p_of = _n(r.get("precio_oferta"))
    p_rel = _n(r.get("precio_oferta_relampago"))
    lim = _n(r.get("limite_oferta_relampago"))

    if c_of > 0 and p_of > 0:
        partes.append(f"Desde {c_of:g}")
    elif p_of > 0:
        partes.append("Directa")
    if p_rel > 0:
        partes.append("Relámpago" + (f" ≤{int(lim)}" if lim > 0 else ""))
    return " · ".join(partes) if partes else "—"


class TablaOfertas(QTableWidget):
    """Lista: nombre, precio, stock, oferta y reglas. Sin ID ni código en pantalla."""

    item_checked = pyqtSignal(str, bool)
    necesita_mas_datos = pyqtSignal()

    HEADERS = ["Nombre", "Precio", "Oferta", "Reglas", "Stock"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(len(self.HEADERS))
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(False)
        self.verticalHeader().setVisible(False)
        self.setShowGrid(False)
        self.setWordWrap(False)

        hh = self.horizontalHeader()
        hh.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hh.setMinimumSectionSize(64)
        # Nombre estira; Stock al final.
        col_widths = [-1, 100, 100, 160, 80]
        for i, w in enumerate(col_widths):
            if w == -1:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self.setColumnWidth(i, w)

        self.verticalHeader().setDefaultSectionSize(42)
        self.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                gridline-color: transparent;
                font-size: 13px;
            }
            QHeaderView::section {
                background: #F8FAFC;
                color: #475569;
                font-weight: 800;
                font-size: 12px;
                padding: 10px 8px;
                border: none;
                border-bottom: 1px solid #E2E8F0;
            }
            QTableWidget::item:selected {
                background: #DBEAFE;
                color: #0F172A;
            }
        """)
        self.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)
        self._paginando = False

    def aplicar_tema(self):
        pass

    def _al_hacer_scroll(self, value):
        if self._paginando:
            return
        bar = self.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() - 15:
            self._paginando = True
            try:
                self.necesita_mas_datos.emit()
            finally:
                self._paginando = False

    def popular_datos(self, filas_nuevas, inicio, checked_ids=None):
        self.blockSignals(True)
        fin = inicio + len(filas_nuevas)
        if self.rowCount() < fin:
            self.setRowCount(fin)

        for i, r in enumerate(filas_nuevas, start=inicio):
            stock = _n(r.get("stock"))
            p_of = _n(r.get("precio_oferta"))
            p_rel = _n(r.get("precio_oferta_relampago"))
            precio_promo = p_of or p_rel
            en_promo = precio_promo > 0
            row_bg = QColor("#FFF7ED" if en_promo else ("#FFFFFF" if i % 2 == 0 else "#F8FAFC"))

            vals = [
                (str(r.get("nombre") or "—"), Qt.AlignmentFlag.AlignLeft),
                (_fmt_plata(r.get("precio")), Qt.AlignmentFlag.AlignRight),
                (_fmt_plata(precio_promo) if en_promo else "—", Qt.AlignmentFlag.AlignRight),
                (_texto_reglas(r), Qt.AlignmentFlag.AlignLeft),
                (_fmt_stock(stock), Qt.AlignmentFlag.AlignRight),
            ]

            for j, (v, align) in enumerate(vals):
                it = QTableWidgetItem(v)
                if j == 0:
                    it.setData(Qt.ItemDataRole.UserRole, str(r.get("id")))
                    if en_promo:
                        it.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                        it.setForeground(QColor("#C2410C"))
                    else:
                        it.setForeground(QColor("#0F172A"))
                else:
                    it.setForeground(QColor("#0F172A"))

                it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | align)
                it.setBackground(row_bg)

                if j == 2 and en_promo:
                    it.setForeground(QColor("#EA580C"))
                    it.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

                if j == 4:
                    if stock <= 0:
                        it.setForeground(QColor("#DC2626"))
                        it.setBackground(QColor("#FEF2F2"))
                    elif stock < 5:
                        it.setForeground(QColor("#D97706"))
                        it.setBackground(QColor("#FFFBEB"))
                    else:
                        it.setForeground(QColor("#059669"))

                self.setItem(i, j, it)

        self.blockSignals(False)

    def select_product_by_id(self, prod_id):
        self.blockSignals(True)
        for row in range(self.rowCount()):
            item = self.item(row, 0)
            if item:
                id_p = item.data(Qt.ItemDataRole.UserRole)
                if str(id_p) == str(prod_id):
                    self.selectRow(row)
                    self.setCurrentItem(item)
                    break
        self.blockSignals(False)
