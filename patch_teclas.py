with open('src/cajero/paso6_cobro/fiado_en_cobro/nativo.py', 'r', encoding='utf8') as f:
    text = f.read()

import re

# Remove F1-F4 from keyPressEvent
text = re.sub(r'        if k == Qt\.Key\.Key_F1:.*?return\n', '', text, flags=re.DOTALL)
text = re.sub(r'        if k == Qt\.Key\.Key_F2:.*?return\n', '', text, flags=re.DOTALL)
text = re.sub(r'        if k == Qt\.Key\.Key_F3:.*?return\n', '', text, flags=re.DOTALL)
text = re.sub(r'        if k == Qt\.Key\.Key_F4:.*?return\n', '', text, flags=re.DOTALL)

with open('src/cajero/paso6_cobro/fiado_en_cobro/nativo.py', 'w', encoding='utf8') as f:
    f.write(text)