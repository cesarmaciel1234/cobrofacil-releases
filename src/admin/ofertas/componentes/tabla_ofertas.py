from PyQt6.QtWidgets import QTableWidget, QAbstractItemView, QHeaderView, QTableWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont


class TablaOfertas(QTableWidget):
    item_checked = pyqtSignal(str, bool)
    necesita_mas_datos = pyqtSignal()
    
    HEADERS = ["🗹", "ID / Cód.", "Producto", "Departamento", "Costo", "Precio Reg.", "Stock", "U. Oferta", "Cant. Promo", "Precio Promo"]

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
                
        col_widths = [35, 120, -1, 110, 80, 80, 80, 80, 80, 80]
        hh = self.horizontalHeader()
        for i, w in enumerate(col_widths):
            if w == -1:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                self.setColumnWidth(i, w)

        self.verticalHeader().setDefaultSectionSize(40)
        self.itemChanged.connect(self._on_item_changed)
        self.verticalScrollBar().valueChanged.connect(self._al_hacer_scroll)

    def aplicar_tema(self):
        pass
    def _on_item_changed(self, item):
        if item.column() == 0:
            row = item.row()
            id_item = self.item(row, 1)
            if id_item:
                id_p = id_item.data(Qt.ItemDataRole.UserRole)
                if not id_p: id_p = id_item.text()
                is_checked = (item.checkState() == Qt.CheckState.Checked)
                self.item_checked.emit(str(id_p), is_checked)

    def _al_hacer_scroll(self, value):
        bar = self.verticalScrollBar()
        if bar.maximum() > 0 and value >= bar.maximum() - 15:
            self.necesita_mas_datos.emit()
            
    def popular_datos(self, filas_nuevas, inicio, checked_ids):
        self.blockSignals(True)
        fin = inicio + len(filas_nuevas)
        if self.rowCount() < fin:
            self.setRowCount(fin)
            
        for i, r in enumerate(filas_nuevas, start=inicio):
            dep   = r['departamento'] or ''
            stock = r['stock'] or 0.0
            uni   = (r['unidad'] or 'UN').upper()
            tipo  = "KILO" if uni == 'KG' else "UNIDAD"

            c_of = float(r['cant_oferta'] or 0.0)
            p_of = float(r['precio_oferta'] or 0.0)
            nombre_display = r['nombre'] or ''
            row_bg = QColor("#FFFFFF" if i % 2 == 0 else "#F8FAFC")

            it_check = QTableWidgetItem()
            it_check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            it_check.setBackground(row_bg)
            if str(r['id']) in checked_ids:
                it_check.setCheckState(Qt.CheckState.Checked)
            else:
                it_check.setCheckState(Qt.CheckState.Unchecked)
            self.setItem(i, 0, it_check)

            cod = r['codigo'] or ''
            id_cod_text = f"[{r['id']}]  {cod}" if cod else f"[{r['id']}]"

            vals = [
                (id_cod_text,        Qt.AlignmentFlag.AlignCenter),
                (nombre_display,     Qt.AlignmentFlag.AlignLeft),
                (dep,                Qt.AlignmentFlag.AlignLeft),
                (f"${r['costo']:.2f}", Qt.AlignmentFlag.AlignRight),
                (f"${r['precio']:.2f}", Qt.AlignmentFlag.AlignRight),
                (f"{stock:.2f}",     Qt.AlignmentFlag.AlignRight),
                (tipo,               Qt.AlignmentFlag.AlignCenter),
                (f"{c_of:g}" if c_of > 0 else "-", Qt.AlignmentFlag.AlignCenter),
                (f"${p_of:.2f}" if p_of > 0 else "-", Qt.AlignmentFlag.AlignRight),
            ]

            for j_val, (v, align) in enumerate(vals):
                j = j_val + 1
                it = QTableWidgetItem(v)
                if j == 1:
                    it.setData(Qt.ItemDataRole.UserRole, str(r['id']))
                it.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | align)
                it.setBackground(row_bg)
                it.setForeground(QColor("#0F172A"))

                if j == 2 and c_of > 0 and p_of > 0:
                    it.setForeground(QColor("#EA580C"))
                    it.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

                if j == 6: # Stock
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
            item = self.item(row, 1)
            if item:
                id_p = item.data(Qt.ItemDataRole.UserRole)
                if not id_p: id_p = item.text()
                if str(id_p) == str(prod_id):
                    self.selectRow(row)
                    self.setCurrentItem(item)
                    break
        self.blockSignals(False)
