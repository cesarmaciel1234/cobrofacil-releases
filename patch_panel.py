import re
with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'r', encoding='utf8') as f:
    text = f.read()

# I will modify PanelFiadoCobro to have a QLineEdit for the amount.