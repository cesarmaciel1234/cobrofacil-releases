from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QPushButton, QAbstractItemView, QCheckBox, QMessageBox,
    QDialog, QGridLayout, QDoubleSpinBox, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
try:
    from src.database import db_manager
except ImportError:
    from database import db_manager


class Admin2Masivo(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💹 Cambio de Precios Masivo")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 750)
        self._todos_productos = []
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #f8fafc; font-family: 'Segoe UI'; }
            QFrame#header { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1e3a8a, stop:1 #3b82f6); }
            QTableWidget { background: white; border: 1px solid #e2e8f0; border-radius: 8px; }
            QHeaderView::section { background: #1e3a8a; color: white; font-weight: bold; padding: 6px; border: none; }
            QPushButton { border-radius: 8px; font-weight: bold; padding: 8px 18px; }
        """)
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # --- HEADER ---
        header = QFrame(); header.setObjectName("header"); header.setFixedHeight(55)
        hl = QHBoxLayout(header); hl.setContentsMargins(20, 0, 20, 0)
        lbl = QLabel("💹 CAMBIO MASIVO DE PRECIOS")
        lbl.setStyleSheet("color: white; font-size: 18px; font-weight: 900; letter-spacing: 1px;")
        hl.addWidget(lbl)
        hl.addStretch()
        lbl_sub = QLabel("Seleccioná productos y aplicá el ajuste")
        lbl_sub.setStyleSheet("color: #93c5fd; font-size: 12px;")
        hl.addWidget(lbl_sub)
        main.addWidget(header)

        # --- FILTROS ---
        filtros = QFrame(); filtros.setStyleSheet("background: white; border-bottom: 1px solid #e2e8f0;")
        fl = QHBoxLayout(filtros); fl.setContentsMargins(15, 10, 15, 10); fl.setSpacing(12)

        fl.addWidget(QLabel("🔍 Buscar:"))
        self.txt_buscar = QLineEdit(); self.txt_buscar.setPlaceholderText("Nombre o código...")
        self.txt_buscar.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 10px;")
        self.txt_buscar.textChanged.connect(self._filtrar)
        fl.addWidget(self.txt_buscar, 2)

        fl.addWidget(QLabel("📂 Categoría:"))
        self.cmb_cat = QComboBox()
        self.cmb_cat.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 8px;")
        self.cmb_cat.currentTextChanged.connect(self._filtrar)
        fl.addWidget(self.cmb_cat, 1)

        btn_sel_todo = QPushButton("☑ Seleccionar todo")
        btn_sel_todo.setStyleSheet("background: #e2e8f0; color: #334155;")
        btn_sel_todo.clicked.connect(self._seleccionar_todo)
        fl.addWidget(btn_sel_todo)

        btn_desel = QPushButton("☐ Deseleccionar")
        btn_desel.setStyleSheet("background: #e2e8f0; color: #334155;")
        btn_desel.clicked.connect(self._deseleccionar_todo)
        fl.addWidget(btn_desel)

        main.addWidget(filtros)

        # --- TABLA ---
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(["✅", "Código", "Nombre", "Categoría", "Precio Actual", "Nuevo Precio", "Diferencia"])
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.setColumnWidth(0, 40)
        self.tabla.setColumnWidth(1, 80)
        self.tabla.setColumnWidth(3, 130)
        self.tabla.setColumnWidth(4, 110)
        self.tabla.setColumnWidth(5, 110)
        self.tabla.setColumnWidth(6, 100)
        self.tabla.setSelectionMode(QAbstractItemView.NoSelection)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setStyleSheet("""
            QTableWidget { alternate-background-color: #f8fafc; }
        """)
        main.addWidget(self.tabla, 1)

        # --- PANEL DE AJUSTE ---
        panel = QFrame(); panel.setStyleSheet("background: white; border-top: 2px solid #e2e8f0;")
        panel.setFixedHeight(90)
        pl = QHBoxLayout(panel); pl.setContentsMargins(20, 10, 20, 10); pl.setSpacing(20)

        pl.addWidget(QLabel("⚙️ Tipo de ajuste:"))
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["% Aumento", "% Descuento", "Precio fijo", "$ Aumento", "$ Descuento"])
        self.cmb_tipo.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 10px; min-width: 130px;")
        self.cmb_tipo.currentIndexChanged.connect(self._preview_ajuste)
        pl.addWidget(self.cmb_tipo)

        pl.addWidget(QLabel("Valor:"))
        self.spin_valor = QDoubleSpinBox()
        self.spin_valor.setRange(0, 9999999)
        self.spin_valor.setDecimals(2)
        self.spin_valor.setSuffix(" %")
        self.spin_valor.setValue(10.0)
        self.spin_valor.setStyleSheet("border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 8px; min-width: 110px;")
        self.spin_valor.valueChanged.connect(self._preview_ajuste)
        self.cmb_tipo.currentIndexChanged.connect(self._actualizar_sufijo)
        pl.addWidget(self.spin_valor)

        pl.addStretch()

        # Contador seleccionados
        self.lbl_sel = QLabel("0 productos seleccionados")
        self.lbl_sel.setStyleSheet("color: #64748b; font-weight: bold;")
        pl.addWidget(self.lbl_sel)

        btn_preview = QPushButton("👁 Vista Previa")
        btn_preview.setStyleSheet("background: #e0f2fe; color: #0284c7; border: 1px solid #0284c7;")
        btn_preview.clicked.connect(self._preview_ajuste)
        pl.addWidget(btn_preview)

        self.btn_conf = QPushButton("💾 APLICAR CAMBIOS")
        self.btn_conf.setStyleSheet("background: #16a34a; color: white; font-size: 14px; padding: 10px 24px;")
        self.btn_conf.clicked.connect(self._confirmar)
        pl.addWidget(self.btn_conf)

        main.addWidget(panel)

    def _actualizar_sufijo(self):
        tipo = self.cmb_tipo.currentText()
        if "%" in tipo:
            self.spin_valor.setSuffix(" %")
        else:
            self.spin_valor.setSuffix(" $")

    def cargar_datos(self):
        res = db_manager.execute_query(
            "SELECT id, nombre, precio, stock, categoria FROM productos ORDER BY nombre"
        ) or []
        self._todos_productos = [dict(r) for r in res]

        # Llenar combo categorías
        cats = sorted(set(r.get('categoria', '') or 'Sin categoría' for r in self._todos_productos))
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.addItem("Todas")
        self.cmb_cat.addItems(cats)
        self.cmb_cat.blockSignals(False)

        self._renderizar(self._todos_productos)

    def _filtrar(self):
        texto = self.txt_buscar.text().lower()
        cat = self.cmb_cat.currentText()
        filtrados = []
        for p in self._todos_productos:
            if texto and texto not in (p.get('nombre', '') or '').lower() and texto not in str(p.get('id', '')):
                continue
            if cat != "Todas" and (p.get('categoria', '') or 'Sin categoría') != cat:
                continue
            filtrados.append(p)
        self._renderizar(filtrados)

    def _renderizar(self, productos):
        self.tabla.setRowCount(len(productos))
        for i, p in enumerate(productos):
            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Unchecked)
            chk.setData(Qt.UserRole, p['id'])
            self.tabla.setItem(i, 0, chk)
            self.tabla.setItem(i, 1, QTableWidgetItem(str(p.get('id', ''))))
            self.tabla.setItem(i, 2, QTableWidgetItem(p.get('nombre', '')))
            cat_item = QTableWidgetItem(p.get('categoria', '') or 'Sin categoría')
            cat_item.setForeground(QColor("#64748b"))
            self.tabla.setItem(i, 3, cat_item)
            precio = p.get('precio', 0) or 0
            it_p = QTableWidgetItem(f"${precio:,.2f}")
            it_p.setForeground(QColor("#0284c7"))
            self.tabla.setItem(i, 4, it_p)
            self.tabla.setItem(i, 5, QTableWidgetItem(""))
            self.tabla.setItem(i, 6, QTableWidgetItem(""))
        self._actualizar_contador()

    def _seleccionar_todo(self):
        for i in range(self.tabla.rowCount()):
            self.tabla.item(i, 0).setCheckState(Qt.Checked)
        self._actualizar_contador()

    def _deseleccionar_todo(self):
        for i in range(self.tabla.rowCount()):
            self.tabla.item(i, 0).setCheckState(Qt.Unchecked)
        self._actualizar_contador()

    def _actualizar_contador(self):
        sel = sum(1 for i in range(self.tabla.rowCount()) if self.tabla.item(i, 0) and self.tabla.item(i, 0).checkState() == Qt.Checked)
        self.lbl_sel.setText(f"{sel} producto(s) seleccionado(s)")

    def _calcular_nuevo_precio(self, precio_actual, tipo, valor):
        if tipo == "% Aumento":
            return precio_actual * (1 + valor / 100)
        elif tipo == "% Descuento":
            return precio_actual * (1 - valor / 100)
        elif tipo == "Precio fijo":
            return valor
        elif tipo == "$ Aumento":
            return precio_actual + valor
        elif tipo == "$ Descuento":
            return max(0, precio_actual - valor)
        return precio_actual

    def _preview_ajuste(self):
        tipo = self.cmb_tipo.currentText()
        valor = self.spin_valor.value()
        for i in range(self.tabla.rowCount()):
            chk = self.tabla.item(i, 0)
            precio_item = self.tabla.item(i, 4)
            if not chk or not precio_item:
                continue
            precio_str = precio_item.text().replace("$", "").replace(",", "").strip()
            try:
                precio = float(precio_str)
            except:
                continue
            if chk.checkState() == Qt.Checked:
                nuevo = self._calcular_nuevo_precio(precio, tipo, valor)
                diferencia = nuevo - precio
                it_n = QTableWidgetItem(f"${nuevo:,.2f}")
                it_n.setForeground(QColor("#16a34a"))
                self.tabla.setItem(i, 5, it_n)
                it_d = QTableWidgetItem(f"+${diferencia:,.2f}" if diferencia >= 0 else f"-${abs(diferencia):,.2f}")
                it_d.setForeground(QColor("#16a34a" if diferencia >= 0 else "#dc2626"))
                self.tabla.setItem(i, 6, it_d)
            else:
                self.tabla.setItem(i, 5, QTableWidgetItem(""))
                self.tabla.setItem(i, 6, QTableWidgetItem(""))
        self._actualizar_contador()

    def _confirmar(self):
        tipo = self.cmb_tipo.currentText()
        valor = self.spin_valor.value()
        cambios = []
        for i in range(self.tabla.rowCount()):
            chk = self.tabla.item(i, 0)
            if chk and chk.checkState() == Qt.Checked:
                pid = chk.data(Qt.UserRole)
                precio_str = (self.tabla.item(i, 4) or QTableWidgetItem("0")).text().replace("$", "").replace(",", "").strip()
                try:
                    precio = float(precio_str)
                    nuevo = self._calcular_nuevo_precio(precio, tipo, valor)
                    cambios.append((round(nuevo, 2), pid))
                except:
                    pass

        if not cambios:
            QMessageBox.warning(self, "Sin selección", "Seleccioná al menos un producto.")
            return

        r = QMessageBox.question(self, "Confirmar cambio masivo",
            f"Se actualizarán {len(cambios)} precios con '{tipo}' de {valor}.\n¿Confirmar?",
            QMessageBox.Yes | QMessageBox.No)
        if r != QMessageBox.Yes:
            return

        ok = 0
        for nuevo_precio, pid in cambios:
            try:
                db_manager.execute_query("UPDATE productos SET precio=? WHERE id=?", (nuevo_precio, pid))
                ok += 1
            except:
                pass

        QMessageBox.information(self, "✅ Listo", f"Se actualizaron {ok} productos correctamente.")
        self.cargar_datos()
