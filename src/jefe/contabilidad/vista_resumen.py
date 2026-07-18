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
        title_lbl = QLabel("📈  Dashboard Financiero (CFO)")
        title_lbl.setStyleSheet(f"font-size: 24px; font-weight: 800; color: {PAL['primary']}; background: transparent; border: none;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        self._btn_resumen_reload = btn_primary("🔄 Actualizar Datos")
        self._btn_resumen_reload.clicked.connect(self._load_resumen)
        hdr.addWidget(self._btn_resumen_reload)
        lay.addLayout(hdr)
        
        lay.addSpacing(15)

        # KPIs row (4 columns)
        self._kpi_layout = QHBoxLayout()
        self._kpi_layout.setSpacing(15)
        lay.addLayout(self._kpi_layout)
        
        lay.addSpacing(20)

        # ERP 3-Pillar Row
        mid_lay = QHBoxLayout()
        mid_lay.setSpacing(20)
        
        # 1. P&L (Estado de Resultados)
        pnl_card = QFrame()
        pnl_card.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border-radius: 16px; border: 1px solid {PAL['border']}; }}")
        pnl_lay = QVBoxLayout(pnl_card)
        pnl_lay.setContentsMargins(20, 20, 20, 20)
        pnl_lay.setSpacing(10)
        
        lbl_pnl = QLabel("📊 Estado de Resultados (P&L)")
        lbl_pnl.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PAL['text']}; border: none; background: transparent;")
        pnl_lay.addWidget(lbl_pnl)
        
        self._pnl_ing = self._build_pnl_row("Ingresos Operativos", "$ 0.00", PAL['success'])
        pnl_lay.addWidget(self._pnl_ing)
        self._pnl_cogs = self._build_pnl_row("(-) Costo Mercadería", "$ 0.00", PAL['danger'])
        pnl_lay.addWidget(self._pnl_cogs)
        self._pnl_mg = self._build_pnl_row("(=) MARGEN BRUTO", "$ 0.00", PAL['primary'], bold=True)
        pnl_lay.addWidget(self._pnl_mg)
        
        div1 = QFrame(); div1.setFixedHeight(1); div1.setStyleSheet(f"background: {PAL['border']}; border: none;")
        pnl_lay.addWidget(div1)
        
        self._pnl_opex_f = self._build_pnl_row("(-) OPEX Fijos", "$ 0.00", PAL['warning'])
        pnl_lay.addWidget(self._pnl_opex_f)
        self._pnl_opex_v = self._build_pnl_row("(-) OPEX Varios", "$ 0.00", PAL['warning'])
        pnl_lay.addWidget(self._pnl_opex_v)
        
        div2 = QFrame(); div2.setFixedHeight(1); div2.setStyleSheet(f"background: {PAL['border']}; border: none;")
        pnl_lay.addWidget(div2)
        
        self._pnl_ebitda = self._build_pnl_row("(=) GANANCIA NETA", "$ 0.00", PAL['success'], bold=True, is_total=True)
        pnl_lay.addWidget(self._pnl_ebitda)
        pnl_lay.addStretch()
        mid_lay.addWidget(pnl_card, 1)

        # 2. Cash Flow (Flujo de Efectivo)
        cf_card = QFrame()
        cf_card.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border-radius: 16px; border: 1px solid {PAL['border']}; }}")
        cf_lay = QVBoxLayout(cf_card)
        cf_lay.setContentsMargins(20, 20, 20, 20)
        cf_lay.setSpacing(10)
        
        lbl_cf = QLabel("💸 Flujo de Efectivo (Cash Flow)")
        lbl_cf.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PAL['text']}; border: none; background: transparent;")
        cf_lay.addWidget(lbl_cf)
        
        self._cf_in = self._build_pnl_row("Entradas (Ventas)", "$ 0.00", PAL['success'])
        cf_lay.addWidget(self._cf_in)
        self._cf_out_op = self._build_pnl_row("(-) Salidas Operativas", "$ 0.00", PAL['danger'])
        cf_lay.addWidget(self._cf_out_op)
        self._cf_out_fin = self._build_pnl_row("(-) Salidas Financieras", "$ 0.00", PAL['warning'])
        cf_lay.addWidget(self._cf_out_fin)
        
        div3 = QFrame(); div3.setFixedHeight(1); div3.setStyleSheet(f"background: {PAL['border']}; border: none;")
        cf_lay.addWidget(div3)
        
        self._cf_net = self._build_pnl_row("(=) FLUJO NETO", "$ 0.00", PAL['primary'], bold=True, is_total=True)
        cf_lay.addWidget(self._cf_net)
        cf_lay.addStretch()
        mid_lay.addWidget(cf_card, 1)

        # 3. Balance General Summary
        bs_card = QFrame()
        bs_card.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border-radius: 16px; border: 1px solid {PAL['border']}; }}")
        bs_lay = QVBoxLayout(bs_card)
        bs_lay.setContentsMargins(20, 20, 20, 20)
        bs_lay.setSpacing(10)
        
        lbl_bs = QLabel("🏛️ Resumen de Balance")
        lbl_bs.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {PAL['text']}; border: none; background: transparent;")
        bs_lay.addWidget(lbl_bs)
        
        self._bs_inv = self._build_pnl_row("Activos: Inversiones", "$ 0.00", PAL['success'])
        bs_lay.addWidget(self._bs_inv)
        self._bs_liq = self._build_pnl_row("Activos: Liquidez Mes", "$ 0.00", PAL['primary'])
        bs_lay.addWidget(self._bs_liq)
        
        div4 = QFrame(); div4.setFixedHeight(1); div4.setStyleSheet(f"background: {PAL['border']}; border: none;")
        bs_lay.addWidget(div4)
        
        self._bs_liab = self._build_pnl_row("(-) Pasivos: Deuda Total", "$ 0.00", PAL['danger'])
        bs_lay.addWidget(self._bs_liab)
        
        div5 = QFrame(); div5.setFixedHeight(1); div5.setStyleSheet(f"background: {PAL['border']}; border: none;")
        bs_lay.addWidget(div5)
        
        self._bs_equity = self._build_pnl_row("(=) SALUD FINANCIERA", "$ 0.00", PAL['success'], bold=True, is_total=True)
        bs_lay.addWidget(self._bs_equity)
        bs_lay.addStretch()
        mid_lay.addWidget(bs_card, 1)
        
        lay.addLayout(mid_lay)
        lay.addSpacing(20)

        # Bottom: Historial
        lay.addWidget(section_title("🕒  Últimos Movimientos (Flujo de Caja General)"))
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
        lbl.setStyleSheet(lbl.styleSheet().replace(lbl.styleSheet().split("color: ")[1].split(";")[0], color))

    def _load_resumen(self):
        if not self._db: return
        try:
            stats = self._db.get_stats(self._mes, self._año)
            
            # --- P&L (Estado de Resultados) ---
            ing = stats.get("total_income", 0.0) or 0.0
            total_gas = stats.get("total_expenses", 0.0) or 0.0
            
            cats = stats.get("categories", []) or []
            costo_mercaderia = 0.0
            for cat, amount in cats:
                if cat in ("Mercadería", "Mercadería / Stock", "Proveedor", "Mercaderia"):
                    costo_mercaderia += amount
                    
            gastos_fijos = stats.get("fixed_expenses", 0.0) or 0.0
            gastos_varios = total_gas - costo_mercaderia - gastos_fijos
            if gastos_varios < 0: gastos_varios = 0.0
            
            margen_bruto = ing - costo_mercaderia
            ganancia_neta = margen_bruto - gastos_fijos - gastos_varios
            
            self._update_pnl_row(self._pnl_ing, f"$ {ing:,.2f}", PAL["success"])
            self._update_pnl_row(self._pnl_cogs, f"$ {costo_mercaderia:,.2f}", PAL["danger"])
            self._update_pnl_row(self._pnl_mg, f"$ {margen_bruto:,.2f}", PAL["primary"] if margen_bruto >= 0 else PAL["danger"])
            self._update_pnl_row(self._pnl_opex_f, f"$ {gastos_fijos:,.2f}", PAL["warning"])
            self._update_pnl_row(self._pnl_opex_v, f"$ {gastos_varios:,.2f}", PAL["warning"])
            self._update_pnl_row(self._pnl_ebitda, f"$ {ganancia_neta:,.2f}", PAL["success"] if ganancia_neta >= 0 else PAL["danger"])

            # --- Cash Flow (Flujo de Efectivo) ---
            fin_out = stats.get("financial_expenses", 0.0) or 0.0
            flujo_neto = ing - total_gas - fin_out
            
            self._update_pnl_row(self._cf_in, f"$ {ing:,.2f}", PAL["success"])
            self._update_pnl_row(self._cf_out_op, f"$ {total_gas:,.2f}", PAL["danger"])
            self._update_pnl_row(self._cf_out_fin, f"$ {fin_out:,.2f}", PAL["warning"])
            self._update_pnl_row(self._cf_net, f"$ {flujo_neto:,.2f}", PAL["primary"] if flujo_neto >= 0 else PAL["danger"])

            # --- Balance General Summary ---
            inv_bal = stats.get("investments_balance", 0.0) or 0.0
            liq_mes = flujo_neto
            liab = sum(stats.get("balances", {}).values())
            salud = inv_bal + liq_mes - liab
            
            self._update_pnl_row(self._bs_inv, f"$ {inv_bal:,.2f}", PAL["success"])
            self._update_pnl_row(self._bs_liq, f"$ {liq_mes:,.2f}", PAL["primary"] if liq_mes >= 0 else PAL["warning"])
            self._update_pnl_row(self._bs_liab, f"$ {liab:,.2f}", PAL["danger"])
            self._update_pnl_row(self._bs_equity, f"$ {salud:,.2f}", PAL["success"] if salud >= 0 else PAL["danger"])

            # --- KPIs ---
            for i in reversed(range(self._kpi_layout.count())):
                item = self._kpi_layout.takeAt(i)
                if item.widget(): item.widget().deleteLater()

            kpis = [
                ("INGRESOS MES",    f"${ing:,.0f}",   PAL["success"], "Ventas y Facturación"),
                ("OPEX (GASTOS)",   f"${total_gas:,.0f}", PAL["warning"], "Gastos Operativos"),
                ("GANANCIA NETA",   f"${ganancia_neta:,.0f}", PAL["primary"] if ganancia_neta >= 0 else PAL["danger"], "Bolsillo"),
                ("FLUJO NETO",      f"${flujo_neto:,.0f}", PAL["success"] if flujo_neto >= 0 else PAL["danger"], "Caja Real"),
            ]
            
            for t, v, c, s in kpis:
                card = self._create_kpi_pro(t, v, c, s)
                self._kpi_layout.addWidget(card)

            # --- Últimos Movimientos ---
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
        lbl_v.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 900; background: transparent; border: none;")
        l.addWidget(lbl_v)
        
        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet(f"color: {PAL['text2']}; font-size: 13px; background: transparent; border: none;")
        l.addWidget(lbl_s)
        
        return w
