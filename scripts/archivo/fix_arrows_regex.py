import codecs
import re

path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with codecs.open(path, 'r', 'utf-8-sig', errors='ignore') as f:
    code = f.read()

pattern = r'if k in \(Qt\.Key_Left, Qt\.Key_Right, Qt\.Key_Up, Qt\.Key_Down\):.*?return True # Consumir evento\s*elif event\.type\(\) == QEvent\.FocusOut:'

replacement = '''# LAS FLECHAS YA NO CAMBIAN EL MÉTODO (Lógica nueva)
            # Solo permiten moverse dentro del QLineEdit
            elif event.type() == QEvent.FocusOut:'''

code = re.sub(pattern, replacement, code, flags=re.DOTALL)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(code)

print("Arrows fixed via regex!")
