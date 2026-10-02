file_path = 'src/cajero/paso6_cobro/paso6_cobro.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace button text
text = text.replace('self.btn_tipo_desc = QPushButton("$")', 'self.btn_tipo_desc = QPushButton("$ ▾")')
text = text.replace('self.btn_tipo_rec = QPushButton("$")', 'self.btn_tipo_rec = QPushButton("$ ▾")')
text = text.replace('self.btn_tipo_desc.setFixedSize(32, 32)', 'self.btn_tipo_desc.setFixedSize(48, 32)')
text = text.replace('self.btn_tipo_rec.setFixedSize(32, 32)', 'self.btn_tipo_rec.setFixedSize(48, 32)')

old_toggle_desc = '''    def _toggle_tipo_desc(self):
        if self.btn_tipo_desc.text() == "$":
            self.btn_tipo_desc.setText("%")
        else:
            self.btn_tipo_desc.setText("$")
        self.on_descuento_changed(self.txt_desc.text())'''
new_toggle_desc = '''    def _toggle_tipo_desc(self):
        if "$" in self.btn_tipo_desc.text():
            self.btn_tipo_desc.setText("% ▾")
        else:
            self.btn_tipo_desc.setText("$ ▾")
        self.on_descuento_changed(self.txt_desc.text())'''
text = text.replace(old_toggle_desc, new_toggle_desc)

old_toggle_rec = '''    def _toggle_tipo_rec(self):
        if self.btn_tipo_rec.text() == "$":
            self.btn_tipo_rec.setText("%")
        else:
            self.btn_tipo_rec.setText("$")
        self.on_recargo_changed(self.txt_rec.text())'''
new_toggle_rec = '''    def _toggle_tipo_rec(self):
        if "$" in self.btn_tipo_rec.text():
            self.btn_tipo_rec.setText("% ▾")
        else:
            self.btn_tipo_rec.setText("$ ▾")
        self.on_recargo_changed(self.txt_rec.text())'''
text = text.replace(old_toggle_rec, new_toggle_rec)

text = text.replace('self.btn_tipo_desc.text() == "%"', '"%" in self.btn_tipo_desc.text()')
text = text.replace('self.btn_tipo_rec.text() == "%"', '"%" in self.btn_tipo_rec.text()')

old_style = 'QPushButton { background: #E2E8F0; color: #1E293B; border-radius: 6px; font-weight: bold; } QPushButton:hover { background: #CBD5E1; }'
new_style = 'QPushButton { background: #E2E8F0; color: #1E293B; border-radius: 6px; font-weight: bold; border: 1px solid #CBD5E1; } QPushButton:hover { background: #CBD5E1; border: 1px solid #94A3B8; }'
text = text.replace(old_style, new_style)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched button texts and logic')
