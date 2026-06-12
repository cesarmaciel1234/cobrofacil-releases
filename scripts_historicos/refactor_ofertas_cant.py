import codecs
import re

with codecs.open('src/jefe/jefe_contabilidad.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update Columns & Labels
c1 = content.find("self._prom_tabla = build_table([\"Corte\", \"Kilos\", \"Costo $/kg\", \"% Ganancia\", \"Precio/kg Venta\", \"Oferta\", \"Venta Total\", \"Ganancia Neta\"])")
if c1 != -1:
    content = content.replace("self._prom_tabla = build_table([\"Corte\", \"Kilos\", \"Costo $/kg\", \"% Ganancia\", \"Precio/kg Venta\", \"Oferta\", \"Venta Total\", \"Ganancia Neta\"])",
                              "self._prom_tabla = build_table([\"Corte\", \"Kilos\", \"Costo $/kg\", \"% Ganancia\", \"Precio/kg Venta\", \"Oferta\", \"Cant. Oferta\", \"Venta Total\", \"Ganancia Neta\"])")

c2 = content.find("self._lbl_prom_totales = QLabel(\"Total Venta: $0.00 | Ganancia: $0.00\")")
if c2 != -1:
    # We replace the tot_lay label setup
    search_lbls = """        self._lbl_prom_totales = QLabel("Total Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales.setStyleSheet(f"QLabel {{ font-size: 18px; font-weight: 900; color: {PAL['success']}; }}")"""
    replace_lbls = """        self._lbl_prom_totales_normal = QLabel("Normal => Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales_oferta = QLabel("Ofertas => Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales_normal.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 900; color: {PAL['success']}; }}")
        self._lbl_prom_totales_oferta.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 900; color: {PAL['info']}; }}")
        
        lbl_vbox = QVBoxLayout()
        lbl_vbox.addWidget(self._lbl_prom_totales_normal)
        lbl_vbox.addWidget(self._lbl_prom_totales_oferta)"""
    content = content.replace(search_lbls, replace_lbls)

    search_totlay = """        tot_lay.addWidget(self._lbl_prom_totales)
        tot_lay.addStretch()"""
    replace_totlay = """        tot_lay.addLayout(lbl_vbox)
        tot_lay.addStretch()"""
    content = content.replace(search_totlay, replace_totlay)


# 2. _guardar_estado_actual
content = content.replace("for c in range(8)]", "for c in range(9)]")
content = content.replace("for c in range(8):", "for c in range(9):")

# 3. _load_cortes_base
search_load = """                self._prom_tabla.setItem(i,4,QTableWidgetItem("0.00")) # Venta
                self._prom_tabla.setItem(i,5,QTableWidgetItem("")) # Oferta
                self._prom_tabla.setItem(i,6,QTableWidgetItem("0.00")) # Venta Tot
                self._prom_tabla.setItem(i,7,QTableWidgetItem("0.00")) # Ganancia Neta
                
        for r in range(self._prom_tabla.rowCount()):
            for c in [0, 2, 6, 7]: # Corte, Costo, Venta Tot, Ganancia Neta son solo lectura"""
replace_load = """                self._prom_tabla.setItem(i,4,QTableWidgetItem("0.00")) # Venta
                self._prom_tabla.setItem(i,5,QTableWidgetItem("")) # Oferta
                self._prom_tabla.setItem(i,6,QTableWidgetItem("")) # Cant. Oferta
                self._prom_tabla.setItem(i,7,QTableWidgetItem("0.00")) # Venta Tot
                self._prom_tabla.setItem(i,8,QTableWidgetItem("0.00")) # Ganancia Neta
                
        for r in range(self._prom_tabla.rowCount()):
            for c in [0, 2, 7, 8]: # Corte, Costo, Venta Tot, Ganancia Neta son solo lectura"""
content = content.replace(search_load, replace_load)

# 4. _on_prom_tabla_changed
# This one is tricky, I'll replace the loop body
search_on_change = """        t_venta = 0.0
        t_ganancia = 0.0
        suma_kilos_cortes = 0.0
        
        font_strike = QFont()
        font_strike.setStrikeOut(True)
        font_normal = QFont()
        
        for r in range(self._prom_tabla.rowCount()):
            kilos_str = self._prom_tabla.item(r, 1).text()
            if kilos_str:
                try:
                    kilos = float(kilos_str.replace(',','.'))
                    suma_kilos_cortes += kilos
                    
                    costo_r = kilos * self._costo_real_kg
                    self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{self._costo_real_kg:,.2f}"))
                    
                    # Logica tachado
                    oferta_str = self._prom_tabla.item(r, 5).text().replace(',','').strip()
                    precio_base_str = self._prom_tabla.item(r, 4).text().replace(',','').strip()
                    
                    it_precio_base = self._prom_tabla.item(r, 4)
                    precio_final = 0.0
                    
                    if oferta_str:
                        try:
                            precio_final = float(oferta_str)
                            it_precio_base.setFont(font_strike)
                            it_precio_base.setForeground(QColor("#94A3B8")) # gris
                        except: pass
                    else:
                        it_precio_base.setFont(font_normal)
                        it_precio_base.setForeground(QColor(PAL['text']))
                        if precio_base_str:
                            try: precio_final = float(precio_base_str)
                            except: pass
                            
                    venta_t = kilos * precio_final
                    ganancia_t = venta_t - costo_r
                    t_venta += venta_t
                    t_ganancia += ganancia_t
                    
                    self._prom_tabla.setItem(r, 6, QTableWidgetItem(f"{venta_t:,.2f}"))
                    self._prom_tabla.setItem(r, 7, QTableWidgetItem(f"{ganancia_t:,.2f}"))
                except:
                    pass
        
        self._prom_merma.setText(f"{max(0, float(self._prom_kilos.text() or 0) - suma_kilos_cortes):.2f}")
        self._lbl_prom_totales.setText(f"Total Venta: ${t_venta:,.2f} | Ganancia: ${t_ganancia:,.2f}")"""

replace_on_change = """        t_venta_normal = 0.0
        t_ganancia_normal = 0.0
        t_venta_oferta = 0.0
        t_ganancia_oferta = 0.0
        suma_kilos_cortes = 0.0
        
        font_strike = QFont()
        font_strike.setStrikeOut(True)
        font_normal = QFont()
        
        for r in range(self._prom_tabla.rowCount()):
            kilos_str = self._prom_tabla.item(r, 1).text()
            if kilos_str:
                try:
                    kilos = float(kilos_str.replace(',','.'))
                    suma_kilos_cortes += kilos
                    
                    costo_r = kilos * self._costo_real_kg
                    self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{self._costo_real_kg:,.2f}"))
                    
                    oferta_str = self._prom_tabla.item(r, 5).text().replace(',','').strip()
                    precio_base_str = self._prom_tabla.item(r, 4).text().replace(',','').strip()
                    
                    it_precio_base = self._prom_tabla.item(r, 4)
                    precio_base = float(precio_base_str) if precio_base_str else 0.0
                    precio_oferta = 0.0
                    
                    if oferta_str:
                        try:
                            precio_oferta = float(oferta_str)
                            it_precio_base.setFont(font_strike)
                            it_precio_base.setForeground(QColor("#94A3B8"))
                        except: pass
                    else:
                        it_precio_base.setFont(font_normal)
                        it_precio_base.setForeground(QColor(PAL['text']))
                            
                    # Normal Calc
                    venta_n = kilos * precio_base
                    ganancia_n = venta_n - costo_r
                    t_venta_normal += venta_n
                    t_ganancia_normal += ganancia_n
                    
                    # Oferta Calc
                    precio_final_oferta = precio_oferta if precio_oferta > 0 else precio_base
                    venta_o = kilos * precio_final_oferta
                    ganancia_o = venta_o - costo_r
                    t_venta_oferta += venta_o
                    t_ganancia_oferta += ganancia_o
                    
                    # UI shows normal row totals but strike if offer exists
                    self._prom_tabla.setItem(r, 7, QTableWidgetItem(f"{venta_n:,.2f}"))
                    self._prom_tabla.setItem(r, 8, QTableWidgetItem(f"{ganancia_n:,.2f}"))
                except:
                    pass
        
        self._prom_merma.setText(f"{max(0, float(self._prom_kilos.text().replace(',','.') or 0) - suma_kilos_cortes):.2f}")
        self._lbl_prom_totales_normal.setText(f"Normal => Venta: ${t_venta_normal:,.2f} | Ganancia: ${t_ganancia_normal:,.2f}")
        self._lbl_prom_totales_oferta.setText(f"Ofertas => Venta: ${t_venta_oferta:,.2f} | Ganancia: ${t_ganancia_oferta:,.2f}")"""

if search_on_change in content:
    content = content.replace(search_on_change, replace_on_change)
else:
    print("WARNING: Could not find _on_prom_tabla_changed body to replace!")


# 5. _prom_exportar_inventario
search_exp = """                precio = 0.0
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
                    actualizados += 1"""
replace_exp = """                cant_str = self._prom_tabla.item(r, 6).text().replace(',','').strip()
                precio = 0.0
                precio_oferta = 0.0
                cant_oferta = 0.0
                
                try: 
                    if precio_base_str: precio = float(precio_base_str)
                except: pass
                try:
                    if oferta_str: precio_oferta = float(oferta_str)
                except: pass
                try:
                    if cant_str: cant_oferta = float(cant_str)
                except: pass
                
                if precio > 0 or precio_oferta > 0:
                    db.execute_non_query("UPDATE productos SET precio = ?, precio_oferta = ?, cant_oferta = ? WHERE nombre = ?", (precio, precio_oferta, cant_oferta, corte))
                    actualizados += 1"""
if search_exp in content:
    content = content.replace(search_exp, replace_exp)
else:
    print("WARNING: could not find export block")


# 6. _prom_sincronizar_inventario
search_sync = """                res = db.execute_query("SELECT precio, precio_oferta FROM productos WHERE nombre = ?", (corte,))
                
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
                        
                    actualizados += 1"""

replace_sync = """                res = db.execute_query("SELECT precio, precio_oferta, cant_oferta FROM productos WHERE nombre = ?", (corte,))
                
                if res and len(res) > 0:
                    row = res[0]
                    try:
                        precio = float(row['precio'] or 0)
                        precio_oferta = float(row['precio_oferta'] or 0)
                        cant_oferta = float(row['cant_oferta'] or 0)
                    except:
                        precio = float(row[0] or 0)
                        precio_oferta = float(row[1] or 0)
                        cant_oferta = float(row[2] or 0)
                    
                    if precio > 0:
                        self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{precio:,.2f}"))
                    
                    if precio_oferta > 0:
                        self._prom_tabla.setItem(r, 5, QTableWidgetItem(f"{precio_oferta:,.2f}"))
                    else:
                        self._prom_tabla.setItem(r, 5, QTableWidgetItem(""))
                        
                    if cant_oferta > 0:
                        self._prom_tabla.setItem(r, 6, QTableWidgetItem(f"{cant_oferta:g}"))
                    else:
                        self._prom_tabla.setItem(r, 6, QTableWidgetItem(""))
                        
                    actualizados += 1"""
if search_sync in content:
    content = content.replace(search_sync, replace_sync)
else:
    print("WARNING: could not find sync block")

with codecs.open('src/jefe/jefe_contabilidad.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Cant Oferta feature applied.")
