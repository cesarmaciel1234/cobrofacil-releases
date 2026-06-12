import codecs

with codecs.open('src/jefe/jefe_contabilidad.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. ADD SINC BUTTON TO UI
search_ui = """        btn_export = QPushButton("💾 Exportar a Inventario")
        btn_export.setStyleSheet("background: #0EA5E9; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_export.clicked.connect(self._prom_exportar_inventario)"""

replace_ui = """        btn_export = QPushButton("💾 Exportar a Inventario")
        btn_export.setStyleSheet("background: #0EA5E9; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_export.clicked.connect(self._prom_exportar_inventario)
        
        btn_sync = QPushButton("🔄 Sincronizar")
        btn_sync.setStyleSheet("background: #10B981; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_sync.clicked.connect(self._prom_sincronizar_inventario)"""

content = content.replace(search_ui, replace_ui)

search_add_to_lay = """        tot_lay.addWidget(self._lbl_prom_totales)
        tot_lay.addStretch()
        tot_lay.addWidget(btn_export)
        tot_lay.addWidget(btn_redondeo)"""

replace_add_to_lay = """        tot_lay.addWidget(self._lbl_prom_totales)
        tot_lay.addStretch()
        tot_lay.addWidget(btn_sync)
        tot_lay.addWidget(btn_export)
        tot_lay.addWidget(btn_redondeo)"""

content = content.replace(search_add_to_lay, replace_add_to_lay)


# 2. UPDATE EXPORT AND ADD SYNC LOGIC
search_export = """    def _prom_exportar_inventario(self):
        pwd, ok = QInputDialog.getText(self, "Exportar Inventario", "Ingrese contraseña de Jefe para autorizar:", QLineEdit.Password)
        if not ok or not pwd: return
        
        # Validar contraseña
        from src.base_de_datos.database import MariaDBConnection
        db = MariaDBConnection()
        res = db.fetch_all("SELECT rol FROM usuarios WHERE password = %s", (pwd,))
        if not res or res[0]['rol'] != 'jefe':
            QMessageBox.critical(self, "Acceso Denegado", "Contraseña incorrecta o el usuario no es Jefe.")
            db.close()
            return
            
        try:
            # Iterar tabla y actualizar productos
            actualizados = 0
            for r in range(self._prom_tabla.rowCount()):
                corte = self._prom_tabla.item(r, 0).text().strip()
                # Priorizar oferta
                oferta_str = self._prom_tabla.item(r, 5).text().replace(',','').strip()
                precio_base_str = self._prom_tabla.item(r, 4).text().replace(',','').strip()
                
                precio_final = 0.0
                if oferta_str:
                    try: precio_final = float(oferta_str)
                    except: pass
                if precio_final <= 0 and precio_base_str:
                    try: precio_final = float(precio_base_str)
                    except: pass
                    
                if precio_final > 0:
                    # Update DB where name matches exactly
                    db.execute_query("UPDATE productos SET precio_venta = %s WHERE nombre = %s", (precio_final, corte))
                    # Note: Execute query returns cursor or count usually, but if it doesn't fail, we assume it's fine.
                    actualizados += 1
            db.close()
            QMessageBox.information(self, "Éxito", f"Se exportaron los precios de {actualizados} cortes al inventario general.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo la exportación: {e}")"""

replace_export = """    def _prom_exportar_inventario(self):
        pwd, ok = QInputDialog.getText(self, "Exportar Inventario", "Ingrese contraseña de Jefe para autorizar:", QLineEdit.Password)
        if not ok or not pwd: return
        
        from src.base_de_datos.database import DatabaseManager
        db = DatabaseManager()
        res = db.execute_query("SELECT rol FROM usuarios WHERE pin = ? OR password_hash = ?", (pwd, pwd))
        if not res or res[0]['rol'] != 'jefe':
            QMessageBox.critical(self, "Acceso Denegado", "Contraseña incorrecta o el usuario no es Jefe.")
            return
            
        try:
            actualizados = 0
            for r in range(self._prom_tabla.rowCount()):
                corte = self._prom_tabla.item(r, 0).text().strip()
                oferta_str = self._prom_tabla.item(r, 5).text().replace(',','').strip()
                precio_base_str = self._prom_tabla.item(r, 4).text().replace(',','').strip()
                
                precio = 0.0
                precio_oferta = 0.0
                
                try: 
                    if precio_base_str: precio = float(precio_base_str)
                except: pass
                try:
                    if oferta_str: precio_oferta = float(oferta_str)
                except: pass
                
                if precio > 0 or precio_oferta > 0:
                    # Update DB where name matches exactly
                    db.execute_non_query("UPDATE productos SET precio = ?, precio_oferta = ? WHERE nombre = ?", (precio, precio_oferta, corte))
                    actualizados += 1
            
            QMessageBox.information(self, "Éxito", f"Se exportaron los precios de {actualizados} cortes al inventario general.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo la exportación: {e}")

    def _prom_sincronizar_inventario(self):
        from src.base_de_datos.database import DatabaseManager
        db = DatabaseManager()
        
        try:
            actualizados = 0
            self._prom_tabla.blockSignals(True)
            for r in range(self._prom_tabla.rowCount()):
                corte = self._prom_tabla.item(r, 0).text().strip()
                res = db.execute_query("SELECT precio, precio_oferta FROM productos WHERE nombre = ?", (corte,))
                
                if res and len(res) > 0:
                    row = res[0]
                    # The fetchall() with dictionary=True or sqlite3.Row provides dict-like access
                    # To be safe, we access by index if keys fail, but Row supports both.
                    try:
                        precio = float(row['precio'] or 0)
                        precio_oferta = float(row['precio_oferta'] or 0)
                    except:
                        precio = float(row[0] or 0)
                        precio_oferta = float(row[1] or 0)
                    
                    if precio > 0:
                        self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{precio:,.2f}"))
                    
                    if precio_oferta > 0:
                        self._prom_tabla.setItem(r, 5, QTableWidgetItem(f"{precio_oferta:,.2f}"))
                    else:
                        self._prom_tabla.setItem(r, 5, QTableWidgetItem(""))
                        
                    actualizados += 1
            
            self._prom_tabla.blockSignals(False)
            self._on_prom_tabla_changed(None) # Force recalculation to update percentages and totals
            QMessageBox.information(self, "Sincronizado", f"Se importaron {actualizados} precios/ofertas desde el Inventario.")
        except Exception as e:
            self._prom_tabla.blockSignals(False)
            QMessageBox.warning(self, "Error", f"Fallo la sincronización: {e}")"""

if search_export in content:
    content = content.replace(search_export, replace_export)
else:
    print("Could not find export block")

with codecs.open('src/jefe/jefe_contabilidad.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Sync logic added successfully")
