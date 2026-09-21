import codecs
import re

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

pattern = r"lbl_p\.setAlignment\(Qt\.AlignmentFlag\.AlignRight \| Qt\.AlignmentFlag\.AlignVCenter\)\s*lbl_p\.setMinimumWidth\(120\)\s*lbl_s = QLabel.*?lay\.addWidget\(lbl_s\)"

replacement = '''lbl_p.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                
                lbl_s = QLabel(f"📦 {stk_str}")
                lbl_s.setStyleSheet("font-size: 16px; font-weight: bold; color: #64748B; background: transparent;")
                lbl_s.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                lay.addWidget(lbl_n, 5)  # 5 partes para el nombre (Izquierda)
                lay.addWidget(lbl_p, 2)  # 2 partes para el precio (Medio)
                lay.addWidget(lbl_s, 2)  # 2 partes para el stock (Derecha)'''

if re.search(pattern, code, re.DOTALL):
    code = re.sub(pattern, replacement, code, flags=re.DOTALL)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Fixed layout alignment!")
else:
    print("Pattern not found!")
