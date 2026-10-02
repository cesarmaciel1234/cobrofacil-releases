with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'r', encoding='utf8') as f:
    lines = f.readlines()

with open('src/cajero/paso6_cobro/fiado_en_cobro/panel.py', 'w', encoding='utf8') as f:
    for line in lines:
        if 'self.txt_monto_abono.installEventFilter(self)' in line:
            f.write('            self.txt_monto_abono.installEventFilter(self)\n')
        else:
            f.write(line)