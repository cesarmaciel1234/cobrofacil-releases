from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaResumenMixin:
    def _build_tab_resumen(self):
        lay, _ = self._page()

        # Header
        hdr = QHBoxLayout()
        title_lbl = QLabel("📊  Dashboard Financiero (CFO)")
        title_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {PAL['primary']}; background: transparent; border: none;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        self._btn_resumen_reload = btn_primary("🔄 Actualizar Datos")
        self._btn_resumen_reload.clicked.connect(self._load_resumen)
        hdr.addWidget(self._btn_resumen_reload)
        lay.addLayout(hdr)
        
        # Spacer
        lay.addSpacing(15)

        # KPIs row (4 columns)
        self._kpi_layout = QHBoxLayout()
        self._kpi_layout.setSpacing(15)
        lay.addLayout(self._kpi_layout)
        
        lay.addSpacing(20)

        # P&L and Top Expenses Row
        mid_lay = QHBoxLayout()
        mid_lay.setSpacing(20)
        
        # Left: P&L (Estado de Resultados)
        pnl_card = QFrame()
        pnl_card.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border-radius: 16px; border: 1px solid {PAL['border']}; }}")
        pnl_lay = QVBoxLayout(pnl_card)
        pnl_lay.setContentsMargins(20, 20, 20, 20)
        pnl_lay.setSpacing(10)
        
        lbl_pnl_title = QLabel("📉 Estado de Resultados (P&L)")
        lbl_pnl_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PAL['text']}; border: none; background: transparent;")
        pnl_lay.addWidget(lbl_pnl_title)
        
        self._pnl_ingresos = self._build_pnl_row("Ingresos Operativos", "$ 0.00", PAL['success'])
        pnl_lay.addWidget(self._pnl_ingresos)
        
        self._pnl_costo_merc = self._build_pnl_row("(-) Costo Mercadería", "$ 0.00", PAL['danger'])
        pnl_lay.addWidget(self._pnl_costo_merc)
        
        self._pnl_margen_bruto = self._build_pnl_row("(=) MARGEN BRUTO", "$ 0.00", PAL['primary'], bold=True)
        pnl_lay.addWidget(self._pnl_margen_bruto)
        
        # Divisor
        div1 = QFrame(); div1.setFixedHeight(1); div1.setStyleSheet(f"background: {PAL['border']}; border: none;")
        pnl_lay.addWidget(div1)
        
        self._pnl_fijos = self._build_pnl_row("(-) Costos Fijos", "$ 0.00", PAL['warning'])
        pnl_lay.addWidget(self._pnl_fijos)
        
        self._pnl_vars = self._build_pnl_row("(-) Gastos Varios", "$ 0.00", PAL['warning'])
        pnl_lay.addWidget(self._pnl_vars)
        
        # Divisor
        div2 = QFrame(); div2.setFixedHeight(1); div2.setStyleSheet(f"background: {PAL['border']}; border: none;")
        pnl_lay.addWidget(div2)
        
        self._pnl_neta = self._build_pnl_row("(=) GANANCIA NETA", "$ 0.00", PAL['success'], bold=True, is_total=True)
        pnl_lay.addWidget(self._pnl_neta)
        
        pnl_lay.addStretch()
        mid_lay.addWidget(pnl_card, 1)
        
        # Right: Distribución de Gastos
        exp_card = QFrame()
        exp_card.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border-radius: 16px; border: 1px solid {PAL['border']}; }}")
        exp_lay = QVBoxLayout(exp_card)
        exp_lay.setContentsMargins(20, 20, 20, 20)
        exp_lay.setSpacing(15)
        
        lbl_exp_title = QLabel("📊 Distribución de Gastos")
        lbl_exp_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PAL['text']}; border: none; background: transparent;")
        exp_lay.addWidget(lbl_exp_title)
        
        self._exp_bars_layout = QVBoxLayout()
        self._exp_bars_layout.setSpacing(15)
        exp_lay.addLayout(self._exp_bars_layout)
        exp_lay.addStretch()
        
        mid_lay.addWidget(exp_card, 1)
        
        lay.addLayout(mid_lay)
        lay.addSpacing(20)

        # Bottom: Historial
        lay.addWidget(section_title("📋  Últimos Movimientos"))
        self._tbl_resumen = build_table(["Fecha", "Tipo", "Categoría", "Descripción", "Monto"])
        self._tbl_resumen.setMaximumHeight(250)
        lay.addWidget(self._tbl_resumen)
        lay.addStretch()

    def _build_pnl_row(self, title, value, color, bold=False, is_total=False):
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 5, 0, 5)
        lbl_t = QLabel(title)
        lbl_v = QLabel(value)
        
        font_size = "18px" if is_total else ("14px" if bold else "13px")
        weight = "bold" if bold or is_total else "normal"
        lbl_t.setStyleSheet(f"color: {PAL['text2']}; font-size: {font_size}; font-weight: {weight};")
        lbl_v.setStyleSheet(f"color: {color}; font-size: {font_size}; font-weight: {weight};")
        
        l.addWidget(lbl_t)
        l.addStretch()
        l.addWidget(lbl_v)
        return w

    def _update_pnl_row(self, widget, value_str, color):
        lbl = widget.layout().itemAt(2).widget()
        lbl.setText(value_str)
        lbl.setStyleSheet(lbl.styleSheet().replace(lbl.styleSheet().split('color: ')[1].split(';')[0], color))

    def _load_resumen(self):
        if not self._db: return
        try:
            stats = self._db.get_stats(self._mes, self._año)
            ing   = stats.get("total_income", 0.0) or 0.0
            total_gas = stats.get("total_expenses", 0.0) or 0.0
            
            cats = stats.get("categories", []) or []
            costo_mercaderia = 0.0
            gastos_fijos = stats.get("fixed_expenses", 0.0) or 0.0
            gastos_varios = 0.0
            
            other_cats = []
            for cat, amount in cats:
                if cat in ("Mercadería", "Mercadería / Stock", "Proveedor", "Mercaderia"):
                    costo_mercaderia += amount
                else:
                    other_cats.append((cat, amount))
            
            gastos_varios = total_gas - costo_mercaderia - gastos_fijos
            if gastos_varios < 0: gastos_varios = 0.0
            
            margen_bruto = ing - costo_mercaderia
            ganancia_neta = margen_bruto - gastos_fijos - gastos_varios
            
            self._update_pnl_row(self._pnl_ingresos, f"$ {ing:,.2f}", PAL['success'])
            self._update_pnl_row(self._pnl_costo_merc, f"$ {costo_mercaderia:,.2f}", PAL['danger'])
            self._update_pnl_row(self._pnl_margen_bruto, f"$ {margen_bruto:,.2f}", PAL['primary'] if margen_bruto >= 0 else PAL['danger'])
            self._update_pnl_row(self._pnl_fijos, f"$ {gastos_fijos:,.2f}", PAL['warning'])
            self._update_pnl_row(self._pnl_vars, f"$ {gastos_varios:,.2f}", PAL['warning'])
            self._update_pnl_row(self._pnl_neta, f"$ {ganancia_neta:,.2f}", PAL['success'] if ganancia_neta >= 0 else PAL['danger'])

            for i in reversed(range(self._kpi_layout.count())):
                item = self._kpi_layout.takeAt(i)
                if item.widget(): item.widget().deleteLater()

            bal_c = sum(stats.get("balances", {}).values())
            kpis = [
                ("INGRESOS MES",    f"${ing:,.0f}",   PAL["success"], "Ventas y Facturación"),
                ("EGRESOS MES",     f"${total_gas:,.0f}", PAL["danger"], "Todos los gastos"),
                ("GANANCIA NETA",   f"${ganancia_neta:,.0f}", PAL["primary"] if ganancia_neta >= 0 else PAL["danger"], "Bolsillo"),
                ("DEUDA FLOTANTE",  f"${bal_c:,.0f}", PAL["warning"], "A pagar (Cheques/Prov)"),
            ]
            
            for t, v, c, s in kpis:
                card = self._create_kpi_pro(t, v, c, s)
                self._kpi_layout.addWidget(card)

            for i in reversed(range(self._exp_bars_layout.count())):
                item = self._exp_bars_layout.takeAt(i)
                if item.widget(): item.widget().deleteLater()
                
            if total_gas > 0:
                colors = ['#ef4444', '#f97316', '#eab308', '#3b82f6', '#8b5cf6', '#ec4899', '#14b8a6']
                for i, (cat, amount) in enumerate(cats[:6]):
                    pct = (amount / total_gas) * 100
                    bar = self._create_expense_bar(cat, amount, pct, colors[i % len(colors)])
                    self._exp_bars_layout.addWidget(bar)
            else:
                lbl = QLabel("No hay gastos registrados en este período.")
                lbl.setStyleSheet(f"color: {PAL['text3']}; background: transparent; border: none;")
                self._exp_bars_layout.addWidget(lbl)

            movs = self._db.get_all_movements(self._mes, self._año)
            self._tbl_resumen.setRowCount(0)
            for row_data in (movs or [])[:50]:
                r = self._tbl_resumen.rowCount()
                self._tbl_resumen.insertRow(r)
                fecha = str(row_data[0]) if row_data[0] else ""
                tipo  = str(row_data[1]) if row_data[1] else ""
                cat   = str(row_data[2]) if row_data[2] else ""
                desc  = str(row_data[3]) if row_data[3] else ""
                monto = float(row_data[4]) if row_data[4] else 0.0
                vals  = [fecha, tipo, cat, desc, f"$ {monto:,.2f}"]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignVCenter | (Qt.AlignRight if c == 4 else Qt.AlignLeft))
                    if tipo == "INGRESO":
                        item.setForeground(QColor(PAL["success"]))
                    elif tipo == "EGRESO":
                        item.setForeground(QColor(PAL["danger"]))
                    self._tbl_resumen.setItem(r, c, item)
        except Exception as e:
            print(f"load_resumen: {e}")

    def _create_kpi_pro(self, title, value, color, subtitle):
        w = QFrame()
        w.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PAL['surface']}, stop:1 #1e293b);
                border-radius: 16px;
                border: 1px solid {PAL['border']};
                border-bottom: 4px solid {color};
            }}
        """)
        l = QVBoxLayout(w)
        l.setContentsMargins(20, 20, 20, 20)
        
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(f"color: {PAL['text3']}; font-weight: bold; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; background: transparent; border: none;")
        l.addWidget(lbl_t)
        
        lbl_v = QLabel(value)
        lbl_v.setStyleSheet(f"color: {color}; font-weight: 900; font-size: 28px; background: transparent; border: none;")
        l.addWidget(lbl_v)
        
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet(f"color: {PAL['text2']}; font-size: 13px; text-transform: uppercase; background: transparent; border: none;")
        l.addWidget(lbl_s)
        
        return w

    def _create_expense_bar(self, cat, amount, pct, color):
        w = QWidget()
        w.setStyleSheet("background: transparent; border: none;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(5)
        
        hl = QHBoxLayout()
        lbl_cat = QLabel(cat)
        lbl_cat.setStyleSheet(f"color: {PAL['text']}; font-weight: bold; font-size: 13px; background: transparent;")
        
        lbl_amt = QLabel(f"${amount:,.0f} ({pct:.1f}%)")
        lbl_amt.setStyleSheet(f"color: {PAL['text2']}; font-size: 12px; background: transparent;")
        
        hl.addWidget(lbl_cat)
        hl.addStretch()
        hl.addWidget(lbl_amt)
        l.addLayout(hl)
        
        pbar = QProgressBar()
        pbar.setFixedHeight(8)
        pbar.setTextVisible(False)
        pbar.setValue(int(pct))
        pbar.setStyleSheet(f"""
            QProgressBar {{
                background: {PAL['border']};
                border: none;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 4px;
            }}
        """)
        l.addWidget(pbar)
        
        return w

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — INGRESOS
    # ─────────────────────────────────────────────────────────────────────────
