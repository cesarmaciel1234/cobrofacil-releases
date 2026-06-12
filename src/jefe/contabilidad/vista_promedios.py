from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import datetime
from src.jefe.contabilidad.shared_globals import *

class VistaPromediosMixin:
    def _build_tab_promedios(self):
        lay, _ = self._page()
        
        # ESTADOS
        self._estado_promedios = {
            "Carne": {"kilos": "", "merma": "", "precio": "", "filas": []},
            "Cerdo": {"kilos": "", "merma": "", "precio": "", "filas": []},
            "Pollo": {"kilos": "", "merma": "", "precio": "", "filas": []}
        }
        self._tipo_promedio = "Carne"
        
        botones_lay = QHBoxLayout()
        botones_lay.setSpacing(10)
        
        self._btn_tipo_carne = QPushButton("🥩 CARNE")
        self._btn_tipo_cerdo = QPushButton("🐖 CERDO")
        self._btn_tipo_pollo = QPushButton("🍗 POLLO")
        
        self._btn_tipo_carne.setCursor(Qt.PointingHandCursor)
        self._btn_tipo_cerdo.setCursor(Qt.PointingHandCursor)
        self._btn_tipo_pollo.setCursor(Qt.PointingHandCursor)
        
        self._btn_tipo_carne.clicked.connect(lambda: self._cambiar_tipo_promedio("Carne"))
        self._btn_tipo_cerdo.clicked.connect(lambda: self._cambiar_tipo_promedio("Cerdo"))
        self._btn_tipo_pollo.clicked.connect(lambda: self._cambiar_tipo_promedio("Pollo"))
        
        botones_lay.addWidget(self._btn_tipo_carne)
        botones_lay.addWidget(self._btn_tipo_cerdo)
        botones_lay.addWidget(self._btn_tipo_pollo)
        botones_lay.addStretch()
        lay.addLayout(botones_lay)

        self._costo_real_kg = 0.0

        cab = QHBoxLayout()
        self._prom_prov = input_field("Proveedor")
        self._prom_fecha = date_field()
        cab.addWidget(QLabel("Proveedor:"))
        cab.addWidget(self._prom_prov)
        cab.addStretch()
        cab.addWidget(QLabel("Fecha:"))
        cab.addWidget(self._prom_fecha)
        lay.addLayout(cab)

        media_frame = QFrame()
        media_frame.setStyleSheet(f"background: {PAL['surface']}; border: 1px solid {PAL['border']}; border-radius: 8px;")
        m_lay = QHBoxLayout(media_frame)
        m_lay.setContentsMargins(15, 15, 15, 15)
        
        self._prom_kilos = input_field("Kilos totales")
        self._prom_merma = input_field("Merma Auto (kg)")
        self._prom_merma.setReadOnly(True)
        self._prom_merma.setStyleSheet(f"QLineEdit {{ background: #E2E8F0; border: 1px solid #94A3B8; color: #DC2626; font-weight: bold; border-radius: 6px; padding: 8px; }}")
        
        self._prom_precio = input_field("Precio/kg compra")
        
        for qle in [self._prom_kilos, self._prom_precio, self._prom_prov]:
            qle.setStyleSheet(f"QLineEdit {{ background: #FFFFFF; border: 1px solid #94A3B8; color: #0F172A; border-radius: 6px; padding: 8px; font-weight: bold; }}")
        
        btn_calc = btn_primary("⚙️ Calcular Costo Base")
        btn_calc.clicked.connect(self._calc_media_res)
        
        lbl_kilos = QLabel("Kilos:")
        lbl_merma = QLabel("Merma:")
        lbl_precio = QLabel("Precio/kg:")
        for lbl in [lbl_kilos, lbl_merma, lbl_precio]:
            lbl.setStyleSheet("QLabel { color: #0F172A; font-weight: bold; }")
            
        m_lay.addWidget(lbl_kilos)
        m_lay.addWidget(self._prom_kilos)
        m_lay.addWidget(lbl_merma)
        m_lay.addWidget(self._prom_merma)
        m_lay.addWidget(lbl_precio)
        m_lay.addWidget(self._prom_precio)
        m_lay.addStretch()
        m_lay.addWidget(btn_calc)
        lay.addWidget(media_frame)

        self._lbl_prom_costos = QLabel("Kilos útiles: 0.00 | Costo real kg: $0.00")
        self._lbl_prom_costos.setStyleSheet(f"QLabel {{ font-size: 16px; font-weight: 900; color: {PAL['danger']}; }}")
        lay.addWidget(self._lbl_prom_costos)

        # NUEVAS COLUMNAS (Sin Costo Total, con Oferta)
        self._prom_tabla = build_table(["Corte", "Kilos", "Costo $/kg", "% Ganancia", "Precio/kg Venta", "Oferta", "Cant. Oferta", "Venta Total", "Ganancia Neta"])
        self._prom_tabla.itemChanged.connect(self._on_prom_tabla_changed)
        lay.addWidget(self._prom_tabla)

        tot_lay = QHBoxLayout()
        self._lbl_prom_totales_normal = QLabel("Normal => Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales_oferta = QLabel("Ofertas => Venta: $0.00 | Ganancia: $0.00")
        self._lbl_prom_totales_normal.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 900; color: {PAL['success']}; }}")
        self._lbl_prom_totales_oferta.setStyleSheet(f"QLabel {{ font-size: 15px; font-weight: 900; color: {PAL['info']}; }}")
        
        lbl_vbox = QVBoxLayout()
        lbl_vbox.addWidget(self._lbl_prom_totales_normal)
        lbl_vbox.addWidget(self._lbl_prom_totales_oferta)
        
        btn_redondeo = QPushButton("Redondear Precios (500)")
        btn_redondeo.setStyleSheet(f"QPushButton {{ background: {PAL['warning']}; color: #0F172A; font-weight: bold; padding: 10px; border-radius: 6px; }}")
        btn_redondeo.clicked.connect(self._prom_redondear)
        
        btn_export = QPushButton("💾 Exportar a Inventario")
        btn_export.setStyleSheet("QPushButton { background: #0EA5E9; color: #ffffff; font-weight: bold; padding: 10px; border-radius: 6px; }")
        btn_export.clicked.connect(self._prom_exportar_inventario)
        
        btn_sync = QPushButton("🔄 Sincronizar")
        btn_sync.setStyleSheet("QPushButton { background: #10B981; color: #ffffff; font-weight: bold; padding: 10px; border-radius: 6px; }")
        btn_sync.clicked.connect(self._prom_sincronizar_inventario)

        btn_pdf_int = btn_primary("📄 PDF Interno")
        btn_pdf_int.clicked.connect(self._prom_pdf_interno)

        btn_pdf_cli = btn_primary("📄 PDF Público (Lista Precios)")
        btn_pdf_cli.clicked.connect(self._prom_pdf_clientes)

        tot_lay.addLayout(lbl_vbox)
        tot_lay.addStretch()
        tot_lay.addWidget(btn_sync)
        tot_lay.addWidget(btn_export)
        tot_lay.addWidget(btn_redondeo)
        tot_lay.addWidget(btn_pdf_int)
        tot_lay.addWidget(btn_pdf_cli)
        lay.addLayout(tot_lay)

        self._load_cortes_base()

    def _guardar_estado_actual(self):
        if not hasattr(self, '_prom_tabla'): return
        filas = []
        for r in range(self._prom_tabla.rowCount()):
            row_data = [self._prom_tabla.item(r, c).text() if self._prom_tabla.item(r, c) else "" for c in range(9)]
            filas.append(row_data)
        
        self._estado_promedios[self._tipo_promedio] = {
            "kilos": self._prom_kilos.text(),
            "merma": self._prom_merma.text(),
            "precio": self._prom_precio.text(),
            "filas": filas
        }

    def _cambiar_tipo_promedio(self, tipo):
        if hasattr(self, '_prom_tabla'):
            self._guardar_estado_actual()
            
        self._tipo_promedio = tipo
        active_style = f"QPushButton {{ background: {PAL['primary']}; color: white; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 14px; }}"
        inactive_style = "QPushButton { background: #E2E8F0; color: #0F172A; border: 1px solid #94A3B8; border-radius: 8px; padding: 12px 24px; font-weight: bold; font-size: 14px; }"
        
        self._btn_tipo_carne.setStyleSheet(active_style if tipo == "Carne" else inactive_style)
        self._btn_tipo_cerdo.setStyleSheet(active_style if tipo == "Cerdo" else inactive_style)
        self._btn_tipo_pollo.setStyleSheet(active_style if tipo == "Pollo" else inactive_style)
        
        self._load_cortes_base()

    def _load_cortes_base(self):
        self._prom_tabla.blockSignals(True)
        self._prom_tabla.setRowCount(0)
        
        estado = self._estado_promedios.get(self._tipo_promedio, {})
        filas = estado.get("filas", [])
        
        self._prom_kilos.setText(estado.get("kilos", ""))
        self._prom_merma.setText(estado.get("merma", ""))
        self._prom_precio.setText(estado.get("precio", ""))
        
        if filas:
            for i, row_data in enumerate(filas):
                self._prom_tabla.insertRow(i)
                for c in range(9):
                    val = row_data[c] if c < len(row_data) else ""
                    self._prom_tabla.setItem(i, c, QTableWidgetItem(val))
        else:
            cortes = []
            if self._tipo_promedio == "Carne": cortes = self.CORTES_CARNE
            elif self._tipo_promedio == "Cerdo": cortes = self.CORTES_CERDO
            elif self._tipo_promedio == "Pollo": cortes = self.CORTES_POLLO
            
            for i, (corte, kilos, pct) in enumerate(cortes):
                self._prom_tabla.insertRow(i)
                self._prom_tabla.setItem(i,0,QTableWidgetItem(corte))
                self._prom_tabla.setItem(i,1,QTableWidgetItem(str(kilos)))
                self._prom_tabla.setItem(i,2,QTableWidgetItem("0.00")) # Costo
                self._prom_tabla.setItem(i,3,QTableWidgetItem(str(pct))) # Ganancia
                self._prom_tabla.setItem(i,4,QTableWidgetItem("0.00")) # Venta
                self._prom_tabla.setItem(i,5,QTableWidgetItem("")) # Oferta
                self._prom_tabla.setItem(i,6,QTableWidgetItem("")) # Cant. Oferta
                self._prom_tabla.setItem(i,7,QTableWidgetItem("0.00")) # Venta Tot
                self._prom_tabla.setItem(i,8,QTableWidgetItem("0.00")) # Ganancia Neta
                
        for r in range(self._prom_tabla.rowCount()):
            for c in [0, 2, 7, 8]: # Corte, Costo, Venta Tot, Ganancia Neta son solo lectura
                it = self._prom_tabla.item(r, c)
                if it:
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                    if c == 2: it.setForeground(QColor(PAL['text3']))
                    
        self._prom_tabla.blockSignals(False)
        self._calc_media_res()

    def _calc_media_res(self):
        try:
            kilos_totales = float(self._prom_kilos.text().replace(',', '.') or "0")
            precio = float(self._prom_precio.text().replace(',', '.') or "0")
            
            suma_kilos = 0.0
            for r in range(self._prom_tabla.rowCount()):
                try: suma_kilos += float(self._prom_tabla.item(r, 1).text())
                except: pass
            
            merma_auto = kilos_totales - suma_kilos
            self._prom_merma.setText(f"{merma_auto:.2f}")
            
            self._kilos_utiles = kilos_totales - merma_auto
            total_compra = kilos_totales * precio
            self._costo_real_kg = total_compra / self._kilos_utiles if self._kilos_utiles > 0 else 0
            
            self._lbl_prom_costos.setText(f"Kilos útiles: {self._kilos_utiles:.2f} kg | Costo real kg: ${self._costo_real_kg:,.2f}")
            self._on_prom_tabla_changed(None)
        except Exception as e:
            pass # Silent on load

    def _prom_redondear(self):
        import math
        if getattr(self, '_costo_real_kg', 0) == 0: return
        self._prom_tabla.blockSignals(True)
        for r in range(self._prom_tabla.rowCount()):
            try:
                precio_actual = float(self._prom_tabla.item(r, 4).text().replace(',', ''))
                if precio_actual > 0:
                    redondeado = math.ceil(precio_actual / 500) * 500
                    self._prom_tabla.setItem(r, 4, QTableWidgetItem(f"{redondeado:,.2f}"))
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
                self._prom_tabla.setItem(r, 7, vi)
                
                gi = QTableWidgetItem(f"{gan_n:,.2f}")
                gi.setForeground(QColor(PAL['success'] if gan_n >= 0 else PAL['danger']))
                self._prom_tabla.setItem(r, 8, gi)
                
                suma_kilos_cortes += kilos
            except Exception as e:
                pass
            
        try:
            kilos_totales = float(self._prom_kilos.text().replace(',', '.') or "0")
            if kilos_totales > 0:
                merma_auto = kilos_totales - suma_kilos_cortes
                self._prom_merma.setText(f"{merma_auto:.2f}")
        except: pass

        if hasattr(self, '_lbl_prom_totales_normal') and hasattr(self, '_lbl_prom_totales_oferta'):
            self._lbl_prom_totales_normal.setText(f"Normal => Venta: ${t_venta_normal:,.2f} | Ganancia: ${t_ganancia_normal:,.2f}")
            self._lbl_prom_totales_oferta.setText(f"Ofertas => Venta: ${t_venta_oferta:,.2f} | Ganancia: ${t_ganancia_oferta:,.2f}")

        self._prom_tabla.blockSignals(False)

    def _prom_exportar_inventario(self):
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
                
                cant_str = self._prom_tabla.item(r, 6).text().replace(',','').strip()
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
                res = db.execute_query("SELECT precio, precio_oferta, cant_oferta FROM productos WHERE nombre = ?", (corte,))
                
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
                        
                    actualizados += 1
            
            self._prom_tabla.blockSignals(False)
            self._on_prom_tabla_changed(None) # Force recalculation to update percentages and totals
            QMessageBox.information(self, "Sincronizado", f"Se importaron {actualizados} precios/ofertas desde el Inventario.")
        except Exception as e:
            self._prom_tabla.blockSignals(False)
            QMessageBox.warning(self, "Error", f"Fallo la sincronización: {e}")

    def _prom_pdf_interno(self):
        try:
            from src.jefe.contabilidad.pdf_promedios import exportar_pdf_interno
            kilos = float(self._prom_kilos.text().replace(',', '.') or 0)
            merma = float(self._prom_merma.text().replace(',', '.') or 0)
            precio = float(self._prom_precio.text().replace(',', '.') or 0)
            exportar_pdf_interno(self._prom_tabla, self._prom_prov.text(), self._prom_fecha.date().toString("yyyy-MM-dd"), kilos, merma, precio, self)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al abrir PDF interno: {e}")

    def _prom_pdf_clientes(self):
        try:
            from src.jefe.contabilidad.pdf_promedios import exportar_pdf_clientes
            exportar_pdf_clientes(self._prom_tabla, self._prom_prov.text(), self._prom_fecha.date().toString("yyyy-MM-dd"), self)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Fallo al abrir PDF público: {e}")

    def _load_promedios(self):
        pass


    # ─────────────────────────────────────────────────────────────────────────
