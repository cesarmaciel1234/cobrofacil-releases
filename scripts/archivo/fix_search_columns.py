import codecs
import re

path = 'src/cajero/paso5_terminal/paso5_terminal.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

pattern = r'for r in res:.*?self\.list_results\.addItem\(item\)'

replacement = '''for r in res:
                stk = float(r['stock'] or 0.0)
                stk_str = f'{int(stk)}' if stk.is_integer() else f'{stk:.2f}'
                
                item = QListWidgetItem()
                item.setData(Qt.UserRole, r)
                self.list_results.addItem(item)
                
                w = QWidget()
                # Truco para que el widget pase los eventos de click al ListWidget
                w.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                lay = QHBoxLayout(w)
                lay.setContentsMargins(10, 2, 10, 2)
                
                lbl_n = QLabel(str(r['nombre']))
                lbl_n.setStyleSheet("font-size: 18px; font-weight: bold; background: transparent; color: inherit;")
                
                lbl_p = QLabel(f"${r['precio']:.2f}")
                lbl_p.setStyleSheet("font-size: 18px; font-weight: bold; color: #059669; background: transparent;")
                lbl_p.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                lbl_p.setMinimumWidth(120)
                
                lbl_s = QLabel(f"📦 {stk_str}")
                lbl_s.setStyleSheet("font-size: 16px; font-weight: bold; color: #64748B; background: transparent;")
                lbl_s.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                lbl_s.setMinimumWidth(100)
                
                lay.addWidget(lbl_n, 1)
                lay.addWidget(lbl_p)
                lay.addWidget(lbl_s)
                
                item.setSizeHint(w.sizeHint())
                self.list_results.setItemWidget(item, w)'''

if re.search(pattern, code, re.DOTALL):
    code = re.sub(pattern, replacement, code, flags=re.DOTALL)
    with codecs.open(path, 'w', 'utf-8') as f:
        f.write(code)
    print("Fixed list format to columns!")
else:
    print("Pattern not found!")
