import codecs
import re
import re

with codecs.open('src/jefe/jefe_contabilidad.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ---------------------------------------------------------
# 1. WOW UI FOR PROVEEDORES
# ---------------------------------------------------------
start_prov = content.find('    def _build_tab_proveedores(self):')
end_prov = content.find('    def _on_prov_type_change(self, text):')

wow_proveedores = """    def _build_tab_proveedores(self):
        lay, _ = self._page()
        lay.addWidget(section_title("🚚  Proveedores — Frigorífico y Carga Rápida"))

        # --- CONTENEDOR PRINCIPAL ---
        main_h = QHBoxLayout()
        main_h.setSpacing(20)

        # 1. PANEL IZQUIERDO: FORMULARIO DE CARGA WOW
        left_panel = QFrame()
        left_panel.setObjectName("Card")
        left_panel.setStyleSheet(f\"\"\"
            QFrame#Card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {PAL['surface']}, stop:1 #F8FAFC);
                border: 1px solid {PAL['border']};
                border-radius: 16px;
            }}
        \"\"\")
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setColor(QColor(0,0,0,30)); shadow.setOffset(0, 4)
        left_panel.setGraphicsEffect(shadow)
        
        fl = QGridLayout(left_panel)
        fl.setContentsMargins(25, 25, 25, 25); fl.setSpacing(15)

        title_lbl = QLabel("🧾 DATOS DEL REMITO")
        title_lbl.setStyleSheet(f"color: {PAL['primary']}; font-weight: 900; font-size: 14px; letter-spacing: 1px;")
        fl.addWidget(title_lbl, 0, 0, 1, 4)

        fl.addWidget(QLabel("Fecha:"), 1, 0)
        self._prov_date = date_field(); fl.addWidget(self._prov_date, 1, 1)

        fl.addWidget(QLabel("Proveedor:"), 1, 2)
        self._prov_nombre = input_field("Ej: Frigorífico Rioplatense"); fl.addWidget(self._prov_nombre, 1, 3)

        fl.addWidget(QLabel("Tropa/Lote:"), 2, 0)
        self._prov_tropa = input_field("Nro Tropa"); fl.addWidget(self._prov_tropa, 2, 1)

        fl.addWidget(QLabel("Mercadería:"), 2, 2)
        self._prov_type = QComboBox()
        self._prov_type.addItems(["Carne (Media Res)", "Cerdo", "Pollo", "Achuras", "Otro"])
        self._prov_type.setStyleSheet(f"background: {PAL['surface2']}; border: 1px solid {PAL['border']}; padding: 8px; border-radius: 6px; color: {PAL['text']}; font-weight: 800; font-size: 13px;")
        self._prov_type.currentTextChanged.connect(self._on_prov_type_change)
        fl.addWidget(self._prov_type, 2, 3)

        fl.addWidget(QLabel("Precio Unit.:"), 3, 0)
        self._prov_precio = input_field("$ Precio x Kg/Caja")
        self._prov_precio.setStyleSheet(f"background: #FEF3C7; border: 2px solid #F59E0B; padding: 10px; border-radius: 8px; color: #92400E; font-weight: bold; font-size: 14px;")
        self._prov_precio.textChanged.connect(self._update_prov_calc)
        fl.addWidget(self._prov_precio, 3, 1)

        self._lbl_carga = QLabel("⚡ CARGA RÁPIDA (PESO + ENTER):")
        self._lbl_carga.setStyleSheet("color: #EF4444; font-weight: 900; font-size: 11px;")
        fl.addWidget(self._lbl_carga, 3, 2)
        
        self._romaneo_input = input_field("Ej: 80.5 y Enter")
        self._romaneo_input.setStyleSheet(f"background: #ECFDF5; border: 2px solid #10B981; padding: 12px; border-radius: 8px; color: #065F46; font-weight: 900; font-size: 16px;")
        self._romaneo_input.returnPressed.connect(self._add_romaneo_item)
        fl.addWidget(self._romaneo_input, 3, 3)

        # Grilla de pesaje
        self._romaneo_table = build_table(["Nro", "Peso/Cant", "X"])
        self._romaneo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._romaneo_table.setFixedHeight(200)
        self._romaneo_table.setStyleSheet(f"QTableWidget {{ background: white; border: 1px solid {PAL['border']}; border-radius: 8px; font-size: 14px; font-weight: 600; }}")
        fl.addWidget(self._romaneo_table, 4, 0, 1, 4)

        main_h.addWidget(left_panel, stretch=6)

        # 2. PANEL DERECHO: TOTALES WOW Y ACCIONES
        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        # Tarjeta Totales
        totals_card = QFrame()
        totals_card.setStyleSheet(f\"\"\"
            QFrame {{ background: #0F172A; border-radius: 16px; border: 2px solid #1E293B; }}
            QLabel {{ color: white; background: transparent; }}
        \"\"\")
        totals_card.setGraphicsEffect(shadow)
        t_lay = QVBoxLayout(totals_card)
        t_lay.setContentsMargins(20, 20, 20, 20)

        lbl_t1 = QLabel("RESUMEN DE ROMANEO")
        lbl_t1.setStyleSheet("color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px;")
        t_lay.addWidget(lbl_t1)

        self._lbl_romaneo_totals = QLabel("0 items - 0.00 kg")
        self._lbl_romaneo_totals.setStyleSheet("color: #38BDF8; font-weight: 900; font-size: 26px;")
        t_lay.addWidget(self._lbl_romaneo_totals)

        t_lay.addSpacing(15)
        lbl_t2 = QLabel("MONTO TOTAL")
        lbl_t2.setStyleSheet("color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px;")
        t_lay.addWidget(lbl_t2)

        self._prov_amount = QLineEdit("0.00")
        self._prov_amount.setReadOnly(True)
        self._prov_amount.setAlignment(Qt.AlignRight)
        self._prov_amount.setStyleSheet("background: transparent; border: none; color: #10B981; font-weight: 900; font-size: 36px;")
        t_lay.addWidget(self._prov_amount)

        right_panel.addWidget(totals_card)

        # Tarjeta Acción
        action_card = QFrame()
        action_card.setStyleSheet(f"background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 16px;")
        a_lay = QVBoxLayout(action_card)
        a_lay.setContentsMargins(20, 20, 20, 20)
        
        a_lay.addWidget(QLabel("💳 CONDICIÓN DE PAGO:"))
        self._prov_payment = QComboBox()
        self._prov_payment.addItems(["A Pagar (Deuda en Cta. Cte.)", "Contado (Pago Inmediato)"])
        self._prov_payment.setStyleSheet(f"background: {PAL['surface2']}; border: 1px solid {PAL['border']}; padding: 12px; border-radius: 8px; color: {PAL['text']}; font-weight: 800; font-size: 13px;")
        a_lay.addWidget(self._prov_payment)
        
        a_lay.addSpacing(15)
        btn_add = QPushButton("✅ PROCESAR COMPRA")
        btn_add.setStyleSheet(f\"\"\"
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10B981, stop:1 #059669);
                color: white; border-radius: 10px; padding: 15px; font-weight: 900; font-size: 16px;
            }}
            QPushButton:hover {{ background: #059669; }}
        \"\"\")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._save_proveedor)
        a_lay.addWidget(btn_add)

        right_panel.addWidget(action_card)
        right_panel.addStretch()

        main_h.addLayout(right_panel, stretch=4)
        lay.addLayout(main_h)

        lay.addWidget(section_title("📋  Histórico de Compras a Proveedores"))
        self._tbl_prov = build_table(["ID", "Proveedor", "Monto Total", "Pagado", "Restante", "Vencimiento", "Estado", "Pagar"])
        self._tbl_prov.setFixedHeight(200)
        lay.addWidget(self._tbl_prov)
        lay.addStretch()

"""

if start_prov != -1 and end_prov != -1:
    content = content[:start_prov] + wow_proveedores + content[end_prov:]


# ---------------------------------------------------------
# 2. PROMEDIOS LOGIC AND UI
# ---------------------------------------------------------
start_promedios = content.find('    def _build_tab_promedios(self):')
end_promedios = content.find('    def _load_promedios(self):')
end_promedios_func = content.find('        pass', end_promedios) + 12

if start_promedios != -1 and end_promedios != -1:
    wow_promedios = """    # ================= ESTILOS =================
    CORTES_BASE = [
        ("Matambre", 1, 40), ("Paleta", 6, 36), ("Palomita", 1, 36), ("Osobuco", 6, -22),
        ("Tapa de asado", 2, 36), ("Vacío", 5, 38), ("Entraña", 1, 36), ("Asado", 9, 27),
        ("Roast beef", 7, 22), ("Lomo", 2, 57), ("Angosto", 6, 36), ("Falda", 3, 15),
        ("Cuadril", 3, 57), ("Colita", 1, 57), ("Nalga", 5, 57), ("Tapa de nalga", 2, 36),
        ("Peceto", 2, 57), ("Cuadrada", 5, 48), ("Tortuguita", 2, 36), ("Bola de lomo", 4, 48),
        ("Bife chorizo", 3, 57), ("Espinazo", 3, -30)
    ]

    def _build_tab_promedios(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📈  Desposte y Rentabilidad de Media Res"))

        self._costo_real_kg = 0.0

        # CABECERA
        cab = QHBoxLayout()
        self._prom_prov = input_field("Proveedor")
        self._prom_fecha = date_field()
        cab.addWidget(QLabel("Proveedor:"))
        cab.addWidget(self._prom_prov)
        cab.addStretch()
        cab.addWidget(QLabel("Fecha:"))
        cab.addWidget(self._prom_fecha)
        lay.addLayout(cab)

        # DATOS MEDIA RES
        media_frame = QFrame()
        media_frame.setStyleSheet(f"background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 8px;")
        m_lay = QHBoxLayout(media_frame)
        m_lay.setContentsMargins(15, 15, 15, 15)
        
        self._prom_kilos = input_field("Kilos totales")
        self._prom_merma = input_field("Merma (kg)")
        self._prom_precio = input_field("Precio/kg compra")
        
        btn_calc = btn_primary("⚙️ Calcular Costo Base")
        btn_calc.clicked.connect(self._calc_media_res)
        
        m_lay.addWidget(QLabel("Kilos:"))
        m_lay.addWidget(self._prom_kilos)
        m_lay.addWidget(QLabel("Merma:"))
        m_lay.addWidget(self._prom_merma)
        m_lay.addWidget(QLabel("Precio/kg:"))
        m_lay.addWidget(self._prom_precio)
        m_lay.addStretch()
        m_lay.addWidget(btn_calc)
        lay.addWidget(media_frame)

        # RESUMEN COSTOS
        self._lbl_prom_costos = QLabel("Kilos útiles: 0.00 | Costo real kg: $0.00")
        self._lbl_prom_costos.setStyleSheet(f"font-size: 16px; font-weight: 900; color: {PAL['danger']};")
        lay.addWidget(self._lbl_prom_costos)

        # TABLA DE CORTES
        self._prom_tabla = build_table(["Corte", "Kilos", "Costo $/kg", "Costo Total", "% Ganancia", "Precio/kg Venta", "Venta Total", "Ganancia Neta"])
        self._prom_tabla.itemChanged.connect(self._on_prom_tabla_changed)
        lay.addWidget(self._prom_tabla)

        # TOTALES Y ACCIONES
        tot_lay = QHBoxLayout()
        self._lbl_prom_totales = QLabel("Total Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {PAL['success']};")
        
        btn_redondeo = QPushButton("Redondear Precios (500)")
        btn_redondeo.setStyleSheet(f"background: {PAL['warning']}; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_redondeo.clicked.connect(self._prom_redondear)

        btn_pdf_int = btn_primary("📄 PDF Interno")
        btn_pdf_int.clicked.connect(self._prom_pdf_interno)

        btn_pdf_cli = btn_primary("📄 PDF Público (Lista Precios)")
        btn_pdf_cli.clicked.connect(self._prom_pdf_clientes)

        tot_lay.addWidget(self._lbl_prom_totales)
        tot_lay.addStretch()
        tot_lay.addWidget(btn_redondeo)
        tot_lay.addWidget(btn_pdf_int)
        tot_lay.addWidget(btn_pdf_cli)
        lay.addLayout(tot_lay)

        # CARGAR CORTES BASE
        self._load_cortes_base()

    def _load_cortes_base(self):
        self._prom_tabla.blockSignals(True)
        self._prom_tabla.setRowCount(0)
        for corte, kilos, pct in self.CORTES_BASE:
            r = self._prom_tabla.rowCount()
            self._prom_tabla.insertRow(r)
            self._prom_tabla.setItem(r,0,QTableWidgetItem(corte))
            self._prom_tabla.setItem(r,1,QTableWidgetItem(str(kilos)))
            self._prom_tabla.setItem(r,2,QTableWidgetItem("0.00"))
            self._prom_tabla.setItem(r,3,QTableWidgetItem("0.00"))
            self._prom_tabla.setItem(r,4,QTableWidgetItem(str(pct)))
            self._prom_tabla.setItem(r,5,QTableWidgetItem("0.00"))
            self._prom_tabla.setItem(r,6,QTableWidgetItem("0.00"))
            self._prom_tabla.setItem(r,7,QTableWidgetItem("0.00"))
            
            # Make columns 0, 1, 2, 3, 6, 7 read-only
            for c in [0, 1, 2, 3, 6, 7]:
                it = self._prom_tabla.item(r, c)
                it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if c in [2, 3]: it.setForeground(QColor(PAL['text3']))
        self._prom_tabla.blockSignals(False)

    def _calc_media_res(self):
        try:
            kilos = float(self._prom_kilos.text().replace(',', '.') or "0")
            merma = float(self._prom_merma.text().replace(',', '.') or "0")
            precio = float(self._prom_precio.text().replace(',', '.') or "0")
            
            if merma >= kilos:
                QMessageBox.warning(self, "Error", "La merma no puede ser mayor o igual a los kilos.")
                return
                
            self._kilos_utiles = kilos - merma
            total_compra = kilos * precio
            self._costo_real_kg = total_compra / self._kilos_utiles
            
            self._lbl_prom_costos.setText(f"Kilos útiles: {self._kilos_utiles:.2f} kg | Costo real kg: ${self._costo_real_kg:,.2f}")
            self._on_prom_tabla_changed(None)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Verifique los datos numéricos: {e}")

    def _prom_redondear(self):
        import math
        if self._costo_real_kg == 0: return
        self._prom_tabla.blockSignals(True)
        for r in range(self._prom_tabla.rowCount()):
            try:
                precio_actual = float(self._prom_tabla.item(r, 5).text().replace(',', ''))
                if precio_actual > 0:
                    redondeado = math.ceil(precio_actual / 500) * 500
                    self._prom_tabla.setItem(r, 5, QTableWidgetItem(f"{redondeado:,.2f}"))
            except: pass
        self._prom_tabla.blockSignals(False)
        self._on_prom_tabla_changed(None)

    def _on_prom_tabla_changed(self, item):
        if getattr(self, '_costo_real_kg', 0) == 0: return
        self._prom_tabla.blockSignals(True)

        if item is not None:
            r = item.row()
            col = item.column()
            try:
                if col == 4: # % Ganancia
                    pct = float(item.text().replace(',','.'))
                    precio_venta = self._costo_real_kg * (1 + pct / 100)
                    self._prom_tabla.setItem(r, 5, QTableWidgetItem(f"{precio_venta:,.2f}"))
                elif col == 5: # Precio Venta
                    precio_venta = float(item.text().replace(',','.'))
                    pct = ((precio_venta / self._costo_real_kg) - 1) * 100
                    self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{pct:.2f}"))
            except: pass

        t_venta = 0.0
        t_ganancia = 0.0
        for r in range(self._prom_tabla.rowCount()):
            try:
                kilos = float(self._prom_tabla.item(r, 1).text())
                precio_venta = float(self._prom_tabla.item(r, 5).text().replace(',',''))
                if self._costo_real_kg > 0 and precio_venta > 0:
                    pct = ((precio_venta / self._costo_real_kg) - 1) * 100
                    self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{pct:.2f}"))
                
                costo_tot = kilos * self._costo_real_kg
                venta_tot = kilos * precio_venta
                ganancia = venta_tot - costo_tot

                self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{self._costo_real_kg:,.2f}"))
                self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{costo_tot:,.2f}"))
                
                vi = QTableWidgetItem(f"{venta_tot:,.2f}")
                vi.setForeground(QColor(PAL['success'] if ganancia >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 6, vi)

                gi = QTableWidgetItem(f"{ganancia:,.2f}")
                gi.setForeground(QColor(PAL['success'] if ganancia >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 7, gi)

                t_venta += venta_tot
                t_ganancia += ganancia
            except: pass
            
        self._lbl_prom_totales.setText(f"Total Venta: ${t_venta:,.2f} | Ganancia: ${t_ganancia:,.2f}")
        self._prom_tabla.blockSignals(False)

    def _prom_pdf_interno(self):
        try:
            from src.jefe.contabilidad.pdf_promedios import exportar_pdf_interno
            exportar_pdf_interno(self._prom_tabla, self._prom_prov.text(), self._prom_fecha.date().toString("yyyy-MM-dd"), float(self._prom_kilos.text().replace(",", ".") or 0), float(self._prom_merma.text().replace(",", ".") or 0), float(self._prom_precio.text().replace(",", ".") or 0), self)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error exportando PDF:\\n{e}")

    def _prom_pdf_clientes(self):
        try:
            from src.jefe.contabilidad.pdf_promedios import exportar_pdf_clientes
            exportar_pdf_clientes(self._prom_tabla, self._prom_prov.text(), self._prom_fecha.date().toString("yyyy-MM-dd"), self)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error exportando PDF:\\n{e}")

    def _load_promedios(self):
        pass
"""
    content = content[:start_promedios] + wow_promedios + content[end_promedios_func:]

# Replace the updated file content
with codecs.open('src/jefe/jefe_contabilidad.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("WOW refactor applied")
