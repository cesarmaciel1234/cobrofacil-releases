import codecs

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix overall background
content = content.replace('self.setStyleSheet("background-color: #0F172A;")', 'self.setStyleSheet("background-color: #F8FAFC;")')

# Fix Tab Buttons (Semana Actual, etc.)
new_active_style = """
            QPushButton {
                background: #1E293B;
                color: #FFFFFF;
                font-weight: 800;
                border-radius: 18px;
                padding: 8px 18px;
                font-size: 12px;
                border: none;
            }
"""
new_inactive_style = """
            QPushButton {
                background: #FFFFFF;
                color: #475569;
                font-weight: 700;
                border-radius: 18px;
                padding: 8px 18px;
                font-size: 12px;
                border: 1px solid #E2E8F0;
            }
            QPushButton:hover {
                background: #F1F5F9;
                color: #1E293B;
            }
"""
# Replace empty styles if they exist
content = content.replace("QPushButton {\n                \n                \n                font-weight: 800;", "QPushButton {\n                background: #1E293B;\n                color: #FFFFFF;\n                font-weight: 800;")
content = content.replace("QPushButton {\n                background: transparent;\n                \n                font-weight: 700;", "QPushButton {\n                background: #FFFFFF;\n                color: #475569;\n                font-weight: 700;")
content = content.replace("QPushButton:hover {\n                \n                \n            }", "QPushButton:hover {\n                background: #F1F5F9;\n                color: #1E293B;\n            }")

# Fix create_kpi title color
# def create_kpi(title, value, color="#0F172A", align="left"): ... lbl_t.setStyleSheet(f"font-size: 12px; font-weight: 800; color: #94A3B8;")
content = content.replace('lbl_t.setStyleSheet(f"font-size: 12px; font-weight: 800; color: #94A3B8;', 'lbl_t.setStyleSheet(f"font-size: 12px; font-weight: 800; color: #475569;')
content = content.replace('lbl_t.setStyleSheet(f"font-size: 13px; font-weight: 800; color: #94A3B8;', 'lbl_t.setStyleSheet(f"font-size: 13px; font-weight: 800; color: #475569;')

# Fix Checkbox text color "Comparar con periodo anterior"
content = content.replace('self.chk_compare.setStyleSheet("color: white;")', 'self.chk_compare.setStyleSheet("color: #1E293B; font-weight: 600;")')
content = content.replace('self.chk_compare.setStyleSheet("color: #FFFFFF;")', 'self.chk_compare.setStyleSheet("color: #1E293B; font-weight: 600;")')

# Fix lbl_tit_tabla (e.g. "Ventas por Departamento")
content = content.replace('lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900;  background: transparent; border: none; letter-spacing: -0.5px;")', 'lbl_tit.setStyleSheet("font-size: 18px; font-weight: 900; color: #1E293B; background: transparent; border: none; letter-spacing: -0.5px;")')

# Graph text color inside LineChartWidget
content = content.replace('painter.setPen(QPen(QColor(148, 163, 184), 1))', 'painter.setPen(QPen(QColor(71, 85, 105), 1))')
content = content.replace('painter.setPen(QPen(QColor(255, 255, 255), 1))', 'painter.setPen(QPen(QColor(30, 41, 59), 1))')

# Ensure title text is dark
content = content.replace('self.lbl_titulo = QLabel("Resumen de Ventas de Junio")\n        self.lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 900; color: white;")', 'self.lbl_titulo = QLabel("Resumen de Ventas de Junio")\n        self.lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A;")')
content = content.replace('self.lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 900; color: white;")', 'self.lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A;")')
content = content.replace('self.lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 900; color: #FFFFFF;")', 'self.lbl_titulo.setStyleSheet("font-size: 26px; font-weight: 900; color: #0F172A;")')


with codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Colors fixed")
