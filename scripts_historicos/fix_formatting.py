import codecs
import re

with codecs.open('src/jefe/jefe_reportes.py', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'(                if text == periodo:.*?btn\.setStyleSheet\("QPushButton \{  font-size: 13px; font-weight: bold; border: none; background: transparent; text-decoration: underline; \}"\).*?)(                else:\s*lbl_title\.setText)', text, flags=re.DOTALL)
if match:
    correct = """                if text == periodo:
                    btn.setStyleSheet("QPushButton {  font-size: 13px; font-weight: bold; border: none; background: transparent; text-decoration: underline; }")
                else:
                    btn.setStyleSheet("QPushButton {  font-size: 13px; font-weight: bold; border: none; background: transparent; text-decoration: underline; } QPushButton:hover {  }")
            
            lbl_title = self.findChild(QLabel, "lbl_main_title_financial")
            if lbl_title:
                m_name = ""
                if "Mes" in periodo:
                    try:
                        m_idx = int(start_str[5:7])
                        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                        m_name = meses[m_idx]
                        lbl_title.setText(f"Resumen de Ventas de {m_name}")
                    except: lbl_title.setText(f"Resumen de Ventas ({periodo})")
"""
    text = text.replace(match.group(1), correct)
    codecs.open('src/jefe/jefe_reportes.py', 'w', encoding='utf-8').write(text)
    print('Fixed formatting logic.')
else:
    print('Regex failed')
