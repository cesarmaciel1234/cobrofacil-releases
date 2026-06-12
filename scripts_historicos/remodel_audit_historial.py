import codecs
import re

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix Queries in _buscar_auditoria
# Replace strftime('%m', ...) with MONTH(...)
content = content.replace("query += \" AND strftime('%m', v.fecha) = ?\"", "query += \" AND MONTH(v.fecha) = ?\"")
content = content.replace("params.append(f\"{idx_mes:02d}\")", "params.append(idx_mes)")
# Replace strftime('%Y', ...) with YEAR(...)
content = content.replace("query += \" AND strftime('%Y', v.fecha) = ?\"", "query += \" AND YEAR(v.fecha) = ?\"")
# We already appended anio_sel directly earlier, which works fine in YEAR(v.fecha) = '2026'

# 2. Fix Query in _cargar_historial_tickets
content = content.replace("LEFT JOIN productos p ON dv.id_producto = p.codigo", "LEFT JOIN productos p ON dv.id_producto = p.id")

# 3. Fix Styles for table_audit
# In setup_audit_ui, table_audit has a setStyleSheet
new_table_audit_style = """
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Segoe UI';
                gridline-color: #F1F5F9;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #F8FAFC;
            }
            QTableWidget::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #475569;
                font-weight: 800;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-size: 11px;
            }
            QScrollBar:vertical { background: #F1F5F9; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 4px; }
"""
# Replace the dark table style block
content = re.sub(r'self\.table_audit\.setStyleSheet\("""\s*QTableWidget\s*\{.*?\}\s*"""\)', 'self.table_audit.setStyleSheet("""' + new_table_audit_style + '""")', content, flags=re.DOTALL)


# 4. Fix Styles for tabla_historial_crudo
# In setup_historial_ui, it has background-color: #1E293B;
new_table_hist_style = """
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                font-size: 13px;
                font-family: 'Segoe UI';
                gridline-color: #F1F5F9;
            }
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid #F8FAFC;
            }
            QTableWidget::item:selected {
                background-color: #EEF2FF;
                color: #4F46E5;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #475569;
                font-weight: 800;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-size: 11px;
            }
            QScrollBar:vertical { background: #F1F5F9; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #CBD5E1; border-radius: 4px; }
"""
content = re.sub(r'self\.tabla_historial_crudo\.setStyleSheet\("""\s*QTableWidget\s*\{.*?\}\s*"""\)', 'self.tabla_historial_crudo.setStyleSheet("""' + new_table_hist_style + '""")', content, flags=re.DOTALL)

# 5. Fix alternating row colors in _cargar_historial_tickets
# It was setting alternating background using dark slate. We should use #F8FAFC
content = content.replace("b_color = QColor('#1E293B') if i % 2 == 0 else QColor('#0F172A')", "b_color = QColor('#FFFFFF') if i % 2 == 0 else QColor('#F8FAFC')")
content = content.replace("b_color = QColor('#FFFFFF') if i % 2 == 0 else QColor('#F8FAFC')", "b_color = QColor('#FFFFFF') if i % 2 == 0 else QColor('#F8FAFC')") # Ensure it's correct
content = content.replace("self.tabla_historial_crudo.item(i, j).setBackground(b_color)", "self.tabla_historial_crudo.item(i, j).setBackground(b_color)")

# 6. Make search input style light 
content = content.replace("border: 1px solid #2B3139;", "border: 1px solid #E2E8F0; color: #1E293B;")
content = content.replace("QPushButton {\n                  font-weight: 900; border-radius: 4px;", "QPushButton {\n                  background: #1E293B; color: #FFFFFF; font-weight: 900; border-radius: 4px;")

with codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Auditoria and Historial styling and queries updated.")
