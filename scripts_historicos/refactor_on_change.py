import codecs

with codecs.open('src/jefe/jefe_contabilidad.py', 'r', encoding='utf-8') as f:
    content = f.read()

search_str = """    def _on_prom_tabla_changed(self, item):
        if getattr(self, '_costo_real_kg', 0) == 0: return
        self._prom_tabla.blockSignals(True)

        if item is not None:
            r = item.row()
            col = item.column()
            try:
                if col == 3: # % Ganancia
                    pct = float(item.text().replace(',','.'))
                    precio_venta = self._costo_real_kg * (1 + pct / 100)
                    self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{precio_venta:,.2f}"))
                elif col == 4: # Precio Venta
                    precio_venta = float(item.text().replace(',','.'))
                    pct = ((precio_venta / self._costo_real_kg) - 1) * 100
                    self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pct:.2f}"))
            except: pass

        t_venta = 0.0
        t_ganancia = 0.0
        suma_kilos_cortes = 0.0
        
        font_strike = QFont()
        font_strike.setStrikeOut(True)
        font_normal = QFont()
        font_normal.setStrikeOut(False)
        
        for r in range(self._prom_tabla.rowCount()):
            try:
                kilos = float(self._prom_tabla.item(r, 1).text() or 0)
                precio_venta_base = float(self._prom_tabla.item(r, 4).text().replace(',','') or 0)
                
                # Oferta logic
                oferta_str = self._prom_tabla.item(r, 5).text().replace(',','').strip()
                precio_activo = precio_venta_base
                tiene_oferta = False
                if oferta_str:
                    try:
                        precio_oferta = float(oferta_str)
                        if precio_oferta > 0:
                            precio_activo = precio_oferta
                            tiene_oferta = True
                    except: pass
                
                # Strikethrough for base price if offer exists
                it_venta = self._prom_tabla.item(r, 4)
                if tiene_oferta:
                    it_venta.setFont(font_strike)
                    it_venta.setForeground(QColor("#94A3B8")) # Gray out
                else:
                    it_venta.setFont(font_normal)
                    it_venta.setForeground(QColor(PAL['text']))
                
                # Update % if base price changed manually (only if no offer, or just let it be)
                if self._costo_real_kg > 0 and precio_venta_base > 0:
                    pct = ((precio_venta_base / self._costo_real_kg) - 1) * 100
                    self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pct:.2f}"))
                
                costo_tot = kilos * self._costo_real_kg
                venta_tot = kilos * precio_activo
                ganancia = venta_tot - costo_tot
                
                self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{self._costo_real_kg:,.2f}"))
                
                vi = QTableWidgetItem(f"{venta_tot:,.2f}")
                vi.setForeground(QColor(PAL['success'] if ganancia >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 6, vi)
                
                gi = QTableWidgetItem(f"{ganancia:,.2f}")
                gi.setForeground(QColor(PAL['success'] if ganancia >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 7, gi)
                
                suma_kilos_cortes += kilos
                t_venta += venta_tot
                t_ganancia += ganancia
            except:
                pass

        try:
            kilos_totales = float(self._prom_kilos.text().replace(',','.') or 0)
            self._prom_merma.setText(f"{max(0, kilos_totales - suma_kilos_cortes):.2f}")
        except: pass
        
        self._lbl_prom_totales.setText(f"Total Venta: ${t_venta:,.2f} | Ganancia: ${t_ganancia:,.2f}")
        
        self._prom_tabla.blockSignals(False)"""

replace_str = """    def _on_prom_tabla_changed(self, item):
        if getattr(self, '_costo_real_kg', 0) == 0: return
        self._prom_tabla.blockSignals(True)

        if item is not None:
            r = item.row()
            col = item.column()
            try:
                if col == 3: # % Ganancia
                    pct = float(item.text().replace(',','.'))
                    precio_venta = self._costo_real_kg * (1 + pct / 100)
                    self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{precio_venta:,.2f}"))
                elif col == 4: # Precio Venta
                    precio_venta = float(item.text().replace(',','.'))
                    pct = ((precio_venta / self._costo_real_kg) - 1) * 100
                    self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pct:.2f}"))
            except: pass

        t_venta_normal = 0.0
        t_ganancia_normal = 0.0
        t_venta_oferta = 0.0
        t_ganancia_oferta = 0.0
        suma_kilos_cortes = 0.0
        
        font_strike = QFont()
        font_strike.setStrikeOut(True)
        font_normal = QFont()
        font_normal.setStrikeOut(False)
        
        for r in range(self._prom_tabla.rowCount()):
            try:
                kilos = float(self._prom_tabla.item(r, 1).text() or 0)
                precio_venta_base = float(self._prom_tabla.item(r, 4).text().replace(',','') or 0)
                
                oferta_str = self._prom_tabla.item(r, 5).text().replace(',','').strip()
                precio_oferta = 0.0
                tiene_oferta = False
                if oferta_str:
                    try:
                        precio_oferta = float(oferta_str)
                        if precio_oferta > 0: tiene_oferta = True
                    except: pass
                
                it_venta = self._prom_tabla.item(r, 4)
                if tiene_oferta:
                    it_venta.setFont(font_strike)
                    it_venta.setForeground(QColor("#94A3B8"))
                else:
                    it_venta.setFont(font_normal)
                    it_venta.setForeground(QColor(PAL['text']))
                
                if self._costo_real_kg > 0 and precio_venta_base > 0:
                    pct = ((precio_venta_base / self._costo_real_kg) - 1) * 100
                    self._prom_tabla.setItem(r, 3, QTableWidgetItem(f"{pct:.2f}"))
                
                costo_tot = kilos * self._costo_real_kg
                
                # Normal Scenario
                venta_n = kilos * precio_venta_base
                gan_n = venta_n - costo_tot
                t_venta_normal += venta_n
                t_ganancia_normal += gan_n
                
                # Offer Scenario
                venta_o = kilos * (precio_oferta if tiene_oferta else precio_venta_base)
                gan_o = venta_o - costo_tot
                t_venta_oferta += venta_o
                t_ganancia_oferta += gan_o
                
                self._prom_tabla.setItem(r, 2, QTableWidgetItem(f"{self._costo_real_kg:,.2f}"))
                
                # Update row UI to show normal
                vi = QTableWidgetItem(f"{venta_n:,.2f}")
                vi.setForeground(QColor(PAL['success'] if gan_n >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 7, vi) # Was 6, now 7 because of Cant. Oferta
                
                gi = QTableWidgetItem(f"{gan_n:,.2f}")
                gi.setForeground(QColor(PAL['success'] if gan_n >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 8, gi) # Was 7, now 8
                
                suma_kilos_cortes += kilos
            except:
                pass

        try:
            kilos_totales = float(self._prom_kilos.text().replace(',','.') or 0)
            self._prom_merma.setText(f"{max(0, kilos_totales - suma_kilos_cortes):.2f}")
        except: pass
        
        self._lbl_prom_totales_normal.setText(f"Normal => Venta: ${t_venta_normal:,.2f} | Ganancia: ${t_ganancia_normal:,.2f}")
        self._lbl_prom_totales_oferta.setText(f"Ofertas => Venta: ${t_venta_oferta:,.2f} | Ganancia: ${t_ganancia_oferta:,.2f}")
        
        self._prom_tabla.blockSignals(False)"""

if search_str in content:
    content = content.replace(search_str, replace_str)
else:
    print("Could not find exact _on_prom_tabla_changed body")

with codecs.open('src/jefe/jefe_contabilidad.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("_on_prom_tabla_changed replaced successfully.")
