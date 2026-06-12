import codecs
import re

# 1. FIX main.py to set config.current_user
text_main = codecs.open('main.py', 'r', encoding='utf-8').read()
replacement_main = '''        elif step == 2:
            if role_selected == "carteleria":
                from src.config import config
                config.current_user = {"role": "carteleria"}
                step = 4
                continue'''
text_main = text_main.replace('''        elif step == 2:
            if role_selected == "carteleria":
                step = 4
                continue''', replacement_main)
codecs.open('main.py', 'w', encoding='utf-8').write(text_main)


# 2. FIX main_window.py (add to screens, factories, and apply_roles)
text_mw = codecs.open('src/main_window.py', 'r', encoding='utf-8').read()

# Add to screens list
text_mw = text_mw.replace('None,    # 20 — JefeReportes             (lazy)', 'None,    # 20 — JefeReportes             (lazy)\n            None,    # 21 — CarteleriaMain           (lazy)')

# Add to factories
text_mw = text_mw.replace("20: lambda: __import__('src.jefe.reportes.reportes_main', fromlist=['ReportesMain']).ReportesMain(),", "20: lambda: __import__('src.jefe.reportes.reportes_main', fromlist=['ReportesMain']).ReportesMain(),\n            21: lambda: __import__('src.carteleria.carteleria_main', fromlist=['CarteleriaMain']).CarteleriaMain(),")

# Update apply_roles
apply_replacement = '''        if role == "cajero":
            self.switch_tab(1)
        elif role == "jefe":
            self.switch_tab(19)
        elif role == "carteleria":
            if hasattr(self, 'nav_bar_v3'): self.nav_bar_v3.hide()
            if hasattr(self, 'top_bar_v3'): self.top_bar_v3.hide()
            self.switch_tab(21)
        else:
            self.switch_tab(0)'''
text_mw = text_mw.replace('''        if role == "cajero":
            self.switch_tab(1)
        elif role == "jefe":
            self.switch_tab(19)
        else:
            self.switch_tab(0)''', apply_replacement)

# Also intercept switch_tab to connect request_logout
switch_replacement = '''        # Conectar señales comunes si existen
        if hasattr(s, 'request_logout'):
            try:
                s.request_logout.disconnect()
            except:
                pass
            s.request_logout.connect(self._logout_to_selector)'''
text_mw = text_mw.replace("        if hasattr(s, 'request_logout'):", switch_replacement)


codecs.open('src/main_window.py', 'w', encoding='utf-8').write(text_mw)
print('Patch applied successfully!')
