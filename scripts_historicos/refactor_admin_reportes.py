import codecs
import re

with codecs.open('src/admin/admin3_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. ADD BUTTONS TO filters_layout
# Find: self.chk_comparativa = QCheckBox("Comparar con periodo anterior")
btn_code = """        
        # --- ALERT BUTTONS ---
        filters_layout.addSpacing(20)
        btn_alerta_stock = QPushButton("📉 ALERTA STOCK")
        btn_alerta_stock.setCursor(Qt.PointingHandCursor)
        btn_alerta_stock.setStyleSheet("background: #EF4444; color: white; font-weight: bold; padding: 6px 16px; border-radius: 8px;")
        btn_alerta_stock.clicked.connect(lambda: DialogoInventarioBajo(self).exec_())
        
        btn_hora_pico = QPushButton("⏱️ HORAS PICO")
        btn_hora_pico.setCursor(Qt.PointingHandCursor)
        btn_hora_pico.setStyleSheet("background: #F59E0B; color: white; font-weight: bold; padding: 6px 16px; border-radius: 8px;")
        btn_hora_pico.clicked.connect(lambda: DialogoVentasPorHora(self).exec_())
        
        filters_layout.addWidget(btn_alerta_stock)
        filters_layout.addWidget(btn_hora_pico)
        # ---------------------
"""
content = content.replace(
    '        self.chk_comparativa = QCheckBox("Comparar con periodo anterior")',
    btn_code + '\n        self.chk_comparativa = QCheckBox("Comparar con periodo anterior")'
)

# 2. ADD CARDS TO tables_grid
# Find: self.content_layout.addLayout(self.tables_grid)
cards_code = """
        # Col 1 - CEO Metrics
        self.card_cajeros, self.tabla_cajeros, _ = self._crear_tabla_estilizada("🏆 Ranking de Cajeros", 3)
        self.tables_grid.addWidget(self.card_cajeros, 4, 0)
        
        # Col 2 - CEO Metrics
        self.card_estrellas, self.tabla_estrellas, _ = self._crear_tabla_estilizada("⭐ Top 5 Productos Estrella", 3)
        self.tables_grid.addWidget(self.card_estrellas, 4, 1)
"""
content = content.replace(
    '        self.content_layout.addLayout(self.tables_grid)',
    cards_code + '\n        self.content_layout.addLayout(self.tables_grid)'
)

# 3. ADD LOGIC TO cargar_datos
# Find: self.pago_chart.update_data(chart_pago_data)
# Add queries for cajeros and productos
query_code = """
            self.pago_chart.update_data(chart_pago_data)
            
            # --- CEO METRICS: RANKING CAJEROS ---
            self.tabla_cajeros.setRowCount(0)
            self.tabla_cajeros.setStyleSheet(table_style)
            self.tabla_cajeros.setSelectionBehavior(QTableWidget.SelectRows)
            
            res_cajeros = db_manager.execute_query(
                "SELECT COALESCE(u.username, v.cajero) as cajero, COUNT(v.id) as cant, SUM(v.total) as tot "
                "FROM ventas v LEFT JOIN usuarios u ON v.id_usuario = u.id "
                "WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') "
                "GROUP BY cajero ORDER BY tot DESC LIMIT 5", (start_str, end_str)
            )
            if res_cajeros:
                for i, r in enumerate(res_cajeros):
                    self.tabla_cajeros.insertRow(i)
                    nombre = str(r['cajero'] or 'Desconocido').capitalize()
                    cant = r['cant']
                    tot = float(r['tot'] or 0.0)
                    
                    self.tabla_cajeros.setItem(i, 0, QTableWidgetItem(f"👤 {nombre}"))
                    
                    it_cant = QTableWidgetItem(f"{cant} tickets")
                    it_cant.setTextAlignment(Qt.AlignCenter)
                    it_cant.setForeground(QBrush(QColor("#64748B")))
                    self.tabla_cajeros.setItem(i, 1, it_cant)
                    
                    it_tot = QTableWidgetItem(f"${tot:,.2f}")
                    it_tot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    it_tot.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    it_tot.setForeground(QBrush(QColor("#10B981")))
                    self.tabla_cajeros.setItem(i, 2, it_tot)
            else:
                self.tabla_cajeros.insertRow(0)
                self.tabla_cajeros.setItem(0, 0, QTableWidgetItem("Sin ventas"))

            # --- CEO METRICS: TOP 5 PRODUCTOS ESTRELLA ---
            self.tabla_estrellas.setRowCount(0)
            self.tabla_estrellas.setStyleSheet(table_style)
            self.tabla_estrellas.setSelectionBehavior(QTableWidget.SelectRows)
            
            res_productos = db_manager.execute_query(
                "SELECT p.nombre, SUM(dv.cantidad) as cant, SUM(dv.subtotal) as tot "
                "FROM detalles_ventas dv JOIN ventas v ON dv.id_venta = v.id "
                "JOIN productos p ON dv.id_producto = p.id "
                "WHERE (v.fecha BETWEEN ? AND ?) AND v.estado IN ('COMPLETADA', 'CERRADA') "
                "GROUP BY p.id ORDER BY tot DESC LIMIT 5", (start_str, end_str)
            )
            if res_productos:
                for i, r in enumerate(res_productos):
                    self.tabla_estrellas.insertRow(i)
                    nombre = str(r['nombre'] or 'Producto').title()
                    if len(nombre) > 20: nombre = nombre[:17] + "..."
                    cant = float(r['cant'] or 0.0)
                    tot = float(r['tot'] or 0.0)
                    
                    it_nom = QTableWidgetItem(f"⭐ {nombre}")
                    it_nom.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    self.tabla_estrellas.setItem(i, 0, it_nom)
                    
                    it_cant = QTableWidgetItem(f"{cant:,.2f} u/kg")
                    it_cant.setTextAlignment(Qt.AlignCenter)
                    it_cant.setForeground(QBrush(QColor("#64748B")))
                    self.tabla_estrellas.setItem(i, 1, it_cant)
                    
                    it_tot = QTableWidgetItem(f"${tot:,.2f}")
                    it_tot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    it_tot.setFont(QFont("Segoe UI", 10, QFont.Bold))
                    it_tot.setForeground(QBrush(QColor("#F59E0B")))
                    self.tabla_estrellas.setItem(i, 2, it_tot)
            else:
                self.tabla_estrellas.insertRow(0)
                self.tabla_estrellas.setItem(0, 0, QTableWidgetItem("Sin datos"))
"""
content = content.replace(
    '            self.pago_chart.update_data(chart_pago_data)',
    query_code
)

with codecs.open('src/admin/admin3_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("CEO Metrics Injected Successfully")
