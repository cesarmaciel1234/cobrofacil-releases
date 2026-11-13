# dialogo_codigos_adicionales.py - Gestión de códigos de barras adicionales (1 a N).
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QComboBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from src.repositories.producto_repository import ProductoRepository
from src.utils.letra import fuente_id, fuente_nombre, fuente_numero


class DialogoCodigosAdicionales(QDialog):
    """
    Diálogo para ver, agregar y eliminar códigos de escaneo adicionales vinculados a un producto.
    Permite asociar DUN-14, códigos de bulto con factor multiplicador, o cambios de envase.
    """

    TIPOS_CODIGO = [
        ("DUN-14 / Bulto cerrado", "DUN"),
        ("Pack / Caja cerrada", "BULTO"),
        ("Packaging alternativo", "EAN"),
        ("Código de proveedor", "PROVEEDOR"),
        ("Balanza / PLU secundario", "BALANZA"),
    ]

    def __init__(self, producto_id, nombre_producto="", parent=None):
        super().__init__(parent)
        self.producto_id = producto_id
        self.nombre_producto = nombre_producto or f"Producto #{producto_id}"
        self.setWindowTitle(f"🔗 Códigos Adicionales — ID #{self.producto_id}")
        self.setMinimumSize(840, 540)
        self.resize(840, 540)
        self.setStyleSheet("background-color: white; font-family: 'Segoe UI', sans-serif;")
        self._setup_ui()
        self.cargar_codigos()

    def _setup_ui(self):
        dlg_lay = QVBoxLayout(self)
        dlg_lay.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self)
        container.setObjectName("DialogoCodigosContainer")
        container.setStyleSheet(
            "QFrame#DialogoCodigosContainer { background-color: white; border: 2px solid #3B82F6; border-radius: 12px; }"
        )
        dlg_lay.addWidget(container)

        lay = QVBoxLayout(container)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(14)

        # Header
        h_lay = QHBoxLayout()
        v_titles = QVBoxLayout()
        v_titles.setSpacing(3)
        lbl_tit = QLabel("🔗 Códigos de Escaneo Adicionales")
        lbl_tit.setStyleSheet("font-size: 19px; font-weight: 900; color: #0F172A; border: none; background: transparent;")
        lbl_sub = QLabel(f"📦 {self.nombre_producto}")
        lbl_sub.setFont(fuente_nombre(12))
        lbl_sub.setStyleSheet("font-size: 13px; color: #334155; font-weight: bold; border: none; background: transparent;")
        v_titles.addWidget(lbl_tit)
        v_titles.addWidget(lbl_sub)
        h_lay.addLayout(v_titles)
        h_lay.addStretch()

        lbl_badge = QLabel(f"ID #{self.producto_id} (PERMANENTE)")
        lbl_badge.setStyleSheet(
            "background: #EFF6FF; color: #1D4ED8; font-weight: 900; font-family: 'Consolas', monospace; "
            "font-size: 13px; padding: 6px 14px; border-radius: 8px; border: 1px solid #BFDBFE;"
        )
        h_lay.addWidget(lbl_badge)
        lay.addLayout(h_lay)

        # Info corporativa
        lbl_info = QLabel("Permite escanear diferentes códigos (cajas, bultos x12, nuevos envases) para este mismo producto.")
        lbl_info.setStyleSheet("color: #475569; font-size: 12px; background: #F8FAFC; padding: 8px 12px; border-radius: 6px; border: 1px solid #E2E8F0;")
        lay.addWidget(lbl_info)

        # Tabla de códigos
        self.tabla = QTableWidget(self)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels(["Código de Barras / DUN", "Tipo", "Factor Un.", "Descripción / Nota", "Acción"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setShowGrid(True)
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 1px solid #CBD5E1; border-radius: 8px; gridline-color: #E2E8F0;
                background: white; font-size: 12px;
            }
            QTableWidget::item {
                padding: 6px 10px; border-bottom: 1px solid #F1F5F9;
            }
            QHeaderView::section {
                background: #F8FAFC; color: #334155; font-weight: bold; font-size: 12px;
                padding: 8px 10px; border: none; border-bottom: 2px solid #CBD5E1;
            }
        """)
        hh = self.tabla.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(0, 190)
        self.tabla.setColumnWidth(1, 140)
        self.tabla.setColumnWidth(2, 90)
        self.tabla.setColumnWidth(4, 75)
        lay.addWidget(self.tabla)

        # Formulario para agregar código
        frame_add = QFrame(container)
        frame_add.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px;")
        f_lay = QVBoxLayout(frame_add)
        f_lay.setContentsMargins(14, 12, 14, 12)
        f_lay.setSpacing(10)

        lbl_add_tit = QLabel("➕ Vincular nuevo código a este producto:")
        lbl_add_tit.setStyleSheet("font-weight: bold; font-size: 12px; color: #0F172A; border: none; background: transparent;")
        f_lay.addWidget(lbl_add_tit)

        h_inputs = QHBoxLayout()
        h_inputs.setSpacing(8)

        self.txt_nuevo_codigo = QLineEdit()
        self.txt_nuevo_codigo.setPlaceholderText("Código barras o DUN...")
        self.txt_nuevo_codigo.setMinimumWidth(180)
        self.txt_nuevo_codigo.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 10px; font-family: 'Consolas', monospace; font-size: 12px; font-weight: bold;")
        self.txt_nuevo_codigo.returnPressed.connect(self._agregar_codigo)
        h_inputs.addWidget(self.txt_nuevo_codigo, 3)

        self.cmb_tipo = QComboBox()
        for label, val in self.TIPOS_CODIGO:
            self.cmb_tipo.addItem(label, val)
        self.cmb_tipo.setMinimumWidth(150)
        self.cmb_tipo.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 8px; font-size: 11px;")
        h_inputs.addWidget(self.cmb_tipo, 2)

        self.txt_factor = QLineEdit("1.0")
        self.txt_factor.setToolTip("Unidades que descuenta al escanear (ej: 12 para caja de 12)")
        self.txt_factor.setPlaceholderText("1.0")
        self.txt_factor.setFixedWidth(65)
        self.txt_factor.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 6px; font-family: 'Consolas', monospace; font-size: 12px; font-weight: bold; text-align: center;")
        self.txt_factor.returnPressed.connect(self._agregar_codigo)
        h_inputs.addWidget(self.txt_factor, 1)

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Nota (ej. Caja x12)...")
        self.txt_desc.setMinimumWidth(150)
        self.txt_desc.setStyleSheet("background: white; border: 1px solid #CBD5E1; border-radius: 6px; padding: 8px 10px; font-size: 11px;")
        self.txt_desc.returnPressed.connect(self._agregar_codigo)
        h_inputs.addWidget(self.txt_desc, 3)

        btn_agregar = QPushButton("➕ Agregar")
        btn_agregar.setMinimumWidth(90)
        btn_agregar.setAutoDefault(False)
        btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_agregar.setStyleSheet(
            "QPushButton { background: #2563EB; color: white; font-weight: bold; font-size: 12px; "
            "padding: 8px 14px; border-radius: 6px; border: none; } "
            "QPushButton:hover { background: #1D4ED8; }"
        )
        btn_agregar.clicked.connect(self._agregar_codigo)
        h_inputs.addWidget(btn_agregar)

        f_lay.addLayout(h_inputs)
        lay.addWidget(frame_add)

        # Botón Cerrar
        h_foot = QHBoxLayout()
        h_foot.addStretch()
        btn_cerrar = QPushButton("Listo / Cerrar")
        btn_cerrar.setAutoDefault(False)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet(
            "QPushButton { background: white; color: #334155; font-weight: bold; font-size: 12px; "
            "padding: 8px 20px; border-radius: 6px; border: 1px solid #CBD5E1; } "
            "QPushButton:hover { background: #F1F5F9; }"
        )
        btn_cerrar.clicked.connect(self.accept)
        h_foot.addWidget(btn_cerrar)
        lay.addLayout(h_foot)

    def cargar_codigos(self):
        """Carga la lista de códigos adicionales de este producto en la tabla."""
        codigos = ProductoRepository.obtener_codigos_adicionales(self.producto_id)
        self.tabla.setRowCount(len(codigos))
        f_id = fuente_id(10)
        f_nom = fuente_nombre(11)
        f_num = fuente_numero(11)

        for i, row in enumerate(codigos):
            reg_id = row.get("id")
            cod_txt = str(row.get("codigo") or "")
            tipo_txt = str(row.get("tipo") or "EAN")
            factor = float(row.get("factor_unidades") or 1.0)
            desc_txt = str(row.get("descripcion") or "")

            it_cod = QTableWidgetItem(cod_txt)
            it_cod.setFont(f_id)
            it_cod.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.tabla.setItem(i, 0, it_cod)

            it_tipo = QTableWidgetItem(tipo_txt)
            it_tipo.setFont(f_nom)
            it_tipo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 1, it_tipo)

            factor_str = f"{int(factor)}x" if factor == int(factor) else f"{factor:.2f}x"
            it_fac = QTableWidgetItem(factor_str)
            it_fac.setFont(f_num)
            it_fac.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla.setItem(i, 2, it_fac)

            it_desc = QTableWidgetItem(desc_txt or "—")
            it_desc.setFont(f_nom)
            it_desc.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.tabla.setItem(i, 3, it_desc)

            btn_del = QPushButton("🗑")
            btn_del.setToolTip("Eliminar este código adicional")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setStyleSheet(
                "QPushButton { background: transparent; color: #DC2626; font-size: 13px; border: none; font-weight: bold; } "
                "QPushButton:hover { background: #FEE2E2; border-radius: 4px; }"
            )
            btn_del.clicked.connect(lambda _, rid=reg_id, c=cod_txt: self._eliminar_codigo(rid, c))
            self.tabla.setCellWidget(i, 4, btn_del)

    def _agregar_codigo(self):
        cod = self.txt_nuevo_codigo.text().strip()
        if not cod:
            QMessageBox.warning(self, "Código Requerido", "Por favor ingresá un código de barras.")
            self.txt_nuevo_codigo.setFocus()
            return

        tipo = self.cmb_tipo.currentData() or "EAN"
        try:
            factor = float(self.txt_factor.text().replace(",", "."))
            if factor <= 0:
                factor = 1.0
        except ValueError:
            factor = 1.0

        desc = self.txt_desc.text().strip()

        ok, msg = ProductoRepository.agregar_codigo_adicional(
            self.producto_id, cod, tipo=tipo, factor_unidades=factor, descripcion=desc
        )
        if not ok:
            QMessageBox.warning(self, "No se pudo agregar", msg)
            return

        self.txt_nuevo_codigo.clear()
        self.txt_desc.clear()
        self.txt_factor.setText("1.0")
        self.cargar_codigos()
        self.txt_nuevo_codigo.setFocus()

    def _eliminar_codigo(self, reg_id, codigo):
        if QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Seguro que querés quitar el código {codigo} de este producto?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            ProductoRepository.eliminar_codigo_adicional(reg_id)
            self.cargar_codigos()
