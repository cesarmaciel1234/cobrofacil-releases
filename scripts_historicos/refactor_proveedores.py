import codecs
import re

with codecs.open('src/jefe/jefe_contabilidad.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find("    def _build_tab_proveedores(self):")
end_idx = content.find("    # ─────────────────────────────────────────────────────────────────────────\\n    # TAB 4 — PRÉSTAMOS")

if start_idx == -1 or end_idx == -1:
    print("Could not find boundaries")
    exit(1)

new_methods = """    def _build_tab_proveedores(self):
        lay, _ = self._page()
        lay.addWidget(section_title("🚚  Proveedores — Frigorífico y Carga Rápida"))

        main_h = QHBoxLayout()
        main_h.setSpacing(20)

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
        title_lbl.setStyleSheet(f"QLabel {{ color: {PAL['primary']}; font-weight: 900; font-size: 14px; letter-spacing: 1px; }}")
        fl.addWidget(title_lbl, 0, 0, 1, 4)

        lbl_fecha = QLabel("Fecha:")
        lbl_fecha.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_fecha, 1, 0)
        self._prov_date = date_field(); fl.addWidget(self._prov_date, 1, 1)

        lbl_prov = QLabel("Proveedor:")
        lbl_prov.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_prov, 1, 2)
        self._prov_nombre = input_field("Ej: Frigorífico Rioplatense"); fl.addWidget(self._prov_nombre, 1, 3)

        lbl_tropa = QLabel("Tropa/Lote:")
        lbl_tropa.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_tropa, 2, 0)
        self._prov_tropa = input_field("Nro Tropa"); fl.addWidget(self._prov_tropa, 2, 1)

        lbl_merc = QLabel("Mercadería (Foco):")
        lbl_merc.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_merc, 2, 2)
        self._prov_type = QComboBox()
        self._prov_type.addItems(["Carne (Media Res)", "Cerdo", "Pollo", "Achuras", "Otro"])
        self._prov_type.setStyleSheet(f"QComboBox {{ background: {PAL['surface2']}; border: 1px solid {PAL['border']}; padding: 8px; border-radius: 6px; color: {PAL['text']}; font-weight: 800; font-size: 13px; }}")
        self._prov_type.currentTextChanged.connect(self._on_prov_type_change)
        fl.addWidget(self._prov_type, 2, 3)

        lbl_precio = QLabel("Precio Unit.:")
        lbl_precio.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        fl.addWidget(lbl_precio, 3, 0)
        self._prov_precio = input_field("$ Precio x Kg/Caja")
        self._prov_precio.setStyleSheet(f"QLineEdit {{ background: #FEF3C7; border: 2px solid #F59E0B; padding: 10px; border-radius: 8px; color: #92400E; font-weight: bold; font-size: 14px; }}")
        fl.addWidget(self._prov_precio, 3, 1)

        self._lbl_carga = QLabel("⚡ CARGA RÁPIDA (PESO + ENTER):")
        self._lbl_carga.setStyleSheet("QLabel { color: #EF4444; font-weight: 900; font-size: 11px; }")
        fl.addWidget(self._lbl_carga, 3, 2)
        
        self._romaneo_input = input_field("Ej: 80.5 y Enter")
        self._romaneo_input.setStyleSheet(f"QLineEdit {{ background: #ECFDF5; border: 2px solid #10B981; padding: 12px; border-radius: 8px; color: #065F46; font-weight: 900; font-size: 16px; }}")
        self._romaneo_input.returnPressed.connect(self._add_romaneo_item)
        fl.addWidget(self._romaneo_input, 3, 3)

        self._romaneo_table = build_table(["Nro", "Mercadería", "Precio Unit.", "Peso/Cant", "Subtotal", "X"])
        self._romaneo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._romaneo_table.setFixedHeight(200)
        self._romaneo_table.setStyleSheet(f"QTableWidget {{ background: white; border: 1px solid {PAL['border']}; border-radius: 8px; font-size: 13px; font-weight: 600; }}")
        fl.addWidget(self._romaneo_table, 4, 0, 1, 4)

        main_h.addWidget(left_panel, stretch=6)

        right_panel = QVBoxLayout()
        right_panel.setSpacing(15)

        totals_card = QFrame()
        totals_card.setStyleSheet(f\"\"\"
            QFrame {{ background: #0F172A; border-radius: 16px; border: 2px solid #1E293B; }}
            QLabel {{ color: white; background: transparent; }}
        \"\"\")
        totals_card.setGraphicsEffect(shadow)
        t_lay = QVBoxLayout(totals_card)
        t_lay.setContentsMargins(20, 20, 20, 20)

        lbl_t1 = QLabel("RESUMEN DE ROMANEO")
        lbl_t1.setStyleSheet("QLabel { color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px; }")
        t_lay.addWidget(lbl_t1)

        self._lbl_romaneo_totals = QLabel("0 items - $0.00")
        self._lbl_romaneo_totals.setStyleSheet("QLabel { color: #38BDF8; font-weight: 900; font-size: 22px; }")
        t_lay.addWidget(self._lbl_romaneo_totals)

        t_lay.addSpacing(15)
        lbl_t2 = QLabel("MONTO TOTAL")
        lbl_t2.setStyleSheet("QLabel { color: #94A3B8; font-weight: 900; font-size: 12px; letter-spacing: 2px; }")
        t_lay.addWidget(lbl_t2)

        self._prov_amount = QLineEdit("0.00")
        self._prov_amount.setReadOnly(True)
        self._prov_amount.setAlignment(Qt.AlignRight)
        self._prov_amount.setStyleSheet("QLineEdit { background: transparent; border: none; color: #10B981; font-weight: 900; font-size: 36px; }")
        t_lay.addWidget(self._prov_amount)

        right_panel.addWidget(totals_card)

        action_card = QFrame()
        action_card.setStyleSheet(f"QFrame {{ background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 16px; }}")
        a_lay = QVBoxLayout(action_card)
        a_lay.setContentsMargins(20, 20, 20, 20)
        
        lbl_pago = QLabel("💳 CONDICIÓN DE PAGO:")
        lbl_pago.setStyleSheet(f"QLabel {{ color: {PAL['text']}; font-weight: bold; }}")
        a_lay.addWidget(lbl_pago)
        self._prov_payment = QComboBox()
        self._prov_payment.addItems(["A Pagar (Deuda en Cta. Cte.)", "Contado (Pago Inmediato)"])
        self._prov_payment.setStyleSheet(f"QComboBox {{ background: {PAL['surface2']}; border: 1px solid {PAL['border']}; padding: 12px; border-radius: 8px; color: {PAL['text']}; font-weight: 800; font-size: 13px; }}")
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

        lbl_hist = section_title("📋  Histórico de Compras a Proveedores")
        lay.addWidget(lbl_hist)
        self._tbl_prov = build_table(["ID", "Proveedor", "Monto Total", "Pagado", "Restante", "Vencimiento", "Estado", "Acciones"])
        self._tbl_prov.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self._tbl_prov.setFixedHeight(200)
        lay.addWidget(self._tbl_prov)
        lay.addStretch()

    def _on_prov_type_change(self, text):
        if text in ["Pollo", "Achuras", "Otro"]:
            self._lbl_carga.setText("Carga Rápida (Cajas y presiona Enter):")
            self._prov_precio.setPlaceholderText("Precio x Caja/Unid.")
            self._romaneo_input.setPlaceholderText("Cant Cajas (ej: 5) y Enter")
        else:
            self._lbl_carga.setText("Carga Rápida (Escribe peso y presiona Enter):")
            self._prov_precio.setPlaceholderText("Precio x Kg")
            self._romaneo_input.setPlaceholderText("Ej: 80.5 y Enter")
        self._romaneo_input.setFocus()

    def _add_romaneo_item(self):
        val = self._romaneo_input.text().strip().replace(',', '.')
        precio_val = self._prov_precio.text().strip().replace(',', '.')
        if not val or not precio_val:
            QMessageBox.warning(self, "Error", "Debe ingresar el Precio Unitario antes de cargar pesos.")
            self._prov_precio.setFocus()
            return
            
        try:
            val_float = float(val)
            precio_float = float(precio_val)
            subtotal = val_float * precio_float
            
            row = self._romaneo_table.rowCount()
            self._romaneo_table.insertRow(row)
            
            nro_item = QTableWidgetItem(f"#{row+1}")
            nro_item.setTextAlignment(Qt.AlignCenter)
            self._romaneo_table.setItem(row, 0, nro_item)
            
            merc_item = QTableWidgetItem(self._prov_type.currentText())
            merc_item.setTextAlignment(Qt.AlignCenter)
            self._romaneo_table.setItem(row, 1, merc_item)
            
            pu_item = QTableWidgetItem(f"${precio_float:,.2f}")
            pu_item.setTextAlignment(Qt.AlignCenter)
            self._romaneo_table.setItem(row, 2, pu_item)
            
            peso_item = QTableWidgetItem(f"{val_float:.2f}")
            peso_item.setTextAlignment(Qt.AlignCenter)
            self._romaneo_table.setItem(row, 3, peso_item)
            
            sub_item = QTableWidgetItem(f"${subtotal:,.2f}")
            sub_item.setTextAlignment(Qt.AlignCenter)
            self._romaneo_table.setItem(row, 4, sub_item)
            
            btn_del = QPushButton("X")
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet("QPushButton { background-color: #ef4444; color: white; border-radius: 4px; font-weight: bold; }")
            btn_del.clicked.connect(lambda _, r=row: self._remove_romaneo_item(r))
            
            widget = QWidget()
            l = QHBoxLayout(widget)
            l.setContentsMargins(0,0,0,0)
            l.addWidget(btn_del)
            l.setAlignment(Qt.AlignCenter)
            self._romaneo_table.setCellWidget(row, 5, widget)
            
            self._romaneo_input.clear()
            self._romaneo_input.setFocus()
            self._romaneo_table.scrollToBottom()
            self._update_prov_calc()
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese valores numéricos válidos en Peso/Precio.")

    def _remove_romaneo_item(self, row):
        self._romaneo_table.removeRow(row)
        for i in range(self._romaneo_table.rowCount()):
            self._romaneo_table.item(i, 0).setText(f"#{i+1}")
            widget = self._romaneo_table.cellWidget(i, 5)
            if widget:
                btn = widget.findChild(QPushButton)
                if btn:
                    try: btn.clicked.disconnect()
                    except: pass
                    btn.clicked.connect(lambda _, r=i: self._remove_romaneo_item(r))
        self._update_prov_calc()

    def _update_prov_calc(self):
        monto_total = 0.0
        items_count = self._romaneo_table.rowCount()
        for i in range(items_count):
            sub_str = self._romaneo_table.item(i, 4).text().replace('$','').replace(',','')
            monto_total += float(sub_str)
            
        self._lbl_romaneo_totals.setText(f"{items_count} items - ${monto_total:,.2f}")
        self._prov_amount.setText(f"{monto_total:.2f}")

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
                
                desc_full = str(row[1] or "")
                prov_match = re.search(r"Proveedor:\\s*(.*)", desc_full)
                prov_show = prov_match.group(1).strip() if prov_match else "Proveedor General"
                
                vals = [str(row[0]), prov_show, f"$ {monto:,.2f}",
                        f"$ {pagado:,.2f}", f"$ {rest:,.2f}", str(row[4] or ""), estado_txt]
                for c, v in enumerate(vals):
                    it = QTableWidgetItem(v)
                    if c == 6 and status == "pending":
                        it.setForeground(QColor(PAL["danger"]))
                    self._tbl_prov.setItem(r, c, it)
                
                w = QWidget()
                l = QHBoxLayout(w)
                l.setContentsMargins(0,0,0,0)
                l.setSpacing(5)
                
                btn_ver = btn_secondary("👁️ Ver")
                btn_ver.setFixedSize(60, 30)
                btn_ver.clicked.connect(lambda _, d=desc_full: self._show_remito_detail(d))
                
                btn_pagar = btn_primary("💳 Pagar")
                btn_pagar.setFixedSize(70, 30)
                btn_pagar.clicked.connect(lambda _, rid=row[0], rem=rest: self._pagar_proveedor(rid, rem))
                
                l.addWidget(btn_ver)
                l.addWidget(btn_pagar)
                l.addStretch()
                self._tbl_prov.setCellWidget(r, 7, w)
        except Exception as e:
            logger.error(f"load_proveedores: {e}")

    def _show_remito_detail(self, desc):
        msg = QMessageBox(self)
        msg.setWindowTitle("📄 Detalle de Remito")
        msg.setText("<b>Desglose de la Compra:</b>")
        msg.setInformativeText(desc)
        msg.setStyleSheet(f"QLabel {{ font-size: 14px; color: {PAL['text']}; }} QMessageBox {{ background: {PAL['bg']}; }} QPushButton {{ padding: 6px 12px; }}")
        msg.exec_()

    def _pagar_proveedor(self, debt_id, restante):
        if restante <= 0:
            QMessageBox.information(self, "Aviso", "Esta cuenta ya está saldada.")
            return
        amt, ok = QInputDialog.getDouble(self, "Pagar a Proveedor", f"Monto a pagar (Restante: ${restante:,.2f}):", min=0, max=restante, decimals=2)
        if ok and amt > 0:
            try:
                self._db.pay_debt(debt_id, amt)
                QMessageBox.information(self, "Éxito", f"Pago de ${amt:,.2f} registrado.")
                self._load_proveedores()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"No se pudo registrar el pago: {e}")

    def _save_proveedor(self):
        amount_text = self._prov_amount.text()
        if not amount_text or self._romaneo_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Debe cargar ítems y un monto total.")
            return
        try:
            amount = float(amount_text)
            date = self._prov_date.date().toString("yyyy-MM-dd")
            prov_name = self._prov_nombre.text() or "Proveedor General"
            tropa = self._prov_tropa.text() or "-"
            
            grupos = {}
            for i in range(self._romaneo_table.rowCount()):
                nro = self._romaneo_table.item(i, 0).text()
                merc = self._romaneo_table.item(i, 1).text()
                precio = float(self._romaneo_table.item(i, 2).text().replace('$','').replace(',',''))
                peso = float(self._romaneo_table.item(i, 3).text())
                key = (merc, precio)
                if key not in grupos: grupos[key] = []
                grupos[key].append((nro, peso))

            payment = self._prov_payment.currentText()
            
            try:
                from src.base_de_datos.database import db_manager
                for (merc, precio), items in grupos.items():
                    total_kilos_grupo = sum([p for n, p in items])
                    monto_grupo = total_kilos_grupo * precio
                    
                    db_manager.execute_non_query(
                        "INSERT INTO romaneos (fecha, proveedor, tropa, tipo_carne, precio_unitario, total_kilos, monto_total, estado_pago, registrado_por) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (date, prov_name, tropa, merc, precio, total_kilos_grupo, monto_grupo, payment, 'jefe_admin')
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
            
            desc = f"Proveedor: {prov_name}\\nTropa: {tropa}\\n\\n--- DETALLE DE COMPRA ---\\n"
            for (merc, precio), items in grupos.items():
                total_kilos_grupo = sum([p for n, p in items])
                monto_grupo = total_kilos_grupo * precio
                desc += f"• {merc}: {len(items)} items | Total: {total_kilos_grupo:.2f} | Precio: ${precio:,.2f} | Subtotal: ${monto_grupo:,.2f}\\n"
            desc += f"\\nTOTAL GENERAL: ${amount:,.2f}"

            if payment == "Contado (Pago Inmediato)":
                self._db.add_expense(date, "Mercadería / Stock", amount, desc, 'variable')
                QMessageBox.information(self, "Exito", "Compra multi-ítem registrada (Pagado al Contado)")
            else:
                self._db.add_general_debt(desc, "Proveedor", amount, date)
                QMessageBox.information(self, "Exito", "Compra multi-ítem registrada (Deuda Pendiente)")
                
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
"""

content = content[:start_idx] + new_methods + "\\n" + content[end_idx:]

with codecs.open('src/jefe/jefe_contabilidad.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Refactor with popup success.")
