import codecs

with codecs.open('src/jefe/jefe_contabilidad.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add IDX_PROMEDIOS
if "IDX_PROMEDIOS =" not in content:
    idx_reportes_idx = content.find("IDX_REPORTES   = 10")
    if idx_reportes_idx != -1:
        insert_text = "\n    IDX_PROMEDIOS  = 11\n"
        idx_end = content.find("\n", idx_reportes_idx)
        content = content[:idx_end] + insert_text + content[idx_end:]

# 2. Add Promedios to ALL_ITEMS
if '("📈  Promedios"' not in content:
    reportes_item_idx = content.find('("📄  Reportes PDF",       self.IDX_REPORTES),')
    if reportes_item_idx != -1:
        insert_text = '\n            (None, None),\n            ("📈  Promedios",          self.IDX_PROMEDIOS),'
        item_end = content.find("\n", reportes_item_idx)
        content = content[:item_end] + insert_text + content[item_end:]

# 3. Route Promedios
if 'self.IDX_PROMEDIOS:' not in content:
    route_reportes_idx = content.find('self.IDX_REPORTES:    self._load_reportes,')
    if route_reportes_idx != -1:
        insert_text = '\n            self.IDX_PROMEDIOS:   self._load_promedios,'
        route_end = content.find("\n", route_reportes_idx)
        content = content[:route_end] + insert_text + content[route_end:]

# 4. Create _build_tab_promedios and _load_promedios
promedios_methods = """
    # ─────────────────────────────────────────────────────────────────────────
    # TAB 11 — PROMEDIOS
    # ─────────────────────────────────────────────────────────────────────────
    def _build_tab_promedios(self):
        lay, _ = self._page()
        lay.addWidget(section_title("📈  Módulo de Promedios (En Construcción)"))
        lay.addStretch()

    def _load_promedios(self):
        pass
"""
if "def _build_tab_promedios" not in content:
    # insert before _build_tab_reportes or at the end of tabs
    build_reportes_idx = content.find("def _build_tab_reportes(self):")
    if build_reportes_idx != -1:
        # find the preceding comment
        preceding_comment = content.rfind("# ──", 0, build_reportes_idx)
        if preceding_comment != -1:
            content = content[:preceding_comment] + promedios_methods + "\n    " + content[preceding_comment:]


# 5. Add to self._pages setup
if 'self._build_tab_promedios()' not in content:
    setup_reportes_idx = content.find("self._build_tab_reportes()")
    if setup_reportes_idx != -1:
        insert_text = "\n        self._build_tab_promedios()"
        setup_end = content.find("\n", setup_reportes_idx)
        content = content[:setup_end] + insert_text + content[setup_end:]

# 6. Replace Proveedores logic!
start_prov = content.find('    def _build_tab_proveedores(self):')
end_prov = content.find('    # TAB 4 — PRÉSTAMOS')

new_proveedores_logic = """    def _build_tab_proveedores(self):
        lay, _ = self._page()
        lay.addWidget(section_title("🚚  Proveedores — Cuentas a Pagar y Carga Rápida"))

        # Carga Rápida / Romaneo Form
        form_frame = QFrame()
        form_frame.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 12px; }}")
        fl = QGridLayout(form_frame)
        fl.setContentsMargins(20, 16, 20, 16); fl.setSpacing(12)

        fl.addWidget(QLabel("Fecha:"), 0, 0)
        self._prov_date = date_field(); fl.addWidget(self._prov_date, 0, 1)

        fl.addWidget(QLabel("Proveedor:"), 0, 2)
        self._prov_nombre = input_field("Nombre del proveedor..."); fl.addWidget(self._prov_nombre, 0, 3)

        fl.addWidget(QLabel("Tropa/Lote:"), 1, 0)
        self._prov_tropa = input_field("Nro Tropa (Opcional)"); fl.addWidget(self._prov_tropa, 1, 1)

        fl.addWidget(QLabel("Mercadería:"), 1, 2)
        self._prov_type = QComboBox()
        self._prov_type.addItems(["Carne (Media Res)", "Cerdo", "Pollo", "Achuras", "Otro"])
        self._prov_type.setStyleSheet(f"background: {PAL['surface2']}; border: 1px solid {PAL['border']}; padding: 8px; border-radius: 6px; color: {PAL['text']}; font-weight: 600;")
        self._prov_type.currentTextChanged.connect(self._on_prov_type_change)
        fl.addWidget(self._prov_type, 1, 3)

        fl.addWidget(QLabel("Precio Unit.:"), 2, 0)
        self._prov_precio = input_field("Precio x Kg/Caja")
        self._prov_precio.textChanged.connect(self._update_prov_calc)
        fl.addWidget(self._prov_precio, 2, 1)

        self._lbl_carga = QLabel("Carga Rápida (Escribe peso y presiona Enter):")
        fl.addWidget(self._lbl_carga, 2, 2)
        
        self._romaneo_input = input_field("Ej: 80.5 y Enter")
        self._romaneo_input.returnPressed.connect(self._add_romaneo_item)
        fl.addWidget(self._romaneo_input, 2, 3)

        # Grilla de pesaje
        self._romaneo_table = build_table(["Nro", "Peso/Cant", "X"])
        self._romaneo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._romaneo_table.setFixedHeight(140)
        fl.addWidget(self._romaneo_table, 3, 0, 1, 4)

        # Totales y Footer
        self._lbl_romaneo_totals = QLabel("Total: 0 items - 0.00 kg")
        self._lbl_romaneo_totals.setStyleSheet(f"font-weight: bold; color: {PAL['primary']}; font-size: 14px;")
        fl.addWidget(self._lbl_romaneo_totals, 4, 0, 1, 2)

        fl.addWidget(QLabel("Monto Total ($):"), 4, 2)
        self._prov_amount = input_field("0.00")
        fl.addWidget(self._prov_amount, 4, 3)

        fl.addWidget(QLabel("Forma Pago:"), 5, 0)
        self._prov_payment = QComboBox()
        self._prov_payment.addItems(["A Pagar (Deuda)", "Contado (Pago Inmediato)"])
        self._prov_payment.setStyleSheet(f"background: {PAL['surface2']}; border: 1px solid {PAL['border']}; padding: 8px; border-radius: 6px; color: {PAL['text']}; font-weight: 600;")
        fl.addWidget(self._prov_payment, 5, 1)

        btn_add = btn_primary("➕  Guardar Compra")
        btn_add.clicked.connect(self._save_proveedor)
        fl.addWidget(btn_add, 5, 2, 1, 2)

        for lbl_w in form_frame.findChildren(QLabel):
            if lbl_w != self._lbl_romaneo_totals:
                lbl_w.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PAL['text2']}; background: transparent; border: none;")
        lay.addWidget(form_frame)

        lay.addWidget(section_title("Histórico de Compras a Proveedores"))
        self._tbl_prov = build_table(["ID", "Proveedor", "Monto Total", "Pagado", "Restante", "Vencimiento", "Estado", "Pagar"])
        lay.addWidget(self._tbl_prov)
        lay.addStretch()

    def _on_prov_type_change(self, text):
        if text in ["Pollo", "Achuras", "Otro"]:
            self._lbl_carga.setText("Carga Rápida (Cajas y presiona Enter):")
            self._prov_precio.setPlaceholderText("Precio x Caja/Unid.")
            self._romaneo_input.setPlaceholderText("Cant Cajas (ej: 5) y Enter")
            self._lbl_romaneo_totals.setText("Total: 0 items - 0 Cajas")
        else:
            self._lbl_carga.setText("Carga Rápida (Escribe peso y presiona Enter):")
            self._prov_precio.setPlaceholderText("Precio x Kg")
            self._romaneo_input.setPlaceholderText("Ej: 80.5 y Enter")
            self._lbl_romaneo_totals.setText("Total: 0 items - 0.00 kg")
        self._romaneo_table.setRowCount(0)
        self._update_prov_calc()

    def _add_romaneo_item(self):
        val = self._romaneo_input.text().strip().replace(',', '.')
        if not val: return
        try:
            val_float = float(val)
            row = self._romaneo_table.rowCount()
            self._romaneo_table.insertRow(row)
            
            nro_item = QTableWidgetItem(f"#{row+1}")
            nro_item.setTextAlignment(Qt.AlignCenter)
            self._romaneo_table.setItem(row, 0, nro_item)
            
            peso_item = QTableWidgetItem(f"{val_float:.2f}")
            peso_item.setTextAlignment(Qt.AlignCenter)
            self._romaneo_table.setItem(row, 1, peso_item)
            
            btn_del = QPushButton("X")
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet("background-color: #ef4444; color: white; border-radius: 4px; font-weight: bold;")
            btn_del.clicked.connect(lambda _, r=row: self._remove_romaneo_item(r))
            
            widget = QWidget()
            l = QHBoxLayout(widget)
            l.setContentsMargins(0,0,0,0)
            l.addWidget(btn_del)
            l.setAlignment(Qt.AlignCenter)
            self._romaneo_table.setCellWidget(row, 2, widget)
            
            self._romaneo_input.clear()
            self._romaneo_input.setFocus()
            self._romaneo_table.scrollToBottom()
            self._update_prov_calc()
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese un valor numérico válido.")

    def _remove_romaneo_item(self, row):
        self._romaneo_table.removeRow(row)
        for i in range(self._romaneo_table.rowCount()):
            self._romaneo_table.item(i, 0).setText(f"#{i+1}")
            widget = self._romaneo_table.cellWidget(i, 2)
            if widget:
                btn = widget.findChild(QPushButton)
                if btn:
                    try: btn.clicked.disconnect()
                    except: pass
                    btn.clicked.connect(lambda _, r=i: self._remove_romaneo_item(r))
        self._update_prov_calc()

    def _update_prov_calc(self):
        total_qty = 0.0
        items_count = self._romaneo_table.rowCount()
        for i in range(items_count):
            total_qty += float(self._romaneo_table.item(i, 1).text())
            
        is_pollo = self._prov_type.currentText() in ["Pollo", "Achuras", "Otro"]
        if is_pollo:
            self._lbl_romaneo_totals.setText(f"Total: {items_count} items - {int(total_qty)} Cajas")
        else:
            self._lbl_romaneo_totals.setText(f"Total: {items_count} items - {total_qty:.2f} kg")
            
        precio_text = self._prov_precio.text().replace(',', '.')
        if precio_text:
            try:
                precio = float(precio_text)
                self._prov_amount.setText(f"{total_qty * precio:.2f}")
            except: pass

    def _load_proveedores(self):
        if not self._db: return
        try:
            rows = self._db.get_general_debts()
            rows = [r for r in (rows or []) if str(r[2] or "") == "Proveedor"]
            self._tbl_prov.setRowCount(0)
            for row in rows:
                r = self._tbl_prov.rowCount()
                self._tbl_prov.insertRow(r)
                monto   = float(row[3] or 0)
                pagado  = float(row[6] if len(row) > 6 else 0)
                rest    = monto - pagado
                status  = str(row[5] or "pending")
                estado_txt = {"pending": "⏳ Pendiente", "partial": "🔶 Parcial", "paid": "✅ Pagado"}.get(status, status)
                vals = [str(row[0]), str(row[1] or ""), f"$ {monto:,.2f}",
                        f"$ {pagado:,.2f}", f"$ {rest:,.2f}", str(row[4] or ""), estado_txt]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if c == 6 and status == "pending":
                        it.setForeground(QColor(PAL["danger"]))
                    self._tbl_prov.setItem(r, c, it)
                btn = btn_primary("💳 Pagar")
                btn.setFixedSize(80, 30)
                btn.clicked.connect(lambda _, rid=row[0], rem=rest: self._pagar_proveedor(rid, rem))
                self._tbl_prov.setCellWidget(r, 7, btn)
        except Exception as e:
            logger.error(f"load_proveedores: {e}")

    def _save_proveedor(self):
        amount_text = self._prov_amount.text()
        if not amount_text or self._romaneo_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Debe cargar ítems y un monto total.")
            return
        try:
            amount = float(amount_text)
            date = self._prov_date.date().toString("yyyy-MM-dd")
            prov_name = self._prov_nombre.text() or "Proveedor General"
            prov_type = self._prov_type.currentText()
            tropa = self._prov_tropa.text() or "-"
            precio_text = self._prov_precio.text().replace(',', '.')
            precio = float(precio_text) if precio_text else 0.0
            
            items = []
            total_kilos = 0.0
            for i in range(self._romaneo_table.rowCount()):
                nro = self._romaneo_table.item(i, 0).text()
                peso = float(self._romaneo_table.item(i, 1).text())
                items.append((nro, peso))
                total_kilos += peso

            payment = self._prov_payment.currentText()
            
            # Guardado Central (Inventario)
            try:
                from src.base_de_datos.database import db_manager
                db_manager.execute_non_query(
                    "INSERT INTO romaneos (fecha, proveedor, tropa, tipo_carne, precio_unitario, total_kilos, monto_total, estado_pago, registrado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (date, prov_name, tropa, prov_type, precio, total_kilos, amount, payment, 'jefe_admin')
                )
                res = db_manager.execute_query("SELECT id FROM romaneos ORDER BY id DESC LIMIT 1")
                if res and len(res) > 0:
                    romaneo_id = res[0]['id']
                    for nro, peso in items:
                        db_manager.execute_non_query(
                            "INSERT INTO romaneo_items (romaneo_id, nro_garrote, peso) VALUES (?, ?, ?)",
                            (romaneo_id, nro, peso)
                        )
            except Exception as e_db:
                print(f"Error DB central romaneos: {e_db}")
            
            # Guardado Finanzas Jefatura (Local SQLite)
            desc = f"Proveedor: {prov_name}\\nMercadería: {prov_type}\\nTropa: {tropa}\\n"
            is_pollo = prov_type in ["Pollo", "Achuras", "Otro"]
            if is_pollo:
                desc += f"Cantidad: {int(total_kilos)} cajas\\nPrecio: ${precio:,.2f} c/u"
            else:
                desc += f"Total: {total_kilos:.2f} kg ({len(items)} items)\\nPrecio: ${precio:,.2f}/kg"

            if payment == "Contado (Pago Inmediato)":
                self._db.add_expense(date, "Mercadería / Stock", amount, desc, 'variable')
                QMessageBox.information(self, "Exito", "Compra registrada (Pagado al Contado)")
            else:
                self._db.add_general_debt(desc, "Proveedor", amount, date)
                QMessageBox.information(self, "Exito", "Compra registrada (Deuda Pendiente)")
                
            self._romaneo_table.setRowCount(0)
            self._prov_precio.clear()
            self._prov_amount.clear()
            self._romaneo_input.clear()
            self._prov_tropa.clear()
            self._prov_nombre.clear()
            self._update_prov_calc()
            self._load_proveedores()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error guardando proveedor: {e}")

    # ─────────────────────────────────────────────────────────────────────────
"""

if start_prov != -1 and end_prov != -1:
    content = content[:start_prov] + new_proveedores_logic + content[end_prov:]


with codecs.open('src/jefe/jefe_contabilidad.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Migration successful")
