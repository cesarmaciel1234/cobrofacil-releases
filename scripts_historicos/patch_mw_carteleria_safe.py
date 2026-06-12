import re

with open('src/main_window.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add to screens
text = text.replace('None,    # 20 — JefeReportes             (lazy)', 'None,    # 20 — JefeReportes             (lazy)\n            None,    # 21 — CarteleriaMain           (lazy)')

# 2. Add to factories
text = text.replace("20: lambda: __import__('src.jefe.reportes.reportes_main', fromlist=['ReportesMain']).ReportesMain(),", "20: lambda: __import__('src.jefe.reportes.reportes_main', fromlist=['ReportesMain']).ReportesMain(),\n            21: lambda: __import__('src.carteleria.carteleria_main', fromlist=['CarteleriaMain']).CarteleriaMain(),")

# 3. Patch apply_roles
# We use regex to match apply_roles until the end of the method
pattern_apply_roles = r'(def apply_roles\(self\):.*?)(?=\s*def _on_jefe_request_tab)'
def replacer(match):
    original = match.group(1)
    # We just replace the if/else block inside it
    new_block = '''        if role == "cajero":
            self.switch_tab(1)
        elif role == "jefe":
            self.switch_tab(19)
        elif role == "carteleria":
            if hasattr(self, 'nav_bar_v3'): self.nav_bar_v3.hide()
            if hasattr(self, 'top_bar_v3'): self.top_bar_v3.hide()
            self.switch_tab(21)
        else:
            self.switch_tab(0)'''
    # Replace the old if/else block
    res = re.sub(r'        if role == "cajero":.*?self\.switch_tab\(0\)', new_block, original, flags=re.DOTALL)
    return res

text = re.sub(pattern_apply_roles, replacer, text, flags=re.DOTALL)

# 4. Patch switch_tab request_logout
switch_replacement = '''        # Conectar señales comunes si existen
        if hasattr(s, 'request_logout'):
            try:
                s.request_logout.disconnect()
            except:
                pass
            s.request_logout.connect(self._logout_to_selector)'''
text = text.replace("        if hasattr(s, 'request_logout'):", switch_replacement)

with open('src/main_window.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Patch applied successfully to main_window.py!')
