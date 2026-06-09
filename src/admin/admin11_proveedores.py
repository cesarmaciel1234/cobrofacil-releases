"""
admin11_proveedores.py — Gestión de Compras y Proveedores
TPV Pro 2026 · Cobro Fácil POS

Diseño enterprise sincronizado con Admin0Dashboard:
- Misma navbar, mismos KPI cards, misma tabla style
- Para el perfil Admin: acceso completo
- Para el perfil Jefe: se abre desde el ERP (JefeContabilidad, tab Proveedores)
  por lo que este módulo es usado solo por el admin con funciones de compras/órdenes
"""

import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QFormLayout, QDialog, QMessageBox,
    QScrollArea, QGridLayout, QGraphicsDropShadowEffect, QAbstractItemView,
    QDateEdit, QDoubleSpinBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QColor, QFont

from src.utils.theme_manager import theme_manager

try:
    from src.base_de_datos.database import db_manager
except ImportError:
    from database import db_manager

# ── Paleta sincronizada con el admin ─────────────────────────────────────────
_P = {
    "primary":   "#6366F1",
    "success":   "#10B981",
    "danger":    "#EF4444",
    "warning":   "#F59E0B",
    "info":      "#0EA5E9",
    "surface":   "#FFFFFF",
    "surface2":  "#F8FAFC",
    "border":    "#E2E8F0",
    "border2":   "#CBD5E1",
    "text":      "#0F172A",
    "text2":     "#475569",
    "text3":     "#94A3B8",
}

# ─────────────────────────────────────────────────────────────────────────────
#  KPI Card — mismo estilo que el resto del sistema
# ─────────────────────────────────────────────────────────────────────────────
def _kpi(title, value, color):
    card = QFrame()
    card.setObjectName("KpiProv")
    card.setStyleSheet(f"""
        QFrame#KpiProv {{
            background: {_P['surface']};
            border: 1px solid {_P['border']};
            border-left: 4px solid {color};
            border-radius: 12px;
        }}
    """)
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(12); sh.setOffset(0, 3); sh.setColor(QColor(0, 0, 0, 18))
    card.setGraphicsEffect(sh)

    lay = QVBoxLayout(card)
    lay.setContentsMargins(18, 14, 18, 14)
    lay.setSpacing(4)

    lt = QLabel(title.upper())
    lt.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {_P['text3']};"
                     " letter-spacing: 1px; background: transparent; border: none;")
    lay.addWidget(lt)

    lv = QLabel(value)
    lv.setObjectName("KpiVal")
    lv.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {_P['text']};"
                     " background: transparent; border: none;")
    lay.addWidget(lv)
    card._lv = lv
    return card


# ─────────────────────────────────────────────────────────────────────────────
#  MÓDULO PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
class Admin11Proveedores(QWidget):
    request_dashboard = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._setup_db()
        self._build_ui()
        self.cargar_datos()

    # ── Garantizar columna status ─────────────────────────────────────────────
    def _setup_db(self):
        try:
            if getattr(db_manager, "db_engine_type", "sqlite") == "mariadb":
                res = db_manager.execute_query("SHOW COLUMNS FROM gastos")
                cols = [c[0] for c in res] if res else []
            else:
                res = db_manager.execute_query("PRAGMA table_info(gastos)")
                cols = [c[1] for c in res] if res else []
            if "status" not in cols:
                db_manager.execute_non_query(
                    "ALTER TABLE gastos ADD COLUMN status TEXT DEFAULT 'Pagado'")
        except Exception:
            pass

    # ── UI ───────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── NAVBAR ───────────────────────────────────────────────────────────
        nav = QFrame()
        nav.setObjectName("ProvNav")
        nav.setFixedHeight(60)
        nav.setStyleSheet(f"""
            QFrame#ProvNav {{
                background: {theme_manager.get_color('nav_bg')};
                border-bottom: 1px solid {theme_manager.get_color('nav_border')};
            }}
        """)
        nl = QHBoxLayout(nav)
        nl.setContentsMargins(24, 0, 24, 0)
        nl.setSpacing(14)

        btn_back = QPushButton("← Volver")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setFixedHeight(34)
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: {_P['surface2']}; color: {_P['text2']};
                border: 1px solid {_P['border']}; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
            }}
            QPushButton:hover {{ background: {_P['border2']}; color: {_P['text']}; }}
        """)
        btn_back.clicked.connect(self.request_dashboard.emit)
        nl.addWidget(btn_back)

        sep = QFrame(); sep.setFixedSize(1, 28)
        sep.setStyleSheet(f"background: {_P['border']};")
        nl.addWidget(sep)

        lbl_title = QLabel("🚚  Compras y Proveedores")
        lbl_title.setStyleSheet(
            f"font-size: 15px; font-weight: 900; color: {_P['text']};"
            " background: transparent; border: none;")
        nl.addWidget(lbl_title)
        nl.addStretch()

        btn_new = QPushButton("＋  Nueva Orden de Compra")
        btn_new.setCursor(Qt.PointingHandCursor)
        btn_new.setFixedHeight(36)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background: {_P['primary']}; color: #fff;
                border: none; border-radius: 8px;
                padding: 0 20px; font-weight: 700; font-size: 12px;
            }}
            QPushButton:hover {{ background: #4F46E5; }}
            QPushButton:pressed {{ background: #4338CA; }}
        """)
        btn_new.clicked.connect(self._nueva_orden)
        nl.addWidget(btn_new)

        root.addWidget(nav)

        # ── CONTENIDO con scroll ──────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ background: {_P['surface2']}; border: none; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background: {_P['surface2']};")
        il = QVBoxLayout(inner)
        il.setContentsMargins(32, 28, 32, 32)
        il.setSpacing(24)

        # ── KPIs ─────────────────────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        self._kpi_mes    = _kpi("Compras del Mes",    "$ 0,00", _P["primary"])
        self._kpi_pend   = _kpi("Pendientes de Pago", "$ 0,00", _P["danger"])
        self._kpi_prov   = _kpi("Proveedores Activos","0",      _P["info"])
        self._kpi_pagado = _kpi("Total Pagado",        "$ 0,00", _P["success"])
        for k in [self._kpi_mes, self._kpi_pend, self._kpi_prov, self._kpi_pagado]:
            kpi_row.addWidget(k)
        il.addLayout(kpi_row)

        # ── TABLA ────────────────────────────────────────────────────────────
        lbl_sec = QLabel("ÓRDENES DE COMPRA Y PROVEEDORES")
        lbl_sec.setStyleSheet(
            f"font-size: 10px; font-weight: 900; letter-spacing: 2px;"
            f" color: {_P['text3']}; background: transparent; border: none;")
        il.addWidget(lbl_sec)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Proveedor", "Mercadería / Detalle", "Monto Total", "Estado", "Registrado por", "Acción"])
        self.tabla.setStyleSheet(f"""
            QTableWidget {{
                background: {_P['surface']};
                border: 1px solid {_P['border']};
                border-radius: 12px;
                gridline-color: {_P['surface2']};
                font-size: 12px; color: {_P['text']};
                alternate-background-color: {_P['surface2']};
                selection-background-color: {_P['primary']}18;
                selection-color: {_P['text']};
            }}
            QTableWidget::item {{ padding: 10px 12px; border: none; }}
            QTableWidget::item:hover {{ background: {_P['surface2']}; }}
            QHeaderView::section {{
                background: {_P['surface2']};
                color: {_P['primary']};
                font-weight: 900; font-size: 11px;
                padding: 10px 12px; border: none;
                border-bottom: 2px solid {_P['border']};
                letter-spacing: 0.5px;
            }}
            QScrollBar:vertical {{ background: {_P['surface2']}; width: 7px; border-radius: 4px; }}
            QScrollBar::handle:vertical {{ background: {_P['border2']}; border-radius: 4px; }}
        """)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectRows)

        sh_tbl = QGraphicsDropShadowEffect()
        sh_tbl.setBlurRadius(16); sh_tbl.setOffset(0, 4); sh_tbl.setColor(QColor(0, 0, 0, 20))
        self.tabla.setGraphicsEffect(sh_tbl)

        il.addWidget(self.tabla)
        scroll.setWidget(inner)
        root.addWidget(scroll)

    # ── Carga de datos ────────────────────────────────────────────────────────
    def cargar_datos(self):
        try:
            query = """
                SELECT fecha, descripcion, monto, status
                FROM gastos
                WHERE categoria = 'Mercadería / Stock'
                ORDER BY fecha DESC
                LIMIT 100
            """
            res = db_manager.execute_query(query) or []

            self.tabla.setRowCount(0)
            total_mes = 0.0
            total_pend = 0.0
            total_pag  = 0.0
            proveedores_vistos = set()

            for r in res:
                row = self.tabla.rowCount()
                self.tabla.insertRow(row)

                fecha  = str(r["fecha"]  if isinstance(r, dict) else r[0])
                desc   = str(r["descripcion"] if isinstance(r, dict) else r[1])
                monto  = float(r["monto"] if isinstance(r, dict) else r[2])
                status = str(r["status"] if isinstance(r, dict) else (r[3] if len(r) > 3 else "Pagado"))

                # Extraer proveedor del campo descripción (formato: "Proveedor: detalle")
                if ": " in desc:
                    proveedor, detalle = desc.split(": ", 1)
                else:
                    proveedor, detalle = "General", desc

                proveedores_vistos.add(proveedor)
                total_mes += monto

                # Estado con color
                it_status = QTableWidgetItem(status)
                if status in ("Pendiente", "pending"):
                    it_status.setForeground(QColor(_P["danger"]))
                    it_status.setText("⏳ Pendiente")
                    total_pend += monto
                else:
                    it_status.setForeground(QColor(_P["success"]))
                    it_status.setText("✅ Pagado")
                    total_pag += monto

                vals = [fecha, proveedor, detalle, f"$ {monto:,.2f}", "", "admin"]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    it.setTextAlignment(Qt.AlignVCenter | (Qt.AlignRight if c == 3 else Qt.AlignLeft))
                    self.tabla.setItem(row, c, it)
                self.tabla.setItem(row, 4, it_status)

                # Botón marcar pagado
                if status in ("Pendiente", "pending"):
                    btn_pay = QPushButton("💳 Pagar")
                    btn_pay.setFixedSize(90, 28)
                    btn_pay.setCursor(Qt.PointingHandCursor)
                    btn_pay.setStyleSheet(f"""
                        QPushButton {{
                            background: {_P['success']}22; color: {_P['success']};
                            border: 1px solid {_P['success']}44; border-radius: 6px;
                            font-size: 11px; font-weight: 700;
                        }}
                        QPushButton:hover {{ background: {_P['success']}; color: #fff; }}
                    """)
                    btn_pay.clicked.connect(
                        lambda _, d=desc: self._marcar_pagado(d))
                    self.tabla.setCellWidget(row, 6, btn_pay)

            # Actualizar KPIs
            self._kpi_mes._lv.setText(f"$ {total_mes:,.2f}")
            self._kpi_pend._lv.setText(f"$ {total_pend:,.2f}")
            self._kpi_prov._lv.setText(str(len(proveedores_vistos)))
            self._kpi_pagado._lv.setText(f"$ {total_pag:,.2f}")

        except Exception as e:
            print(f"[Admin11Proveedores] Error cargando datos: {e}")

    def _marcar_pagado(self, descripcion):
        try:
            db_manager.execute_non_query(
                "UPDATE gastos SET status = 'Pagado' WHERE descripcion = ? AND status = 'Pendiente'",
                (descripcion,))
            self.cargar_datos()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    # ── Diálogo nueva orden ───────────────────────────────────────────────────
    def _nueva_orden(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Nueva Orden de Compra")
        dlg.setFixedWidth(440)
        dlg.setStyleSheet(f"""
            QDialog {{ background: {_P['surface']}; font-family: 'Segoe UI'; }}
            QLabel  {{ color: {_P['text']}; font-weight: 600; font-size: 12px; }}
            QLineEdit, QComboBox, QDoubleSpinBox, QDateEdit {{
                background: {_P['surface2']}; border: 1px solid {_P['border']};
                border-radius: 8px; padding: 8px 12px; color: {_P['text']}; font-size: 12px;
            }}
            QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
                border: 2px solid {_P['primary']};
            }}
        """)

        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        lbl_hdr = QLabel("🚚  Nueva Orden de Compra")
        lbl_hdr.setStyleSheet(
            f"font-size: 16px; font-weight: 900; color: {_P['text']}; border: none; background: transparent;")
        lay.addWidget(lbl_hdr)

        form = QFormLayout(); form.setSpacing(10)

        cb_prov = QComboBox()
        cb_prov.setEditable(True)
        cb_prov.addItems(["Systel S.A.", "Distribuidora General", "Frigorífico Central",
                          "Proveedor Local", "Importadora", "Otro"])
        form.addRow("Proveedor:", cb_prov)

        txt_desc = QLineEdit(); txt_desc.setPlaceholderText("Detalle de la mercadería...")
        form.addRow("Detalle:", txt_desc)

        spin_monto = QDoubleSpinBox()
        spin_monto.setRange(0, 9_999_999); spin_monto.setDecimals(2); spin_monto.setPrefix("$ ")
        form.addRow("Monto Total:", spin_monto)

        cb_status = QComboBox()
        cb_status.addItems(["Pendiente", "Pagado"])
        form.addRow("Estado:", cb_status)

        dt_fecha = QDateEdit(QDate.currentDate())
        dt_fecha.setCalendarPopup(True)
        dt_fecha.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha:", dt_fecha)

        lay.addLayout(form)

        # Botones
        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {_P['surface2']}; color: {_P['text2']};
                border: 1px solid {_P['border']}; border-radius: 8px;
                padding: 9px 20px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {_P['border']}; }}
        """)
        btn_cancel.clicked.connect(dlg.reject)

        btn_save = QPushButton("Registrar Orden")
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {_P['primary']}; color: #fff;
                border: none; border-radius: 8px;
                padding: 9px 20px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #4F46E5; }}
        """)
        btn_save.clicked.connect(lambda: self._guardar_orden(
            dlg,
            cb_prov.currentText(),
            txt_desc.text(),
            spin_monto.value(),
            cb_status.currentText(),
            dt_fecha.date().toString("yyyy-MM-dd")
        ))

        btn_row.addWidget(btn_cancel)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        lay.addLayout(btn_row)
        dlg.exec_()

    def _guardar_orden(self, dlg, proveedor, detalle, monto, status, fecha):
        if monto <= 0:
            QMessageBox.warning(self, "Monto inválido", "Ingresá un monto mayor a cero.")
            return
        try:
            desc_completo = f"{proveedor}: {detalle}" if detalle else proveedor
            db_manager.execute_non_query(
                "INSERT INTO gastos (fecha, categoria, descripcion, monto, status, usuario)"
                " VALUES (?, 'Mercadería / Stock', ?, ?, ?, 'admin')",
                (fecha, desc_completo, monto, status))
            QMessageBox.information(self, "✅ Registrado",
                                    f"Orden de compra registrada.\nProveedor: {proveedor}")
            dlg.accept()
            self.cargar_datos()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # Compatibilidad con IA Boss
    def auto_import_ai(self, items):
        summary = "Pedido sugerido por IA: " + ", ".join(items)
        self._nueva_orden()
