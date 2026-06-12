import codecs

with codecs.open('src/jefe/jefe_contabilidad.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix self._prom_merma
content = content.replace(
    """self._prom_merma.setStyleSheet(f"QLineEdit { background: #E2E8F0; border: 1px solid #94A3B8; color: #DC2626; font-weight: bold; border-radius: 6px; padding: 8px; }")""",
    """self._prom_merma.setStyleSheet(f"QLineEdit {{ background: #E2E8F0; border: 1px solid #94A3B8; color: #DC2626; font-weight: bold; border-radius: 6px; padding: 8px; }}")"""
)

# Fix qle
content = content.replace(
    """qle.setStyleSheet(f"QLineEdit { background: #FFFFFF; border: 1px solid #94A3B8; color: #0F172A; border-radius: 6px; padding: 8px; font-weight: bold; }")""",
    """qle.setStyleSheet(f"QLineEdit {{ background: #FFFFFF; border: 1px solid #94A3B8; color: #0F172A; border-radius: 6px; padding: 8px; font-weight: bold; }}")"""
)

# Fix self._lbl_prom_costos
content = content.replace(
    """self._lbl_prom_costos.setStyleSheet(f"QLabel { font-size: 16px; font-weight: 900; color: {PAL['danger']}; }")""",
    """self._lbl_prom_costos.setStyleSheet(f"QLabel {{ font-size: 16px; font-weight: 900; color: {PAL['danger']}; }}")"""
)

# Fix self._lbl_prom_totales
content = content.replace(
    """self._lbl_prom_totales.setStyleSheet(f"QLabel { font-size: 18px; font-weight: 900; color: {PAL['success']}; }")""",
    """self._lbl_prom_totales.setStyleSheet(f"QLabel {{ font-size: 18px; font-weight: 900; color: {PAL['success']}; }}")"""
)

# Fix btn_redondeo
content = content.replace(
    """btn_redondeo.setStyleSheet(f"QPushButton { background: {PAL['warning']}; color: #0F172A; font-weight: bold; padding: 10px; border-radius: 6px; }")""",
    """btn_redondeo.setStyleSheet(f"QPushButton {{ background: {PAL['warning']}; color: #0F172A; font-weight: bold; padding: 10px; border-radius: 6px; }}")"""
)


with codecs.open('src/jefe/jefe_contabilidad.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("f-strings fixed.")
