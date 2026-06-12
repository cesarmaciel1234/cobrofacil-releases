import codecs

with codecs.open('src/jefe/contabilidad/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# REPLACE init_proveedores_tab AND on_prov_type_change
start_idx = content.find('    def init_proveedores_tab(self):')
end_idx = content.find('    def init_fixed_costs_tab(self):')

if start_idx == -1 or end_idx == -1:
    print("Error finding init_proveedores_tab block")
    exit(1)

new_init = """    def init_proveedores_tab(self):
        self.tab_proveedores = QWidget()
        layout = QHBoxLayout(self.tab_proveedores)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Left: Form
        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setFixedWidth(380)
        form_layout = QVBoxLayout(form_container)
        form_layout.addWidget(QLabel("NUEVA COMPRA / ROMANEO"))
        
        self.prov_date = QDateEdit()
        self.prov_date.setCalendarPopup(True)
        self.prov_date.setDate(QDate.currentDate())
        form_layout.addWidget(QLabel("Fecha:"))
        form_layout.addWidget(self.prov_date)

        self.prov_tropa = QLineEdit()
        self.prov_tropa.setPlaceholderText("Nro Tropa / Lote (Opcional)")
        form_layout.addWidget(QLabel("Tropa / Lote:"))
        form_layout.addWidget(self.prov_tropa)

        self.prov_name = QLineEdit()
        self.prov_name.setPlaceholderText("Nombre Proveedor (Opcional)")
        form_layout.addWidget(QLabel("Proveedor:"))
        form_layout.addWidget(self.prov_name)

        self.prov_type = QComboBox()
        self.prov_type.addItems(["Carne (Media Res)", "Cerdo", "Pollo", "Achuras", "Otro"])
        self.prov_type.currentTextChanged.connect(self.on_prov_type_change)
        form_layout.addWidget(QLabel("Tipo de Mercadería:"))
        form_layout.addWidget(self.prov_type)

        self.prov_precio_kg = QLineEdit()
        self.prov_precio_kg.setPlaceholderText("Precio x Kg / Caja")
        self.prov_precio_kg.textChanged.connect(self.update_prov_calc)
        form_layout.addWidget(QLabel("Precio Acordado:"))
        form_layout.addWidget(self.prov_precio_kg)

        self.prov_calc_label = QLabel("Carga Rápida (Escribe peso y presiona Enter):")
        form_layout.addWidget(self.prov_calc_label)

        self.romaneo_input = QLineEdit()
        self.romaneo_input.setPlaceholderText("Ej: 80.5 y Enter")
        self.romaneo_input.returnPressed.connect(self.add_romaneo_item)
        form_layout.addWidget(self.romaneo_input)

        self.romaneo_table = QTableWidget()
        self.romaneo_table.setColumnCount(3)
        self.romaneo_table.setHorizontalHeaderLabels(["Nro", "Peso/Cant", "X"])
        self.romaneo_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.romaneo_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.romaneo_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.romaneo_table.verticalHeader().setVisible(False)
        self.romaneo_table.setFixedHeight(140)
        form_layout.addWidget(self.romaneo_table)

        self.lbl_romaneo_totals = QLabel("Total: 0 items - 0.00 kg")
        self.lbl_romaneo_totals.setStyleSheet("font-weight: bold; color: #3b82f6;")
        form_layout.addWidget(self.lbl_romaneo_totals)

        self.prov_amount = QLineEdit()
        self.prov_amount.setPlaceholderText("0.00")
        form_layout.addWidget(QLabel("Monto Total a Pagar ($):"))
        form_layout.addWidget(self.prov_amount)

        self.prov_payment = QComboBox()
        self.prov_payment.addItems(["Contado (Pago Inmediato)", "A Pagar (Deuda)"])
        form_layout.addWidget(QLabel("Forma de Pago:"))
        form_layout.addWidget(self.prov_payment)

        btn_save = QPushButton("Guardar Compra")
        btn_save.clicked.connect(self.save_proveedor)
        form_layout.addWidget(btn_save)
        form_layout.addStretch()
        layout.addWidget(form_container)

        table_container = QFrame()
        table_container.setObjectName("Card")
        table_layout = QVBoxLayout(table_container)
        table_layout.addWidget(QLabel("ÚLTIMAS COMPRAS REGISTRADAS (MES ACTUAL)"))
        self.prov_table = QTableWidget()
        self.prov_table.setColumnCount(10)
        self.prov_table.setHorizontalHeaderLabels(["Fecha", "Proveedor", "Mercadería", "Cant.", "Pesos/Detalle", "Total Kg/Und", "Precio Unit.", "Monto", "Estado", "Acciones"])
        self.prov_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.prov_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.prov_table.verticalHeader().setVisible(False)
        self.prov_table.setWordWrap(True)
        table_layout.addWidget(self.prov_table)
        
        layout.addWidget(table_container)
        self.stack.addWidget(self.tab_proveedores)

    def on_prov_type_change(self, text):
        if text in ["Pollo", "Achuras", "Otro"]:
            self.prov_calc_label.setText("Carga Rápida (Cajas y presiona Enter):")
            self.prov_precio_kg.setPlaceholderText("Precio x Caja/Unid.")
            self.romaneo_input.setPlaceholderText("Cant Cajas (ej: 5) y Enter")
            self.lbl_romaneo_totals.setText("Total: 0 items - 0 Cajas")
        else:
            self.prov_calc_label.setText("Carga Rápida (Escribe peso y presiona Enter):")
            self.prov_precio_kg.setPlaceholderText("Precio x Kg")
            self.romaneo_input.setPlaceholderText("Ej: 80.5 y Enter")
            self.lbl_romaneo_totals.setText("Total: 0 items - 0.00 kg")
        self.romaneo_table.setRowCount(0)
        self.update_prov_calc()

    def add_romaneo_item(self):
        val = self.romaneo_input.text().strip().replace(',', '.')
        if not val:
            return
        try:
            val_float = float(val)
            row = self.romaneo_table.rowCount()
            self.romaneo_table.insertRow(row)
            
            nro_item = QTableWidgetItem(f"#{row+1}")
            nro_item.setTextAlignment(Qt.AlignCenter)
            self.romaneo_table.setItem(row, 0, nro_item)
            
            peso_item = QTableWidgetItem(f"{val_float:.2f}")
            peso_item.setTextAlignment(Qt.AlignCenter)
            self.romaneo_table.setItem(row, 1, peso_item)
            
            btn_del = QPushButton("X")
            btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet("background-color: #ef4444; color: white; border-radius: 4px; font-weight: bold;")
            btn_del.clicked.connect(lambda _, r=row: self.remove_romaneo_item(r))
            
            widget = QWidget()
            l = QHBoxLayout(widget)
            l.setContentsMargins(0,0,0,0)
            l.addWidget(btn_del)
            l.setAlignment(Qt.AlignCenter)
            self.romaneo_table.setCellWidget(row, 2, widget)
            
            self.romaneo_input.clear()
            self.romaneo_input.setFocus()
            self.romaneo_table.scrollToBottom()
            self.update_prov_calc()
            
        except ValueError:
            QMessageBox.warning(self, "Error", "Ingrese un valor numérico válido.")

    def remove_romaneo_item(self, row):
        self.romaneo_table.removeRow(row)
        for i in range(self.romaneo_table.rowCount()):
            self.romaneo_table.item(i, 0).setText(f"#{i+1}")
            widget = self.romaneo_table.cellWidget(i, 2)
            if widget:
                btn = widget.findChild(QPushButton)
                if btn:
                    try: btn.clicked.disconnect()
                    except: pass
                    btn.clicked.connect(lambda _, r=i: self.remove_romaneo_item(r))
        self.update_prov_calc()

    def update_prov_calc(self):
        total_qty = 0.0
        items_count = self.romaneo_table.rowCount()
        for i in range(items_count):
            total_qty += float(self.romaneo_table.item(i, 1).text())
            
        is_pollo = self.prov_type.currentText() in ["Pollo", "Achuras", "Otro"]
        if is_pollo:
            self.lbl_romaneo_totals.setText(f"Total: {items_count} items - {int(total_qty)} Cajas")
        else:
            self.lbl_romaneo_totals.setText(f"Total: {items_count} items - {total_qty:.2f} kg")
            
        precio_text = self.prov_precio_kg.text().replace(',', '.')
        if precio_text:
            try:
                precio = float(precio_text)
                self.prov_amount.setText(f"{total_qty * precio:.2f}")
            except: pass

"""

content = content[:start_idx] + new_init + content[end_idx:]


# REPLACE save_proveedor
start_save_idx = content.find('    def save_proveedor(self):')
end_save_idx = content.find('    def on_loan_calc_change(self, source):')

if start_save_idx == -1 or end_save_idx == -1:
    print("Error finding save_proveedor block")
    exit(1)

new_save = """    def save_proveedor(self):
        amount_text = self.prov_amount.text()
        if not amount_text or self.romaneo_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "Debe cargar ítems y un monto total.")
            return
        try:
            amount = float(amount_text)
            date = self.prov_date.date().toString("yyyy-MM-dd")
            prov_name = self.prov_name.text() or "Proveedor General"
            prov_type = self.prov_type.currentText()
            tropa = self.prov_tropa.text() or "-"
            precio_text = self.prov_precio_kg.text().replace(',', '.')
            precio = float(precio_text) if precio_text else 0.0
            
            # Recopilar items del romaneo
            items = []
            total_kilos = 0.0
            for i in range(self.romaneo_table.rowCount()):
                nro = self.romaneo_table.item(i, 0).text()
                peso = float(self.romaneo_table.item(i, 1).text())
                items.append((nro, peso))
                total_kilos += peso

            payment = self.prov_payment.currentText()
            
            # 1. Guardar en MariaDB (Red / Inventario)
            try:
                from src.database import db_manager
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
                print(f"No se pudo guardar el romaneo en DB central (ignorado): {e_db}")
            
            # 2. Guardar en SQLite (Finanzas / Contabilidad Jefe)
            desc = f"Proveedor: {prov_name}\\nMercadería: {prov_type}\\nTropa/Lote: {tropa}\\n"
            is_pollo = prov_type in ["Pollo", "Achuras", "Otro"]
            if is_pollo:
                desc += f"Cantidad: {int(total_kilos)} cajas\\nPrecio: ${precio:,.2f} c/u"
            else:
                desc += f"Total: {total_kilos:.2f} kg ({len(items)} medias)\\nPrecio: ${precio:,.2f}/kg"

            if payment == "Contado (Pago Inmediato)":
                self.db.add_expense(date, "Carne / Proveedores", amount, desc, 'variable')
                ToastNotification(self, "Compra y Romaneo registrado (Pagado)", "✅")
            else:
                self.db.add_general_debt(desc, "Proveedor", amount, date)
                ToastNotification(self, "Compra y Romaneo registrado (Deuda)", "✅")
                
            self.romaneo_table.setRowCount(0)
            self.prov_precio_kg.clear()
            self.prov_amount.clear()
            self.romaneo_input.clear()
            self.prov_tropa.clear()
            self.prov_name.clear()
            self.update_prov_calc()
            self.load_all_data()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Verifique los datos: {e}")

"""

content = content[:start_save_idx] + new_save + content[end_save_idx:]

with codecs.open('src/jefe/contabilidad/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement successful")
