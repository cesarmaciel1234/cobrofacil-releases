from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox,
    QFrame, QPushButton, QFormLayout, QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal


class CreadorPromociones(QWidget):
    """Reglas de promo + precio de lista. Costo/stock en Inventario. No imprime."""

    activar_promo = pyqtSignal(dict)
    quitar_promo = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.producto_id = None
        self._precio = 0.0
        self._costo = 0.0
        self._setup_ui()

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: #F8FAFC; }")

        self.panel = QFrame()
        self.panel.setObjectName("ControlCenter")
        self.panel.setStyleSheet("""
            QFrame#ControlCenter {
                background-color: #FFFFFF;
                border-left: 1px solid #E2E8F0;
            }
            QLabel { background: transparent; color: #334155; }
            QDoubleSpinBox {
                background-color: #F8FAFC;
                color: #0F172A;
                border: 1px solid #CBD5E1;
                border-radius: 8px;
                min-height: 36px;
                padding: 4px 8px;
                font-size: 14px;
            }
        """)
        lay = QVBoxLayout(self.panel)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        lbl_head = QLabel("REGLAS DE PROMOCIÓN")
        lbl_head.setStyleSheet(
            "color: #64748B; font-size: 12px; font-weight: 900; letter-spacing: 1px;"
        )
        lay.addWidget(lbl_head)

        self.lbl_prod_nombre = QLabel("Elegí un producto de la lista")
        self.lbl_prod_nombre.setStyleSheet(
            "color: #1D4ED8; font-size: 18px; font-weight: 900;"
        )
        self.lbl_prod_nombre.setWordWrap(True)
        lay.addWidget(self.lbl_prod_nombre)

        self.lbl_prod_detalles = QLabel("ID: —  ·  PLU: —")
        self.lbl_prod_detalles.setStyleSheet(
            "color: #64748B; font-size: 12px; font-weight: 700;"
        )
        lay.addWidget(self.lbl_prod_detalles)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #E2E8F0; border: none;")
        lay.addWidget(sep)

        form = QFormLayout()
        form.setSpacing(12)
        form.setContentsMargins(0, 8, 0, 8)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.sp_precio_lista = QDoubleSpinBox()
        self.sp_precio_lista.setRange(0, 9999999)
        self.sp_precio_lista.setDecimals(2)
        self.sp_precio_lista.setPrefix("$ ")

        self.sp_quick_cant_oferta = QDoubleSpinBox()
        self.sp_quick_cant_oferta.setRange(0, 99999)
        self.sp_quick_cant_oferta.setDecimals(2)

        self.sp_quick_precio_oferta = QDoubleSpinBox()
        self.sp_quick_precio_oferta.setRange(0, 9999999)
        self.sp_quick_precio_oferta.setDecimals(2)

        self.sp_quick_oferta_relampago = QDoubleSpinBox()
        self.sp_quick_oferta_relampago.setRange(0, 9999999)
        self.sp_quick_oferta_relampago.setDecimals(2)

        self.sp_limite_relampago = QDoubleSpinBox()
        self.sp_limite_relampago.setRange(0, 9999999)
        self.sp_limite_relampago.setDecimals(0)

        form.addRow(QLabel("Precio lista ($)"), self.sp_precio_lista)
        form.addRow(QLabel("Oferta desde (cant.)"), self.sp_quick_cant_oferta)
        form.addRow(QLabel("Precio oferta ($)"), self.sp_quick_precio_oferta)
        form.addRow(QLabel("Of. relámpago ($)"), self.sp_quick_oferta_relampago)
        form.addRow(QLabel("Límite (uds)"), self.sp_limite_relampago)
        self.lbl_cupo_relampago = QLabel("Cupo flash: —")
        self.lbl_cupo_relampago.setStyleSheet("color: #D97706; font-weight: 800;")
        form.addRow(QLabel(""), self.lbl_cupo_relampago)
        lay.addLayout(form)

        self.group_simulador = QFrame()
        self.group_simulador.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
            }
            QLabel { border: none; }
        """)
        lay_sim = QVBoxLayout(self.group_simulador)
        lay_sim.setContentsMargins(16, 14, 16, 14)
        lay_sim.setSpacing(8)

        lbl_sim_tit = QLabel("MARGEN DE LA PROMO")
        lbl_sim_tit.setStyleSheet(
            "color: #475569; font-weight: 900; font-size: 11px; letter-spacing: 1px;"
        )
        lay_sim.addWidget(lbl_sim_tit)

        self.lbl_margen_reg = QLabel("Margen lista: —")
        self.lbl_margen_reg.setStyleSheet("color: #64748B; font-size: 13px; font-weight: 700;")
        lay_sim.addWidget(self.lbl_margen_reg)

        self.lbl_margen_promo = QLabel("Margen promo: —")
        self.lbl_margen_promo.setStyleSheet("color: #059669; font-size: 16px; font-weight: 900;")
        lay_sim.addWidget(self.lbl_margen_promo)

        self.lbl_ahorro_total = QLabel("Ahorro cliente: —")
        self.lbl_ahorro_total.setStyleSheet("color: #D97706; font-size: 14px; font-weight: 800;")
        lay_sim.addWidget(self.lbl_ahorro_total)

        self.lbl_semaforo = QLabel("Elegí un producto")
        self.lbl_semaforo.setStyleSheet("color: #475569; font-size: 12px; font-weight: 800;")
        self.lbl_semaforo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_semaforo.setWordWrap(True)
        lay_sim.addWidget(self.lbl_semaforo)

        lay.addWidget(self.group_simulador)

        lay_btns = QHBoxLayout()
        lay_btns.setSpacing(10)
        self.btn_activar_promo = QPushButton("ACTIVAR PROMO")
        self.btn_activar_promo.setMinimumHeight(48)
        self.btn_activar_promo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_activar_promo.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: white; font-weight: 900; font-size: 13px;
                padding: 12px; border-radius: 10px; border: none;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        self.btn_activar_promo.clicked.connect(self._emit_activar_promo)

        self.btn_quitar_promo = QPushButton("QUITAR PROMO")
        self.btn_quitar_promo.setMinimumHeight(48)
        self.btn_quitar_promo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_quitar_promo.setStyleSheet("""
            QPushButton {
                color: #DC2626; background: #FFFFFF; font-weight: 800; font-size: 13px;
                padding: 12px; border-radius: 10px; border: 2px solid #FECACA;
            }
            QPushButton:hover { background-color: #FEE2E2; }
        """)
        self.btn_quitar_promo.clicked.connect(self._emit_quitar_promo)

        lay_btns.addWidget(self.btn_activar_promo)
        lay_btns.addWidget(self.btn_quitar_promo)
        lay.addLayout(lay_btns)
        lay.addStretch()

        self.scroll.setWidget(self.panel)
        root.addWidget(self.scroll)

        for sp in (
            self.sp_precio_lista, self.sp_quick_cant_oferta,
            self.sp_quick_precio_oferta, self.sp_quick_oferta_relampago,
        ):
            sp.valueChanged.connect(self._recargar_simulador)

        self.set_enabled(False)

    def aplicar_tema(self):
        pass

    def cargar_producto(self, p):
        if not p:
            self.producto_id = None
            self._precio = 0.0
            self._costo = 0.0
            self.lbl_prod_nombre.setText("Elegí un producto de la lista")
            self.lbl_prod_detalles.setText("ID: —  ·  PLU: —")
            self.sp_precio_lista.blockSignals(True)
            self.sp_precio_lista.setValue(0)
            self.sp_precio_lista.blockSignals(False)
            self.lbl_cupo_relampago.setText("Cupo flash: —")
            self.set_enabled(False)
            self._recargar_simulador()
            return

        def _num(key):
            try:
                v = p.get(key)
                if v is None or v == "":
                    return 0.0
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        self.producto_id = str(p.get("id") or "")
        self._precio = _num("precio")
        self._costo = _num("costo")
        self.lbl_prod_nombre.setText(str(p.get("nombre") or "Producto"))
        self.lbl_prod_detalles.setText(
            f"ID: {p.get('id')}  ·  PLU: {p.get('codigo') or 'Sin código'}"
        )

        for w in (
            self.sp_precio_lista, self.sp_quick_cant_oferta,
            self.sp_quick_precio_oferta, self.sp_quick_oferta_relampago,
            self.sp_limite_relampago,
        ):
            w.blockSignals(True)

        self.sp_precio_lista.setValue(self._precio)
        self.sp_quick_cant_oferta.setValue(_num("cant_oferta"))
        self.sp_quick_precio_oferta.setValue(_num("precio_oferta"))
        self.sp_quick_oferta_relampago.setValue(_num("precio_oferta_relampago"))
        self.sp_limite_relampago.setValue(_num("limite_oferta_relampago"))
        ventas = _num("ventas_oferta_relampago")
        limite = _num("limite_oferta_relampago")
        if _num("precio_oferta_relampago") > 0 and limite > 0:
            self.lbl_cupo_relampago.setText(
                f"Vendidos: {ventas:g} / {limite:g}"
                + ("  ·  AGOTADO" if ventas >= limite else "")
            )
        elif _num("precio_oferta_relampago") > 0:
            self.lbl_cupo_relampago.setText("Flash activo · sin tope (no se apaga solo)")
        else:
            self.lbl_cupo_relampago.setText("Cupo flash: —")

        for w in (
            self.sp_precio_lista, self.sp_quick_cant_oferta,
            self.sp_quick_precio_oferta, self.sp_quick_oferta_relampago,
            self.sp_limite_relampago,
        ):
            w.blockSignals(False)

        self.set_enabled(True)
        self._recargar_simulador()

    def set_enabled(self, val):
        for w in (
            self.sp_precio_lista, self.sp_quick_cant_oferta,
            self.sp_quick_precio_oferta, self.sp_quick_oferta_relampago,
            self.sp_limite_relampago, self.btn_activar_promo, self.btn_quitar_promo,
        ):
            w.setEnabled(bool(val))

    def _recargar_simulador(self):
        if not self.producto_id:
            self.lbl_margen_reg.setText("Margen lista: —")
            self.lbl_margen_promo.setText("Margen promo: —")
            self.lbl_ahorro_total.setText("Ahorro cliente: —")
            self.lbl_semaforo.setText("Elegí un producto")
            self.lbl_semaforo.setStyleSheet(
                "color: #475569; font-size: 12px; font-weight: 800; background: transparent;"
            )
            return

        costo = self._costo
        reg_precio = self.sp_precio_lista.value()
        self._precio = reg_precio
        promo_precio = self.sp_quick_precio_oferta.value()
        promo_cant = self.sp_quick_cant_oferta.value()

        if reg_precio > 0:
            margen_reg = ((reg_precio - costo) / reg_precio) * 100
            self.lbl_margen_reg.setText(f"Margen lista: {margen_reg:.1f}%")
        else:
            self.lbl_margen_reg.setText("Margen lista: 0.0%")

        if promo_precio > 0:
            margen_promo = ((promo_precio - costo) / promo_precio) * 100
            self.lbl_margen_promo.setText(f"Margen promo: {margen_promo:.1f}%")
            ahorro = max(0.0, reg_precio - promo_precio) * max(promo_cant, 1)
            self.lbl_ahorro_total.setText(f"Ahorro cliente: ${ahorro:,.2f}")

            if promo_precio <= costo:
                self.lbl_semaforo.setText("Pérdida: oferta bajo el costo")
                self.lbl_semaforo.setStyleSheet(
                    "font-size: 12px; font-weight: 900; background-color: #FEE2E2; "
                    "color: #B91C1C; border-radius: 6px; padding: 6px;"
                )
            elif margen_promo < 10.0:
                self.lbl_semaforo.setText("Margen bajo")
                self.lbl_semaforo.setStyleSheet(
                    "font-size: 12px; font-weight: 900; background-color: #FEF3C7; "
                    "color: #92400E; border-radius: 6px; padding: 6px;"
                )
            else:
                self.lbl_semaforo.setText("Promo con margen")
                self.lbl_semaforo.setStyleSheet(
                    "font-size: 12px; font-weight: 900; background-color: #DCFCE7; "
                    "color: #166534; border-radius: 6px; padding: 6px;"
                )
        else:
            self.lbl_margen_promo.setText("Margen promo: —")
            self.lbl_ahorro_total.setText("Ahorro cliente: —")
            self.lbl_semaforo.setText("Cargá un precio de oferta")
            self.lbl_semaforo.setStyleSheet(
                "font-size: 12px; font-weight: 800; background-color: #F1F5F9; "
                "color: #475569; border-radius: 6px; padding: 6px;"
            )

    def _emit_activar_promo(self):
        if not self.producto_id:
            return

        precio_reg = self.sp_precio_lista.value()
        self._precio = precio_reg
        p_of = self.sp_quick_precio_oferta.value()
        p_rel = self.sp_quick_oferta_relampago.value()

        if precio_reg <= 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "El precio de lista tiene que ser mayor a cero.")
            return

        if (p_of > 0 and p_of >= precio_reg) or (p_rel > 0 and p_rel >= precio_reg):
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, "Error",
                "El precio de oferta tiene que ser menor al precio de lista.",
            )
            return

        self.activar_promo.emit({
            "id": self.producto_id,
            "nombre": self.lbl_prod_nombre.text(),
            "cant_oferta": self.sp_quick_cant_oferta.value(),
            "precio_oferta": p_of,
            "precio_oferta_relampago": p_rel,
            "precio_oferta_promedio": 0,
            "limite_oferta_relampago": self.sp_limite_relampago.value(),
            "precio_regular": precio_reg,
        })

    def _emit_quitar_promo(self):
        if not self.producto_id:
            return
        self.quitar_promo.emit(self.producto_id)
