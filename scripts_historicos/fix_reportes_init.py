import codecs

with codecs.open('src/admin/admin3_reportes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace self.cargar_datos("Semana Actual") with a timer
old_str = "self.setup_ui()\n        self.cargar_datos(\"Semana Actual\")"
new_str = "self.setup_ui()\n        from PyQt5.QtCore import QTimer\n        QTimer.singleShot(100, lambda: self.cargar_datos(\"Semana Actual\"))"

content = content.replace(old_str, new_str)

with codecs.open('src/admin/admin3_reportes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Init replaced successfully!")
