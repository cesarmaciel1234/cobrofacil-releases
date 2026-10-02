import re

file_path = 'src/contabilidad/jefe_contabilidad.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Add signal
if 'request_logout = pyqtSignal()' not in text:
    text = text.replace('request_dashboard = pyqtSignal()', 'request_dashboard = pyqtSignal()\n    request_logout = pyqtSignal()')

# Change btn_back
pattern_btn = r"btn_back = QPushButton\(\"⬅ Panel Jefe\"\).*?btn_back\.clicked\.connect\(self\.request_dashboard\.emit\)"

new_btn = """from src.config import config
        is_contabilidad_only = (config.current_user and config.current_user.get('role') == 'contabilidad')
        
        btn_back = QPushButton("⬅ Cerrar Sesión" if is_contabilidad_only else "⬅ Panel Jefe")
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setFixedHeight(34)
        btn_back.setStyleSheet(f\"\"\"
            QPushButton {{
                background: {PAL['surface2']}; color: {PAL['text2']};
                border: 1px solid {PAL['border']}; border-radius: 8px;
                padding: 0 16px; font-weight: 700; font-size: 12px;
            }}
            QPushButton:hover {{ background: {PAL['border2']}; color: {PAL['text']}; }}
        \"\"\")
        
        if is_contabilidad_only:
            btn_back.clicked.connect(self.request_logout.emit)
        else:
            btn_back.clicked.connect(self.request_dashboard.emit)"""

text = re.sub(pattern_btn, new_btn, text, flags=re.DOTALL)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched navbar')
