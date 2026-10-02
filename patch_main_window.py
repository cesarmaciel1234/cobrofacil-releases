import re

file_path = 'src/main_window.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r"if hasattr\(s, 'request_dashboard'\):\s+s\.request_dashboard\.connect\(self\._handle_global_dashboard_return\)\s+if hasattr\(s, 'turno_cerrado'\):"

new_code = """if hasattr(s, 'request_dashboard'):
            s.request_dashboard.connect(self._handle_global_dashboard_return)
        if hasattr(s, 'request_logout'):
            s.request_logout.connect(self._logout_to_selector)
        if hasattr(s, 'turno_cerrado'):"""

text = re.sub(pattern, new_code, text)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)
print('Patched main_window')
