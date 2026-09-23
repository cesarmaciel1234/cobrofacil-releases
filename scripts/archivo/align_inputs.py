import codecs
import re

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

pattern1 = r'self\.txt_pago = QLineEdit\(""\)\s*self\.txt_pago\.setObjectName\("InputPago"\)'
replacement1 = '''self.txt_pago = QLineEdit("")
        self.txt_pago.setObjectName("InputPago")
        self.txt_pago.setAlignment(Qt.AlignmentFlag.AlignCenter)'''

pattern2 = r'self\.txt_otro = QLineEdit\("0\.00"\)\s*self\.txt_otro\.setObjectName\("InputPago"\)'
replacement2 = '''self.txt_otro = QLineEdit("0.00")
        self.txt_otro.setObjectName("InputPago")
        self.txt_otro.setAlignment(Qt.AlignmentFlag.AlignCenter)'''

if re.search(pattern1, code):
    code = re.sub(pattern1, replacement1, code)
if re.search(pattern2, code):
    code = re.sub(pattern2, replacement2, code)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Inputs aligned to center!")
